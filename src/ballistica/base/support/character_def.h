// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_SUPPORT_CHARACTER_DEF_H_
#define BALLISTICA_BASE_SUPPORT_CHARACTER_DEF_H_

#include <string>
#include <vector>

#include "ballistica/base/assets/asset.h"
#include "ballistica/base/assets/mesh_asset.h"
#include "ballistica/base/assets/sound_asset.h"
#include "ballistica/base/assets/texture_asset.h"
#include "ballistica/base/support/media_block.h"
#include "ballistica/shared/foundation/object.h"
#include "ballistica/shared/math/matrix44f.h"

namespace ballistica::base {

/// One asset reference in a character definition (see PackageAssetRef).
using CharacterAssetRef = PackageAssetRef;

/// How one of a character's eyes is drawn. Sides are the character's
/// own left/right (his left eye is on the viewer's right when he
/// faces the camera). Unrecognized wire values parse as kRegular so
/// new styles can be added server-side without breaking older
/// clients (they just draw a regular eye).
enum class CharacterEyeStyle : uint8_t {
  /// Eyeball plus a resting/blinking eyelid.
  kRegular,
  /// Bare eyeball; the lid appears only during blinks (bears,
  /// penguins).
  kLidless,
  /// No eye drawn at all (painted-on/eyeless heads, eyepatches).
  kNone,
};

/// A character's body parts, for per-part look overrides (see
/// BasicSpazDef::PartLookDef). The first three have no left/right
/// pair.
enum class CharacterBodyPart : uint8_t {
  kHead,
  kTorso,
  kPelvis,
  kUpperArm,
  kForearm,
  kHand,
  kUpperLeg,
  kLowerLeg,
  kToes,
};
constexpr int kCharacterBodyPartCount = 9;

/// Optional tint colors for one piece of a character (a body part, a
/// wing, an attachment segment): each present one stands in for the
/// character's own color / highlight / highlight2 on that piece.
///
/// A piece can likewise set how strongly team coloring tones its
/// highlights (Graphics::ToneForTeamColor's strength, 0-1; negative
/// = unset, the character's own applies), so a piece borrowed from
/// another character reacts to team colors as it does there.
struct CharacterTintDef {
  bool has_color{};
  bool has_highlight{};
  bool has_highlight2{};
  float color[3]{1.0f, 1.0f, 1.0f};
  float highlight[3]{0.5f, 0.5f, 0.5f};
  float highlight2[3]{1.0f, 1.0f, 1.0f};
  float highlight_team_coloring_strength{-1.0f};
  float highlight2_team_coloring_strength{-1.0f};
};

/// Body an attachment hangs off. Mirrors AttachTarget in bamaster
/// baserver/character.py. Unrecognized targets in a definition are
/// dropped silently on parse (new targets may arrive from newer
/// servers), so this enum is also the parse-time allow-list.
///
/// The first three are the core bodies, which are also the character
/// rig's anchors (kCharacterRigAnchorCount) and take any kind of
/// attachment. The limb targets take kStatic attachments only (other
/// kinds are dropped on parse; they would need rig support), drawn in
/// the limb's own frame wherever its mesh draws. A plain limb target
/// covers both sides, mirrored on the left exactly as the limb mesh
/// is; a kLeft* target, when present in a definition (even empty),
/// replaces it for the left side.
///
/// The wing targets are a pair of the same sort with no mesh of their
/// own: each is a frame at the torso that swings and flaps as a wing
/// does, and whatever is attached there is the wing. A character has
/// wings exactly when something is attached to one. Static only, and
/// sided as limbs are (kWing covers both, mirrored on the left;
/// kLeftWing, when present, replaces it there).
enum class CharacterAttachTarget : uint8_t {
  kHead,
  kTorso,
  kPelvis,
  kUpperArm,
  kForearm,
  kHand,
  kUpperLeg,
  kLowerLeg,
  kToes,
  kLeftUpperArm,
  kLeftForearm,
  kLeftHand,
  kLeftUpperLeg,
  kLeftLowerLeg,
  kLeftToes,
  // (After the limbs so those keep their part-index arithmetic.)
  kWing,
  kLeftWing,
  kLast = kLeftWing,
};
constexpr int kCharacterAttachTargetCount =
    static_cast<int>(CharacterAttachTarget::kLast) + 1;
constexpr int kCharacterRigAnchorCount = 3;
constexpr int kCharacterLimbAttachTargetCount = 6;

/// Kind of attachment hanging off one of a character's bodies. The
/// kind carries the whole physique -- capsule dims, mass, joint
/// anchors, spring stiffness/damping, and collision behavior are
/// fixed engine-side per kind (matching the legacy Zoe hair rig
/// exactly). A definition only chooses kinds, placements, and art.
/// Attachments are cosmetic: this client simulates them on its
/// bg-dynamics thread (never in the gameplay sim). The kLegacy* kinds
/// reproduce the classic Zoe hair rig and are discouraged for new
/// characters (off-center anchors give them a wonky twirl); prefer
/// the base-anchored kinds like kAntenna. kStatic has no bodies at
/// all: one mesh drawn rigidly on the target (place it with the
/// segment offset). Unrecognized kinds are dropped silently on parse.
/// Mirrors AttachmentType in bamaster baserver/character.py.
enum class CharacterAttachmentType : uint8_t {
  kLegacyTuftLarge,
  kLegacyTuftMedium,
  kLegacyTuftSmall,
  kLegacyPonytail2,
  kAntenna,
  kAntenna2,
  kAntenna3,
  kAntenna4,
  kStatic,
};

/// Basic tier of a character's icon component: what today's tinted
/// icon/mask image pairs draw. Self-contained -- it carries its own
/// color and highlight even though the spaz component does too -- so
/// an icon can be delivered and drawn with no other component present
/// (store items, embedded name/icon displays).
struct BasicIconDef {
  // Package manifest for indexed refs (see CharacterAssetRef), and the
  // producer's digest of the index domain it laid out over that
  // manifest (empty = none sent; the check is a guard, not a
  // requirement). See CharacterDef for the mismatch rule.
  std::vector<std::string> packages;
  std::string domain_digest;
  CharacterAssetRef texture;
  CharacterAssetRef color_mask_texture;
  // Tints applied through the mask (red channel takes color, green
  // takes highlight, blue takes highlight2 -- white, the no-op, unless
  // set).
  float color[3]{0.5f, 0.5f, 0.5f};
  float highlight[3]{0.5f, 0.5f, 0.5f};
  float highlight2[3]{1.0f, 1.0f, 1.0f};
  // How strongly team coloring tones each highlight
  // (Graphics::ToneForTeamColor's strength, 0-1); negative = unset,
  // the standard strength applies.
  float highlight_team_coloring_strength{-1.0f};
  float highlight2_team_coloring_strength{-1.0f};
};

/// The loaded media for a BasicIconDef.
struct BasicIconMedia {
  Object::Ref<TextureAsset> texture;
  Object::Ref<TextureAsset> color_mask_texture;
};

/// Basic tier of a character's in-game spaz component: static
/// per-part meshes, a color/colorize texture pair, voice sound sets,
/// and the physique/look knobs the spaz node has always had. Every
/// field defaults to the standard-spaz value and numeric fields are
/// clamped to the spans the legacy style presets covered (mirrors
/// bamaster baserver/character.py, the schema's home).
struct BasicSpazDef {
  // Package manifest for indexed refs: apverids in index order, each
  // contributing its full canonical sorted logical-path listing to one
  // flat integer domain (concatenated in manifest order; the doc-ui
  // scheme). domain_digest: as on BasicIconDef.
  std::vector<std::string> packages;
  std::string domain_digest;
  // Textures.
  CharacterAssetRef color_texture;
  CharacterAssetRef color_mask_texture;
  // Meshes.
  CharacterAssetRef head_mesh;
  CharacterAssetRef torso_mesh;
  CharacterAssetRef pelvis_mesh;
  CharacterAssetRef upper_arm_mesh;
  CharacterAssetRef forearm_mesh;
  CharacterAssetRef hand_mesh;
  CharacterAssetRef upper_leg_mesh;
  CharacterAssetRef lower_leg_mesh;
  CharacterAssetRef toes_mesh;
  // Optional per-part looks, indexed by CharacterBodyPart. A part's
  // own texture / tint mask stand in for the character's color
  // texture / color mask on that part alone (absent = the
  // character's, so one-atlas characters just work). Paired parts
  // can also give their left side its own mesh and textures: the
  // left mesh is still authored as a right-side part and drawn
  // mirrored like any other; absent = the right side's mesh, and
  // absent left textures = the part's own (then the character's).
  // Tint colors follow the same chain: left, then the part's, then
  // the character's.
  struct PartLookDef {
    CharacterAssetRef texture;
    CharacterAssetRef tint_texture;
    CharacterAssetRef left_mesh;
    CharacterAssetRef left_texture;
    CharacterAssetRef left_tint_texture;
    CharacterTintDef tint;
    CharacterTintDef left_tint;
  };
  PartLookDef part_looks[kCharacterBodyPartCount];
  // Sounds.
  std::vector<CharacterAssetRef> jump_sounds;
  std::vector<CharacterAssetRef> attack_sounds;
  std::vector<CharacterAssetRef> impact_sounds;
  std::vector<CharacterAssetRef> death_sounds;
  std::vector<CharacterAssetRef> pickup_sounds;
  std::vector<CharacterAssetRef> fall_sounds;
  // Colors. A definition's primary color is a default the spaz node's
  // own color attr overrides once set (has_color says there is one;
  // without it the node attr is all there is).
  bool has_color{false};
  float color[3]{1.0f, 1.0f, 1.0f};
  float highlight[3]{0.5f, 0.5f, 0.5f};
  // Through the color mask's blue channel; white (the no-op) unless set.
  float highlight2[3]{1.0f, 1.0f, 1.0f};
  // How strongly team coloring tones each highlight
  // (Graphics::ToneForTeamColor's strength, 0-1); negative = unset,
  // the standard strength applies. Pieces can set their own (see
  // CharacterTintDef).
  float highlight_team_coloring_strength{-1.0f};
  float highlight2_team_coloring_strength{-1.0f};
  // Physique (sim state; must never depend on media).
  float torso_radius{0.15f};
  float shoulder_offset[3]{0.0f, 0.0f, 0.0f};
  float thigh_radius{0.04f};
  float ankle_radius{0.07f};
  float step_separation{0.08f};
  // 1.0 = fully rigid arms while idle (the default and a true no-op);
  // lower relaxes the forearms while standing (0.2 = classic slouch).
  float idle_arm_stiffness{1.0f};
  float arm_swing{0.6f};
  float idle_sway{0.05f};
  // Look.
  CharacterEyeStyle eye_style_left{CharacterEyeStyle::kRegular};
  CharacterEyeStyle eye_style_right{CharacterEyeStyle::kRegular};
  float eye_scale{1.0f};
  float eye_offset[3]{0.065f, -0.036f, 0.205f};
  float eye_color[3]{0.5f, 0.5f, 1.2f};
  float eyeball_color[3]{0.46f, 0.38f, 0.36f};
  float eyelid_color[3]{0.5f, 0.3f, 0.2f};
  float eyelid_angle{0.0f};
  float reflection_scale{0.1f};
  bool flippers{};
  // (Wings are attachments on the wing targets; see
  // CharacterAttachTarget.)
  // Attachments (hair tufts, antennas, static props), per target
  // body. Cosmetic only: simulated client-side on the bg-dynamics
  // thread and drawn relative to the target body.
  struct AttachmentSegmentDef {
    CharacterAssetRef mesh;
    // Optional; absent = the character's own color texture / color
    // mask (one-atlas characters just work).
    CharacterAssetRef texture;
    CharacterAssetRef tint_texture;
    // Optional tint colors; absent = the character's own.
    CharacterTintDef tint;
    // Draw offset applied to the mesh in the segment body's frame
    // (the target body's frame for kStatic). Identity when absent.
    Matrix44f offset{kMatrix44fIdentity};
    bool has_offset{};
  };
  struct AttachmentDef {
    CharacterAttachmentType type{CharacterAttachmentType::kLegacyTuftLarge};
    // Target-body-local anchor point.
    float position[3]{};
    // Rest orientation relative to the target body; (w, x, y, z),
    // normalized on parse.
    float rotation[4]{1.0f, 0.0f, 0.0f, 0.0f};
    // Calibration scalars (0-1); per-kind meaning. The tuft/ponytail
    // kinds ignore them; kAntenna maps them geometrically onto its
    // angular spring stiffness/damping.
    float stiffness{0.5f};
    float damping{0.5f};
    // Per-step linear-velocity bleed (0-1); 0 = none, 0.5 = the
    // classic hair trail, which is also the default. Applies to
    // every kind.
    float drag{0.5f};
    // Rest bend at each chain joint, -1 to 1: every segment (the root
    // included, on top of the attachment rotation) rests rotated
    // curl * 90 degrees toward the attachment's local up (+y).
    // 0 = straight.
    float curl{};
    // Segment length dial, 0-1 -> 0.5x-1.5x the kind's capsule length
    // (collision capsule, mass capsule and chain-axis joint anchors;
    // art is untouched). kStatic ignores it.
    float length{0.5f};
    // Segment radius dial, 0-1 -> 1x-3x the kind's capsule radius
    // (collision + mass capsule; total mass stays tabulated).
    float radius{};
    // Per-segment drift of curl/length/radius along a chain (-1..1):
    // segment i uses value + i * change, clamped to the value's range.
    float curl_change{};
    float length_change{};
    float radius_change{};
    // Same drift for the stiffness/damping dials, counted from the
    // root joint (clamped to 0-1 per segment).
    float stiffness_change{};
    float damping_change{};
    // Segment count is fixed per type (ponytail 2, tufts 1).
    std::vector<AttachmentSegmentDef> segments;
  };
  // Indexed by CharacterAttachTarget.
  std::vector<AttachmentDef> attachments[kCharacterAttachTargetCount];
  // Whether each target appeared in the definition at all (an empty
  // kLeft* list still replaces the both-sides one for the left).
  bool attachment_target_present[kCharacterAttachTargetCount]{};
  auto has_attachments() const -> bool {
    for (const auto& list : attachments) {
      if (!list.empty()) {
        return true;
      }
    }
    return false;
  }
};

/// The loaded media for a BasicSpazDef. Populated only when every
/// referenced package is registered locally; otherwise the node wears
/// the app-mode-supplied standin.
struct BasicSpazMedia {
  Object::Ref<TextureAsset> color_texture;
  Object::Ref<TextureAsset> color_mask_texture;
  Object::Ref<MeshAsset> head_mesh;
  Object::Ref<MeshAsset> torso_mesh;
  Object::Ref<MeshAsset> pelvis_mesh;
  Object::Ref<MeshAsset> upper_arm_mesh;
  Object::Ref<MeshAsset> forearm_mesh;
  Object::Ref<MeshAsset> hand_mesh;
  Object::Ref<MeshAsset> upper_leg_mesh;
  Object::Ref<MeshAsset> lower_leg_mesh;
  Object::Ref<MeshAsset> toes_mesh;
  // Parallel to BasicSpazDef::part_looks.
  struct PartLookMedia {
    Object::Ref<TextureAsset> texture;
    Object::Ref<TextureAsset> tint_texture;
    Object::Ref<MeshAsset> left_mesh;
    Object::Ref<TextureAsset> left_texture;
    Object::Ref<TextureAsset> left_tint_texture;
  };
  PartLookMedia part_looks[kCharacterBodyPartCount];
  struct AttachmentSegmentMedia {
    Object::Ref<MeshAsset> mesh;
    Object::Ref<TextureAsset> texture;
    Object::Ref<TextureAsset> tint_texture;
  };
  struct AttachmentMedia {
    std::vector<AttachmentSegmentMedia> segments;
  };
  // Parallel to BasicSpazDef::attachments (per target).
  std::vector<AttachmentMedia> attachments[kCharacterAttachTargetCount];
  std::vector<Object::Ref<SoundAsset>> jump_sounds;
  std::vector<Object::Ref<SoundAsset>> attack_sounds;
  std::vector<Object::Ref<SoundAsset>> impact_sounds;
  std::vector<Object::Ref<SoundAsset>> death_sounds;
  std::vector<Object::Ref<SoundAsset>> pickup_sounds;
  std::vector<Object::Ref<SoundAsset>> fall_sounds;
};

/// A parsed character definition: the presentation of an entity as
/// three optional self-contained components -- name, icon, and the
/// in-game spaz form -- each with a required basic tier this build
/// reads (richer tiers may appear beside it later; a component whose
/// basic tier is missing or malformed simply counts as absent).
/// Across components the rule is: use every block you understand,
/// ignore the rest.
///
/// The json is server-authored (bamaster baserver/character.py is the
/// schema's home) and parsed here natively; the client never exposes
/// the schema. Mods will hand-write json regardless, so anything
/// unusable degrades to "absent" or clamps -- never throws.
///
/// Indexed asset refs decode against a domain both ends build from
/// different sources (the producer's vendored listings, our registry).
/// A block that carries the producer's domain digest is decoded only if
/// ours matches; on a mismatch the block stays on the standin and logs
/// the per-package slice widths, since a wrong-but-in-range index would
/// otherwise silently draw a different asset (same rule as doc-ui's
/// asset_index_digest). No digest = no check.
///
/// This sits below scene_v1 and ui_v1 on purpose: an in-scene spaz, a
/// UI icon/name widget, and a doc-ui decoration all draw from it,
/// with the same standin fallback wherever a component's media isn't
/// local. scene_v1's Character wraps one of these with scene/stream
/// lifecycle. Design: docs/initiatives/character-skins.md.
class CharacterDef {
 public:
  /// Which character part a json holds: an icon block or a spaz block,
  /// on its own (a character is only a delivery bundle; nothing here
  /// takes a whole one). The other part is then simply absent.
  enum class Form : uint8_t { kIcon, kSpaz };

  /// Parses the definition. Media is NOT loaded here: holders call
  /// RetryMedia() when they first display the definition (and on
  /// registry changes), so building one costs a json parse and a
  /// lobby can build one per profile cheaply. Logic thread only.
  CharacterDef(std::string json, Form form);

  /// Re-attempt loading media for any component still wearing the
  /// standin: either its packages weren't registered when we last
  /// tried (registry lookups; holders call this on a slow cadence and
  /// when the registry generation moves) or its assets are still
  /// loading on the asset pipeline (a few atomic reads; holders call
  /// it every draw/step while media_pending()). Returns true if any
  /// component became ready, so a holder can swap its look in place.
  /// A component only becomes ready once every texture and mesh it
  /// references is fully loaded -- flipping earlier would make the
  /// renderer inline-load them on the graphics thread (a hitch); the
  /// standin covers the wait. Logic thread.
  auto RetryMedia() -> bool;

  /// Whether some component has its asset handles but is waiting for
  /// them to finish loading (see RetryMedia).
  auto media_pending() const -> bool {
    return icon_block_.pending() || spaz_block_.pending();
  }

  /// The raw json this was built from (what travels the stream).
  auto json() const -> const std::string& { return json_; }

  auto has_icon() const -> bool { return has_icon_; }
  auto icon() const -> const BasicIconDef& { return icon_; }
  /// Whether the icon's textures are loaded (their packages were
  /// registered locally). False means draw the standin icon.
  auto icon_media_ready() const -> bool { return icon_block_.ready(); }
  auto icon_media() const -> const BasicIconMedia& { return icon_media_; }

  /// Whether the json carried a spaz form this build understands.
  /// False means a node wears the standin with default physique.
  auto has_spaz() const -> bool { return has_spaz_; }
  auto spaz() const -> const BasicSpazDef& { return spaz_; }
  /// Whether every media asset the spaz form references is loaded
  /// (all its packages were registered locally). False means the node
  /// draws/plays the standin while keeping the definition's physique.
  auto spaz_media_ready() const -> bool { return spaz_block_.ready(); }
  auto spaz_media() const -> const BasicSpazMedia& { return spaz_media_; }

 private:
  void Parse_();
  void LoadIconMedia_();
  void LoadSpazMedia_();
  auto SpazRequiredRefs_() const -> std::vector<const CharacterAssetRef*>;
  static auto LoadSpazMediaWith_(const BasicSpazDef& d, MediaGetter* get)
      -> BasicSpazMedia;

  bool has_icon_{};
  bool has_spaz_{};
  Form form_{};
  std::string json_;
  BasicIconDef icon_;
  BasicIconMedia icon_media_;
  MediaBlock icon_block_;
  BasicSpazDef spaz_;
  BasicSpazMedia spaz_media_;
  MediaBlock spaz_block_;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_SUPPORT_CHARACTER_DEF_H_
