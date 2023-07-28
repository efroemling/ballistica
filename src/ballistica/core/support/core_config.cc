// Released under the MIT License. See LICENSE for details.

#include "ballistica/core/support/core_config.h"

#include <cstring>
#include <filesystem>

// Note to self: this stuff gets used before *any* of the engine is inited
// so we can't use engine functionality at all here.

namespace ballistica::core {

// Kicks out of arg processing and tells the app to return an error code.
class BadArgsException : public ::std::exception {};

/// Look for a special case such as --help.
static auto IsSingleArgSpecialCase(int argc, char** argv, const char* arg_long,
                                   const char* arg_short = nullptr) -> bool {
  // See if the args exists *anywhere*.
  for (int i = 1; i < argc; ++i) {
    for (const char* arg : {arg_short, arg_long}) {
      if (arg == nullptr) {
        continue;
      }
      if (!strcmp(argv[i], arg)) {
        // These args are designed to not coexist with others.
        if (argc != 2) {
          printf("Error: Arg '%s' cannot be used with other args.\n", argv[i]);
          throw BadArgsException();
        }
        return true;
      }
    }
  }
  return false;
}

static void PrintHelp() {
  printf(
      "ballisticakit help:\n"
      " -h, --help                Print this help.\n"
      " -v, --version             Print app version information.\n"
      " -c, --command     <cmd>   Run a Python command instead of the normal"
      " app loop.\n"
      " -e, --exec        <cmd>   Run a Python command from within"
      " the app loop.\n"
      " -C, --config-dir  <path>  Override the app config directory.\n"
      " -d, --data-dir    <path>  Override the app data directory.\n"
      " -m, --mods-dir    <path>  Override the app mods directory.\n");
}

/// If the arg at the provided index matches the long/short names given,
/// returns the value in the next arg place and increments the index.
static auto ParseArgValue(int argc, char** argv, int* i, const char* arg_long,
                          const char* arg_short = nullptr)
    -> std::optional<std::string> {
  assert(i);
  assert(*i < argc);
  for (const char* arg : {arg_short, arg_long}) {
    if (arg == nullptr) {
      continue;
    }
    if (!strcmp(argv[*i], arg)) {
      // Ok; we match!
      auto val_index = *i + 1;
      if (val_index >= argc) {
        printf("Error: No value provided following arg '%s'.\n", argv[*i]);
        throw BadArgsException();
      }
      *i += 2;
      return argv[val_index];
    }
  }
  // No match.
  return {};
}

void CoreConfig::ApplyEnvVars() {
  if (auto* envval = getenv("BA_LIFECYCLE_LOG")) {
    if (!strcmp(envval, "1")) {
      lifecycle_log = true;
    }
  }
  if (auto* envval = getenv("BA_DEBUGGER_ATTACHED")) {
    if (!strcmp(envval, "1")) {
      debugger_attached = true;
    }
  }
  if (auto* envval = getenv("BA_DEBUG_TIMING")) {
    if (!strcmp(envval, "1")) {
      debug_timing = true;
    }
  }
}

void CoreConfig::ApplyArgs(int argc, char** argv) {
  try {
    // First handle single-arg special cases like --help or --version.
    if (IsSingleArgSpecialCase(argc, argv, "--help", "-h")) {
      PrintHelp();
      immediate_return_code = 0;
      return;
    }
    if (IsSingleArgSpecialCase(argc, argv, "--version", "-v")) {
      printf("BallisticaKit %s build %d\n", kEngineVersion, kEngineBuildNumber);
      immediate_return_code = 0;
      return;
    }
    if (IsSingleArgSpecialCase(argc, argv, "--crash")) {
      int dummyval{};
      int* invalid_ptr{&dummyval};

      // A bit of obfuscation to try and keep linters quiet.
      if (explicit_bool(true)) {
        invalid_ptr = nullptr;
      }
      if (explicit_bool(true)) {
        *invalid_ptr = 1;
      }
      return;
    }

    // Ok, all single-arg cases handled; now go through everything else
    // parsing flags/values from left to right.
    int i = 1;
    std::optional<std::string> value;
    while (i < argc) {
      if ((value = ParseArgValue(argc, argv, &i, "--command", "-c"))) {
        call_command = *value;
      } else if ((value = ParseArgValue(argc, argv, &i, "--exec", "-e"))) {
        exec_command = *value;
      } else if ((value =
                      ParseArgValue(argc, argv, &i, "--config-dir", "-C"))) {
        config_dir = *value;
        // Make sure what they passed exists.
        // Note: Normally baenv will try to create whatever the config dir is;
        // do we just want to allow that to happen in this case? But perhaps
        // being more strict is ok when accepting user input.
        if (!std::filesystem::is_directory(*config_dir)) {
          printf("Error: Provided config-dir path '%s' is not a directory.",
                 config_dir->c_str());
          throw BadArgsException();
        }
      } else if ((value = ParseArgValue(argc, argv, &i, "--data-dir", "-d"))) {
        data_dir = *value;
        // Make sure what they passed exists.
        if (!std::filesystem::is_directory(*data_dir)) {
          printf("Error: Provided data-dir path '%s' is not a directory.",
                 data_dir->c_str());
          throw BadArgsException();
        }
      } else if ((value = ParseArgValue(argc, argv, &i, "--mods-dir", "-m"))) {
        user_python_dir = *value;
        // Make sure what they passed exists.
        if (!std::filesystem::is_directory(*user_python_dir)) {
          printf("Error: Provided mods-dir path '%s' is not a directory.",
                 user_python_dir->c_str());
          throw BadArgsException();
        }
      } else {
        printf(
            "Error: Invalid arg '%s'.\n"
            "Run 'ballisticakit --help' to see available args.\n",
            argv[i]);
        throw BadArgsException();
      }
    }
  } catch (const BadArgsException&) {
    immediate_return_code = 1;
  }
}

auto CoreConfig::ForEnvVars() -> CoreConfig {
  CoreConfig cfg{};

  cfg.ApplyEnvVars();

  return cfg;
}

auto CoreConfig::ForArgsAndEnvVars(int argc, char** argv) -> CoreConfig {
  CoreConfig cfg{};

  // Apply env-vars first. We want explicit args to override these.
  cfg.ApplyEnvVars();
  cfg.ApplyArgs(argc, argv);

  return cfg;
}

}  // namespace ballistica::core
