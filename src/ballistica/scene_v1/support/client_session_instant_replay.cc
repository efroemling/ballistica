// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/support/client_session_instant_replay.h"

#include <utility>
#include <vector>

#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging.h"

namespace ballistica::scene_v1 {

// How much clip (in stream time) we keep taken in ahead of playback.
// What we take in goes out to remote viewers right then, so this is the
// cushion their playback has against network jitter; it costs nothing
// locally, where the messages are already in memory.
const int kForwardLeadMillisecs = 500;

ClientSessionInstantReplay::ClientSessionInstantReplay(
    std::vector<std::vector<uint8_t> > messages, float speed,
    int stream_protocol)
    : messages_{std::move(messages)}, speed_{speed} {
  // The window came off our own live stream, so it speaks whatever
  // protocol we host at.
  set_stream_protocol(stream_protocol);

  // Nothing else to set up: ClientSession starts empty and at time zero,
  // and our first FetchMessages feeds it the baseline.
}

ClientSessionInstantReplay::~ClientSessionInstantReplay() = default;

void ClientSessionInstantReplay::FetchMessages() {
  if (complete_) {
    return;
  }
  // Take in messages until we're a lead ahead (or have nothing queued
  // at all; a message with no time step in it, like the baseline, adds
  // commands without adding buffered time).
  while (
      next_index_ < messages_.size()
      && (commands().empty() || base_time_buffered() < kForwardLeadMillisecs)) {
    const auto& message = messages_[next_index_];
    HandleSessionMessage(message);
    if (forwarder_) {
      forwarder_(message);
    }
    next_index_++;
  }
  if (commands().empty() && next_index_ >= messages_.size()) {
    // Marks the end of the clip; lands in OnEndOfStream above once the
    // interpreter reaches it.
    add_end_of_file_command();
  }
}

auto ClientSessionInstantReplay::GetActualTimeAdvanceMillisecs(
    double base_advance_millisecs) -> double {
  return base_advance_millisecs * static_cast<double>(speed_);
}

}  // namespace ballistica::scene_v1
