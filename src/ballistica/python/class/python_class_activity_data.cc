// Copyright (c) 2011-2020 Eric Froemling

#include "ballistica/python/class/python_class_activity_data.h"

#include <string>

#include "ballistica/game/game.h"
#include "ballistica/game/host_activity.h"
#include "ballistica/game/session/host_session.h"
#include "ballistica/generic/utils.h"

namespace ballistica {

auto PythonClassActivityData::nb_bool(PythonClassActivityData* self) -> int {
  return self->host_activity_->exists();
}

PyNumberMethods PythonClassActivityData::as_number_;

void PythonClassActivityData::SetupType(PyTypeObject* obj) {
  PythonClass::SetupType(obj);
  obj->tp_name = "_ba.ActivityData";
  obj->tp_basicsize = sizeof(PythonClassActivityData);
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

auto PythonClassActivityData::Create(HostActivity* host_activity) -> PyObject* {
  auto* py_activity_data = reinterpret_cast<PythonClassActivityData*>(
      PyObject_CallObject(reinterpret_cast<PyObject*>(&type_obj), nullptr));
  BA_PRECONDITION(py_activity_data);
  *(py_activity_data->host_activity_) = host_activity;
  return reinterpret_cast<PyObject*>(py_activity_data);
}

auto PythonClassActivityData::GetHostActivity() const -> HostActivity* {
  HostActivity* host_activity = host_activity_->get();
  if (!host_activity)
    throw Exception(
        "Invalid ActivityData; this activity has probably been expired and "
        "should not be getting used.");
  return host_activity;
}

auto PythonClassActivityData::tp_repr(PythonClassActivityData* self)
    -> PyObject* {
  BA_PYTHON_TRY;
  return Py_BuildValue(
      "s", (std::string("<Ballistica ActivityData ")
            + Utils::PtrToString(self->host_activity_->get()) + " >")
               .c_str());
  BA_PYTHON_CATCH;
}

auto PythonClassActivityData::tp_new(PyTypeObject* type, PyObject* args,
                                     PyObject* keywds) -> PyObject* {
  auto* self =
      reinterpret_cast<PythonClassActivityData*>(type->tp_alloc(type, 0));
  if (self) {
    BA_PYTHON_TRY;
    if (!InGameThread()) {
      throw Exception(
          "ERROR: " + std::string(type_obj.tp_name)
          + " objects must only be created in the game thread (current is ("
          + GetCurrentThreadName() + ").");
    }
    self->host_activity_ = new Object::WeakRef<HostActivity>();
    BA_PYTHON_NEW_CATCH;
  }
  return reinterpret_cast<PyObject*>(self);
}

void PythonClassActivityData::tp_dealloc(PythonClassActivityData* self) {
  BA_PYTHON_TRY;

  // These have to be destructed in the game thread; send them along to
  // it if need be; otherwise do it immediately.
  if (!InGameThread()) {
    Object::WeakRef<HostActivity>* h = self->host_activity_;
    g_game->PushCall([h] { delete h; });
  } else {
    delete self->host_activity_;
  }
  BA_PYTHON_DEALLOC_CATCH;
  Py_TYPE(self)->tp_free(reinterpret_cast<PyObject*>(self));
}

auto PythonClassActivityData::exists(PythonClassActivityData* self)
    -> PyObject* {
  BA_PYTHON_TRY;

  HostActivity* host_activity = self->host_activity_->get();
  if (host_activity) {
    Py_RETURN_TRUE;
  } else {
    Py_RETURN_FALSE;
  }

  BA_PYTHON_CATCH;
}

auto PythonClassActivityData::make_foreground(PythonClassActivityData* self)
    -> PyObject* {
  BA_PYTHON_TRY;

  HostActivity* a = self->host_activity_->get();
  if (!a) {
    throw Exception("Invalid activity.", PyExcType::kActivityNotFound);
  }
  HostSession* session = a->GetHostSession();
  if (!session) {
    throw Exception("Activity's Session not found.",
                    PyExcType::kSessionNotFound);
  }
  session->SetForegroundHostActivity(a);

  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PythonClassActivityData::start(PythonClassActivityData* self)
    -> PyObject* {
  BA_PYTHON_TRY;

  HostActivity* a = self->host_activity_->get();
  if (!a) {
    throw Exception("Invalid activity data.", PyExcType::kActivityNotFound);
  }
  a->start();

  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PythonClassActivityData::expire(PythonClassActivityData* self)
    -> PyObject* {
  BA_PYTHON_TRY;
  HostActivity* a = self->host_activity_->get();

  // The python side may have stuck around after our c++ side was
  // torn down; that's ok.
  if (a) {
    HostSession* session = a->GetHostSession();
    if (!session) {
      throw Exception("Activity's Session not found.",
                      PyExcType::kSessionNotFound);
    }
    session->DestroyHostActivity(a);
  }
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

PyTypeObject PythonClassActivityData::type_obj;
PyMethodDef PythonClassActivityData::tp_methods[] = {
    {"exists", (PyCFunction)exists, METH_NOARGS,
     "exists() -> bool\n"
     "\n"
     "Returns whether the ActivityData still exists.\n"
     "Most functionality will fail on a nonexistent instance."},
    {"make_foreground", (PyCFunction)make_foreground, METH_NOARGS,
     "make_foreground() -> None\n"
     "\n"
     "Sets this activity as the foreground one in its session."},
    {"expire", (PyCFunction)expire, METH_NOARGS,
     "expire() -> None\n"
     "\n"
     "Expires the internal data for the activity"},
    {"start", (PyCFunction)start, METH_NOARGS,
     "start() -> None\n"
     "\n"
     "Begins the activity running"},
    {nullptr}};

}  // namespace ballistica
