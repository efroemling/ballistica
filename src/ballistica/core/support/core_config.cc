// Released under the MIT License. See LICENSE for details.

#include "ballistica/core/support/core_config.h"

#include <cstring>
#include <filesystem>

// Note to self: this stuff gets used before *any* of the engine is inited
// so we can't use engine functionality at all here.

namespace ballistica::core {

// Kicks out of arg processing and tells the app to return an error code.
class BadArgsException : public ::std::exception {};

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

auto CoreConfig::FromCommandLineAndEnv(int argc, char** argv) -> CoreConfig {
  auto cfg = CoreConfig();

  // First set any values we allow env-vars for.
  // We want explicitly passed values to override these in any cases where both
  // forms are accepted.
  if (auto* envval = getenv("BA_BOOT_LOG")) {
    if (!strcmp(envval, "1")) {
      cfg.log_boot_process = true;
    }
  }
  if (auto* envval = getenv("BA_DEBUGGER_ATTACHED")) {
    if (!strcmp(envval, "1")) {
      cfg.debugger_attached = true;
    }
  }

  // REMOVE ME FOR 1.7.20 FINAL.
  printf("TEMP: forcing BA_BOOT_LOG=1 during 1.7.20 development.\n");
  cfg.log_boot_process = true;

  try {
    // First handle single-arg special cases like --help or --version.
    if (IsSingleArgSpecialCase(argc, argv, "--help", "-h")) {
      PrintHelp();
      cfg.immediate_return_code = 0;
      return cfg;
    }
    if (IsSingleArgSpecialCase(argc, argv, "--version", "-v")) {
      printf("BallisticaKit %s build %d\n", kEngineVersion, kEngineBuildNumber);
      cfg.immediate_return_code = 0;
      return cfg;
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
      return cfg;
    }

    // Ok, all single-arg cases handled; now go through everything else
    // parsing flags/values from left to right.
    int i = 1;
    std::optional<std::string> value;
    while (i < argc) {
      if ((value = ParseArgValue(argc, argv, &i, "--command", "-c"))) {
        cfg.call_command = *value;
      } else if ((value = ParseArgValue(argc, argv, &i, "--exec", "-e"))) {
        cfg.exec_command = *value;
      } else if ((value =
                      ParseArgValue(argc, argv, &i, "--config-dir", "-C"))) {
        cfg.config_dir = *value;
        // Make sure what they passed exists.
        // Note: Normally baenv will try to create whatever the config dir is;
        // do we just want to allow that to happen in this case? But perhaps
        // being more strict is ok when accepting user input.
        if (!std::filesystem::exists(*cfg.config_dir)) {
          printf("Error: Provided config dir does not exist: '%s'.",
                 cfg.config_dir->c_str());
          throw BadArgsException();
        }
      } else if ((value = ParseArgValue(argc, argv, &i, "--data-dir", "-d"))) {
        cfg.data_dir = *value;
        // Make sure what they passed exists.
        if (!std::filesystem::exists(*cfg.data_dir)) {
          printf("Error: Provided data dir does not exist: '%s'.",
                 cfg.data_dir->c_str());
          throw BadArgsException();
        }
      } else if ((value = ParseArgValue(argc, argv, &i, "--mods-dir", "-m"))) {
        cfg.user_python_dir = *value;
        // Make sure what they passed exists.
        if (!std::filesystem::exists(*cfg.user_python_dir)) {
          printf("Error: Provided mods dir does not exist: '%s'.",
                 cfg.user_python_dir->c_str());
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
    cfg.immediate_return_code = 1;
  }
  return cfg;
}

}  // namespace ballistica::core
