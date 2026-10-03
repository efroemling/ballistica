// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/graphics/text/text_group.h"

#include <algorithm>
#include <memory>
#include <optional>
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

  // Stored for self-healing rebuilds (see GetElementCount()).
  alignment_h_ = alignment_h;
  alignment_v_ = alignment_v;
  big_raw_ = big;
  res_scale_ = resolution_scale;
  incomplete_ = false;

  // Snapshot this BEFORE building: any measures our build kicks off
  // complete (and bump the epoch) strictly after this, so a completion
  // can never slip between our build and our snapshot and leave us
  // waiting forever.
  int64_t epoch_before = g_base->text_graphics->os_span_measure_epoch();

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
    entry->tex =
        g_base->assets->BuiltinTexture(BuiltinTextureID::kTexturesFontBig);
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
           && (*i != static_cast<int>(TextGraphics::FontPage::kExtras4))
           && (*i != static_cast<int>(TextGraphics::FontPage::kExtras5)));

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

      if (!entry->mesh.complete()) {
        // Some OS-span measures were cold and got deferred to the
        // background; this build is a throwaway (we present nothing
        // until the rebuild; see below). Importantly, do NOT create a
        // texture from the packer in this case — its spans carry
        // placeholder bounds and text textures are content-cached.
        incomplete_ = true;
      }

      if (packer.exists() && !incomplete_) {
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
          entry->tex = g_base->assets->BuiltinTexture(
              BuiltinTextureID::kTexturesFontSmall0);
          break;
        case 1:
          entry->tex = g_base->assets->BuiltinTexture(
              BuiltinTextureID::kTexturesFontSmall1);
          break;
        case 2:
          entry->tex = g_base->assets->BuiltinTexture(
              BuiltinTextureID::kTexturesFontSmall2);
          break;
        case 3:
          entry->tex = g_base->assets->BuiltinTexture(
              BuiltinTextureID::kTexturesFontSmall3);
          break;
        case 4:
          entry->tex = g_base->assets->BuiltinTexture(
              BuiltinTextureID::kTexturesFontSmall4);
          break;
        case 5:
          entry->tex = g_base->assets->BuiltinTexture(
              BuiltinTextureID::kTexturesFontSmall5);
          break;
        case 6:
          entry->tex = g_base->assets->BuiltinTexture(
              BuiltinTextureID::kTexturesFontSmall6);
          break;
        case 7:
          entry->tex = g_base->assets->BuiltinTexture(
              BuiltinTextureID::kTexturesFontSmall7);
          break;
        case static_cast<int>(TextGraphics::FontPage::kOSRendered):
          entry->tex = os_texture_;
          break;
        case static_cast<int>(TextGraphics::FontPage::kExtras1):
          entry->tex = g_base->assets->BuiltinTexture(
              BuiltinTextureID::kTexturesFontExtras);
          break;
        case static_cast<int>(TextGraphics::FontPage::kExtras2):
          entry->tex = g_base->assets->BuiltinTexture(
              BuiltinTextureID::kTexturesFontExtras2);
          break;
        case static_cast<int>(TextGraphics::FontPage::kExtras3):
          entry->tex = g_base->assets->BuiltinTexture(
              BuiltinTextureID::kTexturesFontExtras3);
          break;
        case static_cast<int>(TextGraphics::FontPage::kExtras4):
          entry->tex = g_base->assets->BuiltinTexture(
              BuiltinTextureID::kTexturesFontExtras4);
          break;
        case static_cast<int>(TextGraphics::FontPage::kExtras5):
          entry->tex = g_base->assets->BuiltinTexture(
              BuiltinTextureID::kTexturesFontExtras5);
          break;
        default:
          throw Exception();
      }
      entries_.push_back(std::move(entry));
    }
  }

  if (incomplete_) {
    // Present nothing until our deferred measures land and we rebuild
    // (blank-until-ready, same story as unrendered text textures).
    // GetElementCount() re-runs us once the epoch moves past this.
    entries_.clear();
    os_texture_.Clear();
    build_epoch_ = epoch_before;
  }
}

auto TextGroup::GetCaratPts(const std::string& text_in,
                            TextMesh::HAlign alignment_h,
                            TextMesh::VAlign alignment_v, int carat_position,
                            float* carat_x, float* carat_y) -> bool {
  assert(carat_x && carat_y);
  assert(Utils::IsValidUTF8(text_in));

  // These mirror TextMesh::SetText()'s layout (zero-size bounds;
  // alignment is relative to the origin).
  constexpr float kCharOffsetH{-3.0f};
  constexpr float kCharOffsetV{-3.0f};
  const float row_height{kTextRowHeight};

  std::vector<uint32_t> chars = Utils::UnicodeFromUTF8(text_in, "cpt83kd");
  int char_count = static_cast<int>(chars.size());
  carat_position = std::clamp(carat_position, 0, char_count);

  // Locate the carat's line: its row index and char range.
  int row{};
  int line_start{};
  for (int i = 0; i < carat_position; ++i) {
    if (chars[i] == '\n') {
      ++row;
      line_start = i + 1;
    }
  }
  int line_end{carat_position};
  while (line_end < char_count && chars[line_end] != '\n') {
    ++line_end;
  }

  // Vertical: the first row's baseline per alignment, then down a row
  // per preceding newline.
  float text_height{};
  if (alignment_v == TextMesh::VAlign::kCenter
      || alignment_v == TextMesh::VAlign::kBottom) {
    int rows = 1;
    for (uint32_t c : chars) {
      if (c == '\n') {
        ++rows;
      }
    }
    text_height = static_cast<float>(rows) * row_height;
  }
  float y_offset;
  switch (alignment_v) {
    case TextMesh::VAlign::kNone:
      y_offset = kCharOffsetV;
      break;
    case TextMesh::VAlign::kTop:
      y_offset = kCharOffsetV - row_height;
      break;
    case TextMesh::VAlign::kCenter:
      y_offset = kCharOffsetV + (text_height / 2) - row_height;
      break;
    case TextMesh::VAlign::kBottom:
      y_offset = kCharOffsetV + text_height - row_height;
      break;
    default:
      throw Exception();
  }
  y_offset -= static_cast<float>(row) * row_height;

  // Non-stalling measures: a cold OS-span measure defers to the
  // background (we report failure; the caller retries later).
  auto measure = [this, &chars](int start, int end) -> std::optional<float> {
    std::vector<uint32_t> span(chars.begin() + start, chars.begin() + end);
    return g_base->text_graphics->TryGetStringWidth(
        Utils::UTF8FromUnicode(span), big_);
  };

  // Horizontal: line origin per alignment. Centered/right lines need the
  // full line width, measured the same way the mesh lays it out
  // (including OS-rendered spans).
  float x_offset{kCharOffsetH};
  if (alignment_h == TextMesh::HAlign::kCenter
      || alignment_h == TextMesh::HAlign::kRight) {
    auto line_width = measure(line_start, line_end);
    if (!line_width.has_value()) {
      return false;
    }
    x_offset -= (alignment_h == TextMesh::HAlign::kCenter) ? *line_width / 2
                                                           : *line_width;
  }

  auto prefix_width = measure(line_start, carat_position);
  if (!prefix_width.has_value()) {
    return false;
  }
  *carat_x = x_offset + *prefix_width;
  *carat_y = y_offset;
  return true;
}

auto TextGroup::GetCaratPosAtPoint(const std::string& text_in,
                                   TextMesh::HAlign alignment_h,
                                   TextMesh::VAlign alignment_v, float x,
                                   float y, CaratHitMode mode)
    -> std::optional<int> {
  int char_count = Utils::UTF8StringLength(text_in.c_str());
  std::vector<std::pair<float, float>> pts(char_count + 1);
  for (int i = 0; i <= char_count; ++i) {
    if (!GetCaratPts(text_in, alignment_h, alignment_v, i, &pts[i].first,
                     &pts[i].second)) {
      return {};
    }
  }

  // Nearest row first. (Every slot on a row shares one exact y.)
  float row_y{pts[0].second};
  for (auto& pt : pts) {
    if (std::abs(pt.second - y) < std::abs(row_y - y)) {
      row_y = pt.second;
    }
  }

  // Then the slot within it.
  std::optional<int> best;
  for (int i = 0; i <= char_count; ++i) {
    auto [cx, cy] = pts[i];
    if (cy != row_y) {
      continue;
    }
    switch (mode) {
      case CaratHitMode::kNearestBoundary:
        if (!best.has_value()
            || std::abs(cx - x) < std::abs(pts[*best].first - x)) {
          best = i;
        }
        break;
      case CaratHitMode::kContainingChar:
        // The last slot at or left of the point (or the row's first
        // slot for a point left of everything).
        if (!best.has_value() || cx <= x) {
          best = i;
        }
        break;
      default:
        throw Exception("Invalid CaratHitMode.");
    }
  }
  return best;
}

}  // namespace ballistica::base
