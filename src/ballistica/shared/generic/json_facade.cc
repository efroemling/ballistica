// Released under the MIT License. See LICENSE for details.

#include "ballistica/shared/generic/json_facade.h"

#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include <optional>
#include <string>
#include <string_view>
#include <utility>

#if BA_DEBUG_BUILD
#include <memory>
#endif

// This is the one translation unit permitted to include yyjson directly
// (decision D7). Everything else in the engine goes through the facade.
#include "external/yyjson/yyjson.h"

namespace ballistica {

// Thin wrappers around yyjson's "unsafe" (bounds-unchecked) stepping helpers,
// kept here so iteration logic in the header doesn't need the yyjson header.
// Callers must bound iteration themselves (the iterators below do, via a
// remaining-count).
static auto ContainerFirst_(yyjson_val* container) -> yyjson_val* {
  return unsafe_yyjson_get_first(container);
}

static auto ValNext_(yyjson_val* val) -> yyjson_val* {
  return unsafe_yyjson_get_next(val);
}

static auto WriteMutDoc_(const yyjson_mut_doc* doc, yyjson_write_flag flag)
    -> std::string {
  size_t len{};
  char* out = yyjson_mut_write(doc, flag, &len);
  if (out == nullptr) {
    return "";
  }
  std::string result(out, len);
  free(out);
  return result;
}

// -------------------------- JsonDoc ----------------------------------------

auto JsonDoc::Parse(std::string_view json, const JsonReadOptions& options)
    -> std::expected<JsonDoc, JsonReadError> {
  if (options.max_bytes != 0 && json.size() > options.max_bytes) {
    return std::unexpected(
        JsonReadError{.message = "Input exceeds max_bytes.", .byte_offset = 0});
  }
  yyjson_read_err err;
  // Not using YYJSON_READ_INSITU, so yyjson copies the input into its own
  // buffer and never writes to ours; the const_cast is safe (mirrors what the
  // const yyjson_read() wrapper does internally).
  yyjson_doc* doc =
      yyjson_read_opts(const_cast<char*>(json.data()), json.size(),
                       YYJSON_READ_NOFLAG, nullptr, &err);
  if (doc == nullptr) {
    return std::unexpected(JsonReadError{
        .message = err.msg != nullptr ? err.msg : "Unknown JSON parse error.",
        .byte_offset = err.pos});
  }
  return JsonDoc(doc);
}

JsonDoc::JsonDoc(yyjson_doc* doc) : doc_{doc} {
#if BA_DEBUG_BUILD
  alive_ = std::make_shared<int>(0);
#endif
}

JsonDoc::JsonDoc(JsonDoc&& other) noexcept : doc_{other.doc_} {
  other.doc_ = nullptr;
#if BA_DEBUG_BUILD
  alive_ = std::move(other.alive_);
#endif
}

auto JsonDoc::operator=(JsonDoc&& other) noexcept -> JsonDoc& {
  if (this != &other) {
    if (doc_ != nullptr) {
      yyjson_doc_free(doc_);
    }
    doc_ = other.doc_;
    other.doc_ = nullptr;
#if BA_DEBUG_BUILD
    alive_ = std::move(other.alive_);
#endif
  }
  return *this;
}

JsonDoc::~JsonDoc() {
  if (doc_ != nullptr) {
    yyjson_doc_free(doc_);
  }
}

auto JsonDoc::MakeGuard_() const -> JsonDocGuard {
#if BA_DEBUG_BUILD
  return alive_;
#else
  return {};
#endif
}

auto JsonDoc::root() const -> JsonRef {
  return JsonRef(yyjson_doc_get_root(doc_), MakeGuard_());
}

// -------------------------- JsonRef ----------------------------------------

auto JsonRef::operator[](std::string_view key) const -> JsonRef {
  AssertDocAlive_();
  if (val_ == nullptr || !yyjson_is_obj(val_)) {
    return Child_(nullptr);
  }
  return Child_(yyjson_obj_getn(val_, key.data(), key.size()));
}

auto JsonRef::operator[](size_t index) const -> JsonRef {
  AssertDocAlive_();
  if (val_ == nullptr || !yyjson_is_arr(val_)) {
    return Child_(nullptr);
  }
  return Child_(yyjson_arr_get(val_, index));
}

auto JsonRef::is_object() const -> bool {
  AssertDocAlive_();
  return yyjson_is_obj(val_);
}

auto JsonRef::is_array() const -> bool {
  AssertDocAlive_();
  return yyjson_is_arr(val_);
}

auto JsonRef::is_string() const -> bool {
  AssertDocAlive_();
  return yyjson_is_str(val_);
}

auto JsonRef::is_number() const -> bool {
  AssertDocAlive_();
  return yyjson_is_num(val_);
}

auto JsonRef::is_bool() const -> bool {
  AssertDocAlive_();
  return yyjson_is_bool(val_);
}

auto JsonRef::is_null() const -> bool {
  AssertDocAlive_();
  return yyjson_is_null(val_);
}

auto JsonRef::as_string() const -> std::optional<std::string_view> {
  AssertDocAlive_();
  if (!yyjson_is_str(val_)) {
    return std::nullopt;
  }
  return std::string_view(yyjson_get_str(val_), yyjson_get_len(val_));
}

auto JsonRef::as_int() const -> std::optional<int64_t> {
  AssertDocAlive_();
  if (yyjson_is_sint(val_)) {
    return yyjson_get_sint(val_);
  }
  if (yyjson_is_uint(val_)) {
    return static_cast<int64_t>(yyjson_get_uint(val_));
  }
  return std::nullopt;
}

auto JsonRef::as_double() const -> std::optional<double> {
  AssertDocAlive_();
  if (!yyjson_is_num(val_)) {
    return std::nullopt;
  }
  return yyjson_get_num(val_);
}

auto JsonRef::as_bool() const -> std::optional<bool> {
  AssertDocAlive_();
  if (!yyjson_is_bool(val_)) {
    return std::nullopt;
  }
  return yyjson_get_bool(val_);
}

auto JsonRef::string_or(std::string_view default_value) const
    -> std::string_view {
  return as_string().value_or(default_value);
}

auto JsonRef::int_or(int64_t default_value) const -> int64_t {
  return as_int().value_or(default_value);
}

auto JsonRef::double_or(double default_value) const -> double {
  return as_double().value_or(default_value);
}

auto JsonRef::bool_or(bool default_value) const -> bool {
  return as_bool().value_or(default_value);
}

auto JsonRef::size() const -> size_t {
  AssertDocAlive_();
  if (yyjson_is_arr(val_)) {
    return yyjson_arr_size(val_);
  }
  if (yyjson_is_obj(val_)) {
    return yyjson_obj_size(val_);
  }
  return 0;
}

auto JsonRef::items() const -> JsonObjItemRange {
  AssertDocAlive_();
  return JsonObjItemRange(yyjson_is_obj(val_) ? val_ : nullptr, guard_);
}

auto JsonRef::elements() const -> JsonArrElemRange {
  AssertDocAlive_();
  return JsonArrElemRange(yyjson_is_arr(val_) ? val_ : nullptr, guard_);
}

// -------------------------- iteration --------------------------------------

auto JsonObjItemRange::begin() const -> JsonObjItemIterator {
  size_t count = obj_ != nullptr ? yyjson_obj_size(obj_) : 0;
  if (count == 0) {
    return JsonObjItemIterator(nullptr, 0, guard_);
  }
  return JsonObjItemIterator(ContainerFirst_(obj_), count, guard_);
}

auto JsonObjItemRange::end() const -> JsonObjItemIterator {
  return JsonObjItemIterator(nullptr, 0, guard_);
}

auto JsonObjItemIterator::operator*() const
    -> std::pair<std::string_view, JsonRef> {
  yyjson_val* val = ValNext_(key_);
  std::string_view key_view(yyjson_get_str(key_), yyjson_get_len(key_));
  return {key_view, JsonRef(val, guard_)};
}

auto JsonObjItemIterator::operator++() -> JsonObjItemIterator& {
  --remaining_;
  if (remaining_ == 0) {
    key_ = nullptr;
  } else {
    // Step past this key's value, then to the next key.
    key_ = ValNext_(ValNext_(key_));
  }
  return *this;
}

auto JsonArrElemRange::begin() const -> JsonArrElemIterator {
  size_t count = arr_ != nullptr ? yyjson_arr_size(arr_) : 0;
  if (count == 0) {
    return JsonArrElemIterator(nullptr, 0, guard_);
  }
  return JsonArrElemIterator(ContainerFirst_(arr_), count, guard_);
}

auto JsonArrElemRange::end() const -> JsonArrElemIterator {
  return JsonArrElemIterator(nullptr, 0, guard_);
}

auto JsonArrElemIterator::operator*() const -> JsonRef {
  return JsonRef(cur_, guard_);
}

auto JsonArrElemIterator::operator++() -> JsonArrElemIterator& {
  --remaining_;
  if (remaining_ == 0) {
    cur_ = nullptr;
  } else {
    cur_ = ValNext_(cur_);
  }
  return *this;
}

// -------------------------- JsonBuilder ------------------------------------

JsonBuilder::JsonBuilder() : doc_{yyjson_mut_doc_new(nullptr)} {}

JsonBuilder::JsonBuilder(JsonBuilder&& other) noexcept : doc_{other.doc_} {
  other.doc_ = nullptr;
}

auto JsonBuilder::operator=(JsonBuilder&& other) noexcept -> JsonBuilder& {
  if (this != &other) {
    if (doc_ != nullptr) {
      yyjson_mut_doc_free(doc_);
    }
    doc_ = other.doc_;
    other.doc_ = nullptr;
  }
  return *this;
}

JsonBuilder::~JsonBuilder() {
  if (doc_ != nullptr) {
    yyjson_mut_doc_free(doc_);
  }
}

auto JsonBuilder::root_object() -> JsonObjBuilder {
  yyjson_mut_val* obj = yyjson_mut_obj(doc_);
  yyjson_mut_doc_set_root(doc_, obj);
  return JsonObjBuilder(doc_, obj);
}

auto JsonBuilder::root_array() -> JsonArrBuilder {
  yyjson_mut_val* arr = yyjson_mut_arr(doc_);
  yyjson_mut_doc_set_root(doc_, arr);
  return JsonArrBuilder(doc_, arr);
}

auto JsonBuilder::Write() const -> std::string {
  return WriteMutDoc_(doc_, YYJSON_WRITE_NOFLAG);
}

auto JsonBuilder::WritePretty() const -> std::string {
  return WriteMutDoc_(doc_, YYJSON_WRITE_PRETTY);
}

// -------------------------- JsonObjBuilder ---------------------------------

auto JsonObjBuilder::Add(std::string_view key, std::string_view value)
    -> JsonObjBuilder& {
  yyjson_mut_val* k = yyjson_mut_strncpy(doc_, key.data(), key.size());
  yyjson_mut_val* v = yyjson_mut_strncpy(doc_, value.data(), value.size());
  yyjson_mut_obj_add(obj_, k, v);
  return *this;
}

auto JsonObjBuilder::Add(std::string_view key, const char* value)
    -> JsonObjBuilder& {
  return Add(key, std::string_view(value));
}

auto JsonObjBuilder::Add(std::string_view key, bool value) -> JsonObjBuilder& {
  yyjson_mut_val* k = yyjson_mut_strncpy(doc_, key.data(), key.size());
  yyjson_mut_obj_add(obj_, k, yyjson_mut_bool(doc_, value));
  return *this;
}

auto JsonObjBuilder::Add(std::string_view key, int value) -> JsonObjBuilder& {
  return Add(key, static_cast<int64_t>(value));
}

auto JsonObjBuilder::Add(std::string_view key, int64_t value)
    -> JsonObjBuilder& {
  yyjson_mut_val* k = yyjson_mut_strncpy(doc_, key.data(), key.size());
  yyjson_mut_obj_add(obj_, k, yyjson_mut_sint(doc_, value));
  return *this;
}

auto JsonObjBuilder::Add(std::string_view key, float value) -> JsonObjBuilder& {
  return Add(key, static_cast<double>(value));
}

auto JsonObjBuilder::Add(std::string_view key, double value)
    -> JsonObjBuilder& {
  yyjson_mut_val* k = yyjson_mut_strncpy(doc_, key.data(), key.size());
  yyjson_mut_obj_add(obj_, k, yyjson_mut_real(doc_, value));
  return *this;
}

auto JsonObjBuilder::AddObject(std::string_view key) -> JsonObjBuilder {
  yyjson_mut_val* k = yyjson_mut_strncpy(doc_, key.data(), key.size());
  yyjson_mut_val* obj = yyjson_mut_obj(doc_);
  yyjson_mut_obj_add(obj_, k, obj);
  return JsonObjBuilder(doc_, obj);
}

auto JsonObjBuilder::AddArray(std::string_view key) -> JsonArrBuilder {
  yyjson_mut_val* k = yyjson_mut_strncpy(doc_, key.data(), key.size());
  yyjson_mut_val* arr = yyjson_mut_arr(doc_);
  yyjson_mut_obj_add(obj_, k, arr);
  return JsonArrBuilder(doc_, arr);
}

// -------------------------- JsonArrBuilder ---------------------------------

auto JsonArrBuilder::Add(std::string_view value) -> JsonArrBuilder& {
  yyjson_mut_arr_append(arr_,
                        yyjson_mut_strncpy(doc_, value.data(), value.size()));
  return *this;
}

auto JsonArrBuilder::Add(const char* value) -> JsonArrBuilder& {
  return Add(std::string_view(value));
}

auto JsonArrBuilder::Add(bool value) -> JsonArrBuilder& {
  yyjson_mut_arr_append(arr_, yyjson_mut_bool(doc_, value));
  return *this;
}

auto JsonArrBuilder::Add(int value) -> JsonArrBuilder& {
  return Add(static_cast<int64_t>(value));
}

auto JsonArrBuilder::Add(int64_t value) -> JsonArrBuilder& {
  yyjson_mut_arr_append(arr_, yyjson_mut_sint(doc_, value));
  return *this;
}

auto JsonArrBuilder::Add(float value) -> JsonArrBuilder& {
  return Add(static_cast<double>(value));
}

auto JsonArrBuilder::Add(double value) -> JsonArrBuilder& {
  yyjson_mut_arr_append(arr_, yyjson_mut_real(doc_, value));
  return *this;
}

auto JsonArrBuilder::AddObject() -> JsonObjBuilder {
  yyjson_mut_val* obj = yyjson_mut_obj(doc_);
  yyjson_mut_arr_append(arr_, obj);
  return JsonObjBuilder(doc_, obj);
}

auto JsonArrBuilder::AddArray() -> JsonArrBuilder {
  yyjson_mut_val* arr = yyjson_mut_arr(doc_);
  yyjson_mut_arr_append(arr_, arr);
  return JsonArrBuilder(doc_, arr);
}

// -------------------------- free helpers -----------------------------------

auto JsonEncodeString(std::string_view value) -> std::string {
  yyjson_mut_doc* doc = yyjson_mut_doc_new(nullptr);
  yyjson_mut_val* root = yyjson_mut_strncpy(doc, value.data(), value.size());
  yyjson_mut_doc_set_root(doc, root);
  std::string out = WriteMutDoc_(doc, YYJSON_WRITE_NOFLAG);
  yyjson_mut_doc_free(doc);
  return out;
}

}  // namespace ballistica
