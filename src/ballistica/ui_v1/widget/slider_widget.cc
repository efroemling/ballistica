// Released under the MIT License. See LICENSE for details.

#include "ballistica/ui_v1/widget/slider_widget.h"

#include <Python.h>

#include <algorithm>
#include <cmath>

#include "ballistica/base/assets/assets.h"
#include "ballistica/base/assets/texture_asset.h"
#include "ballistica/base/audio/audio.h"
#include "ballistica/base/graphics/component/empty_component.h"
#include "ballistica/base/graphics/component/simple_component.h"
#include "ballistica/base/input/input.h"
#include "ballistica/base/logic/logic.h"
#include "ballistica/base/python/support/python_context_call.h"
#include "ballistica/base/support/app_timer.h"
#include "ballistica/base/ui/ui.h"
#include "ballistica/core/core.h"
#include "ballistica/core/platform/platform.h"

namespace ballistica::ui_v1 {

/// Backing grey level. Note this is multiplied against the nub art's
/// shaded-sphere rgb, which is well below white, so the backing lands a
/// good deal darker than this number alone suggests.
constexpr float kBackingColor{0.4f};

/// Backing opacity.
constexpr float kBackingOpacity{0.2f};

/// Groove corner radius, as a fraction of the backing's radius.
constexpr float kGrooveRadiusScale{0.2f};

/// Groove opacity. Heavier than the backing so it reads as a recess.
constexpr float kGrooveOpacity{0.6f};

/// Drawn size of the nub relative to the geometric size the layout math
/// uses, so it hangs slightly over the well it rides in. Deliberately
/// *not* folded into NubSize_(): that drives travel and groove extents,
/// which stay tied to our actual bounds.
constexpr float kNubOverhangScale{1.4f};

/// How far the selection glow extends past us, as a fraction of our
/// height.
constexpr float kGlowExtendScale{0.35f};

/// Peak opacity of the selection glow.
constexpr float kGlowOpacity{0.3f};

/// Nub brightness while held. Matches the multiplier ButtonWidget uses
/// for a pressed button, so grabbing a nub reads the same as holding a
/// button down.
constexpr float kNubPressedMult{3.0f};

/// How close to a grid point (as a fraction of one increment) counts as
/// being on it, and how close to an endpoint counts as being at it.
constexpr float kGridTolerance{1e-3f};

/// How long after its last step a run of key/controller steps settles
/// (fires the change call). Long enough to span a held key's repeats and
/// a user tapping their way to a value; a run also settles at once when
/// we lose selection or a pointer press begins.
constexpr seconds_t kStepSettleSeconds{0.5};

/// Opacity multiplier for the backing and groove while disabled.
constexpr float kDisabledTrackOpacityScale{0.5f};

/// Nub grey level and opacity while disabled.
constexpr float kDisabledNubGrey{0.45f};
constexpr float kDisabledNubOpacity{0.6f};

/// Groove grey level. Deliberately not pure black: at zero the texture's
/// rgb is multiplied away entirely and only its alpha silhouette survives,
/// so the nub art's shading could not reach the groove at all.
constexpr float kGrooveColor{0.12f};

/// Build a rounded-rect ninepatch spanning [x, x+w] x [y, y+h].
static auto MakeRoundedMesh_(float x, float y, float w, float h, float radius)
    -> Object::Ref<base::NinePatchMesh> {
  return Object::New<base::NinePatchMesh>(
      x, y, 0.0f, w, h, base::NinePatchMesh::BorderForRadius(radius, w, h),
      base::NinePatchMesh::BorderForRadius(radius, h, w),
      base::NinePatchMesh::BorderForRadius(radius, w, h),
      base::NinePatchMesh::BorderForRadius(radius, h, w));
}

SliderWidget::SliderWidget() {
  birth_time_millisecs_ =
      static_cast<millisecs_t>(g_base->logic->display_time() * 1000.0);
}

SliderWidget::~SliderWidget() = default;

auto SliderWidget::TransitionScale_(millisecs_t current_time) const -> float {
  if (transition_type_ != TransitionType::kScale) {
    return 1.0f;
  }
  float in_progress = static_cast<float>(birth_time_millisecs_
                                         + transition_delay_ - current_time);
  if (in_progress <= 0.0f) {
    return 1.0f;
  }
  // Fixed 150ms scale-up at the tail of the transition window
  // (quadratic ease-out), the same curve TextWidget/ButtonWidget use.
  constexpr float kScaleDurationMs = 150.0f;
  float t = std::max(0.0f, 1.0f - in_progress / kScaleDurationMs);
  return 1.0f - (1.0f - t) * (1.0f - t);
}

auto SliderWidget::NubSize_() const -> float {
  return std::min(width_, height_);
}

auto SliderWidget::NubMinCenterX_() const -> float { return NubSize_() * 0.5f; }

auto SliderWidget::NubTravel_() const -> float {
  return std::max(0.0f, width_ - NubSize_());
}

auto SliderWidget::ValueFraction_() const -> float {
  float range = max_value_ - min_value_;
  if (range <= 0.0f) {
    return 0.0f;
  }
  return std::clamp((value_ - min_value_) / range, 0.0f, 1.0f);
}

auto SliderWidget::NubCenterX_() const -> float {
  return NubMinCenterX_() + ValueFraction_() * NubTravel_();
}

auto SliderWidget::GridValue_(float index) const -> float {
  // Always computed from an index rather than by accumulating increments.
  // Accumulation drifts -- step far enough and you land on 0.9999999
  // instead of 1.0 -- and it makes the value depend on the path taken to
  // reach it. This way a value arrived at by stepping is bit-identical to
  // the same value arrived at by dragging.
  float val = min_value_ + index * increment_;

  // An increment with no exact float representation (0.05, say) can still
  // put us a hair off an endpoint. Land on it exactly.
  float tolerance = std::abs(increment_) * kGridTolerance;
  if (std::abs(val - max_value_) < tolerance) {
    return max_value_;
  }
  if (std::abs(val - min_value_) < tolerance) {
    return min_value_;
  }
  return std::clamp(val, min_value_, max_value_);
}

auto SliderWidget::ValueGridIndex_() const -> float {
  float index = (value_ - min_value_) / increment_;

  // Treat an index a hair off a whole number as being on it, so float
  // error can't demote a step into a fractional nudge.
  float rounded = std::round(index);
  return std::abs(index - rounded) < kGridTolerance ? rounded : index;
}

auto SliderWidget::SnapValue_(float val) const -> float {
  val = std::clamp(val, min_value_, max_value_);
  if (increment_ <= 0.0f) {
    return val;
  }
  float snapped = GridValue_(std::round((val - min_value_) / increment_));

  // The range is not always a whole number of increments; where it is not,
  // max_value_ is off the grid and rounding alone could never reach it. Let
  // it win when it is the closer of the two.
  if (std::abs(max_value_ - val) < std::abs(snapped - val)) {
    return max_value_;
  }
  return snapped;
}

void SliderWidget::SetRange(float min_value, float max_value) {
  min_value_ = min_value;
  max_value_ = std::max(min_value, max_value);
  SetValue(value_);
}

void SliderWidget::SetValue(float val) {
  value_ = std::clamp(val, min_value_, max_value_);
}

void SliderWidget::SetOnDragCall(PyObject* call_tuple) {
  on_drag_call_ = Object::New<base::PythonContextCall>(call_tuple);
}

void SliderWidget::SetOnChangeCall(PyObject* call_tuple) {
  on_change_call_ = Object::New<base::PythonContextCall>(call_tuple);
}

void SliderWidget::RunCall_(
    const Object::Ref<base::PythonContextCall>& call) const {
  if (auto* c = call.get()) {
    PythonRef args(Py_BuildValue("(f)", value_), PythonRef::kSteal);

    // Schedule this to run immediately after any current UI traversal.
    c->ScheduleInUIOperation(args);
  }
}

void SliderWidget::OnStep_(float prev_value) {
  if (!step_settle_timer_.exists()) {
    step_start_value_ = prev_value;
  }
  RunCall_(on_drag_call_);

  // Restart the quiet period. (Recreated rather than re-lengthened so the
  // countdown provably starts over from this step.)
  step_settle_timer_ = base::AppTimer::New(kStepSettleSeconds, false, [this] {
    // Runs from a timer, so outside of any UI operation; give our calls
    // one to run in.
    base::UI::OperationContext ui_op_context;
    SettleSteps_();
    ui_op_context.Finish();
  });
}

void SliderWidget::SettleSteps_() {
  if (!step_settle_timer_.exists()) {
    return;
  }
  // Note: this may be running from the timer itself; clearing it here is
  // fine (ButtonWidget's repeat timer does the same).
  step_settle_timer_.Clear();
  if (value_ != step_start_value_) {
    RunCall_(on_change_call_);
  }
}

void SliderWidget::SetEnabled(bool val) {
  if (val == enabled_) {
    return;
  }
  enabled_ = val;
  if (!enabled_) {
    // Whatever was in progress ends here. A drag commits where it got
    // to, just as a release would; a pending run of steps settles.
    // (Callers can disable us outside of UI operations, so bring our
    // own.)
    base::UI::OperationContext ui_op_context;
    if (pressed_) {
      pressed_ = false;
      dragging_ = false;
      if (value_ != drag_start_value_) {
        RunCall_(on_change_call_);
      }
    }
    SettleSteps_();
    hover_ = false;
    ui_op_context.Finish();
  }
}

void SliderWidget::SetSelected(bool s, SelectionCause cause) {
  Widget::SetSelected(s, cause);
  if (!s) {
    // Nothing else can step us now, so there is nothing to wait for.
    // (Callers can deselect outside of UI operations, so bring our own.)
    base::UI::OperationContext ui_op_context;
    SettleSteps_();
    ui_op_context.Finish();
  }
}

auto SliderWidget::SetValueFromPointerX_(float x) -> bool {
  float travel = NubTravel_();
  float frac = travel <= 0.0f
                   ? 0.0f
                   : std::clamp((x - NubMinCenterX_()) / travel, 0.0f, 1.0f);
  float val = SnapValue_(min_value_ + frac * (max_value_ - min_value_));
  if (val == value_) {
    return false;
  }
  value_ = val;
  return true;
}

auto SliderWidget::Step_(int dir) -> bool {
  if (increment_ <= 0.0f) {
    // No grid to step along.
    return false;
  }
  float index = ValueGridIndex_();

  // Move to the adjacent grid point. Using floor/ceil rather than index +
  // dir means a value sitting *between* grid points (one set exactly by
  // SetValue, or an off-grid max) steps onto the grid rather than staying
  // off it forever.
  float target = dir > 0 ? std::floor(index) + 1.0f : std::ceil(index) - 1.0f;
  float val = GridValue_(target);
  if (val == value_) {
    return false;
  }
  value_ = val;
  return true;
}

auto SliderWidget::GetMult_(millisecs_t current_time, bool textured) const
    -> float {
  float mult = 1.0f;
  if (IsHierarchySelected() && g_base->ui->ShouldHighlightWidgets()) {
    mult =
        0.8f
        + std::abs(sinf(static_cast<float>(current_time) * 0.006467f)) * 0.2f;

    // Same split ButtonWidget uses: textured bits pulse brighter, since a
    // custom texture can be dark on its own.
    mult *= textured ? 2.0f : 1.7f;
  } else {
    // Idle hover highlight -- mouse only, never touchscreen.
    if (hover_ && !g_base->ui->touch_mode()) {
      mult = 1.2f;
    }
  }
  return mult;
}

void SliderWidget::EnsureMeshes_() {
  if (backing_mesh_.exists() && mesh_width_ == width_
      && mesh_height_ == height_) {
    return;
  }
  mesh_width_ = width_;
  mesh_height_ = height_;

  // Backing: a radius of exactly half our height makes the two ends
  // half-circles, so the (circular, height-diameter) nub sits flush inside
  // them when driven fully left or right.
  //
  // Centered on its own origin like the groove, so Draw() can mirror it
  // with a negative scale without also moving it.
  float backing_radius = height_ * 0.5f;
  backing_mesh_ = MakeRoundedMesh_(width_ * -0.5f, height_ * -0.5f, width_,
                                   height_, backing_radius);

  // Groove: spans exactly the nub-center travel, so it reads as the line
  // the nub rides along. Its own height is twice its radius, making it a
  // pill like the backing.
  //
  // Built centered on its own origin rather than in place. Its travel span
  // is symmetric about the widget, so its center is simply our center --
  // and drawing it from a centered mesh is what lets Draw() flip it with a
  // negative scale (see there) without also moving it.
  float groove_radius = backing_radius * kGrooveRadiusScale;
  float groove_h = groove_radius * 2.0f;
  float groove_w = NubTravel_();
  if (groove_w <= 0.0f) {
    // Degenerate (we're no wider than we are tall): no travel, so there's
    // no groove to draw.
    groove_mesh_.Clear();
  } else {
    groove_mesh_ = MakeRoundedMesh_(groove_w * -0.5f, groove_h * -0.5f,
                                    groove_w, groove_h, groove_radius);
  }

  // Selection glow: our shape, inflated on every side. Its radius keeps it
  // a pill too, so the glow hugs the backing rather than boxing it.
  float glow_extend = height_ * kGlowExtendScale;
  float glow_w = width_ + glow_extend * 2.0f;
  float glow_h = height_ + glow_extend * 2.0f;
  glow_mesh_ = MakeRoundedMesh_(-glow_extend, -glow_extend, glow_w, glow_h,
                                glow_h * 0.5f);
}

void SliderWidget::Draw(base::RenderPass* pass, bool draw_transparent) {
  // Everything we draw is alpha-blended, so we're a transparent-pass-only
  // widget.
  if (!draw_transparent) {
    return;
  }

  millisecs_t real_time = g_core->AppTimeMillisecs();

  Vector3f tilt = 0.01f * g_base->input->tilt();
  if (draw_control_parent()) {
    tilt += 0.02f * g_base->input->tilt();
  }
  float extra_offs_x = -tilt.y;
  float extra_offs_y = tilt.x;

  EnsureMeshes_();

  auto* nub_tex = g_ui_v1->assets().nub.get();

  // Scale-in transition: everything below scales about our center. (The
  // transform's scope runs to the end of this function.)
  base::EmptyComponent transition_c(pass);
  transition_c.SetTransparent(true);
  {
    auto transition_xf = transition_c.ScopedTransform();
    float transition_scale =
        TransitionScale_(pass->frame_def()->display_time_millisecs());
    if (transition_scale != 1.0f) {
      transition_c.Translate(width_ * 0.5f, height_ * 0.5f, 0.0f);
      transition_c.Scale(transition_scale, transition_scale, 1.0f);
      transition_c.Translate(-width_ * 0.5f, -height_ * 0.5f, 0.0f);
    }
    transition_c.Submit();

    // Selection glow (depth 0.05, behind everything). The ninepatch
    // 'uniform' glow TextWidget uses for its selection highlight -- shaped
    // to our outline rather than the older gradient blob, which only ever
    // approximates a rectangle.
    if (IsHierarchySelected() && g_base->ui->ShouldHighlightWidgets()) {
      // Same pulse TextWidget's highlight runs on.
      float m =
          0.5f
          + std::abs(sinf(static_cast<float>(real_time) * 0.006467f) * 0.4f);
      auto* tex = g_ui_v1->assets().shadow_sharp.get();

      // Premultiply rgb by alpha for premultiplied textures so the glow
      // composites 'over' under premult blend instead of adding
      // full-brightness rgb.
      float a = kGlowOpacity * m;
      float cmul = tex->premultiplied() ? a : 1.0f;

      base::SimpleComponent c(pass);
      c.SetTransparent(true);
      c.SetColor(0.9f * m * cmul, 1.0f * m * cmul, 0.0f, a);
      c.SetTexture(tex);
      {
        auto xf = c.ScopedTransform();
        c.Translate(extra_offs_x, extra_offs_y, 0.05f);
        c.DrawMesh(glow_mesh_.get());
      }
      c.Submit();
    }

    // Backing (depth 0.1). Textured and mirrored exactly like the groove, so
    // the whole well reads as one indented surface.
    //
    // Its base color is grey rather than white for two reasons: the
    // selection multiplier needs somewhere to go (at full white it would
    // just clamp and never visibly highlight), and the texture's rgb -- where
    // the shading lives -- has to survive being multiplied by it.
    {
      float mult = GetMult_(real_time, false);
      float opacity =
          kBackingOpacity * (enabled_ ? 1.0f : kDisabledTrackOpacityScale);

      // Premultiply rgb by alpha for premultiplied textures so this
      // composites 'over' under premult blend instead of adding
      // full-brightness rgb.
      float cmul = nub_tex->premultiplied() ? opacity : 1.0f;
      float c_base = kBackingColor * mult * cmul;

      base::SimpleComponent c(pass);
      c.SetTransparent(true);
      c.SetColor(c_base, c_base, c_base, opacity);
      c.SetTexture(nub_tex);
      {
        auto xf = c.ScopedTransform();
        c.Translate(width_ * 0.5f + extra_offs_x, height_ * 0.5f + extra_offs_y,
                    0.1f);
        // Mirrored on both axes; see the groove draw below for why this is
        // safe and what it buys.
        c.Scale(-1.0f, -1.0f, 1.0f);
        c.DrawMesh(backing_mesh_.get());
      }
      c.Submit();
    }

    // Groove (depth 0.3, between the backing and the nub).
    //
    // Textured with the nub art so the two read as the same material, but
    // flipped on both axes -- the nub's shading is lit from above, which on
    // a groove reads as extruded; mirroring it puts the highlight on the
    // lower edge so the groove reads as indented instead.
    //
    // No selection multiplier here: the groove reads as a recess rather than
    // a lit surface, so holding it steady while the backing around it pulses
    // is the intent.
    if (groove_mesh_.exists()) {
      float opacity =
          kGrooveOpacity * (enabled_ ? 1.0f : kDisabledTrackOpacityScale);

      // Premultiply rgb by alpha for premultiplied textures, as with the
      // backing.
      float cmul = nub_tex->premultiplied() ? opacity : 1.0f;
      float c_base = kGrooveColor * cmul;

      base::SimpleComponent c(pass);
      c.SetTransparent(true);
      c.SetColor(c_base, c_base, c_base, opacity);
      c.SetTexture(nub_tex);
      {
        auto xf = c.ScopedTransform();
        c.Translate(width_ * 0.5f + extra_offs_x, height_ * 0.5f + extra_offs_y,
                    0.3f);
        // Mirror on both axes. The mesh is centered and the pill is symmetric
        // about both, so the silhouette is unchanged and only the texture
        // mapping flips. Two mirrors compose to a rotation, so winding order
        // -- and thus face culling -- is preserved.
        c.Scale(-1.0f, -1.0f, 1.0f);
        c.DrawMesh(groove_mesh_.get());
      }
      c.Submit();
    }

    // Nub (depth 0.5, in front of everything else). Sized to our short
    // dimension; this will become the draggable part.
    {
      // Held wins over the selection pulse, the same precedence
      // ButtonWidget::GetMult uses. Note this stays lit for the whole drag
      // even once the pointer wanders off us -- unlike a button, which
      // un-lights when you slide off it, a slider still owns the grab.
      // (A disabled slider can be pressed - that selects it - but its
      // nub doesn't light as if grabbed.)
      float mult =
          (pressed_ && enabled_) ? kNubPressedMult : GetMult_(real_time, true);
      float nub_size = NubSize_() * kNubOverhangScale;

      // Disabled: grey and see-through (still pulsing when selected, so
      // selection stays visible). Premultiplied as with the backing,
      // since this is the one case where the nub isn't opaque.
      float r = color_r_;
      float g = color_g_;
      float b = color_b_;
      float a = 1.0f;
      if (!enabled_) {
        r = g = b = kDisabledNubGrey;
        a = kDisabledNubOpacity;
      }
      float cmul = nub_tex->premultiplied() ? a : 1.0f;
      base::SimpleComponent c(pass);
      c.SetTransparent(true);
      c.SetColor(r * mult * cmul, g * mult * cmul, b * mult * cmul, a);
      c.SetTexture(nub_tex);
      {
        auto xf = c.ScopedTransform();
        c.Translate(NubCenterX_() + 3.0f * extra_offs_x,
                    height_ * 0.5f + 3.0f * extra_offs_y, 0.5f);
        c.Scale(nub_size, nub_size, 0.5f);
        c.DrawMeshAsset(g_ui_v1->assets().image1x1.get());
      }
      c.Submit();
    }
  }  // End of the transition transform's scope.
  transition_c.Submit();
}

auto SliderWidget::HandleMessage(const base::WidgetMessage& m) -> bool {
  // How far outside our bounds touches register.
  float overlap;
  if (g_core->platform->IsRunningOnDesktop()) {
    overlap = 0.0f;
  } else {
    overlap = 12.0f;
  }
  auto in_bounds = [this, overlap](float x, float y) {
    return (x >= -overlap) && (x < width_ + overlap) && (y >= -overlap)
           && (y < height_ + overlap);
  };

  switch (m.type) {
    case base::WidgetMessage::Type::kMouseMove: {
      bool claimed = (m.fval3 > 0.0f);
      // (No hover while disabled, as with ButtonWidget.)
      hover_ = (claimed || !enabled_) ? false : in_bounds(m.fval1, m.fval2);
      if (dragging_) {
        if (SetValueFromPointerX_(m.fval1)) {
          RunCall_(on_drag_call_);
        }
        return true;
      }
      return hover_;
    }
    case base::WidgetMessage::Type::kMouseDown: {
      // Disabled: a press still selects us (we stay selectable, so a tap
      // should do what navigating to us does) but never drags. We still
      // claim it, and so its release; with dragging_ off and the value
      // untouched, the release commits nothing.
      if (!enabled_) {
        if (in_bounds(m.fval1, m.fval2)) {
          GlobalSelect();
          pressed_ = true;
          dragging_ = false;
          drag_start_value_ = value_;
          return true;
        }
        return false;
      }
      if (in_bounds(m.fval1, m.fval2)) {
        // A pending run of steps is over; commit it before this drag
        // starts measuring from our current value.
        SettleSteps_();
        GlobalSelect();
        pressed_ = true;
        dragging_ = true;
        drag_start_value_ = value_;

        // A press anywhere on us takes the nub to that spot and drags on
        // from there, rather than requiring the nub itself be hit -- it is
        // a small target, especially on touch.
        if (SetValueFromPointerX_(m.fval1)) {
          RunCall_(on_drag_call_);
        }
        return true;
      }
      return false;
    }
    case base::WidgetMessage::Type::kMouseUp: {
      // Claim the release of anything we claimed the press for, so the
      // input system doesn't consider a press still outstanding.
      if (pressed_) {
        pressed_ = false;
        dragging_ = false;
        if (value_ != drag_start_value_) {
          RunCall_(on_change_call_);
        }
        return true;
      }
      break;
    }
    case base::WidgetMessage::Type::kMouseCancel: {
      if (pressed_) {
        pressed_ = false;
        dragging_ = false;

        // A release just outside a scroll area we sit in comes through
        // as a cancel, but it's still the drag ending where it ended
        // (dragged off the end of the track, say); commit it like any
        // release.
        if (m.released_outside) {
          if (value_ != drag_start_value_) {
            RunCall_(on_change_call_);
          }
          return true;
        }

        // A cancel means the gesture was not ours after all (a parent
        // scroll-widget claiming a swipe, say), so put the value back.
        //
        // The revert goes out on the *drag* call, not the change call:
        // on_drag_call is the live-display channel, so a caller mirroring
        // the value would otherwise be left showing one we no longer
        // hold. on_change_call stays silent -- nothing was committed, so
        // whatever expensive work it guards should not run.
        if (value_ != drag_start_value_) {
          value_ = drag_start_value_;
          RunCall_(on_drag_call_);
        }
        return true;
      }
      break;
    }
    case base::WidgetMessage::Type::kMoveLeft:
    case base::WidgetMessage::Type::kMoveRight: {
      int dir = m.type == base::WidgetMessage::Type::kMoveLeft ? -1 : 1;
      float prev_value = value_;
      if (!enabled_) {
        // Swallowed (see below), but say no audibly.
        g_base->audio->SafePlayBuiltinSound(base::BuiltinSoundID::kAudioError);
      } else if (Step_(dir)) {
        if (dragging_) {
          // Stepped mid-drag; just part of the drag, which the release
          // commits.
          RunCall_(on_drag_call_);
        } else {
          OnStep_(prev_value);
        }
      }
      // Consumed even when we did not move (or are disabled), so
      // horizontal navigation never escapes a slider; up/down is the way
      // out.
      return true;
    }
    default:
      break;
  }
  return false;
}

}  // namespace ballistica::ui_v1
