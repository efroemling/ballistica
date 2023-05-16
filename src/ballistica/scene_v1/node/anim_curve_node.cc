// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/node/anim_curve_node.h"

#include <cmath>

#include "ballistica/scene_v1/node/node_attribute.h"
#include "ballistica/scene_v1/node/node_type.h"

namespace ballistica::scene_v1 {

class AnimCurveNodeType : public NodeType {
 public:
#define BA_NODE_TYPE_CLASS AnimCurveNode
  BA_NODE_CREATE_CALL(CreateAnimCurve);
  BA_FLOAT_ATTR(in, in, set_in);
  BA_BOOL_ATTR(loop, loop, set_loop);
  BA_INT64_ARRAY_ATTR(times, times, set_times);
  BA_FLOAT_ARRAY_ATTR(values, values, set_values);
  BA_FLOAT_ATTR(offset, offset, set_offset);
  BA_FLOAT_ATTR_READONLY(out, GetOut);
#undef BA_NODE_TYPE_CLASS

  AnimCurveNodeType()
      : NodeType("animcurve", CreateAnimCurve),
        in(this),
        loop(this),
        times(this),
        values(this),
        offset(this),
        out(this) {}
};

static NodeType* node_type{};

auto AnimCurveNode::InitType() -> NodeType* {
  node_type = new AnimCurveNodeType();
  return node_type;
}

AnimCurveNode::AnimCurveNode(Scene* scene) : Node(scene, node_type) {}

AnimCurveNode::~AnimCurveNode() = default;

auto AnimCurveNode::GetOut() -> float {
  // Recreate our keyframes if need be.
  if (keys_dirty_) {
    keyframes_.clear();
    auto num = std::min(times_.size(), values_.size());
    if (num < 1) {
      input_start_ = 0;
      input_end_ = 0;
    }
    for (size_t i = 0; i < num; i++) {
      if (i == 0) {
        input_start_ = static_cast<float>(times_[i]);
      }
      if (i == (num - 1)) {
        input_end_ = static_cast<float>(times_[i]);
      }
      keyframes_.emplace_back(times_[i], values_[i]);
    }
    keys_dirty_ = false;
    out_dirty_ = true;
  }

  // Now update out if need-be.
  if (out_dirty_) {
    float in_val = in_ - offset_;
    if ((input_end_ - input_start_) > 0) {
      if (keyframes_.size() < 2) {
        assert(keyframes_.size() == 1);
        out_ = keyframes_[0].value;
      } else {
        bool got;
        if (loop_) {
          in_val = fmodf(in_val, (input_end_ - input_start_));
          if (in_val < 0) {
            in_val += (input_end_ - input_start_);
          }
          got = false;
        } else {
          if (in_val >= input_end_) {
            out_ = keyframes_.back().value;
            got = true;
          } else if (in_val <= input_start_) {
            out_ = keyframes_.front().value;
            got = true;
          } else {
            got = false;
          }
        }
        if (!got) {
          // out_ = keyframes_[0].value;

          // Ok we know we've got at least 2 keyframes.
          auto i1 = keyframes_.begin();
          auto i2 = keyframes_.begin();
          auto i = keyframes_.begin();
          while (true) {
            if (i == keyframes_.end()) {
              break;
            }
            if (static_cast<float>(i->time) < in_val) {
              i++;
              i1 = i2;
              i2 = i;
            } else {
              break;
            }
          }
          if (i2->time - i1->time == 0) {
            out_ = i1->value;
          } else {
            out_ = i1->value
                   + ((in_val - static_cast<float>(i1->time))
                      / static_cast<float>(i2->time - i1->time))
                         * (i2->value - i1->value);
          }
        }
      }
    } else {
      // No keyframes?.. hmm, just go with 0.
      if (keyframes_.empty()) {
        out_ = 0.0f;
      } else {
        // We have one keyframe; hmm what to do.
        out_ = keyframes_[0].value;
      }
    }
    out_dirty_ = false;
  }
  return out_;
}

}  // namespace ballistica::scene_v1
