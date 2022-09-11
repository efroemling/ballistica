// Released under the MIT License. See LICENSE for details.

#include "ballistica/game/game.h"

#include "ballistica/app/app_config.h"
#include "ballistica/app/app_flavor.h"
#include "ballistica/audio/audio.h"
#include "ballistica/core/thread.h"
#include "ballistica/dynamics/bg/bg_dynamics.h"
#include "ballistica/game/connection/connection_set.h"
#include "ballistica/game/connection/connection_to_client_udp.h"
#include "ballistica/game/connection/connection_to_host_udp.h"
#include "ballistica/game/friend_score_set.h"
#include "ballistica/game/host_activity.h"
#include "ballistica/game/player.h"
#include "ballistica/game/session/client_session.h"
#include "ballistica/game/session/host_session.h"
#include "ballistica/game/session/net_client_session.h"
#include "ballistica/game/session/replay_client_session.h"
#include "ballistica/game/v1_account.h"
#include "ballistica/generic/json.h"
#include "ballistica/generic/timer.h"
#include "ballistica/graphics/graphics.h"
#include "ballistica/graphics/graphics_server.h"
#include "ballistica/graphics/text/text_graphics.h"
#include "ballistica/input/device/client_input_device.h"
#include "ballistica/input/device/keyboard_input.h"
#include "ballistica/input/device/touch_input.h"
#include "ballistica/internal/app_internal.h"
#include "ballistica/networking/network_writer.h"
#include "ballistica/networking/sockaddr.h"
#include "ballistica/networking/telnet_server.h"
#include "ballistica/python/python.h"
#include "ballistica/python/python_command.h"
#include "ballistica/python/python_context_call.h"
#include "ballistica/python/python_sys.h"
#include "ballistica/scene/node/globals_node.h"
#include "ballistica/ui/console.h"
#include "ballistica/ui/root_ui.h"
#include "ballistica/ui/ui.h"
#include "ballistica/ui/widget/root_widget.h"
#include "ballistica/ui/widget/text_widget.h"

namespace ballistica {

/// How long a kick vote lasts.
const int kKickVoteDuration = 30000;

/// How long everyone has to wait to start a new kick vote after a failed one.
const int kKickVoteFailRetryDelay = 60000;

/// Extra delay for the initiator of a failed vote.
const int kKickVoteFailRetryDelayInitiatorExtra = 120000;

// Minimum clients that must be present for a kick vote to count.
// (for non-headless builds we require more votes since the host doesn't count
// but may be playing (in a 2on2 with 3 clients, don't want 2 clients able to
// kick).
// NOLINTNEXTLINE(cert-err58-cpp)
const int kKickVoteMinimumClients = (g_buildconfig.headless_build() ? 3 : 4);

const int kMaxChatMessages = 40;

// Go with 5 minute ban.
const int kKickBanSeconds = 5 * 60;

Game::Game(Thread* thread)
    : thread_(thread),
      game_roster_(cJSON_CreateArray()),
      realtimers_(new TimerList()),
      connections_(std::make_unique<ConnectionSet>()) {
  assert(g_game == nullptr);
  g_game = this;

  try {
    // Our thread should hold the Python GIL by default.
    // TODO(ericf): It could be better to have each individual Python call
    // we make acquire the GIL. Then we're not holding it during long
    // bits of C++ logic.
    thread->SetHoldsPythonGIL();

    if (!HeadlessMode()) {
      BGDynamics::Init();
    }

    InitSpecialChars();

    // We want to be informed when our thread is pausing.
    thread->AddPauseCallback(NewLambdaRunnableRaw([this] { OnThreadPause(); }));

    g_ui->LogicThreadInit();

    // Init python and apply our settings immediately.
    // This way we can get started loading stuff in the background
    // and it'll come in with the correct texture quality etc.
    g_python->Reset(true);
  } catch (const std::exception& e) {
    // If anything went wrong, trigger a deferred error.
    // This way it is more likely we can show a fatal error dialog
    // since the main thread won't be blocking waiting for us to init.
    std::string what = e.what();
    this->thread()->PushCall([what] {
      // Just throw a standard exception since our what already
      // contains a stack trace; if we throw an Exception we wind
      // up with a useless second one.
      throw std::logic_error(what.c_str());
    });
  }
}

auto Game::OnThreadPause() -> void {
  ScopedSetContext cp(GetUIContextTarget());

  // Let Python and internal layers do their thing.
  g_python->obj(Python::ObjID::kOnAppPauseCall).Call();
  g_app_internal->OnLogicThreadPause();
}

void Game::InitSpecialChars() {
  std::scoped_lock lock(special_char_mutex_);

  special_char_strings_[SpecialChar::kDownArrow] = "\xee\x80\x84";
  special_char_strings_[SpecialChar::kUpArrow] = "\xee\x80\x83";
  special_char_strings_[SpecialChar::kLeftArrow] = "\xee\x80\x81";
  special_char_strings_[SpecialChar::kRightArrow] = "\xee\x80\x82";
  special_char_strings_[SpecialChar::kTopButton] = "\xee\x80\x86";
  special_char_strings_[SpecialChar::kLeftButton] = "\xee\x80\x85";
  special_char_strings_[SpecialChar::kRightButton] = "\xee\x80\x87";
  special_char_strings_[SpecialChar::kBottomButton] = "\xee\x80\x88";
  special_char_strings_[SpecialChar::kDelete] = "\xee\x80\x89";
  special_char_strings_[SpecialChar::kShift] = "\xee\x80\x8A";
  special_char_strings_[SpecialChar::kBack] = "\xee\x80\x8B";
  special_char_strings_[SpecialChar::kLogoFlat] = "\xee\x80\x8C";
  special_char_strings_[SpecialChar::kRewindButton] = "\xee\x80\x8D";
  special_char_strings_[SpecialChar::kPlayPauseButton] = "\xee\x80\x8E";
  special_char_strings_[SpecialChar::kFastForwardButton] = "\xee\x80\x8F";
  special_char_strings_[SpecialChar::kDpadCenterButton] = "\xee\x80\x90";

  special_char_strings_[SpecialChar::kOuyaButtonO] = "\xee\x80\x99";
  special_char_strings_[SpecialChar::kOuyaButtonU] = "\xee\x80\x9A";
  special_char_strings_[SpecialChar::kOuyaButtonY] = "\xee\x80\x9B";
  special_char_strings_[SpecialChar::kOuyaButtonA] = "\xee\x80\x9C";
  special_char_strings_[SpecialChar::kOuyaLogo] = "\xee\x80\x9D";
  special_char_strings_[SpecialChar::kLogo] = "\xee\x80\x9E";
  special_char_strings_[SpecialChar::kTicket] = "\xee\x80\x9F";
  special_char_strings_[SpecialChar::kGooglePlayGamesLogo] = "\xee\x80\xA0";
  special_char_strings_[SpecialChar::kGameCenterLogo] = "\xee\x80\xA1";
  special_char_strings_[SpecialChar::kDiceButton1] = "\xee\x80\xA2";
  special_char_strings_[SpecialChar::kDiceButton2] = "\xee\x80\xA3";
  special_char_strings_[SpecialChar::kDiceButton3] = "\xee\x80\xA4";
  special_char_strings_[SpecialChar::kDiceButton4] = "\xee\x80\xA5";
  special_char_strings_[SpecialChar::kGameCircleLogo] = "\xee\x80\xA6";
  special_char_strings_[SpecialChar::kPartyIcon] = "\xee\x80\xA7";
  special_char_strings_[SpecialChar::kTestAccount] = "\xee\x80\xA8";
  special_char_strings_[SpecialChar::kTicketBacking] = "\xee\x80\xA9";
  special_char_strings_[SpecialChar::kTrophy1] = "\xee\x80\xAA";
  special_char_strings_[SpecialChar::kTrophy2] = "\xee\x80\xAB";
  special_char_strings_[SpecialChar::kTrophy3] = "\xee\x80\xAC";
  special_char_strings_[SpecialChar::kTrophy0a] = "\xee\x80\xAD";
  special_char_strings_[SpecialChar::kTrophy0b] = "\xee\x80\xAE";
  special_char_strings_[SpecialChar::kTrophy4] = "\xee\x80\xAF";
  special_char_strings_[SpecialChar::kLocalAccount] = "\xee\x80\xB0";
  special_char_strings_[SpecialChar::kAlibabaLogo] = "\xee\x80\xB1";

  special_char_strings_[SpecialChar::kFlagUnitedStates] = "\xee\x80\xB2";
  special_char_strings_[SpecialChar::kFlagMexico] = "\xee\x80\xB3";
  special_char_strings_[SpecialChar::kFlagGermany] = "\xee\x80\xB4";
  special_char_strings_[SpecialChar::kFlagBrazil] = "\xee\x80\xB5";
  special_char_strings_[SpecialChar::kFlagRussia] = "\xee\x80\xB6";
  special_char_strings_[SpecialChar::kFlagChina] = "\xee\x80\xB7";
  special_char_strings_[SpecialChar::kFlagUnitedKingdom] = "\xee\x80\xB8";
  special_char_strings_[SpecialChar::kFlagCanada] = "\xee\x80\xB9";
  special_char_strings_[SpecialChar::kFlagIndia] = "\xee\x80\xBA";
  special_char_strings_[SpecialChar::kFlagJapan] = "\xee\x80\xBB";
  special_char_strings_[SpecialChar::kFlagFrance] = "\xee\x80\xBC";
  special_char_strings_[SpecialChar::kFlagIndonesia] = "\xee\x80\xBD";
  special_char_strings_[SpecialChar::kFlagItaly] = "\xee\x80\xBE";
  special_char_strings_[SpecialChar::kFlagSouthKorea] = "\xee\x80\xBF";
  special_char_strings_[SpecialChar::kFlagNetherlands] = "\xee\x81\x80";

  special_char_strings_[SpecialChar::kFedora] = "\xee\x81\x81";
  special_char_strings_[SpecialChar::kHal] = "\xee\x81\x82";
  special_char_strings_[SpecialChar::kCrown] = "\xee\x81\x83";
  special_char_strings_[SpecialChar::kYinYang] = "\xee\x81\x84";
  special_char_strings_[SpecialChar::kEyeBall] = "\xee\x81\x85";
  special_char_strings_[SpecialChar::kSkull] = "\xee\x81\x86";
  special_char_strings_[SpecialChar::kHeart] = "\xee\x81\x87";
  special_char_strings_[SpecialChar::kDragon] = "\xee\x81\x88";
  special_char_strings_[SpecialChar::kHelmet] = "\xee\x81\x89";
  special_char_strings_[SpecialChar::kMushroom] = "\xee\x81\x8A";

  special_char_strings_[SpecialChar::kNinjaStar] = "\xee\x81\x8B";
  special_char_strings_[SpecialChar::kVikingHelmet] = "\xee\x81\x8C";
  special_char_strings_[SpecialChar::kMoon] = "\xee\x81\x8D";
  special_char_strings_[SpecialChar::kSpider] = "\xee\x81\x8E";
  special_char_strings_[SpecialChar::kFireball] = "\xee\x81\x8F";

  special_char_strings_[SpecialChar::kFlagUnitedArabEmirates] = "\xee\x81\x90";
  special_char_strings_[SpecialChar::kFlagQatar] = "\xee\x81\x91";
  special_char_strings_[SpecialChar::kFlagEgypt] = "\xee\x81\x92";
  special_char_strings_[SpecialChar::kFlagKuwait] = "\xee\x81\x93";
  special_char_strings_[SpecialChar::kFlagAlgeria] = "\xee\x81\x94";
  special_char_strings_[SpecialChar::kFlagSaudiArabia] = "\xee\x81\x95";
  special_char_strings_[SpecialChar::kFlagMalaysia] = "\xee\x81\x96";
  special_char_strings_[SpecialChar::kFlagCzechRepublic] = "\xee\x81\x97";
  special_char_strings_[SpecialChar::kFlagAustralia] = "\xee\x81\x98";
  special_char_strings_[SpecialChar::kFlagSingapore] = "\xee\x81\x99";

  special_char_strings_[SpecialChar::kOculusLogo] = "\xee\x81\x9A";
  special_char_strings_[SpecialChar::kSteamLogo] = "\xee\x81\x9B";
  special_char_strings_[SpecialChar::kNvidiaLogo] = "\xee\x81\x9C";

  special_char_strings_[SpecialChar::kFlagIran] = "\xee\x81\x9D";
  special_char_strings_[SpecialChar::kFlagPoland] = "\xee\x81\x9E";
  special_char_strings_[SpecialChar::kFlagArgentina] = "\xee\x81\x9F";
  special_char_strings_[SpecialChar::kFlagPhilippines] = "\xee\x81\xA0";
  special_char_strings_[SpecialChar::kFlagChile] = "\xee\x81\xA1";

  special_char_strings_[SpecialChar::kMikirog] = "\xee\x81\xA2";
  special_char_strings_[SpecialChar::kV2Logo] = "\xee\x81\xA3";
}

void Game::SetGameRoster(cJSON* r) {
  if (game_roster_ != nullptr) {
    cJSON_Delete(game_roster_);
  }
  game_roster_ = r;
}

void Game::ResetActivityTracking() {
  largest_draw_time_increment_since_last_reset_ = 0;
  first_draw_real_time_ = last_draw_real_time_ = g_platform->GetTicks();
}

#if BA_VR_BUILD

void Game::PushVRHandsState(const VRHandsState& state) {
  thread()->PushCall([this, state] { vr_hands_state_ = state; });
}

#endif  // BA_VR_BUILD

void Game::PushMediaPruneCall(int level) {
  thread()->PushCall([level] {
    assert(InLogicThread());
    g_assets->Prune(level);
  });
}

void Game::PushSetV1LoginCall(V1AccountType account_type,
                              V1LoginState account_state,
                              const std::string& account_name,
                              const std::string& account_id) {
  thread()->PushCall(
      [this, account_type, account_state, account_name, account_id] {
        g_v1_account->SetLogin(account_type, account_state, account_name,
                               account_id);
      });
}

void Game::PushInitialScreenCreatedCall() {
  thread()->PushCall([this] { InitialScreenCreated(); });
}

void Game::InitialScreenCreated() {
  assert(InLogicThread());

  // Ok; graphics-server is telling us we've got a screen.

  // We can now let the media thread go to town pre-loading system media
  // while we wait.
  g_assets->LoadSystemAssets();

  // FIXME: ideally we should create this as part of bootstrapping, but
  // we need it to be possible to load textures/etc. before the renderer
  // exists.
  if (!HeadlessMode()) {
    assert(!g_app->console);
    g_app->console = new Console();
  }

  // Set up our timers.
  process_timer_ =
      thread()->NewTimer(0, true, NewLambdaRunnable([this] { Process(); }));
  media_prune_timer_ = thread()->NewTimer(
      2345, true, NewLambdaRunnable([this] { PruneMedia(); }));

  // Normally we schedule updates when we're asked to draw a frame.
  // In headless mode, however, we're not drawing, so we need a dedicated
  // timer to take its place.
  if (HeadlessMode()) {
    headless_update_timer_ =
        thread()->NewTimer(8, true, NewLambdaRunnable([this] { Update(); }));
  }

  RunAppLaunchCommands();
}

void Game::PruneMedia() { g_assets->Prune(); }

// Launch into main menu or whatever else.
void Game::RunAppLaunchCommands() {
  assert(InLogicThread());
  assert(!ran_app_launch_commands_);

  // First off, run our python app-launch call.
  {
    // Run this in the UI context.
    ScopedSetContext cp(GetUIContext());
    g_python->obj(Python::ObjID::kFinishBootstrappingCall).Call();
  }
  ran_app_launch_commands_ = true;

  // If we were passed launch command args, run them.
  if (!g_app->exec_command.empty()) {
    bool success = PythonCommand(g_app->exec_command, BA_BCFN).Run();
    if (!success) {
      exit(1);
    }
  }

  // If the stuff we just ran didn't result in a session, create a default one.
  if (!foreground_session_.exists()) {
    RunMainMenu();
  }

  UpdateProcessTimer();
}

// Set up our sleeping based on what we're doing.
void Game::UpdateProcessTimer() {
  assert(InLogicThread());

  // This might get called before we set up our timer in some cases. (such as
  // very early) should be safe to ignore since we update the interval
  // explicitly after creating the timers.
  if (!process_timer_) {
    return;
  }

  // If there's loading to do, keep at it rather vigorously.
  if (have_pending_loads_) {
    assert(process_timer_);
    process_timer_->SetLength(1);
  } else {
    // Otherwise we've got nothing to do; go to sleep until something changes.
    assert(process_timer_);
    process_timer_->SetLength(-1);
  }
}

void Game::PruneSessions() {
  bool have_dead_session = false;
  for (auto&& i : sessions_) {
    if (i.exists()) {
      // If this session is no longer foreground and is ready to die, kill it.
      if (i.exists() && i.get() != foreground_session_.get()) {
        try {
          i.Clear();
        } catch (const std::exception& e) {
          Log("Exception killing Session: " + std::string(e.what()));
        }
        have_dead_session = true;
      }
    } else {
      have_dead_session = true;
    }
  }
  if (have_dead_session) {
    std::vector<Object::Ref<Session> > live_list;
    for (auto&& i : sessions_) {
      if (i.exists()) {
        live_list.push_back(i);
      }
    }
    sessions_.swap(live_list);
  }
}

void Game::UpdateKickVote() {
  if (!kick_vote_in_progress_) {
    return;
  }
  ConnectionToClient* kick_vote_starter = kick_vote_starter_.get();
  ConnectionToClient* kick_vote_target = kick_vote_target_.get();

  // If the target is no longer with us, silently end.
  if (kick_vote_target == nullptr) {
    kick_vote_in_progress_ = false;
    return;
  }
  millisecs_t current_time{GetRealTime()};
  int total_client_count = 0;
  int yes_votes = 0;
  int no_votes = 0;

  // Tally current votes for connected clients; if anything has changed, print
  // the update and possibly perform the kick.
  for (ConnectionToClient* client : connections()->GetConnectionsToClients()) {
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

    // Disallow kicking for a while for everyone.. but ESPECIALLY so for the guy
    // who launched the failed vote.
    for (ConnectionToClient* client :
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
        votes_required = HeadlessMode() ? 2 : 3;
        break;
      case 4:
        votes_required = 3;
        break;
      case 5:
        votes_required = HeadlessMode() ? 3 : 4;
        break;
      case 6:
        votes_required = 4;
        break;
      case 7:
        votes_required = HeadlessMode() ? 4 : 5;
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
      connections_->DisconnectClient(kick_vote_target->id(), kKickBanSeconds);

    } else if (votes_needed != last_kick_votes_needed_) {
      last_kick_votes_needed_ = votes_needed;
      connections()->SendScreenMessageToClients(
          R"({"r":"votesNeededText","s":[["${NUMBER}",")"
              + std::to_string(votes_needed) + "\"]]}",
          1, 1, 0);
    }
  }
}

void Game::HandleQuitOnIdle() {
  if (idle_exit_minutes_) {
    float idle_seconds{g_input->input_idle_time() * 0.001f};
    if (!idle_exiting_ && idle_seconds > (idle_exit_minutes_.value() * 60.0f)) {
      idle_exiting_ = true;

      thread()->PushCall([this, idle_seconds] {
        assert(InLogicThread());

        // Just go through _ba.quit()
        // FIXME: Shouldn't need to go out to the python layer here...
        g_python->obj(Python::ObjID::kQuitCall).Call();
      });
    }
  }
}

// Bring our scenes, real-time timers, etc up to date.
void Game::Update() {
  auto startms{Platform::GetCurrentMilliseconds()};
  assert(InLogicThread());
  millisecs_t real_time = GetRealTime();
  g_platform->SetDebugKey("LastUpdateTime", std::to_string(startms));
  if (first_update_) {
    master_time_offset_ = master_time_ - real_time;
    first_update_ = false;
  }
  in_update_ = true;
  g_input->Update();
  UpdateKickVote();

  HandleQuitOnIdle();

  // Send the game roster to our clients if it's changed recently.
  if (game_roster_dirty_) {
    if (real_time > last_game_roster_send_time_ + 2500) {
      // Now send it to all connected clients.
      std::vector<uint8_t> msg = GetGameRosterMessage();
      for (auto&& c : connections()->GetConnectionsToClients()) {
        c->SendReliableMessage(msg);
      }
      game_roster_dirty_ = false;
      last_game_roster_send_time_ = real_time;
    }
  }

  connections_->Update();

  // Ok, here's the deal:
  // This is where we regulate the speed of everything that's running under us
  // (sessions, activities, frame_def-creation, etc)
  // we have a master_time which we try to have match real-time as closely
  // as possible (unless we physically aren't fast enough to get everything
  // done, in which case it'll be slower). We also increment our underlying
  // machinery in 8ms increments (1/120 of a second) and try to do 2 updates
  // each time we're called, since we're usually being called in a 60hz refresh
  // cycle and that'll line our draws up perfectly with our sim steps.

  // TODO(ericf): On modern systems (VR and otherwise) we'll see 80hz, 90hz,
  //  120hz, 240hz, etc. It would be great to generalize this to gravitate
  //  towards clean step patterns in all cases, not just the 60hz and 90hz
  //  cases we handle now. In general we want stuff like 1,1,2,1,1,2,1,1,2,
  //  not 1,1,1,2,1,2,2,1,1.

  // Figure out where our net-time *should* be getting to to match real-time.
  millisecs_t target_master_time = real_time + master_time_offset_;
  millisecs_t amount_behind = target_master_time - master_time_;

  // Normally we assume 60hz so we gravitate towards 2 steps per update to line
  // up with our 120hz update timing.
  int target_steps = 2;

#if BA_RIFT_BUILD
  // On Rift VR mode we're running 90hz, so lets aim for 1/2/1/2 steps to hit
  // our 120hz target.
  if (IsVRMode()) {
    target_steps = rift_step_index_ + 1;
    rift_step_index_ = !rift_step_index_;
  }
#endif  // BA_RIFT_BUILD

  // Ideally we should be behind by 16 (or 8 for single steps); if its
  // *slightly* more than that, let our timing slip a tiny bit to maintain sync.
  // This lets us match framerates that are a tiny bit slower than 60hz, such as
  // seems to be the case with the Gear VR.
  if (amount_behind > 16) {
    master_time_offset_ -= 1;

    //.. and recalc these..
    target_master_time = real_time + master_time_offset_;
    amount_behind = target_master_time - master_time_;
  }

  // if we've fallen behind by a lot, just cut our losses
  if (amount_behind > 50) {
    master_time_offset_ -= (amount_behind - 50);
    target_master_time = real_time + master_time_offset_;
  }

  // min/max net-time targets we can aim for; gives us about a steps worth of
  // wiggle room to try and keep our exact target cadence
  millisecs_t min_target_master_time =
      target_master_time >= 8 ? (target_master_time - 8) : 0;
  millisecs_t max_target_master_time = target_master_time + 8;

  // run up our real-time timers
  realtimers_->Run(real_time);

  // Run session updates until we catch up with projected base time (or run out
  // of time).
  int step = 1;

  while (true) {
    // Try to stick to our target step count whenever possible, but if we get
    // too far off target we may need to bail earlier/later.
    if (step > target_steps) {
      // As long as we're within a step of where we should be, bail now.
      if (master_time_ >= min_target_master_time) break;
    } else {
      // If we've gone too far already, bail.
      if (master_time_ >= max_target_master_time) {
        // Log("BAILING EARLY");
        // On rift if this is a 2-step and we bailed after 1, aim for 2 again
        // next time (otherwise we'll always get 3 singles in a row when this
        // happens).
#if BA_RIFT_BUILD
        if (IsVRMode() && target_steps == 2 && step == 2) {
          rift_step_index_ = !rift_step_index_;
        }
#endif  // BA_RIFT_BUILD
        break;
      }
    }

    // Update our UI scene/etc.
    g_ui->Update(8);

    // Update all of our sessions.
    for (auto&& i : sessions_) {
      assert(i.exists());
      i->Update(8);
    }

    last_session_update_master_time_ = master_time_;

    // Go ahead and prune dead ones.
    PruneSessions();

    // Advance master time..
    master_time_ += 8;

    // Bail if we spend too much time in here.
    millisecs_t new_real_time = GetRealTime();
    if (new_real_time - real_time > 30) {
      break;
    }
    step++;
  }
  in_update_ = false;

  // Report excessively long updates.
  if (g_app->debug_timing && real_time >= next_long_update_report_time_) {
    auto duration{Platform::GetCurrentMilliseconds() - startms};

    // Complain when our full update takes longer than 1/60th second.
    if (duration > (1000 / 60)) {
      Log("Game update took too long (" + std::to_string(duration) + " ms).",
          true, false);

      // Limit these if we want (not doing so for now).
      next_long_update_report_time_ = real_time;
    }
  }
}

// Reset the game to a blank slate.
void Game::Reset() {
  assert(InLogicThread());

  // Tear down any existing setup.
  // This should allow high-level objects to die gracefully.
  assert(g_python->inited());

  // Tear down our existing session.
  foreground_session_.Clear();
  PruneSessions();

  // If all is well our sessions should all be dead.
  if (g_app->session_count != 0) {
    Log("Error: session-count is non-zero ("
        + std::to_string(g_app->session_count) + ") on Game::Reset.");
  }

  // Note: we don't clear real-time timers anymore. Should we?..
  g_ui->Reset();
  g_input->Reset();
  g_graphics->Reset();
  g_python->Reset();
  g_audio->Reset();

  if (!HeadlessMode()) {
    // If we haven't, send a first frame_def to the graphics thread to kick
    // things off (it'll start sending us requests for more after it gets the
    // first).
    if (!have_sent_initial_frame_def_) {
      g_graphics->BuildAndPushFrameDef();
      have_sent_initial_frame_def_ = true;
    }
  }
}

auto Game::IsInUIContext() const -> bool {
  return (g_ui && Context::current().target.get() == g_ui);
}

void Game::PushShowURLCall(const std::string& url) {
  thread()->PushCall([url] {
    assert(InLogicThread());
    assert(g_python);
    g_python->ShowURL(url);
  });
}

auto Game::GetForegroundContext() -> Context {
  Session* s = GetForegroundSession();
  if (s) {
    return s->GetForegroundContext();
  } else {
    return Context();
  }
}

void Game::PushBackButtonCall(InputDevice* input_device) {
  thread()->PushCall([this, input_device] {
    assert(InLogicThread());

    // Ignore if UI isn't up yet.
    if (!g_ui || !g_ui->overlay_root_widget() || !g_ui->screen_root_widget()) {
      return;
    }

    // If there's a UI up, send along a cancel message.
    if (g_ui->overlay_root_widget()->GetChildCount() != 0
        || g_ui->screen_root_widget()->GetChildCount() != 0) {
      g_ui->root_widget()->HandleMessage(
          WidgetMessage(WidgetMessage::Type::kCancel));
    } else {
      // If there's no main screen or overlay windows, ask for a menu owned by
      // this device.
      MainMenuPress(input_device);
    }
  });
}

void Game::PushStringEditSetCall(const std::string& value) {
  thread()->PushCall([value] {
    if (!g_ui) {
      Log("Error: No ui on StringEditSetEvent.");
      return;
    }
#if BA_OSTYPE_ANDROID
    TextWidget* w = TextWidget::GetAndroidStringEditWidget();
    if (w) {
      w->SetText(value);
    }
#else
    throw Exception();  // Shouldn't get here.
#endif
  });
}

void Game::PushStringEditCancelCall() {
  thread()->PushCall([] {
    if (!g_ui) {
      Log("Error: No ui in PushStringEditCancelCall.");
      return;
    }
  });
}

// Called by a newly made Session instance to set itself as the current
// session.
void Game::SetForegroundSession(Session* s) {
  assert(InLogicThread());
  foreground_session_ = s;
}

void Game::SetForegroundScene(Scene* sg) {
  assert(InLogicThread());
  if (foreground_scene_.get() != sg) {
    foreground_scene_ = sg;

    // If this scene has a globals-node, put it in charge of stuff.
    if (GlobalsNode* g = sg->globals_node()) {
      g->SetAsForeground();
    }
  }
}

void Game::LaunchClientSession() {
  if (in_update_) {
    throw Exception(
        "can't launch a session from within a session update; use "
        "ba.pushcall()");
  }
  assert(InLogicThread());

  // Don't want to pick up any old stuff in here.
  ScopedSetContext cp(nullptr);

  // This should kill any current session and get us back to a blank slate.
  Reset();

  // Create the new session.
  Object::WeakRef<Session> old_foreground_session(foreground_session_);
  try {
    auto s(Object::New<Session, NetClientSession>());
    sessions_.push_back(s);

    // It should have set itself as FG.
    assert(foreground_session_ == s);
  } catch (const std::exception& e) {
    // If it failed, restore the previous current session and re-throw.
    SetForegroundSession(old_foreground_session.get());
    throw Exception(std::string("HostSession failed: ") + e.what());
  }
}

void Game::LaunchReplaySession(const std::string& file_name) {
  if (in_update_)
    throw Exception(
        "can't launch a session from within a session update; use "
        "ba.pushcall()");

  assert(InLogicThread());

  // Don't want to pick up any old stuff in here.
  ScopedSetContext cp(nullptr);

  // This should kill any current session and get us back to a blank slate.
  Reset();

  // Create the new session.
  Object::WeakRef<Session> old_foreground_session(foreground_session_);
  try {
    auto s(Object::New<Session, ReplayClientSession>(file_name));
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

void Game::LaunchHostSession(PyObject* session_type_obj,
                             BenchmarkType benchmark_type) {
  if (in_update_) {
    throw Exception(
        "can't call host_session() from within session update; use "
        "ba.pushcall()");
  }

  assert(InLogicThread());

  connections_->PrepareForLaunchHostSession();

  // Don't want to pick up any old stuff in here.
  ScopedSetContext cp(nullptr);

  // This should kill any current session and get us back to a blank slate.
  Reset();

  Object::WeakRef<Session> old_foreground_session(foreground_session_);
  try {
    // Create the new session.
    auto s(Object::New<HostSession>(session_type_obj));
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

void Game::RunMainMenu() {
  assert(InLogicThread());
  if (g_app->shutting_down) {
    return;
  }
  assert(g_python);
  assert(InLogicThread());
  PythonRef result =
      g_python->obj(Python::ObjID::kLaunchMainMenuSessionCall).Call();
  if (!result.exists()) {
    throw Exception("error running main menu");
  }
}

// Commands run via the in-game console. These are a bit more 'casual' and run
// in the current visible context.

void Game::PushInGameConsoleScriptCommand(const std::string& command) {
  thread()->PushCall([this, command] {
    // These are always run in whichever context is 'visible'.
    ScopedSetContext cp(GetForegroundContext());
    PythonCommand cmd(command, "<in-game-console>");
    if (!g_app->user_ran_commands) {
      g_app->user_ran_commands = true;
    }
    if (cmd.CanEval()) {
      PyObject* obj = cmd.RunReturnObj(true, nullptr);
      if (obj && obj != Py_None) {
        PyObject* s = PyObject_Repr(obj);
        if (s) {
          const char* c = PyUnicode_AsUTF8(s);
          if (g_app->console) {
            g_app->console->Print(std::string(c) + "\n");
          }
          Py_DECREF(s);
        }
        Py_DECREF(obj);
      }
    } else {
      // Not eval-able; just run it.
      cmd.Run();
    }
  });
}

// Commands run via stdin.
void Game::PushStdinScriptCommand(const std::string& command) {
  thread()->PushCall([this, command] {
    // These are always run in whichever context is 'visible'.
    ScopedSetContext cp(GetForegroundContext());
    PythonCommand cmd(command, "<stdin>");
    if (!g_app->user_ran_commands) {
      g_app->user_ran_commands = true;
    }

    // Eval this if possible (so we can possibly print return value).
    if (cmd.CanEval()) {
      if (PyObject* obj = cmd.RunReturnObj(true, nullptr)) {
        // Print the value if we're running directly from a terminal
        // (or being run under the server-manager)
        if ((g_platform->is_stdin_a_terminal()
             || g_app_flavor->server_wrapper_managed())
            && obj != Py_None) {
          PyObject* s = PyObject_Repr(obj);
          if (s) {
            const char* c = PyUnicode_AsUTF8(s);
            printf("%s\n", c);
            fflush(stdout);
            Py_DECREF(s);
          }
        }
        Py_DECREF(obj);
      }
    } else {
      // Can't eval it; just run it.
      cmd.Run();
    }
  });
}

void Game::PushInterruptSignalCall() {
  thread()->PushCall([this] {
    assert(InLogicThread());

    // Special case; when running under the server-wrapper, we completely
    // ignore interrupt signals (the wrapper acts on them).
    if (g_app_flavor->server_wrapper_managed()) {
      return;
    }

    // FIXME: Shouldn't need to go out to the Python layer here...
    g_python->obj(Python::ObjID::kQuitCall).Call();
  });
}

void Game::PushAskUserForTelnetAccessCall() {
  thread()->PushCall([this] {
    assert(InLogicThread());
    ScopedSetContext cp(GetUIContext());
    g_python->obj(Python::ObjID::kTelnetAccessRequestCall).Call();
  });
}

void Game::PushPythonCall(const Object::Ref<PythonContextCall>& call) {
  // Since we're mucking with refs, need to limit to game thread.
  BA_PRECONDITION(InLogicThread());
  BA_PRECONDITION(call->object_strong_ref_count() > 0);
  thread()->PushCall([call] {
    assert(call.exists());
    call->Run();
  });
}

void Game::PushPythonCallArgs(const Object::Ref<PythonContextCall>& call,
                              const PythonRef& args) {
  // Since we're mucking with refs, need to limit to game thread.
  BA_PRECONDITION(InLogicThread());
  BA_PRECONDITION(call->object_strong_ref_count() > 0);
  thread()->PushCall([call, args] {
    assert(call.exists());
    call->Run(args.get());
  });
}

void Game::PushPythonWeakCall(const Object::WeakRef<PythonContextCall>& call) {
  // Since we're mucking with refs, need to limit to game thread.
  BA_PRECONDITION(InLogicThread());

  // Even though we only hold a weak ref, we expect a valid strong-reffed
  // object to be passed in.
  assert(call.exists() && call->object_strong_ref_count() > 0);

  thread()->PushCall([call] {
    if (call.exists()) {
      Python::ScopedCallLabel label("PythonWeakCallMessage");
      call->Run();
    }
  });
}

void Game::PushPythonWeakCallArgs(
    const Object::WeakRef<PythonContextCall>& call, const PythonRef& args) {
  // Since we're mucking with refs, need to limit to game thread.
  BA_PRECONDITION(InLogicThread());

  // Even though we only hold a weak ref, we expect a valid strong-reffed
  // object to be passed in.
  assert(call.exists() && call->object_strong_ref_count() > 0);

  thread()->PushCall([call, args] {
    if (call.exists()) call->Run(args.get());
  });
}

void Game::PushPythonRawCallable(PyObject* callable) {
  thread()->PushCall([this, callable] {
    assert(InLogicThread());

    // Lets run this in the UI context.
    // (can add other options if we need later)
    ScopedSetContext cp(GetUIContext());

    // This event contains a raw python obj with an incremented ref-count.
    auto call(Object::New<PythonContextCall>(callable));
    Py_DECREF(callable);  // now just held by call

    call->Run();
  });
}

void Game::PushScreenMessage(const std::string& message,
                             const Vector3f& color) {
  thread()->PushCall(
      [message, color] { g_graphics->AddScreenMessage(message, color); });
}

void Game::SetReplaySpeedExponent(int val) {
  replay_speed_exponent_ = std::min(3, std::max(-3, val));
  replay_speed_mult_ = powf(2.0f, static_cast<float>(replay_speed_exponent_));
}

void Game::SetDebugSpeedExponent(int val) {
  debug_speed_exponent_ = val;
  debug_speed_mult_ = powf(2.0f, static_cast<float>(debug_speed_exponent_));

  Session* s = GetForegroundSession();
  if (s) s->DebugSpeedMultChanged();
}

void Game::ChangeGameSpeed(int offs) {
  assert(InLogicThread());

  // If we're in a replay session, adjust playback speed there.
  if (dynamic_cast<ReplayClientSession*>(GetForegroundSession())) {
    int old_speed = replay_speed_exponent();
    SetReplaySpeedExponent(replay_speed_exponent() + offs);
    if (old_speed != replay_speed_exponent()) {
      ScreenMessage(
          "{\"r\":\"watchWindow.playbackSpeedText\","
          "\"s\":[[\"${SPEED}\",\""
          + std::to_string(replay_speed_mult()) + "\"]]}");
    }
    return;
  }
  // Otherwise, in debug build, we allow speeding/slowing anything.
  if (g_buildconfig.debug_build()) {
    debug_speed_exponent_ += offs;
    debug_speed_mult_ = powf(2.0f, static_cast<float>(debug_speed_exponent_));
    ScreenMessage("DEBUG GAME SPEED TO " + std::to_string(debug_speed_mult_));
    Session* s = GetForegroundSession();
    if (s) {
      s->DebugSpeedMultChanged();
    }
  }
}

auto Game::GetUIContext() const -> Context {
  return Context(GetUIContextTarget());
}

void Game::PushToggleManualCameraCall() {
  thread()->PushCall([] { g_graphics->ToggleManualCamera(); });
}

void Game::PushToggleDebugInfoDisplayCall() {
  thread()->PushCall([] { g_graphics->ToggleNetworkDebugDisplay(); });
}

void Game::PushToggleCollisionGeometryDisplayCall() {
  thread()->PushCall([] { g_graphics->ToggleDebugDraw(); });
}

void Game::PushMainMenuPressCall(InputDevice* device) {
  thread()->PushCall([this, device] { MainMenuPress(device); });
}

void Game::MainMenuPress(InputDevice* device) {
  assert(InLogicThread());
  g_python->HandleDeviceMenuPress(device);
}

void Game::PushScreenResizeCall(float virtual_width, float virtual_height,
                                float pixel_width, float pixel_height) {
  thread()->PushCall([=] {
    ScreenResize(virtual_width, virtual_height, pixel_width, pixel_height);
  });
}

void Game::ScreenResize(float virtual_width, float virtual_height,
                        float pixel_width, float pixel_height) {
  assert(InLogicThread());
  assert(g_graphics != nullptr);
  if (g_graphics) {
    g_graphics->ScreenResize(virtual_width, virtual_height, pixel_width,
                             pixel_height);
  }
  if (g_ui) {
    g_ui->ScreenSizeChanged();
  }
  if (Session* session = GetForegroundSession()) {
    session->ScreenSizeChanged();
  }
}

void Game::PushGameServiceAchievementListCall(
    const std::set<std::string>& achievements) {
  thread()->PushCall(
      [this, achievements] { GameServiceAchievementList(achievements); });
}

void Game::GameServiceAchievementList(
    const std::set<std::string>& achievements) {
  assert(g_python);
  assert(InLogicThread());
  g_app_internal->DispatchRemoteAchievementList(achievements);
}

void Game::PushPlaySoundCall(SystemSoundID sound) {
  thread()->PushCall(
      [sound] { g_audio->PlaySound(g_assets->GetSound(sound)); });
}

void Game::PushFriendScoreSetCall(const FriendScoreSet& score_set) {
  thread()->PushCall(
      [score_set] { g_python->HandleFriendScoresCB(score_set); });
}

void Game::PushConfirmQuitCall() {
  thread()->PushCall([this] {
    assert(InLogicThread());
    if (HeadlessMode()) {
      Log("PushConfirmQuitCall() unhandled on headless.");
    } else {
      // If input is locked, just quit immediately.. a confirm screen wouldn't
      // work anyway
      if (g_input->IsInputLocked()
          || (g_app->console != nullptr && g_app->console->active())) {
        // Just go through _ba.quit()
        // FIXME: Shouldn't need to go out to the python layer here...
        g_python->obj(Python::ObjID::kQuitCall).Call();
        return;
      } else {
        // this needs to be run in the UI context
        ScopedSetContext cp(GetUIContextTarget());

        g_audio->PlaySound(g_assets->GetSound(SystemSoundID::kSwish));
        g_python->obj(Python::ObjID::kQuitWindowCall).Call();

        // if we have a keyboard, give it UI ownership
        InputDevice* keyboard = g_input->keyboard_input();
        if (keyboard) {
          g_ui->SetUIInputDevice(keyboard);
        }
      }
    }
  });
}

void Game::Draw() {
  g_graphics->BuildAndPushFrameDef();

  // Now bring the game up to date.
  // By doing this *after* shipping a new frame-def we're reducing the
  // chance of frame drops at the expense of adding a bit of visual latency.
  // Could maybe try to be smart about which to do first, but not sure
  // if its worth it.
  Update();

  // Update our cheat tests.
  millisecs_t now = g_platform->GetTicks();
  millisecs_t elapsed = now - last_draw_real_time_;
  if (elapsed > largest_draw_time_increment_since_last_reset_) {
    largest_draw_time_increment_since_last_reset_ = elapsed;
  }
  last_draw_real_time_ = now;

  // Sanity test: can make sure our scene is taking exactly 2 steps
  // per frame here.. (should generally be the case on 60hz devices).
  if (explicit_bool(false)) {
    static int64_t last_step = 0;
    HostActivity* ha = GetForegroundContext().GetHostActivity();
    if (ha) {
      int64_t step = ha->scene()->stepnum();
      Log(std::to_string(step - last_step));
      last_step = step;
    }
  }
}

void Game::PushFrameDefRequest() {
  thread()->PushCall([this] { Draw(); });
}

void Game::PushOnAppResumeCall() {
  thread()->PushCall([] {
    // Wipe out whatever input device was in control of the UI.
    assert(g_ui);
    g_ui->SetUIInputDevice(nullptr);
  });
}

// Look through everything in our config dict and act on it.
void Game::ApplyConfig() {
  assert(InLogicThread());

  // Not relevant for fullscreen anymore
  // since we're fullscreen windows everywhere.
  int width = 800;
  int height = 600;

  // Texture quality.
  TextureQuality texture_quality_requested;
  std::string texqualstr =
      g_app_config->Resolve(AppConfig::StringID::kTextureQuality);

  if (texqualstr == "Auto") {
    texture_quality_requested = TextureQuality::kAuto;
  } else if (texqualstr == "High") {
    texture_quality_requested = TextureQuality::kHigh;
  } else if (texqualstr == "Medium") {
    texture_quality_requested = TextureQuality::kMedium;
  } else if (texqualstr == "Low") {
    texture_quality_requested = TextureQuality::kLow;
  } else {
    Log("Invalid texture quality: '" + texqualstr + "'; defaulting to low.");
    texture_quality_requested = TextureQuality::kLow;
  }

  // Graphics quality.
  std::string gqualstr =
      g_app_config->Resolve(AppConfig::StringID::kGraphicsQuality);
  GraphicsQuality graphics_quality_requested;

  if (gqualstr == "Auto") {
    graphics_quality_requested = GraphicsQuality::kAuto;
  } else if (gqualstr == "Higher") {
    graphics_quality_requested = GraphicsQuality::kHigher;
  } else if (gqualstr == "High") {
    graphics_quality_requested = GraphicsQuality::kHigh;
  } else if (gqualstr == "Medium") {
    graphics_quality_requested = GraphicsQuality::kMedium;
  } else if (gqualstr == "Low") {
    graphics_quality_requested = GraphicsQuality::kLow;
  } else {
    Log("Error: Invalid graphics quality: '" + gqualstr
        + "'; defaulting to auto.");
    graphics_quality_requested = GraphicsQuality::kAuto;
  }

  // Android res string.
  std::string android_res =
      g_app_config->Resolve(AppConfig::StringID::kResolutionAndroid);

  bool fullscreen = g_app_config->Resolve(AppConfig::BoolID::kFullscreen);

  // Note: when the graphics-thread applies the first set-screen event it will
  // trigger the remainder of startup such as media-loading; make sure nothing
  // below this will affect that.
  g_graphics_server->PushSetScreenCall(fullscreen, width, height,
                                       texture_quality_requested,
                                       graphics_quality_requested, android_res);

  // FIXME: The graphics server should kick this off *AFTER* it sets the actual
  //  quality values; here we're just sending along our requested values which
  //  is wrong. If there's a session up, inform it of the (potential) change.
  Session* session = GetForegroundSession();
  if (session) {
    session->GraphicsQualityChanged(graphics_quality_requested);
  }

  if (!HeadlessMode()) {
    g_app->remote_server_accepting_connections =
        g_app_config->Resolve(AppConfig::BoolID::kEnableRemoteApp);
  }

  chat_muted_ = g_app_config->Resolve(AppConfig::BoolID::kChatMuted);
  g_graphics->set_show_fps(g_app_config->Resolve(AppConfig::BoolID::kShowFPS));

  // Set tv border (for both client and server).
  // FIXME: this should exist either on the client or the server; not both.
  //  (and should be communicated via frameldefs/etc.)
  bool tv_border = g_app_config->Resolve(AppConfig::BoolID::kTVBorder);
  g_graphics_server->thread()->PushCall(
      [tv_border] { g_graphics_server->set_tv_border(tv_border); });
  g_graphics->set_tv_border(tv_border);

  g_graphics_server->PushSetScreenGammaCall(
      g_app_config->Resolve(AppConfig::FloatID::kScreenGamma));
  g_graphics_server->PushSetScreenPixelScaleCall(
      g_app_config->Resolve(AppConfig::FloatID::kScreenPixelScale));

  TextWidget::set_always_use_internal_keyboard(
      g_app_config->Resolve(AppConfig::BoolID::kAlwaysUseInternalKeyboard));

  // V-sync setting.
  std::string v_sync =
      g_app_config->Resolve(AppConfig::StringID::kVerticalSync);
  bool do_v_sync{};
  bool auto_v_sync{};
  if (v_sync == "Auto") {
    do_v_sync = true;
    auto_v_sync = true;
  } else if (v_sync == "Always") {
    do_v_sync = true;
    auto_v_sync = false;
  } else if (v_sync == "Never") {
    do_v_sync = false;
    auto_v_sync = false;
  } else {
    do_v_sync = false;
    auto_v_sync = false;
    Log("Error: Invalid 'Vertical Sync' value: '" + v_sync + "'");
  }
  g_graphics_server->PushSetVSyncCall(do_v_sync, auto_v_sync);

  g_audio->SetVolumes(g_app_config->Resolve(AppConfig::FloatID::kMusicVolume),
                      g_app_config->Resolve(AppConfig::FloatID::kSoundVolume));

  // Kick-idle-players setting (hmm is this still relevant?).
  auto* host_session = dynamic_cast<HostSession*>(foreground_session_.get());
  kick_idle_players_ =
      g_app_config->Resolve(AppConfig::BoolID::kKickIdlePlayers);
  if (host_session) {
    host_session->SetKickIdlePlayers(kick_idle_players_);
  }

  assert(g_input);
  g_input->ApplyAppConfig();

  // Set up network ports/states.
  int port = g_app_config->Resolve(AppConfig::IntID::kPort);
  int telnet_port = g_app_config->Resolve(AppConfig::IntID::kTelnetPort);

  // NOTE: Hard disabling telnet for now in headless builds;
  // it was being exploited to own servers.
  bool enable_telnet =
      g_buildconfig.headless_build()
          ? false
          : g_app_config->Resolve(AppConfig::BoolID::kEnableTelnet);
  std::string telnet_password =
      g_app_config->Resolve(AppConfig::StringID::kTelnetPassword);

  g_app_flavor->PushNetworkSetupCall(port, telnet_port, enable_telnet,
                                     telnet_password);

  bool disable_camera_shake =
      g_app_config->Resolve(AppConfig::BoolID::kDisableCameraShake);
  g_graphics->set_camera_shake_disabled(disable_camera_shake);

  bool disable_camera_gyro =
      g_app_config->Resolve(AppConfig::BoolID::kDisableCameraGyro);
  g_graphics->set_camera_gyro_explicitly_disabled(disable_camera_gyro);

  idle_exit_minutes_ =
      g_app_config->Resolve(AppConfig::OptionalFloatID::kIdleExitMinutes);

  // Any platform-specific settings.
  g_platform->ApplyConfig();
}

void Game::PushApplyConfigCall() {
  thread()->PushCall([this] { ApplyConfig(); });
}

void Game::PushRemoveGraphicsServerRenderHoldCall() {
  thread()->PushCall([] {
    // This call acts as a flush of sorts; when it goes through,
    // we push a call to the graphics server saying its ok for it
    // to start rendering again.  Thus any already-queued-up
    // frame_defs or whatnot will be ignored.
    g_graphics_server->PushRemoveRenderHoldCall();
  });
}

void Game::PushFreeAssetComponentRefsCall(
    const std::vector<Object::Ref<AssetComponentData>*>& components) {
  thread()->PushCall([components] {
    for (auto&& i : components) {
      delete i;
    }
  });
}

void Game::PushHavePendingLoadsDoneCall() {
  thread()->PushCall([] { g_assets->ClearPendingLoadsDoneList(); });
}

void Game::ToggleConsole() {
  assert(InLogicThread());
  if (auto console = g_app->console) {
    console->ToggleState();
  }
}

void Game::PushConsolePrintCall(const std::string& msg) {
  thread()->PushCall([msg] {
    // Send them to the console if its been created or store them
    // for when it is (unless we're headless in which case it never will).
    if (auto console = g_app->console) {
      console->Print(msg);
    } else if (!HeadlessMode()) {
      g_app->console_startup_messages += msg;
    }
  });
}

void Game::PushHavePendingLoadsCall() {
  thread()->PushCall([this] {
    have_pending_loads_ = true;
    UpdateProcessTimer();
  });
}

void Game::PushShutdownCall(bool soft) {
  thread()->PushCall([this, soft] { Shutdown(soft); });
}

void Game::Shutdown(bool soft) {
  assert(InLogicThread());

  if (!g_app->shutting_down) {
    g_app->shutting_down = true;

    // Nuke the app if we get stuck shutting down.
    Utils::StartSuicideTimer("shutdown", 10000);

    // Call our shutdown callback.
    g_python->obj(Python::ObjID::kShutdownCall).Call();

    connections_->Shutdown();

    // Let's do the same stuff we do when our thread is pausing. (committing
    // account-client to disk, etc).
    OnThreadPause();

    // Attempt to report/store outstanding log stuff.
    g_app_internal->PutLog(false);

    // Ideally we'd want to give some of the above stuff
    // a few seconds to complete, but just calling it done for now.
    g_app_flavor->PushShutdownCompleteCall();
  }
}

void Game::ResetInput() {
  assert(InLogicThread());
  g_input->ResetKeyboardHeldKeys();
  g_input->ResetJoyStickHeldButtons();
}

auto Game::RemovePlayer(Player* player) -> void {
  assert(InLogicThread());
  if (HostSession* host_session = player->GetHostSession()) {
    host_session->RemovePlayer(player);
  } else {
    Log("Got RemovePlayer call but have no host_session");
  }
}

auto Game::NewRealTimer(millisecs_t length, bool repeat,
                        const Object::Ref<Runnable>& runnable) -> int {
  int offset = 0;
  Timer* t = realtimers_->NewTimer(GetRealTime(), length, offset,
                                   repeat ? -1 : 0, runnable);
  return t->id();
}

void Game::DeleteRealTimer(int timer_id) { realtimers_->DeleteTimer(timer_id); }

void Game::SetRealTimerLength(int timer_id, millisecs_t length) {
  Timer* t = realtimers_->GetTimer(timer_id);
  if (t) {
    t->SetLength(length);
  } else {
    Log("Error: Game::SetRealTimerLength() called on nonexistent timer.");
  }
}

void Game::Process() {
  have_pending_loads_ = g_assets->RunPendingLoadsLogicThread();
  UpdateProcessTimer();
}

void Game::SetLanguageKeys(
    const std::unordered_map<std::string, std::string>& language) {
  assert(InLogicThread());
  {
    std::scoped_lock lock(language_mutex_);
    language_ = language;
  }

  // Let's also inform existing session stuff so it can update itself.
  if (Session* session = GetForegroundSession()) {
    session->LanguageChanged();
  }

  // As well as existing UI stuff.
  if (Widget* root_widget = g_ui->root_widget()) {
    root_widget->OnLanguageChange();
  }

  // Also clear translations on all screen-messages.
  g_graphics->ClearScreenMessageTranslations();
}

auto DoCompileResourceString(cJSON* obj) -> std::string {
  // NOTE: We currently talk to Python here so need to be sure
  // we're holding the GIL. Perhaps in the future we could handle this
  // stuff completely in C++ and be free of this limitation.
  assert(Python::HaveGIL());
  assert(obj != nullptr);

  std::string result;

  // If its got a "r" key, look it up as a resource.. (with optional fallback).
  cJSON* resource = cJSON_GetObjectItem(obj, "r");
  if (resource == nullptr) {
    resource = cJSON_GetObjectItem(obj, "resource");
    // As of build 14318, complain if we find long key names; hope to remove
    // them soon.
    if (resource != nullptr) {
      static bool printed = false;
      if (!printed) {
        printed = true;
        char* c = cJSON_Print(obj);
        BA_LOG_ONCE("found long key 'resource' in raw lstr json: "
                    + std::string(c));
        free(c);
      }
    }
  }
  if (resource != nullptr) {
    // Look for fallback-resource.
    cJSON* fallback_resource = cJSON_GetObjectItem(obj, "f");
    if (fallback_resource == nullptr) {
      fallback_resource = cJSON_GetObjectItem(obj, "fallback");

      // As of build 14318, complain if we find old long key names; hope to
      // remove them soon.
      if (fallback_resource != nullptr) {
        static bool printed = false;
        if (!printed) {
          printed = true;
          char* c = cJSON_Print(obj);
          BA_LOG_ONCE("found long key 'fallback' in raw lstr json: "
                      + std::string(c));
          free(c);
        }
      }
    }
    cJSON* fallback_value = cJSON_GetObjectItem(obj, "fv");
    result = g_python->GetResource(
        resource->valuestring,
        fallback_resource ? fallback_resource->valuestring : nullptr,
        fallback_value ? fallback_value->valuestring : nullptr);
  } else {
    // Apparently not a resource; lets try as a translation ("t" keys).
    cJSON* translate = cJSON_GetObjectItem(obj, "t");
    if (translate == nullptr) {
      translate = cJSON_GetObjectItem(obj, "translate");

      // As of build 14318, complain if we find long key names; hope to remove
      // them soon.
      if (translate != nullptr) {
        static bool printed = false;
        if (!printed) {
          printed = true;
          char* c = cJSON_Print(obj);
          BA_LOG_ONCE("found long key 'translate' in raw lstr json: "
                      + std::string(c));
          free(c);
        }
      }
    }
    if (translate != nullptr) {
      if (translate->type != cJSON_Array
          || cJSON_GetArraySize(translate) != 2) {
        throw Exception("Expected a 2 member array for translate");
      }
      cJSON* category = cJSON_GetArrayItem(translate, 0);
      if (category->type != cJSON_String) {
        throw Exception(
            "First member of translate array (category) must be a string");
      }
      cJSON* value = cJSON_GetArrayItem(translate, 1);
      if (value->type != cJSON_String) {
        throw Exception(
            "Second member of translate array (value) must be a string");
      }
      result =
          g_python->GetTranslation(category->valuestring, value->valuestring);
    } else {
      // Lastly try it as a value ("value" or "v").
      // (can be useful for feeding explicit strings while still allowing
      // translated subs
      cJSON* value = cJSON_GetObjectItem(obj, "v");
      if (value == nullptr) {
        value = cJSON_GetObjectItem(obj, "value");

        // As of build 14318, complain if we find long key names; hope to remove
        // them soon.
        if (value != nullptr) {
          static bool printed = false;
          if (!printed) {
            printed = true;
            char* c = cJSON_Print(obj);
            BA_LOG_ONCE("found long key 'value' in raw lstr json: "
                        + std::string(c));
            free(c);
          }
        }
      }
      if (value != nullptr) {
        if (value->type != cJSON_String) {
          throw Exception("Expected a string for value");
        }
        result = value->valuestring;
      } else {
        throw Exception("no 'resource', 'translate', or 'value' keys found");
      }
    }
  }

  // Ok; now no matter what it was, see if it contains any subs and replace
  // them.
  // ("subs" or "s")
  cJSON* subs = cJSON_GetObjectItem(obj, "s");
  if (subs == nullptr) {
    subs = cJSON_GetObjectItem(obj, "subs");

    // As of build 14318, complain if we find long key names; hope to remove
    // them soon.
    if (subs != nullptr) {
      static bool printed = false;
      if (!printed) {
        printed = true;
        char* c = cJSON_Print(obj);
        BA_LOG_ONCE("found long key 'subs' in raw lstr json: "
                    + std::string(c));
        free(c);
      }
    }
  }
  if (subs != nullptr) {
    if (subs->type != cJSON_Array) {
      throw Exception("expected an array for 'subs'");
    }
    int subs_count = cJSON_GetArraySize(subs);
    for (int i = 0; i < subs_count; i++) {
      cJSON* sub = cJSON_GetArrayItem(subs, i);
      if (sub->type != cJSON_Array || cJSON_GetArraySize(sub) != 2) {
        throw Exception(
            "Invalid subs entry; expected length 2 list of sub/replacement.");
      }

      // First item should be a string.
      cJSON* key = cJSON_GetArrayItem(sub, 0);
      if (key->type != cJSON_String) {
        throw Exception("Sub keys must be strings.");
      }
      std::string s_key = key->valuestring;

      // Second item can be a string or a dict; if its a dict, we go recursive.
      cJSON* value = cJSON_GetArrayItem(sub, 1);
      std::string s_val;
      if (value->type == cJSON_String) {
        s_val = value->valuestring;
      } else if (value->type == cJSON_Object) {
        s_val = DoCompileResourceString(value);
      } else {
        throw Exception("Sub values must be strings or dicts.");
      }

      // Replace *ALL* occurrences.
      // FIXME: Using this simple logic, If our replace value contains our
      // search value we get an infinite loop. For now, just error in that case.
      if (s_val.find(s_key) != std::string::npos) {
        throw Exception("Subs replace string cannot contain search string.");
      }
      while (true) {
        size_t pos = result.find(s_key);
        if (pos == std::string::npos) {
          break;
        }
        result.replace(pos, s_key.size(), s_val);
      }
    }
  }
  return result;
}

auto Game::CompileResourceString(const std::string& s, const std::string& loc,
                                 bool* valid) -> std::string {
  assert(g_python != nullptr);

  bool dummyvalid;
  if (valid == nullptr) {
    valid = &dummyvalid;
  }

  // Quick out: if it doesn't start with a { and end with a }, treat it as a
  // literal and just return it as-is.
  if (s.size() < 2 || s[0] != '{' || s[s.size() - 1] != '}') {
    *valid = true;
    return s;
  }

  cJSON* root = cJSON_Parse(s.c_str());
  if (root == nullptr) {
    Log("CompileResourceString failed (loc " + loc + "); invalid json: '" + s
        + "'");
    *valid = false;
    return "";
  }
  std::string result;
  try {
    result = DoCompileResourceString(root);
    *valid = true;
  } catch (const std::exception& e) {
    Log("CompileResourceString failed (loc " + loc
        + "): " + std::string(e.what()) + "; str='" + s + "'");
    result = "<error>";
    *valid = false;
  }
  cJSON_Delete(root);
  return result;
}

auto Game::GetResourceString(const std::string& key) -> std::string {
  std::string val;
  {
    std::scoped_lock lock(language_mutex_);
    auto i = language_.find(key);
    if (i != language_.end()) {
      val = i->second;
    }
  }
  return val;
}

auto Game::CharStr(SpecialChar id) -> std::string {
  std::scoped_lock lock(special_char_mutex_);
  std::string val;
  auto i = special_char_strings_.find(id);
  if (i != special_char_strings_.end()) {
    val = i->second;
  } else {
    BA_LOG_PYTHON_TRACE_ONCE("invalid key in CharStr(): '"
                             + std::to_string(static_cast<int>(id)) + "'");
    val = "?";
  }
  return val;
}

auto Game::ShouldAnnouncePartyJoinsAndLeaves() -> bool {
  assert(InLogicThread());

  // At the moment we don't announce these for public internet parties.. (too
  // much noise).
  return !public_party_enabled();
}

void Game::CleanUpBeforeConnectingToHost() {
  // We can't have connected clients and a host-connection at the same time.
  // Make a minimal attempt to disconnect any client connections we have, but
  // get them off the list immediately.
  // FIXME: Should we have a 'purgatory' for dying client connections?..
  // (they may not get the single 'go away' packet we send here)
  connections_->ForceDisconnectClients();

  // Also make sure our public party state is off; this will inform the server
  // that it should not be handing out our address to anyone.
  assert(g_python);
  SetPublicPartyEnabled(false);
}

auto Game::GetPartySize() const -> int {
  assert(InLogicThread());
  assert(game_roster_ != nullptr);
  return cJSON_GetArraySize(game_roster_);
}

void Game::LocalDisplayChatMessage(const std::vector<uint8_t>& buffer) {
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
          PlayerSpec(b1.data()).GetDisplayString() + ": " + b2.data();

      // Store it locally.
      chat_messages_.push_back(final_message);
      while (chat_messages_.size() > kMaxChatMessages) {
        chat_messages_.pop_front();
      }

      // Show it on the screen if they don't have their chat window open
      // (and don't have chat muted).
      if (!g_ui->root_ui()->party_window_open()) {
        if (!chat_muted_) {
          ScreenMessage(final_message, {0.7f, 1.0f, 0.7f});
        }
      } else {
        // Party window is open - notify it that there's a new message.
        g_python->HandleLocalChatMessage(final_message);
      }
      if (!chat_muted_) {
        g_audio->PlaySound(g_assets->GetSound(SystemSoundID::kTap));
      }
    }
  }
}

auto Game::GetGameRosterMessage() -> std::vector<uint8_t> {
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

auto Game::IsPlayerBanned(const PlayerSpec& spec) -> bool {
  millisecs_t current_time = GetRealTime();

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

void Game::StartKickVote(ConnectionToClient* starter,
                         ConnectionToClient* target) {
  // Restrict votes per client.
  millisecs_t current_time = GetRealTime();

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
    std::vector<ConnectionToClient*> connected_clients =
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
    for (ConnectionToClient* client :
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

void Game::BanPlayer(const PlayerSpec& spec, millisecs_t duration) {
  banned_players_.emplace_back(GetRealTime() + duration, spec);
}

void Game::UpdateGameRoster() {
  assert(InLogicThread());

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

  // UPDATE: starting with our big ui revision we'll always include ourself
  // here
  bool include_self = (connections()->GetConnectedClientCount() > 0);

#if BA_TOOLBAR_TEST
  include_self = true;
#endif  // BA_TOOLBAR_TEST

  if (auto* hs = dynamic_cast<HostSession*>(GetForegroundSession())) {
    // Add our host-y self.
    if (include_self) {
      cJSON* client_dict = cJSON_CreateObject();
      cJSON_AddItemToObject(
          client_dict, "spec",
          cJSON_CreateString(
              PlayerSpec::GetAccountPlayerSpec().GetSpecString().c_str()));

      // Add our list of local players.
      cJSON* player_array = cJSON_CreateArray();
      for (auto&& p : hs->players()) {
        InputDevice* input_device = p->GetInputDevice();

        // Add some basic info for each local player (only ones with real
        // names though; don't wanna send <selecting character>, etc).
        if (p->accepted() && p->name_is_real() && input_device != nullptr
            && !input_device->IsRemoteClient()) {
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
          InputDevice* input_device = p->GetInputDevice();
          if (p->accepted() && p->name_is_real() && input_device != nullptr
              && input_device->IsRemoteClient()) {
            auto* cid = static_cast<ClientInputDevice*>(input_device);
            ConnectionToClient* ctc = cid->connection_to_client();

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

  // Keep the Python layer informed on our number of connections; it may want
  // to pass the info along to the master server if we're hosting a public
  // party.
  SetPublicPartySize(total_party_size);

  // Mark the roster as dirty so we know we need to send it to everyone soon.
  game_roster_dirty_ = true;
}

void Game::SetPublicPartyEnabled(bool val) {
  assert(InLogicThread());
  if (val == public_party_enabled_) {
    return;
  }
  public_party_enabled_ = val;
  g_app_internal->PushPublicPartyState();
}

void Game::SetPublicPartySize(int count) {
  assert(InLogicThread());
  if (count == public_party_size_) {
    return;
  }
  public_party_size_ = count;

  // Push our new state to the server *ONLY* if public-party is turned on
  // (wasteful otherwise).
  if (public_party_enabled_) {
    g_app_internal->PushPublicPartyState();
  }
}

void Game::SetPublicPartyMaxSize(int count) {
  assert(InLogicThread());
  if (count == public_party_max_size_) {
    return;
  }
  public_party_max_size_ = count;

  // Push our new state to the server *ONLY* if public-party is turned on
  // (wasteful otherwise).
  if (public_party_enabled_) {
    g_app_internal->PushPublicPartyState();
  }
}

void Game::SetPublicPartyName(const std::string& name) {
  assert(InLogicThread());
  if (name == public_party_name_) {
    return;
  }
  public_party_name_ = name;

  // Push our new state to the server *ONLY* if public-party is turned on
  // (wasteful otherwise).
  if (public_party_enabled_) {
    g_app_internal->PushPublicPartyState();
  }
}

void Game::SetPublicPartyStatsURL(const std::string& url) {
  assert(InLogicThread());
  if (url == public_party_stats_url_) {
    return;
  }
  public_party_stats_url_ = url;

  // Push our new state to the server *ONLY* if public-party is turned on
  // (wasteful otherwise).
  if (public_party_enabled_) {
    g_app_internal->PushPublicPartyState();
  }
}

void Game::SetPublicPartyPlayerCount(int count) {
  assert(InLogicThread());
  if (count == public_party_player_count_) {
    return;
  }
  public_party_player_count_ = count;

  // Push our new state to the server *ONLY* if public-party is turned on
  // (wasteful otherwise).
  if (public_party_enabled_) {
    g_app_internal->PushPublicPartyState();
  }
}

}  // namespace ballistica
