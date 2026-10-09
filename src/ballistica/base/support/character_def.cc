// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/support/character_def.h"

#include <algorithm>
#include <cmath>
#include <memory>
#include <string>
#include <utility>
#include <vector>

#include "ballistica/base/assets/asset_package_registry.h"
#include "ballistica/base/assets/assets.h"
#include "ballistica/base/base.h"
#include "ballistica/base/generated/character_ranges.h"
#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging.h"
#include "ballistica/core/logging/logging_macros.h"
#include "ballistica/shared/generic/json_facade.h"

namespace ballistica::base {

// The allowed span of every numeric field (the kCharacterRange*
// constants) comes from generated/character_ranges.h, which is
// generated from the one table the cloud and the authoring tools also
// read (tools/bacommon/characterranges.py). Change a span there, never
// here.
namespace {

void ReadFloat(const JsonRef& obj, const char* key, float* out,
               const CharacterRange& range) {
  if (auto val = obj[key].as_double()) {
    *out = std::clamp(static_cast<float>(*val), range.lo, range.hi);
  }
}

// Returns whether the key held a 3-element array (and so was applied).
auto ReadFloat3(const JsonRef& obj, const char* key, float* out,
                const CharacterRange& range) -> bool {
  JsonRef arr = obj[key];
  if (!arr.is_array() || arr.size() != 3) {
    return false;
  }
  for (size_t i = 0; i < 3; ++i) {
    if (auto val = arr[i].as_double()) {
      out[i] = std::clamp(static_cast<float>(*val), range.lo, range.hi);
    }
  }
  return true;
}

// The team-coloring strengths for the two highlights: keys are
// ``prefix`` + 'hls' / 'hl2s' + ``suffix``. Left as is if absent.
void ReadTeamColoringStrengths(const JsonRef& obj, const std::string& prefix,
                               const std::string& suffix, float* highlight,
                               float* highlight2) {
  ReadFloat(obj, (prefix + "hls" + suffix).c_str(), highlight,
            kCharacterRangeTeamColoringStrength);
  ReadFloat(obj, (prefix + "hl2s" + suffix).c_str(), highlight2,
            kCharacterRangeTeamColoringStrength);
}

// A piece's optional tint colors: keys are ``prefix`` + 'cl' / 'hl' /
// 'hl2' + ``suffix`` (the base color keys, wrapped), plus its
// team-coloring strengths.
void ReadTint(const JsonRef& obj, const std::string& prefix,
              const std::string& suffix, CharacterTintDef* out) {
  ReadTeamColoringStrengths(obj, prefix, suffix,
                            &out->highlight_team_coloring_strength,
                            &out->highlight2_team_coloring_strength);
  out->has_color = ReadFloat3(obj, (prefix + "cl" + suffix).c_str(), out->color,
                              kCharacterRangeColor);
  out->has_highlight = ReadFloat3(obj, (prefix + "hl" + suffix).c_str(),
                                  out->highlight, kCharacterRangeHighlight);
  out->has_highlight2 = ReadFloat3(obj, (prefix + "hl2" + suffix).c_str(),
                                   out->highlight2, kCharacterRangeHighlight);
}

void ReadBool(const JsonRef& obj, const char* key, bool* out) {
  if (auto val = obj[key].as_bool()) {
    *out = *val;
  }
}

// Wire values 'r'/'l'/'n'; anything unrecognized (including a future
// style this build predates) falls back to kRegular by design.
void ReadEyeStyle(const JsonRef& obj, const char* key, CharacterEyeStyle* out) {
  auto val = obj[key].as_string();
  if (!val) {
    return;
  }
  if (*val == "l") {
    *out = CharacterEyeStyle::kLidless;
  } else if (*val == "n") {
    *out = CharacterEyeStyle::kNone;
  } else {
    *out = CharacterEyeStyle::kRegular;
  }
}

// Attachment calibration scalars get a one-time warning on
// out-of-range values (unlike the silently-clamping numeric fields):
// the dial's span is its whole range, and modders poking at
// definitions should learn they can't overdrive the springs.
void ReadAttachmentScalar(const JsonRef& obj, const char* key, float* out,
                          const CharacterRange& range) {
  auto val = obj[key].as_double();
  if (!val) {
    return;
  }
  auto fval = static_cast<float>(*val);
  float lo = range.lo;
  float hi = range.hi;
  if (fval < lo || fval > hi) {
    BA_LOG_ONCE(LogName::kBa, LogLevel::kWarning,
                "Character attachment scalar '" + std::string(key)
                    + "' value " + std::to_string(fval)
                    + " is outside its range; clamping. These scalars"
                      " cannot overdrive attachment springs or bends.");
  }
  *out = std::clamp(fval, lo, hi);
}
// Per target body; matches MAX_ATTACHMENTS in the server schema.
const size_t kMaxAttachments{10};

// Segment counts are fixed per attachment type (see
// CharacterAttachmentType); malformed entries drop the attachment.
auto AttachmentSegmentCount(CharacterAttachmentType type) -> size_t {
  switch (type) {
    case CharacterAttachmentType::kLegacyPonytail2:
    case CharacterAttachmentType::kAntenna2:
      return 2;
    case CharacterAttachmentType::kAntenna3:
      return 3;
    case CharacterAttachmentType::kAntenna4:
      return 4;
    default:
      return 1;
  }
}

// Rotation matrix from a normalized (w, x, y, z) quaternion.
auto MatrixFromQuaternion(const float q[4]) -> Matrix44f {
  float w = q[0], x = q[1], y = q[2], z = q[3];
  Matrix44f m{kMatrix44fIdentity};
  m.m[0] = 1.0f - 2.0f * (y * y + z * z);
  m.m[1] = 2.0f * (x * y + z * w);
  m.m[2] = 2.0f * (x * z - y * w);
  m.m[4] = 2.0f * (x * y - z * w);
  m.m[5] = 1.0f - 2.0f * (x * x + z * z);
  m.m[6] = 2.0f * (y * z + x * w);
  m.m[8] = 2.0f * (x * z + y * w);
  m.m[9] = 2.0f * (y * z - x * w);
  m.m[10] = 1.0f - 2.0f * (x * x + y * y);
  return m;
}

// Parse a segment's optional draw offset. By length: 1 = uniform
// scale, 3 = xyz scale, 6 = scale + translate, 10 = scale + translate
// + (w, x, y, z) rotation, 16 = full column-major matrix. The short
// forms compose scale, then rotate, then translate. Any other length
// (a form this build predates) leaves the identity in place rather
// than dropping the attachment.
void ReadSegmentOffset(const JsonRef& seg,
                       BasicSpazDef::AttachmentSegmentDef* sdef) {
  JsonRef arr = seg["o"];
  if (!arr.is_array()) {
    return;
  }
  size_t n = arr.size();
  if (n != 1 && n != 3 && n != 6 && n != 10 && n != 16) {
    return;
  }
  float vals[16];
  for (size_t i = 0; i < n; ++i) {
    auto val = arr[i].as_double();
    if (!val || !std::isfinite(*val)) {
      return;
    }
    vals[i] = static_cast<float>(*val);
  }
  Matrix44f offset{kMatrix44fIdentity};
  if (n == 16) {
    for (int i = 0; i < 16; ++i) {
      offset.m[i] = vals[i];
    }
  } else {
    Vector3f scale = (n == 1) ? Vector3f{vals[0], vals[0], vals[0]}
                              : Vector3f{vals[0], vals[1], vals[2]};
    // Matrix44f's operator* applies its left operand first.
    offset = Matrix44fScale(scale);
    if (n == 10) {
      float q[4] = {vals[6], vals[7], vals[8], vals[9]};
      float norm =
          std::sqrt(q[0] * q[0] + q[1] * q[1] + q[2] * q[2] + q[3] * q[3]);
      if (norm > 0.001f) {
        for (float& component : q) {
          component /= norm;
        }
        offset = offset * MatrixFromQuaternion(q);
      }
    }
    if (n >= 6) {
      offset = offset * Matrix44fTranslate(vals[3], vals[4], vals[5]);
    }
  }
  sdef->offset = offset;
  sdef->has_offset = true;
}

// Parse one target's attachment list. Unrecognized types (a future
// kind this build predates) and malformed entries are dropped
// attachment-by-attachment by design.
void ReadAttachmentList(const JsonRef& arr, bool static_only,
                        std::vector<BasicSpazDef::AttachmentDef>* out) {
  out->clear();
  if (!arr.is_array()) {
    return;
  }
  for (size_t i = 0; i < arr.size() && out->size() < kMaxAttachments; ++i) {
    JsonRef entry = arr[i];
    if (!entry.is_object()) {
      continue;
    }
    BasicSpazDef::AttachmentDef adef;
    auto type = entry["t"].as_string();
    if (!type) {
      continue;
    }
    if (*type == "lt") {
      adef.type = CharacterAttachmentType::kLegacyTuftLarge;
    } else if (*type == "mt") {
      adef.type = CharacterAttachmentType::kLegacyTuftMedium;
    } else if (*type == "st") {
      adef.type = CharacterAttachmentType::kLegacyTuftSmall;
    } else if (*type == "pt") {
      adef.type = CharacterAttachmentType::kLegacyPonytail2;
    } else if (*type == "an") {
      adef.type = CharacterAttachmentType::kAntenna;
    } else if (*type == "a2") {
      adef.type = CharacterAttachmentType::kAntenna2;
    } else if (*type == "a3") {
      adef.type = CharacterAttachmentType::kAntenna3;
    } else if (*type == "a4") {
      adef.type = CharacterAttachmentType::kAntenna4;
    } else if (*type == "fx") {
      adef.type = CharacterAttachmentType::kStatic;
    } else {
      continue;
    }
    // Limb targets take static attachments only (see
    // CharacterAttachTarget).
    if (static_only && adef.type != CharacterAttachmentType::kStatic) {
      continue;
    }
    ReadFloat3(entry, "p", adef.position, kCharacterRangeAttachmentPosition);
    ReadAttachmentScalar(entry, "k", &adef.stiffness,
                         kCharacterRangeAttachmentStiffness);
    ReadAttachmentScalar(entry, "d", &adef.damping,
                         kCharacterRangeAttachmentDamping);
    ReadAttachmentScalar(entry, "dg", &adef.drag,
                         kCharacterRangeAttachmentDrag);
    ReadAttachmentScalar(entry, "c", &adef.curl, kCharacterRangeAttachmentCurl);
    ReadAttachmentScalar(entry, "l", &adef.length,
                         kCharacterRangeAttachmentLength);
    ReadAttachmentScalar(entry, "r", &adef.radius,
                         kCharacterRangeAttachmentRadius);
    ReadAttachmentScalar(entry, "cc", &adef.curl_change,
                         kCharacterRangeAttachmentCurlChange);
    ReadAttachmentScalar(entry, "lc", &adef.length_change,
                         kCharacterRangeAttachmentLengthChange);
    ReadAttachmentScalar(entry, "rc", &adef.radius_change,
                         kCharacterRangeAttachmentRadiusChange);
    ReadAttachmentScalar(entry, "kc", &adef.stiffness_change,
                         kCharacterRangeAttachmentStiffnessChange);
    ReadAttachmentScalar(entry, "dc", &adef.damping_change,
                         kCharacterRangeAttachmentDampingChange);
    JsonRef quat = entry["q"];
    if (quat.is_array() && quat.size() == 4) {
      for (size_t qi = 0; qi < 4; ++qi) {
        if (auto val = quat[qi].as_double()) {
          adef.rotation[qi] = static_cast<float>(*val);
        }
      }
      // Normalize (identically on every peer; sim state).
      float norm = std::sqrt(adef.rotation[0] * adef.rotation[0]
                             + adef.rotation[1] * adef.rotation[1]
                             + adef.rotation[2] * adef.rotation[2]
                             + adef.rotation[3] * adef.rotation[3]);
      if (norm < 0.001f) {
        adef.rotation[0] = 1.0f;
        adef.rotation[1] = adef.rotation[2] = adef.rotation[3] = 0.0f;
      } else {
        for (float& component : adef.rotation) {
          component /= norm;
        }
      }
    }
    JsonRef segs = entry["s"];
    if (!segs.is_array() || segs.size() != AttachmentSegmentCount(adef.type)) {
      continue;
    }
    bool segs_ok = true;
    for (size_t si = 0; si < segs.size(); ++si) {
      BasicSpazDef::AttachmentSegmentDef sdef;
      JsonRef seg = segs[si];
      if (!seg.is_object() || !ReadPackageAssetRef(seg, "m", &sdef.mesh)) {
        segs_ok = false;
        break;
      }
      ReadPackageAssetRef(seg, "t", &sdef.texture);
      ReadPackageAssetRef(seg, "tm", &sdef.tint_texture);
      ReadTint(seg, "", "", &sdef.tint);
      ReadSegmentOffset(seg, &sdef);
      adef.segments.push_back(std::move(sdef));
    }
    if (!segs_ok) {
      continue;
    }
    out->push_back(std::move(adef));
  }
  if (arr.size() > kMaxAttachments) {
    BA_LOG_ONCE(LogName::kBa, LogLevel::kDebug,
                "Character has " + std::to_string(arr.size())
                    + " attachments on one body; only the first "
                    + std::to_string(kMaxAttachments) + " are used.");
  }
}

// Parse the optional attachments dict (target key -> list). Only the
// targets this build knows are read; anything else is ignored.
// (Limb target keys are the part's mesh-key suffix, 'l'-prefixed for
// the left-side ones.)
void ReadAttachments(const JsonRef& obj, const char* key,
                     std::vector<BasicSpazDef::AttachmentDef> (
                         &out)[kCharacterAttachTargetCount],
                     bool (&present)[kCharacterAttachTargetCount]) {
  for (auto& list : out) {
    list.clear();
  }
  for (auto& val : present) {
    val = false;
  }
  JsonRef dict = obj[key];
  if (!dict.is_object()) {
    return;
  }
  static const struct {
    const char* key;
    CharacterAttachTarget target;
  } kTargets[] = {
      {"h", CharacterAttachTarget::kHead},
      {"t", CharacterAttachTarget::kTorso},
      {"p", CharacterAttachTarget::kPelvis},
      {"ua", CharacterAttachTarget::kUpperArm},
      {"fa", CharacterAttachTarget::kForearm},
      {"hn", CharacterAttachTarget::kHand},
      {"ul", CharacterAttachTarget::kUpperLeg},
      {"ll", CharacterAttachTarget::kLowerLeg},
      {"to", CharacterAttachTarget::kToes},
      {"lua", CharacterAttachTarget::kLeftUpperArm},
      {"lfa", CharacterAttachTarget::kLeftForearm},
      {"lhn", CharacterAttachTarget::kLeftHand},
      {"lul", CharacterAttachTarget::kLeftUpperLeg},
      {"lll", CharacterAttachTarget::kLeftLowerLeg},
      {"lto", CharacterAttachTarget::kLeftToes},
  };
  for (const auto& entry : kTargets) {
    int ti = static_cast<int>(entry.target);
    JsonRef list = dict[entry.key];
    present[ti] = list.is_array();
    ReadAttachmentList(list, ti >= kCharacterRigAnchorCount, &out[ti]);
  }
}

// The basic tier of a component block: required whenever the block
// is present. Null when the block is absent (normal) or carries no
// basic tier (a malformed or future-only block; logged once since the
// schema says basic always accompanies richer tiers).
auto BasicTier(const JsonRef& block, const char* what) -> JsonRef {
  if (!block.is_object()) {
    return block;
  }
  JsonRef basic = block["b"];
  if (!basic.is_object()) {
    BA_LOG_ONCE(LogName::kBa, LogLevel::kWarning,
                std::string("Character ") + what
                    + " block has no basic tier; ignoring it.");
  }
  return basic;
}

auto ReadIcon(const JsonRef& basic, BasicIconDef* out) -> bool {
  BasicIconDef d;
  ReadPackageManifest(basic, &d.packages, &d.domain_digest);
  if (!ReadPackageAssetRef(basic, "tx", &d.texture)
      || !ReadPackageAssetRef(basic, "cm", &d.color_mask_texture)) {
    BA_LOG_ONCE(LogName::kBa, LogLevel::kError,
                "Character icon block is missing asset refs; using standin.");
    return false;
  }
  ReadFloat3(basic, "cl", d.color, kCharacterRangeColor);
  ReadFloat3(basic, "hl", d.highlight, kCharacterRangeHighlight);
  ReadFloat3(basic, "hl2", d.highlight2, kCharacterRangeHighlight);
  ReadTeamColoringStrengths(basic, "", "", &d.highlight_team_coloring_strength,
                            &d.highlight2_team_coloring_strength);
  *out = std::move(d);
  return true;
}

// Wire-key suffix per CharacterBodyPart (as in each part's mesh key:
// 'mh', 'mua', ...), and the first part that has a left/right pair.
const char* const kBodyPartKeySuffixes[kCharacterBodyPartCount] = {
    "h", "t", "p", "ua", "fa", "hn", "ul", "ll", "to"};
const int kFirstPairedBodyPart = static_cast<int>(CharacterBodyPart::kUpperArm);

auto ReadSpaz(const JsonRef& basic, BasicSpazDef* out) -> bool {
  BasicSpazDef d;
  ReadPackageManifest(basic, &d.packages, &d.domain_digest);

  // Required asset refs; a definition missing any of these can't be
  // drawn in this form.
  bool ok = ReadPackageAssetRef(basic, "ct", &d.color_texture)
            && ReadPackageAssetRef(basic, "cm", &d.color_mask_texture)
            && ReadPackageAssetRef(basic, "mh", &d.head_mesh)
            && ReadPackageAssetRef(basic, "mt", &d.torso_mesh)
            && ReadPackageAssetRef(basic, "mua", &d.upper_arm_mesh)
            && ReadPackageAssetRef(basic, "mul", &d.upper_leg_mesh)
            && ReadPackageAssetRef(basic, "mll", &d.lower_leg_mesh)
            && ReadPackageAssetRef(basic, "mto", &d.toes_mesh);
  if (!ok) {
    BA_LOG_ONCE(LogName::kBa, LogLevel::kError,
                "Character spaz block is missing asset refs; using standin.");
    return false;
  }
  // Optional parts, absent = never drawn: forearm/hand (a
  // flipper-style character's upper-arm mesh is the whole limb) and
  // pelvis (big round characters historically shipped centimeter-scale
  // dummy pelvises just to fill the slot).
  ReadPackageAssetRef(basic, "mfa", &d.forearm_mesh);
  ReadPackageAssetRef(basic, "mhn", &d.hand_mesh);
  ReadPackageAssetRef(basic, "mp", &d.pelvis_mesh);
  // Optional wings: mesh presence is what makes a character winged;
  // the texture alone does nothing.
  ReadPackageAssetRef(basic, "mw", &d.wing_mesh);
  ReadPackageAssetRef(basic, "tw", &d.wing_texture);
  ReadPackageAssetRef(basic, "wm", &d.wing_tint_texture);
  ReadPackageAssetRef(basic, "lmw", &d.wing_left_mesh);
  ReadPackageAssetRef(basic, "ltw", &d.wing_left_texture);
  ReadPackageAssetRef(basic, "lwm", &d.wing_left_tint_texture);
  ReadTint(basic, "", "w", &d.wing_tint);
  ReadTint(basic, "l", "w", &d.wing_left_tint);
  // Optional per-part looks. Keys are a prefix plus the part's suffix
  // (the one its mesh key uses): 't' texture, 'tm' tint mask, and
  // 'cl' / 'hl' / 'hl2' tint colors; for paired parts 'lm' / 'lt' /
  // 'ltm' and 'lcl' / 'lhl' / 'lhl2' are the left side's mesh,
  // texture, tint mask and tint colors.
  for (int i = 0; i < kCharacterBodyPartCount; ++i) {
    auto& look = d.part_looks[i];
    const std::string suffix = kBodyPartKeySuffixes[i];
    ReadPackageAssetRef(basic, ("t" + suffix).c_str(), &look.texture);
    ReadPackageAssetRef(basic, ("tm" + suffix).c_str(), &look.tint_texture);
    ReadTint(basic, "", suffix, &look.tint);
    if (i >= kFirstPairedBodyPart) {
      ReadTint(basic, "l", suffix, &look.left_tint);
      ReadPackageAssetRef(basic, ("lm" + suffix).c_str(), &look.left_mesh);
      ReadPackageAssetRef(basic, ("lt" + suffix).c_str(), &look.left_texture);
      ReadPackageAssetRef(basic, ("ltm" + suffix).c_str(),
                          &look.left_tint_texture);
    }
  }
  ReadAttachments(basic, "at", d.attachments, d.attachment_target_present);

  ReadPackageAssetRefs(basic, "sj", &d.jump_sounds);
  ReadPackageAssetRefs(basic, "sa", &d.attack_sounds);
  ReadPackageAssetRefs(basic, "si", &d.impact_sounds);
  ReadPackageAssetRefs(basic, "sd", &d.death_sounds);
  ReadPackageAssetRefs(basic, "sp", &d.pickup_sounds);
  ReadPackageAssetRefs(basic, "sf", &d.fall_sounds);

  d.has_color = ReadFloat3(basic, "cl", d.color, kCharacterRangeColor);
  ReadFloat3(basic, "hl", d.highlight, kCharacterRangeHighlight);
  ReadFloat3(basic, "hl2", d.highlight2, kCharacterRangeHighlight);
  ReadTeamColoringStrengths(basic, "", "", &d.highlight_team_coloring_strength,
                            &d.highlight2_team_coloring_strength);

  ReadFloat(basic, "tr", &d.torso_radius, kCharacterRangeTorsoRadius);
  ReadFloat3(basic, "so", d.shoulder_offset, kCharacterRangeShoulderOffset);
  ReadFloat(basic, "lt", &d.thigh_radius, kCharacterRangeThighRadius);
  ReadFloat(basic, "la", &d.ankle_radius, kCharacterRangeAnkleRadius);
  ReadFloat(basic, "ss", &d.step_separation, kCharacterRangeStepSeparation);
  ReadFloat(basic, "ia", &d.idle_arm_stiffness,
            kCharacterRangeIdleArmStiffness);
  ReadFloat(basic, "aw", &d.arm_swing, kCharacterRangeArmSwing);
  ReadFloat(basic, "iw", &d.idle_sway, kCharacterRangeIdleSway);

  ReadEyeStyle(basic, "le", &d.eye_style_left);
  ReadEyeStyle(basic, "re", &d.eye_style_right);
  ReadFloat(basic, "es", &d.eye_scale, kCharacterRangeEyeScale);
  ReadFloat3(basic, "eo", d.eye_offset, kCharacterRangeEyeOffset);
  ReadFloat3(basic, "ec", d.eye_color, kCharacterRangeEyeColor);
  ReadFloat3(basic, "eb", d.eyeball_color, kCharacterRangeEyeballColor);
  ReadFloat3(basic, "lc", d.eyelid_color, kCharacterRangeEyelidColor);
  ReadFloat(basic, "ln", &d.eyelid_angle, kCharacterRangeEyelidAngle);
  ReadFloat(basic, "rs", &d.reflection_scale, kCharacterRangeReflectionScale);
  ReadBool(basic, "fl", &d.flippers);

  *out = std::move(d);
  return true;
}

}  // namespace

CharacterDef::CharacterDef(std::string json, Form form)
    : form_(form), json_(std::move(json)) {
  // Parse only. Media (listing decode + asset handles) loads on the
  // first RetryMedia() from something that displays us: a lobby
  // builds a definition for every cloud profile of every joining
  // player but shows one per player, so paying for media up front
  // would be N x M resolves on the logic thread for N loads' worth
  // of display (character-skins.md, lazy media).
  assert(g_base->InLogicThread());
  Parse_();
}

void CharacterDef::Parse_() {
  auto doc = JsonDoc::Parse(json_);
  if (!doc || !doc->root().is_object()) {
    BA_LOG_ONCE(LogName::kBa, LogLevel::kError,
                "Character json is not an object; using standin.");
    return;
  }
  JsonRef root = doc->root();

  // An empty block is a deliberate request for the standin (e.g. a
  // viewer showing the standard spaz), not malformed input.
  if (root.size() == 0) {
    return;
  }

  // The part's block on its own; each read from its basic tier 'b'.
  switch (form_) {
    case Form::kIcon: {
      JsonRef icon = BasicTier(root, "icon");
      if (icon.is_object()) {
        has_icon_ = ReadIcon(icon, &icon_);
      }
      break;
    }
    case Form::kSpaz: {
      JsonRef spaz = BasicTier(root, "spaz");
      if (spaz.is_object()) {
        has_spaz_ = ReadSpaz(spaz, &spaz_);
      }
      break;
    }
  }
}

auto CharacterDef::RetryMedia() -> bool {
  assert(g_base->InLogicThread());
  if (has_icon_) {
    LoadIconMedia_();
  }
  if (has_spaz_) {
    LoadSpazMedia_();
  }
  bool changed{};
  changed |= icon_block_.CheckPending();
  changed |= spaz_block_.CheckPending();
  return changed;
}

void CharacterDef::LoadIconMedia_() {
  if (icon_block_.ready() || icon_block_.pending()) {
    return;
  }
  BasicIconDef& d = icon_;
  std::vector<MediaBlock::IndexedRef> indexed;
  MediaBlock::NoteIndexed(&d.texture, "textures/", &indexed);
  MediaBlock::NoteIndexed(&d.color_mask_texture, "textures/", &indexed);
  icon_block_.Load(d.packages, d.domain_digest, indexed,
                   {&d.texture, &d.color_mask_texture},
                   [this, &d](MediaGetter* get) {
                     BasicIconMedia m;
                     m.texture = get->Texture(d.texture);
                     m.color_mask_texture = get->Texture(d.color_mask_texture);
                     icon_media_ = std::move(m);
                   });
}

void CharacterDef::LoadSpazMedia_() {
  if (spaz_block_.ready() || spaz_block_.pending()) {
    return;
  }
  BasicSpazDef& d = spaz_;
  auto note = [](CharacterAssetRef* ref, const char* prefix,
                 std::vector<MediaBlock::IndexedRef>* out) {
    MediaBlock::NoteIndexed(ref, prefix, out);
  };
  std::vector<MediaBlock::IndexedRef> indexed;
  note(&d.color_texture, "textures/", &indexed);
  note(&d.color_mask_texture, "textures/", &indexed);
  note(&d.wing_texture, "textures/", &indexed);
  note(&d.wing_tint_texture, "textures/", &indexed);
  note(&d.head_mesh, "meshes/", &indexed);
  note(&d.torso_mesh, "meshes/", &indexed);
  note(&d.pelvis_mesh, "meshes/", &indexed);
  note(&d.upper_arm_mesh, "meshes/", &indexed);
  note(&d.forearm_mesh, "meshes/", &indexed);
  note(&d.hand_mesh, "meshes/", &indexed);
  note(&d.upper_leg_mesh, "meshes/", &indexed);
  note(&d.lower_leg_mesh, "meshes/", &indexed);
  note(&d.toes_mesh, "meshes/", &indexed);
  note(&d.wing_mesh, "meshes/", &indexed);
  note(&d.wing_left_mesh, "meshes/", &indexed);
  note(&d.wing_left_texture, "textures/", &indexed);
  note(&d.wing_left_tint_texture, "textures/", &indexed);
  for (auto& look : d.part_looks) {
    note(&look.texture, "textures/", &indexed);
    note(&look.tint_texture, "textures/", &indexed);
    note(&look.left_mesh, "meshes/", &indexed);
    note(&look.left_texture, "textures/", &indexed);
    note(&look.left_tint_texture, "textures/", &indexed);
  }
  for (auto& list : d.attachments) {
    for (auto& attachment : list) {
      for (auto& seg : attachment.segments) {
        note(&seg.mesh, "meshes/", &indexed);
        note(&seg.texture, "textures/", &indexed);
        note(&seg.tint_texture, "textures/", &indexed);
      }
    }
  }
  for (auto* list : {&d.jump_sounds, &d.attack_sounds, &d.impact_sounds,
                     &d.death_sounds, &d.pickup_sounds, &d.fall_sounds}) {
    for (auto& ref : *list) {
      note(&ref, "audio/", &indexed);
    }
  }

  // The required list holds pointers, and the block resolves indices
  // before checking registration, so required refs are checked by
  // their resolved names. (Optional parts in indexed form, name still
  // empty here, are left out -- their packages are manifest packages,
  // which the index resolve already requires to be registered.)
  spaz_block_.Load(d.packages, d.domain_digest, indexed, SpazRequiredRefs_(),
                   [this, &d](MediaGetter* get) {
                     spaz_media_ = LoadSpazMediaWith_(d, get);
                   });
}

auto CharacterDef::SpazRequiredRefs_() const
    -> std::vector<const CharacterAssetRef*> {
  const BasicSpazDef& d = spaz_;
  std::vector<const CharacterAssetRef*> refs = {
      &d.color_texture,  &d.color_mask_texture, &d.head_mesh,
      &d.torso_mesh,     &d.upper_arm_mesh,     &d.upper_leg_mesh,
      &d.lower_leg_mesh, &d.toes_mesh};
  // Optional parts join the check only when present.
  for (const auto* opt :
       {&d.forearm_mesh, &d.hand_mesh, &d.pelvis_mesh, &d.wing_mesh,
        &d.wing_texture, &d.wing_tint_texture, &d.wing_left_mesh,
        &d.wing_left_texture, &d.wing_left_tint_texture}) {
    if (!opt->name.empty()) {
      refs.push_back(opt);
    }
  }
  for (const auto& look : d.part_looks) {
    for (const auto* opt : {&look.texture, &look.tint_texture, &look.left_mesh,
                            &look.left_texture, &look.left_tint_texture}) {
      if (!opt->name.empty()) {
        refs.push_back(opt);
      }
    }
  }
  for (const auto& list : d.attachments) {
    for (const auto& attachment : list) {
      for (const auto& seg : attachment.segments) {
        for (const auto* opt : {&seg.mesh, &seg.texture, &seg.tint_texture}) {
          if (!opt->name.empty()) {
            refs.push_back(opt);
          }
        }
      }
    }
  }
  for (const auto* list : {&d.jump_sounds, &d.attack_sounds, &d.impact_sounds,
                           &d.death_sounds, &d.pickup_sounds, &d.fall_sounds}) {
    for (const auto& ref : *list) {
      refs.push_back(&ref);
    }
  }
  return refs;
}

auto CharacterDef::LoadSpazMediaWith_(const BasicSpazDef& d, MediaGetter* get)
    -> BasicSpazMedia {
  BasicSpazMedia m;
  m.color_texture = get->Texture(d.color_texture);
  m.color_mask_texture = get->Texture(d.color_mask_texture);
  m.head_mesh = get->Mesh(d.head_mesh);
  m.torso_mesh = get->Mesh(d.torso_mesh);
  if (!d.pelvis_mesh.name.empty()) {
    m.pelvis_mesh = get->Mesh(d.pelvis_mesh);
  }
  m.upper_arm_mesh = get->Mesh(d.upper_arm_mesh);
  if (!d.forearm_mesh.name.empty()) {
    m.forearm_mesh = get->Mesh(d.forearm_mesh);
  }
  if (!d.hand_mesh.name.empty()) {
    m.hand_mesh = get->Mesh(d.hand_mesh);
  }
  m.upper_leg_mesh = get->Mesh(d.upper_leg_mesh);
  m.lower_leg_mesh = get->Mesh(d.lower_leg_mesh);
  m.toes_mesh = get->Mesh(d.toes_mesh);
  if (!d.wing_mesh.name.empty()) {
    m.wing_mesh = get->Mesh(d.wing_mesh);
  }
  if (!d.wing_texture.name.empty()) {
    m.wing_texture = get->Texture(d.wing_texture);
  }
  if (!d.wing_tint_texture.name.empty()) {
    m.wing_tint_texture = get->Texture(d.wing_tint_texture);
  }
  auto opt_texture = [get](const CharacterAssetRef& ref,
                           Object::Ref<TextureAsset>* out) {
    if (!ref.name.empty()) {
      *out = get->Texture(ref);
    }
  };
  auto opt_mesh = [get](const CharacterAssetRef& ref,
                        Object::Ref<MeshAsset>* out) {
    if (!ref.name.empty()) {
      *out = get->Mesh(ref);
    }
  };
  opt_mesh(d.wing_left_mesh, &m.wing_left_mesh);
  opt_texture(d.wing_left_texture, &m.wing_left_texture);
  opt_texture(d.wing_left_tint_texture, &m.wing_left_tint_texture);
  for (int i = 0; i < kCharacterBodyPartCount; ++i) {
    const auto& look = d.part_looks[i];
    auto& lmedia = m.part_looks[i];
    opt_texture(look.texture, &lmedia.texture);
    opt_texture(look.tint_texture, &lmedia.tint_texture);
    opt_mesh(look.left_mesh, &lmedia.left_mesh);
    opt_texture(look.left_texture, &lmedia.left_texture);
    opt_texture(look.left_tint_texture, &lmedia.left_tint_texture);
  }
  for (int ti = 0; ti < kCharacterAttachTargetCount; ++ti) {
    for (const auto& attachment : d.attachments[ti]) {
      BasicSpazMedia::AttachmentMedia amedia;
      for (const auto& seg : attachment.segments) {
        BasicSpazMedia::AttachmentSegmentMedia smedia;
        smedia.mesh = get->Mesh(seg.mesh);
        if (!seg.texture.name.empty()) {
          smedia.texture = get->Texture(seg.texture);
        }
        if (!seg.tint_texture.name.empty()) {
          smedia.tint_texture = get->Texture(seg.tint_texture);
        }
        amedia.segments.push_back(std::move(smedia));
      }
      m.attachments[ti].push_back(std::move(amedia));
    }
  }
  auto load_sounds = [get](const std::vector<CharacterAssetRef>& in,
                           std::vector<Object::Ref<SoundAsset>>* out) {
    for (const auto& ref : in) {
      out->push_back(get->Sound(ref));
    }
  };
  load_sounds(d.jump_sounds, &m.jump_sounds);
  load_sounds(d.attack_sounds, &m.attack_sounds);
  load_sounds(d.impact_sounds, &m.impact_sounds);
  load_sounds(d.death_sounds, &m.death_sounds);
  load_sounds(d.pickup_sounds, &m.pickup_sounds);
  load_sounds(d.fall_sounds, &m.fall_sounds);
  return m;
}

}  // namespace ballistica::base
