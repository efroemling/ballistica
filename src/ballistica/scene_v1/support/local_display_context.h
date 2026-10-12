// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_SUPPORT_LOCAL_DISPLAY_CONTEXT_H_
#define BALLISTICA_SCENE_V1_SUPPORT_LOCAL_DISPLAY_CONTEXT_H_

#include <string>

#include "ballistica/scene_v1/support/local_scene_context.h"
#include "ballistica/shared/python/python_ref.h"

namespace ballistica::scene_v1 {

/// A self-contained scene context owned by a LocalDisplayNode.
///
/// Both hosts and clients run one of these for each localdisplay node,
/// which is what lets a single streamed node result in every machine
/// drawing its own local version of something (its own controller
/// button names, for instance). The owning node steps us from its own
/// Step() (so we advance in lockstep with its scene) and draws us from
/// its Draw(). See LocalSceneContext for what we consist of.
class LocalDisplayContext : public LocalSceneContext {
 public:
  explicit LocalDisplayContext(Scene* parent_scene);
  ~LocalDisplayContext() override;

  auto GetContextDescription() -> std::string override;

  /// Store a weak-ref to the Python LocalDisplay object wrapping us.
  void RegisterPyLocalDisplay(PyObject* obj);

  /// Return a NEW ref to the Python LocalDisplay or nullptr if
  /// nonexistent.
  auto GetPyLocalDisplay() const -> PyObject*;

 private:
  PythonRef py_local_display_weak_ref_;
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_SUPPORT_LOCAL_DISPLAY_CONTEXT_H_
