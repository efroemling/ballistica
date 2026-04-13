// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SHARED_BUILDCONFIG_BUILDCONFIG_WINDOWS_HEADLESS_H_
#define BALLISTICA_SHARED_BUILDCONFIG_BUILDCONFIG_WINDOWS_HEADLESS_H_

// note: define overrides BEFORE common header

// Currently building these as test variant. Can reconsider at some point if
// we want to make things slightly more streamlined.
#define BA_VARIANT "test_build"
#define BA_VARIANT_TEST_BUILD 1

#define BA_ENABLE_STDIO_CONSOLE 1
#define BA_HEADLESS_BUILD 1
#define BA_MINSDL_BUILD 1

#include "ballistica/shared/buildconfig/buildconfig_windows_common.h"

// This must always be last.
#include "ballistica/shared/buildconfig/buildconfig_common.h"

#endif  // BALLISTICA_SHARED_BUILDCONFIG_BUILDCONFIG_WINDOWS_HEADLESS_H_
