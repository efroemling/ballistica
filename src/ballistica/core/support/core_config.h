// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_CORE_SUPPORT_CORE_CONFIG_H_
#define BALLISTICA_CORE_SUPPORT_CORE_CONFIG_H_

#include <optional>
#include <string>

#include "ballistica/shared/ballistica.h"

namespace ballistica::core {

/// A collection of low level options for a run of the engine; passed when
/// initing the core feature-set.
class CoreConfig {
 public:
  static auto ForArgsAndEnvVars(int argc, char** argv) -> CoreConfig;

  static auto ForEnvVars() -> CoreConfig;

  /// Build a core-config for a modular app being run from the command-line.
  /// In this case, Python has already been inited and Ballistica has
  /// already been imported (since that's where this code lives) so there is
  /// less that can be affected by a core-config.

  void ApplyEnvVars();
  void ApplyArgs(int argc, char** argv);

  /// Enable vr mode on supported platforms.
  bool vr_mode{};

  /// Log various stages/times in the bootstrapping process.
  // bool lifecycle_log{};

  /// Let the engine know there's a debugger attached so it should do things
  /// like abort() instead of exiting with error codes.
  bool debugger_attached{};

  /// Enables some extra timing logs/prints.
  bool debug_timing{};

  /// If set, the app should exit immediately with this return code (on
  /// applicable platforms). This can be set by command-line parsing in
  /// response to arguments such as 'version' or 'help' which are processed
  /// immediately in their entirety.
  std::optional<int> immediate_return_code{};

  /// If set, this single Python command will be run instead of the
  /// normal app loop (monolithic builds only).
  std::optional<std::string> call_command{};

  /// Python command to be run within the normal app loop.
  std::optional<std::string> exec_command{};

  /// Explicitly passed config dir.
  std::optional<std::string> config_dir{};

  /// Explicitly passed data dir.
  std::optional<std::string> data_dir{};

  /// Explicitly passed user-python (mods) dir.
  std::optional<std::string> user_python_dir{};

  /// Explicitly passed cache dir.
  std::optional<std::string> cache_dir{};

  /// Disable writing of bytecode (.pyc) files.
  bool dont_write_bytecode{};
};

}  // namespace ballistica::core

#endif  // BALLISTICA_CORE_SUPPORT_CORE_CONFIG_H_
