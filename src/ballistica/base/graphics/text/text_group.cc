// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/graphics/text/text_group.h"

#include <memory>
#include <set>
#include <string>
#include <utility>
#include <vector>

#include "ballistica/base/graphics/text/text_graphics.h"
#include "ballistica/base/graphics/text/text_packer.h"
#include "ballistica/shared/generic/utils.h"

namespace ballistica::base {

void TextGroup::SetText(const std::string& text, TextMesh::HAlign alignment_h,
                        TextMesh::VAlign alignment_v, bool big,
                        float resolution_scale) {
  text_ = text;

  // In order to *actually* draw big, all our letters must be available in
  // the big font.
  big_ = (big && TextGraphics::HaveBigChars(text));

  // If we had an OS texture for custom drawing, release it. It should stick
  // around for a while; we'll be able to re-grab the same one if we havn't
  // changed.
  os_texture_.Clear();

  // If we're drawing big we always just need 1 font page (the big one).
  if (big_) {
    // Now create entries for each page we use.
    entries_.clear();
    auto entry{std::make_unique<TextMeshEntry>()};
    entry->u_scale = entry->v_scale = 1.5f;
    entry->can_color = true;
    entry->max_flatness = 1.0f;
    entry->mesh.SetText(text, alignment_h, alignment_v, true, 0, 65535,
                        TextMeshEntryType::kRegular, nullptr);
    entry->tex = g_base->assets->SysTexture(SysTextureID::kFontBig);
    entries_.push_back(std::move(entry));

  } else {
    // Drawing non-big; we might use any number of font pages.

    // First, calc which font pages we'll need to draw this text.
    std::set<int> font_pages;
    g_base->text_graphics->GetFontPagesForText(text, &font_pages);

    // Now create entries for each page we use. We iterate this in reverse
    // so that our custom pages draw first; we want that stuff to show up
    // underneath normal text since we sometimes use it as backing elements,
    // etc.
    entries_.clear();
    for (auto i = font_pages.rbegin(); i != font_pages.rend(); i++) {
      uint32_t min, max;
      g_base->text_graphics->GetFontPageCharRange(*i, &min, &max);
      auto entry{std::make_unique<TextMeshEntry>()};

      // Our custom font page IDs start at value 9990 (kExtras1); make sure
      // for all private-use unicode chars (U+E000–U+F8FF) that we only use
      // these font pages and not OS rendering or other pages (even if those
      // technically support that range).
      if (*i >= static_cast<int>(TextGraphics::FontPage::kExtras1)) {
        entry->type = TextMeshEntryType::kExtras;
        entry->u_scale = entry->v_scale = 3.0f;
        entry->max_flatness = 1.0f;
      } else if (*i == static_cast<int>(TextGraphics::FontPage::kOSRendered)) {
        entry->type = TextMeshEntryType::kOSRendered;

        // Disallow flattening of OS text (otherwise emojis get wrecked).
        // Perhaps we could be smarter about limiting this to emojis and not
        // other text, but we'd have to do something smarter about breaking
        // emojis and non-emojis into separate pages.
        entry->max_flatness = 0.0f;

        // We'll set uv_scale for this guy below; we don't know what it is
        // until we've generated our text-packer.
      } else {
        entry->type = TextMeshEntryType::kRegular;
        entry->u_scale = entry->v_scale = 1.0f;
        entry->max_flatness = 1.0f;
      }

      // Currently we can color or flatten everything except the second, third,
      // and fourth extras pages (those are all pre-colored characters;
      // flattening or coloring would mess them up)
      entry->can_color =
          ((*i != static_cast<int>(TextGraphics::FontPage::kExtras2))
           && (*i != static_cast<int>(TextGraphics::FontPage::kExtras3))
           && (*i != static_cast<int>(TextGraphics::FontPage::kExtras4)));

      // For the few we can't color, we don't want to be able to
      // flatten them either.
      if (!entry->can_color) {
        entry->max_flatness = 0.0f;
      }

      // For OS-rendered text we fill out a text-packer will all the spans
      // we'll need. we then hand that over to the OS to draw and create
      // our texture from that.
      Object::Ref<TextPacker> packer;
      if (entry->type == TextMeshEntryType::kOSRendered) {
        packer = Object::New<TextPacker>(resolution_scale);
      }

      entry->mesh.SetText(text, alignment_h, alignment_v, false, min, max,
                          entry->type, packer.get());

      if (packer.exists()) {
        // If we made a text-packer, we need to fetch/generate a texture
        // that matches it.
        // There should only ever be one of these.
        assert(!os_texture_.exists());
        {
          Assets::AssetListLock lock;
          os_texture_ = g_base->assets->GetTexture(packer.get());
        }

        // We also need to know what uv-scales to use for shadows/etc. This
        // should be proportional to the font-scale over the texture
        // dimension so that its always visually similar.
        float t_scale = packer->text_scale() * 500.0f;
        entry->u_scale = t_scale / static_cast<float>(packer->texture_width());
        entry->v_scale = t_scale / static_cast<float>(packer->texture_height());
      }
      switch (*i) {
        case 0:
          entry->tex = g_base->assets->SysTexture(SysTextureID::kFontSmall0);
          break;
        case 1:
          entry->tex = g_base->assets->SysTexture(SysTextureID::kFontSmall1);
          break;
        case 2:
          entry->tex = g_base->assets->SysTexture(SysTextureID::kFontSmall2);
          break;
        case 3:
          entry->tex = g_base->assets->SysTexture(SysTextureID::kFontSmall3);
          break;
        case 4:
          entry->tex = g_base->assets->SysTexture(SysTextureID::kFontSmall4);
          break;
        case 5:
          entry->tex = g_base->assets->SysTexture(SysTextureID::kFontSmall5);
          break;
        case 6:
          entry->tex = g_base->assets->SysTexture(SysTextureID::kFontSmall6);
          break;
        case 7:
          entry->tex = g_base->assets->SysTexture(SysTextureID::kFontSmall7);
          break;
        case static_cast<int>(TextGraphics::FontPage::kOSRendered):
          entry->tex = os_texture_;
          break;
        case static_cast<int>(TextGraphics::FontPage::kExtras1):
          entry->tex = g_base->assets->SysTexture(SysTextureID::kFontExtras);
          break;
        case static_cast<int>(TextGraphics::FontPage::kExtras2):
          entry->tex = g_base->assets->SysTexture(SysTextureID::kFontExtras2);
          break;
        case static_cast<int>(TextGraphics::FontPage::kExtras3):
          entry->tex = g_base->assets->SysTexture(SysTextureID::kFontExtras3);
          break;
        case static_cast<int>(TextGraphics::FontPage::kExtras4):
          entry->tex = g_base->assets->SysTexture(SysTextureID::kFontExtras4);
          break;
        default:
          throw Exception();
      }
      entries_.push_back(std::move(entry));
    }
  }
}

void TextGroup::GetCaratPts(const std::string& text_in,
                            TextMesh::HAlign alignment_h,
                            TextMesh::VAlign alignment_v, int carat_position,
                            float* carat_x, float* carat_y) {
  assert(carat_x && carat_y);
  assert(Utils::IsValidUTF8(text_in));
  const char* txt = text_in.c_str();
  float x = 0;
  float x_offset;
  float y_offset;
  x_offset = x;
  float char_width{32.0};
  uint32_t char_val;
  float row_height = kTextRowHeight;
  float line_length;
  float l{0.0f};
  float r{0.0f};
  float b{0.0f};
  float t{0.0f};
  float text_height;
  float char_offset_h{-3.0f};
  float char_offset_v{-3.0f};

  // Calc the height of the text where needed.
  switch (alignment_v) {
    case TextMesh::VAlign::kNone:
    case TextMesh::VAlign::kTop:
      text_height = 0;  // Not used here.
      break;
    case TextMesh::VAlign::kCenter:
    case TextMesh::VAlign::kBottom: {
      int rows = 1;
      for (const char* c = txt; *c != 0; c++) {
        if (*c == '\n') rows++;
      }
      text_height = static_cast<float>(rows) * row_height;
      break;
    }
    default:
      throw Exception();
  }
  switch (alignment_v) {
    case TextMesh::VAlign::kNone:
      y_offset = b + char_offset_v;
      break;
    case TextMesh::VAlign::kTop:
      y_offset = b + char_offset_v + (t - b) - row_height;
      break;
    case TextMesh::VAlign::kCenter:
      y_offset =
          b + char_offset_v + ((t - b) / 2) + (text_height / 2) - row_height;
      break;
    case TextMesh::VAlign::kBottom:
      y_offset = b + char_offset_v + text_height - row_height;
      break;
    default:
      throw Exception();
  }
  const char* tc = txt;
  bool first_char = true;
  std::vector<uint32_t> line;
  int char_num = 0;
  while (*tc != 0) {
    const char* tv_prev = tc;
    char_val = Utils::GetUTF8Value(tc);
    Utils::AdvanceUTF8(&tc);

    // Reset alignment on new lines.
    if (first_char || char_val == '\n') {
      switch (alignment_h) {
        case TextMesh::HAlign::kLeft:
          x_offset = l + char_offset_h;
          line.clear();
          break;
        case TextMesh::HAlign::kCenter:
        case TextMesh::HAlign::kRight: {
          // Find the length of this line.
          line_length = 0;
          const char* c;

          // If this was the first char, include it in this line tally if it
          // was a newline, don't.
          if (first_char) {
            c = tv_prev;
          } else {
            c = tc;
          }
          while (true) {
            // Note Sept 2019: this was set to uint8_t. Assuming that was an
            // accident?
            uint32_t val;
            if (*c == 0) {  // NOLINT(bugprone-branch-clone)
              break;
            } else if (*c == '\n') {
              break;
            } else {
              val = Utils::GetUTF8Value(c);
              Utils::AdvanceUTF8(&c);

              // Special case: if we're already doing an OS-span, tack
              // certain chars onto it instead of switching back to glyph
              // mode. (to reduce the number of times we switch back and
              // forth)
              if (TextGraphics::Glyph* g =
                      g_base->text_graphics->GetGlyph(val, big_)) {
                line_length += char_width * g->advance;
              } else {
                // TODO(ericf): add non-glyph chars into spans and ask the
                //  OS for their length.
              }
            }
          }
          if (alignment_h == TextMesh::HAlign::kCenter) {
            x_offset = l + char_offset_h + ((r - l) / 2) - (line_length / 2);
            line.clear();
          } else {
            x_offset = l + char_offset_h + (r - l) - line_length;
            line.clear();
          }
          break;
        }
        default:
          throw Exception();
      }
      first_char = false;
    }
    switch (char_val) {
      case '\n':
        y_offset -= row_height;
        break;
      case '\r':
      case ' ':
        break;
      default: {
      }
    }
    if (carat_position == char_num) {
      break;
    }
    if (char_val != '\n') {
      line.push_back(char_val);
    }
    char_num++;
  }
  *carat_x = x_offset
             + g_base->text_graphics->GetStringWidth(
                 Utils::UTF8FromUnicode(line).c_str());
  *carat_y = y_offset;
}

}  // namespace ballistica::base
