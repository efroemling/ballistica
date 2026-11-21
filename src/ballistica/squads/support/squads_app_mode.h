// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SQUADS_SUPPORT_SQUADS_APP_MODE_H_
#define BALLISTICA_SQUADS_SUPPORT_SQUADS_APP_MODE_H_

#include "ballistica/base/app_mode/app_mode.h"
#include "ballistica/shared/foundation/object.h"
#include "ballistica/squads/squads.h"

namespace ballistica::squads {

/// The app-mode for squads (being built during the 1.9 cycle). Currently
/// a scaffold: it draws a placeholder and runs the remote-app server, but
/// not classic networking (it will make its own per-connection sockets).
class SquadsAppMode : public base::AppMode {
 public:
  static auto GetSingleton() -> SquadsAppMode*;

  void OnActivate() override;
  auto WantsRemoteAppServer() const -> bool override { return true; }
  void DrawWorld(base::FrameDef* frame_def) override;

 private:
  SquadsAppMode();

  Object::Ref<base::TextGroup> text_group_;
};

}  // namespace ballistica::squads

#endif  // BALLISTICA_SQUADS_SUPPORT_SQUADS_APP_MODE_H_
