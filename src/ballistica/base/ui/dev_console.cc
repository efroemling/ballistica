// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/ui/dev_console.h"

#include "ballistica/base/app_adapter/app_adapter.h"
#include "ballistica/base/app_mode/app_mode.h"
#include "ballistica/base/audio/audio.h"
#include "ballistica/base/graphics/component/simple_component.h"
#include "ballistica/base/graphics/mesh/nine_patch_mesh.h"
#include "ballistica/base/graphics/text/text_graphics.h"
#include "ballistica/base/input/input.h"
#include "ballistica/base/logic/logic.h"
#include "ballistica/base/platform/base_platform.h"
#include "ballistica/base/python/base_python.h"
#include "ballistica/base/support/repeater.h"
#include "ballistica/base/ui/ui.h"
#include "ballistica/shared/foundation/event_loop.h"
#include "ballistica/shared/generic/utils.h"
#include "ballistica/shared/python/python_command.h"
#include "ballistica/shared/python/python_sys.h"

namespace ballistica::base {

// How much of the screen the console covers when it is at full size.
const float kDevConsoleSize{0.9f};
const int kDevConsoleLineLimit{80};
const int kDevConsoleStringBreakUpSize{1950};
const float kDevConsoleTabButtonCornerRadius{16.0f};

const double kTransitionSeconds{0.15};

enum class DevConsoleHAnchor_ { kLeft, kCenter, kRight };
enum class DevButtonStyle_ { kNormal, kDark };

static auto DevButtonStyleFromStr_(const char* strval) {
  if (!strcmp(strval, "dark")) {
    return DevButtonStyle_::kDark;
  }
  assert(!strcmp(strval, "normal"));
  return DevButtonStyle_::kNormal;
}

static auto DevConsoleHAttachFromStr_(const char* strval) {
  if (!strcmp(strval, "left")) {
    return DevConsoleHAnchor_::kLeft;
  } else if (!strcmp(strval, "right")) {
    return DevConsoleHAnchor_::kRight;
  }
  assert(!strcmp(strval, "center"));
  return DevConsoleHAnchor_::kCenter;
}

static auto TextMeshHAlignFromStr_(const char* strval) {
  if (!strcmp(strval, "left")) {
    return TextMesh::HAlign::kLeft;
  } else if (!strcmp(strval, "right")) {
    return TextMesh::HAlign::kRight;
  }
  assert(!strcmp(strval, "center"));
  return TextMesh::HAlign::kCenter;
}

static auto TextMeshVAlignFromStr_(const char* strval) {
  if (!strcmp(strval, "top")) {
    return TextMesh::VAlign::kTop;
  } else if (!strcmp(strval, "bottom")) {
    return TextMesh::VAlign::kBottom;
  } else if (!strcmp(strval, "none")) {
    return TextMesh::VAlign::kNone;
  }
  assert(!strcmp(strval, "center"));
  return TextMesh::VAlign::kCenter;
}

static auto XOffs(DevConsoleHAnchor_ attach) -> float {
  switch (attach) {
    case DevConsoleHAnchor_::kLeft:
      return 0.0f;
    case DevConsoleHAnchor_::kRight:
      return g_base->graphics->screen_virtual_width();
    case DevConsoleHAnchor_::kCenter:
      return g_base->graphics->screen_virtual_width() * 0.5f;
  }
  assert(false);
  return 0.0f;
}

static void DrawRect(RenderPass* pass, Mesh* mesh, float bottom, float x,
                     float y, float width, float height,
                     const Vector3f& bgcolor) {
  SimpleComponent c(pass);
  c.SetTransparent(true);
  c.SetColor(bgcolor.x, bgcolor.y, bgcolor.z, 1.0f);
  c.SetTexture(g_base->assets->SysTexture(SysTextureID::kCircle));
  // Draw mesh bg.
  if (mesh) {
    auto xf = c.ScopedTransform();
    c.Translate(x, y + bottom, kDevConsoleZDepth);
    c.DrawMesh(mesh);
  }
}

static void DrawText(RenderPass* pass, TextGroup* tgrp, float tscale,
                     float bottom, float x, float y, const Vector3f& fgcolor) {
  SimpleComponent c(pass);
  c.SetTransparent(true);
  // Draw text.
  {
    auto xf = c.ScopedTransform();
    c.Translate(x, y + bottom, kDevConsoleZDepth);
    c.Scale(tscale, tscale, 1.0f);
    int elem_count = tgrp->GetElementCount();
    c.SetColor(fgcolor.x, fgcolor.y, fgcolor.z, 1.0f);
    c.SetFlatness(1.0f);
    for (int e = 0; e < elem_count; e++) {
      c.SetTexture(tgrp->GetElementTexture(e));
      c.DrawMesh(tgrp->GetElementMesh(e));
    }
  }
}

/// Anyone iterating through or mucking with the UI lists should hold one
/// of these while doing so; they simply keep us informed if we're editing
/// UI stuff where we shouldn't be.
class DevConsole::ScopedUILock_ {
 public:
  explicit ScopedUILock_(DevConsole* dev_console) : dev_console_{dev_console} {
    assert(g_base->InLogicThread());
    dev_console_->ui_lock_count_++;
  }
  ~ScopedUILock_() {
    assert(g_base->InLogicThread());
    dev_console_->ui_lock_count_--;
    assert(dev_console_->ui_lock_count_ >= 0);
  }

 private:
  DevConsole* dev_console_;
};

/// Super-simple widget type for populating dev-console
/// (we don't want to depend on any of our full UI feature-sets).
class DevConsole::Widget_ {
 public:
  virtual ~Widget_() = default;
  virtual auto HandleMouseDown(float mx, float my) -> bool { return false; }
  virtual void HandleMouseUp(float mx, float my) {}
  virtual void Draw(RenderPass* pass, float bottom) = 0;
};

class DevConsole::Text_ : public DevConsole::Widget_ {
 public:
  DevConsoleHAnchor_ h_attach;
  TextMesh::HAlign h_align;
  TextMesh::VAlign v_align;
  float x;
  float y;
  float scale;
  TextGroup text_group;
  DevButtonStyle_ style;

  Text_(const std::string& text, float x, float y, DevConsoleHAnchor_ h_attach,
        TextMesh::HAlign h_align, TextMesh::VAlign v_align, float scale)
      : h_attach{h_attach},
        h_align(h_align),
        v_align(v_align),
        x{x},
        y{y},
        scale{scale} {
    text_group.SetText(text, h_align, v_align);
  }

  void Draw(RenderPass* pass, float bottom) override {
    auto fgcolor = Vector3f{0.8f, 0.7f, 0.8f};
    DrawText(pass, &text_group, scale, bottom, x + XOffs(h_attach), y, fgcolor);
  }
};

class DevConsole::Button_ : public DevConsole::Widget_ {
 public:
  DevConsoleHAnchor_ attach;
  float x;
  float y;
  float width;
  float height;
  bool pressed{};
  Object::Ref<Runnable> call;
  NinePatchMesh mesh;
  TextGroup text_group;
  float text_scale;
  DevButtonStyle_ style;

  template <typename F>
  Button_(const std::string& label, float text_scale, DevConsoleHAnchor_ attach,
          float x, float y, float width, float height, float corner_radius,
          DevButtonStyle_ style, const F& lambda)
      : attach{attach},
        x{x},
        y{y},
        width{width},
        height{height},
        call{NewLambdaRunnable(lambda)},
        text_scale{text_scale},
        style{style},
        mesh(0.0f, 0.0f, 0.0f, width, height,
             NinePatchMesh::BorderForRadius(corner_radius, width, height),
             NinePatchMesh::BorderForRadius(corner_radius, height, width),
             NinePatchMesh::BorderForRadius(corner_radius, width, height),
             NinePatchMesh::BorderForRadius(corner_radius, height, width)) {
    text_group.SetText(label, TextMesh::HAlign::kCenter,
                       TextMesh::VAlign::kCenter);
  }

  auto InUs(float mx, float my) -> bool {
    mx -= XOffs(attach);
    return (mx >= x && mx <= (x + width) && my >= y && my <= (y + height));
  }

  auto HandleMouseDown(float mx, float my) -> bool override {
    if (InUs(mx, my)) {
      pressed = true;
      return true;
    }
    return false;
  }

  void HandleMouseUp(float mx, float my) override {
    if (pressed) {
      pressed = false;
      if (InUs(mx, my)) {
        if (call.Exists()) {
          call.Get()->Run();
        }
      }
    }
  }

  void Draw(RenderPass* pass, float bottom) override {
    Vector3f fgcolor;
    Vector3f bgcolor;
    switch (style) {
      case DevButtonStyle_::kDark:
        fgcolor =
            pressed ? Vector3f{0.0f, 0.0f, 0.0f} : Vector3f{0.8f, 0.7f, 0.8f};
        bgcolor =
            pressed ? Vector3f{0.6f, 0.5f, 0.6f} : Vector3f{0.16, 0.07f, 0.18f};
        break;
      default:
        assert(style == DevButtonStyle_::kNormal);
        fgcolor =
            pressed ? Vector3f{0.0f, 0.0f, 0.0f} : Vector3f{0.8f, 0.7f, 0.8f};
        bgcolor =
            pressed ? Vector3f{0.8f, 0.7f, 0.8f} : Vector3f{0.25, 0.2f, 0.3f};
    }
    DrawRect(pass, &mesh, bottom, x + XOffs(attach), y, width, height, bgcolor);
    DrawText(pass, &text_group, text_scale, bottom,
             x + XOffs(attach) + width * 0.5f, y + height * 0.5f, fgcolor);
  }
};

class DevConsole::ToggleButton_ : public DevConsole::Widget_ {
 public:
  DevConsoleHAnchor_ attach;
  float x;
  float y;
  float width;
  float height;
  bool pressed{};
  bool on{};
  Object::Ref<Runnable> on_call;
  Object::Ref<Runnable> off_call;
  NinePatchMesh mesh;
  TextGroup text_group;
  float text_scale;

  template <typename F, typename G>
  ToggleButton_(const std::string& label, float text_scale,
                DevConsoleHAnchor_ attach, float x, float y, float width,
                float height, float corner_radius, const F& on_call,
                const G& off_call)
      : attach{attach},
        x{x},
        y{y},
        width{width},
        height{height},
        on_call{NewLambdaRunnable(on_call)},
        off_call{NewLambdaRunnable(off_call)},
        text_scale{text_scale},
        mesh(0.0f, 0.0f, 0.0f, width, height,
             NinePatchMesh::BorderForRadius(corner_radius, width, height),
             NinePatchMesh::BorderForRadius(corner_radius, height, width),
             NinePatchMesh::BorderForRadius(corner_radius, width, height),
             NinePatchMesh::BorderForRadius(corner_radius, height, width)) {
    text_group.SetText(label, TextMesh::HAlign::kCenter,
                       TextMesh::VAlign::kCenter);
  }

  auto InUs(float mx, float my) -> bool {
    mx -= XOffs(attach);
    return (mx >= x && mx <= (x + width) && my >= y && my <= (y + height));
  }

  auto HandleMouseDown(float mx, float my) -> bool override {
    if (InUs(mx, my)) {
      pressed = true;
      return true;
    }
    return false;
  }

  void HandleMouseUp(float mx, float my) override {
    if (pressed) {
      pressed = false;
      if (InUs(mx, my)) {
        on = !on;
        auto&& call = on ? on_call : off_call;
        if (call.Exists()) {
          call.Get()->Run();
        }
      }
    }
  }

  void Draw(RenderPass* pass, float bottom) override {
    DrawRect(pass, &mesh, bottom, x + XOffs(attach), y, width, height,
             pressed ? Vector3f{0.5f, 0.2f, 1.0f}
             : on    ? Vector3f{0.5f, 0.4f, 0.6f}
                     : Vector3f{0.25, 0.2f, 0.3f});
    DrawText(pass, &text_group, text_scale, bottom,
             x + XOffs(attach) + width * 0.5f, y + height * 0.5f,
             pressed ? Vector3f{1.0f, 1.0f, 1.0f}
             : on    ? Vector3f{1.0f, 1.0f, 1.0f}
                     : Vector3f{0.8f, 0.7f, 0.8f});
  }
};

class DevConsole::TabButton_ : public DevConsole::Widget_ {
 public:
  DevConsoleHAnchor_ attach;
  float x;
  float y;
  float width;
  float height;
  bool pressed{};
  bool selected{};
  Object::Ref<Runnable> call;
  TextGroup text_group;
  NinePatchMesh mesh;
  float text_scale;

  template <typename F>
  TabButton_(const std::string& label, bool selected, float text_scale,
             DevConsoleHAnchor_ attach, float x, float y, float width,
             float height, const F& call)
      : attach{attach},
        x{x},
        y{y},
        selected{selected},
        width{width},
        height{height},
        call{NewLambdaRunnable(call)},
        text_scale{text_scale},
        mesh(0.0f, 0.0f, 0.0f, width, height,
             NinePatchMesh::BorderForRadius(kDevConsoleTabButtonCornerRadius,
                                            width, height),
             NinePatchMesh::BorderForRadius(kDevConsoleTabButtonCornerRadius,
                                            height, width),
             NinePatchMesh::BorderForRadius(kDevConsoleTabButtonCornerRadius,
                                            width, height),
             0.0f) {
    text_group.SetText(label, TextMesh::HAlign::kCenter,
                       TextMesh::VAlign::kCenter);
  }

  auto InUs(float mx, float my) -> bool {
    mx -= XOffs(attach);
    return (mx >= x && mx <= (x + width) && my >= y && my <= (y + height));
  }

  auto HandleMouseDown(float mx, float my) -> bool override {
    if (InUs(mx, my) && !selected) {
      pressed = true;
      return true;
    }
    return false;
  }

  void HandleMouseUp(float mx, float my) override {
    if (pressed) {
      pressed = false;
      if (InUs(mx, my)) {
        // Technically this callback should cause us to be recreated in a
        // selected state, but that happens in a deferred call, so go ahead
        // and set ourself as selected already so we don't flash as
        // unselected for a frame before the deferred call runs.
        selected = true;

        if (call.Exists()) {
          call.Get()->Run();
        }
      }
    }
  }

  void Draw(RenderPass* pass, float bottom) override {
    DrawRect(pass, &mesh, bottom, x + XOffs(attach), y, width, height,
             pressed    ? Vector3f{0.4f, 0.2f, 0.8f}
             : selected ? Vector3f{0.4f, 0.3f, 0.4f}
                        : Vector3f{0.25, 0.2f, 0.3f});
    DrawText(pass, &text_group, text_scale, bottom,
             x + XOffs(attach) + width * 0.5f, y + height * 0.5f,
             pressed    ? Vector3f{1.0f, 1.0f, 1.0f}
             : selected ? Vector3f{1.0f, 1.0f, 1.0f}
                        : Vector3f{0.6f, 0.5f, 0.6f});
  }
};

class DevConsole::OutputLine_ {
 public:
  OutputLine_(std::string s_in, double c)
      : creation_time(c), s(std::move(s_in)) {}
  double creation_time;
  std::string s;
  auto GetText() -> TextGroup& {
    if (!s_mesh_.Exists()) {
      s_mesh_ = Object::New<TextGroup>();
      s_mesh_->SetText(s);
    }
    return *s_mesh_;
  }

 private:
  Object::Ref<TextGroup> s_mesh_;
};

DevConsole::DevConsole() {
  assert(g_base->InLogicThread());
  std::string title = std::string("BallisticaKit ") + kEngineVersion + " ("
                      + std::to_string(kEngineBuildNumber) + ")";
  if (g_buildconfig.debug_build()) {
    title += " (debug)";
  }
  if (g_buildconfig.test_build()) {
    title += " (test)";
  }
  title_text_group_.SetText(title);
  built_text_group_.SetText("Built: " __DATE__ " " __TIME__);
  prompt_text_group_.SetText(">");
}

void DevConsole::RefreshTabButtons_() {
  // IMPORTANT: This code should always be run in its own top level call and
  // never directly from user code. Otherwise we can wind up mucking with
  // the UI list as we're iterating through it.
  assert(!ui_lock_count_);

  // Ask the Python layer for the latest set of tabs.
  tabs_ = g_base->python->objs()
              .Get(BasePython::ObjID::kGetDevConsoleTabNamesCall)
              .Call()
              .ValueAsStringSequence();
  // If we have tabs and none of them are selected, select the first.
  if (!tabs_.empty()) {
    bool found{};
    for (auto&& tab : tabs_) {
      if (active_tab_ == tab) {
        found = true;
        break;
      }
    }
    if (!found) {
      active_tab_ = tabs_.front();
    }
  }

  // Now rebuild our buttons for them.
  tab_buttons_.clear();
  float bs = BaseScale();
  float bwidth = 90.0f * bs;
  float bheight = 26.0f * bs;
  float bscale = 0.6f * bs;
  float total_width = tabs_.size() * bwidth;
  float x = total_width * -0.5f;
  for (auto&& tab : tabs_) {
    tab_buttons_.emplace_back(std::make_unique<TabButton_>(
        tab, active_tab_ == tab, bscale, DevConsoleHAnchor_::kCenter, x,
        -bheight, bwidth, bheight, [this, tab] {
          active_tab_ = tab;
          // Can't muck with UI from code called while iterating through UI.
          // So defer it.
          g_base->logic->event_loop()->PushCall([this] {
            RefreshTabButtons_();
            RefreshTabContents_();
          });
        }));
    x += bwidth;
  }
}

void DevConsole::RefreshTabContents_() {
  BA_PRECONDITION(g_base->InLogicThread());

  // IMPORTANT: This code should always be run in its own top level call and
  // never directly from user code. Otherwise we can wind up mucking with
  // the UI list as we're iterating through it.
  assert(!ui_lock_count_);

  // Consider any refresh requests fulfilled. Subsequent refresh-requests
  // will generate a new refresh at this point.
  refresh_pending_ = false;

  // Clear to an empty slate.
  widgets_.clear();
  python_terminal_visible_ = false;

  // Now ask the Python layer to fill this tab in.
  PythonRef args(Py_BuildValue("(s)", active_tab_.c_str()), PythonRef::kSteal);
  g_base->python->objs()
      .Get(BasePython::ObjID::kAppDevConsoleDoRefreshTabCall)
      .Call(args);
}

void DevConsole::AddText(const char* text, float x, float y,
                         const char* h_anchor_str, const char* h_align_str,
                         const char* v_align_str, float scale) {
  auto h_anchor = DevConsoleHAttachFromStr_(h_anchor_str);
  auto h_align = TextMeshHAlignFromStr_(h_align_str);
  auto v_align = TextMeshVAlignFromStr_(v_align_str);

  widgets_.emplace_back(
      std::make_unique<Text_>(text, x, y, h_anchor, h_align, v_align, scale));
}

void DevConsole::AddButton(const char* label, float x, float y, float width,
                           float height, PyObject* call,
                           const char* h_anchor_str, float label_scale,
                           float corner_radius, const char* style_str) {
  assert(g_base->InLogicThread());

  auto style = DevButtonStyleFromStr_(style_str);
  auto h_anchor = DevConsoleHAttachFromStr_(h_anchor_str);

  widgets_.emplace_back(std::make_unique<Button_>(
      label, label_scale, h_anchor, x, y, width, height, corner_radius, style,
      [this, callref = PythonRef::Acquired(call)] {
        if (callref.Get() != Py_None) {
          callref.Call();
        }
      }));
}

void DevConsole::AddPythonTerminal() {
  float bs = BaseScale();
  widgets_.emplace_back(std::make_unique<Button_>(
      "Exec", 0.5f * bs, DevConsoleHAnchor_::kRight, -33.0f * bs, 15.95f * bs,
      32.0f * bs, 13.0f * bs, 2.0 * bs, DevButtonStyle_::kNormal,
      [this] { Exec(); }));
  python_terminal_visible_ = true;
}

void DevConsole::RequestRefresh() {
  assert(g_base->InLogicThread());

  // Schedule a refresh. If one is already scheduled but hasn't run, do
  // nothing.
  if (refresh_pending_) {
    return;
  }
  refresh_pending_ = true;
  g_base->logic->event_loop()->PushCall([this] { RefreshTabContents_(); });
}

auto DevConsole::HandleMouseDown(int button, float x, float y) -> bool {
  assert(g_base->InLogicThread());

  if (state_ == State_::kInactive) {
    return false;
  }
  float bottom{Bottom_()};

  // Pass to any buttons (in bottom-local space).
  if (button == 1) {
    // Make sure we don't muck with our UI while we're in here.
    auto lock = ScopedUILock_(this);

    for (auto&& button : tab_buttons_) {
      if (button->HandleMouseDown(x, y - bottom)) {
        return true;
      }
    }
    for (auto&& button : widgets_) {
      if (button->HandleMouseDown(x, y - bottom)) {
        return true;
      }
    }
  }

  if (y < bottom) {
    return false;
  }

  if (button == 1 && python_terminal_visible_) {
    python_terminal_pressed_ = true;
  }

  return true;
}

auto DevConsole::Width() -> float {
  return g_base->graphics->screen_virtual_width();
}

auto DevConsole::Height() -> float {
  return g_base->graphics->screen_virtual_height() - Bottom_();
}

void DevConsole::HandleMouseUp(int button, float x, float y) {
  assert(g_base->InLogicThread());
  float bottom{Bottom_()};

  if (button == 1) {
    // Make sure we don't muck with our UI while we're in here.
    auto lock = ScopedUILock_(this);

    for (auto&& button : tab_buttons_) {
      button->HandleMouseUp(x, y - bottom);
    }
    for (auto&& button : widgets_) {
      button->HandleMouseUp(x, y - bottom);
    }
  }

  if (button == 1 && python_terminal_pressed_) {
    python_terminal_pressed_ = false;
    if (y > bottom) {
      // If we're not getting fed keyboard events and have a string editor
      // available, invoke it.
      if (!g_base->ui->UIHasDirectKeyboardInput()
          && g_base->platform->HaveStringEditor()) {
        InvokeStringEditor_();
      }
    }
  }
}

void DevConsole::InvokeStringEditor_() {
  // If there's already a valid edit-adapter attached to us, do nothing.
  if (string_edit_adapter_.Exists()
      && !g_base->python->CanPyStringEditAdapterBeReplaced(
          string_edit_adapter_.Get())) {
    return;
  }

  // Create a Python StringEditAdapter for this widget, passing ourself as
  // the sole arg.
  auto result = g_base->python->objs()
                    .Get(BasePython::ObjID::kDevConsoleStringEditAdapterClass)
                    .Call();
  if (!result.Exists()) {
    Log(LogLevel::kError, "Error invoking string edit dialog.");
    return;
  }

  // If this new one is already marked replacable, it means it wasn't able
  // to register as the active one, so we can ignore it.
  if (g_base->python->CanPyStringEditAdapterBeReplaced(result.Get())) {
    return;
  }

  // Ok looks like we're good; store the adapter as our active one.
  string_edit_adapter_ = result;

  g_base->platform->InvokeStringEditor(string_edit_adapter_.Get());
}

void DevConsole::set_input_string(const std::string& val) {
  assert(g_base->InLogicThread());
  input_string_ = val;
  input_text_dirty_ = true;
}

void DevConsole::InputAdapterFinish() {
  assert(g_base->InLogicThread());
  string_edit_adapter_.Release();
}

auto DevConsole::HandleKeyPress(const SDL_Keysym* keysym) -> bool {
  assert(g_base->InLogicThread());

  // Any presses or releases cancels repeat actions.
  key_repeater_.Clear();

  // Handle our toggle buttons no matter whether we're active.
  //  switch (keysym->sym) {
  //    case kDevConsoleActivateKey1:
  //    case kDevConsoleActivateKey2: {
  //      if (!g_buildconfig.demo_build() && !g_buildconfig.arcade_build()) {
  //        // (reset input so characters don't continue walking and stuff)
  //        g_base->input->ResetHoldStates();
  //        if (auto console = g_base->ui->dev_console()) {
  //          console->ToggleState();
  //        }
  //      }
  //      return true;
  //    }
  //    default:
  //      break;
  //  }

  if (state_ == State_::kInactive) {
    return false;
  }

  // Handle some stuff only while active.
  switch (keysym->sym) {
    case SDLK_ESCAPE:
      Dismiss();
      return true;
    default:
      break;
  }

  // If we support direct keyboard input, and python terminal is showing,
  // handle some keys directly.
  if (python_terminal_visible_ && g_base->ui->UIHasDirectKeyboardInput()) {
    switch (keysym->sym) {
      case SDLK_BACKSPACE: {
        key_repeater_ = Repeater::New(
            g_base->app_adapter->GetKeyRepeatDelay(),
            g_base->app_adapter->GetKeyRepeatInterval(), [this] {
              auto unichars = Utils::UnicodeFromUTF8(input_string_, "fjco38");
              if (!unichars.empty()) {
                unichars.resize(unichars.size() - 1);
                input_string_ = Utils::UTF8FromUnicode(unichars);
                input_text_dirty_ = true;
              }
            });
        break;
      }
      case SDLK_UP:
      case SDLK_DOWN: {
        if (input_history_.empty()) {
          break;
        }
        if (keysym->sym == SDLK_UP) {
          input_history_position_++;
        } else {
          input_history_position_--;
        }
        int input_history_position_used =
            (input_history_position_ - 1)
            % static_cast<int>(input_history_.size());
        int j = 0;
        for (auto& i : input_history_) {
          if (j == input_history_position_used) {
            input_string_ = i;
            input_text_dirty_ = true;
            break;
          }
          j++;
        }
        break;
      }
      case SDLK_KP_ENTER:
      case SDLK_RETURN: {
        Exec();
        break;
      }
      default: {
        break;
      }
    }
    return true;
  }

  // By default don't claim key events; we want to be able to show the
  // console while still playing/navigating normally.
  return false;
}

auto DevConsole::HandleKeyRelease(const SDL_Keysym* keysym) -> bool {
  // Any presses or releases cancels repeat actions.
  key_repeater_.Clear();

  // Otherwise absorb *all* key-ups when we're active.
  return state_ != State_::kInactive;
}

void DevConsole::Exec() {
  BA_PRECONDITION(g_base->InLogicThread());
  if (!input_enabled_) {
    Log(LogLevel::kWarning, "Console input is not allowed yet.");
    return;
  }
  input_history_position_ = 0;
  if (input_string_ == "clear") {
    last_line_.clear();
    output_lines_.clear();
  } else {
    SubmitPythonCommand_(input_string_);
  }
  input_history_.push_front(input_string_);
  if (input_history_.size() > 100) {
    input_history_.pop_back();
  }
  input_string_.resize(0);
  input_text_dirty_ = true;
}

void DevConsole::SubmitPythonCommand_(const std::string& command) {
  assert(g_base);
  g_base->logic->event_loop()->PushCall([command, this] {
    // These are always run in whichever context is 'visible'.
    ScopedSetContext ssc(g_base->app_mode()->GetForegroundContext());
    PythonCommand cmd(command, "<console>");
    if (!g_core->user_ran_commands) {
      g_core->user_ran_commands = true;
    }
    if (cmd.CanEval()) {
      auto obj = cmd.Eval(true, nullptr, nullptr);
      if (obj.Exists() && obj.Get() != Py_None) {
        Print(obj.Repr() + "\n");
      }
    } else {
      // Not eval-able; just exec it.
      cmd.Exec(true, nullptr, nullptr);
    }
  });
}

void DevConsole::EnableInput() {
  assert(g_base->InLogicThread());
  input_enabled_ = true;
}

void DevConsole::Dismiss() {
  assert(g_base->InLogicThread());
  if (state_ == State_::kInactive) {
    return;
  }

  state_prev_ = state_;
  state_ = State_::kInactive;
  transition_start_ = g_base->logic->display_time();
}

void DevConsole::ToggleState() {
  assert(g_base->InLogicThread());
  state_prev_ = state_;
  switch (state_) {
    case State_::kInactive:
      state_ = State_::kMini;
      // Can't muck with UI from code (potentially) called while iterating
      // through UI. So defer it.
      g_base->logic->event_loop()->PushCall([this] {
        RefreshTabButtons_();
        RefreshTabContents_();
      });
      break;
    case State_::kMini:
      state_ = State_::kFull;
      // Can't muck with UI from code (potentially) called while iterating
      // through UI. So defer it.
      g_base->logic->event_loop()->PushCall([this] { RefreshTabContents_(); });
      break;
    case State_::kFull:
      state_ = State_::kInactive;
      break;
  }
  g_base->audio->PlaySound(g_base->assets->SysSound(SysSoundID::kBlip));
  transition_start_ = g_base->logic->display_time();
}

auto DevConsole::HandleTextEditing(const std::string& text) -> bool {
  assert(g_base->InLogicThread());
  if (state_ == State_::kInactive) {
    return false;
  }

  // Ignore back-tick because we use that key to toggle the console.
  //
  // FIXME: Perhaps should allow typing it if some control-character is
  // held?
  if (text == "`") {
    return false;
  }
  input_string_ += text;
  input_text_dirty_ = true;
  return true;
}

void DevConsole::Print(const std::string& s_in) {
  assert(g_base->InLogicThread());
  std::string s = Utils::GetValidUTF8(s_in.c_str(), "cspr");
  last_line_ += s;
  std::vector<std::string> broken_up;
  g_base->text_graphics->BreakUpString(
      last_line_.c_str(), kDevConsoleStringBreakUpSize, &broken_up);

  // Spit out all completed lines and keep the last one as lastline.
  for (size_t i = 0; i < broken_up.size() - 1; i++) {
    output_lines_.emplace_back(broken_up[i], g_base->logic->display_time());
    if (output_lines_.size() > kDevConsoleLineLimit) {
      output_lines_.pop_front();
    }
  }
  last_line_ = broken_up[broken_up.size() - 1];
  last_line_mesh_dirty_ = true;
}

auto DevConsole::Bottom_() const -> float {
  float vh = g_base->graphics->screen_virtual_height();

  float ratio =
      (g_base->logic->display_time() - transition_start_) / kTransitionSeconds;
  float bottom;

  // NOTE: Originally I was tweaking this based on UI scale, but I decided
  // that it would be a better idea to have a constant value everywhere.
  // dev-consoles are not meant to be especially pretty and I think it is
  // more important for them to be able to be written to a known hard-coded
  // mini-size.
  float mini_size = 100.0f;

  // Now that we have tabs and drop-shadows hanging down, we have to
  // overshoot the top of the screen when transitioning out.
  float top_buffer = 100.0f;
  if (state_ == State_::kMini) {
    bottom = vh - mini_size;
  } else {
    bottom = vh - vh * kDevConsoleSize;
  }
  if (g_base->logic->display_time() - transition_start_ < kTransitionSeconds) {
    float from_height;
    if (state_prev_ == State_::kMini) {
      from_height = vh - mini_size;
    } else if (state_prev_ == State_::kFull) {
      from_height = vh - vh * kDevConsoleSize;
    } else {
      from_height = vh + top_buffer;
    }
    float to_height;
    if (state_ == State_::kMini) {
      to_height = vh - mini_size;
    } else if (state_ == State_::kFull) {
      to_height = vh - vh * kDevConsoleSize;
    } else {
      to_height = vh + top_buffer;
    }
    bottom = to_height * ratio + from_height * (1.0 - ratio);
  }
  return bottom;
}

void DevConsole::Draw(FrameDef* frame_def) {
  float bs = BaseScale();
  RenderPass* pass = frame_def->overlay_front_pass();

  // If we're not yet transitioning in for the first time OR have completed
  // transitioning out, do nothing.
  if (transition_start_ <= 0.0
      || (state_ == State_::kInactive
          && ((g_base->logic->display_time() - transition_start_)
              >= kTransitionSeconds))) {
    return;
  }

  float bottom = Bottom_();

  float border_height{3.0f};
  {
    bg_mesh_.SetPositionAndSize(0, bottom, kDevConsoleZDepth,
                                pass->virtual_width(),
                                (pass->virtual_height() - bottom));
    stripe_mesh_.SetPositionAndSize(0, bottom + 15.0f * bs, kDevConsoleZDepth,
                                    pass->virtual_width(), 15.0f * bs);
    border_mesh_.SetPositionAndSize(0, bottom - border_height * bs,
                                    kDevConsoleZDepth, pass->virtual_width(),
                                    border_height * bs);
    {
      SimpleComponent c(pass);
      c.SetTransparent(true);
      c.SetColor(0, 0, 0.1f, 0.9f);
      c.DrawMesh(&bg_mesh_);
      c.Submit();
      if (python_terminal_visible_) {
        c.SetColor(1.0f, 1.0f, 1.0f, 0.1f);
        c.DrawMesh(&stripe_mesh_);
        c.Submit();
      }
      c.SetColor(0.25f, 0.2f, 0.3f, 1.0f);
      c.DrawMesh(&border_mesh_);
    }
  }

  // Drop shadow.
  {
    SimpleComponent c(pass);
    c.SetTransparent(true);
    c.SetColor(0.03, 0, 0.09, 0.9f);
    c.SetTexture(g_base->assets->SysTexture(SysTextureID::kSoftRectVertical));
    {
      auto scissor = c.ScopedScissor({0.0f, 0.0f, pass->virtual_width(),
                                      bottom - (border_height * 0.75f) * bs});
      auto xf = c.ScopedTransform();
      c.Translate(pass->virtual_width() * 0.5f, bottom + 160.0f);
      c.Scale(pass->virtual_width() * 1.2f, 600.0f);
      c.DrawMeshAsset(g_base->assets->SysMesh(SysMeshID::kImage1x1));
    }
  }

  if (python_terminal_visible_) {
    if (input_text_dirty_) {
      input_text_group_.SetText(input_string_);
      input_text_dirty_ = false;
      last_input_text_change_time_ = pass->frame_def()->app_time_millisecs();
    }
    {
      SimpleComponent c(pass);
      c.SetFlatness(1.0f);
      c.SetTransparent(true);
      c.SetColor(0.4f, 0.33f, 0.45f, 0.8f);
      int elem_count = built_text_group_.GetElementCount();
      for (int e = 0; e < elem_count; e++) {
        c.SetTexture(built_text_group_.GetElementTexture(e));
        {
          auto xf = c.ScopedTransform();
          c.Translate(pass->virtual_width() - 115.0f * bs, bottom + 1.9f * bs,
                      kDevConsoleZDepth);
          c.Scale(0.35f * bs, 0.35f * bs, 1.0f);
          c.DrawMesh(built_text_group_.GetElementMesh(e));
        }
      }
      elem_count = title_text_group_.GetElementCount();
      for (int e = 0; e < elem_count; e++) {
        c.SetTexture(title_text_group_.GetElementTexture(e));
        {
          auto xf = c.ScopedTransform();
          c.Translate(10.0f * bs, bottom + 1.9f * bs, kDevConsoleZDepth);
          c.Scale(0.35f * bs, 0.35f * bs, 1.0f);
          c.DrawMesh(title_text_group_.GetElementMesh(e));
        }
      }
      elem_count = prompt_text_group_.GetElementCount();
      for (int e = 0; e < elem_count; e++) {
        c.SetTexture(prompt_text_group_.GetElementTexture(e));
        c.SetColor(1, 1, 1, 1);
        {
          auto xf = c.ScopedTransform();
          c.Translate(5.0f * bs, bottom + 14.5f * bs, kDevConsoleZDepth);
          c.Scale(0.5f * bs, 0.5f * bs, 1.0f);
          c.DrawMesh(prompt_text_group_.GetElementMesh(e));
        }
      }
      elem_count = input_text_group_.GetElementCount();
      for (int e = 0; e < elem_count; e++) {
        c.SetTexture(input_text_group_.GetElementTexture(e));
        {
          auto xf = c.ScopedTransform();
          c.Translate(15.0f * bs, bottom + 14.5f * bs, kDevConsoleZDepth);
          c.Scale(0.5f * bs, 0.5f * bs, 1.0f);
          c.DrawMesh(input_text_group_.GetElementMesh(e));
        }
      }
    }

    // Carat.
    millisecs_t real_time = pass->frame_def()->app_time_millisecs();
    if (real_time % 200 < 100
        || (real_time - last_input_text_change_time_ < 100)) {
      SimpleComponent c(pass);
      c.SetTransparent(true);
      c.SetColor(1, 1, 1, 0.7f);
      {
        auto xf = c.ScopedTransform();
        c.Translate(
            (19.0f
             + g_base->text_graphics->GetStringWidth(input_string_) * 0.5f)
                * bs,
            bottom + 22.5f * bs, kDevConsoleZDepth);
        c.Scale(6.0f * bs, 12.0f * bs, 1.0f);
        c.DrawMeshAsset(g_base->assets->SysMesh(SysMeshID::kImage1x1));
      }
    }

    // Output lines.
    {
      SimpleComponent c(pass);
      c.SetTransparent(true);
      c.SetColor(1, 1, 1, 1);
      c.SetFlatness(1.0f);
      float draw_scale = 0.6f;
      float v_inc = 18.0f;
      float h = 0.5f
                * (g_base->graphics->screen_virtual_width()
                   - (kDevConsoleStringBreakUpSize * draw_scale));
      float v = bottom + 32.0f * bs;
      if (!last_line_.empty()) {
        if (last_line_mesh_dirty_) {
          if (!last_line_mesh_group_.Exists()) {
            last_line_mesh_group_ = Object::New<TextGroup>();
          }
          last_line_mesh_group_->SetText(last_line_);
          last_line_mesh_dirty_ = false;
        }
        int elem_count = last_line_mesh_group_->GetElementCount();
        for (int e = 0; e < elem_count; e++) {
          c.SetTexture(last_line_mesh_group_->GetElementTexture(e));
          {
            auto xf = c.ScopedTransform();
            c.Translate(h, v + 2, kDevConsoleZDepth);
            c.Scale(draw_scale, draw_scale);
            c.DrawMesh(last_line_mesh_group_->GetElementMesh(e));
          }
        }
        v += v_inc;
      }
      for (auto i = output_lines_.rbegin(); i != output_lines_.rend(); i++) {
        int elem_count = i->GetText().GetElementCount();
        for (int e = 0; e < elem_count; e++) {
          c.SetTexture(i->GetText().GetElementTexture(e));
          {
            auto xf = c.ScopedTransform();
            c.Translate(h, v + 2, kDevConsoleZDepth);
            c.Scale(draw_scale, draw_scale);
            c.DrawMesh(i->GetText().GetElementMesh(e));
          }
        }
        v += v_inc;
        if (v > pass->virtual_height() + v_inc) {
          break;
        }
      }
    }
  }

  // Tab Buttons.
  {
    // Make sure we don't muck with our UI while we're in here.
    auto lock = ScopedUILock_(this);

    for (auto&& button : tab_buttons_) {
      button->Draw(pass, bottom);
    }
  }

  // Buttons.
  {
    // Make sure we don't muck with our UI while we're in here.
    auto lock = ScopedUILock_(this);

    for (auto&& button : widgets_) {
      button->Draw(pass, bottom);
    }
  }
}

auto DevConsole::BaseScale() const -> float {
  switch (g_base->ui->scale()) {
    case UIScale::kLarge:
      return 1.5f;
    case UIScale::kMedium:
      return 1.75f;
    case UIScale::kSmall:
    case UIScale::kLast:
      return 2.0f;
  }
  FatalError("Unhandled scale.");
  return 1.0f;
}

void DevConsole::StepDisplayTime() {
  assert(g_base->InLogicThread());

  // IMPORTANT: We can muck with UI here so make sure noone is iterating
  // through or editing it.
  assert(!ui_lock_count_);

  // If we're inactive, blow away all our stuff once we transition fully
  // off screen. This will kill any Python stuff attached to our widgets
  // so things can clean themselves up.
  if (state_ == State_::kInactive && !tab_buttons_.empty()) {
    if ((g_base->logic->display_time() - transition_start_)
        >= kTransitionSeconds) {
      // Reset to a blank slate but *don't refresh anything (that will
      // happen once we get vis'ed again).
      tab_buttons_.clear();
      widgets_.clear();
      python_terminal_visible_ = false;
    }
  }
}

}  // namespace ballistica::base
