// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/support/client_session_replay.h"

#include <algorithm>
#include <cstdio>
#include <string>
#include <utility>
#include <vector>

#include "ballistica/base/assets/builtin_strings.h"
#include "ballistica/base/networking/networking.h"
#include "ballistica/classic/support/classic_app_mode.h"
#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging.h"
#include "ballistica/core/platform/platform.h"
#include "ballistica/scene_v1/connection/connection_set.h"
#include "ballistica/scene_v1/connection/connection_to_client.h"
#include "ballistica/scene_v1/support/huffman.h"
#include "ballistica/scene_v1/support/session_stream.h"
#include "ballistica/shared/math/vector3f.h"

namespace ballistica::scene_v1 {

static const millisecs_t kReplayStateDumpIntervalMillisecs = 500;

// Cap on header listing size, purely a corruption/hostile-file guard
// (real universes are a handful of packages).
static const uint32_t kReplayHeaderMaxPackages = 4096;
static const uint32_t kReplayHeaderMaxApveridLen = 1024;

// Read the header asset-package listing from an open file positioned
// just past the file-id + version fields. For pre-39 streams this reads
// nothing and yields an empty list. Returns false on a truncated/bogus
// listing (leaving the file position undefined).
static auto ReadAssetPackageListing_(FILE* file, uint16_t version,
                                     std::vector<std::string>* out) -> bool {
  out->clear();
  if (version < kProtocolVersionLangStrWire) {
    return true;
  }
  uint32_t count;
  if (fread(&count, sizeof(count), 1, file) != 1) {
    return false;
  }
  if (count > kReplayHeaderMaxPackages) {
    return false;
  }
  out->reserve(count);
  for (uint32_t i = 0; i < count; ++i) {
    uint32_t len;
    if (fread(&len, sizeof(len), 1, file) != 1
        || len > kReplayHeaderMaxApveridLen) {
      return false;
    }
    std::string apverid(len, '\0');
    if (len > 0 && fread(apverid.data(), len, 1, file) != 1) {
      return false;
    }
    out->push_back(std::move(apverid));
  }
  return true;
}

auto ReadReplayAssetPackages(const std::string& file_name)
    -> std::optional<std::vector<std::string>> {
  FILE* file = g_core->platform->FOpen(file_name.c_str(), "rb");
  if (!file) {
    return {};
  }
  uint32_t file_id;
  uint16_t version;
  std::vector<std::string> packages;
  bool ok =
      fread(&file_id, sizeof(file_id), 1, file) == 1 && file_id == kBrpFileID
      && fread(&version, sizeof(version), 1, file) == 1
      && version <= kProtocolVersionMax && version >= kProtocolVersionClientMin
      && ReadAssetPackageListing_(file, version, &packages);
  fclose(file);
  if (!ok) {
    return {};
  }
  return packages;
}

auto ClientSessionReplay::GetActualTimeAdvanceMillisecs(
    double base_advance_millisecs) -> double {
  if (is_fast_forwarding_) {
    if (base_time() < fast_forward_base_time_) {
      return std::min(
          base_advance_millisecs * 8,
          static_cast<double>(fast_forward_base_time_ - base_time()));
    }
    is_fast_forwarding_ = false;
  }
  auto* appmode = classic::ClassicAppMode::GetActiveOrFatal();
  if (appmode->is_replay_paused()) {
    // FIXME: seeking a replay results in black screen here
    return 0;
  }
  return base_advance_millisecs * pow(2.0f, appmode->replay_speed_exponent());
}

ClientSessionReplay::ClientSessionReplay(std::string filename)
    : file_name_(std::move(filename)) {
  auto* appmode = classic::ClassicAppMode::GetActiveOrThrow();

  // Kick any connected clients before we take over. Replay streams carry
  // exact-apverid package tables + indexed asset refs for the REPLAY's
  // universe, which connected clients never prepped (they arrive-ready
  // for the host's live app-run universe, not an arbitrary recording) --
  // so forwarding a replay to them would bounce them on the first
  // unresolvable indexed load. We disallow client broadcasting for
  // replays entirely (mirrors CleanUpBeforeConnectingToHost; the
  // interactive launch path warns first, and new joins are refused at
  // the packet level via ClassicAppMode::InReplay).
  appmode->connections()->ForceDisconnectClients();

  // take responsibility for feeding all clients to this device..
  appmode->connections()->RegisterClientController(this);

  // go ahead and just do a reset here, which will get things going..
  Reset(true);
}

ClientSessionReplay::~ClientSessionReplay() {
  auto* appmode = classic::ClassicAppMode::GetActiveOrThrow();

  // we no longer are responsible for feeding clients to this device..
  appmode->connections()->UnregisterClientController(this);
  appmode->ResumeReplay();
  if (file_) {
    fclose(file_);
    file_ = nullptr;
  }
}

void ClientSessionReplay::OnCommandBufferUnderrun() { ResetTargetBaseTime(); }

void ClientSessionReplay::OnClientConnected(ConnectionToClient* c) {
  // sanity check - abort if its on either of our lists already
  for (ConnectionToClient* i : connections_to_clients_) {
    if (i == c) {
      g_core->logging->Log(LogName::kBaNetworking, LogLevel::kError,
                           "ReplayClientSession::OnClientConnected()"
                           " got duplicate connection");
      return;
    }
  }
  for (ConnectionToClient* i : connections_to_clients_ignored_) {
    if (i == c) {
      g_core->logging->Log(LogName::kBaNetworking, LogLevel::kError,
                           "ReplayClientSession::OnClientConnected()"
                           " got duplicate connection");
      return;
    }
  }

  // We no longer broadcast replays to clients (see the ctor's
  // ForceDisconnectClients rationale): existing clients are kicked
  // before we take over and new joins are refused at the packet level
  // (ClassicAppMode::InReplay). Reaching here means a client slipped
  // through; refuse it defensively rather than feeding it a stream it
  // can't resolve.
  g_core->logging->Log(
      LogName::kBaNetworking, LogLevel::kWarning,
      "ReplayClientSession got a client connection; refusing (replay"
      " broadcasting is disabled).");
  c->RequestDisconnect();
}

void ClientSessionReplay::OnClientDisconnected(ConnectionToClient* c) {
  // Search for it on either our ignored or regular lists.
  for (auto i = connections_to_clients_.begin();
       i != connections_to_clients_.end(); i++) {
    if (*i == c) {
      connections_to_clients_.erase(i);
      return;
    }
  }
  for (auto i = connections_to_clients_ignored_.begin();
       i != connections_to_clients_ignored_.end(); i++) {
    if (*i == c) {
      connections_to_clients_ignored_.erase(i);
      return;
    }
  }
  g_core->logging->Log(LogName::kBaNetworking, LogLevel::kError,
                       "ReplayClientSession::OnClientDisconnected()"
                       " called for connection not on lists");
}

void ClientSessionReplay::FetchMessages() {
  if (!file_ || shutting_down()) {
    return;
  }

  // If we have no messages left, read from the file until we get some.
  while (commands().empty()) {
    // Before we read next message, let's save our current state
    // if we didn't that for too long.
    if (base_time() >= (states_.empty() ? 0 : states_.back().base_time_)
                           + kReplayStateDumpIntervalMillisecs) {
      SessionStream out(nullptr, false);
      DumpFullState(&out);

      current_state_.base_time_ = base_time();
      current_state_.correction_messages_.clear();
      GetCorrectionMessages(false, &current_state_.correction_messages_);

      fflush(file_);
      current_state_.file_position_ = ftell(file_);
      current_state_.message_ = out.GetOutMessage();
      states_.push_back(current_state_);
    }

    std::vector<uint8_t> buffer;
    uint8_t len8;
    uint32_t len32;

    // Read the size of the message.
    // the first byte represents the actual size if the value is < 254
    // if it is 254, the 2 bytes after it represent size
    // if it is 255, the 4 bytes after it represent size
    if (fread(&len8, 1, 1, file_) != 1) {
      // So they know to be done when they reach the end of the command list
      // (instead of just waiting for more commands)
      add_end_of_file_command();
      fclose(file_);
      file_ = nullptr;
      return;
    }
    if (len8 < 254) {
      len32 = len8;
    } else {
      // Pull 16 bit len.
      if (len8 == 254) {
        uint16_t len16;
        if (fread(&len16, 2, 1, file_) != 1) {
          // so they know to be done when they reach the end of the command
          // list (instead of just waiting for more commands)
          add_end_of_file_command();
          fclose(file_);
          file_ = nullptr;
          return;
        }
        assert(len16 >= 254);
        len32 = len16;
      } else {
        // Pull 32 bit len.
        if (fread(&len32, 4, 1, file_) != 1) {
          // so they know to be done when they reach the end of the command
          // list (instead of just waiting for more commands)
          add_end_of_file_command();
          fclose(file_);
          file_ = nullptr;
          return;
        }
        assert(len32 > 65535);
      }
    }

    // Read and decompress the actual message.
    BA_PRECONDITION(len32 > 0);
    buffer.resize(len32);
    if (fread(&(buffer[0]), len32, 1, file_) != 1) {
      add_end_of_file_command();
      fclose(file_);
      file_ = nullptr;
      return;
    }
    std::vector<uint8_t> data_decompressed =
        g_scene_v1->huffman->decompress(buffer);
    HandleSessionMessage(data_decompressed);

    // Also send it to all client-connections we're attached to.
    // NOTE: We currently are sending everything as reliable; we can maybe do
    // unreliable for certain type of messages. Though perhaps when passing
    // around replays maybe its best to keep everything intact.
    have_sent_client_message_ = true;
    for (auto&& i : connections_to_clients_) {
      i->SendReliableMessage(data_decompressed);
    }
  }
}

void ClientSessionReplay::Error(const std::string& description) {
  // Close the replay, announce something went wrong with it, and then do
  // standard error response..
  g_base->ScreenMessage(base::BuiltinStrings::Replay::ReadError()->Evaluate(),
                        {1, 0, 0});
  if (file_) {
    fclose(file_);
    file_ = nullptr;
  }
  ClientSession::Error(description);
}

void ClientSessionReplay::OnReset(bool rewind) {
  // Handles base resetting.
  ClientSession::OnReset(rewind);

  // Hack or not, but let's reset our fast-forward flag here, in case we were
  // asked to seek replay further than it's length.
  is_fast_forwarding_ = false;

  // If we've got any clients attached to us, tell them to reset as well.
  for (auto&& i : connections_to_clients_) {
    i->SendReliableMessage(std::vector<uint8_t>(1, BA_MESSAGE_SESSION_RESET));
  }

  // If rewinding, pop back to the start of our file.
  if (rewind) {
    if (file_) {
      fclose(file_);
      file_ = nullptr;
    }

    file_ = g_core->platform->FOpen(file_name_.c_str(), "rb");
    if (!file_) {
      Error("can't open file for reading");
      return;
    }

    // Read file ID and version to make sure we support this file.
    uint32_t file_id;
    if ((fread(&file_id, sizeof(file_id), 1, file_) != 1)) {
      Error("error reading file_id");
      return;
    }
    if (file_id != kBrpFileID) {
      Error("incorrect file_id");
      return;
    }

    // Make sure its a compatible protocol version.
    uint16_t version;
    if (fread(&version, sizeof(version), 1, file_) != 1) {
      Error("error reading version");
      return;
    }
    if (version > kProtocolVersionMax || version < kProtocolVersionClientMin) {
      g_base->ScreenMessage(
          base::BuiltinStrings::Replay::VersionError()->Evaluate(), {1, 0, 0});
      End();
      return;
    }
    set_stream_protocol(version);

    // Consume the header asset-package listing (protocol 39+) so the
    // message stream that follows is read from the correct offset. The
    // stream itself re-declares the table, so we don't need to retain
    // it here -- this is purely to advance past it.
    std::vector<std::string> header_packages;
    if (!ReadAssetPackageListing_(file_, version, &header_packages)) {
      Error("error reading replay asset-package listing");
      return;
    }
  }
}

void ClientSessionReplay::SeekTo(millisecs_t to_base_time) {
  is_fast_forwarding_ = false;
  if (to_base_time < base_time()) {
    auto it = std::lower_bound(
        states_.rbegin(), states_.rend(), to_base_time,
        [&](const IntermediateState& state, millisecs_t time) -> bool {
          return state.base_time_ > time;
        });
    if (it == states_.rend()) {
      Reset(true);
    } else {
      current_state_ = *it;
      RestoreFromCurrentState();
    }
  } else {
    auto it = std::lower_bound(
        states_.begin(), states_.end(), to_base_time,
        [&](const IntermediateState& state, millisecs_t time) -> bool {
          return state.base_time_ < time;
        });
    if (it == states_.end()) {
      if (!states_.empty()) {
        current_state_ = states_.back();
        RestoreFromCurrentState();
      }
      // Let's speed up replay a bit
      // (and we'll collect needed states along).
      is_fast_forwarding_ = true;
      fast_forward_base_time_ = to_base_time;
    } else {
      current_state_ = *it;
      RestoreFromCurrentState();
    }
  }
}

void ClientSessionReplay::RestoreFromCurrentState() {
  // FIXME: calling reset here causes background music to start over
  Reset(true);
  fseek(file_, current_state_.file_position_, SEEK_SET);

  SetBaseTime(current_state_.base_time_);
  HandleSessionMessage(current_state_.message_);
  for (const auto& msg : current_state_.correction_messages_) {
    HandleSessionMessage(msg);
  }
}

}  // namespace ballistica::scene_v1
