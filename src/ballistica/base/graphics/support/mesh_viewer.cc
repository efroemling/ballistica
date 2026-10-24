// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/graphics/support/mesh_viewer.h"

#include <algorithm>
#include <cmath>
#include <string>
#include <tuple>
#include <utility>
#include <variant>
#include <vector>

#include "ballistica/base/assets/assets.h"
#include "ballistica/base/assets/mesh_asset.h"
#include "ballistica/base/assets/texture_asset.h"
#include "ballistica/base/graphics/component/object_component.h"
#include "ballistica/base/graphics/support/fixed_camera.h"
#include "ballistica/base/graphics/support/frame_def.h"
#include "ballistica/base/graphics/support/render_view.h"
#include "ballistica/base/logic/logic.h"
#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging.h"
#include "ballistica/shared/generic/json_facade.h"

namespace ballistica::base {

namespace {

// Framing and motion, as bamaster's browser mesh preview does them
// (bamaster_mesh_preview.ts): everything seen from this many of its
// radii back, this wide, starting this far above.
const float kCameraDistance{3.6f};
const float kFieldOfViewY{36.0f};  // Degrees (0.2 pi).
const float kStartPitch{0.5f};     // Radians, looking down.
const float kSpinRate{0.7f};       // Radians per second.

// Dragging can tilt the camera to just short of straight above or
// below (straight on, its up direction would be undefined).
const float kMaxPitch{1.55f};

// Our near clip never comes closer than this share of our far one. It
// only comes into it with our camera within something's bounds (else
// the near clip sits at the nearest bounds), and depth buffers can be
// 16 bits, which loses too much precision far out much below this.
const float kMinNearClipRatio{0.01f};

const float kPi{3.14159265358979f};
// Read exactly ``count`` finite numbers into ``out``.
auto ReadFloats(const JsonRef& obj, const char* key, size_t count, float* out)
    -> bool {
  JsonRef arr = obj[key];
  if (!arr.is_array() || arr.size() != count) {
    return false;
  }
  for (size_t i = 0; i < count; ++i) {
    auto val = arr[i].as_double();
    if (!val || !std::isfinite(*val)) {
      return false;
    }
    out[i] = static_cast<float>(*val);
  }
  return true;
}

auto ReadVector(const JsonRef& obj, const char* key, Vector3f* out) -> bool {
  float vals[3]{};
  if (!ReadFloats(obj, key, 3, vals)) {
    return false;
  }
  *out = {vals[0], vals[1], vals[2]};
  return true;
}

}  // namespace

/// Our view: a texture view whose world is our meshes.
class MeshViewer::View : public RenderView {
 public:
  View(MeshViewer* viewer, Camera* camera, int width, int height)
      : RenderView(camera, width, height), viewer_(viewer) {}

  void PrepareFrame(FrameDef* frame_def) override {
    if (MeshViewer* viewer = viewer_.get()) {
      viewer->PrepareFrame_(frame_def);
    }
  }

  void DrawWorld(FrameDef* frame_def) override {
    if (MeshViewer* viewer = viewer_.get()) {
      viewer->Draw_(frame_def);
    }
  }

 private:
  Object::WeakRef<MeshViewer> viewer_;
};

MeshViewer::MeshViewer(int width, int height) {
  assert(g_base->InLogicThread());
  camera_ = Object::New<FixedCamera>();
  pitch_ = kStartPitch;
  UpdateCamera_();
  auto [fit_width, fit_height] = FitSize_(width, height);
  view_ = Object::New<View>(this, camera_.get(), fit_width, fit_height);
  view_->set_max_quality(GraphicsQuality::kMedium);
  // The character viewer's mild vignette. (A view's default is the
  // strongest there is: the object shader darkens by up to all of a
  // color toward the edges, a stark radial gradient.)
  view_->set_vignette_outer({0.57f, 0.57f, 0.57f});
  view_->set_vignette_inner({0.9f, 0.9f, 0.9f});
}

MeshViewer::~MeshViewer() = default;

auto MeshViewer::view() const -> RenderView* {
  assert(view_.exists());
  return view_.get();
}

auto MeshViewer::FitSize_(int width, int height) -> std::pair<int, int> {
  width = std::max(width, 1);
  height = std::max(height, 1);
  int largest = std::max(width, height);
  if (largest > kMaxSize) {
    const double scale = static_cast<double>(kMaxSize) / largest;
    width =
        std::clamp(static_cast<int>(std::round(width * scale)), 1, kMaxSize);
    height =
        std::clamp(static_cast<int>(std::round(height * scale)), 1, kMaxSize);
  }
  return {width, height};
}

void MeshViewer::SetSize(int width, int height) {
  assert(g_base->InLogicThread());
  std::tie(width, height) = FitSize_(width, height);
  if (width != view_->width() || height != view_->height()) {
    view_->SetSize(width, height);
  }
}

auto MeshViewer::SetDepiction(const std::string& json) -> bool {
  assert(g_base->InLogicThread());
  if (json == json_) {
    return !entries_.empty();
  }
  json_ = json;
  entries_.clear();
  packages_.clear();
  domain_digest_.clear();
  block_ = MediaBlock();
  pacer_ = MediaRetryPacer();

  float old_yaw = start_yaw_;
  float old_pitch = start_pitch_;
  std::optional<ManualCamera> old_camera = manual_camera_;
  failure_ = Parse_(json);
  if (!failure_.empty()) {
    entries_.clear();
  }
  // A moving camera starts its motion over only if it changed.
  if (manual_camera_ != old_camera) {
    camera_time_ = 0.0;
  }
  // Take up a new starting pose -- but an update leaving it as it was
  // (an editor's draft, say) keeps however far it's been dragged.
  // (One that can't be dragged is always exactly its pose.)
  if (!have_pose_ || start_yaw_ != old_yaw || start_pitch_ != old_pitch
      || !draggable_) {
    have_pose_ = true;
    user_yaw_ = start_yaw_;
    pitch_ = start_pitch_;
  }
  // Held still, it shows exactly its starting turn, not wherever an
  // earlier spin left off.
  if (!spin_) {
    spin_angle_ = 0.0f;
  }
  UpdateCamera_();
  // The character viewer's hand-held wobble (see
  // bascenev1lib.characterviewer), scaled. By default only a set shot
  // (a hand-placed camera) wobbles; framed turntables hold still.
  // (Both amounts clamp to 0..10.)
  const float shake = std::clamp(
      camera_shake_ ? *camera_shake_ : (manual_camera_ ? 1.0f : 0.0f), 0.0f,
      10.0f);
  camera_->SetShake(1.3f * shake, 100.0f, 2.0f, 0.15f, 1.0f);
  // Turning the device turns our view around what we're looking at:
  // a generous swing when we frame things (it reads as turning them in
  // hand), a subtler one for a set shot (the character viewer's; see
  // bascenev1lib.characterviewer).
  camera_->set_tilt_orbit(std::clamp(camera_gyro_, 0.0f, 10.0f)
                          * (manual_camera_ ? 0.2f : 0.6f));
  view_->set_clear_color(background_ ? *background_ : default_background_);
  UpdateTransparent_();
  return failure_.empty();
}

auto MeshViewer::ParseCamera_(const JsonRef& cam)
    -> std::variant<std::optional<ManualCamera>, std::string> {
  if (!cam.is_object()) {
    return std::string("Its camera ('cam') is not an object.");
  }
  // A pose: a position ('p') and target ('t') of 3 numbers each and a
  // field of view ('f') in degrees.
  auto read_pose = [](const JsonRef& obj, const std::string& what,
                      CameraPose* pose) -> std::string {
    auto fov = obj["f"].as_double();
    if (!obj.is_object() || !ReadVector(obj, "p", &pose->position)
        || !ReadVector(obj, "t", &pose->target) || !fov || !std::isfinite(*fov)
        || *fov <= 0.0 || *fov >= 180.0) {
      return what
             + " needs a position ('p') and target ('t') of 3 numbers each"
               " and a field of view ('f') between 0 and 180.";
    }
    if ((pose->target - pose->position).Length() < 1.0e-5f) {
      return what + " looks from its target to itself.";
    }
    pose->fov_y = static_cast<float>(*fov);
    return {};
  };

  ManualCamera manual;
  // No kind given is a still camera (the only kind there once was).
  JsonRef kind = cam["_t"];
  std::string kind_name =
      kind.exists() ? std::string(kind.as_string().value_or("")) : "s";
  if (kind_name == "s") {
    auto error = read_pose(cam, "Its camera ('cam')", &manual.a);
    if (!error.empty()) {
      return error;
    }
    return manual;
  }
  if (kind_name == "pp") {
    CameraPose b;
    for (auto [key, pose] : {std::pair{"a", &manual.a}, std::pair{"b", &b}}) {
      auto error = read_pose(
          cam[key], std::string("Its camera's pose '") + key + "' ('cam')",
          pose);
      if (!error.empty()) {
        return error;
      }
    }
    manual.b = b;
    auto travel = cam["d"].as_double();
    if (!travel || !std::isfinite(*travel) || *travel <= 0.0) {
      return std::string(
          "Its camera's travel time ('cam' 'd') is not a positive number.");
    }
    manual.travel_time = static_cast<float>(*travel);
    if (cam["l"].exists()) {
      auto loop = cam["l"].as_bool();
      if (!loop) {
        return std::string("Its camera's loop ('cam' 'l') is not a bool.");
      }
      manual.loop = *loop;
    }
    return manual;
  }
  // A kind newer than us (or 'u', one our Python side didn't know).
  return std::optional<ManualCamera>{};
}

auto MeshViewer::ManualPose_() const -> CameraPose {
  assert(manual_camera_);
  const ManualCamera& cam = *manual_camera_;
  if (!cam.b) {
    return cam.a;
  }
  // One smooth sine wave: a to b and back every two travel times (or,
  // not looping, its first half: a to b and stop).
  const double legs = camera_time_ / cam.travel_time;
  const double phase = (cam.loop ? std::fmod(legs, 2.0) : std::min(legs, 1.0))
                       * static_cast<double>(kPi);
  const auto u = static_cast<float>(0.5 - 0.5 * std::cos(phase));
  const CameraPose& a = cam.a;
  const CameraPose& b = *cam.b;
  CameraPose pose;
  pose.position = a.position + (b.position - a.position) * u;
  pose.target = a.target + (b.target - a.target) * u;
  pose.fov_y = a.fov_y + (b.fov_y - a.fov_y) * u;
  // (Passing through its own target would leave no direction to look:
  // look the way it started instead.)
  if ((pose.target - pose.position).Length() < 1.0e-5f) {
    pose.target = pose.position + (a.target - a.position);
  }
  return pose;
}

auto MeshViewer::Parse_(const std::string& json) -> std::string {
  background_.reset();
  spin_ = true;
  draggable_ = true;
  bounds_scale_ = 1.0f;
  start_yaw_ = 0.0f;
  start_pitch_ = kStartPitch;
  manual_camera_.reset();
  camera_shake_.reset();
  camera_gyro_ = 1.0f;
  auto doc = JsonDoc::Parse(json);
  if (!doc || !doc->root().is_object()) {
    return "Its json is not an object.";
  }
  JsonRef root = doc->root();
  ReadPackageManifest(root, &packages_, &domain_digest_);
  if (auto spin = root["sp"].as_bool()) {
    spin_ = *spin;
  }
  if (auto draggable = root["dr"].as_bool()) {
    draggable_ = *draggable;
  }
  if (root["bs"].exists()) {
    auto bounds_scale = root["bs"].as_double();
    if (!bounds_scale || !std::isfinite(*bounds_scale)
        || *bounds_scale <= 0.0) {
      return "Its bounds scale ('bs') is not a positive number.";
    }
    bounds_scale_ = static_cast<float>(*bounds_scale);
  }
  // Starting turn and camera height, in degrees on the wire.
  for (auto [key, out] :
       {std::pair{"vy", &start_yaw_}, std::pair{"vp", &start_pitch_}}) {
    if (root[key].exists()) {
      auto degrees = root[key].as_double();
      if (!degrees || !std::isfinite(*degrees)) {
        return std::string("Its '") + key + "' is not a number.";
      }
      *out = static_cast<float>(*degrees) * kPi / 180.0f;
    }
  }
  start_pitch_ = std::clamp(start_pitch_, -kMaxPitch, kMaxPitch);
  if (root["cam"].exists()) {
    auto camera = ParseCamera_(root["cam"]);
    if (auto* error = std::get_if<std::string>(&camera)) {
      return *error;
    }
    // (None for a kind we don't know: we frame things ourselves.)
    manual_camera_ = std::get<std::optional<ManualCamera>>(camera);
  }
  if (root["cs"].exists()) {
    auto shake = root["cs"].as_double();
    if (!shake || !std::isfinite(*shake)) {
      return "Its camera shake ('cs') is not a number.";
    }
    camera_shake_ = static_cast<float>(*shake);
  }
  if (root["cg"].exists()) {
    auto gyro = root["cg"].as_double();
    if (!gyro || !std::isfinite(*gyro)) {
      return "Its camera gyro ('cg') is not a number.";
    }
    camera_gyro_ = static_cast<float>(*gyro);
  }
  if (root["bg"].exists()) {
    Vector3f bg;
    if (!ReadVector(root, "bg", &bg)) {
      return "Its background color ('bg') is not 3 numbers.";
    }
    background_ = bg;
  }
  JsonRef entries = root["e"];
  if (!entries.is_array() || entries.size() == 0) {
    return "It has no entries ('e').";
  }
  for (size_t i = 0; i < entries.size(); ++i) {
    std::string where = "Entry " + std::to_string(i) + ": ";
    JsonRef obj = entries[i];
    if (!obj.is_object()) {
      return where + "not an object.";
    }
    Entry entry;
    if (!ReadPackageAssetRef(obj, "m", &entry.mesh)) {
      return where + "no usable mesh ref ('m').";
    }
    // (All optional; untextured meshes draw in their color alone.)
    for (auto [key, ref, what] :
         {std::tuple{"t", &entry.texture, "texture"},
          std::tuple{"rf", &entry.reflection, "reflection cube map"},
          std::tuple{"tt", &entry.tint_texture, "tint texture"}}) {
      if (obj[key].exists() && !ReadPackageAssetRef(obj, key, ref)) {
        return where + "unusable " + what + " ref ('" + key + "').";
      }
    }
    for (const auto* ref : {&entry.mesh, &entry.texture, &entry.reflection,
                            &entry.tint_texture}) {
      if (ref->index >= 0 && packages_.empty()) {
        return where + "an indexed ref but no package manifest ('pk').";
      }
    }
    if (obj["c"].exists() && !ReadFloats(obj, "c", 4, entry.color)) {
      return where + "its color ('c') is not 4 numbers.";
    }
    if (auto transparent = obj["tr"].as_bool()) {
      entry.transparent = *transparent;
    }
    if (obj["rs"].exists()
        && !ReadFloats(obj, "rs", 3, entry.reflection_scale)) {
      return where + "its reflection scale ('rs') is not 3 numbers.";
    }
    for (auto [key, out] : {std::pair{"tc1", entry.tint_colors[0]},
                            std::pair{"tc2", entry.tint_colors[1]},
                            std::pair{"tc3", entry.tint_colors[2]}}) {
      if (obj[key].exists() && !ReadFloats(obj, key, 3, out)) {
        return where + "'" + key + "' is not 3 numbers.";
      }
    }
    // No shading both blends and tints; blending wins.
    if (entry.transparent && entry.tint_texture.present()) {
      if (!warned_tint_blend_) {
        warned_tint_blend_ = true;
        g_core->logging->Log(
            LogName::kBaGraphics, LogLevel::kWarning,
            "Mesh viewer: entry " + std::to_string(i)
                + " is both transparent and tinted, which can't be drawn"
                  " together; drawing it blended, untinted.");
      }
      entry.tint_texture = {};
    }
    for (auto [key, out] :
         {std::pair{"p", &entry.position}, std::pair{"r", &entry.rotation},
          std::pair{"s", &entry.scale}}) {
      if (obj[key].exists() && !ReadVector(obj, key, out)) {
        return where + "'" + key + "' is not 3 numbers.";
      }
    }
    entries_.push_back(std::move(entry));
  }
  return {};
}

auto MeshViewer::failure() const -> std::string {
  if (!failure_.empty()) {
    return failure_;
  }
  return block_.failed() ? block_.failure() : std::string();
}

void MeshViewer::SetDefaultBackground(const Vector3f& color) {
  assert(g_base->InLogicThread());
  default_background_ = color;
  if (!background_) {
    view_->set_clear_color(color);
  }
}

void MeshViewer::SetTransparent(bool transparent) {
  assert(g_base->InLogicThread());
  transparent_ = transparent;
  UpdateTransparent_();
}

void MeshViewer::UpdateTransparent_() {
  // A background our depiction asks for is drawn whatever our host
  // would like.
  view_->set_transparent(transparent_ && !background_);
}

void MeshViewer::Orbit(float dx, float dy) {
  assert(g_base->InLogicThread());
  if (!draggable_) {
    return;
  }
  // A full width across is half a turn, both ways; vertical motion is
  // measured in widths too, so a drag turns as far whichever way it
  // goes. Dragging down raises the camera (the surface facing us
  // follows the pointer).
  float aspect = static_cast<float>(view_->height())
                 / static_cast<float>(std::max(1, view_->width()));
  user_yaw_ += dx * kPi;
  // (A camera placed by hand stays put; only the turntable turns.)
  if (manual_camera_) {
    return;
  }
  pitch_ = std::clamp(pitch_ - dy * aspect * kPi, -kMaxPitch, kMaxPitch);
  UpdateCamera_();
}

void MeshViewer::UpdateCamera_() {
  if (manual_camera_) {
    const CameraPose cam = ManualPose_();
    camera_->set_position(cam.position);
    camera_->set_target(cam.target);
    camera_->set_field_of_view_y(cam.fov_y);
    // (Its field of view is what was asked for, whatever our shape.)
    camera_->set_min_field_of_view_x(0.0f);
    return;
  }
  camera_->set_field_of_view_y(kFieldOfViewY);
  // Never narrower across than up and down, so a tall, thin picture
  // shrinks what it shows rather than cutting off its sides.
  camera_->set_min_field_of_view_x(kFieldOfViewY);
  // Back far enough to frame it all (well, a sphere bounds scale times
  // its size), looking at its middle.
  const Vector3f center = have_fit_ ? fit_.center : Vector3f(0.0f, 0.0f, 0.0f);
  const float dist =
      kCameraDistance * (have_fit_ ? fit_.radius : 1.0f) * bounds_scale_;
  camera_->set_position(
      center + Vector3f(0.0f, dist * sinf(pitch_), dist * cosf(pitch_)));
  camera_->set_target(center);
}

auto MeshViewer::Pivot_() const -> Vector3f {
  if (manual_camera_ || !have_fit_) {
    return {0.0f, 0.0f, 0.0f};
  }
  return fit_.center;
}

void MeshViewer::UpdateClip_() {
  // Each thing as it is turned right now; our camera fits its clip range
  // to them each frame from exactly where it ends up looking (gyro and
  // shake included), so as much depth precision as there can be goes
  // to what's there.
  const Vector3f pivot = Pivot_();
  const float turn_degrees = (spin_angle_ + user_yaw_) * 180.0f / kPi;
  const Matrix44f turn =
      Matrix44fTranslate(-pivot.x, -pivot.y, -pivot.z)
      * Matrix44fRotate(Vector3f(0.0f, 1.0f, 0.0f), turn_degrees)
      * Matrix44fTranslate(pivot);
  std::vector<FixedCamera::ClipSphere> spheres;
  spheres.reserve(fit_.spheres.size());
  for (const Sphere& s : fit_.spheres) {
    spheres.push_back({turn * s.center, s.radius});
  }
  if (spheres.empty()) {
    // Nothing with bounds (or not here yet): plenty either way of where
    // we look at.
    const float dist =
        std::max(1.0f, (camera_->target() - camera_->GetPosition()).Length());
    camera_->SetClip(dist * 0.1f, dist * 10.0f);
  }
  camera_->SetClipSpheres(std::move(spheres), kMinNearClipRatio);
}

void MeshViewer::UpdateMedia_() {
  if (entries_.empty() || block_.ready()) {
    return;
  }
  auto now = static_cast<millisecs_t>(g_base->logic->display_time() * 1000.0);
  if (!pacer_.Due(block_.pending(), now)) {
    return;
  }
  std::vector<const PackageAssetRef*> required;
  std::vector<MediaBlock::IndexedRef> indexed;
  for (auto& entry : entries_) {
    required.push_back(&entry.mesh);
    MediaBlock::NoteIndexed(&entry.mesh, "meshes/", &indexed);
    // (Cube maps live among a package's textures.)
    for (auto* ref : {&entry.texture, &entry.reflection, &entry.tint_texture}) {
      if (ref->present()) {
        required.push_back(ref);
        MediaBlock::NoteIndexed(ref, "textures/", &indexed);
      }
    }
  }
  block_.Load(
      packages_, domain_digest_, indexed, required, [this](MediaGetter* get) {
        for (auto& entry : entries_) {
          entry.mesh_asset = get->Mesh(entry.mesh);
          if (entry.texture.present()) {
            entry.texture_asset = get->Texture(entry.texture);
          }
          if (entry.reflection.present()) {
            entry.reflection_asset = get->CubeMapTexture(entry.reflection);
          }
          if (entry.tint_texture.present()) {
            entry.tint_texture_asset = get->Texture(entry.tint_texture);
          }
        }
      });
  if (block_.CheckPending()) {
    // Everything's here; frame it (at once: easing over from whatever
    // we showed before just reads as a zoom).
    fit_ = CalcFit_();
    have_fit_ = true;
    UpdateCamera_();
  }
}

void MeshViewer::ApplyEntryTransform_(const Entry& entry, RenderComponent* c) {
  c->Translate(entry.position.x, entry.position.y, entry.position.z);
  c->Rotate(entry.rotation.z, 0.0f, 0.0f, 1.0f);
  c->Rotate(entry.rotation.y, 0.0f, 1.0f, 0.0f);
  c->Rotate(entry.rotation.x, 1.0f, 0.0f, 0.0f);
  c->Scale(entry.scale.x, entry.scale.y, entry.scale.z);
}

auto MeshViewer::CalcFit_() const -> Fit {
  // Each entry's mesh as a sphere (its bounds' center and radius)
  // carried through the entry's placement; then a sphere holding all
  // of those, about the middle of their combined box. (The same
  // framing the browser preview does per vertex, from data meshes
  // carry with them.)
  Fit fit;
  std::vector<Sphere>& spheres = fit.spheres;
  for (const auto& entry : entries_) {
    if (!entry.mesh_asset.exists() || !entry.mesh_asset->bounds()) {
      continue;
    }
    const MeshAsset::Bounds& bounds = *entry.mesh_asset->bounds();
    Matrix44f xf =
        Matrix44fScale(entry.scale)
        * Matrix44fRotate(Vector3f(1.0f, 0.0f, 0.0f), entry.rotation.x)
        * Matrix44fRotate(Vector3f(0.0f, 1.0f, 0.0f), entry.rotation.y)
        * Matrix44fRotate(Vector3f(0.0f, 0.0f, 1.0f), entry.rotation.z)
        * Matrix44fTranslate(entry.position);
    float scale = std::max({std::abs(entry.scale.x), std::abs(entry.scale.y),
                            std::abs(entry.scale.z)});
    spheres.push_back({xf * bounds.center(), bounds.radius * scale});
  }
  if (spheres.empty()) {
    return fit;
  }
  Vector3f lo = spheres[0].center;
  Vector3f hi = spheres[0].center;
  for (const auto& s : spheres) {
    lo.x = std::min(lo.x, s.center.x - s.radius);
    lo.y = std::min(lo.y, s.center.y - s.radius);
    lo.z = std::min(lo.z, s.center.z - s.radius);
    hi.x = std::max(hi.x, s.center.x + s.radius);
    hi.y = std::max(hi.y, s.center.y + s.radius);
    hi.z = std::max(hi.z, s.center.z + s.radius);
  }
  fit.center = (lo + hi) * 0.5f;
  float radius{};
  for (const auto& s : spheres) {
    radius = std::max(radius, (s.center - fit.center).Length() + s.radius);
  }
  // (A point, or near enough: frame it as a unit's worth.)
  fit.radius = radius > 1.0e-6f ? radius : 1.0f;
  return fit;
}

void MeshViewer::PrepareFrame_(FrameDef* frame_def) {
  UpdateMedia_();

  // We turn only while drawn: time unseen doesn't count.
  double now = frame_def->display_time();
  if (last_draw_time_ >= 0.0) {
    auto elapsed = static_cast<float>(std::min(now - last_draw_time_, 0.1));
    if (spin_) {
      spin_angle_ = std::fmod(spin_angle_ + elapsed * kSpinRate, 2.0f * kPi);
    }
    // A moving hand-placed camera moves on (it waits for its media,
    // so it always starts out from its first pose).
    // (Not looping, it's done once it gets there.)
    if (manual_camera_ && manual_camera_->b && have_fit_
        && (manual_camera_->loop
            || camera_time_ < manual_camera_->travel_time)) {
      camera_time_ += elapsed;
      UpdateCamera_();
    }
  }
  last_draw_time_ = now;

  // (Our camera is applied to the frame next, then we draw.)
  UpdateClip_();
}

void MeshViewer::Draw_(FrameDef* frame_def) {
  if (!block_.ready() || !have_fit_) {
    return;
  }
  float turn_degrees = (spin_angle_ + user_yaw_) * 180.0f / kPi;
  // Solid entries first, then blended ones over them.
  for (bool transparent : {false, true}) {
    for (const auto& entry : entries_) {
      if (entry.transparent == transparent) {
        DrawEntry_(entry, frame_def, turn_degrees);
      }
    }
  }
}

void MeshViewer::DrawEntry_(const Entry& entry, FrameDef* frame_def,
                            float turn_degrees) {
  ObjectComponent c(frame_def->beauty_pass());
  // (Untextured, a white one: just the color.)
  c.SetTexture(entry.texture_asset.exists()
                   ? entry.texture_asset.get()
                   : g_base->assets->SolidTexture(SolidTextureColor::kWhite));
  c.SetColor(entry.color[0], entry.color[1], entry.color[2], entry.color[3]);
  TextureAsset* reflection = entry.reflection_asset.get();
  const float* reflection_scale = entry.reflection_scale;
  if (entry.transparent) {
    c.SetTransparent(true);
    // No shading blends and reflects with the light/shadow term, which
    // is neutral here anyway (we run no light pass).
    c.SetLightShadow(LightShadowType::kNone);
  } else if (entry.tint_texture_asset.exists()) {
    // (Parsing dropped any tint on blended entries.)
    c.SetColorizeTexture(entry.tint_texture_asset.get());
    const auto& tc = entry.tint_colors;
    c.SetColorizeColor(tc[0][0], tc[0][1], tc[0][2]);
    c.SetColorizeColor2(tc[1][0], tc[1][1], tc[1][2]);
    c.SetColorizeColor3(tc[2][0], tc[2][1], tc[2][2]);
    // Only reflecting shadings tint; with nothing to reflect, reflect
    // black (reflections add, so that's none).
    if (reflection == nullptr) {
      static const float kNoScale[3]{0.0f, 0.0f, 0.0f};
      reflection =
          g_base->assets->SolidCubeMapTexture(SolidTextureColor::kBlack);
      reflection_scale = kNoScale;
    }
  }
  if (reflection != nullptr) {
    c.SetReflectionCubeMap(reflection);
    c.SetReflectionScale(reflection_scale[0], reflection_scale[1],
                         reflection_scale[2]);
  }
  {
    auto xf = c.ScopedTransform();
    // Everything stays where (and the size) the depiction put it, but
    // for the turntable's turn about its pivot.
    const Vector3f pivot = Pivot_();
    c.Translate(pivot.x, pivot.y, pivot.z);
    c.Rotate(turn_degrees, 0.0f, 1.0f, 0.0f);
    c.Translate(-pivot.x, -pivot.y, -pivot.z);
    ApplyEntryTransform_(entry, &c);
    c.DrawMeshAsset(entry.mesh_asset.get());
  }
  c.Submit();
}

}  // namespace ballistica::base
