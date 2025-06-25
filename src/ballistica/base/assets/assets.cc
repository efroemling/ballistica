// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/assets/assets.h"

#include <cstdio>
#include <set>
#include <string>
#include <unordered_map>
#include <vector>

#include "ballistica/base/app_adapter/app_adapter.h"
#include "ballistica/base/app_mode/app_mode.h"
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
#include "ballistica/core/platform/core_platform.h"
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

void Assets::LoadSystemTexture(SysTextureID id, const char* name) {
  assert(asset_lists_locked_);
  system_textures_.push_back(GetTexture(name));
  assert(system_textures_.size() == static_cast<int>(id) + 1);
}

void Assets::LoadSystemCubeMapTexture(SysCubeMapTextureID id,
                                      const char* name) {
  assert(asset_lists_locked_);
  system_cube_map_textures_.push_back(GetCubeMapTexture(name));
  assert(system_cube_map_textures_.size() == static_cast<int>(id) + 1);
}

void Assets::LoadSystemSound(SysSoundID id, const char* name) {
  system_sounds_.push_back(GetSound(name));
  assert(system_sounds_.size() == static_cast<int>(id) + 1);
}

void Assets::LoadSystemData(SystemDataID id, const char* name) {
  system_datas_.push_back(GetDataAsset(name));
  assert(system_datas_.size() == static_cast<int>(id) + 1);
}

void Assets::LoadSystemMesh(SysMeshID id, const char* name) {
  system_meshes_.push_back(GetMesh(name));
  assert(system_meshes_.size() == static_cast<int>(id) + 1);
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

  // Just grab the lock once for all this stuff for efficiency.
  AssetListLock lock;

  // System textures:
  LoadSystemTexture(SysTextureID::kUIAtlas, "uiAtlas");
  LoadSystemTexture(SysTextureID::kButtonSquare, "buttonSquare");
  LoadSystemTexture(SysTextureID::kWhite, "white");
  LoadSystemTexture(SysTextureID::kFontSmall0, "fontSmall0");
  LoadSystemTexture(SysTextureID::kFontBig, "fontBig");
  LoadSystemTexture(SysTextureID::kCursor, "cursor");
  LoadSystemTexture(SysTextureID::kBoxingGlove, "boxingGlovesColor");
  LoadSystemTexture(SysTextureID::kShield, "shield");
  LoadSystemTexture(SysTextureID::kExplosion, "explosion");
  LoadSystemTexture(SysTextureID::kTextClearButton, "textClearButton");
  LoadSystemTexture(SysTextureID::kWindowHSmallVMed, "windowHSmallVMed");
  LoadSystemTexture(SysTextureID::kWindowHSmallVSmall, "windowHSmallVSmall");
  LoadSystemTexture(SysTextureID::kGlow, "glow");
  LoadSystemTexture(SysTextureID::kScrollWidget, "scrollWidget");
  LoadSystemTexture(SysTextureID::kScrollWidgetGlow, "scrollWidgetGlow");
  LoadSystemTexture(SysTextureID::kFlagPole, "flagPoleColor");
  LoadSystemTexture(SysTextureID::kScorch, "scorch");
  LoadSystemTexture(SysTextureID::kScorchBig, "scorchBig");
  LoadSystemTexture(SysTextureID::kShadow, "shadow");
  LoadSystemTexture(SysTextureID::kLight, "light");
  LoadSystemTexture(SysTextureID::kShadowSharp, "shadowSharp");
  LoadSystemTexture(SysTextureID::kLightSharp, "lightSharp");
  LoadSystemTexture(SysTextureID::kShadowSoft, "shadowSoft");
  LoadSystemTexture(SysTextureID::kLightSoft, "lightSoft");
  LoadSystemTexture(SysTextureID::kSparks, "sparks");
  LoadSystemTexture(SysTextureID::kEye, "eyeColor");
  LoadSystemTexture(SysTextureID::kEyeTint, "eyeColorTintMask");
  LoadSystemTexture(SysTextureID::kFuse, "fuse");
  LoadSystemTexture(SysTextureID::kShrapnel1, "shrapnel1Color");
  LoadSystemTexture(SysTextureID::kSmoke, "smoke");
  LoadSystemTexture(SysTextureID::kCircle, "circle");
  LoadSystemTexture(SysTextureID::kCircleOutline, "circleOutline");
  LoadSystemTexture(SysTextureID::kCircleNoAlpha, "circleNoAlpha");
  LoadSystemTexture(SysTextureID::kCircleOutlineNoAlpha,
                    "circleOutlineNoAlpha");
  LoadSystemTexture(SysTextureID::kCircleShadow, "circleShadow");
  LoadSystemTexture(SysTextureID::kSoftRect, "softRect");
  LoadSystemTexture(SysTextureID::kSoftRect2, "softRect2");
  LoadSystemTexture(SysTextureID::kSoftRectVertical, "softRectVertical");
  LoadSystemTexture(SysTextureID::kStartButton, "startButton");
  LoadSystemTexture(SysTextureID::kBombButton, "bombButton");
  LoadSystemTexture(SysTextureID::kOuyaAButton, "ouyaAButton");
  LoadSystemTexture(SysTextureID::kBackIcon, "backIcon");
  LoadSystemTexture(SysTextureID::kNub, "nub");
  LoadSystemTexture(SysTextureID::kArrow, "arrow");
  LoadSystemTexture(SysTextureID::kMenuButton, "menuButton");
  LoadSystemTexture(SysTextureID::kUsersButton, "usersButton");
  LoadSystemTexture(SysTextureID::kActionButtons, "actionButtons");
  LoadSystemTexture(SysTextureID::kTouchArrows, "touchArrows");
  LoadSystemTexture(SysTextureID::kTouchArrowsActions, "touchArrowsActions");
  LoadSystemTexture(SysTextureID::kRGBStripes, "rgbStripes");
  LoadSystemTexture(SysTextureID::kUIAtlas2, "uiAtlas2");
  LoadSystemTexture(SysTextureID::kFontSmall1, "fontSmall1");
  LoadSystemTexture(SysTextureID::kFontSmall2, "fontSmall2");
  LoadSystemTexture(SysTextureID::kFontSmall3, "fontSmall3");
  LoadSystemTexture(SysTextureID::kFontSmall4, "fontSmall4");
  LoadSystemTexture(SysTextureID::kFontSmall5, "fontSmall5");
  LoadSystemTexture(SysTextureID::kFontSmall6, "fontSmall6");
  LoadSystemTexture(SysTextureID::kFontSmall7, "fontSmall7");
  LoadSystemTexture(SysTextureID::kFontExtras, "fontExtras");
  LoadSystemTexture(SysTextureID::kFontExtras2, "fontExtras2");
  LoadSystemTexture(SysTextureID::kFontExtras3, "fontExtras3");
  LoadSystemTexture(SysTextureID::kFontExtras4, "fontExtras4");
  LoadSystemTexture(SysTextureID::kCharacterIconMask, "characterIconMask");
  LoadSystemTexture(SysTextureID::kBlack, "black");
  LoadSystemTexture(SysTextureID::kWings, "wings");
  LoadSystemTexture(SysTextureID::kSpinner, "spinner");
  LoadSystemTexture(SysTextureID::kSpinner0, "spinner0");
  LoadSystemTexture(SysTextureID::kSpinner1, "spinner1");
  LoadSystemTexture(SysTextureID::kSpinner2, "spinner2");
  LoadSystemTexture(SysTextureID::kSpinner3, "spinner3");
  LoadSystemTexture(SysTextureID::kSpinner4, "spinner4");
  LoadSystemTexture(SysTextureID::kSpinner5, "spinner5");
  LoadSystemTexture(SysTextureID::kSpinner6, "spinner6");
  LoadSystemTexture(SysTextureID::kSpinner7, "spinner7");
  LoadSystemTexture(SysTextureID::kSpinner8, "spinner8");
  LoadSystemTexture(SysTextureID::kSpinner9, "spinner9");
  LoadSystemTexture(SysTextureID::kSpinner10, "spinner10");
  LoadSystemTexture(SysTextureID::kSpinner11, "spinner11");

  // System cube map textures:
  LoadSystemCubeMapTexture(SysCubeMapTextureID::kReflectionChar,
                           "reflectionChar#");
  LoadSystemCubeMapTexture(SysCubeMapTextureID::kReflectionPowerup,
                           "reflectionPowerup#");
  LoadSystemCubeMapTexture(SysCubeMapTextureID::kReflectionSoft,
                           "reflectionSoft#");
  LoadSystemCubeMapTexture(SysCubeMapTextureID::kReflectionSharp,
                           "reflectionSharp#");
  LoadSystemCubeMapTexture(SysCubeMapTextureID::kReflectionSharper,
                           "reflectionSharper#");
  LoadSystemCubeMapTexture(SysCubeMapTextureID::kReflectionSharpest,
                           "reflectionSharpest#");

  // System sounds:
  LoadSystemSound(SysSoundID::kDeek, "deek");
  LoadSystemSound(SysSoundID::kBlip, "blip");
  LoadSystemSound(SysSoundID::kBlank, "blank");
  LoadSystemSound(SysSoundID::kPunch, "punch01");
  LoadSystemSound(SysSoundID::kClick, "click01");
  LoadSystemSound(SysSoundID::kErrorBeep, "error");
  LoadSystemSound(SysSoundID::kSwish, "swish");
  LoadSystemSound(SysSoundID::kSwish2, "swish2");
  LoadSystemSound(SysSoundID::kSwish3, "swish3");
  LoadSystemSound(SysSoundID::kTap, "tap");
  LoadSystemSound(SysSoundID::kCorkPop, "corkPop");
  LoadSystemSound(SysSoundID::kGunCock, "gunCocking");
  LoadSystemSound(SysSoundID::kTickingCrazy, "tickingCrazy");
  LoadSystemSound(SysSoundID::kSparkle, "sparkle01");
  LoadSystemSound(SysSoundID::kSparkle2, "sparkle02");
  LoadSystemSound(SysSoundID::kSparkle3, "sparkle03");
  LoadSystemSound(SysSoundID::kScoreIncrease, "scoreIncrease");
  LoadSystemSound(SysSoundID::kCashRegister, "cashRegister");
  LoadSystemSound(SysSoundID::kPowerDown, "powerdown01");
  LoadSystemSound(SysSoundID::kDing, "ding");

  // System datas:
  // (crickets)

  // System meshes:
  LoadSystemMesh(SysMeshID::kButtonSmallTransparent, "buttonSmallTransparent");
  LoadSystemMesh(SysMeshID::kButtonSmallOpaque, "buttonSmallOpaque");
  LoadSystemMesh(SysMeshID::kButtonMediumTransparent,
                 "buttonMediumTransparent");
  LoadSystemMesh(SysMeshID::kButtonMediumOpaque, "buttonMediumOpaque");
  LoadSystemMesh(SysMeshID::kButtonBackTransparent, "buttonBackTransparent");
  LoadSystemMesh(SysMeshID::kButtonBackOpaque, "buttonBackOpaque");
  LoadSystemMesh(SysMeshID::kButtonBackSmallTransparent,
                 "buttonBackSmallTransparent");
  LoadSystemMesh(SysMeshID::kButtonBackSmallOpaque, "buttonBackSmallOpaque");
  LoadSystemMesh(SysMeshID::kButtonTabTransparent, "buttonTabTransparent");
  LoadSystemMesh(SysMeshID::kButtonTabOpaque, "buttonTabOpaque");
  LoadSystemMesh(SysMeshID::kButtonLargeTransparent, "buttonLargeTransparent");
  LoadSystemMesh(SysMeshID::kButtonLargeOpaque, "buttonLargeOpaque");
  LoadSystemMesh(SysMeshID::kButtonLargerTransparent,
                 "buttonLargerTransparent");
  LoadSystemMesh(SysMeshID::kButtonLargerOpaque, "buttonLargerOpaque");
  LoadSystemMesh(SysMeshID::kButtonSquareTransparent,
                 "buttonSquareTransparent");
  LoadSystemMesh(SysMeshID::kButtonSquareOpaque, "buttonSquareOpaque");
  LoadSystemMesh(SysMeshID::kCheckTransparent, "checkTransparent");
  LoadSystemMesh(SysMeshID::kScrollBarThumbTransparent,
                 "scrollBarThumbTransparent");
  LoadSystemMesh(SysMeshID::kScrollBarThumbOpaque, "scrollBarThumbOpaque");
  LoadSystemMesh(SysMeshID::kScrollBarThumbSimple, "scrollBarThumbSimple");
  LoadSystemMesh(SysMeshID::kScrollBarThumbShortTransparent,
                 "scrollBarThumbShortTransparent");
  LoadSystemMesh(SysMeshID::kScrollBarThumbShortOpaque,
                 "scrollBarThumbShortOpaque");
  LoadSystemMesh(SysMeshID::kScrollBarThumbShortSimple,
                 "scrollBarThumbShortSimple");
  LoadSystemMesh(SysMeshID::kScrollBarTroughTransparent,
                 "scrollBarTroughTransparent");
  LoadSystemMesh(SysMeshID::kTextBoxTransparent, "textBoxTransparent");
  LoadSystemMesh(SysMeshID::kImage1x1, "image1x1");
  LoadSystemMesh(SysMeshID::kImage1x1FullScreen, "image1x1FullScreen");
  LoadSystemMesh(SysMeshID::kImage2x1, "image2x1");
  LoadSystemMesh(SysMeshID::kImage4x1, "image4x1");
  LoadSystemMesh(SysMeshID::kImage16x1, "image16x1");
#if BA_VR_BUILD
  LoadSystemMesh(SysMeshID::kImage1x1VRFullScreen, "image1x1VRFullScreen");
  LoadSystemMesh(SysMeshID::kVROverlay, "vrOverlay");
  LoadSystemMesh(SysMeshID::kVRFade, "vrFade");
#endif  // BA_VR_BUILD
  LoadSystemMesh(SysMeshID::kOverlayGuide, "overlayGuide");
  LoadSystemMesh(SysMeshID::kWindowHSmallVMedTransparent,
                 "windowHSmallVMedTransparent");
  LoadSystemMesh(SysMeshID::kWindowHSmallVMedOpaque, "windowHSmallVMedOpaque");
  LoadSystemMesh(SysMeshID::kWindowHSmallVSmallTransparent,
                 "windowHSmallVSmallTransparent");
  LoadSystemMesh(SysMeshID::kWindowHSmallVSmallOpaque,
                 "windowHSmallVSmallOpaque");
  LoadSystemMesh(SysMeshID::kSoftEdgeOutside, "softEdgeOutside");
  LoadSystemMesh(SysMeshID::kSoftEdgeInside, "softEdgeInside");
  LoadSystemMesh(SysMeshID::kBoxingGlove, "boxingGlove");
  LoadSystemMesh(SysMeshID::kShield, "shield");
  LoadSystemMesh(SysMeshID::kFlagPole, "flagPole");
  LoadSystemMesh(SysMeshID::kFlagStand, "flagStand");
  LoadSystemMesh(SysMeshID::kScorch, "scorch");
  LoadSystemMesh(SysMeshID::kEyeBall, "eyeBall");
  LoadSystemMesh(SysMeshID::kEyeBallIris, "eyeBallIris");
  LoadSystemMesh(SysMeshID::kEyeLid, "eyeLid");
  LoadSystemMesh(SysMeshID::kHairTuft1, "hairTuft1");
  LoadSystemMesh(SysMeshID::kHairTuft1b, "hairTuft1b");
  LoadSystemMesh(SysMeshID::kHairTuft2, "hairTuft2");
  LoadSystemMesh(SysMeshID::kHairTuft3, "hairTuft3");
  LoadSystemMesh(SysMeshID::kHairTuft4, "hairTuft4");
  LoadSystemMesh(SysMeshID::kShrapnel1, "shrapnel1");
  LoadSystemMesh(SysMeshID::kShrapnelSlime, "shrapnelSlime");
  LoadSystemMesh(SysMeshID::kShrapnelBoard, "shrapnelBoard");
  LoadSystemMesh(SysMeshID::kShockWave, "shockWave");
  LoadSystemMesh(SysMeshID::kFlash, "flash");
  LoadSystemMesh(SysMeshID::kCylinder, "cylinder");
  LoadSystemMesh(SysMeshID::kArrowFront, "arrowFront");
  LoadSystemMesh(SysMeshID::kArrowBack, "arrowBack");
  LoadSystemMesh(SysMeshID::kActionButtonLeft, "actionButtonLeft");
  LoadSystemMesh(SysMeshID::kActionButtonTop, "actionButtonTop");
  LoadSystemMesh(SysMeshID::kActionButtonRight, "actionButtonRight");
  LoadSystemMesh(SysMeshID::kActionButtonBottom, "actionButtonBottom");
  LoadSystemMesh(SysMeshID::kBox, "box");
  LoadSystemMesh(SysMeshID::kLocator, "locator");
  LoadSystemMesh(SysMeshID::kLocatorBox, "locatorBox");
  LoadSystemMesh(SysMeshID::kLocatorCircle, "locatorCircle");
  LoadSystemMesh(SysMeshID::kLocatorCircleOutline, "locatorCircleOutline");
  LoadSystemMesh(SysMeshID::kCrossOut, "crossOut");
  LoadSystemMesh(SysMeshID::kWing, "wing");

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
auto Assets::GetTexture(const std::string& file_name)
    -> Object::Ref<TextureAsset> {
  assert(g_base->InLogicThread());
  assert(asset_lists_locked_);
  auto i = textures_.find(file_name);
  if (i != textures_.end()) {
    return Object::Ref<TextureAsset>(i->second.get());
  } else {
    static std::set<std::string>* quality_map_medium = nullptr;
    static std::set<std::string>* quality_map_high = nullptr;
    static bool quality_maps_inited = false;

    // TEMP - we currently set min quality based on filename;
    // in the future this will be stored with the texture package or whatnot
    if (!quality_maps_inited) {
      quality_maps_inited = true;
      quality_map_medium = new std::set<std::string>();
      quality_map_high = new std::set<std::string>();
      const char* vals_med[] = {
          "fontSmall0", "fontSmall1", "fontSmall2", "fontSmall3", "fontSmall4",
          "fontSmall5", "fontSmall6", "fontSmall7", "fontExtras", nullptr};

      const char* vals_high[] = {"frostyIcon", "jackIcon",  "melIcon",
                                 "santaIcon",  "ninjaIcon", "neoSpazIcon",
                                 "zoeIcon",    "kronkIcon", "scrollWidgetGlow",
                                 "glow",       nullptr};

      for (const char** val3 = vals_med; *val3 != nullptr; val3++) {
        quality_map_medium->insert(*val3);
      }
      for (const char** val2 = vals_high; *val2 != nullptr; val2++) {
        quality_map_high->insert(*val2);
      }
    }

    TextureMinQuality min_quality = TextureMinQuality::kLow;
    if (quality_map_medium->find(file_name) != quality_map_medium->end()) {
      min_quality = TextureMinQuality::kMedium;
    } else if (quality_map_high->find(file_name) != quality_map_high->end()) {
      min_quality = TextureMinQuality::kHigh;
    }

    auto d(Object::New<TextureAsset>(file_name, TextureType::k2D, min_quality));
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
  bool flush = false;
  millisecs_t starttime = g_core->AppTimeMillisecs();

  std::vector<Object::Ref<T>*> l;
  std::vector<Object::Ref<T>*> l_unfinished;
  std::vector<Object::Ref<T>*> l_finished;
  {
    std::scoped_lock lock(pending_load_list_mutex_);

    // If we're already out of time.
    if (!flush
        && g_core->AppTimeMillisecs() - starttime > PENDING_LOAD_PROCESS_TIME) {
      bool return_val = (!c_list->empty());
      return return_val;
    }

    // Save time if there's nothing to load.
    if (c_list->empty()) {
      return false;
    }

    // Pull the contents of c_list and set it to empty.
    l.swap(*c_list);
  }

  // Run loads on our list until either the list is empty or we're out of time
  // (don't want to block here for very long...)
  // We should also think about the fact that even if a load is quick here it
  // may add work on the graphics thread/etc so maybe we should add other
  // restrictions.
  bool out_of_time = false;
  if (!l.empty()) {
    while (true) {
      for (auto i = l.begin(); i != l.end(); i++) {
        if (!out_of_time) {
          (***i).Load(false);

          // If the load finished, pop it on our "done-loading" list.. otherwise
          // keep it around.
          l_finished.push_back(*i);  // else l_unfinished.push_back(*i);
          if (g_core->AppTimeMillisecs() - starttime > PENDING_LOAD_PROCESS_TIME
              && !flush) {
            out_of_time = true;
          }
        } else {
          // Already out of time - just save this one for later.
          l_unfinished.push_back(*i);
        }
      }
      l = l_unfinished;
      l_unfinished.clear();
      if (l.empty() || out_of_time) {
        break;
      }
    }
  }

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

  const char* ext = "";
  const char* prefix1 = "";
  const char* prefix2 = "";

  switch (type) {
    case FileType::kSound:
      if (g_core->HeadlessMode()) {
        return "headless_dummy_path.sound";
      }
      prefix1 = "audio/";
      prefix2 = "audio2/";
      ext = ".ogg";
      break;

    case FileType::kMesh:
      if (g_core->HeadlessMode()) {
        return "headless_dummy_path.mesh";
      }
      prefix1 = "meshes/";
      prefix2 = "meshes2/";
      ext = ".bob";
      break;

    case FileType::kCollisionMesh:
      prefix1 = "meshes/";
      prefix2 = "meshes2/";
      ext = ".cob";
      break;

    case FileType::kData:
      prefix1 = "data/";
      prefix2 = "data2/";
      ext = ".json";
      break;

    case FileType::kTexture: {
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
      prefix1 = "textures/";
      prefix2 = "textures2/";

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

  const std::vector<std::string>& asset_paths_used = asset_paths_;

  for (auto&& i : asset_paths_used) {
    // TEMP - try our '2' stuff first.
    for (auto&& prefix : {prefix2, prefix1}) {
      file_out = i + "/" + prefix + name + ext;  // NOLINT
      bool exists;

      // '#' denotes a cube map texture, which is actually 6 files.
      if (strchr(file_out.c_str(), '#')) {
        // Just look for one of them i guess.
        std::string tmp_name = file_out;
        tmp_name.replace(tmp_name.find('#'), 1, "_+x");
        exists = g_core->platform->FilePathExists(tmp_name);
      } else {
        exists = g_core->platform->FilePathExists(file_out);
      }
      if (exists) {
        return file_out;
      }
    }
  }

  // We wanna fail gracefully for some types.
  if (type == FileType::kSound && name != "blank") {
    g_core->logging->Log(LogName::kBaAssets, LogLevel::kError,
                         "Unable to load audio: '" + name + "'.");
    return FindAssetFile(type, "blank");
  } else if (type == FileType::kTexture && name != "white") {
    g_core->logging->Log(LogName::kBaAssets, LogLevel::kError,
                         "Unable to load texture: '" + name + "'.");
    return FindAssetFile(type, "white");
  }

  throw Exception("Can't find asset: \"" + name + "\"");
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
  special_char_strings_[SpecialChar::kGameCircleLogo] = "\xee\x80\xA6";
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

auto Assets::SysTexture(SysTextureID id) -> TextureAsset* {
  assert(asset_loads_allowed_ && sys_assets_loaded_);
  assert(g_base->InLogicThread());
  assert(static_cast<size_t>(id) < system_textures_.size());
  return system_textures_[static_cast<int>(id)].get();
}

auto Assets::SysCubeMapTexture(SysCubeMapTextureID id) -> TextureAsset* {
  assert(asset_loads_allowed_ && sys_assets_loaded_);
  assert(g_base->InLogicThread());
  assert(static_cast<size_t>(id) < system_cube_map_textures_.size());
  return system_cube_map_textures_[static_cast<int>(id)].get();
}

auto Assets::IsValidSysSound(SysSoundID id) -> bool {
  return static_cast<size_t>(id) < system_sounds_.size();
}

auto Assets::SysSound(SysSoundID id) -> SoundAsset* {
  assert(asset_loads_allowed_ && sys_assets_loaded_);
  assert(g_base->InLogicThread());
  assert(IsValidSysSound(id));
  return system_sounds_[static_cast<int>(id)].get();
}

auto Assets::SysMesh(SysMeshID id) -> MeshAsset* {
  assert(asset_loads_allowed_ && sys_assets_loaded_);
  assert(g_base->InLogicThread());
  assert(static_cast<size_t>(id) < system_meshes_.size());
  return system_meshes_[static_cast<int>(id)].get();
}

}  // namespace ballistica::base
