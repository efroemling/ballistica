// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_UI_V1_PYTHON_CLASS_PYTHON_CLASS_VIEWER_SOURCE_H_
#define BALLISTICA_UI_V1_PYTHON_CLASS_PYTHON_CLASS_VIEWER_SOURCE_H_

#include "ballistica/base/python/class/python_class_asset_ref.h"
#include "ballistica/ui_v1/support/viewer_source.h"

namespace ballistica::ui_v1 {

/// Python handle to a ViewerSource. Opaque; whatever provides sources
/// hands these out and viewer widgets take them.
class PythonClassViewerSource
    : public base::PythonClassAssetRef<PythonClassViewerSource, ViewerSource> {
 public:
  static auto type_name() -> const char* { return "ViewerSource"; }
  static constexpr const char* kTpName = "bauiv1.ViewerSource";
  static constexpr const char* kTpDoc =
      "Something that makes a picture for a live depiction to show.\n"
      "\n"
      "These come from whatever provides such pictures (a scene viewer,\n"
      "for instance) and are drawn by the depictions showing them.\n"
      "They are made to outlast the widgets showing them, so a rebuilt\n"
      "window can carry on showing what the old one was.\n"
      "\n"
      ":meta private:";
  static constexpr const char* kFactoryCall = "a viewer's source attr";

  static PyMethodDef tp_methods[];

  auto source() const -> ViewerSource& { return asset(); }

 private:
  static auto GetIdleTime(PythonClassViewerSource* self) -> PyObject*;
};

}  // namespace ballistica::ui_v1

#endif  // BALLISTICA_UI_V1_PYTHON_CLASS_PYTHON_CLASS_VIEWER_SOURCE_H_
