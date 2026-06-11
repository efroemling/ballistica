// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/assets/asset_name_compat.h"

#include <string>
#include <unordered_map>
#include <utility>

#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging.h"

namespace ballistica::base {

struct Row_ {
  const char* legacy;
  const char* package_key;
  const char* logical_path;
};

// One row per migrated asset. The legacy side is frozen (old peers and
// replays speak these names forever); the (package_key, logical_path)
// side must track package contents - update_project --check verifies
// it against the wrapper modules. Add a row here whenever an asset
// migrates out of the legacy tree.
static const Row_ kRows[] = {
    {"achievementBoxer", "stdassets", "textures/achievement_boxer"},
    {"achievementCrossHair", "stdassets", "textures/achievement_cross_hair"},
    {"achievementDualWielding", "stdassets",
     "textures/achievement_dual_wielding"},
    {"achievementEmpty", "stdassets", "textures/achievement_empty"},
    {"achievementFlawlessVictory", "stdassets",
     "textures/achievement_flawless_victory"},
    {"achievementFootballShutout", "stdassets",
     "textures/achievement_football_shutout"},
    {"achievementFootballVictory", "stdassets",
     "textures/achievement_football_victory"},
    {"achievementFreeLoader", "stdassets", "textures/achievement_free_loader"},
    {"achievementGotTheMoves", "stdassets",
     "textures/achievement_got_the_moves"},
    {"achievementInControl", "stdassets", "textures/achievement_in_control"},
    {"achievementMedalLarge", "stdassets", "textures/achievement_medal_large"},
    {"achievementMedalMedium", "stdassets",
     "textures/achievement_medal_medium"},
    {"achievementMedalSmall", "stdassets", "textures/achievement_medal_small"},
    {"achievementMine", "stdassets", "textures/achievement_mine"},
    {"achievementOffYouGo", "stdassets", "textures/achievement_off_you_go"},
    {"achievementOnslaught", "stdassets", "textures/achievement_onslaught"},
    {"achievementOutline", "stdassets", "textures/achievement_outline"},
    {"achievementRunaround", "stdassets", "textures/achievement_runaround"},
    {"achievementSharingIsCaring", "stdassets",
     "textures/achievement_sharing_is_caring"},
    {"achievementStayinAlive", "stdassets",
     "textures/achievement_stayin_alive"},
    {"achievementSuperPunch", "stdassets", "textures/achievement_super_punch"},
    {"achievementTNT", "stdassets", "textures/achievement_tnt"},
    {"achievementTeamPlayer", "stdassets", "textures/achievement_team_player"},
    {"achievementWall", "stdassets", "textures/achievement_wall"},
    {"achievementsIcon", "stdassets", "textures/achievements_icon"},
    {"actionButtons", "builtinassets", "textures/action_buttons"},
    {"actionHeroColor", "stdassets", "textures/action_hero_color"},
    {"actionHeroColorMask", "stdassets", "textures/action_hero_color_mask"},
    {"actionHeroIcon", "stdassets", "textures/action_hero_icon"},
    {"actionHeroIconColorMask", "stdassets",
     "textures/action_hero_icon_color_mask"},
    {"advancedIcon", "stdassets", "textures/advanced_icon"},
    {"agentColor", "stdassets", "textures/agent_color"},
    {"agentColorMask", "stdassets", "textures/agent_color_mask"},
    {"agentIcon", "stdassets", "textures/agent_icon"},
    {"agentIconColorMask", "stdassets", "textures/agent_icon_color_mask"},
    {"aliColor", "stdassets", "textures/ali_color"},
    {"aliColorMask", "stdassets", "textures/ali_color_mask"},
    {"aliIcon", "stdassets", "textures/ali_icon"},
    {"aliIconColorMask", "stdassets", "textures/ali_icon_color_mask"},
    {"aliSplash", "stdassets", "textures/ali_splash"},
    {"alienColor", "stdassets", "textures/alien_color"},
    {"alienColorMask", "stdassets", "textures/alien_color_mask"},
    {"alienIcon", "stdassets", "textures/alien_icon"},
    {"alienIconColorMask", "stdassets", "textures/alien_icon_color_mask"},
    {"alwaysLandBGColor", "stdassets", "textures/always_land_bgcolor"},
    {"alwaysLandLevelColor", "stdassets", "textures/always_land_level_color"},
    {"alwaysLandPreview", "stdassets", "textures/always_land_preview"},
    {"analogStick", "stdassets", "textures/analog_stick"},
    {"arrow", "builtinassets", "textures/arrow"},
    {"assassinColor", "stdassets", "textures/assassin_color"},
    {"assassinColorMask", "stdassets", "textures/assassin_color_mask"},
    {"assassinIcon", "stdassets", "textures/assassin_icon"},
    {"assassinIconColorMask", "stdassets", "textures/assassin_icon_color_mask"},
    {"audioIcon", "stdassets", "textures/audio_icon"},
    {"backIcon", "builtinassets", "textures/back_icon"},
    {"bar", "stdassets", "textures/bar"},
    {"bearColor", "stdassets", "textures/bear_color"},
    {"bearColorMask", "stdassets", "textures/bear_color_mask"},
    {"bearIcon", "stdassets", "textures/bear_icon"},
    {"bearIconColorMask", "stdassets", "textures/bear_icon_color_mask"},
    {"bg", "stdassets", "textures/bg"},
    {"bigG", "stdassets", "textures/big_g"},
    {"bigGPreview", "stdassets", "textures/big_gpreview"},
    {"black", "builtinassets", "textures/black"},
    {"bombButton", "builtinassets", "textures/bomb_button"},
    {"bombColor", "stdassets", "textures/bomb_color"},
    {"bombColorIce", "stdassets", "textures/bomb_color_ice"},
    {"bombStickyColor", "stdassets", "textures/bomb_sticky_color"},
    {"bonesColor", "stdassets", "textures/bones_color"},
    {"bonesColorMask", "stdassets", "textures/bones_color_mask"},
    {"bonesIcon", "stdassets", "textures/bones_icon"},
    {"bonesIconColorMask", "stdassets", "textures/bones_icon_color_mask"},
    {"boxingGlovesColor", "builtinassets", "textures/boxing_gloves_color"},
    {"bridgitLevelColor", "stdassets", "textures/bridgit_level_color"},
    {"bridgitPreview", "stdassets", "textures/bridgit_preview"},
    {"bunnyColor", "stdassets", "textures/bunny_color"},
    {"bunnyColorMask", "stdassets", "textures/bunny_color_mask"},
    {"bunnyIcon", "stdassets", "textures/bunny_icon"},
    {"bunnyIconColorMask", "stdassets", "textures/bunny_icon_color_mask"},
    {"buttonBomb", "stdassets", "textures/button_bomb"},
    {"buttonJump", "stdassets", "textures/button_jump"},
    {"buttonPickUp", "stdassets", "textures/button_pick_up"},
    {"buttonPunch", "stdassets", "textures/button_punch"},
    {"buttonSquare", "builtinassets", "textures/button_square"},
    {"buttonSquareWide", "builtinassets", "textures/button_square_wide"},
    {"chTitleChar1", "stdassets", "textures/ch_title_char1"},
    {"chTitleChar2", "stdassets", "textures/ch_title_char2"},
    {"chTitleChar3", "stdassets", "textures/ch_title_char3"},
    {"chTitleChar4", "stdassets", "textures/ch_title_char4"},
    {"chTitleChar5", "stdassets", "textures/ch_title_char5"},
    {"characterIconMask", "builtinassets", "textures/character_icon_mask"},
    {"chestIcon", "stdassets", "textures/chest_icon"},
    {"chestIconEmpty", "stdassets", "textures/chest_icon_empty"},
    {"chestIconMulti", "stdassets", "textures/chest_icon_multi"},
    {"chestIconTint", "stdassets", "textures/chest_icon_tint"},
    {"chestOpenIcon", "stdassets", "textures/chest_open_icon"},
    {"chestOpenIconTint", "stdassets", "textures/chest_open_icon_tint"},
    {"circle", "builtinassets", "textures/circle"},
    {"circleNoAlpha", "builtinassets", "textures/circle_no_alpha"},
    {"circleOutline", "builtinassets", "textures/circle_outline"},
    {"circleOutlineNoAlpha", "builtinassets",
     "textures/circle_outline_no_alpha"},
    {"circleShadow", "builtinassets", "textures/circle_shadow"},
    {"circleSoft", "builtinassets", "textures/circle_soft"},
    {"circleZigZag", "stdassets", "textures/circle_zig_zag"},
    {"clayStroke", "stdassets", "textures/clay_stroke"},
    {"coin", "stdassets", "textures/coin"},
    {"controllerIcon", "stdassets", "textures/controller_icon"},
    {"courtyardLevelColor", "stdassets", "textures/courtyard_level_color"},
    {"courtyardPreview", "stdassets", "textures/courtyard_preview"},
    {"cowboyColor", "stdassets", "textures/cowboy_color"},
    {"cowboyColorMask", "stdassets", "textures/cowboy_color_mask"},
    {"cowboyIcon", "stdassets", "textures/cowboy_icon"},
    {"cowboyIconColorMask", "stdassets", "textures/cowboy_icon_color_mask"},
    {"cragCastleLevelColor", "stdassets", "textures/crag_castle_level_color"},
    {"cragCastlePreview", "stdassets", "textures/crag_castle_preview"},
    {"crossOut", "stdassets", "textures/cross_out"},
    {"crossOutMask", "stdassets", "textures/cross_out_mask"},
    {"cursor", "builtinassets", "textures/cursor"},
    {"cuteSpaz", "stdassets", "textures/cute_spaz"},
    {"cyborgColor", "stdassets", "textures/cyborg_color"},
    {"cyborgColorMask", "stdassets", "textures/cyborg_color_mask"},
    {"cyborgIcon", "stdassets", "textures/cyborg_icon"},
    {"cyborgIconColorMask", "stdassets", "textures/cyborg_icon_color_mask"},
    {"discordIcon", "stdassets", "textures/discord_icon"},
    {"discordLogo", "stdassets", "textures/discord_logo"},
    {"discordServer", "stdassets", "textures/discord_server"},
    {"doomShroomBGColor", "stdassets", "textures/doom_shroom_bgcolor"},
    {"doomShroomLevelColor", "stdassets", "textures/doom_shroom_level_color"},
    {"doomShroomPreview", "stdassets", "textures/doom_shroom_preview"},
    {"downButton", "stdassets", "textures/down_button"},
    {"egg1", "stdassets", "textures/egg1"},
    {"egg2", "stdassets", "textures/egg2"},
    {"egg3", "stdassets", "textures/egg3"},
    {"egg4", "stdassets", "textures/egg4"},
    {"eggTex1", "stdassets", "textures/egg_tex1"},
    {"eggTex2", "stdassets", "textures/egg_tex2"},
    {"eggTex3", "stdassets", "textures/egg_tex3"},
    {"empty", "stdassets", "textures/empty"},
    {"explosion", "builtinassets", "textures/explosion"},
    {"eyeColor", "builtinassets", "textures/eye_color"},
    {"eyeColorTintMask", "builtinassets", "textures/eye_color_tint_mask"},
    {"file", "stdassets", "textures/file"},
    {"flagColor", "stdassets", "textures/flag_color"},
    {"flagPoleColor", "builtinassets", "textures/flag_pole_color"},
    {"folder", "stdassets", "textures/folder"},
    {"fontBig", "builtinassets", "textures/font_big"},
    {"fontExtras", "builtinassets", "textures/font_extras"},
    {"fontExtras2", "builtinassets", "textures/font_extras2"},
    {"fontExtras3", "builtinassets", "textures/font_extras3"},
    {"fontExtras4", "builtinassets", "textures/font_extras4"},
    {"fontExtras5", "builtinassets", "textures/font_extras5"},
    {"fontSmall0", "builtinassets", "textures/font_small0"},
    {"fontSmall1", "builtinassets", "textures/font_small1"},
    {"fontSmall2", "builtinassets", "textures/font_small2"},
    {"fontSmall3", "builtinassets", "textures/font_small3"},
    {"fontSmall4", "builtinassets", "textures/font_small4"},
    {"fontSmall5", "builtinassets", "textures/font_small5"},
    {"fontSmall6", "builtinassets", "textures/font_small6"},
    {"fontSmall7", "builtinassets", "textures/font_small7"},
    {"footballStadium", "stdassets", "textures/football_stadium"},
    {"footballStadiumPreview", "stdassets",
     "textures/football_stadium_preview"},
    {"frameInset", "stdassets", "textures/frame_inset"},
    {"frostyColor", "stdassets", "textures/frosty_color"},
    {"frostyColorMask", "stdassets", "textures/frosty_color_mask"},
    {"frostyIcon", "stdassets", "textures/frosty_icon"},
    {"frostyIconColorMask", "stdassets", "textures/frosty_icon_color_mask"},
    {"fuse", "builtinassets", "textures/fuse"},
    {"gameCenterIcon", "stdassets", "textures/game_center_icon"},
    {"githubLogo", "stdassets", "textures/github_logo"},
    {"gladiatorColor", "stdassets", "textures/gladiator_color"},
    {"gladiatorColorMask", "stdassets", "textures/gladiator_color_mask"},
    {"gladiatorIcon", "stdassets", "textures/gladiator_icon"},
    {"gladiatorIconColorMask", "stdassets",
     "textures/gladiator_icon_color_mask"},
    {"glow", "builtinassets", "textures/glow"},
    {"goldPass", "stdassets", "textures/gold_pass"},
    {"googlePlayAchievementsIcon", "stdassets",
     "textures/google_play_achievements_icon"},
    {"googlePlayGamesIcon", "stdassets", "textures/google_play_games_icon"},
    {"googlePlayLeaderboardsIcon", "stdassets",
     "textures/google_play_leaderboards_icon"},
    {"googlePlusIcon", "stdassets", "textures/google_plus_icon"},
    {"googlePlusSignInButton", "stdassets",
     "textures/google_plus_sign_in_button"},
    {"graphicsIcon", "stdassets", "textures/graphics_icon"},
    {"heart", "stdassets", "textures/heart"},
    {"hockeyStadium", "stdassets", "textures/hockey_stadium"},
    {"hockeyStadiumPreview", "stdassets", "textures/hockey_stadium_preview"},
    {"iconOnslaught", "stdassets", "textures/icon_onslaught"},
    {"iconRunaround", "stdassets", "textures/icon_runaround"},
    {"impactBombColor", "stdassets", "textures/impact_bomb_color"},
    {"impactBombColorLit", "stdassets", "textures/impact_bomb_color_lit"},
    {"inventoryIcon", "stdassets", "textures/inventory_icon"},
    {"jackColor", "stdassets", "textures/jack_color"},
    {"jackColorMask", "stdassets", "textures/jack_color_mask"},
    {"jackIcon", "stdassets", "textures/jack_icon"},
    {"jackIconColorMask", "stdassets", "textures/jack_icon_color_mask"},
    {"jumpsuitColor", "stdassets", "textures/jumpsuit_color"},
    {"jumpsuitColorMask", "stdassets", "textures/jumpsuit_color_mask"},
    {"jumpsuitIcon", "stdassets", "textures/jumpsuit_icon"},
    {"jumpsuitIconColorMask", "stdassets", "textures/jumpsuit_icon_color_mask"},
    {"kronk", "stdassets", "textures/kronk"},
    {"kronkColorMask", "stdassets", "textures/kronk_color_mask"},
    {"kronkIcon", "stdassets", "textures/kronk_icon"},
    {"kronkIconColorMask", "stdassets", "textures/kronk_icon_color_mask"},
    {"lakeFrigid", "stdassets", "textures/lake_frigid"},
    {"lakeFrigidPreview", "stdassets", "textures/lake_frigid_preview"},
    {"lakeFrigidReflections", "stdassets", "textures/lake_frigid_reflections"},
    {"landMine", "stdassets", "textures/land_mine"},
    {"landMineLit", "stdassets", "textures/land_mine_lit"},
    {"leaderboardsIcon", "stdassets", "textures/leaderboards_icon"},
    {"leftButton", "stdassets", "textures/left_button"},
    {"levelIcon", "stdassets", "textures/level_icon"},
    {"light", "builtinassets", "textures/light"},
    {"lightSharp", "builtinassets", "textures/light_sharp"},
    {"lightSoft", "builtinassets", "textures/light_soft"},
    {"lock", "stdassets", "textures/lock"},
    {"logIcon", "stdassets", "textures/log_icon"},
    {"logo", "stdassets", "textures/logo"},
    {"logoEaster", "stdassets", "textures/logo_easter"},
    {"mapPreviewMask", "stdassets", "textures/map_preview_mask"},
    {"medalBronze", "stdassets", "textures/medal_bronze"},
    {"medalComplete", "stdassets", "textures/medal_complete"},
    {"medalGold", "stdassets", "textures/medal_gold"},
    {"medalSilver", "stdassets", "textures/medal_silver"},
    {"melColor", "stdassets", "textures/mel_color"},
    {"melColorMask", "stdassets", "textures/mel_color_mask"},
    {"melIcon", "stdassets", "textures/mel_icon"},
    {"melIconColorMask", "stdassets", "textures/mel_icon_color_mask"},
    {"menuBG", "stdassets", "textures/menu_bg"},
    {"menuButton", "builtinassets", "textures/menu_button"},
    {"menuIcon", "stdassets", "textures/menu_icon"},
    {"merch", "stdassets", "textures/merch"},
    {"meter", "stdassets", "textures/meter"},
    {"monkeyFaceLevelColor", "stdassets", "textures/monkey_face_level_color"},
    {"monkeyFacePreview", "stdassets", "textures/monkey_face_preview"},
    {"multiplayerExamples", "stdassets", "textures/multiplayer_examples"},
    {"natureBackgroundColor", "stdassets", "textures/nature_background_color"},
    {"neoSpazColor", "stdassets", "textures/neo_spaz_color"},
    {"neoSpazColorMask", "stdassets", "textures/neo_spaz_color_mask"},
    {"neoSpazIcon", "stdassets", "textures/neo_spaz_icon"},
    {"neoSpazIconColorMask", "stdassets", "textures/neo_spaz_icon_color_mask"},
    {"nextLevelIcon", "stdassets", "textures/next_level_icon"},
    {"ninjaColor", "stdassets", "textures/ninja_color"},
    {"ninjaColorMask", "stdassets", "textures/ninja_color_mask"},
    {"ninjaIcon", "stdassets", "textures/ninja_icon"},
    {"ninjaIconColorMask", "stdassets", "textures/ninja_icon_color_mask"},
    {"nub", "builtinassets", "textures/nub"},
    {"null", "stdassets", "textures/null"},
    {"oldLadyColor", "stdassets", "textures/old_lady_color"},
    {"oldLadyColorMask", "stdassets", "textures/old_lady_color_mask"},
    {"oldLadyIcon", "stdassets", "textures/old_lady_icon"},
    {"oldLadyIconColorMask", "stdassets", "textures/old_lady_icon_color_mask"},
    {"operaSingerColor", "stdassets", "textures/opera_singer_color"},
    {"operaSingerColorMask", "stdassets", "textures/opera_singer_color_mask"},
    {"operaSingerIcon", "stdassets", "textures/opera_singer_icon"},
    {"operaSingerIconColorMask", "stdassets",
     "textures/opera_singer_icon_color_mask"},
    {"ouyaAButton", "builtinassets", "textures/ouya_abutton"},
    {"ouyaIcon", "stdassets", "textures/ouya_icon"},
    {"ouyaOButton", "stdassets", "textures/ouya_obutton"},
    {"ouyaUButton", "stdassets", "textures/ouya_ubutton"},
    {"ouyaYButton", "stdassets", "textures/ouya_ybutton"},
    {"pageLeftRight", "builtinassets", "textures/page_left_right"},
    {"penguinColor", "stdassets", "textures/penguin_color"},
    {"penguinColorMask", "stdassets", "textures/penguin_color_mask"},
    {"penguinIcon", "stdassets", "textures/penguin_icon"},
    {"penguinIconColorMask", "stdassets", "textures/penguin_icon_color_mask"},
    {"pixieColor", "stdassets", "textures/pixie_color"},
    {"pixieColorMask", "stdassets", "textures/pixie_color_mask"},
    {"pixieIcon", "stdassets", "textures/pixie_icon"},
    {"pixieIconColorMask", "stdassets", "textures/pixie_icon_color_mask"},
    {"playerLineup", "stdassets", "textures/player_lineup"},
    {"plusButton", "stdassets", "textures/plus_button"},
    {"powerupBomb", "stdassets", "textures/powerup_bomb"},
    {"powerupCurse", "stdassets", "textures/powerup_curse"},
    {"powerupHealth", "stdassets", "textures/powerup_health"},
    {"powerupIceBombs", "stdassets", "textures/powerup_ice_bombs"},
    {"powerupImpactBombs", "stdassets", "textures/powerup_impact_bombs"},
    {"powerupLandMines", "stdassets", "textures/powerup_land_mines"},
    {"powerupPunch", "stdassets", "textures/powerup_punch"},
    {"powerupShield", "stdassets", "textures/powerup_shield"},
    {"powerupSpeed", "stdassets", "textures/powerup_speed"},
    {"powerupStickyBombs", "stdassets", "textures/powerup_sticky_bombs"},
    {"puckColor", "stdassets", "textures/puck_color"},
    {"quoteBubble", "stdassets", "textures/quote_bubble"},
    {"rampageBGColor", "stdassets", "textures/rampage_bgcolor"},
    {"rampageBGColor2", "stdassets", "textures/rampage_bgcolor2"},
    {"rampageLevelColor", "stdassets", "textures/rampage_level_color"},
    {"rampagePreview", "stdassets", "textures/rampage_preview"},
    {"replayIcon", "stdassets", "textures/replay_icon"},
    {"rgbStripes", "builtinassets", "textures/rgb_stripes"},
    {"rightButton", "stdassets", "textures/right_button"},
    {"robotColor", "stdassets", "textures/robot_color"},
    {"robotColorMask", "stdassets", "textures/robot_color_mask"},
    {"robotIcon", "stdassets", "textures/robot_icon"},
    {"robotIconColorMask", "stdassets", "textures/robot_icon_color_mask"},
    {"roundaboutLevelColor", "stdassets", "textures/roundabout_level_color"},
    {"roundaboutPreview", "stdassets", "textures/roundabout_preview"},
    {"santaColor", "stdassets", "textures/santa_color"},
    {"santaColorMask", "stdassets", "textures/santa_color_mask"},
    {"santaIcon", "stdassets", "textures/santa_icon"},
    {"santaIconColorMask", "stdassets", "textures/santa_icon_color_mask"},
    {"scorch", "builtinassets", "textures/scorch"},
    {"scorchBig", "builtinassets", "textures/scorch_big"},
    {"scrollWidget", "builtinassets", "textures/scroll_widget"},
    {"scrollWidgetGlow", "builtinassets", "textures/scroll_widget_glow"},
    {"settingsIcon", "stdassets", "textures/settings_icon"},
    {"shadow", "builtinassets", "textures/shadow"},
    {"shadowSharp", "builtinassets", "textures/shadow_sharp"},
    {"shadowSoft", "builtinassets", "textures/shadow_soft"},
    {"shield", "builtinassets", "textures/shield"},
    {"shrapnel1Color", "builtinassets", "textures/shrapnel1_color"},
    {"slash", "stdassets", "textures/slash"},
    {"smoke", "builtinassets", "textures/smoke"},
    {"softRect", "builtinassets", "textures/soft_rect"},
    {"softRect2", "builtinassets", "textures/soft_rect2"},
    {"softRectVertical", "builtinassets", "textures/soft_rect_vertical"},
    {"sparks", "builtinassets", "textures/sparks"},
    {"spinner", "builtinassets", "textures/spinner"},
    {"spinner0", "builtinassets", "textures/spinner0"},
    {"spinner1", "builtinassets", "textures/spinner1"},
    {"spinner10", "builtinassets", "textures/spinner10"},
    {"spinner11", "builtinassets", "textures/spinner11"},
    {"spinner2", "builtinassets", "textures/spinner2"},
    {"spinner3", "builtinassets", "textures/spinner3"},
    {"spinner4", "builtinassets", "textures/spinner4"},
    {"spinner5", "builtinassets", "textures/spinner5"},
    {"spinner6", "builtinassets", "textures/spinner6"},
    {"spinner7", "builtinassets", "textures/spinner7"},
    {"spinner8", "builtinassets", "textures/spinner8"},
    {"spinner9", "builtinassets", "textures/spinner9"},
    {"star", "stdassets", "textures/star"},
    {"startButton", "builtinassets", "textures/start_button"},
    {"stepRightUpLevelColor", "stdassets",
     "textures/step_right_up_level_color"},
    {"stepRightUpPreview", "stdassets", "textures/step_right_up_preview"},
    {"storeCharacter", "stdassets", "textures/store_character"},
    {"storeCharacterEaster", "stdassets", "textures/store_character_easter"},
    {"storeCharacterXmas", "stdassets", "textures/store_character_xmas"},
    {"storeIcon", "stdassets", "textures/store_icon"},
    {"superheroColor", "stdassets", "textures/superhero_color"},
    {"superheroColorMask", "stdassets", "textures/superhero_color_mask"},
    {"superheroIcon", "stdassets", "textures/superhero_icon"},
    {"superheroIconColorMask", "stdassets",
     "textures/superhero_icon_color_mask"},
    {"textClearButton", "builtinassets", "textures/text_clear_button"},
    {"thePadLevelColor", "stdassets", "textures/the_pad_level_color"},
    {"thePadPreview", "stdassets", "textures/the_pad_preview"},
    {"ticketRoll", "stdassets", "textures/ticket_roll"},
    {"ticketRollBig", "stdassets", "textures/ticket_roll_big"},
    {"ticketRolls", "stdassets", "textures/ticket_rolls"},
    {"tickets", "stdassets", "textures/tickets"},
    {"ticketsMore", "stdassets", "textures/tickets_more"},
    {"ticketsPurple", "stdassets", "textures/tickets_purple"},
    {"tipTopBGColor", "stdassets", "textures/tip_top_bgcolor"},
    {"tipTopLevelColor", "stdassets", "textures/tip_top_level_color"},
    {"tipTopPreview", "stdassets", "textures/tip_top_preview"},
    {"tnt", "stdassets", "textures/tnt"},
    {"tokens1", "stdassets", "textures/tokens1"},
    {"tokens2", "stdassets", "textures/tokens2"},
    {"tokens3", "stdassets", "textures/tokens3"},
    {"tokens4", "stdassets", "textures/tokens4"},
    {"touchArrows", "builtinassets", "textures/touch_arrows"},
    {"touchArrowsActions", "builtinassets", "textures/touch_arrows_actions"},
    {"towerDLevelColor", "stdassets", "textures/tower_dlevel_color"},
    {"towerDPreview", "stdassets", "textures/tower_dpreview"},
    {"treesColor", "stdassets", "textures/trees_color"},
    {"trophy", "stdassets", "textures/trophy"},
    {"tv", "stdassets", "textures/tv"},
    {"uiAtlas", "builtinassets", "textures/ui_atlas"},
    {"uiAtlas2", "builtinassets", "textures/ui_atlas2"},
    {"upButton", "stdassets", "textures/up_button"},
    {"usersButton", "builtinassets", "textures/users_button"},
    {"vrFillMound", "stdassets", "textures/vr_fill_mound"},
    {"warriorColor", "stdassets", "textures/warrior_color"},
    {"warriorColorMask", "stdassets", "textures/warrior_color_mask"},
    {"warriorIcon", "stdassets", "textures/warrior_icon"},
    {"warriorIconColorMask", "stdassets", "textures/warrior_icon_color_mask"},
    {"white", "builtinassets", "textures/white"},
    {"windowBottomCap", "stdassets", "textures/window_bottom_cap"},
    {"windowHSmallVMed", "builtinassets", "textures/window_hsmall_vmed"},
    {"windowHSmallVSmall", "builtinassets", "textures/window_hsmall_vsmall"},
    {"wings", "builtinassets", "textures/wings"},
    {"witchColor", "stdassets", "textures/witch_color"},
    {"witchColorMask", "stdassets", "textures/witch_color_mask"},
    {"witchIcon", "stdassets", "textures/witch_icon"},
    {"witchIconColorMask", "stdassets", "textures/witch_icon_color_mask"},
    {"wizardColor", "stdassets", "textures/wizard_color"},
    {"wizardColorMask", "stdassets", "textures/wizard_color_mask"},
    {"wizardIcon", "stdassets", "textures/wizard_icon"},
    {"wizardIconColorMask", "stdassets", "textures/wizard_icon_color_mask"},
    {"wrestlerColor", "stdassets", "textures/wrestler_color"},
    {"wrestlerColorMask", "stdassets", "textures/wrestler_color_mask"},
    {"wrestlerIcon", "stdassets", "textures/wrestler_icon"},
    {"wrestlerIconColorMask", "stdassets", "textures/wrestler_icon_color_mask"},
    {"zigZagLevelColor", "stdassets", "textures/zig_zag_level_color"},
    {"zigzagPreview", "stdassets", "textures/zigzag_preview"},
    {"zoeColor", "stdassets", "textures/zoe_color"},
    {"zoeColorMask", "stdassets", "textures/zoe_color_mask"},
    {"zoeIcon", "stdassets", "textures/zoe_icon"},
    {"zoeIconColorMask", "stdassets", "textures/zoe_icon_color_mask"},
};

struct State_ {
  // Legacy name -> (package_key, logical_path).
  std::unordered_map<std::string, std::pair<std::string, std::string>>
      from_legacy;
  // 'package_key:logical_path' -> legacy name.
  std::unordered_map<std::string, std::string> to_legacy;
  // package_key -> registered full apverid.
  std::unordered_map<std::string, std::string> package_versions;
  // Versionless apverid prefix ('a-0.babuiltinassets') -> package_key.
  std::unordered_map<std::string, std::string> versionless_to_key;
};

static auto GetState_() -> State_& {
  static State_* state = [] {
    auto* st = new State_();
    for (const Row_& row : kRows) {
      st->from_legacy[row.legacy] = {row.package_key, row.logical_path};
      st->to_legacy[std::string(row.package_key) + ":" + row.logical_path] =
          row.legacy;
    }
    return st;
  }();
  return *state;
}

// Strip the trailing version segment off an apverid
// ('a-0.babuiltinassets.dev260610e' -> 'a-0.babuiltinassets').
static auto VersionlessApverid_(const std::string& apverid) -> std::string {
  size_t pos = apverid.rfind('.');
  return pos == std::string::npos ? apverid : apverid.substr(0, pos);
}

void AssetNameCompat::SetPackageVersion(const std::string& package_key,
                                        const std::string& apverid) {
  assert(g_base->InLogicThread());
  auto& state = GetState_();
  // Drop any versionless mapping from a previous registration.
  auto old = state.package_versions.find(package_key);
  if (old != state.package_versions.end()) {
    state.versionless_to_key.erase(VersionlessApverid_(old->second));
  }
  state.package_versions[package_key] = apverid;
  state.versionless_to_key[VersionlessApverid_(apverid)] = package_key;
}

auto AssetNameCompat::FromLegacy(const std::string& name) -> std::string {
  assert(g_base->InLogicThread());
  if (name.find(':') != std::string::npos) {
    return name;  // Already qualified.
  }
  auto& state = GetState_();
  auto row = state.from_legacy.find(name);
  if (row == state.from_legacy.end()) {
    return name;  // No asset-package home; a true legacy name.
  }
  auto version = state.package_versions.find(row->second.first);
  if (version == state.package_versions.end()) {
    return name;  // Package version not registered (yet).
  }
  std::string mapped = version->second + ":" + row->second.second;
  g_core->logging->Log(
      LogName::kBaAssets, LogLevel::kDebug,
      "AssetNameCompat: from-legacy '" + name + "' -> '" + mapped + "'.");
  return mapped;
}

auto AssetNameCompat::ToLegacy(const std::string& name) -> std::string {
  assert(g_base->InLogicThread());
  size_t colon = name.find(':');
  if (colon == std::string::npos) {
    return name;  // Already a bare name.
  }
  auto& state = GetState_();
  auto key =
      state.versionless_to_key.find(VersionlessApverid_(name.substr(0, colon)));
  if (key == state.versionless_to_key.end()) {
    return name;  // Not a package we know about.
  }
  auto legacy =
      state.to_legacy.find(key->second + ":" + name.substr(colon + 1));
  if (legacy == state.to_legacy.end()) {
    return name;
  }
  g_core->logging->Log(
      LogName::kBaAssets, LogLevel::kDebug,
      "AssetNameCompat: to-legacy '" + name + "' -> '" + legacy->second + "'.");
  return legacy->second;
}

}  // namespace ballistica::base
