// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/support/player_spec.h"

#include "ballistica/classic/support/v1_account.h"
#include "ballistica/core/platform/core_platform.h"
#include "ballistica/scene_v1/support/scene_v1_app_mode.h"
#include "ballistica/shared/generic/json.h"
#include "ballistica/shared/generic/utils.h"

namespace ballistica::scene_v1 {

PlayerSpec::PlayerSpec() = default;

PlayerSpec::PlayerSpec(const std::string& s) {
  cJSON* root_obj = cJSON_Parse(s.c_str());
  bool success = false;
  if (root_obj) {
    cJSON* name_obj = cJSON_GetObjectItem(root_obj, "n");
    cJSON* short_name_obj = cJSON_GetObjectItem(root_obj, "sn");
    cJSON* account_obj = cJSON_GetObjectItem(root_obj, "a");
    if (name_obj && short_name_obj && account_obj) {
      name_ = Utils::GetValidUTF8(name_obj->valuestring, "psps");
      short_name_ = Utils::GetValidUTF8(short_name_obj->valuestring, "psps2");

      // Account type may technically be something we don't recognize,
      // but that's ok.. it'll just be 'invalid' to us in that case
      account_type_ =
          classic::V1Account::AccountTypeFromString(account_obj->valuestring);
      success = true;
    }
    cJSON_Delete(root_obj);
  }
  if (!success) {
    Log(LogLevel::kError, "Error creating PlayerSpec from string: '" + s + "'");
    name_ = "<error>";
    short_name_ = "";
    account_type_ = classic::V1AccountType::kInvalid;
  }
}

auto PlayerSpec::GetDisplayString() const -> std::string {
  return classic::V1Account::AccountTypeToIconString(account_type_) + name_;
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
          && spec.account_type_ == account_type_);
}

auto PlayerSpec::GetSpecString() const -> std::string {
  cJSON* root;
  root = cJSON_CreateObject();
  cJSON_AddStringToObject(root, "n", name_.c_str());
  cJSON_AddStringToObject(
      root, "a",
      classic::V1Account::AccountTypeToString(account_type_).c_str());
  cJSON_AddStringToObject(root, "sn", short_name_.c_str());
  char* out = cJSON_PrintUnformatted(root);
  std::string out_s = out;
  free(out);
  cJSON_Delete(root);

  // We should never allow ourself to have all this add up to more than 256.
  assert(out_s.size() < 256);

  return out_s;
}

auto PlayerSpec::GetAccountPlayerSpec() -> PlayerSpec {
  auto* appmode = SceneV1AppMode::GetActiveOrThrow();
  PlayerSpec spec;
  if (g_classic->v1_account->GetLoginState()
      == classic::V1LoginState::kSignedIn) {
    spec.account_type_ = g_classic->account_type;
    spec.name_ = Utils::GetValidUTF8(
        g_classic->v1_account->GetLoginName().c_str(), "bsgaps");
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
    Log(LogLevel::kError, "account name size too long: '" + spec.name_ + "'");
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
    Log(LogLevel::kError,
        "dummy player spec name too long: '" + spec.name_ + "'");
    spec.name_.resize(100);
    spec.name_ = Utils::GetValidUTF8(spec.name_.c_str(), "bsgdps2");
  }
  return spec;
}

}  // namespace ballistica::scene_v1
