// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_GRAPHICS_NET_GRAPH_H_
#define BALLISTICA_GRAPHICS_NET_GRAPH_H_

#include <memory>

#include "ballistica/core/object.h"

namespace ballistica {

class NetGraph : public Object {
 public:
  NetGraph();
  ~NetGraph() override;
  void AddSample(double time, double value);
  void Draw(RenderPass* pass, double time, double x, double y, double w,
            double h);

 private:
  class Impl;
  std::unique_ptr<Impl> impl_;
};

}  // namespace ballistica

#endif  // BALLISTICA_GRAPHICS_NET_GRAPH_H_
