// Released under the MIT License. See LICENSE for details.

#include "ballistica/app/app_globals.h"

#include <cstring>

namespace ballistica {

AppGlobals::AppGlobals(int argc_in, char** argv_in)
    : argc{argc_in}, argv{argv_in}, main_thread_id{std::this_thread::get_id()} {
  // Enable extra timing logs via env var.
  const char* debug_timing_env = getenv("BA_DEBUG_TIMING");
  if (debug_timing_env != nullptr && !strcmp(debug_timing_env, "1")) {
    debug_timing = true;
  }
}

}  // namespace ballistica
