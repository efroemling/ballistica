// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_GENERIC_REAL_TIMER_H_
#define BALLISTICA_GENERIC_REAL_TIMER_H_

#include "ballistica/ballistica.h"
#include "ballistica/core/object.h"
#include "ballistica/generic/runnable.h"
#include "ballistica/logic/logic.h"

namespace ballistica {

// Manages a timer which runs on real time and calls a
// 'HandleRealTimerExpired' method on the provided pointer.
template <typename T>
class RealTimer : public Object {
 public:
  RealTimer(millisecs_t length, bool repeat, T* delegate) {
    assert(g_logic);
    assert(InLogicThread());
    timer_id_ = g_logic->NewRealTimer(
        length, repeat, Object::New<Runnable, Callback>(delegate, this));
  }
  void SetLength(uint32_t length) {
    assert(InLogicThread());
    g_logic->SetRealTimerLength(timer_id_, length);
  }
  ~RealTimer() override {
    assert(InLogicThread());
    g_logic->DeleteRealTimer(timer_id_);
  }

 private:
  class Callback : public Runnable {
   public:
    Callback(T* delegate, RealTimer<T>* timer)
        : delegate_(delegate), timer_(timer) {}
    void Run() override { delegate_->HandleRealTimerExpired(timer_); }

   private:
    RealTimer<T>* timer_;
    T* delegate_;
  };
  int timer_id_;
};

}  // namespace ballistica

#endif  // BALLISTICA_GENERIC_REAL_TIMER_H_
