// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/python/methods/python_methods_base_2.h"

#include <string>
#include <vector>

#include "ballistica/base/app_adapter/app_adapter.h"
#include "ballistica/base/assets/assets.h"
#include "ballistica/base/graphics/graphics.h"
#include "ballistica/base/graphics/support/camera.h"
#include "ballistica/base/graphics/support/screen_messages.h"
#include "ballistica/base/graphics/text/text_graphics.h"
#include "ballistica/base/platform/base_platform.h"
#include "ballistica/base/python/base_python.h"
#include "ballistica/base/python/support/python_context_call.h"
#include "ballistica/base/ui/ui.h"
#include "ballistica/core/core.h"
#include "ballistica/core/platform/core_platform.h"
#include "ballistica/shared/foundation/macros.h"
#include "ballistica/shared/generic/utils.h"
#include "ballistica/shared/python/python.h"
#include "ballistica/shared/python/python_sys.h"

namespace ballistica::base {

// Ignore signed bitwise stuff; python macros do it quite a bit.
#pragma clang diagnostic push
#pragma ide diagnostic ignored "hicpp-signed-bitwise"

// ------------------------------- open_url ------------------------------------

static auto PyOpenURL(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  const char* address{};
  int force_fallback{};
  static const char* kwlist[] = {"address", "force_fallback", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "s|p",
                                   const_cast<char**>(kwlist), &address,
                                   &force_fallback)) {
    return nullptr;
  }
  if (force_fallback) {
    g_base->ui->ShowURL(address);
  } else {
    g_base->platform->OpenURL(address);
  }
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyOpenURLDef = {
    "open_url",                    // name
    (PyCFunction)PyOpenURL,        // method
    METH_VARARGS | METH_KEYWORDS,  // flags

    "open_url(address: str, force_fallback: bool = False) -> None\n"
    "\n"
    "Open the provided URL.\n"
    "\n"
    "Category: **General Utility Functions**\n"
    "\n"
    "Attempts to open the provided url in a web-browser. If that is not\n"
    "possible (or force_fallback is True), instead displays the url as\n"
    "a string and/or qrcode."};

// --------------------- overlay_web_browser_is_supported ----------------------

static auto PyOverlayWebBrowserIsSupported(PyObject* self, PyObject* args,
                                           PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  if (g_base->platform->OverlayWebBrowserIsSupported()) {
    Py_RETURN_TRUE;
  } else {
    Py_RETURN_FALSE;
  }
  BA_PYTHON_CATCH;
}

static PyMethodDef PyOverlayWebBrowserIsSupportedDef = {
    "overlay_web_browser_is_supported",           // name
    (PyCFunction)PyOverlayWebBrowserIsSupported,  // method
    METH_NOARGS,                                  // flags

    "overlay_web_browser_is_supported() -> bool\n"
    "\n"
    "Return whether an overlay web browser is supported here.\n"
    "\n"
    "Category: **General Utility Functions**\n"
    "\n"
    "An overlay web browser is a small dialog that pops up over the top\n"
    "of the main engine window. It can be used for performing simple\n"
    "tasks such as sign-ins."};

// --------------------- overlay_web_browser_open_url --------------------------

static auto PyOverlayWebBrowserOpenURL(PyObject* self, PyObject* args,
                                       PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  const char* address{};
  static const char* kwlist[] = {"address", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "s",
                                   const_cast<char**>(kwlist), &address)) {
    return nullptr;
  }
  g_base->platform->OverlayWebBrowserOpenURL(address);

  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyOverlayWebBrowserOpenURLDef = {
    "overlay_web_browser_open_url",           // name
    (PyCFunction)PyOverlayWebBrowserOpenURL,  // method
    METH_VARARGS | METH_KEYWORDS,             // flags

    "overlay_web_browser_open_url(address: str) -> None\n"
    "\n"
    "Open the provided URL in an overlayw web browser.\n"
    "\n"
    "Category: **General Utility Functions**\n"
    "\n"
    "An overlay web browser is a small dialog that pops up over the top\n"
    "of the main engine window. It can be used for performing simple\n"
    "tasks such as sign-ins."};

// --------------------- overlay_web_browser_is_open ----------------------

static auto PyOverlayWebBrowserIsOpen(PyObject* self, PyObject* args,
                                      PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  if (g_base->platform->OverlayWebBrowserIsOpen()) {
    Py_RETURN_TRUE;
  } else {
    Py_RETURN_FALSE;
  }
  BA_PYTHON_CATCH;
}

static PyMethodDef PyOverlayWebBrowserIsOpenDef = {
    "overlay_web_browser_is_open",           // name
    (PyCFunction)PyOverlayWebBrowserIsOpen,  // method
    METH_NOARGS,                             // flags

    "overlay_web_browser_is_open() -> bool\n"
    "\n"
    "Return whether an overlay web browser is open currently.\n"
    "\n"
    "Category: **General Utility Functions**"};

// ------------------------ overlay_web_browser_close --------------------------

static auto PyOverlayWebBrowserClose(PyObject* self, PyObject* args,
                                     PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  g_base->platform->OverlayWebBrowserClose();
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyOverlayWebBrowserCloseDef = {
    "overlay_web_browser_close",            // name
    (PyCFunction)PyOverlayWebBrowserClose,  // method
    METH_NOARGS,                            // flags

    "overlay_web_browser_close() -> bool\n"
    "\n"
    "Close any open overlay web browser.\n"
    "\n"
    "Category: **General Utility Functions**\n"};
// ---------------------------- screenmessage ----------------------------------

static auto PyScreenMessage(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  PyObject* color_obj = Py_None;
  PyObject* message_obj;
  int log{};
  static const char* kwlist[] = {"message", "color", "log", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "O|Op",
                                   const_cast<char**>(kwlist), &message_obj,
                                   &color_obj, &log)) {
    return nullptr;
  }

  std::string message_str = g_base->python->GetPyLString(message_obj);
  Vector3f color{1, 1, 1};
  if (color_obj != Py_None) {
    color = BasePython::GetPyVector3f(color_obj);
  }
  if (log) {
    g_core->Log(LogName::kBa, LogLevel::kInfo, message_str);
  }

  // This version simply displays it locally.
  g_base->graphics->screenmessages->AddScreenMessage(message_str, color);

  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyScreenMessageDef = {
    "screenmessage",               // name
    (PyCFunction)PyScreenMessage,  // method
    METH_VARARGS | METH_KEYWORDS,  // flags

    "screenmessage(message: str | babase.Lstr,\n"
    "  color: Sequence[float] | None = None,\n"
    "  log: bool = False)\n"
    " -> None\n"
    "\n"
    "Print a message to the local client's screen, in a given color.\n"
    "\n"
    "Category: **General Utility Functions**\n"
    "\n"
    "Note that this version of the function is purely for local display.\n"
    "To broadcast screen messages in network play, look for methods such as\n"
    "broadcastmessage() provided by the scene-version packages.",
};

// -------------------------- get_camera_position ------------------------------

static auto PyGetCameraPosition(PyObject* self, PyObject* args,
                                PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  float x = 0.0f;
  float y = 0.0f;
  float z = 0.0f;
  Camera* cam = g_base->graphics->camera();
  cam->get_position(&x, &y, &z);
  return Py_BuildValue("(fff)", x, y, z);
  BA_PYTHON_CATCH;
}

static PyMethodDef PyGetCameraPositionDef = {
    "get_camera_position",             // name
    (PyCFunction)PyGetCameraPosition,  // method
    METH_VARARGS | METH_KEYWORDS,      // flags

    "get_camera_position() -> tuple[float, ...]\n"
    "\n"
    "(internal)\n"
    "\n"
    "WARNING: these camera controls will not apply to network clients\n"
    "and may behave unpredictably in other ways. Use them only for\n"
    "tinkering.",
};

// --------------------------- get_camera_target -------------------------------

static auto PyGetCameraTarget(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  float x = 0.0f;
  float y = 0.0f;
  float z = 0.0f;
  Camera* cam = g_base->graphics->camera();
  cam->target_smoothed(&x, &y, &z);
  return Py_BuildValue("(fff)", x, y, z);
  BA_PYTHON_CATCH;
}

static PyMethodDef PyGetCameraTargetDef = {
    "get_camera_target",             // name
    (PyCFunction)PyGetCameraTarget,  // method
    METH_VARARGS | METH_KEYWORDS,    // flags

    "get_camera_target() -> tuple[float, ...]\n"
    "\n"
    "(internal)\n"
    "\n"
    "WARNING: these camera controls will not apply to network clients\n"
    "and may behave unpredictably in other ways. Use them only for\n"
    "tinkering.",
};

// --------------------------- set_camera_position -----------------------------

static auto PySetCameraPosition(PyObject* self, PyObject* args,
                                PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  float x = 0.0f;
  float y = 0.0f;
  float z = 0.0f;
  static const char* kwlist[] = {"x", "y", "z", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "fff",
                                   const_cast<char**>(kwlist), &x, &y, &z)) {
    return nullptr;
  }
  assert(g_base->logic);
  g_base->graphics->camera()->SetPosition(x, y, z);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PySetCameraPositionDef = {
    "set_camera_position",             // name
    (PyCFunction)PySetCameraPosition,  // method
    METH_VARARGS | METH_KEYWORDS,      // flags

    "set_camera_position(x: float, y: float, z: float) -> None\n"
    "\n"
    "(internal)\n"
    "\n"
    "WARNING: these camera controls will not apply to network clients\n"
    "and may behave unpredictably in other ways. Use them only for\n"
    "tinkering.",
};

// ---------------------------- set_camera_target ------------------------------

static auto PySetCameraTarget(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  float x = 0.0f;
  float y = 0.0f;
  float z = 0.0f;
  static const char* kwlist[] = {"x", "y", "z", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "fff",
                                   const_cast<char**>(kwlist), &x, &y, &z)) {
    return nullptr;
  }
  assert(g_base->logic);
  g_base->graphics->camera()->SetTarget(x, y, z);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PySetCameraTargetDef = {
    "set_camera_target",             // name
    (PyCFunction)PySetCameraTarget,  // method
    METH_VARARGS | METH_KEYWORDS,    // flags

    "set_camera_target(x: float, y: float, z: float) -> None\n"
    "\n"
    "(internal)\n"
    "\n"
    "WARNING: these camera controls will not apply to network clients\n"
    "and may behave unpredictably in other ways. Use them only for\n"
    "tinkering.",
};

// ---------------------------- set_camera_manual ------------------------------

static auto PySetCameraManual(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  bool value = false;
  static const char* kwlist[] = {"value", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "b",
                                   const_cast<char**>(kwlist), &value)) {
    return nullptr;
  }
  assert(g_base->logic);
  g_base->graphics->camera()->SetManual(value);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PySetCameraManualDef = {
    "set_camera_manual",             // name
    (PyCFunction)PySetCameraManual,  // method
    METH_VARARGS | METH_KEYWORDS,    // flags

    "set_camera_manual(value: bool) -> None\n"
    "\n"
    "(internal)\n"
    "\n"
    "WARNING: these camera controls will not apply to network clients\n"
    "and may behave unpredictably in other ways. Use them only for\n"
    "tinkering.",
};

// -------------------------------- charstr ------------------------------------

static auto PyCharStr(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  PyObject* name_obj;
  static const char* kwlist[] = {"name", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "O",
                                   const_cast<char**>(kwlist), &name_obj)) {
    return nullptr;
  }
  assert(g_base->logic);
  auto id(BasePython::GetPyEnum_SpecialChar(name_obj));
  assert(Utils::IsValidUTF8(g_base->assets->CharStr(id)));
  return PyUnicode_FromString(g_base->assets->CharStr(id).c_str());
  BA_PYTHON_CATCH;
}

static PyMethodDef PyCharStrDef = {
    "charstr",                     // name
    (PyCFunction)PyCharStr,        // method
    METH_VARARGS | METH_KEYWORDS,  // flags

    "charstr(char_id: babase.SpecialChar) -> str\n"
    "\n"
    "Get a unicode string representing a special character.\n"
    "\n"
    "Category: **General Utility Functions**\n"
    "\n"
    "Note that these utilize the private-use block of unicode characters\n"
    "(U+E000-U+F8FF) and are specific to the game; exporting or rendering\n"
    "them elsewhere will be meaningless.\n"
    "\n"
    "See babase.SpecialChar for the list of available characters.",
};

// ------------------------------- safecolor -----------------------------------

static auto PySafeColor(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  PyObject* color_obj;
  float red, green, blue;
  float target_intensity = 0.6f;
  static const char* kwlist[] = {"color", "target_intensity", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "O|f",
                                   const_cast<char**>(kwlist), &color_obj,
                                   &target_intensity)) {
    return nullptr;
  }
  if (!PySequence_Check(color_obj)) {
    throw Exception("Expected a sequence.", PyExcType::kType);
  }
  int len = static_cast<int>(PySequence_Length(color_obj));
  if (len != 3 && len != 4) {
    throw Exception("Expected a 3 or 4 length sequence; got "
                        + Python::ObjToString(color_obj) + ".",
                    PyExcType::kValue);
  }
  PythonRef red_obj(PySequence_GetItem(color_obj, 0), PythonRef::kSteal);
  PythonRef green_obj(PySequence_GetItem(color_obj, 1), PythonRef::kSteal);
  PythonRef blue_obj(PySequence_GetItem(color_obj, 2), PythonRef::kSteal);
  red = Python::GetPyFloat(red_obj.get());
  green = Python::GetPyFloat(green_obj.get());
  blue = Python::GetPyFloat(blue_obj.get());
  Graphics::GetSafeColor(&red, &green, &blue, target_intensity);
  if (len == 3) {
    return Py_BuildValue("(fff)", red, green, blue);
  } else {
    PythonRef alpha_obj(PySequence_GetItem(color_obj, 3), PythonRef::kSteal);
    float alpha = Python::GetPyFloat(alpha_obj.get());
    return Py_BuildValue("(ffff)", red, green, blue, alpha);
  }
  BA_PYTHON_CATCH;
}

static PyMethodDef PySafeColorDef = {
    "safecolor",                   // name
    (PyCFunction)PySafeColor,      // method
    METH_VARARGS | METH_KEYWORDS,  // flags

    "safecolor(color: Sequence[float], target_intensity: float = 0.6)\n"
    "  -> tuple[float, ...]\n"
    "\n"
    "Given a color tuple, return a color safe to display as text.\n"
    "\n"
    "Category: **General Utility Functions**\n"
    "\n"
    "Accepts tuples of length 3 or 4. This will slightly brighten very\n"
    "dark colors, etc.",
};

// ------------------------ get_max_graphics_quality ---------------------------

static auto PyGetMaxGraphicsQuality(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;
  // Currently all our supported devices can go up to higher.
  return Py_BuildValue("s", "Higher");
  BA_PYTHON_CATCH;
}

static PyMethodDef PyGetMaxGraphicsQualityDef = {
    "get_max_graphics_quality",            // name
    (PyCFunction)PyGetMaxGraphicsQuality,  // method
    METH_NOARGS,                           // flags

    "get_max_graphics_quality() -> str\n"
    "\n"
    "(internal)\n"
    "\n"
    "Return the max graphics-quality supported on the current hardware.",
};

// ------------------------------ evaluate_lstr --------------------------------

static auto PyEvaluateLstr(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  const char* value;
  static const char* kwlist[] = {"value", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "s",
                                   const_cast<char**>(kwlist), &value)) {
    return nullptr;
  }
  return PyUnicode_FromString(
      g_base->assets->CompileResourceString(value).c_str());
  BA_PYTHON_CATCH;
}

static PyMethodDef PyEvaluateLstrDef = {
    "evaluate_lstr",               // name
    (PyCFunction)PyEvaluateLstr,   // method
    METH_VARARGS | METH_KEYWORDS,  // flags

    "evaluate_lstr(value: str) -> str\n"
    "\n"
    "(internal)",
};

// --------------------------- get_string_height -------------------------------

static auto PyGetStringHeight(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  std::string s;
  int suppress_warning = 0;
  PyObject* s_obj;
  static const char* kwlist[] = {"string", "suppress_warning", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "O|i",
                                   const_cast<char**>(kwlist), &s_obj,
                                   &suppress_warning)) {
    return nullptr;
  }
  if (!suppress_warning) {
    BA_LOG_PYTHON_TRACE(
        "get_string_height() use is heavily discouraged as it reduces "
        "language-independence; pass suppress_warning=True if you must use "
        "it.");
  }
  s = g_base->python->GetPyLString(s_obj);
#if BA_DEBUG_BUILD
  if (g_base->assets->CompileResourceString(s) != s) {
    BA_LOG_PYTHON_TRACE(
        "Resource-string passed to get_string_height; this should be avoided.");
  }
#endif
  assert(g_base->graphics);
  return Py_BuildValue("f", g_base->text_graphics->GetStringHeight(s));
  BA_PYTHON_CATCH;
}

static PyMethodDef PyGetStringHeightDef = {
    "get_string_height",             // name
    (PyCFunction)PyGetStringHeight,  // method
    METH_VARARGS | METH_KEYWORDS,    // flags

    "get_string_height(string: str, suppress_warning: bool = False) -> "
    "float\n"
    "\n"
    "(internal)\n"
    "\n"
    "Given a string, returns its height using the standard small app\n"
    "font.",
};

// ---------------------------- get_string_width -------------------------------

static auto PyGetStringWidth(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  std::string s;
  PyObject* s_obj;
  int suppress_warning = 0;
  static const char* kwlist[] = {"string", "suppress_warning", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "O|i",
                                   const_cast<char**>(kwlist), &s_obj,
                                   &suppress_warning)) {
    return nullptr;
  }
  if (!suppress_warning) {
    BA_LOG_PYTHON_TRACE(
        "get_string_width() use is heavily discouraged as it reduces "
        "language-independence; pass suppress_warning=True if you must use "
        "it.");
  }
  s = g_base->python->GetPyLString(s_obj);
#if BA_DEBUG_BUILD
  if (g_base->assets->CompileResourceString(s) != s) {
    BA_LOG_PYTHON_TRACE(
        "resource-string passed to get_string_width; this should be avoided");
  }
#endif
  assert(g_base->graphics);
  return Py_BuildValue("f", g_base->text_graphics->GetStringWidth(s));
  BA_PYTHON_CATCH;
}

static PyMethodDef PyGetStringWidthDef = {
    "get_string_width",             // name
    (PyCFunction)PyGetStringWidth,  // method
    METH_VARARGS | METH_KEYWORDS,   // flags

    "get_string_width(string: str, suppress_warning: bool = False) -> "
    "float\n"
    "\n"
    "(internal)\n"
    "\n"
    "Given a string, returns its width using the standard small app\n"
    "font.",
};

// ------------------------------ have_chars -----------------------------------

static auto PyHaveChars(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  std::string text;
  PyObject* text_obj;
  static const char* kwlist[] = {"text", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "O",
                                   const_cast<char**>(kwlist), &text_obj)) {
    return nullptr;
  }
  text = g_base->python->GetPyLString(text_obj);
  if (TextGraphics::HaveChars(text)) {
    Py_RETURN_TRUE;
  } else {
    Py_RETURN_FALSE;
  }
  BA_PYTHON_CATCH;
}

static PyMethodDef PyHaveCharsDef = {
    "have_chars",                  // name
    (PyCFunction)PyHaveChars,      // method
    METH_VARARGS | METH_KEYWORDS,  // flags

    "have_chars(text: str) -> bool\n"
    "\n"
    "(internal)",
};

// ----------------------------- fade_screen -----------------------------------

static auto PyFadeScreen(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;

  int fade{};
  float time{0.25f};
  PyObject* endcall = nullptr;
  static const char* kwlist[] = {"to", "time", "endcall", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "|pfO",
                                   const_cast<char**>(kwlist), &fade, &time,
                                   &endcall)) {
    return nullptr;
  }
  BA_PRECONDITION(g_base->InLogicThread());
  g_base->graphics->FadeScreen(static_cast<bool>(fade),
                               static_cast<int>(1000.0f * time), endcall);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyFadeScreenDef = {
    "fade_screen",                 // name
    (PyCFunction)PyFadeScreen,     // method
    METH_VARARGS | METH_KEYWORDS,  // flags

    "fade_screen(to: int = 0, time: float = 0.25,\n"
    "  endcall: Callable[[], None] | None = None) -> None\n"
    "\n"
    "(internal)\n"
    "\n"
    "Fade the local game screen in our out from black over a duration of\n"
    "time. if \"to\" is 0, the screen will fade out to black.  Otherwise "
    "it\n"
    "will fade in from black. If endcall is provided, it will be run after "
    "a\n"
    "completely faded frame is drawn.",
};

// ---------------------- add_clean_frame_callback -----------------------------

static auto PyAddCleanFrameCallback(PyObject* self, PyObject* args,
                                    PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  PyObject* call_obj;
  static const char* kwlist[] = {"call", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "O",
                                   const_cast<char**>(kwlist), &call_obj)) {
    return nullptr;
  }
  g_base->graphics->AddCleanFrameCommand(
      Object::New<PythonContextCall>(call_obj));
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyAddCleanFrameCallbackDef = {
    "add_clean_frame_callback",            // name
    (PyCFunction)PyAddCleanFrameCallback,  // method
    METH_VARARGS | METH_KEYWORDS,          // flags

    "add_clean_frame_callback(call: Callable) -> None\n"
    "\n"
    "(internal)\n"
    "\n"
    "Provide an object to be called once the next non-progress-bar-frame "
    "has\n"
    "been rendered. Useful for queueing things to load in the background\n"
    "without elongating any current progress-bar-load.",
};

// ------------------------- get_display_resolution ----------------------------

static auto PyGetDisplayResolution(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;
  int x = 0;
  int y = 0;
  bool have_res = g_core->platform->GetDisplayResolution(&x, &y);
  if (have_res) {
    return Py_BuildValue("(ii)", x, y);
  } else {
    Py_RETURN_NONE;
  }
  BA_PYTHON_CATCH;
}

static PyMethodDef PyGetDisplayResolutionDef = {
    "get_display_resolution",             // name
    (PyCFunction)PyGetDisplayResolution,  // method
    METH_NOARGS,                          // flags

    "get_display_resolution() -> tuple[int, int] | None\n"
    "\n"
    "(internal)\n"
    "\n"
    "Return the currently selected display resolution for fullscreen\n"
    "display. Returns None if resolutions cannot be directly set.",
};

// ---------------------- fullscreen_control_available -------------------------

static auto PyFullscreenControlAvailable(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;

  BA_PRECONDITION(g_base->InLogicThread());
  if (g_base->app_adapter->FullscreenControlAvailable()) {
    Py_RETURN_TRUE;
  }
  Py_RETURN_FALSE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyFullscreenControlAvailableDef = {
    "fullscreen_control_available",             // name
    (PyCFunction)PyFullscreenControlAvailable,  // method
    METH_NOARGS,                                // flags

    "fullscreen_control_available() -> bool\n"
    "\n"
    "(internal)\n",
};

// --------------------- fullscreen_control_key_shortcut -----------------------

static auto PyFullscreenControlKeyShortcut(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;

  BA_PRECONDITION(g_base->InLogicThread());
  BA_PRECONDITION(g_base->app_adapter->FullscreenControlAvailable());

  auto val = g_base->app_adapter->FullscreenControlKeyShortcut();
  if (val.has_value()) {
    return PyUnicode_FromString(val->c_str());
  }
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyFullscreenControlKeyShortcutDef = {
    "fullscreen_control_key_shortcut",            // name
    (PyCFunction)PyFullscreenControlKeyShortcut,  // method
    METH_NOARGS,                                  // flags

    "fullscreen_control_key_shortcut() -> str | None\n"
    "\n"
    "(internal)\n",
};

// ------------------------ fullscreen_control_get -----------------------------

static auto PyFullscreenControlGet(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;

  BA_PRECONDITION(g_base->InLogicThread());
  if (g_base->app_adapter->FullscreenControlGet()) {
    Py_RETURN_TRUE;
  }
  Py_RETURN_FALSE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyFullscreenControlGetDef = {
    "fullscreen_control_get",             // name
    (PyCFunction)PyFullscreenControlGet,  // method
    METH_NOARGS,                          // flags

    "fullscreen_control_get() -> bool\n"
    "\n"
    "(internal)\n",
};

// ------------------------ fullscreen_control_set -----------------------------

static auto PyFullscreenControlSet(PyObject* self, PyObject* args,
                                   PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;

  BA_PRECONDITION(g_base->InLogicThread());

  int val{};
  static const char* kwlist[] = {"val", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "p",
                                   const_cast<char**>(kwlist), &val)) {
    return nullptr;
  }

  g_base->app_adapter->FullscreenControlSet(val);

  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyFullscreenControlSetDef = {
    "fullscreen_control_set",             // name
    (PyCFunction)PyFullscreenControlSet,  // method
    METH_VARARGS | METH_KEYWORDS,         // flags

    "fullscreen_control_set(val: bool) -> None\n"
    "\n"
    "(internal)\n",
};

// -------------------------- allows_ticket_sales ------------------------------

static auto PyAllowsTicketSales(PyObject* self, PyObject* args,
                                PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;

  BA_PRECONDITION(g_base->InLogicThread());

  Py_RETURN_TRUE;

  BA_PYTHON_CATCH;
}

static PyMethodDef PyAllowsTicketSalesDef = {
    "allows_ticket_sales",             // name
    (PyCFunction)PyAllowsTicketSales,  // method
    METH_NOARGS,                       // flags

    "allows_ticket_sales() -> bool\n"
    "\n"
    "(internal)\n",
};

// ----------------------------- supports_vsync --------------------------------

static auto PySupportsVSync(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;

  if (g_base->app_adapter->SupportsVSync()) {
    Py_RETURN_TRUE;
  }
  Py_RETURN_FALSE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PySupportsVSyncDef = {
    "supports_vsync",              // name
    (PyCFunction)PySupportsVSync,  // method
    METH_NOARGS,                   // flags

    "supports_vsync() -> bool\n"
    "\n"
    "(internal)\n",
};

// --------------------------- supports_max_fps --------------------------------

static auto PySupportsMaxFPS(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;

  if (g_base->app_adapter->SupportsMaxFPS()) {
    Py_RETURN_TRUE;
  }
  Py_RETURN_FALSE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PySupportsMaxFPSDef = {
    "supports_max_fps",             // name
    (PyCFunction)PySupportsMaxFPS,  // method
    METH_NOARGS,                    // flags

    "supports_max_fps() -> bool\n"
    "\n"
    "(internal)\n",
};

// ---------------------- supports_unicode_display -----------------------------

static auto PySupportsUnicodeDisplay(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;

  if (g_buildconfig.enable_os_font_rendering()) {
    Py_RETURN_TRUE;
  }
  Py_RETURN_FALSE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PySupportsUnicodeDisplayDef = {
    "supports_unicode_display",             // name
    (PyCFunction)PySupportsUnicodeDisplay,  // method
    METH_NOARGS,                            // flags

    "supports_unicode_display() -> bool\n"
    "\n"
    "Return whether we can display all unicode characters in the gui.\n",
};

// --------------------------- show_progress_bar -------------------------------

static auto PyShowProgressBar(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;

  g_base->graphics->EnableProgressBar(false);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyShowProgressBarDef = {
    "show_progress_bar",             // name
    (PyCFunction)PyShowProgressBar,  // method
    METH_VARARGS | METH_KEYWORDS,    // flags

    "show_progress_bar() -> None\n"
    "\n"
    "(internal)\n"
    "\n"
    "Category: **General Utility Functions**",
};

// ------------------------- set_ui_account_state ------------------------------

static auto PySetUIAccountState(PyObject* self, PyObject* args,
                                PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;

  BA_PRECONDITION(g_base->InLogicThread());

  int signed_in{};
  PyObject* name_obj{Py_None};
  static const char* kwlist[] = {"signed_in", "name", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "p|O",
                                   const_cast<char**>(kwlist), &signed_in,
                                   &name_obj)) {
    return nullptr;
  }

  if (signed_in) {
    auto name = Python::GetPyString(name_obj);
    g_base->ui->SetAccountState(true, name);
  } else {
    g_base->ui->SetAccountState(false, "");
  }

  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PySetUIAccountStateDef = {
    "set_ui_account_state",            // name
    (PyCFunction)PySetUIAccountState,  // method
    METH_VARARGS | METH_KEYWORDS,      // flags

    "set_ui_account_state(signed_in: bool, name: str | None = None) -> None\n"
    "\n"
    "(internal)\n",
};

// ------------------------ get_virtual_screen_size ----------------------------

static auto PyGetVirtualScreenSize(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;
  BA_PRECONDITION(g_base->InLogicThread());

  float x{g_base->graphics->screen_virtual_width()};
  float y{g_base->graphics->screen_virtual_height()};
  return Py_BuildValue("(ff)", x, y);
  BA_PYTHON_CATCH;
}

static PyMethodDef PyGetVirtualScreenSizeDef = {
    "get_virtual_screen_size",            // name
    (PyCFunction)PyGetVirtualScreenSize,  // method
    METH_NOARGS,                          // flags

    "get_virtual_screen_size() -> tuple[float, float]\n"
    "\n"
    "(internal)\n"
    "\n"
    "Return the current virtual size of the display.",
};

// ----------------------- get_virtual_safe_area_size --------------------------

static auto PyGetVirtualSafeAreaSize(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;
  BA_PRECONDITION(g_base->InLogicThread());

  float x, y;
  g_base->graphics->GetBaseVirtualRes(&x, &y);
  return Py_BuildValue("(ff)", x, y);
  BA_PYTHON_CATCH;
}

static PyMethodDef PyGetVirtualSafeAreaSizeDef = {
    "get_virtual_safe_area_size",           // name
    (PyCFunction)PyGetVirtualSafeAreaSize,  // method
    METH_NOARGS,                            // flags

    "get_virtual_safe_area_size() -> tuple[float, float]\n"
    "\n"
    "(internal)\n"
    "\n"
    "Return the size of the area on screen that will always be visible.",
};

// -----------------------------------------------------------------------------

auto PythonMethodsBase2::GetMethods() -> std::vector<PyMethodDef> {
  return {
      PyOpenURLDef,
      PyOverlayWebBrowserIsSupportedDef,
      PyOverlayWebBrowserOpenURLDef,
      PyOverlayWebBrowserIsOpenDef,
      PyOverlayWebBrowserCloseDef,
      PyGetDisplayResolutionDef,
      PyGetCameraPositionDef,
      PyGetCameraTargetDef,
      PySetCameraPositionDef,
      PySetCameraTargetDef,
      PySetCameraManualDef,
      PyAddCleanFrameCallbackDef,
      PyHaveCharsDef,
      PyFadeScreenDef,
      PyScreenMessageDef,
      PyGetStringWidthDef,
      PyGetStringHeightDef,
      PyEvaluateLstrDef,
      PyGetMaxGraphicsQualityDef,
      PySafeColorDef,
      PyCharStrDef,
      PyFullscreenControlAvailableDef,
      PyAllowsTicketSalesDef,
      PySupportsVSyncDef,
      PySupportsMaxFPSDef,
      PySupportsUnicodeDisplayDef,
      PyShowProgressBarDef,
      PyFullscreenControlKeyShortcutDef,
      PyFullscreenControlGetDef,
      PyFullscreenControlSetDef,
      PySetUIAccountStateDef,
      PyGetVirtualScreenSizeDef,
      PyGetVirtualSafeAreaSizeDef,
  };
}

#pragma clang diagnostic pop

}  // namespace ballistica::base
