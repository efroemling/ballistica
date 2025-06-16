// Released under the MIT License. See LICENSE for details.

#include "ballistica/ui_v1/python/class/python_class_widget.h"

#include <string>

#include "ballistica/base/graphics/graphics.h"
#include "ballistica/base/logic/logic.h"
#include "ballistica/base/ui/ui.h"
#include "ballistica/shared/foundation/event_loop.h"
#include "ballistica/shared/foundation/macros.h"
#include "ballistica/shared/generic/utils.h"
#include "ballistica/ui_v1/widget/container_widget.h"

namespace ballistica::ui_v1 {

auto PythonClassWidget::nb_bool(PythonClassWidget* self) -> int {
  return self->widget_->exists();
}

PyNumberMethods PythonClassWidget::as_number_;

// Attrs we expose through our custom getattr/setattr.
#define ATTR_TRANSITIONING_OUT "transitioning_out"

// The set we expose via dir().
static const char* extra_dir_attrs[] = {ATTR_TRANSITIONING_OUT, nullptr};

auto PythonClassWidget::type_name() -> const char* { return "Widget"; }

void PythonClassWidget::SetupType(PyTypeObject* cls) {
  PythonClass::SetupType(cls);
  // Fully qualified type path we will be exposed as:
  cls->tp_name = "bauiv1.Widget";
  cls->tp_basicsize = sizeof(PythonClassWidget);

  // clang-format off

  cls->tp_doc =
      "Internal type for low level UI elements; buttons, windows, etc.\n"
      "\n"
      "This class represents a weak reference to a widget object\n"
      "in the internal C++ layer. Currently, functions such as\n"
      "bauiv1.buttonwidget() must be used to instantiate or edit these.\n"
      "Attributes:\n"
      "    " ATTR_TRANSITIONING_OUT " (bool):\n"
      "        Whether this widget is in the process of dying (read only).\n"
      "\n"
      "        It can be useful to check this on a window's root widget to\n"
      "        prevent multiple window actions from firing simultaneously,\n"
      "        potentially leaving the UI in a broken state.\n";

  // clang-format on

  cls->tp_new = tp_new;
  cls->tp_dealloc = (destructor)tp_dealloc;
  cls->tp_repr = (reprfunc)tp_repr;
  cls->tp_methods = tp_methods;
  cls->tp_getattro = (getattrofunc)tp_getattro;

  // we provide number methods only for bool functionality
  memset(&as_number_, 0, sizeof(as_number_));
  as_number_.nb_bool = (inquiry)nb_bool;
  cls->tp_as_number = &as_number_;
}

auto PythonClassWidget::Create(Widget* widget) -> PyObject* {
  // Make sure we only have one Python ref per Widget.
  if (widget) {
    assert(!widget->HasPyRef());
  }

  assert(TypeIsSetUp(&type_obj));
  auto* py_widget = reinterpret_cast<PythonClassWidget*>(
      PyObject_CallObject(reinterpret_cast<PyObject*>(&type_obj), nullptr));
  if (!py_widget) {
    throw Exception("bauiv1.Widget creation failed");
  }

  *py_widget->widget_ = widget;

  auto* out = reinterpret_cast<PyObject*>(py_widget);
  return out;
}

auto PythonClassWidget::GetWidget() const -> Widget* {
  Widget* w = widget_->get();
  if (!w) {
    throw Exception("Invalid Widget", PyExcType::kReference);
  }
  return w;
}

auto PythonClassWidget::tp_getattro(PythonClassWidget* self, PyObject* attr)
    -> PyObject* {
  BA_PYTHON_TRY;

  BA_PRECONDITION(g_base->InLogicThread());

  // Assuming this will always be a str?
  assert(PyUnicode_Check(attr));

  const char* s = PyUnicode_AsUTF8(attr);
  if (!strcmp(s, ATTR_TRANSITIONING_OUT)) {
    Widget* w = self->widget_->get();
    if (!w) {
      throw Exception("Invalid Widget", PyExcType::kReference);
    }
    if (w->IsTransitioningOut()) {
      Py_RETURN_TRUE;
    }
    Py_RETURN_FALSE;
  }

  // Fall back to generic behavior.
  PyObject* val;
  val = PyObject_GenericGetAttr(reinterpret_cast<PyObject*>(self), attr);
  return val;
  BA_PYTHON_CATCH;
}

auto PythonClassWidget::tp_setattro(PythonClassWidget* self, PyObject* attr,
                                    PyObject* val) -> int {
  BA_PYTHON_TRY;

  BA_PRECONDITION(g_base->InLogicThread());

  // Assuming this will always be a str?
  assert(PyUnicode_Check(attr));

  throw Exception("Attr '" + std::string(PyUnicode_AsUTF8(attr))
                      + "' is not settable on SessionPlayer objects.",
                  PyExcType::kAttribute);
  BA_PYTHON_INT_CATCH;
}

auto PythonClassWidget::tp_repr(PythonClassWidget* self) -> PyObject* {
  BA_PYTHON_TRY;
  Widget* w = self->widget_->get();
  return Py_BuildValue("s", (std::string("<bauiv1 '")
                             + (w ? w->GetWidgetTypeName() : "<invalid>")
                             + "' widget " + Utils::PtrToString(w) + ">")
                                .c_str());
  BA_PYTHON_CATCH;
}

auto PythonClassWidget::tp_new(PyTypeObject* type, PyObject* args,
                               PyObject* keywds) -> PyObject* {
  auto* self = reinterpret_cast<PythonClassWidget*>(type->tp_alloc(type, 0));
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
  self->widget_ = new Object::WeakRef<Widget>();
  return reinterpret_cast<PyObject*>(self);
  BA_PYTHON_NEW_CATCH;
}

void PythonClassWidget::tp_dealloc(PythonClassWidget* self) {
  BA_PYTHON_TRY;
  // these have to be destructed in the logic thread - send them along to it
  // if need be
  if (!g_base->InLogicThread()) {
    Object::WeakRef<Widget>* w = self->widget_;
    g_base->logic->event_loop()->PushCall([w] { delete w; });
  } else {
    delete self->widget_;
  }
  BA_PYTHON_DEALLOC_CATCH;
  Py_TYPE(self)->tp_free(reinterpret_cast<PyObject*>(self));
}

auto PythonClassWidget::Exists(PythonClassWidget* self) -> PyObject* {
  BA_PYTHON_TRY;
  BA_PRECONDITION(g_base->InLogicThread());
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
  BA_PRECONDITION(g_base->InLogicThread());
  Widget* w = self->widget_->get();
  if (!w) {
    throw Exception(PyExcType::kWidgetNotFound);
  }
  return PyUnicode_FromString(w->GetWidgetTypeName().c_str());
  BA_PYTHON_CATCH;
}

auto PythonClassWidget::Activate(PythonClassWidget* self) -> PyObject* {
  BA_PYTHON_TRY;
  BA_PRECONDITION(g_base->InLogicThread());
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
  BA_PRECONDITION(g_base->InLogicThread());
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
  BA_PRECONDITION(g_base->InLogicThread());
  Widget* w = self->widget_->get();
  if (!w) {
    throw Exception(PyExcType::kWidgetNotFound);
  }
  if (auto* cw = dynamic_cast<ContainerWidget*>(w)) {
    if (Widget* selected_widget = cw->selected_widget()) {
      return selected_widget->NewPyRef();
    }
  }
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PythonClassWidget::GetScreenSpaceCenter(PythonClassWidget* self)
    -> PyObject* {
  BA_PYTHON_TRY;
  BA_PRECONDITION(g_base->InLogicThread());
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
  float screen_width = g_base->graphics->screen_virtual_width();
  float screen_height = g_base->graphics->screen_virtual_height();
  x -= screen_width * 0.5f;
  y -= screen_height * 0.5f;
  return Py_BuildValue("(ff)", x, y);
  BA_PYTHON_CATCH;
}

auto PythonClassWidget::Delete(PythonClassWidget* self, PyObject* args,
                               PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  BA_PRECONDITION(g_base->InLogicThread());
  int ignore_missing = true;
  static const char* kwlist[] = {"ignore_missing", nullptr};
  if (!PyArg_ParseTupleAndKeywords(
          args, keywds, "|i", const_cast<char**>(kwlist), &ignore_missing)) {
    return nullptr;
  }

  // Defer any user code triggered by selects/etc until the end.
  base::UI::OperationContext ui_op_context;

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
      g_core->logging->Log(LogName::kBa, LogLevel::kError,
                           "Can't delete widget: no parent.");
    }
  }

  // Run any user code that got triggered.
  ui_op_context.Finish();
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PythonClassWidget::AddDeleteCallback(PythonClassWidget* self,
                                          PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  BA_PRECONDITION(g_base->InLogicThread());
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

auto PythonClassWidget::Dir(PythonClassWidget* self) -> PyObject* {
  BA_PYTHON_TRY;

  // Start with the standard Python dir listing.
  PyObject* dir_list = Python::generic_dir(reinterpret_cast<PyObject*>(self));
  assert(PyList_Check(dir_list));

  // ..and add in our custom attr names.
  for (const char** name = extra_dir_attrs; *name != nullptr; name++) {
    PyList_Append(
        dir_list,
        PythonRef(PyUnicode_FromString(*name), PythonRef::kSteal).get());
  }
  PyList_Sort(dir_list);
  return dir_list;

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
     "is different from the Python bauiv1.Widget type, which is the same for\n"
     "all widgets."},
    {"activate", (PyCFunction)Activate, METH_NOARGS,
     "activate() -> None\n"
     "\n"
     "Activates a widget; the same as if it had been clicked."},
    {"get_children", (PyCFunction)GetChildren, METH_NOARGS,
     "get_children() -> list[bauiv1.Widget]\n"
     "\n"
     "Returns any child Widgets of this Widget."},
    {"get_screen_space_center", (PyCFunction)GetScreenSpaceCenter, METH_NOARGS,
     "get_screen_space_center() -> tuple[float, float]\n"
     "\n"
     "Returns the coords of the bauiv1.Widget center relative to the center\n"
     "of the screen. This can be useful for placing pop-up windows and other\n"
     "special cases."},
    {"get_selected_child", (PyCFunction)GetSelectedChild, METH_NOARGS,
     "get_selected_child() -> bauiv1.Widget | None\n"
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
    {"__dir__", (PyCFunction)Dir, METH_NOARGS,
     "allows inclusion of our custom attrs in standard python dir()"},
    {nullptr}};

}  // namespace ballistica::ui_v1
