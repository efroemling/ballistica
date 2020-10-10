// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_PYTHON_PYTHON_CONTEXT_CALL_RUNNABLE_H_
#define BALLISTICA_PYTHON_PYTHON_CONTEXT_CALL_RUNNABLE_H_

#include "ballistica/python/python_context_call.h"

namespace ballistica {

// a simple runnable that stores and runs a python context call
class PythonContextCallRunnable : public Runnable {
 public:
  explicit PythonContextCallRunnable(PyObject* o)
      : call(Object::New<PythonContextCall>(o)) {}
  Object::Ref<PythonContextCall> call;
  void Run() override {
    assert(call.exists());
    call->Run();
  }
  virtual ~PythonContextCallRunnable() = default;
};

}  // namespace ballistica

#endif  // BALLISTICA_PYTHON_PYTHON_CONTEXT_CALL_RUNNABLE_H_
