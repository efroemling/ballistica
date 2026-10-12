// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/python/class/python_class_scene_depiction.h"

#include <string>

#include "ballistica/base/logic/logic.h"
#include "ballistica/scene_v1/support/host_activity.h"
#include "ballistica/scene_v1/support/host_session.h"
#include "ballistica/shared/foundation/event_loop.h"
#include "ballistica/shared/generic/utils.h"
#include "ballistica/shared/python/python.h"

namespace ballistica::scene_v1 {

PyTypeObject PythonClassSceneDepiction::type_obj;
bool PythonClassSceneDepiction::s_create_empty_ = false;

auto PythonClassSceneDepiction::type_name() -> const char* {
  return "Depiction";
}

auto PythonClassSceneDepiction::Create(SceneDepiction* d) -> PyObject* {
  assert(d != nullptr);
  // Make sure we only have one python ref per depiction.
  assert(!d->has_py_object());

  s_create_empty_ = true;  // Prevent class from erroring on create.
  assert(TypeIsSetUp(&type_obj));
  auto* py_dep = reinterpret_cast<PythonClassSceneDepiction*>(
      PyObject_CallObject(reinterpret_cast<PyObject*>(&type_obj), nullptr));
  s_create_empty_ = false;
  if (!py_dep) {
    throw Exception("bascenev1.Depiction creation failed.");
  }
  *py_dep->depiction_ = d;
  d->set_py_object(reinterpret_cast<PyObject*>(py_dep));
  return reinterpret_cast<PyObject*>(py_dep);
}

void PythonClassSceneDepiction::SetupType(PyTypeObject* cls) {
  PythonClass::SetupType(cls);
  // Fully qualified type path we will be exposed as:
  cls->tp_name = "bascenev1.Depiction";
  cls->tp_repr = (reprfunc)tp_repr;
  cls->tp_basicsize = sizeof(PythonClassSceneDepiction);

  // clang-format off
  cls->tp_doc =
      "Depiction(json: str)\n"
      "\n"
      "A depiction registered in a scene, for nodes to show.\n"
      "\n"
      "Built from a json-serialized :class:`bacommon.depiction.Depiction`\n"
      "(a name, a character's icon, ...) and assigned to node attrs of\n"
      "the depiction type (a ``depictiondisplay`` node's ``depiction``,\n"
      "say). It crosses the stream once however many nodes show it;\n"
      "every machine draws it natively, as a placeholder if it can't.\n"
      "\n"
      "Lifetime works like :class:`Material`: the depiction lives as\n"
      "long as something references it (this object or a node attr)\n"
      "and leaves the session automatically once nothing does.\n"
      "\n"
      "Must be created in a host activity or host session context, and\n"
      "can only be assigned to nodes of that same scene (scene objects\n"
      "never cross scenes; the session's lobby has its own). To show\n"
      "the same thing in another activity, build another from the same\n"
      "json there.\n";
  // clang-format on

  cls->tp_methods = tp_methods;
  cls->tp_new = tp_new;
  cls->tp_dealloc = (destructor)tp_dealloc;
}

auto PythonClassSceneDepiction::tp_new(PyTypeObject* type, PyObject* args,
                                       PyObject* keywds) -> PyObject* {
  auto* self =
      reinterpret_cast<PythonClassSceneDepiction*>(type->tp_alloc(type, 0));
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
  Object::Ref<SceneDepiction> d;
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
    auto* context =
        ContextRefSceneV1::FromCurrent().GetContextTyped<SceneV1Context>();
    if (context == nullptr) {
      throw Exception("Can't create depictions in this context_ref.",
                      PyExcType::kContext);
    }
    d = context->NewDepiction(json);
    d->set_py_object(reinterpret_cast<PyObject*>(self));
  }
  self->depiction_ = new Object::Ref<SceneDepiction>(d);
  return reinterpret_cast<PyObject*>(self);
  BA_PYTHON_NEW_CATCH;
}

void PythonClassSceneDepiction::Delete(Object::Ref<SceneDepiction>* d) {
  assert(g_base->InLogicThread());

  // If we're the py-object for a depiction, clear them out.
  if (d->exists()) {
    assert((*d)->py_object() != nullptr);
    (*d)->set_py_object(nullptr);
  }
  delete d;
}

void PythonClassSceneDepiction::tp_dealloc(PythonClassSceneDepiction* self) {
  BA_PYTHON_TRY;

  // These have to be deleted in the logic thread - push a call if
  // need be.. otherwise do it immediately.
  if (!g_base->InLogicThread()) {
    Object::Ref<SceneDepiction>* ptr = self->depiction_;
    g_base->logic->event_loop()->PushCall([ptr] { Delete(ptr); });
  } else {
    Delete(self->depiction_);
  }
  BA_PYTHON_DEALLOC_CATCH;
  Py_TYPE(self)->tp_free(reinterpret_cast<PyObject*>(self));
}

auto PythonClassSceneDepiction::tp_repr(PythonClassSceneDepiction* self)
    -> PyObject* {
  BA_PYTHON_TRY;
  return Py_BuildValue("s", std::string("<bascenev1.Depiction at "
                                        + Utils::PtrToString(self) + ">")
                                .c_str());
  BA_PYTHON_CATCH;
}

PyMethodDef PythonClassSceneDepiction::tp_methods[] = {
    {nullptr}  // Sentinel
};

}  // namespace ballistica::scene_v1
