// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_DEPICTION_DEPICTION_H_
#define BALLISTICA_BASE_DEPICTION_DEPICTION_H_

#include <functional>
#include <optional>
#include <string>

#include "ballistica/base/base.h"
#include "ballistica/shared/foundation/object.h"
#include "ballistica/shared/generic/json_facade.h"

namespace ballistica::base {

/// The kinds of thing that host depictions. A kind that can't draw in
/// some host says so (see Depiction::SupportsHost), and that host
/// shows the placeholder instead.
enum class DepictionHost : uint8_t {
  /// A ui widget.
  kUI,
  /// An in-scene node (a 2d overlay in a game).
  kScene,
};

enum class DepictionHAlign : uint8_t { kLeft, kCenter, kRight };
enum class DepictionVAlign : uint8_t { kBottom, kCenter, kTop };

/// An axis-aligned box: left, bottom, width, height.
struct DepictionBox {
  float x{};
  float y{};
  float width{};
  float height{};
};

class Depiction;

/// Fit a depiction's shape into a host's box by alignment: contain-fit
/// at its aspect (width / height), except that a box narrower than
/// that but no narrower than its minimum aspect is taken whole (the
/// depiction squeezes itself to fit; see Depiction::GetMinAspect). No
/// aspect means the depiction has no shape of its own and takes the
/// whole box. The one place alignment math happens, so no kind (and no
/// host) does its own.
auto FitDepictionBox(const DepictionBox& box, const Depiction& depiction,
                     DepictionHAlign h_align, DepictionVAlign v_align)
    -> DepictionBox;

/// What a host hands a depiction to draw.
struct DepictionDrawContext {
  RenderPass* pass{};

  /// Which pass this is. UI draws an opaque and a transparent pass (and
  /// calls Draw for each); scene overlays draw once, transparent.
  bool transparent{true};

  /// Where to draw, already fitted (see FitDepictionBox), in the pass's
  /// current frame.
  DepictionBox box;
  float z{};

  /// The host's state. Brightness is a multiplier carrying emphasis
  /// (ui: its draw controller's brightness, the same one a button's
  /// label and images follow -- press flashes, focus pulses, hover),
  /// so a depiction flashes and pulses in step with its button.
  /// Disabled means the host is (ui: its draw controller is a
  /// standard-disabled button). Kinds show all of this through the
  /// standard look (the Standard* calls below) unless they draw states
  /// their own way. More states (focused, pressed, ...) can join here
  /// when a kind needs to tell them apart; they never touch the wire.
  float brightness{1.0f};
  float opacity{1.0f};
  bool disabled{};

  /// Physical pixels per box unit, as settled on screen (transitions
  /// aside), so kinds that render to a texture can size it to land one
  /// to one. Computed by the host from its own corners.
  float pixels_per_unit{1.0f};

  /// Host styling a kind may honor where it makes sense (a live picture
  /// does; an icon has its own shape): a mask whose alpha cuts the
  /// drawing's edges and whose green channel adds a frame in
  /// frame_color. Null for none.
  TextureAsset* mask_texture{};
  float frame_color[3]{1.0f, 1.0f, 1.0f};

  /// The standard look: what to draw with, host state applied. A
  /// disabled host fades its depiction and greys its colors, the way a
  /// disabled button fades its icon and greys its body (there's no
  /// desaturating a texture's own colors, so tints carry the grey).
  auto StandardOpacity() const -> float;
  auto StandardBrightness() const -> float;

  /// Grey an rgb color in place if disabled (to a grey scaled from its
  /// luminance, as disabled buttons and text do); else leave it be.
  void StandardColor(float* rgb) const;
};

/// Input a host routes to a depiction (hosts opt in; see
/// Depiction::GetInput). Positions are fractions (0-1) across the
/// depiction's box and up it.
class DepictionInput {
 public:
  /// A press landed on us. Return whether we take it; only a taken
  /// press gets drags and a release.
  virtual auto HandlePress(float x, float y) -> bool = 0;
  virtual void HandleDrag(float x, float y) = 0;
  virtual void HandleRelease() = 0;
};

/// A flat-color look a host can put over a depiction (see
/// Depiction::GetTintControl): drawn as one flat color in place of its
/// usual coloring -- a toolbar chest whose window is open, say. Applies
/// to this instance only; a replacement depiction starts without it,
/// so hosts re-apply on each update.
class DepictionTintControl {
 public:
  /// Draw flat in `rgb` (`flatness` 0-1, as SimpleComponent).
  virtual void SetFlatColor(const float* rgb, float flatness) = 0;
  virtual void ClearFlatColor() = 0;
};

/// One live depiction: something a server described for us to draw
/// (bacommon.depiction), parsed and ready. Created by the registry;
/// held by whatever hosts it. Logic thread only.
///
/// Design: docs/initiatives/depictions.md.
class Depiction : public Object {
 public:
  explicit Depiction(std::string type_id);
  ~Depiction() override;

  /// The shape we want (width / height), or none to fill the box.
  virtual auto GetAspect() const -> std::optional<float>;

  /// The narrowest shape (width / height) we can squeeze to while
  /// keeping the box's full height, for kinds that can give up width
  /// without shrinking (a capsule name compresses its text); in boxes
  /// narrower still we shrink at this aspect. Never more than
  /// GetAspect. None (the default) means we never squeeze.
  virtual auto GetMinAspect() const -> std::optional<float>;

  /// The part of ``box`` (our fitted box; see FitDepictionBox) we
  /// actually cover, for hosts that hit-test against what is drawn
  /// rather than their whole box. Defaults to all of it; a kind whose
  /// drawing doesn't fill its box (a short name in a wide one, say)
  /// can report less once it knows (until then, all of it, so a press
  /// never falls in a gap).
  virtual auto GetContentBox(const DepictionBox& box) const -> DepictionBox;

  /// Whether we can draw in a host of this kind.
  virtual auto SupportsHost(DepictionHost host) const -> bool;

  /// Called once per frame a host shows us, before drawing; kinds
  /// retry missing media here (see MediaRetryPacer). ``now`` is the
  /// host's millisecond clock.
  virtual void Update(millisecs_t now);

  virtual void Draw(const DepictionDrawContext& context) = 0;

  /// Our input handling, or nullptr if we take no input. Hosts only
  /// route input to us if they opt in (a depiction on a button must
  /// never swallow the button's press). See the design doc,
  /// "Capabilities".
  virtual auto GetInput() -> DepictionInput*;

  /// A Python object for driving us directly (a live viewer's own
  /// object, say, whose methods adjust what it shows without a new
  /// depiction from the server), or nullptr if we offer none. Borrowed
  /// reference; don't hold it past the host holding us.
  virtual auto GetPythonControl() -> PyObject*;

  /// Our flat-color override, or nullptr if we offer none (hosts then
  /// make do with brightness). Named by capability, not kind, so any
  /// kind may offer it. See the design doc, "Capabilities".
  virtual auto GetTintControl() -> DepictionTintControl*;

  /// Our kind's wire type id (bacommon.depiction.DepictionTypeID).
  auto type_id() const -> const std::string& { return type_id_; }

  /// Hosts call this each frame they show us (see Update).
  void MarkShown();

  /// Display-time seconds since we were last shown, so expensive kinds
  /// can be retired when idle.
  auto GetIdleTime() const -> seconds_t;

 private:
  std::string type_id_;
  seconds_t last_shown_time_{};
};

/// Where depiction kinds are made.
///
/// Kinds register a factory by wire type id. base registers its own;
/// kinds needing higher layers (a live 3d viewer needs scenes) are
/// registered by their feature set, so base never depends upward.
/// Logic thread only.
class DepictionRegistry {
 public:
  /// Parses a kind's json (the whole depiction object, ``_t``
  /// included) into an instance; may return nullptr for json it can't
  /// use, which gets the placeholder.
  struct Source {
    /// The parsed depiction object.
    const JsonRef& root;
    /// The json it was parsed from, for kinds that pass it along whole.
    const std::string& json;
    /// The host's key (see Create).
    const std::string& key;
  };
  using Factory =
      std::function<auto(const Source& source)->Object::Ref<Depiction>>;

  /// Register a kind. Done at startup by whichever feature set draws
  /// it (before anything makes depictions).
  static void RegisterKind(const std::string& type_id, Factory factory);

  /// Make a depiction from its json for a host. Anything this build
  /// can't draw in that host -- an unrecognized kind, a kind the host
  /// doesn't support, unusable json -- comes back as the placeholder
  /// (an outlined box with a question mark), with a one-time warning
  /// per kind: producers should only send clients what they can draw.
  ///
  /// ``key`` names what the host is showing, so kinds with something
  /// long-lived behind them (a live viewer) can carry on with it when
  /// the host gets a new depiction under the same key -- an editor's
  /// updated draft changes the picture in place instead of starting it
  /// over. Hosts pass a key unique to themselves by default.
  static auto Create(const std::string& json, DepictionHost host,
                     const std::string& key) -> Object::Ref<Depiction>;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_DEPICTION_DEPICTION_H_
