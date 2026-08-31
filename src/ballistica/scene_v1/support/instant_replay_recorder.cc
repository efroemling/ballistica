// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/support/instant_replay_recorder.h"

#include <utility>
#include <vector>

namespace ballistica::scene_v1 {

InstantReplayRecorder::InstantReplayRecorder(millisecs_t window_millisecs,
                                             size_t max_bytes) {
  window_millisecs_ = window_millisecs;
  max_bytes_ = max_bytes;
}

void InstantReplayRecorder::AddKeyframe(
    millisecs_t base_time, std::vector<uint8_t> baseline,
    std::vector<std::vector<uint8_t> > corrections) {
  Segment_ segment;
  segment.base_time = base_time;
  segment.bytes = baseline.size();
  for (auto&& correction : corrections) {
    segment.bytes += correction.size();
  }
  segment.baseline = std::move(baseline);
  segment.corrections = std::move(corrections);

  total_bytes_ += segment.bytes;
  segments_.push_back(std::move(segment));
  Prune_();
}

void InstantReplayRecorder::AddMessage(const std::vector<uint8_t>& message) {
  if (segments_.empty()) {
    // Nothing to hang this off of yet; a delta with no keyframe in front
    // of it can never be replayed.
    return;
  }
  segments_.back().bytes += message.size();
  total_bytes_ += message.size();
  segments_.back().deltas.push_back(message);
  Prune_();
}

void InstantReplayRecorder::Prune_() {
  // Keep the last segment no matter what -- without a keyframe there is
  // no window at all, and a single oversized segment is still better than
  // nothing.
  while (segments_.size() > 1) {
    // The front segment is only needed if the one after it doesn't yet
    // reach back far enough to cover our window.
    bool second_covers_window =
        (newest_base_time_() - segments_[1].base_time) >= window_millisecs_;
    bool over_budget = total_bytes_ > max_bytes_;
    if (!second_covers_window && !over_budget) {
      break;
    }
    total_bytes_ -= segments_.front().bytes;
    segments_.pop_front();
  }
}

auto InstantReplayRecorder::available_millisecs() const -> millisecs_t {
  if (segments_.empty()) {
    return 0;
  }
  return newest_base_time_() - segments_.front().base_time;
}

auto InstantReplayRecorder::BuildWindow(millisecs_t duration_millisecs) const
    -> std::vector<std::vector<uint8_t> > {
  std::vector<std::vector<uint8_t> > out;
  if (segments_.empty()) {
    return out;
  }

  // Start from the newest keyframe that is still old enough to cover what
  // was asked for; if none is, we start from the oldest we have and the
  // clip is simply shorter than requested.
  size_t start{};
  for (size_t i = 0; i < segments_.size(); i++) {
    if ((newest_base_time_() - segments_[i].base_time) >= duration_millisecs) {
      start = i;
    } else {
      break;
    }
  }

  out.push_back(segments_[start].baseline);
  for (auto&& correction : segments_[start].corrections) {
    out.push_back(correction);
  }
  for (size_t i = start; i < segments_.size(); i++) {
    for (auto&& delta : segments_[i].deltas) {
      out.push_back(delta);
    }
  }
  return out;
}

}  // namespace ballistica::scene_v1
