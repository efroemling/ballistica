// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_MEDIA_COMPONENT_MODEL_H_
#define BALLISTICA_MEDIA_COMPONENT_MODEL_H_

#include <string>
#include <vector>

#include "ballistica/ballistica.h"
#include "ballistica/core/object.h"
#include "ballistica/media/component/media_component.h"
#include "ballistica/media/data/media_component_data.h"
#include "ballistica/media/data/model_data.h"
#include "ballistica/media/data/model_renderer_data.h"
#include "ballistica/media/media.h"

namespace ballistica {

// user-facing model class
class Model : public MediaComponent {
 public:
  Model(const std::string& name, Scene* scene);
  ~Model() override;

  // return the ModelData currently associated with this model
  // note that a model's data can change over time as different
  // versions are spooled in/out/etc
  auto model_data() const -> ModelData* { return model_data_.get(); }
  auto GetMediaComponentTypeName() const -> std::string override {
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

#endif  // BALLISTICA_MEDIA_COMPONENT_MODEL_H_
