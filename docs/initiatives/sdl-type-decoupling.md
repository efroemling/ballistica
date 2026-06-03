# SDL type decoupling

## Goal

Make the engine's internal input vocabulary independent of SDL, so SDL's
surface area collapses to (effectively) just the SDL app-adapter. This is
the long-documented endgame noted at the top of
`core/platform/support/min_sdl.h`, and a cleanup we want done before the
ANGLE-across-all-platforms work begins.

Today `min_sdl.h` either includes real SDL (`BA_SDL_BUILD`) or, for
non-SDL builds, hand-defines a minimal subset of SDL types
(`SDL_Keycode`, `SDL_Scancode`, `SDLK_*`, `KMOD_*`, `SDL_Keysym`,
`SDL_EventType`, the `SDL_*Event` structs, `SDL_BUTTON_*`, `SDL_HAT_*`).
The engine then passes SDL-typed values around everywhere. We want the
engine to use ballistica-native types instead, with SDL↔native conversion
confined to the SDL boundary.

## Decision (2026-06-03)

**Faithful mirror.** Define global `BA`-prefixed C-style types/enums/structs
that mirror SDL's layout **and values exactly** (e.g. `BAKeycode`,
`BAK_a`, `enum BAScancode { kBAScancode... }`, `BAKeysym`, `BAEventType`,
`BA*Event`, `BA_BUTTON_*`, `BA_HAT_*`). Because values are identical:
- SDL→native conversion at the boundary is near-identity (casts).
- Python-facing keycode/scancode integer values are unchanged (they're
  exposed via `scene_v1_python` and must not shift).
- The engine-wide change is a near-mechanical rename, not an input-model
  redesign (lowest risk for behavior-sensitive input code across many
  build configs we can't all build locally).

(Considered + rejected for now: a modern `enum class` redesign — cleaner
but much higher churn/risk; revisit later as a separate pass if desired.)

## Build-flag matrix (relevant context)

- `BA_SDL_BUILD` (real SDL lib present): cmake, Windows generic/meta/testbuild.
- `BA_MINSDL_BUILD` (no real SDL; used the hand-defined fallback types):
  iOS, tvOS, mac (xcode), Android, Windows-headless. (cmake sets both.)
- `min_sdl.h` lives in `core/` (must, for `SDL_main`/fatal-dialog reasons
  in `main()`), but the **types** must be reachable from `shared/`
  (`shared/ballistica.h` forward-declares `SDL_Event`/`SDL_Keysym`/
  `SDL_Joystick`). So the native types header lives in `shared/`.

## Plan

1. **Native types header** — `shared/foundation/input_types.h`: BA-prefixed
   mirror of `min_sdl.h`'s fallback block, dependency-free, no build-flag
   gating (always available).
2. **Boundary conversions** — SDL app-adapter (`app_adapter_sdl.cc`)
   converts incoming `SDL_Event`→native (near-identity). The platform
   tables that already translate *native platform* input into SDL types —
   `platform_android.cc` (~495 refs), `apple/GameControllers.swift` (~135),
   `from_swift.*` — retarget to BA types directly.
3. **Engine-internal rename** — replace `SDL_*` with `BA*` across the
   SDL-shaped engine vocabulary: `base/input/*` (input, keyboard_input,
   joystick_input, input_device, test_input, remote_app_server),
   `base/ui/{dev_console,widget_message}`, `ui_v1/widget/text_widget`,
   `scene_v1/python/scene_v1_python`, `shared/ballistica.{h,cc}`.
4. **Collapse `min_sdl.h`** — remove the fallback type block (engine uses
   BA types now); keep the `#if BA_SDL_BUILD` real-SDL include for the
   app-adapter/main(). Drop now-unnecessary `BA_SDL_BUILD || BA_MINSDL_BUILD`
   forward-decl gating where it only existed to expose SDL types.
5. **Verify** — `make cmake-build` + `cmake-server-build` locally after each
   chunk; `check-full`; a GUI run; then CI for the platform builds
   (Apple/Android/Windows/Oculus) we can't build locally.

## Status

- [x] Step 1: native types header — `shared/foundation/input_types.h`.
- [x] Step 2: boundary conversions — `app_adapter_sdl.cc` converts
      `SDL_Keysym`→`BAKeysym` and `SDL_Event`→`BAEvent` (joystick) at the
      `PushKey*Event`/`PushJoystickEvent` call sites (field copies; identical
      values). `app_adapter_sdl.h` forward-declares `union SDL_Event;`.
- [x] Step 3: engine-internal rename — explicit word-boundaried recipe
      applied to 24 files (input/*, dev_console, widget_message, text_widget,
      scene_v1_python, platform_android, android/apple adapters, from_swift,
      GameControllers.swift, main_rift, min_sdl_key_names); each includes
      `input_types.h`. Real SDL fns (SDL_Joystick*, SDL_GetKeyName,
      SDL_ShowSimpleMessageBox, SDL_PushEvent) preserved.
- [x] Step 4: collapse min_sdl.h — fallback type block removed (803→71
      lines); only the `#if BA_SDL_BUILD` real-SDL include remains.
      `ballistica.h` now forward-declares `union BAEvent; struct BAKeysym;`
      (un-gated) + keeps gated `SDL_Joystick`.
- [~] Step 5: verify — LOCAL DONE: cmake-build (SDL desktop) + cmake-server
      (headless) compile clean; check-full (cpplint+mypy+pylint+update-check)
      all green. PENDING: CI (Apple/Android/Windows/Oculus = the BA_MINSDL
      path, only buildable on CI); interactive-input GUI smoke (not covered
      by CI — neither CI nor headless exercises real keyboard/mouse/joystick
      events through the new conversion).

## Remaining / follow-ups

- **GameControllers.swift** references the renamed C constants; Apple builds
  expose `input_types.h` via the bridging header — verify on Apple CI.
- **SDL *functions*** — phase-2 (decoupling the *types* is done; functions
  remain). Progress:
  - [x] **Fatal-error dialog** (`SDL_ShowSimpleMessageBox`) — removed from
    shared `CorePlatform`. Now per-OS: Windows native `MessageBoxW`,
    xcode-mac native Cocoa, Linux + cmake-mac via a single gated
    `core/platform/support/sdl_message_box.{h,cc}` (option 3 — keep SDL
    where there's no trivial native dialog). `platform.cc` is now SDL-free.
  - [x] **joystick lib** (`SDL_Joystick*`) — moved out of `joystick_input`
    into `app_adapter_sdl`. The adapter now opens the `SDL_Joystick`,
    resolves instance-id + name (+ XInput fixup), owns the handle (parallel
    `sdl_joystick_handles_`, closed in `RemoveSDLInputDevice_`), and hands
    `JoystickInput` resolved data. `JoystickInput` dropped its `SDL_Joystick*`
    member (`IsSDLController()` → `is_sdl_joystick_` bool) and is now
    SDL-free. Also fixes the awkward cross-thread close (was deferred from
    the logic-thread dtor; now immediate on the main-thread adapter).
  - [x] **`main_rift` quit** — `SDL_PushEvent(SDL_QUIT)` → a direct
    `g_base->QuitApp(false)` (the SDL_QUIT handler did exactly that; the
    idiomatic quit per the codebase's own comments). `SDL_PushEvent` is now
    gone except the adapter's own internal runnable-wake use.
  - [ ] GL context (`SDL_GL_*`) → fold into the ANGLE work (it reworks
    context creation + proc loading anyway).
  - [ ] `SDL_GetKeyName` (app_adapter_sdl; android/apple already use the
    `MinSDL_GetKeyName` fallback) + `SDL_main` glue (build-level; stays).
- Interactive-input GUI smoke (keyboard/mouse/controller) recommended.

## Rename recipe (drives step 3 too)

Apply these `sed -E` substitutions in order (CamelCase types first so the
final catch-all only hits SCREAMING_SNAKE constants):

```
s/SDL_KeyboardEvent/BAKeyboardEvent/g ; s/SDL_TextInputEvent/BATextInputEvent/g
s/SDL_MouseMotionEvent/BAMouseMotionEvent/g ; s/SDL_MouseButtonEvent/BAMouseButtonEvent/g
s/SDL_MouseWheelEvent/BAMouseWheelEvent/g ; s/SDL_JoyAxisEvent/BAJoyAxisEvent/g
s/SDL_JoyHatEvent/BAJoyHatEvent/g ; s/SDL_JoyButtonEvent/BAJoyButtonEvent/g
s/SDL_EventType/BAEventType/g ; s/SDL_Event/BAEvent/g
s/SDL_Keysym/BAKeysym/g ; s/SDL_Keymod/BAKeymod/g
s/SDL_Scancode/BAScancode/g ; s/SDL_Keycode/BAKeycode/g
s/SDLK_/BAK_/g ; s/KMOD_/BA_KMOD_/g ; s/SDL_/BA_/g
```

For step 3 this applies only to the engine-internal files (NOT the SDL
app-adapter, which keeps real SDL + converts at the boundary). Each
converted file then includes `shared/foundation/input_types.h` instead
of `min_sdl.h`.

## Notes / gotchas

- **Values must stay identical to SDL** (Python keycodes + any stored/wire
  values). The mirror enforces this by construction.
- Only cmake (SDL desktop) + headless are locally buildable; Apple/Android/
  Windows/Oculus correctness rides on CI — go incrementally and lean on the
  faithful-mirror (identical values/layout) to keep those low-risk.
- `min_sdl_key_names.h` (key→name table) is part of step 3's rename.

## Windows vendoring — SDL3 swap checklist

The Windows builds do **not** use a system SDL; they link a copy of SDL
vendored in-tree. Currently that's **SDL2 2.28.3**. When the SDL3 upgrade
begins, every item below must move from SDL2 → SDL3 (target **3.4.10**, to
match the system installs now on the GUI build machines — see the
`project_sdl3_installed_build_machines` note). The non-Windows GUI builds
(Linux/mac) instead discover SDL via pkg-config, so their swap is the cmake
`pkg_check_modules` change at the bottom of this list.

Source for the new Windows binaries: SDL's official MSVC pack
`SDL3-devel-3.4.10-VC.zip` from the GitHub release
(`libsdl-org/SDL` → release-3.4.10). Pull `SDL3.lib` + `SDL3.dll`.

**arm64 prep (per Eric, 2026-06-02):** when swapping, if SDL3 ships arm64
Windows binaries, drop them into the arm64 dirs too — even though we don't
build Windows-arm64 yet, we're pre-staging for it. Today `lib/arm64/` holds
only `libEGL.lib`/`libGLESv2.lib` (ANGLE), i.e. arm64 Windows is
headless/ANGLE-only with no SDL. So this is *new* coverage: add
`lib/arm64/SDL3.lib` and an arm64 `SDL3.dll` (under
`src/assets/windows/arm64/` — a new dir) if the upstream pack provides them.

Vendored artifacts (binary blobs in git — swap is `git rm` SDL2 + `git add`
SDL3, not a text edit):

- [ ] **Headers** `src/external/windows/include/SDL2/` (full 2.28.3 tree)
      → SDL3 headers. Note the layout/include convention changes: SDL3 is
      `#include <SDL3/SDL.h>` (dir becomes `include/SDL3/`).
- [ ] **Import libs** `src/external/windows/lib/{Win32,x64}/SDL2.lib` +
      `SDL2main.lib` → `SDL3.lib` **only**. SDL3 drops `SDL2main` (its main
      shim is header-only now). Add `lib/arm64/SDL3.lib` (new — see arm64
      prep above).
- [ ] **Runtime DLL** `src/assets/windows/{Win32,x64}/SDL2.dll` →
      `SDL3.dll`. Add `src/assets/windows/arm64/SDL3.dll` (new — arm64 prep).

Build/code wiring that references the vendored SDL:

- [ ] **Link pragmas** `core/platform/windows/platform_windows.cc:54-55` —
      `#pragma comment(lib, "SDL2.lib")` + `"SDL2main.lib"` (gated
      `#if !BA_HEADLESS_BUILD`) → a single `#pragma comment(lib, "SDL3.lib")`
      (drop the SDL2main line).
- [ ] **MSBuild include dirs** — 8 `.vcxproj` (Generic, GenericPlus,
      Headless, HeadlessPlus, TestBuild, TestBuildPlus, Oculus, OculusPlus),
      `<AdditionalIncludeDirectories>` references `…/external/windows/include/SDL2`
      in all 4 config blocks each → repoint to the SDL3 include dir. Even the
      Headless projects include the SDL header dir (they compile against the
      headers though the lib is `#if !BA_HEADLESS_BUILD`-gated out), so SDL3
      headers must stay present/parseable for headless.
- [ ] **MSBuild lib dir** — same vcxproj,
      `<AdditionalLibraryDirectories>…/external/windows/lib/$(Platform)` —
      path unchanged; it just holds `SDL3.lib` now.
- [ ] **Staging** `tools/batools/staging.py:394` — copies `SDL2.dll` into
      staged GUI builds → `SDL3.dll`.
- [ ] **Asset Makefile** `src/assets/Makefile:5532,5629` — Win32/x64
      `SDL2.dll` staging rules → `SDL3.dll` (+ arm64 rule if pre-staging).
- [ ] **Asset manifest** `src/assets/.asset_manifest_private.json:4299,4863`
      → `SDL3.dll` (regenerated by `make update`).
- [ ] **cmake (Linux/mac, not vendored)**
      `ballisticakit-cmake/CMakeLists.txt:71,91,99` —
      `pkg_check_modules(SDL2 REQUIRED IMPORTED_TARGET sdl2)` + `PkgConfig::SDL2`
      → `sdl3` / `PkgConfig::SDL3` (the pkg-config path fed by the build
      machines' system SDL3).

Biggest behavioral SDL2→SDL3 deltas to expect in `app_adapter_sdl.cc` (the
boundary), separate from this vendoring: the dropped `SDL_main` callback
model, `SDL_Init` flag changes, event-struct field renames, and `SDL_GL_*`
(which dovetails with the ANGLE-across-platforms work).

## SDL3 upgrade — DONE (2026-06-03), CI-green

The SDL2→SDL3 upgrade landed. `smoke` + `fulltest` are green on all three
repos (ballistica-internal, bombsquad, spinoff-template) on **SDL3 3.4.10**.
Commits: ballistica-internal `dc7192af34` (the port + vendoring) +
`59ab4c83fd` (entry-point fix); spinoffs regenerated via
`spinoff-upgrade-push-all`.

What the port touched (real-SDL configs only — MinSDL/Apple/Android/headless
were insulated): event-type renames, flattened key events (`SDL_Keysym`
gone → `event.key.scancode/key/mod`), float mouse/wheel coords, bool return
values, instance-id joystick model (`SDL_OpenJoystick`/`SDL_GetJoysticks`/
`SDL_CloseJoystick`/`SDL_GetJoystickID`/`SDL_GetJoystickName`/
`SDL_SetJoystickEventsEnabled`), `SDL_HideCursor`,
`SDL_GetWindowSizeInPixels`, new `SDL_CreateWindow(title,w,h,flags)` + flags
(`HIGH_PIXEL_DENSITY`, bare `FULLSCREEN`), window events split into
top-level types, `min_sdl.h` → `<SDL3/SDL.h>`, cmake `sdl2`→`sdl3`. GL got a
minimal compile-port keeping BOTH desktop-GL (Linux/mac) and ES/ANGLE
(Windows) paths.

**Entry-point gotcha (the one CI catch — worth remembering):** SDL3's
header-only main shim (`SDL_main.h` → `SDL_main_impl.h`) emits `wmain`/
`WinMain` on a UNICODE Windows build, which does NOT satisfy our
**Console-subsystem** CRT (it wants ANSI `main`) → Oculus smoke failed with
`LNK2019: unresolved external symbol main`. Fix: opt out of SDL's entry shim
with **`SDL_MAIN_HANDLED`** (set in `min_sdl.h` before the SDL includes),
keep our own plain `main()` (`shared/ballistica.cc`; the Oculus
`main_rift.cc` `SDL_main`→`main`), and call **`SDL_SetMainReady()`** before
`SDL_Init` (in `app_adapter_sdl`'s `OnMainThreadStartApp`). `SDL_main.h` is
still included (under `SDL_MAIN_HANDLED`) only for the `SDL_SetMainReady`
declaration.

**Runtime validation (2026-06-03):** Mac GUI build (`make cmake`) launches +
renders fine, and a **game controller works** — which exercises the biggest
behavioral rework (SDL3 instance-id joystick model + renamed open/close/name
calls + `down`-vs-`state` button field). So window/GL/event-loop + the
joystick path are runtime-confirmed, not just CI-green. Minor remaining
spot-checks: fullscreen toggle (Alt+Enter / Mac window-widget) and vsync;
plus a Linux GUI run for completeness. The Mac fullscreen-via-window-widget
path still maps MAXIMIZED/RESTORED; SDL3 has dedicated `ENTER/
LEAVE_FULLSCREEN` events worth switching to once verified (TODO left in
`app_adapter_sdl.cc`).
