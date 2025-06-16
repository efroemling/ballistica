// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_CONNECTION_CONNECTION_H_
#define BALLISTICA_SCENE_V1_CONNECTION_CONNECTION_H_

#include <string>
#include <unordered_map>
#include <vector>

#include "ballistica/scene_v1/support/player_spec.h"
#include "ballistica/shared/foundation/object.h"

namespace ballistica::scene_v1 {

// Start near the top of the range to make sure looping works as expected.
const int kFirstConnectionStateNum = 65520;

// Extra bytes added to message packets.
const int kMessagePacketHeaderSize = 6;

/// Connection to a remote session; either as a host or client.
class Connection : public Object {
 public:
  Connection();

  /// Send a reliable message to the client. These will always be delivered
  /// in the order sent.
  void SendReliableMessage(const std::vector<uint8_t>& data);

  /// Send an unreliable message to the client; these are not guaranteed to
  /// be delivered, but when they are, they're delivered properly in order
  /// between other unreliable/reliable messages.
  void SendUnreliableMessage(const std::vector<uint8_t>& data);

  /// Send a json-based reliable message.
  void SendJMessage(cJSON* val);
  virtual void Update();

  /// Called with raw packets as they come in from the network.
  virtual void HandleGamePacket(const std::vector<uint8_t>& buffer);

  /// Called when the next in-order message is available.
  virtual void HandleMessagePacket(const std::vector<uint8_t>& buffer) = 0;

  /// Request an orderly disconnect.
  virtual void RequestDisconnect() = 0;

  auto GetBytesOutPerSecond() const -> int64_t { return last_bytes_out_; }
  auto GetBytesOutPerSecondCompressed() const -> int64_t {
    return last_bytes_out_compressed_;
  }
  auto GetMessagesOutPerSecond() const -> int64_t {
    return last_packet_count_out_;
  }
  auto GetMessageResendsPerSecond() const -> int64_t {
    return last_resend_packet_count_;
  }
  auto GetBytesInPerSecond() const -> int64_t { return last_bytes_in_; }
  auto GetBytesInPerSecondCompressed() const -> int64_t {
    return last_bytes_in_compressed_;
  }
  auto GetMessagesInPerSecond() const -> int64_t {
    return last_packet_count_in_;
  }
  auto GetBytesResentPerSecond() const -> int64_t {
    return last_resend_bytes_out_;
  }
  auto current_ping() const -> float { return current_ping_; }
  auto can_communicate() const -> bool { return can_communicate_; }
  auto peer_spec() const -> const PlayerSpec& { return peer_spec_; }
  void HandleGamePacketCompressed(const std::vector<uint8_t>& data);
  auto errored() const -> bool { return errored_; }
  auto creation_time() const -> millisecs_t { return creation_time_; }
  auto multipart_buffer_size() const -> size_t {
    return multipart_buffer_.size();
  }

 protected:
  void SendGamePacket(const std::vector<uint8_t>& data);
  virtual void SendGamePacketCompressed(const std::vector<uint8_t>& data) = 0;
  void ErrorSilent() { Error(""); }
  virtual void Error(const std::string& error_msg);
  void set_peer_spec(const PlayerSpec& spec) { peer_spec_ = spec; }
  void set_can_communicate(bool val) { can_communicate_ = val; }
  void set_connection_dying(bool val) { connection_dying_ = val; }
  void set_errored(bool val) { errored_ = val; }

 private:
  void ProcessWaitingMessages();
  void HandleResends(millisecs_t real_time, const std::vector<uint8_t>& data,
                     int offset);
  void EmbedAcks(millisecs_t real_time, std::vector<uint8_t>* data, int offset);
  std::vector<uint8_t> multipart_buffer_;

  struct ReliableMessageIn {
    std::vector<uint8_t> data;
    millisecs_t arrival_time;
  };

  struct ReliableMessageOut {
    std::vector<uint8_t> data;
    millisecs_t first_send_time;
    millisecs_t last_send_time;
    millisecs_t resend_time;
    bool acked;
  };

  PlayerSpec peer_spec_;  // Name of the account/device on the other end.
  std::unordered_map<uint16_t, ReliableMessageIn> in_messages_;
  std::unordered_map<uint16_t, ReliableMessageOut> out_messages_;
  int64_t last_resend_bytes_out_{};
  int64_t last_bytes_out_{};
  int64_t last_bytes_out_compressed_{};
  int64_t bytes_out_{};
  int64_t bytes_out_compressed_{};
  int64_t resend_bytes_out_{};
  int64_t last_packet_count_out_{};
  int64_t last_resend_packet_count_{};
  int64_t resend_packet_count_{};
  int64_t packet_count_out_{};
  int64_t last_bytes_in_{};
  int64_t last_bytes_in_compressed_{};
  int64_t bytes_in_{};
  int64_t bytes_in_compressed_{};
  int64_t last_packet_count_in_{};
  int64_t packet_count_in_{};
  millisecs_t last_average_update_time_{};
  millisecs_t creation_time_{};
  millisecs_t last_prune_time_{};
  millisecs_t last_ack_send_time_{};
  millisecs_t last_ping_measure_time_{};
  float current_ping_{};
  int huffman_error_count_{};
  // These are explicitly 16 bit values.
  uint16_t next_out_message_num_ = kFirstConnectionStateNum;
  uint16_t next_out_unreliable_message_num_{};
  uint16_t next_in_message_num_ = kFirstConnectionStateNum;
  uint16_t next_in_unreliable_message_num_{};
  bool can_communicate_{};
  bool errored_{};
  // Leaf classes should set this when they start dying.
  // This prevents any SendGamePacketCompressed() calls from happening.
  bool connection_dying_{};
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_CONNECTION_CONNECTION_H_
