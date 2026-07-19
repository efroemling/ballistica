// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_SUPPORT_LANG_STR_H_
#define BALLISTICA_BASE_SUPPORT_LANG_STR_H_

#include <cstdint>
#include <expected>
#include <memory>
#include <optional>
#include <string>
#include <string_view>
#include <unordered_map>
#include <utility>
#include <variant>
#include <vector>

namespace ballistica::base {

/// Cap on nested-substitution depth; mirrors the Python
/// bacommon.langstr.MAX_NESTING_DEPTH (wire data is untrusted, so
/// recursive paths refuse trees deeper than this instead of recursing
/// unboundedly).
inline constexpr int kLangStrMaxNestingDepth{16};

/// A localized string whose final form is chosen at render time; the
/// native mirror of bacommon.loctext.StringSelector. ``forms`` maps a
/// form key to its leaf text (which may carry ``{name}`` substitutions
/// and, for plurals, ``#`` for the count). For plural selectors the
/// keys are CLDR category names or ``=N`` exact-count matches; for
/// select they are possible string values of ``arg``; ``other`` is the
/// fallback.
struct LangStrSelector {
  bool is_plural{};  // Plural ('p') vs select ('s').
  std::string arg;
  std::vector<std::pair<std::string, std::string>> forms;
};

/// One string's per-locale value: plain text or a selector.
using LangStrTableValue = std::variant<std::string, LangStrSelector>;

/// Definition-time line-wrapping hints (decision D-t): the balanced
/// best-effort splitter constraints, applied to evaluated text via the
/// engine's SplitTextIntoLines (whose 0-means-unlimited sentinels
/// these mirror; Python WrapParams None maps to 0).
struct LangStrWrap {
  int min_lines{1};
  int max_lines{0};           // 0 = unlimited.
  int max_chars_per_line{0};  // 0 = none.
};

/// One string's table entry: its value plus optional definition-time
/// wrap hints.
struct LangStrTableEntry {
  LangStrTableValue value;
  std::optional<LangStrWrap> wrap;
};

/// One package's language-string entries plus the canonical
/// sorted-name order that fixes integer string indices (both ends
/// derive it identically, so indexed values resolve without shipping
/// the mapping; mirrors the Python PackageStructure convention).
struct LangStrPackageTable {
  std::unordered_map<std::string, LangStrTableEntry> values;
  std::vector<std::string> sorted_names;
};

/// The native language-string tables for the client's current locale:
/// per-apverid tables parsed once from each resolved package's
/// ``language/<locale>`` blob (Assets::ReloadLanguage), plus the
/// resolved-locale wire value that drives CLDR plural selection.
/// Published as an immutable shared snapshot; any thread may read.
struct LangStrTables {
  std::string plural_locale;
  std::unordered_map<std::string, LangStrPackageTable> packages;
};

/// The native language-string value: an immutable, language-agnostic
/// complex string mirroring the Python ``bacommon.langstr.LangStr``
/// multitype (see docs/initiatives/language-string-context.md). A value
/// is one of three forms:
///
/// - **resource**: an asset-package string addressed by apverid +
///   logical name, with keyword substitutions.
/// - **value**: a raw literal (locale-independent) with keyword
///   substitutions into its ``{name}`` tokens.
/// - **resource-indexed**: the compact integer-addressed projection of
///   a resource (package index + string index + positional subs); the
///   wire default form.
///
/// Substitution values are flat strings/ints or nested language-strings,
/// so a value is a recursive tree; it holds tokens, not text, and only
/// evaluates to a flat string in some particular locale at display time.
///
/// Values are immutable after construction (const-shared by convention:
/// build one, hand it to a ``std::shared_ptr<const LangStr>``, never
/// mutate after). The atomic refcount means any thread may hold, copy,
/// and release refs freely with no GIL or logic-thread involvement.
/// Python-side handles are minted per touch (PythonClassLangStr);
/// native code stores plain shared_ptrs.
class LangStr {
 public:
  enum class Form : uint8_t {
    kResource,
    kValue,
    kResourceIndexed,
  };

  /// A substitution value: flat string, flat integer, or a nested
  /// language-string.
  using Sub =
      std::variant<std::string, int64_t, std::shared_ptr<const LangStr>>;

  /// One substitution entry. ``key`` is the keyword for resource/value
  /// forms and empty for the indexed form (whose subs are positional).
  struct SubEntry {
    std::string key;
    Sub value;
  };

  /// Parse a value from its canonical wire JSON (the dataclassio
  /// serialization of the Python multitype: an object with optional
  /// type tag 't' -- 'r' resource {a,n,s?}, 'v' value {v,s?}, and 'i'
  /// (or tag-free) indexed {p,n,s?}). When ``packages`` is provided
  /// (a payload's package-index manifest), indexed nodes *bind* at
  /// parse: their package int resolves to its apverid, making the
  /// value self-contained (evaluable and convertible once tables are
  /// present). Without it, indexed nodes parse but stay unbound (they
  /// round-trip but refuse to evaluate). Returns the parsed value or
  /// a human-readable error; never throws.
  static auto FromJson(std::string_view json,
                       const std::vector<std::string>* packages = nullptr)
      -> std::expected<std::shared_ptr<const LangStr>, std::string>;

  /// Convert (recursively) to the self-describing resource form's wire
  /// JSON: bound indexed nodes become resource nodes (name + keyword
  /// subs, resolved via the current native tables); resource/value
  /// nodes pass through. For consumers that persist values beyond
  /// their payload's package-index context (e.g. deferred client
  /// effects). Errors for unbound indexed nodes or names/packages
  /// missing from the tables.
  auto ToResourceJson() const -> std::expected<std::string, std::string>;

  /// Evaluate to flat display text. Fail-visible like the Python decode
  /// side: any structural problem (missing substitution, excessive
  /// depth, or -- until the native table store exists -- any
  /// resource/indexed form) yields a ``LANGSTR_ERROR:...`` sentinel
  /// string plus a logged warning, never a crash or throw.
  auto Evaluate() const -> std::string;

  /// Serialize back to canonical wire JSON (matching the dataclassio
  /// form this was parsed from: tag-free for indexed, 's' omitted when
  /// empty).
  auto ToJson() const -> std::string;

  /// Deep structural equality.
  auto Equals(const LangStr& other) const -> bool;

  /// Structural hash consistent with Equals().
  auto Hash() const -> size_t;

  // Plain aggregate-style data; see the immutability convention above.
  // Only the fields relevant to `form` are meaningful.
  Form form{Form::kValue};
  std::string apverid;  // kResource
  std::string name;     // kResource
  std::string value;    // kValue
  int64_t pkg{-1};      // kResourceIndexed
  int64_t index{-1};    // kResourceIndexed
  std::vector<SubEntry> subs;

  // Optional usage-site wrap override (applied post-eval; wins over
  // any definition-time wrap from the tables). Not part of the wire
  // form (ToJson omits it) but included in Equals/Hash.
  std::optional<LangStrWrap> wrap;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_SUPPORT_LANG_STR_H_
