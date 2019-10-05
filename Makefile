# This Makefile encompasses most high level functionality you should need when
# working with the game. These rules are also handy as reference or a starting
# point if you need specific funtionality beyond what is here.
# The targets here do not expect -jX to be passed to them and generally
# add that argument to subprocesses as needed.

# Default is to build/run the mac version.
all: mac

# We often want one job per core, so try to determine our logical core count.
ifeq ($(wildcard /proc),/proc)  # Linux
  JOBS = $(shell cat /proc/cpuinfo | awk '/^processor/{print $3}' | wc -l)
else  # Mac
  JOBS = $(shell sysctl -n hw.ncpu)
endif

# Prefix used for output of docs/changelogs/etc targets for use in webpages.
DOCPREFIX = "ballisticacore_"

# Tell make which of these targets don't represent files.
.PHONY: all


################################################################################
#                                                                              #
#                                   General                                    #
#                                                                              #
################################################################################

# Prerequisites that should be in place before running most any other build;
# things like tool config files, etc.
PREREQS = .dir-locals.el .mypy.ini .pycheckers .pylintrc \
  .style.yapf .clang-format ballisticacore-cmake/.clang-format \
  .irony/compile_commands.json

# List the targets in this Makefile and basic descriptions for them.
list:
	@tools/snippets makefile_target_list Makefile

# Same as 'list'
help: list

prereqs: ${PREREQS}

prereqs-clean:
	rm -rf ${PREREQS} .irony

# Build all assets for all platforms.
assets:
	@cd assets && make -j${JOBS}

# Build only assets required for desktop builds (mac, pc, linux).
assets-desktop:
	@cd assets && make -j${JOBS} desktop

# Build only assets required for ios.
assets-ios:
	@cd assets && make -j${JOBS} ios

# Build only assets required for android.
assets-android:
	@cd assets && make -j${JOBS} android

# Clean all assets.
assets-clean:
	@cd assets && make clean

# Build resources.
resources: resources/Makefile
	@cd resources && make -j${JOBS} resources

# Clean resources.
resources-clean:
	@cd resources && make clean

# Build our generated code.
code:
	@cd src/generated_src && make -j${JOBS} generated_code

# Clean generated code.
code-clean:
	@cd src/generated_src && make clean

# Remove *ALL* files and directories that aren't managed by git
# (except for a few things such as localconfig.json).
clean:
	@${CHECK_CLEAN_SAFETY}
	@git clean -dfx ${ROOT_CLEAN_IGNORES}

# Show what clean would delete without actually deleting it.
cleanlist:
	@${CHECK_CLEAN_SAFETY}
	@git clean -dnx ${ROOT_CLEAN_IGNORES}

# For spinoff projects: pull in the newest parent project
# and sync changes into ourself.
spinoff-upgrade:
	@echo Pulling latest parent project...
	@cd submodules/ballistica && git checkout master && git pull
	@echo Syncing parent into current project...
	@tools/spinoff update
	@echo spinoff upgrade successful!

# Shortcut to run a spinoff upgrade and push to git.
spinoff-upgrade-push: spinoff-upgrade
	git add .
	git commit -m "spinoff upgrade"
	git push

# Force regenerate the dummy module.
dummymodule:
	./tools/gendummymodule.py --force

# Tell make which of these targets don't represent files.
.PHONY: list prereqs prereqs-clean assets assets-desktop assets-ios\
  assets-android assets-clean resources resources-clean code code-clean\
  clean cleanlist spinoff-upgrade spinoff-upgrade-push dummymodule


################################################################################
#                                                                              #
#                            Formatting / Checking                             #
#                                                                              #
################################################################################

# Note: Some of these targets have alternative flavors:
# 'full' - clears caches/etc so all files are reprocessed even if not dirty.
# 'fast' - takes some shortcuts for faster iteration, but may miss things

# Format code/scripts.

# Run formatting on all files in the project considered 'dirty'.
format:
	@make -j3 formatcode formatscripts formatmakefile
	@echo Formatting complete!

# Same but always formats; ignores dirty state.
formatfull:
	@make -j3 formatcodefull formatscriptsfull formatmakefile
	@echo Formatting complete!

# Run formatting for compiled code sources (.cc, .h, etc.).
formatcode: prereqs
	@tools/snippets formatcode

# Same but always formats; ignores dirty state.
formatcodefull: prereqs
	@tools/snippets formatcode -full

# Runs formatting for scripts (.py, etc).
formatscripts: prereqs
	@tools/snippets formatscripts

# Same but always formats; ignores dirty state.
formatscriptsfull: prereqs
	@tools/snippets formatscripts -full

formatmakefile: prereqs
	@tools/snippets formatmakefile

# Note: the '2' varieties include extra inspections such as PyCharm.
# These are useful, but can take significantly longer and/or be a bit flaky.

check: updatecheck
	@make -j3 cpplintcode pylintscripts mypyscripts
	@echo ALL CHECKS PASSED!
check2: updatecheck
	@make -j4 cpplintcode pylintscripts mypyscripts pycharmscripts
	@echo ALL CHECKS PASSED!

checkfast: updatecheck
	@make -j3 cpplintcode pylintscriptsfast mypyscripts
	@echo ALL CHECKS PASSED!
checkfast2: updatecheck
	@make -j4 cpplintcode pylintscriptsfast mypyscripts pycharmscripts
	@echo ALL CHECKS PASSED!

checkfull: updatecheck
	@make -j3 cpplintcodefull pylintscriptsfull mypyscriptsfull
	@echo ALL CHECKS PASSED!
checkfull2: updatecheck
	@make -j4 cpplintcodefull pylintscriptsfull mypyscriptsfull pycharmscriptsfull
	@echo ALL CHECKS PASSED!

cpplintcode: prereqs
	@tools/snippets cpplintcode

cpplintcodefull: prereqs
	@tools/snippets cpplintcode -full

pylintscripts: prereqs
	@tools/snippets pylintscripts

pylintscriptsfull: prereqs
	@tools/snippets pylintscripts -full

mypyscripts: prereqs
	@tools/snippets mypyscripts

mypyscriptsfull: prereqs
	@tools/snippets mypyscripts -full

pycharmscripts: prereqs
	@tools/snippets pycharmscripts

pycharmscriptsfull: prereqs
	@tools/snippets pycharmscripts -full

# 'Fast' script checking using dependency recursion limits.
# This can require much less re-checking but may miss problems in rare cases.
# Its not a bad idea to run a non-fast check every so often or before pushing.
pylintscriptsfast: prereqs
	@tools/snippets pylintscripts -fast

# Tell make which of these targets don't represent files.
.PHONY: format formatfull formatcode formatcodefull formatscripts \
  formatscriptsfull check check2 checkfast checkfast2 checkfull checkfull2 \
  cpplintcode cpplintcodefull pylintscripts pylintscriptsfull mypyscripts \
  mypyscriptsfull pycharmscripts pycharmscriptsfull


################################################################################
#                                                                              #
#                           Updating / Preflighting                            #
#                                                                              #
################################################################################

# Update any project files that need it (does NOT build projects).
update: prereqs
	@tools/update_project

# Don't update but fail if anything needs it.
updatecheck: prereqs
	@tools/update_project --check

# Run an update and check together; handy while iterating.
# (slightly more efficient than running update/check separately).
updatethencheck: update
	@make -j3 cpplintcode pylintscripts mypyscripts
	@echo ALL CHECKS PASSED!
updatethencheck2: update
	@make -j4 cpplintcode pylintscripts mypyscripts pycharmscripts
	@echo ALL CHECKS PASSED!

updatethencheckfast: update
	@make -j3 cpplintcode pylintscriptsfast mypyscripts
	@echo ALL CHECKS PASSED!
updatethencheckfast2: update
	@make -j4 cpplintcode pylintscriptsfast mypyscripts pycharmscripts
	@echo ALL CHECKS PASSED!

updatethencheckfull: update
	@make -j3 cpplintcodefull pylintscriptsfull mypyscriptsfull
	@echo ALL CHECKS PASSED!
updatethencheckfull2: update
	@make -j4 cpplintcodefull pylintscriptsfull mypyscriptsfull pycharmscriptsfull
	@echo ALL CHECKS PASSED!

# Run a format, an update, and then a check.
# Handy before pushing commits.

preflight:
	@make format
	@make updatethencheck
	@echo PREFLIGHT SUCCESSFUL!
preflight2:
	@make format
	@make updatethencheck2
	@echo PREFLIGHT SUCCESSFUL!

preflightfast:
	@make format
	@make updatethencheckfast
	@echo PREFLIGHT SUCCESSFUL!
preflightfast2:
	@make format
	@make updatethencheckfast2
	@echo PREFLIGHT SUCCESSFUL!

preflightfull:
	@make formatfull
	@make updatethencheckfull
	@echo PREFLIGHT SUCCESSFUL!
preflightfull2:
	@make formatfull
	@make updatethencheckfull2
	@echo PREFLIGHT SUCCESSFUL!

# Tell make which of these targets don't represent files.
.PHONY: update updatecheck updatethencheck updatethencheck2 \
  updatethencheckfast updatethencheckfast2 updatethencheckfull \
  updatethencheckfull2 preflight preflight2 preflightfast preflightfast2 \
  preflightfull preflightfull2


################################################################################
#                                                                              #
#                                    CMake                                     #
#                                                                              #
################################################################################

# Build and run the cmake build.
cmake: cmake-build
	@cd ballisticacore-cmake/build/debug && ./ballisticacore

# Build but don't run it.
cmake-build: assets-desktop resources code
	@${STAGE_ASSETS} -cmake ballisticacore-cmake/build/debug
	@cd ballisticacore-cmake/build/debug && test -f Makefile \
      || cmake -DCMAKE_BUILD_TYPE=Debug ../..
	@cd ballisticacore-cmake/build/debug && make -j${JOBS}

# Build and run it with an immediate quit command.
# Tests if the game is able to bootstrap itself.
cmake-launchtest: cmake-build
	@cd ballisticacore-cmake/build/debug \
      && ./ballisticacore -exec "ba.quit()"

# Build, sync to homebook fro, and run there.
cmake-hometest: cmake-build
	@rsync --verbose --recursive --links --checksum --delete -e "ssh -p 49136" \
      ballisticacore-cmake/build/ballisticacore/ \
      efro.duckdns.org:/Users/ericf/Documents/remote_ballisticacore_test
  # Note: use -t so the game sees a terminal and we get prompts & log output.
	@ssh -t -p 49136 efro.duckdns.org \
      cd /Users/ericf/Documents/remote_ballisticacore_test \&\& ./ballisticacore

cmake-clean:
	rm -rf ballisticacore-cmake/build/debug

cmake-server: cmake-server-build
	@cd ballisticacore-cmake/build/server-debug && ./ballisticacore

cmake-server-build: assets-desktop resources code
	@${STAGE_ASSETS} -cmake-server ballisticacore-cmake/build/server-debug
	@cd ballisticacore-cmake/build/server-debug && test -f Makefile \
      || cmake -DCMAKE_BUILD_TYPE=Debug -DHEADLESS=true ../..
	@cd ballisticacore-cmake/build/server-debug && make -j${JOBS}

cmake-server-clean:
	rm -rf ballisticacore-cmake/build/server-debug

# Tell make which of these targets don't represent files.
.PHONY: cmake cmake-build cmake-launchtest cmake-hometest cmake-clean \
  cmake-server cmake-server-build cmake-server-clean


################################################################################
#                                                                              #
#                                  Auxiliary                                   #
#                                                                              #
################################################################################

ROOT_DIR = ${abspath ${CURDIR}}
VERSION = $(shell tools/version_utils version)
BUILD_NUMBER = $(shell tools/version_utils build)
DIST_DIR = ${ROOT_DIR}/build

# Things to ignore when doing root level cleans.
ROOT_CLEAN_IGNORES = --exclude=assets/src_master \
  --exclude=config/localconfig.json \
  --exclude=.spinoffdata

CHECK_CLEAN_SAFETY = ${ROOT_DIR}/tools/snippets check_clean_safety
ASSET_CACHE_DIR = ${shell ${ROOT_DIR}/tools/convert_util --get-asset-cache-dir}
ASSET_CACHE_NAME = ${shell ${ROOT_DIR}/tools/convert_util \
  --get-asset-cache-name}
RPI_SERVER_PACKAGE_NAME = BallisticaCore_Server_RaspberryPi_${VERSION}

MAC_PACKAGE_NAME = BallisticaCore_Mac_${VERSION}
MAC_SERVER_PACKAGE_NAME = BallisticaCore_Server_Mac_${VERSION}
MAC_DIST_BUILD_DIR = ${shell ${ROOT_DIR}/tools/xc_build_path \
  ${ROOT_DIR}/ballisticacore-mac.xcodeproj Release}
MAC_DEBUG_BUILD_DIR = ${shell ${ROOT_DIR}/tools/xc_build_path \
  ${ROOT_DIR}/ballisticacore-mac.xcodeproj Debug}

STAGE_ASSETS = ${ROOT_DIR}/tools/stage_assets

# Eww; no way to do multi-line constants in make without spaces :-(
_WMSBE_1 = \"C:\\Program Files \(x86\)\\Microsoft Visual Studio\\2019
_WMSBE_2 = \\Community\\MSBuild\\Current\\Bin\\MSBuild.exe\"

WIN_INTERNAL_HOME = $(shell tools/vmshell win7 GET_INTERNAL_HOME)
WIN_MSBUILD_EXE = ${_WMSBE_1}${_WMSBE_2}
VISUAL_STUDIO_VERSION = /p:VisualStudioVersion=16
WIN_SERVER_PACKAGE_NAME = BallisticaCore_Server_Windows_${VERSION}
WIN_PACKAGE_NAME = BallisticaCore_Windows_${VERSION}
WIN_OCULUS_PACKAGE_NAME = BallisticaCore_Windows_Oculus
WINPRJ = $(WINDOWS_PROJECT)
WINPLT = $(WINDOWS_PLATFORM)
WINCFG = $(WINDOWS_CONFIGURATION)

# Assemble a package for a standard desktop build
_windows-package: windows-rebuild
	@mkdir -p ${DIST_DIR} && cd ${DIST_DIR} && \
      rm -rf ${WIN_PACKAGE_NAME}.zip ${WIN_PACKAGE_NAME} \
      && mkdir ${WIN_PACKAGE_NAME}
	@cd ${ROOT_DIR}/ballisticacore-windows/Build/$(WINCFG)_$(WINPLT) \
      && cp -r DLLs Lib data BallisticaCore$(WINPRJ).exe \
      VC_redist.*.exe *.dll ${DIST_DIR}/${WIN_PACKAGE_NAME}
	@cd ${DIST_DIR} && zip -rq ${WIN_PACKAGE_NAME}.zip \
      ${WIN_PACKAGE_NAME} && rm -rf ${WIN_PACKAGE_NAME}
	@echo SUCCESS! - created ${WIN_PACKAGE_NAME}.zip

# Assemble a package containing server components.
_windows-server-package: windows-rebuild
	@mkdir -p ${DIST_DIR} && cd ${DIST_DIR} && \
      rm -rf ${WIN_SERVER_PACKAGE_NAME}.zip ${WIN_SERVER_PACKAGE_NAME} \
      && mkdir ${WIN_SERVER_PACKAGE_NAME}
	@cd ${ROOT_DIR}/ballisticacore-windows/Build/$(WINCFG)_$(WINPLT) \
      && mv BallisticaCore$(WINPRJ).exe bs_headless.exe \
      && cp -r DLLs Lib data bs_headless.exe \
      python.exe VC_redist.*.exe python37.dll \
      ${DIST_DIR}/${WIN_SERVER_PACKAGE_NAME}/
	@cd ${DIST_DIR}/${WIN_SERVER_PACKAGE_NAME} \
      && cp ${ROOT_DIR}/assets/src/server/server.py \
      ./ballisticacore_server.py \
      && cp ${ROOT_DIR}/assets/src/server/server.bat \
      ./launch_ballisticacore_server.bat \
      && cp ${ROOT_DIR}/assets/src/server/README.txt ./README.txt \
      && cp ${ROOT_DIR}/CHANGELOG.md ./CHANGELOG.txt \
      && cp ${ROOT_DIR}/assets/src/server/config.py ./config.py
	@cd ${DIST_DIR}/${WIN_SERVER_PACKAGE_NAME} && unix2dos CHANGELOG.txt \
      README.txt config.py
	@cd ${DIST_DIR} && zip -rq ${WIN_SERVER_PACKAGE_NAME}.zip \
      ${WIN_SERVER_PACKAGE_NAME} && rm -rf ${WIN_SERVER_PACKAGE_NAME}
	@echo SUCCESS! - created ${WIN_SERVER_PACKAGE_NAME}.zip

# Assemble a package for uploading to the oculus store.
_windows-oculus-package: windows-rebuild
	@mkdir -p ${DIST_DIR} && cd ${DIST_DIR} && \
      rm -rf ${WIN_OCULUS_PACKAGE_NAME}.zip ${WIN_OCULUS_PACKAGE_NAME} \
      && mkdir ${WIN_OCULUS_PACKAGE_NAME}
	@cd ${ROOT_DIR}/ballisticacore-windows/Build/$(WINCFG)_$(WINPLT)\
      && cp -r DLLs Lib data BallisticaCore$(WINPRJ).exe *.dll \
      ${DIST_DIR}/${WIN_OCULUS_PACKAGE_NAME}
	@cd ${DIST_DIR} && zip -rq ${WIN_OCULUS_PACKAGE_NAME}.zip \
      ${WIN_OCULUS_PACKAGE_NAME} && rm -rf ${WIN_OCULUS_PACKAGE_NAME}
	@echo SUCCESS! - created ${WIN_OCULUS_PACKAGE_NAME}.zip

ANDROID_ADB = ${shell tools/android_sdk_utils get-adb-path}
ANDROID_FILTERED_LOGCAT = ${ANDROID_ADB} logcat -v color SDL:V \
  BallisticaCore:V VrLib:V VrApi:V VrApp:V TimeWarp:V EyeBuf:V GlUtils:V \
  DirectRender:V HmdInfo:V IabHelper:V CrashAnrDetector:V DEBUG:V *:S
AN_STRT = am start -a android.intent.action.MAIN -n
AN_BLD_OUT_DIR = ballisticacore-android/BallisticaCore/build/outputs
AN_BLDTP = $(ANDROID_BUILDTYPE)
AN_BLDTP_C = $(shell $(ROOT_DIR)/tools/snippets capitalize $(ANDROID_BUILDTYPE))
AN_PLAT = $(ANDROID_PLATFORM)
AN_PLAT_C = $(shell $(ROOT_DIR)/tools/snippets capitalize $(ANDROID_PLATFORM))
AN_MODE = $(ANDROID_MODE)
AN_MODE_C = $(shell $(ROOT_DIR)/tools/snippets capitalize $(ANDROID_MODE))
AN_ASSEMBLE_CMD = ./gradlew assemble$(AN_PLAT_C)$(AN_MODE_C)$(AN_BLDTP_C)
AN_PLATFORM_DIR = ballisticacore-android/BallisticaCore/src/${ANDROID_PLATFORM}
# (public facing name; doesn't reflect build settings)
ANDROID_PACKAGE_NAME = BallisticaCore_Android_Generic_$(VERSION)

AN_APK_DIR = ${AN_BLD_OUT_DIR}/apk/$(AN_PLAT)$(AN_MODE_C)/$(AN_BLDTP)
AN_APK = $(AN_APK_DIR)/BallisticaCore-$(AN_PLAT)-$(AN_MODE)-$(AN_BLDTP).apk
AN_BNDL_DIR = $(AN_BLD_OUT_DIR)/bundle/$(AN_PLAT)$(AN_MODE_C)$(AN_BLDTP_C)
AN_BNDL = $(AN_BNDL_DIR)/BallisticaCore-$(AN_PLAT)-$(AN_MODE)-$(AN_BLDTP).aab

BA_ARCHIVE_ROOT ?= $(HOME)/build_archives
AN_ARCHIVE_ROOT = $(BA_ARCHIVE_ROOT)/ballisticacore/android
AN_ARCHIVE_DIR = $(AN_ARCHIVE_ROOT)/$(AN_PLAT)/$(VERSION)_$(BUILD_NUMBER)

ARCH ?= $(shell uname -m)
ifeq ($(ARCH),x86_64)
	ARCH_NAME?=64bit
	ARCH_NAME_SHORT?=linux64
	ARCH_NAME_SERVER_SHORT?=linux64_server
else
	ARCH_NAME?=32bit
	ARCH_NAME_SHORT?=linux32
	ARCH_NAME_SERVER_SHORT?=linux32_server
endif

# For our ssh/scp/rsh stuff we want to rely on public key auth
# and just fail if anything is off instead of prompting.
SSH_BATCH_ARGS = -oBatchMode=yes -oStrictHostKeyChecking=yes

# Target run from within linux vm to build and run.
_linux: _linux-build
	cd build/${ARCH_NAME_SHORT}/ballisticacore && \
      DISPLAY=:0 ./ballisticacore

# Build only.
_linux-build:
	@mkdir -p build/${ARCH_NAME_SHORT} && cd build/${ARCH_NAME_SHORT} \
      && test -f Makefile || cmake -DCMAKE_BUILD_TYPE=Debug \
      ${PWD}/ballisticacore-cmake
	cd build/${ARCH_NAME_SHORT} && make -j${JOBS}

# Target used from within linux vm to build a package.
# NOTE: building in place from linux over hgfs seems slightly flaky
# (for instance, have seen tar complain source changing under it
# when assembling a package).. so when possible we build on the local
# disk and then copy the results back over hgfs.
# We just need to make sure we only launch one build at a time per VM,
# but that should already be the case.
LINUX_BUILD_BASE = ~/ballisticacore_builds
LINUX_PACKAGE_BASE_NAME = BallisticaCore_Linux
LINUX_PACKAGE_NAME = ${LINUX_PACKAGE_BASE_NAME}_${ARCH_NAME}_${VERSION}
LINUX_BUILD_DIR = ${LINUX_BUILD_BASE}/${LINUX_PACKAGE_NAME}_build
LINUX_PACKAGE_DIR = build/${LINUX_PACKAGE_NAME}

# Build for linux package (to be run under vm).
_linux-package-build:
	@rm -rf ${DIST_DIR}/${LINUX_PACKAGE_NAME}.tar.gz ${LINUX_BUILD_DIR} \
      ${LINUX_PACKAGE_DIR} ${LINUX_PACKAGE_DIR}.tar.gz
	@mkdir -p ${LINUX_BUILD_DIR} ${LINUX_PACKAGE_DIR} ${DIST_DIR}
	@cd ${LINUX_BUILD_DIR} && cmake -DCMAKE_BUILD_TYPE=Release -DTEST_BUILD=true \
      ${ROOT_DIR}/ballisticacore-cmake && make -j${JOBS}
	@cd ${LINUX_PACKAGE_DIR} && \
      cp ${LINUX_BUILD_DIR}/ballisticacore .
	@rm -rf ${LINUX_BUILD_DIR}

# Complete linux package (to be run on mac).
_linux-package-assemble:
	@cd ${LINUX_PACKAGE_DIR} && ${STAGE_ASSETS} -cmake .
	@cd build && tar -zcf ${LINUX_PACKAGE_NAME}.tar.gz ${LINUX_PACKAGE_NAME}
	@rm -rf ${LINUX_PACKAGE_DIR}
	@echo SUCCESS! - created ${LINUX_PACKAGE_NAME}.tar.gz

# Build only.
_linux-server-build:
	@mkdir -p build/${ARCH_NAME_SERVER_SHORT} \
      && cd build/${ARCH_NAME_SERVER_SHORT} \
      && test -f Makefile || cmake -DCMAKE_BUILD_TYPE=Debug -DHEADLESS=true \
      ${PWD}/ballisticacore-cmake
	cd build/${ARCH_NAME_SERVER_SHORT} && make -j${JOBS}

# Used from within linux vm to build a server package.
LINUX_SERVER_PACKAGE_BASE_NAME = BallisticaCore_Server_Linux
LINUX_SERVER_PACKAGE_NAME = \
  ${LINUX_SERVER_PACKAGE_BASE_NAME}_${ARCH_NAME}_${VERSION}
LINUX_SERVER_BUILD_DIR = ${LINUX_BUILD_BASE}/${LINUX_SERVER_PACKAGE_NAME}_build
LINUX_SERVER_PACKAGE_DIR = build/${LINUX_SERVER_PACKAGE_NAME}

_linux-server-package-build:
	@rm -rf ${DIST_DIR}/${LINUX_SERVER_PACKAGE_NAME}.tar.gz \
      ${LINUX_SERVER_BUILD_DIR} ${LINUX_SERVER_PACKAGE_DIR} \
      ${LINUX_SERVER_PACKAGE_DIR}.tar.gz
	@mkdir -p ${LINUX_SERVER_BUILD_DIR} ${LINUX_SERVER_PACKAGE_DIR} ${DIST_DIR}
	@cd ${LINUX_SERVER_BUILD_DIR} && cmake -DCMAKE_BUILD_TYPE=Release \
      -DHEADLESS=true ${ROOT_DIR}/ballisticacore-cmake && make -j${JOBS}
	@cd ${LINUX_SERVER_PACKAGE_DIR} \
      && cp ${LINUX_SERVER_BUILD_DIR}/ballisticacore \
      ./bs_headless
	@rm -rf ${LINUX_SERVER_BUILD_DIR}

_linux-server-package-assemble:
	@cd ${LINUX_SERVER_PACKAGE_DIR} \
      && cp ${ROOT_DIR}/assets/src/server/server.py \
        ./ballisticacore_server \
      && cp ${ROOT_DIR}/assets/src/server/README.txt ./README.txt \
      && cp ${ROOT_DIR}/assets/src/server/config.py ./config.py \
      && cp ${ROOT_DIR}/CHANGELOG.md ./CHANGELOG.txt \
      && ${STAGE_ASSETS} -cmake-server .
	@cd ${LINUX_SERVER_PACKAGE_DIR}/.. && tar -zcf \
      ${LINUX_SERVER_PACKAGE_NAME}.tar.gz ${LINUX_SERVER_PACKAGE_NAME}
	@rm -rf ${LINUX_SERVER_PACKAGE_DIR}
	@echo SUCCESS! - created ${LINUX_SERVER_PACKAGE_NAME}.tar.gz

# This target attempts to verify that we have a valid android sdk setup going
# and creates our local.properties file if need be so gradle builds will go
# through.
_android-sdk:
	@tools/android_sdk_utils check

# FIXME: needs updating to find unstripped libs for new cmake setup
_android-archive: android-build
	make android-fullclean
	tools/spinoff update
	rm -rf $(AN_ARCHIVE_DIR)
	mkdir -p $(AN_ARCHIVE_DIR)
	mkdir -p $(AN_ARCHIVE_DIR)/unstripped_libs
	make android-build
	cp $(AN_APK) $(AN_ARCHIVE_DIR)
	git log -n 5 > $(AN_ARCHIVE_DIR)/gitlog.txt
	test -e submodules/ballistica && cd submodules/ballistica \
    && git log -n 5 > $(AN_ARCHIVE_DIR)/gitlogcore.txt || true
	cp ballisticacore-android/BallisticaCore/build/outputs/\
mapping/$(AN_PLAT)$(AN_MODE_C)/$(AN_BLDTP)/mapping.txt $(AN_ARCHIVE_DIR)
	open $(AN_ARCHIVE_DIR)

# FIXME: needs updating to find unstripped libs for new cmake setup
_android-bundle-archive:
	make android-fullclean
	tools/spinoff update
	rm -rf $(AN_ARCHIVE_DIR)
	mkdir -p $(AN_ARCHIVE_DIR)
	mkdir -p $(AN_ARCHIVE_DIR)/unstripped_libs
	make android-staging
	cd ballisticacore-android\
 && ./gradlew bundle$(AN_PLAT_C)$(AN_MODE_C)$(AN_BLDTP_C)
	cp $(AN_BNDL) $(AN_ARCHIVE_DIR)
	git log -n 5 > $(AN_ARCHIVE_DIR)/gitlog.txt
	test -e submodules/ballistica && cd submodules/ballistica \
    && git log -n 5 > $(AN_ARCHIVE_DIR)/gitlogcore.txt || true
	cp ballisticacore-android/BallisticaCore/build/outputs/\
mapping/$(AN_PLAT)$(AN_MODE_C)/$(AN_BLDTP)/mapping.txt $(AN_ARCHIVE_DIR)
	open $(AN_ARCHIVE_DIR)

_android-package:
	make android-fullclean
	tools/spinoff update
	@rm -f ${DIST_DIR}/${ANDROID_PACKAGE_NAME}.apk
	make android-build
	@mkdir -p ${DIST_DIR}
	@cp ballisticacore-android/BallisticaCore/build/outputs/\
apk/$(AN_PLAT)$(AN_MODE_C)/$(AN_BLDTP)/\
BallisticaCore-$(AN_PLAT)-$(AN_MODE)-$(AN_BLDTP).apk \
${DIST_DIR}/${ANDROID_PACKAGE_NAME}.apk
	@echo SUCCESS! - created ${ANDROID_PACKAGE_NAME}.apk

# Efro specific: runs spinoff upgrade on a few local projects.
# (ideally should pull this out of here or abstract it ala syncall).
spinoff-upgrade-push-all:
	@echo UPGRADING SPINOFF TEMPLATE
	@cd ~/Documents/spinoff-template && make spinoff-upgrade-push
	@echo UPGRADING BOMBSQUAD
	@cd ~/Documents/bombsquad && make spinoff-upgrade-push

# Generate and push our changelog to the staging server.
pushchangelog:
	@echo GENERATING CHANGELOG HTML...
	@mkdir -p ${DIST_DIR}
	@./tools/gen_changelog
	@echo UPLOADING CHANGELOG...
	@scp ${SSH_BATCH_ARGS} ${DIST_DIR}/changelog.html \
      ${BLOG_SERVER}:blog_code/${DOCPREFIX}changelog.html\

# Generate docs.
docs:
	@echo GENERATING DOCS HTML...
	@mkdir -p ${DIST_DIR}
	@./tools/gendocs.py

# Generate and push docs to the staging server.
pushdocs: docs
	@echo UPLOADING DOCS...
	@scp ${SSH_BATCH_ARGS} ${DIST_DIR}/docs.html \
      ${BLOG_SERVER}:blog_code/${DOCPREFIX}docs.html

# Some tool configs that need filtering (mainly injecting projroot path).
TOOL_CFG_INST = tools/snippets tool_config_install

# Anything that affects tool-config generation.
TOOL_CFG_SRC = tools/efrotools/snippets.py config/config.json

.clang-format: config/toolconfigsrc/clang-format ${TOOL_CFG_SRC}
	${TOOL_CFG_INST} $< $@

# When using CLion, our cmake dir is root. Expose .clang-format there too.
ballisticacore-cmake/.clang-format: .clang-format
	cd ballisticacore-cmake && ln -sf ../.clang-format .

.style.yapf: config/toolconfigsrc/style.yapf ${TOOL_CFG_SRC}
	${TOOL_CFG_INST} $< $@

.pylintrc: config/toolconfigsrc/pylintrc ${TOOL_CFG_SRC}
	${TOOL_CFG_INST} $< $@

.dir-locals.el: config/toolconfigsrc/dir-locals.el ${TOOL_CFG_SRC}
	${TOOL_CFG_INST} $< $@

.mypy.ini: config/toolconfigsrc/mypy.ini ${TOOL_CFG_SRC}
	${TOOL_CFG_INST} $< $@

.pycheckers: config/toolconfigsrc/pycheckers ${TOOL_CFG_SRC}
	${TOOL_CFG_INST} $< $@

# Irony in emacs requires us to use cmake to generate a full
# list of compile commands for all files; lets keep it up to date
# whenever CMakeLists changes.
.irony/compile_commands.json: ballisticacore-cmake/CMakeLists.txt
	@echo Generating Irony compile-commands-list...
	@mkdir -p .irony
	@cd .irony \
      && cmake -DCMAKE_EXPORT_COMPILE_COMMANDS=ON -DCMAKE_BUILD_TYPE=Debug \
      ../ballisticacore-cmake
	@mv .irony/compile_commands.json . && rm -rf .irony && mkdir .irony \
      && mkdir .irony/ballisticacore .irony/make_bob .irony/ode \
      && mv compile_commands.json .irony
	@echo Created $@

# Clear and build our assets to update cache timestamps.
# files, and then prune non-recent cache files which should pretty much limit
# it to the current set which we then package and upload as a 'starter-pack'
# for new builds to use (takes full asset builds from an hour down to a
# minute or so).
asset_cache_refresh:
	@echo REFRESHING ASSET CACHE: ${ASSET_CACHE_NAME}
	@echo REBUILDING ASSETS...
	@make assets-clean && make assets
	@test -d "${ASSET_CACHE_DIR}" && echo ARCHIVING ASSET CACHE FROM \
      ${ASSET_CACHE_DIR}...
	@${ROOT_DIR}/tools/convert_util --prune-to-recent-assets
	@mkdir -p ${DIST_DIR}
	@cd ${ASSET_CACHE_DIR} && tar -zcf \
      ${DIST_DIR}/${ASSET_CACHE_NAME}.tar.gz *
	@echo UPLOADING ASSET CACHE...
	@scp ${SSH_BATCH_ARGS} ${DIST_DIR}/${ASSET_CACHE_NAME}.tar.gz \
      ${STAGING_SERVER}:files.ballistica.net/misc/\
${ASSET_CACHE_NAME}.tar.gz.new
	@ssh ${SSH_BATCH_ARGS} ${STAGING_SERVER} mv \
      files.ballistica.net/misc/${ASSET_CACHE_NAME}.tar.gz.new \
      files.ballistica.net/misc/${ASSET_CACHE_NAME}.tar.gz
	@echo SUCCESSFULLY UPDATED ASSET CACHE: ${ASSET_CACHE_NAME}

STAGING_SERVER ?= ubuntu@ballistica.net
STAGING_SERVER_BUILDS_DIR = files.ballistica.net/ballisticacore/builds
BLOG_SERVER ?= ecfroeml@froemling.net

# Ensure we can sign in to staging server.
# Handy to do before starting lengthy operations instead of failing
# after wasting a bunch of time.
verify_staging_server_auth:
	@echo -n Verifying staging server auth...
	@ssh ${SSH_BATCH_ARGS} ${STAGING_SERVER} true
	@echo ok.

ARCHIVE_OLD_PUBLIC_BUILDS = \
  ${ROOT_DIR}/tools/snippets archive_old_builds ${STAGING_SERVER} \
  ${STAGING_SERVER_BUILDS_DIR} ${SSH_BATCH_ARGS}

ALL_TEST_PACKAGE_FILES = \
  ${DIST_DIR}/${LINUX_PACKAGE_BASE_NAME}_64bit_${VERSION}.tar.gz \
  ${DIST_DIR}/${WIN_PACKAGE_NAME}.zip \
  ${DIST_DIR}/${MAC_PACKAGE_NAME}.zip \
  ${DIST_DIR}/${ANDROID_PACKAGE_NAME}.apk

# Note: currently not including rpi until we figure out the py3.7 situation.
ALL_SERVER_PACKAGE_FILES = \
  ${DIST_DIR}/${LINUX_SERVER_PACKAGE_BASE_NAME}_64bit_${VERSION}.tar.gz \
  ${DIST_DIR}/${WIN_SERVER_PACKAGE_NAME}.zip \
  ${DIST_DIR}/${MAC_SERVER_PACKAGE_NAME}.zip \
  ${DIST_DIR}/${RPI_SERVER_PACKAGE_NAME}.tar.gz

# Tell make which of these targets don't represent files.
.PHONY: _windows-package _windows-server-package _windows-oculus-package \
  _linux _linux-build _linux-package-build _linux-package-assemble \
  _android-sdk _android-archive _android-bundle-archive _android-package \
  _linux-server-build _linux-server-package-build \
  _linux-server-package-assemble spinoff-upgrade-push-all pushchangelog \
  docs pushdocs asset_cache_refresh verify_staging_server_auth
