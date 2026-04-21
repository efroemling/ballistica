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
  static auto ForArgsAndEnvVars(int argc, char** argv, seconds_t launch_time)
      -> CoreConfig;

  static auto ForEnvVars() -> CoreConfig;

  /// Build a core-config for a modular app being run from the command-line.
  /// In this case, Python has already been inited and Ballistica has
  /// already been imported (since that's where this code lives) so there is
  /// less that can be affected by a core-config.

  void ApplyEnvVars();
  void ApplyArgs(int argc, char** argv);

  /// Enable vr mode on supported platforms.
  bool vr_mode{};

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

  /// If set, this single Python command will be run instead of the normal
  /// app loop (monolithic builds only).
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

  /// Wall-clock seconds-since-epoch captured as early as possible at
  /// process start (typically the first line of main()). Passed on to
  /// baenv.configure() so the Python-side log-handler's 'relative time'
  /// anchor matches process start rather than baenv.configure() entry.
  /// Unit matches Python's time.time() so the two can be compared.
  seconds_t launch_time{};

  /// If true, indicates the caller intends to bring up a Python
  /// LogHandler later in startup (typically via
  /// baenv.configure(setup_logging=True)). When set, C++ log calls made
  /// before that handler is wired up are buffered and replayed through
  /// it with their original timestamps, rather than being emitted to
  /// Python's default root logger (which at default WARNING would drop
  /// INFO/DEBUG messages silently). When false (the default) log calls
  /// flow through to Python as soon as the interpreter is ready.
  /// Auto-derived by ForArgsAndEnvVars() as !call_command.has_value().
  bool expect_log_handler_setup{};
};

}  // namespace ballistica::core

#endif  // BALLISTICA_CORE_SUPPORT_CORE_CONFIG_H_
