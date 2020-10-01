// Copyright (c) 2011-2020 Eric Froemling

#include "ballistica/app/app_config.h"

#include <utility>

#include "ballistica/ballistica.h"
#include "ballistica/platform/platform.h"
#include "ballistica/python/python.h"

namespace ballistica {

void AppConfig::Init() { new AppConfig(); }

auto AppConfig::Entry::FloatValue() const -> float {
  throw Exception("not a float entry");
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
    return g_python->GetRawConfigValue(name().c_str(), default_value_.c_str());
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
    return g_python->GetRawConfigValue(name().c_str(), default_value_);
  }
  auto FloatValue() const -> float override { return Resolve(); }
  auto DefaultFloatValue() const -> float override { return default_value_; }

 private:
  float default_value_{};
};

class AppConfig::IntEntry : public AppConfig::Entry {
 public:
  IntEntry() = default;
  IntEntry(const char* name, int default_value)
      : Entry(name), default_value_(default_value) {}
  auto GetType() const -> Type override { return Type::kInt; }
  auto Resolve() const -> int {
    return g_python->GetRawConfigValue(name().c_str(), default_value_);
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
    return g_python->GetRawConfigValue(name().c_str(), default_value_);
  }
  auto BoolValue() const -> bool override { return Resolve(); }
  auto DefaultBoolValue() const -> bool override { return default_value_; }

 private:
  bool default_value_{};
};

AppConfig::AppConfig() {
  // (We're a singleton).
  assert(g_app_config == nullptr);
  g_app_config = this;
  SetupEntries();
}

template <typename T>
void AppConfig::CompleteMap(const T& entry_map) {
  for (auto&& i : entry_map) {
    assert(entries_by_name_.find(i.second.name()) == entries_by_name_.end());
    assert(i.first < decltype(i.first)::kLast);
    entries_by_name_[i.second.name()] = &i.second;
  }

  // Make sure all values have entries.
#if BA_DEBUG_BUILD
  int last = static_cast<int>(decltype(entry_map.begin()->first)::kLast);  // ew
  for (int j = 0; j < last; ++j) {
    auto i2 =
        entry_map.find(static_cast<decltype(entry_map.begin()->first)>(j));
    if (i2 == entry_map.end()) {
      throw Exception("Missing appconfig entry " + std::to_string(j));
    }
  }
#endif
}

void AppConfig::SetupEntries() {
  // Register all our typed entries.
  float_entries_[FloatID::kScreenGamma] = FloatEntry("Screen Gamma", 1.0F);
  float_entries_[FloatID::kScreenPixelScale] =
      FloatEntry("Screen Pixel Scale", 1.0F);
  float_entries_[FloatID::kTouchControlsScale] =
      FloatEntry("Touch Controls Scale", 1.0F);
  float_entries_[FloatID::kTouchControlsScaleMovement] =
      FloatEntry("Touch Controls Scale Movement", 1.0F);
  float_entries_[FloatID::kTouchControlsScaleActions] =
      FloatEntry("Touch Controls Scale Actions", 1.0F);
  float_entries_[FloatID::kSoundVolume] = FloatEntry("Sound Volume", 1.0F);
  float_entries_[FloatID::kMusicVolume] = FloatEntry("Music Volume", 1.0F);

  // Note: keep this synced with the defaults in MainActivity.java.
  float gvrrts_default = g_platform->IsRunningOnDaydream() ? 1.0F : 0.5F;
  float_entries_[FloatID::kGoogleVRRenderTargetScale] =
      FloatEntry("GVR Render Target Scale", gvrrts_default);

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
  string_entries_[StringID::kTelnetPassword] =
      StringEntry("Telnet Password", "changeme");

  int_entries_[IntID::kPort] = IntEntry("Port", kDefaultPort);
  int_entries_[IntID::kTelnetPort] =
      IntEntry("Telnet Port", kDefaultTelnetPort);

  bool_entries_[BoolID::kTouchControlsSwipeHidden] =
      BoolEntry("Touch Controls Swipe Hidden", false);
  bool_entries_[BoolID::kFullscreen] = BoolEntry("Fullscreen", false);
  bool_entries_[BoolID::kKickIdlePlayers] =
      BoolEntry("Kick Idle Players", false);
  bool_entries_[BoolID::kAlwaysUseInternalKeyboard] =
      BoolEntry("Always Use Internal Keyboard", false);
  bool_entries_[BoolID::kShowFPS] = BoolEntry("Show FPS", false);
  bool_entries_[BoolID::kTVBorder] =
      BoolEntry("TV Border", g_platform->IsRunningOnTV());
  bool_entries_[BoolID::kKeyboardP2Enabled] =
      BoolEntry("Keyboard P2 Enabled", false);
  bool_entries_[BoolID::kEnablePackageMods] =
      BoolEntry("Enable Package Mods", false);
  bool_entries_[BoolID::kChatMuted] = BoolEntry("Chat Muted", false);
  bool_entries_[BoolID::kEnableRemoteApp] =
      BoolEntry("Enable Remote App", true);
  bool_entries_[BoolID::kEnableTelnet] = BoolEntry("Enable Telnet", true);
  bool_entries_[BoolID::kDisableCameraShake] =
      BoolEntry("Disable Camera Shake", false);
  bool_entries_[BoolID::kDisableCameraGyro] =
      BoolEntry("Disable Camera Gyro", false);

  // Now add everything to our name map and make sure all is kosher.
  CompleteMap(float_entries_);
  CompleteMap(int_entries_);
  CompleteMap(string_entries_);
  CompleteMap(bool_entries_);
}

auto AppConfig::Resolve(FloatID id) -> float {
  auto i = float_entries_.find(id);
  if (i == float_entries_.end()) {
    throw Exception("Invalid config entry");
  }
  return i->second.Resolve();
}

auto AppConfig::Resolve(StringID id) -> std::string {
  auto i = string_entries_.find(id);
  if (i == string_entries_.end()) {
    throw Exception("Invalid config entry");
  }
  return i->second.Resolve();
}

auto AppConfig::Resolve(BoolID id) -> bool {
  auto i = bool_entries_.find(id);
  if (i == bool_entries_.end()) {
    throw Exception("Invalid config entry");
  }
  return i->second.Resolve();
}

auto AppConfig::Resolve(IntID id) -> int {
  auto i = int_entries_.find(id);
  if (i == int_entries_.end()) {
    throw Exception("Invalid config entry");
  }
  return i->second.Resolve();
}

}  // namespace ballistica
