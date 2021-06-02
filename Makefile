# Released under the MIT License. See LICENSE for details.
#
# This Makefile encompasses most high level functionality you should need when
# working with Ballistica. These build rules are also handy as reference or a
# starting point if you need specific funtionality beyond that exposed here.
# Targets in this top level Makefile do not expect -jX to be passed to them
# and generally handle spawning an appropriate number of child jobs themselves.

# Prefix used for output of docs/changelogs/etc. targets for use in webpages.
DOCPREFIX = "ballisticacore_"

# Set env-var BA_ENABLE_IRONY_BUILD_DB=1 to enable creating/updating a
# cmake compile-commands database for use with irony for emacs (and possibly
# other tools).
ifeq ($(BA_ENABLE_IRONY_BUILD_DB),1)
 PREREQ_IRONY = .cache/irony/compile_commands.json
endif


################################################################################
#                                                                              #
#                                   General                                    #
#                                                                              #
################################################################################

# List targets in this Makefile and basic descriptions for them.
help:
	@tools/pcommand makefile_target_list Makefile

PREREQS = .cache/checkenv $(PREREQ_IRONY) .dir-locals.el \
  .mypy.ini .pycheckers .pylintrc .style.yapf .clang-format \
  ballisticacore-cmake/.clang-format .projectile .editorconfig

# Target that should be built before running most any other build.
# This installs tool config files, runs environment checks, etc.
prereqs: ${PREREQS}

prereqs-clean:
	@rm -rf ${PREREQS}

# Build all assets for all platforms.
assets: prereqs
	@cd assets && make -j${CPUS}

# Build assets required for cmake builds (linux, mac)
assets-cmake: prereqs
	@cd assets && ${MAKE} -j${CPUS} cmake

# Build assets required for WINDOWS_PLATFORM windows builds.
assets-windows: prereqs
	@cd assets && ${MAKE} -j${CPUS} win-${WINDOWS_PLATFORM}

# Build assets required for Win32 windows builds.
assets-windows-Win32: prereqs
	@cd assets && ${MAKE} -j${CPUS} win-Win32

# Build assets required for x64 windows builds.
assets-windows-x64: prereqs
	@cd assets && ${MAKE} -j${CPUS} win-x64

# Build assets required for mac xcode builds
assets-mac: prereqs
	@cd assets && ${MAKE} -j${CPUS} mac

# Build assets required for ios.
assets-ios: prereqs
	@cd assets && ${MAKE} -j${CPUS} ios

# Build assets required for android.
assets-android: prereqs
	@cd assets && ${MAKE} -j${CPUS} android

# Clean all assets.
assets-clean:
	@cd assets && ${MAKE} clean

# Build resources.
resources: prereqs
	@tools/pcommand lazybuild resources_src ${LAZYBUILDDIR}/resources \
 cd resources \&\& ${MAKE} -j${CPUS} resources

# Clean resources.
resources-clean:
	@cd resources && ${MAKE} clean
	@rm -f ${LAZYBUILDDIR}/resources

# Build our generated code.
# TODO: should perhaps make this a more standard component, including it
# in other standard targets such as checks and tests (at least once we're
# generating things that can affect the outcome of said checks/tests).
code: prereqs
	@tools/pcommand lazybuild code_gen_src ${LAZYBUILDDIR}/code \
 cd src/generated_src \&\& ${MAKE} -j${CPUS} generated_code

# Clean our generated code.
code-clean:
	@cd src/generated_src && ${MAKE} clean
	@rm -f ${LAZYBUILDDIR}/code

# Remove ALL files and directories that aren't managed by git
# (except for a few things such as localconfig.json).
clean:
	@${CHECK_CLEAN_SAFETY}
	@git clean -dfx ${ROOT_CLEAN_IGNORES}

# Show what clean would delete without actually deleting it.
clean-list:
	@${CHECK_CLEAN_SAFETY}
	@git clean -dnx ${ROOT_CLEAN_IGNORES}

# Tell make which of these targets don't represent files.
.PHONY: help prereqs prereqs-clean assets assets-cmake assets-windows \
  assets-windows-Win32 assets-windows-x64 \
  assets-mac assets-ios assets-android assets-clean \
  resources resources-clean code code-clean \
  clean clean-list


################################################################################
#                                                                              #
#                                    Prefab                                    #
#                                                                              #
################################################################################

# Prebuilt binaries for various platforms.

# Assemble & run a debug build for this platform.
prefab-debug: prefab-debug-build
	${${shell tools/pcommand prefab_run_var debug}}

# Assemble & run a release build for this platform.
prefab-release: prefab-release-build
	${${shell tools/pcommand prefab_run_var release}}

# Assemble a debug build for this platform.
prefab-debug-build:
	@tools/pcommand make_prefab debug

# Assemble a release build for this platform.
prefab-release-build:
	@tools/pcommand make_prefab release

# Assemble & run a server debug build for this platform.
prefab-server-debug: prefab-server-debug-build
	${${shell tools/pcommand prefab_run_var server-debug}}

# Assemble & run a server release build for this platform.
prefab-server-release: prefab-server-release-build
	${${shell tools/pcommand prefab_run_var server-release}}

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

# (what visual studio calls their x86 target platform)
WINPLAT_X86 = Win32

# Mac debug:

RUN_PREFAB_MAC_X86_64_DEBUG = cd build/prefab/full/mac_x86_64/debug \
  && ./ballisticacore

RUN_PREFAB_MAC_ARM64_DEBUG = cd build/prefab/full/mac_arm64/debug \
  && ./ballisticacore

prefab-mac-x86-64-debug: prefab-mac-x86-64-debug-build
	@tools/pcommand ensure_prefab_platform mac_x86_64
	@${RUN_PREFAB_MAC_X86_64_DEBUG}

prefab-mac-arm64-debug: prefab-mac-arm64-debug-build
	@tools/pcommand ensure_prefab_platform mac_arm64
	@${RUN_PREFAB_MAC_ARM64_DEBUG}

prefab-mac-x86-64-debug-build: prereqs assets-cmake \
 build/prefab/full/mac_x86_64/debug/ballisticacore
	@${STAGE_ASSETS} -cmake build/prefab/full/mac_x86_64/debug

prefab-mac-arm64-debug-build: prereqs assets-cmake \
 build/prefab/full/mac_arm64/debug/ballisticacore
	@${STAGE_ASSETS} -cmake build/prefab/full/mac_arm64/debug

build/prefab/full/mac_%/debug/ballisticacore: .efrocachemap
	@tools/pcommand efrocache_get $@

build/prefab/lib/mac_%/debug/libballisticacore_internal.a: .efrocachemap
	@tools/pcommand efrocache_get $@

# Mac release:

RUN_PREFAB_MAC_X86_64_RELEASE = cd build/prefab/full/mac_x86_64/release \
  && ./ballisticacore

RUN_PREFAB_MAC_ARM64_RELEASE = cd build/prefab/full/mac_arm64/release \
  && ./ballisticacore

prefab-mac-x86-64-release: prefab-mac-x86-64-release-build
	@tools/pcommand ensure_prefab_platform mac_x86_64
	@${RUN_PREFAB_MAC_X86_64_RELEASE}

prefab-mac-arm64-release: prefab-mac-arm64-release-build
	@tools/pcommand ensure_prefab_platform mac_arm64
	@${RUN_PREFAB_MAC_ARM64_RELEASE}

prefab-mac-x86-64-release-build: prereqs assets-cmake \
 build/prefab/full/mac_x86_64/release/ballisticacore
	@${STAGE_ASSETS} -cmake build/prefab/full/mac_x86_64/release

prefab-mac-arm64-release-build: prereqs assets-cmake \
 build/prefab/full/mac_arm64/release/ballisticacore
	@${STAGE_ASSETS} -cmake build/prefab/full/mac_arm64/release

build/prefab/full/mac_%/release/ballisticacore: .efrocachemap
	@tools/pcommand efrocache_get $@

build/prefab/lib/mac_%/release/libballisticacore_internal.a: .efrocachemap
	@tools/pcommand efrocache_get $@

# Mac server debug:

RUN_PREFAB_MAC_X86_64_SERVER_DEBUG = cd \
 build/prefab/full/mac_x86_64_server/debug && ./ballisticacore_server

RUN_PREFAB_MAC_ARM64_SERVER_DEBUG = cd \
 build/prefab/full/mac_arm64_server/debug && ./ballisticacore_server

prefab-mac-x86-64-server-debug: prefab-mac-x86-64-server-debug-build
	@tools/pcommand ensure_prefab_platform mac_x86_64
	@${RUN_PREFAB_MAC_X86_64_SERVER_DEBUG}

prefab-mac-arm64-server-debug: prefab-mac-arm64-server-debug-build
	@tools/pcommand ensure_prefab_platform mac_arm64
	@${RUN_PREFAB_MAC_ARM64_SERVER_DEBUG}

prefab-mac-x86-64-server-debug-build: prereqs assets-cmake \
 build/prefab/full/mac_x86_64_server/debug/dist/ballisticacore_headless
	@${STAGE_ASSETS} -cmakeserver -debug build/prefab/full/mac_x86_64_server/debug

prefab-mac-arm64-server-debug-build: prereqs assets-cmake \
 build/prefab/full/mac_arm64_server/debug/dist/ballisticacore_headless
	@${STAGE_ASSETS} -cmakeserver -debug build/prefab/full/mac_arm64_server/debug

build/prefab/full/mac_%_server/debug/dist/ballisticacore_headless: .efrocachemap
	@tools/pcommand efrocache_get $@

build/prefab/lib/mac_%_server/debug/libballisticacore_internal.a: .efrocachemap
	@tools/pcommand efrocache_get $@

# Mac server release:

RUN_PREFAB_MAC_X86_64_SERVER_RELEASE = cd \
 build/prefab/full/mac_x86_64_server/release && ./ballisticacore_server

RUN_PREFAB_MAC_ARM64_SERVER_RELEASE = cd \
 build/prefab/full/mac_arm64_server/release && ./ballisticacore_server

prefab-mac-x86-64-server-release: prefab-mac-x86-64-server-release-build
	@tools/pcommand ensure_prefab_platform mac_x86_64
	@${RUN_PREFAB_MAC_X86_64_SERVER_RELEASE}

prefab-mac-arm64-server-release: prefab-mac-arm64-server-release-build
	@tools/pcommand ensure_prefab_platform mac_arm64
	@${RUN_PREFAB_MAC_ARM64_SERVER_RELEASE}

prefab-mac-x86-64-server-release-build: prereqs assets-cmake \
 build/prefab/full/mac_x86_64_server/release/dist/ballisticacore_headless
	@${STAGE_ASSETS} -cmakeserver -release \
      build/prefab/full/mac_x86_64_server/release

prefab-mac-arm64-server-release-build: prereqs assets-cmake \
 build/prefab/full/mac_arm64_server/release/dist/ballisticacore_headless
	@${STAGE_ASSETS} -cmakeserver -release \
      build/prefab/full/mac_arm64_server/release

build/prefab/full/mac_%_server/release/dist/ballisticacore_headless: .efrocachemap
	@tools/pcommand efrocache_get $@

build/prefab/lib/mac_%_server/release/libballisticacore_internal.a: .efrocachemap
	@tools/pcommand efrocache_get $@

# Linux debug:

RUN_PREFAB_LINUX_X86_64_DEBUG = cd \
  build/prefab/full/linux_x86_64/debug && ./ballisticacore

RUN_PREFAB_LINUX_ARM64_DEBUG = cd \
  build/prefab/full/linux_arm64/debug && ./ballisticacore

prefab-linux-x86-64-debug: prefab-linux-x86-64-debug-build
	@tools/pcommand ensure_prefab_platform linux_x86_64
	@${RUN_PREFAB_LINUX_X86_64_DEBUG}

prefab-linux-arm64-debug: prefab-linux-arm64-debug-build
	@tools/pcommand ensure_prefab_platform linux_arm64
	@${RUN_PREFAB_LINUX_ARM64_DEBUG}

prefab-linux-x86-64-debug-build: prereqs assets-cmake \
 build/prefab/full/linux_x86_64/debug/ballisticacore
	@${STAGE_ASSETS} -cmake build/prefab/full/linux_x86_64/debug

prefab-linux-arm64-debug-build: prereqs assets-cmake \
 build/prefab/full/linux_arm64/debug/ballisticacore
	@${STAGE_ASSETS} -cmake build/prefab/full/linux_arm64/debug

build/prefab/full/linux_%/debug/ballisticacore: .efrocachemap
	@tools/pcommand efrocache_get $@

build/prefab/lib/linux_%/debug/libballisticacore_internal.a: .efrocachemap
	@tools/pcommand efrocache_get $@

# Linux release:

RUN_PREFAB_LINUX_X86_64_RELEASE = cd \
  build/prefab/full/linux_x86_64/release && ./ballisticacore

RUN_PREFAB_LINUX_ARM64_RELEASE = cd \
  build/prefab/full/linux_arm64/release && ./ballisticacore

prefab-linux-x86-64-release: prefab-linux-x86-64-release-build
	@tools/pcommand ensure_prefab_platform linux_x86_64
	@${RUN_PREFAB_LINUX_X86_64_RELEASE}

prefab-linux-arm64-release: prefab-linux-arm64-release-build
	@tools/pcommand ensure_prefab_platform linux_arm64
	@${RUN_PREFAB_LINUX_ARM64_RELEASE}

prefab-linux-x86-64-release-build: prereqs assets-cmake \
 build/prefab/full/linux_x86_64/release/ballisticacore
	@${STAGE_ASSETS} -cmake build/prefab/full/linux_x86_64/release

prefab-linux-arm64-release-build: prereqs assets-cmake \
 build/prefab/full/linux_arm64/release/ballisticacore
	@${STAGE_ASSETS} -cmake build/prefab/full/linux_arm64/release

build/prefab/full/linux_%/release/ballisticacore: .efrocachemap
	@tools/pcommand efrocache_get $@

build/prefab/lib/linux_%/release/libballisticacore_internal.a: .efrocachemap
	@tools/pcommand efrocache_get $@

# Linux server debug:

RUN_PREFAB_LINUX_X86_64_SERVER_DEBUG = cd \
  build/prefab/full/linux_x86_64_server/debug && ./ballisticacore_server

RUN_PREFAB_LINUX_ARM64_SERVER_DEBUG = cd \
  build/prefab/full/linux_arm64_server/debug && ./ballisticacore_server

prefab-linux-x86-64-server-debug: prefab-linux-x86-64-server-debug-build
	@tools/pcommand ensure_prefab_platform linux_x86_64
	@${RUN_PREFAB_LINUX_X86_64_SERVER_DEBUG}

prefab-linux-arm64-server-debug: prefab-linux-arm64-server-debug-build
	@tools/pcommand ensure_prefab_platform linux_arm64
	@${RUN_PREFAB_LINUX_ARM64_SERVER_DEBUG}

prefab-linux-x86-64-server-debug-build: prereqs assets-cmake \
 build/prefab/full/linux_x86_64_server/debug/dist/ballisticacore_headless
	@${STAGE_ASSETS} -cmakeserver -debug \
      build/prefab/full/linux_x86_64_server/debug

prefab-linux-arm64-server-debug-build: prereqs assets-cmake \
 build/prefab/full/linux_arm64_server/debug/dist/ballisticacore_headless
	@${STAGE_ASSETS} -cmakeserver -debug \
      build/prefab/full/linux_arm64_server/debug

build/prefab/full/linux_%_server/debug/dist/ballisticacore_headless: .efrocachemap
	@tools/pcommand efrocache_get $@

build/prefab/lib/linux_%_server/debug/libballisticacore_internal.a: .efrocachemap
	@tools/pcommand efrocache_get $@

# Linux server release:

RUN_PREFAB_LINUX_X86_64_SERVER_RELEASE = cd \
  build/prefab/full/linux_x86_64_server/release && ./ballisticacore_server

RUN_PREFAB_LINUX_ARM64_SERVER_RELEASE = cd \
  build/prefab/full/linux_arm64_server/release && ./ballisticacore_server

prefab-linux-x86-64-server-release: prefab-linux-x86-64-server-release-build
	@tools/pcommand ensure_prefab_platform linux_x86_64
	@${RUN_PREFAB_LINUX_X86_64_SERVER_RELEASE}

prefab-linux-arm64-server-release: prefab-linux-arm64-server-release-build
	@tools/pcommand ensure_prefab_platform linux_arm64
	@${RUN_PREFAB_LINUX_ARM64_SERVER_RELEASE}

prefab-linux-x86-64-server-release-build: prereqs assets-cmake \
 build/prefab/full/linux_x86_64_server/release/dist/ballisticacore_headless
	@${STAGE_ASSETS} -cmakeserver -release \
      build/prefab/full/linux_x86_64_server/release

prefab-linux-arm64-server-release-build: prereqs assets-cmake \
 build/prefab/full/linux_arm64_server/release/dist/ballisticacore_headless
	@${STAGE_ASSETS} -cmakeserver -release \
      build/prefab/full/linux_arm64_server/release

build/prefab/full/linux_%_server/release/dist/ballisticacore_headless: .efrocachemap
	@tools/pcommand efrocache_get $@

build/prefab/lib/linux_%_server/release/libballisticacore_internal.a: .efrocachemap
	@tools/pcommand efrocache_get $@

# Windows debug:

RUN_PREFAB_WINDOWS_X86_DEBUG = cd build/prefab/full/windows_x86/debug \
  && ./BallisticaCore.exe

prefab-windows-x86-debug: prefab-windows-x86-debug-build
	@tools/pcommand ensure_prefab_platform windows_x86
	@{RUN_PREFAB_WINDOWS_X86_DEBUG}

prefab-windows-x86-debug-build: prereqs assets-windows-${WINPLAT_X86} \
 build/prefab/full/windows_x86/debug/BallisticaCore.exe
	@${STAGE_ASSETS} -win-${WINPLAT_X86}-Debug \
build/prefab/full/windows_x86/debug

build/prefab/full/windows_x86/debug/BallisticaCore.exe: .efrocachemap
	@tools/pcommand efrocache_get $@

# Windows release:

RUN_PREFAB_WINDOWS_X86_RELEASE = cd build/prefab/full/windows_x86/release \
 && ./BallisticaCore.exe

prefab-windows-x86-release: prefab-windows-x86-release-build
	@tools/pcommand ensure_prefab_platform windows_x86
	@{RUN_PREFAB_WINDOWS_X86_RELEASE}

prefab-windows-x86-release-build: prereqs \
 assets-windows-${WINPLAT_X86} \
 build/prefab/full/windows_x86/release/BallisticaCore.exe
	@${STAGE_ASSETS} -win-${WINPLAT_X86}-Release \
build/prefab/full/windows_x86/release

build/prefab/full/windows_x86/release/BallisticaCore.exe: .efrocachemap
	@tools/pcommand efrocache_get $@

# Windows server debug:

RUN_PREFAB_WINDOWS_X86_SERVER_DEBUG = cd \
 build/prefab/full/windows_x86_server/debug \
 && dist/python_d.exe ballisticacore_server.py

prefab-windows-x86-server-debug: prefab-windows-x86-server-debug-build
	@tools/pcommand ensure_prefab_platform windows_x86
	@{RUN_PREFAB_WINDOWS_X86_SERVER_DEBUG}

prefab-windows-x86-server-debug-build: prereqs \
 assets-windows-${WINPLAT_X86} \
 build/prefab/full/windows_x86_server/debug/dist/BallisticaCoreHeadless.exe
	@${STAGE_ASSETS} -winserver-${WINPLAT_X86}-Debug \
 build/prefab/full/windows_x86_server/debug

build/prefab/full/windows_x86_server/debug/dist/BallisticaCoreHeadless.exe: .efrocachemap
	@tools/pcommand efrocache_get $@

# Windows server release:

RUN_PREFAB_WINDOWS_X86_SERVER_RELEASE = cd \
  build/prefab/full/windows_x86_server/release \
  && dist/python.exe -O ballisticacore_server.py

prefab-windows-x86-server-release: prefab-windows-x86-server-release-build
	@tools/pcommand ensure_prefab_platform windows_x86
	@{RUN_PREFAB_WINDOWS_X86_SERVER_RELEASE}

prefab-windows-x86-server-release-build: prereqs \
 assets-windows-${WINPLAT_X86} \
 build/prefab/full/windows_x86_server/release/dist/BallisticaCoreHeadless.exe
	@${STAGE_ASSETS} -winserver-${WINPLAT_X86}-Release \
 build/prefab/full/windows_x86_server/release

build/prefab/full/windows_x86_server/release/dist/BallisticaCoreHeadless.exe: .efrocachemap
	@tools/pcommand efrocache_get $@

# Tell make which of these targets don't represent files.
.PHONY: prefab-debug prefab-release prefab-debug-build prefab-release-build \
 prefab-server-debug prefab-server-release prefab-server-debug-build \
 prefab-server-release-build prefab-clean _cmake_prefab_binary \
 _cmake_prefab_server_binary prefab-mac-x86-64-debug prefab-mac-arm64-debug \
 prefab-mac-x86-64-debug-build prefab-mac-arm64-debug-build \
 prefab-mac-x86-64-release prefab-mac-arm64-release \
 prefab-mac-x86-64-release-build prefab-mac-arm64-release-build \
 prefab-mac-x86-64-server-debug prefab-mac-arm64-server-debug \
 prefab-mac-x86-64-server-debug-build prefab-mac-arm64-server-debug-build \
 prefab-mac-x86-64-server-release prefab-mac-arm64-server-release \
 prefab-mac-x86-64-server-release-build prefab-mac-arm64-server-release-build \
 prefab-linux-x86-64-debug prefab-linux-arm64-debug \
 prefab-linux-x86-64-debug-build prefab-linux-arm64-debug-build \
 prefab-linux-x86-64-release prefab-linux-arm64-release \
 prefab-linux-x86-64-release-build prefab-linux-arm64-release-build \
 prefab-linux-x86-64-server-debug prefab-linux-arm64-server-debug \
 prefab-linux-x86-64-server-debug-build prefab-linux-arm64-server-debug-build \
 prefab-linux-x86-64-server-release prefab-linux-arm64-server-release \
 prefab-linux-x86-64-server-release-build \
 prefab-linux-arm64-server-release-build \
 prefab-windows-x86-debug prefab-windows-x86-debug-build \
 prefab-windows-x86-release prefab-windows-x86-release-build \
 prefab-windows-x86-server-debug prefab-windows-x86-server-debug-build \
 prefab-windows-x86-server-release prefab-windows-x86-server-release-build


################################################################################
#                                                                              #
#                                   Updating                                   #
#                                                                              #
################################################################################

# Update any project files that need it (does NOT build projects).
update: prereqs
	@tools/pcommand update_project

# Don't update but fail if anything needs it.
update-check: prereqs
	@tools/pcommand update_project --check

# Tell make which of these targets don't represent files.
.PHONY: update update-check


################################################################################
#                                                                              #
#                                  Formatting                                  #
#                                                                              #
################################################################################

# Run formatting on all files in the project considered 'dirty'.
format:
	@${MAKE} -j3 format-code format-scripts format-makefile
	@tools/pcommand echo BLD Formatting complete!

# Same but always formats; ignores dirty state.
format-full:
	@${MAKE} -j3 format-code-full format-scripts-full format-makefile
	@tools/pcommand echo BLD Formatting complete!

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
check: update-check
	@${MAKE} -j3 cpplint pylint mypy
	@tools/pcommand echo SGRN BLD ALL CHECKS PASSED!

# Same as check but no caching (all files are checked).
check-full: update-check
	@${MAKE} -j3 cpplint-full pylint-full mypy-full
	@tools/pcommand echo SGRN BLD ALL CHECKS PASSED!

# Same as 'check' plus optional/slow extra checks.
check2: update-check
	@${MAKE} -j4 cpplint pylint mypy pycharm
	@tools/pcommand echo SGRN BLD ALL CHECKS PASSED!

# Same as check2 but no caching (all files are checked).
check2-full: update-check
	@${MAKE} -j4 cpplint-full pylint-full mypy-full pycharm-full
	@tools/pcommand echo SGRN BLD ALL CHECKS PASSED!

# Run Cpplint checks on all C/C++ code.
cpplint: prereqs
	@tools/pcommand cpplint

# Run Cpplint checks without caching (all files are checked).
cpplint-full: prereqs
	@tools/pcommand cpplint -full

# Run Pylint checks on all Python Code.
pylint: prereqs
	@tools/pcommand pylint

# Run Pylint checks without caching (all files are checked).
pylint-full: prereqs
	@tools/pcommand pylint -full

# Run Mypy checks on all Python code.
mypy: prereqs
	@tools/pcommand mypy

# Run Mypy checks without caching (all files are checked).
mypy-full: prereqs
	@tools/pcommand mypy -full

# Run Mypy checks on all Python code using daemon mode.
dmypy: prereqs
	@tools/pcommand dmypy

# Stop the mypy daemon
dmypy-stop: prereqs
	@tools/pcommand dmypy -stop

# Run PyCharm checks on all Python code.
pycharm: prereqs
	@tools/pcommand pycharm

# Run PyCharm checks without caching (all files are checked).
pycharm-full: prereqs
	@tools/pcommand pycharm -full

# Tell make which of these targets don't represent files.
.PHONY: check check-full check2 check2-full \
  cpplint cpplint-full pylint pylint-full mypy \
  mypy-full pycharm pycharm-full


################################################################################
#                                                                              #
#                                   Testing                                    #
#                                                                              #
################################################################################

# Run all tests. (live execution verification)
test: prereqs
	@tools/pcommand echo BLU Running all tests...
	@tools/pcommand pytest -v tests

# Run tests with any caching disabled.
test-full: test

# Individual test with extra output enabled.
test-assetmanager:
	@tools/pcommand pytest -o log_cli=true -o log_cli_level=debug -s -vv \
      tests/test_ba/test_assetmanager.py::test_assetmanager

# Individual test with extra output enabled.
test-dataclassio:
	@tools/pcommand pytest -o log_cli=true -o log_cli_level=debug -s -vv \
      tests/test_efro/test_dataclassio.py

# Individual test with extra output enabled.
test-entity:
	@tools/pcommand pytest -o log_cli=true -o log_cli_level=debug -s -vv \
      tests/test_efro/test_entity.py

# Tell make which of these targets don't represent files.
.PHONY: test test-full test-assetmanager


################################################################################
#                                                                              #
#                                 Preflighting                                 #
#                                                                              #
################################################################################

# Format, update, check, & test the project. Do this before commits.
preflight:
	@${MAKE} format
	@${MAKE} update
	@${MAKE} -j4 cpplint pylint mypy test
	@tools/pcommand echo SGRN BLD PREFLIGHT SUCCESSFUL!

# Same as 'preflight' without caching (all files are visited).
preflight-full:
	@${MAKE} format-full
	@${MAKE} update
	@${MAKE} -j4 cpplint-full pylint-full mypy-full test-full
	@tools/pcommand echo SGRN BLD PREFLIGHT SUCCESSFUL!

# Same as 'preflight' plus optional/slow extra checks.
preflight2:
	@${MAKE} format
	@${MAKE} update
	@${MAKE} -j5 cpplint pylint mypy pycharm test
	@tools/pcommand echo SGRN BLD PREFLIGHT SUCCESSFUL!

# Same as 'preflight2' but without caching (all files visited).
preflight2-full:
	@${MAKE} format-full
	@${MAKE} update
	@${MAKE} -j5 cpplint-full pylint-full mypy-full pycharm-full test-full
	@tools/pcommand echo SGRN BLD PREFLIGHT SUCCESSFUL!

# Tell make which of these targets don't represent files.
.PHONY: preflight preflight-full preflight2 preflight2-full


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
	@cd build/cmake/$(CM_BT_LC) && ./ballisticacore

# Build but don't run it.
cmake-build: assets-cmake resources code
	@tools/pcommand cmake_prep_dir build/cmake/$(CM_BT_LC)
	@tools/pcommand update_cmake_prefab_lib standard ${CM_BT_LC} build/cmake/${CM_BT_LC}
	@${STAGE_ASSETS} -cmake build/cmake/$(CM_BT_LC)
	@cd build/cmake/$(CM_BT_LC) && test -f Makefile \
      || cmake -DCMAKE_BUILD_TYPE=$(CMAKE_BUILD_TYPE) \
      ${PWD}/ballisticacore-cmake
	@cd build/cmake/$(CM_BT_LC) && ${MAKE} -j${CPUS}

cmake-clean:
	rm -rf build/cmake/$(CM_BT_LC)

cmake-server: cmake-server-build
	@cd build/cmake/server-$(CM_BT_LC) && ./ballisticacore_server

cmake-server-build: assets-cmake resources code
	@tools/pcommand cmake_prep_dir build/cmake/server-$(CM_BT_LC)/dist
	@tools/pcommand update_cmake_prefab_lib server ${CM_BT_LC} build/cmake/server-${CM_BT_LC}/dist
	@${STAGE_ASSETS} -cmakeserver -${CM_BT_LC} build/cmake/server-$(CM_BT_LC)
	@cd build/cmake/server-$(CM_BT_LC)/dist && test -f Makefile \
      || cmake -DCMAKE_BUILD_TYPE=$(CMAKE_BUILD_TYPE) -DHEADLESS=true \
      ${PWD}/ballisticacore-cmake
	@cd build/cmake/server-$(CM_BT_LC)/dist && ${MAKE} -j${CPUS}
	@cd build/cmake/server-$(CM_BT_LC)/dist && test -f ballisticacore_headless \
      || ln -sf ballisticacore ballisticacore_headless

cmake-server-clean:
	rm -rf build/cmake/server-$(CM_BT_LC)

# Tell make which of these targets don't represent files.
.PHONY: cmake cmake-build cmake-clean cmake-server cmake-server-build \
      cmake-server-clean


################################################################################
#                                                                              #
#                                  Auxiliary                                   #
#                                                                              #
################################################################################

# This should give the cpu count on linux and mac; may need to expand this
# if using this on other platforms.
CPUS = $(shell getconf _NPROCESSORS_ONLN || echo 8)
PROJ_DIR = ${abspath ${CURDIR}}
VERSION = $(shell tools/version_utils version)
BUILD_NUMBER = $(shell tools/version_utils build)
BUILD_DIR = ${PROJ_DIR}/build
LAZYBUILDDIR = .cache/lazybuild
STAGE_ASSETS = ${PROJ_DIR}/tools/pcommand stage_assets

# Things to ignore when doing root level cleans.
ROOT_CLEAN_IGNORES = --exclude=assets/src_master \
  --exclude=config/localconfig.json \
  --exclude=.spinoffdata

CHECK_CLEAN_SAFETY = ${PROJ_DIR}/tools/pcommand check_clean_safety

# Some tool configs that need filtering (mainly injecting projroot path).
TOOL_CFG_INST = tools/pcommand tool_config_install

# Anything that affects tool-config generation.
TOOL_CFG_SRC = tools/efrotools/pcommand.py config/config.json

# Anything that should trigger an environment-check when changed.
ENV_SRC = tools/pcommand tools/batools/build.py

.clang-format: config/toolconfigsrc/clang-format ${TOOL_CFG_SRC}
	@${TOOL_CFG_INST} $< $@

.style.yapf: config/toolconfigsrc/style.yapf ${TOOL_CFG_SRC}
	@${TOOL_CFG_INST} $< $@

.pylintrc: config/toolconfigsrc/pylintrc ${TOOL_CFG_SRC}
	@${TOOL_CFG_INST} $< $@

.projectile: config/toolconfigsrc/projectile ${TOOL_CFG_SRC}
	@${TOOL_CFG_INST} $< $@

.editorconfig: config/toolconfigsrc/editorconfig ${TOOL_CFG_SRC}
	@${TOOL_CFG_INST} $< $@

.dir-locals.el: config/toolconfigsrc/dir-locals.el ${TOOL_CFG_SRC}
	@${TOOL_CFG_INST} $< $@

.mypy.ini: config/toolconfigsrc/mypy.ini ${TOOL_CFG_SRC}
	@${TOOL_CFG_INST} $< $@

.pycheckers: config/toolconfigsrc/pycheckers ${TOOL_CFG_SRC}
	@${TOOL_CFG_INST} $< $@

# Set this to 1 to skip environment checks.
SKIP_ENV_CHECKS ?= 0

.cache/checkenv: ${ENV_SRC}
	@if [ ${SKIP_ENV_CHECKS} -ne 1 ]; then \
      tools/pcommand checkenv && mkdir -p .cache && touch .cache/checkenv; \
  fi

# CMake build-type lowercase
CM_BT_LC = $(shell echo $(CMAKE_BUILD_TYPE) | tr A-Z a-z)

# When using CLion, our cmake dir is root. Expose .clang-format there too.
ballisticacore-cmake/.clang-format: .clang-format
	@cd ballisticacore-cmake && ln -sf ../.clang-format .

# Simple target for CI to build a binary but not download/assemble assets/etc.
_cmake-simple-ci-server-build:
	SKIP_ENV_CHECKS=1 ${MAKE} code
	rm -rf build/cmake_simple_ci_server_build
	mkdir -p build/cmake_simple_ci_server_build
	tools/pcommand update_cmake_prefab_lib \
      server debug build/cmake_simple_ci_server_build
	cd build/cmake_simple_ci_server_build && \
      cmake -DCMAKE_BUILD_TYPE=Debug -DHEADLESS=true ${PWD}/ballisticacore-cmake
	cd build/cmake_simple_ci_server_build && ${MAKE} -j${CPUS}

# Irony in emacs requires us to use cmake to generate a full
# list of compile commands for all files; lets try to keep it up to date
# whenever CMakeLists changes.
.cache/irony/compile_commands.json: ballisticacore-cmake/CMakeLists.txt
	@tools/pcommand echo BLU Updating Irony build commands db...
	@echo Generating Irony compile-commands-list...
	@mkdir -p .cache/irony
	@cd .cache/irony \
      && cmake -DCMAKE_EXPORT_COMPILE_COMMANDS=ON -DCMAKE_BUILD_TYPE=Debug \
      ${PWD}/ballisticacore-cmake
	@mv .cache/irony/compile_commands.json . \
      && rm -rf .cache/irony \
      && mkdir .cache/irony \
      && mv compile_commands.json .cache/irony
	@tools/pcommand echo BLU Created Irony build db at $@

# Tell make which of these targets don't represent files.
.PHONY: _cmake-simple-ci-server-build
