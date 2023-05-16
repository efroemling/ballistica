// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_PLATFORM_BASE_PLATFORM_H_
#define BALLISTICA_BASE_PLATFORM_BASE_PLATFORM_H_

#include <list>

#include "ballistica/base/base.h"

namespace ballistica::base {

class BasePlatform {
 public:
  /// Create the proper BasePlatform subclass for the current platform.
  static auto CreatePlatform() -> BasePlatform*;

  /// Create the proper App module and add it to the main_event_loop.
  static auto CreateApp() -> App*;

  /// Create the appropriate Graphics subclass for the app.
  static auto CreateGraphics() -> Graphics*;

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

  /// Open the provided URL in a browser or whatnot.
  void OpenURL(const std::string& url);

  /// Get the most up-to-date cursor position.
  void GetCursorPosition(float* x, float* y);

 protected:
  /// Open the provided URL in a browser or whatnot.
  virtual void DoOpenURL(const std::string& url);

  /// Make a purchase.
  virtual void DoPurchase(const std::string& item);

  BasePlatform();
  virtual ~BasePlatform();

 private:
  /// Called after our singleton has been instantiated.
  /// Any construction functionality requiring virtual functions resolving to
  /// their final class versions can go here.
  virtual void PostInit();

  bool ran_base_post_init_{};
  std::string public_device_uuid_;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_PLATFORM_BASE_PLATFORM_H_
