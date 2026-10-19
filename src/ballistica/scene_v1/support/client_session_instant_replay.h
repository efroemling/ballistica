// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_SUPPORT_CLIENT_SESSION_INSTANT_REPLAY_H_
#define BALLISTICA_SCENE_V1_SUPPORT_CLIENT_SESSION_INSTANT_REPLAY_H_

#include <functional>
#include <utility>
#include <vector>

#include "ballistica/scene_v1/support/client_session.h"

namespace ballistica::scene_v1 {

/// Plays back a short window of stream held in memory (see
/// InstantReplayRecorder) while the live session sits suspended behind it.
///
/// Deliberately much smaller than ClientSessionReplay: no file, no seek
/// spool, and -- importantly -- it neither registers as the global client
/// controller nor disconnects anybody. The live host session still owns
/// the connections; we are only borrowing the screen.
class ClientSessionInstantReplay : public ClientSession {
 public:
  /// `messages` is a self-contained sequence starting with a full-state
  /// baseline. `speed` scales playback (0.4 for slow motion, 1.0 for
  /// real time). `stream_protocol` is the protocol the window was
  /// recorded at.
  ClientSessionInstantReplay(std::vector<std::vector<uint8_t> > messages,
                             float speed, int stream_protocol);
  ~ClientSessionInstantReplay() override;

  void OnEndOfStream() override { complete_ = true; }
  void FetchMessages() override;
  auto GetActualTimeAdvanceMillisecs(double base_advance_millisecs)
      -> double override;

  /// Pause rather than skip ahead if we somehow run dry mid-clip.
  void OnCommandBufferUnderrun() override { ResetTargetBaseTime(); }

  /// True once the clip has run out. The app-mode watches for this and
  /// hands the screen back to the live session; we can't do it ourselves
  /// because we'd be destroying our own caller mid-update.
  auto complete() const -> bool { return complete_; }

  /// Have each message passed to `forwarder` as we take it in, which is
  /// how remote viewers get the clip: paced by our own playback (plus a
  /// short lead) rather than all at once. Set before the first update.
  void set_forwarder(
      std::function<void(const std::vector<uint8_t>&)> forwarder) {
    forwarder_ = std::move(forwarder);
  }

 private:
  std::vector<std::vector<uint8_t> > messages_;
  std::function<void(const std::vector<uint8_t>&)> forwarder_;
  size_t next_index_{};
  float speed_;
  bool complete_{};
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_SUPPORT_CLIENT_SESSION_INSTANT_REPLAY_H_
