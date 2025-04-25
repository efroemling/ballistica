// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/node/time_display_node.h"

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <string>

#include "ballistica/base/assets/assets.h"
#include "ballistica/scene_v1/node/node_attribute.h"
#include "ballistica/scene_v1/node/node_type.h"
#include "ballistica/shared/generic/utils.h"

namespace ballistica::scene_v1 {

class TimeDisplayNodeType : public NodeType {
 public:
#define BA_NODE_TYPE_CLASS TimeDisplayNode
  BA_NODE_CREATE_CALL(CreateTimeDisplayNode);
  BA_STRING_ATTR_READONLY(output, GetOutput);
  BA_INT64_ATTR(time2, time2, set_time2);
  BA_INT64_ATTR(time1, time1, set_time1);
  BA_INT64_ATTR(timemin, time_min, set_time_min);
  BA_INT64_ATTR(timemax, time_max, set_time_max);
  BA_BOOL_ATTR(showsubseconds, show_sub_seconds, set_show_sub_seconds);
#undef BA_NODE_TYPE_CLASS

  TimeDisplayNodeType()
      : NodeType("timedisplay", CreateTimeDisplayNode),
        output(this),
        time2(this),
        time1(this),
        timemin(this),
        timemax(this),
        showsubseconds(this) {}
};

static NodeType* node_type{};

auto TimeDisplayNode::InitType() -> NodeType* {
  node_type = new TimeDisplayNodeType();
  return node_type;
}

TimeDisplayNode::TimeDisplayNode(Scene* scene) : Node(scene, node_type) {}

TimeDisplayNode::~TimeDisplayNode() = default;

auto TimeDisplayNode::GetOutput() -> std::string {
  assert(g_base->InLogicThread());
  if (translations_dirty_) {
    time_suffix_hours_ =
        g_base->assets->CompileResourceString(R"({"r":"timeSuffixHoursText"})");
    time_suffix_minutes_ = g_base->assets->CompileResourceString(
        R"({"r":"timeSuffixMinutesText"})");
    time_suffix_seconds_ = g_base->assets->CompileResourceString(
        R"({"r":"timeSuffixSecondsText"})");
    translations_dirty_ = false;
    output_dirty_ = true;
  }
  if (output_dirty_) {
    millisecs_t t = time2_ - time1_;
    t = std::min(t, time_max_);
    t = std::max(t, time_min_);
    output_ = "";
    bool is_negative = false;
    if (t < 0) {
      t = -t;
      is_negative = true;
    }

    // Drop the last digit to better line up with in-game math.
    t = (t / 10) * 10;

    // Hours.
    int h = static_cast_check_fit<int>((t / 1000) / (60 * 60));
    if (h != 0) {
      std::string s = time_suffix_hours_;
      char buffer[100];
      snprintf(buffer, sizeof(buffer), "%d", h);
      Utils::StringReplaceOne(&s, "${COUNT}", buffer);
      if (!output_.empty()) {
        output_ += " ";
      }
      output_ += s;
    }

    // Minutes.
    int m = static_cast_check_fit<int>(((t / 1000) / 60) % 60);
    if (m != 0) {
      std::string s = time_suffix_minutes_;
      char buffer[100];
      snprintf(buffer, sizeof(buffer), "%d", m);
      Utils::StringReplaceOne(&s, "${COUNT}", buffer);
      if (!output_.empty()) {
        output_ += " ";
      }
      output_ += s;
    }

    // Seconds (with hundredths).
    if (show_sub_seconds_) {
      float sec = fmod(static_cast<float>(t) / 1000.0f, 60.0f);
      if (sec >= 0.005f || output_.empty()) {
        std::string s = time_suffix_seconds_;
        char buffer[100];
        snprintf(buffer, sizeof(buffer), "%.2f", sec);
        Utils::StringReplaceOne(&s, "${COUNT}", buffer);
        if (!output_.empty()) {
          output_ += " ";
        }
        output_ += s;
      }
    } else {
      // Seconds (integer).
      int sec = static_cast_check_fit<int>(t / 1000 % 60);
      if (sec != 0 || output_.empty()) {
        std::string s = time_suffix_seconds_;
        char buffer[100];
        snprintf(buffer, sizeof(buffer), "%d", sec);
        Utils::StringReplaceOne(&s, "${COUNT}", buffer);
        if (!output_.empty()) {
          output_ += " ";
        }
        output_ += s;
      }
    }
    if (is_negative) {
      output_ = "-" + output_;
    }
    output_dirty_ = false;
  }
  return output_;
}

void TimeDisplayNode::OnLanguageChange() { translations_dirty_ = true; }

}  // namespace ballistica::scene_v1
