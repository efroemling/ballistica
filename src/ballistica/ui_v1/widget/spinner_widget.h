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
  auto GetWidth() -> float override;
  auto GetHeight() -> float override;
  auto GetWidgetTypeName() -> std::string override { return "spinner"; }

  void set_style(Style val) { style_ = val; }

 private:
  float size_{32.0f};
  float presence_{};
  Style style_{Style::kSimple};
  bool visible_{true};
};

}  // namespace ballistica::ui_v1

#endif  // BALLISTICA_UI_V1_WIDGET_SPINNER_WIDGET_H_
