// Released under the MIT License. See LICENSE for details.

#include "ballistica/ui_v1/python/class/python_class_viewer_source.h"

namespace ballistica::ui_v1 {

auto PythonClassViewerSource::GetIdleTime(PythonClassViewerSource* self)
    -> PyObject* {
  BA_PYTHON_TRY;
  BA_PRECONDITION(g_base->InLogicThread());
  return PyFloat_FromDouble(self->GetAsset()->GetIdleTime());
  BA_PYTHON_CATCH;
}

auto PythonClassViewerSource::MarkRetired(PythonClassViewerSource* self)
    -> PyObject* {
  BA_PYTHON_TRY;
  BA_PRECONDITION(g_base->InLogicThread());
  self->GetAsset()->MarkRetired();
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

PyMethodDef PythonClassViewerSource::tp_methods[] = {
    {"get_idle_time", (PyCFunction)GetIdleTime, METH_NOARGS,
     "get_idle_time() -> float\n"
     "\n"
     "Return seconds (of display time) since a widget last showed us,\n"
     "or since we were created if none ever has."},
    {"mark_retired", (PyCFunction)MarkRetired, METH_NOARGS,
     "mark_retired() -> None\n"
     "\n"
     "Note that our owner has retired us for good, so anything still\n"
     "showing us asks for a viewer again (the viewer registry calls\n"
     "this as it shuts a viewer down)."},
    {nullptr}  // Sentinel
};

}  // namespace ballistica::ui_v1
