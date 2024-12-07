// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/python/class/python_class_context_ref.h"

#include <string>

#include "ballistica/base/logic/logic.h"
#include "ballistica/shared/foundation/event_loop.h"

namespace ballistica::base {

auto PythonClassContextRef::type_name() -> const char* { return "ContextRef"; }

void PythonClassContextRef::SetupType(PyTypeObject* cls) {
  PythonClass::SetupType(cls);
  // Fully qualified type path we will be exposed as:
  cls->tp_name = "babase.ContextRef";
  cls->tp_basicsize = sizeof(PythonClassContextRef);
  cls->tp_doc =
      "ContextRef()\n"
      "\n"
      "Store or use a ballistica context.\n"
      "\n"
      "Category: **General Utility Classes**\n"
      "\n"
      "Many operations such as bascenev1.newnode() or bascenev1.gettexture()\n"
      "operate implicitly on a current 'context'. A context is some sort of\n"
      "state that functionality can implicitly use. Context determines, for\n"
      "example, which scene nodes or textures get added to without having to\n"
      "specify it explicitly in the newnode()/gettexture() call. Contexts can\n"
      "also affect object lifecycles; for example a babase.ContextCall will\n"
      "become a no-op when the context it was created in is destroyed.\n"
      "\n"
      "In general, if you are a modder, you should not need to worry about\n"
      "contexts; mod code should mostly be getting run in the correct\n"
      "context and timers and other callbacks will take care of saving\n"
      "and restoring contexts automatically. There may be rare cases,\n"
      "however, where you need to deal directly with contexts, and that is\n"
      "where this class comes in.\n"
      "\n"
      "Creating a babase.ContextRef() will capture a reference to the current\n"
      "context. Other modules may provide ways to access their contexts; for\n"
      "example a bascenev1.Activity instance has a 'context' attribute. You\n"
      "can also use babase.ContextRef.empty() to create a reference to *no*\n"
      "context. Some code such as UI calls may expect this and may complain\n"
      "if you try to use them within a context.\n"
      "\n"
      "##### Usage\n"
      "ContextRefs are generally used with the Python 'with' statement, which\n"
      "sets the context they point to as current on entry and resets it to\n"
      "the previous value on exit.\n"
      "\n"
      "##### Example\n"
      "Explicitly create a few UI bits with no context set.\n"
      "(UI stuff may complain if called within a context):\n"
      ">>> with bui.ContextRef.empty():\n"
      "...     my_container = bui.containerwidget()\n";

  cls->tp_new = tp_new;
  cls->tp_dealloc = (destructor)tp_dealloc;
  cls->tp_repr = (reprfunc)tp_repr;
  cls->tp_richcompare = (richcmpfunc)tp_richcompare;
  cls->tp_methods = tp_methods;
}

auto PythonClassContextRef::tp_repr(PythonClassContextRef* self) -> PyObject* {
  BA_PYTHON_TRY;

  auto context_str =
      "<ba.Context (" + self->context_ref_->GetDescription() + ")>";
  return PyUnicode_FromString(context_str.c_str());
  BA_PYTHON_CATCH;
}

auto PythonClassContextRef::tp_richcompare(PythonClassContextRef* c1,
                                           PyObject* c2, int op) -> PyObject* {
  // always return false against other types
  if (!Check(c2)) {
    Py_RETURN_FALSE;
  }
  bool eq = (*c1->context_ref_
             == *reinterpret_cast<PythonClassContextRef*>(c2)->context_ref_);
  if (op == Py_EQ) {
    if (eq) {
      Py_RETURN_TRUE;
    } else {
      Py_RETURN_FALSE;
    }
  } else if (op == Py_NE) {
    if (!eq) {
      Py_RETURN_TRUE;
    } else {
      Py_RETURN_FALSE;
    }
  } else {
    // don't support other ops
    Py_RETURN_NOTIMPLEMENTED;
  }
}

auto PythonClassContextRef::tp_new(PyTypeObject* type, PyObject* args,
                                   PyObject* keywds) -> PyObject* {
  PythonClassContextRef* self{};
  BA_PYTHON_TRY;
  if (!PyArg_ParseTuple(args, "")) {
    return nullptr;
  }

  if (!g_base->InLogicThread()) {
    throw Exception(
        "ERROR: " + std::string(type_obj.tp_name)
        + " objects must only be created in the logic thread (current is ("
        + CurrentThreadName() + ").");
  }

  auto cs = g_base->CurrentContext();

  self = reinterpret_cast<PythonClassContextRef*>(type->tp_alloc(type, 0));
  if (!self) {
    return nullptr;
  }
  self->context_ref_ = new ContextRef(cs);
  self->context_ref_prev_ = new ContextRef();
  return reinterpret_cast<PyObject*>(self);
  BA_PYTHON_NEW_CATCH;
}

void PythonClassContextRef::tp_dealloc(PythonClassContextRef* self) {
  BA_PYTHON_TRY;
  // Contexts have to be deleted in the logic thread;
  // ship them to it for deletion if need be; otherwise do it immediately.
  if (!g_base->InLogicThread()) {
    ContextRef* c = self->context_ref_;
    ContextRef* c2 = self->context_ref_prev_;
    g_base->logic->event_loop()->PushCall([c, c2] {
      delete c;
      delete c2;
    });
  } else {
    delete self->context_ref_;
    delete self->context_ref_prev_;
  }
  BA_PYTHON_DEALLOC_CATCH;
  Py_TYPE(self)->tp_free(reinterpret_cast<PyObject*>(self));
}

auto PythonClassContextRef::Enter(PythonClassContextRef* self) -> PyObject* {
  BA_PYTHON_TRY;
  *self->context_ref_prev_ = g_base->CurrentContext();
  g_base->SetCurrentContext(*self->context_ref_);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PythonClassContextRef::Exit(PythonClassContextRef* self, PyObject* args)
    -> PyObject* {
  BA_PYTHON_TRY;
  g_base->SetCurrentContext(*self->context_ref_prev_);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PythonClassContextRef::Create(Context* context) -> PyObject* {
  assert(g_base->InLogicThread());
  assert(TypeIsSetUp(&type_obj));
  auto* py_cref = reinterpret_cast<PythonClassContextRef*>(
      PyObject_CallObject(reinterpret_cast<PyObject*>(&type_obj), nullptr));
  if (!py_cref) {
    throw Exception("ContextRef creation failed.");
  }
  py_cref->context_ref_->SetTarget(context);
  return reinterpret_cast<PyObject*>(py_cref);
}

auto PythonClassContextRef::Empty(PyObject* cls, PyObject* args) -> PyObject* {
  BA_PYTHON_TRY;
  if (!PyArg_ParseTuple(args, "")) {
    return nullptr;
  }
  return Create(nullptr);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PythonClassContextRef::IsEmpty(PythonClassContextRef* self) -> PyObject* {
  BA_PYTHON_TRY;
  if (self->context_ref_->IsEmpty()) {
    Py_RETURN_TRUE;
  }
  Py_RETURN_FALSE;
  BA_PYTHON_CATCH;
}

auto PythonClassContextRef::IsExpired(PythonClassContextRef* self)
    -> PyObject* {
  BA_PYTHON_TRY;
  if (self->context_ref_->IsExpired()) {
    Py_RETURN_TRUE;
  }
  Py_RETURN_FALSE;
  BA_PYTHON_CATCH;
}

PyTypeObject PythonClassContextRef::type_obj;
PyMethodDef PythonClassContextRef::tp_methods[] = {
    {"__enter__", (PyCFunction)Enter, METH_NOARGS,
     "enter call for 'with' functionality"},
    {"__exit__", (PyCFunction)Exit, METH_VARARGS,
     "exit call for 'with' functionality"},
    {"empty", (PyCFunction)Empty, METH_VARARGS | METH_CLASS,
     "empty() -> ContextRef\n"
     "\n"
     "Return a ContextRef pointing to no context.\n"
     "\n"
     "This is useful when code should be run free of a context.\n"
     "For example, UI code generally insists on being run this way.\n"
     "Otherwise, callbacks set on the UI could inadvertently stop working\n"
     "due to a game activity ending, which would be unintuitive "
     "behavior."},
    {"is_empty", (PyCFunction)IsEmpty, METH_NOARGS,
     "is_empty() -> bool\n"
     "\n"
     "Whether the context was created as empty."},
    {"is_expired", (PyCFunction)IsExpired, METH_NOARGS,
     "is_expired() -> bool\n"
     "\n"
     "Whether the context has expired."},
    {nullptr}};

}  // namespace ballistica::base
