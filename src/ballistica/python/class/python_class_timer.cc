// Copyright (c) 2011-2020 Eric Froemling

#include "ballistica/python/class/python_class_timer.h"

#include <string>

#include "ballistica/game/game.h"
#include "ballistica/game/host_activity.h"
#include "ballistica/game/session/host_session.h"
#include "ballistica/python/python_context_call_runnable.h"

namespace ballistica {

void PythonClassTimer::SetupType(PyTypeObject* obj) {
  PythonClass::SetupType(obj);
  obj->tp_name = "ba.Timer";
  obj->tp_basicsize = sizeof(PythonClassTimer);
  obj->tp_doc =
      "Timer(time: float, call: Callable[[], Any], repeat: bool = False,\n"
      "  timetype: ba.TimeType = TimeType.SIM,\n"
      "  timeformat: ba.TimeFormat = TimeFormat.SECONDS,\n"
      "  suppress_format_warning: bool = False)\n"
      "\n"
      "Timers are used to run code at later points in time.\n"
      "\n"
      "Category: General Utility Classes\n"
      "\n"
      "This class encapsulates a timer in the current ba.Context.\n"
      "The underlying timer will be destroyed when either this object is\n"
      "no longer referenced or when its Context (Activity, etc.) dies. If you\n"
      "do not want to worry about keeping a reference to your timer around,\n"
      "you should use the ba.timer() function instead.\n"
      "\n"
      "time: length of time (in seconds by default) that the timer will wait\n"
      "before firing. Note that the actual delay experienced may vary\n "
      "depending on the timetype. (see below)\n"
      "\n"
      "call: A callable Python object. Note that the timer will retain a\n"
      "strong reference to the callable for as long as it exists, so you\n"
      "may want to look into concepts such as ba.WeakCall if that is not\n"
      "desired.\n"
      "\n"
      "repeat: if True, the timer will fire repeatedly, with each successive\n"
      "firing having the same delay as the first.\n"
      "\n"
      "timetype can be either 'sim', 'base', or 'real'. It defaults to\n"
      "'sim'. Types are explained below:\n"
      "\n"
      "'sim' time maps to local simulation time in ba.Activity or ba.Session\n"
      "Contexts. This means that it may progress slower in slow-motion play\n"
      "modes, stop when the game is paused, etc.  This time type is not\n"
      "available in UI contexts.\n"
      "\n"
      "'base' time is also linked to gameplay in ba.Activity or ba.Session\n"
      "Contexts, but it progresses at a constant rate regardless of\n "
      "slow-motion states or pausing.  It can, however, slow down or stop\n"
      "in certain cases such as network outages or game slowdowns due to\n"
      "cpu load. Like 'sim' time, this is unavailable in UI contexts.\n"
      "\n"
      "'real' time always maps to actual clock time with a bit of filtering\n"
      "added, regardless of Context.  (the filtering prevents it from going\n"
      "backwards or jumping forward by large amounts due to the app being\n"
      "backgrounded, system time changing, etc.)\n"
      "Real time timers are currently only available in the UI context.\n"
      "\n"
      "the 'timeformat' arg defaults to SECONDS but can also be MILLISECONDS\n"
      "if you want to pass time as milliseconds.\n"
      "\n"
      "# Example: use a Timer object to print repeatedly for a few seconds:\n"
      "def say_it():\n"
      "    ba.screenmessage('BADGER!')\n"
      "def stop_saying_it():\n"
      "    self.t = None\n"
      "    ba.screenmessage('MUSHROOM MUSHROOM!')\n"
      "# create our timer; it will run as long as we hold self.t\n"
      "self.t = ba.Timer(0.3, say_it, repeat=True)\n"
      "# now fire off a one-shot timer to kill it\n"
      "ba.timer(3.89, stop_saying_it)";
  obj->tp_new = tp_new;
  obj->tp_dealloc = (destructor)tp_dealloc;
}

auto PythonClassTimer::tp_new(PyTypeObject* type, PyObject* args,
                              PyObject* keywds) -> PyObject* {
  auto* self = reinterpret_cast<PythonClassTimer*>(type->tp_alloc(type, 0));
  if (self) {
    BA_PYTHON_TRY;

    if (!InGameThread()) {
      throw Exception(
          "ERROR: " + std::string(type_obj.tp_name)
          + " objects must only be created in the game thread (current is ("
          + GetCurrentThreadName() + ").");
    }

    self->context_ = new Context();

    PyObject* length_obj{};
    int64_t length;
    int repeat{};
    int suppress_format_warning{};
    PyObject* call_obj{};
    PyObject* time_type_obj{};
    PyObject* time_format_obj{};
    static const char* kwlist[] = {"time",       "call",
                                   "repeat",     "timetype",
                                   "timeformat", "suppress_format_warning",
                                   nullptr};
    if (!PyArg_ParseTupleAndKeywords(
            args, keywds, "OO|pOOp", const_cast<char**>(kwlist), &length_obj,
            &call_obj, &repeat, &time_type_obj, &time_format_obj,
            &suppress_format_warning)) {
      return nullptr;
    }

    auto time_type = TimeType::kSim;
    if (time_type_obj != nullptr) {
      time_type = Python::GetPyEnum_TimeType(time_type_obj);
    }
    auto time_format = TimeFormat::kSeconds;
    if (time_format_obj != nullptr) {
      time_format = Python::GetPyEnum_TimeFormat(time_format_obj);
    }

#if BA_TEST_BUILD || BA_DEBUG_BUILD
    if (!suppress_format_warning) {
      g_python->TimeFormatCheck(time_format, length_obj);
    }
#endif

    // We currently work with integer milliseconds internally.
    if (time_format == TimeFormat::kSeconds) {
      length = static_cast<int>(Python::GetPyDouble(length_obj) * 1000.0);
    } else if (time_format == TimeFormat::kMilliseconds) {
      length = Python::GetPyInt64(length_obj);
    } else {
      throw Exception("Invalid timeformat: '"
                          + std::to_string(static_cast<int>(time_format))
                          + "'.",
                      PyExcType::kValue);
    }
    if (length < 0) {
      throw Exception("Timer length < 0.", PyExcType::kValue);
    }

    auto runnable(Object::New<Runnable, PythonContextCallRunnable>(call_obj));

    self->time_type_ = time_type;

    // Now just make sure we've got a valid context-target and ask us to
    // make us a timer.
    if (!self->context_->target.exists()) {
      throw Exception("Invalid current context.", PyExcType::kContext);
    }
    self->timer_id_ = self->context_->target->NewTimer(
        self->time_type_, length, static_cast<bool>(repeat), runnable);
    self->have_timer_ = true;

    BA_PYTHON_NEW_CATCH;
  }
  return reinterpret_cast<PyObject*>(self);
}
void PythonClassTimer::DoDelete(bool have_timer, TimeType time_type,
                                int timer_id, Context* context) {
  assert(InGameThread());
  if (!context) {
    return;
  }
  if (context->target.exists() && have_timer) {
    context->target->DeleteTimer(time_type, timer_id);
  }
  delete context;
}

void PythonClassTimer::tp_dealloc(PythonClassTimer* self) {
  BA_PYTHON_TRY;
  // These have to be deleted in the game thread.
  if (!InGameThread()) {
    auto a0 = self->have_timer_;
    auto a1 = self->time_type_;
    auto a2 = self->timer_id_;
    auto a3 = self->context_;
    g_game->PushCall(
        [a0, a1, a2, a3] { PythonClassTimer::DoDelete(a0, a1, a2, a3); });
  } else {
    DoDelete(self->have_timer_, self->time_type_, self->timer_id_,
             self->context_);
  }
  BA_PYTHON_DEALLOC_CATCH;
  Py_TYPE(self)->tp_free(reinterpret_cast<PyObject*>(self));
}

PyTypeObject PythonClassTimer::type_obj;

}  // namespace ballistica
