// Released under the MIT License. See LICENSE for details.

#include "ballistica/core/python/pyc_prewarm.h"

#ifdef _WIN32
#include <direct.h>
#include <fcntl.h>
#include <io.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <windows.h>
#else
#include <fcntl.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>
#endif

#include <atomic>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <mutex>
#include <set>
#include <string>
#include <thread>
#include <utility>
#include <vector>

#include "ballistica/shared/ballistica.h"
#include "ballistica/shared/generic/json_facade.h"
#include "external/monocypher/monocypher.h"

namespace ballistica::core {

namespace {

/// Digest size matching batools._prewarmstage.HASH_DIGEST_SIZE.
constexpr size_t kHashDigestSize{16};

/// Manifest format we understand (batools._prewarmstage).
constexpr int kManifestVersion{1};

struct Entry_ {
  std::string src_path;      // Installed source .py.
  std::string payload_path;  // Bundled pyc within the prewarm dir.
  std::string dst_path;      // Final pyc under pycache_prefix.
  int64_t src_size{};
  std::string src_hash_hex;  // Lowercase hex BLAKE2b-16.
};

// ---- Tiny portability shims (raw CRT/syscall I/O for speed). -------------

#ifdef _WIN32
using FileStat_ = struct __stat64;

// All windows path calls go through wide-char APIs: the narrow CRT
// variants use the ANSI codepage and fail on non-ascii paths (e.g. a
// cache dir under a non-ascii username), while our path strings are
// UTF-8 throughout (same reasoning as PlatformWindows::Stat etc.).
auto ToWide_(const std::string& utf8) -> std::wstring {
  if (utf8.empty()) {
    return std::wstring();
  }
  int size = MultiByteToWideChar(CP_UTF8, 0, utf8.data(),
                                 static_cast<int>(utf8.size()), nullptr, 0);
  std::wstring out(static_cast<size_t>(size), 0);
  MultiByteToWideChar(CP_UTF8, 0, utf8.data(), static_cast<int>(utf8.size()),
                      out.data(), size);
  return out;
}

auto FromWide_(const std::wstring& wide) -> std::string {
  if (wide.empty()) {
    return std::string();
  }
  int size = WideCharToMultiByte(CP_UTF8, 0, wide.data(),
                                 static_cast<int>(wide.size()), nullptr, 0,
                                 nullptr, nullptr);
  std::string out(static_cast<size_t>(size), 0);
  WideCharToMultiByte(CP_UTF8, 0, wide.data(), static_cast<int>(wide.size()),
                      out.data(), size, nullptr, nullptr);
  return out;
}
#else
using FileStat_ = struct stat;
#endif

auto StatPath_(const std::string& path, FileStat_* out) -> bool {
#ifdef _WIN32
  return _wstat64(ToWide_(path).c_str(), out) == 0;
#else
  return stat(path.c_str(), out) == 0;
#endif
}

auto OpenRead_(const std::string& path) -> int {
#ifdef _WIN32
  return _wopen(ToWide_(path).c_str(), _O_RDONLY | _O_BINARY);
#else
  return open(path.c_str(), O_RDONLY);
#endif
}

auto OpenWriteTrunc_(const std::string& path) -> int {
#ifdef _WIN32
  return _wopen(ToWide_(path).c_str(),
                _O_WRONLY | _O_CREAT | _O_TRUNC | _O_BINARY,
                _S_IREAD | _S_IWRITE);
#else
  return open(path.c_str(), O_WRONLY | O_CREAT | O_TRUNC, 0644);
#endif
}

auto ReadFd_(int filedesc, void* buf, size_t len) -> int64_t {
#ifdef _WIN32
  return _read(filedesc, buf, static_cast<unsigned int>(len));
#else
  return read(filedesc, buf, len);
#endif
}

auto WriteFd_(int filedesc, const void* buf, size_t len) -> int64_t {
#ifdef _WIN32
  return _write(filedesc, buf, static_cast<unsigned int>(len));
#else
  return write(filedesc, buf, len);
#endif
}

void CloseFd_(int filedesc) {
#ifdef _WIN32
  _close(filedesc);
#else
  close(filedesc);
#endif
}

void MkDir_(const std::string& path) {
#ifdef _WIN32
  _wmkdir(ToWide_(path).c_str());
#else
  mkdir(path.c_str(), 0755);
#endif
}

void RemoveFile_(const std::string& path) {
#ifdef _WIN32
  _wremove(ToWide_(path).c_str());
#else
  remove(path.c_str());
#endif
}

/// Rename with replace-existing semantics on all platforms. POSIX
/// rename() replaces atomically by definition. Windows rename errors
/// if the target exists (the quirk PlatformWindows::Rename also works
/// around), so there we remove-then-rename: this leaves a brief
/// window where the target momentarily doesn't exist, but that only
/// ever makes a concurrent importer recompile that one module (safe)
/// -- it can never expose a truncated file, which is the guarantee
/// that matters. (MoveFileExW with MOVEFILE_REPLACE_EXISTING was
/// tried as a true one-call replace but failed at runtime replacing
/// existing/locked targets -- ~30 silent failures + the marker on a
/// pre-populated cache; the proven remove-first path is used instead.
/// Revisit with GetLastError diagnostics if a true atomic replace is
/// ever wanted.)
auto RenameFile_(const std::string& from, const std::string& to) -> bool {
#ifdef _WIN32
  _wremove(ToWide_(to).c_str());
  return _wrename(ToWide_(from).c_str(), ToWide_(to).c_str()) == 0;
#else
  return rename(from.c_str(), to.c_str()) == 0;
#endif
}

auto GetPid_() -> int64_t {
#ifdef _WIN32
  return static_cast<int64_t>(GetCurrentProcessId());
#else
  return static_cast<int64_t>(getpid());
#endif
}

auto GetCwd_() -> std::string {
#ifdef _WIN32
  wchar_t cwd[4096];
  if (_wgetcwd(cwd, 4096) == nullptr) {
    return std::string();
  }
  return FromWide_(cwd);
#else
  char cwd[4096];
  if (getcwd(cwd, sizeof(cwd)) == nullptr) {
    return std::string();
  }
  return cwd;
#endif
}

auto IsPathSep_(char character) -> bool {
  return character == '/' || character == '\\';
}

auto IsAbsPath_(const std::string& path) -> bool {
  if (path.empty()) {
    return false;
  }
  if (IsPathSep_(path[0])) {
    return true;
  }
  // Windows drive form ('C:...') counts as absolute for our purposes
  // (our controlled inputs never use drive-relative paths).
  return path.size() >= 2 && path[1] == ':';
}

// --------------------------------------------------------------------------

auto ReadFileBytes_(const std::string& path, std::vector<uint8_t>* out)
    -> bool {
  FileStat_ filestat{};
  if (!StatPath_(path, &filestat)) {
    return false;
  }
  int filedesc = OpenRead_(path);
  if (filedesc < 0) {
    return false;
  }
  auto size = static_cast<size_t>(filestat.st_size);
  out->resize(size);
  auto readsize = ReadFd_(filedesc, out->data(), size);
  CloseFd_(filedesc);
  return readsize == static_cast<int64_t>(size);
}

auto HashHex_(const std::vector<uint8_t>& data) -> std::string {
  uint8_t digest[kHashDigestSize];
  crypto_blake2b(digest, sizeof(digest), data.data(), data.size());
  static const char* hexchars = "0123456789abcdef";
  std::string out;
  out.reserve(kHashDigestSize * 2);
  for (auto byteval : digest) {
    out.push_back(hexchars[byteval >> 4u]);
    out.push_back(hexchars[byteval & 0xFu]);
  }
  return out;
}

/// os.path.abspath semantics (cwd-join + no symlink resolution) minus
/// dot-segment cleanup we don't need for our controlled inputs.
auto AbsPath_(const std::string& path) -> std::string {
  if (IsAbsPath_(path)) {
    return path;
  }
  auto out = GetCwd_();
  if (out.empty()) {
    return path;
  }
  if (path == ".") {
    return out;
  }
  std::string rel = path;
  while (rel.size() >= 2 && rel[0] == '.' && IsPathSep_(rel[1])) {
    rel = rel.substr(2);
  }
  return out + "/" + rel;
}

/// The piece of an absolute source path that lives under
/// pycache_prefix: importlib's cache_from_source drops the drive (on
/// windows) and any leading separators, then joins under the prefix.
auto CacheRelPath_(const std::string& abspath) -> std::string {
  std::string out = abspath;
  if (out.size() >= 2 && out[1] == ':') {
    out = out.substr(2);
  }
  size_t start = 0;
  while (start < out.size() && IsPathSep_(out[start])) {
    ++start;
  }
  return out.substr(start);
}

void MakeDirs_(const std::string& path, std::set<std::string>* made) {
  if (made->count(path)) {
    return;
  }
  std::string sofar;
  size_t pos = 0;
  while (pos != std::string::npos) {
    size_t next_slash = std::string::npos;
    for (size_t i = pos + 1; i < path.size(); ++i) {
      if (IsPathSep_(path[i])) {
        next_slash = i;
        break;
      }
    }
    pos = next_slash;
    sofar = (pos == std::string::npos) ? path : path.substr(0, pos);
    if (!sofar.empty() && made->insert(sofar).second) {
      MkDir_(sofar);
    }
  }
}

/// Outcome of processing one entry.
enum class EntryResult_ {
  kInstalled,
  kModified,  // Source absent/changed -- benign; organic recompile.
  kError,     // I/O failure -- unexpected.
};

/// Process one entry: verify source, patch header, write dst pyc.
/// ``err_out`` receives a short reason on kError.
auto InstallEntry_(const Entry_& entry, std::vector<uint8_t>* srcbytes,
                   std::vector<uint8_t>* pycbytes,
                   const std::string& thread_suffix, std::string* err_out)
    -> EntryResult_ {
  // Source must exist with the exact expected size (fast reject for
  // most user modifications without reading a byte). A missing/
  // resized source is the benign modder case, not an error.
  FileStat_ srcstat{};
  if (!StatPath_(entry.src_path, &srcstat)
      || static_cast<int64_t>(srcstat.st_size) != entry.src_size) {
    return EntryResult_::kModified;
  }
  // ...and hash to what the payload pyc was compiled from, so a
  // user-modified source is never masked by our pyc. A hash mismatch
  // is a modded source (benign); a read failure on a size-matching
  // source is a real I/O error.
  if (!ReadFileBytes_(entry.src_path, srcbytes)) {
    *err_out = "source read failed: " + entry.src_path;
    return EntryResult_::kError;
  }
  if (HashHex_(*srcbytes) != entry.src_hash_hex) {
    return EntryResult_::kModified;
  }

  // Header patch values (PEP 552): flags word -> 0 (timestamp
  // invalidation) and the installed source's actual mtime+size, so
  // validation is correct by construction no matter what any
  // installer did to file times. Little-endian u32s at offset 4.
  uint8_t header_patch[12];
  auto put_u32 = [&header_patch](size_t offset, uint32_t val) {
    header_patch[offset] = static_cast<uint8_t>(val & 0xFFu);
    header_patch[offset + 1] = static_cast<uint8_t>((val >> 8u) & 0xFFu);
    header_patch[offset + 2] = static_cast<uint8_t>((val >> 16u) & 0xFFu);
    header_patch[offset + 3] = static_cast<uint8_t>((val >> 24u) & 0xFFu);
  };
  put_u32(0, 0u);
  put_u32(4, static_cast<uint32_t>(srcstat.st_mtime));
  put_u32(8, static_cast<uint32_t>(srcstat.st_size));

  // (An APFS clonefile+pwrite fast path was benched here and lost to
  // plain read+write at our file sizes: the clone is a metadata
  // transaction and its extra round trips cost more than copying a
  // few KB.)
  auto& pyc = *pycbytes;
  if (!ReadFileBytes_(entry.payload_path, pycbytes) || pyc.size() < 16) {
    *err_out = "payload pyc read failed: " + entry.payload_path;
    return EntryResult_::kError;
  }
  memcpy(pyc.data() + 4, header_patch, sizeof(header_patch));

  // Write via temp + rename so a concurrent app instance
  // (double-launch) or a mid-install kill can never expose a
  // half-written pyc to an importing interpreter (a truncated body
  // behind a valid header raises at import rather than recompiling).
  // Temp name is process+thread-unique. RenameFile_ is atomic on
  // posix; on windows it remove-then-renames (a brief no-file window
  // that at worst makes an importer recompile that one module --
  // never a truncated read; see RenameFile_).
  std::string tmp_path = entry.dst_path + ".tmp" + thread_suffix;
  int outdesc = OpenWriteTrunc_(tmp_path);
  if (outdesc < 0) {
    *err_out = "temp open failed: " + tmp_path;
    return EntryResult_::kError;
  }
  auto wrote = WriteFd_(outdesc, pyc.data(), pyc.size());
  CloseFd_(outdesc);
  if (wrote != static_cast<int64_t>(pyc.size())) {
    RemoveFile_(tmp_path);
    *err_out = "temp write failed: " + tmp_path;
    return EntryResult_::kError;
  }
  if (!RenameFile_(tmp_path, entry.dst_path)) {
    RemoveFile_(tmp_path);
    *err_out = "rename failed: " + entry.dst_path;
    return EntryResult_::kError;
  }
  return EntryResult_::kInstalled;
}

}  // namespace

auto InstallPycPrewarm(const PycPrewarmArgs& args) -> PycPrewarmResult {
  PycPrewarmResult result;

  // Marker short-circuit: one successful install per marker value
  // (the caller passes the app build number, so each update
  // reinstalls once and every boot after that is a single tiny
  // read). Lives inside the pycache dir so an OS cache wipe clears
  // both together and the next boot self-heals.
  std::string marker_path = args.pycache_prefix + "/pyc_prewarm_installed";
  std::string marker_value = args.marker + " " + args.cache_tag + " opt"
                             + std::to_string(args.optimize) + "\n";
  if (!args.marker.empty()) {
    std::vector<uint8_t> marker_bytes;
    if (ReadFileBytes_(marker_path, &marker_bytes)
        && std::string(marker_bytes.begin(), marker_bytes.end())
               == marker_value) {
      result.noop = true;
      return result;
    }
  }

  // Read + parse the manifest; no manifest means no payload.
  std::vector<uint8_t> manifest_bytes;
  if (!ReadFileBytes_(args.prewarm_dir + "/manifest.json", &manifest_bytes)) {
    result.noop = true;
    return result;
  }
  auto doc = JsonDoc::Parse(
      std::string_view(reinterpret_cast<const char*>(manifest_bytes.data()),
                       manifest_bytes.size()));
  if (!doc.has_value()) {
    result.noop = true;
    return result;
  }
  auto root = doc->root();
  if (root["version"].int_or(-1) != kManifestVersion
      || root["cache_tag"].string_or("") != args.cache_tag
      || root["optimize"].int_or(-1) != args.optimize) {
    // Built for some other interpreter/config; ignore wholesale.
    result.noop = true;
    return result;
  }

  std::string optsuffix =
      args.optimize > 0 ? ".opt-" + std::to_string(args.optimize) : "";
  std::string pycsuffix = "." + args.cache_tag + optsuffix + ".pyc";

  // Resolve roots to the absolute paths Python will see at import
  // time (pycache_prefix layout mirrors absolute source paths).
  std::vector<std::pair<std::string, std::string>> abs_roots;
  abs_roots.reserve(args.roots.size());
  for (const auto& root_pair : args.roots) {
    abs_roots.emplace_back(root_pair.first, AbsPath_(root_pair.second));
  }

  // Build the entry list.
  std::vector<Entry_> entries;
  auto manifest_entries = root["entries"];
  entries.reserve(manifest_entries.size());
  for (const auto& [key, val] : manifest_entries.items()) {
    // Key is '<rootkey>/<relpath>.py'.
    auto slashpos = key.find('/');
    if (slashpos == std::string_view::npos) {
      continue;
    }
    std::string rootkey(key.substr(0, slashpos));
    std::string relpath(key.substr(slashpos + 1));
    const std::string* rootbase{};
    for (const auto& root_pair : abs_roots) {
      if (root_pair.first == rootkey) {
        rootbase = &root_pair.second;
        break;
      }
    }
    if (rootbase == nullptr || relpath.size() < 4) {
      // Unknown root key or a too-short key: a malformed/foreign
      // manifest entry, not an I/O error -- treat as a benign skip.
      result.skipped_modified++;
      continue;
    }
    std::string relstem = relpath.substr(0, relpath.size() - 3);  // '.py'
    Entry_ entry;
    entry.src_path = *rootbase + "/" + relpath;
    entry.payload_path =
        args.prewarm_dir + "/" + rootkey + "/" + relstem + pycsuffix;
    // pycache_prefix layout: prefix + (drive-stripped) abs source dir
    // + cache-tagged file name, mirroring importlib's
    // cache_from_source. Separator spelling need not match Python's
    // (both resolve to the same file); components must.
    entry.dst_path = args.pycache_prefix + "/" + CacheRelPath_(*rootbase) + "/"
                     + relstem + pycsuffix;
    entry.src_size = val["s"].int_or(-1);
    entry.src_hash_hex = std::string(val["h"].string_or(""));
    entries.push_back(std::move(entry));
  }

  // Pre-create all dst dirs in one pass, single-threaded (no races in
  // workers), memoized so shared parent chains cost one mkdir each.
  auto dirs_start = std::chrono::steady_clock::now();
  std::set<std::string> dstdirs;
  for (const auto& entry : entries) {
    auto slashpos = entry.dst_path.rfind('/');
    if (slashpos != std::string::npos) {
      dstdirs.insert(entry.dst_path.substr(0, slashpos));
    }
  }
  std::set<std::string> made_dirs;
  for (const auto& dstdir : dstdirs) {
    MakeDirs_(dstdir, &made_dirs);
  }
  result.dirs_ms = std::chrono::duration_cast<std::chrono::microseconds>(
                       std::chrono::steady_clock::now() - dirs_start)
                       .count()
                   / 1000.0;

  // Chew through entries multithreaded. Benched 2026-09-01 on ~1030
  // files: APFS/mac ~4-8 workers best (metadata contention +
  // efficiency cores make more threads worse); NTFS/windows benched
  // far higher optima (32-64) but that box is EC2/EBS whose
  // network-storage latency likely inflates the win, so per Eric we
  // hold ONE conservative value everywhere until benched on real
  // consumer hardware. The BA_PYC_PREWARM_THREADS override remains
  // for sweeps.
  constexpr unsigned int kDefaultThreads{8};
  unsigned int thread_count = args.threads > 0
                                  ? static_cast<unsigned int>(args.threads)
                                  : kDefaultThreads;
  if (thread_count < 1) {
    thread_count = 1;
  }
  std::atomic<size_t> next_index{0};
  std::atomic<int> installed{0};
  std::atomic<int> modified{0};
  std::atomic<int> errored{0};
  std::atomic<unsigned int> next_worker_id{0};
  std::mutex errors_mutex;
  std::vector<std::string> errors;
  constexpr size_t kMaxErrorSamples{8};
  auto worker = [&entries, &next_index, &installed, &modified, &errored,
                 &next_worker_id, &errors_mutex, &errors] {
    // Reusable per-thread buffers (grow once, no per-file allocs)
    // and a unique temp-file suffix for atomic writes. Includes the
    // pid so concurrent app instances can't collide on temp names.
    std::string thread_suffix = "." + std::to_string(GetPid_()) + "."
                                + std::to_string(next_worker_id.fetch_add(1));
    std::vector<uint8_t> srcbuf;
    std::vector<uint8_t> pycbuf;
    while (true) {
      size_t index = next_index.fetch_add(1);
      if (index >= entries.size()) {
        break;
      }
      // A single entry must never take the whole run (or the thread,
      // and thus the boot) down -- this is a pure optimization, so
      // any unexpected throw (bad_alloc, etc.) degrades to "that
      // module compiles organically". Nothing here may escape.
      try {
        std::string err;
        switch (InstallEntry_(entries[index], &srcbuf, &pycbuf, thread_suffix,
                              &err)) {
          case EntryResult_::kInstalled:
            installed.fetch_add(1);
            break;
          case EntryResult_::kModified:
            modified.fetch_add(1);
            break;
          case EntryResult_::kError:
            errored.fetch_add(1);
            {
              std::scoped_lock lock(errors_mutex);
              if (errors.size() < kMaxErrorSamples) {
                errors.push_back(err);
              }
            }
            break;
        }
      } catch (...) {
        errored.fetch_add(1);
        std::scoped_lock lock(errors_mutex);
        if (errors.size() < kMaxErrorSamples) {
          errors.push_back("exception installing " + entries[index].dst_path);
        }
      }
    }
  };
  if (thread_count == 1 || entries.size() < 32) {
    worker();
  } else {
    // Spawn defensively: if thread creation fails partway (e.g. an OS
    // thread limit), run the remaining work on this thread rather
    // than letting std::system_error escape -- and ALWAYS join what
    // we did create (a joinable std::thread destructor terminates).
    std::vector<std::thread> threads;
    threads.reserve(thread_count);
    try {
      for (unsigned int i = 0; i < thread_count; ++i) {
        threads.emplace_back(worker);
      }
    } catch (...) {
      worker();  // Finish the remainder inline.
    }
    for (auto& thread : threads) {
      thread.join();
    }
  }
  result.installed += installed.load();
  result.skipped_modified += modified.load();
  result.errored += errored.load();
  result.errors = std::move(errors);

  // Certify via the marker (temp + rename so a crash mid-write can't
  // leave a valid-looking marker; a missing marker just means we redo
  // the idempotent install next boot). Modified-source skips don't
  // block certification (they are deliberately left to organic
  // compiles). I/O ERRORS do: leaving the marker off means the next
  // boot retries the failed entries rather than trusting a partial
  // install -- the whole thing is idempotent, so a retry is free.
  if (!args.marker.empty() && result.errored == 0) {
    std::string tmp_path = marker_path + ".tmp";
    int markdesc = OpenWriteTrunc_(tmp_path);
    if (markdesc >= 0) {
      auto wrote = WriteFd_(markdesc, marker_value.data(), marker_value.size());
      CloseFd_(markdesc);
      if (wrote == static_cast<int64_t>(marker_value.size())) {
        RenameFile_(tmp_path, marker_path);
      }
    }
  }
  return result;
}

}  // namespace ballistica::core
