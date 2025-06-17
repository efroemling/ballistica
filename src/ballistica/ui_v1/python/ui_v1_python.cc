// Released under the MIT License. See LICENSE for details.

#include "ballistica/ui_v1/python/ui_v1_python.h"

#include <string>

#include "ballistica/base/audio/audio.h"
#include "ballistica/base/input/device/keyboard_input.h"
#include "ballistica/base/input/input.h"
#include "ballistica/base/python/base_python.h"
#include "ballistica/base/python/support/python_context_call.h"
#include "ballistica/base/ui/dev_console.h"
#include "ballistica/base/ui/ui.h"
#include "ballistica/shared/python/python_command.h"  // IWYU pragma: keep.
#include "ballistica/shared/python/python_module_builder.h"
#include "ballistica/ui_v1/python/class/python_class_ui_mesh.h"
#include "ballistica/ui_v1/python/class/python_class_ui_sound.h"
#include "ballistica/ui_v1/python/class/python_class_ui_texture.h"
#include "ballistica/ui_v1/python/class/python_class_widget.h"
#include "ballistica/ui_v1/python/methods/python_methods_ui_v1.h"

namespace ballistica::ui_v1 {

UIV1Python::UIV1Python() = default;

// Declare a plain C PyInit_XXX function for our Python module; this is how
// Python inits our binary module (and by extension, our entire
// feature-set).
extern "C" auto PyInit__bauiv1() -> PyObject* {
  auto* builder =
      new PythonModuleBuilder("_bauiv1",
                              {
                                  PythonMethodsUIV1::GetMethods(),
                              },
                              [](PyObject* module) -> int {
                                BA_PYTHON_TRY;
                                UIV1FeatureSet::OnModuleExec(module);
                                return 0;
                                BA_PYTHON_INT_CATCH;
                              });
  return builder->Build();
}

void UIV1Python::AddPythonClasses(PyObject* module) {
  PythonModuleBuilder::AddClass<PythonClassUISound>(module);
  PythonModuleBuilder::AddClass<PythonClassUITexture>(module);
  PythonModuleBuilder::AddClass<PythonClassUIMesh>(module);
  PythonModuleBuilder::AddClass<PythonClassWidget>(module);
}

void UIV1Python::ImportPythonObjs() {
  // Import and grab all our objs_. This code blob expects 'ObjID' and
  // 'objs_' to be defined.
#include "ballistica/ui_v1/mgen/pyembed/binding_ui_v1.inc"
}

auto UIV1Python::GetPyWidget(PyObject* o) -> Widget* {
  assert(Python::HaveGIL());
  assert(o != nullptr);

  if (PythonClassWidget::Check(o)) {
    // This will succeed or throw its own Exception.
    return reinterpret_cast<ui_v1::PythonClassWidget*>(o)->GetWidget();
  }

  // Nothing here should have led to an unresolved Python error state.
  assert(!PyErr_Occurred());

  throw Exception(
      "Can't get widget from value: " + Python::ObjToString(o) + ".",
      PyExcType::kType);
}

void UIV1Python::ShowURL(const std::string& url) {
  assert(g_base->InLogicThread());

  if (objs().Exists(ObjID::kShowURLWindowCall)) {
    base::ScopedSetContext ssc(nullptr);
    PythonRef args(Py_BuildValue("(s)", url.c_str()), PythonRef::kSteal);
    objs().Get(ObjID::kShowURLWindowCall).Call(args);
  } else {
    g_core->logging->Log(LogName::kBa, LogLevel::kError,
                         "ShowURLWindowCall nonexistent.");
  }
}

void UIV1Python::InvokeStringEditor(PyObject* string_edit_adapter_instance) {
  BA_PRECONDITION(g_base->InLogicThread());
  BA_PRECONDITION(string_edit_adapter_instance);

  base::ScopedSetContext ssc(nullptr);
  g_base->audio->SafePlaySysSound(base::SysSoundID::kSwish);

  PythonRef args(Py_BuildValue("(O)", string_edit_adapter_instance),
                 PythonRef::kSteal);

  auto context_call = Object::New<base::PythonContextCall>(
      objs().Get(ObjID::kOnScreenKeyboardClass));

  // This is probably getting called from within UI handling, so we need to
  // schedule things to run post-ui-traversal in that case.
  if (g_base->ui->InUIOperation()) {
    context_call->ScheduleInUIOperation(args);
  } else {
    // Otherwise just run immediately.
    g_core->logging->Log(
        LogName::kBa, LogLevel::kWarning,
        "UIV1Python::InvokeStringEditor running outside of UIInteraction; "
        "unexpected.");
    context_call->Run(args);
  }
}

void UIV1Python::InvokeQuitWindow(QuitType quit_type) {
  assert(g_base->InLogicThread());
  base::ScopedSetContext ssc(nullptr);

  // If the in-app console is active, dismiss it.
  if (auto* dev_console = g_base->ui->dev_console()) {
    if (dev_console->IsActive()) {
      dev_console->Dismiss();
    }
  }

  g_base->audio->SafePlaySysSound(base::SysSoundID::kSwish);
  auto py_enum = g_base->python->PyQuitType(quit_type);
  auto args = PythonRef::Stolen(Py_BuildValue("(O)", py_enum.get()));
  objs().Get(UIV1Python::ObjID::kQuitWindowCall).Call(args);

  // If we have a keyboard, give it UI ownership.
  base::KeyboardInput* keyboard = g_base->input->keyboard_input();
  if (keyboard) {
    g_base->ui->SetMainUIInputDevice(keyboard);
  }
}

}  // namespace ballistica::ui_v1
