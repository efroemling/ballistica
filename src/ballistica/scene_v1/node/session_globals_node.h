// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_NODE_SESSION_GLOBALS_NODE_H_
#define BALLISTICA_SCENE_V1_NODE_SESSION_GLOBALS_NODE_H_

#include "ballistica/scene_v1/node/node.h"

namespace ballistica::scene_v1 {

class SessionGlobalsNode : public Node {
 public:
  static auto InitType() -> NodeType*;
  explicit SessionGlobalsNode(Scene* scene);
  ~SessionGlobalsNode() override;
  auto AppTimeMillisecs() -> millisecs_t;
  auto GetTime() -> millisecs_t;
  auto GetStep() -> int64_t;
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_NODE_SESSION_GLOBALS_NODE_H_
