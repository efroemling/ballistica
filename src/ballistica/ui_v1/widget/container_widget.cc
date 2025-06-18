// Released under the MIT License. See LICENSE for details.

#include "ballistica/ui_v1/widget/container_widget.h"

#include <algorithm>
#include <string>

#include "ballistica/base/assets/assets.h"
#include "ballistica/base/audio/audio.h"
#include "ballistica/base/graphics/component/empty_component.h"
#include "ballistica/base/graphics/component/simple_component.h"
#include "ballistica/base/logic/logic.h"
#include "ballistica/base/python/support/python_context_call.h"
#include "ballistica/base/ui/ui.h"
#include "ballistica/base/ui/widget_message.h"
#include "ballistica/shared/foundation/event_loop.h"
#include "ballistica/shared/generic/utils.h"
#include "ballistica/shared/math/random.h"
#include "ballistica/shared/python/python.h"
#include "ballistica/ui_v1/python/ui_v1_python.h"
#include "ballistica/ui_v1/widget/button_widget.h"
#include "ballistica/ui_v1/widget/root_widget.h"
#include "ballistica/ui_v1/widget/stack_widget.h"

namespace ballistica::ui_v1 {

// Set this to -100 or so to make sure culling is active
// (things should visibly pop in & out of existence in that case).
#define SIMPLE_CULLING_V_OFFSET 0
#define SIMPLE_CULLING_H_OFFSET 0

#define AUTO_SELECT_SLOPE_CLAMP 4.0f
#define AUTO_SELECT_MIN_SLOPE 0.1f
#define AUTO_SELECT_SLOPE_OFFSET 1.0f
#define AUTO_SELECT_SLOPE_WEIGHT 0.5f

#define TRANSITION_DURATION 120

ContainerWidget::ContainerWidget(float width_in, float height_in)
    : width_(width_in),
      height_(height_in),
      dynamics_update_time_millisecs_(
          static_cast<millisecs_t>(g_base->logic->display_time() * 1000.0)) {}

ContainerWidget::~ContainerWidget() {
  BA_DEBUG_UI_READ_LOCK;
  // Wipe out our children.
  widgets_.clear();
}

void ContainerWidget::SetOnActivateCall(PyObject* c) {
  on_activate_call_ = Object::New<base::PythonContextCall>(c);
}

void ContainerWidget::SetOnOutsideClickCall(PyObject* c) {
  on_outside_click_call_ = Object::New<base::PythonContextCall>(c);
}

void ContainerWidget::DrawChildren(base::RenderPass* pass,
                                   bool draw_transparent, float x_offset,
                                   float y_offset, float scale) {
  BA_DEBUG_UI_READ_LOCK;

  // We're expected to fill z space 0..1 when we draw... so we need to divide
  // that space between our child widgets plus our bg layer.
  float layer_thickness{};
  float layer_spacing{};
  float base_offset{};
  float layer_thickness1{};
  float layer_thickness2{};
  float layer_thickness3{};
  float layer_spacing1{};
  float layer_spacing2{};
  float layer_spacing3{};
  float base_offset1{};
  float base_offset2{};
  float base_offset3{};

  // In single-depth mode we draw all widgets at the same depth so they each get
  // our full depth resolution. however they may overlap incorrectly.
  if (background_) {
    assert(!single_depth_root_);
    if (single_depth_) {
      // Reserve a sliver of 0.2 for our backing geometry.
      layer_thickness = 0.8f;
      base_offset = 0.2f;
      layer_spacing = 0.0f;
    } else {
      layer_thickness = 1.0f / static_cast<float>(widgets_.size() + 1);
      layer_spacing = layer_thickness;
      base_offset = layer_thickness;
    }
  } else {
    if (single_depth_) {
      // Single-depth-root is a special mode for our root container
      // where the first child (the screen stack) gets most of the depth range,
      // the last child (the overlay stack) gets a bit of the rest, and the
      // remainder is shared between root widget children (toolbars, etc).
      if (single_depth_root_) {
        layer_thickness1 = 0.9f;
        base_offset1 = 0.0f;
        layer_spacing1 = 0.0f;
        layer_thickness2 = 0.05f;
        base_offset2 = 0.9f;
        layer_spacing2 = 0.0f;
        layer_thickness3 = 0.05f;
        base_offset3 = 0.95f;
        layer_spacing3 = 0.0f;
      } else {
        layer_thickness = 1.0f;
        base_offset = 0.0f;
        layer_spacing = 0.0f;
      }
    } else {
      layer_thickness = 1.0f / static_cast<float>(widgets_.size());
      layer_spacing = layer_thickness;
      base_offset = 0;
    }
  }

  size_t w_count = widgets_.size();
  bool doing_culling_v = false;
  bool doing_culling_h = false;
  Widget* pw = parent_widget();
  float cull_top = 0.0f;
  float cull_bottom = 0.0f;
  float cull_left = 0.0f;
  float cull_right = 0.0f;
  float cull_offset_v = 0.0f;
  float cull_offset_h = 0.0f;

  // FIXME: need to test/update this to support scaling.
  if (pw && pw->simple_culling_v() >= 0.0f) {
    doing_culling_v = true;
    cull_top = pw->simple_culling_top() - ty();
    cull_bottom = pw->simple_culling_bottom() - ty();
    cull_offset_v = pw->simple_culling_v();
  }
  if (pw && pw->simple_culling_h() >= 0.0f) {
    doing_culling_h = true;
    cull_right = pw->simple_culling_right() - tx();
    cull_left = pw->simple_culling_left() - tx();
    cull_offset_h = pw->simple_culling_h();
  }

  // In opaque mode, draw our child widgets immediately front-to-back to best
  // make use of the z buffer.
  if (draw_transparent) {
    base::EmptyComponent c(pass);
    c.SetTransparent(true);

    for (size_t i = 0; i < w_count; i++) {
      if (single_depth_root_) {
        if (i == 0) {
          layer_thickness = layer_thickness1;
          base_offset = base_offset1;
          layer_spacing = layer_spacing1;
        } else if (i == w_count - 1) {
          layer_thickness = layer_thickness3;
          base_offset = base_offset3;
          layer_spacing = layer_spacing3;
        } else {
          layer_thickness = layer_thickness2;
          base_offset = base_offset2;
          layer_spacing = layer_spacing2;
        }
      }

      Widget& w(*widgets_[i]);

      if (!w.visible_in_container()) {
        continue;
      }

      float tx = w.tx();
      float ty = w.ty();
      float s = w.scale();

      // Some bare-bones culling to keep large scroll areas responsive.
      if (doing_culling_v) {
        if ((y_offset + ty > cull_top + cull_offset_v + SIMPLE_CULLING_V_OFFSET)
            || (y_offset + ty + s * w.GetHeight()
                < cull_bottom - cull_offset_v - SIMPLE_CULLING_V_OFFSET)) {
          continue;
        }
      }
      if (doing_culling_h) {
        if ((x_offset + tx
             > cull_right + cull_offset_h + SIMPLE_CULLING_H_OFFSET)
            || (x_offset + tx + s * w.GetWidth()
                < cull_left - cull_offset_h - SIMPLE_CULLING_H_OFFSET)) {
          continue;
        }
      }
      {
        auto xf = c.ScopedTransform();

        float z_offs = base_offset + static_cast<float>(i) * layer_spacing;
        if (transition_scale_ != 1.0f) {
          c.Translate(bg_center_x_, bg_center_y_, 0);
          c.Scale(transition_scale_, transition_scale_, 1.0f);
          c.Translate(-bg_center_x_, -bg_center_y_, 0);
        }

        // Widgets can opt to use a subset of their allotted depth slice.
        float d_min = w.depth_range_min();
        float d_max = w.depth_range_max();
        float this_z_offs;
        float this_layer_thickness;
        if (d_min != 0.0f || d_max != 1.0f) {
          this_z_offs = z_offs + layer_thickness * d_min;
          this_layer_thickness = layer_thickness * (d_max - d_min);
        } else {
          this_z_offs = z_offs;
          this_layer_thickness = layer_thickness;
        }
        c.Translate(x_offset + tx, y_offset + ty, this_z_offs);
        c.Scale(s, s, this_layer_thickness);
        c.Submit();
        w.Draw(pass, draw_transparent);
      }
      c.Submit();
    }
    c.Submit();

  } else {
    base::EmptyComponent c(&(*pass));
    c.SetTransparent(false);

    for (int i = static_cast<int>(w_count - 1); i >= 0; i--) {
      if (single_depth_root_) {
        if (i == 0) {
          layer_thickness = layer_thickness1;
          base_offset = base_offset1;
          layer_spacing = layer_spacing1;
        } else if (i == w_count - 1) {
          layer_thickness = layer_thickness3;
          base_offset = base_offset3;
          layer_spacing = layer_spacing3;
        } else {
          layer_thickness = layer_thickness2;
          base_offset = base_offset2;
          layer_spacing = layer_spacing2;
        }
      }

      Widget& w(*widgets_[i]);

      if (!w.visible_in_container()) {
        continue;
      }

      float tx = w.tx();
      float ty = w.ty();
      float s = w.scale();

      // Some bare-bones culling to keep large scroll areas responsive.
      if (doing_culling_v) {
        if ((y_offset + ty > cull_top + cull_offset_v + SIMPLE_CULLING_V_OFFSET)
            || (y_offset + ty + s * w.GetHeight()
                < cull_bottom - cull_offset_v - SIMPLE_CULLING_V_OFFSET)) {
          continue;
        }
      }
      if (doing_culling_h) {
        if ((x_offset + tx
             > cull_right + cull_offset_h + SIMPLE_CULLING_H_OFFSET)
            || (x_offset + tx + s * w.GetWidth()
                < cull_left - cull_offset_h - SIMPLE_CULLING_H_OFFSET)) {
          continue;
        }
      }

      {
        auto xf = c.ScopedTransform();
        float z_offs = base_offset + static_cast<float>(i) * layer_spacing;
        if (transition_scale_ != 1.0f) {
          c.Translate(bg_center_x_, bg_center_y_, 0);
          c.Scale(transition_scale_, transition_scale_, 1.0f);
          c.Translate(-bg_center_x_, -bg_center_y_, 0);
        }

        // Widgets can opt to use a subset of their allotted depth slice.
        float d_min = w.depth_range_min();
        float d_max = w.depth_range_max();
        float this_z_offs;
        float this_layer_thickness;
        if (d_min != 0.0f || d_max != 1.0f) {
          this_z_offs = z_offs + layer_thickness * d_min;
          this_layer_thickness = layer_thickness * (d_max - d_min);
        } else {
          this_z_offs = z_offs;
          this_layer_thickness = layer_thickness;
        }
        c.Translate(x_offset + tx, y_offset + ty, this_z_offs);
        c.Scale(s, s, this_layer_thickness);
        c.Submit();
        w.Draw(pass, draw_transparent);
      }
      c.Submit();
    }
    c.Submit();
  }
}

auto ContainerWidget::HandleMessage(const base::WidgetMessage& m) -> bool {
  BA_DEBUG_UI_READ_LOCK;

  bool claimed = false;
  if (ignore_input_) {
    return claimed;
  }

  switch (m.type) {
    case base::WidgetMessage::Type::kTextInput:
    case base::WidgetMessage::Type::kKey:
    case base::WidgetMessage::Type::kPaste:
      if (selected_widget_) {
        bool val = selected_widget_->HandleMessage(m);
        if (val != 0) {
          return true;
        }
      }
      break;

      // Ewww we dont want subclasses to do this
      // but we need to ourself for standalone containers
      // ...reaaaly need to make babase.container() a subclass.
    case base::WidgetMessage::Type::kShow: {
      // Told to show something.. send this along to our parent (we can't do
      // anything).
      Widget* w = parent_widget();
      if (w) {
        w->HandleMessage(m);
      }
      return true;
    }

    case base::WidgetMessage::Type::kStart: {
      if (selected_widget_) {
        if (selected_widget_->HandleMessage(m)) {
          claimed = true;
        }
      }
      if (!claimed && start_button_.exists()) {
        claimed = true;
        start_button_->Activate();
      }
      break;
    }

    case base::WidgetMessage::Type::kCancel: {
      if (selected_widget_) {
        if (selected_widget_->HandleMessage(m)) {
          claimed = true;
        }
      }
      if (!claimed) {
        if (cancel_button_.exists()) {
          claimed = true;
          cancel_button_->Activate();
        } else if (auto* call = on_cancel_call_.get()) {
          claimed = true;

          // Schedule this to run immediately after any current UI
          // traversal.
          call->ScheduleInUIOperation();
        }
      }
      break;
    }

    // case base::WidgetMessage::Type::kTabNext:
    case base::WidgetMessage::Type::kMoveRight:
    case base::WidgetMessage::Type::kMoveDown: {
      if (m.type == base::WidgetMessage::Type::kMoveRight
          && !claims_left_right_) {
        break;
      }
      if (m.type == base::WidgetMessage::Type::kMoveDown && !claims_up_down_) {
        break;
      }
      if (selected_widget_) {
        if (selected_widget_->HandleMessage(m)) {
          claimed = true;
        }
      }
      if (!claimed) {
        if (!root_selectable_) {
          if (m.type == base::WidgetMessage::Type::kMoveDown) {
            SelectDownWidget();
          } else if (m.type == base::WidgetMessage::Type::kMoveRight) {
            SelectRightWidget();
          } else {
            SelectNextWidget();
          }
          if (IsHierarchySelected()) {
            ShowWidget(selected_widget());
          }
          claimed = true;
        }
      }
      break;
    }

    // case base::WidgetMessage::Type::kTabPrev:
    case base::WidgetMessage::Type::kMoveLeft:
    case base::WidgetMessage::Type::kMoveUp: {
      if (m.type == base::WidgetMessage::Type::kMoveLeft
          && !claims_left_right_) {
        break;
      }
      if (m.type == base::WidgetMessage::Type::kMoveUp && !claims_up_down_) {
        break;
      }
      if (selected_widget_) {
        if (selected_widget_->HandleMessage(m)) {
          claimed = true;
        }
      }
      if (!claimed) {
        if (!root_selectable_) {
          if (m.type == base::WidgetMessage::Type::kMoveUp) {
            SelectUpWidget();
          } else if (m.type == base::WidgetMessage::Type::kMoveLeft) {
            SelectLeftWidget();
          } else {
            SelectPrevWidget();
          }
          if (IsHierarchySelected()) {
            ShowWidget(selected_widget());
          }
          claimed = true;
        }
      }
      break;
    }

    case base::WidgetMessage::Type::kActivate: {
      if (root_selectable_) {
        Activate();
        claimed = true;
      } else {
        if (selected_widget_) {
          if (selected_widget_->HandleMessage(m)) {
            claimed = true;
          }
        }
        if (!claimed) {
          if (selected_widget_) {
            selected_widget_->Activate();
          }
          claimed = true;
        }
      }
      break;
    }

    case base::WidgetMessage::Type::kMouseMove: {
      CheckLayout();

      // Ignore mouse stuff while transitioning out.
      if (transitioning_ && transitioning_out_) {
        break;
      }

      float x = m.fval1;
      float y = m.fval2;
      float l = 0.0f;
      float r = width_;
      float b = 0.0f;
      float t = height_;

      // If we're dragging, the drag claims all attention.
      if (dragging_) {
        bg_dirty_ = glow_dirty_ = true;
        set_translate(tx() + (x - drag_x_) * scale(),
                      ty() + (y - drag_y_) * scale());
        break;
      }

      if (!root_selectable_) {
        // Go through all widgets backwards until one claims the cursor position
        // (we still send it to other widgets even then though in case they
        // case).
        for (auto i = widgets_.rbegin(); i != widgets_.rend(); i++) {
          float cx = x;
          float cy = y;
          TransformPointToChild(&cx, &cy, **i);
          if ((**i).HandleMessage(
                  base::WidgetMessage(m.type, nullptr, cx, cy, claimed))) {
            claimed = true;
          }
          if (modal_children_) {
            break;
          }
        }
      }

      // If its not yet claimed, see if its within our contained region, in
      // which case we claim it (only for regular taps).
      if (!claimed) {
        if (background_ || root_selectable_) {
          if (x >= l && x < r && y >= b && y < t) {
            claimed = true;
            mouse_over_ = true;
          } else {
            mouse_over_ = false;
          }
        }
      } else {
        mouse_over_ = false;
      }
      break;
    }

    case base::WidgetMessage::Type::kMouseWheel:
    case base::WidgetMessage::Type::kMouseWheelH:
    case base::WidgetMessage::Type::kMouseWheelVelocity:
    case base::WidgetMessage::Type::kMouseWheelVelocityH: {
      CheckLayout();

      // Ignore mouse stuff while transitioning.
      if (transitioning_ && transitioning_out_) {
        break;
      }

      float x = m.fval1;
      float y = m.fval2;
      float amount = m.fval3;
      float momentum = m.fval4;

      float l = 0;
      float r = width_;
      float b = 0;
      float t = height_;

      // Go through all widgets backwards until one claims the wheel.
      for (auto i = widgets_.rbegin(); i != widgets_.rend(); i++) {
        float cx = x;
        float cy = y;
        TransformPointToChild(&cx, &cy, ((**i)));
        if ((**i).HandleMessage(base::WidgetMessage(m.type, nullptr, cx, cy,
                                                    amount, momentum))) {
          claimed = true;
          break;
        }
        if (modal_children_) break;
      }

      // If its not yet claimed, see if its within our contained region, in
      // which case we claim it but do nothing.
      if (!claimed) {
        if (background_) {
          if (x >= l && x < r && y >= b && y < t) {
            claimed = true;
          }
        }
      }
      break;
    }
    case base::WidgetMessage::Type::kScrollMouseDown:
    case base::WidgetMessage::Type::kMouseDown: {
      CheckLayout();

      // Ignore mouse stuff while transitioning.
      if (transitioning_ && transitioning_out_) {
        break;
      }

      float x = m.fval1;
      float y = m.fval2;
      auto click_count = static_cast<int>(m.fval3);

      float l = 0;
      float r = width_;
      float b = 0;
      float t = height_;

      if (!root_selectable_) {
        // Go through all widgets backwards until one claims the click.
        for (auto i = widgets_.rbegin(); i != widgets_.rend(); i++) {
          float cx = x;
          float cy = y;
          TransformPointToChild(&cx, &cy, **i);
          if ((**i).HandleMessage(base::WidgetMessage(
                  m.type, nullptr, cx, cy, static_cast<float>(click_count)))) {
            claimed = true;
            break;
          }
          if (modal_children_) {
            claimed = true;
            break;
          }
        }
      }

      // If its not yet claimed, see if its within our contained region, in
      // which case we claim it (only for regular mouse-downs).
      if (!claimed && m.type == base::WidgetMessage::Type::kMouseDown) {
        float bottom_overlap = 2;
        float top_overlap = 2;

        if (background_ || root_selectable_) {
          if (x >= l && x < r && y >= b - bottom_overlap
              && y < t + top_overlap) {
            claimed = true;
            mouse_over_ = true;

            if (root_selectable_) {
              GlobalSelect();

              pressed_ = true;

              pressed_activate_ = click_count == 2 || click_activate_;

              // First click just selects.
              if (click_count == 1) {
                g_base->audio->SafePlaySysSound(base::SysSoundID::kTap);
              }
            } else {
              // Special case: If we've got a child text widget that's
              // selected, clicking on our background de-selects it. This is a
              // common way of getting rid of a screen keyboard on ios, etc.
              if (dynamic_cast<TextWidget*>(selected_widget_) != nullptr) {
                SelectWidget(nullptr);
              }

              if (draggable_) {
                dragging_ = true;
                drag_x_ = x;
                drag_y_ = y;
              }
            }
          }
        }

        // Call our outside-click callback if unclaimed.
        if (!claimed && on_outside_click_call_.exists()) {
          // Schedule this to run immediately after any current UI traversal.
          on_outside_click_call_->ScheduleInUIOperation();
        }

        // Always claim if they want.
        if (claims_outside_clicks_) {
          claimed = true;
        }
      }
      break;
    }
    case base::WidgetMessage::Type::kMouseUp:
    case base::WidgetMessage::Type::kMouseCancel: {
      CheckLayout();
      dragging_ = false;
      float x = m.fval1;
      float y = m.fval2;
      claimed = (m.fval3 > 0.0f);
      float l = 0;
      float r = width_;
      float b = 0;
      float t = height_;
      if (!root_selectable_) {
        // Go through all widgets backwards until one claims the click.
        // We then send it to everyone else too; just marking it as claimed.
        // (this helps prevent widgets getting 'stuck' because someone else
        // claimed their mouse-up).
        for (auto i = widgets_.rbegin(); i != widgets_.rend(); i++) {
          float cx = x;
          float cy = y;
          TransformPointToChild(&cx, &cy, ((**i)));
          if ((**i).HandleMessage(
                  base::WidgetMessage(m.type, nullptr, cx, cy, claimed))) {
            claimed = true;
          }
          if (modal_children_) {
            break;
          }
        }
      }
      float bottom_overlap = 2;
      float top_overlap = 2;

      // When pressed, we *always* claim mouse-ups/cancels.
      if (pressed_) {
        pressed_ = false;

        // If we're pressed, mouse-ups within our region trigger activation.
        if (pressed_activate_ && !claimed && x >= l && x < r
            && y >= b - bottom_overlap && y < t + top_overlap) {
          if (m.type == base::WidgetMessage::Type::kMouseUp) {
            Activate();
          }
          pressed_activate_ = false;
        }
        return true;
      }
      // If its not yet claimed, see if its within our contained region, in
      // which case we claim it but do nothing.
      if (!claimed) {
        if (background_) {
          if (x >= l && x < r && y >= b - bottom_overlap
              && y < t + top_overlap) {
            claimed = true;
          }
        }
      }
      break;
    }
    default:
      break;
  }
  return claimed;
}

auto ContainerWidget::GetMult(millisecs_t current_time, bool for_glow) const
    -> float {
  if (root_selectable_ && selected()) {
    float m;

    // Only pulsate if regular widget highlighting is on and we're selected.
    if (g_base->ui->ShouldHighlightWidgets()) {
      if (IsHierarchySelected()) {
        m = 0.5f
            + std::abs(sinf(static_cast<float>(current_time) * 0.006467f)
                       * 0.4f);
      } else {
        m = 0.7f;
      }
    } else {
      m = 0.7f;
    }

    // Extra brightness for draw dependents.
    float m2 = 1.0f;

    // Current or recent presses jack things up.
    if ((mouse_over_ && pressed_)
        || (current_time - last_activate_time_millisecs_ < 200)) {
      m *= 1.7f;
      m2 *= 1.1f;
    } else if (g_base->ui->ShouldHighlightWidgets()) {
      // Otherwise if we're supposed to always highlight all widgets, pulsate
      // when directly selected and glow softly when indirectly.
      if (IsHierarchySelected()) {
        // Pulsate.
        m = 0.5f
            + std::abs(sinf(static_cast<float>(current_time) * 0.006467f)
                       * 0.4f);
      } else {
        // Not directly selected; highlight only if we're always supposed to.
        if (always_highlight_) {
          m = 0.7f;
        } else {
          if (for_glow)
            m = 0.0f;
          else
            m = 0.7f;
        }
      }
    } else if (always_highlight_) {
      // Otherwise if we're specifically set to always highlight, do so.
      m *= 1.3f;
      m2 *= 1.0f;
    } else {
      // Otherwise no glow.
      // For glow we return 0 in this case. For other purposes 1.
      if (for_glow) {
        m = 0.0f;
      } else {
        m = 0.7f;
      }
    }
    return (1.0f / 0.7f) * m * m2;  // Anyone linked to us uses this.
  } else {
    return 1.0f;
  }
}

auto ContainerWidget::GetDrawBrightness(millisecs_t current_time) const
    -> float {
  return GetMult(current_time);
}

void ContainerWidget::SetOnCancelCall(PyObject* call_tuple) {
  on_cancel_call_ = Object::New<base::PythonContextCall>(call_tuple);
}

void ContainerWidget::SetRootSelectable(bool enable) {
  root_selectable_ = enable;

  // If *we* are selectable, can't have selected children.
  if (root_selectable_) {
    SelectWidget(nullptr);
  }
}

void ContainerWidget::Draw(base::RenderPass* pass, bool draw_transparent) {
  BA_DEBUG_UI_READ_LOCK;

  CheckLayout();
  millisecs_t net_time = pass->frame_def()->display_time_millisecs();
  float offset_h = 0.0f;

  // If we're transitioning, update our offsets in the first (opaque) pass.
  if (transitioning_) {
    bg_dirty_ = true;

    if (!draw_transparent) {
      if (transition_type_ == TransitionType::kInScale) {
        if (net_time - dynamics_update_time_millisecs_ > 1000)
          dynamics_update_time_millisecs_ = net_time - 1000;
        while (net_time - dynamics_update_time_millisecs_ > 5) {
          dynamics_update_time_millisecs_ += 5;
          d_transition_scale_ +=
              std::min(0.2f, (1.0f - transition_scale_)) * 0.04f;
          d_transition_scale_ *= 0.87f;
          transition_scale_ += d_transition_scale_;
          if (std::abs(transition_scale_ - 1.0f) < 0.001
              && std::abs(d_transition_scale_) < 0.0001f) {
            transition_scale_ = 1.0f;
            transitioning_ = false;
          }
        }
      } else if (transition_type_ == TransitionType::kOutScale) {
        if (net_time - dynamics_update_time_millisecs_ > 1000)
          dynamics_update_time_millisecs_ = net_time - 1000;
        while (net_time - dynamics_update_time_millisecs_ > 5) {
          dynamics_update_time_millisecs_ += 5;
          transition_scale_ -= 0.04f;
          if (transition_scale_ <= 0.0f) {
            transition_scale_ = 0.0f;

            // Probably not safe to delete ourself here since we're in
            // the draw loop, but we can push a call to do it.
            Object::WeakRef<Widget> weakref(this);
            g_base->logic->event_loop()->PushCall([weakref] {
              Widget* w = weakref.get();
              if (w) {
                g_ui_v1->DeleteWidget(w);
              }
            });
            return;
          }
        }
      } else {
        // Step our dynamics up to the present.
        if (net_time - dynamics_update_time_millisecs_ > 1000)
          dynamics_update_time_millisecs_ = net_time - 1000;
        while (net_time - dynamics_update_time_millisecs_ > 5) {
          dynamics_update_time_millisecs_ += 5;

          if (transitioning_) {
            millisecs_t t = dynamics_update_time_millisecs_;
            if (t - transition_start_time_ < TRANSITION_DURATION) {
              float amt = static_cast<float>(t - transition_start_time_)
                          / TRANSITION_DURATION;
              if (transitioning_out_) {
                amt = pow(amt, 1.1f);
              } else {
                amt = 1.0f - pow(1.0f - amt, 1.1f);
              }
              transition_offset_x_ = transition_start_offset_ * (1.0f - amt)
                                     + transition_target_offset_ * amt;
              offset_h += transition_offset_x_;
            } else {
              // Transition is done when we come to a stop.
              if (transitioning_out_) {
                transition_offset_x_ = transition_target_offset_;
              } else {
                transition_offset_x_ = 0.0f;
              }

              // If going out, we're done as soon.
              bool done;
              if (transitioning_out_) {
                done = (std::abs(transition_offset_x_smoothed_
                                 - transition_offset_x_)
                        < 1000.0f);
              } else {
                done = ((std::abs(transition_offset_x_vel_) < 0.05f)
                        && (std::abs(transition_offset_y_vel_) < 0.05f)
                        && (std::abs(transition_offset_x_smoothed_) < 0.05f)
                        && (std::abs(transition_offset_y_smoothed_) < 0.05f));
              }
              if (done) {
                transitioning_ = false;
                transition_offset_x_smoothed_ = 0.0f;
                transition_offset_y_smoothed_ = 0.0f;
                if (transitioning_out_) {
                  // Probably not safe to delete ourself here since we're in the
                  // draw loop, but we can set up an event to do it.
                  Object::WeakRef<Widget> weakref(this);
                  g_base->logic->event_loop()->PushCall([weakref] {
                    Widget* w = weakref.get();
                    if (w) {
                      g_ui_v1->DeleteWidget(w);
                    }
                  });
                  return;
                }
              }
            }

            // Update our springy smoothed values.
            float diff = transition_offset_x_ - transition_offset_x_smoothed_;
            if (transitioning_out_) {
              transition_offset_x_vel_ += diff * 0.03f;
              transition_offset_x_vel_ *= 0.5f;
            } else {
              transition_offset_x_vel_ += diff * 0.04f;
              transition_offset_x_vel_ *= 0.805f;
            }
            transition_offset_x_smoothed_ += transition_offset_x_vel_;
            diff = transition_offset_y_ - transition_offset_y_smoothed_;
            transition_offset_y_vel_ += diff * 0.04f;
            transition_offset_y_vel_ *= 0.98f;
            transition_offset_y_smoothed_ += transition_offset_y_vel_;
          }
        }
      }

      // If we're scaling in or out, update our transition offset
      // (so we can zoom from a point somewhere else on screen).
      if (transition_type_ == TransitionType::kInScale
          || transition_type_ == TransitionType::kOutScale) {
        // Add a fudge factor since our scale point isn't exactly in our center.
        // :-(
        float xdiff = scale_origin_stack_offset_x_ - stack_offset_x()
                      + GetWidth() * -0.05f;
        float ydiff = scale_origin_stack_offset_y_ - stack_offset_y();
        transition_scale_offset_x_ =
            ((1.0f - transition_scale_) * xdiff) / scale();
        transition_scale_offset_y_ =
            ((1.0f - transition_scale_) * ydiff) / scale();
      }
    }
  }

  // Don't draw if we've fully transitioned out.
  if (transitioning_out_ && !transitioning_) {
    return;
  }

  float l = transition_offset_x_smoothed_ + transition_scale_offset_x_;
  float r = l + width_;
  float b = transition_offset_y_smoothed_ + transition_scale_offset_y_;
  float t = b + height_;

  float w = width_;
  float h = height_;

  // Update bg vals if need be
  // (we may need these even if bg is turned off so always calc them).
  if (bg_dirty_) {
    base::SysTextureID tex_id;
    float l_border, r_border, b_border, t_border;
    float width = r - l;
    float height = t - b;
    if (height > width * 0.6f) {
      tex_id = base::SysTextureID::kWindowHSmallVMed;
      bg_mesh_transparent_i_d_ = base::SysMeshID::kWindowHSmallVMedTransparent;
      bg_mesh_opaque_i_d_ = base::SysMeshID::kWindowHSmallVMedOpaque;
      l_border = width * 0.07f;
      r_border = width * 0.19f;
      b_border = height * 0.1f;
      t_border = height * 0.07f;
    } else {
      tex_id = base::SysTextureID::kWindowHSmallVSmall;
      bg_mesh_transparent_i_d_ =
          base::SysMeshID::kWindowHSmallVSmallTransparent;
      bg_mesh_opaque_i_d_ = base::SysMeshID::kWindowHSmallVSmallOpaque;
      l_border = width * 0.12f;
      r_border = width * 0.19f;
      b_border = height * 0.45f;
      t_border = height * 0.23f;
    }
    bg_width_ = r - l + l_border + r_border;
    bg_height_ = t - b + b_border + t_border;
    bg_center_x_ = l - l_border + bg_width_ * 0.5f;
    bg_center_y_ = b - b_border + bg_height_ * 0.5f;
    if (background_) {
      tex_ = g_base->assets->SysTexture(tex_id);
    }
    bg_dirty_ = false;
  }

  // In opaque mode, draw our child widgets immediately front-to-back to best
  // make use of the z buffer.
  if (!draw_transparent) {
    DrawChildren(pass, draw_transparent, l, b, transition_scale_);
  }

  // Draw our window backing if we have one.
  if ((w > 0) && (h > 0)) {
    if (background_) {
      base::SimpleComponent c(pass);
      c.SetTransparent(draw_transparent);
      float s = 1.0f;
      if (transition_scale_ <= 0.9f && !transitioning_out_) {
        float amt = transition_scale_ / 0.9f;
        s = std::min((1.0f - amt) * 4.0f, 2.5f) + amt * 1.0f;
      }
      c.SetColor(red_ * s, green_ * s, blue_ * s, alpha_);
      c.SetTexture(tex_.get());
      {
        auto xf = c.ScopedTransform();
        c.Translate(bg_center_x_, bg_center_y_);
        c.Scale(bg_width_ * transition_scale_, bg_height_ * transition_scale_);
        c.DrawMeshAsset(g_base->assets->SysMesh(
            draw_transparent ? bg_mesh_transparent_i_d_ : bg_mesh_opaque_i_d_));
      }
      c.Submit();
    }
  }

  // Draw our widgets here back-to-front in transparent mode.
  if (draw_transparent) {
    DrawChildren(pass, draw_transparent, l, b, transition_scale_);
  }

  // Draw overlay glow.
  if (root_selectable_ && selected()) {
    float m = GetMult(net_time, true);
    if (draw_transparent) {
      if (glow_dirty_) {
        float l_border, r_border, b_border, t_border;
        l_border = 18;
        r_border = 10;
        b_border = 18;
        t_border = 18;
        glow_width_ = r - l + l_border + r_border;
        glow_height_ = t - b + b_border + t_border;
        glow_center_x_ = l - l_border + glow_width_ * 0.5f;
        glow_center_y_ = b - b_border + glow_height_ * 0.5f;
        glow_dirty_ = false;
      }
      base::SimpleComponent c(pass);
      c.SetTransparent(true);
      c.SetPremultiplied(true);
      c.SetTexture(g_base->assets->SysTexture(base::SysTextureID::kGlow));
      c.SetColor(0.25f * m, 0.25f * m, 0, 0.3f * m);
      {
        auto xf = c.ScopedTransform();
        c.Translate(glow_center_x_, glow_center_y_);
        c.Scale(glow_width_, glow_height_);
        c.DrawMeshAsset(g_base->assets->SysMesh(base::SysMeshID::kImage4x1));
      }
      c.Submit();
    }
  }
}

void ContainerWidget::TransformPointToChild(float* x, float* y,
                                            const Widget& child) const {
  assert(child.parent_widget() == this);
  if (child.scale() == 1.0f) {
    (*x) -= child.tx();
    (*y) -= child.ty();
  } else {
    (*x) -= child.tx();
    (*y) -= child.ty();
    (*x) /= child.scale();
    (*y) /= child.scale();
  }
}

void ContainerWidget::TransformPointFromChild(float* x, float* y,
                                              const Widget& child) const {
  assert(child.parent_widget() == this);
  if (child.scale() == 1.0f) {
    (*x) += child.tx();
    (*y) += child.ty();
  } else {
    (*x) *= child.scale();
    (*y) *= child.scale();
    (*x) += child.tx();
    (*y) += child.ty();
  }
}

void ContainerWidget::Activate() {
  last_activate_time_millisecs_ =
      static_cast<millisecs_t>(g_base->logic->display_time() * 1000.0);
  if (auto* call = on_activate_call_.get()) {
    // Schedule this to run immediately after any current UI traversal.
    call->ScheduleInUIOperation();
  }
}

void ContainerWidget::AddWidget(Widget* w) {
  BA_PRECONDITION(g_base->InLogicThread());
  Object::WeakRef<ContainerWidget> weakthis(this);
  {
    BA_DEBUG_UI_WRITE_LOCK;
    w->set_parent_widget(this);
    widgets_.insert(widgets_.end(), Object::Ref<Widget>(w));
  }

  // If we're not selectable ourself and our child is, select it.
  if (!root_selectable_
      && ((selected_widget_ == nullptr) || is_window_stack_)) {
    if (w->IsSelectable()) {
      // A change on the main or overlay window stack changes the global
      // selection (unless its on the main window stack and there's already
      // something on the overlay stack) in all other cases we just shift our
      // direct selected child (which may not affect the global selection).
      if (is_window_stack_
          && (is_overlay_window_stack_
              || !g_ui_v1->root_widget()
                      ->overlay_window_stack()
                      ->HasChildren())) {
        w->GlobalSelect();

        // Special case for the main window stack; whenever a window is added,
        // update the toolbar state for the topmost living container.
        if (is_main_window_stack_) {
          g_ui_v1->root_widget()->UpdateForFocusedWindow();
        }
      } else {
        SelectWidget(w);
      }
    }
  }

  // Select actions we run above may trigger user code which may kill us.
  if (!weakthis.exists()) {
    return;
  }

  MarkForUpdate();
}

auto ContainerWidget::IsAcceptingInput() const -> bool {
  return (!ignore_input_);
}

// Delete all widgets.
void ContainerWidget::Clear() {
  BA_DEBUG_UI_WRITE_LOCK;
  widgets_.clear();
  selected_widget_ = nullptr;
  prev_selected_widget_ = nullptr;
}

void ContainerWidget::SetCancelButton(ButtonWidget* button) {
  assert(button);

  if (!button->is_color_set()) {
    button->set_color(0.7f, 0.4f, 0.34f);
    button->set_text_color(0.9f, 0.9f, 1.0f, 1.0f);
  }
  cancel_button_ = button;

  // Don't give it a back icon if it has a custom assigned one..
  // FIXME: This should be dynamic.
  if (button->icon() == nullptr) {
    button->set_icon_type(ButtonWidget::IconType::kCancel);
  }
}

void ContainerWidget::SetStartButton(ButtonWidget* button) {
  assert(button);
  if (!button->is_color_set()) {
    button->set_color(0.2f, 0.8f, 0.55f);
  }
  start_button_ = button;

  button->set_icon_type(ButtonWidget::IconType::kStart);
}

static auto _IsTransitionOut(ContainerWidget::TransitionType type) {
  // Note: framing this without a 'default:' so we get compiler warnings
  // when enums are added/removed.
  bool val = false;
  switch (type) {
    case ContainerWidget::TransitionType::kUnset:
    case ContainerWidget::TransitionType::kInLeft:
    case ContainerWidget::TransitionType::kInRight:
    case ContainerWidget::TransitionType::kInScale:
      val = false;
      break;
    case ContainerWidget::TransitionType::kOutLeft:
    case ContainerWidget::TransitionType::kOutRight:
    case ContainerWidget::TransitionType::kOutScale:
      val = true;
      break;
  }
  return val;
}

void ContainerWidget::SetTransition(TransitionType t) {
  BA_DEBUG_UI_READ_LOCK;
  assert(g_base->InLogicThread());

  bg_dirty_ = glow_dirty_ = true;
  ContainerWidget* parent = parent_widget();
  if (parent == nullptr) {
    return;
  }
  parent->CheckLayout();
  auto display_time_millisecs =
      static_cast<millisecs_t>(g_base->logic->display_time() * 1000.0);

  // Warn if setting out-transition twice. This likely means a window is
  // switching to another window twice which can leave the UI broken.
  if (_IsTransitionOut(transition_type_) && _IsTransitionOut(t)) {
    g_ui_v1->python->objs()
        .Get(UIV1Python::ObjID::kDoubleTransitionOutWarningCall)
        .Call();
  }

  transition_type_ = t;

  // Scale transitions are simpler.
  if (t == TransitionType::kInScale) {
    transition_start_time_ = display_time_millisecs;
    dynamics_update_time_millisecs_ = display_time_millisecs;
    transitioning_ = true;
    transitioning_out_ = false;
    transition_scale_ = 0.0f;
    d_transition_scale_ = 0.0f;
  } else if (t == TransitionType::kOutScale) {
    transition_start_time_ = display_time_millisecs;
    dynamics_update_time_millisecs_ = display_time_millisecs;
    transitioning_ = true;
    transitioning_out_ = true;
    ignore_input_ = true;
  } else {
    // Calculate the screen size in our own local space - we'll
    // animate an offset to slide on/off screen.
    float screen_min_x = 0.0f;
    float screen_min_y = 0.0f;
    float screen_max_x = g_base->graphics->screen_virtual_width();
    float screen_max_y = g_base->graphics->screen_virtual_height();
    ScreenPointToWidget(&screen_min_x, &screen_min_y);
    ScreenPointToWidget(&screen_max_x, &screen_max_y);

    // In case we're mid-transition, this avoids hitches.
    float y_offs = 2.0f;
    if (t == TransitionType::kInLeft) {
      transition_start_time_ = display_time_millisecs;
      transition_start_offset_ = screen_min_x - width_ - 100;
      transition_offset_x_smoothed_ = transition_start_offset_;
      transition_offset_y_smoothed_ = (RandomFloat() > 0.5f) ? y_offs : -y_offs;
      transition_target_offset_ = 0;
      transitioning_ = true;
      dynamics_update_time_millisecs_ = display_time_millisecs;
      transitioning_out_ = false;
    } else if (t == TransitionType::kInRight) {
      transition_start_time_ = display_time_millisecs;
      transition_start_offset_ = screen_max_x + 100;
      transition_offset_x_smoothed_ = transition_start_offset_;
      transition_offset_y_smoothed_ = (RandomFloat() > 0.5f) ? y_offs : -y_offs;
      transition_target_offset_ = 0;
      transitioning_ = true;
      dynamics_update_time_millisecs_ = display_time_millisecs;
      transitioning_out_ = false;
    } else if (t == TransitionType::kOutLeft) {
      transition_start_time_ = display_time_millisecs;
      transition_start_offset_ = transition_offset_x_;
      transition_target_offset_ = -2.0f * (screen_max_x - screen_min_x);
      transition_offset_x_smoothed_ = transition_start_offset_;
      transition_offset_y_smoothed_ = 0.0f;
      transitioning_ = true;
      dynamics_update_time_millisecs_ = display_time_millisecs;
      transitioning_out_ = true;
      ignore_input_ = true;
    } else if (t == TransitionType::kOutRight) {
      transition_start_time_ = display_time_millisecs;
      transition_start_offset_ = transition_offset_x_;
      transition_target_offset_ = 2.0f * (screen_max_x - screen_min_x);
      transition_offset_x_smoothed_ = transition_start_offset_;
      transition_offset_y_smoothed_ = 0.0f;
      transitioning_ = true;
      dynamics_update_time_millisecs_ = display_time_millisecs;
      transitioning_out_ = true;
      ignore_input_ = true;
    }
  }

  // If we're transitioning out in some way and our parent is the main window
  // stack, update the toolbar for the new topmost input-accepting window
  // *immediately* (otherwise we'd have to wait for our transition to complete
  // before the toolbar switches).
  if (transitioning_ && transitioning_out_ && parent->is_main_window_stack_) {
    g_ui_v1->root_widget()->UpdateForFocusedWindow();
  }
}

void ContainerWidget::ReselectLastSelectedWidget() {
  if (prev_selected_widget_ != nullptr
      && prev_selected_widget_ != selected_widget_
      && prev_selected_widget_->IsSelectable()) {
    SelectWidget(prev_selected_widget_);
  }
}

// Remove the widget from our list which should kill it.
void ContainerWidget::DeleteWidget(Widget* w) {
  bool found = false;
  {
    BA_DEBUG_UI_WRITE_LOCK;
    // Hmmm couldn't we do this without having to iterate here?
    // (at least in release build).
    for (auto i = widgets_.begin(); i != widgets_.end(); i++) {
      if (&(**i) == w) {
        if (selected_widget_ == w) {
          selected_widget_ = nullptr;
        }
        if (prev_selected_widget_ == w) {
          prev_selected_widget_ = nullptr;
        }
        // Grab a ref until we clear it off the list to avoid funky recursion
        // issues.
        auto w2 = Object::Ref<Widget>(*i);
        widgets_.erase(i);
        found = true;
        break;
      }
    }
  }

  assert(found);

  // Special case: if we're the overlay stack and we've deleted our last
  // widget, try to reselect whatever was last selected before the overlay
  // stack.
  if (is_overlay_window_stack_) {
    if (widgets_.empty()) {
      // Eww this logic should be in some sort of controller.
      g_ui_v1->root_widget()->ReselectLastSelectedWidget();
      return;
    }
  }

  // in some cases we want to auto select a new child widget
  if (selected_widget_ == nullptr || is_window_stack_) {
    BA_DEBUG_UI_READ_LOCK;
    // no UI lock needed here.. we don't change anything until SelectWidget,
    // at which point we exit the loop..
    for (auto i = widgets_.rbegin(); i != widgets_.rend(); i++) {
      if ((**i).IsSelectable()) {
        // A change on the main or overlay window stack changes the global
        // selection (unless its on the main window stack and there's already
        // something on the overlay stack) in all other cases we just shift
        // our direct selected child (which may not affect the global
        // selection).
        if (is_window_stack_
            && (is_overlay_window_stack_
                || !g_ui_v1->root_widget()
                        ->overlay_window_stack()
                        ->HasChildren())) {
          (**i).GlobalSelect();
        } else {
          SelectWidget(&(**i));
        }
        break;
      }
    }
  }

  // Special case: if we're the main window stack,
  // update the active toolbar/etc.
  if (is_main_window_stack_) {
    g_ui_v1->root_widget()->UpdateForFocusedWindow();
  }
}

auto ContainerWidget::GetTopmostToolbarInfluencingWidget() -> Widget* {
  // Look for the first window that is accepting input (filters out windows
  // that are transitioning out) and also set to affect the toolbar state.
  for (auto w = widgets_.rbegin(); w != widgets_.rend(); ++w) {
    if ((**w).IsAcceptingInput()
        && (**w).toolbar_visibility() != ToolbarVisibility::kInherit) {
      return &(**w);
    }
  }
  return nullptr;
}

void ContainerWidget::ShowWidget(Widget* w) {
  if (!w) {
    return;
  }

  // Hacky exception; scroll-widgets don't respond directly to this
  // (it always arrives via a child's child.. need to clean this up)
  // it causes double-shows to happen otherwise and odd jumpy behavior.
  if (GetWidgetTypeName() == "scroll") {
    return;
  }

  CheckLayout();
  float s = scale();
  float buffer_top = w->show_buffer_top();
  float buffer_bottom = w->show_buffer_bottom();
  float buffer_right = w->show_buffer_right();
  float buffer_left = w->show_buffer_left();
  float tx = (w->tx() - buffer_left) * s;
  float ty = (w->ty() - buffer_bottom) * s;
  float width = (w->GetWidth() + buffer_left + buffer_right) * s;
  float height = (w->GetHeight() + buffer_bottom + buffer_top) * s;
  HandleMessage(base::WidgetMessage(base::WidgetMessage::Type::kShow, nullptr,
                                    tx, ty, width, height));
}

void ContainerWidget::SelectWidget(Widget* w, SelectionCause c) {
  BA_DEBUG_UI_READ_LOCK;

  if (w == nullptr) {
    if (selected_widget_) {
      prev_selected_widget_ = selected_widget_;
      selected_widget_->SetSelected(false, SelectionCause::kNone);
      selected_widget_ = nullptr;
    }
  } else {
    if (root_selectable_) {
      g_core->logging->Log(
          LogName::kBa, LogLevel::kError,
          "SelectWidget() called on a ContainerWidget which is itself "
          "selectable. Ignoring.");
      return;
    }
    for (auto& widget : widgets_) {
      if (widget.get() == w) {
        Widget* prev_selected_widget = selected_widget_;

        // Deactivate old selected widget.
        if (selected_widget_) {
          selected_widget_->SetSelected(false, SelectionCause::kNone);
          selected_widget_ = nullptr;
        }
        if (widget->IsSelectable()) {
          widget->SetSelected(true, c);
          selected_widget_ = &(*widget);

          // Store the old one as prev-selected if its not the one we're
          // selecting now. (otherwise re-selecting repeatedly kills our prev
          // mechanism).
          if (prev_selected_widget != selected_widget_) {
            prev_selected_widget_ = prev_selected_widget;
          }
        } else {
          static bool printed = false;
          if (!printed) {
            g_core->logging->Log(LogName::kBa, LogLevel::kWarning,
                                 "SelectWidget called on unselectable widget: "
                                     + w->GetWidgetTypeName());
            Python::PrintStackTrace();
            printed = true;
          }
        }
        break;
      }
    }
  }
}

void ContainerWidget::SetSelected(bool s, SelectionCause cause) {
  BA_DEBUG_UI_READ_LOCK;

  Widget::SetSelected(s, cause);

  // If we've got selection-looping-to-parent enabled, being selected via
  // next/prev snaps our sub-selection to our first or last widget.
  if (s) {
    if (selection_loops_to_parent()) {
      if (cause == SelectionCause::kNextSelected) {
        for (auto& widget : widgets_) {
          if ((*widget).IsSelectable()) {
            ShowWidget(&(*widget));
            SelectWidget(&(*widget), cause);
            break;
          }
        }
      } else if (cause == SelectionCause::kPrevSelected) {
        for (auto i = widgets_.rbegin(); i != widgets_.rend(); i++) {
          if ((**i).IsSelectable()) {
            ShowWidget(&(**i));
            SelectWidget(&(**i), cause);
            break;
          }
        }
      }
    }
  } else {
    // if we're being deselected and we have a selected child, tell them
    // they're deselected if (selected_widget_) {
    // }
  }
}

auto ContainerWidget::GetClosestLeftWidget(float our_x, float our_y,
                                           Widget* ignore_widget) -> Widget* {
  Widget* w = nullptr;
  float x, y;
  float closest_val = 9999.0f;
  for (auto i = widgets_.begin(); i != widgets_.end(); i++) {
    assert(i->exists());
    (**i).GetCenter(&x, &y);
    float slope = std::abs(x - our_x) / (std::max(0.001f, std::abs(y - our_y)));
    slope = std::min(
        slope, AUTO_SELECT_SLOPE_CLAMP);  // Beyond this, just go by distance.
    float slope_weighted = AUTO_SELECT_SLOPE_WEIGHT * slope
                           + (1.0f - AUTO_SELECT_SLOPE_WEIGHT) * 1.0f;
    if (i->get() != ignore_widget && x < our_x && slope > AUTO_SELECT_MIN_SLOPE
        && (**i).IsSelectable() && (**i).IsSelectableViaKeys()) {
      // Take distance diff and multiply by our slope.
      float xdist = x - our_x;
      float ydist = y - our_y;
      float dist = sqrtf(xdist * xdist + ydist * ydist);
      float val =
          dist / std::max(0.001f, slope_weighted + AUTO_SELECT_SLOPE_OFFSET);
      if (val < closest_val || w == nullptr) {
        closest_val = val;
        w = i->get();
      }
    }
  }
  return w;
}

auto ContainerWidget::GetClosestRightWidget(float our_x, float our_y,
                                            Widget* ignore_widget) -> Widget* {
  Widget* w = nullptr;
  float x, y;
  float closest_val = 9999.0f;
  for (auto i = widgets_.begin(); i != widgets_.end(); i++) {
    assert(i->exists());
    (**i).GetCenter(&x, &y);
    float slope = std::abs(x - our_x) / (std::max(0.001f, std::abs(y - our_y)));
    slope = std::min(
        slope, AUTO_SELECT_SLOPE_CLAMP);  // beyond this, just go by distance
    float slopeWeighted = AUTO_SELECT_SLOPE_WEIGHT * slope
                          + (1.0f - AUTO_SELECT_SLOPE_WEIGHT) * 1.0f;
    if (i->get() != ignore_widget && x > our_x && slope > AUTO_SELECT_MIN_SLOPE
        && (**i).IsSelectable() && (**i).IsSelectableViaKeys()) {
      // Take distance diff and multiply by our slope.
      float xDist = x - our_x;
      float yDist = y - our_y;
      float dist = sqrtf(xDist * xDist + yDist * yDist);
      float val =
          dist / std::max(0.001f, slopeWeighted + AUTO_SELECT_SLOPE_OFFSET);
      if (val < closest_val || w == nullptr) {
        closest_val = val;
        w = i->get();
      }
    }
  }
  return w;
}

auto ContainerWidget::GetClosestUpWidget(float our_x, float our_y,
                                         Widget* ignoreWidget) -> Widget* {
  Widget* w = nullptr;
  float x, y;
  float closest_val = 9999.0f;
  for (auto i = widgets_.begin(); i != widgets_.end(); i++) {
    assert(i->exists());
    (**i).GetCenter(&x, &y);
    float slope = std::abs(y - our_y) / (std::max(0.001f, std::abs(x - our_x)));
    slope = std::min(
        slope, AUTO_SELECT_SLOPE_CLAMP);  // Beyond this, just go by distance.
    float slopeWeighted = AUTO_SELECT_SLOPE_WEIGHT * slope
                          + (1.0f - AUTO_SELECT_SLOPE_WEIGHT) * 1.0f;
    if (i->get() != ignoreWidget && y > our_y && slope > AUTO_SELECT_MIN_SLOPE
        && (**i).IsSelectable() && (**i).IsSelectableViaKeys()) {
      // Take distance diff and multiply by our slope.
      float xDist = x - our_x;
      float yDist = y - our_y;
      float dist = sqrtf(xDist * xDist + yDist * yDist);
      float val =
          dist / std::max(0.001f, slopeWeighted + AUTO_SELECT_SLOPE_OFFSET);
      if (val < closest_val || w == nullptr) {
        closest_val = val;
        w = i->get();
      }
    }
  }
  return w;
}

auto ContainerWidget::GetClosestDownWidget(float our_x, float our_y,
                                           Widget* ignoreWidget) -> Widget* {
  Widget* w = nullptr;
  float x, y;
  float closest_val = 9999.0f;
  for (auto i = widgets_.begin(); i != widgets_.end(); i++) {
    assert(i->exists());
    (**i).GetCenter(&x, &y);
    float slope = std::abs(y - our_y) / (std::max(0.001f, std::abs(x - our_x)));
    slope = std::min(
        slope, AUTO_SELECT_SLOPE_CLAMP);  // Beyond this, just go by distance.
    float slopeWeighted = AUTO_SELECT_SLOPE_WEIGHT * slope
                          + (1.0f - AUTO_SELECT_SLOPE_WEIGHT) * 1.0f;
    if (i->get() != ignoreWidget && y < our_y && slope > AUTO_SELECT_MIN_SLOPE
        && (**i).IsSelectable() && (**i).IsSelectableViaKeys()) {
      // Take distance diff and multiply by our slope.
      float xDist = x - our_x;
      float yDist = y - our_y;
      float dist = sqrtf(xDist * xDist + yDist * yDist);
      float val =
          dist / std::max(0.001f, slopeWeighted + AUTO_SELECT_SLOPE_OFFSET);
      if (val < closest_val || w == nullptr) {
        closest_val = val;
        w = i->get();
      }
    }
  }
  return w;
}

void ContainerWidget::SelectDownWidget() {
  BA_DEBUG_UI_READ_LOCK;

  if (!g_ui_v1 || !g_ui_v1->root_widget() || !g_ui_v1->screen_root_widget()) {
    BA_LOG_ONCE(LogName::kBa, LogLevel::kError,
                "SelectDownWidget called before UI init.");
    return;
  }

  // If the current widget has an explicit down-widget set, go to it.
  if (selected_widget_) {
    Widget* w = selected_widget_->down_widget();

    // If its auto-select, find our closest child widget.
    if (!w && selected_widget_->auto_select()) {
      float our_x, our_y;
      selected_widget_->GetCenter(&our_x, &our_y);
      w = GetClosestDownWidget(our_x, our_y, selected_widget_);
      if (!w) {
        // If we found no viable children and we're under the main window
        // stack, see if we should pass focus to a toolbar widget.
        if (IsInMainStack()) {
          float x = our_x;
          float y = our_y;
          WidgetPointToScreen(&x, &y);
          g_ui_v1->root_widget()->ScreenPointToWidget(&x, &y);
          w = g_ui_v1->root_widget()->GetClosestDownWidget(
              x, y, g_ui_v1->screen_root_widget());
        }
        // When we find no viable targets for an autoselect widget we do
        // nothing.
        if (!w) {
          return;
        }
      }
    }
    if (w) {
      if (!w->IsSelectable()) {
        g_core->logging->Log(LogName::kBa, LogLevel::kError,
                             "Down_widget is not selectable.");
      } else {
        w->Show();
        // Avoid tap sounds and whatnot if we're just re-selecting ourself.
        if (w != selected_widget_) {
          w->GlobalSelect();
          g_base->audio->SafePlaySysSound(base::SysSoundID::kTap);
        }
      }
    } else {
      // Have a selected widget but no specific 'down' widget; revert to just
      // doing 'next'.
      SelectNextWidget();
    }
  } else {
    // If nothing is selected, either do a select-next if we have
    // something selectable or call our parent's select-down otherwise.
    if (HasKeySelectableChild()) {
      SelectNextWidget();
    } else {
      if (ContainerWidget* parent = parent_widget()) {
        parent->SelectDownWidget();
      }
    }
  }
}

void ContainerWidget::SelectUpWidget() {
  BA_DEBUG_UI_READ_LOCK;

  if (!g_ui_v1 || !g_ui_v1->root_widget() || !g_ui_v1->screen_root_widget()) {
    BA_LOG_ONCE(LogName::kBa, LogLevel::kError,
                "SelectUpWidget called before UI init.");
    return;
  }

  // If the current widget has an explicit up-widget set, go to it.
  if (selected_widget_) {
    Widget* w = selected_widget_->up_widget();

    // If its auto-select, find the closest widget.
    if (!w && selected_widget_->auto_select()) {
      float our_x, our_y;
      selected_widget_->GetCenter(&our_x, &our_y);
      w = GetClosestUpWidget(our_x, our_y, selected_widget_);
      if (!w) {
        // If we found no viable children and we're on the main window stack,
        // see if we should pass focus to a toolbar widget.
        if (IsInMainStack()) {
          float x = our_x;
          float y = our_y;
          WidgetPointToScreen(&x, &y);
          g_ui_v1->root_widget()->ScreenPointToWidget(&x, &y);
          w = g_ui_v1->root_widget()->GetClosestUpWidget(
              x, y, g_ui_v1->screen_root_widget());
        }
        // When we find no viable targets for an autoselect widget we do
        // nothing.
        if (!w) {
          return;
        }
      }
    }
    if (w) {
      if (!w->IsSelectable()) {
        g_core->logging->Log(LogName::kBa, LogLevel::kError,
                             "up_widget is not selectable.");
      } else {
        w->Show();
        // Avoid tap sounds and whatnot if we're just re-selecting ourself.
        if (w != selected_widget_) {
          w->GlobalSelect();
          g_base->audio->SafePlaySysSound(base::SysSoundID::kTap);
        }
      }
    } else {
      // Have a selected widget but no specific 'up' widget; revert to just
      // doing prev.
      SelectPrevWidget();
    }
  } else {
    // If nothing is selected, either do a select-prev if we have
    // something selectable or call our parent's select-up otherwise.
    if (HasKeySelectableChild()) {
      SelectPrevWidget();
    } else {
      if (ContainerWidget* parent = parent_widget()) {
        parent->SelectUpWidget();
      }
    }
  }
}

void ContainerWidget::SelectLeftWidget() {
  BA_DEBUG_UI_READ_LOCK;

  if (!g_ui_v1 || !g_ui_v1->root_widget() || !g_ui_v1->screen_root_widget()) {
    BA_LOG_ONCE(LogName::kBa, LogLevel::kError,
                "SelectLeftWidget called before UI init.");
    return;
  }

  // If the current widget has an explicit left-widget set, go to it.
  if (selected_widget_) {
    Widget* w = selected_widget_->left_widget();

    // If its auto-select, find the closest widget.
    if (!w && selected_widget_->auto_select()) {
      float our_x, our_y;
      selected_widget_->GetCenter(&our_x, &our_y);
      w = GetClosestLeftWidget(our_x, our_y, selected_widget_);
      // When we find no viable targets for an autoselect widget we do
      // nothing.
      if (!w) {
        return;
      }
    }
    if (w) {
      if (!w->IsSelectable()) {
        g_core->logging->Log(LogName::kBa, LogLevel::kError,
                             "left_widget is not selectable.");
      } else {
        w->Show();
        // Avoid tap sounds and whatnot if we're just re-selecting ourself.
        if (w != selected_widget_) {
          w->GlobalSelect();
          g_base->audio->SafePlaySysSound(base::SysSoundID::kTap);
        }
      }
    } else {
      // Have a selected widget but no specific 'left' widget; revert to just
      // doing prev.
      SelectPrevWidget();
    }
  } else {
    // If nothing is selected, either do a select-prev if we have
    // something selectable or call our parent's select-left otherwise.
    if (HasKeySelectableChild()) {
      SelectPrevWidget();
    } else {
      if (ContainerWidget* parent = parent_widget()) {
        parent->SelectLeftWidget();
      }
    }
  }
}
void ContainerWidget::SelectRightWidget() {
  BA_DEBUG_UI_READ_LOCK;

  if (!g_base->ui || !g_ui_v1->root_widget()
      || !g_ui_v1->screen_root_widget()) {
    BA_LOG_ONCE(LogName::kBa, LogLevel::kError,
                "SelectRightWidget called before UI init.");
    return;
  }

  // If the current widget has an explicit right-widget set, go to it.
  if (selected_widget_) {
    Widget* w = selected_widget_->right_widget();

    // If its auto-select, find the closest widget.
    if (!w && selected_widget_->auto_select()) {
      float our_x, our_y;
      selected_widget_->GetCenter(&our_x, &our_y);
      w = GetClosestRightWidget(our_x, our_y, selected_widget_);

      // For autoselect widgets, if we find no viable targets, we do nothing.
      if (!w) {
        return;
      }
    }
    if (w) {
      if (!w->IsSelectable()) {
        g_core->logging->Log(LogName::kBa, LogLevel::kError,
                             "right_widget is not selectable.");
      } else {
        w->Show();
        // Avoid tap sounds and whatnot if we're just re-selecting ourself.
        if (w != selected_widget_) {
          w->GlobalSelect();
          g_base->audio->SafePlaySysSound(base::SysSoundID::kTap);
        }
      }
    } else {
      // Have a selected widget but no specific 'right' widget; revert to just
      // doing next.
      SelectNextWidget();
    }
  } else {
    // If nothing is selected, either do a select-next if we have
    // something selectable or call our parent's select-right otherwise.
    if (HasKeySelectableChild()) {
      SelectNextWidget();
    } else {
      if (ContainerWidget* parent = parent_widget()) {
        parent->SelectRightWidget();
      }
    }
  }
}

void ContainerWidget::SelectNextWidget() {
  BA_DEBUG_UI_READ_LOCK;

  if (!g_base->ui || !g_ui_v1->root_widget()
      || !g_ui_v1->screen_root_widget()) {
    BA_LOG_ONCE(LogName::kBa, LogLevel::kError,
                "SelectNextWidget called before UI init.");
    return;
  }

  millisecs_t old_last_prev_next_time = last_prev_next_time_millisecs_;
  if (should_print_list_exit_instructions_) {
    last_prev_next_time_millisecs_ =
        static_cast<millisecs_t>(g_base->logic->display_time() * 1000.0);
  }

  // Grab the iterator for our selected widget if possible.
  auto i = widgets_.begin();
  if (selected_widget_) {
    for (; i != widgets_.end(); i++) {
      if ((&(**i) == selected_widget_)) {
        break;
      }
    }
  }

  if (selected_widget_) {
    // If we have a selection we should have been able to find its iterator.
    assert((&(**i) == selected_widget_));
    i++;
  }

  while (true) {
    if (i == widgets_.end()) {
      // Loop around if we allow it; otherwise abort.
      if (selection_loops_to_parent()) {
        ContainerWidget* w = parent_widget();
        if (w) {
          w->SelectNextWidget();
          w->ShowWidget(w->selected_widget());
        }
        return;
      } else if (selected_widget_
                 == nullptr) {  // NOLINT(bugprone-branch-clone)
        // We've got no selection and we've scanned the whole list to no
        // avail, fail.
        PrintExitListInstructions(old_last_prev_next_time);
        return;
      } else if (selection_loops()) {
        i = widgets_.begin();
      } else {
        PrintExitListInstructions(old_last_prev_next_time);
        return;
      }
    }

    // If we had a selection, we abort if we've looped back to it.
    if (&(**i) == selected_widget_) {
      return;
    }
    if ((**i).IsSelectable() && (**i).IsSelectableViaKeys()) {
      SelectWidget(&(**i), SelectionCause::kNextSelected);
      g_base->audio->SafePlaySysSound(base::SysSoundID::kTap);
      return;
    }
    i++;
  }
}

// FIXME: should kill this.
void ContainerWidget::PrintExitListInstructions(
    millisecs_t old_last_prev_next_time) {
  if (should_print_list_exit_instructions_) {
    auto t = static_cast<millisecs_t>(g_base->logic->display_time() * 1000.0);
    if ((t - old_last_prev_next_time > 250)
        && (t - last_list_exit_instructions_print_time_ > 5000)) {
      last_list_exit_instructions_print_time_ = t;
      g_base->audio->SafePlaySysSound(base::SysSoundID::kErrorBeep);
      std::string s = g_base->assets->GetResourceString("arrowsToExitListText");
      {
        // Left arrow.
        Utils::StringReplaceOne(
            &s, "${LEFT}", g_base->assets->CharStr(SpecialChar::kLeftArrow));
      }
      {
        // Right arrow.
        Utils::StringReplaceOne(
            &s, "${RIGHT}", g_base->assets->CharStr(SpecialChar::kRightArrow));
      }
      g_base->ScreenMessage(s);
    }
  }
}

void ContainerWidget::SelectPrevWidget() {
  BA_DEBUG_UI_READ_LOCK;

  millisecs_t old_last_prev_next_time = last_prev_next_time_millisecs_;
  if (should_print_list_exit_instructions_) {
    last_prev_next_time_millisecs_ =
        static_cast<millisecs_t>(g_base->logic->display_time() * 1000.0);
  }

  // Grab the iterator for our selected widget if possible.
  auto i = widgets_.rbegin();
  if (selected_widget_) {
    for (; i != widgets_.rend(); i++) {
      if ((&(**i) == selected_widget_)) {
        break;
      }
    }
  }

  if (selected_widget_) {
    // If we have a selection we should have been able to find its iterator.
    assert(&(**i) == selected_widget_);
    i++;  // Start with next one if we had this selected.
  }

  while (true) {
    if (i == widgets_.rend()) {
      // Loop around if we allow it; otherwise abort.
      if (selection_loops_to_parent()) {
        ContainerWidget* w = parent_widget();
        if (w) {
          w->SelectPrevWidget();
          w->ShowWidget(w->selected_widget());
        }
        return;
      } else if (selected_widget_
                 == nullptr) {  // NOLINT(bugprone-branch-clone)
        // If we've got no selection and we've scanned the whole list to no
        // avail, fail.
        PrintExitListInstructions(old_last_prev_next_time);
        return;
      } else if (selection_loops()) {
        i = widgets_.rbegin();
      } else {
        PrintExitListInstructions(old_last_prev_next_time);
        return;
      }
    }

    // If we had a selection, we abort if we loop back to it.
    if (&(**i) == selected_widget_) {
      return;
    }

    if ((**i).IsSelectable() && (**i).IsSelectableViaKeys()) {
      SelectWidget(&(**i), SelectionCause::kPrevSelected);
      g_base->audio->SafePlaySysSound(base::SysSoundID::kTap);
      return;
    }
    i++;
  }
}

auto ContainerWidget::HasKeySelectableChild() const -> bool {
  for (auto i = widgets_.begin(); i != widgets_.end(); i++) {
    assert(i->exists());
    if ((**i).IsSelectable() && (**i).IsSelectableViaKeys()) {
      return true;
    }
  }
  return false;
}

void ContainerWidget::CheckLayout() {
  if (needs_update_) {
    managed_ = false;
    UpdateLayout();
    managed_ = true;
    needs_update_ = false;
  }
}

void ContainerWidget::MarkForUpdate() {
  ContainerWidget* w = this;
  while (w) {
    if (!w->managed_) {
      return;
    }
    w->needs_update_ = true;
    w = w->parent_widget();
  }
}

void ContainerWidget::OnLanguageChange() {
  for (auto&& widget : widgets_) {
    if (widget.exists()) {
      widget->OnLanguageChange();
    }
  }
}

auto ContainerWidget::IsTransitioningOut() const -> bool {
  return transitioning_out_;
}

}  // namespace ballistica::ui_v1
