// Released under the MIT License. See LICENSE for details.

#include "ballistica/classic/python/methods/python_methods_classic.h"

#include <algorithm>
#include <string>
#include <vector>

#include "ballistica/base/graphics/graphics.h"
#include "ballistica/base/graphics/support/camera.h"
#include "ballistica/base/input/input.h"
#include "ballistica/base/logic/logic.h"
#include "ballistica/classic/support/classic_app_mode.h"
#include "ballistica/classic/support/stress_test.h"
#include "ballistica/shared/foundation/event_loop.h"
#include "ballistica/shared/foundation/exception.h"
#include "ballistica/shared/python/python.h"
#include "ballistica/shared/python/python_command.h"
#include "ballistica/shared/python/python_macros.h"

namespace ballistica::classic {

// -------------------------------- value_test ---------------------------------

static auto PyValueTest(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  const char* arg;
  double change = 0.0f;
  double absolute = 0.0f;
  bool have_change = false;
  bool have_absolute = false;
  PyObject* change_obj = Py_None;
  PyObject* absolute_obj = Py_None;
  static const char* kwlist[] = {"arg", "change", "absolute", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "s|OO",
                                   const_cast<char**>(kwlist), &arg,
                                   &change_obj, &absolute_obj)) {
    return nullptr;
  }
  if (change_obj != Py_None) {
    if (absolute_obj != Py_None) {
      throw Exception("Can't provide both a change and absolute");
    }
    have_change = true;
    change = Python::GetDouble(change_obj);
  }
  if (absolute_obj != Py_None) {
    have_absolute = true;
    absolute = Python::GetDouble(absolute_obj);
  }
  double return_val = 0.0f;
  if (!strcmp(arg, "bufferTime")) {
    auto* appmode = ClassicAppMode::GetSingleton();

    if (have_change) {
      appmode->set_buffer_time(appmode->buffer_time()
                               + static_cast<int>(change));
    }
    if (have_absolute) {
      appmode->set_buffer_time(static_cast<int>(absolute));
    }
    appmode->set_buffer_time(std::max(0, appmode->buffer_time()));
    return_val = appmode->buffer_time();
  } else if (!strcmp(arg, "delaySampling")) {
    auto* appmode = ClassicAppMode::GetSingleton();
    if (have_change) {
      appmode->set_delay_bucket_samples(appmode->delay_bucket_samples()
                                        + static_cast<int>(change));
    }
    if (have_absolute) {
      appmode->set_buffer_time(static_cast<int>(absolute));
    }
    appmode->set_delay_bucket_samples(
        std::max(1, appmode->delay_bucket_samples()));
    return_val = appmode->delay_bucket_samples();
  } else if (!strcmp(arg, "dynamicsSyncTime")) {
    auto* appmode = ClassicAppMode::GetSingleton();
    if (have_change) {
      appmode->set_dynamics_sync_time(appmode->dynamics_sync_time()
                                      + static_cast<int>(change));
    }
    if (have_absolute) {
      appmode->set_dynamics_sync_time(static_cast<int>(absolute));
    }
    appmode->set_dynamics_sync_time(std::max(0, appmode->dynamics_sync_time()));
    return_val = appmode->dynamics_sync_time();
  } else if (!strcmp(arg, "showNetInfo")) {
    if (have_change && change > 0.5f) {
      g_base->graphics->set_show_net_info(true);
    }
    if (have_change && change < -0.5f) {
      g_base->graphics->set_show_net_info(false);
    }
    if (have_absolute) {
      g_base->graphics->set_show_net_info(static_cast<bool>(absolute));
    }
    return_val = g_base->graphics->show_net_info();
  } else if (!strcmp(arg, "allowCameraMovement")) {
    base::Camera* camera = g_base->graphics->camera();
    if (camera) {
      if (have_change && change > 0.5f) {
        camera->set_lock_panning(false);
      }
      if (have_change && change < -0.5f) {
        camera->set_lock_panning(true);
      }
      if (have_absolute) {
        camera->set_lock_panning(!static_cast<bool>(absolute));
      }
      return_val = !camera->lock_panning();
    }
  } else if (!strcmp(arg, "cameraPanSpeedScale")) {
    base::Camera* camera = g_base->graphics->camera();
    if (camera) {
      double val = camera->pan_speed_scale();
      if (have_change) {
        camera->set_pan_speed_scale(static_cast<float>(val + change));
      }
      if (have_absolute) {
        camera->set_pan_speed_scale(static_cast<float>(absolute));
      }
      if (camera->pan_speed_scale() < 0) {
        camera->set_pan_speed_scale(0);
      }
      return_val = camera->pan_speed_scale();
    }
  } else {
    auto handled = g_base->graphics->ValueTest(
        arg, have_absolute ? &absolute : nullptr,
        have_change ? &change : nullptr, &return_val);
    if (!handled) {
      g_base->ScreenMessage("invalid arg: " + std::string(arg));
    }
  }

  return PyFloat_FromDouble(return_val);

  BA_PYTHON_CATCH;
}

static PyMethodDef PyValueTestDef = {
    "value_test",                  // name
    (PyCFunction)PyValueTest,      // method
    METH_VARARGS | METH_KEYWORDS,  // flags

    "value_test(arg: str, change: float | None = None,\n"
    "  absolute: float | None = None) -> float\n"
    "\n"
    "(internal)",
};

// -------------------------- set_stress_testing -------------------------------

static auto PySetStressTesting(PyObject* self, PyObject* args) -> PyObject* {
  BA_PYTHON_TRY;
  int enable;
  int player_count;
  int attract_mode;
  if (!PyArg_ParseTuple(args, "pip", &enable, &player_count, &attract_mode)) {
    return nullptr;
  }
  g_base->logic->event_loop()->PushCall([enable, player_count, attract_mode] {
    g_classic->stress_test()->Set(enable, player_count, attract_mode);
    g_base->input->set_attract_mode(enable && attract_mode);
  });
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PySetStressTestingDef = {
    "set_stress_testing",  // name
    PySetStressTesting,    // method
    METH_VARARGS,          // flags

    "set_stress_testing(testing: bool,\n"
    "                        player_count: int,\n"
    "                        attract_mode: bool) -> None\n"
    "\n"
    "(internal)",
};

// --------------- classic_app_mode_handle_app_intent_exec ---------------------

static auto PyClassicAppModeHandleAppIntentExec(PyObject* self, PyObject* args,
                                                PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  const char* command;
  static const char* kwlist[] = {"command", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "s",
                                   const_cast<char**>(kwlist), &command)) {
    return nullptr;
  }
  auto* appmode = ClassicAppMode::GetActiveOrThrow();

  // Run the command.
  if (g_core->core_config().exec_command.has_value()) {
    bool success = PythonCommand(*g_core->core_config().exec_command,
                                 BA_BUILD_COMMAND_FILENAME)
                       .Exec(true, nullptr, nullptr);
    if (!success) {
      // TODO(ericf): what should we do in this case?
      //  Obviously if we add return/success values for intents we should set
      //  that here.
    }
  }
  //  If the stuff we just ran didn't result in a session, create a default
  //  one.
  if (!appmode->GetForegroundSession()) {
    appmode->RunMainMenu();
  }
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyClassicAppModeHandleAppIntentExecDef = {
    "classic_app_mode_handle_app_intent_exec",         // name
    (PyCFunction)PyClassicAppModeHandleAppIntentExec,  // method
    METH_VARARGS | METH_KEYWORDS,                      // flags

    "classic_app_mode_handle_app_intent_exec(command: str) -> None\n"
    "\n"
    "(internal)",
};

// -------------- classic_app_mode_handle_app_intent_default ------------------

static auto PyClassicAppModeHandleAppIntentDefault(PyObject* self)
    -> PyObject* {
  BA_PYTHON_TRY;
  BA_PRECONDITION(g_base->InLogicThread());
  auto* appmode = ClassicAppMode::GetActiveOrThrow();
  appmode->RunMainMenu();
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyClassicAppModeHandleAppIntentDefaultDef = {
    "classic_app_mode_handle_app_intent_default",         // name
    (PyCFunction)PyClassicAppModeHandleAppIntentDefault,  // method
    METH_NOARGS,                                          // flags

    "classic_app_mode_handle_app_intent_default() -> None\n"
    "\n"
    "(internal)\n",
};

// ------------------------ classic_app_mode_activate --------------------------

static auto PyClassicAppModeActivate(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;
  BA_PRECONDITION(g_base->InLogicThread());
  g_base->set_app_mode(ClassicAppMode::GetSingleton());
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyClassicAppModeActivateDef = {
    "classic_app_mode_activate",            // name
    (PyCFunction)PyClassicAppModeActivate,  // method
    METH_NOARGS,                            // flags

    "classic_app_mode_activate() -> None\n"
    "\n"
    "(internal)\n",
};

// ---------------------- classic_app_mode_deactivate --------------------------

static auto PyClassicAppModeDeactivate(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;
  BA_PRECONDITION(g_base->InLogicThread());
  // Currently doing nothing.
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyClassicAppModeDeactivateDef = {
    "classic_app_mode_deactivate",            // name
    (PyCFunction)PyClassicAppModeDeactivate,  // method
    METH_NOARGS,                              // flags

    "classic_app_mode_deactivate() -> None\n"
    "\n"
    "(internal)\n",
};

// --------------------- set_have_live_account_values --------------------------

static auto PySetHaveLiveAccountValues(PyObject* self, PyObject* args,
                                       PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;

  int have_live_values{};

  static const char* kwlist[] = {"have", nullptr};
  if (!PyArg_ParseTupleAndKeywords(
          args, keywds, "p", const_cast<char**>(kwlist), &have_live_values)) {
    return nullptr;
  }
  BA_PRECONDITION(g_base->InLogicThread());

  auto* appmode = ClassicAppMode::GetActiveOrThrow();
  appmode->SetHaveLiveAccountValues(have_live_values);

  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PySetHaveLiveAccountValuesDef = {
    "set_have_live_account_values",           // name
    (PyCFunction)PySetHaveLiveAccountValues,  // method
    METH_VARARGS | METH_KEYWORDS,             // flags

    "set_have_live_account_values(have: bool) -> None\n"
    "\n"
    "Inform the native layer whether we are being fed with live account\n"
    "values from the server.",
};

// ---------------------- set_root_ui_account_values ---------------------------

static auto PySetRootUIAccountValues(PyObject* self, PyObject* args,
                                     PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;

  int tickets;
  int tokens;
  int league_rank;
  int league_number;
  const char* league_type;
  const char* achievements_percent_text;
  const char* level_text;
  const char* xp_text;
  int inbox_count;
  int inbox_count_is_max;
  const char* chest_0_appearance;
  const char* chest_1_appearance;
  const char* chest_2_appearance;
  const char* chest_3_appearance;
  const char* inbox_announce_text;
  double chest_0_create_time;
  double chest_1_create_time;
  double chest_2_create_time;
  double chest_3_create_time;
  double chest_0_unlock_time;
  double chest_1_unlock_time;
  double chest_2_unlock_time;
  double chest_3_unlock_time;
  int chest_0_unlock_tokens;
  int chest_1_unlock_tokens;
  int chest_2_unlock_tokens;
  int chest_3_unlock_tokens;
  double chest_0_ad_allow_time;
  double chest_1_ad_allow_time;
  double chest_2_ad_allow_time;
  double chest_3_ad_allow_time;
  int gold_pass{};

  static const char* kwlist[] = {"tickets",
                                 "tokens",
                                 "league_type",
                                 "league_number",
                                 "league_rank",
                                 "achievements_percent_text",
                                 "level_text",
                                 "xp_text",
                                 "inbox_count",
                                 "inbox_count_is_max",
                                 "inbox_announce_text",
                                 "gold_pass",
                                 "chest_0_appearance",
                                 "chest_1_appearance",
                                 "chest_2_appearance",
                                 "chest_3_appearance",
                                 "chest_0_create_time",
                                 "chest_1_create_time",
                                 "chest_2_create_time",
                                 "chest_3_create_time",
                                 "chest_0_unlock_time",
                                 "chest_1_unlock_time",
                                 "chest_2_unlock_time",
                                 "chest_3_unlock_time",
                                 "chest_0_unlock_tokens",
                                 "chest_1_unlock_tokens",
                                 "chest_2_unlock_tokens",
                                 "chest_3_unlock_tokens",
                                 "chest_0_ad_allow_time",
                                 "chest_1_ad_allow_time",
                                 "chest_2_ad_allow_time",
                                 "chest_3_ad_allow_time",
                                 nullptr};
  if (!PyArg_ParseTupleAndKeywords(
          args, keywds, "iisiisssipspssssddddddddiiiidddd",
          const_cast<char**>(kwlist), &tickets, &tokens, &league_type,
          &league_number, &league_rank, &achievements_percent_text, &level_text,
          &xp_text, &inbox_count, &inbox_count_is_max, &inbox_announce_text,
          &gold_pass, &chest_0_appearance, &chest_1_appearance,
          &chest_2_appearance, &chest_3_appearance, &chest_0_create_time,
          &chest_1_create_time, &chest_2_create_time, &chest_3_create_time,
          &chest_0_unlock_time, &chest_1_unlock_time, &chest_2_unlock_time,
          &chest_3_unlock_time, &chest_0_unlock_tokens, &chest_1_unlock_tokens,
          &chest_2_unlock_tokens, &chest_3_unlock_tokens,
          &chest_0_ad_allow_time, &chest_1_ad_allow_time,
          &chest_2_ad_allow_time, &chest_3_ad_allow_time)) {
    return nullptr;
  }
  BA_PRECONDITION(g_base->InLogicThread());

  auto* appmode = ClassicAppMode::GetActiveOrThrow();

  // Pass these all along to the app-mode which will store them and forward
  // them to any current and future UI instances.
  appmode->SetRootUITicketsMeterValue(tickets);
  appmode->SetRootUITokensMeterValue(tokens);
  appmode->SetRootUILeagueValues(league_type, league_number, league_rank);
  appmode->SetRootUIAchievementsPercentText(achievements_percent_text);
  appmode->SetRootUILevelText(level_text);
  appmode->SetRootUIXPText(xp_text);
  appmode->SetRootUIInboxState(inbox_count, inbox_count_is_max,
                               inbox_announce_text);
  appmode->SetRootUIGoldPass(gold_pass);
  appmode->SetRootUIChests(
      chest_0_appearance, chest_1_appearance, chest_2_appearance,
      chest_3_appearance, chest_0_create_time, chest_1_create_time,
      chest_2_create_time, chest_3_create_time, chest_0_unlock_time,
      chest_1_unlock_time, chest_2_unlock_time, chest_3_unlock_time,
      chest_0_unlock_tokens, chest_1_unlock_tokens, chest_2_unlock_tokens,
      chest_3_unlock_tokens, chest_0_ad_allow_time, chest_1_ad_allow_time,
      chest_2_ad_allow_time, chest_3_ad_allow_time);

  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PySetRootUIAccountValuesDef = {
    "set_root_ui_account_values",           // name
    (PyCFunction)PySetRootUIAccountValues,  // method
    METH_VARARGS | METH_KEYWORDS,           // flags

    "set_root_ui_account_values(*,\n"
    "      tickets: int,\n"
    "      tokens: int,\n"
    "      league_type: str,\n"
    "      league_number: int,\n"
    "      league_rank: int,\n"
    "      achievements_percent_text: str,\n"
    "      level_text: str,\n"
    "      xp_text: str,\n"
    "      inbox_count: int,\n"
    "      inbox_count_is_max: bool,\n"
    "      inbox_announce_text: str,\n"
    "      gold_pass: bool,\n"
    "      chest_0_appearance: str,\n"
    "      chest_1_appearance: str,\n"
    "      chest_2_appearance: str,\n"
    "      chest_3_appearance: str,\n"
    "      chest_0_create_time: float,\n"
    "      chest_1_create_time: float,\n"
    "      chest_2_create_time: float,\n"
    "      chest_3_create_time: float,\n"
    "      chest_0_unlock_time: float,\n"
    "      chest_1_unlock_time: float,\n"
    "      chest_2_unlock_time: float,\n"
    "      chest_3_unlock_time: float,\n"
    "      chest_0_unlock_tokens: int,\n"
    "      chest_1_unlock_tokens: int,\n"
    "      chest_2_unlock_tokens: int,\n"
    "      chest_3_unlock_tokens: int,\n"
    "      chest_0_ad_allow_time: float,\n"
    "      chest_1_ad_allow_time: float,\n"
    "      chest_2_ad_allow_time: float,\n"
    "      chest_3_ad_allow_time: float,\n"
    ") -> None\n"
    "\n"
    "Pass values to the native layer for use in the root UI or elsewhere.",
};

// ------------------- animate_root_ui_chest_unlock_time -----------------------

static auto PyAnimateRootUIChestUnlockTime(PyObject* self, PyObject* args,
                                           PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;

  const char* chestid;
  double duration;
  double startvalue;
  double endvalue;

  static const char* kwlist[] = {"chestid", "duration", "startvalue",
                                 "endvalue", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "sddd",
                                   const_cast<char**>(kwlist), &chestid,
                                   &duration, &startvalue, &endvalue)) {
    return nullptr;
  }
  BA_PRECONDITION(g_base->InLogicThread());

  auto* appmode = ClassicAppMode::GetActiveOrThrow();

  appmode->AnimateRootUIChestUnlockTime(chestid, duration, startvalue,
                                        endvalue);

  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyAnimateRootUIChestUnlockTimeDef = {
    "animate_root_ui_chest_unlock_time",          // name
    (PyCFunction)PyAnimateRootUIChestUnlockTime,  // method
    METH_VARARGS | METH_KEYWORDS,                 // flags

    "animate_root_ui_chest_unlock_time(*,\n"
    "      chestid: str,\n"
    "      duration: float,\n"
    "      startvalue: float,\n"
    "      endvalue: float,\n"
    ") -> None\n"
    "\n"
    "Animate the unlock time on a chest.",
};

// ------------------------ animate_root_ui_tickets ----------------------------

static auto PyAnimateRootUITickets(PyObject* self, PyObject* args,
                                   PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;

  double duration;
  int startvalue;
  int endvalue;

  static const char* kwlist[] = {"duration", "startvalue", "endvalue", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "dii",
                                   const_cast<char**>(kwlist), &duration,
                                   &startvalue, &endvalue)) {
    return nullptr;
  }
  BA_PRECONDITION(g_base->InLogicThread());

  auto* appmode = ClassicAppMode::GetActiveOrThrow();

  appmode->AnimateRootUITickets(duration, startvalue, endvalue);

  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyAnimateRootUITicketsDef = {
    "animate_root_ui_tickets",            // name
    (PyCFunction)PyAnimateRootUITickets,  // method
    METH_VARARGS | METH_KEYWORDS,         // flags

    "animate_root_ui_tickets(*,\n"
    "      duration: float,\n"
    "      startvalue: int,\n"
    "      endvalue: int,\n"
    ") -> None\n"
    "\n"
    "Animate the displayed tickets value.",
};

// ------------------------ animate_root_ui_tokens -----------------------------

static auto PyAnimateRootUITokens(PyObject* self, PyObject* args,
                                  PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;

  double duration;
  int startvalue;
  int endvalue;

  static const char* kwlist[] = {"duration", "startvalue", "endvalue", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "dii",
                                   const_cast<char**>(kwlist), &duration,
                                   &startvalue, &endvalue)) {
    return nullptr;
  }
  BA_PRECONDITION(g_base->InLogicThread());

  auto* appmode = ClassicAppMode::GetActiveOrThrow();

  appmode->AnimateRootUITokens(duration, startvalue, endvalue);

  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyAnimateRootUITokensDef = {
    "animate_root_ui_tokens",            // name
    (PyCFunction)PyAnimateRootUITokens,  // method
    METH_VARARGS | METH_KEYWORDS,        // flags

    "animate_root_ui_tokens(*,\n"
    "      duration: float,\n"
    "      startvalue: int,\n"
    "      endvalue: int,\n"
    ") -> None\n"
    "\n"
    "Animate the displayed tokens value.",
};

// --------------------------- get_account_state -------------------------------

static auto PyGetAccountState(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;

  BA_PRECONDITION(g_base->InLogicThread());

  auto* appmode = ClassicAppMode::GetActiveOrThrow();

  std::string league_type;
  int league_number;
  int league_rank;
  int inbox_count;
  bool inbox_count_is_max;

  appmode->GetAccountState(&league_type, &league_number, &league_rank,
                           &inbox_count, &inbox_count_is_max);
  // If values are unset, return None.
  if (league_type.empty()) {
    Py_RETURN_NONE;
  }

  // clang-format off

  return Py_BuildValue(
     "{"
     "ss"  // league type
     "si"  // league number
     "si"  // league rank
     "si"  // inbox count
     "sO"  // inbox count is max
     "}",
     "tp", league_type.c_str(),
     "num", league_number,
     "rank", league_rank,
     "c", inbox_count,
     "m", inbox_count_is_max ? Py_True : Py_False);

  // clang-format on

  BA_PYTHON_CATCH;
}

static PyMethodDef PyGetAccountStateDef = {
    "get_account_state",             // name
    (PyCFunction)PyGetAccountState,  // method
    METH_NOARGS,                     // flags

    "get_account_state() -> Any\n"
    "\n"
    "(internal)",
};

// ---------------------------- set_account_state ------------------------------

static auto PySetAccountState(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;

  BA_PRECONDITION(g_base->InLogicThread());

  static const char* kwlist[] = {"vals", nullptr};

  PyObject* vals_obj;

  if (!PyArg_ParseTupleAndKeywords(args, keywds, "O",
                                   const_cast<char**>(kwlist), &vals_obj)) {
    return nullptr;
  }

  auto* appmode = ClassicAppMode::GetActiveOrThrow();

  BA_PRECONDITION(PyDict_Check(vals_obj));

  auto league_type{Python::GetString(PyDict_GetItemString(vals_obj, "tp"))};
  auto league_number{Python::GetInt(PyDict_GetItemString(vals_obj, "num"))};
  auto league_rank{Python::GetInt(PyDict_GetItemString(vals_obj, "rank"))};

  int inbox_count;
  if (auto* inbox_count_obj = PyDict_GetItemString(vals_obj, "c")) {
    inbox_count = Python::GetInt(inbox_count_obj);
  } else {
    inbox_count = -1;  // Special case for 'unset'.
  }
  bool inbox_count_is_max;
  if (auto* inbox_count_is_max_obj = PyDict_GetItemString(vals_obj, "m")) {
    inbox_count_is_max = Python::GetBool(inbox_count_is_max_obj);
  } else {
    inbox_count_is_max = false;
  }

  appmode->SetAccountState(league_type, league_number, league_rank, inbox_count,
                           inbox_count_is_max);
  Py_RETURN_NONE;

  BA_PYTHON_CATCH;
}

static PyMethodDef PySetAccountStateDef = {
    "set_account_state",             // name
    (PyCFunction)PySetAccountState,  // method
    METH_VARARGS | METH_KEYWORDS,    // flags

    "set_account_state(vals: dict) -> None\n"
    "\n"
    "(internal)",
};

// -----------------------------------------------------------------------------

auto PythonMethodsClassic::GetMethods() -> std::vector<PyMethodDef> {
  return {
      PyValueTestDef,
      PySetStressTestingDef,
      PyClassicAppModeHandleAppIntentExecDef,
      PyClassicAppModeHandleAppIntentDefaultDef,
      PyClassicAppModeActivateDef,
      PyClassicAppModeDeactivateDef,
      PySetRootUIAccountValuesDef,
      PyAnimateRootUIChestUnlockTimeDef,
      PyAnimateRootUITicketsDef,
      PyAnimateRootUITokensDef,
      PyGetAccountStateDef,
      PySetAccountStateDef,
      PySetHaveLiveAccountValuesDef,
  };
}

}  // namespace ballistica::classic
