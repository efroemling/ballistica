# OpenAL Builds

**Description:** How OpenAL Soft is built and consumed across platforms — the Apple xcframework pipeline, Android static lib, version-bump gotchas, and per-target consumption map.

All platforms use OpenAL Soft (pinned at **1.25.2** everywhere) as the
audio backend, but it reaches each build type through a different
supply path. This doc maps who consumes what and how the prebuilt
artifacts are produced.

## Per-target consumption map

- **Apple Xcode targets (mac/iOS/tvOS/visionOS)** — all link + embed a
  single framework-based
  `src/external/openal-apple/OpenALSoft.xcframework` (slices:
  macos-arm64_x86_64, ios-arm64[+sim], tvos-arm64[+sim],
  xros-arm64[+sim]). This retired Apple's deprecated system
  `OpenAL.framework` (formerly used on iOS/tvOS) and the bare
  `lib/macos/libopenal.1.dylib` (formerly used by the mac targets).
- **macOS uses the xcframework's framework slice too** — unlike ANGLE,
  which deliberately keeps mac on bare dylibs. OpenAL doesn't need
  that: it's a single self-contained lib with no sibling `dlopen`
  (ANGLE's libEGL→libGLESv2 is what forces the dylib arrangement
  there).
- **macOS cmake/SDL build** — uses its own *separate* OpenAL
  (`build/static_dependencies/libopenal.a` / homebrew `openal-soft`,
  per `ballisticakit-cmake/CMakeLists.txt`); the xcframework is
  consumed only by the Xcode targets.
- **Android** — separate static `libopenal.a` (plus `liboboe.a`, Oboe
  1.10.0) for all 8 ABI/mode combos, built by
  `tools/efrotools/openalbuildandroid.py`. Also on 1.25.2 and also
  tarball-fetch (matching the Apple build's structure; build root
  `build/openal-android/`; examples/utils/tests disabled — 1.25.2's
  examples fail to link against the static lib). Builds locally via the
  NDK (`make openal-android-all` + `openal-android-gather`); no cloud
  build+gather target yet.

## Apple build tooling

`tools/efrotools/openalbuildapple.py`, driven by pcommands
`openal_apple_build` / `openal_apple_test_build` /
`openal_apple_gather`; Makefile targets `openal-apple-build` /
`-test-build` / `-gather` plus `openal-apple-test-cloud-build`;
cloudshell env `openal-apple`; CI canary `openal.apple` in the apple
upkeep list in `batoolsinternal/build.py`.

- **Tarball, not git:** the build fetches the OpenAL Soft release
  tarball pinned by `OPENAL_SOFT_TAG` rather than cloning — a nested
  `.git` trips the build sandbox.
- **Full-wipe, non-incremental:** `_do_build` wipes the whole
  `build/openal-apple/` each run (OpenAL builds fast; `test_build` ==
  `build`).
- ⚠ **1.25.2 needs a patch — re-check on version bumps:** it
  force-promotes `-Wfunction-effects` to `-Werror=function-effects`,
  and its own CoreAudio backend trips that under current Xcode clang.
  `_patch_checkout` demotes it back to a warning. (The Android build
  applies the same demotion.)
- **Not published to public:** `pubsync.py` excludes
  `src/external/openal-apple` — contrast ANGLE's apple binaries, which
  *are* published.

## C++ wiring

The `BA_USE_FRAMEWORK_OPENAL` macro/branch is fully removed: `al_sys.h`
unconditionally includes OpenAL Soft's `<al.h>`, and the
`-Wdeprecated-declarations` pragmas (which only silenced Apple's
deprecated system OpenAL) are gone from al_sys.cc / audio_server.cc /
audio_streamer.cc / sound_asset.cc.

## Open items

- **tvOS / visionOS audio runtime unverified** (iOS confirmed working;
  mac obviously exercised).
- **No `AVAudioSession` management** — iOS/tvOS/visionOS use CoreAudio
  RemoteIO (no device enumeration; `CAN_ENUMERATE 0`), and OpenAL Soft
  does not manage the session (category/interruptions); route changes
  surface via AVAudioSession, not OpenAL disconnect events. Any mobile
  audio oddity (interruptions, headphone-unplug recovery) will live
  here — vs the macOS device-disconnect/reopen path in
  `audio_server.cc`.
- **visionOS slice is built and shipped** in the xcframework, but no
  visionOS Xcode target exists yet (nothing links the xros slice).
