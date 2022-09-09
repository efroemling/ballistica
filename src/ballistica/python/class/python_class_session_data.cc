// Released under the MIT License. See LICENSE for details.

#include "ballistica/python/class/python_class_session_data.h"

#include "ballistica/core/thread.h"
#include "ballistica/game/game.h"
#include "ballistica/game/session/session.h"
#include "ballistica/generic/utils.h"
#include "ballistica/python/python.h"

namespace ballistica {

auto PythonClassSessionData::nb_bool(PythonClassSessionData* self) -> int {
  return self->session_->exists();
}

PyNumberMethods PythonClassSessionData::as_number_;

void PythonClassSessionData::SetupType(PyTypeObject* obj) {
  PythonClass::SetupType(obj);
  obj->tp_name = "_ba.SessionData";
  obj->tp_basicsize = sizeof(PythonClassSessionData);
  obj->tp_doc = "(internal)";
  obj->tp_new = tp_new;
  obj->tp_dealloc = (destructor)tp_dealloc;
  obj->tp_repr = (reprfunc)tp_repr;
  obj->tp_methods = tp_methods;

  // We provide number methods only for bool functionality.
  memset(&as_number_, 0, sizeof(as_number_));
  as_number_.nb_bool = (inquiry)nb_bool;
  obj->tp_as_number = &as_number_;
}

auto PythonClassSessionData::Create(Session* session) -> PyObject* {
  auto* py_session_data = reinterpret_cast<PythonClassSessionData*>(
      PyObject_CallObject(reinterpret_cast<PyObject*>(&type_obj), nullptr));
  BA_PRECONDITION(py_session_data);
  *(py_session_data->session_) = session;
  return reinterpret_cast<PyObject*>(py_session_data);
}

auto PythonClassSessionData::GetSession() const -> Session* {
  Session* session = session_->get();
  if (!session) {
    throw Exception("Invalid SessionData.", PyExcType::kSessionNotFound);
  }
  return session;
}

auto PythonClassSessionData::tp_repr(PythonClassSessionData* self)
    -> PyObject* {
  BA_PYTHON_TRY;
  return Py_BuildValue("s", (std::string("<Ballistica SessionData ")
                             + Utils::PtrToString(self->session_->get()) + " >")
                                .c_str());
  BA_PYTHON_CATCH;
}

auto PythonClassSessionData::tp_new(PyTypeObject* type, PyObject* args,
                                    PyObject* keywds) -> PyObject* {
  auto* self =
      reinterpret_cast<PythonClassSessionData*>(type->tp_alloc(type, 0));
  if (self) {
    BA_PYTHON_TRY;
    if (!InLogicThread()) {
      throw Exception(
          "ERROR: " + std::string(type_obj.tp_name)
          + " objects must only be created in the game thread (current is ("
          + GetCurrentThreadName() + ").");
    }
    self->session_ = new Object::WeakRef<Session>();
    BA_PYTHON_NEW_CATCH;
  }
  return reinterpret_cast<PyObject*>(self);
}

void PythonClassSessionData::tp_dealloc(PythonClassSessionData* self) {
  BA_PYTHON_TRY;
  // These have to be deleted in the game thread;
  // ...send the ptr along if need be.
  // FIXME: technically the main thread has a pointer to a dead PyObject
  // until the delete goes through; could that ever be a problem?
  if (!InLogicThread()) {
    Object::WeakRef<Session>* s = self->session_;
    g_game->thread()->PushCall([s] { delete s; });
  } else {
    delete self->session_;
  }
  BA_PYTHON_DEALLOC_CATCH;
  Py_TYPE(self)->tp_free(reinterpret_cast<PyObject*>(self));
}

auto PythonClassSessionData::Exists(PythonClassSessionData* self) -> PyObject* {
  BA_PYTHON_TRY;
  Session* sgc = self->session_->get();
  if (sgc) {
    Py_RETURN_TRUE;
  } else {
    Py_RETURN_FALSE;
  }
  BA_PYTHON_CATCH;
}

PyTypeObject PythonClassSessionData::type_obj;
PyMethodDef PythonClassSessionData::tp_methods[] = {
    {"exists", (PyCFunction)Exists, METH_NOARGS,
     "exists() -> bool\n"
     "\n"
     "Returns whether the SessionData still exists.\n"
     "Most functionality will fail on a nonexistent instance."},
    {nullptr}};

}  // namespace ballistica
