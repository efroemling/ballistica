// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/support/scene_depiction.h"

#include <Python.h>

#include <string>
#include <utility>

#include "ballistica/base/base.h"
#include "ballistica/scene_v1/python/class/python_class_scene_depiction.h"
#include "ballistica/scene_v1/support/scene.h"
#include "ballistica/scene_v1/support/session_stream.h"

namespace ballistica::scene_v1 {

SceneDepiction::SceneDepiction(std::string json, Scene* scene)
    : scene_(scene), json_(std::move(json)) {
  assert(g_base->InLogicThread());

  // If we're being made in a scene with an output stream, write ourself
  // to it.
  assert(scene);
  if (SessionStream* os = scene->GetSceneStream()) {
    os->AddDepiction(this);
  }
}

SceneDepiction::~SceneDepiction() { MarkDead(); }

void SceneDepiction::MarkDead() {
  if (dead_) {
    return;
  }
  // If we're in a scene with an output-stream, inform them of our demise.
  Scene* scene = scene_.get();
  if (scene) {
    if (SessionStream* os = scene->GetSceneStream()) {
      os->RemoveDepiction(this);
    }
  }
  dead_ = true;
}

auto SceneDepiction::NewPyRef() -> PyObject* {
  assert(g_base->InLogicThread());
  // The wrapper that created us may be long gone (nodes keep the native
  // object alive), so hand out a fresh wrapper when asked.
  if (!py_object_) {
    // New ref; sets py_object_.
    return PythonClassSceneDepiction::Create(this);
  }
  Py_INCREF(py_object_);
  return py_object_;
}

}  // namespace ballistica::scene_v1
