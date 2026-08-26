// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/graphics/text/text_graphics.h"

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <list>
#include <memory>
#include <set>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

#include "ballistica/base/assets/assets_server.h"
#include "ballistica/base/base.h"
#include "ballistica/base/graphics/text/font_page_map_data.h"
#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging_macros.h"
#include "ballistica/core/platform/platform.h"
#include "ballistica/shared/foundation/event_loop.h"
#include "ballistica/shared/generic/native_stack_trace.h"
#include "ballistica/shared/generic/utils.h"

namespace ballistica::base {

// Tight alpha bounding box of each big-font glyph's ink on the legacy
// 8x8 sheet layout, in absolute normalized texture uv (v-down). The
// sheet-layout metrics built in the constructor define where each
// glyph's quad lands on screen; these bounds are what let those quads
// be tightened to the ink (dropping transparent margin) before being
// retargeted at the packed atlas. Measured from the (pre-packing)
// 4096x4096 sheet source at alpha>4; the ink is crisp enough that
// these barely move between alpha thresholds 1 and 128. Slots 45-63 of
// the 8x8 sheet are unused (all-empty).
struct BigGlyphInkBounds {
  float u_min;
  float u_max;
  float v_min;
  float v_max;
};
const BigGlyphInkBounds kBigGlyphInkBounds[64] = {
    {0.010498f, 0.087646f, 0.000000f, 0.114746f},  // 0
    {0.157471f, 0.209961f, 0.009277f, 0.113525f},  // 1
    {0.281006f, 0.333740f, 0.003906f, 0.116211f},  // 2
    {0.406494f, 0.459961f, 0.007568f, 0.112549f},  // 3
    {0.532715f, 0.571533f, 0.007080f, 0.109863f},  // 4
    {0.659424f, 0.696289f, 0.007080f, 0.111816f},  // 5
    {0.784668f, 0.835938f, 0.008545f, 0.110596f},  // 6
    {0.908447f, 0.958740f, 0.008057f, 0.111084f},  // 7
    {0.032471f, 0.057373f, 0.127197f, 0.233154f},  // 8
    {0.155762f, 0.203613f, 0.133057f, 0.234863f},  // 9
    {0.281006f, 0.335449f, 0.136719f, 0.234863f},  // 10
    {0.406494f, 0.450439f, 0.132324f, 0.237061f},  // 11
    {0.533691f, 0.599609f, 0.133545f, 0.236328f},  // 12
    {0.658691f, 0.708496f, 0.133301f, 0.234375f},  // 13
    {0.785156f, 0.832520f, 0.130371f, 0.233398f},  // 14
    {0.908447f, 0.955566f, 0.134033f, 0.233887f},  // 15
    {0.036133f, 0.085205f, 0.258545f, 0.371826f},  // 16
    {0.158447f, 0.206543f, 0.258301f, 0.359131f},  // 17
    {0.284912f, 0.329102f, 0.259277f, 0.359375f},  // 18
    {0.406494f, 0.453613f, 0.259277f, 0.357910f},  // 19
    {0.533691f, 0.583984f, 0.257568f, 0.357422f},  // 20
    {0.655762f, 0.707031f, 0.256348f, 0.360352f},  // 21
    {0.779785f, 0.857910f, 0.254639f, 0.358887f},  // 22
    {0.902832f, 0.950439f, 0.258057f, 0.358154f},  // 23
    {0.033936f, 0.078369f, 0.382080f, 0.486816f},  // 24
    {0.158447f, 0.198975f, 0.384521f, 0.484863f},  // 25
    {0.281738f, 0.325684f, 0.382080f, 0.485840f},  // 26
    {0.408447f, 0.440918f, 0.384521f, 0.484375f},  // 27
    {0.533447f, 0.575928f, 0.381592f, 0.484131f},  // 28
    {0.659424f, 0.701172f, 0.379150f, 0.486084f},  // 29
    {0.778809f, 0.833496f, 0.385986f, 0.487793f},  // 30
    {0.906738f, 0.952393f, 0.383057f, 0.486084f},  // 31
    {0.033691f, 0.076660f, 0.505127f, 0.610840f},  // 32
    {0.158447f, 0.199707f, 0.507080f, 0.607666f},  // 33
    {0.283447f, 0.325684f, 0.506592f, 0.612793f},  // 34
    {0.408447f, 0.450684f, 0.507568f, 0.611816f},  // 35
    {0.532471f, 0.557617f, 0.506592f, 0.610352f},  // 36
    {0.658691f, 0.700439f, 0.503662f, 0.610840f},  // 37
    {0.780029f, 0.803223f, 0.585693f, 0.608887f},  // 38
    {0.907959f, 0.941895f, 0.556396f, 0.572754f},  // 39
    {0.031250f, 0.053467f, 0.666748f, 0.734375f},  // 40
    {0.159424f, 0.230713f, 0.653809f, 0.725830f},  // 41
    {0.285645f, 0.350098f, 0.650391f, 0.720947f},  // 42
    {0.407471f, 0.432617f, 0.630859f, 0.735107f},  // 43
    {0.600586f, 0.618164f, 0.662109f, 0.717285f},  // 44
    {0.0f, 0.0f, 0.0f, 0.0f},                      // 45
    {0.0f, 0.0f, 0.0f, 0.0f},                      // 46
    {0.0f, 0.0f, 0.0f, 0.0f},                      // 47
    {0.0f, 0.0f, 0.0f, 0.0f},                      // 48
    {0.0f, 0.0f, 0.0f, 0.0f},                      // 49
    {0.0f, 0.0f, 0.0f, 0.0f},                      // 50
    {0.0f, 0.0f, 0.0f, 0.0f},                      // 51
    {0.0f, 0.0f, 0.0f, 0.0f},                      // 52
    {0.0f, 0.0f, 0.0f, 0.0f},                      // 53
    {0.0f, 0.0f, 0.0f, 0.0f},                      // 54
    {0.0f, 0.0f, 0.0f, 0.0f},                      // 55
    {0.0f, 0.0f, 0.0f, 0.0f},                      // 56
    {0.0f, 0.0f, 0.0f, 0.0f},                      // 57
    {0.0f, 0.0f, 0.0f, 0.0f},                      // 58
    {0.0f, 0.0f, 0.0f, 0.0f},                      // 59
    {0.0f, 0.0f, 0.0f, 0.0f},                      // 60
    {0.0f, 0.0f, 0.0f, 0.0f},                      // 61
    {0.0f, 0.0f, 0.0f, 0.0f},                      // 62
    {0.0f, 0.0f, 0.0f, 0.0f},                      // 63
};

// Sampled uv rect of each glyph in the packed big-font atlas
// (babuiltinassets textures/font_big). Generated (2026-07) by a scratch
// shelf-packer from the 8192 master: each glyph resampled at a uniform
// 0.9432x of master resolution (1.886x the old 4096 sheet) and packed
// into 4096x4096 at 82.9 percent utilization. Zeroed slots draw
// nothing (space, unused sheet cells).
//
// What got packed is each glyph's EXACT tightened sampled window (the
// ink+margin window computed in the constructor below), NOT the raw
// ink bbox. That distinction matters: where the original sheet metrics
// already clipped a glyph (slot 0, 'A' -- ink runs past the sampled
// window on two sides), ink+margin is wider than the tightened window,
// and packing anything else would map a different slice of art into
// the quad and render the glyph shrunk. Because the packed content
// matches the tightened window 1:1, the constructor can reuse the
// tightened quad geometry verbatim and just swap in these uvs. If the
// atlas is ever re-packed, regenerate these from the constructor's
// tightened windows (dump gb tex bounds per glyph) the same way.
const BigGlyphInkBounds kBigGlyphPackedUVs[64] = {
    {0.207520f, 0.333496f, 0.000000f, 0.220215f},  // 0
    {0.000000f, 0.106934f, 0.230713f, 0.443115f},  // 1
    {0.100098f, 0.207520f, 0.000000f, 0.222656f},  // 2
    {0.420654f, 0.529541f, 0.000000f, 0.213867f},  // 3
    {0.913086f, 0.993896f, 0.230713f, 0.440186f},  // 4
    {0.711426f, 0.788574f, 0.000000f, 0.213379f},  // 5
    {0.246826f, 0.351318f, 0.443115f, 0.651123f},  // 6
    {0.582520f, 0.685059f, 0.230713f, 0.440674f},  // 7
    {0.657471f, 0.711914f, 0.443115f, 0.650146f},  // 8
    {0.462646f, 0.560547f, 0.443115f, 0.650635f},  // 9
    {0.636475f, 0.747314f, 0.651855f, 0.851807f},  // 10
    {0.529541f, 0.619873f, 0.000000f, 0.213379f},  // 11
    {0.778809f, 0.913086f, 0.230713f, 0.440186f},  // 12
    {0.711914f, 0.813477f, 0.443115f, 0.648926f},  // 13
    {0.560547f, 0.657471f, 0.443115f, 0.650391f},  // 14
    {0.272217f, 0.368652f, 0.651855f, 0.855225f},  // 15
    {0.000000f, 0.100098f, 0.000000f, 0.230713f},  // 16
    {0.813477f, 0.911865f, 0.443115f, 0.648438f},  // 17
    {0.083984f, 0.174805f, 0.651855f, 0.855713f},  // 18
    {0.540039f, 0.636475f, 0.651855f, 0.852783f},  // 19
    {0.437500f, 0.540039f, 0.651855f, 0.855225f},  // 20
    {0.372314f, 0.476807f, 0.230713f, 0.441895f},  // 21
    {0.087646f, 0.246826f, 0.443115f, 0.651367f},  // 22
    {0.174805f, 0.272217f, 0.651855f, 0.855713f},  // 23
    {0.619873f, 0.711182f, 0.000000f, 0.213379f},  // 24
    {0.000000f, 0.083984f, 0.651855f, 0.856201f},  // 25
    {0.281738f, 0.372070f, 0.230713f, 0.442139f},  // 26
    {0.368652f, 0.437500f, 0.651855f, 0.855225f},  // 27
    {0.000000f, 0.087646f, 0.443115f, 0.651855f},  // 28
    {0.788330f, 0.874512f, 0.000000f, 0.212646f},  // 29
    {0.351318f, 0.462646f, 0.443115f, 0.650635f},  // 30
    {0.685059f, 0.778809f, 0.230713f, 0.440674f},  // 31
    {0.193115f, 0.281738f, 0.230713f, 0.442871f},  // 32
    {0.911621f, 0.997070f, 0.443115f, 0.647949f},  // 33
    {0.333496f, 0.420654f, 0.000000f, 0.215820f},  // 34
    {0.874756f, 0.961914f, 0.000000f, 0.212402f},  // 35
    {0.476807f, 0.529785f, 0.230713f, 0.441895f},  // 36
    {0.106934f, 0.193115f, 0.230713f, 0.442871f},  // 37
    {0.180664f, 0.231934f, 0.856201f, 0.907471f},  // 38
    {0.232178f, 0.303711f, 0.856201f, 0.894531f},  // 39
    {0.131348f, 0.180908f, 0.856201f, 0.993896f},  // 40
    {0.747314f, 0.892578f, 0.651855f, 0.798584f},  // 41
    {0.000000f, 0.131348f, 0.856201f, 1.000000f},  // 42
    {0.529785f, 0.582764f, 0.230713f, 0.441406f},  // 43
    {0.0f, 0.0f, 0.0f, 0.0f},                      // 44
    {0.0f, 0.0f, 0.0f, 0.0f},                      // 45
    {0.0f, 0.0f, 0.0f, 0.0f},                      // 46
    {0.0f, 0.0f, 0.0f, 0.0f},                      // 47
    {0.0f, 0.0f, 0.0f, 0.0f},                      // 48
    {0.0f, 0.0f, 0.0f, 0.0f},                      // 49
    {0.0f, 0.0f, 0.0f, 0.0f},                      // 50
    {0.0f, 0.0f, 0.0f, 0.0f},                      // 51
    {0.0f, 0.0f, 0.0f, 0.0f},                      // 52
    {0.0f, 0.0f, 0.0f, 0.0f},                      // 53
    {0.0f, 0.0f, 0.0f, 0.0f},                      // 54
    {0.0f, 0.0f, 0.0f, 0.0f},                      // 55
    {0.0f, 0.0f, 0.0f, 0.0f},                      // 56
    {0.0f, 0.0f, 0.0f, 0.0f},                      // 57
    {0.0f, 0.0f, 0.0f, 0.0f},                      // 58
    {0.0f, 0.0f, 0.0f, 0.0f},                      // 59
    {0.0f, 0.0f, 0.0f, 0.0f},                      // 60
    {0.0f, 0.0f, 0.0f, 0.0f},                      // 61
    {0.0f, 0.0f, 0.0f, 0.0f},                      // 62
    {0.0f, 0.0f, 0.0f, 0.0f},                      // 63
};

// How much uv padding to keep outside the measured ink when
// tightening glyph windows.
//
// This can't be a small fixed number of texels. The ink bounds are
// measured on the top mip, but a glyph drawn small samples a coarse mip
// where one texel covers 2^level source texels, and bilinear reaches a
// full mip-texel past the edge -- at mip 5 that's ~32 source texels
// (~0.008 uv here), far outside a 2-texel margin. Cutting the quad
// inside that bleed slices the soft filtered edge off with a hard line.
//
// So the buffer scales with the glyph: a fraction of each axis's own ink
// extent (which tracks how much mip headroom that glyph has), with an
// absolute floor so small glyphs like '.' and ':' -- where a percentage
// of a tiny extent would be nothing -- still get real padding. Both are
// knobs; raise them if anything looks cut at small sizes.
const float kBigGlyphInkMarginFrac = 0.04f;
const float kBigGlyphInkMarginMin = 0.002f;

// Boot-time OS-text warm-up is currently DISABLED: we can never
// exhaustively pre-load every script that may appear in online content
// (player names, chat, etc.), so lazy per-script font loads need to be
// made non-hitching *structurally* — background measuring/prep, as the
// credits window does — rather than papered over for a hand-picked set
// that would leave the uncovered scripts getting less attention. A
// short delay before such text first appears is fine; a frame hitch is
// not. Also, players who never encounter a given script (likely a
// substantial number for any specific one) shouldn't pay its load cost.
// The machinery stays wired so a more *targeted* warm-up (emoji-only,
// or driven by the user's own locale) can be enabled later if desired.
constexpr bool kEnableOSTextWarmUp{false};

void TextGraphics::WarmUpOSText() {
  if (!kEnableOSTextWarmUp) {
    return;
  }
  if (!g_buildconfig.enable_os_font_rendering()) {
    return;
  }
  g_base->assets_server->event_loop()->PushCall([] {
    millisecs_t start = g_core->AppTimeMillisecs();
    // A measure call on text the engine has no glyphs for (CJK here)
    // forces the backend's full one-time init (font-map build, font
    // loads). Multiple scripts pull in a couple of fallback fonts
    // while we're at it.
    Rect r;
    float width{};
    g_core->platform->GetTextBoundsAndWidth(
        "\xe6\x96\x87\xe5\xad\x97\xe3\x83\x86\xe3\x82\xb9"
        "\xe3\x83\x88\xed\x95\x9c\xea\xb8\x80",
        &r, &width);
    g_core->logging->Log(LogName::kBaPerformance, LogLevel::kDebug, [start] {
      return "os-text warm-up took "
             + std::to_string(g_core->AppTimeMillisecs() - start) + "ms";
    });
  });
}

TextGraphics::TextGraphics() {
  // Init glyph values for our custom font pages.
  for (int page = 0; page < kFontExtrasPages; page++) {
    for (int x = 0; x < kFontExtrasColumns; x++) {
      for (int y = 0; y < kFontExtrasRows; y++) {
        int index = kFontExtrasColumns * kFontExtrasRows * page
                    + y * kFontExtrasColumns + x;
        Glyph& g(glyphs_extras_[index]);

        float extra_advance = 0.0f;

        g.pen_offset_x = 0.1f;
        g.pen_offset_y = -0.2f;

        g.x_size = 1.0f;
        g.y_size = 1.0f;

        // Euro symbol should be a bit smaller.
        if (index == 0) {
          g.x_size = 0.8f;
          g.y_size = 0.8f;
        }

        // Move all arrows down a bit.
        if (index > 0 && index < 5) {
          g.pen_offset_y -= 0.1f;
        }

        // Bring Fast Forward & Rewind down and to the left a bit.
        if (index == 13 || index == 15) {
          g.pen_offset_y -= 0.055;
          g.pen_offset_x -= 0.01;
        }

        // Shrink account logos and move them up a bit.
        if (index == 32 || index == 33 || index == 38 || index == 40
            || index == 48 || index == 49) {
          g.pen_offset_y += 0.4f;
          extra_advance += 0.08f;
          g.x_size *= 0.55f;
          g.y_size *= 0.55f;
        }

        // Same with the logo and most icons on sheets 3, 4, and 5.
        if (index == 30 || (index >= 50 && index < 99)
            || (index >= 100 && index < 125)) {
          // A few are *extra* big.
          if (index == 67 || index == 65 || index == 70 || index == 72
              || index == 73 || index == 75 || index == 76 || index == 78
              || index == 79 || index == 100 || index == 101 || index == 102
              || index == 103) {
            g.pen_offset_y += 0.31f;
            if (index == 70) {
              g.pen_offset_y -= 0.02f;
            }
            extra_advance += 0.04f;
            g.x_size *= 0.75f;
            g.y_size *= 0.75f;

            // potato!
            if (index == 101) {
              g.x_size *= 1.2f;
              g.y_size *= 1.2f;
              extra_advance += 0.05f;
              g.pen_offset_y -= 0.1f;
            }
            // palm tree
            // if (index == 102) {
            // g.x_size *= 1.2f;
            // g.y_size *= 1.2f;
            // extra_advance += 0.05f;
            // g.pen_offset_y -= 0.1f;
            // }
            // boxing glove
            if (index == 103) {
              // g.x_size *= 1.1f;
              // g.y_size *= 1.1f;
              extra_advance += 0.08f;
              // g.pen_offset_y -= 0.1f;
            }
          } else {
            g.pen_offset_y += 0.4f;
            extra_advance += 0.08f;
            g.x_size *= 0.55f;
            g.y_size *= 0.55f;
          }
        }
        // Special handling of tokens icon.
        if (index == 29) {
          extra_advance += 0.12f;
        }

        // Special case for v2 logo.
        if (index == 99) {
          g.pen_offset_y += 0.25f;
          extra_advance += 0.12f;
          g.x_size *= 0.75f;
          g.y_size *= 0.75f;
        }
        g.advance = g.x_size - 0.09f + extra_advance;

        // Ticket overlay should be big and shouldn't advance us at all.
        if (index == 41) {
          g.x_size *= 1.1f;
          g.y_size *= 1.1f;
          g.pen_offset_x -= 0.3f;
          g.pen_offset_y -= 0.1f;
          g.advance = 0;
        }

        // Trophies should be big.
        if (index >= 42 && index <= 47) {
          float s = 1.5f;
          g.x_size *= s;
          g.y_size *= s;
          g.pen_offset_x -= 0.07f;
          g.pen_offset_y -= 0.2f;
          g.advance *= s;
        }

        // Up/down arrows are a bit thinner.
        if (index == 3 || index == 4) {
          g.advance -= 0.3f;
          g.pen_offset_x -= 0.15f;
        }

        g.tex_min_x = 0.2f * static_cast<float>(x);
        g.tex_min_y = 0.2f * static_cast<float>(y + 1);
        g.tex_max_x = 0.2f * static_cast<float>(x + 1);
        g.tex_max_y = 0.2f * static_cast<float>(y);
      }
    }
  }

  // Init glyph values for our big font page (a 8x8 array).
  {
    float x_offs = 0.009f;
    float y_offs = 0.0059f;
    float scale_extra = -0.012f;
    for (int x = 0; x < 8; x++) {
      for (int y = 0; y < 8; y++) {
        int c = y * 8 + x;
        Glyph& g(glyphs_big_[c]);
        g.pen_offset_x = 0.05f;
        g.pen_offset_y = -0.215f;
        float w = 0.41f;
        float bot_offset = 0.0f;
        float left_offset = 0.0f;
        float right_offset = 0.0f;
        float top_offset = 0.0f;
        switch (c) {
          case 0:  // NOLINT(bugprone-branch-clone)
            w = 0.415f;
            break;  // A
          case 1:
            w = 0.415f;
            break;  // B
          case 2:
            w = 0.40f;
            break;  // C
          case 4:
            w = 0.315f;
            break;  // E
          case 5:
            w = 0.31f;
            break;  // F
          case 7:
            w = 0.42f;
            break;  // H
          case 8:
            w = 0.215f;
            break;  // I
          case 9:
            w = 0.38f;
            break;  // J
          case 10:
            w = 0.42f;
            break;  // K
          case 11:
            w = 0.345f;
            break;  // L
          case 12:
            w = 0.56f;
            break;  // M
          case 13:
            w = 0.42f;
            break;  // N
          case 15:
            w = 0.38f;
            break;  // P
          case 16:
            bot_offset = 0.07f;
            break;  // Q
          case 18:  // NOLINT(bugprone-branch-clone)
            w = 0.375f;
            break;  // S
          case 19:
            w = 0.375f;
            break;  // T
          case 20:
            w = 0.43f;
            break;  // U
          case 21:
            w = 0.42f;
            break;  // V
          case 22:
            w = 0.625f;
            break;  // W
          case 23:
            w = 0.36f;
            break;  // X
          case 24:
            w = 0.4f;
            break;  // Y
          case 25:
            w = 0.34f;
            break;  // Z
          case 26:
            w = 0.37f;
            break;  // 0
          case 27:
            w = 0.28f;
            break;  // 1
          case 28:  // NOLINT(bugprone-branch-clone)
            w = 0.37f;
            break;  // 2
          case 29:
            w = 0.37f;
            break;  // 3
          case 30:
            w = 0.37f;
            break;  // 4
          case 31:
            w = 0.37f;
            break;  // 5
          case 32:  // NOLINT(bugprone-branch-clone)
            w = 0.36f;
            break;  // 6
          case 33:
            w = 0.36f;
            break;  // 7
          case 34:  // NOLINT(bugprone-branch-clone)
            w = 0.37f;
            break;  // 8
          case 35:
            w = 0.37f;
            break;  // 9
          case 36:
            w = 0.18f;
            break;  // !
          case 37:
            w = 0.35f;
            break;  // ?
          case 38:
            w = 0.21f;
            top_offset = -0.72f;
            break;  // .
          case 39:
            w = 0.30f;
            top_offset = -0.44f;
            bot_offset = -0.3f;
            break;  // -
          case 40:
            w = 0.20f;
            top_offset = -0.3f;
            bot_offset = 0.0f;
            break;  // :
          case 41:
            w = 0.6f;
            top_offset = -0.19f;
            bot_offset = -0.1f;
            break;  // %
          case 42:
            w = 0.54f;
            top_offset = -0.16f;
            bot_offset = -0.1f;
            break;  // #
          case 43:  // NOLINT(bugprone-branch-clone)
            w = 0.18f;
            break;  // upside-down !
          case 44:
            w = 0.18f;
            break;  // space
          default:
            break;
        }
        bot_offset += 0.04f;
        right_offset += 0.04f;
        top_offset += 0.03f;
        left_offset += 0.03f;

        g.advance = w * 1.15f;
        g.x_size = 1.03f;
        g.y_size = 1.03f;
        g.tex_min_x = (1.0f / 8.0f) * static_cast<float>(x) + x_offs;
        g.tex_min_y =
            (1.0f / 8.0f) * static_cast<float>(y + 1) + y_offs + scale_extra;
        g.tex_max_x =
            (1.0f / 8.0f) * static_cast<float>(x + 1) + x_offs + scale_extra;
        g.tex_max_y = (1.0f / 8.0f) * static_cast<float>(y) + y_offs;

        // Just scooted letters over; account for that.
        float foo_x = 0.0183f;
        float foo_y = 0.000f;
        g.tex_min_x += foo_x;
        g.tex_max_x += foo_x;
        g.tex_min_y += foo_y;
        g.tex_max_y += foo_y;

        // Clamp based on char width.
        float scale = w * 1.32f;
        g.x_size *= scale;
        g.tex_max_x = g.tex_min_x + (g.tex_max_x - g.tex_min_x) * scale;

        // Add bot offset.
        if (bot_offset != 0.0f) {
          g.tex_min_y = g.tex_max_y
                        + (g.tex_min_y - g.tex_max_y)
                              * ((g.y_size + bot_offset) / g.y_size);
          g.pen_offset_y -= bot_offset;
          g.y_size += bot_offset;
        }
        // Add left offset.
        if (left_offset != 0.0f) {
          g.tex_min_x = g.tex_max_x
                        + (g.tex_min_x - g.tex_max_x)
                              * ((g.x_size + left_offset) / g.x_size);
          g.pen_offset_x -= left_offset;
          g.x_size += left_offset;
        }
        // Add right offset.
        if (right_offset != 0.0f) {
          g.tex_max_x = g.tex_min_x
                        + (g.tex_max_x - g.tex_min_x)
                              * ((g.x_size + right_offset) / g.x_size);
          g.x_size += right_offset;
        }
        // Add top offset.
        if (top_offset != 0.0f) {
          g.tex_max_y = g.tex_min_y
                        + (g.tex_max_y - g.tex_min_y)
                              * ((g.y_size + top_offset) / g.y_size);
          g.y_size += top_offset;
        }

        if (g.tex_max_x > 1.0f || g.tex_max_x < 0.0f || g.tex_min_x > 1.0
            || g.tex_min_x < 0.0f || g.tex_max_y > 1.0f || g.tex_max_y < 0.0
            || g.tex_min_y > 1.0f || g.tex_min_y < 0.0f) {
          BA_LOG_ONCE(LogName::kBaGraphics, LogLevel::kWarning,
                      "glyph bounds error");
        }

        // The sheet-layout metrics just built for ``g`` define where the
        // glyph's quad lands on screen, but the atlas we actually ship is
        // packed (see kBigGlyphPackedUVs). Finalize the glyph in two
        // steps: shrink the quad and its sampled uv window in lockstep
        // down to the measured ink (plus margin) so only transparent
        // margin is dropped -- every remaining texel lands at the exact
        // same spot on screen, and advance is untouched so nothing
        // reflows -- then swap the sampled uvs for the glyph's rect in
        // the packed atlas, which holds exactly that tightened window's
        // content. Space and the unused sheet slots collapse to zero
        // size so the mesh builder skips their quads entirely.
        {
          Glyph gt = g;
          const BigGlyphInkBounds& ink(kBigGlyphInkBounds[c]);
          const BigGlyphInkBounds& puv(kBigGlyphPackedUVs[c]);

          // Per-axis buffer; see kBigGlyphInkMarginFrac above.
          float mx = std::max(kBigGlyphInkMarginMin,
                              (ink.u_max - ink.u_min) * kBigGlyphInkMarginFrac);
          float my = std::max(kBigGlyphInkMarginMin,
                              (ink.v_max - ink.v_min) * kBigGlyphInkMarginFrac);

          // X: tex_min_x is the left edge, tex_max_x the right.
          float left = std::max(g.tex_min_x, ink.u_min - mx);
          float right = std::min(g.tex_max_x, ink.u_max + mx);
          float u_span = g.tex_max_x - g.tex_min_x;

          // Y: note v is flipped -- tex_min_y is the *bottom* of the glyph
          // and holds the larger v; tex_max_y is the top with the smaller.
          float bot = std::min(g.tex_min_y, ink.v_max + my);
          float top = std::max(g.tex_max_y, ink.v_min - my);
          float v_span = g.tex_max_y - g.tex_min_y;

          if (!(left < right && top < bot)
              || !(puv.u_max > puv.u_min && puv.v_max > puv.v_min)) {
            // No ink inside the sheet window (the space glyph, whose
            // narrow window lands on a blank part of its cell, and the
            // unused slots) or nothing packed for this slot: collapse to
            // a zero-size glyph that still advances the pen.
            gt.x_size = 0.0f;
            gt.y_size = 0.0f;
          } else if (std::abs(u_span) > 0.0f && std::abs(v_span) > 0.0f) {
            float s_left = (left - g.tex_min_x) / u_span;
            float s_right = (right - g.tex_min_x) / u_span;
            float t_bot = (bot - g.tex_min_y) / v_span;
            float t_top = (top - g.tex_min_y) / v_span;

            gt.pen_offset_x = g.pen_offset_x + g.x_size * s_left;
            gt.x_size = g.x_size * (s_right - s_left);
            gt.pen_offset_y = g.pen_offset_y + g.y_size * t_bot;
            gt.y_size = g.y_size * (t_top - t_bot);
            gt.tex_min_x = puv.u_min;
            gt.tex_max_x = puv.u_max;
            // v is flipped in glyph space: tex_min_y is the bottom.
            gt.tex_min_y = puv.v_max;
            gt.tex_max_y = puv.v_min;
          }
          g = gt;
        }
      }
    }
  }
}

static auto GetBigGlyphIndex(uint32_t char_val) -> int {
  int index;
  switch (char_val) {
    case 'A':
    case 'a':
    case 0x00C0:
    case 0x00E0:
    case 0x00C1:
    case 0x00E1:
    case 0x00C2:
    case 0x00E2:
    case 0x00C3:
    case 0x00E3:
    case 0x00C4:
    case 0x00E4:
    case 0x00C5:
    case 0x00E5:
    case 0x0100:
    case 0x0101:
    case 0x0102:
    case 0x0103:
    case 0x0104:
    case 0x0105:
      index = 0;
      break;
    case 'B':
    case 'b':
      index = 1;
      break;
    case 'C':
    case 'c':
    case 0x0106:
    case 0x0107:
    case 0x0108:
    case 0x0109:
    case 0x010A:
    case 0x010B:
    case 0x010C:
    case 0x010D:
      index = 2;
      break;
    case 'D':
    case 'd':
    case 0x00D0:
    case 0x010E:
    case 0x010F:
    case 0x0110:
    case 0x0111:
      index = 3;
      break;
    case 'E':
    case 'e':
    case 0x00C8:
    case 0x00E8:
    case 0x00C9:
    case 0x00E9:
    case 0x00CA:
    case 0x00EA:
    case 0x00CB:
    case 0x00EB:
    case 0x0112:
    case 0x0113:
    case 0x0114:
    case 0x0115:
    case 0x0116:
    case 0x0117:
    case 0x0118:
    case 0x0119:
    case 0x011A:
    case 0x011B:
      index = 4;
      break;
    case 'F':
    case 'f':
      index = 5;
      break;
    case 'G':
    case 'g':
    case 0x011C:
    case 0x011D:
    case 0x011E:
    case 0x011F:
    case 0x0120:
    case 0x0121:
    case 0x0122:
    case 0x0123:
      index = 6;
      break;
    case 'H':
    case 'h':
    case 0x0124:
    case 0x0125:
    case 0x0126:
    case 0x0127:
      index = 7;
      break;
    case 'I':
    case 'i':
    case 0x00CD:
    case 0x00ED:
    case 0x00CE:
    case 0x00EE:
    case 0x00CF:
    case 0x00EF:
    case 0x0128:
    case 0x0129:
    case 0x012A:
    case 0x012B:
    case 0x012C:
    case 0x012D:
    case 0x012E:
    case 0x012F:
    case 0x0130:
      index = 8;
      break;
    case 'J':
    case 'j':
    case 0x0134:
    case 0x0135:
      index = 9;
      break;
    case 'K':
    case 'k':
    case 0x0136:
    case 0x0137:
    case 0x0138:
      index = 10;
      break;
    case 'L':
    case 'l':
    case 0x0139:
    case 0x013A:
    case 0x013B:
    case 0x013C:
    case 0x013D:
    case 0x013E:
    case 0x013F:
    case 0x0140:
    case 0x0141:
    case 0x0142:
      index = 11;
      break;
    case 'M':
    case 'm':
      index = 12;
      break;
    case 'N':
    case 'n':
    case 0x00D1:
    case 0x00F1:
    case 0x0143:
    case 0x0144:
    case 0x0145:
    case 0x0146:
    case 0x0147:
    case 0x0148:
    case 0x0149:
    case 0x014A:
    case 0x014B:
      index = 13;
      break;
    case 'O':
    case 'o':
    case 0x00D2:
    case 0x00F2:
    case 0x00D3:
    case 0x00F3:
    case 0x00D4:
    case 0x00F4:
    case 0x00D5:
    case 0x00F5:
    case 0x00D6:
    case 0x00F6:
    case 0x014C:
    case 0x014D:
    case 0x014E:
    case 0x014F:
    case 0x0150:
    case 0x0151:
      index = 14;
      break;
    case 'P':
    case 'p':
      index = 15;
      break;
    case 'Q':
    case 'q':
      index = 16;
      break;
    case 'R':
    case 'r':
    case 0x0154:
    case 0x0155:
    case 0x0156:
    case 0x0157:
    case 0x0158:
    case 0x0159:
      index = 17;
      break;
    case 'S':
    case 's':
    case 0x015A:
    case 0x015B:
    case 0x015C:
    case 0x015D:
    case 0x015E:
    case 0x015F:
    case 0x0160:
    case 0x0161:
      index = 18;
      break;
    case 'T':
    case 't':
    case 0x0162:
    case 0x0163:
    case 0x0164:
    case 0x0165:
    case 0x0166:
    case 0x0167:
      index = 19;
      break;
    case 'U':
    case 'u':
    case 0x00D9:
    case 0x00F9:
    case 0x00DA:
    case 0x00FA:
    case 0x00DB:
    case 0x00FB:
    case 0x00DC:
    case 0x00FC:
    case 0x0168:
    case 0x0169:
    case 0x016A:
    case 0x016B:
    case 0x016C:
    case 0x016D:
    case 0x016E:
    case 0x016F:
    case 0x0170:
    case 0x0171:
    case 0x0172:
    case 0x0173:
      index = 20;
      break;
    case 'V':
    case 'v':
      index = 21;
      break;
    case 'W':
    case 'w':
    case 0x0174:
    case 0x0175:
      index = 22;
      break;
    case 'X':
    case 'x':
      index = 23;
      break;
    case 'Y':
    case 'y':
    case 0x00DD:
    case 0x00FD:
    case 0x00FF:
    case 0x0176:
    case 0x0177:
    case 0x0178:
      index = 24;
      break;
    case 'Z':
    case 'z':
    case 0x0179:
    case 0x017A:
    case 0x017B:
    case 0x017C:
    case 0x017D:
    case 0x017E:
      index = 25;
      break;
    case '0':
      index = 26;
      break;
    case '1':
      index = 27;
      break;
    case '2':
      index = 28;
      break;
    case '3':
      index = 29;
      break;
    case '4':
      index = 30;
      break;
    case '5':
      index = 31;
      break;
    case '6':
      index = 32;
      break;
    case '7':
      index = 33;
      break;
    case '8':
      index = 34;
      break;
    case '9':
      index = 35;
      break;
    case '!':
      index = 36;
      break;
    case '?':
      index = 37;
      break;
    case '.':
      index = 38;
      break;
    case '-':
      index = 39;
      break;
    case ':':
      index = 40;
      break;
    case '%':
      index = 41;
      break;
    case '#':
      index = 42;
      break;
    case 161:
      index = 43;
      break;  // upside-down !
    case ' ':
      index = 44;
      break;
    default:
      index = -1;
      break;
  }
  return index;
}

auto TextGraphics::GetBigCharIndex(int c) -> int {
  int index;
  if (c >= 'a' && c <= 'z') {
    index = c - 'a';
  } else if (c >= 'A' && c <= 'Z') {
    index = c - 'A';
  } else if (c >= '0' && c <= '9') {
    index = c - '0' + 26;
  } else {
    switch (c) {
      case '!':
        index = 36;
        break;
      case '?':
        index = 37;
        break;
      case '.':
        index = 38;
        break;
      case '-':
        index = 39;
        break;
      case ':':
        index = 40;
        break;
      case '%':
        index = 41;
        break;
      case '#':
        index = 42;
        break;

      case 192:
      case 193:
      case 194:
      case 195:
      case 196:
      case 197:
      case 198:
        index = 'a' - 'a';
        break;
      case 199:
        index = 'c' - 'a';
        break;
      case 200:
      case 201:
      case 202:
      case 203:
        index = 'e' - 'a';
        break;
      case 204:
      case 205:
      case 206:
      case 207:
        index = 'i' - 'a';
        break;
      case 208:
        index = 'd' - 'a';
        break;
      case 209:
        index = 'n' - 'a';
        break;
      case 210:
      case 211:
      case 212:
      case 213:
      case 216:
        index = 'o' - 'a';
        break;
      case 217:
      case 218:
      case 219:
      case 220:
        index = 'u' - 'a';
        break;
      case 221:
        index = 'y' - 'a';
        break;
      case 224:
      case 225:
      case 226:
      case 227:
      case 228:
      case 229:
      case 230:
        index = 'a' - 'a';
        break;
      case 231:
        index = 'c' - 'a';
        break;
      case 232:
      case 233:
      case 234:
      case 235:
        index = 'e' - 'a';
        break;
      case 236:
      case 237:
      case 238:
      case 239:
        index = 'i' - 'a';
        break;
      case 240:
        index = 'o' - 'a';
        break;
      case 241:
        index = 'n' - 'a';
        break;
      case 242:
      case 243:
      case 244:
      case 245:
      case 246:
      case 248:
        index = 'o' - 'a';
        break;
      case 249:
      case 250:
      case 251:
      case 252:
        index = 'u' - 'a';
        break;
      case 253:
        index = 'y' - 'a';
        break;
      case 254:
        index = 'p' - 'a';
        break;
      case 255:
        index = 'y' - 'a';
        break;
      default:
        index = -1;
    }
  }
  return index;
}

void TextGraphics::LoadGlyphPage(uint32_t index) {
  std::scoped_lock lock(glyph_load_mutex_);

  // Its possible someone else coulda loaded it since we last checked.
  if (g_glyph_pages[index] == nullptr) {
    char buffer[256];
    snprintf(buffer, sizeof(buffer), "%s%sba_data%sfonts%sfontSmall%d.fdata",
             g_core->GetDataDirectory().c_str(), BA_DIRSLASH, BA_DIRSLASH,
             BA_DIRSLASH, index);
    FILE* f = g_core->platform->FOpen(buffer, "rb");
    BA_PRECONDITION(f);
    BA_PRECONDITION(sizeof(TextGraphics::Glyph[2]) == sizeof(float[18]));
    uint32_t total_size = sizeof(Glyph) * g_glyph_page_glyph_counts[index];
    g_glyph_pages[index] = static_cast<Glyph*>(malloc(total_size));
    BA_PRECONDITION(g_glyph_pages[index]);
    BA_PRECONDITION(fread(g_glyph_pages[index], total_size, 1, f) == 1);
    fclose(f);
  }
}

void TextGraphics::GetFontPageCharRange(int page, uint32_t* first_char,
                                        uint32_t* last_char) {
  // Our special pages:
  switch (page) {
    case static_cast<int>(FontPage::kOSRendered): {
      // We allow the OS to render anything not in one of our glyph textures
      // (technically this overlaps the private-use range which we use our
      // own textures for, but that's handled as a special-case by
      // TextGroup::SetText.
      (*first_char) = kGlyphCount;
      // hmm what's the max unicode value we should ever see?..
      (*last_char) = kTextMaxUnicodeVal;
      break;
    }
    case static_cast<int>(FontPage::kExtras1): {
      (*first_char) = 0xE000;
      (*last_char) = (*first_char) + 24;
      break;
    }
    case static_cast<int>(FontPage::kExtras2): {
      (*first_char) = 0xE000 + 25;
      (*last_char) = (*first_char) + 24;
      break;
    }
    case static_cast<int>(FontPage::kExtras3): {
      (*first_char) = 0xE000 + 50;
      (*last_char) = (*first_char) + 24;
      break;
    }
    case static_cast<int>(FontPage::kExtras4): {
      (*first_char) = 0xE000 + 75;
      (*last_char) = (*first_char) + 24;
      break;
    }
    case static_cast<int>(FontPage::kExtras5): {
      (*first_char) = 0xE000 + 100;
      (*last_char) = (*first_char) + 24;
      break;
    }
    default: {
      assert(page < BA_GLYPH_PAGE_COUNT);
      (*first_char) = g_glyph_page_start_index_map[page];
      (*last_char) = (*first_char) + g_glyph_page_glyph_counts[page] - 1;
      break;
    }
  }
}

void TextGraphics::GetFontPagesForText(const std::string& text,
                                       std::set<int>* font_pages) {
  int last_page = -1;
  std::vector<uint32_t> unicode = Utils::UnicodeFromUTF8(text, "c03853");
  for (uint32_t val : unicode) {
    int page{-1};

    // Hack: allow showing euro even if we don't support unicode font
    // rendering.
    // if (g_buildconfig.enable_os_font_rendering()) {
    //   if (val == 8364) {
    //     val = 0xE000;
    //   }
    // }

    bool covered{};

    // For values in the custom-char range (U+E000–U+F8FF) we point at our
    // own custom page(s)
    if (val >= 0xE000 && val <= 0xF8FF) {
      // The 25 chars after this are in our fontExtras sheet.
      if (val < 0xE000 + 25) {
        // Special value denoting our custom font page.
        page = static_cast<int>(FontPage::kExtras1);
        covered = true;
      } else if (val < 0xE000 + 50) {
        // Special value denoting our custom font page.
        page = static_cast<int>(FontPage::kExtras2);
        covered = true;
      } else if (val < 0xE000 + 75) {
        // Special value denoting our custom font page.
        page = static_cast<int>(FontPage::kExtras3);
        covered = true;
      } else if (val < 0xE000 + 100) {
        // Special value denoting our custom font page.
        page = static_cast<int>(FontPage::kExtras4);
        covered = true;
      } else if (val < 0xE000 + 125) {
        // Special value denoting our custom font page.
        page = static_cast<int>(FontPage::kExtras5);
        covered = true;
      }
    } else if (val < kGlyphCount) {
      page = g_glyph_map[val];
      covered = true;
    }

    if (!covered) {
      if (g_buildconfig.enable_os_font_rendering()) {
        page = static_cast<int>(FontPage::kOSRendered);
      } else {
        val = '?';
        page = g_glyph_map[val];
      }
    }

    // Compare to last_page to avoid doing a set insert for *everything*
    // since most will be the same.
    if (page != last_page) {
      font_pages->insert(page);
      last_page = page;
    }
  }
}

auto TextGraphics::HaveBigChars(const std::string& text) -> bool {
  std::vector<uint32_t> unicode = Utils::UnicodeFromUTF8(text, "fnc93rh");
  // NOLINTNEXTLINE(readability-use-anyofallof)
  for (unsigned int val : unicode) {
    if (GetBigGlyphIndex(val) == -1) {
      // Don't count misses for newlines, spaces, etc.
      if ((val != '\n') && (val != '\r')) {
        return false;
      }
    }
  }
  return true;  // Success!
}

inline auto IsSpecialChar(uint32_t val) -> bool {
  return (val >= 0xE000
          && val < (0xE000
                    + kFontExtrasRows * kFontExtrasColumns * kFontExtrasPages));
}

auto TextGraphics::HaveChars(const std::string& text) -> bool {
  if (g_buildconfig.enable_os_font_rendering()) {
    return true;
  } else {
    std::vector<uint32_t> unicode = Utils::UnicodeFromUTF8(text, "c957fj");
    // NOLINTNEXTLINE(readability-use-anyofallof)
    for (auto&& val : unicode) {
      // There's a few special chars we have.
      if (val >= kGlyphCount && !IsSpecialChar(val)) {
        return false;
      }
    }
    return true;  // Success!
  }
}

auto TextGraphics::HasOSChars(const std::string& text) -> bool {
  std::vector<uint32_t> unicode = Utils::UnicodeFromUTF8(text, "cf0d9j");
  // NOLINTNEXTLINE(readability-use-anyofallof)
  for (auto&& val : unicode) {
    // Anything past our glyph range that isn't one of our special chars
    // goes to the OS (see GetGlyph()).
    if (val >= kGlyphCount && !IsSpecialChar(val)) {
      return true;
    }
  }
  return false;
}

auto TextGraphics::GetGlyph(uint32_t val, bool big) -> TextGraphics::Glyph* {
  if (big) {
    int index = GetBigGlyphIndex(val);
    if (index == -1) index = 37;  // default to '?'
    return &glyphs_big_[index];
  } else {
    // Special case; if its in our custom range, handle it special.
    if (IsSpecialChar(val)) {
      return &glyphs_extras_[val - 0xE000];
    } else if (val >= kGlyphCount) {
      return nullptr;
    }
    uint32_t page = g_glyph_map[val];
    uint32_t start_index = g_glyph_page_start_index_map[page];
    uint32_t local_index = val - start_index;
    if (g_glyph_pages[page] == nullptr) {
      LoadGlyphPage(page);
    }
    return &g_glyph_pages[page][local_index];
  }
}

void TextGraphics::GetOSTextSpanBoundsAndWidth(const std::string& s, Rect* r,
                                               float* width) {
  // Note: callable from ANY thread (logic-thread UI measuring,
  // background warm-ups, doc-ui background prep). Cache state is
  // mutex-guarded here and the platform backends handle their own
  // synchronization.

  // Asking the OS to calculate text bounds sounds expensive,
  // so let's use a cache of recent results.
  {
    std::scoped_lock lock(text_span_bounds_cache_mutex_);
    auto i = text_span_bounds_cache_map_.find(s);
    if (i != text_span_bounds_cache_map_.end()) {
      *r = i->second.r;
      *width = i->second.width;

      // Send this entry to the back of the lru list since we used it.
      text_span_bounds_cache_lru_.splice(text_span_bounds_cache_lru_.end(),
                                         text_span_bounds_cache_lru_,
                                         i->second.lru_iterator);
      return;
    }
  }

  // Cache miss.

  // Root-out aid (all builds): a *synchronous* cold measure on the
  // logic thread can stall on lazy OS font loads (tens of ms = a frame
  // hitch). Deferring consumers (text meshes, widgets) route through
  // TryGetOSTextSpanBoundsAndWidth/TryGetStringWidth instead; anything
  // landing here on the logic thread is a call site that should be
  // converted to those (or moved to a background thread). The goal is
  // ZERO expected triggers — treat any sighting as a bug to fix, not
  // noise to ignore. Logged once per unique span, capped per run;
  // debug builds add a native stack trace to finger the call site.
  // Cost note: this lives on the cache-MISS path only (hits return
  // above), so it adds nothing measurable to normal text flow.
  if (g_base->InLogicThread() && !ScopedSyncMeasureAck::active()) {
    // (Logic-thread-only by the check above, so no locking needed.)
    static std::set<std::string> s_warned_spans;
    if (s_warned_spans.size() < 10 && s_warned_spans.insert(s).second) {
      std::string trace_str;
      if (g_buildconfig.debug_build()) {
        std::unique_ptr<NativeStackTrace> trace(
            g_core->platform->GetNativeStackTrace());
        trace_str = "\n"
                    + (trace ? trace->FormatForDisplay()
                             : std::string("<native trace unavailable>"));
      }
      g_core->logging->Log(
          LogName::kBaGraphics, LogLevel::kWarning,
          "os-text span measured synchronously on the logic thread (span='" + s
              + "'); cold measures can stall on OS font loads. Prefer the"
                " TryGet measure variants or a background thread."
                " (once per unique span, capped per run)"
              + trace_str);
    }
  }

  // Measure *without* holding our lock: a cold measure can
  // take milliseconds-plus (lazy per-script font loads in the OS
  // backend) and must not block cache hits on other threads meanwhile.
  Rect bounds;
  float bounds_width;
  if (g_buildconfig.enable_os_font_rendering()) {
    g_core->platform->GetTextBoundsAndWidth(s, &bounds, &bounds_width);
  } else {
    BA_LOG_ONCE(
        LogName::kBaGraphics, LogLevel::kError,
        "FIXME: GetOSTextSpanBoundsAndWidth unimplemented on this platform");
    bounds.l = 0.0f;
    bounds.r = 1.0f;
    bounds.t = 1.0f;
    bounds.b = 0.0f;
    bounds_width = 1.0f;
  }
  *r = bounds;
  *width = bounds_width;

  std::scoped_lock lock(text_span_bounds_cache_mutex_);

  // Another thread may have measured and inserted this same span while
  // we were measuring; results are identical so just leave theirs.
  if (text_span_bounds_cache_map_.contains(s)) {
    return;
  }
  auto lru_iterator =
      text_span_bounds_cache_lru_.insert(text_span_bounds_cache_lru_.end(), s);
  text_span_bounds_cache_map_[s] =
      TextSpanBoundsCacheEntry_{bounds, bounds_width, lru_iterator};

  // Keep cache from growing too large. (Size note: background prep
  // passes pre-measure big batches — the credits window populates
  // several hundred spans — and those entries need to survive until
  // the logic thread's mesh building consumes them, so this must
  // comfortably exceed such batch sizes. Entries are small; ~1000 is
  // on the order of 100KB.)
  //
  // Eviction-vs-deferral invariant: a background-measured result CAN
  // in principle be evicted here before its deferred requester
  // re-polls (would need 1000+ unique spans in between). That is safe
  // only because deferring consumers re-REQUEST on their next attempt
  // rather than assuming a completed measure implies a cached result;
  // each round still converges since the fonts stay warm. Keep that
  // property if reworking the deferral flow.
  while (text_span_bounds_cache_lru_.size() > 1000) {
    text_span_bounds_cache_map_.erase(text_span_bounds_cache_lru_.front());
    text_span_bounds_cache_lru_.pop_front();
  }
}

void TextGraphics::WarmUpStringAsync(const std::string& text, bool big) {
  if (!g_buildconfig.enable_os_font_rendering()) {
    return;
  }
  // Warm-up is purely an optimization, and very early screen-messages
  // can land before the assets-server loop exists; skip quietly there
  // (the string then simply gets measured on demand later).
  if (g_base->assets_server == nullptr
      || g_base->assets_server->event_loop() == nullptr) {
    return;
  }
  g_base->assets_server->event_loop()->PushCall([this, text, big] {
    // A plain measure walk; every span it touches lands in the cache
    // (cold ones pay their font loads here, off the logic thread).
    GetStringWidth(text, big);
  });
}

auto TextGraphics::TryGetOSTextSpanBoundsAndWidth(const std::string& s, Rect* r,
                                                  float* width) -> bool {
  {
    std::scoped_lock lock(text_span_bounds_cache_mutex_);
    auto i = text_span_bounds_cache_map_.find(s);
    if (i != text_span_bounds_cache_map_.end()) {
      *r = i->second.r;
      *width = i->second.width;
      text_span_bounds_cache_lru_.splice(text_span_bounds_cache_lru_.end(),
                                         text_span_bounds_cache_lru_,
                                         i->second.lru_iterator);
      return true;
    }
  }

  // Cache miss. Off the logic thread we can simply measure inline.
  if (!g_base->InLogicThread()) {
    GetOSTextSpanBoundsAndWidth(s, r, width);
    return true;
  }

  // Logic-thread cache miss: measuring inline can stall on lazy OS
  // font loads (tens of ms), so kick a background measure instead
  // (dedup'd against ones already in flight) and let the caller defer.
  {
    std::scoped_lock lock(text_span_bounds_cache_mutex_);
    if (!os_span_measures_in_flight_.insert(s).second) {
      return false;  // Already being measured.
    }
  }
  g_base->assets_server->event_loop()->PushCall([this, s] {
    Rect r2;
    float width2;
    GetOSTextSpanBoundsAndWidth(s, &r2, &width2);
    {
      std::scoped_lock lock(text_span_bounds_cache_mutex_);
      os_span_measures_in_flight_.erase(s);
    }
    // Bump AFTER the result is in the cache, so anyone woken by this
    // is guaranteed to find it.
    os_span_measure_epoch_.fetch_add(1, std::memory_order_relaxed);
  });
  return false;
}

auto TextGraphics::GetStringWidth(const char* text, bool big) -> float {
  bool complete{};
  return StringWidthInternal_(text, big, false, &complete);
}

auto TextGraphics::TryGetStringWidth(const char* text, bool big)
    -> std::optional<float> {
  bool complete{};
  float width = StringWidthInternal_(text, big, true, &complete);
  if (!complete) {
    return {};
  }
  return width;
}

auto TextGraphics::StringWidthInternal_(const char* text, bool big,
                                        bool allow_defer, bool* complete)
    -> float {
  assert(Utils::IsValidUTF8(text));

  *complete = true;

  // even if they ask for the big font, their string might not support it...
  big = (big && TextGraphics::HaveBigChars(text));

  float char_width = 32.0f;
  const char* t = text;
  float line_length = 0;
  float max_line_length = 0;

  // We have the OS render some chars, broken into single-line spans.
  std::vector<uint32_t> os_span;

  // Tally an os-span's width into line_length. In allow-defer mode a
  // cold span contributes nothing but flips 'complete' off (a
  // background measure gets kicked; note we keep walking so ALL of the
  // string's cold spans get their measures in flight in one pass).
  auto tally_span = [&] {
    std::string s = Utils::UTF8FromUnicode(os_span);
    os_span.clear();
    if (allow_defer) {
      Rect r;
      float width{};
      if (TryGetOSTextSpanBoundsAndWidth(s, &r, &width)) {
        line_length += width;
      } else {
        *complete = false;
      }
    } else {
      line_length += GetOSTextSpanWidth(s);
    }
  };

  while (*t != 0) {
    if (*t == '\n') {
      // Add/reset os-span.
      if (!os_span.empty()) {
        tally_span();
      }
      if (line_length > max_line_length) {
        max_line_length = line_length;
      }
      line_length = 0;
      t++;
    } else {
      uint32_t val = Utils::GetUTF8Value(t);
      Utils::AdvanceUTF8(&t);
      // Special case: if we're already doing an OS-span, tack certain
      // chars onto it instead of switching back to glyph mode.
      // (to reduce the number of times we switch back and forth)
      if (TextGraphics::IsOSDrawableAscii(val) && !os_span.empty()) {
        os_span.push_back(val);
      } else if (Glyph* g = GetGlyph(val, big)) {
        // If we *had* been building a span, add its length.
        if (!os_span.empty()) {
          tally_span();
        }
        line_length += char_width * g->advance;
      } else {
        // Add to os-span.
        if (g_buildconfig.enable_os_font_rendering()) {
          os_span.push_back(val);
        }
      }
    }
  }
  // Tally final span if there is one.
  if (!os_span.empty()) {
    tally_span();
  }
  // Check last line.
  if (line_length > max_line_length) {
    max_line_length = line_length;
  }
  return max_line_length;
}

auto TextGraphics::GetStringHeight(const char* text) -> float {
  size_t str_size = strlen(text);
  int char_val;
  float y_offset = 0;
  for (size_t i = 0; i < str_size; i++) {
    char_val = ((unsigned char*)text)[i];
    if (char_val == '\n') y_offset += kTextRowHeight;
  }
  return y_offset + kTextRowHeight;
}

void TextGraphics::BreakUpString(const char* text, float width,
                                 std::vector<std::string>* v) {
  assert(Utils::IsValidUTF8(text));
  v->clear();
  std::vector<char> buffer_(strlen(text) + 1);
  char* buffer(&(buffer_[0]));
  strcpy(buffer, text);  // NOLINT
  float char_width = 32.0f;
  float line_length = 0;
  const char* s_begin = buffer;
  const char* t = buffer;
  while (true) {
    // If we hit a newline or string end, dump a string.
    if (*t == '\n' || *t == 0) {
      bool is_end = (*t == 0);
      // So we can just use s_begin as a string.
      *(char*)t = 0;  // NOLINT hmmm this code is ugly
      v->push_back(Utils::GetValidUTF8(s_begin, "gbus"));
      line_length = 0.0f;
      if (is_end) {
        break;  // done!
      } else {
        t++;
        s_begin = t;
      }
    } else {
      if (*t == 0) {
        throw Exception();
      }
      uint32_t val = Utils::GetUTF8Value(t);
      Utils::AdvanceUTF8(&t);

      // Special case: if we're already doing an OS-span, tack certain
      // chars onto it instead of switching back to glyph mode.
      // (to reduce the number of times we switch back and forth).
      // NOLINTNEXTLINE(bugprone-branch-clone)
      if (TextGraphics::IsOSDrawableAscii(val) && explicit_bool(false)) {
        // I think I disabled this for consistency?...
        // FIXME FIXME FIXME - handle this along with stuff below..
      } else if (Glyph* g = GetGlyph(val, false)) {
        line_length += char_width * g->advance;
      } else {
        // FIXME FIXME FIXME - need to clump non-glyph characters into
        //  spans and use OS text stuff to get their lengths.
      }

      // If this char puts us over the width, clip a line.
      if (line_length > width) {
        line_length = 0.0f;
        char tmp = *t;
        *(char*)t = 0;  // NOLINT temp for string copy
        v->push_back(Utils::GetValidUTF8(s_begin, "gbus2"));
        *(char*)t = tmp;  // NOLINT
        s_begin = t;
      }
    }
  }
}

}  // namespace ballistica::base
