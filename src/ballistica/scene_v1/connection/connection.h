// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_CONNECTION_CONNECTION_H_
#define BALLISTICA_SCENE_V1_CONNECTION_CONNECTION_H_

#include <cstdio>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

#include "ballistica/scene_v1/support/player_spec.h"
#include "ballistica/shared/foundation/object.h"

namespace ballistica::scene_v1 {

// Start near the top of the range to make sure looping works as expected.
const int kFirstConnectionStateNum = 65520;

// Extra bytes added to message packets.
// Packet-type flag: the packet's ack field carries a 32-bit have-bitfield
// instead of 8 (kProtocolVersionWideAcks peers). Self-describing, so a
// receiver never has to guess the layout.
const uint8_t kPacketWideAcksFlag = 0x40;
// Ack field: 2-byte next-wanted reliable num + 1 (legacy) or 4 (wide)
// bytes of have-bits for the messages after it.
const int kAckSizeLegacy = 3;
const int kAckSizeWide = 6;
// While the reliable stream has a gap, ack at least this often (instead
// of riding the keepalive cadence) so the sender learns about it.
const millisecs_t kGapAckDelay = 20;
// A message the peer has evidently lost (they already have later ones)
// is resent at least this often instead of waiting out the backoff.
const millisecs_t kLossResendTime = 40;
const millisecs_t kMaxResendTime = 800;

const int kUnreliableMaxParts = 32;
// A complete unreliable message may be this many reliable messages
// behind the receiver's stream and still apply (each is one ~8ms ship).
const int kUnreliableStaleTolerance = 2;
// Partial or held unreliable state older than this is discarded.
const millisecs_t kUnreliableHoldTime = 250;

/// Connection to a remote session; either as a host or client.
class Connection : public Object {
 public:
  Connection();
  ~Connection() override;

  /// Send a reliable message to the client. These will always be delivered
  /// in the order sent.
  void SendReliableMessage(const std::vector<uint8_t>& data);

  /// Send an unreliable message to the client; these are not guaranteed to
  /// be delivered, but when they are, they're delivered properly in order
  /// between other unreliable/reliable messages.
  void SendUnreliableMessage(const std::vector<uint8_t>& data);

  /// Send a json-based reliable message. `val` is the already-serialized
  /// json string (build it with JsonBuilder).
  void SendJMessage(const std::string& val);
  virtual void Update();

  /// Called with raw packets as they come in from the network.
  virtual void HandleGamePacket(const std::vector<uint8_t>& buffer);

  /// Called when the next in-order message is available.
  virtual void HandleMessagePacket(const std::vector<uint8_t>& buffer) = 0;

  /// Request an orderly disconnect.
  virtual void RequestDisconnect() = 0;

  /// Whether the peer is known to speak protocol
  /// kProtocolVersionZstdPackets (so our packets to it may use zstd).
  /// Receiving needs no such knowledge: the codec is read off each
  /// packet's first byte.
  virtual auto PeerSupportsZstdPackets() const -> bool { return false; }

  /// Whether the peer accepts unreliable multipart packets
  /// (BA_SCENEPACKET_MESSAGE_UNRELIABLE_PART; protocol
  /// kProtocolVersionUnreliableParts). Oversized unreliable messages to
  /// other peers fall back to reliable.
  virtual auto PeerSupportsUnreliableParts() const -> bool { return false; }

  /// Whether the peer understands the 32-bit ack have-bitfield
  /// (kPacketWideAcksFlag; protocol kProtocolVersionWideAcks). Receiving
  /// needs no such knowledge: the flag is on each packet's type byte.
  virtual auto PeerSupportsWideAcks() const -> bool { return false; }

  /// Whether the peer accepts packets up to kMaxPacketSizeBig
  /// (protocol kProtocolVersionBigPackets); legacy peers get
  /// kMaxPacketSize.
  virtual auto PeerSupportsBigPackets() const -> bool { return false; }

  /// Receive-side unreliable delivery accounting since the last take.
  struct UnreliableStats {
    int64_t parts_in{};            // Part packets received.
    int64_t reassembled{};         // Multipart messages completed.
    int64_t applied{};             // Messages handed up.
    int64_t held{};                // Complete but ahead of the reliable stream.
    int64_t dropped_stale{};       // Too old, or behind an applied one.
    int64_t dropped_incomplete{};  // Partial superseded or timed out.
  };
  auto TakeStatsUnreliable() -> UnreliableStats {
    return std::exchange(stats_unreliable_, {});
  }
  /// Outgoing packets dropped by the BA_PACKET_LOSS dev aid.
  auto TakeStatsPacketsDropped() -> int64_t {
    return std::exchange(stats_packets_dropped_, 0);
  }

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
  /// Wire accounting since the last take (for stream stats): bytes
  /// handed to the socket (huffman-compressed), the same before
  /// compression, packets, and resent bytes. Every packet type counts.
  auto TakeStatsBytesOutCompressed() -> int64_t {
    return std::exchange(stats_bytes_out_compressed_, 0);
  }
  auto TakeStatsBytesOut() -> int64_t {
    return std::exchange(stats_bytes_out_, 0);
  }
  auto TakeStatsPacketsOut() -> int64_t {
    return std::exchange(stats_packets_out_, 0);
  }
  auto TakeStatsResendBytesOut() -> int64_t {
    return std::exchange(stats_resend_bytes_out_, 0);
  }
  /// Packets since the last take, by packet-type byte (count, bytes on
  /// the wire), and how many landed in the same millisecond as the
  /// packet before them (what coalescing to 1ms buckets would merge).
  struct PacketTypeStats {
    int64_t count{};
    int64_t bytes{};
  };
  auto TakeStatsPacketTypes() -> std::unordered_map<int, PacketTypeStats> {
    return std::exchange(stats_packet_types_, {});
  }
  auto TakeStatsPacketsSameMs() -> int64_t {
    return std::exchange(stats_packets_same_ms_, 0);
  }
  /// Reliable/unreliable messages sent since the last take, by their
  /// message-type byte (count, payload bytes).
  auto TakeStatsMessageTypes() -> std::unordered_map<int, PacketTypeStats> {
    return std::exchange(stats_message_types_, {});
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
  // BA_PACKET_DUMP: raw (pre-compression) outgoing packets, u16
  // length-prefixed, for offline compression experiments.
  FILE* packet_dump_file_{};
  bool packet_dump_checked_{};
  std::unordered_map<int, PacketTypeStats> stats_packet_types_;
  std::unordered_map<int, PacketTypeStats> stats_message_types_;
  int64_t stats_packets_same_ms_{};
  millisecs_t stats_last_packet_ms_{-1};
  int64_t stats_bytes_out_compressed_{};
  int64_t stats_bytes_out_{};
  int64_t stats_packets_out_{};
  int64_t stats_resend_bytes_out_{};
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
  // Unreliable delivery: the sender stamps each unreliable message with
  // the reliable number it was about to send next and a per-reliable
  // unreliable counter (so stamps only ever grow). We apply a message
  // once the reliable stream has reached its stamp (holding one that
  // arrives early), never one older than the last applied, and never
  // one more than kUnreliableStaleTolerance ships behind.
  auto MaxPacketSize_() const -> size_t;
  static auto AckSize_(bool wide) -> int {
    return wide ? kAckSizeWide : kAckSizeLegacy;
  }
  void EmbedAcks_(millisecs_t real_time, std::vector<uint8_t>* data, int offset,
                  bool wide);
  void HandleResends_(millisecs_t real_time, const std::vector<uint8_t>& data,
                      int offset, bool wide);
  void SendAck_(millisecs_t real_time);
  void SendReliablePacket_(uint16_t num, const std::vector<uint8_t>& payload,
                           millisecs_t real_time);
  void DeliverUnreliable_(uint16_t rel, uint16_t unrel,
                          std::vector<uint8_t> data, millisecs_t real_time,
                          bool is_retry = false);
  void RetryHeldUnreliable_();
  void PruneUnreliable_(millisecs_t real_time);
  static auto StampNewer_(uint16_t rel_a, uint16_t unrel_a, uint16_t rel_b,
                          uint16_t unrel_b) -> bool;
  struct UnreliablePartial_ {
    bool active{};
    uint16_t rel{};
    uint16_t unrel{};
    int part_count{};
    uint32_t parts_have{};
    std::vector<std::vector<uint8_t>> parts;
    millisecs_t start_time{};
  };
  struct UnreliableHeld_ {
    bool active{};
    uint16_t rel{};
    uint16_t unrel{};
    std::vector<uint8_t> data;
    millisecs_t time{};
  };
  UnreliablePartial_ unreliable_partial_;
  UnreliableHeld_ unreliable_held_;
  bool have_in_unreliable_{};
  uint16_t in_unreliable_rel_{};
  uint16_t in_unreliable_num_{};
  UnreliableStats stats_unreliable_;
  int64_t stats_packets_dropped_{};
  bool can_communicate_{};
  bool errored_{};
  // Leaf classes should set this when they start dying.
  // This prevents any SendGamePacketCompressed() calls from happening.
  bool connection_dying_{};
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_CONNECTION_CONNECTION_H_
