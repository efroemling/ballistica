// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_DYNAMICS_BG_BG_DYNAMICS_CHARACTER_H_
#define BALLISTICA_BASE_DYNAMICS_BG_BG_DYNAMICS_CHARACTER_H_

#include "ballistica/base/dynamics/bg/bg_dynamics.h"
#include "ballistica/base/dynamics/bg/bg_dynamics_channel.h"
#include "ballistica/base/dynamics/bg/bg_dynamics_kinds.h"
#include "ballistica/base/dynamics/bg/bg_dynamics_world.h"
#include "ballistica/shared/ballistica.h"

namespace ballistica::base {

// Logic-side handle for one character's bg-simulated cosmetic rig (see
// BGDynamicsCharacterKind). Feed every anchor body's transform each
// step; read back the simmed body poses whenever you like (they are
// the latest the bg thread has published, typically a step or two
// behind).
//
// A rig lives in the bg-dynamics world it is made in (the terrain it
// collides with is that world's) and keeps that world around for as
// long as it exists.
class BGDynamicsCharacterRig {
 public:
  using Config = BGDynamicsCharacterKind::Config;
  using Output = BGDynamicsCharacterKind::Output;

  BGDynamicsCharacterRig(BGDynamicsWorld* world, const Config& config);
  ~BGDynamicsCharacterRig();

  /// Set one anchor's transform for this step. Every anchor in the
  /// config should be set each step.
  void SetAnchor(int anchor, const Matrix44f& transform);

  /// Request a re-place after a teleport, so the rig lands on the
  /// anchors instead of springing over.
  void Snap();

  /// Load shedding: the fraction of sim steps (0-1) the rig sits out;
  /// see BGDynamicsCharacterKind::Input::skip. Sticky until changed.
  void SetSkip(float skip);

  /// Whether the character is frozen; see
  /// BGDynamicsCharacterKind::Input::frozen. Sticky until changed.
  void SetFrozen(bool frozen);

  /// Whether the character has shattered; see
  /// BGDynamicsCharacterKind::Input::shattered. Sticky until changed.
  void SetShattered(bool shattered);

  /// This step's limb joint targets (Config::limb_joints order, count
  /// entries); see BGDynamicsCharacterKind::Input::limb_joints.
  void SetLimbJointTargets(
      const BGDynamicsCharacterKind::LimbJointTarget* targets, int count);

  /// The latest published poses, or nullptr if none have arrived yet.
  auto output() const -> const Output*;

 private:
  Object::Ref<BGDynamicsWorld> world_;
  BGDynamicsSlot slot_;
  BA_DISALLOW_CLASS_COPIES(BGDynamicsCharacterRig);
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_DYNAMICS_BG_BG_DYNAMICS_CHARACTER_H_
