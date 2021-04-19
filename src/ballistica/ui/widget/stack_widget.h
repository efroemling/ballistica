// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_UI_WIDGET_STACK_WIDGET_H_
#define BALLISTICA_UI_WIDGET_STACK_WIDGET_H_

#include <string>

#include "ballistica/ui/widget/container_widget.h"

namespace ballistica {

// Organizational widget for stacking sub-widgets.
class StackWidget : public ContainerWidget {
 public:
  StackWidget();
  ~StackWidget() override;
  auto GetWidgetTypeName() -> std::string override { return "stack"; }
  void SetWidth(float w) override {
    set_width(w);
    _sizeDirty = true;
    MarkForUpdate();
  }
  void SetHeight(float h) override {
    set_height(h);
    _sizeDirty = true;
    MarkForUpdate();
  }
  // stack widget doesn't have a clearly visible position so don't wanna allow
  // selecting it via keys
  auto IsSelectableViaKeys() -> bool override { return false; }

 protected:
  // move/resize the contained widgets
  void UpdateLayout() override;

 private:
  bool _sizeDirty = false;
};

}  // namespace ballistica

#endif  // BALLISTICA_UI_WIDGET_STACK_WIDGET_H_
