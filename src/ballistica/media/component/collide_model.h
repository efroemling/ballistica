// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_MEDIA_COMPONENT_COLLIDE_MODEL_H_
#define BALLISTICA_MEDIA_COMPONENT_COLLIDE_MODEL_H_

#include <string>

#include "ballistica/media/component/media_component.h"
#include "ballistica/media/data/collide_model_data.h"
#include "ballistica/media/media.h"

namespace ballistica {

// user-facing collide_model class
class CollideModel : public MediaComponent {
 public:
  CollideModel(const std::string& name, Scene* scene);
  ~CollideModel() override;

  // return the CollideModelData currently associated with this collide_model
  // note that a collide_model's data can change over time as different
  // versions are spooled in/out/etc
  auto collide_model_data() const -> CollideModelData* {
    return collide_model_data_.get();
  }
  auto GetMediaComponentTypeName() const -> std::string override {
    return "CollideModel";
  }
  void MarkDead();

 protected:
  auto CreatePyObject() -> PyObject* override;

 private:
  bool dead_;
  Object::Ref<CollideModelData> collide_model_data_;
};

}  // namespace ballistica

#endif  // BALLISTICA_MEDIA_COMPONENT_COLLIDE_MODEL_H_
