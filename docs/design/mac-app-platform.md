# Mac app platform

**Description:** How the Cocoa shell reports lifecycle on the xcode mac build — why app-active follows window visibility while keep-awake follows frontmost, and why those two axes must not be merged.

Scope is the **xcode** mac build (`CocoaAppDelegate`, `CocoaSupport`,
`CocoaGLView`). The cmake mac build is SDL-driven and goes through
`app_adapter_sdl.cc` instead; where the two must agree is called out below.
The iOS/tvOS shell is a separate document (`ios-tvos-app-platform.md`), as
are the Swift-6 concurrency conventions shared by both
(`apple-swift-concurrency.md`).

## Two lifecycle axes that are not interchangeable

`CocoaAppDelegate` feeds two different signals into `CocoaSupport`. They
look like the same "is the app in use?" question and are not. **Don't
unify them** — the asymmetry is the point.

| | Driven by | Used for |
|---|---|---|
| **app-active** | `applicationDidHide`/`Unhide` + `windowDidMiniaturize`/`Deminiaturize` | engine app-active state |
| **keep-awake** | `applicationDidBecomeActive` / `applicationDidResignActive` | display-sleep assertion |

### app-active follows window visibility

`CocoaSupport.setHidden` / `setMiniaturized` → `applyAppActive` →
`from_swift.SetAppActive` → logic thread → Python
`AppMode.on_app_active_changed`.

It follows **visibility, not focus**: cmd-tabbing to another app leaves a
game running. That much matches the SDL builds, which drive the same state
from `SDL_EVENT_WINDOW_HIDDEN` / `SDL_EVENT_WINDOW_SHOWN`
(`app_adapter_sdl.cc`) — deliberate parity, since these are two shells for
the same product and "active" meaning different things in each would be a
trap.

**Where we deliberately diverge from SDL: miniaturizing.** A window in the
dock is every bit as invisible as a hidden app, and leaving a game running
behind it is the exact thing this axis exists to prevent, so
`windowDidMiniaturize`/`windowDidDeminiaturize` feed the same state.

SDL reports this differently, and not by omission: its cocoa backend emits
HIDDEN from a KVO observer on the window's `visible` property explicitly
guarded with `![_data.nswindow isMiniaturized]`
(`src/video/cocoa/SDL_cocoawindow.m` 886-888 and 905-907 in 3.4.16), so
miniaturize delivers `MINIMIZED` alone while deminiaturize delivers
`RESTORED` *and* `SHOWN`. `app_adapter_sdl.cc` originally ignored
MINIMIZED outright, so a minimized SDL build kept playing; it now tracks
`hidden_`/`minimized_` as two flags and derives app-active from both,
mirroring `applyAppActive` here (see `docs/followups.md` for the event
asymmetry and the `RESTORED`-overload trap). Both mac builds therefore
agree again as of 2026-09-23 — they just learn about it through different
events.

The semantics are user-visible, which is why the choice matters: baclassic's
`on_app_active_changed` calls `request_main_ui()` when going inactive, which
pauses the action and pops up the main UI. Wiring this to frontmost instead
would mean cmd-tabbing away pauses your game.

Three implementation notes:

- **Both conditions must clear** before going active again — `applyAppActive`
  computes `!hidden && !miniaturized`. Cmd-H'ing an already-miniaturized
  window and then unhiding must not resume play.
- The applied state is tracked and seeded `true`, matching the engine's boot
  state (`app_active_{true}` in `base.h`). A clean launch therefore pushes
  nothing. The engine logs a warning when fed the same state twice running,
  so the seeding is load-bearing, not tidiness.
- The `from_swift` bridge drops calls arriving before the engine is up.
  That's safe here rather than merely tolerable: the engine is started from
  the draw path, so it cannot come up while the app is hidden or
  miniaturized.

Before 2026-09-23 the xcode mac build reported app-active **not at all** —
only SDL, Android and UIKit did. If you are chasing a "why didn't the game
pause" report against an older mac build, that's why.

### keep-awake follows frontmost

`CocoaSupport.setFrontmost` holds a `ProcessInfo.beginActivity` assertion
with `[.userInitiated, .idleDisplaySleepDisabled]` while the app is
frontmost, so the display doesn't sleep during idle gameplay — someone on a
gamepad, or just watching a match, generates no input to reset the idle
timer.

**Unlike iOS, macOS does not scope this to the frontmost app.** An activity
assertion holds process-wide until explicitly ended, so releasing it on
resign-active is required, not decoration.

Frontmost is the strictly tighter of the two signals — hiding an app also
deactivates it, so `hidden ⇒ not frontmost`, and gating on both would add a
condition that is never independently false. Tighter is what keep-awake
needs: a merely *visible* window, sitting on a second display while the user
works elsewhere and then walks away, is not reason enough to pin someone's
display on. Driving keep-awake off app-active would silently reintroduce
exactly that case.

Transient deactivations (Spotlight, Mission Control) do briefly release the
assertion. That's harmless — the idle timer runs in minutes, and the input
that summoned Spotlight resets it — and not worth adding hysteresis for.

## The cmake/SDL mac build stays vanilla

The cmake/SDL Mac build uses SDL exactly as Windows/Linux do;
Mac-specific polish belongs in the Xcode (Cocoa) builds. Three Mac cases
in `app_adapter_sdl.cc` are sanctioned and stay: the 0.35 mouse-wheel
multiplier, the GL 4.1 Core profile request on the desktop-GL fallback
(when ANGLE isn't bundled), and the bundled-ANGLE dylib path hints
(`SetAngleLibPaths_()`).

## Verifying lifecycle changes

Both axes are observable from outside the process, so check them rather
than reasoning about them:

- **keep-awake**: `pmset -g assertions` lists the live assertion by owning
  pid and reason (ours reads `"Game is frontmost"`), plus a
  `PreventUserIdleDisplaySleep` count. This is ground truth — better than
  any in-app readback.
- **app-active**: run with `--log 'ba.lifecycle=INFO'` and watch for
  `app-active is now True/False` (`logic.cc`). A
  `SetAppActive called with state ... twice in a row` warning means the
  applied-state tracking has drifted.

Driving the transitions needs a real focus change, which the Claude sandbox
cannot synthesize — `osascript` fails with LaunchServices `-10810` and
`open -a <bundle>` is not on the unsandboxed whitelist. Hiding via cmd-H and
restoring via the dock icon by hand is the practical route.

Files: `app_platform/apple/{CocoaAppDelegate.swift,CocoaSupport.swift}`,
`app_platform/apple/{from_swift.h,from_swift.cc}`,
`app_adapter/app_adapter_sdl.cc` (the parity reference).
