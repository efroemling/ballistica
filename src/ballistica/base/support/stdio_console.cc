// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/support/stdio_console.h"

#include <Python.h>

#include <cstdio>
#include <string>

#include "ballistica/base/app_adapter/app_adapter.h"
#include "ballistica/base/app_mode/app_mode.h"
#include "ballistica/base/logic/logic.h"
#include "ballistica/base/platform/base_platform.h"
#include "ballistica/base/support/context.h"
#include "ballistica/core/core.h"
#include "ballistica/core/platform/core_platform.h"
#include "ballistica/shared/foundation/event_loop.h"
#include "ballistica/shared/python/python_command.h"

namespace ballistica::base {

StdioConsole::StdioConsole() = default;

void StdioConsole::Start() {
  g_base->app_adapter->PushMainThreadCall([this] { StartInMainThread_(); });
}

void StdioConsole::StartInMainThread_() {
  assert(g_core && g_core->InMainThread());

  // Spin up our thread.
  event_loop_ = new EventLoop(EventLoopID::kStdin);
  g_core->suspendable_event_loops.push_back(event_loop_);

  // Tell our thread to start reading.
  event_loop()->PushCall([this] {
    bool stdin_is_terminal = g_core->platform->is_stdin_a_terminal();

    while (true) {
      // Print a prompt if we're a tty. We send this to the logic thread so
      // it happens AFTER the results of the last script-command message we
      // may have just sent.
      if (stdin_is_terminal) {
        g_base->logic->event_loop()->PushCall([] {
          if (!g_base->logic->shutting_down()) {
            printf(">>> ");
            fflush(stdout);
          }
        });
      }

      // Was using getline, but switched to new fgets based approach (more
      // portable). Ideally at some point we can wire up to the Python api
      // to get behavior more like the actual Python command line.
      char buffer[4096];
      char* val;

      // Use our fancy safe version of fgets(); on some platforms this will
      // return a fake EOF once the app/engine starts going down. This
      // avoids some scenarios where regular blocking fgets() prevents the
      // process from exiting (until they press Ctrl-D in the terminal).
      if (explicit_bool(true)) {
        val = g_base->platform->SafeStdinFGetS(buffer, sizeof(buffer), stdin);
      } else {
        val = fgets(buffer, sizeof(buffer), stdin);
      }
      if (val) {
        pending_input_ += val;

        if (!pending_input_.empty()
            && pending_input_[pending_input_.size() - 1] == '\n') {
          // Get rid of the last newline and ship it to the game.
          pending_input_.pop_back();

          // Handle special cases ourself.
          if (pending_input_ == std::string("@clear")) {
            Clear_();
          } else {
            // Otherwise ship it off to the engine to run.
            PushCommand_(pending_input_);
          }
          pending_input_.clear();
        }
      } else {
        // Bail on any error (could be actual EOF or one of our fake ones).
        if (stdin_is_terminal) {
          // Ok this is strange: on windows consoles, it seems that Ctrl-C
          // in a terminal immediately closes our stdin even if we catch
          // the interrupt, and then our Python interrupt handler runs a
          // moment later. This means we wind up telling the user that EOF
          // was reached and they should Ctrl-C to quit right after
          // they've hit Ctrl-C to quit. To hopefully avoid this, let's
          // hold off on the print for a second and see if a shutdown has
          // begun first. (or, more likely, just never print because the
          // app has exited).
          if (g_buildconfig.windows_console_build()) {
            core::CorePlatform::SleepMillisecs(250);
          }
          if (!g_base->logic->shutting_down()) {
            printf("Stdin EOF reached. Use Ctrl-C to quit.\n");
            fflush(stdout);
          }
        }
        break;
      }
    }
  });
}

void StdioConsole::Clear_() {
  int retval{-1};
  if (g_buildconfig.platform_macos() || g_buildconfig.platform_linux()) {
    // Attempt to run actual clear command on unix-y systems to plop
    // our prompt back at the top of the screen.
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
}

void StdioConsole::PushCommand_(const std::string& command) {
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
      if (obj.exists()) {
        // Print the value if we're running directly from a terminal
        // (or being run under the server-manager)
        if ((g_core->platform->is_stdin_a_terminal()
             || g_base->server_wrapper_managed())
            && obj.get() != Py_None) {
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
