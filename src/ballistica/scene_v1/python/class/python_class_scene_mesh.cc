// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/python/class/python_class_scene_mesh.h"

#include <string>

#include "ballistica/base/logic/logic.h"
#include "ballistica/scene_v1/assets/scene_mesh.h"
#include "ballistica/shared/foundation/event_loop.h"

namespace ballistica::scene_v1 {

auto PythonClassSceneMesh::tp_repr(PythonClassSceneMesh* self) -> PyObject* {
  BA_PYTHON_TRY;
  auto&& m = *(self->mesh_);
  return Py_BuildValue(
      "s", (std::string("<_bascenev1.Mesh ")
            + (m.exists() ? ("\"" + m->name() + "\"") : "(empty ref)") + ">")
               .c_str());
  BA_PYTHON_CATCH;
}

auto PythonClassSceneMesh::type_name() -> const char* { return "Mesh"; }

void PythonClassSceneMesh::SetupType(PyTypeObject* cls) {
  PythonClass::SetupType(cls);
  // Fully qualified type path we will be exposed as:
  cls->tp_name = "_bascenev1.Mesh";
  cls->tp_basicsize = sizeof(PythonClassSceneMesh);
  cls->tp_doc =
      "A reference to a mesh.\n"
      "\n"
      "Meshes are used for drawing.\n"
      "Use :meth:`bascenev1.getmesh()` to instantiate one.";
  cls->tp_repr = (reprfunc)tp_repr;
  cls->tp_new = tp_new;
  cls->tp_dealloc = (destructor)tp_dealloc;
}

auto PythonClassSceneMesh::Create(SceneMesh* mesh) -> PyObject* {
  s_create_empty_ = true;  // prevent class from erroring on create
  assert(TypeIsSetUp(&type_obj));
  auto* t = reinterpret_cast<PythonClassSceneMesh*>(
      PyObject_CallObject(reinterpret_cast<PyObject*>(&type_obj), nullptr));
  s_create_empty_ = false;
  if (!t) {
    throw Exception("bascenev1.Mesh creation failed.");
  }
  *t->mesh_ = mesh;
  return reinterpret_cast<PyObject*>(t);
}

auto PythonClassSceneMesh::GetMesh(bool doraise) const -> SceneMesh* {
  SceneMesh* mesh = mesh_->get();
  if (!mesh && doraise) {
    throw Exception("Invalid mesh.", PyExcType::kNotFound);
  }
  return mesh;
}

// Clion makes some incorrect inferences here.
#pragma clang diagnostic push
#pragma ide diagnostic ignored "UnreachableCode"
#pragma ide diagnostic ignored "ConstantConditionsOC"
#pragma ide diagnostic ignored "ConstantFunctionResult"

auto PythonClassSceneMesh::tp_new(PyTypeObject* type, PyObject* args,
                                  PyObject* kwds) -> PyObject* {
  auto* self = reinterpret_cast<PythonClassSceneMesh*>(type->tp_alloc(type, 0));
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
  if (!s_create_empty_) {
    throw Exception(
        "Can't instantiate Meshes directly; use bascenev1.getmesh() to get "
        "them.");
  }
  self->mesh_ = new Object::Ref<SceneMesh>();
  return reinterpret_cast<PyObject*>(self);
  BA_PYTHON_NEW_CATCH;
}

#pragma clang diagnostic pop

void PythonClassSceneMesh::tp_dealloc(PythonClassSceneMesh* self) {
  BA_PYTHON_TRY;
  // Our Object::Ref needs to be released in the logic thread.
  auto* ptr = self->mesh_;
  if (g_base->InLogicThread()) {
    delete ptr;
  } else {
    g_base->logic->event_loop()->PushCall([ptr] { delete ptr; });
  }
  BA_PYTHON_DEALLOC_CATCH;
  Py_TYPE(self)->tp_free(reinterpret_cast<PyObject*>(self));
}

bool PythonClassSceneMesh::s_create_empty_ = false;
PyTypeObject PythonClassSceneMesh::type_obj;

}  // namespace ballistica::scene_v1
