// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_CLASSIC_CLASSIC_H_
#define BALLISTICA_CLASSIC_CLASSIC_H_

#include <ballistica/base/input/device/input_device.h>

#include <string>
#include <vector>

#include "ballistica/base/support/classic_soft.h"
#include "ballistica/shared/foundation/feature_set_native_component.h"

// Common header that most everything using our feature-set should include.
// It predeclares our feature-set's various types and globals and other
// bits.

// Predeclared types from other feature sets that we use.
namespace ballistica::core {
class CoreFeatureSet;
}
namespace ballistica::base {
class BaseFeatureSet;
}
namespace ballistica::scene_v1 {
class SceneV1FeatureSet;
}
namespace ballistica::ui_v1 {
class UIV1FeatureSet;
}

namespace ballistica::classic {

// Predeclared types our feature-set provides.
class ClassicAppMode;
class ClassicFeatureSet;
class ClassicPython;
class StressTest;
class V1Account;

enum class V1AccountType {
  kInvalid,
  kTest,
  kGameCenter,
  kGameCircle,
  kGooglePlay,
  kDevice,
  kServer,
  kOculus,
  kSteam,
  kNvidiaChina,
  kV2,
};

enum class V1LoginState {
  kSignedOut,
  kSigningIn,
  kSignedIn,
};

// Our feature-set's globals.
// Feature-sets should NEVER directly access globals in another feature-set's
// namespace. All functionality we need from other feature-sets should be
// imported into globals in our own namespace. Generally we do this when we
// are initially imported (just as regular Python modules do).
extern core::CoreFeatureSet* g_core;
extern base::BaseFeatureSet* g_base;
extern ClassicFeatureSet* g_classic;
extern scene_v1::SceneV1FeatureSet* g_scene_v1;
extern ui_v1::UIV1FeatureSet* g_ui_v1;

/// Our C++ front-end to our feature set. This is what other C++
/// feature-sets can 'Import' from us.
class ClassicFeatureSet : public FeatureSetNativeComponent,
                          public base::ClassicSoftInterface {
 public:
  /// Instantiate our FeatureSet if needed and return the single
  /// instance of it. Basically a Python import statement.
  static auto Import() -> ClassicFeatureSet*;

  /// Called when our associated Python module is instantiated.
  static void OnModuleExec(PyObject* module);
  auto GetControllerValue(base::InputDevice* device,
                          const std::string& value_name) -> int override;
  auto GetControllerFloatValue(base::InputDevice* device,
                               const std::string& value_name) -> float override;
  auto IsV1AccountSignedIn() -> bool override;
  auto HandleSignOutV1() -> bool override;
  void V2SetV1AccountState(const char* statestr, const char* loginid,
                           const char* tag) override;
  auto GetV1AccountToken() -> std::string override;
  auto GetV1AccountExtra() -> std::string override;
  auto GetV1AccountExtra2() -> std::string override;
  auto GetV1AccountLoginName() -> std::string override;
  auto GetV1AccountTypeString() -> std::string override;
  auto GetV1AccountLoginStateString() -> std::string override;
  auto GetV1AccountLoginStateNum() -> int override;
  auto GetV1AccountLoginID() -> std::string override;
  void SetV1AccountProductsPurchased(
      const std::vector<std::string>& purchases) override;
  auto GetV1AccountProductPurchased(const char* item) -> bool override;
  auto GetV1AccountProductPurchasesState() -> int override;
  void SetV1DeviceAccount(const std::string& name) override;
  auto GetClientInfoQueryResponseCall() -> PyObject* override;
  auto BuildPublicPartyStateVal() -> PyObject* override;
  auto GetV1AccountDisplayString(bool full) -> std::string override;
  auto GetV1AccountTypeFromString(const char* value) -> int override;
  auto GetV1AccountTypeIconString(int account_type) -> std::string override;
  auto V1AccountTypeToString(int account_type) -> std::string override;
  auto GetV1AccountType() -> int override;
  void GetClassicChestDisplayInfo(const std::string& id, std::string* texclosed,
                                  std::string* texclosedtint, Vector3f* color,
                                  Vector3f* tint, Vector3f* tint2) override;

  ClassicPython* const python;
  V1Account* const v1_account;

  auto v1_account_type() const { return v1_account_type_; }
  void set_v1_account_type(V1AccountType tp) { v1_account_type_ = tp; }
  void PlayMusic(const std::string& music_type, bool continuous) override;

  auto* stress_test() const { return stress_test_; }

 private:
  ClassicFeatureSet();
  V1AccountType v1_account_type_{V1AccountType::kInvalid};
  StressTest* stress_test_;
};

}  // namespace ballistica::classic

#endif  // BALLISTICA_CLASSIC_CLASSIC_H_
