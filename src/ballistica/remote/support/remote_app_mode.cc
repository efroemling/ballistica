// Released under the MIT License. See LICENSE for details.

#include "ballistica/remote/support/remote_app_mode.h"

#include <Python.h>

#include <algorithm>

#include "ballistica/base/base.h"
#include "ballistica/base/graphics/component/simple_component.h"
#include "ballistica/base/graphics/graphics.h"
#include "ballistica/base/graphics/text/text_group.h"
#include "ballistica/base/input/support/remote_app_server.h"
#include "ballistica/remote/support/remote_input_device_delegate.h"

namespace ballistica::remote {

static RemoteAppMode* g_remote_app_mode{};

RemoteAppMode::RemoteAppMode() = default;

auto RemoteAppMode::GetSingleton() -> RemoteAppMode* {
  assert(g_base->InLogicThread());
  if (g_remote_app_mode == nullptr) {
    g_remote_app_mode = new RemoteAppMode();
  }
  return g_remote_app_mode;
}

auto RemoteAppMode::GetActive() -> RemoteAppMode* {
  assert(g_base->InLogicThread());
  if (g_remote_app_mode != nullptr && g_base->app_mode() == g_remote_app_mode) {
    return g_remote_app_mode;
  }
  return nullptr;
}

void RemoteAppMode::OnActivate() {
  assert(g_base->InLogicThread());

  // Reset the engine to a default state and fade in.
  g_base->Reset();
  g_base->graphics->FadeScreen(true, 250, nullptr);
}

void RemoteAppMode::OnDeactivate() {
  assert(g_base->InLogicThread());
  connected_ = false;
  input_callback_.Release();
  delegates_.clear();
}

auto RemoteAppMode::CreateInputDeviceDelegate(base::InputDevice* device)
    -> base::InputDeviceDelegate* {
  auto* delegate = Object::NewDeferred<RemoteInputDeviceDelegate>();

  // Track it so we can combine state across devices (dropping any that
  // have since died).
  delegates_.erase(
      std::remove_if(delegates_.begin(), delegates_.end(),
                     [](const auto& ref) { return !ref.exists(); }),
      delegates_.end());
  delegates_.emplace_back(delegate);
  return delegate;
}

void RemoteAppMode::RequestMainUI() {
  assert(g_base->InLogicThread());
  if (!connected_) {
    return;
  }

  // A press immediately followed by a release; both states go out in
  // order, so the game sees a tap of the menu button.
  SendState_(static_cast<uint8_t>(buttons_ | base::kRemoteStateMenu), h_, v_);
  SendState_(buttons_, h_, v_);
}

void RemoteAppMode::SetConnected(bool connected) {
  assert(g_base->InLogicThread());
  connected_ = connected;
}

void RemoteAppMode::SetInputCallback(PyObject* call) {
  assert(g_base->InLogicThread());
  if (call == Py_None) {
    input_callback_.Release();
  } else {
    input_callback_.Acquire(call);
  }
}

void RemoteAppMode::OnInputStateChanged() {
  assert(g_base->InLogicThread());

  // Buttons held on any device count; the stick comes from whichever
  // device moved its stick most recently.
  uint8_t buttons{};
  uint8_t h{128};
  uint8_t v{128};
  uint64_t newest_axis_serial{};
  for (auto& ref : delegates_) {
    if (auto* delegate = ref.get()) {
      buttons = static_cast<uint8_t>(buttons | delegate->buttons());
      if (delegate->axis_serial() > newest_axis_serial) {
        newest_axis_serial = delegate->axis_serial();
        h = delegate->axis_h();
        v = delegate->axis_v();
      }
    }
  }
  if (buttons == buttons_ && h == h_ && v == v_) {
    return;
  }
  buttons_ = buttons;
  h_ = h;
  v_ = v;
  SendState_(buttons, h, v);
}

void RemoteAppMode::SendState_(uint8_t buttons, uint8_t h, uint8_t v) {
  if (!input_callback_.exists()) {
    return;
  }
  auto args = PythonRef::Stolen(Py_BuildValue("(iii)", buttons, h, v));
  input_callback_.Call(args);
}

void RemoteAppMode::DrawWorld(base::FrameDef* frame_def) {
  // Placeholder until there's real ui.
  if (!text_group_.exists()) {
    text_group_ = Object::New<base::TextGroup>();
    text_group_->SetText("Remote (placeholder)");
  }
  auto& grp(*text_group_);
  auto* pass = frame_def->overlay_pass();

  base::SimpleComponent c(pass);
  c.SetTransparent(true);
  c.SetColor(0.3f, 0.8f, 1.0f, 1.0f);
  {
    auto xf = c.ScopedTransform();

    // Up top, out of the way of the touch controls. Z value -1 will draw
    // us under most everything.
    c.Translate(pass->virtual_width() * 0.5f - 200.0f,
                pass->virtual_height() * 0.85f, -1.0f);
    c.Scale(2.0, 2.0);
    int text_elem_count = grp.GetElementCount();
    for (int e = 0; e < text_elem_count; e++) {
      c.SetTexture(grp.GetElementTexture(e));
      c.SetFlatness(1.0f);
      c.DrawMesh(grp.GetElementMesh(e));
    }
  }
  c.Submit();
}

}  // namespace ballistica::remote
