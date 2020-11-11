// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_NODE_NODE_ATTRIBUTE_H_
#define BALLISTICA_SCENE_NODE_NODE_ATTRIBUTE_H_

#include <string>
#include <vector>

#include "ballistica/ballistica.h"

namespace ballistica {

#pragma clang diagnostic push
#pragma ide diagnostic ignored "OCUnusedMacroInspection"

// Unbound node attribute; these are statically stored in a node type
// and contain logic to get/set a particular attribute on a node
// in various ways.
class NodeAttributeUnbound {
 public:
  static auto GetNodeAttributeTypeName(NodeAttributeType) -> std::string;

  NodeAttributeUnbound(NodeType* node_type, NodeAttributeType type,
                       std::string name, uint32_t flags);

  // Attrs should override the calls they support; by default
  // these all raise exceptions.
  // Generally attrs are get/set as their native type,
  // but in cases of attr connections a 'get' corresponding
  // to the native type of the dst attr is made on the src attr
  // (so if connecting float attr foo to int attr bar,
  // the update will essentially be: bar.set(foo.GetAsInt()) )
  virtual auto GetAsFloat(Node* node) -> float;
  virtual void Set(Node* node, float value);

  virtual auto GetAsInt(Node* node) -> int64_t;
  virtual void Set(Node* node, int64_t value);

  virtual auto GetAsBool(Node* node) -> bool;
  virtual void Set(Node* node, bool value);

  virtual auto GetAsString(Node* node) -> std::string;
  virtual void Set(Node* node, const std::string& value);

  virtual auto GetAsFloats(Node* node) -> std::vector<float>;
  virtual void Set(Node* node, const std::vector<float>& value);

  virtual auto GetAsInts(Node* node) -> std::vector<int64_t>;
  virtual void Set(Node* node, const std::vector<int64_t>& value);

  virtual auto GetAsNode(Node* node) -> Node*;
  virtual void Set(Node* node, Node* value);

  virtual auto GetAsNodes(Node* node) -> std::vector<Node*>;
  virtual void Set(Node* node, const std::vector<Node*>& values);

  virtual auto GetAsPlayer(Node* node) -> Player*;
  virtual void Set(Node* node, Player* value);

  virtual auto GetAsMaterials(Node* node) -> std::vector<Material*>;
  virtual void Set(Node* node, const std::vector<Material*>& value);

  virtual auto GetAsTexture(Node* node) -> Texture*;
  virtual void Set(Node* node, Texture* value);

  virtual auto GetAsTextures(Node* node) -> std::vector<Texture*>;
  virtual void Set(Node* node, const std::vector<Texture*>& values);

  virtual auto GetAsSound(Node* node) -> Sound*;
  virtual void Set(Node* node, Sound* value);

  virtual auto GetAsSounds(Node* node) -> std::vector<Sound*>;
  virtual void Set(Node* node, const std::vector<Sound*>& values);

  virtual auto GetAsModel(Node* node) -> Model*;
  virtual void Set(Node* node, Model* value);

  virtual auto GetAsModels(Node* node) -> std::vector<Model*>;
  virtual void Set(Node* node, const std::vector<Model*>& values);

  virtual auto GetAsCollideModel(Node* node) -> CollideModel*;
  virtual void Set(Node* node, CollideModel* value);

  virtual auto GetAsCollideModels(Node* node) -> std::vector<CollideModel*>;
  virtual void Set(Node* node, const std::vector<CollideModel*>& values);

  auto is_read_only() const -> bool {
    return static_cast<bool>(flags_ & kNodeAttributeFlagReadOnly);
  }
  auto type() const -> NodeAttributeType { return type_; }
  auto GetTypeName() const -> std::string {
    return GetNodeAttributeTypeName(type_);
  }
  auto name() const -> const std::string& { return name_; }
  auto node_type() const -> NodeType* { return node_type_; }
  auto index() const -> int { return index_; }
  void DisconnectIncoming(Node* node);

 protected:
  void NotReadableError(Node* node);
  void NotWritableError(Node* node);

 private:
  NodeType* node_type_;
  NodeAttributeType type_;
  std::string name_;
  uint32_t flags_;
  int index_;
};

// Simple node-attribute pair; used as a convenience measure.
// Note that this simply stores pointers; it does not check to
// ensure the node is still valid or anything like that.
class NodeAttribute {
 public:
  void assign(Node* node_in, NodeAttributeUnbound* attr_in) {
    node = node_in;
    attr = attr_in;
  }
  NodeAttribute() = default;
  NodeAttribute(Node* node_in, NodeAttributeUnbound* attr_in)
      : node(node_in), attr(attr_in) {}
  Node* node = nullptr;
  NodeAttributeUnbound* attr = nullptr;
  auto type() const -> NodeAttributeType { return attr->type(); }
  auto GetTypeName() const -> std::string { return attr->GetTypeName(); }
  auto name() const -> const std::string& { return attr->name(); }
  auto node_type() const -> NodeType* { return attr->node_type(); }
  auto index() const -> int { return attr->index(); }
  void DisconnectIncoming() { attr->DisconnectIncoming(node); }
  auto is_read_only() const -> bool { return attr->is_read_only(); }
  auto GetAsFloat() const -> float { return attr->GetAsFloat(node); }
  void Set(float value) const { attr->Set(node, value); }
  auto GetAsInt() const -> int64_t { return attr->GetAsInt(node); }
  void Set(int64_t value) const { attr->Set(node, value); }
  auto GetAsBool() const -> bool { return attr->GetAsBool(node); }
  void Set(bool value) const { attr->Set(node, value); }
  auto GetAsString() const -> std::string { return attr->GetAsString(node); }
  void Set(const std::string& value) const { attr->Set(node, value); }
  auto GetAsFloats() const -> std::vector<float> {
    return attr->GetAsFloats(node);
  }
  void Set(const std::vector<float>& value) const { attr->Set(node, value); }
  auto GetAsInts() const -> std::vector<int64_t> {
    return attr->GetAsInts(node);
  }
  void Set(const std::vector<int64_t>& value) const { attr->Set(node, value); }
  auto GetAsNode() const -> Node* { return attr->GetAsNode(node); }
  void Set(Node* value) const { attr->Set(node, value); }
  auto GetAsNodes() const -> std::vector<Node*> {
    return attr->GetAsNodes(node);
  }
  void Set(const std::vector<Node*>& value) const { attr->Set(node, value); }
  auto GetAsPlayer() const -> Player* { return attr->GetAsPlayer(node); }
  void Set(Player* value) const { attr->Set(node, value); }
  auto GetAsMaterials() const -> std::vector<Material*> {
    return attr->GetAsMaterials(node);
  }
  void Set(const std::vector<Material*>& value) const {
    attr->Set(node, value);
  }
  auto GetAsTexture() const -> Texture* { return attr->GetAsTexture(node); }
  void Set(Texture* value) const { attr->Set(node, value); }
  auto GetAsTextures() const -> std::vector<Texture*> {
    return attr->GetAsTextures(node);
  }
  void Set(const std::vector<Texture*>& values) const {
    attr->Set(node, values);
  }
  auto GetAsSound() const -> Sound* { return attr->GetAsSound(node); }
  void Set(Sound* value) const { attr->Set(node, value); }
  auto GetAsSounds() const -> std::vector<Sound*> {
    return attr->GetAsSounds(node);
  }
  void Set(const std::vector<Sound*>& values) const { attr->Set(node, values); }
  auto GetAsModel() const -> Model* { return attr->GetAsModel(node); }
  void Set(Model* value) const { attr->Set(node, value); }
  auto GetAsModels() const -> std::vector<Model*> {
    return attr->GetAsModels(node);
  }
  void Set(const std::vector<Model*>& values) const { attr->Set(node, values); }
  auto GetAsCollideModel() const -> CollideModel* {
    return attr->GetAsCollideModel(node);
  }
  void Set(CollideModel* value) const { attr->Set(node, value); }
  auto GetAsCollideModels() const -> std::vector<CollideModel*> {
    return attr->GetAsCollideModels(node);
  }
  void Set(const std::vector<CollideModel*>& values) const {
    attr->Set(node, values);
  }
};

// Single float attr; subclasses just need to override float get/set
// and this will provide the other numeric get/sets based on that.
class NodeAttributeUnboundFloat : public NodeAttributeUnbound {
 public:
  NodeAttributeUnboundFloat(NodeType* node_type, const std::string& name,
                            uint32_t flags)
      : NodeAttributeUnbound(node_type, NodeAttributeType::kFloat, name,
                             flags) {}

  // Override these:
  auto GetAsFloat(Node* node) -> float override {
    NotReadableError(node);
    return 0.0f;
  }
  void Set(Node* node, float val) override { NotWritableError(node); }

  // These are handled automatically:
  auto GetAsInt(Node* node) -> int64_t final {
    return static_cast<int64_t>(GetAsFloat(node));
  }
  auto GetAsBool(Node* node) -> bool final {
    return static_cast<bool>(GetAsFloat(node));
  }
  void Set(Node* node, int64_t val) final {
    Set(node, static_cast<float>(val));
  }
  void Set(Node* node, bool val) final { Set(node, static_cast<float>(val)); }
};

// Float array attr.
class NodeAttributeUnboundFloatArray : public NodeAttributeUnbound {
 public:
  NodeAttributeUnboundFloatArray(NodeType* node_type, const std::string& name,
                                 uint32_t flags)
      : NodeAttributeUnbound(node_type, NodeAttributeType::kFloatArray, name,
                             flags) {}

  // Override these:
  auto GetAsFloats(Node* node) -> std::vector<float> override {
    NotReadableError(node);
    return std::vector<float>();
  }
  void Set(Node* node, const std::vector<float>& vals) override {
    NotWritableError(node);
  }
};

// Single int attr; subclasses just need to override int get/set
// and this will provide the other numeric get/sets based on that.
class NodeAttributeUnboundInt : public NodeAttributeUnbound {
 public:
  NodeAttributeUnboundInt(NodeType* node_type, const std::string& name,
                          uint32_t flags)
      : NodeAttributeUnbound(node_type, NodeAttributeType::kInt, name, flags) {}

  // Override these:
  auto GetAsInt(Node* node) -> int64_t override {
    NotReadableError(node);
    return 0;
  }
  void Set(Node* node, int64_t val) override { NotWritableError(node); }

  // These are handled automatically:
  auto GetAsFloat(Node* node) -> float final { return GetAsInt(node); }
  auto GetAsBool(Node* node) -> bool final {
    return static_cast<bool>(GetAsInt(node));
  }
  void Set(Node* node, float val) final {
    Set(node, static_cast<int64_t>(val));
  }
  void Set(Node* node, bool val) final { Set(node, static_cast<int64_t>(val)); }
};

// Int array attr.
class NodeAttributeUnboundIntArray : public NodeAttributeUnbound {
 public:
  NodeAttributeUnboundIntArray(NodeType* node_type, const std::string& name,
                               uint32_t flags)
      : NodeAttributeUnbound(node_type, NodeAttributeType::kIntArray, name,
                             flags) {}

  // Override these:
  auto GetAsInts(Node* node) -> std::vector<int64_t> override {
    NotReadableError(node);
    return std::vector<int64_t>();
  }
  void Set(Node* node, const std::vector<int64_t>& vals) override = 0;
};

// Single bool attr; subclasses just need to override bool get/set
// and this will provide the other numeric get/sets based on that.
class NodeAttributeUnboundBool : public NodeAttributeUnbound {
 public:
  NodeAttributeUnboundBool(NodeType* node_type, const std::string& name,
                           uint32_t flags)
      : NodeAttributeUnbound(node_type, NodeAttributeType::kBool, name, flags) {
  }

  // Override these:
  auto GetAsBool(Node* node) -> bool override {
    NotReadableError(node);
    return false;
  };
  void Set(Node* node, bool val) override { NotWritableError(node); }

  // These are handled automatically:
  auto GetAsFloat(Node* node) -> float final {
    return GetAsBool(node) ? 1.0f : 0.0f;
  }
  auto GetAsInt(Node* node) -> int64_t final { return GetAsBool(node) ? 1 : 0; }
  void Set(Node* node, float val) final { Set(node, val != 0.0f); }
  void Set(Node* node, int64_t val) final { Set(node, val != 0); }
};

// String attr.
class NodeAttributeUnboundString : public NodeAttributeUnbound {
 public:
  NodeAttributeUnboundString(NodeType* node_type, const std::string& name,
                             uint32_t flags)
      : NodeAttributeUnbound(node_type, NodeAttributeType::kString, name,
                             flags) {}

  // Override these:
  auto GetAsString(Node* node) -> std::string override {
    NotReadableError(node);
    return "";
  };
  void Set(Node* node, const std::string& val) override {
    NotWritableError(node);
  }
};

// Node attr.
class NodeAttributeUnboundNode : public NodeAttributeUnbound {
 public:
  NodeAttributeUnboundNode(NodeType* node_type, const std::string& name,
                           uint32_t flags)
      : NodeAttributeUnbound(node_type, NodeAttributeType::kNode, name, flags) {
  }

  // Override these:
  auto GetAsNode(Node* node) -> Node* override {
    NotReadableError(node);
    return nullptr;
  };
  void Set(Node* node, Node* val) override { NotWritableError(node); }
};

// Node array attr.
class NodeAttributeUnboundNodeArray : public NodeAttributeUnbound {
 public:
  NodeAttributeUnboundNodeArray(NodeType* node_type, const std::string& name,
                                uint32_t flags)
      : NodeAttributeUnbound(node_type, NodeAttributeType::kNodeArray, name,
                             flags) {}
  // Override these:
  auto GetAsNodes(Node* node) -> std::vector<Node*> override {
    NotReadableError(node);
    return std::vector<Node*>();
  };
  void Set(Node* node, const std::vector<Node*>& vals) override {
    NotWritableError(node);
  }
};

// Player attr.
class NodeAttributeUnboundPlayer : public NodeAttributeUnbound {
 public:
  NodeAttributeUnboundPlayer(NodeType* node_type, const std::string& name,
                             uint32_t flags)
      : NodeAttributeUnbound(node_type, NodeAttributeType::kPlayer, name,
                             flags) {}
  // override these:
  auto GetAsPlayer(Node* node) -> Player* override {
    NotReadableError(node);
    return nullptr;
  }
  void Set(Node* node, Player* val) override { NotWritableError(node); }
};

// Material array attr.
class NodeAttributeUnboundMaterialArray : public NodeAttributeUnbound {
 public:
  NodeAttributeUnboundMaterialArray(NodeType* node_type,
                                    const std::string& name, uint32_t flags)
      : NodeAttributeUnbound(node_type, NodeAttributeType::kMaterialArray, name,
                             flags) {}
  // override these:
  auto GetAsMaterials(Node* node) -> std::vector<Material*> override {
    NotReadableError(node);
    return std::vector<Material*>();
  }
  void Set(Node* node, const std::vector<Material*>& materials) override {
    NotWritableError(node);
  }
};

// Texture attr.
class NodeAttributeUnboundTexture : public NodeAttributeUnbound {
 public:
  NodeAttributeUnboundTexture(NodeType* node_type, const std::string& name,
                              uint32_t flags)
      : NodeAttributeUnbound(node_type, NodeAttributeType::kTexture, name,
                             flags) {}
  // Override these:
  auto GetAsTexture(Node* node) -> Texture* override {
    NotReadableError(node);
    return nullptr;
  }
  void Set(Node* node, Texture* val) override { NotWritableError(node); }
};

// Texture array attr.
class NodeAttributeUnboundTextureArray : public NodeAttributeUnbound {
 public:
  NodeAttributeUnboundTextureArray(NodeType* node_type, const std::string& name,
                                   uint32_t flags)
      : NodeAttributeUnbound(node_type, NodeAttributeType::kTextureArray, name,
                             flags) {}
  // Override these:
  auto GetAsTextures(Node* node) -> std::vector<Texture*> override {
    NotReadableError(node);
    return std::vector<Texture*>();
  }
  void Set(Node* node, const std::vector<Texture*>& vals) override {
    NotWritableError(node);
  }
};

// Sound attr.
class NodeAttributeUnboundSound : public NodeAttributeUnbound {
 public:
  NodeAttributeUnboundSound(NodeType* node_type, const std::string& name,
                            uint32_t flags)
      : NodeAttributeUnbound(node_type, NodeAttributeType::kSound, name,
                             flags) {}
  // override these:
  auto GetAsSound(Node* node) -> Sound* override {
    NotReadableError(node);
    return nullptr;
  }
  void Set(Node* node, Sound* val) override { NotWritableError(node); }
};

// Sound array attr.
class NodeAttributeUnboundSoundArray : public NodeAttributeUnbound {
 public:
  NodeAttributeUnboundSoundArray(NodeType* node_type, const std::string& name,
                                 uint32_t flags)
      : NodeAttributeUnbound(node_type, NodeAttributeType::kSoundArray, name,
                             flags) {}
  // Override these:
  auto GetAsSounds(Node* node) -> std::vector<Sound*> override {
    NotReadableError(node);
    return std::vector<Sound*>();
  }
  void Set(Node* node, const std::vector<Sound*>& vals) override {
    NotWritableError(node);
  }
};

// Model attr.
class NodeAttributeUnboundModel : public NodeAttributeUnbound {
 public:
  NodeAttributeUnboundModel(NodeType* node_type, const std::string& name,
                            uint32_t flags)
      : NodeAttributeUnbound(node_type, NodeAttributeType::kModel, name,
                             flags) {}
  // Override these:
  auto GetAsModel(Node* node) -> Model* override {
    NotReadableError(node);
    return nullptr;
  }
  void Set(Node* node, Model* val) override { NotWritableError(node); }
};

// Model array attr.
class NodeAttributeUnboundModelArray : public NodeAttributeUnbound {
 public:
  NodeAttributeUnboundModelArray(NodeType* node_type, const std::string& name,
                                 uint32_t flags)
      : NodeAttributeUnbound(node_type, NodeAttributeType::kModelArray, name,
                             flags) {}
  // Override these:
  auto GetAsModels(Node* node) -> std::vector<Model*> override {
    NotReadableError(node);
    return std::vector<Model*>();
  }
  void Set(Node* node, const std::vector<Model*>& vals) override {
    NotWritableError(node);
  }
};

// Collide_model attr.
class NodeAttributeUnboundCollideModel : public NodeAttributeUnbound {
 public:
  NodeAttributeUnboundCollideModel(NodeType* node_type, const std::string& name,
                                   uint32_t flags)
      : NodeAttributeUnbound(node_type, NodeAttributeType::kCollideModel, name,
                             flags) {}
  // Override these:
  auto GetAsCollideModel(Node* node) -> CollideModel* override {
    NotReadableError(node);
    return nullptr;
  }
  void Set(Node* node, CollideModel* val) override { NotWritableError(node); }
};

// Collide_model array attr.
class NodeAttributeUnboundCollideModelArray : public NodeAttributeUnbound {
 public:
  NodeAttributeUnboundCollideModelArray(NodeType* node_type,
                                        const std::string& name, uint32_t flags)
      : NodeAttributeUnbound(node_type, NodeAttributeType::kCollideModelArray,
                             name, flags) {}
  // Override these:
  auto GetAsCollideModels(Node* node) -> std::vector<CollideModel*> override {
    NotReadableError(node);
    return std::vector<CollideModel*>();
  }
  void Set(Node* node, const std::vector<CollideModel*>& vals) override {
    NotWritableError(node);
  }
};

// Defines a float attr subclass that interfaces with specific getter/setter
// calls.
#define BA_FLOAT_ATTR(NAME, GETTER, SETTER)                               \
  class Attr_##NAME : public NodeAttributeUnboundFloat {                  \
   public:                                                                \
    explicit Attr_##NAME(NodeType* node_type)                             \
        : NodeAttributeUnboundFloat(node_type, #NAME, 0) {}               \
    auto GetAsFloat(Node* node) -> float override {                       \
      BA_NODE_TYPE_CLASS* tnode = static_cast<BA_NODE_TYPE_CLASS*>(node); \
      assert(dynamic_cast<BA_NODE_TYPE_CLASS*>(node) == tnode);           \
      return tnode->GETTER();                                             \
    }                                                                     \
    void Set(Node* node, float val) override {                            \
      BA_NODE_TYPE_CLASS* tnode = static_cast<BA_NODE_TYPE_CLASS*>(node); \
      assert(dynamic_cast<BA_NODE_TYPE_CLASS*>(node) == tnode);           \
      tnode->SETTER(val);                                                 \
    }                                                                     \
  };                                                                      \
  Attr_##NAME NAME;

// Defines a float attr subclass that interfaces with specific getter/setter
// calls.
#define BA_FLOAT_ATTR_READONLY(NAME, GETTER)                              \
  class Attr_##NAME : public NodeAttributeUnboundFloat {                  \
   public:                                                                \
    explicit Attr_##NAME(NodeType* node_type)                             \
        : NodeAttributeUnboundFloat(node_type, #NAME,                     \
                                    kNodeAttributeFlagReadOnly) {}        \
    auto GetAsFloat(Node* node) -> float override {                       \
      BA_NODE_TYPE_CLASS* tnode = static_cast<BA_NODE_TYPE_CLASS*>(node); \
      assert(dynamic_cast<BA_NODE_TYPE_CLASS*>(node) == tnode);           \
      return tnode->GETTER();                                             \
    }                                                                     \
  };                                                                      \
  Attr_##NAME NAME;

// Defines a float-array attr subclass that interfaces with specific
// getter/setter calls.
#define BA_FLOAT_ARRAY_ATTR(NAME, GETTER, SETTER)                         \
  class Attr_##NAME : public NodeAttributeUnboundFloatArray {             \
   public:                                                                \
    explicit Attr_##NAME(NodeType* node_type)                             \
        : NodeAttributeUnboundFloatArray(node_type, #NAME, 0) {}          \
    auto GetAsFloats(Node* node) -> std::vector<float> override {         \
      BA_NODE_TYPE_CLASS* tnode = static_cast<BA_NODE_TYPE_CLASS*>(node); \
      assert(dynamic_cast<BA_NODE_TYPE_CLASS*>(node) == tnode);           \
      return tnode->GETTER();                                             \
    }                                                                     \
    void Set(Node* node, const std::vector<float>& vals) override {       \
      BA_NODE_TYPE_CLASS* tnode = static_cast<BA_NODE_TYPE_CLASS*>(node); \
      assert(dynamic_cast<BA_NODE_TYPE_CLASS*>(node) == tnode);           \
      tnode->SETTER(vals);                                                \
    }                                                                     \
  };                                                                      \
  Attr_##NAME NAME;

// Defines a float-array attr subclass that interfaces with specific
// getter/setter calls.
#define BA_FLOAT_ARRAY_ATTR_READONLY(NAME, GETTER)                        \
  class Attr_##NAME : public NodeAttributeUnboundFloatArray {             \
   public:                                                                \
    explicit Attr_##NAME(NodeType* node_type)                             \
        : NodeAttributeUnboundFloatArray(node_type, #NAME,                \
                                         kNodeAttributeFlagReadOnly) {}   \
    auto GetAsFloats(Node* node) -> std::vector<float> override {         \
      BA_NODE_TYPE_CLASS* tnode = static_cast<BA_NODE_TYPE_CLASS*>(node); \
      assert(dynamic_cast<BA_NODE_TYPE_CLASS*>(node) == tnode);           \
      return tnode->GETTER();                                             \
    }                                                                     \
  };                                                                      \
  Attr_##NAME NAME;

// Defines an int attr subclass that interfaces with specific getter/setter
// calls.
#define BA_INT_ATTR(NAME, GETTER, SETTER)                                 \
  class Attr_##NAME : public NodeAttributeUnboundInt {                    \
   public:                                                                \
    explicit Attr_##NAME(NodeType* node_type)                             \
        : NodeAttributeUnboundInt(node_type, #NAME, 0) {}                 \
    auto GetAsInt(Node* node) -> int64_t override {                       \
      BA_NODE_TYPE_CLASS* tnode = static_cast<BA_NODE_TYPE_CLASS*>(node); \
      assert(dynamic_cast<BA_NODE_TYPE_CLASS*>(node) == tnode);           \
      return tnode->GETTER();                                             \
    }                                                                     \
    void Set(Node* node, int64_t val) override {                          \
      BA_NODE_TYPE_CLASS* tnode = static_cast<BA_NODE_TYPE_CLASS*>(node); \
      assert(dynamic_cast<BA_NODE_TYPE_CLASS*>(node) == tnode);           \
      tnode->SETTER(static_cast_check_fit<int>(val));                     \
    }                                                                     \
  };                                                                      \
  Attr_##NAME NAME;

// Defines an int attr subclass that interfaces with specific getter/setter
// calls.
#define BA_INT_ATTR_READONLY(NAME, GETTER)                                \
  class Attr_##NAME : public NodeAttributeUnboundInt {                    \
   public:                                                                \
    explicit Attr_##NAME(NodeType* node_type)                             \
        : NodeAttributeUnboundInt(node_type, #NAME,                       \
                                  kNodeAttributeFlagReadOnly) {}          \
    auto GetAsInt(Node* node) -> int64_t override {                       \
      BA_NODE_TYPE_CLASS* tnode = static_cast<BA_NODE_TYPE_CLASS*>(node); \
      assert(dynamic_cast<BA_NODE_TYPE_CLASS*>(node) == tnode);           \
      return tnode->GETTER();                                             \
    }                                                                     \
  };                                                                      \
  Attr_##NAME NAME;

// Defines an int attr subclass that interfaces with specific getter/setter
// calls.
#define BA_INT64_ATTR(NAME, GETTER, SETTER)                               \
  class Attr_##NAME : public NodeAttributeUnboundInt {                    \
   public:                                                                \
    explicit Attr_##NAME(NodeType* node_type)                             \
        : NodeAttributeUnboundInt(node_type, #NAME, 0) {}                 \
    auto GetAsInt(Node* node) -> int64_t override {                       \
      BA_NODE_TYPE_CLASS* tnode = static_cast<BA_NODE_TYPE_CLASS*>(node); \
      assert(dynamic_cast<BA_NODE_TYPE_CLASS*>(node) == tnode);           \
      return tnode->GETTER();                                             \
    }                                                                     \
    void Set(Node* node, int64_t val) override {                          \
      BA_NODE_TYPE_CLASS* tnode = static_cast<BA_NODE_TYPE_CLASS*>(node); \
      assert(dynamic_cast<BA_NODE_TYPE_CLASS*>(node) == tnode);           \
      tnode->SETTER(val);                                                 \
    }                                                                     \
  };                                                                      \
  Attr_##NAME NAME;

// Defines an int attr subclass that interfaces with specific getter/setter
// calls.
#define BA_INT64_ATTR_READONLY(NAME, GETTER)                              \
  class Attr_##NAME : public NodeAttributeUnboundInt {                    \
   public:                                                                \
    explicit Attr_##NAME(NodeType* node_type)                             \
        : NodeAttributeUnboundInt(node_type, #NAME,                       \
                                  kNodeAttributeFlagReadOnly) {}          \
    auto GetAsInt(Node* node) -> int64_t override {                       \
      BA_NODE_TYPE_CLASS* tnode = static_cast<BA_NODE_TYPE_CLASS*>(node); \
      assert(dynamic_cast<BA_NODE_TYPE_CLASS*>(node) == tnode);           \
      return tnode->GETTER();                                             \
    }                                                                     \
  };                                                                      \
  Attr_##NAME NAME;

// Defines an int-array attr subclass that interfaces with specific
// getter/setter calls.
#define BA_INT64_ARRAY_ATTR(NAME, GETTER, SETTER)                         \
  class Attr_##NAME : public NodeAttributeUnboundIntArray {               \
   public:                                                                \
    explicit Attr_##NAME(NodeType* node_type)                             \
        : NodeAttributeUnboundIntArray(node_type, #NAME, 0) {}            \
    auto GetAsInts(Node* node) -> std::vector<int64_t> override {         \
      BA_NODE_TYPE_CLASS* tnode = static_cast<BA_NODE_TYPE_CLASS*>(node); \
      assert(dynamic_cast<BA_NODE_TYPE_CLASS*>(node) == tnode);           \
      return tnode->GETTER();                                             \
    }                                                                     \
    void Set(Node* node, const std::vector<int64_t>& vals) override {     \
      BA_NODE_TYPE_CLASS* tnode = static_cast<BA_NODE_TYPE_CLASS*>(node); \
      assert(dynamic_cast<BA_NODE_TYPE_CLASS*>(node) == tnode);           \
      tnode->SETTER(vals);                                                \
    }                                                                     \
  };                                                                      \
  Attr_##NAME NAME;

// Defines a bool attr subclass that interfaces with specific getter/setter
// calls.
#define BA_BOOL_ATTR(NAME, GETTER, SETTER)                                \
  class Attr_##NAME : public NodeAttributeUnboundBool {                   \
   public:                                                                \
    explicit Attr_##NAME(NodeType* node_type)                             \
        : NodeAttributeUnboundBool(node_type, #NAME, 0) {}                \
    auto GetAsBool(Node* node) -> bool override {                         \
      BA_NODE_TYPE_CLASS* tnode = static_cast<BA_NODE_TYPE_CLASS*>(node); \
      assert(dynamic_cast<BA_NODE_TYPE_CLASS*>(node) == tnode);           \
      return tnode->GETTER();                                             \
    }                                                                     \
    void Set(Node* node, bool val) override {                             \
      BA_NODE_TYPE_CLASS* tnode = static_cast<BA_NODE_TYPE_CLASS*>(node); \
      assert(dynamic_cast<BA_NODE_TYPE_CLASS*>(node) == tnode);           \
      tnode->SETTER(val);                                                 \
    }                                                                     \
  };                                                                      \
  Attr_##NAME NAME;

// Defines a bool attr subclass that interfaces with specific getter/setter
// calls.
#define BA_BOOL_ATTR_READONLY(NAME, GETTER)                               \
  class Attr_##NAME : public NodeAttributeUnboundBool {                   \
   public:                                                                \
    explicit Attr_##NAME(NodeType* node_type)                             \
        : NodeAttributeUnboundBool(node_type, #NAME,                      \
                                   kNodeAttributeFlagReadOnly) {}         \
    auto GetAsBool(Node* node) -> bool override {                         \
      BA_NODE_TYPE_CLASS* tnode = static_cast<BA_NODE_TYPE_CLASS*>(node); \
      assert(dynamic_cast<BA_NODE_TYPE_CLASS*>(node) == tnode);           \
      return tnode->GETTER();                                             \
    }                                                                     \
  };                                                                      \
  Attr_##NAME NAME;

// Defines a string attr subclass that interfaces with specific getter/setter
// calls.
#define BA_STRING_ATTR(NAME, GETTER, SETTER)                              \
  class Attr_##NAME : public NodeAttributeUnboundString {                 \
   public:                                                                \
    explicit Attr_##NAME(NodeType* node_type)                             \
        : NodeAttributeUnboundString(node_type, #NAME, 0) {}              \
    auto GetAsString(Node* node) -> std::string override {                \
      BA_NODE_TYPE_CLASS* tnode = static_cast<BA_NODE_TYPE_CLASS*>(node); \
      assert(dynamic_cast<BA_NODE_TYPE_CLASS*>(node) == tnode);           \
      return tnode->GETTER();                                             \
    }                                                                     \
    void Set(Node* node, const std::string& val) override {               \
      BA_NODE_TYPE_CLASS* tnode = static_cast<BA_NODE_TYPE_CLASS*>(node); \
      assert(dynamic_cast<BA_NODE_TYPE_CLASS*>(node) == tnode);           \
      tnode->SETTER(val);                                                 \
    }                                                                     \
  };                                                                      \
  Attr_##NAME NAME;

// Defines a string attr subclass that interfaces with specific getter/setter
// calls.
#define BA_STRING_ATTR_READONLY(NAME, GETTER)                             \
  class Attr_##NAME : public NodeAttributeUnboundString {                 \
   public:                                                                \
    explicit Attr_##NAME(NodeType* node_type)                             \
        : NodeAttributeUnboundString(node_type, #NAME,                    \
                                     kNodeAttributeFlagReadOnly) {}       \
    auto GetAsString(Node* node) -> std::string override {                \
      BA_NODE_TYPE_CLASS* tnode = static_cast<BA_NODE_TYPE_CLASS*>(node); \
      assert(dynamic_cast<BA_NODE_TYPE_CLASS*>(node) == tnode);           \
      return tnode->GETTER();                                             \
    }                                                                     \
  };                                                                      \
  Attr_##NAME NAME;

// Defines a node attr subclass that interfaces with specific getter/setter
// calls.
#define BA_NODE_ATTR(NAME, GETTER, SETTER)                                \
  class Attr_##NAME : public NodeAttributeUnboundNode {                   \
   public:                                                                \
    explicit Attr_##NAME(NodeType* node_type)                             \
        : NodeAttributeUnboundNode(node_type, #NAME, 0) {}                \
    auto GetAsNode(Node* node) -> Node* override {                        \
      BA_NODE_TYPE_CLASS* tnode = static_cast<BA_NODE_TYPE_CLASS*>(node); \
      assert(dynamic_cast<BA_NODE_TYPE_CLASS*>(node) == tnode);           \
      return tnode->GETTER();                                             \
    }                                                                     \
    void Set(Node* node, Node* val) override {                            \
      BA_NODE_TYPE_CLASS* tnode = static_cast<BA_NODE_TYPE_CLASS*>(node); \
      assert(dynamic_cast<BA_NODE_TYPE_CLASS*>(node) == tnode);           \
      tnode->SETTER(val);                                                 \
    }                                                                     \
  };                                                                      \
  Attr_##NAME NAME;

// Defines a node-array attr subclass that interfaces with specific
// getter/setter calls.
#define BA_NODE_ARRAY_ATTR(NAME, GETTER, SETTER)                          \
  class Attr_##NAME : public NodeAttributeUnboundNodeArray {              \
   public:                                                                \
    explicit Attr_##NAME(NodeType* node_type)                             \
        : NodeAttributeUnboundNodeArray(node_type, #NAME, 0) {}           \
    auto GetAsNodes(Node* node) -> std::vector<Node*> override {          \
      BA_NODE_TYPE_CLASS* tnode = static_cast<BA_NODE_TYPE_CLASS*>(node); \
      assert(dynamic_cast<BA_NODE_TYPE_CLASS*>(node) == tnode);           \
      return tnode->GETTER();                                             \
    }                                                                     \
    void Set(Node* node, const std::vector<Node*>& val) override {        \
      BA_NODE_TYPE_CLASS* tnode = static_cast<BA_NODE_TYPE_CLASS*>(node); \
      assert(dynamic_cast<BA_NODE_TYPE_CLASS*>(node) == tnode);           \
      tnode->SETTER(val);                                                 \
    }                                                                     \
  };                                                                      \
  Attr_##NAME NAME;

// Defines a player attr subclass that interfaces with specific getter/setter
// calls.
#define BA_PLAYER_ATTR(NAME, GETTER, SETTER)                              \
  class Attr_##NAME : public NodeAttributeUnboundPlayer {                 \
   public:                                                                \
    explicit Attr_##NAME(NodeType* node_type)                             \
        : NodeAttributeUnboundPlayer(node_type, #NAME, 0) {}              \
    auto GetAsPlayer(Node* node) -> Player* override {                    \
      BA_NODE_TYPE_CLASS* tnode = static_cast<BA_NODE_TYPE_CLASS*>(node); \
      assert(dynamic_cast<BA_NODE_TYPE_CLASS*>(node) == tnode);           \
      return tnode->GETTER();                                             \
    }                                                                     \
    void Set(Node* node, Player* val) override {                          \
      BA_NODE_TYPE_CLASS* tnode = static_cast<BA_NODE_TYPE_CLASS*>(node); \
      assert(dynamic_cast<BA_NODE_TYPE_CLASS*>(node) == tnode);           \
      tnode->SETTER(val);                                                 \
    }                                                                     \
  };                                                                      \
  Attr_##NAME NAME;

// Defines a material-array attr subclass that interfaces with specific
// getter/setter calls.
#define BA_MATERIAL_ARRAY_ATTR(NAME, GETTER, SETTER)                      \
  class Attr_##NAME : public NodeAttributeUnboundMaterialArray {          \
   public:                                                                \
    explicit Attr_##NAME(NodeType* node_type)                             \
        : NodeAttributeUnboundMaterialArray(node_type, #NAME, 0) {}       \
    auto GetAsMaterials(Node* node) -> std::vector<Material*> override {  \
      BA_NODE_TYPE_CLASS* tnode = static_cast<BA_NODE_TYPE_CLASS*>(node); \
      assert(dynamic_cast<BA_NODE_TYPE_CLASS*>(node) == tnode);           \
      return tnode->GETTER();                                             \
    }                                                                     \
    void Set(Node* node, const std::vector<Material*>& val) override {    \
      BA_NODE_TYPE_CLASS* tnode = static_cast<BA_NODE_TYPE_CLASS*>(node); \
      assert(dynamic_cast<BA_NODE_TYPE_CLASS*>(node) == tnode);           \
      tnode->SETTER(val);                                                 \
    }                                                                     \
  };                                                                      \
  Attr_##NAME NAME;

// Defines a texture attr subclass that interfaces with specific getter/setter
// calls.
#define BA_TEXTURE_ATTR(NAME, GETTER, SETTER)                             \
  class Attr_##NAME : public NodeAttributeUnboundTexture {                \
   public:                                                                \
    explicit Attr_##NAME(NodeType* node_type)                             \
        : NodeAttributeUnboundTexture(node_type, #NAME, 0) {}             \
    auto GetAsTexture(Node* node) -> Texture* override {                  \
      BA_NODE_TYPE_CLASS* tnode = static_cast<BA_NODE_TYPE_CLASS*>(node); \
      assert(dynamic_cast<BA_NODE_TYPE_CLASS*>(node) == tnode);           \
      return tnode->GETTER();                                             \
    }                                                                     \
    void Set(Node* node, Texture* val) override {                         \
      BA_NODE_TYPE_CLASS* tnode = static_cast<BA_NODE_TYPE_CLASS*>(node); \
      assert(dynamic_cast<BA_NODE_TYPE_CLASS*>(node) == tnode);           \
      tnode->SETTER(val);                                                 \
    }                                                                     \
  };                                                                      \
  Attr_##NAME NAME;

// Defines a texture attr subclass that interfaces with specific getter/setter
// calls.
#define BA_TEXTURE_ATTR_READONLY(NAME, GETTER)                            \
  class Attr_##NAME : public NodeAttributeUnboundTexture {                \
   public:                                                                \
    explicit Attr_##NAME(NodeType* node_type)                             \
        : NodeAttributeUnboundTexture(node_type, #NAME,                   \
                                      kNodeAttributeFlagReadOnly) {}      \
    auto GetAsTexture(Node* node) -> Texture* override {                  \
      BA_NODE_TYPE_CLASS* tnode = static_cast<BA_NODE_TYPE_CLASS*>(node); \
      assert(dynamic_cast<BA_NODE_TYPE_CLASS*>(node) == tnode);           \
      return tnode->GETTER();                                             \
    }                                                                     \
  };                                                                      \
  Attr_##NAME NAME;

// Defines a texture attr subclass that interfaces with specific getter/setter
// calls.
#define BA_TEXTURE_ARRAY_ATTR(NAME, GETTER, SETTER)                       \
  class Attr_##NAME : public NodeAttributeUnboundTextureArray {           \
   public:                                                                \
    explicit Attr_##NAME(NodeType* node_type)                             \
        : NodeAttributeUnboundTextureArray(node_type, #NAME, 0) {}        \
    auto GetAsTextures(Node* node) -> std::vector<Texture*> override {    \
      BA_NODE_TYPE_CLASS* tnode = static_cast<BA_NODE_TYPE_CLASS*>(node); \
      assert(dynamic_cast<BA_NODE_TYPE_CLASS*>(node) == tnode);           \
      return tnode->GETTER();                                             \
    }                                                                     \
    void Set(Node* node, const std::vector<Texture*>& vals) override {    \
      BA_NODE_TYPE_CLASS* tnode = static_cast<BA_NODE_TYPE_CLASS*>(node); \
      assert(dynamic_cast<BA_NODE_TYPE_CLASS*>(node) == tnode);           \
      tnode->SETTER(vals);                                                \
    }                                                                     \
  };                                                                      \
  Attr_##NAME NAME;

// Defines a sound attr subclass that interfaces with specific getter/setter
// calls.
#define BA_SOUND_ATTR(NAME, GETTER, SETTER)                               \
  class Attr_##NAME : public NodeAttributeUnboundSound {                  \
   public:                                                                \
    explicit Attr_##NAME(NodeType* node_type)                             \
        : NodeAttributeUnboundSound(node_type, #NAME, 0) {}               \
    auto GetAsSound(Node* node) -> Sound* override {                      \
      BA_NODE_TYPE_CLASS* tnode = static_cast<BA_NODE_TYPE_CLASS*>(node); \
      assert(dynamic_cast<BA_NODE_TYPE_CLASS*>(node) == tnode);           \
      return tnode->GETTER();                                             \
    }                                                                     \
    void Set(Node* node, Sound* val) override {                           \
      BA_NODE_TYPE_CLASS* tnode = static_cast<BA_NODE_TYPE_CLASS*>(node); \
      assert(dynamic_cast<BA_NODE_TYPE_CLASS*>(node) == tnode);           \
      tnode->SETTER(val);                                                 \
    }                                                                     \
  };                                                                      \
  Attr_##NAME NAME;

// Defines a sound attr subclass that interfaces with specific getter/setter
// calls.
#define BA_SOUND_ARRAY_ATTR(NAME, GETTER, SETTER)                         \
  class Attr_##NAME : public NodeAttributeUnboundSoundArray {             \
   public:                                                                \
    explicit Attr_##NAME(NodeType* node_type)                             \
        : NodeAttributeUnboundSoundArray(node_type, #NAME, 0) {}          \
    auto GetAsSounds(Node* node) -> std::vector<Sound*> override {        \
      BA_NODE_TYPE_CLASS* tnode = static_cast<BA_NODE_TYPE_CLASS*>(node); \
      assert(dynamic_cast<BA_NODE_TYPE_CLASS*>(node) == tnode);           \
      return tnode->GETTER();                                             \
    }                                                                     \
    void Set(Node* node, const std::vector<Sound*>& vals) override {      \
      BA_NODE_TYPE_CLASS* tnode = static_cast<BA_NODE_TYPE_CLASS*>(node); \
      assert(dynamic_cast<BA_NODE_TYPE_CLASS*>(node) == tnode);           \
      tnode->SETTER(vals);                                                \
    }                                                                     \
  };                                                                      \
  Attr_##NAME NAME;

// Defines a model attr subclass that interfaces with specific getter/setter
// calls.
#define BA_MODEL_ATTR(NAME, GETTER, SETTER)                               \
  class Attr_##NAME : public NodeAttributeUnboundModel {                  \
   public:                                                                \
    explicit Attr_##NAME(NodeType* node_type)                             \
        : NodeAttributeUnboundModel(node_type, #NAME, 0) {}               \
    auto GetAsModel(Node* node) -> Model* override {                      \
      BA_NODE_TYPE_CLASS* tnode = static_cast<BA_NODE_TYPE_CLASS*>(node); \
      assert(dynamic_cast<BA_NODE_TYPE_CLASS*>(node) == tnode);           \
      return tnode->GETTER();                                             \
    }                                                                     \
    void Set(Node* node, Model* val) override {                           \
      BA_NODE_TYPE_CLASS* tnode = static_cast<BA_NODE_TYPE_CLASS*>(node); \
      assert(dynamic_cast<BA_NODE_TYPE_CLASS*>(node) == tnode);           \
      tnode->SETTER(val);                                                 \
    }                                                                     \
  };                                                                      \
  Attr_##NAME NAME;

// Defines a model attr subclass that interfaces with specific getter/setter
// calls.
#define BA_MODEL_ARRAY_ATTR(NAME, GETTER, SETTER)                         \
  class Attr_##NAME : public NodeAttributeUnboundModelArray {             \
   public:                                                                \
    explicit Attr_##NAME(NodeType* node_type)                             \
        : NodeAttributeUnboundModelArray(node_type, #NAME, 0) {}          \
    auto GetAsModels(Node* node) -> std::vector<Model*> override {        \
      BA_NODE_TYPE_CLASS* tnode = static_cast<BA_NODE_TYPE_CLASS*>(node); \
      assert(dynamic_cast<BA_NODE_TYPE_CLASS*>(node) == tnode);           \
      return tnode->GETTER();                                             \
    }                                                                     \
    void Set(Node* node, const std::vector<Model*>& vals) override {      \
      BA_NODE_TYPE_CLASS* tnode = static_cast<BA_NODE_TYPE_CLASS*>(node); \
      assert(dynamic_cast<BA_NODE_TYPE_CLASS*>(node) == tnode);           \
      tnode->SETTER(vals);                                                \
    }                                                                     \
  };                                                                      \
  Attr_##NAME NAME;

// Defines a collide_model attr subclass that interfaces with specific
// getter/setter calls.
#define BA_COLLIDE_MODEL_ATTR(NAME, GETTER, SETTER)                       \
  class Attr_##NAME : public NodeAttributeUnboundCollideModel {           \
   public:                                                                \
    explicit Attr_##NAME(NodeType* node_type)                             \
        : NodeAttributeUnboundCollideModel(node_type, #NAME, 0) {}        \
    auto GetAsCollideModel(Node* node) -> CollideModel* override {        \
      BA_NODE_TYPE_CLASS* tnode = static_cast<BA_NODE_TYPE_CLASS*>(node); \
      assert(dynamic_cast<BA_NODE_TYPE_CLASS*>(node) == tnode);           \
      return tnode->GETTER();                                             \
    }                                                                     \
    void Set(Node* node, CollideModel* val) override {                    \
      BA_NODE_TYPE_CLASS* tnode = static_cast<BA_NODE_TYPE_CLASS*>(node); \
      assert(dynamic_cast<BA_NODE_TYPE_CLASS*>(node) == tnode);           \
      tnode->SETTER(val);                                                 \
    }                                                                     \
  };                                                                      \
  Attr_##NAME NAME;

// Defines a collide_model attr subclass that interfaces with specific
// getter/setter calls.
#define BA_COLLIDE_MODEL_ARRAY_ATTR(NAME, GETTER, SETTER)                   \
  class Attr_##NAME : public NodeAttributeUnboundCollideModelArray {        \
   public:                                                                  \
    explicit Attr_##NAME(NodeType* node_type)                               \
        : NodeAttributeUnboundCollideModelArray(node_type, #NAME, 0) {}     \
    auto GetAsCollideModels(Node* node)                                     \
        -> std::vector<CollideModel*> override {                            \
      BA_NODE_TYPE_CLASS* tnode = static_cast<BA_NODE_TYPE_CLASS*>(node);   \
      assert(dynamic_cast<BA_NODE_TYPE_CLASS*>(node) == tnode);             \
      return tnode->GETTER();                                               \
    }                                                                       \
    void Set(Node* node, const std::vector<CollideModel*>& vals) override { \
      BA_NODE_TYPE_CLASS* tnode = static_cast<BA_NODE_TYPE_CLASS*>(node);   \
      assert(dynamic_cast<BA_NODE_TYPE_CLASS*>(node) == tnode);             \
      tnode->SETTER(vals);                                                  \
    }                                                                       \
  };                                                                        \
  Attr_##NAME NAME;

#pragma clang diagnostic pop

}  // namespace ballistica

#endif  // BALLISTICA_SCENE_NODE_NODE_ATTRIBUTE_H_
