// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/python/class/python_class_scene_sound.h"

#include <string>
#include <vector>

#include "ballistica/base/audio/audio.h"
#include "ballistica/base/python/base_python.h"
#include "ballistica/scene_v1/support/scene.h"
#include "ballistica/shared/python/python.h"

namespace ballistica::scene_v1 {

auto PythonClassSceneSound::Play(PythonClassSceneSound* self, PyObject* args,
                                 PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  BA_PRECONDITION(g_base->InLogicThread());
  float volume = 1.0f;
  int host_only = 0;
  PyObject* pos_obj = Py_None;
  PyObject* group_obj = Py_None;
  PyObject* group_cap_obj = Py_None;
  PyObject* priority_obj = Py_None;
  static const char* kwlist[] = {"volume",     "position",       "host_only",
                                 "play_group", "play_group_cap", "priority",
                                 nullptr};
  if (!PyArg_ParseTupleAndKeywords(
          args, keywds, "|fOpOOO", const_cast<char**>(kwlist), &volume,
          &pos_obj, &host_only, &group_obj, &group_cap_obj, &priority_obj)) {
    return nullptr;
  }
  auto* sound = self->GetSound();

  SoundPlayOptions options;
  if (group_obj != Py_None) {
    options.group =
        base::Audio::NormalizePlayGroupName(Python::GetString(group_obj));
    if (options.group.empty()) {
      throw Exception("play_group can't be empty.", PyExcType::kValue);
    }
  }
  if (group_cap_obj != Py_None) {
    options.group_cap = static_cast<int>(Python::GetInt(group_cap_obj));
    if (options.group_cap < 1
        || options.group_cap > base::kMaxRemotePlayGroupCap) {
      throw Exception("play_group_cap must be between 1 and "
                          + std::to_string(base::kMaxRemotePlayGroupCap) + ".",
                      PyExcType::kValue);
    }
  }
  if (priority_obj != Py_None) {
    options.priority =
        static_cast<int>(g_base->python->GetPyEnum_SoundPriority(priority_obj));
  }
  options.Sanitize();

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
                                 static_cast<bool>(host_only), options);
    } else {
      scene->PlaySound(sound, volume, static_cast<bool>(host_only), options);
    }
  } else {
    throw Exception("Can't play sounds in this context_ref.",
                    PyExcType::kContext);
  }

  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

PyMethodDef PythonClassSceneSound::tp_methods[] = {
    {
        "play",
        (PyCFunction)Play,
        METH_VARARGS | METH_KEYWORDS,
        "play(volume: float = 1.0, position: Sequence[float] | None = None,\n"
        "     host_only: bool = False, play_group: str | None = None,\n"
        "     play_group_cap: int | None = None,\n"
        "     priority: bascenev1.SoundPriority | None = None) -> None\n"
        "\n"
        "Play the sound a single time.\n"
        "\n"
        "If position is not provided, the sound will be at a constant volume\n"
        "everywhere. Position should be a float tuple of size 3.\n"
        "\n"
        "Only so many sounds can play at once, and the last three arguments\n"
        "bear on which ones do when there are more than that. Sounds\n"
        "belong to play groups; by default a sound's group comes from its\n"
        "name, with numbered variations of a sound ('explosion01',\n"
        "'explosion02') sharing one. Only a few sounds of a group play at\n"
        "once, a new one cutting off the group's oldest. Pass\n"
        "``play_group`` to count this play toward a group of your choosing\n"
        "and ``play_group_cap`` to change how many of that group may play\n"
        "at once (1 means each play cuts off the last). ``priority``\n"
        "overrides the sound's own; see\n"
        ":class:`~bascenev1.SoundPriority`.",
    },
    {nullptr}};

}  // namespace ballistica::scene_v1
