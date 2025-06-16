// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/python/class/python_class_scene_data_asset.h"

#include <string>

#include "ballistica/base/logic/logic.h"
#include "ballistica/scene_v1/assets/scene_data_asset.h"
#include "ballistica/shared/foundation/event_loop.h"

namespace ballistica::scene_v1 {

auto PythonClassSceneDataAsset::tp_repr(PythonClassSceneDataAsset* self)
    -> PyObject* {
  BA_PYTHON_TRY;
  auto&& m = *self->data_;
  return Py_BuildValue(
      "s", (std::string("<ba.Data ")
            + (m.exists() ? ("\"" + m->name() + "\"") : "(empty ref)") + ">")
               .c_str());
  BA_PYTHON_CATCH;
}

auto PythonClassSceneDataAsset::type_name() -> const char* { return "Data"; }

void PythonClassSceneDataAsset::SetupType(PyTypeObject* cls) {
  PythonClass::SetupType(cls);
  // Fully qualified type path we will be exposed as:
  cls->tp_name = "bascenev1.Data";
  cls->tp_basicsize = sizeof(PythonClassSceneDataAsset);
  cls->tp_doc =
      "A reference to a data object.\n"
      "\n"
      "Use :meth:`bascenev1.getdata()` to instantiate one.";
  cls->tp_repr = (reprfunc)tp_repr;
  cls->tp_new = tp_new;
  cls->tp_dealloc = (destructor)tp_dealloc;
  cls->tp_methods = tp_methods;
}

auto PythonClassSceneDataAsset::Create(SceneDataAsset* data) -> PyObject* {
  s_create_empty_ = true;  // prevent class from erroring on create
  assert(TypeIsSetUp(&type_obj));
  auto* t = reinterpret_cast<PythonClassSceneDataAsset*>(
      PyObject_CallObject(reinterpret_cast<PyObject*>(&type_obj), nullptr));
  s_create_empty_ = false;
  if (!t) {
    throw Exception("babase.Data creation failed.");
  }
  *t->data_ = data;
  return reinterpret_cast<PyObject*>(t);
}

auto PythonClassSceneDataAsset::GetData(bool doraise) const -> SceneDataAsset* {
  SceneDataAsset* data = data_->get();
  if (!data && doraise) {
    throw Exception("Invalid Data.", PyExcType::kNotFound);
  }
  return data;
}
// Clion makes some incorrect inferences here.
#pragma clang diagnostic push
#pragma ide diagnostic ignored "UnreachableCode"
#pragma ide diagnostic ignored "ConstantConditionsOC"
#pragma ide diagnostic ignored "ConstantFunctionResult"

auto PythonClassSceneDataAsset::tp_new(PyTypeObject* type, PyObject* args,
                                       PyObject* kwds) -> PyObject* {
  auto* self =
      reinterpret_cast<PythonClassSceneDataAsset*>(type->tp_alloc(type, 0));
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
        "Can't instantiate Datas directly; use bascenev1.getdata() to get "
        "them.");
  }
  self->data_ = new Object::Ref<SceneDataAsset>();
  return reinterpret_cast<PyObject*>(self);
  BA_PYTHON_NEW_CATCH;
}
#pragma clang diagnostic pop

void PythonClassSceneDataAsset::tp_dealloc(PythonClassSceneDataAsset* self) {
  BA_PYTHON_TRY;
  // Our Object::Ref needs to be released in the logic thread.
  auto* ptr = self->data_;
  if (g_base->InLogicThread()) {
    delete ptr;
  } else {
    g_base->logic->event_loop()->PushCall([ptr] { delete ptr; });
  }
  BA_PYTHON_DEALLOC_CATCH;
  Py_TYPE(self)->tp_free(reinterpret_cast<PyObject*>(self));
}

auto PythonClassSceneDataAsset::GetValue(PythonClassSceneDataAsset* self)
    -> PyObject* {
  BA_PYTHON_TRY;
  SceneDataAsset* data = self->data_->get();
  if (data == nullptr) {
    throw Exception("Invalid data object.", PyExcType::kNotFound);
  }
  // haha really need to rename this class.
  base::DataAsset* datadata = data->data_data();
  datadata->Load();
  datadata->set_last_used_time(g_core->AppTimeMillisecs());
  PyObject* obj = datadata->object().get();
  assert(obj);
  Py_INCREF(obj);
  return obj;
  BA_PYTHON_CATCH;
}

bool PythonClassSceneDataAsset::s_create_empty_ = false;
PyTypeObject PythonClassSceneDataAsset::type_obj;

PyMethodDef PythonClassSceneDataAsset::tp_methods[] = {
    {"getvalue", (PyCFunction)GetValue, METH_NOARGS,
     "getvalue() -> Any\n"
     "\n"
     "Return the data object's value.\n"
     "\n"
     "This can consist of anything representable by json (dicts, lists,\n"
     "numbers, bools, None, etc).\n"
     "Note that this call will block if the data has not yet been loaded,\n"
     "so it can be beneficial to plan a short bit of time between when\n"
     "the data object is requested and when it's value is accessed.\n"},
    {nullptr}};

}  // namespace ballistica::scene_v1
