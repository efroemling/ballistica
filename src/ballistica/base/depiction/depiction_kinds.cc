// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/depiction/depiction_kinds.h"

#include <algorithm>
#include <cmath>
#include <optional>
#include <string>
#include <utility>
#include <vector>

#include "ballistica/base/assets/assets.h"
#include "ballistica/base/depiction/depiction.h"
#include "ballistica/base/graphics/component/simple_component.h"
#include "ballistica/base/graphics/graphics.h"
#include "ballistica/base/graphics/mesh/nine_patch_mesh.h"
#include "ballistica/base/graphics/text/text_graphics.h"
#include "ballistica/base/graphics/text/text_group.h"
#include "ballistica/base/support/character_def.h"
#include "ballistica/base/support/media_block.h"
#include "ballistica/base/support/name_def.h"
#include "ballistica/core/core.h"
#include "ballistica/shared/generic/json_facade.h"

namespace ballistica::base {

namespace {

// Wire type ids (bacommon.depiction.DepictionTypeID).
const char* const kTypeImage = "i";
const char* const kTypeCharacterIcon = "ci";
const char* const kTypeName = "n";

/// A character's icon: its art tinted by its colors through the round
/// icon mask, or the standard-spaz standin (in those same colors) while
/// the art isn't local, upgrading in place once it is.
///
/// A color override replaces its main color, the way a team's color
/// replaces a character's own on its spaz (a player's icon in a teams
/// game); highlights are always the icon's own.
class CharacterIconDepiction : public Depiction {
 public:
  /// ``json`` is an icon block on its own (a character's 'i').
  explicit CharacterIconDepiction(std::string json)
      : Depiction(kTypeCharacterIcon),
        def_(std::move(json), CharacterDef::Form::kIcon) {}

  auto GetAspect() const -> std::optional<float> override { return 1.0f; }

  void Update(millisecs_t now) override {
    if (def_.has_icon() && !def_.icon_media_ready()
        && pacer_.Due(def_.media_pending(), now)) {
      def_.RetryMedia();
    }
  }

  void Draw(const DepictionDrawContext& context) override {
    if (!context.transparent) {
      return;
    }
    const BaseAssetSet& assets = g_base->assets->base_assets();
    TextureAsset* tex = assets.standin_icon.get();
    TextureAsset* tint = assets.standin_icon_color_mask.get();
    float color[3] = {0.5f, 0.5f, 0.5f};
    float highlight[3] = {0.5f, 0.5f, 0.5f};
    float highlight2[3] = {1.0f, 1.0f, 1.0f};
    if (def_.has_icon()) {
      const BasicIconDef& icon = def_.icon();
      std::copy(std::begin(icon.color), std::end(icon.color), color);
      std::copy(std::begin(icon.highlight), std::end(icon.highlight),
                highlight);
      std::copy(std::begin(icon.highlight2), std::end(icon.highlight2),
                highlight2);
      if (def_.icon_media_ready()) {
        tex = def_.icon_media().texture.get();
        tint = def_.icon_media().color_mask_texture.get();
      }
    }
    if (!tex) {
      return;
    }
    if (const float* over = context.color_override) {
      std::copy(over, over + 3, color);
    }
    // Team coloring: our main color (the override, or our own without
    // one) stays dominant over our highlights.
    if (context.team_coloring) {
      float strength = Graphics::TeamColoringStrength();
      float strength2 = strength;
      if (def_.has_icon()) {
        const BasicIconDef& icon = def_.icon();
        if (icon.highlight_team_coloring_strength >= 0.0f) {
          strength = icon.highlight_team_coloring_strength;
        }
        if (icon.highlight2_team_coloring_strength >= 0.0f) {
          strength2 = icon.highlight2_team_coloring_strength;
        }
      }
      Graphics::ToneForTeamColor(color, highlight, strength);
      Graphics::ToneForTeamColor(color, highlight2, strength2);
    }
    context.StandardColor(color);
    context.StandardColor(highlight);
    context.StandardColor(highlight2);
    const DepictionBox& b = context.box;
    float alpha = context.StandardOpacity();
    // Premultiplied art composites 'over' only if rgb is scaled by
    // alpha (see image node).
    float cmul =
        (tex->premultiplied() ? alpha : 1.0f) * context.StandardBrightness();
    SimpleComponent c(context.pass);
    c.SetTransparent(true);
    c.SetTexture(tex);
    c.SetColor(cmul, cmul, cmul, alpha);
    if (tint) {
      c.SetColorizeTexture(tint);
      c.SetColorizeColor(color[0], color[1], color[2]);
      c.SetColorizeColor2(highlight[0], highlight[1], highlight[2]);
      c.SetColorizeColor3(highlight2[0], highlight2[1], highlight2[2]);
    }
    c.SetMaskTexture(assets.character_icon_mask.get());
    {
      auto xf = c.ScopedTransform();
      c.Translate(b.x + b.width * 0.5f, b.y + b.height * 0.5f, context.z);
      c.Scale(b.width, b.height, 1.0f);
      c.DrawMeshAsset(
          g_base->assets->BuiltinMesh(BuiltinMeshID::kMeshesImage1x1));
    }
    c.Submit();
  }

 private:
  CharacterDef def_;
  MediaRetryPacer pacer_;
};

/// A name (a NameDef: an account's, a character's, ...), drawn in its
/// richest form we understand:
///
/// - Basic: its text in its color, as large as fits the box.
/// - Glyph: the same, after an icon glyph (a global profile's look).
/// - Capsule: the text in a rounded capsule (a 9-patch, a circle by
///   default), with an optional square icon covering the capsule's left
///   end; the text sits against the icon (or reaches into the left
///   end) and reaches into the right end, by the icon edge and text
///   inset. The whole capsule is the shape fitted to the box; in a box
///   too narrow for it, the capsule keeps the box's height (and the
///   icon its size) and only the text shrinks to fit, down to
///   kMinTextShrink of its size, past which everything shrinks.
///
/// Our shape is known once our text is measured (in the background
/// for cold OS-drawn text); until then we report none and draw nothing,
/// so hosts fill and hit-test their whole box for that moment.
class NameDepiction : public Depiction {
 public:
  /// ``json`` is a name block on its own ({"b": ..., "c": ...}).
  explicit NameDepiction(std::string json) : Depiction(kTypeName) {
    if (auto doc = JsonDoc::Parse(json)) {
      if (auto name = NameDef::Parse(doc->root())) {
        name_ = std::move(*name);
      }
    }
    // A glyph tier puts its icon before the text (unless a capsule,
    // which brings its own icon, draws instead); otherwise it is
    // exactly the basic tier.
    if (name_.glyph && !name_.capsule) {
      shown_text_ = name_.glyph->icon + name_.basic.text;
    } else {
      shown_text_ = name_.basic.text;
    }
    text_group_.SetText(shown_text_, TextMesh::HAlign::kCenter,
                        TextMesh::VAlign::kCenter);
  }

  auto GetAspect() const -> std::optional<float> override {
    if (!width_) {
      return std::nullopt;
    }
    if (const CapsuleNameDef* cap = Capsule_()) {
      float r = CapsuleRadius_(*cap);
      return Layout_(*cap, *width_).length / (2.0f * r);
    }
    return std::max(*width_, 1.0f) / kTextHeight;
  }

  auto GetMinAspect() const -> std::optional<float> override {
    const CapsuleNameDef* cap = Capsule_();
    if (!width_ || !cap) {
      return std::nullopt;
    }
    float r = CapsuleRadius_(*cap);
    return Layout_(*cap, *width_ * kMinTextShrink).length / (2.0f * r);
  }

  void Update(millisecs_t now) override {
    // Measure without stalling (cold OS-span measures run in the
    // background; until then we have no shape and draw nothing).
    if (!width_ && !shown_text_.empty()) {
      width_ = g_base->text_graphics->TryGetStringWidth(shown_text_);
    }
    if (const CapsuleNameDef* cap = Capsule_()) {
      LoadCapsuleMedia_(*cap, now);
    }
  }

  void Draw(const DepictionDrawContext& context) override {
    if (!context.transparent || !width_) {
      return;
    }
    const DepictionBox& b = context.box;
    if (const CapsuleNameDef* cap = Capsule_()) {
      // In box units: the capsule's radius is half the box's height.
      float r = b.height * 0.5f;
      float natural_r = CapsuleRadius_(*cap);
      float scale = r / natural_r;
      DrawCapsuleBody_(context, *cap, r);
      bool has_icon = cap->icon_texture.present();
      if (has_icon) {
        DrawIcon_(context, *cap, r);
      }
      // A box narrower than our natural length (see GetMinAspect)
      // shrinks the text to fit what's left between the ends (still
      // centered on the capsule's midline).
      CapsuleLayout layout = Layout_(*cap, *width_);
      float shrink{1.0f};
      float length = b.width / scale;
      if (length < layout.length && *width_ > 0.0f) {
        shrink = std::clamp((*width_ - (layout.length - length)) / *width_,
                            0.0f, 1.0f);
      }
      float text_left = b.x + layout.text_left * scale;
      DrawText_(context, text_left + *width_ * shrink * scale * 0.5f, b.y + r,
                scale * shrink);
      return;
    }
    DrawText_(context, b.x + b.width * 0.5f, b.y + b.height * 0.5f,
              b.height / kTextHeight);
  }

 private:
  /// A basic-tier name's box height at text scale 1: the text's row
  /// height (kTextRowHeight, 32) plus padding around it. (Capsules are
  /// sized in cap heights instead, kTextCapHeight being their unit.)
  static constexpr float kTextHeight{40.0f};

  /// How small a capsule's text may shrink within it (a fraction of
  /// its size) before the whole capsule shrinks instead.
  static constexpr float kMinTextShrink{0.4f};

  auto Capsule_() const -> const CapsuleNameDef* {
    return name_.capsule ? &*name_.capsule : nullptr;
  }

  /// The capsule's radius at text scale 1 (radius 1.0 = cap height).
  static auto CapsuleRadius_(const CapsuleNameDef& cap) -> float {
    return cap.radius * kTextCapHeight * 0.5f;
  }

  /// Room kept between the capitals and the curve when the text inset
  /// is automatic, in cap heights.
  static constexpr float kAutoInsetMargin{0.1f};

  /// How much of that available depth the automatic inset uses (all of
  /// it read as cramped at larger radii).
  static constexpr float kAutoInsetFraction{0.5f};

  /// How far the text reaches into a rounded end (a fraction of the
  /// end's depth; see CapsuleNameDef::text_inset). Automatic: a share of
  /// how deep the capitals' corners (half a cap height off center) can
  /// go while staying a margin inside the curve -- none at radius 1.0,
  /// where the curve hugs the capitals, and more as the radius grows.
  static auto TextInset_(const CapsuleNameDef& cap) -> float {
    if (cap.text_inset) {
      return *cap.text_inset;
    }
    float end_r = cap.radius * 0.5f;  // In cap heights.
    float reach = end_r - kAutoInsetMargin;
    float depth_sq = reach * reach - 0.25f;
    return depth_sq > 0.0f ? kAutoInsetFraction * std::sqrt(depth_sq) / end_r
                           : 0.0f;
  }

  struct CapsuleLayout {
    float text_left;
    float length;
  };

  /// Where the text starts and how long the capsule is, at text scale
  /// 1, for text ``text_width`` wide: the left end (up to the icon's edge point
  /// -- its center at the left cap's center, out by its scaled half-size times
  /// its edge -- or a cap less its inset), the text, then the right cap less
  /// its inset. Never shorter than a circle; text too short for that is
  /// centered in the room.
  static auto Layout_(const CapsuleNameDef& cap, float text_width)
      -> CapsuleLayout {
    float r = CapsuleRadius_(cap);
    float end = r * (1.0f - TextInset_(cap));
    float left = cap.icon_texture.present()
                     ? r * (1.0f + cap.icon_scale * cap.icon_edge)
                     : end;
    float length = left + std::max(text_width, 0.0f) + end;
    float min_length = 2.0f * r;
    if (length < min_length) {
      return {left + (min_length - length) * 0.5f, min_length};
    }
    return {left, length};
  }

  void LoadCapsuleMedia_(const CapsuleNameDef& cap, millisecs_t now) {
    std::vector<const PackageAssetRef*> required;
    for (const auto* ref :
         {&cap.capsule_texture, &cap.capsule_tint_texture, &cap.icon_texture}) {
      if (ref->present()) {
        required.push_back(ref);
      }
    }
    if (required.empty() || block_.ready()
        || !pacer_.Due(block_.pending(), now)) {
      return;
    }
    // MediaBlock notes indexed refs to resolve in place.
    CapsuleNameDef& d = *name_.capsule;
    std::vector<MediaBlock::IndexedRef> indexed;
    MediaBlock::NoteIndexed(&d.capsule_texture, "textures/", &indexed);
    MediaBlock::NoteIndexed(&d.capsule_tint_texture, "textures/", &indexed);
    MediaBlock::NoteIndexed(&d.icon_texture, "textures/", &indexed);
    block_.Load(d.packages, d.domain_digest, indexed, required,
                [this, &d](MediaGetter* get) {
                  if (d.capsule_texture.present()) {
                    capsule_texture_asset_ = get->Texture(d.capsule_texture);
                  }
                  if (d.capsule_tint_texture.present()) {
                    capsule_tint_texture_asset_ =
                        get->Texture(d.capsule_tint_texture);
                  }
                  if (d.icon_texture.present()) {
                    icon_texture_asset_ = get->Texture(d.icon_texture);
                  }
                });
    block_.CheckPending();
  }

  /// A host-state-applied color multiplier for a texture (see
  /// ImageDepiction): rgb premultiplied when the texture is.
  static void SetColor_(SimpleComponent* c, const DepictionDrawContext& ctx,
                        TextureAsset* tex, const float* rgba) {
    float rgb[3]{rgba[0], rgba[1], rgba[2]};
    ctx.StandardColor(rgb);
    float alpha = rgba[3] * ctx.StandardOpacity();
    float cmul =
        (tex->premultiplied() ? alpha : 1.0f) * ctx.StandardBrightness();
    c->SetColor(rgb[0] * cmul, rgb[1] * cmul, rgb[2] * cmul, alpha);
  }

  void DrawCapsuleBody_(const DepictionDrawContext& context,
                        const CapsuleNameDef& cap, float r) {
    // Our own art once it's here; a plain circle until then (or if we
    // have none). Only the look changes when it arrives, never sizes.
    bool ours = cap.capsule_texture.present() && block_.ready();
    TextureAsset* tex =
        ours
            ? capsule_texture_asset_.get()
            : g_base->assets->BuiltinTexture(BuiltinTextureID::kTexturesCircle);
    if (!tex || !tex->loaded()) {
      return;
    }
    // Insets, tiling, and tint describe our art; the circle has none.
    NinePatchSourceInsets insets;
    NinePatchFill fill{NinePatchFill::kStretch};
    TextureAsset* tint_tex{};
    if (ours) {
      insets.left = cap.capsule_insets[0];
      insets.right = cap.capsule_insets[1];
      if (cap.capsule_tile) {
        fill = NinePatchFill::kTileFit;
      }
      tint_tex = capsule_tint_texture_asset_.get();
    }
    // The art's own radius, so its edge-ratio point lands on the
    // capsule's logical edge (anything beyond -- a glow -- spills out).
    const DepictionBox& b = context.box;
    float art_r = r / cap.capsule_edge;
    float grow = art_r - r;
    float w = b.width + 2.0f * grow;
    float h = b.height + 2.0f * grow;
    // Nothing to draw in an empty box (and the negation also catches
    // NaN from one).
    if (!(w > 0.0f && h > 0.0f)) {
      return;
    }
    float bx = NinePatchMesh::BorderForRadius(art_r, w, h);
    float by = NinePatchMesh::BorderForRadius(art_r, h, w);
    auto mesh = Object::New<NinePatchMesh>(b.x - grow, b.y - grow, context.z, w,
                                           h, bx, by, bx, by, insets, fill,
                                           NinePatchFill::kStretch);
    SimpleComponent c(context.pass);
    c.SetTransparent(true);
    c.SetTexture(tex);
    const float* over = context.color_override;
    if (over && cap.override_capsule) {
      float rgba[4]{over[0], over[1], over[2], cap.capsule_color[3]};
      SetColor_(&c, context, tex, rgba);
    } else {
      float rgba[4];
      std::copy(cap.capsule_color, cap.capsule_color + 4, rgba);
      TeamTone_(context, rgba, cap.capsule_team_coloring_strength);
      SetColor_(&c, context, tex, rgba);
    }
    if (tint_tex) {
      float tints[3][3];
      for (int i = 0; i < 3; ++i) {
        bool overridden = over && cap.override_tints[i];
        const float* src = overridden ? over : cap.capsule_tint_colors[i];
        std::copy(src, src + 3, tints[i]);
        if (!overridden) {
          TeamTone_(context, tints[i],
                    cap.capsule_tint_team_coloring_strengths[i]);
        }
        context.StandardColor(tints[i]);
      }
      c.SetColorizeTexture(tint_tex);
      c.SetColorizeColor(tints[0][0], tints[0][1], tints[0][2]);
      c.SetColorizeColor2(tints[1][0], tints[1][1], tints[1][2]);
      c.SetColorizeColor3(tints[2][0], tints[2][1], tints[2][2]);
    }
    c.DrawMesh(mesh.get());
    c.Submit();
  }

  void DrawIcon_(const DepictionDrawContext& context, const CapsuleNameDef& cap,
                 float r) {
    // Nothing until it's here: its square is already in the layout.
    if (!block_.ready() || !icon_texture_asset_.exists()) {
      return;
    }
    TextureAsset* tex = icon_texture_asset_.get();
    const DepictionBox& b = context.box;
    float size = 2.0f * r * cap.icon_scale;
    SimpleComponent c(context.pass);
    c.SetTransparent(true);
    c.SetTexture(tex);
    const float* over = context.color_override;
    if (over && cap.override_icon) {
      float rgba[4]{over[0], over[1], over[2], cap.icon_color[3]};
      SetColor_(&c, context, tex, rgba);
    } else {
      float rgba[4];
      std::copy(cap.icon_color, cap.icon_color + 4, rgba);
      TeamTone_(context, rgba, cap.icon_team_coloring_strength);
      SetColor_(&c, context, tex, rgba);
    }
    {
      auto xf = c.ScopedTransform();
      c.Translate(b.x + r, b.y + r, context.z);
      c.Scale(size, size, 1.0f);
      c.DrawMeshAsset(
          g_base->assets->BuiltinMesh(BuiltinMeshID::kMeshesImage1x1));
    }
    c.Submit();
  }

  /// Under team coloring, tone one of our own colors (a part the
  /// override isn't routed to) so 'our color' stays dominant: the
  /// override if there is one, else our text's own color.
  /// ``strength`` is that color's own setting (negative = the standard).
  void TeamTone_(const DepictionDrawContext& context, float* rgb,
                 float strength = -1.0f) const {
    if (!context.team_coloring) {
      return;
    }
    Graphics::ToneForTeamColor(
        context.color_override ? context.color_override : name_.basic.color,
        rgb, strength >= 0.0f ? strength : Graphics::TeamColoringStrength());
  }

  /// How much the text glows like neon (see CapsuleNameDef::text_glow);
  /// 0 draws plain text with its usual drop shadow.
  auto TextGlow_() const -> float {
    const CapsuleNameDef* cap = Capsule_();
    return cap ? cap->text_glow : 0.0f;
  }

  void DrawText_(const DepictionDrawContext& context, float cx, float cy,
                 float scale) {
    float alpha = context.StandardOpacity();
    // A host's color override replaces our own (unless our capsule
    // routes it elsewhere; see CapsuleNameDef).
    const CapsuleNameDef* cap = Capsule_();
    bool take_override = context.color_override && (!cap || cap->override_text);
    const float* own =
        take_override ? context.color_override : name_.basic.color;
    float rgb[3]{own[0], own[1], own[2]};
    if (!take_override) {
      TeamTone_(context, rgb);
    }
    context.StandardColor(rgb);
    // Our text brightens toward white (a flash of saturated text still
    // shows); see Graphics::BrightenColor.
    float brightness = context.StandardBrightness();
    Graphics::BrightenColor(rgb, brightness);
    // Glyphs with colors of their own (icon chars) keep them, as they do
    // in text widgets (and can only brighten by a multiply).
    float rgb_plain[3]{brightness, brightness, brightness};
    context.StandardColor(rgb_plain);
    SimpleComponent c(context.pass);
    c.SetTransparent(true);
    int elem_count = text_group_.GetElementCount();
    for (int e = 0; e < elem_count; e++) {
      TextureAsset* t = text_group_.GetElementTexture(e);
      if (!t->preloaded()) {
        continue;
      }
      c.SetTexture(t);
      float shadow_opacity;
      float text_glow = TextGlow_();
      if (text_glow > 0.0f) {
        // Glowing text: the glow is its whole surround (no shadow).
        shadow_opacity = 0.0f;
        c.SetShadow(0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, text_glow);
      } else {
        shadow_opacity = 0.5f * alpha * alpha;
        c.SetShadow(-0.004f * text_group_.GetElementUScale(e),
                    -0.004f * text_group_.GetElementVScale(e), 0.0f,
                    shadow_opacity);
      }
      if (shadow_opacity > 0 || text_glow > 0) {
        c.SetMaskUV2Texture(text_group_.GetElementMaskUV2Texture(e));
      } else {
        c.ClearMaskUV2Texture();
      }
      // (Brightness is already in both colors.)
      float cmul = t->premultiplied() ? alpha : 1.0f;
      const float* ergb = text_group_.GetElementCanColor(e) ? rgb : rgb_plain;
      c.SetColor(ergb[0] * cmul, ergb[1] * cmul, ergb[2] * cmul, alpha);
      c.SetFlatness(std::min(text_group_.GetElementMaxFlatness(e), 1.0f));
      {
        auto xf = c.ScopedTransform();
        c.Translate(cx, cy, context.z);
        c.Scale(scale, scale, 1.0f);
        c.DrawMesh(text_group_.GetElementMesh(e));
      }
    }
    c.Submit();
  }

  NameDef name_;
  /// What we draw as text: the basic tier's, after any glyph.
  std::string shown_text_;
  TextGroup text_group_;
  std::optional<float> width_;
  MediaBlock block_;
  MediaRetryPacer pacer_;
  Object::Ref<TextureAsset> capsule_texture_asset_;
  Object::Ref<TextureAsset> capsule_tint_texture_asset_;
  Object::Ref<TextureAsset> icon_texture_asset_;
};

/// A texture, fetched on demand, optionally masked and tinted. A faint
/// soft box stands in while the art isn't local.
class ImageDepiction : public Depiction, public DepictionTintControl {
 public:
  ImageDepiction() : Depiction(kTypeImage) {}

  auto GetTintControl() -> DepictionTintControl* override { return this; }

  void SetFlatColor(const float* rgb, float flatness) override {
    std::copy(rgb, rgb + 3, flat_rgb_);
    flatness_ = flatness;
    has_flat_ = true;
  }

  void ClearFlatColor() override { has_flat_ = false; }

  /// Parse; false if the json can't be used (no texture, or indexed
  /// refs with no package manifest to index into).
  auto Parse(const JsonRef& root) -> bool {
    if (!ReadPackageAssetRef(root, "t", &texture_)) {
      return false;
    }
    ReadPackageAssetRef(root, "mt", &mask_texture_);
    ReadPackageAssetRef(root, "tt", &tint_texture_);
    // Refs may be full specs or indices into this manifest (the
    // compact wire form; see bacommon.depiction.ImageDepiction).
    ReadPackageManifest(root, &packages_, &domain_digest_);
    for (const auto* ref : {&texture_, &mask_texture_, &tint_texture_}) {
      if (ref->index >= 0 && packages_.empty()) {
        return false;
      }
    }
    if (auto aspect = root["a"].as_double(); aspect && *aspect > 0.0) {
      aspect_ = static_cast<float>(*aspect);
    }
    if (auto scale = root["s"].as_double()) {
      scale_ = std::clamp(static_cast<float>(*scale), 0.0f, 2.0f);
    }
    ReadFloats(root, "c", color_, 4);
    has_tint_color_ = ReadFloats(root, "tc1", tint_color_, 3);
    has_tint2_color_ = ReadFloats(root, "tc2", tint2_color_, 3);
    has_tint3_color_ = ReadFloats(root, "tc3", tint3_color_, 3);
    return true;
  }

  auto GetAspect() const -> std::optional<float> override { return aspect_; }

  void Update(millisecs_t now) override {
    if (block_.ready() || !pacer_.Due(block_.pending(), now)) {
      return;
    }
    std::vector<const PackageAssetRef*> required{&texture_};
    for (const auto* opt : {&mask_texture_, &tint_texture_}) {
      if (opt->present()) {
        required.push_back(opt);
      }
    }
    std::vector<MediaBlock::IndexedRef> indexed;
    MediaBlock::NoteIndexed(&texture_, "textures/", &indexed);
    MediaBlock::NoteIndexed(&mask_texture_, "textures/", &indexed);
    MediaBlock::NoteIndexed(&tint_texture_, "textures/", &indexed);
    block_.Load(packages_, domain_digest_, indexed, required,
                [this](MediaGetter* get) {
                  texture_asset_ = get->Texture(texture_);
                  if (mask_texture_.present()) {
                    mask_texture_asset_ = get->Texture(mask_texture_);
                  }
                  if (tint_texture_.present()) {
                    tint_texture_asset_ = get->Texture(tint_texture_);
                  }
                });
    block_.CheckPending();
  }

  void Draw(const DepictionDrawContext& context) override {
    if (!context.transparent) {
      return;
    }
    const DepictionBox& b = context.box;
    MeshAsset* quad =
        g_base->assets->BuiltinMesh(BuiltinMeshID::kMeshesImage1x1);
    if (!block_.ready()) {
      DrawLoading_(context, quad);
      return;
    }
    SimpleComponent c(context.pass);
    c.SetTransparent(true);
    {
      float color[3]{color_[0], color_[1], color_[2]};
      if (has_flat_) {
        std::copy(std::begin(flat_rgb_), std::end(flat_rgb_), color);
      }
      float tint[3]{tint_color_[0], tint_color_[1], tint_color_[2]};
      float tint2[3]{tint2_color_[0], tint2_color_[1], tint2_color_[2]};
      float tint3[3]{tint3_color_[0], tint3_color_[1], tint3_color_[2]};
      context.StandardColor(color);
      context.StandardColor(tint);
      context.StandardColor(tint2);
      context.StandardColor(tint3);
      float alpha = color_[3] * context.StandardOpacity();
      float cmul = (texture_asset_->premultiplied() ? alpha : 1.0f)
                   * context.StandardBrightness();
      c.SetTexture(texture_asset_.get());
      c.SetColor(color[0] * cmul, color[1] * cmul, color[2] * cmul, alpha);
      if (has_flat_) {
        // One flat color in place of the usual coloring (no colorize).
        c.SetFlatness(flatness_);
      } else if (tint_texture_asset_.exists()) {
        c.SetColorizeTexture(tint_texture_asset_.get());
        if (has_tint_color_) {
          c.SetColorizeColor(tint[0], tint[1], tint[2]);
        }
        if (has_tint2_color_) {
          c.SetColorizeColor2(tint2[0], tint2[1], tint2[2]);
        }
        if (has_tint3_color_) {
          c.SetColorizeColor3(tint3[0], tint3[1], tint3[2]);
        }
      }
      if (mask_texture_asset_.exists()) {
        c.SetMaskTexture(mask_texture_asset_.get());
      }
    }
    {
      auto xf = c.ScopedTransform();
      c.Translate(b.x + b.width * 0.5f, b.y + b.height * 0.5f, context.z);
      // Our scale grows or shrinks the drawing about the box's center;
      // the box itself (layout, presses) is untouched.
      c.Scale(b.width * scale_, b.height * scale_, 1.0f);
      c.DrawMeshAsset(quad);
    }
    c.Submit();
  }

 private:
  /// Standin while the art isn't local: the app's busy spinner, mostly
  /// faded and turning, a third of the box. (Loads retry indefinitely,
  /// so there's no failed look; see depictions.md, Image.)
  static void DrawLoading_(const DepictionDrawContext& context,
                           MeshAsset* quad) {
    const DepictionBox& b = context.box;
    TextureAsset* spinner =
        g_base->assets->base_assets().depiction_spinner.get();
    if (!spinner) {
      return;
    }
    float alpha = 0.25f * context.StandardOpacity();
    float cmul = (spinner->premultiplied() ? alpha : 1.0f)
                 * context.StandardBrightness();
    float size = std::min(b.width, b.height) / 3.0f;
    auto turns = static_cast<float>(std::fmod(
        static_cast<double>(g_core->AppTimeMillisecs()) / 1000.0, 1.0));
    SimpleComponent c(context.pass);
    c.SetTransparent(true);
    c.SetTexture(spinner);
    c.SetColor(cmul, cmul, cmul, alpha);
    {
      auto xf = c.ScopedTransform();
      c.Translate(b.x + b.width * 0.5f, b.y + b.height * 0.5f, context.z);
      c.Scale(size, size, 1.0f);
      c.Rotate(-360.0f * turns, 0.0f, 0.0f, 1.0f);
      c.DrawMeshAsset(quad);
    }
    c.Submit();
  }

  static auto ReadFloats(const JsonRef& root, const char* key, float* out,
                         size_t count) -> bool {
    JsonRef arr = root[key];
    if (!arr.is_array() || arr.size() != count) {
      return false;
    }
    for (size_t i = 0; i < count; ++i) {
      if (auto val = arr[i].as_double()) {
        out[i] = static_cast<float>(*val);
      }
    }
    return true;
  }

  PackageAssetRef texture_;
  PackageAssetRef mask_texture_;
  PackageAssetRef tint_texture_;
  std::vector<std::string> packages_;
  std::string domain_digest_;
  float aspect_{1.0f};
  float scale_{1.0f};
  float color_[4]{1.0f, 1.0f, 1.0f, 1.0f};
  float tint_color_[3]{1.0f, 1.0f, 1.0f};
  float tint2_color_[3]{1.0f, 1.0f, 1.0f};
  float tint3_color_[3]{1.0f, 1.0f, 1.0f};
  bool has_tint_color_{};
  bool has_tint2_color_{};
  bool has_tint3_color_{};
  bool has_flat_{};
  float flat_rgb_[3]{1.0f, 1.0f, 1.0f};
  float flatness_{};
  MediaBlock block_;
  MediaRetryPacer pacer_;
  Object::Ref<TextureAsset> texture_asset_;
  Object::Ref<TextureAsset> mask_texture_asset_;
  Object::Ref<TextureAsset> tint_texture_asset_;
};

// The component json a character icon (an icon block) or name (a name
// block) carries, from its 'j' field.
auto ComponentJson(const JsonRef& root) -> std::optional<std::string> {
  auto val = root["j"].as_string();
  if (!val) {
    return std::nullopt;
  }
  return std::string(*val);
}

}  // namespace

void RegisterBaseDepictionKinds() {
  DepictionRegistry::RegisterKind(
      kTypeCharacterIcon,
      [](const DepictionRegistry::Source& src) -> Object::Ref<Depiction> {
        auto json = ComponentJson(src.root);
        if (!json) {
          return {};
        }
        return Object::New<Depiction, CharacterIconDepiction>(std::move(*json));
      });
  DepictionRegistry::RegisterKind(
      kTypeName,
      [](const DepictionRegistry::Source& src) -> Object::Ref<Depiction> {
        auto json = ComponentJson(src.root);
        if (!json) {
          return {};
        }
        return Object::New<Depiction, NameDepiction>(std::move(*json));
      });
  DepictionRegistry::RegisterKind(
      kTypeImage,
      [](const DepictionRegistry::Source& src) -> Object::Ref<Depiction> {
        auto out = Object::New<ImageDepiction>();
        if (!out->Parse(src.root)) {
          return {};
        }
        return Object::Ref<Depiction>(out.get());
      });
}

}  // namespace ballistica::base
