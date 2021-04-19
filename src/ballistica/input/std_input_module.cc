// Released under the MIT License. See LICENSE for details.

#include "ballistica/input/std_input_module.h"

#if BA_OSTYPE_LINUX
#include <cstring>
#endif

#include "ballistica/app/app_globals.h"
#include "ballistica/game/game.h"
#include "ballistica/platform/platform.h"

namespace ballistica {

StdInputModule::StdInputModule(Thread* thread) : Module("stdin", thread) {
  assert(g_std_input_module == nullptr);
  g_std_input_module = this;
}

StdInputModule::~StdInputModule() = default;

void StdInputModule::PushBeginReadCall() {
  PushCall([this] {
    bool stdin_is_terminal = IsStdinATerminal();

    while (true) {
      // Print a prompt if we're a tty.
      // We send this to the game thread so it happens AFTER the
      // results of the last script-command message we may have just sent.
      if (stdin_is_terminal) {
        g_game->PushCall([] {
          if (!g_app_globals->shutting_down) {
            printf(">>> ");
            fflush(stdout);
          }
        });
      }

      // Was using getline, but switched to
      // new fgets based approach (more portable).
      // Ideally at some point we can wire up to the Python api to get behavior
      // more like the actual Python command line.
      char buffer[4096];
      char* val = fgets(buffer, sizeof(buffer), stdin);
      if (val) {
        int last_char = static_cast<int>(strlen(buffer) - 1);

        // Clip off our last char if its a newline (just to keep things tidier).
        if (last_char >= 0 && buffer[last_char] == '\n') {
          buffer[last_char] = 0;
        }
        g_game->PushStdinScriptCommand(buffer);
      } else {
        // At the moment we bail on any read error.
        if (feof(stdin)) {
          if (stdin_is_terminal) {
            // Ok this is strange: on windows consoles, it seems that Ctrl-C in
            // a terminal immediately closes our stdin even if we catch the
            // interrupt, and then our python interrupt handler runs a moment
            // later. This means we wind up telling the user that EOF was
            // reached and they should Ctrl-C to quit right after they've hit
            // Ctrl-C to quit. To hopefully avoid this, let's hold off on the
            // print for a second and see if a shutdown has begun first.
            // (or, more likely, just never print because the app has exited).
            if (g_buildconfig.windows_console_build()) {
              Platform::SleepMS(250);
            }
            if (!g_app_globals->shutting_down) {
              printf("Stdin EOF reached. Use Ctrl-C to quit.\n");
              fflush(stdout);
            }
          }
        } else {
          Log("StdInputModule got non-eof error reading stdin: "
              + std::to_string(ferror(stdin)));
        }
        break;
      }
    }
  });
}

}  // namespace ballistica
