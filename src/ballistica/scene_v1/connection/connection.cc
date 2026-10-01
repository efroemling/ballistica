// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/connection/connection.h"

#include <algorithm>
#include <cstdio>
#include <cstdlib>
#include <string>
#include <utility>
#include <vector>

#include "ballistica/base/base.h"
#include "ballistica/base/networking/networking.h"
#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging_macros.h"
#include "ballistica/core/platform/platform.h"
#include "ballistica/scene_v1/scene_v1.h"
#include "ballistica/scene_v1/support/huffman.h"
#include "ballistica/scene_v1/support/zstd_packet_codec.h"
#include "ballistica/shared/math/random.h"
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

Connection::~Connection() {
  if (packet_dump_file_) {
    fclose(packet_dump_file_);
  }
}

Connection::Connection() {
  // NOLINTNEXTLINE(cppcoreguidelines-prefer-member-initializer)
  creation_time_ = last_average_update_time_ = g_core->AppTimeMillisecs();
}

void Connection::ProcessWaitingMessages() {
  // Process waiting in-messages until we find one that's missing.
  bool advanced = false;
  while (true) {
    auto i = in_messages_.find(next_in_message_num_);
    if (i == in_messages_.end()) {
      break;
    }
    HandleMessagePacket(i->second.data);
    in_messages_.erase(i);
    next_in_message_num_++;
    advanced = true;
    // A complete unreliable message that arrived ahead of the reliable
    // stream applies at exactly its stamp: after a resend lands we can
    // chew through a whole backlog here, so waiting until the loop
    // ends would jump past its window.
    if (unreliable_held_.active
        && unreliable_held_.rel == next_in_message_num_) {
      RetryHeldUnreliable_();
    }
  }
  if (advanced) {
    if (unreliable_held_.active) {
      RetryHeldUnreliable_();
    }
    PruneUnreliable_(g_core->AppTimeMillisecs());
  }
}

void Connection::RetryHeldUnreliable_() {
  UnreliableHeld_ held = std::move(unreliable_held_);
  unreliable_held_ = {};
  DeliverUnreliable_(held.rel, held.unrel, std::move(held.data), held.time,
                     true);
}

auto Connection::StampNewer_(uint16_t rel_a, uint16_t unrel_a, uint16_t rel_b,
                             uint16_t unrel_b) -> bool {
  auto drel = static_cast<int16_t>(rel_a - rel_b);
  if (drel != 0) {
    return drel > 0;
  }
  return static_cast<int16_t>(unrel_a - unrel_b) > 0;
}

void Connection::DeliverUnreliable_(uint16_t rel, uint16_t unrel,
                                    std::vector<uint8_t> data,
                                    millisecs_t real_time, bool is_retry) {
  // Never apply anything older than what we've already applied.
  if (have_in_unreliable_
      && !StampNewer_(rel, unrel, in_unreliable_rel_, in_unreliable_num_)) {
    stats_unreliable_.dropped_stale++;
    return;
  }
  // rel is the reliable message the sender was about to send after this;
  // we may apply once we've processed everything before it, and for a
  // few ships past that (the state is then at most ~16ms old).
  auto behind = static_cast<int16_t>(next_in_message_num_ - rel);
  if (behind < 0) {
    // Ahead of our reliable stream (reordered, or the stream is waiting
    // on a resend): hold it until we catch up. Anything newer replaces
    // it.
    if (!unreliable_held_.active
        || StampNewer_(rel, unrel, unreliable_held_.rel,
                       unreliable_held_.unrel)) {
      if (unreliable_held_.active) {
        stats_unreliable_.dropped_stale++;
      }
      unreliable_held_ = {true, rel, unrel, std::move(data), real_time};
      if (!is_retry) {
        stats_unreliable_.held++;
      }
    } else {
      stats_unreliable_.dropped_stale++;
    }
    return;
  }
  if (behind > kUnreliableStaleTolerance) {
    stats_unreliable_.dropped_stale++;
    return;
  }
  have_in_unreliable_ = true;
  in_unreliable_rel_ = rel;
  in_unreliable_num_ = unrel;
  stats_unreliable_.applied++;
  HandleMessagePacket(data);
}

void Connection::PruneUnreliable_(millisecs_t real_time) {
  if (unreliable_partial_.active) {
    auto behind =
        static_cast<int16_t>(next_in_message_num_ - unreliable_partial_.rel);
    if (behind > kUnreliableStaleTolerance
        || real_time - unreliable_partial_.start_time > kUnreliableHoldTime) {
      unreliable_partial_ = {};
      stats_unreliable_.dropped_incomplete++;
    }
  }
  if (unreliable_held_.active
      && real_time - unreliable_held_.time > kUnreliableHoldTime) {
    unreliable_held_ = {};
    stats_unreliable_.dropped_stale++;
  }
}

void Connection::EmbedAcks_(millisecs_t real_time, std::vector<uint8_t>* data,
                            int offset, bool wide) {
  assert(data);

  // Store full value for the next message num we want.
  memcpy(data->data() + offset, &next_in_message_num_,
         sizeof(next_in_message_num_));

  // Then a bitfield telling which of the messages following
  // next_in_message_num_ we already have (8 of them legacy, 32 wide),
  // so the other end resends only what's actually missing.
  int nbits = wide ? 32 : 8;
  uint32_t have_bits = 0;
  uint16_t num = next_in_message_num_;
  for (int i = 0; i < nbits; i++) {
    if (in_messages_.find(++num) != in_messages_.end()) {
      have_bits |= (1u << i);
    }
  }
  if (wide) {
    memcpy(data->data() + offset + 2, &have_bits, sizeof(have_bits));
  } else {
    (*data)[offset + 2] = static_cast<uint8_t>(have_bits & 0xff);
  }
  last_ack_send_time_ = real_time;
}

void Connection::HandleResends_(millisecs_t real_time,
                                const std::vector<uint8_t>& data, int offset,
                                bool wide) {
  // Pull the next number they want.
  uint16_t their_next_in;
  memcpy(&their_next_in, data.data() + offset, sizeof(their_next_in));

  // Along with a bit-field of which ones after that they already have.
  uint32_t have_bits;
  int nbits;
  if (wide) {
    memcpy(&have_bits, data.data() + offset + 2, sizeof(have_bits));
    nbits = 32;
  } else {
    have_bits = data[offset + 2];
    nbits = 8;
  }

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

  // Re-send un-acked messages they're missing: the one they're asking
  // for plus any zero in their have-bits.
  uint16_t num = their_next_in;
  for (int i = 0; i < nbits + 1; i++) {
    // If we've reached our next out-number, we haven't sent it yet so
    // we're peachy.
    if (num == next_out_message_num_) break;

    bool they_want_this_packet;
    if (i == 0) {
      // They *always* want the one they're asking for.
      they_want_this_packet = true;
    } else {
      they_want_this_packet = ((have_bits & (1u << (i - 1))) == 0);
    }

    // If we have no record for this out-packet, it's too old; abort the
    // connection.
    auto j2 = out_messages_.find(num);
    if (j2 == out_messages_.end()) {
      g_core->logging->Log(LogName::kBaNetworking, LogLevel::kError,
                           "Dropping connection: peer wants reliable message "
                               + std::to_string(num) + " (their next-in "
                               + std::to_string(their_next_in)
                               + ", our next-out "
                               + std::to_string(next_out_message_num_) + ", "
                               + std::to_string(out_messages_.size())
                               + " kept) which we no longer have.");
      Error("");
      return;
    }
    ReliableMessageOut& msg(j2->second);

    // Check with the actual packet for ack state (it may have been acked by
    // another packet but not this one).
    if (!they_want_this_packet) {
      msg.acked = true;
    }

    if (!msg.acked) {
      // If they already have something after this one it's lost rather
      // than merely late (reordering aside), so resend on a short fuse
      // instead of waiting out the backoff.
      bool lost = (have_bits >> i) != 0;
      millisecs_t wait = msg.resend_time;
      if (lost) {
        wait = std::min(
            wait, std::max(kLossResendTime,
                           static_cast<millisecs_t>(current_ping_ * 0.75f)));
      }
      if (real_time - msg.last_send_time > wait) {
        msg.resend_time = std::min(msg.resend_time * 2, kMaxResendTime);
        msg.last_send_time = real_time;
        SendReliablePacket_(num, msg.data, real_time);
        resend_packet_count_++;
        resend_bytes_out_ += static_cast<int64_t>(msg.data.size());
        stats_resend_bytes_out_ += static_cast<int64_t>(msg.data.size());
      }
    }
    num++;
  }
}

void Connection::HandleGamePacketCompressed(const std::vector<uint8_t>& data) {
  std::vector<uint8_t> data_decompressed;
  try {
    if (ZstdPacketCodec::IsZstdPacket(data)) {
      if (!g_scene_v1->zstd_packets) {
        throw Exception("zstd packet received with no codec installed");
      }
      data_decompressed = g_scene_v1->zstd_packets->decompress(data);
    } else {
      data_decompressed = g_scene_v1->huffman->decompress(data);
    }
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

  // Wide-ack packets carry a 4-byte have-bitfield instead of 1.
  bool wide = (data[0] & kPacketWideAcksFlag) != 0;
  auto type = static_cast<uint8_t>(data[0] & ~kPacketWideAcksFlag);
  int ack_size = AckSize_(wide);

  switch (type) {
    case BA_SCENEPACKET_KEEPALIVE: {
      if (data.size() != static_cast<size_t>(1 + ack_size)) {
        BA_LOG_ONCE(LogName::kBaNetworking, LogLevel::kError,
                    "Error: got invalid BA_SCENEPACKET_KEEPALIVE packet.");
        return;
      }
      millisecs_t real_time = g_core->AppTimeMillisecs();
      HandleResends_(real_time, data, 1, wide);
      break;
    }

    case BA_SCENEPACKET_MESSAGE: {
      millisecs_t real_time = g_core->AppTimeMillisecs();

      // 1 type, 2 num, acks, at least 1 byte payload.
      size_t header = 3 + static_cast<size_t>(ack_size);
      if (data.size() < header + 1) {
        g_core->logging->Log(LogName::kBaNetworking, LogLevel::kError,
                             "Got invalid BA_PACKET_STATE packet.");
        return;
      }
      uint16_t num;
      memcpy(&num, data.data() + 1, sizeof(num));

      // Run any necessary re-sends based on this guy's acks.
      HandleResends_(real_time, data, 3, wide);

      // If they're an upcoming message number this difference will be small;
      // otherwise we can ignore them since they're in the past.
      if (num - next_in_message_num_ > 32000) {
        return;
      }

      // Store this packet.
      ReliableMessageIn& msg(in_messages_[num]);
      msg.data.assign(data.begin() + static_cast<ptrdiff_t>(header),
                      data.end());
      msg.arrival_time = real_time;

      // Now run all in-order packets we've got.
      ProcessWaitingMessages();

      // Anything still queued means we're missing something before it.
      // Tell the sender promptly rather than waiting for the keepalive
      // cadence; every packet we send carries the have-bits, so this
      // is what turns one lost packet into one quick resend.
      if (!in_messages_.empty()
          && real_time - last_ack_send_time_ >= kGapAckDelay) {
        SendAck_(real_time);
      }
      break;
    }

    case BA_SCENEPACKET_MESSAGE_UNRELIABLE: {
      // 1 type, 2 reliable-num, 2 unreliable-num, acks, >= 1 payload.
      size_t header = 5 + static_cast<size_t>(ack_size);
      if (data.size() < header + 1) {
        g_core->logging->Log(LogName::kBaNetworking, LogLevel::kError,
                             "Got invalid BA_PACKET_STATE_UNRELIABLE packet.");
        return;
      }
      millisecs_t real_time = g_core->AppTimeMillisecs();
      uint16_t num, num_unreliable;
      memcpy(&num, data.data() + 1, sizeof(num));
      memcpy(&num_unreliable, data.data() + 3, sizeof(num_unreliable));
      HandleResends_(real_time, data, 5, wide);
      std::vector<uint8_t> msg_data(
          data.begin() + static_cast<ptrdiff_t>(header), data.end());
      DeliverUnreliable_(num, num_unreliable, std::move(msg_data), real_time);
      break;
    }

    case BA_SCENEPACKET_MESSAGE_UNRELIABLE_PART: {
      // As above plus 1 part-index, 1 part-count.
      size_t header = 7 + static_cast<size_t>(ack_size);
      if (data.size() < header + 1) {
        BA_LOG_ONCE(LogName::kBaNetworking, LogLevel::kError,
                    "Got invalid BA_SCENEPACKET_MESSAGE_UNRELIABLE_PART"
                    " packet.");
        return;
      }
      millisecs_t real_time = g_core->AppTimeMillisecs();
      uint16_t num, num_unreliable;
      memcpy(&num, data.data() + 1, sizeof(num));
      memcpy(&num_unreliable, data.data() + 3, sizeof(num_unreliable));
      HandleResends_(real_time, data, 5, wide);
      int part_index = data[5 + ack_size];
      int part_count = data[6 + ack_size];
      if (part_count < 2 || part_count > kUnreliableMaxParts
          || part_index >= part_count) {
        BA_LOG_ONCE(LogName::kBaNetworking, LogLevel::kError,
                    "Got unreliable part with bad index/count.");
        return;
      }
      stats_unreliable_.parts_in++;
      auto& partial = unreliable_partial_;
      if (partial.active
          && (partial.rel != num || partial.unrel != num_unreliable)) {
        if (!StampNewer_(num, num_unreliable, partial.rel, partial.unrel)) {
          // A straggler from an older message; ignore it.
          return;
        }
        // A newer message has started; the old one can never complete.
        // (All-or-nothing: we never apply a partial.)
        partial = {};
        stats_unreliable_.dropped_incomplete++;
      }
      if (!partial.active) {
        partial.active = true;
        partial.rel = num;
        partial.unrel = num_unreliable;
        partial.part_count = part_count;
        partial.parts_have = 0;
        partial.parts.assign(static_cast<size_t>(part_count), {});
        partial.start_time = real_time;
      } else if (partial.part_count != part_count) {
        BA_LOG_ONCE(LogName::kBaNetworking, LogLevel::kError,
                    "Unreliable part count changed mid-message.");
        partial = {};
        return;
      }
      uint32_t bit = 1u << part_index;
      if (partial.parts_have & bit) {
        break;  // Duplicate.
      }
      partial.parts[part_index].assign(
          data.begin() + static_cast<ptrdiff_t>(header), data.end());
      partial.parts_have |= bit;
      uint32_t all = part_count >= 32 ? 0xffffffffu : ((1u << part_count) - 1u);
      if (partial.parts_have == all) {
        std::vector<uint8_t> msg_data;
        for (auto& part : partial.parts) {
          msg_data.insert(msg_data.end(), part.begin(), part.end());
        }
        partial = {};
        stats_unreliable_.reassembled++;
        DeliverUnreliable_(num, num_unreliable, std::move(msg_data), real_time);
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
  g_core->logging->Log(LogName::kBaNetworking, LogLevel::kDebug, [this, &msg] {
    return "Connection errored ("
           + g_core->platform->DemangleCXXSymbol(typeid(*this).name()) + "): '"
           + msg + "'.";
  });
  if (!msg.empty()) {
    g_base->ScreenMessage(msg, {1.0f, 0.0, 0.0f});
  }
}

auto Connection::MaxPacketSize_() const -> size_t {
  return static_cast<size_t>(PeerSupportsBigPackets() ? kMaxPacketSizeBig
                                                      : kMaxPacketSize);
}

void Connection::SendReliablePacket_(uint16_t num,
                                     const std::vector<uint8_t>& payload,
                                     millisecs_t real_time) {
  // 1 type, 2 packet-num, acks, payload.
  bool wide = PeerSupportsWideAcks();
  size_t header = 3 + static_cast<size_t>(AckSize_(wide));
  std::vector<uint8_t> data_out(payload.size() + header);
  data_out[0] = static_cast<uint8_t>(BA_SCENEPACKET_MESSAGE
                                     | (wide ? kPacketWideAcksFlag : 0));
  memcpy(data_out.data() + 1, &num, sizeof(num));
  EmbedAcks_(real_time, &data_out, 3, wide);
  memcpy(data_out.data() + header, payload.data(), payload.size());
  SendGamePacket(data_out);
}

void Connection::SendAck_(millisecs_t real_time) {
  // A keepalive is nothing but an ack: 1 type + the ack field.
  bool wide = PeerSupportsWideAcks();
  std::vector<uint8_t> data(1 + static_cast<size_t>(AckSize_(wide)));
  data[0] = static_cast<uint8_t>(BA_SCENEPACKET_KEEPALIVE
                                 | (wide ? kPacketWideAcksFlag : 0));
  EmbedAcks_(real_time, &data, 1, wide);
  SendGamePacket(data);
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
  // Chunk to the peer's packet budget (legacy peers keep the historical
  // 480-byte chunks); each chunk message is 1 type byte + payload.
  auto chunk = static_cast<uint32_t>(
      PeerSupportsBigPackets()
          ? MaxPacketSize_() - 3
                - static_cast<size_t>(AckSize_(PeerSupportsWideAcks()))
          : 480);
  if (data.size() > chunk) {
    auto data_size = static_cast<uint32_t>(data.size());
    uint32_t part_start = 0;
    uint32_t part_size = chunk - 1;
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
  {
    auto& mt = stats_message_types_[data[0]];
    mt.count++;
    mt.bytes += static_cast<int64_t>(data.size());
  }

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

  SendReliablePacket_(num, data, real_time);
}

void Connection::SendUnreliableMessage(const std::vector<uint8_t>& data) {
  assert(!data.empty());

  // If our connection is going down, silently ignore this.
  if (connection_dying_) {
    return;
  }
  millisecs_t real_time = g_core->AppTimeMillisecs();
  bool wide = PeerSupportsWideAcks();
  int ack_size = AckSize_(wide);

  // 1 type, 2 reliable-num, 2 unreliable-num, acks.
  size_t single_header = 5 + static_cast<size_t>(ack_size);
  size_t single_max = MaxPacketSize_() - single_header;
  if (data.size() <= single_max) {
    uint16_t num = next_out_unreliable_message_num_++;
    {
      auto& mt = stats_message_types_[data[0]];
      mt.count++;
      mt.bytes += static_cast<int64_t>(data.size());
    }
    std::vector<uint8_t> data_out(data.size() + single_header);
    data_out[0] = static_cast<uint8_t>(BA_SCENEPACKET_MESSAGE_UNRELIABLE
                                       | (wide ? kPacketWideAcksFlag : 0));
    memcpy(data_out.data() + 1, &next_out_message_num_,
           sizeof(next_out_message_num_));
    memcpy(data_out.data() + 3, &num, sizeof(num));
    EmbedAcks_(real_time, &data_out, 5, wide);
    memcpy(data_out.data() + single_header, data.data(), data.size());
    SendGamePacket(data_out);
    return;
  }

  // Too big for one packet: split into parts the peer reassembles and
  // applies all-or-nothing, or fall back to reliable for peers that
  // don't know parts (and for absurd sizes).
  size_t part_header = single_header + 2;  // + part-index, part-count.
  size_t part_max = MaxPacketSize_() - part_header;
  size_t part_count = (data.size() + part_max - 1) / part_max;
  if (!PeerSupportsUnreliableParts()
      || part_count > static_cast<size_t>(kUnreliableMaxParts)) {
    SendReliableMessage(data);
    return;
  }
  uint16_t num = next_out_unreliable_message_num_++;
  {
    auto& mt = stats_message_types_[data[0]];
    mt.count++;
    mt.bytes += static_cast<int64_t>(data.size());
  }
  size_t offset = 0;
  for (size_t i = 0; i < part_count; ++i) {
    size_t n = std::min(part_max, data.size() - offset);
    std::vector<uint8_t> data_out(n + part_header);
    data_out[0] = static_cast<uint8_t>(BA_SCENEPACKET_MESSAGE_UNRELIABLE_PART
                                       | (wide ? kPacketWideAcksFlag : 0));
    memcpy(data_out.data() + 1, &next_out_message_num_,
           sizeof(next_out_message_num_));
    memcpy(data_out.data() + 3, &num, sizeof(num));
    EmbedAcks_(real_time, &data_out, 5, wide);
    data_out[5 + ack_size] = static_cast<uint8_t>(i);
    data_out[6 + ack_size] = static_cast<uint8_t>(part_count);
    memcpy(data_out.data() + part_header, data.data() + offset, n);
    offset += n;
    SendGamePacket(data_out);
  }
}

void Connection::SendJMessage(const std::string& val) {
  std::vector<uint8_t> msg(1u + val.size() + 1u);
  msg[0] = BA_MESSAGE_JMESSAGE;
  // +1 to include the terminating null char (the receiver relies on it).
  memcpy(msg.data() + 1u, val.c_str(), val.size() + 1u);
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

  PruneUnreliable_(real_time);

  if (can_communicate() && real_time - last_ack_send_time_ > kKeepaliveDelay) {
    // If we haven't sent anything with an ack out in a while, send along
    // a keepalive packet (a packet containing nothing but an ack).

    SendAck_(real_time);
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
        if (!multipart_buffer_.empty()
            && multipart_buffer_[0] == BA_MESSAGE_MULTIPART) {
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

  // Dev aid (BA_PACKET_LOSS=<percent>; test_game_run --packet-loss N):
  // drop that share of outgoing packets at random. Handshakes and
  // disconnects are exempt so sessions can still form and end.
  static int s_packet_loss_percent = -1;
  if (s_packet_loss_percent < 0) {
    s_packet_loss_percent = 0;
    if (const char* v = getenv("BA_PACKET_LOSS")) {
      s_packet_loss_percent = std::clamp(atoi(v), 0, 100);
    }
  }
  if (s_packet_loss_percent > 0 && data[0] != BA_SCENEPACKET_HANDSHAKE
      && data[0] != BA_SCENEPACKET_HANDSHAKE_RESPONSE
      && data[0] != BA_SCENEPACKET_DISCONNECT
      && RandomFloat() * 100.0f < static_cast<float>(s_packet_loss_percent)) {
    stats_packets_dropped_++;
    return;
  }

  packet_count_out_++;
  bytes_out_ += data.size();

  // Dev aid (BA_PACKET_DUMP; test_game_run --packet-dump): append every
  // raw outgoing packet to <config dir>/packet_dump_<n>.bin as
  // [u16 length][bytes], for offline compression experiments.
  if (!packet_dump_checked_) {
    packet_dump_checked_ = true;
    if (getenv("BA_PACKET_DUMP") != nullptr) {
      static int s_dump_index = 0;
      std::string path = g_core->GetConfigDirectory() + BA_DIRSLASH
                         + "packet_dump_" + std::to_string(s_dump_index++)
                         + ".bin";
      packet_dump_file_ = g_core->platform->FOpen(path.c_str(), "wb");
    }
  }
  if (packet_dump_file_) {
    auto len = static_cast<uint16_t>(data.size());
    fwrite(&len, 2, 1, packet_dump_file_);
    fwrite(data.data(), 1, data.size(), packet_dump_file_);
  }

  // Compress on the way out: zstd with the shared dictionary for peers
  // known to speak it, the legacy huffman otherwise (and for the
  // handshake itself, which runs before we know).
  std::vector<uint8_t> data_compressed =
      (g_scene_v1->zstd_packets && PeerSupportsZstdPackets())
          ? g_scene_v1->zstd_packets->compress(data)
          : g_scene_v1->huffman->compress(data);

#if kTestPacketDrops
  if (rand() % 100 < kTestPacketDropPercent) {  // NOLINT
    return;
  }
#endif

  bytes_out_compressed_ += data_compressed.size();
  stats_bytes_out_ += static_cast<int64_t>(data.size());
  stats_bytes_out_compressed_ += static_cast<int64_t>(data_compressed.size());
  stats_packets_out_++;
  {
    auto& pt = stats_packet_types_[data[0] & ~kPacketWideAcksFlag];
    pt.count++;
    pt.bytes += static_cast<int64_t>(data_compressed.size());
    millisecs_t now = g_core->AppTimeMillisecs();
    if (now == stats_last_packet_ms_) {
      stats_packets_same_ms_++;
    }
    stats_last_packet_ms_ = now;
  }
  SendGamePacketCompressed(data_compressed);
}

}  // namespace ballistica::scene_v1
