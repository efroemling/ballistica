// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/python/class/python_class_session_player.h"

#include <string>
#include <vector>

#include "ballistica/base/logic/logic.h"
#include "ballistica/base/python/base_python.h"
#include "ballistica/core/logging/logging_macros.h"
#include "ballistica/scene_v1/python/scene_v1_python.h"
#include "ballistica/scene_v1/support/host_session.h"
#include "ballistica/scene_v1/support/scene_v1_input_device_delegate.h"
#include "ballistica/shared/foundation/event_loop.h"
#include "ballistica/shared/python/python.h"

namespace ballistica::scene_v1 {

// Ignore signed bitwise stuff; python macros do it quite a bit.
#pragma clang diagnostic push
#pragma ide diagnostic ignored "hicpp-signed-bitwise"
#pragma ide diagnostic ignored "RedundantCast"

auto PythonClassSessionPlayer::nb_bool(PythonClassSessionPlayer* self) -> int {
  return self->player_->exists();
}

PyNumberMethods PythonClassSessionPlayer::as_number_;

// Attrs we expose through our custom getattr/setattr.
#define ATTR_IN_GAME "in_game"
#define ATTR_SESSIONTEAM "sessionteam"
#define ATTR_COLOR "color"
#define ATTR_HIGHLIGHT "highlight"
#define ATTR_CHARACTER "character"
#define ATTR_ACTIVITYPLAYER "activityplayer"
#define ATTR_ID "id"
#define ATTR_INPUT_DEVICE "inputdevice"

// The set we expose via dir().
static const char* extra_dir_attrs[] = {
    ATTR_ID,        ATTR_IN_GAME,   ATTR_SESSIONTEAM,  ATTR_COLOR,
    ATTR_HIGHLIGHT, ATTR_CHARACTER, ATTR_INPUT_DEVICE, nullptr};

auto PythonClassSessionPlayer::type_name() -> const char* {
  return "SessionPlayer";
}

void PythonClassSessionPlayer::SetupType(PyTypeObject* cls) {
  PythonClass::SetupType(cls);
  // Fully qualified type path we will be exposed as:
  cls->tp_name = "bascenev1.SessionPlayer";
  cls->tp_basicsize = sizeof(PythonClassSessionPlayer);

  // clang-format off

  cls->tp_doc =
    "A reference to a player in a :class:`~bascenev1.Session`.\n"
    "\n"
    "These are created and managed internally and provided to your\n"
    ":class:`~bascenev1.Session`/:class:`~bascenev1.Activity`\n"
    "instances. Be aware that, like :class:`~bascenev1.Node` objects,\n"
    ":class:`~bascenev1.SessionPlayer` objects are effectively 'weak'\n"
    "references under-the-hood; a player can leave the game at any point.\n"
    "For this reason, you should make judicious use of the\n"
    ":meth:`bascenev1.SessionPlayer.exists()` method (or boolean operator) to\n"
    "ensure that a :class:`SessionPlayer` is still present if retaining\n"
    "references to one for any length of time.\n"
    "\n"
    "Attributes:\n"
    "    " ATTR_ID " (int):\n"
    "        The unique numeric id of the player.\n"
    "\n"
    "        Note that you can also use the boolean operator for this same\n"
    "        functionality, so a statement such as ``if player:`` will do\n"
    "        the right thing both for :class:`~bascenev1.SessionPlayer`\n"
    "        objects as well as values of ``None``.\n"
    "\n"
    "    " ATTR_IN_GAME " (bool):\n"
    "        This bool value will be True once the player has completed\n"
    "        any lobby character/team selection.\n"
    "\n"
    "    " ATTR_SESSIONTEAM " (bascenev1.SessionTeam):\n"
    "        The session-team this session-player is on. If the player is\n"
    "        still in its lobby selecting a team/etc. then a\n"
    "        :class:`~bascenev1.SessionTeamNotFoundError` will be raised.\n"
    "\n"
    "    " ATTR_INPUT_DEVICE " (bascenev1.InputDevice):\n"
    "        The input device associated with the player.\n"
    "\n"
    "    " ATTR_COLOR " (Sequence[float]):\n"
    "        The base color for this player.\n"
    "        In team games this will match the team's\n"
    "        color.\n"
    "\n"
    "    " ATTR_HIGHLIGHT " (Sequence[float]):\n"
    "        A secondary color for this player.\n"
    "        This is used for minor highlights and accents\n"
    "        to allow a player to stand apart from his teammates\n"
    "        who may all share the same team (primary) color.\n"
    "\n"
    "    " ATTR_CHARACTER " (str):\n"
    "        The character this player has selected in their profile.\n"
    "\n"
    "    " ATTR_ACTIVITYPLAYER " (bascenev1.Player | None):\n"
    "        The current game-specific instance for this player.\n";

  // clang-format on

  cls->tp_new = tp_new;
  cls->tp_repr = (reprfunc)tp_repr;
  cls->tp_methods = tp_methods;
  cls->tp_dealloc = (destructor)tp_dealloc;
  cls->tp_getattro = (getattrofunc)tp_getattro;
  cls->tp_setattro = (setattrofunc)tp_setattro;

  // We provide number methods only for bool functionality.
  memset(&as_number_, 0, sizeof(as_number_));
  as_number_.nb_bool = (inquiry)nb_bool;
  cls->tp_as_number = &as_number_;
}

auto PythonClassSessionPlayer::Create(Player* player) -> PyObject* {
  // Make sure we only have one python ref per material.
  if (player) {
    assert(!player->HasPyRef());
  }
  s_create_empty_ = true;  // Prevent class from erroring on create.
  assert(TypeIsSetUp(&type_obj));
  auto* py_player = reinterpret_cast<PythonClassSessionPlayer*>(
      PyObject_CallObject(reinterpret_cast<PyObject*>(&type_obj), nullptr));
  s_create_empty_ = false;
  if (!py_player) {
    throw Exception("bascenev1.Player creation failed.");
  }

  *py_player->player_ = player;
  return reinterpret_cast<PyObject*>(py_player);
}

auto PythonClassSessionPlayer::GetPlayer(bool doraise) const -> Player* {
  Player* player = player_->get();
  if ((!player) && doraise) {
    throw Exception("Invalid SessionPlayer.",
                    PyExcType::kSessionPlayerNotFound);
  }
  return player;
}

auto PythonClassSessionPlayer::tp_repr(PythonClassSessionPlayer* self)
    -> PyObject* {
  BA_PYTHON_TRY;
  Player* p = self->player_->get();
  int player_id = p ? p->id() : -1;
  std::string p_name = p ? p->GetName() : "invalid";
  return Py_BuildValue("s",
                       (std::string("<Ballistica SessionPlayer ")
                        + std::to_string(player_id) + " \"" + p_name + "\">")
                           .c_str());
  BA_PYTHON_CATCH;
}

auto PythonClassSessionPlayer::tp_new(PyTypeObject* type, PyObject* args,
                                      PyObject* keywds) -> PyObject* {
  auto* self =
      reinterpret_cast<PythonClassSessionPlayer*>(type->tp_alloc(type, 0));
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

  // If the user is creating one, make sure they passed None to get an
  // invalid ref.
  // Clion incorrectly things s_create_empty will always be false.
#pragma clang diagnostic push
#pragma ide diagnostic ignored "ConstantConditionsOC"

  if (!s_create_empty_) {
    if (!PyTuple_Check(args) || (PyTuple_GET_SIZE(args) != 1)
        || (keywds != nullptr) || (PyTuple_GET_ITEM(args, 0) != Py_None))
      throw Exception(
          "Can't instantiate SessionPlayers. To create an invalid"
          " SessionPlayer reference, call bascenev1.SessionPlayer(None).");
  }
  self->player_ = new Object::WeakRef<Player>();
#pragma clang diagnostic pop
  return reinterpret_cast<PyObject*>(self);
  BA_PYTHON_NEW_CATCH;
}

void PythonClassSessionPlayer::tp_dealloc(PythonClassSessionPlayer* self) {
  BA_PYTHON_TRY;

  // These have to be deleted in the logic thread - send the ptr along if need
  // be; otherwise do it immediately.
  if (!g_base->InLogicThread()) {
    Object::WeakRef<Player>* p = self->player_;
    g_base->logic->event_loop()->PushCall([p] { delete p; });
  } else {
    delete self->player_;
  }
  BA_PYTHON_DEALLOC_CATCH;
  Py_TYPE(self)->tp_free(reinterpret_cast<PyObject*>(self));
}

auto PythonClassSessionPlayer::tp_getattro(PythonClassSessionPlayer* self,
                                           PyObject* attr) -> PyObject* {
  BA_PYTHON_TRY;

  BA_PRECONDITION(g_base->InLogicThread());

  // Assuming this will always be a str?
  assert(PyUnicode_Check(attr));

  const char* s = PyUnicode_AsUTF8(attr);
  if (!strcmp(s, ATTR_IN_GAME)) {
    Player* p = self->player_->get();
    if (!p) {
      throw Exception(PyExcType::kSessionPlayerNotFound);
    }

    // GetPyTeam returns a new ref or nullptr.
    auto team{PythonRef::StolenSoft(p->GetPyTeam())};
    // We get placed on a team as soon as we finish in the lobby
    // so lets use that as whether we're in-game or not.
    if (!team.exists()) {
      Py_RETURN_FALSE;
    } else {
      Py_RETURN_TRUE;
    }
  } else if (!strcmp(s, ATTR_ID)) {
    Player* p = self->player_->get();
    if (!p) {
      throw Exception(PyExcType::kSessionPlayerNotFound);
    }
    return PyLong_FromLong(p->id());
  } else if (!strcmp(s, ATTR_INPUT_DEVICE)) {
    Player* player = self->player_->get();
    if (!player) {
      throw Exception(PyExcType::kSessionPlayerNotFound);
    }

    if (auto* delegate = player->input_device_delegate()) {
      return delegate->NewPyRef();
    }
    throw Exception(PyExcType::kInputDeviceNotFound);
  } else if (!strcmp(s, ATTR_SESSIONTEAM)) {
    Player* p = self->player_->get();
    if (!p) {
      throw Exception(PyExcType::kSessionPlayerNotFound);
    }
    // GetPyTeam returns a new ref or nullptr.
    auto team{PythonRef::StolenSoft(p->GetPyTeam())};
    if (!team.exists()) {
      PyErr_SetString(
          g_base->python->objs()
              .Get(base::BasePython::ObjID::kSessionTeamNotFoundError)
              .get(),
          "SessionTeam does not exist.");
      return nullptr;
    }
    return team.NewRef();
  } else if (!strcmp(s, ATTR_CHARACTER)) {
    Player* p = self->player_->get();
    if (!p) {
      throw Exception(PyExcType::kSessionPlayerNotFound);
    }
    if (!p->has_py_data()) {
      BA_LOG_ONCE(LogName::kBa, LogLevel::kError,
                  "Calling getAttr for player attr '" + std::string(s)
                      + "' without data set.");
    }
    PyObject* obj = p->GetPyCharacter();
    Py_INCREF(obj);
    return obj;
  } else if (!strcmp(s, ATTR_COLOR)) {
    Player* p = self->player_->get();
    if (!p) {
      throw Exception(PyExcType::kSessionPlayerNotFound);
    }
    if (!p->has_py_data()) {
      BA_LOG_ONCE(LogName::kBa, LogLevel::kError,
                  "Calling getAttr for player attr '" + std::string(s)
                      + "' without data set.");
    }
    PyObject* obj = p->GetPyColor();
    Py_INCREF(obj);
    return obj;
  } else if (!strcmp(s, ATTR_HIGHLIGHT)) {
    Player* p = self->player_->get();
    if (!p) {
      throw Exception(PyExcType::kSessionPlayerNotFound);
    }
    if (!p->has_py_data()) {
      BA_LOG_ONCE(LogName::kBa, LogLevel::kError,
                  "Calling getAttr for player attr '" + std::string(s)
                      + "' without data set.");
    }
    PyObject* obj = p->GetPyHighlight();
    Py_INCREF(obj);
    return obj;
  } else if (!strcmp(s, ATTR_ACTIVITYPLAYER)) {
    Player* p = self->player_->get();
    if (!p) {
      throw Exception(PyExcType::kSessionPlayerNotFound);
    }
    if (!p->has_py_data()) {
      BA_LOG_ONCE(LogName::kBa, LogLevel::kError,
                  "Calling getAttr for player attr '" + std::string(s)
                      + "' without data set.");
    }
    PyObject* obj = p->GetPyActivityPlayer();
    Py_INCREF(obj);
    return obj;
  }

  // Fall back to generic behavior.
  PyObject* val;
  val = PyObject_GenericGetAttr(reinterpret_cast<PyObject*>(self), attr);
  return val;
  BA_PYTHON_CATCH;
}

auto PythonClassSessionPlayer::tp_setattro(PythonClassSessionPlayer* self,
                                           PyObject* attr, PyObject* val)
    -> int {
  BA_PYTHON_TRY;

  BA_PRECONDITION(g_base->InLogicThread());

  // Assuming this will always be a str?
  assert(PyUnicode_Check(attr));
  const char* s = PyUnicode_AsUTF8(attr);

  if (!strcmp(s, ATTR_ACTIVITYPLAYER)) {
    Player* p = self->player_->get();
    if (!p) {
      throw Exception(PyExcType::kSessionPlayerNotFound);
    }
    p->SetPyActivityPlayer(val);
    return 0;
  }
  throw Exception("Attr '" + std::string(PyUnicode_AsUTF8(attr))
                      + "' is not settable on SessionPlayer objects.",
                  PyExcType::kAttribute);
  // return PyObject_GenericSetAttr(reinterpret_cast<PyObject*>(self), attr,
  // val);
  BA_PYTHON_INT_CATCH;
}

auto PythonClassSessionPlayer::GetName(PythonClassSessionPlayer* self,
                                       PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  assert(g_base->InLogicThread());
  int full = false;
  int icon = true;
  static const char* kwlist[] = {"full", "icon", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "|pp",
                                   const_cast<char**>(kwlist), &full, &icon)) {
    return nullptr;
  }
  Player* p = self->player_->get();
  if (!p) {
    throw Exception(PyExcType::kSessionPlayerNotFound);
  }
  return PyUnicode_FromString(
      p->GetName(static_cast<bool>(full), static_cast<bool>(icon)).c_str());
  BA_PYTHON_CATCH;
}

auto PythonClassSessionPlayer::Exists(PythonClassSessionPlayer* self)
    -> PyObject* {
  BA_PYTHON_TRY;
  assert(g_base->InLogicThread());
  if (self->player_->exists()) {
    Py_RETURN_TRUE;
  }
  Py_RETURN_FALSE;
  BA_PYTHON_CATCH;
}

auto PythonClassSessionPlayer::SetName(PythonClassSessionPlayer* self,
                                       PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  assert(g_base->InLogicThread());
  PyObject* name_obj;
  PyObject* full_name_obj = Py_None;

  // This should be false for temp names like <choosing player>.
  int real = 1;
  static const char* kwlist[] = {"name", "full_name", "real", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "O|Op",
                                   const_cast<char**>(kwlist), &name_obj,
                                   &full_name_obj, &real)) {
    return nullptr;
  }
  std::string name = g_base->python->GetPyLString(name_obj);
  std::string full_name = (full_name_obj == Py_None)
                              ? name
                              : g_base->python->GetPyLString(full_name_obj);
  Player* p = self->player_->get();
  if (!p) {
    throw Exception(PyExcType::kSessionPlayerNotFound);
  }
  p->SetName(name, full_name, static_cast<bool>(real));
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PythonClassSessionPlayer::ResetInput(PythonClassSessionPlayer* self)
    -> PyObject* {
  BA_PYTHON_TRY;
  assert(g_base->InLogicThread());
  Player* p = self->player_->get();
  if (!p) {
    throw Exception(PyExcType::kSessionPlayerNotFound);
  }
  p->ResetInput();
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PythonClassSessionPlayer::AssignInputCall(PythonClassSessionPlayer* self,
                                               PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  assert(g_base->InLogicThread());
  PyObject* input_type_obj;
  PyObject* call_obj;
  static const char* kwlist[] = {"type", "call", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "OO",
                                   const_cast<char**>(kwlist), &input_type_obj,
                                   &call_obj)) {
    return nullptr;
  }
  Player* player = self->player_->get();
  if (!player) {
    throw Exception(PyExcType::kSessionPlayerNotFound);
  }
  if (g_base->python->IsPyEnum_InputType(input_type_obj)) {
    InputType input_type = g_base->python->GetPyEnum_InputType(input_type_obj);
    player->AssignInputCall(input_type, call_obj);
  } else {
    if (!PyTuple_Check(input_type_obj)) {
      PyErr_SetString(PyExc_TypeError,
                      "Expected InputType or tuple for type arg.");
      return nullptr;
    }
    Py_ssize_t tuple_size = PyTuple_GET_SIZE(input_type_obj);
    for (Py_ssize_t i = 0; i < tuple_size; i++) {
      PyObject* obj = PyTuple_GET_ITEM(input_type_obj, i);
      if (!g_base->python->IsPyEnum_InputType(obj)) {
        PyErr_SetString(PyExc_TypeError, "Expected tuple of InputTypes.");
        return nullptr;
      }
      InputType input_type = g_base->python->GetPyEnum_InputType(obj);
      player->AssignInputCall(input_type, call_obj);
    }
  }
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PythonClassSessionPlayer::RemoveFromGame(PythonClassSessionPlayer* self)
    -> PyObject* {
  BA_PYTHON_TRY;
  assert(g_base->InLogicThread());
  Player* player = self->player_->get();
  if (!player) {
    throw Exception(PyExcType::kSessionPlayerNotFound);
  } else {
    HostSession* host_session = player->GetHostSession();
    if (!host_session) {
      throw Exception("Player's host-session not found.",
                      PyExcType::kSessionNotFound);
    }
    host_session->RemovePlayer(player);
  }
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PythonClassSessionPlayer::GetTeam(PythonClassSessionPlayer* self)
    -> PyObject* {
  BA_PYTHON_TRY;
  assert(g_base->InLogicThread());
  Player* p = self->player_->get();
  if (!p) {
    throw Exception(PyExcType::kSessionPlayerNotFound);
  }
  // GetPyTeam() returns a new ref or nullptr.
  auto team{PythonRef::StolenSoft(p->GetPyTeam())};
  return team.NewRef();
  BA_PYTHON_CATCH;
}

// NOTE: this returns their PUBLIC account-id; we want to keep
// actual account-ids as hidden as possible for now.
auto PythonClassSessionPlayer::GetV1AccountID(PythonClassSessionPlayer* self)
    -> PyObject* {
  BA_PYTHON_TRY;
  assert(g_base->InLogicThread());
  Player* p = self->player_->get();
  if (!p) {
    throw Exception(PyExcType::kSessionPlayerNotFound);
  }
  std::string account_id = p->GetPublicV1AccountID();
  if (account_id.empty()) {
    Py_RETURN_NONE;
  }
  return PyUnicode_FromString(account_id.c_str());
  BA_PYTHON_CATCH;
}

auto PythonClassSessionPlayer::SetData(PythonClassSessionPlayer* self,
                                       PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  assert(g_base->InLogicThread());
  PyObject* team_obj;
  PyObject* character_obj;
  PyObject* color_obj;
  PyObject* highlight_obj;
  static const char* kwlist[] = {"team", "character", "color", "highlight",
                                 nullptr};
  if (!PyArg_ParseTupleAndKeywords(
          args, keywds, "OOOO", const_cast<char**>(kwlist), &team_obj,
          &character_obj, &color_obj, &highlight_obj)) {
    return nullptr;
  }
  Player* p = self->player_->get();
  if (!p) {
    throw Exception(PyExcType::kSessionPlayerNotFound);
  }
  p->set_has_py_data(true);
  p->SetPyTeam(team_obj);
  p->SetPyCharacter(character_obj);
  p->SetPyColor(color_obj);
  p->SetPyHighlight(highlight_obj);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PythonClassSessionPlayer::GetIconInfo(PythonClassSessionPlayer* self)
    -> PyObject* {
  BA_PYTHON_TRY;
  assert(g_base->InLogicThread());
  Player* p = self->player_->get();
  if (!p) {
    throw Exception(PyExcType::kSessionPlayerNotFound);
  }
  std::vector<float> color = p->icon_tint_color();
  std::vector<float> color2 = p->icon_tint2_color();
  return Py_BuildValue(
      "{sssss(fff)s(fff)}", "texture", p->icon_tex_name().c_str(),
      "tint_texture", p->icon_tint_tex_name().c_str(), "tint_color", color[0],
      color[1], color[2], "tint2_color", color2[0], color2[1], color2[2]);
  BA_PYTHON_CATCH;
}

auto PythonClassSessionPlayer::SetIconInfo(PythonClassSessionPlayer* self,
                                           PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  assert(g_base->InLogicThread());
  PyObject* texture_name_obj;
  PyObject* tint_texture_name_obj;
  PyObject* tint_color_obj;
  PyObject* tint2_color_obj;
  static const char* kwlist[] = {"texture", "tint_texture", "tint_color",
                                 "tint2_color", nullptr};
  if (!PyArg_ParseTupleAndKeywords(
          args, keywds, "OOOO", const_cast<char**>(kwlist), &texture_name_obj,
          &tint_texture_name_obj, &tint_color_obj, &tint2_color_obj)) {
    return nullptr;
  }
  Player* p = self->player_->get();
  if (!p) {
    throw Exception(PyExcType::kSessionPlayerNotFound);
  }
  std::string texture_name = Python::GetString(texture_name_obj);
  std::string tint_texture_name = Python::GetString(tint_texture_name_obj);
  std::vector<float> tint_color = Python::GetFloats(tint_color_obj);
  if (tint_color.size() != 3) {
    throw Exception("Expected 3 floats for tint-color.", PyExcType::kValue);
  }
  std::vector<float> tint2_color = Python::GetFloats(tint2_color_obj);
  if (tint2_color.size() != 3) {
    throw Exception("Expected 3 floats for tint-color.", PyExcType::kValue);
  }
  p->SetIcon(texture_name, tint_texture_name, tint_color, tint2_color);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PythonClassSessionPlayer::SetActivity(PythonClassSessionPlayer* self,
                                           PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  assert(g_base->InLogicThread());
  PyObject* activity_obj;
  static const char* kwlist[] = {"activity", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "O",
                                   const_cast<char**>(kwlist), &activity_obj)) {
    return nullptr;
  }
  Player* p = self->player_->get();
  if (!p) {
    throw Exception(PyExcType::kSessionPlayerNotFound);
  }
  HostActivity* a;
  if (activity_obj == Py_None) {
    a = nullptr;
  } else {
    a = SceneV1Python::GetPyHostActivity(activity_obj);
  }
  p->SetHostActivity(a);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PythonClassSessionPlayer::SetNode(PythonClassSessionPlayer* self,
                                       PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  assert(g_base->InLogicThread());
  PyObject* node_obj;
  static const char* kwlist[] = {"node", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "O",
                                   const_cast<char**>(kwlist), &node_obj)) {
    return nullptr;
  }
  Player* p = self->player_->get();
  if (!p) {
    throw Exception(PyExcType::kSessionPlayerNotFound);
  }
  Node* node;
  if (node_obj == Py_None) {
    node = nullptr;
  } else {
    node = SceneV1Python::GetPyNode(node_obj);
  }
  p->set_node(node);

  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PythonClassSessionPlayer::GetIcon(PythonClassSessionPlayer* self)
    -> PyObject* {
  BA_PYTHON_TRY;
  assert(g_base->InLogicThread());
  Player* p = self->player_->get();
  if (!p) {
    throw Exception(PyExcType::kSessionPlayerNotFound);
  }

  // Now kindly ask the activity to load/return an icon for us.
  PythonRef args(Py_BuildValue("(O)", p->BorrowPyRef()), PythonRef::kSteal);
  PythonRef results;
  {
    Python::ScopedCallLabel label("get_player_icon");
    results = g_scene_v1->python->objs()
                  .Get(SceneV1Python::ObjID::kGetPlayerIconCall)
                  .Call(args);
  }
  return results.NewRef();
  BA_PYTHON_CATCH;
}

auto PythonClassSessionPlayer::Dir(PythonClassSessionPlayer* self)
    -> PyObject* {
  BA_PYTHON_TRY;

  // Start with the standard python dir listing.
  PyObject* dir_list = Python::generic_dir(reinterpret_cast<PyObject*>(self));
  assert(PyList_Check(dir_list));

  // ..and add in our custom attr names.
  for (const char** name = extra_dir_attrs; *name != nullptr; name++) {
    PyList_Append(
        dir_list,
        PythonRef(PyUnicode_FromString(*name), PythonRef::kSteal).get());
  }
  PyList_Sort(dir_list);
  return dir_list;

  BA_PYTHON_CATCH;
}

bool PythonClassSessionPlayer::s_create_empty_ = false;
PyTypeObject PythonClassSessionPlayer::type_obj;
PyMethodDef PythonClassSessionPlayer::tp_methods[] = {
    {"getname", (PyCFunction)GetName, METH_VARARGS | METH_KEYWORDS,
     "getname(full: bool = False, icon: bool = True) -> str\n"
     "\n"
     "Returns the player's name. If ``icon`` is True, the long version of the\n"
     "name may include an icon."},
    {"setname", (PyCFunction)SetName, METH_VARARGS | METH_KEYWORDS,
     "setname(name: str, full_name: str | None = None, real: bool = True)\n"
     "  -> None\n"
     "\n"
     "Set the player's name to the provided string.\n"
     "A number will automatically be appended if the name is not unique from\n"
     "other players."},
    {"resetinput", (PyCFunction)ResetInput, METH_NOARGS,
     "resetinput() -> None\n"
     "\n"
     "Clears out the player's assigned input actions."},
    {"exists", (PyCFunction)Exists, METH_NOARGS,
     "exists() -> bool\n"
     "\n"
     "Return whether the underlying player is still in the game."},
    {"assigninput", (PyCFunction)AssignInputCall, METH_VARARGS | METH_KEYWORDS,
     "assigninput(type: bascenev1.InputType\n"
     " | tuple[bascenev1.InputType, ...], call: Callable) -> None\n"
     "\n"
     "Set the python callable to be run for one or more types of input."},
    {"remove_from_game", (PyCFunction)RemoveFromGame, METH_NOARGS,
     "remove_from_game() -> None\n"
     "\n"
     "Removes the player from the game."},
    {"get_v1_account_id", (PyCFunction)GetV1AccountID,
     METH_VARARGS | METH_KEYWORDS,
     "get_v1_account_id() -> str\n"
     "\n"
     "Return the V1 account id this player is signed in under, if\n"
     "there is one and it can be determined with relative certainty.\n"
     "Returns None otherwise. Note that this may require an active\n"
     "internet connection (especially for network-connected players)\n"
     "and may return None for a short while after a player initially\n"
     "joins (while verification occurs)."},
    {"setdata", (PyCFunction)SetData, METH_VARARGS | METH_KEYWORDS,
     "setdata(team: bascenev1.SessionTeam, character: str,\n"
     "  color: Sequence[float], highlight: Sequence[float]) -> None\n"
     "\n"
     "(internal)"},
    {"set_icon_info", (PyCFunction)SetIconInfo, METH_VARARGS | METH_KEYWORDS,
     "set_icon_info(texture: str, tint_texture: str,\n"
     "  tint_color: Sequence[float], tint2_color: Sequence[float]) -> None\n"
     "\n"
     "(internal)\n"
     "\n"
     ":meta private:"},
    {"setactivity", (PyCFunction)SetActivity, METH_VARARGS | METH_KEYWORDS,
     "setactivity(activity: bascenev1.Activity | None) -> None\n"
     "\n"
     "(internal)\n"
     "\n"
     ":meta private:"},
    {"setnode", (PyCFunction)SetNode, METH_VARARGS | METH_KEYWORDS,
     "setnode(node: bascenev1.Node | None) -> None\n"
     "\n"
     "(internal)\n"
     "\n"
     ":meta private:"},
    {"get_icon", (PyCFunction)GetIcon, METH_NOARGS,
     "get_icon() -> dict[str, Any]\n"
     "\n"
     "Return the character's icon (images, colors, etc contained\n"
     "in a dict."},
    {"get_icon_info", (PyCFunction)GetIconInfo, METH_NOARGS,
     "get_icon_info() -> dict[str, Any]\n"
     "\n"
     "(internal)\n"
     "\n"
     ":meta private:"},
    {"__dir__", (PyCFunction)Dir, METH_NOARGS,
     "Allows inclusion of our custom attrs in standard python dir()."},
    {nullptr}};

#pragma clang diagnostic pop

}  // namespace ballistica::scene_v1
