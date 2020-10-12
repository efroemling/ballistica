// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_NODE_SESSION_GLOBALS_NODE_H_
#define BALLISTICA_SCENE_NODE_SESSION_GLOBALS_NODE_H_

#include "ballistica/scene/node/node.h"

namespace ballistica {

class SessionGlobalsNode : public Node {
 public:
  static auto InitType() -> NodeType*;
  explicit SessionGlobalsNode(Scene* scene);
  ~SessionGlobalsNode() override;
  auto GetRealTime() -> millisecs_t;
  auto GetTime() -> millisecs_t;
  auto GetStep() -> int64_t;
};

}  // namespace ballistica

#endif  // BALLISTICA_SCENE_NODE_SESSION_GLOBALS_NODE_H_
