// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/automation/automation.h"

#if BA_ENABLE_AUTOMATION

#include <cctype>
#include <cstdio>
#include <cstring>
#include <string>
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
#include "ballistica/base/graphics/gl/renderer_gl.h"
#include "ballistica/base/graphics/graphics_server.h"
#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging.h"
#include "ballistica/shared/math/rect.h"
#include "external/stb/stb_image_write.h"

namespace ballistica::base {

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

// Helper: true if a path's extension (lowercased) is .jpg/.jpeg.
static auto PathIsJpeg(const std::string& path) -> bool {
  auto dot = path.rfind('.');
  if (dot == std::string::npos) {
    return false;
  }
  std::string ext = path.substr(dot + 1);
  for (auto& c : ext) {
    c = static_cast<char>(std::tolower(static_cast<unsigned char>(c)));
  }
  return ext == "jpg" || ext == "jpeg";
}

// JPEG quality for screenshot captures. Game frames are photographic
// content; ~90 keeps them visually clean at a fraction of PNG size,
// which is what makes captures cheap to move over the wire.
static const int kScreenshotJpegQuality = 90;

#if BA_ENABLE_OPENGL
// Write a small JSON sidecar next to a screenshot describing how to map
// an image pixel back to a virtual-screen coordinate (what synthesized
// input — automation_press_at_virtual etc. — consumes). Needed because
// the image is the whole framebuffer (game content plus any tv-border /
// aspect-clamp black bars) at backing-buffer resolution, while virtual
// coords live only over the content sub-rect at a different size; the
// driver can't recover the mapping from pixels alone. The device Python
// (baplus._automationsession) reads this and fills the ScreenshotEvent's
// mapping fields. Fields (all frame-relative so resolution cancels):
//   iw,ih  image pixel dims; vw,vh  virtual-screen size;
//   cl,ct,cw,ch  content rect as top-left-origin fractions [0..1] of
//   the image. Image px (px,py) -> virtual (bottom-left origin, y-up):
//     vx = vw * ((px/iw - cl) / cw)
//     vy = vh * (1 - (py/ih - ct) / ch)
static void WriteScreenshotMeta_(const std::string& image_path, int iw, int ih,
                                 float vw, float vh, float cl, float ct,
                                 float cw, float ch) {
  char buf[512];
  int n = snprintf(buf, sizeof(buf),
                   "{\"iw\":%d,\"ih\":%d,\"vw\":%.3f,\"vh\":%.3f,"
                   "\"cl\":%.6f,\"ct\":%.6f,\"cw\":%.6f,\"ch\":%.6f}\n",
                   iw, ih, vw, vh, cl, ct, cw, ch);
  if (n <= 0 || n >= static_cast<int>(sizeof(buf))) {
    return;
  }
  std::string meta_path = image_path + ".meta";
  FILE* f = fopen(meta_path.c_str(), "wb");
  if (f == nullptr) {
    return;
  }
  fwrite(buf, 1, static_cast<size_t>(n), f);
  fclose(f);
}
#endif  // BA_ENABLE_OPENGL

void Automation::CaptureScreenshot(const std::string& path,
                                   const std::string& tag) {
  // No graphics server in headless builds. Bail with a structured
  // failure rather than queueing something that will never run.
  if (g_base->graphics_server == nullptr) {
    EmitAutomationLog(tag, "fail", "no_graphics_server");
    return;
  }

  // Queue the request rather than reading here. The actual readback
  // must happen at the tail of a frame render (RunPendingCaptures,
  // called from GraphicsServer::TryRender) — the only point where the
  // window framebuffer holds a complete, coherent frame. May be called
  // from any thread, hence the lock.
  {
    auto lock = std::scoped_lock(pending_captures_mutex_);
    pending_captures_.push_back({path, tag});
  }
}

void Automation::RunPendingCaptures() {
  // Runs in the graphics context at the tail of a frame draw. Grab the
  // queue quickly under lock, then do the work outside it.
  std::vector<PendingCapture_> captures;
  {
    auto lock = std::scoped_lock(pending_captures_mutex_);
    if (pending_captures_.empty()) {
      return;
    }
    pending_captures_.swap(captures);
  }

#if BA_ENABLE_OPENGL
  assert(g_base->app_adapter->InGraphicsContext());
  auto* renderer =
      static_cast<RendererGL*>(g_base->graphics_server->renderer());

  // The renderer picks (and prepares) a framebuffer we can read
  // reliably: the offscreen backing target when one is in use (a
  // texture-backed FBO holding the complete composited frame), else a
  // GPU blit of the window's default framebuffer into a texture. Never
  // the default framebuffer directly — on ANGLE's Metal backend it's
  // the swapchain drawable, whose CPU readback tears. (GL_FRONT is also
  // out: GLES default framebuffers only allow GL_BACK.)
  GLuint read_fb;
  int w;
  int h;
  bool content_only;
  renderer->GetScreenshotReadTarget(&read_fb, &w, &h, &content_only);

  // Bind the chosen framebuffer for reading; restore the prior
  // read-binding after so we don't desync the renderer's next frame.
  GLint prev_read_fb = 0;
  glGetIntegerv(GL_READ_FRAMEBUFFER_BINDING, &prev_read_fb);
  glBindFramebuffer(GL_READ_FRAMEBUFFER, read_fb);

  std::vector<uint8_t> pixels;
  if (w > 0 && h > 0) {
    // Force the frame's GPU work to fully complete before we read, so
    // we never observe a partially-rasterized target.
    glFinish();

    // RGBA8 — 4 bytes per pixel.
    pixels.resize(static_cast<size_t>(w) * h * 4);
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
  }

  glBindFramebuffer(GL_READ_FRAMEBUFFER, prev_read_fb);

  // Gather the pixel->virtual mapping metadata for the sidecar, as
  // top-left-origin fractions of the delivered image. Where the game
  // content sits in the image depends on which framebuffer we read:
  //  - backing target (content_only): the image *is* the content
  //    region, so content fills it (0,0,1,1) and pixels map to virtual
  //    by a uniform scale.
  //  - window framebuffer (fallback): the image is the whole window, so
  //    content is the inset active_render_rect.
  // Guard against a zero-size window (mapping is then meaningless; we
  // just skip the sidecar below).
  auto* gs = g_base->graphics_server;
  const float vw = gs->screen_virtual_width();
  const float vh = gs->screen_virtual_height();
  const float win_w = gs->screen_pixel_width();
  const float win_h = gs->screen_pixel_height();
  const bool have_meta = win_w > 0.0f && win_h > 0.0f;
  float content_l = 0.0f;
  float content_t = 0.0f;
  float content_w = 1.0f;
  float content_h = 1.0f;
  if (have_meta && !content_only) {
    const Rect& rect = gs->screen_active_rect();
    content_l = rect.l / win_w;
    content_w = rect.width() / win_w;
    content_h = rect.height() / win_h;
    // rect.t is the top edge measured from the bottom (y-up); its
    // top-left-origin distance from the top is (win_h - rect.t).
    content_t = (win_h - rect.t) / win_h;
  }

  for (auto&& capture : captures) {
    const std::string& path = capture.path;
    const std::string& tag = capture.tag;
    if (w <= 0 || h <= 0) {
      EmitAutomationLog(tag, "fail", "bad_viewport");
      continue;
    }
    // The extension picks the format: .jpg/.jpeg gets lossy JPEG (the
    // right default — small enough to move over the wire), anything
    // else gets lossless PNG (for when pixel-perfect data is actually
    // needed). stb's jpg writer ignores the alpha channel of our RGBA
    // data.
    const size_t row_bytes = static_cast<size_t>(w) * 4;
    int wrote = PathIsJpeg(path)
                    ? stbi_write_jpg(path.c_str(), w, h, 4, pixels.data(),
                                     kScreenshotJpegQuality)
                    : stbi_write_png(path.c_str(), w, h, 4, pixels.data(),
                                     static_cast<int>(row_bytes));
    if (wrote == 0) {
      EmitAutomationLog(tag, "fail", "image_write_failed:" + path);
      continue;
    }
    if (have_meta) {
      WriteScreenshotMeta_(path, w, h, vw, vh, content_l, content_t, content_w,
                           content_h);
    }
    EmitAutomationLog(tag, "ok",
                      path + " " + std::to_string(w) + "x" + std::to_string(h));
  }
#else
  for (auto&& capture : captures) {
    EmitAutomationLog(capture.tag, "fail", "no_gl");
  }
#endif
}

}  // namespace ballistica::base

#endif  // BA_ENABLE_AUTOMATION
