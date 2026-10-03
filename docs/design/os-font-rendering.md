# OS font rendering

**Description:** Dynamic text is rendered and line-broken (UAX #14) via each OS's native text stack behind one small platform interface, so the engine ships no huge Unicode fonts or line-break tables.

The engine ships pre-baked glyph pages covering a core character set, but the
full Unicode range is far too large to pre-bake. Everything outside the baked
set is rendered at runtime by the host OS's native text stack — CoreText on
Apple, Java Canvas on Android, DirectWrite/Direct2D on Windows, Pango+Cairo on
Linux — through a small platform-virtual interface. This keeps text looking
native-quality everywhere (CJK, Arabic, emoji-adjacent symbols, etc.) without
bundling gigantic fonts.

## Key files

- `src/ballistica/base/graphics/text/text_graphics.h/cc` — glyph management,
  LRU text-bounds cache.
- `src/ballistica/base/graphics/text/text_group.h/cc` — high-level text
  orchestration.
- `src/ballistica/base/graphics/text/text_packer.h/cc` — bin-packing layout of
  OS-rendered spans into textures (32–2048px).
- `src/ballistica/base/graphics/text/font_page_map_data.h` — Unicode →
  glyph-page lookup.
- `src/ballistica/base/graphics/mesh/text_mesh.h/cc` — GPU quad generation per
  character.
- `src/ballistica/core/platform/platform.h` — the platform virtual interface.
- `src/ballistica/core/platform/apple/platform_apple.h/cc` — CoreText impl
  (plus the Pango path for Apple cmake builds).
- `src/ballistica/core/platform/android/platform_android.h/cc` — JNI impl.
- `src/ballistica/core/platform/windows/platform_windows.h/cc` —
  DirectWrite/D2D impl.
- `src/ballistica/core/platform/support/platform_pango.h` — shared inline
  Pango/Cairo helpers used by the Linux (and Apple-cmake) impls.
- `src/ballistica/base/app_platform/apple/TextTextureData.swift` — Swift
  CoreText wrapper.

## The platform virtual interface

Each platform implements five virtuals on `CorePlatform`
(`src/ballistica/core/platform/platform.h`):

```cpp
virtual void GetTextBoundsAndWidth(const std::string& text, Rect* r,
                                   float* width);
virtual void* CreateTextTexture(int width, int height,
                                const std::vector<std::string>& strings,
                                const std::vector<float>& positions,
                                const std::vector<float>& widths, float scale);
virtual uint8_t* GetTextTextureData(void* tex);
virtual void FreeTextTexture(void* tex);
virtual std::vector<int> DoGetTextLineBreakOffsets(const std::string& text);
```

The graphics layer measures text (`GetTextBoundsAndWidth`), bin-packs the
spans it needs into a texture layout (`text_packer`), asks the platform to
render them all into one texture (`CreateTextTexture`), reads the pixels back
(`GetTextTextureData`), and frees the platform object when done.

`GetTextLineBreakOffsets` is a sibling concern (line *breaking*, not
rendering): it returns utf-8 byte offsets where a new line may begin, per
the OS text stack's Unicode UAX #14 analysis — including dictionary-based
word segmentation for Thai and friends — so the engine never ships Unicode
break tables or word dictionaries. Callable from any thread (since
2026-10-02): the public non-virtual `GetTextLineBreakOffsets()` holds one
mutex around the protected `DoGetTextLineBreakOffsets()` that platforms
override, so implementations never run concurrently and may keep shared
state. Android needs it (one shared ICU `BreakIterator` on the Java side,
whose method is also `synchronized`); the others build fresh analyzers per
call and are covered as insurance. Calls are microseconds, so the lock
costs nothing measurable. An override must never call the public wrapper
(self-deadlock); fall back via `Platform::DoGetTextLineBreakOffsets()`. On
Android, an off-thread call attaches the thread to the JVM; `GetEnv()`
detaches threads it attached when they exit (unregistered, they leak a
zombie `java.lang.Thread` each — measured on API 29/37). The base-class
fallback (headless etc.) breaks at spaces/newlines only.
Per-backend sources: CFStringTokenizer's `kCFStringTokenizerUnitLineBreak`
(Apple Xcode builds), `android.icu.text.BreakIterator.getLineInstance` over
sync JNI (Android), `IDWriteTextAnalyzer::AnalyzeLineBreakpoints` (Windows),
`pango_get_log_attrs` (Linux + Apple cmake builds). Verified on all four
2026-07-11 at 3–60µs per call (behavior probe + timings:
`babase._text.run_line_break_selftest`, via the private
`_babase.get_text_line_break_offsets` binding). Backends differ slightly
in Thai word choices (ICU vs libthai dictionaries) — cosmetic; don't
golden-test exact offsets cross-platform.

First real consumer: `Platform::SplitTextIntoLines()` (exposed as
`babase.split_text_into_lines()`), a constraint-based splitter
(min/max lines, max chars per line) that treats characters as equal
width and picks the most balanced break set via a small DP; callable
from any thread, like the call it builds on. It exists
to feed flat new-style translations into places expecting preformatted
line counts (the legacy translations baked in hard line breaks); a
proper font-aware wrapping text widget supersedes it eventually.

## Per-platform implementations

- **Apple (Xcode builds)** — CoreText drawing into a `CGContext`, wrapped by
  `TextTextureData.swift` and reached over Swift/C++ interop. 26pt system
  font, regular weight (`useBoldFont=false`). Output is RGBA8 premultiplied.
- **Android** — JNI bridge to the Java `Canvas`/`Bitmap` APIs. Note the
  UTF-8 → modified-UTF-16 conversion required at the JNI boundary.
- **Windows** — DirectWrite for layout plus Direct2D for rasterization into a
  D3D11 texture, read back through a staging texture. Pixels arrive as BGRA8
  (swizzled to RGBA on readback); uses a semi-bold weight.
- **Linux (and Apple cmake builds)** — Pango+Cairo, shared via the inline
  helpers in `platform_pango.h`. REQUIRED by default for gui-flavor cmake
  builds as of 2026-07-12 (`REQUIRE_OS_FONT_RENDERING` defaults ON): a
  missing pangocairo fails the configure loudly rather than silently
  producing a build with the internal fallback text handling — pass
  `-DREQUIRE_OS_FONT_RENDERING=OFF` to opt out. On Ubuntu the dependency is
  `libpango1.0-dev` (installed by the public CI build-env action). The
  check lives inside the `else()` of `if(HEADLESS)`, so headless server
  builds never require or link it.

Two Pango details worth keeping:

- Font is "Sans" at `PANGO_WEIGHT_MEDIUM`, sized via
  `pango_font_description_set_absolute_size` — the absolute-size call
  **bypasses system DPI**, keeping metrics consistent with CoreText's 72-DPI
  behavior regardless of how the host configures DPI.
- Cairo's `CAIRO_FORMAT_ARGB32` is little-endian BGRA in memory, so the same
  B↔R swizzle used on Windows is applied on readback.

## Font pages

Characters map to *font pages* via `font_page_map_data.h`:

- **Pages 0–7** — pre-baked regular fonts (~1,280 glyphs total), lazy-loaded
  from `.fdata` files.
- **Page 9989 (kOSRendered)** — the dynamic OS-rendered page; everything not
  covered by the baked pages lands here and goes through the platform
  interface above.
- **Pages 9990–9994 (kExtras)** — custom icons in the Unicode private-use
  area (U+E000–U+F8FF).

## Output convention

All OS renderers produce **white-on-transparent RGBA8 with premultiplied
alpha**; colorization happens in the shader. Because the textures are
premultiplied, drawing them is subject to the caller-premultiply convention —
see `docs/design/premultiplied-alpha.md` (the text drop-shadow shader path
there also branches on this).

## Caching tiers

- **Text span bounds** — mutex-guarded LRU cache (1000 entries) in
  `text_graphics`, shared by all threads, since measuring via the OS is
  comparatively expensive. Sized to comfortably exceed the biggest
  background pre-measure batches (the credits window populates several
  hundred spans) so entries survive until the logic thread consumes them.
- **Generated textures** — hash-keyed in the asset system and shared across
  `TextGroup`s, so identical strings rendered in multiple places reuse one
  texture.
- **Glyph pages** — lazy-loaded on first use and never evicted.

## Threading: measurement off the logic thread

A *cold* OS measure can block for tens of milliseconds on the OS backend's
lazy per-script font loads — a visible frame hitch if it happens on the
logic thread. Since 2026-08-24 the rule is: **the logic thread never waits
on a cold measure.** The pieces (all in `TextGraphics`,
`text_graphics.h/cc`):

- **Measurement is thread-safe** on all four backends (CoreText, minikin
  over JNI, DirectWrite, Pango). The span cache and glyph-page loads are
  mutex-guarded and the platform backends handle their own
  synchronization; the OS measure itself runs *outside* the cache lock so
  a cold measure never blocks cache hits on other threads. (Line breaking
  and rasterization keep their own, narrower contracts.)
- **Non-stalling `Try` variants.** `TryGetOSTextSpanBoundsAndWidth()` and
  the string-level `TryGetStringWidth()` measure inline on a cache hit or
  when called off the logic thread; on a logic-thread cache miss they
  kick a background measure on the assets-server event loop (dedup'd
  against in-flight ones; `TryGetStringWidth` kicks all of a string's
  cold spans in one pass) and report not-ready. String *height* needs no
  variant — it is pure row counting.
- **Epoch self-heal.** `os_span_measure_epoch()` bumps after each
  background measure lands in the cache. `TextMesh`/`TextGroup` defer
  whole builds (blank until ready): `TextGroup` records the epoch at
  build time and `GetElementCount()` re-runs `SetText` once the epoch
  moves. Widgets and nodes ride `TryGetStringWidth` and retry next
  frame. Deferring consumers must re-*request* on each attempt rather
  than assume a completed measure implies a cached result (an entry can
  in principle be evicted first); rounds still converge because the fonts
  stay warm.
- **`WarmUpStringAsync()`** — the cheap pre-warm for text *setters* on
  the logic thread: costs a string copy at the call site (after a quick
  `HasOSChars()` early-out), with the full measure walk on the assets
  loop. Skips quietly if the assets-server loop isn't up yet.
- **`warm_up_string_measure()`** (Python; `babase`/`bauiv1`) exposes the
  same warm-up to app code. For acknowledged sync-measure sites whose
  strings are known before the measure is needed: `PopupMenu` warms its
  choice strings when its *button* is built, so the popup window's
  logic-thread width measures are cache hits by the time it opens (the
  language picker's ~40 native-script names stalled ~80ms cold before
  this, 2026-09-21). The stall-tripwire warnings point here.
- **Boot pre-warm is disabled by design** (`kEnableOSTextWarmUp{false}`;
  `WarmUpOSText()` is a no-op). The set of scripts that can appear in
  online content is unboundable, so lazy font loads are made non-hitching
  structurally rather than papered over for a hand-picked set; players
  who never see a script shouldn't pay its load cost. The machinery stays
  wired for a possible targeted variant (emoji-only, or locale-driven).
- **Big batches measure on a background thread.** App code expecting to
  measure many multi-script strings (the credits window's contributor
  list) composes and lays out off-thread, then creates premeasured
  widgets in per-frame batches.

Tripwires — the goal is zero expected triggers, so treat any sighting as
a call site to convert:

- A *synchronous* logic-thread cache miss logs a `ba.graphics` warning
  (all builds; once per unique span, capped per run; debug builds add a
  native stack trace).
- The Python `get_string_width()`/`get_string_height()` bindings warn on
  mere *presence* of OS-rendered chars on the logic thread (catches sites
  whose stall is hidden by another path having warmed the cache).
  Passing `suppress_logic_thread_warning=True` acknowledges a site that
  genuinely needs the value for logic-thread layout; acked sites stay
  quiet unless the measure actually stalls past 5ms.
- Debug builds report every 16th new span's first logic-thread `Try` as
  cold even when warm, so a consumer missing its defer branch fails fast
  instead of only when it loses the warm-up race.
