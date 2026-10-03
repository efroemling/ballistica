# Android Game Mode & Frame Rate Governance

**Description:** How the Android client escapes the OS's 60hz game cap and runs at native display rate, with battery-game-mode and thermal back-off layered on one frame-rate vote, plus the GameState loading-boost wiring.

Shipped 2026-08-25. All device verification below was done on a Pixel
7a (90hz panel, Android 17). A Pixel-green run proves nothing for other
OEMs: the Pixel idles at its peak rate, so it never exercised the
peak-selection or display-mode-request paths that the 2026-09-10 Realme
field report broke on (see "The vote function").

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

- target = display peak (max refresh rate over `getSupportedModes()`
  at the current mode's resolution, plus the current rate; never
  hardcoded). **Not** `getAlternativeRefreshRates()`: that lists only
  *seamless* alternatives, and on devices whose 60↔120 switch is a
  non-seamless mode change (ColorOS/MediaTek — a Realme narzo 70 Turbo
  on Android 16 was the field report, 2026-09-10) it comes back empty,
  so the original code voted for whatever rate the panel was idling at
  (60) and only ever reached 120 when SystemUI's own vote dragged the
  display up (notification shade open). Since we pass
  `CHANGE_FRAME_RATE_ALWAYS`, non-seamless switches are permitted, so
  the peak must be computed over the same set;
- capped to 60 when the user chose **battery game mode**;
- capped to 60 while our **thermal back-off** is engaged;
- applied via `setFrameRate(target, FRAME_RATE_COMPATIBILITY_DEFAULT,
  CHANGE_FRAME_RATE_ALWAYS)` (3-arg API 31+, 2-arg API 30, no-op
  below);
- **and** as a window-level mode request: `WindowManager.LayoutParams
  .preferredDisplayModeId` set to the fastest mode at the current
  resolution not exceeding the target (so caps pick the 60 mode).
  Added 2026-09-10 for the Realme field report: that phone accepted
  a 120 surface vote and kept the whole display at 60 anyway (only
  another app's window on top pulled it to 120). The surface vote is a
  per-layer preference some OEM display policies ignore for games; the
  window mode request goes through display-mode arbitration, which is
  the path most engines rely on for 120hz on those devices. Confirmed
  on that phone the same day: with the mode request in, its report
  showed the display at 120 within 3s of the vote and holding at +60s,
  and the user saw 120hz in play. (Its reports also showed the OEM
  reporting thermal SEVERE for a few seconds at every launch, which is
  what motivated the engage dwell below.)

Callers: surface creation (a `SurfaceHolder.Callback` on the
GLSurfaceView holder, so recreation re-applies), `onResume()` (game
mode can change while backgrounded; there is no change-callback API),
and thermal transitions. Each application logs
`Requested surface frame rate <N> (constraints) (current R, supported
at WxH: ...)` via BaLog at INFO on the engine's `ba` logger (so it is
capturable by client log reports; enable `ba=INFO` to see it locally).

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
activity onCreate). Cap engages once status has held at **SEVERE+ for
a sustained 10s dwell** — not MODERATE, which fires too readily on
some OEMs (warm pocket, sunlight); we only shed frames under real
pressure. Recovery requires status to stay at **LIGHT or below for a
sustained 60s dwell**; a bounce to MODERATE cancels whichever dwell is
pending (hysteresis — a status hovering at a boundary can't flap us
between rates). The engage dwell was added 2026-09-10 after a Realme
narzo 70 Turbo (Android 16) reported SEVERE the instant the app
launched and cooled to NONE within a minute; an instant cap there
held 60hz for the whole recovery dwell on a cool phone.

**Player notice.** When the cap engages, Java sends the typed-bus
message `ThermalFrameRateCapNotice` and the engine shows the
`babuiltinassets` string `strings/device/thermal_frame_rate_cap`
("Device is running hot; frame rate reduced to 60 until it cools.")
as a screen message. Gating, all Java-side: at most once per run, only
on the engage transition (never on recovery), and only when the cap
actually lowers our vote — i.e. the display's peak rate at the current
resolution exceeds 60. On a 60hz panel the cap is a no-op and the
notice would be noise. A launch that comes up already capped shows it
too (after the engage dwell): the player expecting their 120hz panel
deserves the same explanation whether or not they saw a drop.

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
