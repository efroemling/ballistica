// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_APP_STRESS_TEST_H_
#define BALLISTICA_APP_STRESS_TEST_H_

#include "ballistica/ballistica.h"

namespace ballistica {

// FIXME: This is not wired up; I just moved things here from App.
class StressTest {
 public:
  // This used to be a SetStressTesting() call in App.
  void Set(bool enable, int player_count);

  // This used to get run from RunEvents() in App.
  void Update();

 private:
  FILE* stress_test_stats_file_{};
  millisecs_t last_stress_test_update_time_{};
  bool stress_testing_{};
  int stress_test_player_count_{8};
  int last_total_frames_rendered_{};
};

}  // namespace ballistica

#endif  // BALLISTICA_APP_STRESS_TEST_H_
