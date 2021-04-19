// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_CORE_INLINE_H_
#define BALLISTICA_CORE_INLINE_H_

#ifdef __cplusplus

#include <cassert>
#include <string>
#include <type_traits>

// Bits of functionality that are useful enough to include fully as
// inlines/templates in our top level namespace.

namespace ballistica {

// Support functions we declare in our .cc file; not for public use.
// auto InlineDebugExplicitBool(bool val) -> bool;

/// Return the same bool value passed in, but obfuscated enough in debug mode
/// that no 'value is always true/false', 'code will never run', type warnings
/// should appear. In release builds it should optimize away to a no-op.
inline auto explicit_bool(bool val) -> bool {
#if BA_DEBUG_BUILD
  return InlineDebugExplicitBool(val);
#else
  return val;
#endif
}

/// Simply a static_cast, but in debug builds casts the results back to ensure
/// the value fits into the receiver unchanged. Handy as a sanity check when
/// stuffing a 32 bit value into a 16 bit container, etc.
template <typename OUT_TYPE, typename IN_TYPE>
auto static_cast_check_fit(IN_TYPE in) -> OUT_TYPE {
  // Make sure we don't try to use this when casting to or from floats or
  // doubles. We don't expect to always get the same value back
  // on casting back in that case.
  static_assert(!std::is_same<IN_TYPE, float>::value
                    && !std::is_same<IN_TYPE, double>::value
                    && !std::is_same<IN_TYPE, const float>::value
                    && !std::is_same<IN_TYPE, const double>::value
                    && !std::is_same<OUT_TYPE, float>::value
                    && !std::is_same<OUT_TYPE, double>::value
                    && !std::is_same<OUT_TYPE, const float>::value
                    && !std::is_same<OUT_TYPE, const double>::value,
                "static_cast_check_fit cannot be used with floats or doubles.");
#if BA_DEBUG_BUILD
  assert(static_cast<IN_TYPE>(static_cast<OUT_TYPE>(in)) == in);
#endif
  return static_cast<OUT_TYPE>(in);
}

/// Like static_cast_check_fit, but runs checks even in release builds and
/// throws an Exception on failure.
template <typename OUT_TYPE, typename IN_TYPE>
auto static_cast_check_fit_always(IN_TYPE in) -> OUT_TYPE {
  // Make sure we don't try to use this when casting to or from floats or
  // doubles. We don't expect to always get the same value back
  // on casting back in that case.
  static_assert(
      !std::is_same<IN_TYPE, float>::value
          && !std::is_same<IN_TYPE, double>::value
          && !std::is_same<IN_TYPE, const float>::value
          && !std::is_same<IN_TYPE, const double>::value
          && !std::is_same<OUT_TYPE, float>::value
          && !std::is_same<OUT_TYPE, double>::value
          && !std::is_same<OUT_TYPE, const float>::value
          && !std::is_same<OUT_TYPE, const double>::value,
      "static_cast_always_checked cannot be used with floats or doubles.");
  auto out = static_cast<OUT_TYPE>(in);
  if (static_cast<IN_TYPE>(out) != in) {
    throw Exception("static_cast_check_fit_always failed for value "
                    + std::to_string(in) + ".");
  }
  return static_cast<OUT_TYPE>(in);
}

/// Simply a static_cast, but in debug builds also runs a dynamic cast to
/// ensure the results would have been the same. Handy for keeping casts
/// lightweight when types are known while still having a sanity check.
template <typename OUT_TYPE, typename IN_TYPE>
auto static_cast_check_type(IN_TYPE in) -> OUT_TYPE {
  auto out_static = static_cast<OUT_TYPE>(in);
#if BA_DEBUG_BUILD
  auto out_dynamic = dynamic_cast<OUT_TYPE>(in);
  assert(out_static == out_dynamic);
#endif
  return out_static;
}

// This call hijacks compile-type pretty-function-printing functionality
// to give human-readable strings for arbitrary types. Note that these
// will not be consistent across platforms and should only be used for
// logging/debugging. Also note that this code is dependent on very specific
// compiler output which could change at any time; to watch out for this
// it is recommended to add static_assert()s somewhere to ensure that
// output for a few given types matches expected result(s).
template <typename T>
constexpr auto static_type_name_constexpr(bool debug_full = false)
    -> std::string_view {
  std::string_view name, prefix, suffix;
#ifdef __clang__
  name = __PRETTY_FUNCTION__;
  prefix =
      "std::string_view ballistica::"
      "static_type_name_constexpr(bool) [T = ";
  suffix = "]";
#elif defined(__GNUC__)
  name = __PRETTY_FUNCTION__;
  prefix =
      "constexpr std::string_view "
      "ballistica::static_type_name_constexpr(bool) "
      "[with T = ";
  suffix = "; std::string_view = std::basic_string_view<char>]";
#elif defined(_MSC_VER)
  name = __FUNCSIG__;
  prefix =
      "class std::basic_string_view<char,struct std::char_traits<char> > "
      "__cdecl ballistica::static_type_name_constexpr<";
  suffix = ">(bool)";
#else
#error unimplemented
#endif
  if (debug_full) {
    return name;
  }
  name.remove_prefix(prefix.size());
  name.remove_suffix(suffix.size());
  return name;
}

/// Return a human-readable string for the template type.
template <typename T>
static auto static_type_name(bool debug_full = false) -> std::string {
  return std::string(static_type_name_constexpr<T>(debug_full));
}

}  // namespace ballistica

#endif  // __cplusplus

#endif  // BALLISTICA_CORE_INLINE_H_
