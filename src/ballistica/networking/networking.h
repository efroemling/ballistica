// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_NETWORKING_NETWORKING_H_
#define BALLISTICA_NETWORKING_NETWORKING_H_

#include <map>
#include <mutex>
#include <string>
#include <vector>

#include "ballistica/ballistica.h"

namespace ballistica {

// Packet types (first byte of raw udp packet).
// These packets can apply to our UDP connection layer, Remote App, etc.
// and don't exist for other connection mechanisms (GPGS, etc).
#define BA_PACKET_REMOTE_PING 0
#define BA_PACKET_REMOTE_PONG 1
#define BA_PACKET_REMOTE_ID_REQUEST 2
#define BA_PACKET_REMOTE_ID_RESPONSE 3
#define BA_PACKET_REMOTE_DISCONNECT 4
#define BA_PACKET_REMOTE_STATE 5
#define BA_PACKET_REMOTE_STATE_ACK 6
#define BA_PACKET_REMOTE_DISCONNECT_ACK 7
#define BA_PACKET_REMOTE_GAME_QUERY 8
#define BA_PACKET_REMOTE_GAME_RESPONSE 9
#define BA_PACKET_REMOTE_STATE2 10

// Very simple 1 byte packet/response used to test accessibility.
#define BA_PACKET_SIMPLE_PING 11
#define BA_PACKET_SIMPLE_PONG 12

// Fancier ping packet that can contain arbitrary data snippets.
// (so we can include stuff like current player counts, etc. in our response)
#define BA_PACKET_JSON_PING 13
#define BA_PACKET_JSON_PONG 14

// Used on android to wake our socket up so we can kill it.
#define BA_PACKET_POKE 21

// Local network game scanning.
#define BA_PACKET_GAME_QUERY 22
#define BA_PACKET_GAME_QUERY_RESPONSE 23
#define BA_PACKET_CLIENT_REQUEST 24
#define BA_PACKET_CLIENT_ACCEPT 25
#define BA_PACKET_CLIENT_DENY 26
#define BA_PACKET_CLIENT_DENY_VERSION_MISMATCH 27
#define BA_PACKET_CLIENT_DENY_ALREADY_IN_PARTY 28
#define BA_PACKET_CLIENT_DENY_PARTY_FULL 29
#define BA_PACKET_DISCONNECT_FROM_CLIENT_REQUEST 32
#define BA_PACKET_DISCONNECT_FROM_CLIENT_ACK 33
#define BA_PACKET_DISCONNECT_FROM_HOST_REQUEST 34
#define BA_PACKET_DISCONNECT_FROM_HOST_ACK 35
#define BA_PACKET_CLIENT_GAMEPACKET_COMPRESSED 36
#define BA_PACKET_HOST_GAMEPACKET_COMPRESSED 37

// Gamepackets are chunks of compressed data that apply specifically to a
// ballistica game connection. These packets can be provided over the UDP
// connection layer or by any other transport layer. When decompressed they have
// the following types as their first byte. NOTE - these originally shared a
// domain with BA_PACKET, but now they're independent... so need to avoid value
// clashes.. (hmm did i mean to say NO need?)
#define BA_GAMEPACKET_HANDSHAKE 15
#define BA_GAMEPACKET_HANDSHAKE_RESPONSE 16
#define BA_GAMEPACKET_MESSAGE 17
#define BA_GAMEPACKET_MESSAGE_UNRELIABLE 18
#define BA_GAMEPACKET_DISCONNECT 19
#define BA_GAMEPACKET_KEEPALIVE 20

// Messages is our high level layer that sits on top of gamepackets.
// They can be any size and will always arrive in the order they were sent
// (though ones marked unreliable may be dropped).
#define BA_MESSAGE_SESSION_RESET 0
#define BA_MESSAGE_SESSION_COMMANDS 1
#define BA_MESSAGE_SESSION_DYNAMICS_CORRECTION 2
#define BA_MESSAGE_NULL 3
#define BA_MESSAGE_REQUEST_REMOTE_PLAYER 4
#define BA_MESSAGE_ATTACH_REMOTE_PLAYER 5  // OBSOLETE (use the _2 version)
#define BA_MESSAGE_DETACH_REMOTE_PLAYER 6
#define BA_MESSAGE_REMOTE_PLAYER_INPUT_COMMANDS 7
#define BA_MESSAGE_REMOVE_REMOTE_PLAYER 8
#define BA_MESSAGE_PARTY_ROSTER 9
#define BA_MESSAGE_CHAT 10
#define BA_MESSAGE_PARTY_MEMBER_JOINED 11
#define BA_MESSAGE_PARTY_MEMBER_LEFT 12

// Hmmm; should multipart logic exist at the gamepacket layer instead?...
// A: that would require the re-send logic to be aware of multi-packet messages
// so maybe this is best.
#define BA_MESSAGE_MULTIPART 13
#define BA_MESSAGE_MULTIPART_END 14
#define BA_MESSAGE_CLIENT_PLAYER_PROFILES 15
#define BA_MESSAGE_ATTACH_REMOTE_PLAYER_2 16
#define BA_MESSAGE_HOST_INFO 17
#define BA_MESSAGE_CLIENT_INFO 18
#define BA_MESSAGE_KICK_VOTE 19

// General purpose json message type; its "t" entry is is an int corresponding
// to the BA_JMESSAGE types below.
#define BA_MESSAGE_JMESSAGE 20
#define BA_MESSAGE_CLIENT_PLAYER_PROFILES_JSON 21

#define BA_JMESSAGE_SCREEN_MESSAGE 0

// Enable huffman compression for all net packets?
#define BA_HUFFMAN_NET_COMPRESSION 1

// Enable training mode to build the huffman tree.
// This will spit a C array of ints to stdout based on net data.
// we currently hard code our tree.
#if !BA_HUFFMAN_NET_COMPRESSION
#define HUFFMAN_TRAINING_MODE 0
#endif

// Bits used by the logic thread for network communication.
class Networking {
 public:
  // Send a message to an address.  This may block for a brief moment, so it can
  // be more efficient to send a SendToMessage to the NetworkWrite thread which
  // will do this there.
  static void SendTo(const std::vector<uint8_t>& buffer, const SockAddr& addr);
  Networking();

  // Run a cycle of host scanning (basically sending out a broadcast packet to
  // see who's out there).
  void HostScanCycle();
  void EndHostScanning();

  // Called on mobile platforms when going into the background, etc
  // (when all networking should be shut down)
  void Pause();
  void Resume();
  struct ScanResultsEntry {
    std::string display_string;
    std::string address;
  };
  auto GetScanResults() -> std::vector<ScanResultsEntry>;

 private:
  void PruneScanResults();
  struct ScanResultsEntryPriv;

  // Note: would use an unordered_map here but gcc doesn't seem to allow
  // forward declarations of their template params.
  std::map<std::string, ScanResultsEntryPriv> scan_results_;
  std::mutex scan_results_mutex_;
  uint32_t next_scan_query_id_{};
  int scan_socket_{-1};
  bool running_{true};
};

}  // namespace ballistica

#endif  // BALLISTICA_NETWORKING_NETWORKING_H_
