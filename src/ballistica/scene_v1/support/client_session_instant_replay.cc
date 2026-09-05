// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/support/client_session_instant_replay.h"

#include <utility>
#include <vector>

#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging.h"

namespace ballistica::scene_v1 {

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
  while (commands().empty()) {
    if (next_index_ >= messages_.size()) {
      // Marks the end of the clip; lands in OnEndOfStream above once the
      // interpreter reaches it.
      add_end_of_file_command();
      return;
    }
    HandleSessionMessage(messages_[next_index_]);
    next_index_++;
  }
}

auto ClientSessionInstantReplay::GetActualTimeAdvanceMillisecs(
    double base_advance_millisecs) -> double {
  return base_advance_millisecs * static_cast<double>(speed_);
}

}  // namespace ballistica::scene_v1
