// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_DYNAMICS_BG_BG_DYNAMICS_VOLUME_LIGHT_DATA_H_
#define BALLISTICA_DYNAMICS_BG_BG_DYNAMICS_VOLUME_LIGHT_DATA_H_

#include "ballistica/dynamics/bg/bg_dynamics_server.h"

namespace ballistica {

struct BGDynamicsVolumeLightData {
  bool client_dead{};

  // Position value owned by the client.
  Vector3f pos_client{0.0f, 0.0f, 0.0f};
  float radius_client{};
  float r_client{};
  float g_client{};
  float b_client{};

  // Position value owned by the worker thread.
  Vector3f pos_worker{0.0f, 0.0f, 0.0f};
  float radius_worker{};
  float r_worker{};
  float g_worker{};
  float b_worker{};
};

}  // namespace ballistica

#endif  // BALLISTICA_DYNAMICS_BG_BG_DYNAMICS_VOLUME_LIGHT_DATA_H_
