// Released under the MIT License. See LICENSE for details.

#include "ballistica/ui_v1/widget/column_widget.h"

namespace ballistica::ui_v1 {

ColumnWidget::ColumnWidget() {
  set_background(false);  // Influences default event handling; ew.
  set_claims_left_right(false);
  set_draggable(false);
  set_selection_loops(false);
}

ColumnWidget::~ColumnWidget() = default;

auto ColumnWidget::HandleMessage(const base::WidgetMessage& m) -> bool {
  switch (m.type) {
    case base::WidgetMessage::Type::kShow: {
      // Told to show something... send this along to our parent (we can't do
      // anything).
      Widget* w = parent_widget();
      if (w) {
        w->HandleMessage(m);
      }
      return true;
    }
    default:
      break;
  }
  return ContainerWidget::HandleMessage(m);
}

void ColumnWidget::UpdateLayout() {
  BA_DEBUG_UI_READ_LOCK;

  float total_height{2.0f * margin_};
  for (const auto& i : widgets()) {
    float wh = (*i).GetHeight() * (*i).scale();
    total_height += 2.0f * border_ + wh + top_border_ + bottom_border_;
  }
  float b{total_height - margin_};
  float l{border_ + left_border_ + margin_};
  for (auto&& i : widgets()) {
    float w_scale = (*i).scale();
    float wh = (*i).GetHeight() * w_scale;
    b -= border_;
    b -= top_border_;
    b -= wh;
    (*i).set_translate(l, b);
    b -= bottom_border_;
    b -= border_;
  }
  if (height() != total_height) {
    set_height(total_height);
  }
}

}  // namespace ballistica::ui_v1
