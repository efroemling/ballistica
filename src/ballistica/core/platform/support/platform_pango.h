// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_CORE_PLATFORM_SUPPORT_PLATFORM_PANGO_H_
#define BALLISTICA_CORE_PLATFORM_SUPPORT_PLATFORM_PANGO_H_

// Pango+Cairo OS font rendering helpers.
// Shared by PlatformLinux and PlatformApple (cmake builds).

#if BA_ENABLE_OS_FONT_RENDERING

#include <pango/pangocairo.h>

#include <cstdint>
#include <cstdio>
#include <string>
#include <vector>

#include "ballistica/core/platform/platform.h"
#include "ballistica/shared/math/rect.h"

namespace ballistica::core {

static constexpr float kPangoBaseFontSize = 26.0f;
static constexpr bool kPangoDebugFontBounds = false;
static constexpr const char* kPangoFontFamily = "Sans";

struct PangoTextData_ {
  std::vector<uint8_t> pixels;
  int width{};
  int height{};
};

inline void PangoGetTextBoundsAndWidth_(const std::string& text, Rect* r,
                                        float* width) {
  cairo_surface_t* surface =
      cairo_image_surface_create(CAIRO_FORMAT_ARGB32, 1, 1);
  cairo_t* cr = cairo_create(surface);
  PangoLayout* layout = pango_cairo_create_layout(cr);
  PangoFontDescription* font_desc = pango_font_description_new();
  pango_font_description_set_family(font_desc, kPangoFontFamily);
  pango_font_description_set_weight(font_desc, PANGO_WEIGHT_MEDIUM);
  pango_font_description_set_absolute_size(
      font_desc, static_cast<int>(kPangoBaseFontSize * PANGO_SCALE));
  pango_layout_set_font_description(layout, font_desc);
  pango_font_description_free(font_desc);
  pango_layout_set_text(layout, text.c_str(), -1);
  PangoRectangle ink_rect{};
  PangoRectangle logical_rect{};
  pango_layout_get_extents(layout, &ink_rect, &logical_rect);
  float baseline =
      static_cast<float>(pango_layout_get_baseline(layout)) / PANGO_SCALE;
  r->l = static_cast<float>(ink_rect.x) / PANGO_SCALE;
  r->r = static_cast<float>(ink_rect.x + ink_rect.width) / PANGO_SCALE;
  r->t = baseline - static_cast<float>(ink_rect.y) / PANGO_SCALE;
  r->b = -(static_cast<float>(ink_rect.y + ink_rect.height) / PANGO_SCALE
           - baseline);
  *width = static_cast<float>(logical_rect.width) / PANGO_SCALE;
  if (kPangoDebugFontBounds) {
    printf(
        "GetTextBoundsAndWidth '%s': "
        "l=%.2f r=%.2f t=%.2f b=%.2f width=%.2f "
        "[baseline=%.2f ink: x=%d y=%d w=%d h=%d]\n",
        text.c_str(), r->l, r->r, r->t, r->b, *width, baseline, ink_rect.x,
        ink_rect.y, ink_rect.width, ink_rect.height);
    fflush(stdout);
  }
  g_object_unref(layout);
  cairo_destroy(cr);
  cairo_surface_destroy(surface);
}

inline auto PangoCreateTextTexture_(int width, int height,
                                    const std::vector<std::string>& strings,
                                    const std::vector<float>& positions,
                                    const std::vector<float>& widths,
                                    float scale) -> void* {
  if (kPangoDebugFontBounds) {
    printf("CreateTextTexture: %dx%d scale=%.2f strings=%zu\n", width, height,
           scale, strings.size());
    for (size_t i = 0; i < strings.size(); ++i) {
      printf("  [%zu] '%s' pos=(%.2f,%.2f) width=%.2f\n", i, strings[i].c_str(),
             positions[i * 2], positions[i * 2 + 1], widths[i]);
    }
    fflush(stdout);
  }
  cairo_surface_t* surface =
      cairo_image_surface_create(CAIRO_FORMAT_ARGB32, width, height);
  cairo_t* cr = cairo_create(surface);
  cairo_set_operator(cr, CAIRO_OPERATOR_CLEAR);
  cairo_paint(cr);
  cairo_set_operator(cr, CAIRO_OPERATOR_OVER);
  if (kPangoDebugFontBounds) {
    // Transparent red background over the whole sheet.
    cairo_set_source_rgba(cr, 1.0, 0.0, 0.0, 0.5);
    cairo_paint(cr);
  }
  cairo_set_source_rgba(cr, 1.0, 1.0, 1.0, 1.0);
  PangoFontDescription* font_desc = pango_font_description_new();
  pango_font_description_set_family(font_desc, kPangoFontFamily);
  pango_font_description_set_weight(font_desc, PANGO_WEIGHT_MEDIUM);
  pango_font_description_set_absolute_size(
      font_desc, static_cast<int>(kPangoBaseFontSize * scale * PANGO_SCALE));
  for (size_t i = 0; i < strings.size(); ++i) {
    PangoLayout* layout = pango_cairo_create_layout(cr);
    pango_layout_set_font_description(layout, font_desc);
    pango_layout_set_text(layout, strings[i].c_str(), -1);
    float baseline_offset =
        static_cast<float>(pango_layout_get_baseline(layout)) / PANGO_SCALE;
    double tx = static_cast<double>(positions[i * 2]);
    double ty = static_cast<double>(positions[i * 2 + 1] - baseline_offset);
    if (kPangoDebugFontBounds) {
      // Solid red ink bounds for this string.
      PangoRectangle ink{};
      pango_layout_get_extents(layout, &ink, nullptr);
      cairo_set_source_rgba(cr, 1.0, 0.0, 0.0, 1.0);
      cairo_rectangle(cr, tx + static_cast<double>(ink.x) / PANGO_SCALE,
                      ty + static_cast<double>(ink.y) / PANGO_SCALE,
                      static_cast<double>(ink.width) / PANGO_SCALE,
                      static_cast<double>(ink.height) / PANGO_SCALE);
      cairo_fill(cr);
      cairo_set_source_rgba(cr, 1.0, 1.0, 1.0, 1.0);
    }
    cairo_move_to(cr, tx, ty);
    pango_cairo_show_layout(cr, layout);
    g_object_unref(layout);
  }
  pango_font_description_free(font_desc);
  cairo_surface_flush(surface);
  int stride = cairo_image_surface_get_stride(surface);
  unsigned char* data = cairo_image_surface_get_data(surface);
  auto* result = new PangoTextData_();
  result->width = width;
  result->height = height;
  result->pixels.resize(static_cast<size_t>(width * height * 4));
  // Cairo ARGB32 on little-endian stores bytes as B, G, R, A.
  // Swizzle B and R to produce R, G, B, A output expected by the engine.
  for (int y = 0; y < height; ++y) {
    const uint8_t* src_row = data + y * stride;
    uint8_t* dst_row = result->pixels.data() + y * width * 4;
    for (int x = 0; x < width; ++x) {
      dst_row[x * 4 + 0] = src_row[x * 4 + 2];  // R ← Cairo B
      dst_row[x * 4 + 1] = src_row[x * 4 + 1];  // G ← Cairo G
      dst_row[x * 4 + 2] = src_row[x * 4 + 0];  // B ← Cairo R
      dst_row[x * 4 + 3] = src_row[x * 4 + 3];  // A ← Cairo A
    }
  }
  cairo_destroy(cr);
  cairo_surface_destroy(surface);
  return result;
}

inline auto PangoGetTextTextureData_(void* tex) -> uint8_t* {
  return static_cast<PangoTextData_*>(tex)->pixels.data();
}

inline void PangoFreeTextTexture_(void* tex) {
  delete static_cast<PangoTextData_*>(tex);
}

}  // namespace ballistica::core

#endif  // BA_ENABLE_OS_FONT_RENDERING
#endif  // BALLISTICA_CORE_PLATFORM_SUPPORT_PLATFORM_PANGO_H_
