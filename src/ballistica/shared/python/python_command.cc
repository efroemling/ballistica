// Released under the MIT License. See LICENSE for details.

#include "ballistica/shared/python/python_command.h"

#include <string>
#include <utility>

#include "ballistica/core/python/core_python.h"
#include "ballistica/shared/python/python.h"
#include "ballistica/shared/python/python_macros.h"

// Save/restore current command for logging/etc.
// this isn't exception-safe, but we should never let
// exceptions bubble up through Python api calls anyway
// or we'll have bigger problems on our hands.
// FIXME: What about thread safety? Seems like this isn't.
#define PUSH_PYCOMMAND(OBJ)                     \
  PythonCommand* prev_pycmd = current_command_; \
  current_command_ = OBJ
#define POP_PYCOMMAND() current_command_ = prev_pycmd

namespace ballistica {

PythonCommand* PythonCommand::current_command_ = nullptr;

PythonCommand::PythonCommand() = default;

PythonCommand::PythonCommand(std::string command_in)
    : command_(std::move(command_in)) {}

PythonCommand::PythonCommand(std::string command_in, std::string file_name_in)
    : command_(std::move(command_in)), file_name_(std::move(file_name_in)) {}

PythonCommand::PythonCommand(const PythonCommand& c) : command_(c.command_) {}

auto PythonCommand::operator=(const PythonCommand& src) -> PythonCommand& {
  if (&src == this) {
    return *this;
  }
  // TODO(ericf): we should just grab refs to their code objs if they have
  //  them, right?
  file_code_obj_.Release();
  eval_code_obj_.Release();
  command_ = src.command_;
  return *this;
}

auto PythonCommand::operator=(const std::string& src) -> PythonCommand& {
  file_code_obj_.Release();
  eval_code_obj_.Release();
  command_ = src;
  return *this;
}

void PythonCommand::CompileForExec() {
  assert(Python::HaveGIL());
  assert(file_code_obj_.get() == nullptr);
  PyObject* o =
      Py_CompileString(command_.c_str(), file_name_.c_str(), Py_file_input);
  if (o == nullptr) {
    // we pass zero here to avoid grabbing references to this exception
    // which can cause objects to stick around and trip up our deletion checks
    // (nodes, actors existing after their games have ended)
    PyErr_PrintEx(0);
  } else {
    file_code_obj_.Acquire(o);
  }
}

void PythonCommand::CompileForEval(bool print_errors) {
  assert(Python::HaveGIL());
  assert(eval_code_obj_.get() == nullptr);
  PyObject* o =
      Py_CompileString(command_.c_str(), file_name_.c_str(), Py_eval_input);
  if (o == nullptr) {
    if (print_errors) {
      // we pass zero here to avoid grabbing references to this exception
      // which can cause objects to stick around and trip up our deletion checks
      // (nodes, actors existing after their games have ended)
      PyErr_PrintEx(0);
    }
    PyErr_Clear();
  } else {
    eval_code_obj_.Acquire(o);
  }
}

PythonCommand::~PythonCommand() { dead_ = true; }

auto PythonCommand::CanEval() -> bool {
  assert(Python::HaveGIL());
  if (!eval_code_obj_.get()) {
    CompileForEval(false);
  }
  if (!eval_code_obj_.get()) {
    PyErr_Clear();
    return false;
  }
  PyErr_Clear();
  return true;
}

auto PythonCommand::Exec(bool print_errors, PyObject* globals, PyObject* locals)
    -> bool {
  assert(Python::HaveGIL());

  // If we're being used before core is up, we need both global and
  // locals to be passed.
  // Note: accessing core globals directly here; normally don't do this.
  assert(core::g_core != nullptr || (globals != nullptr && locals != nullptr));

  assert(!dead_);

  if (globals == nullptr) {
    globals = core::g_core->python->objs()
                  .Get(core::CorePython::ObjID::kMainDict)
                  .get();
  }
  if (locals == nullptr) {
    locals = core::g_core->python->objs()
                 .Get(core::CorePython::ObjID::kMainDict)
                 .get();
  }

  if (!file_code_obj_.get()) {
    CompileForExec();
    assert(!dead_);
  }
  if (file_code_obj_.get()) {
    PUSH_PYCOMMAND(this);
    PyObject* v = PyEval_EvalCode(file_code_obj_.get(), globals, locals);
    POP_PYCOMMAND();

    // Technically the Python call could have killed us;
    // make sure that didn't happen.
    assert(!dead_);
    // TODO(ericf): we shouldn't care. Should grab everything we might need
    //  for the rest of this call before doing that so it doesn't matter.

    if (v == nullptr) {
      // Special case; when a SystemExit is thrown, we always just
      // do a PyErr_Print. As per Python docs, that silently exits
      // the process with the SystemExit's error code.
      if (PyErr_ExceptionMatches(PyExc_SystemExit)) {
        PyErr_Print();
      }

      if (print_errors) {
        // Save/restore error or it can mess with context print calls.
        BA_PYTHON_ERROR_SAVE;
        PySys_WriteStderr("Exception in Python call:\n");
        PrintContext();
        BA_PYTHON_ERROR_RESTORE;

        // We pass zero here to avoid grabbing references to this exception
        // which can cause objects to stick around and trip up our deletion
        // checks (nodes, actors existing after their games have ended).
        PyErr_PrintEx(0);
      }
      PyErr_Clear();
    } else {
      Py_DECREF(v);
      return true;
    }
  }
  return false;
}

auto PythonCommand::Eval(bool print_errors, PyObject* globals, PyObject* locals)
    -> PythonRef {
  assert(Python::HaveGIL());
  assert(!dead_);

  if (globals == nullptr) {
    assert(core::g_core);
    globals = core::g_core->python->objs()
                  .Get(core::CorePython::ObjID::kMainDict)
                  .get();
  }
  if (locals == nullptr) {
    assert(core::g_core);
    locals = core::g_core->python->objs()
                 .Get(core::CorePython::ObjID::kMainDict)
                 .get();
  }

  assert(PyDict_Check(globals));
  assert(PyDict_Check(locals));

  if (!eval_code_obj_.get()) {
    CompileForEval(print_errors);
    assert(!dead_);
  }

  // Attempt to compile for eval if necessary.
  if (!eval_code_obj_.get()) {
    if (print_errors) {
      // Save/restore error or it can mess with context print calls.
      BA_PYTHON_ERROR_SAVE;
      PySys_WriteStderr("Exception in Python call:\n");
      PrintContext();
      BA_PYTHON_ERROR_RESTORE;
      // We pass zero here to avoid grabbing references to this exception
      // which can cause objects to stick around and trip up our deletion checks
      // (nodes, actors existing after their games have ended)
      PyErr_PrintEx(0);
    }

    // Consider the Python error handled at this point.
    // If C++ land wants to throw an exception or whatnot based on this result,
    // that's a totally different thing.
    PyErr_Clear();
    return {};
  }
  PUSH_PYCOMMAND(this);
  PyObject* v = PyEval_EvalCode(eval_code_obj_.get(), globals, locals);
  POP_PYCOMMAND();
  assert(!dead_);
  if (v == nullptr) {
    if (print_errors) {
      // save/restore error or it can mess with context print calls
      BA_PYTHON_ERROR_SAVE;
      PySys_WriteStderr("Exception in Python call:\n");
      PrintContext();
      BA_PYTHON_ERROR_RESTORE;
      // we pass zero here to avoid grabbing references to this exception
      // which can cause objects to stick around and trip up our deletion checks
      // (nodes, actors existing after their games have ended)
      PyErr_PrintEx(0);
    }

    // Consider the Python error handled at this point.
    // If C++ land wants to throw an exception or whatnot based on this result,
    // that's a totally different thing.
    PyErr_Clear();
    return {};
  }
  return {v, PythonRef::kSteal};
}

void PythonCommand::PrintContext() {
  assert(Python::HaveGIL());
  std::string s;

  // Add the call only if its a one-liner.
  if (command().find('\n') == std::string::npos) {
    s += std::string("  call: ") + command() + "\n";
  }
  s += Python::GetContextBaseString();
  PySys_WriteStderr("%s\n", s.c_str());
}

}  // namespace ballistica
