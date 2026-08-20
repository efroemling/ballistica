# ANGLE on Windows

**Description:** How Windows builds get OpenGL ES 3 via ANGLE/D3D11 — the vcpkg supply pipeline, its gotcha catalog, and the C++/vcxproj/runtime wiring.

All non-VR Windows builds (Generic, Headless, GenericPlus, HeadlessPlus)
render through ANGLE (Almost Native Graphics Layer Engine), which provides
OpenGL ES 3.0 on top of Direct3D 11. This keeps the Windows renderer on the
same GLES code path as mobile instead of maintaining a separate desktop-GL
one. Only VR/Oculus builds still use desktop OpenGL. The prebuilt ANGLE
binaries are checked into the repo; this doc covers how they are produced,
the vcpkg pitfalls hit along the way, and how the engine consumes them.

## Supply pipeline

Two Make targets, run rarely (only when refreshing ANGLE):

1. **`make angle-windows-build`** — runs
   `tools/batools/buildanglewindows.ps1` on the Windows build host via
   `tools/cloudshell` (`--env angle-windows`). The script clones vcpkg,
   builds the `angle` port for the `x64-windows`, `x86-windows`, and
   `arm64-windows` triplets, and stages headers/libs/dlls; cloudshell's
   `--out` pulls the staging tree back to `build/angle-windows-artifacts/`
   locally.

2. **`make angle-windows-gather`** — runs the
   `install_angle_windows_artifacts` pcommand
   (`tools/batoolsinternal/pcommands.py`), which installs from
   `build/angle-windows-artifacts/`:
   - Headers: `include/{EGL,GLES2,GLES3,KHR}` →
     `src/external/windows/include/`
   - Import libs: `lib/{x64,Win32,arm64}/libEGL.lib`, `libGLESv2.lib` →
     `src/external/windows/lib/{x64,Win32,arm64}/`
   - Runtime DLLs: `dll/{x64,Win32,arm64}/libEGL.dll`, `libGLESv2.dll` →
     `src/assets/windows/{x64,Win32,ARM64}/`

   Before installing anything, the pcommand scans each staged DLL's
   imported-dll name strings against an allowlist and fails loudly on
   anything unexpected. vcpkg dependency changes can silently add runtime
   deps we don't ship — in 2026 its zlib dll was renamed `zlib1.dll` →
   `z.dll`, shipping builds that died at load with "z.dll missing". (The
   build script statically links zlib via an overlay triplet precisely to
   avoid this class of problem.)

## vcpkg gotcha catalog

Hard-won; all are baked into `buildanglewindows.ps1`, listed here so nobody
"optimizes" them away:

- **Do NOT clone vcpkg with `--depth 1`.** A shallow clone breaks vcpkg's
  port version resolution, causing cryptic `vcpkg_cmake_configure` errors.
  The script does a full clone.
- **MAX_PATH / `C:\abt\` temp base.** The cloudshell workspace path is
  already ~80 chars; vcpkg's virtualenv pip-wheel extraction creates deep
  subdirectories that blow past Windows' 260-char MAX_PATH — specifically
  for the arm64 triplet. The script roots vcpkg's temp/work dirs at
  `C:\abt\` ("angle build temp") instead of inside the workspace.
- **`vcpkg-cmake` is a host-tool port living in `installed/x64-windows`.**
  Do not delete that directory mid-build; subsequent triplets lose
  `vcpkg_cmake_configure` and fail confusingly.

## C++ wiring

- **`BA_OPENGL_IS_ES`** defaults to `1` for all Windows builds in
  `src/ballistica/shared/buildconfig/buildconfig_windows_common.h`;
  VR/Oculus builds define it to `0` *before* including the common header
  (`buildconfig_windows_meta.h`).
- **`src/ballistica/base/graphics/gl/gl_sys_windows.h`** — under
  `BA_OPENGL_IS_ES` it includes `<GLES3/gl3.h>` + `<GLES2/gl2ext.h>`; all
  core GLES3 functions resolve through the import lib, so none of the
  desktop-GL manual function-pointer loading is needed.
- **`src/ballistica/base/graphics/gl/gl_sys_windows.cc`** —
  `#pragma comment(lib, "libGLESv2.lib")` links ANGLE's GLES import lib.
  It intentionally does **not** link `libEGL.lib`: the engine never calls
  `egl*` itself — SDL creates and manages the EGL context. Both DLLs must
  still be present at runtime (`libGLESv2.dll` depends on `libEGL.dll`).
- **`src/ballistica/base/app_adapter/app_adapter_sdl.cc`** — tells SDL to
  use ANGLE rather than `opengl32.dll`:
  `SDL_SetHint(SDL_HINT_OPENGL_ES_DRIVER, "1")` plus
  `SDL_GL_SetAttribute(SDL_GL_CONTEXT_PROFILE_MASK,
  SDL_GL_CONTEXT_PROFILE_ES)` with GL version 3.0.

## VS project wiring

All non-Meta vcxproj files under `ballisticakit-windows/` (e.g.
`Generic/BallisticaKitGeneric.vcxproj`) pick the artifacts up via:

- `AdditionalIncludeDirectories` includes
  `../../src/external/windows/include` (where the EGL/GLES headers land).
- `AdditionalLibraryDirectories` is
  `../../src/external/windows/lib/$(Platform)` — the import libs are then
  pulled in by the `#pragma comment(lib, ...)` above, so no per-project
  linker-input entries are needed.

## Runtime

`libEGL.dll` and `libGLESv2.dll` ship alongside the executable from
`src/assets/windows/{x64,Win32,ARM64}/`. Nothing loads them explicitly at
startup beyond SDL's `SDL_GL_LoadLibrary(nullptr)` locating `libEGL.dll`
per the ES-driver hint.
