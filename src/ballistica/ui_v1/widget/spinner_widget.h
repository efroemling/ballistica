// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_UI_V1_WIDGET_SPINNER_WIDGET_H_
#define BALLISTICA_UI_V1_WIDGET_SPINNER_WIDGET_H_

#include <string>

#include "ballistica/ui_v1/widget/widget.h"

namespace ballistica::ui_v1 {

class SpinnerWidget : public Widget {
 public:
  enum class Style : uint8_t {
    kBomb,
    kSimple,
  };
  SpinnerWidget();
  ~SpinnerWidget() override;
  void Draw(base::RenderPass* pass, bool transparent) override;
  auto HandleMessage(const base::WidgetMessage& m) -> bool override;
  void set_size(float size) { size_ = size; }

  /// Setting the visibility attr on a spinner will cause it to fade in
  /// gradually when made visible. Setting visible-in-container will not
  /// have this effect.
  void set_visible(bool val) { visible_ = val; }

  void set_fade(bool val) { fade_ = val; }

  /// When fading, how long after becoming visible we stay fully
  /// invisible, and how long the fade-in then takes (seconds). A
  /// short-lived spinner that is gone before the delay is up never
  /// shows at all, which is the point.
  void set_fade_delay(float val) { fade_delay_ = val; }
  void set_fade_duration(float val) { fade_duration_ = val; }
  auto GetWidth() -> float override;
  auto GetHeight() -> float override;
  auto GetWidgetTypeName() -> std::string override { return "spinner"; }

  void set_style(Style val) { style_ = val; }

 private:
  /// Our current alpha, from how long we have been visible.
  auto Alpha_() const -> float;

  float size_{32.0f};
  /// Seconds we have been visible (capped at the fade's end); drains
  /// when hidden so a hide/show flicker doesn't restart the fade.
  float presence_{};
  float fade_delay_{0.5f};
  float fade_duration_{0.5f};
  Style style_{Style::kSimple};
  bool visible_{true};
  bool fade_{true};
};

}  // namespace ballistica::ui_v1

#endif  // BALLISTICA_UI_V1_WIDGET_SPINNER_WIDGET_H_
