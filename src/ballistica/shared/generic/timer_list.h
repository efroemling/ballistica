// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SHARED_GENERIC_TIMER_LIST_H_
#define BALLISTICA_SHARED_GENERIC_TIMER_LIST_H_

#include <cstdio>
#include <vector>

#include "ballistica/shared/ballistica.h"
#include "ballistica/shared/foundation/object.h"

namespace ballistica {

class TimerList {
 public:
  TimerList();
  ~TimerList();

  // Run timers up to the provided target time. Any errors are caught and
  // logged.
  void Run(TimerMedium target_time);

  // Create a timer with provided runnable.
  auto NewTimer(TimerMedium current_time, TimerMedium length,
                TimerMedium offset, int repeat_count, Runnable* runnable)
      -> Timer*;

  // Return a timer by its id, or nullptr if the timer no longer exists.
  auto GetTimer(int id) -> Timer*;

  // Delete a currently-queued timer via its id.
  void DeleteTimer(int timer_id);

  // Return the time until the next timer goes off.
  // If no timers are present, -1 is returned.
  auto TimeToNextExpire(TimerMedium current_time) -> TimerMedium;

  // Return the active timer count. Note that this does not include the client
  // timer (a timer returned via GetExpiredTimer() but not yet re-submitted).
  auto ActiveTimerCount() const -> int { return timer_count_active_; }

  auto Empty() -> bool { return (timers_ == nullptr); }

  void Clear();

 private:
  // Returns the next expired timer. When finished with the timer,
  // return it to the list with Timer::submit()
  // (this will either put it back in line or delete it)
  auto GetExpiredTimer(TimerMedium target_time) -> Timer*;
  auto GetExpiredCount(TimerMedium target_time) -> int;
  auto PullTimer(int timer_id, bool remove = true) -> Timer*;
  auto SubmitTimer(Timer* t) -> Timer*;
  void AddTimer(Timer* t);

  int timer_count_active_{};
  int timer_count_inactive_{};
  int timer_count_total_{};
  Timer* client_timer_{};
  Timer* timers_{};
  Timer* timers_inactive_{};
  int next_timer_id_{1};
  bool running_{};
  bool are_clearing_{};
  friend class Timer;
};

class Timer {
 public:
  auto id() const -> int { return id_; }
  auto length() const -> TimerMedium { return length_; }
  void SetLength(TimerMedium l, bool set_start_time = false,
                 TimerMedium starttime = 0);

 private:
  Timer(TimerList* list, int id, TimerMedium current_time, TimerMedium length,
        TimerMedium offset, int repeat_count);
  virtual ~Timer();
  TimerList* list_{};
  bool on_list_{};
  Timer* next_{};
  bool initial_{};
  bool dead_{};
  bool list_died_{};
  TimerMedium last_run_time_{};
  TimerMedium expire_time_{};
  int id_{};
  TimerMedium length_{};
  int repeat_count_{};
  Object::Ref<Runnable> runnable_;
  friend class TimerList;
};

}  // namespace ballistica

#endif  // BALLISTICA_SHARED_GENERIC_TIMER_LIST_H_
