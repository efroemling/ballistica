// Released under the MIT License. See LICENSE for details.

#include "ballistica/graphics/component/render_component.h"

#include "ballistica/dynamics/rigid_body.h"
#include "ballistica/graphics/graphics_server.h"

namespace ballistica {

void RenderComponent::ScissorPush(const Rect& rIn) {
  EnsureDrawing();
  cmd_buffer_->PutCommand(RenderCommandBuffer::Command::kScissorPush);
  cmd_buffer_->PutFloats(rIn.l, rIn.b, rIn.r, rIn.t);
}

#if BA_DEBUG_BUILD
void RenderComponent::ConfigForEmptyDebugChecks(bool transparent) {
  assert(InGameThread());
  if (g_graphics->drawing_opaque_only() && transparent) {
    throw Exception("Transparent component submitted in opaque-only section");
  }
  if (g_graphics->drawing_transparent_only() && !transparent) {
    throw Exception("Opaque component submitted in transparent-only section");
  }
}

void RenderComponent::ConfigForShadingDebugChecks(ShadingType shading_type) {
  assert(InGameThread());
  if (g_graphics->drawing_opaque_only()
      && Graphics::IsShaderTransparent(shading_type)) {
    throw Exception("Transparent component submitted in opaque-only section");
  }
  if (g_graphics->drawing_transparent_only()
      && !Graphics::IsShaderTransparent(shading_type)) {
    throw Exception("Opaque component submitted in transparent-only section");
  }
}
#endif  // BA_DEBUG_BUILD

void RenderComponent::TransformToBody(const RigidBody& b) {
  dBodyID body = b.body();
  dGeomID geom = b.geom();
  const dReal* pos_in;
  const dReal* r_in;
  if (b.type() == RigidBody::Type::kBody) {
    pos_in = dBodyGetPosition(body);
    r_in = dBodyGetRotation(body);
  } else {
    pos_in = dGeomGetPosition(geom);
    r_in = dGeomGetRotation(geom);
  }
  float pos[3];
  float r[12];
  for (int x = 0; x < 3; x++) {
    pos[x] = pos_in[x];
  }
  pos[0] += b.blend_offset().x;
  pos[1] += b.blend_offset().y;
  pos[2] += b.blend_offset().z;
  for (int x = 0; x < 12; x++) {
    r[x] = r_in[x];
  }
  float matrix[16];
  matrix[0] = r[0];
  matrix[1] = r[4];
  matrix[2] = r[8];
  matrix[3] = 0;
  matrix[4] = r[1];
  matrix[5] = r[5];
  matrix[6] = r[9];
  matrix[7] = 0;
  matrix[8] = r[2];
  matrix[9] = r[6];
  matrix[10] = r[10];
  matrix[11] = 0;
  matrix[12] = pos[0];
  matrix[13] = pos[1];
  matrix[14] = pos[2];
  matrix[15] = 1;
  MultMatrix(matrix);
}

}  // namespace ballistica
