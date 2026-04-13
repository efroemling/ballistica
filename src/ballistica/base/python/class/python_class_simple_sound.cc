// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/python/class/python_class_simple_sound.h"

#include <string>

#include "ballistica/base/assets/sound_asset.h"
#include "ballistica/base/audio/audio.h"
#include "ballistica/base/logic/logic.h"
#include "ballistica/shared/foundation/event_loop.h"

namespace ballistica::base {

auto PythonClassSimpleSound::type_name() -> const char* {
  return "SimpleSound";
}

void PythonClassSimpleSound::SetupType(PyTypeObject* cls) {
  PythonClass::SetupType(cls);
  // Fully qualified type path we will be exposed as:
  cls->tp_name = "babase.SimpleSound";
  cls->tp_basicsize = sizeof(PythonClassSimpleSound);
  cls->tp_doc =
      "A simple sound wrapper for internal use.\n"
      "\n"
      "Do not use for gameplay code as it will only play locally.\n"
      "\n"
      ":meta private:";
  cls->tp_new = tp_new;
  cls->tp_dealloc = (destructor)tp_dealloc;
  cls->tp_repr = (reprfunc)tp_repr;
  cls->tp_methods = tp_methods;
}

auto PythonClassSimpleSound::Create(SoundAsset* sound) -> PyObject* {
  assert(TypeIsSetUp(&type_obj));
  auto* py_sound = reinterpret_cast<PythonClassSimpleSound*>(
      PyObject_CallObject(reinterpret_cast<PyObject*>(&type_obj), nullptr));
  if (!py_sound) {
    throw Exception("SimpleSound creation failed.");
  }

  *py_sound->sound_ = sound;
  return reinterpret_cast<PyObject*>(py_sound);
}

auto PythonClassSimpleSound::tp_repr(PythonClassSimpleSound* self)
    -> PyObject* {
  BA_PYTHON_TRY;
  SoundAsset* s = self->sound_->get();
  return Py_BuildValue(
      "s", (std::string("<Ballistica SimpleSound '") + (s->GetName()) + "'>")
               .c_str());
  BA_PYTHON_CATCH;
}

auto PythonClassSimpleSound::tp_new(PyTypeObject* type, PyObject* args,
                                    PyObject* keywds) -> PyObject* {
  auto* self =
      reinterpret_cast<PythonClassSimpleSound*>(type->tp_alloc(type, 0));
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
  self->sound_ = new Object::Ref<SoundAsset>();
  return reinterpret_cast<PyObject*>(self);
  BA_PYTHON_NEW_CATCH;
}

void PythonClassSimpleSound::tp_dealloc(PythonClassSimpleSound* self) {
  BA_PYTHON_TRY;
  // Our Object::Ref needs to be cleared in the logic thread.
  auto* ptr = self->sound_;
  if (g_base->InLogicThread()) {
    delete ptr;
  } else {
    g_base->logic->event_loop()->PushCall([ptr] { delete ptr; });
  }
  BA_PYTHON_DEALLOC_CATCH;
  Py_TYPE(self)->tp_free(reinterpret_cast<PyObject*>(self));
}

auto PythonClassSimpleSound::Play(PythonClassSimpleSound* self, PyObject* args,
                                  PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  float volume{1.0f};
  static const char* kwlist[] = {"volume", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "|f",
                                   const_cast<char**>(kwlist), &volume)) {
    return nullptr;
  }
  SoundAsset* s = self->sound_->get();
  g_base->audio->PlaySound(s, volume);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

PyTypeObject PythonClassSimpleSound::type_obj;
PyMethodDef PythonClassSimpleSound::tp_methods[] = {
    {"play", (PyCFunction)PythonClassSimpleSound::Play,
     METH_VARARGS | METH_KEYWORDS,
     "play() -> None\n"
     "\n"
     "Play the sound locally.\n"
     ""},

    {nullptr}};

}  // namespace ballistica::base
