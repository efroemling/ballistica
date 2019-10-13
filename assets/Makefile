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

############################ ASSET GENERATION TARGETS ##########################

# For high level targets we run a build from master-src (if present) into src
# followed by a build of src into build. Originally I tried to handle all
# dependencies in one go, but I ran into weird corner cases where removing
# some file in src would kick off a maya process to rebuild it which would also
# as a side effect rebuild other files in src, but those other files' associated
# build targets would not get updated until the next make invocation. Possibly
# this was harmless but it felt janky; having a multi-tiered approach ensures
# that maya or whatever else in master-src can muck with whatever it wants in
# src and it will all get properly propagated to build in the next phase.

# If VERBOSE env var is 1, show command output.. (handy to diagnose failures).
VERBOSE ?= 0
ifeq (${VERBOSE},1)
	VERBOSE_REDIRECT =
else
	VERBOSE_REDIRECT = >/dev/null 2>&1
endif



# Note; make sure these are full paths; some code relies on that.
TOOLS_DIR = ${abspath ${CURDIR}/../tools}
PROJ_DIR = ${abspath ${CURDIR}/..}

WIN_EXTRAS_DIR = ${abspath ${CURDIR}/../ballisticacore-windows/Extras}
ASSET_SRC_DIR = ${CURDIR}/src
ASSET_SRC_MASTER_DIR := $(shell $(TOOLS_DIR)/snippets get_master_asset_src_dir)
ASSET_BUILD_DIR = build
CONVERT_UTIL = ${TOOLS_DIR}/convert_util
MAKE_BOB = ${TOOLS_DIR}/make_bob/mac/make_bob
MAYA_BIN = /Applications/Autodesk/maya2019/Maya.app/Contents/bin/maya

# High level targets: generally these are what you should use here.

# Build everything for all platforms.
all:
	@test -d ${ASSET_SRC_MASTER_DIR} && make asset_sources || true
	@${TOOLS_DIR}/convert_util --init-asset-cache
	@make assets
	@${TOOLS_DIR}/snippets clean_orphaned_assets

# Build everything needed for desktop platforms (mac, windows, linux).
desktop:
	@test -d ${ASSET_SRC_MASTER_DIR} && make asset_sources || true
	@${TOOLS_DIR}/convert_util --init-asset-cache
	@make assets-desktop
	@${TOOLS_DIR}/snippets clean_orphaned_assets

# Build everything needed for ios.
ios:
	@test -d ${ASSET_SRC_MASTER_DIR} && make asset_sources || true
	@${TOOLS_DIR}/convert_util --init-asset-cache
	@make assets-ios
	@${TOOLS_DIR}/snippets clean_orphaned_assets

# Build everything needed for android.
android:
	@test -d ${ASSET_SRC_MASTER_DIR} && make asset_sources || true
	@${TOOLS_DIR}/convert_util --init-asset-cache
	@make assets-android
	@${TOOLS_DIR}/snippets clean_orphaned_assets

MAKE_AUDIO = 1
MAKE_TEXTURES = 1
MAKE_SCRIPTS = 1
MAKE_FONTS = 1
MAKE_DATA = 1

ASSET_TARGETS_COMMON =
ASSET_TARGETS_DESKTOP =
ASSET_TARGETS_IOS =
ASSET_TARGETS_ANDROID =


# Audio.
ifeq ($(MAKE_AUDIO),1)
ASSET_TARGETS_COMMON += $(AUDIO_TARGETS)
endif


# FontData.
ifeq ($(MAKE_FONTS),1)
ASSET_TARGETS_COMMON += $(FONT_TARGETS)
endif

# Data.
ifeq ($(MAKE_DATA),1)
ASSET_TARGETS_COMMON += $(DATA_TARGETS)
endif

# Textures.
ifeq ($(MAKE_TEXTURES),1)

TEX2D_SRC_SOURCES = $(wildcard $(ASSET_SRC_MASTER_DIR)/textures/*.tex2d.psd)
TEX2D_SRC_TARGETS = $(subst $(ASSET_SRC_MASTER_DIR),$(ASSET_SRC_DIR)/data,\
      $(patsubst %.tex2d.psd,%.tex2d.png,$(TEX2D_SRC_SOURCES)))

ASSET_TARGETS_DESKTOP += $(TEXTURE_TARGETS_DESKTOP)
ASSET_TARGETS_IOS += $(TEXTURE_TARGETS_IOS)
ASSET_TARGETS_ANDROID += $(TEXTURE_TARGETS_ANDROID)
ASSET_TARGETS_COMMON += $(TEXTURE_TARGETS_PREVIEW)

CUBE_SRC_SOURCES = $(wildcard $(ASSET_SRC_MASTER_DIR)/textures/*.texcube.psd)
CUBE_SRC_TARGETS = $(subst $(ASSET_SRC_MASTER_DIR),$(ASSET_SRC_DIR)/data,\
      $(patsubst %.texcube.psd,%_+x.tex2d.png,$(CUBE_SRC_SOURCES))) \
      $(subst $(ASSET_SRC_MASTER_DIR),$(ASSET_SRC_DIR)/data,\
      $(patsubst %.texcube.psd,%_-x.tex2d.png,$(CUBE_SRC_SOURCES))) \
      $(subst $(ASSET_SRC_MASTER_DIR),$(ASSET_SRC_DIR)/data,\
      $(patsubst %.texcube.psd,%_+y.tex2d.png,$(CUBE_SRC_SOURCES))) \
      $(subst $(ASSET_SRC_MASTER_DIR),$(ASSET_SRC_DIR)/data,\
      $(patsubst %.texcube.psd,%_-y.tex2d.png,$(CUBE_SRC_SOURCES))) \
      $(subst $(ASSET_SRC_MASTER_DIR),$(ASSET_SRC_DIR)/data,\
      $(patsubst %.texcube.psd,%_+z.tex2d.png,$(CUBE_SRC_SOURCES))) \
      $(subst $(ASSET_SRC_MASTER_DIR),$(ASSET_SRC_DIR)/data,\
      $(patsubst %.texcube.psd,%_-z.tex2d.png,$(CUBE_SRC_SOURCES)))


endif # Textures


# Scripts
ifeq ($(MAKE_SCRIPTS),1)
ASSET_TARGETS_COMMON += $(SCRIPT_TARGETS)
endif

#AUTOGENERATED_BEGIN (this section is managed by the "update_project" tool)

SCRIPT_TARGETS_PY_1 = \
  ${ASSET_BUILD_DIR}/server/server.py \
  ${ASSET_BUILD_DIR}/server/config.py \
  ${ASSET_BUILD_DIR}/data/scripts/bafoundation/executils.py \
  ${ASSET_BUILD_DIR}/data/scripts/bafoundation/dataclassutils.py \
  ${ASSET_BUILD_DIR}/data/scripts/bafoundation/util.py \
  ${ASSET_BUILD_DIR}/data/scripts/bafoundation/__init__.py \
  ${ASSET_BUILD_DIR}/data/scripts/bafoundation/jsonutils.py \
  ${ASSET_BUILD_DIR}/data/scripts/bafoundation/err.py \
  ${ASSET_BUILD_DIR}/data/scripts/bafoundation/entity/_base.py \
  ${ASSET_BUILD_DIR}/data/scripts/bafoundation/entity/_support.py \
  ${ASSET_BUILD_DIR}/data/scripts/bafoundation/entity/util.py \
  ${ASSET_BUILD_DIR}/data/scripts/bafoundation/entity/_entity.py \
  ${ASSET_BUILD_DIR}/data/scripts/bafoundation/entity/_field.py \
  ${ASSET_BUILD_DIR}/data/scripts/bafoundation/entity/__init__.py \
  ${ASSET_BUILD_DIR}/data/scripts/bafoundation/entity/_value.py \
  ${ASSET_BUILD_DIR}/data/scripts/ba/_gameactivity.py \
  ${ASSET_BUILD_DIR}/data/scripts/ba/_apputils.py \
  ${ASSET_BUILD_DIR}/data/scripts/ba/_coopsession.py \
  ${ASSET_BUILD_DIR}/data/scripts/ba/_appdelegate.py \
  ${ASSET_BUILD_DIR}/data/scripts/ba/internal.py \
  ${ASSET_BUILD_DIR}/data/scripts/ba/_coopgame.py \
  ${ASSET_BUILD_DIR}/data/scripts/ba/_meta.py \
  ${ASSET_BUILD_DIR}/data/scripts/ba/_math.py \
  ${ASSET_BUILD_DIR}/data/scripts/ba/_appconfig.py \
  ${ASSET_BUILD_DIR}/data/scripts/ba/_gameresults.py \
  ${ASSET_BUILD_DIR}/data/scripts/ba/_profile.py \
  ${ASSET_BUILD_DIR}/data/scripts/ba/_error.py \
  ${ASSET_BUILD_DIR}/data/scripts/ba/_achievement.py \
  ${ASSET_BUILD_DIR}/data/scripts/ba/_teambasesession.py \
  ${ASSET_BUILD_DIR}/data/scripts/ba/_gameutils.py \
  ${ASSET_BUILD_DIR}/data/scripts/ba/_activity.py \
  ${ASSET_BUILD_DIR}/data/scripts/ba/deprecated.py \
  ${ASSET_BUILD_DIR}/data/scripts/ba/_modutils.py \
  ${ASSET_BUILD_DIR}/data/scripts/ba/_tips.py \
  ${ASSET_BUILD_DIR}/data/scripts/ba/_store.py \
  ${ASSET_BUILD_DIR}/data/scripts/ba/_activitytypes.py \
  ${ASSET_BUILD_DIR}/data/scripts/ba/__init__.py \
  ${ASSET_BUILD_DIR}/data/scripts/ba/_session.py \
  ${ASSET_BUILD_DIR}/data/scripts/ba/_hooks.py \
  ${ASSET_BUILD_DIR}/data/scripts/ba/_enums.py \
  ${ASSET_BUILD_DIR}/data/scripts/ba/_netutils.py \
  ${ASSET_BUILD_DIR}/data/scripts/ba/_app.py \
  ${ASSET_BUILD_DIR}/data/scripts/ba/_benchmark.py \
  ${ASSET_BUILD_DIR}/data/scripts/ba/_tournament.py \
  ${ASSET_BUILD_DIR}/data/scripts/ba/_messages.py \
  ${ASSET_BUILD_DIR}/data/scripts/ba/_teamssession.py \
  ${ASSET_BUILD_DIR}/data/scripts/ba/_freeforallsession.py \
  ${ASSET_BUILD_DIR}/data/scripts/ba/_playlist.py \
  ${ASSET_BUILD_DIR}/data/scripts/ba/_team.py \
  ${ASSET_BUILD_DIR}/data/scripts/ba/_actor.py \
  ${ASSET_BUILD_DIR}/data/scripts/ba/_powerup.py \
  ${ASSET_BUILD_DIR}/data/scripts/ba/_campaign.py \
  ${ASSET_BUILD_DIR}/data/scripts/ba/_lobby.py \
  ${ASSET_BUILD_DIR}/data/scripts/ba/_stats.py \
  ${ASSET_BUILD_DIR}/data/scripts/ba/_input.py \
  ${ASSET_BUILD_DIR}/data/scripts/ba/_dep.py \
  ${ASSET_BUILD_DIR}/data/scripts/ba/_level.py \
  ${ASSET_BUILD_DIR}/data/scripts/ba/_general.py \
  ${ASSET_BUILD_DIR}/data/scripts/ba/_server.py \
  ${ASSET_BUILD_DIR}/data/scripts/ba/_account.py \
  ${ASSET_BUILD_DIR}/data/scripts/ba/_music.py \
  ${ASSET_BUILD_DIR}/data/scripts/ba/_lang.py \
  ${ASSET_BUILD_DIR}/data/scripts/ba/_maps.py \
  ${ASSET_BUILD_DIR}/data/scripts/ba/_teamgame.py \
  ${ASSET_BUILD_DIR}/data/scripts/ba/ui/__init__.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/mainmenu.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/maps.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/appdelegate.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/tutorial.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/__init__.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/stdmap.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/playoptions.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/mainmenu.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/getremote.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/tournamententry.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/telnet.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/appinvite.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/gather.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/config.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/colorpicker.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/tabs.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/promocode.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/fileselector.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/feedback.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/teamnamescolors.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/configerror.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/serverdialog.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/getcurrency.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__init__.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/specialoffer.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/helpui.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/purchase.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/continues.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/play.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/popup.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/onscreenkeyboard.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/kiosk.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/qrcode.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/trophies.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/partyqueue.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/url.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/debug.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/iconpicker.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/watch.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/achievements.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/radiogroup.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/creditslist.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/tournamentscores.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/characterpicker.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/report.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/resourcetypeinfo.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/confirm.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/party.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/settings/graphics.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/settings/advanced.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/settings/controls.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/settings/gamepadadvanced.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/settings/gamepadselect.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/settings/touchscreen.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/settings/__init__.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/settings/xbox360controller.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/settings/audio.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/settings/gamepad.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/settings/nettesting.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/settings/remoteapp.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/settings/testing.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/settings/wiimote.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/settings/vrtesting.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/settings/allsettings.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/settings/ps3controller.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/settings/keyboard.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/playlist/customizebrowser.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/playlist/__init__.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/playlist/edit.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/playlist/browser.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/playlist/mapselect.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/playlist/share.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/playlist/editgame.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/playlist/editcontroller.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/playlist/addgame.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/soundtrack/entrytypeselect.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/soundtrack/itunes.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/soundtrack/__init__.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/soundtrack/edit.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/soundtrack/browser.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/league/__init__.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/league/rankbutton.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/league/rankwindow.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/coop/gamebutton.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/coop/__init__.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/coop/browser.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/coop/level.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/profile/__init__.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/profile/edit.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/profile/upgrade.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/profile/browser.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/account/link.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/account/viewer.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/account/__init__.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/account/unlink.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/account/settings.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/store/__init__.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/store/browser.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/store/button.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/store/item.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/activity/freeforallendscreen.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/activity/__init__.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/activity/coopscorescreen.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/activity/dualteamscorescreen.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/activity/coopjoinscreen.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/activity/multiteamendscreen.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/activity/teamsscorescreen.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/activity/multiteamjoinscreen.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/activity/drawscreen.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/game/capturetheflag.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/game/targetpractice.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/game/ninjafight.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/game/easteregghunt.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/game/race.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/game/meteorshower.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/game/thelaststand.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/game/__init__.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/game/football.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/game/kingofthehill.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/game/assault.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/game/keepaway.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/game/elimination.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/game/deathmatch.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/game/onslaught.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/game/hockey.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/game/chosenone.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/game/conquest.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/game/runaround.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/mapdata/bridgit.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/mapdata/big_g.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/mapdata/hockey_stadium.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/mapdata/courtyard.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/mapdata/tower_d.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/mapdata/__init__.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/mapdata/roundabout.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/mapdata/rampage.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/mapdata/crag_castle.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/mapdata/step_right_up.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/mapdata/football_stadium.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/mapdata/the_pad.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/mapdata/happy_thoughts.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/mapdata/monkey_face.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/mapdata/doom_shroom.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/mapdata/zig_zag.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/mapdata/lake_frigid.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/mapdata/tip_top.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/actor/spazfactory.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/actor/bomb.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/actor/spazbot.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/actor/flag.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/actor/scoreboard.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/actor/popuptext.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/actor/background.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/actor/__init__.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/actor/zoomtext.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/actor/spaz.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/actor/spazappearance.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/actor/controlsguide.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/actor/powerupbox.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/actor/text.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/actor/spawner.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/actor/respawnicon.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/actor/playerspaz.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/actor/tipstext.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/actor/onscreencountdown.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/actor/onscreentimer.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/actor/image.py \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/session/__init__.py

SCRIPT_TARGETS_PYC_1 = \
  ${ASSET_BUILD_DIR}/server/__pycache__/server.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/server/__pycache__/config.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bafoundation/__pycache__/executils.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bafoundation/__pycache__/dataclassutils.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bafoundation/__pycache__/util.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bafoundation/__pycache__/__init__.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bafoundation/__pycache__/jsonutils.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bafoundation/__pycache__/err.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bafoundation/entity/__pycache__/_base.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bafoundation/entity/__pycache__/_support.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bafoundation/entity/__pycache__/util.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bafoundation/entity/__pycache__/_entity.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bafoundation/entity/__pycache__/_field.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bafoundation/entity/__pycache__/__init__.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bafoundation/entity/__pycache__/_value.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_gameactivity.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_apputils.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_coopsession.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_appdelegate.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/internal.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_coopgame.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_meta.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_math.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_appconfig.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_gameresults.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_profile.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_error.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_achievement.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_teambasesession.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_gameutils.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_activity.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/deprecated.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_modutils.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_tips.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_store.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_activitytypes.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/__init__.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_session.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_hooks.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_enums.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_netutils.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_app.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_benchmark.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_tournament.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_messages.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_teamssession.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_freeforallsession.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_playlist.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_team.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_actor.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_powerup.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_campaign.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_lobby.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_stats.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_input.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_dep.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_level.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_general.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_server.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_account.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_music.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_lang.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_maps.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_teamgame.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/ba/ui/__pycache__/__init__.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/__pycache__/mainmenu.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/__pycache__/maps.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/__pycache__/appdelegate.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/__pycache__/tutorial.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/__pycache__/__init__.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/__pycache__/stdmap.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/playoptions.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/mainmenu.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/getremote.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/tournamententry.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/telnet.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/appinvite.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/gather.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/config.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/colorpicker.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/tabs.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/promocode.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/fileselector.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/feedback.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/teamnamescolors.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/configerror.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/serverdialog.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/getcurrency.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/__init__.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/specialoffer.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/helpui.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/purchase.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/continues.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/play.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/popup.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/onscreenkeyboard.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/kiosk.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/qrcode.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/trophies.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/partyqueue.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/url.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/debug.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/iconpicker.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/watch.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/achievements.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/radiogroup.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/creditslist.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/tournamentscores.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/characterpicker.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/report.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/resourcetypeinfo.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/confirm.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/party.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/settings/__pycache__/graphics.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/settings/__pycache__/advanced.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/settings/__pycache__/controls.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/settings/__pycache__/gamepadadvanced.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/settings/__pycache__/gamepadselect.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/settings/__pycache__/touchscreen.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/settings/__pycache__/__init__.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/settings/__pycache__/xbox360controller.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/settings/__pycache__/audio.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/settings/__pycache__/gamepad.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/settings/__pycache__/nettesting.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/settings/__pycache__/remoteapp.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/settings/__pycache__/testing.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/settings/__pycache__/wiimote.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/settings/__pycache__/vrtesting.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/settings/__pycache__/allsettings.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/settings/__pycache__/ps3controller.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/settings/__pycache__/keyboard.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/playlist/__pycache__/customizebrowser.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/playlist/__pycache__/__init__.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/playlist/__pycache__/edit.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/playlist/__pycache__/browser.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/playlist/__pycache__/mapselect.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/playlist/__pycache__/share.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/playlist/__pycache__/editgame.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/playlist/__pycache__/editcontroller.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/playlist/__pycache__/addgame.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/soundtrack/__pycache__/entrytypeselect.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/soundtrack/__pycache__/itunes.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/soundtrack/__pycache__/__init__.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/soundtrack/__pycache__/edit.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/soundtrack/__pycache__/browser.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/league/__pycache__/__init__.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/league/__pycache__/rankbutton.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/league/__pycache__/rankwindow.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/coop/__pycache__/gamebutton.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/coop/__pycache__/__init__.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/coop/__pycache__/browser.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/coop/__pycache__/level.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/profile/__pycache__/__init__.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/profile/__pycache__/edit.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/profile/__pycache__/upgrade.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/profile/__pycache__/browser.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/account/__pycache__/link.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/account/__pycache__/viewer.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/account/__pycache__/__init__.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/account/__pycache__/unlink.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/account/__pycache__/settings.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/store/__pycache__/__init__.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/store/__pycache__/browser.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/store/__pycache__/button.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/store/__pycache__/item.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/activity/__pycache__/freeforallendscreen.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/activity/__pycache__/__init__.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/activity/__pycache__/coopscorescreen.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/activity/__pycache__/dualteamscorescreen.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/activity/__pycache__/coopjoinscreen.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/activity/__pycache__/multiteamendscreen.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/activity/__pycache__/teamsscorescreen.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/activity/__pycache__/multiteamjoinscreen.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/activity/__pycache__/drawscreen.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/game/__pycache__/capturetheflag.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/game/__pycache__/targetpractice.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/game/__pycache__/ninjafight.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/game/__pycache__/easteregghunt.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/game/__pycache__/race.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/game/__pycache__/meteorshower.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/game/__pycache__/thelaststand.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/game/__pycache__/__init__.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/game/__pycache__/football.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/game/__pycache__/kingofthehill.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/game/__pycache__/assault.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/game/__pycache__/keepaway.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/game/__pycache__/elimination.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/game/__pycache__/deathmatch.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/game/__pycache__/onslaught.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/game/__pycache__/hockey.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/game/__pycache__/chosenone.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/game/__pycache__/conquest.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/game/__pycache__/runaround.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/mapdata/__pycache__/bridgit.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/mapdata/__pycache__/big_g.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/mapdata/__pycache__/hockey_stadium.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/mapdata/__pycache__/courtyard.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/mapdata/__pycache__/tower_d.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/mapdata/__pycache__/__init__.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/mapdata/__pycache__/roundabout.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/mapdata/__pycache__/rampage.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/mapdata/__pycache__/crag_castle.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/mapdata/__pycache__/step_right_up.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/mapdata/__pycache__/football_stadium.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/mapdata/__pycache__/the_pad.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/mapdata/__pycache__/happy_thoughts.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/mapdata/__pycache__/monkey_face.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/mapdata/__pycache__/doom_shroom.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/mapdata/__pycache__/zig_zag.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/mapdata/__pycache__/lake_frigid.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/mapdata/__pycache__/tip_top.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/actor/__pycache__/spazfactory.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/actor/__pycache__/bomb.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/actor/__pycache__/spazbot.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/actor/__pycache__/flag.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/actor/__pycache__/scoreboard.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/actor/__pycache__/popuptext.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/actor/__pycache__/background.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/actor/__pycache__/__init__.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/actor/__pycache__/zoomtext.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/actor/__pycache__/spaz.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/actor/__pycache__/spazappearance.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/actor/__pycache__/controlsguide.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/actor/__pycache__/powerupbox.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/actor/__pycache__/text.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/actor/__pycache__/spawner.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/actor/__pycache__/respawnicon.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/actor/__pycache__/playerspaz.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/actor/__pycache__/tipstext.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/actor/__pycache__/onscreencountdown.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/actor/__pycache__/onscreentimer.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/actor/__pycache__/image.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/data/scripts/bastd/session/__pycache__/__init__.cpython-37.opt-1.pyc

SCRIPT_TARGETS_PY_2 = \
  ${ASSET_BUILD_DIR}/pylib-android/zipfile.py \
  ${ASSET_BUILD_DIR}/pylib-android/shutil.py \
  ${ASSET_BUILD_DIR}/pylib-android/tempfile.py \
  ${ASSET_BUILD_DIR}/pylib-android/queue.py \
  ${ASSET_BUILD_DIR}/pylib-android/macpath.py \
  ${ASSET_BUILD_DIR}/pylib-android/_pyio.py \
  ${ASSET_BUILD_DIR}/pylib-android/crypt.py \
  ${ASSET_BUILD_DIR}/pylib-android/pkgutil.py \
  ${ASSET_BUILD_DIR}/pylib-android/_dummy_thread.py \
  ${ASSET_BUILD_DIR}/pylib-android/lzma.py \
  ${ASSET_BUILD_DIR}/pylib-android/asyncore.py \
  ${ASSET_BUILD_DIR}/pylib-android/__phello__.foo.py \
  ${ASSET_BUILD_DIR}/pylib-android/_sitebuiltins.py \
  ${ASSET_BUILD_DIR}/pylib-android/copyreg.py \
  ${ASSET_BUILD_DIR}/pylib-android/sndhdr.py \
  ${ASSET_BUILD_DIR}/pylib-android/rlcompleter.py \
  ${ASSET_BUILD_DIR}/pylib-android/gzip.py \
  ${ASSET_BUILD_DIR}/pylib-android/ipaddress.py \
  ${ASSET_BUILD_DIR}/pylib-android/trace.py \
  ${ASSET_BUILD_DIR}/pylib-android/webbrowser.py \
  ${ASSET_BUILD_DIR}/pylib-android/nntplib.py \
  ${ASSET_BUILD_DIR}/pylib-android/_compat_pickle.py \
  ${ASSET_BUILD_DIR}/pylib-android/_sysconfigdata_m_linux_.py \
  ${ASSET_BUILD_DIR}/pylib-android/dis.py \
  ${ASSET_BUILD_DIR}/pylib-android/formatter.py \
  ${ASSET_BUILD_DIR}/pylib-android/bdb.py \
  ${ASSET_BUILD_DIR}/pylib-android/zipapp.py \
  ${ASSET_BUILD_DIR}/pylib-android/cmd.py \
  ${ASSET_BUILD_DIR}/pylib-android/tty.py \
  ${ASSET_BUILD_DIR}/pylib-android/tabnanny.py \
  ${ASSET_BUILD_DIR}/pylib-android/_py_abc.py \
  ${ASSET_BUILD_DIR}/pylib-android/cProfile.py \
  ${ASSET_BUILD_DIR}/pylib-android/token.py \
  ${ASSET_BUILD_DIR}/pylib-android/textwrap.py \
  ${ASSET_BUILD_DIR}/pylib-android/base64.py \
  ${ASSET_BUILD_DIR}/pylib-android/_markupbase.py \
  ${ASSET_BUILD_DIR}/pylib-android/bz2.py \
  ${ASSET_BUILD_DIR}/pylib-android/signal.py \
  ${ASSET_BUILD_DIR}/pylib-android/sre_constants.py \
  ${ASSET_BUILD_DIR}/pylib-android/cgitb.py \
  ${ASSET_BUILD_DIR}/pylib-android/_threading_local.py \
  ${ASSET_BUILD_DIR}/pylib-android/pyclbr.py \
  ${ASSET_BUILD_DIR}/pylib-android/gettext.py \
  ${ASSET_BUILD_DIR}/pylib-android/wave.py \
  ${ASSET_BUILD_DIR}/pylib-android/weakref.py \
  ${ASSET_BUILD_DIR}/pylib-android/bisect.py \
  ${ASSET_BUILD_DIR}/pylib-android/opcode.py \
  ${ASSET_BUILD_DIR}/pylib-android/netrc.py \
  ${ASSET_BUILD_DIR}/pylib-android/heapq.py \
  ${ASSET_BUILD_DIR}/pylib-android/functools.py \
  ${ASSET_BUILD_DIR}/pylib-android/modulefinder.py \
  ${ASSET_BUILD_DIR}/pylib-android/_compression.py \
  ${ASSET_BUILD_DIR}/pylib-android/tracemalloc.py \
  ${ASSET_BUILD_DIR}/pylib-android/hashlib.py \
  ${ASSET_BUILD_DIR}/pylib-android/cgi.py \
  ${ASSET_BUILD_DIR}/pylib-android/codeop.py \
  ${ASSET_BUILD_DIR}/pylib-android/fnmatch.py \
  ${ASSET_BUILD_DIR}/pylib-android/traceback.py \
  ${ASSET_BUILD_DIR}/pylib-android/nturl2path.py \
  ${ASSET_BUILD_DIR}/pylib-android/warnings.py \
  ${ASSET_BUILD_DIR}/pylib-android/subprocess.py \
  ${ASSET_BUILD_DIR}/pylib-android/profile.py \
  ${ASSET_BUILD_DIR}/pylib-android/imghdr.py \
  ${ASSET_BUILD_DIR}/pylib-android/this.py \
  ${ASSET_BUILD_DIR}/pylib-android/filecmp.py \
  ${ASSET_BUILD_DIR}/pylib-android/codecs.py \
  ${ASSET_BUILD_DIR}/pylib-android/uu.py \
  ${ASSET_BUILD_DIR}/pylib-android/_weakrefset.py \
  ${ASSET_BUILD_DIR}/pylib-android/io.py \
  ${ASSET_BUILD_DIR}/pylib-android/code.py \
  ${ASSET_BUILD_DIR}/pylib-android/operator.py \
  ${ASSET_BUILD_DIR}/pylib-android/fileinput.py \
  ${ASSET_BUILD_DIR}/pylib-android/os.py \
  ${ASSET_BUILD_DIR}/pylib-android/difflib.py \
  ${ASSET_BUILD_DIR}/pylib-android/pydoc.py \
  ${ASSET_BUILD_DIR}/pylib-android/symbol.py \
  ${ASSET_BUILD_DIR}/pylib-android/selectors.py \
  ${ASSET_BUILD_DIR}/pylib-android/decimal.py \
  ${ASSET_BUILD_DIR}/pylib-android/socketserver.py \
  ${ASSET_BUILD_DIR}/pylib-android/copy.py \
  ${ASSET_BUILD_DIR}/pylib-android/genericpath.py \
  ${ASSET_BUILD_DIR}/pylib-android/linecache.py \
  ${ASSET_BUILD_DIR}/pylib-android/types.py \
  ${ASSET_BUILD_DIR}/pylib-android/mimetypes.py \
  ${ASSET_BUILD_DIR}/pylib-android/xdrlib.py \
  ${ASSET_BUILD_DIR}/pylib-android/colorsys.py \
  ${ASSET_BUILD_DIR}/pylib-android/numbers.py \
  ${ASSET_BUILD_DIR}/pylib-android/_strptime.py \
  ${ASSET_BUILD_DIR}/pylib-android/dummy_threading.py \
  ${ASSET_BUILD_DIR}/pylib-android/contextvars.py \
  ${ASSET_BUILD_DIR}/pylib-android/random.py \
  ${ASSET_BUILD_DIR}/pylib-android/ftplib.py \
  ${ASSET_BUILD_DIR}/pylib-android/chunk.py \
  ${ASSET_BUILD_DIR}/pylib-android/optparse.py \
  ${ASSET_BUILD_DIR}/pylib-android/pdb.py \
  ${ASSET_BUILD_DIR}/pylib-android/threading.py \
  ${ASSET_BUILD_DIR}/pylib-android/platform.py \
  ${ASSET_BUILD_DIR}/pylib-android/pstats.py \
  ${ASSET_BUILD_DIR}/pylib-android/glob.py \
  ${ASSET_BUILD_DIR}/pylib-android/quopri.py \
  ${ASSET_BUILD_DIR}/pylib-android/symtable.py \
  ${ASSET_BUILD_DIR}/pylib-android/pprint.py \
  ${ASSET_BUILD_DIR}/pylib-android/calendar.py \
  ${ASSET_BUILD_DIR}/pylib-android/inspect.py \
  ${ASSET_BUILD_DIR}/pylib-android/poplib.py \
  ${ASSET_BUILD_DIR}/pylib-android/binhex.py \
  ${ASSET_BUILD_DIR}/pylib-android/plistlib.py \
  ${ASSET_BUILD_DIR}/pylib-android/pickletools.py \
  ${ASSET_BUILD_DIR}/pylib-android/pipes.py \
  ${ASSET_BUILD_DIR}/pylib-android/site.py \
  ${ASSET_BUILD_DIR}/pylib-android/telnetlib.py \
  ${ASSET_BUILD_DIR}/pylib-android/keyword.py \
  ${ASSET_BUILD_DIR}/pylib-android/configparser.py \
  ${ASSET_BUILD_DIR}/pylib-android/reprlib.py \
  ${ASSET_BUILD_DIR}/pylib-android/secrets.py \
  ${ASSET_BUILD_DIR}/pylib-android/shlex.py \
  ${ASSET_BUILD_DIR}/pylib-android/posixpath.py \
  ${ASSET_BUILD_DIR}/pylib-android/py_compile.py \
  ${ASSET_BUILD_DIR}/pylib-android/_osx_support.py \
  ${ASSET_BUILD_DIR}/pylib-android/stat.py \
  ${ASSET_BUILD_DIR}/pylib-android/compileall.py \
  ${ASSET_BUILD_DIR}/pylib-android/csv.py \
  ${ASSET_BUILD_DIR}/pylib-android/fractions.py \
  ${ASSET_BUILD_DIR}/pylib-android/sched.py \
  ${ASSET_BUILD_DIR}/pylib-android/mailbox.py \
  ${ASSET_BUILD_DIR}/pylib-android/sre_compile.py \
  ${ASSET_BUILD_DIR}/pylib-android/locale.py \
  ${ASSET_BUILD_DIR}/pylib-android/ast.py \
  ${ASSET_BUILD_DIR}/pylib-android/doctest.py \
  ${ASSET_BUILD_DIR}/pylib-android/argparse.py \
  ${ASSET_BUILD_DIR}/pylib-android/getpass.py \
  ${ASSET_BUILD_DIR}/pylib-android/pickle.py \
  ${ASSET_BUILD_DIR}/pylib-android/pty.py \
  ${ASSET_BUILD_DIR}/pylib-android/contextlib.py \
  ${ASSET_BUILD_DIR}/pylib-android/statistics.py \
  ${ASSET_BUILD_DIR}/pylib-android/_collections_abc.py \
  ${ASSET_BUILD_DIR}/pylib-android/sunau.py \
  ${ASSET_BUILD_DIR}/pylib-android/__future__.py \
  ${ASSET_BUILD_DIR}/pylib-android/dataclasses.py \
  ${ASSET_BUILD_DIR}/pylib-android/shelve.py \
  ${ASSET_BUILD_DIR}/pylib-android/string.py \
  ${ASSET_BUILD_DIR}/pylib-android/smtplib.py \
  ${ASSET_BUILD_DIR}/pylib-android/getopt.py \
  ${ASSET_BUILD_DIR}/pylib-android/antigravity.py \
  ${ASSET_BUILD_DIR}/pylib-android/enum.py \
  ${ASSET_BUILD_DIR}/pylib-android/timeit.py \
  ${ASSET_BUILD_DIR}/pylib-android/hmac.py \
  ${ASSET_BUILD_DIR}/pylib-android/tarfile.py \
  ${ASSET_BUILD_DIR}/pylib-android/stringprep.py \
  ${ASSET_BUILD_DIR}/pylib-android/typing.py \
  ${ASSET_BUILD_DIR}/pylib-android/ssl.py \
  ${ASSET_BUILD_DIR}/pylib-android/socket.py \
  ${ASSET_BUILD_DIR}/pylib-android/datetime.py \
  ${ASSET_BUILD_DIR}/pylib-android/sysconfig.py \
  ${ASSET_BUILD_DIR}/pylib-android/pathlib.py \
  ${ASSET_BUILD_DIR}/pylib-android/_pydecimal.py \
  ${ASSET_BUILD_DIR}/pylib-android/ntpath.py \
  ${ASSET_BUILD_DIR}/pylib-android/tokenize.py \
  ${ASSET_BUILD_DIR}/pylib-android/uuid.py \
  ${ASSET_BUILD_DIR}/pylib-android/imp.py \
  ${ASSET_BUILD_DIR}/pylib-android/smtpd.py \
  ${ASSET_BUILD_DIR}/pylib-android/re.py \
  ${ASSET_BUILD_DIR}/pylib-android/mailcap.py \
  ${ASSET_BUILD_DIR}/pylib-android/aifc.py \
  ${ASSET_BUILD_DIR}/pylib-android/struct.py \
  ${ASSET_BUILD_DIR}/pylib-android/asynchat.py \
  ${ASSET_BUILD_DIR}/pylib-android/sre_parse.py \
  ${ASSET_BUILD_DIR}/pylib-android/abc.py \
  ${ASSET_BUILD_DIR}/pylib-android/runpy.py \
  ${ASSET_BUILD_DIR}/pylib-android/_bootlocale.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/mac_romanian.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/mac_farsi.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/idna.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/cp273.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/punycode.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/raw_unicode_escape.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/utf_8.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/cp1252.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/cp869.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/iso8859_14.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/iso8859_2.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/mac_arabic.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/mac_croatian.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/big5hkscs.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/cp1256.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/iso8859_6.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/iso8859_10.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/iso2022_kr.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/cp1140.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/unicode_internal.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/cp1125.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/iso2022_jp_1.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/cp1257.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/cp949.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/cp858.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/iso8859_7.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/iso8859_11.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/hp_roman8.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/koi8_r.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/zlib_codec.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/gbk.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/johab.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/cp1253.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/iso8859_15.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/iso2022_jp_2004.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/mac_iceland.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/iso8859_3.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/mac_greek.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/rot_13.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/utf_16_be.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/euc_kr.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/mac_centeuro.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/euc_jisx0213.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/cp863.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/ascii.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/iso8859_8.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/cp857.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/utf_32_be.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/cp1258.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/oem.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/mac_latin2.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/cp775.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/mac_roman.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__init__.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/cp852.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/shift_jisx0213.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/cp866.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/utf_7.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/base64_codec.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/cp932.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/cp720.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/cp862.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/cp437.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/palmos.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/iso8859_9.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/cp856.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/aliases.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/latin_1.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/cp875.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/cp950.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/unicode_escape.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/cp737.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/cp865.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/ptcp154.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/big5.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/cp424.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/cp861.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/euc_jp.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/cp855.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/shift_jis.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/utf_32_le.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/cp500.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/undefined.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/cp860.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/uu_codec.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/utf_16_le.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/gb18030.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/cp65001.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/cp874.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/cp850.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/cp864.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/utf_32.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/koi8_u.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/cp1254.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/iso2022_jp_2.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/utf_16.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/iso8859_4.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/euc_jis_2004.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/mbcs.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/cp1250.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/gb2312.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/iso8859_16.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/mac_cyrillic.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/hex_codec.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/tis_620.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/cp037.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/cp1006.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/cp1251.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/mac_turkish.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/iso2022_jp_ext.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/iso8859_1.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/hz.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/bz2_codec.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/quopri_codec.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/kz1048.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/utf_8_sig.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/koi8_t.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/cp1255.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/iso2022_jp_3.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/shift_jis_2004.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/cp1026.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/charmap.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/iso8859_5.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/iso8859_13.py \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/iso2022_jp.py \
  ${ASSET_BUILD_DIR}/pylib-android/ctypes/_aix.py \
  ${ASSET_BUILD_DIR}/pylib-android/ctypes/wintypes.py \
  ${ASSET_BUILD_DIR}/pylib-android/ctypes/util.py \
  ${ASSET_BUILD_DIR}/pylib-android/ctypes/__init__.py \
  ${ASSET_BUILD_DIR}/pylib-android/ctypes/_endian.py \
  ${ASSET_BUILD_DIR}/pylib-android/ctypes/macholib/dyld.py \
  ${ASSET_BUILD_DIR}/pylib-android/ctypes/macholib/framework.py \
  ${ASSET_BUILD_DIR}/pylib-android/ctypes/macholib/__init__.py \
  ${ASSET_BUILD_DIR}/pylib-android/ctypes/macholib/dylib.py \
  ${ASSET_BUILD_DIR}/pylib-android/curses/textpad.py \
  ${ASSET_BUILD_DIR}/pylib-android/curses/ascii.py \
  ${ASSET_BUILD_DIR}/pylib-android/curses/__init__.py \
  ${ASSET_BUILD_DIR}/pylib-android/curses/has_key.py \
  ${ASSET_BUILD_DIR}/pylib-android/curses/panel.py \
  ${ASSET_BUILD_DIR}/pylib-android/urllib/error.py \
  ${ASSET_BUILD_DIR}/pylib-android/urllib/request.py \
  ${ASSET_BUILD_DIR}/pylib-android/urllib/__init__.py \
  ${ASSET_BUILD_DIR}/pylib-android/urllib/response.py \
  ${ASSET_BUILD_DIR}/pylib-android/urllib/robotparser.py \
  ${ASSET_BUILD_DIR}/pylib-android/urllib/parse.py \
  ${ASSET_BUILD_DIR}/pylib-android/html/__init__.py \
  ${ASSET_BUILD_DIR}/pylib-android/html/parser.py \
  ${ASSET_BUILD_DIR}/pylib-android/html/entities.py \
  ${ASSET_BUILD_DIR}/pylib-android/xml/__init__.py \
  ${ASSET_BUILD_DIR}/pylib-android/xml/parsers/expat.py \
  ${ASSET_BUILD_DIR}/pylib-android/xml/parsers/__init__.py \
  ${ASSET_BUILD_DIR}/pylib-android/xml/sax/handler.py \
  ${ASSET_BUILD_DIR}/pylib-android/xml/sax/__init__.py \
  ${ASSET_BUILD_DIR}/pylib-android/xml/sax/saxutils.py \
  ${ASSET_BUILD_DIR}/pylib-android/xml/sax/xmlreader.py \
  ${ASSET_BUILD_DIR}/pylib-android/xml/sax/expatreader.py \
  ${ASSET_BUILD_DIR}/pylib-android/xml/sax/_exceptions.py \
  ${ASSET_BUILD_DIR}/pylib-android/xml/dom/pulldom.py \
  ${ASSET_BUILD_DIR}/pylib-android/xml/dom/expatbuilder.py \
  ${ASSET_BUILD_DIR}/pylib-android/xml/dom/domreg.py \
  ${ASSET_BUILD_DIR}/pylib-android/xml/dom/minicompat.py \
  ${ASSET_BUILD_DIR}/pylib-android/xml/dom/__init__.py \
  ${ASSET_BUILD_DIR}/pylib-android/xml/dom/NodeFilter.py \
  ${ASSET_BUILD_DIR}/pylib-android/xml/dom/xmlbuilder.py \
  ${ASSET_BUILD_DIR}/pylib-android/xml/dom/minidom.py \
  ${ASSET_BUILD_DIR}/pylib-android/xml/etree/ElementPath.py \
  ${ASSET_BUILD_DIR}/pylib-android/xml/etree/cElementTree.py \
  ${ASSET_BUILD_DIR}/pylib-android/xml/etree/__init__.py \
  ${ASSET_BUILD_DIR}/pylib-android/xml/etree/ElementInclude.py \
  ${ASSET_BUILD_DIR}/pylib-android/xml/etree/ElementTree.py \
  ${ASSET_BUILD_DIR}/pylib-android/json/decoder.py \
  ${ASSET_BUILD_DIR}/pylib-android/json/scanner.py \
  ${ASSET_BUILD_DIR}/pylib-android/json/__init__.py \
  ${ASSET_BUILD_DIR}/pylib-android/json/encoder.py \
  ${ASSET_BUILD_DIR}/pylib-android/json/tool.py \
  ${ASSET_BUILD_DIR}/pylib-android/http/cookies.py \
  ${ASSET_BUILD_DIR}/pylib-android/http/server.py \
  ${ASSET_BUILD_DIR}/pylib-android/http/client.py \
  ${ASSET_BUILD_DIR}/pylib-android/http/__init__.py \
  ${ASSET_BUILD_DIR}/pylib-android/http/cookiejar.py \
  ${ASSET_BUILD_DIR}/pylib-android/sqlite3/__init__.py \
  ${ASSET_BUILD_DIR}/pylib-android/sqlite3/dump.py \
  ${ASSET_BUILD_DIR}/pylib-android/sqlite3/dbapi2.py \
  ${ASSET_BUILD_DIR}/pylib-android/concurrent/__init__.py \
  ${ASSET_BUILD_DIR}/pylib-android/concurrent/futures/_base.py \
  ${ASSET_BUILD_DIR}/pylib-android/concurrent/futures/thread.py \
  ${ASSET_BUILD_DIR}/pylib-android/concurrent/futures/__init__.py \
  ${ASSET_BUILD_DIR}/pylib-android/concurrent/futures/process.py \
  ${ASSET_BUILD_DIR}/pylib-android/importlib/util.py \
  ${ASSET_BUILD_DIR}/pylib-android/importlib/_bootstrap.py \
  ${ASSET_BUILD_DIR}/pylib-android/importlib/__init__.py \
  ${ASSET_BUILD_DIR}/pylib-android/importlib/_bootstrap_external.py \
  ${ASSET_BUILD_DIR}/pylib-android/importlib/resources.py \
  ${ASSET_BUILD_DIR}/pylib-android/importlib/machinery.py \
  ${ASSET_BUILD_DIR}/pylib-android/importlib/abc.py \
  ${ASSET_BUILD_DIR}/pylib-android/xmlrpc/server.py \
  ${ASSET_BUILD_DIR}/pylib-android/xmlrpc/client.py \
  ${ASSET_BUILD_DIR}/pylib-android/xmlrpc/__init__.py \
  ${ASSET_BUILD_DIR}/pylib-android/collections/__init__.py \
  ${ASSET_BUILD_DIR}/pylib-android/collections/abc.py \
  ${ASSET_BUILD_DIR}/pylib-android/asyncio/queues.py \
  ${ASSET_BUILD_DIR}/pylib-android/asyncio/streams.py \
  ${ASSET_BUILD_DIR}/pylib-android/asyncio/tasks.py \
  ${ASSET_BUILD_DIR}/pylib-android/asyncio/selector_events.py \
  ${ASSET_BUILD_DIR}/pylib-android/asyncio/log.py \
  ${ASSET_BUILD_DIR}/pylib-android/asyncio/protocols.py \
  ${ASSET_BUILD_DIR}/pylib-android/asyncio/events.py \
  ${ASSET_BUILD_DIR}/pylib-android/asyncio/base_events.py \
  ${ASSET_BUILD_DIR}/pylib-android/asyncio/subprocess.py \
  ${ASSET_BUILD_DIR}/pylib-android/asyncio/constants.py \
  ${ASSET_BUILD_DIR}/pylib-android/asyncio/proactor_events.py \
  ${ASSET_BUILD_DIR}/pylib-android/asyncio/format_helpers.py \
  ${ASSET_BUILD_DIR}/pylib-android/asyncio/locks.py \
  ${ASSET_BUILD_DIR}/pylib-android/asyncio/__init__.py \
  ${ASSET_BUILD_DIR}/pylib-android/asyncio/futures.py \
  ${ASSET_BUILD_DIR}/pylib-android/asyncio/sslproto.py \
  ${ASSET_BUILD_DIR}/pylib-android/asyncio/base_subprocess.py \
  ${ASSET_BUILD_DIR}/pylib-android/asyncio/windows_utils.py \
  ${ASSET_BUILD_DIR}/pylib-android/asyncio/runners.py \
  ${ASSET_BUILD_DIR}/pylib-android/asyncio/transports.py \
  ${ASSET_BUILD_DIR}/pylib-android/asyncio/base_tasks.py \
  ${ASSET_BUILD_DIR}/pylib-android/asyncio/coroutines.py \
  ${ASSET_BUILD_DIR}/pylib-android/asyncio/windows_events.py \
  ${ASSET_BUILD_DIR}/pylib-android/asyncio/base_futures.py \
  ${ASSET_BUILD_DIR}/pylib-android/asyncio/unix_events.py \
  ${ASSET_BUILD_DIR}/pylib-android/logging/config.py \
  ${ASSET_BUILD_DIR}/pylib-android/logging/handlers.py \
  ${ASSET_BUILD_DIR}/pylib-android/logging/__init__.py \
  ${ASSET_BUILD_DIR}/pylib-android/email/contentmanager.py \
  ${ASSET_BUILD_DIR}/pylib-android/email/_policybase.py \
  ${ASSET_BUILD_DIR}/pylib-android/email/header.py \
  ${ASSET_BUILD_DIR}/pylib-android/email/_encoded_words.py \
  ${ASSET_BUILD_DIR}/pylib-android/email/_header_value_parser.py \
  ${ASSET_BUILD_DIR}/pylib-android/email/policy.py \
  ${ASSET_BUILD_DIR}/pylib-android/email/__init__.py \
  ${ASSET_BUILD_DIR}/pylib-android/email/message.py \
  ${ASSET_BUILD_DIR}/pylib-android/email/encoders.py \
  ${ASSET_BUILD_DIR}/pylib-android/email/parser.py \
  ${ASSET_BUILD_DIR}/pylib-android/email/generator.py \
  ${ASSET_BUILD_DIR}/pylib-android/email/utils.py \
  ${ASSET_BUILD_DIR}/pylib-android/email/charset.py \
  ${ASSET_BUILD_DIR}/pylib-android/email/iterators.py \
  ${ASSET_BUILD_DIR}/pylib-android/email/quoprimime.py \
  ${ASSET_BUILD_DIR}/pylib-android/email/errors.py \
  ${ASSET_BUILD_DIR}/pylib-android/email/feedparser.py \
  ${ASSET_BUILD_DIR}/pylib-android/email/_parseaddr.py \
  ${ASSET_BUILD_DIR}/pylib-android/email/base64mime.py \
  ${ASSET_BUILD_DIR}/pylib-android/email/headerregistry.py \
  ${ASSET_BUILD_DIR}/pylib-android/email/mime/multipart.py \
  ${ASSET_BUILD_DIR}/pylib-android/email/mime/__init__.py \
  ${ASSET_BUILD_DIR}/pylib-android/email/mime/message.py \
  ${ASSET_BUILD_DIR}/pylib-android/email/mime/application.py \
  ${ASSET_BUILD_DIR}/pylib-android/email/mime/nonmultipart.py \
  ${ASSET_BUILD_DIR}/pylib-android/email/mime/text.py \
  ${ASSET_BUILD_DIR}/pylib-android/email/mime/audio.py \
  ${ASSET_BUILD_DIR}/pylib-android/email/mime/image.py \
  ${ASSET_BUILD_DIR}/pylib-android/email/mime/base.py \
  ${ASSET_BUILD_DIR}/pylib-apple/zipfile.py \
  ${ASSET_BUILD_DIR}/pylib-apple/shutil.py \
  ${ASSET_BUILD_DIR}/pylib-apple/tempfile.py \
  ${ASSET_BUILD_DIR}/pylib-apple/queue.py \
  ${ASSET_BUILD_DIR}/pylib-apple/macpath.py \
  ${ASSET_BUILD_DIR}/pylib-apple/_sysconfigdata_m_darwin_darwin.py \
  ${ASSET_BUILD_DIR}/pylib-apple/_pyio.py \
  ${ASSET_BUILD_DIR}/pylib-apple/crypt.py \
  ${ASSET_BUILD_DIR}/pylib-apple/pkgutil.py \
  ${ASSET_BUILD_DIR}/pylib-apple/_dummy_thread.py \
  ${ASSET_BUILD_DIR}/pylib-apple/lzma.py \
  ${ASSET_BUILD_DIR}/pylib-apple/asyncore.py \
  ${ASSET_BUILD_DIR}/pylib-apple/__phello__.foo.py \
  ${ASSET_BUILD_DIR}/pylib-apple/_sitebuiltins.py \
  ${ASSET_BUILD_DIR}/pylib-apple/copyreg.py \
  ${ASSET_BUILD_DIR}/pylib-apple/sndhdr.py \
  ${ASSET_BUILD_DIR}/pylib-apple/rlcompleter.py \
  ${ASSET_BUILD_DIR}/pylib-apple/gzip.py \
  ${ASSET_BUILD_DIR}/pylib-apple/ipaddress.py \
  ${ASSET_BUILD_DIR}/pylib-apple/trace.py \
  ${ASSET_BUILD_DIR}/pylib-apple/webbrowser.py \
  ${ASSET_BUILD_DIR}/pylib-apple/nntplib.py \
  ${ASSET_BUILD_DIR}/pylib-apple/_compat_pickle.py \
  ${ASSET_BUILD_DIR}/pylib-apple/dis.py \
  ${ASSET_BUILD_DIR}/pylib-apple/formatter.py \
  ${ASSET_BUILD_DIR}/pylib-apple/bdb.py \
  ${ASSET_BUILD_DIR}/pylib-apple/zipapp.py \
  ${ASSET_BUILD_DIR}/pylib-apple/cmd.py \
  ${ASSET_BUILD_DIR}/pylib-apple/tty.py \
  ${ASSET_BUILD_DIR}/pylib-apple/tabnanny.py \
  ${ASSET_BUILD_DIR}/pylib-apple/_py_abc.py \
  ${ASSET_BUILD_DIR}/pylib-apple/cProfile.py \
  ${ASSET_BUILD_DIR}/pylib-apple/token.py \
  ${ASSET_BUILD_DIR}/pylib-apple/textwrap.py \
  ${ASSET_BUILD_DIR}/pylib-apple/base64.py \
  ${ASSET_BUILD_DIR}/pylib-apple/_markupbase.py \
  ${ASSET_BUILD_DIR}/pylib-apple/bz2.py \
  ${ASSET_BUILD_DIR}/pylib-apple/signal.py \
  ${ASSET_BUILD_DIR}/pylib-apple/sre_constants.py \
  ${ASSET_BUILD_DIR}/pylib-apple/cgitb.py \
  ${ASSET_BUILD_DIR}/pylib-apple/_threading_local.py \
  ${ASSET_BUILD_DIR}/pylib-apple/pyclbr.py \
  ${ASSET_BUILD_DIR}/pylib-apple/gettext.py \
  ${ASSET_BUILD_DIR}/pylib-apple/wave.py \
  ${ASSET_BUILD_DIR}/pylib-apple/weakref.py \
  ${ASSET_BUILD_DIR}/pylib-apple/bisect.py \
  ${ASSET_BUILD_DIR}/pylib-apple/opcode.py \
  ${ASSET_BUILD_DIR}/pylib-apple/netrc.py \
  ${ASSET_BUILD_DIR}/pylib-apple/heapq.py \
  ${ASSET_BUILD_DIR}/pylib-apple/functools.py \
  ${ASSET_BUILD_DIR}/pylib-apple/modulefinder.py \
  ${ASSET_BUILD_DIR}/pylib-apple/_compression.py \
  ${ASSET_BUILD_DIR}/pylib-apple/tracemalloc.py \
  ${ASSET_BUILD_DIR}/pylib-apple/hashlib.py \
  ${ASSET_BUILD_DIR}/pylib-apple/cgi.py \
  ${ASSET_BUILD_DIR}/pylib-apple/codeop.py \
  ${ASSET_BUILD_DIR}/pylib-apple/fnmatch.py \
  ${ASSET_BUILD_DIR}/pylib-apple/traceback.py \
  ${ASSET_BUILD_DIR}/pylib-apple/nturl2path.py \
  ${ASSET_BUILD_DIR}/pylib-apple/warnings.py \
  ${ASSET_BUILD_DIR}/pylib-apple/subprocess.py \
  ${ASSET_BUILD_DIR}/pylib-apple/profile.py \
  ${ASSET_BUILD_DIR}/pylib-apple/imghdr.py \
  ${ASSET_BUILD_DIR}/pylib-apple/this.py \
  ${ASSET_BUILD_DIR}/pylib-apple/filecmp.py \
  ${ASSET_BUILD_DIR}/pylib-apple/codecs.py \
  ${ASSET_BUILD_DIR}/pylib-apple/uu.py \
  ${ASSET_BUILD_DIR}/pylib-apple/_weakrefset.py \
  ${ASSET_BUILD_DIR}/pylib-apple/io.py \
  ${ASSET_BUILD_DIR}/pylib-apple/code.py \
  ${ASSET_BUILD_DIR}/pylib-apple/operator.py \
  ${ASSET_BUILD_DIR}/pylib-apple/fileinput.py \
  ${ASSET_BUILD_DIR}/pylib-apple/os.py \
  ${ASSET_BUILD_DIR}/pylib-apple/difflib.py \
  ${ASSET_BUILD_DIR}/pylib-apple/pydoc.py \
  ${ASSET_BUILD_DIR}/pylib-apple/symbol.py \
  ${ASSET_BUILD_DIR}/pylib-apple/selectors.py \
  ${ASSET_BUILD_DIR}/pylib-apple/decimal.py \
  ${ASSET_BUILD_DIR}/pylib-apple/socketserver.py \
  ${ASSET_BUILD_DIR}/pylib-apple/copy.py \
  ${ASSET_BUILD_DIR}/pylib-apple/genericpath.py \
  ${ASSET_BUILD_DIR}/pylib-apple/linecache.py \
  ${ASSET_BUILD_DIR}/pylib-apple/types.py \
  ${ASSET_BUILD_DIR}/pylib-apple/mimetypes.py \
  ${ASSET_BUILD_DIR}/pylib-apple/xdrlib.py \
  ${ASSET_BUILD_DIR}/pylib-apple/colorsys.py \
  ${ASSET_BUILD_DIR}/pylib-apple/numbers.py \
  ${ASSET_BUILD_DIR}/pylib-apple/_strptime.py \
  ${ASSET_BUILD_DIR}/pylib-apple/dummy_threading.py \
  ${ASSET_BUILD_DIR}/pylib-apple/contextvars.py \
  ${ASSET_BUILD_DIR}/pylib-apple/random.py \
  ${ASSET_BUILD_DIR}/pylib-apple/ftplib.py \
  ${ASSET_BUILD_DIR}/pylib-apple/chunk.py \
  ${ASSET_BUILD_DIR}/pylib-apple/optparse.py \
  ${ASSET_BUILD_DIR}/pylib-apple/pdb.py \
  ${ASSET_BUILD_DIR}/pylib-apple/threading.py \
  ${ASSET_BUILD_DIR}/pylib-apple/platform.py \
  ${ASSET_BUILD_DIR}/pylib-apple/pstats.py \
  ${ASSET_BUILD_DIR}/pylib-apple/glob.py \
  ${ASSET_BUILD_DIR}/pylib-apple/quopri.py \
  ${ASSET_BUILD_DIR}/pylib-apple/symtable.py \
  ${ASSET_BUILD_DIR}/pylib-apple/pprint.py \
  ${ASSET_BUILD_DIR}/pylib-apple/calendar.py \
  ${ASSET_BUILD_DIR}/pylib-apple/inspect.py \
  ${ASSET_BUILD_DIR}/pylib-apple/poplib.py \
  ${ASSET_BUILD_DIR}/pylib-apple/binhex.py \
  ${ASSET_BUILD_DIR}/pylib-apple/plistlib.py \
  ${ASSET_BUILD_DIR}/pylib-apple/pickletools.py \
  ${ASSET_BUILD_DIR}/pylib-apple/pipes.py \
  ${ASSET_BUILD_DIR}/pylib-apple/site.py \
  ${ASSET_BUILD_DIR}/pylib-apple/telnetlib.py \
  ${ASSET_BUILD_DIR}/pylib-apple/keyword.py \
  ${ASSET_BUILD_DIR}/pylib-apple/configparser.py \
  ${ASSET_BUILD_DIR}/pylib-apple/reprlib.py \
  ${ASSET_BUILD_DIR}/pylib-apple/secrets.py \
  ${ASSET_BUILD_DIR}/pylib-apple/shlex.py \
  ${ASSET_BUILD_DIR}/pylib-apple/posixpath.py \
  ${ASSET_BUILD_DIR}/pylib-apple/py_compile.py \
  ${ASSET_BUILD_DIR}/pylib-apple/_osx_support.py \
  ${ASSET_BUILD_DIR}/pylib-apple/stat.py \
  ${ASSET_BUILD_DIR}/pylib-apple/compileall.py \
  ${ASSET_BUILD_DIR}/pylib-apple/csv.py \
  ${ASSET_BUILD_DIR}/pylib-apple/fractions.py \
  ${ASSET_BUILD_DIR}/pylib-apple/sched.py \
  ${ASSET_BUILD_DIR}/pylib-apple/mailbox.py \
  ${ASSET_BUILD_DIR}/pylib-apple/sre_compile.py \
  ${ASSET_BUILD_DIR}/pylib-apple/locale.py \
  ${ASSET_BUILD_DIR}/pylib-apple/ast.py \
  ${ASSET_BUILD_DIR}/pylib-apple/doctest.py \
  ${ASSET_BUILD_DIR}/pylib-apple/argparse.py \
  ${ASSET_BUILD_DIR}/pylib-apple/getpass.py \
  ${ASSET_BUILD_DIR}/pylib-apple/pickle.py \
  ${ASSET_BUILD_DIR}/pylib-apple/pty.py \
  ${ASSET_BUILD_DIR}/pylib-apple/contextlib.py \
  ${ASSET_BUILD_DIR}/pylib-apple/statistics.py \
  ${ASSET_BUILD_DIR}/pylib-apple/_collections_abc.py \
  ${ASSET_BUILD_DIR}/pylib-apple/sunau.py \
  ${ASSET_BUILD_DIR}/pylib-apple/__future__.py \
  ${ASSET_BUILD_DIR}/pylib-apple/dataclasses.py \
  ${ASSET_BUILD_DIR}/pylib-apple/shelve.py \
  ${ASSET_BUILD_DIR}/pylib-apple/string.py \
  ${ASSET_BUILD_DIR}/pylib-apple/smtplib.py \
  ${ASSET_BUILD_DIR}/pylib-apple/getopt.py \
  ${ASSET_BUILD_DIR}/pylib-apple/antigravity.py \
  ${ASSET_BUILD_DIR}/pylib-apple/enum.py \
  ${ASSET_BUILD_DIR}/pylib-apple/timeit.py \
  ${ASSET_BUILD_DIR}/pylib-apple/hmac.py \
  ${ASSET_BUILD_DIR}/pylib-apple/tarfile.py \
  ${ASSET_BUILD_DIR}/pylib-apple/stringprep.py \
  ${ASSET_BUILD_DIR}/pylib-apple/typing.py \
  ${ASSET_BUILD_DIR}/pylib-apple/ssl.py \
  ${ASSET_BUILD_DIR}/pylib-apple/socket.py \
  ${ASSET_BUILD_DIR}/pylib-apple/datetime.py \
  ${ASSET_BUILD_DIR}/pylib-apple/sysconfig.py \
  ${ASSET_BUILD_DIR}/pylib-apple/pathlib.py \
  ${ASSET_BUILD_DIR}/pylib-apple/_pydecimal.py \
  ${ASSET_BUILD_DIR}/pylib-apple/ntpath.py \
  ${ASSET_BUILD_DIR}/pylib-apple/tokenize.py \
  ${ASSET_BUILD_DIR}/pylib-apple/uuid.py \
  ${ASSET_BUILD_DIR}/pylib-apple/imp.py \
  ${ASSET_BUILD_DIR}/pylib-apple/smtpd.py \
  ${ASSET_BUILD_DIR}/pylib-apple/re.py \
  ${ASSET_BUILD_DIR}/pylib-apple/mailcap.py \
  ${ASSET_BUILD_DIR}/pylib-apple/aifc.py \
  ${ASSET_BUILD_DIR}/pylib-apple/struct.py \
  ${ASSET_BUILD_DIR}/pylib-apple/asynchat.py \
  ${ASSET_BUILD_DIR}/pylib-apple/sre_parse.py \
  ${ASSET_BUILD_DIR}/pylib-apple/abc.py \
  ${ASSET_BUILD_DIR}/pylib-apple/runpy.py \
  ${ASSET_BUILD_DIR}/pylib-apple/_bootlocale.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/mac_romanian.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/mac_farsi.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/idna.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp273.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/punycode.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/raw_unicode_escape.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/utf_8.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp1252.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp869.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/iso8859_14.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/iso8859_2.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/mac_arabic.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/mac_croatian.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/big5hkscs.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp1256.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/iso8859_6.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/iso8859_10.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/iso2022_kr.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp1140.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/unicode_internal.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp1125.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/iso2022_jp_1.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp1257.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp949.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp858.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/iso8859_7.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/iso8859_11.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/hp_roman8.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/koi8_r.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/zlib_codec.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/gbk.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/johab.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp1253.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/iso8859_15.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/iso2022_jp_2004.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/mac_iceland.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/iso8859_3.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/mac_greek.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/rot_13.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/utf_16_be.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/euc_kr.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/mac_centeuro.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/euc_jisx0213.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp863.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/ascii.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/iso8859_8.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp857.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/utf_32_be.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp1258.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/oem.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/mac_latin2.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp775.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/mac_roman.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__init__.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp852.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/shift_jisx0213.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp866.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/utf_7.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/base64_codec.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp932.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp720.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp862.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp437.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/palmos.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/iso8859_9.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp856.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/aliases.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/latin_1.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp875.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp950.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/unicode_escape.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp737.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp865.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/ptcp154.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/big5.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp424.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp861.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/euc_jp.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp855.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/shift_jis.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/utf_32_le.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp500.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/undefined.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp860.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/uu_codec.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/utf_16_le.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/gb18030.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp65001.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp874.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp850.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp864.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/utf_32.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/koi8_u.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp1254.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/iso2022_jp_2.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/utf_16.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/iso8859_4.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/euc_jis_2004.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/mbcs.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp1250.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/gb2312.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/iso8859_16.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/mac_cyrillic.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/hex_codec.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/tis_620.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp037.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp1006.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp1251.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/mac_turkish.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/iso2022_jp_ext.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/iso8859_1.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/hz.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/bz2_codec.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/quopri_codec.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/kz1048.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/utf_8_sig.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/koi8_t.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp1255.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/iso2022_jp_3.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/shift_jis_2004.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp1026.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/charmap.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/iso8859_5.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/iso8859_13.py \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/iso2022_jp.py \
  ${ASSET_BUILD_DIR}/pylib-apple/ctypes/_aix.py \
  ${ASSET_BUILD_DIR}/pylib-apple/ctypes/wintypes.py \
  ${ASSET_BUILD_DIR}/pylib-apple/ctypes/util.py \
  ${ASSET_BUILD_DIR}/pylib-apple/ctypes/__init__.py \
  ${ASSET_BUILD_DIR}/pylib-apple/ctypes/_endian.py \
  ${ASSET_BUILD_DIR}/pylib-apple/ctypes/macholib/dyld.py \
  ${ASSET_BUILD_DIR}/pylib-apple/ctypes/macholib/framework.py \
  ${ASSET_BUILD_DIR}/pylib-apple/ctypes/macholib/__init__.py \
  ${ASSET_BUILD_DIR}/pylib-apple/ctypes/macholib/dylib.py \
  ${ASSET_BUILD_DIR}/pylib-apple/curses/textpad.py \
  ${ASSET_BUILD_DIR}/pylib-apple/curses/ascii.py \
  ${ASSET_BUILD_DIR}/pylib-apple/curses/__init__.py \
  ${ASSET_BUILD_DIR}/pylib-apple/curses/has_key.py \
  ${ASSET_BUILD_DIR}/pylib-apple/curses/panel.py \
  ${ASSET_BUILD_DIR}/pylib-apple/urllib/error.py \
  ${ASSET_BUILD_DIR}/pylib-apple/urllib/request.py \
  ${ASSET_BUILD_DIR}/pylib-apple/urllib/__init__.py \
  ${ASSET_BUILD_DIR}/pylib-apple/urllib/response.py \
  ${ASSET_BUILD_DIR}/pylib-apple/urllib/robotparser.py \
  ${ASSET_BUILD_DIR}/pylib-apple/urllib/parse.py \
  ${ASSET_BUILD_DIR}/pylib-apple/html/__init__.py \
  ${ASSET_BUILD_DIR}/pylib-apple/html/parser.py \
  ${ASSET_BUILD_DIR}/pylib-apple/html/entities.py \
  ${ASSET_BUILD_DIR}/pylib-apple/xml/__init__.py \
  ${ASSET_BUILD_DIR}/pylib-apple/xml/parsers/expat.py \
  ${ASSET_BUILD_DIR}/pylib-apple/xml/parsers/__init__.py \
  ${ASSET_BUILD_DIR}/pylib-apple/xml/sax/handler.py \
  ${ASSET_BUILD_DIR}/pylib-apple/xml/sax/__init__.py \
  ${ASSET_BUILD_DIR}/pylib-apple/xml/sax/saxutils.py \
  ${ASSET_BUILD_DIR}/pylib-apple/xml/sax/xmlreader.py \
  ${ASSET_BUILD_DIR}/pylib-apple/xml/sax/expatreader.py \
  ${ASSET_BUILD_DIR}/pylib-apple/xml/sax/_exceptions.py \
  ${ASSET_BUILD_DIR}/pylib-apple/xml/dom/pulldom.py \
  ${ASSET_BUILD_DIR}/pylib-apple/xml/dom/expatbuilder.py \
  ${ASSET_BUILD_DIR}/pylib-apple/xml/dom/domreg.py \
  ${ASSET_BUILD_DIR}/pylib-apple/xml/dom/minicompat.py \
  ${ASSET_BUILD_DIR}/pylib-apple/xml/dom/__init__.py \
  ${ASSET_BUILD_DIR}/pylib-apple/xml/dom/NodeFilter.py \
  ${ASSET_BUILD_DIR}/pylib-apple/xml/dom/xmlbuilder.py \
  ${ASSET_BUILD_DIR}/pylib-apple/xml/dom/minidom.py \
  ${ASSET_BUILD_DIR}/pylib-apple/xml/etree/ElementPath.py \
  ${ASSET_BUILD_DIR}/pylib-apple/xml/etree/cElementTree.py \
  ${ASSET_BUILD_DIR}/pylib-apple/xml/etree/__init__.py \
  ${ASSET_BUILD_DIR}/pylib-apple/xml/etree/ElementInclude.py \
  ${ASSET_BUILD_DIR}/pylib-apple/xml/etree/ElementTree.py \
  ${ASSET_BUILD_DIR}/pylib-apple/json/decoder.py \
  ${ASSET_BUILD_DIR}/pylib-apple/json/scanner.py \
  ${ASSET_BUILD_DIR}/pylib-apple/json/__init__.py \
  ${ASSET_BUILD_DIR}/pylib-apple/json/encoder.py \
  ${ASSET_BUILD_DIR}/pylib-apple/json/tool.py \
  ${ASSET_BUILD_DIR}/pylib-apple/http/cookies.py \
  ${ASSET_BUILD_DIR}/pylib-apple/http/server.py \
  ${ASSET_BUILD_DIR}/pylib-apple/http/client.py \
  ${ASSET_BUILD_DIR}/pylib-apple/http/__init__.py \
  ${ASSET_BUILD_DIR}/pylib-apple/http/cookiejar.py \
  ${ASSET_BUILD_DIR}/pylib-apple/sqlite3/__init__.py \
  ${ASSET_BUILD_DIR}/pylib-apple/sqlite3/dump.py \
  ${ASSET_BUILD_DIR}/pylib-apple/sqlite3/dbapi2.py \
  ${ASSET_BUILD_DIR}/pylib-apple/concurrent/__init__.py \
  ${ASSET_BUILD_DIR}/pylib-apple/concurrent/futures/_base.py \
  ${ASSET_BUILD_DIR}/pylib-apple/concurrent/futures/thread.py \
  ${ASSET_BUILD_DIR}/pylib-apple/concurrent/futures/__init__.py \
  ${ASSET_BUILD_DIR}/pylib-apple/concurrent/futures/process.py \
  ${ASSET_BUILD_DIR}/pylib-apple/importlib/util.py \
  ${ASSET_BUILD_DIR}/pylib-apple/importlib/_bootstrap.py \
  ${ASSET_BUILD_DIR}/pylib-apple/importlib/__init__.py \
  ${ASSET_BUILD_DIR}/pylib-apple/importlib/_bootstrap_external.py \
  ${ASSET_BUILD_DIR}/pylib-apple/importlib/resources.py \
  ${ASSET_BUILD_DIR}/pylib-apple/importlib/machinery.py \
  ${ASSET_BUILD_DIR}/pylib-apple/importlib/abc.py \
  ${ASSET_BUILD_DIR}/pylib-apple/xmlrpc/server.py \
  ${ASSET_BUILD_DIR}/pylib-apple/xmlrpc/client.py \
  ${ASSET_BUILD_DIR}/pylib-apple/xmlrpc/__init__.py \
  ${ASSET_BUILD_DIR}/pylib-apple/collections/__init__.py \
  ${ASSET_BUILD_DIR}/pylib-apple/collections/abc.py \
  ${ASSET_BUILD_DIR}/pylib-apple/asyncio/queues.py \
  ${ASSET_BUILD_DIR}/pylib-apple/asyncio/streams.py \
  ${ASSET_BUILD_DIR}/pylib-apple/asyncio/tasks.py \
  ${ASSET_BUILD_DIR}/pylib-apple/asyncio/selector_events.py \
  ${ASSET_BUILD_DIR}/pylib-apple/asyncio/log.py \
  ${ASSET_BUILD_DIR}/pylib-apple/asyncio/protocols.py \
  ${ASSET_BUILD_DIR}/pylib-apple/asyncio/events.py \
  ${ASSET_BUILD_DIR}/pylib-apple/asyncio/base_events.py \
  ${ASSET_BUILD_DIR}/pylib-apple/asyncio/subprocess.py \
  ${ASSET_BUILD_DIR}/pylib-apple/asyncio/constants.py \
  ${ASSET_BUILD_DIR}/pylib-apple/asyncio/proactor_events.py \
  ${ASSET_BUILD_DIR}/pylib-apple/asyncio/format_helpers.py \
  ${ASSET_BUILD_DIR}/pylib-apple/asyncio/locks.py \
  ${ASSET_BUILD_DIR}/pylib-apple/asyncio/__init__.py \
  ${ASSET_BUILD_DIR}/pylib-apple/asyncio/futures.py \
  ${ASSET_BUILD_DIR}/pylib-apple/asyncio/sslproto.py \
  ${ASSET_BUILD_DIR}/pylib-apple/asyncio/base_subprocess.py \
  ${ASSET_BUILD_DIR}/pylib-apple/asyncio/windows_utils.py \
  ${ASSET_BUILD_DIR}/pylib-apple/asyncio/runners.py \
  ${ASSET_BUILD_DIR}/pylib-apple/asyncio/transports.py \
  ${ASSET_BUILD_DIR}/pylib-apple/asyncio/base_tasks.py \
  ${ASSET_BUILD_DIR}/pylib-apple/asyncio/coroutines.py \
  ${ASSET_BUILD_DIR}/pylib-apple/asyncio/windows_events.py \
  ${ASSET_BUILD_DIR}/pylib-apple/asyncio/base_futures.py \
  ${ASSET_BUILD_DIR}/pylib-apple/asyncio/unix_events.py \
  ${ASSET_BUILD_DIR}/pylib-apple/logging/config.py \
  ${ASSET_BUILD_DIR}/pylib-apple/logging/handlers.py \
  ${ASSET_BUILD_DIR}/pylib-apple/logging/__init__.py \
  ${ASSET_BUILD_DIR}/pylib-apple/email/contentmanager.py \
  ${ASSET_BUILD_DIR}/pylib-apple/email/_policybase.py \
  ${ASSET_BUILD_DIR}/pylib-apple/email/header.py \
  ${ASSET_BUILD_DIR}/pylib-apple/email/_encoded_words.py \
  ${ASSET_BUILD_DIR}/pylib-apple/email/_header_value_parser.py \
  ${ASSET_BUILD_DIR}/pylib-apple/email/policy.py \
  ${ASSET_BUILD_DIR}/pylib-apple/email/__init__.py \
  ${ASSET_BUILD_DIR}/pylib-apple/email/message.py \
  ${ASSET_BUILD_DIR}/pylib-apple/email/encoders.py \
  ${ASSET_BUILD_DIR}/pylib-apple/email/parser.py \
  ${ASSET_BUILD_DIR}/pylib-apple/email/generator.py \
  ${ASSET_BUILD_DIR}/pylib-apple/email/utils.py \
  ${ASSET_BUILD_DIR}/pylib-apple/email/charset.py \
  ${ASSET_BUILD_DIR}/pylib-apple/email/iterators.py \
  ${ASSET_BUILD_DIR}/pylib-apple/email/quoprimime.py \
  ${ASSET_BUILD_DIR}/pylib-apple/email/errors.py \
  ${ASSET_BUILD_DIR}/pylib-apple/email/feedparser.py \
  ${ASSET_BUILD_DIR}/pylib-apple/email/_parseaddr.py \
  ${ASSET_BUILD_DIR}/pylib-apple/email/base64mime.py \
  ${ASSET_BUILD_DIR}/pylib-apple/email/headerregistry.py \
  ${ASSET_BUILD_DIR}/pylib-apple/email/mime/multipart.py \
  ${ASSET_BUILD_DIR}/pylib-apple/email/mime/__init__.py \
  ${ASSET_BUILD_DIR}/pylib-apple/email/mime/message.py \
  ${ASSET_BUILD_DIR}/pylib-apple/email/mime/application.py \
  ${ASSET_BUILD_DIR}/pylib-apple/email/mime/nonmultipart.py \
  ${ASSET_BUILD_DIR}/pylib-apple/email/mime/text.py \
  ${ASSET_BUILD_DIR}/pylib-apple/email/mime/audio.py \
  ${ASSET_BUILD_DIR}/pylib-apple/email/mime/image.py \
  ${ASSET_BUILD_DIR}/pylib-apple/email/mime/base.py \
  ${ASSET_BUILD_DIR}/pylib-site-packages/typing_extensions.py

SCRIPT_TARGETS_PYC_2 = \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/zipfile.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/shutil.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/tempfile.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/queue.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/macpath.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/_pyio.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/crypt.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/pkgutil.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/_dummy_thread.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/lzma.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/asyncore.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/__phello__.foo.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/_sitebuiltins.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/copyreg.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/sndhdr.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/rlcompleter.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/gzip.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/ipaddress.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/trace.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/webbrowser.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/nntplib.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/_compat_pickle.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/_sysconfigdata_m_linux_.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/dis.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/formatter.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/bdb.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/zipapp.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/cmd.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/tty.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/tabnanny.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/_py_abc.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/cProfile.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/token.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/textwrap.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/base64.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/_markupbase.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/bz2.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/signal.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/sre_constants.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/cgitb.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/_threading_local.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/pyclbr.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/gettext.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/wave.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/weakref.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/bisect.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/opcode.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/netrc.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/heapq.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/functools.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/modulefinder.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/_compression.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/tracemalloc.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/hashlib.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/cgi.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/codeop.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/fnmatch.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/traceback.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/nturl2path.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/warnings.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/subprocess.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/profile.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/imghdr.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/this.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/filecmp.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/codecs.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/uu.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/_weakrefset.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/io.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/code.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/operator.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/fileinput.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/os.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/difflib.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/pydoc.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/symbol.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/selectors.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/decimal.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/socketserver.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/copy.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/genericpath.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/linecache.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/types.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/mimetypes.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/xdrlib.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/colorsys.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/numbers.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/_strptime.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/dummy_threading.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/contextvars.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/random.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/ftplib.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/chunk.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/optparse.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/pdb.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/threading.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/platform.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/pstats.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/glob.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/quopri.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/symtable.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/pprint.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/calendar.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/inspect.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/poplib.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/binhex.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/plistlib.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/pickletools.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/pipes.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/site.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/telnetlib.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/keyword.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/configparser.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/reprlib.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/secrets.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/shlex.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/posixpath.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/py_compile.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/_osx_support.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/stat.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/compileall.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/csv.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/fractions.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/sched.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/mailbox.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/sre_compile.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/locale.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/ast.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/doctest.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/argparse.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/getpass.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/pickle.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/pty.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/contextlib.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/statistics.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/_collections_abc.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/sunau.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/__future__.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/dataclasses.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/shelve.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/string.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/smtplib.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/getopt.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/antigravity.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/enum.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/timeit.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/hmac.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/tarfile.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/stringprep.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/typing.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/ssl.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/socket.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/datetime.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/sysconfig.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/pathlib.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/_pydecimal.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/ntpath.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/tokenize.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/uuid.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/imp.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/smtpd.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/re.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/mailcap.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/aifc.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/struct.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/asynchat.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/sre_parse.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/abc.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/runpy.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/__pycache__/_bootlocale.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/mac_romanian.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/mac_farsi.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/idna.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp273.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/punycode.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/raw_unicode_escape.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/utf_8.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp1252.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp869.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/iso8859_14.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/iso8859_2.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/mac_arabic.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/mac_croatian.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/big5hkscs.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp1256.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/iso8859_6.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/iso8859_10.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/iso2022_kr.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp1140.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/unicode_internal.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp1125.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/iso2022_jp_1.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp1257.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp949.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp858.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/iso8859_7.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/iso8859_11.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/hp_roman8.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/koi8_r.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/zlib_codec.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/gbk.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/johab.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp1253.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/iso8859_15.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/iso2022_jp_2004.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/mac_iceland.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/iso8859_3.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/mac_greek.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/rot_13.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/utf_16_be.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/euc_kr.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/mac_centeuro.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/euc_jisx0213.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp863.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/ascii.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/iso8859_8.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp857.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/utf_32_be.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp1258.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/oem.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/mac_latin2.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp775.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/mac_roman.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/__init__.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp852.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/shift_jisx0213.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp866.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/utf_7.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/base64_codec.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp932.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp720.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp862.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp437.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/palmos.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/iso8859_9.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp856.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/aliases.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/latin_1.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp875.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp950.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/unicode_escape.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp737.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp865.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/ptcp154.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/big5.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp424.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp861.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/euc_jp.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp855.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/shift_jis.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/utf_32_le.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp500.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/undefined.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp860.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/uu_codec.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/utf_16_le.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/gb18030.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp65001.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp874.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp850.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp864.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/utf_32.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/koi8_u.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp1254.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/iso2022_jp_2.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/utf_16.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/iso8859_4.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/euc_jis_2004.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/mbcs.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp1250.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/gb2312.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/iso8859_16.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/mac_cyrillic.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/hex_codec.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/tis_620.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp037.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp1006.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp1251.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/mac_turkish.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/iso2022_jp_ext.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/iso8859_1.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/hz.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/bz2_codec.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/quopri_codec.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/kz1048.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/utf_8_sig.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/koi8_t.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp1255.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/iso2022_jp_3.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/shift_jis_2004.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp1026.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/charmap.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/iso8859_5.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/iso8859_13.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/iso2022_jp.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/ctypes/__pycache__/_aix.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/ctypes/__pycache__/wintypes.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/ctypes/__pycache__/util.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/ctypes/__pycache__/__init__.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/ctypes/__pycache__/_endian.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/ctypes/macholib/__pycache__/dyld.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/ctypes/macholib/__pycache__/framework.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/ctypes/macholib/__pycache__/__init__.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/ctypes/macholib/__pycache__/dylib.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/curses/__pycache__/textpad.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/curses/__pycache__/ascii.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/curses/__pycache__/__init__.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/curses/__pycache__/has_key.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/curses/__pycache__/panel.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/urllib/__pycache__/error.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/urllib/__pycache__/request.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/urllib/__pycache__/__init__.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/urllib/__pycache__/response.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/urllib/__pycache__/robotparser.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/urllib/__pycache__/parse.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/html/__pycache__/__init__.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/html/__pycache__/parser.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/html/__pycache__/entities.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/xml/__pycache__/__init__.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/xml/parsers/__pycache__/expat.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/xml/parsers/__pycache__/__init__.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/xml/sax/__pycache__/handler.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/xml/sax/__pycache__/__init__.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/xml/sax/__pycache__/saxutils.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/xml/sax/__pycache__/xmlreader.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/xml/sax/__pycache__/expatreader.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/xml/sax/__pycache__/_exceptions.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/xml/dom/__pycache__/pulldom.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/xml/dom/__pycache__/expatbuilder.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/xml/dom/__pycache__/domreg.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/xml/dom/__pycache__/minicompat.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/xml/dom/__pycache__/__init__.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/xml/dom/__pycache__/NodeFilter.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/xml/dom/__pycache__/xmlbuilder.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/xml/dom/__pycache__/minidom.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/xml/etree/__pycache__/ElementPath.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/xml/etree/__pycache__/cElementTree.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/xml/etree/__pycache__/__init__.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/xml/etree/__pycache__/ElementInclude.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/xml/etree/__pycache__/ElementTree.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/json/__pycache__/decoder.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/json/__pycache__/scanner.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/json/__pycache__/__init__.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/json/__pycache__/encoder.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/json/__pycache__/tool.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/http/__pycache__/cookies.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/http/__pycache__/server.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/http/__pycache__/client.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/http/__pycache__/__init__.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/http/__pycache__/cookiejar.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/sqlite3/__pycache__/__init__.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/sqlite3/__pycache__/dump.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/sqlite3/__pycache__/dbapi2.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/concurrent/__pycache__/__init__.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/concurrent/futures/__pycache__/_base.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/concurrent/futures/__pycache__/thread.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/concurrent/futures/__pycache__/__init__.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/concurrent/futures/__pycache__/process.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/importlib/__pycache__/util.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/importlib/__pycache__/_bootstrap.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/importlib/__pycache__/__init__.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/importlib/__pycache__/_bootstrap_external.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/importlib/__pycache__/resources.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/importlib/__pycache__/machinery.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/importlib/__pycache__/abc.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/xmlrpc/__pycache__/server.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/xmlrpc/__pycache__/client.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/xmlrpc/__pycache__/__init__.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/collections/__pycache__/__init__.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/collections/__pycache__/abc.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/asyncio/__pycache__/queues.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/asyncio/__pycache__/streams.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/asyncio/__pycache__/tasks.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/asyncio/__pycache__/selector_events.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/asyncio/__pycache__/log.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/asyncio/__pycache__/protocols.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/asyncio/__pycache__/events.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/asyncio/__pycache__/base_events.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/asyncio/__pycache__/subprocess.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/asyncio/__pycache__/constants.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/asyncio/__pycache__/proactor_events.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/asyncio/__pycache__/format_helpers.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/asyncio/__pycache__/locks.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/asyncio/__pycache__/__init__.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/asyncio/__pycache__/futures.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/asyncio/__pycache__/sslproto.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/asyncio/__pycache__/base_subprocess.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/asyncio/__pycache__/windows_utils.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/asyncio/__pycache__/runners.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/asyncio/__pycache__/transports.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/asyncio/__pycache__/base_tasks.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/asyncio/__pycache__/coroutines.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/asyncio/__pycache__/windows_events.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/asyncio/__pycache__/base_futures.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/asyncio/__pycache__/unix_events.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/logging/__pycache__/config.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/logging/__pycache__/handlers.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/logging/__pycache__/__init__.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/email/__pycache__/contentmanager.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/email/__pycache__/_policybase.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/email/__pycache__/header.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/email/__pycache__/_encoded_words.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/email/__pycache__/_header_value_parser.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/email/__pycache__/policy.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/email/__pycache__/__init__.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/email/__pycache__/message.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/email/__pycache__/encoders.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/email/__pycache__/parser.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/email/__pycache__/generator.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/email/__pycache__/utils.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/email/__pycache__/charset.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/email/__pycache__/iterators.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/email/__pycache__/quoprimime.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/email/__pycache__/errors.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/email/__pycache__/feedparser.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/email/__pycache__/_parseaddr.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/email/__pycache__/base64mime.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/email/__pycache__/headerregistry.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/email/mime/__pycache__/multipart.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/email/mime/__pycache__/__init__.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/email/mime/__pycache__/message.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/email/mime/__pycache__/application.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/email/mime/__pycache__/nonmultipart.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/email/mime/__pycache__/text.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/email/mime/__pycache__/audio.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/email/mime/__pycache__/image.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-android/email/mime/__pycache__/base.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/zipfile.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/shutil.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/tempfile.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/queue.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/macpath.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/_sysconfigdata_m_darwin_darwin.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/_pyio.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/crypt.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/pkgutil.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/_dummy_thread.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/lzma.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/asyncore.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/__phello__.foo.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/_sitebuiltins.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/copyreg.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/sndhdr.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/rlcompleter.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/gzip.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/ipaddress.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/trace.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/webbrowser.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/nntplib.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/_compat_pickle.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/dis.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/formatter.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/bdb.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/zipapp.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/cmd.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/tty.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/tabnanny.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/_py_abc.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/cProfile.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/token.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/textwrap.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/base64.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/_markupbase.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/bz2.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/signal.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/sre_constants.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/cgitb.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/_threading_local.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/pyclbr.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/gettext.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/wave.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/weakref.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/bisect.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/opcode.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/netrc.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/heapq.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/functools.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/modulefinder.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/_compression.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/tracemalloc.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/hashlib.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/cgi.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/codeop.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/fnmatch.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/traceback.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/nturl2path.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/warnings.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/subprocess.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/profile.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/imghdr.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/this.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/filecmp.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/codecs.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/uu.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/_weakrefset.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/io.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/code.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/operator.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/fileinput.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/os.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/difflib.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/pydoc.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/symbol.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/selectors.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/decimal.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/socketserver.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/copy.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/genericpath.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/linecache.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/types.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/mimetypes.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/xdrlib.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/colorsys.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/numbers.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/_strptime.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/dummy_threading.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/contextvars.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/random.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/ftplib.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/chunk.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/optparse.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/pdb.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/threading.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/platform.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/pstats.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/glob.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/quopri.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/symtable.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/pprint.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/calendar.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/inspect.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/poplib.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/binhex.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/plistlib.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/pickletools.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/pipes.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/site.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/telnetlib.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/keyword.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/configparser.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/reprlib.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/secrets.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/shlex.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/posixpath.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/py_compile.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/_osx_support.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/stat.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/compileall.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/csv.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/fractions.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/sched.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/mailbox.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/sre_compile.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/locale.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/ast.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/doctest.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/argparse.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/getpass.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/pickle.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/pty.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/contextlib.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/statistics.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/_collections_abc.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/sunau.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/__future__.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/dataclasses.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/shelve.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/string.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/smtplib.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/getopt.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/antigravity.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/enum.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/timeit.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/hmac.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/tarfile.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/stringprep.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/typing.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/ssl.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/socket.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/datetime.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/sysconfig.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/pathlib.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/_pydecimal.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/ntpath.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/tokenize.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/uuid.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/imp.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/smtpd.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/re.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/mailcap.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/aifc.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/struct.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/asynchat.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/sre_parse.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/abc.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/runpy.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/__pycache__/_bootlocale.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/mac_romanian.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/mac_farsi.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/idna.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp273.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/punycode.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/raw_unicode_escape.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/utf_8.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp1252.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp869.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/iso8859_14.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/iso8859_2.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/mac_arabic.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/mac_croatian.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/big5hkscs.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp1256.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/iso8859_6.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/iso8859_10.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/iso2022_kr.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp1140.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/unicode_internal.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp1125.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/iso2022_jp_1.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp1257.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp949.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp858.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/iso8859_7.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/iso8859_11.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/hp_roman8.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/koi8_r.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/zlib_codec.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/gbk.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/johab.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp1253.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/iso8859_15.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/iso2022_jp_2004.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/mac_iceland.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/iso8859_3.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/mac_greek.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/rot_13.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/utf_16_be.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/euc_kr.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/mac_centeuro.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/euc_jisx0213.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp863.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/ascii.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/iso8859_8.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp857.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/utf_32_be.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp1258.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/oem.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/mac_latin2.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp775.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/mac_roman.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/__init__.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp852.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/shift_jisx0213.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp866.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/utf_7.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/base64_codec.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp932.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp720.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp862.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp437.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/palmos.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/iso8859_9.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp856.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/aliases.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/latin_1.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp875.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp950.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/unicode_escape.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp737.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp865.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/ptcp154.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/big5.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp424.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp861.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/euc_jp.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp855.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/shift_jis.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/utf_32_le.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp500.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/undefined.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp860.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/uu_codec.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/utf_16_le.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/gb18030.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp65001.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp874.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp850.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp864.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/utf_32.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/koi8_u.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp1254.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/iso2022_jp_2.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/utf_16.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/iso8859_4.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/euc_jis_2004.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/mbcs.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp1250.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/gb2312.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/iso8859_16.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/mac_cyrillic.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/hex_codec.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/tis_620.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp037.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp1006.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp1251.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/mac_turkish.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/iso2022_jp_ext.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/iso8859_1.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/hz.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/bz2_codec.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/quopri_codec.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/kz1048.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/utf_8_sig.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/koi8_t.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp1255.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/iso2022_jp_3.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/shift_jis_2004.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp1026.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/charmap.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/iso8859_5.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/iso8859_13.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/iso2022_jp.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/ctypes/__pycache__/_aix.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/ctypes/__pycache__/wintypes.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/ctypes/__pycache__/util.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/ctypes/__pycache__/__init__.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/ctypes/__pycache__/_endian.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/ctypes/macholib/__pycache__/dyld.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/ctypes/macholib/__pycache__/framework.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/ctypes/macholib/__pycache__/__init__.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/ctypes/macholib/__pycache__/dylib.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/curses/__pycache__/textpad.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/curses/__pycache__/ascii.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/curses/__pycache__/__init__.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/curses/__pycache__/has_key.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/curses/__pycache__/panel.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/urllib/__pycache__/error.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/urllib/__pycache__/request.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/urllib/__pycache__/__init__.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/urllib/__pycache__/response.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/urllib/__pycache__/robotparser.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/urllib/__pycache__/parse.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/html/__pycache__/__init__.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/html/__pycache__/parser.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/html/__pycache__/entities.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/xml/__pycache__/__init__.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/xml/parsers/__pycache__/expat.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/xml/parsers/__pycache__/__init__.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/xml/sax/__pycache__/handler.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/xml/sax/__pycache__/__init__.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/xml/sax/__pycache__/saxutils.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/xml/sax/__pycache__/xmlreader.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/xml/sax/__pycache__/expatreader.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/xml/sax/__pycache__/_exceptions.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/xml/dom/__pycache__/pulldom.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/xml/dom/__pycache__/expatbuilder.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/xml/dom/__pycache__/domreg.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/xml/dom/__pycache__/minicompat.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/xml/dom/__pycache__/__init__.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/xml/dom/__pycache__/NodeFilter.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/xml/dom/__pycache__/xmlbuilder.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/xml/dom/__pycache__/minidom.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/xml/etree/__pycache__/ElementPath.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/xml/etree/__pycache__/cElementTree.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/xml/etree/__pycache__/__init__.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/xml/etree/__pycache__/ElementInclude.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/xml/etree/__pycache__/ElementTree.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/json/__pycache__/decoder.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/json/__pycache__/scanner.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/json/__pycache__/__init__.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/json/__pycache__/encoder.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/json/__pycache__/tool.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/http/__pycache__/cookies.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/http/__pycache__/server.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/http/__pycache__/client.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/http/__pycache__/__init__.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/http/__pycache__/cookiejar.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/sqlite3/__pycache__/__init__.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/sqlite3/__pycache__/dump.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/sqlite3/__pycache__/dbapi2.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/concurrent/__pycache__/__init__.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/concurrent/futures/__pycache__/_base.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/concurrent/futures/__pycache__/thread.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/concurrent/futures/__pycache__/__init__.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/concurrent/futures/__pycache__/process.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/importlib/__pycache__/util.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/importlib/__pycache__/_bootstrap.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/importlib/__pycache__/__init__.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/importlib/__pycache__/_bootstrap_external.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/importlib/__pycache__/resources.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/importlib/__pycache__/machinery.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/importlib/__pycache__/abc.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/xmlrpc/__pycache__/server.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/xmlrpc/__pycache__/client.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/xmlrpc/__pycache__/__init__.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/collections/__pycache__/__init__.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/collections/__pycache__/abc.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/asyncio/__pycache__/queues.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/asyncio/__pycache__/streams.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/asyncio/__pycache__/tasks.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/asyncio/__pycache__/selector_events.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/asyncio/__pycache__/log.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/asyncio/__pycache__/protocols.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/asyncio/__pycache__/events.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/asyncio/__pycache__/base_events.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/asyncio/__pycache__/subprocess.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/asyncio/__pycache__/constants.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/asyncio/__pycache__/proactor_events.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/asyncio/__pycache__/format_helpers.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/asyncio/__pycache__/locks.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/asyncio/__pycache__/__init__.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/asyncio/__pycache__/futures.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/asyncio/__pycache__/sslproto.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/asyncio/__pycache__/base_subprocess.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/asyncio/__pycache__/windows_utils.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/asyncio/__pycache__/runners.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/asyncio/__pycache__/transports.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/asyncio/__pycache__/base_tasks.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/asyncio/__pycache__/coroutines.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/asyncio/__pycache__/windows_events.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/asyncio/__pycache__/base_futures.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/asyncio/__pycache__/unix_events.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/logging/__pycache__/config.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/logging/__pycache__/handlers.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/logging/__pycache__/__init__.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/email/__pycache__/contentmanager.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/email/__pycache__/_policybase.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/email/__pycache__/header.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/email/__pycache__/_encoded_words.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/email/__pycache__/_header_value_parser.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/email/__pycache__/policy.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/email/__pycache__/__init__.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/email/__pycache__/message.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/email/__pycache__/encoders.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/email/__pycache__/parser.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/email/__pycache__/generator.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/email/__pycache__/utils.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/email/__pycache__/charset.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/email/__pycache__/iterators.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/email/__pycache__/quoprimime.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/email/__pycache__/errors.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/email/__pycache__/feedparser.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/email/__pycache__/_parseaddr.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/email/__pycache__/base64mime.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/email/__pycache__/headerregistry.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/email/mime/__pycache__/multipart.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/email/mime/__pycache__/__init__.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/email/mime/__pycache__/message.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/email/mime/__pycache__/application.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/email/mime/__pycache__/nonmultipart.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/email/mime/__pycache__/text.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/email/mime/__pycache__/audio.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/email/mime/__pycache__/image.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-apple/email/mime/__pycache__/base.cpython-37.opt-1.pyc \
  ${ASSET_BUILD_DIR}/pylib-site-packages/__pycache__/typing_extensions.cpython-37.opt-1.pyc


# rule to copy src asset scripts to dst
# (and make non-writable so I'm less likely to accidentally edit them there)
$(SCRIPT_TARGETS_PY_1) : ${ASSET_BUILD_DIR}/%.py : ${ASSET_SRC_DIR}/%.py
	@echo Copying script: $(notdir $@)
	@mkdir -p $(dir $@)
	@rm -f $@
	@cp $^ $@
	@chmod 444 $@

# rule to copy src asset scripts to dst
# (and make non-writable so I'm less likely to accidentally edit them there)
$(SCRIPT_TARGETS_PY_2) : ../.efrocachemap
	@cd .. && tools/snippets efrocache_get assets/$@

# looks like path mangling from py to pyc is too complex for pattern rules so
# just generating explicit targets for each:

${ASSET_BUILD_DIR}/server/__pycache__/server.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/server/server.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/server/__pycache__/config.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/server/config.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bafoundation/__pycache__/executils.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bafoundation/executils.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bafoundation/__pycache__/dataclassutils.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bafoundation/dataclassutils.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bafoundation/__pycache__/util.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bafoundation/util.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bafoundation/__pycache__/__init__.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bafoundation/__init__.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bafoundation/__pycache__/jsonutils.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bafoundation/jsonutils.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bafoundation/__pycache__/err.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bafoundation/err.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bafoundation/entity/__pycache__/_base.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bafoundation/entity/_base.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bafoundation/entity/__pycache__/_support.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bafoundation/entity/_support.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bafoundation/entity/__pycache__/util.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bafoundation/entity/util.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bafoundation/entity/__pycache__/_entity.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bafoundation/entity/_entity.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bafoundation/entity/__pycache__/_field.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bafoundation/entity/_field.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bafoundation/entity/__pycache__/__init__.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bafoundation/entity/__init__.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bafoundation/entity/__pycache__/_value.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bafoundation/entity/_value.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_gameactivity.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/ba/_gameactivity.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_apputils.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/ba/_apputils.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_coopsession.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/ba/_coopsession.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_appdelegate.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/ba/_appdelegate.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/internal.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/ba/internal.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_coopgame.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/ba/_coopgame.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_meta.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/ba/_meta.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_math.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/ba/_math.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_appconfig.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/ba/_appconfig.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_gameresults.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/ba/_gameresults.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_profile.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/ba/_profile.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_error.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/ba/_error.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_achievement.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/ba/_achievement.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_teambasesession.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/ba/_teambasesession.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_gameutils.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/ba/_gameutils.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_activity.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/ba/_activity.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/deprecated.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/ba/deprecated.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_modutils.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/ba/_modutils.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_tips.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/ba/_tips.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_store.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/ba/_store.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_activitytypes.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/ba/_activitytypes.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/__init__.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/ba/__init__.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_session.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/ba/_session.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_hooks.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/ba/_hooks.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_enums.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/ba/_enums.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_netutils.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/ba/_netutils.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_app.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/ba/_app.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_benchmark.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/ba/_benchmark.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_tournament.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/ba/_tournament.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_messages.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/ba/_messages.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_teamssession.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/ba/_teamssession.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_freeforallsession.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/ba/_freeforallsession.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_playlist.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/ba/_playlist.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_team.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/ba/_team.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_actor.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/ba/_actor.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_powerup.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/ba/_powerup.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_campaign.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/ba/_campaign.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_lobby.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/ba/_lobby.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_stats.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/ba/_stats.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_input.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/ba/_input.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_dep.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/ba/_dep.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_level.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/ba/_level.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_general.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/ba/_general.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_server.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/ba/_server.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_account.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/ba/_account.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_music.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/ba/_music.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_lang.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/ba/_lang.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_maps.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/ba/_maps.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/ba/__pycache__/_teamgame.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/ba/_teamgame.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/ba/ui/__pycache__/__init__.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/ba/ui/__init__.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/__pycache__/mainmenu.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/mainmenu.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/__pycache__/maps.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/maps.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/__pycache__/appdelegate.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/appdelegate.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/__pycache__/tutorial.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/tutorial.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/__pycache__/__init__.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/__init__.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/__pycache__/stdmap.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/stdmap.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/playoptions.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/playoptions.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/mainmenu.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/mainmenu.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/getremote.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/getremote.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/tournamententry.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/tournamententry.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/telnet.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/telnet.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/appinvite.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/appinvite.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/gather.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/gather.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/config.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/config.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/colorpicker.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/colorpicker.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/tabs.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/tabs.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/promocode.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/promocode.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/fileselector.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/fileselector.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/feedback.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/feedback.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/teamnamescolors.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/teamnamescolors.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/configerror.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/configerror.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/serverdialog.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/serverdialog.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/getcurrency.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/getcurrency.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/__init__.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__init__.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/specialoffer.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/specialoffer.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/helpui.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/helpui.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/purchase.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/purchase.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/continues.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/continues.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/play.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/play.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/popup.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/popup.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/onscreenkeyboard.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/onscreenkeyboard.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/kiosk.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/kiosk.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/qrcode.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/qrcode.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/trophies.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/trophies.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/partyqueue.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/partyqueue.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/url.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/url.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/debug.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/debug.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/iconpicker.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/iconpicker.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/watch.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/watch.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/achievements.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/achievements.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/radiogroup.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/radiogroup.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/creditslist.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/creditslist.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/tournamentscores.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/tournamentscores.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/characterpicker.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/characterpicker.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/report.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/report.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/resourcetypeinfo.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/resourcetypeinfo.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/confirm.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/confirm.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/__pycache__/party.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/party.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/settings/__pycache__/graphics.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/settings/graphics.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/settings/__pycache__/advanced.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/settings/advanced.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/settings/__pycache__/controls.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/settings/controls.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/settings/__pycache__/gamepadadvanced.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/settings/gamepadadvanced.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/settings/__pycache__/gamepadselect.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/settings/gamepadselect.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/settings/__pycache__/touchscreen.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/settings/touchscreen.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/settings/__pycache__/__init__.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/settings/__init__.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/settings/__pycache__/xbox360controller.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/settings/xbox360controller.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/settings/__pycache__/audio.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/settings/audio.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/settings/__pycache__/gamepad.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/settings/gamepad.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/settings/__pycache__/nettesting.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/settings/nettesting.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/settings/__pycache__/remoteapp.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/settings/remoteapp.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/settings/__pycache__/testing.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/settings/testing.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/settings/__pycache__/wiimote.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/settings/wiimote.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/settings/__pycache__/vrtesting.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/settings/vrtesting.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/settings/__pycache__/allsettings.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/settings/allsettings.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/settings/__pycache__/ps3controller.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/settings/ps3controller.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/settings/__pycache__/keyboard.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/settings/keyboard.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/playlist/__pycache__/customizebrowser.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/playlist/customizebrowser.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/playlist/__pycache__/__init__.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/playlist/__init__.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/playlist/__pycache__/edit.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/playlist/edit.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/playlist/__pycache__/browser.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/playlist/browser.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/playlist/__pycache__/mapselect.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/playlist/mapselect.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/playlist/__pycache__/share.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/playlist/share.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/playlist/__pycache__/editgame.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/playlist/editgame.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/playlist/__pycache__/editcontroller.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/playlist/editcontroller.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/playlist/__pycache__/addgame.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/playlist/addgame.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/soundtrack/__pycache__/entrytypeselect.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/soundtrack/entrytypeselect.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/soundtrack/__pycache__/itunes.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/soundtrack/itunes.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/soundtrack/__pycache__/__init__.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/soundtrack/__init__.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/soundtrack/__pycache__/edit.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/soundtrack/edit.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/soundtrack/__pycache__/browser.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/soundtrack/browser.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/league/__pycache__/__init__.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/league/__init__.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/league/__pycache__/rankbutton.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/league/rankbutton.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/league/__pycache__/rankwindow.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/league/rankwindow.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/coop/__pycache__/gamebutton.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/coop/gamebutton.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/coop/__pycache__/__init__.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/coop/__init__.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/coop/__pycache__/browser.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/coop/browser.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/coop/__pycache__/level.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/coop/level.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/profile/__pycache__/__init__.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/profile/__init__.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/profile/__pycache__/edit.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/profile/edit.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/profile/__pycache__/upgrade.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/profile/upgrade.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/profile/__pycache__/browser.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/profile/browser.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/account/__pycache__/link.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/account/link.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/account/__pycache__/viewer.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/account/viewer.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/account/__pycache__/__init__.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/account/__init__.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/account/__pycache__/unlink.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/account/unlink.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/account/__pycache__/settings.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/account/settings.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/store/__pycache__/__init__.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/store/__init__.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/store/__pycache__/browser.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/store/browser.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/store/__pycache__/button.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/store/button.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/ui/store/__pycache__/item.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/ui/store/item.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/activity/__pycache__/freeforallendscreen.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/activity/freeforallendscreen.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/activity/__pycache__/__init__.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/activity/__init__.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/activity/__pycache__/coopscorescreen.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/activity/coopscorescreen.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/activity/__pycache__/dualteamscorescreen.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/activity/dualteamscorescreen.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/activity/__pycache__/coopjoinscreen.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/activity/coopjoinscreen.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/activity/__pycache__/multiteamendscreen.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/activity/multiteamendscreen.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/activity/__pycache__/teamsscorescreen.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/activity/teamsscorescreen.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/activity/__pycache__/multiteamjoinscreen.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/activity/multiteamjoinscreen.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/activity/__pycache__/drawscreen.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/activity/drawscreen.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/game/__pycache__/capturetheflag.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/game/capturetheflag.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/game/__pycache__/targetpractice.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/game/targetpractice.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/game/__pycache__/ninjafight.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/game/ninjafight.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/game/__pycache__/easteregghunt.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/game/easteregghunt.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/game/__pycache__/race.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/game/race.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/game/__pycache__/meteorshower.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/game/meteorshower.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/game/__pycache__/thelaststand.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/game/thelaststand.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/game/__pycache__/__init__.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/game/__init__.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/game/__pycache__/football.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/game/football.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/game/__pycache__/kingofthehill.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/game/kingofthehill.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/game/__pycache__/assault.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/game/assault.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/game/__pycache__/keepaway.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/game/keepaway.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/game/__pycache__/elimination.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/game/elimination.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/game/__pycache__/deathmatch.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/game/deathmatch.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/game/__pycache__/onslaught.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/game/onslaught.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/game/__pycache__/hockey.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/game/hockey.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/game/__pycache__/chosenone.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/game/chosenone.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/game/__pycache__/conquest.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/game/conquest.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/game/__pycache__/runaround.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/game/runaround.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/mapdata/__pycache__/bridgit.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/mapdata/bridgit.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/mapdata/__pycache__/big_g.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/mapdata/big_g.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/mapdata/__pycache__/hockey_stadium.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/mapdata/hockey_stadium.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/mapdata/__pycache__/courtyard.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/mapdata/courtyard.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/mapdata/__pycache__/tower_d.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/mapdata/tower_d.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/mapdata/__pycache__/__init__.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/mapdata/__init__.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/mapdata/__pycache__/roundabout.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/mapdata/roundabout.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/mapdata/__pycache__/rampage.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/mapdata/rampage.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/mapdata/__pycache__/crag_castle.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/mapdata/crag_castle.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/mapdata/__pycache__/step_right_up.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/mapdata/step_right_up.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/mapdata/__pycache__/football_stadium.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/mapdata/football_stadium.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/mapdata/__pycache__/the_pad.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/mapdata/the_pad.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/mapdata/__pycache__/happy_thoughts.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/mapdata/happy_thoughts.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/mapdata/__pycache__/monkey_face.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/mapdata/monkey_face.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/mapdata/__pycache__/doom_shroom.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/mapdata/doom_shroom.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/mapdata/__pycache__/zig_zag.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/mapdata/zig_zag.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/mapdata/__pycache__/lake_frigid.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/mapdata/lake_frigid.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/mapdata/__pycache__/tip_top.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/mapdata/tip_top.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/actor/__pycache__/spazfactory.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/actor/spazfactory.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/actor/__pycache__/bomb.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/actor/bomb.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/actor/__pycache__/spazbot.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/actor/spazbot.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/actor/__pycache__/flag.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/actor/flag.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/actor/__pycache__/scoreboard.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/actor/scoreboard.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/actor/__pycache__/popuptext.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/actor/popuptext.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/actor/__pycache__/background.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/actor/background.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/actor/__pycache__/__init__.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/actor/__init__.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/actor/__pycache__/zoomtext.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/actor/zoomtext.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/actor/__pycache__/spaz.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/actor/spaz.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/actor/__pycache__/spazappearance.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/actor/spazappearance.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/actor/__pycache__/controlsguide.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/actor/controlsguide.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/actor/__pycache__/powerupbox.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/actor/powerupbox.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/actor/__pycache__/text.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/actor/text.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/actor/__pycache__/spawner.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/actor/spawner.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/actor/__pycache__/respawnicon.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/actor/respawnicon.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/actor/__pycache__/playerspaz.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/actor/playerspaz.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/actor/__pycache__/tipstext.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/actor/tipstext.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/actor/__pycache__/onscreencountdown.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/actor/onscreencountdown.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/actor/__pycache__/onscreentimer.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/actor/onscreentimer.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/actor/__pycache__/image.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/actor/image.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/data/scripts/bastd/session/__pycache__/__init__.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/data/scripts/bastd/session/__init__.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/zipfile.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/zipfile.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/shutil.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/shutil.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/tempfile.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/tempfile.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/queue.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/queue.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/macpath.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/macpath.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/_pyio.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/_pyio.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/crypt.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/crypt.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/pkgutil.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/pkgutil.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/_dummy_thread.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/_dummy_thread.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/lzma.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/lzma.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/asyncore.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/asyncore.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/__phello__.foo.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/__phello__.foo.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/_sitebuiltins.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/_sitebuiltins.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/copyreg.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/copyreg.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/sndhdr.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/sndhdr.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/rlcompleter.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/rlcompleter.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/gzip.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/gzip.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/ipaddress.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/ipaddress.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/trace.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/trace.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/webbrowser.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/webbrowser.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/nntplib.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/nntplib.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/_compat_pickle.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/_compat_pickle.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/_sysconfigdata_m_linux_.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/_sysconfigdata_m_linux_.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/dis.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/dis.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/formatter.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/formatter.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/bdb.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/bdb.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/zipapp.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/zipapp.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/cmd.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/cmd.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/tty.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/tty.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/tabnanny.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/tabnanny.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/_py_abc.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/_py_abc.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/cProfile.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/cProfile.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/token.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/token.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/textwrap.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/textwrap.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/base64.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/base64.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/_markupbase.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/_markupbase.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/bz2.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/bz2.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/signal.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/signal.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/sre_constants.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/sre_constants.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/cgitb.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/cgitb.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/_threading_local.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/_threading_local.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/pyclbr.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/pyclbr.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/gettext.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/gettext.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/wave.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/wave.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/weakref.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/weakref.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/bisect.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/bisect.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/opcode.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/opcode.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/netrc.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/netrc.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/heapq.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/heapq.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/functools.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/functools.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/modulefinder.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/modulefinder.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/_compression.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/_compression.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/tracemalloc.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/tracemalloc.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/hashlib.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/hashlib.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/cgi.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/cgi.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/codeop.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/codeop.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/fnmatch.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/fnmatch.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/traceback.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/traceback.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/nturl2path.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/nturl2path.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/warnings.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/warnings.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/subprocess.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/subprocess.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/profile.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/profile.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/imghdr.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/imghdr.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/this.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/this.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/filecmp.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/filecmp.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/codecs.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/codecs.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/uu.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/uu.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/_weakrefset.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/_weakrefset.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/io.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/io.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/code.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/code.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/operator.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/operator.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/fileinput.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/fileinput.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/os.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/os.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/difflib.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/difflib.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/pydoc.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/pydoc.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/symbol.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/symbol.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/selectors.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/selectors.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/decimal.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/decimal.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/socketserver.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/socketserver.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/copy.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/copy.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/genericpath.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/genericpath.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/linecache.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/linecache.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/types.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/types.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/mimetypes.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/mimetypes.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/xdrlib.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/xdrlib.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/colorsys.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/colorsys.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/numbers.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/numbers.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/_strptime.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/_strptime.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/dummy_threading.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/dummy_threading.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/contextvars.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/contextvars.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/random.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/random.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/ftplib.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/ftplib.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/chunk.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/chunk.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/optparse.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/optparse.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/pdb.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/pdb.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/threading.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/threading.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/platform.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/platform.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/pstats.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/pstats.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/glob.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/glob.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/quopri.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/quopri.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/symtable.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/symtable.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/pprint.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/pprint.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/calendar.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/calendar.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/inspect.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/inspect.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/poplib.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/poplib.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/binhex.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/binhex.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/plistlib.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/plistlib.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/pickletools.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/pickletools.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/pipes.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/pipes.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/site.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/site.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/telnetlib.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/telnetlib.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/keyword.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/keyword.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/configparser.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/configparser.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/reprlib.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/reprlib.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/secrets.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/secrets.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/shlex.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/shlex.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/posixpath.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/posixpath.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/py_compile.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/py_compile.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/_osx_support.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/_osx_support.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/stat.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/stat.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/compileall.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/compileall.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/csv.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/csv.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/fractions.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/fractions.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/sched.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/sched.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/mailbox.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/mailbox.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/sre_compile.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/sre_compile.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/locale.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/locale.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/ast.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/ast.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/doctest.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/doctest.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/argparse.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/argparse.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/getpass.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/getpass.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/pickle.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/pickle.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/pty.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/pty.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/contextlib.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/contextlib.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/statistics.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/statistics.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/_collections_abc.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/_collections_abc.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/sunau.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/sunau.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/__future__.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/__future__.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/dataclasses.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/dataclasses.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/shelve.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/shelve.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/string.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/string.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/smtplib.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/smtplib.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/getopt.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/getopt.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/antigravity.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/antigravity.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/enum.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/enum.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/timeit.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/timeit.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/hmac.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/hmac.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/tarfile.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/tarfile.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/stringprep.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/stringprep.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/typing.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/typing.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/ssl.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/ssl.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/socket.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/socket.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/datetime.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/datetime.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/sysconfig.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/sysconfig.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/pathlib.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/pathlib.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/_pydecimal.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/_pydecimal.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/ntpath.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/ntpath.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/tokenize.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/tokenize.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/uuid.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/uuid.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/imp.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/imp.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/smtpd.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/smtpd.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/re.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/re.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/mailcap.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/mailcap.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/aifc.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/aifc.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/struct.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/struct.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/asynchat.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/asynchat.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/sre_parse.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/sre_parse.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/abc.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/abc.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/runpy.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/runpy.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/__pycache__/_bootlocale.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/_bootlocale.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/mac_romanian.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/mac_romanian.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/mac_farsi.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/mac_farsi.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/idna.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/idna.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp273.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/cp273.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/punycode.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/punycode.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/raw_unicode_escape.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/raw_unicode_escape.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/utf_8.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/utf_8.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp1252.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/cp1252.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp869.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/cp869.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/iso8859_14.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/iso8859_14.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/iso8859_2.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/iso8859_2.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/mac_arabic.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/mac_arabic.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/mac_croatian.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/mac_croatian.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/big5hkscs.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/big5hkscs.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp1256.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/cp1256.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/iso8859_6.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/iso8859_6.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/iso8859_10.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/iso8859_10.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/iso2022_kr.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/iso2022_kr.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp1140.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/cp1140.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/unicode_internal.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/unicode_internal.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp1125.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/cp1125.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/iso2022_jp_1.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/iso2022_jp_1.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp1257.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/cp1257.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp949.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/cp949.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp858.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/cp858.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/iso8859_7.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/iso8859_7.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/iso8859_11.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/iso8859_11.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/hp_roman8.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/hp_roman8.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/koi8_r.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/koi8_r.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/zlib_codec.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/zlib_codec.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/gbk.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/gbk.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/johab.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/johab.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp1253.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/cp1253.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/iso8859_15.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/iso8859_15.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/iso2022_jp_2004.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/iso2022_jp_2004.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/mac_iceland.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/mac_iceland.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/iso8859_3.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/iso8859_3.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/mac_greek.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/mac_greek.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/rot_13.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/rot_13.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/utf_16_be.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/utf_16_be.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/euc_kr.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/euc_kr.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/mac_centeuro.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/mac_centeuro.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/euc_jisx0213.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/euc_jisx0213.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp863.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/cp863.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/ascii.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/ascii.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/iso8859_8.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/iso8859_8.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp857.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/cp857.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/utf_32_be.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/utf_32_be.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp1258.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/cp1258.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/oem.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/oem.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/mac_latin2.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/mac_latin2.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp775.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/cp775.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/mac_roman.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/mac_roman.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/__init__.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/__init__.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp852.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/cp852.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/shift_jisx0213.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/shift_jisx0213.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp866.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/cp866.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/utf_7.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/utf_7.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/base64_codec.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/base64_codec.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp932.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/cp932.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp720.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/cp720.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp862.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/cp862.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp437.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/cp437.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/palmos.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/palmos.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/iso8859_9.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/iso8859_9.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp856.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/cp856.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/aliases.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/aliases.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/latin_1.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/latin_1.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp875.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/cp875.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp950.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/cp950.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/unicode_escape.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/unicode_escape.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp737.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/cp737.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp865.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/cp865.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/ptcp154.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/ptcp154.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/big5.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/big5.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp424.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/cp424.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp861.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/cp861.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/euc_jp.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/euc_jp.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp855.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/cp855.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/shift_jis.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/shift_jis.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/utf_32_le.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/utf_32_le.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp500.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/cp500.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/undefined.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/undefined.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp860.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/cp860.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/uu_codec.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/uu_codec.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/utf_16_le.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/utf_16_le.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/gb18030.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/gb18030.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp65001.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/cp65001.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp874.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/cp874.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp850.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/cp850.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp864.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/cp864.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/utf_32.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/utf_32.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/koi8_u.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/koi8_u.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp1254.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/cp1254.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/iso2022_jp_2.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/iso2022_jp_2.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/utf_16.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/utf_16.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/iso8859_4.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/iso8859_4.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/euc_jis_2004.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/euc_jis_2004.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/mbcs.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/mbcs.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp1250.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/cp1250.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/gb2312.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/gb2312.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/iso8859_16.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/iso8859_16.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/mac_cyrillic.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/mac_cyrillic.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/hex_codec.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/hex_codec.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/tis_620.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/tis_620.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp037.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/cp037.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp1006.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/cp1006.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp1251.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/cp1251.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/mac_turkish.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/mac_turkish.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/iso2022_jp_ext.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/iso2022_jp_ext.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/iso8859_1.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/iso8859_1.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/hz.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/hz.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/bz2_codec.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/bz2_codec.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/quopri_codec.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/quopri_codec.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/kz1048.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/kz1048.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/utf_8_sig.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/utf_8_sig.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/koi8_t.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/koi8_t.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp1255.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/cp1255.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/iso2022_jp_3.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/iso2022_jp_3.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/shift_jis_2004.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/shift_jis_2004.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/cp1026.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/cp1026.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/charmap.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/charmap.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/iso8859_5.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/iso8859_5.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/iso8859_13.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/iso8859_13.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/encodings/__pycache__/iso2022_jp.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/encodings/iso2022_jp.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/ctypes/__pycache__/_aix.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/ctypes/_aix.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/ctypes/__pycache__/wintypes.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/ctypes/wintypes.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/ctypes/__pycache__/util.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/ctypes/util.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/ctypes/__pycache__/__init__.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/ctypes/__init__.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/ctypes/__pycache__/_endian.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/ctypes/_endian.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/ctypes/macholib/__pycache__/dyld.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/ctypes/macholib/dyld.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/ctypes/macholib/__pycache__/framework.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/ctypes/macholib/framework.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/ctypes/macholib/__pycache__/__init__.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/ctypes/macholib/__init__.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/ctypes/macholib/__pycache__/dylib.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/ctypes/macholib/dylib.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/curses/__pycache__/textpad.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/curses/textpad.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/curses/__pycache__/ascii.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/curses/ascii.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/curses/__pycache__/__init__.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/curses/__init__.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/curses/__pycache__/has_key.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/curses/has_key.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/curses/__pycache__/panel.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/curses/panel.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/urllib/__pycache__/error.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/urllib/error.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/urllib/__pycache__/request.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/urllib/request.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/urllib/__pycache__/__init__.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/urllib/__init__.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/urllib/__pycache__/response.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/urllib/response.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/urllib/__pycache__/robotparser.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/urllib/robotparser.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/urllib/__pycache__/parse.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/urllib/parse.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/html/__pycache__/__init__.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/html/__init__.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/html/__pycache__/parser.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/html/parser.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/html/__pycache__/entities.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/html/entities.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/xml/__pycache__/__init__.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/xml/__init__.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/xml/parsers/__pycache__/expat.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/xml/parsers/expat.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/xml/parsers/__pycache__/__init__.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/xml/parsers/__init__.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/xml/sax/__pycache__/handler.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/xml/sax/handler.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/xml/sax/__pycache__/__init__.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/xml/sax/__init__.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/xml/sax/__pycache__/saxutils.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/xml/sax/saxutils.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/xml/sax/__pycache__/xmlreader.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/xml/sax/xmlreader.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/xml/sax/__pycache__/expatreader.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/xml/sax/expatreader.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/xml/sax/__pycache__/_exceptions.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/xml/sax/_exceptions.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/xml/dom/__pycache__/pulldom.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/xml/dom/pulldom.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/xml/dom/__pycache__/expatbuilder.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/xml/dom/expatbuilder.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/xml/dom/__pycache__/domreg.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/xml/dom/domreg.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/xml/dom/__pycache__/minicompat.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/xml/dom/minicompat.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/xml/dom/__pycache__/__init__.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/xml/dom/__init__.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/xml/dom/__pycache__/NodeFilter.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/xml/dom/NodeFilter.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/xml/dom/__pycache__/xmlbuilder.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/xml/dom/xmlbuilder.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/xml/dom/__pycache__/minidom.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/xml/dom/minidom.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/xml/etree/__pycache__/ElementPath.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/xml/etree/ElementPath.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/xml/etree/__pycache__/cElementTree.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/xml/etree/cElementTree.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/xml/etree/__pycache__/__init__.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/xml/etree/__init__.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/xml/etree/__pycache__/ElementInclude.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/xml/etree/ElementInclude.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/xml/etree/__pycache__/ElementTree.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/xml/etree/ElementTree.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/json/__pycache__/decoder.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/json/decoder.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/json/__pycache__/scanner.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/json/scanner.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/json/__pycache__/__init__.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/json/__init__.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/json/__pycache__/encoder.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/json/encoder.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/json/__pycache__/tool.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/json/tool.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/http/__pycache__/cookies.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/http/cookies.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/http/__pycache__/server.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/http/server.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/http/__pycache__/client.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/http/client.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/http/__pycache__/__init__.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/http/__init__.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/http/__pycache__/cookiejar.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/http/cookiejar.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/sqlite3/__pycache__/__init__.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/sqlite3/__init__.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/sqlite3/__pycache__/dump.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/sqlite3/dump.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/sqlite3/__pycache__/dbapi2.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/sqlite3/dbapi2.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/concurrent/__pycache__/__init__.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/concurrent/__init__.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/concurrent/futures/__pycache__/_base.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/concurrent/futures/_base.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/concurrent/futures/__pycache__/thread.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/concurrent/futures/thread.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/concurrent/futures/__pycache__/__init__.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/concurrent/futures/__init__.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/concurrent/futures/__pycache__/process.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/concurrent/futures/process.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/importlib/__pycache__/util.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/importlib/util.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/importlib/__pycache__/_bootstrap.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/importlib/_bootstrap.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/importlib/__pycache__/__init__.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/importlib/__init__.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/importlib/__pycache__/_bootstrap_external.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/importlib/_bootstrap_external.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/importlib/__pycache__/resources.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/importlib/resources.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/importlib/__pycache__/machinery.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/importlib/machinery.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/importlib/__pycache__/abc.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/importlib/abc.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/xmlrpc/__pycache__/server.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/xmlrpc/server.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/xmlrpc/__pycache__/client.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/xmlrpc/client.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/xmlrpc/__pycache__/__init__.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/xmlrpc/__init__.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/collections/__pycache__/__init__.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/collections/__init__.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/collections/__pycache__/abc.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/collections/abc.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/asyncio/__pycache__/queues.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/asyncio/queues.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/asyncio/__pycache__/streams.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/asyncio/streams.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/asyncio/__pycache__/tasks.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/asyncio/tasks.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/asyncio/__pycache__/selector_events.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/asyncio/selector_events.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/asyncio/__pycache__/log.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/asyncio/log.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/asyncio/__pycache__/protocols.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/asyncio/protocols.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/asyncio/__pycache__/events.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/asyncio/events.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/asyncio/__pycache__/base_events.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/asyncio/base_events.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/asyncio/__pycache__/subprocess.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/asyncio/subprocess.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/asyncio/__pycache__/constants.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/asyncio/constants.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/asyncio/__pycache__/proactor_events.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/asyncio/proactor_events.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/asyncio/__pycache__/format_helpers.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/asyncio/format_helpers.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/asyncio/__pycache__/locks.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/asyncio/locks.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/asyncio/__pycache__/__init__.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/asyncio/__init__.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/asyncio/__pycache__/futures.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/asyncio/futures.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/asyncio/__pycache__/sslproto.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/asyncio/sslproto.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/asyncio/__pycache__/base_subprocess.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/asyncio/base_subprocess.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/asyncio/__pycache__/windows_utils.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/asyncio/windows_utils.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/asyncio/__pycache__/runners.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/asyncio/runners.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/asyncio/__pycache__/transports.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/asyncio/transports.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/asyncio/__pycache__/base_tasks.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/asyncio/base_tasks.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/asyncio/__pycache__/coroutines.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/asyncio/coroutines.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/asyncio/__pycache__/windows_events.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/asyncio/windows_events.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/asyncio/__pycache__/base_futures.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/asyncio/base_futures.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/asyncio/__pycache__/unix_events.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/asyncio/unix_events.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/logging/__pycache__/config.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/logging/config.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/logging/__pycache__/handlers.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/logging/handlers.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/logging/__pycache__/__init__.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/logging/__init__.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/email/__pycache__/contentmanager.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/email/contentmanager.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/email/__pycache__/_policybase.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/email/_policybase.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/email/__pycache__/header.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/email/header.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/email/__pycache__/_encoded_words.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/email/_encoded_words.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/email/__pycache__/_header_value_parser.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/email/_header_value_parser.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/email/__pycache__/policy.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/email/policy.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/email/__pycache__/__init__.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/email/__init__.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/email/__pycache__/message.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/email/message.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/email/__pycache__/encoders.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/email/encoders.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/email/__pycache__/parser.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/email/parser.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/email/__pycache__/generator.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/email/generator.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/email/__pycache__/utils.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/email/utils.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/email/__pycache__/charset.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/email/charset.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/email/__pycache__/iterators.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/email/iterators.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/email/__pycache__/quoprimime.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/email/quoprimime.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/email/__pycache__/errors.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/email/errors.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/email/__pycache__/feedparser.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/email/feedparser.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/email/__pycache__/_parseaddr.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/email/_parseaddr.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/email/__pycache__/base64mime.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/email/base64mime.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/email/__pycache__/headerregistry.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/email/headerregistry.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/email/mime/__pycache__/multipart.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/email/mime/multipart.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/email/mime/__pycache__/__init__.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/email/mime/__init__.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/email/mime/__pycache__/message.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/email/mime/message.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/email/mime/__pycache__/application.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/email/mime/application.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/email/mime/__pycache__/nonmultipart.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/email/mime/nonmultipart.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/email/mime/__pycache__/text.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/email/mime/text.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/email/mime/__pycache__/audio.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/email/mime/audio.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/email/mime/__pycache__/image.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/email/mime/image.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-android/email/mime/__pycache__/base.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-android/email/mime/base.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/zipfile.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/zipfile.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/shutil.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/shutil.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/tempfile.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/tempfile.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/queue.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/queue.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/macpath.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/macpath.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/_sysconfigdata_m_darwin_darwin.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/_sysconfigdata_m_darwin_darwin.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/_pyio.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/_pyio.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/crypt.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/crypt.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/pkgutil.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/pkgutil.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/_dummy_thread.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/_dummy_thread.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/lzma.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/lzma.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/asyncore.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/asyncore.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/__phello__.foo.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/__phello__.foo.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/_sitebuiltins.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/_sitebuiltins.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/copyreg.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/copyreg.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/sndhdr.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/sndhdr.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/rlcompleter.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/rlcompleter.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/gzip.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/gzip.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/ipaddress.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/ipaddress.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/trace.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/trace.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/webbrowser.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/webbrowser.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/nntplib.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/nntplib.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/_compat_pickle.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/_compat_pickle.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/dis.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/dis.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/formatter.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/formatter.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/bdb.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/bdb.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/zipapp.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/zipapp.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/cmd.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/cmd.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/tty.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/tty.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/tabnanny.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/tabnanny.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/_py_abc.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/_py_abc.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/cProfile.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/cProfile.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/token.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/token.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/textwrap.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/textwrap.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/base64.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/base64.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/_markupbase.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/_markupbase.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/bz2.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/bz2.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/signal.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/signal.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/sre_constants.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/sre_constants.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/cgitb.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/cgitb.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/_threading_local.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/_threading_local.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/pyclbr.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/pyclbr.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/gettext.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/gettext.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/wave.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/wave.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/weakref.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/weakref.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/bisect.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/bisect.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/opcode.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/opcode.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/netrc.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/netrc.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/heapq.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/heapq.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/functools.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/functools.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/modulefinder.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/modulefinder.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/_compression.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/_compression.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/tracemalloc.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/tracemalloc.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/hashlib.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/hashlib.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/cgi.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/cgi.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/codeop.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/codeop.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/fnmatch.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/fnmatch.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/traceback.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/traceback.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/nturl2path.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/nturl2path.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/warnings.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/warnings.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/subprocess.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/subprocess.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/profile.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/profile.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/imghdr.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/imghdr.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/this.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/this.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/filecmp.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/filecmp.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/codecs.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/codecs.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/uu.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/uu.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/_weakrefset.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/_weakrefset.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/io.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/io.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/code.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/code.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/operator.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/operator.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/fileinput.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/fileinput.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/os.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/os.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/difflib.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/difflib.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/pydoc.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/pydoc.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/symbol.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/symbol.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/selectors.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/selectors.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/decimal.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/decimal.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/socketserver.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/socketserver.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/copy.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/copy.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/genericpath.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/genericpath.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/linecache.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/linecache.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/types.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/types.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/mimetypes.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/mimetypes.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/xdrlib.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/xdrlib.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/colorsys.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/colorsys.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/numbers.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/numbers.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/_strptime.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/_strptime.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/dummy_threading.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/dummy_threading.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/contextvars.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/contextvars.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/random.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/random.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/ftplib.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/ftplib.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/chunk.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/chunk.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/optparse.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/optparse.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/pdb.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/pdb.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/threading.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/threading.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/platform.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/platform.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/pstats.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/pstats.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/glob.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/glob.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/quopri.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/quopri.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/symtable.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/symtable.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/pprint.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/pprint.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/calendar.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/calendar.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/inspect.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/inspect.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/poplib.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/poplib.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/binhex.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/binhex.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/plistlib.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/plistlib.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/pickletools.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/pickletools.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/pipes.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/pipes.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/site.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/site.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/telnetlib.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/telnetlib.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/keyword.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/keyword.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/configparser.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/configparser.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/reprlib.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/reprlib.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/secrets.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/secrets.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/shlex.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/shlex.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/posixpath.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/posixpath.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/py_compile.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/py_compile.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/_osx_support.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/_osx_support.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/stat.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/stat.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/compileall.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/compileall.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/csv.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/csv.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/fractions.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/fractions.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/sched.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/sched.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/mailbox.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/mailbox.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/sre_compile.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/sre_compile.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/locale.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/locale.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/ast.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/ast.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/doctest.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/doctest.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/argparse.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/argparse.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/getpass.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/getpass.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/pickle.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/pickle.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/pty.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/pty.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/contextlib.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/contextlib.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/statistics.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/statistics.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/_collections_abc.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/_collections_abc.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/sunau.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/sunau.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/__future__.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/__future__.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/dataclasses.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/dataclasses.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/shelve.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/shelve.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/string.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/string.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/smtplib.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/smtplib.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/getopt.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/getopt.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/antigravity.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/antigravity.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/enum.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/enum.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/timeit.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/timeit.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/hmac.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/hmac.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/tarfile.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/tarfile.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/stringprep.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/stringprep.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/typing.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/typing.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/ssl.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/ssl.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/socket.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/socket.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/datetime.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/datetime.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/sysconfig.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/sysconfig.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/pathlib.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/pathlib.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/_pydecimal.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/_pydecimal.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/ntpath.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/ntpath.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/tokenize.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/tokenize.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/uuid.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/uuid.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/imp.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/imp.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/smtpd.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/smtpd.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/re.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/re.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/mailcap.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/mailcap.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/aifc.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/aifc.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/struct.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/struct.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/asynchat.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/asynchat.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/sre_parse.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/sre_parse.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/abc.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/abc.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/runpy.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/runpy.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/__pycache__/_bootlocale.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/_bootlocale.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/mac_romanian.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/mac_romanian.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/mac_farsi.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/mac_farsi.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/idna.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/idna.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp273.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp273.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/punycode.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/punycode.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/raw_unicode_escape.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/raw_unicode_escape.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/utf_8.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/utf_8.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp1252.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp1252.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp869.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp869.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/iso8859_14.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/iso8859_14.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/iso8859_2.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/iso8859_2.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/mac_arabic.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/mac_arabic.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/mac_croatian.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/mac_croatian.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/big5hkscs.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/big5hkscs.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp1256.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp1256.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/iso8859_6.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/iso8859_6.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/iso8859_10.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/iso8859_10.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/iso2022_kr.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/iso2022_kr.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp1140.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp1140.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/unicode_internal.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/unicode_internal.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp1125.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp1125.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/iso2022_jp_1.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/iso2022_jp_1.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp1257.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp1257.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp949.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp949.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp858.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp858.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/iso8859_7.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/iso8859_7.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/iso8859_11.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/iso8859_11.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/hp_roman8.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/hp_roman8.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/koi8_r.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/koi8_r.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/zlib_codec.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/zlib_codec.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/gbk.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/gbk.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/johab.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/johab.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp1253.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp1253.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/iso8859_15.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/iso8859_15.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/iso2022_jp_2004.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/iso2022_jp_2004.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/mac_iceland.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/mac_iceland.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/iso8859_3.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/iso8859_3.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/mac_greek.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/mac_greek.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/rot_13.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/rot_13.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/utf_16_be.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/utf_16_be.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/euc_kr.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/euc_kr.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/mac_centeuro.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/mac_centeuro.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/euc_jisx0213.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/euc_jisx0213.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp863.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp863.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/ascii.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/ascii.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/iso8859_8.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/iso8859_8.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp857.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp857.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/utf_32_be.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/utf_32_be.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp1258.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp1258.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/oem.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/oem.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/mac_latin2.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/mac_latin2.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp775.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp775.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/mac_roman.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/mac_roman.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/__init__.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/__init__.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp852.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp852.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/shift_jisx0213.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/shift_jisx0213.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp866.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp866.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/utf_7.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/utf_7.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/base64_codec.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/base64_codec.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp932.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp932.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp720.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp720.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp862.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp862.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp437.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp437.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/palmos.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/palmos.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/iso8859_9.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/iso8859_9.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp856.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp856.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/aliases.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/aliases.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/latin_1.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/latin_1.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp875.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp875.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp950.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp950.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/unicode_escape.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/unicode_escape.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp737.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp737.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp865.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp865.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/ptcp154.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/ptcp154.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/big5.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/big5.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp424.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp424.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp861.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp861.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/euc_jp.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/euc_jp.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp855.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp855.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/shift_jis.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/shift_jis.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/utf_32_le.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/utf_32_le.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp500.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp500.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/undefined.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/undefined.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp860.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp860.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/uu_codec.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/uu_codec.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/utf_16_le.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/utf_16_le.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/gb18030.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/gb18030.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp65001.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp65001.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp874.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp874.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp850.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp850.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp864.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp864.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/utf_32.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/utf_32.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/koi8_u.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/koi8_u.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp1254.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp1254.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/iso2022_jp_2.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/iso2022_jp_2.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/utf_16.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/utf_16.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/iso8859_4.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/iso8859_4.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/euc_jis_2004.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/euc_jis_2004.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/mbcs.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/mbcs.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp1250.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp1250.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/gb2312.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/gb2312.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/iso8859_16.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/iso8859_16.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/mac_cyrillic.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/mac_cyrillic.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/hex_codec.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/hex_codec.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/tis_620.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/tis_620.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp037.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp037.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp1006.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp1006.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp1251.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp1251.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/mac_turkish.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/mac_turkish.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/iso2022_jp_ext.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/iso2022_jp_ext.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/iso8859_1.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/iso8859_1.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/hz.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/hz.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/bz2_codec.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/bz2_codec.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/quopri_codec.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/quopri_codec.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/kz1048.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/kz1048.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/utf_8_sig.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/utf_8_sig.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/koi8_t.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/koi8_t.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp1255.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp1255.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/iso2022_jp_3.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/iso2022_jp_3.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/shift_jis_2004.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/shift_jis_2004.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/cp1026.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/cp1026.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/charmap.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/charmap.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/iso8859_5.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/iso8859_5.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/iso8859_13.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/iso8859_13.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/encodings/__pycache__/iso2022_jp.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/encodings/iso2022_jp.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/ctypes/__pycache__/_aix.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/ctypes/_aix.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/ctypes/__pycache__/wintypes.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/ctypes/wintypes.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/ctypes/__pycache__/util.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/ctypes/util.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/ctypes/__pycache__/__init__.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/ctypes/__init__.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/ctypes/__pycache__/_endian.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/ctypes/_endian.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/ctypes/macholib/__pycache__/dyld.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/ctypes/macholib/dyld.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/ctypes/macholib/__pycache__/framework.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/ctypes/macholib/framework.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/ctypes/macholib/__pycache__/__init__.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/ctypes/macholib/__init__.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/ctypes/macholib/__pycache__/dylib.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/ctypes/macholib/dylib.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/curses/__pycache__/textpad.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/curses/textpad.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/curses/__pycache__/ascii.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/curses/ascii.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/curses/__pycache__/__init__.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/curses/__init__.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/curses/__pycache__/has_key.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/curses/has_key.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/curses/__pycache__/panel.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/curses/panel.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/urllib/__pycache__/error.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/urllib/error.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/urllib/__pycache__/request.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/urllib/request.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/urllib/__pycache__/__init__.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/urllib/__init__.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/urllib/__pycache__/response.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/urllib/response.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/urllib/__pycache__/robotparser.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/urllib/robotparser.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/urllib/__pycache__/parse.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/urllib/parse.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/html/__pycache__/__init__.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/html/__init__.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/html/__pycache__/parser.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/html/parser.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/html/__pycache__/entities.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/html/entities.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/xml/__pycache__/__init__.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/xml/__init__.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/xml/parsers/__pycache__/expat.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/xml/parsers/expat.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/xml/parsers/__pycache__/__init__.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/xml/parsers/__init__.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/xml/sax/__pycache__/handler.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/xml/sax/handler.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/xml/sax/__pycache__/__init__.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/xml/sax/__init__.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/xml/sax/__pycache__/saxutils.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/xml/sax/saxutils.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/xml/sax/__pycache__/xmlreader.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/xml/sax/xmlreader.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/xml/sax/__pycache__/expatreader.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/xml/sax/expatreader.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/xml/sax/__pycache__/_exceptions.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/xml/sax/_exceptions.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/xml/dom/__pycache__/pulldom.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/xml/dom/pulldom.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/xml/dom/__pycache__/expatbuilder.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/xml/dom/expatbuilder.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/xml/dom/__pycache__/domreg.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/xml/dom/domreg.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/xml/dom/__pycache__/minicompat.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/xml/dom/minicompat.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/xml/dom/__pycache__/__init__.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/xml/dom/__init__.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/xml/dom/__pycache__/NodeFilter.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/xml/dom/NodeFilter.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/xml/dom/__pycache__/xmlbuilder.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/xml/dom/xmlbuilder.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/xml/dom/__pycache__/minidom.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/xml/dom/minidom.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/xml/etree/__pycache__/ElementPath.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/xml/etree/ElementPath.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/xml/etree/__pycache__/cElementTree.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/xml/etree/cElementTree.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/xml/etree/__pycache__/__init__.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/xml/etree/__init__.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/xml/etree/__pycache__/ElementInclude.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/xml/etree/ElementInclude.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/xml/etree/__pycache__/ElementTree.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/xml/etree/ElementTree.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/json/__pycache__/decoder.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/json/decoder.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/json/__pycache__/scanner.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/json/scanner.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/json/__pycache__/__init__.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/json/__init__.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/json/__pycache__/encoder.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/json/encoder.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/json/__pycache__/tool.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/json/tool.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/http/__pycache__/cookies.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/http/cookies.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/http/__pycache__/server.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/http/server.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/http/__pycache__/client.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/http/client.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/http/__pycache__/__init__.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/http/__init__.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/http/__pycache__/cookiejar.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/http/cookiejar.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/sqlite3/__pycache__/__init__.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/sqlite3/__init__.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/sqlite3/__pycache__/dump.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/sqlite3/dump.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/sqlite3/__pycache__/dbapi2.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/sqlite3/dbapi2.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/concurrent/__pycache__/__init__.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/concurrent/__init__.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/concurrent/futures/__pycache__/_base.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/concurrent/futures/_base.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/concurrent/futures/__pycache__/thread.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/concurrent/futures/thread.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/concurrent/futures/__pycache__/__init__.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/concurrent/futures/__init__.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/concurrent/futures/__pycache__/process.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/concurrent/futures/process.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/importlib/__pycache__/util.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/importlib/util.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/importlib/__pycache__/_bootstrap.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/importlib/_bootstrap.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/importlib/__pycache__/__init__.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/importlib/__init__.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/importlib/__pycache__/_bootstrap_external.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/importlib/_bootstrap_external.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/importlib/__pycache__/resources.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/importlib/resources.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/importlib/__pycache__/machinery.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/importlib/machinery.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/importlib/__pycache__/abc.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/importlib/abc.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/xmlrpc/__pycache__/server.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/xmlrpc/server.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/xmlrpc/__pycache__/client.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/xmlrpc/client.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/xmlrpc/__pycache__/__init__.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/xmlrpc/__init__.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/collections/__pycache__/__init__.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/collections/__init__.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/collections/__pycache__/abc.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/collections/abc.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/asyncio/__pycache__/queues.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/asyncio/queues.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/asyncio/__pycache__/streams.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/asyncio/streams.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/asyncio/__pycache__/tasks.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/asyncio/tasks.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/asyncio/__pycache__/selector_events.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/asyncio/selector_events.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/asyncio/__pycache__/log.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/asyncio/log.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/asyncio/__pycache__/protocols.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/asyncio/protocols.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/asyncio/__pycache__/events.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/asyncio/events.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/asyncio/__pycache__/base_events.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/asyncio/base_events.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/asyncio/__pycache__/subprocess.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/asyncio/subprocess.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/asyncio/__pycache__/constants.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/asyncio/constants.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/asyncio/__pycache__/proactor_events.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/asyncio/proactor_events.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/asyncio/__pycache__/format_helpers.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/asyncio/format_helpers.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/asyncio/__pycache__/locks.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/asyncio/locks.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/asyncio/__pycache__/__init__.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/asyncio/__init__.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/asyncio/__pycache__/futures.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/asyncio/futures.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/asyncio/__pycache__/sslproto.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/asyncio/sslproto.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/asyncio/__pycache__/base_subprocess.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/asyncio/base_subprocess.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/asyncio/__pycache__/windows_utils.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/asyncio/windows_utils.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/asyncio/__pycache__/runners.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/asyncio/runners.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/asyncio/__pycache__/transports.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/asyncio/transports.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/asyncio/__pycache__/base_tasks.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/asyncio/base_tasks.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/asyncio/__pycache__/coroutines.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/asyncio/coroutines.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/asyncio/__pycache__/windows_events.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/asyncio/windows_events.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/asyncio/__pycache__/base_futures.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/asyncio/base_futures.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/asyncio/__pycache__/unix_events.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/asyncio/unix_events.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/logging/__pycache__/config.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/logging/config.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/logging/__pycache__/handlers.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/logging/handlers.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/logging/__pycache__/__init__.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/logging/__init__.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/email/__pycache__/contentmanager.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/email/contentmanager.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/email/__pycache__/_policybase.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/email/_policybase.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/email/__pycache__/header.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/email/header.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/email/__pycache__/_encoded_words.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/email/_encoded_words.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/email/__pycache__/_header_value_parser.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/email/_header_value_parser.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/email/__pycache__/policy.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/email/policy.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/email/__pycache__/__init__.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/email/__init__.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/email/__pycache__/message.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/email/message.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/email/__pycache__/encoders.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/email/encoders.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/email/__pycache__/parser.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/email/parser.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/email/__pycache__/generator.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/email/generator.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/email/__pycache__/utils.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/email/utils.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/email/__pycache__/charset.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/email/charset.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/email/__pycache__/iterators.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/email/iterators.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/email/__pycache__/quoprimime.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/email/quoprimime.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/email/__pycache__/errors.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/email/errors.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/email/__pycache__/feedparser.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/email/feedparser.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/email/__pycache__/_parseaddr.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/email/_parseaddr.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/email/__pycache__/base64mime.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/email/base64mime.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/email/__pycache__/headerregistry.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/email/headerregistry.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/email/mime/__pycache__/multipart.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/email/mime/multipart.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/email/mime/__pycache__/__init__.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/email/mime/__init__.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/email/mime/__pycache__/message.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/email/mime/message.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/email/mime/__pycache__/application.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/email/mime/application.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/email/mime/__pycache__/nonmultipart.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/email/mime/nonmultipart.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/email/mime/__pycache__/text.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/email/mime/text.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/email/mime/__pycache__/audio.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/email/mime/audio.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/email/mime/__pycache__/image.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/email/mime/image.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-apple/email/mime/__pycache__/base.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-apple/email/mime/base.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@

${ASSET_BUILD_DIR}/pylib-site-packages/__pycache__/typing_extensions.cpython-37.opt-1.pyc: \
      ${ASSET_BUILD_DIR}/pylib-site-packages/typing_extensions.py
	@echo Compiling script: $(notdir $^)
	@rm -rf $@ && ${TOOLS_DIR}/compile_python_files $^ && chmod 444 $@


COB_TARGETS = \
  ${ASSET_BUILD_DIR}/data/models/zigZagLevelBumper.cob \
  ${ASSET_BUILD_DIR}/data/models/rampageBumper.cob \
  ${ASSET_BUILD_DIR}/data/models/bigGBumper.cob \
  ${ASSET_BUILD_DIR}/data/models/roundaboutLevelCollide.cob \
  ${ASSET_BUILD_DIR}/data/models/cragCastleLevelBumper.cob \
  ${ASSET_BUILD_DIR}/data/models/lakeFrigidCollide.cob \
  ${ASSET_BUILD_DIR}/data/models/stepRightUpLevelCollide.cob \
  ${ASSET_BUILD_DIR}/data/models/courtyardPlayerWall.cob \
  ${ASSET_BUILD_DIR}/data/models/rampageLevelCollide.cob \
  ${ASSET_BUILD_DIR}/data/models/monkeyFaceLevelCollide.cob \
  ${ASSET_BUILD_DIR}/data/models/courtyardLevelCollide.cob \
  ${ASSET_BUILD_DIR}/data/models/hockeyStadiumCollide.cob \
  ${ASSET_BUILD_DIR}/data/models/towerDLevelCollide.cob \
  ${ASSET_BUILD_DIR}/data/models/tipTopLevelCollide.cob \
  ${ASSET_BUILD_DIR}/data/models/monkeyFaceLevelBumper.cob \
  ${ASSET_BUILD_DIR}/data/models/zigZagLevelCollide.cob \
  ${ASSET_BUILD_DIR}/data/models/bridgitLevelRailingCollide.cob \
  ${ASSET_BUILD_DIR}/data/models/thePadLevelBumper.cob \
  ${ASSET_BUILD_DIR}/data/models/natureBackgroundCollide.cob \
  ${ASSET_BUILD_DIR}/data/models/doomShroomLevelCollide.cob \
  ${ASSET_BUILD_DIR}/data/models/footballStadiumCollide.cob \
  ${ASSET_BUILD_DIR}/data/models/doomShroomStemCollide.cob \
  ${ASSET_BUILD_DIR}/data/models/bridgitLevelCollide.cob \
  ${ASSET_BUILD_DIR}/data/models/alwaysLandLevelCollide.cob \
  ${ASSET_BUILD_DIR}/data/models/cragCastleLevelCollide.cob \
  ${ASSET_BUILD_DIR}/data/models/roundaboutLevelBumper.cob \
  ${ASSET_BUILD_DIR}/data/models/towerDPlayerWall.cob \
  ${ASSET_BUILD_DIR}/data/models/tipTopLevelBumper.cob \
  ${ASSET_BUILD_DIR}/data/models/thePadLevelCollide.cob \
  ${ASSET_BUILD_DIR}/data/models/bigGCollide.cob


BOB_TARGETS = \
  ${ASSET_BUILD_DIR}/data/models/wrestlerToes.bob \
  ${ASSET_BUILD_DIR}/data/models/melTorso.bob \
  ${ASSET_BUILD_DIR}/data/models/gladiatorHead.bob \
  ${ASSET_BUILD_DIR}/data/models/image16x1.bob \
  ${ASSET_BUILD_DIR}/data/models/actionButtonBottom.bob \
  ${ASSET_BUILD_DIR}/data/models/santaUpperLeg.bob \
  ${ASSET_BUILD_DIR}/data/models/thePadBGSmall.bob \
  ${ASSET_BUILD_DIR}/data/models/cowboyForeArm.bob \
  ${ASSET_BUILD_DIR}/data/models/image1x1.bob \
  ${ASSET_BUILD_DIR}/data/models/trees.bob \
  ${ASSET_BUILD_DIR}/data/models/plasticEyesTransparent.bob \
  ${ASSET_BUILD_DIR}/data/models/currencyPlusButton.bob \
  ${ASSET_BUILD_DIR}/data/models/scrollBarThumbOpaque.bob \
  ${ASSET_BUILD_DIR}/data/models/cyborgUpperArm.bob \
  ${ASSET_BUILD_DIR}/data/models/jumpsuitTorso.bob \
  ${ASSET_BUILD_DIR}/data/models/jumpsuitToes.bob \
  ${ASSET_BUILD_DIR}/data/models/natureBackground.bob \
  ${ASSET_BUILD_DIR}/data/models/operaSingerPelvis.bob \
  ${ASSET_BUILD_DIR}/data/models/oldLadyUpperArm.bob \
  ${ASSET_BUILD_DIR}/data/models/hairTuft1.bob \
  ${ASSET_BUILD_DIR}/data/models/neoSpazUpperLeg.bob \
  ${ASSET_BUILD_DIR}/data/models/overlayGuide.bob \
  ${ASSET_BUILD_DIR}/data/models/gladiatorUpperLeg.bob \
  ${ASSET_BUILD_DIR}/data/models/alienTorso.bob \
  ${ASSET_BUILD_DIR}/data/models/zoeTorso.bob \
  ${ASSET_BUILD_DIR}/data/models/operaSingerForeArm.bob \
  ${ASSET_BUILD_DIR}/data/models/buttonTabOpaque.bob \
  ${ASSET_BUILD_DIR}/data/models/wizardToes.bob \
  ${ASSET_BUILD_DIR}/data/models/witchTorso.bob \
  ${ASSET_BUILD_DIR}/data/models/shrapnelBoard.bob \
  ${ASSET_BUILD_DIR}/data/models/puck.bob \
  ${ASSET_BUILD_DIR}/data/models/jumpsuitLowerLeg.bob \
  ${ASSET_BUILD_DIR}/data/models/zoeHand.bob \
  ${ASSET_BUILD_DIR}/data/models/witchLowerLeg.bob \
  ${ASSET_BUILD_DIR}/data/models/achievementOutline.bob \
  ${ASSET_BUILD_DIR}/data/models/bonesToes.bob \
  ${ASSET_BUILD_DIR}/data/models/bearToes.bob \
  ${ASSET_BUILD_DIR}/data/models/buttonBackOpaque.bob \
  ${ASSET_BUILD_DIR}/data/models/vrOverlay.bob \
  ${ASSET_BUILD_DIR}/data/models/playerLineup2Transparent.bob \
  ${ASSET_BUILD_DIR}/data/models/kronkToes.bob \
  ${ASSET_BUILD_DIR}/data/models/alwaysLandLevel.bob \
  ${ASSET_BUILD_DIR}/data/models/oldLadyToes.bob \
  ${ASSET_BUILD_DIR}/data/models/superheroHand.bob \
  ${ASSET_BUILD_DIR}/data/models/toolbarBacking.bob \
  ${ASSET_BUILD_DIR}/data/models/bomb.bob \
  ${ASSET_BUILD_DIR}/data/models/currencyMeter.bob \
  ${ASSET_BUILD_DIR}/data/models/cowboyUpperLeg.bob \
  ${ASSET_BUILD_DIR}/data/models/ninjaLowerLeg.bob \
  ${ASSET_BUILD_DIR}/data/models/kronkForeArm.bob \
  ${ASSET_BUILD_DIR}/data/models/ninjaHand.bob \
  ${ASSET_BUILD_DIR}/data/models/windowBGBlotch.bob \
  ${ASSET_BUILD_DIR}/data/models/kronkPelvis.bob \
  ${ASSET_BUILD_DIR}/data/models/agentTorso.bob \
  ${ASSET_BUILD_DIR}/data/models/penguinLowerLeg.bob \
  ${ASSET_BUILD_DIR}/data/models/scrollBarThumbShortOpaque.bob \
  ${ASSET_BUILD_DIR}/data/models/bunnyLowerLeg.bob \
  ${ASSET_BUILD_DIR}/data/models/neoSpazPelvis.bob \
  ${ASSET_BUILD_DIR}/data/models/scrollWidgetShort.bob \
  ${ASSET_BUILD_DIR}/data/models/operaSingerHand.bob \
  ${ASSET_BUILD_DIR}/data/models/image1x1FullScreen.bob \
  ${ASSET_BUILD_DIR}/data/models/ninjaTorso.bob \
  ${ASSET_BUILD_DIR}/data/models/assassinHead.bob \
  ${ASSET_BUILD_DIR}/data/models/jackHead.bob \
  ${ASSET_BUILD_DIR}/data/models/level_select_button_transparent.bob \
  ${ASSET_BUILD_DIR}/data/models/rampageLevelBottom.bob \
  ${ASSET_BUILD_DIR}/data/models/pixieHead.bob \
  ${ASSET_BUILD_DIR}/data/models/toolbarBackingTransparent.bob \
  ${ASSET_BUILD_DIR}/data/models/aliUpperLeg.bob \
  ${ASSET_BUILD_DIR}/data/models/alienToes.bob \
  ${ASSET_BUILD_DIR}/data/models/cyborgLowerLeg.bob \
  ${ASSET_BUILD_DIR}/data/models/runningShoes.bob \
  ${ASSET_BUILD_DIR}/data/models/oldLadyLowerLeg.bob \
  ${ASSET_BUILD_DIR}/data/models/scorch.bob \
  ${ASSET_BUILD_DIR}/data/models/cowboyToes.bob \
  ${ASSET_BUILD_DIR}/data/models/ninjaPelvis.bob \
  ${ASSET_BUILD_DIR}/data/models/wrestlerForeArm.bob \
  ${ASSET_BUILD_DIR}/data/models/heartOpaque.bob \
  ${ASSET_BUILD_DIR}/data/models/level_select_button_opaque.bob \
  ${ASSET_BUILD_DIR}/data/models/frostyUpperLeg.bob \
  ${ASSET_BUILD_DIR}/data/models/bonesForeArm.bob \
  ${ASSET_BUILD_DIR}/data/models/frostyHead.bob \
  ${ASSET_BUILD_DIR}/data/models/witchHand.bob \
  ${ASSET_BUILD_DIR}/data/models/cyborgToes.bob \
  ${ASSET_BUILD_DIR}/data/models/wizardTorso.bob \
  ${ASSET_BUILD_DIR}/data/models/shield.bob \
  ${ASSET_BUILD_DIR}/data/models/image4x1.bob \
  ${ASSET_BUILD_DIR}/data/models/frostyForeArm.bob \
  ${ASSET_BUILD_DIR}/data/models/bunnyUpperArm.bob \
  ${ASSET_BUILD_DIR}/data/models/bridgitLevelTop.bob \
  ${ASSET_BUILD_DIR}/data/models/agentHand.bob \
  ${ASSET_BUILD_DIR}/data/models/flagStand.bob \
  ${ASSET_BUILD_DIR}/data/models/cragCastleLevelBottom.bob \
  ${ASSET_BUILD_DIR}/data/models/doomShroomBG.bob \
  ${ASSET_BUILD_DIR}/data/models/melHead.bob \
  ${ASSET_BUILD_DIR}/data/models/assassinTorso.bob \
  ${ASSET_BUILD_DIR}/data/models/image1x1VRFullScreen.bob \
  ${ASSET_BUILD_DIR}/data/models/witchForeArm.bob \
  ${ASSET_BUILD_DIR}/data/models/penguinUpperArm.bob \
  ${ASSET_BUILD_DIR}/data/models/aliForeArm.bob \
  ${ASSET_BUILD_DIR}/data/models/robotHand.bob \
  ${ASSET_BUILD_DIR}/data/models/lakeFrigidVRFill.bob \
  ${ASSET_BUILD_DIR}/data/models/oldLadyPelvis.bob \
  ${ASSET_BUILD_DIR}/data/models/bunnyHand.bob \
  ${ASSET_BUILD_DIR}/data/models/wing.bob \
  ${ASSET_BUILD_DIR}/data/models/ninjaUpperArm.bob \
  ${ASSET_BUILD_DIR}/data/models/bonesPelvis.bob \
  ${ASSET_BUILD_DIR}/data/models/santaHand.bob \
  ${ASSET_BUILD_DIR}/data/models/neoSpazTorso.bob \
  ${ASSET_BUILD_DIR}/data/models/witchUpperArm.bob \
  ${ASSET_BUILD_DIR}/data/models/superheroForeArm.bob \
  ${ASSET_BUILD_DIR}/data/models/jumpsuitUpperArm.bob \
  ${ASSET_BUILD_DIR}/data/models/hairTuft1b.bob \
  ${ASSET_BUILD_DIR}/data/models/superheroUpperLeg.bob \
  ${ASSET_BUILD_DIR}/data/models/bearPelvis.bob \
  ${ASSET_BUILD_DIR}/data/models/natureBackgroundVRFill.bob \
  ${ASSET_BUILD_DIR}/data/models/penguinHead.bob \
  ${ASSET_BUILD_DIR}/data/models/warriorToes.bob \
  ${ASSET_BUILD_DIR}/data/models/arrowBack.bob \
  ${ASSET_BUILD_DIR}/data/models/zigZagLevel.bob \
  ${ASSET_BUILD_DIR}/data/models/frostyUpperArm.bob \
  ${ASSET_BUILD_DIR}/data/models/tipTopLevelBottom.bob \
  ${ASSET_BUILD_DIR}/data/models/santaLowerLeg.bob \
  ${ASSET_BUILD_DIR}/data/models/playerLineup3Transparent.bob \
  ${ASSET_BUILD_DIR}/data/models/santaForeArm.bob \
  ${ASSET_BUILD_DIR}/data/models/agentToes.bob \
  ${ASSET_BUILD_DIR}/data/models/doomShroomLevel.bob \
  ${ASSET_BUILD_DIR}/data/models/bombSticky.bob \
  ${ASSET_BUILD_DIR}/data/models/zoeForeArm.bob \
  ${ASSET_BUILD_DIR}/data/models/doomShroomVRFill.bob \
  ${ASSET_BUILD_DIR}/data/models/alwaysLandLevelBottom.bob \
  ${ASSET_BUILD_DIR}/data/models/aliUpperArm.bob \
  ${ASSET_BUILD_DIR}/data/models/towerDLevelBottom.bob \
  ${ASSET_BUILD_DIR}/data/models/actionHeroPelvis.bob \
  ${ASSET_BUILD_DIR}/data/models/warriorHand.bob \
  ${ASSET_BUILD_DIR}/data/models/operaSingerTorso.bob \
  ${ASSET_BUILD_DIR}/data/models/frostyTorso.bob \
  ${ASSET_BUILD_DIR}/data/models/toolbarBackingBottom.bob \
  ${ASSET_BUILD_DIR}/data/models/gladiatorLowerLeg.bob \
  ${ASSET_BUILD_DIR}/data/models/neoSpazLowerLeg.bob \
  ${ASSET_BUILD_DIR}/data/models/robotToes.bob \
  ${ASSET_BUILD_DIR}/data/models/bunnyToes.bob \
  ${ASSET_BUILD_DIR}/data/models/santaToes.bob \
  ${ASSET_BUILD_DIR}/data/models/cowboyLowerLeg.bob \
  ${ASSET_BUILD_DIR}/data/models/ninjaUpperLeg.bob \
  ${ASSET_BUILD_DIR}/data/models/windowHSmallVMedOpaque.bob \
  ${ASSET_BUILD_DIR}/data/models/aliHead.bob \
  ${ASSET_BUILD_DIR}/data/models/cowboyHand.bob \
  ${ASSET_BUILD_DIR}/data/models/thePadBG.bob \
  ${ASSET_BUILD_DIR}/data/models/thePadVRFillBottom.bob \
  ${ASSET_BUILD_DIR}/data/models/bearTorso.bob \
  ${ASSET_BUILD_DIR}/data/models/superheroUpperArm.bob \
  ${ASSET_BUILD_DIR}/data/models/buttonLargerOpaque.bob \
  ${ASSET_BUILD_DIR}/data/models/witchUpperLeg.bob \
  ${ASSET_BUILD_DIR}/data/models/eyeBallIris.bob \
  ${ASSET_BUILD_DIR}/data/models/alienHand.bob \
  ${ASSET_BUILD_DIR}/data/models/jumpsuitUpperLeg.bob \
  ${ASSET_BUILD_DIR}/data/models/stepRightUpLevelBottom.bob \
  ${ASSET_BUILD_DIR}/data/models/cyborgHand.bob \
  ${ASSET_BUILD_DIR}/data/models/bunnyUpperLeg.bob \
  ${ASSET_BUILD_DIR}/data/models/witchToes.bob \
  ${ASSET_BUILD_DIR}/data/models/cowboyPelvis.bob \
  ${ASSET_BUILD_DIR}/data/models/penguinUpperLeg.bob \
  ${ASSET_BUILD_DIR}/data/models/melForeArm.bob \
  ${ASSET_BUILD_DIR}/data/models/buttonBackTransparent.bob \
  ${ASSET_BUILD_DIR}/data/models/monkeyFaceLevelBottom.bob \
  ${ASSET_BUILD_DIR}/data/models/frostyPelvis.bob \
  ${ASSET_BUILD_DIR}/data/models/pixieForeArm.bob \
  ${ASSET_BUILD_DIR}/data/models/neoSpazUpperArm.bob \
  ${ASSET_BUILD_DIR}/data/models/gladiatorUpperArm.bob \
  ${ASSET_BUILD_DIR}/data/models/superheroToes.bob \
  ${ASSET_BUILD_DIR}/data/models/oldLadyHand.bob \
  ${ASSET_BUILD_DIR}/data/models/kronkHand.bob \
  ${ASSET_BUILD_DIR}/data/models/oldLadyUpperLeg.bob \
  ${ASSET_BUILD_DIR}/data/models/windowHSmallVSmallTransparent.bob \
  ${ASSET_BUILD_DIR}/data/models/buttonSmallTransparent.bob \
  ${ASSET_BUILD_DIR}/data/models/cyborgUpperLeg.bob \
  ${ASSET_BUILD_DIR}/data/models/box.bob \
  ${ASSET_BUILD_DIR}/data/models/buttonSmallOpaque.bob \
  ${ASSET_BUILD_DIR}/data/models/aliLowerLeg.bob \
  ${ASSET_BUILD_DIR}/data/models/zoeToes.bob \
  ${ASSET_BUILD_DIR}/data/models/bearHand.bob \
  ${ASSET_BUILD_DIR}/data/models/bonesHand.bob \
  ${ASSET_BUILD_DIR}/data/models/alienPelvis.bob \
  ${ASSET_BUILD_DIR}/data/models/lakeFrigid.bob \
  ${ASSET_BUILD_DIR}/data/models/hockeyStadiumStands.bob \
  ${ASSET_BUILD_DIR}/data/models/penguinPelvis.bob \
  ${ASSET_BUILD_DIR}/data/models/superheroTorso.bob \
  ${ASSET_BUILD_DIR}/data/models/footballStadium.bob \
  ${ASSET_BUILD_DIR}/data/models/wrestlerPelvis.bob \
  ${ASSET_BUILD_DIR}/data/models/operaSingerToes.bob \
  ${ASSET_BUILD_DIR}/data/models/actionHeroHead.bob \
  ${ASSET_BUILD_DIR}/data/models/ninjaToes.bob \
  ${ASSET_BUILD_DIR}/data/models/flash.bob \
  ${ASSET_BUILD_DIR}/data/models/santaUpperArm.bob \
  ${ASSET_BUILD_DIR}/data/models/frostyLowerLeg.bob \
  ${ASSET_BUILD_DIR}/data/models/gladiatorTorso.bob \
  ${ASSET_BUILD_DIR}/data/models/superheroPelvis.bob \
  ${ASSET_BUILD_DIR}/data/models/cylinder.bob \
  ${ASSET_BUILD_DIR}/data/models/windowHSmallVSmallOpaque.bob \
  ${ASSET_BUILD_DIR}/data/models/thePadLevelBottom.bob \
  ${ASSET_BUILD_DIR}/data/models/neoSpazHead.bob \
  ${ASSET_BUILD_DIR}/data/models/toolbarBackingOpaque.bob \
  ${ASSET_BUILD_DIR}/data/models/shrapnel1.bob \
  ${ASSET_BUILD_DIR}/data/models/assassinForeArm.bob \
  ${ASSET_BUILD_DIR}/data/models/arrowFront.bob \
  ${ASSET_BUILD_DIR}/data/models/wrestlerHand.bob \
  ${ASSET_BUILD_DIR}/data/models/angryComputerTransparent.bob \
  ${ASSET_BUILD_DIR}/data/models/buttonLargeTransparent.bob \
  ${ASSET_BUILD_DIR}/data/models/wizardHand.bob \
  ${ASSET_BUILD_DIR}/data/models/boxingGlove.bob \
  ${ASSET_BUILD_DIR}/data/models/tipTopLevel.bob \
  ${ASSET_BUILD_DIR}/data/models/bonesTorso.bob \
  ${ASSET_BUILD_DIR}/data/models/lakeFrigidReflections.bob \
  ${ASSET_BUILD_DIR}/data/models/image2x1.bob \
  ${ASSET_BUILD_DIR}/data/models/superheroLowerLeg.bob \
  ${ASSET_BUILD_DIR}/data/models/buttonNull.bob \
  ${ASSET_BUILD_DIR}/data/models/cowboyUpperArm.bob \
  ${ASSET_BUILD_DIR}/data/models/buttonLargeOpaque.bob \
  ${ASSET_BUILD_DIR}/data/models/jumpsuitHand.bob \
  ${ASSET_BUILD_DIR}/data/models/locatorBox.bob \
  ${ASSET_BUILD_DIR}/data/models/cyborgPelvis.bob \
  ${ASSET_BUILD_DIR}/data/models/aliHand.bob \
  ${ASSET_BUILD_DIR}/data/models/cowboyHead.bob \
  ${ASSET_BUILD_DIR}/data/models/wrestlerLowerLeg.bob \
  ${ASSET_BUILD_DIR}/data/models/jackLowerLeg.bob \
  ${ASSET_BUILD_DIR}/data/models/alienLowerLeg.bob \
  ${ASSET_BUILD_DIR}/data/models/hairTuft3.bob \
  ${ASSET_BUILD_DIR}/data/models/pixieToes.bob \
  ${ASSET_BUILD_DIR}/data/models/rampageBG.bob \
  ${ASSET_BUILD_DIR}/data/models/impactBomb.bob \
  ${ASSET_BUILD_DIR}/data/models/alienHead.bob \
  ${ASSET_BUILD_DIR}/data/models/scrollBarThumbShortTransparent.bob \
  ${ASSET_BUILD_DIR}/data/models/assassinToes.bob \
  ${ASSET_BUILD_DIR}/data/models/jackToes.bob \
  ${ASSET_BUILD_DIR}/data/models/actionButtonTop.bob \
  ${ASSET_BUILD_DIR}/data/models/witchPelvis.bob \
  ${ASSET_BUILD_DIR}/data/models/cyborgHead.bob \
  ${ASSET_BUILD_DIR}/data/models/melUpperArm.bob \
  ${ASSET_BUILD_DIR}/data/models/tnt.bob \
  ${ASSET_BUILD_DIR}/data/models/wizardPelvis.bob \
  ${ASSET_BUILD_DIR}/data/models/rampageBG2.bob \
  ${ASSET_BUILD_DIR}/data/models/wizardUpperLeg.bob \
  ${ASSET_BUILD_DIR}/data/models/cowboyTorso.bob \
  ${ASSET_BUILD_DIR}/data/models/locatorCircle.bob \
  ${ASSET_BUILD_DIR}/data/models/frostyToes.bob \
  ${ASSET_BUILD_DIR}/data/models/bunnyForeArm.bob \
  ${ASSET_BUILD_DIR}/data/models/warriorLowerLeg.bob \
  ${ASSET_BUILD_DIR}/data/models/penguinForeArm.bob \
  ${ASSET_BUILD_DIR}/data/models/actionHeroUpperArm.bob \
  ${ASSET_BUILD_DIR}/data/models/actionButtonLeft.bob \
  ${ASSET_BUILD_DIR}/data/models/actionHeroForeArm.bob \
  ${ASSET_BUILD_DIR}/data/models/powerupSimple.bob \
  ${ASSET_BUILD_DIR}/data/models/robotUpperArm.bob \
  ${ASSET_BUILD_DIR}/data/models/bearForeArm.bob \
  ${ASSET_BUILD_DIR}/data/models/melToes.bob \
  ${ASSET_BUILD_DIR}/data/models/shrapnelSlime.bob \
  ${ASSET_BUILD_DIR}/data/models/lakeFrigidTop.bob \
  ${ASSET_BUILD_DIR}/data/models/pixieUpperLeg.bob \
  ${ASSET_BUILD_DIR}/data/models/operaSingerUpperArm.bob \
  ${ASSET_BUILD_DIR}/data/models/cyborgForeArm.bob \
  ${ASSET_BUILD_DIR}/data/models/shockWave.bob \
  ${ASSET_BUILD_DIR}/data/models/warriorHead.bob \
  ${ASSET_BUILD_DIR}/data/models/assassinPelvis.bob \
  ${ASSET_BUILD_DIR}/data/models/bearLowerLeg.bob \
  ${ASSET_BUILD_DIR}/data/models/penguinToes.bob \
  ${ASSET_BUILD_DIR}/data/models/jackForeArm.bob \
  ${ASSET_BUILD_DIR}/data/models/buttonSquareTransparent.bob \
  ${ASSET_BUILD_DIR}/data/models/aliPelvis.bob \
  ${ASSET_BUILD_DIR}/data/models/bonesLowerLeg.bob \
  ${ASSET_BUILD_DIR}/data/models/toolbarBackingTop.bob \
  ${ASSET_BUILD_DIR}/data/models/thePadLevel.bob \
  ${ASSET_BUILD_DIR}/data/models/kronkUpperLeg.bob \
  ${ASSET_BUILD_DIR}/data/models/tipTopBG.bob \
  ${ASSET_BUILD_DIR}/data/models/wizardForeArm.bob \
  ${ASSET_BUILD_DIR}/data/models/neoSpazHand.bob \
  ${ASSET_BUILD_DIR}/data/models/agentForeArm.bob \
  ${ASSET_BUILD_DIR}/data/models/actionHeroTorso.bob \
  ${ASSET_BUILD_DIR}/data/models/warriorUpperArm.bob \
  ${ASSET_BUILD_DIR}/data/models/logoTransparent.bob \
  ${ASSET_BUILD_DIR}/data/models/wrestlerHead.bob \
  ${ASSET_BUILD_DIR}/data/models/toolbarBackingBottom2.bob \
  ${ASSET_BUILD_DIR}/data/models/melLowerLeg.bob \
  ${ASSET_BUILD_DIR}/data/models/assassinUpperLeg.bob \
  ${ASSET_BUILD_DIR}/data/models/gladiatorToes.bob \
  ${ASSET_BUILD_DIR}/data/models/vrFade.bob \
  ${ASSET_BUILD_DIR}/data/models/rampageVRFill.bob \
  ${ASSET_BUILD_DIR}/data/models/cragCastleVRFillMound.bob \
  ${ASSET_BUILD_DIR}/data/models/courtyardLevel.bob \
  ${ASSET_BUILD_DIR}/data/models/landMine.bob \
  ${ASSET_BUILD_DIR}/data/models/wizardHead.bob \
  ${ASSET_BUILD_DIR}/data/models/oldLadyTorso.bob \
  ${ASSET_BUILD_DIR}/data/models/jackUpperArm.bob \
  ${ASSET_BUILD_DIR}/data/models/wrestlerUpperArm.bob \
  ${ASSET_BUILD_DIR}/data/models/alienUpperArm.bob \
  ${ASSET_BUILD_DIR}/data/models/jumpsuitHead.bob \
  ${ASSET_BUILD_DIR}/data/models/eyeBall.bob \
  ${ASSET_BUILD_DIR}/data/models/textBoxTransparent.bob \
  ${ASSET_BUILD_DIR}/data/models/bridgitLevelBottom.bob \
  ${ASSET_BUILD_DIR}/data/models/oldLadyHead.bob \
  ${ASSET_BUILD_DIR}/data/models/kronkHead.bob \
  ${ASSET_BUILD_DIR}/data/models/bearUpperArm.bob \
  ${ASSET_BUILD_DIR}/data/models/bunnyTorso.bob \
  ${ASSET_BUILD_DIR}/data/models/bonesUpperArm.bob \
  ${ASSET_BUILD_DIR}/data/models/bearHead.bob \
  ${ASSET_BUILD_DIR}/data/models/bonesHead.bob \
  ${ASSET_BUILD_DIR}/data/models/oldLadyForeArm.bob \
  ${ASSET_BUILD_DIR}/data/models/windowHSmallVMedTransparent.bob \
  ${ASSET_BUILD_DIR}/data/models/buttonMediumOpaque.bob \
  ${ASSET_BUILD_DIR}/data/models/roundaboutLevelBottom.bob \
  ${ASSET_BUILD_DIR}/data/models/buttonTabTransparent.bob \
  ${ASSET_BUILD_DIR}/data/models/warriorForeArm.bob \
  ${ASSET_BUILD_DIR}/data/models/operaSingerLowerLeg.bob \
  ${ASSET_BUILD_DIR}/data/models/agentUpperLeg.bob \
  ${ASSET_BUILD_DIR}/data/models/actionHeroLowerLeg.bob \
  ${ASSET_BUILD_DIR}/data/models/robotLowerLeg.bob \
  ${ASSET_BUILD_DIR}/data/models/buttonLargerTransparent.bob \
  ${ASSET_BUILD_DIR}/data/models/robotPelvis.bob \
  ${ASSET_BUILD_DIR}/data/models/actionButtonRight.bob \
  ${ASSET_BUILD_DIR}/data/models/zoeUpperLeg.bob \
  ${ASSET_BUILD_DIR}/data/models/actionHeroHand.bob \
  ${ASSET_BUILD_DIR}/data/models/buttonSquareOpaque.bob \
  ${ASSET_BUILD_DIR}/data/models/zoeHead.bob \
  ${ASSET_BUILD_DIR}/data/models/egg.bob \
  ${ASSET_BUILD_DIR}/data/models/hockeyStadiumInner.bob \
  ${ASSET_BUILD_DIR}/data/models/alienUpperLeg.bob \
  ${ASSET_BUILD_DIR}/data/models/jackUpperLeg.bob \
  ${ASSET_BUILD_DIR}/data/models/wrestlerUpperLeg.bob \
  ${ASSET_BUILD_DIR}/data/models/buttonBackSmallTransparent.bob \
  ${ASSET_BUILD_DIR}/data/models/monkeyFaceLevel.bob \
  ${ASSET_BUILD_DIR}/data/models/hairTuft2.bob \
  ${ASSET_BUILD_DIR}/data/models/bunnyPelvis.bob \
  ${ASSET_BUILD_DIR}/data/models/superheroHead.bob \
  ${ASSET_BUILD_DIR}/data/models/meterTransparent.bob \
  ${ASSET_BUILD_DIR}/data/models/warriorUpperLeg.bob \
  ${ASSET_BUILD_DIR}/data/models/gladiatorPelvis.bob \
  ${ASSET_BUILD_DIR}/data/models/actionHeroToes.bob \
  ${ASSET_BUILD_DIR}/data/models/jumpsuitPelvis.bob \
  ${ASSET_BUILD_DIR}/data/models/ninjaHead.bob \
  ${ASSET_BUILD_DIR}/data/models/footballStadiumVRFill.bob \
  ${ASSET_BUILD_DIR}/data/models/crossOut.bob \
  ${ASSET_BUILD_DIR}/data/models/checkTransparent.bob \
  ${ASSET_BUILD_DIR}/data/models/operaSingerHead.bob \
  ${ASSET_BUILD_DIR}/data/models/wizardLowerLeg.bob \
  ${ASSET_BUILD_DIR}/data/models/cyborgTorso.bob \
  ${ASSET_BUILD_DIR}/data/models/stepRightUpVRFillMound.bob \
  ${ASSET_BUILD_DIR}/data/models/robotForeArm.bob \
  ${ASSET_BUILD_DIR}/data/models/assassinUpperArm.bob \
  ${ASSET_BUILD_DIR}/data/models/scrollBarThumbShortSimple.bob \
  ${ASSET_BUILD_DIR}/data/models/bigG.bob \
  ${ASSET_BUILD_DIR}/data/models/agentUpperArm.bob \
  ${ASSET_BUILD_DIR}/data/models/courtyardLevelBottom.bob \
  ${ASSET_BUILD_DIR}/data/models/eyeLid.bob \
  ${ASSET_BUILD_DIR}/data/models/pixieLowerLeg.bob \
  ${ASSET_BUILD_DIR}/data/models/gladiatorHand.bob \
  ${ASSET_BUILD_DIR}/data/models/ninjaForeArm.bob \
  ${ASSET_BUILD_DIR}/data/models/penguinTorso.bob \
  ${ASSET_BUILD_DIR}/data/models/toolbarBackingTop2.bob \
  ${ASSET_BUILD_DIR}/data/models/stepRightUpLevel.bob \
  ${ASSET_BUILD_DIR}/data/models/neoSpazToes.bob \
  ${ASSET_BUILD_DIR}/data/models/zoeUpperArm.bob \
  ${ASSET_BUILD_DIR}/data/models/kronkTorso.bob \
  ${ASSET_BUILD_DIR}/data/models/warriorPelvis.bob \
  ${ASSET_BUILD_DIR}/data/models/gladiatorForeArm.bob \
  ${ASSET_BUILD_DIR}/data/models/locator.bob \
  ${ASSET_BUILD_DIR}/data/models/neoSpazForeArm.bob \
  ${ASSET_BUILD_DIR}/data/models/buttonMediumTransparent.bob \
  ${ASSET_BUILD_DIR}/data/models/pixiePelvis.bob \
  ${ASSET_BUILD_DIR}/data/models/logo.bob \
  ${ASSET_BUILD_DIR}/data/models/scrollBarThumbSimple.bob \
  ${ASSET_BUILD_DIR}/data/models/kronkLowerLeg.bob \
  ${ASSET_BUILD_DIR}/data/models/aliTorso.bob \
  ${ASSET_BUILD_DIR}/data/models/scrollBarThumbTransparent.bob \
  ${ASSET_BUILD_DIR}/data/models/locatorCircleOutline.bob \
  ${ASSET_BUILD_DIR}/data/models/alwaysLandVRFillMound.bob \
  ${ASSET_BUILD_DIR}/data/models/alienForeArm.bob \
  ${ASSET_BUILD_DIR}/data/models/bonesUpperLeg.bob \
  ${ASSET_BUILD_DIR}/data/models/softEdgeOutside.bob \
  ${ASSET_BUILD_DIR}/data/models/bearUpperLeg.bob \
  ${ASSET_BUILD_DIR}/data/models/roundaboutLevel.bob \
  ${ASSET_BUILD_DIR}/data/models/wizardUpperArm.bob \
  ${ASSET_BUILD_DIR}/data/models/playerLineup4Transparent.bob \
  ${ASSET_BUILD_DIR}/data/models/zigZagLevelBottom.bob \
  ${ASSET_BUILD_DIR}/data/models/assassinLowerLeg.bob \
  ${ASSET_BUILD_DIR}/data/models/melUpperLeg.bob \
  ${ASSET_BUILD_DIR}/data/models/robotTorso.bob \
  ${ASSET_BUILD_DIR}/data/models/cragCastleLevel.bob \
  ${ASSET_BUILD_DIR}/data/models/zoePelvis.bob \
  ${ASSET_BUILD_DIR}/data/models/agentHead.bob \
  ${ASSET_BUILD_DIR}/data/models/rampageLevel.bob \
  ${ASSET_BUILD_DIR}/data/models/thePadVRFillMound.bob \
  ${ASSET_BUILD_DIR}/data/models/melHand.bob \
  ${ASSET_BUILD_DIR}/data/models/jackTorso.bob \
  ${ASSET_BUILD_DIR}/data/models/pixieTorso.bob \
  ${ASSET_BUILD_DIR}/data/models/santaHead.bob \
  ${ASSET_BUILD_DIR}/data/models/playerLineup1Transparent.bob \
  ${ASSET_BUILD_DIR}/data/models/bigGBottom.bob \
  ${ASSET_BUILD_DIR}/data/models/robotHead.bob \
  ${ASSET_BUILD_DIR}/data/models/frameInset.bob \
  ${ASSET_BUILD_DIR}/data/models/bunnyHead.bob \
  ${ASSET_BUILD_DIR}/data/models/santaTorso.bob \
  ${ASSET_BUILD_DIR}/data/models/penguinHand.bob \
  ${ASSET_BUILD_DIR}/data/models/heartTransparent.bob \
  ${ASSET_BUILD_DIR}/data/models/hairTuft4.bob \
  ${ASSET_BUILD_DIR}/data/models/doomShroomStem.bob \
  ${ASSET_BUILD_DIR}/data/models/buttonBackSmallOpaque.bob \
  ${ASSET_BUILD_DIR}/data/models/pixieHand.bob \
  ${ASSET_BUILD_DIR}/data/models/scrollBarTroughTransparent.bob \
  ${ASSET_BUILD_DIR}/data/models/assassinHand.bob \
  ${ASSET_BUILD_DIR}/data/models/jackHand.bob \
  ${ASSET_BUILD_DIR}/data/models/agentPelvis.bob \
  ${ASSET_BUILD_DIR}/data/models/towerDLevel.bob \
  ${ASSET_BUILD_DIR}/data/models/softEdgeInside.bob \
  ${ASSET_BUILD_DIR}/data/models/aliToes.bob \
  ${ASSET_BUILD_DIR}/data/models/hockeyStadiumOuter.bob \
  ${ASSET_BUILD_DIR}/data/models/warriorTorso.bob \
  ${ASSET_BUILD_DIR}/data/models/image2x1Vertical.bob \
  ${ASSET_BUILD_DIR}/data/models/kronkUpperArm.bob \
  ${ASSET_BUILD_DIR}/data/models/zoeLowerLeg.bob \
  ${ASSET_BUILD_DIR}/data/models/wrestlerTorso.bob \
  ${ASSET_BUILD_DIR}/data/models/frostyHand.bob \
  ${ASSET_BUILD_DIR}/data/models/robotUpperLeg.bob \
  ${ASSET_BUILD_DIR}/data/models/alwaysLandBG.bob \
  ${ASSET_BUILD_DIR}/data/models/jumpsuitForeArm.bob \
  ${ASSET_BUILD_DIR}/data/models/actionHeroUpperLeg.bob \
  ${ASSET_BUILD_DIR}/data/models/agentLowerLeg.bob \
  ${ASSET_BUILD_DIR}/data/models/witchHead.bob \
  ${ASSET_BUILD_DIR}/data/models/operaSingerUpperLeg.bob \
  ${ASSET_BUILD_DIR}/data/models/pixieUpperArm.bob \
  ${ASSET_BUILD_DIR}/data/models/flagPole.bob \
  ${ASSET_BUILD_DIR}/data/models/powerup.bob \
  ${ASSET_BUILD_DIR}/data/models/thePadVRFillTop.bob


FONT_TARGETS = \
  ${ASSET_BUILD_DIR}/data/fonts/fontSmall1.fdata \
  ${ASSET_BUILD_DIR}/data/fonts/fontSmall3.fdata \
  ${ASSET_BUILD_DIR}/data/fonts/fontSmall7.fdata \
  ${ASSET_BUILD_DIR}/data/fonts/fontSmall5.fdata \
  ${ASSET_BUILD_DIR}/data/fonts/fontSmall2.fdata \
  ${ASSET_BUILD_DIR}/data/fonts/fontSmall0.fdata \
  ${ASSET_BUILD_DIR}/data/fonts/fontSmall4.fdata \
  ${ASSET_BUILD_DIR}/data/fonts/fontSmall6.fdata


DATA_TARGETS = \
  ${ASSET_BUILD_DIR}/data/data/langdata.json \
  ${ASSET_BUILD_DIR}/data/data/maps/monkey_face.json \
  ${ASSET_BUILD_DIR}/data/data/maps/football_stadium.json \
  ${ASSET_BUILD_DIR}/data/data/maps/tip_top.json \
  ${ASSET_BUILD_DIR}/data/data/maps/crag_castle.json \
  ${ASSET_BUILD_DIR}/data/data/maps/doom_shroom.json \
  ${ASSET_BUILD_DIR}/data/data/maps/zig_zag.json \
  ${ASSET_BUILD_DIR}/data/data/maps/step_right_up.json \
  ${ASSET_BUILD_DIR}/data/data/maps/bridgit.json \
  ${ASSET_BUILD_DIR}/data/data/maps/happy_thoughts.json \
  ${ASSET_BUILD_DIR}/data/data/maps/roundabout.json \
  ${ASSET_BUILD_DIR}/data/data/maps/rampage.json \
  ${ASSET_BUILD_DIR}/data/data/maps/lake_frigid.json \
  ${ASSET_BUILD_DIR}/data/data/maps/tower_d.json \
  ${ASSET_BUILD_DIR}/data/data/maps/hockey_stadium.json \
  ${ASSET_BUILD_DIR}/data/data/maps/courtyard.json \
  ${ASSET_BUILD_DIR}/data/data/maps/the_pad.json \
  ${ASSET_BUILD_DIR}/data/data/maps/big_g.json \
  ${ASSET_BUILD_DIR}/data/data/languages/arabic.json \
  ${ASSET_BUILD_DIR}/data/data/languages/chinese.json \
  ${ASSET_BUILD_DIR}/data/data/languages/hungarian.json \
  ${ASSET_BUILD_DIR}/data/data/languages/french.json \
  ${ASSET_BUILD_DIR}/data/data/languages/serbian.json \
  ${ASSET_BUILD_DIR}/data/data/languages/belarussian.json \
  ${ASSET_BUILD_DIR}/data/data/languages/polish.json \
  ${ASSET_BUILD_DIR}/data/data/languages/persian.json \
  ${ASSET_BUILD_DIR}/data/data/languages/esperanto.json \
  ${ASSET_BUILD_DIR}/data/data/languages/croatian.json \
  ${ASSET_BUILD_DIR}/data/data/languages/turkish.json \
  ${ASSET_BUILD_DIR}/data/data/languages/german.json \
  ${ASSET_BUILD_DIR}/data/data/languages/spanish.json \
  ${ASSET_BUILD_DIR}/data/data/languages/portuguese.json \
  ${ASSET_BUILD_DIR}/data/data/languages/korean.json \
  ${ASSET_BUILD_DIR}/data/data/languages/romanian.json \
  ${ASSET_BUILD_DIR}/data/data/languages/english.json \
  ${ASSET_BUILD_DIR}/data/data/languages/russian.json \
  ${ASSET_BUILD_DIR}/data/data/languages/ukrainian.json \
  ${ASSET_BUILD_DIR}/data/data/languages/swedish.json \
  ${ASSET_BUILD_DIR}/data/data/languages/gibberish.json \
  ${ASSET_BUILD_DIR}/data/data/languages/dutch.json \
  ${ASSET_BUILD_DIR}/data/data/languages/greek.json \
  ${ASSET_BUILD_DIR}/data/data/languages/hindi.json \
  ${ASSET_BUILD_DIR}/data/data/languages/czech.json \
  ${ASSET_BUILD_DIR}/data/data/languages/indonesian.json \
  ${ASSET_BUILD_DIR}/data/data/languages/italian.json \
  ${ASSET_BUILD_DIR}/data/data/languages/danish.json


AUDIO_TARGETS = \
  ${ASSET_BUILD_DIR}/data/audio/penguinDeath.ogg \
  ${ASSET_BUILD_DIR}/data/audio/ali1.ogg \
  ${ASSET_BUILD_DIR}/data/audio/whenJohnnyComesMarchingHomeMusic.ogg \
  ${ASSET_BUILD_DIR}/data/audio/kronk4.ogg \
  ${ASSET_BUILD_DIR}/data/audio/bearHit1.ogg \
  ${ASSET_BUILD_DIR}/data/audio/jumpsuitHit1.ogg \
  ${ASSET_BUILD_DIR}/data/audio/skid01.ogg \
  ${ASSET_BUILD_DIR}/data/audio/swish3.ogg \
  ${ASSET_BUILD_DIR}/data/audio/ticking.ogg \
  ${ASSET_BUILD_DIR}/data/audio/agent4.ogg \
  ${ASSET_BUILD_DIR}/data/audio/announceTen.ogg \
  ${ASSET_BUILD_DIR}/data/audio/spazImpact04.ogg \
  ${ASSET_BUILD_DIR}/data/audio/bearFall.ogg \
  ${ASSET_BUILD_DIR}/data/audio/jumpsuitFall.ogg \
  ${ASSET_BUILD_DIR}/data/audio/tap.ogg \
  ${ASSET_BUILD_DIR}/data/audio/wizard4.ogg \
  ${ASSET_BUILD_DIR}/data/audio/jackHit01.ogg \
  ${ASSET_BUILD_DIR}/data/audio/kronk10.ogg \
  ${ASSET_BUILD_DIR}/data/audio/agentHit2.ogg \
  ${ASSET_BUILD_DIR}/data/audio/swish2.ogg \
  ${ASSET_BUILD_DIR}/data/audio/corkPop.ogg \
  ${ASSET_BUILD_DIR}/data/audio/laser.ogg \
  ${ASSET_BUILD_DIR}/data/audio/announceFour.ogg \
  ${ASSET_BUILD_DIR}/data/audio/frostyDeath.ogg \
  ${ASSET_BUILD_DIR}/data/audio/superhero1.ogg \
  ${ASSET_BUILD_DIR}/data/audio/scoreHit02.ogg \
  ${ASSET_BUILD_DIR}/data/audio/warnBeep.ogg \
  ${ASSET_BUILD_DIR}/data/audio/kronk5.ogg \
  ${ASSET_BUILD_DIR}/data/audio/oldLadyHit2.ogg \
  ${ASSET_BUILD_DIR}/data/audio/crowdChant.ogg \
  ${ASSET_BUILD_DIR}/data/audio/scamper01.ogg \
  ${ASSET_BUILD_DIR}/data/audio/ali2.ogg \
  ${ASSET_BUILD_DIR}/data/audio/kronk7.ogg \
  ${ASSET_BUILD_DIR}/data/audio/refWhistle.ogg \
  ${ASSET_BUILD_DIR}/data/audio/bearHit2.ogg \
  ${ASSET_BUILD_DIR}/data/audio/jumpsuitHit2.ogg \
  ${ASSET_BUILD_DIR}/data/audio/superhero3.ogg \
  ${ASSET_BUILD_DIR}/data/audio/jackFall01.ogg \
  ${ASSET_BUILD_DIR}/data/audio/aliDeath.ogg \
  ${ASSET_BUILD_DIR}/data/audio/technoHit01.ogg \
  ${ASSET_BUILD_DIR}/data/audio/frostyFall.ogg \
  ${ASSET_BUILD_DIR}/data/audio/oldLadyFall.ogg \
  ${ASSET_BUILD_DIR}/data/audio/jackHit03.ogg \
  ${ASSET_BUILD_DIR}/data/audio/alien4.ogg \
  ${ASSET_BUILD_DIR}/data/audio/agentFall.ogg \
  ${ASSET_BUILD_DIR}/data/audio/activateBeep.ogg \
  ${ASSET_BUILD_DIR}/data/audio/freeze.ogg \
  ${ASSET_BUILD_DIR}/data/audio/jackHit02.ogg \
  ${ASSET_BUILD_DIR}/data/audio/blank.ogg \
  ${ASSET_BUILD_DIR}/data/audio/dingSmall.ogg \
  ${ASSET_BUILD_DIR}/data/audio/agentHit1.ogg \
  ${ASSET_BUILD_DIR}/data/audio/superhero2.ogg \
  ${ASSET_BUILD_DIR}/data/audio/scoreHit01.ogg \
  ${ASSET_BUILD_DIR}/data/audio/kronk6.ogg \
  ${ASSET_BUILD_DIR}/data/audio/oldLadyHit1.ogg \
  ${ASSET_BUILD_DIR}/data/audio/ali3.ogg \
  ${ASSET_BUILD_DIR}/data/audio/zoeEff.ogg \
  ${ASSET_BUILD_DIR}/data/audio/swip2.ogg \
  ${ASSET_BUILD_DIR}/data/audio/swish.ogg \
  ${ASSET_BUILD_DIR}/data/audio/kronk2.ogg \
  ${ASSET_BUILD_DIR}/data/audio/witchHit2.ogg \
  ${ASSET_BUILD_DIR}/data/audio/penguinHit2.ogg \
  ${ASSET_BUILD_DIR}/data/audio/agent2.ogg \
  ${ASSET_BUILD_DIR}/data/audio/dingSmallHigh.ogg \
  ${ASSET_BUILD_DIR}/data/audio/santaDeath.ogg \
  ${ASSET_BUILD_DIR}/data/audio/alienFall.ogg \
  ${ASSET_BUILD_DIR}/data/audio/jackHit06.ogg \
  ${ASSET_BUILD_DIR}/data/audio/alien1.ogg \
  ${ASSET_BUILD_DIR}/data/audio/spazScream01.ogg \
  ${ASSET_BUILD_DIR}/data/audio/spazImpact02.ogg \
  ${ASSET_BUILD_DIR}/data/audio/wizard3.ogg \
  ${ASSET_BUILD_DIR}/data/audio/spazFall01.ogg \
  ${ASSET_BUILD_DIR}/data/audio/wizard2.ogg \
  ${ASSET_BUILD_DIR}/data/audio/spazImpact03.ogg \
  ${ASSET_BUILD_DIR}/data/audio/scoreIncrease.ogg \
  ${ASSET_BUILD_DIR}/data/audio/jackHit07.ogg \
  ${ASSET_BUILD_DIR}/data/audio/bunnyHit2.ogg \
  ${ASSET_BUILD_DIR}/data/audio/ninjaFall1.ogg \
  ${ASSET_BUILD_DIR}/data/audio/orchestraHit.ogg \
  ${ASSET_BUILD_DIR}/data/audio/agent3.ogg \
  ${ASSET_BUILD_DIR}/data/audio/melFall01.ogg \
  ${ASSET_BUILD_DIR}/data/audio/playerDeath.ogg \
  ${ASSET_BUILD_DIR}/data/audio/alienHit1.ogg \
  ${ASSET_BUILD_DIR}/data/audio/kronk3.ogg \
  ${ASSET_BUILD_DIR}/data/audio/operaSingerDeath.ogg \
  ${ASSET_BUILD_DIR}/data/audio/witchHit1.ogg \
  ${ASSET_BUILD_DIR}/data/audio/kronk1.ogg \
  ${ASSET_BUILD_DIR}/data/audio/bunnyFall.ogg \
  ${ASSET_BUILD_DIR}/data/audio/ali4.ogg \
  ${ASSET_BUILD_DIR}/data/audio/penguinHit1.ogg \
  ${ASSET_BUILD_DIR}/data/audio/superPunch.ogg \
  ${ASSET_BUILD_DIR}/data/audio/agent1.ogg \
  ${ASSET_BUILD_DIR}/data/audio/ooh.ogg \
  ${ASSET_BUILD_DIR}/data/audio/alien2.ogg \
  ${ASSET_BUILD_DIR}/data/audio/jackHit05.ogg \
  ${ASSET_BUILD_DIR}/data/audio/fuse01.ogg \
  ${ASSET_BUILD_DIR}/data/audio/spazImpact01.ogg \
  ${ASSET_BUILD_DIR}/data/audio/flagCatcherMusic.ogg \
  ${ASSET_BUILD_DIR}/data/audio/foghorn.ogg \
  ${ASSET_BUILD_DIR}/data/audio/wizard1.ogg \
  ${ASSET_BUILD_DIR}/data/audio/announceThree.ogg \
  ${ASSET_BUILD_DIR}/data/audio/jackHit04.ogg \
  ${ASSET_BUILD_DIR}/data/audio/alien3.ogg \
  ${ASSET_BUILD_DIR}/data/audio/shieldDown.ogg \
  ${ASSET_BUILD_DIR}/data/audio/penguinFall.ogg \
  ${ASSET_BUILD_DIR}/data/audio/kronkDeath.ogg \
  ${ASSET_BUILD_DIR}/data/audio/witchFall.ogg \
  ${ASSET_BUILD_DIR}/data/audio/spazOw.ogg \
  ${ASSET_BUILD_DIR}/data/audio/bunnyHit1.ogg \
  ${ASSET_BUILD_DIR}/data/audio/superhero4.ogg \
  ${ASSET_BUILD_DIR}/data/audio/punchWeak01.ogg \
  ${ASSET_BUILD_DIR}/data/audio/alienHit2.ogg \
  ${ASSET_BUILD_DIR}/data/audio/deek2.ogg \
  ${ASSET_BUILD_DIR}/data/audio/actionHeroHit2.ogg \
  ${ASSET_BUILD_DIR}/data/audio/pixie3.ogg \
  ${ASSET_BUILD_DIR}/data/audio/ninjaHit2.ogg \
  ${ASSET_BUILD_DIR}/data/audio/warriorDeath.ogg \
  ${ASSET_BUILD_DIR}/data/audio/jumpsuitDeath.ogg \
  ${ASSET_BUILD_DIR}/data/audio/bearDeath.ogg \
  ${ASSET_BUILD_DIR}/data/audio/actionHeroDeath.ogg \
  ${ASSET_BUILD_DIR}/data/audio/oldLady4.ogg \
  ${ASSET_BUILD_DIR}/data/audio/frosty01.ogg \
  ${ASSET_BUILD_DIR}/data/audio/gladiatorHit1.ogg \
  ${ASSET_BUILD_DIR}/data/audio/pixieDeath.ogg \
  ${ASSET_BUILD_DIR}/data/audio/healthPowerup.ogg \
  ${ASSET_BUILD_DIR}/data/audio/impactMedium.ogg \
  ${ASSET_BUILD_DIR}/data/audio/jackDeath01.ogg \
  ${ASSET_BUILD_DIR}/data/audio/zoeImpact01.ogg \
  ${ASSET_BUILD_DIR}/data/audio/forwardMarchMusic.ogg \
  ${ASSET_BUILD_DIR}/data/audio/woodDebrisFall.ogg \
  ${ASSET_BUILD_DIR}/data/audio/ninjaHit3.ogg \
  ${ASSET_BUILD_DIR}/data/audio/pixieHit2.ogg \
  ${ASSET_BUILD_DIR}/data/audio/splatter.ogg \
  ${ASSET_BUILD_DIR}/data/audio/gladiatorFall.ogg \
  ${ASSET_BUILD_DIR}/data/audio/tick.ogg \
  ${ASSET_BUILD_DIR}/data/audio/pixie2.ogg \
  ${ASSET_BUILD_DIR}/data/audio/actionHeroHit1.ogg \
  ${ASSET_BUILD_DIR}/data/audio/swip.ogg \
  ${ASSET_BUILD_DIR}/data/audio/ninjaHit1.ogg \
  ${ASSET_BUILD_DIR}/data/audio/zoeImpact03.ogg \
  ${ASSET_BUILD_DIR}/data/audio/zoeFall01.ogg \
  ${ASSET_BUILD_DIR}/data/audio/frosty02.ogg \
  ${ASSET_BUILD_DIR}/data/audio/gladiatorHit2.ogg \
  ${ASSET_BUILD_DIR}/data/audio/pixieFall.ogg \
  ${ASSET_BUILD_DIR}/data/audio/zoeScream01.ogg \
  ${ASSET_BUILD_DIR}/data/audio/frosty03.ogg \
  ${ASSET_BUILD_DIR}/data/audio/actionHeroFall.ogg \
  ${ASSET_BUILD_DIR}/data/audio/menuMusic.ogg \
  ${ASSET_BUILD_DIR}/data/audio/zoeImpact02.ogg \
  ${ASSET_BUILD_DIR}/data/audio/penguin4.ogg \
  ${ASSET_BUILD_DIR}/data/audio/runAwayMusic.ogg \
  ${ASSET_BUILD_DIR}/data/audio/pixieHit1.ogg \
  ${ASSET_BUILD_DIR}/data/audio/pixie1.ogg \
  ${ASSET_BUILD_DIR}/data/audio/metalHit.ogg \
  ${ASSET_BUILD_DIR}/data/audio/hiss.ogg \
  ${ASSET_BUILD_DIR}/data/audio/ninjaHit4.ogg \
  ${ASSET_BUILD_DIR}/data/audio/bunnyJump.ogg \
  ${ASSET_BUILD_DIR}/data/audio/cowboyDeath.ogg \
  ${ASSET_BUILD_DIR}/data/audio/oldLady2.ogg \
  ${ASSET_BUILD_DIR}/data/audio/mel09.ogg \
  ${ASSET_BUILD_DIR}/data/audio/announceSix.ogg \
  ${ASSET_BUILD_DIR}/data/audio/raceBeep2.ogg \
  ${ASSET_BUILD_DIR}/data/audio/announceTwo.ogg \
  ${ASSET_BUILD_DIR}/data/audio/mel08.ogg \
  ${ASSET_BUILD_DIR}/data/audio/oldLady3.ogg \
  ${ASSET_BUILD_DIR}/data/audio/punch01.ogg \
  ${ASSET_BUILD_DIR}/data/audio/penguin1.ogg \
  ${ASSET_BUILD_DIR}/data/audio/orchestraHitBig2.ogg \
  ${ASSET_BUILD_DIR}/data/audio/robotHit2.ogg \
  ${ASSET_BUILD_DIR}/data/audio/ninjaHit5.ogg \
  ${ASSET_BUILD_DIR}/data/audio/pixie4.ogg \
  ${ASSET_BUILD_DIR}/data/audio/operaSingerHit2.ogg \
  ${ASSET_BUILD_DIR}/data/audio/cyborgDeath.ogg \
  ${ASSET_BUILD_DIR}/data/audio/ninjaHit7.ogg \
  ${ASSET_BUILD_DIR}/data/audio/survivalMusic.ogg \
  ${ASSET_BUILD_DIR}/data/audio/penguin3.ogg \
  ${ASSET_BUILD_DIR}/data/audio/oldLady1.ogg \
  ${ASSET_BUILD_DIR}/data/audio/agentDeath.ogg \
  ${ASSET_BUILD_DIR}/data/audio/cashRegister2.ogg \
  ${ASSET_BUILD_DIR}/data/audio/frosty04.ogg \
  ${ASSET_BUILD_DIR}/data/audio/operaSingerFall.ogg \
  ${ASSET_BUILD_DIR}/data/audio/robotFall.ogg \
  ${ASSET_BUILD_DIR}/data/audio/scaryMusic.ogg \
  ${ASSET_BUILD_DIR}/data/audio/raceBeep1.ogg \
  ${ASSET_BUILD_DIR}/data/audio/frosty05.ogg \
  ${ASSET_BUILD_DIR}/data/audio/penguin2.ogg \
  ${ASSET_BUILD_DIR}/data/audio/zoeImpact04.ogg \
  ${ASSET_BUILD_DIR}/data/audio/orchestraHitBig1.ogg \
  ${ASSET_BUILD_DIR}/data/audio/robotHit1.ogg \
  ${ASSET_BUILD_DIR}/data/audio/ninjaHit6.ogg \
  ${ASSET_BUILD_DIR}/data/audio/gong.ogg \
  ${ASSET_BUILD_DIR}/data/audio/operaSingerHit1.ogg \
  ${ASSET_BUILD_DIR}/data/audio/shieldUp.ogg \
  ${ASSET_BUILD_DIR}/data/audio/charSelectMusic.ogg \
  ${ASSET_BUILD_DIR}/data/audio/cyborg2.ogg \
  ${ASSET_BUILD_DIR}/data/audio/santa05.ogg \
  ${ASSET_BUILD_DIR}/data/audio/bones1.ogg \
  ${ASSET_BUILD_DIR}/data/audio/shatter.ogg \
  ${ASSET_BUILD_DIR}/data/audio/kronkFall.ogg \
  ${ASSET_BUILD_DIR}/data/audio/impactHard.ogg \
  ${ASSET_BUILD_DIR}/data/audio/bombRoll01.ogg \
  ${ASSET_BUILD_DIR}/data/audio/explosion05.ogg \
  ${ASSET_BUILD_DIR}/data/audio/announceEight.ogg \
  ${ASSET_BUILD_DIR}/data/audio/superheroFall.ogg \
  ${ASSET_BUILD_DIR}/data/audio/mel06.ogg \
  ${ASSET_BUILD_DIR}/data/audio/santaHit01.ogg \
  ${ASSET_BUILD_DIR}/data/audio/cyborgHit2.ogg \
  ${ASSET_BUILD_DIR}/data/audio/bonesDeath.ogg \
  ${ASSET_BUILD_DIR}/data/audio/deek.ogg \
  ${ASSET_BUILD_DIR}/data/audio/mel07.ogg \
  ${ASSET_BUILD_DIR}/data/audio/gladiator4.ogg \
  ${ASSET_BUILD_DIR}/data/audio/explosion04.ogg \
  ${ASSET_BUILD_DIR}/data/audio/wrestler1.ogg \
  ${ASSET_BUILD_DIR}/data/audio/spazJump01.ogg \
  ${ASSET_BUILD_DIR}/data/audio/santaFall.ogg \
  ${ASSET_BUILD_DIR}/data/audio/superheroHit1.ogg \
  ${ASSET_BUILD_DIR}/data/audio/punchSwish.ogg \
  ${ASSET_BUILD_DIR}/data/audio/santa04.ogg \
  ${ASSET_BUILD_DIR}/data/audio/cyborg3.ogg \
  ${ASSET_BUILD_DIR}/data/audio/zoePickup01.ogg \
  ${ASSET_BUILD_DIR}/data/audio/cyborg1.ogg \
  ${ASSET_BUILD_DIR}/data/audio/spazAttack04.ogg \
  ${ASSET_BUILD_DIR}/data/audio/bigImpact2.ogg \
  ${ASSET_BUILD_DIR}/data/audio/bones2.ogg \
  ${ASSET_BUILD_DIR}/data/audio/ninjaHit8.ogg \
  ${ASSET_BUILD_DIR}/data/audio/announceNine.ogg \
  ${ASSET_BUILD_DIR}/data/audio/spazJump03.ogg \
  ${ASSET_BUILD_DIR}/data/audio/wrestler3.ogg \
  ${ASSET_BUILD_DIR}/data/audio/bunnyDeath.ogg \
  ${ASSET_BUILD_DIR}/data/audio/mel05.ogg \
  ${ASSET_BUILD_DIR}/data/audio/santaHit02.ogg \
  ${ASSET_BUILD_DIR}/data/audio/cyborgHit1.ogg \
  ${ASSET_BUILD_DIR}/data/audio/bear4.ogg \
  ${ASSET_BUILD_DIR}/data/audio/gunCocking.ogg \
  ${ASSET_BUILD_DIR}/data/audio/spawn.ogg \
  ${ASSET_BUILD_DIR}/data/audio/powerdown01.ogg \
  ${ASSET_BUILD_DIR}/data/audio/santaHit03.ogg \
  ${ASSET_BUILD_DIR}/data/audio/assassin4.ogg \
  ${ASSET_BUILD_DIR}/data/audio/mel04.ogg \
  ${ASSET_BUILD_DIR}/data/audio/mel10.ogg \
  ${ASSET_BUILD_DIR}/data/audio/cyborgFall.ogg \
  ${ASSET_BUILD_DIR}/data/audio/wrestler2.ogg \
  ${ASSET_BUILD_DIR}/data/audio/spazJump02.ogg \
  ${ASSET_BUILD_DIR}/data/audio/bones3.ogg \
  ${ASSET_BUILD_DIR}/data/audio/superheroHit2.ogg \
  ${ASSET_BUILD_DIR}/data/audio/bellMed.ogg \
  ${ASSET_BUILD_DIR}/data/audio/santa03.ogg \
  ${ASSET_BUILD_DIR}/data/audio/cyborg4.ogg \
  ${ASSET_BUILD_DIR}/data/audio/powerup01.ogg \
  ${ASSET_BUILD_DIR}/data/audio/robotDeath.ogg \
  ${ASSET_BUILD_DIR}/data/audio/flyingMusic.ogg \
  ${ASSET_BUILD_DIR}/data/audio/shieldHit.ogg \
  ${ASSET_BUILD_DIR}/data/audio/spazAttack01.ogg \
  ${ASSET_BUILD_DIR}/data/audio/sparkle02.ogg \
  ${ASSET_BUILD_DIR}/data/audio/cowboyHit1.ogg \
  ${ASSET_BUILD_DIR}/data/audio/cashRegister.ogg \
  ${ASSET_BUILD_DIR}/data/audio/explosion03.ogg \
  ${ASSET_BUILD_DIR}/data/audio/announceOne.ogg \
  ${ASSET_BUILD_DIR}/data/audio/gladiator3.ogg \
  ${ASSET_BUILD_DIR}/data/audio/impactMedium2.ogg \
  ${ASSET_BUILD_DIR}/data/audio/bear1.ogg \
  ${ASSET_BUILD_DIR}/data/audio/wrestlerDeath.ogg \
  ${ASSET_BUILD_DIR}/data/audio/pop01.ogg \
  ${ASSET_BUILD_DIR}/data/audio/frostyHit01.ogg \
  ${ASSET_BUILD_DIR}/data/audio/cowboyFall.ogg \
  ${ASSET_BUILD_DIR}/data/audio/assassin1.ogg \
  ${ASSET_BUILD_DIR}/data/audio/gladiator2.ogg \
  ${ASSET_BUILD_DIR}/data/audio/mel01.ogg \
  ${ASSET_BUILD_DIR}/data/audio/warriorHit2.ogg \
  ${ASSET_BUILD_DIR}/data/audio/explosion02.ogg \
  ${ASSET_BUILD_DIR}/data/audio/blip.ogg \
  ${ASSET_BUILD_DIR}/data/audio/sparkle03.ogg \
  ${ASSET_BUILD_DIR}/data/audio/bigImpact.ogg \
  ${ASSET_BUILD_DIR}/data/audio/santa02.ogg \
  ${ASSET_BUILD_DIR}/data/audio/boo.ogg \
  ${ASSET_BUILD_DIR}/data/audio/sparkle01.ogg \
  ${ASSET_BUILD_DIR}/data/audio/spazAttack02.ogg \
  ${ASSET_BUILD_DIR}/data/audio/warriorFall.ogg \
  ${ASSET_BUILD_DIR}/data/audio/cymbal.ogg \
  ${ASSET_BUILD_DIR}/data/audio/cowboyHit2.ogg \
  ${ASSET_BUILD_DIR}/data/audio/slowEpicMusic.ogg \
  ${ASSET_BUILD_DIR}/data/audio/laserReverse.ogg \
  ${ASSET_BUILD_DIR}/data/audio/mel03.ogg \
  ${ASSET_BUILD_DIR}/data/audio/bellLow.ogg \
  ${ASSET_BUILD_DIR}/data/audio/bear2.ogg \
  ${ASSET_BUILD_DIR}/data/audio/santaHit04.ogg \
  ${ASSET_BUILD_DIR}/data/audio/assassin3.ogg \
  ${ASSET_BUILD_DIR}/data/audio/zoeOw.ogg \
  ${ASSET_BUILD_DIR}/data/audio/frostyHit03.ogg \
  ${ASSET_BUILD_DIR}/data/audio/frostyHit02.ogg \
  ${ASSET_BUILD_DIR}/data/audio/victoryMusic.ogg \
  ${ASSET_BUILD_DIR}/data/audio/assassin2.ogg \
  ${ASSET_BUILD_DIR}/data/audio/bear3.ogg \
  ${ASSET_BUILD_DIR}/data/audio/gladiator1.ogg \
  ${ASSET_BUILD_DIR}/data/audio/mel02.ogg \
  ${ASSET_BUILD_DIR}/data/audio/warriorHit1.ogg \
  ${ASSET_BUILD_DIR}/data/audio/explosion01.ogg \
  ${ASSET_BUILD_DIR}/data/audio/boxDrop.ogg \
  ${ASSET_BUILD_DIR}/data/audio/wrestler4.ogg \
  ${ASSET_BUILD_DIR}/data/audio/wizardDeath.ogg \
  ${ASSET_BUILD_DIR}/data/audio/spazJump04.ogg \
  ${ASSET_BUILD_DIR}/data/audio/oldLadyDeath.ogg \
  ${ASSET_BUILD_DIR}/data/audio/zoeDeath01.ogg \
  ${ASSET_BUILD_DIR}/data/audio/spazAttack03.ogg \
  ${ASSET_BUILD_DIR}/data/audio/bellHigh.ogg \
  ${ASSET_BUILD_DIR}/data/audio/santa01.ogg \
  ${ASSET_BUILD_DIR}/data/audio/cowboy1.ogg \
  ${ASSET_BUILD_DIR}/data/audio/jack04.ogg \
  ${ASSET_BUILD_DIR}/data/audio/toTheDeathMusic.ogg \
  ${ASSET_BUILD_DIR}/data/audio/jumpsuit3.ogg \
  ${ASSET_BUILD_DIR}/data/audio/ninjaAttack7.ogg \
  ${ASSET_BUILD_DIR}/data/audio/actionHero3.ogg \
  ${ASSET_BUILD_DIR}/data/audio/warrior1.ogg \
  ${ASSET_BUILD_DIR}/data/audio/alienDeath.ogg \
  ${ASSET_BUILD_DIR}/data/audio/zoeAttack03.ogg \
  ${ASSET_BUILD_DIR}/data/audio/orchestraHit3.ogg \
  ${ASSET_BUILD_DIR}/data/audio/bunny4.ogg \
  ${ASSET_BUILD_DIR}/data/audio/boxingBell.ogg \
  ${ASSET_BUILD_DIR}/data/audio/assassinHit2.ogg \
  ${ASSET_BUILD_DIR}/data/audio/operaSinger4.ogg \
  ${ASSET_BUILD_DIR}/data/audio/error.ogg \
  ${ASSET_BUILD_DIR}/data/audio/click01.ogg \
  ${ASSET_BUILD_DIR}/data/audio/achievement.ogg \
  ${ASSET_BUILD_DIR}/data/audio/playerLeft.ogg \
  ${ASSET_BUILD_DIR}/data/audio/aliHit2.ogg \
  ${ASSET_BUILD_DIR}/data/audio/footImpact01.ogg \
  ${ASSET_BUILD_DIR}/data/audio/spazDeath01.ogg \
  ${ASSET_BUILD_DIR}/data/audio/dripity.ogg \
  ${ASSET_BUILD_DIR}/data/audio/stickyImpact.ogg \
  ${ASSET_BUILD_DIR}/data/audio/debrisFall.ogg \
  ${ASSET_BUILD_DIR}/data/audio/orchestraHit2.ogg \
  ${ASSET_BUILD_DIR}/data/audio/zoeAttack02.ogg \
  ${ASSET_BUILD_DIR}/data/audio/actionHero2.ogg \
  ${ASSET_BUILD_DIR}/data/audio/score.ogg \
  ${ASSET_BUILD_DIR}/data/audio/ninjaAttack6.ogg \
  ${ASSET_BUILD_DIR}/data/audio/witch1.ogg \
  ${ASSET_BUILD_DIR}/data/audio/punchStrong02.ogg \
  ${ASSET_BUILD_DIR}/data/audio/wizardHit2.ogg \
  ${ASSET_BUILD_DIR}/data/audio/robot1.ogg \
  ${ASSET_BUILD_DIR}/data/audio/jumpsuit2.ogg \
  ${ASSET_BUILD_DIR}/data/audio/jack05.ogg \
  ${ASSET_BUILD_DIR}/data/audio/superheroDeath.ogg \
  ${ASSET_BUILD_DIR}/data/audio/cowboy2.ogg \
  ${ASSET_BUILD_DIR}/data/audio/drumRoll.ogg \
  ${ASSET_BUILD_DIR}/data/audio/robot3.ogg \
  ${ASSET_BUILD_DIR}/data/audio/ninjaAttack4.ogg \
  ${ASSET_BUILD_DIR}/data/audio/alarm.ogg \
  ${ASSET_BUILD_DIR}/data/audio/witch3.ogg \
  ${ASSET_BUILD_DIR}/data/audio/warrior2.ogg \
  ${ASSET_BUILD_DIR}/data/audio/impactHard3.ogg \
  ${ASSET_BUILD_DIR}/data/audio/aliFall.ogg \
  ${ASSET_BUILD_DIR}/data/audio/spazEff.ogg \
  ${ASSET_BUILD_DIR}/data/audio/wizardFall.ogg \
  ${ASSET_BUILD_DIR}/data/audio/block.ogg \
  ${ASSET_BUILD_DIR}/data/audio/assassinHit1.ogg \
  ${ASSET_BUILD_DIR}/data/audio/footImpact03.ogg \
  ${ASSET_BUILD_DIR}/data/audio/trashRummage.ogg \
  ${ASSET_BUILD_DIR}/data/audio/footImpact02.ogg \
  ${ASSET_BUILD_DIR}/data/audio/aliHit1.ogg \
  ${ASSET_BUILD_DIR}/data/audio/ninjaDeath1.ogg \
  ${ASSET_BUILD_DIR}/data/audio/announceFive.ogg \
  ${ASSET_BUILD_DIR}/data/audio/zoeAttack01.ogg \
  ${ASSET_BUILD_DIR}/data/audio/actionHero1.ogg \
  ${ASSET_BUILD_DIR}/data/audio/impactHard2.ogg \
  ${ASSET_BUILD_DIR}/data/audio/warrior3.ogg \
  ${ASSET_BUILD_DIR}/data/audio/melDeath01.ogg \
  ${ASSET_BUILD_DIR}/data/audio/witch2.ogg \
  ${ASSET_BUILD_DIR}/data/audio/assassinFall.ogg \
  ${ASSET_BUILD_DIR}/data/audio/punchStrong01.ogg \
  ${ASSET_BUILD_DIR}/data/audio/ninjaAttack5.ogg \
  ${ASSET_BUILD_DIR}/data/audio/wizardHit1.ogg \
  ${ASSET_BUILD_DIR}/data/audio/robot2.ogg \
  ${ASSET_BUILD_DIR}/data/audio/announceSeven.ogg \
  ${ASSET_BUILD_DIR}/data/audio/jack06.ogg \
  ${ASSET_BUILD_DIR}/data/audio/cowboy3.ogg \
  ${ASSET_BUILD_DIR}/data/audio/jumpsuit1.ogg \
  ${ASSET_BUILD_DIR}/data/audio/bombDrop01.ogg \
  ${ASSET_BUILD_DIR}/data/audio/zoeJump03.ogg \
  ${ASSET_BUILD_DIR}/data/audio/warnBeeps.ogg \
  ${ASSET_BUILD_DIR}/data/audio/jack02.ogg \
  ${ASSET_BUILD_DIR}/data/audio/ninjaAttack1.ogg \
  ${ASSET_BUILD_DIR}/data/audio/bunny2.ogg \
  ${ASSET_BUILD_DIR}/data/audio/gladiatorDeath.ogg \
  ${ASSET_BUILD_DIR}/data/audio/operaSinger2.ogg \
  ${ASSET_BUILD_DIR}/data/audio/fanfare.ogg \
  ${ASSET_BUILD_DIR}/data/audio/wrestlerHit1.ogg \
  ${ASSET_BUILD_DIR}/data/audio/tickingCrazy.ogg \
  ${ASSET_BUILD_DIR}/data/audio/metalSkid.ogg \
  ${ASSET_BUILD_DIR}/data/audio/operaSinger3.ogg \
  ${ASSET_BUILD_DIR}/data/audio/actionHero4.ogg \
  ${ASSET_BUILD_DIR}/data/audio/zoeAttack04.ogg \
  ${ASSET_BUILD_DIR}/data/audio/orchestraHit4.ogg \
  ${ASSET_BUILD_DIR}/data/audio/bunny3.ogg \
  ${ASSET_BUILD_DIR}/data/audio/spazPickup01.ogg \
  ${ASSET_BUILD_DIR}/data/audio/wrestlerFall.ogg \
  ${ASSET_BUILD_DIR}/data/audio/cheer.ogg \
  ${ASSET_BUILD_DIR}/data/audio/zoeJump02.ogg \
  ${ASSET_BUILD_DIR}/data/audio/jack03.ogg \
  ${ASSET_BUILD_DIR}/data/audio/jumpsuit4.ogg \
  ${ASSET_BUILD_DIR}/data/audio/bombDrop02.ogg \
  ${ASSET_BUILD_DIR}/data/audio/cowboy4.ogg \
  ${ASSET_BUILD_DIR}/data/audio/jack01.ogg \
  ${ASSET_BUILD_DIR}/data/audio/grandRompMusic.ogg \
  ${ASSET_BUILD_DIR}/data/audio/ninjaAttack2.ogg \
  ${ASSET_BUILD_DIR}/data/audio/kronk8.ogg \
  ${ASSET_BUILD_DIR}/data/audio/bunny1.ogg \
  ${ASSET_BUILD_DIR}/data/audio/warrior4.ogg \
  ${ASSET_BUILD_DIR}/data/audio/ding.ogg \
  ${ASSET_BUILD_DIR}/data/audio/operaSinger1.ogg \
  ${ASSET_BUILD_DIR}/data/audio/wrestlerHit2.ogg \
  ${ASSET_BUILD_DIR}/data/audio/bonesFall.ogg \
  ${ASSET_BUILD_DIR}/data/audio/scoresEpicMusic.ogg \
  ${ASSET_BUILD_DIR}/data/audio/sportsMusic.ogg \
  ${ASSET_BUILD_DIR}/data/audio/witchDeath.ogg \
  ${ASSET_BUILD_DIR}/data/audio/kronk9.ogg \
  ${ASSET_BUILD_DIR}/data/audio/ninjaAttack3.ogg \
  ${ASSET_BUILD_DIR}/data/audio/assassinDeath.ogg \
  ${ASSET_BUILD_DIR}/data/audio/witch4.ogg \
  ${ASSET_BUILD_DIR}/data/audio/zoeJump01.ogg \
  ${ASSET_BUILD_DIR}/data/audio/robot4.ogg \
  ${ASSET_BUILD_DIR}/data/audio/gravelSkid.ogg


TEX2D_DDS_TARGETS = \
  ${ASSET_BUILD_DIR}/data/textures/cyborgIconColorMask.dds \
  ${ASSET_BUILD_DIR}/data/textures/chestOpenIcon.dds \
  ${ASSET_BUILD_DIR}/data/textures/analogStick.dds \
  ${ASSET_BUILD_DIR}/data/textures/circleOutline.dds \
  ${ASSET_BUILD_DIR}/data/textures/white.dds \
  ${ASSET_BUILD_DIR}/data/textures/medalBronze.dds \
  ${ASSET_BUILD_DIR}/data/textures/slash.dds \
  ${ASSET_BUILD_DIR}/data/textures/arrow.dds \
  ${ASSET_BUILD_DIR}/data/textures/ouyaIcon.dds \
  ${ASSET_BUILD_DIR}/data/textures/eyeColor.dds \
  ${ASSET_BUILD_DIR}/data/textures/achievementMedalLarge.dds \
  ${ASSET_BUILD_DIR}/data/textures/cowboyIconColorMask.dds \
  ${ASSET_BUILD_DIR}/data/textures/wings.dds \
  ${ASSET_BUILD_DIR}/data/textures/roundaboutPreview.dds \
  ${ASSET_BUILD_DIR}/data/textures/warriorIcon.dds \
  ${ASSET_BUILD_DIR}/data/textures/windowHSmallVMed.dds \
  ${ASSET_BUILD_DIR}/data/textures/ninjaIconColorMask.dds \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSharpest_+z.dds \
  ${ASSET_BUILD_DIR}/data/textures/stepRightUpLevelColor.dds \
  ${ASSET_BUILD_DIR}/data/textures/fontSmall5.dds \
  ${ASSET_BUILD_DIR}/data/textures/bombButton.dds \
  ${ASSET_BUILD_DIR}/data/textures/aliIconColorMask.dds \
  ${ASSET_BUILD_DIR}/data/textures/chTitleChar2.dds \
  ${ASSET_BUILD_DIR}/data/textures/achievementOnslaught.dds \
  ${ASSET_BUILD_DIR}/data/textures/smoke.dds \
  ${ASSET_BUILD_DIR}/data/textures/lakeFrigidReflections.dds \
  ${ASSET_BUILD_DIR}/data/textures/bunnyColor.dds \
  ${ASSET_BUILD_DIR}/data/textures/leftButton.dds \
  ${ASSET_BUILD_DIR}/data/textures/hockeyStadium.dds \
  ${ASSET_BUILD_DIR}/data/textures/cowboyIcon.dds \
  ${ASSET_BUILD_DIR}/data/textures/lakeFrigid.dds \
  ${ASSET_BUILD_DIR}/data/textures/startButton.dds \
  ${ASSET_BUILD_DIR}/data/textures/footballStadium.dds \
  ${ASSET_BUILD_DIR}/data/textures/crossOutMask.dds \
  ${ASSET_BUILD_DIR}/data/textures/bonesIconColorMask.dds \
  ${ASSET_BUILD_DIR}/data/textures/operaSingerIconColorMask.dds \
  ${ASSET_BUILD_DIR}/data/textures/lakeFrigidPreview.dds \
  ${ASSET_BUILD_DIR}/data/textures/alienIcon.dds \
  ${ASSET_BUILD_DIR}/data/textures/oldLadyColor.dds \
  ${ASSET_BUILD_DIR}/data/textures/ouyaAButton.dds \
  ${ASSET_BUILD_DIR}/data/textures/eggTex3.dds \
  ${ASSET_BUILD_DIR}/data/textures/cyborgIcon.dds \
  ${ASSET_BUILD_DIR}/data/textures/actionHeroColor.dds \
  ${ASSET_BUILD_DIR}/data/textures/achievementTeamPlayer.dds \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSoft_+x.dds \
  ${ASSET_BUILD_DIR}/data/textures/fontExtras3.dds \
  ${ASSET_BUILD_DIR}/data/textures/buttonBomb.dds \
  ${ASSET_BUILD_DIR}/data/textures/star.dds \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSharpest_-y.dds \
  ${ASSET_BUILD_DIR}/data/textures/achievementSharingIsCaring.dds \
  ${ASSET_BUILD_DIR}/data/textures/fontSmall3.dds \
  ${ASSET_BUILD_DIR}/data/textures/powerupSpeed.dds \
  ${ASSET_BUILD_DIR}/data/textures/vrFillMound.dds \
  ${ASSET_BUILD_DIR}/data/textures/agentIconColorMask.dds \
  ${ASSET_BUILD_DIR}/data/textures/kronkIcon.dds \
  ${ASSET_BUILD_DIR}/data/textures/oldLadyIcon.dds \
  ${ASSET_BUILD_DIR}/data/textures/chTitleChar4.dds \
  ${ASSET_BUILD_DIR}/data/textures/nextLevelIcon.dds \
  ${ASSET_BUILD_DIR}/data/textures/gameCircleIcon.dds \
  ${ASSET_BUILD_DIR}/data/textures/bonesIcon.dds \
  ${ASSET_BUILD_DIR}/data/textures/bearIcon.dds \
  ${ASSET_BUILD_DIR}/data/textures/towerDPreview.dds \
  ${ASSET_BUILD_DIR}/data/textures/achievementTNT.dds \
  ${ASSET_BUILD_DIR}/data/textures/medalGold.dds \
  ${ASSET_BUILD_DIR}/data/textures/circleZigZag.dds \
  ${ASSET_BUILD_DIR}/data/textures/bunnyColorMask.dds \
  ${ASSET_BUILD_DIR}/data/textures/black.dds \
  ${ASSET_BUILD_DIR}/data/textures/menuIcon.dds \
  ${ASSET_BUILD_DIR}/data/textures/file.dds \
  ${ASSET_BUILD_DIR}/data/textures/logIcon.dds \
  ${ASSET_BUILD_DIR}/data/textures/controllerIcon.dds \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSharper_-y.dds \
  ${ASSET_BUILD_DIR}/data/textures/operaSingerColorMask.dds \
  ${ASSET_BUILD_DIR}/data/textures/achievementFootballShutout.dds \
  ${ASSET_BUILD_DIR}/data/textures/reflectionPowerup_-x.dds \
  ${ASSET_BUILD_DIR}/data/textures/achievementsIcon.dds \
  ${ASSET_BUILD_DIR}/data/textures/cowboyColor.dds \
  ${ASSET_BUILD_DIR}/data/textures/wrestlerIconColorMask.dds \
  ${ASSET_BUILD_DIR}/data/textures/googlePlayAchievementsIcon.dds \
  ${ASSET_BUILD_DIR}/data/textures/alienIconColorMask.dds \
  ${ASSET_BUILD_DIR}/data/textures/ticketRollBig.dds \
  ${ASSET_BUILD_DIR}/data/textures/wrestlerIcon.dds \
  ${ASSET_BUILD_DIR}/data/textures/egg1.dds \
  ${ASSET_BUILD_DIR}/data/textures/gameCenterIcon.dds \
  ${ASSET_BUILD_DIR}/data/textures/landMineLit.dds \
  ${ASSET_BUILD_DIR}/data/textures/achievementWall.dds \
  ${ASSET_BUILD_DIR}/data/textures/achievementMedalMedium.dds \
  ${ASSET_BUILD_DIR}/data/textures/reflectionChar_-x.dds \
  ${ASSET_BUILD_DIR}/data/textures/softRectVertical.dds \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSharper_+z.dds \
  ${ASSET_BUILD_DIR}/data/textures/wizardIcon.dds \
  ${ASSET_BUILD_DIR}/data/textures/mapPreviewMask.dds \
  ${ASSET_BUILD_DIR}/data/textures/nub.dds \
  ${ASSET_BUILD_DIR}/data/textures/empty.dds \
  ${ASSET_BUILD_DIR}/data/textures/frostyIconColorMask.dds \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSharp_-x.dds \
  ${ASSET_BUILD_DIR}/data/textures/bombColorIce.dds \
  ${ASSET_BUILD_DIR}/data/textures/jumpsuitIcon.dds \
  ${ASSET_BUILD_DIR}/data/textures/footballStadiumPreview.dds \
  ${ASSET_BUILD_DIR}/data/textures/pixieIconColorMask.dds \
  ${ASSET_BUILD_DIR}/data/textures/achievementEmpty.dds \
  ${ASSET_BUILD_DIR}/data/textures/wrestlerColor.dds \
  ${ASSET_BUILD_DIR}/data/textures/shield.dds \
  ${ASSET_BUILD_DIR}/data/textures/iconOnslaught.dds \
  ${ASSET_BUILD_DIR}/data/textures/replayIcon.dds \
  ${ASSET_BUILD_DIR}/data/textures/powerupHealth.dds \
  ${ASSET_BUILD_DIR}/data/textures/bg.dds \
  ${ASSET_BUILD_DIR}/data/textures/chTitleChar3.dds \
  ${ASSET_BUILD_DIR}/data/textures/textClearButton.dds \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSoft_-z.dds \
  ${ASSET_BUILD_DIR}/data/textures/fontSmall4.dds \
  ${ASSET_BUILD_DIR}/data/textures/warriorColor.dds \
  ${ASSET_BUILD_DIR}/data/textures/light.dds \
  ${ASSET_BUILD_DIR}/data/textures/santaColor.dds \
  ${ASSET_BUILD_DIR}/data/textures/jackColor.dds \
  ${ASSET_BUILD_DIR}/data/textures/aliSplash.dds \
  ${ASSET_BUILD_DIR}/data/textures/scorch.dds \
  ${ASSET_BUILD_DIR}/data/textures/zoeIcon.dds \
  ${ASSET_BUILD_DIR}/data/textures/bonesColorMask.dds \
  ${ASSET_BUILD_DIR}/data/textures/pixieColor.dds \
  ${ASSET_BUILD_DIR}/data/textures/actionHeroIconColorMask.dds \
  ${ASSET_BUILD_DIR}/data/textures/treesColor.dds \
  ${ASSET_BUILD_DIR}/data/textures/neoSpazColorMask.dds \
  ${ASSET_BUILD_DIR}/data/textures/superheroIcon.dds \
  ${ASSET_BUILD_DIR}/data/textures/achievementOffYouGo.dds \
  ${ASSET_BUILD_DIR}/data/textures/tipTopBGColor.dds \
  ${ASSET_BUILD_DIR}/data/textures/robotColor.dds \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSharpest_-x.dds \
  ${ASSET_BUILD_DIR}/data/textures/menuButton.dds \
  ${ASSET_BUILD_DIR}/data/textures/powerupStickyBombs.dds \
  ${ASSET_BUILD_DIR}/data/textures/ninjaIcon.dds \
  ${ASSET_BUILD_DIR}/data/textures/witchColorMask.dds \
  ${ASSET_BUILD_DIR}/data/textures/cowboyColorMask.dds \
  ${ASSET_BUILD_DIR}/data/textures/operaSingerIcon.dds \
  ${ASSET_BUILD_DIR}/data/textures/achievementBoxer.dds \
  ${ASSET_BUILD_DIR}/data/textures/eggTex2.dds \
  ${ASSET_BUILD_DIR}/data/textures/rampageBGColor.dds \
  ${ASSET_BUILD_DIR}/data/textures/fontExtras2.dds \
  ${ASSET_BUILD_DIR}/data/textures/rampageLevelColor.dds \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSoft_+y.dds \
  ${ASSET_BUILD_DIR}/data/textures/ticketRolls.dds \
  ${ASSET_BUILD_DIR}/data/textures/natureBackgroundColor.dds \
  ${ASSET_BUILD_DIR}/data/textures/santaIconColorMask.dds \
  ${ASSET_BUILD_DIR}/data/textures/reflectionPowerup_+z.dds \
  ${ASSET_BUILD_DIR}/data/textures/characterIconMask.dds \
  ${ASSET_BUILD_DIR}/data/textures/aliColor.dds \
  ${ASSET_BUILD_DIR}/data/textures/ninjaColorMask.dds \
  ${ASSET_BUILD_DIR}/data/textures/buttonPickUp.dds \
  ${ASSET_BUILD_DIR}/data/textures/chTitleChar5.dds \
  ${ASSET_BUILD_DIR}/data/textures/bigGPreview.dds \
  ${ASSET_BUILD_DIR}/data/textures/hockeyStadiumPreview.dds \
  ${ASSET_BUILD_DIR}/data/textures/achievementMedalSmall.dds \
  ${ASSET_BUILD_DIR}/data/textures/fontSmall2.dds \
  ${ASSET_BUILD_DIR}/data/textures/achievementOutline.dds \
  ${ASSET_BUILD_DIR}/data/textures/levelIcon.dds \
  ${ASSET_BUILD_DIR}/data/textures/googlePlayGamesIcon.dds \
  ${ASSET_BUILD_DIR}/data/textures/gladiatorColorMask.dds \
  ${ASSET_BUILD_DIR}/data/textures/boxingGlovesColor.dds \
  ${ASSET_BUILD_DIR}/data/textures/ouyaOButton.dds \
  ${ASSET_BUILD_DIR}/data/textures/leaderboardsIcon.dds \
  ${ASSET_BUILD_DIR}/data/textures/puckColor.dds \
  ${ASSET_BUILD_DIR}/data/textures/reflectionChar_+z.dds \
  ${ASSET_BUILD_DIR}/data/textures/penguinColor.dds \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSharper_-x.dds \
  ${ASSET_BUILD_DIR}/data/textures/googlePlayLeaderboardsIcon.dds \
  ${ASSET_BUILD_DIR}/data/textures/scrollWidget.dds \
  ${ASSET_BUILD_DIR}/data/textures/courtyardPreview.dds \
  ${ASSET_BUILD_DIR}/data/textures/aliColorMask.dds \
  ${ASSET_BUILD_DIR}/data/textures/penguinColorMask.dds \
  ${ASSET_BUILD_DIR}/data/textures/witchIcon.dds \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSharp_+z.dds \
  ${ASSET_BUILD_DIR}/data/textures/graphicsIcon.dds \
  ${ASSET_BUILD_DIR}/data/textures/agentIcon.dds \
  ${ASSET_BUILD_DIR}/data/textures/fontExtras4.dds \
  ${ASSET_BUILD_DIR}/data/textures/reflectionPowerup_-y.dds \
  ${ASSET_BUILD_DIR}/data/textures/storeIcon.dds \
  ${ASSET_BUILD_DIR}/data/textures/doomShroomPreview.dds \
  ${ASSET_BUILD_DIR}/data/textures/null.dds \
  ${ASSET_BUILD_DIR}/data/textures/backIcon.dds \
  ${ASSET_BUILD_DIR}/data/textures/cyborgColor.dds \
  ${ASSET_BUILD_DIR}/data/textures/monkeyFaceLevelColor.dds \
  ${ASSET_BUILD_DIR}/data/textures/santaIcon.dds \
  ${ASSET_BUILD_DIR}/data/textures/alwaysLandBGColor.dds \
  ${ASSET_BUILD_DIR}/data/textures/roundaboutLevelColor.dds \
  ${ASSET_BUILD_DIR}/data/textures/robotIcon.dds \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSharp_-y.dds \
  ${ASSET_BUILD_DIR}/data/textures/bunnyIcon.dds \
  ${ASSET_BUILD_DIR}/data/textures/circleShadow.dds \
  ${ASSET_BUILD_DIR}/data/textures/flagPoleColor.dds \
  ${ASSET_BUILD_DIR}/data/textures/ouyaUButton.dds \
  ${ASSET_BUILD_DIR}/data/textures/reflectionChar_-y.dds \
  ${ASSET_BUILD_DIR}/data/textures/achievementInControl.dds \
  ${ASSET_BUILD_DIR}/data/textures/wizardColorMask.dds \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSharpest_+x.dds \
  ${ASSET_BUILD_DIR}/data/textures/neoSpazColor.dds \
  ${ASSET_BUILD_DIR}/data/textures/zigZagLevelColor.dds \
  ${ASSET_BUILD_DIR}/data/textures/thePadPreview.dds \
  ${ASSET_BUILD_DIR}/data/textures/superheroIconColorMask.dds \
  ${ASSET_BUILD_DIR}/data/textures/fontSmall7.dds \
  ${ASSET_BUILD_DIR}/data/textures/ticketRoll.dds \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSoft_-y.dds \
  ${ASSET_BUILD_DIR}/data/textures/playerLineup.dds \
  ${ASSET_BUILD_DIR}/data/textures/storeCharacterEaster.dds \
  ${ASSET_BUILD_DIR}/data/textures/coin.dds \
  ${ASSET_BUILD_DIR}/data/textures/circleOutlineNoAlpha.dds \
  ${ASSET_BUILD_DIR}/data/textures/scorchBig.dds \
  ${ASSET_BUILD_DIR}/data/textures/logoEaster.dds \
  ${ASSET_BUILD_DIR}/data/textures/warriorColorMask.dds \
  ${ASSET_BUILD_DIR}/data/textures/assassinColor.dds \
  ${ASSET_BUILD_DIR}/data/textures/bombStickyColor.dds \
  ${ASSET_BUILD_DIR}/data/textures/eggTex1.dds \
  ${ASSET_BUILD_DIR}/data/textures/gladiatorIconColorMask.dds \
  ${ASSET_BUILD_DIR}/data/textures/melColorMask.dds \
  ${ASSET_BUILD_DIR}/data/textures/thePadLevelColor.dds \
  ${ASSET_BUILD_DIR}/data/textures/wizardIconColorMask.dds \
  ${ASSET_BUILD_DIR}/data/textures/bar.dds \
  ${ASSET_BUILD_DIR}/data/textures/zoeIconColorMask.dds \
  ${ASSET_BUILD_DIR}/data/textures/windowHSmallVSmall.dds \
  ${ASSET_BUILD_DIR}/data/textures/circleNoAlpha.dds \
  ${ASSET_BUILD_DIR}/data/textures/gladiatorIcon.dds \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSoft_+z.dds \
  ${ASSET_BUILD_DIR}/data/textures/achievementRunaround.dds \
  ${ASSET_BUILD_DIR}/data/textures/wizardColor.dds \
  ${ASSET_BUILD_DIR}/data/textures/touchArrowsActions.dds \
  ${ASSET_BUILD_DIR}/data/textures/advancedIcon.dds \
  ${ASSET_BUILD_DIR}/data/textures/softRect2.dds \
  ${ASSET_BUILD_DIR}/data/textures/achievementMine.dds \
  ${ASSET_BUILD_DIR}/data/textures/rightButton.dds \
  ${ASSET_BUILD_DIR}/data/textures/touchArrows.dds \
  ${ASSET_BUILD_DIR}/data/textures/cyborgColorMask.dds \
  ${ASSET_BUILD_DIR}/data/textures/jumpsuitIconColorMask.dds \
  ${ASSET_BUILD_DIR}/data/textures/bridgitPreview.dds \
  ${ASSET_BUILD_DIR}/data/textures/ninjaColor.dds \
  ${ASSET_BUILD_DIR}/data/textures/santaColorMask.dds \
  ${ASSET_BUILD_DIR}/data/textures/storeCharacter.dds \
  ${ASSET_BUILD_DIR}/data/textures/flagColor.dds \
  ${ASSET_BUILD_DIR}/data/textures/cragCastlePreview.dds \
  ${ASSET_BUILD_DIR}/data/textures/frameInset.dds \
  ${ASSET_BUILD_DIR}/data/textures/lock.dds \
  ${ASSET_BUILD_DIR}/data/textures/agentColor.dds \
  ${ASSET_BUILD_DIR}/data/textures/achievementGotTheMoves.dds \
  ${ASSET_BUILD_DIR}/data/textures/buttonPunch.dds \
  ${ASSET_BUILD_DIR}/data/textures/settingsIcon.dds \
  ${ASSET_BUILD_DIR}/data/textures/rgbStripes.dds \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSharp_+y.dds \
  ${ASSET_BUILD_DIR}/data/textures/powerupImpactBombs.dds \
  ${ASSET_BUILD_DIR}/data/textures/bigG.dds \
  ${ASSET_BUILD_DIR}/data/textures/melIconColorMask.dds \
  ${ASSET_BUILD_DIR}/data/textures/reflectionChar_+y.dds \
  ${ASSET_BUILD_DIR}/data/textures/multiplayerExamples.dds \
  ${ASSET_BUILD_DIR}/data/textures/actionButtons.dds \
  ${ASSET_BUILD_DIR}/data/textures/melIcon.dds \
  ${ASSET_BUILD_DIR}/data/textures/oldLadyIconColorMask.dds \
  ${ASSET_BUILD_DIR}/data/textures/robotIconColorMask.dds \
  ${ASSET_BUILD_DIR}/data/textures/monkeyFacePreview.dds \
  ${ASSET_BUILD_DIR}/data/textures/achievementDualWielding.dds \
  ${ASSET_BUILD_DIR}/data/textures/folder.dds \
  ${ASSET_BUILD_DIR}/data/textures/frostyColorMask.dds \
  ${ASSET_BUILD_DIR}/data/textures/kronkIconColorMask.dds \
  ${ASSET_BUILD_DIR}/data/textures/fontBig.dds \
  ${ASSET_BUILD_DIR}/data/textures/fontSmall1.dds \
  ${ASSET_BUILD_DIR}/data/textures/shadowSoft.dds \
  ${ASSET_BUILD_DIR}/data/textures/powerupLandMines.dds \
  ${ASSET_BUILD_DIR}/data/textures/stepRightUpPreview.dds \
  ${ASSET_BUILD_DIR}/data/textures/bearIconColorMask.dds \
  ${ASSET_BUILD_DIR}/data/textures/kronk.dds \
  ${ASSET_BUILD_DIR}/data/textures/downButton.dds \
  ${ASSET_BUILD_DIR}/data/textures/bombColor.dds \
  ${ASSET_BUILD_DIR}/data/textures/logo.dds \
  ${ASSET_BUILD_DIR}/data/textures/reflectionPowerup_+y.dds \
  ${ASSET_BUILD_DIR}/data/textures/zoeColorMask.dds \
  ${ASSET_BUILD_DIR}/data/textures/jumpsuitColorMask.dds \
  ${ASSET_BUILD_DIR}/data/textures/penguinIcon.dds \
  ${ASSET_BUILD_DIR}/data/textures/powerupPunch.dds \
  ${ASSET_BUILD_DIR}/data/textures/shadow.dds \
  ${ASSET_BUILD_DIR}/data/textures/reflectionChar_-z.dds \
  ${ASSET_BUILD_DIR}/data/textures/assassinIcon.dds \
  ${ASSET_BUILD_DIR}/data/textures/impactBombColor.dds \
  ${ASSET_BUILD_DIR}/data/textures/storeCharacterXmas.dds \
  ${ASSET_BUILD_DIR}/data/textures/jackIcon.dds \
  ${ASSET_BUILD_DIR}/data/textures/pixieIcon.dds \
  ${ASSET_BUILD_DIR}/data/textures/jumpsuitColor.dds \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSharper_+x.dds \
  ${ASSET_BUILD_DIR}/data/textures/jackColorMask.dds \
  ${ASSET_BUILD_DIR}/data/textures/shrapnel1Color.dds \
  ${ASSET_BUILD_DIR}/data/textures/witchColor.dds \
  ${ASSET_BUILD_DIR}/data/textures/achievementFreeLoader.dds \
  ${ASSET_BUILD_DIR}/data/textures/zoeColor.dds \
  ${ASSET_BUILD_DIR}/data/textures/alienColor.dds \
  ${ASSET_BUILD_DIR}/data/textures/inventoryIcon.dds \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSharp_-z.dds \
  ${ASSET_BUILD_DIR}/data/textures/glow.dds \
  ${ASSET_BUILD_DIR}/data/textures/usersButton.dds \
  ${ASSET_BUILD_DIR}/data/textures/reflectionPowerup_-z.dds \
  ${ASSET_BUILD_DIR}/data/textures/melColor.dds \
  ${ASSET_BUILD_DIR}/data/textures/aliControllerQR.dds \
  ${ASSET_BUILD_DIR}/data/textures/frostyIcon.dds \
  ${ASSET_BUILD_DIR}/data/textures/achievementFootballVictory.dds \
  ${ASSET_BUILD_DIR}/data/textures/tickets.dds \
  ${ASSET_BUILD_DIR}/data/textures/cursor.dds \
  ${ASSET_BUILD_DIR}/data/textures/egg3.dds \
  ${ASSET_BUILD_DIR}/data/textures/crossOut.dds \
  ${ASSET_BUILD_DIR}/data/textures/bonesColor.dds \
  ${ASSET_BUILD_DIR}/data/textures/achievementCrossHair.dds \
  ${ASSET_BUILD_DIR}/data/textures/actionHeroColorMask.dds \
  ${ASSET_BUILD_DIR}/data/textures/chTitleChar1.dds \
  ${ASSET_BUILD_DIR}/data/textures/heart.dds \
  ${ASSET_BUILD_DIR}/data/textures/fontExtras.dds \
  ${ASSET_BUILD_DIR}/data/textures/penguinIconColorMask.dds \
  ${ASSET_BUILD_DIR}/data/textures/eyeColorTintMask.dds \
  ${ASSET_BUILD_DIR}/data/textures/aliIcon.dds \
  ${ASSET_BUILD_DIR}/data/textures/chestIconMulti.dds \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSoft_-x.dds \
  ${ASSET_BUILD_DIR}/data/textures/uiAtlas.dds \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSharpest_+y.dds \
  ${ASSET_BUILD_DIR}/data/textures/cragCastleLevelColor.dds \
  ${ASSET_BUILD_DIR}/data/textures/assassinColorMask.dds \
  ${ASSET_BUILD_DIR}/data/textures/bridgitLevelColor.dds \
  ${ASSET_BUILD_DIR}/data/textures/fontSmall6.dds \
  ${ASSET_BUILD_DIR}/data/textures/towerDLevelColor.dds \
  ${ASSET_BUILD_DIR}/data/textures/ouyaYButton.dds \
  ${ASSET_BUILD_DIR}/data/textures/lightSharp.dds \
  ${ASSET_BUILD_DIR}/data/textures/buttonSquare.dds \
  ${ASSET_BUILD_DIR}/data/textures/softRect.dds \
  ${ASSET_BUILD_DIR}/data/textures/powerupIceBombs.dds \
  ${ASSET_BUILD_DIR}/data/textures/jackIconColorMask.dds \
  ${ASSET_BUILD_DIR}/data/textures/audioIcon.dds \
  ${ASSET_BUILD_DIR}/data/textures/tv.dds \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSharpest_-z.dds \
  ${ASSET_BUILD_DIR}/data/textures/warriorIconColorMask.dds \
  ${ASSET_BUILD_DIR}/data/textures/googlePlusSignInButton.dds \
  ${ASSET_BUILD_DIR}/data/textures/circle.dds \
  ${ASSET_BUILD_DIR}/data/textures/neoSpazIconColorMask.dds \
  ${ASSET_BUILD_DIR}/data/textures/medalComplete.dds \
  ${ASSET_BUILD_DIR}/data/textures/alwaysLandLevelColor.dds \
  ${ASSET_BUILD_DIR}/data/textures/alwaysLandPreview.dds \
  ${ASSET_BUILD_DIR}/data/textures/egg4.dds \
  ${ASSET_BUILD_DIR}/data/textures/wrestlerColorMask.dds \
  ${ASSET_BUILD_DIR}/data/textures/superheroColorMask.dds \
  ${ASSET_BUILD_DIR}/data/textures/gladiatorColor.dds \
  ${ASSET_BUILD_DIR}/data/textures/aliBSRemoteIOSQR.dds \
  ${ASSET_BUILD_DIR}/data/textures/bearColorMask.dds \
  ${ASSET_BUILD_DIR}/data/textures/doomShroomLevelColor.dds \
  ${ASSET_BUILD_DIR}/data/textures/powerupBomb.dds \
  ${ASSET_BUILD_DIR}/data/textures/chestIcon.dds \
  ${ASSET_BUILD_DIR}/data/textures/upButton.dds \
  ${ASSET_BUILD_DIR}/data/textures/iconRunaround.dds \
  ${ASSET_BUILD_DIR}/data/textures/doomShroomBGColor.dds \
  ${ASSET_BUILD_DIR}/data/textures/superheroColor.dds \
  ${ASSET_BUILD_DIR}/data/textures/landMine.dds \
  ${ASSET_BUILD_DIR}/data/textures/buttonJump.dds \
  ${ASSET_BUILD_DIR}/data/textures/sparks.dds \
  ${ASSET_BUILD_DIR}/data/textures/explosion.dds \
  ${ASSET_BUILD_DIR}/data/textures/tipTopLevelColor.dds \
  ${ASSET_BUILD_DIR}/data/textures/bunnyIconColorMask.dds \
  ${ASSET_BUILD_DIR}/data/textures/reflectionChar_+x.dds \
  ${ASSET_BUILD_DIR}/data/textures/ticketsMore.dds \
  ${ASSET_BUILD_DIR}/data/textures/pixieColorMask.dds \
  ${ASSET_BUILD_DIR}/data/textures/medalSilver.dds \
  ${ASSET_BUILD_DIR}/data/textures/neoSpazIcon.dds \
  ${ASSET_BUILD_DIR}/data/textures/meter.dds \
  ${ASSET_BUILD_DIR}/data/textures/scrollWidgetGlow.dds \
  ${ASSET_BUILD_DIR}/data/textures/achievementFlawlessVictory.dds \
  ${ASSET_BUILD_DIR}/data/textures/zigzagPreview.dds \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSharper_-z.dds \
  ${ASSET_BUILD_DIR}/data/textures/alienColorMask.dds \
  ${ASSET_BUILD_DIR}/data/textures/powerupShield.dds \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSharp_+x.dds \
  ${ASSET_BUILD_DIR}/data/textures/chestIconEmpty.dds \
  ${ASSET_BUILD_DIR}/data/textures/agentColorMask.dds \
  ${ASSET_BUILD_DIR}/data/textures/reflectionPowerup_+x.dds \
  ${ASSET_BUILD_DIR}/data/textures/witchIconColorMask.dds \
  ${ASSET_BUILD_DIR}/data/textures/kronkColorMask.dds \
  ${ASSET_BUILD_DIR}/data/textures/menuBG.dds \
  ${ASSET_BUILD_DIR}/data/textures/fontSmall0.dds \
  ${ASSET_BUILD_DIR}/data/textures/assassinIconColorMask.dds \
  ${ASSET_BUILD_DIR}/data/textures/bearColor.dds \
  ${ASSET_BUILD_DIR}/data/textures/operaSingerColor.dds \
  ${ASSET_BUILD_DIR}/data/textures/rampageBGColor2.dds \
  ${ASSET_BUILD_DIR}/data/textures/fuse.dds \
  ${ASSET_BUILD_DIR}/data/textures/frostyColor.dds \
  ${ASSET_BUILD_DIR}/data/textures/achievementSuperPunch.dds \
  ${ASSET_BUILD_DIR}/data/textures/tipTopPreview.dds \
  ${ASSET_BUILD_DIR}/data/textures/googlePlusIcon.dds \
  ${ASSET_BUILD_DIR}/data/textures/powerupCurse.dds \
  ${ASSET_BUILD_DIR}/data/textures/trophy.dds \
  ${ASSET_BUILD_DIR}/data/textures/courtyardLevelColor.dds \
  ${ASSET_BUILD_DIR}/data/textures/oldLadyColorMask.dds \
  ${ASSET_BUILD_DIR}/data/textures/rampagePreview.dds \
  ${ASSET_BUILD_DIR}/data/textures/cuteSpaz.dds \
  ${ASSET_BUILD_DIR}/data/textures/lightSoft.dds \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSharper_+y.dds \
  ${ASSET_BUILD_DIR}/data/textures/uiAtlas2.dds \
  ${ASSET_BUILD_DIR}/data/textures/egg2.dds \
  ${ASSET_BUILD_DIR}/data/textures/shadowSharp.dds \
  ${ASSET_BUILD_DIR}/data/textures/tnt.dds \
  ${ASSET_BUILD_DIR}/data/textures/actionHeroIcon.dds \
  ${ASSET_BUILD_DIR}/data/textures/robotColorMask.dds \
  ${ASSET_BUILD_DIR}/data/textures/impactBombColorLit.dds \
  ${ASSET_BUILD_DIR}/data/textures/achievementStayinAlive.dds


TEX2D_PVR_TARGETS = \
  ${ASSET_BUILD_DIR}/data/textures/cyborgIconColorMask.pvr \
  ${ASSET_BUILD_DIR}/data/textures/chestOpenIcon.pvr \
  ${ASSET_BUILD_DIR}/data/textures/analogStick.pvr \
  ${ASSET_BUILD_DIR}/data/textures/circleOutline.pvr \
  ${ASSET_BUILD_DIR}/data/textures/white.pvr \
  ${ASSET_BUILD_DIR}/data/textures/medalBronze.pvr \
  ${ASSET_BUILD_DIR}/data/textures/slash.pvr \
  ${ASSET_BUILD_DIR}/data/textures/arrow.pvr \
  ${ASSET_BUILD_DIR}/data/textures/ouyaIcon.pvr \
  ${ASSET_BUILD_DIR}/data/textures/eyeColor.pvr \
  ${ASSET_BUILD_DIR}/data/textures/achievementMedalLarge.pvr \
  ${ASSET_BUILD_DIR}/data/textures/cowboyIconColorMask.pvr \
  ${ASSET_BUILD_DIR}/data/textures/wings.pvr \
  ${ASSET_BUILD_DIR}/data/textures/roundaboutPreview.pvr \
  ${ASSET_BUILD_DIR}/data/textures/warriorIcon.pvr \
  ${ASSET_BUILD_DIR}/data/textures/windowHSmallVMed.pvr \
  ${ASSET_BUILD_DIR}/data/textures/ninjaIconColorMask.pvr \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSharpest_+z.pvr \
  ${ASSET_BUILD_DIR}/data/textures/stepRightUpLevelColor.pvr \
  ${ASSET_BUILD_DIR}/data/textures/fontSmall5.pvr \
  ${ASSET_BUILD_DIR}/data/textures/bombButton.pvr \
  ${ASSET_BUILD_DIR}/data/textures/aliIconColorMask.pvr \
  ${ASSET_BUILD_DIR}/data/textures/chTitleChar2.pvr \
  ${ASSET_BUILD_DIR}/data/textures/achievementOnslaught.pvr \
  ${ASSET_BUILD_DIR}/data/textures/smoke.pvr \
  ${ASSET_BUILD_DIR}/data/textures/lakeFrigidReflections.pvr \
  ${ASSET_BUILD_DIR}/data/textures/bunnyColor.pvr \
  ${ASSET_BUILD_DIR}/data/textures/leftButton.pvr \
  ${ASSET_BUILD_DIR}/data/textures/hockeyStadium.pvr \
  ${ASSET_BUILD_DIR}/data/textures/cowboyIcon.pvr \
  ${ASSET_BUILD_DIR}/data/textures/lakeFrigid.pvr \
  ${ASSET_BUILD_DIR}/data/textures/startButton.pvr \
  ${ASSET_BUILD_DIR}/data/textures/footballStadium.pvr \
  ${ASSET_BUILD_DIR}/data/textures/crossOutMask.pvr \
  ${ASSET_BUILD_DIR}/data/textures/bonesIconColorMask.pvr \
  ${ASSET_BUILD_DIR}/data/textures/operaSingerIconColorMask.pvr \
  ${ASSET_BUILD_DIR}/data/textures/lakeFrigidPreview.pvr \
  ${ASSET_BUILD_DIR}/data/textures/alienIcon.pvr \
  ${ASSET_BUILD_DIR}/data/textures/oldLadyColor.pvr \
  ${ASSET_BUILD_DIR}/data/textures/ouyaAButton.pvr \
  ${ASSET_BUILD_DIR}/data/textures/eggTex3.pvr \
  ${ASSET_BUILD_DIR}/data/textures/cyborgIcon.pvr \
  ${ASSET_BUILD_DIR}/data/textures/actionHeroColor.pvr \
  ${ASSET_BUILD_DIR}/data/textures/achievementTeamPlayer.pvr \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSoft_+x.pvr \
  ${ASSET_BUILD_DIR}/data/textures/fontExtras3.pvr \
  ${ASSET_BUILD_DIR}/data/textures/buttonBomb.pvr \
  ${ASSET_BUILD_DIR}/data/textures/star.pvr \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSharpest_-y.pvr \
  ${ASSET_BUILD_DIR}/data/textures/achievementSharingIsCaring.pvr \
  ${ASSET_BUILD_DIR}/data/textures/fontSmall3.pvr \
  ${ASSET_BUILD_DIR}/data/textures/powerupSpeed.pvr \
  ${ASSET_BUILD_DIR}/data/textures/vrFillMound.pvr \
  ${ASSET_BUILD_DIR}/data/textures/agentIconColorMask.pvr \
  ${ASSET_BUILD_DIR}/data/textures/kronkIcon.pvr \
  ${ASSET_BUILD_DIR}/data/textures/oldLadyIcon.pvr \
  ${ASSET_BUILD_DIR}/data/textures/chTitleChar4.pvr \
  ${ASSET_BUILD_DIR}/data/textures/nextLevelIcon.pvr \
  ${ASSET_BUILD_DIR}/data/textures/gameCircleIcon.pvr \
  ${ASSET_BUILD_DIR}/data/textures/bonesIcon.pvr \
  ${ASSET_BUILD_DIR}/data/textures/bearIcon.pvr \
  ${ASSET_BUILD_DIR}/data/textures/towerDPreview.pvr \
  ${ASSET_BUILD_DIR}/data/textures/achievementTNT.pvr \
  ${ASSET_BUILD_DIR}/data/textures/medalGold.pvr \
  ${ASSET_BUILD_DIR}/data/textures/circleZigZag.pvr \
  ${ASSET_BUILD_DIR}/data/textures/bunnyColorMask.pvr \
  ${ASSET_BUILD_DIR}/data/textures/black.pvr \
  ${ASSET_BUILD_DIR}/data/textures/menuIcon.pvr \
  ${ASSET_BUILD_DIR}/data/textures/file.pvr \
  ${ASSET_BUILD_DIR}/data/textures/logIcon.pvr \
  ${ASSET_BUILD_DIR}/data/textures/controllerIcon.pvr \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSharper_-y.pvr \
  ${ASSET_BUILD_DIR}/data/textures/operaSingerColorMask.pvr \
  ${ASSET_BUILD_DIR}/data/textures/achievementFootballShutout.pvr \
  ${ASSET_BUILD_DIR}/data/textures/reflectionPowerup_-x.pvr \
  ${ASSET_BUILD_DIR}/data/textures/achievementsIcon.pvr \
  ${ASSET_BUILD_DIR}/data/textures/cowboyColor.pvr \
  ${ASSET_BUILD_DIR}/data/textures/wrestlerIconColorMask.pvr \
  ${ASSET_BUILD_DIR}/data/textures/googlePlayAchievementsIcon.pvr \
  ${ASSET_BUILD_DIR}/data/textures/alienIconColorMask.pvr \
  ${ASSET_BUILD_DIR}/data/textures/ticketRollBig.pvr \
  ${ASSET_BUILD_DIR}/data/textures/wrestlerIcon.pvr \
  ${ASSET_BUILD_DIR}/data/textures/egg1.pvr \
  ${ASSET_BUILD_DIR}/data/textures/gameCenterIcon.pvr \
  ${ASSET_BUILD_DIR}/data/textures/landMineLit.pvr \
  ${ASSET_BUILD_DIR}/data/textures/achievementWall.pvr \
  ${ASSET_BUILD_DIR}/data/textures/achievementMedalMedium.pvr \
  ${ASSET_BUILD_DIR}/data/textures/reflectionChar_-x.pvr \
  ${ASSET_BUILD_DIR}/data/textures/softRectVertical.pvr \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSharper_+z.pvr \
  ${ASSET_BUILD_DIR}/data/textures/wizardIcon.pvr \
  ${ASSET_BUILD_DIR}/data/textures/mapPreviewMask.pvr \
  ${ASSET_BUILD_DIR}/data/textures/nub.pvr \
  ${ASSET_BUILD_DIR}/data/textures/empty.pvr \
  ${ASSET_BUILD_DIR}/data/textures/frostyIconColorMask.pvr \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSharp_-x.pvr \
  ${ASSET_BUILD_DIR}/data/textures/bombColorIce.pvr \
  ${ASSET_BUILD_DIR}/data/textures/jumpsuitIcon.pvr \
  ${ASSET_BUILD_DIR}/data/textures/footballStadiumPreview.pvr \
  ${ASSET_BUILD_DIR}/data/textures/pixieIconColorMask.pvr \
  ${ASSET_BUILD_DIR}/data/textures/achievementEmpty.pvr \
  ${ASSET_BUILD_DIR}/data/textures/wrestlerColor.pvr \
  ${ASSET_BUILD_DIR}/data/textures/shield.pvr \
  ${ASSET_BUILD_DIR}/data/textures/iconOnslaught.pvr \
  ${ASSET_BUILD_DIR}/data/textures/replayIcon.pvr \
  ${ASSET_BUILD_DIR}/data/textures/powerupHealth.pvr \
  ${ASSET_BUILD_DIR}/data/textures/bg.pvr \
  ${ASSET_BUILD_DIR}/data/textures/chTitleChar3.pvr \
  ${ASSET_BUILD_DIR}/data/textures/textClearButton.pvr \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSoft_-z.pvr \
  ${ASSET_BUILD_DIR}/data/textures/fontSmall4.pvr \
  ${ASSET_BUILD_DIR}/data/textures/warriorColor.pvr \
  ${ASSET_BUILD_DIR}/data/textures/light.pvr \
  ${ASSET_BUILD_DIR}/data/textures/santaColor.pvr \
  ${ASSET_BUILD_DIR}/data/textures/jackColor.pvr \
  ${ASSET_BUILD_DIR}/data/textures/aliSplash.pvr \
  ${ASSET_BUILD_DIR}/data/textures/scorch.pvr \
  ${ASSET_BUILD_DIR}/data/textures/zoeIcon.pvr \
  ${ASSET_BUILD_DIR}/data/textures/bonesColorMask.pvr \
  ${ASSET_BUILD_DIR}/data/textures/pixieColor.pvr \
  ${ASSET_BUILD_DIR}/data/textures/actionHeroIconColorMask.pvr \
  ${ASSET_BUILD_DIR}/data/textures/treesColor.pvr \
  ${ASSET_BUILD_DIR}/data/textures/neoSpazColorMask.pvr \
  ${ASSET_BUILD_DIR}/data/textures/superheroIcon.pvr \
  ${ASSET_BUILD_DIR}/data/textures/achievementOffYouGo.pvr \
  ${ASSET_BUILD_DIR}/data/textures/tipTopBGColor.pvr \
  ${ASSET_BUILD_DIR}/data/textures/robotColor.pvr \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSharpest_-x.pvr \
  ${ASSET_BUILD_DIR}/data/textures/menuButton.pvr \
  ${ASSET_BUILD_DIR}/data/textures/powerupStickyBombs.pvr \
  ${ASSET_BUILD_DIR}/data/textures/ninjaIcon.pvr \
  ${ASSET_BUILD_DIR}/data/textures/witchColorMask.pvr \
  ${ASSET_BUILD_DIR}/data/textures/cowboyColorMask.pvr \
  ${ASSET_BUILD_DIR}/data/textures/operaSingerIcon.pvr \
  ${ASSET_BUILD_DIR}/data/textures/achievementBoxer.pvr \
  ${ASSET_BUILD_DIR}/data/textures/eggTex2.pvr \
  ${ASSET_BUILD_DIR}/data/textures/rampageBGColor.pvr \
  ${ASSET_BUILD_DIR}/data/textures/fontExtras2.pvr \
  ${ASSET_BUILD_DIR}/data/textures/rampageLevelColor.pvr \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSoft_+y.pvr \
  ${ASSET_BUILD_DIR}/data/textures/ticketRolls.pvr \
  ${ASSET_BUILD_DIR}/data/textures/natureBackgroundColor.pvr \
  ${ASSET_BUILD_DIR}/data/textures/santaIconColorMask.pvr \
  ${ASSET_BUILD_DIR}/data/textures/reflectionPowerup_+z.pvr \
  ${ASSET_BUILD_DIR}/data/textures/characterIconMask.pvr \
  ${ASSET_BUILD_DIR}/data/textures/aliColor.pvr \
  ${ASSET_BUILD_DIR}/data/textures/ninjaColorMask.pvr \
  ${ASSET_BUILD_DIR}/data/textures/buttonPickUp.pvr \
  ${ASSET_BUILD_DIR}/data/textures/chTitleChar5.pvr \
  ${ASSET_BUILD_DIR}/data/textures/bigGPreview.pvr \
  ${ASSET_BUILD_DIR}/data/textures/hockeyStadiumPreview.pvr \
  ${ASSET_BUILD_DIR}/data/textures/achievementMedalSmall.pvr \
  ${ASSET_BUILD_DIR}/data/textures/fontSmall2.pvr \
  ${ASSET_BUILD_DIR}/data/textures/achievementOutline.pvr \
  ${ASSET_BUILD_DIR}/data/textures/levelIcon.pvr \
  ${ASSET_BUILD_DIR}/data/textures/googlePlayGamesIcon.pvr \
  ${ASSET_BUILD_DIR}/data/textures/gladiatorColorMask.pvr \
  ${ASSET_BUILD_DIR}/data/textures/boxingGlovesColor.pvr \
  ${ASSET_BUILD_DIR}/data/textures/ouyaOButton.pvr \
  ${ASSET_BUILD_DIR}/data/textures/leaderboardsIcon.pvr \
  ${ASSET_BUILD_DIR}/data/textures/puckColor.pvr \
  ${ASSET_BUILD_DIR}/data/textures/reflectionChar_+z.pvr \
  ${ASSET_BUILD_DIR}/data/textures/penguinColor.pvr \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSharper_-x.pvr \
  ${ASSET_BUILD_DIR}/data/textures/googlePlayLeaderboardsIcon.pvr \
  ${ASSET_BUILD_DIR}/data/textures/scrollWidget.pvr \
  ${ASSET_BUILD_DIR}/data/textures/courtyardPreview.pvr \
  ${ASSET_BUILD_DIR}/data/textures/aliColorMask.pvr \
  ${ASSET_BUILD_DIR}/data/textures/penguinColorMask.pvr \
  ${ASSET_BUILD_DIR}/data/textures/witchIcon.pvr \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSharp_+z.pvr \
  ${ASSET_BUILD_DIR}/data/textures/graphicsIcon.pvr \
  ${ASSET_BUILD_DIR}/data/textures/agentIcon.pvr \
  ${ASSET_BUILD_DIR}/data/textures/fontExtras4.pvr \
  ${ASSET_BUILD_DIR}/data/textures/reflectionPowerup_-y.pvr \
  ${ASSET_BUILD_DIR}/data/textures/storeIcon.pvr \
  ${ASSET_BUILD_DIR}/data/textures/doomShroomPreview.pvr \
  ${ASSET_BUILD_DIR}/data/textures/null.pvr \
  ${ASSET_BUILD_DIR}/data/textures/backIcon.pvr \
  ${ASSET_BUILD_DIR}/data/textures/cyborgColor.pvr \
  ${ASSET_BUILD_DIR}/data/textures/monkeyFaceLevelColor.pvr \
  ${ASSET_BUILD_DIR}/data/textures/santaIcon.pvr \
  ${ASSET_BUILD_DIR}/data/textures/alwaysLandBGColor.pvr \
  ${ASSET_BUILD_DIR}/data/textures/roundaboutLevelColor.pvr \
  ${ASSET_BUILD_DIR}/data/textures/robotIcon.pvr \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSharp_-y.pvr \
  ${ASSET_BUILD_DIR}/data/textures/bunnyIcon.pvr \
  ${ASSET_BUILD_DIR}/data/textures/circleShadow.pvr \
  ${ASSET_BUILD_DIR}/data/textures/flagPoleColor.pvr \
  ${ASSET_BUILD_DIR}/data/textures/ouyaUButton.pvr \
  ${ASSET_BUILD_DIR}/data/textures/reflectionChar_-y.pvr \
  ${ASSET_BUILD_DIR}/data/textures/achievementInControl.pvr \
  ${ASSET_BUILD_DIR}/data/textures/wizardColorMask.pvr \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSharpest_+x.pvr \
  ${ASSET_BUILD_DIR}/data/textures/neoSpazColor.pvr \
  ${ASSET_BUILD_DIR}/data/textures/zigZagLevelColor.pvr \
  ${ASSET_BUILD_DIR}/data/textures/thePadPreview.pvr \
  ${ASSET_BUILD_DIR}/data/textures/superheroIconColorMask.pvr \
  ${ASSET_BUILD_DIR}/data/textures/fontSmall7.pvr \
  ${ASSET_BUILD_DIR}/data/textures/ticketRoll.pvr \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSoft_-y.pvr \
  ${ASSET_BUILD_DIR}/data/textures/playerLineup.pvr \
  ${ASSET_BUILD_DIR}/data/textures/storeCharacterEaster.pvr \
  ${ASSET_BUILD_DIR}/data/textures/coin.pvr \
  ${ASSET_BUILD_DIR}/data/textures/circleOutlineNoAlpha.pvr \
  ${ASSET_BUILD_DIR}/data/textures/scorchBig.pvr \
  ${ASSET_BUILD_DIR}/data/textures/logoEaster.pvr \
  ${ASSET_BUILD_DIR}/data/textures/warriorColorMask.pvr \
  ${ASSET_BUILD_DIR}/data/textures/assassinColor.pvr \
  ${ASSET_BUILD_DIR}/data/textures/bombStickyColor.pvr \
  ${ASSET_BUILD_DIR}/data/textures/eggTex1.pvr \
  ${ASSET_BUILD_DIR}/data/textures/gladiatorIconColorMask.pvr \
  ${ASSET_BUILD_DIR}/data/textures/melColorMask.pvr \
  ${ASSET_BUILD_DIR}/data/textures/thePadLevelColor.pvr \
  ${ASSET_BUILD_DIR}/data/textures/wizardIconColorMask.pvr \
  ${ASSET_BUILD_DIR}/data/textures/bar.pvr \
  ${ASSET_BUILD_DIR}/data/textures/zoeIconColorMask.pvr \
  ${ASSET_BUILD_DIR}/data/textures/windowHSmallVSmall.pvr \
  ${ASSET_BUILD_DIR}/data/textures/circleNoAlpha.pvr \
  ${ASSET_BUILD_DIR}/data/textures/gladiatorIcon.pvr \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSoft_+z.pvr \
  ${ASSET_BUILD_DIR}/data/textures/achievementRunaround.pvr \
  ${ASSET_BUILD_DIR}/data/textures/wizardColor.pvr \
  ${ASSET_BUILD_DIR}/data/textures/touchArrowsActions.pvr \
  ${ASSET_BUILD_DIR}/data/textures/advancedIcon.pvr \
  ${ASSET_BUILD_DIR}/data/textures/softRect2.pvr \
  ${ASSET_BUILD_DIR}/data/textures/achievementMine.pvr \
  ${ASSET_BUILD_DIR}/data/textures/rightButton.pvr \
  ${ASSET_BUILD_DIR}/data/textures/touchArrows.pvr \
  ${ASSET_BUILD_DIR}/data/textures/cyborgColorMask.pvr \
  ${ASSET_BUILD_DIR}/data/textures/jumpsuitIconColorMask.pvr \
  ${ASSET_BUILD_DIR}/data/textures/bridgitPreview.pvr \
  ${ASSET_BUILD_DIR}/data/textures/ninjaColor.pvr \
  ${ASSET_BUILD_DIR}/data/textures/santaColorMask.pvr \
  ${ASSET_BUILD_DIR}/data/textures/storeCharacter.pvr \
  ${ASSET_BUILD_DIR}/data/textures/flagColor.pvr \
  ${ASSET_BUILD_DIR}/data/textures/cragCastlePreview.pvr \
  ${ASSET_BUILD_DIR}/data/textures/frameInset.pvr \
  ${ASSET_BUILD_DIR}/data/textures/lock.pvr \
  ${ASSET_BUILD_DIR}/data/textures/agentColor.pvr \
  ${ASSET_BUILD_DIR}/data/textures/achievementGotTheMoves.pvr \
  ${ASSET_BUILD_DIR}/data/textures/buttonPunch.pvr \
  ${ASSET_BUILD_DIR}/data/textures/settingsIcon.pvr \
  ${ASSET_BUILD_DIR}/data/textures/rgbStripes.pvr \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSharp_+y.pvr \
  ${ASSET_BUILD_DIR}/data/textures/powerupImpactBombs.pvr \
  ${ASSET_BUILD_DIR}/data/textures/bigG.pvr \
  ${ASSET_BUILD_DIR}/data/textures/melIconColorMask.pvr \
  ${ASSET_BUILD_DIR}/data/textures/reflectionChar_+y.pvr \
  ${ASSET_BUILD_DIR}/data/textures/multiplayerExamples.pvr \
  ${ASSET_BUILD_DIR}/data/textures/actionButtons.pvr \
  ${ASSET_BUILD_DIR}/data/textures/melIcon.pvr \
  ${ASSET_BUILD_DIR}/data/textures/oldLadyIconColorMask.pvr \
  ${ASSET_BUILD_DIR}/data/textures/robotIconColorMask.pvr \
  ${ASSET_BUILD_DIR}/data/textures/monkeyFacePreview.pvr \
  ${ASSET_BUILD_DIR}/data/textures/achievementDualWielding.pvr \
  ${ASSET_BUILD_DIR}/data/textures/folder.pvr \
  ${ASSET_BUILD_DIR}/data/textures/frostyColorMask.pvr \
  ${ASSET_BUILD_DIR}/data/textures/kronkIconColorMask.pvr \
  ${ASSET_BUILD_DIR}/data/textures/fontBig.pvr \
  ${ASSET_BUILD_DIR}/data/textures/fontSmall1.pvr \
  ${ASSET_BUILD_DIR}/data/textures/shadowSoft.pvr \
  ${ASSET_BUILD_DIR}/data/textures/powerupLandMines.pvr \
  ${ASSET_BUILD_DIR}/data/textures/stepRightUpPreview.pvr \
  ${ASSET_BUILD_DIR}/data/textures/bearIconColorMask.pvr \
  ${ASSET_BUILD_DIR}/data/textures/kronk.pvr \
  ${ASSET_BUILD_DIR}/data/textures/downButton.pvr \
  ${ASSET_BUILD_DIR}/data/textures/bombColor.pvr \
  ${ASSET_BUILD_DIR}/data/textures/logo.pvr \
  ${ASSET_BUILD_DIR}/data/textures/reflectionPowerup_+y.pvr \
  ${ASSET_BUILD_DIR}/data/textures/zoeColorMask.pvr \
  ${ASSET_BUILD_DIR}/data/textures/jumpsuitColorMask.pvr \
  ${ASSET_BUILD_DIR}/data/textures/penguinIcon.pvr \
  ${ASSET_BUILD_DIR}/data/textures/powerupPunch.pvr \
  ${ASSET_BUILD_DIR}/data/textures/shadow.pvr \
  ${ASSET_BUILD_DIR}/data/textures/reflectionChar_-z.pvr \
  ${ASSET_BUILD_DIR}/data/textures/assassinIcon.pvr \
  ${ASSET_BUILD_DIR}/data/textures/impactBombColor.pvr \
  ${ASSET_BUILD_DIR}/data/textures/storeCharacterXmas.pvr \
  ${ASSET_BUILD_DIR}/data/textures/jackIcon.pvr \
  ${ASSET_BUILD_DIR}/data/textures/pixieIcon.pvr \
  ${ASSET_BUILD_DIR}/data/textures/jumpsuitColor.pvr \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSharper_+x.pvr \
  ${ASSET_BUILD_DIR}/data/textures/jackColorMask.pvr \
  ${ASSET_BUILD_DIR}/data/textures/shrapnel1Color.pvr \
  ${ASSET_BUILD_DIR}/data/textures/witchColor.pvr \
  ${ASSET_BUILD_DIR}/data/textures/achievementFreeLoader.pvr \
  ${ASSET_BUILD_DIR}/data/textures/zoeColor.pvr \
  ${ASSET_BUILD_DIR}/data/textures/alienColor.pvr \
  ${ASSET_BUILD_DIR}/data/textures/inventoryIcon.pvr \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSharp_-z.pvr \
  ${ASSET_BUILD_DIR}/data/textures/glow.pvr \
  ${ASSET_BUILD_DIR}/data/textures/usersButton.pvr \
  ${ASSET_BUILD_DIR}/data/textures/reflectionPowerup_-z.pvr \
  ${ASSET_BUILD_DIR}/data/textures/melColor.pvr \
  ${ASSET_BUILD_DIR}/data/textures/aliControllerQR.pvr \
  ${ASSET_BUILD_DIR}/data/textures/frostyIcon.pvr \
  ${ASSET_BUILD_DIR}/data/textures/achievementFootballVictory.pvr \
  ${ASSET_BUILD_DIR}/data/textures/tickets.pvr \
  ${ASSET_BUILD_DIR}/data/textures/cursor.pvr \
  ${ASSET_BUILD_DIR}/data/textures/egg3.pvr \
  ${ASSET_BUILD_DIR}/data/textures/crossOut.pvr \
  ${ASSET_BUILD_DIR}/data/textures/bonesColor.pvr \
  ${ASSET_BUILD_DIR}/data/textures/achievementCrossHair.pvr \
  ${ASSET_BUILD_DIR}/data/textures/actionHeroColorMask.pvr \
  ${ASSET_BUILD_DIR}/data/textures/chTitleChar1.pvr \
  ${ASSET_BUILD_DIR}/data/textures/heart.pvr \
  ${ASSET_BUILD_DIR}/data/textures/fontExtras.pvr \
  ${ASSET_BUILD_DIR}/data/textures/penguinIconColorMask.pvr \
  ${ASSET_BUILD_DIR}/data/textures/eyeColorTintMask.pvr \
  ${ASSET_BUILD_DIR}/data/textures/aliIcon.pvr \
  ${ASSET_BUILD_DIR}/data/textures/chestIconMulti.pvr \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSoft_-x.pvr \
  ${ASSET_BUILD_DIR}/data/textures/uiAtlas.pvr \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSharpest_+y.pvr \
  ${ASSET_BUILD_DIR}/data/textures/cragCastleLevelColor.pvr \
  ${ASSET_BUILD_DIR}/data/textures/assassinColorMask.pvr \
  ${ASSET_BUILD_DIR}/data/textures/bridgitLevelColor.pvr \
  ${ASSET_BUILD_DIR}/data/textures/fontSmall6.pvr \
  ${ASSET_BUILD_DIR}/data/textures/towerDLevelColor.pvr \
  ${ASSET_BUILD_DIR}/data/textures/ouyaYButton.pvr \
  ${ASSET_BUILD_DIR}/data/textures/lightSharp.pvr \
  ${ASSET_BUILD_DIR}/data/textures/buttonSquare.pvr \
  ${ASSET_BUILD_DIR}/data/textures/softRect.pvr \
  ${ASSET_BUILD_DIR}/data/textures/powerupIceBombs.pvr \
  ${ASSET_BUILD_DIR}/data/textures/jackIconColorMask.pvr \
  ${ASSET_BUILD_DIR}/data/textures/audioIcon.pvr \
  ${ASSET_BUILD_DIR}/data/textures/tv.pvr \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSharpest_-z.pvr \
  ${ASSET_BUILD_DIR}/data/textures/warriorIconColorMask.pvr \
  ${ASSET_BUILD_DIR}/data/textures/googlePlusSignInButton.pvr \
  ${ASSET_BUILD_DIR}/data/textures/circle.pvr \
  ${ASSET_BUILD_DIR}/data/textures/neoSpazIconColorMask.pvr \
  ${ASSET_BUILD_DIR}/data/textures/medalComplete.pvr \
  ${ASSET_BUILD_DIR}/data/textures/alwaysLandLevelColor.pvr \
  ${ASSET_BUILD_DIR}/data/textures/alwaysLandPreview.pvr \
  ${ASSET_BUILD_DIR}/data/textures/egg4.pvr \
  ${ASSET_BUILD_DIR}/data/textures/wrestlerColorMask.pvr \
  ${ASSET_BUILD_DIR}/data/textures/superheroColorMask.pvr \
  ${ASSET_BUILD_DIR}/data/textures/gladiatorColor.pvr \
  ${ASSET_BUILD_DIR}/data/textures/aliBSRemoteIOSQR.pvr \
  ${ASSET_BUILD_DIR}/data/textures/bearColorMask.pvr \
  ${ASSET_BUILD_DIR}/data/textures/doomShroomLevelColor.pvr \
  ${ASSET_BUILD_DIR}/data/textures/powerupBomb.pvr \
  ${ASSET_BUILD_DIR}/data/textures/chestIcon.pvr \
  ${ASSET_BUILD_DIR}/data/textures/upButton.pvr \
  ${ASSET_BUILD_DIR}/data/textures/iconRunaround.pvr \
  ${ASSET_BUILD_DIR}/data/textures/doomShroomBGColor.pvr \
  ${ASSET_BUILD_DIR}/data/textures/superheroColor.pvr \
  ${ASSET_BUILD_DIR}/data/textures/landMine.pvr \
  ${ASSET_BUILD_DIR}/data/textures/buttonJump.pvr \
  ${ASSET_BUILD_DIR}/data/textures/sparks.pvr \
  ${ASSET_BUILD_DIR}/data/textures/explosion.pvr \
  ${ASSET_BUILD_DIR}/data/textures/tipTopLevelColor.pvr \
  ${ASSET_BUILD_DIR}/data/textures/bunnyIconColorMask.pvr \
  ${ASSET_BUILD_DIR}/data/textures/reflectionChar_+x.pvr \
  ${ASSET_BUILD_DIR}/data/textures/ticketsMore.pvr \
  ${ASSET_BUILD_DIR}/data/textures/pixieColorMask.pvr \
  ${ASSET_BUILD_DIR}/data/textures/medalSilver.pvr \
  ${ASSET_BUILD_DIR}/data/textures/neoSpazIcon.pvr \
  ${ASSET_BUILD_DIR}/data/textures/meter.pvr \
  ${ASSET_BUILD_DIR}/data/textures/scrollWidgetGlow.pvr \
  ${ASSET_BUILD_DIR}/data/textures/achievementFlawlessVictory.pvr \
  ${ASSET_BUILD_DIR}/data/textures/zigzagPreview.pvr \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSharper_-z.pvr \
  ${ASSET_BUILD_DIR}/data/textures/alienColorMask.pvr \
  ${ASSET_BUILD_DIR}/data/textures/powerupShield.pvr \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSharp_+x.pvr \
  ${ASSET_BUILD_DIR}/data/textures/chestIconEmpty.pvr \
  ${ASSET_BUILD_DIR}/data/textures/agentColorMask.pvr \
  ${ASSET_BUILD_DIR}/data/textures/reflectionPowerup_+x.pvr \
  ${ASSET_BUILD_DIR}/data/textures/witchIconColorMask.pvr \
  ${ASSET_BUILD_DIR}/data/textures/kronkColorMask.pvr \
  ${ASSET_BUILD_DIR}/data/textures/menuBG.pvr \
  ${ASSET_BUILD_DIR}/data/textures/fontSmall0.pvr \
  ${ASSET_BUILD_DIR}/data/textures/assassinIconColorMask.pvr \
  ${ASSET_BUILD_DIR}/data/textures/bearColor.pvr \
  ${ASSET_BUILD_DIR}/data/textures/operaSingerColor.pvr \
  ${ASSET_BUILD_DIR}/data/textures/rampageBGColor2.pvr \
  ${ASSET_BUILD_DIR}/data/textures/fuse.pvr \
  ${ASSET_BUILD_DIR}/data/textures/frostyColor.pvr \
  ${ASSET_BUILD_DIR}/data/textures/achievementSuperPunch.pvr \
  ${ASSET_BUILD_DIR}/data/textures/tipTopPreview.pvr \
  ${ASSET_BUILD_DIR}/data/textures/googlePlusIcon.pvr \
  ${ASSET_BUILD_DIR}/data/textures/powerupCurse.pvr \
  ${ASSET_BUILD_DIR}/data/textures/trophy.pvr \
  ${ASSET_BUILD_DIR}/data/textures/courtyardLevelColor.pvr \
  ${ASSET_BUILD_DIR}/data/textures/oldLadyColorMask.pvr \
  ${ASSET_BUILD_DIR}/data/textures/rampagePreview.pvr \
  ${ASSET_BUILD_DIR}/data/textures/cuteSpaz.pvr \
  ${ASSET_BUILD_DIR}/data/textures/lightSoft.pvr \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSharper_+y.pvr \
  ${ASSET_BUILD_DIR}/data/textures/uiAtlas2.pvr \
  ${ASSET_BUILD_DIR}/data/textures/egg2.pvr \
  ${ASSET_BUILD_DIR}/data/textures/shadowSharp.pvr \
  ${ASSET_BUILD_DIR}/data/textures/tnt.pvr \
  ${ASSET_BUILD_DIR}/data/textures/actionHeroIcon.pvr \
  ${ASSET_BUILD_DIR}/data/textures/robotColorMask.pvr \
  ${ASSET_BUILD_DIR}/data/textures/impactBombColorLit.pvr \
  ${ASSET_BUILD_DIR}/data/textures/achievementStayinAlive.pvr


TEX2D_KTX_TARGETS = \
  ${ASSET_BUILD_DIR}/data/textures/cyborgIconColorMask.ktx \
  ${ASSET_BUILD_DIR}/data/textures/chestOpenIcon.ktx \
  ${ASSET_BUILD_DIR}/data/textures/analogStick.ktx \
  ${ASSET_BUILD_DIR}/data/textures/circleOutline.ktx \
  ${ASSET_BUILD_DIR}/data/textures/white.ktx \
  ${ASSET_BUILD_DIR}/data/textures/medalBronze.ktx \
  ${ASSET_BUILD_DIR}/data/textures/slash.ktx \
  ${ASSET_BUILD_DIR}/data/textures/arrow.ktx \
  ${ASSET_BUILD_DIR}/data/textures/ouyaIcon.ktx \
  ${ASSET_BUILD_DIR}/data/textures/eyeColor.ktx \
  ${ASSET_BUILD_DIR}/data/textures/achievementMedalLarge.ktx \
  ${ASSET_BUILD_DIR}/data/textures/cowboyIconColorMask.ktx \
  ${ASSET_BUILD_DIR}/data/textures/wings.ktx \
  ${ASSET_BUILD_DIR}/data/textures/roundaboutPreview.ktx \
  ${ASSET_BUILD_DIR}/data/textures/warriorIcon.ktx \
  ${ASSET_BUILD_DIR}/data/textures/windowHSmallVMed.ktx \
  ${ASSET_BUILD_DIR}/data/textures/ninjaIconColorMask.ktx \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSharpest_+z.ktx \
  ${ASSET_BUILD_DIR}/data/textures/stepRightUpLevelColor.ktx \
  ${ASSET_BUILD_DIR}/data/textures/fontSmall5.ktx \
  ${ASSET_BUILD_DIR}/data/textures/bombButton.ktx \
  ${ASSET_BUILD_DIR}/data/textures/aliIconColorMask.ktx \
  ${ASSET_BUILD_DIR}/data/textures/chTitleChar2.ktx \
  ${ASSET_BUILD_DIR}/data/textures/achievementOnslaught.ktx \
  ${ASSET_BUILD_DIR}/data/textures/smoke.ktx \
  ${ASSET_BUILD_DIR}/data/textures/lakeFrigidReflections.ktx \
  ${ASSET_BUILD_DIR}/data/textures/bunnyColor.ktx \
  ${ASSET_BUILD_DIR}/data/textures/leftButton.ktx \
  ${ASSET_BUILD_DIR}/data/textures/hockeyStadium.ktx \
  ${ASSET_BUILD_DIR}/data/textures/cowboyIcon.ktx \
  ${ASSET_BUILD_DIR}/data/textures/lakeFrigid.ktx \
  ${ASSET_BUILD_DIR}/data/textures/startButton.ktx \
  ${ASSET_BUILD_DIR}/data/textures/footballStadium.ktx \
  ${ASSET_BUILD_DIR}/data/textures/crossOutMask.ktx \
  ${ASSET_BUILD_DIR}/data/textures/bonesIconColorMask.ktx \
  ${ASSET_BUILD_DIR}/data/textures/operaSingerIconColorMask.ktx \
  ${ASSET_BUILD_DIR}/data/textures/lakeFrigidPreview.ktx \
  ${ASSET_BUILD_DIR}/data/textures/alienIcon.ktx \
  ${ASSET_BUILD_DIR}/data/textures/oldLadyColor.ktx \
  ${ASSET_BUILD_DIR}/data/textures/ouyaAButton.ktx \
  ${ASSET_BUILD_DIR}/data/textures/eggTex3.ktx \
  ${ASSET_BUILD_DIR}/data/textures/cyborgIcon.ktx \
  ${ASSET_BUILD_DIR}/data/textures/actionHeroColor.ktx \
  ${ASSET_BUILD_DIR}/data/textures/achievementTeamPlayer.ktx \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSoft_+x.ktx \
  ${ASSET_BUILD_DIR}/data/textures/fontExtras3.ktx \
  ${ASSET_BUILD_DIR}/data/textures/buttonBomb.ktx \
  ${ASSET_BUILD_DIR}/data/textures/star.ktx \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSharpest_-y.ktx \
  ${ASSET_BUILD_DIR}/data/textures/achievementSharingIsCaring.ktx \
  ${ASSET_BUILD_DIR}/data/textures/fontSmall3.ktx \
  ${ASSET_BUILD_DIR}/data/textures/powerupSpeed.ktx \
  ${ASSET_BUILD_DIR}/data/textures/vrFillMound.ktx \
  ${ASSET_BUILD_DIR}/data/textures/agentIconColorMask.ktx \
  ${ASSET_BUILD_DIR}/data/textures/kronkIcon.ktx \
  ${ASSET_BUILD_DIR}/data/textures/oldLadyIcon.ktx \
  ${ASSET_BUILD_DIR}/data/textures/chTitleChar4.ktx \
  ${ASSET_BUILD_DIR}/data/textures/nextLevelIcon.ktx \
  ${ASSET_BUILD_DIR}/data/textures/gameCircleIcon.ktx \
  ${ASSET_BUILD_DIR}/data/textures/bonesIcon.ktx \
  ${ASSET_BUILD_DIR}/data/textures/bearIcon.ktx \
  ${ASSET_BUILD_DIR}/data/textures/towerDPreview.ktx \
  ${ASSET_BUILD_DIR}/data/textures/achievementTNT.ktx \
  ${ASSET_BUILD_DIR}/data/textures/medalGold.ktx \
  ${ASSET_BUILD_DIR}/data/textures/circleZigZag.ktx \
  ${ASSET_BUILD_DIR}/data/textures/bunnyColorMask.ktx \
  ${ASSET_BUILD_DIR}/data/textures/black.ktx \
  ${ASSET_BUILD_DIR}/data/textures/menuIcon.ktx \
  ${ASSET_BUILD_DIR}/data/textures/file.ktx \
  ${ASSET_BUILD_DIR}/data/textures/logIcon.ktx \
  ${ASSET_BUILD_DIR}/data/textures/controllerIcon.ktx \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSharper_-y.ktx \
  ${ASSET_BUILD_DIR}/data/textures/operaSingerColorMask.ktx \
  ${ASSET_BUILD_DIR}/data/textures/achievementFootballShutout.ktx \
  ${ASSET_BUILD_DIR}/data/textures/reflectionPowerup_-x.ktx \
  ${ASSET_BUILD_DIR}/data/textures/achievementsIcon.ktx \
  ${ASSET_BUILD_DIR}/data/textures/cowboyColor.ktx \
  ${ASSET_BUILD_DIR}/data/textures/wrestlerIconColorMask.ktx \
  ${ASSET_BUILD_DIR}/data/textures/googlePlayAchievementsIcon.ktx \
  ${ASSET_BUILD_DIR}/data/textures/alienIconColorMask.ktx \
  ${ASSET_BUILD_DIR}/data/textures/ticketRollBig.ktx \
  ${ASSET_BUILD_DIR}/data/textures/wrestlerIcon.ktx \
  ${ASSET_BUILD_DIR}/data/textures/egg1.ktx \
  ${ASSET_BUILD_DIR}/data/textures/gameCenterIcon.ktx \
  ${ASSET_BUILD_DIR}/data/textures/landMineLit.ktx \
  ${ASSET_BUILD_DIR}/data/textures/achievementWall.ktx \
  ${ASSET_BUILD_DIR}/data/textures/achievementMedalMedium.ktx \
  ${ASSET_BUILD_DIR}/data/textures/reflectionChar_-x.ktx \
  ${ASSET_BUILD_DIR}/data/textures/softRectVertical.ktx \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSharper_+z.ktx \
  ${ASSET_BUILD_DIR}/data/textures/wizardIcon.ktx \
  ${ASSET_BUILD_DIR}/data/textures/mapPreviewMask.ktx \
  ${ASSET_BUILD_DIR}/data/textures/nub.ktx \
  ${ASSET_BUILD_DIR}/data/textures/empty.ktx \
  ${ASSET_BUILD_DIR}/data/textures/frostyIconColorMask.ktx \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSharp_-x.ktx \
  ${ASSET_BUILD_DIR}/data/textures/bombColorIce.ktx \
  ${ASSET_BUILD_DIR}/data/textures/jumpsuitIcon.ktx \
  ${ASSET_BUILD_DIR}/data/textures/footballStadiumPreview.ktx \
  ${ASSET_BUILD_DIR}/data/textures/pixieIconColorMask.ktx \
  ${ASSET_BUILD_DIR}/data/textures/achievementEmpty.ktx \
  ${ASSET_BUILD_DIR}/data/textures/wrestlerColor.ktx \
  ${ASSET_BUILD_DIR}/data/textures/shield.ktx \
  ${ASSET_BUILD_DIR}/data/textures/iconOnslaught.ktx \
  ${ASSET_BUILD_DIR}/data/textures/replayIcon.ktx \
  ${ASSET_BUILD_DIR}/data/textures/powerupHealth.ktx \
  ${ASSET_BUILD_DIR}/data/textures/bg.ktx \
  ${ASSET_BUILD_DIR}/data/textures/chTitleChar3.ktx \
  ${ASSET_BUILD_DIR}/data/textures/textClearButton.ktx \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSoft_-z.ktx \
  ${ASSET_BUILD_DIR}/data/textures/fontSmall4.ktx \
  ${ASSET_BUILD_DIR}/data/textures/warriorColor.ktx \
  ${ASSET_BUILD_DIR}/data/textures/light.ktx \
  ${ASSET_BUILD_DIR}/data/textures/santaColor.ktx \
  ${ASSET_BUILD_DIR}/data/textures/jackColor.ktx \
  ${ASSET_BUILD_DIR}/data/textures/aliSplash.ktx \
  ${ASSET_BUILD_DIR}/data/textures/scorch.ktx \
  ${ASSET_BUILD_DIR}/data/textures/zoeIcon.ktx \
  ${ASSET_BUILD_DIR}/data/textures/bonesColorMask.ktx \
  ${ASSET_BUILD_DIR}/data/textures/pixieColor.ktx \
  ${ASSET_BUILD_DIR}/data/textures/actionHeroIconColorMask.ktx \
  ${ASSET_BUILD_DIR}/data/textures/treesColor.ktx \
  ${ASSET_BUILD_DIR}/data/textures/neoSpazColorMask.ktx \
  ${ASSET_BUILD_DIR}/data/textures/superheroIcon.ktx \
  ${ASSET_BUILD_DIR}/data/textures/achievementOffYouGo.ktx \
  ${ASSET_BUILD_DIR}/data/textures/tipTopBGColor.ktx \
  ${ASSET_BUILD_DIR}/data/textures/robotColor.ktx \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSharpest_-x.ktx \
  ${ASSET_BUILD_DIR}/data/textures/menuButton.ktx \
  ${ASSET_BUILD_DIR}/data/textures/powerupStickyBombs.ktx \
  ${ASSET_BUILD_DIR}/data/textures/ninjaIcon.ktx \
  ${ASSET_BUILD_DIR}/data/textures/witchColorMask.ktx \
  ${ASSET_BUILD_DIR}/data/textures/cowboyColorMask.ktx \
  ${ASSET_BUILD_DIR}/data/textures/operaSingerIcon.ktx \
  ${ASSET_BUILD_DIR}/data/textures/achievementBoxer.ktx \
  ${ASSET_BUILD_DIR}/data/textures/eggTex2.ktx \
  ${ASSET_BUILD_DIR}/data/textures/rampageBGColor.ktx \
  ${ASSET_BUILD_DIR}/data/textures/fontExtras2.ktx \
  ${ASSET_BUILD_DIR}/data/textures/rampageLevelColor.ktx \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSoft_+y.ktx \
  ${ASSET_BUILD_DIR}/data/textures/ticketRolls.ktx \
  ${ASSET_BUILD_DIR}/data/textures/natureBackgroundColor.ktx \
  ${ASSET_BUILD_DIR}/data/textures/santaIconColorMask.ktx \
  ${ASSET_BUILD_DIR}/data/textures/reflectionPowerup_+z.ktx \
  ${ASSET_BUILD_DIR}/data/textures/characterIconMask.ktx \
  ${ASSET_BUILD_DIR}/data/textures/aliColor.ktx \
  ${ASSET_BUILD_DIR}/data/textures/ninjaColorMask.ktx \
  ${ASSET_BUILD_DIR}/data/textures/buttonPickUp.ktx \
  ${ASSET_BUILD_DIR}/data/textures/chTitleChar5.ktx \
  ${ASSET_BUILD_DIR}/data/textures/bigGPreview.ktx \
  ${ASSET_BUILD_DIR}/data/textures/hockeyStadiumPreview.ktx \
  ${ASSET_BUILD_DIR}/data/textures/achievementMedalSmall.ktx \
  ${ASSET_BUILD_DIR}/data/textures/fontSmall2.ktx \
  ${ASSET_BUILD_DIR}/data/textures/achievementOutline.ktx \
  ${ASSET_BUILD_DIR}/data/textures/levelIcon.ktx \
  ${ASSET_BUILD_DIR}/data/textures/googlePlayGamesIcon.ktx \
  ${ASSET_BUILD_DIR}/data/textures/gladiatorColorMask.ktx \
  ${ASSET_BUILD_DIR}/data/textures/boxingGlovesColor.ktx \
  ${ASSET_BUILD_DIR}/data/textures/ouyaOButton.ktx \
  ${ASSET_BUILD_DIR}/data/textures/leaderboardsIcon.ktx \
  ${ASSET_BUILD_DIR}/data/textures/puckColor.ktx \
  ${ASSET_BUILD_DIR}/data/textures/reflectionChar_+z.ktx \
  ${ASSET_BUILD_DIR}/data/textures/penguinColor.ktx \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSharper_-x.ktx \
  ${ASSET_BUILD_DIR}/data/textures/googlePlayLeaderboardsIcon.ktx \
  ${ASSET_BUILD_DIR}/data/textures/scrollWidget.ktx \
  ${ASSET_BUILD_DIR}/data/textures/courtyardPreview.ktx \
  ${ASSET_BUILD_DIR}/data/textures/aliColorMask.ktx \
  ${ASSET_BUILD_DIR}/data/textures/penguinColorMask.ktx \
  ${ASSET_BUILD_DIR}/data/textures/witchIcon.ktx \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSharp_+z.ktx \
  ${ASSET_BUILD_DIR}/data/textures/graphicsIcon.ktx \
  ${ASSET_BUILD_DIR}/data/textures/agentIcon.ktx \
  ${ASSET_BUILD_DIR}/data/textures/fontExtras4.ktx \
  ${ASSET_BUILD_DIR}/data/textures/reflectionPowerup_-y.ktx \
  ${ASSET_BUILD_DIR}/data/textures/storeIcon.ktx \
  ${ASSET_BUILD_DIR}/data/textures/doomShroomPreview.ktx \
  ${ASSET_BUILD_DIR}/data/textures/null.ktx \
  ${ASSET_BUILD_DIR}/data/textures/backIcon.ktx \
  ${ASSET_BUILD_DIR}/data/textures/cyborgColor.ktx \
  ${ASSET_BUILD_DIR}/data/textures/monkeyFaceLevelColor.ktx \
  ${ASSET_BUILD_DIR}/data/textures/santaIcon.ktx \
  ${ASSET_BUILD_DIR}/data/textures/alwaysLandBGColor.ktx \
  ${ASSET_BUILD_DIR}/data/textures/roundaboutLevelColor.ktx \
  ${ASSET_BUILD_DIR}/data/textures/robotIcon.ktx \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSharp_-y.ktx \
  ${ASSET_BUILD_DIR}/data/textures/bunnyIcon.ktx \
  ${ASSET_BUILD_DIR}/data/textures/circleShadow.ktx \
  ${ASSET_BUILD_DIR}/data/textures/flagPoleColor.ktx \
  ${ASSET_BUILD_DIR}/data/textures/ouyaUButton.ktx \
  ${ASSET_BUILD_DIR}/data/textures/reflectionChar_-y.ktx \
  ${ASSET_BUILD_DIR}/data/textures/achievementInControl.ktx \
  ${ASSET_BUILD_DIR}/data/textures/wizardColorMask.ktx \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSharpest_+x.ktx \
  ${ASSET_BUILD_DIR}/data/textures/neoSpazColor.ktx \
  ${ASSET_BUILD_DIR}/data/textures/zigZagLevelColor.ktx \
  ${ASSET_BUILD_DIR}/data/textures/thePadPreview.ktx \
  ${ASSET_BUILD_DIR}/data/textures/superheroIconColorMask.ktx \
  ${ASSET_BUILD_DIR}/data/textures/fontSmall7.ktx \
  ${ASSET_BUILD_DIR}/data/textures/ticketRoll.ktx \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSoft_-y.ktx \
  ${ASSET_BUILD_DIR}/data/textures/playerLineup.ktx \
  ${ASSET_BUILD_DIR}/data/textures/storeCharacterEaster.ktx \
  ${ASSET_BUILD_DIR}/data/textures/coin.ktx \
  ${ASSET_BUILD_DIR}/data/textures/circleOutlineNoAlpha.ktx \
  ${ASSET_BUILD_DIR}/data/textures/scorchBig.ktx \
  ${ASSET_BUILD_DIR}/data/textures/logoEaster.ktx \
  ${ASSET_BUILD_DIR}/data/textures/warriorColorMask.ktx \
  ${ASSET_BUILD_DIR}/data/textures/assassinColor.ktx \
  ${ASSET_BUILD_DIR}/data/textures/bombStickyColor.ktx \
  ${ASSET_BUILD_DIR}/data/textures/eggTex1.ktx \
  ${ASSET_BUILD_DIR}/data/textures/gladiatorIconColorMask.ktx \
  ${ASSET_BUILD_DIR}/data/textures/melColorMask.ktx \
  ${ASSET_BUILD_DIR}/data/textures/thePadLevelColor.ktx \
  ${ASSET_BUILD_DIR}/data/textures/wizardIconColorMask.ktx \
  ${ASSET_BUILD_DIR}/data/textures/bar.ktx \
  ${ASSET_BUILD_DIR}/data/textures/zoeIconColorMask.ktx \
  ${ASSET_BUILD_DIR}/data/textures/windowHSmallVSmall.ktx \
  ${ASSET_BUILD_DIR}/data/textures/circleNoAlpha.ktx \
  ${ASSET_BUILD_DIR}/data/textures/gladiatorIcon.ktx \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSoft_+z.ktx \
  ${ASSET_BUILD_DIR}/data/textures/achievementRunaround.ktx \
  ${ASSET_BUILD_DIR}/data/textures/wizardColor.ktx \
  ${ASSET_BUILD_DIR}/data/textures/touchArrowsActions.ktx \
  ${ASSET_BUILD_DIR}/data/textures/advancedIcon.ktx \
  ${ASSET_BUILD_DIR}/data/textures/softRect2.ktx \
  ${ASSET_BUILD_DIR}/data/textures/achievementMine.ktx \
  ${ASSET_BUILD_DIR}/data/textures/rightButton.ktx \
  ${ASSET_BUILD_DIR}/data/textures/touchArrows.ktx \
  ${ASSET_BUILD_DIR}/data/textures/cyborgColorMask.ktx \
  ${ASSET_BUILD_DIR}/data/textures/jumpsuitIconColorMask.ktx \
  ${ASSET_BUILD_DIR}/data/textures/bridgitPreview.ktx \
  ${ASSET_BUILD_DIR}/data/textures/ninjaColor.ktx \
  ${ASSET_BUILD_DIR}/data/textures/santaColorMask.ktx \
  ${ASSET_BUILD_DIR}/data/textures/storeCharacter.ktx \
  ${ASSET_BUILD_DIR}/data/textures/flagColor.ktx \
  ${ASSET_BUILD_DIR}/data/textures/cragCastlePreview.ktx \
  ${ASSET_BUILD_DIR}/data/textures/frameInset.ktx \
  ${ASSET_BUILD_DIR}/data/textures/lock.ktx \
  ${ASSET_BUILD_DIR}/data/textures/agentColor.ktx \
  ${ASSET_BUILD_DIR}/data/textures/achievementGotTheMoves.ktx \
  ${ASSET_BUILD_DIR}/data/textures/buttonPunch.ktx \
  ${ASSET_BUILD_DIR}/data/textures/settingsIcon.ktx \
  ${ASSET_BUILD_DIR}/data/textures/rgbStripes.ktx \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSharp_+y.ktx \
  ${ASSET_BUILD_DIR}/data/textures/powerupImpactBombs.ktx \
  ${ASSET_BUILD_DIR}/data/textures/bigG.ktx \
  ${ASSET_BUILD_DIR}/data/textures/melIconColorMask.ktx \
  ${ASSET_BUILD_DIR}/data/textures/reflectionChar_+y.ktx \
  ${ASSET_BUILD_DIR}/data/textures/multiplayerExamples.ktx \
  ${ASSET_BUILD_DIR}/data/textures/actionButtons.ktx \
  ${ASSET_BUILD_DIR}/data/textures/melIcon.ktx \
  ${ASSET_BUILD_DIR}/data/textures/oldLadyIconColorMask.ktx \
  ${ASSET_BUILD_DIR}/data/textures/robotIconColorMask.ktx \
  ${ASSET_BUILD_DIR}/data/textures/monkeyFacePreview.ktx \
  ${ASSET_BUILD_DIR}/data/textures/achievementDualWielding.ktx \
  ${ASSET_BUILD_DIR}/data/textures/folder.ktx \
  ${ASSET_BUILD_DIR}/data/textures/frostyColorMask.ktx \
  ${ASSET_BUILD_DIR}/data/textures/kronkIconColorMask.ktx \
  ${ASSET_BUILD_DIR}/data/textures/fontBig.ktx \
  ${ASSET_BUILD_DIR}/data/textures/fontSmall1.ktx \
  ${ASSET_BUILD_DIR}/data/textures/shadowSoft.ktx \
  ${ASSET_BUILD_DIR}/data/textures/powerupLandMines.ktx \
  ${ASSET_BUILD_DIR}/data/textures/stepRightUpPreview.ktx \
  ${ASSET_BUILD_DIR}/data/textures/bearIconColorMask.ktx \
  ${ASSET_BUILD_DIR}/data/textures/kronk.ktx \
  ${ASSET_BUILD_DIR}/data/textures/downButton.ktx \
  ${ASSET_BUILD_DIR}/data/textures/bombColor.ktx \
  ${ASSET_BUILD_DIR}/data/textures/logo.ktx \
  ${ASSET_BUILD_DIR}/data/textures/reflectionPowerup_+y.ktx \
  ${ASSET_BUILD_DIR}/data/textures/zoeColorMask.ktx \
  ${ASSET_BUILD_DIR}/data/textures/jumpsuitColorMask.ktx \
  ${ASSET_BUILD_DIR}/data/textures/penguinIcon.ktx \
  ${ASSET_BUILD_DIR}/data/textures/powerupPunch.ktx \
  ${ASSET_BUILD_DIR}/data/textures/shadow.ktx \
  ${ASSET_BUILD_DIR}/data/textures/reflectionChar_-z.ktx \
  ${ASSET_BUILD_DIR}/data/textures/assassinIcon.ktx \
  ${ASSET_BUILD_DIR}/data/textures/impactBombColor.ktx \
  ${ASSET_BUILD_DIR}/data/textures/storeCharacterXmas.ktx \
  ${ASSET_BUILD_DIR}/data/textures/jackIcon.ktx \
  ${ASSET_BUILD_DIR}/data/textures/pixieIcon.ktx \
  ${ASSET_BUILD_DIR}/data/textures/jumpsuitColor.ktx \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSharper_+x.ktx \
  ${ASSET_BUILD_DIR}/data/textures/jackColorMask.ktx \
  ${ASSET_BUILD_DIR}/data/textures/shrapnel1Color.ktx \
  ${ASSET_BUILD_DIR}/data/textures/witchColor.ktx \
  ${ASSET_BUILD_DIR}/data/textures/achievementFreeLoader.ktx \
  ${ASSET_BUILD_DIR}/data/textures/zoeColor.ktx \
  ${ASSET_BUILD_DIR}/data/textures/alienColor.ktx \
  ${ASSET_BUILD_DIR}/data/textures/inventoryIcon.ktx \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSharp_-z.ktx \
  ${ASSET_BUILD_DIR}/data/textures/glow.ktx \
  ${ASSET_BUILD_DIR}/data/textures/usersButton.ktx \
  ${ASSET_BUILD_DIR}/data/textures/reflectionPowerup_-z.ktx \
  ${ASSET_BUILD_DIR}/data/textures/melColor.ktx \
  ${ASSET_BUILD_DIR}/data/textures/aliControllerQR.ktx \
  ${ASSET_BUILD_DIR}/data/textures/frostyIcon.ktx \
  ${ASSET_BUILD_DIR}/data/textures/achievementFootballVictory.ktx \
  ${ASSET_BUILD_DIR}/data/textures/tickets.ktx \
  ${ASSET_BUILD_DIR}/data/textures/cursor.ktx \
  ${ASSET_BUILD_DIR}/data/textures/egg3.ktx \
  ${ASSET_BUILD_DIR}/data/textures/crossOut.ktx \
  ${ASSET_BUILD_DIR}/data/textures/bonesColor.ktx \
  ${ASSET_BUILD_DIR}/data/textures/achievementCrossHair.ktx \
  ${ASSET_BUILD_DIR}/data/textures/actionHeroColorMask.ktx \
  ${ASSET_BUILD_DIR}/data/textures/chTitleChar1.ktx \
  ${ASSET_BUILD_DIR}/data/textures/heart.ktx \
  ${ASSET_BUILD_DIR}/data/textures/fontExtras.ktx \
  ${ASSET_BUILD_DIR}/data/textures/penguinIconColorMask.ktx \
  ${ASSET_BUILD_DIR}/data/textures/eyeColorTintMask.ktx \
  ${ASSET_BUILD_DIR}/data/textures/aliIcon.ktx \
  ${ASSET_BUILD_DIR}/data/textures/chestIconMulti.ktx \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSoft_-x.ktx \
  ${ASSET_BUILD_DIR}/data/textures/uiAtlas.ktx \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSharpest_+y.ktx \
  ${ASSET_BUILD_DIR}/data/textures/cragCastleLevelColor.ktx \
  ${ASSET_BUILD_DIR}/data/textures/assassinColorMask.ktx \
  ${ASSET_BUILD_DIR}/data/textures/bridgitLevelColor.ktx \
  ${ASSET_BUILD_DIR}/data/textures/fontSmall6.ktx \
  ${ASSET_BUILD_DIR}/data/textures/towerDLevelColor.ktx \
  ${ASSET_BUILD_DIR}/data/textures/ouyaYButton.ktx \
  ${ASSET_BUILD_DIR}/data/textures/lightSharp.ktx \
  ${ASSET_BUILD_DIR}/data/textures/buttonSquare.ktx \
  ${ASSET_BUILD_DIR}/data/textures/softRect.ktx \
  ${ASSET_BUILD_DIR}/data/textures/powerupIceBombs.ktx \
  ${ASSET_BUILD_DIR}/data/textures/jackIconColorMask.ktx \
  ${ASSET_BUILD_DIR}/data/textures/audioIcon.ktx \
  ${ASSET_BUILD_DIR}/data/textures/tv.ktx \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSharpest_-z.ktx \
  ${ASSET_BUILD_DIR}/data/textures/warriorIconColorMask.ktx \
  ${ASSET_BUILD_DIR}/data/textures/googlePlusSignInButton.ktx \
  ${ASSET_BUILD_DIR}/data/textures/circle.ktx \
  ${ASSET_BUILD_DIR}/data/textures/neoSpazIconColorMask.ktx \
  ${ASSET_BUILD_DIR}/data/textures/medalComplete.ktx \
  ${ASSET_BUILD_DIR}/data/textures/alwaysLandLevelColor.ktx \
  ${ASSET_BUILD_DIR}/data/textures/alwaysLandPreview.ktx \
  ${ASSET_BUILD_DIR}/data/textures/egg4.ktx \
  ${ASSET_BUILD_DIR}/data/textures/wrestlerColorMask.ktx \
  ${ASSET_BUILD_DIR}/data/textures/superheroColorMask.ktx \
  ${ASSET_BUILD_DIR}/data/textures/gladiatorColor.ktx \
  ${ASSET_BUILD_DIR}/data/textures/aliBSRemoteIOSQR.ktx \
  ${ASSET_BUILD_DIR}/data/textures/bearColorMask.ktx \
  ${ASSET_BUILD_DIR}/data/textures/doomShroomLevelColor.ktx \
  ${ASSET_BUILD_DIR}/data/textures/powerupBomb.ktx \
  ${ASSET_BUILD_DIR}/data/textures/chestIcon.ktx \
  ${ASSET_BUILD_DIR}/data/textures/upButton.ktx \
  ${ASSET_BUILD_DIR}/data/textures/iconRunaround.ktx \
  ${ASSET_BUILD_DIR}/data/textures/doomShroomBGColor.ktx \
  ${ASSET_BUILD_DIR}/data/textures/superheroColor.ktx \
  ${ASSET_BUILD_DIR}/data/textures/landMine.ktx \
  ${ASSET_BUILD_DIR}/data/textures/buttonJump.ktx \
  ${ASSET_BUILD_DIR}/data/textures/sparks.ktx \
  ${ASSET_BUILD_DIR}/data/textures/explosion.ktx \
  ${ASSET_BUILD_DIR}/data/textures/tipTopLevelColor.ktx \
  ${ASSET_BUILD_DIR}/data/textures/bunnyIconColorMask.ktx \
  ${ASSET_BUILD_DIR}/data/textures/reflectionChar_+x.ktx \
  ${ASSET_BUILD_DIR}/data/textures/ticketsMore.ktx \
  ${ASSET_BUILD_DIR}/data/textures/pixieColorMask.ktx \
  ${ASSET_BUILD_DIR}/data/textures/medalSilver.ktx \
  ${ASSET_BUILD_DIR}/data/textures/neoSpazIcon.ktx \
  ${ASSET_BUILD_DIR}/data/textures/meter.ktx \
  ${ASSET_BUILD_DIR}/data/textures/scrollWidgetGlow.ktx \
  ${ASSET_BUILD_DIR}/data/textures/achievementFlawlessVictory.ktx \
  ${ASSET_BUILD_DIR}/data/textures/zigzagPreview.ktx \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSharper_-z.ktx \
  ${ASSET_BUILD_DIR}/data/textures/alienColorMask.ktx \
  ${ASSET_BUILD_DIR}/data/textures/powerupShield.ktx \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSharp_+x.ktx \
  ${ASSET_BUILD_DIR}/data/textures/chestIconEmpty.ktx \
  ${ASSET_BUILD_DIR}/data/textures/agentColorMask.ktx \
  ${ASSET_BUILD_DIR}/data/textures/reflectionPowerup_+x.ktx \
  ${ASSET_BUILD_DIR}/data/textures/witchIconColorMask.ktx \
  ${ASSET_BUILD_DIR}/data/textures/kronkColorMask.ktx \
  ${ASSET_BUILD_DIR}/data/textures/menuBG.ktx \
  ${ASSET_BUILD_DIR}/data/textures/fontSmall0.ktx \
  ${ASSET_BUILD_DIR}/data/textures/assassinIconColorMask.ktx \
  ${ASSET_BUILD_DIR}/data/textures/bearColor.ktx \
  ${ASSET_BUILD_DIR}/data/textures/operaSingerColor.ktx \
  ${ASSET_BUILD_DIR}/data/textures/rampageBGColor2.ktx \
  ${ASSET_BUILD_DIR}/data/textures/fuse.ktx \
  ${ASSET_BUILD_DIR}/data/textures/frostyColor.ktx \
  ${ASSET_BUILD_DIR}/data/textures/achievementSuperPunch.ktx \
  ${ASSET_BUILD_DIR}/data/textures/tipTopPreview.ktx \
  ${ASSET_BUILD_DIR}/data/textures/googlePlusIcon.ktx \
  ${ASSET_BUILD_DIR}/data/textures/powerupCurse.ktx \
  ${ASSET_BUILD_DIR}/data/textures/trophy.ktx \
  ${ASSET_BUILD_DIR}/data/textures/courtyardLevelColor.ktx \
  ${ASSET_BUILD_DIR}/data/textures/oldLadyColorMask.ktx \
  ${ASSET_BUILD_DIR}/data/textures/rampagePreview.ktx \
  ${ASSET_BUILD_DIR}/data/textures/cuteSpaz.ktx \
  ${ASSET_BUILD_DIR}/data/textures/lightSoft.ktx \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSharper_+y.ktx \
  ${ASSET_BUILD_DIR}/data/textures/uiAtlas2.ktx \
  ${ASSET_BUILD_DIR}/data/textures/egg2.ktx \
  ${ASSET_BUILD_DIR}/data/textures/shadowSharp.ktx \
  ${ASSET_BUILD_DIR}/data/textures/tnt.ktx \
  ${ASSET_BUILD_DIR}/data/textures/actionHeroIcon.ktx \
  ${ASSET_BUILD_DIR}/data/textures/robotColorMask.ktx \
  ${ASSET_BUILD_DIR}/data/textures/impactBombColorLit.ktx \
  ${ASSET_BUILD_DIR}/data/textures/achievementStayinAlive.ktx


TEX2D_PREVIEW_PNG_TARGETS = \
  ${ASSET_BUILD_DIR}/data/textures/cyborgIconColorMask_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/chestOpenIcon_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/analogStick_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/circleOutline_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/white_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/medalBronze_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/slash_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/arrow_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/ouyaIcon_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/eyeColor_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/achievementMedalLarge_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/cowboyIconColorMask_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/wings_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/roundaboutPreview_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/warriorIcon_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/windowHSmallVMed_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/ninjaIconColorMask_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSharpest_+z_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/stepRightUpLevelColor_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/fontSmall5_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/bombButton_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/aliIconColorMask_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/chTitleChar2_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/achievementOnslaught_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/smoke_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/lakeFrigidReflections_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/bunnyColor_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/leftButton_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/hockeyStadium_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/cowboyIcon_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/lakeFrigid_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/startButton_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/footballStadium_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/crossOutMask_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/bonesIconColorMask_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/operaSingerIconColorMask_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/lakeFrigidPreview_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/alienIcon_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/oldLadyColor_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/ouyaAButton_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/eggTex3_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/cyborgIcon_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/actionHeroColor_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/achievementTeamPlayer_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSoft_+x_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/fontExtras3_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/buttonBomb_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/star_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSharpest_-y_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/achievementSharingIsCaring_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/fontSmall3_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/powerupSpeed_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/vrFillMound_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/agentIconColorMask_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/kronkIcon_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/oldLadyIcon_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/chTitleChar4_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/nextLevelIcon_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/gameCircleIcon_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/bonesIcon_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/bearIcon_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/towerDPreview_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/achievementTNT_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/medalGold_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/circleZigZag_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/bunnyColorMask_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/black_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/menuIcon_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/file_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/logIcon_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/controllerIcon_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSharper_-y_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/operaSingerColorMask_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/achievementFootballShutout_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/reflectionPowerup_-x_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/achievementsIcon_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/cowboyColor_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/wrestlerIconColorMask_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/googlePlayAchievementsIcon_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/alienIconColorMask_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/ticketRollBig_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/wrestlerIcon_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/egg1_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/gameCenterIcon_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/landMineLit_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/achievementWall_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/achievementMedalMedium_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/reflectionChar_-x_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/softRectVertical_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSharper_+z_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/wizardIcon_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/mapPreviewMask_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/nub_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/empty_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/frostyIconColorMask_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSharp_-x_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/bombColorIce_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/jumpsuitIcon_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/footballStadiumPreview_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/pixieIconColorMask_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/achievementEmpty_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/wrestlerColor_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/shield_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/iconOnslaught_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/replayIcon_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/powerupHealth_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/bg_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/chTitleChar3_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/textClearButton_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSoft_-z_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/fontSmall4_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/warriorColor_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/light_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/santaColor_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/jackColor_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/aliSplash_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/scorch_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/zoeIcon_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/bonesColorMask_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/pixieColor_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/actionHeroIconColorMask_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/treesColor_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/neoSpazColorMask_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/superheroIcon_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/achievementOffYouGo_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/tipTopBGColor_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/robotColor_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSharpest_-x_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/menuButton_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/powerupStickyBombs_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/ninjaIcon_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/witchColorMask_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/cowboyColorMask_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/operaSingerIcon_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/achievementBoxer_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/eggTex2_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/rampageBGColor_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/fontExtras2_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/rampageLevelColor_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSoft_+y_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/ticketRolls_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/natureBackgroundColor_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/santaIconColorMask_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/reflectionPowerup_+z_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/characterIconMask_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/aliColor_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/ninjaColorMask_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/buttonPickUp_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/chTitleChar5_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/bigGPreview_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/hockeyStadiumPreview_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/achievementMedalSmall_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/fontSmall2_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/achievementOutline_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/levelIcon_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/googlePlayGamesIcon_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/gladiatorColorMask_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/boxingGlovesColor_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/ouyaOButton_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/leaderboardsIcon_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/puckColor_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/reflectionChar_+z_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/penguinColor_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSharper_-x_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/googlePlayLeaderboardsIcon_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/scrollWidget_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/courtyardPreview_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/aliColorMask_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/penguinColorMask_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/witchIcon_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSharp_+z_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/graphicsIcon_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/agentIcon_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/fontExtras4_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/reflectionPowerup_-y_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/storeIcon_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/doomShroomPreview_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/null_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/backIcon_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/cyborgColor_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/monkeyFaceLevelColor_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/santaIcon_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/alwaysLandBGColor_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/roundaboutLevelColor_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/robotIcon_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSharp_-y_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/bunnyIcon_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/circleShadow_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/flagPoleColor_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/ouyaUButton_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/reflectionChar_-y_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/achievementInControl_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/wizardColorMask_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSharpest_+x_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/neoSpazColor_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/zigZagLevelColor_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/thePadPreview_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/superheroIconColorMask_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/fontSmall7_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/ticketRoll_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSoft_-y_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/playerLineup_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/storeCharacterEaster_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/coin_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/circleOutlineNoAlpha_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/scorchBig_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/logoEaster_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/warriorColorMask_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/assassinColor_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/bombStickyColor_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/eggTex1_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/gladiatorIconColorMask_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/melColorMask_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/thePadLevelColor_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/wizardIconColorMask_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/bar_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/zoeIconColorMask_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/windowHSmallVSmall_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/circleNoAlpha_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/gladiatorIcon_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSoft_+z_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/achievementRunaround_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/wizardColor_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/touchArrowsActions_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/advancedIcon_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/softRect2_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/achievementMine_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/rightButton_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/touchArrows_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/cyborgColorMask_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/jumpsuitIconColorMask_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/bridgitPreview_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/ninjaColor_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/santaColorMask_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/storeCharacter_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/flagColor_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/cragCastlePreview_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/frameInset_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/lock_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/agentColor_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/achievementGotTheMoves_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/buttonPunch_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/settingsIcon_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/rgbStripes_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSharp_+y_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/powerupImpactBombs_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/bigG_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/melIconColorMask_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/reflectionChar_+y_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/multiplayerExamples_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/actionButtons_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/melIcon_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/oldLadyIconColorMask_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/robotIconColorMask_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/monkeyFacePreview_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/achievementDualWielding_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/folder_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/frostyColorMask_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/kronkIconColorMask_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/fontBig_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/fontSmall1_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/shadowSoft_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/powerupLandMines_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/stepRightUpPreview_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/bearIconColorMask_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/kronk_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/downButton_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/bombColor_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/logo_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/reflectionPowerup_+y_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/zoeColorMask_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/jumpsuitColorMask_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/penguinIcon_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/powerupPunch_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/shadow_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/reflectionChar_-z_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/assassinIcon_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/impactBombColor_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/storeCharacterXmas_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/jackIcon_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/pixieIcon_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/jumpsuitColor_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSharper_+x_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/jackColorMask_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/shrapnel1Color_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/witchColor_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/achievementFreeLoader_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/zoeColor_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/alienColor_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/inventoryIcon_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSharp_-z_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/glow_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/usersButton_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/reflectionPowerup_-z_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/melColor_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/aliControllerQR_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/frostyIcon_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/achievementFootballVictory_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/tickets_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/cursor_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/egg3_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/crossOut_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/bonesColor_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/achievementCrossHair_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/actionHeroColorMask_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/chTitleChar1_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/heart_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/fontExtras_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/penguinIconColorMask_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/eyeColorTintMask_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/aliIcon_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/chestIconMulti_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSoft_-x_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/uiAtlas_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSharpest_+y_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/cragCastleLevelColor_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/assassinColorMask_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/bridgitLevelColor_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/fontSmall6_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/towerDLevelColor_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/ouyaYButton_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/lightSharp_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/buttonSquare_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/softRect_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/powerupIceBombs_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/jackIconColorMask_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/audioIcon_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/tv_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSharpest_-z_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/warriorIconColorMask_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/googlePlusSignInButton_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/circle_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/neoSpazIconColorMask_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/medalComplete_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/alwaysLandLevelColor_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/alwaysLandPreview_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/egg4_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/wrestlerColorMask_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/superheroColorMask_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/gladiatorColor_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/aliBSRemoteIOSQR_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/bearColorMask_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/doomShroomLevelColor_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/powerupBomb_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/chestIcon_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/upButton_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/iconRunaround_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/doomShroomBGColor_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/superheroColor_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/landMine_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/buttonJump_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/sparks_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/explosion_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/tipTopLevelColor_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/bunnyIconColorMask_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/reflectionChar_+x_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/ticketsMore_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/pixieColorMask_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/medalSilver_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/neoSpazIcon_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/meter_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/scrollWidgetGlow_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/achievementFlawlessVictory_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/zigzagPreview_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSharper_-z_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/alienColorMask_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/powerupShield_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSharp_+x_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/chestIconEmpty_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/agentColorMask_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/reflectionPowerup_+x_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/witchIconColorMask_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/kronkColorMask_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/menuBG_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/fontSmall0_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/assassinIconColorMask_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/bearColor_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/operaSingerColor_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/rampageBGColor2_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/fuse_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/frostyColor_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/achievementSuperPunch_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/tipTopPreview_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/googlePlusIcon_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/powerupCurse_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/trophy_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/courtyardLevelColor_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/oldLadyColorMask_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/rampagePreview_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/cuteSpaz_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/lightSoft_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/reflectionSharper_+y_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/uiAtlas2_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/egg2_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/shadowSharp_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/tnt_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/actionHeroIcon_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/robotColorMask_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/impactBombColorLit_preview.png \
  ${ASSET_BUILD_DIR}/data/textures/achievementStayinAlive_preview.png

#AUTOGENERATED_END

ASSET_TARGETS_COMMON += $(MODEL_TARGETS)

${ASSET_BUILD_DIR}/%.bob : ../.efrocachemap
	@cd .. && tools/snippets efrocache_get assets/$@

${ASSET_BUILD_DIR}/%.cob : ../.efrocachemap
	@cd .. && tools/snippets efrocache_get assets/$@

${ASSET_BUILD_DIR}/%.ogg : ../.efrocachemap
	@cd .. && tools/snippets efrocache_get assets/$@

${ASSET_BUILD_DIR}/%.fdata : ../.efrocachemap
	@cd .. && tools/snippets efrocache_get assets/$@

# Langdata one-off json file.
${ASSET_BUILD_DIR}/data/data/langdata.json : ../.efrocachemap
	@cd .. && tools/snippets efrocache_get assets/$@

# Languages json files.
${ASSET_BUILD_DIR}/data/data/languages/%.json : ../.efrocachemap
	@cd .. && tools/snippets efrocache_get assets/$@

# Map json files.
${ASSET_BUILD_DIR}/data/data/maps/%.json : ../.efrocachemap
	@cd .. && tools/snippets efrocache_get assets/$@

${ASSET_SRC_DIR}/%.tex2d.png : ../.efrocachemap
	@cd .. && tools/snippets efrocache_get assets/$@

${ASSET_SRC_DIR}/%_+x.tex2d.png : ../.efrocachemap
	@cd .. && tools/snippets efrocache_get assets/$@

${ASSET_BUILD_DIR}/%_preview.png : ../.efrocachemap
	@cd .. && tools/snippets efrocache_get assets/$@

${ASSET_BUILD_DIR}/%.dds : ../.efrocachemap
	@cd .. && tools/snippets efrocache_get assets/$@

${ASSET_BUILD_DIR}/%.pvr : ../.efrocachemap
	@cd .. && tools/snippets efrocache_get assets/$@

${ASSET_BUILD_DIR}/%.ktx : ../.efrocachemap
	@cd .. && tools/snippets efrocache_get assets/$@

# Copies our previews into ${ASSET_SRC_MASTER_DIR} for use in maya.
${ASSET_SRC_MASTER_DIR}/models/maya/sourceimages/ballistica_textures/%.png : \
      ${ASSET_BUILD_DIR}/textures/%.png
	@mkdir -p $(dir $@)
	@cp $^ $@

audio: $(AUDIO_TARGETS)
clean-audio:
	rm -rf $(ASSET_BUILD_DIR)/audio

data: $(DATA_TARGETS)
clean-data:
	rm -rf $(ASSET_BUILD_DIR)/data

fonts: $(FONT_TARGETS)
clean-fonts:
	rm -rf $(ASSET_BUILD_DIR)/fonts

MODEL_TARGETS = ${BOB_TARGETS} ${COB_TARGETS}
models: $(MODEL_TARGETS)
clean-models:
	rm -rf $(ASSET_BUILD_DIR)/models

TEXTURE_TARGETS_DESKTOP = $(TEX2D_DDS_TARGETS)
TEXTURE_TARGETS_IOS = $(TEX2D_PVR_TARGETS)
TEXTURE_TARGETS_ANDROID = $(TEX2D_KTX_TARGETS)
TEXTURE_TARGETS_PREVIEW = $(TEX2D_PREVIEW_PNG_TARGETS) \
  $(TEX2D_PREVIEW_PNG_TARGETS_2)

clean-textures:
	rm -rf $(ASSET_BUILD_DIR)/textures

SCRIPT_TARGETS = $(SCRIPT_TARGETS_PY_1) $(SCRIPT_TARGETS_PYC_1) \
  $(SCRIPT_TARGETS_PY_2) $(SCRIPT_TARGETS_PYC_2) \
  $(WIN_EXTRAS_SCRIPT_TARGETS_PYC)
scripts: $(SCRIPT_TARGETS)
clean-scripts:
	rm -rf $(ASSET_BUILD_DIR)/scripts

ASSET_TARGETS_ALL = $(ASSET_TARGETS_IOS) $(ASSET_TARGETS_ANDROID) \
      $(ASSET_TARGETS_DESKTOP) $(ASSET_TARGETS_COMMON)

assets: $(ASSET_TARGETS_ALL)
assets-desktop: $(ASSET_TARGETS_DESKTOP) $(ASSET_TARGETS_COMMON)
assets-ios: $(ASSET_TARGETS_IOS) $(ASSET_TARGETS_COMMON)
assets-android: $(ASSET_TARGETS_ANDROID) $(ASSET_TARGETS_COMMON)

asset_sources: $(MODEL_SRC_TARGETS) $(TEX2D_SRC_TARGETS) $(CUBE_SRC_TARGETS)

clean:
	rm -rf $(ASSET_BUILD_DIR)

# TEMP EFROCACHE TESTING------------------------------------------------

foof: $(TEXTURE_TARGETS_DESKTOP) $(TEXTURE_TARGETS_IOS) \
  $(TEXTURE_TARGETS_ANDROID) $(TEXTURE_TARGETS_PREVIEW) $(MODEL_TARGETS)
	echo SUCCESSSSSSS

build/testfile_a: ../.efrocachemap
	@cd .. && tools/snippets efrocache_get assets/$@

EFROCACHE_FILES = build/testfile_a $(TEXTURE_TARGETS_DESKTOP) \
 $(TEXTURE_TARGETS_IOS) $(TEXTURE_TARGETS_ANDROID) $(TEXTURE_TARGETS_PREVIEW) \
 $(MODEL_TARGETS) $(AUDIO_TARGETS) $(DATA_TARGETS) $(SCRIPT_TARGETS_PY_2) \
 $(FONT_TARGETS)

MODERN_MAKE = $(shell $(TOOLS_DIR)/snippets get_modern_make)

# Build everything we want available in efrocache
efrocache_build: $(EFROCACHE_FILES)

# Print everything that'll go to efrocache.
# We have to be a bit roundabout here since make can choke on this huge
# arg list. So we use a file command workaround, but that requires us to
# go through non-standard make on mac (standard make is old and lacks it)
efrocache_list:
	@$(MODERN_MAKE) --quiet _efrocache_list

_efrocache_list:
	$(file >_efrocache_tmp_list,$(EFROCACHE_FILES))
	@cat _efrocache_tmp_list
	@rm _efrocache_tmp_list
# ---------------------------------------------------------------------

# None of these targets correspond to actual files; make sure make knows that.
.PHONY: desktop ios android audio clean-audio fonts clean-fonts \
      data clean-data models clean-models \
      clean-textures scripts clean-scripts \
      assets assets-desktop assets-ios assets-android asset_sources clean
