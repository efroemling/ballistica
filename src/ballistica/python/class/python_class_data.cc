// Copyright (c) 2011-2020 Eric Froemling

#include "ballistica/python/class/python_class_data.h"

#include <string>

#include "ballistica/game/game.h"
#include "ballistica/media/component/data.h"

namespace ballistica {

auto PythonClassData::tp_repr(PythonClassData* self) -> PyObject* {
  BA_PYTHON_TRY;
  Object::Ref<Data> m = *(self->data_);
  return Py_BuildValue(
      "s", (std::string("<ba.Data ")
            + (m.exists() ? ("\"" + m->name() + "\"") : "(empty ref)") + ">")
               .c_str());
  BA_PYTHON_CATCH;
}

void PythonClassData::SetupType(PyTypeObject* obj) {
  PythonClass::SetupType(obj);
  obj->tp_name = "ba.Data";
  obj->tp_basicsize = sizeof(PythonClassData);
  obj->tp_doc =
      "A reference to a data object.\n"
      "\n"
      "Category: Asset Classes\n"
      "\n"
      "Use ba.getdata() to instantiate one.";
  obj->tp_repr = (reprfunc)tp_repr;
  obj->tp_new = tp_new;
  obj->tp_dealloc = (destructor)tp_dealloc;
  obj->tp_methods = tp_methods;
}

auto PythonClassData::Create(Data* data) -> PyObject* {
  s_create_empty_ = true;  // prevent class from erroring on create
  auto* t = reinterpret_cast<PythonClassData*>(
      PyObject_CallObject(reinterpret_cast<PyObject*>(&type_obj), nullptr));
  s_create_empty_ = false;
  if (!t) {
    throw Exception("ba.Data creation failed.");
  }
  *(t->data_) = data;
  return reinterpret_cast<PyObject*>(t);
}

auto PythonClassData::GetData(bool doraise) const -> Data* {
  Data* data = data_->get();
  if (!data && doraise) {
    throw Exception("Invalid Data.", PyExcType::kNotFound);
  }
  return data;
}

auto PythonClassData::tp_new(PyTypeObject* type, PyObject* args, PyObject* kwds)
    -> PyObject* {
  auto* self = reinterpret_cast<PythonClassData*>(type->tp_alloc(type, 0));
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
          "Can't instantiate Datas directly; use ba.getdata() to get "
          "them.");
    }
    self->data_ = new Object::Ref<Data>();
    BA_PYTHON_NEW_CATCH;
  }
  return reinterpret_cast<PyObject*>(self);
}

void PythonClassData::Delete(Object::Ref<Data>* ref) {
  assert(InGameThread());

  // if we're the py-object for a data, clear them out
  // (FIXME - wej should pass the old pointer in here to sanity-test that we
  // were their ref)
  if (ref->exists()) {
    (*ref)->ClearPyObject();
  }
  delete ref;
}

void PythonClassData::tp_dealloc(PythonClassData* self) {
  BA_PYTHON_TRY;
  // these have to be deleted in the game thread - send the ptr along if need
  // be; otherwise do it immediately
  if (!InGameThread()) {
    Object::Ref<Data>* s = self->data_;
    g_game->PushCall([s] { Delete(s); });
  } else {
    Delete(self->data_);
  }
  BA_PYTHON_DEALLOC_CATCH;
  Py_TYPE(self)->tp_free(reinterpret_cast<PyObject*>(self));
}

auto PythonClassData::GetValue(PythonClassData* self) -> PyObject* {
  BA_PYTHON_TRY;
  Data* data = self->data_->get();
  if (data == nullptr) {
    throw Exception("Invalid data object.", PyExcType::kNotFound);
  }
  // haha really need to rename this class.
  DataData* datadata = data->data_data();
  datadata->Load();
  datadata->set_last_used_time(GetRealTime());
  PyObject* obj = datadata->object().get();
  assert(obj);
  Py_INCREF(obj);
  return obj;
  BA_PYTHON_CATCH;
}

bool PythonClassData::s_create_empty_ = false;
PyTypeObject PythonClassData::type_obj;

PyMethodDef PythonClassData::tp_methods[] = {
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

}  // namespace ballistica
