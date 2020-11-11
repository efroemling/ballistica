// Released under the MIT License. See LICENSE for details.

#include "ballistica/media/media.h"

#if !BA_OSTYPE_WINDOWS
#include <sys/stat.h>
#endif

#include <set>
#include <vector>

#include "ballistica/audio/audio_server.h"
#include "ballistica/game/game.h"
#include "ballistica/generic/timer.h"
#include "ballistica/graphics/graphics_server.h"
#include "ballistica/graphics/text/text_packer.h"
#include "ballistica/media/component/collide_model.h"
#include "ballistica/media/component/data.h"
#include "ballistica/media/component/model.h"
#include "ballistica/media/component/texture.h"
#include "ballistica/media/data/data_data.h"
#include "ballistica/media/data/sound_data.h"
#include "ballistica/media/media_server.h"
#include "ballistica/python/python_sys.h"

namespace ballistica {

// Debug printing.
#define BA_SHOW_LOADS_UNLOADS 0
#define SHOW_PRUNING_INFO 0

// Standard prune time for unused media: 10 minutes (1000ms * 60 * 10).
#define STANDARD_MEDIA_PRUNE_TIME 600000

// More aggressive prune time for dynamically-generated text-textures: 10
// seconds.
#define TEXT_TEXTURE_PRUNE_TIME 10000

#define QR_TEXTURE_PRUNE_TIME 10000

// How long we should spend loading media in each runPendingLoads() call.
#define PENDING_LOAD_PROCESS_TIME 5

void Media::Init() {
  // Just create our singleton.
  assert(g_media == nullptr);
  g_media = new Media();
}

Media::Media() {
  media_paths_.emplace_back("ba_data");
  for (bool& have_pending_load : have_pending_loads_) {
    have_pending_load = false;
  }
}

void Media::LoadSystemTexture(SystemTextureID id, const char* name) {
  assert(media_lists_locked_);
  system_textures_.push_back(GetTextureData(name));
  assert(system_textures_.size() == static_cast<int>(id) + 1);
}

void Media::LoadSystemCubeMapTexture(SystemCubeMapTextureID id,
                                     const char* name) {
  assert(media_lists_locked_);
  system_cube_map_textures_.push_back(GetCubeMapTextureData(name));
  assert(system_cube_map_textures_.size() == static_cast<int>(id) + 1);
}

void Media::LoadSystemSound(SystemSoundID id, const char* name) {
  system_sounds_.push_back(GetSoundData(name));
  assert(system_sounds_.size() == static_cast<int>(id) + 1);
}

void Media::LoadSystemData(SystemDataID id, const char* name) {
  system_datas_.push_back(GetDataData(name));
  assert(system_datas_.size() == static_cast<int>(id) + 1);
}

void Media::LoadSystemModel(SystemModelID id, const char* name) {
  system_models_.push_back(GetModelData(name));
  assert(system_models_.size() == static_cast<int>(id) + 1);
}

void Media::LoadSystemMedia() {
  assert(InGameThread());
  assert(g_audio_server && g_media_server && g_graphics_server);
  assert(g_graphics_server
         && g_graphics_server->texture_compression_types_are_set());
  assert(g_graphics && g_graphics_server->texture_quality_set());

  // Just grab the lock once for all this stuff for efficiency.
  MediaListsLock lock;

  // System textures:
  LoadSystemTexture(SystemTextureID::kUIAtlas, "uiAtlas");
  LoadSystemTexture(SystemTextureID::kButtonSquare, "buttonSquare");
  LoadSystemTexture(SystemTextureID::kWhite, "white");
  LoadSystemTexture(SystemTextureID::kFontSmall0, "fontSmall0");
  LoadSystemTexture(SystemTextureID::kFontBig, "fontBig");
  LoadSystemTexture(SystemTextureID::kCursor, "cursor");
  LoadSystemTexture(SystemTextureID::kBoxingGlove, "boxingGlovesColor");
  LoadSystemTexture(SystemTextureID::kShield, "shield");
  LoadSystemTexture(SystemTextureID::kExplosion, "explosion");
  LoadSystemTexture(SystemTextureID::kTextClearButton, "textClearButton");
  LoadSystemTexture(SystemTextureID::kWindowHSmallVMed, "windowHSmallVMed");
  LoadSystemTexture(SystemTextureID::kWindowHSmallVSmall, "windowHSmallVSmall");
  LoadSystemTexture(SystemTextureID::kGlow, "glow");
  LoadSystemTexture(SystemTextureID::kScrollWidget, "scrollWidget");
  LoadSystemTexture(SystemTextureID::kScrollWidgetGlow, "scrollWidgetGlow");
  LoadSystemTexture(SystemTextureID::kFlagPole, "flagPoleColor");
  LoadSystemTexture(SystemTextureID::kScorch, "scorch");
  LoadSystemTexture(SystemTextureID::kScorchBig, "scorchBig");
  LoadSystemTexture(SystemTextureID::kShadow, "shadow");
  LoadSystemTexture(SystemTextureID::kLight, "light");
  LoadSystemTexture(SystemTextureID::kShadowSharp, "shadowSharp");
  LoadSystemTexture(SystemTextureID::kLightSharp, "lightSharp");
  LoadSystemTexture(SystemTextureID::kShadowSoft, "shadowSoft");
  LoadSystemTexture(SystemTextureID::kLightSoft, "lightSoft");
  LoadSystemTexture(SystemTextureID::kSparks, "sparks");
  LoadSystemTexture(SystemTextureID::kEye, "eyeColor");
  LoadSystemTexture(SystemTextureID::kEyeTint, "eyeColorTintMask");
  LoadSystemTexture(SystemTextureID::kFuse, "fuse");
  LoadSystemTexture(SystemTextureID::kShrapnel1, "shrapnel1Color");
  LoadSystemTexture(SystemTextureID::kSmoke, "smoke");
  LoadSystemTexture(SystemTextureID::kCircle, "circle");
  LoadSystemTexture(SystemTextureID::kCircleOutline, "circleOutline");
  LoadSystemTexture(SystemTextureID::kCircleNoAlpha, "circleNoAlpha");
  LoadSystemTexture(SystemTextureID::kCircleOutlineNoAlpha,
                    "circleOutlineNoAlpha");
  LoadSystemTexture(SystemTextureID::kCircleShadow, "circleShadow");
  LoadSystemTexture(SystemTextureID::kSoftRect, "softRect");
  LoadSystemTexture(SystemTextureID::kSoftRect2, "softRect2");
  LoadSystemTexture(SystemTextureID::kSoftRectVertical, "softRectVertical");
  LoadSystemTexture(SystemTextureID::kStartButton, "startButton");
  LoadSystemTexture(SystemTextureID::kBombButton, "bombButton");
  LoadSystemTexture(SystemTextureID::kOuyaAButton, "ouyaAButton");
  LoadSystemTexture(SystemTextureID::kBackIcon, "backIcon");
  LoadSystemTexture(SystemTextureID::kNub, "nub");
  LoadSystemTexture(SystemTextureID::kArrow, "arrow");
  LoadSystemTexture(SystemTextureID::kMenuButton, "menuButton");
  LoadSystemTexture(SystemTextureID::kUsersButton, "usersButton");
  LoadSystemTexture(SystemTextureID::kActionButtons, "actionButtons");
  LoadSystemTexture(SystemTextureID::kTouchArrows, "touchArrows");
  LoadSystemTexture(SystemTextureID::kTouchArrowsActions, "touchArrowsActions");
  LoadSystemTexture(SystemTextureID::kRGBStripes, "rgbStripes");
  LoadSystemTexture(SystemTextureID::kUIAtlas2, "uiAtlas2");
  LoadSystemTexture(SystemTextureID::kFontSmall1, "fontSmall1");
  LoadSystemTexture(SystemTextureID::kFontSmall2, "fontSmall2");
  LoadSystemTexture(SystemTextureID::kFontSmall3, "fontSmall3");
  LoadSystemTexture(SystemTextureID::kFontSmall4, "fontSmall4");
  LoadSystemTexture(SystemTextureID::kFontSmall5, "fontSmall5");
  LoadSystemTexture(SystemTextureID::kFontSmall6, "fontSmall6");
  LoadSystemTexture(SystemTextureID::kFontSmall7, "fontSmall7");
  LoadSystemTexture(SystemTextureID::kFontExtras, "fontExtras");
  LoadSystemTexture(SystemTextureID::kFontExtras2, "fontExtras2");
  LoadSystemTexture(SystemTextureID::kFontExtras3, "fontExtras3");
  LoadSystemTexture(SystemTextureID::kFontExtras4, "fontExtras4");
  LoadSystemTexture(SystemTextureID::kCharacterIconMask, "characterIconMask");
  LoadSystemTexture(SystemTextureID::kBlack, "black");
  LoadSystemTexture(SystemTextureID::kWings, "wings");

  // System cube map textures:
  LoadSystemCubeMapTexture(SystemCubeMapTextureID::kReflectionChar,
                           "reflectionChar#");
  LoadSystemCubeMapTexture(SystemCubeMapTextureID::kReflectionPowerup,
                           "reflectionPowerup#");
  LoadSystemCubeMapTexture(SystemCubeMapTextureID::kReflectionSoft,
                           "reflectionSoft#");
  LoadSystemCubeMapTexture(SystemCubeMapTextureID::kReflectionSharp,
                           "reflectionSharp#");
  LoadSystemCubeMapTexture(SystemCubeMapTextureID::kReflectionSharper,
                           "reflectionSharper#");
  LoadSystemCubeMapTexture(SystemCubeMapTextureID::kReflectionSharpest,
                           "reflectionSharpest#");

  // System sounds:
  LoadSystemSound(SystemSoundID::kDeek, "deek");
  LoadSystemSound(SystemSoundID::kBlip, "blip");
  LoadSystemSound(SystemSoundID::kBlank, "blank");
  LoadSystemSound(SystemSoundID::kPunch, "punch01");
  LoadSystemSound(SystemSoundID::kClick, "click01");
  LoadSystemSound(SystemSoundID::kErrorBeep, "error");
  LoadSystemSound(SystemSoundID::kSwish, "swish");
  LoadSystemSound(SystemSoundID::kSwish2, "swish2");
  LoadSystemSound(SystemSoundID::kSwish3, "swish3");
  LoadSystemSound(SystemSoundID::kTap, "tap");
  LoadSystemSound(SystemSoundID::kCorkPop, "corkPop");
  LoadSystemSound(SystemSoundID::kGunCock, "gunCocking");
  LoadSystemSound(SystemSoundID::kTickingCrazy, "tickingCrazy");
  LoadSystemSound(SystemSoundID::kSparkle, "sparkle01");
  LoadSystemSound(SystemSoundID::kSparkle2, "sparkle02");
  LoadSystemSound(SystemSoundID::kSparkle3, "sparkle03");

  // System datas:
  // (crickets)

  // System models:
  LoadSystemModel(SystemModelID::kButtonSmallTransparent,
                  "buttonSmallTransparent");
  LoadSystemModel(SystemModelID::kButtonSmallOpaque, "buttonSmallOpaque");
  LoadSystemModel(SystemModelID::kButtonMediumTransparent,
                  "buttonMediumTransparent");
  LoadSystemModel(SystemModelID::kButtonMediumOpaque, "buttonMediumOpaque");
  LoadSystemModel(SystemModelID::kButtonBackTransparent,
                  "buttonBackTransparent");
  LoadSystemModel(SystemModelID::kButtonBackOpaque, "buttonBackOpaque");
  LoadSystemModel(SystemModelID::kButtonBackSmallTransparent,
                  "buttonBackSmallTransparent");
  LoadSystemModel(SystemModelID::kButtonBackSmallOpaque,
                  "buttonBackSmallOpaque");
  LoadSystemModel(SystemModelID::kButtonTabTransparent, "buttonTabTransparent");
  LoadSystemModel(SystemModelID::kButtonTabOpaque, "buttonTabOpaque");
  LoadSystemModel(SystemModelID::kButtonLargeTransparent,
                  "buttonLargeTransparent");
  LoadSystemModel(SystemModelID::kButtonLargeOpaque, "buttonLargeOpaque");
  LoadSystemModel(SystemModelID::kButtonLargerTransparent,
                  "buttonLargerTransparent");
  LoadSystemModel(SystemModelID::kButtonLargerOpaque, "buttonLargerOpaque");
  LoadSystemModel(SystemModelID::kButtonSquareTransparent,
                  "buttonSquareTransparent");
  LoadSystemModel(SystemModelID::kButtonSquareOpaque, "buttonSquareOpaque");
  LoadSystemModel(SystemModelID::kCheckTransparent, "checkTransparent");
  LoadSystemModel(SystemModelID::kScrollBarThumbTransparent,
                  "scrollBarThumbTransparent");
  LoadSystemModel(SystemModelID::kScrollBarThumbOpaque, "scrollBarThumbOpaque");
  LoadSystemModel(SystemModelID::kScrollBarThumbSimple, "scrollBarThumbSimple");
  LoadSystemModel(SystemModelID::kScrollBarThumbShortTransparent,
                  "scrollBarThumbShortTransparent");
  LoadSystemModel(SystemModelID::kScrollBarThumbShortOpaque,
                  "scrollBarThumbShortOpaque");
  LoadSystemModel(SystemModelID::kScrollBarThumbShortSimple,
                  "scrollBarThumbShortSimple");
  LoadSystemModel(SystemModelID::kScrollBarTroughTransparent,
                  "scrollBarTroughTransparent");
  LoadSystemModel(SystemModelID::kTextBoxTransparent, "textBoxTransparent");
  LoadSystemModel(SystemModelID::kImage1x1, "image1x1");
  LoadSystemModel(SystemModelID::kImage1x1FullScreen, "image1x1FullScreen");
  LoadSystemModel(SystemModelID::kImage2x1, "image2x1");
  LoadSystemModel(SystemModelID::kImage4x1, "image4x1");
  LoadSystemModel(SystemModelID::kImage16x1, "image16x1");
#if BA_VR_BUILD
  LoadSystemModel(SystemModelID::kImage1x1VRFullScreen, "image1x1VRFullScreen");
  LoadSystemModel(SystemModelID::kVROverlay, "vrOverlay");
  LoadSystemModel(SystemModelID::kVRFade, "vrFade");
#endif  // BA_VR_BUILD
  LoadSystemModel(SystemModelID::kOverlayGuide, "overlayGuide");
  LoadSystemModel(SystemModelID::kWindowHSmallVMedTransparent,
                  "windowHSmallVMedTransparent");
  LoadSystemModel(SystemModelID::kWindowHSmallVMedOpaque,
                  "windowHSmallVMedOpaque");
  LoadSystemModel(SystemModelID::kWindowHSmallVSmallTransparent,
                  "windowHSmallVSmallTransparent");
  LoadSystemModel(SystemModelID::kWindowHSmallVSmallOpaque,
                  "windowHSmallVSmallOpaque");
  LoadSystemModel(SystemModelID::kSoftEdgeOutside, "softEdgeOutside");
  LoadSystemModel(SystemModelID::kSoftEdgeInside, "softEdgeInside");
  LoadSystemModel(SystemModelID::kBoxingGlove, "boxingGlove");
  LoadSystemModel(SystemModelID::kShield, "shield");
  LoadSystemModel(SystemModelID::kFlagPole, "flagPole");
  LoadSystemModel(SystemModelID::kFlagStand, "flagStand");
  LoadSystemModel(SystemModelID::kScorch, "scorch");
  LoadSystemModel(SystemModelID::kEyeBall, "eyeBall");
  LoadSystemModel(SystemModelID::kEyeBallIris, "eyeBallIris");
  LoadSystemModel(SystemModelID::kEyeLid, "eyeLid");
  LoadSystemModel(SystemModelID::kHairTuft1, "hairTuft1");
  LoadSystemModel(SystemModelID::kHairTuft1b, "hairTuft1b");
  LoadSystemModel(SystemModelID::kHairTuft2, "hairTuft2");
  LoadSystemModel(SystemModelID::kHairTuft3, "hairTuft3");
  LoadSystemModel(SystemModelID::kHairTuft4, "hairTuft4");
  LoadSystemModel(SystemModelID::kShrapnel1, "shrapnel1");
  LoadSystemModel(SystemModelID::kShrapnelSlime, "shrapnelSlime");
  LoadSystemModel(SystemModelID::kShrapnelBoard, "shrapnelBoard");
  LoadSystemModel(SystemModelID::kShockWave, "shockWave");
  LoadSystemModel(SystemModelID::kFlash, "flash");
  LoadSystemModel(SystemModelID::kCylinder, "cylinder");
  LoadSystemModel(SystemModelID::kArrowFront, "arrowFront");
  LoadSystemModel(SystemModelID::kArrowBack, "arrowBack");
  LoadSystemModel(SystemModelID::kActionButtonLeft, "actionButtonLeft");
  LoadSystemModel(SystemModelID::kActionButtonTop, "actionButtonTop");
  LoadSystemModel(SystemModelID::kActionButtonRight, "actionButtonRight");
  LoadSystemModel(SystemModelID::kActionButtonBottom, "actionButtonBottom");
  LoadSystemModel(SystemModelID::kBox, "box");
  LoadSystemModel(SystemModelID::kLocator, "locator");
  LoadSystemModel(SystemModelID::kLocatorBox, "locatorBox");
  LoadSystemModel(SystemModelID::kLocatorCircle, "locatorCircle");
  LoadSystemModel(SystemModelID::kLocatorCircleOutline, "locatorCircleOutline");
  LoadSystemModel(SystemModelID::kCrossOut, "crossOut");
  LoadSystemModel(SystemModelID::kWing, "wing");

  // Hooray!
  system_media_loaded_ = true;
}

Media::~Media() = default;

void Media::PrintLoadInfo() {
  std::string s;
  char buffer[256];
  int num = 1;

  // Need to lock lists while iterating over them.
  MediaListsLock lock;
  s = "Media load results:  (all times in milliseconds):\n";
  snprintf(buffer, sizeof(buffer), "    %-50s %10s %10s", "FILE",
           "PRELOAD_TIME", "LOAD_TIME");
  s += buffer;
  Log(s, true, false);
  millisecs_t total_preload_time = 0;
  millisecs_t total_load_time = 0;
  assert(media_lists_locked_);
  for (auto&& i : models_) {
    millisecs_t preload_time = i.second->preload_time();
    millisecs_t load_time = i.second->load_time();
    total_preload_time += preload_time;
    total_load_time += load_time;
    snprintf(buffer, sizeof(buffer), "%-3d %-50s %10d %10d", num,
             i.second->GetName().c_str(),
             static_cast_check_fit<int>(preload_time),
             static_cast_check_fit<int>(load_time));
    Log(buffer, true, false);
    num++;
  }
  assert(media_lists_locked_);
  for (auto&& i : collide_models_) {
    millisecs_t preload_time = i.second->preload_time();
    millisecs_t load_time = i.second->load_time();
    total_preload_time += preload_time;
    total_load_time += load_time;
    snprintf(buffer, sizeof(buffer), "%-3d %-50s %10d %10d", num,
             i.second->GetName().c_str(),
             static_cast_check_fit<int>(preload_time),
             static_cast_check_fit<int>(load_time));
    Log(buffer, true, false);
    num++;
  }
  assert(media_lists_locked_);
  for (auto&& i : sounds_) {
    millisecs_t preload_time = i.second->preload_time();
    millisecs_t load_time = i.second->load_time();
    total_preload_time += preload_time;
    total_load_time += load_time;
    snprintf(buffer, sizeof(buffer), "%-3d %-50s %10d %10d", num,
             i.second->GetName().c_str(),
             static_cast_check_fit<int>(preload_time),
             static_cast_check_fit<int>(load_time));
    Log(buffer, true, false);
    num++;
  }
  assert(media_lists_locked_);
  for (auto&& i : datas_) {
    millisecs_t preload_time = i.second->preload_time();
    millisecs_t load_time = i.second->load_time();
    total_preload_time += preload_time;
    total_load_time += load_time;
    snprintf(buffer, sizeof(buffer), "%-3d %-50s %10d %10d", num,
             i.second->GetName().c_str(),
             static_cast_check_fit<int>(preload_time),
             static_cast_check_fit<int>(load_time));
    Log(buffer, true, false);
    num++;
  }
  assert(media_lists_locked_);
  for (auto&& i : textures_) {
    millisecs_t preload_time = i.second->preload_time();
    millisecs_t load_time = i.second->load_time();
    total_preload_time += preload_time;
    total_load_time += load_time;
    snprintf(buffer, sizeof(buffer), "%-3d %-50s %10d %10d", num,
             i.second->file_name_full().c_str(),
             static_cast_check_fit<int>(preload_time),
             static_cast_check_fit<int>(load_time));
    Log(buffer, true, false);
    num++;
  }
  snprintf(buffer, sizeof(buffer),
           "Total preload time (loading data from disk): %i\nTotal load time "
           "(feeding data to OpenGL, etc): %i",
           static_cast<int>(total_preload_time),
           static_cast<int>(total_load_time));
  Log(buffer, true, false);
}

void Media::MarkAllMediaForLoad() {
  assert(InGameThread());

  // Need to keep lists locked while iterating over them.
  MediaListsLock m_lock;
  for (auto&& i : textures_) {
    if (!i.second->preloaded()) {
      MediaComponentData::LockGuard lock(i.second.get());
      have_pending_loads_[static_cast<int>(MediaType::kTexture)] = true;
      MarkComponentForLoad(i.second.get());
    }
  }
  for (auto&& i : text_textures_) {
    if (!i.second->preloaded()) {
      MediaComponentData::LockGuard lock(i.second.get());
      have_pending_loads_[static_cast<int>(MediaType::kTexture)] = true;
      MarkComponentForLoad(i.second.get());
    }
  }
  for (auto&& i : qr_textures_) {
    if (!i.second->preloaded()) {
      MediaComponentData::LockGuard lock(i.second.get());
      have_pending_loads_[static_cast<int>(MediaType::kTexture)] = true;
      MarkComponentForLoad(i.second.get());
    }
  }
  for (auto&& i : models_) {
    if (!i.second->preloaded()) {
      MediaComponentData::LockGuard lock(i.second.get());
      have_pending_loads_[static_cast<int>(MediaType::kModel)] = true;
      MarkComponentForLoad(i.second.get());
    }
  }
}

// Call this from the graphics thread to immediately unload all
// media used by it. (for when GL context gets lost, etc).
void Media::UnloadRendererBits(bool do_textures, bool do_models) {
  assert(InGraphicsThread());
  // need to keep lists locked while iterating over them..
  MediaListsLock m_lock;
  if (do_textures) {
    assert(media_lists_locked_);
    for (auto&& i : textures_) {
      MediaComponentData::LockGuard lock(i.second.get());
      i.second->Unload(true);
    }
    for (auto&& i : text_textures_) {
      MediaComponentData::LockGuard lock(i.second.get());
      i.second->Unload(true);
    }
    for (auto&& i : qr_textures_) {
      MediaComponentData::LockGuard lock(i.second.get());
      i.second->Unload(true);
    }
  }
  if (do_models) {
    for (auto&& i : models_) {
      MediaComponentData::LockGuard lock(i.second.get());
      i.second->Unload(true);
    }
  }
}

auto Media::GetModelData(const std::string& file_name)
    -> Object::Ref<ModelData> {
  return GetComponentData(file_name, &models_);
}

auto Media::GetSoundData(const std::string& file_name)
    -> Object::Ref<SoundData> {
  return GetComponentData(file_name, &sounds_);
}

auto Media::GetDataData(const std::string& file_name) -> Object::Ref<DataData> {
  return GetComponentData(file_name, &datas_);
}

auto Media::GetCollideModelData(const std::string& file_name)
    -> Object::Ref<CollideModelData> {
  return GetComponentData(file_name, &collide_models_);
}

template <class T>
auto Media::GetComponentData(
    const std::string& file_name,
    std::unordered_map<std::string, Object::Ref<T> >* c_list)
    -> Object::Ref<T> {
  assert(InGameThread());
  assert(media_lists_locked_);
  auto i = c_list->find(file_name);
  if (i != c_list->end()) {
    return Object::Ref<T>(i->second.get());
  } else {
    auto d(Object::New<T>(file_name));
    (*c_list)[file_name] = d;
    {
      MediaComponentData::LockGuard lock(d.get());
      have_pending_loads_[static_cast<int>(d->GetMediaType())] = true;
      MarkComponentForLoad(d.get());
    }
    d->set_last_used_time(GetRealTime());
    return d;
  }
}

auto Media::GetTextureData(TextPacker* packer) -> Object::Ref<TextureData> {
  assert(InGameThread());
  assert(media_lists_locked_);
  const std::string& hash(packer->hash());
  auto i = text_textures_.find(hash);
  if (i != text_textures_.end()) {
    return Object::Ref<TextureData>(i->second.get());
  } else {
    auto d(Object::New<TextureData>(packer));
    text_textures_[hash] = d;
    {
      MediaComponentData::LockGuard lock(d.get());
      have_pending_loads_[static_cast<int>(d->GetMediaType())] = true;
      MarkComponentForLoad(d.get());
    }
    d->set_last_used_time(GetRealTime());
    return d;
  }
}

auto Media::GetTextureDataQRCode(const std::string& url)
    -> Object::Ref<TextureData> {
  assert(InGameThread());
  assert(media_lists_locked_);
  auto i = qr_textures_.find(url);
  if (i != qr_textures_.end()) {
    return Object::Ref<TextureData>(i->second.get());
  } else {
    auto d(Object::New<TextureData>(url));
    qr_textures_[url] = d;
    {
      MediaComponentData::LockGuard lock(d.get());
      have_pending_loads_[static_cast<int>(d->GetMediaType())] = true;
      MarkComponentForLoad(d.get());
    }
    d->set_last_used_time(GetRealTime());
    return d;
  }
}

// Eww can't recycle GetComponent here since we need extra stuff (tex-type arg)
// ..should fix.
auto Media::GetCubeMapTextureData(const std::string& file_name)
    -> Object::Ref<TextureData> {
  assert(InGameThread());
  assert(media_lists_locked_);
  auto i = textures_.find(file_name);
  if (i != textures_.end()) {
    return Object::Ref<TextureData>(i->second.get());
  } else {
    auto d(Object::New<TextureData>(file_name, TextureType::kCubeMap,
                                    TextureMinQuality::kLow));
    textures_[file_name] = d;
    {
      MediaComponentData::LockGuard lock(d.get());
      have_pending_loads_[static_cast<int>(d->GetMediaType())] = true;
      MarkComponentForLoad(d.get());
    }
    d->set_last_used_time(GetRealTime());
    return d;
  }
}

// Eww; can't recycle GetComponent here since we need extra stuff (quality
// settings, etc). Should fix.
auto Media::GetTextureData(const std::string& file_name)
    -> Object::Ref<TextureData> {
  assert(InGameThread());
  assert(media_lists_locked_);
  auto i = textures_.find(file_name);
  if (i != textures_.end()) {
    return Object::Ref<TextureData>(i->second.get());
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

    auto d(Object::New<TextureData>(file_name, TextureType::k2D, min_quality));
    textures_[file_name] = d;
    {
      MediaComponentData::LockGuard lock(d.get());
      have_pending_loads_[static_cast<int>(d->GetMediaType())] = true;
      MarkComponentForLoad(d.get());
    }
    d->set_last_used_time(GetRealTime());
    return d;
  }
}

void Media::MarkComponentForLoad(MediaComponentData* c) {
  assert(InGameThread());

  assert(c->locked());

  // *allocate* a reference as a standalone pointer so we can be
  // sure this guy sticks around until it's been sent all the way
  // through the preload/load cycle. (since other threads will be touching it)
  // once it makes it back to us we can delete the ref (in
  // ClearPendingLoadsDoneList)

  auto media_ptr = new Object::Ref<MediaComponentData>(c);
  g_media_server->PushRunnable(Object::NewDeferred<PreloadRunnable>(media_ptr));
}

auto Media::GetModelPendingLoadCount() -> int {
  if (!have_pending_loads_[static_cast<int>(MediaType::kModel)]) {
    return 0;
  }
  MediaListsLock lock;
  int total = GetComponentPendingLoadCount(&models_, MediaType::kModel);
  if (total == 0) {
    // When fully loaded, stop counting.
    have_pending_loads_[static_cast<int>(MediaType::kModel)] = false;
  }
  return total;
}

auto Media::GetTexturePendingLoadCount() -> int {
  if (!have_pending_loads_[static_cast<int>(MediaType::kTexture)]) {
    return 0;
  }
  MediaListsLock lock;
  int total =
      (GetComponentPendingLoadCount(&textures_, MediaType::kTexture)
       + GetComponentPendingLoadCount(&text_textures_, MediaType::kTexture)
       + GetComponentPendingLoadCount(&qr_textures_, MediaType::kTexture));
  if (total == 0) {
    // When fully loaded, stop counting.
    have_pending_loads_[static_cast<int>(MediaType::kTexture)] = false;
  }
  return total;
}

auto Media::GetSoundPendingLoadCount() -> int {
  if (!have_pending_loads_[static_cast<int>(MediaType::kSound)]) {
    return 0;
  }
  MediaListsLock lock;
  int total = GetComponentPendingLoadCount(&sounds_, MediaType::kSound);
  if (total == 0) {
    // When fully loaded, stop counting.
    have_pending_loads_[static_cast<int>(MediaType::kSound)] = false;
  }
  return total;
}

auto Media::GetDataPendingLoadCount() -> int {
  if (!have_pending_loads_[static_cast<int>(MediaType::kData)]) {
    return 0;
  }
  MediaListsLock lock;
  int total = GetComponentPendingLoadCount(&datas_, MediaType::kData);
  if (total == 0) {
    // When fully loaded, stop counting.
    have_pending_loads_[static_cast<int>(MediaType::kData)] = false;
  }
  return total;
}

auto Media::GetCollideModelPendingLoadCount() -> int {
  if (!have_pending_loads_[static_cast<int>(MediaType::kCollideModel)]) {
    return 0;
  }
  MediaListsLock lock;
  int total =
      GetComponentPendingLoadCount(&collide_models_, MediaType::kCollideModel);
  if (total == 0) {
    // When fully loaded, stop counting.
    have_pending_loads_[static_cast<int>(MediaType::kCollideModel)] = false;
  }
  return total;
}

auto Media::GetGraphicalPendingLoadCount() -> int {
  // Each of these calls lock the media-lists so we don't.
  return GetModelPendingLoadCount() + GetTexturePendingLoadCount();
}

auto Media::GetPendingLoadCount() -> int {
  // Each of these calls lock the media-lists so we don't.
  return GetModelPendingLoadCount() + GetTexturePendingLoadCount()
         + GetDataPendingLoadCount() + GetSoundPendingLoadCount()
         + GetCollideModelPendingLoadCount();
}

template <class T>
auto Media::GetComponentPendingLoadCount(
    std::unordered_map<std::string, Object::Ref<T> >* t_list, MediaType type)
    -> int {
  assert(InGameThread());
  assert(media_lists_locked_);

  int c = 0;
  for (auto&& i : (*t_list)) {
    if (i.second.exists()) {
      if (i.second->TryLock()) {
        MediaComponentData::LockGuard lock(
            i.second.get(), MediaComponentData::LockGuard::Type::kInheritLock);
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
auto Media::RunPendingAudioLoads() -> bool {
  assert(InAudioThread());
  return RunPendingLoadList(&pending_loads_sounds_);
}

// Runs the pending loads that need to run from the graphics thread.
auto Media::RunPendingGraphicsLoads() -> bool {
  assert(InGraphicsThread());
  return RunPendingLoadList(&pending_loads_graphics_);
}

// Runs the pending loads that run in the main thread.  Also clears the list of
// done loads.
auto Media::RunPendingLoadsGameThread() -> bool {
  assert(InGameThread());
  return RunPendingLoadList(&pending_loads_other_);
}

template <class T>
auto Media::RunPendingLoadList(std::vector<Object::Ref<T>*>* c_list) -> bool {
  bool flush = false;
  millisecs_t starttime = GetRealTime();

  std::vector<Object::Ref<T>*> l;
  std::vector<Object::Ref<T>*> l_unfinished;
  std::vector<Object::Ref<T>*> l_finished;
  {
    std::lock_guard<std::mutex> lock(pending_load_list_mutex_);

    // If we're already out of time.
    if (!flush && GetRealTime() - starttime > PENDING_LOAD_PROCESS_TIME) {
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
          if (GetRealTime() - starttime > PENDING_LOAD_PROCESS_TIME && !flush) {
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
    std::lock_guard<std::mutex> lock(pending_load_list_mutex_);
    for (auto&& i : l) {
      c_list->push_back(i);
    }
    for (auto&& i : l_finished) {
      pending_loads_done_.push_back(i);
    }
  }

  // if we dumped anything on the pending loads done list, shake the game thread
  // to tell it to kill the reference..
  if (!l_finished.empty()) {
    assert(g_game);
    g_game->PushHavePendingLoadsDoneCall();
  }
  return (!l.empty());
}

void Media::Prune(int level) {
  assert(InGameThread());
  millisecs_t current_time = GetRealTime();

  // need lists locked while accessing/modifying them
  MediaListsLock lock;

  // we can specify level for more aggressive pruning (during memory warnings
  // and whatnot)
  millisecs_t standard_media_prune_time = STANDARD_MEDIA_PRUNE_TIME;
  millisecs_t text_texture_prune_time = TEXT_TEXTURE_PRUNE_TIME;
  millisecs_t qr_texture_prune_time = QR_TEXTURE_PRUNE_TIME;
  switch (level) {
    case 1:
      standard_media_prune_time = 120000;  // 2 min
      text_texture_prune_time = 1000;      // 1 sec
      qr_texture_prune_time = 1000;        // 1 sec
      break;
    case 2:
      standard_media_prune_time = 30000;  // 30 sec
      text_texture_prune_time = 1000;     // 1 sec
      qr_texture_prune_time = 1000;       // 1 sec
      break;
    case 3:
      standard_media_prune_time = 5000;  // 5 sec
      text_texture_prune_time = 1000;    // 1 sec
      qr_texture_prune_time = 1000;      // 1 sec
      break;
    default:
      break;
  }

  std::vector<Object::Ref<MediaComponentData>*> graphics_thread_unloads;
  std::vector<Object::Ref<MediaComponentData>*> audio_thread_unloads;

#if SHOW_PRUNING_INFO
  assert(media_lists_locked_);
  int old_texture_count = textures_.size();
  int old_text_texture_count = text_textures_.size();
  int old_qr_texture_count = qr_textures_.size();
  int old_model_count = models_.size();
  int old_collide_model_count = collide_models_.size();
  int old_sound_count = sounds_.size();
#endif  // SHOW_PRUNING_INFO

  // prune textures..
  assert(media_lists_locked_);
  for (auto i = textures_.begin(); i != textures_.end();) {
    TextureData* texture_data = i->second.get();
    // attempt to prune if there are no references remaining except our own and
    // its been a while since it was used
    if (current_time - texture_data->last_used_time()
            > standard_media_prune_time
        && (texture_data->object_strong_ref_count() <= 1)) {
      // if its preloaded/loaded we need to ask the graphics thread to unload it
      // first
      if (texture_data->preloaded()) {
        // allocate a reference to keep this texture_data alive while the unload
        // is happening
        graphics_thread_unloads.push_back(
            new Object::Ref<MediaComponentData>(texture_data));
        auto i_next = i;
        i_next++;
        textures_.erase(i);
        i = i_next;
      }
    } else {
      i++;
    }
  }

  // prune text-textures more aggressively since we may generate lots of them
  // FIXME - we may want to prune based on total number of these instead of
  // time..
  assert(media_lists_locked_);
  for (auto i = text_textures_.begin(); i != text_textures_.end();) {
    TextureData* texture_data = i->second.get();
    // attempt to prune if there are no references remaining except our own and
    // its been a while since it was used
    if (current_time - texture_data->last_used_time() > text_texture_prune_time
        && (texture_data->object_strong_ref_count() <= 1)) {
      // if its preloaded/loaded we need to ask the graphics thread to unload it
      // first
      if (texture_data->preloaded()) {
        // allocate a reference to keep this texture_data alive while the unload
        // is happening
        graphics_thread_unloads.push_back(
            new Object::Ref<MediaComponentData>(texture_data));
        auto i_next = i;
        i_next++;
        text_textures_.erase(i);
        i = i_next;
      }
    } else {
      i++;
    }
  }

  // prune textures
  assert(media_lists_locked_);
  for (auto i = qr_textures_.begin(); i != qr_textures_.end();) {
    TextureData* texture_data = i->second.get();
    // attempt to prune if there are no references remaining except our own and
    // its been a while since it was used
    if (current_time - texture_data->last_used_time() > qr_texture_prune_time
        && (texture_data->object_strong_ref_count() <= 1)) {
      // if its preloaded/loaded we need to ask the graphics thread to unload it
      // first
      if (texture_data->preloaded()) {
        // allocate a reference to keep this texture_data alive while the unload
        // is happening
        graphics_thread_unloads.push_back(
            new Object::Ref<MediaComponentData>(texture_data));
        auto i_next = i;
        i_next++;
        qr_textures_.erase(i);
        i = i_next;
      }
    } else {
      i++;
    }
  }

  // prune models..
  assert(media_lists_locked_);
  for (auto i = models_.begin(); i != models_.end();) {
    ModelData* model_data = i->second.get();
    // attempt to prune if there are no references remaining except our own and
    // its been a while since it was used
    if (current_time - model_data->last_used_time() > standard_media_prune_time
        && (model_data->object_strong_ref_count() <= 1)) {
      // if its preloaded/loaded we need to ask the graphics thread to unload it
      // first
      if (model_data->preloaded()) {
        // allocate a reference to keep this model_data alive while the unload
        // is happening
        graphics_thread_unloads.push_back(
            new Object::Ref<MediaComponentData>(model_data));
        auto i_next = i;
        i_next++;
        models_.erase(i);
        i = i_next;
      }
    } else {
      i++;
    }
  }

  // Prune collide-models.
  assert(media_lists_locked_);
  for (auto i = collide_models_.begin(); i != collide_models_.end();) {
    CollideModelData* collide_model_data = i->second.get();
    // attempt to prune if there are no references remaining except our own and
    // its been a while since it was used (unlike other media we never prune
    // these if there's still references to them
    if (current_time - collide_model_data->last_used_time()
            > standard_media_prune_time
        && (collide_model_data->object_strong_ref_count() <= 1)) {
      // we can unload it immediately since that happens in the game thread...
      collide_model_data->Unload();
      auto i_next = i;
      ++i_next;
      collide_models_.erase(i);
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
    assert(media_lists_locked_);
    for (auto i = sounds_.begin(); i != sounds_.end();) {
      SoundData* sound_data = i->second.get();
      // Attempt to prune if there are no references remaining except our own
      // and its been a while since it was used.
      if (current_time - sound_data->last_used_time()
              > standard_media_prune_time
          && (sound_data->object_strong_ref_count() <= 1)) {
        // If its preloaded/loaded we need to ask the graphics thread to unload
        // it first.
        if (sound_data->preloaded()) {
          // Allocate a reference to keep this sound_data alive while the unload
          // is happening.
          audio_thread_unloads.push_back(
              new Object::Ref<MediaComponentData>(sound_data));
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
    g_graphics_server->PushComponentUnloadCall(graphics_thread_unloads);
  }
  if (!audio_thread_unloads.empty()) {
    g_audio_server->PushComponentUnloadCall(audio_thread_unloads);
  }

#if SHOW_PRUNING_INFO
  assert(media_lists_locked_);
  if (textures_.size() != old_texture_count) {
    Log("Textures pruned from " + std::to_string(old_texture_count) + " to "
        + std::to_string(textures_.size()));
  }
  if (text_textures_.size() != old_text_texture_count) {
    Log("TextTextures pruned from " + std::to_string(old_text_texture_count)
        + " to " + std::to_string(text_textures_.size()));
  }
  if (qr_textures_.size() != old_qr_texture_count) {
    Log("QrTextures pruned from " + std::to_string(old_qr_texture_count)
        + " to " + std::to_string(qr_textures_.size()));
  }
  if (models_.size() != old_model_count) {
    Log("Models pruned from " + std::to_string(old_model_count) + " to "
        + std::to_string(models_.size()));
  }
  if (collide_models_.size() != old_collide_model_count) {
    Log("CollideModels pruned from " + std::to_string(old_collide_model_count)
        + " to " + std::to_string(collide_models_.size()));
  }
  if (sounds_.size() != old_sound_count) {
    Log("Sounds pruned from " + std::to_string(old_sound_count) + " to "
        + std::to_string(sounds_.size()));
  }
#endif  // SHOW_PRUNING_INFO
}

auto Media::FindMediaFile(FileType type, const std::string& name)
    -> std::string {
  std::string file_out;

  // We don't protect package-path access so make sure its always from here.
  assert(InGameThread());

  const char* ext = "";
  const char* prefix = "";

  switch (type) {
    case FileType::kSound:
#if BA_HEADLESS_BUILD
      return "headless_dummy_path.sound";
#else  // BA_HEADLESS_BUILD
      prefix = "audio/";
      ext = ".ogg";
      break;
#endif  // BA_HEADLESS_BUILD

    case FileType::kModel:
#if BA_HEADLESS_BUILD
      return "headless_dummy_path.model";
#else  // BA_HEADLESS_BUILD
      prefix = "models/";
      ext = ".bob";
      break;
#endif  // BA_HEADLESS_BUILD

    case FileType::kCollisionModel:
      prefix = "models/";
      ext = ".cob";
      break;

    case FileType::kData:
      prefix = "data/";
      ext = ".json";
      break;

    case FileType::kTexture: {
#if BA_HEADLESS_BUILD
      if (strchr(name.c_str(), '#')) {
        return "headless_dummy_path#.nop";
      } else {
        return "headless_dummy_path.nop";
      }
#else  // BA_HEADLESS_BUILD

      assert(g_graphics_server
             && g_graphics_server->texture_compression_types_are_set());
      assert(g_graphics_server && g_graphics_server->texture_quality_set());
      prefix = "textures/";

#if BA_OSTYPE_ANDROID && !BA_ANDROID_DDS_BUILD
      // On most android builds we go for .kvm, which contains etc2 and etc1.
      ext = ".ktx";
#elif BA_OSTYPE_IOS_TVOS
      // On iOS we use pvr.
      ext = ".pvr";
#else
      // all else defaults to dds
      ext = ".dds";
#endif
#endif  // BA_HEADLESS_BUILD
      break;
    }
    default:
      break;
  }

  const std::vector<std::string>& media_paths_used = media_paths_;

  for (auto&& i : media_paths_used) {
    struct BA_STAT stats {};
    file_out = i + "/" + prefix + name + ext;  // NOLINT
    int result;

    // '#' denotes a cube map texture, which is actually 6 files.
    if (strchr(file_out.c_str(), '#')) {
      std::string tmp_name = file_out;
      tmp_name.replace(tmp_name.find('#'), 1, "_+x");

      // Just look for one of them i guess.
      result = g_platform->Stat(tmp_name.c_str(), &stats);
    } else {
      result = g_platform->Stat(file_out.c_str(), &stats);
    }
    if (result == 0) {
      if (S_ISREG(stats.st_mode)) {  // NOLINT
        return file_out;
      }
    }
  }

  // We wanna fail gracefully for some types.
  if (type == FileType::kSound && name != "blank") {
    Log("Unable to load audio: '" + name + "'; trying fallback...");
    return FindMediaFile(type, "blank");
  } else if (type == FileType::kTexture && name != "white") {
    Log("Unable to load texture: '" + name + "'; trying fallback...");
    return FindMediaFile(type, "white");
  }

  throw Exception("Can't find media: \"" + name + "\"");
  // return file_out;
}

void Media::AddPendingLoad(Object::Ref<MediaComponentData>* c) {
  switch ((**c).GetMediaType()) {
    case MediaType::kTexture:
    case MediaType::kModel: {
      // Tell the graphics thread there's pending loads...
      std::lock_guard<std::mutex> lock(pending_load_list_mutex_);
      pending_loads_graphics_.push_back(c);
      break;
    }
    case MediaType::kSound: {
      // Tell the audio thread there's pending loads.
      {
        std::lock_guard<std::mutex> lock(pending_load_list_mutex_);
        pending_loads_sounds_.push_back(c);
      }
      g_audio_server->PushHavePendingLoadsCall();
      break;
    }
    default: {
      // Tell the game thread there's pending loads.
      {
        std::lock_guard<std::mutex> lock(pending_load_list_mutex_);
        pending_loads_other_.push_back(c);
      }
      g_game->PushHavePendingLoadsCall();
      break;
    }
  }
}

void Media::ClearPendingLoadsDoneList() {
  assert(InGameThread());

  std::lock_guard<std::mutex> lock(pending_load_list_mutex_);

  // Our explicitly-allocated reference pointer has made it back to us here in
  // the game thread.
  // We can now kill the reference knowing that it's safe for this component
  // to die at any time (anyone needing it to be alive now should be holding a
  // reference themselves).
  for (Object::Ref<MediaComponentData>* i : pending_loads_done_) {
    delete i;
  }
  pending_loads_done_.clear();
}

void Media::PreloadRunnable::Run() {
  assert(InMediaThread());

  // add our pointer to one of the preload lists and shake our preload thread to
  // wake it up
  if ((**c).GetMediaType() == MediaType::kSound) {
    g_media_server->pending_preloads_audio_.push_back(c);
  } else {
    g_media_server->pending_preloads_.push_back(c);
  }
  g_media_server->process_timer_->SetLength(0);
}

void Media::AddPackage(const std::string& name, const std::string& path) {
  // we don't protect package-path access so make sure its always from here..
  assert(InGameThread());
#if BA_DEBUG_BUILD
  if (packages_.find(name) != packages_.end()) {
    Log("WARNING: adding duplicate package: '" + name + "'");
  }
#endif  // BA_DEBUG_BUILD
  packages_[name] = path;
}

Media::MediaListsLock::MediaListsLock() {
  BA_DEBUG_FUNCTION_TIMER_BEGIN();
  g_media->media_lists_mutex_.lock();
  assert(!g_media->media_lists_locked_);
  g_media->media_lists_locked_ = true;
  BA_DEBUG_FUNCTION_TIMER_END_THREAD(20);
}

Media::MediaListsLock::~MediaListsLock() {
  assert(g_media->media_lists_locked_);
  g_media->media_lists_locked_ = false;
  g_media->media_lists_mutex_.unlock();
}

}  // namespace ballistica
