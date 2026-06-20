// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SHARED_GENERIC_JSON_FACADE_H_
#define BALLISTICA_SHARED_GENERIC_JSON_FACADE_H_

#include <cassert>
#include <cstddef>
#include <cstdint>
#include <expected>
#include <optional>
#include <string>
#include <string_view>
#include <utility>

#include "ballistica/shared/ballistica.h"

#if BA_DEBUG_BUILD
#include <memory>
#endif

// Safe, modern-C++ facade over the vendored yyjson library.
//
// This is the engine's one sanctioned JSON interface (decision D7 in
// docs/initiatives/strings-asset-migration.md): only json_facade.cc may
// include yyjson directly; all other engine code goes through the types
// declared here. The reader is a null-safe monadic DOM and the writer is a
// chainable builder; nothing here throws (errors are values), matching the
// engine's exception-stripping discipline.

// Forward-declare the vendored yyjson types at global scope (yyjson is a C
// library; its types live in the global namespace). Keeping these as
// incomplete pointers here is what lets the yyjson header stay confined to
// json_facade.cc.
struct yyjson_doc;
struct yyjson_val;
struct yyjson_mut_doc;
struct yyjson_mut_val;

namespace ballistica {

class JsonRef;
class JsonObjItemRange;
class JsonArrElemRange;
class JsonArrBuilder;

// A small token that lets a JsonRef verify (in debug builds) that its owning
// JsonDoc is still alive. In release builds it is an empty type with zero
// overhead.
#if BA_DEBUG_BUILD
using JsonDocGuard = std::weak_ptr<int>;
#else
struct JsonDocGuard {};
#endif

/// Details of a failed parse (returned by JsonDoc::Parse).
struct JsonReadError {
  std::string message;
  size_t byte_offset{};
};

/// Parse-hardening knobs. Minimal and strict by default: yyjson's parser is
/// iterative (no parse-depth limit needed) and rejects comments / trailing
/// commas. Untrusted callers should set max_bytes to their packet budget.
struct JsonReadOptions {
  /// If nonzero, reject inputs larger than this many bytes (0 = no limit).
  size_t max_bytes{0};
};

/// Recommended recursion cap for *consumers* that walk a parsed document
/// recursively (yyjson's own parser is iterative and needs no such cap).
constexpr int kJsonMaxConsumerDepth{64};

/// Null-safe, non-owning view of a value within a parsed JsonDoc.
///
/// Cheap to copy. Navigating into or extracting from a missing or wrong-typed
/// value yields a null JsonRef (navigation) or std::nullopt (extraction)
/// rather than crashing, and null propagates through further navigation -- so
/// `root["a"]["b"][2].as_string()` is always safe no matter the input.
///
/// A JsonRef (and any string_view it hands back) must not outlive the JsonDoc
/// it came from. In debug builds this is asserted; in release builds it is the
/// caller's responsibility.
class JsonRef {
 public:
  JsonRef() = default;

  /// Navigate into an object by key (case-sensitive). Null if this is not an
  /// object or the key is absent.
  auto operator[](std::string_view key) const -> JsonRef;

  /// Navigate into an array by index. Null if this is not an array or the
  /// index is out of range.
  auto operator[](size_t index) const -> JsonRef;

  /// Whether this refers to an actual value (vs null/missing).
  explicit operator bool() const { return val_ != nullptr; }
  auto exists() const -> bool { return val_ != nullptr; }

  auto is_object() const -> bool;
  auto is_array() const -> bool;
  auto is_string() const -> bool;
  auto is_number() const -> bool;
  auto is_bool() const -> bool;
  auto is_null() const -> bool;

  /// Extract a string. Zero-copy: the returned view is valid only while the
  /// owning JsonDoc lives. nullopt if this is not a string.
  auto as_string() const -> std::optional<std::string_view>;
  /// Extract an integer. nullopt if this is not an integer-valued number.
  auto as_int() const -> std::optional<int64_t>;
  /// Extract a number as a double (accepts int or real). nullopt if not a
  /// number.
  auto as_double() const -> std::optional<double>;
  /// Extract a bool. nullopt if this is not a bool.
  auto as_bool() const -> std::optional<bool>;

  auto string_or(std::string_view default_value) const -> std::string_view;
  auto int_or(int64_t default_value) const -> int64_t;
  auto double_or(double default_value) const -> double;
  auto bool_or(bool default_value) const -> bool;

  /// Member/element count (0 if not an object or array).
  auto size() const -> size_t;

  /// Range over object members as (key, value) pairs. Empty if not an object.
  auto items() const -> JsonObjItemRange;
  /// Range over array elements. Empty if not an array.
  auto elements() const -> JsonArrElemRange;

 private:
  friend class JsonDoc;
  friend class JsonObjItemRange;
  friend class JsonArrElemRange;
  friend class JsonObjItemIterator;
  friend class JsonArrElemIterator;

  JsonRef(yyjson_val* val, JsonDocGuard guard)
      : val_{val}, guard_{std::move(guard)} {}

  // Asserts (debug only) that the owning doc is still alive.
  void AssertDocAlive_() const {
#if BA_DEBUG_BUILD
    assert(val_ == nullptr || !guard_.expired());
#else
    static_cast<void>(guard_);
#endif
  }

  // Builds a child ref carrying this ref's same doc-guard.
  auto Child_(yyjson_val* val) const -> JsonRef { return JsonRef(val, guard_); }

  yyjson_val* val_{};
  [[no_unique_address]] JsonDocGuard guard_;
};

/// Iterator over an object's (key, value) pairs. See JsonRef::items().
class JsonObjItemIterator {
 public:
  JsonObjItemIterator(yyjson_val* key, size_t remaining, JsonDocGuard guard)
      : key_{key}, remaining_{remaining}, guard_{std::move(guard)} {}
  auto operator*() const -> std::pair<std::string_view, JsonRef>;
  auto operator++() -> JsonObjItemIterator&;
  auto operator!=(const JsonObjItemIterator& other) const -> bool {
    return key_ != other.key_;
  }

 private:
  yyjson_val* key_{};
  size_t remaining_{};
  [[no_unique_address]] JsonDocGuard guard_;
};

/// Range adaptor for JsonRef::items().
class JsonObjItemRange {
 public:
  JsonObjItemRange(yyjson_val* obj, JsonDocGuard guard)
      : obj_{obj}, guard_{std::move(guard)} {}
  auto begin() const -> JsonObjItemIterator;
  auto end() const -> JsonObjItemIterator;

 private:
  yyjson_val* obj_{};
  [[no_unique_address]] JsonDocGuard guard_;
};

/// Iterator over an array's elements. See JsonRef::elements().
class JsonArrElemIterator {
 public:
  JsonArrElemIterator(yyjson_val* cur, size_t remaining, JsonDocGuard guard)
      : cur_{cur}, remaining_{remaining}, guard_{std::move(guard)} {}
  auto operator*() const -> JsonRef;
  auto operator++() -> JsonArrElemIterator&;
  auto operator!=(const JsonArrElemIterator& other) const -> bool {
    return cur_ != other.cur_;
  }

 private:
  yyjson_val* cur_{};
  size_t remaining_{};
  [[no_unique_address]] JsonDocGuard guard_;
};

/// Range adaptor for JsonRef::elements().
class JsonArrElemRange {
 public:
  JsonArrElemRange(yyjson_val* arr, JsonDocGuard guard)
      : arr_{arr}, guard_{std::move(guard)} {}
  auto begin() const -> JsonArrElemIterator;
  auto end() const -> JsonArrElemIterator;

 private:
  yyjson_val* arr_{};
  [[no_unique_address]] JsonDocGuard guard_;
};

/// RAII owner of a parsed JSON document. Move-only.
class JsonDoc {
 public:
  /// Parse JSON text. Never throws; yields the parsed document or a
  /// JsonReadError.
  static auto Parse(std::string_view json, const JsonReadOptions& options = {})
      -> std::expected<JsonDoc, JsonReadError>;

  JsonDoc(JsonDoc&& other) noexcept;
  auto operator=(JsonDoc&& other) noexcept -> JsonDoc&;
  JsonDoc(const JsonDoc&) = delete;
  auto operator=(const JsonDoc&) -> JsonDoc& = delete;
  ~JsonDoc();

  /// The root value (null JsonRef if the document is somehow empty).
  auto root() const -> JsonRef;

 private:
  explicit JsonDoc(yyjson_doc* doc);
  auto MakeGuard_() const -> JsonDocGuard;

  yyjson_doc* doc_{};
#if BA_DEBUG_BUILD
  std::shared_ptr<int> alive_;
#endif
};

/// Chainable builder for a JSON object. Lightweight handle into a JsonBuilder;
/// must not outlive it. All Add() overloads copy their key and value, so
/// string_view/std::string arguments can never dangle.
class JsonObjBuilder {
 public:
  auto Add(std::string_view key, std::string_view value) -> JsonObjBuilder&;
  auto Add(std::string_view key, const char* value) -> JsonObjBuilder&;
  auto Add(std::string_view key, bool value) -> JsonObjBuilder&;
  auto Add(std::string_view key, int value) -> JsonObjBuilder&;
  auto Add(std::string_view key, int64_t value) -> JsonObjBuilder&;
  auto Add(std::string_view key, float value) -> JsonObjBuilder&;
  auto Add(std::string_view key, double value) -> JsonObjBuilder&;
  /// Add a nested object under key and return a builder for it.
  auto AddObject(std::string_view key) -> JsonObjBuilder;
  /// Add a nested array under key and return a builder for it.
  auto AddArray(std::string_view key) -> JsonArrBuilder;

 private:
  friend class JsonBuilder;
  friend class JsonArrBuilder;
  JsonObjBuilder(yyjson_mut_doc* doc, yyjson_mut_val* obj)
      : doc_{doc}, obj_{obj} {}
  yyjson_mut_doc* doc_{};
  yyjson_mut_val* obj_{};
};

/// Chainable builder for a JSON array. Lightweight handle into a JsonBuilder;
/// must not outlive it.
class JsonArrBuilder {
 public:
  auto Add(std::string_view value) -> JsonArrBuilder&;
  auto Add(const char* value) -> JsonArrBuilder&;
  auto Add(bool value) -> JsonArrBuilder&;
  auto Add(int value) -> JsonArrBuilder&;
  auto Add(int64_t value) -> JsonArrBuilder&;
  auto Add(float value) -> JsonArrBuilder&;
  auto Add(double value) -> JsonArrBuilder&;
  /// Append a nested object and return a builder for it.
  auto AddObject() -> JsonObjBuilder;
  /// Append a nested array and return a builder for it.
  auto AddArray() -> JsonArrBuilder;

 private:
  friend class JsonBuilder;
  friend class JsonObjBuilder;
  JsonArrBuilder(yyjson_mut_doc* doc, yyjson_mut_val* arr)
      : doc_{doc}, arr_{arr} {}
  yyjson_mut_doc* doc_{};
  yyjson_mut_val* arr_{};
};

/// RAII owner of a JSON document being built. Move-only. Hand out a root
/// object/array builder, populate it, then Write().
class JsonBuilder {
 public:
  JsonBuilder();
  JsonBuilder(JsonBuilder&& other) noexcept;
  auto operator=(JsonBuilder&& other) noexcept -> JsonBuilder&;
  JsonBuilder(const JsonBuilder&) = delete;
  auto operator=(const JsonBuilder&) -> JsonBuilder& = delete;
  ~JsonBuilder();

  /// Set the root to a fresh empty object and return a builder for it.
  auto root_object() -> JsonObjBuilder;
  /// Set the root to a fresh empty array and return a builder for it.
  auto root_array() -> JsonArrBuilder;

  /// Serialize to a compact string.
  auto Write() const -> std::string;
  /// Serialize to a pretty (indented) string.
  auto WritePretty() const -> std::string;

 private:
  yyjson_mut_doc* doc_{};
};

/// JSON-encode a bare string value: returns its quoted, escaped form (e.g.
/// `a"b` -> `"a\"b"`). Handy for splicing a string into manually-assembled
/// JSON; prefer JsonBuilder when emitting a whole document.
auto JsonEncodeString(std::string_view value) -> std::string;

}  // namespace ballistica

#endif  // BALLISTICA_SHARED_GENERIC_JSON_FACADE_H_
