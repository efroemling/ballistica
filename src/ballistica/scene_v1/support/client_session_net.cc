// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/support/client_session_net.h"

#include <algorithm>
#include <memory>
#include <vector>

#include "ballistica/base/graphics/graphics.h"
#include "ballistica/base/graphics/support/net_graph.h"
#include "ballistica/base/logic/logic.h"
#include "ballistica/classic/support/classic_app_mode.h"
#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging.h"
#include "ballistica/scene_v1/connection/connection_to_host.h"
#include "ballistica/scene_v1/support/replay_writer.h"

namespace ballistica::scene_v1 {

ClientSessionNet::ClientSessionNet() {
  // Sanity check: we should only ever be writing one replay at once.
  if (g_scene_v1->replay_open) {
    g_core->logging->Log(LogName::kBaNetworking, LogLevel::kError,
                         "g_scene_v1->replay_open true at netclient start;"
                         " shouldn't happen.");
  }
  assert(g_base->assets_server);

  // We always write replays as the highest protocol version we support.
  replay_writer_ = new ReplayWriter;
  writing_replay_ = true;
  g_scene_v1->replay_open = true;
}

ClientSessionNet::~ClientSessionNet() {
  if (writing_replay_) {
    // Sanity check: we should only ever be writing one replay at once.
    if (!g_scene_v1->replay_open) {
      g_core->logging->Log(LogName::kBaNetworking, LogLevel::kError,
                           "g_scene_v1->replay_open false at net-client close;"
                           " shouldn't happen.");
    }
    g_scene_v1->replay_open = false;
    assert(g_base->assets_server);
    replay_writer_->Finish();
    replay_writer_ = nullptr;
    writing_replay_ = false;
  }
}

void ClientSessionNet::SetConnectionToHost(ConnectionToHost* c) {
  connection_to_host_ = c;
}

void ClientSessionNet::OnCommandBufferUnderrun() {
  // We currently don't do anything here; we want to just power
  // through hitches and keep aiming for our target time.
  // (though perhaps we could take note here for analytics purposes).
  // printf("Underrun at %d\n", AppTimeMillisecs());
  // fflush(stdout);
}

void ClientSessionNet::Update(int time_advance_millisecs, double time_advance) {
  if (shutting_down()) {
    return;
  }

  // Now do standard step.
  ClientSession::Update(time_advance_millisecs, time_advance);

  // And update our timing to try and ensure we don't run out of buffer.
  UpdateBuffering();
}

auto ClientSessionNet::GetBucketNum() -> int {
  auto* appmode = classic::ClassicAppMode::GetSingleton();
  return (delay_sample_counter_ / appmode->delay_bucket_samples())
         % static_cast<int>(buckets_.size());
}

void ClientSessionNet::UpdateBuffering() {
  auto* appmode = classic::ClassicAppMode::GetSingleton();
  // Keep record of the most and least amount of time we've had buffered
  // recently, and slow down/speed up a bit based on that.
  {
    // Change bucket every `g_delay_samples` samples.
    int bucketnum{GetBucketNum()};
    int bucket_iteration =
        delay_sample_counter_ % appmode->delay_bucket_samples();
    delay_sample_counter_++;
    SampleBucket& bucket{buckets_[bucketnum]};
    if (bucket_iteration == 0) {
      bucket.max_delay_from_projection = 0;
    }

    // After the last sample in each bucket, update our smoothed values with
    // the full sample set in the bucket.
    if (bucket_iteration == appmode->delay_bucket_samples() - 1) {
      float smoothing = 0.7f;
      last_bucket_max_delay_ =
          static_cast<float>(bucket.max_delay_from_projection);
      max_delay_smoothed_ =
          smoothing * max_delay_smoothed_
          + (1.0f - smoothing)
                * static_cast<float>(bucket.max_delay_from_projection);
    }
    auto now = g_core->AppTimeMillisecs();

    // We want target-base-time to wind up at our projected time minus some
    // safety offset to account for buffering fluctuations.

    // We might want to consider exposing this value or calculate it in a smart
    // way based on conditions. 0.0 gives us lowest latency possible but makes
    // lag spikes very noticeable. 1.0 should avoid most lag spikes. Higher
    // values even moreso at the price of latency;
    float safety_amt{1.0};

    float to_ideal_offset =
        static_cast<float>(ProjectedBaseTime(now) - target_base_time())
        - safety_amt * max_delay_smoothed_;

    // How aggressively we throttle the game speed up or down to accommodate lag
    // spikes.
    float speed_change_aggression{0.004f};
    float new_consume_rate = std::min(
        10.0f,
        std::max(0.5f, 1.0f + speed_change_aggression * to_ideal_offset));
    set_consume_rate(new_consume_rate);

    if (g_base->graphics->network_debug_info_display_enabled()) {
      // Plug display time into these graphs to get smoother looking updates.
      auto now_d = g_base->logic->display_time() * 1000.0;

      if (auto* graph =
              g_base->graphics->GetDebugGraph("1: packet delay", false)) {
        graph->AddSample(now_d, current_delay_);
      }
      if (auto* graph =
              g_base->graphics->GetDebugGraph("2: max delay bucketed", false)) {
        graph->AddSample(now_d, last_bucket_max_delay_);
      }
      if (auto* graph =
              g_base->graphics->GetDebugGraph("3: filtered delay", false)) {
        graph->AddSample(now_d, max_delay_smoothed_);
      }
      if (auto* graph = g_base->graphics->GetDebugGraph("4: run rate", false)) {
        graph->AddSample(now_d, new_consume_rate);
      }
      if (auto* graph =
              g_base->graphics->GetDebugGraph("5: time buffered", true)) {
        graph->AddSample(now_d, base_time_buffered());
      }
    }
  }
}

void ClientSessionNet::OnReset(bool rewind) {
  // Resets should never happen for us after we start, right?...
  base_time_received_ = 0;
  last_base_time_receive_time_ = 0;
  leading_base_time_received_ = 0;
  leading_base_time_receive_time_ = 0;
  ClientSession::OnReset(rewind);
}

void ClientSessionNet::OnBaseTimeStepAdded(int step) {
  auto now = g_core->AppTimeMillisecs();

  millisecs_t new_base_time_received = base_time_received_ + step;

  // We want to be able to project as close as possible to what the
  // current base time is based on when we receive steps (regardless of lag
  // spikes). To do this, we only factor in steps we receive if their times are
  // newer than what we get projecting forward from the last one.
  bool use;
  if (leading_base_time_receive_time_ == 0) {
    use = true;
  } else {
    millisecs_t projected = ProjectedBaseTime(now);

    // Hopefully we'll keep refreshing our leading value consistently
    // but force the issue if it becomes too old.
    use = (new_base_time_received >= projected
           || (now - leading_base_time_receive_time_ > 250));

    // Keep track of the biggest recent delays we get compared to the projected
    // time. (we can use this when calcing how much to buffer to avoid stutter).
    if (new_base_time_received < projected) {
      auto& bucket{buckets_[GetBucketNum()]};
      current_delay_ = bucket.max_delay_from_projection =
          std::max(bucket.max_delay_from_projection,
                   static_cast<int>(projected - new_base_time_received));

    } else {
      current_delay_ = 0.0f;
    }
  }

  base_time_received_ = new_base_time_received;
  last_base_time_receive_time_ = now;

  if (use) {
    leading_base_time_received_ = new_base_time_received;
    leading_base_time_receive_time_ = now;
  }
}

void ClientSessionNet::HandleSessionMessage(
    const std::vector<uint8_t>& message) {
  // Do the standard thing, but also write this message straight to our replay
  // stream if we have one.
  ClientSession::HandleSessionMessage(message);

  if (writing_replay_) {
    assert(g_base->assets_server);
    assert(replay_writer_);
    replay_writer_->PushAddMessageToReplayCall(message);
  }
}

}  // namespace ballistica::scene_v1
