// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_DYNAMICS_MATERIAL_MATERIAL_H_
#define BALLISTICA_SCENE_V1_DYNAMICS_MATERIAL_MATERIAL_H_

#include <string>
#include <vector>

#include "ballistica/scene_v1/scene_v1.h"
#include "ballistica/shared/foundation/object.h"

namespace ballistica::scene_v1 {

/// A material defines actions that occur when a part collides with another part
/// (or separates from it after colliding).  Materials can set up any number of
/// actions to occur dependent on what opposing materials are being hit, what
/// nodes are being hit, etc.
class Material : public Object {
 public:
  Material(std::string name, Scene* scene);
  ~Material() override;

  /// Add a new component to the material.
  /// Pass a component allocated via new.
  void AddComponent(const Object::Ref<MaterialComponent>& c);

  /// Apply the material to a context_ref.
  void Apply(MaterialContext* s, const Part* src_part, const Part* dst_part);
  auto label() const -> const std::string& { return label_; }
  auto NewPyRef() -> PyObject* { return GetPyRef(true); }
  auto BorrowPyRef() -> PyObject* { return GetPyRef(false); }
  void MarkDead();
  auto scene() const -> Scene* { return scene_.Get(); }
  void DumpComponents(SessionStream* out);
  auto stream_id() const -> int64_t { return stream_id_; }
  void set_stream_id(int64_t val) {
    assert(stream_id_ == -1);
    stream_id_ = val;
  }
  void clear_stream_id() {
    assert(stream_id_ != -1);
    stream_id_ = -1;
  }
  void set_py_object(PyObject* obj) { py_object_ = obj; }
  auto has_py_object() const -> bool { return (py_object_ != nullptr); }
  auto py_object() const -> PyObject* { return py_object_; }

 private:
  bool dead_{};
  int64_t stream_id_{-1};
  Object::WeakRef<Scene> scene_;
  PyObject* py_object_{};
  auto GetPyRef(bool new_ref = true) -> PyObject*;
  std::string label_;
  std::vector<Object::Ref<MaterialComponent> > components_;
  friend class ClientSession;
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_DYNAMICS_MATERIAL_MATERIAL_H_
