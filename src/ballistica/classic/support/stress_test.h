// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_CLASSIC_SUPPORT_STRESS_TEST_H_
#define BALLISTICA_CLASSIC_SUPPORT_STRESS_TEST_H_

#include <list>

#include "ballistica/base/base.h"
#include "ballistica/base/support/app_timer.h"
#include "ballistica/shared/foundation/object.h"

namespace ballistica::classic {

class StressTest {
 public:
  void Set(bool enable, int player_count, bool attract_mode);
  void Update();

 private:
  void ProcessInputs(int player_count);
  std::list<base::TestInput*> test_inputs_;

  millisecs_t stress_test_time_{};
  millisecs_t stress_test_last_leave_time_{};
  int stress_test_player_count_{8};
  int last_total_frames_rendered_{};
  bool stress_testing_{};
  bool attract_mode_{};
  Object::Ref<base::AppTimer> update_timer_{};
};

}  // namespace ballistica::classic

#endif  // BALLISTICA_CLASSIC_SUPPORT_STRESS_TEST_H_
