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
  /// ``fail_log_level`` applies if a non-literal message fails to
  /// compile as a resource string; pass a lower one for text we didn't
  /// make and so can't fix (from a host running an older build, say).
  void AddScreenMessage(const std::string& msg, bool literal = false,
                        const Vector3f& color = {1, 1, 1}, bool top = false,
                        TextureAsset* texture = nullptr,
                        TextureAsset* tint_texture = nullptr,
                        const Vector3f& tint = {1, 1, 1},
                        const Vector3f& tint2 = {1, 1, 1},
                        const Vector3f& tint3 = {1, 1, 1},
                        LogLevel fail_log_level = LogLevel::kError);

  /// Add a top screen-message whose icon is a depiction (a
  /// bacommon.depiction json; a player's cloud icon, say). Must be
  /// called from the logic thread.
  void AddTopScreenMessageWithDepiction(const std::string& msg, bool literal,
                                        const Vector3f& color,
                                        const std::string& depiction_json);

  void Draw(FrameDef* frame_def);
  void Reset();

 private:
  class ScreenMessageEntry;
  std::list<ScreenMessageEntry> screen_messages_;
  std::list<ScreenMessageEntry> screen_messages_top_;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_GRAPHICS_SUPPORT_SCREEN_MESSAGES_H_
