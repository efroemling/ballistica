// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/connection/connection.h"

#include <string>
#include <vector>

#include "ballistica/base/base.h"
#include "ballistica/base/networking/networking.h"
#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging_macros.h"
#include "ballistica/core/platform/core_platform.h"
#include "ballistica/scene_v1/scene_v1.h"
#include "ballistica/scene_v1/support/huffman.h"
#include "ballistica/shared/generic/json.h"
#include "ballistica/shared/math/vector3f.h"

namespace ballistica::scene_v1 {

// How long to go without sending a state packet before
// we send keepalives.  Keepalives contain the latest ack info.
const int kKeepaliveDelay = 100;  // 1000/15

// How long before an individual packet is re-sent if we haven't gotten an ack.
const int kPacketResendTime = 100;

// How old a packet must be before we prune it.
const int kPacketPruneTime = 10000;

// How long to go between pruning our packets.
const int kPacketPruneInterval = 1000;

// How long to go between updating our ping measurement.
const int kPingMeasureInterval = 2000;

Connection::Connection() {
  // NOLINTNEXTLINE(cppcoreguidelines-prefer-member-initializer)
  creation_time_ = last_average_update_time_ = g_core->AppTimeMillisecs();
}

void Connection::ProcessWaitingMessages() {
  // Process waiting in-messages until we find one that's missing.
  while (true) {
    auto i = in_messages_.find(next_in_message_num_);
    if (i == in_messages_.end()) {
      break;
    }
    HandleMessagePacket(i->second.data);
    in_messages_.erase(i);
    next_in_message_num_++;

    // Moving to a new in-message-num also resets our next-unreliable-num.
    next_in_unreliable_message_num_ = 0;
  }
}

void Connection::EmbedAcks(millisecs_t real_time, std::vector<uint8_t>* data,
                           int offset) {
  assert(data);

  // Store full value for the next message num we want.
  memcpy(data->data() + offset, &next_in_message_num_,
         sizeof(next_in_message_num_));

  // Now store a 1-byte bitfield telling which of the 8 messages following
  // next_in_message_num_ we already have. This helps prevent redundant
  // re-sends on the other end if we just missed one random packet, etc.
  uint8_t extra_bits = 0;
  uint16_t num = next_in_message_num_;
  for (uint32_t i = 0; i < 8; i++) {
    if (in_messages_.find(++num) != in_messages_.end()) {
      extra_bits |= (0x01u << i);
    }
  }
  (*data)[offset + 2] = extra_bits;
  last_ack_send_time_ = real_time;
}

void Connection::HandleResends(millisecs_t real_time,
                               const std::vector<uint8_t>& data, int offset) {
  // Pull the next number they want.
  uint16_t their_next_in;
  memcpy(&their_next_in, data.data() + offset, sizeof(their_next_in));

  // Along with a bit-field of which ones after that they already have..
  // (prevents some un-necessary re-sending)
  uint8_t extra_bits = data[offset + 2];

  // Ack packets and take the opportunity to measure ping.
  auto test_num = static_cast<uint16_t>(their_next_in - 1u);
  auto j = out_messages_.find(test_num);
  if (j != out_messages_.end()) {
    ReliableMessageOut& msg(j->second);
    if (!msg.acked) {
      // Periodically use this opportunity to measure ping.
      if (real_time - last_ping_measure_time_ > kPingMeasureInterval) {
        current_ping_ = static_cast<float>(real_time - msg.first_send_time);
        last_ping_measure_time_ = real_time;
      }
    }
    msg.acked = true;
  }

  // Re-send up to 9 un-acked packets if it's been long enough.
  // (their next requested plus their 8 extra-bits)
  uint16_t num = their_next_in;
  for (uint32_t i = 0; i < 9; i++) {
    // If we've reached our next out-number, we havn't sent it yet so we're
    // peachy.
    if (num == next_out_message_num_) break;

    bool they_want_this_packet;
    if (i == 0) {
      // They *always* want the one they're asking for.
      they_want_this_packet = true;
    } else {
      they_want_this_packet = ((extra_bits & (0x01u << (i - 1))) == 0);
    }

    // If we have no record for this out-packet, it's too old; abort the
    // connection.
    auto j2 = out_messages_.find(num);
    if (j2 == out_messages_.end()) {
      Error("");
      return;
    }
    ReliableMessageOut& msg(j2->second);

    // Check with the actual packet for ack state (it may have been acked by
    // another packet but not this one).
    if (!they_want_this_packet) {
      msg.acked = true;
    }

    // If its un-acked and older than our threshold, re-send.
    if (!msg.acked && real_time - msg.last_send_time > msg.resend_time) {
      msg.resend_time *= 2;  // wait twice as long with each resend..
      msg.last_send_time = real_time;

      // Add our header/acks and go ahead and send this one out.
      // 1 byte for type, 2 for packet-num, 3 for acks
      std::vector<uint8_t> data_out(msg.data.size() + kMessagePacketHeaderSize);
      data_out[0] = BA_SCENEPACKET_MESSAGE;
      memcpy(data_out.data() + 1, &num, sizeof(num));
      EmbedAcks(real_time, &data_out, 3);
      memcpy(&(data_out[6]), &(msg.data[0]), msg.data.size());
      SendGamePacket(data_out);
      resend_packet_count_++;
      resend_bytes_out_ += data_out.size();
    }
    num++;
  }
}

void Connection::HandleGamePacketCompressed(const std::vector<uint8_t>& data) {
  std::vector<uint8_t> data_decompressed;
  try {
    data_decompressed = g_scene_v1->huffman->decompress(data);
  } catch (const std::exception& e) {
    // Allow a few of these through just in case it is a fluke, but kill the
    // connection after that to stop attacks based on this.
    BA_LOG_ONCE(
        LogName::kBaNetworking, LogLevel::kError,
        std::string("Error in huffman decompression for packet: ") + e.what());
    huffman_error_count_ += 1;
    if (huffman_error_count_ > 5) {
      BA_LOG_ONCE(LogName::kBaNetworking, LogLevel::kError,
                  "Closing connection due to excessive huffman errors.");
      Error("");
    }
    return;
  }
  bytes_in_compressed_ += data.size();
  HandleGamePacket(data_decompressed);
  packet_count_in_++;
  bytes_in_ += data_decompressed.size();
}

void Connection::HandleGamePacket(const std::vector<uint8_t>& data) {
  // Sub-classes shouldn't let invalid messages get to us.
  assert(!data.empty());

  switch (data[0]) {
    case BA_SCENEPACKET_KEEPALIVE: {
      if (data.size() != 4) {
        BA_LOG_ONCE(LogName::kBaNetworking, LogLevel::kError,
                    "Error: got invalid BA_SCENEPACKET_KEEPALIVE packet.");
        return;
      }
      millisecs_t real_time = g_core->AppTimeMillisecs();
      HandleResends(real_time, data, 1);
      break;
    }

    case BA_SCENEPACKET_MESSAGE: {
      millisecs_t real_time = g_core->AppTimeMillisecs();

      // Expect 1 byte type, 2 byte num, 3 byte acks, at least 1 byte payload.
      if (data.size() < 7) {
        g_core->logging->Log(LogName::kBaNetworking, LogLevel::kError,
                             "Got invalid BA_PACKET_STATE packet.");
        return;
      }
      uint16_t num;
      memcpy(&num, data.data() + 1, sizeof(num));

      // Run any necessary re-sends based on this guy's acks.
      HandleResends(real_time, data, 3);

      // If they're an upcoming message number this difference will be small;
      // otherwise we can ignore them since they're in the past.
      if (num - next_in_message_num_ > 32000) {
        return;
      }

      // Store this packet.
      ReliableMessageIn& msg(in_messages_[num]);
      msg.data.resize(data.size() - 6);
      memcpy(&(msg.data[0]), &(data[6]), msg.data.size());
      msg.arrival_time = g_core->AppTimeMillisecs();

      // Now run all in-order packets we've got.
      ProcessWaitingMessages();

      break;
    }

    case BA_SCENEPACKET_MESSAGE_UNRELIABLE: {
      // Expect 1 byte type, 2 byte num, 2 byte unreliable-num, 3 byte acks,
      // at least 1 byte payload.
      if (data.size() < 9) {
        g_core->logging->Log(LogName::kBaNetworking, LogLevel::kError,
                             "Got invalid BA_PACKET_STATE_UNRELIABLE packet.");
        return;
      }
      uint16_t num, num_unreliable;
      memcpy(&num, data.data() + 1, sizeof(num));
      memcpy(&num_unreliable, data.data() + 3, sizeof(num_unreliable));

      // *ONLY* apply this if its num is the next one we're waiting for and
      // num_unreliable is >= our next unreliable num
      if (num == next_in_message_num_
          && num_unreliable >= next_in_unreliable_message_num_) {
        std::vector<uint8_t> msg_data(data.size() - 8);
        memcpy(&(msg_data[0]), &(data[8]), msg_data.size());
        HandleMessagePacket(msg_data);
        next_in_unreliable_message_num_ =
            static_cast<uint16_t>(num_unreliable + 1u);
      }
      break;
    }

    default:
      g_core->logging->Log(LogName::kBaNetworking, LogLevel::kError,
                           "Connection got unknown packet type: "
                               + std::to_string(static_cast<int>(data[0])));
      break;
  }
}

void Connection::Error(const std::string& msg) {
  // If we've already errored, just ignore.
  if (errored_) {
    return;
  }
  errored_ = true;
  if (!msg.empty()) {
    g_base->ScreenMessage(msg, {1.0f, 0.0, 0.0f});
  }
}

void Connection::SendReliableMessage(const std::vector<uint8_t>& data) {
  assert(!data.empty());

  // If our connection is going down, silently ignore this.
  if (connection_dying_) {
    return;
  }

  // To allow sending messages of any size, we transparently break large
  // messages up into BA_MESSAGE_MULTIPART messages which are transparently
  // re-assembled on the other end.
  if (data.size() > 480) {
    auto data_size = static_cast<uint32_t>(data.size());
    uint32_t part_start = 0;
    uint32_t part_size = 479;
    while (true) {
      // If this takes us to the end of the message, send a multipart-end.
      if ((part_start + part_size) >= data_size) {
        part_size = data_size - part_start;
        assert(part_size > 0);
        // 1 byte type plus data
        std::vector<uint8_t> part_message(1 + part_size);
        part_message[0] = BA_MESSAGE_MULTIPART_END;
        memcpy(&(part_message[1]), &(data[part_start]), part_size);
        SendReliableMessage(part_message);
        return;
      } else {
        std::vector<uint8_t> part_message(1 + part_size);
        part_message[0] = BA_MESSAGE_MULTIPART;
        memcpy(&(part_message[1]), &(data[part_start]), part_size);
        SendReliableMessage(part_message);
      }
      part_start += part_size;
    }
  }

  uint16_t num = next_out_message_num_++;

  // By incrementing reliable-message-num we reset the unreliable num.
  next_out_unreliable_message_num_ = 0;

  // Add an entry for it.
  assert(out_messages_.find(num) == out_messages_.end());
  ReliableMessageOut& msg(out_messages_[num]);

  millisecs_t real_time = g_core->AppTimeMillisecs();

  msg.data = data;
  msg.first_send_time = msg.last_send_time = real_time;
  msg.resend_time = kPacketResendTime;
  msg.acked = false;

  // Add our header/acks and go ahead and send this one out.
  // 1 byte for type, 2 for packet-num, 3 for acks
  std::vector<uint8_t> data_out(data.size() + kMessagePacketHeaderSize);

  data_out[0] = BA_SCENEPACKET_MESSAGE;
  memcpy(data_out.data() + 1, &num, sizeof(num));
  EmbedAcks(real_time, &data_out, 3);
  memcpy(&(data_out[6]), &(data[0]), data.size());
  SendGamePacket(data_out);
}

void Connection::SendUnreliableMessage(const std::vector<uint8_t>& data) {
  // For now we just silently drop anything bigger than our max packet size.
  if (data.size() + 8 > kMaxPacketSize) {
    BA_LOG_ONCE(LogName::kBaNetworking, LogLevel::kError,
                "Error: Dropping outgoing unreliable packet of size "
                    + std::to_string(data.size()) + ".");
    return;
  }

  // If our connection is going down, silently ignore this.
  if (connection_dying_) {
    return;
  }

  uint16_t num = next_out_unreliable_message_num_++;
  millisecs_t real_time = g_core->AppTimeMillisecs();

  // Add our header/acks and go ahead and send this one out.
  // 1 byte for type, 2 for packet-num, 2 for unreliable packet-num, 3 for acks.
  std::vector<uint8_t> data_out(data.size() + 8);

  data_out[0] = BA_SCENEPACKET_MESSAGE_UNRELIABLE;
  memcpy(data_out.data() + 1, &next_out_message_num_,
         sizeof(next_out_message_num_));
  memcpy(data_out.data() + 3, &num, sizeof(num));
  EmbedAcks(real_time, &data_out, 5);
  memcpy(&(data_out[8]), &(data[0]), data.size());
  SendGamePacket(data_out);
}

void Connection::SendJMessage(cJSON* val) {
  char* s = cJSON_PrintUnformatted(val);
  auto s_len = static_cast<size_t>(strlen(s));
  std::vector<uint8_t> msg(1u + s_len + 1u);
  msg[0] = BA_MESSAGE_JMESSAGE;
  memcpy(msg.data() + 1u, s, s_len + 1u);
  free(s);
  SendReliableMessage(msg);
}

void Connection::Update() {
  millisecs_t real_time = g_core->AppTimeMillisecs();

  // Update our averages once per second.
  while (real_time - last_average_update_time_ > 1000) {
    last_average_update_time_ += 1000;  // Don't want this to drift.
    last_resend_packet_count_ = resend_packet_count_;
    last_resend_bytes_out_ = resend_bytes_out_;
    last_bytes_out_ = bytes_out_;
    last_bytes_out_compressed_ = bytes_out_compressed_;
    last_packet_count_out_ = packet_count_out_;
    last_bytes_in_ = bytes_in_;
    last_bytes_in_compressed_ = bytes_in_compressed_;
    last_packet_count_in_ = packet_count_in_;
    bytes_out_ = packet_count_out_ = bytes_out_compressed_ = 0;
    bytes_in_ = bytes_in_compressed_ = packet_count_in_ = 0;
    resend_packet_count_ = resend_bytes_out_ = 0;
  }

  if (can_communicate() && real_time - last_ack_send_time_ > kKeepaliveDelay) {
    // If we haven't sent anything with an ack out in a while, send along
    // a keepalive packet (a packet containing nothing but an ack).

    // 1 byte type, 2 byte next-expected, 1 byte extra-acks.
    std::vector<uint8_t> data(4);
    data[0] = BA_SCENEPACKET_KEEPALIVE;
    EmbedAcks(real_time, &data, 1);
    SendGamePacket(data);
  }

  // Occasionally prune our in and out messages.
  if (real_time - last_prune_time_ > kPacketPruneInterval) {
    last_prune_time_ = real_time;
    {
      int prune_count = 0;
      for (auto i = out_messages_.begin(); i != out_messages_.end();) {
        if (real_time - i->second.first_send_time > kPacketPruneTime) {
          auto i_next = i;
          i_next++;
          out_messages_.erase(i);
          prune_count++;
          i = i_next;
        } else {
          i++;
        }
      }
    }
    {
      int prune_count = 0;
      for (auto i = in_messages_.begin(); i != in_messages_.end();) {
        if (real_time - i->second.arrival_time > kPacketPruneTime) {
          auto i_next = i;
          i_next++;
          in_messages_.erase(i);
          prune_count++;
          i = i_next;
        } else {
          i++;
        }
      }
    }
  }
}

void Connection::HandleMessagePacket(const std::vector<uint8_t>& buffer) {
  switch (buffer[0]) {
    // Re-assemble multipart messages that come in and pass them along as
    // regular messages.
    case BA_MESSAGE_MULTIPART:
    case BA_MESSAGE_MULTIPART_END: {
      if (buffer.size() > 1) {
        // Append everything minus the type byte.
        auto old_size = static_cast<uint32_t>(multipart_buffer_.size());
        multipart_buffer_.resize(old_size + (buffer.size() - 1));
        memcpy(&(multipart_buffer_[old_size]), &(buffer[1]), buffer.size() - 1);
      } else {
        g_core->logging->Log(LogName::kBaNetworking, LogLevel::kError,
                             "got invalid BA_MESSAGE_MULTIPART");
      }
      if (buffer[0] == BA_MESSAGE_MULTIPART_END) {
        if (multipart_buffer_[0] == BA_MESSAGE_MULTIPART) {
          BA_LOG_ONCE(LogName::kBaNetworking, LogLevel::kError,
                      "nested multipart message detected; kicking");
          Error("");
        }
        HandleMessagePacket(multipart_buffer_);
        multipart_buffer_.clear();
      }
      break;
    }
    case BA_MESSAGE_NULL:
      // An empty message that can get thrown around for ping purposes.
      break;
    default: {
      // Let's silently ignore these since we may be adding various
      // messages mid-protocol in a backwards-compatible way.
      //  BA_LOG_ONCE("Got unrecognized packet type:
      //  "+std::to_string(int(buffer[0])));
    }
  }
}

void Connection::SendGamePacket(const std::vector<uint8_t>& data) {
  // Don't want to call a pure-virtual SendGamePacketCompressed().
  if (connection_dying_) {
    return;
  }

  assert(!data.empty());

  // Normally we withhold all packets until we know we speak the
  // same language.  However, DISCONNECT is a special case.
  // (if we don't speak the same language we still need to be
  // able to tell them to buzz off)
  bool can_send = can_communicate();
  if (data[0] == BA_SCENEPACKET_DISCONNECT) {
    can_send = true;
  }

  // We aren't allowed to send anything out except handshakes until
  // we've established that we can speak their language.
  // If something does come through, just ignore it.
  if (!can_send && data[0] != BA_SCENEPACKET_HANDSHAKE
      && data[0] != BA_SCENEPACKET_HANDSHAKE_RESPONSE) {
    if (explicit_bool(false)) {
      BA_LOG_ONCE(
          LogName::kBaNetworking, LogLevel::kError,
          "SendGamePacket() called before can_communicate set ("
              + g_core->platform->DemangleCXXSymbol(typeid(*this).name())
              + " ptype " + std::to_string(static_cast<int>(data[0])) + ")");
    }
    return;
  }

  packet_count_out_++;
  bytes_out_ += data.size();

  // We huffman-compress gamepackets on their way out.
  std::vector<uint8_t> data_compressed = g_scene_v1->huffman->compress(data);

#if kTestPacketDrops
  if (rand() % 100 < kTestPacketDropPercent) {  // NOLINT
    return;
  }
#endif

  bytes_out_compressed_ += data_compressed.size();
  SendGamePacketCompressed(data_compressed);
}

}  // namespace ballistica::scene_v1
