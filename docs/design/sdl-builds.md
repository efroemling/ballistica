# SDL: the adapter boundary and how builds get it

**Description:** How SDL stays confined to the SDL app-adapter behind value-identical BA input types, and the per-platform SDL3 supply and version-bump checklist.

SDL is one of several ways the engine gets a window, a GL context and
input events; most shipping builds (iOS, tvOS, Xcode mac, Android,
Windows headless) do not link it at all. The engine's own code never
handles SDL types. Everything SDL-specific lives in
`base/app_adapter/app_adapter_sdl.{h,cc}`, plus two small gated spots
in core (`core/platform/support/min_sdl.h` for the include and
`sdl_message_box.{h,cc}` for the fatal-error dialog).

## BA input types mirror SDL's values

`shared/foundation/input_types.h` defines the engine's input
vocabulary: `BAKeycode`, `BAScancode`, `BAKeysym`, `BAEvent` and
friends, `BA_BUTTON_*`, `BA_HAT_*`. They are dependency-free and
available in every build.

These types copy the layout and the **values** of the SDL types they
replaced, and that must stay true:

- Keycode and scancode integers are exposed to Python
  (`scene_v1_python`) and stored in input configs, so they cannot
  shift.
- The SDL adapter converts with plain field copies
  (`SDLKeyEventToBA_` and neighbours in `app_adapter_sdl.cc`). If a
  future SDL renumbers something, the fix is a translation table in the
  adapter, never a change to the BA values.

Platform layers that produce input without SDL
(`platform_android.cc`, Apple's `GameControllers.swift` and
`from_swift.cc`) emit BA types directly; Apple builds see the header
through the bridging header. `min_sdl_key_names.h` supplies key names
for builds without SDL.

A cleaner `enum class` redesign of the input types was considered and
set aside: it is a behavior-sensitive change across many build
configs that cannot all be built locally, for no functional gain.

## Which builds have SDL

- `BA_SDL_BUILD` (real SDL linked): the cmake builds (Linux, mac) and
  the Windows GUI projects (Generic, TestBuild, Oculus).
- `BA_MINSDL_BUILD` (no SDL library): iOS, tvOS, Xcode mac, Android,
  Windows headless. The name is historical; these builds once used a
  hand-copied subset of SDL's types, which the BA types replaced.
  (cmake sets both flags.)

`min_sdl.h` stays in `core/` because the fatal-error dialog and the
`main()` arrangements are needed before `base` exists. The input types
live in `shared/` because `shared/ballistica.h` forward-declares them.

## What the adapter still owns

- **Joysticks.** The adapter opens each `SDL_Joystick`, resolves its
  instance id and name, owns the handle, and closes it on the main
  thread; `JoystickInput` receives plain data and is SDL-free.
- **The GL context** (`SDL_GL_*`). SDL owns context creation in SDL
  builds, including the ANGLE/EGL ones, so this stays in the adapter by
  design.
- **Key names** (`SDL_GetKeyName`) in SDL builds.
- **Fullscreen sync.** Fullscreen changes made outside the app (a
  window-manager command, the mac window button) are picked up on
  every platform from `SDL_EVENT_WINDOW_ENTER_FULLSCREEN` /
  `LEAVE_FULLSCREEN`.
- **The fatal-error dialog** on Linux and cmake mac
  (`ShowSDLFatalErrorDialog`); Windows and Xcode mac use native
  dialogs so the dialog works even if SDL never initialized.

Mac-specific behavior does not belong in the adapter; see
`mac-app-platform.md` § "The cmake/SDL mac build stays vanilla".

## Our own main()

We supply `main()` ourselves (`shared/ballistica.cc`, and
`main_rift.cc` for Oculus) rather than using SDL's entry-point shim.
SDL3's header-only shim emits `wmain`/`WinMain` on a UNICODE Windows
build, which does not satisfy our Console-subsystem link (it wants a
plain `main`; the symptom is `LNK2019: unresolved external symbol
main`). So `min_sdl.h` defines `SDL_MAIN_HANDLED` before including
SDL, and the adapter calls `SDL_SetMainReady()` before `SDL_Init`.

## Where SDL comes from

**Linux and mac cmake builds** find a system SDL3 through pkg-config
(`pkg_check_modules(SDL3 REQUIRED IMPORTED_TARGET sdl3)` in
`ballisticakit-cmake/CMakeLists.txt`). Every machine that builds a GUI
cmake target needs SDL3 installed where pkg-config can see it.

**Windows builds** use a copy vendored in the repo (binaries from
SDL's official `SDL3-devel-<version>-VC.zip` release pack). The
vendored headers are SDL 3.4.10
(`src/external/windows/include/SDL3/SDL_version.h`):

- headers: `src/external/windows/include/SDL3/`
- import libs: `src/external/windows/lib/{Win32,x64,arm64}/SDL3.lib`
  (SDL3 has no separate main lib)
- runtime DLLs: `src/assets/windows/{Win32,x64,ARM64}/SDL3.dll`

The arm64 pieces are staged ahead of any arm64 Windows GUI build.

### Version-bump checklist

For a point release, replace the vendored headers, the three
`SDL3.lib` files and the three `SDL3.dll` files, run `make update`
(the asset manifest lists the DLLs), and update the system installs on
the cmake build machines to match. A major-version change also
touches:

- the link pragma in `core/platform/windows/platform_windows.cc`
- the vendored header directory name (the Windows `.vcxproj` files
  add only the `src/external/windows/include` root, and code includes
  `<SDL3/SDL.h>`)
- the DLL name in `tools/batools/staging.py` and the Windows DLL rules
  in `src/assets/Makefile`
- the `pkg_check_modules` name in `ballisticakit-cmake/CMakeLists.txt`
- `min_sdl.h`'s include and every SDL call in `app_adapter_sdl.cc`

Only the cmake desktop and headless builds can be built locally; the
Windows and Oculus builds are checked by CI, and neither CI nor a
headless run sends real keyboard, mouse or controller events through
the adapter. After any bump, run a GUI build by hand and check a
controller, the fullscreen toggle, and a window resize.

