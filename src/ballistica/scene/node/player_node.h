// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_NODE_PLAYER_NODE_H_
#define BALLISTICA_SCENE_NODE_PLAYER_NODE_H_

#include <vector>

#include "ballistica/scene/node/node.h"

namespace ballistica {

class PlayerNode : public Node {
 public:
  static auto InitType() -> NodeType*;
  explicit PlayerNode(Scene* scene);
  ~PlayerNode() override;
  auto position() const -> const std::vector<float>& { return position_; }
  void SetPosition(const std::vector<float>& vals);
  auto player_id() const -> int { return player_id_; }
  void SetPlayerID(int val);

 private:
  int player_id_{-1};
  std::vector<float> position_{0.0f, 0.0f, 0.0f};
};

}  // namespace ballistica

#endif  // BALLISTICA_SCENE_NODE_PLAYER_NODE_H_
