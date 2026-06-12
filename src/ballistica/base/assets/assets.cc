// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/assets/assets.h"

#include <cstdio>
#include <string>
#include <unordered_map>
#include <vector>

#include "ballistica/base/app_adapter/app_adapter.h"
#include "ballistica/base/app_mode/app_mode.h"
#include "ballistica/base/assets/asset_name_compat.h"
#include "ballistica/base/assets/assets_server.h"
#include "ballistica/base/assets/collision_mesh_asset.h"
#include "ballistica/base/assets/data_asset.h"
#include "ballistica/base/assets/mesh_asset.h"
#include "ballistica/base/assets/sound_asset.h"
#include "ballistica/base/assets/texture_asset.h"
#include "ballistica/base/audio/audio_server.h"
#include "ballistica/base/graphics/graphics.h"
#include "ballistica/base/graphics/graphics_server.h"
#include "ballistica/base/graphics/text/text_packer.h"
#include "ballistica/base/logic/logic.h"
#include "ballistica/base/python/base_python.h"
#include "ballistica/base/ui/ui.h"
#include "ballistica/core/logging/logging.h"
#include "ballistica/core/logging/logging_macros.h"
#include "ballistica/core/platform/platform.h"
#include "ballistica/shared/foundation/event_loop.h"
#include "ballistica/shared/generic/json.h"
#include "ballistica/shared/python/python.h"

namespace ballistica::base {

static const bool kShowPruningInfo = false;

#define SHOW_PRUNING_INFO 0

// Standard prune time for unused assets: 10 minutes (1000ms * 60 * 10).
#define STANDARD_ASSET_PRUNE_TIME 600000

// More aggressive prune time for dynamically-generated text-textures: 10
// seconds.
#define TEXT_TEXTURE_PRUNE_TIME 10000

#define QR_TEXTURE_PRUNE_TIME 10000

// How long we should spend loading assets in each runPendingLoads() call.
#define PENDING_LOAD_PROCESS_TIME 5

Assets::Assets() {
  asset_paths_.emplace_back(g_core->GetDataDirectory() + BA_DIRSLASH
                            + "ba_data");
  for (bool& have_pending_load : have_pending_loads_) {
    have_pending_load = false;
  }

  InitSpecialChars();
}

void Assets::LoadSystemData(SystemDataID id, const char* name) {
  system_datas_.push_back(GetDataAsset(name));
  assert(system_datas_.size() == static_cast<int>(id) + 1);
}

// Bring-up note: the four LoadBuiltin* loaders below catch lookup
// failures so a stale local cached manifest (or in-progress workspace
// migration) doesn't crash engine startup. They push a null Ref on
// miss to keep the per-id slot invariant intact. Tighten to a hard
// failure once the cache-refresh path is reliable.
void Assets::LoadBuiltinTexture(BuiltinTextureID id, const char* name) {
  assert(asset_lists_locked_);
  Object::Ref<TextureAsset> tex;
  try {
    tex = GetTexture(name);
  } catch (const std::exception& exc) {
    g_core->logging->Log(LogName::kBaAssets, LogLevel::kWarning,
                         std::string("LoadBuiltinTexture failed for '") + name
                             + "': " + exc.what());
  }
  builtin_textures_.push_back(tex);
  assert(builtin_textures_.size() == static_cast<int>(id) + 1);
}

void Assets::LoadBuiltinCubeMapTexture(BuiltinCubeMapTextureID id,
                                       const char* name) {
  assert(asset_lists_locked_);
  Object::Ref<TextureAsset> tex;
  try {
    tex = GetCubeMapTexture(name);
  } catch (const std::exception& exc) {
    g_core->logging->Log(LogName::kBaAssets, LogLevel::kWarning,
                         std::string("LoadBuiltinCubeMapTexture failed for '")
                             + name + "': " + exc.what());
  }
  builtin_cube_map_textures_.push_back(tex);
  assert(builtin_cube_map_textures_.size() == static_cast<int>(id) + 1);
}

void Assets::LoadBuiltinSound(BuiltinSoundID id, const char* name) {
  assert(asset_lists_locked_);
  Object::Ref<SoundAsset> snd;
  try {
    snd = GetSound(name);
  } catch (const std::exception& exc) {
    g_core->logging->Log(LogName::kBaAssets, LogLevel::kWarning,
                         std::string("LoadBuiltinSound failed for '") + name
                             + "': " + exc.what());
  }
  builtin_sounds_.push_back(snd);
  assert(builtin_sounds_.size() == static_cast<int>(id) + 1);
}

void Assets::LoadBuiltinMesh(BuiltinMeshID id, const char* name) {
  assert(asset_lists_locked_);
  Object::Ref<MeshAsset> mesh;
  try {
    mesh = GetMesh(name);
  } catch (const std::exception& exc) {
    g_core->logging->Log(LogName::kBaAssets, LogLevel::kWarning,
                         std::string("LoadBuiltinMesh failed for '") + name
                             + "': " + exc.what());
  }
  builtin_meshes_.push_back(mesh);
  assert(builtin_meshes_.size() == static_cast<int>(id) + 1);
}

void Assets::StartLoading() {
  assert(g_base->InLogicThread());
  assert(g_base);
  assert(g_base->audio_server && g_base->assets_server
         && g_base->graphics_server);
  assert(g_base->graphics->has_client_context());

  // We should only be called once.
  assert(!asset_loads_allowed_);
  asset_loads_allowed_ = true;

  // Populate the asset-package CAS registry before the LoadBuiltin*
  // calls below land — those use qualified-ref names that require the
  // registry to be live.
  g_base->python->objs()
      .Get(BasePython::ObjID::kLoadBundledAssetPackagesCall)
      .Call();

  // Just grab the lock once for all this stuff for efficiency.
  AssetListLock lock;

  // System sounds:

  // System datas:
  // (crickets)

  // System meshes:
#if BA_VR_BUILD
#endif  // BA_VR_BUILD

  // CAS-backed builtin loads. The block below is auto-generated;
  // each line corresponds to one entry in ``BuiltinTextureID`` /
  // ``BuiltinSoundID`` / ``BuiltinMeshID`` / ``BuiltinCubeMapTextureID``
  // in base.h. Rerun ``make update`` to regenerate.
  // __AUTOGENERATED_BUILTIN_ASSET_LOAD_BEGIN__
  // textures
  LoadBuiltinTexture(BuiltinTextureID::kTexturesActionButtons,
                     "a-0.babuiltinassets.260612:textures/action_buttons");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesArrow,
                     "a-0.babuiltinassets.260612:textures/arrow");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesBackIcon,
                     "a-0.babuiltinassets.260612:textures/back_icon");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesBlack,
                     "a-0.babuiltinassets.260612:textures/black");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesBombButton,
                     "a-0.babuiltinassets.260612:textures/bomb_button");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesBoxingGlovesColor,
                     "a-0.babuiltinassets.260612:textures/boxing_gloves_color");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesButtonSquare,
                     "a-0.babuiltinassets.260612:textures/button_square");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesButtonSquareWide,
                     "a-0.babuiltinassets.260612:textures/button_square_wide");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesCharacterIconMask,
                     "a-0.babuiltinassets.260612:textures/character_icon_mask");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesCircle,
                     "a-0.babuiltinassets.260612:textures/circle");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesCircleNoAlpha,
                     "a-0.babuiltinassets.260612:textures/circle_no_alpha");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesCircleOutline,
                     "a-0.babuiltinassets.260612:textures/circle_outline");
  LoadBuiltinTexture(
      BuiltinTextureID::kTexturesCircleOutlineNoAlpha,
      "a-0.babuiltinassets.260612:textures/circle_outline_no_alpha");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesCircleShadow,
                     "a-0.babuiltinassets.260612:textures/circle_shadow");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesCircleSoft,
                     "a-0.babuiltinassets.260612:textures/circle_soft");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesCursor,
                     "a-0.babuiltinassets.260612:textures/cursor");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesExplosion,
                     "a-0.babuiltinassets.260612:textures/explosion");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesEyeColor,
                     "a-0.babuiltinassets.260612:textures/eye_color");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesEyeColorTintMask,
                     "a-0.babuiltinassets.260612:textures/eye_color_tint_mask");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesFlagPoleColor,
                     "a-0.babuiltinassets.260612:textures/flag_pole_color");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesFontBig,
                     "a-0.babuiltinassets.260612:textures/font_big");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesFontExtras,
                     "a-0.babuiltinassets.260612:textures/font_extras");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesFontExtras2,
                     "a-0.babuiltinassets.260612:textures/font_extras2");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesFontExtras3,
                     "a-0.babuiltinassets.260612:textures/font_extras3");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesFontExtras4,
                     "a-0.babuiltinassets.260612:textures/font_extras4");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesFontExtras5,
                     "a-0.babuiltinassets.260612:textures/font_extras5");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesFontSmall0,
                     "a-0.babuiltinassets.260612:textures/font_small0");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesFontSmall1,
                     "a-0.babuiltinassets.260612:textures/font_small1");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesFontSmall2,
                     "a-0.babuiltinassets.260612:textures/font_small2");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesFontSmall3,
                     "a-0.babuiltinassets.260612:textures/font_small3");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesFontSmall4,
                     "a-0.babuiltinassets.260612:textures/font_small4");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesFontSmall5,
                     "a-0.babuiltinassets.260612:textures/font_small5");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesFontSmall6,
                     "a-0.babuiltinassets.260612:textures/font_small6");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesFontSmall7,
                     "a-0.babuiltinassets.260612:textures/font_small7");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesFuse,
                     "a-0.babuiltinassets.260612:textures/fuse");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesGlow,
                     "a-0.babuiltinassets.260612:textures/glow");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesLight,
                     "a-0.babuiltinassets.260612:textures/light");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesLightSharp,
                     "a-0.babuiltinassets.260612:textures/light_sharp");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesLightSoft,
                     "a-0.babuiltinassets.260612:textures/light_soft");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesMenuButton,
                     "a-0.babuiltinassets.260612:textures/menu_button");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesNub,
                     "a-0.babuiltinassets.260612:textures/nub");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesOuyaAbutton,
                     "a-0.babuiltinassets.260612:textures/ouya_abutton");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesPageLeftRight,
                     "a-0.babuiltinassets.260612:textures/page_left_right");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesRgbStripes,
                     "a-0.babuiltinassets.260612:textures/rgb_stripes");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesScorch,
                     "a-0.babuiltinassets.260612:textures/scorch");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesScorchBig,
                     "a-0.babuiltinassets.260612:textures/scorch_big");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesScrollWidget,
                     "a-0.babuiltinassets.260612:textures/scroll_widget");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesScrollWidgetGlow,
                     "a-0.babuiltinassets.260612:textures/scroll_widget_glow");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesShadow,
                     "a-0.babuiltinassets.260612:textures/shadow");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesShadowSharp,
                     "a-0.babuiltinassets.260612:textures/shadow_sharp");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesShadowSoft,
                     "a-0.babuiltinassets.260612:textures/shadow_soft");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesShield,
                     "a-0.babuiltinassets.260612:textures/shield");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesShrapnel1Color,
                     "a-0.babuiltinassets.260612:textures/shrapnel1_color");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesSmoke,
                     "a-0.babuiltinassets.260612:textures/smoke");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesSoftRect,
                     "a-0.babuiltinassets.260612:textures/soft_rect");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesSoftRect2,
                     "a-0.babuiltinassets.260612:textures/soft_rect2");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesSoftRectVertical,
                     "a-0.babuiltinassets.260612:textures/soft_rect_vertical");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesSparks,
                     "a-0.babuiltinassets.260612:textures/sparks");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesSpinner,
                     "a-0.babuiltinassets.260612:textures/spinner");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesSpinner0,
                     "a-0.babuiltinassets.260612:textures/spinner0");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesSpinner1,
                     "a-0.babuiltinassets.260612:textures/spinner1");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesSpinner10,
                     "a-0.babuiltinassets.260612:textures/spinner10");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesSpinner11,
                     "a-0.babuiltinassets.260612:textures/spinner11");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesSpinner2,
                     "a-0.babuiltinassets.260612:textures/spinner2");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesSpinner3,
                     "a-0.babuiltinassets.260612:textures/spinner3");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesSpinner4,
                     "a-0.babuiltinassets.260612:textures/spinner4");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesSpinner5,
                     "a-0.babuiltinassets.260612:textures/spinner5");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesSpinner6,
                     "a-0.babuiltinassets.260612:textures/spinner6");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesSpinner7,
                     "a-0.babuiltinassets.260612:textures/spinner7");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesSpinner8,
                     "a-0.babuiltinassets.260612:textures/spinner8");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesSpinner9,
                     "a-0.babuiltinassets.260612:textures/spinner9");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesStartButton,
                     "a-0.babuiltinassets.260612:textures/start_button");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesTextClearButton,
                     "a-0.babuiltinassets.260612:textures/text_clear_button");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesTouchArrows,
                     "a-0.babuiltinassets.260612:textures/touch_arrows");
  LoadBuiltinTexture(
      BuiltinTextureID::kTexturesTouchArrowsActions,
      "a-0.babuiltinassets.260612:textures/touch_arrows_actions");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesUiAtlas,
                     "a-0.babuiltinassets.260612:textures/ui_atlas");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesUiAtlas2,
                     "a-0.babuiltinassets.260612:textures/ui_atlas2");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesUsersButton,
                     "a-0.babuiltinassets.260612:textures/users_button");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesWhite,
                     "a-0.babuiltinassets.260612:textures/white");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesWindowHsmallVmed,
                     "a-0.babuiltinassets.260612:textures/window_hsmall_vmed");
  LoadBuiltinTexture(
      BuiltinTextureID::kTexturesWindowHsmallVsmall,
      "a-0.babuiltinassets.260612:textures/window_hsmall_vsmall");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesWings,
                     "a-0.babuiltinassets.260612:textures/wings");
  // cube_map_textures
  LoadBuiltinCubeMapTexture(
      BuiltinCubeMapTextureID::kTexturesReflectionChar,
      "a-0.babuiltinassets.260612:textures/reflection_char");
  LoadBuiltinCubeMapTexture(
      BuiltinCubeMapTextureID::kTexturesReflectionPowerup,
      "a-0.babuiltinassets.260612:textures/reflection_powerup");
  LoadBuiltinCubeMapTexture(
      BuiltinCubeMapTextureID::kTexturesReflectionSharp,
      "a-0.babuiltinassets.260612:textures/reflection_sharp");
  LoadBuiltinCubeMapTexture(
      BuiltinCubeMapTextureID::kTexturesReflectionSharper,
      "a-0.babuiltinassets.260612:textures/reflection_sharper");
  LoadBuiltinCubeMapTexture(
      BuiltinCubeMapTextureID::kTexturesReflectionSharpest,
      "a-0.babuiltinassets.260612:textures/reflection_sharpest");
  LoadBuiltinCubeMapTexture(
      BuiltinCubeMapTextureID::kTexturesReflectionSoft,
      "a-0.babuiltinassets.260612:textures/reflection_soft");
  // sounds
  LoadBuiltinSound(BuiltinSoundID::kAudioBlank,
                   "a-0.babuiltinassets.260612:audio/blank");
  LoadBuiltinSound(BuiltinSoundID::kAudioBlip,
                   "a-0.babuiltinassets.260612:audio/blip");
  LoadBuiltinSound(BuiltinSoundID::kAudioCashRegister,
                   "a-0.babuiltinassets.260612:audio/cash_register");
  LoadBuiltinSound(BuiltinSoundID::kAudioClick01,
                   "a-0.babuiltinassets.260612:audio/click01");
  LoadBuiltinSound(BuiltinSoundID::kAudioCorkPop,
                   "a-0.babuiltinassets.260612:audio/cork_pop");
  LoadBuiltinSound(BuiltinSoundID::kAudioDeek,
                   "a-0.babuiltinassets.260612:audio/deek");
  LoadBuiltinSound(BuiltinSoundID::kAudioDing,
                   "a-0.babuiltinassets.260612:audio/ding");
  LoadBuiltinSound(BuiltinSoundID::kAudioError,
                   "a-0.babuiltinassets.260612:audio/error");
  LoadBuiltinSound(BuiltinSoundID::kAudioGunCocking,
                   "a-0.babuiltinassets.260612:audio/gun_cocking");
  LoadBuiltinSound(BuiltinSoundID::kAudioPowerdown01,
                   "a-0.babuiltinassets.260612:audio/powerdown01");
  LoadBuiltinSound(BuiltinSoundID::kAudioPunch01,
                   "a-0.babuiltinassets.260612:audio/punch01");
  LoadBuiltinSound(BuiltinSoundID::kAudioScoreIncrease,
                   "a-0.babuiltinassets.260612:audio/score_increase");
  LoadBuiltinSound(BuiltinSoundID::kAudioSparkle01,
                   "a-0.babuiltinassets.260612:audio/sparkle01");
  LoadBuiltinSound(BuiltinSoundID::kAudioSparkle02,
                   "a-0.babuiltinassets.260612:audio/sparkle02");
  LoadBuiltinSound(BuiltinSoundID::kAudioSparkle03,
                   "a-0.babuiltinassets.260612:audio/sparkle03");
  LoadBuiltinSound(BuiltinSoundID::kAudioSwish,
                   "a-0.babuiltinassets.260612:audio/swish");
  LoadBuiltinSound(BuiltinSoundID::kAudioSwish2,
                   "a-0.babuiltinassets.260612:audio/swish2");
  LoadBuiltinSound(BuiltinSoundID::kAudioSwish3,
                   "a-0.babuiltinassets.260612:audio/swish3");
  LoadBuiltinSound(BuiltinSoundID::kAudioTap,
                   "a-0.babuiltinassets.260612:audio/tap");
  LoadBuiltinSound(BuiltinSoundID::kAudioTickingCrazy,
                   "a-0.babuiltinassets.260612:audio/ticking_crazy");
  // meshs
  LoadBuiltinMesh(BuiltinMeshID::kMeshesActionButtonBottom,
                  "a-0.babuiltinassets.260612:meshes/action_button_bottom");
  LoadBuiltinMesh(BuiltinMeshID::kMeshesActionButtonLeft,
                  "a-0.babuiltinassets.260612:meshes/action_button_left");
  LoadBuiltinMesh(BuiltinMeshID::kMeshesActionButtonRight,
                  "a-0.babuiltinassets.260612:meshes/action_button_right");
  LoadBuiltinMesh(BuiltinMeshID::kMeshesActionButtonTop,
                  "a-0.babuiltinassets.260612:meshes/action_button_top");
  LoadBuiltinMesh(BuiltinMeshID::kMeshesArrowBack,
                  "a-0.babuiltinassets.260612:meshes/arrow_back");
  LoadBuiltinMesh(BuiltinMeshID::kMeshesArrowFront,
                  "a-0.babuiltinassets.260612:meshes/arrow_front");
  LoadBuiltinMesh(BuiltinMeshID::kMeshesBox,
                  "a-0.babuiltinassets.260612:meshes/box");
  LoadBuiltinMesh(BuiltinMeshID::kMeshesBoxingGlove,
                  "a-0.babuiltinassets.260612:meshes/boxing_glove");
  LoadBuiltinMesh(BuiltinMeshID::kMeshesButtonBackOpaque,
                  "a-0.babuiltinassets.260612:meshes/button_back_opaque");
  LoadBuiltinMesh(BuiltinMeshID::kMeshesButtonBackSmallOpaque,
                  "a-0.babuiltinassets.260612:meshes/button_back_small_opaque");
  LoadBuiltinMesh(
      BuiltinMeshID::kMeshesButtonBackSmallTransparent,
      "a-0.babuiltinassets.260612:meshes/button_back_small_transparent");
  LoadBuiltinMesh(BuiltinMeshID::kMeshesButtonBackTransparent,
                  "a-0.babuiltinassets.260612:meshes/button_back_transparent");
  LoadBuiltinMesh(BuiltinMeshID::kMeshesButtonLargeOpaque,
                  "a-0.babuiltinassets.260612:meshes/button_large_opaque");
  LoadBuiltinMesh(BuiltinMeshID::kMeshesButtonLargeTransparent,
                  "a-0.babuiltinassets.260612:meshes/button_large_transparent");
  LoadBuiltinMesh(BuiltinMeshID::kMeshesButtonLargerOpaque,
                  "a-0.babuiltinassets.260612:meshes/button_larger_opaque");
  LoadBuiltinMesh(
      BuiltinMeshID::kMeshesButtonLargerTransparent,
      "a-0.babuiltinassets.260612:meshes/button_larger_transparent");
  LoadBuiltinMesh(BuiltinMeshID::kMeshesButtonMediumOpaque,
                  "a-0.babuiltinassets.260612:meshes/button_medium_opaque");
  LoadBuiltinMesh(
      BuiltinMeshID::kMeshesButtonMediumTransparent,
      "a-0.babuiltinassets.260612:meshes/button_medium_transparent");
  LoadBuiltinMesh(BuiltinMeshID::kMeshesButtonSmallOpaque,
                  "a-0.babuiltinassets.260612:meshes/button_small_opaque");
  LoadBuiltinMesh(BuiltinMeshID::kMeshesButtonSmallTransparent,
                  "a-0.babuiltinassets.260612:meshes/button_small_transparent");
  LoadBuiltinMesh(BuiltinMeshID::kMeshesButtonSquareOpaque,
                  "a-0.babuiltinassets.260612:meshes/button_square_opaque");
  LoadBuiltinMesh(
      BuiltinMeshID::kMeshesButtonSquareTransparent,
      "a-0.babuiltinassets.260612:meshes/button_square_transparent");
  LoadBuiltinMesh(BuiltinMeshID::kMeshesButtonTabOpaque,
                  "a-0.babuiltinassets.260612:meshes/button_tab_opaque");
  LoadBuiltinMesh(BuiltinMeshID::kMeshesButtonTabTransparent,
                  "a-0.babuiltinassets.260612:meshes/button_tab_transparent");
  LoadBuiltinMesh(BuiltinMeshID::kMeshesCheckTransparent,
                  "a-0.babuiltinassets.260612:meshes/check_transparent");
  LoadBuiltinMesh(BuiltinMeshID::kMeshesCrossOut,
                  "a-0.babuiltinassets.260612:meshes/cross_out");
  LoadBuiltinMesh(BuiltinMeshID::kMeshesCylinder,
                  "a-0.babuiltinassets.260612:meshes/cylinder");
  LoadBuiltinMesh(BuiltinMeshID::kMeshesEyeBall,
                  "a-0.babuiltinassets.260612:meshes/eye_ball");
  LoadBuiltinMesh(BuiltinMeshID::kMeshesEyeBallIris,
                  "a-0.babuiltinassets.260612:meshes/eye_ball_iris");
  LoadBuiltinMesh(BuiltinMeshID::kMeshesEyeLid,
                  "a-0.babuiltinassets.260612:meshes/eye_lid");
  LoadBuiltinMesh(BuiltinMeshID::kMeshesFlagPole,
                  "a-0.babuiltinassets.260612:meshes/flag_pole");
  LoadBuiltinMesh(BuiltinMeshID::kMeshesFlagStand,
                  "a-0.babuiltinassets.260612:meshes/flag_stand");
  LoadBuiltinMesh(BuiltinMeshID::kMeshesFlash,
                  "a-0.babuiltinassets.260612:meshes/flash");
  LoadBuiltinMesh(BuiltinMeshID::kMeshesHairTuft1,
                  "a-0.babuiltinassets.260612:meshes/hair_tuft1");
  LoadBuiltinMesh(BuiltinMeshID::kMeshesHairTuft1b,
                  "a-0.babuiltinassets.260612:meshes/hair_tuft1b");
  LoadBuiltinMesh(BuiltinMeshID::kMeshesHairTuft2,
                  "a-0.babuiltinassets.260612:meshes/hair_tuft2");
  LoadBuiltinMesh(BuiltinMeshID::kMeshesHairTuft3,
                  "a-0.babuiltinassets.260612:meshes/hair_tuft3");
  LoadBuiltinMesh(BuiltinMeshID::kMeshesHairTuft4,
                  "a-0.babuiltinassets.260612:meshes/hair_tuft4");
  LoadBuiltinMesh(BuiltinMeshID::kMeshesImage16x1,
                  "a-0.babuiltinassets.260612:meshes/image16x1");
  LoadBuiltinMesh(BuiltinMeshID::kMeshesImage1x1,
                  "a-0.babuiltinassets.260612:meshes/image1x1");
  LoadBuiltinMesh(BuiltinMeshID::kMeshesImage1x1FullScreen,
                  "a-0.babuiltinassets.260612:meshes/image1x1_full_screen");
  LoadBuiltinMesh(BuiltinMeshID::kMeshesImage1x1VrfullScreen,
                  "a-0.babuiltinassets.260612:meshes/image1x1_vrfull_screen");
  LoadBuiltinMesh(BuiltinMeshID::kMeshesImage2x1,
                  "a-0.babuiltinassets.260612:meshes/image2x1");
  LoadBuiltinMesh(BuiltinMeshID::kMeshesImage4x1,
                  "a-0.babuiltinassets.260612:meshes/image4x1");
  LoadBuiltinMesh(BuiltinMeshID::kMeshesLocator,
                  "a-0.babuiltinassets.260612:meshes/locator");
  LoadBuiltinMesh(BuiltinMeshID::kMeshesLocatorBox,
                  "a-0.babuiltinassets.260612:meshes/locator_box");
  LoadBuiltinMesh(BuiltinMeshID::kMeshesLocatorCircle,
                  "a-0.babuiltinassets.260612:meshes/locator_circle");
  LoadBuiltinMesh(BuiltinMeshID::kMeshesLocatorCircleOutline,
                  "a-0.babuiltinassets.260612:meshes/locator_circle_outline");
  LoadBuiltinMesh(BuiltinMeshID::kMeshesOverlayGuide,
                  "a-0.babuiltinassets.260612:meshes/overlay_guide");
  LoadBuiltinMesh(BuiltinMeshID::kMeshesScorch,
                  "a-0.babuiltinassets.260612:meshes/scorch");
  LoadBuiltinMesh(BuiltinMeshID::kMeshesScrollBarThumbOpaque,
                  "a-0.babuiltinassets.260612:meshes/scroll_bar_thumb_opaque");
  LoadBuiltinMesh(
      BuiltinMeshID::kMeshesScrollBarThumbShortOpaque,
      "a-0.babuiltinassets.260612:meshes/scroll_bar_thumb_short_opaque");
  LoadBuiltinMesh(
      BuiltinMeshID::kMeshesScrollBarThumbShortSimple,
      "a-0.babuiltinassets.260612:meshes/scroll_bar_thumb_short_simple");
  LoadBuiltinMesh(
      BuiltinMeshID::kMeshesScrollBarThumbShortTransparent,
      "a-0.babuiltinassets.260612:meshes/scroll_bar_thumb_short_transparent");
  LoadBuiltinMesh(BuiltinMeshID::kMeshesScrollBarThumbSimple,
                  "a-0.babuiltinassets.260612:meshes/scroll_bar_thumb_simple");
  LoadBuiltinMesh(
      BuiltinMeshID::kMeshesScrollBarThumbTransparent,
      "a-0.babuiltinassets.260612:meshes/scroll_bar_thumb_transparent");
  LoadBuiltinMesh(
      BuiltinMeshID::kMeshesScrollBarTroughTransparent,
      "a-0.babuiltinassets.260612:meshes/scroll_bar_trough_transparent");
  LoadBuiltinMesh(BuiltinMeshID::kMeshesShield,
                  "a-0.babuiltinassets.260612:meshes/shield");
  LoadBuiltinMesh(BuiltinMeshID::kMeshesShockWave,
                  "a-0.babuiltinassets.260612:meshes/shock_wave");
  LoadBuiltinMesh(BuiltinMeshID::kMeshesShrapnel1,
                  "a-0.babuiltinassets.260612:meshes/shrapnel1");
  LoadBuiltinMesh(BuiltinMeshID::kMeshesShrapnelBoard,
                  "a-0.babuiltinassets.260612:meshes/shrapnel_board");
  LoadBuiltinMesh(BuiltinMeshID::kMeshesShrapnelSlime,
                  "a-0.babuiltinassets.260612:meshes/shrapnel_slime");
  LoadBuiltinMesh(BuiltinMeshID::kMeshesSoftEdgeInside,
                  "a-0.babuiltinassets.260612:meshes/soft_edge_inside");
  LoadBuiltinMesh(BuiltinMeshID::kMeshesSoftEdgeOutside,
                  "a-0.babuiltinassets.260612:meshes/soft_edge_outside");
  LoadBuiltinMesh(BuiltinMeshID::kMeshesTextBoxTransparent,
                  "a-0.babuiltinassets.260612:meshes/text_box_transparent");
  LoadBuiltinMesh(BuiltinMeshID::kMeshesVrFade,
                  "a-0.babuiltinassets.260612:meshes/vr_fade");
  LoadBuiltinMesh(BuiltinMeshID::kMeshesVrOverlay,
                  "a-0.babuiltinassets.260612:meshes/vr_overlay");
  LoadBuiltinMesh(
      BuiltinMeshID::kMeshesWindowHsmallVmedOpaque,
      "a-0.babuiltinassets.260612:meshes/window_hsmall_vmed_opaque");
  LoadBuiltinMesh(
      BuiltinMeshID::kMeshesWindowHsmallVmedTransparent,
      "a-0.babuiltinassets.260612:meshes/window_hsmall_vmed_transparent");
  LoadBuiltinMesh(
      BuiltinMeshID::kMeshesWindowHsmallVsmallOpaque,
      "a-0.babuiltinassets.260612:meshes/window_hsmall_vsmall_opaque");
  LoadBuiltinMesh(
      BuiltinMeshID::kMeshesWindowHsmallVsmallTransparent,
      "a-0.babuiltinassets.260612:meshes/window_hsmall_vsmall_transparent");
  LoadBuiltinMesh(BuiltinMeshID::kMeshesWing,
                  "a-0.babuiltinassets.260612:meshes/wing");
  // __AUTOGENERATED_BUILTIN_ASSET_LOAD_END__

  sys_assets_loaded_ = true;
}

void Assets::PrintLoadInfo() {
  std::string s;
  char buffer[256];
  int num = 1;

  // Need to lock lists while iterating over them.
  AssetListLock lock;
  s = "Assets load results:  (all times in milliseconds):\n";
  snprintf(buffer, sizeof(buffer), "    %-50s %10s %10s", "FILE",
           "PRELOAD_TIME", "LOAD_TIME");
  s += buffer;
  g_core->logging->Log(LogName::kBaAssets, LogLevel::kInfo, s);
  millisecs_t total_preload_time = 0;
  millisecs_t total_load_time = 0;
  assert(asset_lists_locked_);
  for (auto&& i : meshes_) {
    millisecs_t preload_time = i.second->preload_time();
    millisecs_t load_time = i.second->load_time();
    total_preload_time += preload_time;
    total_load_time += load_time;
    snprintf(buffer, sizeof(buffer), "%-3d %-50s %10d %10d", num,
             i.second->GetName().c_str(),
             static_cast_check_fit<int>(preload_time),
             static_cast_check_fit<int>(load_time));
    g_core->logging->Log(LogName::kBaAssets, LogLevel::kInfo, buffer);
    num++;
  }
  assert(asset_lists_locked_);
  for (auto&& i : collision_meshes_) {
    millisecs_t preload_time = i.second->preload_time();
    millisecs_t load_time = i.second->load_time();
    total_preload_time += preload_time;
    total_load_time += load_time;
    snprintf(buffer, sizeof(buffer), "%-3d %-50s %10d %10d", num,
             i.second->GetName().c_str(),
             static_cast_check_fit<int>(preload_time),
             static_cast_check_fit<int>(load_time));
    g_core->logging->Log(LogName::kBaAssets, LogLevel::kInfo, buffer);
    num++;
  }
  assert(asset_lists_locked_);
  for (auto&& i : sounds_) {
    millisecs_t preload_time = i.second->preload_time();
    millisecs_t load_time = i.second->load_time();
    total_preload_time += preload_time;
    total_load_time += load_time;
    snprintf(buffer, sizeof(buffer), "%-3d %-50s %10d %10d", num,
             i.second->GetName().c_str(),
             static_cast_check_fit<int>(preload_time),
             static_cast_check_fit<int>(load_time));
    g_core->logging->Log(LogName::kBaAssets, LogLevel::kInfo, buffer);
    num++;
  }
  assert(asset_lists_locked_);
  for (auto&& i : datas_) {
    millisecs_t preload_time = i.second->preload_time();
    millisecs_t load_time = i.second->load_time();
    total_preload_time += preload_time;
    total_load_time += load_time;
    snprintf(buffer, sizeof(buffer), "%-3d %-50s %10d %10d", num,
             i.second->GetName().c_str(),
             static_cast_check_fit<int>(preload_time),
             static_cast_check_fit<int>(load_time));
    g_core->logging->Log(LogName::kBaAssets, LogLevel::kInfo, buffer);
    num++;
  }
  assert(asset_lists_locked_);
  for (auto&& i : textures_) {
    millisecs_t preload_time = i.second->preload_time();
    millisecs_t load_time = i.second->load_time();
    total_preload_time += preload_time;
    total_load_time += load_time;
    snprintf(buffer, sizeof(buffer), "%-3d %-50s %10d %10d", num,
             i.second->file_name_full().c_str(),
             static_cast_check_fit<int>(preload_time),
             static_cast_check_fit<int>(load_time));
    g_core->logging->Log(LogName::kBaAssets, LogLevel::kInfo, buffer);
    num++;
  }
  snprintf(buffer, sizeof(buffer),
           "Total preload time (loading data from disk): %i\nTotal load time "
           "(feeding data to OpenGL, etc): %i",
           static_cast<int>(total_preload_time),
           static_cast<int>(total_load_time));
  g_core->logging->Log(LogName::kBaAssets, LogLevel::kInfo, buffer);
}

void Assets::MarkAllAssetsForLoad() {
  assert(g_base->InLogicThread());

  // Need to keep lists locked while iterating over them.
  // (Re-queueing an asset that's already mid-pipeline is harmless; the
  // extra Preload()/Load() pass no-ops once it sees the state.)
  AssetListLock m_lock;
  for (auto&& i : textures_) {
    if (!i.second->preloaded()) {
      have_pending_loads_[static_cast<int>(AssetType::kTexture)] = true;
      MarkAssetForLoad(i.second.get());
    }
  }
  for (auto&& i : text_textures_) {
    if (!i.second->preloaded()) {
      have_pending_loads_[static_cast<int>(AssetType::kTexture)] = true;
      MarkAssetForLoad(i.second.get());
    }
  }
  for (auto&& i : qr_textures_) {
    if (!i.second->preloaded()) {
      have_pending_loads_[static_cast<int>(AssetType::kTexture)] = true;
      MarkAssetForLoad(i.second.get());
    }
  }
  for (auto&& i : meshes_) {
    if (!i.second->preloaded()) {
      have_pending_loads_[static_cast<int>(AssetType::kMesh)] = true;
      MarkAssetForLoad(i.second.get());
    }
  }
}

// Call this from the graphics thread to immediately unload all
// assets used by it. (for when GL context gets lost, etc).
void Assets::UnloadRendererBits(bool do_textures, bool do_meshes) {
  assert(g_base->app_adapter->InGraphicsContext());
  // need to keep lists locked while iterating over them..
  AssetListLock m_lock;
  if (do_textures) {
    assert(asset_lists_locked_);
    for (auto&& i : textures_) {
      i.second->Unload();
    }
    for (auto&& i : text_textures_) {
      i.second->Unload();
    }
    for (auto&& i : qr_textures_) {
      i.second->Unload();
    }
  }
  if (do_meshes) {
    for (auto&& i : meshes_) {
      i.second->Unload();
    }
  }
}

// Phase 1 (logic thread): re-resolve loaded textures/meshes and flag any
// whose underlying CAS blob changed (e.g. fallback -> ideal after a
// downloading asset-package resolve). FindAssetFile (used by ReResolveSource)
// is logic-thread-only, so the re-resolution must happen here; the actual GPU
// unload + reload runs on the graphics thread (UnloadReloadPendingRendererBits,
// kicked off below via the graphics server). No change -> no-op (the warm
// case). (Sound/audio flavors aren't handled here; they'd need an audio-thread
// unload path.)
void Assets::ReloadChangedAssets() {
  assert(g_base->InLogicThread());
  bool any{};
  {
    AssetListLock m_lock;
    for (auto&& i : textures_) {
      if (i.second->ReResolveSourceClaimed()) {
        i.second->set_reload_pending(true);
        any = true;
      }
    }
    for (auto&& i : meshes_) {
      if (i.second->ReResolveSourceClaimed()) {
        i.second->set_reload_pending(true);
        any = true;
      }
    }
  }
  if (any) {
    g_base->graphics_server->PushReloadChangedMediaCall();
  }
}

// Phase 2 (graphics thread): unload the renderer assets flagged for reload by
// ReloadChangedAssets() (re-resolution already happened there). Returns
// whether anything was unloaded.
auto Assets::UnloadReloadPendingRendererBits() -> bool {
  assert(g_base->app_adapter->InGraphicsContext());
  AssetListLock m_lock;
  bool any{};
  for (auto&& i : textures_) {
    if (i.second->reload_pending()) {
      i.second->Unload();
      i.second->set_reload_pending(false);
      any = true;
    }
  }
  for (auto&& i : meshes_) {
    if (i.second->reload_pending()) {
      i.second->Unload();
      i.second->set_reload_pending(false);
      any = true;
    }
  }
  return any;
}

auto Assets::GetMesh(const std::string& file_name) -> Object::Ref<MeshAsset> {
  // Anything handing us a possibly-legacy bare name (old peers over the
  // scene_v1 wire, old replays, modder code) gets routed to its
  // asset-package home if it has one (mirrors GetTexture's hook).
  return GetAsset(AssetNameCompat::FromLegacy(file_name, "meshes"), &meshes_);
}

auto Assets::GetSound(const std::string& file_name) -> Object::Ref<SoundAsset> {
  // Anything handing us a possibly-legacy bare name (old peers over the
  // scene_v1 wire, old replays, modder code) gets routed to its
  // asset-package home if it has one (mirrors GetTexture's hook).
  return GetAsset(AssetNameCompat::FromLegacy(file_name, "audio"), &sounds_);
}

auto Assets::GetDataAsset(const std::string& file_name)
    -> Object::Ref<DataAsset> {
  return GetAsset(file_name, &datas_);
}

auto Assets::GetCollisionMesh(const std::string& file_name)
    -> Object::Ref<CollisionMeshAsset> {
  // Same legacy-name routing as GetMesh above; collision meshes cross
  // the scene_v1 wire too (kAddCollisionMesh).
  return GetAsset(AssetNameCompat::FromLegacy(file_name, "meshes"),
                  &collision_meshes_);
}

template <typename T>
auto Assets::GetAsset(const std::string& file_name,
                      std::unordered_map<std::string, Object::Ref<T> >* c_list)
    -> Object::Ref<T> {
  assert(g_base->InLogicThread());
  assert(asset_lists_locked_);
  assert(asset_loads_allowed_);
  auto i = c_list->find(file_name);
  if (i != c_list->end()) {
    return Object::Ref<T>(i->second.get());
  } else {
    auto d(Object::New<T>(file_name));
    (*c_list)[file_name] = d;
    have_pending_loads_[static_cast<int>(d->GetAssetType())] = true;
    MarkAssetForLoad(d.get());
    d->set_last_used_time(g_core->AppTimeMillisecs());
    return Object::Ref<T>(d);
  }
}

auto Assets::GetTexture(TextPacker* packer) -> Object::Ref<TextureAsset> {
  assert(g_base->InLogicThread());
  assert(asset_lists_locked_);
  const std::string& hash(packer->hash());
  auto i = text_textures_.find(hash);
  if (i != text_textures_.end()) {
    return Object::Ref<TextureAsset>(i->second.get());
  } else {
    auto d{Object::New<TextureAsset>(packer)};
    text_textures_[hash] = d;
    have_pending_loads_[static_cast<int>(d->GetAssetType())] = true;
    MarkAssetForLoad(d.get());
    d->set_last_used_time(g_core->AppTimeMillisecs());
    return Object::Ref<TextureAsset>(d);
  }
}

auto Assets::GetQRCodeTexture(const std::string& url)
    -> Object::Ref<TextureAsset> {
  assert(g_base->InLogicThread());
  assert(asset_lists_locked_);
  auto i = qr_textures_.find(url);
  if (i != qr_textures_.end()) {
    return Object::Ref<TextureAsset>(i->second.get());
  } else {
    auto d(Object::New<TextureAsset>(url));
    qr_textures_[url] = d;
    have_pending_loads_[static_cast<int>(d->GetAssetType())] = true;
    MarkAssetForLoad(d.get());
    d->set_last_used_time(g_core->AppTimeMillisecs());
    return Object::Ref<TextureAsset>(d);
  }
}

// Eww can't recycle GetComponent here since we need extra stuff (tex-type arg)
// ..should fix.
auto Assets::GetCubeMapTexture(const std::string& file_name)
    -> Object::Ref<TextureAsset> {
  assert(g_base->InLogicThread());
  assert(asset_lists_locked_);
  auto i = textures_.find(file_name);
  if (i != textures_.end()) {
    return Object::Ref<TextureAsset>(i->second.get());
  } else {
    auto d(Object::New<TextureAsset>(file_name, TextureType::kCubeMap,
                                     TextureMinQuality::kLow));
    textures_[file_name] = d;
    have_pending_loads_[static_cast<int>(d->GetAssetType())] = true;
    MarkAssetForLoad(d.get());
    d->set_last_used_time(g_core->AppTimeMillisecs());
    return Object::Ref<TextureAsset>(d);
  }
}

// Eww; can't recycle GetComponent here since we need extra stuff (quality
// settings, etc). Should fix.
auto Assets::GetTexture(const std::string& file_name_in)
    -> Object::Ref<TextureAsset> {
  assert(g_base->InLogicThread());
  assert(asset_lists_locked_);
  // Anything handing us a possibly-legacy bare name (old peers over
  // the scene_v1 wire, old replays, server-driven docui content,
  // modder code) gets routed to its asset-package home if it has one.
  std::string file_name = AssetNameCompat::FromLegacy(file_name_in, "textures");
  auto i = textures_.find(file_name);
  if (i != textures_.end()) {
    return Object::Ref<TextureAsset>(i->second.get());
  } else {
    // (The old name-keyed min-quality map lived here; every entry in it
    // has migrated to asset-packages, which handle quality themselves —
    // asset-packages decision #18.)
    auto d(Object::New<TextureAsset>(file_name, TextureType::k2D,
                                     TextureMinQuality::kLow));
    textures_[file_name] = d;
    have_pending_loads_[static_cast<int>(d->GetAssetType())] = true;
    MarkAssetForLoad(d.get());
    d->set_last_used_time(g_core->AppTimeMillisecs());
    return Object::Ref<TextureAsset>(d);
  }
}

void Assets::MarkAssetForLoad(Asset* c) {
  assert(g_base->InLogicThread());

  // *allocate* a reference as a standalone pointer so we can be
  // sure this guy sticks around until it's been sent all the way
  // through the preload/load cycle. (since other threads will be touching it)
  // once it makes it back to us we can delete the ref (in
  // ClearPendingLoadsDoneList)

  auto asset_ref_ptr = new Object::Ref<Asset>(c);
  g_base->assets_server->PushPendingPreload(asset_ref_ptr);
}

#pragma clang diagnostic push
#pragma ide diagnostic ignored "UnreachableCode"
#pragma ide diagnostic ignored "ConstantFunctionResult"

auto Assets::GetMeshPendingLoadCount() -> int {
  if (!have_pending_loads_[static_cast<int>(AssetType::kMesh)]) {
    return 0;
  }
  AssetListLock lock;
  int total = GetAssetPendingLoadCount(&meshes_, AssetType::kMesh);
  if (total == 0) {
    // When fully loaded, stop counting.
    have_pending_loads_[static_cast<int>(AssetType::kMesh)] = false;
  }
  return total;
}

auto Assets::GetTexturePendingLoadCount() -> int {
  if (!have_pending_loads_[static_cast<int>(AssetType::kTexture)]) {
    return 0;
  }
  AssetListLock lock;
  int total = (GetAssetPendingLoadCount(&textures_, AssetType::kTexture)
               + GetAssetPendingLoadCount(&text_textures_, AssetType::kTexture)
               + GetAssetPendingLoadCount(&qr_textures_, AssetType::kTexture));
  if (total == 0) {
    // When fully loaded, stop counting.
    have_pending_loads_[static_cast<int>(AssetType::kTexture)] = false;
  }
  return total;
}

auto Assets::GetSoundPendingLoadCount() -> int {
  if (!have_pending_loads_[static_cast<int>(AssetType::kSound)]) {
    return 0;
  }
  AssetListLock lock;
  int total = GetAssetPendingLoadCount(&sounds_, AssetType::kSound);
  if (total == 0) {
    // When fully loaded, stop counting.
    have_pending_loads_[static_cast<int>(AssetType::kSound)] = false;
  }
  return total;
}

auto Assets::GetDataPendingLoadCount() -> int {
  if (!have_pending_loads_[static_cast<int>(AssetType::kData)]) {
    return 0;
  }
  AssetListLock lock;
  int total = GetAssetPendingLoadCount(&datas_, AssetType::kData);
  if (total == 0) {
    // When fully loaded, stop counting.
    have_pending_loads_[static_cast<int>(AssetType::kData)] = false;
  }
  return total;
}

auto Assets::GetCollisionMeshPendingLoadCount() -> int {
  if (!have_pending_loads_[static_cast<int>(AssetType::kCollisionMesh)]) {
    return 0;
  }
  AssetListLock lock;
  int total =
      GetAssetPendingLoadCount(&collision_meshes_, AssetType::kCollisionMesh);
  if (total == 0) {
    // When fully loaded, stop counting.
    have_pending_loads_[static_cast<int>(AssetType::kCollisionMesh)] = false;
  }
  return total;
}

#pragma clang diagnostic pop

auto Assets::GetGraphicalPendingLoadCount() -> int {
  // Each of these calls lock the asset-lists so we don't.
  return GetMeshPendingLoadCount() + GetTexturePendingLoadCount();
}

auto Assets::GetPendingLoadCount() -> int {
  // Each of these calls lock the asset-lists so we don't.
  return GetMeshPendingLoadCount() + GetTexturePendingLoadCount()
         + GetDataPendingLoadCount() + GetSoundPendingLoadCount()
         + GetCollisionMeshPendingLoadCount();
}

template <typename T>
auto Assets::GetAssetPendingLoadCount(
    std::unordered_map<std::string, Object::Ref<T> >* t_list, AssetType type)
    -> int {
  assert(g_base->InLogicThread());
  assert(asset_lists_locked_);

  int c = 0;
  for (auto&& i : (*t_list)) {
    if (i.second.exists()) {
      // Anything not at rest fully-loaded still counts as pending --
      // EXCEPT terminally-failed assets, which will never load; counting
      // those would wedge loading-progress consumers forever (their
      // failure already got an ERROR log at fail time).
      Asset::State s = i.second->state();
      if (s != Asset::State::kLoaded && s != Asset::State::kFailed) {
        c++;
      }
    }
  }
  return c;
}

// Runs the pending loads that need to run from the audio thread.
auto Assets::RunPendingAudioLoads() -> bool {
  assert(g_base->InAudioThread());
  return RunPendingLoadList(&pending_loads_sounds_);
}

// Runs the pending loads that need to run from the graphics thread.
auto Assets::RunPendingGraphicsLoads() -> bool {
  assert(g_base->app_adapter->InGraphicsContext());
  return RunPendingLoadList(&pending_loads_graphics_);
}

// Runs the pending loads that run in the main thread.  Also clears the list of
// done loads.
auto Assets::RunPendingLoadsLogicThread() -> bool {
  assert(g_base->InLogicThread());
  return RunPendingLoadList(&pending_loads_other_);
}

template <typename T>
auto Assets::RunPendingLoadList(std::vector<Object::Ref<T>*>* c_list) -> bool {
  millisecs_t starttime = g_core->AppTimeMillisecs();

  std::vector<Object::Ref<T>*> l;
  std::vector<Object::Ref<T>*> l_unfinished;
  std::vector<Object::Ref<T>*> l_finished;
  {
    std::scoped_lock lock(pending_load_list_mutex_);

    // Save time if there's nothing to load.
    if (c_list->empty()) {
      return false;
    }

    // Pull the contents of c_list and set it to empty.
    l.swap(*c_list);
  }

  // Run loads until the list is empty or we hit our per-call time budget.
  // We don't want to block the calling thread for long -- and even a quick
  // load here may add work on another thread (graphics/audio), so we keep our
  // slices short and finish the rest on a later call.
  bool out_of_time = false;
  for (auto&& ref : l) {
    if (out_of_time) {
      // Already over budget -- save this one for later.
      l_unfinished.push_back(ref);
      continue;
    }
    try {
      (**ref).Load();
    } catch (const std::exception& exc) {
      // A failed asset (it already published kFailed and ERROR-logged the
      // root cause). Treat it as finished so its queue ref gets cleaned
      // up properly instead of leaking mid-unwind; consumers see the
      // failure via the asset's state.
      g_core->logging->Log(
          LogName::kBaAssets, LogLevel::kError,
          std::string("Pending-load error (asset marked failed): ")
              + exc.what());
    }
    l_finished.push_back(ref);
    if (g_core->AppTimeMillisecs() - starttime > PENDING_LOAD_PROCESS_TIME) {
      out_of_time = true;
    }
  }
  l.swap(l_unfinished);

  // Now add unfinished ones back onto the original list and finished ones into
  // the done list.
  {
    std::scoped_lock lock(pending_load_list_mutex_);
    for (auto&& i : l) {
      c_list->push_back(i);
    }
    for (auto&& i : l_finished) {
      pending_loads_done_.push_back(i);
    }
  }

  // If we dumped anything on the pending loads done list, shake the logic
  // thread to tell it to kill the reference.
  if (!l_finished.empty()) {
    assert(g_base->logic);
    g_base->logic->event_loop()->PushCall(
        [] { g_base->assets->ClearPendingLoadsDoneList(); });
  }
  return (!l.empty());
}

void Assets::Prune(int level) {
  assert(g_base->InLogicThread());
  millisecs_t current_time = g_core->AppTimeMillisecs();

  // Need lists locked while accessing/modifying them.
  AssetListLock lock;

  // We can specify level for more aggressive pruning (during memory warnings
  // and whatnot).
  millisecs_t standard_asset_prune_time = STANDARD_ASSET_PRUNE_TIME;
  millisecs_t text_texture_prune_time = TEXT_TEXTURE_PRUNE_TIME;
  millisecs_t qr_texture_prune_time = QR_TEXTURE_PRUNE_TIME;
  switch (level) {
    case 1:
      standard_asset_prune_time = 120000;  // 2 min
      text_texture_prune_time = 1000;      // 1 sec
      qr_texture_prune_time = 1000;        // 1 sec
      break;
    case 2:
      standard_asset_prune_time = 30000;  // 30 sec
      text_texture_prune_time = 1000;     // 1 sec
      qr_texture_prune_time = 1000;       // 1 sec
      break;
    case 3:
      standard_asset_prune_time = 5000;  // 5 sec
      text_texture_prune_time = 1000;    // 1 sec
      qr_texture_prune_time = 1000;      // 1 sec
      break;
    default:
      break;
  }

  std::vector<Object::Ref<Asset>*> graphics_thread_unloads;
  std::vector<Object::Ref<Asset>*> audio_thread_unloads;

  assert(asset_lists_locked_);
  auto old_texture_count = textures_.size();
  auto old_text_texture_count = text_textures_.size();
  auto old_qr_texture_count = qr_textures_.size();
  auto old_mesh_count = meshes_.size();
  auto old_collision_mesh_count = collision_meshes_.size();
  auto old_sound_count = sounds_.size();

  // Prune textures.
  assert(asset_lists_locked_);
  for (auto i = textures_.begin(); i != textures_.end();) {
    TextureAsset* texture = i->second.get();
    // Attempt to prune if there are no references remaining except our own and
    // its been a while since it was used.
    if (current_time - texture->last_used_time() > standard_asset_prune_time
        && (texture->object_strong_ref_count() <= 1)) {
      Asset::State s = texture->state();
      if (Asset::IsTransientState(s)) {
        // Mid-claim with no outside refs should be impossible (pipeline
        // queues/frame-defs hold refs while driving assets); regardless,
        // never evict mid-work -- skip and let a later prune get it.
        assert(false);
        i++;
      } else if (texture->preloaded()) {
        // It holds payloads; the graphics thread must unload it before it
        // can die. Allocate a reference to keep it alive while the unload
        // is happening.
        graphics_thread_unloads.push_back(new Object::Ref<Asset>(texture));
        i = textures_.erase(i);
      } else {
        // No payloads (never preloaded, or terminally failed); can simply
        // evict. For failed assets this doubles as the retry mechanism: a
        // later fresh use re-creates the asset from scratch. (Note: the
        // old mutex-based code never advanced the iterator on this branch;
        // it was unreachable then but kFailed assets reach it now.)
        i = textures_.erase(i);
      }
    } else {
      i++;
    }
  }

  // Prune text-textures more aggressively since we may generate lots of them
  // FIXME - we may want to prune based on total number of these instead of
  //  time.
  assert(asset_lists_locked_);
  for (auto i = text_textures_.begin(); i != text_textures_.end();) {
    TextureAsset* texture = i->second.get();
    // Attempt to prune if there are no references remaining except our own and
    // its been a while since it was used.
    if (current_time - texture->last_used_time() > text_texture_prune_time
        && (texture->object_strong_ref_count() <= 1)) {
      Asset::State s = texture->state();
      if (Asset::IsTransientState(s)) {
        // See note in the standard-textures loop above.
        assert(false);
        i++;
      } else if (texture->preloaded()) {
        // Allocate a reference to keep this texture_data alive while the
        // graphics-thread unload is happening.
        graphics_thread_unloads.push_back(new Object::Ref<Asset>(texture));
        i = text_textures_.erase(i);
      } else {
        // No payloads; evict directly (see standard-textures loop).
        i = text_textures_.erase(i);
      }
    } else {
      i++;
    }
  }

  // Prune qr-textures.
  assert(asset_lists_locked_);
  for (auto i = qr_textures_.begin(); i != qr_textures_.end();) {
    TextureAsset* texture = i->second.get();
    // Attempt to prune if there are no references remaining except our own and
    // its been a while since it was used.
    if (current_time - texture->last_used_time() > qr_texture_prune_time
        && (texture->object_strong_ref_count() <= 1)) {
      Asset::State s = texture->state();
      if (Asset::IsTransientState(s)) {
        // See note in the standard-textures loop above.
        assert(false);
        i++;
      } else if (texture->preloaded()) {
        // Allocate a reference to keep this texture_data alive while the
        // graphics-thread unload is happening.
        graphics_thread_unloads.push_back(new Object::Ref<Asset>(texture));
        i = qr_textures_.erase(i);
      } else {
        // No payloads; evict directly (see standard-textures loop).
        i = qr_textures_.erase(i);
      }
    } else {
      i++;
    }
  }

  // Prune meshes.
  assert(asset_lists_locked_);
  for (auto i = meshes_.begin(); i != meshes_.end();) {
    MeshAsset* mesh = i->second.get();
    // Attempt to prune if there are no references remaining except our own and
    // its been a while since it was used.
    if (current_time - mesh->last_used_time() > standard_asset_prune_time
        && (mesh->object_strong_ref_count() <= 1)) {
      Asset::State s = mesh->state();
      if (Asset::IsTransientState(s)) {
        // See note in the standard-textures loop above.
        assert(false);
        i++;
      } else if (mesh->preloaded()) {
        // Allocate a reference to keep this mesh_data alive while the
        // graphics-thread unload is happening.
        graphics_thread_unloads.push_back(new Object::Ref<Asset>(mesh));
        i = meshes_.erase(i);
      } else {
        // No payloads; evict directly (see standard-textures loop).
        i = meshes_.erase(i);
      }
    } else {
      i++;
    }
  }

  // Prune collision-meshes.
  assert(asset_lists_locked_);
  for (auto i = collision_meshes_.begin(); i != collision_meshes_.end();) {
    CollisionMeshAsset* mesh = i->second.get();
    // Attempt to prune if there are no references remaining except our own and
    // its been a while since it was used.
    if (current_time - mesh->last_used_time() > standard_asset_prune_time
        && (mesh->object_strong_ref_count() <= 1)) {
      // We can unload it immediately since that happens here in the logic
      // thread.
      mesh->Unload();
      auto i_next = i;
      ++i_next;
      collision_meshes_.erase(i);
      i = i_next;
    } else {
      i++;
    }
  }

  // Prune sounds.
  // (DISABLED FOR NOW - getting AL errors; need to better determine which
  // sounds are still in active use by OpenAL and ensure references exist for
  // them somewhere while that is the case
  if (explicit_bool(false)) {
    assert(asset_lists_locked_);
    for (auto i = sounds_.begin(); i != sounds_.end();) {
      SoundAsset* sound = i->second.get();
      // Attempt to prune if there are no references remaining except our own
      // and its been a while since it was used.
      if (current_time - sound->last_used_time() > standard_asset_prune_time
          && (sound->object_strong_ref_count() <= 1)) {
        Asset::State s = sound->state();
        if (Asset::IsTransientState(s)) {
          // See note in the standard-textures loop above.
          assert(false);
          i++;
        } else if (sound->preloaded()) {
          // Allocate a reference to keep this sound_data alive while the
          // audio-thread unload is happening.
          audio_thread_unloads.push_back(new Object::Ref<Asset>(sound));
          i = sounds_.erase(i);
        } else {
          // No payloads; evict directly (see standard-textures loop).
          i = sounds_.erase(i);
        }
      } else {
        i++;
      }
    }
  }

  if (!graphics_thread_unloads.empty()) {
    g_base->graphics_server->PushComponentUnloadCall(graphics_thread_unloads);
  }
  if (!audio_thread_unloads.empty()) {
    g_base->audio_server->PushComponentUnloadCall(audio_thread_unloads);
  }

  if (kShowPruningInfo) {
    assert(asset_lists_locked_);
    if (textures_.size() != old_texture_count) {
      g_core->logging->Log(LogName::kBaAssets, LogLevel::kInfo,
                           "Textures pruned from "
                               + std::to_string(old_texture_count) + " to "
                               + std::to_string(textures_.size()));
    }
    if (text_textures_.size() != old_text_texture_count) {
      g_core->logging->Log(LogName::kBaAssets, LogLevel::kInfo,
                           "TextTextures pruned from "
                               + std::to_string(old_text_texture_count) + " to "
                               + std::to_string(text_textures_.size()));
    }
    if (qr_textures_.size() != old_qr_texture_count) {
      g_core->logging->Log(LogName::kBaAssets, LogLevel::kInfo,
                           "QrTextures pruned from "
                               + std::to_string(old_qr_texture_count) + " to "
                               + std::to_string(qr_textures_.size()));
    }
    if (meshes_.size() != old_mesh_count) {
      g_core->logging->Log(LogName::kBaAssets, LogLevel::kInfo,
                           "Meshes pruned from "
                               + std::to_string(old_mesh_count) + " to "
                               + std::to_string(meshes_.size()));
    }
    if (collision_meshes_.size() != old_collision_mesh_count) {
      g_core->logging->Log(LogName::kBaAssets, LogLevel::kInfo,
                           "CollisionMeshes pruned from "
                               + std::to_string(old_collision_mesh_count)
                               + " to "
                               + std::to_string(collision_meshes_.size()));
    }
    if (sounds_.size() != old_sound_count) {
      g_core->logging->Log(LogName::kBaAssets, LogLevel::kInfo,
                           "Sounds pruned from "
                               + std::to_string(old_sound_count) + " to "
                               + std::to_string(sounds_.size()));
    }
  }
}

auto Assets::FindAssetFile(FileType type, const std::string& name)
    -> std::string {
  std::string file_out;

  // We don't protect package-path access so make sure its always from here.
  assert(g_base->InLogicThread());

  // CAS-form qualified ref: ``<apverid>:<asset_name>``. Resolve via
  // the asset-package registry instead of searching the on-disk tree.
  // Bare names (no ``:``) fall through to the legacy path below.
  auto colon_pos = name.find(':');
  if (colon_pos != std::string::npos) {
    return FindAssetFileCas_(type, name, colon_pos);
  }

  const char* ext = "";
  const char* prefix = "";

  switch (type) {
    case FileType::kSound:
      if (g_core->HeadlessMode()) {
        return "headless_dummy_path.sound";
      }
      prefix = "audio/";
      ext = ".ogg";
      break;

    case FileType::kMesh:
      if (g_core->HeadlessMode()) {
        return "headless_dummy_path.mesh";
      }
      prefix = "meshes/";
      ext = ".bob";
      break;

    case FileType::kCollisionMesh:
      prefix = "meshes/";
      ext = ".cob";
      break;

    case FileType::kData:
      prefix = "data/";
      ext = ".json";
      break;

    case FileType::kCubeMapTexture:
    case FileType::kTexture: {
      // Legacy bare-name cube maps share the 2D texture path: the name
      // carries a '#' that expands to the six per-face file names at
      // preload, so prefix/ext handling is identical.
      if (g_core->HeadlessMode()) {
        if (strchr(name.c_str(), '#')) {
          return "headless_dummy_path#.nop";
        } else {
          return "headless_dummy_path.nop";
        }
      }

      // Make sure we know what compression/quality to use.
      assert(g_base->graphics->has_client_context());
      // assert(g_base->graphics_server
      //        &&
      //        g_base->graphics_server->texture_compression_types_are_set());
      // assert(g_base->graphics_server
      //        && g_base->graphics_server->texture_quality_set());
      prefix = "textures/";

#if BA_PLATFORM_ANDROID && !BA_ANDROID_DDS_BUILD
      // On most android builds we go for .ktx, which contains etc2 and etc1.
      ext = ".ktx";
#elif BA_PLATFORM_IOS_TVOS
      // On iOS we use pvr.
      ext = ".pvr";
#else
      // all else defaults to dds
      ext = ".dds";
#endif
      break;
    }
    default:
      break;
  }

  // Modder-override prefix: probe ``<type>2/`` before ``<type>/`` so
  // existing mods that drop assets into ``textures2/`` / ``audio2/``
  // / ``meshes2/`` keep working until they migrate to the
  // asset-package wrapper flow. Our builds never populate these dirs
  // — the probe is a no-op when absent. Remove once mod migration is
  // complete.
  std::string prefix_override;
  {
    std::string base_prefix(prefix);
    if (!base_prefix.empty() && base_prefix.back() == '/') {
      prefix_override = base_prefix.substr(0, base_prefix.size() - 1) + "2/";
    }
  }

  const std::vector<std::string>& asset_paths_used = asset_paths_;

  auto check_exists = [](const std::string& path) -> bool {
    // '#' denotes a cube map texture, which is actually 6 files.
    if (strchr(path.c_str(), '#')) {
      // Just look for one of them i guess.
      std::string tmp_name = path;
      tmp_name.replace(tmp_name.find('#'), 1, "_+x");
      return g_core->platform->FilePathExists(tmp_name);
    }
    return g_core->platform->FilePathExists(path);
  };

  for (auto&& i : asset_paths_used) {
    if (!prefix_override.empty()) {
      file_out = i + "/" + prefix_override + name + ext;
      if (check_exists(file_out)) {
        return file_out;
      }
    }
    file_out = i + "/" + prefix + name + ext;
    if (check_exists(file_out)) {
      return file_out;
    }
  }

  // We wanna fail gracefully for some types.
  if (type == FileType::kSound) {
    // The legacy bare-name blank sound is gone; fall back to the
    // builtin asset-package's copy.
    std::string fallback = std::string(kBuiltinAssetsApverid) + ":audio/blank";
    if (name != fallback) {
      g_core->logging->Log(LogName::kBaAssets, LogLevel::kError,
                           "Unable to load audio: '" + name + "'.");
      return FindAssetFile(type, fallback);
    }
  } else if (type == FileType::kTexture) {
    // The legacy bare-name white texture is gone; fall back to the
    // builtin asset-package's copy.
    std::string fallback =
        std::string(kBuiltinAssetsApverid) + ":textures/white";
    if (name != fallback) {
      g_core->logging->Log(LogName::kBaAssets, LogLevel::kError,
                           "Unable to load texture: '" + name + "'.");
      return FindAssetFile(type, fallback);
    }
  }

  throw Exception("Can't find asset: \"" + name + "\"");
}

auto Assets::FindAssetFileCas_(FileType type, const std::string& name,
                               size_t colon_pos) -> std::string {
  // Textures, cube maps, sounds, and meshes (display + collision) are
  // CAS-routed so far. Other asset categories land here as their
  // buckets come online (strings, fonts, etc.).
  if (type != FileType::kTexture && type != FileType::kCubeMapTexture
      && type != FileType::kSound && type != FileType::kMesh
      && type != FileType::kCollisionMesh) {
    throw Exception("CAS asset refs not yet supported for this asset type: '"
                    + name + "'");
  }

  // Collision meshes are the one kind headless builds genuinely load
  // (physics), so they skip the headless short-circuit below — their
  // bytes live in the flavor-invariant constant bucket, which every
  // build including headless resolves (decision #26).
  if (type == FileType::kCollisionMesh) {
    auto cob_path = FindCasCollisionMeshPath(name);
    if (cob_path.empty()) {
      throw Exception("Collision-mesh asset not found in package: '" + name
                      + "' (part=c).");
    }
    return cob_path;
  }

  // Headless builds use the NULL profiles; they don't actually load
  // texture/audio/display-mesh bytes. Match the legacy headless
  // short-circuits and return type-appropriate dummy paths so the stub
  // paths stay consistent.
  if (g_core->HeadlessMode()) {
    if (type == FileType::kSound) {
      return "headless_dummy_path.sound";
    }
    if (type == FileType::kMesh) {
      return "headless_dummy_path.mesh";
    }
    return "headless_dummy_path.nop";
  }

  if (type == FileType::kSound) {
    // Sounds are a single ogg-vorbis blob under part 'a' in the
    // package's audio bucket (decision #25).
    auto sound_path = FindCasSoundPath(name);
    if (sound_path.empty()) {
      throw Exception("Sound asset not found in package: '" + name
                      + "' (part=a).");
    }
    return sound_path;
  }

  if (type == FileType::kMesh) {
    // Display meshes are a single bob blob under part 'm' in the
    // package's meshes bucket (decision #26).
    auto mesh_path = FindCasMeshPath(name);
    if (mesh_path.empty()) {
      throw Exception("Mesh asset not found in package: '" + name
                      + "' (part=m).");
    }
    return mesh_path;
  }

  if (type == FileType::kCubeMapTexture) {
    // Cube maps are a single faceCount=6 KTX2 blob under part 't' in
    // the package's cube_map_textures bucket (decision #24).
    auto cube_path = FindCasCubeMapTexturePath(name);
    if (cube_path.empty()) {
      throw Exception("Cube-map asset not found in package: '" + name
                      + "' (part=t).");
    }
    return cube_path;
  }

  // Textures are single-part: their data lives under part 't'. (The
  // part-map machinery stays general for genuinely multi-file types;
  // textures dropped their placeholder 'j' sidecar — decision #16
  // follow-up.)
  auto path = FindCasTexturePartPath(name, "t");
  if (path.empty()) {
    throw Exception("Asset not found in package: '" + name + "' (part=t).");
  }
  return path;
}

auto Assets::FindCasTexturePartPath(const std::string& name,
                                    const std::string& part) -> std::string {
  assert(g_base->InLogicThread());

  auto colon_pos = name.find(':');
  if (colon_pos == std::string::npos) {
    return "";
  }

  // Headless builds use the NULL texture profile and never sample image
  // bytes; nothing to resolve here.
  if (g_core->HeadlessMode()) {
    return "";
  }

  std::string apverid = name.substr(0, colon_pos);
  std::string asset_name = name.substr(colon_pos + 1);

  // Look up the textures bucket THIS package actually resolved to,
  // rather than assuming a single global flavor. Different packages can
  // resolve differently (one downloads desktop_v1 BC7 while a builtin
  // falls back to its bundled fallback_v1), so we track the resolved
  // flavor per-package via the registry. All profiles ship as ``.ktx2``
  // (RGBA8 / BC7 / ASTC differ only by the container's vkFormat), so the
  // logical path's extension is uniform.
  std::string bucket_id = package_registry_.LookupTextureBucketId(apverid);
  if (bucket_id.empty()) {
    return "";
  }
  std::string logical_path = "ba_data/textures/" + asset_name + ".ktx2";

  auto hash =
      package_registry_.LookupAssetHash(apverid, bucket_id, logical_path, part);
  if (hash.empty()) {
    return "";
  }
  return package_registry_.CasBlobPath(hash);
}

auto Assets::FindCasCubeMapTexturePath(const std::string& name) -> std::string {
  assert(g_base->InLogicThread());

  auto colon_pos = name.find(':');
  if (colon_pos == std::string::npos) {
    return "";
  }

  // Headless builds use the NULL texture profile and never sample image
  // bytes; nothing to resolve here.
  if (g_core->HeadlessMode()) {
    return "";
  }

  std::string apverid = name.substr(0, colon_pos);
  std::string asset_name = name.substr(colon_pos + 1);

  // Mirror of the 2D lookup just above: find the cube_map_textures
  // bucket THIS package actually resolved to (decision #24; same
  // per-package flavor-tracking rationale). All profiles ship as
  // a single ``.ktx2`` per cube map (faceCount=6).
  std::string bucket_id =
      package_registry_.LookupCubeMapTextureBucketId(apverid);
  if (bucket_id.empty()) {
    return "";
  }
  std::string logical_path =
      "ba_data/cube_map_textures/" + asset_name + ".ktx2";

  auto hash =
      package_registry_.LookupAssetHash(apverid, bucket_id, logical_path, "t");
  if (hash.empty()) {
    return "";
  }
  return package_registry_.CasBlobPath(hash);
}

auto Assets::FindCasSoundPath(const std::string& name) -> std::string {
  assert(g_base->InLogicThread());

  auto colon_pos = name.find(':');
  if (colon_pos == std::string::npos) {
    return "";
  }

  // Headless builds use the NULL audio profile and never load audio
  // bytes; nothing to resolve here.
  if (g_core->HeadlessMode()) {
    return "";
  }

  std::string apverid = name.substr(0, colon_pos);
  std::string asset_name = name.substr(colon_pos + 1);

  // Mirror of the texture lookups above: find the audio bucket THIS
  // package actually resolved to (decision #25; same per-package
  // flavor-tracking rationale). All audio profiles ship a single
  // ``.ogg`` blob per sound under part 'a'.
  std::string bucket_id = package_registry_.LookupAudioBucketId(apverid);
  if (bucket_id.empty()) {
    return "";
  }
  std::string logical_path = "ba_data/audio/" + asset_name + ".ogg";

  auto hash =
      package_registry_.LookupAssetHash(apverid, bucket_id, logical_path, "a");
  if (hash.empty()) {
    return "";
  }
  return package_registry_.CasBlobPath(hash);
}

auto Assets::FindCasMeshPath(const std::string& name) -> std::string {
  assert(g_base->InLogicThread());

  auto colon_pos = name.find(':');
  if (colon_pos == std::string::npos) {
    return "";
  }

  // Headless builds use the NULL mesh profile and never load
  // display-mesh bytes; nothing to resolve here.
  if (g_core->HeadlessMode()) {
    return "";
  }

  std::string apverid = name.substr(0, colon_pos);
  std::string asset_name = name.substr(colon_pos + 1);

  // Mirror of the audio lookup above: find the meshes bucket THIS
  // package actually resolved to (decision #26). All mesh profiles
  // ship a single ``.bob`` blob per display mesh under part 'm'.
  std::string bucket_id = package_registry_.LookupMeshBucketId(apverid);
  if (bucket_id.empty()) {
    return "";
  }
  std::string logical_path = "ba_data/meshes/" + asset_name + ".bob";

  auto hash =
      package_registry_.LookupAssetHash(apverid, bucket_id, logical_path, "m");
  if (hash.empty()) {
    return "";
  }
  return package_registry_.CasBlobPath(hash);
}

auto Assets::FindCasCollisionMeshPath(const std::string& name) -> std::string {
  assert(g_base->InLogicThread());

  auto colon_pos = name.find(':');
  if (colon_pos == std::string::npos) {
    return "";
  }

  // NOTE: no headless short-circuit here — collision meshes are the
  // one kind headless genuinely loads; their bytes ride the
  // flavor-invariant constant bucket which every build resolves
  // (decision #26).

  std::string apverid = name.substr(0, colon_pos);
  std::string asset_name = name.substr(colon_pos + 1);

  std::string bucket_id = package_registry_.LookupConstantBucketId(apverid);
  if (bucket_id.empty()) {
    return "";
  }
  std::string logical_path = "ba_data/meshes/" + asset_name + ".cob";

  auto hash =
      package_registry_.LookupAssetHash(apverid, bucket_id, logical_path, "c");
  if (hash.empty()) {
    return "";
  }
  return package_registry_.CasBlobPath(hash);
}

auto Assets::PreferredTextureProfile() const -> std::string {
  // Debug override (BA_FORCE_TEXTURE_PROFILE): force a specific texture
  // profile regardless of platform/headless. Lets headless test runs
  // request a non-null flavor so the real multi-file (t+j) blob
  // download + write path can be exercised without a display.
  if (const char* forced = getenv("BA_FORCE_TEXTURE_PROFILE")) {
    if (forced[0] != 0) {
      return forced;
    }
  }

  // Headless has no renderer and never samples textures; only the NULL
  // texture flavor is bundled/needed there. (Also: graphics caps are
  // never set in headless, so we must not consult them.)
  if (g_core->HeadlessMode()) {
    return "null";
  }

  // Pick the flavor *family* by form factor, then let GPU capability decide
  // whether we get that family's compressed flavor or the universal
  // uncompressed fallback. Form factor -- not raw format support -- chooses
  // the family because a flavor bundles more than just its compression
  // (resolution, etc.); a desktop must never pull the mobile flavor just
  // because its GPU happens to expose ASTC, and vice versa.
  //
  // Debug override (BA_FORCE_TEXTURE_FORM_FACTOR=mobile|desktop): pretend to
  // be the given form factor. Lets a desktop machine -- e.g. a Mac, whose
  // ANGLE/Metal GPU exposes ASTC -- exercise the mobile/ASTC branch
  // end-to-end without a mobile device.
  bool mobile = g_buildconfig.platform_mobile();
  if (const char* ff = getenv("BA_FORCE_TEXTURE_FORM_FACTOR")) {
    if (std::string(ff) == "mobile") {
      mobile = true;
    } else if (std::string(ff) == "desktop") {
      mobile = false;
    }
  }

  // Caps come from the thread-safe mirror since we're on the logic thread;
  // it reads false until the graphics context has detected caps, so a
  // decision made before then safely lands on fallback rather than racing.
  // Both compressed profiles are decoded by the KTX2 loader.
  auto* gs = g_base->graphics_server;
  if (mobile) {
    // Mobile: ASTC LDR if the GPU exposes it, else the universal fallback.
    // iOS/tvOS always have ASTC; only a small, shrinking tail of older
    // Android GPUs lack it. We deliberately carry no ETC2 tier -- the
    // half-res uncompressed fallback lands at ~the same VRAM as full-res
    // ETC2-with-alpha, so those devices aren't materially worse off.
    if (gs->SupportsTextureCompressionTypeThreadsafe(
            TextureCompressionType::kASTC)) {
      return "mobile_v1";
    }
    return "fallback_v1";
  }

  // Desktop: BC7 (BPTC) if exposed -- essentially all desktop GPUs via
  // D3D11 (Windows/ANGLE), Metal (Mac/ANGLE), or modern GL (Linux) -- else
  // the universal fallback. Note a desktop GPU that exposes ASTC but not
  // BC7 (e.g. an Apple Silicon Mac on the desktop-GL fallback build, no
  // ANGLE) deliberately lands on fallback, not mobile: it's a desktop.
  if (gs->SupportsTextureCompressionTypeThreadsafe(
          TextureCompressionType::kBPTC)) {
    return "desktop_v1";
  }
  return "fallback_v1";
}

void Assets::AddPendingLoad(Object::Ref<Asset>* c) {
  switch ((**c).GetAssetType()) {
    case AssetType::kTexture:
    case AssetType::kMesh: {
      // Tell the graphics thread there's pending loads...
      std::scoped_lock lock(pending_load_list_mutex_);
      pending_loads_graphics_.push_back(c);
      break;
    }
    case AssetType::kSound: {
      // Tell the audio thread there's pending loads.
      {
        std::scoped_lock lock(pending_load_list_mutex_);
        pending_loads_sounds_.push_back(c);
      }
      g_base->audio_server->PushHavePendingLoadsCall();
      break;
    }
    default: {
      // Tell the logic thread there's pending loads.
      {
        std::scoped_lock lock(pending_load_list_mutex_);
        pending_loads_other_.push_back(c);
      }
      g_base->logic->event_loop()->PushCall(
          [] { g_base->logic->NotifyOfPendingAssetLoads(); });
      break;
    }
  }
}

void Assets::ClearPendingLoadsDoneList() {
  assert(g_base->InLogicThread());

  std::scoped_lock lock(pending_load_list_mutex_);

  // Our explicitly-allocated reference pointer has made it back to us here in
  // the logic thread.
  // We can now kill the reference knowing that it's safe for this component
  // to die at any time (anyone needing it to be alive now should be holding a
  // reference themselves).
  for (Object::Ref<Asset>* i : pending_loads_done_) {
    delete i;
  }
  pending_loads_done_.clear();
}

void Assets::AddPackage(const std::string& name, const std::string& path) {
  // We don't protect package-path access so make sure its always from here.
  assert(g_base->InLogicThread());
  if (g_buildconfig.debug_build()) {
    if (packages_.find(name) != packages_.end()) {
      g_core->logging->Log(LogName::kBaAssets, LogLevel::kWarning,
                           "adding duplicate package: '" + name + "'");
    }
  }
  packages_[name] = path;
}

void Assets::InitSpecialChars() {
  std::scoped_lock lock(special_char_mutex_);

  special_char_strings_[SpecialChar::kDownArrow] = "\xee\x80\x84";
  special_char_strings_[SpecialChar::kUpArrow] = "\xee\x80\x83";
  special_char_strings_[SpecialChar::kLeftArrow] = "\xee\x80\x81";
  special_char_strings_[SpecialChar::kRightArrow] = "\xee\x80\x82";
  special_char_strings_[SpecialChar::kTopButton] = "\xee\x80\x86";
  special_char_strings_[SpecialChar::kLeftButton] = "\xee\x80\x85";
  special_char_strings_[SpecialChar::kRightButton] = "\xee\x80\x87";
  special_char_strings_[SpecialChar::kBottomButton] = "\xee\x80\x88";
  special_char_strings_[SpecialChar::kDelete] = "\xee\x80\x89";
  special_char_strings_[SpecialChar::kShift] = "\xee\x80\x8A";
  special_char_strings_[SpecialChar::kBack] = "\xee\x80\x8B";
  special_char_strings_[SpecialChar::kLogoFlat] = "\xee\x80\x8C";
  special_char_strings_[SpecialChar::kRewindButton] = "\xee\x80\x8D";
  special_char_strings_[SpecialChar::kPlayPauseButton] = "\xee\x80\x8E";
  special_char_strings_[SpecialChar::kFastForwardButton] = "\xee\x80\x8F";
  special_char_strings_[SpecialChar::kDpadCenterButton] = "\xee\x80\x90";
  special_char_strings_[SpecialChar::kPlayStationCrossButton] = "\xee\x80\x91";
  special_char_strings_[SpecialChar::kPlayStationCircleButton] = "\xee\x80\x92";
  special_char_strings_[SpecialChar::kPlayStationTriangleButton] =
      "\xee\x80\x93";
  special_char_strings_[SpecialChar::kPlayStationSquareButton] = "\xee\x80\x94";
  special_char_strings_[SpecialChar::kPlayButton] = "\xee\x80\x95";
  special_char_strings_[SpecialChar::kPauseButton] = "\xee\x80\x96";
  special_char_strings_[SpecialChar::kClose] = "\xee\x80\x97";

  special_char_strings_[SpecialChar::kOuyaButtonO] = "\xee\x80\x99";
  special_char_strings_[SpecialChar::kOuyaButtonU] = "\xee\x80\x9A";
  special_char_strings_[SpecialChar::kOuyaButtonY] = "\xee\x80\x9B";
  special_char_strings_[SpecialChar::kOuyaButtonA] = "\xee\x80\x9C";
  special_char_strings_[SpecialChar::kToken] = "\xee\x80\x9D";
  special_char_strings_[SpecialChar::kLogo] = "\xee\x80\x9E";
  special_char_strings_[SpecialChar::kTicket] = "\xee\x80\x9F";
  special_char_strings_[SpecialChar::kGooglePlayGamesLogo] = "\xee\x80\xA0";
  special_char_strings_[SpecialChar::kGameCenterLogo] = "\xee\x80\xA1";
  special_char_strings_[SpecialChar::kDiceButton1] = "\xee\x80\xA2";
  special_char_strings_[SpecialChar::kDiceButton2] = "\xee\x80\xA3";
  special_char_strings_[SpecialChar::kDiceButton3] = "\xee\x80\xA4";
  special_char_strings_[SpecialChar::kDiceButton4] = "\xee\x80\xA5";
  special_char_strings_[SpecialChar::kDiscordLogo] = "\xee\x80\xA6";
  special_char_strings_[SpecialChar::kPartyIcon] = "\xee\x80\xA7";
  special_char_strings_[SpecialChar::kTestAccount] = "\xee\x80\xA8";
  special_char_strings_[SpecialChar::kTicketBacking] = "\xee\x80\xA9";
  special_char_strings_[SpecialChar::kTrophy1] = "\xee\x80\xAA";
  special_char_strings_[SpecialChar::kTrophy2] = "\xee\x80\xAB";
  special_char_strings_[SpecialChar::kTrophy3] = "\xee\x80\xAC";
  special_char_strings_[SpecialChar::kTrophy0a] = "\xee\x80\xAD";
  special_char_strings_[SpecialChar::kTrophy0b] = "\xee\x80\xAE";
  special_char_strings_[SpecialChar::kTrophy4] = "\xee\x80\xAF";
  special_char_strings_[SpecialChar::kLocalAccount] = "\xee\x80\xB0";
  special_char_strings_[SpecialChar::kExplodinaryLogo] = "\xee\x80\xB1";

  special_char_strings_[SpecialChar::kFlagUnitedStates] = "\xee\x80\xB2";
  special_char_strings_[SpecialChar::kFlagMexico] = "\xee\x80\xB3";
  special_char_strings_[SpecialChar::kFlagGermany] = "\xee\x80\xB4";
  special_char_strings_[SpecialChar::kFlagBrazil] = "\xee\x80\xB5";
  special_char_strings_[SpecialChar::kFlagRussia] = "\xee\x80\xB6";
  special_char_strings_[SpecialChar::kFlagChina] = "\xee\x80\xB7";
  special_char_strings_[SpecialChar::kFlagUnitedKingdom] = "\xee\x80\xB8";
  special_char_strings_[SpecialChar::kFlagCanada] = "\xee\x80\xB9";
  special_char_strings_[SpecialChar::kFlagIndia] = "\xee\x80\xBA";
  special_char_strings_[SpecialChar::kFlagJapan] = "\xee\x80\xBB";
  special_char_strings_[SpecialChar::kFlagFrance] = "\xee\x80\xBC";
  special_char_strings_[SpecialChar::kFlagIndonesia] = "\xee\x80\xBD";
  special_char_strings_[SpecialChar::kFlagItaly] = "\xee\x80\xBE";
  special_char_strings_[SpecialChar::kFlagSouthKorea] = "\xee\x80\xBF";
  special_char_strings_[SpecialChar::kFlagNetherlands] = "\xee\x81\x80";

  special_char_strings_[SpecialChar::kFedora] = "\xee\x81\x81";
  special_char_strings_[SpecialChar::kHal] = "\xee\x81\x82";
  special_char_strings_[SpecialChar::kCrown] = "\xee\x81\x83";
  special_char_strings_[SpecialChar::kYinYang] = "\xee\x81\x84";
  special_char_strings_[SpecialChar::kEyeBall] = "\xee\x81\x85";
  special_char_strings_[SpecialChar::kSkull] = "\xee\x81\x86";
  special_char_strings_[SpecialChar::kHeart] = "\xee\x81\x87";
  special_char_strings_[SpecialChar::kDragon] = "\xee\x81\x88";
  special_char_strings_[SpecialChar::kHelmet] = "\xee\x81\x89";
  special_char_strings_[SpecialChar::kMushroom] = "\xee\x81\x8A";

  special_char_strings_[SpecialChar::kNinjaStar] = "\xee\x81\x8B";
  special_char_strings_[SpecialChar::kVikingHelmet] = "\xee\x81\x8C";
  special_char_strings_[SpecialChar::kMoon] = "\xee\x81\x8D";
  special_char_strings_[SpecialChar::kSpider] = "\xee\x81\x8E";
  special_char_strings_[SpecialChar::kFireball] = "\xee\x81\x8F";

  special_char_strings_[SpecialChar::kFlagUnitedArabEmirates] = "\xee\x81\x90";
  special_char_strings_[SpecialChar::kFlagQatar] = "\xee\x81\x91";
  special_char_strings_[SpecialChar::kFlagEgypt] = "\xee\x81\x92";
  special_char_strings_[SpecialChar::kFlagKuwait] = "\xee\x81\x93";
  special_char_strings_[SpecialChar::kFlagAlgeria] = "\xee\x81\x94";
  special_char_strings_[SpecialChar::kFlagSaudiArabia] = "\xee\x81\x95";
  special_char_strings_[SpecialChar::kFlagMalaysia] = "\xee\x81\x96";
  special_char_strings_[SpecialChar::kFlagCzechRepublic] = "\xee\x81\x97";
  special_char_strings_[SpecialChar::kFlagAustralia] = "\xee\x81\x98";
  special_char_strings_[SpecialChar::kFlagSingapore] = "\xee\x81\x99";

  special_char_strings_[SpecialChar::kOculusLogo] = "\xee\x81\x9A";
  special_char_strings_[SpecialChar::kSteamLogo] = "\xee\x81\x9B";
  special_char_strings_[SpecialChar::kNvidiaLogo] = "\xee\x81\x9C";

  special_char_strings_[SpecialChar::kFlagIran] = "\xee\x81\x9D";
  special_char_strings_[SpecialChar::kFlagPoland] = "\xee\x81\x9E";
  special_char_strings_[SpecialChar::kFlagArgentina] = "\xee\x81\x9F";
  special_char_strings_[SpecialChar::kFlagPhilippines] = "\xee\x81\xA0";
  special_char_strings_[SpecialChar::kFlagChile] = "\xee\x81\xA1";

  special_char_strings_[SpecialChar::kMikirog] = "\xee\x81\xA2";
  special_char_strings_[SpecialChar::kV2Logo] = "\xee\x81\xA3";
  special_char_strings_[SpecialChar::kSantaHat] = "\xee\x81\xA4";
  special_char_strings_[SpecialChar::kPotato] = "\xee\x81\xA5";
  special_char_strings_[SpecialChar::kPalmTree] = "\xee\x81\xA6";
  special_char_strings_[SpecialChar::kBoxingGlove] = "\xee\x81\xA7";
}

void Assets::SetLanguageKeys(
    const std::unordered_map<std::string, std::string>& language) {
  assert(g_base->InLogicThread());
  {
    std::scoped_lock lock(language_mutex_);
    language_ = language;
  }
  // Log our unique change state so things that go inactive and stop
  // receiving callbacks can see if they're out of date if they become
  // active again.
  language_state_++;

  // Let some subsystems know that language has changed.
  if (auto* app_mode = g_base->app_mode()) {
    app_mode->LanguageChanged();
  }
  g_base->ui->LanguageChanged();
  g_base->graphics->LanguageChanged();
}

auto DoCompileResourceString(cJSON* obj) -> std::string {
  // NOTE: We currently talk to Python here so need to be sure
  // we're holding the GIL. Perhaps in the future we could handle this
  // stuff completely in C++ and be free of this limitation.
  assert(Python::HaveGIL());
  assert(obj != nullptr);

  std::string result;

  // If its got a "r" key, look it up as a resource.. (with optional fallback).
  cJSON* resource = cJSON_GetObjectItem(obj, "r");
  if (resource != nullptr) {
    if (!cJSON_IsString(resource)) {
      throw Exception("expected a string for resource");
    }
    // Look for fallback-resource.
    cJSON* fallback_resource = cJSON_GetObjectItem(obj, "f");
    cJSON* fallback_value = cJSON_GetObjectItem(obj, "fv");
    if (fallback_resource && !cJSON_IsString(fallback_resource)) {
      throw Exception("expected a string for fallback_resource");
    }
    if (fallback_value && !cJSON_IsString(fallback_value)) {
      throw Exception("expected a string for fallback_value");
    }
    result = g_base->python->GetResource(
        resource->valuestring,
        fallback_resource ? fallback_resource->valuestring : nullptr,
        fallback_value ? fallback_value->valuestring : nullptr);
  } else {
    // Apparently not a resource; lets try as a translation ("t" keys).
    cJSON* translate = cJSON_GetObjectItem(obj, "t");
    if (translate != nullptr) {
      if (!cJSON_IsArray(translate) || cJSON_GetArraySize(translate) != 2) {
        throw Exception("Expected a 2 member array for translate");
      }
      cJSON* category = cJSON_GetArrayItem(translate, 0);
      if (!cJSON_IsString(category)) {
        throw Exception(
            "First member of translate array (category) must be a string");
      }
      cJSON* value = cJSON_GetArrayItem(translate, 1);
      if (!cJSON_IsString(value)) {
        throw Exception(
            "Second member of translate array (value) must be a string");
      }
      result = g_base->python->GetTranslation(category->valuestring,
                                              value->valuestring);
    } else {
      // Lastly try it as a value ("value" or "v").
      // (can be useful for feeding explicit strings while still allowing
      // translated subs
      cJSON* value = cJSON_GetObjectItem(obj, "v");
      if (value != nullptr) {
        if (!cJSON_IsString(value)) {
          throw Exception("Expected a string for value");
        }
        result = value->valuestring;
      } else {
        throw Exception("no 'resource', 'translate', or 'value' keys found");
      }
    }
  }

  // Ok; now no matter what it was, see if it contains any subs and replace
  // them ("s").
  cJSON* subs = cJSON_GetObjectItem(obj, "s");
  if (subs != nullptr) {
    if (!cJSON_IsArray(subs)) {
      throw Exception("expected an array for 'subs'");
    }
    int subs_count = cJSON_GetArraySize(subs);
    for (int i = 0; i < subs_count; i++) {
      cJSON* sub = cJSON_GetArrayItem(subs, i);
      if (!cJSON_IsArray(sub) || cJSON_GetArraySize(sub) != 2) {
        throw Exception(
            "Invalid subs entry; expected length 2 list of sub/replacement.");
      }

      // First item should be a string.
      cJSON* key = cJSON_GetArrayItem(sub, 0);
      if (!cJSON_IsString(key)) {
        throw Exception("Sub keys must be strings.");
      }
      std::string s_key = key->valuestring;

      // Second item can be a string or a dict; if its a dict, we go
      // recursive.
      cJSON* value = cJSON_GetArrayItem(sub, 1);
      std::string s_val;
      if (cJSON_IsString(value)) {
        s_val = value->valuestring;
      } else if (cJSON_IsObject(value)) {
        s_val = DoCompileResourceString(value);
      } else {
        throw Exception("Sub values must be strings or dicts.");
      }

      // Replace *ALL* occurrences.
      //
      // FIXME: Using this simple logic, If our replace value contains our
      // search value we get an infinite loop. For now, just error in that
      // case.
      if (s_val.find(s_key) != std::string::npos) {
        throw Exception("Subs replace string cannot contain search string.");
      }
      while (true) {
        size_t pos = result.find(s_key);
        if (pos == std::string::npos) {
          break;
        }
        result.replace(pos, s_key.size(), s_val);
      }
    }
  }
  return result;
}

auto Assets::CompileResourceString(const std::string& s, bool* valid)
    -> std::string {
  bool dummyvalid;
  if (valid == nullptr) {
    valid = &dummyvalid;
  }

  // Quick out: if it doesn't start with a { and end with a }, treat it as a
  // literal and just return it as-is.
  if (s.size() < 2 || s[0] != '{' || s[s.size() - 1] != '}') {
    *valid = true;
    return s;
  }

  cJSON* root = cJSON_Parse(s.c_str());
  if (root && !cJSON_IsObject(root)) {
    cJSON_Delete(root);
    root = nullptr;
  }

  if (root == nullptr) {
    g_core->logging->Log(
        LogName::kBaAssets, LogLevel::kError,
        "CompileResourceString failed; invalid json: '" + s + "'");
    *valid = false;
    return "";
  }
  std::string result;
  try {
    result = DoCompileResourceString(root);
    *valid = true;
  } catch (const std::exception& e) {
    g_core->logging->Log(LogName::kBaAssets, LogLevel::kError,
                         "CompileResourceString failed: "
                             + std::string(e.what()) + "; str='" + s + "'");
    result = "<error>";
    *valid = false;
  }
  cJSON_Delete(root);
  return result;
}

auto Assets::GetResourceString(const std::string& key) -> std::string {
  std::string val;
  {
    std::scoped_lock lock(language_mutex_);
    auto i = language_.find(key);
    if (i != language_.end()) {
      val = i->second;
    }
  }
  return val;
}

auto Assets::CharStr(SpecialChar id) -> std::string {
  std::scoped_lock lock(special_char_mutex_);
  std::string val;
  auto i = special_char_strings_.find(id);
  if (i != special_char_strings_.end()) {
    val = i->second;
  } else {
    BA_LOG_PYTHON_TRACE_ONCE("invalid key in CharStr(): '"
                             + std::to_string(static_cast<int>(id)) + "'");
    val = "?";
  }
  return val;
}

Assets::AssetListLock::AssetListLock() {
  BA_DEBUG_FUNCTION_TIMER_BEGIN();
  g_base->assets->asset_lists_mutex_.lock();
  assert(!g_base->assets->asset_lists_locked_);
  g_base->assets->asset_lists_locked_ = true;
  BA_DEBUG_FUNCTION_TIMER_END_THREAD(20);
}

Assets::AssetListLock::~AssetListLock() {
  assert(g_base->assets->asset_lists_locked_);
  g_base->assets->asset_lists_locked_ = false;
  g_base->assets->asset_lists_mutex_.unlock();
}

auto Assets::BuiltinTexture(BuiltinTextureID id) -> TextureAsset* {
  assert(asset_loads_allowed_ && sys_assets_loaded_);
  assert(g_base->InLogicThread());
  assert(static_cast<size_t>(id) < builtin_textures_.size());
  return builtin_textures_[static_cast<int>(id)].get();
}

auto Assets::BuiltinCubeMapTexture(BuiltinCubeMapTextureID id)
    -> TextureAsset* {
  assert(asset_loads_allowed_ && sys_assets_loaded_);
  assert(g_base->InLogicThread());
  assert(static_cast<size_t>(id) < builtin_cube_map_textures_.size());
  return builtin_cube_map_textures_[static_cast<int>(id)].get();
}

auto Assets::IsValidBuiltinSound(BuiltinSoundID id) -> bool {
  return static_cast<size_t>(id) < builtin_sounds_.size();
}

auto Assets::BuiltinSound(BuiltinSoundID id) -> SoundAsset* {
  assert(asset_loads_allowed_ && sys_assets_loaded_);
  assert(g_base->InLogicThread());
  assert(IsValidBuiltinSound(id));
  return builtin_sounds_[static_cast<int>(id)].get();
}

auto Assets::BuiltinMesh(BuiltinMeshID id) -> MeshAsset* {
  assert(asset_loads_allowed_ && sys_assets_loaded_);
  assert(g_base->InLogicThread());
  assert(static_cast<size_t>(id) < builtin_meshes_.size());
  return builtin_meshes_[static_cast<int>(id)].get();
}

}  // namespace ballistica::base
