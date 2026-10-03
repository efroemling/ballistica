// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/support/spaz_def.h"

#include <Python.h>

#include <string>
#include <utility>

#include "ballistica/base/base.h"
#include "ballistica/scene_v1/python/class/python_class_spaz_def.h"
#include "ballistica/scene_v1/support/scene.h"
#include "ballistica/scene_v1/support/session_stream.h"

namespace ballistica::scene_v1 {

SpazDef::SpazDef(std::string json, Scene* scene)
    : scene_(scene), def_(std::move(json), base::CharacterDef::Form::kSpaz) {
  assert(g_base->InLogicThread());

  // If we're being made in a scene with an output stream, write ourself
  // to it.
  assert(scene);
  if (SessionStream* os = scene->GetSceneStream()) {
    os->AddSpazDef(this);
  }
}

SpazDef::~SpazDef() { MarkDead(); }

void SpazDef::MarkDead() {
  if (dead_) {
    return;
  }
  // If we're in a scene with an output-stream, inform them of our demise.
  Scene* scene = scene_.get();
  if (scene) {
    if (SessionStream* os = scene->GetSceneStream()) {
      os->RemoveSpazDef(this);
    }
  }
  dead_ = true;
}

auto SpazDef::NewPyRef() -> PyObject* {
  assert(g_base->InLogicThread());
  // The wrapper that created us may be long gone (a spaz actor hands
  // its SpazDef straight to newnode and forgets it); nodes keep the
  // native object alive, so hand out a fresh wrapper when asked.
  if (!py_object_) {
    return PythonClassSpazDef::Create(this);  // New ref; sets py_object_.
  }
  Py_INCREF(py_object_);
  return py_object_;
}

}  // namespace ballistica::scene_v1
