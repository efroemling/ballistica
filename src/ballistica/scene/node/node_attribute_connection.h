// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_NODE_NODE_ATTRIBUTE_CONNECTION_H_
#define BALLISTICA_SCENE_NODE_NODE_ATTRIBUTE_CONNECTION_H_

#include <list>

#include "ballistica/core/object.h"

namespace ballistica {

class NodeAttributeConnection : public Object {
 public:
  NodeAttributeConnection() = default;
  void Update();
  Object::WeakRef<Node> src_node;
  int src_attr_index{};
  Object::WeakRef<Node> dst_node;
  int dst_attr_index{};
  bool have_error{};
  std::list<Object::Ref<NodeAttributeConnection> >::iterator src_iterator;
};

}  // namespace ballistica

#endif  // BALLISTICA_SCENE_NODE_NODE_ATTRIBUTE_CONNECTION_H_
