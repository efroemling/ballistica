// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_PLATFORM_BASE_PLATFORM_H_
#define BALLISTICA_BASE_PLATFORM_BASE_PLATFORM_H_

#include "ballistica/base/base.h"
#include "ballistica/shared/python/python_ref.h"

namespace ballistica::base {

/// Most general platform-specific functionality is contained here, to be
/// implemented by platform-specific subclasses. Exceptions to this rule are
/// things such as AppAdapter which are broken out into their own classes so
/// that different adapters (SDL, headless, etc.) may be composed together
/// with a single platform (Windows, Mac, etc.).
class BasePlatform {
 public:
  /// Instantiate the CorePlatform subclass for the current build.
  static auto Create() -> BasePlatform*;

#pragma mark APP EVENTS / LIFECYCLE --------------------------------------------

  /// Called to inform the platform that all subsystems are up and running
  /// and it can start talking to them.
  virtual void OnMainThreadStartAppComplete();

  // Logic thread callbacks.
  virtual void OnAppStart();
  virtual void OnAppPause();
  virtual void OnAppResume();
  virtual void OnAppShutdown();
  virtual void OnAppShutdownComplete();
  virtual void OnScreenSizeChange();
  virtual void DoApplyAppConfig();

#pragma mark IN APP PURCHASES --------------------------------------------------

  void Purchase(const std::string& item);

  // Restore purchases (currently only relevant on Apple platforms).
  virtual void RestorePurchases();

  // Purchase was ack'ed by the master-server (so can consume).
  virtual void PurchaseAck(const std::string& purchase,
                           const std::string& order_id);

#pragma mark ENVIRONMENT -------------------------------------------------------

  /// Get a UUID for the current device that is meant to be publicly shared.
  /// This value will change occasionally due to OS updates, app updates, or
  /// other factors, so it can not be used as a permanent identifier, but it
  /// should remain constant over short periods and should not be easily
  /// changeable by the user, making it useful for purposes such as temporary
  /// server bans or spam prevention.
  auto GetPublicDeviceUUID() -> std::string;

  /// Called when the app should set itself up to intercept ctrl-c presses.
  virtual void SetupInterruptHandling();

#pragma mark INPUT DEVICES -----------------------------------------------------

  // Return a name for a ballistica keycode.
  virtual auto GetKeyName(int keycode) -> std::string;

#pragma mark ACCOUNTS ----------------------------------------------------------

  /// Called when a Python LoginAdapter is requesting an explicit sign-in.
  virtual void LoginAdapterGetSignInToken(const std::string& login_type,
                                          int attempt_id);
  /// Called when a Python LoginAdapter is informing us that a back-end is
  /// active/inactive.
  virtual void LoginAdapterBackEndActiveChange(const std::string& login_type,
                                               bool active);

#pragma mark MISC --------------------------------------------------------------

  /// Do we define a platform-specific string editor? This is something like
  /// a text view popup which allows the use of default OS input methods
  /// such as on-screen-keyboards.
  virtual auto HaveStringEditor() -> bool;

  /// Trigger a string edit for the provided StringEditAdapter Python obj.
  /// This should only be called once the edit-adapter has been verified as
  /// being the globally active one. Must be called from the logic thread.
  void InvokeStringEditor(PyObject* string_edit_adapter);

  /// Open the provided URL in a browser or whatnot.
  void OpenURL(const std::string& url);

  /// Should be called by platform StringEditor to apply a value.
  /// Must be called in the logic thread.
  void StringEditorApply(const std::string& val);

  /// Should be called by platform StringEditor to signify a cancel.
  /// Must be called in the logic thread.
  void StringEditorCancel();

 protected:
  /// Pop up a text edit dialog.
  virtual void DoInvokeStringEditor(const std::string& title,
                                    const std::string& value,
                                    std::optional<int> max_chars);

  /// Open the provided URL in a browser or whatnot.
  virtual void DoOpenURL(const std::string& url);

  /// Make a purchase.
  virtual void DoPurchase(const std::string& item);

  BasePlatform();
  virtual ~BasePlatform();

 private:
  /// Called after our singleton has been instantiated. Any construction
  /// functionality requiring virtual functions resolving to their final
  /// class versions can go here.
  virtual void PostInit();

  bool ran_base_post_init_ : 1 {};
  PythonRef string_edit_adapter_{};
  std::string public_device_uuid_;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_PLATFORM_BASE_PLATFORM_H_
