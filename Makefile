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
	@$(PCOMMAND) makefile_target_list Makefile

# Set env-var BA_ENABLE_COMPILE_COMMANDS_DB=1 to enable creating/updating a
# cmake compile-commands database for use with things like clangd.
ifeq ($(BA_ENABLE_COMPILE_COMMANDS_DB),1)
 PREREQ_COMPILE_COMMANDS_DB = .cache/compile_commands_db/compile_commands.json
endif

# pcommandbatch can be much faster when running hundreds or thousands of
# commands, but has some downsides and limitations compared to regular
# pcommand. See tools/efrotools/pcommandbatch.py for more info on when to use
# which.
PCOMMAND = tools/pcommand
PCOMMANDBATCHBIN = .cache/pcommandbatch/pcommandbatch
ifeq ($(BA_PCOMMANDBATCH_DISABLE),1)
 PCOMMANDBATCH = $(PCOMMAND)
else
 PCOMMANDBATCH = $(PCOMMANDBATCHBIN)
endif

# Prereq targets that should be safe to run anytime; even if project-files
# are out of date.
PREREQS_SAFE = .cache/checkenv $(PCOMMANDBATCHBIN) .dir-locals.el .mypy.ini	\
 .pyrightconfig.json .pycheckers .pylintrc .style.yapf .clang-format				\
 ballisticakit-cmake/.clang-format .editorconfig

# Prereq targets that may break if the project needs updating should go here.
# An example is compile-command-databases; these might try to run cmake and
# fail if the CMakeList files don't match what's on disk. If such a target was
# included in PREREQS_SAFE it would try to build *before* project updates
# which would leave us stuck in a broken state.
PREREQS_POST_UPDATE_ONLY = $(PREREQ_COMPILE_COMMANDS_DB)

# Target that should be built before running most any other build.
# This installs tool config files, runs environment checks, etc.
prereqs: $(PREREQS_SAFE) $(PREREQS_POST_UPDATE_ONLY)

# Set of prereqs safe to run if the project state is dirty.
prereqs-pre-update: $(PREREQS_SAFE)

prereqs-clean:
	rm -rf $(PREREQS_SAFE) $(PREREQS_POST_UPDATE_ONLY)

# Build all assets for all platforms.
assets: prereqs meta
	@$(PCOMMAND) lazybuild assets_src $(LAZYBUILDDIR)/$@ \
 cd src/assets \&\& $(MAKE) -j$(CPUS)

# Build assets required for cmake builds (linux, mac).
assets-cmake: prereqs meta
	@$(PCOMMAND) lazybuild assets_src $(LAZYBUILDDIR)/$@ \
 cd src/assets \&\& $(MAKE) -j$(CPUS) cmake

# Build only script assets for cmake builds (linux, mac).
assets-cmake-scripts: prereqs meta
	@$(PCOMMAND) lazybuild assets_src $(LAZYBUILDDIR)/$@ \
 cd src/assets \&\& $(MAKE) -j$(CPUS) scripts-cmake

# Build assets required for server builds.
assets-server: prereqs meta
	@$(PCOMMAND) lazybuild assets_src $(LAZYBUILDDIR)/$@ \
 cd src/assets \&\& $(MAKE) -j$(CPUS) server

# Build assets required for WINDOWS_PLATFORM windows builds.
assets-windows: prereqs meta
	@$(PCOMMAND) lazybuild assets_src $(LAZYBUILDDIR)/$@ \
 cd src/assets \&\& $(MAKE) -j$(CPUS) win-$(WINDOWS_PLATFORM)

# Build assets required for Win32 windows builds.
assets-windows-Win32: prereqs meta
	@$(PCOMMAND) lazybuild assets_src $(LAZYBUILDDIR)/$@ \
 cd src/assets \&\& $(MAKE) -j$(CPUS) win-Win32

# Build assets required for x64 windows builds.
assets-windows-x64: prereqs meta
	@$(PCOMMAND) lazybuild assets_src $(LAZYBUILDDIR)/$@ \
 cd src/assets \&\& $(MAKE) -j$(CPUS) win-x64

# Build assets required for mac xcode builds
assets-mac: prereqs meta
	@$(PCOMMAND) lazybuild assets_src $(LAZYBUILDDIR)/$@ \
 cd src/assets \&\& $(MAKE) -j$(CPUS) mac

# Build assets required for ios.
assets-ios: prereqs meta
	@$(PCOMMAND) lazybuild assets_src $(LAZYBUILDDIR)/$@ \
 cd src/assets \&\& $(MAKE) -j$(CPUS) ios

# Build assets required for android.
assets-android: prereqs meta
	@$(PCOMMAND) lazybuild assets_src $(LAZYBUILDDIR)/$@ \
 cd src/assets \&\& $(MAKE) -j$(CPUS) android

# Clean all assets.
assets-clean:
	@rm -f $(LAZYBUILDDIR)/assets*
	cd src/assets && $(MAKE) clean

# Build resources.
resources: prereqs meta
	@$(PCOMMAND) lazybuild resources_src $(LAZYBUILDDIR)/$@ \
 cd src/resources \&\& $(MAKE) -j$(CPUS)

# Clean resources.
resources-clean:
	rm -f $(LAZYBUILDDIR)/resources
	cd src/resources && $(MAKE) clean

# Build our generated sources.
#
# Meta builds can affect sources used by asset builds, resource builds, and
# compiles, so it should be listed as a dependency of any of those.
meta: prereqs
	@$(PCOMMAND) lazybuild meta_src $(LAZYBUILDDIR)/$@ \
 cd src/meta \&\& $(MAKE) -j$(CPUS)

# Clean our generated sources.
meta-clean:
	rm -f $(LAZYBUILDDIR)/meta
	cd src/meta && $(MAKE) clean

# Remove ALL files and directories that aren't managed by git (except for a
# few things such as localconfig.json).
clean:
	$(CHECK_CLEAN_SAFETY)
	rm -rf build  # Handle this part ourself; can confuse git.
	git clean -dfx $(ROOT_CLEAN_IGNORES)

# Show what clean would delete without actually deleting it.
clean-list:
	$(CHECK_CLEAN_SAFETY)
	@echo Would remove build  # Handle this part ourself; can confuse git.
	git clean -dnx $(ROOT_CLEAN_IGNORES)

# Build/update dummy python modules.
#
# IMPORTANT - building this target can kick off full builds/cleans and so it
# should not be built in parallel with other targets. See py_check_prereqs
# target for more info.
dummymodules: prereqs meta
	@$(PCOMMAND) lazybuild dummymodules_src $(LAZYBUILDDIR)/$@ \
 rm -rf build/dummymodules \&\& $(PCOMMAND) gen_dummy_modules

dummymodules-clean:
	rm -f $(LAZYBUILDDIR)/dummymodules
	rm -rf build/dummymodules

# Generate all docs.
#
# IMPORTANT: Docs generation targets may themselves run builds, so they should
#  be run alone serially and never in parallel alongside other builds.
docs:
	$(MAKE) docs-pdoc

docs-pdoc:
	@$(PCOMMAND) gen_docs_pdoc

pcommandbatch_speed_test: prereqs
	@$(PCOMMAND) pcommandbatch_speed_test $(PCOMMANDBATCH)

# Tell make which of these targets don't represent files.
.PHONY: help prereqs prereqs-pre-update prereqs-clean assets assets-cmake			\
        assets-cmake-scripts assets-windows assets-windows-Win32							\
        assets-windows-x64 assets-mac assets-ios assets-android assets-clean	\
        resources resources-clean meta meta-clean clean clean-list						\
        dummymodules docs docs-pdoc pcommandbatch_speed_test


################################################################################
#                                                                              #
#                                    Prefab                                    #
#                                                                              #
################################################################################

# Prebuilt binaries for various platforms.

# Assemble & run a gui debug build for this platform.
prefab-gui-debug: prefab-gui-debug-build
	$($(shell $(PCOMMAND) prefab_run_var gui-debug))

# Assemble & run a gui release build for this platform.
prefab-gui-release: prefab-gui-release-build
	$($(shell $(PCOMMAND) prefab_run_var gui-release))

# Assemble a debug build for this platform.
prefab-gui-debug-build:
	@$(PCOMMAND) make_prefab gui-debug

# Assemble a release build for this platform.
prefab-gui-release-build:
	@$(PCOMMAND) make_prefab gui-release

# Assemble & run a server debug build for this platform.
prefab-server-debug: prefab-server-debug-build
	$($(shell $(PCOMMAND) prefab_run_var server-debug))

# Assemble & run a server release build for this platform.
prefab-server-release: prefab-server-release-build
	$($(shell $(PCOMMAND) prefab_run_var server-release))

# Assemble a server debug build for this platform.
prefab-server-debug-build:
	@$(PCOMMAND) make_prefab server-debug

# Assemble a server release build for this platform.
prefab-server-release-build:
	@$(PCOMMAND) make_prefab server-release

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
	@$(PCOMMAND) ensure_prefab_platform mac_x86_64
	@$(RUN_PREFAB_MAC_X86_64_GUI_DEBUG)

prefab-mac-arm64-gui-debug: prefab-mac-arm64-gui-debug-build
	@$(PCOMMAND) ensure_prefab_platform mac_arm64
	@$(RUN_PREFAB_MAC_ARM64_GUI_DEBUG)

prefab-mac-x86-64-gui-debug-build: prereqs assets-cmake \
   build/prefab/full/mac_x86_64_gui/debug/ballisticakit
	@$(STAGE_BUILD) -cmake -debug build/prefab/full/mac_x86_64_gui/debug

prefab-mac-arm64-gui-debug-build: prereqs assets-cmake \
   build/prefab/full/mac_arm64_gui/debug/ballisticakit
	@$(STAGE_BUILD) -cmake -debug build/prefab/full/mac_arm64_gui/debug

build/prefab/full/mac_%_gui/debug/ballisticakit: .efrocachemap
	@$(PCOMMANDBATCH) efrocache_get $@

build/prefab/lib/mac_%_gui/debug/libballisticaplus.a: .efrocachemap
	@$(PCOMMANDBATCH) efrocache_get $@

# Mac gui release:

RUN_PREFAB_MAC_X86_64_GUI_RELEASE = cd \
  build/prefab/full/mac_x86_64_gui/release && ./ballisticakit

RUN_PREFAB_MAC_ARM64_GUI_RELEASE = cd build/prefab/full/mac_arm64_gui/release \
  && ./ballisticakit

prefab-mac-x86-64-gui-release: prefab-mac-x86-64-gui-release-build
	@$(PCOMMAND) ensure_prefab_platform mac_x86_64
	@$(RUN_PREFAB_MAC_X86_64_GUI_RELEASE)

prefab-mac-arm64-gui-release: prefab-mac-arm64-gui_release-build
	@$(PCOMMAND) ensure_prefab_platform mac_arm64
	@$(RUN_PREFAB_MAC_ARM64_GUI_RELEASE)

prefab-mac-x86-64-gui-release-build: prereqs assets-cmake \
   build/prefab/full/mac_x86_64_gui/release/ballisticakit
	@$(STAGE_BUILD) -cmake -release build/prefab/full/mac_x86_64_gui/release

prefab-mac-arm64-gui-release-build: prereqs assets-cmake \
   build/prefab/full/mac_arm64_gui/release/ballisticakit
	@$(STAGE_BUILD) -cmake -release build/prefab/full/mac_arm64_gui/release

build/prefab/full/mac_%_gui/release/ballisticakit: .efrocachemap
	@$(PCOMMANDBATCH) efrocache_get $@

build/prefab/lib/mac_%_gui/release/libballisticaplus.a: .efrocachemap
	@$(PCOMMANDBATCH) efrocache_get $@

# Mac server debug:

RUN_PREFAB_MAC_X86_64_SERVER_DEBUG = cd \
 build/prefab/full/mac_x86_64_server/debug && ./ballisticakit_server

RUN_PREFAB_MAC_ARM64_SERVER_DEBUG = cd \
 build/prefab/full/mac_arm64_server/debug && ./ballisticakit_server

prefab-mac-x86-64-server-debug: prefab-mac-x86-64-server-debug-build
	@$(PCOMMAND) ensure_prefab_platform mac_x86_64
	@$(RUN_PREFAB_MAC_X86_64_SERVER_DEBUG)

prefab-mac-arm64-server-debug: prefab-mac-arm64-server-debug-build
	@$(PCOMMAND) ensure_prefab_platform mac_arm64
	@$(RUN_PREFAB_MAC_ARM64_SERVER_DEBUG)

prefab-mac-x86-64-server-debug-build: prereqs assets-server \
   build/prefab/full/mac_x86_64_server/debug/dist/ballisticakit_headless
	@$(STAGE_BUILD) -cmakeserver -debug build/prefab/full/mac_x86_64_server/debug

prefab-mac-arm64-server-debug-build: prereqs assets-server \
   build/prefab/full/mac_arm64_server/debug/dist/ballisticakit_headless
	@$(STAGE_BUILD) -cmakeserver -debug build/prefab/full/mac_arm64_server/debug

build/prefab/full/mac_%_server/debug/dist/ballisticakit_headless: .efrocachemap
	@$(PCOMMANDBATCH) efrocache_get $@

build/prefab/lib/mac_%_server/debug/libballisticaplus.a: .efrocachemap
	@$(PCOMMANDBATCH) efrocache_get $@

# Mac server release:

RUN_PREFAB_MAC_X86_64_SERVER_RELEASE = cd \
 build/prefab/full/mac_x86_64_server/release && ./ballisticakit_server

RUN_PREFAB_MAC_ARM64_SERVER_RELEASE = cd \
   build/prefab/full/mac_arm64_server/release && ./ballisticakit_server

prefab-mac-x86-64-server-release: prefab-mac-x86-64-server-release-build
	@$(PCOMMAND) ensure_prefab_platform mac_x86_64
	@$(RUN_PREFAB_MAC_X86_64_SERVER_RELEASE)

prefab-mac-arm64-server-release: prefab-mac-arm64-server-release-build
	@$(PCOMMAND) ensure_prefab_platform mac_arm64
	@$(RUN_PREFAB_MAC_ARM64_SERVER_RELEASE)

prefab-mac-x86-64-server-release-build: prereqs assets-server \
   build/prefab/full/mac_x86_64_server/release/dist/ballisticakit_headless
	@$(STAGE_BUILD) -cmakeserver -release \
      build/prefab/full/mac_x86_64_server/release

prefab-mac-arm64-server-release-build: prereqs assets-server \
   build/prefab/full/mac_arm64_server/release/dist/ballisticakit_headless
	@$(STAGE_BUILD) -cmakeserver -release \
      build/prefab/full/mac_arm64_server/release

build/prefab/full/mac_%_server/release/dist/ballisticakit_headless: .efrocachemap
	@$(PCOMMANDBATCH) efrocache_get $@

build/prefab/lib/mac_%_server/release/libballisticaplus.a: .efrocachemap
	@$(PCOMMANDBATCH) efrocache_get $@

# Linux gui debug:

RUN_PREFAB_LINUX_X86_64_GUI_DEBUG = cd \
  build/prefab/full/linux_x86_64_gui/debug && ./ballisticakit

RUN_PREFAB_LINUX_ARM64_GUI_DEBUG = cd \
  build/prefab/full/linux_arm64_gui/debug && ./ballisticakit

prefab-linux-x86-64-gui-debug: prefab-linux-x86-64-gui-debug-build
	@$(PCOMMAND) ensure_prefab_platform linux_x86_64
	@$(RUN_PREFAB_LINUX_X86_64_GUI_DEBUG)

prefab-linux-arm64-gui-debug: prefab-linux-arm64-gui-debug-build
	@$(PCOMMAND) ensure_prefab_platform linux_arm64
	@$(RUN_PREFAB_LINUX_ARM64_GUI_DEBUG)

prefab-linux-x86-64-gui-debug-build: prereqs assets-cmake \
   build/prefab/full/linux_x86_64_gui/debug/ballisticakit
	@$(STAGE_BUILD) -cmake -debug build/prefab/full/linux_x86_64_gui/debug

prefab-linux-arm64-gui-debug-build: prereqs assets-cmake \
   build/prefab/full/linux_arm64_gui/debug/ballisticakit
	@$(STAGE_BUILD) -cmake -debug build/prefab/full/linux_arm64_gui/debug

build/prefab/full/linux_%_gui/debug/ballisticakit: .efrocachemap
	@$(PCOMMANDBATCH) efrocache_get $@

build/prefab/lib/linux_%_gui/debug/libballisticaplus.a: .efrocachemap
	@$(PCOMMANDBATCH) efrocache_get $@

# Linux gui release:

RUN_PREFAB_LINUX_X86_64_GUI_RELEASE = cd \
  build/prefab/full/linux_x86_64_gui/release && ./ballisticakit

RUN_PREFAB_LINUX_ARM64_GUI_RELEASE = cd \
  build/prefab/full/linux_arm64_gui/release && ./ballisticakit

prefab-linux-x86-64-gui-release: prefab-linux-x86-64-gui-release-build
	@$(PCOMMAND) ensure_prefab_platform linux_x86_64
	@$(RUN_PREFAB_LINUX_X86_64_GUI_RELEASE)

prefab-linux-arm64-gui-release: prefab-linux-arm64-gui-release-build
	@$(PCOMMAND) ensure_prefab_platform linux_arm64
	@$(RUN_PREFAB_LINUX_ARM64_GUI_RELEASE)

prefab-linux-x86-64-gui-release-build: prereqs assets-cmake \
   build/prefab/full/linux_x86_64_gui/release/ballisticakit
	@$(STAGE_BUILD) -cmake -release build/prefab/full/linux_x86_64_gui/release

prefab-linux-arm64-gui-release-build: prereqs assets-cmake \
   build/prefab/full/linux_arm64_gui/release/ballisticakit
	@$(STAGE_BUILD) -cmake -release build/prefab/full/linux_arm64_gui/release

build/prefab/full/linux_%_gui/release/ballisticakit: .efrocachemap
	@$(PCOMMANDBATCH) efrocache_get $@

build/prefab/lib/linux_%_gui/release/libballisticaplus.a: .efrocachemap
	@$(PCOMMANDBATCH) efrocache_get $@

# Linux server debug:

RUN_PREFAB_LINUX_X86_64_SERVER_DEBUG = cd \
   build/prefab/full/linux_x86_64_server/debug && ./ballisticakit_server

RUN_PREFAB_LINUX_ARM64_SERVER_DEBUG = cd \
   build/prefab/full/linux_arm64_server/debug && ./ballisticakit_server

prefab-linux-x86-64-server-debug: prefab-linux-x86-64-server-debug-build
	@$(PCOMMAND) ensure_prefab_platform linux_x86_64
	@$(RUN_PREFAB_LINUX_X86_64_SERVER_DEBUG)

prefab-linux-arm64-server-debug: prefab-linux-arm64-server-debug-build
	@$(PCOMMAND) ensure_prefab_platform linux_arm64
	@$(RUN_PREFAB_LINUX_ARM64_SERVER_DEBUG)

prefab-linux-x86-64-server-debug-build: prereqs assets-server \
   build/prefab/full/linux_x86_64_server/debug/dist/ballisticakit_headless
	@$(STAGE_BUILD) -cmakeserver -debug \
      build/prefab/full/linux_x86_64_server/debug

prefab-linux-arm64-server-debug-build: prereqs assets-server \
   build/prefab/full/linux_arm64_server/debug/dist/ballisticakit_headless
	@$(STAGE_BUILD) -cmakeserver -debug \
      build/prefab/full/linux_arm64_server/debug

build/prefab/full/linux_%_server/debug/dist/ballisticakit_headless: .efrocachemap
	@$(PCOMMANDBATCH) efrocache_get $@

build/prefab/lib/linux_%_server/debug/libballisticaplus.a: .efrocachemap
	@$(PCOMMANDBATCH) efrocache_get $@

# Linux server release:

RUN_PREFAB_LINUX_X86_64_SERVER_RELEASE = cd \
   build/prefab/full/linux_x86_64_server/release && ./ballisticakit_server

RUN_PREFAB_LINUX_ARM64_SERVER_RELEASE = cd \
   build/prefab/full/linux_arm64_server/release && ./ballisticakit_server

prefab-linux-x86-64-server-release: prefab-linux-x86-64-server-release-build
	@$(PCOMMAND) ensure_prefab_platform linux_x86_64
	@$(RUN_PREFAB_LINUX_X86_64_SERVER_RELEASE)

prefab-linux-arm64-server-release: prefab-linux-arm64-server-release-build
	@$(PCOMMAND) ensure_prefab_platform linux_arm64
	@$(RUN_PREFAB_LINUX_ARM64_SERVER_RELEASE)

prefab-linux-x86-64-server-release-build: prereqs assets-server \
   build/prefab/full/linux_x86_64_server/release/dist/ballisticakit_headless
	@$(STAGE_BUILD) -cmakeserver -release \
      build/prefab/full/linux_x86_64_server/release

prefab-linux-arm64-server-release-build: prereqs assets-server \
   build/prefab/full/linux_arm64_server/release/dist/ballisticakit_headless
	@$(STAGE_BUILD) -cmakeserver -release \
      build/prefab/full/linux_arm64_server/release

build/prefab/full/linux_%_server/release/dist/ballisticakit_headless: .efrocachemap
	@$(PCOMMANDBATCH) efrocache_get $@

build/prefab/lib/linux_%_server/release/libballisticaplus.a: .efrocachemap
	@$(PCOMMANDBATCH) efrocache_get $@

# Windows gui debug:

RUN_PREFAB_WINDOWS_X86_GUI_DEBUG = cd build/prefab/full/windows_x86_gui/debug \
  && ./BallisticaKit.exe

prefab-windows-x86-gui-debug: prefab-windows-x86-gui-debug-build
	@$(PCOMMAND) ensure_prefab_platform windows_x86
	@$(RUN_PREFAB_WINDOWS_X86_GUI_DEBUG)

prefab-windows-x86-gui-debug-build: prereqs assets-windows-$(WINPLAT_X86) \
   build/prefab/full/windows_x86_gui/debug/BallisticaKit.exe
	@$(STAGE_BUILD) -win-$(WINPLAT_X86) -debug \
      build/prefab/full/windows_x86_gui/debug

build/prefab/full/windows_x86_gui/debug/BallisticaKit.exe: .efrocachemap
	@$(PCOMMANDBATCH) efrocache_get $@

build/prefab/lib/windows/Debug_%/BallisticaKitGenericPlus.lib: .efrocachemap
	@$(PCOMMANDBATCH) efrocache_get $@

build/prefab/lib/windows/Debug_%/BallisticaKitGenericPlus.pdb: .efrocachemap
	@$(PCOMMANDBATCH) efrocache_get $@

# Windows gui release:

RUN_PREFAB_WINDOWS_X86_GUI_RELEASE = cd \
  build/prefab/full/windows_x86_gui/release && ./BallisticaKit.exe

prefab-windows-x86-gui-release: prefab-windows-x86-gui-release-build
	@$(PCOMMAND) ensure_prefab_platform windows_x86
	@$(RUN_PREFAB_WINDOWS_X86_GUI_RELEASE)

prefab-windows-x86-gui-release-build: prereqs \
   assets-windows-$(WINPLAT_X86) \
   build/prefab/full/windows_x86_gui/release/BallisticaKit.exe
	@$(STAGE_BUILD) -win-$(WINPLAT_X86) -release \
      build/prefab/full/windows_x86_gui/release

build/prefab/full/windows_x86_gui/release/BallisticaKit.exe: .efrocachemap
	@$(PCOMMANDBATCH) efrocache_get $@

build/prefab/lib/windows/Release_%/BallisticaKitGenericPlus.lib: .efrocachemap
	@$(PCOMMANDBATCH) efrocache_get $@

build/prefab/lib/windows/Release_%/BallisticaKitGenericPlus.pdb: .efrocachemap
	@$(PCOMMANDBATCH) efrocache_get $@

# Windows server debug:

RUN_PREFAB_WINDOWS_X86_SERVER_DEBUG = cd \
   build/prefab/full/windows_x86_server/debug \
   && dist/python_d.exe ballisticakit_server.py

prefab-windows-x86-server-debug: prefab-windows-x86-server-debug-build
	@$(PCOMMAND) ensure_prefab_platform windows_x86
	@$(RUN_PREFAB_WINDOWS_X86_SERVER_DEBUG)

prefab-windows-x86-server-debug-build: prereqs \
   assets-windows-$(WINPLAT_X86) \
   build/prefab/full/windows_x86_server/debug/dist/BallisticaKitHeadless.exe
	@$(STAGE_BUILD) -winserver-$(WINPLAT_X86) -debug \
      build/prefab/full/windows_x86_server/debug

build/prefab/full/windows_x86_server/debug/dist/BallisticaKitHeadless.exe: .efrocachemap
	@$(PCOMMANDBATCH) efrocache_get $@

build/prefab/lib/windows/Debug_%/BallisticaKitHeadlessPlus.lib: .efrocachemap
	@$(PCOMMANDBATCH) efrocache_get $@

build/prefab/lib/windows/Debug_%/BallisticaKitHeadlessPlus.pdb: .efrocachemap
	@$(PCOMMANDBATCH) efrocache_get $@

# Windows server release:

RUN_PREFAB_WINDOWS_X86_SERVER_RELEASE = cd \
   build/prefab/full/windows_x86_server/release \
   && dist/python.exe -O ballisticakit_server.py

prefab-windows-x86-server-release: prefab-windows-x86-server-release-build
	@$(PCOMMAND) ensure_prefab_platform windows_x86
	@$(RUN_PREFAB_WINDOWS_X86_SERVER_RELEASE)

prefab-windows-x86-server-release-build: prereqs \
   assets-windows-$(WINPLAT_X86) \
   build/prefab/full/windows_x86_server/release/dist/BallisticaKitHeadless.exe
	@$(STAGE_BUILD) -winserver-$(WINPLAT_X86) -release \
      build/prefab/full/windows_x86_server/release

build/prefab/full/windows_x86_server/release/dist/BallisticaKitHeadless.exe: .efrocachemap
	@$(PCOMMANDBATCH) efrocache_get $@

build/prefab/lib/windows/Release_%/BallisticaKitHeadlessPlus.lib: .efrocachemap
	@$(PCOMMANDBATCH) efrocache_get $@

build/prefab/lib/windows/Release_%/BallisticaKitHeadlessPlus.pdb: .efrocachemap
	@$(PCOMMANDBATCH) efrocache_get $@

# Tell make which of these targets don't represent files.
.PHONY: prefab-gui-debug prefab-gui-release prefab-gui-debug-build						\
        prefab-gui-release-build prefab-server-debug prefab-server-release		\
        prefab-server-debug-build prefab-server-release-build prefab-clean		\
        _cmake_prefab_gui_binary _cmake_prefab_server_binary									\
        prefab-mac-x86-64-gui-debug prefab-mac-arm64-gui-debug								\
        prefab-mac-x86-64-gui-debug-build prefab-mac-arm64-gui-debug-build		\
        prefab-mac-x86-64-gui-release prefab-mac-arm64-gui-release						\
        prefab-mac-x86-64-gui-release-build																		\
        prefab-mac-arm64-gui-release-build prefab-mac-x86-64-server-debug			\
        prefab-mac-arm64-server-debug prefab-mac-x86-64-server-debug-build		\
        prefab-mac-arm64-server-debug-build prefab-mac-x86-64-server-release	\
        prefab-mac-arm64-server-release																				\
        prefab-mac-x86-64-server-release-build																\
        prefab-mac-arm64-server-release-build prefab-linux-x86-64-gui-debug		\
        prefab-linux-arm64-gui-debug prefab-linux-x86-64-gui-debug-build			\
        prefab-linux-arm64-gui-debug-build prefab-linux-x86-64-gui-release		\
        prefab-linux-arm64-gui-release prefab-linux-x86-64-gui-release-build	\
        prefab-linux-arm64-gui-release-build prefab-linux-x86-64-server-debug	\
        prefab-linux-arm64-server-debug																				\
        prefab-linux-x86-64-server-debug-build																\
        prefab-linux-arm64-server-debug-build																	\
        prefab-linux-x86-64-server-release prefab-linux-arm64-server-release	\
        prefab-linux-x86-64-server-release-build															\
        prefab-linux-arm64-server-release-build prefab-windows-x86-gui-debug	\
        prefab-windows-x86-gui-debug-build prefab-windows-x86-gui-release			\
        prefab-windows-x86-gui-release-build prefab-windows-x86-server-debug	\
        prefab-windows-x86-server-debug-build																	\
        prefab-windows-x86-server-release																			\
        prefab-windows-x86-server-release-build


################################################################################
#                                                                              #
#                                   Spinoff                                    #
#                                                                              #
################################################################################

SPINOFF_TEST_TARGET ?= core

# Run a given spinoff test.
spinoff-test:
	$(PCOMMAND) spinoff_test $(SPINOFF_TEST_TARGET) $(SPINOFF_TEST_EXTRA_ARGS)

# Build and check core feature set alone.
spinoff-test-core:
	$(PCOMMAND) spinoff_test core $(SPINOFF_TEST_EXTRA_ARGS)

# Build and check base feature set alone.
spinoff-test-base:
	$(PCOMMAND) spinoff_test base $(SPINOFF_TEST_EXTRA_ARGS)

# Build and check plus feature set alone.
spinoff-test-plus:
	$(PCOMMAND) spinoff_test plus $(SPINOFF_TEST_EXTRA_ARGS)

# Build and check classic feature set alone.
spinoff-test-classic:
	$(PCOMMAND) spinoff_test classic $(SPINOFF_TEST_EXTRA_ARGS)

# Build and check template_fs feature set alone.
spinoff-test-template_fs:
	$(PCOMMAND) spinoff_test template_fs $(SPINOFF_TEST_EXTRA_ARGS)

# Build and check ui_v1 feature set alone.
spinoff-test-ui_v1:
	$(PCOMMAND) spinoff_test ui_v1 $(SPINOFF_TEST_EXTRA_ARGS)

# Build and check ui_v1_lib feature set alone.
spinoff-test-ui_v1_lib:
	$(PCOMMAND) spinoff_test ui_v1_lib $(SPINOFF_TEST_EXTRA_ARGS)

# Build and check scene_v1 feature set alone.
spinoff-test-scene_v1:
	$(PCOMMAND) spinoff_test scene_v1 $(SPINOFF_TEST_EXTRA_ARGS)

# Build and check scene_v1_lib feature set alone.
spinoff-test-scene_v1_lib:
	$(PCOMMAND) spinoff_test scene_v1_lib $(SPINOFF_TEST_EXTRA_ARGS)

# Blow away all spinoff-test builds.
spinoff-test-clean:
	rm -rf build/spinofftest

# Grab the current parent project and sync it into ourself.
spinoff-update:
	@$(PCOMMAND) spinoff_check_submodule_parent
	$(MAKE) update
	@$(PCOMMANDBATCH) echo BLU Pulling current parent project...
	git submodule update
	@$(PCOMMANDBATCH) echo BLU Syncing parent into current project...
	tools/spinoff update
	@$(MAKE) update-check  # Make sure spinoff didn't break anything.
	@$(PCOMMANDBATCH) echo GRN Spinoff update successful!

# Upgrade to latest parent project and sync it into ourself.
spinoff-upgrade:
	@$(PCOMMAND) spinoff_check_submodule_parent
	$(MAKE) update
	@$(PCOMMANDBATCH) echo BLU Pulling latest parent project...
	cd submodules/ballistica && git checkout master && git pull
	@$(PCOMMANDBATCH) echo BLU Syncing parent into current project...
	tools/spinoff update
	@$(MAKE) update-check  # Make sure spinoff didn't break anything.
	@$(PCOMMANDBATCH) echo GRN Spinoff upgrade successful!

# Tell make which of these targets don't represent files.
.PHONY: spinoff-test-core spinoff-test-base spinoff-test-plus				\
        spinoff-test-template_fs spinoff-test-clean spinoff-update	\
        spinoff-upgrade


################################################################################
#                                                                              #
#                                   Updating                                   #
#                                                                              #
################################################################################

# Update any project files that need it (does NOT build projects).
update: prereqs-pre-update
	@$(PCOMMAND) update_project
# Though not technically necessary, let's keep things like tool-configs
# immediately updated so our editors/etc. better reflect the current state.
	@$(MAKE) -j$(CPUS) prereqs
	@$(PCOMMANDBATCH) echo GRN Update-Project: SUCCESS!

# Don't update but fail if anything needs it.
update-check: prereqs-pre-update
	@$(PCOMMAND) update_project --check
	@$(PCOMMANDBATCH) echo GRN Check-Project: Everything up to date.

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
	@$(PCOMMANDBATCH) echo BLD Formatting complete for $(notdir $(CURDIR))!

# Same but always formats; ignores dirty state.
format-full:
	@$(MAKE) -j$(CPUS) format-code-full format-scripts-full format-makefile
	@$(PCOMMANDBATCH) echo BLD Formatting complete for $(notdir $(CURDIR))!

# Run formatting for compiled code sources (.cc, .h, etc.).
format-code: prereqs
	@$(PCOMMAND) formatcode

# Same but always formats; ignores dirty state.
format-code-full: prereqs
	@$(PCOMMAND) formatcode -full

# Runs formatting for scripts (.py, etc).
format-scripts: prereqs
	@$(PCOMMAND) formatscripts

# Same but always formats; ignores dirty state.
format-scripts-full: prereqs
	@$(PCOMMAND) formatscripts -full

# Runs formatting on the project Makefile.
format-makefile: prereqs
	@$(PCOMMAND) formatmakefile

.PHONY: format format-full format-code format-code-full format-scripts	\
        format-scripts-full


################################################################################
#                                                                              #
#                                   Checking                                   #
#                                                                              #
################################################################################

# Run all project checks. (static analysis)
check: py_check_prereqs
	@$(DMAKE) -j$(CPUS) update-check cpplint pylint mypy
	@$(PCOMMANDBATCH) echo SGRN BLD ALL CHECKS PASSED!

# Same as check but no caching (all files are checked).
check-full: py_check_prereqs
	@$(DMAKE) -j$(CPUS) update-check cpplint-full pylint-full mypy-full
	@$(PCOMMANDBATCH) echo SGRN BLD ALL CHECKS PASSED!

# Same as 'check' plus optional/slow extra checks.
check2: py_check_prereqs
	@$(DMAKE) -j$(CPUS) update-check cpplint pylint mypy
	@$(PCOMMANDBATCH) echo SGRN BLD ALL CHECKS PASSED!

# Same as check2 but no caching (all files are checked).
check2-full: py_check_prereqs
	@$(DMAKE) -j$(CPUS) update-check cpplint-full pylint-full mypy-full
	@$(PCOMMANDBATCH) echo SGRN BLD ALL CHECKS PASSED!

# Run Cpplint checks on all C/C++ code.
cpplint: prereqs meta
	@$(PCOMMAND) cpplint

# Run Cpplint checks without caching (all files are checked).
cpplint-full: prereqs meta
	@$(PCOMMAND) cpplint -full

# Run Pylint checks on all Python Code.
pylint: py_check_prereqs
	@$(PCOMMAND) pylint

# Run Pylint checks without caching (all files are checked).
pylint-full: py_check_prereqs
	@$(PCOMMAND) pylint -full

# Run Mypy checks on all Python code.
mypy: py_check_prereqs
	@$(PCOMMAND) mypy

# Run Mypy checks without caching (all files are checked).
mypy-full: py_check_prereqs
	@$(PCOMMAND) mypy -full

# Run Mypy checks on all Python code using daemon mode.
dmypy: py_check_prereqs
	@$(PCOMMAND) dmypy

# Stop the mypy daemon
dmypy-stop: py_check_prereqs
	@$(PCOMMAND) dmypy -stop

# Run Pyright checks on all Python code.
pyright: py_check_prereqs
	@$(PCOMMAND) pyright

# Run PyCharm checks on all Python code.
pycharm: py_check_prereqs
	@$(PCOMMAND) pycharm

# Run PyCharm checks without caching (all files are checked).
pycharm-full: py_check_prereqs
	@$(PCOMMAND) pycharm -full

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
py_check_prereqs: dummymodules

# Tell make which of these targets don't represent files.
.PHONY: check check-full check2 check2-full cpplint cpplint-full pylint		\
        pylint-full mypy mypy-full dmypy dmypy-stop pycharm pycharm-full	\
        py_check_prereqs


################################################################################
#                                                                              #
#                                   Testing                                    #
#                                                                              #
################################################################################

# Set the following from the command line to influence the build:

# Override this to run only particular tests.
# Examples:
#   tests/test_efro
#   tests/test_efro/test_message.py
TEST_TARGET ?= tests

# Run all tests. (live execution verification)
test: py_check_prereqs
	@$(PCOMMANDBATCH) echo BLU Running all tests...
	@$(PCOMMAND) tests_warm_start
	@$(PCOMMAND) pytest -v $(TEST_TARGET)

test-verbose: py_check_prereqs
	@$(PCOMMANDBATCH) echo BLU Running all tests...
	@$(PCOMMAND) tests_warm_start
	@$(PCOMMAND) pytest -o log_cli=true -o log_cli_level=debug \
      -s -vv $(TEST_TARGET)

# Run tests with any caching disabled.
test-full: test

# Shortcut to test efro.message only.
test-message:
	@$(PCOMMAND) pytest -o log_cli=true -o log_cli_level=debug -s -vv \
      tests/test_efro/test_message.py

# Shortcut to test efro.dataclassio only.
test-dataclassio:
	@$(PCOMMAND) pytest -o log_cli=true -o log_cli_level=debug -s -vv	\
      tests/test_efro/test_dataclassio.py

# Shortcut to test efro.rpc only.
test-rpc:
	@$(PCOMMAND) pytest -o log_cli=true -o log_cli_level=debug -s -vv \
      tests/test_efro/test_rpc.py

# Tell make which of these targets don't represent files.
.PHONY: test test-verbose test-full test-message test-dataclassio test-rpc


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
	@$(PCOMMANDBATCH) echo SGRN BLD PREFLIGHT SUCCESSFUL!

# Same as 'preflight' without caching (all files are visited).
preflight-full:
	@$(MAKE) format-full
	@$(MAKE) update
	@$(MAKE) -j$(CPUS) cpplint-full pylint-full mypy-full test-full
	@$(PCOMMANDBATCH) echo SGRN BLD PREFLIGHT SUCCESSFUL!

# Same as 'preflight' plus optional/slow extra checks.
preflight2:
	@$(MAKE) format
	@$(MAKE) update
	@$(MAKE) -j$(CPUS) cpplint pylint mypy test
	@$(PCOMMANDBATCH) echo SGRN BLD PREFLIGHT SUCCESSFUL!

# Same as 'preflight2' but without caching (all files visited).
preflight2-full:
	@$(MAKE) format-full
	@$(MAKE) update
	@$(MAKE) -j$(CPUS) cpplint-full pylint-full mypy-full test-full
	@$(PCOMMANDBATCH) echo SGRN BLD PREFLIGHT SUCCESSFUL!

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
	$(STAGE_BUILD) -win-$(WINPLT) -$(WINCFGLC) build/windows/$(WINCFG)_$(WINPLT)

# Build and run a debug windows build (from WSL).
windows-debug: windows-debug-build
	@$(PCOMMAND) ensure_prefab_platform windows_x86
	build/windows/Debug_Win32/BallisticaKitGeneric.exe

# Build and run a release windows build (from WSL).
windows-release: windows-release-build
	@$(PCOMMAND) ensure_prefab_platform windows_x86
	build/windows/Release_Win32/BallisticaKitGeneric.exe

# Build a debug windows build (from WSL).
windows-debug-build: \
   build/prefab/lib/windows/Debug_Win32/BallisticaKitGenericPlus.lib \
   build/prefab/lib/windows/Debug_Win32/BallisticaKitGenericPlus.pdb
	@$(PCOMMAND) ensure_prefab_platform windows_x86
	@$(PCOMMAND) wsl_build_check_win_drive
	WINDOWS_CONFIGURATION=Debug WINDOWS_PLATFORM=Win32 $(MAKE) windows-staging
	WINDOWS_PROJECT=Generic WINDOWS_CONFIGURATION=Debug WINDOWS_PLATFORM=Win32 \
  $(MAKE) _windows-wsl-build

# Rebuild a debug windows build (from WSL).
windows-debug-rebuild: \
   build/prefab/lib/windows/Debug_Win32/BallisticaKitGenericPlus.lib \
   build/prefab/lib/windows/Debug_Win32/BallisticaKitGenericPlus.pdb
	@$(PCOMMAND) ensure_prefab_platform windows_x86
	@$(PCOMMAND) wsl_build_check_win_drive
	WINDOWS_CONFIGURATION=Debug WINDOWS_PLATFORM=Win32 $(MAKE) windows-staging
	WINDOWS_PROJECT=Generic WINDOWS_CONFIGURATION=Debug WINDOWS_PLATFORM=Win32 \
  $(MAKE) _windows-wsl-rebuild

# Build a release windows build (from WSL).
windows-release-build: \
   build/prefab/lib/windows/Release_Win32/BallisticaKitGenericPlus.lib \
   build/prefab/lib/windows/Release_Win32/BallisticaKitGenericPlus.pdb
	@$(PCOMMAND) ensure_prefab_platform windows_x86
	@$(PCOMMAND) wsl_build_check_win_drive
	WINDOWS_CONFIGURATION=Release WINDOWS_PLATFORM=Win32 $(MAKE) windows-staging
	WINDOWS_PROJECT=Generic WINDOWS_CONFIGURATION=Release WINDOWS_PLATFORM=Win32 \
  $(MAKE) _windows-wsl-build

# Rebuild a release windows build (from WSL).
windows-release-rebuild: \
   build/prefab/lib/windows/Release_Win32/BallisticaKitGenericPlus.lib \
   build/prefab/lib/windows/Release_Win32/BallisticaKitGenericPlus.pdb
	@$(PCOMMAND) ensure_prefab_platform windows_x86
	@$(PCOMMAND) wsl_build_check_win_drive
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

# This can be Debug, Release, RelWithDebInfo, or MinSizeRel.
CMAKE_BUILD_TYPE ?= Debug

# Build and run the cmake build.
cmake: cmake-build
	cd build/cmake/$(CM_BT_LC)/staged && ./ballisticakit

# Build and run the cmake build under the gdb debugger.
# Sets up the ballistica environment to do things like abort() out to the
# debugger on errors instead of trying to cleanly exit.
cmake-gdb: cmake-build
	cd build/cmake/$(CM_BT_LC)/staged && \
      BA_DEBUGGER_ATTACHED=1 gdb ./ballisticakit

# Build and run the cmake build under the lldb debugger.
# Sets up the ballistica environment to do things like abort() out to the
# debugger on errors instead of trying to cleanly exit.
cmake-lldb: cmake-build
	cd build/cmake/$(CM_BT_LC)/staged && \
      BA_DEBUGGER_ATTACHED=1 lldb ./ballisticakit

# Build but don't run it.
cmake-build: assets-cmake resources cmake-binary
	@$(STAGE_BUILD) -cmake -$(CM_BT_LC) -builddir build/cmake/$(CM_BT_LC) \
      build/cmake/$(CM_BT_LC)/staged
	@$(PCOMMANDBATCH) echo BLD Build complete: BLU build/cmake/$(CM_BT_LC)/staged

cmake-binary: meta
	@$(PCOMMAND) cmake_prep_dir build/cmake/$(CM_BT_LC)
	@cd build/cmake/$(CM_BT_LC) && test -f Makefile \
      || cmake -DCMAKE_BUILD_TYPE=$(CMAKE_BUILD_TYPE) \
      $(shell pwd)/ballisticakit-cmake
	@tools/pcommand update_cmake_prefab_lib standard $(CM_BT_LC) \
      build/cmake/$(CM_BT_LC)
	@cd build/cmake/$(CM_BT_LC) && $(MAKE) -j$(CPUS) ballisticakitbin

cmake-clean:
	rm -rf build/cmake/$(CM_BT_LC)

cmake-server: cmake-server-build
	cd build/cmake/server-$(CM_BT_LC)/staged && ./ballisticakit_server

cmake-server-build: assets-server meta cmake-server-binary
	@$(STAGE_BUILD) -cmakeserver -$(CM_BT_LC) \
      -builddir build/cmake/server-$(CM_BT_LC) \
      build/cmake/server-$(CM_BT_LC)/staged
	@$(PCOMMANDBATCH) echo BLD \
      Server build complete: BLU build/cmake/server-$(CM_BT_LC)/staged

cmake-server-binary: meta
	@$(PCOMMAND) cmake_prep_dir build/cmake/server-$(CM_BT_LC)
	@cd build/cmake/server-$(CM_BT_LC) && test -f Makefile \
      || cmake -DCMAKE_BUILD_TYPE=$(CMAKE_BUILD_TYPE) -DHEADLESS=true \
      $(shell pwd)/ballisticakit-cmake
	@tools/pcommand update_cmake_prefab_lib server $(CM_BT_LC) \
      build/cmake/server-$(CM_BT_LC)
	@cd build/cmake/server-$(CM_BT_LC) && $(MAKE) -j$(CPUS) ballisticakitbin

cmake-server-clean:
	rm -rf build/cmake/server-$(CM_BT_LC)

cmake-modular-build: assets-cmake meta cmake-modular-binary
	@$(STAGE_BUILD) -cmakemodular -$(CM_BT_LC) \
      -builddir build/cmake/modular-$(CM_BT_LC) \
      build/cmake/modular-$(CM_BT_LC)/staged
	@$(PCOMMANDBATCH) echo BLD \
      Modular build complete: BLU build/cmake/modular-$(CM_BT_LC)/staged

cmake-modular: cmake-modular-build
	cd build/cmake/modular-$(CM_BT_LC)/staged && ./ballisticakit

cmake-modular-binary: meta
	@$(PCOMMAND) cmake_prep_dir build/cmake/modular-$(CM_BT_LC)
	@cd build/cmake/modular-$(CM_BT_LC) && test -f Makefile \
      || cmake -DCMAKE_BUILD_TYPE=$(CMAKE_BUILD_TYPE) \
      $(shell pwd)/ballisticakit-cmake
	@tools/pcommand update_cmake_prefab_lib standard $(CM_BT_LC) \
      build/cmake/modular-$(CM_BT_LC)
	@cd build/cmake/modular-$(CM_BT_LC) && $(MAKE) -j$(CPUS) ballisticakitso

cmake-modular-clean:
	rm -rf build/cmake/modular-$(CM_BT_LC)

cmake-modular-server: cmake-modular-server-build
	cd build/cmake/modular-server-$(CM_BT_LC)/staged && ./ballisticakit_server

cmake-modular-server-build: assets-server meta cmake-modular-server-binary
	@$(STAGE_BUILD) -cmakemodularserver -$(CM_BT_LC) \
      -builddir build/cmake/modular-server-$(CM_BT_LC) \
      build/cmake/modular-server-$(CM_BT_LC)/staged
	@$(PCOMMANDBATCH) echo BLD \
      Server build complete: BLU build/cmake/modular-server-$(CM_BT_LC)/staged

cmake-modular-server-binary: meta
	@$(PCOMMAND) cmake_prep_dir build/cmake/modular-server-$(CM_BT_LC)
	@cd build/cmake/modular-server-$(CM_BT_LC) && test -f Makefile \
      || cmake -DCMAKE_BUILD_TYPE=$(CMAKE_BUILD_TYPE) -DHEADLESS=true \
      $(shell pwd)/ballisticakit-cmake
	@tools/pcommand update_cmake_prefab_lib server $(CM_BT_LC) \
      build/cmake/modular-server-$(CM_BT_LC)
	@cd build/cmake/modular-server-$(CM_BT_LC) && $(MAKE) \
      -j$(CPUS) ballisticakitso

cmake-modular-server-clean:
	rm -rf build/cmake/modular-server-$(CM_BT_LC)

# Stage assets for building/running within CLion.
clion-staging: assets-cmake resources meta
	$(STAGE_BUILD) -cmake -debug build/clion_debug
	$(STAGE_BUILD) -cmake -release build/clion_release

# Tell make which of these targets don't represent files.
.PHONY: cmake cmake-build cmake-clean cmake-server cmake-server-build	\
        cmake-server-clean cmake-modular-build cmake-modular					\
        cmake-modular-binary cmake-modular-clean cmake-modular-server	\
        cmake-modular-server-build cmake-modular-server-binary				\
        cmake-modular-server-clean clion-staging


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
VERSION = $(shell $(PCOMMAND) version version)
BUILD_NUMBER = $(shell $(PCOMMAND) version build)
BUILD_DIR = $(PROJ_DIR)/build
LAZYBUILDDIR = .cache/lazybuild
STAGE_BUILD = $(PROJ_DIR)/$(PCOMMAND) stage_build

# Things to ignore when doing root level cleans. Note that we exclude build
# and just blow that away manually; it might contain git repos or other things
# that can confuse git.
ROOT_CLEAN_IGNORES = --exclude=config/localconfig.json \
  --exclude=.spinoffdata \
  --exclude=/build

CHECK_CLEAN_SAFETY = $(PCOMMAND) check_clean_safety

# Some tool configs that need filtering (mainly injecting projroot path).
TOOL_CFG_INST = $(PCOMMAND) tool_config_install

# Anything that affects tool-config generation.
TOOL_CFG_SRC = tools/efrotools/toolconfig.py config/projectconfig.json

# Anything that should trigger an environment-check when changed.
ENV_SRC = $(PCOMMAND) tools/batools/build.py

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

.pyrightconfig.json: config/toolconfigsrc/pyrightconfig.yaml $(TOOL_CFG_SRC)
	@$(TOOL_CFG_INST) $< $@

.pycheckers: config/toolconfigsrc/pycheckers $(TOOL_CFG_SRC)
	@$(TOOL_CFG_INST) $< $@

# Set this to 1 to skip environment checks.
SKIP_ENV_CHECKS ?= 0

.cache/checkenv: $(ENV_SRC)
	@if [ $(SKIP_ENV_CHECKS) -ne 1 ]; then \
      $(PCOMMAND) checkenv && mkdir -p .cache && touch .cache/checkenv; \
  fi

$(PCOMMANDBATCHBIN): src/tools/pcommandbatch/pcommandbatch.c \
                     src/tools/pcommandbatch/cJSON.c
	@$(PCOMMAND) build_pcommandbatch $^ $@

# CMake build-type lowercase
CM_BT_LC = $(shell echo $(CMAKE_BUILD_TYPE) | tr A-Z a-z)

# Eww; no way to do multi-line constants in make without spaces :-(
_WMSBE_1 = \"C:\\Program Files\\Microsoft Visual Studio\\2022
_WMSBE_2 = \\Community\\MSBuild\\Current\\Bin\\MSBuild.exe\"
_WMSBE_1B = /mnt/c/Program Files/Microsoft Visual Studio/2022
_WMSBE_2B = /Community/MSBuild/Current/Bin/MSBuild.exe

VISUAL_STUDIO_VERSION = -property:VisualStudioVersion=17
WIN_MSBUILD_EXE = $(_WMSBE_1)$(_WMSBE_2)
WIN_MSBUILD_EXE_B = "$(_WMSBE_1B)$(_WMSBE_2B)"
WINPRJ = $(WINDOWS_PROJECT)
WINPLT = $(WINDOWS_PLATFORM)
WINCFG = $(WINDOWS_CONFIGURATION)
WINCFGLC = $(shell echo $(WINDOWS_CONFIGURATION) | tr A-Z a-z)

# When using CLion, our cmake dir is root. Expose .clang-format there too.
ballisticakit-cmake/.clang-format: .clang-format
	@mkdir -p ballisticakit-cmake
	@cd ballisticakit-cmake && ln -sf ../.clang-format .

# Various tools such as Irony for Emacs or clangd make use of a list of
# compile commands for all files; lets try to keep it up to date
# whenever CMakeLists changes.
.cache/compile_commands_db/compile_commands.json: \
      ballisticakit-cmake/CMakeLists.txt
	@$(PCOMMANDBATCH) echo BLU Updating compile commands db...
	@mkdir -p .cache/compile_commands_db
	@cd .cache/compile_commands_db \
      && cmake -DCMAKE_EXPORT_COMPILE_COMMANDS=ON -DCMAKE_BUILD_TYPE=Debug \
      $(shell pwd)/ballisticakit-cmake
	@mv .cache/compile_commands_db/compile_commands.json . \
      && rm -rf .cache/compile_commands_db \
      && mkdir .cache/compile_commands_db \
      && mv compile_commands.json .cache/compile_commands_db
	@$(PCOMMANDBATCH) echo BLU Created compile commands db at $@

_windows-wsl-build:
	@$(PCOMMAND) wsl_build_check_win_drive
	$(WIN_MSBUILD_EXE_B) \
   $(shell $(PCOMMAND) wsl_path_to_win --escape \
   ballisticakit-windows/$(WINPRJ)/BallisticaKit$(WINPRJ).vcxproj) \
   -target:Build \
   -property:Configuration=$(WINCFG) \
   -property:Platform=$(WINPLT) \
   $(VISUAL_STUDIO_VERSION)
	@$(PCOMMAND) echo BLU BLD Built build/windows/BallisticaKit$(WINPRJ).exe.

_windows-wsl-rebuild:
	@$(PCOMMAND) wsl_build_check_win_drive
	$(WIN_MSBUILD_EXE_B) \
   $(shell $(PCOMMAND) wsl_path_to_win --escape \
    ballisticakit-windows/$(WINPRJ)/BallisticaKit$(WINPRJ).vcxproj) \
   -target:Rebuild \
   -property:Configuration=$(WINCFG) \
   -property:Platform=$(WINPLT) \
   $(VISUAL_STUDIO_VERSION)
	@$(PCOMMAND) echo BLU BLD Built build/windows/BallisticaKit$(WINPRJ).exe.

# Tell make which of these targets don't represent files.
.PHONY: _windows-wsl-build _windows-wsl-rebuild
