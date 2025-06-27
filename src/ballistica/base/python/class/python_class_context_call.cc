// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/python/class/python_class_context_call.h"

#include <string>

#include "ballistica/base/logic/logic.h"
#include "ballistica/base/python/support/python_context_call.h"
#include "ballistica/shared/foundation/event_loop.h"

namespace ballistica::base {

auto PythonClassContextCall::type_name() -> const char* {
  return "ContextCall";
}

void PythonClassContextCall::SetupType(PyTypeObject* cls) {
  PythonClass::SetupType(cls);
  // Fully qualified type path we will be exposed as:
  cls->tp_name = "babase.ContextCall";
  cls->tp_basicsize = sizeof(PythonClassContextCall);
  cls->tp_doc =
      "ContextCall(call: Callable)\n"
      "\n"
      "A context-preserving callable.\n"
      "\n"
      "This wraps a callable object along with a reference to the current\n"
      "context (see :class:`~babase.ContextRef`); it handles restoring the\n"
      "context when run and automatically clears itself if the context it\n"
      "belongs to dies.\n"
      "\n"
      "Generally you should not need to use this directly; all standard\n"
      "Ballistica callbacks involved with timers, materials, UI functions,\n"
      "etc. handle this under-the-hood so you don't have to worry about it.\n"
      "The only time it may be necessary is if you are implementing your\n"
      "own callbacks, such as a worker thread that does some action and then\n"
      "runs some engine code when done. By wrapping said callback in one of\n"
      "these, you can ensure that you will not inadvertently be keeping the\n"
      "current activity alive or running code in a torn-down (expired)\n"
      ":class:`~babase.ContextRef`.\n"
      "\n"
      "You can also use :class:`~babase.WeakCall` for similar functionality,\n"
      "but ContextCall has the added bonus that it will not run during\n"
      ":class:`~babase.ContextRef` shutdown, whereas\n"
      ":class:`~babase.WeakCall` simply looks at whether the target object\n"
      "instance still exists.\n"
      "\n"
      "**Example A:** Code like this can inadvertently prevent our activity\n"
      "(self) from ending until the operation completes, since the bound\n"
      "method we're passing (self.dosomething) contains a strong-reference\n"
      "to self)::\n"
      "\n"
      "    start_some_long_action(callback_when_done=self.dosomething)\n"
      "\n"
      "**Example B:** In this case our activity (self) can still die\n"
      "properly; the callback will clear itself when the activity starts\n"
      "shutting down, becoming a harmless no-op and releasing the reference\n"
      "to our activity::\n"
      "\n"
      "    start_long_action(\n"
      "        callback_when_done=babase.ContextCall(self.mycallback))\n";

  cls->tp_new = tp_new;
  cls->tp_dealloc = (destructor)tp_dealloc;
  cls->tp_repr = (reprfunc)tp_repr;
  cls->tp_methods = tp_methods;
  cls->tp_call = (ternaryfunc)tp_call;
}

auto PythonClassContextCall::tp_new(PyTypeObject* type, PyObject* args,
                                    PyObject* keywds) -> PyObject* {
  auto* self =
      reinterpret_cast<PythonClassContextCall*>(type->tp_alloc(type, 0));
  if (!self) {
    return nullptr;
  }
  BA_PYTHON_TRY;

  PyObject* source_obj = Py_None;
  if (!PyArg_ParseTuple(args, "O", &source_obj)) return nullptr;
  if (!g_base->InLogicThread()) {
    throw Exception(
        std::string(type_obj.tp_name)
        + " objects must only be created in the logic thread (current is ("
        + g_core->CurrentThreadName() + ").");
  }
  self->context_call_ = new Object::Ref<PythonContextCall>(
      Object::New<PythonContextCall>(source_obj));
  return reinterpret_cast<PyObject*>(self);
  BA_PYTHON_NEW_CATCH;
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

void PythonClassContextCall::tp_dealloc(PythonClassContextCall* self) {
  BA_PYTHON_TRY;
  // These have to be deleted in the logic thread - send the ptr along if need
  // be; otherwise can do it immediately.
  if (!g_base->InLogicThread()) {
    Object::Ref<PythonContextCall>* ptr = self->context_call_;
    g_base->logic->event_loop()->PushCall([ptr] { delete ptr; });
  } else {
    delete self->context_call_;
  }
  BA_PYTHON_DEALLOC_CATCH;
  Py_TYPE(self)->tp_free(reinterpret_cast<PyObject*>(self));
}

PyTypeObject PythonClassContextCall::type_obj;
PyMethodDef PythonClassContextCall::tp_methods[] = {{nullptr}};

}  // namespace ballistica::base
