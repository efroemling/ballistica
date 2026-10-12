// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_DYNAMICS_BG_BG_DYNAMICS_SERVER_H_
#define BALLISTICA_BASE_DYNAMICS_BG_BG_DYNAMICS_SERVER_H_

#include "ballistica/base/base.h"

namespace ballistica::base {

// ODE quickstep iteration counts for bg worlds: the light count a
// world runs by default (debris, and anything else that doesn't ask),
// and the main sim's count, which character rigs (limbs, attachments)
// set on their own bodies so just their islands solve harder (see
// BGDynamicsServer::character_solver_iterations and the per-body hint
// in the ODE fork, dBodySetSolverIterations).
const int kBGSolverIterations = 3;
const int kBGSolverIterationsCharacter = 10;

/// The bg-dynamics thread and what all bg worlds have in common.
///
/// There is one of us. The simulating is done by worlds
/// (BGDynamicsWorldServer), of which there can be any number, each the
/// far side of a logic-thread BGDynamicsWorld; they all run here on our
/// one thread, taking their steps in the order they were fed.
class BGDynamicsServer {
 public:
  BGDynamicsServer();
  void OnMainThreadStartApp();

  auto event_loop() const -> EventLoop* { return event_loop_; }

  /// The quickstep iteration count worlds run at unless a body hints
  /// otherwise (kBGSolverIterations, or the BA_BG_QUICKSTEP_ITERS pin).
  auto solver_iterations() const -> int {
    return solver_iters_override_ > 0 ? solver_iters_override_
                                      : kBGSolverIterations;
  }

  /// The quickstep iteration hint character rigs put on their bodies
  /// (kBGSolverIterationsCharacter, or the BA_BG_QUICKSTEP_ITERS pin).
  auto character_solver_iterations() const -> int {
    return solver_iters_override_ > 0 ? solver_iters_override_
                                      : kBGSolverIterationsCharacter;
  }

  /// Whether worlds should time their steps and log what they find
  /// (BA_DYNAMICS_PROFILE).
  auto profile() const -> bool { return profile_; }

 private:
  EventLoop* event_loop_{};
  // BA_BG_QUICKSTEP_ITERS pin (test_game_run --bg-solver-iters): every
  // island, hints included, solves with this many.
  int solver_iters_override_{-1};
  bool profile_{};
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_DYNAMICS_BG_BG_DYNAMICS_SERVER_H_
