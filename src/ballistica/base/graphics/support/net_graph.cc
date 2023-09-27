// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/graphics/support/net_graph.h"

#include <list>

#include "ballistica/base/graphics/component/simple_component.h"

namespace ballistica::base {

class NetGraph::Impl {
 public:
  std::list<std::pair<double, float>> samples;
  double duration = 2000.0;
  double v_max_smoothed = 1.0;
  double v_smoothed = 0.0;
  bool smoothed = false;
  std::string label;
  ImageMesh bg_mesh;
  MeshIndexedSimpleFull value_mesh;
  TextGroup max_vel_text;
  millisecs_t last_used_time{};
};

NetGraph::NetGraph() : impl_(new NetGraph::Impl()) {}

NetGraph::~NetGraph() = default;

void NetGraph::SetLabel(const std::string& label) { impl_->label = label; }
void NetGraph::SetSmoothed(bool val) { impl_->smoothed = val; }

void NetGraph::SetLastUsedTime(millisecs_t real_time) {
  impl_->last_used_time = real_time;
}
auto NetGraph::LastUsedTime() -> millisecs_t { return impl_->last_used_time; }

void NetGraph::AddSample(double time, double value) {
  impl_->samples.emplace_back(time, value);
  double cutoffTime = time - impl_->duration;

  // Go ahead and prune old ones here so we don't grow out of control.
  std::list<std::pair<double, float>>::iterator i;
  for (i = impl_->samples.begin(); i != impl_->samples.end();) {
    if (i->first < cutoffTime) {
      auto i_next = i;
      ++i_next;
      impl_->samples.erase(i);
      i = i_next;
    } else {
      break;
    }
  }
}

void NetGraph::Draw(RenderPass* pass, double time, double x, double y, double w,
                    double h) {
  impl_->bg_mesh.SetPositionAndSize(
      static_cast<float>(x), static_cast<float>(y), 0.0f, static_cast<float>(w),
      static_cast<float>(h));

  int num_samples = static_cast<int>(impl_->samples.size());

  double val = 0.0;

  // Draw values (provided we have at least 2 samples)
  bool draw_values = (num_samples >= 2);
  if (draw_values) {
    double t_left = time - impl_->duration;
    double t_right = time;
    double t_width = t_right - t_left;
    double v_bottom = 0.0f;

    // Find the max y value we have and smoothly transition our bounds towards
    // that.
    double v_max = 0.0;
    for (auto&& s : impl_->samples) {
      if (s.second > v_max) {
        v_max = s.second;
      }
    }
    double smoothing = 0.95;
    val = impl_->samples.back().second;
    impl_->v_max_smoothed =
        smoothing * impl_->v_max_smoothed + (1.0 - smoothing) * v_max * 1.1;
    impl_->v_smoothed = smoothing * impl_->v_smoothed + (1.0 - smoothing) * val;

    double v_top = impl_->v_max_smoothed;
    double v_height = v_top - v_bottom;

    // We need 2 verts per sample.
    auto vertex_buffer(
        Object::New<MeshBuffer<VertexSimpleFull>>(num_samples * 2));
    VertexSimpleFull* v = vertex_buffer->elements.data();
    for (auto&& s : impl_->samples) {
      double t = s.first;
      double sval = s.second;
      double vx = x + w * ((t - t_left) / t_width);
      double vy = y + h * ((sval - v_bottom) / v_height);
      v->position[0] = static_cast<float>(vx);
      v->position[1] = static_cast<float>(y);
      v->position[2] = 0.0f;
      v->uv[0] = v->uv[1] = 0;
      v++;
      v->position[0] = static_cast<float>(vx);
      v->position[1] = static_cast<float>(vy);
      v->position[2] = 0.0f;
      v->uv[0] = v->uv[1] = 0;
      v++;
    }

    // We need 2 tris per sample (minus the last).
    auto index_buffer(Object::New<MeshIndexBuffer16>((num_samples - 1) * 6));
    uint16_t* i = index_buffer->elements.data();
    auto s = impl_->samples.begin();
    int v_count = 0;
    while (true) {
      auto s_next = s;
      ++s_next;
      if (s_next == impl_->samples.end()) {
        break;
      } else {
        *i++ = static_cast_check_fit<uint16_t>(v_count);
        *i++ = static_cast_check_fit<uint16_t>(v_count + 2);
        *i++ = static_cast_check_fit<uint16_t>(v_count + 1);
        *i++ = static_cast_check_fit<uint16_t>(v_count + 2);
        *i++ = static_cast_check_fit<uint16_t>(v_count + 3);
        *i++ = static_cast_check_fit<uint16_t>(v_count + 1);
      }
      v_count += 2;
      s = s_next;
    }
    impl_->value_mesh.SetIndexData(index_buffer);
    impl_->value_mesh.SetData(vertex_buffer);
  }

  SimpleComponent c(pass);
  c.SetTransparent(true);
  c.SetColor(0.35f, 0.0f, 0.0f, 0.9f);
  c.DrawMesh(&impl_->bg_mesh);
  c.SetColor(0.0f, 1.0f, 0.0f, 0.85f);
  if (draw_values) {
    c.DrawMesh(&impl_->value_mesh);
  }
  c.Submit();

  char val_str[32];
  if (!impl_->label.empty()) {
    snprintf(val_str, sizeof(val_str), "%s %.3f", impl_->label.c_str(),
             impl_->smoothed ? impl_->v_smoothed : val);

  } else {
    snprintf(val_str, sizeof(val_str), "%.3f",
             impl_->smoothed ? impl_->v_smoothed : val);
  }
  impl_->max_vel_text.SetText(val_str, TextMesh::HAlign::kLeft,
                              TextMesh::VAlign::kTop);

  SimpleComponent c2(pass);
  c2.SetTransparent(true);
  c2.SetColor(1, 0, 0, 1);
  {
    auto xf = c2.ScopedTransform();
    c2.Translate(static_cast<float>(x), static_cast<float>(y + h));
    float scale = static_cast<float>(h) * 0.006f;
    c2.Scale(scale, scale);
    int text_elem_count = impl_->max_vel_text.GetElementCount();
    for (int e = 0; e < text_elem_count; e++) {
      c2.SetTexture(impl_->max_vel_text.GetElementTexture(e));
      c2.SetFlatness(1.0f);
      c2.DrawMesh(impl_->max_vel_text.GetElementMesh(e));
    }
  }
  c2.Submit();
}

}  // namespace ballistica::base
