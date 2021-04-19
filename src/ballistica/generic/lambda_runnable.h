// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_GENERIC_LAMBDA_RUNNABLE_H_
#define BALLISTICA_GENERIC_LAMBDA_RUNNABLE_H_

#include "ballistica/generic/runnable.h"

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

// Call this to allocate and return a raw lambda runnable
template <typename F>
auto NewLambdaRunnable(const F& lambda) -> Object::Ref<Runnable> {
  return Object::New<Runnable, LambdaRunnable<F>>(lambda);
}

// Same but returns the raw pointer instead of a ref;
// (used when passing across threads).
template <typename F>
auto NewLambdaRunnableRaw(const F& lambda) -> Runnable* {
  return Object::NewDeferred<LambdaRunnable<F>>(lambda);
}

}  // namespace ballistica

#endif  // BALLISTICA_GENERIC_LAMBDA_RUNNABLE_H_
