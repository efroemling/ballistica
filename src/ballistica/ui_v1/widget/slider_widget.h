// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_UI_V1_WIDGET_SLIDER_WIDGET_H_
#define BALLISTICA_UI_V1_WIDGET_SLIDER_WIDGET_H_

#include <string>

#include "ballistica/base/graphics/mesh/nine_patch_mesh.h"
#include "ballistica/ui_v1/widget/button_widget.h"

namespace ballistica::ui_v1 {

/// A draggable-nub slider over a min/max/increment range.
///
/// Covers the same ground as the +/- pair in bauiv1lib.config's
/// ConfigNumberEdit. Value semantics: SetValue() takes a value exactly as
/// given (clamped, but never snapped) so a caller restoring a stored
/// value gets it back verbatim; every *interaction* -- dragging or
/// stepping -- lands on the increment grid, or on min/max.
class SliderWidget : public Widget {
 public:
  SliderWidget();
  ~SliderWidget() override;

  void Draw(base::RenderPass* pass, bool transparent) override;
  auto HandleMessage(const base::WidgetMessage& m) -> bool override;

  void set_width(float val) { width_ = val; }
  void set_height(float val) { height_ = val; }

  /// Set the nub's color. Defaults to the same green ButtonWidget uses.
  void set_color(float r, float g, float b) {
    color_r_ = r;
    color_g_ = g;
    color_b_ = b;
  }

  void SetRange(float min_value, float max_value);
  void set_increment(float val) { increment_ = val; }

  /// Set our value. Clamped to our range, but deliberately not snapped to
  /// the increment grid -- a caller restoring a stored value should get
  /// that value back, not a rounded one.
  void SetValue(float val);
  auto value() const -> float { return value_; }

  /// Called with our value repeatedly while the nub is being dragged.
  void SetOnDragCall(PyObject* call_tuple);

  /// Called with our value when a drag is released having changed it, or
  /// when a key/controller press steps it.
  void SetOnChangeCall(PyObject* call_tuple);

  auto GetWidth() -> float override { return width_; }
  auto GetHeight() -> float override { return height_; }

  auto IsSelectable() -> bool override { return true; }
  auto GetWidgetTypeName() -> std::string override { return "slider"; }

 private:
  /// Selected/hover brightness multiplier, matching ButtonWidget's rules.
  auto GetMult_(millisecs_t current_time, bool textured) const -> float;

  /// Diameter of the nub; it is round and spans our short dimension.
  auto NubSize_() const -> float;

  /// Where the nub's center sits at value-minimum. At this x the nub is
  /// concentric with the backing's left end-cap.
  auto NubMinCenterX_() const -> float;

  /// How far the nub's center travels between value-min and value-max.
  auto NubTravel_() const -> float;

  /// Where the nub's center currently sits, from our value.
  auto NubCenterX_() const -> float;

  /// Our value as a 0-1 position along the range.
  auto ValueFraction_() const -> float;

  /// The value at a given increment-grid index, clamped to range.
  auto GridValue_(float index) const -> float;

  /// Our value's position on the increment grid, as a (possibly
  /// fractional) index.
  auto ValueGridIndex_() const -> float;

  /// Round to the nearest point on the increment grid, clamped to range.
  auto SnapValue_(float val) const -> float;

  /// Set our value from a widget-local pointer x, snapping to the grid.
  /// Returns true if the value changed.
  auto SetValueFromPointerX_(float x) -> bool;

  /// Move to the adjacent grid point in `dir` (-1 or 1), or to min/max.
  /// Returns true if the value changed.
  auto Step_(int dir) -> bool;

  void RunCall_(const Object::Ref<base::PythonContextCall>& call) const;

  /// Rebuild our meshes if our size changed. Ninepatch corners must not be
  /// scaled (it would distort them), so rather than scaling one mesh we
  /// rebuild at the exact size whenever that size moves.
  void EnsureMeshes_();

  Object::Ref<base::NinePatchMesh> backing_mesh_;
  Object::Ref<base::NinePatchMesh> groove_mesh_;
  Object::Ref<base::NinePatchMesh> glow_mesh_;
  float mesh_width_{-1.0f};
  float mesh_height_{-1.0f};

  float width_{100.0f};
  float height_{30.0f};

  // Shares ButtonWidget's default color, so a slider sits alongside
  // buttons without looking like it came from somewhere else.
  float color_r_{ButtonWidget::kDefaultColorR};
  float color_g_{ButtonWidget::kDefaultColorG};
  float color_b_{ButtonWidget::kDefaultColorB};

  // Range defaults match ConfigNumberEdit's.
  float min_value_{0.0f};
  float max_value_{100.0f};
  float increment_{1.0f};
  float value_{};

  /// Our value when the current drag began, so a drag can be judged to
  /// have changed anything -- and so a cancelled one can be undone.
  float drag_start_value_{};

  bool hover_{};
  bool pressed_{};
  bool dragging_{};

  // Keep these at the bottom, so they'll be torn down first.
  Object::Ref<base::PythonContextCall> on_drag_call_;
  Object::Ref<base::PythonContextCall> on_change_call_;
};

}  // namespace ballistica::ui_v1

#endif  // BALLISTICA_UI_V1_WIDGET_SLIDER_WIDGET_H_
