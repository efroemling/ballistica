// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/ui/dev_console.h"

#include <Python.h>

#include <algorithm>
#include <memory>
#include <string>
#include <utility>
#include <vector>

#include "ballistica/base/app_adapter/app_adapter.h"
#include "ballistica/base/app_mode/app_mode.h"
#include "ballistica/base/audio/audio.h"
#include "ballistica/base/graphics/component/simple_component.h"
#include "ballistica/base/graphics/mesh/nine_patch_mesh.h"
#include "ballistica/base/graphics/text/text_graphics.h"
#include "ballistica/base/logic/logic.h"
#include "ballistica/base/platform/base_platform.h"
#include "ballistica/base/python/base_python.h"
#include "ballistica/base/support/app_config.h"
#include "ballistica/base/support/context.h"
#include "ballistica/base/support/repeater.h"
#include "ballistica/base/ui/ui.h"
#include "ballistica/shared/foundation/event_loop.h"
#include "ballistica/shared/generic/utils.h"
#include "ballistica/shared/math/vector4f.h"
#include "ballistica/shared/python/python_command.h"

namespace ballistica::base {

// How much of the screen the console covers when it is at full size.
const float kDevConsoleFullSizeCoverage{0.9f};
const float kDevConsoleMiniSize{100.0f};
const int kDevConsoleLineLimit{80};
const int kDevConsoleStringBreakUpSize{1950};
const float kDevConsoleTabButtonCornerRadius{16.0f};
const double kTransitionSeconds{0.15};

enum class DevConsoleHAnchor_ {
  kLeft,
  kCenter,
  kRight,
};

enum class DevButtonStyle_ {
  kNormal,
  kBright,
  kRed,
  kRedBright,
  kPurple,
  kPurpleBright,
  kYellow,
  kYellowBright,
  kBlue,
  kBlueBright,
  kWhite,
  kWhiteBright,
  kBlack,
  kBlackBright,
};

enum class DevConsoleTextStyle_ {
  kNormal,
  kFaded,
};

static auto ButtonStyleFromStr_(const char* strval) {
  if (!strcmp(strval, "normal")) {
    return DevButtonStyle_::kNormal;
  }
  if (!strcmp(strval, "bright")) {
    return DevButtonStyle_::kBright;
  }
  if (!strcmp(strval, "red")) {
    return DevButtonStyle_::kRed;
  }
  if (!strcmp(strval, "red_bright")) {
    return DevButtonStyle_::kRedBright;
  }
  if (!strcmp(strval, "blue")) {
    return DevButtonStyle_::kBlue;
  }
  if (!strcmp(strval, "blue_bright")) {
    return DevButtonStyle_::kBlueBright;
  }
  if (!strcmp(strval, "purple")) {
    return DevButtonStyle_::kPurple;
  }
  if (!strcmp(strval, "purple_bright")) {
    return DevButtonStyle_::kPurpleBright;
  }
  if (!strcmp(strval, "yellow")) {
    return DevButtonStyle_::kYellow;
  }
  if (!strcmp(strval, "yellow_bright")) {
    return DevButtonStyle_::kYellowBright;
  }
  if (!strcmp(strval, "white")) {
    return DevButtonStyle_::kWhite;
  }
  if (!strcmp(strval, "white_bright")) {
    return DevButtonStyle_::kWhiteBright;
  }
  if (!strcmp(strval, "black")) {
    return DevButtonStyle_::kBlack;
  }
  if (!strcmp(strval, "black_bright")) {
    return DevButtonStyle_::kBlackBright;
  }
  g_core->logging->Log(LogName::kBa, LogLevel::kError,
                       std::string("Invalid button-style: ") + strval);
  return DevButtonStyle_::kNormal;
}

static auto TextStyleFromStr_(const char* strval) {
  if (!strcmp(strval, "normal")) {
    return DevConsoleTextStyle_::kNormal;
  }
  if (!strcmp(strval, "faded")) {
    return DevConsoleTextStyle_::kFaded;
  }
  g_core->logging->Log(LogName::kBa, LogLevel::kError,
                       std::string("Invalid text-style: ") + strval);
  return DevConsoleTextStyle_::kNormal;
}

static auto HAttachFromStr_(const char* strval) {
  if (!strcmp(strval, "left")) {
    return DevConsoleHAnchor_::kLeft;
  } else if (!strcmp(strval, "right")) {
    return DevConsoleHAnchor_::kRight;
  }
  assert(!strcmp(strval, "center"));
  return DevConsoleHAnchor_::kCenter;
}

static auto MeshHAlignFromStr_(const char* strval) {
  if (!strcmp(strval, "left")) {
    return TextMesh::HAlign::kLeft;
  } else if (!strcmp(strval, "right")) {
    return TextMesh::HAlign::kRight;
  }
  assert(!strcmp(strval, "center"));
  return TextMesh::HAlign::kCenter;
}

static auto MeshVAlignFromStr_(const char* strval) {
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

static auto IsValidHungryChar_(uint32_t this_char) -> bool {
  // Include letters, numbers, and underscore.
  return ((this_char >= 65 && this_char <= 90)
          || (this_char >= 97 && this_char <= 122)
          || (this_char >= 48 && this_char <= 57) || this_char == '_');
}

static void DrawRect(RenderPass* pass, Mesh* mesh, float x, float y,
                     float width, float height, const Vector3f& bgcolor,
                     float alpha = 1.0f) {
  SimpleComponent c(pass);
  c.SetTransparent(true);
  c.SetColor(bgcolor.x, bgcolor.y, bgcolor.z, alpha);
  c.SetTexture(g_base->assets->SysTexture(SysTextureID::kCircle));
  // Draw mesh bg.
  if (mesh) {
    auto xf = c.ScopedTransform();
    c.Translate(x, y, kDevConsoleZDepth);
    c.DrawMesh(mesh);
  }
}

static void DrawText(RenderPass* pass, TextGroup* tgrp, float tscale, float x,
                     float y, const Vector3f& fgcolor, float alpha = 1.0f) {
  SimpleComponent c(pass);
  c.SetTransparent(true);
  // Draw text.
  {
    auto xf = c.ScopedTransform();
    c.Translate(x, y, kDevConsoleZDepth);
    c.Scale(tscale, tscale, 1.0f);
    int elem_count = tgrp->GetElementCount();
    c.SetColor(fgcolor.x, fgcolor.y, fgcolor.z, alpha);
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
  virtual void HandleMouseCancel(float mx, float my) {}
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
  DevConsoleTextStyle_ style;

  Text_(const std::string& text, float x, float y, DevConsoleHAnchor_ h_attach,
        TextMesh::HAlign h_align, TextMesh::VAlign v_align, float scale,
        DevConsoleTextStyle_ style)
      : h_attach{h_attach},
        h_align(h_align),
        v_align(v_align),
        x{x},
        y{y},
        scale{scale},
        style{style} {
    text_group.SetText(text, h_align, v_align);
  }

  void Draw(RenderPass* pass, float bottom) override {
    auto fgcolor = style == DevConsoleTextStyle_::kFaded
                       ? Vector3f{0.5f, 0.42f, 0.5f}
                       : Vector3f{0.8f, 0.7f, 0.8f};
    DrawText(pass, &text_group, scale, x + XOffs(h_attach), bottom + y,
             fgcolor);
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
  bool disabled;

  template <typename F>
  Button_(const std::string& label, float text_scale, DevConsoleHAnchor_ attach,
          float x, float y, float width, float height, float corner_radius,
          DevButtonStyle_ style, bool disabled, const F& lambda)
      : attach{attach},
        x{x},
        y{y},
        width{width},
        height{height},
        call{NewLambdaRunnable(lambda)},
        text_scale{text_scale},
        style{style},
        disabled{disabled},
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
      if (!disabled) {
        pressed = true;
      }
      return true;
    }
    return false;
  }

  void HandleMouseUp(float mx, float my) override {
    if (pressed) {
      pressed = false;
      if (InUs(mx, my)) {
        if (call.exists()) {
          call.get()->Run();
        }
      }
    }
  }
  void HandleMouseCancel(float mx, float my) override {
    if (pressed) {
      pressed = false;
    }
  }

  void Draw(RenderPass* pass, float bottom) override {
    Vector3f fgcolor;
    Vector3f bgcolor;
    switch (style) {
      case DevButtonStyle_::kYellow:
        fgcolor =
            pressed ? Vector3f{0.0f, 0.0f, 0.0f} : Vector3f{0.9f, 0.8f, 0.9f};
        bgcolor =
            pressed ? Vector3f{0.8f, 0.5f, 0.0f} : Vector3f{0.45, 0.4f, 0.35f};
        break;
      case DevButtonStyle_::kYellowBright:
        fgcolor =
            pressed ? Vector3f{0.0f, 0.0f, 0.0f} : Vector3f{0.0f, 0.0f, 0.0f};
        bgcolor =
            pressed ? Vector3f{1.0f, 0.5f, 0.0f} : Vector3f{0.9, 0.7f, 0.0f};
        break;
      case DevButtonStyle_::kRed:
        fgcolor =
            pressed ? Vector3f{0.0f, 0.0f, 0.0f} : Vector3f{0.9f, 0.8f, 0.9f};
        bgcolor =
            pressed ? Vector3f{1.0f, 0.2f, 0.2f} : Vector3f{0.45, 0.3f, 0.35f};
        break;
      case DevButtonStyle_::kRedBright:
        fgcolor =
            pressed ? Vector3f{0.0f, 0.0f, 0.0f} : Vector3f{0.9f, 0.8f, 0.9f};
        bgcolor =
            pressed ? Vector3f{1.0f, 0.0f, 0.0f} : Vector3f{0.8, 0.05f, 0.1f};
        break;
      case DevButtonStyle_::kPurple:
        fgcolor =
            pressed ? Vector3f{0.0f, 0.0f, 0.0f} : Vector3f{0.9f, 0.8f, 0.9f};
        bgcolor =
            pressed ? Vector3f{0.8f, 0.0f, 1.0f} : Vector3f{0.35, 0.2f, 0.4f};
        break;
      case DevButtonStyle_::kPurpleBright:
        fgcolor =
            pressed ? Vector3f{0.0f, 0.0f, 0.0f} : Vector3f{0.9f, 0.8f, 0.9f};
        bgcolor =
            pressed ? Vector3f{1.0f, 0.5f, 1.0f} : Vector3f{0.6, 0.2f, 0.8f};
        break;
      case DevButtonStyle_::kBlue:
        fgcolor =
            pressed ? Vector3f{0.0f, 0.0f, 0.0f} : Vector3f{0.9f, 0.8f, 0.9f};
        bgcolor =
            pressed ? Vector3f{0.0f, 0.5f, 0.7f} : Vector3f{0.35, 0.4f, 0.55f};
        break;
      case DevButtonStyle_::kBlueBright:
        fgcolor =
            pressed ? Vector3f{0.0f, 0.0f, 0.0f} : Vector3f{0.0f, 0.0f, 0.0f};
        bgcolor =
            pressed ? Vector3f{0.2f, 0.2f, 1.0f} : Vector3f{0.5, 0.7f, 1.0f};
        break;
      case DevButtonStyle_::kWhite:
        fgcolor =
            pressed ? Vector3f{0.0f, 0.0f, 0.0f} : Vector3f{0.9f, 0.8f, 0.9f};
        bgcolor =
            pressed ? Vector3f{0.3f, 0.3f, 0.3f} : Vector3f{0.38, 0.33f, 0.4f};
        break;
      case DevButtonStyle_::kWhiteBright:
        fgcolor =
            pressed ? Vector3f{0.0f, 0.0f, 0.0f} : Vector3f{0.0f, 0.0f, 0.0f};
        bgcolor =
            pressed ? Vector3f{1.0f, 1.0f, 1.0f} : Vector3f{0.9, 0.85f, 0.95f};
        break;
      case DevButtonStyle_::kBlack:
        fgcolor =
            pressed ? Vector3f{0.0f, 0.0f, 0.0f} : Vector3f{0.8f, 0.7f, 0.8f};
        bgcolor =
            pressed ? Vector3f{1.0f, 1.0f, 1.0f} : Vector3f{0.0, 0.0f, 0.0f};
        break;
      case DevButtonStyle_::kBlackBright:
        fgcolor =
            pressed ? Vector3f{1.0f, 1.0f, 1.0f} : Vector3f{1.0f, 0.9f, 1.0f};
        bgcolor =
            pressed ? Vector3f{0.4f, 0.4f, 0.4f} : Vector3f{0.25f, 0.2f, 0.25f};
        break;
      case DevButtonStyle_::kBright:
        fgcolor =
            pressed ? Vector3f{0.0f, 0.0f, 0.0f} : Vector3f{0.9f, 0.8f, 0.9f};
        bgcolor =
            pressed ? Vector3f{0.8f, 0.7f, 0.8f} : Vector3f{0.4, 0.33f, 0.5f};
        break;
      default:
        assert(style == DevButtonStyle_::kNormal);
        fgcolor =
            pressed ? Vector3f{0.0f, 0.0f, 0.0f} : Vector3f{0.8f, 0.7f, 0.8f};
        bgcolor =
            pressed ? Vector3f{0.8f, 0.7f, 0.8f} : Vector3f{0.25, 0.2f, 0.3f};
    }
    float alpha = disabled ? 0.3f : 1.0f;
    DrawRect(pass, &mesh, x + XOffs(attach), bottom + y, width, height, bgcolor,
             alpha);
    DrawText(pass, &text_group, text_scale, x + XOffs(attach) + width * 0.5f,
             bottom + y + height * 0.5f, fgcolor, alpha);
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
        if (call.exists()) {
          call.get()->Run();
        }
      }
    }
  }
  void HandleMouseCancel(float mx, float my) override {
    if (pressed) {
      pressed = false;
    }
  }

  void Draw(RenderPass* pass, float bottom) override {
    DrawRect(pass, &mesh, x + XOffs(attach), bottom + y, width, height,
             pressed ? Vector3f{0.5f, 0.2f, 1.0f}
             : on    ? Vector3f{0.5f, 0.4f, 0.6f}
                     : Vector3f{0.25, 0.2f, 0.3f});
    DrawText(pass, &text_group, text_scale, x + XOffs(attach) + width * 0.5f,
             bottom + y + height * 0.5f,
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

        if (call.exists()) {
          call.get()->Run();
        }
      }
    }
  }
  void HandleMouseCancel(float mx, float my) override {
    if (pressed) {
      pressed = false;
    }
  }

  void Draw(RenderPass* pass, float bottom) override {
    DrawRect(pass, &mesh, x + XOffs(attach), bottom + y, width, height,
             pressed    ? Vector3f{0.4f, 0.2f, 0.8f}
             : selected ? Vector3f{0.4f, 0.3f, 0.4f}
                        : Vector3f{0.25, 0.2f, 0.3f});
    DrawText(pass, &text_group, text_scale, x + XOffs(attach) + width * 0.5f,
             bottom + y + height * 0.5f,
             pressed    ? Vector3f{1.0f, 1.0f, 1.0f}
             : selected ? Vector3f{1.0f, 1.0f, 1.0f}
                        : Vector3f{0.6f, 0.5f, 0.6f});
  }
};

class DevConsole::OutputLine_ {
 public:
  OutputLine_(std::string s_in, double creation_time, float scale,
              Vector4f color)
      : creation_time(creation_time),
        s(std::move(s_in)),
        scale(scale),
        color(color) {}
  std::string s;
  double creation_time;
  float scale;
  Vector4f color;
  auto GetText() -> TextGroup& {
    if (!s_mesh_.exists()) {
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
  if (g_buildconfig.variant_test_build()) {
    title += " (test)";
  }
  title_text_group_.SetText(title);
  built_text_group_.SetText("Built: " __DATE__ " " __TIME__);
  prompt_text_group_.SetText(">");
}

void DevConsole::ApplyAppConfig() {
  assert(g_base->InLogicThread());

  // Read our active tab from app-config only if we don't have one set.
  if (active_tab_.empty()) {
    active_tab_ =
        g_base->app_config->Resolve(AppConfig::StringID::kDevConsoleActiveTab);
  }
}

void DevConsole::OnUIScaleChanged() {
  g_base->logic->event_loop()->PushCall([this] {
    RefreshCloseButton_();
    RefreshTabButtons_();
    RefreshTabContents_();
  });
}

void DevConsole::RefreshCloseButton_() {
  float bs = BaseScale();
  float bwidth = 32.0f * bs;
  float bheight = 26.0f * bs;
  float bscale = 0.6f * bs;
  float x = 0.0f;
  close_button_ = std::make_unique<TabButton_>(
      "×", false, bscale, DevConsoleHAnchor_::kLeft, x, -bheight, bwidth,
      bheight, [this] { Dismiss(); });
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
            RefreshCloseButton_();
            RefreshTabButtons_();
            RefreshTabContents_();
            SaveActiveTab_();
          });
        }));
    x += bwidth;
  }
}

void DevConsole::SaveActiveTab_() {
  assert(g_base->InLogicThread());

  PythonRef args(Py_BuildValue("(s)", active_tab_.c_str()), PythonRef::kSteal);
  g_base->python->objs()
      .Get(BasePython::ObjID::kAppDevConsoleSaveTabCall)
      .Call(args);
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
                         const char* v_align_str, float scale,
                         const char* style_str) {
  auto h_anchor = HAttachFromStr_(h_anchor_str);
  auto h_align = MeshHAlignFromStr_(h_align_str);
  auto v_align = MeshVAlignFromStr_(v_align_str);
  auto style = TextStyleFromStr_(style_str);

  widgets_.emplace_back(std::make_unique<Text_>(text, x, y, h_anchor, h_align,
                                                v_align, scale, style));
}

void DevConsole::AddButton(const char* label, float x, float y, float width,
                           float height, PyObject* call,
                           const char* h_anchor_str, float label_scale,
                           float corner_radius, const char* style_str,
                           bool disabled) {
  assert(g_base->InLogicThread());

  auto style = ButtonStyleFromStr_(style_str);
  auto h_anchor = HAttachFromStr_(h_anchor_str);

  widgets_.emplace_back(std::make_unique<Button_>(
      label, label_scale, h_anchor, x, y, width, height, corner_radius, style,
      disabled, [this, callref = PythonRef::Acquired(call)] {
        if (callref.get() != Py_None) {
          callref.Call();
        }
      }));
}

void DevConsole::AddPythonTerminal() {
  float bs = BaseScale();
  widgets_.emplace_back(std::make_unique<Button_>(
      "Exec", 0.5f * bs, DevConsoleHAnchor_::kRight, -33.0f * bs, 15.95f * bs,
      32.0f * bs, 13.0f * bs, 2.0 * bs, DevButtonStyle_::kNormal, false,
      [this] { Exec(); }));
  widgets_.emplace_back(std::make_unique<Button_>(
      "Copy History", 0.4f * bs, DevConsoleHAnchor_::kRight, -75.0f * bs,
      Height() - 18.0f * bs, 72.0f * bs, 15.0f * bs, 4.0 * bs,
      DevButtonStyle_::kNormal, false, [this] { CopyHistory(); }));
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

    if (close_button_ && close_button_->HandleMouseDown(x, y - bottom)) {
      return true;
    }
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
  if (state_ == State_::kMini) {
    return kDevConsoleMiniSize;
  }
  return g_base->graphics->screen_virtual_height()
         * kDevConsoleFullSizeCoverage;
}

void DevConsole::HandleMouseUp(int button, float x, float y) {
  assert(g_base->InLogicThread());
  float bottom{Bottom_()};

  if (button == 1) {
    // Make sure we don't muck with our UI while we're in here.
    auto lock = ScopedUILock_(this);

    if (close_button_) {
      close_button_->HandleMouseUp(x, y - bottom);
    }

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

void DevConsole::HandleMouseCancel(int button, float x, float y) {
  assert(g_base->InLogicThread());
  float bottom{Bottom_()};

  if (button == 1) {
    // Make sure we don't muck with our UI while we're in here.
    auto lock = ScopedUILock_(this);

    if (close_button_) {
      close_button_->HandleMouseCancel(x, y - bottom);
    }

    for (auto&& button : tab_buttons_) {
      button->HandleMouseCancel(x, y - bottom);
    }
    for (auto&& button : widgets_) {
      button->HandleMouseCancel(x, y - bottom);
    }
  }

  if (button == 1 && python_terminal_pressed_) {
    python_terminal_pressed_ = false;
  }
}

void DevConsole::InvokeStringEditor_() {
  // If there's already a valid edit-adapter attached to us, do nothing.
  if (string_edit_adapter_.exists()
      && !g_base->python->CanPyStringEditAdapterBeReplaced(
          string_edit_adapter_.get())) {
    return;
  }

  // Create a Python StringEditAdapter for this widget, passing ourself as
  // the sole arg.
  auto result = g_base->python->objs()
                    .Get(BasePython::ObjID::kDevConsoleStringEditAdapterClass)
                    .Call();
  if (!result.exists()) {
    g_core->logging->Log(LogName::kBa, LogLevel::kError,
                         "Error invoking string edit dialog.");
    return;
  }

  // If this new one is already marked replacable, it means it wasn't able
  // to register as the active one, so we can ignore it.
  if (g_base->python->CanPyStringEditAdapterBeReplaced(result.get())) {
    return;
  }

  // Ok looks like we're good; store the adapter as our active one.
  string_edit_adapter_ = result;

  g_base->platform->InvokeStringEditor(string_edit_adapter_.get());
}

void DevConsole::set_input_string(const std::string& val) {
  assert(g_base->InLogicThread());
  input_string_ = val;
  input_text_dirty_ = true;
  // Move carat to end.
  carat_char_ =
      static_cast<int>(Utils::UnicodeFromUTF8(input_string_, "fj43t").size());
  assert(CaratCharValid_());
  carat_dirty_ = true;
}

void DevConsole::InputAdapterFinish() {
  assert(g_base->InLogicThread());
  string_edit_adapter_.Release();
}

auto DevConsole::HandleKeyPress(const SDL_Keysym* keysym) -> bool {
  assert(g_base->InLogicThread());

  // Any presses or releases cancels repeat actions.
  key_repeater_.Clear();

  if (state_ == State_::kInactive) {
    return false;
  }

  // Stuff we always look for.
  switch (keysym->sym) {
    case SDLK_ESCAPE:
      Dismiss();
      return true;
    default:
      break;
  }

  // Stuff we look for only when direct keyboard input is enabled and our
  // Python terminal is up.
  if (python_terminal_visible_ && g_base->ui->UIHasDirectKeyboardInput()) {
    bool do_carat_right{};
    bool do_hungry_carat_right{};
    bool do_carat_left{};
    bool do_hungry_carat_left{};
    bool do_history_up{};
    bool do_history_down{};
    bool do_backspace{};
    bool do_forward_delete{};
    bool do_hungry_backspace{};
    bool do_hungry_forward_delete{};
    bool do_move_to_end{};
    bool do_move_to_beginning{};
    bool do_kill_line{};
    switch (keysym->sym) {
      case SDLK_BACKSPACE: {
        if (keysym->mod & KMOD_ALT) {
          do_hungry_backspace = true;
        } else {
          do_backspace = true;
        }
        break;
      }
      case SDLK_DELETE: {
        if (keysym->mod & KMOD_ALT) {
          do_hungry_forward_delete = true;
        } else {
          do_forward_delete = true;
        }
        break;
      }
      case SDLK_HOME:
        do_move_to_beginning = true;
        break;
      case SDLK_END:
        do_move_to_end = true;
        break;
      case SDLK_UP:
        do_history_up = true;
        break;
      case SDLK_DOWN:
        do_history_down = true;
        break;
      case SDLK_RIGHT:
        if (keysym->mod & KMOD_ALT) {
          do_hungry_carat_right = true;
        } else {
          do_carat_right = true;
        }
        break;
      case SDLK_LEFT:
        if (keysym->mod & KMOD_ALT) {
          do_hungry_carat_left = true;
        } else {
          do_carat_left = true;
        }
        break;
      case SDLK_KP_ENTER:
      case SDLK_RETURN: {
        Exec();
        break;
      }

      // Wheeee emacs key shortcuts!!
      case SDLK_n:
        if (keysym->mod & KMOD_CTRL) {
          do_history_down = true;
        }
        break;
      case SDLK_f:
        if (keysym->mod & KMOD_CTRL) {
          do_carat_right = true;
        } else if (keysym->mod & KMOD_ALT) {
          do_hungry_carat_right = true;
        }
        break;
      case SDLK_b:
        if (keysym->mod & KMOD_CTRL) {
          do_carat_left = true;
        } else if (keysym->mod & KMOD_ALT) {
          do_hungry_carat_left = true;
        }
        break;
      case SDLK_p:
        if (keysym->mod & KMOD_CTRL) {
          do_history_up = true;
        }
        break;
      case SDLK_a:
        if (keysym->mod & KMOD_CTRL) {
          do_move_to_beginning = true;
        }
        break;
      case SDLK_d:
        if (keysym->mod & KMOD_CTRL) {
          do_forward_delete = true;
        } else if (keysym->mod & KMOD_ALT) {
          do_hungry_forward_delete = true;
        }
        break;
      case SDLK_e:
        if (keysym->mod & KMOD_CTRL) {
          do_move_to_end = true;
        }
        break;
      case SDLK_k:
        if (keysym->mod & KMOD_CTRL) {
          do_kill_line = true;
        }
      default: {
        break;
      }
    }
    if (do_kill_line) {
      auto unichars = Utils::UnicodeFromUTF8(input_string_, "fjco38");
      assert(CaratCharValid_());
      unichars.resize(carat_char_);
      assert(CaratCharValid_());
      input_string_ = Utils::UTF8FromUnicode(unichars);
      input_text_dirty_ = true;
      carat_dirty_ = true;
    }
    if (do_move_to_beginning) {
      carat_char_ = 0;
      assert(CaratCharValid_());
      carat_dirty_ = true;
    }
    if (do_move_to_end) {
      // Move carat to end.
      carat_char_ = static_cast<int>(
          Utils::UnicodeFromUTF8(input_string_, "fj43t").size());
      assert(CaratCharValid_());
      carat_dirty_ = true;
    }
    if (do_hungry_backspace || do_hungry_carat_left) {
      auto do_delete = do_hungry_backspace;
      key_repeater_ = Repeater::New(
          g_base->app_adapter->GetKeyRepeatDelay(),
          g_base->app_adapter->GetKeyRepeatInterval(), [this, do_delete] {
            auto unichars = Utils::UnicodeFromUTF8(input_string_, "fjco38");
            bool found_valid{};
            // Delete/move until we've found at least one valid char and the
            // stop at the first invalid one.
            while (carat_char_ > 0) {
              assert(CaratCharValid_());
              auto this_char = unichars[carat_char_ - 1];
              auto is_valid = IsValidHungryChar_(this_char);
              if (found_valid && !is_valid) {
                break;
              }
              if (is_valid) {
                found_valid = true;
              }
              if (do_delete) {
                unichars.erase(unichars.begin() + carat_char_ - 1);
              }
              carat_char_ -= 1;
              assert(CaratCharValid_());
            }
            if (do_delete) {
              input_string_ = Utils::UTF8FromUnicode(unichars);
              input_text_dirty_ = true;
            }
            carat_dirty_ = true;
          });
    }
    if (do_hungry_forward_delete || do_hungry_carat_right) {
      auto do_delete = do_hungry_forward_delete;
      key_repeater_ = Repeater::New(
          g_base->app_adapter->GetKeyRepeatDelay(),
          g_base->app_adapter->GetKeyRepeatInterval(), [this, do_delete] {
            auto unichars = Utils::UnicodeFromUTF8(input_string_, "fjco38");
            bool found_valid{};
            // Move until we've found at least one valid char and the
            // stop at the first invalid one.
            while (carat_char_ < static_cast<int>(unichars.size())) {
              assert(CaratCharValid_());
              auto this_char = unichars[carat_char_];
              auto is_valid = IsValidHungryChar_(this_char);
              if (found_valid && !is_valid) {
                break;
              }
              if (is_valid) {
                found_valid = true;
              }
              if (do_delete) {
                unichars.erase(unichars.begin() + carat_char_);
              } else {
                carat_char_ += 1;
              }
              assert(CaratCharValid_());
            }
            if (do_delete) {
              input_string_ = Utils::UTF8FromUnicode(unichars);
              input_text_dirty_ = true;
            }
            carat_dirty_ = true;
          });
    }
    if (do_backspace) {
      key_repeater_ = Repeater::New(
          g_base->app_adapter->GetKeyRepeatDelay(),
          g_base->app_adapter->GetKeyRepeatInterval(), [this] {
            auto unichars = Utils::UnicodeFromUTF8(input_string_, "fjco38");
            if (!unichars.empty() && carat_char_ > 0) {
              assert(CaratCharValid_());
              unichars.erase(unichars.begin() + carat_char_ - 1);
              input_string_ = Utils::UTF8FromUnicode(unichars);
              input_text_dirty_ = true;
              carat_char_ -= 1;
              assert(CaratCharValid_());
              carat_dirty_ = true;
            }
          });
    }
    if (do_forward_delete) {
      key_repeater_ = Repeater::New(
          g_base->app_adapter->GetKeyRepeatDelay(),
          g_base->app_adapter->GetKeyRepeatInterval(), [this] {
            auto unichars = Utils::UnicodeFromUTF8(input_string_, "fjco33");
            if (!unichars.empty()
                && carat_char_ < static_cast<int>(unichars.size())) {
              assert(CaratCharValid_());
              unichars.erase(unichars.begin() + carat_char_);
              input_string_ = Utils::UTF8FromUnicode(unichars);
              input_text_dirty_ = true;
              carat_dirty_ = true;  // Didn't move but might change size.
              assert(CaratCharValid_());
            }
          });
    }
    if (do_carat_left || do_carat_right) {
      key_repeater_ = Repeater::New(
          g_base->app_adapter->GetKeyRepeatDelay(),
          g_base->app_adapter->GetKeyRepeatInterval(),
          [do_carat_left, do_carat_right, this] {
            int offset = do_carat_right ? 1 : -1;
            carat_char_ = std::clamp(
                carat_char_ + offset, 0,
                static_cast<int>(
                    Utils::UnicodeFromUTF8(input_string_, "fffwe").size()));
            assert(CaratCharValid_());
            carat_dirty_ = true;
          });
    }

    if ((do_history_up || do_history_down) && !input_history_.empty()) {
      if (do_history_up) {
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
          carat_char_ = static_cast<int>(
              Utils::UnicodeFromUTF8(input_string_, "fffwe").size());
          assert(CaratCharValid_());
          input_text_dirty_ = true;
          carat_dirty_ = true;
          break;
        }
        j++;
      }
    }
    return true;
  }

  // By default don't claim key events; we want to be able to show the
  // console while still playing/navigating normally.
  return false;
}

auto DevConsole::HandleTextEditing(const std::string& text) -> bool {
  assert(g_base->InLogicThread());
  if (state_ == State_::kInactive) {
    return false;
  }
  assert(CaratCharValid_());
  auto unichars = Utils::UnicodeFromUTF8(input_string_, "jfof8");
  auto addunichars = Utils::UnicodeFromUTF8(text, "jfoef8");
  unichars.insert(unichars.begin() + carat_char_, addunichars.begin(),
                  addunichars.end());
  input_string_ = Utils::UTF8FromUnicode(unichars);
  input_text_dirty_ = true;
  carat_char_ += static_cast<int>(addunichars.size());
  assert(CaratCharValid_());
  carat_dirty_ = true;
  return true;
}

auto DevConsole::HandleKeyRelease(const SDL_Keysym* keysym) -> bool {
  // Any presses or releases cancels repeat actions.
  key_repeater_.Clear();

  // Otherwise absorb *all* key-ups when we're active.
  return state_ != State_::kInactive;
}

void DevConsole::CopyHistory() {
  BA_PRECONDITION(g_base->InLogicThread());
  g_base->python->objs()
      .Get(BasePython::ObjID::kCopyDevConsoleHistoryCall)
      .Call();
}

void DevConsole::Exec() {
  BA_PRECONDITION(g_base->InLogicThread());
  if (!input_enabled_) {
    g_core->logging->Log(LogName::kBa, LogLevel::kWarning,
                         "Console input is not allowed yet.");
    return;
  }
  input_history_position_ = 0;
  if (input_string_ == "clear") {
    output_lines_.clear();
  } else {
    SubmitPythonCommand_(input_string_);
  }
  input_history_.push_front(input_string_);
  if (input_history_.size() > 100) {
    input_history_.pop_back();
  }
  input_string_.resize(0);
  carat_char_ = 0;
  assert(CaratCharValid_());
  input_text_dirty_ = true;
  carat_dirty_ = true;
}

// Just for sanity testing.
auto DevConsole::CaratCharValid_() -> bool {
  return carat_char_ >= 0
         && carat_char_ <= static_cast<int>(
                Utils::UnicodeFromUTF8(input_string_, "fwewffe").size());
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
      if (obj.exists() && obj.get() != Py_None) {
        Print(obj.Repr(), 1.0f, kVector4f1);
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

void DevConsole::CycleState(bool backwards) {
  assert(g_base->InLogicThread());
  state_prev_ = state_;

  // Set our new state.
  switch (state_) {
    case State_::kInactive:
      state_ = backwards ? State_::kFull : State_::kMini;
      break;
    case State_::kMini:
      state_ = backwards ? State_::kInactive : State_::kFull;
      break;
    case State_::kFull:
      state_ = backwards ? State_::kMini : State_::kInactive;
      break;
  }

  if (state_ == State_::kMini || state_ == State_::kFull) {
    if (state_prev_ == State_::kInactive) {
      // Was inactive; refresh everything.
      //
      // Can't muck with UI from code (potentially) called while iterating
      // through UI. So defer it.
      g_base->logic->event_loop()->PushCall([this] {
        RefreshCloseButton_();
        RefreshTabButtons_();
        RefreshTabContents_();
      });
    } else {
      // Was already active; just refresh tab contents.
      //
      // Can't muck with UI from code (potentially) called while iterating
      // through UI. So defer it.
      g_base->logic->event_loop()->PushCall([this] { RefreshTabContents_(); });
    }
  }
  g_base->audio->SafePlaySysSound(SysSoundID::kBlip);
  transition_start_ = g_base->logic->display_time();
}

void DevConsole::Print(const std::string& s_in, float scale, Vector4f color) {
  assert(g_base->InLogicThread());
  std::string s = Utils::GetValidUTF8(s_in.c_str(), "cspr");
  std::vector<std::string> broken_up;
  g_base->text_graphics->BreakUpString(
      s.c_str(), kDevConsoleStringBreakUpSize / scale, &broken_up);

  // Spit out all lines.
  for (size_t i = 0; i < broken_up.size(); i++) {
    output_lines_.emplace_back(broken_up[i], g_base->logic->display_time(),
                               scale, color);
    if (output_lines_.size() > kDevConsoleLineLimit) {
      output_lines_.pop_front();
    }
  }
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
  //
  // Now that we have tabs and drop-shadows hanging down, we have to
  // overshoot the top of the screen when transitioning out.
  float top_buffer = 100.0f;
  if (state_ == State_::kMini) {
    bottom = vh - kDevConsoleMiniSize;
  } else {
    bottom = vh * (1.0f - kDevConsoleFullSizeCoverage);
  }
  if (g_base->logic->display_time() - transition_start_ < kTransitionSeconds) {
    float from_height;
    if (state_prev_ == State_::kMini) {
      from_height = vh - kDevConsoleMiniSize;
    } else if (state_prev_ == State_::kFull) {
      from_height = vh - vh * kDevConsoleFullSizeCoverage;
    } else {
      from_height = vh + top_buffer;
    }
    float to_height;
    if (state_ == State_::kMini) {
      to_height = vh - kDevConsoleMiniSize;
    } else if (state_ == State_::kFull) {
      to_height = vh - vh * kDevConsoleFullSizeCoverage;
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

  // If the virtual screen size has changed, refresh.
  auto screen_virtual_width{g_base->graphics->screen_virtual_width()};
  auto screen_virtual_height{g_base->graphics->screen_virtual_height()};

  if (last_virtual_res_x_ < 0.0f) {
    // First time through, just grab current value; don't refresh.
    last_virtual_res_x_ = screen_virtual_width;
    last_virtual_res_y_ = screen_virtual_height;
  } else {
    // Otherwise if virtual res changed and its been long enough, refresh.
    auto display_time{g_base->logic->display_time()};
    double update_interval{0.2};
    if (display_time > last_virtual_res_change_time_ + update_interval
        && (last_virtual_res_x_ != screen_virtual_width
            || last_virtual_res_y_ != screen_virtual_height)) {
      last_virtual_res_x_ = screen_virtual_width;
      last_virtual_res_y_ = screen_virtual_height;
      last_virtual_res_change_time_ = display_time;
      g_base->logic->event_loop()->PushCall([this] {
        RefreshCloseButton_();
        RefreshTabButtons_();
        RefreshTabContents_();
      });
    }
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

      // Backing.
      c.SetTransparent(true);
      c.SetColor(0.04f, 0, 0.15f, 0.86f);
      c.DrawMesh(&bg_mesh_);
      c.Submit();

      // Stripe.
      if (python_terminal_visible_) {
        c.SetColor(1.0f, 1.0f, 1.0f, 0.1f);
        c.DrawMesh(&stripe_mesh_);
        c.Submit();
      }

      // Border.
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
    }
    {
      SimpleComponent c(pass);
      c.SetFlatness(1.0f);
      c.SetTransparent(true);
      c.SetColor(0.4f, 0.33f, 0.45f, 0.8f);

      // Build.
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

      // Title.
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

      // Prompt.
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

      // Input line.
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
    if (!carat_mesh_.exists() || carat_dirty_) {
      // Note: we explicitly update here if carat is dirty because
      // that updates last_carat_change_time_ which affects whether
      // we draw or not. GetCaratX_() only updates it *if* we draw.
      UpdateCarat_();
    }
    millisecs_t app_time = pass->frame_def()->app_time_millisecs();
    millisecs_t since_change = app_time - last_carat_x_change_time_;
    if (since_change < 300 || since_change % 1000 < 500) {
      SimpleComponent c(pass);
      c.SetTransparent(true);
      c.SetTexture(g_base->assets->SysTexture(SysTextureID::kShadow));
      c.SetColor(0.8, 0.0, 1.0, 0.3f);
      {
        auto xf = c.ScopedTransform();
        auto carat_x = GetCaratX_();
        c.Translate(15.0f * bs, bottom + 14.5f * bs, kDevConsoleZDepth);
        c.Scale(0.5f * bs, 0.5f * bs, 1.0f);
        c.Translate(carat_x, 0.0f, 0.0f);
        c.DrawMesh(carat_glow_mesh_.get());
      }
      c.SetTexture(g_base->assets->SysTexture(SysTextureID::kShadowSharp));
      c.SetColor(1.0, 1.0, 1.0, 1.0f);
      {
        auto xf = c.ScopedTransform();
        auto carat_x = GetCaratX_();
        c.Translate(15.0f * bs, bottom + 14.5f * bs, kDevConsoleZDepth);
        c.Scale(0.5f * bs, 0.5f * bs, 1.0f);
        c.Translate(carat_x, 0.0f, 0.0f);
        c.DrawMesh(carat_mesh_.get());
      }
    }

    // Output lines.
    {
      SimpleComponent c(pass);
      c.SetTransparent(true);
      c.SetFlatness(1.0f);
      float draw_scale = 0.64f;
      float v_inc = 18.0f;
      float h = 0.5f
                * (g_base->graphics->screen_virtual_width()
                   - (kDevConsoleStringBreakUpSize * draw_scale));
      float v = bottom + 32.0f * bs;
      for (auto i = output_lines_.rbegin(); i != output_lines_.rend(); i++) {
        int elem_count = i->GetText().GetElementCount();
        for (int e = 0; e < elem_count; e++) {
          c.SetColor(i->color.x, i->color.y, i->color.z, i->color.a);
          c.SetTexture(i->GetText().GetElementTexture(e));
          {
            auto xf = c.ScopedTransform();
            c.Translate(h, v + 2, kDevConsoleZDepth);
            c.Scale(draw_scale * i->scale, draw_scale * i->scale);
            c.DrawMesh(i->GetText().GetElementMesh(e));
          }
        }
        v += v_inc * i->scale;
        if (v > pass->virtual_height() + v_inc) {
          break;
        }
      }
    }
  }

  // Close Button and Tab Buttons.
  {
    // Make sure we don't muck with our UI while we're in here.
    auto lock = ScopedUILock_(this);

    if (close_button_) {
      close_button_->Draw(pass, bottom);
    }
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
  switch (g_base->ui->uiscale()) {
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

auto DevConsole::PasteFromClipboard() -> bool {
  if (state_ != State_::kInactive) {
    if (python_terminal_visible_) {
      if (g_base->ClipboardIsSupported()) {
        if (g_base->ClipboardHasText()) {
          auto text = g_base->ClipboardGetText();

          // Strip trailing newlines (if we have a single line ending with a
          // newline we want to allow that).

          // Find the position of the last character that is not a newline.
          size_t endpos = text.find_last_not_of("\n\r");
          if (std::string::npos != endpos) {
            // Erase all characters after the last non-newline character.
            text.erase(endpos + 1);
          } else {
            // The string is entirely newlines.
            text.clear();
          }

          if (strstr(text.c_str(), "\n") || strstr(text.c_str(), "\r")) {
            g_base->audio->SafePlaySysSound(SysSoundID::kErrorBeep);
            g_base->ScreenMessage("Can only paste single lines of text.",
                                  Vector3f(1.0f, 0.0f, 0.0f));
          } else {
            HandleTextEditing(text);
          }
          // Ok, we either pasted or complained, so consider it handled.
          return true;
        }
      }
    }
  }
  return false;
}

void DevConsole::UpdateCarat_() {
  last_carat_x_change_time_ = g_core->AppTimeMillisecs();
  auto unichars = Utils::UnicodeFromUTF8(input_string_, "fjfwef");
  auto unichars_clamped = unichars;

  unichars_clamped.resize(carat_char_);
  auto clamped_str = Utils::UTF8FromUnicode(unichars_clamped);
  carat_x_ = g_base->text_graphics->GetStringWidth(clamped_str);

  // Use a base width if we're not covering a char, and use the char's width
  // if we are.
  float width = 14.0f;
  if (carat_char_ < static_cast<int>(unichars.size())) {
    std::vector<uint32_t> covered_char{unichars[carat_char_]};
    auto covered_char_str = Utils::UTF8FromUnicode(covered_char);
    width =
        std::max(3.0f, g_base->text_graphics->GetStringWidth(covered_char_str));
  }

  float height = 32.0f;
  float x_extend = 15.0f;
  float y_extend = 20.0f;
  float x_offset = 2.0f;
  float y_offset = -0.0f;
  float corner_radius = 20.0f;
  float width_fin = width + x_extend * 2.0f;
  float height_fin = height + y_extend * 2.0f;
  float x_border =
      NinePatchMesh::BorderForRadius(corner_radius, width_fin, height_fin);
  float y_border =
      NinePatchMesh::BorderForRadius(corner_radius, height_fin, width_fin);
  carat_glow_mesh_ = Object::New<NinePatchMesh>(
      -x_extend + x_offset, -y_extend + y_offset, 0.0f, width_fin, height_fin,
      x_border, y_border, x_border, y_border);

  corner_radius = 3.0f;
  x_extend = 0.0f;
  y_extend = -3.0f;
  x_offset = 1.0f;
  y_offset = 0.0f;
  width_fin = width + x_extend * 2.0f;
  height_fin = height + y_extend * 2.0f;
  x_border =
      NinePatchMesh::BorderForRadius(corner_radius, width_fin, height_fin);
  y_border =
      NinePatchMesh::BorderForRadius(corner_radius, height_fin, width_fin);
  carat_mesh_ = Object::New<NinePatchMesh>(
      -x_extend + x_offset, -y_extend + y_offset, 0.0f, width_fin, height_fin,
      x_border, y_border, x_border, y_border);
}

auto DevConsole::GetCaratX_() -> float {
  if (carat_dirty_) {
    UpdateCarat_();
    carat_dirty_ = false;
  }
  return carat_x_;
}

}  // namespace ballistica::base
