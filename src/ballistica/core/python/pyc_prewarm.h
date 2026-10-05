// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_CORE_PYTHON_PYC_PREWARM_H_
#define BALLISTICA_CORE_PYTHON_PYC_PREWARM_H_

#include <string>
#include <utility>
#include <vector>

namespace ballistica::core {

/// Args for InstallPycPrewarm().
struct PycPrewarmArgs {
  /// The bundled pycache_prewarm dir (payload pycs + manifest).
  std::string prewarm_dir;
  /// Maps manifest root keys ('app', 'site', 'pylib') to the actual
  /// on-disk source dirs those payload pycs were compiled from.
  std::vector<std::pair<std::string, std::string>> roots;
  /// Python's pycache_prefix dir to install into.
  std::string pycache_prefix;
  /// Expected interpreter cache tag (e.g. 'cpython-314'); payloads
  /// built for any other interpreter are ignored wholesale.
  std::string cache_tag;
  /// Expected optimize level (must match the interpreter's runtime
  /// level; see core_python.cc optimization_level).
  int optimize{};
  /// Worker thread count override; <= 0 means auto (the platform's
  /// benched sweet spot).
  int threads{};
  /// Install-once marker value (typically the app build number);
  /// empty disables marker logic (every call installs).
  std::string marker;
};

/// Results from InstallPycPrewarm().
struct PycPrewarmResult {
  /// Payload pycs installed.
  int installed{};
  /// Entries skipped because the installed source is absent or no
  /// longer byte-identical to what the pyc was built from -- the
  /// EXPECTED benign case (a modder edited a builtin .py); those get
  /// compiled organically and the edit is honored.
  int skipped_modified{};
  /// Entries that failed on an actual I/O error (read/write/rename) --
  /// UNEXPECTED; surfaced (with a few sample reasons in `errors`) so a
  /// real disk/permissions problem isn't hidden as a benign skip.
  int errored{};
  /// True if the whole payload was rejected (no/invalid manifest or
  /// interpreter mismatch) or already installed per the marker.
  bool noop{};
  /// Time spent pre-creating dst dirs (perf diagnostics).
  double dirs_ms{};
  /// First few `errored` reasons, for logging (bounded so a
  /// pathological run can't balloon this).
  std::vector<std::string> errors;
};

/// Install a bundled pycache_prewarm payload into the pycache_prefix
/// tree so Python's imports find everything pre-compiled from the very
/// first launch (see docs/initiatives/pyc-prewarm-bundling.md).
///
/// MONOLITHIC BUILDS ONLY: must run before the interpreter comes up so
/// every import benefits (modular builds have Python running before
/// any of our native code and can't use this).
///
/// For each manifest entry, verifies the installed source file is
/// byte-identical to what the payload pyc was compiled from (size +
/// BLAKE2b check, so user-modified sources are never masked by a stale
/// pyc), then writes the pyc with its header patched to
/// timestamp-invalidation against the source's actual mtime/size.
/// Multithreaded; purely filesystem work.
auto InstallPycPrewarm(const PycPrewarmArgs& args) -> PycPrewarmResult;

}  // namespace ballistica::core

#endif  // BALLISTICA_CORE_PYTHON_PYC_PREWARM_H_
