// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/python/class/python_class_scene_timer.h"

#include <string>

#include "ballistica/base/logic/logic.h"
#include "ballistica/base/python/support/python_context_call_runnable.h"
#include "ballistica/scene_v1/support/scene_v1_context.h"
#include "ballistica/shared/foundation/event_loop.h"

namespace ballistica::scene_v1 {

auto PythonClassSceneTimer::type_name() -> const char* { return "Timer"; }

void PythonClassSceneTimer::SetupType(PyTypeObject* cls) {
  PythonClass::SetupType(cls);
  // Fully qualified type path we will be exposed as:
  cls->tp_name = "bascenev1.Timer";
  cls->tp_basicsize = sizeof(PythonClassSceneTimer);
  cls->tp_doc =
      "Timer(time: float, call: Callable[[], Any], repeat: bool = False)\n"
      "\n"
      "Timers are used to run code at later points in time.\n"
      "\n"
      "This class encapsulates a scene-time timer in the current\n"
      "bascenev1.Context. The underlying timer will be destroyed when either\n"
      "this object is no longer referenced or when its Context (Activity,\n"
      "etc.) dies. If you do not want to worry about keeping a reference to\n"
      "your timer around,\n"
      "you should use the bs.timer() function instead.\n"
      "\n"
      "Scene time maps to local simulation time in bascenev1.Activity or\n"
      "bascenev1.Session Contexts. This means that it may progress slower\n"
      "in slow-motion play modes, stop when the game is paused, etc.\n"
      "\n"
      "Args:\n"
      "\n"
      "  time:\n"
      "    Length of time (in seconds by default) that the timer will wait\n"
      "    before firing. Note that the actual delay experienced may vary\n"
      "    depending on the timetype. (see below)\n"
      "\n"
      "  call:\n"
      "    A callable Python object. Note that the timer will retain a\n"
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
      "    import bascenev1 as bs\n"
      "\n"
      "    def say_it():\n"
      "        bs.screenmessage('BADGER!')\n"
      "\n"
      "    def stop_saying_it():\n"
      "        global g_timer\n"
      "        g_timer = None\n"
      "        bs.screenmessage('MUSHROOM MUSHROOM!')\n"
      "\n"
      "    # Create our timer; it will run as long as we hold its ref.\n"
      "    g_timer = bs.Timer(0.3, say_it, repeat=True)\n"
      "\n"
      "    # Now fire off a one-shot timer to kill the ref.\n"
      "    bs.timer(3.89, stop_saying_it)\n";
  cls->tp_new = tp_new;
  cls->tp_dealloc = (destructor)tp_dealloc;
}

auto PythonClassSceneTimer::tp_new(PyTypeObject* type, PyObject* args,
                                   PyObject* keywds) -> PyObject* {
  auto* self =
      reinterpret_cast<PythonClassSceneTimer*>(type->tp_alloc(type, 0));
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
      TimeType::kSim, static_cast<millisecs_t>(length * 1000.0),
      static_cast<bool>(repeat),
      Object::New<Runnable, base::PythonContextCallRunnable>(call_obj).get());
  self->have_timer_ = true;

  return reinterpret_cast<PyObject*>(self);
  BA_PYTHON_NEW_CATCH;
}

static void DoDelete(bool have_timer, int timer_id,
                     ContextRefSceneV1* context_ref) {
  assert(g_base->InLogicThread());
  if (!context_ref) {
    return;
  }
  auto* context = context_ref->GetContextTyped<SceneV1Context>();
  if (have_timer && context) {
    context->DeleteTimer(TimeType::kSim, timer_id);
  }
  delete context_ref;
}

void PythonClassSceneTimer::tp_dealloc(PythonClassSceneTimer* self) {
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

PyTypeObject PythonClassSceneTimer::type_obj;

}  // namespace ballistica::scene_v1
