// Released under the MIT License. See LICENSE for details.

#include "ballistica/ui/widget/row_widget.h"

#include <string>

#include "ballistica/ui/ui.h"

namespace ballistica {

RowWidget::RowWidget() {
  set_background(false);  // Influences default event handling.
  set_draggable(false);
  set_claims_left_right(false);
  set_claims_tab(false);
  set_selection_loops_to_parent(true);
  set_selection_loops(false);
}

RowWidget::~RowWidget() = default;

auto RowWidget::GetWidgetTypeName() -> std::string { return "row"; }

auto RowWidget::HandleMessage(const WidgetMessage& m) -> bool {
  switch (m.type) {
    case WidgetMessage::Type::kShow: {
      return false;
    }
    default:
      return ContainerWidget::HandleMessage(m);
  }
}

void RowWidget::UpdateLayout() {
  BA_DEBUG_UI_READ_LOCK;
  float border = 2;
  float b = border;
  float l = 0;
  for (const auto& i : widgets()) {
    float ww = (*i).GetWidth();
    l += border;
    (*i).set_translate(l, b);
    l += ww + border;
  }
  set_width(l);
}

}  // namespace ballistica
