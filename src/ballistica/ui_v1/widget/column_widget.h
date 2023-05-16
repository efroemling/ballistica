// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_UI_V1_WIDGET_COLUMN_WIDGET_H_
#define BALLISTICA_UI_V1_WIDGET_COLUMN_WIDGET_H_

#include <string>

#include "ballistica/ui_v1/widget/container_widget.h"

namespace ballistica::ui_v1 {

// Widget that arranges its children in a column.
class ColumnWidget : public ContainerWidget {
 public:
  ColumnWidget();
  ~ColumnWidget() override;
  auto HandleMessage(const base::WidgetMessage& m) -> bool override;
  auto GetWidgetTypeName() -> std::string override { return "column"; }

  auto set_left_border(float val) { left_border_ = val; }
  auto left_border() const { return left_border_; }
  auto set_top_border(float val) { top_border_ = val; }
  auto top_border() const { return top_border_; }
  auto set_bottom_border(float val) { bottom_border_ = val; }
  auto bottom_border() const { return bottom_border_; }
  auto set_border(float val) { border_ = val; }
  auto border() const { return border_; }
  auto set_margin(float val) { margin_ = val; }
  auto margin() const { return margin_; }

 protected:
  void UpdateLayout() override;
  float border_{};
  float margin_{10.0f};
  float left_border_{};
  float top_border_{};
  float bottom_border_{};
};

}  // namespace ballistica::ui_v1

#endif  // BALLISTICA_UI_V1_WIDGET_COLUMN_WIDGET_H_
