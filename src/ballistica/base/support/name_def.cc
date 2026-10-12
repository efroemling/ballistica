// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/support/name_def.h"

#include <algorithm>
#include <optional>
#include <string>

#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging.h"
#include "ballistica/core/logging/logging_macros.h"

namespace ballistica::base {

namespace {

// Allowed spans. Must match the name ranges in bamaster
// baserver/character.py; widen only alongside them.
struct Range {
  float lo;
  float hi;
};

const Range kRangeColor{0.0f, 2.0f};
const Range kRangeAlpha{0.0f, 1.0f};
const Range kRangeRadius{1.0f, 8.0f};
const Range kRangeEdge{0.5f, 1.0f};
const Range kRangeIconScale{0.1f, 2.0f};
const Range kRangeTextInset{-1.0f, 1.0f};
const Range kRangeIconEdge{0.0f, 2.0f};
const Range kRangeTextGlow{0.0f, 4.0f};
const Range kRangeInset{0.0f, 0.5f};
const Range kRangeTeamColoringStrength{0.0f, 1.0f};

void ReadFloat(const JsonRef& obj, const char* key, float* out,
               const Range& range) {
  if (auto val = obj[key].as_double()) {
    *out = std::clamp(static_cast<float>(*val), range.lo, range.hi);
  }
}

// As ReadFloat, for values whose absence means something (left unset).
void ReadOptionalFloat(const JsonRef& obj, const char* key,
                       std::optional<float>* out, const Range& range) {
  if (auto val = obj[key].as_double()) {
    *out = std::clamp(static_cast<float>(*val), range.lo, range.hi);
  }
}

// An [r, g, b] or [r, g, b, a] color (``count`` elements); left as is
// if absent or the wrong size.
void ReadColor(const JsonRef& obj, const char* key, float* out, size_t count) {
  JsonRef arr = obj[key];
  if (!arr.is_array() || arr.size() != count) {
    return;
  }
  for (size_t i = 0; i < count; ++i) {
    if (auto val = arr[i].as_double()) {
      const Range& range = i < 3 ? kRangeColor : kRangeAlpha;
      out[i] = std::clamp(static_cast<float>(*val), range.lo, range.hi);
    }
  }
}

auto ReadCapsule(const JsonRef& tier) -> std::optional<CapsuleNameDef> {
  CapsuleNameDef d;
  ReadFloat(tier, "r", &d.radius, kRangeRadius);
  ReadColor(tier, "cc", d.capsule_color, 4);
  ReadFloat(tier, "ce", &d.capsule_edge, kRangeEdge);
  ReadPackageAssetRef(tier, "ct", &d.capsule_texture);
  if (JsonRef insets = tier["cx"]; insets.is_array() && insets.size() == 2) {
    for (size_t i = 0; i < 2; ++i) {
      if (auto val = insets[i].as_double()) {
        d.capsule_insets[i] = std::clamp(static_cast<float>(*val),
                                         kRangeInset.lo, kRangeInset.hi);
      }
    }
  }
  if (auto fill = tier["cf"].as_double()) {
    d.capsule_tile = (*fill == 1.0);
  }
  // Override targets, by name; names this build doesn't know are
  // ignored (later ones degrade to not taking the override).
  if (JsonRef targets = tier["ot"]; targets.is_array()) {
    d.override_text = false;
    for (size_t i = 0; i < targets.size(); ++i) {
      auto target = targets[i].as_string();
      if (!target) {
        continue;
      }
      if (*target == "t") {
        d.override_text = true;
      } else if (*target == "c") {
        d.override_capsule = true;
      } else if (*target == "t1") {
        d.override_tints[0] = true;
      } else if (*target == "t2") {
        d.override_tints[1] = true;
      } else if (*target == "t3") {
        d.override_tints[2] = true;
      } else if (*target == "i") {
        d.override_icon = true;
      }
    }
  }
  ReadPackageAssetRef(tier, "ctt", &d.capsule_tint_texture);
  ReadColor(tier, "ctc1", d.capsule_tint_colors[0], 3);
  ReadColor(tier, "ctc2", d.capsule_tint_colors[1], 3);
  ReadColor(tier, "ctc3", d.capsule_tint_colors[2], 3);
  ReadPackageAssetRef(tier, "it", &d.icon_texture);
  ReadColor(tier, "ic", d.icon_color, 4);
  ReadFloat(tier, "ccs", &d.capsule_team_coloring_strength,
            kRangeTeamColoringStrength);
  ReadFloat(tier, "ctcs1", &d.capsule_tint_team_coloring_strengths[0],
            kRangeTeamColoringStrength);
  ReadFloat(tier, "ctcs2", &d.capsule_tint_team_coloring_strengths[1],
            kRangeTeamColoringStrength);
  ReadFloat(tier, "ctcs3", &d.capsule_tint_team_coloring_strengths[2],
            kRangeTeamColoringStrength);
  ReadFloat(tier, "ics", &d.icon_team_coloring_strength,
            kRangeTeamColoringStrength);
  ReadFloat(tier, "is", &d.icon_scale, kRangeIconScale);
  ReadFloat(tier, "ie", &d.icon_edge, kRangeIconEdge);
  ReadOptionalFloat(tier, "ti", &d.text_inset, kRangeTextInset);
  ReadFloat(tier, "tg", &d.text_glow, kRangeTextGlow);
  ReadPackageManifest(tier, &d.packages, &d.domain_digest);
  for (const auto* ref :
       {&d.capsule_texture, &d.capsule_tint_texture, &d.icon_texture}) {
    if (ref->index >= 0 && d.packages.empty()) {
      BA_LOG_ONCE(LogName::kBa, LogLevel::kError,
                  "Name capsule has indexed refs but no package manifest;"
                  " drawing the plain name.");
      return std::nullopt;
    }
  }
  return d;
}

}  // namespace

auto NameDef::Parse(const JsonRef& block) -> std::optional<NameDef> {
  if (!block.is_object()) {
    return std::nullopt;
  }
  JsonRef basic = block["b"];
  if (!basic.is_object()) {
    BA_LOG_ONCE(LogName::kBa, LogLevel::kWarning,
                "Name block has no basic tier; ignoring it.");
    return std::nullopt;
  }
  auto text = basic["t"].as_string();
  if (!text || text->empty()) {
    BA_LOG_ONCE(LogName::kBa, LogLevel::kError,
                "Name block has no text; ignoring it.");
    return std::nullopt;
  }
  NameDef d;
  d.basic.text = std::string(*text);
  ReadColor(basic, "c", d.basic.color, 3);
  if (JsonRef capsule = block["c"]; capsule.is_object()) {
    d.capsule = ReadCapsule(capsule);
  }
  if (JsonRef glyph = block["g"]; glyph.is_object()) {
    auto icon = glyph["i"].as_string();
    if (icon && !icon->empty()) {
      d.glyph = GlyphNameDef{std::string(*icon)};
    } else {
      BA_LOG_ONCE(LogName::kBa, LogLevel::kWarning,
                  "Name glyph tier has no icon; ignoring it.");
    }
  }
  return d;
}

}  // namespace ballistica::base
