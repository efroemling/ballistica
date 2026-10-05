#pragma once

// Including SDKDDKVer.h defines the highest available Windows platform.

// If you wish to build your application for a previous Windows platform, include WinSDKVer.h and
// set the _WIN32_WINNT macro to the platform you wish to support before including SDKDDKVer.h.

#include <WinSDKVer.h>

// Targeting Windows 10, which is our officially supported floor.
//
// This said Windows 7 for years after that stopped being true -- the
// Python we bundle dropped Win7 back in the 3.9 days, so these builds
// could not run there regardless of what we declared (see the 1.6.4
// changelog note telling Win7 users to stay on older builds). Keep
// this in sync with the actual support policy; libraries increasingly
// enforce a floor of their own (cpp-httplib, used by the fatal-error
// reporter, hard #errors below Windows 10).
#define WINVER _WIN32_WINNT_WIN10
#define _WIN32_WINNT _WIN32_WINNT_WIN10

#include <SDKDDKVer.h>
