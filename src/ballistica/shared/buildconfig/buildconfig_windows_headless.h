// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SHARED_BUILDCONFIG_BUILDCONFIG_WINDOWS_HEADLESS_H_
#define BALLISTICA_SHARED_BUILDCONFIG_BUILDCONFIG_WINDOWS_HEADLESS_H_

// note: define overrides BEFORE common header

// These are the server bundles we distribute for third-party operators
// (the ballistica.net downloads page) — variant = distribution
// audience. See the AppVariant enum in tools/bacommon/app.py.
#define BA_VARIANT "server"
#define BA_VARIANT_SERVER 1

#define BA_ENABLE_STDIO_CONSOLE 1
#define BA_HEADLESS_BUILD 1
#define BA_MINSDL_BUILD 1

#include "ballistica/shared/buildconfig/buildconfig_windows_common.h"

// This must always be last.
#include "ballistica/shared/buildconfig/buildconfig_common.h"

#endif  // BALLISTICA_SHARED_BUILDCONFIG_BUILDCONFIG_WINDOWS_HEADLESS_H_
