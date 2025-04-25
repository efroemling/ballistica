// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_PYTHON_BASE_PYTHON_H_
#define BALLISTICA_BASE_PYTHON_BASE_PYTHON_H_

#include <set>
#include <string>
#include <vector>

#include "ballistica/base/base.h"
#include "ballistica/shared/python/python_object_set.h"

namespace ballistica::base {

/// General Python support class for the base feature-set.
class BasePython {
 public:
  BasePython();

  void OnMainThreadStartApp();
  void OnAppStart();
  void OnAppSuspend();
  void OnAppUnsuspend();
  void OnAppShutdown();
  void OnAppShutdownComplete();
  void DoApplyAppConfig();
  void OnScreenSizeChange();
  void StepDisplayTime();

  void OnAppActiveChanged();

  void Reset();

  /// Specific Python objects we hold in objs_.
  enum class ObjID {
    kApp,
    kEnv,
    kAppHandleDeepLinkCall,
    kGetResourceCall,
    kTranslateCall,
    kLStrClass,
    kCallClass,
    kGarbageCollectSessionEndCall,
    kConfig,
    kAppOnNativeBootstrappingCompleteCall,
    kResetToMainMenuCall,
    kStoreConfigFullscreenOnCall,
    kStoreConfigFullscreenOffCall,
    kSetConfigFullscreenOnCall,
    kSetConfigFullscreenOffCall,
    kNotSignedInScreenMessageCall,
    kRejectingInviteAlreadyInPartyMessageCall,
    kConnectionFailedMessageCall,
    kTemporarilyUnavailableMessageCall,
    kInProgressMessageCall,
    kErrorMessageCall,
    kSuccessMessageCall,
    kPurchaseNotValidErrorCall,
    kPurchaseAlreadyInProgressErrorCall,
    kVROrientationResetCBMessageCall,
    kVROrientationResetMessageCall,
    kHandleV1CloudLogCall,
    kLanguageTestToggleCall,
    kAwardInControlAchievementCall,
    kAwardDualWieldingAchievementCall,
    kPrintCorruptFileErrorCall,
    kPlayGongSoundCall,
    kLaunchCoopGameCall,
    kPurchasesRestoredMessageCall,
    kDismissWiiRemotesWindowCall,
    kUnavailableMessageCall,
    kSetLastAdNetworkCall,
    kGooglePlayPurchasesNotAvailableMessageCall,
    kGooglePlayServicesNotAvailableMessageCall,
    kEmptyCall,
    kPrintTraceCall,
    kToggleFullscreenCall,
    kUIRemotePressCall,
    kRemoveInGameAdsMessageCall,
    kAppOnNativeStartCall,
    kAppOnNativeSuspendCall,
    kAppOnNativeUnsuspendCall,
    kAppOnNativeShutdownCall,
    kAppOnNativeShutdownCompleteCall,
    kQuitCall,
    kShowPostPurchaseMessageCall,
    kContextError,
    kNotFoundError,
    kNodeNotFoundError,
    kSessionTeamNotFoundError,
    kInputDeviceNotFoundError,
    kDelegateNotFoundError,
    kSessionPlayerNotFoundError,
    kWidgetNotFoundError,
    kActivityNotFoundError,
    kSessionNotFoundError,
    kQuitTypeClass,
    kInputTypeClass,
    kPermissionClass,
    kSpecialCharClass,
    kLstrFromJsonCall,
    kUUIDStrCall,
    kHashStringsCall,
    kHaveAccountV2CredentialsCall,
    kImplicitSignInCall,
    kImplicitSignOutCall,
    kLoginAdapterGetSignInTokenResponseCall,
    kPreEnv,
    kOpenURLWithWebBrowserModuleCall,
    kEnvOnNativeModuleImportCall,
    kOnMainThreadStartAppCall,
    kAppPushApplyAppConfigCall,
    kStringEditAdapterCanBeReplacedCall,
    kDevConsoleStringEditAdapterClass,
    kGetDevConsoleTabNamesCall,
    kAppDevConsoleDoRefreshTabCall,
    kUnsupportedControllerMessageCall,
    kGetV2AccountIdCall,
    kAppOnNativeActiveChangedCall,
    kCopyDevConsoleHistoryCall,
    kAppOnScreenSizeChangeCall,
    kLast  // Sentinel; must be at end.
  };

  void AddPythonClasses(PyObject* module);
  void ImportPythonObjs();
  void ImportPythonAppObjs();
  void SetConfig(PyObject* config);

  const auto& objs() { return objs_; }

  static void EnsureContextAllowsDefaultTimerTypes();

  static auto CanGetPyVector3f(PyObject* o) -> bool;
  static auto GetPyVector3f(PyObject* o) -> Vector3f;

  void StoreEnv(PyObject* obj);
  void StorePreEnv(PyObject* obj);

  void RunDeepLink(const std::string& url);
  auto GetResource(const char* key, const char* fallback_resource = nullptr,
                   const char* fallback_value = nullptr) -> std::string;
  auto GetTranslation(const char* category, const char* s) -> std::string;

  // Fetch raw values from the config dict. The default value is returned if
  // the requested value is not present or not of a compatible type.
  // Note: to get app config values you should generally use the bs::AppConfig
  // functions (which themselves call these functions)
  auto GetRawConfigValue(const char* name)
      -> PyObject*;  // (returns a borrowed ref)
  auto GetRawConfigValue(const char* name, const char* default_value)
      -> std::string;
  auto GetRawConfigValue(const char* name, float default_value) -> float;
  auto GetRawConfigValue(const char* name, std::optional<float> default_value)
      -> std::optional<float>;
  auto GetRawConfigValue(const char* name, int default_value) -> int;
  auto GetRawConfigValue(const char* name, bool default_value) -> bool;
  void SetRawConfigValue(const char* name, float value);

  static auto GetPyEnum_Permission(PyObject* obj) -> Permission;
  static auto GetPyEnum_SpecialChar(PyObject* obj) -> SpecialChar;
  static auto IsPyEnum_InputType(PyObject* obj) -> bool;
  static auto GetPyEnum_InputType(PyObject* obj) -> InputType;
  static auto GetPyEnum_QuitType(PyObject* obj) -> QuitType;

  auto PyQuitType(QuitType val) -> PythonRef;

  auto CanPyStringEditAdapterBeReplaced(PyObject* o) -> bool;

  auto IsPyLString(PyObject* o) -> bool;
  auto GetPyLString(PyObject* o) -> std::string;
  auto GetPyLStrings(PyObject* o) -> std::vector<std::string>;

  /// Call our hook to open a url via Python's webbrowser module.
  void OpenURLWithWebBrowserModule(const std::string& url);

  /// Register Python source code location and returns true if it has not
  /// yet been registered. (for print-once type stuff).
  auto DoOnce() -> bool;

  void SoftImportPlus();
  void SoftImportClassic();

 private:
  std::set<std::string> do_once_locations_;
  PythonObjectSet<ObjID> objs_;
  float last_screen_res_x_{-1.0f};
  float last_screen_res_y_{-1.0f};
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_PYTHON_BASE_PYTHON_H_
