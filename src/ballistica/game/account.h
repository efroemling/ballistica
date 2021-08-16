// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_GAME_ACCOUNT_H_
#define BALLISTICA_GAME_ACCOUNT_H_

#include <mutex>
#include <string>
#include <unordered_map>
#include <vector>

#include "ballistica/ballistica.h"

namespace ballistica {

/// Global account functionality.
class Account {
 public:
  Account();
  static auto AccountTypeFromString(const std::string& val) -> AccountType;
  static auto AccountTypeToString(AccountType type) -> std::string;
  static auto AccountTypeToIconString(AccountType type) -> std::string;

  auto GetLoginName() -> std::string;
  auto GetLoginID() -> std::string;
  auto GetToken() -> std::string;
  auto GetExtra() -> std::string;
  auto GetExtra2() -> std::string;

  /// Return the current account state.
  /// If an int pointer is passed, state-num will also be returned.
  auto GetLoginState(int* state_num = nullptr) -> LoginState;

  // An extra value included when passing our account info to the server
  // ...(can be used for platform-specific install-signature stuff, etc.).
  auto SetExtra(const std::string& extra) -> void;
  auto SetExtra2(const std::string& extra) -> void;
  auto SetToken(const std::string& account_id, const std::string& token)
      -> void;

  auto SetLogin(AccountType account_type, LoginState login_state,
                const std::string& login_name, const std::string& login_id)
      -> void;

  auto SetProductsPurchased(const std::vector<std::string>& products) -> void;
  auto GetProductPurchased(const std::string& product) -> bool;
  auto product_purchases_state() const -> int {
    return product_purchases_state_;
  }

 private:
  // Protects all access to this account (we're thread-safe).
  std::mutex mutex_;
  std::unordered_map<std::string, bool> product_purchases_;
  int product_purchases_state_{};
  std::string login_name_;
  std::string login_id_;
  std::string token_;
  std::string extra_;
  std::string extra_2_;
  LoginState login_state_{LoginState::kSignedOut};
  int login_state_num_{};
};

}  // namespace ballistica

#endif  // BALLISTICA_GAME_ACCOUNT_H_
