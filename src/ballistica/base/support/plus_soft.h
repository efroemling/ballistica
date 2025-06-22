// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_SUPPORT_PLUS_SOFT_H_
#define BALLISTICA_BASE_SUPPORT_PLUS_SOFT_H_

#include <set>
#include <string>
#include <vector>

#include "ballistica/shared/ballistica.h"
#include "ballistica/shared/foundation/feature_set_native_component.h"

namespace ballistica::base {

/// 'Soft' interface to the plus feature-set, managed by base.
/// Feature-sets listing plus as a soft requirement must limit their use of
/// plus to these methods and should be prepared to handle the not-present
/// case.
class PlusSoftInterface {
 public:
  virtual void OnAppStart() = 0;
  virtual void OnAppSuspend() = 0;
  virtual void OnAppUnsuspend() = 0;
  virtual void OnAppShutdown() = 0;
  virtual void OnAppShutdownComplete() = 0;
  virtual void ApplyAppConfig() = 0;
  virtual void OnScreenSizeChange() = 0;
  virtual void StepDisplayTime() = 0;

  virtual auto IsUnmodifiedBlessedBuild() -> bool = 0;

  virtual auto HasBlessingHash() -> bool = 0;
  virtual auto PutLog(bool fatal) -> bool = 0;
  virtual void AAT() = 0;
  virtual void AATE() = 0;
  virtual auto GAHU() -> std::optional<std::string> = 0;
  virtual void V1LoginDidChange() = 0;
  virtual void SetAdCompletionCall(PyObject* obj,
                                   bool pass_actually_showed) = 0;
  virtual void PushAdViewComplete(const std::string& purpose,
                                  bool actually_showed) = 0;
  virtual void PushPublicPartyState() = 0;
  virtual void PushSetFriendListCall(
      const std::vector<std::string>& friends) = 0;
  virtual void DispatchRemoteAchievementList(
      const std::set<std::string>& achs) = 0;
  virtual void SetProductPrice(const std::string& product,
                               const std::string& price) = 0;

  virtual void PushAnalyticsCall(const std::string& type, int increment) = 0;
  virtual void PushPurchaseTransactionCall(const std::string& item,
                                           const std::string& receipt,
                                           const std::string& signature,
                                           const std::string& order_id,
                                           bool user_initiated) = 0;
  virtual auto GetPublicV1AccountID() -> std::string = 0;
  virtual void DirectSendV1CloudLogs(const std::string& prefix,
                                     const std::string& suffix, bool instant,
                                     int* result) = 0;
  virtual void ClientInfoQuery(const std::string& val1, const std::string& val2,
                               const std::string& val3, int build_number) = 0;
  virtual auto CalcV1PeerHash(const std::string& peer_hash_input)
      -> std::string = 0;
  virtual void V1SetClientInfo(JsonDict* dict) = 0;
  virtual void DoPushSubmitAnalyticsCountsCall(const std::string& sval) = 0;
  virtual void SetHaveIncentivizedAd(bool val) = 0;
  virtual auto HaveIncentivizedAd() -> bool = 0;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_SUPPORT_PLUS_SOFT_H_
