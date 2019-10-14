# Copyright (c) 2011-2019 Eric Froemling
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# ------------------------------------------------------------------------------

# This Makefile encompasses most high level functionality you should need when
# working with Ballistica. These build rules are also handy as reference or a
# starting point if you need specific funtionality beyond that exposed here.
# Targets in this top level Makefile do not expect -jX to be passed to them
# and generally handle spawning an appropriate number of child jobs themselves.

# Prefix used for output of docs/changelogs/etc targets for use in webpages.
DOCPREFIX = "ballisticacore_"

# Print help by default
all: help

# Tell make which of these targets don't represent files.
.PHONY: all


################################################################################
#                                                                              #
#                                   General                                    #
#                                                                              #
################################################################################

# Prerequisites that should be in place before running most any other build;
# things like tool config files, etc.
PREREQS = .dir-locals.el .mypy.ini .pycheckers \
  .pylintrc .style.yapf .clang-format \
  .projectile .editorconfig

# List the targets in this Makefile and basic descriptions for them.
list:
	@tools/snippets makefile_target_list Makefile

# Same as 'list'
help: list

prereqs: ${PREREQS}

prereqs-clean:
	@rm -rf ${PREREQS} .irony

# Build all assets for all platforms.
assets:
	@cd assets && make -j${CPUS}

# Build only assets required for desktop builds (mac, pc, linux).
assets-desktop:
	@cd assets && make -j${CPUS} desktop

# Build only assets required for ios.
assets-ios:
	@cd assets && make -j${CPUS} ios

# Build only assets required for android.
assets-android:
	@cd assets && make -j${CPUS} android

# Clean all assets.
assets-clean:
	@cd assets && make clean

# Build resources.
resources: resources/Makefile
	@cd resources && make -j${CPUS} resources

# Clean resources.
resources-clean:
	@cd resources && make clean

# Build our generated code.
code:
	@cd src/generated_src && make -j${CPUS} generated_code

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

# Tell make which of these targets don't represent files.
.PHONY: list prereqs prereqs-clean assets assets-desktop assets-ios\
  assets-android assets-clean resources resources-clean code code-clean\
  clean cleanlist


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

# Things to ignore when doing root level cleans.
ROOT_CLEAN_IGNORES = --exclude=assets/src_master \
  --exclude=config/localconfig.json \
  --exclude=.spinoffdata

CHECK_CLEAN_SAFETY = ${PROJ_DIR}/tools/snippets check_clean_safety

# Some tool configs that need filtering (mainly injecting projroot path).
TOOL_CFG_INST = tools/snippets tool_config_install

# Anything that affects tool-config generation.
TOOL_CFG_SRC = tools/efrotools/snippets.py config/config.json

.clang-format: config/toolconfigsrc/clang-format ${TOOL_CFG_SRC}
	${TOOL_CFG_INST} $< $@

.style.yapf: config/toolconfigsrc/style.yapf ${TOOL_CFG_SRC}
	${TOOL_CFG_INST} $< $@

.pylintrc: config/toolconfigsrc/pylintrc ${TOOL_CFG_SRC}
	${TOOL_CFG_INST} $< $@

.projectile: config/toolconfigsrc/projectile ${TOOL_CFG_SRC}
	${TOOL_CFG_INST} $< $@

.editorconfig: config/toolconfigsrc/editorconfig ${TOOL_CFG_SRC}
	${TOOL_CFG_INST} $< $@

.dir-locals.el: config/toolconfigsrc/dir-locals.el ${TOOL_CFG_SRC}
	${TOOL_CFG_INST} $< $@

.mypy.ini: config/toolconfigsrc/mypy.ini ${TOOL_CFG_SRC}
	${TOOL_CFG_INST} $< $@

.pycheckers: config/toolconfigsrc/pycheckers ${TOOL_CFG_SRC}
	${TOOL_CFG_INST} $< $@

# Tell make which of these targets don't represent files.
.PHONY:
