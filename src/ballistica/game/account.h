// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_GAME_ACCOUNT_H_
#define BALLISTICA_GAME_ACCOUNT_H_

#include <map>
#include <mutex>
#include <string>
#include <vector>

#include "ballistica/ballistica.h"

namespace ballistica {

// Global account functionality.
class Account {
 public:
  Account();
  static auto AccountTypeFromString(const std::string& val) -> AccountType;
  static auto AccountTypeToString(AccountType type) -> std::string;
  static auto AccountTypeToIconString(AccountType type) -> std::string;

  auto GetAccountName() -> std::string;
  auto GetAccountID() -> std::string;
  auto GetAccountToken() -> std::string;
  auto GetAccountExtra() -> std::string;
  auto GetAccountExtra2() -> std::string;

  // Return the current account state.
  // If an int pointer is passed, state-num will also be returned.
  auto GetAccountState(int* state_num = nullptr) -> AccountState;

  // An extra value included when passing our account info to the server
  // ..(can be used for platform-specific install-signature stuff, etc).
  auto SetAccountExtra(const std::string& extra) -> void;
  auto SetAccountExtra2(const std::string& extra) -> void;
  auto SetAccountToken(const std::string& account_id, const std::string& token)
      -> void;

  auto SetAccount(AccountType account_type, AccountState account_state,
                  const std::string& name, const std::string& id) -> void;

  auto SetProductsPurchased(const std::vector<std::string>& products) -> void;
  auto GetProductPurchased(const std::string& product) -> bool;
  auto product_purchases_state() const -> int {
    return product_purchases_state_;
  }

 private:
  // Protects all access to this account (we're thread-safe).
  std::mutex mutex_;
  std::map<std::string, bool> product_purchases_;
  int product_purchases_state_{};
  std::string account_name_;
  std::string account_id_;
  std::string account_token_;
  std::string account_extra_;
  std::string account_extra_2_;
  AccountState account_state_{AccountState::kSignedOut};
  int account_state_num_{};
};

}  // namespace ballistica

#endif  // BALLISTICA_GAME_ACCOUNT_H_
