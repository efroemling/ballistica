// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_SUPPORT_CLASSIC_SOFT_H_
#define BALLISTICA_BASE_SUPPORT_CLASSIC_SOFT_H_

#include <string>
#include <vector>

#include "ballistica/base/base.h"
#include "ballistica/shared/math/vector3f.h"

namespace ballistica::base {

/// 'Soft' interface to the classic feature-set, managed by base.
/// Feature-sets listing classic as a soft requirement must limit their use of
/// it to these methods and should be prepared to handle the not-present
/// case.
class ClassicSoftInterface {
 public:
  virtual auto GetControllerValue(base::InputDevice* device,
                                  const std::string& value_name) -> int = 0;
  virtual auto GetControllerFloatValue(base::InputDevice* device,
                                       const std::string& value_name)
      -> float = 0;
  virtual auto IsV1AccountSignedIn() -> bool = 0;
  virtual auto HandleSignOutV1() -> bool = 0;
  virtual void V2SetV1AccountState(const char* statestr, const char* loginid,
                                   const char* tag) = 0;
  virtual auto GetV1AccountToken() -> std::string = 0;
  virtual auto GetV1AccountExtra() -> std::string = 0;
  virtual auto GetV1AccountExtra2() -> std::string = 0;
  virtual auto GetV1AccountLoginName() -> std::string = 0;
  virtual auto GetV1AccountType() -> int = 0;
  virtual auto GetV1AccountTypeString() -> std::string = 0;
  virtual auto GetV1AccountLoginStateString() -> std::string = 0;
  virtual auto GetV1AccountLoginStateNum() -> int = 0;
  virtual auto GetV1AccountLoginID() -> std::string = 0;
  virtual void SetV1AccountProductsPurchased(
      const std::vector<std::string>& purchases) = 0;
  virtual auto GetV1AccountProductPurchased(const char* item) -> bool = 0;
  virtual auto GetV1AccountProductPurchasesState() -> int = 0;
  virtual void SetV1DeviceAccount(const std::string& name) = 0;
  virtual auto GetClientInfoQueryResponseCall() -> PyObject* = 0;
  virtual auto BuildPublicPartyStateVal() -> PyObject* = 0;
  virtual auto GetV1AccountDisplayString(bool full) -> std::string = 0;
  virtual auto GetV1AccountTypeFromString(const char* value) -> int = 0;
  virtual auto GetV1AccountTypeIconString(int account_type) -> std::string = 0;
  virtual auto V1AccountTypeToString(int account_type) -> std::string = 0;
  virtual void PlayMusic(const std::string& music_type, bool continuous) = 0;
  virtual void GetClassicChestDisplayInfo(const std::string& id,
                                          std::string* texclosed,
                                          std::string* texclosedtint,
                                          Vector3f* color, Vector3f* tint,
                                          Vector3f* tint2) = 0;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_SUPPORT_CLASSIC_SOFT_H_
