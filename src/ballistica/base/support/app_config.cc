// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/support/app_config.h"

#include <string>
#include <utility>

#include "ballistica/base/python/base_python.h"
#include "ballistica/core/core.h"
#include "ballistica/core/platform/core_platform.h"
#include "ballistica/shared/ballistica.h"

namespace ballistica::base {

auto AppConfig::Entry::FloatValue() const -> float {
  throw Exception("not a float entry");
}

auto AppConfig::Entry::OptionalFloatValue() const -> std::optional<float> {
  throw Exception("not an optional float entry");
}

auto AppConfig::Entry::StringValue() const -> std::string {
  throw Exception("not a string entry");
}

auto AppConfig::Entry::IntValue() const -> int {
  throw Exception("not an int entry");
}

auto AppConfig::Entry::BoolValue() const -> bool {
  throw Exception("not a bool entry");
}

auto AppConfig::Entry::DefaultFloatValue() const -> float {
  throw Exception("not a float entry");
}

auto AppConfig::Entry::DefaultOptionalFloatValue() const
    -> std::optional<float> {
  throw Exception("not an optional float entry");
}

auto AppConfig::Entry::DefaultStringValue() const -> std::string {
  throw Exception("not a string entry");
}

auto AppConfig::Entry::DefaultIntValue() const -> int {
  throw Exception("not an int entry");
}

auto AppConfig::Entry::DefaultBoolValue() const -> bool {
  throw Exception("not a bool entry");
}

class AppConfig::StringEntry : public AppConfig::Entry {
 public:
  StringEntry() = default;
  StringEntry(const char* name, std::string default_value)
      : Entry(name), default_value_(std::move(default_value)) {}
  auto GetType() const -> Type override { return Type::kString; }
  auto Resolve() const -> std::string {
    return g_base->python->GetRawConfigValue(name().c_str(),
                                             default_value_.c_str());
  }
  auto StringValue() const -> std::string override { return Resolve(); }
  auto DefaultStringValue() const -> std::string override {
    return default_value_;
  }

 private:
  std::string default_value_;
};

class AppConfig::FloatEntry : public AppConfig::Entry {
 public:
  FloatEntry() = default;
  FloatEntry(const char* name, float default_value)
      : Entry(name), default_value_(default_value) {}
  auto GetType() const -> Type override { return Type::kFloat; }
  auto Resolve() const -> float {
    return g_base->python->GetRawConfigValue(name().c_str(), default_value_);
  }
  auto FloatValue() const -> float override { return Resolve(); }
  auto DefaultFloatValue() const -> float override { return default_value_; }

 private:
  float default_value_{};
};

class AppConfig::OptionalFloatEntry : public AppConfig::Entry {
 public:
  OptionalFloatEntry() = default;
  OptionalFloatEntry(const char* name, std::optional<float> default_value)
      : Entry(name), default_value_(default_value) {}
  auto GetType() const -> Type override { return Type::kOptionalFloat; }
  auto Resolve() const -> std::optional<float> {
    return g_base->python->GetRawConfigValue(name().c_str(), default_value_);
  }
  auto OptionalFloatValue() const -> std::optional<float> override {
    return Resolve();
  }
  auto DefaultOptionalFloatValue() const -> std::optional<float> override {
    return default_value_;
  }

 private:
  std::optional<float> default_value_{};
};

class AppConfig::IntEntry : public AppConfig::Entry {
 public:
  IntEntry() = default;
  IntEntry(const char* name, int default_value)
      : Entry(name), default_value_(default_value) {}
  auto GetType() const -> Type override { return Type::kInt; }
  auto Resolve() const -> int {
    return g_base->python->GetRawConfigValue(name().c_str(), default_value_);
  }
  auto IntValue() const -> int override { return Resolve(); }
  auto DefaultIntValue() const -> int override { return default_value_; }

 private:
  int default_value_{};
};

class AppConfig::BoolEntry : public AppConfig::Entry {
 public:
  BoolEntry() = default;
  BoolEntry(const char* name, bool default_value)
      : Entry(name), default_value_(default_value) {}
  auto GetType() const -> Type override { return Type::kBool; }
  auto Resolve() const -> bool {
    return g_base->python->GetRawConfigValue(name().c_str(), default_value_);
  }
  auto BoolValue() const -> bool override { return Resolve(); }
  auto DefaultBoolValue() const -> bool override { return default_value_; }

 private:
  bool default_value_{};
};

AppConfig::AppConfig() { SetupEntries_(); }

template <typename T>
void AppConfig::CompleteMap_(const T& entry_map) {
  for (auto&& i : entry_map) {
    assert(entries_by_name_.find(i.second.name()) == entries_by_name_.end());
    assert(i.first < decltype(i.first)::kLast);
    entries_by_name_[i.second.name()] = &i.second;
  }

  // Make sure all values have entries.
  if (g_buildconfig.debug_build()) {
    int last =
        static_cast<int>(decltype(entry_map.begin()->first)::kLast);  // ew
    for (int j = 0; j < last; ++j) {
      auto i2 =
          entry_map.find(static_cast<decltype(entry_map.begin()->first)>(j));
      if (i2 == entry_map.end()) {
        throw Exception("Missing appconfig entry " + std::to_string(j));
      }
    }
  }
}

void AppConfig::SetupEntries_() {
  // Register all our typed entries.
  float_entries_[FloatID::kScreenPixelScale] =
      FloatEntry("Screen Pixel Scale", 1.0f);
  float_entries_[FloatID::kTouchControlsScale] =
      FloatEntry("Touch Controls Scale", 1.0f);
  float_entries_[FloatID::kTouchControlsScaleMovement] =
      FloatEntry("Touch Controls Scale Movement", 1.0f);
  float_entries_[FloatID::kTouchControlsScaleActions] =
      FloatEntry("Touch Controls Scale Actions", 1.0f);
  float_entries_[FloatID::kSoundVolume] = FloatEntry("Sound Volume", 1.0f);
  float_entries_[FloatID::kMusicVolume] = FloatEntry("Music Volume", 1.0f);

  // Note: keep this synced with the defaults in MainActivity.java.
  float gvrrts_default = g_core->platform->IsRunningOnDaydream() ? 1.0f : 0.5f;
  float_entries_[FloatID::kGoogleVRRenderTargetScale] =
      FloatEntry("GVR Render Target Scale", gvrrts_default);

  optional_float_entries_[OptionalFloatID::kIdleExitMinutes] =
      OptionalFloatEntry("Idle Exit Minutes", std::optional<float>());

  string_entries_[StringID::kResolutionAndroid] =
      StringEntry("Resolution (Android)", "Auto");
  string_entries_[StringID::kTouchActionControlType] =
      StringEntry("Touch Action Control Type", "buttons");
  string_entries_[StringID::kTouchMovementControlType] =
      StringEntry("Touch Movement Control Type", "swipe");
  string_entries_[StringID::kGraphicsQuality] =
      StringEntry("Graphics Quality", "Auto");
  string_entries_[StringID::kTextureQuality] =
      StringEntry("Texture Quality", "Auto");
  string_entries_[StringID::kVerticalSync] =
      StringEntry("Vertical Sync", "Auto");
  string_entries_[StringID::kVRHeadRelativeAudio] =
      StringEntry("VR Head Relative Audio", "Auto");
  string_entries_[StringID::kMacControllerSubsystem] =
      StringEntry("Mac Controller Subsystem", "Classic");
  string_entries_[StringID::kDevConsoleActiveTab] =
      StringEntry("Dev Console Tab", "Python");

  int_entries_[IntID::kPort] = IntEntry("Port", kDefaultPort);
  int_entries_[IntID::kMaxFPS] = IntEntry("Max FPS", 60);
  int_entries_[IntID::kSceneV1HostProtocol] =
      IntEntry("SceneV1 Host Protocol", 33);

  bool_entries_[BoolID::kTouchControlsSwipeHidden] =
      BoolEntry("Touch Controls Swipe Hidden", false);
  bool_entries_[BoolID::kFullscreen] = BoolEntry("Fullscreen", false);
  bool_entries_[BoolID::kKickIdlePlayers] =
      BoolEntry("Kick Idle Players", false);

  bool_entries_[BoolID::kAlwaysUseInternalKeyboard] =
      BoolEntry("Always Use Internal Keyboard", false);
  bool_entries_[BoolID::kUseInsecureConnections] =
      BoolEntry("Use Insecure Connections", false);
  bool_entries_[BoolID::kShowFPS] = BoolEntry("Show FPS", false);
  bool_entries_[BoolID::kShowPing] = BoolEntry("Show Ping", false);
  bool_entries_[BoolID::kShowDevConsoleButton] =
      BoolEntry("Show Dev Console Button", false);
  bool_entries_[BoolID::kEnableTVBorder] =
      BoolEntry("TV Border", g_core->platform->IsRunningOnTV());
  bool_entries_[BoolID::kKeyboardP2Enabled] =
      BoolEntry("Keyboard P2 Enabled", false);
  bool_entries_[BoolID::kEnablePackageMods] =
      BoolEntry("Enable Package Mods", false);
  bool_entries_[BoolID::kChatMuted] = BoolEntry("Chat Muted", false);
  bool_entries_[BoolID::kEnableRemoteApp] =
      BoolEntry("Enable Remote App", true);
  bool_entries_[BoolID::kDisableCameraShake] =
      BoolEntry("Disable Camera Shake", false);
  bool_entries_[BoolID::kDisableCameraGyro] =
      BoolEntry("Disable Camera Gyro", false);
  bool_entries_[BoolID::kShowDemosWhenIdle] =
      BoolEntry("Show Demos When Idle", false);
  bool_entries_[BoolID::kShowDeprecatedLoginTypes] =
      BoolEntry("Show Deprecated Login Types", false);
  bool_entries_[BoolID::kHighlightPotentialTokenPurchases] =
      BoolEntry("Highlight Potential Token Purchases", true);

  // Now add everything to our name map and make sure all is kosher.
  CompleteMap_(float_entries_);
  CompleteMap_(int_entries_);
  CompleteMap_(string_entries_);
  CompleteMap_(bool_entries_);
}

auto AppConfig::Resolve(FloatID id) -> float {
  assert(g_base->InLogicThread());
  auto i = float_entries_.find(id);
  if (i == float_entries_.end()) {
    throw Exception("Invalid config entry");
  }
  return i->second.Resolve();
}

auto AppConfig::Resolve(OptionalFloatID id) -> std::optional<float> {
  assert(g_base->InLogicThread());
  auto i = optional_float_entries_.find(id);
  if (i == optional_float_entries_.end()) {
    throw Exception("Invalid config entry");
  }
  return i->second.Resolve();
}

auto AppConfig::Resolve(StringID id) -> std::string {
  assert(g_base->InLogicThread());
  auto i = string_entries_.find(id);
  if (i == string_entries_.end()) {
    throw Exception("Invalid config entry");
  }
  return i->second.Resolve();
}

auto AppConfig::Resolve(BoolID id) -> bool {
  assert(g_base->InLogicThread());
  auto i = bool_entries_.find(id);
  if (i == bool_entries_.end()) {
    throw Exception("Invalid config entry");
  }
  return i->second.Resolve();
}

auto AppConfig::Resolve(IntID id) -> int {
  assert(g_base->InLogicThread());
  auto i = int_entries_.find(id);
  if (i == int_entries_.end()) {
    throw Exception("Invalid config entry");
  }
  return i->second.Resolve();
}

}  // namespace ballistica::base
