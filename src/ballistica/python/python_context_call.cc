// Released under the MIT License. See LICENSE for details.

#include "ballistica/python/python_context_call.h"

#include "ballistica/game/host_activity.h"
#include "ballistica/game/session/host_session.h"
#include "ballistica/python/python.h"
#include "ballistica/python/python_sys.h"

namespace ballistica {

// FIXME - should be static member var
PythonContextCall* PythonContextCall::current_call_ = nullptr;

PythonContextCall::PythonContextCall(PyObject* obj_in) {
  assert(InGameThread());
  // as a sanity test, store the current context ptr just to make sure it
  // hasn't changed when we run
#if BA_DEBUG_BUILD
  context_target_sanity_test_ = context_.target.get();
#endif  // BA_DEBUG_BUILD
  BA_PRECONDITION(PyCallable_Check(obj_in));
  object_.Acquire(obj_in);
  GetTrace();
  // ok now we need to register this call with whatever the context is;
  // it can be stored in a host-activity, a host-session, or the UI context.
  // whoever it is registered with will explicitly release its contents on
  // shutdown and ensure that nothing gets run after that point.
  if (HostActivity* ha = context_.GetHostActivity()) {
    ha->RegisterCall(this);
  } else if (HostSession* hs = context_.GetHostSession()) {
    hs->RegisterCall(this);
  } else if (context_.GetUIContext()) {
    // UI context never currently dies so no registering necessary here..
  } else {
    throw Exception(
        "Invalid context; ContextCalls must be created in a non-expired "
        "Activity, Session, or UI context. (call obj = "
            + Python::ObjToString(obj_in) + ").",
        PyExcType::kContext);
  }
}

PythonContextCall::~PythonContextCall() {
  // lets set up context while we take our stuff down
  // (we may be holding refs to actors or whatnot)
  ScopedSetContext cp(context_);
  object_.Release();
}

auto PythonContextCall::GetObjectDescription() const -> std::string {
  return "<PythonContextCall from " + file_loc_ + " at "
         + Utils::PtrToString(this) + ">";
}

void PythonContextCall::GetTrace() {
  PyFrameObject* f = PyThreadState_GET()->frame;
  if (f) {
    // grab the file/line now in case we error
    // (useful for debugging simple timers and callbacks and such)
    file_loc_ = Python::GetPythonFileLocation();
  }
}

// called by our owning context when it goes down
// we should clear ourself out to be a no-op if we still happen to be called
void PythonContextCall::MarkDead() {
  dead_ = true;
  object_.Release();
}

void PythonContextCall::Run(PyObject* args) {
  assert(this);

  if (!g_python) {
    // This probably means the game is dying; let's not
    // throw an exception here so we don't mask the original error.
    Log("PythonCommand: not running due to null g_python");
    return;
  }

  if (dead_) {
    return;
  }

  // Sanity test: make sure our context didn't go away.
#if BA_DEBUG_BUILD
  if (context_.target.get() != context_target_sanity_test_) {
    Log("WARNING: running Call after it's context has died: " + object_.Str());
  }
#endif  // BA_DEBUG_BUILD

  // Restore the context from when we were made.
  ScopedSetContext cp(context_);

  // Hold a ref to this call throughout this process
  // so we know it'll still exist if we need to report
  // exception info and whatnot.
  Object::Ref<PythonContextCall> keep_alive_ref(this);

  PythonContextCall* prev_call = current_call_;
  current_call_ = this;
  assert(Python::HaveGIL());
  PyObject* o = PyObject_Call(
      object_.get(),
      args ? args : g_python->obj(Python::ObjID::kEmptyTuple).get(), nullptr);
  current_call_ = prev_call;

  if (o) {
    Py_DECREF(o);
  } else {
    // Save/restore python error or it can mess with context print calls.
    BA_PYTHON_ERROR_SAVE;

    Log("ERROR: exception in Python call:");
    LogContext();
    BA_PYTHON_ERROR_RESTORE;

    // We pass zero here to avoid grabbing references to this exception
    // which can cause objects to stick around and trip up our deletion checks.
    // (nodes, actors existing after their games have ended).
    PyErr_PrintEx(0);
    PyErr_Clear();
  }
}

void PythonContextCall::LogContext() {
  assert(InGameThread());
  std::string s = std::string("  root call: ") + object().Str();
  s += ("\n  root call origin: " + file_loc());
  s += g_python->GetContextBaseString();
  Log(s);
}

}  // namespace ballistica
