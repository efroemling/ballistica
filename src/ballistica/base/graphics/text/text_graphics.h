// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_GRAPHICS_TEXT_TEXT_GRAPHICS_H_
#define BALLISTICA_BASE_GRAPHICS_TEXT_TEXT_GRAPHICS_H_

#include <list>
#include <mutex>
#include <set>
#include <string>
#include <unordered_map>
#include <vector>

#include "ballistica/shared/foundation/object.h"
#include "ballistica/shared/math/rect.h"

namespace ballistica::base {

// Largest unicode value we ask the OS to draw for us.
const int kTextMaxUnicodeVal = 999999;
const float kTextRowHeight = 32.0f;

// Encapsulates text-display functionality used by the logic thread.
class TextGraphics {
 public:
  TextGraphics();

  enum class FontPage {
    kOSRendered = 9989,
    kExtras1 = 9990,
    kExtras2 = 9991,
    kExtras3 = 9992,
    kExtras4 = 9993
  };

  struct Glyph {
    float pen_offset_x;
    float pen_offset_y;
    float advance;
    float x_size;
    float y_size;
    float tex_min_x;
    float tex_min_y;
    float tex_max_x;
    float tex_max_y;
  };

  static auto GetBigCharIndex(int c) -> int;

  // Returns a glyph or nullptr if it is unavailable.
  auto GetGlyph(uint32_t value, bool big) -> Glyph*;
  static auto HaveBigChars(const std::string& string) -> bool;
  static auto HaveChars(const std::string& string) -> bool;
  void GetFontPagesForText(const std::string& text, std::set<int>* font_pages);
  void GetFontPageCharRange(int page, uint32_t* first_char,
                            uint32_t* last_char);
  auto GetOSTextSpanWidth(const std::string& s) -> float {
    Rect r;
    float width;
    GetOSTextSpanBoundsAndWidth(s, &r, &width);
    return width;
  }
  void GetOSTextSpanBoundsAndWidth(const std::string& s, Rect* r, float* width);

  // Returns the width of a string
  auto GetStringWidth(const char* s, bool big = false) -> float;
  auto GetStringWidth(const std::string& s, bool big = false) -> float {
    return GetStringWidth(s.c_str(), big);
  }

  // Returns the height of a string
  auto GetStringHeight(const char* s) -> float;
  auto GetStringHeight(const std::string& s) -> float {
    return GetStringHeight(s.c_str());
  }

  // Given a target width, breaks the string up into multiple strings so they
  // fit within it
  void BreakUpString(const char* text, float width,
                     std::vector<std::string>* v);

  // Some chars we allow the OS to draw in some cases but draw ourselves in
  // others (to minimize the amount of switching back and forth).
  static auto IsOSDrawableAscii(int val) -> bool {
    // ( exclude a few that usually come in pairs so we
    // avoid one side looking different than the other )
    return (((val >= ' ' && val <= '/') || (val >= ':' && val <= '@')
             || (val >= '[' && val <= '`') || (val >= '{' && val <= '~'))
            && (val != '\'') && (val != '"') && (val != '[') && (val != ']')
            && (val != '{') && (val != '}') && (val != '(') && (val != ')'));
  }

 private:
  class TextSpanBoundsCacheEntry;
  void LoadGlyphPage(uint32_t index);

  // Map of entries for fast lookup.
  std::unordered_map<std::string, Object::Ref<TextSpanBoundsCacheEntry> >
      text_span_bounds_cache_map_;

  // List of entries for sorting by last-use-time
  std::list<Object::Ref<TextSpanBoundsCacheEntry> > text_span_bounds_cache_;
  std::mutex glyph_load_mutex_;
  Glyph glyphs_extras_[100]{};
  Glyph glyphs_big_[64]{};
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_GRAPHICS_TEXT_TEXT_GRAPHICS_H_
