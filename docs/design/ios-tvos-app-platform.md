# iOS / tvOS app platform

**Description:** How the UIKit shell hosts the engine on iOS/tvOS — render/lifecycle/input wiring, staging build phases, the GIL-leaf-lock rule, and per-config verification.

iOS and tvOS run the engine inside a small UIKit/Swift shell that lives in
`src/ballistica/base/app_platform/apple/` and is built by the Xcode project
(`ballisticakit-xcode/BallisticaKit.xcodeproj`). This doc covers how that
shell is wired to the engine, the build/staging pieces that make the app
bundle work, the lifecycle and input model, and the invariants and
verification rules that keep the platform healthy.

## Engine wiring: view controller drives everything

`UIKitAppDelegate` is deliberately a no-op; the engine's entry point is
`UIKitGLViewController`'s per-frame render callback, mirroring the Mac shell's
`CocoaGLView.renderFrame`:

- The **first frame** triggers `UIKitSupport.shared.startEngine()` (which
  calls `ballistica.MonolithicMain`); `UIKitSupport.startEngine` guards
  against repeat calls.
- Once the engine reports inited, each frame ships
  `from_swift.SetScreenResolution(w, h)` on drawable-size change and calls
  `from_swift.TryRender()`.

tvOS compiles the *same* `UIKitGLViewController`/`UIKitSupport`/
`app_adapter_apple.cc` sources as iOS — one shared shell, two targets (see
the `#if os(iOS)` rule below).

## Staging build phases

Both the iOS and tvOS Xcode targets have a `Staging` shell-script build phase
that runs `tools/pcommand stage_build -xcode-ios` / `-xcode-tvos` (the two
modes are folded together in `tools/batools/staging.py` since they're
identical). This copies `ba_data` and the Python stdlib (`pylib`, from
`pylib-apple`) into the app bundle — without it the engine has assets but no
interpreter runtime.

Both targets set `ENABLE_USER_SCRIPT_SANDBOXING = NO` (Debug and Release):
Xcode's build-script sandbox otherwise blocks the staging script from writing
`pylib` into the `.app`. Note that configs with *no explicit value* inherit
the sandboxing default, so a new target needs this set explicitly.

## App lifecycle: two orthogonal axes

`UIKitSceneDelegate`'s scene callbacks feed `UIKitSupport` bookkeeping, which
calls three `from_swift` entry points — `SetAppActive(bool)`, `SuspendApp()`,
`UnsuspendApp()` — mirroring Android's running/active model:

- **running** (`sceneWillEnterForeground` / `sceneDidEnterBackground`, the
  analogue of Android onStart/onStop) → `UnsuspendApp()` / `SuspendApp()`.
  `SuspendApp` parks all event-loop threads; the audio thread's suspend
  callback calls `alcDevicePauseSOFT`, which is what actually stops audio.
  The `CADisplayLink` is also paused
  (`UIKitGLViewController.setRenderingPaused`) so no GPU work happens in the
  background.
- **active** (`sceneWillResignActive` / `sceneDidBecomeActive`, the analogue
  of onPause/onResume) → `SetAppActive(bool)` → logic thread → Python
  `AppMode.on_app_active_changed`. Pauses gameplay while the app keeps
  running and rendering.

iOS delivers resign-active *before* background (and foreground before
become-active), which matches the engine's expectation that app-active goes
false before a suspend (`SuspendApp` waits on that).

A key fact this design leans on: **the engine boots unsuspended and active on
all platforms** (`app_suspended_` false, `app_active_` true in `base.h`).
`UIKitSupport` seeds its applied-state to match, so a clean launch makes
*zero* lifecycle calls — only real transitions fire. (Android instead seeds
its native running-state false and emits a benign no-op `UnsuspendApp` at
boot; the iOS shell avoids that.)

Files: `app_platform/apple/{from_swift.h,from_swift.cc,UIKitSupport.swift,UIKitSceneDelegate.swift,UIKitGLViewController.swift}`.

## Input

- **Touch:** `UIKitGLViewController` overrides
  `touchesBegan/Moved/Ended/Cancelled` (with `isMultipleTouchEnabled` set)
  and forwards multitouch via `from_swift::PushTouchEvent` →
  `Input::PushTouchEvent`, mirroring Android's `NativeTouchEvent`. Per-finger
  identity is the `UITouch` pointer; coordinates are normalized and y-flipped
  to bottom-left; an `overall` flag marks the final finger-up.
- **Gyro / device-motion** (the subtle camera/UI tilt) is owned by the
  **`babase` Input subsystem**, not graphics: Input owns sampling,
  integration, decay, the wonky-gyro health check, and the 'Disable Camera
  Gyro' setting; camera, UI widgets, and scene nodes read
  `g_base->input->tilt()`, and only the camera-shift *math* stays in
  graphics. On iOS a `CMMotionManager` in `UIKitGLViewController` feeds
  `from_swift::PushGyroEvent` (pull API, read per-frame in the render
  callback, orientation-corrected via `windowScene.interfaceOrientation`,
  sampling stopped when backgrounded). Android's equivalent is
  `PlatformAndroid::OnGyroEvent` → `input->PushGyroEvent`.

## The GIL-leaf-lock invariant

The Python GIL must be a **leaf lock**: never block on a cross-thread wait
while holding it. This is the dual of the asset system's GIL invariant, and
iOS is where violating it bites hardest — the classic failure is a
**cold-launch A↔B deadlock**: a Swift device-identity getter doing a blocking
`DispatchQueue.main.sync` from the logic thread (which holds the GIL during
`OnAppStart`) while the main thread is parked in
`EventLoop::PushCallSynchronous` waiting on that same startup. Result: black
screen on first launch, including production installs.

Mitigations now in place:

- Device identity (`getLegacyDeviceUUID`/`isTablet`/`getDeviceName`) is
  cached once on the main thread at launch
  (`UIKitFromCpp.cacheDeviceIdentity()`, called from
  `UIKitSupport.startEngine`); the getters return cached values with no
  main-thread hop.
- Two debug-only (`#if BA_DEBUG_BUILD`) guards make future violations fail
  loud instead of hanging silently:
  1. `EventLoop::PushRunnableSynchronous` FatalErrors if `Python::HaveGIL()`
     (`PyGILState_Check`).
  2. Swift `UIKitFromCpp.onMain` calls
     `from_swift::CheckMainThreadHopSafe()`, which FatalErrors if hopping to
     the main thread while holding the GIL.

## The `#if os(iOS)` rule (and how to verify)

**Any iOS-only API used in the shared Apple view-controller/support files
must be guarded with `#if os(iOS)`** — the same sources compile for tvOS,
which lacks (among others) `prefersStatusBarHidden` /
`prefersHomeIndicatorAutoHidden`, the entire CoreMotion framework (Apple TV
motion is GameController/`GCMotion`), `UIWindowScene.interfaceOrientation`,
and `isMultipleTouchEnabled`.

Verification requires **both** `make ios-build` **and** `make tvos-build`.
`make cmake-build` compiles *none* of this code — the Swift sources and the
`BA_XCODE_BUILD`-gated C++ (e.g. `from_swift.cc`) only build under Xcode —
so a cmake-green change can still break either Apple target.

## Verify Release, not just Debug

Xcode Debug and Release configurations can genuinely diverge, and Swift
compilation conditions are the sharp edge: `SWIFT_ACTIVE_COMPILATION_CONDITIONS`
is per-config in the `.pbxproj` and entirely separate from any C++
prefix-header `#define` of the same name. Historically the iOS **Release**
config was missing `BA_USE_ANGLE` from its Swift conditions while Debug had
it — so Debug rendered through ANGLE fine while every shipped release build
compiled the dead GLKit fallback branch and crashed at launch. (That GLKit
fallback path has since been deleted entirely, but the lesson generalizes:
dead `#else` code paths hide in the configs you don't run.) **Always verify
the shipping configuration (Release), not just Debug**, and prefer making
mismatches fail at compile time (`#error` in unreachable branches) over
letting them ship.

Related `.pbxproj` notes: simulator builds exclude x86_64
(`EXCLUDED_ARCHS[sdk=iphonesimulator*]` / `appletvsimulator`) since the
arm64-only xcframeworks can't link Intel slices; and after any hand-edit of
the `.pbxproj`, run `make update` so `update_project` canonicalizes it
(otherwise `update-check` fails).

Orientation gotcha, since it always surprises: the `UIInterfaceOrientation`
landscape constants are named opposite to intuition — `LandscapeRight`
renders with the home bar on the *left*, `LandscapeLeft` with it on the
*right*. iPhone is pinned landscape-only via
`INFOPLIST_KEY_UISupportedInterfaceOrientations_iPhone`; iPad keeps all four
orientations (staying resizable). The status bar and home indicator are
hidden via view-controller overrides (`prefersStatusBarHidden`,
`prefersHomeIndicatorAutoHidden`) — the Info.plist `UIStatusBarHidden` key
only covers launch under the VC-based-appearance default.

## Running, deploying, and capturing logs

Simulator build/run targets and their semantics (`make ios-build` vs
`make ios`, etc.) are covered in the client tooling docs; the
platform-specific pieces worth knowing:

- **On-device deploy** goes through `xcrun devicectl`: build the device
  target (`-destination 'platform=iOS,id=<udid>' -allowProvisioningUpdates`),
  then `xcrun devicectl device install app --device <udid> <.app|.ipa>` and
  `xcrun devicectl device process launch --console --terminate-existing
  --device <udid> <bundle-id>`. A crash prints its trace (faulthandler /
  `BALLISTICA-NATIVE-STACK-TRACE`) to the `--console` stream, and device
  crashes also sync to `~/Library/Logs/CrashReporter/MobileDevice/<device>/`.
- **Log capture** uses os_log: `PlatformApple::EmitPlatformLog` routes engine
  logs to os_log (subsystem `net.froemling.ballistica`, category `engine`)
  plus stderr. From a simulator:
  `xcrun simctl spawn <device> log show --last 2m --debug --info
  --predicate 'subsystem == "net.froemling.ballistica"'` (or `log stream`).
  Note `simctl launch --console[-pty]` does *not* capture the sim app's
  stderr — os_log is the reliable channel.

### Simulator build/launch recipe (verified 2026-06-18)

For a no-signing sim smoke-test, build for a simulator destination
(the device-targeting `make ios-build` uses `-allowProvisioningUpdates`):

```bash
make ios-staging                              # deps: assets-ios, resources, codegen, discord
tools/pcommand xcodebuild -project ballisticakit-xcode/BallisticaKit.xcodeproj \
    -scheme "BallisticaKit iOS" -configuration Debug \
    -destination 'platform=iOS Simulator,name=iPhone 17' \
    -derivedDataPath build/ios_sim_dd build
xcrun simctl boot "iPhone 17"
open -a Simulator                             # unsandboxed (GUI)
APP=build/ios_sim_dd/Build/Products/Debug-iphonesimulator/BallisticaKit.app
xcrun simctl install booted "$APP"
xcrun simctl launch booted com.ericfroemling.ballisticakit
xcrun simctl io booted screenshot build/tmp/ios_sim_shot.png
```

Bundle id: `com.ericfroemling.ballisticakit`. tvOS mirrors this with
`make tvos-staging`, scheme `"BallisticaKit tvOS"`, destination
`platform=tvOS Simulator,name=Apple TV 4K (3rd generation)`.
`simctl boot/install/list` work *sandboxed*; only the GUI
`open -a Simulator` and console/pty attaches need unsandboxed.

For intermittent launch crashes, a Release cold-launch loop (alive after
~7s == booted past GL init):

```bash
tools/pcommand xcodebuild -project ballisticakit-xcode/BallisticaKit.xcodeproj \
    -scheme "BallisticaKit iOS" -configuration Release \
    -destination 'platform=iOS Simulator,id=<udid>' \
    -derivedDataPath build/ios_sim_rel_dd build
D=<udid>; B=com.ericfroemling.ballisticakit
xcrun simctl install $D build/ios_sim_rel_dd/Build/Products/Release-iphonesimulator/BallisticaKit.app
for i in $(seq 1 15); do xcrun simctl terminate $D $B; xcrun simctl launch $D $B; sleep 7; \
  xcrun simctl spawn $D launchctl list | grep -qi ballisticakit && echo "$i alive" || echo "$i CRASH"; done
```
