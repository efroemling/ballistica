// Released under the MIT License. See LICENSE for details.

#include "ballistica/python/class/python_class_context.h"

#include "ballistica/core/thread.h"
#include "ballistica/game/game.h"
#include "ballistica/game/host_activity.h"
#include "ballistica/game/session/host_session.h"
#include "ballistica/python/python.h"
#include "ballistica/ui/ui.h"

namespace ballistica {

void PythonClassContext::SetupType(PyTypeObject* obj) {
  PythonClass::SetupType(obj);
  obj->tp_name = "ba.Context";
  obj->tp_basicsize = sizeof(PythonClassContext);
  obj->tp_doc =
      "Context(source: Any)\n"
      "\n"
      "A game context state.\n"
      "\n"
      "Category: **General Utility Classes**\n"
      "\n"
      "Many operations such as ba.newnode() or ba.gettexture() operate\n"
      "implicitly on the current context. Each ba.Activity has its own\n"
      "Context and objects within that activity (nodes, media, etc) can only\n"
      "interact with other objects from that context.\n"
      "\n"
      "In general, as a modder, you should not need to worry about contexts,\n"
      "since timers and other callbacks will take care of saving and\n"
      "restoring the context automatically, but there may be rare cases where\n"
      "you need to deal with them, such as when loading media in for use in\n"
      "the UI (there is a special `'ui'` context for all\n"
      "user-interface-related functionality).\n"
      "\n"
      "When instantiating a ba.Context instance, a single `'source'` "
      "argument\n"
      "is passed, which can be one of the following strings/objects:\n\n"
      "###### `'empty'`\n"
      "> Gives an empty context; it can be handy to run code here to ensure\n"
      "it does no loading of media, creation of nodes, etc.\n"
      "\n"
      "###### `'current'`\n"
      "> Sets the context object to the current context.\n"
      "\n"
      "###### `'ui'`\n"
      "> Sets to the UI context. UI functions as well as loading of media to\n"
      "be used in said functions must happen in the UI context.\n"
      "\n"
      "###### A ba.Activity instance\n"
      "> Gives the context for the provided ba.Activity.\n"
      "  Most all code run during a game happens in an Activity's Context.\n"
      "\n"
      "###### A ba.Session instance\n"
      "> Gives the context for the provided ba.Session.\n"
      "Generally a user should not need to run anything here.\n"
      "\n"
      "\n"
      "##### Usage\n"
      "Contexts are generally used with the python 'with' statement, which\n"
      "sets the context as current on entry and resets it to the previous\n"
      "value on exit.\n"
      "\n"
      "##### Example\n"
      "Load a few textures into the UI context\n"
      "(for use in widgets, etc):\n"
      ">>> with ba.Context('ui'):\n"
      "...     tex1 = ba.gettexture('foo_tex_1')\n"
      "...     tex2 = ba.gettexture('foo_tex_2')\n";

  obj->tp_new = tp_new;
  obj->tp_dealloc = (destructor)tp_dealloc;
  obj->tp_repr = (reprfunc)tp_repr;
  obj->tp_richcompare = (richcmpfunc)tp_richcompare;
  obj->tp_methods = tp_methods;
}

auto PythonClassContext::tp_repr(PythonClassContext* self) -> PyObject* {
  BA_PYTHON_TRY;

  std::string context_str;
  if (self->context_->GetUIContext()) {
    context_str = "ui";
  } else if (HostActivity* ha = self->context_->GetHostActivity()) {
    PythonRef ha_obj(ha->GetPyActivity(), PythonRef::kAcquire);
    if (ha_obj.get() != Py_None) {
      context_str = ha_obj.Str();
    } else {
      context_str = ha->GetObjectDescription();
    }
  } else if (self->context_->target.exists()) {
    context_str = self->context_->target->GetObjectDescription();
  } else {
    context_str = "empty";
  }
  context_str = "<ba.Context (" + context_str + ")>";
  return PyUnicode_FromString(context_str.c_str());
  BA_PYTHON_CATCH;
}

auto PythonClassContext::tp_richcompare(PythonClassContext* c1, PyObject* c2,
                                        int op) -> PyObject* {
  // always return false against other types
  if (!Check(c2)) {
    Py_RETURN_FALSE;
  }
  bool eq = (*(c1->context_)
             == *((reinterpret_cast<PythonClassContext*>(c2))->context_));
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

auto PythonClassContext::tp_new(PyTypeObject* type, PyObject* args,
                                PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  PyObject* source_obj = Py_None;
  if (!PyArg_ParseTuple(args, "O", &source_obj)) {
    return nullptr;
  }

  if (!InLogicThread()) {
    throw Exception(
        "ERROR: " + std::string(type_obj.tp_name)
        + " objects must only be created in the game thread (current is ("
        + GetCurrentThreadName() + ").");
  }

  Context cs(nullptr);

  if (Python::IsPyString(source_obj)) {
    std::string source = Python::GetPyString(source_obj);
    if (source == "ui") {
      cs = Context(g_game->GetUIContextTarget());
    } else if (source == "UI") {
      BA_LOG_ONCE("'UI' context-target option is deprecated; please use 'ui'");
      Python::PrintStackTrace();
      cs = Context(g_game->GetUIContextTarget());
    } else if (source == "current") {
      cs = Context::current();
    } else if (source == "empty") {
      cs = Context(nullptr);
    } else {
      throw Exception("invalid context identifier: '" + source + "'");
    }
  } else if (Python::IsPyHostActivity(source_obj)) {
    cs = Context(Python::GetPyHostActivity(source_obj));
  } else if (Python::IsPySession(source_obj)) {
    auto* hs = dynamic_cast<HostSession*>(Python::GetPySession(source_obj));
    assert(hs != nullptr);
    cs = Context(hs);
  } else {
    throw Exception(
        "Invalid argument to ba.Context(): " + Python::ObjToString(source_obj)
        + "; expected 'ui', 'current', 'empty', a ba.Activity, or a "
          "ba.Session");
  }

  auto* self = reinterpret_cast<PythonClassContext*>(type->tp_alloc(type, 0));
  if (self) {
    BA_PYTHON_TRY;
    self->context_ = new Context(cs);
    self->context_prev_ = new Context();
    BA_PYTHON_NEW_CATCH;
  }
  return reinterpret_cast<PyObject*>(self);
  BA_PYTHON_CATCH;
}

void PythonClassContext::tp_dealloc(PythonClassContext* self) {
  BA_PYTHON_TRY;
  // Contexts have to be deleted in the game thread;
  // ship them to it for deletion if need be; otherwise do it immediately.
  if (!InLogicThread()) {
    Context* c = self->context_;
    Context* c2 = self->context_prev_;
    g_game->thread()->PushCall([c, c2] {
      delete c;
      delete c2;
    });
  } else {
    delete self->context_;
    delete self->context_prev_;
  }
  BA_PYTHON_DEALLOC_CATCH;
  Py_TYPE(self)->tp_free(reinterpret_cast<PyObject*>(self));
}

auto PythonClassContext::__enter__(PythonClassContext* self) -> PyObject* {
  BA_PYTHON_TRY;
  *(self->context_prev_) = Context::current();
  Context::set_current(*(self->context_));
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PythonClassContext::__exit__(PythonClassContext* self, PyObject* args)
    -> PyObject* {
  BA_PYTHON_TRY;
  Context::set_current(*(self->context_prev_));
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

PyTypeObject PythonClassContext::type_obj;
PyMethodDef PythonClassContext::tp_methods[] = {
    {"__enter__", (PyCFunction)__enter__, METH_NOARGS,
     "enter call for 'with' functionality"},
    {"__exit__", (PyCFunction)__exit__, METH_VARARGS,
     "exit call for 'with' functionality"},
    {nullptr}};

}  // namespace ballistica
