// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_GRAPHICS_TEXT_TEXT_PACKER_H_
#define BALLISTICA_GRAPHICS_TEXT_TEXT_PACKER_H_

#include <list>
#include <string>
#include <vector>

#include "ballistica/core/object.h"
#include "ballistica/math/rect.h"

namespace ballistica {

class TextPacker : public Object {
 public:
  explicit TextPacker(float resolution_scale);
  ~TextPacker() override;

  // Adds a span.  We could calculate bounds ourselves, but it's often needed
  // outside of here anyway so might as well recycle.
  void AddSpan(const std::string& text, float x, float y, const Rect& bounds);

  auto hash() const -> const std::string& {
    assert(compiled_);
    return hash_;
  }

  struct Span {
    std::vector<uint32_t> unichars;
    std::string string;

    // Position to draw this span at.
    float x;
    float y;

    // Bounds to draw this span with.
    Rect draw_bounds;

    // Texture position to draw this span's text at.
    float tex_x;
    float tex_y;

    // Text-space bounds.
    Rect bounds;
    float u_min;
    float u_max;
    float v_min;
    float v_max;
  };

  // Once done adding spans, call this to calculate final span UV values,
  // texture configuration, and hash.
  void compile();

  auto spans() const -> const std::list<Span>& { return spans_; }

  auto texture_width() const -> int {
    assert(compiled_);
    return texture_width_;
  }

  auto texture_height() const -> int {
    assert(compiled_);
    return texture_height_;
  }

  auto text_scale() const -> float {
    assert(compiled_);
    return text_scale_;
  }

 private:
  float resolution_scale_;
  int texture_width_{};
  int texture_height_{};
  float text_scale_{};
  std::string hash_;
  bool compiled_{false};
  std::list<Span> spans_;
};

}  // namespace ballistica

#endif  // BALLISTICA_GRAPHICS_TEXT_TEXT_PACKER_H_
