// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_MEDIA_COMPONENT_DATA_H_
#define BALLISTICA_MEDIA_COMPONENT_DATA_H_

#include <string>
#include <vector>

#include "ballistica/ballistica.h"
#include "ballistica/core/object.h"
#include "ballistica/media/component/media_component.h"
#include "ballistica/media/data/data_data.h"
#include "ballistica/media/data/media_component_data.h"
#include "ballistica/media/media.h"

namespace ballistica {

// user-facing data class
class Data : public MediaComponent {
 public:
  Data(const std::string& name, Scene* scene);
  ~Data() override;

  // return the DataData currently associated with this data
  // note that a data's data can change over time as different
  // versions are spooled in/out/etc.
  auto data_data() const -> DataData* { return data_data_.get(); }
  auto GetMediaComponentTypeName() const -> std::string override {
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

#endif  // BALLISTICA_MEDIA_COMPONENT_DATA_H_
