// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_SUPPORT_NAME_DEF_H_
#define BALLISTICA_BASE_SUPPORT_NAME_DEF_H_

#include <optional>
#include <string>
#include <vector>

#include "ballistica/base/support/media_block.h"
#include "ballistica/shared/generic/json_facade.h"

namespace ballistica::base {

/// Basic tier of a name: the canonical plain-text name (logs,
/// moderation, kick lists, scoreboards) and its color. Always present
/// whenever a name is; every richer tier degrades to drawing just this.
struct BasicNameDef {
  std::string text;
  float color[3]{1.0f, 1.0f, 1.0f};
};

/// Capsule tier of a name: the name drawn in a rounded capsule, with
/// an optional square icon filling the capsule's left end (an account
/// name's look). Drawn by clients that understand it; others draw the
/// basic tier.
///
/// Lengths are in cap heights (a nominal capital-letter height): a
/// radius of 1.0 makes the capsule exactly as tall as the text's
/// capitals, hugging them. The capsule edge says where the logical
/// shape sits within its art (1.0 = the art's edge; less lets glows and
/// such extend beyond it) so sizing never counts them.
struct CapsuleNameDef {
  float radius{2.3f};
  float capsule_color[4]{1.0f, 1.0f, 1.0f, 1.0f};
  float capsule_edge{1.0f};

  /// Drawn as a 9-patch; a circle if absent.
  PackageAssetRef capsule_texture;

  /// Where the capsule texture splits into its left end, the middle
  /// that fills between the ends, and its right end, as fractions of
  /// its width from each side. 0.5 each splits it at its middle (a
  /// middle one texel wide). Vertically it always splits at its middle.
  float capsule_insets[2]{0.5f, 0.5f};

  /// Repeat the texture's middle at the ends' scale (fitted to a whole
  /// number of copies) rather than stretching it. Its art must tile.
  bool capsule_tile{};

  /// Where a host's color override goes (see
  /// base::DepictionDrawContext::color_override), each replacing that
  /// part's own rgb (alphas still apply): the text (and its glow), the
  /// capsule body, each of the three tint channels, the icon. Just the
  /// text unless the capsule says otherwise -- so a capsule can route
  /// a team color into, say, a glow in one tint channel while its text
  /// keeps its own color.
  bool override_text{true};
  bool override_capsule{};
  bool override_tints[3]{};
  bool override_icon{};

  /// Optional tint texture over the capsule texture (same layout):
  /// its red, green, and blue channels say where each tint color
  /// multiplies in. Unset tint colors are white (no effect).
  PackageAssetRef capsule_tint_texture;
  float capsule_tint_colors[3][3]{
      {1.0f, 1.0f, 1.0f}, {1.0f, 1.0f, 1.0f}, {1.0f, 1.0f, 1.0f}};

  /// Square; absent = no icon (and no room left for one).
  PackageAssetRef icon_texture;
  float icon_color[4]{1.0f, 1.0f, 1.0f, 1.0f};

  /// How strongly team coloring tones each of our own colors (those
  /// the override isn't routed to; Graphics::ToneForTeamColor's
  /// strength, 0-1). Negative = unset: the standard strength.
  float capsule_team_coloring_strength{-1.0f};
  float capsule_tint_team_coloring_strengths[3]{-1.0f, -1.0f, -1.0f};
  float icon_team_coloring_strength{-1.0f};

  /// The icon's drawn size: 1.0 fills the capsule's left end (a square
  /// as tall as the capsule), centered there.
  float icon_scale{1.0f};

  /// Where in the scaled icon the text butts against it, as a fraction
  /// of the way from its center to its edge (above 1 leaves a gap).
  /// Spacing only; never changes how the icon draws. Calibrated per
  /// icon art, after which the text follows any icon_scale.
  float icon_edge{0.9f};

  /// How far the text reaches into the capsule's rounded ends, as a
  /// fraction of an end's depth: 0 keeps it on the straight section, 1
  /// runs it to the tip, negative pads it back. Without an icon this
  /// applies to both ends, with one only to the right. Unset = as far
  /// as the capitals stay inside the curve (see NameDepiction).
  std::optional<float> text_inset;

  /// How much the text glows like neon: white-hot interiors and a soft
  /// glow in the text's own color, in place of its drop shadow (0 =
  /// none and a normal drop shadow, 1 = standard).
  float text_glow{};

  /// Package manifest ('pk') and domain digest ('dg') for indexed
  /// texture refs (see PackageAssetRef).
  std::vector<std::string> packages;
  std::string domain_digest;
};

/// Glyph tier of a name: an icon glyph (one of the game's private-use
/// icon chars) drawn before the basic tier's text, in its color -- a
/// global profile's look. Never sent alongside a capsule; if both
/// arrive, the capsule wins.
struct GlyphNameDef {
  std::string icon;
};

/// A name: its basic tier plus any richer ones this build understands.
/// The same form wherever a name appears -- on its own (a name
/// depiction; an account's name) or as a character's name. Parsed
/// leniently: anything unusable in a richer tier drops that tier, and
/// numbers clamp to their ranges.
struct NameDef {
  BasicNameDef basic;
  std::optional<CapsuleNameDef> capsule;
  std::optional<GlyphNameDef> glyph;

  /// Parse a name block ({"b": {...}, "c": {...}, "g": {...}}). None if
  /// it has no usable basic tier. Logs (once) what it can't use.
  static auto Parse(const JsonRef& block) -> std::optional<NameDef>;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_SUPPORT_NAME_DEF_H_
