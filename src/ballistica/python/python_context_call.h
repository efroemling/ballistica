// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_PYTHON_PYTHON_CONTEXT_CALL_H_
#define BALLISTICA_PYTHON_PYTHON_CONTEXT_CALL_H_

#include <string>

#include "ballistica/core/context.h"
#include "ballistica/core/object.h"
#include "ballistica/python/python_ref.h"

namespace ballistica {

// A callable and context-state wrapped up in a convenient package.
// Handy for use with user-submitted callbacks, as it restores context
// state from when it was created and prints various useful bits of info
// on exceptions.
class PythonContextCall : public Object {
 public:
  static auto current_call() -> PythonContextCall* { return current_call_; }
  PythonContextCall() = default;
  ~PythonContextCall() override;

  /// Initialize from either a single callable object, or a tuple with a
  /// callable and optionally args and keywords
  explicit PythonContextCall(PyObject* callable);
  void Run(PyObject* args = nullptr);
  void Run(const PythonRef& args) { Run(args.get()); }
  auto Exists() const -> bool { return object_.exists(); }
  auto GetObjectDescription() const -> std::string override;
  void MarkDead();
  auto object() const -> const PythonRef& { return object_; }
  auto file_loc() const -> const std::string& { return file_loc_; }
  void LogContext();

 private:
  void GetTrace();  // we try to grab basic trace info
  std::string file_loc_;
  int line_{};
  bool dead_ = false;
  PythonRef object_;
  Context context_;
#if BA_DEBUG_BUILD
  ContextTarget* context_target_sanity_test_{};
#endif
  static PythonContextCall* current_call_;
};

// FIXME: this should be static member var
extern PythonContextCall* g_current_python_call;

}  // namespace ballistica

#endif  // BALLISTICA_PYTHON_PYTHON_CONTEXT_CALL_H_
