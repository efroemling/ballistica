// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/dynamics/bg/bg_dynamics_server.h"

#include <algorithm>
#include <cstdlib>

#include "ballistica/core/core.h"
#include "ballistica/shared/foundation/event_loop.h"

namespace ballistica::base {

BGDynamicsServer::BGDynamicsServer() {
  // Solver iterations: the light world default; character rigs hint
  // their own bodies up to the main sim's count and ODE solves per
  // island (see kBGSolverIterations). BA_BG_QUICKSTEP_ITERS
  // (test_game_run --bg-solver-iters) pins everything to one count for
  // perf/quality trade-off runs.
  if (const char* v = getenv("BA_BG_QUICKSTEP_ITERS")) {
    solver_iters_override_ = std::max(1, atoi(v));
  }
  profile_ = (getenv("BA_DYNAMICS_PROFILE") != nullptr);
}

void BGDynamicsServer::OnMainThreadStartApp() {
  // Spin up our thread.
  event_loop_ = new EventLoop(EventLoopID::kBGDynamics);
  g_core->suspendable_event_loops.push_back(event_loop_);
}

}  // namespace ballistica::base
