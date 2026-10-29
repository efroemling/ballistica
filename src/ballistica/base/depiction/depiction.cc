// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/depiction/depiction.h"

#include <algorithm>
#include <cmath>
#include <set>
#include <string>
#include <unordered_map>
#include <utility>

#include "ballistica/base/assets/assets.h"
#include "ballistica/base/depiction/depiction_kinds.h"
#include "ballistica/base/graphics/component/simple_component.h"
#include "ballistica/base/graphics/graphics.h"
#include "ballistica/base/graphics/mesh/rect_outline_mesh.h"
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
    // (The host's multiplier goes over either.)
    const float* m = context.color_multiply;
    if (ergb) {
      c.SetColor(ergb[0] * cmul * m[0], ergb[1] * cmul * m[1],
                 ergb[2] * cmul * m[2], alpha);
    } else {
      float plain = cmul * brightness;
      c.SetColor(plain * m[0], plain * m[1], plain * m[2], alpha);
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

void DepictionDrawContext::StandardMultiplier(float* rgb) const {
  float b = StandardBrightness();
  for (int i = 0; i < 3; ++i) {
    rgb[i] = b * color_multiply[i];
  }
}

void DepictionDrawContext::StandardColor(float* rgb) const {
  if (!disabled) {
    return;
  }
  float grey =
      kDisabledGreyScale * (0.3f * rgb[0] + 0.59f * rgb[1] + 0.11f * rgb[2]);
  rgb[0] = rgb[1] = rgb[2] = grey;
}

void DepictionDrawContext::StandardLayerColors(float* underlay, float* layer1,
                                               float* layer2) const {
  std::copy(underlay_color, underlay_color + 4, underlay);
  std::copy(layer1_color, layer1_color + 4, layer1);
  std::copy(layer2_color, layer2_color + 4, layer2);
  StandardColor(underlay);
  StandardColor(layer1);
  StandardColor(layer2);
  // The shader takes its underlay premultiplied.
  float brightness = StandardBrightness();
  for (int i = 0; i < 3; ++i) {
    underlay[i] *= underlay[3] * brightness;
  }
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

auto Depiction::GetDebugBoundsType() const -> std::optional<DebugBoundsType> {
  return {};
}

void Depiction::DrawDebugBounds(const DepictionDrawContext& context,
                                const DepictionBox& host_box) const {
  auto type = GetDebugBoundsType();
  if (!type || !g_base->graphics->debug_bounds(*type) || !context.transparent) {
    return;
  }
  TextureAsset* white = g_base->assets->SolidTexture(SolidTextureColor::kWhite);

  // Outlines just inside each box, about a pixel and a half wide
  // whatever scale the host draws at. (Meshes made per draw; fine for
  // a debugging aid.)
  float thickness = 1.5f / std::max(0.001f, context.pixels_per_unit);
  SimpleComponent c(context.pass);
  c.SetTransparent(true);
  c.SetTexture(white);
  auto outline = [&c, &context, thickness](const DepictionBox& b) {
    auto mesh = Object::New<RectOutlineMesh>(b.x, b.y, context.z, b.width,
                                             b.height, thickness);
    c.DrawMesh(mesh.get());
  };
  // The room we have in red, then what we claim of it in green on top.
  c.SetColor(1.0f, 0.15f, 0.15f, 1.0f);
  outline(host_box);
  c.SetColor(0.2f, 1.0f, 0.3f, 1.0f);
  outline(context.box);
  c.Submit();
}

auto Depiction::SupportsHost(DepictionHost host) const -> bool { return true; }

void Depiction::Update(millisecs_t now) {}

auto Depiction::DrawsHostBacking() const -> bool { return false; }

auto Depiction::GetInput() -> DepictionInput* { return nullptr; }

auto Depiction::GetPythonControl() -> PyObject* { return nullptr; }

auto Depiction::GetTintControl() -> DepictionTintControl* { return nullptr; }

void Depiction::MarkShown() {
  last_shown_time_ = g_base->logic->display_time();
}

auto Depiction::GetIdleTime() const -> seconds_t {
  return g_base->logic->display_time() - last_shown_time_;
}

void DrawDepictionLoading(const DepictionDrawContext& context, float size) {
  if (!context.transparent) {
    return;
  }
  const DepictionBox& b = context.box;
  TextureAsset* spinner = g_base->assets->base_assets().depiction_spinner();
  if (!spinner || b.width <= 0.0f || b.height <= 0.0f) {
    return;
  }
  float alpha = 0.25f * context.StandardOpacity();
  float cmul = spinner->premultiplied() ? alpha : 1.0f;
  float mult[3];
  context.StandardMultiplier(mult);
  float side = std::min(b.width, b.height) * size;
  auto turns = static_cast<float>(
      std::fmod(static_cast<double>(g_core->AppTimeMillisecs()) / 1000.0, 1.0));
  SimpleComponent c(context.pass);
  c.SetTransparent(true);
  c.SetTexture(spinner);
  c.SetColor(cmul * mult[0], cmul * mult[1], cmul * mult[2], alpha);
  {
    auto xf = c.ScopedTransform();
    c.Translate(b.x + b.width * 0.5f, b.y + b.height * 0.5f, context.z);
    c.Scale(side, side, 1.0f);
    c.Rotate(-360.0f * turns, 0.0f, 0.0f, 1.0f);
    c.DrawMeshAsset(
        g_base->assets->BuiltinMesh(BuiltinMeshID::kMeshesImage1x1));
  }
  c.Submit();
}

DepictionPlaceholder::DepictionPlaceholder()
    : text_group_{Object::New<TextGroup>()} {
  text_group_->SetText("?", TextMesh::HAlign::kCenter,
                       TextMesh::VAlign::kCenter);
}

DepictionPlaceholder::~DepictionPlaceholder() = default;

void DepictionPlaceholder::Draw(const DepictionDrawContext& context) {
  if (!context.transparent) {
    return;
  }
  DepictionBox b = context.box;
  if (b.width <= 0.0f || b.height <= 0.0f) {
    return;
  }
  if (context.small_placeholder) {
    // A third of the shorter side: big enough to read as something
    // broken, small enough not to read as the pane's frame.
    float side = std::min(b.width, b.height) / 3.0f;
    b = {b.x + (b.width - side) * 0.5f, b.y + (b.height - side) * 0.5f, side,
         side};
  }
  float alpha = 0.4f * context.StandardOpacity();
  float mult[3];
  context.StandardMultiplier(mult);
  TextureAsset* white = g_base->assets->SolidTexture(SolidTextureColor::kWhite);

  // The outline, just inside the box (remade only when the box moves;
  // we draw every frame).
  float thickness = std::max(1.0f, std::min(b.width, b.height) * 0.03f);
  if (!outline_.exists() || b.x != outline_box_.x || b.y != outline_box_.y
      || b.width != outline_box_.width || b.height != outline_box_.height
      || context.z != outline_z_) {
    outline_ = Object::New<RectOutlineMesh>(b.x, b.y, context.z, b.width,
                                            b.height, thickness);
    outline_box_ = b;
    outline_z_ = context.z;
  }
  {
    SimpleComponent c(context.pass);
    c.SetTransparent(true);
    c.SetTexture(white);
    float cmul = white->premultiplied() ? alpha : 1.0f;
    c.SetColor(mult[0] * cmul, mult[1] * cmul, mult[2] * cmul, alpha);
    c.DrawMesh(outline_.get());
    c.Submit();
  }

  // The question mark, about half the box tall. (A line of small text
  // is ~40 units tall at scale 1.)
  float scale = std::min(b.width, b.height) * 0.5f / 40.0f;
  SimpleComponent c(context.pass);
  c.SetTransparent(true);
  int elem_count = text_group_->GetElementCount();
  for (int e = 0; e < elem_count; e++) {
    TextureAsset* t = text_group_->GetElementTexture(e);
    if (!t->preloaded()) {
      continue;
    }
    c.SetTexture(t);
    float cmul = t->premultiplied() ? alpha : 1.0f;
    c.SetColor(mult[0] * cmul, mult[1] * cmul, mult[2] * cmul, alpha);
    c.SetFlatness(1.0f);
    {
      auto xf = c.ScopedTransform();
      c.Translate(b.x + b.width * 0.5f, b.y + b.height * 0.5f, context.z);
      c.Scale(scale, scale, 1.0f);
      c.DrawMesh(text_group_->GetElementMesh(e));
    }
  }
  c.Submit();
}

namespace {

/// What a host shows for a depiction it can't draw (see
/// DepictionPlaceholder).
class PlaceholderDepiction : public Depiction {
 public:
  explicit PlaceholderDepiction(std::string type_id)
      : Depiction(std::move(type_id)) {}

  void Draw(const DepictionDrawContext& context) override {
    placeholder_.Draw(context);
  }

 private:
  DepictionPlaceholder placeholder_;
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
  // Any kind's json can carry a baked color override ([r, g, b]).
  if (JsonRef arr = root["co"]; arr.is_array() && arr.size() == 3) {
    float rgb[3];
    for (size_t i = 0; i < 3; ++i) {
      auto val = arr[i].as_double();
      rgb[i] = std::clamp(static_cast<float>(val ? *val : 0.0), 0.0f, 2.0f);
    }
    out->SetColorOverride(rgb);
  }
  // Likewise baked team coloring.
  if (auto val = root["tco"].as_bool(); val && *val) {
    out->set_team_coloring(true);
  }
  return out;
}

}  // namespace ballistica::base
