// Copyright (c) 2011-2020 Eric Froemling

#include "ballistica/game/session/net_client_session.h"

#include <algorithm>
#include <vector>

#include "ballistica/app/app_globals.h"
#include "ballistica/game/connection/connection_to_host.h"
#include "ballistica/media/media_server.h"

namespace ballistica {

NetClientSession::NetClientSession() {
  // Sanity check: we should only ever be writing one replay at once.
  if (g_app_globals->replay_open) {
    Log("ERROR: g_replay_open true at netclient start; shouldn't happen.");
  }
  assert(g_media_server);
  g_media_server->PushBeginWriteReplayCall();
  writing_replay_ = true;
  g_app_globals->replay_open = true;
}

NetClientSession::~NetClientSession() {
  if (writing_replay_) {
    // Sanity check: we should only ever be writing one replay at once.
    if (!g_app_globals->replay_open) {
      Log("ERROR: g_replay_open false at net-client close; shouldn't happen.");
    }
    g_app_globals->replay_open = false;
    assert(g_media_server);
    g_media_server->PushEndWriteReplayCall();
    writing_replay_ = false;
  }
}

void NetClientSession::SetConnectionToHost(ConnectionToHost* c) {
  connection_to_host_ = c;
}

void NetClientSession::OnCommandBufferUnderrun() {
  // Any time we run out of data, hit the brakes on our playback speed.
  // Update: maybe not.
  // correction_ *= 0.99f;
}

void NetClientSession::Update(int time_advance) {
  if (shutting_down_) {
    return;
  }

  // Now do standard step.
  ClientSession::Update(time_advance);

  // And update our timing to try and ensure we don't run out of buffer.
  UpdateBuffering();
}

void NetClientSession::UpdateBuffering() {
  // if (NetGraph *graph = g_graphics->debug_graph_1()) {
  //   graph->addSample(GetRealTime(), steps_on_list_);
  // }

  // Keep record of the most and least amount of time we've had buffered
  // recently, and slow down/speed up a bit based on that.
  {
    int bucket_count = static_cast<int>(least_buffered_count_list_.size());

    // Change bucket every g_delay_samples samples.
    int bucket = (buffer_count_list_index_ / g_app_globals->delay_samples)
                 % bucket_count;
    int bucket_iteration =
        buffer_count_list_index_ % g_app_globals->delay_samples;

    // *Set* the value the first iteration in each bucket; do *min* after that.
    if (bucket_iteration == 0) {
      least_buffered_count_list_[bucket] = steps_on_list_;
      most_buffered_count_list_[bucket] = steps_on_list_;
    } else {
      least_buffered_count_list_[bucket] =
          std::min(least_buffered_count_list_[bucket], steps_on_list_);
      most_buffered_count_list_[bucket] =
          std::max(most_buffered_count_list_[bucket], steps_on_list_);

      // After the last sample in each bucket, feed the max bucket value in
      // as the 'low pass' buffer-count. The low-pass curve minus our largest
      // spike value should be where we want to aim for in the buffer.
      if (bucket_iteration == g_app_globals->delay_samples - 1) {
        float smoothing = 0.5f;
        low_pass_smoothed_ =
            smoothing * low_pass_smoothed_
            + (1.0f - smoothing)
                  * static_cast<float>(most_buffered_count_list_[bucket]);
      }
    }

    // Keep track of the largest min/max difference in our sample segments.
    int largest_spike = 0;

    buffer_count_list_index_++;
    for (int i = 1; i < bucket_count; i++) {
      int spike = most_buffered_count_list_[i] - least_buffered_count_list_[i];
      if (spike > largest_spike) {
        largest_spike = spike;
      }
    }

    // Slowly adjust largest spike value based on the biggest in recent history.
    {
      float smoothing = 0.95f;
      largest_spike_smoothed_ =
          smoothing * largest_spike_smoothed_
          + (1.0f - smoothing) * static_cast<float>(largest_spike);
    }

    // Low pass is the most buffered data we've had in the most recent slot.
    float ideal_offset = low_pass_smoothed_ - largest_spike_smoothed_ * 1.0f;

    // Any time we've got no current buffered data, slow down fast.
    // (otherwise we can get stuck cruising along with no 0 buffered data and
    // things get real jerky looking)
    if (steps_on_list_ == 0) {
      ideal_offset -= 100.0f;
    }
    float smoothing = 0.0f;
    correction_ = smoothing * correction_
                  + (1.0f - smoothing) * (1.0f + 0.002f * ideal_offset);
    correction_ = std::min(1.5f, std::max(0.5f, correction_));
    // if (NetGraph *graph = g_graphics->debug_graph_2()) {
    //   graph->addSample(GetRealTime(), correction_);
    // }
  }
}
void NetClientSession::HandleSessionMessage(
    const std::vector<uint8_t>& message) {
  // Do the standard thing, but also write this message straight to our replay
  // stream if we have one.
  ClientSession::HandleSessionMessage(message);

  if (writing_replay_) {
    assert(g_media_server);
    g_media_server->PushAddMessageToReplayCall(message);
  }
}

}  // namespace ballistica
