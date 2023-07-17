// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_CORE_SUPPORT_CORE_CONFIG_H_
#define BALLISTICA_CORE_SUPPORT_CORE_CONFIG_H_

#include <optional>
#include <string>

#include "ballistica/shared/ballistica.h"

namespace ballistica::core {

/// Collection of low level options for a run of the engine; passed
/// when initing the core feature-set.
class CoreConfig {
 public:
  static auto FromCommandLineAndEnv(int argc, char** argv) -> CoreConfig;

  /// Enable vr mode on supported platforms.
  bool vr_mode{};

  /// If set, the app should exit immediately with this return code (on
  /// applicable platforms). This can be set by command-line parsing in
  /// response to arguments such as 'version' or 'help' which are processed
  /// immediately in their entirety.
  std::optional<int> immediate_return_code{};

  /// If set, this single Python command will be run instead of the
  /// normal app loop.
  std::optional<std::string> call_command{};

  /// Python command to be run within the normal app loop.
  std::optional<std::string> exec_command{};

  /// Explicitly set config dir.
  std::optional<std::string> config_dir{};

  /// Explicitly set data dir.
  std::optional<std::string> data_dir{};

  /// Explicitly set user-python (mods) dir.
  std::optional<std::string> user_python_dir{};

  /// Log various stages/times in the bootstrapping process.
  bool lifecycle_log{};

  /// Normally early C++ Log() calls are held until babase has been imported
  /// so that when they are pushed out to the Python logging calls they are
  /// properly routed through the full engine. If you are not using babase
  /// or are trying to debug early issues you can flip this off to push
  /// things to Python as soon as technically possible.
  bool hold_early_logs{true};

  /// Let the engine know there's a debugger attached so it should do things
  /// like abort() instead of exiting with error codes.
  bool debugger_attached{};

  /// Enables some extra timing logs/prints.
  bool debug_timing{};
};

}  // namespace ballistica::core

#endif  // BALLISTICA_CORE_SUPPORT_CORE_CONFIG_H_
