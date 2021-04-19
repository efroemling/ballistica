// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_GRAPHICS_NET_GRAPH_H_
#define BALLISTICA_GRAPHICS_NET_GRAPH_H_

#include <memory>
#include <string>

#include "ballistica/core/object.h"

namespace ballistica {

class NetGraph : public Object {
 public:
  NetGraph();
  ~NetGraph() override;
  auto AddSample(double time, double value) -> void;
  auto SetLabel(const std::string& label) -> void;
  auto SetLastUsedTime(millisecs_t real_time) -> void;
  auto LastUsedTime() -> millisecs_t;
  auto SetSmoothed(bool smoothed) -> void;
  auto Draw(RenderPass* pass, double time, double x, double y, double w,
            double h) -> void;

 private:
  class Impl;
  std::unique_ptr<Impl> impl_;
};

}  // namespace ballistica

#endif  // BALLISTICA_GRAPHICS_NET_GRAPH_H_
