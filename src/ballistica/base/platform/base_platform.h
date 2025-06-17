// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_PLATFORM_BASE_PLATFORM_H_
#define BALLISTICA_BASE_PLATFORM_BASE_PLATFORM_H_

#include <cstdio>
#include <deque>
#include <mutex>
#include <string>

#include "ballistica/base/base.h"
#include "ballistica/shared/python/python_ref.h"

namespace ballistica::base {

/// EFRO NOTE: I think everything here should be migrated to app_adapter,
///            which perhaps could be renamed to something like
///            app_platform. Having both base_platform and app_adapter feels
///            redundant. If there is functionality shared by multiple
///            app_platforms, it can be implemented as a common base class
///            or via composition.

/// Most general platform-specific functionality is contained here, to be
/// implemented by platform-specific subclasses. Exceptions to this rule are
/// things such as AppAdapter which are broken out into their own classes so
/// that different adapters (SDL, headless, etc.) may be composed together
/// with a single platform (Windows, Mac, etc.).
class BasePlatform {
 public:
  BasePlatform();

  /// Called after our singleton has been instantiated. Any construction
  /// functionality requiring virtual functions resolving to their final
  /// class versions can go here.
  virtual void PostInit();

#pragma mark APP EVENTS / LIFECYCLE --------------------------------------------

  // Logic thread callbacks.
  virtual void OnAppStart();
  virtual void OnAppSuspend();
  virtual void OnAppUnsuspend();
  virtual void OnAppShutdown();
  virtual void OnAppShutdownComplete();
  virtual void OnScreenSizeChange();
  virtual void ApplyAppConfig();

  /// Equivalent of fgets() but modified to not block process exit.
  auto SafeStdinFGetS(char* s, int n, FILE* iop) -> char*;

#pragma mark IN APP PURCHASES --------------------------------------------------

  void Purchase(const std::string& item);

  /// Restore purchases (currently only relevant on Apple platforms).
  virtual void RestorePurchases();

  /// Purchase was processed by the master-server and should now be completed
  /// locally.
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

#pragma mark ACCOUNTS ----------------------------------------------------------

  /// Called when a Python LoginAdapter is requesting an explicit sign-in.
  /// See the LoginAdapter class in Python for usage details.
  virtual void LoginAdapterGetSignInToken(const std::string& login_type,
                                          int attempt_id);
  /// Called when a Python LoginAdapter is informing us that a back-end is
  /// active/inactive. See the LoginAdapter class in Python for usage
  /// details.
  virtual void LoginAdapterBackEndActiveChange(const std::string& login_type,
                                               bool active);

#pragma mark WEB BROWSER -------------------------------------------------------

  /// Open the provided URL in a browser. Can be called from any thread.
  void OpenURL(const std::string& url);

  /// Do we provide a browser window that can show up over content?
  /// This can be used for simple tasks such as signing into accounts
  /// without leaving the app. It is assumed that only one overlay browser
  /// can exist at a time.
  virtual auto OverlayWebBrowserIsSupported() -> bool;

  /// Open the provided URL in an overlay web browser. Can be called from
  /// any thread.
  void OverlayWebBrowserOpenURL(const std::string& url);

  auto OverlayWebBrowserIsOpen() -> bool;

  /// Overlay web browser implementations should call this when they
  /// close, or if they fail to open. Can be called from any thread.
  void OverlayWebBrowserOnClose();

  /// Close any open overlay web browser. Can be called from any thread.
  void OverlayWebBrowserClose();

#pragma mark STRING EDITOR -----------------------------------------------------

  /// Do we define a platform-specific string editor? This is something like
  /// a text view popup which allows the use of default OS input methods
  /// such as on-screen-keyboards.
  virtual auto HaveStringEditor() -> bool;

  /// Trigger a string edit for the provided StringEditAdapter Python obj.
  /// This should only be called once the edit-adapter has been verified as
  /// being the globally active one. Must be called from the logic thread.
  void InvokeStringEditor(PyObject* string_edit_adapter);

  /// Should be called by platform StringEditor to apply a value.
  /// Must be called in the logic thread.
  void StringEditorApply(const std::string& val);

  /// Should be called by platform StringEditor to signify a cancel.
  /// Must be called in the logic thread.
  void StringEditorCancel();

#pragma mark MISC --------------------------------------------------------------

  auto ran_base_post_init() const { return ran_base_post_init_; }

  /// Do we support opening dirs exteranlly? (via finder, windows explorer,
  /// etc.)
  virtual auto SupportsOpenDirExternally() -> bool;

  /// Open a directory using the system default method (Finder, etc.)
  virtual void OpenDirExternally(const std::string& path);

  /// Open a file using the system default method (in another app, etc.)
  virtual void OpenFileExternally(const std::string& path);

 protected:
  /// Pop up a text edit dialog.
  virtual void DoInvokeStringEditor(const std::string& title,
                                    const std::string& value,
                                    std::optional<int> max_chars);

  /// Open the provided URL in a browser. This will always be called in the
  /// main thread.
  virtual void DoOpenURL(const std::string& url);

  /// Open the provided URL in the overlay browser. This will always be called
  /// in the main thread.
  virtual void DoOverlayWebBrowserOpenURL(const std::string& url);

  /// Should close any existing overlay web browser. This will always be called
  /// in the main thread.
  virtual void DoOverlayWebBrowserClose();

  /// Make a purchase.
  virtual void DoPurchase(const std::string& item);

  virtual ~BasePlatform();

 private:
  int SmartGetC_(FILE* stream);

  bool ran_base_post_init_{};
  bool web_overlay_open_{};
  PythonRef string_edit_adapter_{};
  std::string public_device_uuid_;
  std::deque<char> stdin_buffer_;
  std::mutex web_overlay_mutex_;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_PLATFORM_BASE_PLATFORM_H_
