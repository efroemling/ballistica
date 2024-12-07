// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_APP_MODE_EMPTY_APP_MODE_H_
#define BALLISTICA_BASE_APP_MODE_EMPTY_APP_MODE_H_

#include "ballistica/base/app_mode/app_mode.h"
#include "ballistica/shared/foundation/object.h"

namespace ballistica::base {

/// An app-mode that doesn't do much of anything in particular. It is set as
/// a default when starting the app, but can also be used for 'hello world'
/// type stuff.
class EmptyAppMode : public AppMode {
 public:
  EmptyAppMode();

  static auto GetSingleton() -> EmptyAppMode*;
  void OnActivate() override;
  void DrawWorld(base::FrameDef* frame_def) override;

 private:
  void Reset_();

  Object::Ref<TextGroup> hello_text_group_;
  int reset_count_{};
  bool hello_mode_{};
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_APP_MODE_EMPTY_APP_MODE_H_
