// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SHARED_GENERIC_THREAD_CPU_TIME_H_
#define BALLISTICA_SHARED_GENERIC_THREAD_CPU_TIME_H_

#include <chrono>
#include <ctime>

#include "ballistica/shared/ballistica.h"

namespace ballistica {

/// Cpu time the calling thread has used so far, in milliseconds.
///
/// For timing work that spends part of its wall time blocked (a render
/// waiting on the display, say): time spent blocked is not counted
/// here. Falls back to wall time on platforms that can't report
/// per-thread cpu time (Windows).
inline auto ThreadCPUTimeMillisecs() -> double {
#if BA_PLATFORM_WINDOWS
  return std::chrono::duration<double, std::milli>(
             std::chrono::steady_clock::now().time_since_epoch())
      .count();
#else
  timespec ts{};
  clock_gettime(CLOCK_THREAD_CPUTIME_ID, &ts);
  return 1000.0 * static_cast<double>(ts.tv_sec)
         + static_cast<double>(ts.tv_nsec) / 1000000.0;
#endif
}

}  // namespace ballistica

#endif  // BALLISTICA_SHARED_GENERIC_THREAD_CPU_TIME_H_
