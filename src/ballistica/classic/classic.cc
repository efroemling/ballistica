// Released under the MIT License. See LICENSE for details.

#include "ballistica/classic/classic.h"

#include <string>
#include <vector>

#include "ballistica/classic/python/classic_python.h"
#include "ballistica/classic/support/stress_test.h"
#include "ballistica/classic/support/v1_account.h"
#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging.h"
#include "ballistica/core/platform/core_platform.h"
#include "ballistica/scene_v1/python/scene_v1_python.h"
#include "ballistica/scene_v1/support/player_spec.h"
#include "ballistica/shared/generic/utils.h"
#include "ballistica/ui_v1/ui_v1.h"

namespace ballistica::classic {

core::CoreFeatureSet* g_core{};
base::BaseFeatureSet* g_base{};
ClassicFeatureSet* g_classic{};
scene_v1::SceneV1FeatureSet* g_scene_v1{};
ui_v1::UIV1FeatureSet* g_ui_v1{};

void ClassicFeatureSet::OnModuleExec(PyObject* module) {
  // Ok, our feature-set's Python module is getting imported.
  // Like any normal Python module, we take this opportunity to
  // import/create the stuff we use.

  // Importing core should always be the first thing we do.
  // Various ballistica functionality will fail if this has not been done.
  assert(g_core == nullptr);
  g_core = core::CoreFeatureSet::Import();

  g_core->logging->Log(LogName::kBaLifecycle, LogLevel::kInfo,
                       "_baclassic exec begin");

  // Create our feature-set's C++ front-end.
  assert(g_classic == nullptr);
  g_classic = new ClassicFeatureSet();

  // Store our C++ front-end with our Python module. This is what allows
  // other C++ code to 'import' our C++ front end and talk to us directly.
  g_classic->StoreOnPythonModule(module);

  // Import any Python stuff we use into objs_.
  g_classic->python->ImportPythonObjs();

  // Import any other C++ feature-set-front-ends we use.
  assert(g_base == nullptr);  // Should be getting set once here.
  g_base = base::BaseFeatureSet::Import();

  // Let base know we exist.
  // (save it the trouble of trying to load us if it uses us passively).
  g_base->set_classic(g_classic);

  assert(g_scene_v1 == nullptr);
  g_scene_v1 = scene_v1::SceneV1FeatureSet::Import();

  assert(g_ui_v1 == nullptr);
  g_ui_v1 = ui_v1::UIV1FeatureSet::Import();

  g_core->logging->Log(LogName::kBaLifecycle, LogLevel::kInfo,
                       "_baclassic exec end");
}

ClassicFeatureSet::ClassicFeatureSet()
    : python{new ClassicPython()},
      v1_account{new V1Account()},
      stress_test_{new StressTest()} {
  // We're a singleton. If there's already one of us, something's wrong.
  assert(g_classic == nullptr);
}

auto ClassicFeatureSet::Import() -> ClassicFeatureSet* {
  // Since we provide a native Python module, we piggyback our C++ front-end
  // on top of that. This way our C++ and Python dependencies are resolved
  // consistently no matter which side we are imported from.
  return ImportThroughPythonModule<ClassicFeatureSet>("_baclassic");
}

auto ClassicFeatureSet::GetControllerValue(base::InputDevice* device,
                                           const std::string& value_name)
    -> int {
  return python->GetControllerValue(device, value_name);
}

auto ClassicFeatureSet::GetControllerFloatValue(base::InputDevice* device,
                                                const std::string& value_name)
    -> float {
  return python->GetControllerFloatValue(device, value_name);
}

auto ClassicFeatureSet::IsV1AccountSignedIn() -> bool {
  return v1_account->GetLoginState() == classic::V1LoginState::kSignedIn;
}

auto ClassicFeatureSet::HandleSignOutV1() -> bool {
  // For particular account types we can simply set our state; no need to
  // bring any other parties in to play.
  if (g_classic->v1_account_type() == classic::V1AccountType::kDevice
      || g_classic->v1_account_type() == classic::V1AccountType::kServer
      || g_classic->v1_account_type() == classic::V1AccountType::kV2) {
    g_classic->v1_account->PushSetV1LoginCall(g_classic->v1_account_type(),
                                              classic::V1LoginState::kSignedOut,
                                              "", "");
    return true;  // We handled it.
  }
  // We didn't handle it.
  return false;
}
void ClassicFeatureSet::V2SetV1AccountState(const char* statestr,
                                            const char* loginid,
                                            const char* tag) {
  V1LoginState state;
  if (statestr == std::string("signing_in")) {
    state = classic::V1LoginState::kSigningIn;
  } else if (statestr == std::string("signed_in")) {
    state = classic::V1LoginState::kSignedIn;
  } else {
    throw Exception("Invalid state value.");
  }
  g_classic->v1_account->PushSetV1LoginCall(classic::V1AccountType::kV2, state,
                                            tag, loginid);
}

auto ClassicFeatureSet::GetV1AccountToken() -> std::string {
  return g_classic->v1_account->GetToken();
}

auto ClassicFeatureSet::GetV1AccountExtra() -> std::string {
  return g_classic->v1_account->GetExtra();
}

auto ClassicFeatureSet::GetV1AccountExtra2() -> std::string {
  return g_classic->v1_account->GetExtra2();
}

auto ClassicFeatureSet::GetV1AccountLoginName() -> std::string {
  return g_classic->v1_account->GetLoginName();
}

auto ClassicFeatureSet::GetV1AccountTypeString() -> std::string {
  return V1Account::AccountTypeToString(g_classic->v1_account_type());
}

auto ClassicFeatureSet::GetV1AccountLoginStateString() -> std::string {
  const char* out;
  auto state{g_classic->v1_account->GetLoginState()};
  switch (state) {
    case classic::V1LoginState::kSignedIn:
      out = "signed_in";
      break;
    case classic::V1LoginState::kSignedOut:
      out = "signed_out";
      break;
    case classic::V1LoginState::kSigningIn:
      out = "signing_in";
      break;
    default:
      g_core->logging->Log(LogName::kBa, LogLevel::kError,
                           "Unknown V1LoginState '"
                               + std::to_string(static_cast<int>(state)) + "'");
      out = "signed_out";
      break;
  }
  return out;
}

auto ClassicFeatureSet::GetV1AccountLoginStateNum() -> int {
  int num;
  g_classic->v1_account->GetLoginState(&num);
  return num;
}

auto ClassicFeatureSet::GetV1AccountLoginID() -> std::string {
  return g_classic->v1_account->GetLoginID();
}

void ClassicFeatureSet::SetV1AccountProductsPurchased(
    const std::vector<std::string>& purchases) {
  g_classic->v1_account->SetProductsPurchased(purchases);
}

auto ClassicFeatureSet::GetV1AccountProductPurchased(const char* item) -> bool {
  return g_classic->v1_account->GetProductPurchased(item);
}

auto ClassicFeatureSet::GetV1AccountProductPurchasesState() -> int {
  return g_classic->v1_account->product_purchases_state();
}

void ClassicFeatureSet::SetV1DeviceAccount(const std::string& name) {
  classic::V1AccountType acc_type;

  // on headless builds we keep these distinct from regular
  // device accounts (so we get a 'ServerXXX' name, etc)
  if (g_buildconfig.headless_build()) {
    acc_type = classic::V1AccountType::kServer;
  } else {
    acc_type = classic::V1AccountType::kDevice;
  }
  g_classic->v1_account->PushSetV1LoginCall(
      acc_type, classic::V1LoginState::kSignedIn, name,
      g_core->platform->GetDeviceV1AccountID());
}

auto ClassicFeatureSet::GetClientInfoQueryResponseCall() -> PyObject* {
  return g_scene_v1->python->objs()
      .Get(scene_v1::SceneV1Python::ObjID::kClientInfoQueryResponseCall)
      .get();
}

auto ClassicFeatureSet::BuildPublicPartyStateVal() -> PyObject* {
  return python->BuildPublicPartyStateVal();
}

auto ClassicFeatureSet::GetV1AccountDisplayString(bool full) -> std::string {
  if (full) {
    assert(Utils::IsValidUTF8(
        scene_v1::PlayerSpec::GetAccountPlayerSpec().GetDisplayString()));
    return scene_v1::PlayerSpec::GetAccountPlayerSpec().GetDisplayString();
  } else {
    assert(Utils::IsValidUTF8(
        scene_v1::PlayerSpec::GetAccountPlayerSpec().GetShortName()));
    return scene_v1::PlayerSpec::GetAccountPlayerSpec().GetShortName();
  }
}

auto ClassicFeatureSet::GetV1AccountTypeFromString(const char* value) -> int {
  return static_cast<int>(V1Account::AccountTypeFromString(value));
}

auto ClassicFeatureSet::GetV1AccountTypeIconString(int account_type_in)
    -> std::string {
  return V1Account::AccountTypeToIconString(
      static_cast<V1AccountType>(account_type_in));
}

auto ClassicFeatureSet::V1AccountTypeToString(int account_type_in)
    -> std::string {
  return V1Account::AccountTypeToString(
      static_cast<V1AccountType>(account_type_in));
}

auto ClassicFeatureSet::GetV1AccountType() -> int {
  return static_cast<int>(v1_account_type());
}

void ClassicFeatureSet::PlayMusic(const std::string& music_type,
                                  bool continuous) {
  python->PlayMusic(music_type, continuous);
}

void ClassicFeatureSet::GetClassicChestDisplayInfo(
    const std::string& id, std::string* texclosed, std::string* texclosedtint,
    Vector3f* color, Vector3f* tint, Vector3f* tint2) {
  python->GetClassicChestDisplayInfo(id, texclosed, texclosedtint, color, tint,
                                     tint2);
}

}  // namespace ballistica::classic
