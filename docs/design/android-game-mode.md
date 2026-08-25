# Android Game Mode & Frame Rate Governance

**Description:** How the Android client escapes the OS's 60hz game cap and runs at native display rate, with battery-game-mode and thermal back-off layered on one frame-rate vote, plus the GameState loading-boost wiring.

Shipped 2026-08-25. All device verification below was done on a Pixel
7a (90hz panel, Android 17).

## The one mental model: we vote, the platform clamps

`Surface.setFrameRate()` is a **vote**, not a command. SurfaceFlinger
arbitrates it against everything else — Battery Saver (clamps policy
to 60), the user's Smooth Display setting, per-game FPS caps set in a
Game Dashboard (`gameModeOverride`), thermal policy, and the
game-default cap. Effective rate ≈ min(our vote, user overrides,
system policy). Every design decision below leans on this: each layer
only expresses intent, and interactions can't conflict because they
all funnel through one arbiter.

Without any vote, Android 15+'s *game default frame rate* feature caps
apps declared `android:appCategory="game"` at a device-configured
default (60 on Pixels: `ro.surface_flinger.game_default_frame_rate_override`)
even when the panel runs faster. An explicit non-zero vote exempts us.
That cap was why BombSquad ran 60fps on 90hz devices.

## The vote function

All frame-rate inputs funnel into a single function —
`BallisticaActivity.applyPreferredFrameRate()`:

- target = display peak (max of the current mode's
  `getAlternativeRefreshRates()` + current rate; never hardcoded);
- capped to 60 when the user chose **battery game mode**;
- capped to 60 while our **thermal back-off** is engaged;
- applied via `setFrameRate(target, FRAME_RATE_COMPATIBILITY_DEFAULT,
  CHANGE_FRAME_RATE_ALWAYS)` (3-arg API 31+, 2-arg API 30, no-op
  below).

Callers: surface creation (a `SurfaceHolder.Callback` on the
GLSurfaceView holder, so recreation re-applies), `onResume()` (game
mode can change while backgrounded; there is no change-callback API),
and thermal transitions. Each application logs
`Requested surface frame rate <N> (constraints)` at Log.v.

Decisions:

- **Standard mode = native rate, not 60.** 90hz is a real feel win in
  action gameplay; battery-conscious users already have three dials
  (battery game mode, Battery Saver, Smooth Display off) that all
  still work via arbitration.
- **Performance mode = standard for now** — a hook awaiting a meaning
  (e.g. pairing with a higher quality tier).
- **No custom-FPS plumbing of our own.** Dashboard per-game FPS caps
  are enforced by SurfaceFlinger *beneath* our vote; reading them via
  `getGameModeInfo()` would add a second source of truth with nothing
  to do. We keep `allowGameFpsOverride="true"` so they work.
- The engine paces off actual vsync and uses display-time, so no
  engine-side changes were needed for 90hz.

## Thermal back-off (deliberately conservative)

`PowerManager.addThermalStatusListener` (API 29+, registered in
activity onCreate). Cap engages **immediately at SEVERE+** — not
MODERATE, which fires too readily on some OEMs (warm pocket,
sunlight); we only shed frames under real pressure. Recovery requires
status to stay at **LIGHT or below for a sustained 60s dwell**; a
bounce to MODERATE cancels the pending recovery (hysteresis — a
status hovering at a boundary can't flap us between rates).

Why act at all when the OS already handles thermals: the OS sheds
heat by clawing back clocks (skin-temp tiers in the vendor
powerhint.json), which at a 90fps target degrades into missed-frame
jitter. Proactively dropping to 60 instead gives a stable cadence and
cuts render work ~1/3. Frame rate is the biggest power knob we hold.

## Game Mode declaration

`res/xml/game_mode_config.xml` (+ `android.game_mode_config`
meta-data; two legacy boolean meta-data entries cover Android 12):
declares battery+performance support, `allowGameDownscaling="false"`
(we manage our own render resolution), `allowGameFpsOverride="true"`.
Declaring support transfers responsibility: the platform then applies
no interventions of its own for those modes and trusts us to adjust —
so the declaration and the mode handling must ship together.

Game Mode APIs are pure framework (`android.app.GameManager`) — no
Play Services dependency, identical in generic and Google flavors, no
minSdk impact (runtime-guarded; ART soft-fails unexecuted references).

## GameState loading boost

Java flips `GameManager.setGameState(GameState(loading, MODE_NONE))`
(API 33+) **on** when kicking off native init
(`BallisticaContext.updateNativeState()`), and the engine sends the
typed-bus message `SetGameLoading(false)` from
`PyMarkConstructAssetsComplete` when the construct-mode asset gate
opens — the same hand-off point the asset gate keys on. Platform hook:
`Platform::SetOSGameLoadingState()` (no-op default, Android override
sends the bus message).

Reality check: the boost only helps devices whose Power HAL wires the
`GAME_LOADING` power mode — the Pixel 7a does **not** (its
powerhint.json has no entry; its generic 5s LAUNCH boost covers app
start regardless), and Samsung's GOS boosts loading via its own
detection. Treat it as truthful state reporting that pays off where
vendors consume it, not a measurable win today. Loading windows longer
than any boost duration are fine — vendor tables time-box their own
actions.

## Measuring frame rate (verification tooling)

Engine side: `a.fps()` in `babase._automation` /
`_babase.get_last_fps()` — frames rendered over the last one-second
stats window (tracked whether or not the on-screen 'Show FPS' display
is enabled; 0 in headless). System side + forcing modes/thermal states
via adb: recipes live in the `/baclient` skill ("Frame rate / Game
Mode / thermal"). Verified end-to-end: standard=90 / battery=60 /
SEVERE→60 instantly / recovery→90 only after the 60s dwell; presented
frames via SurfaceFlinger timestats moved 603→903 per 10s.

## Deferred

- Richer GameState gameplay modes (interruptible / uninterruptible /
  content) — cheap on the existing bus pattern; no confirmed consumers.
- Battery mode shedding render *quality* in addition to frame rate.
- ADPF performance hint sessions / CPU-GPU headroom — only if
  thermal/frame-time behavior becomes a real topic.
- iOS sibling: ProMotion iPhones default to 60 similarly, cured via
  `CADisplayLink.preferredFrameRateRange` — separate platform, same
  shape.
- API 30 (2-arg setFrameRate) and sub-31 paths verified by inspection
  only; populations tiny, guards trivial.
