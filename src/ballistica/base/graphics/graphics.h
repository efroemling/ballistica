// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_GRAPHICS_GRAPHICS_H_
#define BALLISTICA_BASE_GRAPHICS_GRAPHICS_H_

#include <list>
#include <map>
#include <mutex>
#include <string>
#include <vector>

#include "ballistica/base/base.h"
#include "ballistica/base/graphics/support/graphics_client_context.h"
#include "ballistica/base/graphics/support/graphics_settings.h"
#include "ballistica/shared/foundation/object.h"
#include "ballistica/shared/generic/snapshot.h"
#include "ballistica/shared/math/rect.h"
#include "ballistica/shared/math/vector2f.h"
#include "ballistica/shared/math/vector3f.h"

namespace ballistica::base {

// Thickness of each edge's black border in tv-border mode, as a fraction
// of window height (uniform thickness on all four edges). Note that this
// intentionally differs from broadcast safe-area conventions (which are
// per-dimension percentages); a uniform frame looks more deliberate, and
// this value still covers typical (2.5-5% per edge) overscan vertically
// and horizontally on common aspect ratios.
const float kTVBorder = 0.035f;

// Bounds our active render rect's aspect ratio is clamped to; window
// regions beyond these get black bars so extreme window shapes can't
// break our UI. Max matches the widest broadly-available phone aspect
// (mainstream tops out at 20:9; 21:9 covers legacy Sony Xperias).
// Foldable cover displays (~22-23:9) intentionally get thin bars.
const float kMinAspectRatio = 4.0f / 3.0f;
const float kMaxAspectRatio = 21.0f / 9.0f;

// Whether content may bleed a little past a computed OS inset.
//
// SET THIS FALSE WHEN MEASURING VIRTUAL BOUNDS AGAINST OS-PROVIDED
// GEOMETRY -- notches, cutouts, rounded corners. The bleed deliberately
// pulls the bounds *inside* the obstruction, so with it on you cannot
// tell a correct inset from one that is off by about the bleed amount.
// Our alignment checks all assume it is off.
const bool kVirtualBoundsBleedEnabled = true;

// How far past a computed inset content may extend, in VIRTUAL units
// (the same units widgets are positioned in, where the safe area is
// 1280x720). Defining property: a rect this many units wide, drawn in
// virtual coords, is exactly the overhang.
//
// Virtual units rather than pixels because this offsets our own UI's
// margins, which are in virtual units too -- compensating in the same
// units as the thing being compensated keeps it right across devices.
// Our elements already sit some way in from the virtual screen edge,
// so insetting by an obstruction's full depth stacks that margin on
// clearance that is already sufficient.
//
// A starting guess, meant to be tuned by eye rather than derived. Note
// there is no obstruction we can safely bleed into "for free": a
// rounded corner starts clipping immediately, and so does a cutout
// that reaches the screen edge. Even one that floats clear of the edge
// (an iPhone's Dynamic Island) only spares us until the bleed reaches
// it. So this is a judgment across all of those at once -- how much
// overhang looks right given our elements' own margins -- and not a
// figure any single case implies.
const float kVirtualBoundsBleed = 40.0f;

// Most of one edge of the active render rect we will give up to an
// OS-reported inset. This drives camera framing and UI layout now, so
// a device reporting something absurd (or a unit mix-up in a platform
// layer) should cost us a clipped corner, not the play area.
const float kMaxVirtualBoundsInsetFraction = 0.15f;

// Debug-only forced virtual-bounds inset, as fractions of the active
// render rect (l/r of its width, b/t of its height). Deliberately
// ASYMMETRIC on all four edges: a symmetric inset would hide a
// transposed or sign-flipped axis, which is exactly the bug class the
// A/B test exists to catch. Only ever applied when the
// BA_VIRTUAL_BOUNDS_AB env var asks for it.
const float kDebugVirtualBoundsInsetL = 0.060f;
const float kDebugVirtualBoundsInsetR = 0.020f;
const float kDebugVirtualBoundsInsetB = 0.100f;
const float kDebugVirtualBoundsInsetT = 0.035f;

// How long each config is shown for in A/B toggle mode.
const millisecs_t kDebugVirtualBoundsABPeriod{1000};

// Debug-only forced max-margin virtual bounds: the margin between the
// virtual bounds and the virtual outer rect on each edge while the
// mode is on, in VIRTUAL units (x applies to left and right, y to
// bottom and top). Fixed virtual-unit values on purpose - the margin
// UIs calibrate against must be identical on every device and window
// shape - and sized to comfortably exceed anything OS insets produce
// in the wild (worst current case is an iPhone notch at roughly 100
// units pre-bleed). OS insets and the bleed are irrelevant while this
// is on; those exist to derive reasonable bounds from hardware, where
// this forces exact margins regardless of hardware. Toggled from the
// dev-console UI tab.
const float kDebugMaxVirtualBoundsMarginX = 80.0f;
const float kDebugMaxVirtualBoundsMarginY = 40.0f;

// Debug-only: alternate the virtual outer rect *as reported to UI
// code* once per second between the no-margins rect (matching the
// virtual bounds) and the real thing, firing a full screen-size-change
// reflow on each flip. For eyeballing UIs being adapted to the outer
// rect: backgrounds should expand to fill the margins and snap back
// while layout within the virtual bounds stays put. Pair with the
// dev-console Max Margins toggle to get margins on a desktop window.
//
// Reported-only on purpose: actual rendering (projection extension,
// fade coverage, the graphics-server side) keeps using the real rect,
// so nothing stretches and no camera buffers rebuild - only UI
// consumers (babase.get_virtual_outer_rect() and friends) see the
// alternation.
const bool kDebugVirtualOuterRectToggleEnabled = false;

/// Which of the two equivalent virtual-bounds configs to run in. Both
/// use the exact same bounds rect; they differ only in how far drawing
/// extends past it, so anything inside the bounds must look identical
/// in both. See docs/initiatives/active-render-rect.md.
enum class VirtualBoundsABMode : uint8_t {
  /// No forced inset; bounds match the render rect (normal operation).
  kDisabled,
  /// Render rect inset to the bounds, so black fills the margins.
  kA,
  /// Render rect left full, so real drawn content fills the margins.
  kB,
  /// Alternate A and B once per second.
  kToggle
};

const float kVRBorder = 0.085f;

// Light/shadow res is divided by this to get pure light res.
const int kLightResDiv{4};

// How we divide up our z depth spectrum:
const float kBackingDepth5{1.0f};

// Background
// blit-shapes (with cam buffer)
const float kBackingDepth4{0.9f};

// World (without cam buffer) or overlay-3d (with cam buffer)
const float kBackingDepth3C{0.65f};
const float kBackingDepth3B{0.4f};
const float kBackingDepth3{0.15f};

// Overlay-3d (without cam buffer) / overlay(vr)
const float kBackingDepth2C{0.147f};
const float kBackingDepth2B{0.143f};
const float kBackingDepth2{0.14f};

// Overlay(non-vr) // cover (vr)
const float kBackingDepth1B{0.01f};
const float kBackingDepth1{0.0f};

const float kShadowNeutral{0.5f};

// Cursor depth within the front-overlay (not related to above depths).
const float kCursorZDepth{1.0f};

// Client class for graphics operations (used from the logic thread).
class Graphics {
 public:
  Graphics();

  void OnAppStart();
  void OnAppSuspend();
  void OnAppUnsuspend();
  void OnAppShutdown();
  void OnAppShutdownComplete();
  void OnScreenSizeChange();
  void ApplyAppConfig();

  /// Should be called by the app-adapter to keep the engine informed on the
  /// drawable area it has to work with (in pixels).
  void SetScreenResolution(float x, float y);

  /// Should be called when UIScale changes.
  void OnUIScaleChange();

  /// Report the OS-provided safe-area insets for the current display,
  /// as fractions (0-1) of the full drawable area in each direction.
  ///
  /// Fractions rather than pixels on purpose: a platform's insets and
  /// our GL surface are often in different pixel spaces (an Android
  /// window of 2424x1080 backing a 1616x720 surface, iOS points vs
  /// pixels), and handing pixels across that seam invites applying
  /// them in the wrong one. A fraction is the same number in either.
  ///
  /// Platform layers call this whenever their values change (rotation,
  /// a fold, a window move between displays); it is cheap to call
  /// redundantly since identical values are ignored. All four edges are
  /// taken even though only left/right are honored today -- see
  /// UpdateScreen_ for why that split lives at the point of use rather
  /// than at the platform layers.
  ///
  /// Must be called from the logic thread; platform layers generally
  /// need to push a call (see AppAdapter/from_swift for the pattern).
  void SetOSSafeAreaInsets(float l, float r, float b, float t);

  void StepDisplayTime();

  auto TextureQualityFromAppConfig() -> TextureQualityRequest;
  auto GraphicsQualityFromAppConfig() -> GraphicsQualityRequest;
  auto VSyncFromAppConfig() -> VSyncRequest;

  static auto IsShaderTransparent(ShadingType c) -> bool;
  /// The environment cube map for a reflection type, from the
  /// app-mode-supplied base asset set (see babase.set_base_asset_set).
  static auto CubeMapFromReflectionType(ReflectionType reflection_type)
      -> TextureAsset*;

  // Given a string, return a reflection type.
  static auto ReflectionTypeFromString(const std::string& s) -> ReflectionType;

  // ..and the opposite.
  static auto StringFromReflectionType(ReflectionType reflectionType)
      -> std::string;

  void Reset();
  void BuildAndPushFrameDef();

  virtual void ApplyCamera(FrameDef* frame_def);

  /// Called when the language changes.
  void LanguageChanged();

  void AddCleanFrameCommand(const Object::Ref<PythonContextCall>& c);
  void RunCleanFrameCommands();

  // Called when the GraphicsServer has sent us a frame-def for deletion.
  void ReturnCompletedFrameDef(FrameDef* frame_def);

  auto screen_pixel_width() const {
    assert(g_base->InLogicThread());
    return res_x_;
  }
  auto screen_pixel_height() const {
    assert(g_base->InLogicThread());
    return res_y_;
  }

  // Return the current size of the virtual screen. This value should always
  // be used for interface positioning, etc.
  auto screen_virtual_width() const {
    assert(g_base->InLogicThread());
    return res_x_virtual_;
  }
  auto screen_virtual_height() const {
    assert(g_base->InLogicThread());
    return res_y_virtual_;
  }

  // Given a point in space, returns the shadow density that should be drawn
  // into the shadow pass. Does this belong somewhere else?
  auto GetShadowDensity(float x, float y, float z) -> float;

  static void GetSafeColor(float* r, float* g, float* b,
                           float target_intensity = 0.6f);

  // Fade the local screen in or out over the given time period.
  void FadeScreen(bool to, millisecs_t time, PyObject* endcall);

  static void DrawRadialMeter(MeshIndexedSimpleFull* m, float amt);

  // Ways to add a few simple component types quickly (uses particle
  // rendering for efficient batches).
  void DrawBlotch(const Vector3f& pos, float size, float r, float g, float b,
                  float a) {
    DoDrawBlotch(&blotch_indices_, &blotch_verts_, pos, size, r, g, b, a);
  }

  void DrawBlotchSoft(const Vector3f& pos, float size, float r, float g,
                      float b, float a) {
    DoDrawBlotch(&blotch_soft_indices_, &blotch_soft_verts_, pos, size, r, g, b,
                 a);
  }

  // Draw a soft blotch on objects; not terrain.
  void DrawBlotchSoftObj(const Vector3f& pos, float size, float r, float g,
                         float b, float a) {
    DoDrawBlotch(&blotch_soft_obj_indices_, &blotch_soft_obj_verts_, pos, size,
                 r, g, b, a);
  }

  void DrawVirtualSafeAreaBounds(RenderPass* pass);
  void DrawVirtualBounds(RenderPass* pass);
  void ReadVirtualBoundsABMode_();
  void StepVirtualBoundsABToggle_();
  void StepVirtualOuterRectToggle_();
  auto CalcDebugVirtualBoundsRect_(const Rect& render_rect) -> Rect;
  auto CalcVirtualBoundsRect_(const Rect& render_rect) -> Rect;
  static void GetBaseVirtualRes(float* x, float* y);

  // Enable progress bar drawing locally.
  void EnableProgressBar(bool fade_in);

  auto* camera() { return camera_.get(); }
  void ToggleManualCamera();
  void LocalCameraShake(float intensity);
  void ToggleDebugDraw();
  auto network_debug_info_display_enabled() const {
    return network_debug_display_enabled_;
  }
  void ToggleNetworkDebugDisplay();
  auto floor_reflection() const {
    assert(g_base->InLogicThread());
    return floor_reflection_;
  }
  void set_floor_reflection(bool val) {
    assert(g_base->InLogicThread());
    floor_reflection_ = val;
  }
  void set_shadow_offset(const Vector3f& val) {
    assert(g_base->InLogicThread());
    shadow_offset_ = val;
  }
  void set_shadow_scale(float x, float y) {
    assert(g_base->InLogicThread());
    shadow_scale_.x = x;
    shadow_scale_.y = y;
  }
  void set_shadow_ortho(bool o) {
    assert(g_base->InLogicThread());
    shadow_ortho_ = o;
  }
  auto tint() const { return tint_; }
  void set_tint(const Vector3f& val) {
    assert(g_base->InLogicThread());
    tint_ = val;
  }

  void set_ambient_color(const Vector3f& val) {
    assert(g_base->InLogicThread());
    ambient_color_ = val;
  }
  void set_vignette_outer(const Vector3f& val) {
    assert(g_base->InLogicThread());
    vignette_outer_ = val;
  }
  void set_vignette_inner(const Vector3f& val) {
    assert(g_base->InLogicThread());
    vignette_inner_ = val;
  }
  /// Frames rendered over the most recent one-second stats window.
  /// Updated continuously while rendering (whether or not the
  /// on-screen fps display is enabled); always 0 in headless builds.
  auto last_fps() const {
    assert(g_base->InLogicThread());
    return last_fps_;
  }

  auto shadow_offset() const {
    assert(g_base->InLogicThread());
    return shadow_offset_;
  }
  auto shadow_scale() const {
    assert(g_base->InLogicThread());
    return shadow_scale_;
  }
  auto ambient_color() {
    assert(g_base->InLogicThread());
    return ambient_color_;
  }
  auto vignette_outer() const {
    assert(g_base->InLogicThread());
    return vignette_outer_;
  }
  auto vignette_inner() const {
    assert(g_base->InLogicThread());
    return vignette_inner_;
  }
  auto shadow_ortho() const {
    assert(g_base->InLogicThread());
    return shadow_ortho_;
  }
  void SetShadowRange(float lower_bottom, float lower_top, float upper_bottom,
                      float upper_top);
  void ReleaseFadeEndCommand();

  // Nodes that draw flat stuff into the overlay pass should query this z
  // value for where to draw in z.
  auto overlay_node_z_depth() {
    fetched_overlay_node_z_depth_ = true;
    return overlay_node_z_depth_;
  }

  // This should be called before/after drawing each node to keep the value
  // incrementing.
  void PreNodeDraw() { fetched_overlay_node_z_depth_ = false; }
  void PostNodeDraw() {
    if (fetched_overlay_node_z_depth_) {
      overlay_node_z_depth_ *= 0.99f;
    }
  }

  auto PixelToVirtualX(float x) const -> float {
    // Map based on our position within the virtual bounds (the sub-rect
    // of the window our virtual coordinate system maps onto). Positions
    // in border or bounds-margin regions map outside the
    // 0..virtual-res range.
    return res_x_virtual_
           * ((x - virtual_bounds_rect_.l) / virtual_bounds_rect_.width());
  }

  auto PixelToVirtualY(float y) const -> float {
    return res_y_virtual_
           * ((y - virtual_bounds_rect_.b) / virtual_bounds_rect_.height());
  }

  /// The sub-rect of the physical window that game content occupies, in
  /// pixels (bottom-left origin, y-up). Everything outside it is kept
  /// cleared to black. Matches the full window unless tv-border mode
  /// and/or aspect-ratio limiting is in effect.
  ///
  /// Note that this governs only how far drawing *extends*; what
  /// drawing coordinates *mean* is governed by virtual_bounds_rect().
  auto active_render_rect() const -> const Rect& {
    assert(g_base->InLogicThread());
    return active_render_rect_;
  }

  /// The sub-rect of the active render rect that our virtual coordinate
  /// system maps onto, in pixels (bottom-left origin, y-up). Equal to
  /// the active render rect unless inset to dodge camera cutouts,
  /// rounded screen corners, etc.
  ///
  /// Unlike the active render rect this does NOT clip anything; drawing
  /// simply continues out to the render rect edge with coords beyond
  /// the 0..virtual-res range. We draw *as if* this rect were the
  /// render rect and let the leftover margins fill with whatever the
  /// same drawing commands put there (backgrounds and whatnot), so
  /// important elements can stay inside it while the screen still
  /// paints edge to edge.
  auto virtual_bounds_rect() const -> const Rect& {
    assert(g_base->InLogicThread());
    return virtual_bounds_rect_;
  }

  /// The active render rect expressed in virtual coords. Equals
  /// (0, 0, virtual-res-x, virtual-res-y) when the virtual bounds
  /// aren't inset; otherwise l/b go negative and r/t exceed the virtual
  /// res by the margins. This is what projections extend out to and
  /// what full-screen-cover geometry needs to span.
  auto virtual_outer_rect() const -> const Rect& {
    assert(g_base->InLogicThread());
    return virtual_outer_rect_;
  }

  /// The virtual outer rect as reported to UI code. Normally identical
  /// to virtual_outer_rect(); under kDebugVirtualOuterRectToggleEnabled
  /// it alternates with the no-margins rect so outer-rect UI adaptation
  /// can be eyeballed. UI consumers should use this; rendering
  /// machinery must use virtual_outer_rect().
  auto reported_virtual_outer_rect() const -> Rect {
    assert(g_base->InLogicThread());
    if (kDebugVirtualOuterRectToggleEnabled && virtual_outer_rect_collapsed_) {
      return Rect{0.0f, 0.0f, res_x_virtual_, res_y_virtual_};
    }
    return virtual_outer_rect_;
  }

  /// Calc the virtual bounds for a render rect, given OS safe-area
  /// insets as fractions (0-1) of a ``res_x`` by ``res_y`` screen.
  ///
  /// Honors left/right only; the other two are accepted so the policy
  /// lives here rather than being re-decided per platform, and so that
  /// honoring them later is a change in one tested place.
  ///
  /// Note this *intersects* the unobscured region with the render rect
  /// rather than insetting the rect: tv-mode's border and the
  /// aspect clamp can already have pulled the rect in past a cutout,
  /// and insetting again would double-count. Whichever constraint
  /// reaches further in wins.
  ///
  /// Static and pure so the render path and its test share one
  /// implementation.
  static auto CalcVirtualBoundsRect(const Rect& render_rect, float res_x,
                                    float res_y, float inset_l, float inset_r,
                                    float inset_b, float inset_t,
                                    float bleed = 0.0f) -> Rect;

  /// Calc a virtual-bounds rect inset from ``render_rect`` so that
  /// exactly ``margin_x`` VIRTUAL units of margin land on the left and
  /// right edges and ``margin_y`` on the bottom and top, given the base
  /// virtual res the bounds' virtual scale will pin to.
  ///
  /// Margins are in virtual units while the virtual scale derives from
  /// the bounds being computed, so this solves that fixed point rather
  /// than approximating it: with the margins added, the outer rect
  /// spans (base-res + 2 * margin) virtual units on whichever axis
  /// CalcVirtualRes_ pins, so pixels-per-virtual-unit is render-size
  /// over that span - and the pinned axis is the one yielding the
  /// smaller scale.
  ///
  /// Static and pure so the render path and its test share one
  /// implementation.
  static auto CalcMaxMarginsVirtualBoundsRect(const Rect& render_rect,
                                              float base_virtual_res_x,
                                              float base_virtual_res_y,
                                              float margin_x, float margin_y)
      -> Rect;

  /// Extend a frustum built for ``bounds_rect`` outward so the same
  /// projection keeps going out to ``render_rect``.
  ///
  /// The l/r/b/t are frustum edge distances at the near plane (as
  /// ``Matrix44fFrustum`` wants them, i.e. the left edge sits at
  /// ``-l``). This extends rather than rescales: everything within
  /// the bounds lands on exactly the pixels it would have landed on
  /// had the render rect matched the bounds, which is the invariant
  /// virtual bounds exist to keep. A no-op when the two rects match.
  ///
  /// Static and pure so the render path and its test can share one
  /// implementation rather than two that agree until they don't.
  static void ExtendFrustumToRenderRect(const Rect& render_rect,
                                        const Rect& bounds_rect, float* l,
                                        float* r, float* b, float* t);

  /// Calc the active render rect expressed in virtual coords, given the
  /// render rect, the virtual bounds within it, and the virtual res the
  /// bounds map to. Shared by the logic and graphics threads so the two
  /// can't drift.
  static auto CalcVirtualOuterRect(const Rect& render_rect,
                                   const Rect& bounds_rect, float res_x_virtual,
                                   float res_y_virtual) -> Rect {
    // Guard against degenerate bounds; callers log those separately.
    float bw = bounds_rect.width();
    float bh = bounds_rect.height();
    if (bw <= 0.0f || bh <= 0.0f) {
      return Rect{0.0f, 0.0f, res_x_virtual, res_y_virtual};
    }
    float sx = res_x_virtual / bw;
    float sy = res_y_virtual / bh;
    return Rect{(render_rect.l - bounds_rect.l) * sx,
                (render_rect.b - bounds_rect.b) * sy,
                (render_rect.r - bounds_rect.l) * sx,
                (render_rect.t - bounds_rect.b) * sy};
  }

  /// Which forced virtual-bounds A/B config we're running, if any.
  auto virtual_bounds_ab_mode() const {
    assert(g_base->InLogicThread());
    return virtual_bounds_ab_mode_;
  }

  /// Calc the active render rect for a given window size and tv-border
  /// setting: the window inset by the tv border (if enabled) and then
  /// clamped to our min/max aspect ratios. Border is applied before the
  /// aspect clamp since uniform-thickness borders change the inner
  /// region's aspect.
  static auto CalcActiveRenderRect(float res_x, float res_y, bool tv_border)
      -> Rect;

  void set_internal_components_inited(bool val) {
    internal_components_inited_ = val;
  }
  auto show_net_info() const { return show_net_info_; }
  void set_show_net_info(bool val) { show_net_info_ = val; }
  auto GetDebugGraph(const std::string& name, bool smoothed) -> NetGraph*;

  // Used by meshes.
  void AddMeshDataCreate(MeshData* d);
  void AddMeshDataDestroy(MeshData* d);

  // For debugging: ensures that only transparent or opaque components are
  // submitted while enabled.
  auto drawing_transparent_only() const { return drawing_transparent_only_; }
  void set_drawing_transparent_only(bool val) {
    drawing_transparent_only_ = val;
  }

  /// Draw regular UI.
  virtual void DrawUI(FrameDef* frame_def);

  /// Draw dev console or whatever else on top of normal stuff.
  virtual void DrawDevUI(FrameDef* frame_def);

  auto drawing_opaque_only() const { return drawing_opaque_only_; }
  void set_drawing_opaque_only(bool val) { drawing_opaque_only_ = val; }

  // Handle testing values from _baclassic.value_test()
  virtual auto ValueTest(const std::string& arg, double* absval,
                         double* deltaval, double* outval) -> bool;
  virtual void DrawWorld(FrameDef* frame_def);

  void set_camera_shake_disabled(bool disabled) {
    camera_shake_disabled_ = disabled;
  }
  auto camera_shake_disabled() const { return camera_shake_disabled_; }

  auto* settings() const {
    assert(g_base->InLogicThread());
    assert(settings_snapshot_.exists());
    return settings_snapshot_.get()->get();
  }

  auto GetGraphicsSettingsSnapshot() -> Snapshot<GraphicsSettings>*;

  /// Called by the graphics-server when a new client context is ready.
  void set_client_context(Snapshot<GraphicsClientContext>* context);

  void UpdatePlaceholderSettings();

  auto has_client_context() -> bool {
    return client_context_snapshot_.exists();
  }

  auto client_context() const -> const GraphicsClientContext* {
    assert(g_base->InLogicThread());
    assert(client_context_snapshot_.exists());
    return client_context_snapshot_.get()->get();
  }

  static auto GraphicsQualityFromRequest(GraphicsQualityRequest request,
                                         GraphicsQuality auto_val)
      -> GraphicsQuality;
  static auto TextureQualityFromRequest(TextureQualityRequest request,
                                        TextureQuality auto_val)
      -> TextureQuality;

  /// For temporary use from arbitrary threads. This should be removed when
  /// possible and replaced with proper safe thread-specific access patterns
  /// (so we can support switching renderers/etc.).
  auto placeholder_texture_quality() const {
    assert(client_context_snapshot_.exists());
    return texture_quality_placeholder_;
  }

  /// For temporary use in arbitrary threads. This should be removed when
  /// possible and replaced with proper safe thread-specific access patterns
  /// (so we can support switching renderers/etc.).
  auto placeholder_client_context() const -> const GraphicsClientContext* {
    // Using this from arbitrary threads is currently ok currently since
    // context never changes once set. Will need to kill this call once that
    // can happen though.
    assert(client_context_snapshot_.exists());
    return client_context_snapshot_.get()->get();
  }
  /// Whether to draw a guide showing the virtual bounds - the area our
  /// virtual coord system covers. With no cutout inset this sits right
  /// at the edge of what we draw; inset, it pulls in and everything
  /// between it and the screen edge is margin that keeps getting drawn
  /// into. UI should stay inside it.
  auto draw_virtual_bounds() const {
    assert(g_base->InLogicThread());
    return draw_virtual_bounds_;
  }
  void set_draw_virtual_bounds(bool val) {
    assert(g_base->InLogicThread());
    draw_virtual_bounds_ = val;
  }

  auto draw_virtual_safe_area_bounds() const {
    return draw_virtual_safe_area_bounds_;
  }
  void set_draw_virtual_safe_area_bounds(bool val) {
    draw_virtual_safe_area_bounds_ = val;
  }

  /// Whether virtual bounds are being forced to leave fixed max
  /// margins against the virtual outer rect (a debug calibration
  /// target; see kDebugMaxVirtualBoundsMarginX/Y).
  auto force_max_virtual_bounds_margins() const {
    assert(g_base->InLogicThread());
    return force_max_virtual_bounds_margins_;
  }
  void SetForceMaxVirtualBoundsMargins(bool val);

  auto building_frame_def() const { return building_frame_def_; }

  ScreenMessages* const screenmessages;

 protected:
  void UpdateScreen_();
  virtual ~Graphics();
  virtual void DoDrawFade(FrameDef* frame_def, float amt);
  static void CalcVirtualRes_(float* x, float* y);
  void DrawBoxingGlovesTest(FrameDef* frame_def);
  void DrawBlotches(FrameDef* frame_def);
  void DrawCursor(FrameDef* frame_def);
  void DrawFades(FrameDef* frame_def);
  void DrawDebugBuffers(RenderPass* pass);
  void UpdateAndDrawOnlyProgressBar(FrameDef* frame_def);
  void DoDrawBlotch(std::vector<uint16_t>* indices,
                    std::vector<VertexSprite>* verts, const Vector3f& pos,
                    float size, float r, float g, float b, float a);
  auto GetEmptyFrameDef() -> FrameDef*;
  void InitInternalComponents(FrameDef* frame_def);
  void DrawMiscOverlays(FrameDef* frame_def);
  void DrawLoadDot(RenderPass* pass);
  void ClearFrameDefDeleteList();
  void DrawProgressBar(RenderPass* pass, float opacity);
  void UpdateProgressBarProgress(float target);
  void UpdateInitialGraphicsSettingsSend_();

  int last_total_frames_rendered_{};
  int last_fps_{};
  int progress_bar_loads_{};
  int frame_def_count_{};
  int frame_def_count_filtered_{};
  int next_settings_index_{};
  TextureQuality texture_quality_placeholder_{};
  bool drawing_transparent_only_{};
  bool drawing_opaque_only_{};
  bool internal_components_inited_{};
  bool fade_out_{true};
  bool progress_bar_{};
  bool progress_bar_fade_in_{};
  bool debug_draw_{};
  bool network_debug_display_enabled_{};
  bool hardware_cursor_visible_{};
  bool camera_shake_disabled_{};
  bool show_fps_{};
  bool show_ping_{};
  bool show_net_info_{};
  bool tv_border_{};
  bool floor_reflection_{};
  bool building_frame_def_{};
  bool shadow_ortho_{};
  bool fetched_overlay_node_z_depth_{};
  bool set_fade_start_on_next_draw_{};
  bool graphics_settings_dirty_{true};
  bool applied_app_config_{};
  bool sent_initial_graphics_settings_{};
  bool got_screen_resolution_{};
  bool draw_virtual_safe_area_bounds_{};
  bool draw_virtual_bounds_{};
  bool force_max_virtual_bounds_margins_{};
  bool virtual_bounds_ab_showing_b_{};
  bool virtual_outer_rect_collapsed_{};
  VirtualBoundsABMode virtual_bounds_ab_mode_{VirtualBoundsABMode::kDisabled};
  millisecs_t virtual_bounds_ab_last_switch_time_{};
  millisecs_t virtual_outer_rect_toggle_last_switch_time_{};
  Vector3f shadow_offset_{0.0f, 0.0f, 0.0f};
  Vector2f shadow_scale_{1.0f, 1.0f};
  Vector3f tint_{1.0f, 1.0f, 1.0f};
  Vector3f ambient_color_{1.0f, 1.0f, 1.0f};
  Vector3f vignette_outer_{0.0f, 0.0f, 0.0f};
  Vector3f vignette_inner_{1.0f, 1.0f, 1.0f};
  Vector3f jitter_{0.0f, 0.0f, 0.0f};
  std::string fps_string_;
  std::string ping_string_;
  std::string net_info_string_;
  std::map<std::string, Object::Ref<NetGraph>> debug_graphs_;
  std::mutex frame_def_delete_list_mutex_;
  std::list<Object::Ref<PythonContextCall>> clean_frame_commands_;
  std::vector<FrameDef*> recycle_frame_defs_;
  std::vector<uint16_t> blotch_indices_;
  std::vector<VertexSprite> blotch_verts_;
  std::vector<uint16_t> blotch_soft_indices_;
  std::vector<VertexSprite> blotch_soft_verts_;
  std::vector<uint16_t> blotch_soft_obj_indices_;
  std::vector<VertexSprite> blotch_soft_obj_verts_;
  std::vector<FrameDef*> frame_def_delete_list_;
  std::vector<MeshData*> mesh_data_creates_;
  std::vector<MeshData*> mesh_data_destroys_;
  float fade_{};
  float res_x_{256.0f};
  float res_y_{256.0f};
  float res_x_virtual_{256.0f};
  float res_y_virtual_{256.0f};
  Rect active_render_rect_{0.0f, 0.0f, 256.0f, 256.0f};
  float os_inset_l_{};
  float os_inset_r_{};
  float os_inset_b_{};
  float os_inset_t_{};
  Rect virtual_bounds_rect_{0.0f, 0.0f, 256.0f, 256.0f};
  Rect virtual_outer_rect_{0.0f, 0.0f, 256.0f, 256.0f};
  float overlay_node_z_depth_{};
  float progress_bar_progress_{};
  float shadow_lower_bottom_{-4.0f};
  float shadow_lower_top_{4.0f};
  float shadow_upper_bottom_{30.0f};
  float shadow_upper_top_{40.0f};
  seconds_t last_cursor_visibility_event_time_{};
  millisecs_t fade_start_{};
  millisecs_t fade_cancel_start_{};
  millisecs_t fade_cancel_last_real_ms_{};
  millisecs_t fade_time_{};
  millisecs_t next_stat_update_time_{};
  millisecs_t progress_bar_end_time_{-9999};
  millisecs_t last_progress_bar_draw_time_{};
  millisecs_t last_progress_bar_start_time_{};
  millisecs_t last_create_frame_def_time_millisecs_{};
  millisecs_t last_jitter_update_time_{};
  microsecs_t next_frame_number_filtered_increment_time_{};
  microsecs_t last_create_frame_def_time_microsecs_{};
  Object::Ref<ImageMesh> screen_mesh_;
  Object::Ref<ImageMesh> progress_bar_bottom_mesh_;
  Object::Ref<ImageMesh> progress_bar_top_mesh_;
  Object::Ref<ImageMesh> load_dot_mesh_;
  Object::Ref<TextGroup> fps_text_group_;
  Object::Ref<TextGroup> ping_text_group_;
  Object::Ref<TextGroup> net_info_text_group_;
  Object::Ref<SpriteMesh> shadow_blotch_mesh_;
  Object::Ref<SpriteMesh> shadow_blotch_soft_mesh_;
  Object::Ref<SpriteMesh> shadow_blotch_soft_obj_mesh_;
  Object::Ref<Camera> camera_;
  Object::Ref<PythonContextCall> fade_end_call_;
  Object::Ref<Snapshot<GraphicsSettings>> settings_snapshot_;
  Object::Ref<Snapshot<GraphicsClientContext>> client_context_snapshot_;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_GRAPHICS_GRAPHICS_H_
