// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_PYTHON_CLASS_PYTHON_CLASS_SPAZ_DEF_H_
#define BALLISTICA_SCENE_V1_PYTHON_CLASS_PYTHON_CLASS_SPAZ_DEF_H_

#include "ballistica/scene_v1/scene_v1.h"
#include "ballistica/scene_v1/support/spaz_def.h"
#include "ballistica/shared/python/python_class.h"

namespace ballistica::scene_v1 {

/// Python wrapper for a session-level SpazDef. Opaque: constructed from
/// json and plugged into a spaz node's 'spaz_def' attr; the schema
/// itself is never exposed here beyond the few plain read accessors
/// game logic needs (its default colors).
class PythonClassSpazDef : public PythonClass {
 public:
  static auto type_name() -> const char*;
  static void SetupType(PyTypeObject* cls);
  static auto Check(PyObject* o) -> bool {
    return PyObject_TypeCheck(o, &type_obj);
  }
  static PyTypeObject type_obj;
  /// Wrap an existing SpazDef (one whose original wrapper is gone; e.g.
  /// read back off a node attr). Returns a new reference.
  static auto Create(SpazDef* d) -> PyObject*;
  auto GetSpazDef(bool doraise = true) const -> SpazDef* {
    SpazDef* d = spaz_def_->get();
    if ((!d) && doraise) throw Exception("Invalid SpazDef");
    return d;
  }

 private:
  static bool s_create_empty_;
  static PyMethodDef tp_methods[];
  static PyGetSetDef tp_getsets[];
  static auto tp_new(PyTypeObject* type, PyObject* args, PyObject* keywds)
      -> PyObject*;
  static void Delete(Object::Ref<SpazDef>* d);
  static void tp_dealloc(PythonClassSpazDef* self);
  static auto tp_repr(PythonClassSpazDef* self) -> PyObject*;
  static auto GetColor(PythonClassSpazDef* self, void* closure) -> PyObject*;
  static auto GetHighlight(PythonClassSpazDef* self, void* closure)
      -> PyObject*;
  Object::Ref<SpazDef>* spaz_def_;
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_PYTHON_CLASS_PYTHON_CLASS_SPAZ_DEF_H_
