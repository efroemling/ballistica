// Released under the MIT License. See LICENSE for details.

#include "ballistica/dynamics/material/material.h"

// #include "ballistica/dynamics/material/material_action.h"
#include "ballistica/dynamics/material/material_component.h"
#include "ballistica/dynamics/material/material_condition_node.h"
#include "ballistica/game/game_stream.h"
#include "ballistica/python/python_sys.h"
#include "ballistica/scene/scene.h"

namespace ballistica {

Material::Material(std::string name_in, Scene* scene)
    : label_(std::move(name_in)), scene_(scene) {
  // If we're being made in a scene with an output stream,
  // write ourself to it.
  assert(scene);
  if (GameStream* os = scene->GetGameStream()) {
    os->AddMaterial(this);
  }
}

void Material::MarkDead() {
  if (dead_) {
    return;
  }
  components_.clear();

  // If we're in a scene with an output-stream, inform them of our demise.
  Scene* scene = scene_.get();
  if (scene) {
    if (GameStream* os = scene->GetGameStream()) {
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
  if (GameStream* output_stream = scene()->GetGameStream()) {
    output_stream->AddMaterialComponent(this, c.get());
  }
  components_.push_back(c);
}

void Material::DumpComponents(GameStream* out) {
  for (auto& i : components_) {
    assert(i.exists());
    out->AddMaterialComponent(this, i.get());
  }
}

}  // namespace ballistica
