// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_DYNAMICS_BG_BG_DYNAMICS_DRAW_SNAPSHOT_H_
#define BALLISTICA_DYNAMICS_BG_BG_DYNAMICS_DRAW_SNAPSHOT_H_

#include <vector>

#include "ballistica/graphics/renderer.h"

namespace ballistica {

// Big chunk of data sent back from the bg-dynamics server thread
// to the game thread for drawing.
class BGDynamicsDrawSnapshot {
 public:
  struct TendrilShadow {
    TendrilShadow(const Vector3f& p_in, float density_in)
        : p(p_in), density(density_in) {}
    Vector3f p;
    float density;
  };

  // These are created in the bg-dynamics thread, and object ownership
  // needs to be switched back to the game-thread default when it is passed
  // over or else the debug thread-access-checks will error.
  void SetGameThreadOwnership() {
    if (g_buildconfig.debug_build()) {
      for (Object* o : {static_cast<Object*>(tendril_indices.get()),
                        static_cast<Object*>(tendril_vertices.get()),
                        static_cast<Object*>(fuse_indices.get()),
                        static_cast<Object*>(fuse_vertices.get()),
                        static_cast<Object*>(shadow_indices.get()),
                        static_cast<Object*>(shadow_vertices.get()),
                        static_cast<Object*>(light_indices.get()),
                        static_cast<Object*>(light_vertices.get()),
                        static_cast<Object*>(spark_indices.get()),
                        static_cast<Object*>(spark_vertices.get())}) {
        if (o) {
          o->SetThreadOwnership(Object::ThreadOwnership::kClassDefault);
        }
      }
    }
  }

  // Particles.
  std::vector<Matrix44f> rocks;
  std::vector<Matrix44f> ice;
  std::vector<Matrix44f> slime;
  std::vector<Matrix44f> metal;
  std::vector<Matrix44f> sparks;
  std::vector<Matrix44f> splinters;
  std::vector<Matrix44f> sweats;
  std::vector<Matrix44f> flag_stands;

  // Tendrils.
  Object::Ref<MeshIndexBuffer16> tendril_indices;
  Object::Ref<MeshBufferVertexSmokeFull> tendril_vertices;
  std::vector<TendrilShadow> tendril_shadows;

  // Fuses.
  Object::Ref<MeshIndexBuffer16> fuse_indices;
  Object::Ref<MeshBufferVertexSimpleFull> fuse_vertices;

  // Shadows.
  Object::Ref<MeshIndexBuffer16> shadow_indices;
  Object::Ref<MeshBufferVertexSprite> shadow_vertices;

  // Lights.
  Object::Ref<MeshIndexBuffer16> light_indices;
  Object::Ref<MeshBufferVertexSprite> light_vertices;

  // Sparks.
  Object::Ref<MeshIndexBuffer16> spark_indices;
  Object::Ref<MeshBufferVertexSprite> spark_vertices;
};

}  // namespace ballistica

#endif  // BALLISTICA_DYNAMICS_BG_BG_DYNAMICS_DRAW_SNAPSHOT_H_
