// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_NODE_NODE_TYPE_H_
#define BALLISTICA_SCENE_V1_NODE_NODE_TYPE_H_

#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

#include "ballistica/scene_v1/scene_v1.h"
#include "ballistica/shared/foundation/exception.h"
#include "ballistica/shared/foundation/macros.h"

namespace ballistica::scene_v1 {

// Type structure for a node, storing attribute lists and other static type
// data.
class NodeType {
 public:
  NodeType(std::string name, NodeCreateFunc* create_call)
      : name_(std::move(name)), create_call_(create_call), id_(-1) {}

  /// Return an unbound attribute by name; if missing either throws an exception
  /// or returns nullptr.
  auto GetAttribute(const std::string& name, bool throw_if_missing = true) const
      -> NodeAttributeUnbound* {
    auto i = attributes_by_name_.find(name);
    if (i == attributes_by_name_.end()) {
      if (throw_if_missing) {
        throw Exception("Attribute not found: '" + name + "'");
      } else {
        return nullptr;
      }
    }
    return i->second;
  }
  ~NodeType();

  /// Return an unbound attribute by index.
  auto GetAttribute(int index) const -> NodeAttributeUnbound* {
    BA_PRECONDITION(
        index >= 0
        && index < static_cast_check_fit<int>(attributes_by_index_.size()));
    return attributes_by_index_[index];
  }

  auto HasAttribute(const std::string& name) const -> bool {
    return (GetAttribute(name, false) != nullptr);
  }

  auto name() const -> std::string { return name_; }

  auto GetAttributeNames() const -> std::vector<std::string>;

  auto Create(Scene* sg) -> Node* {
    assert(create_call_);
    return create_call_(sg);
  }

  auto id() const -> int {
    assert(id_ >= 0);
    return id_;
  }

  void set_id(int val) { id_ = val; }
  auto attributes_by_index() const
      -> const std::vector<NodeAttributeUnbound*>& {
    return attributes_by_index_;
  }

 private:
  NodeCreateFunc* create_call_;
  int id_;
  std::string name_;
  std::unordered_map<std::string, NodeAttributeUnbound*> attributes_by_name_;
  std::vector<NodeAttributeUnbound*> attributes_by_index_;
  friend class NodeAttributeUnbound;
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_NODE_NODE_TYPE_H_
