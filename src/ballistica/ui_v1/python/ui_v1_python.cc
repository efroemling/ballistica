// Released under the MIT License. See LICENSE for details.

#include "ballistica/ui_v1/python/ui_v1_python.h"

#include "ballistica/base/assets/assets.h"
#include "ballistica/base/audio/audio.h"
#include "ballistica/base/input/device/input_device.h"
#include "ballistica/base/input/input.h"
#include "ballistica/base/logic/logic.h"
#include "ballistica/base/python/support/python_context_call.h"
#include "ballistica/shared/foundation/event_loop.h"
#include "ballistica/shared/python/python_command.h"
#include "ballistica/shared/python/python_module_builder.h"
#include "ballistica/ui_v1/python/class/python_class_ui_mesh.h"
#include "ballistica/ui_v1/python/class/python_class_ui_sound.h"
#include "ballistica/ui_v1/python/class/python_class_ui_texture.h"
#include "ballistica/ui_v1/python/class/python_class_widget.h"
#include "ballistica/ui_v1/python/methods/python_methods_ui_v1.h"
#include "ballistica/ui_v1/widget/text_widget.h"

namespace ballistica::ui_v1 {

UIV1Python::UIV1Python() = default;

// Declare a plain c PyInit_XXX function for our Python module;
// this is how Python inits our binary module (and by extension, our
// entire feature-set).
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
  // Import and grab all our objs_.
  // This code blob expects 'ObjID' and 'objs_' to be defined.
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
  g_base->logic->event_loop()->PushCall([this, url] {
    assert(g_base->InLogicThread());
    if (objs().Exists(ObjID::kShowURLWindowCall)) {
      base::ScopedSetContext ssc(nullptr);
      PythonRef args(Py_BuildValue("(s)", url.c_str()), PythonRef::kSteal);
      objs().Get(ObjID::kShowURLWindowCall).Call(args);
    } else {
      Log(LogLevel::kError, "ShowURLWindowCall nonexistent.");
    }
  });
}

void UIV1Python::HandleDeviceMenuPress(base::InputDevice* device) {
  assert(device);
  assert(objs().Exists(ObjID::kDeviceMenuPressCall));

  // Ignore if input is locked...
  if (g_base->input->IsInputLocked()) {
    return;
  }
  base::ScopedSetContext ssc(nullptr);
  PythonRef args(device ? Py_BuildValue("(i)", device->index())
                        : Py_BuildValue("(O)", Py_None),
                 PythonRef::kSteal);
  {
    Python::ScopedCallLabel label("handleDeviceMenuPress");
    objs().Get(ObjID::kDeviceMenuPressCall).Call(args);
  }
}

void UIV1Python::LaunchStringEdit(TextWidget* w) {
  assert(g_base->InLogicThread());
  BA_PRECONDITION(w);

  base::ScopedSetContext ssc(nullptr);
  g_base->audio->PlaySound(g_base->assets->SysSound(base::SysSoundID::kSwish));

  // Gotta run this in the next cycle.
  PythonRef args(Py_BuildValue("(Osi)", w->BorrowPyRef(),
                               w->description().c_str(), w->max_chars()),
                 PythonRef::kSteal);
  Object::New<base::PythonContextCall>(
      objs().Get(ObjID::kOnScreenKeyboardClass))
      ->Schedule(args);
}

}  // namespace ballistica::ui_v1
