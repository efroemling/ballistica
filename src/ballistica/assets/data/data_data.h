// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_ASSETS_DATA_DATA_DATA_H_
#define BALLISTICA_ASSETS_DATA_DATA_DATA_H_

#include <string>

#include "ballistica/assets/data/asset_component_data.h"
#include "ballistica/python/python_ref.h"

namespace ballistica {

class DataData : public AssetComponentData {
 public:
  DataData() = default;
  explicit DataData(const std::string& file_name_in);

  void DoPreload() override;
  void DoLoad() override;
  void DoUnload() override;

  auto GetAssetType() const -> AssetType override { return AssetType::kData; }
  auto GetName() const -> std::string override {
    if (!file_name_full_.empty()) {
      return file_name_full_;
    } else {
      return "invalid data";
    }
  }
  auto object() -> const PythonRef& {
    assert(InLogicThread());
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

}  // namespace ballistica

#endif  // BALLISTICA_ASSETS_DATA_DATA_DATA_H_
