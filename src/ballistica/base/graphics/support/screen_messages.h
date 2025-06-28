// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_GRAPHICS_SUPPORT_SCREEN_MESSAGES_H_
#define BALLISTICA_BASE_GRAPHICS_SUPPORT_SCREEN_MESSAGES_H_

#include <list>
#include <string>

#include "ballistica/base/base.h"
#include "ballistica/shared/math/vector3f.h"

namespace ballistica::base {

/// Wrangles a set of screen-messages.
class ScreenMessages {
 public:
  ScreenMessages();

  void ClearScreenMessageTranslations();

  /// Add a screen-message. Must be called from the logic thread.
  void AddScreenMessage(const std::string& msg,
                        const Vector3f& color = {1, 1, 1}, bool top = false,
                        TextureAsset* texture = nullptr,
                        TextureAsset* tint_texture = nullptr,
                        const Vector3f& tint = {1, 1, 1},
                        const Vector3f& tint2 = {1, 1, 1});

  void DrawMiscOverlays(FrameDef* frame_def);
  void Reset();

 private:
  class ScreenMessageEntry;
  std::list<ScreenMessageEntry> screen_messages_;
  std::list<ScreenMessageEntry> screen_messages_top_;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_GRAPHICS_SUPPORT_SCREEN_MESSAGES_H_
