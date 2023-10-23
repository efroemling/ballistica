// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_SUPPORT_SCENE_H_
#define BALLISTICA_SCENE_V1_SUPPORT_SCENE_H_

#include <string>
#include <unordered_map>
#include <vector>

#include "ballistica/base/logic/logic.h"
#include "ballistica/scene_v1/node/node.h"
#include "ballistica/shared/foundation/object.h"

namespace ballistica::scene_v1 {

/// A place where nodes/actors/etc. live.
class Scene : public Object {
 public:
  explicit Scene(millisecs_t starttime);
  ~Scene() override;
  void Step();
  void Draw(base::FrameDef* frame_def);
  auto NewNode(const std::string& type, const std::string& name,
               PyObject* delegate) -> Node*;
  void PlaySoundAtPosition(SceneSound* sound, float volume, float x, float y,
                           float z, bool host_only = false);
  void PlaySound(SceneSound* sound, float volume, bool host_only = false);
  static auto GetNodeMessageType(const std::string& type_name)
      -> NodeMessageType;
  static auto GetNodeMessageTypeName(NodeMessageType t) -> std::string;
  static auto GetNodeMessageFormat(NodeMessageType type) -> const char*;
  auto time() const -> millisecs_t { return time_; }
  auto stepnum() const -> int64_t { return stepnum_; }
  auto nodes() const -> const NodeList& { return nodes_; }
  void AddNode(Node*, int64_t* node_id, NodeList::iterator* i);
  void AddOutOfBoundsNode(Node* n) { out_of_bounds_nodes_.emplace_back(n); }
  auto IsOutOfBounds(float x, float y, float z) -> bool;
  auto dynamics() const -> Dynamics* {
    assert(dynamics_.Exists());
    return dynamics_.Get();
  }
  auto in_step() const -> bool { return in_step_; }
  void SetMapBounds(float x, float y, float z, float X, float Y, float Z);
  void OnScreenSizeChange();
  void LanguageChanged();
  auto out_of_bounds_nodes() -> const std::vector<Object::WeakRef<Node> >& {
    return out_of_bounds_nodes_;
  }
  void DeleteNode(Node* node);
  auto shutting_down() const -> bool { return shutting_down_; }
  void set_shutting_down(bool val) { shutting_down_ = val; }
  auto GetSceneStream() const -> SessionStream*;
  void SetPlayerNode(int id, PlayerNode* n);
  auto GetPlayerNode(int id) -> PlayerNode*;
  auto use_fixed_vr_overlay() const -> bool { return use_fixed_vr_overlay_; }
  void set_use_fixed_vr_overlay(bool val) { use_fixed_vr_overlay_ = val; }
  void increment_bg_cover_count() { bg_cover_count_++; }
  void decrement_bg_cover_count() { bg_cover_count_--; }
  auto has_bg_cover() const -> bool { return (bg_cover_count_ > 0); }
  void Dump(SessionStream* out);
  void DumpNodes(SessionStream* out);
  auto GetCorrectionMessage(bool blended) -> std::vector<uint8_t>;

  void SetOutputStream(SessionStream* val);
  auto stream_id() const -> int64_t { return stream_id_; }
  void set_stream_id(int64_t val) {
    assert(stream_id_ == -1);
    stream_id_ = val;
  }
  void clear_stream_id() {
    assert(stream_id_ != -1);
    stream_id_ = -1;
  }

  auto last_step_real_time() const -> millisecs_t {
    return last_step_real_time_;
  }
  auto globals_node() const -> GlobalsNode* { return globals_node_; }
  void set_globals_node(GlobalsNode* node) { globals_node_ = node; }

 private:
  GlobalsNode* globals_node_{};  // Current globals node (if any).
  std::unordered_map<int, Object::WeakRef<PlayerNode> > player_nodes_;
  int64_t stream_id_{-1};
  Object::WeakRef<SessionStream> output_stream_;
  bool use_fixed_vr_overlay_{};
  base::ContextRef context_;  // Context we were made in.
  millisecs_t time_{};
  int64_t stepnum_{};
  bool in_step_{};
  int64_t next_node_id_{};

  // For globals real_time attr (so is consistent through the step.)
  millisecs_t last_step_real_time_{};
  int bg_cover_count_{};
  bool shutting_down_{};
  float bounds_min_[3]{};
  float bounds_max_[3]{};
  std::vector<Object::WeakRef<Node> > out_of_bounds_nodes_;
  NodeList nodes_;
  Object::Ref<Dynamics> dynamics_;
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_SUPPORT_SCENE_H_
