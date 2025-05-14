// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_NODE_NODE_H_
#define BALLISTICA_SCENE_V1_NODE_NODE_H_

#include <list>
#include <string>
#include <unordered_map>
#include <vector>

#include "ballistica/base/base.h"
#include "ballistica/scene_v1/support/scene_v1_context.h"
#include "ballistica/shared/foundation/object.h"
#include "ballistica/shared/python/python_ref.h"

namespace ballistica::scene_v1 {

// Define a static creation call for this node type
#define BA_NODE_CREATE_CALL(FUNC)                       \
  static auto FUNC(Scene* sg) -> Node* {                \
    return Object::NewDeferred<BA_NODE_TYPE_CLASS>(sg); \
  }

typedef std::list<Object::Ref<Node> > NodeList;

// Base node class.
class Node : public Object {
 public:
  Node(Scene* scene, NodeType* node_type);
  ~Node() override;

  /// Return the node's id in its scene.
  auto id() const -> int64_t { return id_; }

  /// Called for each step of the sim.
  virtual void Step() {}

  /// Called when screen size changes.
  virtual void OnScreenSizeChange() {}

  /// Called when the language changes.
  virtual void OnLanguageChange() {}

  /// The node can rule out collisions between particular bodies using this.
  virtual auto PreFilterCollision(RigidBody* b1, RigidBody* r2) -> bool {
    return true;
  }

  /// Pull a node type out of a buffer.
  static auto extract_node_message_type(const char** b) -> NodeMessageType {
    auto t = static_cast<NodeMessageType>(**b);
    (*b) += 1;
    return t;
  }

  void ConnectAttribute(NodeAttributeUnbound* src_attr, Node* dst_node,
                        NodeAttributeUnbound* dst_attr);

  /// Return an attribute by name.
  auto GetAttribute(const std::string& name) -> NodeAttribute;

  /// Return an attribute by index.
  auto GetAttribute(int index) -> NodeAttribute;

  void SetDelegate(PyObject* delegate_obj);

  auto NewPyRef() -> PyObject* { return GetPyRef(true); }
  auto BorrowPyRef() -> PyObject* { return GetPyRef(false); }

  /// Return the delegate, or nullptr if it doesn't have one (or if the
  /// delegate has since died).
  // auto GetDelegateOld() -> PyObject*;

  /// Return a NEW ref to the delegate or else nullptr if it doesn't have
  /// one (or if the delegate has since died). If an error occurs, return
  /// nullptr and clear any Python exception state.
  auto GetDelegate() -> PyObject*;

  void AddNodeDeathAction(PyObject* call_obj);

  /// Add a node to auto-kill when this one dies.
  void AddDependentNode(Node* node);

  /// Update birth times for all the node's parts. This should be done when
  /// teleporting or otherwise spawning at a new location.
  void UpdatePartBirthTimes();

  /// Retrieve an existing part from a node.
  auto GetPart(unsigned int id) -> Part* {
    assert(id < parts_.size());
    return parts_[id];
  }

  /// Used by RigidBodies when adding themselves to the part.
  auto AddPart(Part* part_in) -> int {
    parts_.push_back(part_in);
    return static_cast<int>(parts_.size() - 1);
  }

  /// Used to send messages to a node
  void DispatchNodeMessage(const char* buffer);

  /// Used to send custom user messages to a node.
  void DispatchUserMessage(PyObject* obj, const char* label);
  void DispatchOutOfBoundsMessage();
  void DispatchPickedUpMessage(Node* n);
  void DispatchDroppedMessage(Node* n);
  void DispatchPickUpMessage(Node* n);
  void DispatchDropMessage();
  void DispatchShouldShatterMessage();
  void DispatchImpactDamageMessage(float intensity);

  /// Utility function to get a rigid body.
  virtual auto GetRigidBody(int id) -> RigidBody* { return nullptr; }

  /// Given a rigid body, return the relative position where it should be
  /// picked up from.
  virtual void GetRigidBodyPickupLocations(int id, float* posObj,
                                           float* pos_char,
                                           float* hand_offset_1,
                                           float* hand_offset_2);

  /// Called for each Node when it should render itself.
  virtual void Draw(base::FrameDef* frame_def);

  /// Called for each node once construction is completed this can be a good
  /// time to create things from the initial attr set, etc
  virtual void OnCreate();

  auto scene() const -> Scene* {
    assert(scene_);
    return scene_;
  }

  /// Used to re-sync client versions of a node from the host version.
  virtual auto GetResyncDataSize() -> int;
  virtual auto GetResyncData() -> std::vector<uint8_t>;
  virtual void ApplyResyncData(const std::vector<uint8_t>& data);
  auto context_ref() const -> const ContextRefSceneV1& { return context_ref_; }

  /// Node labels are purely for local debugging - they aren't unique or
  /// sent across the network or anything.
  void set_label(const std::string& label) { label_ = label; }
  auto label() const -> const std::string& { return label_; }

  void ListAttributes(std::list<std::string>* attrs);
  auto type() const -> NodeType* {
    assert(node_type_);
    return node_type_;
  }
  auto HasAttribute(const std::string& name) const -> bool;
  auto HasPyRef() -> bool { return (py_ref_ != nullptr); }
  void UpdateConnections();
  auto iterator() -> NodeList::iterator { return iterator_; }

  void CheckBodies();

#if BA_DEBUG_BUILD
#define BA_DEBUG_CHECK_BODIES() CheckBodies()
#else
#define BA_DEBUG_CHECK_BODIES() ((void)0)
#endif

  auto GetObjectDescription() const -> std::string override;

  auto parts() const -> const std::vector<Part*>& { return parts_; }

  auto death_actions() const
      -> const std::vector<Object::Ref<base::PythonContextCall> >& {
    return death_actions_;
  }

  auto dependent_nodes() const -> const std::vector<Object::WeakRef<Node> >& {
    return dependent_nodes_;
  }

  auto attribute_connections() const
      -> const std::list<Object::Ref<NodeAttributeConnection> >& {
    return attribute_connections_;
  }

  auto attribute_connections_incoming() const
      -> const std::unordered_map<int, Object::Ref<NodeAttributeConnection> >& {
    return attribute_connections_incoming_;
  }

  auto stream_id() const -> int64_t { return stream_id_; }
  void set_stream_id(int64_t val) {
    assert(stream_id_ == -1);
    stream_id_ = val;
  }

  void clear_stream_id() {
    assert(stream_id_ != -1);
    stream_id_ = -1;
  }

  /// Return a reference to a python wrapper for this node, creating one if
  /// need be.
  auto GetPyRef(bool new_ref = true) -> PyObject*;

  void AddToScene(Scene* scene);

  // Called for each message received by an Node.
  virtual void HandleMessage(const char* buffer);

 private:
  int64_t stream_id_{-1};
  NodeType* node_type_ = nullptr;

  PyObject* py_ref_ = nullptr;

  /// FIXME - We can get by with *just* a pointer to our scene if we add a
  ///  way to pull context from a scene.
  ContextRefSceneV1 context_ref_;
  Scene* scene_{};
  std::string label_;
  std::vector<Object::WeakRef<Node> > dependent_nodes_;
  std::vector<Part*> parts_;
  int64_t id_{};
  NodeList::iterator iterator_;

  // Put this stuff at the bottom so it gets killed first
  PythonRef delegate_;
  std::vector<Object::Ref<base::PythonContextCall> > death_actions_;

  /// Outgoing attr connections in order created.
  std::list<Object::Ref<NodeAttributeConnection> > attribute_connections_;

  /// Incoming attr connections by attr index.
  std::unordered_map<int, Object::Ref<NodeAttributeConnection> >
      attribute_connections_incoming_;

  friend class NodeAttributeUnbound;
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_NODE_NODE_H_
