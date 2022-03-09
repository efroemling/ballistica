// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_GAME_GAME_H_
#define BALLISTICA_GAME_GAME_H_

#include <list>
#include <memory>
#include <mutex>
#include <optional>
#include <set>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

#include "ballistica/core/module.h"

namespace ballistica {

const int kMaxPartyNameCombinedSize = 25;

/// The Game Module generally runs on a dedicated thread; it manages
/// all game logic, builds frame_defs to send to the graphics-server for
/// rendering, etc.
class Game : public Module {
 public:
  explicit Game(Thread* thread);
  ~Game() override;
  auto LaunchHostSession(PyObject* session_type_obj,
                         BenchmarkType benchmark_type = BenchmarkType::kNone)
      -> void;
  auto LaunchClientSession() -> void;
  auto LaunchReplaySession(const std::string& file_name) -> void;

  auto PushSetV1LoginCall(V1AccountType account_type,
                          V1LoginState account_state,
                          const std::string& account_name,
                          const std::string& account_id) -> void;
  auto PushInitialScreenCreatedCall() -> void;
  auto PushApplyConfigCall() -> void;
  auto PushRemoveGraphicsServerRenderHoldCall() -> void;
  auto PushInterruptSignalCall() -> void;

  /// Push a generic 'menu press' event, optionally associated with an
  /// input device (nullptr to specify none). Note: caller must ensure
  /// a RemoveInputDevice() call does not arrive at the game thread
  /// before this one.
  auto PushMainMenuPressCall(InputDevice* device) -> void;

  /// Notify the game of a screen-size change (used by the graphics server).
  auto PushScreenResizeCall(float virtual_width, float virtual_height,
                            float physical_width, float physical_height)
      -> void;

  auto PushGameServiceAchievementListCall(
      const std::set<std::string>& achievements) -> void;
  auto PushScoresToBeatResponseCall(bool success,
                                    const std::list<ScoreToBeat>& scores,
                                    void* py_callback) -> void;
  auto PushToggleCollisionGeometryDisplayCall() -> void;
  auto PushToggleDebugInfoDisplayCall() -> void;
  auto PushToggleManualCameraCall() -> void;
  auto PushHavePendingLoadsDoneCall() -> void;
  auto PushFreeMediaComponentRefsCall(
      const std::vector<Object::Ref<MediaComponentData>*>& components) -> void;
  auto PushHavePendingLoadsCall() -> void;
  auto PushShutdownCall(bool soft) -> void;

  auto PushInGameConsoleScriptCommand(const std::string& command) -> void;
  auto ToggleConsole() -> void;
  auto PushConsolePrintCall(const std::string& msg) -> void;
  auto PushStdinScriptCommand(const std::string& command) -> void;
  auto PushMediaPruneCall(int level) -> void;
  auto PushAskUserForTelnetAccessCall() -> void;

  // Push Python call and keep it alive; must be called from game thread.
  auto PushPythonCall(const Object::Ref<PythonContextCall>& call) -> void;
  auto PushPythonCallArgs(const Object::Ref<PythonContextCall>& call,
                          const PythonRef& args) -> void;

  // Push Python call without keeping it alive; must be called from game thread.
  auto PushPythonWeakCall(const Object::WeakRef<PythonContextCall>& call)
      -> void;
  auto PushPythonWeakCallArgs(const Object::WeakRef<PythonContextCall>& call,
                              const PythonRef& args) -> void;

  // Push a raw Python call, decrements its refcount after running.
  // Can be pushed from any thread.
  auto PushPythonRawCallable(PyObject* callable) -> void;
  auto PushScreenMessage(const std::string& message, const Vector3f& color)
      -> void;
  auto RemovePlayer(Player* player) -> void;
  auto PushPlaySoundCall(SystemSoundID sound) -> void;
  auto PushConfirmQuitCall() -> void;
  auto PushStringEditSetCall(const std::string& value) -> void;
  auto PushStringEditCancelCall() -> void;
  auto PushFriendScoreSetCall(const FriendScoreSet& score_set) -> void;
  auto PushShowURLCall(const std::string& url) -> void;
  auto PushBackButtonCall(InputDevice* input_device) -> void;
  auto PushOnAppResumeCall() -> void;
  auto PushFrameDefRequest() -> void;
  auto ChangeGameSpeed(int offs) -> void;
  auto ResetInput() -> void;
  auto RunMainMenu() -> void;
  auto HandleThreadPause() -> void override;

#if BA_VR_BUILD
  auto PushVRHandsState(const VRHandsState& state) -> void;
  const VRHandsState& vr_hands_state() const { return vr_hands_state_; }
#endif

  // Resets tracking used to detect cheating and tampering in local tournaments.
  auto ResetActivityTracking() -> void;

  // Return whichever context is front and center.
  auto GetForegroundContext() -> Context;

  // Return whichever session is front and center.
  auto GetForegroundSession() const -> Session* {
    return foreground_session_.get();
  }

  auto NewRealTimer(millisecs_t length, bool repeat,
                    const Object::Ref<Runnable>& runnable) -> int;
  auto DeleteRealTimer(int timer_id) -> void;
  auto SetRealTimerLength(int timer_id, millisecs_t length) -> void;
  auto SetLanguageKeys(
      const std::unordered_map<std::string, std::string>& language) -> void;
  auto GetResourceString(const std::string& key) -> std::string;
  auto CharStr(SpecialChar id) -> std::string;
  auto CompileResourceString(const std::string& s, const std::string& loc,
                             bool* valid = nullptr) -> std::string;
  auto kick_idle_players() const -> bool { return kick_idle_players_; }
  auto IsInUIContext() const -> bool;

  // Return the actual UI context (hmm couldn't we just use g_ui?).
  auto GetUIContextTarget() const -> UI* {
    assert(g_ui);
    return g_ui;
  }

  // Simply return a context-state pointing to the ui-context (so you don't have
  // to include the ui header).
  auto GetUIContext() const -> Context;

  // Returns the base time used to drive local sims/etc.  This generally tries
  // to match real-time but has a bit of leeway to sync up with frame drawing or
  // slow down if things are behind (it tries to progress by exactly 1000/60 ms
  // each frame, provided we're rendering 60hz).
  auto master_time() const -> millisecs_t { return master_time_; }

  auto debug_speed_mult() const -> float { return debug_speed_mult_; }
  auto SetDebugSpeedExponent(int val) -> void;

  auto SetReplaySpeedExponent(int val) -> void;
  auto replay_speed_exponent() const -> int { return replay_speed_exponent_; }
  auto replay_speed_mult() const -> float { return replay_speed_mult_; }

  auto GetPartySize() const -> int;
  auto last_connection_to_client_join_time() const -> millisecs_t {
    return last_connection_to_client_join_time_;
  }
  auto set_last_connection_to_client_join_time(millisecs_t val) -> void {
    last_connection_to_client_join_time_ = val;
  }

  auto game_roster() const -> cJSON* { return game_roster_; }

  auto chat_messages() const -> const std::list<std::string>& {
    return chat_messages_;
  }

  // Used to know which globals is in control currently/etc.
  auto GetForegroundScene() const -> Scene* {
    assert(InGameThread());
    return foreground_scene_.get();
  }
  auto SetForegroundScene(Scene* sg) -> void;

  auto UpdateGameRoster() -> void;
  auto IsPlayerBanned(const PlayerSpec& spec) -> bool;
  auto BanPlayer(const PlayerSpec& spec, millisecs_t duration) -> void;

  // For cheat detection. Returns the largest amount of time that has passed
  // between frames since our last reset (for detecting memory modification
  // UIs/etc).
  auto largest_draw_time_increment() const -> millisecs_t {
    return largest_draw_time_increment_since_last_reset_;
  }

  // Anti-hacker stuff.
  auto GetTotalTimeSinceReset() const -> millisecs_t {
    return last_draw_real_time_ - first_draw_real_time_;
  }
  auto SetForegroundSession(Session* s) -> void;
  auto SetGameRoster(cJSON* r) -> void;
  auto LocalDisplayChatMessage(const std::vector<uint8_t>& buffer) -> void;
  auto ShouldAnnouncePartyJoinsAndLeaves() -> bool;

  auto StartKickVote(ConnectionToClient* starter, ConnectionToClient* target)
      -> void;
  auto require_client_authentication() const {
    return require_client_authentication_;
  }
  auto set_require_client_authentication(bool enable) -> void {
    require_client_authentication_ = enable;
  }
  auto set_kick_voting_enabled(bool enable) -> void {
    kick_voting_enabled_ = enable;
  }
  auto set_admin_public_ids(const std::set<std::string>& ids) -> void {
    admin_public_ids_ = ids;
  }
  const std::set<std::string>& admin_public_ids() const {
    return admin_public_ids_;
  }

  auto kick_vote_in_progress() const -> bool { return kick_vote_in_progress_; }

  auto SetPublicPartyEnabled(bool val) -> void;
  auto public_party_enabled() const { return public_party_enabled_; }
  auto public_party_size() const { return public_party_size_; }
  auto SetPublicPartySize(int count) -> void;
  auto public_party_max_size() const { return public_party_max_size_; }
  auto public_party_max_player_count() const {
    return public_party_max_player_count_;
  }
  auto public_party_min_league() const -> const std::string& {
    return public_party_min_league_;
  }
  auto public_party_stats_url() const -> const std::string& {
    return public_party_stats_url_;
  }
  auto SetPublicPartyMaxSize(int count) -> void;
  auto SetPublicPartyName(const std::string& name) -> void;
  auto SetPublicPartyStatsURL(const std::string& name) -> void;
  auto public_party_name() const { return public_party_name_; }
  auto public_party_player_count() const { return public_party_player_count_; }
  auto SetPublicPartyPlayerCount(int count) -> void;
  auto ran_app_launch_commands() const { return ran_app_launch_commands_; }
  auto CleanUpBeforeConnectingToHost() -> void;
  auto connections() -> ConnectionSet* {
    assert(connections_.get());
    return connections_.get();
  }
  auto mark_game_roster_dirty() -> void { game_roster_dirty_ = true; }

 private:
  auto HandleQuitOnIdle() -> void;
  auto InitSpecialChars() -> void;
  auto Draw() -> void;
  auto InitialScreenCreated() -> void;
  auto MainMenuPress(InputDevice* device) -> void;
  auto ScreenResize(float virtual_width, float virtual_height,
                    float pixel_width, float pixel_height) -> void;
  auto GameServiceAchievementList(const std::set<std::string>& achievements)
      -> void;
  auto ScoresToBeatResponse(bool success, const std::list<ScoreToBeat>& scores,
                            void* py_callback) -> void;

  auto Prune() -> void;  // Periodic pruning of dead stuff.
  auto Update() -> void;
  auto Process() -> void;
  auto UpdateKickVote() -> void;
  auto RunAppLaunchCommands() -> void;
  auto PruneSessions() -> void;
  auto ApplyConfig() -> void;
  auto UpdateProcessTimer() -> void;
  auto Reset() -> void;
  auto GetGameRosterMessage() -> std::vector<uint8_t>;
  auto Shutdown(bool soft) -> void;

#if BA_VR_BUILD
  VRHandsState vr_hands_state_;
#endif
#if BA_RIFT_BUILD
  int rift_step_index_{};
#endif

  std::unique_ptr<ConnectionSet> connections_;
  std::list<std::pair<millisecs_t, PlayerSpec> > banned_players_;
  std::list<std::string> chat_messages_;
  bool chat_muted_{};
  bool first_update_{true};
  bool game_roster_dirty_{};
  millisecs_t last_connection_to_client_join_time_{};
  int debug_speed_exponent_{};
  float debug_speed_mult_{1.0f};
  int replay_speed_exponent_{};
  float replay_speed_mult_{1.0f};
  bool have_sent_initial_frame_def_{};
  millisecs_t master_time_{};
  millisecs_t master_time_offset_{};
  millisecs_t last_session_update_master_time_{};
  millisecs_t last_game_roster_send_time_{};
  millisecs_t largest_draw_time_increment_since_last_reset_{};
  millisecs_t last_draw_real_time_{};
  millisecs_t first_draw_real_time_{};

  // *All* existing sessions (including old ones waiting to shut down).
  std::vector<Object::Ref<Session> > sessions_;
  Object::WeakRef<Scene> foreground_scene_;
  Object::WeakRef<Session> foreground_session_;
  std::mutex language_mutex_;
  std::unordered_map<std::string, std::string> language_;
  std::mutex special_char_mutex_;
  std::unordered_map<SpecialChar, std::string> special_char_strings_;
  bool ran_app_launch_commands_{};
  bool kick_idle_players_{};
  std::optional<float> idle_exit_minutes_{};
  bool idle_exiting_{};
  std::unique_ptr<TimerList> realtimers_;
  Timer* process_timer_{};
  Timer* headless_update_timer_{};
  Timer* media_prune_timer_{};
  Timer* debug_timer_{};
  bool have_pending_loads_{};
  bool in_update_{};
  bool require_client_authentication_{};
  bool kick_voting_enabled_{true};
  std::set<std::string> admin_public_ids_;

  cJSON* game_roster_{};
  millisecs_t kick_vote_end_time_{};
  bool kick_vote_in_progress_{};
  int last_kick_votes_needed_{-1};
  Object::WeakRef<ConnectionToClient> kick_vote_starter_;
  Object::WeakRef<ConnectionToClient> kick_vote_target_;
  bool public_party_enabled_{false};
  int public_party_size_{1};  // Always count ourself (is that what we want?).
  int public_party_max_size_{8};
  int public_party_player_count_{0};
  int public_party_max_player_count_{8};
  std::string public_party_name_;
  std::string public_party_min_league_;
  std::string public_party_stats_url_;
};

}  // namespace ballistica

#endif  // BALLISTICA_GAME_GAME_H_
