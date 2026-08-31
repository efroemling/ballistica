// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_SUPPORT_INSTANT_REPLAY_RECORDER_H_
#define BALLISTICA_SCENE_V1_SUPPORT_INSTANT_REPLAY_RECORDER_H_

#include <cstdint>
#include <deque>
#include <vector>

#include "ballistica/scene_v1/scene_v1.h"

namespace ballistica::scene_v1 {

/// Keeps the most recent few seconds of a live session stream in memory so
/// it can be played back immediately (see ClientSessionInstantReplay).
///
/// The stream itself is a delta log, so a window of it only means
/// something when it starts from a full-state keyframe. We therefore hold
/// a short chain of segments, each one a keyframe followed by the delta
/// messages that came after it; playing a window means replaying one
/// segment's keyframe and then every delta from there on.
///
/// Only the keyframes cost anything to produce -- the deltas are the very
/// messages SessionStream already built for clients and the replay file,
/// so we just keep a reference window of them. Owned by SessionStream,
/// which feeds it.
class InstantReplayRecorder {
 public:
  InstantReplayRecorder(millisecs_t window_millisecs, size_t max_bytes);

  /// Begin a new segment. Called on the keyframe cadence. Takes
  /// ownership of the buffers; a keyframe is large and the caller is
  /// done with it.
  void AddKeyframe(millisecs_t base_time, std::vector<uint8_t> baseline,
                   std::vector<std::vector<uint8_t> > corrections);

  /// Append a delta message to the current segment. Messages arriving
  /// before the first keyframe are dropped, since nothing could replay
  /// them.
  void AddMessage(const std::vector<uint8_t>& message);

  /// Build a playable message sequence covering (at most) the last
  /// `duration_millisecs` of stream time: a keyframe old enough to cover
  /// the request, then every message since. Empty if we have nothing
  /// usable yet.
  auto BuildWindow(millisecs_t duration_millisecs) const
      -> std::vector<std::vector<uint8_t> >;

  /// Stream time covered by what we currently hold.
  auto available_millisecs() const -> millisecs_t;

 private:
  struct Segment_ {
    millisecs_t base_time;
    std::vector<uint8_t> baseline;
    std::vector<std::vector<uint8_t> > corrections;
    std::vector<std::vector<uint8_t> > deltas;
    size_t bytes;
  };

  /// Drop whole segments off the front until we're inside both our time
  /// window and our byte cap. We always keep at least one segment, since
  /// a window with no keyframe is unplayable.
  void Prune_();

  /// Base time of the newest segment; only meaningful when non-empty.
  auto newest_base_time_() const -> millisecs_t {
    return segments_.back().base_time;
  }

  std::deque<Segment_> segments_;
  millisecs_t window_millisecs_;
  size_t max_bytes_;
  size_t total_bytes_{};
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_SUPPORT_INSTANT_REPLAY_RECORDER_H_
