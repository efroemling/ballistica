// Released under the MIT License. See LICENSE for details.

#include "ballistica/ui_v1/python/class/python_class_ui_mesh.h"

#include <string>

#include "ballistica/base/assets/mesh_asset.h"
#include "ballistica/base/logic/logic.h"
#include "ballistica/shared/foundation/event_loop.h"
#include "ballistica/ui_v1/ui_v1.h"

namespace ballistica::ui_v1 {

auto PythonClassUIMesh::type_name() -> const char* { return "Mesh"; }

void PythonClassUIMesh::SetupType(PyTypeObject* cls) {
  PythonClass::SetupType(cls);
  // Fully qualified type path we will be exposed as:
  cls->tp_name = "babase.Mesh";
  cls->tp_basicsize = sizeof(PythonClassUIMesh);
  cls->tp_doc = "Mesh asset for local user interface purposes.";
  cls->tp_new = tp_new;
  cls->tp_dealloc = (destructor)tp_dealloc;
  cls->tp_repr = (reprfunc)tp_repr;
  cls->tp_methods = tp_methods;
}

auto PythonClassUIMesh::Create(const Object::Ref<base::MeshAsset>& mesh)
    -> PyObject* {
  assert(TypeIsSetUp(&type_obj));
  auto* py_mesh = reinterpret_cast<PythonClassUIMesh*>(
      PyObject_CallObject(reinterpret_cast<PyObject*>(&type_obj), nullptr));
  if (!py_mesh) {
    throw Exception("Mesh creation failed");
  }

  *py_mesh->mesh_ = mesh;
  return reinterpret_cast<PyObject*>(py_mesh);
}

auto PythonClassUIMesh::tp_repr(PythonClassUIMesh* self) -> PyObject* {
  BA_PYTHON_TRY;
  base::MeshAsset* s = self->mesh_->get();
  return Py_BuildValue(
      "s", (std::string("<bauiv1.Mesh '") + (s->GetName()) + "'>").c_str());
  BA_PYTHON_CATCH;
}

auto PythonClassUIMesh::tp_new(PyTypeObject* type, PyObject* args,
                               PyObject* keywds) -> PyObject* {
  auto* self = reinterpret_cast<PythonClassUIMesh*>(type->tp_alloc(type, 0));
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
  self->mesh_ = new Object::Ref<base::MeshAsset>();
  return reinterpret_cast<PyObject*>(self);
  BA_PYTHON_NEW_CATCH;
}

void PythonClassUIMesh::tp_dealloc(PythonClassUIMesh* self) {
  BA_PYTHON_TRY;
  // Our Object::Ref needs to be cleared in the logic thread.
  auto* ptr = self->mesh_;
  if (g_base->InLogicThread()) {
    delete ptr;
  } else {
    g_base->logic->event_loop()->PushCall([ptr] { delete ptr; });
  }
  BA_PYTHON_DEALLOC_CATCH;
  Py_TYPE(self)->tp_free(reinterpret_cast<PyObject*>(self));
}

PyTypeObject PythonClassUIMesh::type_obj;
PyMethodDef PythonClassUIMesh::tp_methods[] = {{nullptr}};

}  // namespace ballistica::ui_v1
