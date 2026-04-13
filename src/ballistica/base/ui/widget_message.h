// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_UI_WIDGET_MESSAGE_H_
#define BALLISTICA_BASE_UI_WIDGET_MESSAGE_H_

#include <string>

#include "ballistica/core/platform/support/min_sdl.h"

namespace ballistica::base {

// Messages descriptions sent to widgets.
struct WidgetMessage {
  enum class Type {
    kEmptyMessage,
    kMoveUp,
    kMoveDown,
    kMoveLeft,
    kMoveRight,
    kActivate,
    kStart,
    kCancel,
    kShow,
    // In order to work in all-joystick environments,
    // don't rely on the following to be available (they're just a luxury).
    kKey,
    kMouseDown,
    kMouseUp,
    kMouseCancel,
    kMouseWheel,
    kMouseWheelH,
    kMouseWheelVelocity,
    kMouseWheelVelocityH,
    kMouseMove,
    kScrollMouseDown,
    kTextInput,
    kPaste
  };

  Type type{};
  bool has_keysym{};
  SDL_Keysym keysym{};
  float fval1{};
  float fval2{};
  float fval3{};
  float fval4{};
  std::string* sval{};

  explicit WidgetMessage(Type t = Type::kEmptyMessage,
                         const SDL_Keysym* k = nullptr, float f1 = 0,
                         float f2 = 0, float f3 = 0, float f4 = 0,
                         const char* s = nullptr)
      : type(t), has_keysym(false), fval1(f1), fval2(f2), fval3(f3), fval4(f4) {
    if (k) {
      keysym = *k;
      has_keysym = true;
    }
    if (s) {
      sval = new std::string();
      *sval = s;
    } else {
      sval = nullptr;
    }
  }
  ~WidgetMessage() { delete sval; }
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_UI_WIDGET_MESSAGE_H_
