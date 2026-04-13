// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/node/node.h"

#include <string>
#include <vector>

#include "ballistica/base/python/support/python_context_call.h"
#include "ballistica/core/core.h"
#include "ballistica/scene_v1/dynamics/part.h"
#include "ballistica/scene_v1/node/node_attribute.h"
#include "ballistica/scene_v1/node/node_attribute_connection.h"
#include "ballistica/scene_v1/python/class/python_class_node.h"
#include "ballistica/scene_v1/python/scene_v1_python.h"
#include "ballistica/scene_v1/support/scene.h"
#include "ballistica/scene_v1/support/session_stream.h"
#include "ballistica/shared/python/python.h"

namespace ballistica::scene_v1 {

NodeType::~NodeType() {
  g_core->logging->Log(LogName::kBa, LogLevel::kError,
                       "SHOULD NOT BE DESTRUCTING A TYPE type=(" + name_ + ")");
}

Node::Node(Scene* scene_in, NodeType* node_type)
    : node_type_(node_type), scene_(scene_in) {}
void Node::AddToScene(Scene* scene) {
  // we should have already set our scene ptr in our constructor;
  // now we add ourself to its lists..
  // (can't create strong refs in constructors)
  assert(scene_ == scene);
  assert(id_ == 0);

  scene->AddNode(this, &id_, &iterator_);
  // id_ = scene->next_node_id_++;
  // our_iterator_ =
  //     scene->nodes_.insert(scene->nodes_.end(), Object::Ref<Node>(this));
  if (SessionStream* os = scene->GetSceneStream()) {
    os->AddNode(this);
  }
}

Node::~Node() {
  // Kill any incoming/outgoing attr connections.
  for (auto& i : attribute_connections_incoming_) {
    NodeAttributeConnection* a = i.second.get();
    assert(a && a->src_node.exists());

    // Remove from src node's outgoing list.
    a->src_node->attribute_connections_.erase(a->src_iterator);
  }

  // Kill all refs on our side; this should kill the connections.
  attribute_connections_incoming_.clear();
  for (auto& attribute_connection : attribute_connections_) {
    NodeAttributeConnection* a = attribute_connection.get();
    assert(a && a->dst_node.exists());

    // Remove from dst node's incoming list.
    auto j =
        a->dst_node->attribute_connections_incoming_.find(a->dst_attr_index);
    assert(j != a->dst_node->attribute_connections_incoming_.end());
    a->dst_node->attribute_connections_incoming_.erase(j);
  }

  // Kill all refs on our side; should kill the connections.
  attribute_connections_.clear();

  // NOTE: We no longer run death-actions or kill dependent-nodes here in our
  // destructor; we allow the scene to do that to keep things cleaner.

  // Release our ref to ourself if we have one.
  if (py_ref_) {
    Py_DECREF(py_ref_);
  }

  // If we were going to an output stream, inform them of our demise.
  assert(scene());
  if (SessionStream* output_stream = scene()->GetSceneStream()) {
    output_stream->RemoveNode(this);
  }
}

auto Node::GetResyncDataSize() -> int { return 0; }
auto Node::GetResyncData() -> std::vector<uint8_t> { return {}; }

void Node::ApplyResyncData(const std::vector<uint8_t>& data) {}

void Node::Draw(base::FrameDef* frame_def) {}
void Node::OnCreate() {}

auto Node::GetObjectDescription() const -> std::string {
  return "<ballistica::Node #" + std::to_string(id()) + " \""
         + (label().empty() ? type()->name() : label()) + "\">";
}

auto Node::HasAttribute(const std::string& name) const -> bool {
  return type()->HasAttribute(name);
}

auto Node::GetAttribute(const std::string& name) -> NodeAttribute {
  assert(type());
  return {this, type()->GetAttribute(name)};
}

auto Node::GetAttribute(int index) -> NodeAttribute {
  assert(type());
  return {this, type()->GetAttribute(index)};
}

void Node::ConnectAttribute(NodeAttributeUnbound* src_attr, Node* dst_node,
                            NodeAttributeUnbound* dst_attr) {
  // This is a no-op if the scene is shutting down.
  if (scene() == nullptr || scene()->shutting_down()) {
    return;
  }

  assert(dst_node);
  assert(src_attr && dst_attr);
  assert(src_attr->node_type() == type());
  assert(dst_node->type() == dst_attr->node_type());
  assert(!scene()->in_step());

  bool allow = false;

  // Currently limiting to certain types;
  // Will wait and see on other types.
  // A texture/etc attr might not behave well if updated with the same
  // value every step.. hmmm.
  {
    switch (src_attr->type()) {
      // Allow bools, ints, and floats to connect to each other
      case NodeAttributeType::kBool:
      case NodeAttributeType::kInt:
      case NodeAttributeType::kFloat:
        switch (dst_attr->type()) {
          case NodeAttributeType::kBool:
          case NodeAttributeType::kInt:
          case NodeAttributeType::kFloat:
            allow = true;
            break;
          default:
            break;
        }
        break;
      case NodeAttributeType::kString:
        // Allow strings to connect to other strings (new in protocol 31).
        if (dst_attr->type() == NodeAttributeType::kString) {
          allow = true;
        }
        break;
      case NodeAttributeType::kIntArray:
      case NodeAttributeType::kFloatArray:
      case NodeAttributeType::kTexture:
        // Allow these types to connect to other attrs of the same type.
        if (src_attr->type() == dst_attr->type()) allow = true;
        break;
      default:
        break;
    }
  }
  if (!allow) {
    throw Exception("Attribute connections from " + src_attr->GetTypeName()
                    + " to " + dst_attr->GetTypeName()
                    + " attrs are not allowed.");
  }

  // Ok lets do this.

  // Disconnect any existing connection to the dst attr.
  dst_attr->DisconnectIncoming(dst_node);

  auto a(Object::New<NodeAttributeConnection>());

  // Store refs to the connection with both the source and dst nodes.
  a->src_iterator =
      attribute_connections_.insert(attribute_connections_.end(), a);
  dst_node->attribute_connections_incoming_[dst_attr->index()] = a;
  a->src_node = this;
  a->src_attr_index = src_attr->index();
  a->dst_node = dst_node;
  a->dst_attr_index = dst_attr->index();
  a->Update();
}

void Node::UpdateConnections() {
  for (auto& attribute_connection : attribute_connections_) {
    // Connections should go away when either node dies; make sure that's
    // working.
    assert(attribute_connection->src_node.exists()
           && attribute_connection->dst_node.exists());
    attribute_connection->Update();
  }
}

void Node::AddNodeDeathAction(PyObject* call_obj) {
  death_actions_.push_back(Object::New<base::PythonContextCall>(call_obj));
}

void Node::AddDependentNode(Node* node) {
  assert(node);
  if (node->scene() != scene()) {
    throw Exception("Nodes belong to different Scenes");
  }

  // While we're here lets prune any dead nodes from our list.
  // (so if we add/destroy dependents repeatedly we don't build up a giant
  // vector of dead ones)
  if (!dependent_nodes_.empty()) {
    std::vector<Object::WeakRef<Node> > live_nodes;
    for (auto& dependent_node : dependent_nodes_) {
      if (dependent_node.exists()) live_nodes.push_back(dependent_node);
    }
    dependent_nodes_.swap(live_nodes);
  }
  dependent_nodes_.emplace_back(node);
}

void Node::SetDelegate(PyObject* delegate_obj) {
  if (delegate_obj != nullptr && delegate_obj != Py_None) {
    delegate_.Steal(PyWeakref_NewRef(delegate_obj, nullptr));
  } else {
    delegate_.Release();
  }
}

auto Node::GetPyRef(bool new_ref) -> PyObject* {
  assert(g_base->InLogicThread());
  if (py_ref_ == nullptr) {
    py_ref_ = PythonClassNode::Create(this);
  }
  if (new_ref) {
    Py_INCREF(py_ref_);
  }
  return py_ref_;
}

auto Node::GetDelegate() -> PyObject* {
  PyObject* delegate = delegate_.get();
  if (!delegate) {
    return nullptr;
  }
  PyObject* obj{};
  int result = PyWeakref_GetRef(delegate, &obj);

  // The object is valid (1) or has since died (0).
  if (result == 1 || result == 0) {
    return obj;
  }
  // Something went wrong and an exception is set. We don't expect this to
  // ever happen so currently just providing a simple error msg.
  assert(result == -1);
  PyErr_Clear();
  g_core->logging->Log(LogName::kBa, LogLevel::kError,
                       "Node::GetDelegate(): error getting weakref obj.");
  return nullptr;
}

void Node::DispatchNodeMessage(const char* buffer) {
  assert(this);
  assert(buffer);
  if (scene_->shutting_down()) {
    return;
  }

  // If noone else has handled it, pass it to our low-level handler.
  HandleMessage(buffer);
}

void Node::DispatchOutOfBoundsMessage() {
  PythonRef instance;
  {
    Python::ScopedCallLabel label("OutOfBoundsMessage instantiation");
    instance = g_scene_v1->python->objs()
                   .Get(SceneV1Python::ObjID::kOutOfBoundsMessageClass)
                   .Call();
  }
  if (instance.exists()) {
    DispatchUserMessage(instance.get(), "Node OutOfBoundsMessage dispatch");
  } else {
    g_core->logging->Log(LogName::kBa, LogLevel::kError,
                         "Error creating OutOfBoundsMessage");
  }
}

void Node::DispatchPickUpMessage(Node* node) {
  assert(node);
  PythonRef args(Py_BuildValue("(O)", node->BorrowPyRef()), PythonRef::kSteal);
  PythonRef instance;
  {
    Python::ScopedCallLabel label("PickUpMessage instantiation");
    instance = g_scene_v1->python->objs()
                   .Get(SceneV1Python::ObjID::kPickUpMessageClass)
                   .Call(args);
  }
  if (instance.exists()) {
    DispatchUserMessage(instance.get(), "Node PickUpMessage dispatch");
  } else {
    g_core->logging->Log(LogName::kBa, LogLevel::kError,
                         "Error creating PickUpMessage");
  }
}

void Node::DispatchDropMessage() {
  PythonRef instance;
  {
    Python::ScopedCallLabel label("DropMessage instantiation");
    instance = g_scene_v1->python->objs()
                   .Get(SceneV1Python::ObjID::kDropMessageClass)
                   .Call();
  }
  if (instance.exists()) {
    DispatchUserMessage(instance.get(), "Node DropMessage dispatch");
  } else {
    g_core->logging->Log(LogName::kBa, LogLevel::kError,
                         "Error creating DropMessage");
  }
}

void Node::DispatchPickedUpMessage(Node* by_node) {
  assert(by_node);
  PythonRef args(Py_BuildValue("(O)", by_node->BorrowPyRef()),
                 PythonRef::kSteal);
  PythonRef instance;
  {
    Python::ScopedCallLabel label("PickedUpMessage instantiation");
    instance = g_scene_v1->python->objs()
                   .Get(SceneV1Python::ObjID::kPickedUpMessageClass)
                   .Call(args);
  }
  if (instance.exists()) {
    DispatchUserMessage(instance.get(), "Node PickedUpMessage dispatch");
  } else {
    g_core->logging->Log(LogName::kBa, LogLevel::kError,
                         "Error creating PickedUpMessage");
  }
}

void Node::DispatchDroppedMessage(Node* by_node) {
  assert(by_node);
  PythonRef args(Py_BuildValue("(O)", by_node->BorrowPyRef()),
                 PythonRef::kSteal);
  PythonRef instance;
  {
    Python::ScopedCallLabel label("DroppedMessage instantiation");
    instance = g_scene_v1->python->objs()
                   .Get(SceneV1Python::ObjID::kDroppedMessageClass)
                   .Call(args);
  }
  if (instance.exists()) {
    DispatchUserMessage(instance.get(), "Node DroppedMessage dispatch");
  } else {
    g_core->logging->Log(LogName::kBa, LogLevel::kError,
                         "Error creating DroppedMessage");
  }
}

void Node::DispatchShouldShatterMessage() {
  PythonRef instance;
  {
    Python::ScopedCallLabel label("ShouldShatterMessage instantiation");
    instance = g_scene_v1->python->objs()
                   .Get(SceneV1Python::ObjID::kShouldShatterMessageClass)
                   .Call();
  }
  if (instance.exists()) {
    DispatchUserMessage(instance.get(), "Node ShouldShatterMessage dispatch");
  } else {
    g_core->logging->Log(LogName::kBa, LogLevel::kError,
                         "Error creating ShouldShatterMessage");
  }
}

void Node::DispatchImpactDamageMessage(float intensity) {
  PythonRef args(Py_BuildValue("(f)", intensity), PythonRef::kSteal);
  PythonRef instance;
  {
    Python::ScopedCallLabel label("ImpactDamageMessage instantiation");
    instance = g_scene_v1->python->objs()
                   .Get(SceneV1Python::ObjID::kImpactDamageMessageClass)
                   .Call(args);
  }
  if (instance.exists()) {
    DispatchUserMessage(instance.get(), "Node ImpactDamageMessage dispatch");
  } else {
    g_core->logging->Log(LogName::kBa, LogLevel::kError,
                         "Error creating ImpactDamageMessage");
  }
}

void Node::DispatchUserMessage(PyObject* obj, const char* label) {
  assert(g_base->InLogicThread());
  if (scene_->shutting_down()) {
    return;
  }

  base::ScopedSetContext ssc(context_ref());

  // GetDelegate() returns a new ref or nullptr.
  auto delegate{PythonRef::StolenSoft(GetDelegate())};
  if (delegate.exists() && delegate.get() != Py_None) {
    try {
      PyObject* handlemessage_obj =
          PyObject_GetAttrString(delegate.get(), "handlemessage");
      if (!handlemessage_obj) {
        PyErr_Clear();
        throw Exception("No 'handlemessage' found on delegate object for '"
                        + type()->name() + "' node ("
                        + Python::ObjToString(delegate.get()) + ")");
      }
      PythonRef c(handlemessage_obj, PythonRef::kSteal);
      {
        Python::ScopedCallLabel lscope(label);
        c.Call(PythonRef(Py_BuildValue("(O)", obj), PythonRef::kSteal));
      }
    } catch (const std::exception& e) {
      g_core->logging->Log(LogName::kBa, LogLevel::kError,
                           std::string("Error in handlemessage() with message ")
                               + PythonRef(obj, PythonRef::kAcquire).Str()
                               + ": '" + e.what() + "'");
    }
  }
}

void Node::HandleMessage(const char* data_in) {}

void Node::UpdatePartBirthTimes() {
  for (auto&& i : parts_) {
    i->UpdateBirthTime();
  }
}

void Node::CheckBodies() {
  for (auto&& i : parts_) {
    i->CheckBodies();
  }
}

auto NodeType::GetAttributeNames() const -> std::vector<std::string> {
  std::vector<std::string> names;
  names.reserve(attributes_by_name_.size());
  for (auto&& i : attributes_by_name_) {
    names.push_back(i.second->name());
  }
  return names;
}

void Node::ListAttributes(std::list<std::string>* attrs) {
  attrs->clear();

  // New attrs.
  std::vector<std::string> type_attrs = type()->GetAttributeNames();
  for (auto&& i : type_attrs) {
    attrs->push_back(i);
  }
}

void Node::GetRigidBodyPickupLocations(int id, float* pos_obj, float* pos_char,
                                       float* hand_offset_1,
                                       float* hand_offset_2) {
  pos_obj[0] = pos_obj[1] = pos_obj[2] = 0;
  pos_char[0] = pos_char[1] = pos_char[2] = 0;
  hand_offset_1[0] = hand_offset_1[1] = hand_offset_1[2] = 0;
  hand_offset_2[0] = hand_offset_2[1] = hand_offset_2[2] = 0;
}

}  // namespace ballistica::scene_v1
