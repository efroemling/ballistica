// Released under the MIT License. See LICENSE for details.

#include "ballistica/python/class/python_class_widget.h"

#include "ballistica/core/thread.h"
#include "ballistica/game/game.h"
#include "ballistica/generic/utils.h"
#include "ballistica/graphics/graphics.h"
#include "ballistica/python/python.h"
#include "ballistica/ui/widget/container_widget.h"

namespace ballistica {

auto PythonClassWidget::nb_bool(PythonClassWidget* self) -> int {
  return self->widget_->exists();
}

PyNumberMethods PythonClassWidget::as_number_;

void PythonClassWidget::SetupType(PyTypeObject* obj) {
  PythonClass::SetupType(obj);
  obj->tp_name = "ba.Widget";
  obj->tp_basicsize = sizeof(PythonClassWidget);
  obj->tp_doc =
      "Internal type for low level UI elements; buttons, windows, etc.\n"
      "\n"
      "Category: **User Interface Classes**\n"
      "\n"
      "This class represents a weak reference to a widget object\n"
      "in the internal C++ layer. Currently, functions such as\n"
      "ba.buttonwidget() must be used to instantiate or edit these.";
  obj->tp_new = tp_new;
  obj->tp_dealloc = (destructor)tp_dealloc;
  obj->tp_repr = (reprfunc)tp_repr;
  obj->tp_methods = tp_methods;

  // we provide number methods only for bool functionality
  memset(&as_number_, 0, sizeof(as_number_));
  as_number_.nb_bool = (inquiry)nb_bool;
  obj->tp_as_number = &as_number_;
}

auto PythonClassWidget::Create(Widget* widget) -> PyObject* {
  // Make sure we only have one python ref per widget.
  if (widget) {
    assert(!widget->has_py_ref());
  }

  auto* py_widget = reinterpret_cast<PythonClassWidget*>(
      PyObject_CallObject(reinterpret_cast<PyObject*>(&type_obj), nullptr));
  if (!py_widget) throw Exception("ba.Widget creation failed");

  *(py_widget->widget_) = widget;
  return reinterpret_cast<PyObject*>(py_widget);
}

auto PythonClassWidget::GetWidget() const -> Widget* {
  Widget* w = widget_->get();
  if (!w) throw Exception("Invalid widget");
  return w;
}

auto PythonClassWidget::tp_repr(PythonClassWidget* self) -> PyObject* {
  BA_PYTHON_TRY;
  Widget* w = self->widget_->get();
  return Py_BuildValue("s", (std::string("<Ballistica '")
                             + (w ? w->GetWidgetTypeName() : "<invalid>")
                             + "' widget " + Utils::PtrToString(w) + ">")
                                .c_str());
  BA_PYTHON_CATCH;
}

auto PythonClassWidget::tp_new(PyTypeObject* type, PyObject* args,
                               PyObject* keywds) -> PyObject* {
  auto* self = reinterpret_cast<PythonClassWidget*>(type->tp_alloc(type, 0));
  if (self) {
    BA_PYTHON_TRY;
    if (!InLogicThread()) {
      throw Exception(
          "ERROR: " + std::string(type_obj.tp_name)
          + " objects must only be created in the game thread (current is ("
          + GetCurrentThreadName() + ").");
    }
    self->widget_ = new Object::WeakRef<Widget>();
    BA_PYTHON_NEW_CATCH;
  }
  return reinterpret_cast<PyObject*>(self);
}

void PythonClassWidget::tp_dealloc(PythonClassWidget* self) {
  BA_PYTHON_TRY;
  // these have to be destructed in the game thread - send them along to it if
  // need be
  if (!InLogicThread()) {
    Object::WeakRef<Widget>* w = self->widget_;
    g_game->thread()->PushCall([w] { delete w; });
  } else {
    delete self->widget_;
  }
  BA_PYTHON_DEALLOC_CATCH;
  Py_TYPE(self)->tp_free(reinterpret_cast<PyObject*>(self));
}

auto PythonClassWidget::Exists(PythonClassWidget* self) -> PyObject* {
  BA_PYTHON_TRY;
  Widget* w = self->widget_->get();
  if (w) {
    Py_RETURN_TRUE;
  } else {
    Py_RETURN_FALSE;
  }
  BA_PYTHON_CATCH;
}

auto PythonClassWidget::GetWidgetType(PythonClassWidget* self) -> PyObject* {
  BA_PYTHON_TRY;
  Widget* w = self->widget_->get();
  if (!w) {
    throw Exception(PyExcType::kWidgetNotFound);
  }
  return PyUnicode_FromString(w->GetWidgetTypeName().c_str());
  BA_PYTHON_CATCH;
}

auto PythonClassWidget::Activate(PythonClassWidget* self) -> PyObject* {
  BA_PYTHON_TRY;
  Widget* w = self->widget_->get();
  if (!w) {
    throw Exception(PyExcType::kWidgetNotFound);
  }
  w->Activate();
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PythonClassWidget::GetChildren(PythonClassWidget* self) -> PyObject* {
  BA_PYTHON_TRY;
  Widget* w = self->widget_->get();
  if (!w) {
    throw Exception(PyExcType::kWidgetNotFound);
  }
  PyObject* py_list = PyList_New(0);
  auto* cw = dynamic_cast<ContainerWidget*>(w);

  // Clion seems to think dynamic_casting a Widget* to a ContainerWidget*
  // will always succeed. Go home Clion; you're drunk.
#pragma clang diagnostic push
#pragma ide diagnostic ignored "ConstantConditionsOC"
  if (cw) {
#pragma clang diagnostic pop
    for (auto&& i : cw->widgets()) {
      assert(i.exists());
      PyList_Append(py_list, i->BorrowPyRef());
    }
  }
  return py_list;
  BA_PYTHON_CATCH;
}

auto PythonClassWidget::GetSelectedChild(PythonClassWidget* self) -> PyObject* {
  BA_PYTHON_TRY;
  Widget* w = self->widget_->get();
  if (!w) {
    throw Exception(PyExcType::kWidgetNotFound);
  }
  auto* cw = dynamic_cast<ContainerWidget*>(w);

  // Clion seems to think dynamic_casting a Widget* to a ContainerWidget*
  // will always succeed. Go home Clion; you're drunk.
#pragma clang diagnostic push
#pragma ide diagnostic ignored "ConstantConditionsOC"
  if (cw) {
#pragma clang diagnostic pop
    Widget* selected_widget = cw->selected_widget();
    if (selected_widget) return selected_widget->NewPyRef();
  }
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PythonClassWidget::GetScreenSpaceCenter(PythonClassWidget* self)
    -> PyObject* {
  BA_PYTHON_TRY;
  Widget* w = self->widget_->get();
  if (!w) {
    throw Exception(PyExcType::kWidgetNotFound);
  }
  float x, y;
  w->GetCenter(&x, &y);

  // this gives us coords in the widget's parent's space; translate from that
  // to screen space
  if (ContainerWidget* parent = w->parent_widget()) {
    parent->WidgetPointToScreen(&x, &y);
  }
  // ..but we actually want to return points relative to the center of the
  // screen (so they're useful as stack-offset values)
  float screen_width = g_graphics->screen_virtual_width();
  float screen_height = g_graphics->screen_virtual_height();
  x -= screen_width * 0.5f;
  y -= screen_height * 0.5f;
  return Py_BuildValue("(ff)", x, y);
  BA_PYTHON_CATCH;
}

auto PythonClassWidget::Delete(PythonClassWidget* self, PyObject* args,
                               PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  int ignore_missing = true;
  static const char* kwlist[] = {"ignore_missing", nullptr};
  if (!PyArg_ParseTupleAndKeywords(
          args, keywds, "|i", const_cast<char**>(kwlist), &ignore_missing)) {
    return nullptr;
  }
  Widget* w = self->widget_->get();
  if (!w) {
    if (!ignore_missing) {
      throw Exception(PyExcType::kWidgetNotFound);
    }
  } else {
    ContainerWidget* p = w->parent_widget();
    if (p) {
      p->DeleteWidget(w);
    } else {
      Log("Error: Can't delete widget: no parent.");
    }
  }
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PythonClassWidget::AddDeleteCallback(PythonClassWidget* self,
                                          PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  PyObject* call_obj;
  static const char* kwlist[] = {"call", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "O",
                                   const_cast<char**>(kwlist), &call_obj)) {
    return nullptr;
  }
  Widget* w = self->widget_->get();
  if (!w) {
    throw Exception(PyExcType::kWidgetNotFound);
  }
  w->AddOnDeleteCall(call_obj);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

PyTypeObject PythonClassWidget::type_obj;
PyMethodDef PythonClassWidget::tp_methods[] = {
    {"exists", (PyCFunction)Exists, METH_NOARGS,
     "exists() -> bool\n"
     "\n"
     "Returns whether the Widget still exists.\n"
     "Most functionality will fail on a nonexistent widget.\n"
     "\n"
     "Note that you can also use the boolean operator for this same\n"
     "functionality, so a statement such as \"if mywidget\" will do\n"
     "the right thing both for Widget objects and values of None."},
    {"get_widget_type", (PyCFunction)GetWidgetType, METH_NOARGS,
     "get_widget_type() -> str\n"
     "\n"
     "Return the internal type of the Widget as a string. Note that this\n"
     "is different from the Python ba.Widget type, which is the same for\n"
     "all widgets."},
    {"activate", (PyCFunction)Activate, METH_NOARGS,
     "activate() -> None\n"
     "\n"
     "Activates a widget; the same as if it had been clicked."},
    {"get_children", (PyCFunction)GetChildren, METH_NOARGS,
     "get_children() -> list[ba.Widget]\n"
     "\n"
     "Returns any child Widgets of this Widget."},
    {"get_screen_space_center", (PyCFunction)GetScreenSpaceCenter, METH_NOARGS,
     "get_screen_space_center() -> tuple[float, float]\n"
     "\n"
     "Returns the coords of the ba.Widget center relative to the center\n"
     "of the screen. This can be useful for placing pop-up windows and other\n"
     "special cases."},
    {"get_selected_child", (PyCFunction)GetSelectedChild, METH_NOARGS,
     "get_selected_child() -> ba.Widget | None\n"
     "\n"
     "Returns the selected child Widget or None if nothing is selected."},
    // NOLINTNEXTLINE (signed bitwise stuff)
    {"delete", (PyCFunction)Delete, METH_VARARGS | METH_KEYWORDS,
     "delete(ignore_missing: bool = True) -> None\n"
     "\n"
     "Delete the Widget. Ignores already-deleted Widgets if ignore_missing\n"
     "is True; otherwise an Exception is thrown."},
    {"add_delete_callback", (PyCFunction)AddDeleteCallback,
     METH_VARARGS | METH_KEYWORDS,  // NOLINT (signed bitwise stuff)
     "add_delete_callback(call: Callable) -> None\n"
     "\n"
     "Add a call to be run immediately after this widget is destroyed."},
    {nullptr}};

}  // namespace ballistica
