// Released under the MIT License. See LICENSE for details.

#include "ballistica/python/class/python_class_model.h"

#include "ballistica/assets/component/model.h"
#include "ballistica/core/thread.h"
#include "ballistica/logic/logic.h"
#include "ballistica/python/python.h"

namespace ballistica {

auto PythonClassModel::tp_repr(PythonClassModel* self) -> PyObject* {
  BA_PYTHON_TRY;
  Object::Ref<Model> m = *(self->model_);
  return Py_BuildValue(
      "s", (std::string("<ba.Model ")
            + (m.exists() ? ("\"" + m->name() + "\"") : "(empty ref)") + ">")
               .c_str());
  BA_PYTHON_CATCH;
}

void PythonClassModel::SetupType(PyTypeObject* obj) {
  PythonClass::SetupType(obj);
  obj->tp_name = "ba.Model";
  obj->tp_basicsize = sizeof(PythonClassModel);
  obj->tp_doc =
      "A reference to a model.\n"
      "\n"
      "Category: **Asset Classes**\n"
      "\n"
      "Models are used for drawing.\n"
      "Use ba.getmodel() to instantiate one.";
  obj->tp_repr = (reprfunc)tp_repr;
  obj->tp_new = tp_new;
  obj->tp_dealloc = (destructor)tp_dealloc;
}

auto PythonClassModel::Create(Model* model) -> PyObject* {
  s_create_empty_ = true;  // prevent class from erroring on create
  auto* t = reinterpret_cast<PythonClassModel*>(
      PyObject_CallObject(reinterpret_cast<PyObject*>(&type_obj), nullptr));
  s_create_empty_ = false;
  if (!t) {
    throw Exception("ba.Model creation failed.");
  }
  *(t->model_) = model;
  return reinterpret_cast<PyObject*>(t);
}

auto PythonClassModel::GetModel(bool doraise) const -> Model* {
  Model* model = model_->get();
  if (!model && doraise) {
    throw Exception("Invalid Model.", PyExcType::kNotFound);
  }
  return model;
}

// Clion makes some incorrect inferences here.
#pragma clang diagnostic push
#pragma ide diagnostic ignored "UnreachableCode"
#pragma ide diagnostic ignored "ConstantConditionsOC"
#pragma ide diagnostic ignored "ConstantFunctionResult"

auto PythonClassModel::tp_new(PyTypeObject* type, PyObject* args,
                              PyObject* kwds) -> PyObject* {
  auto* self = reinterpret_cast<PythonClassModel*>(type->tp_alloc(type, 0));
  if (self) {
    BA_PYTHON_TRY;
    if (!InLogicThread()) {
      throw Exception(
          "ERROR: " + std::string(type_obj.tp_name)
          + " objects must only be created in the logic thread (current is ("
          + GetCurrentThreadName() + ").");
    }
    if (!s_create_empty_) {
      throw Exception(
          "Can't instantiate Models directly; use ba.getmodel() to get "
          "them.");
    }
    self->model_ = new Object::Ref<Model>();
    BA_PYTHON_NEW_CATCH;
  }
  return reinterpret_cast<PyObject*>(self);
}

#pragma clang diagnostic pop

void PythonClassModel::Delete(Object::Ref<Model>* ref) {
  assert(InLogicThread());

  // if we're the py-object for a model, clear them out
  // (FIXME - we should pass the old pointer in here to sanity-test that we
  // were their ref)
  if (ref->exists()) {
    (*ref)->ClearPyObject();
  }
  delete ref;
}

void PythonClassModel::tp_dealloc(PythonClassModel* self) {
  BA_PYTHON_TRY;
  // these have to be deleted in the logic thread - send the ptr along if need
  // be; otherwise do it immediately
  if (!InLogicThread()) {
    Object::Ref<Model>* m = self->model_;
    g_logic->thread()->PushCall([m] { Delete(m); });
  } else {
    Delete(self->model_);
  }
  BA_PYTHON_DEALLOC_CATCH;
  Py_TYPE(self)->tp_free(reinterpret_cast<PyObject*>(self));
}

bool PythonClassModel::s_create_empty_ = false;
PyTypeObject PythonClassModel::type_obj;

}  // namespace ballistica
