// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_SUPPORT_CLIENT_SESSION_REPLAY_H_
#define BALLISTICA_SCENE_V1_SUPPORT_CLIENT_SESSION_REPLAY_H_

#include <cstdio>
#include <optional>
#include <string>
#include <vector>

#include "ballistica/scene_v1/support/client_controller_interface.h"
#include "ballistica/scene_v1/support/client_session.h"

namespace ballistica::scene_v1 {

/// Read just a replay file's header asset-package listing without
/// starting playback (protocol 39+ files carry it; older files return
/// an empty list). For lightweight consumers -- pre-playback content
/// resolve, Watch-tab requirement display. Returns nullopt on a
/// missing/corrupt/incompatible file. Does blocking file IO; the
/// header is tiny, but call off the logic thread for large-scale use.
auto ReadReplayAssetPackages(const std::string& file_name)
    -> std::optional<std::vector<std::string>>;

// A client-session fed by a replay file.
class ClientSessionReplay : public ClientSession,
                            public ClientControllerInterface {
 public:
  explicit ClientSessionReplay(std::string filename);
  ~ClientSessionReplay() override;
  void OnReset(bool rewind) override;

  // Our ClientControllerInterface implementation.
  auto GetActualTimeAdvanceMillisecs(double base_advance_millisecs)
      -> double override;
  void OnClientConnected(ConnectionToClient* c) override;
  void OnClientDisconnected(ConnectionToClient* c) override;
  void OnCommandBufferUnderrun() override;

  void Error(const std::string& description) override;
  void FetchMessages() override;

  void SeekTo(millisecs_t to_base_time);

 private:
  // Index entry for a state snapshot we can seek back to. The snapshot
  // payload itself (full scene dump + correction messages) lives in a
  // disk spool file, not in memory - long replays accumulate thousands
  // of these and the payloads are large (see FetchMessages).
  struct IntermediateState {
    // Offset of this snapshot's record in the spool file.
    int64_t spool_position_;

    // A position in replay file where we should continue from.
    int64_t file_position_;

    millisecs_t base_time_;
  };

  void RestoreFromCurrentState();
  // Append a snapshot record to the spool, returning its offset or -1
  // on failure (in which case spooling is disabled for the session).
  auto WriteSnapshotToSpool_(
      const std::vector<uint8_t>& message,
      const std::vector<std::vector<uint8_t>>& correction_messages) -> int64_t;
  // Read a snapshot record back from the spool.
  auto ReadSnapshotFromSpool_(
      int64_t spool_position, std::vector<uint8_t>* message,
      std::vector<std::vector<uint8_t>>* correction_messages) -> bool;
  void CloseAndRemoveSpool_();

  /// Spool a snapshot and add it to the seek index. The one way an
  /// IntermediateState gets built, whether the snapshot came off the
  /// file as a keyframe or we derived it ourselves.
  void IndexSnapshot_(
      millisecs_t base_time, const std::vector<uint8_t>& message,
      const std::vector<std::vector<uint8_t>>& correction_messages);

  /// Unpack a BA_MESSAGE_SESSION_KEYFRAME record (protocol 44+) into its
  /// baseline message and correction messages. Returns false if the
  /// record is malformed.
  static auto UnpackKeyframeRecord_(
      const std::vector<uint8_t>& record, millisecs_t* base_time,
      std::vector<uint8_t>* message,
      std::vector<std::vector<uint8_t>>* correction_messages) -> bool;

  // List of passed states which we can rewind to.
  std::vector<IntermediateState> states_;
  IntermediateState current_state_;

  FILE* spool_file_{};
  std::string spool_path_;
  int64_t spool_size_{};
  bool spool_failed_{};

  // Set once we've seen a keyframe record in the file. Such a file
  // supplies its own seek states, so we stop deriving our own (which
  // means no DumpFullState work during playback at all).
  bool have_file_keyframes_{};

  bool is_fast_forwarding_{};
  millisecs_t fast_forward_base_time_{};

  bool have_sent_client_message_{};
  std::vector<ConnectionToClient*> connections_to_clients_;
  std::vector<ConnectionToClient*> connections_to_clients_ignored_;
  std::string file_name_;
  FILE* file_{};
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_SUPPORT_CLIENT_SESSION_REPLAY_H_
