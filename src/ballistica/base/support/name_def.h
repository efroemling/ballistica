// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_SUPPORT_NAME_DEF_H_
#define BALLISTICA_BASE_SUPPORT_NAME_DEF_H_

#include <array>
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

  /// Drawn as a 9-patch split at its middle; a circle if absent.
  PackageAssetRef capsule_texture;

  /// Square; absent = no icon (and no room left for one).
  PackageAssetRef icon_texture;
  float icon_color[4]{1.0f, 1.0f, 1.0f, 1.0f};

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

  /// A glow around the text (RGBA; alpha = strength) in place of its
  /// drop shadow. Unset = the usual black drop shadow.
  std::optional<std::array<float, 4>> text_glow;

  /// Package manifest ('pk') and domain digest ('dg') for indexed
  /// texture refs (see PackageAssetRef).
  std::vector<std::string> packages;
  std::string domain_digest;
};

/// A name: its basic tier plus any richer ones this build understands.
/// The same form wherever a name appears -- on its own (a name
/// depiction; an account's name) or as a character's name. Parsed
/// leniently: anything unusable in a richer tier drops that tier, and
/// numbers clamp to their ranges.
struct NameDef {
  BasicNameDef basic;
  std::optional<CapsuleNameDef> capsule;

  /// Parse a name block ({"b": {...}, "c": {...}}). None if it has no
  /// usable basic tier. Logs (once) what it can't use.
  static auto Parse(const JsonRef& block) -> std::optional<NameDef>;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_SUPPORT_NAME_DEF_H_
