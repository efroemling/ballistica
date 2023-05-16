// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/dynamics/material/material.h"

#include "ballistica/scene_v1/dynamics/material/material_component.h"
#include "ballistica/scene_v1/support/scene.h"
#include "ballistica/scene_v1/support/session_stream.h"
#include "ballistica/shared/python/python_sys.h"

namespace ballistica::scene_v1 {

Material::Material(std::string name_in, Scene* scene)
    : label_(std::move(name_in)), scene_(scene) {
  // If we're being made in a scene with an output stream,
  // write ourself to it.
  assert(scene);
  if (SessionStream* os = scene->GetSceneStream()) {
    os->AddMaterial(this);
  }
}

void Material::MarkDead() {
  if (dead_) {
    return;
  }
  components_.clear();

  // If we're in a scene with an output-stream, inform them of our demise.
  Scene* scene = scene_.Get();
  if (scene) {
    if (SessionStream* os = scene->GetSceneStream()) {
      os->RemoveMaterial(this);
    }
  }
  dead_ = true;
}

auto Material::GetPyRef(bool new_ref) -> PyObject* {
  if (!py_object_) {
    throw Exception("This material is not associated with a python object");
  }
  if (new_ref) {
    Py_INCREF(py_object_);
  }
  return py_object_;
}

Material::~Material() { MarkDead(); }

void Material::Apply(MaterialContext* s, const Part* src_part,
                     const Part* dst_part) {
  // Apply all applicable components to the context.
  for (auto& component : components_) {
    if (component->eval_conditions(component->conditions, *this, src_part,
                                   dst_part, *s)) {
      component->Apply(s, src_part, dst_part);
    }
  }
}

void Material::AddComponent(const Object::Ref<MaterialComponent>& c) {
  // If there's an output stream, push this to that first
  if (SessionStream* output_stream = scene()->GetSceneStream()) {
    output_stream->AddMaterialComponent(this, c.Get());
  }
  components_.push_back(c);
}

void Material::DumpComponents(SessionStream* out) {
  for (auto& i : components_) {
    assert(i.Exists());
    out->AddMaterialComponent(this, i.Get());
  }
}

}  // namespace ballistica::scene_v1
