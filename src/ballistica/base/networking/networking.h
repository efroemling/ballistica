// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_NETWORKING_NETWORKING_H_
#define BALLISTICA_BASE_NETWORKING_NETWORKING_H_

#include <vector>

#include "ballistica/shared/ballistica.h"

namespace ballistica::base {

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

// Local network scanning.
#define BA_PACKET_HOST_QUERY 22
#define BA_PACKET_HOST_QUERY_RESPONSE 23

// Connection/disconnection.
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

// Scene-packets in huffman-compressed form.
#define BA_PACKET_CLIENT_GAMEPACKET_COMPRESSED 36
#define BA_PACKET_HOST_GAMEPACKET_COMPRESSED 37

// Scene-packets are chunks of data that apply specifically to a
// ballistica scene connection. These packets can be provided over the UDP
// connection layer or by some other transport layer. When decompressed
// they have the types listed below as their first byte.
// NOTE: these originally shared a domain with BA_PACKET, but now they're
// independent, so no need to avoid value clashes if new types are added.
#define BA_SCENEPACKET_HANDSHAKE 15
#define BA_SCENEPACKET_HANDSHAKE_RESPONSE 16
#define BA_SCENEPACKET_MESSAGE 17
#define BA_SCENEPACKET_MESSAGE_UNRELIABLE 18
#define BA_SCENEPACKET_DISCONNECT 19
#define BA_SCENEPACKET_KEEPALIVE 20

// Messages is our high level layer that sits on top of scene-packets.
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
// Hmmm; should multipart logic exist at the scenepacket layer instead?...
// A: that would require message layer re-send logic to be aware of
// multi-packet messages so maybe this is simpler.
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

// Singleton based in the main thread for wrangling network stuff.
class Networking {
 public:
  // Called in the logic thread when the app is reading its config.
  void ApplyAppConfig();

  // Send a message to an address.  This may block for a brief moment, so it can
  // be more efficient to send a SendToMessage to the NetworkWrite thread which
  // will do this there.
  static void SendTo(const std::vector<uint8_t>& buffer, const SockAddr& addr);
  Networking();

  // Called on mobile platforms when going into the background, etc
  // (when all networking should be shut down)
  void OnAppSuspend();
  void OnAppUnsuspend();

  auto remote_server_accepting_connections() -> bool {
    return remote_server_accepting_connections_;
  }

 private:
  bool remote_server_accepting_connections_{true};
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_NETWORKING_NETWORKING_H_
