// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_GENERIC_TIMER_H_
#define BALLISTICA_GENERIC_TIMER_H_

#include "ballistica/ballistica.h"
#include "ballistica/core/object.h"
#include "ballistica/generic/runnable.h"

namespace ballistica {

class Timer {
 public:
  auto id() const -> int { return id_; }
  auto length() const -> TimerMedium { return length_; }
  void SetLength(TimerMedium l, bool set_start_time = false,
                 TimerMedium starttime = 0);

 private:
  Timer(TimerList* list_in, int id_in, TimerMedium current_time,
        TimerMedium length_in, TimerMedium offset_in, int repeat_count_in);
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
  // FIXME: Shouldn't have friend classes in different files.
  friend class TimerList;
};

}  // namespace ballistica

#endif  // BALLISTICA_GENERIC_TIMER_H_
