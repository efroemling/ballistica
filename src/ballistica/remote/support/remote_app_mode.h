// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_REMOTE_SUPPORT_REMOTE_APP_MODE_H_
#define BALLISTICA_REMOTE_SUPPORT_REMOTE_APP_MODE_H_

#include <cstdint>
#include <vector>

#include "ballistica/base/app_mode/app_mode.h"
#include "ballistica/remote/remote.h"
#include "ballistica/shared/foundation/object.h"
#include "ballistica/shared/python/python_ref.h"

namespace ballistica::remote {

/// The app-mode for using a device as a game controller (being built
/// during the 1.9 cycle). Its Python client finds a game and connects to
/// it; while connected, every input device (touchscreen controls,
/// keyboard, gamepads) feeds controller state to that client through a
/// RemoteInputDeviceDelegate. It wants neither classic networking nor the
/// remote-app server (the client opens its own socket), so the engine's
/// well-known UDP port stays free.
class RemoteAppMode : public base::AppMode {
 public:
  static auto GetSingleton() -> RemoteAppMode*;

  /// Return the singleton if it is the active app-mode, otherwise null.
  static auto GetActive() -> RemoteAppMode*;

  void OnActivate() override;
  void OnDeactivate() override;
  void DrawWorld(base::FrameDef* frame_def) override;
  auto CreateInputDeviceDelegate(base::InputDevice* device)
      -> base::InputDeviceDelegate* override;

  /// Our devices have no main ui to show; a menu request instead becomes
  /// a tap of the remote's menu button (bringing up the game's menu).
  void RequestMainUI() override;

  /// Whether the client is connected to a game (set from Python).
  auto connected() const -> bool { return connected_; }
  void SetConnected(bool connected);

  /// The Python callable that receives combined controller state as
  /// (buttons, h, v) whenever it changes; None to clear.
  void SetInputCallback(PyObject* call);

  /// Called by our delegates whenever their state changes.
  void OnInputStateChanged();

 private:
  RemoteAppMode();
  void SendState_(uint8_t buttons, uint8_t h, uint8_t v);

  Object::Ref<base::TextGroup> text_group_;
  std::vector<Object::WeakRef<RemoteInputDeviceDelegate>> delegates_;
  PythonRef input_callback_;
  bool connected_{};
  uint8_t buttons_{};
  uint8_t h_{128};
  uint8_t v_{128};
};

}  // namespace ballistica::remote

#endif  // BALLISTICA_REMOTE_SUPPORT_REMOTE_APP_MODE_H_
