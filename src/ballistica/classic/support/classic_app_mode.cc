// Released under the MIT License. See LICENSE for details.

#include "ballistica/classic/support/classic_app_mode.h"

#include <algorithm>
#include <cstdio>
#include <string>
#include <vector>

#include "ballistica/base/audio/audio.h"
#include "ballistica/base/audio/audio_source.h"
#include "ballistica/base/graphics/graphics.h"
#include "ballistica/base/graphics/support/frame_def.h"
#include "ballistica/base/input/input.h"
#include "ballistica/base/logic/logic.h"
#include "ballistica/base/networking/network_writer.h"
#include "ballistica/base/networking/networking.h"
#include "ballistica/base/support/app_config.h"
#include "ballistica/base/support/plus_soft.h"
#include "ballistica/base/ui/ui.h"
#include "ballistica/classic/classic.h"
#include "ballistica/classic/python/classic_python.h"
#include "ballistica/core/logging/logging.h"
#include "ballistica/core/logging/logging_macros.h"
#include "ballistica/core/platform/core_platform.h"
#include "ballistica/scene_v1/connection/connection_set.h"
#include "ballistica/scene_v1/connection/connection_to_client.h"
#include "ballistica/scene_v1/connection/connection_to_host.h"
#include "ballistica/scene_v1/node/globals_node.h"
#include "ballistica/scene_v1/python/scene_v1_python.h"
#include "ballistica/scene_v1/support/client_input_device.h"
#include "ballistica/scene_v1/support/client_input_device_delegate.h"
#include "ballistica/scene_v1/support/client_session_net.h"
#include "ballistica/scene_v1/support/client_session_replay.h"
#include "ballistica/scene_v1/support/host_session.h"
#include "ballistica/scene_v1/support/scene.h"
#include "ballistica/shared/foundation/event_loop.h"
#include "ballistica/shared/foundation/macros.h"
#include "ballistica/shared/generic/json.h"
#include "ballistica/shared/generic/utils.h"
#include "ballistica/shared/networking/sockaddr.h"
#include "ballistica/ui_v1/ui_v1.h"
#include "ballistica/ui_v1/widget/root_widget.h"

namespace ballistica::classic {

const int kMaxChatMessages{40};

/// How long a kick vote lasts.
const int kKickVoteDuration{30000};

/// How long everyone has to wait to start a new kick vote after a failed one.
const int kKickVoteFailRetryDelay{60000};

/// Extra delay for the initiator of a failed vote.
const int kKickVoteFailRetryDelayInitiatorExtra{120000};

// Minimum clients that must be present for a kick vote to count. (for
// non-headless builds we require more votes since the host doesn't count
// but may be playing (in a 2on2 with 3 clients, don't want 2 clients able
// to kick).
const int kKickVoteMinimumClients{g_buildconfig.headless_build() ? 3 : 4};

struct ClassicAppMode::ScanResultsEntryPriv_ {
  scene_v1::PlayerSpec player_spec;
  std::string address;
  uint32_t last_query_id{};
  millisecs_t last_contact_time{};
};

base::InputDeviceDelegate* ClassicAppMode::CreateInputDeviceDelegate(
    base::InputDevice* device) {
  // We create a special delegate for our special ClientInputDevice types;
  // everything else gets our regular delegate.
  if (auto* client_device =
          dynamic_cast<scene_v1::ClientInputDevice*>(device)) {
    auto* obj = Object::NewDeferred<scene_v1::ClientInputDeviceDelegate>();
    obj->StoreClientDeviceInfo(client_device);
    return obj;
  }
  return Object::NewDeferred<scene_v1::SceneV1InputDeviceDelegate>();
}

// Go with 5 minute ban.
const int kKickBanSeconds{5 * 60};

bool ClassicAppMode::IsInMainMenu() const {
  scene_v1::HostSession* hostsession =
      scene_v1::ContextRefSceneV1::FromAppForegroundContext().GetHostSession();
  return (hostsession && hostsession->is_main_menu());
}

static ClassicAppMode* g_scene_v1_app_mode{};

void ClassicAppMode::OnActivate() {
  assert(g_base->InLogicThread());

  // Make sure we pull this only once when we are first active.
  if (host_protocol_version_ == -1) {
    host_protocol_version_ = std::clamp(
        g_base->app_config->Resolve(
            base::AppConfig::IntID::kSceneV1HostProtocol),
        scene_v1::kProtocolVersionHostMin, scene_v1::kProtocolVersionMax);
  }

  Reset_();

  // Explicitly fire some of our 'On-Foo-Changed' callbacks to set initial
  // states.
  ApplyAppConfig();
  LanguageChanged();
  OnGameRosterChanged_();
}

void ClassicAppMode::OnAppStart() { assert(g_base->InLogicThread()); }

void ClassicAppMode::OnAppShutdown() {
  assert(g_base->InLogicThread());
  connections_->Shutdown();
}

void ClassicAppMode::OnAppSuspend() {
  assert(g_base->InLogicThread());

  // App is going into background or whatnot. Kill any sockets/etc.
  EndHostScanning();
}

void ClassicAppMode::OnAppUnsuspend() { assert(g_base->InLogicThread()); }

void ClassicAppMode::RequestMainUI() {
  g_classic->python->objs()
      .Get(ClassicPython::ObjID::kRequestMainUICall)
      .Call();
}

// Reset everything to a blank slate.
void ClassicAppMode::Reset_() {
  assert(g_base);
  assert(g_base->InLogicThread());

  // Let our Python delegate know we're gonna do a reset so it can save any
  // state it needs to or whatnot.
  // HMM; should we make resets an official part of AppModes or something?
  PythonRef result = g_classic->python->objs()
                         .Get(ClassicPython::ObjID::kOnEngineWillResetCall)
                         .Call();
  if (!result.exists()) {
    throw Exception("Error calling kOnEngineWillResetCall.");
  }

  // Tear down any existing session.
  foreground_session_.Clear();
  PruneSessions_();

  // If all is well our sessions should all be dead at this point.
  if (g_scene_v1->session_count != 0) {
    g_core->logging->Log(LogName::kBa, LogLevel::kError,
                         "SceneV1 session count is non-zero ("
                             + std::to_string(g_scene_v1->session_count)
                             + ") on ClassicAppMode::Reset_().");
  }

  // Reset the engine itself to a default state.
  g_base->Reset();

  // Import UIV1 and wire it up for UI duty.
  if (!g_core->HeadlessMode()) {
    uiv1_ = ui_v1::UIV1FeatureSet::Import();
    g_base->ui->SetUIDelegate(uiv1_);

    // At this point uiv1 is in a reset-to-default state. Now plug in our
    // current values for everything.
    if (auto* root_widget = uiv1_->root_widget()) {
      root_widget->SetTicketsMeterValue(root_ui_tickets_meter_value_);
      root_widget->SetTokensMeterValue(root_ui_tokens_meter_value_,
                                       root_ui_gold_pass_);
      root_widget->SetLeagueRankValues(
          root_ui_league_type_, root_ui_league_number_, root_ui_league_rank_);
      root_widget->SetAchievementPercentText(root_ui_achievement_percent_text_);
      root_widget->SetLevelText(root_ui_level_text_);
      root_widget->SetXPText(root_ui_xp_text_);
      root_widget->SetInboxState(root_ui_inbox_count_,
                                 root_ui_inbox_count_is_max_,
                                 root_ui_inbox_announce_text_);
      root_widget->set_highlight_potential_token_purchases(
          root_ui_highlight_potential_token_purchases_);

      root_widget->SetChests(
          root_ui_chest_0_appearance_, root_ui_chest_1_appearance_,
          root_ui_chest_2_appearance_, root_ui_chest_3_appearance_,
          root_ui_chest_0_create_time_, root_ui_chest_1_create_time_,
          root_ui_chest_2_create_time_, root_ui_chest_3_create_time_,
          root_ui_chest_0_unlock_time_, root_ui_chest_1_unlock_time_,
          root_ui_chest_2_unlock_time_, root_ui_chest_3_unlock_time_,
          root_ui_chest_0_unlock_tokens_, root_ui_chest_1_unlock_tokens_,
          root_ui_chest_2_unlock_tokens_, root_ui_chest_3_unlock_tokens_,
          root_ui_chest_0_ad_allow_time_, root_ui_chest_1_ad_allow_time_,
          root_ui_chest_2_ad_allow_time_, root_ui_chest_3_ad_allow_time_);
      root_widget->SetHaveLiveValues(root_ui_have_live_values_);
    }
  }

  // Fade in if we currently aren't.
  g_base->graphics->FadeScreen(true, 250, nullptr);

  // Let our Python delegate know we're done doing our reset.
  result = g_classic->python->objs()
               .Get(ClassicPython::ObjID::kOnEngineDidResetCall)
               .Call();
  if (!result.exists()) {
    throw Exception("Error calling kOnEngineDidResetCall.");
  }
}

// Note: for now we're making our host-scan network calls directly from the
// logic thread. This is generally not a good idea since it appears that even
// in non-blocking mode they're still blocking for 3-4ms sometimes. But for
// now since this is only used minimally and only while in the UI I guess it's
// ok.
void ClassicAppMode::HostScanCycle() {
  assert(g_base->InLogicThread());

  // We need to create a scanner socket - an ipv4 socket we can send out
  // broadcast messages from.
  if (scan_socket_ == -1) {
    scan_socket_ = socket(AF_INET, SOCK_DGRAM, 0);

    if (scan_socket_ == -1) {
      g_core->logging->Log(LogName::kBaNetworking, LogLevel::kError,
                           "Error opening scan socket: "
                               + g_core->platform->GetSocketErrorString()
                               + ".");
      return;
    }

    // Since this guy lives in the logic-thread we need it to not block.
    if (!g_core->platform->SetSocketNonBlocking(scan_socket_)) {
      g_core->logging->Log(LogName::kBaNetworking, LogLevel::kError,
                           "Error setting socket non-blocking.");
      g_core->platform->CloseSocket(scan_socket_);
      scan_socket_ = -1;
      return;
    }

    // Bind to whatever.
    struct sockaddr_in serv_addr{};
    memset(&serv_addr, 0, sizeof(serv_addr));
    serv_addr.sin_family = AF_INET;
    serv_addr.sin_addr.s_addr = htonl(INADDR_ANY);  // NOLINT
    serv_addr.sin_port = 0;                         // any
    int result =
        ::bind(scan_socket_, (struct sockaddr*)&serv_addr, sizeof(serv_addr));
    if (result == 1) {
      g_core->logging->Log(
          LogName::kBaNetworking, LogLevel::kError,
          "Error binding socket: " + g_core->platform->GetSocketErrorString()
              + ".");
      g_core->platform->CloseSocket(scan_socket_);
      scan_socket_ = -1;
      return;
    }

    // Enable broadcast on the socket.
    BA_SOCKET_SETSOCKOPT_VAL_TYPE op_val{1};
    result = setsockopt(scan_socket_, SOL_SOCKET, SO_BROADCAST, &op_val,
                        sizeof(op_val));

    if (result != 0) {
      g_core->logging->Log(LogName::kBaNetworking, LogLevel::kError,
                           "Error enabling broadcast for scan-socket: "
                               + g_core->platform->GetSocketErrorString()
                               + ".");
      g_core->platform->CloseSocket(scan_socket_);
      scan_socket_ = -1;
      return;
    }
  }

  // Ok we've got a valid scanner socket. Now lets send out broadcast pings on
  // all available networks.
  std::vector<uint32_t> addrs = g_core->platform->GetBroadcastAddrs();
  for (auto&& i : addrs) {
    sockaddr_in addr{};
    addr.sin_family = AF_INET;
    addr.sin_port = htons(kDefaultPort);  // NOLINT
    addr.sin_addr.s_addr = htonl(i);      // NOLINT

    // Include our query id (so we can sort out which responses come back
    // quickest).
    uint8_t data[5];
    data[0] = BA_PACKET_HOST_QUERY;
    memcpy(data + 1, &next_scan_query_id_, 4);
    BA_DEBUG_TIME_CHECK_BEGIN(sendto);
    ssize_t result = sendto(
        scan_socket_, reinterpret_cast<socket_send_data_t*>(data), sizeof(data),
        0, reinterpret_cast<sockaddr*>(&addr), sizeof(addr));
    BA_DEBUG_TIME_CHECK_END(sendto, 10);
    if (result == -1) {
      int err = g_core->platform->GetSocketError();
      switch (err) {  // NOLINT(hicpp-multiway-paths-covered)
        case ENETUNREACH:
          break;
        default:
          g_core->logging->Log(LogName::kBaNetworking, LogLevel::kError,
                               "Error on scan-socket sendto: "
                                   + g_core->platform->GetSocketErrorString());
      }
    }
  }
  next_scan_query_id_++;

  // ..and see if any responses came in from previous sends.
  char buffer[256];
  sockaddr_storage from{};
  socklen_t from_size = sizeof(from);
  while (true) {
    BA_DEBUG_TIME_CHECK_BEGIN(recvfrom);
    ssize_t result = recvfrom(scan_socket_, buffer, sizeof(buffer), 0,
                              reinterpret_cast<sockaddr*>(&from), &from_size);
    BA_DEBUG_TIME_CHECK_END(recvfrom, 10);

    if (result == -1) {
      int err = g_core->platform->GetSocketError();
      switch (err) {  // NOLINT(hicpp-multiway-paths-covered)
        case EWOULDBLOCK:
          break;
        default:
          g_core->logging->Log(LogName::kBaNetworking, LogLevel::kError,
                               "Error: recvfrom error: "
                                   + g_core->platform->GetSocketErrorString());
          break;
      }
      break;
    }

    if (result > 2 && buffer[0] == BA_PACKET_HOST_QUERY_RESPONSE) {
      // Size should be between 13 and 366 (1 byte type, 4 byte query_id, 4
      // byte protocol_id, 1 byte id_len, 1 byte player_spec_len, 1-100 byte
      // id, 1-255 byte player-spec).
      if (result >= 14 && result <= 366) {
        uint32_t protocol_version;
        uint32_t query_id;

        memcpy(&query_id, buffer + 1, 4);
        memcpy(&protocol_version, buffer + 5, 4);
        auto id_len = static_cast<uint32_t>(buffer[9]);
        auto player_spec_len = static_cast<uint32_t>(buffer[10]);

        if (id_len > 0 && id_len <= 100 && player_spec_len > 0
            && player_spec_len <= 255
            && (11 + id_len + player_spec_len == result)) {
          char id[101];
          char player_spec_str[256];
          memcpy(id, buffer + 11, id_len);
          memcpy(player_spec_str, buffer + 11 + id_len, player_spec_len);

          id[id_len] = 0;
          player_spec_str[player_spec_len] = 0;

          // Add or modify an entry for this.
          {
            std::scoped_lock lock(scan_results_mutex_);

            // Ignore if it looks like its us.
            if (id != g_base->GetAppInstanceUUID()) {
              std::string key = id;
              auto i = scan_results_.find(key);

              // Make a new entry if its not there.
              bool do_update_entry = (i == scan_results_.end()
                                      || i->second.last_query_id != query_id);
              if (do_update_entry) {
                ScanResultsEntryPriv_& entry(scan_results_[key]);
                entry.player_spec = scene_v1::PlayerSpec(player_spec_str);
                char buffer2[256];
                entry.address = inet_ntop(
                    AF_INET,
                    &((reinterpret_cast<sockaddr_in*>(&from))->sin_addr),
                    buffer2, sizeof(buffer2));
                entry.last_query_id = query_id;
                entry.last_contact_time = g_core->AppTimeMillisecs();
              }
            }
            PruneScanResults_();
          }
        } else {
          g_core->logging->Log(
              LogName::kBaNetworking, LogLevel::kError,
              "Got invalid BA_PACKET_HOST_QUERY_RESPONSE packet");
        }
      } else {
        g_core->logging->Log(
            LogName::kBaNetworking, LogLevel::kError,
            "Got invalid BA_PACKET_HOST_QUERY_RESPONSE packet");
      }
    }
  }
}

void ClassicAppMode::EndHostScanning() {
  if (scan_socket_ != -1) {
    g_core->platform->CloseSocket(scan_socket_);
    scan_socket_ = -1;
  }
}

void ClassicAppMode::PruneScanResults_() {
  millisecs_t t = g_core->AppTimeMillisecs();
  auto i = scan_results_.begin();
  while (i != scan_results_.end()) {
    auto i_next = i;
    i_next++;
    if (t - i->second.last_contact_time > 3000) {
      scan_results_.erase(i);
    }
    i = i_next;
  }
}

auto ClassicAppMode::GetScanResults()
    -> std::vector<ClassicAppMode::ScanResultsEntry> {
  std::vector<ScanResultsEntry> results;
  results.resize(scan_results_.size());
  {
    std::scoped_lock lock(scan_results_mutex_);
    int out_num = 0;
    for (auto&& i : scan_results_) {
      ScanResultsEntryPriv_& in(i.second);
      ScanResultsEntry& out(results[out_num]);
      out.display_string = in.player_spec.GetDisplayString();
      out.address = in.address;
      out_num++;
    }
    PruneScanResults_();
  }
  return results;
}

auto ClassicAppMode::GetActive() -> ClassicAppMode* {
  // Note: this gets called by non-logic threads, and not
  // doing any locking here so bg thread callers should
  // keep in mind that app-mode may change under them.

  // Otherwise return our singleton only if it is current.
  if (g_base->app_mode() == g_scene_v1_app_mode) {
    return g_scene_v1_app_mode;
  }
  return nullptr;
}

bool ClassicAppMode::HasConnectionToHost() const {
  return connections()->has_connection_to_host();
}

millisecs_t ClassicAppMode::LastClientJoinTime() const {
  return last_connection_to_client_join_time();
}

bool ClassicAppMode::HasConnectionToClients() const {
  return connections()->HasConnectionToClients();
}

auto ClassicAppMode::GetActiveOrWarn() -> ClassicAppMode* {
  auto* val{GetActive()};
  if (val == nullptr) {
    g_core->logging->Log(
        LogName::kBa, LogLevel::kWarning,
        "Attempting to access ClassicAppMode while it is inactive.");
  }
  return val;
}

auto ClassicAppMode::GetActiveOrThrow() -> ClassicAppMode* {
  auto* val{GetActive()};
  if (val == nullptr) {
    throw Exception(
        "Attempting to access ClassicAppMode while it is inactive.");
  }
  return val;
}

auto ClassicAppMode::GetActiveOrFatal() -> ClassicAppMode* {
  auto* val{GetActive()};
  if (val == nullptr) {
    FatalError("Attempting to access ClassicAppMode while it is inactive.");
  }
  return val;
}

auto ClassicAppMode::GetSingleton() -> ClassicAppMode* {
  assert(g_base->InLogicThread());

  if (g_scene_v1_app_mode == nullptr) {
    g_scene_v1_app_mode = new ClassicAppMode();
  }
  return g_scene_v1_app_mode;
}

ClassicAppMode::ClassicAppMode()
    : game_roster_(cJSON_CreateArray()),
      connections_(std::make_unique<scene_v1::ConnectionSet>()) {}

void ClassicAppMode::HandleIncomingUDPPacket(const std::vector<uint8_t>& data,
                                             const SockAddr& addr) {
  // Just forward it along to our connection-set to handle.
  connections()->HandleIncomingUDPPacket(data, addr);
}

auto ClassicAppMode::HandleJSONPing(const std::string& data_str)
    -> std::string {
  // Note to self - this is called in a non-logic thread.
  cJSON* data = cJSON_Parse(data_str.c_str());
  if (data == nullptr) {
    return "";
  }
  cJSON_Delete(data);

  // Ok lets include some basic info that might be pertinent to someone
  // pinging us. Currently that includes our current/max connection count.
  char buffer[256];
  snprintf(buffer, sizeof(buffer), R"({"b":%d,"ps":%d,"psmx":%d})",
           kEngineBuildNumber, public_party_size(), public_party_max_size());
  return buffer;
}

void ClassicAppMode::SetGameRoster(cJSON* r) {
  assert(g_base->InLogicThread());
  if (game_roster_ != nullptr) {
    cJSON_Delete(game_roster_);
  }
  game_roster_ = r;
  OnGameRosterChanged_();
}

void ClassicAppMode::OnGameRosterChanged_() {
  assert(g_base->InLogicThread());
  g_base->ui->SetSquadSizeLabel(GetPartySize());
}

auto ClassicAppMode::GetPartySize() const -> int {
  assert(g_base->InLogicThread());
  assert(game_roster_ != nullptr);
  return cJSON_GetArraySize(game_roster_);
}

auto ClassicAppMode::GetHeadlessNextDisplayTimeStep() -> microsecs_t {
  std::optional<microsecs_t> min_time_to_next;
  for (auto&& i : sessions_) {
    if (!i.exists()) {
      continue;
    }
    auto this_time_to_next = i->TimeToNextEvent();
    if (this_time_to_next.has_value()) {
      if (!min_time_to_next.has_value()) {
        min_time_to_next = *this_time_to_next;
      } else {
        min_time_to_next = std::min(*min_time_to_next, *this_time_to_next);
      }
    }
  }
  return min_time_to_next.has_value() ? *min_time_to_next
                                      : base::kHeadlessMaxDisplayTimeStep;
}

void ClassicAppMode::StepDisplayTime() {
  assert(g_base->InLogicThread());

  auto startms{core::CorePlatform::TimeMonotonicMillisecs()};
  millisecs_t app_time = g_core->AppTimeMillisecs();
  g_core->platform->SetDebugKey("LastUpdateTime", std::to_string(startms));
  in_update_ = true;

  // NOTE: We now simply drive our old milliseconds time using display-time.
  legacy_display_time_millisecs_ =
      static_cast<millisecs_t>(g_base->logic->display_time() * 1000.0);

  // Calc our integer increment using our previous millisecs conversion.
  // (don't want to simply round g_logic->display_time_increment() each time
  // since that would accumulate precision loss; ie: 16.6 would round up to 17
  // each time).
  millisecs_t legacy_display_time_millisecs_inc;
  if (legacy_display_time_millisecs_prev_ < 0) {
    // Convert directly *only* the first time when we don't have prev
    // available.
    legacy_display_time_millisecs_inc = static_cast<millisecs_t>(
        g_base->logic->display_time_increment() * 1000.0);

  } else {
    legacy_display_time_millisecs_inc =
        legacy_display_time_millisecs_ - legacy_display_time_millisecs_prev_;
  }
  legacy_display_time_millisecs_prev_ = legacy_display_time_millisecs_;

  // Special case: due to things like app-mode-switches our
  // prev-display-time-millisecs may be way far in the past which can give
  // us huge step values. So if this value is much bigger than the direct
  // conversion of display_time_increment, clamp it.
  auto milliseconds_inc_max =
      static_cast<int>(g_base->logic->display_time_increment() * 1000.0 * 1.5);
  if (legacy_display_time_millisecs_inc > milliseconds_inc_max) {
    legacy_display_time_millisecs_inc = milliseconds_inc_max;
  }

  UpdateKickVote_();

  HandleQuitOnIdle_();

  // Send the game roster to our clients if it's changed recently.
  if (game_roster_dirty_) {
    if (app_time > last_game_roster_send_time_ + 2500) {
      // Now send it to all connected clients.
      std::vector<uint8_t> msg = GetGameRosterMessage_();
      for (auto&& c : connections()->GetConnectionsToClients()) {
        c->SendReliableMessage(msg);
      }
      game_roster_dirty_ = false;
      last_game_roster_send_time_ = app_time;
    }
  }

  connections_->Update();

  // Update all of our sessions.
  for (auto&& i : sessions_) {
    if (!i.exists()) {
      continue;
    }
    // Pass our old int milliseconds time vals for legacy purposes
    // along with the newer exact ones for anyone who wants to use them.
    // (ideally at some point we can pass neither of these and anyone who
    // needs this can just use g_logic->display_time() directly).
    i->Update(static_cast<int>(legacy_display_time_millisecs_inc),
              g_base->logic->display_time_increment());
  }

  // Go ahead and prune dead ones.
  PruneSessions_();

  in_update_ = false;

  // Report excessively long updates.
  if (g_core->core_config().debug_timing
      && app_time >= next_long_update_report_time_) {
    auto duration{core::CorePlatform::TimeMonotonicMillisecs() - startms};

    // Complain when our full update takes longer than 1/60th second.
    if (duration > (1000 / 60)) {
      g_core->logging->Log(LogName::kBa, LogLevel::kInfo,
                           "Logic::StepDisplayTime update took too long ("
                               + std::to_string(duration) + " ms).");

      // Limit these if we want (not doing so for now).
      next_long_update_report_time_ = app_time;
    }
  }
}

auto ClassicAppMode::GetGameRosterMessage_() -> std::vector<uint8_t> {
  // This message is simply a flattened json string of our roster (including
  // terminating char).
  char* s = cJSON_PrintUnformatted(game_roster_);
  auto s_len = strlen(s);
  std::vector<uint8_t> msg(1 + s_len + 1);
  msg[0] = BA_MESSAGE_PARTY_ROSTER;
  memcpy(&(msg[1]), s, s_len + 1);
  free(s);

  return msg;
}

base::ContextRef ClassicAppMode::GetForegroundContext() {
  scene_v1::Session* s = GetForegroundSession();
  if (s) {
    return s->GetForegroundContext();
  } else {
    return {};
  }
}

void ClassicAppMode::UpdateGameRoster() {
  assert(g_base->InLogicThread());

  assert(game_roster_ != nullptr);
  if (game_roster_ != nullptr) {
    cJSON_Delete(game_roster_);
  }

  // Our party-roster is just a json array of dicts containing player-specs.
  game_roster_ = cJSON_CreateArray();

  int total_party_size = 1;  // include ourself here..

  // Add ourself first (that's currently how they know we're the party leader)
  // ..but only if we have a connected client (otherwise our party is
  // considered 'empty').

  bool include_self = (connections()->GetConnectedClientCount() > 0);

  if (auto* hs = dynamic_cast<scene_v1::HostSession*>(GetForegroundSession())) {
    // Add our host-y self.
    if (include_self) {
      cJSON* client_dict = cJSON_CreateObject();
      cJSON_AddItemToObject(
          client_dict, "spec",
          cJSON_CreateString(scene_v1::PlayerSpec::GetAccountPlayerSpec()
                                 .GetSpecString()
                                 .c_str()));

      // Add our list of local players.
      cJSON* player_array = cJSON_CreateArray();
      for (auto&& p : hs->players()) {
        auto* delegate = p->input_device_delegate();
        if (delegate == nullptr || !delegate->InputDeviceExists()) {
          BA_LOG_ONCE(LogName::kBa, LogLevel::kWarning,
                      "Found player with no/invalid input-device-delegate in "
                      "UpdateGameRoster.");
          continue;
        }

        // Add some basic info for each local player (only ones with real
        // names though; don't wanna send <selecting character>, etc).
        if (p->accepted() && p->name_is_real() && !delegate->IsRemoteClient()) {
          cJSON* player_dict = cJSON_CreateObject();
          cJSON_AddItemToObject(player_dict, "n",
                                cJSON_CreateString(p->GetName().c_str()));
          cJSON_AddItemToObject(player_dict, "nf",
                                cJSON_CreateString(p->GetName(true).c_str()));
          cJSON_AddItemToObject(player_dict, "i", cJSON_CreateNumber(p->id()));
          cJSON_AddItemToArray(player_array, player_dict);
        }
      }
      cJSON_AddItemToObject(client_dict, "p", player_array);
      cJSON_AddItemToObject(
          client_dict, "i",
          cJSON_CreateNumber(-1));  // -1 client_id means we're the host.
      cJSON_AddItemToArray(game_roster_, client_dict);
    }

    // Add all connected clients.
    for (auto&& i : connections()->connections_to_clients()) {
      if (i.second->can_communicate()) {
        cJSON* client_dict = cJSON_CreateObject();
        cJSON_AddItemToObject(
            client_dict, "spec",
            cJSON_CreateString(i.second->peer_spec().GetSpecString().c_str()));

        // Add their list of players.
        cJSON* player_array = cJSON_CreateArray();

        // Include all players that are remote and coming from this same
        // client connection.
        for (auto&& p : hs->players()) {
          auto* delegate = p->input_device_delegate();
          if (delegate == nullptr || !delegate->InputDeviceExists()) {
            // Logged this above; would be redundant here.
            continue;
          }

          if (p->accepted() && p->name_is_real()
              && delegate->IsRemoteClient()) {
            auto* client_delegate =
                static_cast<scene_v1::ClientInputDeviceDelegate*>(delegate);
            assert(dynamic_cast<scene_v1::ClientInputDeviceDelegate*>(delegate)
                   == client_delegate);
            scene_v1::ConnectionToClient* ctc =
                client_delegate->connection_to_client();

            // Add some basic info for each remote player.
            if (ctc != nullptr && ctc == i.second.get()) {
              cJSON* player_dict = cJSON_CreateObject();
              cJSON_AddItemToObject(player_dict, "n",
                                    cJSON_CreateString(p->GetName().c_str()));
              cJSON_AddItemToObject(
                  player_dict, "nf",
                  cJSON_CreateString(p->GetName(true).c_str()));
              cJSON_AddItemToObject(player_dict, "i",
                                    cJSON_CreateNumber(p->id()));
              cJSON_AddItemToArray(player_array, player_dict);
            }
          }
        }
        cJSON_AddItemToObject(client_dict, "p", player_array);
        cJSON_AddItemToObject(client_dict, "i",
                              cJSON_CreateNumber(i.second->id()));
        cJSON_AddItemToArray(game_roster_, client_dict);
        total_party_size += 1;
      }
    }
  }

  OnGameRosterChanged_();

  // Keep the Python layer informed on our number of connections; it may want
  // to pass the info along to the master server if we're hosting a public
  // party.
  SetPublicPartySize(total_party_size);

  // Mark the roster as dirty so we know we need to send it to everyone soon.
  game_roster_dirty_ = true;
}

void ClassicAppMode::UpdateKickVote_() {
  if (!kick_vote_in_progress_) {
    return;
  }
  scene_v1::ConnectionToClient* kick_vote_starter = kick_vote_starter_.get();
  scene_v1::ConnectionToClient* kick_vote_target = kick_vote_target_.get();

  // If the target is no longer with us, silently end.
  if (kick_vote_target == nullptr) {
    kick_vote_in_progress_ = false;
    return;
  }
  millisecs_t current_time{g_core->AppTimeMillisecs()};
  int total_client_count = 0;
  int yes_votes = 0;
  int no_votes = 0;

  // Tally current votes for connected clients; if anything has changed, print
  // the update and possibly perform the kick.
  for (scene_v1::ConnectionToClient* client :
       connections()->GetConnectionsToClients()) {
    ++total_client_count;
    if (client->kick_voted()) {
      if (client->kick_vote_choice()) {
        ++yes_votes;
      } else {
        ++no_votes;
      }
    }
  }
  bool vote_failed = false;

  // If we've fallen below the minimum necessary voters or time has run out,
  // fail.
  if (total_client_count < kKickVoteMinimumClients) {
    vote_failed = true;
  }
  if (current_time > kick_vote_end_time_) {
    vote_failed = true;
  }

  if (vote_failed) {
    connections()->SendScreenMessageToClients(R"({"r":"kickVoteFailedText"})",
                                              1, 1, 0);
    kick_vote_in_progress_ = false;

    // Disallow kicking for a while for everyone.. but ESPECIALLY so for the
    // guy who launched the failed vote.
    for (scene_v1::ConnectionToClient* client :
         connections()->GetConnectionsToClients()) {
      millisecs_t delay = kKickVoteFailRetryDelay;
      if (client == kick_vote_starter) {
        delay += kKickVoteFailRetryDelayInitiatorExtra;
      }
      client->set_next_kick_vote_allow_time(
          std::max(client->next_kick_vote_allow_time(), current_time + delay));
    }
  } else {
    int votes_required;
    switch (total_client_count) {
      case 1:
      case 2:
        votes_required = 2;  // Shouldn't actually be possible.
        break;
      case 3:
        votes_required = g_core->HeadlessMode() ? 2 : 3;
        break;
      case 4:
        votes_required = 3;
        break;
      case 5:
        votes_required = g_core->HeadlessMode() ? 3 : 4;
        break;
      case 6:
        votes_required = 4;
        break;
      case 7:
        votes_required = g_core->HeadlessMode() ? 4 : 5;
        break;
      default:
        votes_required = total_client_count - 3;
        break;
    }
    int votes_needed = votes_required - yes_votes;
    if (votes_needed <= 0) {
      // ZOMG the vote passed; perform the kick.
      connections()->SendScreenMessageToClients(
          R"({"r":"kickOccurredText","s":[["${NAME}",)"
              + Utils::GetJSONString(kick_vote_target->GetCombinedSpec()
                                         .GetDisplayString()
                                         .c_str())
              + "]]}",
          1, 1, 0);
      kick_vote_in_progress_ = false;
      connections()->DisconnectClient(kick_vote_target->id(), kKickBanSeconds);

    } else if (votes_needed != last_kick_votes_needed_) {
      last_kick_votes_needed_ = votes_needed;
      connections()->SendScreenMessageToClients(
          R"({"r":"votesNeededText","s":[["${NUMBER}",")"
              + std::to_string(votes_needed) + "\"]]}",
          1, 1, 0);
    }
  }
}

void ClassicAppMode::StartKickVote(scene_v1::ConnectionToClient* starter,
                                   scene_v1::ConnectionToClient* target) {
  // Restrict votes per client.
  millisecs_t current_time = g_core->AppTimeMillisecs();

  if (starter == target) {
    // Don't let anyone kick themselves.
    starter->SendScreenMessage(R"({"r":"kickVoteCantKickSelfText",)"
                               R"("f":"kickVoteFailedText"})",
                               1, 0, 0);
  } else if (target->IsAdmin()) {
    // Admins are immune to kicking
    starter->SendScreenMessage(R"({"r":"kickVoteCantKickAdminText",)"
                               R"("f":"kickVoteFailedText"})",
                               1, 0, 0);
  } else if (starter->IsAdmin()) {
    // Admin doing the kicking succeeds instantly.
    connections()->SendScreenMessageToClients(
        R"({"r":"kickOccurredText","s":[["${NAME}",)"
            + Utils::GetJSONString(
                target->GetCombinedSpec().GetDisplayString().c_str())
            + "]]}",
        1, 1, 0);
    connections()->DisconnectClient(target->id(), kKickBanSeconds);
    starter->SendScreenMessage(R"({"r":"kickVoteCantKickAdminText",)"
                               R"("f":"kickVoteFailedText"})",
                               1, 0, 0);
  } else if (!kick_voting_enabled_) {
    // No kicking otherwise if its disabled.
    starter->SendScreenMessage(R"({"r":"kickVotingDisabledText",)"
                               R"("f":"kickVoteFailedText"})",
                               1, 0, 0);
  } else if (kick_vote_in_progress_) {
    // Vote in progress error.
    starter->SendScreenMessage(R"({"r":"voteInProgressText"})", 1, 0, 0);
  } else if (connections()->GetConnectedClientCount()
             < kKickVoteMinimumClients) {
    // There's too few clients to effectively vote.
    starter->SendScreenMessage(R"({"r":"kickVoteFailedNotEnoughVotersText",)"
                               R"("f":"kickVoteFailedText"})",
                               1, 0, 0);
  } else if (current_time < starter->next_kick_vote_allow_time()) {
    // Not yet allowed error.
    starter->SendScreenMessage(
        R"({"r":"voteDelayText","s":[["${NUMBER}",")"
            + std::to_string(std::max(
                millisecs_t{1},
                (starter->next_kick_vote_allow_time() - current_time) / 1000))
            + "\"]]}",
        1, 0, 0);
  } else {
    std::vector<scene_v1::ConnectionToClient*> connected_clients =
        connections()->GetConnectionsToClients();

    // Ok, kick off a vote.. (send the question and instructions to everyone
    // except the starter and the target).
    for (auto&& client : connected_clients) {
      if (client != starter && client != target) {
        client->SendScreenMessage(
            R"({"r":"kickQuestionText","s":[["${NAME}",)"
                + Utils::GetJSONString(
                    target->GetCombinedSpec().GetDisplayString().c_str())
                + "]]}",
            1, 1, 0);
        client->SendScreenMessage(R"({"r":"kickWithChatText","s":)"
                                  R"([["${YES}","'1'"],["${NO}","'0'"]]})",
                                  1, 1, 0);
      } else {
        // For the kicker/kickee, simply print that a kick vote has been
        // started.
        client->SendScreenMessage(
            R"({"r":"kickVoteStartedText","s":[["${NAME}",)"
                + Utils::GetJSONString(
                    target->GetCombinedSpec().GetDisplayString().c_str())
                + "]]}",
            1, 1, 0);
      }
    }
    kick_vote_end_time_ = current_time + kKickVoteDuration;
    kick_vote_in_progress_ = true;
    last_kick_votes_needed_ = -1;  // make sure we print starting num

    // Keep track of who started the vote.
    kick_vote_starter_ = starter;
    kick_vote_target_ = target;

    // Reset votes for all connected clients.
    for (scene_v1::ConnectionToClient* client :
         connections()->GetConnectionsToClients()) {
      if (client == starter) {
        client->set_kick_voted(true);
        client->set_kick_vote_choice(true);
      } else {
        client->set_kick_voted(false);
      }
    }
  }
}

void ClassicAppMode::SetForegroundScene(scene_v1::Scene* sg) {
  assert(g_base->InLogicThread());
  if (foreground_scene_.get() != sg) {
    foreground_scene_ = sg;

    // If this scene has a globals-node, put it in charge of stuff.
    if (scene_v1::GlobalsNode* g = sg->globals_node()) {
      g->SetAsForeground();
    }
  }
}

auto ClassicAppMode::GetNetworkDebugString() -> std::string {
  char net_info_str[128];
  int64_t in_count = 0;
  int64_t in_size = 0;
  int64_t in_size_compressed = 0;
  int64_t outCount = 0;
  int64_t out_size = 0;
  int64_t out_size_compressed = 0;
  int64_t resends = 0;
  int64_t resends_size = 0;
  bool show = false;

  // Add in/out data for any host connection.
  if (scene_v1::ConnectionToHost* connection_to_host =
          connections()->connection_to_host()) {
    if (connection_to_host->can_communicate()) show = true;
    in_size += connection_to_host->GetBytesInPerSecond();
    in_size_compressed += connection_to_host->GetBytesInPerSecondCompressed();
    in_count += connection_to_host->GetMessagesInPerSecond();
    out_size += connection_to_host->GetBytesOutPerSecond();
    out_size_compressed += connection_to_host->GetBytesOutPerSecondCompressed();
    outCount += connection_to_host->GetMessagesOutPerSecond();
    resends += connection_to_host->GetMessageResendsPerSecond();
    resends_size += connection_to_host->GetBytesResentPerSecond();
  } else {
    int connected_count = 0;
    for (auto&& i : connections()->connections_to_clients()) {
      scene_v1::ConnectionToClient* client = i.second.get();
      if (client->can_communicate()) {
        show = true;
        connected_count += 1;
      }
      in_size += client->GetBytesInPerSecond();
      in_size_compressed += client->GetBytesInPerSecondCompressed();
      in_count += client->GetMessagesInPerSecond();
      out_size += client->GetBytesOutPerSecond();
      out_size_compressed += client->GetBytesOutPerSecondCompressed();
      outCount += client->GetMessagesOutPerSecond();
      resends += client->GetMessageResendsPerSecond();
      resends_size += client->GetBytesResentPerSecond();
    }
  }
  if (!show) {
    return "";
  }
  snprintf(net_info_str, sizeof(net_info_str),
           "in:   %d/%d/%d\nout: %d/%d/%d\nrpt: %d/%d",
           static_cast_check_fit<int>(in_size),
           static_cast_check_fit<int>(in_size_compressed),
           static_cast_check_fit<int>(in_count),
           static_cast_check_fit<int>(out_size),
           static_cast_check_fit<int>(out_size_compressed),
           static_cast_check_fit<int>(outCount),
           static_cast_check_fit<int>(resends_size),
           static_cast_check_fit<int>(resends));
  return net_info_str;
}
auto ClassicAppMode::GetDisplayPing() -> std::optional<float> {
  if (scene_v1::ConnectionToHost* connection_to_host =
          connections()->connection_to_host()) {
    if (connection_to_host->can_communicate()) {
      return connection_to_host->current_ping();
    }
  }
  return {};
}

void ClassicAppMode::CleanUpBeforeConnectingToHost() {
  // We can't have connected clients and a host-connection at the same time.
  // Make a minimal attempt to disconnect any client connections we have, but
  // get them off the list immediately.
  // FIXME: Should we have a 'purgatory' for dying client connections?..
  //  (they may not get the single 'go away' packet we send here)
  connections_->ForceDisconnectClients();

  // Also make sure our public party state is off; this will inform the server
  // that it should not be handing out our address to anyone.
  SetPublicPartyEnabled(false);
}

void ClassicAppMode::LaunchHostSession(PyObject* session_type_obj,
                                       base::BenchmarkType benchmark_type) {
  if (in_update_) {
    throw Exception(
        "can't call host_session() from within session update; use "
        "babase.pushcall()");
  }

  assert(g_base->InLogicThread());

  connections_->PrepareForLaunchHostSession();

  // Don't want to pick up any old stuff in here.
  base::ScopedSetContext ssc(nullptr);

  // This should kill any current session and get us back to a blank slate.
  Reset_();

  Object::WeakRef<scene_v1::Session> old_foreground_session(
      foreground_session_);
  try {
    // Create the new session.
    auto s(Object::New<scene_v1::HostSession>(session_type_obj));
    s->set_benchmark_type(benchmark_type);
    sessions_.emplace_back(s);

    // It should have set itself as FG.
    assert(foreground_session_ == s);
  } catch (const std::exception& e) {
    // If it failed, restore the previous session context and re-throw the
    // exception.
    SetForegroundSession(old_foreground_session.get());
    throw Exception(std::string("HostSession failed: ") + e.what());
  }
}

void ClassicAppMode::LaunchReplaySession(const std::string& file_name) {
  if (in_update_)
    throw Exception(
        "can't launch a session from within a session update; use "
        "babase.pushcall()");

  assert(g_base->InLogicThread());

  // Don't want to pick up any old stuff in here.
  base::ScopedSetContext ssc(nullptr);

  // This should kill any current session and get us back to a blank slate.
  Reset_();

  // Create the new session.
  Object::WeakRef<scene_v1::Session> old_foreground_session(
      foreground_session_);
  try {
    auto s(Object::New<scene_v1::Session, scene_v1::ClientSessionReplay>(
        file_name));
    sessions_.push_back(s);

    // It should have set itself as FG.
    assert(foreground_session_ == s);
  } catch (const std::exception& e) {
    // If it failed, restore the previous current session and re-throw the
    // exception.
    SetForegroundSession(old_foreground_session.get());
    throw Exception(std::string("HostSession failed: ") + e.what());
  }
}

void ClassicAppMode::LaunchClientSession() {
  if (in_update_) {
    throw Exception(
        "can't launch a session from within a session update; use "
        "babase.pushcall()");
  }
  assert(g_base->InLogicThread());

  // Don't want to pick up any old stuff in here.
  base::ScopedSetContext ssc(nullptr);

  // This should kill any current session and get us back to a blank slate.
  Reset_();

  // Create the new session.
  Object::WeakRef<scene_v1::Session> old_foreground_session(
      foreground_session_);
  try {
    auto s(Object::New<scene_v1::Session, scene_v1::ClientSessionNet>());
    sessions_.push_back(s);

    // It should have set itself as FG.
    assert(foreground_session_ == s);
  } catch (const std::exception& e) {
    // If it failed, restore the previous current session and re-throw.
    SetForegroundSession(old_foreground_session.get());
    throw Exception(std::string("HostSession failed: ") + e.what());
  }
}

void ClassicAppMode::ChangeGameSpeed(int offs) {
  assert(g_base->InLogicThread());

  // If we're in a replay session, adjust playback speed there.
  if (dynamic_cast<scene_v1::ClientSessionReplay*>(GetForegroundSession())) {
    int old_speed = replay_speed_exponent();
    SetReplaySpeedExponent(replay_speed_exponent() + offs);
    if (old_speed != replay_speed_exponent()) {
      g_base->ScreenMessage(
          "{\"r\":\"watchWindow.playbackSpeedText\","
          "\"s\":[[\"${SPEED}\",\""
          + std::to_string(replay_speed_mult()) + "\"]]}");
    }
    return;
  }
  // Otherwise, in debug builds, we allow speeding/slowing anything.
  if (g_buildconfig.debug_build()) {
    debug_speed_exponent_ += offs;
    debug_speed_mult_ = powf(2.0f, static_cast<float>(debug_speed_exponent_));
    g_base->ScreenMessage("DEBUG GAME SPEED TO "
                          + std::to_string(debug_speed_mult_));
    scene_v1::Session* s = GetForegroundSession();
    if (s) {
      s->DebugSpeedMultChanged();
    }
  }
}

void ClassicAppMode::OnScreenSizeChange() {
  if (scene_v1::Session* session = GetForegroundSession()) {
    session->OnScreenSizeChange();
  }
}

// Called by a newly made Session instance to set itself as the current
// session.
void ClassicAppMode::SetForegroundSession(scene_v1::Session* s) {
  assert(g_base->InLogicThread());
  foreground_session_ = s;
}

void ClassicAppMode::LocalDisplayChatMessage(
    const std::vector<uint8_t>& buffer) {
  // 1 type byte, 1 spec-len byte, 1 or more spec chars, 0 or more msg chars.
  if (buffer.size() > 3) {
    size_t spec_len = buffer[1];
    if (spec_len > 0 && spec_len + 2 <= buffer.size()) {
      size_t msg_len = buffer.size() - spec_len - 2;
      std::vector<char> b1(spec_len + 1);
      memcpy(&(b1[0]), &(buffer[2]), spec_len);
      b1[spec_len] = 0;
      std::vector<char> b2(msg_len + 1);
      if (msg_len > 0) {
        memcpy(&(b2[0]), &(buffer[2 + spec_len]), msg_len);
      }
      b2[msg_len] = 0;

      std::string final_message =
          scene_v1::PlayerSpec(b1.data()).GetDisplayString() + ": " + b2.data();

      // Store it locally.
      chat_messages_.push_back(final_message);
      while (chat_messages_.size() > kMaxChatMessages) {
        chat_messages_.pop_front();
      }

      // Show it on the screen if they don't have their chat window open
      // (and don't have chat muted).
      if (!g_base->ui->IsPartyWindowOpen()) {
        if (!chat_muted_) {
          g_base->ScreenMessage(final_message, {0.7f, 1.0f, 0.7f});
        }
      } else {
        // Party window is open - notify it that there's a new message.
        g_scene_v1->python->HandleLocalChatMessage(final_message);
      }
      if (!chat_muted_) {
        g_base->audio->SafePlaySysSound(base::SysSoundID::kTap);
      }
    }
  }
}

void ClassicAppMode::ApplyAppConfig() {
  // Kick-idle-players setting (hmm is this still relevant?).
  auto* host_session =
      dynamic_cast<scene_v1::HostSession*>(foreground_session_.get());
  kick_idle_players_ =
      g_base->app_config->Resolve(base::AppConfig::BoolID::kKickIdlePlayers);
  if (host_session) {
    host_session->SetKickIdlePlayers(kick_idle_players_);
  }

  chat_muted_ =
      g_base->app_config->Resolve(base::AppConfig::BoolID::kChatMuted);

  idle_exit_minutes_ = g_base->app_config->Resolve(
      base::AppConfig::OptionalFloatID::kIdleExitMinutes);

  // Whether to highlight chests that *could* be opened with tokens.
  root_ui_highlight_potential_token_purchases_ = g_base->app_config->Resolve(
      base::AppConfig::BoolID::kHighlightPotentialTokenPurchases);
  // Apply to any running ui.
  if (uiv1_) {
    if (auto* root_widget = uiv1_->root_widget()) {
      root_widget->set_highlight_potential_token_purchases(
          root_ui_highlight_potential_token_purchases_);
    }
  }
}

void ClassicAppMode::PruneSessions_() {
  bool have_dead_session = false;
  for (auto&& i : sessions_) {
    if (i.exists()) {
      // If this session is no longer foreground and is ready to die, kill it.
      if (i.exists() && i.get() != foreground_session_.get()) {
        try {
          i.Clear();
        } catch (const std::exception& e) {
          g_core->logging->Log(
              LogName::kBa, LogLevel::kError,
              "Exception killing Session: " + std::string(e.what()));
        }
        have_dead_session = true;
      }
    } else {
      have_dead_session = true;
    }
  }
  if (have_dead_session) {
    std::vector<Object::Ref<scene_v1::Session> > live_list;
    for (auto&& i : sessions_) {
      if (i.exists()) {
        live_list.push_back(i);
      }
    }
    sessions_.swap(live_list);
  }
}

void ClassicAppMode::LanguageChanged() {
  assert(g_base && g_base->InLogicThread());
  if (scene_v1::Session* session = GetForegroundSession()) {
    session->LanguageChanged();
  }
}

void ClassicAppMode::SetReplaySpeedExponent(int val) {
  replay_speed_exponent_ = std::min(3, std::max(-3, val));
  replay_speed_mult_ = powf(2.0f, static_cast<float>(replay_speed_exponent_));
}

void ClassicAppMode::PauseReplay() { replay_paused_ = true; }

void ClassicAppMode::ResumeReplay() { replay_paused_ = false; }

void ClassicAppMode::SetDebugSpeedExponent(int val) {
  debug_speed_exponent_ = val;
  debug_speed_mult_ = powf(2.0f, static_cast<float>(debug_speed_exponent_));

  scene_v1::Session* s = GetForegroundSession();
  if (s) s->DebugSpeedMultChanged();
}

void ClassicAppMode::SetPublicPartyEnabled(bool val) {
  assert(g_base->InLogicThread());
  if (val == public_party_enabled_) {
    return;
  }
  public_party_enabled_ = val;
  g_base->Plus()->PushPublicPartyState();
}

void ClassicAppMode::SetPublicPartySize(int count) {
  assert(g_base->InLogicThread());
  if (count == public_party_size_) {
    return;
  }
  public_party_size_ = count;

  // Push our new state to the server *ONLY* if public-party is turned on
  // (wasteful otherwise).
  if (public_party_enabled_) {
    g_base->Plus()->PushPublicPartyState();
  }
}

void ClassicAppMode::SetPublicPartyQueueEnabled(bool enabled) {
  assert(g_base->InLogicThread());
  if (enabled == public_party_queue_enabled_) {
    return;
  }
  public_party_queue_enabled_ = enabled;

  // Push our new state to the server *ONLY* if public-party is turned on
  // (wasteful otherwise).
  if (public_party_enabled_) {
    g_base->Plus()->PushPublicPartyState();
  }
}

void ClassicAppMode::SetPublicPartyMaxSize(int count) {
  assert(g_base->InLogicThread());
  if (count == public_party_max_size_) {
    return;
  }
  public_party_max_size_ = count;

  // Push our new state to the server *ONLY* if public-party is turned on
  // (wasteful otherwise).
  if (public_party_enabled_) {
    g_base->Plus()->PushPublicPartyState();
  }
}

void ClassicAppMode::SetPublicPartyName(const std::string& name) {
  assert(g_base->InLogicThread());
  if (name == public_party_name_) {
    return;
  }
  public_party_name_ = name;

  // Push our new state to the server *ONLY* if public-party is turned on
  // (wasteful otherwise).
  if (public_party_enabled_) {
    g_base->Plus()->PushPublicPartyState();
  }
}

void ClassicAppMode::SetPublicPartyStatsURL(const std::string& url) {
  assert(g_base->InLogicThread());
  if (url == public_party_stats_url_) {
    return;
  }
  public_party_stats_url_ = url;

  // Push our new state to the server *ONLY* if public-party is turned on
  // (wasteful otherwise).
  if (public_party_enabled_) {
    g_base->Plus()->PushPublicPartyState();
  }
}

void ClassicAppMode::SetPublicPartyPlayerCount(int count) {
  assert(g_base->InLogicThread());
  if (count == public_party_player_count_) {
    return;
  }
  public_party_player_count_ = count;

  // Push our new state to the server *ONLY* if public-party is turned on
  // (wasteful otherwise).
  if (public_party_enabled_) {
    g_base->Plus()->PushPublicPartyState();
  }
}

auto ClassicAppMode::DoesWorldFillScreen() -> bool {
  if (auto* session = GetForegroundSession()) {
    return session->DoesFillScreen();
  }
  return false;
}

void ClassicAppMode::DrawWorld(base::FrameDef* frame_def) {
  if (auto* session = GetForegroundSession()) {
    session->Draw(frame_def);
    frame_def->set_benchmark_type(session->benchmark_type());
  }
}

auto ClassicAppMode::ShouldAnnouncePartyJoinsAndLeaves() -> bool {
  assert(g_base->InLogicThread());

  // At the moment we don't announce these for public internet parties.. (too
  // much noise).
  return !public_party_enabled();
}

auto ClassicAppMode::IsPlayerBanned(const scene_v1::PlayerSpec& spec) -> bool {
  millisecs_t current_time = g_core->AppTimeMillisecs();

  // Now is a good time to prune no-longer-banned specs.
  while (!banned_players_.empty()
         && banned_players_.front().first < current_time) {
    banned_players_.pop_front();
  }
  // NOLINTNEXTLINE(readability-use-anyofallof)
  for (auto&& test_spec : banned_players_) {
    if (test_spec.second == spec) {
      return true;
    }
  }
  return false;
}

void ClassicAppMode::BanPlayer(const scene_v1::PlayerSpec& spec,
                               millisecs_t duration) {
  banned_players_.emplace_back(g_core->AppTimeMillisecs() + duration, spec);
}

void ClassicAppMode::HandleQuitOnIdle_() {
  if (idle_exit_minutes_) {
    auto idle_seconds{static_cast<float>(g_base->input->input_idle_time())
                      * 0.001f};
    if (!idle_exiting_ && idle_seconds > (idle_exit_minutes_.value() * 60.0f)) {
      idle_exiting_ = true;

      g_core->logging->Log(LogName::kBa, LogLevel::kInfo,
                           "Quitting due to reaching idle-exit-minutes.");
      g_base->logic->event_loop()->PushCall([] { g_base->logic->Shutdown(); });
    }
  }
}

void ClassicAppMode::SetInternalMusic(base::SoundAsset* music, float volume,
                                      bool loop) {
  // Stop any playing music.
  if (internal_music_play_id_) {
    g_base->audio->PushSourceStopSoundCall(*internal_music_play_id_);
    internal_music_play_id_.reset();
  }
  // Start any new music provided.
  if (music) {
    assert(!internal_music_play_id_);
    base::AudioSource* s = g_base->audio->SourceBeginNew();
    if (s) {
      s->SetLooping(loop);
      s->SetPositional(false);
      s->SetGain(volume);
      s->SetIsMusic(true);
      internal_music_play_id_ = s->Play(music);
      s->End();
    }
  }
}

void ClassicAppMode::HandleGameQuery(const char* buffer, size_t size,
                                     sockaddr_storage* from) {
  if (size == 5) {
    // If we're already in a party, don't advertise since they wouldn't be
    // able to join us anyway.
    if (g_base->app_mode()->HasConnectionToHost()) {
      return;
    }

    // Pull the query id from the packet.
    uint32_t query_id;
    memcpy(&query_id, buffer + 1, 4);

    // Ship them a response packet containing the query id, our protocol
    // version, our unique-app-instance-id, and our player_spec.
    char msg[400];

    std::string usid = g_base->GetAppInstanceUUID();
    std::string player_spec_string;

    // If we're signed in, send our account spec. Otherwise just send a
    // dummy made with our device name.
    player_spec_string =
        scene_v1::PlayerSpec::GetAccountPlayerSpec().GetSpecString();

    // This should always be the case (len needs to be 1 byte)
    BA_PRECONDITION_FATAL(player_spec_string.size() < 256);

    BA_PRECONDITION_FATAL(!usid.empty());
    if (usid.size() > 100) {
      g_core->logging->Log(LogName::kBa, LogLevel::kError,
                           "had to truncate session-id; shouldn't happen");
      usid.resize(100);
    }
    if (usid.empty()) {
      usid = "error";
    }

    msg[0] = BA_PACKET_HOST_QUERY_RESPONSE;
    memcpy(msg + 1, &query_id, 4);
    uint32_t protocol_version = host_protocol_version();
    memcpy(msg + 5, &protocol_version, 4);
    msg[9] = static_cast<char>(usid.size());
    msg[10] = static_cast<char>(player_spec_string.size());

    memcpy(msg + 11, usid.c_str(), usid.size());
    memcpy(msg + 11 + usid.size(), player_spec_string.c_str(),
           player_spec_string.size());
    size_t msg_len = 11 + player_spec_string.size() + usid.size();
    BA_PRECONDITION_FATAL(msg_len <= sizeof(msg));

    std::vector<uint8_t> msg_buffer(msg_len);
    memcpy(msg_buffer.data(), msg, msg_len);

    g_base->network_writer->PushSendToCall(msg_buffer, SockAddr(*from));

  } else {
    // Log invalid packets only once to avoid weaponized log spam.
    BA_LOG_ONCE(LogName::kBaNetworking, LogLevel::kError,
                "Got invalid game-query packet of len " + std::to_string(size)
                    + "; expected 5.");
  }
}

void ClassicAppMode::RunMainMenu() {
  assert(g_base->InLogicThread());
  if (g_base->logic->shutting_down()) {
    return;
  }
  assert(g_base->InLogicThread());
  PythonRef result =
      g_scene_v1->python->objs()
          .Get(scene_v1::SceneV1Python::ObjID::kLaunchMainMenuSessionCall)
          .Call();
  if (!result.exists()) {
    throw Exception("Error running scene_v1 main menu.");
  }
}

void ClassicAppMode::SetRootUITicketsMeterValue(int value) {
  assert(g_base->InLogicThread());
  if (value == root_ui_tickets_meter_value_) {
    return;
  }
  // Store the value.
  root_ui_tickets_meter_value_ = value;

  // Apply it to any existing UI.
  if (uiv1_) {
    if (auto* root_widget = uiv1_->root_widget()) {
      root_widget->SetTicketsMeterValue(root_ui_tickets_meter_value_);
    }
  }
}

void ClassicAppMode::SetRootUITokensMeterValue(int value) {
  assert(g_base->InLogicThread());
  if (value == root_ui_tokens_meter_value_) {
    return;
  }
  // Store the value.
  root_ui_tokens_meter_value_ = value;

  // Apply it to any existing UI.
  if (uiv1_) {
    if (auto* root_widget = uiv1_->root_widget()) {
      root_widget->SetTokensMeterValue(root_ui_tokens_meter_value_,
                                       root_ui_gold_pass_);
    }
  }
}

void ClassicAppMode::SetRootUILeagueValues(const std::string league_type,
                                           int league_number, int rank) {
  assert(g_base->InLogicThread());

  // Filter out redundant sets.
  if (league_type == root_ui_league_type_
      && league_number == root_ui_league_number_
      && rank == root_ui_league_rank_) {
    return;
  }

  // Store new values.
  root_ui_league_type_ = league_type;
  root_ui_league_number_ = league_number;
  root_ui_league_rank_ = rank;

  // Apply to any existing UI.
  if (uiv1_) {
    if (auto* root_widget = uiv1_->root_widget()) {
      root_widget->SetLeagueRankValues(
          root_ui_league_type_, root_ui_league_number_, root_ui_league_rank_);
    }
  }
}

void ClassicAppMode::GetAccountState(std::string* league_type,
                                     int* league_number, int* league_rank,
                                     int* inbox_count,
                                     bool* inbox_count_is_max) {
  assert(g_base->InLogicThread());
  assert(league_type && league_number && league_rank && inbox_count
         && inbox_count_is_max);

  // What we're asking for here is the current *displayed* values in the ui
  // (the latest values we have provided to them may not be visible yet due
  // to the meter being offscreen/etc.)
  if (uiv1_) {
    if (auto* root_widget = uiv1_->root_widget()) {
      *league_type = root_widget->league_type_vis_value();
      *league_number = root_widget->league_number_vis_value();
      *league_rank = root_widget->league_rank_vis_value();
      *inbox_count = root_widget->inbox_count_vis_value();
      *inbox_count_is_max = root_widget->inbox_count_is_max_vis_value();
      return;
    }
  }

  // Unset.
  *league_type = "";
  *league_number = -1;
  *league_rank = -1;
  *inbox_count = -1;
  *inbox_count_is_max = false;
}

void ClassicAppMode::SetAccountState(const std::string& league_type,
                                     int league_number, int league_rank,
                                     int inbox_count, bool inbox_count_is_max) {
  assert(g_base->InLogicThread());

  // Apply it to any existing UI.
  if (uiv1_) {
    if (auto* root_widget = uiv1_->root_widget()) {
      // Ask the root widget to restore these vis values and kick off anims
      // to the current actual values or whatnot if applicable.
      root_widget->SetAccountState(league_type, league_number, league_rank,
                                   inbox_count, inbox_count_is_max);
    }
  }
}

void ClassicAppMode::SetRootUIAchievementsPercentText(const std::string text) {
  assert(g_base->InLogicThread());
  if (text == root_ui_achievement_percent_text_) {
    return;
  }
  // Store the value.
  root_ui_achievement_percent_text_ = text;

  // Apply it to any existing UI.
  if (uiv1_) {
    if (auto* root_widget = uiv1_->root_widget()) {
      root_widget->SetAchievementPercentText(root_ui_achievement_percent_text_);
    }
  }
}

void ClassicAppMode::SetRootUILevelText(const std::string text) {
  assert(g_base->InLogicThread());
  if (text == root_ui_level_text_) {
    return;
  }

  // Store the value.
  root_ui_level_text_ = text;

  // Apply it to any existing UI.
  if (uiv1_) {
    if (auto* root_widget = uiv1_->root_widget()) {
      root_widget->SetLevelText(root_ui_level_text_);
    }
  }
}

void ClassicAppMode::SetRootUIXPText(const std::string text) {
  assert(g_base->InLogicThread());
  if (text == root_ui_xp_text_) {
    return;
  }

  // Store the value.
  root_ui_xp_text_ = text;

  // Apply it to any existing UI.
  if (uiv1_) {
    if (auto* root_widget = uiv1_->root_widget()) {
      root_widget->SetXPText(root_ui_xp_text_);
    }
  }
}

void ClassicAppMode::SetRootUIInboxState(int count, bool is_max,
                                         const std::string& announce_text) {
  assert(g_base->InLogicThread());
  if (count == root_ui_inbox_count_ && is_max == root_ui_inbox_count_is_max_) {
    return;
  }

  // Store the value.
  root_ui_inbox_count_ = count;
  root_ui_inbox_count_is_max_ = is_max;
  root_ui_inbox_announce_text_ = announce_text;

  // Apply it to any existing UI.
  if (uiv1_) {
    if (auto* root_widget = uiv1_->root_widget()) {
      root_widget->SetInboxState(root_ui_inbox_count_,
                                 root_ui_inbox_count_is_max_,
                                 root_ui_inbox_announce_text_);
    }
  }
}

void ClassicAppMode::SetRootUIGoldPass(bool enabled) {
  assert(g_base->InLogicThread());
  if (enabled == root_ui_gold_pass_) {
    return;
  }

  // Store the value.
  root_ui_gold_pass_ = enabled;

  // Apply it to any existing UI.
  if (uiv1_) {
    if (auto* root_widget = uiv1_->root_widget()) {
      root_widget->SetTokensMeterValue(root_ui_tokens_meter_value_,
                                       root_ui_gold_pass_);
    }
  }
}

void ClassicAppMode::SetHaveLiveAccountValues(bool have_live_values) {
  if (have_live_values == root_ui_have_live_values_) {
    return;
  }

  // Store the value.
  root_ui_have_live_values_ = have_live_values;

  // Apply it to any existing UI.
  if (uiv1_) {
    if (auto* root_widget = uiv1_->root_widget()) {
      root_widget->SetHaveLiveValues(root_ui_have_live_values_);
    }
  }
}

void ClassicAppMode::SetRootUIChests(
    const std::string& chest_0_appearance,
    const std::string& chest_1_appearance,
    const std::string& chest_2_appearance,
    const std::string& chest_3_appearance, seconds_t chest_0_create_time,
    seconds_t chest_1_create_time, seconds_t chest_2_create_time,
    seconds_t chest_3_create_time, seconds_t chest_0_unlock_time,
    seconds_t chest_1_unlock_time, seconds_t chest_2_unlock_time,
    seconds_t chest_3_unlock_time, int chest_0_unlock_tokens,
    int chest_1_unlock_tokens, int chest_2_unlock_tokens,
    int chest_3_unlock_tokens, seconds_t chest_0_ad_allow_time,
    seconds_t chest_1_ad_allow_time, seconds_t chest_2_ad_allow_time,
    seconds_t chest_3_ad_allow_time) {
  assert(g_base->InLogicThread());
  if (chest_0_appearance == root_ui_chest_0_appearance_
      && chest_1_appearance == root_ui_chest_1_appearance_
      && chest_2_appearance == root_ui_chest_2_appearance_
      && chest_3_appearance == root_ui_chest_3_appearance_
      && chest_0_create_time == root_ui_chest_0_create_time_
      && chest_1_create_time == root_ui_chest_1_create_time_
      && chest_2_create_time == root_ui_chest_2_create_time_
      && chest_3_create_time == root_ui_chest_3_create_time_
      && chest_0_unlock_time == root_ui_chest_0_unlock_time_
      && chest_1_unlock_time == root_ui_chest_1_unlock_time_
      && chest_2_unlock_time == root_ui_chest_2_unlock_time_
      && chest_3_unlock_time == root_ui_chest_3_unlock_time_
      && chest_0_ad_allow_time == root_ui_chest_0_ad_allow_time_
      && chest_1_ad_allow_time == root_ui_chest_1_ad_allow_time_
      && chest_2_ad_allow_time == root_ui_chest_2_ad_allow_time_
      && chest_3_ad_allow_time == root_ui_chest_3_ad_allow_time_) {
    return;
  }

  // Store the values.
  root_ui_chest_0_appearance_ = chest_0_appearance;
  root_ui_chest_1_appearance_ = chest_1_appearance;
  root_ui_chest_2_appearance_ = chest_2_appearance;
  root_ui_chest_3_appearance_ = chest_3_appearance;
  root_ui_chest_0_create_time_ = chest_0_create_time;
  root_ui_chest_1_create_time_ = chest_1_create_time;
  root_ui_chest_2_create_time_ = chest_2_create_time;
  root_ui_chest_3_create_time_ = chest_3_create_time;
  root_ui_chest_0_unlock_time_ = chest_0_unlock_time;
  root_ui_chest_1_unlock_time_ = chest_1_unlock_time;
  root_ui_chest_2_unlock_time_ = chest_2_unlock_time;
  root_ui_chest_3_unlock_time_ = chest_3_unlock_time;
  root_ui_chest_0_unlock_tokens_ = chest_0_unlock_tokens;
  root_ui_chest_1_unlock_tokens_ = chest_1_unlock_tokens;
  root_ui_chest_2_unlock_tokens_ = chest_2_unlock_tokens;
  root_ui_chest_3_unlock_tokens_ = chest_3_unlock_tokens;
  root_ui_chest_0_ad_allow_time_ = chest_0_ad_allow_time;
  root_ui_chest_1_ad_allow_time_ = chest_1_ad_allow_time;
  root_ui_chest_2_ad_allow_time_ = chest_2_ad_allow_time;
  root_ui_chest_3_ad_allow_time_ = chest_3_ad_allow_time;

  // Apply it to any existing UI.
  if (uiv1_) {
    if (auto* root_widget = uiv1_->root_widget()) {
      root_widget->SetChests(
          root_ui_chest_0_appearance_, root_ui_chest_1_appearance_,
          root_ui_chest_2_appearance_, root_ui_chest_3_appearance_,
          root_ui_chest_0_create_time_, root_ui_chest_1_create_time_,
          root_ui_chest_2_create_time_, root_ui_chest_3_create_time_,
          root_ui_chest_0_unlock_time_, root_ui_chest_1_unlock_time_,
          root_ui_chest_2_unlock_time_, root_ui_chest_3_unlock_time_,
          root_ui_chest_0_unlock_tokens_, root_ui_chest_1_unlock_tokens_,
          root_ui_chest_2_unlock_tokens_, root_ui_chest_3_unlock_tokens_,
          root_ui_chest_0_ad_allow_time_, root_ui_chest_1_ad_allow_time_,
          root_ui_chest_2_ad_allow_time_, root_ui_chest_3_ad_allow_time_);
    }
  }
}

auto ClassicAppMode::GetBottomLeftEdgeHeight() -> float {
  assert(g_base->InLogicThread());
  if (uiv1_) {
    if (auto* root_widget = uiv1_->root_widget()) {
      return root_widget->bottom_left_height();
    }
  }
  return 0.0f;
}

void ClassicAppMode::AnimateRootUIChestUnlockTime(const std::string& chestid,
                                                  seconds_t duration,
                                                  seconds_t startvalue,
                                                  seconds_t endvalue) {
  assert(g_base->InLogicThread());
  if (uiv1_) {
    if (auto* root_widget = uiv1_->root_widget()) {
      root_widget->AnimateChestUnlockTime(chestid, duration, startvalue,
                                          endvalue);
    }
  }
}

void ClassicAppMode::AnimateRootUITickets(seconds_t duration, int startvalue,
                                          int endvalue) {
  assert(g_base->InLogicThread());
  if (uiv1_) {
    if (auto* root_widget = uiv1_->root_widget()) {
      root_widget->AnimateTickets(duration, startvalue, endvalue);
    }
  }
}

void ClassicAppMode::AnimateRootUITokens(seconds_t duration, int startvalue,
                                         int endvalue) {
  assert(g_base->InLogicThread());
  if (uiv1_) {
    if (auto* root_widget = uiv1_->root_widget()) {
      root_widget->AnimateTokens(duration, startvalue, endvalue);
    }
  }
}

}  // namespace ballistica::classic
