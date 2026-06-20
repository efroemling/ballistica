// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/support/player_spec.h"

#include <optional>
#include <string>
#include <string_view>

#include "ballistica/base/support/classic_soft.h"
#include "ballistica/classic/support/classic_app_mode.h"
#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging_macros.h"
#include "ballistica/core/platform/platform.h"
#include "ballistica/shared/generic/json_facade.h"
#include "ballistica/shared/generic/utils.h"

namespace ballistica::scene_v1 {

PlayerSpec::PlayerSpec() = default;

PlayerSpec::PlayerSpec(const std::string& s) {
  bool success = false;
  if (auto doc = JsonDoc::Parse(s)) {
    JsonRef root = doc->root();
    if (root.is_object()) {
      std::optional<std::string_view> name = root["n"].as_string();
      std::optional<std::string_view> short_name = root["sn"].as_string();
      std::optional<std::string_view> account = root["a"].as_string();
      if (name.has_value() && short_name.has_value() && account.has_value()) {
        name_ = Utils::GetValidUTF8(std::string(*name).c_str(), "psps");
        short_name_ =
            Utils::GetValidUTF8(std::string(*short_name).c_str(), "psps2");

        // Account type may technically be something we don't recognize,
        // but that's ok.. it'll just be 'invalid' to us in that case
        if (g_base->HaveClassic()) {
          v1_account_type_ = g_base->classic()->GetV1AccountTypeFromString(
              std::string(*account).c_str());
        } else {
          v1_account_type_ = 0;  // kInvalid.
        }
        success = true;
      }
    }
  }
  if (!success) {
    valid_ = false;

    // Only log this once in case it is used as an attack.
    BA_LOG_ONCE(LogName::kBa, LogLevel::kError,
                "Error creating PlayerSpec from string: '" + s + "'");
    name_ = "<error>";
    short_name_ = "<error>";
    v1_account_type_ = 0;  // kInvalid.
  }
}

auto PlayerSpec::GetDisplayString() const -> std::string {
  if (g_base->HaveClassic()) {
    return g_base->classic()->GetV1AccountTypeIconString(v1_account_type_)
           + name_;
  }
  return name_;
}

auto PlayerSpec::GetShortName() const -> std::string {
  if (short_name_.empty()) {
    return name_;
  }
  return short_name_;
}

auto PlayerSpec::operator==(const PlayerSpec& spec) const -> bool {
  // NOTE: need to add account ID in here once that's available
  return (spec.name_ == name_ && spec.short_name_ == short_name_
          && spec.v1_account_type_ == v1_account_type_);
}

auto PlayerSpec::GetSpecString() const -> std::string {
  std::string account_type =
      g_base->HaveClassic()
          ? g_base->classic()->V1AccountTypeToString(v1_account_type_)
          : "";
  JsonBuilder builder;
  builder.root_object()
      .Add("n", name_)
      .Add("a", account_type)
      .Add("sn", short_name_);
  std::string out_s = builder.Write();

  // We should never allow ourself to have all this add up to more than 256.
  assert(out_s.size() < 256);

  return out_s;
}

auto PlayerSpec::GetAccountPlayerSpec() -> PlayerSpec {
  auto* appmode = classic::ClassicAppMode::GetActiveOrThrow();
  PlayerSpec spec;
  if (g_base->HaveClassic() && g_base->classic()->IsV1AccountSignedIn()) {
    spec.v1_account_type_ = g_base->classic()->GetV1AccountType();
    // g_classic->v1_account_type();
    spec.name_ = Utils::GetValidUTF8(
        g_base->classic()->GetV1AccountLoginName().c_str(), "bsgaps");
  } else {
    // Headless builds fall back to V1 public-party name if that's available.
    if (g_buildconfig.headless_build()
        && !appmode->public_party_name().empty()) {
      spec.name_ =
          Utils::GetValidUTF8(appmode->public_party_name().c_str(), "bsgp3r");
    } else {
      // Or lastly fall back to device name.
      spec.name_ = Utils::GetValidUTF8(
          g_core->platform->GetDeviceName().c_str(), "bsgaps2");
    }
  }
  if (spec.name_.size() > 100) {
    // FIXME should perhaps clamp this in unicode space
    g_core->logging->Log(LogName::kBa, LogLevel::kError,
                         "account name size too long: '" + spec.name_ + "'");
    spec.name_.resize(100);
    spec.name_ = Utils::GetValidUTF8(spec.name_.c_str(), "bsgaps3");
  }
  return spec;
}

auto PlayerSpec::GetDummyPlayerSpec(const std::string& name) -> PlayerSpec {
  PlayerSpec spec;
  spec.name_ = Utils::GetValidUTF8(name.c_str(), "bsgdps1");
  if (spec.name_.size() > 100) {
    // FIXME should perhaps clamp this in unicode space
    g_core->logging->Log(
        LogName::kBa, LogLevel::kError,
        "dummy player spec name too long: '" + spec.name_ + "'");
    spec.name_.resize(100);
    spec.name_ = Utils::GetValidUTF8(spec.name_.c_str(), "bsgdps2");
  }
  return spec;
}

}  // namespace ballistica::scene_v1
