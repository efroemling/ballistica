// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_MEDIA_COMPONENT_SOUND_H_
#define BALLISTICA_MEDIA_COMPONENT_SOUND_H_

#include <string>
#include <vector>

#include "ballistica/media/component/media_component.h"

namespace ballistica {

class Sound : public MediaComponent {
 public:
  Sound(const std::string& name, Scene* scene);
  ~Sound() override;

  // Return the SoundData currently associated with this sound.
  // Note that a sound's data can change over time as different
  // versions are spooled in/out/etc.
  auto GetSoundData() const -> SoundData* { return sound_data_.get(); }
  auto GetMediaComponentTypeName() const -> std::string override {
    return "Sound";
  }
  void MarkDead();

 protected:
  auto CreatePyObject() -> PyObject* override;

 private:
  bool dead_{};
  Object::Ref<SoundData> sound_data_;
};

}  // namespace ballistica

#endif  // BALLISTICA_MEDIA_COMPONENT_SOUND_H_
