// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_UI_SIMPLE_DIALOG_H_
#define BALLISTICA_BASE_UI_SIMPLE_DIALOG_H_

#include <string>

#include "ballistica/base/graphics/mesh/nine_patch_mesh.h"
#include "ballistica/base/graphics/text/text_group.h"
#include "ballistica/base/ui/dev_console.h"

namespace ballistica::base {

class FrameDef;

/// Where on the overlay-front-pass we draw. Just under the dev-console
/// depth (and submitted just before it) so the dev-console -- and the
/// fade/cursor drawn above it -- layer cleanly on top of us, for both
/// transparent and opaque geometry.
const float kSimpleDialogZDepth = kDevConsoleZDepth - 0.01f;

/// A minimal core dialog, drawn end-to-end here using only babase + builtin
/// assets (à la the dev console) rather than a higher-level UI feature-set.
///
/// That keeps it usable in any context -- gui app-modes, server-mode, early
/// boot before any real app-mode is up -- which is exactly when we need it
/// (e.g. asset-package resolve progress + dead-in-the-water errors). It is
/// deliberately dumb: a title, an optional progress bar, a multi-line message
/// area, and an optional single (centered) button. The *meaning* of the button
/// and what it does live entirely with the caller; this class only renders
/// state and reports presses. As soon as a real UI toolkit is up (with its
/// multi-controller ownership model, etc.) callers should prefer that instead.
///
/// Instances are owned by :class:`UI` and addressed by integer id from Python
/// (see ``_babase.simpledialog_*`` + ``babase.SimpleDialog``).
class SimpleDialog {
 public:
  explicit SimpleDialog(int id);

  auto id() const -> int { return id_; }
  auto has_button() const -> bool { return !button_label_.empty(); }

  /// Set the dialog's full visible state. ``progress`` < 0 hides the bar;
  /// an empty ``button_label`` hides the button. Text-meshes are rebuilt only
  /// when their strings actually change.
  void SetState(const std::string& title, const std::string& message,
                float progress, const std::string& button_label);

  /// Drive a self-animating demo (cycles the progress bar from display-time).
  /// For look-iteration only; real dialogs are driven via SetState.
  void set_demo_animate(bool val) { demo_animate_ = val; }

  void Draw(FrameDef* frame_def);

  /// Mouse input. HandleMouseDown returns true if it consumed the press (so
  /// the main UI underneath doesn't also get it). HandleMouseUp returns true
  /// if the button was activated (released in-bounds after a press).
  auto HandleMouseDown(int button, float x, float y) -> bool;
  auto HandleMouseUp(int button, float x, float y) -> bool;
  void HandleMouseCancel(int button, float x, float y);

  /// Device-agnostic OK/confirm activation (keyboard/controller/remote).
  /// Returns true if the dialog had a button to fire (and thus consumed it).
  auto Activate() -> bool;

 private:
  /// A simple rectangular button. Bounds are recomputed each Draw (so they
  /// track the live layout); pressed-state is input-driven.
  struct Button_ {
    float center_x{};
    float center_y{};
    float width{};
    float height{};
    bool pressed{};
    auto Contains(float x, float y) const -> bool {
      return x >= center_x - width * 0.5f && x <= center_x + width * 0.5f
             && y >= center_y - height * 0.5f && y <= center_y + height * 0.5f;
    }
  };

  void DrawButton_(FrameDef* frame_def, const Button_& b, TextGroup* label,
                   bool bounds_mode, bool pressed);
  /// Rebuild a cached rounded-rect mesh if its dimensions changed.
  static void EnsureRoundedMesh_(Object::Ref<NinePatchMesh>* mesh, float* cur_w,
                                 float* cur_h, float w, float h,
                                 float corner_radius);

  int id_{};
  std::string title_;
  std::string message_;
  std::string button_label_;
  float progress_{-1.0f};
  bool demo_animate_{};
  Button_ button_;
  TextGroup title_text_group_;
  TextGroup message_text_group_;
  TextGroup button_text_group_;
  Object::Ref<NinePatchMesh> panel_mesh_;
  Object::Ref<NinePatchMesh> button_mesh_;
  float panel_mesh_w_{-1.0f};
  float panel_mesh_h_{-1.0f};
  float button_mesh_w_{-1.0f};
  float button_mesh_h_{-1.0f};
  /// App-time (ms) until which the button shows its pressed glow after a
  /// key/controller activation (mouse uses the held Button_::pressed state).
  millisecs_t button_flash_end_time_{};
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_UI_SIMPLE_DIALOG_H_
