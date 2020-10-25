// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_SCENE_H_
#define BALLISTICA_SCENE_SCENE_H_

#include <string>
#include <unordered_map>
#include <vector>

#include "ballistica/core/object.h"
#include "ballistica/game/game.h"
#include "ballistica/scene/node/node.h"

namespace ballistica {

class Scene : public Object {
 public:
  static auto Init() -> void;
  explicit Scene(millisecs_t starttime);
  ~Scene() override;
  auto Step() -> void;
  auto Draw(FrameDef* frame_def) -> void;
  auto NewNode(const std::string& type, const std::string& name,
               PyObject* delegate) -> Node*;
  auto PlaySoundAtPosition(Sound* sound, float volume, float x, float y,
                           float z, bool host_only = false) -> void;
  auto PlaySound(Sound* sound, float volume, bool host_only = false) -> void;
  static auto GetNodeMessageType(const std::string& type_name)
      -> NodeMessageType;
  static auto GetNodeMessageTypeName(NodeMessageType t) -> std::string;
  static auto GetNodeMessageFormat(NodeMessageType type) -> const char*;
  auto time() const -> millisecs_t { return time_; }
  auto stepnum() const -> int64_t { return stepnum_; }
  auto nodes() const -> const NodeList& { return nodes_; }
  auto AddNode(Node*, int64_t* node_id, NodeList::iterator* i) -> void;
  auto AddOutOfBoundsNode(Node* n) -> void {
    out_of_bounds_nodes_.emplace_back(n);
  }
  auto IsOutOfBounds(float x, float y, float z) -> bool;
  auto dynamics() const -> Dynamics* {
    assert(dynamics_.exists());
    return dynamics_.get();
  }
  auto in_step() const -> bool { return in_step_; }
  auto SetMapBounds(float x, float y, float z, float X, float Y, float Z)
      -> void;
  auto ScreenSizeChanged() -> void;
  auto LanguageChanged() -> void;
  auto GraphicsQualityChanged(GraphicsQuality q) -> void;
  auto out_of_bounds_nodes() -> const std::vector<Object::WeakRef<Node> >& {
    return out_of_bounds_nodes_;
  }
  auto DeleteNode(Node* node) -> void;
  auto shutting_down() const -> bool { return shutting_down_; }
  auto set_shutting_down(bool val) -> void { shutting_down_ = val; }
  auto GetGameStream() const -> GameStream*;
  auto SetPlayerNode(int id, PlayerNode* n) -> void;
  auto GetPlayerNode(int id) -> PlayerNode*;
  auto use_fixed_vr_overlay() const -> bool { return use_fixed_vr_overlay_; }
  auto set_use_fixed_vr_overlay(bool val) -> void {
    use_fixed_vr_overlay_ = val;
  }
  auto increment_bg_cover_count() -> void { bg_cover_count_++; }
  auto decrement_bg_cover_count() -> void { bg_cover_count_--; }
  auto has_bg_cover() const -> bool { return (bg_cover_count_ > 0); }
  auto Dump(GameStream* out) -> void;
  auto DumpNodes(GameStream* out) -> void;
  auto GetCorrectionMessage(bool blended) -> std::vector<uint8_t>;

  auto SetOutputStream(GameStream* val) -> void;
  auto stream_id() const -> int64_t { return stream_id_; }
  auto set_stream_id(int64_t val) -> void {
    assert(stream_id_ == -1);
    stream_id_ = val;
  }
  auto clear_stream_id() -> void {
    assert(stream_id_ != -1);
    stream_id_ = -1;
  }

  auto last_step_real_time() const -> millisecs_t {
    return last_step_real_time_;
  }
  auto globals_node() const -> GlobalsNode* { return globals_node_; }
  auto set_globals_node(GlobalsNode* node) -> void { globals_node_ = node; }

 private:
  static auto SetupNodeMessageType(const std::string& name, NodeMessageType val,
                                   const std::string& format) -> void;

  GlobalsNode* globals_node_{};  // Current globals node (if any).
  std::unordered_map<int, Object::WeakRef<PlayerNode> > player_nodes_;
  int64_t stream_id_{-1};
  Object::WeakRef<GameStream> output_stream_;
  bool use_fixed_vr_overlay_{};
  Context context_;  // Context we were made in.
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

}  // namespace ballistica

#endif  // BALLISTICA_SCENE_SCENE_H_
