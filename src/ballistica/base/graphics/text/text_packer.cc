// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/graphics/text/text_packer.h"

namespace ballistica::base {

TextPacker::TextPacker(float resolution_scale)
    : resolution_scale_{resolution_scale} {}

TextPacker::~TextPacker() = default;

void TextPacker::AddSpan(const std::string& text, float x, float y,
                         const Rect& bounds) {
  spans_.emplace_back();
  Span& s(spans_.back());
  s.string = text;
  s.x = x;
  s.y = y;
  s.u_min = 0.0f;
  s.u_max = 1.0f;
  s.v_min = 0.0f;
  s.v_max = 1.0f;
  s.bounds = bounds;
}

// FIXME - we currently run into minor problems because we measure our text
//  bounds at one size and then scale that linearly when trying to fit
//  things into the texture. However, fonts don't always scale linearly (and
//  even when that's an option it can be expensive).

void TextPacker::Compile() {
  assert(!compiled_);
  if (spans_.empty()) {
    compiled_ = true;
    return;
  }
  float max_width = 2048.0;
  float max_height = 2048.0;
  float width = 32.0;
  float height = 32.0;
  float scale = resolution_scale_ * 2.0f;
  float span_buffer = 3.0f;  // Note: buffer scales along with text.
  float widest_unscaled_span_width = 0.0f;

  // Find our widest span width; we'll use this to determine the width
  // of the texture (and whether we need to scale our text down to fit).
  for (auto& span : spans_) {
    float w = span.bounds.width() + 2.0f * span_buffer;
    if (w > widest_unscaled_span_width) widest_unscaled_span_width = w;
  }

  // Ok, lets crank our width up until its a bit wider than the widest span
  // width (should hopefully allow for at least a few spans per line in
  // general).
  while (width < (widest_unscaled_span_width * scale * 1.2f)
         && width < max_width) {
    width *= 2;
  }

  // Alternately, if we're too big, crank our scale down so that our widest
  // span fits.
  if (widest_unscaled_span_width * scale > width * 0.9f) {
    scale *= ((width * 0.9f) / (widest_unscaled_span_width * scale));
  }
  float start_height = height;
  int mini_shrink_tries = 0;

  // Ok; we've now locked in a width and scale. Now we go through and
  // position our spans. We may need to do this more than once if our height
  // comes out too big. (hopefully this will never be a problem in practice)
  while (true) {
    height = start_height;

    // We currently just lay out left-to-right, top-to-bottom. This could be
    // somewhat wasteful in particular configurations. (leaving half-filled
    // lines, etc) so it might be worth improving later.
    float widest_fill_right = 0.0f;
    float fill_right = 0.0f;
    float fill_bottom = 0.0f;
    float line_height = 0.0f;
    for (auto&& i : spans_) {
      float span_width = (i.bounds.width() + 2.0f * span_buffer) * scale;
      float span_height =
          (std::abs(i.bounds.height()) + 2.0f * span_buffer) * scale;

      // Start a new line if this would put us past the end.
      if (fill_right + span_width > width) {
        if (fill_right > widest_fill_right) {
          // Keep track of how far over we go.
          widest_fill_right = fill_right;
        }
        fill_right = 0.0f;
        fill_bottom += line_height;
        line_height = 0.0f;
      }

      // Position x such that x + left bound - buffer lines up with our
      // current right point.
      float to_left = (i.bounds.l - span_buffer) * scale;
      i.tex_x = fill_right - to_left;
      fill_right += span_width;

      // Position y such that y - top bound - buffer lines up with our
      // current bottom point.
      float to_top = (-i.bounds.t - span_buffer) * scale;
      i.tex_y = fill_bottom - to_top;

      // If our total height is greater than the current line height, expand
      // the line's.
      if (span_height > line_height) {
        line_height = span_height;
      }

      // Increase height if need be.
      while ((fill_bottom + line_height) > height) {
        height *= 2;
      }
    }
    if (fill_right > widest_fill_right) widest_fill_right = fill_right;

    float mini_shrink_threshold_h = 0.55f;
    float mini_shrink_threshold_v = 0.55f;

    if (height > max_height) {
      // If it doesn't fit, repeat again with a smaller scale until it does.

      // Dropping our scale has a disproportional effect on the final height
      // (since it opens up more relative horizontal space). I'm not sure
      // how to figure out how much to drop by other than incrementally
      // dropping values until we fit.
      scale *= 0.75f;

    } else if (((widest_fill_right < (width * mini_shrink_threshold_h)
                 && width > 16)
                || fill_bottom + line_height
                       < (height * mini_shrink_threshold_v))
               && mini_shrink_tries < 3) {
      // If we're here it means we *barely* use more than half of the
      // texture in one direction or the other; let's shrink just a tiny bit
      // and we should be able to chop our texture size in half
      if (widest_fill_right < width * mini_shrink_threshold_h && width > 16) {
        float scale_val = 0.99f * (((width * 0.5f) / widest_fill_right));
        if (scale_val < 1.0f) {
          // FIXME - should think about a fixed multiplier here; under the
          //  hood the system might be caching glyphs based on scale and
          //  this would leave us with fewer different scales in the end and
          //  thus better caching performance
          scale *= scale_val;
        }
        width /= 2;
      } else {
        float scale_val = 0.99f * (height * 0.5f) / (fill_bottom + line_height);
        if (scale_val < 1.0f) {
          // FIXME - should think about a fixed multiplier here; under the
          //  hood the system might be caching glyphs based on scale and
          //  this would leave us with fewer different scales in the end and
          //  thus better caching performance
          scale *= scale_val;
        }
      }
      mini_shrink_tries += 1;
    } else {
      // we fit; hooray!
      break;
    }
  }

  // Lastly, now that our texture width and height are completely finalized,
  // we can calculate UVs.
  for (auto&& i : spans_) {
    // Now store uv coords for this span; they should include the buffer.
    i.u_min = (i.tex_x + (i.bounds.l - span_buffer) * scale) / width;
    i.u_max = (i.tex_x + (i.bounds.r + span_buffer) * scale) / width;
    i.v_max = (i.tex_y + (-i.bounds.b + span_buffer) * scale) / height;
    i.v_min = (i.tex_y + (-i.bounds.t - span_buffer) * scale) / height;

    // Also calculate draw-bounds which accounts for our buffer.
    i.draw_bounds.l = (i.bounds.l - span_buffer);
    i.draw_bounds.r = (i.bounds.r + span_buffer);
    i.draw_bounds.t = (i.bounds.t + span_buffer);
    i.draw_bounds.b = (i.bounds.b - span_buffer);
  }

  // TODO(ericf): now we calculate a hash that's unique to this text
  //  configuration; we'll use that as a key for the texture we'll
  //  generate/use. ..this way multiple meshes can share the same generated
  //  texture. *technically* we could calculate this hash and check for an
  //  existing texture before we bother laying out our spans, but that might
  //  not save us much time and would complicate things.
  hash_ = std::to_string(resolution_scale_);
  for (auto&& i : spans_) {
    char buffer[64];
    snprintf(buffer, sizeof(buffer), "!SP!%f|%f|", i.x, i.y);
    hash_ += buffer;
    hash_ += i.string;
  }
  texture_width_ = static_cast<int>(width);
  texture_height_ = static_cast<int>(height);
  text_scale_ = scale;
  compiled_ = true;
}

}  // namespace ballistica::base
