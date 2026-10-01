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

PyMethodDef PythonClassViewerSource::tp_methods[] = {
    {"get_idle_time", (PyCFunction)GetIdleTime, METH_NOARGS,
     "get_idle_time() -> float\n"
     "\n"
     "Return seconds (of display time) since a widget last showed us,\n"
     "or since we were created if none ever has."},
    {nullptr}  // Sentinel
};

}  // namespace ballistica::ui_v1
