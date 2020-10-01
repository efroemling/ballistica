// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_APP_APP_GLOBALS_H_
#define BALLISTICA_APP_APP_GLOBALS_H_

#include <map>
#include <mutex>
#include <string>
#include <thread>
#include <vector>

#include "ballistica/ballistica.h"
#include "ballistica/networking/master_server_config.h"

namespace ballistica {

// The first thing the engine does is allocate an instance of this as g_globals.
// As much as possible, previously static/global values should be moved to here,
// ideally as a temporary measure until they can be placed as non-static members
// in the proper classes.
// Any use of non-trivial global/static values such as class instances should be
// avoided since it can introduce ambiguities during init and teardown.
// For more explanation, see the 'Static and Global Variables' section in the
// Google C++ Style Guide.
class AppGlobals {
 public:
  AppGlobals(int argc, char** argv);

  /// Program argument count (on applicable platforms).
  int argc{};

  /// Program argument values (on applicable platforms).
  char** argv{};

  std::map<std::string, NodeType*> node_types;
  std::map<int, NodeType*> node_types_by_id;
  std::map<std::string, NodeMessageType> node_message_types;
  std::vector<std::string> node_message_formats;
  std::string calced_blessing_hash;
  bool have_mods{};
  bool replay_open{};
  std::vector<Thread*> pausable_threads;
  TouchInput* touch_input{};
  std::string console_startup_messages;
  std::mutex log_mutex;
  std::string log;
  bool put_log{};
  bool log_full{};
  int master_server_source{1};
  int session_count{};
  bool shutting_down{};
  bool have_incentivized_ad{true};
  bool should_pause{};
  TelnetServer* telnet_server{};
  Console* console{};
  bool reset_vr_orientation{};
  bool user_ran_commands{};
  UIScale ui_scale{UIScale::kLarge};
  AccountType account_type{AccountType::kInvalid};
  bool remote_server_accepting_connections{true};
  std::string game_commands;
  std::string user_agent_string{"BA_USER_AGENT_UNSET (" BA_PLATFORM_STRING ")"};
  int return_value{};
  bool is_stdin_a_terminal{true};
  std::thread::id main_thread_id{};
  bool is_bootstrapped{};
  bool args_handled{};
  std::string user_config_dir;
  bool started_suicide{};

  // Netplay testing.
  int buffer_time{1000 / 30};

  // How often we send dynamics sync packets.
  int dynamics_sync_time{500};

  // How many steps we sample for each bucket.
  int delay_samples{20};

  bool vr_mode{g_buildconfig.vr_build()};
  // Temp dirty way to do some shutdown stuff (FIXME: move to an App method).
  void (*temp_cleanup_callback)() = nullptr;
  millisecs_t real_time{};
  millisecs_t last_real_time_ticks{};
  std::mutex real_time_mutex;
  std::mutex thread_name_map_mutex;
  std::map<std::thread::id, std::string> thread_name_map;
  std::string master_server_addr{BA_MASTER_SERVER_DEFAULT_ADDR};
  std::string master_server_fallback_addr{BA_MASTER_SERVER_FALLBACK_ADDR};
#if BA_DEBUG_BUILD
  std::mutex object_list_mutex;
  Object* object_list_first{};
  int object_count{0};
#endif
};

}  // namespace ballistica

#endif  // BALLISTICA_APP_APP_GLOBALS_H_
