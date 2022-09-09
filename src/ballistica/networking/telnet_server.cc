// Released under the MIT License. See LICENSE for details.

#include "ballistica/networking/telnet_server.h"

#include "ballistica/app/app_globals.h"
#include "ballistica/core/context.h"
#include "ballistica/core/thread.h"
#include "ballistica/game/game.h"
#include "ballistica/networking/networking.h"
#include "ballistica/networking/networking_sys.h"
#include "ballistica/platform/platform.h"
#include "ballistica/python/python_command.h"
#include "ballistica/python/python_sys.h"

namespace ballistica {

TelnetServer::TelnetServer(int port) : port_(port) {
  thread_ = new std::thread(RunThreadStatic, this);
  assert(g_app_globals->telnet_server == nullptr);
  g_app_globals->telnet_server = this;

  // NOTE: we consider access implicitly granted on headless builds
  // since we can't pop up the request dialog.
  // There is still password protection and we now don't even spin
  // up the telnet socket by default on servers.
  if (HeadlessMode()) {
    user_has_granted_access_ = true;
  }
}

void TelnetServer::Pause() {
  assert(InMainThread());
  assert(!paused_);
  {
    std::unique_lock<std::mutex> lock(paused_mutex_);
    paused_ = true;
  }

  // FIXME - need a way to kill these sockets;
  //  On iOS they die automagically but not android.
  //  attempted to force-close at some point but it didn't work (on android at
  //  least)
}

void TelnetServer::Resume() {
  assert(InMainThread());
  assert(paused_);
  {
    std::unique_lock<std::mutex> lock(paused_mutex_);
    paused_ = false;
  }

  // Poke our thread so it can go on its way.
  paused_cv_.notify_all();
}

#pragma clang diagnostic push
#pragma ide diagnostic ignored "ConstantFunctionResult"

auto TelnetServer::RunThread() -> int {
  // Do this whole thing in a loop.
  // If we get put to sleep we just start over.
  while (true) {
    // Sleep until we're unpaused.
    if (paused_) {
      std::unique_lock<std::mutex> lock(paused_mutex_);
      paused_cv_.wait(lock, [this] { return (!paused_); });
    }

    sd_ = socket(AF_INET, SOCK_STREAM, 0);
    if (sd_ < 0) {
      Log("Error: Unable to open host socket; errno " + std::to_string(errno));
      return 1;
    }

    // Make it reusable.
    int on = 1;
    int status =
        setsockopt(sd_, SOL_SOCKET, SO_REUSEADDR, (const char*)&on, sizeof(on));
    if (-1 == status) {
      Log("Error setting SO_REUSEADDR on telnet server");
    }

    // Bind to local server port.
    struct sockaddr_in serv_addr {};
    serv_addr.sin_family = AF_INET;
    serv_addr.sin_addr.s_addr = htonl(INADDR_ANY);  // NOLINT
    int result;
    serv_addr.sin_port = htons(port_);  // NOLINT
    result = ::bind(sd_, (struct sockaddr*)&serv_addr, sizeof(serv_addr));
    if (result != 0) {
      return 1;
    }
    char buffer[10000];
    const char* prompt = "ballisticacore> ";
    const char* password_prompt = "password:";

    // Now just listen and forward msg along to people.
    while (true) {
      struct sockaddr_storage from {};
      socklen_t from_size = sizeof(from);
      if (listen(sd_, 0) == 0) {
        client_sd_ = accept(sd_, (struct sockaddr*)&from, &from_size);
        if (client_sd_ < 0) {
          break;
        }

        // If we dont have access and havnt asked the user for it yet, ask them.
        if (!user_has_granted_access_ && g_game
            && !have_asked_user_for_access_) {
          g_game->PushAskUserForTelnetAccessCall();
          have_asked_user_for_access_ = true;
        }

        // Require password for each connection if we have one
        reading_password_ = require_password_;

        if (g_game) {
          if (reading_password_) {
            PushPrint(password_prompt);
          } else {
            PushPrint(prompt);
          }
        }
        while (true) {
          result =
              static_cast<int>(recv(client_sd_, buffer, sizeof(buffer) - 1, 0));

          // Socket closed/disconnected.
          if (result == 0 || result == -1) {
            // We got closed for whatever reason.
            if (client_sd_ != -1) {
              g_platform->CloseSocket(client_sd_);
            }
            client_sd_ = -1;
            break;
          } else {
            buffer[result] = 0;

            // Looks like these come in with '\r\n' at the end.. lets strip
            // that.
            if (result > 0 && (buffer[result - 1] == '\n')) {
              buffer[result - 1] = 0;
              if (result > 1 && (buffer[result - 2] == '\r'))
                buffer[result - 2] = 0;
            }
            if (g_game) {
              if (user_has_granted_access_) {
                if (reading_password_) {
                  if (GetRealTime() - last_try_time_ < 2000) {
                    PushPrint(
                        std::string("retried too soon; please wait a moment "
                                    "and try again.\n")
                        + password_prompt);
                  } else if (buffer == password_) {
                    reading_password_ = false;
                    PushPrint(prompt);
                  } else {
                    last_try_time_ = GetRealTime();
                    PushPrint(std::string("incorrect.\n") + password_prompt);
                  }
                } else {
                  PushTelnetScriptCommand(buffer);
                }
              } else {
                PushPrint(g_game->GetResourceString("telnetAccessDeniedText"));
              }
            }
          }
        }
      } else {
        // Listening failed; abort.
        if (sd_ != -1) {
          g_platform->CloseSocket(sd_);
        }
        break;
      }
    }

    // Sleep for a moment to keep us from running wild if we're unable to block.
    Platform::SleepMS(1000);
  }
}

#pragma clang diagnostic pop

void TelnetServer::PushTelnetScriptCommand(const std::string& command) {
  assert(g_game);
  if (g_game == nullptr) {
    return;
  }
  g_game->thread()->PushCall([this, command] {
    // These are always run in whichever context is 'visible'.
    ScopedSetContext cp(g_game->GetForegroundContext());
    if (!g_app_globals->user_ran_commands) {
      g_app_globals->user_ran_commands = true;
    }
    PythonCommand cmd(command, "<telnet>");
    if (cmd.CanEval()) {
      PyObject* obj = cmd.RunReturnObj(true, nullptr);
      if (obj && obj != Py_None) {
        PyObject* s = PyObject_Repr(obj);
        if (s) {
          const char* c = PyUnicode_AsUTF8(s);
          PushPrint(std::string(c) + "\n");
          Py_DECREF(s);
        }
        Py_DECREF(obj);
      }
    } else {
      // Not eval-able; just run it.
      cmd.Run();
    }
    PushPrint("ballisticacore> ");
  });
}

void TelnetServer::PushPrint(const std::string& s) {
  assert(g_game);
  g_game->thread()->PushCall([this, s] { Print(s); });
}

void TelnetServer::Print(const std::string& s) {
  // Currently we make the assumption that *only* the game thread writes to our
  // socket.
  assert(InLogicThread());
  if (client_sd_ != -1) {
    send(client_sd_, s.c_str(),
         static_cast_check_fit<socket_send_length_t>(s.size()), 0);
  }
}

TelnetServer::~TelnetServer() = default;

void TelnetServer::SetAccessEnabled(bool v) { user_has_granted_access_ = v; }

void TelnetServer::SetPassword(const char* password) {
  if (password != nullptr) {
    password_ = password;
    require_password_ = true;
  } else {
    require_password_ = false;
  }
}

}  // namespace ballistica
