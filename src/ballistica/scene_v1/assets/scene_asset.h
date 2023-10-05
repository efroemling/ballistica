// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_ASSETS_SCENE_ASSET_H_
#define BALLISTICA_SCENE_V1_ASSETS_SCENE_ASSET_H_

#include <list>
#include <string>
#include <unordered_map>

#include "ballistica/scene_v1/support/scene_v1_context.h"
#include "ballistica/shared/foundation/object.h"

namespace ballistica::scene_v1 {

/// Handy function to try to return an asset from a std::unordered_map
/// of weak-refs, loading/adding it if need be.
template <typename T>
static auto GetAsset(std::unordered_map<std::string, Object::WeakRef<T> >* list,
                     const std::string& name, Scene* scene) -> Object::Ref<T> {
  assert(g_base->InLogicThread());
  assert(list);
  auto i = list->find(name);

  // If we have an entry pointing to a live component, just return a new ref
  // to it.
  if (i != list->end() && i->second.Exists()) {
    return Object::Ref<T>(i->second.Get());
  } else {
    // Otherwise make a new one, pop a weak-ref on our list, and return a
    // strong-ref to it.
    auto t(Object::New<T>(name, scene));
    (*list)[name] = t;
    return Object::Ref<T>(t);
  }
}

/// A usage of an asset in a scene context_ref.
class SceneAsset : public Object {
 public:
  SceneAsset(std::string name, Scene* scene);
  auto name() const -> std::string { return name_; }

  auto has_py_object() const -> bool { return (py_object_ != nullptr); }
  auto NewPyRef() -> PyObject* { return GetPyRef(true); }
  auto BorrowPyRef() -> PyObject* { return GetPyRef(false); }
  auto GetObjectDescription() const -> std::string override;
  auto scene() const -> Scene* { return scene_.Get(); }

  auto stream_id() const -> int64_t { return stream_id_; }
  void set_stream_id(int64_t val) {
    assert(stream_id_ == -1);
    stream_id_ = val;
  }

  void clear_stream_id() {
    assert(stream_id_ != -1);
    stream_id_ = -1;
  }

  auto dead() const { return dead_; }
  auto set_dead(bool val) { dead_ = val; }

 protected:
  void ReleasePyObj();
  virtual auto GetAssetTypeName() const -> std::string = 0;

  // Create a python representation of this object.
  virtual auto CreatePyObject() -> PyObject* = 0;

 private:
  int64_t stream_id_{-1};
  Object::WeakRef<Scene> scene_;
  PyObject* py_object_{};

  // Return a Python reference to the object, (creating Python obj if needed).
  auto GetPyRef(bool new_ref = true) -> PyObject*;
  std::string name_;
  ContextRefSceneV1 context_;
  bool dead_{false};
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_ASSETS_SCENE_ASSET_H_
