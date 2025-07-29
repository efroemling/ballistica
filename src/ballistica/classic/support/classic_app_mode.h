// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_CLASSIC_SUPPORT_CLASSIC_APP_MODE_H_
#define BALLISTICA_CLASSIC_SUPPORT_CLASSIC_APP_MODE_H_

#include <list>
#include <map>
#include <memory>
#include <mutex>
#include <optional>
#include <set>
#include <string>
#include <vector>

#include "ballistica/base/app_mode/app_mode.h"
#include "ballistica/base/base.h"
#include "ballistica/classic/classic.h"
#include "ballistica/scene_v1/scene_v1.h"
#include "ballistica/shared/foundation/object.h"
#include "ballistica/ui_v1/ui_v1.h"

namespace ballistica::classic {

const int kMaxPartyNameCombinedSize{25};

/// Defines high level app behavior when we're active.
class ClassicAppMode : public base::AppMode {
 public:
  /// Create or return our singleton (regardless of active state).
  /// Will never return nullptr.
  static auto GetSingleton() -> ClassicAppMode*;

  /// Return our singleton if it is active and nullptr otherwise.
  /// Be sure to handle the case where it is not.
  static auto GetActive() -> ClassicAppMode*;

  /// Return our singleton if it is active and log a warning and return nullptr
  /// if not. Use when you're gracefully handling the nullptr case but don't
  /// expect it to ever occur.
  static auto GetActiveOrWarn() -> ClassicAppMode*;

  /// Return our singleton if it is active and throw an Exception if not.
  /// Use when exception logic can gracefully handle the fail case.
  static auto GetActiveOrThrow() -> ClassicAppMode*;

  /// Return our singleton if it is active and fatal-error otherwise.
  /// Use when you are not handling the nullptr case and don't expect
  /// it to ever occur.
  static auto GetActiveOrFatal() -> ClassicAppMode*;

  void RequestMainUI() override;

  auto HandleJSONPing(const std::string& data_str) -> std::string override;
  void HandleIncomingUDPPacket(const std::vector<uint8_t>& data_in,
                               const SockAddr& addr) override;
  void StepDisplayTime() override;
  void OnAppShutdown() override;
  auto game_roster() const -> cJSON* { return game_roster_; }
  void UpdateGameRoster();
  void MarkGameRosterDirty() { game_roster_dirty_ = true; }
  void SetGameRoster(cJSON* r);
  auto GetPartySize() const -> int override;
  auto kick_vote_in_progress() const -> bool { return kick_vote_in_progress_; }
  void StartKickVote(scene_v1::ConnectionToClient* starter,
                     scene_v1::ConnectionToClient* target);
  void set_kick_voting_enabled(bool enable) { kick_voting_enabled_ = enable; }
  void SetForegroundScene(scene_v1::Scene* sg);

  void LaunchHostSession(
      PyObject* session_type_obj,
      base::BenchmarkType benchmark_type = base::BenchmarkType::kNone);
  void LaunchReplaySession(const std::string& file_name);
  void LaunchClientSession();

  auto GetNetworkDebugString() -> std::string override;
  auto GetDisplayPing() -> std::optional<float> override;
  auto HasConnectionToHost() const -> bool override;
  auto HasConnectionToClients() const -> bool override;
  auto connections() const -> scene_v1::ConnectionSet* {
    assert(connections_.get());
    return connections_.get();
  }
  void CleanUpBeforeConnectingToHost();
  void ChangeGameSpeed(int offs) override;
  void SetForegroundSession(scene_v1::Session* s);
  void LocalDisplayChatMessage(const std::vector<uint8_t>& buffer);
  auto chat_messages() const -> const std::list<std::string>& {
    return chat_messages_;
  }
  void ApplyAppConfig() override;

  // Return whichever session is front and center.
  auto GetForegroundSession() const -> scene_v1::Session* {
    return foreground_session_.get();
  }

  // Used to know which globals is in control currently/etc.
  auto GetForegroundScene() const -> scene_v1::Scene* {
    assert(g_base->InLogicThread());
    return foreground_scene_.get();
  }
  auto GetForegroundContext() -> base::ContextRef override;
  auto debug_speed_mult() const -> float { return debug_speed_mult_; }
  auto replay_speed_exponent() const -> int { return replay_speed_exponent_; }
  auto replay_speed_mult() const -> float { return replay_speed_mult_; }
  auto is_replay_paused() const -> bool { return replay_paused_; }
  void OnScreenSizeChange() override;
  auto kick_idle_players() const -> bool { return kick_idle_players_; }
  void LanguageChanged() override;
  auto GetBottomLeftEdgeHeight() -> float override;

  void SetDebugSpeedExponent(int val);
  void SetReplaySpeedExponent(int val);
  void PauseReplay();
  void ResumeReplay();
  void set_admin_public_ids(const std::set<std::string>& ids) {
    admin_public_ids_ = ids;
  }
  const std::set<std::string>& admin_public_ids() const {
    return admin_public_ids_;
  }
  auto last_connection_to_client_join_time() const -> millisecs_t {
    return last_connection_to_client_join_time_;
  }
  void set_last_connection_to_client_join_time(millisecs_t val) {
    last_connection_to_client_join_time_ = val;
  }
  auto LastClientJoinTime() const -> millisecs_t override;
  void SetPublicPartyEnabled(bool val);
  auto public_party_enabled() const { return public_party_enabled_; }
  auto public_party_size() const { return public_party_size_; }
  void SetPublicPartySize(int count);
  auto public_party_max_size() const { return public_party_max_size_; }
  void SetPublicPartyQueueEnabled(bool enabled);
  auto public_party_queue_enabled() const {
    return public_party_queue_enabled_;
  }
  auto public_party_max_player_count() const {
    return public_party_max_player_count_;
  }
  auto public_party_min_league() const -> const std::string& {
    return public_party_min_league_;
  }
  auto public_party_stats_url() const -> const std::string& {
    return public_party_stats_url_;
  }

  void SetPublicPartyMaxSize(int count);
  void SetPublicPartyName(const std::string& name);
  void SetPublicPartyStatsURL(const std::string& name);
  auto public_party_name() const { return public_party_name_; }
  auto public_party_player_count() const { return public_party_player_count_; }
  void SetPublicPartyPlayerCount(int count);
  auto ShouldAnnouncePartyJoinsAndLeaves() -> bool;
  auto require_client_authentication() const {
    return require_client_authentication_;
  }
  void set_require_client_authentication(bool enable) {
    require_client_authentication_ = enable;
  }
  auto IsPlayerBanned(const scene_v1::PlayerSpec& spec) -> bool;
  void BanPlayer(const scene_v1::PlayerSpec& spec, millisecs_t duration);
  void OnAppStart() override;
  void OnAppSuspend() override;
  void OnAppUnsuspend() override;
  auto IsInMainMenu() const -> bool override;
  auto CreateInputDeviceDelegate(base::InputDevice* device)
      -> base::InputDeviceDelegate* override;

  void SetInternalMusic(base::SoundAsset* music, float volume = 1.0,
                        bool loop = true);

  // Run a cycle of host scanning (basically sending out a broadcast packet
  // to see who's out there).
  void HostScanCycle();
  void EndHostScanning();

  struct ScanResultsEntry {
    std::string display_string;
    std::string address;
  };

  auto GetScanResults() -> std::vector<ScanResultsEntry>;
  void HandleGameQuery(const char* buffer, size_t size,
                       sockaddr_storage* from) override;
  void DrawWorld(base::FrameDef* frame_def) override;
  auto DoesWorldFillScreen() -> bool override;
  void RunMainMenu();

  auto dynamics_sync_time() const { return dynamics_sync_time_; }
  void set_dynamics_sync_time(int val) { dynamics_sync_time_ = val; }
  auto delay_bucket_samples() const { return delay_bucket_samples_; }
  void set_delay_bucket_samples(int val) { delay_bucket_samples_ = val; }
  auto buffer_time() const { return buffer_time_; }
  void set_buffer_time(int val) { buffer_time_ = val; }
  void OnActivate() override;
  auto GetHeadlessNextDisplayTimeStep() -> microsecs_t override;

  auto host_protocol_version() const {
    assert(host_protocol_version_ != -1);
    return host_protocol_version_;
  }

  auto public_party_public_address_ipv4() const {
    return public_party_public_address_ipv4_;
  }
  void set_public_party_public_address_ipv4(
      const std::optional<std::string>& val) {
    public_party_public_address_ipv4_ = val;
  }

  auto public_party_public_address_ipv6() const {
    return public_party_public_address_ipv6_;
  }
  void set_public_party_public_address_ipv6(
      const std::optional<std::string>& val) {
    public_party_public_address_ipv6_ = val;
  }

  void AnimateRootUIChestUnlockTime(const std::string& chestid,
                                    seconds_t duration, seconds_t startvalue,
                                    seconds_t endvalue);
  void AnimateRootUITickets(seconds_t duration, int startvalue, int endvalue);
  void AnimateRootUITokens(seconds_t duration, int startvalue, int endvalue);
  void SetRootUITicketsMeterValue(int value);
  void SetRootUITokensMeterValue(int value);
  void SetRootUILeagueValues(const std::string league_type, int league_number,
                             int rank);
  void SetRootUIAchievementsPercentText(const std::string text);
  void SetRootUILevelText(const std::string text);
  void SetRootUIXPText(const std::string text);
  void SetRootUIInboxState(int count, bool is_max,
                           const std::string& announce_text);
  void SetRootUIGoldPass(bool enabled);
  void SetRootUIChests(
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
      seconds_t chest_3_ad_allow_time);
  void SetHaveLiveAccountValues(bool val);
  void GetAccountState(std::string* league_type, int* league_number,
                       int* league_rank, int* inbox_count,
                       bool* inbox_count_is_max);
  void SetAccountState(const std::string& league_type, int league_number,
                       int league_rank, int inbox_count,
                       bool inbox_count_is_max);

 private:
  ClassicAppMode();
  void OnGameRosterChanged_();
  void PruneScanResults_();
  void UpdateKickVote_();
  auto GetGameRosterMessage_() -> std::vector<uint8_t>;
  void Reset_();
  void PruneSessions_();
  void HandleQuitOnIdle_();

  struct ScanResultsEntryPriv_;

  // Note: would use an unordered_map here but gcc doesn't seem to allow
  // forward declarations of their template params.
  std::map<std::string, ScanResultsEntryPriv_> scan_results_;
  std::mutex scan_results_mutex_;

  std::string root_ui_chest_0_appearance_;
  std::string root_ui_chest_1_appearance_;
  std::string root_ui_chest_2_appearance_;
  std::string root_ui_chest_3_appearance_;
  seconds_t root_ui_chest_0_create_time_;
  seconds_t root_ui_chest_1_create_time_;
  seconds_t root_ui_chest_2_create_time_;
  seconds_t root_ui_chest_3_create_time_;
  seconds_t root_ui_chest_0_unlock_time_;
  seconds_t root_ui_chest_1_unlock_time_;
  seconds_t root_ui_chest_2_unlock_time_;
  seconds_t root_ui_chest_3_unlock_time_;
  seconds_t root_ui_chest_0_ad_allow_time_;
  seconds_t root_ui_chest_1_ad_allow_time_;
  seconds_t root_ui_chest_2_ad_allow_time_;
  seconds_t root_ui_chest_3_ad_allow_time_;

  uint32_t next_scan_query_id_{};
  int scan_socket_{-1};
  int host_protocol_version_{-1};

  std::list<std::string> chat_messages_;
  // *All* existing sessions (including old ones waiting to shut down).
  std::vector<Object::Ref<scene_v1::Session> > sessions_;
  Object::WeakRef<scene_v1::Scene> foreground_scene_;
  Object::WeakRef<scene_v1::Session> foreground_session_;

  bool chat_muted_{};
  bool in_update_{};
  bool kick_idle_players_{};
  bool public_party_enabled_{};
  bool public_party_queue_enabled_{true};
  bool require_client_authentication_{};
  bool idle_exiting_{};
  bool game_roster_dirty_{};
  bool kick_vote_in_progress_{};
  bool kick_voting_enabled_{true};
  bool replay_paused_{};
  bool root_ui_gold_pass_{};
  bool root_ui_have_live_values_{};
  bool root_ui_highlight_potential_token_purchases_{};

  ui_v1::UIV1FeatureSet* uiv1_{};
  cJSON* game_roster_{};
  millisecs_t last_game_roster_send_time_{};
  std::unique_ptr<scene_v1::ConnectionSet> connections_;
  Object::WeakRef<scene_v1::ConnectionToClient> kick_vote_starter_;
  Object::WeakRef<scene_v1::ConnectionToClient> kick_vote_target_;
  millisecs_t kick_vote_end_time_{};
  int last_kick_votes_needed_{-1};
  millisecs_t legacy_display_time_millisecs_{};
  millisecs_t legacy_display_time_millisecs_prev_{-1};

  // How often we send dynamics resync messages.
  int dynamics_sync_time_{500};
  // How many steps we sample for each bucket.
  int delay_bucket_samples_{60};

  // Maximum time in milliseconds to buffer game input/output before sending
  // it over the network.
  int buffer_time_{};

  millisecs_t next_long_update_report_time_{};
  int debug_speed_exponent_{};
  int replay_speed_exponent_{};
  int public_party_size_{1};  // Always count ourself (is that what we want?).
  int public_party_max_size_{8};
  int public_party_player_count_{0};
  int public_party_max_player_count_{8};
  int root_ui_tickets_meter_value_{-1};
  int root_ui_tokens_meter_value_{-1};
  int root_ui_league_rank_{-1};
  int root_ui_league_number_{-1};
  int root_ui_inbox_count_{-1};
  int root_ui_chest_0_unlock_tokens_;
  int root_ui_chest_1_unlock_tokens_;
  int root_ui_chest_2_unlock_tokens_;
  int root_ui_chest_3_unlock_tokens_;
  float debug_speed_mult_{1.0f};
  float replay_speed_mult_{1.0f};
  std::set<std::string> admin_public_ids_;
  millisecs_t last_connection_to_client_join_time_{};
  std::string public_party_name_;
  std::string public_party_min_league_;
  std::string public_party_stats_url_;
  std::string root_ui_league_type_;
  std::string root_ui_achievement_percent_text_;
  std::string root_ui_level_text_;
  std::string root_ui_xp_text_;
  std::string root_ui_inbox_announce_text_;
  std::list<std::pair<millisecs_t, scene_v1::PlayerSpec> > banned_players_;
  std::optional<float> idle_exit_minutes_{};
  std::optional<uint32_t> internal_music_play_id_{};
  std::optional<std::string> public_party_public_address_ipv4_{};
  std::optional<std::string> public_party_public_address_ipv6_{};
  bool root_ui_inbox_count_is_max_{};
};

}  // namespace ballistica::classic

#endif  // BALLISTICA_CLASSIC_SUPPORT_CLASSIC_APP_MODE_H_
