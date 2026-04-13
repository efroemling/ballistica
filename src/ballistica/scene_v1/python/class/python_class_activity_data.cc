// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/python/class/python_class_activity_data.h"

#include <string>

#include "ballistica/base/logic/logic.h"
#include "ballistica/base/python/class/python_class_context_ref.h"
#include "ballistica/scene_v1/support/host_activity.h"
#include "ballistica/scene_v1/support/host_session.h"
#include "ballistica/shared/foundation/event_loop.h"
#include "ballistica/shared/generic/utils.h"

namespace ballistica::scene_v1 {

auto PythonClassActivityData::nb_bool(PythonClassActivityData* self) -> int {
  return self->host_activity_->exists();
}

PyNumberMethods PythonClassActivityData::as_number_;

auto PythonClassActivityData::type_name() -> const char* {
  return "ActivityData";
}

void PythonClassActivityData::SetupType(PyTypeObject* cls) {
  PythonClass::SetupType(cls);
  // Fully qualified type path we will be exposed as:
  cls->tp_name = "bascenev1.ActivityData";
  cls->tp_basicsize = sizeof(PythonClassActivityData);
  cls->tp_doc =
      "Internal; holds native data for the activity.\n"
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

auto PythonClassActivityData::Create(HostActivity* host_activity) -> PyObject* {
  assert(TypeIsSetUp(&type_obj));
  auto* py_activity_data = reinterpret_cast<PythonClassActivityData*>(
      PyObject_CallObject(reinterpret_cast<PyObject*>(&type_obj), nullptr));
  BA_PRECONDITION(py_activity_data);
  *py_activity_data->host_activity_ = host_activity;
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
  self->host_activity_ = new Object::WeakRef<HostActivity>();
  return reinterpret_cast<PyObject*>(self);
  BA_PYTHON_NEW_CATCH;
}

void PythonClassActivityData::tp_dealloc(PythonClassActivityData* self) {
  BA_PYTHON_TRY;

  // These have to be destructed in the logic thread; send them along to
  // it if need be; otherwise do it immediately.
  if (!g_base->InLogicThread()) {
    Object::WeakRef<HostActivity>* h = self->host_activity_;
    g_base->logic->event_loop()->PushCall([h] { delete h; });
  } else {
    delete self->host_activity_;
  }
  BA_PYTHON_DEALLOC_CATCH;
  Py_TYPE(self)->tp_free(reinterpret_cast<PyObject*>(self));
}

auto PythonClassActivityData::Exists(PythonClassActivityData* self)
    -> PyObject* {
  BA_PYTHON_TRY;
  BA_PRECONDITION(g_base->InLogicThread());
  HostActivity* host_activity = self->host_activity_->get();
  if (host_activity) {
    Py_RETURN_TRUE;
  } else {
    Py_RETURN_FALSE;
  }

  BA_PYTHON_CATCH;
}

auto PythonClassActivityData::MakeForeground(PythonClassActivityData* self)
    -> PyObject* {
  BA_PYTHON_TRY;
  BA_PRECONDITION(g_base->InLogicThread());
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

auto PythonClassActivityData::Start(PythonClassActivityData* self)
    -> PyObject* {
  BA_PYTHON_TRY;
  BA_PRECONDITION(g_base->InLogicThread());

  HostActivity* a = self->host_activity_->get();
  if (!a) {
    throw Exception("Invalid activity data.", PyExcType::kActivityNotFound);
  }
  a->Start();

  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PythonClassActivityData::Expire(PythonClassActivityData* self)
    -> PyObject* {
  BA_PYTHON_TRY;
  BA_PRECONDITION(g_base->InLogicThread());
  HostActivity* a = self->host_activity_->get();

  // The Python side may have stuck around after our c++ side was
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

auto PythonClassActivityData::Context(PythonClassActivityData* self)
    -> PyObject* {
  BA_PYTHON_TRY;
  BA_PRECONDITION(g_base->InLogicThread());
  HostActivity* a = self->host_activity_->get();
  if (!a) {
    throw Exception("Activity is not valid.");
  }
  return base::PythonClassContextRef::Create(a);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

PyTypeObject PythonClassActivityData::type_obj;
PyMethodDef PythonClassActivityData::tp_methods[] = {
    {"exists", (PyCFunction)Exists, METH_NOARGS,
     "exists() -> bool\n"
     "\n"
     "Returns whether the activity-data still exists.\n"
     "Most functionality will fail on a nonexistent instance."},
    {"make_foreground", (PyCFunction)MakeForeground, METH_NOARGS,
     "make_foreground() -> None\n"
     "\n"
     "Sets this activity as the foreground one in its session."},
    {"expire", (PyCFunction)Expire, METH_NOARGS,
     "expire() -> None\n"
     "\n"
     "Expires the internal data for the activity"},
    {"start", (PyCFunction)Start, METH_NOARGS,
     "start() -> None\n"
     "\n"
     "Begins the activity running"},
    {"context", (PyCFunction)Context, METH_NOARGS,
     "context() -> bascenev1.ContextRef\n"
     "\n"
     "Return a context-ref pointing to the activity."},

    {nullptr}};

}  // namespace ballistica::scene_v1
