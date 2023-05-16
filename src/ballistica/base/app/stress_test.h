// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_APP_STRESS_TEST_H_
#define BALLISTICA_BASE_APP_STRESS_TEST_H_

#include "ballistica/shared/ballistica.h"

namespace ballistica::base {

class StressTest {
 public:
  void Set(bool enable, int player_count);
  void Update();

 private:
  FILE* stress_test_stats_file_{};
  millisecs_t last_stress_test_update_time_{};
  bool stress_testing_{};
  int stress_test_player_count_{8};
  int last_total_frames_rendered_{};
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_APP_STRESS_TEST_H_
