// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/python/class/python_class_scene_collision_mesh.h"

#include <string>

#include "ballistica/base/logic/logic.h"
#include "ballistica/scene_v1/assets/scene_collision_mesh.h"
#include "ballistica/shared/foundation/event_loop.h"

namespace ballistica::scene_v1 {

auto PythonClassSceneCollisionMesh::tp_repr(PythonClassSceneCollisionMesh* self)
    -> PyObject* {
  BA_PYTHON_TRY;
  assert(self->collision_mesh_);
  auto&& m = *self->collision_mesh_;
  return Py_BuildValue(
      "s", (std::string("<bascenev1.CollisionMesh ")
            + (m.exists() ? ("\"" + m->name() + "\"") : "(empty ref)") + ">")
               .c_str());
  BA_PYTHON_CATCH;
}

auto PythonClassSceneCollisionMesh::type_name() -> const char* {
  return "CollisionMesh";
}

void PythonClassSceneCollisionMesh::SetupType(PyTypeObject* cls) {
  PythonClass::SetupType(cls);
  // Fully qualified type path we will be exposed as:
  cls->tp_name = "bascenev1.CollisionMesh";
  cls->tp_basicsize = sizeof(PythonClassSceneCollisionMesh);
  cls->tp_doc =
      "A reference to a collision-mesh.\n"
      "\n"
      "Use :meth:`bascenev1.getcollisionmesh()` to instantiate one.";
  cls->tp_repr = (reprfunc)tp_repr;
  cls->tp_new = tp_new;
  cls->tp_dealloc = (destructor)tp_dealloc;
}

auto PythonClassSceneCollisionMesh::Create(SceneCollisionMesh* collision_mesh)
    -> PyObject* {
  s_create_empty_ = true;  // prevent class from erroring on create
  assert(TypeIsSetUp(&type_obj));
  auto* t = reinterpret_cast<PythonClassSceneCollisionMesh*>(
      PyObject_CallObject(reinterpret_cast<PyObject*>(&type_obj), nullptr));
  s_create_empty_ = false;
  if (!t) {
    throw Exception("babase.CollisionMesh creation failed.");
  }
  *t->collision_mesh_ = collision_mesh;
  return reinterpret_cast<PyObject*>(t);
}

auto PythonClassSceneCollisionMesh::GetCollisionMesh(bool doraise) const
    -> SceneCollisionMesh* {
  SceneCollisionMesh* collision_mesh = collision_mesh_->get();
  if (!collision_mesh && doraise) {
    throw Exception("Invalid CollisionMesh.", PyExcType::kNotFound);
  }
  return collision_mesh;
}

// Clion makes some incorrect inferences here.
#pragma clang diagnostic push
#pragma ide diagnostic ignored "UnreachableCode"
#pragma ide diagnostic ignored "ConstantConditionsOC"
#pragma ide diagnostic ignored "ConstantFunctionResult"

auto PythonClassSceneCollisionMesh::tp_new(PyTypeObject* type, PyObject* args,
                                           PyObject* kwds) -> PyObject* {
  auto* self =
      reinterpret_cast<PythonClassSceneCollisionMesh*>(type->tp_alloc(type, 0));
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
        "Can't instantiate CollisionMeshes directly; use "
        "babase.getcollisionmesh() to get them.");
  }
  self->collision_mesh_ = new Object::Ref<SceneCollisionMesh>();
  return reinterpret_cast<PyObject*>(self);
  BA_PYTHON_NEW_CATCH;
}

#pragma clang diagnostic pop

void PythonClassSceneCollisionMesh::tp_dealloc(
    PythonClassSceneCollisionMesh* self) {
  BA_PYTHON_TRY;
  // Our Object::Ref needs to be released in the logic thread.
  auto* ptr = self->collision_mesh_;
  if (g_base->InLogicThread()) {
    delete ptr;
  } else {
    g_base->logic->event_loop()->PushCall([ptr] { delete ptr; });
  }
  BA_PYTHON_DEALLOC_CATCH;
  Py_TYPE(self)->tp_free(reinterpret_cast<PyObject*>(self));
}

bool PythonClassSceneCollisionMesh::s_create_empty_ = false;
PyTypeObject PythonClassSceneCollisionMesh::type_obj;

}  // namespace ballistica::scene_v1
