// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/automation/automation.h"

#if BA_ENABLE_AUTOMATION

#include <fcntl.h>
#include <sys/stat.h>
#include <unistd.h>

#include <cerrno>
#include <cstdlib>
#include <cstring>
#include <string>
#include <utility>
#include <vector>

// Bring in stb_image_write's implementation in this single TU.
// Vendored at src/external/stb/ alongside other third-party headers;
// the project's header-guard convention check doesn't apply to
// files under src/external/.
#define STB_IMAGE_WRITE_IMPLEMENTATION
#define STB_IMAGE_WRITE_STATIC
#include "ballistica/base/app_adapter/app_adapter.h"
#include "ballistica/base/base.h"
#include "ballistica/base/graphics/gl/gl_sys.h"
#include "ballistica/base/graphics/graphics_server.h"
#include "ballistica/base/logic/logic.h"
#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging.h"
#include "ballistica/shared/foundation/event_loop.h"
#include "ballistica/shared/python/python_command.h"
#include "external/stb/stb_image_write.h"

namespace ballistica::base {

Automation::Automation(std::string fifo_path)
    : fifo_path_{std::move(fifo_path)} {
  // Create the FIFO if it doesn't exist; tolerate it pre-existing
  // (common case when the launching script created it, or a prior
  // run left it behind — FIFOs don't carry persistent data).
  struct stat st;
  if (stat(fifo_path_.c_str(), &st) != 0) {
    if (mkfifo(fifo_path_.c_str(), 0600) != 0) {
      g_core->logging->Log(LogName::kBa, LogLevel::kError,
                           std::string("Automation: failed to mkfifo at ")
                               + fifo_path_ + ": " + std::strerror(errno));
      return;
    }
  } else if (!S_ISFIFO(st.st_mode)) {
    g_core->logging->Log(
        LogName::kBa, LogLevel::kError,
        "Automation: path exists but is not a FIFO: " + fifo_path_);
    return;
  }

  // Open with O_RDWR so the reader thread doesn't see EOF when there
  // are momentarily no external writers, and so we can unblock it on
  // shutdown by simply closing the fd from the destructor.
  fifo_fd_ = open(fifo_path_.c_str(), O_RDWR);
  if (fifo_fd_ < 0) {
    g_core->logging->Log(LogName::kBa, LogLevel::kError,
                         std::string("Automation: failed to open FIFO at ")
                             + fifo_path_ + ": " + std::strerror(errno));
    return;
  }

  g_core->logging->Log(LogName::kBa, LogLevel::kInfo,
                       "Automation: listening for commands at " + fifo_path_);

  reader_thread_ = std::thread(&Automation::RunReader, this);
}

Automation::~Automation() {
  shutdown_ = true;
  if (fifo_fd_ >= 0) {
    // Closing the fd unblocks the reader thread's blocking read().
    close(fifo_fd_);
    fifo_fd_ = -1;
  }
  if (reader_thread_.joinable()) {
    reader_thread_.join();
  }
}

void Automation::RunReader() {
  std::string buffer;
  char chunk[1024];
  while (!shutdown_) {
    ssize_t n = read(fifo_fd_, chunk, sizeof(chunk));
    if (n < 0) {
      if (errno == EINTR) {
        continue;
      }
      // EBADF on shutdown (we closed the fd) is expected; everything
      // else is logged.
      if (errno != EBADF) {
        g_core->logging->Log(
            LogName::kBa, LogLevel::kError,
            std::string("Automation: read error: ") + std::strerror(errno));
      }
      break;
    }
    if (n == 0) {
      // Shouldn't happen with O_RDWR (we hold the write side) but
      // exit cleanly if it does.
      break;
    }
    buffer.append(chunk, static_cast<size_t>(n));
    // Extract complete lines.
    while (true) {
      auto pos = buffer.find('\n');
      if (pos == std::string::npos) {
        break;
      }
      std::string line = buffer.substr(0, pos);
      buffer.erase(0, pos + 1);
      // Trim trailing \r for CRLF tolerance.
      if (!line.empty() && line.back() == '\r') {
        line.pop_back();
      }
      if (!line.empty()) {
        DispatchLine(line);
      }
    }
  }
}

void Automation::DispatchLine(const std::string& line) {
  // Decode wire-level backslash escapes so multi-line Python can be
  // piped through a single FIFO line. The sender (tools/pcommand
  // test_game_cmd) encodes literal newlines as \n and literal
  // backslashes as \\; we reverse that here before handing the code
  // to PythonCommand.
  std::string decoded;
  decoded.reserve(line.size());
  for (size_t i = 0; i < line.size(); ++i) {
    if (line[i] == '\\' && i + 1 < line.size()) {
      char next = line[i + 1];
      if (next == 'n') {
        decoded += '\n';
        ++i;
        continue;
      }
      if (next == '\\') {
        decoded += '\\';
        ++i;
        continue;
      }
    }
    decoded += line[i];
  }

  // Run on the logic thread (which holds the GIL during ticks). The
  // decoded source is captured by value into the lambda since the
  // buffer it came from belongs to the reader thread.
  g_base->logic->event_loop()->PushCall([decoded]() {
    PythonCommand cmd(decoded, "<automation>");
    cmd.Exec(/*print_errors=*/true, nullptr, nullptr);
  });
}

// Helper: emit a standardized [automation] log line. Used both here
// and from Python-side helpers so external watchers can grep for one
// consistent format regardless of whether a result originated in C++
// or Python.
static void EmitAutomationLog(const std::string& tag, const std::string& status,
                              const std::string& payload) {
  std::string msg = "[automation] " + tag + " " + status;
  if (!payload.empty()) {
    msg += " " + payload;
  }
  g_core->logging->Log(LogName::kBaApp, LogLevel::kInfo, msg);
}

void Automation::CaptureScreenshot(const std::string& path,
                                   const std::string& tag) {
  // No graphics server in headless builds. Bail with a structured
  // failure rather than crashing.
  if (g_base->graphics_server == nullptr) {
    EmitAutomationLog(tag, "fail", "no_graphics_server");
    return;
  }

  // glReadPixels needs the GL context, which on Ballistica lives on
  // the main thread (SDL drives the render loop there). Pushing onto
  // the main-thread runnable queue runs us between frame draws when
  // the back buffer is in a coherent post-draw state.
  g_base->app_adapter->PushMainThreadCall([path, tag]() {
#if BA_ENABLE_OPENGL
    // Query current viewport dimensions — these are the framebuffer
    // pixel dimensions, which on retina displays is 2x the logical
    // window size.
    GLint viewport[4]{};
    glGetIntegerv(GL_VIEWPORT, viewport);
    int w = viewport[2];
    int h = viewport[3];
    if (w <= 0 || h <= 0) {
      EmitAutomationLog(tag, "fail", "bad_viewport");
      return;
    }

    // RGBA8 — 4 bytes per pixel.
    std::vector<uint8_t> pixels(static_cast<size_t>(w) * h * 4);
    glReadPixels(0, 0, w, h, GL_RGBA, GL_UNSIGNED_BYTE, pixels.data());

    // OpenGL origin is bottom-left; PNG (and most image formats) use
    // top-left. Flip rows in place.
    const size_t row_bytes = static_cast<size_t>(w) * 4;
    std::vector<uint8_t> row_swap(row_bytes);
    for (int y = 0; y < h / 2; ++y) {
      uint8_t* top = pixels.data() + y * row_bytes;
      uint8_t* bot = pixels.data() + (h - 1 - y) * row_bytes;
      std::memcpy(row_swap.data(), top, row_bytes);
      std::memcpy(top, bot, row_bytes);
      std::memcpy(bot, row_swap.data(), row_bytes);
    }

    int wrote = stbi_write_png(path.c_str(), w, h, 4, pixels.data(),
                               static_cast<int>(row_bytes));
    if (wrote == 0) {
      EmitAutomationLog(tag, "fail", "png_write_failed:" + path);
      return;
    }

    EmitAutomationLog(tag, "ok",
                      path + " " + std::to_string(w) + "x" + std::to_string(h));
#else
    EmitAutomationLog(tag, "fail", "no_gl");
#endif
  });
}

}  // namespace ballistica::base

#endif  // BA_ENABLE_AUTOMATION
