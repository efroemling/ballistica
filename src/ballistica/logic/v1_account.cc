// Released under the MIT License. See LICENSE for details.

#include "ballistica/logic/v1_account.h"

#include "ballistica/app/app.h"
#include "ballistica/generic/utils.h"
#include "ballistica/internal/app_internal.h"
#include "ballistica/logic/logic.h"
#include "ballistica/platform/platform.h"

namespace ballistica {

auto V1Account::AccountTypeFromString(const std::string& val) -> V1AccountType {
  if (val == "Game Center") {
    return V1AccountType::kGameCenter;
  } else if (val == "Game Circle") {
    return V1AccountType::kGameCircle;
  } else if (val == "Google Play") {
    return V1AccountType::kGooglePlay;
  } else if (val == "Steam") {
    return V1AccountType::kSteam;
  } else if (val == "Oculus") {
    return V1AccountType::kOculus;
  } else if (val == "NVIDIA China") {
    return V1AccountType::kNvidiaChina;
  } else if (val == "Test") {
    return V1AccountType::kTest;
  } else if (val == "Local") {
    return V1AccountType::kDevice;
  } else if (val == "Server") {
    return V1AccountType::kServer;
  } else if (val == "V2") {
    return V1AccountType::kV2;
  } else {
    return V1AccountType::kInvalid;
  }
}

auto V1Account::AccountTypeToString(V1AccountType type) -> std::string {
  switch (type) {
    case V1AccountType::kGameCenter:
      return "Game Center";
    case V1AccountType::kGameCircle:
      return "Game Circle";
    case V1AccountType::kGooglePlay:
      return "Google Play";
    case V1AccountType::kSteam:
      return "Steam";
    case V1AccountType::kOculus:
      return "Oculus";
    case V1AccountType::kTest:
      return "Test";
    case V1AccountType::kDevice:
      return "Local";
    case V1AccountType::kServer:
      return "Server";
    case V1AccountType::kNvidiaChina:
      return "NVIDIA China";
    case V1AccountType::kV2:
      return "V2";
    default:
      return "";
  }
}

auto V1Account::AccountTypeToIconString(V1AccountType type) -> std::string {
  switch (type) {
    case V1AccountType::kTest:
      return g_logic->CharStr(SpecialChar::kTestAccount);
    case V1AccountType::kNvidiaChina:
      return g_logic->CharStr(SpecialChar::kNvidiaLogo);
    case V1AccountType::kGooglePlay:
      return g_logic->CharStr(SpecialChar::kGooglePlayGamesLogo);
    case V1AccountType::kSteam:
      return g_logic->CharStr(SpecialChar::kSteamLogo);
    case V1AccountType::kOculus:
      return g_logic->CharStr(SpecialChar::kOculusLogo);
    case V1AccountType::kGameCenter:
      return g_logic->CharStr(SpecialChar::kGameCenterLogo);
    case V1AccountType::kGameCircle:
      return g_logic->CharStr(SpecialChar::kGameCircleLogo);
    case V1AccountType::kDevice:
    case V1AccountType::kServer:
      return g_logic->CharStr(SpecialChar::kLocalAccount);
    case V1AccountType::kV2:
      return g_logic->CharStr(SpecialChar::kV2Logo);
    default:
      return "";
  }
}

V1Account::V1Account() = default;

auto V1Account::GetLoginName() -> std::string {
  std::scoped_lock lock(mutex_);
  return login_name_;
}

auto V1Account::GetLoginID() -> std::string {
  std::scoped_lock lock(mutex_);
  return login_id_;
}

auto V1Account::GetToken() -> std::string {
  std::scoped_lock lock(mutex_);
  return token_;
}

auto V1Account::GetExtra() -> std::string {
  std::scoped_lock lock(mutex_);
  return extra_;
}

auto V1Account::GetExtra2() -> std::string {
  std::scoped_lock lock(mutex_);
  return extra_2_;
}

auto V1Account::GetLoginState(int* state_num) -> V1LoginState {
  std::scoped_lock lock(mutex_);
  if (state_num) {
    *state_num = login_state_num_;
  }
  return login_state_;
}

void V1Account::SetExtra(const std::string& extra) {
  std::scoped_lock lock(mutex_);
  extra_ = extra;
}

void V1Account::SetExtra2(const std::string& extra) {
  std::scoped_lock lock(mutex_);
  extra_2_ = extra;
}

void V1Account::SetToken(const std::string& account_id,
                         const std::string& token) {
  std::scoped_lock lock(mutex_);
  // Hmm, does this compare logic belong in here?
  if (login_id_ == account_id) {
    token_ = token;
  }
}

void V1Account::SetLogin(V1AccountType account_type, V1LoginState login_state,
                         const std::string& login_name,
                         const std::string& login_id) {
  bool call_login_did_change = false;
  {
    std::scoped_lock lock(mutex_);

    // We call out to Python so need to be in game thread.
    assert(InLogicThread());
    if (login_state_ != login_state || g_app->account_type != account_type
        || login_id_ != login_id || login_name_ != login_name) {
      // Special case: if they sent a sign-out for an account type that is
      // currently not signed in, ignore it.
      if (login_state == V1LoginState::kSignedOut
          && (account_type != g_app->account_type)) {
        // No-op.
      } else {
        login_state_ = login_state;
        g_app->account_type = account_type;
        login_id_ = login_id;
        login_name_ = Utils::GetValidUTF8(login_name.c_str(), "gthm");

        // If they signed out of an account, account type switches to invalid.
        if (login_state == V1LoginState::kSignedOut) {
          g_app->account_type = V1AccountType::kInvalid;
        }
        login_state_num_ += 1;
        call_login_did_change = true;
      }
    }
  }
  if (call_login_did_change) {
    // Inform a few subsystems of the change.
    g_app_internal->V1LoginDidChange();
    g_platform->V1LoginDidChange();
  }
}

void V1Account::SetProductsPurchased(const std::vector<std::string>& products) {
  std::scoped_lock lock(mutex_);
  std::unordered_map<std::string, bool> purchases_old = product_purchases_;
  product_purchases_.clear();
  for (auto&& i : products) {
    product_purchases_[i] = true;
  }
  if (product_purchases_ != purchases_old) {
    product_purchases_state_++;
  }
}

auto V1Account::GetProductPurchased(const std::string& product) -> bool {
  std::scoped_lock lock(mutex_);
  auto i = product_purchases_.find(product);
  if (i == product_purchases_.end()) {
    return false;
  } else {
    return i->second;
  }
}

}  // namespace ballistica
