// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SHARED_GENERIC_LAMBDA_RUNNABLE_H_
#define BALLISTICA_SHARED_GENERIC_LAMBDA_RUNNABLE_H_

#include "ballistica/shared/generic/runnable.h"

namespace ballistica {

// (don't use this class directly; call NewLambdaRunnable below)
// from what I hear, heavy use of std::function can slow
// compiles down dramatically, so sticking to raw lambdas here
template <typename F>
class LambdaRunnable : public Runnable {
 public:
  explicit LambdaRunnable(F lambda) : lambda_(lambda) {}
  void Run() override { lambda_(); }

 private:
  F lambda_;
};

/// Create a LambdaRunnable from a raw lambda.
template <typename F>
auto NewLambdaRunnable(const F& lambda) -> Object::Ref<Runnable> {
  return Object::New<Runnable, LambdaRunnable<F>>(lambda);
}

/// Create an unmanaged LambdaRunnable from a raw lambda.
/// Use this with functionality that explicitly asks for unmanaged objects.
template <typename F>
auto NewLambdaRunnableUnmanaged(const F& lambda) -> Runnable* {
  return Object::NewUnmanaged<LambdaRunnable<F>>(lambda);
}

}  // namespace ballistica

#endif  // BALLISTICA_SHARED_GENERIC_LAMBDA_RUNNABLE_H_
