// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/depiction/depiction.h"

#include <algorithm>
#include <set>
#include <string>
#include <unordered_map>
#include <utility>

#include "ballistica/base/assets/assets.h"
#include "ballistica/base/depiction/depiction_kinds.h"
#include "ballistica/base/graphics/component/simple_component.h"
#include "ballistica/base/graphics/graphics.h"
#include "ballistica/base/graphics/text/text_graphics.h"
#include "ballistica/base/graphics/text/text_group.h"
#include "ballistica/base/logic/logic.h"
#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging.h"

namespace ballistica::base {

auto FitDepictionBox(const DepictionBox& box, const Depiction& depiction,
                     DepictionHAlign h_align, DepictionVAlign v_align,
                     float trailing_aspect) -> DepictionBox {
  // We fit the whole shape (depiction plus any trailing room), then
  // hand back the depiction's part of it.
  float trailing = std::max(0.0f, trailing_aspect);
  float width = box.width;
  float height = box.height;
  std::optional<float> aspect = depiction.GetAspect();
  if (aspect.has_value() && *aspect > 0.0f && box.width > 0.0f
      && box.height > 0.0f) {
    std::optional<float> min_aspect = depiction.GetMinAspect();
    float squeezed = (min_aspect.has_value() && *min_aspect > 0.0f)
                         ? std::min(*min_aspect, *aspect)
                         : *aspect;
    float whole = *aspect + trailing;
    float whole_squeezed = squeezed + trailing;
    float box_aspect = box.width / box.height;
    if (box_aspect > whole) {
      height = box.height;
      width = box.height * whole;
    } else if (box_aspect < whole_squeezed) {
      width = box.width;
      height = box.width / whole_squeezed;
    }
    // (Otherwise the box is between our two shapes: take it whole.)
  }
  DepictionBox out{box.x, box.y, width, height};
  // (A shapeless depiction fills what the trailing room leaves.)
  float dep_width = std::max(0.0f, width - trailing * height);
  switch (h_align) {
    case DepictionHAlign::kLeft:
      break;
    case DepictionHAlign::kCenter:
      out.x += (box.width - width) * 0.5f;
      break;
    case DepictionHAlign::kRight:
      out.x += box.width - width;
      break;
  }
  switch (v_align) {
    case DepictionVAlign::kBottom:
      break;
    case DepictionVAlign::kCenter:
      out.y += (box.height - height) * 0.5f;
      break;
    case DepictionVAlign::kTop:
      out.y += box.height - height;
      break;
  }
  out.width = dep_width;
  return out;
}

namespace {

/// A suffix's text scale, per unit of its depiction's height: the
/// basic name tier's (a ~40-unit line of small text fills its box).
constexpr float kSuffixScalePerHeight{1.0f / 40.0f};

/// The gap between a depiction and its suffix, in depiction heights.
constexpr float kSuffixGap{0.15f};

}  // namespace

DepictionSuffix::DepictionSuffix() = default;
DepictionSuffix::~DepictionSuffix() = default;

void DepictionSuffix::SetText(const std::string& text) {
  if (text == text_) {
    return;
  }
  text_ = text;
  width_.reset();
  if (text_.empty()) {
    text_group_.Clear();
    return;
  }
  if (!text_group_.exists()) {
    text_group_ = Object::New<TextGroup>();
  }
  text_group_->SetText(text_, TextMesh::HAlign::kLeft,
                       TextMesh::VAlign::kCenter);
}

auto DepictionSuffix::GetTrailingAspect() const -> float {
  if (text_.empty()) {
    return 0.0f;
  }
  // Measure without stalling (cold OS-span measures run in the
  // background; until then we take no room and draw nothing).
  if (!width_) {
    width_ = g_base->text_graphics->TryGetStringWidth(text_);
  }
  if (!width_) {
    return 0.0f;
  }
  return kSuffixGap + *width_ * kSuffixScalePerHeight;
}

void DepictionSuffix::Draw(const DepictionDrawContext& context,
                           const DepictionBox& depiction_box,
                           const float* rgb) {
  if (!context.transparent || !width_ || !text_group_.exists()) {
    return;
  }
  float h = depiction_box.height;
  float scale = h * kSuffixScalePerHeight;
  float x = depiction_box.x + depiction_box.width + kSuffixGap * h;
  float y = depiction_box.y + h * 0.5f;
  float color[3]{1.0f, 1.0f, 1.0f};
  if (rgb) {
    std::copy(rgb, rgb + 3, color);
  }
  context.StandardColor(color);
  // Brightens toward white, as a name's text does (see
  // Graphics::BrightenColor); own-colored glyphs just multiply.
  float brightness = context.StandardBrightness();
  Graphics::BrightenColor(color, brightness);
  float alpha = context.StandardOpacity();
  SimpleComponent c(context.pass);
  c.SetTransparent(true);
  int elem_count = text_group_->GetElementCount();
  for (int e = 0; e < elem_count; e++) {
    TextureAsset* t = text_group_->GetElementTexture(e);
    if (!t->preloaded()) {
      continue;
    }
    c.SetTexture(t);
    c.SetShadow(-0.004f * text_group_->GetElementUScale(e),
                -0.004f * text_group_->GetElementVScale(e), 0.0f,
                0.5f * alpha * alpha);
    c.SetMaskUV2Texture(text_group_->GetElementMaskUV2Texture(e));
    float cmul = t->premultiplied() ? alpha : 1.0f;
    const float* ergb = text_group_->GetElementCanColor(e) ? color : nullptr;
    if (ergb) {
      c.SetColor(ergb[0] * cmul, ergb[1] * cmul, ergb[2] * cmul, alpha);
    } else {
      float plain = cmul * brightness;
      c.SetColor(plain, plain, plain, alpha);
    }
    c.SetFlatness(std::min(text_group_->GetElementMaxFlatness(e), 1.0f));
    {
      auto xf = c.ScopedTransform();
      c.Translate(x, y, context.z);
      c.Scale(scale, scale, 1.0f);
      c.DrawMesh(text_group_->GetElementMesh(e));
    }
  }
  c.Submit();
}

namespace {

// The standard disabled look (see DepictionDrawContext): a fade like a
// disabled button's icon, a slight dim, and colors grey at their
// luminance scaled like a disabled button's body.
constexpr float kDisabledOpacityScale{0.5f};
constexpr float kDisabledBrightnessScale{0.85f};
constexpr float kDisabledGreyScale{0.85f};

}  // namespace

auto DepictionDrawContext::StandardOpacity() const -> float {
  return disabled ? opacity * kDisabledOpacityScale : opacity;
}

auto DepictionDrawContext::StandardBrightness() const -> float {
  return disabled ? brightness * kDisabledBrightnessScale : brightness;
}

void DepictionDrawContext::StandardColor(float* rgb) const {
  if (!disabled) {
    return;
  }
  float grey =
      kDisabledGreyScale * (0.3f * rgb[0] + 0.59f * rgb[1] + 0.11f * rgb[2]);
  rgb[0] = rgb[1] = rgb[2] = grey;
}

Depiction::Depiction(std::string type_id)
    : type_id_{std::move(type_id)},
      last_shown_time_{g_base->logic->display_time()} {}

Depiction::~Depiction() = default;

auto Depiction::GetAspect() const -> std::optional<float> {
  return std::nullopt;
}

auto Depiction::GetMinAspect() const -> std::optional<float> {
  return std::nullopt;
}

auto Depiction::GetContentBox(const DepictionBox& box) const -> DepictionBox {
  return box;
}

auto Depiction::SupportsHost(DepictionHost host) const -> bool { return true; }

void Depiction::Update(millisecs_t now) {}

auto Depiction::GetInput() -> DepictionInput* { return nullptr; }

auto Depiction::GetPythonControl() -> PyObject* { return nullptr; }

auto Depiction::GetTintControl() -> DepictionTintControl* { return nullptr; }

void Depiction::MarkShown() {
  last_shown_time_ = g_base->logic->display_time();
}

auto Depiction::GetIdleTime() const -> seconds_t {
  return g_base->logic->display_time() - last_shown_time_;
}

namespace {

/// What a host shows for a depiction it can't draw: an outlined box
/// with a question mark, like a browser's broken image. Says "something
/// belongs here" without pretending to be it, and fills the same box
/// the real thing would, so nothing around it shifts.
class PlaceholderDepiction : public Depiction {
 public:
  explicit PlaceholderDepiction(std::string type_id)
      : Depiction(std::move(type_id)) {
    text_group_.SetText("?", TextMesh::HAlign::kCenter,
                        TextMesh::VAlign::kCenter);
  }

  void Draw(const DepictionDrawContext& context) override {
    if (!context.transparent) {
      return;
    }
    const DepictionBox& b = context.box;
    if (b.width <= 0.0f || b.height <= 0.0f) {
      return;
    }
    float alpha = 0.4f * context.StandardOpacity();
    float bright = context.StandardBrightness();
    TextureAsset* white =
        g_base->assets->BuiltinTexture(BuiltinTextureID::kTexturesWhite);
    MeshAsset* quad =
        g_base->assets->BuiltinMesh(BuiltinMeshID::kMeshesImage1x1);

    // The outline: four thin rects just inside the box.
    float thickness = std::max(1.0f, std::min(b.width, b.height) * 0.03f);
    {
      SimpleComponent c(context.pass);
      c.SetTransparent(true);
      c.SetTexture(white);
      float cmul = white->premultiplied() ? alpha : 1.0f;
      c.SetColor(bright * cmul, bright * cmul, bright * cmul, alpha);
      auto rect = [&c, quad, &context](float x, float y, float w, float h) {
        auto xf = c.ScopedTransform();
        c.Translate(x + w * 0.5f, y + h * 0.5f, context.z);
        c.Scale(w, h, 1.0f);
        c.DrawMeshAsset(quad);
      };
      rect(b.x, b.y, b.width, thickness);
      rect(b.x, b.y + b.height - thickness, b.width, thickness);
      rect(b.x, b.y, thickness, b.height);
      rect(b.x + b.width - thickness, b.y, thickness, b.height);
      c.Submit();
    }

    // The question mark, about half the box tall. (A line of small text
    // is ~40 units tall at scale 1.)
    float scale = std::min(b.width, b.height) * 0.5f / 40.0f;
    SimpleComponent c(context.pass);
    c.SetTransparent(true);
    int elem_count = text_group_.GetElementCount();
    for (int e = 0; e < elem_count; e++) {
      TextureAsset* t = text_group_.GetElementTexture(e);
      if (!t->preloaded()) {
        continue;
      }
      c.SetTexture(t);
      float cmul = t->premultiplied() ? alpha : 1.0f;
      c.SetColor(bright * cmul, bright * cmul, bright * cmul, alpha);
      c.SetFlatness(1.0f);
      {
        auto xf = c.ScopedTransform();
        c.Translate(b.x + b.width * 0.5f, b.y + b.height * 0.5f, context.z);
        c.Scale(scale, scale, 1.0f);
        c.DrawMesh(text_group_.GetElementMesh(e));
      }
    }
    c.Submit();
  }

 private:
  TextGroup text_group_;
};

auto Factories()
    -> std::unordered_map<std::string, DepictionRegistry::Factory>& {
  static std::unordered_map<std::string, DepictionRegistry::Factory> factories;
  return factories;
}

// Warn once per kind about drawing a placeholder in its place.
void WarnPlaceholder(const std::string& type_id, const std::string& why) {
  static std::set<std::string> warned;
  if (!warned.insert(type_id).second) {
    return;
  }
  g_core->logging->Log(
      LogName::kBaUI, LogLevel::kWarning,
      "Drawing a placeholder for a '" + type_id + "' depiction: " + why
          + " Producers should only send clients depictions they can draw.");
}

}  // namespace

void DepictionRegistry::RegisterKind(const std::string& type_id,
                                     Factory factory) {
  // (Startup-time; feature sets register as their modules load, before
  // anything makes depictions.)
  Factories()[type_id] = std::move(factory);
}

auto DepictionRegistry::Create(const std::string& json, DepictionHost host,
                               const std::string& key)
    -> Object::Ref<Depiction> {
  assert(g_base->InLogicThread());
  static bool registered_base_kinds{};
  if (!registered_base_kinds) {
    registered_base_kinds = true;
    RegisterBaseDepictionKinds();
  }
  auto doc = JsonDoc::Parse(json);
  if (!doc || !doc->root().is_object()) {
    WarnPlaceholder("<invalid>", "its json is not an object.");
    return Object::New<Depiction, PlaceholderDepiction>("<invalid>");
  }
  JsonRef root = doc->root();
  auto type_id_view = root["_t"].as_string();
  std::string type_id = type_id_view ? std::string(*type_id_view) : "<none>";
  auto& factories = Factories();
  auto it = factories.find(type_id);
  if (it == factories.end()) {
    WarnPlaceholder(type_id, "this build doesn't recognize that kind.");
    return Object::New<Depiction, PlaceholderDepiction>(type_id);
  }
  // (Kinds with something costly behind them acquire it on first
  // Update, so making one only to find the host can't use it is cheap.)
  Object::Ref<Depiction> out = it->second(Source{root, json, key});
  if (!out.exists()) {
    WarnPlaceholder(type_id, "its json is unusable.");
    return Object::New<Depiction, PlaceholderDepiction>(type_id);
  }
  if (!out->SupportsHost(host)) {
    WarnPlaceholder(type_id, "this kind can't draw in this host.");
    return Object::New<Depiction, PlaceholderDepiction>(type_id);
  }
  return out;
}

}  // namespace ballistica::base
