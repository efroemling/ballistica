// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/python/class/python_class_spaz_def.h"

#include <string>

#include "ballistica/base/logic/logic.h"
#include "ballistica/scene_v1/support/host_activity.h"
#include "ballistica/scene_v1/support/host_session.h"
#include "ballistica/shared/foundation/event_loop.h"
#include "ballistica/shared/generic/utils.h"
#include "ballistica/shared/python/python.h"

namespace ballistica::scene_v1 {

PyTypeObject PythonClassSpazDef::type_obj;
bool PythonClassSpazDef::s_create_empty_ = false;

auto PythonClassSpazDef::type_name() -> const char* { return "SpazDef"; }

auto PythonClassSpazDef::Create(SpazDef* d) -> PyObject* {
  assert(d != nullptr);
  // Make sure we only have one python ref per definition.
  assert(!d->has_py_object());

  s_create_empty_ = true;  // Prevent class from erroring on create.
  assert(TypeIsSetUp(&type_obj));
  auto* py_def = reinterpret_cast<PythonClassSpazDef*>(
      PyObject_CallObject(reinterpret_cast<PyObject*>(&type_obj), nullptr));
  s_create_empty_ = false;
  if (!py_def) {
    throw Exception("bascenev1.SpazDef creation failed.");
  }
  *py_def->spaz_def_ = d;
  d->set_py_object(reinterpret_cast<PyObject*>(py_def));
  return reinterpret_cast<PyObject*>(py_def);
}

void PythonClassSpazDef::SetupType(PyTypeObject* cls) {
  PythonClass::SetupType(cls);
  // Fully qualified type path we will be exposed as:
  cls->tp_name = "bascenev1.SpazDef";
  cls->tp_repr = (reprfunc)tp_repr;
  cls->tp_basicsize = sizeof(PythonClassSpazDef);

  // clang-format off
  cls->tp_doc =
      "SpazDef(json: str)\n"
      "\n"
      "A spaz definition: how a spaz node looks, sounds, and is\n"
      "proportioned.\n"
      "\n"
      "Built from a json spaz definition (a character's spaz part, as\n"
      "delivered by the master server for a player's verified profile\n"
      "or bundled for the builtin characters; see\n"
      ":func:`bascenev1.split_character`) and assigned to a spaz node's\n"
      "``spaz_def`` attr. The definition is opaque here; the node draws,\n"
      "voices, and proportions itself from it, wearing a standard-spaz\n"
      "standin until any media it references is available locally.\n"
      "\n"
      "Lifetime works like :class:`Material`: the definition lives as\n"
      "long as something references it (this object or a node attr)\n"
      "and leaves the session automatically once nothing does.\n"
      "\n"
      "Must be created in a host activity or host session context. One\n"
      "created in a session context (as the lobby does for a player's\n"
      "cloud profile) can be assigned to nodes in any of that session's\n"
      "activities; one created in an activity context only to nodes of\n"
      "that activity.\n";
  // clang-format on

  cls->tp_methods = tp_methods;
  cls->tp_getset = tp_getsets;
  cls->tp_new = tp_new;
  cls->tp_dealloc = (destructor)tp_dealloc;
}

auto PythonClassSpazDef::tp_new(PyTypeObject* type, PyObject* args,
                                PyObject* keywds) -> PyObject* {
  auto* self = reinterpret_cast<PythonClassSpazDef*>(type->tp_alloc(type, 0));
  if (!self) {
    return nullptr;
  }
  BA_PYTHON_TRY;

  // Do anything that might throw an exception *before* our placement-new
  // stuff so we don't have to worry about cleaning it up on errors.
  if (!g_base->InLogicThread()) {
    throw Exception(
        "ERROR: " + std::string(type_obj.tp_name)
        + " objects must only be created in the logic thread (current is ("
        + g_core->CurrentThreadName() + ").");
  }
  Object::Ref<SpazDef> d;
  if (!s_create_empty_) {
    const char* json;
    static const char* kwlist[] = {"json", nullptr};
    if (!PyArg_ParseTupleAndKeywords(args, keywds, "s",
                                     const_cast<char**>(kwlist), &json)) {
      // ew; can't throw an exception here because we want to keep the
      // python one that was just set. Just manually do a free I guess.
      type->tp_free(self);
      return nullptr;
    }
    // Definitions live in the scene of whichever context we're made
    // in: an activity's, the session's own (where the lobby's choosers
    // build them before any activity has the player), or a scene
    // viewer's. It is up to the context whether it has a place for
    // them.
    auto* context =
        ContextRefSceneV1::FromCurrent().GetContextTyped<SceneV1Context>();
    if (context == nullptr) {
      throw Exception("Can't create spaz definitions in this context_ref.",
                      PyExcType::kContext);
    }
    d = context->NewSpazDef(json);
    d->set_py_object(reinterpret_cast<PyObject*>(self));
  }
  self->spaz_def_ = new Object::Ref<SpazDef>(d);
  return reinterpret_cast<PyObject*>(self);
  BA_PYTHON_NEW_CATCH;
}

void PythonClassSpazDef::Delete(Object::Ref<SpazDef>* d) {
  assert(g_base->InLogicThread());

  // If we're the py-object for a definition, clear them out.
  if (d->exists()) {
    assert((*d)->py_object() != nullptr);
    (*d)->set_py_object(nullptr);
  }
  delete d;
}

void PythonClassSpazDef::tp_dealloc(PythonClassSpazDef* self) {
  BA_PYTHON_TRY;

  // These have to be deleted in the logic thread - push a call if
  // need be.. otherwise do it immediately.
  if (!g_base->InLogicThread()) {
    Object::Ref<SpazDef>* ptr = self->spaz_def_;
    g_base->logic->event_loop()->PushCall([ptr] { Delete(ptr); });
  } else {
    Delete(self->spaz_def_);
  }
  BA_PYTHON_DEALLOC_CATCH;
  Py_TYPE(self)->tp_free(reinterpret_cast<PyObject*>(self));
}

auto PythonClassSpazDef::tp_repr(PythonClassSpazDef* self) -> PyObject* {
  BA_PYTHON_TRY;
  return Py_BuildValue("s", std::string("<bascenev1.SpazDef at "
                                        + Utils::PtrToString(self) + ">")
                                .c_str());
  BA_PYTHON_CATCH;
}

PyMethodDef PythonClassSpazDef::tp_methods[] = {
    {nullptr}  // Sentinel
};

auto PythonClassSpazDef::GetColor(PythonClassSpazDef* self, void* closure)
    -> PyObject* {
  BA_PYTHON_TRY;
  const base::CharacterDef& def = self->GetSpazDef()->def();
  if (!def.has_spaz() || !def.spaz().has_color) {
    Py_RETURN_NONE;
  }
  const float* c = def.spaz().color;
  return Py_BuildValue("(fff)", c[0], c[1], c[2]);
  BA_PYTHON_CATCH;
}

auto PythonClassSpazDef::GetHighlight(PythonClassSpazDef* self, void* closure)
    -> PyObject* {
  BA_PYTHON_TRY;
  const base::CharacterDef& def = self->GetSpazDef()->def();
  if (!def.has_spaz() || !def.spaz().has_color) {
    Py_RETURN_NONE;
  }
  const float* c = def.spaz().highlight;
  return Py_BuildValue("(fff)", c[0], c[1], c[2]);
  BA_PYTHON_CATCH;
}

PyGetSetDef PythonClassSpazDef::tp_getsets[] = {
    {const_cast<char*>("color"), (getter)GetColor, nullptr,
     const_cast<char*>(
         "color: tuple[float, float, float] | None\n"
         "\n"
         "The definition's own primary color, or None if it carries none\n"
         "(the node then takes its color attr). What a lobby offers as\n"
         "the player's color when they pick this look; game modes may\n"
         "still override per player."),
     nullptr},
    {const_cast<char*>("highlight"), (getter)GetHighlight, nullptr,
     const_cast<char*>(
         "highlight: tuple[float, float, float] | None\n"
         "\n"
         "The definition's own highlight color, or None if it carries\n"
         "none."),
     nullptr},
    {nullptr}  // Sentinel
};

}  // namespace ballistica::scene_v1
