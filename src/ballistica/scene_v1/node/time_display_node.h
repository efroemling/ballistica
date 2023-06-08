// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_NODE_TIME_DISPLAY_NODE_H_
#define BALLISTICA_SCENE_V1_NODE_TIME_DISPLAY_NODE_H_

#include <string>

#include "ballistica/scene_v1/node/node.h"

namespace ballistica::scene_v1 {

class TimeDisplayNode : public Node {
 public:
  static auto InitType() -> NodeType*;
  auto GetOutput() -> std::string;
  auto time2() const -> millisecs_t { return time2_; }
  void set_time2(millisecs_t value) {
    if (time2_ != value) {
      time2_ = value;
      output_dirty_ = true;
    }
  }
  auto time1() const -> millisecs_t { return time1_; }
  void set_time1(millisecs_t value) {
    if (time1_ != value) {
      time1_ = value;
      output_dirty_ = true;
    }
  }
  auto time_min() const -> millisecs_t { return time_min_; }
  void set_time_min(millisecs_t val) {
    if (time_min_ != val) {
      time_min_ = val;
      output_dirty_ = true;
    }
  }
  auto time_max() const -> millisecs_t { return time_max_; }
  void set_time_max(millisecs_t val) {
    if (time_max_ != val) {
      time_max_ = val;
      output_dirty_ = true;
    }
  }
  auto show_sub_seconds() const -> bool { return show_sub_seconds_; }
  void set_show_sub_seconds(bool val) {
    if (show_sub_seconds_ != val) {
      show_sub_seconds_ = val;
      output_dirty_ = true;
    }
  }
  explicit TimeDisplayNode(Scene* scene);
  ~TimeDisplayNode() override;
  void OnLanguageChange() override;

 private:
  bool output_dirty_{true};
  std::string output_;
  millisecs_t time_min_{-999999999};
  millisecs_t time_max_{999999999};
  millisecs_t time2_{};
  millisecs_t time1_{};
  bool show_sub_seconds_{};
  std::string time_suffix_hours_;
  std::string time_suffix_minutes_;
  std::string time_suffix_seconds_;
  bool translations_dirty_{true};
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_NODE_TIME_DISPLAY_NODE_H_
