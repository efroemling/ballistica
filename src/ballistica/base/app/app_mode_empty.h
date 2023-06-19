// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_APP_APP_MODE_EMPTY_H_
#define BALLISTICA_BASE_APP_APP_MODE_EMPTY_H_

#include <vector>

#include "ballistica/base/app/app_mode.h"
#include "ballistica/shared/foundation/object.h"

namespace ballistica::base {

class AppModeEmpty : public AppMode {
 public:
  AppModeEmpty();

  static auto GetSingleton() -> AppModeEmpty*;
  void Reset();
  void DrawWorld(base::FrameDef* frame_def) override;

 private:
  Object::Ref<TextGroup> hello_text_group_;
  bool hello_mode_{};
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_APP_APP_MODE_EMPTY_H_
