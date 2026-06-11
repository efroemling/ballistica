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

void Assets::LoadBuiltinSoundOld(BuiltinSoundOldID id, const char* name) {
  builtin_sounds_old_.push_back(GetSound(name));
  assert(builtin_sounds_old_.size() == static_cast<int>(id) + 1);
}

void Assets::LoadSystemData(SystemDataID id, const char* name) {
  system_datas_.push_back(GetDataAsset(name));
  assert(system_datas_.size() == static_cast<int>(id) + 1);
}

void Assets::LoadBuiltinMeshOld(BuiltinMeshOldID id, const char* name) {
  builtin_meshes_old_.push_back(GetMesh(name));
  assert(builtin_meshes_old_.size() == static_cast<int>(id) + 1);
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
  LoadBuiltinSoundOld(BuiltinSoundOldID::kDeek, "deek");
  LoadBuiltinSoundOld(BuiltinSoundOldID::kBlip, "blip");
  LoadBuiltinSoundOld(BuiltinSoundOldID::kBlank, "blank");
  LoadBuiltinSoundOld(BuiltinSoundOldID::kPunch, "punch01");
  LoadBuiltinSoundOld(BuiltinSoundOldID::kClick, "click01");
  LoadBuiltinSoundOld(BuiltinSoundOldID::kErrorBeep, "error");
  LoadBuiltinSoundOld(BuiltinSoundOldID::kSwish, "swish");
  LoadBuiltinSoundOld(BuiltinSoundOldID::kSwish2, "swish2");
  LoadBuiltinSoundOld(BuiltinSoundOldID::kSwish3, "swish3");
  LoadBuiltinSoundOld(BuiltinSoundOldID::kTap, "tap");
  LoadBuiltinSoundOld(BuiltinSoundOldID::kCorkPop, "corkPop");
  LoadBuiltinSoundOld(BuiltinSoundOldID::kGunCock, "gunCocking");
  LoadBuiltinSoundOld(BuiltinSoundOldID::kTickingCrazy, "tickingCrazy");
  LoadBuiltinSoundOld(BuiltinSoundOldID::kSparkle, "sparkle01");
  LoadBuiltinSoundOld(BuiltinSoundOldID::kSparkle2, "sparkle02");
  LoadBuiltinSoundOld(BuiltinSoundOldID::kSparkle3, "sparkle03");
  LoadBuiltinSoundOld(BuiltinSoundOldID::kScoreIncrease, "scoreIncrease");
  LoadBuiltinSoundOld(BuiltinSoundOldID::kCashRegister, "cashRegister");
  LoadBuiltinSoundOld(BuiltinSoundOldID::kPowerDown, "powerdown01");
  LoadBuiltinSoundOld(BuiltinSoundOldID::kDing, "ding");

  // System datas:
  // (crickets)

  // System meshes:
  LoadBuiltinMeshOld(BuiltinMeshOldID::kButtonSmallTransparent,
                     "buttonSmallTransparent");
  LoadBuiltinMeshOld(BuiltinMeshOldID::kButtonSmallOpaque, "buttonSmallOpaque");
  LoadBuiltinMeshOld(BuiltinMeshOldID::kButtonMediumTransparent,
                     "buttonMediumTransparent");
  LoadBuiltinMeshOld(BuiltinMeshOldID::kButtonMediumOpaque,
                     "buttonMediumOpaque");
  LoadBuiltinMeshOld(BuiltinMeshOldID::kButtonBackTransparent,
                     "buttonBackTransparent");
  LoadBuiltinMeshOld(BuiltinMeshOldID::kButtonBackOpaque, "buttonBackOpaque");
  LoadBuiltinMeshOld(BuiltinMeshOldID::kButtonBackSmallTransparent,
                     "buttonBackSmallTransparent");
  LoadBuiltinMeshOld(BuiltinMeshOldID::kButtonBackSmallOpaque,
                     "buttonBackSmallOpaque");
  LoadBuiltinMeshOld(BuiltinMeshOldID::kButtonTabTransparent,
                     "buttonTabTransparent");
  LoadBuiltinMeshOld(BuiltinMeshOldID::kButtonTabOpaque, "buttonTabOpaque");
  LoadBuiltinMeshOld(BuiltinMeshOldID::kButtonLargeTransparent,
                     "buttonLargeTransparent");
  LoadBuiltinMeshOld(BuiltinMeshOldID::kButtonLargeOpaque, "buttonLargeOpaque");
  LoadBuiltinMeshOld(BuiltinMeshOldID::kButtonLargerTransparent,
                     "buttonLargerTransparent");
  LoadBuiltinMeshOld(BuiltinMeshOldID::kButtonLargerOpaque,
                     "buttonLargerOpaque");
  LoadBuiltinMeshOld(BuiltinMeshOldID::kButtonSquareTransparent,
                     "buttonSquareTransparent");
  LoadBuiltinMeshOld(BuiltinMeshOldID::kButtonSquareOpaque,
                     "buttonSquareOpaque");
  LoadBuiltinMeshOld(BuiltinMeshOldID::kCheckTransparent, "checkTransparent");
  LoadBuiltinMeshOld(BuiltinMeshOldID::kScrollBarThumbTransparent,
                     "scrollBarThumbTransparent");
  LoadBuiltinMeshOld(BuiltinMeshOldID::kScrollBarThumbOpaque,
                     "scrollBarThumbOpaque");
  LoadBuiltinMeshOld(BuiltinMeshOldID::kScrollBarThumbSimple,
                     "scrollBarThumbSimple");
  LoadBuiltinMeshOld(BuiltinMeshOldID::kScrollBarThumbShortTransparent,
                     "scrollBarThumbShortTransparent");
  LoadBuiltinMeshOld(BuiltinMeshOldID::kScrollBarThumbShortOpaque,
                     "scrollBarThumbShortOpaque");
  LoadBuiltinMeshOld(BuiltinMeshOldID::kScrollBarThumbShortSimple,
                     "scrollBarThumbShortSimple");
  LoadBuiltinMeshOld(BuiltinMeshOldID::kScrollBarTroughTransparent,
                     "scrollBarTroughTransparent");
  LoadBuiltinMeshOld(BuiltinMeshOldID::kTextBoxTransparent,
                     "textBoxTransparent");
  LoadBuiltinMeshOld(BuiltinMeshOldID::kImage1x1, "image1x1");
  LoadBuiltinMeshOld(BuiltinMeshOldID::kImage1x1FullScreen,
                     "image1x1FullScreen");
  LoadBuiltinMeshOld(BuiltinMeshOldID::kImage2x1, "image2x1");
  LoadBuiltinMeshOld(BuiltinMeshOldID::kImage4x1, "image4x1");
  LoadBuiltinMeshOld(BuiltinMeshOldID::kImage16x1, "image16x1");
#if BA_VR_BUILD
  LoadBuiltinMeshOld(BuiltinMeshOldID::kImage1x1VRFullScreen,
                     "image1x1VRFullScreen");
  LoadBuiltinMeshOld(BuiltinMeshOldID::kVROverlay, "vrOverlay");
  LoadBuiltinMeshOld(BuiltinMeshOldID::kVRFade, "vrFade");
#endif  // BA_VR_BUILD
  LoadBuiltinMeshOld(BuiltinMeshOldID::kOverlayGuide, "overlayGuide");
  LoadBuiltinMeshOld(BuiltinMeshOldID::kWindowHSmallVMedTransparent,
                     "windowHSmallVMedTransparent");
  LoadBuiltinMeshOld(BuiltinMeshOldID::kWindowHSmallVMedOpaque,
                     "windowHSmallVMedOpaque");
  LoadBuiltinMeshOld(BuiltinMeshOldID::kWindowHSmallVSmallTransparent,
                     "windowHSmallVSmallTransparent");
  LoadBuiltinMeshOld(BuiltinMeshOldID::kWindowHSmallVSmallOpaque,
                     "windowHSmallVSmallOpaque");
  LoadBuiltinMeshOld(BuiltinMeshOldID::kSoftEdgeOutside, "softEdgeOutside");
  LoadBuiltinMeshOld(BuiltinMeshOldID::kSoftEdgeInside, "softEdgeInside");
  LoadBuiltinMeshOld(BuiltinMeshOldID::kBoxingGlove, "boxingGlove");
  LoadBuiltinMeshOld(BuiltinMeshOldID::kShield, "shield");
  LoadBuiltinMeshOld(BuiltinMeshOldID::kFlagPole, "flagPole");
  LoadBuiltinMeshOld(BuiltinMeshOldID::kFlagStand, "flagStand");
  LoadBuiltinMeshOld(BuiltinMeshOldID::kScorch, "scorch");
  LoadBuiltinMeshOld(BuiltinMeshOldID::kEyeBall, "eyeBall");
  LoadBuiltinMeshOld(BuiltinMeshOldID::kEyeBallIris, "eyeBallIris");
  LoadBuiltinMeshOld(BuiltinMeshOldID::kEyeLid, "eyeLid");
  LoadBuiltinMeshOld(BuiltinMeshOldID::kHairTuft1, "hairTuft1");
  LoadBuiltinMeshOld(BuiltinMeshOldID::kHairTuft1b, "hairTuft1b");
  LoadBuiltinMeshOld(BuiltinMeshOldID::kHairTuft2, "hairTuft2");
  LoadBuiltinMeshOld(BuiltinMeshOldID::kHairTuft3, "hairTuft3");
  LoadBuiltinMeshOld(BuiltinMeshOldID::kHairTuft4, "hairTuft4");
  LoadBuiltinMeshOld(BuiltinMeshOldID::kShrapnel1, "shrapnel1");
  LoadBuiltinMeshOld(BuiltinMeshOldID::kShrapnelSlime, "shrapnelSlime");
  LoadBuiltinMeshOld(BuiltinMeshOldID::kShrapnelBoard, "shrapnelBoard");
  LoadBuiltinMeshOld(BuiltinMeshOldID::kShockWave, "shockWave");
  LoadBuiltinMeshOld(BuiltinMeshOldID::kFlash, "flash");
  LoadBuiltinMeshOld(BuiltinMeshOldID::kCylinder, "cylinder");
  LoadBuiltinMeshOld(BuiltinMeshOldID::kArrowFront, "arrowFront");
  LoadBuiltinMeshOld(BuiltinMeshOldID::kArrowBack, "arrowBack");
  LoadBuiltinMeshOld(BuiltinMeshOldID::kActionButtonLeft, "actionButtonLeft");
  LoadBuiltinMeshOld(BuiltinMeshOldID::kActionButtonTop, "actionButtonTop");
  LoadBuiltinMeshOld(BuiltinMeshOldID::kActionButtonRight, "actionButtonRight");
  LoadBuiltinMeshOld(BuiltinMeshOldID::kActionButtonBottom,
                     "actionButtonBottom");
  LoadBuiltinMeshOld(BuiltinMeshOldID::kBox, "box");
  LoadBuiltinMeshOld(BuiltinMeshOldID::kLocator, "locator");
  LoadBuiltinMeshOld(BuiltinMeshOldID::kLocatorBox, "locatorBox");
  LoadBuiltinMeshOld(BuiltinMeshOldID::kLocatorCircle, "locatorCircle");
  LoadBuiltinMeshOld(BuiltinMeshOldID::kLocatorCircleOutline,
                     "locatorCircleOutline");
  LoadBuiltinMeshOld(BuiltinMeshOldID::kCrossOut, "crossOut");
  LoadBuiltinMeshOld(BuiltinMeshOldID::kWing, "wing");

  // CAS-backed builtin loads. The block below is auto-generated;
  // each line corresponds to one entry in ``BuiltinTextureID`` /
  // ``BuiltinSoundID`` / ``BuiltinMeshID`` / ``BuiltinCubeMapTextureID``
  // in base.h. Rerun ``make update`` to regenerate.
  // __AUTOGENERATED_BUILTIN_ASSET_LOAD_BEGIN__
  // textures
  LoadBuiltinTexture(BuiltinTextureID::kTexturesActionButtons,
                     "a-0.babuiltinassets.260611:textures/action_buttons");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesArrow,
                     "a-0.babuiltinassets.260611:textures/arrow");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesBackIcon,
                     "a-0.babuiltinassets.260611:textures/back_icon");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesBlack,
                     "a-0.babuiltinassets.260611:textures/black");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesBombButton,
                     "a-0.babuiltinassets.260611:textures/bomb_button");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesBoxingGlovesColor,
                     "a-0.babuiltinassets.260611:textures/boxing_gloves_color");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesButtonSquare,
                     "a-0.babuiltinassets.260611:textures/button_square");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesButtonSquareWide,
                     "a-0.babuiltinassets.260611:textures/button_square_wide");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesCharacterIconMask,
                     "a-0.babuiltinassets.260611:textures/character_icon_mask");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesCircle,
                     "a-0.babuiltinassets.260611:textures/circle");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesCircleNoAlpha,
                     "a-0.babuiltinassets.260611:textures/circle_no_alpha");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesCircleOutline,
                     "a-0.babuiltinassets.260611:textures/circle_outline");
  LoadBuiltinTexture(
      BuiltinTextureID::kTexturesCircleOutlineNoAlpha,
      "a-0.babuiltinassets.260611:textures/circle_outline_no_alpha");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesCircleShadow,
                     "a-0.babuiltinassets.260611:textures/circle_shadow");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesCircleSoft,
                     "a-0.babuiltinassets.260611:textures/circle_soft");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesCursor,
                     "a-0.babuiltinassets.260611:textures/cursor");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesExplosion,
                     "a-0.babuiltinassets.260611:textures/explosion");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesEyeColor,
                     "a-0.babuiltinassets.260611:textures/eye_color");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesEyeColorTintMask,
                     "a-0.babuiltinassets.260611:textures/eye_color_tint_mask");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesFlagPoleColor,
                     "a-0.babuiltinassets.260611:textures/flag_pole_color");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesFontBig,
                     "a-0.babuiltinassets.260611:textures/font_big");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesFontExtras,
                     "a-0.babuiltinassets.260611:textures/font_extras");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesFontExtras2,
                     "a-0.babuiltinassets.260611:textures/font_extras2");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesFontExtras3,
                     "a-0.babuiltinassets.260611:textures/font_extras3");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesFontExtras4,
                     "a-0.babuiltinassets.260611:textures/font_extras4");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesFontExtras5,
                     "a-0.babuiltinassets.260611:textures/font_extras5");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesFontSmall0,
                     "a-0.babuiltinassets.260611:textures/font_small0");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesFontSmall1,
                     "a-0.babuiltinassets.260611:textures/font_small1");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesFontSmall2,
                     "a-0.babuiltinassets.260611:textures/font_small2");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesFontSmall3,
                     "a-0.babuiltinassets.260611:textures/font_small3");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesFontSmall4,
                     "a-0.babuiltinassets.260611:textures/font_small4");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesFontSmall5,
                     "a-0.babuiltinassets.260611:textures/font_small5");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesFontSmall6,
                     "a-0.babuiltinassets.260611:textures/font_small6");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesFontSmall7,
                     "a-0.babuiltinassets.260611:textures/font_small7");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesFuse,
                     "a-0.babuiltinassets.260611:textures/fuse");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesGlow,
                     "a-0.babuiltinassets.260611:textures/glow");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesLight,
                     "a-0.babuiltinassets.260611:textures/light");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesLightSharp,
                     "a-0.babuiltinassets.260611:textures/light_sharp");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesLightSoft,
                     "a-0.babuiltinassets.260611:textures/light_soft");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesMenuButton,
                     "a-0.babuiltinassets.260611:textures/menu_button");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesNub,
                     "a-0.babuiltinassets.260611:textures/nub");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesOuyaAbutton,
                     "a-0.babuiltinassets.260611:textures/ouya_abutton");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesPageLeftRight,
                     "a-0.babuiltinassets.260611:textures/page_left_right");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesRgbStripes,
                     "a-0.babuiltinassets.260611:textures/rgb_stripes");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesScorch,
                     "a-0.babuiltinassets.260611:textures/scorch");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesScorchBig,
                     "a-0.babuiltinassets.260611:textures/scorch_big");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesScrollWidget,
                     "a-0.babuiltinassets.260611:textures/scroll_widget");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesScrollWidgetGlow,
                     "a-0.babuiltinassets.260611:textures/scroll_widget_glow");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesShadow,
                     "a-0.babuiltinassets.260611:textures/shadow");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesShadowSharp,
                     "a-0.babuiltinassets.260611:textures/shadow_sharp");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesShadowSoft,
                     "a-0.babuiltinassets.260611:textures/shadow_soft");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesShield,
                     "a-0.babuiltinassets.260611:textures/shield");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesShrapnel1Color,
                     "a-0.babuiltinassets.260611:textures/shrapnel1_color");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesSmoke,
                     "a-0.babuiltinassets.260611:textures/smoke");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesSoftRect,
                     "a-0.babuiltinassets.260611:textures/soft_rect");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesSoftRect2,
                     "a-0.babuiltinassets.260611:textures/soft_rect2");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesSoftRectVertical,
                     "a-0.babuiltinassets.260611:textures/soft_rect_vertical");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesSparks,
                     "a-0.babuiltinassets.260611:textures/sparks");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesSpinner,
                     "a-0.babuiltinassets.260611:textures/spinner");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesSpinner0,
                     "a-0.babuiltinassets.260611:textures/spinner0");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesSpinner1,
                     "a-0.babuiltinassets.260611:textures/spinner1");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesSpinner10,
                     "a-0.babuiltinassets.260611:textures/spinner10");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesSpinner11,
                     "a-0.babuiltinassets.260611:textures/spinner11");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesSpinner2,
                     "a-0.babuiltinassets.260611:textures/spinner2");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesSpinner3,
                     "a-0.babuiltinassets.260611:textures/spinner3");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesSpinner4,
                     "a-0.babuiltinassets.260611:textures/spinner4");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesSpinner5,
                     "a-0.babuiltinassets.260611:textures/spinner5");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesSpinner6,
                     "a-0.babuiltinassets.260611:textures/spinner6");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesSpinner7,
                     "a-0.babuiltinassets.260611:textures/spinner7");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesSpinner8,
                     "a-0.babuiltinassets.260611:textures/spinner8");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesSpinner9,
                     "a-0.babuiltinassets.260611:textures/spinner9");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesStartButton,
                     "a-0.babuiltinassets.260611:textures/start_button");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesTextClearButton,
                     "a-0.babuiltinassets.260611:textures/text_clear_button");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesTouchArrows,
                     "a-0.babuiltinassets.260611:textures/touch_arrows");
  LoadBuiltinTexture(
      BuiltinTextureID::kTexturesTouchArrowsActions,
      "a-0.babuiltinassets.260611:textures/touch_arrows_actions");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesUiAtlas,
                     "a-0.babuiltinassets.260611:textures/ui_atlas");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesUiAtlas2,
                     "a-0.babuiltinassets.260611:textures/ui_atlas2");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesUsersButton,
                     "a-0.babuiltinassets.260611:textures/users_button");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesWhite,
                     "a-0.babuiltinassets.260611:textures/white");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesWindowHsmallVmed,
                     "a-0.babuiltinassets.260611:textures/window_hsmall_vmed");
  LoadBuiltinTexture(
      BuiltinTextureID::kTexturesWindowHsmallVsmall,
      "a-0.babuiltinassets.260611:textures/window_hsmall_vsmall");
  LoadBuiltinTexture(BuiltinTextureID::kTexturesWings,
                     "a-0.babuiltinassets.260611:textures/wings");
  // cube_map_textures
  LoadBuiltinCubeMapTexture(
      BuiltinCubeMapTextureID::kTexturesReflectionChar,
      "a-0.babuiltinassets.260611:textures/reflection_char");
  LoadBuiltinCubeMapTexture(
      BuiltinCubeMapTextureID::kTexturesReflectionPowerup,
      "a-0.babuiltinassets.260611:textures/reflection_powerup");
  LoadBuiltinCubeMapTexture(
      BuiltinCubeMapTextureID::kTexturesReflectionSharp,
      "a-0.babuiltinassets.260611:textures/reflection_sharp");
  LoadBuiltinCubeMapTexture(
      BuiltinCubeMapTextureID::kTexturesReflectionSharper,
      "a-0.babuiltinassets.260611:textures/reflection_sharper");
  LoadBuiltinCubeMapTexture(
      BuiltinCubeMapTextureID::kTexturesReflectionSharpest,
      "a-0.babuiltinassets.260611:textures/reflection_sharpest");
  LoadBuiltinCubeMapTexture(
      BuiltinCubeMapTextureID::kTexturesReflectionSoft,
      "a-0.babuiltinassets.260611:textures/reflection_soft");
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
  AssetListLock m_lock;
  for (auto&& i : textures_) {
    if (!i.second->preloaded()) {
      Asset::LockGuard lock(i.second.get());
      have_pending_loads_[static_cast<int>(AssetType::kTexture)] = true;
      MarkAssetForLoad(i.second.get());
    }
  }
  for (auto&& i : text_textures_) {
    if (!i.second->preloaded()) {
      Asset::LockGuard lock(i.second.get());
      have_pending_loads_[static_cast<int>(AssetType::kTexture)] = true;
      MarkAssetForLoad(i.second.get());
    }
  }
  for (auto&& i : qr_textures_) {
    if (!i.second->preloaded()) {
      Asset::LockGuard lock(i.second.get());
      have_pending_loads_[static_cast<int>(AssetType::kTexture)] = true;
      MarkAssetForLoad(i.second.get());
    }
  }
  for (auto&& i : meshes_) {
    if (!i.second->preloaded()) {
      Asset::LockGuard lock(i.second.get());
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
      Asset::LockGuard lock(i.second.get());
      i.second->Unload(true);
    }
    for (auto&& i : text_textures_) {
      Asset::LockGuard lock(i.second.get());
      i.second->Unload(true);
    }
    for (auto&& i : qr_textures_) {
      Asset::LockGuard lock(i.second.get());
      i.second->Unload(true);
    }
  }
  if (do_meshes) {
    for (auto&& i : meshes_) {
      Asset::LockGuard lock(i.second.get());
      i.second->Unload(true);
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
      Asset::LockGuard lock(i.second.get());
      if (i.second->loaded() && i.second->ReResolveSource()) {
        i.second->set_reload_pending(true);
        any = true;
      }
    }
    for (auto&& i : meshes_) {
      Asset::LockGuard lock(i.second.get());
      if (i.second->loaded() && i.second->ReResolveSource()) {
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
    Asset::LockGuard lock(i.second.get());
    if (i.second->reload_pending()) {
      i.second->Unload(true);
      i.second->set_reload_pending(false);
      any = true;
    }
  }
  for (auto&& i : meshes_) {
    Asset::LockGuard lock(i.second.get());
    if (i.second->reload_pending()) {
      i.second->Unload(true);
      i.second->set_reload_pending(false);
      any = true;
    }
  }
  return any;
}

auto Assets::GetMesh(const std::string& file_name) -> Object::Ref<MeshAsset> {
  return GetAsset(file_name, &meshes_);
}

auto Assets::GetSound(const std::string& file_name) -> Object::Ref<SoundAsset> {
  return GetAsset(file_name, &sounds_);
}

auto Assets::GetDataAsset(const std::string& file_name)
    -> Object::Ref<DataAsset> {
  return GetAsset(file_name, &datas_);
}

auto Assets::GetCollisionMesh(const std::string& file_name)
    -> Object::Ref<CollisionMeshAsset> {
  return GetAsset(file_name, &collision_meshes_);
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
    {
      Asset::LockGuard lock(d.get());
      have_pending_loads_[static_cast<int>(d->GetAssetType())] = true;
      MarkAssetForLoad(d.get());
    }
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
    {
      Asset::LockGuard lock(d.get());
      have_pending_loads_[static_cast<int>(d->GetAssetType())] = true;
      MarkAssetForLoad(d.get());
    }
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
    {
      Asset::LockGuard lock(d.get());
      have_pending_loads_[static_cast<int>(d->GetAssetType())] = true;
      MarkAssetForLoad(d.get());
    }
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
    {
      Asset::LockGuard lock(d.get());
      have_pending_loads_[static_cast<int>(d->GetAssetType())] = true;
      MarkAssetForLoad(d.get());
    }
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
  std::string file_name = AssetNameCompat::FromLegacy(file_name_in);
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
    {
      Asset::LockGuard lock(d.get());
      have_pending_loads_[static_cast<int>(d->GetAssetType())] = true;
      MarkAssetForLoad(d.get());
    }
    d->set_last_used_time(g_core->AppTimeMillisecs());
    return Object::Ref<TextureAsset>(d);
  }
}

void Assets::MarkAssetForLoad(Asset* c) {
  assert(g_base->InLogicThread());

  assert(c->locked());

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
      if (i.second->TryLock()) {
        Asset::LockGuard lock(i.second.get(),
                              Asset::LockGuard::Type::kInheritLock);
        if (!i.second->loaded()) {
          c++;
        }
      } else {
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
    (**ref).Load();
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
      // If its preloaded/loaded we need to ask the graphics thread to unload it
      // first.
      if (texture->preloaded()) {
        // Allocate a reference to keep this texture_data alive while the unload
        // is happening.
        graphics_thread_unloads.push_back(new Object::Ref<Asset>(texture));
        auto i_next = i;
        i_next++;
        textures_.erase(i);
        i = i_next;
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
      // If its preloaded/loaded we need to ask the graphics thread to unload it
      // first.
      if (texture->preloaded()) {
        // Allocate a reference to keep this texture_data alive while the unload
        // is happening.
        graphics_thread_unloads.push_back(new Object::Ref<Asset>(texture));
        auto i_next = i;
        i_next++;
        text_textures_.erase(i);
        i = i_next;
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
      // If its preloaded/loaded we need to ask the graphics thread to unload it
      // first.
      if (texture->preloaded()) {
        // Allocate a reference to keep this texture_data alive while the unload
        // is happening.
        graphics_thread_unloads.push_back(new Object::Ref<Asset>(texture));
        auto i_next = i;
        i_next++;
        qr_textures_.erase(i);
        i = i_next;
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
      // If its preloaded/loaded we need to ask the graphics thread to unload it
      // first.
      if (mesh->preloaded()) {
        // Allocate a reference to keep this mesh_data alive while the unload
        // is happening.
        graphics_thread_unloads.push_back(new Object::Ref<Asset>(mesh));
        auto i_next = i;
        i_next++;
        meshes_.erase(i);
        i = i_next;
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
        // If its preloaded/loaded we need to ask the audio thread to unload
        // it first.
        if (sound->preloaded()) {
          // Allocate a reference to keep this sound_data alive while the unload
          // is happening.
          audio_thread_unloads.push_back(new Object::Ref<Asset>(sound));
          auto i_next = i;
          i_next++;
          sounds_.erase(i);
          i = i_next;
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
  if (type == FileType::kSound && name != "blank") {
    g_core->logging->Log(LogName::kBaAssets, LogLevel::kError,
                         "Unable to load audio: '" + name + "'.");
    return FindAssetFile(type, "blank");
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
  // Textures, cube maps, and sounds are CAS-routed so far. Other asset
  // categories land here as their buckets come online (strings, meshes,
  // etc.).
  if (type != FileType::kTexture && type != FileType::kCubeMapTexture
      && type != FileType::kSound) {
    throw Exception("CAS asset refs not yet supported for this asset type: '"
                    + name + "'");
  }

  // Headless builds use the NULL profiles; they don't actually load
  // texture/audio bytes. Match the legacy headless short-circuits and
  // return type-appropriate dummy paths so the stub paths stay
  // consistent.
  if (g_core->HeadlessMode()) {
    if (type == FileType::kSound) {
      return "headless_dummy_path.sound";
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

auto Assets::IsValidBuiltinSoundOld(BuiltinSoundOldID id) -> bool {
  return static_cast<size_t>(id) < builtin_sounds_old_.size();
}

auto Assets::BuiltinSoundOld(BuiltinSoundOldID id) -> SoundAsset* {
  assert(asset_loads_allowed_ && sys_assets_loaded_);
  assert(g_base->InLogicThread());
  assert(IsValidBuiltinSoundOld(id));
  return builtin_sounds_old_[static_cast<int>(id)].get();
}

auto Assets::BuiltinMeshOld(BuiltinMeshOldID id) -> MeshAsset* {
  assert(asset_loads_allowed_ && sys_assets_loaded_);
  assert(g_base->InLogicThread());
  assert(static_cast<size_t>(id) < builtin_meshes_old_.size());
  return builtin_meshes_old_[static_cast<int>(id)].get();
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
