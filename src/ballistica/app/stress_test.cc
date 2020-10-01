// Copyright (c) 2011-2020 Eric Froemling

#include "ballistica/app/stress_test.h"

#include "ballistica/ballistica.h"
#include "ballistica/graphics/graphics_server.h"
#include "ballistica/graphics/renderer.h"
#include "ballistica/input/input.h"
#include "ballistica/platform/platform.h"

namespace ballistica {

void StressTest::Update() {
  assert(InMainThread());

  // Handle a little misc stuff here.
  // If we're currently running stress-tests, update that stuff.
  if (stress_testing_ && g_input) {
    // Update our fake inputs to make our dudes run around.
    g_input->ProcessStressTesting(stress_test_player_count_);

    // Every 10 seconds update our stress-test stats.
    millisecs_t t = GetRealTime();
    if (t - last_stress_test_update_time_ >= 10000) {
      if (stress_test_stats_file_ == nullptr) {
        assert(g_platform);
        std::string f_name =
            g_platform->GetUserPythonDirectory() + "/stress_test_stats.csv";
        stress_test_stats_file_ = g_platform->FOpen(f_name.c_str(), "wb");
        if (stress_test_stats_file_ != nullptr) {
          fprintf(stress_test_stats_file_,
                  "time,averageFps,nodes,models,collide_models,textures,sounds,"
                  "pssMem,sharedDirtyMem,privateDirtyMem\n");
          fflush(stress_test_stats_file_);
          if (g_buildconfig.ostype_android()) {
            // On android, let the OS know we've added or removed a file
            // (limit to android or we'll get an unimplemented warning).
            g_platform->AndroidRefreshFile(f_name);
          }
        }
      }
      if (stress_test_stats_file_ != nullptr) {
        // See how many frames we've rendered this past interval.
        int total_frames_rendered;
        if (g_graphics_server && g_graphics_server->renderer()) {
          total_frames_rendered =
              g_graphics_server->renderer()->total_frames_rendered();
        } else {
          total_frames_rendered = last_total_frames_rendered_;
        }
        float avg =
            static_cast<float>(total_frames_rendered
                               - last_total_frames_rendered_)
            / (static_cast<float>(t - last_stress_test_update_time_) / 1000.0f);
        last_total_frames_rendered_ = total_frames_rendered;
        uint32_t model_count = 0;
        uint32_t collide_model_count = 0;
        uint32_t texture_count = 0;
        uint32_t sound_count = 0;
        uint32_t node_count = 0;
        if (g_media) {
          model_count = g_media->total_model_count();
          collide_model_count = g_media->total_collide_model_count();
          texture_count = g_media->total_texture_count();
          sound_count = g_media->total_sound_count();
        }
        assert(g_game);
        std::string mem_usage = g_platform->GetMemUsageInfo();
        fprintf(stress_test_stats_file_, "%d,%.1f,%d,%d,%d,%d,%d,%s\n",
                static_cast_check_fit<int>(GetRealTime()), avg, node_count,
                model_count, collide_model_count, texture_count, sound_count,
                mem_usage.c_str());
        fflush(stress_test_stats_file_);
      }
      last_stress_test_update_time_ = t;
    }
  }
}

void StressTest::Set(bool enable, int player_count) {
  assert(InMainThread());
  bool was_stress_testing = stress_testing_;
  stress_testing_ = enable;
  stress_test_player_count_ = player_count;

  // If we're turning on, reset our intervals and things.
  if (!was_stress_testing && stress_testing_) {
    // So our first sample is 1 interval from now.
    last_stress_test_update_time_ = GetRealTime();

    // Reset our frames-rendered tally.
    if (g_graphics_server && g_graphics_server->renderer()) {
      last_total_frames_rendered_ =
          g_graphics_server->renderer()->total_frames_rendered();
    } else {
      // Assume zero if there's no graphics yet.
      last_total_frames_rendered_ = 0;
    }
  }
}
}  //  namespace ballistica
