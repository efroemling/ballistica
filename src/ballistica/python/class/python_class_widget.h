// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_PYTHON_CLASS_PYTHON_CLASS_WIDGET_H_
#define BALLISTICA_PYTHON_CLASS_PYTHON_CLASS_WIDGET_H_

#include "ballistica/core/object.h"
#include "ballistica/python/class/python_class.h"

namespace ballistica {

class PythonClassWidget : public PythonClass {
 public:
  static void SetupType(PyTypeObject* obj);
  static auto type_name() -> const char* { return "Widget"; }
  static auto Create(Widget* widget) -> PyObject*;
  static auto Check(PyObject* o) -> bool {
    return PyObject_TypeCheck(o, &type_obj);
  }
  static PyTypeObject type_obj;
  auto GetWidget() const -> Widget*;

 private:
  static PyMethodDef tp_methods[];
  static auto tp_repr(PythonClassWidget* self) -> PyObject*;
  static auto tp_new(PyTypeObject* type, PyObject* args, PyObject* keywds)
      -> PyObject*;
  static void tp_dealloc(PythonClassWidget* self);
  static auto Exists(PythonClassWidget* self) -> PyObject*;
  static auto GetWidgetType(PythonClassWidget* self) -> PyObject*;
  static auto Activate(PythonClassWidget* self) -> PyObject*;
  static auto GetChildren(PythonClassWidget* self) -> PyObject*;
  static auto GetSelectedChild(PythonClassWidget* self) -> PyObject*;
  static auto GetScreenSpaceCenter(PythonClassWidget* self) -> PyObject*;
  static auto Delete(PythonClassWidget* self, PyObject* args, PyObject* keywds)
      -> PyObject*;
  static auto AddDeleteCallback(PythonClassWidget* self, PyObject* args,
                                PyObject* keywds) -> PyObject*;
  Object::WeakRef<Widget>* widget_;
  static auto nb_bool(PythonClassWidget* self) -> int;
  static PyNumberMethods as_number_;
};

}  // namespace ballistica

#endif  // BALLISTICA_PYTHON_CLASS_PYTHON_CLASS_WIDGET_H_
