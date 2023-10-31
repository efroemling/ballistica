// Released under the MIT License. See LICENSE for details.

#include "ballistica/classic/support/stress_test.h"

#include "ballistica/base/graphics/graphics_server.h"
#include "ballistica/base/graphics/renderer/renderer.h"
#include "ballistica/base/input/device/test_input.h"
#include "ballistica/base/input/input.h"
#include "ballistica/base/support/app_timer.h"
#include "ballistica/classic/classic.h"

namespace ballistica::classic {

void StressTest::Set(bool enable, int player_count) {
  assert(g_base->InLogicThread());
  bool was_stress_testing = stress_testing_;
  stress_testing_ = enable;
  stress_test_player_count_ = player_count;

  // If we're turning on, reset our intervals and things.
  if (!was_stress_testing && stress_testing_) {
    // So our first sample is 1 interval from now.
    last_stress_test_update_time_ = g_core->GetAppTimeMillisecs();

    // Reset our frames-rendered tally.
    if (g_base && g_base->graphics_server
        && g_base->graphics_server->renderer()) {
      last_total_frames_rendered_ =
          g_base->graphics_server->renderer()->total_frames_rendered();
    } else {
      // Assume zero if there's no graphics yet.
      last_total_frames_rendered_ = 0;
    }

    update_timer_ = base::AppTimer::New(1.0 / 30.0, true, [this] { Update(); });
  }
  if (!stress_testing_) {
    update_timer_.Clear();
  }
}

void StressTest::Update() {
  assert(g_base->InLogicThread());

  // Handle a little misc stuff here.
  // If we're currently running stress-tests, update that stuff.
  if (stress_testing_ && g_base->input) {
    // Update our fake inputs to make our dudes run around.
    ProcessInputs(stress_test_player_count_);

    // Every 10 seconds update our stress-test stats.
    millisecs_t t = g_core->GetAppTimeMillisecs();
    if (t - last_stress_test_update_time_ >= 10000) {
      if (stress_test_stats_file_ == nullptr) {
        assert(g_core);
        auto user_python_dir = g_core->GetUserPythonDirectory();
        if (user_python_dir) {
          std::string f_name = *user_python_dir + "/stress_test_stats.csv";
          stress_test_stats_file_ =
              g_core->platform->FOpen(f_name.c_str(), "wb");
          if (stress_test_stats_file_ != nullptr) {
            fprintf(stress_test_stats_file_,
                    "time,averageFps,nodes,meshes,collision_meshes,textures,"
                    "sounds,"
                    "pssMem,sharedDirtyMem,privateDirtyMem\n");
            fflush(stress_test_stats_file_);
          }
        }
      }
      if (stress_test_stats_file_ != nullptr) {
        // See how many frames we've rendered this past interval.
        int total_frames_rendered;
        if (g_base && g_base->graphics_server
            && g_base->graphics_server->renderer()) {
          total_frames_rendered =
              g_base->graphics_server->renderer()->total_frames_rendered();
        } else {
          total_frames_rendered = last_total_frames_rendered_;
        }
        float avg =
            static_cast<float>(total_frames_rendered
                               - last_total_frames_rendered_)
            / (static_cast<float>(t - last_stress_test_update_time_) / 1000.0f);
        last_total_frames_rendered_ = total_frames_rendered;
        uint32_t mesh_count = 0;
        uint32_t collision_mesh_count = 0;
        uint32_t texture_count = 0;
        uint32_t sound_count = 0;
        uint32_t node_count = 0;
        if (g_base) {
          mesh_count = g_base->assets->total_mesh_count();
          collision_mesh_count = g_base->assets->total_collision_mesh_count();
          texture_count = g_base->assets->total_texture_count();
          sound_count = g_base->assets->total_sound_count();
        }
        assert(g_base->logic);
        std::string mem_usage = g_core->platform->GetMemUsageInfo();
        fprintf(stress_test_stats_file_, "%d,%.1f,%d,%d,%d,%d,%d,%s\n",
                static_cast_check_fit<int>(g_core->GetAppTimeMillisecs()), avg,
                node_count, mesh_count, collision_mesh_count, texture_count,
                sound_count, mem_usage.c_str());
        fflush(stress_test_stats_file_);
      }
      last_stress_test_update_time_ = t;
    }
  }
}

void StressTest::ProcessInputs(int player_count) {
  assert(g_base->InLogicThread());
  assert(player_count >= 0);

  millisecs_t time = g_core->GetAppTimeMillisecs();

  // FIXME: If we don't check for stress_test_last_leave_time_ we totally
  //  confuse the game.. need to be able to survive that.

  // Kill some off if we have too many.
  while (static_cast<int>(test_inputs_.size()) > player_count) {
    delete test_inputs_.front();
    test_inputs_.pop_front();
  }

  // If we have less than full test-inputs, add one randomly.
  if (static_cast<int>(test_inputs_.size()) < player_count
      && ((rand() % 1000 < 10))) {  // NOLINT
    test_inputs_.push_back(new base::TestInput());
  }

  // Every so often lets kill the oldest one off.
  if (explicit_bool(true)) {
    if (test_inputs_.size() > 0 && (rand() % 2000 < 3)) {  // NOLINT
      stress_test_last_leave_time_ = time;

      // Usually do oldest; sometimes newest.
      if (rand() % 5 == 0) {  // NOLINT
        delete test_inputs_.back();
        test_inputs_.pop_back();
      } else {
        delete test_inputs_.front();
        test_inputs_.pop_front();
      }
    }
  }

  if (time - stress_test_time_ > 1000) {
    stress_test_time_ = time;  // reset..
    for (auto& test_input : test_inputs_) {
      (*test_input).Reset();
    }
  }

  while (stress_test_time_ < time) {
    stress_test_time_++;
    for (auto& test_input : test_inputs_) {
      (*test_input).Process(stress_test_time_);
    }
  }
}

}  // namespace ballistica::classic
