// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/assets/asset_name_compat.h"

#include <string>
#include <unordered_map>
#include <utility>

#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging.h"

namespace ballistica::base {

struct Row_ {
  const char* legacy;
  const char* package_key;
  const char* logical_path;
};

// One row per migrated asset. The legacy side is frozen (old peers and
// replays speak these names forever); the (package_key, logical_path)
// side must track package contents - update_project --check verifies
// it against the wrapper modules. Add a row here whenever an asset
// migrates out of the legacy tree.
static const Row_ kRows[] = {
    {"actionButtons", "builtinassets", "textures/action_buttons"},
    {"arrow", "builtinassets", "textures/arrow"},
    {"backIcon", "builtinassets", "textures/back_icon"},
    {"black", "builtinassets", "textures/black"},
    {"bombButton", "builtinassets", "textures/bomb_button"},
    {"boxingGlovesColor", "builtinassets", "textures/boxing_gloves_color"},
    {"buttonSquare", "builtinassets", "textures/button_square"},
    {"buttonSquareWide", "builtinassets", "textures/button_square_wide"},
    {"characterIconMask", "builtinassets", "textures/character_icon_mask"},
    {"circle", "builtinassets", "textures/circle"},
    {"circleNoAlpha", "builtinassets", "textures/circle_no_alpha"},
    {"circleOutline", "builtinassets", "textures/circle_outline"},
    {"circleOutlineNoAlpha", "builtinassets",
     "textures/circle_outline_no_alpha"},
    {"circleShadow", "builtinassets", "textures/circle_shadow"},
    {"circleSoft", "builtinassets", "textures/circle_soft"},
    {"cursor", "builtinassets", "textures/cursor"},
    {"explosion", "builtinassets", "textures/explosion"},
    {"eyeColor", "builtinassets", "textures/eye_color"},
    {"eyeColorTintMask", "builtinassets", "textures/eye_color_tint_mask"},
    {"flagPoleColor", "builtinassets", "textures/flag_pole_color"},
    {"fontBig", "builtinassets", "textures/font_big"},
    {"fontExtras", "builtinassets", "textures/font_extras"},
    {"fontExtras2", "builtinassets", "textures/font_extras2"},
    {"fontExtras3", "builtinassets", "textures/font_extras3"},
    {"fontExtras4", "builtinassets", "textures/font_extras4"},
    {"fontExtras5", "builtinassets", "textures/font_extras5"},
    {"fontSmall0", "builtinassets", "textures/font_small0"},
    {"fontSmall1", "builtinassets", "textures/font_small1"},
    {"fontSmall2", "builtinassets", "textures/font_small2"},
    {"fontSmall3", "builtinassets", "textures/font_small3"},
    {"fontSmall4", "builtinassets", "textures/font_small4"},
    {"fontSmall5", "builtinassets", "textures/font_small5"},
    {"fontSmall6", "builtinassets", "textures/font_small6"},
    {"fontSmall7", "builtinassets", "textures/font_small7"},
    {"fuse", "builtinassets", "textures/fuse"},
    {"glow", "builtinassets", "textures/glow"},
    {"light", "builtinassets", "textures/light"},
    {"lightSharp", "builtinassets", "textures/light_sharp"},
    {"lightSoft", "builtinassets", "textures/light_soft"},
    {"menuButton", "builtinassets", "textures/menu_button"},
    {"nub", "builtinassets", "textures/nub"},
    {"ouyaAButton", "builtinassets", "textures/ouya_abutton"},
    {"pageLeftRight", "builtinassets", "textures/page_left_right"},
    {"rgbStripes", "builtinassets", "textures/rgb_stripes"},
    {"scorch", "builtinassets", "textures/scorch"},
    {"scorchBig", "builtinassets", "textures/scorch_big"},
    {"scrollWidget", "builtinassets", "textures/scroll_widget"},
    {"scrollWidgetGlow", "builtinassets", "textures/scroll_widget_glow"},
    {"shadow", "builtinassets", "textures/shadow"},
    {"shadowSharp", "builtinassets", "textures/shadow_sharp"},
    {"shadowSoft", "builtinassets", "textures/shadow_soft"},
    {"shield", "builtinassets", "textures/shield"},
    {"shrapnel1Color", "builtinassets", "textures/shrapnel1_color"},
    {"smoke", "builtinassets", "textures/smoke"},
    {"softRect", "builtinassets", "textures/soft_rect"},
    {"softRect2", "builtinassets", "textures/soft_rect2"},
    {"softRectVertical", "builtinassets", "textures/soft_rect_vertical"},
    {"sparks", "builtinassets", "textures/sparks"},
    {"spinner", "builtinassets", "textures/spinner"},
    {"spinner0", "builtinassets", "textures/spinner0"},
    {"spinner1", "builtinassets", "textures/spinner1"},
    {"spinner10", "builtinassets", "textures/spinner10"},
    {"spinner11", "builtinassets", "textures/spinner11"},
    {"spinner2", "builtinassets", "textures/spinner2"},
    {"spinner3", "builtinassets", "textures/spinner3"},
    {"spinner4", "builtinassets", "textures/spinner4"},
    {"spinner5", "builtinassets", "textures/spinner5"},
    {"spinner6", "builtinassets", "textures/spinner6"},
    {"spinner7", "builtinassets", "textures/spinner7"},
    {"spinner8", "builtinassets", "textures/spinner8"},
    {"spinner9", "builtinassets", "textures/spinner9"},
    {"startButton", "builtinassets", "textures/start_button"},
    {"textClearButton", "builtinassets", "textures/text_clear_button"},
    {"touchArrows", "builtinassets", "textures/touch_arrows"},
    {"touchArrowsActions", "builtinassets", "textures/touch_arrows_actions"},
    {"uiAtlas", "builtinassets", "textures/ui_atlas"},
    {"uiAtlas2", "builtinassets", "textures/ui_atlas2"},
    {"usersButton", "builtinassets", "textures/users_button"},
    {"white", "builtinassets", "textures/white"},
    {"windowHSmallVMed", "builtinassets", "textures/window_hsmall_vmed"},
    {"windowHSmallVSmall", "builtinassets", "textures/window_hsmall_vsmall"},
    {"wings", "builtinassets", "textures/wings"},
};

struct State_ {
  // Legacy name -> (package_key, logical_path).
  std::unordered_map<std::string, std::pair<std::string, std::string>>
      from_legacy;
  // 'package_key:logical_path' -> legacy name.
  std::unordered_map<std::string, std::string> to_legacy;
  // package_key -> registered full apverid.
  std::unordered_map<std::string, std::string> package_versions;
  // Versionless apverid prefix ('a-0.babuiltinassets') -> package_key.
  std::unordered_map<std::string, std::string> versionless_to_key;
};

static auto GetState_() -> State_& {
  static State_* state = [] {
    auto* st = new State_();
    for (const Row_& row : kRows) {
      st->from_legacy[row.legacy] = {row.package_key, row.logical_path};
      st->to_legacy[std::string(row.package_key) + ":" + row.logical_path] =
          row.legacy;
    }
    return st;
  }();
  return *state;
}

// Strip the trailing version segment off an apverid
// ('a-0.babuiltinassets.dev260610e' -> 'a-0.babuiltinassets').
static auto VersionlessApverid_(const std::string& apverid) -> std::string {
  size_t pos = apverid.rfind('.');
  return pos == std::string::npos ? apverid : apverid.substr(0, pos);
}

void AssetNameCompat::SetPackageVersion(const std::string& package_key,
                                        const std::string& apverid) {
  assert(g_base->InLogicThread());
  auto& state = GetState_();
  // Drop any versionless mapping from a previous registration.
  auto old = state.package_versions.find(package_key);
  if (old != state.package_versions.end()) {
    state.versionless_to_key.erase(VersionlessApverid_(old->second));
  }
  state.package_versions[package_key] = apverid;
  state.versionless_to_key[VersionlessApverid_(apverid)] = package_key;
}

auto AssetNameCompat::FromLegacy(const std::string& name) -> std::string {
  assert(g_base->InLogicThread());
  if (name.find(':') != std::string::npos) {
    return name;  // Already qualified.
  }
  auto& state = GetState_();
  auto row = state.from_legacy.find(name);
  if (row == state.from_legacy.end()) {
    return name;  // No asset-package home; a true legacy name.
  }
  auto version = state.package_versions.find(row->second.first);
  if (version == state.package_versions.end()) {
    return name;  // Package version not registered (yet).
  }
  std::string mapped = version->second + ":" + row->second.second;
  g_core->logging->Log(
      LogName::kBaAssets, LogLevel::kDebug,
      "AssetNameCompat: from-legacy '" + name + "' -> '" + mapped + "'.");
  return mapped;
}

auto AssetNameCompat::ToLegacy(const std::string& name) -> std::string {
  assert(g_base->InLogicThread());
  size_t colon = name.find(':');
  if (colon == std::string::npos) {
    return name;  // Already a bare name.
  }
  auto& state = GetState_();
  auto key =
      state.versionless_to_key.find(VersionlessApverid_(name.substr(0, colon)));
  if (key == state.versionless_to_key.end()) {
    return name;  // Not a package we know about.
  }
  auto legacy =
      state.to_legacy.find(key->second + ":" + name.substr(colon + 1));
  if (legacy == state.to_legacy.end()) {
    return name;
  }
  g_core->logging->Log(
      LogName::kBaAssets, LogLevel::kDebug,
      "AssetNameCompat: to-legacy '" + name + "' -> '" + legacy->second + "'.");
  return legacy->second;
}

}  // namespace ballistica::base
