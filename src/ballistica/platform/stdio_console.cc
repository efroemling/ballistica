// Released under the MIT License. See LICENSE for details.

#include "ballistica/platform/stdio_console.h"

#if BA_OSTYPE_LINUX
#include <cstring>
#endif

#include "ballistica/app/app.h"
#include "ballistica/core/thread.h"
#include "ballistica/logic/logic.h"
#include "ballistica/platform/platform.h"

namespace ballistica {

StdioConsole::StdioConsole() {
  // We're a singleton; make sure we don't already exist.
  assert(g_stdio_console == nullptr);

  // Spin up our thread.
  thread_ = new Thread(ThreadTag::kAssets);
  g_app->pausable_threads.push_back(thread_);
}

auto StdioConsole::OnAppStart() -> void {
  // Tell our thread to start reading.
  thread()->PushCall([this] {
    bool stdin_is_terminal = g_platform->is_stdin_a_terminal();

    while (true) {
      // Print a prompt if we're a tty.
      // We send this to the logic thread so it happens AFTER the
      // results of the last script-command message we may have just sent.
      if (stdin_is_terminal) {
        g_logic->thread()->PushCall([] {
          if (!g_app->shutting_down) {
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
        if (val == std::string("@clear\n")) {
          int retval{-1};
#if BA_OSTYPE_MACOS || BA_OSTYPE_LINUX
          // Attempt to run actual clear command on unix-y systems to
          // plop our prompt back at the top of the screen.
          retval = system("clear");
#endif
          // As a fallback, just spit out a bunch of newlines.
          if (retval != 0) {
            std::string space;
            for (int i = 0; i < 100; ++i) {
              space += "\n";
            }
            printf("%s", space.c_str());
          }
          continue;
        }
        pending_input_ += val;

        if (!pending_input_.empty()
            && pending_input_[pending_input_.size() - 1] == '\n') {
          // Get rid of the last newline and ship it to the game.
          pending_input_.pop_back();
          g_logic->PushStdinScriptCommand(pending_input_);
          pending_input_.clear();
        }
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
            if (!g_app->shutting_down) {
              printf("Stdin EOF reached. Use Ctrl-C to quit.\n");
              fflush(stdout);
            }
          }
        } else {
          Log(LogLevel::kError, "StdioConsole got non-eof error reading stdin: "
                                    + std::to_string(ferror(stdin)));
        }
        break;
      }
    }
  });
}

}  // namespace ballistica
