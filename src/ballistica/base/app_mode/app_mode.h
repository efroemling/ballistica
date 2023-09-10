// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_APP_MODE_APP_MODE_H_
#define BALLISTICA_BASE_APP_MODE_APP_MODE_H_

#include <vector>

#include "ballistica/base/base.h"

namespace ballistica::base {

/// The max amount of time a headless app can sleep if no events are pending.
/// This should not be *too* high or it might cause delays when going from
/// no events present to events present.
const microsecs_t kAppModeMaxHeadlessDisplayStep{500000};

/// The min amount of time a headless app can sleep. This provides an upper
/// limit on stepping overhead in cases where events are densely packed.
const microsecs_t kAppModeMinHeadlessDisplayStep{1000};

/// Represents 'what the app is doing'. The global app-mode can be switched
/// as the app is running. Be aware that, unlike the AppAdapter classes
/// which primarily deal with the main thread, most functionality here is
/// based in the logic thread.
class AppMode {
 public:
  AppMode();
  virtual ~AppMode() = default;

  /// Called when the app-mode is becoming the active one.
  virtual void OnActivate();

  /// Called just before the app-mode ceases being the active one.
  virtual void OnDeactivate();

  virtual void OnAppStart();
  virtual void OnAppPause();
  virtual void OnAppResume();
  virtual void OnAppShutdown();
  virtual void OnAppShutdownComplete();

  /// Apply the app config.
  virtual void DoApplyAppConfig();

  /// Update the logic thread for a new display-time. Can be called at any
  /// frequency. In gui builds, generally corresponds with frame drawing. In
  /// headless builds, generally corresponds with scene stepping or other
  /// scheduled events. Check values on g_base->logic to see current
  /// display-time and most recent step size applied.
  virtual void StepDisplayTime();

  /// Called right after stepping; should return the exact microseconds
  /// between the current display time and the next event the app-mode has
  /// scheduled. If no events are pending, should return
  /// kAppModeMaxHeadlessDisplayStep. This will only be called on headless
  /// builds.
  virtual auto GetHeadlessDisplayStep() -> microsecs_t;

  /// Create a delegate for an input-device.
  /// Return a raw pointer allocated using Object::NewDeferred.
  virtual auto CreateInputDeviceDelegate(InputDevice* device)
      -> InputDeviceDelegate*;

  /// Speed/slow stuff (generally debug builds only).
  virtual void ChangeGameSpeed(int offs);

  /// Used for things like running Python code interactively.
  virtual auto GetForegroundContext() -> ContextRef;

  /// If this returns true, renderers may opt to skip filling with a bg color.
  virtual auto DoesWorldFillScreen() -> bool;

  virtual void DrawWorld(FrameDef* frame_def);

  virtual void GraphicsQualityChanged(GraphicsQuality quality);

  /// Called whenever screen size changes.
  virtual void OnScreenSizeChange();

  /// Called when language changes.
  virtual void LanguageChanged();

  /// Are we currently in a classic 'main menu' session?
  virtual auto InClassicMainMenuSession() const -> bool;

  /// Get current party size (for legacy parties).
  virtual auto GetPartySize() const -> int;

  /// Return whether we are connected to a host (for legacy parties).
  virtual auto HasConnectionToHost() const -> bool;

  /// Return whether we are connected to one or more clients
  /// (for legacy parties).
  virtual auto HasConnectionToClients() const -> bool;

  /// Return real-time when last client joined (for legacy parties).
  /// Returns -1 if nobody has joined yet.
  virtual auto LastClientJoinTime() const -> millisecs_t;

  /// Handle raw network traffic.
  virtual void HandleIncomingUDPPacket(const std::vector<uint8_t>& data_in,
                                       const SockAddr& addr);

  /// Handle a ping packet coming in (legacy). This is called from the
  /// network-reader thread.
  virtual auto HandleJSONPing(const std::string& data_str) -> std::string;

  /// Handle an incoming game query packet (devices on the local network
  /// searching for games).
  virtual void HandleGameQuery(const char* buffer, size_t size,
                               sockaddr_storage* from);

  /// Get a string for debugging current net i/o.
  virtual auto GetNetworkDebugString() -> std::string;

  /// Get a string for current ping display.
  virtual auto GetDisplayPing() -> std::optional<float>;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_APP_MODE_APP_MODE_H_
