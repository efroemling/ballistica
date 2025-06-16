// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/python/class/python_class_node.h"

#include <list>
#include <string>
#include <vector>

#include "ballistica/base/logic/logic.h"
#include "ballistica/scene_v1/python/scene_v1_python.h"
#include "ballistica/scene_v1/support/scene.h"
#include "ballistica/scene_v1/support/session_stream.h"
#include "ballistica/shared/foundation/event_loop.h"
#include "ballistica/shared/python/python.h"

namespace ballistica::scene_v1 {

// Ignore a few things that python macros do.
#pragma clang diagnostic push
#pragma ide diagnostic ignored "hicpp-signed-bitwise"
#pragma ide diagnostic ignored "RedundantCast"

PyNumberMethods PythonClassNode::as_number_;

auto PythonClassNode::type_name() -> const char* { return "Node"; }

void PythonClassNode::SetupType(PyTypeObject* cls) {
  PythonClass::SetupType(cls);
  cls->tp_repr = (reprfunc)tp_repr;
  // Fully qualified type path we will be exposed as:
  cls->tp_name = "bascenev1.Node";
  cls->tp_basicsize = sizeof(PythonClassNode);
  cls->tp_doc =
      "Reference to a Node; the low level building block of a game.\n"
      "\n"
      "At its core, a game is nothing more than a scene of Nodes\n"
      "with attributes getting interconnected or set over time.\n"
      "\n"
      "A :class:`bascenev1.Node` instance should be thought of as a\n"
      "weak-reference to a game node; *not* the node itself. This means\n"
      "a Node's lifecycle is completely independent of how many Python\n"
      "references to it exist. To explicitly add a new node to the game, use\n"
      ":meth:`bascenev1.newnode()`, and to explicitly delete one, use\n"
      ":meth:`bascenev1.Node.delete()`.\n"
      ":meth:`bascenev1.Node.exists()` can be used to determine if a Node\n"
      "still points to a live node in the game.\n"
      "\n"
      "You can use ``bascenev1.Node(None)`` to instantiate an invalid\n"
      "Node reference (sometimes used as attr values/etc).";
  cls->tp_new = tp_new;
  cls->tp_dealloc = (destructor)tp_dealloc;
  cls->tp_getattro = (getattrofunc)tp_getattro;
  cls->tp_setattro = (setattrofunc)tp_setattro;
  cls->tp_methods = tp_methods;

  // We provide number methods only for bool functionality.
  memset(&as_number_, 0, sizeof(as_number_));
  as_number_.nb_bool = (inquiry)nb_bool;
  cls->tp_as_number = &as_number_;
}

auto PythonClassNode::Create(Node* node) -> PyObject* {
  // Make sure we only have one python ref per node.
  if (node) {
    assert(!node->HasPyRef());
  }

  s_create_empty_ = true;  // Prevent class from erroring on create.
  assert(TypeIsSetUp(&type_obj));
  auto* py_node = reinterpret_cast<PythonClassNode*>(
      PyObject_CallObject(reinterpret_cast<PyObject*>(&type_obj), nullptr));
  s_create_empty_ = false;
  if (!py_node) {
    throw Exception("bascenev1.Node creation failed.");
  }

  *py_node->node_ = node;
  return reinterpret_cast<PyObject*>(py_node);
}

auto PythonClassNode::GetNode(bool doraise) const -> Node* {
  Node* n = node_->get();
  if (!n && doraise) {
    throw Exception(PyExcType::kNodeNotFound);
  }
  return n;
}

auto PythonClassNode::tp_new(PyTypeObject* type, PyObject* args,
                             PyObject* keywds) -> PyObject* {
  auto* self = reinterpret_cast<PythonClassNode*>(type->tp_alloc(type, 0));
  if (!self) {
    return nullptr;
  }
  BA_PYTHON_TRY;
  if (!g_base->InLogicThread()) {
    throw Exception(
        "ERROR: " + std::string(type_obj.tp_name)
        + " objects must only be created in the logic thread (current is ("
        + g_core->CurrentThreadName() + ").");
  }
  // Clion incorrectly things s_create_empty will always be false.
#pragma clang diagnostic push
#pragma ide diagnostic ignored "ConstantConditionsOC"
  if (!s_create_empty_) {
    if (!PyTuple_Check(args) || (PyTuple_GET_SIZE(args) != 1)
        || (keywds != nullptr) || (PyTuple_GET_ITEM(args, 0) != Py_None)) {
      throw Exception(
          "Can't create Nodes this way; use bascenev1.newnode() or use "
          "bascenev1.Node(None) to get an invalid reference.");
    }
  }
  self->node_ = new Object::WeakRef<Node>();
#pragma clang diagnostic pop
  return reinterpret_cast<PyObject*>(self);
  BA_PYTHON_NEW_CATCH;
}

void PythonClassNode::tp_dealloc(PythonClassNode* self) {
  BA_PYTHON_TRY;
  // These have to be deleted in the logic thread; send the ptr along if need
  // be; otherwise do it immediately.
  if (!g_base->InLogicThread()) {
    Object::WeakRef<Node>* n = self->node_;
    g_base->logic->event_loop()->PushCall([n] { delete n; });
  } else {
    delete self->node_;
  }
  BA_PYTHON_DEALLOC_CATCH;
  Py_TYPE(self)->tp_free(reinterpret_cast<PyObject*>(self));
}

auto PythonClassNode::tp_repr(PythonClassNode* self) -> PyObject* {
  BA_PYTHON_TRY;
  Node* node = self->node_->get();
  return Py_BuildValue(
      "s",
      std::string("<bascenev1.Node "
                  + (node ? ("#" + std::to_string(node->id()) + " ") : "")
                  + (node ? ("'" + node->label() + "'") : "(empty ref)") + ">")
          .c_str());
  BA_PYTHON_CATCH;
}

auto PythonClassNode::tp_getattro(PythonClassNode* self, PyObject* attr)
    -> PyObject* {
  BA_PYTHON_TRY;

  // Do we need to support other attr types?
  assert(PyUnicode_Check(attr));

  // If our node exists and has this attr, return it.
  // Otherwise do default python path.
  Node* node = self->node_->get();
  const char* attr_name = PyUnicode_AsUTF8(attr);
  if (node && node->HasAttribute(attr_name)) {
    return SceneV1Python::GetNodeAttr(node, attr_name);
  } else {
    return PyObject_GenericGetAttr(reinterpret_cast<PyObject*>(self), attr);
  }
  BA_PYTHON_CATCH;
}

auto PythonClassNode::Exists(PythonClassNode* self) -> PyObject* {
  BA_PYTHON_TRY;
  if (self->node_->exists()) {
    Py_RETURN_TRUE;
  } else {
    Py_RETURN_FALSE;
  }
  BA_PYTHON_CATCH;
}

auto PythonClassNode::GetNodeType(PythonClassNode* self) -> PyObject* {
  BA_PYTHON_TRY;

  Node* node = self->node_->get();
  if (!node) {
    throw Exception(PyExcType::kNodeNotFound);
  }
  return PyUnicode_FromString(node->type()->name().c_str());

  BA_PYTHON_CATCH;
}

auto PythonClassNode::GetName(PythonClassNode* self) -> PyObject* {
  BA_PYTHON_TRY;

  Node* node = self->node_->get();
  if (!node) {
    throw Exception(PyExcType::kNodeNotFound);
  }
  return PyUnicode_FromString(node->label().c_str());

  BA_PYTHON_CATCH;
}

auto PythonClassNode::GetDelegate(PythonClassNode* self, PyObject* args,
                                  PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  static const char* kwlist[] = {"type", "doraise", nullptr};
  PyObject* tp_obj{};
  int doraise{};
  if (!PyArg_ParseTupleAndKeywords(
          args, keywds, "O|p", const_cast<char**>(kwlist), &tp_obj, &doraise)) {
    return nullptr;
  }
  Node* node = self->node_->get();
  if (!node) {
    throw Exception(PyExcType::kNodeNotFound);
  }
  if (!PyType_Check(tp_obj)) {
    throw Exception("Passed type arg is not a type.", PyExcType::kType);
  }
  // GetDelegate() returns a new ref or nullptr.
  auto obj{PythonRef::StolenSoft(node->GetDelegate())};
  if (obj.exists()) {
    // if (PyObject* obj = node->GetDelegateOld()) {
    int isinst = PyObject_IsInstance(obj.get(), tp_obj);
    if (isinst == -1) {
      return nullptr;
    }
    if (isinst) {
      return obj.NewRef();
    } else {
      if (doraise) {
        throw Exception("Requested delegate type not found on '"
                            + node->type()->name()
                            + "' node. (type=" + Python::ObjToString(tp_obj)
                            + ", delegate=" + obj.Str() + ")",
                        PyExcType::kDelegateNotFound);
      }
    }
  } else {
    if (doraise) {
      throw Exception("No delegate set on '" + node->type()->name() + "' node.",
                      PyExcType::kDelegateNotFound);
    }
  }
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PythonClassNode::Delete(PythonClassNode* self, PyObject* args,
                             PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  int ignore_missing = 1;
  static const char* kwlist[] = {"ignore_missing", nullptr};
  if (!PyArg_ParseTupleAndKeywords(
          args, keywds, "|i", const_cast<char**>(kwlist), &ignore_missing)) {
    return nullptr;
  }
  Node* node = self->node_->get();
  if (!node) {
    if (!ignore_missing) {
      throw Exception(PyExcType::kNodeNotFound);
    }
  } else {
    node->scene()->DeleteNode(node);
  }
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PythonClassNode::HandleMessage(PythonClassNode* self, PyObject* args)
    -> PyObject* {
  BA_PYTHON_TRY;
  Py_ssize_t tuple_size = PyTuple_GET_SIZE(args);
  if (tuple_size < 1) {
    PyErr_SetString(PyExc_AttributeError, "must provide at least 1 arg");
    return nullptr;
  }
  std::vector<char> b;
  PyObject* user_message_obj;
  SceneV1Python::DoBuildNodeMessage(args, 0, &b, &user_message_obj);

  // Should we fail if the node doesn't exist??
  Node* node = self->node_->get();
  if (node) {
    HostActivity* host_activity = node->context_ref().GetHostActivity();
    if (!host_activity) {
      throw Exception("Invalid context_ref.", PyExcType::kContext);
    }
    // For user messages we pass them directly to the node
    // since by their nature they don't go out over the network and are just
    // for use within the scripting system.
    if (user_message_obj) {
      node->DispatchUserMessage(user_message_obj, "Node User-Message dispatch");
    } else {
      if (SessionStream* output_stream = node->scene()->GetSceneStream()) {
        output_stream->NodeMessage(node, b.data(), b.size());
      }
      node->DispatchNodeMessage(b.data());
    }
  }
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PythonClassNode::AddDeathAction(PythonClassNode* self, PyObject* args)
    -> PyObject* {
  BA_PYTHON_TRY;
  PyObject* call_obj;
  if (!PyArg_ParseTuple(args, "O", &call_obj)) {
    return nullptr;
  }
  Node* n = self->node_->get();
  if (!n) {
    throw Exception(PyExcType::kNodeNotFound);
  }

  // We don't have to go through a host-activity but lets make sure we're in
  // one.
  HostActivity* host_activity = n->context_ref().GetHostActivity();
  if (!host_activity) {
    throw Exception("Invalid context_ref.", PyExcType::kContext);
  }
  n->AddNodeDeathAction(call_obj);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PythonClassNode::ConnectAttr(PythonClassNode* self, PyObject* args)
    -> PyObject* {
  BA_PYTHON_TRY;
  PyObject* dst_node_obj;
  Node* node = self->node_->get();
  if (!node) {
    throw Exception(PyExcType::kNodeNotFound);
  }
  char *src_attr_name, *dst_attr_name;
  if (!PyArg_ParseTuple(args, "sOs", &src_attr_name, &dst_node_obj,
                        &dst_attr_name)) {
    return nullptr;
  }

  // Allow dead-refs and None.
  Node* dst_node = SceneV1Python::GetPyNode(dst_node_obj, true, true);
  if (!dst_node) {
    throw Exception(PyExcType::kNodeNotFound);
  }
  NodeAttributeUnbound* src_attr =
      node->type()->GetAttribute(std::string(src_attr_name));
  NodeAttributeUnbound* dst_attr =
      dst_node->type()->GetAttribute(std::string(dst_attr_name));

  // Push to output_stream first to catch scene mismatch errors.
  if (SessionStream* output_stream = node->scene()->GetSceneStream()) {
    output_stream->ConnectNodeAttribute(node, src_attr, dst_node, dst_attr);
  }

  // Now apply locally.
  node->ConnectAttribute(src_attr, dst_node, dst_attr);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PythonClassNode::Dir(PythonClassNode* self) -> PyObject* {
  BA_PYTHON_TRY;

  // Start with the standard python dir listing.
  PyObject* dir_list = Python::generic_dir(reinterpret_cast<PyObject*>(self));
  assert(PyList_Check(dir_list));

  // ..now grab all this guy's BA attributes and add them in.
  Node* node = self->node_->get();
  if (node) {
    std::list<std::string> attrs;
    node->ListAttributes(&attrs);
    for (auto& attr : attrs) {
      PyList_Append(dir_list, PythonRef(PyUnicode_FromString(attr.c_str()),
                                        PythonRef::kSteal)
                                  .get());
    }
  }
  PyList_Sort(dir_list);
  return dir_list;
  BA_PYTHON_CATCH;
}

auto PythonClassNode::nb_bool(PythonClassNode* self) -> int {
  return self->node_->exists();
}

auto PythonClassNode::tp_setattro(PythonClassNode* self, PyObject* attr,
                                  PyObject* val) -> int {
  BA_PYTHON_TRY;

  // FIXME: do we need to support other attr types?
  assert(PyUnicode_Check(attr));
  Node* n = self->node_->get();
  if (!n) {
    throw Exception(PyExcType::kNodeNotFound);
  }
  SceneV1Python::SetNodeAttr(n, PyUnicode_AsUTF8(attr), val);
  return 0;
  BA_PYTHON_INT_CATCH;
}

PyMethodDef PythonClassNode::tp_methods[] = {
    {"exists", (PyCFunction)Exists, METH_NOARGS,
     "exists() -> bool\n"
     "\n"
     "Returns whether the Node still exists.\n"
     "Most functionality will fail on a nonexistent Node, so it's never a bad\n"
     "idea to check this.\n"
     "\n"
     "Note that you can also use the boolean operator for this same\n"
     "functionality, so a statement such as \"if mynode\" will do\n"
     "the right thing both for Node objects and values of None."},
    {"getnodetype", (PyCFunction)GetNodeType, METH_NOARGS,
     "getnodetype() -> str\n"
     "\n"
     "Return the internal type of node referenced by this object as a string.\n"
     "(Note this is different from the Python type which is always\n"
     ":class:`bascenev1.Node`)"},
    {"getname", (PyCFunction)GetName, METH_NOARGS,
     "getname() -> str\n"
     "\n"
     "Return the name assigned to a Node; used mainly for debugging"},
    {"getdelegate", (PyCFunction)GetDelegate, METH_VARARGS | METH_KEYWORDS,
     "getdelegate(type: type, doraise: bool = False) -> <varies>\n"
     "\n"
     "Return the node's current delegate object if it matches\n"
     "a certain type.\n"
     "\n"
     "If the node has no delegate or it is not an instance of the passed\n"
     "type, then None will be returned. If 'doraise' is True, then an\n"
     "bascenev1.DelegateNotFoundError will be raised instead."},
    {"delete", (PyCFunction)Delete, METH_VARARGS | METH_KEYWORDS,
     "delete(ignore_missing: bool = True) -> None\n"
     "\n"
     "Delete the node. Ignores already-deleted nodes if `ignore_missing`\n"
     "is True; otherwise a :class:`babase.NodeNotFoundError` is thrown."},
    {"handlemessage", (PyCFunction)HandleMessage, METH_VARARGS,
     "handlemessage(*args: Any) -> None\n"
     "\n"
     "General message handling; can be passed any message object.\n"
     "\n"
     "All standard message objects are forwarded along to the node's\n"
     "delegate for handling (generally the :class:`bascenev1.Actor` that\n"
     "made the node).\n"
     "\n"
     "Nodes also support a second form of message; 'node-messages'.\n"
     "These consist of a string type-name as a first argument along with\n"
     "the args specific to that type name as additional arguments.\n"
     "Node-messages communicate directly with the low-level node\n"
     "layer and are delivered simultaneously on all game clients, acting\n"
     "as an alternative to setting node attributes."},
    {"add_death_action", (PyCFunction)AddDeathAction, METH_VARARGS,
     "add_death_action(action: Callable[[], None]) -> None\n"
     "\n"
     "Add a callable object to be called upon this node's death.\n"
     "Note that these actions are run just after the node dies, not before.\n"},
    {"connectattr", (PyCFunction)ConnectAttr, METH_VARARGS,
     "connectattr(srcattr: str, dstnode: Node, dstattr: str) -> None\n"
     "\n"
     "Connect one of this node's attributes to an attribute on another\n"
     "node. This will immediately set the target attribute's value to that\n"
     "of the source attribute, and will continue to do so once per step\n"
     "as long as the two nodes exist. The connection can be severed by\n"
     "setting the target attribute to any value or connecting another\n"
     "node attribute to it.\n"
     "\n"
     "Example: Create a locator and attach a light to it::\n"
     "\n"
     "    light = bascenev1.newnode('light')\n"
     "    loc = bascenev1.newnode('locator', attrs={'position': (0, 10, 0)})\n"
     "    loc.connectattr('position', light, 'position')\n"},
    {"__dir__", (PyCFunction)Dir, METH_NOARGS,
     "allows inclusion of our custom attrs in standard python dir()"},
    {nullptr}};

bool PythonClassNode::s_create_empty_ = false;
PyTypeObject PythonClassNode::type_obj;

#pragma clang diagnostic pop

}  // namespace ballistica::scene_v1
