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
help: env
	@$(PCOMMAND) makefile_target_list Makefile

# Set env-var BA_ENABLE_COMPILE_COMMANDS_DB=1 to enable creating/updating a
# cmake compile-commands database for use with things like clangd.
ifeq ($(BA_ENABLE_COMPILE_COMMANDS_DB),1)
 ENV_COMPILE_COMMANDS_DB = .cache/compile_commands_db/compile_commands.json
endif

# pcommandbatch can be much faster when running hundreds or thousands of
# commands, but has some downsides and limitations compared to regular
# pcommand. See tools/efrotools/pcommandbatch.py for more info on when to use
# which.
PCOMMAND = tools/pcommand
PCOMMANDBATCHBIN = .cache/pcommandbatch/pcommandbatch
ifeq ($(BA_PCOMMANDBATCH_ENABLE),0)
 PCOMMANDBATCH = $(PCOMMANDBATCHBIN)
else
 PCOMMANDBATCH = $(PCOMMAND)
endif

# Env targets that should be safe to run anytime; even if project-files
# are out of date.
ENV_REQS_SAFE = .cache/checkenv $(PCOMMANDBATCHBIN) .dir-locals.el .rgignore	\
 .mypy.ini .pyrightconfig.json .pylintrc .clang-format												\
 ballisticakit-cmake/.clang-format .editorconfig tools/cloudshell							\
 tools/bacloud tools/pcommand

# Env targets that may break if the project needs updating should go here.
# An example is compile-command-databases; these might try to run cmake and
# fail if the CMakeList files don't match what's on disk. If such a target was
# included in ENV_REQS_SAFE it would try to build *before* project updates
# which would leave us stuck in a broken state.
ENV_REQS_POST_UPDATE_ONLY = $(ENV_COMPILE_COMMANDS_DB)

# Target that should be built before building almost any other target. This
# installs tool config files, sets up the Python virtual environment, etc.
env: $(ENV_REQS_SAFE) $(ENV_REQS_POST_UPDATE_ONLY)

# Set of prereqs safe to run if the project state is dirty.
env-pre-update: $(ENV_REQS_SAFE)

env-clean:
	rm -rf $(ENV_REQS_SAFE) $(ENV_REQS_POST_UPDATE_ONLY)

# Build all assets for all platforms.
assets: env meta
	@$(PCOMMAND) lazybuild assets_src $(LAZYBUILDDIR)/$@ \
 cd src/assets \&\& $(MAKE) -j$(CPUS)

# Build assets required for cmake builds (linux, mac).
assets-cmake: env meta
	@$(PCOMMAND) lazybuild assets_src $(LAZYBUILDDIR)/$@ \
 cd src/assets \&\& $(MAKE) -j$(CPUS) cmake

# Build only script assets for cmake builds (linux, mac).
assets-cmake-scripts: env meta
	@$(PCOMMAND) lazybuild assets_src $(LAZYBUILDDIR)/$@ \
 cd src/assets \&\& $(MAKE) -j$(CPUS) scripts-cmake

# Build assets required for server builds.
assets-server: env meta
	@$(PCOMMAND) lazybuild assets_src $(LAZYBUILDDIR)/$@ \
 cd src/assets \&\& $(MAKE) -j$(CPUS) server

# Build assets required for WINDOWS_PLATFORM windows builds.
assets-windows: env meta
	@$(PCOMMAND) lazybuild assets_src $(LAZYBUILDDIR)/$@ \
 cd src/assets \&\& $(MAKE) -j$(CPUS) win-$(WINDOWS_PLATFORM)

# Build assets required for Win32 windows builds.
assets-windows-Win32: env meta
	@$(PCOMMAND) lazybuild assets_src $(LAZYBUILDDIR)/$@ \
 cd src/assets \&\& $(MAKE) -j$(CPUS) win-Win32

# Build assets required for x64 windows builds.
assets-windows-x64: env meta
	@$(PCOMMAND) lazybuild assets_src $(LAZYBUILDDIR)/$@ \
 cd src/assets \&\& $(MAKE) -j$(CPUS) win-x64

# Build assets required for mac xcode builds
assets-mac: env meta
	@$(PCOMMAND) lazybuild assets_src $(LAZYBUILDDIR)/$@ \
 cd src/assets \&\& $(MAKE) -j$(CPUS) mac

# Build assets required for ios.
assets-ios: env meta
	@$(PCOMMAND) lazybuild assets_src $(LAZYBUILDDIR)/$@ \
 cd src/assets \&\& $(MAKE) -j$(CPUS) ios

# Build assets required for android.
assets-android: env meta
	@$(PCOMMAND) lazybuild assets_src $(LAZYBUILDDIR)/$@ \
 cd src/assets \&\& $(MAKE) -j$(CPUS) android

# Clean all assets.
assets-clean:
	@rm -f $(LAZYBUILDDIR)/assets*
	cd src/assets && $(MAKE) clean

# Build resources.
resources: env meta
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
meta: env
	@$(PCOMMAND) lazybuild meta_src $(LAZYBUILDDIR)/$@ \
 cd src/meta \&\& $(MAKE) -j$(CPUS)

# Clean our generated sources.
meta-clean:
	rm -f $(LAZYBUILDDIR)/meta
	cd src/meta && $(MAKE) clean

# Remove ALL files and directories that aren't managed by git (except for a
# few things such as localconfig.json).
clean: env
	$(CHECK_CLEAN_SAFETY)
	rm -rf build  # Kill this ourself; can confuse git if contains other repos.
	git clean -dfx $(ROOT_CLEAN_IGNORES)

# Show what clean would delete without actually deleting it.
clean-list: env
	$(CHECK_CLEAN_SAFETY)
	@echo Would remove build  # Handle this part ourself; can confuse git.
	git clean -dnx $(ROOT_CLEAN_IGNORES)

# Build/update dummy python modules.
#
# IMPORTANT - building this target can kick off full builds/cleans and so it
# should not be built in parallel with other targets. See py_check_prepass
# target for more info.
dummymodules: env meta
	@$(PCOMMAND) lazybuild dummymodules_src $(LAZYBUILDDIR)/$@ \
 rm -rf build/dummymodules \&\& $(PCOMMAND) gen_dummy_modules

dummymodules-clean: env
	rm -f $(LAZYBUILDDIR)/dummymodules
	rm -rf build/dummymodules

# Build the project's Python virtual environment. This should happen
# automatically as a dependency of the env target.
venv: .venv/.efro_venv_complete

# Update pip requirements to latest versions.
venv-upgrade: env
	$(PCOMMAND) requirements_upgrade config/requirements.txt

venv-clean:
	rm -rf .venv

# Generate all docs.
#
# IMPORTANT: Docs generation targets may themselves run builds, so they should
#  be run alone serially and never in parallel alongside other builds.
docs: env
	@$(PCOMMAND) gen_docs_sphinx

docs-clean:
	rm -rf .cache/sphinx
	rm -rf .cache/sphinxfiltered
	rm -rf build/docs

pcommandbatch_speed_test: env
	@$(PCOMMAND) pcommandbatch_speed_test $(PCOMMANDBATCHBIN)

# Tell make which of these targets don't represent files.
.PHONY: help env env-pre-update env-clean assets assets-cmake			\
        assets-cmake-scripts assets-windows assets-windows-Win32							\
        assets-windows-x64 assets-mac assets-ios assets-android assets-clean	\
        resources resources-clean meta meta-clean clean clean-list						\
        dummymodules venv venv-clean docs docs-clean pcommandbatch_speed_test


################################################################################
#                                                                              #
#                                    Prefab                                    #
#                                                                              #
################################################################################

# Prebuilt binaries for various platforms.

# WSL is Linux but running under Windows, so it can target either. By default
# we want these top level targets (prefab-gui-debug, etc.) to yield native
# Windows builds from WSL, but this env var can be set to override that.
BA_WSL_TARGETS_WINDOWS ?= 1

# Assemble & run a gui debug build for this platform.
prefab-gui-debug: prefab-gui-debug-build
	$($(shell $(WSLU) $(PCOMMAND) prefab_run_var gui-debug))

# Assemble & run a gui release build for this platform.
prefab-gui-release: prefab-gui-release-build
	$($(shell $(WSLU) $(PCOMMAND) prefab_run_var gui-release))

# Assemble a debug build for this platform.
prefab-gui-debug-build: env
	@$(WSLU) $(PCOMMAND) make_prefab gui-debug

# Assemble a release build for this platform.
prefab-gui-release-build: env
	@$(WSLU) $(PCOMMAND) make_prefab gui-release

# Assemble & run a server debug build for this platform.
prefab-server-debug: prefab-server-debug-build
	$($(shell $(WSLU) $(PCOMMAND) prefab_run_var server-debug))

# Assemble & run a server release build for this platform.
prefab-server-release: prefab-server-release-build
	$($(shell $(WSLU) $(PCOMMAND) prefab_run_var server-release))

# Assemble a server debug build for this platform.
prefab-server-debug-build: env
	@$(WSLU) $(PCOMMAND) make_prefab server-debug

# Assemble a server release build for this platform.
prefab-server-release-build: env
	@$(WSLU) $(PCOMMAND) make_prefab server-release

# Clean all prefab builds.
prefab-clean:
	rm -rf build/prefab

# Specific platform prefab targets:

# Visual Studio platform name for prefab builds; can be Win32 or x64.
WINPREVSP = x64

# Associated name for our PrefabPlatform enum.
WINPREPLT = windows_x86_64

# Mac gui debug:

RUN_PREFAB_MAC_X86_64_GUI_DEBUG = cd build/prefab/full/mac_x86_64_gui/debug \
  && ./ballisticakit

RUN_PREFAB_MAC_ARM64_GUI_DEBUG = cd build/prefab/full/mac_arm64_gui/debug \
  && ./ballisticakit

prefab-mac-x86-64-gui-debug: prefab-mac-x86-64-gui-debug-build
	@$(PCOMMAND) ensure_prefab_platform mac_x86_64
	$(RUN_PREFAB_MAC_X86_64_GUI_DEBUG)

prefab-mac-arm64-gui-debug: prefab-mac-arm64-gui-debug-build
	@$(PCOMMAND) ensure_prefab_platform mac_arm64
	$(RUN_PREFAB_MAC_ARM64_GUI_DEBUG)

prefab-mac-x86-64-gui-debug-build: env assets-cmake \
   build/prefab/full/mac_x86_64_gui/debug/ballisticakit
	@$(STAGE_BUILD) -cmake -debug build/prefab/full/mac_x86_64_gui/debug

prefab-mac-arm64-gui-debug-build: env assets-cmake \
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
	$(RUN_PREFAB_MAC_X86_64_GUI_RELEASE)

prefab-mac-arm64-gui-release: prefab-mac-arm64-gui_release-build
	@$(PCOMMAND) ensure_prefab_platform mac_arm64
	$(RUN_PREFAB_MAC_ARM64_GUI_RELEASE)

prefab-mac-x86-64-gui-release-build: env assets-cmake \
   build/prefab/full/mac_x86_64_gui/release/ballisticakit
	@$(STAGE_BUILD) -cmake -release build/prefab/full/mac_x86_64_gui/release

prefab-mac-arm64-gui-release-build: env assets-cmake \
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
	$(RUN_PREFAB_MAC_ARM64_SERVER_DEBUG)

prefab-mac-x86-64-server-debug-build: env assets-server \
   build/prefab/full/mac_x86_64_server/debug/dist/ballisticakit_headless
	@$(STAGE_BUILD) -cmakeserver -debug build/prefab/full/mac_x86_64_server/debug

prefab-mac-arm64-server-debug-build: env assets-server \
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
	$(RUN_PREFAB_MAC_X86_64_SERVER_RELEASE)

prefab-mac-arm64-server-release: prefab-mac-arm64-server-release-build
	@$(PCOMMAND) ensure_prefab_platform mac_arm64
	$(RUN_PREFAB_MAC_ARM64_SERVER_RELEASE)

prefab-mac-x86-64-server-release-build: env assets-server \
   build/prefab/full/mac_x86_64_server/release/dist/ballisticakit_headless
	@$(STAGE_BUILD) -cmakeserver -release \
      build/prefab/full/mac_x86_64_server/release

prefab-mac-arm64-server-release-build: env assets-server \
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
	@$(WSLL) $(PCOMMAND) ensure_prefab_platform linux_x86_64
	$(RUN_PREFAB_LINUX_X86_64_GUI_DEBUG)

prefab-linux-arm64-gui-debug: prefab-linux-arm64-gui-debug-build
	@$(WSLL) $(PCOMMAND) ensure_prefab_platform linux_arm64
	$(RUN_PREFAB_LINUX_ARM64_GUI_DEBUG)

prefab-linux-x86-64-gui-debug-build: env assets-cmake \
   build/prefab/full/linux_x86_64_gui/debug/ballisticakit
	@$(STAGE_BUILD) -cmake -debug build/prefab/full/linux_x86_64_gui/debug

prefab-linux-arm64-gui-debug-build: env assets-cmake \
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
	@$(WSLL) $(PCOMMAND) ensure_prefab_platform linux_x86_64
	$(RUN_PREFAB_LINUX_X86_64_GUI_RELEASE)

prefab-linux-arm64-gui-release: prefab-linux-arm64-gui-release-build
	@$(WSLL) $(PCOMMAND) ensure_prefab_platform linux_arm64
	$(RUN_PREFAB_LINUX_ARM64_GUI_RELEASE)

prefab-linux-x86-64-gui-release-build: env assets-cmake \
   build/prefab/full/linux_x86_64_gui/release/ballisticakit
	@$(STAGE_BUILD) -cmake -release build/prefab/full/linux_x86_64_gui/release

prefab-linux-arm64-gui-release-build: env assets-cmake \
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
	@$(WSLL) $(PCOMMAND) ensure_prefab_platform linux_x86_64
	$(RUN_PREFAB_LINUX_X86_64_SERVER_DEBUG)

prefab-linux-arm64-server-debug: prefab-linux-arm64-server-debug-build
	@$(WSLL) $(PCOMMAND) ensure_prefab_platform linux_arm64
	$(RUN_PREFAB_LINUX_ARM64_SERVER_DEBUG)

prefab-linux-x86-64-server-debug-build: env assets-server \
   build/prefab/full/linux_x86_64_server/debug/dist/ballisticakit_headless
	@$(STAGE_BUILD) -cmakeserver -debug \
      build/prefab/full/linux_x86_64_server/debug

prefab-linux-arm64-server-debug-build: env assets-server \
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
	@$(WSLL) $(PCOMMAND) ensure_prefab_platform linux_x86_64
	$(RUN_PREFAB_LINUX_X86_64_SERVER_RELEASE)

prefab-linux-arm64-server-release: prefab-linux-arm64-server-release-build
	@$(WSLL) $(PCOMMAND) ensure_prefab_platform linux_arm64
	$(RUN_PREFAB_LINUX_ARM64_SERVER_RELEASE)

prefab-linux-x86-64-server-release-build: env assets-server \
   build/prefab/full/linux_x86_64_server/release/dist/ballisticakit_headless
	@$(STAGE_BUILD) -cmakeserver -release \
      build/prefab/full/linux_x86_64_server/release

prefab-linux-arm64-server-release-build: env assets-server \
   build/prefab/full/linux_arm64_server/release/dist/ballisticakit_headless
	@$(STAGE_BUILD) -cmakeserver -release \
      build/prefab/full/linux_arm64_server/release

build/prefab/full/linux_%_server/release/dist/ballisticakit_headless: .efrocachemap
	@$(PCOMMANDBATCH) efrocache_get $@

build/prefab/lib/linux_%_server/release/libballisticaplus.a: .efrocachemap
	@$(PCOMMANDBATCH) efrocache_get $@

# Windows gui debug:

RUN_PREFAB_WINDOWS_X86_64_GUI_DEBUG = cd \
 build/prefab/full/windows_x86_64_gui/debug && ./BallisticaKit.exe

prefab-windows-x86-64-gui-debug: prefab-windows-x86-64-gui-debug-build
	@$(WSLW) $(PCOMMAND) ensure_prefab_platform windows_x86_64
	$(RUN_PREFAB_WINDOWS_X86_64_GUI_DEBUG)

prefab-windows-x86-64-gui-debug-build: env assets-windows-$(WINPREVSP) \
   build/prefab/full/windows_x86_64_gui/debug/BallisticaKit.exe
	@$(STAGE_BUILD) -win-$(WINPREVSP) -debug \
      build/prefab/full/windows_x86_64_gui/debug

build/prefab/full/windows_x86_64_gui/debug/BallisticaKit.exe: .efrocachemap
	@$(PCOMMANDBATCH) efrocache_get $@

build/prefab/lib/windows/Debug_%/BallisticaKitGenericPlus.lib: .efrocachemap
	@$(PCOMMANDBATCH) efrocache_get $@

build/prefab/lib/windows/Debug_%/BallisticaKitGenericPlus.pdb: .efrocachemap
	@$(PCOMMANDBATCH) efrocache_get $@

# Windows gui release:

RUN_PREFAB_WINDOWS_X86_64_GUI_RELEASE = cd \
  build/prefab/full/windows_x86_64_gui/release && ./BallisticaKit.exe

prefab-windows-x86-64-gui-release: prefab-windows-x86-64-gui-release-build
	@$(WSLW) $(PCOMMAND) ensure_prefab_platform windows_x86_64
	$(RUN_PREFAB_WINDOWS_X86_64_GUI_RELEASE)

prefab-windows-x86-64-gui-release-build: env \
   assets-windows-$(WINPREVSP) \
   build/prefab/full/windows_x86_64_gui/release/BallisticaKit.exe
	@$(STAGE_BUILD) -win-$(WINPREVSP) -release \
      build/prefab/full/windows_x86_64_gui/release

build/prefab/full/windows_x86_64_gui/release/BallisticaKit.exe: .efrocachemap
	@$(PCOMMANDBATCH) efrocache_get $@

build/prefab/lib/windows/Release_%/BallisticaKitGenericPlus.lib: .efrocachemap
	@$(PCOMMANDBATCH) efrocache_get $@

build/prefab/lib/windows/Release_%/BallisticaKitGenericPlus.pdb: .efrocachemap
	@$(PCOMMANDBATCH) efrocache_get $@

# Windows server debug:

RUN_PREFAB_WINDOWS_X86_64_SERVER_DEBUG = cd \
   build/prefab/full/windows_x86_64_server/debug \
   && dist/python_d.exe ballisticakit_server.py

prefab-windows-x86-64-server-debug: prefab-windows-x86-64-server-debug-build
	@$(WSLW) $(PCOMMAND) ensure_prefab_platform windows_x86_64_64
	$(RUN_PREFAB_WINDOWS_X86_64_SERVER_DEBUG)

prefab-windows-x86-64-server-debug-build: env \
   assets-windows-$(WINPREVSP) \
   build/prefab/full/windows_x86_64_server/debug/dist/BallisticaKitHeadless.exe
	@$(STAGE_BUILD) -winserver-$(WINPREVSP) -debug \
      build/prefab/full/windows_x86_64_server/debug

build/prefab/full/windows_x86_64_server/debug/dist/BallisticaKitHeadless.exe: .efrocachemap
	@$(PCOMMANDBATCH) efrocache_get $@

build/prefab/lib/windows/Debug_%/BallisticaKitHeadlessPlus.lib: .efrocachemap
	@$(PCOMMANDBATCH) efrocache_get $@

build/prefab/lib/windows/Debug_%/BallisticaKitHeadlessPlus.pdb: .efrocachemap
	@$(PCOMMANDBATCH) efrocache_get $@

# Windows server release:

RUN_PREFAB_WINDOWS_X86_64_SERVER_RELEASE = cd \
   build/prefab/full/windows_x86_64_server/release \
   && dist/python.exe -O ballisticakit_server.py

prefab-windows-x86-64-server-release: prefab-windows-x86-64-server-release-build
	@$(WSLW) $(PCOMMAND) ensure_prefab_platform windows_x86_64
	$(RUN_PREFAB_WINDOWS_X86_64_SERVER_RELEASE)

prefab-windows-x86-64-server-release-build: env \
   assets-windows-$(WINPREVSP) \
 build/prefab/full/windows_x86_64_server/release/dist/BallisticaKitHeadless.exe
	@$(STAGE_BUILD) -winserver-$(WINPREVSP) -release \
      build/prefab/full/windows_x86_64_server/release

build/prefab/full/windows_x86_64_server/release/dist/BallisticaKitHeadless.exe: .efrocachemap
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
        prefab-linux-arm64-server-release-build                               \
        prefab-windows-x86-64-gui-debug	                                      \
        prefab-windows-x86-64-gui-debug-build                                 \
        prefab-windows-x86-64-gui-release                                     \
        prefab-windows-x86-64-gui-release-build                               \
        prefab-windows-x86-64-server-debug	                                  \
        prefab-windows-x86-64-server-debug-build                              \
        prefab-windows-x86-64-server-release                                  \
        prefab-windows-x86-64-server-release-build


################################################################################
#                                                                              #
#                                   Spinoff                                    #
#                                                                              #
################################################################################

SPINOFF_TEST_TARGET ?= core

# Run a given spinoff test.
spinoff-test: env
	$(PCOMMAND) spinoff_test $(SPINOFF_TEST_TARGET) $(SPINOFF_TEST_EXTRA_ARGS)

# Build and check core feature set alone.
spinoff-test-core: env
	$(PCOMMAND) spinoff_test core $(SPINOFF_TEST_EXTRA_ARGS)

# Build and check base feature set alone.
spinoff-test-base: env
	$(PCOMMAND) spinoff_test base $(SPINOFF_TEST_EXTRA_ARGS)

# Build and check plus feature set alone.
spinoff-test-plus: env
	$(PCOMMAND) spinoff_test plus $(SPINOFF_TEST_EXTRA_ARGS)

# Build and check classic feature set alone.
spinoff-test-classic: env
	$(PCOMMAND) spinoff_test classic $(SPINOFF_TEST_EXTRA_ARGS)

# Build and check template_fs feature set alone.
spinoff-test-template_fs: env
	$(PCOMMAND) spinoff_test template_fs $(SPINOFF_TEST_EXTRA_ARGS)

# Build and check ui_v1 feature set alone.
spinoff-test-ui_v1: env
	$(PCOMMAND) spinoff_test ui_v1 $(SPINOFF_TEST_EXTRA_ARGS)

# Build and check ui_v1_lib feature set alone.
spinoff-test-ui_v1_lib: env
	$(PCOMMAND) spinoff_test ui_v1_lib $(SPINOFF_TEST_EXTRA_ARGS)

# Build and check scene_v1 feature set alone.
spinoff-test-scene_v1: env
	$(PCOMMAND) spinoff_test scene_v1 $(SPINOFF_TEST_EXTRA_ARGS)

# Build and check scene_v1_lib feature set alone.
spinoff-test-scene_v1_lib: env
	$(PCOMMAND) spinoff_test scene_v1_lib $(SPINOFF_TEST_EXTRA_ARGS)

# Blow away all spinoff-test builds.
spinoff-test-clean: env
	rm -rf build/spinofftest

# Grab the current parent project and sync it into ourself.
spinoff-update: env
	@$(PCOMMAND) spinoff_check_submodule_parent
	$(MAKE) update
	@$(PCOMMANDBATCH) echo BLU Pulling current parent project...
	git submodule update
	@$(PCOMMANDBATCH) echo BLU Syncing parent into current project...
	tools/spinoff update
	@$(MAKE) update-check  # Make sure spinoff didn't break anything.
	@$(PCOMMANDBATCH) echo GRN Spinoff update successful!

# Upgrade to latest parent project and sync it into ourself.
spinoff-upgrade: env
	@$(PCOMMAND) spinoff_check_submodule_parent
	$(MAKE) update
	@$(PCOMMANDBATCH) echo BLU Pulling latest parent project...
	cd submodules/ballistica && git checkout main && git pull
	@$(PCOMMANDBATCH) echo BLU Syncing parent into current project...
	tools/spinoff update
	@$(MAKE) update-check  # Make sure spinoff didn't break anything.
	@$(PCOMMANDBATCH) echo GRN Spinoff upgrade successful!

# Tell make which of these targets don't represent files.
.PHONY: spinoff-test-core spinoff-test-base spinoff-test-plus       \
        spinoff-test-template_fs spinoff-test-clean spinoff-update  \
        spinoff-upgrade


################################################################################
#                                                                              #
#                                   Updating                                   #
#                                                                              #
################################################################################

# Update any project files that need it (does NOT build projects).
update: env-pre-update
	@$(PCOMMAND) update_project
# Though not technically necessary, let's keep things like tool-configs
# immediately updated so our editors/etc. better reflect the current state.
	@$(MAKE) -j$(CPUS) env
	@$(PCOMMANDBATCH) echo GRN Update-Project: SUCCESS!

# Don't update but fail if anything needs it.
update-check: env-pre-update
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
format: env
	@$(MAKE) -j$(CPUS) format-code format-scripts format-makefile
	@$(PCOMMANDBATCH) echo BLD Formatting complete for $(notdir $(CURDIR))!

# Same but always formats; ignores dirty state.
format-full: env
	@$(MAKE) -j$(CPUS) format-code-full format-scripts-full format-makefile
	@$(PCOMMANDBATCH) echo BLD Formatting complete for $(notdir $(CURDIR))!

# Run formatting for compiled code sources (.cc, .h, etc.).
format-code: env
	@$(PCOMMAND) formatcode

# Same but always formats; ignores dirty state.
format-code-full: env
	@$(PCOMMAND) formatcode -full

# Runs formatting for scripts (.py, etc).
format-scripts: env
	@$(PCOMMAND) formatscripts

# Same but always formats; ignores dirty state.
format-scripts-full: env
	@$(PCOMMAND) formatscripts -full

# Runs formatting on the project Makefile.
format-makefile: env
	@$(PCOMMAND) formatmakefile

.PHONY: format format-full format-code format-code-full format-scripts	\
        format-scripts-full


################################################################################
#                                                                              #
#                                   Checking                                   #
#                                                                              #
################################################################################

# Run all project checks. (static analysis)
check: py_check_prepass
	@$(DMAKE) -j$(CPUS) update-check cpplint pylint mypy
	@$(PCOMMANDBATCH) echo SGRN BLD ALL CHECKS PASSED!

# Same as check but no caching (all files are checked).
check-full: py_check_prepass
	@$(DMAKE) -j$(CPUS) update-check cpplint-full pylint-full mypy-full
	@$(PCOMMANDBATCH) echo SGRN BLD ALL CHECKS PASSED!

# Same as 'check' plus optional/slow extra checks.
check2: py_check_prepass
	@$(DMAKE) -j$(CPUS) update-check cpplint pylint mypy
	@$(PCOMMANDBATCH) echo SGRN BLD ALL CHECKS PASSED!

# Same as check2 but no caching (all files are checked).
check2-full: py_check_prepass
	@$(DMAKE) -j$(CPUS) update-check cpplint-full pylint-full mypy-full
	@$(PCOMMANDBATCH) echo SGRN BLD ALL CHECKS PASSED!

# Run Cpplint checks on all C/C++ code.
cpplint: env meta
	@$(PCOMMAND) cpplint

# Run Cpplint checks without caching (all files are checked).
cpplint-full: env meta
	@$(PCOMMAND) cpplint -full

# Run Pylint checks on all Python Code.
pylint: py_check_prepass
	@$(PCOMMAND) pylint

# Run Pylint checks without caching (all files are checked).
pylint-full: py_check_prepass
	@$(PCOMMAND) pylint -full

# Run Mypy checks on all Python code.
mypy: py_check_prepass
	@$(PCOMMAND) mypy

# Run Mypy checks without caching (all files are checked).
mypy-full: py_check_prepass
	@$(PCOMMAND) mypy -full

# Run Mypy checks on all Python code using daemon mode.
dmypy: py_check_prepass
	@$(PCOMMAND) dmypy

# Stop the mypy daemon
dmypy-stop: py_check_prepass
	@$(PCOMMAND) dmypy -stop

# Run Pyright checks on all Python code.
pyright: py_check_prepass
	@$(PCOMMAND) pyright

# Run PyCharm checks on all Python code.
pycharm: py_check_prepass
	@$(PCOMMAND) pycharm

# Run PyCharm checks without caching (all files are checked).
pycharm-full: py_check_prepass
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
py_check_prepass: dummymodules

# Tell make which of these targets don't represent files.
.PHONY: check check-full check2 check2-full cpplint cpplint-full pylint		\
        pylint-full mypy mypy-full dmypy dmypy-stop pycharm pycharm-full	\
        py_check_prepass


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

# Run tests (live execution verification).
test: py_check_prepass
	@$(PCOMMANDBATCH) echo BLU Running all tests...
	@$(PCOMMAND) tests_warm_start
	@$(PCOMMAND) pytest -v $(TEST_TARGET)

# Run tests (live execution verification). Excludes slow ones.
test-fast: py_check_prepass
	@$(PCOMMANDBATCH) echo BLU Running all tests \(fast\)...
	@$(PCOMMAND) tests_warm_start
	@BA_TEST_FAST_MODE=1 $(PCOMMAND) pytest -v $(TEST_TARGET)

test-verbose: py_check_prepass
	@$(PCOMMANDBATCH) echo BLU Running all tests...
	@$(PCOMMAND) tests_warm_start
	@$(PCOMMAND) pytest -o log_cli=true -o log_cli_level=debug \
      -s -vv $(TEST_TARGET)

# Run tests with any caching disabled.
test-full: test

# Run fast tests with any caching disabled.
test-fast-full: test-fast

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

# Shortcut to test efro.threadpool only.
test-threadpool:
	@$(PCOMMAND) pytest -o log_cli=true -o log_cli_level=debug -s -vv \
      tests/test_efro/test_threadpool.py

# Tell make which of these targets don't represent files.
.PHONY: test test-fast test-verbose test-full test-fast-full \
        test-message test-dataclassio test-rpc


################################################################################
#                                                                              #
#                                 Preflighting                                 #
#                                                                              #
################################################################################

# Format, update, check, & test the project. Do this before commits.
preflight:
	@$(MAKE) format
	@$(MAKE) update
	@$(MAKE) -j$(CPUS) py_check_prepass # Needs to be done explicitly first.
	@$(MAKE) -j$(CPUS) cpplint pylint mypy test-fast
	@$(PCOMMANDBATCH) echo SGRN BLD PREFLIGHT SUCCESSFUL!

# Same as 'preflight' without caching (all files are visited).
preflight-full:
	@$(MAKE) format-full
	@$(MAKE) update
	@$(MAKE) -j$(CPUS) py_check_prepass # Needs to be done explicitly first.
	@$(MAKE) -j$(CPUS) cpplint-full pylint-full mypy-full test-fast-full
	@$(PCOMMANDBATCH) echo SGRN BLD PREFLIGHT SUCCESSFUL!

# Same as 'preflight' plus optional/slow extra checks.
preflight2:
	@$(MAKE) format
	@$(MAKE) update
	@$(MAKE) -j$(CPUS) py_check_prepass # Needs to be done explicitly first.
	@$(MAKE) -j$(CPUS) cpplint pylint mypy test-fast
	@$(PCOMMANDBATCH) echo SGRN BLD PREFLIGHT SUCCESSFUL!

# Same as 'preflight2' but without caching (all files visited).
preflight2-full:
	@$(MAKE) format-full
	@$(MAKE) update
	@$(MAKE) -j$(CPUS) py_check_prepass # Needs to be done explicitly first.
	@$(MAKE) -j$(CPUS) cpplint-full pylint-full mypy-full test-fast-full
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
WINDOWS_PLATFORM ?= x64

# Can be Debug or Release
WINDOWS_CONFIGURATION ?= Debug

# Stage assets and other files so a built binary will run.
windows-staging: assets-windows resources meta
	@$(STAGE_BUILD) -win-$(WINPLT) -$(WINCFGLC) build/windows/$(WINCFG)_$(WINPLT)

# Build and run a debug windows build (from WSL).
windows-debug: windows-debug-build
	@$(WSLW) $(PCOMMAND) ensure_prefab_platform $(WINPREPLT)
	cd build/windows/Debug_$(WINPREVSP) && ./BallisticaKitGeneric.exe

# Build and run a release windows build (from WSL).
windows-release: windows-release-build
	@$(WSLW) $(PCOMMAND) ensure_prefab_platform $(WINPREPLT)
	cd build/windows/Release_$(WINPREVSP) && ./BallisticaKitGeneric.exe

# Build a debug windows build (from WSL).
windows-debug-build: env \
   build/prefab/lib/windows/Debug_$(WINPREVSP)/BallisticaKitGenericPlus.lib \
   build/prefab/lib/windows/Debug_$(WINPREVSP)/BallisticaKitGenericPlus.pdb
	@$(WSLW) $(PCOMMAND) ensure_prefab_platform $(WINPREPLT)
	@$(PCOMMAND) wsl_build_check_win_drive
	WINDOWS_CONFIGURATION=Debug WINDOWS_PLATFORM=$(WINPREVSP) \
 $(MAKE) windows-staging
	WINDOWS_PROJECT=Generic WINDOWS_CONFIGURATION=Debug \
 WINDOWS_PLATFORM=$(WINPREVSP) $(MAKE) _windows-wsl-build

# Rebuild a debug windows build (from WSL).
windows-debug-rebuild: env \
   build/prefab/lib/windows/Debug_$(WINPREVSP)/BallisticaKitGenericPlus.lib \
   build/prefab/lib/windows/Debug_$(WINPREVSP)/BallisticaKitGenericPlus.pdb
	@$(WSLW) $(PCOMMAND) ensure_prefab_platform $(WINPREPLT)
	@$(PCOMMAND) wsl_build_check_win_drive
	WINDOWS_CONFIGURATION=Debug WINDOWS_PLATFORM=$(WINPREVSP) \
 $(MAKE) windows-staging
	WINDOWS_PROJECT=Generic WINDOWS_CONFIGURATION=Debug \
 WINDOWS_PLATFORM=$(WINPREVSP) $(MAKE) _windows-wsl-rebuild

# Build a release windows build (from WSL).
windows-release-build: env \
   build/prefab/lib/windows/Release_$(WINPREVSP)/BallisticaKitGenericPlus.lib \
   build/prefab/lib/windows/Release_$(WINPREVSP)/BallisticaKitGenericPlus.pdb
	@$(WSLW) $(PCOMMAND) ensure_prefab_platform $(WINPREPLT)
	@$(PCOMMAND) wsl_build_check_win_drive
	WINDOWS_CONFIGURATION=Release WINDOWS_PLATFORM=$(WINPREVSP) \
 $(MAKE) windows-staging
	WINDOWS_PROJECT=Generic WINDOWS_CONFIGURATION=Release \
 WINDOWS_PLATFORM=$(WINPREVSP) $(MAKE) _windows-wsl-build

# Rebuild a release windows build (from WSL).
windows-release-rebuild: env \
   build/prefab/lib/windows/Release_$(WINPREVSP)/BallisticaKitGenericPlus.lib \
   build/prefab/lib/windows/Release_$(WINPREVSP)/BallisticaKitGenericPlus.pdb
	@$(WSLW) $(PCOMMAND) ensure_prefab_platform $(WINPREPLT)
	@$(PCOMMAND) wsl_build_check_win_drive
	WINDOWS_CONFIGURATION=Release WINDOWS_PLATFORM=$(WINPREVSP) \
 $(MAKE) windows-staging
	WINDOWS_PROJECT=Generic WINDOWS_CONFIGURATION=Release \
 WINDOWS_PLATFORM=$(WINPREVSP) $(MAKE) _windows-wsl-rebuild

# Remove all non-git-managed files in windows subdir.
windows-clean: env
	@$(CHECK_CLEAN_SAFETY)
	git clean -dfx ballisticakit-windows
	rm -rf build/windows $(LAZYBUILDDIR)

# Show what would be cleaned.
windows-clean-list: env
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
CMAKE_EXTRA_ARGS ?=

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
      || cmake -DCMAKE_BUILD_TYPE=$(CMAKE_BUILD_TYPE) $(CMAKE_EXTRA_ARGS)\
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
	@$(STAGE_BUILD) -cmake -debug build/clion_debug
	@$(STAGE_BUILD) -cmake -release build/clion_release

# Tell make which of these targets don't represent files.
.PHONY: cmake cmake-build cmake-clean cmake-server cmake-server-build	\
        cmake-server-clean cmake-modular-build cmake-modular					\
        cmake-modular-binary cmake-modular-clean cmake-modular-server	\
        cmake-modular-server-build cmake-modular-server-binary				\
        cmake-modular-server-clean clion-staging


################################################################################
#                                                                              #
#                                    Docker                                    #
#                                                                              #
################################################################################

# Build the gui release docker image
docker-gui-release: assets-cmake
	$(PCOMMAND) compose_docker_gui_release

# Build the gui debug docker image 
docker-gui-debug: assets-cmake
	$(PCOMMAND) compose_docker_gui_debug

# Build the server release docker image
docker-server-release: assets-cmake
	$(PCOMMAND) compose_docker_server_release

# Build the server debug docker image
docker-server-debug: assets-cmake
	$(PCOMMAND) compose_docker_server_debug

# Build the gui release docker image for arm64
docker-arm64-gui-release: assets-cmake
	$(PCOMMAND) compose_docker_arm64_gui_release

# Build the gui debug docker image for arm64
docker-arm64-gui-debug: assets-cmake
	$(PCOMMAND) compose_docker_arm64_gui_debug

# Build the server release docker image for arm64
docker-arm64-server-release: assets-cmake
	$(PCOMMAND) compose_docker_arm64_server_release 

# Build the server debug docker image for arm64
docker-arm64-server-debug: assets-cmake
	$(PCOMMAND) compose_docker_arm64_server_debug

# Save the bombsquad_server docker image to build/docker/bombsquad_server_docker.tar
docker-save:
	mkdir -p build/docker/
	$(PCOMMAND) save_docker_images

# Cleanup docker files
docker-clean:
	rm -rf build/docker/
	$(PCOMMAND) remove_docker_images
	docker system prune


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

# IMPORTANT: Make sure anything using these values has built env first (so
#            that pcommand exists).
VERSION = $(shell $(PCOMMAND) version version)
BUILD_NUMBER = $(shell $(PCOMMAND) version build)
STAGE_BUILD = $(PROJ_DIR)/$(PCOMMAND) stage_build

BUILD_DIR = $(PROJ_DIR)/build
LAZYBUILDDIR = .cache/lazybuild

# Things to ignore when doing root level cleans. Note that we exclude build
# and just blow that away manually; it might contain git repos or other things
# that can confuse git.
ROOT_CLEAN_IGNORES = --exclude=config/localconfig.json \
  --exclude=.spinoffdata \
  --exclude=/build

CHECK_CLEAN_SAFETY = $(PCOMMAND) check_clean_safety

# Some tool configs that need filtering (mainly injecting projroot path).
TOOL_CFG_INST = $(PCOMMAND) tool_config_install

# Anything required for tool-config generation.
TOOL_CFG_SRC = tools/efrotools/toolconfig.py config/projectconfig.json \
 tools/pcommand

# Anything that should trigger an environment-check when changed.
ENV_SRC = tools/batools/build.py .venv/.efro_venv_complete

# Generate a pcommand script hard-coded to use our virtual environment.
# This is an env dependency so should not itself depend on env.
tools/pcommand: tools/efrotools/genwrapper.py .venv/.efro_venv_complete
	@echo Generating tools/pcommand...
	@PYTHONPATH=tools python3 -m \
 efrotools.genwrapper pcommand batools.pcommandmain tools/pcommand

# Generate a cloudshell script hard-coded to use our virtual environment.
# This is an env dependency so should not itself depend on env.
tools/cloudshell: tools/efrotools/genwrapper.py .venv/.efro_venv_complete
	@echo Generating tools/cloudshell...
	@PYTHONPATH=tools python3 -m \
 efrotools.genwrapper cloudshell efrotoolsinternal.cloudshell tools/cloudshell

# Generate a bacloud script hard-coded to use our virtual environment.
# This is an env dependency so should not itself depend on env.
tools/bacloud: tools/efrotools/genwrapper.py .venv/.efro_venv_complete
	@echo Generating tools/bacloud...
	@PYTHONPATH=tools python3 -m \
 efrotools.genwrapper bacloud batools.bacloud tools/bacloud

.clang-format: config/toolconfigsrc/clang-format $(TOOL_CFG_SRC)
	@$(TOOL_CFG_INST) $< $@

.pylintrc: config/toolconfigsrc/pylintrc $(TOOL_CFG_SRC)
	@$(TOOL_CFG_INST) $< $@

.projectile: config/toolconfigsrc/projectile $(TOOL_CFG_SRC)
	@$(TOOL_CFG_INST) $< $@

.editorconfig: config/toolconfigsrc/editorconfig $(TOOL_CFG_SRC)
	@$(TOOL_CFG_INST) $< $@

.dir-locals.el: config/toolconfigsrc/dir-locals.el $(TOOL_CFG_SRC)
	@$(TOOL_CFG_INST) $< $@

.rgignore: config/toolconfigsrc/rgignore $(TOOL_CFG_SRC)
	@$(TOOL_CFG_INST) $< $@

.mypy.ini: config/toolconfigsrc/mypy.ini $(TOOL_CFG_SRC)
	@$(TOOL_CFG_INST) $< $@

.pyrightconfig.json: config/toolconfigsrc/pyrightconfig.toml $(TOOL_CFG_SRC)
	@$(TOOL_CFG_INST) $< $@

# Set this to 1 to skip environment checks.
SKIP_ENV_CHECKS ?= 0

VENV_PYTHON ?= python3.13

# Increment this to force all downstream venvs to fully rebuild. Useful after
# removing requirements since upgrading venvs in place will never uninstall
# stuff.
VENV_STATE = 3

# Update our virtual environment whenever reqs changes, Python version
# changes, our venv's Python symlink breaks (can happen for minor Python
# updates), or explicit state number changes. This is a dependency of env so
# should not itself depend on env.
.venv/.efro_venv_complete: \
      config/requirements.txt \
      tools/efrotools/pyver.py \
      .venv/bin/$(VENV_PYTHON) \
      .venv/.efro_venv_state_$(VENV_STATE)
# Update venv in place when possible; otherwise create from scratch.
	@[ -f .venv/bin/$(VENV_PYTHON) ] \
 && [ -f .venv/.efro_venv_state_$(VENV_STATE) ] \
 && echo Updating existing $(VENV_PYTHON) virtual environment in \'.venv\'... \
 || (echo Creating new $(VENV_PYTHON) virtual environment in \'.venv\'... \
 && rm -rf .venv && $(VENV_PYTHON) -m venv .venv \
 && touch .venv/.efro_venv_state_$(VENV_STATE))
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r config/requirements.txt
	@touch .venv/.efro_venv_complete # Done last to signal fully-built venv.
	@echo Project virtual environment for $(VENV_PYTHON) at .venv is ready to use.

# We don't actually create anything with this target, but its existence allows
# .efro_venv_complete to run when these bits don't exist, and that target
# *does* recreate this stuff. Note to self: previously I tried splitting
# things up more and recreating the venv in this target, but that led to
# unintuitive dependency behavior. For example, a python update could cause
# the .venv/bin/$(VENV_PYTHON) symlink to break, which would cause that target
# to blow away and rebuild the venv, but then the reestablished symlink might
# have an old modtime (since modtime is that of python itself) which could
# cause .efro_venv_complete to think it was already up to date and not run,
# leaving us with a half-built venv. So the way we do it now ensures the venv
# update always happens in full and seems mostly foolproof.
.venv/bin/$(VENV_PYTHON) .venv/.efro_venv_state_$(VENV_STATE):

.cache/checkenv: $(ENV_SRC) $(PCOMMAND)
	@if [ $(SKIP_ENV_CHECKS) -ne 1 ]; then \
      $(PCOMMAND) checkenv && mkdir -p .cache && touch .cache/checkenv; \
  fi

PCOMMANDBATCHSRC = src/tools/pcommandbatch/pcommandbatch.c	\
                     src/tools/pcommandbatch/cJSON.c

$(PCOMMANDBATCHBIN): $(PCOMMANDBATCHSRC) $(PCOMMAND)
	@$(PCOMMAND) build_pcommandbatch $(PCOMMANDBATCHSRC) $(PCOMMANDBATCHBIN)

# CMake build-type lowercase
CM_BT_LC = $(shell echo $(CMAKE_BUILD_TYPE) | tr A-Z a-z)

# Eww; no way to do multi-line constants in make without spaces :-(
_WMSBE_1 = \"C:\\Program Files\\Microsoft Visual Studio\\2022
_WMSBE_2 = \\Community\\MSBuild\\Current\\Bin\\MSBuild.exe\"
_WMSBE_1B = /mnt/c/Program Files/Microsoft Visual Studio/2022
_WMSBE_2B = /Community/MSBuild/Current/Bin/MSBuild.exe

# Sets WSL build type to the user's choice (defaults to Windows).
WSLU=BA_WSL_TARGETS_WINDOWS=$(BA_WSL_TARGETS_WINDOWS)
# Sets WSL build type to Linux.
WSLL=BA_WSL_TARGETS_WINDOWS=0
# Sets WSL build type to Windows.
WSLW=BA_WSL_TARGETS_WINDOWS=1

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
      $(PCOMMANDBATCH) \
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

_windows-wsl-build: env
	@$(PCOMMAND) wsl_build_check_win_drive
	$(WIN_MSBUILD_EXE_B) \
   $(shell $(PCOMMAND) wsl_path_to_win --escape \
   ballisticakit-windows/$(WINPRJ)/BallisticaKit$(WINPRJ).vcxproj) \
   -target:Build \
   -property:Configuration=$(WINCFG) \
   -property:Platform=$(WINPLT) \
   $(VISUAL_STUDIO_VERSION)
	@$(PCOMMAND) echo BLU BLD Built build/windows/BallisticaKit$(WINPRJ).exe.

_windows-wsl-rebuild: env
	@$(PCOMMAND) wsl_build_check_win_drive
	$(WIN_MSBUILD_EXE_B) \
   $(shell $(PCOMMAND) wsl_path_to_win --escape \
    ballisticakit-windows/$(WINPRJ)/BallisticaKit$(WINPRJ).vcxproj) \
   -target:Rebuild \
   -property:Configuration=$(WINCFG) \
   -property:Platform=$(WINPLT) \
   $(VISUAL_STUDIO_VERSION)
	@$(PCOMMAND) echo BLU BLD Built build/windows/BallisticaKit$(WINPRJ).exe.

_windows-update-dlls: env
	@$(PCOMMAND) windows_update_dlls

# Tell make which of these targets don't represent files.
.PHONY: _windows-wsl-build _windows-wsl-rebuild
