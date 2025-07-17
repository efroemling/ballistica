// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/python/scene_v1_python.h"

#include <algorithm>
#include <cstdio>
#include <list>
#include <string>
#include <utility>
#include <vector>

#include "ballistica/base/input/device/keyboard_input.h"
#include "ballistica/base/input/input.h"
#include "ballistica/base/python/base_python.h"
#include "ballistica/base/python/class/python_class_context_ref.h"
#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging_macros.h"
#include "ballistica/scene_v1/assets/scene_collision_mesh.h"
#include "ballistica/scene_v1/assets/scene_mesh.h"
#include "ballistica/scene_v1/assets/scene_sound.h"
#include "ballistica/scene_v1/assets/scene_texture.h"
#include "ballistica/scene_v1/dynamics/material/material.h"
#include "ballistica/scene_v1/node/node_attribute.h"
#include "ballistica/scene_v1/python/class/python_class_activity_data.h"
#include "ballistica/scene_v1/python/class/python_class_base_timer.h"
#include "ballistica/scene_v1/python/class/python_class_input_device.h"
#include "ballistica/scene_v1/python/class/python_class_material.h"
#include "ballistica/scene_v1/python/class/python_class_node.h"
#include "ballistica/scene_v1/python/class/python_class_scene_collision_mesh.h"
#include "ballistica/scene_v1/python/class/python_class_scene_data_asset.h"
#include "ballistica/scene_v1/python/class/python_class_scene_mesh.h"
#include "ballistica/scene_v1/python/class/python_class_scene_sound.h"
#include "ballistica/scene_v1/python/class/python_class_scene_texture.h"
#include "ballistica/scene_v1/python/class/python_class_scene_timer.h"
#include "ballistica/scene_v1/python/class/python_class_session_data.h"
#include "ballistica/scene_v1/python/class/python_class_session_player.h"
#include "ballistica/scene_v1/python/methods/python_methods_assets.h"
#include "ballistica/scene_v1/python/methods/python_methods_input.h"
#include "ballistica/scene_v1/python/methods/python_methods_networking.h"
#include "ballistica/scene_v1/python/methods/python_methods_scene.h"
#include "ballistica/scene_v1/support/scene.h"
#include "ballistica/scene_v1/support/scene_v1_input_device_delegate.h"
#include "ballistica/scene_v1/support/session_stream.h"
#include "ballistica/shared/generic/utils.h"
#include "ballistica/shared/python/python_command.h"  // IWYU pragma: keep.
#include "ballistica/shared/python/python_module_builder.h"

namespace ballistica::scene_v1 {

SceneV1Python::SceneV1Python() = default;

// Need to declare a plain c PyInit_XXX function with our module name in it so
// we're discoverable when compiled as a standalone binary Python module.
extern "C" auto PyInit__bascenev1() -> PyObject* {
  auto* builder =
      new PythonModuleBuilder("_bascenev1",
                              {
                                  PythonMethodsInput::GetMethods(),
                                  PythonMethodsAssets::GetMethods(),
                                  PythonMethodsNetworking::GetMethods(),
                                  PythonMethodsScene::GetMethods(),
                              },
                              [](PyObject* module) -> int {
                                BA_PYTHON_TRY;
                                SceneV1FeatureSet::OnModuleExec(module);
                                return 0;
                                BA_PYTHON_INT_CATCH;
                              });
  return builder->Build();
}

void SceneV1Python::AddPythonClasses(PyObject* module) {
  PythonModuleBuilder::AddClass<PythonClassInputDevice>(module);
  PythonModuleBuilder::AddClass<PythonClassNode>(module);
  PythonModuleBuilder::AddClass<PythonClassSessionPlayer>(module);
  PythonModuleBuilder::AddClass<PythonClassSessionData>(module);
  PythonModuleBuilder::AddClass<PythonClassActivityData>(module);
  PythonModuleBuilder::AddClass<PythonClassSceneTimer>(module);
  PythonModuleBuilder::AddClass<PythonClassBaseTimer>(module);
  PythonModuleBuilder::AddClass<PythonClassMaterial>(module);
  PythonModuleBuilder::AddClass<PythonClassSceneTexture>(module);
  PythonModuleBuilder::AddClass<PythonClassSceneSound>(module);
  PythonModuleBuilder::AddClass<PythonClassSceneDataAsset>(module);
  PythonModuleBuilder::AddClass<PythonClassSceneMesh>(module);
  PythonModuleBuilder::AddClass<PythonClassSceneCollisionMesh>(module);
}

void SceneV1Python::ImportPythonObjs() {
#include "ballistica/scene_v1/mgen/pyembed/binding_scene_v1.inc"
}

void SceneV1Python::Reset() {
  assert(g_base->InLogicThread());
  ReleaseJoystickInputCapture();
  ReleaseKeyboardInputCapture();
}

void SceneV1Python::SetNodeAttr(Node* node, const char* attr_name,
                                PyObject* value_obj) {
  assert(node);
  SessionStream* out_stream = node->scene()->GetSceneStream();
  NodeAttribute attr = node->GetAttribute(attr_name);
  switch (attr.type()) {
    case NodeAttributeType::kFloat: {
      float val = Python::GetFloat(value_obj);
      if (out_stream) {
        out_stream->SetNodeAttr(attr, val);
      }

      // If something was driving this attr, disconnect it.
      attr.DisconnectIncoming();
      attr.Set(val);
      break;
    }
    case NodeAttributeType::kInt: {
      int64_t val = Python::GetInt64(value_obj);
      if (out_stream) {
        out_stream->SetNodeAttr(attr, val);
      }

      // If something was driving this attr, disconnect it.
      attr.DisconnectIncoming();
      attr.Set(val);
      break;
    }
    case NodeAttributeType::kBool: {
      bool val = Python::GetBool(value_obj);
      if (out_stream) {
        out_stream->SetNodeAttr(attr, val);
      }

      // If something was driving this attr, disconnect it.
      attr.DisconnectIncoming();
      attr.Set(val);
      break;
    }
    case NodeAttributeType::kFloatArray: {
      std::vector<float> vals = Python::GetFloats(value_obj);
      if (out_stream) {
        out_stream->SetNodeAttr(attr, vals);
      }

      // If something was driving this attr, disconnect it.
      attr.DisconnectIncoming();
      attr.Set(vals);
      break;
    }
    case NodeAttributeType::kIntArray: {
      std::vector<int64_t> vals = Python::GetInts64(value_obj);
      if (out_stream) {
        out_stream->SetNodeAttr(attr, vals);
      }

      // If something was driving this attr, disconnect it.
      attr.DisconnectIncoming();
      attr.Set(vals);
      break;
    }
    case NodeAttributeType::kString: {
      std::string val = g_base->python->GetPyLString(value_obj);
      if (out_stream) {
        out_stream->SetNodeAttr(attr, val);
      }

      // If something was driving this attr, disconnect it.
      attr.DisconnectIncoming();
      attr.Set(val);
      break;
    }
    case NodeAttributeType::kNode: {
      // Allow dead-refs or None.
      Node* val = GetPyNode(value_obj, true, true);
      if (out_stream) {
        out_stream->SetNodeAttr(attr, val);
      }

      // If something was driving this attr, disconnect it.
      attr.DisconnectIncoming();
      attr.Set(val);
      break;
    }
    case NodeAttributeType::kNodeArray: {
      std::vector<Node*> vals = GetPyNodes(value_obj);
      if (out_stream) {
        out_stream->SetNodeAttr(attr, vals);
      }

      // If something was driving this attr, disconnect it.
      attr.DisconnectIncoming();
      attr.Set(vals);
      break;
    }
    case NodeAttributeType::kPlayer: {
      // Allow dead-refs and None.
      Player* val = GetPyPlayer(value_obj, true, true);
      if (out_stream) {
        out_stream->SetNodeAttr(attr, val);
      }

      // If something was driving this attr, disconnect it.
      attr.DisconnectIncoming();
      attr.Set(val);
      break;
    }
    case NodeAttributeType::kMaterialArray: {
      std::vector<Material*> vals = GetPyMaterials(value_obj);
      if (out_stream) {
        out_stream->SetNodeAttr(attr, vals);
      }

      // If something was driving this attr, disconnect it.
      attr.DisconnectIncoming();
      attr.Set(vals);
      break;
    }
    case NodeAttributeType::kTexture: {
      // Don't allow dead-refs, do allow None.
      SceneTexture* val = GetPySceneTexture(value_obj, false, true);
      if (out_stream) {
        out_stream->SetNodeAttr(attr, val);
      }

      // If something was driving this attr, disconnect it.
      attr.DisconnectIncoming();
      attr.Set(val);
      break;
    }
    case NodeAttributeType::kTextureArray: {
      std::vector<SceneTexture*> vals = GetPySceneTextures(value_obj);
      if (out_stream) {
        out_stream->SetNodeAttr(attr, vals);
      }

      // If something was driving this attr, disconnect it.
      attr.DisconnectIncoming();
      attr.Set(vals);
      break;
    }
    case NodeAttributeType::kSound: {
      // Don't allow dead-refs, do allow None.
      SceneSound* val = GetPySceneSound(value_obj, false, true);
      if (out_stream) {
        out_stream->SetNodeAttr(attr, val);
      }

      // If something was driving this attr, disconnect it.
      attr.DisconnectIncoming();
      attr.Set(val);
      break;
    }
    case NodeAttributeType::kSoundArray: {
      std::vector<SceneSound*> vals = GetPySceneSounds(value_obj);
      if (out_stream) {
        out_stream->SetNodeAttr(attr, vals);
      }

      // If something was driving this attr, disconnect it.
      attr.DisconnectIncoming();
      attr.Set(vals);
      break;
    }
    case NodeAttributeType::kMesh: {
      // Don't allow dead-refs, do allow None.
      SceneMesh* val = GetPySceneMesh(value_obj, false, true);
      if (out_stream) {
        out_stream->SetNodeAttr(attr, val);
      }

      // If something was driving this attr, disconnect it.
      attr.DisconnectIncoming();
      attr.Set(val);
      break;
    }
    case NodeAttributeType::kMeshArray: {
      std::vector<SceneMesh*> vals = GetPySceneMeshes(value_obj);
      if (out_stream) {
        out_stream->SetNodeAttr(attr, vals);
      }

      // If something was driving this attr, disconnect it.
      attr.DisconnectIncoming();
      attr.Set(vals);
      break;
    }
    case NodeAttributeType::kCollisionMesh: {
      // Don't allow dead-refs, do allow None.
      SceneCollisionMesh* val = GetPySceneCollisionMesh(value_obj, false, true);
      if (out_stream) {
        out_stream->SetNodeAttr(attr, val);
      }

      // If something was driving this attr, disconnect it.
      attr.DisconnectIncoming();
      attr.Set(val);
      break;
    }
    case NodeAttributeType::kCollisionMeshArray: {
      std::vector<SceneCollisionMesh*> vals =
          GetPySceneCollisionMeshes(value_obj);
      if (out_stream) {
        out_stream->SetNodeAttr(attr, vals);
      }

      // If something was driving this attr, disconnect it.
      attr.DisconnectIncoming();
      attr.Set(vals);
      break;
    }
    default:
      throw Exception("FIXME: unhandled attr type in SetNodeAttr: '"
                      + attr.GetTypeName() + "'.");
  }
}

static auto CompareAttrIndices(
    const std::pair<NodeAttributeUnbound*, PyObject*>& first,
    const std::pair<NodeAttributeUnbound*, PyObject*>& second) -> bool {
  return (first.first->index() < second.first->index());
}

auto SceneV1Python::DoNewNode(PyObject* args, PyObject* keywds) -> Node* {
  BA_PRECONDITION(g_base->InLogicThread());
  PyObject* delegate_obj = Py_None;
  PyObject* owner_obj = Py_None;
  PyObject* name_obj = Py_None;
  static const char* kwlist[] = {"type", "owner",    "attrs",
                                 "name", "delegate", nullptr};
  char* type;
  PyObject* dict = nullptr;
  if (!PyArg_ParseTupleAndKeywords(
          args, keywds, "s|OOOO", const_cast<char**>(kwlist), &type, &owner_obj,
          &dict, &name_obj, &delegate_obj)) {
    return nullptr;
  }

  std::string name;
  if (name_obj != Py_None) {
    name = Python::GetString(name_obj);
  } else {
    // By default do something like 'text@foo.py:20'.
    name = std::string(type) + "@" + Python::GetPythonFileLocation();
  }

  Scene* scene = ContextRefSceneV1::FromCurrent().GetMutableScene();
  if (!scene) {
    throw Exception("Can't create nodes in this context_ref.",
                    PyExcType::kContext);
  }

  Node* node = scene->NewNode(type, name, delegate_obj);

  // Handle attr values fed in.
  if (dict) {
    if (!PyDict_Check(dict)) {
      throw Exception("Expected dict for arg 2.", PyExcType::kType);
    }
    NodeType* t = node->type();
    PyObject* key{};
    PyObject* value{};
    Py_ssize_t pos{};

    // We want to set initial attrs in order based on their attr indices.
    std::list<std::pair<NodeAttributeUnbound*, PyObject*>> attr_vals;

    // Grab all initial attr/values and add them to a list.
    while (PyDict_Next(dict, &pos, &key, &value)) {
      if (!PyUnicode_Check(key)) {
        throw Exception("Expected string key in attr dict.", PyExcType::kType);
      }
      try {
        attr_vals.emplace_back(
            t->GetAttribute(std::string(PyUnicode_AsUTF8(key))), value);
      } catch (const std::exception&) {
        g_core->logging->Log(LogName::kBa, LogLevel::kError,
                             "Attr not found on initial attr set: '"
                                 + std::string(PyUnicode_AsUTF8(key)) + "' on "
                                 + type + " node '" + name + "'");
      }
    }

    // Run the sets in the order of attr indices.
    attr_vals.sort(CompareAttrIndices);
    for (auto&& i : attr_vals) {
      try {
        SetNodeAttr(node, i.first->name().c_str(), i.second);
      } catch (const std::exception& e) {
        g_core->logging->Log(LogName::kBa, LogLevel::kError,
                             "Exception in initial attr set for attr '"
                                 + i.first->name() + "' on " + type + " node '"
                                 + name + "':" + e.what());
      }
    }
  }

  // If an owner was provided, set it up.
  if (owner_obj != Py_None) {
    // If its a node, set up a dependency at the scene level
    // (then we just have to delete the owner node and the scene does the
    // rest).
    if (PythonClassNode::Check(owner_obj)) {
      Node* owner_node = GetPyNode(owner_obj, true);
      if (owner_node == nullptr) {
        g_core->logging->Log(
            LogName::kBa, LogLevel::kError,
            "Empty node-ref passed for 'owner'; pass None if you want "
            "no owner.");
      } else if (owner_node->scene() != node->scene()) {
        g_core->logging->Log(LogName::kBa, LogLevel::kError,
                             "Owner node is from a different scene; ignoring.");
      } else {
        owner_node->AddDependentNode(node);
      }
    } else {
      throw Exception(
          "Invalid node owner: " + Python::ObjToString(owner_obj) + ".",
          PyExcType::kType);
    }
  }

  // Lastly, call this node's OnCreate method for any final setup it may want to
  // do.
  try {
    // Tell clients to do the same.
    if (SessionStream* output_stream = scene->GetSceneStream()) {
      output_stream->NodeOnCreate(node);
    }
    node->OnCreate();
  } catch (const std::exception& e) {
    g_core->logging->Log(LogName::kBa, LogLevel::kError,
                         "Exception in OnCreate() for node "
                             + ballistica::ObjToString(node) + "':" + e.what());
  }

  return node;
}

// Return the node attr as a PyObject, or nullptr if the node doesn't have that
// attr.
auto SceneV1Python::GetNodeAttr(Node* node, const char* attr_name)
    -> PyObject* {
  assert(node);
  NodeAttribute attr = node->GetAttribute(attr_name);
  switch (attr.type()) {
    case NodeAttributeType::kFloat:
      return PyFloat_FromDouble(attr.GetAsFloat());
      break;
    case NodeAttributeType::kInt:
      return PyLong_FromLong(
          static_cast_check_fit<long>(attr.GetAsInt()));  // NOLINT
      break;
    case NodeAttributeType::kBool:
      if (attr.GetAsBool()) {
        Py_RETURN_TRUE;
      } else {
        Py_RETURN_FALSE;
      }
      break;
    case NodeAttributeType::kString: {
      if (g_buildconfig.debug_build()) {
        std::string s = attr.GetAsString();
        assert(Utils::IsValidUTF8(s));
        return PyUnicode_FromString(s.c_str());
      } else {
        return PyUnicode_FromString(attr.GetAsString().c_str());
      }
      break;
    }
    case NodeAttributeType::kNode: {
      // Return a new py ref to this node or create a new empty ref.
      Node* n = attr.GetAsNode();
      return n ? n->NewPyRef() : PythonClassNode::Create(nullptr);
      break;
    }
    case NodeAttributeType::kPlayer: {
      // Player attrs deal with custom user bascenev1.Player classes;
      // not our internal SessionPlayer class.
      Player* p = attr.GetAsPlayer();
      if (p == nullptr) {
        Py_RETURN_NONE;
      }
      PyObject* gameplayer = p->GetPyActivityPlayer();
      Py_INCREF(gameplayer);
      return gameplayer;
      // return p ? p->NewPyRef() : PythonClassSessionPlayer::Create(nullptr);
      break;
    }
    case NodeAttributeType::kFloatArray: {
      std::vector<float> vals = attr.GetAsFloats();
      auto size{static_cast<Py_ssize_t>(vals.size())};
      PyObject* vals_obj = PyTuple_New(size);
      assert(vals_obj);
      for (Py_ssize_t i = 0; i < size; i++) {
        PyTuple_SET_ITEM(vals_obj, i, PyFloat_FromDouble(vals[i]));
      }
      return vals_obj;
      break;
    }
    case NodeAttributeType::kIntArray: {
      std::vector<int64_t> vals = attr.GetAsInts();
      auto size{static_cast<Py_ssize_t>(vals.size())};
      PyObject* vals_obj = PyTuple_New(size);
      assert(vals_obj);
      for (Py_ssize_t i = 0; i < size; i++) {
        PyTuple_SET_ITEM(vals_obj, i,
                         PyLong_FromLong(static_cast_check_fit<long>(  // NOLINT
                             vals[i])));
      }
      return vals_obj;
      break;
    }
    case NodeAttributeType::kNodeArray: {
      std::vector<Node*> vals = attr.GetAsNodes();
      auto size{static_cast<Py_ssize_t>(vals.size())};
      PyObject* vals_obj = PyTuple_New(size);
      assert(vals_obj);
      for (Py_ssize_t i = 0; i < size; i++) {
        Node* n = vals[i];
        PyTuple_SET_ITEM(vals_obj, i,
                         n ? n->NewPyRef() : PythonClassNode::Create(nullptr));
      }
      return vals_obj;
      break;
    }
    case NodeAttributeType::kTexture: {
      SceneTexture* t = attr.GetAsTexture();
      if (!t) {
        Py_RETURN_NONE;
      }
      return t->NewPyRef();
      break;
    }
    case NodeAttributeType::kSound: {
      SceneSound* s = attr.GetAsSound();
      if (!s) {
        Py_RETURN_NONE;
      }
      return s->NewPyRef();
      break;
    }
    case NodeAttributeType::kMesh: {
      SceneMesh* m = attr.GetAsMesh();
      if (!m) {
        Py_RETURN_NONE;
      }
      return m->NewPyRef();
      break;
    }
    case NodeAttributeType::kCollisionMesh: {
      SceneCollisionMesh* c = attr.GetAsCollisionMesh();
      if (!c) {
        Py_RETURN_NONE;
      }
      return c->NewPyRef();
      break;
    }
    case NodeAttributeType::kMaterialArray: {
      std::vector<Material*> vals = attr.GetAsMaterials();
      auto size{static_cast<Py_ssize_t>(vals.size())};
      PyObject* vals_obj = PyTuple_New(size);
      assert(vals_obj);
      for (Py_ssize_t i = 0; i < size; i++) {
        Material* m = vals[i];

        // Array attrs should never return nullptr materials.
        assert(m);
        PyTuple_SET_ITEM(vals_obj, i, m->NewPyRef());
      }
      return vals_obj;
      break;
    }
    case NodeAttributeType::kTextureArray: {
      std::vector<SceneTexture*> vals = attr.GetAsTextures();
      auto size{static_cast<Py_ssize_t>(vals.size())};
      PyObject* vals_obj = PyTuple_New(size);
      assert(vals_obj);
      for (Py_ssize_t i = 0; i < size; i++) {
        SceneTexture* t = vals[i];

        // Array attrs should never return nullptr textures.
        assert(t);
        PyTuple_SET_ITEM(vals_obj, i, t->NewPyRef());
      }
      return vals_obj;
      break;
    }
    case NodeAttributeType::kSoundArray: {
      std::vector<SceneSound*> vals = attr.GetAsSounds();
      auto size{static_cast<Py_ssize_t>(vals.size())};
      PyObject* vals_obj = PyTuple_New(size);
      assert(vals_obj);
      for (Py_ssize_t i = 0; i < size; i++) {
        SceneSound* s = vals[i];

        // Array attrs should never return nullptr sounds.
        assert(s);
        PyTuple_SET_ITEM(vals_obj, i, s->NewPyRef());
      }
      return vals_obj;
      break;
    }
    case NodeAttributeType::kMeshArray: {
      std::vector<SceneMesh*> vals = attr.GetAsMeshes();
      auto size{static_cast<Py_ssize_t>(vals.size())};
      PyObject* vals_obj = PyTuple_New(size);
      assert(vals_obj);
      for (Py_ssize_t i = 0; i < size; i++) {
        SceneMesh* m = vals[i];

        // Array attrs should never return nullptr meshes.
        assert(m);
        PyTuple_SET_ITEM(vals_obj, i, m->NewPyRef());
      }
      return vals_obj;
      break;
    }
    case NodeAttributeType::kCollisionMeshArray: {
      std::vector<SceneCollisionMesh*> vals = attr.GetAsCollisionMeshes();
      auto size{static_cast<Py_ssize_t>(vals.size())};
      PyObject* vals_obj = PyTuple_New(size);
      assert(vals_obj);
      for (Py_ssize_t i = 0; i < size; i++) {
        SceneCollisionMesh* c = vals[i];

        // Array attrs should never return nullptr collision-meshes.
        assert(c);
        PyTuple_SET_ITEM(vals_obj, i, c->NewPyRef());
      }
      return vals_obj;
      break;
    }

    default:
      throw Exception("FIXME: unhandled attr type in GetNodeAttr: '"
                      + attr.GetTypeName() + "'.");
  }
  return nullptr;
}

auto SceneV1Python::IsPyHostActivity(PyObject* o) -> bool {
  assert(Python::HaveGIL());
  BA_PRECONDITION_FATAL(o != nullptr);

  int result =
      PyObject_IsInstance(o, g_scene_v1->python->objs()
                                 .Get(SceneV1Python::ObjID::kActivityClass)
                                 .get());
  if (result == -1) {
    result = 0;
    PyErr_Clear();
  }
  return static_cast<bool>(result);
}

auto SceneV1Python::GetPyHostActivity(PyObject* o) -> HostActivity* {
  assert(Python::HaveGIL());
  BA_PRECONDITION_FATAL(o != nullptr);

  PyExcType pyexctype{PyExcType::kType};

  // Make sure it's a subclass of bascenev1.Activity.
  if (IsPyHostActivity(o)) {
    // Look for an _activity_data attr on it.
    if (PyObject* activity_data = PyObject_GetAttrString(o, "_activity_data")) {
      // This will deallocate for us.
      PythonRef ref(activity_data, PythonRef::kSteal);
      if (PythonClassActivityData::Check(activity_data)) {
        return (reinterpret_cast<PythonClassActivityData*>(activity_data))
            ->GetHostActivity();
      }
    } else {
      pyexctype = PyExcType::kRuntime;  // activity Obj is wonky.
    }
  }

  // Failed, we have.
  // Clear any Python error that got us here; we're in C++ Exception land now.
  PyErr_Clear();
  throw Exception(
      "Can't get activity from value: " + Python::ObjToString(o) + ".",
      pyexctype);
}

auto SceneV1Python::GetPyNode(PyObject* o, bool allow_empty_ref,
                              bool allow_none) -> Node* {
  assert(Python::HaveGIL());
  BA_PRECONDITION_FATAL(o != nullptr);

  if (allow_none && (o == Py_None)) {
    return nullptr;
  }
  if (PythonClassNode::Check(o)) {
    // This will succeed or throw its own Exception.
    return (reinterpret_cast<PythonClassNode*>(o))->GetNode(!allow_empty_ref);
  }

  // Nothing here should have led to an unresolved Python error state.
  assert(!PyErr_Occurred());

  throw Exception("Can't get node from value: " + Python::ObjToString(o) + ".",
                  PyExcType::kType);
}

auto SceneV1Python::GetPyNodes(PyObject* o) -> std::vector<Node*> {
  assert(Python::HaveGIL());
  BA_PRECONDITION_FATAL(o != nullptr);

  if (!PySequence_Check(o)) {
    throw Exception("Object is not a sequence.", PyExcType::kType);
  }
  PythonRef sequence(PySequence_Fast(o, "Not a sequence."), PythonRef::kSteal);
  assert(sequence.exists());
  auto size = static_cast<size_t>(PySequence_Fast_GET_SIZE(sequence.get()));
  PyObject** pyobjs = PySequence_Fast_ITEMS(sequence.get());
  std::vector<Node*> vals(size);
  assert(vals.size() == size);
  for (size_t i = 0; i < size; i++) {
    vals[i] = GetPyNode(pyobjs[i]);
  }
  return vals;
}

auto SceneV1Python::GetPyMaterial(PyObject* o, bool allow_empty_ref,
                                  bool allow_none) -> Material* {
  assert(Python::HaveGIL());
  BA_PRECONDITION_FATAL(o != nullptr);

  if (allow_none && (o == Py_None)) {
    return nullptr;
  }
  if (PythonClassMaterial::Check(o)) {
    // This will succeed or throw its own Exception.
    return reinterpret_cast<PythonClassMaterial*>(o)->GetMaterial(
        !allow_empty_ref);
  }

  // Nothing here should have led to an unresolved Python error state.
  assert(!PyErr_Occurred());

  throw Exception(
      "Can't get material from value: " + Python::ObjToString(o) + ".",
      PyExcType::kType);
}

auto SceneV1Python::GetPyMaterials(PyObject* o) -> std::vector<Material*> {
  assert(Python::HaveGIL());
  BA_PRECONDITION_FATAL(o != nullptr);

  if (!PySequence_Check(o)) {
    throw Exception("Object is not a sequence.", PyExcType::kType);
  }
  PythonRef sequence(PySequence_Fast(o, "Not a sequence."), PythonRef::kSteal);
  assert(sequence.exists());
  auto size = static_cast<size_t>(PySequence_Fast_GET_SIZE(sequence.get()));
  PyObject** pyobjs = PySequence_Fast_ITEMS(sequence.get());
  std::vector<Material*> vals(size);
  assert(vals.size() == size);
  for (size_t i = 0; i < size; i++) {
    vals[i] = GetPyMaterial(pyobjs[i]);  // DON'T allow nullptr refs.
  }
  return vals;
}

auto SceneV1Python::GetPySceneTexture(PyObject* o, bool allow_empty_ref,
                                      bool allow_none) -> SceneTexture* {
  assert(Python::HaveGIL());
  BA_PRECONDITION_FATAL(o != nullptr);

  if (allow_none && (o == Py_None)) {
    return nullptr;
  }
  if (PythonClassSceneTexture::Check(o)) {
    // This will succeed or throw its own Exception.
    return reinterpret_cast<PythonClassSceneTexture*>(o)->GetTexture(
        !allow_empty_ref);
  }

  // Nothing here should have led to an unresolved Python error state.
  assert(!PyErr_Occurred());

  throw Exception(
      "Can't get bascenev1.Texture from value: " + Python::ObjToString(o) + ".",
      PyExcType::kType);
}

auto SceneV1Python::GetPySceneTextures(PyObject* o)
    -> std::vector<SceneTexture*> {
  assert(Python::HaveGIL());
  BA_PRECONDITION_FATAL(o != nullptr);

  if (!PySequence_Check(o)) {
    throw Exception("Object is not a sequence.", PyExcType::kType);
  }
  PythonRef sequence(PySequence_Fast(o, "Not a sequence."), PythonRef::kSteal);
  assert(sequence.exists());
  auto size = static_cast<size_t>(PySequence_Fast_GET_SIZE(sequence.get()));
  PyObject** pyobjs = PySequence_Fast_ITEMS(sequence.get());
  std::vector<SceneTexture*> vals(size);
  assert(vals.size() == size);
  for (size_t i = 0; i < size; i++) {
    vals[i] =
        GetPySceneTexture(pyobjs[i]);  // DON'T allow nullptr refs or None.
  }
  return vals;
}

auto SceneV1Python::GetPySceneMesh(PyObject* o, bool allow_empty_ref,
                                   bool allow_none) -> SceneMesh* {
  assert(Python::HaveGIL());
  BA_PRECONDITION_FATAL(o != nullptr);

  if (allow_none && (o == Py_None)) {
    return nullptr;
  }
  if (PythonClassSceneMesh::Check(o)) {
    // This will succeed or throw its own Exception.
    return reinterpret_cast<PythonClassSceneMesh*>(o)->GetMesh(
        !allow_empty_ref);
  }

  // Nothing here should have led to an unresolved Python error state.
  assert(!PyErr_Occurred());

  throw Exception(
      "Can't get bascenev1.Mesh from value: " + Python::ObjToString(o) + ".",
      PyExcType::kType);
}

auto SceneV1Python::GetPySceneMeshes(PyObject* o) -> std::vector<SceneMesh*> {
  assert(Python::HaveGIL());
  BA_PRECONDITION_FATAL(o != nullptr);

  if (!PySequence_Check(o)) {
    throw Exception("Object is not a sequence.", PyExcType::kType);
  }
  PythonRef sequence(PySequence_Fast(o, "Not a sequence."), PythonRef::kSteal);
  assert(sequence.exists());
  auto size = static_cast<size_t>(PySequence_Fast_GET_SIZE(sequence.get()));
  PyObject** pyobjs = PySequence_Fast_ITEMS(sequence.get());
  std::vector<SceneMesh*> vals(size);
  assert(vals.size() == size);
  for (size_t i = 0; i < size; i++) {
    vals[i] = GetPySceneMesh(pyobjs[i], false);  // DON'T allow nullptr refs.
  }
  return vals;
}

auto SceneV1Python::IsPyPlayer(PyObject* o) -> bool {
  assert(Python::HaveGIL());
  BA_PRECONDITION_FATAL(o != nullptr);

  int result = PyObject_IsInstance(
      o,
      g_scene_v1->python->objs().Get(SceneV1Python::ObjID::kPlayerClass).get());
  if (result == -1) {
    result = 0;
    PyErr_Clear();
  }
  return static_cast<bool>(result);
}

auto SceneV1Python::GetPyPlayer(PyObject* o, bool allow_empty_ref,
                                bool allow_none) -> Player* {
  assert(Python::HaveGIL());
  BA_PRECONDITION_FATAL(o != nullptr);

  PyExcType pyexctype{PyExcType::kType};

  if (allow_none && (o == Py_None)) {
    return nullptr;
  }

  // Make sure it's a subclass of bascenev1.Player.
  if (IsPyPlayer(o)) {
    // Look for an sessionplayer attr on it.
    if (PyObject* sessionplayer = PyObject_GetAttrString(o, "sessionplayer")) {
      // This will deallocate for us.
      PythonRef ref(sessionplayer, PythonRef::kSteal);

      if (PythonClassSessionPlayer::Check(sessionplayer)) {
        // This will succeed or throw an exception itself.
        return (reinterpret_cast<PythonClassSessionPlayer*>(sessionplayer))
            ->GetPlayer(!allow_empty_ref);
      }
    } else {
      pyexctype = PyExcType::kRuntime;  // We've got a wonky object.
    }
  }

  // Failed, we have.
  // Clear any Python error that got us here; we're in C++ Exception land now.
  PyErr_Clear();
  throw Exception(
      "Can't get player from value: " + Python::ObjToString(o) + ".",
      pyexctype);
}

auto SceneV1Python::ValidatedPackageAssetName(PyObject* package,
                                              const char* name) -> std::string {
  assert(g_base->InLogicThread());
  assert(g_scene_v1->python->objs().Exists(
      SceneV1Python::ObjID::kAssetPackageClass));

  if (!PyObject_IsInstance(package,
                           g_scene_v1->python->objs()
                               .Get(SceneV1Python::ObjID::kAssetPackageClass)
                               .get())) {
    throw Exception("Object is not an AssetPackage.", PyExcType::kType);
  }

  // Ok; they've passed us an asset-package object.
  // Now validate that its context is current...
  PythonRef context_obj(PyObject_GetAttrString(package, "context_ref"),
                        PythonRef::kSteal);
  if (!context_obj.exists()
      || !(PyObject_IsInstance(context_obj.get(),
                               reinterpret_cast<PyObject*>(
                                   &base::PythonClassContextRef::type_obj)))) {
    throw Exception("Asset package context_ref not found.",
                    PyExcType::kNotFound);
  }
  auto* pycontext =
      reinterpret_cast<base::PythonClassContextRef*>(context_obj.get());
  auto* ctargetref = pycontext->context_ref().Get();
  if (!ctargetref) {
    throw Exception("Asset package context_ref does not exist.",
                    PyExcType::kNotFound);
  }
  auto* ctargetref2 = g_base->CurrentContext().Get();
  if (ctargetref != ctargetref2) {
    throw Exception("Asset package context_ref is not current.");
  }

  // Hooray; the asset package's context exists and is current.
  // Ok; now pull the package id...
  PythonRef package_id(PyObject_GetAttrString(package, "package_id"),
                       PythonRef::kSteal);
  if (!PyUnicode_Check(package_id.get())) {
    throw Exception("Got non-string AssetPackage ID.", PyExcType::kType);
  }

  // TODO(ericf): make sure the package is valid for this context,
  // and return a fully qualified name with the package included.

  printf("would give %s:%s\n", PyUnicode_AsUTF8(package_id.get()), name);
  return name;
}

auto SceneV1Python::GetPySceneSound(PyObject* o, bool allow_empty_ref,
                                    bool allow_none) -> SceneSound* {
  assert(Python::HaveGIL());
  BA_PRECONDITION_FATAL(o != nullptr);

  if (allow_none && (o == Py_None)) {
    return nullptr;
  }
  if (PythonClassSceneSound::Check(o)) {
    // This will succeed or throw its own Exception.
    return reinterpret_cast<PythonClassSceneSound*>(o)->GetSound(
        !allow_empty_ref);
  }

  // Nothing here should have led to an unresolved Python error state.
  assert(!PyErr_Occurred());

  throw Exception(
      "Can't get bascenev1.Sound from value: " + Python::ObjToString(o) + ".",
      PyExcType::kType);
}

auto SceneV1Python::GetPySceneSounds(PyObject* o) -> std::vector<SceneSound*> {
  assert(Python::HaveGIL());
  BA_PRECONDITION_FATAL(o != nullptr);

  if (!PySequence_Check(o)) {
    throw Exception("Object is not a sequence.", PyExcType::kType);
  }
  PythonRef sequence(PySequence_Fast(o, "Not a sequence."), PythonRef::kSteal);
  assert(sequence.exists());
  auto size = static_cast<size_t>(PySequence_Fast_GET_SIZE(sequence.get()));
  PyObject** pyobjs = PySequence_Fast_ITEMS(sequence.get());
  std::vector<SceneSound*> vals(size);
  assert(vals.size() == size);
  for (size_t i = 0; i < size; i++) {
    vals[i] = GetPySceneSound(pyobjs[i]);  // DON'T allow nullptr refs
  }
  return vals;
}

auto SceneV1Python::GetPySceneCollisionMesh(PyObject* o, bool allow_empty_ref,
                                            bool allow_none)
    -> SceneCollisionMesh* {
  assert(Python::HaveGIL());
  BA_PRECONDITION_FATAL(o != nullptr);

  if (allow_none && (o == Py_None)) {
    return nullptr;
  }
  if (PythonClassSceneCollisionMesh::Check(o)) {
    // This will succeed or throw its own Exception.
    return reinterpret_cast<PythonClassSceneCollisionMesh*>(o)
        ->GetCollisionMesh(!allow_empty_ref);
  }

  // Nothing here should have led to an unresolved Python error state.
  assert(!PyErr_Occurred());

  throw Exception("Can't get bascenev1.CollisionMesh from value: "
                      + Python::ObjToString(o) + ".",
                  PyExcType::kType);
}

auto SceneV1Python::GetPySceneCollisionMeshes(PyObject* o)
    -> std::vector<SceneCollisionMesh*> {
  assert(Python::HaveGIL());
  BA_PRECONDITION_FATAL(o != nullptr);

  if (!PySequence_Check(o)) {
    throw Exception("Object is not a sequence.", PyExcType::kType);
  }
  PythonRef sequence(PySequence_Fast(o, "Not a sequence."), PythonRef::kSteal);
  assert(sequence.exists());
  auto size = static_cast<size_t>(PySequence_Fast_GET_SIZE(sequence.get()));
  PyObject** pyobjs = PySequence_Fast_ITEMS(sequence.get());
  std::vector<SceneCollisionMesh*> vals(size);
  assert(vals.size() == size);
  for (size_t i = 0; i < size; i++) {
    vals[i] = GetPySceneCollisionMesh(pyobjs[i]);  // DON'T allow nullptr refs.
  }
  return vals;
}

auto SceneV1Python::IsPySession(PyObject* o) -> bool {
  assert(Python::HaveGIL());
  BA_PRECONDITION_FATAL(o != nullptr);

  int result = PyObject_IsInstance(
      o, g_scene_v1->python->objs()
             .Get(SceneV1Python::ObjID::kSceneV1SessionClass)
             .get());
  if (result == -1) {
    PyErr_Clear();
    result = 0;
  }
  return static_cast<bool>(result);
}

auto SceneV1Python::GetPySession(PyObject* o) -> Session* {
  assert(Python::HaveGIL());
  BA_PRECONDITION_FATAL(o != nullptr);

  PyExcType pyexctype{PyExcType::kType};
  if (IsPySession(o)) {
    // Look for an _sessiondata attr on it.
    if (PyObject* sessiondata = PyObject_GetAttrString(o, "_sessiondata")) {
      // This will deallocate for us.
      PythonRef ref(sessiondata, PythonRef::kSteal);
      if (PythonClassSessionData::Check(sessiondata)) {
        // This will succeed or throw its own Exception.
        return (reinterpret_cast<PythonClassSessionData*>(sessiondata))
            ->GetSession();
      }
    } else {
      pyexctype = PyExcType::kRuntime;  // Wonky session obj.
    }
  }

  // Failed, we have.
  // Clear any Python error that got us here; we're in C++ Exception land now.
  PyErr_Clear();
  throw Exception(
      "Can't get Session from value: " + Python::ObjToString(o) + ".",
      pyexctype);
}

auto SceneV1Python::GetPySessionPlayer(PyObject* o, bool allow_empty_ref,
                                       bool allow_none) -> Player* {
  assert(Python::HaveGIL());
  BA_PRECONDITION_FATAL(o != nullptr);

  if (allow_none && (o == Py_None)) {
    return nullptr;
  }
  if (PythonClassSessionPlayer::Check(o)) {
    // This will succeed or throw its own Exception.
    return reinterpret_cast<PythonClassSessionPlayer*>(o)->GetPlayer(
        !allow_empty_ref);
  }

  // Nothing here should have led to an unresolved Python error state.
  assert(!PyErr_Occurred());

  throw Exception("Can't get bascenev1.SessionPlayer from value: "
                      + Python::ObjToString(o) + ".",
                  PyExcType::kType);
}

auto SceneV1Python::GetPySceneDataAsset(PyObject* o, bool allow_empty_ref,
                                        bool allow_none) -> SceneDataAsset* {
  assert(Python::HaveGIL());
  BA_PRECONDITION_FATAL(o != nullptr);

  if (allow_none && (o == Py_None)) {
    return nullptr;
  }
  if (PythonClassSceneDataAsset::Check(o)) {
    // This will succeed or throw its own Exception.
    return reinterpret_cast<PythonClassSceneDataAsset*>(o)->GetData(
        !allow_empty_ref);
  }

  // Nothing here should have led to an unresolved Python error state.
  assert(!PyErr_Occurred());

  throw Exception(
      "Can't get bascenev1.Data from value: " + Python::ObjToString(o) + ".",
      PyExcType::kType);
}

auto SceneV1Python::FilterChatMessage(std::string* message, int client_id)
    -> bool {
  assert(message);
  base::ScopedSetContext ssc(nullptr);

  // This string data can be coming straight in off the network; need
  // to avoid letting malicious garbage through to Python api.
  if (!Utils::IsValidUTF8(*message)) {
    BA_LOG_ONCE(LogName::kBa, LogLevel::kWarning,
                "FilterChatMessage got invalid UTF8 data; could be an attack.");
    return false;
  }

  PythonRef args(Py_BuildValue("(si)", message->c_str(), client_id),
                 PythonRef::kSteal);
  PythonRef result = objs().Get(ObjID::kFilterChatMessageCall).Call(args);

  // If something went wrong, just allow all messages through verbatim.
  if (!result.exists()) {
    return true;
  }

  // If they returned None, they want to ignore the message.
  if (result.get() == Py_None) {
    return false;
  }

  // Replace the message string with whatever they gave us.
  try {
    *message = g_base->python->GetPyLString(result.get());
  } catch (const std::exception& e) {
    g_core->logging->Log(
        LogName::kBa, LogLevel::kError,
        "Error getting string from chat filter: " + std::string(e.what()));
  }
  return true;
}

void SceneV1Python::HandleLocalChatMessage(const std::string& message) {
  base::ScopedSetContext ssc(nullptr);
  PythonRef args(Py_BuildValue("(s)", message.c_str()), PythonRef::kSteal);
  objs().Get(ObjID::kHandleLocalChatMessageCall).Call(args);
}

// Put together a node message with all args on the provided tuple (starting
// with arg_offset) returns false on failure, true on success.
void SceneV1Python::DoBuildNodeMessage(PyObject* args, int arg_offset,
                                       std::vector<char>* b,
                                       PyObject** user_message_obj) {
  Py_ssize_t tuple_size = PyTuple_GET_SIZE(args);
  if (tuple_size - arg_offset < 1) {
    throw Exception("Got message of size zero.", PyExcType::kValue);
  }
  std::string type;
  PyObject* obj;

  // Pull first arg.
  obj = PyTuple_GET_ITEM(args, arg_offset);
  BA_PRECONDITION(obj);
  if (!PyUnicode_Check(obj)) {
    // If first arg is not a string, its an actual message itself.
    (*user_message_obj) = obj;
    return;
  } else {
    (*user_message_obj) = nullptr;
  }
  type = Python::GetString(obj);
  NodeMessageType ac = Scene::GetNodeMessageType(type);
  const char* format = Scene::GetNodeMessageFormat(ac);
  assert(format);
  const char* f = format;

  // Allow space for 1 type byte (fixme - may need more than 1).
  size_t full_size = 1;
  for (Py_ssize_t i = arg_offset + 1; i < tuple_size; i++) {
    // Make sure our format string ends the same time as our arg count.
    if (*f == 0) {
      throw Exception(
          "Wrong number of arguments on node message '" + type + "'.",
          PyExcType::kValue);
    }
    obj = PyTuple_GET_ITEM(args, i);
    BA_PRECONDITION(obj);
    switch (*f) {
      case 'I':

        // 4 byte int
        if (!PyNumber_Check(obj)) {
          throw Exception("Expected an int for node message arg "
                              + std::to_string(i - (arg_offset + 1)) + ".",
                          PyExcType::kType);
        }
        full_size += 4;
        break;
      case 'i':

        // 2 byte int.
        if (!PyNumber_Check(obj)) {
          throw Exception("Expected an int for node message arg "
                              + std::to_string(i - (arg_offset + 1)) + ".",
                          PyExcType::kType);
        }
        full_size += 2;
        break;
      case 'c':  // NOLINT(bugprone-branch-clone)

        // 1 byte int.
        if (!PyNumber_Check(obj)) {
          throw Exception("Expected an int for node message arg "
                              + std::to_string(i - (arg_offset + 1)) + ".",
                          PyExcType::kType);
        }
        full_size += 1;
        break;
      case 'b':

        // bool (currently 1 byte int).
        if (!PyNumber_Check(obj)) {
          throw Exception("Expected an int for node message arg "
                              + std::to_string(i - (arg_offset + 1)) + ".",
                          PyExcType::kType);
        }
        full_size += 1;
        break;
      case 'F':

        // 32 bit float.
        if (!PyNumber_Check(obj)) {
          throw Exception("Expected a float for node message arg "
                              + std::to_string(i - (arg_offset + 1)) + ".",
                          PyExcType::kType);
        }
        full_size += 4;
        break;
      case 'f':

        // 16 bit float.
        if (!PyNumber_Check(obj)) {
          throw Exception("Expected a float for node message arg "
                              + std::to_string(i - (arg_offset + 1)) + ".",
                          PyExcType::kType);
        }
        full_size += 2;
        break;
      case 's':
        if (!PyUnicode_Check(obj)) {
          throw Exception("Expected a string for node message arg "
                              + std::to_string(i - (arg_offset + 1)) + ".",
                          PyExcType::kType);
        }
        full_size += strlen(PyUnicode_AsUTF8(obj)) + 1;
        break;
      default:
        throw Exception("Invalid argument type: " + std::to_string(*f) + ".",
                        PyExcType::kValue);
        break;
    }
    f++;
  }

  // Make sure our format string ends the same time as our arg count.
  if (*f != 0) {
    throw Exception("Wrong number of arguments on node message '" + type + "'.",
                    PyExcType::kValue);
  }
  b->resize(full_size);
  char* ptr = b->data();
  *ptr = static_cast<char>(ac);
  ptr++;
  f = format;
  for (Py_ssize_t i = arg_offset + 1; i < tuple_size; i++) {
    obj = PyTuple_GET_ITEM(args, i);
    BA_PRECONDITION(obj);
    switch (*f) {
      case 'I':
        Utils::EmbedInt32NBO(
            &ptr, static_cast_check_fit<int32_t>(Python::GetInt64(obj)));
        break;
      case 'i':
        Utils::EmbedInt16NBO(
            &ptr, static_cast_check_fit<int16_t>(Python::GetInt64(obj)));
        break;
      case 'c':  // NOLINT(bugprone-branch-clone)
        Utils::EmbedInt8(&ptr,
                         static_cast_check_fit<int8_t>(Python::GetInt64(obj)));
        break;
      case 'b':
        Utils::EmbedInt8(&ptr,
                         static_cast_check_fit<int8_t>(Python::GetInt64(obj)));
        break;
      case 'F':
        Utils::EmbedFloat32(&ptr, Python::GetFloat(obj));
        break;
      case 'f':
        Utils::EmbedFloat16NBO(&ptr, Python::GetFloat(obj));
        break;
      case 's':
        Utils::EmbedString(&ptr, PyUnicode_AsUTF8(obj));
        break;
      default:
        throw Exception(PyExcType::kValue);
        break;
    }
    f++;
  }
}

auto SceneV1Python::GetPyInputDevice(PyObject* o)
    -> SceneV1InputDeviceDelegate* {
  assert(Python::HaveGIL());
  BA_PRECONDITION_FATAL(o != nullptr);

  if (PythonClassInputDevice::Check(o)) {
    // This will succeed or throw its own Exception.
    return reinterpret_cast<PythonClassInputDevice*>(o)->GetInputDevice();
  }

  // Nothing here should have led to an unresolved Python error state.
  assert(!PyErr_Occurred());

  throw Exception(
      "Can't get input-device from value: " + Python::ObjToString(o) + ".",
      PyExcType::kType);
}

void SceneV1Python::CaptureJoystickInput(PyObject* obj) {
  assert(g_base->InLogicThread());
  ReleaseJoystickInputCapture();
  if (PyCallable_Check(obj)) {
    joystick_capture_call_.Acquire(obj);
    g_base->input->CaptureJoystickInput(HandleCapturedJoystickEventCall);
  } else {
    throw Exception("Object is not callable.", PyExcType::kType);
  }
}

void SceneV1Python::ReleaseJoystickInputCapture() {
  joystick_capture_call_.Release();
  g_base->input->ReleaseJoystickInput();
}

void SceneV1Python::CaptureKeyboardInput(PyObject* obj) {
  assert(g_base->InLogicThread());
  ReleaseKeyboardInputCapture();
  if (PyCallable_Check(obj)) {
    keyboard_capture_call_.Acquire(obj);
    g_base->input->CaptureKeyboardInput(HandleCapturedKeyPressCall,
                                        HandleCapturedKeyReleaseCall);
  } else {
    throw Exception("Object is not callable.", PyExcType::kType);
  }
}
void SceneV1Python::ReleaseKeyboardInputCapture() {
  keyboard_capture_call_.Release();
  g_base->input->ReleaseKeyboardInput();
}

auto SceneV1Python::HandleCapturedJoystickEventCall(
    const SDL_Event& event, base::InputDevice* input_device) -> bool {
  return g_scene_v1->python->HandleCapturedJoystickEvent(event, input_device);
}

auto SceneV1Python::HandleCapturedKeyPressCall(const SDL_Keysym& keysym)
    -> bool {
  return g_scene_v1->python->HandleCapturedKeyPress(keysym);
}

auto SceneV1Python::HandleCapturedKeyReleaseCall(const SDL_Keysym& keysym)
    -> bool {
  return g_scene_v1->python->HandleCapturedKeyRelease(keysym);
}

auto SceneV1Python::HandleCapturedKeyPress(const SDL_Keysym& keysym) -> bool {
  assert(g_base->InLogicThread());
  if (!keyboard_capture_call_.exists()) {
    return false;
  }
  base::ScopedSetContext ssc(nullptr);
  auto* keyboard = g_base->input->keyboard_input();
  BA_PRECONDITION(keyboard);

  // This currently only works with the scene_v1 input-device classes.
  if (auto* delegate =
          dynamic_cast<SceneV1InputDeviceDelegate*>(&keyboard->delegate())) {
    PythonRef args(
        Py_BuildValue("({s:s,s:i,s:O})", "type", "BUTTONDOWN", "button",
                      static_cast<int>(keysym.sym), "input_device",
                      keyboard ? delegate->BorrowPyRef() : Py_None),
        PythonRef::kSteal);
    keyboard_capture_call_.Call(args);
  } else {
    BA_LOG_ONCE(
        LogName::kBa, LogLevel::kWarning,
        "Python key-press callbacks do not work with this input-device class.");
  }
  return true;
}
auto SceneV1Python::HandleCapturedKeyRelease(const SDL_Keysym& keysym) -> bool {
  assert(g_base->InLogicThread());
  if (!keyboard_capture_call_.exists()) {
    return false;
  }
  base::ScopedSetContext ssc(nullptr);
  auto* keyboard = g_base->input->keyboard_input();
  BA_PRECONDITION(keyboard);

  // This currently only works with the scene_v1 input-device classes.
  if (auto* delegate =
          dynamic_cast<SceneV1InputDeviceDelegate*>(&keyboard->delegate())) {
    PythonRef args(
        Py_BuildValue("({s:s,s:i,s:O})", "type", "BUTTONUP", "button",
                      static_cast<int>(keysym.sym), "input_device",
                      keyboard ? delegate->BorrowPyRef() : Py_None),
        PythonRef::kSteal);
    keyboard_capture_call_.Call(args);
  } else {
    BA_LOG_ONCE(
        LogName::kBa, LogLevel::kWarning,
        "Python key-press callbacks do not work with this input-device class.");
  }
  return true;
}

auto SceneV1Python::HandleCapturedJoystickEvent(const SDL_Event& event,
                                                base::InputDevice* input_device)
    -> bool {
  assert(g_base->InLogicThread());
  assert(input_device != nullptr);
  if (!joystick_capture_call_.exists()) {
    return false;
  }
  // This currently only works with the scene_v1 input-device classes.
  if (auto* delegate = dynamic_cast<SceneV1InputDeviceDelegate*>(
          &input_device->delegate())) {
    base::ScopedSetContext ssc(nullptr);
    // If we got a device we can pass events.
    if (input_device) {
      switch (event.type) {
        case SDL_JOYBUTTONDOWN: {
          PythonRef args(
              Py_BuildValue("({s:s,s:i,s:O})", "type", "BUTTONDOWN", "button",
                            static_cast<int>(event.jbutton.button)
                                + 1,  // give them base-1
                            "input_device", delegate->BorrowPyRef()),
              PythonRef::kSteal);
          joystick_capture_call_.Call(args);
          break;
        }
        case SDL_JOYBUTTONUP: {
          PythonRef args(
              Py_BuildValue("({s:s,s:i,s:O})", "type", "BUTTONUP", "button",
                            static_cast<int>(event.jbutton.button)
                                + 1,  // give them base-1
                            "input_device", delegate->BorrowPyRef()),
              PythonRef::kSteal);
          joystick_capture_call_.Call(args);
          break;
        }
        case SDL_JOYHATMOTION: {
          PythonRef args(
              Py_BuildValue(
                  "({s:s,s:i,s:i,s:O})", "type", "HATMOTION", "hat",
                  static_cast<int>(event.jhat.hat) + 1,  // give them base-1
                  "value", event.jhat.value, "input_device",
                  delegate->BorrowPyRef()),
              PythonRef::kSteal);
          joystick_capture_call_.Call(args);
          break;
        }
        case SDL_JOYAXISMOTION: {
          PythonRef args(
              Py_BuildValue(
                  "({s:s,s:i,s:f,s:O})", "type", "AXISMOTION", "axis",
                  static_cast<int>(event.jaxis.axis) + 1,  // give them base-1
                  "value",
                  std::min(1.0f,
                           std::max(-1.0f, static_cast<float>(event.jaxis.value)
                                               / 32767.0f)),
                  "input_device", delegate->BorrowPyRef()),
              PythonRef::kSteal);
          joystick_capture_call_.Call(args);
          break;
        }
        default:
          break;
      }
    }
  } else {
    BA_LOG_ONCE(
        LogName::kBa, LogLevel::kWarning,
        "Python key-press callbacks do not work with this input-device class.");
  }
  return true;
}

}  // namespace ballistica::scene_v1
