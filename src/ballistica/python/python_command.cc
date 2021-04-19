// Released under the MIT License. See LICENSE for details.

#include "ballistica/python/python_command.h"

#include "ballistica/python/python.h"
#include "ballistica/python/python_sys.h"

// Save/restore current command for logging/etc.
// this isn't exception-safe, but we should never let
// exceptions bubble up through python api calls anyway
// or we'll have bigger problems on our hands.
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

auto PythonCommand::Run() -> bool {
  assert(Python::HaveGIL());
  if (!g_python) {
    // This probably means the game is dying; let's not
    // throw an exception here so we don't mask the original error.
    Log("PythonCommand: not running due to null g_python");
    return false;
  }
  assert(!dead_);
  if (!file_code_obj_.get()) {
    CompileForExec();
    assert(!dead_);
  }
  if (file_code_obj_.get()) {
    PUSH_PYCOMMAND(this);
    PyObject* v = PyEval_EvalCode(file_code_obj_.get(), g_python->main_dict(),
                                  g_python->main_dict());
    POP_PYCOMMAND();

    // Technically the python call could have killed us;
    // make sure that didn't happen.
    assert(!dead_);
    if (v == nullptr) {
      // Save/restore error or it can mess with context print calls.
      BA_PYTHON_ERROR_SAVE;
      Log("ERROR: exception in Python call:");
      LogContext();
      BA_PYTHON_ERROR_RESTORE;

      // We pass zero here to avoid grabbing references to this exception
      // which can cause objects to stick around and trip up our deletion
      // checks (nodes, actors existing after their games have ended).
      PyErr_PrintEx(0);
      PyErr_Clear();
    } else {
      Py_DECREF(v);
      return true;
    }
  }
  return false;
}

auto PythonCommand::CanEval() -> bool {
  assert(Python::HaveGIL());
  assert(g_python);
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

auto PythonCommand::RunReturnObj(bool print_errors, PyObject* context)
    -> PyObject* {
  assert(Python::HaveGIL());
  assert(g_python);
  assert(!dead_);
  if (context == nullptr) {
    context = g_python->main_dict();
  }

#pragma clang diagnostic push
#pragma ide diagnostic ignored "RedundantCast"
  assert(PyDict_Check(context));
#pragma clang diagnostic pop

  if (!eval_code_obj_.get()) {
    CompileForEval(print_errors);
    assert(!dead_);
  }
  if (!eval_code_obj_.get()) {
    if (print_errors) {
      // Save/restore error or it can mess with context print calls.
      BA_PYTHON_ERROR_SAVE;
      Log("ERROR: exception in Python call:");
      LogContext();
      BA_PYTHON_ERROR_RESTORE;
      // We pass zero here to avoid grabbing references to this exception
      // which can cause objects to stick around and trip up our deletion checks
      // (nodes, actors existing after their games have ended)
      PyErr_PrintEx(0);
    }

    // Consider the python error handled at this point.
    // If C++ land wants to throw an exception or whatnot based on this result,
    // that's a totally different thing.
    PyErr_Clear();
    return nullptr;
  }
  PUSH_PYCOMMAND(this);
  PyObject* v = PyEval_EvalCode(eval_code_obj_.get(), context, context);
  POP_PYCOMMAND();
  assert(!dead_);
  if (v == nullptr) {
    if (print_errors) {
      // save/restore error or it can mess with context print calls
      BA_PYTHON_ERROR_SAVE;
      Log("ERROR: exception in Python call:");
      LogContext();
      BA_PYTHON_ERROR_RESTORE;
      // we pass zero here to avoid grabbing references to this exception
      // which can cause objects to stick around and trip up our deletion checks
      // (nodes, actors existing after their games have ended)
      PyErr_PrintEx(0);
    }

    // Consider the python error handled at this point.
    // If C++ land wants to throw an exception or whatnot based on this result,
    // that's a totally different thing.
    PyErr_Clear();
    return nullptr;
  }
  return v;
}

void PythonCommand::LogContext() {
  assert(Python::HaveGIL());
  std::string s = std::string("  call: ") + command();
  s += g_python->GetContextBaseString();
  Log(s);
}

}  // namespace ballistica
