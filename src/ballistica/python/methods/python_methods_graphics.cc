// Released under the MIT License. See LICENSE for details.

#include "ballistica/python/methods/python_methods_graphics.h"

#include <string>

#include "ballistica/game/game.h"
#include "ballistica/graphics/graphics.h"
#include "ballistica/graphics/text/text_graphics.h"
#include "ballistica/platform/platform.h"
#include "ballistica/python/python.h"
#include "ballistica/python/python_context_call_runnable.h"

namespace ballistica {

// Ignore signed bitwise stuff; python macros do it quite a bit.
#pragma clang diagnostic push
#pragma ide diagnostic ignored "hicpp-signed-bitwise"

auto PyCharStr(PyObject* self, PyObject* args, PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("charstr");
  PyObject* name_obj;
  static const char* kwlist[] = {"name", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "O",
                                   const_cast<char**>(kwlist), &name_obj)) {
    return nullptr;
  }
  assert(g_game);
  auto id(Python::GetPyEnum_SpecialChar(name_obj));
  assert(Utils::IsValidUTF8(g_game->CharStr(id)));
  return PyUnicode_FromString(g_game->CharStr(id).c_str());
  BA_PYTHON_CATCH;
}

auto PySafeColor(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("safecolor");
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

auto PyGetMaxGraphicsQuality(PyObject* self, PyObject* args) -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("get_max_graphics_quality");
  if (g_graphics && g_graphics->has_supports_high_quality_graphics_value()
      && g_graphics->supports_high_quality_graphics()) {
    return Py_BuildValue("s", "High");
  } else {
    return Py_BuildValue("s", "Medium");
  }
  BA_PYTHON_CATCH;
}

auto PyEvaluateLstr(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("evaluate_lstr");
  const char* value;
  static const char* kwlist[] = {"value", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "s",
                                   const_cast<char**>(kwlist), &value)) {
    return nullptr;
  }
  return PyUnicode_FromString(
      g_game->CompileResourceString(value, "evaluate_lstr").c_str());
  BA_PYTHON_CATCH;
}

auto PyGetStringHeight(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("get_string_height");
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
  s = Python::GetPyString(s_obj);
#if BA_DEBUG_BUILD
  if (g_game->CompileResourceString(s, "get_string_height test") != s) {
    BA_LOG_PYTHON_TRACE(
        "resource-string passed to get_string_height; this should be avoided");
  }
#endif
  assert(g_graphics);
  return Py_BuildValue("f", g_text_graphics->GetStringHeight(s));
  BA_PYTHON_CATCH;
}

auto PyGetStringWidth(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("get_string_width");
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
  s = Python::GetPyString(s_obj);
#if BA_DEBUG_BUILD
  if (g_game->CompileResourceString(s, "get_string_width debug test") != s) {
    BA_LOG_PYTHON_TRACE(
        "resource-string passed to get_string_width; this should be avoided");
  }
#endif
  assert(g_graphics);
  return Py_BuildValue("f", g_text_graphics->GetStringWidth(s));
  BA_PYTHON_CATCH;
}

auto PyHaveChars(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("have_chars");
  std::string text;
  PyObject* text_obj;
  static const char* kwlist[] = {"text", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "O",
                                   const_cast<char**>(kwlist), &text_obj)) {
    return nullptr;
  }
  text = Python::GetPyString(text_obj);
  if (TextGraphics::HaveChars(text)) {
    Py_RETURN_TRUE;
  } else {
    Py_RETURN_FALSE;
  }
  BA_PYTHON_CATCH;
}

auto PyAddCleanFrameCallback(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("add_clean_frame_callback");
  PyObject* call_obj;
  static const char* kwlist[] = {"call", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "O",
                                   const_cast<char**>(kwlist), &call_obj)) {
    return nullptr;
  }
  g_python->AddCleanFrameCommand(Object::New<PythonContextCall>(call_obj));
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyHasGammaControl(PyObject* self, PyObject* args) -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("has_gamma_control");
  // phasing this out; our old non-sdl2 mac has gamma controls but nothing newer
  // does...
#if BA_OSTYPE_MACOS && !BA_SDL2_BUILD
  Py_RETURN_TRUE;
#else
  Py_RETURN_FALSE;
#endif
  BA_PYTHON_CATCH;
}

auto PyGetDisplayResolution(PyObject* self, PyObject* args) -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("get_display_resolution");
  int x = 0;
  int y = 0;
  bool have_res = g_platform->GetDisplayResolution(&x, &y);
  if (have_res) {
    return Py_BuildValue("(ii)", x, y);
  } else {
    Py_RETURN_NONE;
  }
  BA_PYTHON_CATCH;
}

PyMethodDef PythonMethodsGraphics::methods_def[] = {
    {"get_display_resolution", PyGetDisplayResolution, METH_VARARGS,
     "get_display_resolution() -> Optional[Tuple[int, int]]\n"
     "\n"
     "(internal)\n"
     "\n"
     "Return the currently selected display resolution for fullscreen\n"
     "display. Returns None if resolutions cannot be directly set."},

    {"has_gamma_control", PyHasGammaControl, METH_VARARGS,
     "has_gamma_control() -> bool\n"
     "\n"
     "(internal)\n"
     "\n"
     "Returns whether the system can adjust overall screen gamma)"},

    {"add_clean_frame_callback", (PyCFunction)PyAddCleanFrameCallback,
     METH_VARARGS | METH_KEYWORDS,
     "add_clean_frame_callback(call: Callable) -> None\n"
     "\n"
     "(internal)\n"
     "\n"
     "Provide an object to be called once the next non-progress-bar-frame has\n"
     "been rendered. Useful for queueing things to load in the background\n"
     "without elongating any current progress-bar-load."},

    {"have_chars", (PyCFunction)PyHaveChars, METH_VARARGS | METH_KEYWORDS,
     "have_chars(text: str) -> bool\n"
     "\n"
     "(internal)"},

    {"get_string_width", (PyCFunction)PyGetStringWidth,
     METH_VARARGS | METH_KEYWORDS,
     "get_string_width(string: str, suppress_warning: bool = False) -> float\n"
     "\n"
     "(internal)\n"
     "\n"
     "Given a string, returns its width using the standard small app\n"
     "font."},

    {"get_string_height", (PyCFunction)PyGetStringHeight,
     METH_VARARGS | METH_KEYWORDS,
     "get_string_height(string: str, suppress_warning: bool = False) -> float\n"
     "\n"
     "(internal)\n"
     "\n"
     "Given a string, returns its height using the standard small app\n"
     "font."},

    {"evaluate_lstr", (PyCFunction)PyEvaluateLstr, METH_VARARGS | METH_KEYWORDS,
     "evaluate_lstr(value: str) -> str\n"
     "\n"
     "(internal)"},

    {"get_max_graphics_quality", PyGetMaxGraphicsQuality, METH_VARARGS,
     "get_max_graphics_quality() -> str\n"
     "\n"
     "(internal)\n"
     "\n"
     "Return the max graphics-quality supported on the current hardware."},

    {"safecolor", (PyCFunction)PySafeColor, METH_VARARGS | METH_KEYWORDS,
     "safecolor(color: Sequence[float], target_intensity: float = 0.6)\n"
     "  -> Tuple[float, ...]\n"
     "\n"
     "Given a color tuple, return a color safe to display as text.\n"
     "\n"
     "Category: General Utility Functions\n"
     "\n"
     "Accepts tuples of length 3 or 4. This will slightly brighten very\n"
     "dark colors, etc."},

    {"charstr", (PyCFunction)PyCharStr, METH_VARARGS | METH_KEYWORDS,
     "charstr(char_id: ba.SpecialChar) -> str\n"
     "\n"
     "Get a unicode string representing a special character.\n"
     "\n"
     "Category: General Utility Functions\n"
     "\n"
     "Note that these utilize the private-use block of unicode characters\n"
     "(U+E000-U+F8FF) and are specific to the game; exporting or rendering\n"
     "them elsewhere will be meaningless.\n"
     "\n"
     "see ba.SpecialChar for the list of available characters."},

    {nullptr, nullptr, 0, nullptr}};

#pragma clang diagnostic pop

}  // namespace ballistica
