# Initiative: ANGLE on Apple (Mac now, iOS-ready, tvOS/visionOS parked)

**Status:** macOS supply pipeline BUILT + validated (2026-06-03) — vcpkg
build → xcframeworks → vendor + nightly canary, mirroring Windows. iOS supply
BLOCKED on vcpkg (port limitation, see below) — deferred. **cmake-Mac consumer
WIRED + build-verified (2026-06-03)** — auto-detects the xcframework (ANGLE
when present, desktop-GL fallback when absent so the public repo still
builds); both paths compile+link on a real Mac. **Runtime GUI render test
PASSED (2026-06-03, Eric) — SDL3→ANGLE→Metal renders correctly, confirmed
running on ANGLE.** Xcode-Mac consumer still pending (Cocoa rewrite, the real
investment), gated behind `sdl-type-decoupling`.
**Started:** 2026-06-03
**Owner:** Eric

## Goal

Give the Apple platforms a path off Apple's deprecated *system* OpenGL /
OpenGL ES onto ANGLE (GL ES → Metal), without disrupting the platforms
that have no reason to move. Concretely:

- **macOS:** migrate to ANGLE. This is the one with a real *capability*
  driver, not just deprecation (see below).
- **iOS:** keep system GLES at runtime for now, but keep the ANGLE *supply*
  path alive and ready so the migration is one decision away, not one
  project away.
- **tvOS / visionOS:** parked. No ANGLE path planned (see "tvOS/visionOS"
  below and `docs/followups.md` → Graphics / ANGLE).

## Current state (facts established 2026-06-03)

- ANGLE today is **Windows-only** (GL ES → D3D11). No `src/external/mac`
  or Apple ANGLE anywhere in the tree.
- **macOS** (both the cmake/SDL prefab and the Xcode builds) renders through
  Apple's *desktop* OpenGL: `BA_ENABLE_OPENGL 1`, `BA_OPENGL_IS_ES` unset →
  0 (`buildconfig_cmake.h` `__APPLE__` arm; `buildconfig_xcode_mac_common.h`).
- **iOS and tvOS** already render via **GL ES** (`BA_OPENGL_IS_ES 1` in
  `buildconfig_xcode_ios.h` / `buildconfig_xcode_tvos.h`) but through Apple's
  *system* `OpenGLES.framework` / EAGL (and GLKit) — not ANGLE.
- **visionOS** is not a current engine GL target at all (only ios/tvos/mac
  buildconfigs exist; the xrOS slices in `Python.xcframework` are toolchain
  plumbing, not a render target).
- The engine-side renderer (`renderer_gl`) is already ES-capable; the
  Android-only `eglGetProcAddress` branch stays Android-gated and is not
  involved.

### Why macOS has a real driver and iOS does not

The compelling reason for macOS is a **capability gap**, not just
deprecation: Mac desktop GL tops out at GL 4.1 Core with **no ASTC**. The
construct-mode mobile asset flavors (ASTC) therefore can't be used on Mac
desktop GL. ANGLE-on-Metal exposes ASTC on Apple Silicon, closing that gap.

iOS has **no such gap**: iOS GLES 3.0 already exposes ASTC natively (tile
GPUs), so it consumes the exact mobile asset flavors the pipeline already
produces. On iOS the only driver is deprecation, and iOS system GLES is far
more entrenched than Mac's (huge installed base, ~7 years deprecated-but-
working, no removal signal). Hence: migrate Mac, wait on iOS.

## Decisions

1. **Build ANGLE via vcpkg, mirroring Windows** — `vcpkg install
   'angle[metal]:<triplet>'` on a Mac host (fromini). Stick with vcpkg as long
   as we can. NOTE (discovered 2026-06-03): vcpkg's `angle` port only selects
   the Metal ("Mac") buildsystem for `VCPKG_TARGET_IS_OSX`; **iOS triplets
   fall through to the desktop-GL ("Linux") config and do not produce a usable
   Metal library** — so vcpkg builds **macOS only**, not iOS. iOS supply needs
   a patched port or a native gn build (deferred — aligns with the deferred
   iOS runtime migration). This *strengthens* the "vcpkg as long as we can"
   stance for the platforms it serves and pushes the gn question to whenever
   iOS/tvOS/visionOS genuinely come into scope. See "Build-system fork".
2. **Vendor as xcframework(s)**, not loose fat dylibs — matches the existing
   Apple idiom (`Python.xcframework`) and lets Xcode auto-embed + code-sign
   the dylibs. "Consistent with Windows" was the wrong axis: Windows has no
   framework concept, so match the *Apple* side. ANGLE is two dylibs
   (`libEGL` + `libGLESv2`, latter depends on former) → **two** xcframeworks
   (`xcodebuild -create-xcframework` packages slices of *one* library). Both
   embedded in the same `Frameworks/` dir; the inter-dylib `@rpath` resolves
   naturally. Vendor to `src/external/angle-apple/`.
3. **Freshness = build-only nightly canary, manual update** — mirror the
   Windows model exactly: a nightly `angle-mac-build` (analog of
   `angle-windows-build`) that builds to `build/angle-artifacts/` **without**
   the gather/install step, proving "we *can* update" while keeping updating
   a manual `make update-angle-mac` decision. **No** drift-notifier /
   "newer version available" canary for now — may add later.
4. **cmake-Mac is the first consumer**, proving the whole ANGLE-on-Metal
   supply + rendering stack on the public prefab before touching Xcode.
5. **Plan the supply pipeline for iOS now; defer the iOS runtime migration.**
   Include the iOS slice(s) in the xcframework + canary; do **not** do the
   `UIKitGLViewController` rewrite until there's a trigger.

## Supply pipeline (build + vendor) — AS BUILT (2026-06-03)

Structurally identical to Windows + the Python xcframework assembly. Named
`angle-apple-*` (umbrella term; covers macOS now, iOS later) to match
`src/external/python-apple` / `gen_fulltest_buildfile_apple`.

1. `make angle-apple-build` → `tools/cloudshell $(CLOUDSHELL_HOST_MAC_ARM64)
   --env angle-apple --out build/angle-artifacts/ -- make angle-apple-build-local`
   → runs the `build_angle_apple` pcommand (`tools/batools/buildangleapple.py`)
   on fromini, which:
   - clones + bootstraps a throwaway vcpkg;
   - writes **dynamic** overlay triplets (`arm64-osx-dynamic`,
     `x64-osx-dynamic`) — the stock osx triplet is static, but we need
     dylibs; `VCPKG_BUILD_TYPE release` skips the debug build (~2× faster);
   - `vcpkg install 'angle[metal]:<triplet>'` (the `metal` *feature* is
     required for the Metal backend; without it you get the GL backend);
   - assembles per-lib: ANGLE emits `liblibEGL_angle.dylib` /
     `liblibGLESv2_angle.dylib`, which we **rename** to the standard
     `libEGL.dylib` / `libGLESv2.dylib` (so SDL's ES-driver + the engine
     resolve them), `lipo`-merge arm64+x86_64 into one fat dylib, rewrite
     load commands (`install_name_tool`: ids + the `libEGL`↔`libGLESv2`
     cross-ref to `@rpath`, and ANGLE's `@rpath/libz.1.3.2.dylib` →
     system `/usr/lib/libz.1.dylib` to avoid bundling a third dylib), and
     **ad-hoc codesign** (install_name_tool invalidates the linker
     signature; unsigned modified dylibs won't load on Apple Silicon);
   - `xcodebuild -create-xcframework` per lib → header-less
     `libEGL.xcframework` + `libGLESv2.xcframework`, plus a shared
     `include/{EGL,GLES2,GLES3,KHR}` header tree, staged to
     `build/angle-artifacts/`.
2. `make angle-apple-gather` → `install_angle_apple_artifacts` pcommand
   copies `build/angle-artifacts/{include,*.xcframework}` →
   `src/external/angle-apple/`, **committed**. (Analog of
   `angle-windows-gather` / `install_angle_artifacts`.)
3. Nightly canary: `gen_fulltest_buildfile_apple` adds `make
   angle-apple-build` roughly every 11 days (offset from the Windows ANGLE
   day so they don't always coincide) — build-only, no gather, so the
   pipeline stays exercised without auto-updating.

Files: `tools/batools/buildangleapple.py` (the recipe module),
`build_angle_apple` + `install_angle_apple_artifacts` pcommands (public, in
`tools/batools/pcommands.py`), Makefile public `angle-apple-build-local` /
`angle-apple-gather` + private cloud wrapper `angle-apple-build`, cloudshell
`angle-apple` EnvConfig (now syncs the full tools tree so the remote can run
`make env` + pcommand), nightly line in `build.py`.

**Public build-it-yourself path:** the build recipe + install are public
pcommands, so anyone with the source can build the xcframeworks themselves
(`make angle-apple-build-local` then `make angle-apple-gather`) — no
reference to our cloud build architecture (cloudshell/fromini) ships. Only the
`angle-apple-build` cloud wrapper, the cloudshell env, and the nightly canary
(all spinoff-stripped/private) reference our infra.

**iOS-ready by construction:** `buildangleapple.py` groups triplets into
xcframework slices generically (`macos`/`ios`/`ios-sim`) and has the iOS
triplets defined behind `--include-ios`; the moment a working iOS ANGLE build
exists (patched port or gn), its slices drop into the same xcframeworks. The
packaging tail (rename + lipo + create-xcframework + vendoring) is agnostic to
which build system produced the dylibs.

## Keeping ANGLE out of the public repo (2026-06-03)

The vendored binaries must NOT reach public (public macOS cmake builds fall
back to desktop GL). Two independent layers enforce this — note the public
repo does **not** behave like the spinoffs here:

1. **Pubsync exclusion.** The public repo (via pubsync) *commits*
   `src/external/*` binaries (e.g. the Windows ANGLE `.lib`s the public
   Windows build needs) — unlike the bombsquad/spinoff repos, which gitignore
   `/src/external` wholesale. So a new `src/external/<dir>` flows to public by
   default. `src/external/angle-apple` is therefore added to `NO_SYNC_DIRS` in
   `tools/batoolsinternal/pubsync.py` to keep the binaries private. (The build
   recipe `tools/batools/buildangleapple.py` + its pcommands and the initiative
   docs DO go public — they reference no build infra — matching the
   already-public `buildanglewindows.ps1` + existing initiative docs. Only
   the binaries are excluded.)
2. **Prefab forced to desktop GL.** The prebuilt mac prefab binary (what
   public users download) is built via the `ba-cmake-alldeps` cloud env, which
   *does* sync the xcframework (so dev `cmake-cloud-build` can validate the
   ANGLE path). So `_cmake_prefab_gui_binary` passes `-DBALLISTICA_USE_ANGLE=OFF`
   explicitly — public prefab binaries are always desktop-GL and never ANGLE-
   linked (an ANGLE-linked prefab would also be broken, since the prefab ships
   only the binary, not the dylibs).

Gotcha: public-bound `tools/` Python needs the MIT license header
(`# Released under the MIT License. See LICENSE for details.`), not the
internal `# Copyright (c) …` one — pubsync passes it through unchanged and the
public license check enforces it.

## Runtime integration

### cmake-Mac (cheap — SDL does the heavy lifting)

SDL's `SDL_HINT_OPENGL_ES_DRIVER` makes SDL load ANGLE transparently, exactly
as on Windows. Three layers:

1. **Build config (trivial):** `buildconfig_cmake.h` already branches
   `#if __APPLE__` / `#elif __linux__` cleanly. Put `BA_OPENGL_IS_ES 1` in the
   `__APPLE__` arm only; Linux stays at 0 (desktop GL). Gate it on the cmake
   option below.
2. **cmake linking (straightforward):** an `if(APPLE)` block links the ANGLE
   dylib slices from `src/external/angle-apple/*.xcframework/macos-*/`, copies
   them into the staged `.app`'s `Frameworks/`, sets rpath. Linux's `else`
   links nothing extra (system GL).
3. **One real C++ edit (~10 lines):** `app_adapter_sdl.cc` (~line 862)
   currently does `if (platform_macos()) { GL 4.1 Core }` *before* the
   `#if BA_OPENGL_IS_ES` Windows/ANGLE branch, and the Mac arm is **not**
   guarded by the ES flag — so flipping `BA_OPENGL_IS_ES` on Mac alone
   wouldn't take effect. Restructure so the ANGLE ES path
   (`SDL_HINT_OPENGL_ES_DRIVER` + ES 3.0) covers **both** Windows and Mac
   under `#if BA_OPENGL_IS_ES`, with desktop-4.1-Core as the `#else` for Mac:

   ```cpp
   #if BA_OPENGL_IS_ES
       // ANGLE ES via D3D11 (Windows) or Metal (Mac).
       SDL_SetHint(SDL_HINT_OPENGL_ES_DRIVER, "1");
       SDL_GL_SetAttribute(SDL_GL_CONTEXT_PROFILE_MASK, SDL_GL_CONTEXT_PROFILE_ES);
       ... ES 3.0 ...
   #else
       if (platform_macos()) { ...GL 4.1 Core... } else { ...generic... }
   #endif
   ```

**Escape hatch:** wrap layers 1+2 in a cmake option `BALLISTICA_USE_ANGLE`,
default **ON** for Apple, **OFF** for Linux. Drives both the
`BA_OPENGL_IS_ES` define and the lib linking. `-DBALLISTICA_USE_ANGLE=OFF`
reverts a Mac build to the deprecated desktop-GL path (A/B debugging); Linux
never touches ANGLE.

### Xcode-Mac / Cocoa (the real investment — deferred-able)

**Not a drop-in.** The Xcode build doesn't use SDL; `CocoaGLView` subclasses
`NSOpenGLView`, builds `NSOpenGLPixelFormat` + `NSOpenGLContext` (4.1 Core),
presents via `CGLLockContext` / `CGLFlushDrawable` driven by a `CVDisplayLink`.
ANGLE has **no NSOpenGL/CGL integration** — it's EGL-only, rendering into a
`CAMetalLayer`. So `CocoaGLView` needs a rewrite:

- `NSOpenGLView` → plain `NSView` hosting a `CAMetalLayer`
- `NSOpenGLContext`/`NSOpenGLPixelFormat` → `eglGetPlatformDisplay` (ANGLE
  Metal display) + `eglCreateWindowSurface` against the layer +
  `eglCreateContext` (ES 3.0) + `eglMakeCurrent`
- `CGLFlushDrawable` → `eglSwapBuffers` (keep the `CVDisplayLink` driving the
  loop)

Well-trodden (Chromium runs ANGLE-on-Mac this way; SDL's own Cocoa-EGL glue +
ANGLE samples are references), but a genuine rewrite isolated to
`CocoaGLView`. The renderer is unchanged. The two Mac paths can migrate
independently (their context mechanisms — SDL vs Cocoa — are already
separate), so: do cmake-Mac first to prove the stack; keep Xcode on desktop
GL until ready; migrate Xcode reusing the proven binaries + renderer.

### iOS (supply-ready now; runtime deferred)

The iOS GUI path (`UIKitGLViewController.swift`) uses `GLKViewController` +
`GLKView` + `EAGLContext(api: .openGLES3)` — system GLES via GLKit/EAGL
(GLKit itself also deprecated). Migrating would mirror the Cocoa rewrite:
`GLKViewController`/`GLKView`/`EAGLContext` → a `CAMetalLayer`-backed `UIView`
+ EGL. **Deferred** — no capability gap (ASTC already works), high
entrenchment, real cost, and ANGLE adds a translation layer over native GLES.

Migrate iOS only when a trigger fires: (a) we're already doing the Apple GUI
EGL/CAMetalLayer plumbing for Mac and want to knock out UIKit in the same
pass, (b) Apple signals real GLES removal, or (c) an iOS-specific capability
need emerges. Until then: iOS slice stays in the xcframework + canary so the
build path never rots.

## Build-system fork (vcpkg vs gn/depot_tools)

- **Apple scope = macOS (+iOS)** → **vcpkg**, mirrors Windows, one mental
  model. (Current plan.)
- **Apple scope reaches tvOS/visionOS** → vcpkg can't (those aren't vcpkg
  triplets); you'd need ANGLE's native **gn/depot_tools** build with custom
  appletvos/xros toolchain patches. If you go gn for *any* Apple target, go
  gn for *all* — mixing vcpkg + gn slices in one xcframework risks different
  ANGLE commits/flags. The packaging tail is unaffected either way.

Realistically the gn need is low for now (tvOS/iOS can ride Apple GLES a
while; visionOS is a curiosity), so vcpkg is the way as long as we can.

## tvOS / visionOS

No ANGLE path planned. ANGLE officially covers Windows/macOS/Linux/Android/
**iOS** and stops there on Apple — tvOS and visionOS are neither official
targets nor CI'd. tvOS is the awkward one: a shipping GLES target today with
no official ANGLE escape hatch if Apple ever pulls system GLES. Tracked in
`docs/followups.md` → Graphics / ANGLE. Revisit only if GLES removal looms or
tvOS ANGLE support is genuinely wanted.

## Sequencing

1. (Prereq) `sdl-type-decoupling` cleanup lands first.
2. ✅ **DONE (2026-06-03, macOS).** Supply pipeline: `angle-apple-build` +
   vcpkg-on-fromini (macOS slices) + xcframework packaging +
   `src/external/angle-apple/` vendoring + `angle-apple-gather` + nightly
   build-only canary. iOS slices blocked on the vcpkg port limitation
   (deferred). Remaining before this is fully "shipped": run
   `angle-apple-gather` to vendor the first artifacts + commit; propagate the
   `cloudshell.py` env via `make efrosync`.
3. ✅ **DONE (2026-06-03, build-verified).** cmake-Mac consumer:
   `BALLISTICA_USE_ANGLE` cache var (AUTO/ON/OFF, default AUTO = presence-based
   so the public repo without the xcframework falls back to desktop GL);
   `ballisticakit-cmake/CMakeLists.txt` detects the vendored xcframework,
   defines `BA_OPENGL_IS_ES=1`, swaps `OpenGL::GL`→ANGLE dylibs + include dir,
   and POST_BUILD-copies the dylibs next to the binary with an
   `@executable_path` rpath; `gl_sys.h` pulls ANGLE's GLES3 headers
   (`<GLES3/gl3.h>` + `<GLES2/gl2ext.h>`, matching the Windows set — note
   ANGLE ships no `gl3ext.h`); `app_adapter_sdl.cc` takes the ES context path
   on macOS and points SDL at the bundled dylibs via `SDL_HINT_EGL_LIBRARY`/
   `SDL_HINT_OPENGL_LIBRARY` (real-exe-dir resolved, since dev builds symlink
   the staged binary). `src/external/angle-apple` added to the `ba-cmake-alldeps`
   (+`-ex`) cloud envs so cloud builds exercise the ANGLE path. Both ANGLE and
   fallback paths compile+link on fromini; the ANGLE binary links
   `@rpath/libGLESv2.dylib` + `@rpath/libEGL.dylib`. **GUI runtime render test
   PASSED (2026-06-03, Eric ran it) — renders correctly via SDL3→ANGLE→Metal,
   confirmed on ANGLE.** Remaining: explicit ASTC-on-Apple-Silicon validation
   (the original capability driver — exercise a mobile_v1 download + sample).
   The hook now exists: texture-flavor selection is form-factor-first
   (desktop→`desktop_v1`/BC7, mobile→`mobile_v1`/ASTC; see
   `Assets::PreferredTextureProfile`), and `BA_FORCE_TEXTURE_FORM_FACTOR=mobile`
   (`test_game_run --force-texture-form-factor mobile`) runs the mobile/ASTC
   branch on a Mac — ANGLE/Metal exposes ASTC, so this exercises the real ASTC
   download + decode path on desktop. (This is also why the form-factor split
   matters: pre-ANGLE Apple-Silicon Macs landed on `mobile_v1` by accident,
   since GL 4.1 exposed ASTC but not BC7 — exactly the form-factor confusion
   the new selection fixes.)
4. (When ready) Xcode-Mac: `CocoaGLView` → CAMetalLayer + EGL rewrite.
5. (Deferred, on trigger) iOS: first unblock iOS *supply* (patch the vcpkg
   port to select the Metal buildsystem for iOS, or build via gn), then the
   `UIKitGLViewController` → UIView + EGL runtime rewrite.

## References

- Windows precedent: `Makefile` (`angle-windows-build` /
  `angle-windows-gather`), `tools/batools/buildanglewindows.ps1`,
  `install_angle_artifacts` (`tools/batoolsinternal/pcommands.py`),
  cloudshell `angle-windows` EnvConfig, `src/external/windows/`.
- xcframework assembly precedent: `tools/efrotools/python_build_apple.py`
  (~1251), `src/external/python-apple/Python.xcframework`.
- Runtime: `app_adapter_sdl.cc` (~862, ES/ANGLE context),
  `CocoaGLView.swift`, `UIKitGLViewController.swift`, `renderer_gl.cc`,
  `gl_sys.h` (`BA_OPENGL_IS_ES`).
- Related: `docs/initiatives/sdl-type-decoupling.md` (prereq cleanup),
  `docs/followups.md` → Graphics / ANGLE (tvOS gap).
