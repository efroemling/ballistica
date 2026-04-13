// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/python/class/python_class_session_data.h"

#include <string>

#include "ballistica/base/logic/logic.h"
#include "ballistica/base/python/class/python_class_context_ref.h"
#include "ballistica/scene_v1/support/session.h"
#include "ballistica/shared/foundation/event_loop.h"
#include "ballistica/shared/generic/utils.h"

namespace ballistica::scene_v1 {

auto PythonClassSessionData::nb_bool(PythonClassSessionData* self) -> int {
  return self->session_->exists();
}

PyNumberMethods PythonClassSessionData::as_number_;

auto PythonClassSessionData::type_name() -> const char* {
  return "SessionData";
}

void PythonClassSessionData::SetupType(PyTypeObject* cls) {
  PythonClass::SetupType(cls);
  // Fully qualified type path we will be exposed as:
  cls->tp_name = "bascenev1.SessionData";
  cls->tp_basicsize = sizeof(PythonClassSessionData);
  cls->tp_doc =
      "Internal; holds native data for the session.\n"
      "\n"
      ":meta private:";
  cls->tp_new = tp_new;
  cls->tp_dealloc = (destructor)tp_dealloc;
  cls->tp_repr = (reprfunc)tp_repr;
  cls->tp_methods = tp_methods;

  // We provide number methods only for bool functionality.
  memset(&as_number_, 0, sizeof(as_number_));
  as_number_.nb_bool = (inquiry)nb_bool;
  cls->tp_as_number = &as_number_;
}

auto PythonClassSessionData::Create(Session* session) -> PyObject* {
  assert(TypeIsSetUp(&type_obj));
  auto* py_session_data = reinterpret_cast<PythonClassSessionData*>(
      PyObject_CallObject(reinterpret_cast<PyObject*>(&type_obj), nullptr));
  BA_PRECONDITION(py_session_data);
  *py_session_data->session_ = session;
  return reinterpret_cast<PyObject*>(py_session_data);
}

auto PythonClassSessionData::GetSession() const -> Session* {
  Session* session = session_->get();
  if (!session) {
    throw Exception("Invalid SessionData.", PyExcType::kSessionNotFound);
  }
  return session;
}

auto PythonClassSessionData::Context(PythonClassSessionData* self)
    -> PyObject* {
  BA_PYTHON_TRY;
  BA_PRECONDITION(g_base->InLogicThread());
  Session* s = self->session_->get();
  if (!s) {
    throw Exception("Session is not valid.");
  }
  return base::PythonClassContextRef::Create(s);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
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
  self->session_ = new Object::WeakRef<Session>();
  return reinterpret_cast<PyObject*>(self);
  BA_PYTHON_NEW_CATCH;
}

void PythonClassSessionData::tp_dealloc(PythonClassSessionData* self) {
  BA_PYTHON_TRY;
  // These have to be deleted in the logic thread;
  // ...send the ptr along if need be.
  // FIXME: technically the main thread has a pointer to a dead PyObject
  // until the delete goes through; could that ever be a problem?
  if (!g_base->InLogicThread()) {
    Object::WeakRef<Session>* s = self->session_;
    g_base->logic->event_loop()->PushCall([s] { delete s; });
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
    {"context", (PyCFunction)Context, METH_NOARGS,
     "context() -> bascenev1.ContextRef\n"
     "\n"
     "Return a context-ref pointing to the session."},

    {nullptr}};

}  // namespace ballistica::scene_v1
