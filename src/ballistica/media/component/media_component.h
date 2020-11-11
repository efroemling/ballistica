// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_MEDIA_COMPONENT_MEDIA_COMPONENT_H_
#define BALLISTICA_MEDIA_COMPONENT_MEDIA_COMPONENT_H_

#include <string>

#include "ballistica/core/context.h"
#include "ballistica/core/object.h"

namespace ballistica {

class MediaComponent : public Object {
 public:
  MediaComponent(std::string name, Scene* scene);
  auto name() const -> std::string { return name_; }

  // Returns true if this texture was created in the UI context.
  // UI stuff should check this before accepting a texture.
  auto IsFromUIContext() const -> bool {
    return (context_.GetUIContext() != nullptr);
  }
  auto has_py_object() const -> bool { return (py_object_ != nullptr); }
  auto NewPyRef() -> PyObject* { return GetPyRef(true); }
  auto BorrowPyRef() -> PyObject* { return GetPyRef(false); }
  auto GetObjectDescription() const -> std::string override;
  auto scene() const -> Scene* { return scene_.get(); }

  // Called by python wrapper objs when they are dying.
  void ClearPyObject();

  auto stream_id() const -> int64_t { return stream_id_; }
  void set_stream_id(int64_t val) {
    assert(stream_id_ == -1);
    stream_id_ = val;
  }

  void clear_stream_id() {
    assert(stream_id_ != -1);
    stream_id_ = -1;
  }

 protected:
  virtual auto GetMediaComponentTypeName() const -> std::string = 0;

  // Create a python representation of this object.
  virtual auto CreatePyObject() -> PyObject* = 0;

 private:
  int64_t stream_id_{-1};
  Object::WeakRef<Scene> scene_;
  PyObject* py_object_{};

  // Return a python reference to the object, (creating python obj if needed).
  auto GetPyRef(bool new_ref = true) -> PyObject*;
  std::string name_;
  Context context_;
  friend class ClientSession;
};

}  // namespace ballistica

#endif  // BALLISTICA_MEDIA_COMPONENT_MEDIA_COMPONENT_H_
