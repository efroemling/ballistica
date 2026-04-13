// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/python/class/python_class_feature_set_data.h"

namespace ballistica::base {

auto PythonClassFeatureSetData::type_name() -> const char* {
  return "FeatureSetData";
}

void PythonClassFeatureSetData::SetupType(PyTypeObject* cls) {
  PythonClass::SetupType(cls);
  // Fully qualified type path we will be exposed as:
  cls->tp_name = "_babase.FeatureSetData";
  cls->tp_basicsize = sizeof(PythonClassFeatureSetData);
  cls->tp_doc = "Internal.";
  cls->tp_new = tp_new;
  cls->tp_dealloc = (destructor)tp_dealloc;
  cls->tp_methods = tp_methods;
}

auto PythonClassFeatureSetData::Create(FeatureSetNativeComponent* feature_set)
    -> PyObject* {
  assert(feature_set);
  assert(TypeIsSetUp(&type_obj));
  auto* py_sound = reinterpret_cast<PythonClassFeatureSetData*>(
      PyObject_CallObject(reinterpret_cast<PyObject*>(&type_obj), nullptr));
  if (!feature_set) {
    throw Exception("FeatureSetData creation failed.");
  }

  py_sound->feature_set_ = feature_set;
  return reinterpret_cast<PyObject*>(py_sound);
}

auto PythonClassFeatureSetData::tp_new(PyTypeObject* type, PyObject* args,
                                       PyObject* keywds) -> PyObject* {
  auto* self =
      reinterpret_cast<PythonClassFeatureSetData*>(type->tp_alloc(type, 0));
  return reinterpret_cast<PyObject*>(self);
}

void PythonClassFeatureSetData::tp_dealloc(PythonClassFeatureSetData* self) {
  BA_PYTHON_TRY;
  BA_PYTHON_DEALLOC_CATCH;
  Py_TYPE(self)->tp_free(reinterpret_cast<PyObject*>(self));
}

PyTypeObject PythonClassFeatureSetData::type_obj;
PyMethodDef PythonClassFeatureSetData::tp_methods[] = {{nullptr}};

}  // namespace ballistica::base
