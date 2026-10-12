// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/graphics/mesh/nine_patch_mesh.h"

#include <cmath>
#include <optional>
#include <vector>

namespace ballistica::base {

namespace {

/// Most tiles we'll lay along one axis; keeps a huge span over tiny
/// corners from blowing past 16-bit indices.
const int kMaxTilesPerAxis{64};

/// One strip of a 9-patch along an axis: where it draws and which part
/// of the texture it shows (as fractions from the left/bottom).
struct NinePatchSegment {
  float pos0;
  float pos1;
  float tex0;
  float tex1;
};

/// The scale an axis's corners are drawn at (output units per whole
/// texture), or nothing if it has no corners to say.
auto CornerScale(float size, float border_lo, float border_hi, float src_lo,
                 float src_hi) -> std::optional<float> {
  float total{};
  int count{};
  if (src_lo > 0.0f && border_lo > 0.0f) {
    total += border_lo * size / src_lo;
    ++count;
  }
  if (src_hi > 0.0f && border_hi > 0.0f) {
    total += border_hi * size / src_hi;
    ++count;
  }
  if (count == 0) {
    return std::nullopt;
  }
  return total / static_cast<float>(count);
}

void BuildAxis(float pos, float size, float border_lo, float border_hi,
               float src_lo, float src_hi, NinePatchFill fill,
               std::optional<float> scale, std::vector<NinePatchSegment>* out) {
  float p0 = pos;
  float p1 = pos + border_lo * size;
  float p2 = pos + (1.0f - border_hi) * size;
  float p3 = pos + size;
  float t1 = src_lo;
  float t2 = 1.0f - src_hi;

  out->push_back({p0, p1, 0.0f, t1});

  float span = p2 - p1;
  float src_mid = t2 - t1;
  int tiles{1};
  if (fill == NinePatchFill::kTileFit && scale.has_value() && src_mid > 0.0f
      && span > 0.0f) {
    float tile = src_mid * *scale;
    if (tile > 0.0f) {
      tiles = std::clamp(static_cast<int>(std::lround(span / tile)), 1,
                         kMaxTilesPerAxis);
    }
  }
  float step = span / static_cast<float>(tiles);
  for (int i = 0; i < tiles; ++i) {
    float a = p1 + step * static_cast<float>(i);
    // Land the last one exactly on the far corner.
    float b = (i == tiles - 1) ? p2 : a + step;
    out->push_back({a, b, t1, t2});
  }

  out->push_back({p2, p3, t2, 1.0f});
}

auto TexToU16(float t) -> uint16_t {
  return static_cast<uint16_t>(
      std::lround(std::clamp(t, 0.0f, 1.0f) * 65535.0f));
}

}  // namespace

NinePatchMesh::NinePatchMesh(float x, float y, float z, float width,
                             float height, float border_left,
                             float border_bottom, float border_right,
                             float border_top)
    : NinePatchMesh(x, y, z, width, height, border_left, border_bottom,
                    border_right, border_top, NinePatchSourceInsets{},
                    NinePatchFill::kStretch, NinePatchFill::kStretch) {}

NinePatchMesh::NinePatchMesh(float x, float y, float z, float width,
                             float height, float border_left,
                             float border_bottom, float border_right,
                             float border_top,
                             const NinePatchSourceInsets& source,
                             NinePatchFill fill_h, NinePatchFill fill_v) {
  if (g_buildconfig.debug_build()) {
    if ((border_bottom < 0.0f || border_top < 0.0f
         || (border_bottom + border_top) > 1.0f)
        || (border_left < 0.0f || border_right < 0.0f
            || (border_left + border_right) > 1.0f)) {
      BA_LOG_ONCE(LogName::kBaGraphics, LogLevel::kWarning,
                  "Invalid nine-patch values provided.");
    }
    if ((source.bottom < 0.0f || source.top < 0.0f
         || (source.bottom + source.top) > 1.0f)
        || (source.left < 0.0f || source.right < 0.0f
            || (source.left + source.right) > 1.0f)) {
      BA_LOG_ONCE(LogName::kBaGraphics, LogLevel::kWarning,
                  "Invalid nine-patch source insets provided.");
    }
  }

  // Each axis tiles at its own corners' scale; one with no corners
  // borrows the other's.
  auto scale_h =
      CornerScale(width, border_left, border_right, source.left, source.right);
  auto scale_v =
      CornerScale(height, border_bottom, border_top, source.bottom, source.top);
  std::vector<NinePatchSegment> cols;
  std::vector<NinePatchSegment> rows;
  BuildAxis(x, width, border_left, border_right, source.left, source.right,
            fill_h, scale_h.has_value() ? scale_h : scale_v, &cols);
  BuildAxis(y, height, border_bottom, border_top, source.bottom, source.top,
            fill_v, scale_v.has_value() ? scale_v : scale_h, &rows);

  // Each patch gets its own 4 verts: tiles jump back to the start of
  // the middle region, so neighbors can't share.
  std::vector<VertexSimpleFull> verts;
  std::vector<uint16_t> indices;
  verts.reserve(cols.size() * rows.size() * 4);
  indices.reserve(cols.size() * rows.size() * 6);
  for (const auto& row : rows) {
    if (row.pos1 <= row.pos0) {
      continue;
    }
    // Texture v runs top-down; our fractions run bottom-up.
    uint16_t v0 = TexToU16(1.0f - row.tex0);
    uint16_t v1 = TexToU16(1.0f - row.tex1);
    for (const auto& col : cols) {
      if (col.pos1 <= col.pos0) {
        continue;
      }
      uint16_t u0 = TexToU16(col.tex0);
      uint16_t u1 = TexToU16(col.tex1);
      auto base = static_cast<uint16_t>(verts.size());
      verts.push_back({{col.pos0, row.pos0, z}, {u0, v0}});
      verts.push_back({{col.pos1, row.pos0, z}, {u1, v0}});
      verts.push_back({{col.pos1, row.pos1, z}, {u1, v1}});
      verts.push_back({{col.pos0, row.pos1, z}, {u0, v1}});
      for (uint16_t i : {0, 1, 2, 0, 2, 3}) {
        indices.push_back(static_cast<uint16_t>(base + i));
      }
    }
  }
  // Keep both buffers non-empty even when every patch is (a zero-size
  // box): one vertex and a degenerate triangle that draws nothing.
  if (verts.empty()) {
    verts.push_back({{x, y, z}, {0, 0}});
  }
  if (indices.empty()) {
    indices = {0, 0, 0};
  }
  assert(verts.size() <= 65536);
  SetIndexData(Object::New<MeshIndexBuffer16>(static_cast<int>(indices.size()),
                                              indices.data()));
  SetData(Object::New<MeshBuffer<VertexSimpleFull>>(
      static_cast<int>(verts.size()), verts.data()));
}

}  // namespace ballistica::base
