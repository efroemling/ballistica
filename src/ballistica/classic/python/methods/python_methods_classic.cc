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
#include "ballistica/shared/python/python_sys.h"

namespace ballistica::classic {

// Ignore signed bitwise warnings; python macros do it quite a bit.
#pragma clang diagnostic push
#pragma ide diagnostic ignored "hicpp-signed-bitwise"
#pragma ide diagnostic ignored "RedundantCast"

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
    change = Python::GetPyDouble(change_obj);
  }
  if (absolute_obj != Py_None) {
    have_absolute = true;
    absolute = Python::GetPyDouble(absolute_obj);
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
      ScreenMessage("invalid arg: " + std::string(arg));
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
  const char* inbox_count_text;
  const char* chest_0_appearance;
  const char* chest_1_appearance;
  const char* chest_2_appearance;
  const char* chest_3_appearance;
  double chest_0_unlock_time;
  double chest_1_unlock_time;
  double chest_2_unlock_time;
  double chest_3_unlock_time;
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
                                 "inbox_count_text",
                                 "gold_pass",
                                 "chest_0_appearance",
                                 "chest_1_appearance",
                                 "chest_2_appearance",
                                 "chest_3_appearance",
                                 "chest_0_unlock_time",
                                 "chest_1_unlock_time",
                                 "chest_2_unlock_time",
                                 "chest_3_unlock_time",
                                 "chest_0_ad_allow_time",
                                 "chest_1_ad_allow_time",
                                 "chest_2_ad_allow_time",
                                 "chest_3_ad_allow_time",
                                 nullptr};
  if (!PyArg_ParseTupleAndKeywords(
          args, keywds, "iisiisssspssssdddddddd", const_cast<char**>(kwlist),
          &tickets, &tokens, &league_type, &league_number, &league_rank,
          &achievements_percent_text, &level_text, &xp_text, &inbox_count_text,
          &gold_pass, &chest_0_appearance, &chest_1_appearance,
          &chest_2_appearance, &chest_3_appearance, &chest_0_unlock_time,
          &chest_1_unlock_time, &chest_2_unlock_time, &chest_3_unlock_time,
          &chest_0_ad_allow_time, &chest_1_ad_allow_time,
          &chest_2_ad_allow_time, &chest_3_ad_allow_time)) {
    return nullptr;
  }
  BA_PRECONDITION(g_base->InLogicThread());

  auto* appmode = ClassicAppMode::GetActiveOrThrow();

  // Pass these all along to the app-mode which will store them and forward
  // them to any current and future UIs.
  appmode->SetRootUITicketsMeterValue(tickets);
  appmode->SetRootUITokensMeterValue(tokens);
  appmode->SetRootUILeagueValues(league_type, league_number, league_rank);
  appmode->SetRootUIAchievementsPercentText(achievements_percent_text);
  appmode->SetRootUILevelText(level_text);
  appmode->SetRootUIXPText(xp_text);
  appmode->SetRootUIInboxCountText(inbox_count_text);
  appmode->SetRootUIGoldPass(gold_pass);
  appmode->SetRootUIChests(
      chest_0_appearance, chest_1_appearance, chest_2_appearance,
      chest_3_appearance, chest_0_unlock_time, chest_1_unlock_time,
      chest_2_unlock_time, chest_3_unlock_time, chest_0_ad_allow_time,
      chest_1_ad_allow_time, chest_2_ad_allow_time, chest_3_ad_allow_time);

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
    "      inbox_count_text: str,\n"
    "      gold_pass: bool,\n"
    "      chest_0_appearance: str,\n"
    "      chest_1_appearance: str,\n"
    "      chest_2_appearance: str,\n"
    "      chest_3_appearance: str,\n"
    "      chest_0_unlock_time: float,\n"
    "      chest_1_unlock_time: float,\n"
    "      chest_2_unlock_time: float,\n"
    "      chest_3_unlock_time: float,\n"
    "      chest_0_ad_allow_time: float,\n"
    "      chest_1_ad_allow_time: float,\n"
    "      chest_2_ad_allow_time: float,\n"
    "      chest_3_ad_allow_time: float,\n"
    ") -> None\n"
    "\n"
    "(internal)",
};

// ----------------- get_root_ui_account_league_vis_values ---------------------

static auto PyGetRootUIAccountLeagueVisValues(PyObject* self, PyObject* args,
                                              PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;

  BA_PRECONDITION(g_base->InLogicThread());

  auto* appmode = ClassicAppMode::GetActiveOrThrow();

  std::string league_type;
  int league_number;
  int league_rank;

  appmode->GetRootUIAccountLeagueVisValues(&league_type, &league_number,
                                           &league_rank);
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
     "}",
     "tp", league_type.c_str(),
     "num", league_number,
     "rank", league_rank);
  // clang-format on

  BA_PYTHON_CATCH;
}

static PyMethodDef PyGetRootUIAccountLeagueVisValuesDef = {
    "get_root_ui_account_league_vis_values",         // name
    (PyCFunction)PyGetRootUIAccountLeagueVisValues,  // method
    METH_NOARGS,                                     // flags

    "get_root_ui_account_league_vis_values() -> Any\n"
    "\n"
    "(internal)",
};

// ----------------- set_root_ui_account_league_vis_values ---------------------

static auto PySetRootUIAccountLeagueVisValues(PyObject* self, PyObject* args,
                                              PyObject* keywds) -> PyObject* {
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
  auto* league_type_obj = PyDict_GetItemString(vals_obj, "tp");
  if (league_type_obj == nullptr || !PyUnicode_Check(league_type_obj)) {
    throw Exception("Incorrect type for league-type arg", PyExcType::kType);
  }

  auto* league_number_obj = PyDict_GetItemString(vals_obj, "num");
  if (league_number_obj == nullptr || !PyLong_Check(league_number_obj)) {
    throw Exception("Incorrect type for league-number arg", PyExcType::kType);
  }

  auto* league_rank_obj = PyDict_GetItemString(vals_obj, "rank");
  if (league_rank_obj == nullptr || !PyLong_Check(league_rank_obj)) {
    throw Exception("Incorrect type for league-rank arg", PyExcType::kType);
  }
  appmode->SetRootUIAccountLeagueVisValues(PyUnicode_AsUTF8(league_type_obj),
                                           PyLong_AsLong(league_number_obj),
                                           PyLong_AsLong(league_rank_obj));
  Py_RETURN_NONE;

  BA_PYTHON_CATCH;
}

static PyMethodDef PySetRootUIAccountLeagueVisValuesDef = {
    "set_root_ui_account_league_vis_values",         // name
    (PyCFunction)PySetRootUIAccountLeagueVisValues,  // method
    METH_VARARGS | METH_KEYWORDS,                    // flags

    "set_root_ui_account_league_vis_values(vals: dict) -> None\n"
    "\n"
    "(internal)",
};

// --------------------- set_root_ui_have_live_values --------------------------

static auto PySetRootUIHaveLiveValues(PyObject* self, PyObject* args,
                                      PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;

  int have_live_values{};

  static const char* kwlist[] = {"have_live_values", nullptr};
  if (!PyArg_ParseTupleAndKeywords(
          args, keywds, "p", const_cast<char**>(kwlist), &have_live_values)) {
    return nullptr;
  }
  BA_PRECONDITION(g_base->InLogicThread());

  auto* appmode = ClassicAppMode::GetActiveOrThrow();
  appmode->SetRootUIHaveLiveValues(have_live_values);

  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PySetRootUIHaveLiveValuesDef = {
    "set_root_ui_have_live_values",          // name
    (PyCFunction)PySetRootUIHaveLiveValues,  // method
    METH_VARARGS | METH_KEYWORDS,            // flags

    "set_root_ui_have_live_values(have_live_values: bool) -> None\n"
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
      PyGetRootUIAccountLeagueVisValuesDef,
      PySetRootUIAccountLeagueVisValuesDef,
      PySetRootUIHaveLiveValuesDef,
  };
}

#pragma clang diagnostic pop

}  // namespace ballistica::classic
