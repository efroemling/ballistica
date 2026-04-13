// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/python/class/python_class_display_timer.h"

#include <string>

#include "ballistica/base/logic/logic.h"
#include "ballistica/base/python/base_python.h"
#include "ballistica/base/python/support/python_context_call_runnable.h"
#include "ballistica/shared/foundation/event_loop.h"

namespace ballistica::base {

auto PythonClassDisplayTimer::type_name() -> const char* {
  return "DisplayTimer";
}

void PythonClassDisplayTimer::SetupType(PyTypeObject* cls) {
  PythonClass::SetupType(cls);
  // Fully qualified type path we will be exposed as:
  cls->tp_name = "babase.DisplayTimer";
  cls->tp_basicsize = sizeof(PythonClassDisplayTimer);
  cls->tp_doc =
      "DisplayTimer(time: float, call: Callable[[], Any], repeat: bool = "
      "False)\n"
      "\n"
      "Timers are used to run code at later points in time.\n"
      "\n"
      "This class encapsulates a timer based on display-time.\n"
      "The underlying timer will be destroyed when this object is no longer\n"
      "referenced. If you do not want to worry about keeping a reference to\n"
      "your timer around, use the :meth:`~babase.displaytimer()` function\n"
      "instead to get a one-off timer.\n"
      "\n"
      "Display-time is a time value intended to be used for animation and\n"
      "other visual purposes. It will generally increment by a consistent\n"
      "amount each frame. It will pass at an overall similar rate to AppTime,\n"
      "but trades accuracy for smoothness.\n"
      "\n"
      "Args:\n"
      "\n"
      "  time:\n"
      "    Length of time in seconds that the timer will wait before firing.\n"
      "\n"
      "  call:\n"
      "    A callable Python object. Remember that the timer will retain a\n"
      "    strong reference to the callable for as long as it exists, so you\n"
      "    may want to look into concepts such as :class:`~babase.WeakCall`\n"
      "    if that is not desired.\n"
      "\n"
      "  repeat:\n"
      "    If True, the timer will fire repeatedly, with each successive\n"
      "    firing having the same delay as the first.\n"
      "\n"
      "Example: Use a Timer object to print repeatedly for a few seconds::\n"
      "\n"
      "    def say_it():\n"
      "        babase.screenmessage('BADGER!')\n"
      "\n"
      "    def stop_saying_it():\n"
      "        global g_timer\n"
      "        g_timer = None\n"
      "        babase.screenmessage('MUSHROOM MUSHROOM!')\n"
      "\n"
      "    # Create our timer; it will run as long as we keep its ref alive.\n"
      "    g_timer = babase.DisplayTimer(0.3, say_it, repeat=True)\n"
      "\n"
      "    # Now fire off a one-shot timer to kill the ref.\n"
      "    babase.displaytimer(3.89, stop_saying_it)\n";
  cls->tp_new = tp_new;
  cls->tp_dealloc = (destructor)tp_dealloc;
}

auto PythonClassDisplayTimer::tp_new(PyTypeObject* type, PyObject* args,
                                     PyObject* keywds) -> PyObject* {
  PythonClassDisplayTimer* self{};
  BA_PYTHON_TRY;

  if (!g_base->InLogicThread()) {
    throw Exception(
        "ERROR: " + std::string(type_obj.tp_name)
        + " objects must only be created in the logic thread (current is ("
        + g_core->CurrentThreadName() + ").");
  }

  double length;
  int repeat{};
  PyObject* call_obj{};
  static const char* kwlist[] = {"time", "call", "repeat", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "dO|p",
                                   const_cast<char**>(kwlist), &length,
                                   &call_obj, &repeat)) {
    return nullptr;
  }
  BasePython::EnsureContextAllowsDefaultTimerTypes();
  if (length < 0) {
    throw Exception("Timer length cannot be < 0.", PyExcType::kValue);
  }

  auto runnable(Object::New<Runnable, PythonContextCallRunnable>(call_obj));

  self = reinterpret_cast<PythonClassDisplayTimer*>(type->tp_alloc(type, 0));
  if (!self) {
    return nullptr;
  }
  self->timer_id_ = g_base->logic->NewDisplayTimer(
      static_cast<microsecs_t>(length * 1000000.0), repeat,
      Object::New<Runnable, PythonContextCallRunnable>(call_obj).get());

  self->have_timer_ = true;

  return reinterpret_cast<PyObject*>(self);
  BA_PYTHON_NEW_CATCH;
}

void PythonClassDisplayTimer::tp_dealloc(PythonClassDisplayTimer* self) {
  BA_PYTHON_TRY;

  // These have to be deleted in the logic thread.
  if (g_base->InLogicThread()) {
    g_base->logic->DeleteDisplayTimer(self->timer_id_);
  } else {
    g_base->logic->event_loop()->PushCall(
        [tid = self->timer_id_] { g_base->logic->DeleteDisplayTimer(tid); });
  }

  BA_PYTHON_DEALLOC_CATCH;
  Py_TYPE(self)->tp_free(reinterpret_cast<PyObject*>(self));
}

PyTypeObject PythonClassDisplayTimer::type_obj;

}  // namespace ballistica::base
