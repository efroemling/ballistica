// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/graphics/mesh/nine_patch_mesh.h"

namespace ballistica::base {

NinePatchMesh::NinePatchMesh(float x, float y, float z, float width,
                             float height, float border_left,
                             float border_bottom, float border_right,
                             float border_top) {
  if (g_buildconfig.debug_build()) {
    if ((border_bottom < 0.0f || border_top < 0.0f
         || (border_bottom + border_top) > 1.0f)
        || (border_left < 0.0f || border_right < 0.0f
            || (border_left + border_right) > 1.0f)) {
      BA_LOG_ONCE(LogLevel::kWarning, "Invalid nine-patch values provided.");
    }
  }
  // Statically allocate enough for a full 9 patches even though we may
  // not use them all (in cases of size 0 borders).
  VertexSimpleFull verts[16];  // 4 vertical * 4 horizontal slices.
  uint16_t indices[54];        // 9 patches * 2 triangles * 3 verts.

  // Vertical slices.
  float y0 = y;
  float y1 = y + border_bottom * height;
  float y2 = y + (1.0 - border_top) * height;
  float y3 = y + height;
  auto v0 = 65535;
  auto v1 = 32767;
  auto v2 = 32767;
  auto v3 = 0;

  // Horizontal slices.
  float x0 = x;
  float x1 = x + border_left * width;
  float x2 = x + (1.0 - border_right) * width;
  float x3 = x + width;
  auto u0 = 0;
  auto u1 = 32767;
  auto u2 = 32767;
  auto u3 = 65535;

  // Fill out all 16 verts.
  for (int yi = 0; yi < 4; ++yi) {
    for (int xi = 0; xi < 4; ++xi) {
      VertexSimpleFull* v = verts + yi * 4 + xi;

      float xpos, ypos;
      uint16_t uval, vval;
      switch (xi) {
        case 0:
          xpos = x0;
          uval = u0;
          break;
        case 1:
          xpos = x1;
          uval = u1;
          break;
        case 2:
          xpos = x2;
          uval = u2;
          break;
        default:
          assert(xi == 3);
          xpos = x3;
          uval = u3;
      }
      switch (yi) {
        case 0:
          ypos = y0;
          vval = v0;
          break;
        case 1:
          ypos = y1;
          vval = v1;
          break;
        case 2:
          ypos = y2;
          vval = v2;
          break;
        default:
          assert(yi == 3);
          ypos = y3;
          vval = v3;
      }

      v->position[0] = xpos;
      v->position[1] = ypos;
      v->position[2] = z;
      v->uv[0] = uval;
      v->uv[1] = vval;
    }
  }

  // Now add triangle draws for any of the 9 patches with width/height > 0.
  int icount{};
  for (int yi = 0; yi < 3; ++yi) {
    for (int xi = 0; xi < 3; ++xi) {
      VertexSimpleFull* v = verts + yi * 4 + xi;
      VertexSimpleFull* vright = v + 1;
      VertexSimpleFull* vtop = v + 4;
      if (vright->position[0] > v->position[0]
          && vtop->position[1] > v->position[1]) {
        indices[icount++] = yi * 4 + xi;
        indices[icount++] = yi * 4 + xi + 1;
        indices[icount++] = (yi + 1) * 4 + xi + 1;
        indices[icount++] = yi * 4 + xi;
        indices[icount++] = (yi + 1) * 4 + xi + 1;
        indices[icount++] = (yi + 1) * 4 + xi;
      }
    }
  }
  assert(icount <= 54);
  SetIndexData(Object::New<MeshIndexBuffer16>(icount, indices));
  SetData(Object::New<MeshBuffer<VertexSimpleFull>>(16, verts));
}

}  // namespace ballistica::base
