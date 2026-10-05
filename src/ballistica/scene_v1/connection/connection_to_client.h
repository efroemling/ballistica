// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_CONNECTION_CONNECTION_TO_CLIENT_H_
#define BALLISTICA_SCENE_V1_CONNECTION_CONNECTION_TO_CLIENT_H_

#include <string>
#include <unordered_map>
#include <vector>

#include "ballistica/scene_v1/connection/connection.h"
#include "ballistica/scene_v1/scene_v1.h"
#include "ballistica/shared/python/python_ref.h"

namespace ballistica::scene_v1 {

/// Connection to a party client if we're the host.
class ConnectionToClient : public Connection {
 public:
  explicit ConnectionToClient(int id);
  ~ConnectionToClient() override;
  void Update() override;
  void HandleMessagePacket(const std::vector<uint8_t>& buffer) override;
  void HandleGamePacket(const std::vector<uint8_t>& buffer) override;
  auto id() const -> int { return id_; }

  // More efficient than dynamic_cast (hmm do we still want this?).
  virtual auto GetAsUDP() -> ConnectionToClientUDP*;
  void SetController(ClientControllerInterface* c);
  auto GetPlayerProfiles() const -> PyObject* { return player_profiles_.get(); }
  /// The classic-inventory purchase legacy-ids owned by this client's
  /// account as provided by the master server, or ``Py_None`` /
  /// ``nullptr`` when no list was provided (non-v2-auth connection,
  /// older master-server version, or master-server-side unknown).
  /// Python-side callers should treat all "absent" cases as
  /// ``None``.
  auto GetClassicPurchases() const -> PyObject* {
    return classic_purchases_.get();
  }
  /// This client's account's cloud profiles as cloud-composed
  /// character json strings (list of str), as provided by the master
  /// server via v2-auth, or ``Py_None`` / ``nullptr`` when none were
  /// provided (non-v2-auth connection, older master, unknown). The
  /// lobby offers these instead of the legacy ``player_profiles``.
  auto GetCloudCharacters() const -> PyObject* {
    return cloud_characters_.get();
  }
  auto build_number() const -> int { return build_number_; }
  /// Send a screen-message. ``s`` is the legacy flat/resource-json text
  /// every build understands; ``tagged``, when non-empty, is a lang-str
  /// tagged wire value (see kLangStrWireTag*) shipped alongside it --
  /// new enough clients prefer it and render in their own locale.
  void SendScreenMessage(const std::string& s, float r = 1.0f, float g = 1.0f,
                         float b = 1.0f,
                         const std::string& tagged = std::string());

  /// Send a post-handshake join-rejection reason CODE (a BA_REJECT_REASON_*
  /// value) as a BA_JMESSAGE_REJECT_REASON; the joiner renders its own
  /// localized string. Only understood by peers at or above
  /// BA_REJECT_REASON_MIN_BUILD; gate the call on build_number().
  void SendRejectReason(int reason);
  auto token() const -> const std::string& { return token_; }
  void HandleMasterServerClientInfo(PyObject* info_obj);

  /// Return the public id for this client. If they have not been verified
  /// by the master-server, returns an empty string.
  auto peer_public_account_id() const -> const std::string& {
    return peer_public_account_id_;
  }

  /// Whether our handshake offered this client v2-auth. Decided once,
  /// at our first handshake send, from the app mode's ClientAuthMode
  /// (optional mode offers it only if we have a global app-instance id
  /// then), and fixed for the connection: the client latches whatever
  /// our first handshake says.
  auto v2_auth_offered() const { return v2_auth_offered_; }

  /// Whether this client authenticated through v2-auth (so its peer
  /// spec, account id, and profiles came verified from the cloud).
  /// Always true for an accepted client when auth is required; for
  /// optional auth, only for those that could.
  auto v2_authed() const { return v2_authed_; }

  /// Return whether this client is an admin. Will only return true once their
  /// account id has been verified by the master server.
  auto IsAdmin() const -> bool;

  auto kick_voted() const { return kick_voted_; }
  auto set_kick_voted(bool val) { kick_voted_ = val; }
  auto kick_vote_choice() const { return kick_vote_choice_; }
  auto set_kick_vote_choice(bool val) { kick_vote_choice_ = val; }
  auto set_next_kick_vote_allow_time(millisecs_t val) {
    next_kick_vote_allow_time_ = val;
  }
  auto next_kick_vote_allow_time() const { return next_kick_vote_allow_time_; }
  auto public_device_id() const { return public_device_id_; }
  // Returns a spec for this client that incorporates their player names
  // or their peer name if they have no players.
  auto GetCombinedSpec() -> PlayerSpec;

  auto protocol_version() const {
    assert(protocol_version_ != -1);
    return protocol_version_;
  }
  auto PeerSupportsZstdPackets() const -> bool override {
    // Set once the client's handshake response has claimed a version
    // matching ours; before that (our own handshake) it's huffman.
    return can_communicate()
           && protocol_version_ >= kProtocolVersionZstdPackets;
  }
  auto PeerSupportsUnreliableParts() const -> bool override {
    return can_communicate()
           && protocol_version_ >= kProtocolVersionUnreliableParts;
  }
  auto PeerSupportsWideAcks() const -> bool override {
    return can_communicate() && protocol_version_ >= kProtocolVersionWideAcks;
  }
  auto PeerSupportsBigPackets() const -> bool override {
    return can_communicate() && protocol_version_ >= kProtocolVersionBigPackets;
  }

  /// Protocol version the client claimed in its CLIENT_REQUEST packet, or
  /// -1 if we never saw one. Note this is client-supplied and completely
  /// unverified (we don't gate connects on it), so treat it as a
  /// diagnostic hint only -- it is useful mainly for telling stock
  /// clients apart from hand-rolled ones when a join goes wrong.
  auto client_claimed_protocol_version() const {
    return client_claimed_protocol_version_;
  }
  void set_client_claimed_protocol_version(int val) {
    client_claimed_protocol_version_ = val;
  }

 private:
  auto GetClientInputDevice(int remote_id) -> ClientInputDevice*;
  void Error(const std::string& error_msg) override;
  auto ApplyV2AuthToken_(const std::string& token) -> bool;

  int protocol_version_;
  int client_claimed_protocol_version_{-1};
  std::string our_handshake_player_spec_str_;
  std::string our_handshake_salt_;
  std::string peer_public_account_id_;
  std::string public_device_id_;
  ClientControllerInterface* controller_{};
  std::unordered_map<int, ClientInputDevice*> client_input_devices_;
  millisecs_t last_hand_shake_send_time_{};
  int id_{-1};
  int build_number_{};
  bool got_client_info_{};
  bool kick_voted_{};
  bool kick_vote_choice_{};
  std::string token_;
  std::string peer_hash_;
  PythonRef player_profiles_;
  PythonRef classic_purchases_;
  PythonRef cloud_characters_;
  bool got_v1_auth_from_master_server_{};
  bool v2_auth_decided_{};
  bool v2_auth_offered_{};
  bool v2_auth_required_{};
  bool v2_authed_{};
  std::string v2_auth_app_instance_id_;
  std::vector<millisecs_t> last_chat_times_;
  millisecs_t next_kick_vote_allow_time_{};
  millisecs_t chat_block_time_{};
  millisecs_t last_remove_player_time_{-99999};
  int next_chat_block_seconds_{10};
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_CONNECTION_CONNECTION_TO_CLIENT_H_
