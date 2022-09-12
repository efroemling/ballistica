// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_INTERNAL_APP_INTERNAL_H_
#define BALLISTICA_INTERNAL_APP_INTERNAL_H_

#include <set>
#include <string>

#include "ballistica/core/types.h"

namespace ballistica {

auto CreateAppInternal() -> AppInternal*;

class AppInternal {
 public:
  virtual ~AppInternal() {}

  virtual auto PyInitialize(void* pyconfig) -> void = 0;
  virtual auto PythonPostInit() -> void = 0;
  virtual auto HasBlessingHash() -> bool = 0;
  virtual auto PutLog(bool fatal) -> bool = 0;
  virtual auto AAT() -> void = 0;
  virtual auto AATE() -> void = 0;
  virtual auto V1LoginDidChange() -> void = 0;
  virtual auto SetAdCompletionCall(PyObject* obj, bool pass_actually_showed)
      -> void = 0;
  virtual auto PushAdViewComplete(const std::string& purpose,
                                  bool actually_showed) -> void = 0;
  virtual auto PushPublicPartyState() -> void = 0;
  virtual auto PushSetFriendListCall(const std::vector<std::string>& friends)
      -> void = 0;
  virtual auto DispatchRemoteAchievementList(const std::set<std::string>& achs)
      -> void = 0;
  virtual auto PushAnalyticsCall(const std::string& type, int increment)
      -> void = 0;
  virtual auto PushPurchaseTransactionCall(const std::string& item,
                                           const std::string& receipt,
                                           const std::string& signature,
                                           const std::string& order_id,
                                           bool user_initiated) -> void = 0;
  virtual auto GetPublicV1AccountID() -> std::string = 0;
  virtual auto OnLogicThreadPause() -> void = 0;
  virtual auto DirectSendLogs(const std::string& prefix,
                              const std::string& suffix, bool instant,
                              int* result = nullptr) -> void = 0;
  virtual auto ClientInfoQuery(const std::string& val1, const std::string& val2,
                               const std::string& val3, int build_number)
      -> void = 0;
  virtual auto CalcV1PeerHash(const std::string& peer_hash_input)
      -> std::string = 0;
  virtual auto V1SetClientInfo(JsonDict* dict) -> void = 0;
};

}  // namespace ballistica

#endif  // BALLISTICA_INTERNAL_APP_INTERNAL_H_
