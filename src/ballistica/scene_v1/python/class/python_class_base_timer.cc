// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/python/class/python_class_base_timer.h"

#include "ballistica/base/logic/logic.h"
#include "ballistica/base/python/support/python_context_call_runnable.h"
#include "ballistica/scene_v1/support/scene_v1_context.h"
#include "ballistica/shared/foundation/event_loop.h"
#include "ballistica/shared/python/python.h"

namespace ballistica::scene_v1 {

auto PythonClassBaseTimer::type_name() -> const char* { return "BaseTimer"; }

void PythonClassBaseTimer::SetupType(PyTypeObject* cls) {
  PythonClass::SetupType(cls);
  // Fully qualified type path we will be exposed as:
  cls->tp_name = "bascenev1.BaseTimer";
  cls->tp_basicsize = sizeof(PythonClassBaseTimer);
  cls->tp_doc =
      "BaseTimer(time: float, call: Callable[[], Any], repeat: bool = False)\n"
      "\n"
      "Timers are used to run code at later points in time.\n"
      "\n"
      "Category: **General Utility Classes**\n"
      "\n"
      "This class encapsulates a base-time timer in the current scene\n"
      "context.\n"
      "The underlying timer will be destroyed when either this object is\n"
      "no longer referenced or when its Context (Activity, etc.) dies. If you\n"
      "do not want to worry about keeping a reference to your timer around,\n"
      "you should use the bascenev1.basetimer() function instead.\n"
      "\n"
      "###### time (float)\n"
      "> Length of time in seconds that the timer will wait\n"
      "before firing.\n"
      "\n"
      "###### call (Callable[[], Any])\n"
      "> A callable Python object. Remember that the timer will retain a\n"
      "strong reference to the callable for as long as it exists, so you\n"
      "may want to look into concepts such as babase.WeakCall if that is not\n"
      "desired.\n"
      "\n"
      "###### repeat (bool)\n"
      "> If True, the timer will fire repeatedly, with each successive\n"
      "firing having the same delay as the first.\n"
      "\n"
      "##### Example\n"
      "\n"
      "Use a BaseTimer object to print repeatedly for a few seconds:\n"
      ">>> import bascenev1 as bs\n"
      "... def say_it():\n"
      "...     bs.screenmessage('BADGER!')\n"
      "... def stop_saying_it():\n"
      "...     global g_timer\n"
      "...     g_timer = None\n"
      "...     bs.screenmessage('MUSHROOM MUSHROOM!')\n"
      "... # Create our timer; it will run as long as we have the self.t ref.\n"
      "... g_timer = bs.BaseTimer(0.3, say_it, repeat=True)\n"
      "... # Now fire off a one-shot timer to kill it.\n"
      "... bs.basetimer(3.89, stop_saying_it)\n";
  cls->tp_new = tp_new;
  cls->tp_dealloc = (destructor)tp_dealloc;
}

auto PythonClassBaseTimer::tp_new(PyTypeObject* type, PyObject* args,
                                  PyObject* keywds) -> PyObject* {
  auto* self = reinterpret_cast<PythonClassBaseTimer*>(type->tp_alloc(type, 0));
  if (!self) {
    return nullptr;
  }
  BA_PYTHON_TRY;

  if (!g_base->InLogicThread()) {
    throw Exception(
        "ERROR: " + std::string(type_obj.tp_name)
        + " objects must only be created in the logic thread (current is ("
        + CurrentThreadName() + ").");
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
  if (length < 0.0) {
    throw Exception("Timer length cannot be < 0.", PyExcType::kValue);
  }
  self->context_ref_ = new ContextRefSceneV1();
  self->timer_id_ = SceneV1Context::Current().NewTimer(
      TimeType::kBase, static_cast<millisecs_t>(length * 1000.0),
      static_cast<bool>(repeat),
      Object::New<Runnable, base::PythonContextCallRunnable>(call_obj).Get());
  self->have_timer_ = true;

  return reinterpret_cast<PyObject*>(self);
  BA_PYTHON_NEW_CATCH;
}

static void DoDelete(bool have_timer, int timer_id,
                     ContextRefSceneV1* context_state) {
  assert(g_base->InLogicThread());
  if (!context_state) {
    return;
  }
  auto* context = context_state->GetContextTyped<SceneV1Context>();
  if (have_timer && context) {
    context->DeleteTimer(TimeType::kBase, timer_id);
  }
  delete context_state;
}

void PythonClassBaseTimer::tp_dealloc(PythonClassBaseTimer* self) {
  BA_PYTHON_TRY;
  // These have to be deleted in the logic thread.
  if (!g_base->InLogicThread()) {
    auto a0 = self->have_timer_;
    auto a1 = self->timer_id_;
    auto a2 = self->context_ref_;
    g_base->logic->event_loop()->PushCall(
        [a0, a1, a2] { DoDelete(a0, a1, a2); });
  } else {
    DoDelete(self->have_timer_, self->timer_id_, self->context_ref_);
  }
  BA_PYTHON_DEALLOC_CATCH;
  Py_TYPE(self)->tp_free(reinterpret_cast<PyObject*>(self));
}

PyTypeObject PythonClassBaseTimer::type_obj;

}  // namespace ballistica::scene_v1
