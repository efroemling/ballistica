// Released under the MIT License. See LICENSE for details.

#include "ballistica/ui_v1/python/class/python_class_ui_sound.h"

#include <string>

#include "ballistica/base/assets/sound_asset.h"
#include "ballistica/base/audio/audio.h"
#include "ballistica/base/logic/logic.h"
#include "ballistica/shared/foundation/event_loop.h"
#include "ballistica/ui_v1/ui_v1.h"

namespace ballistica::ui_v1 {

auto PythonClassUISound::type_name() -> const char* { return "Sound"; }

void PythonClassUISound::SetupType(PyTypeObject* cls) {
  PythonClass::SetupType(cls);
  // Fully qualified type path we will be exposed as:
  cls->tp_name = "babase.Sound";
  cls->tp_basicsize = sizeof(PythonClassUISound);
  cls->tp_doc = "Sound asset for local user interface purposes.";
  cls->tp_new = tp_new;
  cls->tp_dealloc = (destructor)tp_dealloc;
  cls->tp_repr = (reprfunc)tp_repr;
  cls->tp_methods = tp_methods;
}

auto PythonClassUISound::Create(base::SoundAsset* sound) -> PyObject* {
  assert(TypeIsSetUp(&type_obj));
  auto* py_sound = reinterpret_cast<PythonClassUISound*>(
      PyObject_CallObject(reinterpret_cast<PyObject*>(&type_obj), nullptr));
  if (!py_sound) {
    throw Exception("Sound creation failed");
  }

  *py_sound->sound_ = sound;
  return reinterpret_cast<PyObject*>(py_sound);
}

auto PythonClassUISound::tp_repr(PythonClassUISound* self) -> PyObject* {
  BA_PYTHON_TRY;
  base::SoundAsset* s = self->sound_->get();
  return Py_BuildValue(
      "s", (std::string("<bauiv1.Sound '") + (s->GetName()) + "'>").c_str());
  BA_PYTHON_CATCH;
}

auto PythonClassUISound::tp_new(PyTypeObject* type, PyObject* args,
                                PyObject* keywds) -> PyObject* {
  auto* self = reinterpret_cast<PythonClassUISound*>(type->tp_alloc(type, 0));
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
  self->sound_ = new Object::Ref<base::SoundAsset>();
  return reinterpret_cast<PyObject*>(self);
  BA_PYTHON_NEW_CATCH;
}

void PythonClassUISound::tp_dealloc(PythonClassUISound* self) {
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

auto PythonClassUISound::Play(PythonClassUISound* self, PyObject* args,
                              PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  BA_PRECONDITION(g_base->InLogicThread());
  float volume{1.0f};
  static const char* kwlist[] = {"volume", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "|f",
                                   const_cast<char**>(kwlist), &volume)) {
    return nullptr;
  }
  base::SoundAsset* s = self->sound_->get();
  auto play_id = g_base->audio->PlaySound(s, volume);
  if (play_id) {
    self->playing_ = true;
    self->play_id_ = *play_id;
  } else {
    self->playing_ = false;
  }
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PythonClassUISound::Stop(PythonClassUISound* self, PyObject* args,
                              PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  BA_PRECONDITION(g_base->InLogicThread());
  static const char* kwlist[] = {nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "",
                                   const_cast<char**>(kwlist))) {
    return nullptr;
  }
  if (self->playing_) {
    g_base->audio->PushSourceStopSoundCall(self->play_id_);
    self->playing_ = false;
  }
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

PyTypeObject PythonClassUISound::type_obj;
PyMethodDef PythonClassUISound::tp_methods[] = {
    {"play", (PyCFunction)PythonClassUISound::Play,
     METH_VARARGS | METH_KEYWORDS,
     "play(volume: float = 1.0) -> None\n"
     "\n"
     "Play the sound locally.\n"
     ""},
    {"stop", (PyCFunction)PythonClassUISound::Stop,
     METH_VARARGS | METH_KEYWORDS,
     "stop() -> None\n"
     "\n"
     "Stop the sound if it is playing.\n"
     ""},

    {nullptr}};

}  // namespace ballistica::ui_v1
