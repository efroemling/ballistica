# Released under the MIT License. See LICENSE for details.
#
################################################################################
#                                                                              #
#                               Asset Generation                               #
#                                                                              #
################################################################################

# Generally this Makefile should not be modified by hand. To add or remove
# assets, add or remove files under the src/assets directory and then run
# "make update" from the project root. That will update this file as well as
# other relevant files such as assets/manifest.json

# Generally you shouldn't need to use this Makefile directly. Targets in the
# root level Makefile should handle asset building for you. If you do use
# this Makefile directly for whatever reason, remember to pass -jX on the
# command line to speed up your builds. (with X being the number of procs
# in your machine)

PROJ_DIR = ../..
SRC_DIR = $(PROJ_DIR)/src
TOOLS_DIR = $(PROJ_DIR)/tools
BUILD_DIR = $(PROJ_DIR)/build/assets

PCOMMAND = $(TOOLS_DIR)/pcommand

# pcommandbatch can be much faster when running hundreds or thousands of
# commands, but has some downsides and limitations compared to regular
# pcommand. See tools/efrotools/pcommandbatch.py for more info on when to use
# which.
PCOMMANDBATCHBIN = $(PROJ_DIR)/.cache/pcommandbatch/pcommandbatch
ifeq ($(BA_PCOMMANDBATCH_ENABLE),0)
 PCOMMANDBATCH = $(PCOMMANDBATCHBIN)
 PCOMMANDBATCHFROMROOT = .cache/pcommandbatch/pcommandbatch
else
 PCOMMANDBATCH = $(TOOLS_DIR)/pcommand
 PCOMMANDBATCHFROMROOT = tools/pcommand
endif

# High level targets: generally these are what should be used here.

# Build everything needed for all platforms.
all:
	@$(PCOMMAND) warm_start_asset_build gui
	@$(MAKE) assets
	@$(PCOMMAND) clean_orphaned_assets

# Build everything needed for our cmake builds (linux, mac).
cmake:
	@$(PCOMMAND) warm_start_asset_build gui
	@$(MAKE) assets-cmake
	@$(PCOMMAND) clean_orphaned_assets

# Build everything needed for our server builds.
server:
	@$(PCOMMAND) warm_start_asset_build server
	@$(MAKE) assets-server
	@$(PCOMMAND) clean_orphaned_assets

# Build everything needed for x86 windows builds.
win-Win32:
	@$(PCOMMAND) warm_start_asset_build gui
	@$(MAKE) assets-win-Win32
	@$(PCOMMAND) clean_orphaned_assets

# Build everything needed for x86-64 windows builds.
win-x64:
	@$(PCOMMAND) warm_start_asset_build gui
	@$(MAKE) assets-win-x64
	@$(PCOMMAND) clean_orphaned_assets

# Build everything needed for x86 windows server builds.
win-server-Win32:
	@$(PCOMMAND) warm_start_asset_build server
	@$(MAKE) assets-win-server-Win32
	@$(PCOMMAND) clean_orphaned_assets

# Build everything needed for x86-64 windows server builds.
win-server-x64:
	@$(PCOMMAND) warm_start_asset_build server
	@$(MAKE) assets-win-server-x64
	@$(PCOMMAND) clean_orphaned_assets

# Build everything needed for our mac xcode builds.
mac:
	@$(PCOMMAND) warm_start_asset_build gui
	@$(MAKE) assets-mac
	@$(PCOMMAND) clean_orphaned_assets

# Build everything needed for our ios/tvos builds.
ios:
	@$(PCOMMAND) warm_start_asset_build gui
	@$(MAKE) assets-ios
	@$(PCOMMAND) clean_orphaned_assets

# Build everything needed for android.
android:
	@$(PCOMMAND) warm_start_asset_build gui
	@$(MAKE) assets-android
	@$(PCOMMAND) clean_orphaned_assets

MAKE_SCRIPTS = 1
MAKE_FONTS = 1
MAKE_DATA = 1

ASSET_TARGETS_COMMON_GUI =
ASSET_TARGETS_COMMON_SERVER =
ASSET_TARGETS_CMAKE =
ASSET_TARGETS_SERVER =
ASSET_TARGETS_MAC =
ASSET_TARGETS_WIN_WIN32 =
ASSET_TARGETS_WIN_X64 =
ASSET_TARGETS_WIN_SERVER_WIN32 =
ASSET_TARGETS_WIN_SERVER_X64 =
ASSET_TARGETS_IOS =
ASSET_TARGETS_ANDROID =

# (The legacy Maya master -> src .obj export flow lived here until
# 2026-06-12; mesh sources now live in the asset-package workspaces
# (decision #26), so the maya dependency scan + export rules are
# retired. Future Maya exports should target workspace checkouts.
# Audio/texture/mesh compiles followed in the same sweep once those
# kinds finished migrating to asset-packages.)

# FontData.
ifeq ($(MAKE_FONTS),1)
ASSET_TARGETS_COMMON_GUI += $(FONT_TARGETS)
ASSET_TARGETS_COMMON_SERVER += $(FONT_TARGETS)
endif

# Data.
ifeq ($(MAKE_DATA),1)
ASSET_TARGETS_COMMON_GUI += $(DATA_TARGETS)
ASSET_TARGETS_COMMON_SERVER += $(DATA_TARGETS)
endif

# Scripts
ifeq ($(MAKE_SCRIPTS),1)
ASSET_TARGETS_CMAKE += $(SCRIPT_TARGETS_CMAKE)
ASSET_TARGETS_SERVER += $(SCRIPT_TARGETS_SERVER)
ASSET_TARGETS_MAC += $(SCRIPT_TARGETS_MAC)
ASSET_TARGETS_WIN_WIN32 += $(SCRIPT_TARGETS_WIN_WIN32)
ASSET_TARGETS_WIN_X64 += $(SCRIPT_TARGETS_WIN_X64)
ASSET_TARGETS_WIN_SERVER_WIN32 += $(SCRIPT_TARGETS_WIN_WIN32)
ASSET_TARGETS_WIN_SERVER_X64 += $(SCRIPT_TARGETS_WIN_X64)
ASSET_TARGETS_IOS += $(SCRIPT_TARGETS_IOS)
ASSET_TARGETS_ANDROID += $(SCRIPT_TARGETS_ANDROID)
ASSET_TARGETS_COMMON_GUI += $(SCRIPT_TARGETS_COMMON)
ASSET_TARGETS_COMMON_SERVER += $(SCRIPT_TARGETS_COMMON)
endif

# Extras
ASSET_TARGETS_WIN_WIN32 += $(EXTRAS_TARGETS_WIN_WIN32)
ASSET_TARGETS_WIN_X64 += $(EXTRAS_TARGETS_WIN_X64)
ASSET_TARGETS_WIN_SERVER_WIN32 += $(EXTRAS_TARGETS_WIN_WIN32)
ASSET_TARGETS_WIN_SERVER_X64 += $(EXTRAS_TARGETS_WIN_X64)

# Windows ARM64 asset staging (future windows-arm64 builds). Not
# pulled into any gui/server aggregate yet; the win-arm64-staging
# target (defined near the end of this file, after the generated
# lists it consumes) builds it on demand.
ASSET_TARGETS_WIN_ARM64 = $(SCRIPT_TARGETS_WIN_ARM64) \
 $(EXTRAS_TARGETS_WIN_ARM64)

# Asset bundle (the construct-mode minimum: an English language
# bucket + a regular-quality texture bucket + the constant
# bucket, for the asset-package version named in
# projectconfig.json's "assets" field). Two variants:
#
# - gui: fallback-profile (real renderable) textures. Pulled
#   in by GUI build targets.
# - headless: null-profile textures (single shared empty blob
#   per logical texture path) so headless server builds keep
#   the same wrapper-module layout and type-checks without
#   shipping image data.
#
# Both variants emit ``manifest.json`` at
# ``$(PROJ_DIR)/.cache/asset_bundle/<variant>/manifest.json``
# and share the same CAS blob store at
# ``$(PROJ_DIR)/.cache/assetdata/``. Staging picks the right
# variant per platform.
#
# These ride the COMMON_GUI / COMMON_SERVER lists so EVERY gui /
# server asset target assembles the bundle through the identical
# rule -- internal cmake/xcode builds and public prefab builds
# alike. The only per-build difference is environmental (dev-vs-prod
# pin, authenticated-vs-anonymous bacloud), not a separate code path.
ASSET_TARGETS_COMMON_GUI += \
  $(PROJ_DIR)/.cache/asset_bundle/gui-minimal/manifest.json
ASSET_TARGETS_COMMON_SERVER += \
  $(PROJ_DIR)/.cache/asset_bundle/headless-minimal/manifest.json

# This section is generated by batools.assetsmakefile; do not edit by hand.
# __AUTOGENERATED_PUBLIC_BEGIN__

SCRIPT_TARGETS_PY_PUBLIC = \
  $(BUILD_DIR)/ba_data/python/babase/__init__.py \
  $(BUILD_DIR)/ba_data/python/babase/_accountv2.py \
  $(BUILD_DIR)/ba_data/python/babase/_analytics.py \
  $(BUILD_DIR)/ba_data/python/babase/_app.py \
  $(BUILD_DIR)/ba_data/python/babase/_appcomponent.py \
  $(BUILD_DIR)/ba_data/python/babase/_appconfig.py \
  $(BUILD_DIR)/ba_data/python/babase/_appintent.py \
  $(BUILD_DIR)/ba_data/python/babase/_appmode.py \
  $(BUILD_DIR)/ba_data/python/babase/_appmodeselector.py \
  $(BUILD_DIR)/ba_data/python/babase/_appsubsystem.py \
  $(BUILD_DIR)/ba_data/python/babase/_apputils.py \
  $(BUILD_DIR)/ba_data/python/babase/_asset_packages.py \
  $(BUILD_DIR)/ba_data/python/babase/_assetsubsystem.py \
  $(BUILD_DIR)/ba_data/python/babase/_assetwrap.py \
  $(BUILD_DIR)/ba_data/python/babase/_asyncio.py \
  $(BUILD_DIR)/ba_data/python/babase/_automation.py \
  $(BUILD_DIR)/ba_data/python/babase/_baeventloop.py \
  $(BUILD_DIR)/ba_data/python/babase/_cloud.py \
  $(BUILD_DIR)/ba_data/python/babase/_constructmode.py \
  $(BUILD_DIR)/ba_data/python/babase/_devconsole.py \
  $(BUILD_DIR)/ba_data/python/babase/_devconsoletabs.py \
  $(BUILD_DIR)/ba_data/python/babase/_emptyappmode.py \
  $(BUILD_DIR)/ba_data/python/babase/_env.py \
  $(BUILD_DIR)/ba_data/python/babase/_error.py \
  $(BUILD_DIR)/ba_data/python/babase/_gc.py \
  $(BUILD_DIR)/ba_data/python/babase/_general.py \
  $(BUILD_DIR)/ba_data/python/babase/_generated/__init__.py \
  $(BUILD_DIR)/ba_data/python/babase/_generated/enums.py \
  $(BUILD_DIR)/ba_data/python/babase/_hooks.py \
  $(BUILD_DIR)/ba_data/python/babase/_language.py \
  $(BUILD_DIR)/ba_data/python/babase/_locale.py \
  $(BUILD_DIR)/ba_data/python/babase/_logging.py \
  $(BUILD_DIR)/ba_data/python/babase/_login.py \
  $(BUILD_DIR)/ba_data/python/babase/_math.py \
  $(BUILD_DIR)/ba_data/python/babase/_meta.py \
  $(BUILD_DIR)/ba_data/python/babase/_net.py \
  $(BUILD_DIR)/ba_data/python/babase/_plugin.py \
  $(BUILD_DIR)/ba_data/python/babase/_simpledialog.py \
  $(BUILD_DIR)/ba_data/python/babase/_stringedit.py \
  $(BUILD_DIR)/ba_data/python/babase/_text.py \
  $(BUILD_DIR)/ba_data/python/babase/_ui.py \
  $(BUILD_DIR)/ba_data/python/babase/_workspace.py \
  $(BUILD_DIR)/ba_data/python/babase/modutils.py \
  $(BUILD_DIR)/ba_data/python/baclassic/__init__.py \
  $(BUILD_DIR)/ba_data/python/baclassic/_accountv1.py \
  $(BUILD_DIR)/ba_data/python/baclassic/_achievement.py \
  $(BUILD_DIR)/ba_data/python/baclassic/_analytics.py \
  $(BUILD_DIR)/ba_data/python/baclassic/_appmode.py \
  $(BUILD_DIR)/ba_data/python/baclassic/_appsubsystem.py \
  $(BUILD_DIR)/ba_data/python/baclassic/_benchmark.py \
  $(BUILD_DIR)/ba_data/python/baclassic/_chest.py \
  $(BUILD_DIR)/ba_data/python/baclassic/_clienteffect.py \
  $(BUILD_DIR)/ba_data/python/baclassic/_displayitem.py \
  $(BUILD_DIR)/ba_data/python/baclassic/_hooks.py \
  $(BUILD_DIR)/ba_data/python/baclassic/_input.py \
  $(BUILD_DIR)/ba_data/python/baclassic/_music.py \
  $(BUILD_DIR)/ba_data/python/baclassic/_net.py \
  $(BUILD_DIR)/ba_data/python/baclassic/_servermode.py \
  $(BUILD_DIR)/ba_data/python/baclassic/_store.py \
  $(BUILD_DIR)/ba_data/python/baclassic/_tips.py \
  $(BUILD_DIR)/ba_data/python/baclassic/_tournament.py \
  $(BUILD_DIR)/ba_data/python/baclassic/macmusicapp.py \
  $(BUILD_DIR)/ba_data/python/baclassic/osmusic.py \
  $(BUILD_DIR)/ba_data/python/baenv.py \
  $(BUILD_DIR)/ba_data/python/baplus/__init__.py \
  $(BUILD_DIR)/ba_data/python/baplus/_ads.py \
  $(BUILD_DIR)/ba_data/python/baplus/_appsubsystem.py \
  $(BUILD_DIR)/ba_data/python/baplus/_cloud.py \
  $(BUILD_DIR)/ba_data/python/baplus/_hooks.py \
  $(BUILD_DIR)/ba_data/python/bascenev1/__init__.py \
  $(BUILD_DIR)/ba_data/python/bascenev1/_activity.py \
  $(BUILD_DIR)/ba_data/python/bascenev1/_activitytypes.py \
  $(BUILD_DIR)/ba_data/python/bascenev1/_actor.py \
  $(BUILD_DIR)/ba_data/python/bascenev1/_assetwrap.py \
  $(BUILD_DIR)/ba_data/python/bascenev1/_campaign.py \
  $(BUILD_DIR)/ba_data/python/bascenev1/_collision.py \
  $(BUILD_DIR)/ba_data/python/bascenev1/_coopgame.py \
  $(BUILD_DIR)/ba_data/python/bascenev1/_coopsession.py \
  $(BUILD_DIR)/ba_data/python/bascenev1/_debug.py \
  $(BUILD_DIR)/ba_data/python/bascenev1/_dualteamsession.py \
  $(BUILD_DIR)/ba_data/python/bascenev1/_featureset.py \
  $(BUILD_DIR)/ba_data/python/bascenev1/_freeforallsession.py \
  $(BUILD_DIR)/ba_data/python/bascenev1/_gameactivity.py \
  $(BUILD_DIR)/ba_data/python/bascenev1/_gameresults.py \
  $(BUILD_DIR)/ba_data/python/bascenev1/_gameutils.py \
  $(BUILD_DIR)/ba_data/python/bascenev1/_hooks.py \
  $(BUILD_DIR)/ba_data/python/bascenev1/_level.py \
  $(BUILD_DIR)/ba_data/python/bascenev1/_lobby.py \
  $(BUILD_DIR)/ba_data/python/bascenev1/_map.py \
  $(BUILD_DIR)/ba_data/python/bascenev1/_messages.py \
  $(BUILD_DIR)/ba_data/python/bascenev1/_multiteamsession.py \
  $(BUILD_DIR)/ba_data/python/bascenev1/_music.py \
  $(BUILD_DIR)/ba_data/python/bascenev1/_net.py \
  $(BUILD_DIR)/ba_data/python/bascenev1/_nodeactor.py \
  $(BUILD_DIR)/ba_data/python/bascenev1/_player.py \
  $(BUILD_DIR)/ba_data/python/bascenev1/_playlist.py \
  $(BUILD_DIR)/ba_data/python/bascenev1/_powerup.py \
  $(BUILD_DIR)/ba_data/python/bascenev1/_profile.py \
  $(BUILD_DIR)/ba_data/python/bascenev1/_score.py \
  $(BUILD_DIR)/ba_data/python/bascenev1/_session.py \
  $(BUILD_DIR)/ba_data/python/bascenev1/_settings.py \
  $(BUILD_DIR)/ba_data/python/bascenev1/_stats.py \
  $(BUILD_DIR)/ba_data/python/bascenev1/_team.py \
  $(BUILD_DIR)/ba_data/python/bascenev1/_teamgame.py \
  $(BUILD_DIR)/ba_data/python/bascenev1/builtinassets.py \
  $(BUILD_DIR)/ba_data/python/bascenev1/stdassets.py \
  $(BUILD_DIR)/ba_data/python/bascenev1lib/__init__.py \
  $(BUILD_DIR)/ba_data/python/bascenev1lib/activity/__init__.py \
  $(BUILD_DIR)/ba_data/python/bascenev1lib/activity/coopjoin.py \
  $(BUILD_DIR)/ba_data/python/bascenev1lib/activity/coopscore.py \
  $(BUILD_DIR)/ba_data/python/bascenev1lib/activity/drawscore.py \
  $(BUILD_DIR)/ba_data/python/bascenev1lib/activity/dualteamscore.py \
  $(BUILD_DIR)/ba_data/python/bascenev1lib/activity/freeforallvictory.py \
  $(BUILD_DIR)/ba_data/python/bascenev1lib/activity/multiteamjoin.py \
  $(BUILD_DIR)/ba_data/python/bascenev1lib/activity/multiteamscore.py \
  $(BUILD_DIR)/ba_data/python/bascenev1lib/activity/multiteamvictory.py \
  $(BUILD_DIR)/ba_data/python/bascenev1lib/actor/__init__.py \
  $(BUILD_DIR)/ba_data/python/bascenev1lib/actor/background.py \
  $(BUILD_DIR)/ba_data/python/bascenev1lib/actor/bomb.py \
  $(BUILD_DIR)/ba_data/python/bascenev1lib/actor/controlsguide.py \
  $(BUILD_DIR)/ba_data/python/bascenev1lib/actor/flag.py \
  $(BUILD_DIR)/ba_data/python/bascenev1lib/actor/image.py \
  $(BUILD_DIR)/ba_data/python/bascenev1lib/actor/onscreencountdown.py \
  $(BUILD_DIR)/ba_data/python/bascenev1lib/actor/onscreentimer.py \
  $(BUILD_DIR)/ba_data/python/bascenev1lib/actor/playerspaz.py \
  $(BUILD_DIR)/ba_data/python/bascenev1lib/actor/popuptext.py \
  $(BUILD_DIR)/ba_data/python/bascenev1lib/actor/powerupbox.py \
  $(BUILD_DIR)/ba_data/python/bascenev1lib/actor/respawnicon.py \
  $(BUILD_DIR)/ba_data/python/bascenev1lib/actor/scoreboard.py \
  $(BUILD_DIR)/ba_data/python/bascenev1lib/actor/spawner.py \
  $(BUILD_DIR)/ba_data/python/bascenev1lib/actor/spaz.py \
  $(BUILD_DIR)/ba_data/python/bascenev1lib/actor/spazappearance.py \
  $(BUILD_DIR)/ba_data/python/bascenev1lib/actor/spazbot.py \
  $(BUILD_DIR)/ba_data/python/bascenev1lib/actor/spazfactory.py \
  $(BUILD_DIR)/ba_data/python/bascenev1lib/actor/text.py \
  $(BUILD_DIR)/ba_data/python/bascenev1lib/actor/tipstext.py \
  $(BUILD_DIR)/ba_data/python/bascenev1lib/actor/zoomtext.py \
  $(BUILD_DIR)/ba_data/python/bascenev1lib/game/__init__.py \
  $(BUILD_DIR)/ba_data/python/bascenev1lib/game/assault.py \
  $(BUILD_DIR)/ba_data/python/bascenev1lib/game/capturetheflag.py \
  $(BUILD_DIR)/ba_data/python/bascenev1lib/game/chosenone.py \
  $(BUILD_DIR)/ba_data/python/bascenev1lib/game/conquest.py \
  $(BUILD_DIR)/ba_data/python/bascenev1lib/game/deathmatch.py \
  $(BUILD_DIR)/ba_data/python/bascenev1lib/game/easteregghunt.py \
  $(BUILD_DIR)/ba_data/python/bascenev1lib/game/elimination.py \
  $(BUILD_DIR)/ba_data/python/bascenev1lib/game/football.py \
  $(BUILD_DIR)/ba_data/python/bascenev1lib/game/hockey.py \
  $(BUILD_DIR)/ba_data/python/bascenev1lib/game/keepaway.py \
  $(BUILD_DIR)/ba_data/python/bascenev1lib/game/kingofthehill.py \
  $(BUILD_DIR)/ba_data/python/bascenev1lib/game/meteorshower.py \
  $(BUILD_DIR)/ba_data/python/bascenev1lib/game/ninjafight.py \
  $(BUILD_DIR)/ba_data/python/bascenev1lib/game/onslaught.py \
  $(BUILD_DIR)/ba_data/python/bascenev1lib/game/race.py \
  $(BUILD_DIR)/ba_data/python/bascenev1lib/game/runaround.py \
  $(BUILD_DIR)/ba_data/python/bascenev1lib/game/targetpractice.py \
  $(BUILD_DIR)/ba_data/python/bascenev1lib/game/thelaststand.py \
  $(BUILD_DIR)/ba_data/python/bascenev1lib/gameutils.py \
  $(BUILD_DIR)/ba_data/python/bascenev1lib/mainmenu.py \
  $(BUILD_DIR)/ba_data/python/bascenev1lib/mapdata/__init__.py \
  $(BUILD_DIR)/ba_data/python/bascenev1lib/mapdata/big_g.py \
  $(BUILD_DIR)/ba_data/python/bascenev1lib/mapdata/bridgit.py \
  $(BUILD_DIR)/ba_data/python/bascenev1lib/mapdata/courtyard.py \
  $(BUILD_DIR)/ba_data/python/bascenev1lib/mapdata/crag_castle.py \
  $(BUILD_DIR)/ba_data/python/bascenev1lib/mapdata/doom_shroom.py \
  $(BUILD_DIR)/ba_data/python/bascenev1lib/mapdata/football_stadium.py \
  $(BUILD_DIR)/ba_data/python/bascenev1lib/mapdata/happy_thoughts.py \
  $(BUILD_DIR)/ba_data/python/bascenev1lib/mapdata/hockey_stadium.py \
  $(BUILD_DIR)/ba_data/python/bascenev1lib/mapdata/lake_frigid.py \
  $(BUILD_DIR)/ba_data/python/bascenev1lib/mapdata/monkey_face.py \
  $(BUILD_DIR)/ba_data/python/bascenev1lib/mapdata/rampage.py \
  $(BUILD_DIR)/ba_data/python/bascenev1lib/mapdata/roundabout.py \
  $(BUILD_DIR)/ba_data/python/bascenev1lib/mapdata/step_right_up.py \
  $(BUILD_DIR)/ba_data/python/bascenev1lib/mapdata/the_pad.py \
  $(BUILD_DIR)/ba_data/python/bascenev1lib/mapdata/tip_top.py \
  $(BUILD_DIR)/ba_data/python/bascenev1lib/mapdata/tower_d.py \
  $(BUILD_DIR)/ba_data/python/bascenev1lib/mapdata/zig_zag.py \
  $(BUILD_DIR)/ba_data/python/bascenev1lib/maps.py \
  $(BUILD_DIR)/ba_data/python/bascenev1lib/session/__init__.py \
  $(BUILD_DIR)/ba_data/python/bascenev1lib/tutorial.py \
  $(BUILD_DIR)/ba_data/python/batemplatefs/__init__.py \
  $(BUILD_DIR)/ba_data/python/batemplatefs/_appsubsystem.py \
  $(BUILD_DIR)/ba_data/python/batemplatefs/_hooks.py \
  $(BUILD_DIR)/ba_data/python/bauiv1/__init__.py \
  $(BUILD_DIR)/ba_data/python/bauiv1/_appsubsystem.py \
  $(BUILD_DIR)/ba_data/python/bauiv1/_assetwrap.py \
  $(BUILD_DIR)/ba_data/python/bauiv1/_automation.py \
  $(BUILD_DIR)/ba_data/python/bauiv1/_hooks.py \
  $(BUILD_DIR)/ba_data/python/bauiv1/_keyboard.py \
  $(BUILD_DIR)/ba_data/python/bauiv1/_uitypes.py \
  $(BUILD_DIR)/ba_data/python/bauiv1/_window.py \
  $(BUILD_DIR)/ba_data/python/bauiv1/builtinassets.py \
  $(BUILD_DIR)/ba_data/python/bauiv1/onscreenkeyboard.py \
  $(BUILD_DIR)/ba_data/python/bauiv1/stdassets.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/__init__.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/account/__init__.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/account/settings.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/account/signin.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/account/v2proxy.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/account/viewer.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/achievements.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/appinvite.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/characterpicker.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/chest.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/colorpicker.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/config.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/confirm.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/connect.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/connectivity.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/coop/__init__.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/coop/browser.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/coop/gamebutton.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/coop/level.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/coop/tournamentbutton.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/credits.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/discord.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/docui/__init__.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/docui/_controller.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/docui/_window.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/docui/v1prep/__init__.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/docui/v1prep/_calls.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/docui/v1prep/_calls2.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/docui/v1prep/_types.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/docuitest.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/fileselector.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/gather/__init__.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/gather/_gather.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/gather/abouttab.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/gather/manualtab.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/gather/nearbytab.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/gather/privatetab.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/gather/publictab.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/getremote.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/gettokens.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/help.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/iconpicker.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/inbox.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/ingamemenu.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/inventory.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/keyboard/__init__.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/keyboard/englishkeyboard.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/kiosk.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/league/__init__.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/league/presidency.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/league/rankwindow.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/mainmenu.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/party.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/partyqueue.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/play.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/playlist/__init__.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/playlist/addgame.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/playlist/browser.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/playlist/customizebrowser.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/playlist/edit.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/playlist/editcontroller.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/playlist/editgame.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/playlist/mapselect.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/playlist/share.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/playoptions.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/popup.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/profile/__init__.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/profile/edit.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/profile/upgrade.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/qrcode.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/radiogroup.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/report.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/resourcetypeinfo.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/sendinfo.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/serverdialog.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/settings/__init__.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/settings/advanced.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/settings/allsettings.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/settings/audio.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/settings/benchmarks.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/settings/controls.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/settings/devtools.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/settings/gamepad.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/settings/gamepadadvanced.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/settings/gamepadselect.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/settings/graphics.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/settings/keyboard.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/settings/nettesting.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/settings/plugins.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/settings/pluginsettings.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/settings/remoteapp.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/settings/testing.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/settings/touchscreen.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/settings/vrtesting.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/soundtrack/__init__.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/soundtrack/browser.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/soundtrack/edit.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/soundtrack/entrytypeselect.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/soundtrack/macmusicapp.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/store.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/tabs.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/teamnamescolors.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/template.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/tournamententry.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/tournamentscores.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/trophies.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/url.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/utils.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/v2upgrade.py \
  $(BUILD_DIR)/ba_data/python/bauiv1lib/watch.py \
  $(BUILD_DIR)/server_package/ballisticakit_server.py

SCRIPT_TARGETS_SO_PUBLIC = \
  

SCRIPT_TARGETS_ZSTDDICT_PUBLIC = \
  

# Rule to copy src asset scripts to dst.
# (and make non-writable so I'm less likely to accidentally edit them there)
$(SCRIPT_TARGETS_PY_PUBLIC) : $(BUILD_DIR)/%.py : %.py
	@$(PCOMMANDBATCH) copy_python_file $^ $@


SCRIPT_TARGETS_PY_PUBLIC_TOOLS = \
  $(BUILD_DIR)/ba_data/python/bacommon/__init__.py \
  $(BUILD_DIR)/ba_data/python/bacommon/analytics.py \
  $(BUILD_DIR)/ba_data/python/bacommon/app.py \
  $(BUILD_DIR)/ba_data/python/bacommon/assetcas.py \
  $(BUILD_DIR)/ba_data/python/bacommon/bacloud.py \
  $(BUILD_DIR)/ba_data/python/bacommon/build.py \
  $(BUILD_DIR)/ba_data/python/bacommon/classic/__init__.py \
  $(BUILD_DIR)/ba_data/python/bacommon/classic/_account.py \
  $(BUILD_DIR)/ba_data/python/bacommon/classic/_chest.py \
  $(BUILD_DIR)/ba_data/python/bacommon/classic/_classic.py \
  $(BUILD_DIR)/ba_data/python/bacommon/classic/_displayitem.py \
  $(BUILD_DIR)/ba_data/python/bacommon/classic/_msg.py \
  $(BUILD_DIR)/ba_data/python/bacommon/clienteffect.py \
  $(BUILD_DIR)/ba_data/python/bacommon/cloud.py \
  $(BUILD_DIR)/ba_data/python/bacommon/clouddialog/__init__.py \
  $(BUILD_DIR)/ba_data/python/bacommon/clouddialog/_clouddialog.py \
  $(BUILD_DIR)/ba_data/python/bacommon/clouddialog/basic.py \
  $(BUILD_DIR)/ba_data/python/bacommon/displayitem.py \
  $(BUILD_DIR)/ba_data/python/bacommon/docui/__init__.py \
  $(BUILD_DIR)/ba_data/python/bacommon/docui/_docui.py \
  $(BUILD_DIR)/ba_data/python/bacommon/docui/v1.py \
  $(BUILD_DIR)/ba_data/python/bacommon/locale.py \
  $(BUILD_DIR)/ba_data/python/bacommon/loctext.py \
  $(BUILD_DIR)/ba_data/python/bacommon/loggercontrol.py \
  $(BUILD_DIR)/ba_data/python/bacommon/logging.py \
  $(BUILD_DIR)/ba_data/python/bacommon/login.py \
  $(BUILD_DIR)/ba_data/python/bacommon/meshzstddict.py \
  $(BUILD_DIR)/ba_data/python/bacommon/metascan.py \
  $(BUILD_DIR)/ba_data/python/bacommon/msg/__init__.py \
  $(BUILD_DIR)/ba_data/python/bacommon/msg/basntosandbox.py \
  $(BUILD_DIR)/ba_data/python/bacommon/msg/sandboxtobasn.py \
  $(BUILD_DIR)/ba_data/python/bacommon/net.py \
  $(BUILD_DIR)/ba_data/python/bacommon/restapi/__init__.py \
  $(BUILD_DIR)/ba_data/python/bacommon/restapi/v1/__init__.py \
  $(BUILD_DIR)/ba_data/python/bacommon/restapi/v1/accounts.py \
  $(BUILD_DIR)/ba_data/python/bacommon/restapi/v1/prefabs.py \
  $(BUILD_DIR)/ba_data/python/bacommon/restapi/v1/workspaces.py \
  $(BUILD_DIR)/ba_data/python/bacommon/securedata.py \
  $(BUILD_DIR)/ba_data/python/bacommon/servermanager.py \
  $(BUILD_DIR)/ba_data/python/bacommon/text.py \
  $(BUILD_DIR)/ba_data/python/bacommon/transfer.py \
  $(BUILD_DIR)/ba_data/python/bacommon/workspace/__init__.py \
  $(BUILD_DIR)/ba_data/python/bacommon/workspace/assetsv1.py \
  $(BUILD_DIR)/ba_data/python/bacommontools/__init__.py \
  $(BUILD_DIR)/ba_data/python/bacommontools/bacloud.py \
  $(BUILD_DIR)/ba_data/python/bacommontools/meshcompile.py \
  $(BUILD_DIR)/ba_data/python/bacommontools/pcommands.py \
  $(BUILD_DIR)/ba_data/python/bacommontools/streamws.py \
  $(BUILD_DIR)/ba_data/python/efro/__init__.py \
  $(BUILD_DIR)/ba_data/python/efro/call.py \
  $(BUILD_DIR)/ba_data/python/efro/cloudshell.py \
  $(BUILD_DIR)/ba_data/python/efro/dataclassio/__init__.py \
  $(BUILD_DIR)/ba_data/python/efro/dataclassio/_api.py \
  $(BUILD_DIR)/ba_data/python/efro/dataclassio/_base.py \
  $(BUILD_DIR)/ba_data/python/efro/dataclassio/_inputter.py \
  $(BUILD_DIR)/ba_data/python/efro/dataclassio/_outputter.py \
  $(BUILD_DIR)/ba_data/python/efro/dataclassio/_pathcapture.py \
  $(BUILD_DIR)/ba_data/python/efro/dataclassio/_prep.py \
  $(BUILD_DIR)/ba_data/python/efro/dataclassio/extras.py \
  $(BUILD_DIR)/ba_data/python/efro/dataclassio/templatemultitype.py \
  $(BUILD_DIR)/ba_data/python/efro/debug.py \
  $(BUILD_DIR)/ba_data/python/efro/error.py \
  $(BUILD_DIR)/ba_data/python/efro/logging.py \
  $(BUILD_DIR)/ba_data/python/efro/message/__init__.py \
  $(BUILD_DIR)/ba_data/python/efro/message/_message.py \
  $(BUILD_DIR)/ba_data/python/efro/message/_module.py \
  $(BUILD_DIR)/ba_data/python/efro/message/_protocol.py \
  $(BUILD_DIR)/ba_data/python/efro/message/_receiver.py \
  $(BUILD_DIR)/ba_data/python/efro/message/_sender.py \
  $(BUILD_DIR)/ba_data/python/efro/rpc.py \
  $(BUILD_DIR)/ba_data/python/efro/rpcws.py \
  $(BUILD_DIR)/ba_data/python/efro/terminal.py \
  $(BUILD_DIR)/ba_data/python/efro/threadpool.py \
  $(BUILD_DIR)/ba_data/python/efro/util.py \
  $(BUILD_DIR)/ba_data/python/efro/venvpatch.py

SCRIPT_TARGETS_SO_PUBLIC_TOOLS = \
  

SCRIPT_TARGETS_ZSTDDICT_PUBLIC_TOOLS = \
  $(BUILD_DIR)/ba_data/python/bacommon/bob_v1.zstddict

# Rule to copy src asset scripts to dst.
# (and make non-writable so I'm less likely to accidentally edit them there)
$(SCRIPT_TARGETS_PY_PUBLIC_TOOLS) : $(BUILD_DIR)/ba_data/python/%.py : $(TOOLS_DIR)/%.py
	@$(PCOMMANDBATCH) copy_python_file $^ $@

# Rule to copy bundled .zstddict data files to dst.
# (and make non-writable so I'm less likely to accidentally edit them there)
$(SCRIPT_TARGETS_ZSTDDICT_PUBLIC_TOOLS) : $(BUILD_DIR)/ba_data/python/%.zstddict : $(TOOLS_DIR)/%.zstddict
	@$(PCOMMANDBATCH) copy_python_file $^ $@

# __AUTOGENERATED_PUBLIC_END__

# This section is generated by batools.assetsmakefile; do not edit by hand.
# __AUTOGENERATED_PRIVATE_BEGIN__

SCRIPT_TARGETS_PY_PRIVATE_APPLE_MAC = \
  $(BUILD_DIR)/pylib-apple/__future__.py \
  $(BUILD_DIR)/pylib-apple/__hello__.py \
  $(BUILD_DIR)/pylib-apple/_aix_support.py \
  $(BUILD_DIR)/pylib-apple/_android_support.py \
  $(BUILD_DIR)/pylib-apple/_apple_support.py \
  $(BUILD_DIR)/pylib-apple/_ast_unparse.py \
  $(BUILD_DIR)/pylib-apple/_collections_abc.py \
  $(BUILD_DIR)/pylib-apple/_colorize.py \
  $(BUILD_DIR)/pylib-apple/_compat_pickle.py \
  $(BUILD_DIR)/pylib-apple/_ios_support.py \
  $(BUILD_DIR)/pylib-apple/_markupbase.py \
  $(BUILD_DIR)/pylib-apple/_opcode_metadata.py \
  $(BUILD_DIR)/pylib-apple/_osx_support.py \
  $(BUILD_DIR)/pylib-apple/_py_abc.py \
  $(BUILD_DIR)/pylib-apple/_py_warnings.py \
  $(BUILD_DIR)/pylib-apple/_pydatetime.py \
  $(BUILD_DIR)/pylib-apple/_pydecimal.py \
  $(BUILD_DIR)/pylib-apple/_pyio.py \
  $(BUILD_DIR)/pylib-apple/_pylong.py \
  $(BUILD_DIR)/pylib-apple/_pyrepl/__init__.py \
  $(BUILD_DIR)/pylib-apple/_pyrepl/__main__.py \
  $(BUILD_DIR)/pylib-apple/_pyrepl/_module_completer.py \
  $(BUILD_DIR)/pylib-apple/_pyrepl/_threading_handler.py \
  $(BUILD_DIR)/pylib-apple/_pyrepl/base_eventqueue.py \
  $(BUILD_DIR)/pylib-apple/_pyrepl/commands.py \
  $(BUILD_DIR)/pylib-apple/_pyrepl/completing_reader.py \
  $(BUILD_DIR)/pylib-apple/_pyrepl/console.py \
  $(BUILD_DIR)/pylib-apple/_pyrepl/fancy_termios.py \
  $(BUILD_DIR)/pylib-apple/_pyrepl/historical_reader.py \
  $(BUILD_DIR)/pylib-apple/_pyrepl/input.py \
  $(BUILD_DIR)/pylib-apple/_pyrepl/keymap.py \
  $(BUILD_DIR)/pylib-apple/_pyrepl/main.py \
  $(BUILD_DIR)/pylib-apple/_pyrepl/pager.py \
  $(BUILD_DIR)/pylib-apple/_pyrepl/reader.py \
  $(BUILD_DIR)/pylib-apple/_pyrepl/readline.py \
  $(BUILD_DIR)/pylib-apple/_pyrepl/simple_interact.py \
  $(BUILD_DIR)/pylib-apple/_pyrepl/terminfo.py \
  $(BUILD_DIR)/pylib-apple/_pyrepl/trace.py \
  $(BUILD_DIR)/pylib-apple/_pyrepl/types.py \
  $(BUILD_DIR)/pylib-apple/_pyrepl/unix_console.py \
  $(BUILD_DIR)/pylib-apple/_pyrepl/unix_eventqueue.py \
  $(BUILD_DIR)/pylib-apple/_pyrepl/utils.py \
  $(BUILD_DIR)/pylib-apple/_pyrepl/windows_console.py \
  $(BUILD_DIR)/pylib-apple/_pyrepl/windows_eventqueue.py \
  $(BUILD_DIR)/pylib-apple/_sitebuiltins.py \
  $(BUILD_DIR)/pylib-apple/_strptime.py \
  $(BUILD_DIR)/pylib-apple/_sysconfigdata__darwin_darwin.py \
  $(BUILD_DIR)/pylib-apple/_sysconfigdata__ios_arm64-iphoneos.py \
  $(BUILD_DIR)/pylib-apple/_sysconfigdata__ios_arm64-iphonesimulator.py \
  $(BUILD_DIR)/pylib-apple/_sysconfigdata__ios_x86_64-iphonesimulator.py \
  $(BUILD_DIR)/pylib-apple/_sysconfigdata__tvos_arm64-appletvos.py \
  $(BUILD_DIR)/pylib-apple/_sysconfigdata__tvos_arm64-appletvsimulator.py \
  $(BUILD_DIR)/pylib-apple/_sysconfigdata__tvos_x86_64-appletvsimulator.py \
  $(BUILD_DIR)/pylib-apple/_sysconfigdata__visionos_arm64-xros.py \
  $(BUILD_DIR)/pylib-apple/_sysconfigdata__visionos_arm64-xrsimulator.py \
  $(BUILD_DIR)/pylib-apple/_threading_local.py \
  $(BUILD_DIR)/pylib-apple/_weakrefset.py \
  $(BUILD_DIR)/pylib-apple/abc.py \
  $(BUILD_DIR)/pylib-apple/annotationlib.py \
  $(BUILD_DIR)/pylib-apple/antigravity.py \
  $(BUILD_DIR)/pylib-apple/argparse.py \
  $(BUILD_DIR)/pylib-apple/ast.py \
  $(BUILD_DIR)/pylib-apple/asyncio/__init__.py \
  $(BUILD_DIR)/pylib-apple/asyncio/__main__.py \
  $(BUILD_DIR)/pylib-apple/asyncio/base_events.py \
  $(BUILD_DIR)/pylib-apple/asyncio/base_futures.py \
  $(BUILD_DIR)/pylib-apple/asyncio/base_subprocess.py \
  $(BUILD_DIR)/pylib-apple/asyncio/base_tasks.py \
  $(BUILD_DIR)/pylib-apple/asyncio/constants.py \
  $(BUILD_DIR)/pylib-apple/asyncio/coroutines.py \
  $(BUILD_DIR)/pylib-apple/asyncio/events.py \
  $(BUILD_DIR)/pylib-apple/asyncio/exceptions.py \
  $(BUILD_DIR)/pylib-apple/asyncio/format_helpers.py \
  $(BUILD_DIR)/pylib-apple/asyncio/futures.py \
  $(BUILD_DIR)/pylib-apple/asyncio/graph.py \
  $(BUILD_DIR)/pylib-apple/asyncio/locks.py \
  $(BUILD_DIR)/pylib-apple/asyncio/log.py \
  $(BUILD_DIR)/pylib-apple/asyncio/mixins.py \
  $(BUILD_DIR)/pylib-apple/asyncio/proactor_events.py \
  $(BUILD_DIR)/pylib-apple/asyncio/protocols.py \
  $(BUILD_DIR)/pylib-apple/asyncio/queues.py \
  $(BUILD_DIR)/pylib-apple/asyncio/runners.py \
  $(BUILD_DIR)/pylib-apple/asyncio/selector_events.py \
  $(BUILD_DIR)/pylib-apple/asyncio/sslproto.py \
  $(BUILD_DIR)/pylib-apple/asyncio/staggered.py \
  $(BUILD_DIR)/pylib-apple/asyncio/streams.py \
  $(BUILD_DIR)/pylib-apple/asyncio/subprocess.py \
  $(BUILD_DIR)/pylib-apple/asyncio/taskgroups.py \
  $(BUILD_DIR)/pylib-apple/asyncio/tasks.py \
  $(BUILD_DIR)/pylib-apple/asyncio/threads.py \
  $(BUILD_DIR)/pylib-apple/asyncio/timeouts.py \
  $(BUILD_DIR)/pylib-apple/asyncio/tools.py \
  $(BUILD_DIR)/pylib-apple/asyncio/transports.py \
  $(BUILD_DIR)/pylib-apple/asyncio/trsock.py \
  $(BUILD_DIR)/pylib-apple/asyncio/unix_events.py \
  $(BUILD_DIR)/pylib-apple/asyncio/windows_events.py \
  $(BUILD_DIR)/pylib-apple/asyncio/windows_utils.py \
  $(BUILD_DIR)/pylib-apple/base64.py \
  $(BUILD_DIR)/pylib-apple/bdb.py \
  $(BUILD_DIR)/pylib-apple/bisect.py \
  $(BUILD_DIR)/pylib-apple/bz2.py \
  $(BUILD_DIR)/pylib-apple/cProfile.py \
  $(BUILD_DIR)/pylib-apple/calendar.py \
  $(BUILD_DIR)/pylib-apple/cmd.py \
  $(BUILD_DIR)/pylib-apple/code.py \
  $(BUILD_DIR)/pylib-apple/codecs.py \
  $(BUILD_DIR)/pylib-apple/codeop.py \
  $(BUILD_DIR)/pylib-apple/collections/__init__.py \
  $(BUILD_DIR)/pylib-apple/colorsys.py \
  $(BUILD_DIR)/pylib-apple/compileall.py \
  $(BUILD_DIR)/pylib-apple/compression/__init__.py \
  $(BUILD_DIR)/pylib-apple/compression/_common/__init__.py \
  $(BUILD_DIR)/pylib-apple/compression/_common/_streams.py \
  $(BUILD_DIR)/pylib-apple/compression/bz2.py \
  $(BUILD_DIR)/pylib-apple/compression/gzip.py \
  $(BUILD_DIR)/pylib-apple/compression/lzma.py \
  $(BUILD_DIR)/pylib-apple/compression/zlib.py \
  $(BUILD_DIR)/pylib-apple/compression/zstd/__init__.py \
  $(BUILD_DIR)/pylib-apple/compression/zstd/_zstdfile.py \
  $(BUILD_DIR)/pylib-apple/concurrent/__init__.py \
  $(BUILD_DIR)/pylib-apple/concurrent/futures/__init__.py \
  $(BUILD_DIR)/pylib-apple/concurrent/futures/_base.py \
  $(BUILD_DIR)/pylib-apple/concurrent/futures/interpreter.py \
  $(BUILD_DIR)/pylib-apple/concurrent/futures/process.py \
  $(BUILD_DIR)/pylib-apple/concurrent/futures/thread.py \
  $(BUILD_DIR)/pylib-apple/concurrent/interpreters/__init__.py \
  $(BUILD_DIR)/pylib-apple/concurrent/interpreters/_crossinterp.py \
  $(BUILD_DIR)/pylib-apple/concurrent/interpreters/_queues.py \
  $(BUILD_DIR)/pylib-apple/configparser.py \
  $(BUILD_DIR)/pylib-apple/contextlib.py \
  $(BUILD_DIR)/pylib-apple/contextvars.py \
  $(BUILD_DIR)/pylib-apple/copy.py \
  $(BUILD_DIR)/pylib-apple/copyreg.py \
  $(BUILD_DIR)/pylib-apple/csv.py \
  $(BUILD_DIR)/pylib-apple/ctypes/__init__.py \
  $(BUILD_DIR)/pylib-apple/ctypes/_aix.py \
  $(BUILD_DIR)/pylib-apple/ctypes/_endian.py \
  $(BUILD_DIR)/pylib-apple/ctypes/_layout.py \
  $(BUILD_DIR)/pylib-apple/ctypes/macholib/__init__.py \
  $(BUILD_DIR)/pylib-apple/ctypes/macholib/dyld.py \
  $(BUILD_DIR)/pylib-apple/ctypes/macholib/dylib.py \
  $(BUILD_DIR)/pylib-apple/ctypes/macholib/framework.py \
  $(BUILD_DIR)/pylib-apple/ctypes/util.py \
  $(BUILD_DIR)/pylib-apple/ctypes/wintypes.py \
  $(BUILD_DIR)/pylib-apple/curses/__init__.py \
  $(BUILD_DIR)/pylib-apple/curses/ascii.py \
  $(BUILD_DIR)/pylib-apple/curses/has_key.py \
  $(BUILD_DIR)/pylib-apple/curses/panel.py \
  $(BUILD_DIR)/pylib-apple/curses/textpad.py \
  $(BUILD_DIR)/pylib-apple/dataclasses.py \
  $(BUILD_DIR)/pylib-apple/datetime.py \
  $(BUILD_DIR)/pylib-apple/decimal.py \
  $(BUILD_DIR)/pylib-apple/difflib.py \
  $(BUILD_DIR)/pylib-apple/dis.py \
  $(BUILD_DIR)/pylib-apple/doctest.py \
  $(BUILD_DIR)/pylib-apple/email/__init__.py \
  $(BUILD_DIR)/pylib-apple/email/_encoded_words.py \
  $(BUILD_DIR)/pylib-apple/email/_header_value_parser.py \
  $(BUILD_DIR)/pylib-apple/email/_parseaddr.py \
  $(BUILD_DIR)/pylib-apple/email/_policybase.py \
  $(BUILD_DIR)/pylib-apple/email/base64mime.py \
  $(BUILD_DIR)/pylib-apple/email/charset.py \
  $(BUILD_DIR)/pylib-apple/email/contentmanager.py \
  $(BUILD_DIR)/pylib-apple/email/encoders.py \
  $(BUILD_DIR)/pylib-apple/email/errors.py \
  $(BUILD_DIR)/pylib-apple/email/feedparser.py \
  $(BUILD_DIR)/pylib-apple/email/generator.py \
  $(BUILD_DIR)/pylib-apple/email/header.py \
  $(BUILD_DIR)/pylib-apple/email/headerregistry.py \
  $(BUILD_DIR)/pylib-apple/email/iterators.py \
  $(BUILD_DIR)/pylib-apple/email/message.py \
  $(BUILD_DIR)/pylib-apple/email/mime/__init__.py \
  $(BUILD_DIR)/pylib-apple/email/mime/application.py \
  $(BUILD_DIR)/pylib-apple/email/mime/audio.py \
  $(BUILD_DIR)/pylib-apple/email/mime/base.py \
  $(BUILD_DIR)/pylib-apple/email/mime/image.py \
  $(BUILD_DIR)/pylib-apple/email/mime/message.py \
  $(BUILD_DIR)/pylib-apple/email/mime/multipart.py \
  $(BUILD_DIR)/pylib-apple/email/mime/nonmultipart.py \
  $(BUILD_DIR)/pylib-apple/email/mime/text.py \
  $(BUILD_DIR)/pylib-apple/email/parser.py \
  $(BUILD_DIR)/pylib-apple/email/policy.py \
  $(BUILD_DIR)/pylib-apple/email/quoprimime.py \
  $(BUILD_DIR)/pylib-apple/email/utils.py \
  $(BUILD_DIR)/pylib-apple/encodings/__init__.py \
  $(BUILD_DIR)/pylib-apple/encodings/_win_cp_codecs.py \
  $(BUILD_DIR)/pylib-apple/encodings/aliases.py \
  $(BUILD_DIR)/pylib-apple/encodings/ascii.py \
  $(BUILD_DIR)/pylib-apple/encodings/base64_codec.py \
  $(BUILD_DIR)/pylib-apple/encodings/big5.py \
  $(BUILD_DIR)/pylib-apple/encodings/big5hkscs.py \
  $(BUILD_DIR)/pylib-apple/encodings/bz2_codec.py \
  $(BUILD_DIR)/pylib-apple/encodings/charmap.py \
  $(BUILD_DIR)/pylib-apple/encodings/cp037.py \
  $(BUILD_DIR)/pylib-apple/encodings/cp1006.py \
  $(BUILD_DIR)/pylib-apple/encodings/cp1026.py \
  $(BUILD_DIR)/pylib-apple/encodings/cp1125.py \
  $(BUILD_DIR)/pylib-apple/encodings/cp1140.py \
  $(BUILD_DIR)/pylib-apple/encodings/cp1250.py \
  $(BUILD_DIR)/pylib-apple/encodings/cp1251.py \
  $(BUILD_DIR)/pylib-apple/encodings/cp1252.py \
  $(BUILD_DIR)/pylib-apple/encodings/cp1253.py \
  $(BUILD_DIR)/pylib-apple/encodings/cp1254.py \
  $(BUILD_DIR)/pylib-apple/encodings/cp1255.py \
  $(BUILD_DIR)/pylib-apple/encodings/cp1256.py \
  $(BUILD_DIR)/pylib-apple/encodings/cp1257.py \
  $(BUILD_DIR)/pylib-apple/encodings/cp1258.py \
  $(BUILD_DIR)/pylib-apple/encodings/cp273.py \
  $(BUILD_DIR)/pylib-apple/encodings/cp424.py \
  $(BUILD_DIR)/pylib-apple/encodings/cp437.py \
  $(BUILD_DIR)/pylib-apple/encodings/cp500.py \
  $(BUILD_DIR)/pylib-apple/encodings/cp720.py \
  $(BUILD_DIR)/pylib-apple/encodings/cp737.py \
  $(BUILD_DIR)/pylib-apple/encodings/cp775.py \
  $(BUILD_DIR)/pylib-apple/encodings/cp850.py \
  $(BUILD_DIR)/pylib-apple/encodings/cp852.py \
  $(BUILD_DIR)/pylib-apple/encodings/cp855.py \
  $(BUILD_DIR)/pylib-apple/encodings/cp856.py \
  $(BUILD_DIR)/pylib-apple/encodings/cp857.py \
  $(BUILD_DIR)/pylib-apple/encodings/cp858.py \
  $(BUILD_DIR)/pylib-apple/encodings/cp860.py \
  $(BUILD_DIR)/pylib-apple/encodings/cp861.py \
  $(BUILD_DIR)/pylib-apple/encodings/cp862.py \
  $(BUILD_DIR)/pylib-apple/encodings/cp863.py \
  $(BUILD_DIR)/pylib-apple/encodings/cp864.py \
  $(BUILD_DIR)/pylib-apple/encodings/cp865.py \
  $(BUILD_DIR)/pylib-apple/encodings/cp866.py \
  $(BUILD_DIR)/pylib-apple/encodings/cp869.py \
  $(BUILD_DIR)/pylib-apple/encodings/cp874.py \
  $(BUILD_DIR)/pylib-apple/encodings/cp875.py \
  $(BUILD_DIR)/pylib-apple/encodings/cp932.py \
  $(BUILD_DIR)/pylib-apple/encodings/cp949.py \
  $(BUILD_DIR)/pylib-apple/encodings/cp950.py \
  $(BUILD_DIR)/pylib-apple/encodings/euc_jis_2004.py \
  $(BUILD_DIR)/pylib-apple/encodings/euc_jisx0213.py \
  $(BUILD_DIR)/pylib-apple/encodings/euc_jp.py \
  $(BUILD_DIR)/pylib-apple/encodings/euc_kr.py \
  $(BUILD_DIR)/pylib-apple/encodings/gb18030.py \
  $(BUILD_DIR)/pylib-apple/encodings/gb2312.py \
  $(BUILD_DIR)/pylib-apple/encodings/gbk.py \
  $(BUILD_DIR)/pylib-apple/encodings/hex_codec.py \
  $(BUILD_DIR)/pylib-apple/encodings/hp_roman8.py \
  $(BUILD_DIR)/pylib-apple/encodings/hz.py \
  $(BUILD_DIR)/pylib-apple/encodings/idna.py \
  $(BUILD_DIR)/pylib-apple/encodings/iso2022_jp.py \
  $(BUILD_DIR)/pylib-apple/encodings/iso2022_jp_1.py \
  $(BUILD_DIR)/pylib-apple/encodings/iso2022_jp_2.py \
  $(BUILD_DIR)/pylib-apple/encodings/iso2022_jp_2004.py \
  $(BUILD_DIR)/pylib-apple/encodings/iso2022_jp_3.py \
  $(BUILD_DIR)/pylib-apple/encodings/iso2022_jp_ext.py \
  $(BUILD_DIR)/pylib-apple/encodings/iso2022_kr.py \
  $(BUILD_DIR)/pylib-apple/encodings/iso8859_1.py \
  $(BUILD_DIR)/pylib-apple/encodings/iso8859_10.py \
  $(BUILD_DIR)/pylib-apple/encodings/iso8859_11.py \
  $(BUILD_DIR)/pylib-apple/encodings/iso8859_13.py \
  $(BUILD_DIR)/pylib-apple/encodings/iso8859_14.py \
  $(BUILD_DIR)/pylib-apple/encodings/iso8859_15.py \
  $(BUILD_DIR)/pylib-apple/encodings/iso8859_16.py \
  $(BUILD_DIR)/pylib-apple/encodings/iso8859_2.py \
  $(BUILD_DIR)/pylib-apple/encodings/iso8859_3.py \
  $(BUILD_DIR)/pylib-apple/encodings/iso8859_4.py \
  $(BUILD_DIR)/pylib-apple/encodings/iso8859_5.py \
  $(BUILD_DIR)/pylib-apple/encodings/iso8859_6.py \
  $(BUILD_DIR)/pylib-apple/encodings/iso8859_7.py \
  $(BUILD_DIR)/pylib-apple/encodings/iso8859_8.py \
  $(BUILD_DIR)/pylib-apple/encodings/iso8859_9.py \
  $(BUILD_DIR)/pylib-apple/encodings/johab.py \
  $(BUILD_DIR)/pylib-apple/encodings/koi8_r.py \
  $(BUILD_DIR)/pylib-apple/encodings/koi8_t.py \
  $(BUILD_DIR)/pylib-apple/encodings/koi8_u.py \
  $(BUILD_DIR)/pylib-apple/encodings/kz1048.py \
  $(BUILD_DIR)/pylib-apple/encodings/latin_1.py \
  $(BUILD_DIR)/pylib-apple/encodings/mac_arabic.py \
  $(BUILD_DIR)/pylib-apple/encodings/mac_croatian.py \
  $(BUILD_DIR)/pylib-apple/encodings/mac_cyrillic.py \
  $(BUILD_DIR)/pylib-apple/encodings/mac_farsi.py \
  $(BUILD_DIR)/pylib-apple/encodings/mac_greek.py \
  $(BUILD_DIR)/pylib-apple/encodings/mac_iceland.py \
  $(BUILD_DIR)/pylib-apple/encodings/mac_latin2.py \
  $(BUILD_DIR)/pylib-apple/encodings/mac_roman.py \
  $(BUILD_DIR)/pylib-apple/encodings/mac_romanian.py \
  $(BUILD_DIR)/pylib-apple/encodings/mac_turkish.py \
  $(BUILD_DIR)/pylib-apple/encodings/mbcs.py \
  $(BUILD_DIR)/pylib-apple/encodings/oem.py \
  $(BUILD_DIR)/pylib-apple/encodings/palmos.py \
  $(BUILD_DIR)/pylib-apple/encodings/ptcp154.py \
  $(BUILD_DIR)/pylib-apple/encodings/punycode.py \
  $(BUILD_DIR)/pylib-apple/encodings/quopri_codec.py \
  $(BUILD_DIR)/pylib-apple/encodings/raw_unicode_escape.py \
  $(BUILD_DIR)/pylib-apple/encodings/rot_13.py \
  $(BUILD_DIR)/pylib-apple/encodings/shift_jis.py \
  $(BUILD_DIR)/pylib-apple/encodings/shift_jis_2004.py \
  $(BUILD_DIR)/pylib-apple/encodings/shift_jisx0213.py \
  $(BUILD_DIR)/pylib-apple/encodings/tis_620.py \
  $(BUILD_DIR)/pylib-apple/encodings/undefined.py \
  $(BUILD_DIR)/pylib-apple/encodings/unicode_escape.py \
  $(BUILD_DIR)/pylib-apple/encodings/utf_16.py \
  $(BUILD_DIR)/pylib-apple/encodings/utf_16_be.py \
  $(BUILD_DIR)/pylib-apple/encodings/utf_16_le.py \
  $(BUILD_DIR)/pylib-apple/encodings/utf_32.py \
  $(BUILD_DIR)/pylib-apple/encodings/utf_32_be.py \
  $(BUILD_DIR)/pylib-apple/encodings/utf_32_le.py \
  $(BUILD_DIR)/pylib-apple/encodings/utf_7.py \
  $(BUILD_DIR)/pylib-apple/encodings/utf_8.py \
  $(BUILD_DIR)/pylib-apple/encodings/utf_8_sig.py \
  $(BUILD_DIR)/pylib-apple/encodings/uu_codec.py \
  $(BUILD_DIR)/pylib-apple/encodings/zlib_codec.py \
  $(BUILD_DIR)/pylib-apple/enum.py \
  $(BUILD_DIR)/pylib-apple/filecmp.py \
  $(BUILD_DIR)/pylib-apple/fileinput.py \
  $(BUILD_DIR)/pylib-apple/fnmatch.py \
  $(BUILD_DIR)/pylib-apple/fractions.py \
  $(BUILD_DIR)/pylib-apple/ftplib.py \
  $(BUILD_DIR)/pylib-apple/functools.py \
  $(BUILD_DIR)/pylib-apple/genericpath.py \
  $(BUILD_DIR)/pylib-apple/getopt.py \
  $(BUILD_DIR)/pylib-apple/getpass.py \
  $(BUILD_DIR)/pylib-apple/gettext.py \
  $(BUILD_DIR)/pylib-apple/glob.py \
  $(BUILD_DIR)/pylib-apple/graphlib.py \
  $(BUILD_DIR)/pylib-apple/gzip.py \
  $(BUILD_DIR)/pylib-apple/hashlib.py \
  $(BUILD_DIR)/pylib-apple/heapq.py \
  $(BUILD_DIR)/pylib-apple/hmac.py \
  $(BUILD_DIR)/pylib-apple/html/__init__.py \
  $(BUILD_DIR)/pylib-apple/html/entities.py \
  $(BUILD_DIR)/pylib-apple/html/parser.py \
  $(BUILD_DIR)/pylib-apple/http/__init__.py \
  $(BUILD_DIR)/pylib-apple/http/client.py \
  $(BUILD_DIR)/pylib-apple/http/cookiejar.py \
  $(BUILD_DIR)/pylib-apple/http/cookies.py \
  $(BUILD_DIR)/pylib-apple/http/server.py \
  $(BUILD_DIR)/pylib-apple/importlib/__init__.py \
  $(BUILD_DIR)/pylib-apple/importlib/_abc.py \
  $(BUILD_DIR)/pylib-apple/importlib/_bootstrap.py \
  $(BUILD_DIR)/pylib-apple/importlib/_bootstrap_external.py \
  $(BUILD_DIR)/pylib-apple/importlib/abc.py \
  $(BUILD_DIR)/pylib-apple/importlib/machinery.py \
  $(BUILD_DIR)/pylib-apple/importlib/metadata/__init__.py \
  $(BUILD_DIR)/pylib-apple/importlib/metadata/_adapters.py \
  $(BUILD_DIR)/pylib-apple/importlib/metadata/_collections.py \
  $(BUILD_DIR)/pylib-apple/importlib/metadata/_functools.py \
  $(BUILD_DIR)/pylib-apple/importlib/metadata/_itertools.py \
  $(BUILD_DIR)/pylib-apple/importlib/metadata/_meta.py \
  $(BUILD_DIR)/pylib-apple/importlib/metadata/_text.py \
  $(BUILD_DIR)/pylib-apple/importlib/metadata/diagnose.py \
  $(BUILD_DIR)/pylib-apple/importlib/readers.py \
  $(BUILD_DIR)/pylib-apple/importlib/resources/__init__.py \
  $(BUILD_DIR)/pylib-apple/importlib/resources/_adapters.py \
  $(BUILD_DIR)/pylib-apple/importlib/resources/_common.py \
  $(BUILD_DIR)/pylib-apple/importlib/resources/_functional.py \
  $(BUILD_DIR)/pylib-apple/importlib/resources/_itertools.py \
  $(BUILD_DIR)/pylib-apple/importlib/resources/abc.py \
  $(BUILD_DIR)/pylib-apple/importlib/resources/readers.py \
  $(BUILD_DIR)/pylib-apple/importlib/resources/simple.py \
  $(BUILD_DIR)/pylib-apple/importlib/simple.py \
  $(BUILD_DIR)/pylib-apple/importlib/util.py \
  $(BUILD_DIR)/pylib-apple/inspect.py \
  $(BUILD_DIR)/pylib-apple/io.py \
  $(BUILD_DIR)/pylib-apple/ipaddress.py \
  $(BUILD_DIR)/pylib-apple/json/__init__.py \
  $(BUILD_DIR)/pylib-apple/json/__main__.py \
  $(BUILD_DIR)/pylib-apple/json/decoder.py \
  $(BUILD_DIR)/pylib-apple/json/encoder.py \
  $(BUILD_DIR)/pylib-apple/json/scanner.py \
  $(BUILD_DIR)/pylib-apple/json/tool.py \
  $(BUILD_DIR)/pylib-apple/keyword.py \
  $(BUILD_DIR)/pylib-apple/linecache.py \
  $(BUILD_DIR)/pylib-apple/locale.py \
  $(BUILD_DIR)/pylib-apple/logging/__init__.py \
  $(BUILD_DIR)/pylib-apple/logging/config.py \
  $(BUILD_DIR)/pylib-apple/logging/handlers.py \
  $(BUILD_DIR)/pylib-apple/lzma.py \
  $(BUILD_DIR)/pylib-apple/mailbox.py \
  $(BUILD_DIR)/pylib-apple/mimetypes.py \
  $(BUILD_DIR)/pylib-apple/modulefinder.py \
  $(BUILD_DIR)/pylib-apple/netrc.py \
  $(BUILD_DIR)/pylib-apple/ntpath.py \
  $(BUILD_DIR)/pylib-apple/nturl2path.py \
  $(BUILD_DIR)/pylib-apple/numbers.py \
  $(BUILD_DIR)/pylib-apple/opcode.py \
  $(BUILD_DIR)/pylib-apple/operator.py \
  $(BUILD_DIR)/pylib-apple/optparse.py \
  $(BUILD_DIR)/pylib-apple/os.py \
  $(BUILD_DIR)/pylib-apple/pathlib/__init__.py \
  $(BUILD_DIR)/pylib-apple/pathlib/_local.py \
  $(BUILD_DIR)/pylib-apple/pathlib/_os.py \
  $(BUILD_DIR)/pylib-apple/pathlib/types.py \
  $(BUILD_DIR)/pylib-apple/pdb.py \
  $(BUILD_DIR)/pylib-apple/pickle.py \
  $(BUILD_DIR)/pylib-apple/pickletools.py \
  $(BUILD_DIR)/pylib-apple/pkgutil.py \
  $(BUILD_DIR)/pylib-apple/platform.py \
  $(BUILD_DIR)/pylib-apple/plistlib.py \
  $(BUILD_DIR)/pylib-apple/poplib.py \
  $(BUILD_DIR)/pylib-apple/posixpath.py \
  $(BUILD_DIR)/pylib-apple/pprint.py \
  $(BUILD_DIR)/pylib-apple/profile.py \
  $(BUILD_DIR)/pylib-apple/pstats.py \
  $(BUILD_DIR)/pylib-apple/pty.py \
  $(BUILD_DIR)/pylib-apple/py_compile.py \
  $(BUILD_DIR)/pylib-apple/pyclbr.py \
  $(BUILD_DIR)/pylib-apple/pydoc.py \
  $(BUILD_DIR)/pylib-apple/queue.py \
  $(BUILD_DIR)/pylib-apple/quopri.py \
  $(BUILD_DIR)/pylib-apple/random.py \
  $(BUILD_DIR)/pylib-apple/re/__init__.py \
  $(BUILD_DIR)/pylib-apple/re/_casefix.py \
  $(BUILD_DIR)/pylib-apple/re/_compiler.py \
  $(BUILD_DIR)/pylib-apple/re/_constants.py \
  $(BUILD_DIR)/pylib-apple/re/_parser.py \
  $(BUILD_DIR)/pylib-apple/reprlib.py \
  $(BUILD_DIR)/pylib-apple/rlcompleter.py \
  $(BUILD_DIR)/pylib-apple/runpy.py \
  $(BUILD_DIR)/pylib-apple/sched.py \
  $(BUILD_DIR)/pylib-apple/secrets.py \
  $(BUILD_DIR)/pylib-apple/selectors.py \
  $(BUILD_DIR)/pylib-apple/shelve.py \
  $(BUILD_DIR)/pylib-apple/shlex.py \
  $(BUILD_DIR)/pylib-apple/shutil.py \
  $(BUILD_DIR)/pylib-apple/signal.py \
  $(BUILD_DIR)/pylib-apple/site.py \
  $(BUILD_DIR)/pylib-apple/smtplib.py \
  $(BUILD_DIR)/pylib-apple/socket.py \
  $(BUILD_DIR)/pylib-apple/socketserver.py \
  $(BUILD_DIR)/pylib-apple/sqlite3/__init__.py \
  $(BUILD_DIR)/pylib-apple/sqlite3/__main__.py \
  $(BUILD_DIR)/pylib-apple/sqlite3/dbapi2.py \
  $(BUILD_DIR)/pylib-apple/sqlite3/dump.py \
  $(BUILD_DIR)/pylib-apple/sre_compile.py \
  $(BUILD_DIR)/pylib-apple/sre_constants.py \
  $(BUILD_DIR)/pylib-apple/sre_parse.py \
  $(BUILD_DIR)/pylib-apple/ssl.py \
  $(BUILD_DIR)/pylib-apple/stat.py \
  $(BUILD_DIR)/pylib-apple/statistics.py \
  $(BUILD_DIR)/pylib-apple/string/__init__.py \
  $(BUILD_DIR)/pylib-apple/string/templatelib.py \
  $(BUILD_DIR)/pylib-apple/stringprep.py \
  $(BUILD_DIR)/pylib-apple/struct.py \
  $(BUILD_DIR)/pylib-apple/subprocess.py \
  $(BUILD_DIR)/pylib-apple/symtable.py \
  $(BUILD_DIR)/pylib-apple/sysconfig/__init__.py \
  $(BUILD_DIR)/pylib-apple/sysconfig/__main__.py \
  $(BUILD_DIR)/pylib-apple/tabnanny.py \
  $(BUILD_DIR)/pylib-apple/tarfile.py \
  $(BUILD_DIR)/pylib-apple/tempfile.py \
  $(BUILD_DIR)/pylib-apple/textwrap.py \
  $(BUILD_DIR)/pylib-apple/this.py \
  $(BUILD_DIR)/pylib-apple/threading.py \
  $(BUILD_DIR)/pylib-apple/timeit.py \
  $(BUILD_DIR)/pylib-apple/token.py \
  $(BUILD_DIR)/pylib-apple/tokenize.py \
  $(BUILD_DIR)/pylib-apple/tomllib/__init__.py \
  $(BUILD_DIR)/pylib-apple/tomllib/_parser.py \
  $(BUILD_DIR)/pylib-apple/tomllib/_re.py \
  $(BUILD_DIR)/pylib-apple/tomllib/_types.py \
  $(BUILD_DIR)/pylib-apple/trace.py \
  $(BUILD_DIR)/pylib-apple/traceback.py \
  $(BUILD_DIR)/pylib-apple/tracemalloc.py \
  $(BUILD_DIR)/pylib-apple/tty.py \
  $(BUILD_DIR)/pylib-apple/types.py \
  $(BUILD_DIR)/pylib-apple/typing.py \
  $(BUILD_DIR)/pylib-apple/urllib/__init__.py \
  $(BUILD_DIR)/pylib-apple/urllib/error.py \
  $(BUILD_DIR)/pylib-apple/urllib/parse.py \
  $(BUILD_DIR)/pylib-apple/urllib/request.py \
  $(BUILD_DIR)/pylib-apple/urllib/response.py \
  $(BUILD_DIR)/pylib-apple/urllib/robotparser.py \
  $(BUILD_DIR)/pylib-apple/uuid.py \
  $(BUILD_DIR)/pylib-apple/warnings.py \
  $(BUILD_DIR)/pylib-apple/wave.py \
  $(BUILD_DIR)/pylib-apple/weakref.py \
  $(BUILD_DIR)/pylib-apple/webbrowser.py \
  $(BUILD_DIR)/pylib-apple/xml/__init__.py \
  $(BUILD_DIR)/pylib-apple/xml/dom/NodeFilter.py \
  $(BUILD_DIR)/pylib-apple/xml/dom/__init__.py \
  $(BUILD_DIR)/pylib-apple/xml/dom/domreg.py \
  $(BUILD_DIR)/pylib-apple/xml/dom/expatbuilder.py \
  $(BUILD_DIR)/pylib-apple/xml/dom/minicompat.py \
  $(BUILD_DIR)/pylib-apple/xml/dom/minidom.py \
  $(BUILD_DIR)/pylib-apple/xml/dom/pulldom.py \
  $(BUILD_DIR)/pylib-apple/xml/dom/xmlbuilder.py \
  $(BUILD_DIR)/pylib-apple/xml/etree/ElementInclude.py \
  $(BUILD_DIR)/pylib-apple/xml/etree/ElementPath.py \
  $(BUILD_DIR)/pylib-apple/xml/etree/ElementTree.py \
  $(BUILD_DIR)/pylib-apple/xml/etree/__init__.py \
  $(BUILD_DIR)/pylib-apple/xml/etree/cElementTree.py \
  $(BUILD_DIR)/pylib-apple/xml/parsers/__init__.py \
  $(BUILD_DIR)/pylib-apple/xml/parsers/expat.py \
  $(BUILD_DIR)/pylib-apple/xml/sax/__init__.py \
  $(BUILD_DIR)/pylib-apple/xml/sax/_exceptions.py \
  $(BUILD_DIR)/pylib-apple/xml/sax/expatreader.py \
  $(BUILD_DIR)/pylib-apple/xml/sax/handler.py \
  $(BUILD_DIR)/pylib-apple/xml/sax/saxutils.py \
  $(BUILD_DIR)/pylib-apple/xml/sax/xmlreader.py \
  $(BUILD_DIR)/pylib-apple/xmlrpc/__init__.py \
  $(BUILD_DIR)/pylib-apple/xmlrpc/client.py \
  $(BUILD_DIR)/pylib-apple/xmlrpc/server.py \
  $(BUILD_DIR)/pylib-apple/zipapp.py \
  $(BUILD_DIR)/pylib-apple/zipfile/__init__.py \
  $(BUILD_DIR)/pylib-apple/zipfile/__main__.py \
  $(BUILD_DIR)/pylib-apple/zipfile/_path/__init__.py \
  $(BUILD_DIR)/pylib-apple/zipfile/_path/glob.py \
  $(BUILD_DIR)/pylib-apple/zipimport.py \
  $(BUILD_DIR)/pylib-apple/zoneinfo/__init__.py \
  $(BUILD_DIR)/pylib-apple/zoneinfo/_common.py \
  $(BUILD_DIR)/pylib-apple/zoneinfo/_tzpath.py \
  $(BUILD_DIR)/pylib-apple/zoneinfo/_zoneinfo.py

SCRIPT_TARGETS_SO_PRIVATE_APPLE_MAC = \
  

SCRIPT_TARGETS_ZSTDDICT_PRIVATE_APPLE_MAC = \
  

# Rule to copy src asset scripts to dst.
# (and make non-writable so I'm less likely to accidentally edit them there)
$(SCRIPT_TARGETS_PY_PRIVATE_APPLE_MAC) : ../../.efrocachemap
	@cd ../.. && $(PCOMMANDBATCHFROMROOT) efrocache_get src/assets/$@


SCRIPT_TARGETS_PY_PRIVATE_ANDROID = \
  $(BUILD_DIR)/pylib-android/__future__.py \
  $(BUILD_DIR)/pylib-android/__hello__.py \
  $(BUILD_DIR)/pylib-android/_aix_support.py \
  $(BUILD_DIR)/pylib-android/_android_support.py \
  $(BUILD_DIR)/pylib-android/_apple_support.py \
  $(BUILD_DIR)/pylib-android/_ast_unparse.py \
  $(BUILD_DIR)/pylib-android/_collections_abc.py \
  $(BUILD_DIR)/pylib-android/_colorize.py \
  $(BUILD_DIR)/pylib-android/_compat_pickle.py \
  $(BUILD_DIR)/pylib-android/_ios_support.py \
  $(BUILD_DIR)/pylib-android/_markupbase.py \
  $(BUILD_DIR)/pylib-android/_opcode_metadata.py \
  $(BUILD_DIR)/pylib-android/_osx_support.py \
  $(BUILD_DIR)/pylib-android/_py_abc.py \
  $(BUILD_DIR)/pylib-android/_py_warnings.py \
  $(BUILD_DIR)/pylib-android/_pydatetime.py \
  $(BUILD_DIR)/pylib-android/_pydecimal.py \
  $(BUILD_DIR)/pylib-android/_pyio.py \
  $(BUILD_DIR)/pylib-android/_pylong.py \
  $(BUILD_DIR)/pylib-android/_pyrepl/__init__.py \
  $(BUILD_DIR)/pylib-android/_pyrepl/__main__.py \
  $(BUILD_DIR)/pylib-android/_pyrepl/_module_completer.py \
  $(BUILD_DIR)/pylib-android/_pyrepl/_threading_handler.py \
  $(BUILD_DIR)/pylib-android/_pyrepl/base_eventqueue.py \
  $(BUILD_DIR)/pylib-android/_pyrepl/commands.py \
  $(BUILD_DIR)/pylib-android/_pyrepl/completing_reader.py \
  $(BUILD_DIR)/pylib-android/_pyrepl/console.py \
  $(BUILD_DIR)/pylib-android/_pyrepl/fancy_termios.py \
  $(BUILD_DIR)/pylib-android/_pyrepl/historical_reader.py \
  $(BUILD_DIR)/pylib-android/_pyrepl/input.py \
  $(BUILD_DIR)/pylib-android/_pyrepl/keymap.py \
  $(BUILD_DIR)/pylib-android/_pyrepl/main.py \
  $(BUILD_DIR)/pylib-android/_pyrepl/pager.py \
  $(BUILD_DIR)/pylib-android/_pyrepl/reader.py \
  $(BUILD_DIR)/pylib-android/_pyrepl/readline.py \
  $(BUILD_DIR)/pylib-android/_pyrepl/simple_interact.py \
  $(BUILD_DIR)/pylib-android/_pyrepl/terminfo.py \
  $(BUILD_DIR)/pylib-android/_pyrepl/trace.py \
  $(BUILD_DIR)/pylib-android/_pyrepl/types.py \
  $(BUILD_DIR)/pylib-android/_pyrepl/unix_console.py \
  $(BUILD_DIR)/pylib-android/_pyrepl/unix_eventqueue.py \
  $(BUILD_DIR)/pylib-android/_pyrepl/utils.py \
  $(BUILD_DIR)/pylib-android/_pyrepl/windows_console.py \
  $(BUILD_DIR)/pylib-android/_pyrepl/windows_eventqueue.py \
  $(BUILD_DIR)/pylib-android/_sitebuiltins.py \
  $(BUILD_DIR)/pylib-android/_strptime.py \
  $(BUILD_DIR)/pylib-android/_sysconfigdata__android_aarch64-linux-android.py \
  $(BUILD_DIR)/pylib-android/_sysconfigdata__android_arm-linux-androideabi.py \
  $(BUILD_DIR)/pylib-android/_sysconfigdata__android_i686-linux-android.py \
  $(BUILD_DIR)/pylib-android/_sysconfigdata__android_x86_64-linux-android.py \
  $(BUILD_DIR)/pylib-android/_sysconfigdata_d_android_aarch64-linux-android.py \
  $(BUILD_DIR)/pylib-android/_sysconfigdata_d_android_arm-linux-androideabi.py \
  $(BUILD_DIR)/pylib-android/_sysconfigdata_d_android_i686-linux-android.py \
  $(BUILD_DIR)/pylib-android/_sysconfigdata_d_android_x86_64-linux-android.py \
  $(BUILD_DIR)/pylib-android/_threading_local.py \
  $(BUILD_DIR)/pylib-android/_weakrefset.py \
  $(BUILD_DIR)/pylib-android/abc.py \
  $(BUILD_DIR)/pylib-android/annotationlib.py \
  $(BUILD_DIR)/pylib-android/antigravity.py \
  $(BUILD_DIR)/pylib-android/argparse.py \
  $(BUILD_DIR)/pylib-android/ast.py \
  $(BUILD_DIR)/pylib-android/asyncio/__init__.py \
  $(BUILD_DIR)/pylib-android/asyncio/__main__.py \
  $(BUILD_DIR)/pylib-android/asyncio/base_events.py \
  $(BUILD_DIR)/pylib-android/asyncio/base_futures.py \
  $(BUILD_DIR)/pylib-android/asyncio/base_subprocess.py \
  $(BUILD_DIR)/pylib-android/asyncio/base_tasks.py \
  $(BUILD_DIR)/pylib-android/asyncio/constants.py \
  $(BUILD_DIR)/pylib-android/asyncio/coroutines.py \
  $(BUILD_DIR)/pylib-android/asyncio/events.py \
  $(BUILD_DIR)/pylib-android/asyncio/exceptions.py \
  $(BUILD_DIR)/pylib-android/asyncio/format_helpers.py \
  $(BUILD_DIR)/pylib-android/asyncio/futures.py \
  $(BUILD_DIR)/pylib-android/asyncio/graph.py \
  $(BUILD_DIR)/pylib-android/asyncio/locks.py \
  $(BUILD_DIR)/pylib-android/asyncio/log.py \
  $(BUILD_DIR)/pylib-android/asyncio/mixins.py \
  $(BUILD_DIR)/pylib-android/asyncio/proactor_events.py \
  $(BUILD_DIR)/pylib-android/asyncio/protocols.py \
  $(BUILD_DIR)/pylib-android/asyncio/queues.py \
  $(BUILD_DIR)/pylib-android/asyncio/runners.py \
  $(BUILD_DIR)/pylib-android/asyncio/selector_events.py \
  $(BUILD_DIR)/pylib-android/asyncio/sslproto.py \
  $(BUILD_DIR)/pylib-android/asyncio/staggered.py \
  $(BUILD_DIR)/pylib-android/asyncio/streams.py \
  $(BUILD_DIR)/pylib-android/asyncio/subprocess.py \
  $(BUILD_DIR)/pylib-android/asyncio/taskgroups.py \
  $(BUILD_DIR)/pylib-android/asyncio/tasks.py \
  $(BUILD_DIR)/pylib-android/asyncio/threads.py \
  $(BUILD_DIR)/pylib-android/asyncio/timeouts.py \
  $(BUILD_DIR)/pylib-android/asyncio/tools.py \
  $(BUILD_DIR)/pylib-android/asyncio/transports.py \
  $(BUILD_DIR)/pylib-android/asyncio/trsock.py \
  $(BUILD_DIR)/pylib-android/asyncio/unix_events.py \
  $(BUILD_DIR)/pylib-android/asyncio/windows_events.py \
  $(BUILD_DIR)/pylib-android/asyncio/windows_utils.py \
  $(BUILD_DIR)/pylib-android/base64.py \
  $(BUILD_DIR)/pylib-android/bdb.py \
  $(BUILD_DIR)/pylib-android/bisect.py \
  $(BUILD_DIR)/pylib-android/bz2.py \
  $(BUILD_DIR)/pylib-android/cProfile.py \
  $(BUILD_DIR)/pylib-android/calendar.py \
  $(BUILD_DIR)/pylib-android/cmd.py \
  $(BUILD_DIR)/pylib-android/code.py \
  $(BUILD_DIR)/pylib-android/codecs.py \
  $(BUILD_DIR)/pylib-android/codeop.py \
  $(BUILD_DIR)/pylib-android/collections/__init__.py \
  $(BUILD_DIR)/pylib-android/colorsys.py \
  $(BUILD_DIR)/pylib-android/compileall.py \
  $(BUILD_DIR)/pylib-android/compression/__init__.py \
  $(BUILD_DIR)/pylib-android/compression/_common/__init__.py \
  $(BUILD_DIR)/pylib-android/compression/_common/_streams.py \
  $(BUILD_DIR)/pylib-android/compression/bz2.py \
  $(BUILD_DIR)/pylib-android/compression/gzip.py \
  $(BUILD_DIR)/pylib-android/compression/lzma.py \
  $(BUILD_DIR)/pylib-android/compression/zlib.py \
  $(BUILD_DIR)/pylib-android/compression/zstd/__init__.py \
  $(BUILD_DIR)/pylib-android/compression/zstd/_zstdfile.py \
  $(BUILD_DIR)/pylib-android/concurrent/__init__.py \
  $(BUILD_DIR)/pylib-android/concurrent/futures/__init__.py \
  $(BUILD_DIR)/pylib-android/concurrent/futures/_base.py \
  $(BUILD_DIR)/pylib-android/concurrent/futures/interpreter.py \
  $(BUILD_DIR)/pylib-android/concurrent/futures/process.py \
  $(BUILD_DIR)/pylib-android/concurrent/futures/thread.py \
  $(BUILD_DIR)/pylib-android/concurrent/interpreters/__init__.py \
  $(BUILD_DIR)/pylib-android/concurrent/interpreters/_crossinterp.py \
  $(BUILD_DIR)/pylib-android/concurrent/interpreters/_queues.py \
  $(BUILD_DIR)/pylib-android/configparser.py \
  $(BUILD_DIR)/pylib-android/contextlib.py \
  $(BUILD_DIR)/pylib-android/contextvars.py \
  $(BUILD_DIR)/pylib-android/copy.py \
  $(BUILD_DIR)/pylib-android/copyreg.py \
  $(BUILD_DIR)/pylib-android/csv.py \
  $(BUILD_DIR)/pylib-android/ctypes/__init__.py \
  $(BUILD_DIR)/pylib-android/ctypes/_aix.py \
  $(BUILD_DIR)/pylib-android/ctypes/_endian.py \
  $(BUILD_DIR)/pylib-android/ctypes/_layout.py \
  $(BUILD_DIR)/pylib-android/ctypes/macholib/__init__.py \
  $(BUILD_DIR)/pylib-android/ctypes/macholib/dyld.py \
  $(BUILD_DIR)/pylib-android/ctypes/macholib/dylib.py \
  $(BUILD_DIR)/pylib-android/ctypes/macholib/framework.py \
  $(BUILD_DIR)/pylib-android/ctypes/util.py \
  $(BUILD_DIR)/pylib-android/ctypes/wintypes.py \
  $(BUILD_DIR)/pylib-android/curses/__init__.py \
  $(BUILD_DIR)/pylib-android/curses/ascii.py \
  $(BUILD_DIR)/pylib-android/curses/has_key.py \
  $(BUILD_DIR)/pylib-android/curses/panel.py \
  $(BUILD_DIR)/pylib-android/curses/textpad.py \
  $(BUILD_DIR)/pylib-android/dataclasses.py \
  $(BUILD_DIR)/pylib-android/datetime.py \
  $(BUILD_DIR)/pylib-android/decimal.py \
  $(BUILD_DIR)/pylib-android/difflib.py \
  $(BUILD_DIR)/pylib-android/dis.py \
  $(BUILD_DIR)/pylib-android/doctest.py \
  $(BUILD_DIR)/pylib-android/email/__init__.py \
  $(BUILD_DIR)/pylib-android/email/_encoded_words.py \
  $(BUILD_DIR)/pylib-android/email/_header_value_parser.py \
  $(BUILD_DIR)/pylib-android/email/_parseaddr.py \
  $(BUILD_DIR)/pylib-android/email/_policybase.py \
  $(BUILD_DIR)/pylib-android/email/base64mime.py \
  $(BUILD_DIR)/pylib-android/email/charset.py \
  $(BUILD_DIR)/pylib-android/email/contentmanager.py \
  $(BUILD_DIR)/pylib-android/email/encoders.py \
  $(BUILD_DIR)/pylib-android/email/errors.py \
  $(BUILD_DIR)/pylib-android/email/feedparser.py \
  $(BUILD_DIR)/pylib-android/email/generator.py \
  $(BUILD_DIR)/pylib-android/email/header.py \
  $(BUILD_DIR)/pylib-android/email/headerregistry.py \
  $(BUILD_DIR)/pylib-android/email/iterators.py \
  $(BUILD_DIR)/pylib-android/email/message.py \
  $(BUILD_DIR)/pylib-android/email/mime/__init__.py \
  $(BUILD_DIR)/pylib-android/email/mime/application.py \
  $(BUILD_DIR)/pylib-android/email/mime/audio.py \
  $(BUILD_DIR)/pylib-android/email/mime/base.py \
  $(BUILD_DIR)/pylib-android/email/mime/image.py \
  $(BUILD_DIR)/pylib-android/email/mime/message.py \
  $(BUILD_DIR)/pylib-android/email/mime/multipart.py \
  $(BUILD_DIR)/pylib-android/email/mime/nonmultipart.py \
  $(BUILD_DIR)/pylib-android/email/mime/text.py \
  $(BUILD_DIR)/pylib-android/email/parser.py \
  $(BUILD_DIR)/pylib-android/email/policy.py \
  $(BUILD_DIR)/pylib-android/email/quoprimime.py \
  $(BUILD_DIR)/pylib-android/email/utils.py \
  $(BUILD_DIR)/pylib-android/encodings/__init__.py \
  $(BUILD_DIR)/pylib-android/encodings/_win_cp_codecs.py \
  $(BUILD_DIR)/pylib-android/encodings/aliases.py \
  $(BUILD_DIR)/pylib-android/encodings/ascii.py \
  $(BUILD_DIR)/pylib-android/encodings/base64_codec.py \
  $(BUILD_DIR)/pylib-android/encodings/big5.py \
  $(BUILD_DIR)/pylib-android/encodings/big5hkscs.py \
  $(BUILD_DIR)/pylib-android/encodings/bz2_codec.py \
  $(BUILD_DIR)/pylib-android/encodings/charmap.py \
  $(BUILD_DIR)/pylib-android/encodings/cp037.py \
  $(BUILD_DIR)/pylib-android/encodings/cp1006.py \
  $(BUILD_DIR)/pylib-android/encodings/cp1026.py \
  $(BUILD_DIR)/pylib-android/encodings/cp1125.py \
  $(BUILD_DIR)/pylib-android/encodings/cp1140.py \
  $(BUILD_DIR)/pylib-android/encodings/cp1250.py \
  $(BUILD_DIR)/pylib-android/encodings/cp1251.py \
  $(BUILD_DIR)/pylib-android/encodings/cp1252.py \
  $(BUILD_DIR)/pylib-android/encodings/cp1253.py \
  $(BUILD_DIR)/pylib-android/encodings/cp1254.py \
  $(BUILD_DIR)/pylib-android/encodings/cp1255.py \
  $(BUILD_DIR)/pylib-android/encodings/cp1256.py \
  $(BUILD_DIR)/pylib-android/encodings/cp1257.py \
  $(BUILD_DIR)/pylib-android/encodings/cp1258.py \
  $(BUILD_DIR)/pylib-android/encodings/cp273.py \
  $(BUILD_DIR)/pylib-android/encodings/cp424.py \
  $(BUILD_DIR)/pylib-android/encodings/cp437.py \
  $(BUILD_DIR)/pylib-android/encodings/cp500.py \
  $(BUILD_DIR)/pylib-android/encodings/cp720.py \
  $(BUILD_DIR)/pylib-android/encodings/cp737.py \
  $(BUILD_DIR)/pylib-android/encodings/cp775.py \
  $(BUILD_DIR)/pylib-android/encodings/cp850.py \
  $(BUILD_DIR)/pylib-android/encodings/cp852.py \
  $(BUILD_DIR)/pylib-android/encodings/cp855.py \
  $(BUILD_DIR)/pylib-android/encodings/cp856.py \
  $(BUILD_DIR)/pylib-android/encodings/cp857.py \
  $(BUILD_DIR)/pylib-android/encodings/cp858.py \
  $(BUILD_DIR)/pylib-android/encodings/cp860.py \
  $(BUILD_DIR)/pylib-android/encodings/cp861.py \
  $(BUILD_DIR)/pylib-android/encodings/cp862.py \
  $(BUILD_DIR)/pylib-android/encodings/cp863.py \
  $(BUILD_DIR)/pylib-android/encodings/cp864.py \
  $(BUILD_DIR)/pylib-android/encodings/cp865.py \
  $(BUILD_DIR)/pylib-android/encodings/cp866.py \
  $(BUILD_DIR)/pylib-android/encodings/cp869.py \
  $(BUILD_DIR)/pylib-android/encodings/cp874.py \
  $(BUILD_DIR)/pylib-android/encodings/cp875.py \
  $(BUILD_DIR)/pylib-android/encodings/cp932.py \
  $(BUILD_DIR)/pylib-android/encodings/cp949.py \
  $(BUILD_DIR)/pylib-android/encodings/cp950.py \
  $(BUILD_DIR)/pylib-android/encodings/euc_jis_2004.py \
  $(BUILD_DIR)/pylib-android/encodings/euc_jisx0213.py \
  $(BUILD_DIR)/pylib-android/encodings/euc_jp.py \
  $(BUILD_DIR)/pylib-android/encodings/euc_kr.py \
  $(BUILD_DIR)/pylib-android/encodings/gb18030.py \
  $(BUILD_DIR)/pylib-android/encodings/gb2312.py \
  $(BUILD_DIR)/pylib-android/encodings/gbk.py \
  $(BUILD_DIR)/pylib-android/encodings/hex_codec.py \
  $(BUILD_DIR)/pylib-android/encodings/hp_roman8.py \
  $(BUILD_DIR)/pylib-android/encodings/hz.py \
  $(BUILD_DIR)/pylib-android/encodings/idna.py \
  $(BUILD_DIR)/pylib-android/encodings/iso2022_jp.py \
  $(BUILD_DIR)/pylib-android/encodings/iso2022_jp_1.py \
  $(BUILD_DIR)/pylib-android/encodings/iso2022_jp_2.py \
  $(BUILD_DIR)/pylib-android/encodings/iso2022_jp_2004.py \
  $(BUILD_DIR)/pylib-android/encodings/iso2022_jp_3.py \
  $(BUILD_DIR)/pylib-android/encodings/iso2022_jp_ext.py \
  $(BUILD_DIR)/pylib-android/encodings/iso2022_kr.py \
  $(BUILD_DIR)/pylib-android/encodings/iso8859_1.py \
  $(BUILD_DIR)/pylib-android/encodings/iso8859_10.py \
  $(BUILD_DIR)/pylib-android/encodings/iso8859_11.py \
  $(BUILD_DIR)/pylib-android/encodings/iso8859_13.py \
  $(BUILD_DIR)/pylib-android/encodings/iso8859_14.py \
  $(BUILD_DIR)/pylib-android/encodings/iso8859_15.py \
  $(BUILD_DIR)/pylib-android/encodings/iso8859_16.py \
  $(BUILD_DIR)/pylib-android/encodings/iso8859_2.py \
  $(BUILD_DIR)/pylib-android/encodings/iso8859_3.py \
  $(BUILD_DIR)/pylib-android/encodings/iso8859_4.py \
  $(BUILD_DIR)/pylib-android/encodings/iso8859_5.py \
  $(BUILD_DIR)/pylib-android/encodings/iso8859_6.py \
  $(BUILD_DIR)/pylib-android/encodings/iso8859_7.py \
  $(BUILD_DIR)/pylib-android/encodings/iso8859_8.py \
  $(BUILD_DIR)/pylib-android/encodings/iso8859_9.py \
  $(BUILD_DIR)/pylib-android/encodings/johab.py \
  $(BUILD_DIR)/pylib-android/encodings/koi8_r.py \
  $(BUILD_DIR)/pylib-android/encodings/koi8_t.py \
  $(BUILD_DIR)/pylib-android/encodings/koi8_u.py \
  $(BUILD_DIR)/pylib-android/encodings/kz1048.py \
  $(BUILD_DIR)/pylib-android/encodings/latin_1.py \
  $(BUILD_DIR)/pylib-android/encodings/mac_arabic.py \
  $(BUILD_DIR)/pylib-android/encodings/mac_croatian.py \
  $(BUILD_DIR)/pylib-android/encodings/mac_cyrillic.py \
  $(BUILD_DIR)/pylib-android/encodings/mac_farsi.py \
  $(BUILD_DIR)/pylib-android/encodings/mac_greek.py \
  $(BUILD_DIR)/pylib-android/encodings/mac_iceland.py \
  $(BUILD_DIR)/pylib-android/encodings/mac_latin2.py \
  $(BUILD_DIR)/pylib-android/encodings/mac_roman.py \
  $(BUILD_DIR)/pylib-android/encodings/mac_romanian.py \
  $(BUILD_DIR)/pylib-android/encodings/mac_turkish.py \
  $(BUILD_DIR)/pylib-android/encodings/mbcs.py \
  $(BUILD_DIR)/pylib-android/encodings/oem.py \
  $(BUILD_DIR)/pylib-android/encodings/palmos.py \
  $(BUILD_DIR)/pylib-android/encodings/ptcp154.py \
  $(BUILD_DIR)/pylib-android/encodings/punycode.py \
  $(BUILD_DIR)/pylib-android/encodings/quopri_codec.py \
  $(BUILD_DIR)/pylib-android/encodings/raw_unicode_escape.py \
  $(BUILD_DIR)/pylib-android/encodings/rot_13.py \
  $(BUILD_DIR)/pylib-android/encodings/shift_jis.py \
  $(BUILD_DIR)/pylib-android/encodings/shift_jis_2004.py \
  $(BUILD_DIR)/pylib-android/encodings/shift_jisx0213.py \
  $(BUILD_DIR)/pylib-android/encodings/tis_620.py \
  $(BUILD_DIR)/pylib-android/encodings/undefined.py \
  $(BUILD_DIR)/pylib-android/encodings/unicode_escape.py \
  $(BUILD_DIR)/pylib-android/encodings/utf_16.py \
  $(BUILD_DIR)/pylib-android/encodings/utf_16_be.py \
  $(BUILD_DIR)/pylib-android/encodings/utf_16_le.py \
  $(BUILD_DIR)/pylib-android/encodings/utf_32.py \
  $(BUILD_DIR)/pylib-android/encodings/utf_32_be.py \
  $(BUILD_DIR)/pylib-android/encodings/utf_32_le.py \
  $(BUILD_DIR)/pylib-android/encodings/utf_7.py \
  $(BUILD_DIR)/pylib-android/encodings/utf_8.py \
  $(BUILD_DIR)/pylib-android/encodings/utf_8_sig.py \
  $(BUILD_DIR)/pylib-android/encodings/uu_codec.py \
  $(BUILD_DIR)/pylib-android/encodings/zlib_codec.py \
  $(BUILD_DIR)/pylib-android/enum.py \
  $(BUILD_DIR)/pylib-android/filecmp.py \
  $(BUILD_DIR)/pylib-android/fileinput.py \
  $(BUILD_DIR)/pylib-android/fnmatch.py \
  $(BUILD_DIR)/pylib-android/fractions.py \
  $(BUILD_DIR)/pylib-android/ftplib.py \
  $(BUILD_DIR)/pylib-android/functools.py \
  $(BUILD_DIR)/pylib-android/genericpath.py \
  $(BUILD_DIR)/pylib-android/getopt.py \
  $(BUILD_DIR)/pylib-android/getpass.py \
  $(BUILD_DIR)/pylib-android/gettext.py \
  $(BUILD_DIR)/pylib-android/glob.py \
  $(BUILD_DIR)/pylib-android/graphlib.py \
  $(BUILD_DIR)/pylib-android/gzip.py \
  $(BUILD_DIR)/pylib-android/hashlib.py \
  $(BUILD_DIR)/pylib-android/heapq.py \
  $(BUILD_DIR)/pylib-android/hmac.py \
  $(BUILD_DIR)/pylib-android/html/__init__.py \
  $(BUILD_DIR)/pylib-android/html/entities.py \
  $(BUILD_DIR)/pylib-android/html/parser.py \
  $(BUILD_DIR)/pylib-android/http/__init__.py \
  $(BUILD_DIR)/pylib-android/http/client.py \
  $(BUILD_DIR)/pylib-android/http/cookiejar.py \
  $(BUILD_DIR)/pylib-android/http/cookies.py \
  $(BUILD_DIR)/pylib-android/http/server.py \
  $(BUILD_DIR)/pylib-android/importlib/__init__.py \
  $(BUILD_DIR)/pylib-android/importlib/_abc.py \
  $(BUILD_DIR)/pylib-android/importlib/_bootstrap.py \
  $(BUILD_DIR)/pylib-android/importlib/_bootstrap_external.py \
  $(BUILD_DIR)/pylib-android/importlib/abc.py \
  $(BUILD_DIR)/pylib-android/importlib/machinery.py \
  $(BUILD_DIR)/pylib-android/importlib/metadata/__init__.py \
  $(BUILD_DIR)/pylib-android/importlib/metadata/_adapters.py \
  $(BUILD_DIR)/pylib-android/importlib/metadata/_collections.py \
  $(BUILD_DIR)/pylib-android/importlib/metadata/_functools.py \
  $(BUILD_DIR)/pylib-android/importlib/metadata/_itertools.py \
  $(BUILD_DIR)/pylib-android/importlib/metadata/_meta.py \
  $(BUILD_DIR)/pylib-android/importlib/metadata/_text.py \
  $(BUILD_DIR)/pylib-android/importlib/metadata/diagnose.py \
  $(BUILD_DIR)/pylib-android/importlib/readers.py \
  $(BUILD_DIR)/pylib-android/importlib/resources/__init__.py \
  $(BUILD_DIR)/pylib-android/importlib/resources/_adapters.py \
  $(BUILD_DIR)/pylib-android/importlib/resources/_common.py \
  $(BUILD_DIR)/pylib-android/importlib/resources/_functional.py \
  $(BUILD_DIR)/pylib-android/importlib/resources/_itertools.py \
  $(BUILD_DIR)/pylib-android/importlib/resources/abc.py \
  $(BUILD_DIR)/pylib-android/importlib/resources/readers.py \
  $(BUILD_DIR)/pylib-android/importlib/resources/simple.py \
  $(BUILD_DIR)/pylib-android/importlib/simple.py \
  $(BUILD_DIR)/pylib-android/importlib/util.py \
  $(BUILD_DIR)/pylib-android/inspect.py \
  $(BUILD_DIR)/pylib-android/io.py \
  $(BUILD_DIR)/pylib-android/ipaddress.py \
  $(BUILD_DIR)/pylib-android/json/__init__.py \
  $(BUILD_DIR)/pylib-android/json/__main__.py \
  $(BUILD_DIR)/pylib-android/json/decoder.py \
  $(BUILD_DIR)/pylib-android/json/encoder.py \
  $(BUILD_DIR)/pylib-android/json/scanner.py \
  $(BUILD_DIR)/pylib-android/json/tool.py \
  $(BUILD_DIR)/pylib-android/keyword.py \
  $(BUILD_DIR)/pylib-android/linecache.py \
  $(BUILD_DIR)/pylib-android/locale.py \
  $(BUILD_DIR)/pylib-android/logging/__init__.py \
  $(BUILD_DIR)/pylib-android/logging/config.py \
  $(BUILD_DIR)/pylib-android/logging/handlers.py \
  $(BUILD_DIR)/pylib-android/lzma.py \
  $(BUILD_DIR)/pylib-android/mailbox.py \
  $(BUILD_DIR)/pylib-android/mimetypes.py \
  $(BUILD_DIR)/pylib-android/modulefinder.py \
  $(BUILD_DIR)/pylib-android/netrc.py \
  $(BUILD_DIR)/pylib-android/ntpath.py \
  $(BUILD_DIR)/pylib-android/nturl2path.py \
  $(BUILD_DIR)/pylib-android/numbers.py \
  $(BUILD_DIR)/pylib-android/opcode.py \
  $(BUILD_DIR)/pylib-android/operator.py \
  $(BUILD_DIR)/pylib-android/optparse.py \
  $(BUILD_DIR)/pylib-android/os.py \
  $(BUILD_DIR)/pylib-android/pathlib/__init__.py \
  $(BUILD_DIR)/pylib-android/pathlib/_local.py \
  $(BUILD_DIR)/pylib-android/pathlib/_os.py \
  $(BUILD_DIR)/pylib-android/pathlib/types.py \
  $(BUILD_DIR)/pylib-android/pdb.py \
  $(BUILD_DIR)/pylib-android/pickle.py \
  $(BUILD_DIR)/pylib-android/pickletools.py \
  $(BUILD_DIR)/pylib-android/pkgutil.py \
  $(BUILD_DIR)/pylib-android/platform.py \
  $(BUILD_DIR)/pylib-android/plistlib.py \
  $(BUILD_DIR)/pylib-android/poplib.py \
  $(BUILD_DIR)/pylib-android/posixpath.py \
  $(BUILD_DIR)/pylib-android/pprint.py \
  $(BUILD_DIR)/pylib-android/profile.py \
  $(BUILD_DIR)/pylib-android/pstats.py \
  $(BUILD_DIR)/pylib-android/pty.py \
  $(BUILD_DIR)/pylib-android/py_compile.py \
  $(BUILD_DIR)/pylib-android/pyclbr.py \
  $(BUILD_DIR)/pylib-android/pydoc.py \
  $(BUILD_DIR)/pylib-android/queue.py \
  $(BUILD_DIR)/pylib-android/quopri.py \
  $(BUILD_DIR)/pylib-android/random.py \
  $(BUILD_DIR)/pylib-android/re/__init__.py \
  $(BUILD_DIR)/pylib-android/re/_casefix.py \
  $(BUILD_DIR)/pylib-android/re/_compiler.py \
  $(BUILD_DIR)/pylib-android/re/_constants.py \
  $(BUILD_DIR)/pylib-android/re/_parser.py \
  $(BUILD_DIR)/pylib-android/reprlib.py \
  $(BUILD_DIR)/pylib-android/rlcompleter.py \
  $(BUILD_DIR)/pylib-android/runpy.py \
  $(BUILD_DIR)/pylib-android/sched.py \
  $(BUILD_DIR)/pylib-android/secrets.py \
  $(BUILD_DIR)/pylib-android/selectors.py \
  $(BUILD_DIR)/pylib-android/shelve.py \
  $(BUILD_DIR)/pylib-android/shlex.py \
  $(BUILD_DIR)/pylib-android/shutil.py \
  $(BUILD_DIR)/pylib-android/signal.py \
  $(BUILD_DIR)/pylib-android/site.py \
  $(BUILD_DIR)/pylib-android/smtplib.py \
  $(BUILD_DIR)/pylib-android/socket.py \
  $(BUILD_DIR)/pylib-android/socketserver.py \
  $(BUILD_DIR)/pylib-android/sqlite3/__init__.py \
  $(BUILD_DIR)/pylib-android/sqlite3/__main__.py \
  $(BUILD_DIR)/pylib-android/sqlite3/dbapi2.py \
  $(BUILD_DIR)/pylib-android/sqlite3/dump.py \
  $(BUILD_DIR)/pylib-android/sre_compile.py \
  $(BUILD_DIR)/pylib-android/sre_constants.py \
  $(BUILD_DIR)/pylib-android/sre_parse.py \
  $(BUILD_DIR)/pylib-android/ssl.py \
  $(BUILD_DIR)/pylib-android/stat.py \
  $(BUILD_DIR)/pylib-android/statistics.py \
  $(BUILD_DIR)/pylib-android/string/__init__.py \
  $(BUILD_DIR)/pylib-android/string/templatelib.py \
  $(BUILD_DIR)/pylib-android/stringprep.py \
  $(BUILD_DIR)/pylib-android/struct.py \
  $(BUILD_DIR)/pylib-android/subprocess.py \
  $(BUILD_DIR)/pylib-android/symtable.py \
  $(BUILD_DIR)/pylib-android/sysconfig/__init__.py \
  $(BUILD_DIR)/pylib-android/sysconfig/__main__.py \
  $(BUILD_DIR)/pylib-android/tabnanny.py \
  $(BUILD_DIR)/pylib-android/tarfile.py \
  $(BUILD_DIR)/pylib-android/tempfile.py \
  $(BUILD_DIR)/pylib-android/textwrap.py \
  $(BUILD_DIR)/pylib-android/this.py \
  $(BUILD_DIR)/pylib-android/threading.py \
  $(BUILD_DIR)/pylib-android/timeit.py \
  $(BUILD_DIR)/pylib-android/token.py \
  $(BUILD_DIR)/pylib-android/tokenize.py \
  $(BUILD_DIR)/pylib-android/tomllib/__init__.py \
  $(BUILD_DIR)/pylib-android/tomllib/_parser.py \
  $(BUILD_DIR)/pylib-android/tomllib/_re.py \
  $(BUILD_DIR)/pylib-android/tomllib/_types.py \
  $(BUILD_DIR)/pylib-android/trace.py \
  $(BUILD_DIR)/pylib-android/traceback.py \
  $(BUILD_DIR)/pylib-android/tracemalloc.py \
  $(BUILD_DIR)/pylib-android/tty.py \
  $(BUILD_DIR)/pylib-android/types.py \
  $(BUILD_DIR)/pylib-android/typing.py \
  $(BUILD_DIR)/pylib-android/urllib/__init__.py \
  $(BUILD_DIR)/pylib-android/urllib/error.py \
  $(BUILD_DIR)/pylib-android/urllib/parse.py \
  $(BUILD_DIR)/pylib-android/urllib/request.py \
  $(BUILD_DIR)/pylib-android/urllib/response.py \
  $(BUILD_DIR)/pylib-android/urllib/robotparser.py \
  $(BUILD_DIR)/pylib-android/uuid.py \
  $(BUILD_DIR)/pylib-android/warnings.py \
  $(BUILD_DIR)/pylib-android/wave.py \
  $(BUILD_DIR)/pylib-android/weakref.py \
  $(BUILD_DIR)/pylib-android/webbrowser.py \
  $(BUILD_DIR)/pylib-android/xml/__init__.py \
  $(BUILD_DIR)/pylib-android/xml/dom/NodeFilter.py \
  $(BUILD_DIR)/pylib-android/xml/dom/__init__.py \
  $(BUILD_DIR)/pylib-android/xml/dom/domreg.py \
  $(BUILD_DIR)/pylib-android/xml/dom/expatbuilder.py \
  $(BUILD_DIR)/pylib-android/xml/dom/minicompat.py \
  $(BUILD_DIR)/pylib-android/xml/dom/minidom.py \
  $(BUILD_DIR)/pylib-android/xml/dom/pulldom.py \
  $(BUILD_DIR)/pylib-android/xml/dom/xmlbuilder.py \
  $(BUILD_DIR)/pylib-android/xml/etree/ElementInclude.py \
  $(BUILD_DIR)/pylib-android/xml/etree/ElementPath.py \
  $(BUILD_DIR)/pylib-android/xml/etree/ElementTree.py \
  $(BUILD_DIR)/pylib-android/xml/etree/__init__.py \
  $(BUILD_DIR)/pylib-android/xml/etree/cElementTree.py \
  $(BUILD_DIR)/pylib-android/xml/parsers/__init__.py \
  $(BUILD_DIR)/pylib-android/xml/parsers/expat.py \
  $(BUILD_DIR)/pylib-android/xml/sax/__init__.py \
  $(BUILD_DIR)/pylib-android/xml/sax/_exceptions.py \
  $(BUILD_DIR)/pylib-android/xml/sax/expatreader.py \
  $(BUILD_DIR)/pylib-android/xml/sax/handler.py \
  $(BUILD_DIR)/pylib-android/xml/sax/saxutils.py \
  $(BUILD_DIR)/pylib-android/xml/sax/xmlreader.py \
  $(BUILD_DIR)/pylib-android/xmlrpc/__init__.py \
  $(BUILD_DIR)/pylib-android/xmlrpc/client.py \
  $(BUILD_DIR)/pylib-android/xmlrpc/server.py \
  $(BUILD_DIR)/pylib-android/zipapp.py \
  $(BUILD_DIR)/pylib-android/zipfile/__init__.py \
  $(BUILD_DIR)/pylib-android/zipfile/__main__.py \
  $(BUILD_DIR)/pylib-android/zipfile/_path/__init__.py \
  $(BUILD_DIR)/pylib-android/zipfile/_path/glob.py \
  $(BUILD_DIR)/pylib-android/zipimport.py \
  $(BUILD_DIR)/pylib-android/zoneinfo/__init__.py \
  $(BUILD_DIR)/pylib-android/zoneinfo/_common.py \
  $(BUILD_DIR)/pylib-android/zoneinfo/_tzpath.py \
  $(BUILD_DIR)/pylib-android/zoneinfo/_zoneinfo.py

SCRIPT_TARGETS_SO_PRIVATE_ANDROID = \
  

SCRIPT_TARGETS_ZSTDDICT_PRIVATE_ANDROID = \
  

# Rule to copy src asset scripts to dst.
# (and make non-writable so I'm less likely to accidentally edit them there)
$(SCRIPT_TARGETS_PY_PRIVATE_ANDROID) : ../../.efrocachemap
	@cd ../.. && $(PCOMMANDBATCHFROMROOT) efrocache_get src/assets/$@


SCRIPT_TARGETS_PY_PRIVATE_COMMON = \
  $(BUILD_DIR)/ba_data/python-site-packages/certifi/__init__.py \
  $(BUILD_DIR)/ba_data/python-site-packages/certifi/__main__.py \
  $(BUILD_DIR)/ba_data/python-site-packages/certifi/core.py \
  $(BUILD_DIR)/ba_data/python-site-packages/typing_extensions.py \
  $(BUILD_DIR)/ba_data/python-site-packages/urllib3/__init__.py \
  $(BUILD_DIR)/ba_data/python-site-packages/urllib3/_base_connection.py \
  $(BUILD_DIR)/ba_data/python-site-packages/urllib3/_collections.py \
  $(BUILD_DIR)/ba_data/python-site-packages/urllib3/_request_methods.py \
  $(BUILD_DIR)/ba_data/python-site-packages/urllib3/_version.py \
  $(BUILD_DIR)/ba_data/python-site-packages/urllib3/connection.py \
  $(BUILD_DIR)/ba_data/python-site-packages/urllib3/connectionpool.py \
  $(BUILD_DIR)/ba_data/python-site-packages/urllib3/contrib/__init__.py \
  $(BUILD_DIR)/ba_data/python-site-packages/urllib3/contrib/emscripten/__init__.py \
  $(BUILD_DIR)/ba_data/python-site-packages/urllib3/contrib/emscripten/connection.py \
  $(BUILD_DIR)/ba_data/python-site-packages/urllib3/contrib/emscripten/fetch.py \
  $(BUILD_DIR)/ba_data/python-site-packages/urllib3/contrib/emscripten/request.py \
  $(BUILD_DIR)/ba_data/python-site-packages/urllib3/contrib/emscripten/response.py \
  $(BUILD_DIR)/ba_data/python-site-packages/urllib3/contrib/pyopenssl.py \
  $(BUILD_DIR)/ba_data/python-site-packages/urllib3/contrib/socks.py \
  $(BUILD_DIR)/ba_data/python-site-packages/urllib3/exceptions.py \
  $(BUILD_DIR)/ba_data/python-site-packages/urllib3/fields.py \
  $(BUILD_DIR)/ba_data/python-site-packages/urllib3/filepost.py \
  $(BUILD_DIR)/ba_data/python-site-packages/urllib3/http2/__init__.py \
  $(BUILD_DIR)/ba_data/python-site-packages/urllib3/http2/connection.py \
  $(BUILD_DIR)/ba_data/python-site-packages/urllib3/http2/probe.py \
  $(BUILD_DIR)/ba_data/python-site-packages/urllib3/poolmanager.py \
  $(BUILD_DIR)/ba_data/python-site-packages/urllib3/response.py \
  $(BUILD_DIR)/ba_data/python-site-packages/urllib3/util/__init__.py \
  $(BUILD_DIR)/ba_data/python-site-packages/urllib3/util/connection.py \
  $(BUILD_DIR)/ba_data/python-site-packages/urllib3/util/proxy.py \
  $(BUILD_DIR)/ba_data/python-site-packages/urllib3/util/request.py \
  $(BUILD_DIR)/ba_data/python-site-packages/urllib3/util/response.py \
  $(BUILD_DIR)/ba_data/python-site-packages/urllib3/util/retry.py \
  $(BUILD_DIR)/ba_data/python-site-packages/urllib3/util/ssl_.py \
  $(BUILD_DIR)/ba_data/python-site-packages/urllib3/util/ssl_match_hostname.py \
  $(BUILD_DIR)/ba_data/python-site-packages/urllib3/util/ssltransport.py \
  $(BUILD_DIR)/ba_data/python-site-packages/urllib3/util/timeout.py \
  $(BUILD_DIR)/ba_data/python-site-packages/urllib3/util/url.py \
  $(BUILD_DIR)/ba_data/python-site-packages/urllib3/util/util.py \
  $(BUILD_DIR)/ba_data/python-site-packages/urllib3/util/wait.py \
  $(BUILD_DIR)/ba_data/python-site-packages/websockets/__init__.py \
  $(BUILD_DIR)/ba_data/python-site-packages/websockets/__main__.py \
  $(BUILD_DIR)/ba_data/python-site-packages/websockets/asyncio/__init__.py \
  $(BUILD_DIR)/ba_data/python-site-packages/websockets/asyncio/async_timeout.py \
  $(BUILD_DIR)/ba_data/python-site-packages/websockets/asyncio/client.py \
  $(BUILD_DIR)/ba_data/python-site-packages/websockets/asyncio/compatibility.py \
  $(BUILD_DIR)/ba_data/python-site-packages/websockets/asyncio/connection.py \
  $(BUILD_DIR)/ba_data/python-site-packages/websockets/asyncio/messages.py \
  $(BUILD_DIR)/ba_data/python-site-packages/websockets/asyncio/router.py \
  $(BUILD_DIR)/ba_data/python-site-packages/websockets/asyncio/server.py \
  $(BUILD_DIR)/ba_data/python-site-packages/websockets/auth.py \
  $(BUILD_DIR)/ba_data/python-site-packages/websockets/cli.py \
  $(BUILD_DIR)/ba_data/python-site-packages/websockets/client.py \
  $(BUILD_DIR)/ba_data/python-site-packages/websockets/connection.py \
  $(BUILD_DIR)/ba_data/python-site-packages/websockets/datastructures.py \
  $(BUILD_DIR)/ba_data/python-site-packages/websockets/exceptions.py \
  $(BUILD_DIR)/ba_data/python-site-packages/websockets/extensions/__init__.py \
  $(BUILD_DIR)/ba_data/python-site-packages/websockets/extensions/base.py \
  $(BUILD_DIR)/ba_data/python-site-packages/websockets/extensions/permessage_deflate.py \
  $(BUILD_DIR)/ba_data/python-site-packages/websockets/frames.py \
  $(BUILD_DIR)/ba_data/python-site-packages/websockets/headers.py \
  $(BUILD_DIR)/ba_data/python-site-packages/websockets/http.py \
  $(BUILD_DIR)/ba_data/python-site-packages/websockets/http11.py \
  $(BUILD_DIR)/ba_data/python-site-packages/websockets/imports.py \
  $(BUILD_DIR)/ba_data/python-site-packages/websockets/legacy/__init__.py \
  $(BUILD_DIR)/ba_data/python-site-packages/websockets/legacy/auth.py \
  $(BUILD_DIR)/ba_data/python-site-packages/websockets/legacy/client.py \
  $(BUILD_DIR)/ba_data/python-site-packages/websockets/legacy/exceptions.py \
  $(BUILD_DIR)/ba_data/python-site-packages/websockets/legacy/framing.py \
  $(BUILD_DIR)/ba_data/python-site-packages/websockets/legacy/handshake.py \
  $(BUILD_DIR)/ba_data/python-site-packages/websockets/legacy/http.py \
  $(BUILD_DIR)/ba_data/python-site-packages/websockets/legacy/protocol.py \
  $(BUILD_DIR)/ba_data/python-site-packages/websockets/legacy/server.py \
  $(BUILD_DIR)/ba_data/python-site-packages/websockets/protocol.py \
  $(BUILD_DIR)/ba_data/python-site-packages/websockets/proxy.py \
  $(BUILD_DIR)/ba_data/python-site-packages/websockets/server.py \
  $(BUILD_DIR)/ba_data/python-site-packages/websockets/streams.py \
  $(BUILD_DIR)/ba_data/python-site-packages/websockets/sync/__init__.py \
  $(BUILD_DIR)/ba_data/python-site-packages/websockets/sync/client.py \
  $(BUILD_DIR)/ba_data/python-site-packages/websockets/sync/connection.py \
  $(BUILD_DIR)/ba_data/python-site-packages/websockets/sync/messages.py \
  $(BUILD_DIR)/ba_data/python-site-packages/websockets/sync/router.py \
  $(BUILD_DIR)/ba_data/python-site-packages/websockets/sync/server.py \
  $(BUILD_DIR)/ba_data/python-site-packages/websockets/sync/utils.py \
  $(BUILD_DIR)/ba_data/python-site-packages/websockets/typing.py \
  $(BUILD_DIR)/ba_data/python-site-packages/websockets/uri.py \
  $(BUILD_DIR)/ba_data/python-site-packages/websockets/utils.py \
  $(BUILD_DIR)/ba_data/python-site-packages/websockets/version.py \
  $(BUILD_DIR)/sphinx/static/conf.py

SCRIPT_TARGETS_SO_PRIVATE_COMMON = \
  

SCRIPT_TARGETS_ZSTDDICT_PRIVATE_COMMON = \
  

# Rule to copy src asset scripts to dst.
# (and make non-writable so I'm less likely to accidentally edit them there)
$(SCRIPT_TARGETS_PY_PRIVATE_COMMON) : ../../.efrocachemap
	@cd ../.. && $(PCOMMANDBATCHFROMROOT) efrocache_get src/assets/$@


SCRIPT_TARGETS_PY_PRIVATE_WIN_WIN32 = \
  $(BUILD_DIR)/windows/Win32/Lib/__future__.py \
  $(BUILD_DIR)/windows/Win32/Lib/__hello__.py \
  $(BUILD_DIR)/windows/Win32/Lib/_aix_support.py \
  $(BUILD_DIR)/windows/Win32/Lib/_android_support.py \
  $(BUILD_DIR)/windows/Win32/Lib/_apple_support.py \
  $(BUILD_DIR)/windows/Win32/Lib/_ast_unparse.py \
  $(BUILD_DIR)/windows/Win32/Lib/_collections_abc.py \
  $(BUILD_DIR)/windows/Win32/Lib/_colorize.py \
  $(BUILD_DIR)/windows/Win32/Lib/_compat_pickle.py \
  $(BUILD_DIR)/windows/Win32/Lib/_ios_support.py \
  $(BUILD_DIR)/windows/Win32/Lib/_markupbase.py \
  $(BUILD_DIR)/windows/Win32/Lib/_opcode_metadata.py \
  $(BUILD_DIR)/windows/Win32/Lib/_osx_support.py \
  $(BUILD_DIR)/windows/Win32/Lib/_py_abc.py \
  $(BUILD_DIR)/windows/Win32/Lib/_py_warnings.py \
  $(BUILD_DIR)/windows/Win32/Lib/_pydatetime.py \
  $(BUILD_DIR)/windows/Win32/Lib/_pydecimal.py \
  $(BUILD_DIR)/windows/Win32/Lib/_pyio.py \
  $(BUILD_DIR)/windows/Win32/Lib/_pylong.py \
  $(BUILD_DIR)/windows/Win32/Lib/_pyrepl/__init__.py \
  $(BUILD_DIR)/windows/Win32/Lib/_pyrepl/__main__.py \
  $(BUILD_DIR)/windows/Win32/Lib/_pyrepl/_module_completer.py \
  $(BUILD_DIR)/windows/Win32/Lib/_pyrepl/_threading_handler.py \
  $(BUILD_DIR)/windows/Win32/Lib/_pyrepl/base_eventqueue.py \
  $(BUILD_DIR)/windows/Win32/Lib/_pyrepl/commands.py \
  $(BUILD_DIR)/windows/Win32/Lib/_pyrepl/completing_reader.py \
  $(BUILD_DIR)/windows/Win32/Lib/_pyrepl/console.py \
  $(BUILD_DIR)/windows/Win32/Lib/_pyrepl/fancy_termios.py \
  $(BUILD_DIR)/windows/Win32/Lib/_pyrepl/historical_reader.py \
  $(BUILD_DIR)/windows/Win32/Lib/_pyrepl/input.py \
  $(BUILD_DIR)/windows/Win32/Lib/_pyrepl/keymap.py \
  $(BUILD_DIR)/windows/Win32/Lib/_pyrepl/main.py \
  $(BUILD_DIR)/windows/Win32/Lib/_pyrepl/pager.py \
  $(BUILD_DIR)/windows/Win32/Lib/_pyrepl/reader.py \
  $(BUILD_DIR)/windows/Win32/Lib/_pyrepl/readline.py \
  $(BUILD_DIR)/windows/Win32/Lib/_pyrepl/simple_interact.py \
  $(BUILD_DIR)/windows/Win32/Lib/_pyrepl/terminfo.py \
  $(BUILD_DIR)/windows/Win32/Lib/_pyrepl/trace.py \
  $(BUILD_DIR)/windows/Win32/Lib/_pyrepl/types.py \
  $(BUILD_DIR)/windows/Win32/Lib/_pyrepl/unix_console.py \
  $(BUILD_DIR)/windows/Win32/Lib/_pyrepl/unix_eventqueue.py \
  $(BUILD_DIR)/windows/Win32/Lib/_pyrepl/utils.py \
  $(BUILD_DIR)/windows/Win32/Lib/_pyrepl/windows_console.py \
  $(BUILD_DIR)/windows/Win32/Lib/_pyrepl/windows_eventqueue.py \
  $(BUILD_DIR)/windows/Win32/Lib/_sitebuiltins.py \
  $(BUILD_DIR)/windows/Win32/Lib/_strptime.py \
  $(BUILD_DIR)/windows/Win32/Lib/_threading_local.py \
  $(BUILD_DIR)/windows/Win32/Lib/_weakrefset.py \
  $(BUILD_DIR)/windows/Win32/Lib/abc.py \
  $(BUILD_DIR)/windows/Win32/Lib/annotationlib.py \
  $(BUILD_DIR)/windows/Win32/Lib/antigravity.py \
  $(BUILD_DIR)/windows/Win32/Lib/argparse.py \
  $(BUILD_DIR)/windows/Win32/Lib/ast.py \
  $(BUILD_DIR)/windows/Win32/Lib/asyncio/__init__.py \
  $(BUILD_DIR)/windows/Win32/Lib/asyncio/__main__.py \
  $(BUILD_DIR)/windows/Win32/Lib/asyncio/base_events.py \
  $(BUILD_DIR)/windows/Win32/Lib/asyncio/base_futures.py \
  $(BUILD_DIR)/windows/Win32/Lib/asyncio/base_subprocess.py \
  $(BUILD_DIR)/windows/Win32/Lib/asyncio/base_tasks.py \
  $(BUILD_DIR)/windows/Win32/Lib/asyncio/constants.py \
  $(BUILD_DIR)/windows/Win32/Lib/asyncio/coroutines.py \
  $(BUILD_DIR)/windows/Win32/Lib/asyncio/events.py \
  $(BUILD_DIR)/windows/Win32/Lib/asyncio/exceptions.py \
  $(BUILD_DIR)/windows/Win32/Lib/asyncio/format_helpers.py \
  $(BUILD_DIR)/windows/Win32/Lib/asyncio/futures.py \
  $(BUILD_DIR)/windows/Win32/Lib/asyncio/graph.py \
  $(BUILD_DIR)/windows/Win32/Lib/asyncio/locks.py \
  $(BUILD_DIR)/windows/Win32/Lib/asyncio/log.py \
  $(BUILD_DIR)/windows/Win32/Lib/asyncio/mixins.py \
  $(BUILD_DIR)/windows/Win32/Lib/asyncio/proactor_events.py \
  $(BUILD_DIR)/windows/Win32/Lib/asyncio/protocols.py \
  $(BUILD_DIR)/windows/Win32/Lib/asyncio/queues.py \
  $(BUILD_DIR)/windows/Win32/Lib/asyncio/runners.py \
  $(BUILD_DIR)/windows/Win32/Lib/asyncio/selector_events.py \
  $(BUILD_DIR)/windows/Win32/Lib/asyncio/sslproto.py \
  $(BUILD_DIR)/windows/Win32/Lib/asyncio/staggered.py \
  $(BUILD_DIR)/windows/Win32/Lib/asyncio/streams.py \
  $(BUILD_DIR)/windows/Win32/Lib/asyncio/subprocess.py \
  $(BUILD_DIR)/windows/Win32/Lib/asyncio/taskgroups.py \
  $(BUILD_DIR)/windows/Win32/Lib/asyncio/tasks.py \
  $(BUILD_DIR)/windows/Win32/Lib/asyncio/threads.py \
  $(BUILD_DIR)/windows/Win32/Lib/asyncio/timeouts.py \
  $(BUILD_DIR)/windows/Win32/Lib/asyncio/tools.py \
  $(BUILD_DIR)/windows/Win32/Lib/asyncio/transports.py \
  $(BUILD_DIR)/windows/Win32/Lib/asyncio/trsock.py \
  $(BUILD_DIR)/windows/Win32/Lib/asyncio/unix_events.py \
  $(BUILD_DIR)/windows/Win32/Lib/asyncio/windows_events.py \
  $(BUILD_DIR)/windows/Win32/Lib/asyncio/windows_utils.py \
  $(BUILD_DIR)/windows/Win32/Lib/base64.py \
  $(BUILD_DIR)/windows/Win32/Lib/bdb.py \
  $(BUILD_DIR)/windows/Win32/Lib/bisect.py \
  $(BUILD_DIR)/windows/Win32/Lib/bz2.py \
  $(BUILD_DIR)/windows/Win32/Lib/cProfile.py \
  $(BUILD_DIR)/windows/Win32/Lib/calendar.py \
  $(BUILD_DIR)/windows/Win32/Lib/cmd.py \
  $(BUILD_DIR)/windows/Win32/Lib/code.py \
  $(BUILD_DIR)/windows/Win32/Lib/codecs.py \
  $(BUILD_DIR)/windows/Win32/Lib/codeop.py \
  $(BUILD_DIR)/windows/Win32/Lib/collections/__init__.py \
  $(BUILD_DIR)/windows/Win32/Lib/colorsys.py \
  $(BUILD_DIR)/windows/Win32/Lib/compileall.py \
  $(BUILD_DIR)/windows/Win32/Lib/compression/__init__.py \
  $(BUILD_DIR)/windows/Win32/Lib/compression/_common/__init__.py \
  $(BUILD_DIR)/windows/Win32/Lib/compression/_common/_streams.py \
  $(BUILD_DIR)/windows/Win32/Lib/compression/bz2.py \
  $(BUILD_DIR)/windows/Win32/Lib/compression/gzip.py \
  $(BUILD_DIR)/windows/Win32/Lib/compression/lzma.py \
  $(BUILD_DIR)/windows/Win32/Lib/compression/zlib.py \
  $(BUILD_DIR)/windows/Win32/Lib/compression/zstd/__init__.py \
  $(BUILD_DIR)/windows/Win32/Lib/compression/zstd/_zstdfile.py \
  $(BUILD_DIR)/windows/Win32/Lib/concurrent/__init__.py \
  $(BUILD_DIR)/windows/Win32/Lib/concurrent/futures/__init__.py \
  $(BUILD_DIR)/windows/Win32/Lib/concurrent/futures/_base.py \
  $(BUILD_DIR)/windows/Win32/Lib/concurrent/futures/interpreter.py \
  $(BUILD_DIR)/windows/Win32/Lib/concurrent/futures/process.py \
  $(BUILD_DIR)/windows/Win32/Lib/concurrent/futures/thread.py \
  $(BUILD_DIR)/windows/Win32/Lib/concurrent/interpreters/__init__.py \
  $(BUILD_DIR)/windows/Win32/Lib/concurrent/interpreters/_crossinterp.py \
  $(BUILD_DIR)/windows/Win32/Lib/concurrent/interpreters/_queues.py \
  $(BUILD_DIR)/windows/Win32/Lib/configparser.py \
  $(BUILD_DIR)/windows/Win32/Lib/contextlib.py \
  $(BUILD_DIR)/windows/Win32/Lib/contextvars.py \
  $(BUILD_DIR)/windows/Win32/Lib/copy.py \
  $(BUILD_DIR)/windows/Win32/Lib/copyreg.py \
  $(BUILD_DIR)/windows/Win32/Lib/csv.py \
  $(BUILD_DIR)/windows/Win32/Lib/ctypes/__init__.py \
  $(BUILD_DIR)/windows/Win32/Lib/ctypes/_aix.py \
  $(BUILD_DIR)/windows/Win32/Lib/ctypes/_endian.py \
  $(BUILD_DIR)/windows/Win32/Lib/ctypes/_layout.py \
  $(BUILD_DIR)/windows/Win32/Lib/ctypes/macholib/__init__.py \
  $(BUILD_DIR)/windows/Win32/Lib/ctypes/macholib/dyld.py \
  $(BUILD_DIR)/windows/Win32/Lib/ctypes/macholib/dylib.py \
  $(BUILD_DIR)/windows/Win32/Lib/ctypes/macholib/framework.py \
  $(BUILD_DIR)/windows/Win32/Lib/ctypes/util.py \
  $(BUILD_DIR)/windows/Win32/Lib/ctypes/wintypes.py \
  $(BUILD_DIR)/windows/Win32/Lib/curses/__init__.py \
  $(BUILD_DIR)/windows/Win32/Lib/curses/ascii.py \
  $(BUILD_DIR)/windows/Win32/Lib/curses/has_key.py \
  $(BUILD_DIR)/windows/Win32/Lib/curses/panel.py \
  $(BUILD_DIR)/windows/Win32/Lib/curses/textpad.py \
  $(BUILD_DIR)/windows/Win32/Lib/dataclasses.py \
  $(BUILD_DIR)/windows/Win32/Lib/datetime.py \
  $(BUILD_DIR)/windows/Win32/Lib/decimal.py \
  $(BUILD_DIR)/windows/Win32/Lib/difflib.py \
  $(BUILD_DIR)/windows/Win32/Lib/dis.py \
  $(BUILD_DIR)/windows/Win32/Lib/doctest.py \
  $(BUILD_DIR)/windows/Win32/Lib/email/__init__.py \
  $(BUILD_DIR)/windows/Win32/Lib/email/_encoded_words.py \
  $(BUILD_DIR)/windows/Win32/Lib/email/_header_value_parser.py \
  $(BUILD_DIR)/windows/Win32/Lib/email/_parseaddr.py \
  $(BUILD_DIR)/windows/Win32/Lib/email/_policybase.py \
  $(BUILD_DIR)/windows/Win32/Lib/email/base64mime.py \
  $(BUILD_DIR)/windows/Win32/Lib/email/charset.py \
  $(BUILD_DIR)/windows/Win32/Lib/email/contentmanager.py \
  $(BUILD_DIR)/windows/Win32/Lib/email/encoders.py \
  $(BUILD_DIR)/windows/Win32/Lib/email/errors.py \
  $(BUILD_DIR)/windows/Win32/Lib/email/feedparser.py \
  $(BUILD_DIR)/windows/Win32/Lib/email/generator.py \
  $(BUILD_DIR)/windows/Win32/Lib/email/header.py \
  $(BUILD_DIR)/windows/Win32/Lib/email/headerregistry.py \
  $(BUILD_DIR)/windows/Win32/Lib/email/iterators.py \
  $(BUILD_DIR)/windows/Win32/Lib/email/message.py \
  $(BUILD_DIR)/windows/Win32/Lib/email/mime/__init__.py \
  $(BUILD_DIR)/windows/Win32/Lib/email/mime/application.py \
  $(BUILD_DIR)/windows/Win32/Lib/email/mime/audio.py \
  $(BUILD_DIR)/windows/Win32/Lib/email/mime/base.py \
  $(BUILD_DIR)/windows/Win32/Lib/email/mime/image.py \
  $(BUILD_DIR)/windows/Win32/Lib/email/mime/message.py \
  $(BUILD_DIR)/windows/Win32/Lib/email/mime/multipart.py \
  $(BUILD_DIR)/windows/Win32/Lib/email/mime/nonmultipart.py \
  $(BUILD_DIR)/windows/Win32/Lib/email/mime/text.py \
  $(BUILD_DIR)/windows/Win32/Lib/email/parser.py \
  $(BUILD_DIR)/windows/Win32/Lib/email/policy.py \
  $(BUILD_DIR)/windows/Win32/Lib/email/quoprimime.py \
  $(BUILD_DIR)/windows/Win32/Lib/email/utils.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/__init__.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/_win_cp_codecs.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/aliases.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/ascii.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/base64_codec.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/big5.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/big5hkscs.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/bz2_codec.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/charmap.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/cp037.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/cp1006.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/cp1026.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/cp1125.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/cp1140.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/cp1250.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/cp1251.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/cp1252.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/cp1253.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/cp1254.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/cp1255.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/cp1256.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/cp1257.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/cp1258.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/cp273.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/cp424.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/cp437.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/cp500.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/cp720.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/cp737.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/cp775.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/cp850.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/cp852.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/cp855.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/cp856.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/cp857.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/cp858.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/cp860.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/cp861.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/cp862.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/cp863.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/cp864.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/cp865.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/cp866.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/cp869.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/cp874.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/cp875.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/cp932.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/cp949.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/cp950.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/euc_jis_2004.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/euc_jisx0213.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/euc_jp.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/euc_kr.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/gb18030.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/gb2312.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/gbk.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/hex_codec.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/hp_roman8.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/hz.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/idna.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/iso2022_jp.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/iso2022_jp_1.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/iso2022_jp_2.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/iso2022_jp_2004.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/iso2022_jp_3.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/iso2022_jp_ext.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/iso2022_kr.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/iso8859_1.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/iso8859_10.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/iso8859_11.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/iso8859_13.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/iso8859_14.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/iso8859_15.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/iso8859_16.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/iso8859_2.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/iso8859_3.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/iso8859_4.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/iso8859_5.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/iso8859_6.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/iso8859_7.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/iso8859_8.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/iso8859_9.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/johab.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/koi8_r.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/koi8_t.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/koi8_u.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/kz1048.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/latin_1.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/mac_arabic.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/mac_croatian.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/mac_cyrillic.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/mac_farsi.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/mac_greek.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/mac_iceland.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/mac_latin2.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/mac_roman.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/mac_romanian.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/mac_turkish.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/mbcs.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/oem.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/palmos.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/ptcp154.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/punycode.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/quopri_codec.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/raw_unicode_escape.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/rot_13.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/shift_jis.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/shift_jis_2004.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/shift_jisx0213.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/tis_620.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/undefined.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/unicode_escape.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/utf_16.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/utf_16_be.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/utf_16_le.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/utf_32.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/utf_32_be.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/utf_32_le.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/utf_7.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/utf_8.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/utf_8_sig.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/uu_codec.py \
  $(BUILD_DIR)/windows/Win32/Lib/encodings/zlib_codec.py \
  $(BUILD_DIR)/windows/Win32/Lib/enum.py \
  $(BUILD_DIR)/windows/Win32/Lib/filecmp.py \
  $(BUILD_DIR)/windows/Win32/Lib/fileinput.py \
  $(BUILD_DIR)/windows/Win32/Lib/fnmatch.py \
  $(BUILD_DIR)/windows/Win32/Lib/fractions.py \
  $(BUILD_DIR)/windows/Win32/Lib/ftplib.py \
  $(BUILD_DIR)/windows/Win32/Lib/functools.py \
  $(BUILD_DIR)/windows/Win32/Lib/genericpath.py \
  $(BUILD_DIR)/windows/Win32/Lib/getopt.py \
  $(BUILD_DIR)/windows/Win32/Lib/getpass.py \
  $(BUILD_DIR)/windows/Win32/Lib/gettext.py \
  $(BUILD_DIR)/windows/Win32/Lib/glob.py \
  $(BUILD_DIR)/windows/Win32/Lib/graphlib.py \
  $(BUILD_DIR)/windows/Win32/Lib/gzip.py \
  $(BUILD_DIR)/windows/Win32/Lib/hashlib.py \
  $(BUILD_DIR)/windows/Win32/Lib/heapq.py \
  $(BUILD_DIR)/windows/Win32/Lib/hmac.py \
  $(BUILD_DIR)/windows/Win32/Lib/html/__init__.py \
  $(BUILD_DIR)/windows/Win32/Lib/html/entities.py \
  $(BUILD_DIR)/windows/Win32/Lib/html/parser.py \
  $(BUILD_DIR)/windows/Win32/Lib/http/__init__.py \
  $(BUILD_DIR)/windows/Win32/Lib/http/client.py \
  $(BUILD_DIR)/windows/Win32/Lib/http/cookiejar.py \
  $(BUILD_DIR)/windows/Win32/Lib/http/cookies.py \
  $(BUILD_DIR)/windows/Win32/Lib/http/server.py \
  $(BUILD_DIR)/windows/Win32/Lib/importlib/__init__.py \
  $(BUILD_DIR)/windows/Win32/Lib/importlib/_abc.py \
  $(BUILD_DIR)/windows/Win32/Lib/importlib/_bootstrap.py \
  $(BUILD_DIR)/windows/Win32/Lib/importlib/_bootstrap_external.py \
  $(BUILD_DIR)/windows/Win32/Lib/importlib/abc.py \
  $(BUILD_DIR)/windows/Win32/Lib/importlib/machinery.py \
  $(BUILD_DIR)/windows/Win32/Lib/importlib/metadata/__init__.py \
  $(BUILD_DIR)/windows/Win32/Lib/importlib/metadata/_adapters.py \
  $(BUILD_DIR)/windows/Win32/Lib/importlib/metadata/_collections.py \
  $(BUILD_DIR)/windows/Win32/Lib/importlib/metadata/_functools.py \
  $(BUILD_DIR)/windows/Win32/Lib/importlib/metadata/_itertools.py \
  $(BUILD_DIR)/windows/Win32/Lib/importlib/metadata/_meta.py \
  $(BUILD_DIR)/windows/Win32/Lib/importlib/metadata/_text.py \
  $(BUILD_DIR)/windows/Win32/Lib/importlib/metadata/diagnose.py \
  $(BUILD_DIR)/windows/Win32/Lib/importlib/readers.py \
  $(BUILD_DIR)/windows/Win32/Lib/importlib/resources/__init__.py \
  $(BUILD_DIR)/windows/Win32/Lib/importlib/resources/_adapters.py \
  $(BUILD_DIR)/windows/Win32/Lib/importlib/resources/_common.py \
  $(BUILD_DIR)/windows/Win32/Lib/importlib/resources/_functional.py \
  $(BUILD_DIR)/windows/Win32/Lib/importlib/resources/_itertools.py \
  $(BUILD_DIR)/windows/Win32/Lib/importlib/resources/abc.py \
  $(BUILD_DIR)/windows/Win32/Lib/importlib/resources/readers.py \
  $(BUILD_DIR)/windows/Win32/Lib/importlib/resources/simple.py \
  $(BUILD_DIR)/windows/Win32/Lib/importlib/simple.py \
  $(BUILD_DIR)/windows/Win32/Lib/importlib/util.py \
  $(BUILD_DIR)/windows/Win32/Lib/inspect.py \
  $(BUILD_DIR)/windows/Win32/Lib/io.py \
  $(BUILD_DIR)/windows/Win32/Lib/ipaddress.py \
  $(BUILD_DIR)/windows/Win32/Lib/json/__init__.py \
  $(BUILD_DIR)/windows/Win32/Lib/json/__main__.py \
  $(BUILD_DIR)/windows/Win32/Lib/json/decoder.py \
  $(BUILD_DIR)/windows/Win32/Lib/json/encoder.py \
  $(BUILD_DIR)/windows/Win32/Lib/json/scanner.py \
  $(BUILD_DIR)/windows/Win32/Lib/json/tool.py \
  $(BUILD_DIR)/windows/Win32/Lib/keyword.py \
  $(BUILD_DIR)/windows/Win32/Lib/linecache.py \
  $(BUILD_DIR)/windows/Win32/Lib/locale.py \
  $(BUILD_DIR)/windows/Win32/Lib/logging/__init__.py \
  $(BUILD_DIR)/windows/Win32/Lib/logging/config.py \
  $(BUILD_DIR)/windows/Win32/Lib/logging/handlers.py \
  $(BUILD_DIR)/windows/Win32/Lib/lzma.py \
  $(BUILD_DIR)/windows/Win32/Lib/mailbox.py \
  $(BUILD_DIR)/windows/Win32/Lib/mimetypes.py \
  $(BUILD_DIR)/windows/Win32/Lib/modulefinder.py \
  $(BUILD_DIR)/windows/Win32/Lib/netrc.py \
  $(BUILD_DIR)/windows/Win32/Lib/ntpath.py \
  $(BUILD_DIR)/windows/Win32/Lib/nturl2path.py \
  $(BUILD_DIR)/windows/Win32/Lib/numbers.py \
  $(BUILD_DIR)/windows/Win32/Lib/opcode.py \
  $(BUILD_DIR)/windows/Win32/Lib/operator.py \
  $(BUILD_DIR)/windows/Win32/Lib/optparse.py \
  $(BUILD_DIR)/windows/Win32/Lib/os.py \
  $(BUILD_DIR)/windows/Win32/Lib/pathlib/__init__.py \
  $(BUILD_DIR)/windows/Win32/Lib/pathlib/_local.py \
  $(BUILD_DIR)/windows/Win32/Lib/pathlib/_os.py \
  $(BUILD_DIR)/windows/Win32/Lib/pathlib/types.py \
  $(BUILD_DIR)/windows/Win32/Lib/pdb.py \
  $(BUILD_DIR)/windows/Win32/Lib/pickle.py \
  $(BUILD_DIR)/windows/Win32/Lib/pickletools.py \
  $(BUILD_DIR)/windows/Win32/Lib/pkgutil.py \
  $(BUILD_DIR)/windows/Win32/Lib/platform.py \
  $(BUILD_DIR)/windows/Win32/Lib/plistlib.py \
  $(BUILD_DIR)/windows/Win32/Lib/poplib.py \
  $(BUILD_DIR)/windows/Win32/Lib/posixpath.py \
  $(BUILD_DIR)/windows/Win32/Lib/pprint.py \
  $(BUILD_DIR)/windows/Win32/Lib/profile.py \
  $(BUILD_DIR)/windows/Win32/Lib/pstats.py \
  $(BUILD_DIR)/windows/Win32/Lib/pty.py \
  $(BUILD_DIR)/windows/Win32/Lib/py_compile.py \
  $(BUILD_DIR)/windows/Win32/Lib/pyclbr.py \
  $(BUILD_DIR)/windows/Win32/Lib/pydoc.py \
  $(BUILD_DIR)/windows/Win32/Lib/queue.py \
  $(BUILD_DIR)/windows/Win32/Lib/quopri.py \
  $(BUILD_DIR)/windows/Win32/Lib/random.py \
  $(BUILD_DIR)/windows/Win32/Lib/re/__init__.py \
  $(BUILD_DIR)/windows/Win32/Lib/re/_casefix.py \
  $(BUILD_DIR)/windows/Win32/Lib/re/_compiler.py \
  $(BUILD_DIR)/windows/Win32/Lib/re/_constants.py \
  $(BUILD_DIR)/windows/Win32/Lib/re/_parser.py \
  $(BUILD_DIR)/windows/Win32/Lib/reprlib.py \
  $(BUILD_DIR)/windows/Win32/Lib/rlcompleter.py \
  $(BUILD_DIR)/windows/Win32/Lib/runpy.py \
  $(BUILD_DIR)/windows/Win32/Lib/sched.py \
  $(BUILD_DIR)/windows/Win32/Lib/secrets.py \
  $(BUILD_DIR)/windows/Win32/Lib/selectors.py \
  $(BUILD_DIR)/windows/Win32/Lib/shelve.py \
  $(BUILD_DIR)/windows/Win32/Lib/shlex.py \
  $(BUILD_DIR)/windows/Win32/Lib/shutil.py \
  $(BUILD_DIR)/windows/Win32/Lib/signal.py \
  $(BUILD_DIR)/windows/Win32/Lib/site.py \
  $(BUILD_DIR)/windows/Win32/Lib/smtplib.py \
  $(BUILD_DIR)/windows/Win32/Lib/socket.py \
  $(BUILD_DIR)/windows/Win32/Lib/socketserver.py \
  $(BUILD_DIR)/windows/Win32/Lib/sqlite3/__init__.py \
  $(BUILD_DIR)/windows/Win32/Lib/sqlite3/__main__.py \
  $(BUILD_DIR)/windows/Win32/Lib/sqlite3/dbapi2.py \
  $(BUILD_DIR)/windows/Win32/Lib/sqlite3/dump.py \
  $(BUILD_DIR)/windows/Win32/Lib/sre_compile.py \
  $(BUILD_DIR)/windows/Win32/Lib/sre_constants.py \
  $(BUILD_DIR)/windows/Win32/Lib/sre_parse.py \
  $(BUILD_DIR)/windows/Win32/Lib/ssl.py \
  $(BUILD_DIR)/windows/Win32/Lib/stat.py \
  $(BUILD_DIR)/windows/Win32/Lib/statistics.py \
  $(BUILD_DIR)/windows/Win32/Lib/string/__init__.py \
  $(BUILD_DIR)/windows/Win32/Lib/string/templatelib.py \
  $(BUILD_DIR)/windows/Win32/Lib/stringprep.py \
  $(BUILD_DIR)/windows/Win32/Lib/struct.py \
  $(BUILD_DIR)/windows/Win32/Lib/subprocess.py \
  $(BUILD_DIR)/windows/Win32/Lib/symtable.py \
  $(BUILD_DIR)/windows/Win32/Lib/sysconfig/__init__.py \
  $(BUILD_DIR)/windows/Win32/Lib/sysconfig/__main__.py \
  $(BUILD_DIR)/windows/Win32/Lib/tabnanny.py \
  $(BUILD_DIR)/windows/Win32/Lib/tarfile.py \
  $(BUILD_DIR)/windows/Win32/Lib/tempfile.py \
  $(BUILD_DIR)/windows/Win32/Lib/textwrap.py \
  $(BUILD_DIR)/windows/Win32/Lib/this.py \
  $(BUILD_DIR)/windows/Win32/Lib/threading.py \
  $(BUILD_DIR)/windows/Win32/Lib/timeit.py \
  $(BUILD_DIR)/windows/Win32/Lib/token.py \
  $(BUILD_DIR)/windows/Win32/Lib/tokenize.py \
  $(BUILD_DIR)/windows/Win32/Lib/tomllib/__init__.py \
  $(BUILD_DIR)/windows/Win32/Lib/tomllib/_parser.py \
  $(BUILD_DIR)/windows/Win32/Lib/tomllib/_re.py \
  $(BUILD_DIR)/windows/Win32/Lib/tomllib/_types.py \
  $(BUILD_DIR)/windows/Win32/Lib/trace.py \
  $(BUILD_DIR)/windows/Win32/Lib/traceback.py \
  $(BUILD_DIR)/windows/Win32/Lib/tracemalloc.py \
  $(BUILD_DIR)/windows/Win32/Lib/tty.py \
  $(BUILD_DIR)/windows/Win32/Lib/types.py \
  $(BUILD_DIR)/windows/Win32/Lib/typing.py \
  $(BUILD_DIR)/windows/Win32/Lib/urllib/__init__.py \
  $(BUILD_DIR)/windows/Win32/Lib/urllib/error.py \
  $(BUILD_DIR)/windows/Win32/Lib/urllib/parse.py \
  $(BUILD_DIR)/windows/Win32/Lib/urllib/request.py \
  $(BUILD_DIR)/windows/Win32/Lib/urllib/response.py \
  $(BUILD_DIR)/windows/Win32/Lib/urllib/robotparser.py \
  $(BUILD_DIR)/windows/Win32/Lib/uuid.py \
  $(BUILD_DIR)/windows/Win32/Lib/warnings.py \
  $(BUILD_DIR)/windows/Win32/Lib/wave.py \
  $(BUILD_DIR)/windows/Win32/Lib/weakref.py \
  $(BUILD_DIR)/windows/Win32/Lib/webbrowser.py \
  $(BUILD_DIR)/windows/Win32/Lib/xml/__init__.py \
  $(BUILD_DIR)/windows/Win32/Lib/xml/dom/NodeFilter.py \
  $(BUILD_DIR)/windows/Win32/Lib/xml/dom/__init__.py \
  $(BUILD_DIR)/windows/Win32/Lib/xml/dom/domreg.py \
  $(BUILD_DIR)/windows/Win32/Lib/xml/dom/expatbuilder.py \
  $(BUILD_DIR)/windows/Win32/Lib/xml/dom/minicompat.py \
  $(BUILD_DIR)/windows/Win32/Lib/xml/dom/minidom.py \
  $(BUILD_DIR)/windows/Win32/Lib/xml/dom/pulldom.py \
  $(BUILD_DIR)/windows/Win32/Lib/xml/dom/xmlbuilder.py \
  $(BUILD_DIR)/windows/Win32/Lib/xml/etree/ElementInclude.py \
  $(BUILD_DIR)/windows/Win32/Lib/xml/etree/ElementPath.py \
  $(BUILD_DIR)/windows/Win32/Lib/xml/etree/ElementTree.py \
  $(BUILD_DIR)/windows/Win32/Lib/xml/etree/__init__.py \
  $(BUILD_DIR)/windows/Win32/Lib/xml/etree/cElementTree.py \
  $(BUILD_DIR)/windows/Win32/Lib/xml/parsers/__init__.py \
  $(BUILD_DIR)/windows/Win32/Lib/xml/parsers/expat.py \
  $(BUILD_DIR)/windows/Win32/Lib/xml/sax/__init__.py \
  $(BUILD_DIR)/windows/Win32/Lib/xml/sax/_exceptions.py \
  $(BUILD_DIR)/windows/Win32/Lib/xml/sax/expatreader.py \
  $(BUILD_DIR)/windows/Win32/Lib/xml/sax/handler.py \
  $(BUILD_DIR)/windows/Win32/Lib/xml/sax/saxutils.py \
  $(BUILD_DIR)/windows/Win32/Lib/xml/sax/xmlreader.py \
  $(BUILD_DIR)/windows/Win32/Lib/xmlrpc/__init__.py \
  $(BUILD_DIR)/windows/Win32/Lib/xmlrpc/client.py \
  $(BUILD_DIR)/windows/Win32/Lib/xmlrpc/server.py \
  $(BUILD_DIR)/windows/Win32/Lib/zipapp.py \
  $(BUILD_DIR)/windows/Win32/Lib/zipfile/__init__.py \
  $(BUILD_DIR)/windows/Win32/Lib/zipfile/__main__.py \
  $(BUILD_DIR)/windows/Win32/Lib/zipfile/_path/__init__.py \
  $(BUILD_DIR)/windows/Win32/Lib/zipfile/_path/glob.py \
  $(BUILD_DIR)/windows/Win32/Lib/zipimport.py \
  $(BUILD_DIR)/windows/Win32/Lib/zoneinfo/__init__.py \
  $(BUILD_DIR)/windows/Win32/Lib/zoneinfo/_common.py \
  $(BUILD_DIR)/windows/Win32/Lib/zoneinfo/_tzpath.py \
  $(BUILD_DIR)/windows/Win32/Lib/zoneinfo/_zoneinfo.py

SCRIPT_TARGETS_SO_PRIVATE_WIN_WIN32 = \
  

SCRIPT_TARGETS_ZSTDDICT_PRIVATE_WIN_WIN32 = \
  

# Rule to copy src asset scripts to dst.
# (and make non-writable so I'm less likely to accidentally edit them there)
$(SCRIPT_TARGETS_PY_PRIVATE_WIN_WIN32) : ../../.efrocachemap
	@cd ../.. && $(PCOMMANDBATCHFROMROOT) efrocache_get src/assets/$@


SCRIPT_TARGETS_PY_PRIVATE_WIN_X64 = \
  $(BUILD_DIR)/windows/x64/Lib/__future__.py \
  $(BUILD_DIR)/windows/x64/Lib/__hello__.py \
  $(BUILD_DIR)/windows/x64/Lib/_aix_support.py \
  $(BUILD_DIR)/windows/x64/Lib/_android_support.py \
  $(BUILD_DIR)/windows/x64/Lib/_apple_support.py \
  $(BUILD_DIR)/windows/x64/Lib/_ast_unparse.py \
  $(BUILD_DIR)/windows/x64/Lib/_collections_abc.py \
  $(BUILD_DIR)/windows/x64/Lib/_colorize.py \
  $(BUILD_DIR)/windows/x64/Lib/_compat_pickle.py \
  $(BUILD_DIR)/windows/x64/Lib/_ios_support.py \
  $(BUILD_DIR)/windows/x64/Lib/_markupbase.py \
  $(BUILD_DIR)/windows/x64/Lib/_opcode_metadata.py \
  $(BUILD_DIR)/windows/x64/Lib/_osx_support.py \
  $(BUILD_DIR)/windows/x64/Lib/_py_abc.py \
  $(BUILD_DIR)/windows/x64/Lib/_py_warnings.py \
  $(BUILD_DIR)/windows/x64/Lib/_pydatetime.py \
  $(BUILD_DIR)/windows/x64/Lib/_pydecimal.py \
  $(BUILD_DIR)/windows/x64/Lib/_pyio.py \
  $(BUILD_DIR)/windows/x64/Lib/_pylong.py \
  $(BUILD_DIR)/windows/x64/Lib/_pyrepl/__init__.py \
  $(BUILD_DIR)/windows/x64/Lib/_pyrepl/__main__.py \
  $(BUILD_DIR)/windows/x64/Lib/_pyrepl/_module_completer.py \
  $(BUILD_DIR)/windows/x64/Lib/_pyrepl/_threading_handler.py \
  $(BUILD_DIR)/windows/x64/Lib/_pyrepl/base_eventqueue.py \
  $(BUILD_DIR)/windows/x64/Lib/_pyrepl/commands.py \
  $(BUILD_DIR)/windows/x64/Lib/_pyrepl/completing_reader.py \
  $(BUILD_DIR)/windows/x64/Lib/_pyrepl/console.py \
  $(BUILD_DIR)/windows/x64/Lib/_pyrepl/fancy_termios.py \
  $(BUILD_DIR)/windows/x64/Lib/_pyrepl/historical_reader.py \
  $(BUILD_DIR)/windows/x64/Lib/_pyrepl/input.py \
  $(BUILD_DIR)/windows/x64/Lib/_pyrepl/keymap.py \
  $(BUILD_DIR)/windows/x64/Lib/_pyrepl/main.py \
  $(BUILD_DIR)/windows/x64/Lib/_pyrepl/pager.py \
  $(BUILD_DIR)/windows/x64/Lib/_pyrepl/reader.py \
  $(BUILD_DIR)/windows/x64/Lib/_pyrepl/readline.py \
  $(BUILD_DIR)/windows/x64/Lib/_pyrepl/simple_interact.py \
  $(BUILD_DIR)/windows/x64/Lib/_pyrepl/terminfo.py \
  $(BUILD_DIR)/windows/x64/Lib/_pyrepl/trace.py \
  $(BUILD_DIR)/windows/x64/Lib/_pyrepl/types.py \
  $(BUILD_DIR)/windows/x64/Lib/_pyrepl/unix_console.py \
  $(BUILD_DIR)/windows/x64/Lib/_pyrepl/unix_eventqueue.py \
  $(BUILD_DIR)/windows/x64/Lib/_pyrepl/utils.py \
  $(BUILD_DIR)/windows/x64/Lib/_pyrepl/windows_console.py \
  $(BUILD_DIR)/windows/x64/Lib/_pyrepl/windows_eventqueue.py \
  $(BUILD_DIR)/windows/x64/Lib/_sitebuiltins.py \
  $(BUILD_DIR)/windows/x64/Lib/_strptime.py \
  $(BUILD_DIR)/windows/x64/Lib/_threading_local.py \
  $(BUILD_DIR)/windows/x64/Lib/_weakrefset.py \
  $(BUILD_DIR)/windows/x64/Lib/abc.py \
  $(BUILD_DIR)/windows/x64/Lib/annotationlib.py \
  $(BUILD_DIR)/windows/x64/Lib/antigravity.py \
  $(BUILD_DIR)/windows/x64/Lib/argparse.py \
  $(BUILD_DIR)/windows/x64/Lib/ast.py \
  $(BUILD_DIR)/windows/x64/Lib/asyncio/__init__.py \
  $(BUILD_DIR)/windows/x64/Lib/asyncio/__main__.py \
  $(BUILD_DIR)/windows/x64/Lib/asyncio/base_events.py \
  $(BUILD_DIR)/windows/x64/Lib/asyncio/base_futures.py \
  $(BUILD_DIR)/windows/x64/Lib/asyncio/base_subprocess.py \
  $(BUILD_DIR)/windows/x64/Lib/asyncio/base_tasks.py \
  $(BUILD_DIR)/windows/x64/Lib/asyncio/constants.py \
  $(BUILD_DIR)/windows/x64/Lib/asyncio/coroutines.py \
  $(BUILD_DIR)/windows/x64/Lib/asyncio/events.py \
  $(BUILD_DIR)/windows/x64/Lib/asyncio/exceptions.py \
  $(BUILD_DIR)/windows/x64/Lib/asyncio/format_helpers.py \
  $(BUILD_DIR)/windows/x64/Lib/asyncio/futures.py \
  $(BUILD_DIR)/windows/x64/Lib/asyncio/graph.py \
  $(BUILD_DIR)/windows/x64/Lib/asyncio/locks.py \
  $(BUILD_DIR)/windows/x64/Lib/asyncio/log.py \
  $(BUILD_DIR)/windows/x64/Lib/asyncio/mixins.py \
  $(BUILD_DIR)/windows/x64/Lib/asyncio/proactor_events.py \
  $(BUILD_DIR)/windows/x64/Lib/asyncio/protocols.py \
  $(BUILD_DIR)/windows/x64/Lib/asyncio/queues.py \
  $(BUILD_DIR)/windows/x64/Lib/asyncio/runners.py \
  $(BUILD_DIR)/windows/x64/Lib/asyncio/selector_events.py \
  $(BUILD_DIR)/windows/x64/Lib/asyncio/sslproto.py \
  $(BUILD_DIR)/windows/x64/Lib/asyncio/staggered.py \
  $(BUILD_DIR)/windows/x64/Lib/asyncio/streams.py \
  $(BUILD_DIR)/windows/x64/Lib/asyncio/subprocess.py \
  $(BUILD_DIR)/windows/x64/Lib/asyncio/taskgroups.py \
  $(BUILD_DIR)/windows/x64/Lib/asyncio/tasks.py \
  $(BUILD_DIR)/windows/x64/Lib/asyncio/threads.py \
  $(BUILD_DIR)/windows/x64/Lib/asyncio/timeouts.py \
  $(BUILD_DIR)/windows/x64/Lib/asyncio/tools.py \
  $(BUILD_DIR)/windows/x64/Lib/asyncio/transports.py \
  $(BUILD_DIR)/windows/x64/Lib/asyncio/trsock.py \
  $(BUILD_DIR)/windows/x64/Lib/asyncio/unix_events.py \
  $(BUILD_DIR)/windows/x64/Lib/asyncio/windows_events.py \
  $(BUILD_DIR)/windows/x64/Lib/asyncio/windows_utils.py \
  $(BUILD_DIR)/windows/x64/Lib/base64.py \
  $(BUILD_DIR)/windows/x64/Lib/bdb.py \
  $(BUILD_DIR)/windows/x64/Lib/bisect.py \
  $(BUILD_DIR)/windows/x64/Lib/bz2.py \
  $(BUILD_DIR)/windows/x64/Lib/cProfile.py \
  $(BUILD_DIR)/windows/x64/Lib/calendar.py \
  $(BUILD_DIR)/windows/x64/Lib/cmd.py \
  $(BUILD_DIR)/windows/x64/Lib/code.py \
  $(BUILD_DIR)/windows/x64/Lib/codecs.py \
  $(BUILD_DIR)/windows/x64/Lib/codeop.py \
  $(BUILD_DIR)/windows/x64/Lib/collections/__init__.py \
  $(BUILD_DIR)/windows/x64/Lib/colorsys.py \
  $(BUILD_DIR)/windows/x64/Lib/compileall.py \
  $(BUILD_DIR)/windows/x64/Lib/compression/__init__.py \
  $(BUILD_DIR)/windows/x64/Lib/compression/_common/__init__.py \
  $(BUILD_DIR)/windows/x64/Lib/compression/_common/_streams.py \
  $(BUILD_DIR)/windows/x64/Lib/compression/bz2.py \
  $(BUILD_DIR)/windows/x64/Lib/compression/gzip.py \
  $(BUILD_DIR)/windows/x64/Lib/compression/lzma.py \
  $(BUILD_DIR)/windows/x64/Lib/compression/zlib.py \
  $(BUILD_DIR)/windows/x64/Lib/compression/zstd/__init__.py \
  $(BUILD_DIR)/windows/x64/Lib/compression/zstd/_zstdfile.py \
  $(BUILD_DIR)/windows/x64/Lib/concurrent/__init__.py \
  $(BUILD_DIR)/windows/x64/Lib/concurrent/futures/__init__.py \
  $(BUILD_DIR)/windows/x64/Lib/concurrent/futures/_base.py \
  $(BUILD_DIR)/windows/x64/Lib/concurrent/futures/interpreter.py \
  $(BUILD_DIR)/windows/x64/Lib/concurrent/futures/process.py \
  $(BUILD_DIR)/windows/x64/Lib/concurrent/futures/thread.py \
  $(BUILD_DIR)/windows/x64/Lib/concurrent/interpreters/__init__.py \
  $(BUILD_DIR)/windows/x64/Lib/concurrent/interpreters/_crossinterp.py \
  $(BUILD_DIR)/windows/x64/Lib/concurrent/interpreters/_queues.py \
  $(BUILD_DIR)/windows/x64/Lib/configparser.py \
  $(BUILD_DIR)/windows/x64/Lib/contextlib.py \
  $(BUILD_DIR)/windows/x64/Lib/contextvars.py \
  $(BUILD_DIR)/windows/x64/Lib/copy.py \
  $(BUILD_DIR)/windows/x64/Lib/copyreg.py \
  $(BUILD_DIR)/windows/x64/Lib/csv.py \
  $(BUILD_DIR)/windows/x64/Lib/ctypes/__init__.py \
  $(BUILD_DIR)/windows/x64/Lib/ctypes/_aix.py \
  $(BUILD_DIR)/windows/x64/Lib/ctypes/_endian.py \
  $(BUILD_DIR)/windows/x64/Lib/ctypes/_layout.py \
  $(BUILD_DIR)/windows/x64/Lib/ctypes/macholib/__init__.py \
  $(BUILD_DIR)/windows/x64/Lib/ctypes/macholib/dyld.py \
  $(BUILD_DIR)/windows/x64/Lib/ctypes/macholib/dylib.py \
  $(BUILD_DIR)/windows/x64/Lib/ctypes/macholib/framework.py \
  $(BUILD_DIR)/windows/x64/Lib/ctypes/util.py \
  $(BUILD_DIR)/windows/x64/Lib/ctypes/wintypes.py \
  $(BUILD_DIR)/windows/x64/Lib/curses/__init__.py \
  $(BUILD_DIR)/windows/x64/Lib/curses/ascii.py \
  $(BUILD_DIR)/windows/x64/Lib/curses/has_key.py \
  $(BUILD_DIR)/windows/x64/Lib/curses/panel.py \
  $(BUILD_DIR)/windows/x64/Lib/curses/textpad.py \
  $(BUILD_DIR)/windows/x64/Lib/dataclasses.py \
  $(BUILD_DIR)/windows/x64/Lib/datetime.py \
  $(BUILD_DIR)/windows/x64/Lib/decimal.py \
  $(BUILD_DIR)/windows/x64/Lib/difflib.py \
  $(BUILD_DIR)/windows/x64/Lib/dis.py \
  $(BUILD_DIR)/windows/x64/Lib/doctest.py \
  $(BUILD_DIR)/windows/x64/Lib/email/__init__.py \
  $(BUILD_DIR)/windows/x64/Lib/email/_encoded_words.py \
  $(BUILD_DIR)/windows/x64/Lib/email/_header_value_parser.py \
  $(BUILD_DIR)/windows/x64/Lib/email/_parseaddr.py \
  $(BUILD_DIR)/windows/x64/Lib/email/_policybase.py \
  $(BUILD_DIR)/windows/x64/Lib/email/base64mime.py \
  $(BUILD_DIR)/windows/x64/Lib/email/charset.py \
  $(BUILD_DIR)/windows/x64/Lib/email/contentmanager.py \
  $(BUILD_DIR)/windows/x64/Lib/email/encoders.py \
  $(BUILD_DIR)/windows/x64/Lib/email/errors.py \
  $(BUILD_DIR)/windows/x64/Lib/email/feedparser.py \
  $(BUILD_DIR)/windows/x64/Lib/email/generator.py \
  $(BUILD_DIR)/windows/x64/Lib/email/header.py \
  $(BUILD_DIR)/windows/x64/Lib/email/headerregistry.py \
  $(BUILD_DIR)/windows/x64/Lib/email/iterators.py \
  $(BUILD_DIR)/windows/x64/Lib/email/message.py \
  $(BUILD_DIR)/windows/x64/Lib/email/mime/__init__.py \
  $(BUILD_DIR)/windows/x64/Lib/email/mime/application.py \
  $(BUILD_DIR)/windows/x64/Lib/email/mime/audio.py \
  $(BUILD_DIR)/windows/x64/Lib/email/mime/base.py \
  $(BUILD_DIR)/windows/x64/Lib/email/mime/image.py \
  $(BUILD_DIR)/windows/x64/Lib/email/mime/message.py \
  $(BUILD_DIR)/windows/x64/Lib/email/mime/multipart.py \
  $(BUILD_DIR)/windows/x64/Lib/email/mime/nonmultipart.py \
  $(BUILD_DIR)/windows/x64/Lib/email/mime/text.py \
  $(BUILD_DIR)/windows/x64/Lib/email/parser.py \
  $(BUILD_DIR)/windows/x64/Lib/email/policy.py \
  $(BUILD_DIR)/windows/x64/Lib/email/quoprimime.py \
  $(BUILD_DIR)/windows/x64/Lib/email/utils.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/__init__.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/_win_cp_codecs.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/aliases.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/ascii.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/base64_codec.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/big5.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/big5hkscs.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/bz2_codec.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/charmap.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/cp037.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/cp1006.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/cp1026.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/cp1125.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/cp1140.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/cp1250.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/cp1251.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/cp1252.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/cp1253.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/cp1254.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/cp1255.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/cp1256.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/cp1257.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/cp1258.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/cp273.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/cp424.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/cp437.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/cp500.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/cp720.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/cp737.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/cp775.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/cp850.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/cp852.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/cp855.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/cp856.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/cp857.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/cp858.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/cp860.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/cp861.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/cp862.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/cp863.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/cp864.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/cp865.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/cp866.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/cp869.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/cp874.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/cp875.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/cp932.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/cp949.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/cp950.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/euc_jis_2004.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/euc_jisx0213.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/euc_jp.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/euc_kr.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/gb18030.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/gb2312.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/gbk.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/hex_codec.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/hp_roman8.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/hz.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/idna.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/iso2022_jp.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/iso2022_jp_1.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/iso2022_jp_2.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/iso2022_jp_2004.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/iso2022_jp_3.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/iso2022_jp_ext.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/iso2022_kr.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/iso8859_1.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/iso8859_10.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/iso8859_11.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/iso8859_13.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/iso8859_14.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/iso8859_15.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/iso8859_16.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/iso8859_2.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/iso8859_3.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/iso8859_4.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/iso8859_5.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/iso8859_6.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/iso8859_7.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/iso8859_8.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/iso8859_9.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/johab.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/koi8_r.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/koi8_t.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/koi8_u.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/kz1048.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/latin_1.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/mac_arabic.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/mac_croatian.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/mac_cyrillic.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/mac_farsi.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/mac_greek.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/mac_iceland.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/mac_latin2.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/mac_roman.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/mac_romanian.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/mac_turkish.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/mbcs.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/oem.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/palmos.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/ptcp154.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/punycode.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/quopri_codec.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/raw_unicode_escape.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/rot_13.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/shift_jis.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/shift_jis_2004.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/shift_jisx0213.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/tis_620.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/undefined.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/unicode_escape.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/utf_16.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/utf_16_be.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/utf_16_le.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/utf_32.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/utf_32_be.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/utf_32_le.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/utf_7.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/utf_8.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/utf_8_sig.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/uu_codec.py \
  $(BUILD_DIR)/windows/x64/Lib/encodings/zlib_codec.py \
  $(BUILD_DIR)/windows/x64/Lib/enum.py \
  $(BUILD_DIR)/windows/x64/Lib/filecmp.py \
  $(BUILD_DIR)/windows/x64/Lib/fileinput.py \
  $(BUILD_DIR)/windows/x64/Lib/fnmatch.py \
  $(BUILD_DIR)/windows/x64/Lib/fractions.py \
  $(BUILD_DIR)/windows/x64/Lib/ftplib.py \
  $(BUILD_DIR)/windows/x64/Lib/functools.py \
  $(BUILD_DIR)/windows/x64/Lib/genericpath.py \
  $(BUILD_DIR)/windows/x64/Lib/getopt.py \
  $(BUILD_DIR)/windows/x64/Lib/getpass.py \
  $(BUILD_DIR)/windows/x64/Lib/gettext.py \
  $(BUILD_DIR)/windows/x64/Lib/glob.py \
  $(BUILD_DIR)/windows/x64/Lib/graphlib.py \
  $(BUILD_DIR)/windows/x64/Lib/gzip.py \
  $(BUILD_DIR)/windows/x64/Lib/hashlib.py \
  $(BUILD_DIR)/windows/x64/Lib/heapq.py \
  $(BUILD_DIR)/windows/x64/Lib/hmac.py \
  $(BUILD_DIR)/windows/x64/Lib/html/__init__.py \
  $(BUILD_DIR)/windows/x64/Lib/html/entities.py \
  $(BUILD_DIR)/windows/x64/Lib/html/parser.py \
  $(BUILD_DIR)/windows/x64/Lib/http/__init__.py \
  $(BUILD_DIR)/windows/x64/Lib/http/client.py \
  $(BUILD_DIR)/windows/x64/Lib/http/cookiejar.py \
  $(BUILD_DIR)/windows/x64/Lib/http/cookies.py \
  $(BUILD_DIR)/windows/x64/Lib/http/server.py \
  $(BUILD_DIR)/windows/x64/Lib/importlib/__init__.py \
  $(BUILD_DIR)/windows/x64/Lib/importlib/_abc.py \
  $(BUILD_DIR)/windows/x64/Lib/importlib/_bootstrap.py \
  $(BUILD_DIR)/windows/x64/Lib/importlib/_bootstrap_external.py \
  $(BUILD_DIR)/windows/x64/Lib/importlib/abc.py \
  $(BUILD_DIR)/windows/x64/Lib/importlib/machinery.py \
  $(BUILD_DIR)/windows/x64/Lib/importlib/metadata/__init__.py \
  $(BUILD_DIR)/windows/x64/Lib/importlib/metadata/_adapters.py \
  $(BUILD_DIR)/windows/x64/Lib/importlib/metadata/_collections.py \
  $(BUILD_DIR)/windows/x64/Lib/importlib/metadata/_functools.py \
  $(BUILD_DIR)/windows/x64/Lib/importlib/metadata/_itertools.py \
  $(BUILD_DIR)/windows/x64/Lib/importlib/metadata/_meta.py \
  $(BUILD_DIR)/windows/x64/Lib/importlib/metadata/_text.py \
  $(BUILD_DIR)/windows/x64/Lib/importlib/metadata/diagnose.py \
  $(BUILD_DIR)/windows/x64/Lib/importlib/readers.py \
  $(BUILD_DIR)/windows/x64/Lib/importlib/resources/__init__.py \
  $(BUILD_DIR)/windows/x64/Lib/importlib/resources/_adapters.py \
  $(BUILD_DIR)/windows/x64/Lib/importlib/resources/_common.py \
  $(BUILD_DIR)/windows/x64/Lib/importlib/resources/_functional.py \
  $(BUILD_DIR)/windows/x64/Lib/importlib/resources/_itertools.py \
  $(BUILD_DIR)/windows/x64/Lib/importlib/resources/abc.py \
  $(BUILD_DIR)/windows/x64/Lib/importlib/resources/readers.py \
  $(BUILD_DIR)/windows/x64/Lib/importlib/resources/simple.py \
  $(BUILD_DIR)/windows/x64/Lib/importlib/simple.py \
  $(BUILD_DIR)/windows/x64/Lib/importlib/util.py \
  $(BUILD_DIR)/windows/x64/Lib/inspect.py \
  $(BUILD_DIR)/windows/x64/Lib/io.py \
  $(BUILD_DIR)/windows/x64/Lib/ipaddress.py \
  $(BUILD_DIR)/windows/x64/Lib/json/__init__.py \
  $(BUILD_DIR)/windows/x64/Lib/json/__main__.py \
  $(BUILD_DIR)/windows/x64/Lib/json/decoder.py \
  $(BUILD_DIR)/windows/x64/Lib/json/encoder.py \
  $(BUILD_DIR)/windows/x64/Lib/json/scanner.py \
  $(BUILD_DIR)/windows/x64/Lib/json/tool.py \
  $(BUILD_DIR)/windows/x64/Lib/keyword.py \
  $(BUILD_DIR)/windows/x64/Lib/linecache.py \
  $(BUILD_DIR)/windows/x64/Lib/locale.py \
  $(BUILD_DIR)/windows/x64/Lib/logging/__init__.py \
  $(BUILD_DIR)/windows/x64/Lib/logging/config.py \
  $(BUILD_DIR)/windows/x64/Lib/logging/handlers.py \
  $(BUILD_DIR)/windows/x64/Lib/lzma.py \
  $(BUILD_DIR)/windows/x64/Lib/mailbox.py \
  $(BUILD_DIR)/windows/x64/Lib/mimetypes.py \
  $(BUILD_DIR)/windows/x64/Lib/modulefinder.py \
  $(BUILD_DIR)/windows/x64/Lib/netrc.py \
  $(BUILD_DIR)/windows/x64/Lib/ntpath.py \
  $(BUILD_DIR)/windows/x64/Lib/nturl2path.py \
  $(BUILD_DIR)/windows/x64/Lib/numbers.py \
  $(BUILD_DIR)/windows/x64/Lib/opcode.py \
  $(BUILD_DIR)/windows/x64/Lib/operator.py \
  $(BUILD_DIR)/windows/x64/Lib/optparse.py \
  $(BUILD_DIR)/windows/x64/Lib/os.py \
  $(BUILD_DIR)/windows/x64/Lib/pathlib/__init__.py \
  $(BUILD_DIR)/windows/x64/Lib/pathlib/_local.py \
  $(BUILD_DIR)/windows/x64/Lib/pathlib/_os.py \
  $(BUILD_DIR)/windows/x64/Lib/pathlib/types.py \
  $(BUILD_DIR)/windows/x64/Lib/pdb.py \
  $(BUILD_DIR)/windows/x64/Lib/pickle.py \
  $(BUILD_DIR)/windows/x64/Lib/pickletools.py \
  $(BUILD_DIR)/windows/x64/Lib/pkgutil.py \
  $(BUILD_DIR)/windows/x64/Lib/platform.py \
  $(BUILD_DIR)/windows/x64/Lib/plistlib.py \
  $(BUILD_DIR)/windows/x64/Lib/poplib.py \
  $(BUILD_DIR)/windows/x64/Lib/posixpath.py \
  $(BUILD_DIR)/windows/x64/Lib/pprint.py \
  $(BUILD_DIR)/windows/x64/Lib/profile.py \
  $(BUILD_DIR)/windows/x64/Lib/pstats.py \
  $(BUILD_DIR)/windows/x64/Lib/pty.py \
  $(BUILD_DIR)/windows/x64/Lib/py_compile.py \
  $(BUILD_DIR)/windows/x64/Lib/pyclbr.py \
  $(BUILD_DIR)/windows/x64/Lib/pydoc.py \
  $(BUILD_DIR)/windows/x64/Lib/queue.py \
  $(BUILD_DIR)/windows/x64/Lib/quopri.py \
  $(BUILD_DIR)/windows/x64/Lib/random.py \
  $(BUILD_DIR)/windows/x64/Lib/re/__init__.py \
  $(BUILD_DIR)/windows/x64/Lib/re/_casefix.py \
  $(BUILD_DIR)/windows/x64/Lib/re/_compiler.py \
  $(BUILD_DIR)/windows/x64/Lib/re/_constants.py \
  $(BUILD_DIR)/windows/x64/Lib/re/_parser.py \
  $(BUILD_DIR)/windows/x64/Lib/reprlib.py \
  $(BUILD_DIR)/windows/x64/Lib/rlcompleter.py \
  $(BUILD_DIR)/windows/x64/Lib/runpy.py \
  $(BUILD_DIR)/windows/x64/Lib/sched.py \
  $(BUILD_DIR)/windows/x64/Lib/secrets.py \
  $(BUILD_DIR)/windows/x64/Lib/selectors.py \
  $(BUILD_DIR)/windows/x64/Lib/shelve.py \
  $(BUILD_DIR)/windows/x64/Lib/shlex.py \
  $(BUILD_DIR)/windows/x64/Lib/shutil.py \
  $(BUILD_DIR)/windows/x64/Lib/signal.py \
  $(BUILD_DIR)/windows/x64/Lib/site.py \
  $(BUILD_DIR)/windows/x64/Lib/smtplib.py \
  $(BUILD_DIR)/windows/x64/Lib/socket.py \
  $(BUILD_DIR)/windows/x64/Lib/socketserver.py \
  $(BUILD_DIR)/windows/x64/Lib/sqlite3/__init__.py \
  $(BUILD_DIR)/windows/x64/Lib/sqlite3/__main__.py \
  $(BUILD_DIR)/windows/x64/Lib/sqlite3/dbapi2.py \
  $(BUILD_DIR)/windows/x64/Lib/sqlite3/dump.py \
  $(BUILD_DIR)/windows/x64/Lib/sre_compile.py \
  $(BUILD_DIR)/windows/x64/Lib/sre_constants.py \
  $(BUILD_DIR)/windows/x64/Lib/sre_parse.py \
  $(BUILD_DIR)/windows/x64/Lib/ssl.py \
  $(BUILD_DIR)/windows/x64/Lib/stat.py \
  $(BUILD_DIR)/windows/x64/Lib/statistics.py \
  $(BUILD_DIR)/windows/x64/Lib/string/__init__.py \
  $(BUILD_DIR)/windows/x64/Lib/string/templatelib.py \
  $(BUILD_DIR)/windows/x64/Lib/stringprep.py \
  $(BUILD_DIR)/windows/x64/Lib/struct.py \
  $(BUILD_DIR)/windows/x64/Lib/subprocess.py \
  $(BUILD_DIR)/windows/x64/Lib/symtable.py \
  $(BUILD_DIR)/windows/x64/Lib/sysconfig/__init__.py \
  $(BUILD_DIR)/windows/x64/Lib/sysconfig/__main__.py \
  $(BUILD_DIR)/windows/x64/Lib/tabnanny.py \
  $(BUILD_DIR)/windows/x64/Lib/tarfile.py \
  $(BUILD_DIR)/windows/x64/Lib/tempfile.py \
  $(BUILD_DIR)/windows/x64/Lib/textwrap.py \
  $(BUILD_DIR)/windows/x64/Lib/this.py \
  $(BUILD_DIR)/windows/x64/Lib/threading.py \
  $(BUILD_DIR)/windows/x64/Lib/timeit.py \
  $(BUILD_DIR)/windows/x64/Lib/token.py \
  $(BUILD_DIR)/windows/x64/Lib/tokenize.py \
  $(BUILD_DIR)/windows/x64/Lib/tomllib/__init__.py \
  $(BUILD_DIR)/windows/x64/Lib/tomllib/_parser.py \
  $(BUILD_DIR)/windows/x64/Lib/tomllib/_re.py \
  $(BUILD_DIR)/windows/x64/Lib/tomllib/_types.py \
  $(BUILD_DIR)/windows/x64/Lib/trace.py \
  $(BUILD_DIR)/windows/x64/Lib/traceback.py \
  $(BUILD_DIR)/windows/x64/Lib/tracemalloc.py \
  $(BUILD_DIR)/windows/x64/Lib/tty.py \
  $(BUILD_DIR)/windows/x64/Lib/types.py \
  $(BUILD_DIR)/windows/x64/Lib/typing.py \
  $(BUILD_DIR)/windows/x64/Lib/urllib/__init__.py \
  $(BUILD_DIR)/windows/x64/Lib/urllib/error.py \
  $(BUILD_DIR)/windows/x64/Lib/urllib/parse.py \
  $(BUILD_DIR)/windows/x64/Lib/urllib/request.py \
  $(BUILD_DIR)/windows/x64/Lib/urllib/response.py \
  $(BUILD_DIR)/windows/x64/Lib/urllib/robotparser.py \
  $(BUILD_DIR)/windows/x64/Lib/uuid.py \
  $(BUILD_DIR)/windows/x64/Lib/warnings.py \
  $(BUILD_DIR)/windows/x64/Lib/wave.py \
  $(BUILD_DIR)/windows/x64/Lib/weakref.py \
  $(BUILD_DIR)/windows/x64/Lib/webbrowser.py \
  $(BUILD_DIR)/windows/x64/Lib/xml/__init__.py \
  $(BUILD_DIR)/windows/x64/Lib/xml/dom/NodeFilter.py \
  $(BUILD_DIR)/windows/x64/Lib/xml/dom/__init__.py \
  $(BUILD_DIR)/windows/x64/Lib/xml/dom/domreg.py \
  $(BUILD_DIR)/windows/x64/Lib/xml/dom/expatbuilder.py \
  $(BUILD_DIR)/windows/x64/Lib/xml/dom/minicompat.py \
  $(BUILD_DIR)/windows/x64/Lib/xml/dom/minidom.py \
  $(BUILD_DIR)/windows/x64/Lib/xml/dom/pulldom.py \
  $(BUILD_DIR)/windows/x64/Lib/xml/dom/xmlbuilder.py \
  $(BUILD_DIR)/windows/x64/Lib/xml/etree/ElementInclude.py \
  $(BUILD_DIR)/windows/x64/Lib/xml/etree/ElementPath.py \
  $(BUILD_DIR)/windows/x64/Lib/xml/etree/ElementTree.py \
  $(BUILD_DIR)/windows/x64/Lib/xml/etree/__init__.py \
  $(BUILD_DIR)/windows/x64/Lib/xml/etree/cElementTree.py \
  $(BUILD_DIR)/windows/x64/Lib/xml/parsers/__init__.py \
  $(BUILD_DIR)/windows/x64/Lib/xml/parsers/expat.py \
  $(BUILD_DIR)/windows/x64/Lib/xml/sax/__init__.py \
  $(BUILD_DIR)/windows/x64/Lib/xml/sax/_exceptions.py \
  $(BUILD_DIR)/windows/x64/Lib/xml/sax/expatreader.py \
  $(BUILD_DIR)/windows/x64/Lib/xml/sax/handler.py \
  $(BUILD_DIR)/windows/x64/Lib/xml/sax/saxutils.py \
  $(BUILD_DIR)/windows/x64/Lib/xml/sax/xmlreader.py \
  $(BUILD_DIR)/windows/x64/Lib/xmlrpc/__init__.py \
  $(BUILD_DIR)/windows/x64/Lib/xmlrpc/client.py \
  $(BUILD_DIR)/windows/x64/Lib/xmlrpc/server.py \
  $(BUILD_DIR)/windows/x64/Lib/zipapp.py \
  $(BUILD_DIR)/windows/x64/Lib/zipfile/__init__.py \
  $(BUILD_DIR)/windows/x64/Lib/zipfile/__main__.py \
  $(BUILD_DIR)/windows/x64/Lib/zipfile/_path/__init__.py \
  $(BUILD_DIR)/windows/x64/Lib/zipfile/_path/glob.py \
  $(BUILD_DIR)/windows/x64/Lib/zipimport.py \
  $(BUILD_DIR)/windows/x64/Lib/zoneinfo/__init__.py \
  $(BUILD_DIR)/windows/x64/Lib/zoneinfo/_common.py \
  $(BUILD_DIR)/windows/x64/Lib/zoneinfo/_tzpath.py \
  $(BUILD_DIR)/windows/x64/Lib/zoneinfo/_zoneinfo.py

SCRIPT_TARGETS_SO_PRIVATE_WIN_X64 = \
  

SCRIPT_TARGETS_ZSTDDICT_PRIVATE_WIN_X64 = \
  

# Rule to copy src asset scripts to dst.
# (and make non-writable so I'm less likely to accidentally edit them there)
$(SCRIPT_TARGETS_PY_PRIVATE_WIN_X64) : ../../.efrocachemap
	@cd ../.. && $(PCOMMANDBATCHFROMROOT) efrocache_get src/assets/$@


SCRIPT_TARGETS_PY_PRIVATE_WIN_ARM64 = \
  $(BUILD_DIR)/windows/ARM64/Lib/__future__.py \
  $(BUILD_DIR)/windows/ARM64/Lib/__hello__.py \
  $(BUILD_DIR)/windows/ARM64/Lib/_aix_support.py \
  $(BUILD_DIR)/windows/ARM64/Lib/_android_support.py \
  $(BUILD_DIR)/windows/ARM64/Lib/_apple_support.py \
  $(BUILD_DIR)/windows/ARM64/Lib/_ast_unparse.py \
  $(BUILD_DIR)/windows/ARM64/Lib/_collections_abc.py \
  $(BUILD_DIR)/windows/ARM64/Lib/_colorize.py \
  $(BUILD_DIR)/windows/ARM64/Lib/_compat_pickle.py \
  $(BUILD_DIR)/windows/ARM64/Lib/_ios_support.py \
  $(BUILD_DIR)/windows/ARM64/Lib/_markupbase.py \
  $(BUILD_DIR)/windows/ARM64/Lib/_opcode_metadata.py \
  $(BUILD_DIR)/windows/ARM64/Lib/_osx_support.py \
  $(BUILD_DIR)/windows/ARM64/Lib/_py_abc.py \
  $(BUILD_DIR)/windows/ARM64/Lib/_py_warnings.py \
  $(BUILD_DIR)/windows/ARM64/Lib/_pydatetime.py \
  $(BUILD_DIR)/windows/ARM64/Lib/_pydecimal.py \
  $(BUILD_DIR)/windows/ARM64/Lib/_pyio.py \
  $(BUILD_DIR)/windows/ARM64/Lib/_pylong.py \
  $(BUILD_DIR)/windows/ARM64/Lib/_pyrepl/__init__.py \
  $(BUILD_DIR)/windows/ARM64/Lib/_pyrepl/__main__.py \
  $(BUILD_DIR)/windows/ARM64/Lib/_pyrepl/_module_completer.py \
  $(BUILD_DIR)/windows/ARM64/Lib/_pyrepl/_threading_handler.py \
  $(BUILD_DIR)/windows/ARM64/Lib/_pyrepl/base_eventqueue.py \
  $(BUILD_DIR)/windows/ARM64/Lib/_pyrepl/commands.py \
  $(BUILD_DIR)/windows/ARM64/Lib/_pyrepl/completing_reader.py \
  $(BUILD_DIR)/windows/ARM64/Lib/_pyrepl/console.py \
  $(BUILD_DIR)/windows/ARM64/Lib/_pyrepl/fancy_termios.py \
  $(BUILD_DIR)/windows/ARM64/Lib/_pyrepl/historical_reader.py \
  $(BUILD_DIR)/windows/ARM64/Lib/_pyrepl/input.py \
  $(BUILD_DIR)/windows/ARM64/Lib/_pyrepl/keymap.py \
  $(BUILD_DIR)/windows/ARM64/Lib/_pyrepl/main.py \
  $(BUILD_DIR)/windows/ARM64/Lib/_pyrepl/pager.py \
  $(BUILD_DIR)/windows/ARM64/Lib/_pyrepl/reader.py \
  $(BUILD_DIR)/windows/ARM64/Lib/_pyrepl/readline.py \
  $(BUILD_DIR)/windows/ARM64/Lib/_pyrepl/simple_interact.py \
  $(BUILD_DIR)/windows/ARM64/Lib/_pyrepl/terminfo.py \
  $(BUILD_DIR)/windows/ARM64/Lib/_pyrepl/trace.py \
  $(BUILD_DIR)/windows/ARM64/Lib/_pyrepl/types.py \
  $(BUILD_DIR)/windows/ARM64/Lib/_pyrepl/unix_console.py \
  $(BUILD_DIR)/windows/ARM64/Lib/_pyrepl/unix_eventqueue.py \
  $(BUILD_DIR)/windows/ARM64/Lib/_pyrepl/utils.py \
  $(BUILD_DIR)/windows/ARM64/Lib/_pyrepl/windows_console.py \
  $(BUILD_DIR)/windows/ARM64/Lib/_pyrepl/windows_eventqueue.py \
  $(BUILD_DIR)/windows/ARM64/Lib/_sitebuiltins.py \
  $(BUILD_DIR)/windows/ARM64/Lib/_strptime.py \
  $(BUILD_DIR)/windows/ARM64/Lib/_threading_local.py \
  $(BUILD_DIR)/windows/ARM64/Lib/_weakrefset.py \
  $(BUILD_DIR)/windows/ARM64/Lib/abc.py \
  $(BUILD_DIR)/windows/ARM64/Lib/annotationlib.py \
  $(BUILD_DIR)/windows/ARM64/Lib/antigravity.py \
  $(BUILD_DIR)/windows/ARM64/Lib/argparse.py \
  $(BUILD_DIR)/windows/ARM64/Lib/ast.py \
  $(BUILD_DIR)/windows/ARM64/Lib/asyncio/__init__.py \
  $(BUILD_DIR)/windows/ARM64/Lib/asyncio/__main__.py \
  $(BUILD_DIR)/windows/ARM64/Lib/asyncio/base_events.py \
  $(BUILD_DIR)/windows/ARM64/Lib/asyncio/base_futures.py \
  $(BUILD_DIR)/windows/ARM64/Lib/asyncio/base_subprocess.py \
  $(BUILD_DIR)/windows/ARM64/Lib/asyncio/base_tasks.py \
  $(BUILD_DIR)/windows/ARM64/Lib/asyncio/constants.py \
  $(BUILD_DIR)/windows/ARM64/Lib/asyncio/coroutines.py \
  $(BUILD_DIR)/windows/ARM64/Lib/asyncio/events.py \
  $(BUILD_DIR)/windows/ARM64/Lib/asyncio/exceptions.py \
  $(BUILD_DIR)/windows/ARM64/Lib/asyncio/format_helpers.py \
  $(BUILD_DIR)/windows/ARM64/Lib/asyncio/futures.py \
  $(BUILD_DIR)/windows/ARM64/Lib/asyncio/graph.py \
  $(BUILD_DIR)/windows/ARM64/Lib/asyncio/locks.py \
  $(BUILD_DIR)/windows/ARM64/Lib/asyncio/log.py \
  $(BUILD_DIR)/windows/ARM64/Lib/asyncio/mixins.py \
  $(BUILD_DIR)/windows/ARM64/Lib/asyncio/proactor_events.py \
  $(BUILD_DIR)/windows/ARM64/Lib/asyncio/protocols.py \
  $(BUILD_DIR)/windows/ARM64/Lib/asyncio/queues.py \
  $(BUILD_DIR)/windows/ARM64/Lib/asyncio/runners.py \
  $(BUILD_DIR)/windows/ARM64/Lib/asyncio/selector_events.py \
  $(BUILD_DIR)/windows/ARM64/Lib/asyncio/sslproto.py \
  $(BUILD_DIR)/windows/ARM64/Lib/asyncio/staggered.py \
  $(BUILD_DIR)/windows/ARM64/Lib/asyncio/streams.py \
  $(BUILD_DIR)/windows/ARM64/Lib/asyncio/subprocess.py \
  $(BUILD_DIR)/windows/ARM64/Lib/asyncio/taskgroups.py \
  $(BUILD_DIR)/windows/ARM64/Lib/asyncio/tasks.py \
  $(BUILD_DIR)/windows/ARM64/Lib/asyncio/threads.py \
  $(BUILD_DIR)/windows/ARM64/Lib/asyncio/timeouts.py \
  $(BUILD_DIR)/windows/ARM64/Lib/asyncio/tools.py \
  $(BUILD_DIR)/windows/ARM64/Lib/asyncio/transports.py \
  $(BUILD_DIR)/windows/ARM64/Lib/asyncio/trsock.py \
  $(BUILD_DIR)/windows/ARM64/Lib/asyncio/unix_events.py \
  $(BUILD_DIR)/windows/ARM64/Lib/asyncio/windows_events.py \
  $(BUILD_DIR)/windows/ARM64/Lib/asyncio/windows_utils.py \
  $(BUILD_DIR)/windows/ARM64/Lib/base64.py \
  $(BUILD_DIR)/windows/ARM64/Lib/bdb.py \
  $(BUILD_DIR)/windows/ARM64/Lib/bisect.py \
  $(BUILD_DIR)/windows/ARM64/Lib/bz2.py \
  $(BUILD_DIR)/windows/ARM64/Lib/cProfile.py \
  $(BUILD_DIR)/windows/ARM64/Lib/calendar.py \
  $(BUILD_DIR)/windows/ARM64/Lib/cmd.py \
  $(BUILD_DIR)/windows/ARM64/Lib/code.py \
  $(BUILD_DIR)/windows/ARM64/Lib/codecs.py \
  $(BUILD_DIR)/windows/ARM64/Lib/codeop.py \
  $(BUILD_DIR)/windows/ARM64/Lib/collections/__init__.py \
  $(BUILD_DIR)/windows/ARM64/Lib/colorsys.py \
  $(BUILD_DIR)/windows/ARM64/Lib/compileall.py \
  $(BUILD_DIR)/windows/ARM64/Lib/compression/__init__.py \
  $(BUILD_DIR)/windows/ARM64/Lib/compression/_common/__init__.py \
  $(BUILD_DIR)/windows/ARM64/Lib/compression/_common/_streams.py \
  $(BUILD_DIR)/windows/ARM64/Lib/compression/bz2.py \
  $(BUILD_DIR)/windows/ARM64/Lib/compression/gzip.py \
  $(BUILD_DIR)/windows/ARM64/Lib/compression/lzma.py \
  $(BUILD_DIR)/windows/ARM64/Lib/compression/zlib.py \
  $(BUILD_DIR)/windows/ARM64/Lib/compression/zstd/__init__.py \
  $(BUILD_DIR)/windows/ARM64/Lib/compression/zstd/_zstdfile.py \
  $(BUILD_DIR)/windows/ARM64/Lib/concurrent/__init__.py \
  $(BUILD_DIR)/windows/ARM64/Lib/concurrent/futures/__init__.py \
  $(BUILD_DIR)/windows/ARM64/Lib/concurrent/futures/_base.py \
  $(BUILD_DIR)/windows/ARM64/Lib/concurrent/futures/interpreter.py \
  $(BUILD_DIR)/windows/ARM64/Lib/concurrent/futures/process.py \
  $(BUILD_DIR)/windows/ARM64/Lib/concurrent/futures/thread.py \
  $(BUILD_DIR)/windows/ARM64/Lib/concurrent/interpreters/__init__.py \
  $(BUILD_DIR)/windows/ARM64/Lib/concurrent/interpreters/_crossinterp.py \
  $(BUILD_DIR)/windows/ARM64/Lib/concurrent/interpreters/_queues.py \
  $(BUILD_DIR)/windows/ARM64/Lib/configparser.py \
  $(BUILD_DIR)/windows/ARM64/Lib/contextlib.py \
  $(BUILD_DIR)/windows/ARM64/Lib/contextvars.py \
  $(BUILD_DIR)/windows/ARM64/Lib/copy.py \
  $(BUILD_DIR)/windows/ARM64/Lib/copyreg.py \
  $(BUILD_DIR)/windows/ARM64/Lib/csv.py \
  $(BUILD_DIR)/windows/ARM64/Lib/ctypes/__init__.py \
  $(BUILD_DIR)/windows/ARM64/Lib/ctypes/_aix.py \
  $(BUILD_DIR)/windows/ARM64/Lib/ctypes/_endian.py \
  $(BUILD_DIR)/windows/ARM64/Lib/ctypes/_layout.py \
  $(BUILD_DIR)/windows/ARM64/Lib/ctypes/macholib/__init__.py \
  $(BUILD_DIR)/windows/ARM64/Lib/ctypes/macholib/dyld.py \
  $(BUILD_DIR)/windows/ARM64/Lib/ctypes/macholib/dylib.py \
  $(BUILD_DIR)/windows/ARM64/Lib/ctypes/macholib/framework.py \
  $(BUILD_DIR)/windows/ARM64/Lib/ctypes/util.py \
  $(BUILD_DIR)/windows/ARM64/Lib/ctypes/wintypes.py \
  $(BUILD_DIR)/windows/ARM64/Lib/curses/__init__.py \
  $(BUILD_DIR)/windows/ARM64/Lib/curses/ascii.py \
  $(BUILD_DIR)/windows/ARM64/Lib/curses/has_key.py \
  $(BUILD_DIR)/windows/ARM64/Lib/curses/panel.py \
  $(BUILD_DIR)/windows/ARM64/Lib/curses/textpad.py \
  $(BUILD_DIR)/windows/ARM64/Lib/dataclasses.py \
  $(BUILD_DIR)/windows/ARM64/Lib/datetime.py \
  $(BUILD_DIR)/windows/ARM64/Lib/decimal.py \
  $(BUILD_DIR)/windows/ARM64/Lib/difflib.py \
  $(BUILD_DIR)/windows/ARM64/Lib/dis.py \
  $(BUILD_DIR)/windows/ARM64/Lib/doctest.py \
  $(BUILD_DIR)/windows/ARM64/Lib/email/__init__.py \
  $(BUILD_DIR)/windows/ARM64/Lib/email/_encoded_words.py \
  $(BUILD_DIR)/windows/ARM64/Lib/email/_header_value_parser.py \
  $(BUILD_DIR)/windows/ARM64/Lib/email/_parseaddr.py \
  $(BUILD_DIR)/windows/ARM64/Lib/email/_policybase.py \
  $(BUILD_DIR)/windows/ARM64/Lib/email/base64mime.py \
  $(BUILD_DIR)/windows/ARM64/Lib/email/charset.py \
  $(BUILD_DIR)/windows/ARM64/Lib/email/contentmanager.py \
  $(BUILD_DIR)/windows/ARM64/Lib/email/encoders.py \
  $(BUILD_DIR)/windows/ARM64/Lib/email/errors.py \
  $(BUILD_DIR)/windows/ARM64/Lib/email/feedparser.py \
  $(BUILD_DIR)/windows/ARM64/Lib/email/generator.py \
  $(BUILD_DIR)/windows/ARM64/Lib/email/header.py \
  $(BUILD_DIR)/windows/ARM64/Lib/email/headerregistry.py \
  $(BUILD_DIR)/windows/ARM64/Lib/email/iterators.py \
  $(BUILD_DIR)/windows/ARM64/Lib/email/message.py \
  $(BUILD_DIR)/windows/ARM64/Lib/email/mime/__init__.py \
  $(BUILD_DIR)/windows/ARM64/Lib/email/mime/application.py \
  $(BUILD_DIR)/windows/ARM64/Lib/email/mime/audio.py \
  $(BUILD_DIR)/windows/ARM64/Lib/email/mime/base.py \
  $(BUILD_DIR)/windows/ARM64/Lib/email/mime/image.py \
  $(BUILD_DIR)/windows/ARM64/Lib/email/mime/message.py \
  $(BUILD_DIR)/windows/ARM64/Lib/email/mime/multipart.py \
  $(BUILD_DIR)/windows/ARM64/Lib/email/mime/nonmultipart.py \
  $(BUILD_DIR)/windows/ARM64/Lib/email/mime/text.py \
  $(BUILD_DIR)/windows/ARM64/Lib/email/parser.py \
  $(BUILD_DIR)/windows/ARM64/Lib/email/policy.py \
  $(BUILD_DIR)/windows/ARM64/Lib/email/quoprimime.py \
  $(BUILD_DIR)/windows/ARM64/Lib/email/utils.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/__init__.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/_win_cp_codecs.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/aliases.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/ascii.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/base64_codec.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/big5.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/big5hkscs.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/bz2_codec.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/charmap.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/cp037.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/cp1006.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/cp1026.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/cp1125.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/cp1140.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/cp1250.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/cp1251.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/cp1252.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/cp1253.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/cp1254.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/cp1255.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/cp1256.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/cp1257.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/cp1258.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/cp273.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/cp424.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/cp437.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/cp500.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/cp720.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/cp737.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/cp775.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/cp850.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/cp852.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/cp855.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/cp856.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/cp857.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/cp858.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/cp860.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/cp861.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/cp862.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/cp863.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/cp864.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/cp865.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/cp866.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/cp869.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/cp874.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/cp875.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/cp932.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/cp949.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/cp950.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/euc_jis_2004.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/euc_jisx0213.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/euc_jp.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/euc_kr.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/gb18030.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/gb2312.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/gbk.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/hex_codec.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/hp_roman8.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/hz.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/idna.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/iso2022_jp.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/iso2022_jp_1.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/iso2022_jp_2.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/iso2022_jp_2004.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/iso2022_jp_3.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/iso2022_jp_ext.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/iso2022_kr.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/iso8859_1.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/iso8859_10.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/iso8859_11.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/iso8859_13.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/iso8859_14.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/iso8859_15.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/iso8859_16.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/iso8859_2.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/iso8859_3.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/iso8859_4.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/iso8859_5.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/iso8859_6.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/iso8859_7.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/iso8859_8.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/iso8859_9.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/johab.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/koi8_r.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/koi8_t.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/koi8_u.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/kz1048.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/latin_1.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/mac_arabic.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/mac_croatian.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/mac_cyrillic.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/mac_farsi.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/mac_greek.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/mac_iceland.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/mac_latin2.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/mac_roman.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/mac_romanian.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/mac_turkish.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/mbcs.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/oem.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/palmos.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/ptcp154.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/punycode.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/quopri_codec.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/raw_unicode_escape.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/rot_13.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/shift_jis.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/shift_jis_2004.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/shift_jisx0213.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/tis_620.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/undefined.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/unicode_escape.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/utf_16.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/utf_16_be.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/utf_16_le.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/utf_32.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/utf_32_be.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/utf_32_le.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/utf_7.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/utf_8.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/utf_8_sig.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/uu_codec.py \
  $(BUILD_DIR)/windows/ARM64/Lib/encodings/zlib_codec.py \
  $(BUILD_DIR)/windows/ARM64/Lib/enum.py \
  $(BUILD_DIR)/windows/ARM64/Lib/filecmp.py \
  $(BUILD_DIR)/windows/ARM64/Lib/fileinput.py \
  $(BUILD_DIR)/windows/ARM64/Lib/fnmatch.py \
  $(BUILD_DIR)/windows/ARM64/Lib/fractions.py \
  $(BUILD_DIR)/windows/ARM64/Lib/ftplib.py \
  $(BUILD_DIR)/windows/ARM64/Lib/functools.py \
  $(BUILD_DIR)/windows/ARM64/Lib/genericpath.py \
  $(BUILD_DIR)/windows/ARM64/Lib/getopt.py \
  $(BUILD_DIR)/windows/ARM64/Lib/getpass.py \
  $(BUILD_DIR)/windows/ARM64/Lib/gettext.py \
  $(BUILD_DIR)/windows/ARM64/Lib/glob.py \
  $(BUILD_DIR)/windows/ARM64/Lib/graphlib.py \
  $(BUILD_DIR)/windows/ARM64/Lib/gzip.py \
  $(BUILD_DIR)/windows/ARM64/Lib/hashlib.py \
  $(BUILD_DIR)/windows/ARM64/Lib/heapq.py \
  $(BUILD_DIR)/windows/ARM64/Lib/hmac.py \
  $(BUILD_DIR)/windows/ARM64/Lib/html/__init__.py \
  $(BUILD_DIR)/windows/ARM64/Lib/html/entities.py \
  $(BUILD_DIR)/windows/ARM64/Lib/html/parser.py \
  $(BUILD_DIR)/windows/ARM64/Lib/http/__init__.py \
  $(BUILD_DIR)/windows/ARM64/Lib/http/client.py \
  $(BUILD_DIR)/windows/ARM64/Lib/http/cookiejar.py \
  $(BUILD_DIR)/windows/ARM64/Lib/http/cookies.py \
  $(BUILD_DIR)/windows/ARM64/Lib/http/server.py \
  $(BUILD_DIR)/windows/ARM64/Lib/importlib/__init__.py \
  $(BUILD_DIR)/windows/ARM64/Lib/importlib/_abc.py \
  $(BUILD_DIR)/windows/ARM64/Lib/importlib/_bootstrap.py \
  $(BUILD_DIR)/windows/ARM64/Lib/importlib/_bootstrap_external.py \
  $(BUILD_DIR)/windows/ARM64/Lib/importlib/abc.py \
  $(BUILD_DIR)/windows/ARM64/Lib/importlib/machinery.py \
  $(BUILD_DIR)/windows/ARM64/Lib/importlib/metadata/__init__.py \
  $(BUILD_DIR)/windows/ARM64/Lib/importlib/metadata/_adapters.py \
  $(BUILD_DIR)/windows/ARM64/Lib/importlib/metadata/_collections.py \
  $(BUILD_DIR)/windows/ARM64/Lib/importlib/metadata/_functools.py \
  $(BUILD_DIR)/windows/ARM64/Lib/importlib/metadata/_itertools.py \
  $(BUILD_DIR)/windows/ARM64/Lib/importlib/metadata/_meta.py \
  $(BUILD_DIR)/windows/ARM64/Lib/importlib/metadata/_text.py \
  $(BUILD_DIR)/windows/ARM64/Lib/importlib/metadata/diagnose.py \
  $(BUILD_DIR)/windows/ARM64/Lib/importlib/readers.py \
  $(BUILD_DIR)/windows/ARM64/Lib/importlib/resources/__init__.py \
  $(BUILD_DIR)/windows/ARM64/Lib/importlib/resources/_adapters.py \
  $(BUILD_DIR)/windows/ARM64/Lib/importlib/resources/_common.py \
  $(BUILD_DIR)/windows/ARM64/Lib/importlib/resources/_functional.py \
  $(BUILD_DIR)/windows/ARM64/Lib/importlib/resources/_itertools.py \
  $(BUILD_DIR)/windows/ARM64/Lib/importlib/resources/abc.py \
  $(BUILD_DIR)/windows/ARM64/Lib/importlib/resources/readers.py \
  $(BUILD_DIR)/windows/ARM64/Lib/importlib/resources/simple.py \
  $(BUILD_DIR)/windows/ARM64/Lib/importlib/simple.py \
  $(BUILD_DIR)/windows/ARM64/Lib/importlib/util.py \
  $(BUILD_DIR)/windows/ARM64/Lib/inspect.py \
  $(BUILD_DIR)/windows/ARM64/Lib/io.py \
  $(BUILD_DIR)/windows/ARM64/Lib/ipaddress.py \
  $(BUILD_DIR)/windows/ARM64/Lib/json/__init__.py \
  $(BUILD_DIR)/windows/ARM64/Lib/json/__main__.py \
  $(BUILD_DIR)/windows/ARM64/Lib/json/decoder.py \
  $(BUILD_DIR)/windows/ARM64/Lib/json/encoder.py \
  $(BUILD_DIR)/windows/ARM64/Lib/json/scanner.py \
  $(BUILD_DIR)/windows/ARM64/Lib/json/tool.py \
  $(BUILD_DIR)/windows/ARM64/Lib/keyword.py \
  $(BUILD_DIR)/windows/ARM64/Lib/linecache.py \
  $(BUILD_DIR)/windows/ARM64/Lib/locale.py \
  $(BUILD_DIR)/windows/ARM64/Lib/logging/__init__.py \
  $(BUILD_DIR)/windows/ARM64/Lib/logging/config.py \
  $(BUILD_DIR)/windows/ARM64/Lib/logging/handlers.py \
  $(BUILD_DIR)/windows/ARM64/Lib/lzma.py \
  $(BUILD_DIR)/windows/ARM64/Lib/mailbox.py \
  $(BUILD_DIR)/windows/ARM64/Lib/mimetypes.py \
  $(BUILD_DIR)/windows/ARM64/Lib/modulefinder.py \
  $(BUILD_DIR)/windows/ARM64/Lib/netrc.py \
  $(BUILD_DIR)/windows/ARM64/Lib/ntpath.py \
  $(BUILD_DIR)/windows/ARM64/Lib/nturl2path.py \
  $(BUILD_DIR)/windows/ARM64/Lib/numbers.py \
  $(BUILD_DIR)/windows/ARM64/Lib/opcode.py \
  $(BUILD_DIR)/windows/ARM64/Lib/operator.py \
  $(BUILD_DIR)/windows/ARM64/Lib/optparse.py \
  $(BUILD_DIR)/windows/ARM64/Lib/os.py \
  $(BUILD_DIR)/windows/ARM64/Lib/pathlib/__init__.py \
  $(BUILD_DIR)/windows/ARM64/Lib/pathlib/_local.py \
  $(BUILD_DIR)/windows/ARM64/Lib/pathlib/_os.py \
  $(BUILD_DIR)/windows/ARM64/Lib/pathlib/types.py \
  $(BUILD_DIR)/windows/ARM64/Lib/pdb.py \
  $(BUILD_DIR)/windows/ARM64/Lib/pickle.py \
  $(BUILD_DIR)/windows/ARM64/Lib/pickletools.py \
  $(BUILD_DIR)/windows/ARM64/Lib/pkgutil.py \
  $(BUILD_DIR)/windows/ARM64/Lib/platform.py \
  $(BUILD_DIR)/windows/ARM64/Lib/plistlib.py \
  $(BUILD_DIR)/windows/ARM64/Lib/poplib.py \
  $(BUILD_DIR)/windows/ARM64/Lib/posixpath.py \
  $(BUILD_DIR)/windows/ARM64/Lib/pprint.py \
  $(BUILD_DIR)/windows/ARM64/Lib/profile.py \
  $(BUILD_DIR)/windows/ARM64/Lib/pstats.py \
  $(BUILD_DIR)/windows/ARM64/Lib/pty.py \
  $(BUILD_DIR)/windows/ARM64/Lib/py_compile.py \
  $(BUILD_DIR)/windows/ARM64/Lib/pyclbr.py \
  $(BUILD_DIR)/windows/ARM64/Lib/pydoc.py \
  $(BUILD_DIR)/windows/ARM64/Lib/queue.py \
  $(BUILD_DIR)/windows/ARM64/Lib/quopri.py \
  $(BUILD_DIR)/windows/ARM64/Lib/random.py \
  $(BUILD_DIR)/windows/ARM64/Lib/re/__init__.py \
  $(BUILD_DIR)/windows/ARM64/Lib/re/_casefix.py \
  $(BUILD_DIR)/windows/ARM64/Lib/re/_compiler.py \
  $(BUILD_DIR)/windows/ARM64/Lib/re/_constants.py \
  $(BUILD_DIR)/windows/ARM64/Lib/re/_parser.py \
  $(BUILD_DIR)/windows/ARM64/Lib/reprlib.py \
  $(BUILD_DIR)/windows/ARM64/Lib/rlcompleter.py \
  $(BUILD_DIR)/windows/ARM64/Lib/runpy.py \
  $(BUILD_DIR)/windows/ARM64/Lib/sched.py \
  $(BUILD_DIR)/windows/ARM64/Lib/secrets.py \
  $(BUILD_DIR)/windows/ARM64/Lib/selectors.py \
  $(BUILD_DIR)/windows/ARM64/Lib/shelve.py \
  $(BUILD_DIR)/windows/ARM64/Lib/shlex.py \
  $(BUILD_DIR)/windows/ARM64/Lib/shutil.py \
  $(BUILD_DIR)/windows/ARM64/Lib/signal.py \
  $(BUILD_DIR)/windows/ARM64/Lib/site.py \
  $(BUILD_DIR)/windows/ARM64/Lib/smtplib.py \
  $(BUILD_DIR)/windows/ARM64/Lib/socket.py \
  $(BUILD_DIR)/windows/ARM64/Lib/socketserver.py \
  $(BUILD_DIR)/windows/ARM64/Lib/sqlite3/__init__.py \
  $(BUILD_DIR)/windows/ARM64/Lib/sqlite3/__main__.py \
  $(BUILD_DIR)/windows/ARM64/Lib/sqlite3/dbapi2.py \
  $(BUILD_DIR)/windows/ARM64/Lib/sqlite3/dump.py \
  $(BUILD_DIR)/windows/ARM64/Lib/sre_compile.py \
  $(BUILD_DIR)/windows/ARM64/Lib/sre_constants.py \
  $(BUILD_DIR)/windows/ARM64/Lib/sre_parse.py \
  $(BUILD_DIR)/windows/ARM64/Lib/ssl.py \
  $(BUILD_DIR)/windows/ARM64/Lib/stat.py \
  $(BUILD_DIR)/windows/ARM64/Lib/statistics.py \
  $(BUILD_DIR)/windows/ARM64/Lib/string/__init__.py \
  $(BUILD_DIR)/windows/ARM64/Lib/string/templatelib.py \
  $(BUILD_DIR)/windows/ARM64/Lib/stringprep.py \
  $(BUILD_DIR)/windows/ARM64/Lib/struct.py \
  $(BUILD_DIR)/windows/ARM64/Lib/subprocess.py \
  $(BUILD_DIR)/windows/ARM64/Lib/symtable.py \
  $(BUILD_DIR)/windows/ARM64/Lib/sysconfig/__init__.py \
  $(BUILD_DIR)/windows/ARM64/Lib/sysconfig/__main__.py \
  $(BUILD_DIR)/windows/ARM64/Lib/tabnanny.py \
  $(BUILD_DIR)/windows/ARM64/Lib/tarfile.py \
  $(BUILD_DIR)/windows/ARM64/Lib/tempfile.py \
  $(BUILD_DIR)/windows/ARM64/Lib/textwrap.py \
  $(BUILD_DIR)/windows/ARM64/Lib/this.py \
  $(BUILD_DIR)/windows/ARM64/Lib/threading.py \
  $(BUILD_DIR)/windows/ARM64/Lib/timeit.py \
  $(BUILD_DIR)/windows/ARM64/Lib/token.py \
  $(BUILD_DIR)/windows/ARM64/Lib/tokenize.py \
  $(BUILD_DIR)/windows/ARM64/Lib/tomllib/__init__.py \
  $(BUILD_DIR)/windows/ARM64/Lib/tomllib/_parser.py \
  $(BUILD_DIR)/windows/ARM64/Lib/tomllib/_re.py \
  $(BUILD_DIR)/windows/ARM64/Lib/tomllib/_types.py \
  $(BUILD_DIR)/windows/ARM64/Lib/trace.py \
  $(BUILD_DIR)/windows/ARM64/Lib/traceback.py \
  $(BUILD_DIR)/windows/ARM64/Lib/tracemalloc.py \
  $(BUILD_DIR)/windows/ARM64/Lib/tty.py \
  $(BUILD_DIR)/windows/ARM64/Lib/types.py \
  $(BUILD_DIR)/windows/ARM64/Lib/typing.py \
  $(BUILD_DIR)/windows/ARM64/Lib/urllib/__init__.py \
  $(BUILD_DIR)/windows/ARM64/Lib/urllib/error.py \
  $(BUILD_DIR)/windows/ARM64/Lib/urllib/parse.py \
  $(BUILD_DIR)/windows/ARM64/Lib/urllib/request.py \
  $(BUILD_DIR)/windows/ARM64/Lib/urllib/response.py \
  $(BUILD_DIR)/windows/ARM64/Lib/urllib/robotparser.py \
  $(BUILD_DIR)/windows/ARM64/Lib/uuid.py \
  $(BUILD_DIR)/windows/ARM64/Lib/warnings.py \
  $(BUILD_DIR)/windows/ARM64/Lib/wave.py \
  $(BUILD_DIR)/windows/ARM64/Lib/weakref.py \
  $(BUILD_DIR)/windows/ARM64/Lib/webbrowser.py \
  $(BUILD_DIR)/windows/ARM64/Lib/xml/__init__.py \
  $(BUILD_DIR)/windows/ARM64/Lib/xml/dom/NodeFilter.py \
  $(BUILD_DIR)/windows/ARM64/Lib/xml/dom/__init__.py \
  $(BUILD_DIR)/windows/ARM64/Lib/xml/dom/domreg.py \
  $(BUILD_DIR)/windows/ARM64/Lib/xml/dom/expatbuilder.py \
  $(BUILD_DIR)/windows/ARM64/Lib/xml/dom/minicompat.py \
  $(BUILD_DIR)/windows/ARM64/Lib/xml/dom/minidom.py \
  $(BUILD_DIR)/windows/ARM64/Lib/xml/dom/pulldom.py \
  $(BUILD_DIR)/windows/ARM64/Lib/xml/dom/xmlbuilder.py \
  $(BUILD_DIR)/windows/ARM64/Lib/xml/etree/ElementInclude.py \
  $(BUILD_DIR)/windows/ARM64/Lib/xml/etree/ElementPath.py \
  $(BUILD_DIR)/windows/ARM64/Lib/xml/etree/ElementTree.py \
  $(BUILD_DIR)/windows/ARM64/Lib/xml/etree/__init__.py \
  $(BUILD_DIR)/windows/ARM64/Lib/xml/etree/cElementTree.py \
  $(BUILD_DIR)/windows/ARM64/Lib/xml/parsers/__init__.py \
  $(BUILD_DIR)/windows/ARM64/Lib/xml/parsers/expat.py \
  $(BUILD_DIR)/windows/ARM64/Lib/xml/sax/__init__.py \
  $(BUILD_DIR)/windows/ARM64/Lib/xml/sax/_exceptions.py \
  $(BUILD_DIR)/windows/ARM64/Lib/xml/sax/expatreader.py \
  $(BUILD_DIR)/windows/ARM64/Lib/xml/sax/handler.py \
  $(BUILD_DIR)/windows/ARM64/Lib/xml/sax/saxutils.py \
  $(BUILD_DIR)/windows/ARM64/Lib/xml/sax/xmlreader.py \
  $(BUILD_DIR)/windows/ARM64/Lib/xmlrpc/__init__.py \
  $(BUILD_DIR)/windows/ARM64/Lib/xmlrpc/client.py \
  $(BUILD_DIR)/windows/ARM64/Lib/xmlrpc/server.py \
  $(BUILD_DIR)/windows/ARM64/Lib/zipapp.py \
  $(BUILD_DIR)/windows/ARM64/Lib/zipfile/__init__.py \
  $(BUILD_DIR)/windows/ARM64/Lib/zipfile/__main__.py \
  $(BUILD_DIR)/windows/ARM64/Lib/zipfile/_path/__init__.py \
  $(BUILD_DIR)/windows/ARM64/Lib/zipfile/_path/glob.py \
  $(BUILD_DIR)/windows/ARM64/Lib/zipimport.py \
  $(BUILD_DIR)/windows/ARM64/Lib/zoneinfo/__init__.py \
  $(BUILD_DIR)/windows/ARM64/Lib/zoneinfo/_common.py \
  $(BUILD_DIR)/windows/ARM64/Lib/zoneinfo/_tzpath.py \
  $(BUILD_DIR)/windows/ARM64/Lib/zoneinfo/_zoneinfo.py

SCRIPT_TARGETS_SO_PRIVATE_WIN_ARM64 = \
  

SCRIPT_TARGETS_ZSTDDICT_PRIVATE_WIN_ARM64 = \
  

# Rule to copy src asset scripts to dst.
# (and make non-writable so I'm less likely to accidentally edit them there)
$(SCRIPT_TARGETS_PY_PRIVATE_WIN_ARM64) : ../../.efrocachemap
	@cd ../.. && $(PCOMMANDBATCHFROMROOT) efrocache_get src/assets/$@


FONT_TARGETS = \
  $(BUILD_DIR)/ba_data/fonts/fontSmall0.fdata \
  $(BUILD_DIR)/ba_data/fonts/fontSmall1.fdata \
  $(BUILD_DIR)/ba_data/fonts/fontSmall2.fdata \
  $(BUILD_DIR)/ba_data/fonts/fontSmall3.fdata \
  $(BUILD_DIR)/ba_data/fonts/fontSmall4.fdata \
  $(BUILD_DIR)/ba_data/fonts/fontSmall5.fdata \
  $(BUILD_DIR)/ba_data/fonts/fontSmall6.fdata \
  $(BUILD_DIR)/ba_data/fonts/fontSmall7.fdata

PEM_TARGETS = \
  $(BUILD_DIR)/ba_data/python-site-packages/certifi/cacert.pem

DATA_TARGETS = \
  

EXTRAS_TARGETS_WIN_WIN32 = \
  $(BUILD_DIR)/windows/Win32/DLLs/_asyncio.pyd \
  $(BUILD_DIR)/windows/Win32/DLLs/_asyncio_d.pyd \
  $(BUILD_DIR)/windows/Win32/DLLs/_bz2.pyd \
  $(BUILD_DIR)/windows/Win32/DLLs/_bz2_d.pyd \
  $(BUILD_DIR)/windows/Win32/DLLs/_ctypes.pyd \
  $(BUILD_DIR)/windows/Win32/DLLs/_ctypes_d.pyd \
  $(BUILD_DIR)/windows/Win32/DLLs/_decimal.pyd \
  $(BUILD_DIR)/windows/Win32/DLLs/_decimal_d.pyd \
  $(BUILD_DIR)/windows/Win32/DLLs/_elementtree.pyd \
  $(BUILD_DIR)/windows/Win32/DLLs/_elementtree_d.pyd \
  $(BUILD_DIR)/windows/Win32/DLLs/_hashlib.pyd \
  $(BUILD_DIR)/windows/Win32/DLLs/_hashlib_d.pyd \
  $(BUILD_DIR)/windows/Win32/DLLs/_lzma.pyd \
  $(BUILD_DIR)/windows/Win32/DLLs/_lzma_d.pyd \
  $(BUILD_DIR)/windows/Win32/DLLs/_multiprocessing.pyd \
  $(BUILD_DIR)/windows/Win32/DLLs/_multiprocessing_d.pyd \
  $(BUILD_DIR)/windows/Win32/DLLs/_overlapped.pyd \
  $(BUILD_DIR)/windows/Win32/DLLs/_overlapped_d.pyd \
  $(BUILD_DIR)/windows/Win32/DLLs/_queue.pyd \
  $(BUILD_DIR)/windows/Win32/DLLs/_queue_d.pyd \
  $(BUILD_DIR)/windows/Win32/DLLs/_remote_debugging.pyd \
  $(BUILD_DIR)/windows/Win32/DLLs/_remote_debugging_d.pyd \
  $(BUILD_DIR)/windows/Win32/DLLs/_socket.pyd \
  $(BUILD_DIR)/windows/Win32/DLLs/_socket_d.pyd \
  $(BUILD_DIR)/windows/Win32/DLLs/_sqlite3.pyd \
  $(BUILD_DIR)/windows/Win32/DLLs/_sqlite3_d.pyd \
  $(BUILD_DIR)/windows/Win32/DLLs/_ssl.pyd \
  $(BUILD_DIR)/windows/Win32/DLLs/_ssl_d.pyd \
  $(BUILD_DIR)/windows/Win32/DLLs/_uuid.pyd \
  $(BUILD_DIR)/windows/Win32/DLLs/_uuid_d.pyd \
  $(BUILD_DIR)/windows/Win32/DLLs/_wmi.pyd \
  $(BUILD_DIR)/windows/Win32/DLLs/_wmi_d.pyd \
  $(BUILD_DIR)/windows/Win32/DLLs/_zoneinfo.pyd \
  $(BUILD_DIR)/windows/Win32/DLLs/_zoneinfo_d.pyd \
  $(BUILD_DIR)/windows/Win32/DLLs/_zstd.pyd \
  $(BUILD_DIR)/windows/Win32/DLLs/_zstd_d.pyd \
  $(BUILD_DIR)/windows/Win32/DLLs/libcrypto-3.dll \
  $(BUILD_DIR)/windows/Win32/DLLs/libffi-8.dll \
  $(BUILD_DIR)/windows/Win32/DLLs/libssl-3.dll \
  $(BUILD_DIR)/windows/Win32/DLLs/pyexpat.pyd \
  $(BUILD_DIR)/windows/Win32/DLLs/pyexpat_d.pyd \
  $(BUILD_DIR)/windows/Win32/DLLs/python_lib.cat \
  $(BUILD_DIR)/windows/Win32/DLLs/select.pyd \
  $(BUILD_DIR)/windows/Win32/DLLs/select_d.pyd \
  $(BUILD_DIR)/windows/Win32/DLLs/sqlite3.dll \
  $(BUILD_DIR)/windows/Win32/DLLs/sqlite3_d.dll \
  $(BUILD_DIR)/windows/Win32/DLLs/unicodedata.pyd \
  $(BUILD_DIR)/windows/Win32/DLLs/unicodedata_d.pyd \
  $(BUILD_DIR)/windows/Win32/DLLs/winsound.pyd \
  $(BUILD_DIR)/windows/Win32/DLLs/winsound_d.pyd \
  $(BUILD_DIR)/windows/Win32/Lib/ctypes/macholib/README.ctypes \
  $(BUILD_DIR)/windows/Win32/Lib/ctypes/macholib/fetch_macholib \
  $(BUILD_DIR)/windows/Win32/Lib/ctypes/macholib/fetch_macholib.bat \
  $(BUILD_DIR)/windows/Win32/Lib/email/architecture.rst \
  $(BUILD_DIR)/windows/Win32/OpenAL32.dll \
  $(BUILD_DIR)/windows/Win32/SDL3.dll \
  $(BUILD_DIR)/windows/Win32/libEGL.dll \
  $(BUILD_DIR)/windows/Win32/libGLESv2.dll \
  $(BUILD_DIR)/windows/Win32/libvorbis.dll \
  $(BUILD_DIR)/windows/Win32/libvorbisfile.dll \
  $(BUILD_DIR)/windows/Win32/ogg.dll \
  $(BUILD_DIR)/windows/Win32/python.exe \
  $(BUILD_DIR)/windows/Win32/python314.dll \
  $(BUILD_DIR)/windows/Win32/python314_d.dll \
  $(BUILD_DIR)/windows/Win32/python_d.exe \
  $(BUILD_DIR)/windows/Win32/pythonw.exe \
  $(BUILD_DIR)/windows/Win32/pythonw_d.exe \
  $(BUILD_DIR)/windows/Win32/vc_redist.x86.exe \
  $(BUILD_DIR)/windows/Win32/zlib1.dll

# Rule to copy src extras to build.
$(EXTRAS_TARGETS_WIN_WIN32) : ../../.efrocachemap
	@cd ../.. && $(PCOMMANDBATCHFROMROOT) efrocache_get src/assets/$@


EXTRAS_TARGETS_WIN_X64 = \
  $(BUILD_DIR)/windows/x64/DLLs/_asyncio.pyd \
  $(BUILD_DIR)/windows/x64/DLLs/_asyncio_d.pyd \
  $(BUILD_DIR)/windows/x64/DLLs/_bz2.pyd \
  $(BUILD_DIR)/windows/x64/DLLs/_bz2_d.pyd \
  $(BUILD_DIR)/windows/x64/DLLs/_ctypes.pyd \
  $(BUILD_DIR)/windows/x64/DLLs/_ctypes_d.pyd \
  $(BUILD_DIR)/windows/x64/DLLs/_decimal.pyd \
  $(BUILD_DIR)/windows/x64/DLLs/_decimal_d.pyd \
  $(BUILD_DIR)/windows/x64/DLLs/_elementtree.pyd \
  $(BUILD_DIR)/windows/x64/DLLs/_elementtree_d.pyd \
  $(BUILD_DIR)/windows/x64/DLLs/_hashlib.pyd \
  $(BUILD_DIR)/windows/x64/DLLs/_hashlib_d.pyd \
  $(BUILD_DIR)/windows/x64/DLLs/_lzma.pyd \
  $(BUILD_DIR)/windows/x64/DLLs/_lzma_d.pyd \
  $(BUILD_DIR)/windows/x64/DLLs/_multiprocessing.pyd \
  $(BUILD_DIR)/windows/x64/DLLs/_multiprocessing_d.pyd \
  $(BUILD_DIR)/windows/x64/DLLs/_overlapped.pyd \
  $(BUILD_DIR)/windows/x64/DLLs/_overlapped_d.pyd \
  $(BUILD_DIR)/windows/x64/DLLs/_queue.pyd \
  $(BUILD_DIR)/windows/x64/DLLs/_queue_d.pyd \
  $(BUILD_DIR)/windows/x64/DLLs/_remote_debugging.pyd \
  $(BUILD_DIR)/windows/x64/DLLs/_remote_debugging_d.pyd \
  $(BUILD_DIR)/windows/x64/DLLs/_socket.pyd \
  $(BUILD_DIR)/windows/x64/DLLs/_socket_d.pyd \
  $(BUILD_DIR)/windows/x64/DLLs/_sqlite3.pyd \
  $(BUILD_DIR)/windows/x64/DLLs/_sqlite3_d.pyd \
  $(BUILD_DIR)/windows/x64/DLLs/_ssl.pyd \
  $(BUILD_DIR)/windows/x64/DLLs/_ssl_d.pyd \
  $(BUILD_DIR)/windows/x64/DLLs/_uuid.pyd \
  $(BUILD_DIR)/windows/x64/DLLs/_uuid_d.pyd \
  $(BUILD_DIR)/windows/x64/DLLs/_wmi.pyd \
  $(BUILD_DIR)/windows/x64/DLLs/_wmi_d.pyd \
  $(BUILD_DIR)/windows/x64/DLLs/_zoneinfo.pyd \
  $(BUILD_DIR)/windows/x64/DLLs/_zoneinfo_d.pyd \
  $(BUILD_DIR)/windows/x64/DLLs/_zstd.pyd \
  $(BUILD_DIR)/windows/x64/DLLs/_zstd_d.pyd \
  $(BUILD_DIR)/windows/x64/DLLs/libcrypto-3.dll \
  $(BUILD_DIR)/windows/x64/DLLs/libffi-8.dll \
  $(BUILD_DIR)/windows/x64/DLLs/libssl-3.dll \
  $(BUILD_DIR)/windows/x64/DLLs/pyexpat.pyd \
  $(BUILD_DIR)/windows/x64/DLLs/pyexpat_d.pyd \
  $(BUILD_DIR)/windows/x64/DLLs/python_lib.cat \
  $(BUILD_DIR)/windows/x64/DLLs/select.pyd \
  $(BUILD_DIR)/windows/x64/DLLs/select_d.pyd \
  $(BUILD_DIR)/windows/x64/DLLs/sqlite3.dll \
  $(BUILD_DIR)/windows/x64/DLLs/sqlite3_d.dll \
  $(BUILD_DIR)/windows/x64/DLLs/unicodedata.pyd \
  $(BUILD_DIR)/windows/x64/DLLs/unicodedata_d.pyd \
  $(BUILD_DIR)/windows/x64/DLLs/winsound.pyd \
  $(BUILD_DIR)/windows/x64/DLLs/winsound_d.pyd \
  $(BUILD_DIR)/windows/x64/Lib/ctypes/macholib/README.ctypes \
  $(BUILD_DIR)/windows/x64/Lib/ctypes/macholib/fetch_macholib \
  $(BUILD_DIR)/windows/x64/Lib/ctypes/macholib/fetch_macholib.bat \
  $(BUILD_DIR)/windows/x64/Lib/email/architecture.rst \
  $(BUILD_DIR)/windows/x64/OpenAL32.dll \
  $(BUILD_DIR)/windows/x64/SDL3.dll \
  $(BUILD_DIR)/windows/x64/libEGL.dll \
  $(BUILD_DIR)/windows/x64/libGLESv2.dll \
  $(BUILD_DIR)/windows/x64/libvorbis.dll \
  $(BUILD_DIR)/windows/x64/libvorbisfile.dll \
  $(BUILD_DIR)/windows/x64/ogg.dll \
  $(BUILD_DIR)/windows/x64/python.exe \
  $(BUILD_DIR)/windows/x64/python314.dll \
  $(BUILD_DIR)/windows/x64/python314_d.dll \
  $(BUILD_DIR)/windows/x64/python_d.exe \
  $(BUILD_DIR)/windows/x64/pythonw.exe \
  $(BUILD_DIR)/windows/x64/pythonw_d.exe \
  $(BUILD_DIR)/windows/x64/vc_redist.x64.exe \
  $(BUILD_DIR)/windows/x64/zlib1.dll

# Rule to copy src extras to build.
$(EXTRAS_TARGETS_WIN_X64) : ../../.efrocachemap
	@cd ../.. && $(PCOMMANDBATCHFROMROOT) efrocache_get src/assets/$@


EXTRAS_TARGETS_WIN_ARM64 = \
  $(BUILD_DIR)/windows/ARM64/DLLs/_asyncio.pyd \
  $(BUILD_DIR)/windows/ARM64/DLLs/_asyncio_d.pyd \
  $(BUILD_DIR)/windows/ARM64/DLLs/_bz2.pyd \
  $(BUILD_DIR)/windows/ARM64/DLLs/_bz2_d.pyd \
  $(BUILD_DIR)/windows/ARM64/DLLs/_ctypes.pyd \
  $(BUILD_DIR)/windows/ARM64/DLLs/_ctypes_d.pyd \
  $(BUILD_DIR)/windows/ARM64/DLLs/_decimal.pyd \
  $(BUILD_DIR)/windows/ARM64/DLLs/_decimal_d.pyd \
  $(BUILD_DIR)/windows/ARM64/DLLs/_elementtree.pyd \
  $(BUILD_DIR)/windows/ARM64/DLLs/_elementtree_d.pyd \
  $(BUILD_DIR)/windows/ARM64/DLLs/_hashlib.pyd \
  $(BUILD_DIR)/windows/ARM64/DLLs/_hashlib_d.pyd \
  $(BUILD_DIR)/windows/ARM64/DLLs/_lzma.pyd \
  $(BUILD_DIR)/windows/ARM64/DLLs/_lzma_d.pyd \
  $(BUILD_DIR)/windows/ARM64/DLLs/_multiprocessing.pyd \
  $(BUILD_DIR)/windows/ARM64/DLLs/_multiprocessing_d.pyd \
  $(BUILD_DIR)/windows/ARM64/DLLs/_overlapped.pyd \
  $(BUILD_DIR)/windows/ARM64/DLLs/_overlapped_d.pyd \
  $(BUILD_DIR)/windows/ARM64/DLLs/_queue.pyd \
  $(BUILD_DIR)/windows/ARM64/DLLs/_queue_d.pyd \
  $(BUILD_DIR)/windows/ARM64/DLLs/_remote_debugging.pyd \
  $(BUILD_DIR)/windows/ARM64/DLLs/_remote_debugging_d.pyd \
  $(BUILD_DIR)/windows/ARM64/DLLs/_socket.pyd \
  $(BUILD_DIR)/windows/ARM64/DLLs/_socket_d.pyd \
  $(BUILD_DIR)/windows/ARM64/DLLs/_sqlite3.pyd \
  $(BUILD_DIR)/windows/ARM64/DLLs/_sqlite3_d.pyd \
  $(BUILD_DIR)/windows/ARM64/DLLs/_ssl.pyd \
  $(BUILD_DIR)/windows/ARM64/DLLs/_ssl_d.pyd \
  $(BUILD_DIR)/windows/ARM64/DLLs/_uuid.pyd \
  $(BUILD_DIR)/windows/ARM64/DLLs/_uuid_d.pyd \
  $(BUILD_DIR)/windows/ARM64/DLLs/_wmi.pyd \
  $(BUILD_DIR)/windows/ARM64/DLLs/_wmi_d.pyd \
  $(BUILD_DIR)/windows/ARM64/DLLs/_zoneinfo.pyd \
  $(BUILD_DIR)/windows/ARM64/DLLs/_zoneinfo_d.pyd \
  $(BUILD_DIR)/windows/ARM64/DLLs/_zstd.pyd \
  $(BUILD_DIR)/windows/ARM64/DLLs/_zstd_d.pyd \
  $(BUILD_DIR)/windows/ARM64/DLLs/libcrypto-3-arm64.dll \
  $(BUILD_DIR)/windows/ARM64/DLLs/libffi-8.dll \
  $(BUILD_DIR)/windows/ARM64/DLLs/libssl-3-arm64.dll \
  $(BUILD_DIR)/windows/ARM64/DLLs/pyexpat.pyd \
  $(BUILD_DIR)/windows/ARM64/DLLs/pyexpat_d.pyd \
  $(BUILD_DIR)/windows/ARM64/DLLs/python_lib.cat \
  $(BUILD_DIR)/windows/ARM64/DLLs/select.pyd \
  $(BUILD_DIR)/windows/ARM64/DLLs/select_d.pyd \
  $(BUILD_DIR)/windows/ARM64/DLLs/sqlite3.dll \
  $(BUILD_DIR)/windows/ARM64/DLLs/sqlite3_d.dll \
  $(BUILD_DIR)/windows/ARM64/DLLs/unicodedata.pyd \
  $(BUILD_DIR)/windows/ARM64/DLLs/unicodedata_d.pyd \
  $(BUILD_DIR)/windows/ARM64/DLLs/winsound.pyd \
  $(BUILD_DIR)/windows/ARM64/DLLs/winsound_d.pyd \
  $(BUILD_DIR)/windows/ARM64/Lib/ctypes/macholib/README.ctypes \
  $(BUILD_DIR)/windows/ARM64/Lib/ctypes/macholib/fetch_macholib \
  $(BUILD_DIR)/windows/ARM64/Lib/ctypes/macholib/fetch_macholib.bat \
  $(BUILD_DIR)/windows/ARM64/Lib/email/architecture.rst \
  $(BUILD_DIR)/windows/ARM64/SDL3.dll \
  $(BUILD_DIR)/windows/ARM64/libEGL.dll \
  $(BUILD_DIR)/windows/ARM64/libGLESv2.dll \
  $(BUILD_DIR)/windows/ARM64/python.exe \
  $(BUILD_DIR)/windows/ARM64/python314.dll \
  $(BUILD_DIR)/windows/ARM64/python314_d.dll \
  $(BUILD_DIR)/windows/ARM64/python_d.exe \
  $(BUILD_DIR)/windows/ARM64/pythonw.exe \
  $(BUILD_DIR)/windows/ARM64/pythonw_d.exe \
  $(BUILD_DIR)/windows/ARM64/vc_redist.arm64.exe

# Rule to copy src extras to build.
$(EXTRAS_TARGETS_WIN_ARM64) : ../../.efrocachemap
	@cd ../.. && $(PCOMMANDBATCHFROMROOT) efrocache_get src/assets/$@

# __AUTOGENERATED_PRIVATE_END__

$(BUILD_DIR)/%.fdata : ../../.efrocachemap
	@cd ../.. && $(PCOMMANDBATCHFROMROOT) efrocache_get src/assets/$@

$(BUILD_DIR)/%.pem : ../../.efrocachemap
	@cd ../.. && $(PCOMMANDBATCHFROMROOT) efrocache_get src/assets/$@

data: $(DATA_TARGETS)

data-clean:
	rm -rf $(BUILD_DIR)/ba_data/data

fonts: $(FONT_TARGETS)
fonts-clean:
	rm -rf $(BUILD_DIR)/ba_data/fonts

# Script targets needed per-platform (may overlap)
SCRIPT_TARGETS_CMAKE =
SCRIPT_TARGETS_SERVER =
SCRIPT_TARGETS_WIN_WIN32 = $(SCRIPT_TARGETS_PY_PRIVATE_WIN_WIN32)
SCRIPT_TARGETS_WIN_X64 = $(SCRIPT_TARGETS_PY_PRIVATE_WIN_X64)
# Note: ARM64 is staged for future windows-arm64 builds; nothing
# aggregates it into gui/server builds yet.
SCRIPT_TARGETS_WIN_ARM64 = $(SCRIPT_TARGETS_PY_PRIVATE_WIN_ARM64)

# Explicit on-demand staging of the windows ARM64 asset set. (Must
# live after the generated lists it consumes so prereqs expand
# non-empty at rule-parse time.)
.PHONY: win-arm64-staging
win-arm64-staging: $(ASSET_TARGETS_WIN_ARM64)
SCRIPT_TARGETS_MAC = $(SCRIPT_TARGETS_PY_PRIVATE_APPLE_MAC) \
 $(SCRIPT_TARGETS_SO_PRIVATE_APPLE_MAC)
SCRIPT_TARGETS_IOS = $(SCRIPT_TARGETS_PY_PRIVATE_APPLE_MAC) \
 $(SCRIPT_TARGETS_SO_PRIVATE_APPLE_MAC)
SCRIPT_TARGETS_ANDROID = $(SCRIPT_TARGETS_PY_PRIVATE_ANDROID)

# Script targets needed by all platforms.
SCRIPT_TARGETS_COMMON = $(SCRIPT_TARGETS_PY_PUBLIC) \
 $(SCRIPT_TARGETS_PY_PUBLIC_TOOLS) \
 $(SCRIPT_TARGETS_ZSTDDICT_PUBLIC_TOOLS) \
 $(SCRIPT_TARGETS_PY_PRIVATE_COMMON) \
 $(PEM_TARGETS)

# Build scripts for a specific platform.
scripts-cmake: $(SCRIPT_TARGETS_CMAKE) $(SCRIPT_TARGETS_COMMON)
scripts-server: $(SCRIPT_TARGETS_SERVER) $(SCRIPT_TARGETS_COMMON)
scripts-win-Win32: $(SCRIPT_TARGETS_WIN_WIN32) $(SCRIPT_TARGETS_COMMON)
scripts-win-x64: $(SCRIPT_TARGETS_WIN_X64) $(SCRIPT_TARGETS_COMMON)
scripts-mac: $(SCRIPT_TARGETS_MAC) $(SCRIPT_TARGETS_COMMON)
scripts-ios: $(SCRIPT_TARGETS_IOS) $(SCRIPT_TARGETS_COMMON)
scripts-android: $(SCRIPT_TARGETS_ANDROID) $(SCRIPT_TARGETS_COMMON)

# Build scripts for all platforms
scripts: scripts-cmake scripts-win-Win32 scripts-win-x64 scripts-mac \
  scripts-ios scripts-android
scripts-clean:
	rm -rf $(BUILD_DIR)/ba_data/python $(BUILD_DIR)/ba_data/python-site-packages \
  $(BUILD_DIR)/pylib-android $(BUILD_DIR)/pylib-apple \
  $(BUILD_DIR)/windows/Win32/Lib $(BUILD_DIR)/windows/x64/Lib

# Build all required assets for a specific platform.
assets-cmake: $(ASSET_TARGETS_CMAKE) $(ASSET_TARGETS_COMMON_GUI)
assets-server: $(ASSET_TARGETS_SERVER) $(ASSET_TARGETS_COMMON_SERVER)
assets-win-Win32: $(ASSET_TARGETS_WIN_WIN32) $(ASSET_TARGETS_COMMON_GUI)
assets-win-x64: $(ASSET_TARGETS_WIN_X64) $(ASSET_TARGETS_COMMON_GUI)
assets-win-server-Win32: $(ASSET_TARGETS_WIN_SERVER_WIN32) \
      $(ASSET_TARGETS_COMMON_SERVER)
assets-win-server-x64: $(ASSET_TARGETS_WIN_SERVER_X64) \
      $(ASSET_TARGETS_COMMON_SERVER)
assets-mac: $(ASSET_TARGETS_MAC) $(ASSET_TARGETS_COMMON_GUI)
assets-ios: $(ASSET_TARGETS_IOS) $(ASSET_TARGETS_COMMON_GUI)
assets-android: $(ASSET_TARGETS_ANDROID) $(ASSET_TARGETS_COMMON_GUI)

# Build all assets for all platforms.
assets: assets-cmake assets-win-x64
clean:
	@rm -rf $(BUILD_DIR)

# Asset bundle (construct-mode minimum).
#
# The build path consumes a fully-resolved apverid from
# projectconfig's ``"assets"`` field. Dev resolution + pin
# writeback lives exclusively in ``tools/pcommand assetpins``;
# the build itself just reads projectconfig and asks bacloud for
# the manifest. Cloud-talking happens here as a build-time
# on-demand pull (the only build-flow surface that may touch
# the network — and only to fetch blob/manifest content for the
# already-resolved apverid). Steady-state builds hit the cache
# and exit fast via ``asset_bundle_build``'s apverid-match
# early-out.
# These rules are keyed on projectconfig mtime, so a build with an
# unchanged pin normally skips them. When iterating on the server-side
# asset pipeline, a recipe/pipeline-version bump changes the built
# output WITHOUT changing the apverid, so the rule would otherwise stay
# satisfied and bake stale bundled assets. BA_ASSET_BUNDLE_FORCE_REFETCH=1
# adds a phony prereq so these always re-run; asset_bundle_build then also
# bypasses its own apverid early-out (see pcommands2.py) so it actually
# re-fetches the manifest + blobs from the server.
_ASSET_BUNDLE_FORCE :=
ifeq ($(BA_ASSET_BUNDLE_FORCE_REFETCH),1)
  _ASSET_BUNDLE_FORCE := _asset_bundle_force
endif

.PHONY: _asset_bundle_force
_asset_bundle_force:

$(PROJ_DIR)/.cache/asset_bundle/gui-minimal/manifest.json: \
      $(PROJ_DIR)/pconfig/projectconfig.json $(_ASSET_BUNDLE_FORCE)
	@$(PCOMMAND) asset_bundle_build gui-minimal

$(PROJ_DIR)/.cache/asset_bundle/headless-minimal/manifest.json: \
      $(PROJ_DIR)/pconfig/projectconfig.json $(_ASSET_BUNDLE_FORCE)
	@$(PCOMMAND) asset_bundle_build headless-minimal

# These targets don't correspond to actual files; make sure make knows that.
.PHONY: cmake win mac ios android fonts fonts-clean data data-clean			\
        scripts scripts-clean assets assets-cmake assets-server				\
        assets-win-Win32 assets-win-x64 win-server-Win32 win-server-x64		\
        assets-win-server-Win32 assets-win-server-x64 assets-mac				\
        assets-ios assets-android clean
