// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/graphics/mesh/text_mesh.h"

#include "ballistica/base/graphics/text/text_graphics.h"
#include "ballistica/base/graphics/text/text_packer.h"
#include "ballistica/shared/generic/utils.h"

namespace ballistica::base {

TextMesh::TextMesh() : MeshIndexedDualTextureFull(MeshDrawType::kStatic) {}

void TextMesh::SetText(const std::string& text_in, HAlign alignment_h,
                       VAlign alignment_v, bool big, uint32_t min_val,
                       uint32_t max_val, TextMeshEntryType entry_type,
                       TextPacker* packer) {
  if (text_in == text_) {
    // Covers corner case where we assign a new string to empty.
    if (text_in.empty()) {
      SetEmpty();
    }
    return;
  }
  text_ = text_in;

  assert(Utils::IsValidUTF8(text_));

  const char* txt = text_in.c_str();

  // Quick-out for empty strings.
  if (txt[0] == 0) {
    SetEmpty();
    return;
  }

  if (entry_type == TextMeshEntryType::kOSRendered) {
    assert(packer != nullptr);
  }

  // Start buffers big enough to handle the worst case
  // (every char being a discrete letter).
  int text_size = static_cast<int>(text_in.size());
  assert(text_size > 0);
  Object::Ref<MeshIndexBuffer16> indices16;
  Object::Ref<MeshIndexBuffer32> indices32;

  // Go with 32 bit indices if there's any chance we'll have over 65535 pts;
  // otherwise go with 16 bit.
  // NOTE: disabling 32 bit indices for now; turns out they're
  // not supported in OpenGL ES2 :-(
  // It may be worth adding logic to split up meshes into multiple
  // draw-calls. (or we can just wait until ES2 is dead).
  if (explicit_bool(false) && 4 * text_size > 65535) {
    indices32 = Object::New<MeshIndexBuffer32>(6 * (text_size));
  } else {
    indices16 = Object::New<MeshIndexBuffer16>(6 * (text_size));
  }
  auto vertices(Object::New<MeshBuffer<VertexDualTextureFull>>(4 * text_size));

  uint16_t* index16 = indices16.Exists() ? indices16->elements.data() : nullptr;
  uint32_t* index32 = indices32.Exists() ? indices32->elements.data() : nullptr;

  VertexDualTextureFull* v = &vertices->elements[0];
  uint32_t index_offset = 0;
  float x = 0;
  float x_offset, y_offset;
  x_offset = x;

  float char_width;
  float char_height;
  float row_height;
  float char_offset_h;
  float char_offset_v;

  char_width = char_height = 32.0f;
  row_height = kTextRowHeight;
  char_offset_h = -3.0f;
  char_offset_v = 7.0f;
  uint32_t char_val;
  float line_length;

  float l = 0;
  float r = 0;
  float b = 0;
  float t = 0;

  float text_height;

  // Pre-calc the height of the text (if needed).
  switch (alignment_v) {
    case VAlign::kNone:
    case VAlign::kTop:
      text_height = 0;  // Not used here.
      break;
    case VAlign::kCenter:
    case VAlign::kBottom: {
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
    case VAlign::kNone:
      y_offset = b + char_offset_v;
      break;
    case VAlign::kTop:
      y_offset = b + char_offset_v + (t - b) - row_height;
      break;
    case VAlign::kCenter:
      y_offset =
          b + char_offset_v + ((t - b) / 2) + (text_height / 2) - row_height;
      break;
    case VAlign::kBottom:
      y_offset = b + char_offset_v + text_height - row_height;
      break;
    default:
      throw Exception();
  }

  const char* tc = txt;
  bool first_char = true;

  std::vector<uint32_t> os_span;

  while (*tc != 0) {
    const char* tc_prev = tc;

    char_val = Utils::GetUTF8Value(tc);

    Utils::AdvanceUTF8(&tc);

    // Reset alignment on new lines.
    if (first_char || char_val == '\n') {
      // If we've been building an os-span, add it to the text-packer.
      if (char_val == '\n' && !os_span.empty()) {
        Rect r2;
        float width;
        std::string s = Utils::UTF8FromUnicode(os_span);
        g_base->text_graphics->GetOSTextSpanBoundsAndWidth(s, &r2, &width);
        if (packer) {
          packer->AddSpan(s, x_offset, y_offset, r2);
        }
        os_span.clear();
      }

      switch (alignment_h) {
        case HAlign::kLeft:
          x_offset = l + char_offset_h;
          break;
        case HAlign::kCenter:
        case HAlign::kRight: {
          // For some alignments we need to pre-calc the length of the line.
          line_length = 0;
          const char* c;

          // If this was the first char, include it in this line tally.
          // if it was a newline, don't.
          if (first_char) {
            c = tc_prev;
          } else {
            c = tc;
          }

          // We have the OS render some chars, broken into single-line spans.
          std::vector<uint32_t> os_span_l;

          while (true) {
            uint32_t val;
            if (*c == 0) {  // NOLINT(bugprone-branch-clone)
              break;
            } else if (*c == '\n') {
              break;
            } else {
              val = Utils::GetUTF8Value(c);
              Utils::AdvanceUTF8(&c);

              // Special case: if we're already doing an OS-span, tack certain
              // chars onto it instead of switching back to glyph mode.
              // (to reduce the number of times we switch back and forth)
              if (TextGraphics::IsOSDrawableAscii(val) && !os_span_l.empty()) {
                os_span_l.push_back(val);
              } else if (TextGraphics::Glyph* g =
                             g_base->text_graphics->GetGlyph(val, big)) {
                // Flipping back to glyphs; if we had been building an os_span,
                // tally it.
                if (!os_span_l.empty()) {
                  std::string s = Utils::UTF8FromUnicode(os_span_l);
                  line_length += g_base->text_graphics->GetOSTextSpanWidth(s);
                  os_span_l.clear();
                }
                line_length += char_width * g->advance;
              } else {
                // Not a glyph char: add it to our current span to handle
                // through the OS.

                if (g_buildconfig.enable_os_font_rendering()) {
                  os_span_l.push_back(val);
                }
              }
            }
          }

          // Add final os_span if there is one.
          if (!os_span_l.empty()) {
            std::string s = Utils::UTF8FromUnicode(os_span_l);
            line_length += g_base->text_graphics->GetOSTextSpanWidth(s);
            os_span_l.clear();
          }
          if (alignment_h == HAlign::kCenter) {
            x_offset = l + char_offset_h + ((r - l) / 2) - (line_length / 2);
          } else {
            x_offset = l + char_offset_h + (r - l) - line_length;
          }
          break;
        }
        default:
          throw Exception();
      }
      first_char = false;
    }

    switch (char_val) {  // NOLINT
      case '\n':
        y_offset -= row_height;
        break;

      default: {
        bool draw = true;
        if (char_val < min_val || char_val > max_val) draw = false;

        // Only draw the private-use range when doing our extras sheets.
        // (technically OS might be able to render these but don't allow that)
        if (entry_type != TextMeshEntryType::kExtras
            && (char_val >= 0xE000 && char_val <= 0xF8FF)) {
          draw = false;
        }

        // Special case: if we're already doing an OS-span, tack certain
        // chars onto it instead of switching back to glyph mode.
        // (to reduce the number of times we switch back and forth)
        if (TextGraphics::IsOSDrawableAscii(char_val) && !os_span.empty()) {
          os_span.push_back(char_val);
        } else if (TextGraphics::Glyph* glyph =
                       g_base->text_graphics->GetGlyph(char_val, big)) {
          // If we had been building up an OS-text span,
          // commit it since we're flipping to glyphs now.
          if (!os_span.empty()) {
            Rect r2;
            float width;
            std::string s = Utils::UTF8FromUnicode(os_span);
            g_base->text_graphics->GetOSTextSpanBoundsAndWidth(s, &r2, &width);
            if (packer) packer->AddSpan(s, x_offset, y_offset, r2);
            x_offset += width;
            os_span.clear();
          }

          // Draw this glyph.
          if (draw) {
            float v_min = glyph->tex_min_y;
            float v_max = glyph->tex_max_y;
            float u_min = glyph->tex_min_x;
            float u_max = glyph->tex_max_x;
            auto v_max_i = static_cast<int>(65535.0f * v_max);
            auto v_min_i = static_cast<int>(65535.0f * v_min);
            auto u_max_i = static_cast<int>(65535.0f * u_max);
            auto u_min_i = static_cast<int>(65535.0f * u_min);

            if (index16) {
              *index16++ = static_cast_check_fit<uint16_t>(index_offset + 0);
              *index16++ = static_cast_check_fit<uint16_t>(index_offset + 1);
              *index16++ = static_cast_check_fit<uint16_t>(index_offset + 2);
              *index16++ = static_cast_check_fit<uint16_t>(index_offset + 1);
              *index16++ = static_cast_check_fit<uint16_t>(index_offset + 3);
              *index16++ = static_cast_check_fit<uint16_t>(index_offset + 2);
            }
            if (index32) {
              *index32++ = index_offset + 0;
              *index32++ = index_offset + 1;
              *index32++ = index_offset + 2;
              *index32++ = index_offset + 1;
              *index32++ = index_offset + 3;
              *index32++ = index_offset + 2;
            }

            // Bot left.
            v->position[0] = x_offset + char_width * glyph->pen_offset_x;
            v->position[1] = y_offset + char_height * glyph->pen_offset_y;
            v->position[2] = 0;
            v->uv[0] = static_cast_check_fit<uint16_t>(u_min_i);
            v->uv[1] = static_cast_check_fit<uint16_t>(v_min_i);
            v->uv2[0] = 0;
            v->uv2[1] = 65535;
            v++;

            // Bot right.
            v->position[0] =
                x_offset + char_width * (glyph->pen_offset_x + glyph->x_size);
            v->position[1] = y_offset + char_height * glyph->pen_offset_y;
            v->position[2] = 0;
            v->uv[0] = static_cast_check_fit<uint16_t>(u_max_i);
            v->uv[1] = static_cast_check_fit<uint16_t>(v_min_i);
            v->uv2[0] = 65535;
            v->uv2[1] = 65535;
            v++;

            // Top left.
            v->position[0] = x_offset + char_width * (glyph->pen_offset_x);
            v->position[1] =
                y_offset + char_height * (glyph->pen_offset_y + glyph->y_size);
            v->position[2] = 0;
            v->uv[0] = static_cast_check_fit<uint16_t>(u_min_i);
            v->uv[1] = static_cast_check_fit<uint16_t>(v_max_i);
            v->uv2[0] = 0;
            v->uv2[1] = 0;
            v++;

            // Top right.
            v->position[0] =
                x_offset + char_width * (glyph->pen_offset_x + glyph->x_size);
            v->position[1] =
                y_offset + char_height * (glyph->pen_offset_y + glyph->y_size);
            v->position[2] = 0;
            v->uv[0] = static_cast_check_fit<uint16_t>(u_max_i);
            v->uv[1] = static_cast_check_fit<uint16_t>(v_max_i);
            v->uv2[0] = 65535;
            v->uv2[1] = 0;
            v++;
            index_offset += 4;
          }
          x_offset += char_width * glyph->advance;
        } else {
          // Add to the single-line span we'll ask the OS to render.
          if (g_buildconfig.enable_os_font_rendering()) {
            os_span.push_back(char_val);
          }
        }
        break;
      }
    }
  }

  // Commit any final OS-text span (can skip this if we're not
  // the one drawing OS text).
  if ((!os_span.empty()) && packer) {
    Rect r2;
    float width;
    std::string s = Utils::UTF8FromUnicode(os_span);
    g_base->text_graphics->GetOSTextSpanBoundsAndWidth(s, &r2, &width);
    packer->AddSpan(s, x_offset, y_offset, r2);
    os_span.clear();
  }

  // Now if we've been building a text-packer,
  // compile it and add its final spans to our mesh.
  if (packer) {
    std::vector<TextPacker::Span> spans;
    packer->Compile();

    // DEBUGGING - add a single quad above our first
    // span showing the entire texture for debugging purposes
    if (explicit_bool(false) && !packer->spans().empty()) {
      int v_max_i = static_cast<int>(65535 * 1.0f);
      int v_min_i = static_cast<int>(65535 * 0.0f);
      int u_max_i = static_cast<int>(65535 * 1.0f);
      int u_min_i = static_cast<int>(65535 * 0.0f);

      if (index16) {
        *index16++ = static_cast_check_fit<uint16_t>(index_offset + 0);
        *index16++ = static_cast_check_fit<uint16_t>(index_offset + 1);
        *index16++ = static_cast_check_fit<uint16_t>(index_offset + 2);
        *index16++ = static_cast_check_fit<uint16_t>(index_offset + 1);
        *index16++ = static_cast_check_fit<uint16_t>(index_offset + 3);
        *index16++ = static_cast_check_fit<uint16_t>(index_offset + 2);
      }
      if (index32) {
        *index32++ = index_offset + 0;
        *index32++ = index_offset + 1;
        *index32++ = index_offset + 2;
        *index32++ = index_offset + 1;
        *index32++ = index_offset + 3;
        *index32++ = index_offset + 2;
      }

      x_offset =
          packer->spans().front().bounds.l + packer->spans().front().x - 80.0f;
      y_offset =
          packer->spans().front().bounds.t + packer->spans().front().y + 90.0f;

      float width = static_cast<float>(packer->texture_width()) * 0.7f;
      float height = static_cast<float>(packer->texture_height()) * 0.7f;

      // Bottom left.
      v->position[0] = x_offset;
      v->position[1] = y_offset;
      v->position[2] = 0;
      v->uv[0] = static_cast_check_fit<uint16_t>(u_min_i);
      v->uv[1] = static_cast_check_fit<uint16_t>(v_max_i);
      v->uv2[0] = 0;
      v->uv2[1] = 65535;
      v++;

      // Bottom right.
      v->position[0] = x_offset + width;
      v->position[1] = y_offset;
      v->position[2] = 0;
      v->uv[0] = static_cast_check_fit<uint16_t>(u_max_i);
      v->uv[1] = static_cast_check_fit<uint16_t>(v_max_i);
      v->uv2[0] = 65535;
      v->uv2[1] = 65535;
      v++;

      // Top left.
      v->position[0] = x_offset;
      v->position[1] = y_offset + height;
      v->position[2] = 0;
      v->uv[0] = static_cast_check_fit<uint16_t>(u_min_i);
      v->uv[1] = static_cast_check_fit<uint16_t>(v_min_i);
      v->uv2[0] = 0;
      v->uv2[1] = 0;
      v++;

      // Top right.
      v->position[0] = x_offset + width;
      v->position[1] = y_offset + height;
      v->position[2] = 0;
      v->uv[0] = static_cast_check_fit<uint16_t>(u_max_i);
      v->uv[1] = static_cast_check_fit<uint16_t>(v_min_i);
      v->uv2[0] = 65535;
      v->uv2[1] = 0;
      v++;

      index_offset += 4;
    }

    for (auto&& i : packer->spans()) {
      int v_max_i =
          std::max(0, std::min(65535, static_cast<int>(65535 * i.v_max)));
      int v_min_i =
          std::max(0, std::min(65535, static_cast<int>(65535 * i.v_min)));
      int u_max_i =
          std::max(0, std::min(65535, static_cast<int>(65535 * i.u_max)));
      int u_min_i =
          std::max(0, std::min(65535, static_cast<int>(65535 * i.u_min)));

      if (index16) {
        *index16++ = static_cast_check_fit<uint16_t>(index_offset + 0);
        *index16++ = static_cast_check_fit<uint16_t>(index_offset + 1);
        *index16++ = static_cast_check_fit<uint16_t>(index_offset + 2);
        *index16++ = static_cast_check_fit<uint16_t>(index_offset + 1);
        *index16++ = static_cast_check_fit<uint16_t>(index_offset + 3);
        *index16++ = static_cast_check_fit<uint16_t>(index_offset + 2);
      }
      if (index32) {
        *index32++ = index_offset + 0;
        *index32++ = index_offset + 1;
        *index32++ = index_offset + 2;
        *index32++ = index_offset + 1;
        *index32++ = index_offset + 3;
        *index32++ = index_offset + 2;
      }

      // Fudge-factor for lining OS-spans up with our stuff.
      x_offset = i.x + 3.0f;
      y_offset = i.y;

      // Bot left.
      v->position[0] = x_offset + i.draw_bounds.l;
      v->position[1] = y_offset + i.draw_bounds.b;
      v->position[2] = 0;
      v->uv[0] = static_cast_check_fit<uint16_t>(u_min_i);
      v->uv[1] = static_cast_check_fit<uint16_t>(v_max_i);
      v->uv2[0] = 0;
      v->uv2[1] = 65535;
      v++;

      // Bot right.
      v->position[0] = x_offset + i.draw_bounds.r;
      v->position[1] = y_offset + i.draw_bounds.b;
      v->position[2] = 0;
      v->uv[0] = static_cast_check_fit<uint16_t>(u_max_i);
      v->uv[1] = static_cast_check_fit<uint16_t>(v_max_i);
      v->uv2[0] = 65535;
      v->uv2[1] = 65535;
      v++;

      // Top left.
      v->position[0] = x_offset + i.draw_bounds.l;
      v->position[1] = y_offset + i.draw_bounds.t;
      v->position[2] = 0;
      v->uv[0] = static_cast_check_fit<uint16_t>(u_min_i);
      v->uv[1] = static_cast_check_fit<uint16_t>(v_min_i);
      v->uv2[0] = 0;
      v->uv2[1] = 0;
      v++;

      // Top right.
      v->position[0] = x_offset + i.draw_bounds.r;
      v->position[1] = y_offset + i.draw_bounds.t;
      v->position[2] = 0;
      v->uv[0] = static_cast_check_fit<uint16_t>(u_max_i);
      v->uv[1] = static_cast_check_fit<uint16_t>(v_min_i);
      v->uv2[0] = 65535;
      v->uv2[1] = 0;
      v++;

      index_offset += 4;
    }
  }

  // Make sure we didn't overshoot the end of our buffer.
  if (index16) {
    assert((index16 - indices16->elements.data())
           <= static_cast<int>(indices16->elements.size()));
  }
  if (index32) {
    assert((index32 - indices32->elements.data())
           <= static_cast<int>(indices32->elements.size()));
  }
  assert((v - (&(vertices->elements[0])))
         <= static_cast<int>(vertices->elements.size()));

  // clamp to what we actually used..
  if (index16) {
    indices16->elements.resize(index16 - (indices16->elements.data()));
  }
  if (index32) {
    indices32->elements.resize(index32 - (indices32->elements.data()));
  }
  vertices->elements.resize(v - (&(vertices->elements[0])));

  // Either set data or abort if empty.
  if (index16 && !indices16->elements.empty()) {
    SetIndexData(indices16);
    SetData(vertices);
  } else if (index32 && !indices32->elements.empty()) {
    // In a lot of cases we actually wind up with fewer than 65535 pts.
    // (we theoretically could have needed more which is why we went 32bit).
    // ...lets go ahead and downsize to 16 bit in this case to save a wee bit
    // of gpu memory.
    if (vertices->elements.size() < 65535) {
      int size = static_cast<int>(indices32->elements.size());
      indices16 = Object::NewDeferred<MeshIndexBuffer16>(size);
      uint16_t* i16 = indices16->elements.data();
      uint32_t* i32 = indices32->elements.data();
      for (int i = 0; i < size; i++) {
        *i16++ = static_cast_check_fit<uint16_t>(*i32++);
      }
      assert((i32 - indices32->elements.data())
             <= static_cast<int>(indices32->elements.size()));
      assert((i16 - indices16->elements.data())
             <= static_cast<int>(indices16->elements.size()));
      SetIndexData(indices16);
    } else {
      // we *actually* need 32 bit indices...
      SetIndexData(indices32);
    }
    SetData(vertices);
  } else {
    SetEmpty();
  }
}

}  // namespace ballistica::base
