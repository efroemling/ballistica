// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_PYTHON_SUPPORT_PYTHON_CONTEXT_CALL_H_
#define BALLISTICA_BASE_PYTHON_SUPPORT_PYTHON_CONTEXT_CALL_H_

#include <string>

#include "ballistica/base/support/context.h"
#include "ballistica/shared/foundation/object.h"
#include "ballistica/shared/python/python_ref.h"

namespace ballistica::base {

// A callable and Ballistica context-state wrapped up in a convenient
// package. Handy for use with user-submitted callbacks, as it restores
// context state from when it was created and prints various useful bits of
// context info on exceptions.
class PythonContextCall : public Object {
 public:
  static auto current_call() -> PythonContextCall* { return current_call_; }
  PythonContextCall() = default;
  ~PythonContextCall() override;

  /// Initialize with a raw callable Python object.
  explicit PythonContextCall(PyObject* callable);

  /// Initialize with a callable PythonRef.
  explicit PythonContextCall(const PythonRef& ref)
      : PythonContextCall(ref.get()) {}

  void Run(PyObject* args = nullptr);
  void Run(const PythonRef& args) { Run(args.get()); }
  auto exists() const -> bool { return object_.exists(); }
  auto GetObjectDescription() const -> std::string override;
  void MarkDead();
  auto object() const -> const PythonRef& { return object_; }
  auto file_loc() const -> const std::string& { return file_loc_; }
  void PrintContext();

  /// Run in an upcoming cycle of the logic thread. Must be called from the
  /// logic thread. This form creates a strong-reference so the
  /// context_ref-call is guaranteed to exist until run.
  void Schedule();

  /// Run in an upcoming cycle of the logic thread with provided args. Must
  /// be called from the logic thread. This form creates a strong-reference
  /// so the context_ref-call is guaranteed to exist until run.
  void Schedule(const PythonRef& args);

  /// Run in an upcoming cycle of the logic thread. Must be called from the
  /// logic thread. This form creates a weak-reference and is a no-op if the
  /// context_ref-call is destroyed before its scheduled run.
  void ScheduleWeak();

  /// Run in an upcoming cycle of the logic thread with provided args. Must
  /// be called from the logic thread. This form creates a weak-reference
  /// and is a no-op if the context_ref-call is destroyed before its
  /// scheduled run.
  void ScheduleWeak(const PythonRef& args);

  /// Schedule a call to run as part of a current UI interaction such as a
  /// button being clicked. Must be called from the logic thread. Calls
  /// scheduled this way will be run as part of the handling of the event
  /// that triggered them, though safely outside of any UI traversal. This
  /// avoids pitfalls that can arise with regular Schedule() where calls
  /// that run some action and then disable further UI interaction can get
  /// run twice due to interaction not actually being disabled until the
  /// next event loop cycle, potentially allowing multiple calls to be
  /// scheduled before the disable happens.
  void ScheduleInUIOperation();

  /// Schedule a call to run as part of a current UI interaction such as a
  /// button being clicked. Must be called from the logic thread. Calls
  /// scheduled this way will be run as part of the handling of the event
  /// that triggered them, though safely outside of any UI traversal. This
  /// avoids pitfalls that can arise with regular Schedule() where calls
  /// that run some action and then disable further UI interaction can get
  /// run twice due to interaction not actually being disabled until the
  /// next event loop cycle, potentially allowing multiple calls to be
  /// scheduled before the disable happens.
  void ScheduleInUIOperation(const PythonRef& args);

 private:
  void GetTrace();  // we try to grab basic trace info

  int line_{};
  bool dead_{};
  std::string file_loc_;
  PythonRef object_;
  base::ContextRef context_state_;
  static PythonContextCall* current_call_;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_PYTHON_SUPPORT_PYTHON_CONTEXT_CALL_H_
