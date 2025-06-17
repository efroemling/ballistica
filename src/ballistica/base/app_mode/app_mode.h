// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_APP_MODE_APP_MODE_H_
#define BALLISTICA_BASE_APP_MODE_APP_MODE_H_

#include <string>
#include <vector>

#include "ballistica/base/base.h"

namespace ballistica::base {

/// Represents 'what the app is doing'. The global app-mode can be switched
/// as the app is running. The Python layer has its own Python AppMode
/// classes, and generally when one of them becomes active it calls down
/// to the C++ layer to make a corresponding C++ AppMode class active.
class AppMode {
 public:
  AppMode();
  virtual ~AppMode() = default;

  /// Called when the app-mode is becoming the active one.
  virtual void OnActivate();

  /// Called just before the app-mode ceases being the active one.
  virtual void OnDeactivate();

  /// Logic thread callbacks that run while the app-mode is active.
  virtual void OnAppStart();
  virtual void OnAppSuspend();
  virtual void OnAppUnsuspend();
  virtual void OnAppShutdown();
  virtual void OnAppShutdownComplete();
  virtual void ApplyAppConfig();

  /// Update the logic thread for a new display-time. Can be called at any
  /// frequency. In gui builds, generally corresponds with frame drawing. In
  /// headless builds, generally corresponds with scene stepping or other
  /// scheduled events. Check values on g_base->logic to see current
  /// display-time and most recent step size applied.
  virtual void StepDisplayTime();

  /// Called right after stepping; should return the exact microseconds
  /// between the current display time and the next event the app-mode has
  /// scheduled. If no events are pending, should return
  /// kHeadlessMaxDisplayTimeStep. This will only be called on headless
  /// builds.
  virtual auto GetHeadlessNextDisplayTimeStep() -> microsecs_t;

  /// Create a delegate for an input-device.
  /// Return a raw pointer allocated using Object::NewDeferred.
  virtual auto CreateInputDeviceDelegate(InputDevice* device)
      -> InputDeviceDelegate*;

  /// Attempt to bring up a main ui (generally an in-game menu).
  virtual void RequestMainUI();

  /// Speed/slow stuff (generally debug builds only).
  virtual void ChangeGameSpeed(int offs);

  /// Used for things like running Python code interactively.
  virtual auto GetForegroundContext() -> ContextRef;

  /// If this returns true, renderers may opt to skip filling with a bg color.
  virtual auto DoesWorldFillScreen() -> bool;

  virtual void DrawWorld(FrameDef* frame_def);

  /// Called whenever screen size changes.
  virtual void OnScreenSizeChange();

  /// Called when language changes.
  virtual void LanguageChanged();

  /// Are we currently in a 'main menu' situation (as opposed to gameplay)?
  virtual auto IsInMainMenu() const -> bool;

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

  /// Return the offset used when drawing elements such as fps counters at
  /// the bottom left of the screen. Should be used to avoid overlap with
  /// icons or toolbars placed there by the app-mode.
  virtual auto GetBottomLeftEdgeHeight() -> float;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_APP_MODE_APP_MODE_H_
