// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_UI_V1_PYTHON_UI_V1_PYTHON_H_
#define BALLISTICA_UI_V1_PYTHON_UI_V1_PYTHON_H_

#include <string>

#include "ballistica/base/base.h"
#include "ballistica/shared/python/python_object_set.h"
#include "ballistica/ui_v1/ui_v1.h"

namespace ballistica::ui_v1 {

/// General Python support class for UIV1.
class UIV1Python {
 public:
  UIV1Python();

  void AddPythonClasses(PyObject* module);
  void ImportPythonObjs();

  void InvokeStringEditor(PyObject* string_edit_adapter_instance);
  void ShowURL(const std::string& url);

  static auto GetPyWidget(PyObject* o) -> Widget*;
  void InvokeQuitWindow(QuitType quit_type);

  /// Specific Python objects we hold in objs_.
  enum class ObjID {
    kOnScreenKeyboardClass,
    kRootUITicketIconPressCall,
    kRootUIGetTokensButtonPressCall,
    kRootUIAccountButtonPressCall,
    kRootUIInboxButtonPressCall,
    kRootUISettingsButtonPressCall,
    kRootUIAchievementsButtonPressCall,
    kRootUIStoreButtonPressCall,
    kRootUIChestSlot0PressCall,
    kRootUIChestSlot1PressCall,
    kRootUIChestSlot2PressCall,
    kRootUIChestSlot3PressCall,
    kRootUIInventoryButtonPressCall,
    kRootUITrophyMeterPressCall,
    kRootUILevelIconPressCall,
    kRootUITokensMeterPressCall,
    kEmptyCall,
    kRootUIMenuButtonPressCall,
    kRootUIBackButtonPressCall,
    kRootUISquadButtonPressCall,
    kQuitWindowCall,
    kShowURLWindowCall,
    kDoubleTransitionOutWarningCall,
    kTextWidgetStringEditAdapterClass,
    kLast  // Sentinel; must be at end.
  };

  const auto& objs() { return objs_; }

 private:
  PythonObjectSet<ObjID> objs_;
};

}  // namespace ballistica::ui_v1

#endif  // BALLISTICA_UI_V1_PYTHON_UI_V1_PYTHON_H_
