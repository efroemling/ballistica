// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SHARED_NETWORKING_NETWORKING_SYS_H_
#define BALLISTICA_SHARED_NETWORKING_NETWORKING_SYS_H_

// Include everything needed for standard sockets api usage.

#if BA_PLATFORM_WINDOWS
// (need includes to stay in this order to disabling formatting)
// clang-format off
#include <ws2tcpip.h>
#include <iphlpapi.h>
// clang-format on
#else
#include <arpa/inet.h>
#include <netdb.h>
#include <netinet/in.h>
#include <poll.h>
#include <sys/socket.h>  // IWYU pragma: export
#include <sys/types.h>
#include <unistd.h>
#if BA_PLATFORM_ANDROID
// NOTE TO SELF: Apparently once we target API 24, ifaddrs.h is available.
#include "ballistica/core/platform/android/ifaddrs_android_ext.h"
#else
#include <ifaddrs.h>
#endif
#endif

#endif  // BALLISTICA_SHARED_NETWORKING_NETWORKING_SYS_H_
