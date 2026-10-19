// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/dynamics/bg/bg_dynamics.h"

#include <utility>

#include "ballistica/base/dynamics/bg/bg_dynamics_world.h"
#include "ballistica/base/graphics/graphics.h"
#include "ballistica/base/graphics/support/render_view.h"

namespace ballistica::base {

BGDynamics::BGDynamics() = default;

auto BGDynamics::main_world() -> BGDynamicsWorld* {
  assert(g_base->InLogicThread());

  // Made when first asked for; the bg-dynamics thread and the main
  // view both come to be after we do.
  if (!main_world_.exists()) {
    main_world_ = Object::New<BGDynamicsWorld>(g_base->graphics->main_view());
  }
  return main_world_.get();
}

auto BGDynamics::ParkMainWorld() -> Object::Ref<BGDynamicsWorld> {
  assert(g_base->InLogicThread());
  main_world();  // Make sure there is one to park.
  auto parked = std::move(main_world_);
  main_world_ = Object::New<BGDynamicsWorld>(g_base->graphics->main_view());
  return parked;
}

void BGDynamics::RestoreMainWorld(Object::Ref<BGDynamicsWorld> world) {
  assert(g_base->InLogicThread());
  assert(world.exists());
  main_world_ = std::move(world);
}

}  // namespace ballistica::base
