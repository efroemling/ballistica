// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SHARED_PYTHON_PYTHON_COMMAND_H_
#define BALLISTICA_SHARED_PYTHON_PYTHON_COMMAND_H_

#include <string>

#include "ballistica/shared/ballistica.h"
#include "ballistica/shared/python/python_ref.h"

namespace ballistica {

// String based Python commands.

// Note to self: Originally I though I'd be using this in a lot of places,
// so I added the ability to compile once and run repeatedly, quietly
// capture output instead of printing it, etc. Now, however, its usage is
// pretty much limited to a few places such as handling stdin and the in-app
// console. Most places it is much cleaner to work with proper python
// modules and just interact with PyObject* refs to them. I should look and
// see if Python's default high level calls would suffice for these purposes
// and potentially kill this off.
class PythonCommand {
 public:
  PythonCommand();
  PythonCommand(std::string command);  // NOLINT (want to allow char*)

  static auto current_command() -> PythonCommand* { return current_command_; }
  // file_name will be listed on error output
  PythonCommand(std::string command, std::string file_name);
  PythonCommand(const PythonCommand& other);

  // copy a command
  auto operator=(const PythonCommand& other) -> PythonCommand&;

  // set the command to a new command string
  auto operator=(const std::string& command) -> PythonCommand&;
  ~PythonCommand();
  auto command() -> const std::string& { return command_; }

  /// Run the command in exec mode. Return true if the command completed
  /// successfully (not to be confused with the command's result).
  /// This works for both eval-able and non-eval-able commands.
  auto Exec(bool print_errors, PyObject* globals, PyObject* locals) -> bool;

  /// Run the command and return the result as a new Python reference.
  /// Only works for eval-able commands.
  /// Returns nullptr on errors, but Python error state will be cleared.
  auto Eval(bool print_errors, PyObject* globals, PyObject* locals)
      -> PythonRef;

  void PrintContext();

  /// Return true if the command can be evaluated; otherwise it can only be
  /// executed
  auto CanEval() -> bool;
  void CompileForExec();
  void CompileForEval(bool print_errors);

 private:
  bool dead_{};
  PythonRef file_code_obj_;
  PythonRef eval_code_obj_;
  std::string command_;
  std::string file_name_;
  static PythonCommand* current_command_;
};

}  // namespace ballistica

#endif  // BALLISTICA_SHARED_PYTHON_PYTHON_COMMAND_H_
