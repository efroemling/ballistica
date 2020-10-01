// Copyright (c) 2011-2020 Eric Froemling

#include "ballistica/generic/timer.h"

#include "ballistica/generic/timer_list.h"

namespace ballistica {

Timer::Timer(TimerList* list_in, int id_in, TimerMedium current_time,
             TimerMedium length_in, TimerMedium offset_in, int repeat_count_in)
    : list_(list_in),
      on_list_(false),
      initial_(true),
      dead_(false),
      list_died_(false),
      last_run_time_(current_time),
      expire_time_(current_time + offset_in),
      id_(id_in),
      length_(length_in),
      repeat_count_(repeat_count_in) {
  list_->timer_count_total_++;
}

Timer::~Timer() {
  // If the list is dead, dont touch the corpse.
  if (!list_died_) {
    if (on_list_) {
      list_->PullTimer(id_);
    } else {
      // Should never be explicitly deleting the current client timer
      // (it should just get marked as dead so the loop can kill it when
      // re-submitted).
      assert(list_->client_timer_ != this);
    }
    list_->timer_count_total_--;
  }
}

void Timer::SetLength(TimerMedium l, bool set_start_time,
                      TimerMedium starttime) {
  if (on_list_) {
    assert(id_ != 0);  // zero denotes "no-id"
    Timer* t = list_->PullTimer(id_);
    BA_PRECONDITION(t == this);
    length_ = l;
    if (set_start_time) last_run_time_ = starttime;
    expire_time_ = last_run_time_ + length_;
    list_->AddTimer(this);
  } else {
    length_ = l;
    if (set_start_time) last_run_time_ = starttime;
  }
}

}  // namespace ballistica
