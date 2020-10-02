// Copyright (c) 2011-2020 Eric Froemling

#include "ballistica/game/account.h"

#include "ballistica/app/app_globals.h"
#include "ballistica/game/game.h"
#include "ballistica/generic/utils.h"
#include "ballistica/python/python.h"

namespace ballistica {

auto Account::AccountTypeFromString(const std::string& val) -> AccountType {
  if (val == "Game Center") {
    return AccountType::kGameCenter;
  } else if (val == "Game Circle") {
    return AccountType::kGameCircle;
  } else if (val == "Google Play") {
    return AccountType::kGooglePlay;
  } else if (val == "Steam") {
    return AccountType::kSteam;
  } else if (val == "Oculus") {
    return AccountType::kOculus;
  } else if (val == "NVIDIA China") {
    return AccountType::kNvidiaChina;
  } else if (val == "Test") {
    return AccountType::kTest;
  } else if (val == "Local") {
    return AccountType::kDevice;
  } else if (val == "Server") {
    return AccountType::kServer;
  } else {
    return AccountType::kInvalid;
  }
}

auto Account::AccountTypeToString(AccountType type) -> std::string {
  switch (type) {
    case AccountType::kGameCenter:
      return "Game Center";
    case AccountType::kGameCircle:
      return "Game Circle";
    case AccountType::kGooglePlay:
      return "Google Play";
    case AccountType::kSteam:
      return "Steam";
    case AccountType::kOculus:
      return "Oculus";
    case AccountType::kTest:
      return "Test";
    case AccountType::kDevice:
      return "Local";
    case AccountType::kServer:
      return "Server";
    case AccountType::kNvidiaChina:
      return "NVIDIA China";
    default:
      return "";
  }
}

auto Account::AccountTypeToIconString(AccountType type) -> std::string {
  switch (type) {
    case AccountType::kTest:
      return g_game->CharStr(SpecialChar::kTestAccount);
    case AccountType::kNvidiaChina:
      return g_game->CharStr(SpecialChar::kNvidiaLogo);
    case AccountType::kGooglePlay:
      return g_game->CharStr(SpecialChar::kGooglePlayGamesLogo);
    case AccountType::kSteam:
      return g_game->CharStr(SpecialChar::kSteamLogo);
    case AccountType::kOculus:
      return g_game->CharStr(SpecialChar::kOculusLogo);
    case AccountType::kGameCenter:
      return g_game->CharStr(SpecialChar::kGameCenterLogo);
    case AccountType::kGameCircle:
      return g_game->CharStr(SpecialChar::kGameCircleLogo);
    case AccountType::kDevice:
    case AccountType::kServer:
      return g_game->CharStr(SpecialChar::kLocalAccount);
    default:
      return "";
  }
}

Account::Account() = default;

auto Account::GetAccountName() -> std::string {
  std::lock_guard<std::mutex> lock(mutex_);
  return account_name_;
}

auto Account::GetAccountID() -> std::string {
  std::lock_guard<std::mutex> lock(mutex_);
  return account_id_;
}

auto Account::GetAccountToken() -> std::string {
  std::lock_guard<std::mutex> lock(mutex_);
  return account_token_;
}

auto Account::GetAccountExtra() -> std::string {
  std::lock_guard<std::mutex> lock(mutex_);
  return account_extra_;
}

auto Account::GetAccountExtra2() -> std::string {
  std::lock_guard<std::mutex> lock(mutex_);
  return account_extra_2_;
}

auto Account::GetAccountState(int* state_num) -> AccountState {
  std::lock_guard<std::mutex> lock(mutex_);
  if (state_num) {
    *state_num = account_state_num_;
  }
  return account_state_;
}

void Account::SetAccountExtra(const std::string& extra) {
  std::lock_guard<std::mutex> lock(mutex_);
  account_extra_ = extra;
}

void Account::SetAccountExtra2(const std::string& extra) {
  std::lock_guard<std::mutex> lock(mutex_);
  account_extra_2_ = extra;
}

void Account::SetAccountToken(const std::string& account_id,
                              const std::string& token) {
  std::lock_guard<std::mutex> lock(mutex_);
  // Hmm does this compare logic belong in here?
  if (account_id_ == account_id) {
    account_token_ = token;
  }
}

void Account::SetAccount(AccountType account_type, AccountState account_state,
                         const std::string& account_name,
                         const std::string& account_id) {
  bool call_account_changed = false;
  {
    std::lock_guard<std::mutex> lock(mutex_);

    // We call out to python so need to be in game thread.
    assert(InGameThread());
    if (account_state_ != account_state
        || g_app_globals->account_type != account_type
        || account_id_ != account_id || account_name_ != account_name) {
      // Special case: if they sent a sign-out for an account type that is.
      // currently not signed in, ignore it.
      if (account_state == AccountState::kSignedOut
          && (account_type != g_app_globals->account_type)) {
        // No-op.
      } else {
        account_state_ = account_state;
        g_app_globals->account_type = account_type;
        account_id_ = account_id;
        account_name_ = Utils::GetValidUTF8(account_name.c_str(), "gthm");

        // If they signed out of an account, account type switches to invalid.
        if (account_state == AccountState::kSignedOut) {
          g_app_globals->account_type = AccountType::kInvalid;
        }
        account_state_num_ += 1;
        call_account_changed = true;
      }
    }
  }
  if (call_account_changed) {
    // Inform python layer this has changed.
    g_python->AccountChanged();
  }
}

void Account::SetProductsPurchased(const std::vector<std::string>& products) {
  std::lock_guard<std::mutex> lock(mutex_);
  std::map<std::string, bool> purchases_old = product_purchases_;
  product_purchases_.clear();
  for (auto&& i : products) {
    product_purchases_[i] = true;
  }
  if (product_purchases_ != purchases_old) {
    product_purchases_state_++;
  }
}

auto Account::GetProductPurchased(const std::string& product) -> bool {
  std::lock_guard<std::mutex> lock(mutex_);
  auto i = product_purchases_.find(product);
  if (i == product_purchases_.end()) {
    return false;
  } else {
    return i->second;
  }
}

}  // namespace ballistica
