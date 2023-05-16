// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_ASSETS_SCENE_SOUND_H_
#define BALLISTICA_SCENE_V1_ASSETS_SCENE_SOUND_H_

#include <string>
#include <vector>

#include "ballistica/base/base.h"
#include "ballistica/scene_v1/assets/scene_asset.h"

namespace ballistica::scene_v1 {

class SceneSound : public SceneAsset {
 public:
  SceneSound(const std::string& name, Scene* scene);
  ~SceneSound() override;

  // Return the SoundData currently associated with this sound.
  // Note that a sound's data can change over time as different
  // versions are spooled in/out/etc.
  auto GetSoundData() const -> base::SoundAsset* { return sound_data_.Get(); }
  auto GetAssetTypeName() const -> std::string override { return "Sound"; }
  void MarkDead();

 protected:
  auto CreatePyObject() -> PyObject* override;

 private:
  Object::Ref<base::SoundAsset> sound_data_;
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_ASSETS_SCENE_SOUND_H_
