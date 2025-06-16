// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/dynamics/part.h"

#include <vector>

#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging.h"
#include "ballistica/scene_v1/dynamics/dynamics.h"
#include "ballistica/scene_v1/dynamics/material/material.h"
#include "ballistica/scene_v1/support/scene.h"
#include "ballistica/shared/generic/utils.h"

namespace ballistica::scene_v1 {

Part::Part(Node* node, bool default_collide)
    : our_id_(node->AddPart(this)),
      default_collides_(default_collide),
      node_(node) {
  assert(node_.exists());
  birth_time_ = node_->scene()->time();
  dynamics_ = node_->scene()->dynamics();
}

Part::~Part() = default;

void Part::CheckBodies() {
  for (auto&& i : rigid_bodies_) {
    i->Check();
  }
}

void Part::KillConstraints() {
  for (auto&& i : rigid_bodies_) {
    i->KillConstraints();
  }
}

void Part::UpdateBirthTime() { birth_time_ = node_->scene()->time(); }

auto Part::GetMaterials() const -> std::vector<Material*> {
  return RefsToPointers(materials_);
}

void Part::SetMaterials(const std::vector<Material*>& vals) {
  assert(!Utils::HasNullMembers(vals));

  // Hold strong refs to the materials passed.
  materials_ = PointersToRefs(vals);

  // Wake us up in case our new materials make us stop colliding or whatnot.
  // (we may be asleep resting on something we suddenly no longer hit)
  Wake();

  // Reset all of our active collisions so new collisions will take effect
  // with the new materials.
  for (auto&& i : collisions_) {
    dynamics_->ResetCollision(node()->id(), id(), i.node, i.part);
  }
}

void Part::ApplyMaterials(MaterialContext* s, const Part* src_part,
                          const Part* dst_part) {
  for (auto&& i : materials_) {
    assert(i.exists());
    i->Apply(s, src_part, dst_part);
  }
}

auto Part::ContainsMaterial(const Material* m) const -> bool {
  assert(m);
  for (auto&& i : materials_) {
    assert(i.exists());
    if (m == i.get()) {
      return true;
    }
  }
  return false;
}

auto Part::IsCollidingWith(int64_t node, int part) const -> bool {
  for (auto&& i : collisions_) {
    if (i.node == node && i.part == part) return true;
  }
  return false;
}

auto Part::IsCollidingWith(int64_t node) const -> bool {
  for (auto&& i : collisions_) {
    if (i.node == node) {
      return true;
    }
  }
  return false;
}

void Part::SetCollidingWith(int64_t node_id, int part, bool colliding,
                            bool physical) {
  if (colliding) {
    // Add this to our list of collisions if its not on it.
    for (auto&& i : collisions_) {
      if (i.node == node_id && i.part == part) {
        BA_PRECONDITION(node());
        g_core->logging->Log(
            LogName::kBa, LogLevel::kError,
            "Got SetCollidingWith for part already colliding with.");
        return;
      }
    }
    collisions_.emplace_back(node_id, part);

  } else {
    // Make sure our bodies are awake - we may have been asleep
    // resting on something that no longer exists.
    if (physical) {
      Wake();
    }

    // Remove the part from our colliding-with list.
    for (auto i = collisions_.begin(); i != collisions_.end(); ++i) {
      if (i->node == node_id && i->part == part) {
        collisions_.erase(i);
        return;
      }
    }
    g_core->logging->Log(LogName::kBa, LogLevel::kError,
                         "Got SetCollidingWith (separated) call for part we're "
                         "not colliding with.");
  }
}

auto Part::GetAge() const -> millisecs_t {
  assert(node_.exists());
  assert(node_->scene()->time() >= birth_time_);
  return node_->scene()->time() - birth_time_;
}

}  // namespace ballistica::scene_v1
