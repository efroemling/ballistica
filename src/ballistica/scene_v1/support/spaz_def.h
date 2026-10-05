// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_SUPPORT_SPAZ_DEF_H_
#define BALLISTICA_SCENE_V1_SUPPORT_SPAZ_DEF_H_

#include <string>

#include "ballistica/base/support/character_def.h"
#include "ballistica/scene_v1/scene_v1.h"
#include "ballistica/shared/foundation/object.h"

namespace ballistica::scene_v1 {

/// A session-level spaz definition (how a spaz looks, sounds and is
/// proportioned), referenced by spaz nodes via their typed 'spaz_def'
/// attr. Its name and icon live elsewhere (depictions): a character is
/// only a delivery bundle, never something the scene holds.
///
/// This is the scene/stream wrapper around a base::CharacterDef holding
/// just a spaz form (which owns parsing, media resolution and the
/// standin rules). Lifecycle mirrors Material exactly: plain
/// refcounted, the Python wrapper holds one ref and every node attr
/// referencing it holds another; construction writes kAddSpazDef to
/// the scene's session stream and the destructor writes kRemoveSpazDef
/// (recycling the stream id), so a definition leaves the stream -- and
/// never reaches a late joiner's baseline -- the moment its last
/// reference is gone. Immutable after construction. Scoping: one built
/// in the host session's own scene may be referenced by nodes in any
/// scene of that session (see SessionStream::SetNodeAttr); one built in
/// an activity scene only by that scene's nodes.
/// Design: docs/initiatives/character-skins.md.
class SpazDef : public Object {
 public:
  /// ``json`` is a spaz block on its own (a character's 's').
  SpazDef(std::string json, Scene* scene);
  ~SpazDef() override;

  /// The parsed definition (spaz form, media, standin state).
  auto def() const -> const base::CharacterDef& { return def_; }
  /// Re-attempt media loads for components still on the standin (see
  /// base::CharacterDef::RetryMedia). True if any became ready.
  auto RetryMedia() -> bool { return def_.RetryMedia(); }
  /// The raw json this was built from (what travels the stream).
  auto json() const -> const std::string& { return def_.json(); }
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
  base::CharacterDef def_;

  friend class ClientSession;
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_SUPPORT_SPAZ_DEF_H_
