// Released under the MIT License. See LICENSE for details.

#include "ballistica/classic/python/methods/python_methods_classic.h"

#include "ballistica/base/graphics/graphics.h"
#include "ballistica/base/graphics/support/camera.h"
#include "ballistica/base/logic/logic.h"
#include "ballistica/classic/support/stress_test.h"
#include "ballistica/scene_v1/support/scene_v1_app_mode.h"
#include "ballistica/shared/foundation/event_loop.h"
#include "ballistica/shared/python/python.h"
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
    auto* appmode = scene_v1::SceneV1AppMode::GetSingleton();

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
    auto* appmode = scene_v1::SceneV1AppMode::GetSingleton();
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
    auto* appmode = scene_v1::SceneV1AppMode::GetSingleton();
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
  if (!PyArg_ParseTuple(args, "pi", &enable, &player_count)) {
    return nullptr;
  }
  g_base->logic->event_loop()->PushCall([enable, player_count] {
    g_classic->stress_test()->Set(enable, player_count);
  });
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PySetStressTestingDef = {
    "set_stress_testing",  // name
    PySetStressTesting,    // method
    METH_VARARGS,          // flags

    "set_stress_testing(testing: bool, player_count: int) -> None\n"
    "\n"
    "(internal)",
};

// -----------------------------------------------------------------------------

auto PythonMethodsClassic::GetMethods() -> std::vector<PyMethodDef> {
  return {
      PyValueTestDef,
      PySetStressTestingDef,
  };
}

#pragma clang diagnostic pop

}  // namespace ballistica::classic
