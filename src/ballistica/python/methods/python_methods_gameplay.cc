// Released under the MIT License. See LICENSE for details.

#include "ballistica/python/methods/python_methods_gameplay.h"

#include <list>

#include "ballistica/app/app.h"
#include "ballistica/dynamics/bg/bg_dynamics.h"
#include "ballistica/dynamics/collision.h"
#include "ballistica/dynamics/dynamics.h"
#include "ballistica/dynamics/material/material_action.h"
#include "ballistica/game/connection/connection_set.h"
#include "ballistica/game/connection/connection_to_client.h"
#include "ballistica/game/game_stream.h"
#include "ballistica/game/host_activity.h"
#include "ballistica/generic/json.h"
#include "ballistica/graphics/graphics.h"
#include "ballistica/input/device/input_device.h"
#include "ballistica/media/component/sound.h"
#include "ballistica/platform/platform.h"
#include "ballistica/python/python.h"
#include "ballistica/python/python_context_call_runnable.h"
#include "ballistica/python/python_sys.h"
#include "ballistica/scene/node/node.h"
#include "ballistica/scene/node/node_type.h"
#include "ballistica/scene/scene.h"

namespace ballistica {

// Ignore signed bitwise stuff; python macros do it quite a bit.
#pragma clang diagnostic push
#pragma ide diagnostic ignored "hicpp-signed-bitwise"

auto PyNewNode(PyObject* self, PyObject* args, PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("new_node");
  Node* n = g_python->DoNewNode(args, keywds);
  if (!n) {
    return nullptr;
  }
  return n->NewPyRef();
  BA_PYTHON_CATCH;
}

auto PyPrintNodes(PyObject* self, PyObject* args) -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("print_nodes");
  HostActivity* host_activity =
      g_game->GetForegroundContext().GetHostActivity();
  if (!host_activity) {
    throw Exception(PyExcType::kContext);
  }
  Scene* scene = host_activity->scene();
  std::string s;
  int count = 1;
  for (auto&& i : scene->nodes()) {
    char buffer[128];
    snprintf(buffer, sizeof(buffer), "#%d:   type: %-14s desc: %s", count,
             i->type()->name().c_str(), i->label().c_str());
    s += buffer;
    Log(buffer);
    count++;
  }
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyGetNodes(PyObject* self, PyObject* args) -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("get_nodes");
  HostActivity* host_activity = Context::current().GetHostActivity();
  if (!host_activity) {
    throw Exception(PyExcType::kContext);
  }
  Scene* scene = host_activity->scene();
  PyObject* py_list = PyList_New(0);
  for (auto&& i : scene->nodes()) {
    PyList_Append(py_list, i->BorrowPyRef());
  }
  return py_list;
  BA_PYTHON_CATCH;
}

static auto DoGetCollideValue(Dynamics* dynamics, const Collision* c,
                              const char* name) -> PyObject* {
  BA_PYTHON_TRY;
  if (!strcmp(name, "depth")) {
    return Py_BuildValue("f", c->depth);
  } else if (!strcmp(name, "position")) {
    return Py_BuildValue("(fff)", c->x, c->y, c->z);
  } else if (!strcmp(name, "sourcenode")) {
    if (!dynamics->in_collide_message()) {
      PyErr_SetString(
          PyExc_AttributeError,
          "collide value 'sourcenode' is only valid while processing "
          "collide messages");
      return nullptr;
    }
    Node* n = dynamics->GetActiveCollideSrcNode();
    if (n) {
      return n->NewPyRef();
    } else {
      Py_RETURN_NONE;
    }
  } else if (!strcmp(name, "opposingnode")) {
    if (!dynamics->in_collide_message()) {
      PyErr_SetString(
          PyExc_AttributeError,
          "collide value 'opposingnode' is only valid while processing "
          "collide messages");
      return nullptr;
    }
    Node* n = dynamics->GetActiveCollideDstNode();
    if (n) {
      return n->NewPyRef();
    } else {
      Py_RETURN_NONE;
    }
  } else if (!strcmp(name, "opposingbody")) {
    return Py_BuildValue("i", dynamics->GetCollideMessageReverseOrder()
                                  ? c->body_id_2
                                  : c->body_id_1);
  } else {
    PyErr_SetString(
        PyExc_AttributeError,
        (std::string("\"") + name + "\" is not a valid collide value name")
            .c_str());
    return nullptr;
  }
  BA_PYTHON_CATCH;
}

auto PyGetCollisionInfo(PyObject* self, PyObject* args) -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("get_collision_info");
  HostActivity* host_activity = Context::current().GetHostActivity();
  if (!host_activity) {
    throw Exception(PyExcType::kContext);
  }
  Dynamics* dynamics = host_activity->scene()->dynamics();
  assert(dynamics);
  PyObject* obj = nullptr;

  // Take arg list as individual items or possibly a single tuple
  Py_ssize_t argc = PyTuple_GET_SIZE(args);
  if (argc > 1) {
    obj = args;
  } else if (argc == 1) {
    obj = PyTuple_GET_ITEM(args, 0);
  }
  Collision* c = dynamics->active_collision();
  if (!c) {
    PyErr_SetString(PyExc_RuntimeError,
                    "This must be called from a collision callback.");
    return nullptr;
  }
  if (PyUnicode_Check(obj)) {
    return DoGetCollideValue(dynamics, c, PyUnicode_AsUTF8(obj));
  } else if (PyTuple_Check(obj)) {
    Py_ssize_t size = PyTuple_GET_SIZE(obj);
    PyObject* return_tuple = PyTuple_New(size);
    for (Py_ssize_t i = 0; i < size; i++) {
      PyObject* o = PyTuple_GET_ITEM(obj, i);
      if (PyUnicode_Check(o)) {
        PyObject* val_obj = DoGetCollideValue(dynamics, c, PyUnicode_AsUTF8(o));
        if (val_obj) {
          PyTuple_SetItem(return_tuple, i, val_obj);
        } else {
          Py_DECREF(return_tuple);
          return nullptr;
        }
      } else {
        Py_DECREF(return_tuple);
        PyErr_SetString(PyExc_TypeError, "Expected a string as tuple member.");
        return nullptr;
      }
    }
    return return_tuple;
  } else {
    PyErr_SetString(PyExc_TypeError, "Expected a string or tuple.");
    return nullptr;
  }
  BA_PYTHON_CATCH;
}

auto PyCameraShake(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("camera_shake");
  assert(InGameThread());
  float intensity = 1.0f;
  static const char* kwlist[] = {"intensity", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "|f",
                                   const_cast<char**>(kwlist), &intensity)) {
    return nullptr;
  }
  g_graphics->LocalCameraShake(intensity);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyPlaySound(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("play_sound");

  assert(InGameThread());
  PyObject* sound_obj;
  float volume = 1.0f;
  int host_only = 0;
  PyObject* pos_obj = Py_None;
  static const char* kwlist[] = {"sound", "volume", "position", "host_only",
                                 nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "O|fOp",
                                   const_cast<char**>(kwlist), &sound_obj,
                                   &volume, &pos_obj, &host_only)) {
    return nullptr;
  }

  Sound* sound = Python::GetPySound(sound_obj);

  // Can play sounds in a host scene context.
  if (Scene* scene = Context::current().GetMutableScene()) {
    if (sound->scene() != scene) {
      throw Exception("Sound was not loaded in this context.",
                      PyExcType::kContext);
    }
    if (pos_obj != Py_None) {
      std::vector<float> vals = Python::GetPyFloats(pos_obj);
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
    throw Exception("Can't play sounds in this context.", PyExcType::kContext);
  }

  Py_RETURN_NONE;

  BA_PYTHON_CATCH;
}

auto PyEmitFx(PyObject* self, PyObject* args, PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("emit_fx");
  static const char* kwlist[] = {"position",  "velocity",     "count",
                                 "scale",     "spread",       "chunk_type",
                                 "emit_type", "tendril_type", nullptr};
  PyObject* pos_obj = Py_None;
  PyObject* vel_obj = Py_None;
  int count = 10;
  float scale = 1.0f;
  float spread = 1.0f;
  const char* chunk_type_str = "rock";
  const char* emit_type_str = "chunks";
  const char* tendril_type_str = "smoke";
  assert(InGameThread());
  if (!PyArg_ParseTupleAndKeywords(
          args, keywds, "O|Oiffsss", const_cast<char**>(kwlist), &pos_obj,
          &vel_obj, &count, &scale, &spread, &chunk_type_str, &emit_type_str,
          &tendril_type_str)) {
    return nullptr;
  }
  float x, y, z;
  assert(pos_obj);
  {
    std::vector<float> vals = Python::GetPyFloats(pos_obj);
    if (vals.size() != 3) {
      throw Exception("Expected 3 floats for position.", PyExcType::kValue);
    }
    x = vals[0];
    y = vals[1];
    z = vals[2];
  }
  float vx = 0.0f;
  float vy = 0.0f;
  float vz = 0.0f;
  if (vel_obj != Py_None) {
    std::vector<float> vals = Python::GetPyFloats(vel_obj);
    if (vals.size() != 3) {
      throw Exception("Expected 3 floats for velocity.", PyExcType::kValue);
    }
    vx = vals[0];
    vy = vals[1];
    vz = vals[2];
  }
  BGDynamicsChunkType chunk_type;
  if (!strcmp(chunk_type_str, "rock")) {
    chunk_type = BGDynamicsChunkType::kRock;
  } else if (!strcmp(chunk_type_str, "ice")) {
    chunk_type = BGDynamicsChunkType::kIce;
  } else if (!strcmp(chunk_type_str, "slime")) {
    chunk_type = BGDynamicsChunkType::kSlime;
  } else if (!strcmp(chunk_type_str, "metal")) {
    chunk_type = BGDynamicsChunkType::kMetal;
  } else if (!strcmp(chunk_type_str, "spark")) {
    chunk_type = BGDynamicsChunkType::kSpark;
  } else if (!strcmp(chunk_type_str, "splinter")) {
    chunk_type = BGDynamicsChunkType::kSplinter;
  } else if (!strcmp(chunk_type_str, "sweat")) {
    chunk_type = BGDynamicsChunkType::kSweat;
  } else {
    throw Exception(
        "Invalid chunk type: '" + std::string(chunk_type_str) + "'.",
        PyExcType::kValue);
  }
  BGDynamicsTendrilType tendril_type;
  if (!strcmp(tendril_type_str, "smoke")) {
    tendril_type = BGDynamicsTendrilType::kSmoke;
  } else if (!strcmp(tendril_type_str, "thin_smoke")) {
    tendril_type = BGDynamicsTendrilType::kThinSmoke;
  } else if (!strcmp(tendril_type_str, "ice")) {
    tendril_type = BGDynamicsTendrilType::kIce;
  } else {
    throw Exception(
        "Invalid tendril type: '" + std::string(tendril_type_str) + "'.",
        PyExcType::kValue);
  }
  BGDynamicsEmitType emit_type;
  if (!strcmp(emit_type_str, "chunks")) {
    emit_type = BGDynamicsEmitType::kChunks;
  } else if (!strcmp(emit_type_str, "stickers")) {
    emit_type = BGDynamicsEmitType::kStickers;
  } else if (!strcmp(emit_type_str, "tendrils")) {
    emit_type = BGDynamicsEmitType::kTendrils;
  } else if (!strcmp(emit_type_str, "distortion")) {
    emit_type = BGDynamicsEmitType::kDistortion;
  } else if (!strcmp(emit_type_str, "flag_stand")) {
    emit_type = BGDynamicsEmitType::kFlagStand;
  } else {
    throw Exception("Invalid emit type: '" + std::string(emit_type_str) + "'.",
                    PyExcType::kValue);
  }
  if (Scene* scene = Context::current().GetMutableScene()) {
    BGDynamicsEmission e;
    e.emit_type = emit_type;
    e.position = Vector3f(x, y, z);
    e.velocity = Vector3f(vx, vy, vz);
    e.count = count;
    e.scale = scale;
    e.spread = spread;
    e.chunk_type = chunk_type;
    e.tendril_type = tendril_type;
    if (GameStream* output_stream = scene->GetGameStream()) {
      output_stream->EmitBGDynamics(e);
    }
#if !BA_HEADLESS_BUILD
    g_bg_dynamics->Emit(e);
#endif  // !BA_HEADLESS_BUILD
  } else {
    throw Exception("Can't emit bg dynamics in this context.",
                    PyExcType::kContext);
  }
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PySetMapBounds(PyObject* self, PyObject* args) -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("set_map_bounds");
  HostActivity* host_activity = Context::current().GetHostActivity();
  if (!host_activity) {
    throw Exception(PyExcType::kContext);
  }
  float xmin, ymin, zmin, xmax, ymax, zmax;
  assert(InGameThread());
  if (!PyArg_ParseTuple(args, "(ffffff)", &xmin, &ymin, &zmin, &xmax, &ymax,
                        &zmax)) {
    return nullptr;
  }
  host_activity->scene()->SetMapBounds(xmin, ymin, zmin, xmax, ymax, zmax);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyGetForegroundHostActivity(PyObject* self, PyObject* args,
                                 PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("get_foreground_host_activity");
  static const char* kwlist[] = {nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "",
                                   const_cast<char**>(kwlist))) {
    return nullptr;
  }

  // Note: we return None if not in the game thread.
  HostActivity* h = InGameThread()
                        ? g_game->GetForegroundContext().GetHostActivity()
                        : nullptr;
  if (h != nullptr) {
    PyObject* obj = h->GetPyActivity();
    Py_INCREF(obj);
    return obj;
  }
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyGetGameRoster(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("get_game_roster");
  BA_PRECONDITION(InGameThread());
  static const char* kwlist[] = {nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "",
                                   const_cast<char**>(kwlist))) {
    return nullptr;
  }
  PythonRef py_client_list(PyList_New(0), PythonRef::kSteal);
  cJSON* party = g_game->game_roster();
  assert(party);
  int len = cJSON_GetArraySize(party);
  for (int i = 0; i < len; i++) {
    cJSON* client = cJSON_GetArrayItem(party, i);
    assert(client);
    cJSON* spec = cJSON_GetObjectItem(client, "spec");
    cJSON* players = cJSON_GetObjectItem(client, "p");
    PythonRef py_player_list(PyList_New(0), PythonRef::kSteal);
    if (players != nullptr) {
      int plen = cJSON_GetArraySize(players);
      for (int j = 0; j < plen; ++j) {
        cJSON* player = cJSON_GetArrayItem(players, j);
        if (player != nullptr) {
          cJSON* name = cJSON_GetObjectItem(player, "n");
          cJSON* py_name_full = cJSON_GetObjectItem(player, "nf");
          cJSON* id_obj = cJSON_GetObjectItem(player, "i");
          int id_val = id_obj ? id_obj->valueint : -1;
          if (name != nullptr && name->valuestring != nullptr
              && py_name_full != nullptr && py_name_full->valuestring != nullptr
              && id_val != -1) {
            PythonRef py_player(
                Py_BuildValue(
                    "{sssssi}", "name",
                    Utils::GetValidUTF8(name->valuestring, "ggr1").c_str(),
                    "name_full",
                    Utils::GetValidUTF8(py_name_full->valuestring, "ggr2")
                        .c_str(),
                    "id", id_val),
                PythonRef::kSteal);
            // This increments ref.
            PyList_Append(py_player_list.get(), py_player.get());
          }
        }
      }
    }

    // If there's a client_id with this data, include it; otherwise pass None.
    cJSON* client_id = cJSON_GetObjectItem(client, "i");
    int clientid{};
    PythonRef client_id_ref;
    if (client_id != nullptr) {
      clientid = client_id->valueint;
      client_id_ref.Steal(PyLong_FromLong(clientid));
    } else {
      client_id_ref.Acquire(Py_None);
    }

    // Let's also include a public account-id if we have one.
    std::string account_id;
    if (clientid == -1) {
      account_id = AppInternalGetPublicAccountID();
    } else {
      auto client2 =
          g_game->connections()->connections_to_clients().find(clientid);
      if (client2 != g_game->connections()->connections_to_clients().end()) {
        account_id = client2->second->peer_public_account_id();
      }
    }
    PythonRef account_id_ref;
    if (account_id.empty()) {
      account_id_ref.Acquire(Py_None);
    } else {
      account_id_ref.Steal(PyUnicode_FromString(account_id.c_str()));
    }

    // Py_BuildValue steals a ref; gotta increment ourself (edit: NO IT DOESNT)
    // Py_INCREF(py_player_list.get());
    PythonRef py_client(
        Py_BuildValue(
            "{sssssOsOsO}", "display_string",
            (spec && spec->valuestring)
                ? PlayerSpec(spec->valuestring).GetDisplayString().c_str()
                : "",
            "spec_string", (spec && spec->valuestring) ? spec->valuestring : "",
            "players", py_player_list.get(), "client_id", client_id_ref.get(),
            "account_id", account_id_ref.get()),
        PythonRef::kSteal);
    PyList_Append(py_client_list.get(),
                  py_client.get());  // this increments ref
  }
  return py_client_list.NewRef();
  BA_PYTHON_CATCH;
}

auto PyGetScoresToBeat(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("get_scores_to_beat");
  const char* level;
  const char* config;
  PyObject* callback_obj = Py_None;
  static const char* kwlist[] = {"level", "config", "callback", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "ssO",
                                   const_cast<char**>(kwlist), &level, &config,
                                   &callback_obj)) {
    return nullptr;
  }

  // Allocate a Call object for this and pass its pointer to the main thread;
  // we'll ref/de-ref it when it comes back.
  auto* call = Object::NewDeferred<PythonContextCall>(callback_obj);
  g_app->PushGetScoresToBeatCall(level, config, call);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PySetDebugSpeedExponent(PyObject* self, PyObject* args) -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("set_debug_speed_exponent");
  int speed;
  if (!PyArg_ParseTuple(args, "i", &speed)) {
    return nullptr;
  }
  HostActivity* host_activity = Context::current().GetHostActivity();
  if (!host_activity) {
    throw Exception(PyExcType::kContext);
  }
#if BA_DEBUG_BUILD
  g_game->SetDebugSpeedExponent(speed);
#else
  throw Exception("This call only functions in the debug build.");
#endif
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyGetReplaySpeedExponent(PyObject* self, PyObject* args) -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("get_replay_speed_exponent");
  assert(g_game);
  return PyLong_FromLong(g_game->replay_speed_exponent());
  BA_PYTHON_CATCH;
}

auto PySetReplaySpeedExponent(PyObject* self, PyObject* args) -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("set_replay_speed_exponent");
  int speed;
  if (!PyArg_ParseTuple(args, "i", &speed)) return nullptr;
  assert(g_game);
  g_game->SetReplaySpeedExponent(speed);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyResetGameActivityTracking(PyObject* self, PyObject* args,
                                 PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("reset_game_activity_tracking");
  static const char* kwlist[] = {nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "",
                                   const_cast<char**>(kwlist))) {
    return nullptr;
  }
  if (g_game) {
    g_game->ResetActivityTracking();
  }
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyResetRandomPlayerNames(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("reset_random_player_names");
  InputDevice::ResetRandomNames();
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyGetRandomNames(PyObject* self, PyObject* args) -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("get_random_names");
  PyObject* list = PyList_New(0);
  const std::list<std::string>& random_name_list = Utils::GetRandomNameList();
  for (const auto& i : random_name_list) {
    assert(Utils::IsValidUTF8(i));
    PyObject* obj = PyUnicode_FromString(i.c_str());
    PyList_Append(list, obj);
    Py_DECREF(obj);
  }
  return list;
  BA_PYTHON_CATCH;
}

auto PythonMethodsGameplay::GetMethods() -> std::vector<PyMethodDef> {
  return {
      {"get_random_names", PyGetRandomNames, METH_VARARGS,
       "get_random_names() -> list\n"
       "\n"
       "(internal)\n"
       "\n"
       "Returns the random names used by the game."},

      {"reset_random_player_names", (PyCFunction)PyResetRandomPlayerNames,
       METH_VARARGS | METH_KEYWORDS,
       "reset_random_player_names() -> None\n"
       "\n"
       "(internal)"},

      {"reset_game_activity_tracking", (PyCFunction)PyResetGameActivityTracking,
       METH_VARARGS | METH_KEYWORDS,
       "reset_game_activity_tracking() -> None\n"
       "\n"
       "(internal)"},

      {"set_replay_speed_exponent", PySetReplaySpeedExponent, METH_VARARGS,
       "set_replay_speed_exponent(speed: int) -> None\n"
       "\n"
       "(internal)\n"
       "\n"
       "Set replay speed. Actual displayed speed is pow(2, speed)."},

      {"get_replay_speed_exponent", PyGetReplaySpeedExponent, METH_VARARGS,
       "get_replay_speed_exponent() -> int\n"
       "\n"
       "(internal)\n"
       "\n"
       "Returns current replay speed value. Actual displayed speed is "
       "pow(2,speed)."},

      {"set_debug_speed_exponent", PySetDebugSpeedExponent, METH_VARARGS,
       "set_debug_speed_exponent(speed: int) -> None\n"
       "\n"
       "(internal)\n"
       "\n"
       "Sets the debug speed scale for the game. Actual speed is "
       "pow(2,speed)."},

      {"get_scores_to_beat", (PyCFunction)PyGetScoresToBeat,
       METH_VARARGS | METH_KEYWORDS,
       "get_scores_to_beat(level: str, config: str, callback: Callable) -> "
       "None\n"
       "\n"
       "(internal)"},

      {"get_game_roster", (PyCFunction)PyGetGameRoster,
       METH_VARARGS | METH_KEYWORDS,
       "get_game_roster() -> list[dict[str, Any]]\n"
       "\n"
       "(internal)"},

      {"get_foreground_host_activity", (PyCFunction)PyGetForegroundHostActivity,
       METH_VARARGS | METH_KEYWORDS,
       "get_foreground_host_activity() -> Optional[ba.Activity]\n"
       "\n"
       "(internal)\n"
       "\n"
       "Returns the ba.Activity currently in the foreground, or None if there\n"
       "is none.\n"},

      {"set_map_bounds", (PyCFunction)PySetMapBounds,
       METH_VARARGS | METH_KEYWORDS,
       "set_map_bounds(bounds: tuple[float, float, float, float, float, "
       "float])\n"
       "  -> None\n"
       "\n"
       "(internal)\n"
       "\n"
       "Set map bounds. Generally nodes that go outside of this box are "
       "killed."},

      {"emitfx", (PyCFunction)PyEmitFx, METH_VARARGS | METH_KEYWORDS,
       "emitfx(position: Sequence[float],\n"
       "  velocity: Optional[Sequence[float]] = None,\n"
       "  count: int = 10, scale: float = 1.0, spread: float = 1.0,\n"
       "  chunk_type: str = 'rock', emit_type: str ='chunks',\n"
       "  tendril_type: str = 'smoke') -> None\n"
       "\n"
       "Emit particles, smoke, etc. into the fx sim layer.\n"
       "\n"
       "Category: **Gameplay Functions**\n"
       "\n"
       "The fx sim layer is a secondary dynamics simulation that runs in\n"
       "the background and just looks pretty; it does not affect gameplay.\n"
       "Note that the actual amount emitted may vary depending on graphics\n"
       "settings, exiting element counts, or other factors."},

      {"playsound", (PyCFunction)PyPlaySound, METH_VARARGS | METH_KEYWORDS,
       "playsound(sound: Sound, volume: float = 1.0,\n"
       "  position: Sequence[float] = None, host_only: bool = False) -> None\n"
       "\n"
       "Play a ba.Sound a single time.\n"
       "\n"
       "Category: **Gameplay Functions**\n"
       "\n"
       "If position is not provided, the sound will be at a constant volume\n"
       "everywhere. Position should be a float tuple of size 3."},

      {"camerashake", (PyCFunction)PyCameraShake, METH_VARARGS | METH_KEYWORDS,
       "camerashake(intensity: float = 1.0) -> None\n"
       "\n"
       "Shake the camera.\n"
       "\n"
       "Category: **Gameplay Functions**\n"
       "\n"
       "Note that some cameras and/or platforms (such as VR) may not display\n"
       "camera-shake, so do not rely on this always being visible to the\n"
       "player as a gameplay cue."},

      {"get_collision_info", PyGetCollisionInfo, METH_VARARGS,
       "get_collision_info(*args: Any) -> Any\n"
       "\n"
       "Return collision related values\n"
       "\n"
       "Category: **Gameplay Functions**\n"
       "\n"
       "Returns a single collision value or tuple of values such as location,\n"
       "depth, nodes involved, etc. Only call this in the handler of a\n"
       "collision-triggered callback or message"},

      {"getnodes", PyGetNodes, METH_VARARGS,
       "getnodes() -> list\n"
       "\n"
       "Return all nodes in the current ba.Context."
       "\n"
       "Category: **Gameplay Functions**"},

      {"printnodes", PyPrintNodes, METH_VARARGS,
       "printnodes() -> None\n"
       "\n"
       "Print various info about existing nodes; useful for debugging.\n"
       "\n"
       "Category: **Gameplay Functions**"},

      {"newnode", (PyCFunction)PyNewNode, METH_VARARGS | METH_KEYWORDS,
       "newnode(type: str, owner: ba.Node = None,\n"
       "attrs: dict = None, name: str = None, delegate: Any = None)\n"
       " -> Node\n"
       "\n"
       "Add a node of the given type to the game.\n"
       "\n"
       "Category: **Gameplay Functions**\n"
       "\n"
       "If a dict is provided for 'attributes', the node's initial attributes\n"
       "will be set based on them.\n"
       "\n"
       "'name', if provided, will be stored with the node purely for "
       "debugging\n"
       "purposes. If no name is provided, an automatic one will be generated\n"
       "such as 'terrain@foo.py:30'.\n"
       "\n"
       "If 'delegate' is provided, Python messages sent to the node will go "
       "to\n"
       "that object's handlemessage() method. Note that the delegate is "
       "stored\n"
       "as a weak-ref, so the node itself will not keep the object alive.\n"
       "\n"
       "if 'owner' is provided, the node will be automatically killed when "
       "that\n"
       "object dies. 'owner' can be another node or a ba.Actor"},
  };
}

#pragma clang diagnostic pop

}  // namespace ballistica
