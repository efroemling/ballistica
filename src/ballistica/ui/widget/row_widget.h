// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_UI_WIDGET_ROW_WIDGET_H_
#define BALLISTICA_UI_WIDGET_ROW_WIDGET_H_

#include <string>

#include "ballistica/ui/widget/container_widget.h"

namespace ballistica {

// Layout widget for organizing widgets in a row
class RowWidget : public ContainerWidget {
 public:
  RowWidget();
  ~RowWidget() override;
  auto HandleMessage(const WidgetMessage& m) -> bool override;
  auto GetWidgetTypeName() -> std::string override;

 protected:
  void UpdateLayout() override;
};

}  // namespace ballistica

#endif  // BALLISTICA_UI_WIDGET_ROW_WIDGET_H_
