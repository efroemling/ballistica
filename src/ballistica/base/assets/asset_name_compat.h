// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_ASSETS_ASSET_NAME_COMPAT_H_
#define BALLISTICA_BASE_ASSETS_ASSET_NAME_COMPAT_H_

#include <string>

#include "ballistica/base/base.h"

namespace ballistica::base {

/// Bidirectional mapping between legacy bare asset names and their
/// asset-package homes, for the surfaces where legacy names still
/// flow: the scene_v1 wire and replays (which stay permanently
/// legacy-named), server-driven docui content, and modder bare-name
/// refs. The legacy side of the table is a frozen snapshot; it grows
/// one row per asset as migrations land and existing rows never
/// change. A project-update check verifies the asset-package side
/// against the wrapper modules so package-path renames can't silently
/// strand a row. All calls must be made in the logic thread.
class AssetNameCompat {
 public:
  /// Register the full asset-package version id in effect for a
  /// package key ('builtinassets' / 'classicassets'). Called at
  /// classic-app-mode activation with values sourced from the Python
  /// wrapper modules' __asset_package__ attrs, so a modder-swapped
  /// package keeps working as long as it carries the same logical
  /// paths.
  static void SetPackageVersion(const std::string& package_key,
                                const std::string& apverid);

  /// Given a possibly-legacy bare asset name, return the qualified
  /// asset-package ref it now lives at (if it has a known home and
  /// that package's version has been registered); otherwise return
  /// the name unchanged. ``kind`` is the logical-path head the caller
  /// wants ('textures', 'audio', 'meshes', ...) — legacy names were
  /// only unique per asset type ('shield' names both a texture and a
  /// mesh), so lookups are kind-scoped.
  static auto FromLegacy(const std::string& name, const char* kind)
      -> std::string;

  /// Given a possibly-qualified asset-package ref, return the legacy
  /// bare name old peers expect (if its package and logical path have
  /// one); otherwise return the name unchanged. The apverid's version
  /// segment is ignored when matching, so any registered package
  /// version maps.
  static auto ToLegacy(const std::string& name) -> std::string;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_ASSETS_ASSET_NAME_COMPAT_H_
