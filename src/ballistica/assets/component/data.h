// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_ASSETS_COMPONENT_DATA_H_
#define BALLISTICA_ASSETS_COMPONENT_DATA_H_

#include <string>
#include <vector>

#include "ballistica/assets/assets.h"
#include "ballistica/assets/component/asset_component.h"
#include "ballistica/assets/data/asset_component_data.h"
#include "ballistica/assets/data/data_data.h"
#include "ballistica/ballistica.h"
#include "ballistica/core/object.h"

namespace ballistica {

// user-facing data class
class Data : public AssetComponent {
 public:
  Data(const std::string& name, Scene* scene);
  ~Data() override;

  // return the DataData currently associated with this data
  // note that a data's data can change over time as different
  // versions are spooled in/out/etc.
  auto data_data() const -> DataData* { return data_data_.get(); }
  auto GetAssetComponentTypeName() const -> std::string override {
    return "Data";
  }
  void MarkDead();

 protected:
  auto CreatePyObject() -> PyObject* override;

 private:
  bool dead_;
  Object::Ref<DataData> data_data_;
};

}  // namespace ballistica

#endif  // BALLISTICA_ASSETS_COMPONENT_DATA_H_
