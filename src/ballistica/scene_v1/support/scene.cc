// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/support/scene.h"

#include <string>
#include <vector>

#include "ballistica/base/audio/audio.h"
#include "ballistica/base/dynamics/bg/bg_dynamics.h"
#include "ballistica/base/dynamics/bg/bg_dynamics_world.h"
#include "ballistica/base/graphics/graphics.h"
#include "ballistica/base/graphics/support/camera.h"
#include "ballistica/base/graphics/support/render_view.h"
#include "ballistica/base/networking/networking.h"
#include "ballistica/base/python/support/python_context_call.h"
#include "ballistica/classic/support/classic_app_mode.h"
#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging_macros.h"
#include "ballistica/scene_v1/assets/scene_sound.h"
#include "ballistica/scene_v1/dynamics/dynamics.h"
#include "ballistica/scene_v1/dynamics/part.h"
#include "ballistica/scene_v1/node/node_attribute.h"
#include "ballistica/scene_v1/node/node_attribute_connection.h"
#include "ballistica/scene_v1/node/node_type.h"
#include "ballistica/scene_v1/node/player_node.h"
#include "ballistica/scene_v1/support/session_stream.h"

namespace ballistica::scene_v1 {

auto Scene::GetSceneStream() const -> SessionStream* {
  return output_stream_.get();
}

auto Scene::render_view() const -> base::RenderView* {
  if (render_view_.exists()) {
    return render_view_.get();
  }
  return g_base->graphics->main_view();
}

void Scene::set_render_view(base::RenderView* view) {
  // Nodes register things with their scene's view (its camera, for
  // one) as they are made, so this can't change out from under them.
  assert(nodes_.empty());
  render_view_ = view;

  // A world with a view of its own gets bg-dynamics of its own to go
  // with it, so its debris, smoke, and shadows are its alone. (Headless
  // builds have no bg-dynamics at all.)
  bg_dynamics_world_.Clear();
  if (view != nullptr && g_base->bg_dynamics != nullptr) {
    bg_dynamics_world_ = Object::New<base::BGDynamicsWorld>(view);
  }
}

auto Scene::bg_dynamics_world() const -> base::BGDynamicsWorld* {
  if (bg_dynamics_world_.exists()) {
    return bg_dynamics_world_.get();
  }
  if (g_base->bg_dynamics == nullptr) {
    return nullptr;
  }
  return g_base->bg_dynamics->main_world();
}

auto Scene::NewAudioSource() -> base::AudioSource* {
  if (silent_) {
    return nullptr;
  }
  base::AudioSource* source = g_base->audio->SourceBeginNew();
  if (source != nullptr && audio_listener_space_.has_value()) {
    source->SetListenerSpace(*audio_listener_space_);
  }
  return source;
}

void Scene::SetAudioListenerSpace(const base::AudioListenerSpace* space) {
  if (space == nullptr) {
    audio_listener_space_.reset();
  } else {
    audio_listener_space_ = *space;
  }
}

void Scene::SetMapBounds(float xmin, float ymin, float zmin, float xmax,
                         float ymax, float zmax) {
  bounds_min_[0] = xmin;
  bounds_min_[1] = ymin;
  bounds_min_[2] = zmin;
  bounds_max_[0] = xmax;
  bounds_max_[1] = ymax;
  bounds_max_[2] = zmax;
}

Scene::Scene(millisecs_t start_time)
    : time_(start_time),
      stepnum_(start_time / kGameStepMilliseconds),
      last_step_real_time_(g_core->AppTimeMillisecs()) {
  dynamics_ = Object::New<Dynamics>(this);

  // Reset world bounds to default.
  bounds_min_[0] = -30;
  bounds_max_[0] = 30;
  bounds_min_[1] = -10;
  bounds_max_[1] = 100;
  bounds_min_[2] = -30;
  bounds_max_[2] = 30;
}

Scene::~Scene() {
  // This may already be set to true by a host_activity/etc, but
  // make sure it is at this point.
  shutting_down_ = true;

  // Manually kill our nodes so they can remove all their own dynamics stuff
  // before dynamics goes down.
  nodes_.clear();

  dynamics_.Clear();

  // If we were associated with an output-stream, inform it of our demise.
  if (output_stream_.exists()) {
    output_stream_->RemoveScene(this);
  }
}

void Scene::PlaySoundAtPosition(SceneSound* sound, float volume, float x,
                                float y, float z, bool host_only) {
  if (output_stream_.exists() && !host_only) {
    output_stream_->PlaySoundAtPosition(sound, volume, x, y, z);
  }
  if (silent_) {
    return;
  }
  // With a listener of our own, go through one of our sources so it
  // places the sound for it.
  if (audio_listener_space_.has_value()) {
    if (!g_base->audio->ShouldPlay(sound->GetSoundData())) {
      return;
    }
    if (base::AudioSource* source = NewAudioSource()) {
      source->SetGain(volume);
      source->SetPosition(x, y, z);
      source->Play(sound->GetSoundData());
      source->End();
    }
    return;
  }
  g_base->audio->PlaySoundAtPosition(sound->GetSoundData(), volume, x, y, z);
}

void Scene::PlaySound(SceneSound* sound, float volume, bool host_only) {
  if (output_stream_.exists() && !host_only) {
    output_stream_->PlaySound(sound, volume);
  }
  if (silent_) {
    return;
  }
  // Unplaced sounds just take our listener's gain.
  if (audio_listener_space_.has_value()) {
    volume *= audio_listener_space_->gain;
  }
  g_base->audio->PlaySound(sound->GetSoundData(), volume);
}

auto Scene::IsOutOfBounds(float x, float y, float z) -> bool {
  if (std::isnan(x) || std::isnan(y) || std::isnan(z) || std::isinf(x)
      || std::isinf(y) || std::isinf(z))
    BA_LOG_ONCE(LogName::kBa, LogLevel::kError,
                "Got INF/NAN value on IsOutOfBounds() check");

  return ((x < bounds_min_[0]) || (x > bounds_max_[0]) || (y < bounds_min_[1])
          || (y > bounds_max_[1]) || (z < bounds_min_[2])
          || (z > bounds_max_[2]) || std::isnan(x) || std::isnan(y)
          || std::isnan(z) || std::isinf(x) || std::isinf(y) || std::isinf(z));
}

void Scene::Draw(base::FrameDef* frame_def) {
  // With bg-dynamics of our own, seeing to it is up to us. (The main
  // world's is shared by scenes that come and go, so Graphics sees to
  // that.) Nodes that show its results read them while drawing, so
  // pull the latest in first, waiting briefly for a step still in
  // flight.
  base::BGDynamicsWorld* own_bg_world = bg_dynamics_world_.get();
  if (own_bg_world != nullptr) {
    own_bg_world->AdoptResults(true);
  }

  // Draw our nodes.
  for (auto&& i : nodes_) {
    g_base->graphics->PreNodeDraw();
    i->Draw(frame_def);
    g_base->graphics->PostNodeDraw();
  }

  // Draw any dynamics debugging extras.
  dynamics_->Draw(frame_def);

  if (own_bg_world != nullptr) {
    own_bg_world->Draw(frame_def);
  }
}

auto Scene::GetNodeMessageType(const std::string& type) -> NodeMessageType {
  assert(g_scene_v1 != nullptr);
  auto i = g_scene_v1->node_message_types().find(type);
  if (i == g_scene_v1->node_message_types().end()) {
    throw Exception("Invalid node-message type: '" + type + "'");
  }
  return i->second;
}

auto Scene::GetNodeMessageTypeName(NodeMessageType t) -> std::string {
  assert(g_scene_v1 != nullptr);
  for (auto&& i : g_scene_v1->node_message_types()) {
    if (i.second == t) {
      return i.first;
    }
  }
  return "";
}

void Scene::SetPlayerNode(int id, PlayerNode* n) { player_nodes_[id] = n; }

auto Scene::GetPlayerNode(int id) -> PlayerNode* {
  auto i = player_nodes_.find(id);
  if (i != player_nodes_.end()) {
    return i->second.get();
  }
  return nullptr;
}

void Scene::Step() {
  out_of_bounds_nodes_.clear();

  auto* appmode = classic::ClassicAppMode::GetActiveOrFatal();

  // Step all our nodes.
  {
    in_step_ = true;
    last_step_real_time_ = g_core->AppTimeMillisecs();
    for (auto&& i : nodes_) {
      Node* node = i.get();
      node->Step();

      // Now that it's stepped, pump new values to any nodes it's connected to.
      node->UpdateConnections();
    }
    in_step_ = false;
  }
  bool is_foreground = (appmode->GetForegroundScene() == this);

  // Add a step command to the output stream.
  if (output_stream_.exists()) {
    output_stream_->StepScene(this);
  }

  // And step things locally.
  // The main world's bg-dynamics is shared by whichever scenes draw
  // through the main view, and steps with the one in the foreground. A
  // scene with its own steps its own, foreground or no.
  if (is_foreground || bg_dynamics_world_.exists()) {
    Vector3f cam_pos = {0.0f, 0.0f, 0.0f};
    render_view()->camera()->get_position(&cam_pos.x, &cam_pos.y, &cam_pos.z);
    if (base::BGDynamicsWorld* world = bg_dynamics_world()) {
      world->Step(cam_pos, kGameStepMilliseconds);
    }
  }

  // Lastly step our sim.
  dynamics_->Process();

  time_ += kGameStepMilliseconds;
  stepnum_++;
}

void Scene::DeleteNode(Node* node) {
  assert(node);

  // Clion incorrectly things in_step_ will always be false.
#pragma clang diagnostic push
#pragma ide diagnostic ignored "UnreachableCode"
#pragma ide diagnostic ignored "ConstantConditionsOC"
  if (in_step_) {
    throw Exception(
        "Cannot delete nodes within a sim step."
        " Consider a deferred call or timer. Node="
        + node->GetObjectDescription());
  }
#pragma clang diagnostic pop

  // Copy refs to its death-actions and dependent-nodes; we'll deal with these
  // after the node is dead so we're sure they don't muck with the node.
  std::vector<Object::Ref<base::PythonContextCall> > death_actions =
      node->death_actions();
  std::vector<Object::WeakRef<Node> > dependent_nodes = node->dependent_nodes();

  // Sanity test to make sure it dies when we ask.
#if BA_DEBUG_BUILD
  Object::WeakRef<Node> temp_weak_ref(node);
  BA_PRECONDITION(temp_weak_ref.exists());
#endif

  // Copy a strong ref to this node to keep it alive until we've wiped it from
  // the list. (so in its destructor it won't see itself on the list).
  Object::Ref<Node> temp_ref(node);
  nodes_.erase(node->iterator());

  temp_ref.Clear();

  // Sanity test: at this point the node should be dead.
#if BA_DEBUG_BUILD
  if (temp_weak_ref.exists()) {
    g_core->logging->Log(LogName::kBa, LogLevel::kError,
                         "Node still exists after ref release!!");
  }
#endif  // BA_DEBUG_BUILD

  // Lastly run any death actions the node had and kill dependent nodes.
  if (!shutting_down()) {
    for (auto&& i : death_actions) {
      i->Run();
    }
    for (auto&& i : dependent_nodes) {
      Node* node2 = i.get();
      if (node2) {
        node2->scene()->DeleteNode(node2);
      }
    }
  }
}

void Scene::OnScreenSizeChange() {
  assert(g_base->InLogicThread());
  for (auto&& i : nodes_) {
    i->OnScreenSizeChange();  // New.
  }
}

void Scene::LanguageChanged() {
  assert(g_base->InLogicThread());
  for (auto&& i : nodes_) {
    i->OnLanguageChange();  // New.
  }
}

auto Scene::GetNodeMessageFormat(NodeMessageType type) -> const char* {
  assert(g_scene_v1 != nullptr);
  if ((unsigned int)type >= g_scene_v1->node_message_formats().size()) {
    return nullptr;
  }
  return g_scene_v1->node_message_formats().at(static_cast<int>(type)).c_str();
}

auto Scene::NewNode(const std::string& type_string, const std::string& name,
                    PyObject* delegate) -> Node* {
  assert(g_base->InLogicThread());

  // Clion incorrectly things in_step_ will always be false.
#pragma clang diagnostic push
#pragma ide diagnostic ignored "UnreachableCode"
#pragma ide diagnostic ignored "ConstantConditionsOC"
  if (in_step_) {
    throw Exception(
        "Cannot create nodes within a sim step."
        " Consider a deferred call or timer.");
  }
#pragma clang diagnostic pop

  // Should never change the scene while we're stepping it.
  assert(!in_step_);
  assert(g_core != nullptr);
  auto i = g_scene_v1->node_types().find(type_string);
  if (i == g_scene_v1->node_types().end()) {
    throw Exception("Invalid node type: '" + type_string + "'");
  }
  auto node = Object::CompleteDeferred<Node>(i->second->Create(this));
  assert(node.exists());
  node->AddToScene(this);
  node->set_label(name);
  node->SetDelegate(delegate);
  return node.get();  // NOLINT
}

void Scene::Dump(SessionStream* stream) {
  assert(g_base->InLogicThread());
  auto* appmode = classic::ClassicAppMode::GetActiveOrFatal();
  stream->AddScene(this);

  // If we're the foreground one, communicate that fact as well.
  if (appmode->GetForegroundScene() == this) {
    stream->SetForegroundScene(this);
  }
}

void Scene::DumpNodes(SessionStream* out) {
  // Dumps commands to the output stream to recreate scene's nodes
  // in their current state.

  // First we go through and create all nodes.
  // We have to do this all at once before setting attrs since any node
  // can refer to any other in an attr set.
  for (auto&& i : nodes_) {
    Node* node = i.get();
    assert(node);

    // Add the node.
    out->AddNode(node);
  }

  std::vector<std::pair<NodeAttribute, Node*> > node_attr_sets;

  // Now go through and set *most* node attr values.
  for (auto&& i1 : nodes_) {
    Node* node = i1.get();
    assert(node);

    // Now we need to set *all* of its attrs in order.
    // FIXME: Could be nice to send only ones that have changed from
    //  defaults; would need to add that functionality to NodeType.
    NodeType* node_type = node->type();
    for (auto&& i2 : node_type->attributes_by_index()) {
      NodeAttribute attr;
      attr.assign(node, i2);
      if (!attr.is_read_only()) {
        switch (attr.type()) {
          case NodeAttributeType::kFloat: {
            out->SetNodeAttr(attr, attr.GetAsFloat());
            break;
          }
          case NodeAttributeType::kInt: {
            out->SetNodeAttr(attr, attr.GetAsInt());
            break;
          }
          case NodeAttributeType::kBool: {
            out->SetNodeAttr(attr, attr.GetAsBool());
            break;
          }
          case NodeAttributeType::kFloatArray: {
            out->SetNodeAttr(attr, attr.GetAsFloats());
            break;
          }
          case NodeAttributeType::kIntArray: {
            out->SetNodeAttr(attr, attr.GetAsInts());
            break;
          }
          case NodeAttributeType::kString: {
            out->SetNodeAttr(attr, attr.GetAsString());
            break;
          }
          case NodeAttributeType::kNode: {
            // Node-attrs are a special case - we can't set them until after
            // nodes are fully constructed. so lets just make a list of them
            // and do it at the end.
            node_attr_sets.emplace_back(attr, attr.GetAsNode());
            break;
          }
          case NodeAttributeType::kPlayer: {
            out->SetNodeAttr(attr, attr.GetAsPlayer());
            break;
          }
          case NodeAttributeType::kMaterialArray: {
            out->SetNodeAttr(attr, attr.GetAsMaterials());
            break;
          }
          case NodeAttributeType::kTexture: {
            out->SetNodeAttr(attr, attr.GetAsTexture());
            break;
          }
          case NodeAttributeType::kSpazDef: {
            out->SetNodeAttr(attr, attr.GetAsSpazDef());
            break;
          }
          case NodeAttributeType::kDepiction: {
            out->SetNodeAttr(attr, attr.GetAsDepiction());
            break;
          }
          case NodeAttributeType::kTextureArray: {
            out->SetNodeAttr(attr, attr.GetAsTextures());
            break;
          }
          case NodeAttributeType::kSound: {
            out->SetNodeAttr(attr, attr.GetAsSound());
            break;
          }
          case NodeAttributeType::kSoundArray: {
            out->SetNodeAttr(attr, attr.GetAsSounds());
            break;
          }
          case NodeAttributeType::kMesh: {
            out->SetNodeAttr(attr, attr.GetAsMesh());
            break;
          }
          case NodeAttributeType::kMeshArray: {
            out->SetNodeAttr(attr, attr.GetAsMeshes());
            break;
          }
          case NodeAttributeType::kCollisionMesh: {
            out->SetNodeAttr(attr, attr.GetAsCollisionMesh());
            break;
          }
          case NodeAttributeType::kCollisionMeshArray: {
            out->SetNodeAttr(attr, attr.GetAsCollisionMeshes());
            break;
          }
          default:
            g_core->logging->Log(
                LogName::kBa, LogLevel::kError,
                "Invalid attr type for Scene::DumpNodes() attr set: "
                    + std::to_string(static_cast<int>(attr.type())));
            break;
        }
      }
    }
  }

  // Now run through all nodes once more and add an OnCreate() call
  // so they can do any post-create setup they need to.
  for (auto&& i : nodes_) {
    Node* node = i.get();
    assert(node);
    out->NodeOnCreate(node);
  }

  // Set any node-attribute values now that all nodes are fully constructed.
  for (auto&& i : node_attr_sets) {
    out->SetNodeAttr(i.first, i.second);
  }

  // And lastly re-establish node attribute-connections.
  for (auto&& i : nodes_) {
    Node* node = i.get();
    assert(node);
    for (auto&& j : node->attribute_connections()) {
      assert(j.exists());
      Node* src_node = j->src_node.get();
      assert(src_node);
      Node* dst_node = j->dst_node.get();
      assert(dst_node);
      NodeAttributeUnbound* src_attr =
          src_node->type()->GetAttribute(j->src_attr_index);
      NodeAttributeUnbound* dst_attr =
          dst_node->type()->GetAttribute(j->dst_attr_index);
      out->ConnectNodeAttribute(src_node, src_attr, dst_node, dst_attr);
    }
  }
}

auto Scene::GetCorrectionMessageCompact_(bool blended) -> std::vector<uint8_t> {
  // Body payload first; the node count goes in front as a varint once
  // we know it.
  std::vector<uint8_t> payload;
  uint32_t node_count = 0;
  std::vector<RigidBody*> dynamic_bodies;
  for (auto&& i : nodes_) {
    Node* n = i.get();
    assert(n);
    if (!n || n->parts().empty()) {
      continue;
    }
    dynamic_bodies.clear();
    for (auto&& j : n->parts()) {
      for (auto&& k : j->rigid_bodies()) {
        if (k->type() == RigidBody::Type::kBody) {
          dynamic_bodies.push_back(k);
        }
      }
    }
    if (dynamic_bodies.empty()) {
      continue;
    }
    node_count++;
    AppendVarint(&payload, static_cast_check_fit<uint32_t>(n->stream_id()));
    payload.push_back(static_cast_check_fit<uint8_t>(dynamic_bodies.size()));
    for (auto* b : dynamic_bodies) {
      payload.push_back(static_cast_check_fit<uint8_t>(b->id()));
      b->EmbedCompact(&payload);
    }
    std::vector<uint8_t> resync = n->GetResyncData();
    AppendVarint(&payload, static_cast_check_fit<uint32_t>(resync.size()));
    payload.insert(payload.end(), resync.begin(), resync.end());
  }
  // An empty correction is 3 bytes here (callers treat <= 4 as empty).
  std::vector<uint8_t> message;
  message.reserve(payload.size() + 8);
  message.push_back(BA_MESSAGE_SESSION_DYNAMICS_CORRECTION);
  message.push_back(static_cast<uint8_t>(blended));
  AppendVarint(&message, node_count);
  message.insert(message.end(), payload.begin(), payload.end());
  return message;
}

auto Scene::GetCorrectionMessage(bool blended) -> std::vector<uint8_t> {
  if (protocol_version() >= kProtocolVersionCompactCorrections) {
    return GetCorrectionMessageCompact_(blended);
  }

  // Let's loop over our nodes sending a bit of correction data.

  // Go through until we find at least 1 node to send corrections for,
  // or until we loop all the way through.

  // 1 byte type, 1 byte blending, 2 byte node count
  std::vector<uint8_t> message(4);
  message[0] = BA_MESSAGE_SESSION_DYNAMICS_CORRECTION;
  message[1] = static_cast<uint8_t>(blended);
  int node_count = 0;

  std::vector<RigidBody*> dynamic_bodies;

  for (auto&& i : nodes_) {
    Node* n = i.get();
    assert(n);
    if (n && !n->parts().empty()) {
      dynamic_bodies.clear();
      for (auto&& j : n->parts()) {
        if (!j->rigid_bodies().empty()) {
          for (auto&& k : j->rigid_bodies()) {
            if (k->type() == RigidBody::Type::kBody) {
              dynamic_bodies.push_back(k);
            }
          }
        }
      }
      if (!dynamic_bodies.empty()) {
        int node_embed_size = 5;  // 4 byte node-ID and 1 byte body-count
        int body_count = 0;
        for (auto&& i2 : dynamic_bodies) {
          node_embed_size += 3 + i2->GetEmbeddedSizeFull();
          body_count++;
        }

        // Lastly add custom data.
        node_embed_size += 2;  // size
        int resync_data_size = n->GetResyncDataSize();
        node_embed_size += resync_data_size;

        // If this size puts us over our max packet size (and we've got
        // something in the packet already) just ship what we've got.
        // We'll come back to this one next time.
        {
          node_count++;
          size_t old_size = message.size();
          message.resize(old_size + node_embed_size);

          // Embed node id.
          auto stream_id_val = static_cast_check_fit<uint32_t>(n->stream_id());
          memcpy(message.data() + old_size, &stream_id_val,
                 sizeof(stream_id_val));

          // Embed body count.
          message[old_size + 4] = static_cast_check_fit<uint8_t>(body_count);
          size_t offset = old_size + 5;
          for (auto&& i2 : dynamic_bodies) {
            // Embed body id.
            message[offset++] = static_cast_check_fit<uint8_t>(i2->id());
            int body_embed_size = i2->GetEmbeddedSizeFull();

            // Embed body size.
            auto val = static_cast_check_fit<uint16_t>(body_embed_size);
            memcpy(message.data() + offset, &val, sizeof(val));
            offset += 2;
            char* p1 = reinterpret_cast<char*>(&(message[offset]));
            char* p2 = p1;
            i2->EmbedFull(&p2);
            assert(p2 - p1 == body_embed_size);
            offset += body_embed_size;
          }

          // Lastly embed custom data size and custom data.
          auto val = static_cast_check_fit<uint16_t>(resync_data_size);
          memcpy(message.data() + offset, &val, sizeof(val));
          offset += 2;
          if (resync_data_size > 0) {
            std::vector<uint8_t> resync_data = n->GetResyncData();
            assert(resync_data.size() == resync_data_size);
            memcpy(message.data() + offset, &(resync_data[0]),
                   resync_data.size());
            offset += resync_data_size;
          }
          assert(offset == message.size());
        }
      }
    }
  }

  // If we embedded any nodes, send.
  // Store node count in packet.
  auto val = static_cast_check_fit<uint16_t>(node_count);
  memcpy(message.data() + 2, &val, sizeof(val));

  return message;
}

void Scene::SetOutputStream(SessionStream* val) { output_stream_ = val; }

void Scene::AddNode(Node* node, int64_t* node_id, NodeList::iterator* i) {
  assert(node && node_id && i);
  *node_id = next_node_id_++;
  *i = nodes_.insert(nodes_.end(), Object::Ref<Node>(node));
}

}  // namespace ballistica::scene_v1
