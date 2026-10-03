// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/dynamics/bg/bg_dynamics.h"

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

}  // namespace ballistica::base
