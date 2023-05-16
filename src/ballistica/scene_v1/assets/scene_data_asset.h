// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_ASSETS_SCENE_DATA_ASSET_H_
#define BALLISTICA_SCENE_V1_ASSETS_SCENE_DATA_ASSET_H_

#include <string>
#include <vector>

#include "ballistica/base/assets/asset.h"
#include "ballistica/base/assets/assets.h"
#include "ballistica/base/assets/data_asset.h"
#include "ballistica/scene_v1/assets/scene_asset.h"
#include "ballistica/shared/ballistica.h"
#include "ballistica/shared/foundation/object.h"

namespace ballistica::scene_v1 {

// user-facing data class
class SceneDataAsset : public SceneAsset {
 public:
  SceneDataAsset(const std::string& name, Scene* scene);
  ~SceneDataAsset() override;

  // return the DataData currently associated with this data
  // note that a data's data can change over time as different
  // versions are spooled in/out/etc.
  auto data_data() const -> base::DataAsset* { return data_data_.Get(); }
  auto GetAssetTypeName() const -> std::string override { return "Data"; }
  void MarkDead();

 protected:
  auto CreatePyObject() -> PyObject* override;

 private:
  Object::Ref<base::DataAsset> data_data_;
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_ASSETS_SCENE_DATA_ASSET_H_
