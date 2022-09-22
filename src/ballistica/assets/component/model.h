// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_ASSETS_COMPONENT_MODEL_H_
#define BALLISTICA_ASSETS_COMPONENT_MODEL_H_

#include <string>
#include <vector>

#include "ballistica/assets/assets.h"
#include "ballistica/assets/component/asset_component.h"
#include "ballistica/assets/data/asset_component_data.h"
#include "ballistica/assets/data/model_data.h"
#include "ballistica/assets/data/model_renderer_data.h"
#include "ballistica/ballistica.h"
#include "ballistica/core/object.h"

namespace ballistica {

// user-facing model class
class Model : public AssetComponent {
 public:
  Model(const std::string& name, Scene* scene);
  ~Model() override;

  // return the ModelData currently associated with this model
  // note that a model's data can change over time as different
  // versions are spooled in/out/etc
  auto model_data() const -> ModelData* { return model_data_.get(); }
  auto GetAssetComponentTypeName() const -> std::string override {
    return "Model";
  }
  void MarkDead();

 protected:
  auto CreatePyObject() -> PyObject* override;

 private:
  bool dead_;
  Object::Ref<ModelData> model_data_;
};

}  // namespace ballistica

#endif  // BALLISTICA_ASSETS_COMPONENT_MODEL_H_
