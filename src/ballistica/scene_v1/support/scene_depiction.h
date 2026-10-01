// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_SUPPORT_SCENE_DEPICTION_H_
#define BALLISTICA_SCENE_V1_SUPPORT_SCENE_DEPICTION_H_

#include <string>

#include "ballistica/scene_v1/scene_v1.h"
#include "ballistica/shared/foundation/object.h"

namespace ballistica::scene_v1 {

/// A session-level depiction (bacommon.depiction json: a name, an
/// icon, ...) registered once in a scene and referenced by id from node
/// attrs of type NodeAttributeType::kDepiction -- so a player's name or
/// icon shown in several places (a label, a scoreboard row) crosses the
/// stream once.
///
/// We hold only the json: every node showing us makes its own
/// base::Depiction from it (instances hold per-host media and
/// lifecycle state), so a kind a machine can't draw is its placeholder
/// there. Lifecycle and scoping exactly as SpazDef: refcounted by the
/// Python wrapper and referencing node attrs; construction writes
/// kAddDepiction and the destructor kRemoveDepiction (recycling the
/// stream id); one built in the host session's own scene works for
/// nodes in any of that session's scenes. Immutable after construction.
/// Design: docs/initiatives/depictions.md.
class SceneDepiction : public Object {
 public:
  SceneDepiction(std::string json, Scene* scene);
  ~SceneDepiction() override;

  /// The depiction's json (what travels the stream).
  auto json() const -> const std::string& { return json_; }
  auto scene() const -> Scene* { return scene_.get(); }

  /// A new reference to our Python wrapper, creating one if the
  /// original is gone (nodes keep us alive independently of it).
  auto NewPyRef() -> PyObject*;
  void MarkDead();

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
  std::string json_;

  friend class ClientSession;
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_SUPPORT_SCENE_DEPICTION_H_
