// Released under the MIT License. See LICENSE for details.

#include "ballistica/game/player_spec.h"

#include "ballistica/app/app_globals.h"
#include "ballistica/game/account.h"
#include "ballistica/game/game.h"
#include "ballistica/generic/json.h"
#include "ballistica/generic/utils.h"
#include "ballistica/platform/platform.h"

namespace ballistica {

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
      account_type_ = Account::AccountTypeFromString(account_obj->valuestring);
      success = true;
    }
    cJSON_Delete(root_obj);
  }
  if (!success) {
    Log("Error creating PlayerSpec from string: '" + s + "'");
    name_ = "<error>";
    short_name_ = "";
    account_type_ = V1AccountType::kInvalid;
  }
}

auto PlayerSpec::GetDisplayString() const -> std::string {
  return Account::AccountTypeToIconString(account_type_) + name_;
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
  cJSON_AddStringToObject(root, "a",
                          Account::AccountTypeToString(account_type_).c_str());
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
  PlayerSpec spec;
  if (g_account->GetLoginState() == V1LoginState::kSignedIn) {
    spec.account_type_ = g_app_globals->account_type;
    spec.name_ =
        Utils::GetValidUTF8(g_account->GetLoginName().c_str(), "bsgaps");
  } else {
    // Headless builds fall back to V1 public-party name if that's available.
    if (g_buildconfig.headless_build()
        && !g_game->public_party_name().empty()) {
      spec.name_ =
          Utils::GetValidUTF8(g_game->public_party_name().c_str(), "bsgp3r");
    } else {
      // Or lastly fall back to device name.
      spec.name_ =
          Utils::GetValidUTF8(g_platform->GetDeviceName().c_str(), "bsgaps2");
    }
  }
  if (spec.name_.size() > 100) {
    // FIXME should perhaps clamp this in unicode space
    Log("account name size too long: '" + spec.name_ + "'");
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
    Log("dummy player spec name too long: '" + spec.name_ + "'");
    spec.name_.resize(100);
    spec.name_ = Utils::GetValidUTF8(spec.name_.c_str(), "bsgdps2");
  }
  return spec;
}

}  // namespace ballistica
