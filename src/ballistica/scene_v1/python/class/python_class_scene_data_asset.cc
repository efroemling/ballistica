// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/python/class/python_class_scene_data_asset.h"

#include "ballistica/base/assets/data_asset.h"

namespace ballistica::scene_v1 {

auto PythonClassSceneDataAsset::GetValue(PythonClassSceneDataAsset* self)
    -> PyObject* {
  BA_PYTHON_TRY;
  SceneDataAsset* data = self->GetData();
  base::DataAsset* datadata = data->data_data();
  datadata->Load();
  datadata->set_last_used_time(g_core->AppTimeMillisecs());
  PyObject* obj = datadata->object().get();
  assert(obj);
  Py_INCREF(obj);
  return obj;
  BA_PYTHON_CATCH;
}

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
