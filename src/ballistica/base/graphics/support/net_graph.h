// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_GRAPHICS_SUPPORT_NET_GRAPH_H_
#define BALLISTICA_BASE_GRAPHICS_SUPPORT_NET_GRAPH_H_

#include <memory>
#include <string>

#include "ballistica/base/base.h"
#include "ballistica/shared/foundation/object.h"

namespace ballistica::base {

class NetGraph : public Object {
 public:
  NetGraph();
  ~NetGraph() override;
  void AddSample(double time, double value);
  void SetLabel(const std::string& label);
  void SetLastUsedTime(millisecs_t real_time);
  auto LastUsedTime() -> millisecs_t;
  void SetSmoothed(bool smoothed);
  void Draw(RenderPass* pass, double time, double x, double y, double w,
            double h);

 private:
  class Impl;
  std::unique_ptr<Impl> impl_;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_GRAPHICS_SUPPORT_NET_GRAPH_H_
