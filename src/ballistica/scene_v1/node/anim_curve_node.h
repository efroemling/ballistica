// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_NODE_ANIM_CURVE_NODE_H_
#define BALLISTICA_SCENE_V1_NODE_ANIM_CURVE_NODE_H_

#include <vector>

#include "ballistica/scene_v1/node/node.h"

namespace ballistica::scene_v1 {

// Node containing a keyframe graph associating an input value with an output
// value.
class AnimCurveNode : public Node {
 public:
  static auto InitType() -> NodeType*;

  explicit AnimCurveNode(Scene* scene);
  ~AnimCurveNode() override;

  auto in() const -> float { return in_; }
  void set_in(float value) {
    in_ = value;
    out_dirty_ = true;
  }

  auto loop() const -> bool { return loop_; }
  void set_loop(bool val) {
    loop_ = val;
    out_dirty_ = true;
  }

  auto times() const -> const std::vector<millisecs_t>& { return times_; }
  void set_times(const std::vector<millisecs_t>& vals) {
    times_ = vals;
    keys_dirty_ = true;
  }

  auto values() const -> const std::vector<float>& { return values_; }
  void set_values(const std::vector<float>& vals) {
    values_ = vals;
    keys_dirty_ = true;
  }

  auto offset() const -> float { return offset_; }
  void set_offset(float val) {
    offset_ = val;
    out_dirty_ = true;
  }

  auto GetOut() -> float;

 private:
  struct Keyframe {
    Keyframe(uint32_t t, float v) : time(t), value(v) {}
    uint32_t time;
    float value;
  };

  float in_ = 0.0f;
  std::vector<millisecs_t> times_;
  std::vector<float> values_;
  bool keys_dirty_ = true;
  bool out_dirty_ = true;
  float out_ = 0.0f;
  bool loop_ = true;
  std::vector<Keyframe> keyframes_;
  float input_start_ = 0.0f;
  float input_end_ = 0.0f;
  float offset_ = 0.0f;
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_NODE_ANIM_CURVE_NODE_H_
