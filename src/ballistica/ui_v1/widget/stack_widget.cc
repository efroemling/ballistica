// Released under the MIT License. See LICENSE for details.

#include "ballistica/ui_v1/widget/stack_widget.h"

namespace ballistica::ui_v1 {

StackWidget::StackWidget() {
  set_modal_children(true);
  set_single_depth(false);
  set_background(false);

  // Enable certain behavior such as auto-focusing new top widgets.
  set_is_window_stack(true);
}

StackWidget::~StackWidget() = default;

void StackWidget::UpdateLayout() {
  BA_DEBUG_UI_READ_LOCK;
  // Stick everything in the middle.
  for (const auto& i : widgets()) {
    float x_offs = (*i).stack_offset_x();
    float y_offs = (*i).stack_offset_y();
    float w = (*i).GetWidth() * (*i).scale();
    float h = (*i).GetHeight() * (*i).scale();
    float l = (width() - w) / 2 + x_offs;
    float b = (height() - h) / 2 + y_offs;
    (*i).set_translate(l, b);
    _sizeDirty = false;
  }
}

}  // namespace ballistica::ui_v1
