# Apple Python build

**Description:** How Apple platforms get their embedded interpreter — the 10-slice static `python_build_apple.py` build, XCFramework assembly, and the cross-compilation gotcha catalog.

## Overview

`tools/efrotools/python_build_apple.py` — self-contained static Apple Python
build. Builds 10 slices into `build/python_apple_<slice>/libpython_merged.a`,
then assembles a `Python.xcframework` via
`xcodebuild -create-xcframework -library`.

Fleet-wide Python-version wiring (which interpreter each platform/CI target
gets, and the yearly bump runbook) lives in efrohome
`docs/global_design/python-wiring.md`; this doc is the Apple build-internals
reference.

## Commands

- `make _python-apple-build-<slice>` — build one slice (e.g.
  `_python-apple-build-macosx-arm64`)
- `make python-apple-gather` — lipo-merge + XCFramework + copy to project
- `make python-apple-build` — all 10 slices + gather

## The 10 slices

macosx.arm64, macosx.x86_64, iphoneos.arm64, iphonesimulator.arm64,
iphonesimulator.x86_64, appletvos.arm64, appletvsimulator.arm64,
appletvsimulator.x86_64, xros.arm64, xrsimulator.arm64

## Output

- `src/external/python-apple/Python.xcframework` — 7-slice XCFramework
  (simulator pairs lipo-merged): macos-arm64_x86_64, ios-arm64,
  ios-arm64_x86_64-simulator, tvos-arm64, tvos-arm64_x86_64-simulator,
  xros-arm64, xros-arm64-simulator
- `src/assets/pylib-apple/` — Python 3.14 stdlib (.py files + per-platform
  sysconfigdata)
- Old artifacts: `src/external/python-apple-old/` (legacy dynamic framework
  approach)

## Version constants (`python_build_apple.py`, ~line 55; verified 2026-07-10)

- PY_VER = '3.14', PY_VER_EXACT = '3.14.6'
- BEEWARE_BRANCH = '3.14'
- OpenSSL 3.5.7-1, libffi 3.4.7-2, XZ 5.6.4-2, bzip2 1.0.8-2,
  mpdecimal 4.0.0-2, zstd 1.5.7-1
- zstd/`_zstd` wired in 2026-07-10 (fixes runtime CAS zstd decompress on
  shipped Apple builds): embedded slices use BeeWare prebuilt `zstd` tarballs;
  macOS slices source-build via `_build_macos_zstd_source` (mirrors android
  `_build_zstd`); `LIBZSTD_CFLAGS/LIBS` passed to configure;
  `_check_zstd_in_libpython` fail-loud check per slice; `pybuild.py` `_zstd`
  enable now unconditional
- Deployment targets: macOS 11.0, iOS 13.0, tvOS 12.0, visionOS 2.0

## Build approach

Two build paths depending on slice type:

- **macOS** (is_macos=True): Native clang with cross-arch flags; deps built
  from source
- **Embedded** (iOS/tvOS/visionOS): BeeWare toolchain wrapper scripts;
  prebuilt dep tarballs

Steps per slice:

1. Download CPython source tarball, apply BeeWare patches
2. Download prebuilt deps (embedded) or build from source (macOS)
3. Patch `Modules/Setup.stdlib.in` for static modules
4. Configure with `--prefix=/usr` (no `--enable-framework`);
   STATIC_LIBPYTHON=1
5. Patch generated Makefile (remove -ldl/-framework deps, fix build_all for
   embedded)
6. `make` + install (libainstall/libinstall/inclinstall for embedded, full
   install for macOS)
7. `_check_no_shared_modules` — verify no .so in lib-dynload
8. `libtool` merge of libpython.a + dep .a files into merged archive

## Key gotchas fixed

### macOS x86_64 cross-compilation on Apple Silicon

1. **`-isysroot {sdk}`** in CFLAGS/LDFLAGS — required for linker to find TBD
   stubs (e.g. libz.dylib has no unversioned file on disk; only SDK stub
   exists)
2. **`PKG_CONFIG_LIBDIR={deps_dir}/lib/pkgconfig`** — replaces (not prepends)
   default pkg-config search paths; prevents Homebrew's arm64-only libb2 from
   being found (clearing only `PKG_CONFIG_PATH` is not sufficient since
   Homebrew's pkg-config binary has `/opt/homebrew/lib/pkgconfig` as a
   compiled-in default)
3. **Post-configure Makefile patch** (`_patch_macos_makefile` /
   `_patch_embedded_makefile`): removes `-ldl` (not a standalone lib on
   macOS >= 12) and clears `MODULE__BLAKE2_LDFLAGS` to keep external libb2
   out of the (unused) blake2 .so link. NOTE (2026-06-15): `_blake2` is now
   ENABLED (it's the only source of hashlib.blake2{b,s}); the patches must
   NOT clear `MODULE__BLAKE2_CFLAGS` or blake2module.c can't find the HACL
   `krml/` headers. See python-wiring.md Pitfalls (efrohome global_design)
   for the full blake2/_hmac story.
4. **`_clean_macos_dep_env(arch)`** — minimal Homebrew-free env for dep
   builds; uses `-target {arch}-apple-macosx{MACOS_MIN}` in CC (BeeWare
   style), `-isysroot` in CFLAGS/LDFLAGS only, PKG_CONFIG_LIBDIR/PATH cleared
5. **XZ gets `--host`/`--build`** in autoconf configure (BeeWare alignment)
6. **mpdecimal not built for macOS** — Python 3.13 bundles it; omit
   `--with-system-libmpdec` in macOS configure; `LIBMPDEC_*` env vars only
   set for non-macOS slices
7. **bzip2 uses `make install PREFIX=...`** instead of manual cp (BeeWare
   alignment)

### BeeWare wrapper scripts

Wrapper scripts added by `Python.patch` (e.g. `arm64-apple-ios-clang`) must
be:

- On PATH via `Apple/{Platform}/Resources/bin/`
- Made executable with `os.chmod(0o755)` — patch(1) doesn't restore the
  executable bit

### BeeWare dep tarballs

- Flat layout (include/ and lib/ at top level, no wrapper dir)
- All extracted to same `deps_dir` so they merge: `tar -xf tb -C deps_dir`
- NOT available for macOS desktop — must build from source

### --enable-framework removal

`_patch_configure(pydir)` removes `as_fn_error` lines BeeWare injects to
enforce `--enable-framework` (8 lines across 2 blocks). Regex:
`^[^\n]*\bas_fn_error.*builds must use --enable-framework.*\n` with
`re.MULTILINE`.

### Embedded Makefile patches (`_patch_embedded_makefile`)

- Removes `$(PYTHONFRAMEWORKDIR)/$(PYTHONFRAMEWORK)` from LINKFORSHARED
- Replaces `$(BUILDPYTHON)` with `$(LIBRARY)` in `build_all`
- Removes `Programs/_testembed`, `checksharedmods`, `rundsymutil` from
  `build_all`
- Removes `$(INSTALL_DATA) Programs/python.o ...` from `libainstall`

## References in codebase

- `tools/efrotools/python_build_apple.py` — main build script
- `tools/batools/pcommands.py` — registers `python_apple_gather` command
- `tools/efrotoolsinternal/cloudshell.py` — syncs `src/external/python-apple`
  and `build/assets/pylib-apple`
- `tools/batools/staging.py` — pylib_src_path = `'pylib-apple'` for
  `-xcode-mac`
- `tools/batools/assetsmakefile.py` — `private-apple-mac` subset reads from
  `src/assets/pylib-apple`, stages to `build/assets/pylib-apple`

## stdlib details

All platform slices share identical .py files; platform differences live in
per-platform `_sysconfigdata_*.py` files. Empty placeholder .py files exist
for modules that can't be static.
