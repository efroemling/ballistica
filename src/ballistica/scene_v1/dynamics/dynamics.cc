// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/dynamics/dynamics.h"

#include <unordered_map>
#include <utility>

#include "ballistica/base/audio/audio.h"
#include "ballistica/base/audio/audio_source.h"
#include "ballistica/base/dynamics/collision_cache.h"
#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging.h"
#include "ballistica/scene_v1/assets/scene_sound.h"
#include "ballistica/scene_v1/dynamics/collision.h"
#include "ballistica/scene_v1/dynamics/material/material_action.h"
#include "ballistica/scene_v1/dynamics/part.h"
#include "ballistica/scene_v1/support/scene.h"
#include "ode/ode_collision_kernel.h"
#include "ode/ode_collision_util.h"

namespace ballistica::scene_v1 {

// Max contacts for rigid body collisions.
// TODO(ericf): Probably a good idea to accept more than this
//  and then randomly discard some - otherwise
//  we may get contacts only at one end of an object, etc.
#define MAX_CONTACTS 20

// Given two parts, returns true if part1 is major in
// the storage order.
static auto IsInStoreOrder(int64_t node1, int part1, int64_t node2, int part2)
    -> bool {
  assert(node1 >= 0 && part1 >= 0 && node2 >= 0 && part2 >= 0);

  // Node with smaller id is primary search node.
  if (node1 < node2) {
    return true;
  } else if (node1 > node2) {
    return false;
  } else {
    // If nodes are same, classify by part id.
    // If part ids are the same, it doesnt matter.
    return (part1 < part2);
  }
}

// Modified version of dBodyGetPointVel - instead of applying the body's
// linear and angular velocities, we apply a provided force and torque
// to get its local equivalent.
void do_dBodyGetLocalFeedback(dBodyID b, dReal px, dReal py, dReal pz,
                              dReal lvx, dReal lvy, dReal lvz, dReal avx,
                              dReal avy, dReal avz, dVector3 result) {
  dAASSERT(b);
  dVector3 p;
  p[0] = px - b->pos[0];
  p[1] = py - b->pos[1];
  p[2] = pz - b->pos[2];
  p[3] = 0;
  result[0] = lvx;
  result[1] = lvy;
  result[2] = lvz;
  dReal avel[4];
  avel[0] = avx;
  avel[1] = avy;
  avel[2] = avz;
  avel[3] = 0;
  dCROSS(result, +=, avel, p);
}

// Stores info about a collision needing a reset
// (used when parts change materials).
class Dynamics::CollisionReset_ {
 public:
  int node1;
  int node2;
  int part1;
  int part2;
  CollisionReset_(int node1_in, int part1_in, int node2_in, int part2_in)
      : node1(node1_in), node2(node2_in), part1(part1_in), part2(part2_in) {}
};

class Dynamics::CollisionEvent_ {
 public:
  Object::Ref<MaterialAction> action;
  Object::Ref<Collision> collision;
  Object::WeakRef<Node> node1;  // first event node
  Object::WeakRef<Node> node2;  // second event node
  CollisionEvent_(Node* node1_in, Node* node2_in,
                  const Object::Ref<MaterialAction>& action_in,
                  const Object::Ref<Collision>& collision_in)
      : node1(node1_in),
        node2(node2_in),
        action(action_in),
        collision(collision_in) {}
};

class Dynamics::SrcPartCollideMap_ {
 public:
  std::unordered_map<int, Object::Ref<Collision> > dst_part_collisions;
};

class Dynamics::DstNodeCollideMap_ {
 public:
  std::unordered_map<int, SrcPartCollideMap_> src_parts;
  int collideDisabled;
  DstNodeCollideMap_() : collideDisabled(0) {}
  ~DstNodeCollideMap_() = default;
};

class Dynamics::SrcNodeCollideMap_ {
 public:
  std::unordered_map<int64_t, DstNodeCollideMap_> dst_nodes;
};

class Dynamics::Impl_ {
 public:
  explicit Impl_(Dynamics* dynamics) : dynamics_(dynamics) {}

  // NOTE: we need to implement this here in an Impl class because
  // gcc currently chokes on unordered_maps with forward-declared types,
  // so we can't have this in our header without pushing all our map/collision
  // types there too.
  void HandleDisconnect(
      const std::unordered_map<int64_t, Dynamics::SrcNodeCollideMap_>::iterator&
          i,
      const std::unordered_map<int64_t, Dynamics::DstNodeCollideMap_>::iterator&
          j,
      const std::unordered_map<int, SrcPartCollideMap_>::iterator& k,
      const std::unordered_map<int, Object::Ref<Collision> >::iterator& l);

 private:
  Dynamics* dynamics_{};
  // Contains in-progress collisions for current nodes.
  std::unordered_map<int64_t, SrcNodeCollideMap_> node_collisions_;
  friend class Dynamics;
};

Dynamics::Dynamics(Scene* scene_in)
    : scene_(scene_in),
      collision_cache_(std::make_unique<base::CollisionCache>()),
      impl_(std::make_unique<Impl_>(this)) {
  ResetODE_();
}

Dynamics::~Dynamics() {
  if (in_process_) {
    g_core->logging->Log(LogName::kBa, LogLevel::kError,
                         "Dynamics going down within Process() call;"
                         " should not happen.");
  }
  ShutdownODE_();
}

void Dynamics::Draw(base::FrameDef* frame_def) {
// draw collisions if desired..
#if BA_DEBUG_BUILD && 0
  SimpleComponent c(frame_def->overlay_3d_pass());
  c.SetColor(1, 0, 0);
  c.SetTransparent(true);
  for (auto&& i : debug_collisions_) {
    auto xf = c.ScopedTransform();
    c.Translate(i.x(), i.y(), i.z());
    c.scaleUniform(0.05f);
    c.DrawMeshAsset(g_assets->GetMesh(Assets::BOX_MESH));
  }
  c.Submit();
  debug_collisions_.clear();
#endif  // BA_DEBUG_BUILD
}

void Dynamics::ResetCollision(int64_t node1, int part1, int64_t node2,
                              int part2) {
  // Make sure this isn't called while we're in the middle of processing
  // collides (it shouldn't be possible but just in case).
  BA_PRECONDITION(!processing_collisions_);

  // We don't actually do any resetting here; we just store a notice that
  // these two parts should be separated and the notice is sent out at
  // collide process time.
  collision_resets_.emplace_back(node1, part1, node2, part2);
}

void Dynamics::AddTrimesh(dGeomID g) {
  assert(dGeomGetClass(g) == dTriMeshClass);
  trimeshes_.push_back(g);

  // Do a one-time bbox update; these never move so this should cover us.
  g->recomputeAABB();
  g->gflags &= (~(GEOM_DIRTY | GEOM_AABB_BAD));  // NOLINT

  // Update our collision cache.
  collision_cache_->SetGeoms(trimeshes_);
}

void Dynamics::RemoveTrimesh(dGeomID g) {
  assert(dGeomGetClass(g) == dTriMeshClass);
  for (auto i = trimeshes_.begin(); i != trimeshes_.end(); i++) {
    if ((*i) == g) {
      trimeshes_.erase(i);

      // Update our collision cache.
      collision_cache_->SetGeoms(trimeshes_);
      return;
    }
  }
  throw Exception("trimesh not found");
}

auto Dynamics::AreColliding_(const Part& p1_in, const Part& p2_in) -> bool {
  const Part* p1;
  const Part* p2;
  if (IsInStoreOrder(p1_in.node()->id(), p1_in.id(), p2_in.node()->id(),
                     p2_in.id())) {
    p1 = &p1_in;
    p2 = &p2_in;
  } else {
    p1 = &p2_in;
    p2 = &p1_in;
  }

  // Go down the hierarchy until we either find a missing level or
  // find the collision.
  auto i = impl_->node_collisions_.find(p1->node()->id());
  if (i != impl_->node_collisions_.end()) {
    auto j = i->second.dst_nodes.find(p2->node()->id());
    if (j != i->second.dst_nodes.end()) {
      auto k = j->second.src_parts.find(p1->id());
      if (k != j->second.src_parts.end()) {
        auto l = k->second.dst_part_collisions.find(p2->id());
        if (l != k->second.dst_part_collisions.end()) return true;
      }
    }
  }
  return false;
}

auto Dynamics::GetCollision(Part* p1_in, Part* p2_in, MaterialContext** cc1,
                            MaterialContext** cc2) -> Collision* {
  Part* p1;
  Part* p2;

  if (IsInStoreOrder(p1_in->node()->id(), p1_in->id(), p2_in->node()->id(),
                     p2_in->id())) {
    p1 = p1_in;
    p2 = p2_in;
  } else {
    p1 = p2_in;
    p2 = p1_in;
  }

  std::pair<std::unordered_map<int, Object::Ref<Collision> >::iterator, bool>
      i = impl_->node_collisions_[p1->node()->id()]
              .dst_nodes[p2->node()->id()]
              .src_parts[p1->id()]
              .dst_part_collisions.insert(
                  std::make_pair(p2->id(), Object::Ref<Collision>()));

  Collision* new_collision;

  // If it didnt exist, go ahead and set up the collision.
  if (i.second) {
    i.first->second = Object::New<Collision>(scene_);
    new_collision = i.first->second.get();
  } else {
    new_collision = nullptr;
  }

  (*cc1) = &i.first->second->src_context;
  (*cc2) = &i.first->second->dst_context;

  // Continue setting it up.
  if (new_collision) {
    new_collision->src_part = p1;
    new_collision->dst_part = p2;

    // Init contexts with parts' defaults.
    (*cc1)->collide = p1->default_collides();
    (*cc2)->collide = p2->default_collides();

    // Apply each part's materials to its context.
    p1->ApplyMaterials(*cc1, p1, p2);
    p2->ApplyMaterials(*cc2, p2, p1);

    // If either disabled collisions between these two nodes, store that.
    DstNodeCollideMap_* dncm =
        &impl_->node_collisions_[p1->node()->id()].dst_nodes[p2->node()->id()];
    if (!(*cc1)->node_collide || !(*cc2)->node_collide) {
      dncm->collideDisabled = true;
    }

    // Don't collide if either context doesnt want us to or if the nodes
    // aren't colliding (unless either context wants to ignore node
    // collision status).
    new_collision->collide =
        ((*cc1)->collide && (*cc2)->collide
         && (!dncm->collideDisabled || !(*cc1)->use_node_collide
             || !(*cc2)->use_node_collide));

    // If theres a physical collision involved, inform the parts
    // so they can keep track of who they're touching.
    if (new_collision->collide) {
      bool physical = (*cc1)->physical && (*cc2)->physical;
      p1->SetCollidingWith(p2->node()->id(), p2->id(), true, physical);
      if (p1 != p2) {
        p2->SetCollidingWith(p1->node()->id(), p1->id(), true, physical);
      }

      // Also add all new-collide events to the global list
      // (to be executed after all contacts are found).
      for (auto& connect_action : (*cc1)->connect_actions)
        collision_events_.emplace_back(p1->node(), p2->node(), connect_action,
                                       Object::Ref<Collision>(new_collision));
      for (auto& connect_action : (*cc2)->connect_actions)
        collision_events_.emplace_back(p2->node(), p1->node(), connect_action,
                                       Object::Ref<Collision>(new_collision));
    }
  }

  // Regardless, set it as claimed so we know its current.
  i.first->second->claim_count++;

  return &(*(i.first->second));
}

void Dynamics::Impl_::HandleDisconnect(
    const std::unordered_map<int64_t, Dynamics::SrcNodeCollideMap_>::iterator&
        i,
    const std::unordered_map<int64_t, Dynamics::DstNodeCollideMap_>::iterator&
        j,
    const std::unordered_map<int, SrcPartCollideMap_>::iterator& k,
    const std::unordered_map<int, Object::Ref<Collision> >::iterator& l) {
  // Handle disconnect equivalents if they were colliding.
  if (l->second->collide) {
    // Add the contexts' disconnect commands to be executed.
    for (auto m = l->second->src_context.disconnect_actions.begin();
         m != l->second->src_context.disconnect_actions.end(); m++) {
      Part* src_part = l->second->src_part.get();
      Part* dst_part = l->second->dst_part.get();
      dynamics_->collision_events_.emplace_back(
          src_part ? src_part->node() : nullptr,
          dst_part ? dst_part->node() : nullptr, *m, l->second);
    }

    for (auto m = l->second->dst_context.disconnect_actions.begin();
         m != l->second->dst_context.disconnect_actions.end(); m++) {
      Part* src_part = l->second->src_part.get();
      Part* dst_part = l->second->dst_part.get();
      dynamics_->collision_events_.emplace_back(
          dst_part ? dst_part->node() : nullptr,
          src_part ? src_part->node() : nullptr, *m, l->second);
    }

    // Now see if either of the two parts involved still exist and if they do,
    // tell them they're no longer colliding with the other.
    bool physical =
        l->second->src_context.physical && l->second->dst_context.physical;
    Part* p1 = l->second->dst_part.get();
    Part* p2 = l->second->src_part.get();
    if (p1) {
      assert(p1 == l->second->dst_part.get());
      p1->SetCollidingWith(i->first, k->first, false, physical);  // NOLINT
    }
    if (p2) {
      assert(p2 == l->second->src_part.get());
    }
    if (p2 && (p2 != p1)) {
      p2->SetCollidingWith(j->first, l->first, false, physical);  // NOLINT
    }
  }

  // Remove this particular collision.
  k->second.dst_part_collisions.erase(l);
}

void Dynamics::ProcessCollision_() {
  processing_collisions_ = true;

  collision_count_ = 0;

  // First handle our explicitly reset collisions.
  // For each reset request, we check if the surfaces are colliding and if so
  // we separate them and add their separation commands to our to-do list.
  if (!collision_resets_.empty()) {
    for (auto& collision_reset : collision_resets_) {
      int n1, n2;
      int p1, p2;

      if (IsInStoreOrder(collision_reset.node1, collision_reset.part1,
                         collision_reset.node2, collision_reset.part2)) {
        n1 = collision_reset.node1;
        p1 = collision_reset.part1;
        n2 = collision_reset.node2;
        p2 = collision_reset.part2;
      } else {
        n1 = collision_reset.node2;
        p1 = collision_reset.part2;
        n2 = collision_reset.node1;
        p2 = collision_reset.part1;
      }

      // Go down the hierarchy until we either find a missing level or
      // find the collision to reset.
      {
        auto i = impl_->node_collisions_.find(n1);
        if (i != impl_->node_collisions_.end()) {
          auto j = i->second.dst_nodes.find(n2);
          if (j != i->second.dst_nodes.end()) {
            auto k = j->second.src_parts.find(p1);
            if (k != j->second.src_parts.end()) {
              auto l = k->second.dst_part_collisions.find(p2);
              if (l != k->second.dst_part_collisions.end()) {
                // They were colliding - separate them.
                impl_->HandleDisconnect(i, j, k, l);
              }

              // Erase if none left.
              if (k->second.dst_part_collisions.empty()) {
                j->second.src_parts.erase(k);
              }
            }

            // Erase if none left.
            if (j->second.src_parts.empty()) i->second.dst_nodes.erase(j);
          }

          // Erase if none left.
          if (i->second.dst_nodes.empty()) impl_->node_collisions_.erase(i);
        }
      }
    }
    collision_resets_.clear();
  }

  // Reset our claim counts. When we run collision tests, claim counts
  // will be incremented for things that are still in contact.
  for (auto& node_collision : impl_->node_collisions_) {
    for (auto& dst_node : node_collision.second.dst_nodes) {
      for (auto& src_part : dst_node.second.src_parts) {
        for (auto& dst_part_collision : src_part.second.dst_part_collisions) {
          dst_part_collision.second->claim_count = 0;
        }
      }
    }
  }

  // Process all standard collisions. This will trigger our callback which
  // do the real work (add collisions to list, store commands to be
  // called, etc).
  dSpaceCollide(ode_space_, this, &DoCollideCallback_);

  // Collide our trimeshes against everything.
  collision_cache_->CollideAgainstSpace(ode_space_, this, &DoCollideCallback_);

  // Do a bit of precalc each cycle.
  collision_cache_->Precalc();

  // Now go through our list of currently-colliding stuff,
  // setting parts' currently-colliding-with lists
  // based on current info,
  // removing unclaimed collisions and empty groups.
  std::unordered_map<int64_t, SrcNodeCollideMap_>::iterator i_next;
  std::unordered_map<int64_t, DstNodeCollideMap_>::iterator j_next;
  std::unordered_map<int, SrcPartCollideMap_>::iterator k_next;
  std::unordered_map<int, Object::Ref<Collision> >::iterator l_next;
  for (auto i = impl_->node_collisions_.begin();
       i != impl_->node_collisions_.end(); i = i_next) {
    i_next = i;
    i_next++;
    for (auto j = i->second.dst_nodes.begin(); j != i->second.dst_nodes.end();
         j = j_next) {
      j_next = j;
      j_next++;
      for (auto k = j->second.src_parts.begin(); k != j->second.src_parts.end();
           k = k_next) {
        k_next = k;
        k_next++;
        for (auto l = k->second.dst_part_collisions.begin();
             l != k->second.dst_part_collisions.end(); l = l_next) {
          l_next = l;
          l_next++;

          // Not claimed; separating.
          if (!l->second->claim_count) {
            impl_->HandleDisconnect(i, j, k, l);
          }
        }
        if (k->second.dst_part_collisions.empty()) {
          j->second.src_parts.erase(k);
        }
      }
      if (j->second.src_parts.empty()) {
        i->second.dst_nodes.erase(j);
      }
    }
    if (i->second.dst_nodes.empty()) {
      impl_->node_collisions_.erase(i);
    }
  }

  // We're now done processing collisions - its now safe to reset
  // collisions, etc. since we're no longer going through the lists.
  processing_collisions_ = false;

  // Execute all events that we built up due to collisions.
  for (auto&& i : collision_events_) {
    active_collision_ = i.collision.get();
    active_collide_src_node_ = i.node1;
    active_collide_dst_node_ = i.node2;
    i.action->Execute(i.node1.get(), i.node2.get(), scene_);
  }
  active_collision_ = nullptr;
  collision_events_.clear();
}

void Dynamics::Process() {
  in_process_ = true;
  // Update this once so we can recycle results.
  real_time_ = g_core->AppTimeMillisecs();
  ProcessCollision_();
  dWorldQuickStep(ode_world_, kGameStepSeconds);
  dJointGroupEmpty(ode_contact_group_);
  in_process_ = false;
}

void Dynamics::DoCollideCallback_(void* data, dGeomID o1, dGeomID o2) {
  auto* d = static_cast<Dynamics*>(data);
  d->CollideCallback_(o1, o2);
}

// Run collisions for everything. Store any callbacks that will need to be made
// and run them after all collision constraints are made.
// This way we know all bodies and their associated nodes, etc are valid
// throughout collision processing.
void Dynamics::CollideCallback_(dGeomID o1, dGeomID o2) {
  dBodyID b1 = dGeomGetBody(o1);
  dBodyID b2 = dGeomGetBody(o2);

  auto* r1 = static_cast<RigidBody*>(dGeomGetData(o1));
  auto* r2 = static_cast<RigidBody*>(dGeomGetData(o2));
  assert(r1 && r2);

  // If both of these guys are either terrain (a trimesh) or an inactive body,
  // we can skip actually testing for a collision.
  if ((dGeomGetClass(o1) == dTriMeshClass && b2 && !dBodyIsEnabled(b2))
      || (dGeomGetClass(o2) == dTriMeshClass && b1 && !dBodyIsEnabled(b1))) {
    // We do, however, need to poke any existing collision so a disconnect event
    // doesn't occur if we were colliding.
    Part* p1_in = r1->part();
    Part* p2_in = r2->part();
    assert(p1_in && p2_in);
    Part* p1;
    Part* p2;

    if (IsInStoreOrder(p1_in->node()->id(), p1_in->id(), p2_in->node()->id(),
                       p2_in->id())) {
      p1 = p1_in;
      p2 = p2_in;
    } else {
      p1 = p2_in;
      p2 = p1_in;
    }
    auto i = impl_->node_collisions_.find(p1->node()->id());
    if (i != impl_->node_collisions_.end()) {
      auto j = i->second.dst_nodes.find(p2->node()->id());
      if (j != i->second.dst_nodes.end()) {
        auto k = j->second.src_parts.find(p1->id());
        if (k != j->second.src_parts.end()) {
          auto l = k->second.dst_part_collisions.find(p2->id());
          if (l != k->second.dst_part_collisions.end()) {
#pragma clang diagnostic push
#pragma ide diagnostic ignored "UnusedValue"
            l->second->claim_count++;
#pragma clang diagnostic pop
          }
        }
      }
    }
    return;
  }

  // Check their overall types to count out some basics
  // (landscapes never collide against landscapes, etc).
  if (!((r1->collide_type() & r2->collide_mask())
        && (r2->collide_type() & r1->collide_mask()))) {  // NOLINT
    return;
  }

  Part* p1 = r1->part();
  Part* p2 = r2->part();
  assert(p1 && p2);

  // Pre-filter collisions.
  if (!(p1->node()->PreFilterCollision(r1, r2)
        && p2->node()->PreFilterCollision(r2, r1))) {
    return;
  }

  // Perhaps an optimization could be to avoid collision testing
  // if we're certain two materials will never result in a collision?
  // I don't think calculating full material-states before each collision
  // detection test would be economical but if there's a simple way to know
  // they'll never collide.
  dContact contact[MAX_CONTACTS];  // up to MAX_CONTACTS contacts per pair
  if (int numc =
          dCollide(o1, o2, MAX_CONTACTS, &contact[0].geom, sizeof(dContact))) {
    MaterialContext* cc1;
    MaterialContext* cc2;

    // Create or acquire a collision.
    Collision* c = GetCollision(p1, p2, &cc1, &cc2);

    // If theres no physical collision between these two suckers we're done.
    if (!c->collide) {
      return;
    }

    // Store body IDs for use in callback messages.
    // There may be more than one body ID per part-on-part contact
    // but we just keep one at the moment.
    c->body_id_1 = r1->id();
    c->body_id_2 = r2->id();

    // Get average depth for all contacts.
    if (numc > 0) {
      float d = 0;
      for (int i = 0; i < numc; i++) {
        d += contact[i].geom.depth;
      }
      c->depth = d / static_cast<float>(numc);
    }

    // Get average position for all contacts.
    float apx = 0;
    float apy = 0;
    float apz = 0;
    if (numc > 0) {
      for (int i = 0; i < numc; i++) {
        apx += contact[i].geom.pos[0];
        apy += contact[i].geom.pos[1];
        apz += contact[i].geom.pos[2];
      }
      auto fnumc = static_cast<float>(numc);
      apx /= fnumc;
      apy /= fnumc;
      apz /= fnumc;
    }
    c->x = apx;
    c->y = apy;
    c->z = apz;

    // If theres an impact sound, skid sound, or roll sound attached to this
    // collision, calculate applicable values.
    // Impact is based on the component of the vector (force x relative
    // velocity) that is parallel to the collision normal.
    // Skid is the component tangential to the collision normal.
    // Roll is based on tangential velocity multiplied by parallel force.
    bool get_feedback_for_these_collisions = false;

    if (cc1->complex_sound || cc2->complex_sound) {
      millisecs_t real_time = real_time_;

      // Its possible that we have more than one set of colliding things
      // that resolve to the same collision record
      // (multiple bodies in the same part, etc).
      // However we can only calc feedback for the first one we come across
      // (there's only one feedback buffer in the Collision).
      if (c->claim_count == 1) {
        get_feedback_for_these_collisions = true;
      }

      dVector3 an;
      an[0] = an[1] = an[2] = 0;
      dVector3 b1v;
      dVector3 b2v;
      dVector3 b1cv;
      dVector3 b2cv;

      // Get average collide normal for all contacts.
      {
        if (numc > 0) {
          for (int i = 0; i < numc; i++) {
            an[0] += contact[i].geom.normal[0];
            an[1] += contact[i].geom.normal[1];
            an[2] += contact[i].geom.normal[2];
          }
          auto fnumc = static_cast<float>(numc);
          an[0] /= fnumc;
          an[1] /= fnumc;
          an[2] /= fnumc;
        }

        const dReal* v;

        // Get body velocities at the avg contact point in global coords.
        if (b1) {
          v = dBodyGetLinearVel(b1);
          b1cv[0] = v[0];
          b1cv[1] = v[1];
          b1cv[2] = v[2];
          dBodyGetPointVel(b1, apx, apy, apz, b1v);
        } else {
          b1cv[0] = b1cv[1] = b1cv[2] = 0;
          b1v[0] = b1v[1] = b1v[2] = 0;
        }
        if (b2) {
          v = dBodyGetLinearVel(b2);
          b2cv[0] = v[0];
          b2cv[1] = v[1];
          b2cv[2] = v[2];
          dBodyGetPointVel(b2, apx, apy, apz, b2v);
        } else {
          b2cv[0] = b2cv[1] = b2cv[2] = 0;
          b2v[0] = b2v[1] = b2v[2] = 0;
        }
      }

      dVector3 local_feedback;
      if (!c->collide_feedback.empty()) {
        assert(b1 || b2);
        dBodyID fb;
        float affx = 0;
        float affy = 0;
        float affz = 0;
        float aftx = 0;
        float afty = 0;
        float aftz = 0;

        // Get one or the other force. Once we convert it to local
        // it should be equal/opposite.
        if (b1) {
          fb = b1;
          for (auto& i : c->collide_feedback) {
            affx += i.f1[0];
            affy += i.f1[1];
            affz += i.f1[2];
            aftx += i.t1[0];
            afty += i.t1[1];
            aftz += i.t1[2];
          }
        } else {
          fb = b2;
          for (auto& i : c->collide_feedback) {
            affx += i.f2[0];
            affy += i.f2[1];
            affz += i.f2[2];
            aftx += i.t2[0];
            afty += i.t2[1];
            aftz += i.t2[2];
          }
        }
        dMass mass;
        dBodyGetMass(fb, &mass);

        // Average them and divide by mass to normalize the force.
        float count = c->collide_feedback.size();
        affx /= (count * mass.mass * 10.0f);
        affy /= (count * mass.mass * 10.0f);
        affz /= (count * mass.mass * 10.0f);
        aftx /= (count * mass.mass * 10.0f);
        afty /= (count * mass.mass * 10.0f);
        aftz /= (count * mass.mass * 10.0f);

        // Get local feedback.
        do_dBodyGetLocalFeedback(fb, apx, apy, apz, affx, affy, affz, aftx,
                                 afty, aftz, local_feedback);

        // TODO(ericf): normalize feedback based on body mass so all bodies can
        //  use similar ranges? ...  hmm maybe not a good idea.. larger object
        //  *should* be louder plus then we're using object mass, which doesnt
        //  account for objects
        //  connected to it via fixed constraints, etc
        //  the sound should simply have a impulse associated with it -
        //  anything less than that will scale appropriately
      } else {
        local_feedback[0] = 0;
        local_feedback[1] = 0;
        local_feedback[2] = 0;
      }

      // Combine both velocities into one relative velocity for the contact
      // point.
      dVector3 rvel;
      rvel[0] = b2v[0] - b1v[0];
      rvel[1] = b2v[1] - b1v[1];
      rvel[2] = b2v[2] - b1v[2];

      // Get our overall relative velocity (at the objects' centers-of-gravity
      // we use this to determine roll.
      dVector3 crvel;
      crvel[0] = b2cv[0] - b1cv[0];
      crvel[1] = b2cv[1] - b1cv[1];
      crvel[2] = b2cv[2] - b1cv[2];

      // Now multiply our feedback force by our relative velocity and use the
      // component of that which is parallel to our collide normal as "impact"
      // and the tangential component as "skid".
      {
        dVector3 vec = {local_feedback[0] * rvel[0],
                        local_feedback[1] * rvel[1],
                        local_feedback[2] * rvel[2]};
        float cur_impact = std::abs(dDOT(an, vec)) / 3;
        float vec_len = dVector3Length(vec);
        float cur_skid = sqrtf(vec_len * vec_len - cur_impact * cur_impact) / 2;

        // Roll is calculated as the component of force parallel to the normal
        // multiplied by the tangential velocity component (relative
        // center-of-gravity velocities - not at the contact point).
        float cur_roll;
        {
          float vparallel = dDOT(an, crvel);
          float vec_len_2 = dVector3Length(crvel);
          float vtangential =
              sqrtf(vec_len_2 * vec_len_2 - vparallel * vparallel);
          cur_roll = (vtangential);
        }
        cur_roll -= cur_impact;
        cur_skid -= cur_impact;
        if (cur_roll < 0) {
          cur_roll = 0;
        }
        if (cur_skid < 0) {
          cur_skid = 0;
        }

        // Weigh our new values with previous ones to get more smooth consistent
        // values over time.
        float impact_weight = 0.3f;
        float skid_weight = 0.1f;
        float roll_weight = 0.1f;

        c->impact =
            (1.0f - impact_weight) * c->impact + impact_weight * cur_impact;
        c->skid = (1.0f - skid_weight) * c->skid + skid_weight * cur_skid;
        c->roll = (1.0f - roll_weight) * c->roll + roll_weight * cur_roll;

        // Draw debugging lines - red for impact, green for skid, blue for roll.
        // if (scene_->getShowCollisions()) {
        //     g_graphics_server->addDebugDrawObject(
        //         new GraphicsServer::DebugDrawLine(
        //             apx, apy, apz,
        //             apx+0*0.5f*c->impact,
        //             apy+1*0.5f*c->impact,
        //             apz+0*0.5f*c->impact, 15, 1, 0, 0));
        //     g_graphics_server->addDebugDrawObject(
        //         new GraphicsServer::DebugDrawLine(
        //             apx, apy, apz,
        //             apx-0*0.5f*c->skid,
        //             apy-1*0.5f*c->skid,
        //             apz-0*0.5f*c->skid, 10, 0, 1, 0));
        //     g_graphics_server->addDebugDrawObject(
        //         new GraphicsServer::DebugDrawLine(
        //             apx, apy, apz,
        //             apx+1*0.5f*c->roll,
        //             apy+0*0.5f*c->roll,
        //             apz+0*0.5f*c->roll, 15, 0, 0, 1));
        // }

        // Play impact sounds if its been long enough since last.
        // Clip if impact value is low enough (otherwise we'd be running tiny
        // little impact sounds constantly).
        // Also only play impact sound when our current impact is less than
        // our average (so that as impact spikes we hit it near the top instead
        // of on the way up).
        if ((real_time - p1->last_impact_sound_time() >= 500)
            || (real_time - p2->last_impact_sound_time() > 500)) {
          float clip = 0.15f;
          MaterialContext* contexts[] = {cc1, cc2};
          for (auto context : contexts) {
            for (auto&& i : context->impact_sounds) {
              if (c->impact > i.target_impulse * clip
                  && cur_impact < c->impact) {
                float volume = i.target_impulse > 0.0001f
                                   ? (c->impact - (i.target_impulse * clip))
                                         / (i.target_impulse * (1.0f - clip))
                                   : 1.0f;

                if (volume > 1) volume = 1;
                assert(i.sound.exists());
                if (base::AudioSource* source =
                        g_base->audio->SourceBeginNew()) {
                  source->SetGain(volume * i.volume);
                  source->SetPosition(apx, apy, apz);
                  source->Play(i.sound->GetSoundData());
                  p1->set_last_impact_sound_time(real_time);
                  p2->set_last_impact_sound_time(real_time);
                  last_impact_sound_time_ = real_time;
                  source->End();
                }
              }
            }
          }
        }

        // Play skid sounds.
        {
          float clip = 0.15f;
          MaterialContext* contexts[] = {cc1, cc2};
          for (auto context : contexts) {
            for (auto&& i : context->skid_sounds) {
              if (c->skid > i.target_impulse * clip) {
                float volume = i.target_impulse > 0.0001f
                                   ? (c->skid - (i.target_impulse * clip))
                                         / (i.target_impulse * (1.0f - clip))
                                   : 1.0f;
                if (volume > 1) volume = 1;

                // If we're already playing, just adjust volume
                // and position - otherwise get a sound started.
                if (i.playing) {
                  base::AudioSource* s =
                      g_base->audio->SourceBeginExisting(i.play_id, 101);
                  if (s) {
                    s->SetGain(volume * i.volume);
                    s->SetPosition(apx, apy, apz);
                    s->End();
                  } else {
                    // Spare ourself some trouble next time.
                    i.playing = false;
                  }
                } else if (real_time - p1->last_skid_sound_time() >= 250
                           || real_time - p2->last_skid_sound_time() > 250) {
                  assert(i.sound.exists());
                  if (base::AudioSource* source =
                          g_base->audio->SourceBeginNew()) {
                    source->SetLooping(true);
                    source->SetGain(volume * i.volume);
                    source->SetPosition(apx, apy, apz);
                    i.play_id = source->Play(i.sound->GetSoundData());
                    i.playing = true;
                    p1->set_last_skid_sound_time(real_time);
                    p2->set_last_skid_sound_time(real_time);
                    source->End();
                  }
                }
              } else {
                // Skid values are low - stop any playing skid sounds.
                if (i.playing) {
                  g_base->audio->PushSourceFadeOutCall(i.play_id, 200);
                  i.playing = false;
                }
              }
            }
          }
        }

        // Play roll sounds.
        {
          float clip = 0.15f;
          MaterialContext* contexts[] = {cc1, cc2};
          for (auto context : contexts) {
            for (auto&& i : context->roll_sounds) {
              if (c->roll > i.target_impulse * clip) {
                float volume = i.target_impulse > 0.0001f
                                   ? (c->roll - (i.target_impulse * clip))
                                         / (i.target_impulse * (1.0f - clip))
                                   : 1;
                if (volume > 1) volume = 1;

                // If we're already playing, just adjust volume
                // and position; otherwise get a sound started.
                if (i.playing) {
                  base::AudioSource* s =
                      g_base->audio->SourceBeginExisting(i.play_id, 102);
                  if (s) {
                    s->SetGain(volume * i.volume);
                    s->SetPosition(apx, apy, apz);
                    s->End();
                  } else {
                    // spare ourself some trouble next time
                    i.playing = false;
                  }
                } else if (real_time - p1->last_roll_sound_time() >= 250
                           || real_time - p2->last_roll_sound_time() > 250) {
                  assert(i.sound.exists());
                  if (base::AudioSource* source =
                          g_base->audio->SourceBeginNew()) {
                    source->SetLooping(true);
                    source->SetGain(volume * i.volume);
                    source->SetPosition(apx, apy, apz);
                    i.play_id = source->Play(i.sound->GetSoundData());
                    i.playing = true;
                    p1->set_last_roll_sound_time(real_time);
                    p2->set_last_roll_sound_time(real_time);
                    source->End();
                  }
                }
              } else {
                // roll values are low - stop any playing roll sounds
                if (i.playing) {
                  g_base->audio->PushSourceFadeOutCall(i.play_id, 200);
                  i.playing = false;
                }
              }
            }
          }
        }
      }
      if (get_feedback_for_these_collisions) {
        assert(numc >= 0);
        c->collide_feedback.resize(static_cast<uint32_t>(numc));
      }
    }

    // Play collide sounds when new contacts happen
    // or when the averaged collide-position relative to
    // both objects changes by a largeish amount.
    // (in a normal rolling or sliding situation, the collide position
    // will stay relatively constant in at least one of the object's
    // frame-of-reference)
    bool play_collide_sounds = false;

    // Normal sounds should just happen on initial contact creation.
    if (c->contact_count == 0 && numc > 0) {
      play_collide_sounds = true;
    }

    c->contact_count = numc;

    if (play_collide_sounds) {
      for (auto&& i : cc1->connect_sounds) {
        assert(i.sound.exists());
        if (base::AudioSource* source = g_base->audio->SourceBeginNew()) {
          source->SetPosition(apx, apy, apz);
          source->SetGain(i.volume);
          source->Play(i.sound->GetSoundData());
          source->End();
        }
      }
      for (auto&& i : cc2->connect_sounds) {
        assert(i.sound.exists());
        if (base::AudioSource* source = g_base->audio->SourceBeginNew()) {
          source->SetPosition(apx, apy, apz);
          source->SetGain(i.volume);
          source->Play(i.sound->GetSoundData());
          source->End();
        }
      }
    }

    // Set up collision constraints for this frame as long
    // as theres at least one body involved.
    if ((b1 || b2) && (cc1->physical && cc2->physical)) {
      float friction = 1.2f * sqrtf(cc1->friction * cc2->friction);
      float bounce = sqrtf(cc1->bounce * cc2->bounce);
      float stiffness;
      if (cc1->stiffness < 0.00000001f || cc2->stiffness < 0.00000001f) {
        stiffness = 0.00000001f;
      } else {
        stiffness = 8000 * sqrtf(cc1->stiffness * cc2->stiffness);
      }
      float damping = 80 * cc1->damping + cc2->damping;
      if ((stiffness < 0.00000001f) && (damping < 0.00000001f)) {
        damping = 0.00000001f;
      }

      // Cfm/erp (based off stiffness/damping).
      float erp = (kGameStepSeconds * stiffness)
                  / ((kGameStepSeconds * stiffness) + damping);
      float cfm = 1.0f / ((kGameStepSeconds * stiffness) + damping);

      // Normally a geom against a body does not automatically wake the body.
      // However we explicitly do so in certain cases (if the geom is moving,
      // etc).
      if (r1->geom_wake_on_collide() || r2->geom_wake_on_collide()) {
        if (b1) {
          dBodyEnable(b1);
        }
        if (b2) {
          dBodyEnable(b2);
        }
      }
      bool do_collide = true;

      // Set up our contacts.
      // FIXME should really do some merging in cases with > 15 or so contacts
      //  (which seem to occur often with boxes and such).

      for (int i = 0; i < numc; i += 1) {
        // NOLINTNEXTLINE
        contact[i].surface.mode = dContactBounce | dContactSoftCFM
                                  | dContactSoftERP | dContactApprox1;
        contact[i].surface.mu2 = 0;
        contact[i].surface.bounce_vel = 0.1f;
        contact[i].surface.mu = friction;
        contact[i].surface.bounce = bounce;
        contact[i].surface.soft_cfm = cfm;
        contact[i].surface.soft_erp = erp;
      }

      // Let each side of the collision modify our stuff. If any party objects
      // to the collision occurring, we scrap the whole plan.
      if ((!r1->CallCollideCallbacks(contact, numc, r2))
          || (!r2->CallCollideCallbacks(contact, numc, r1))) {
        do_collide = false;
      }
      if (do_collide) {
        collision_count_ += numc;
        for (int i = 0; i < numc; i += 1) {
          dJointID constraint =
              dJointCreateContact(ode_world_, ode_contact_group_, contact + i);
          dJointAttach(constraint, b1, b2);
          if (get_feedback_for_these_collisions) {
            dJointSetFeedback(constraint, &c->collide_feedback[i]);
          }
        }
      }
    }
  }
}

void Dynamics::ShutdownODE_() {
  if (ode_space_) {
    dSpaceDestroy(ode_space_);
    ode_space_ = nullptr;
  }
  if (ode_world_) {
    dWorldDestroy(ode_world_);
    ode_world_ = nullptr;
  }
  if (ode_contact_group_) {
    dJointGroupDestroy(ode_contact_group_);
    ode_contact_group_ = nullptr;
  }
}

void Dynamics::ResetODE_() {
  ShutdownODE_();
  ode_world_ = dWorldCreate();
  assert(ode_world_);
  dWorldSetGravity(ode_world_, 0, -20, 0);
  dWorldSetContactSurfaceLayer(ode_world_, 0.001f);
  dWorldSetAutoDisableFlag(ode_world_, true);
  dWorldSetAutoDisableSteps(ode_world_, 5);
  dWorldSetAutoDisableLinearThreshold(ode_world_, 0.1f);
  dWorldSetAutoDisableAngularThreshold(ode_world_, 0.1f);
  dWorldSetAutoDisableSteps(ode_world_, 10);
  dWorldSetAutoDisableTime(ode_world_, 0);
  dWorldSetQuickStepNumIterations(ode_world_, 10);
  ode_space_ = dHashSpaceCreate(nullptr);
  assert(ode_space_);
  ode_contact_group_ = dJointGroupCreate(0);
  assert(ode_contact_group_);
  dRandSetSeed(5432);
}

}  // namespace ballistica::scene_v1
