// Released under the MIT License. See LICENSE for details.

#include "ballistica/ui_v1/python/class/python_class_ui_sound.h"

#include "ballistica/base/assets/sound_asset.h"
#include "ballistica/base/audio/audio.h"
#include "ballistica/ui_v1/ui_v1.h"

namespace ballistica::ui_v1 {

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
  auto play_id = g_base->audio->PlaySound(self->GetAsset(), volume);
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
