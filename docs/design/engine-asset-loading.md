# Engine Asset Loading

**Description:** The C++ client asset lifecycle — the claimed load-state machine, preload/load threading, the inline-load escape hatch, and the platform-call thread-safety contract it imposes.

This covers the *engine-level* machinery in
`src/ballistica/base/assets/` — how an individual `Asset` gets its
bytes into usable form and which threads do that work. The
package/CAS layer above it (apverids, resolves, the writable cache,
the bundle) is documented in
`efrohome:docs/global_design/asset-packages.md`; this doc picks up
where that one hands content to the engine.

## Cast of characters

- **`Asset`** (`asset.h/.cc`) — base class for a loadable payload
  (`TextureAsset`, `MeshAsset`, `SoundAsset`, `DataAsset`,
  `CollisionMeshAsset`). Owns the load-state machine. Scene/UI-level
  objects hold refs to these; the payload itself lives here.
- **`Assets`** (`assets.h/.cc`) — the registry: per-type name→asset
  maps, the per-type *pending-load* queues, pruning, language data
  (legacy), and the client-context gating that keeps loads from
  running before the graphics context/texture-quality settings
  exist.
- **`AssetsServer`** (`assets_server.h/.cc`) — a dedicated event-loop
  thread ("assets thread") that drains the *pending-preload* queue in
  small time-budgeted batches and hosts attached background
  `Processor`s (e.g. replay stream writing).
- **Platform text stack** (`CoreConfig`/platform classes) — OS-side
  unicode text rasterization (`CreateTextTexture` etc.) and
  measuring/line-breaking; see `os-font-rendering.md`. Relevant here
  because rasterization runs *inside* texture preload.

## The claimed state machine

An asset's load-state is a single `std::atomic<State>`; the full
model is documented at the top of `asset.h` and is summarized here.
States are either **stable** (`kUnloaded`, `kPreloaded`, `kLoaded`,
`kFailed`) or **claims** (`kPreloading`, `kLoading`, `kUnloading`,
`kReresolving`). Work starts only by CAS-ing from a stable state into
a claim; there is no transition *from* a claim except by its owner,
so the owning thread works lock-free and finishes by release-storing
the next stable state. Waiters block on a shared condition variable;
the hot already-loaded path is one atomic acquire-load.

Two invariants worth repeating:

- **`kFailed` is terminal** — no retry/log storms; pruning may evict
  an unreferenced failed asset so a fresh use can retry via
  re-creation.
- **No blocking GIL acquisition while holding a claim** — the logic
  thread may hold the GIL while waiting on that very claim. Claims
  arm a debug no-GIL-lock zone; logs are emitted only after
  publishing.

## Two paths to loaded

### 1. The pipeline (the common path)

1. **Logic thread**: an asset is created/looked up (`kUnloaded`) and
   `Assets::MarkAssetForLoad()` (logic-thread-only) pushes a
   heap-allocated ref to the assets server.
2. **Assets thread**: `AssetsServer::Process_()` drains pending
   preloads in batches bounded by a small time budget (audio queued
   separately at lower priority — sounds hitch least when loaded
   on-demand). Each gets `Preload()` (disk read, decode, and — for
   text textures — OS rasterization), then moves to the per-type
   pending-*load* queues on `Assets`.
3. **Type-appropriate thread finishes the load** (`DoLoad`, which
   generally needs an API context):
   - textures/meshes → graphics-server thread
     (`RunPendingGraphicsLoads()` per frame; GL upload happens here)
   - sounds → audio-server thread
   - data assets and the rest → logic thread
     (`RunPendingLoadsLogicThread()`)

### 2. On-demand (the escape hatch — read this part twice)

`Asset::Load()`'s `kUnloaded` branch **claims and runs the entire
preload+load inline on whatever thread called it**. This is by
design (a consumer that needs the asset *now* shouldn't deadlock or
wait for a queue), and it has real callers:

- **Graphics thread** — `Renderer::LoadMedia()` force-loads every
  asset referenced by each frame. Since frames outpace the assets
  thread's budgeted batches, a just-created UI text texture is
  routinely preloaded *here*, not on the assets thread.
- **Audio thread** — the audio server `Load()`s sounds on use.
- **BG-dynamics thread** — collision meshes.
- **Logic thread** — data assets (holding the GIL — fine per the
  invariant above).

This is not just an implementation accident — it is the **specified
API contract** (stated on `Asset::DoPreload()` in `asset.h`):

- `DoPreload()` may run on **any** thread, and preloads of
  *different* assets may run **concurrently** on different threads
  (per-asset claims serialize only the individual asset). This
  covers the on-demand path today and deliberately reserves the
  option of parallel preload workers in the future.
- Implementations — and anything they call transitively, platform
  code especially — must not assume a particular thread or exclusive
  execution. Code touching genuinely non-thread-safe shared state
  wrangles its **own** mutex locally; the engine core stays
  lock-free.
- `DoLoad()` is the asymmetric counterpart: it **is** thread-pinned
  by design (it needs the type's API context), which is what the
  per-type pending-load queues exist for.

## The platform text-rasterization contract

Text textures rasterize their glyphs during preload
(`TextureAsset::DoPreload()` → `platform->CreateTextTexture()` /
`GetTextTextureData()` / `FreeTextTexture()`), so per the above the
OS text stack can be entered from the assets thread *or* the graphics
thread, concurrently with itself and with logic-thread text
*measuring* (`GetTextBoundsAndWidth`, `GetTextLineBreakOffsets`).
The required contract for the platform implementations is therefore
**callable from any thread, including concurrently** — not "runs on
the assets thread". Per the DoPreload contract above, each backend
owns whatever locking it needs to meet that. Status per backend
(audited + fixed 2026-07-17):

- **Android**: naturally safe, no lock needed. JNI env is fetched
  via the auto-attach pthread-key pattern (any thread works), and
  the Java side builds a per-call `Bitmap`/`Canvas` (legal off the
  UI thread).
- **Windows**: the D2D/DWrite factories are `MULTI_THREADED` and
  render targets are per-call, but the pixel readback runs through
  the shared D3D11 immediate context (`CopyResource`/`Map`/`Unmap`
  on `g_d3d11_context`), which is not thread-safe — including
  against D2D's *internal* use of that context at `EndDraw`.
  `CreateTextTexture` therefore serializes its whole
  rasterize+readback body behind a file-local mutex
  (`g_text_texture_mutex`, `platform_windows.cc`). Measuring
  (`GetTextBoundsAndWidth`) deliberately takes no lock — it only
  touches the thread-safe shared DWrite factory.
- **Pango** (Linux, and currently the Apple path too —
  `PlatformApple::CreateTextTexture` routes to Pango with the old
  CoreText implementation commented out): per-call
  surface/context/layout objects, but the **shared default fontmap**
  underneath. Modern pango (≥1.32.6) + fontconfig (≥2.13) document
  this as thread-safe, but we don't pin those minimums, and
  logic-thread measuring runs concurrently with rasterization
  *today* — so all Pango entry points (measure, line-break,
  rasterize) share one belt-and-braces mutex (`g_pango_mutex_`,
  `platform_pango.h`).

Text-texture creation is rare and ms-scale, so the coarse locks cost
nothing measurable. If the Apple CoreText path is ever revived, it
must be audited under the same any-thread contract.

## Pruning and lifecycle edges

- `Assets` prunes assets unreferenced beyond a standard interval
  (`last_used_time`), including evicting `kFailed` entries so later
  uses can retry.
- Loads are gated on the graphics client-context existing (texture
  quality/compression formats must be known before texture preloads
  make choices); renderer changes re-mark everything for load
  (`MarkAllAssetsForLoad()`).
- `kReresolving` exists for in-place source-identity swaps on loaded
  assets (asset-package re-resolves) without dropping the payload.

## Where the package layer hands off

Python-side `app.assets.resolve()` (see the global asset-packages
doc) materializes package content into the CAS caches and registers
logical names; engine-side asset lookups then find those names via
the package registry (`asset_package_registry.cc`) and individual
`Asset`s load from the resolved files through the machinery above.
The planned native language-string store (language-string-context
initiative, D-r) will hang off this same handoff: package resolve
delivers per-locale string blobs, and a parse-once native table load
rides the pipeline like any other asset payload.
