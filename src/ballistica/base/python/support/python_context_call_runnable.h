// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_PYTHON_SUPPORT_PYTHON_CONTEXT_CALL_RUNNABLE_H_
#define BALLISTICA_BASE_PYTHON_SUPPORT_PYTHON_CONTEXT_CALL_RUNNABLE_H_

#include "ballistica/base/python/support/python_context_call.h"
#include "ballistica/shared/generic/runnable.h"

namespace ballistica::base {

// a simple runnable that stores and runs a python context call
class PythonContextCallRunnable : public Runnable {
 public:
  explicit PythonContextCallRunnable(PyObject* o)
      : call(Object::New<PythonContextCall>(o)) {}
  Object::Ref<PythonContextCall> call;
  void Run() override {
    assert(call.Exists());
    call->Run();
  }
  ~PythonContextCallRunnable() override = default;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_PYTHON_SUPPORT_PYTHON_CONTEXT_CALL_RUNNABLE_H_
