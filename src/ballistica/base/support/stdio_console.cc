// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/support/stdio_console.h"

#include <Python.h>

#include <cstdio>
#include <string>

#include "ballistica/base/app_adapter/app_adapter.h"
#include "ballistica/base/app_mode/app_mode.h"
#include "ballistica/base/logic/logic.h"
#include "ballistica/base/platform/base_platform.h"
#include "ballistica/base/python/base_python.h"
#include "ballistica/base/support/context.h"
#include "ballistica/core/core.h"
#include "ballistica/core/platform/core_platform.h"
#include "ballistica/shared/foundation/event_loop.h"
#include "ballistica/shared/python/python.h"
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

    // Use Python's native interactive loop which includes readline support
    // for autocompletion, history, and line editing.
    if (Py_IsInitialized()) {
      Python::ScopedInterpreterLock gil;

      // Enable readline for full REPL features:
      // - Command history (up/down arrows)
      // - Line editing (backspace, left/right)
      // - Tab autocompletion
      const char* readline_import =
          "import readline\n"
          "import rlcompleter\n"
          "readline.parse_and_bind('tab: complete')\n";

      PyRun_SimpleString(readline_import);

      // Run default imports (babase, bascenev1, bauiv1, etc)
      // which are configured in projectconfig.json
      g_base->python->objs()
          .Get(BasePython::ObjID::kRunDefaultImportsCall)
          .Call();

      // Print any errors that occurred during default imports
      if (PyErr_Occurred()) {
        PyErr_Print();
      }

      // Run Python's interactive loop directly. This handles:
      // - Autocompletion (via readline + rlcompleter)
      // - Command history (via readline)
      // - Multi-line statements
      // - Importing of ballistica modules
      PyRun_InteractiveLoop(stdin, "<stdin>");
    } else {
      if (stdin_is_terminal) {
        g_base->logic->event_loop()->PushCall([] {
          if (!g_base->logic->shutting_down()) {
            printf(">>> ");
            fflush(stdout);
          }
        });
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

}  // namespace ballistica::base
