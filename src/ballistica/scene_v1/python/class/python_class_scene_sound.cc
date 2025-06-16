// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/python/class/python_class_scene_sound.h"

#include <string>
#include <vector>

#include "ballistica/base/logic/logic.h"
#include "ballistica/scene_v1/assets/scene_sound.h"
#include "ballistica/scene_v1/support/scene.h"
#include "ballistica/shared/foundation/event_loop.h"
#include "ballistica/shared/python/python.h"

namespace ballistica::scene_v1 {

auto PythonClassSceneSound::type_name() -> const char* { return "Sound"; }

void PythonClassSceneSound::SetupType(PyTypeObject* cls) {
  PythonClass::SetupType(cls);
  // Fully qualified type path we will be exposed as:
  cls->tp_name = "bascenev1.Sound";
  cls->tp_basicsize = sizeof(PythonClassSceneSound);
  cls->tp_doc =
      "A reference to a sound.\n"
      "\n"
      "Use :meth:`bascenev1.getsound()` to instantiate one.";
  cls->tp_methods = tp_methods;
  cls->tp_repr = (reprfunc)tp_repr;
  cls->tp_new = tp_new;
  cls->tp_dealloc = (destructor)tp_dealloc;
}

auto PythonClassSceneSound::tp_repr(PythonClassSceneSound* self) -> PyObject* {
  BA_PYTHON_TRY;
  auto&& m = *(self->sound_);
  return Py_BuildValue(
      "s", (std::string("<bascenev1.Sound ")
            + (m.exists() ? ("\"" + m->name() + "\"") : "(empty ref)") + ">")
               .c_str());
  BA_PYTHON_CATCH;
}

auto PythonClassSceneSound::Create(SceneSound* sound) -> PyObject* {
  s_create_empty_ = true;  // prevent class from erroring on create
  assert(TypeIsSetUp(&type_obj));
  auto* t = reinterpret_cast<PythonClassSceneSound*>(
      PyObject_CallObject(reinterpret_cast<PyObject*>(&type_obj), nullptr));
  s_create_empty_ = false;
  if (!t) {
    throw Exception("bascenev1.Sound creation failed.");
  }
  *t->sound_ = sound;
  return reinterpret_cast<PyObject*>(t);
}

auto PythonClassSceneSound::GetSound(bool doraise) const -> SceneSound* {
  SceneSound* sound = sound_->get();
  if (!sound && doraise) {
    throw Exception("Invalid Sound.", PyExcType::kNotFound);
  }
  return sound;
}

// Clion makes some incorrect inferences here.
#pragma clang diagnostic push
#pragma ide diagnostic ignored "UnreachableCode"
#pragma ide diagnostic ignored "ConstantConditionsOC"
#pragma ide diagnostic ignored "ConstantFunctionResult"

auto PythonClassSceneSound::tp_new(PyTypeObject* type, PyObject* args,
                                   PyObject* kwds) -> PyObject* {
  auto* self =
      reinterpret_cast<PythonClassSceneSound*>(type->tp_alloc(type, 0));
  if (!self) {
    return nullptr;
  }
  BA_PYTHON_TRY;
  if (!g_base->InLogicThread()) {
    throw Exception(
        "ERROR: " + std::string(type_obj.tp_name)
        + " objects must only be created in the logic thread (current is ("
        + g_core->CurrentThreadName() + ").");
  }
  if (!s_create_empty_) {
    throw Exception(
        "Can't instantiate Sounds directly; use bascenev1.getsound() to get "
        "them.");
  }
  self->sound_ = new Object::Ref<SceneSound>();
  return reinterpret_cast<PyObject*>(self);
  BA_PYTHON_NEW_CATCH;
}

#pragma clang diagnostic pop

auto PythonClassSceneSound::Play(PythonClassSceneSound* self, PyObject* args,
                                 PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  BA_PRECONDITION(g_base->InLogicThread());
  float volume = 1.0f;
  int host_only = 0;
  PyObject* pos_obj = Py_None;
  static const char* kwlist[] = {"volume", "position", "host_only", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "|fOp",
                                   const_cast<char**>(kwlist), &volume,
                                   &pos_obj, &host_only)) {
    return nullptr;
  }
  auto* sound = self->GetSound();

  // Can play sounds in a host scene context.
  if (Scene* scene = ContextRefSceneV1::FromCurrent().GetMutableScene()) {
    if (sound->scene() != scene) {
      throw Exception("Sound was not loaded in this context_ref.",
                      PyExcType::kContext);
    }
    if (pos_obj != Py_None) {
      std::vector<float> vals = Python::GetFloats(pos_obj);
      if (vals.size() != 3) {
        throw Exception("Expected 3 floats for pos (got "
                            + std::to_string(vals.size()) + ")",
                        PyExcType::kValue);
      }
      scene->PlaySoundAtPosition(sound, volume, vals[0], vals[1], vals[2],
                                 static_cast<bool>(host_only));
    } else {
      scene->PlaySound(sound, volume, static_cast<bool>(host_only));
    }
  } else {
    throw Exception("Can't play sounds in this context_ref.",
                    PyExcType::kContext);
  }

  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

void PythonClassSceneSound::tp_dealloc(PythonClassSceneSound* self) {
  BA_PYTHON_TRY;
  // Our Object::Ref needs to be released in the logic thread.
  auto* ptr = self->sound_;
  if (g_base->InLogicThread()) {
    delete ptr;
  } else {
    g_base->logic->event_loop()->PushCall([ptr] { delete ptr; });
  }
  BA_PYTHON_DEALLOC_CATCH;
  Py_TYPE(self)->tp_free(reinterpret_cast<PyObject*>(self));
}

bool PythonClassSceneSound::s_create_empty_ = false;
PyTypeObject PythonClassSceneSound::type_obj;
PyMethodDef PythonClassSceneSound::tp_methods[] = {
    {
        "play",
        (PyCFunction)Play,
        METH_VARARGS | METH_KEYWORDS,
        "play(volume: float = 1.0, position: Sequence[float] | None = None,\n"
        "     host_only: bool = False) -> None\n"
        "\n"
        "Play the sound a single time.\n"
        "\n"
        "If position is not provided, the sound will be at a constant volume\n"
        "everywhere. Position should be a float tuple of size 3.",
    },
    {nullptr}};
}  // namespace ballistica::scene_v1
