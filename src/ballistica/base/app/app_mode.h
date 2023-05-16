// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_APP_APP_MODE_H_
#define BALLISTICA_BASE_APP_APP_MODE_H_

#include <vector>

#include "ballistica/base/base.h"

namespace ballistica::base {

/// Represents 'what the app is doing'. The global app-mode can be switched
/// as the app is running. Be aware that, unlike the App/App classes
/// which operate in the main thread, most functionality here is based in the
/// logic thread.
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

  /// Apply the app config.
  virtual void ApplyAppConfig();

  /// Update the logic thread. Can be called at any frequency; generally
  /// corresponds to frame draws or a fixed timer.
  virtual void StepDisplayTime();

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

  /// Are we currently in a 'main menu'?
  virtual auto InMainMenu() const -> bool;

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
  virtual auto GetPingString() -> std::string;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_APP_APP_MODE_H_
