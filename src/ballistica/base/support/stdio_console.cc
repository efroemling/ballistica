// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/support/stdio_console.h"

#include <cstring>

#include "ballistica/base/app_adapter/app_adapter.h"
#include "ballistica/base/app_mode/app_mode.h"
#include "ballistica/base/logic/logic.h"
#include "ballistica/base/support/context.h"
#include "ballistica/core/platform/core_platform.h"
#include "ballistica/shared/foundation/event_loop.h"
#include "ballistica/shared/python/python_command.h"
#include "ballistica/shared/python/python_sys.h"

namespace ballistica::base {

StdioConsole::StdioConsole() = default;

void StdioConsole::Start() {
  g_base->app_adapter->PushMainThreadCall([this] { StartInMainThread(); });
}

void StdioConsole::StartInMainThread() {
  assert(g_core && g_core->InMainThread());

  // Spin up our thread.
  event_loop_ = new EventLoop(EventLoopID::kStdin);
  g_core->suspendable_event_loops.push_back(event_loop_);

  // Tell our thread to start reading.
  event_loop()->PushCall([this] {
    bool stdin_is_terminal = g_core->platform->is_stdin_a_terminal();

    while (true) {
      // Print a prompt if we're a tty.
      // We send this to the logic thread so it happens AFTER the
      // results of the last script-command message we may have just sent.
      if (stdin_is_terminal) {
        g_base->logic->event_loop()->PushCall([] {
          if (!g_base->logic->shutting_down()) {
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
          if (g_buildconfig.ostype_macos() || g_buildconfig.ostype_linux()) {
            // Attempt to run actual clear command on unix-y systems to
            // plop our prompt back at the top of the screen.
            retval = core::CorePlatform::System("clear");
          }
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
          PushCommand(pending_input_);
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
              core::CorePlatform::SleepMillisecs(250);
            }
            if (!g_base->logic->shutting_down()) {
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

void StdioConsole::PushCommand(const std::string& command) {
  g_base->logic->event_loop()->PushCall([command] {
    // These are always run in whichever context is 'visible'.
    ScopedSetContext ssc(g_base->app_mode()->GetForegroundContext());
    PythonCommand cmd(command, "<stdin>");
    if (!g_core->user_ran_commands) {
      g_core->user_ran_commands = true;
    }

    // Eval this if possible (so we can possibly print return value).
    if (cmd.CanEval()) {
      auto obj = cmd.Eval(true, nullptr, nullptr);
      if (obj.Exists()) {
        // Print the value if we're running directly from a terminal
        // (or being run under the server-manager)
        if ((g_core->platform->is_stdin_a_terminal()
             || g_base->server_wrapper_managed())
            && obj.Get() != Py_None) {
          printf("%s\n", obj.Repr().c_str());
          fflush(stdout);
        }
      }
    } else {
      // Can't eval it; exec it.
      cmd.Exec(true, nullptr, nullptr);
    }
  });
}

}  // namespace ballistica::base
