// Released under the MIT License. See LICENSE for details.

#include "ballistica/python/class/python_class_context_call.h"

#include "ballistica/game/game.h"
#include "ballistica/python/python_context_call.h"

namespace ballistica {

void PythonClassContextCall::SetupType(PyTypeObject* obj) {
  PythonClass::SetupType(obj);
  obj->tp_name = "ba.ContextCall";
  obj->tp_basicsize = sizeof(PythonClassContextCall);
  obj->tp_doc =
      "ContextCall(call: Callable)\n"
      "\n"
      "A context-preserving callable.\n"
      "\n"
      "Category: **General Utility Classes**\n"
      "\n"
      "A ContextCall wraps a callable object along with a reference\n"
      "to the current context (see ba.Context); it handles restoring the\n"
      "context when run and automatically clears itself if the context\n"
      "it belongs to shuts down.\n"
      "\n"
      "Generally you should not need to use this directly; all standard\n"
      "Ballistica callbacks involved with timers, materials, UI functions,\n"
      "etc. handle this under-the-hood you don't have to worry about it.\n"
      "The only time it may be necessary is if you are implementing your\n"
      "own callbacks, such as a worker thread that does some action and then\n"
      "runs some game code when done. By wrapping said callback in one of\n"
      "these, you can ensure that you will not inadvertently be keeping the\n"
      "current activity alive or running code in a torn-down (expired)\n"
      "context.\n"
      "\n"
      "You can also use ba.WeakCall for similar functionality, but\n"
      "ContextCall has the added bonus that it will not run during context\n"
      "shutdown, whereas ba.WeakCall simply looks at whether the target\n"
      "object still exists.\n"
      "\n"
      "##### Examples\n"
      "**Example A:** code like this can inadvertently prevent our activity\n"
      "(self) from ending until the operation completes, since the bound\n"
      "method we're passing (self.dosomething) contains a strong-reference\n"
      "to self).\n"
      ">>> start_some_long_action(callback_when_done=self.dosomething)\n"
      "\n"
      "**Example B:** in this case our activity (self) can still die\n"
      "properly; the callback will clear itself when the activity starts\n"
      "shutting down, becoming a harmless no-op and releasing the reference\n"
      "to our activity.\n"
      "\n"
      ">>> start_long_action(\n"
      "...     callback_when_done=ba.ContextCall(self.mycallback))\n";

  obj->tp_new = tp_new;
  obj->tp_dealloc = (destructor)tp_dealloc;
  obj->tp_repr = (reprfunc)tp_repr;
  obj->tp_methods = tp_methods;
  obj->tp_call = (ternaryfunc)tp_call;
}

auto PythonClassContextCall::tp_call(PythonClassContextCall* self,
                                     PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  static const char* kwlist[] = {nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "",
                                   const_cast<char**>(kwlist)))
    return nullptr;

  (*(self->context_call_))->Run();

  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PythonClassContextCall::tp_repr(PythonClassContextCall* self)
    -> PyObject* {
  BA_PYTHON_TRY;
  assert(self->context_call_->exists());
  return PyUnicode_FromString(
      ("<ba.ContextCall call="
       + (*(self->context_call_))->GetObjectDescription() + ">")
          .c_str());
  BA_PYTHON_CATCH;
}

auto PythonClassContextCall::tp_new(PyTypeObject* type, PyObject* args,
                                    PyObject* keywds) -> PyObject* {
  auto* self =
      reinterpret_cast<PythonClassContextCall*>(type->tp_alloc(type, 0));
  if (self) {
    BA_PYTHON_TRY;

    // try to do anything that may throw an exception before/during our
    // placement-new so we don't have to worry about tearing it down if
    // something goes wrong afterwards
    PyObject* source_obj = Py_None;
    if (!PyArg_ParseTuple(args, "O", &source_obj)) return nullptr;
    if (!InLogicThread()) {
      throw Exception(
          "ERROR: " + std::string(type_obj.tp_name)
          + " objects must only be created in the game thread (current is ("
          + GetCurrentThreadName() + ").");
    }
    self->context_call_ = new Object::Ref<PythonContextCall>(
        Object::New<PythonContextCall>(source_obj));
    BA_PYTHON_NEW_CATCH;
  }
  return reinterpret_cast<PyObject*>(self);
}

void PythonClassContextCall::tp_dealloc(PythonClassContextCall* self) {
  BA_PYTHON_TRY;
  // these have to be deleted in the game thread - send the ptr along if need
  // be; otherwise do it immediately
  if (!InLogicThread()) {
    Object::Ref<PythonContextCall>* c = self->context_call_;
    g_game->PushCall([c] { delete c; });
  } else {
    delete self->context_call_;
  }
  BA_PYTHON_DEALLOC_CATCH;
  Py_TYPE(self)->tp_free(reinterpret_cast<PyObject*>(self));
}

PyTypeObject PythonClassContextCall::type_obj;
PyMethodDef PythonClassContextCall::tp_methods[] = {{nullptr}};

}  // namespace ballistica
