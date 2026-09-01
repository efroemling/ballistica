// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_GRAPHICS_TEXT_TEXT_GRAPHICS_H_
#define BALLISTICA_BASE_GRAPHICS_TEXT_TEXT_GRAPHICS_H_

#include <atomic>
#include <list>
#include <mutex>
#include <optional>
#include <set>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

#include "ballistica/shared/foundation/object.h"
#include "ballistica/shared/math/rect.h"

namespace ballistica::base {

// Largest unicode value we ask the OS to draw for us.
const int kTextMaxUnicodeVal = 999999;
const float kTextRowHeight = 32.0f;

constexpr int kFontExtrasRows{5};
constexpr int kFontExtrasColumns{5};
constexpr int kFontExtrasPages{5};

// Encapsulates text-display functionality used by the logic thread.
class TextGraphics {
 public:
  TextGraphics();

  /// RAII scope acknowledging a synchronous logic-thread OS-text
  /// measure: within it, the miss-path logic-thread warning is
  /// skipped. Callers using it own the responsibility of reporting
  /// actual stalls instead (time the measure; warn past a threshold)
  /// — see the Python get_string_width binding for the pattern. This
  /// keeps acknowledged call sites quiet in the common warm case
  /// while worst offenders still surface.
  class ScopedSyncMeasureAck {
   public:
    ScopedSyncMeasureAck() { depth_() += 1; }
    ~ScopedSyncMeasureAck() { depth_() -= 1; }
    static auto active() -> bool { return depth_() > 0; }

   private:
    static auto depth_() -> int& {
      static thread_local int depth{};
      return depth;
    }
  };

  /// Kick off a one-time background warm-up of the OS text backend.
  /// First use of OS text rendering pays a substantial one-time init
  /// cost (font-map construction, font loading — ~85ms of Pango/
  /// fontconfig work on a fast Mac), which otherwise lands inside
  /// whatever innocent UI first measures or draws OS-rendered text on
  /// the logic thread and causes a visible hitch — text meshes for
  /// widgets get built there, so any locale whose UI text needs OS
  /// rendering would eat this at first draw. Runs on the assets-server
  /// event loop — the thread that already rasterizes OS text for text
  /// textures on every platform — so thread-affinity-wise this is
  /// proven ground. Call once during app bootstrapping. (App code
  /// expecting to measure big multi-script batches — e.g. the credits
  /// window's contributor list — should instead do that measuring on a
  /// background thread; measurement is thread-safe.)
  /// NOTE: currently a no-op; see kEnableOSTextWarmUp in the
  /// implementation for the reasoning and possible future targeted
  /// variants.
  void WarmUpOSText();

  enum class FontPage {
    kOSRendered = 9989,
    kExtras1 = 9990,
    kExtras2 = 9991,
    kExtras3 = 9992,
    kExtras4 = 9993,
    kExtras5 = 9994
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
  auto GetGlyph(uint32_t value, bool big) -> const Glyph*;
  static auto HaveBigChars(const std::string& string) -> bool;
  static auto HaveChars(const std::string& string) -> bool;

  /// Return whether any chars in the string get handed to the OS text
  /// backend to draw/measure (i.e. aren't covered by our built-in
  /// glyphs). Measuring such strings can be slow (one-time lazy
  /// per-script OS font loads), so it should happen on background
  /// threads, not the logic thread.
  static auto HasOSChars(const std::string& string) -> bool;
  void GetFontPagesForText(const std::string& text, std::set<int>* font_pages);
  void GetFontPageCharRange(int page, uint32_t* first_char,
                            uint32_t* last_char);
  // Note: text *measurement* (GetOSTextSpanWidth/BoundsAndWidth,
  // GetStringWidth, GetStringHeight) is callable from any thread: the
  // span cache is mutex-guarded, glyph-page loads are mutex-guarded,
  // and the per-platform OS measure backends handle their own
  // synchronization. (Line-breaking and rasterization have their own,
  // narrower contracts.)
  auto GetOSTextSpanWidth(const std::string& s) -> float {
    Rect r;
    float width;
    GetOSTextSpanBoundsAndWidth(s, &r, &width);
    return width;
  }
  void GetOSTextSpanBoundsAndWidth(const std::string& s, Rect* r, float* width);

  /// Measure an OS text span like GetOSTextSpanBoundsAndWidth(), but
  /// never stall the calling thread on a cold measure (which can block
  /// tens of ms on lazy OS font loads): on a span-cache hit — or when
  /// called off the logic thread — this measures inline and returns
  /// true; on a logic-thread cache miss it kicks a background measure
  /// on the assets-server loop and returns false. The result lands in
  /// the span cache and os_span_measure_epoch() bumps once it (and any
  /// other in-flight measures) complete, so callers can defer their
  /// output and rebuild when the epoch moves (see TextGroup's
  /// self-healing for the canonical pattern).
  auto TryGetOSTextSpanBoundsAndWidth(const std::string& s, Rect* r,
                                      float* width) -> bool;

  /// Debug builds only: spans already considered by the defer-chaos
  /// block in TryGetOSTextSpanBoundsAndWidth (every 16th new span gets
  /// its first Try reported cold). Guarded by
  /// text_span_bounds_cache_mutex_.
  std::unordered_set<std::string> debug_chaos_seen_spans_;
  int debug_chaos_span_count_{};

  /// Bumped each time a background span measure kicked off by
  /// TryGetOSTextSpanBoundsAndWidth() completes.
  auto os_span_measure_epoch() const -> int64_t {
    return os_span_measure_epoch_.load(std::memory_order_relaxed);
  }

  // Returns the width of a string
  auto GetStringWidth(const char* s, bool big = false) -> float;
  auto GetStringWidth(const std::string& s, bool big = false) -> float {
    return GetStringWidth(s.c_str(), big);
  }

  /// Warm any needed OS-span measures for a string in the background
  /// (a full measure walk runs on the assets-server loop; results
  /// land in the span cache). The cheap way for text *setters* on the
  /// logic thread to get measures warmed before first draw: costs
  /// only a string copy at the call site, where walking the string
  /// synchronously costs O(length) (~200-350us for a 50-line block on
  /// a midrange phone — real frame-budget money when many widgets are
  /// created at once).
  void WarmUpStringAsync(const std::string& text, bool big = false);

  /// String-level counterpart to TryGetOSTextSpanBoundsAndWidth():
  /// returns the string's width without ever stalling the calling
  /// thread on cold OS measures. Returns empty when any of the
  /// string's OS spans are cold (background measures for ALL of them
  /// get kicked in one pass); watch os_span_measure_epoch() and retry.
  /// (String *height* needs no such variant; it is pure row counting.)
  auto TryGetStringWidth(const char* s, bool big = false)
      -> std::optional<float>;
  auto TryGetStringWidth(const std::string& s, bool big = false)
      -> std::optional<float> {
    return TryGetStringWidth(s.c_str(), big);
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
  auto StringWidthInternal_(const char* text, bool big, bool allow_defer,
                            bool* complete) -> float;

  struct TextSpanBoundsCacheEntry_ {
    Rect r;
    float width{};
    // Position in text_span_bounds_cache_lru_.
    std::list<std::string>::iterator lru_iterator;
  };
  // Guards the two span-bounds cache containers below (plus the
  // in-flight background-measure set). Measurement is callable from
  // any thread (logic-thread UI measuring, background warm-ups,
  // doc-ui background prep), so cache state must be locked; the
  // platform measure backends below us handle their own
  // synchronization.
  std::mutex text_span_bounds_cache_mutex_;

  // Spans currently being measured in the background for
  // TryGetOSTextSpanBoundsAndWidth() (guarded by the mutex above).
  std::set<std::string> os_span_measures_in_flight_;

  std::atomic<int64_t> os_span_measure_epoch_{};

  // Map of entries for fast lookup.
  //
  // Key note: entries are keyed by span string ALONE, which is valid
  // only while OS measurement runs language-agnostic (backends use
  // their process-default language for both measuring and
  // rasterizing, so the two always agree). If we ever pass the app
  // language through to the text backends — desirable someday for
  // correct Han-unification glyph variants (the same CJK codepoints
  // measure/render differently for ja vs zh) — the language must
  // become part of this key or cached widths will go stale across
  // language switches.
  std::unordered_map<std::string, TextSpanBoundsCacheEntry_>
      text_span_bounds_cache_map_;

  // Keys ordered by last use; front = least-recently-used.
  std::list<std::string> text_span_bounds_cache_lru_;
  Glyph
      glyphs_extras_[kFontExtrasRows * kFontExtrasColumns * kFontExtrasPages]{};
  Glyph glyphs_big_[64]{};
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_GRAPHICS_TEXT_TEXT_GRAPHICS_H_
