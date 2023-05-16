// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_CLASSIC_SUPPORT_V1_ACCOUNT_H_
#define BALLISTICA_CLASSIC_SUPPORT_V1_ACCOUNT_H_

#include <mutex>
#include <string>
#include <unordered_map>
#include <vector>

#include "ballistica/classic/classic.h"
#include "ballistica/shared/ballistica.h"

namespace ballistica::classic {

/// Global account functionality.
class V1Account {
 public:
  void PushSetV1LoginCall(V1AccountType account_type,
                          V1LoginState account_state,
                          const std::string& account_name,
                          const std::string& account_id);

  V1Account();
  static auto AccountTypeFromString(const std::string& val) -> V1AccountType;
  static auto AccountTypeToString(V1AccountType type) -> std::string;
  static auto AccountTypeToIconString(V1AccountType type) -> std::string;

  auto GetLoginName() -> std::string;
  auto GetLoginID() -> std::string;
  auto GetToken() -> std::string;
  auto GetExtra() -> std::string;
  auto GetExtra2() -> std::string;

  /// Return the current account state.
  /// If an int pointer is passed, state-num will also be returned.
  auto GetLoginState(int* state_num = nullptr) -> V1LoginState;

  // An extra value included when passing our account info to the server
  // ...(can be used for platform-specific install-signature stuff, etc.).
  void SetExtra(const std::string& extra);
  void SetExtra2(const std::string& extra);
  void SetToken(const std::string& account_id, const std::string& token);

  void SetLogin(V1AccountType account_type, V1LoginState login_state,
                const std::string& login_name, const std::string& login_id);

  void SetProductsPurchased(const std::vector<std::string>& products);
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
  V1LoginState login_state_{V1LoginState::kSignedOut};
  int login_state_num_{};
};

}  // namespace ballistica::classic

#endif  // BALLISTICA_CLASSIC_SUPPORT_V1_ACCOUNT_H_
