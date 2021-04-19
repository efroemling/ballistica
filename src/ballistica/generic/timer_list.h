// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_GENERIC_TIMER_LIST_H_
#define BALLISTICA_GENERIC_TIMER_LIST_H_

#include <cstdio>
#include <vector>

#include "ballistica/ballistica.h"
#include "ballistica/core/object.h"

namespace ballistica {

class TimerList {
 public:
  TimerList();
  ~TimerList();

  // Run timers up to the provided target time.
  void Run(TimerMedium target_time);

  // Create a timer with provided runnable.
  auto NewTimer(TimerMedium current_time, TimerMedium length,
                TimerMedium offset, int repeat_count,
                const Object::Ref<Runnable>& runnable) -> Timer*;

  // Return a timer by its id, or nullptr if the timer no longer exists.
  auto GetTimer(int id) -> Timer*;

  // Delete a currently-queued timer via its id.
  void DeleteTimer(int timer_id);

  // Return the time until the next timer goes off.
  // If no timers are present, -1 is returned.
  auto GetTimeToNextExpire(TimerMedium current_time) -> TimerMedium;

  // Return the active timer count.  Note that this does not include the client
  // timer (a timer returned via getExpiredTimer() but not yet re-submitted).
  auto active_timer_count() const -> int { return timer_count_active_; }

  auto empty() -> bool { return (timers_ == nullptr); }

  void Clear();

 private:
  // Returns the next expired timer.  When done with the timer,
  // return it to the list with Timer::submit()
  // (this will either put it back in line or delete it)
  auto GetExpiredTimer(TimerMedium target_time) -> Timer*;
  auto GetExpiredCount(TimerMedium target_time) -> int;
  auto PullTimer(int timer_id, bool remove = true) -> Timer*;
  auto SubmitTimer(Timer* t) -> Timer*;
  void AddTimer(Timer* t);
  int timer_count_active_ = 0;
  int timer_count_inactive_ = 0;
  int timer_count_total_ = 0;
  Timer* client_timer_ = nullptr;
  Timer* timers_ = nullptr;
  Timer* timers_inactive_ = nullptr;
  int next_timer_id_ = 1;
  bool running_ = false;
  bool are_clearing_ = false;
  friend class Timer;
};

}  // namespace ballistica

#endif  // BALLISTICA_GENERIC_TIMER_LIST_H_
