# Released under the MIT License. See LICENSE for details.
#
# This Makefile encompasses most high level functionality you should need when
# working with Ballistica. These build rules are also handy as reference or a
# starting point if you need specific funtionality beyond that exposed here.
# Targets in this top level Makefile do not expect -jX to be passed to them
# and generally handle spawning an appropriate number of child jobs
# themselves.
#
# Note: Some of these targets use the lazybuild system to keep things extra
# efficient. This means, for example, that if nothing in asset sources has
# changed since the last successful asset build, we won't even dive into the
# src/assets dir and trigger the Makefile there the next time the 'assets'
# target here gets built. However, if you manually clear out built assets or
# muck around in src/assets yourself you may need to blow away the lazybuild
# states to get things building again. These live in '.cache/lazybuild'. You
# can blow away individual files there or the whole directory to force
# lazybuild to run builds it wouldn't otherwise run.


################################################################################
#                                                                              #
#                                   General                                    #
#                                                                              #
################################################################################

# List targets in this Makefile and basic descriptions for them.
help:
	@tools/pcommand makefile_target_list Makefile

# Set env-var BA_ENABLE_IRONY_BUILD_DB=1 to enable creating/updating a cmake
# compile-commands database for use with irony for emacs (and possibly other
# tools).
ifeq ($(BA_ENABLE_IRONY_BUILD_DB),1)
 PREREQ_IRONY_BUILD_DB = .cache/irony/compile_commands.json
endif

# Prereq targets that should be safe to run anytime; even if project-files
# are out of date.
PREREQS_SAFE = .cache/checkenv .dir-locals.el .mypy.ini .pycheckers .pylintrc \
 .style.yapf .clang-format ballisticakit-cmake/.clang-format .editorconfig

# Prereq targets that may break if the project needs updating should go here.
# An example is compile-command-databases; these might try to run cmake and
# fail if the CMakeList files don't match what's on disk. If such a target was
# included in PREREQS_SAFE it would try to build *before* project updates
# which would leave us stuck in a broken state.
PREREQS_POST_UPDATE_ONLY = $(PREREQ_IRONY_BUILD_DB)

# Target that should be built before running most any other build.
# This installs tool config files, runs environment checks, etc.
prereqs: $(PREREQS_SAFE) $(PREREQS_POST_UPDATE_ONLY)

# Set of prereqs that is safe to run if the project state is dirty.
prereqs-pre-update: $(PREREQS_SAFE)

prereqs-clean:
	rm -rf $(PREREQS_SAFE) $(PREREQS_POST_UPDATE_ONLY)

# Build all assets for all platforms.
assets: prereqs meta
	@tools/pcommand lazybuild assets_src $(LAZYBUILDDIR)/$@ \
 cd src/assets \&\& $(MAKE) -j$(CPUS)

# Build assets required for cmake builds (linux, mac)
assets-cmake: prereqs meta
	@tools/pcommand lazybuild assets_src $(LAZYBUILDDIR)/$@ \
 cd src/assets \&\& $(MAKE) -j$(CPUS) cmake

# Build only script assets required for cmake builds (linux, mac)
assets-cmake-scripts: prereqs meta
	@tools/pcommand lazybuild assets_src $(LAZYBUILDDIR)/$@ \
 cd src/assets \&\& $(MAKE) -j$(CPUS) scripts-cmake

# Build assets required for WINDOWS_PLATFORM windows builds.
assets-windows: prereqs meta
	@tools/pcommand lazybuild assets_src $(LAZYBUILDDIR)/$@ \
 cd src/assets \&\& $(MAKE) -j$(CPUS) win-$(WINDOWS_PLATFORM)

# Build assets required for Win32 windows builds.
assets-windows-Win32: prereqs meta
	@tools/pcommand lazybuild assets_src $(LAZYBUILDDIR)/$@ \
 cd src/assets \&\& $(MAKE) -j$(CPUS) win-Win32

# Build assets required for x64 windows builds.
assets-windows-x64: prereqs meta
	@tools/pcommand lazybuild assets_src $(LAZYBUILDDIR)/$@ \
 cd src/assets \&\& $(MAKE) -j$(CPUS) win-x64

# Build assets required for mac xcode builds
assets-mac: prereqs meta
	@tools/pcommand lazybuild assets_src $(LAZYBUILDDIR)/$@ \
 cd src/assets \&\& $(MAKE) -j$(CPUS) mac

# Build assets required for ios.
assets-ios: prereqs meta
	@tools/pcommand lazybuild assets_src $(LAZYBUILDDIR)/$@ \
 cd src/assets \&\& $(MAKE) -j$(CPUS) ios

# Build assets required for android.
assets-android: prereqs meta
	@tools/pcommand lazybuild assets_src $(LAZYBUILDDIR)/$@ \
 cd src/assets \&\& $(MAKE) -j$(CPUS) android

# Clean all assets.
assets-clean:
	@rm -f $(LAZYBUILDDIR)/assets*
	cd src/assets && $(MAKE) clean

# Build resources.
resources: prereqs meta
	@tools/pcommand lazybuild resources_src $(LAZYBUILDDIR)/$@ \
 cd src/resources \&\& $(MAKE) -j$(CPUS)

# Clean resources.
resources-clean:
	rm -f $(LAZYBUILDDIR)/resources
	cd src/resources && $(MAKE) clean

# Build our generated sources.
# Meta builds can affect sources used by asset builds, resource builds, and
# compiles, so it should be listed as a dependency of any of those.
meta: prereqs
	@tools/pcommand lazybuild meta_src $(LAZYBUILDDIR)/$@ \
 cd src/meta \&\& $(MAKE) -j$(CPUS)

# Clean our generated sources.
meta-clean:
	rm -f $(LAZYBUILDDIR)/meta
	cd src/meta && $(MAKE) clean

# Remove ALL files and directories that aren't managed by git
# (except for a few things such as localconfig.json).
clean:
	$(CHECK_CLEAN_SAFETY)
	rm -rf build
	git clean -dfx $(ROOT_CLEAN_IGNORES)

# Show what clean would delete without actually deleting it.
clean-list:
	$(CHECK_CLEAN_SAFETY)
	@echo Would remove build  # We do this ourself; not git.
	git clean -dnx $(ROOT_CLEAN_IGNORES)

# Build/update dummy python modules.
# IMPORTANT - building this target can kick off full builds/cleans and so
# it should not be built in parallel with other targets.
# See py_check_prepass target for more info.
dummymodules: build/dummymodules/.dummy_modules_state

dummymodules-clean:
	rm -rf build/dummymodules

# Generate docs.
docs: assets-cmake
	@tools/pcommand gendocs

# Tell make which of these targets don't represent files.
.PHONY: help prereqs prereqs-pre-update prereqs-clean assets assets-cmake \
 assets-cmake-scripts assets-windows assets-windows-Win32 assets-windows-x64 \
 assets-mac assets-ios assets-android assets-clean resources resources-clean \
 meta meta-clean clean clean-list dummymodules docs


################################################################################
#                                                                              #
#                                    Prefab                                    #
#                                                                              #
################################################################################

# Prebuilt binaries for various platforms.

# Assemble & run a gui debug build for this platform.
prefab-gui-debug: prefab-gui-debug-build
	$($(shell tools/pcommand prefab_run_var gui-debug))

# Assemble & run a gui release build for this platform.
prefab-gui-release: prefab-gui-release-build
	$($(shell tools/pcommand prefab_run_var gui-release))

# Assemble a debug build for this platform.
prefab-gui-debug-build:
	@tools/pcommand make_prefab gui-debug

# Assemble a release build for this platform.
prefab-gui-release-build:
	@tools/pcommand make_prefab gui-release

# Assemble & run a server debug build for this platform.
prefab-server-debug: prefab-server-debug-build
	$($(shell tools/pcommand prefab_run_var server-debug))

# Assemble & run a server release build for this platform.
prefab-server-release: prefab-server-release-build
	$($(shell tools/pcommand prefab_run_var server-release))

# Assemble a server debug build for this platform.
prefab-server-debug-build:
	@tools/pcommand make_prefab server-debug

# Assemble a server release build for this platform.
prefab-server-release-build:
	@tools/pcommand make_prefab server-release

# Clean all prefab builds.
prefab-clean:
	rm -rf build/prefab

# Specific platform prefab targets:

# (what visual studio calls their x86 (32 bit) target platform)
WINPLAT_X86 = Win32

# Mac gui debug:

RUN_PREFAB_MAC_X86_64_GUI_DEBUG = cd build/prefab/full/mac_x86_64_gui/debug \
  && ./ballisticakit

RUN_PREFAB_MAC_ARM64_GUI_DEBUG = cd build/prefab/full/mac_arm64_gui/debug \
  && ./ballisticakit

prefab-mac-x86-64-gui-debug: prefab-mac-x86-64-gui-debug-build
	@tools/pcommand ensure_prefab_platform mac_x86_64
	@$(RUN_PREFAB_MAC_X86_64_GUI_DEBUG)

prefab-mac-arm64-gui-debug: prefab-mac-arm64-gui-debug-build
	@tools/pcommand ensure_prefab_platform mac_arm64
	@$(RUN_PREFAB_MAC_ARM64_GUI_DEBUG)

prefab-mac-x86-64-gui-debug-build: prereqs assets-cmake \
   build/prefab/full/mac_x86_64_gui/debug/ballisticakit
	@$(STAGE_ASSETS) -cmake build/prefab/full/mac_x86_64_gui/debug

prefab-mac-arm64-gui-debug-build: prereqs assets-cmake \
   build/prefab/full/mac_arm64_gui/debug/ballisticakit
	@$(STAGE_ASSETS) -cmake build/prefab/full/mac_arm64_gui/debug

build/prefab/full/mac_%_gui/debug/ballisticakit: .efrocachemap
	@tools/pcommand efrocache_get $@

build/prefab/lib/mac_%_gui/debug/libballisticakit_internal.a: .efrocachemap
	@tools/pcommand efrocache_get $@

# Mac gui release:

RUN_PREFAB_MAC_X86_64_GUI_RELEASE = cd \
  build/prefab/full/mac_x86_64_gui/release && ./ballisticakit

RUN_PREFAB_MAC_ARM64_GUI_RELEASE = cd build/prefab/full/mac_arm64_gui/release \
  && ./ballisticakit

prefab-mac-x86-64-gui-release: prefab-mac-x86-64-gui-release-build
	@tools/pcommand ensure_prefab_platform mac_x86_64
	@$(RUN_PREFAB_MAC_X86_64_GUI_RELEASE)

prefab-mac-arm64-gui-release: prefab-mac-arm64-gui_release-build
	@tools/pcommand ensure_prefab_platform mac_arm64
	@$(RUN_PREFAB_MAC_ARM64_GUI_RELEASE)

prefab-mac-x86-64-gui-release-build: prereqs assets-cmake \
   build/prefab/full/mac_x86_64_gui/release/ballisticakit
	@$(STAGE_ASSETS) -cmake build/prefab/full/mac_x86_64_gui/release

prefab-mac-arm64-gui-release-build: prereqs assets-cmake \
   build/prefab/full/mac_arm64_gui/release/ballisticakit
	@$(STAGE_ASSETS) -cmake build/prefab/full/mac_arm64_gui/release

build/prefab/full/mac_%_gui/release/ballisticakit: .efrocachemap
	@tools/pcommand efrocache_get $@

build/prefab/lib/mac_%_gui/release/libballisticakit_internal.a: .efrocachemap
	@tools/pcommand efrocache_get $@

# Mac server debug:

RUN_PREFAB_MAC_X86_64_SERVER_DEBUG = cd \
 build/prefab/full/mac_x86_64_server/debug && ./ballisticakit_server

RUN_PREFAB_MAC_ARM64_SERVER_DEBUG = cd \
 build/prefab/full/mac_arm64_server/debug && ./ballisticakit_server

prefab-mac-x86-64-server-debug: prefab-mac-x86-64-server-debug-build
	@tools/pcommand ensure_prefab_platform mac_x86_64
	@$(RUN_PREFAB_MAC_X86_64_SERVER_DEBUG)

prefab-mac-arm64-server-debug: prefab-mac-arm64-server-debug-build
	@tools/pcommand ensure_prefab_platform mac_arm64
	@$(RUN_PREFAB_MAC_ARM64_SERVER_DEBUG)

prefab-mac-x86-64-server-debug-build: prereqs assets-cmake \
   build/prefab/full/mac_x86_64_server/debug/dist/ballisticakit_headless
	@$(STAGE_ASSETS) -cmakeserver -debug build/prefab/full/mac_x86_64_server/debug

prefab-mac-arm64-server-debug-build: prereqs assets-cmake \
   build/prefab/full/mac_arm64_server/debug/dist/ballisticakit_headless
	@$(STAGE_ASSETS) -cmakeserver -debug build/prefab/full/mac_arm64_server/debug

build/prefab/full/mac_%_server/debug/dist/ballisticakit_headless: .efrocachemap
	@tools/pcommand efrocache_get $@

build/prefab/lib/mac_%_server/debug/libballisticakit_internal.a: .efrocachemap
	@tools/pcommand efrocache_get $@

# Mac server release:

RUN_PREFAB_MAC_X86_64_SERVER_RELEASE = cd \
 build/prefab/full/mac_x86_64_server/release && ./ballisticakit_server

RUN_PREFAB_MAC_ARM64_SERVER_RELEASE = cd \
   build/prefab/full/mac_arm64_server/release && ./ballisticakit_server

prefab-mac-x86-64-server-release: prefab-mac-x86-64-server-release-build
	@tools/pcommand ensure_prefab_platform mac_x86_64
	@$(RUN_PREFAB_MAC_X86_64_SERVER_RELEASE)

prefab-mac-arm64-server-release: prefab-mac-arm64-server-release-build
	@tools/pcommand ensure_prefab_platform mac_arm64
	@$(RUN_PREFAB_MAC_ARM64_SERVER_RELEASE)

prefab-mac-x86-64-server-release-build: prereqs assets-cmake \
   build/prefab/full/mac_x86_64_server/release/dist/ballisticakit_headless
	@$(STAGE_ASSETS) -cmakeserver -release \
      build/prefab/full/mac_x86_64_server/release

prefab-mac-arm64-server-release-build: prereqs assets-cmake \
   build/prefab/full/mac_arm64_server/release/dist/ballisticakit_headless
	@$(STAGE_ASSETS) -cmakeserver -release \
      build/prefab/full/mac_arm64_server/release

build/prefab/full/mac_%_server/release/dist/ballisticakit_headless: .efrocachemap
	@tools/pcommand efrocache_get $@

build/prefab/lib/mac_%_server/release/libballisticakit_internal.a: .efrocachemap
	@tools/pcommand efrocache_get $@

# Linux gui debug:

RUN_PREFAB_LINUX_X86_64_GUI_DEBUG = cd \
  build/prefab/full/linux_x86_64_gui/debug && ./ballisticakit

RUN_PREFAB_LINUX_ARM64_GUI_DEBUG = cd \
  build/prefab/full/linux_arm64_gui/debug && ./ballisticakit

prefab-linux-x86-64-gui-debug: prefab-linux-x86-64-gui-debug-build
	@tools/pcommand ensure_prefab_platform linux_x86_64
	@$(RUN_PREFAB_LINUX_X86_64_GUI_DEBUG)

prefab-linux-arm64-gui-debug: prefab-linux-arm64-gui-debug-build
	@tools/pcommand ensure_prefab_platform linux_arm64
	@$(RUN_PREFAB_LINUX_ARM64_GUI_DEBUG)

prefab-linux-x86-64-gui-debug-build: prereqs assets-cmake \
   build/prefab/full/linux_x86_64_gui/debug/ballisticakit
	@$(STAGE_ASSETS) -cmake build/prefab/full/linux_x86_64_gui/debug

prefab-linux-arm64-gui-debug-build: prereqs assets-cmake \
   build/prefab/full/linux_arm64_gui/debug/ballisticakit
	@$(STAGE_ASSETS) -cmake build/prefab/full/linux_arm64_gui/debug

build/prefab/full/linux_%_gui/debug/ballisticakit: .efrocachemap
	@tools/pcommand efrocache_get $@

build/prefab/lib/linux_%_gui/debug/libballisticakit_internal.a: .efrocachemap
	@tools/pcommand efrocache_get $@

# Linux gui release:

RUN_PREFAB_LINUX_X86_64_GUI_RELEASE = cd \
  build/prefab/full/linux_x86_64_gui/release && ./ballisticakit

RUN_PREFAB_LINUX_ARM64_GUI_RELEASE = cd \
  build/prefab/full/linux_arm64_gui/release && ./ballisticakit

prefab-linux-x86-64-gui-release: prefab-linux-x86-64-gui-release-build
	@tools/pcommand ensure_prefab_platform linux_x86_64
	@$(RUN_PREFAB_LINUX_X86_64_GUI_RELEASE)

prefab-linux-arm64-gui-release: prefab-linux-arm64-gui-release-build
	@tools/pcommand ensure_prefab_platform linux_arm64
	@$(RUN_PREFAB_LINUX_ARM64_GUI_RELEASE)

prefab-linux-x86-64-gui-release-build: prereqs assets-cmake \
   build/prefab/full/linux_x86_64_gui/release/ballisticakit
	@$(STAGE_ASSETS) -cmake build/prefab/full/linux_x86_64_gui/release

prefab-linux-arm64-gui-release-build: prereqs assets-cmake \
   build/prefab/full/linux_arm64_gui/release/ballisticakit
	@$(STAGE_ASSETS) -cmake build/prefab/full/linux_arm64_gui/release

build/prefab/full/linux_%_gui/release/ballisticakit: .efrocachemap
	@tools/pcommand efrocache_get $@

build/prefab/lib/linux_%_gui/release/libballisticakit_internal.a: .efrocachemap
	@tools/pcommand efrocache_get $@

# Linux server debug:

RUN_PREFAB_LINUX_X86_64_SERVER_DEBUG = cd \
   build/prefab/full/linux_x86_64_server/debug && ./ballisticakit_server

RUN_PREFAB_LINUX_ARM64_SERVER_DEBUG = cd \
   build/prefab/full/linux_arm64_server/debug && ./ballisticakit_server

prefab-linux-x86-64-server-debug: prefab-linux-x86-64-server-debug-build
	@tools/pcommand ensure_prefab_platform linux_x86_64
	@$(RUN_PREFAB_LINUX_X86_64_SERVER_DEBUG)

prefab-linux-arm64-server-debug: prefab-linux-arm64-server-debug-build
	@tools/pcommand ensure_prefab_platform linux_arm64
	@$(RUN_PREFAB_LINUX_ARM64_SERVER_DEBUG)

prefab-linux-x86-64-server-debug-build: prereqs assets-cmake \
   build/prefab/full/linux_x86_64_server/debug/dist/ballisticakit_headless
	@$(STAGE_ASSETS) -cmakeserver -debug \
 build/prefab/full/linux_x86_64_server/debug

prefab-linux-arm64-server-debug-build: prereqs assets-cmake \
   build/prefab/full/linux_arm64_server/debug/dist/ballisticakit_headless
	@$(STAGE_ASSETS) -cmakeserver -debug \
 build/prefab/full/linux_arm64_server/debug

build/prefab/full/linux_%_server/debug/dist/ballisticakit_headless: .efrocachemap
	@tools/pcommand efrocache_get $@

build/prefab/lib/linux_%_server/debug/libballisticakit_internal.a: .efrocachemap
	@tools/pcommand efrocache_get $@

# Linux server release:

RUN_PREFAB_LINUX_X86_64_SERVER_RELEASE = cd \
   build/prefab/full/linux_x86_64_server/release && ./ballisticakit_server

RUN_PREFAB_LINUX_ARM64_SERVER_RELEASE = cd \
   build/prefab/full/linux_arm64_server/release && ./ballisticakit_server

prefab-linux-x86-64-server-release: prefab-linux-x86-64-server-release-build
	@tools/pcommand ensure_prefab_platform linux_x86_64
	@$(RUN_PREFAB_LINUX_X86_64_SERVER_RELEASE)

prefab-linux-arm64-server-release: prefab-linux-arm64-server-release-build
	@tools/pcommand ensure_prefab_platform linux_arm64
	@$(RUN_PREFAB_LINUX_ARM64_SERVER_RELEASE)

prefab-linux-x86-64-server-release-build: prereqs assets-cmake \
   build/prefab/full/linux_x86_64_server/release/dist/ballisticakit_headless
	@$(STAGE_ASSETS) -cmakeserver -release \
      build/prefab/full/linux_x86_64_server/release

prefab-linux-arm64-server-release-build: prereqs assets-cmake \
   build/prefab/full/linux_arm64_server/release/dist/ballisticakit_headless
	@$(STAGE_ASSETS) -cmakeserver -release \
      build/prefab/full/linux_arm64_server/release

build/prefab/full/linux_%_server/release/dist/ballisticakit_headless: .efrocachemap
	@tools/pcommand efrocache_get $@

build/prefab/lib/linux_%_server/release/libballisticakit_internal.a: .efrocachemap
	@tools/pcommand efrocache_get $@

# Windows gui debug:

RUN_PREFAB_WINDOWS_X86_GUI_DEBUG = cd build/prefab/full/windows_x86_gui/debug \
  && ./BallisticaKit.exe

prefab-windows-x86-gui-debug: prefab-windows-x86-gui-debug-build
	@tools/pcommand ensure_prefab_platform windows_x86
	@$(RUN_PREFAB_WINDOWS_X86_GUI_DEBUG)

prefab-windows-x86-gui-debug-build: prereqs assets-windows-$(WINPLAT_X86) \
   build/prefab/full/windows_x86_gui/debug/BallisticaKit.exe
	@$(STAGE_ASSETS) -win-$(WINPLAT_X86)-Debug \
   build/prefab/full/windows_x86_gui/debug

build/prefab/full/windows_x86_gui/debug/BallisticaKit.exe: .efrocachemap
	@tools/pcommand efrocache_get $@

build/prefab/lib/windows/Debug_%/BallisticaKitGenericInternal.lib: .efrocachemap
	@tools/pcommand efrocache_get $@

build/prefab/lib/windows/Debug_%/BallisticaKitGenericInternal.pdb: .efrocachemap
	@tools/pcommand efrocache_get $@

# Windows gui release:

RUN_PREFAB_WINDOWS_X86_GUI_RELEASE = cd \
  build/prefab/full/windows_x86_gui/release && ./BallisticaKit.exe

prefab-windows-x86-gui-release: prefab-windows-x86-gui-release-build
	@tools/pcommand ensure_prefab_platform windows_x86
	@$(RUN_PREFAB_WINDOWS_X86_GUI_RELEASE)

prefab-windows-x86-gui-release-build: prereqs \
   assets-windows-$(WINPLAT_X86) \
   build/prefab/full/windows_x86_gui/release/BallisticaKit.exe
	@$(STAGE_ASSETS) -win-$(WINPLAT_X86)-Release \
build/prefab/full/windows_x86_gui/release

build/prefab/full/windows_x86_gui/release/BallisticaKit.exe: .efrocachemap
	@tools/pcommand efrocache_get $@

build/prefab/lib/windows/Release_%/BallisticaKitGenericInternal.lib: .efrocachemap
	@tools/pcommand efrocache_get $@

build/prefab/lib/windows/Release_%/BallisticaKitGenericInternal.pdb: .efrocachemap
	@tools/pcommand efrocache_get $@

# Windows server debug:

RUN_PREFAB_WINDOWS_X86_SERVER_DEBUG = cd \
   build/prefab/full/windows_x86_server/debug \
   && dist/python_d.exe ballisticakit_server.py

prefab-windows-x86-server-debug: prefab-windows-x86-server-debug-build
	@tools/pcommand ensure_prefab_platform windows_x86
	@$(RUN_PREFAB_WINDOWS_X86_SERVER_DEBUG)

prefab-windows-x86-server-debug-build: prereqs \
   assets-windows-$(WINPLAT_X86) \
   build/prefab/full/windows_x86_server/debug/dist/BallisticaKitHeadless.exe
	@$(STAGE_ASSETS) -winserver-$(WINPLAT_X86)-Debug \
 build/prefab/full/windows_x86_server/debug

build/prefab/full/windows_x86_server/debug/dist/BallisticaKitHeadless.exe: .efrocachemap
	@tools/pcommand efrocache_get $@

build/prefab/lib/windows/Debug_%/BallisticaKitHeadlessInternal.lib: .efrocachemap
	@tools/pcommand efrocache_get $@

build/prefab/lib/windows/Debug_%/BallisticaKitHeadlessInternal.pdb: .efrocachemap
	@tools/pcommand efrocache_get $@

# Windows server release:

RUN_PREFAB_WINDOWS_X86_SERVER_RELEASE = cd \
   build/prefab/full/windows_x86_server/release \
   && dist/python.exe -O ballisticakit_server.py

prefab-windows-x86-server-release: prefab-windows-x86-server-release-build
	@tools/pcommand ensure_prefab_platform windows_x86
	@$(RUN_PREFAB_WINDOWS_X86_SERVER_RELEASE)

prefab-windows-x86-server-release-build: prereqs \
   assets-windows-$(WINPLAT_X86) \
   build/prefab/full/windows_x86_server/release/dist/BallisticaKitHeadless.exe
	@$(STAGE_ASSETS) -winserver-$(WINPLAT_X86)-Release \
   build/prefab/full/windows_x86_server/release

build/prefab/full/windows_x86_server/release/dist/BallisticaKitHeadless.exe: .efrocachemap
	@tools/pcommand efrocache_get $@

build/prefab/lib/windows/Release_%/BallisticaKitHeadlessInternal.lib: .efrocachemap
	@tools/pcommand efrocache_get $@

build/prefab/lib/windows/Release_%/BallisticaKitHeadlessInternal.pdb: .efrocachemap
	@tools/pcommand efrocache_get $@

# Tell make which of these targets don't represent files.
.PHONY: prefab-gui-debug prefab-gui-release prefab-gui-debug-build \
 prefab-gui-release-build prefab-server-debug prefab-server-release \
 prefab-server-debug-build prefab-server-release-build prefab-clean \
 _cmake_prefab_gui_binary _cmake_prefab_server_binary \
 prefab-mac-x86-64-gui-debug prefab-mac-arm64-gui-debug \
 prefab-mac-x86-64-gui-debug-build prefab-mac-arm64-gui-debug-build \
 prefab-mac-x86-64-gui-release prefab-mac-arm64-gui-release \
 prefab-mac-x86-64-gui-release-build prefab-mac-arm64-gui-release-build \
 prefab-mac-x86-64-server-debug prefab-mac-arm64-server-debug \
 prefab-mac-x86-64-server-debug-build prefab-mac-arm64-server-debug-build \
 prefab-mac-x86-64-server-release prefab-mac-arm64-server-release \
 prefab-mac-x86-64-server-release-build prefab-mac-arm64-server-release-build \
 prefab-linux-x86-64-gui-debug prefab-linux-arm64-gui-debug \
 prefab-linux-x86-64-gui-debug-build prefab-linux-arm64-gui-debug-build \
 prefab-linux-x86-64-gui-release prefab-linux-arm64-gui-release \
 prefab-linux-x86-64-gui-release-build prefab-linux-arm64-gui-release-build \
 prefab-linux-x86-64-server-debug prefab-linux-arm64-server-debug \
 prefab-linux-x86-64-server-debug-build prefab-linux-arm64-server-debug-build \
 prefab-linux-x86-64-server-release prefab-linux-arm64-server-release \
 prefab-linux-x86-64-server-release-build \
 prefab-linux-arm64-server-release-build \
 prefab-windows-x86-gui-debug prefab-windows-x86-gui-debug-build \
 prefab-windows-x86-gui-release prefab-windows-x86-gui-release-build \
 prefab-windows-x86-server-debug prefab-windows-x86-server-debug-build \
 prefab-windows-x86-server-release prefab-windows-x86-server-release-build


################################################################################
#                                                                              #
#                                   Updating                                   #
#                                                                              #
################################################################################

# Update any project files that need it (does NOT build projects).
update: prereqs-pre-update
	@tools/pcommand update_project
# Though not technically necessary, let's keep things like tool-configs
# immediately updated so our editors/etc. better reflect the current state.
	@$(MAKE) -j$(CPUS) prereqs
	@tools/pcommand echo GRN Update-Project: SUCCESS!

# Don't update but fail if anything needs it.
update-check: prereqs-pre-update
	@tools/pcommand update_project --check
	@tools/pcommand echo GRN Check-Project: Everything up to date.

# Tell make which of these targets don't represent files.
.PHONY: update update-check


################################################################################
#                                                                              #
#                                  Formatting                                  #
#                                                                              #
################################################################################

# Run formatting on all files in the project considered 'dirty'.
format:
	@$(MAKE) -j$(CPUS) format-code format-scripts format-makefile
	@tools/pcommand echo BLD Formatting complete for $(notdir $(CURDIR))!

# Same but always formats; ignores dirty state.
format-full:
	@$(MAKE) -j$(CPUS) format-code-full format-scripts-full format-makefile
	@tools/pcommand echo BLD Formatting complete for $(notdir $(CURDIR))!

# Run formatting for compiled code sources (.cc, .h, etc.).
format-code: prereqs
	@tools/pcommand formatcode

# Same but always formats; ignores dirty state.
format-code-full: prereqs
	@tools/pcommand formatcode -full

# Runs formatting for scripts (.py, etc).
format-scripts: prereqs
	@tools/pcommand formatscripts

# Same but always formats; ignores dirty state.
format-scripts-full: prereqs
	@tools/pcommand formatscripts -full

# Runs formatting on the project Makefile.
format-makefile: prereqs
	@tools/pcommand formatmakefile

.PHONY: format format-full format-code format-code-full format-scripts \
 format-scripts-full


################################################################################
#                                                                              #
#                                   Checking                                   #
#                                                                              #
################################################################################

# Run all project checks. (static analysis)
check: py_check_prepass
# TEMP - disabling some checks during 1.7.20 refactor.
	@$(DMAKE) -j$(CPUS) update-check cpplint mypy
	@tools/pcommand echo SGRN BLD ALL CHECKS PASSED!
#	@$(DMAKE) -j$(CPUS) update-check cpplint pylint mypy
#	@tools/pcommand echo SGRN BLD ALL CHECKS PASSED!

# Same as check but no caching (all files are checked).
check-full: py_check_prepass
	@$(DMAKE) -j$(CPUS) update-check cpplint-full pylint-full mypy-full
	@tools/pcommand echo SGRN BLD ALL CHECKS PASSED!

# Same as 'check' plus optional/slow extra checks.
# check2:
# 	@$(DMAKE) -j$(CPUS) update-check cpplint pylint mypy pycharm depcheck
# 	@tools/pcommand echo SGRN BLD ALL CHECKS PASSED!
# TEMP - disabling some during refactor.
check2: py_check_prepass
	@$(DMAKE) -j$(CPUS) update-check cpplint mypy
	@tools/pcommand echo SGRN BLD ALL CHECKS PASSED!

# Same as check2 but no caching (all files are checked).
# check2-full:
# 	@$(DMAKE) -j$(CPUS) update-check cpplint-full pylint-full mypy-full \
#    pycharm-full
# 	@tools/pcommand echo SGRN BLD ALL CHECKS PASSED!
# TEMP - disabling some checks during 1.7.20 refactor.
check2-full: py_check_prepass
	@$(DMAKE) -j$(CPUS) update-check cpplint-full mypy-full
	@tools/pcommand echo SGRN BLD ALL CHECKS PASSED!

# Run Cpplint checks on all C/C++ code.
cpplint: prereqs meta
	@tools/pcommand cpplint

# Run Cpplint checks without caching (all files are checked).
cpplint-full: prereqs meta
	@tools/pcommand cpplint -full

# Run Pylint checks on all Python Code.
pylint: py_check_prepass
	@tools/pcommand pylint

# Run Pylint checks without caching (all files are checked).
pylint-full: py_check_prepass
	@tools/pcommand pylint -full

# Run Mypy checks on all Python code.
mypy: py_check_prepass
	@tools/pcommand mypy

# Run Mypy checks without caching (all files are checked).
mypy-full: py_check_prepass
	@tools/pcommand mypy -full

# Run Mypy checks on all Python code using daemon mode.
dmypy: py_check_prepass
	@tools/pcommand dmypy

# Stop the mypy daemon
dmypy-stop: py_check_prepass
	@tools/pcommand dmypy -stop

# Run PyCharm checks on all Python code.
pycharm: py_check_prepass
	@tools/pcommand pycharm

# Run PyCharm checks without caching (all files are checked).
pycharm-full: py_check_prepass
	@tools/pcommand pycharm -full

# Run extra mypy checks with various dependency permutations.
# ensures packages don't depend on thing they're not supposed to.
depchecks: py_check_prepass
	@tools/pcommand depchecks

featuresettest: py_check_prepass
	echo WOULD DO FS

# Build prerequisites needed for python checks.
#
# IMPORTANT - this target may kick off new meta/asset/binary builds/cleans as
# part of doing its thing. For this reason, be sure this target gets built
# alone in a make process and not mixed in with others as it would likely
# stomp on them or their dependencies.
#
# Practically, this means any target depending on this should list it as its
# one and only dependency. And when any such target gets built alongside
# others (such as by the 'check-full' target) the parent target should
# explicitly built this beforehand to ensure it does not happen during the
# parallel part.
# Note to self: Originally prereqs and meta were listed as deps of
# .dummy_modules_state, but because prereqs has no output dependencies
# it always fires which meant dummy modules would get rebuilt every run.
# This config should do the right thing without violating the above rules.
py_check_prepass: prereqs meta
	@$(MAKE) dummymodules

# The following section is auto-generated; do not edit by hand.
# __AUTOGENERATED_DUMMY_MODULES_BEGIN__

# Update dummy Python modules when source files contributing to them change.
build/dummymodules/.dummy_modules_state: \
 src/ballistica/base/python/class/python_class_app_timer.cc \
 src/ballistica/base/python/class/python_class_context_call.cc \
 src/ballistica/base/python/class/python_class_context_ref.cc \
 src/ballistica/base/python/class/python_class_display_timer.cc \
 src/ballistica/base/python/class/python_class_feature_set_data.cc \
 src/ballistica/base/python/class/python_class_simple_sound.cc \
 src/ballistica/base/python/class/python_class_vec3.cc \
 src/ballistica/base/python/methods/python_methods_app.cc \
 src/ballistica/base/python/methods/python_methods_graphics.cc \
 src/ballistica/base/python/methods/python_methods_misc.cc \
 src/ballistica/classic/python/methods/python_methods_classic.cc \
 src/ballistica/scene_v1/python/class/python_class_activity_data.cc \
 src/ballistica/scene_v1/python/class/python_class_base_timer.cc \
 src/ballistica/scene_v1/python/class/python_class_input_device.cc \
 src/ballistica/scene_v1/python/class/python_class_material.cc \
 src/ballistica/scene_v1/python/class/python_class_node.cc \
 src/ballistica/scene_v1/python/class/python_class_scene_collision_mesh.cc \
 src/ballistica/scene_v1/python/class/python_class_scene_data_asset.cc \
 src/ballistica/scene_v1/python/class/python_class_scene_mesh.cc \
 src/ballistica/scene_v1/python/class/python_class_scene_sound.cc \
 src/ballistica/scene_v1/python/class/python_class_scene_texture.cc \
 src/ballistica/scene_v1/python/class/python_class_scene_timer.cc \
 src/ballistica/scene_v1/python/class/python_class_session_data.cc \
 src/ballistica/scene_v1/python/class/python_class_session_player.cc \
 src/ballistica/scene_v1/python/methods/python_methods_assets.cc \
 src/ballistica/scene_v1/python/methods/python_methods_input.cc \
 src/ballistica/scene_v1/python/methods/python_methods_networking.cc \
 src/ballistica/scene_v1/python/methods/python_methods_scene.cc \
 src/ballistica/template_fs/python/class/python_class_hello.cc \
 src/ballistica/template_fs/python/methods/python_methods_template_fs.cc \
 src/ballistica/ui_v1/python/class/python_class_ui_mesh.cc \
 src/ballistica/ui_v1/python/class/python_class_ui_sound.cc \
 src/ballistica/ui_v1/python/class/python_class_ui_texture.cc \
 src/ballistica/ui_v1/python/class/python_class_widget.cc \
 src/ballistica/ui_v1/python/methods/python_methods_ui_v1.cc
	@tools/pcommand with_build_lock gen_dummy_modules_lock \
 rm -rf build/dummymodules \&\& mkdir -p build/dummymodules \
 \&\& ./tools/pcommand gen_dummy_modules \
 \&\& touch build/dummymodules/.dummy_modules_state
# __AUTOGENERATED_DUMMY_MODULES_END__

# Tell make which of these targets don't represent files.
.PHONY: check check-full check2 check2-full \
 cpplint cpplint-full pylint pylint-full mypy \
 mypy-full dmypy dmypy-stop pycharm pycharm-full py_check_prepass


################################################################################
#                                                                              #
#                                   Testing                                    #
#                                                                              #
################################################################################

# Run all tests. (live execution verification)
test: py_check_prepass
	@tools/pcommand echo BLU Running all tests...
	@tools/pcommand pytest -v tests

# Run tests with any caching disabled.
test-full: test

# Individual test with extra output enabled.
test-assetmanager:
	@tools/pcommand pytest -o log_cli=true -o log_cli_level=debug -s -vv \
      tests/test_babase/test_assetmanager.py::test_assetmanager

# Individual test with extra output enabled.
test-message:
	@tools/pcommand pytest -o log_cli=true -o log_cli_level=debug -s -vv \
      tests/test_efro/test_message.py

# Individual test with extra output enabled.
test-dataclassio:
	@tools/pcommand pytest -o log_cli=true -o log_cli_level=debug -s -vv \
      tests/test_efro/test_dataclassio.py

# Individual test with extra output enabled.
test-rpc:
	@tools/pcommand pytest -o log_cli=true -o log_cli_level=debug -s -vv \
      tests/test_efro/test_rpc.py

# Tell make which of these targets don't represent files.
.PHONY: test test-full test-assetmanager


################################################################################
#                                                                              #
#                                 Preflighting                                 #
#                                                                              #
################################################################################

# Format, update, check, & test the project. Do this before commits.
preflight:
	@$(MAKE) format
	@$(MAKE) update
	@$(MAKE) -j$(CPUS) cpplint pylint mypy test
	@tools/pcommand echo SGRN BLD PREFLIGHT SUCCESSFUL!

# Same as 'preflight' without caching (all files are visited).
preflight-full:
	@$(MAKE) format-full
	@$(MAKE) update
	@$(MAKE) -j$(CPUS) cpplint-full pylint-full mypy-full test-full
	@tools/pcommand echo SGRN BLD PREFLIGHT SUCCESSFUL!

# Same as 'preflight' plus optional/slow extra checks.
preflight2:
	@$(MAKE) format
	@$(MAKE) update
	@$(MAKE) -j$(CPUS) cpplint pylint mypy pycharm test
	@tools/pcommand echo SGRN BLD PREFLIGHT SUCCESSFUL!

# Same as 'preflight2' but without caching (all files visited).
preflight2-full:
	@$(MAKE) format-full
	@$(MAKE) update
	@$(MAKE) -j$(CPUS) cpplint-full pylint-full mypy-full pycharm-full test-full
	@tools/pcommand echo SGRN BLD PREFLIGHT SUCCESSFUL!

# Tell make which of these targets don't represent files.
.PHONY: preflight preflight-full preflight2 preflight2-full


################################################################################
#                                                                              #
#                                   Windows                                    #
#                                                                              #
################################################################################

# Set these env vars from the command line to influence the build:

# Can be Generic, Headless, or Oculus
WINDOWS_PROJECT ?= Generic

# Can be Win32 or x64
WINDOWS_PLATFORM ?= Win32

# Can be Debug or Release
WINDOWS_CONFIGURATION ?= Debug

# Stage assets and other files so a built binary will run.
windows-staging: assets-windows resources meta
	$(STAGE_ASSETS) -win-$(WINPLT)-$(WINCFG) \
   build/windows/$(WINCFG)_$(WINPLT)

# Build and run a debug windows build (from WSL).
windows-debug: windows-debug-build
	@tools/pcommand ensure_prefab_platform windows_x86
	build/windows/Debug_Win32/BallisticaKitGeneric.exe

# Build and run a release windows build (from WSL).
windows-release: windows-release-build
	@tools/pcommand ensure_prefab_platform windows_x86
	build/windows/Release_Win32/BallisticaKitGeneric.exe

# Build a debug windows build (from WSL).
windows-debug-build: \
   build/prefab/lib/windows/Debug_Win32/BallisticaKitGenericInternal.lib \
   build/prefab/lib/windows/Debug_Win32/BallisticaKitGenericInternal.pdb
	@tools/pcommand ensure_prefab_platform windows_x86
	@tools/pcommand wsl_build_check_win_drive
	WINDOWS_CONFIGURATION=Debug WINDOWS_PLATFORM=Win32 $(MAKE) windows-staging
	WINDOWS_PROJECT=Generic WINDOWS_CONFIGURATION=Debug WINDOWS_PLATFORM=Win32 \
  $(MAKE) _windows-wsl-build

# Rebuild a debug windows build (from WSL).
windows-debug-rebuild: \
   build/prefab/lib/windows/Debug_Win32/BallisticaKitGenericInternal.lib \
   build/prefab/lib/windows/Debug_Win32/BallisticaKitGenericInternal.pdb
	@tools/pcommand ensure_prefab_platform windows_x86
	@tools/pcommand wsl_build_check_win_drive
	WINDOWS_CONFIGURATION=Debug WINDOWS_PLATFORM=Win32 $(MAKE) windows-staging
	WINDOWS_PROJECT=Generic WINDOWS_CONFIGURATION=Debug WINDOWS_PLATFORM=Win32 \
  $(MAKE) _windows-wsl-rebuild

# Build a release windows build (from WSL).
windows-release-build: \
   build/prefab/lib/windows/Release_Win32/BallisticaKitGenericInternal.lib \
   build/prefab/lib/windows/Release_Win32/BallisticaKitGenericInternal.pdb
	@tools/pcommand ensure_prefab_platform windows_x86
	@tools/pcommand wsl_build_check_win_drive
	WINDOWS_CONFIGURATION=Release WINDOWS_PLATFORM=Win32 $(MAKE) windows-staging
	WINDOWS_PROJECT=Generic WINDOWS_CONFIGURATION=Release WINDOWS_PLATFORM=Win32 \
  $(MAKE) _windows-wsl-build

# Rebuild a release windows build (from WSL).
windows-release-rebuild: \
   build/prefab/lib/windows/Release_Win32/BallisticaKitGenericInternal.lib \
   build/prefab/lib/windows/Release_Win32/BallisticaKitGenericInternal.pdb
	@tools/pcommand ensure_prefab_platform windows_x86
	@tools/pcommand wsl_build_check_win_drive
	WINDOWS_CONFIGURATION=Release WINDOWS_PLATFORM=Win32 $(MAKE) windows-staging
	WINDOWS_PROJECT=Generic WINDOWS_CONFIGURATION=Release WINDOWS_PLATFORM=Win32 \
  $(MAKE) _windows-wsl-rebuild

# Remove all non-git-managed files in windows subdir.
windows-clean:
	@$(CHECK_CLEAN_SAFETY)
	git clean -dfx ballisticakit-windows
	rm -rf build/windows $(LAZYBUILDDIR)

# Show what would be cleaned.
windows-clean-list:
	@$(CHECK_CLEAN_SAFETY)
	git clean -dnx ballisticakit-windows
	echo would also remove build/windows $(LAZYBUILDDIR)


################################################################################
#                                                                              #
#                                    CMake                                     #
#                                                                              #
################################################################################

# Set the following from the command line to influence the build:

# This can be Debug or Release.
CMAKE_BUILD_TYPE ?= Debug

# Build and run the cmake build.
cmake: cmake-build
	@cd build/cmake/$(CM_BT_LC) && ./ballisticakit

# Build and run the cmake build under lldb.
cmake-lldb: cmake-build
	@cd build/cmake/$(CM_BT_LC) && BA_DEBUGGER_ATTACHED=1 lldb ./ballisticakit

# Build but don't run it.
cmake-build: assets-cmake resources cmake-binary
	@$(STAGE_ASSETS) -cmake build/cmake/$(CM_BT_LC)

cmake-binary: meta
	@tools/pcommand cmake_prep_dir build/cmake/$(CM_BT_LC)
	@cd build/cmake/$(CM_BT_LC) && test -f Makefile \
      || cmake -DCMAKE_BUILD_TYPE=$(CMAKE_BUILD_TYPE) \
      $(PWD)/ballisticakit-cmake
	@tools/pcommand update_cmake_prefab_lib standard $(CM_BT_LC) build/cmake/$(CM_BT_LC)
	@cd build/cmake/$(CM_BT_LC) && $(MAKE) -j$(CPUS) ballisticakit

cmake-clean:
	rm -rf build/cmake/$(CM_BT_LC)

cmake-server: cmake-server-build
	@cd build/cmake/server-$(CM_BT_LC) && ./ballisticakit_server

cmake-server-build: assets-cmake resources meta cmake-server-binary
	@$(STAGE_ASSETS) -cmakeserver -$(CM_BT_LC) build/cmake/server-$(CM_BT_LC)

# Build just the headless binary.
# Note: We currently symlink FOO_headless. In packaged builds we rename it.
cmake-server-binary: meta
	@tools/pcommand cmake_prep_dir build/cmake/server-$(CM_BT_LC)/dist
	@cd build/cmake/server-$(CM_BT_LC)/dist && test -f Makefile \
      || cmake -DCMAKE_BUILD_TYPE=$(CMAKE_BUILD_TYPE) -DHEADLESS=true \
      $(PWD)/ballisticakit-cmake
	@tools/pcommand update_cmake_prefab_lib server $(CM_BT_LC) build/cmake/server-$(CM_BT_LC)/dist
	@cd build/cmake/server-$(CM_BT_LC)/dist && $(MAKE) -j$(CPUS)

cmake-server-clean:
	rm -rf build/cmake/server-$(CM_BT_LC)

# Stage assets for building/running within CLion.
clion-staging: assets-cmake resources meta
	$(STAGE_ASSETS) -cmake build/clion_debug
	$(STAGE_ASSETS) -cmake build/clion_release

# Tell make which of these targets don't represent files.
.PHONY: cmake cmake-build cmake-clean cmake-server cmake-server-build \
 cmake-server-clean


################################################################################
#                                                                              #
#                                  Auxiliary                                   #
#                                                                              #
################################################################################

# Can be used in place of the recommended $(MAKE) to suppress various warnings
# about the jobserver being disabled due to -jX options being passed to
# sub-makes. Generally passing -jX as part of a recursive make instantiation
# is frowned upon, but we treat this Makefile as a high level orchestration
# layer and we want to handle details like that for the user, so we try to
# pick smart -j values ourselves. We can't really rely on the jobserver anyway
# to balance our loads since we often call out to other systems (XCode,
# Gradle, Visual Studio, etc.) which wrangle jobs in their own ways.
DMAKE = $(MAKE) MAKEFLAGS= MKFLAGS= MAKELEVEL=

# This should give the cpu count on linux and mac; may need to expand this
# if using this on other platforms.
CPUS = $(shell getconf _NPROCESSORS_ONLN || echo 8)
PROJ_DIR = $(abspath $(CURDIR))
VERSION = $(shell tools/pcommand version version)
BUILD_NUMBER = $(shell tools/pcommand version build)
BUILD_DIR = $(PROJ_DIR)/build
LAZYBUILDDIR = .cache/lazybuild
STAGE_ASSETS = $(PROJ_DIR)/tools/pcommand stage_assets

# Things to ignore when doing root level cleans. Note that we exclude build
# and just blow that away manually; it might contain git repos or other things
# that can confuse git.
ROOT_CLEAN_IGNORES = --exclude=config/localconfig.json \
  --exclude=.spinoffdata \
  --exclude=/build

CHECK_CLEAN_SAFETY = tools/pcommand check_clean_safety

# Some tool configs that need filtering (mainly injecting projroot path).
TOOL_CFG_INST = tools/pcommand tool_config_install

# Anything that affects tool-config generation.
TOOL_CFG_SRC = tools/efrotools/pcommand.py config/projectconfig.json

# Anything that should trigger an environment-check when changed.
ENV_SRC = tools/pcommand tools/batools/build.py

.clang-format: config/toolconfigsrc/clang-format $(TOOL_CFG_SRC)
	@$(TOOL_CFG_INST) $< $@

.style.yapf: config/toolconfigsrc/style.yapf $(TOOL_CFG_SRC)
	@$(TOOL_CFG_INST) $< $@

.pylintrc: config/toolconfigsrc/pylintrc $(TOOL_CFG_SRC)
	@$(TOOL_CFG_INST) $< $@

.projectile: config/toolconfigsrc/projectile $(TOOL_CFG_SRC)
	@$(TOOL_CFG_INST) $< $@

.editorconfig: config/toolconfigsrc/editorconfig $(TOOL_CFG_SRC)
	@$(TOOL_CFG_INST) $< $@

.dir-locals.el: config/toolconfigsrc/dir-locals.el $(TOOL_CFG_SRC)
	@$(TOOL_CFG_INST) $< $@

.mypy.ini: config/toolconfigsrc/mypy.ini $(TOOL_CFG_SRC)
	@$(TOOL_CFG_INST) $< $@

.pycheckers: config/toolconfigsrc/pycheckers $(TOOL_CFG_SRC)
	@$(TOOL_CFG_INST) $< $@

# Set this to 1 to skip environment checks.
SKIP_ENV_CHECKS ?= 0

.cache/checkenv: $(ENV_SRC)
	@if [ $(SKIP_ENV_CHECKS) -ne 1 ]; then \
      tools/pcommand checkenv && mkdir -p .cache && touch .cache/checkenv; \
  fi

# CMake build-type lowercase
CM_BT_LC = $(shell echo $(CMAKE_BUILD_TYPE) | tr A-Z a-z)

# Eww; no way to do multi-line constants in make without spaces :-(
_WMSBE_1 = \"C:\\Program Files \(x86\)\\Microsoft Visual Studio\\2019
_WMSBE_2 = \\Community\\MSBuild\\Current\\Bin\\MSBuild.exe\"
_WMSBE_1B = /mnt/c/Program Files (x86)/Microsoft Visual Studio/2019
_WMSBE_2B = /Community/MSBuild/Current/Bin/MSBuild.exe

VISUAL_STUDIO_VERSION = -property:VisualStudioVersion=16
WIN_MSBUILD_EXE = $(_WMSBE_1)$(_WMSBE_2)
WIN_MSBUILD_EXE_B = "$(_WMSBE_1B)$(_WMSBE_2B)"
WINPRJ = $(WINDOWS_PROJECT)
WINPLT = $(WINDOWS_PLATFORM)
WINCFG = $(WINDOWS_CONFIGURATION)

# When using CLion, our cmake dir is root. Expose .clang-format there too.
ballisticakit-cmake/.clang-format: .clang-format
	@mkdir -p ballisticakit-cmake
	@cd ballisticakit-cmake && ln -sf ../.clang-format .

# Simple target for CI to build a binary but not download/assemble assets/etc.
_cmake-simple-ci-server-build:
	SKIP_ENV_CHECKS=1 $(MAKE) meta
	rm -rf build/cmake_simple_ci_server_build
	mkdir -p build/cmake_simple_ci_server_build
	tools/pcommand update_cmake_prefab_lib \
      server debug build/cmake_simple_ci_server_build
	cd build/cmake_simple_ci_server_build && \
      cmake -DCMAKE_BUILD_TYPE=Debug -DHEADLESS=true $(PWD)/ballisticakit-cmake
	cd build/cmake_simple_ci_server_build && $(MAKE) -j$(CPUS)

# Irony in emacs requires us to use cmake to generate a full
# list of compile commands for all files; lets try to keep it up to date
# whenever CMakeLists changes.
.cache/irony/compile_commands.json: ballisticakit-cmake/CMakeLists.txt
	@tools/pcommand echo BLU Updating Irony build commands db...
	@echo Generating Irony compile-commands-list...
	@mkdir -p .cache/irony
	@cd .cache/irony \
      && cmake -DCMAKE_EXPORT_COMPILE_COMMANDS=ON -DCMAKE_BUILD_TYPE=Debug \
      $(PWD)/ballisticakit-cmake
	@mv .cache/irony/compile_commands.json . \
      && rm -rf .cache/irony \
      && mkdir .cache/irony \
      && mv compile_commands.json .cache/irony
	@tools/pcommand echo BLU Created Irony build db at $@

_windows-wsl-build:
	@tools/pcommand wsl_build_check_win_drive
	$(WIN_MSBUILD_EXE_B) \
   $(shell tools/pcommand wsl_path_to_win --escape \
   ballisticakit-windows/$(WINPRJ)/BallisticaKit$(WINPRJ).vcxproj) \
   -target:Build \
   -property:Configuration=$(WINCFG) \
   -property:Platform=$(WINPLT) \
   $(VISUAL_STUDIO_VERSION)
	@tools/pcommand echo BLU BLD Built build/windows/BallisticaKit$(WINPRJ).exe.

_windows-wsl-rebuild:
	@tools/pcommand wsl_build_check_win_drive
	$(WIN_MSBUILD_EXE_B) \
   $(shell tools/pcommand wsl_path_to_win --escape \
    ballisticakit-windows/$(WINPRJ)/BallisticaKit$(WINPRJ).vcxproj) \
   -target:Rebuild \
   -property:Configuration=$(WINCFG) \
   -property:Platform=$(WINPLT) \
   $(VISUAL_STUDIO_VERSION)
	@tools/pcommand echo BLU BLD Built build/windows/BallisticaKit$(WINPRJ).exe.

# Tell make which of these targets don't represent files.
.PHONY: _cmake-simple-ci-server-build _windows-wsl-build _windows-wsl-rebuild
