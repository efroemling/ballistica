// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_APP_APP_H_
#define BALLISTICA_APP_APP_H_

#include <mutex>
#include <string>
#include <thread>
#include <unordered_map>
#include <vector>

#include "ballistica/ballistica.h"

namespace ballistica {

// The first thing the engine does is allocate an instance of this as g_app.
class App {
 public:
  App(int argc, char** argv);

  // The following are misc values that should be migrated to applicable
  // subsystem classes.
  int argc{};
  char** argv{};
  bool threads_paused{};
  std::unordered_map<std::string, NodeType*> node_types;
  std::unordered_map<int, NodeType*> node_types_by_id;
  std::unordered_map<std::string, NodeMessageType> node_message_types;
  std::vector<std::string> node_message_formats;
  bool workspaces_in_use{};
  bool replay_open{};
  std::vector<Thread*> pausable_threads;
  TouchInput* touch_input{};
  std::string console_startup_messages;
  std::mutex v1_cloud_log_mutex;
  std::string v1_cloud_log;
  bool did_put_v1_cloud_log{};
  bool v1_cloud_log_full{};
  int master_server_source{0};
  int session_count{};
  bool shutting_down{};
  bool have_incentivized_ad{false};
  bool should_pause{};
  TelnetServer* telnet_server{};
  Console* console{};
  bool reset_vr_orientation{};
  bool user_ran_commands{};
  V1AccountType account_type{V1AccountType::kInvalid};
  bool remote_server_accepting_connections{true};
  std::string exec_command;
  std::string user_agent_string{"BA_USER_AGENT_UNSET (" BA_PLATFORM_STRING ")"};
  int return_value{};
  bool debug_timing{};
  std::thread::id main_thread_id{};
  bool is_bootstrapped{};
  bool args_handled{};
  std::string user_config_dir;
  bool started_suicide{};

  // Maximum time in milliseconds to buffer game input/output before sending
  // it over the network.
  int buffer_time{0};

  // How often we send dynamics resync messages.
  int dynamics_sync_time{500};

  // How many steps we sample for each bucket.
  int delay_bucket_samples{60};

  bool vr_mode{g_buildconfig.vr_build()};
  millisecs_t real_time{};
  millisecs_t last_real_time_ticks{};
  std::mutex real_time_mutex;
  std::mutex thread_name_map_mutex;
  std::unordered_map<std::thread::id, std::string> thread_name_map;
#if BA_DEBUG_BUILD
  std::mutex object_list_mutex;
  Object* object_list_first{};
  int object_count{0};
#endif
};

}  // namespace ballistica

#endif  // BALLISTICA_APP_APP_H_
