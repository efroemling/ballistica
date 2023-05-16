// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_ASSETS_DATA_ASSET_H_
#define BALLISTICA_BASE_ASSETS_DATA_ASSET_H_

#include <string>

#include "ballistica/base/assets/asset.h"
#include "ballistica/shared/python/python_ref.h"

namespace ballistica::base {

class DataAsset : public Asset {
 public:
  DataAsset() = default;
  explicit DataAsset(const std::string& file_name_in);

  void DoPreload() override;
  void DoLoad() override;
  void DoUnload() override;
  auto GetAssetType() const -> AssetType override;
  auto GetName() const -> std::string override;

  auto object() -> const PythonRef& {
    assert(g_base->InLogicThread());
    assert(loaded());
    return object_;
  }
  auto file_name() const -> const std::string& { return file_name_; }
  auto file_name_full() const -> const std::string& { return file_name_full_; }

 private:
  PythonRef object_;
  std::string file_name_;
  std::string file_name_full_;
  std::string raw_input_;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_ASSETS_DATA_ASSET_H_
