// Released under the MIT License. See LICENSE for details.

#include "ballistica/python/class/python_class_collide_model.h"

#include "ballistica/game/game.h"
#include "ballistica/media/component/collide_model.h"

namespace ballistica {

auto PythonClassCollideModel::tp_repr(PythonClassCollideModel* self)
    -> PyObject* {
  BA_PYTHON_TRY;
  Object::Ref<CollideModel> m = *(self->collide_model_);
  return Py_BuildValue(
      "s", (std::string("<ba.CollideModel ")
            + (m.exists() ? ("\"" + m->name() + "\"") : "(empty ref)") + ">")
               .c_str());
  BA_PYTHON_CATCH;
}

void PythonClassCollideModel::SetupType(PyTypeObject* obj) {
  PythonClass::SetupType(obj);
  obj->tp_name = "ba.CollideModel";
  obj->tp_basicsize = sizeof(PythonClassCollideModel);
  obj->tp_doc =
      "A reference to a collide-model.\n"
      "\n"
      "Category: **Asset Classes**\n"
      "\n"
      "Use ba.getcollidemodel() to instantiate one.";
  obj->tp_repr = (reprfunc)tp_repr;
  obj->tp_new = tp_new;
  obj->tp_dealloc = (destructor)tp_dealloc;
}

auto PythonClassCollideModel::Create(CollideModel* collide_model) -> PyObject* {
  s_create_empty_ = true;  // prevent class from erroring on create
  auto* t = reinterpret_cast<PythonClassCollideModel*>(
      PyObject_CallObject(reinterpret_cast<PyObject*>(&type_obj), nullptr));
  s_create_empty_ = false;
  if (!t) {
    throw Exception("ba.CollideModel creation failed.");
  }
  *(t->collide_model_) = collide_model;
  return reinterpret_cast<PyObject*>(t);
}

auto PythonClassCollideModel::GetCollideModel(bool doraise) const
    -> CollideModel* {
  CollideModel* collide_model = collide_model_->get();
  if (!collide_model && doraise) {
    throw Exception("Invalid CollideModel.", PyExcType::kNotFound);
  }
  return collide_model;
}

// Clion makes some incorrect inferences here.
#pragma clang diagnostic push
#pragma ide diagnostic ignored "UnreachableCode"
#pragma ide diagnostic ignored "ConstantConditionsOC"
#pragma ide diagnostic ignored "ConstantFunctionResult"

auto PythonClassCollideModel::tp_new(PyTypeObject* type, PyObject* args,
                                     PyObject* kwds) -> PyObject* {
  auto* self =
      reinterpret_cast<PythonClassCollideModel*>(type->tp_alloc(type, 0));
  if (self) {
    BA_PYTHON_TRY;
    if (!InGameThread()) {
      throw Exception(
          "ERROR: " + std::string(type_obj.tp_name)
          + " objects must only be created in the game thread (current is ("
          + GetCurrentThreadName() + ").");
    }

    if (!s_create_empty_) {
      throw Exception(
          "Can't instantiate CollideModels directly; use "
          "ba.getcollidemodel() to get them.");
    }
    self->collide_model_ = new Object::Ref<CollideModel>();
    BA_PYTHON_NEW_CATCH;
  }
  return reinterpret_cast<PyObject*>(self);
}

#pragma clang diagnostic pop

void PythonClassCollideModel::Delete(Object::Ref<CollideModel>* ref) {
  assert(InGameThread());
  // if we're the py-object for a collide_model, clear them out
  // (FIXME - we should pass the old pointer in here to sanity-test that we
  //   were their ref)
  if (ref->exists()) {
    (*ref)->ClearPyObject();
  }
  delete ref;
}

void PythonClassCollideModel::tp_dealloc(PythonClassCollideModel* self) {
  BA_PYTHON_TRY;
  // these have to be deleted in the game thread - send the ptr along if need
  // be; otherwise do it immediately
  if (!InGameThread()) {
    Object::Ref<CollideModel>* c = self->collide_model_;
    g_game->PushCall([c] { Delete(c); });
  } else {
    Delete(self->collide_model_);
  }
  BA_PYTHON_DEALLOC_CATCH;
  Py_TYPE(self)->tp_free(reinterpret_cast<PyObject*>(self));
}

bool PythonClassCollideModel::s_create_empty_ = false;
PyTypeObject PythonClassCollideModel::type_obj;

}  // namespace ballistica
