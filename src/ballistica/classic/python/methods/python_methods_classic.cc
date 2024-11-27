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
#include "ballistica/shared/python/python.h"
#include "ballistica/shared/python/python_command.h"
#include "ballistica/shared/python/python_sys.h"
#include "ballistica/ui_v1/widget/root_widget.h"

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

// -------------------------- set_root_ui_values -------------------------------

static auto PySetRootUIValues(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;

  const char* tickets_text;
  const char* tokens_text;
  const char* league_rank_text;
  static const char* kwlist[] = {"tickets_text", "tokens_text",
                                 "league_rank_text", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "sss",
                                   const_cast<char**>(kwlist), &tickets_text,
                                   &tokens_text, &league_rank_text)) {
    return nullptr;
  }
  BA_PRECONDITION(g_base->InLogicThread());

  auto* appmode = ClassicAppMode::GetActiveOrThrow();

  appmode->SetRootUITicketsMeterText(tickets_text);
  appmode->SetRootUITokensMeterText(tokens_text);
  appmode->SetRootUILeagueRankText(league_rank_text);

  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PySetRootUIValuesDef = {
    "set_root_ui_values",            // name
    (PyCFunction)PySetRootUIValues,  // method
    METH_VARARGS | METH_KEYWORDS,    // flags

    "set_root_ui_values(tickets_text: str,\n"
    "      tokens_text: str,\n"
    "      league_rank_text: str,\n"
    ") -> None\n"
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
      PySetRootUIValuesDef,
  };
}

#pragma clang diagnostic pop

}  // namespace ballistica::classic
