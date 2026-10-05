// Released under the MIT License. See LICENSE for details.

#include "ballistica/ui_v1/python/methods/python_methods_ui_v1.h"

#include <initializer_list>
#include <string>
#include <vector>

#include "ballistica/base/assets/assets.h"
#include "ballistica/base/assets/sound_asset.h"
#include "ballistica/base/logic/logic.h"
#include "ballistica/base/python/base_python.h"
#include "ballistica/base/python/class/python_class_lang_str.h"
#include "ballistica/base/support/context.h"
#include "ballistica/base/ui/ui.h"
#include "ballistica/shared/foundation/event_loop.h"
#include "ballistica/shared/foundation/macros.h"
#include "ballistica/ui_v1/python/class/python_class_ui_mesh.h"
#include "ballistica/ui_v1/python/class/python_class_ui_sound.h"
#include "ballistica/ui_v1/python/class/python_class_ui_texture.h"
#include "ballistica/ui_v1/python/class/python_class_viewer_source.h"
#include "ballistica/ui_v1/python/ui_v1_python.h"
#include "ballistica/ui_v1/widget/button_widget.h"
#include "ballistica/ui_v1/widget/check_box_widget.h"
#include "ballistica/ui_v1/widget/column_widget.h"
#include "ballistica/ui_v1/widget/depiction_slot.h"
#include "ballistica/ui_v1/widget/h_scroll_widget.h"
#include "ballistica/ui_v1/widget/image_widget.h"
#include "ballistica/ui_v1/widget/root_widget.h"
#include "ballistica/ui_v1/widget/row_widget.h"
#include "ballistica/ui_v1/widget/scroll_widget.h"
#include "ballistica/ui_v1/widget/slider_widget.h"
#include "ballistica/ui_v1/widget/spinner_widget.h"

namespace ballistica::ui_v1 {

// ------------------------------ getsound -------------------------------------

static auto PyGetSound(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  const char* name;
  static const char* kwlist[] = {"name", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "s",
                                   const_cast<char**>(kwlist), &name)) {
    return nullptr;
  }
  base::Assets::FailOnAssetPackagePath(name, "getsound");
  {
    base::Assets::AssetListLock lock;
    Object::Ref<base::SoundAsset> sound = g_base->assets->GetSound(name);
    return PythonClassUISound::Create(sound.get());
  }
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyGetSoundDef = {
    "getsound",                    // name
    (PyCFunction)PyGetSound,       // method
    METH_VARARGS | METH_KEYWORDS,  // flags

    "getsound(name: str) -> bauiv1.Sound\n"
    "\n"
    "Load a sound for use in the ui.",
};

// ------------------------------ apsoundget -----------------------------------

static auto PyApSoundGet(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  int64_t apvernum;
  const char* name;
  static const char* kwlist[] = {"apvernum", "name", nullptr};
  if (!PyArg_ParseTupleAndKeywords(
          args, keywds, "Ls", const_cast<char**>(kwlist), &apvernum, &name)) {
    return nullptr;
  }
  // The engine keys packages by numeric id as text.
  std::string apverid = std::to_string(apvernum);
  {
    base::Assets::AssetListLock lock;
    Object::Ref<base::SoundAsset> sound =
        g_base->assets->GetPackageSound(apverid, name);
    return PythonClassUISound::Create(sound.get());
  }
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyApSoundGetDef = {
    "apsoundget",                  // name
    (PyCFunction)PyApSoundGet,     // method
    METH_VARARGS | METH_KEYWORDS,  // flags

    "apsoundget(apvernum: int, name: str) -> bauiv1.Sound\n"
    "\n"
    "Load a ui sound from an asset-package (internal).\n"
    "\n"
    "Do not call this directly; asset-package assets should be accessed\n"
    "through their package's generated Python wrapper module, which routes\n"
    "through this call. Requires a fully-qualified '<apvernum>:<path>'\n"
    "asset name.\n"
    "\n"
    ":meta private:",
};

// ----------------------------- gettexture ------------------------------------

static auto PyGetTexture(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  const char* name;
  static const char* kwlist[] = {"name", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "s",
                                   const_cast<char**>(kwlist), &name)) {
    return nullptr;
  }
  base::Assets::FailOnAssetPackagePath(name, "gettexture");
  {
    base::Assets::AssetListLock lock;
    return PythonClassUITexture::Create(g_base->assets->GetTexture(name));
  }
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyGetTextureDef = {
    "gettexture",                  // name
    (PyCFunction)PyGetTexture,     // method
    METH_VARARGS | METH_KEYWORDS,  // flags

    "gettexture(name: str) -> bauiv1.Texture\n"
    "\n"
    "Load a texture for use in the ui.",
};

// ----------------------------- aptextureget ----------------------------------

static auto PyApTextureGet(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  int64_t apvernum;
  const char* name;
  static const char* kwlist[] = {"apvernum", "name", nullptr};
  if (!PyArg_ParseTupleAndKeywords(
          args, keywds, "Ls", const_cast<char**>(kwlist), &apvernum, &name)) {
    return nullptr;
  }
  // The engine keys packages by numeric id as text.
  std::string apverid = std::to_string(apvernum);
  {
    base::Assets::AssetListLock lock;
    return PythonClassUITexture::Create(
        g_base->assets->GetPackageTexture(apverid, name));
  }
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyApTextureGetDef = {
    "aptextureget",                // name
    (PyCFunction)PyApTextureGet,   // method
    METH_VARARGS | METH_KEYWORDS,  // flags

    "aptextureget(apvernum: int, name: str) -> bauiv1.Texture\n"
    "\n"
    "Load a ui texture from an asset-package (internal).\n"
    "\n"
    "Do not call this directly; asset-package assets should be accessed\n"
    "through their package's generated Python wrapper module, which routes\n"
    "through this call. Requires a fully-qualified '<apvernum>:<path>'\n"
    "asset name.\n"
    "\n"
    ":meta private:",
};

// -------------------------- get_qrcode_texture -------------------------------

static auto PyGetQRCodeTexture(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  const char* url;
  static const char* kwlist[] = {"url", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "s",
                                   const_cast<char**>(kwlist), &url)) {
    return nullptr;
  }
  {
    base::Assets::AssetListLock lock;
    return PythonClassUITexture::Create(g_base->assets->GetQRCodeTexture(url));
  }
  BA_PYTHON_CATCH;
}

static PyMethodDef PyGetQRCodeTextureDef = {
    "get_qrcode_texture",             // name
    (PyCFunction)PyGetQRCodeTexture,  // method
    METH_VARARGS | METH_KEYWORDS,     // flags

    "get_qrcode_texture(url: str) -> bauiv1.Texture\n"
    "\n"
    "Return a QR code texture.\n"
    "\n"
    "The provided url must be 64 bytes or less.",
};

// ------------------------------- getmesh -------------------------------------

static auto PyGetMesh(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  const char* name;
  static const char* kwlist[] = {"name", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "s",
                                   const_cast<char**>(kwlist), &name)) {
    return nullptr;
  }
  base::Assets::FailOnAssetPackagePath(name, "getmesh");
  {
    base::Assets::AssetListLock lock;
    return PythonClassUIMesh::Create(g_base->assets->GetMesh(name));
  }
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyGetMeshDef = {
    "getmesh",                     // name
    (PyCFunction)PyGetMesh,        // method
    METH_VARARGS | METH_KEYWORDS,  // flags

    "getmesh(name: str) -> bauiv1.Mesh\n"
    "\n"
    "Load a mesh for use solely in the local user interface.",
};

// ------------------------------ apmeshget ------------------------------------

static auto PyApMeshGet(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  int64_t apvernum;
  const char* name;
  static const char* kwlist[] = {"apvernum", "name", nullptr};
  if (!PyArg_ParseTupleAndKeywords(
          args, keywds, "Ls", const_cast<char**>(kwlist), &apvernum, &name)) {
    return nullptr;
  }
  // The engine keys packages by numeric id as text.
  std::string apverid = std::to_string(apvernum);
  {
    base::Assets::AssetListLock lock;
    return PythonClassUIMesh::Create(
        g_base->assets->GetPackageMesh(apverid, name));
  }
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyApMeshGetDef = {
    "apmeshget",                   // name
    (PyCFunction)PyApMeshGet,      // method
    METH_VARARGS | METH_KEYWORDS,  // flags

    "apmeshget(apvernum: int, name: str) -> bauiv1.Mesh\n"
    "\n"
    "Load a ui mesh from an asset-package (internal).\n"
    "\n"
    "Do not call this directly; asset-package assets should be accessed\n"
    "through their package's generated Python wrapper module, which routes\n"
    "through this call. Requires a fully-qualified '<apvernum>:<path>'\n"
    "asset name.\n"
    "\n"
    ":meta private:",
};

// --------------------------- depiction args ----------------------------------

/// Apply the depiction args image and button widgets share (Py_None
/// for any left unset).
static void ApplyDepictionArgs(DepictionSlot* slot, PyObject* depiction_obj,
                               PyObject* key_obj, PyObject* h_align_obj,
                               PyObject* v_align_obj, PyObject* debug_obj) {
  if (debug_obj != Py_None) {
    slot->set_debug(Python::GetBool(debug_obj));
  }
  // Key first: it applies to the depiction set below.
  if (key_obj != Py_None) {
    slot->set_key(Python::GetString(key_obj));
  }
  if (h_align_obj != Py_None) {
    std::string val = Python::GetString(h_align_obj);
    if (val == "left") {
      slot->set_h_align(base::DepictionHAlign::kLeft);
    } else if (val == "center") {
      slot->set_h_align(base::DepictionHAlign::kCenter);
    } else if (val == "right") {
      slot->set_h_align(base::DepictionHAlign::kRight);
    } else {
      throw Exception("Invalid depiction_h_align: '" + val + "'.",
                      PyExcType::kValue);
    }
  }
  if (v_align_obj != Py_None) {
    std::string val = Python::GetString(v_align_obj);
    if (val == "bottom") {
      slot->set_v_align(base::DepictionVAlign::kBottom);
    } else if (val == "center") {
      slot->set_v_align(base::DepictionVAlign::kCenter);
    } else if (val == "top") {
      slot->set_v_align(base::DepictionVAlign::kTop);
    } else {
      throw Exception("Invalid depiction_v_align: '" + val + "'.",
                      PyExcType::kValue);
    }
  }
  if (depiction_obj != Py_None) {
    slot->SetDepiction(Python::GetString(depiction_obj));
  }
}

/// Whether any of these args is set (so a widget needs its depiction
/// slot).
static auto AnySet(std::initializer_list<PyObject*> objs) -> bool {
  for (PyObject* obj : objs) {
    if (obj != Py_None) {
      return true;
    }
  }
  return false;
}

// ----------------------------- buttonwidget ----------------------------------

static auto PyButtonWidget(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  PyObject* parent_obj{Py_None};
  PyObject* id_obj{Py_None};
  PyObject* size_obj{Py_None};
  PyObject* pos_obj{Py_None};
  PyObject* label_obj{Py_None};
  PyObject* edit_obj{Py_None};
  PyObject* query_obj{Py_None};
  ContainerWidget* parent_widget{};
  PyObject* on_activate_call_obj{Py_None};
  PyObject* color_obj{Py_None};
  PyObject* down_widget_obj{Py_None};
  Widget* down_widget{};
  PyObject* up_widget_obj{Py_None};
  Widget* up_widget{};
  PyObject* left_widget_obj{Py_None};
  Widget* left_widget{};
  PyObject* right_widget_obj{Py_None};
  Widget* right_widget{};
  PyObject* texture_obj{Py_None};
  PyObject* tint_texture_obj{Py_None};
  PyObject* text_scale_obj{Py_None};
  PyObject* textcolor_obj{Py_None};
  PyObject* enable_sound_obj{Py_None};
  PyObject* mesh_transparent_obj{Py_None};
  PyObject* mesh_opaque_obj{Py_None};
  PyObject* repeat_obj{Py_None};
  PyObject* scale_obj{Py_None};
  PyObject* transition_delay_obj{Py_None};
  PyObject* on_select_call_obj{Py_None};
  PyObject* button_type_obj{Py_None};
  PyObject* extra_touch_border_scale_obj{Py_None};
  PyObject* selectable_obj{Py_None};
  PyObject* show_buffer_top_obj{Py_None};
  PyObject* icon_obj{Py_None};
  PyObject* icon_scale_obj{Py_None};
  PyObject* icon_tint_obj{Py_None};
  PyObject* icon_color_obj{Py_None};
  PyObject* autoselect_obj{Py_None};
  PyObject* mask_texture_obj{Py_None};
  PyObject* tint_color_obj{Py_None};
  PyObject* tint2_color_obj{Py_None};
  PyObject* text_flatness_obj{Py_None};
  PyObject* text_res_scale_obj{Py_None};
  PyObject* text_literal_obj{Py_None};
  PyObject* opacity_obj{Py_None};
  PyObject* rotate_obj{Py_None};
  PyObject* enabled_obj{Py_None};
  PyObject* better_bg_fit_obj{Py_None};
  PyObject* transition_type_obj{Py_None};
  PyObject* on_actions_complete_call_obj{Py_None};
  PyObject* text_h_align_obj{Py_None};
  PyObject* accessory_obj{Py_None};
  PyObject* depiction_obj{Py_None};
  PyObject* depiction_key_obj{Py_None};
  PyObject* depiction_h_align_obj{Py_None};
  PyObject* depiction_v_align_obj{Py_None};
  PyObject* depiction_hit_area_obj{Py_None};
  PyObject* depiction_debug_obj{Py_None};
  PyObject* tint3_color_obj{Py_None};
  static const char* kwlist[] = {"edit",
                                 "parent",
                                 "id",
                                 "size",
                                 "position",
                                 "on_activate_call",
                                 "label",
                                 "color",
                                 "down_widget",
                                 "up_widget",
                                 "left_widget",
                                 "right_widget",
                                 "texture",
                                 "text_scale",
                                 "textcolor",
                                 "enable_sound",
                                 "mesh_transparent",
                                 "mesh_opaque",
                                 "repeat",
                                 "scale",
                                 "transition_delay",
                                 "on_select_call",
                                 "button_type",
                                 "extra_touch_border_scale",
                                 "selectable",
                                 "show_buffer_top",
                                 "icon",
                                 "iconscale",
                                 "icon_tint",
                                 "icon_color",
                                 "autoselect",
                                 "mask_texture",
                                 "tint_texture",
                                 "tint_color",
                                 "tint2_color",
                                 "text_flatness",
                                 "text_res_scale",
                                 "enabled",
                                 "text_literal",
                                 "opacity",
                                 "rotate",
                                 "better_bg_fit",
                                 "transition_type",
                                 "query",
                                 "on_actions_complete_call",
                                 "text_h_align",
                                 "accessory",
                                 "depiction",
                                 "depiction_key",
                                 "depiction_h_align",
                                 "depiction_v_align",
                                 "depiction_hit_area",
                                 "depiction_debug",
                                 "tint3_color",
                                 nullptr};
  if (!PyArg_ParseTupleAndKeywords(
          args, keywds,
          "|OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO",
          const_cast<char**>(kwlist), &edit_obj, &parent_obj, &id_obj,
          &size_obj, &pos_obj, &on_activate_call_obj, &label_obj, &color_obj,
          &down_widget_obj, &up_widget_obj, &left_widget_obj, &right_widget_obj,
          &texture_obj, &text_scale_obj, &textcolor_obj, &enable_sound_obj,
          &mesh_transparent_obj, &mesh_opaque_obj, &repeat_obj, &scale_obj,
          &transition_delay_obj, &on_select_call_obj, &button_type_obj,
          &extra_touch_border_scale_obj, &selectable_obj, &show_buffer_top_obj,
          &icon_obj, &icon_scale_obj, &icon_tint_obj, &icon_color_obj,
          &autoselect_obj, &mask_texture_obj, &tint_texture_obj,
          &tint_color_obj, &tint2_color_obj, &text_flatness_obj,
          &text_res_scale_obj, &enabled_obj, &text_literal_obj, &opacity_obj,
          &rotate_obj, &better_bg_fit_obj, &transition_type_obj, &query_obj,
          &on_actions_complete_call_obj, &text_h_align_obj, &accessory_obj,
          &depiction_obj, &depiction_key_obj, &depiction_h_align_obj,
          &depiction_v_align_obj, &depiction_hit_area_obj, &depiction_debug_obj,
          &tint3_color_obj))
    return nullptr;

  if (!g_base->CurrentContext().IsEmpty()) {
    throw Exception("UI functions must be called with no context set.");
  }

  // Handle the query special case first (mirrors textwidget's `query`).
  if (query_obj != Py_None) {
    auto* qb = dynamic_cast<ButtonWidget*>(UIV1Python::GetPyWidget(query_obj));
    if (qb == nullptr) {
      throw Exception("Invalid or nonexistent widget.",
                      PyExcType::kWidgetNotFound);
    }
    return PyUnicode_FromString(qb->GetQueryText().c_str());
  }

  // Gather up any user code triggered by this stuff and run it at the end
  // before we return.
  base::UI::OperationContext ui_op_context;

  // Grab the edited widget or create a new one.
  Object::Ref<ButtonWidget> b;
  if (edit_obj != Py_None) {
    b = dynamic_cast<ButtonWidget*>(UIV1Python::GetPyWidget(edit_obj));
    if (!b.exists()) {
      throw Exception("Invalid or nonexistent widget.",
                      PyExcType::kWidgetNotFound);
    }
  } else {
    parent_widget = parent_obj == Py_None
                        ? g_ui_v1->screen_root_widget()
                        : dynamic_cast<ContainerWidget*>(
                              UIV1Python::GetPyWidget(parent_obj));
    if (parent_widget == nullptr) {
      throw Exception("Parent widget nonexistent or not a container.",
                      PyExcType::kWidgetNotFound);
    }
    b = Object::New<ButtonWidget>();
  }

  // Set applicable values.
  if (id_obj != Py_None) {
    b->SetID(Python::GetString(id_obj));
  }
  if (text_literal_obj != Py_None) {
    b->SetTextLiteral(Python::GetBool(text_literal_obj));
  }
  if (label_obj != Py_None) {
    // See the textwidget text param note re native language-strings.
    if (base::PythonClassLangStr::Check(label_obj)) {
      b->SetLangStr(base::PythonClassLangStr::FromPyObj(label_obj).value());
    } else {
      b->SetText(g_base->python->GetPyLString(label_obj));
    }
  }
  if (on_activate_call_obj != Py_None) {
    b->SetOnActivateCall(on_activate_call_obj);
  }
  if (on_actions_complete_call_obj != Py_None) {
    b->SetOnActionsCompleteCall(on_actions_complete_call_obj);
  }

  if (down_widget_obj != Py_None) {
    down_widget = UIV1Python::GetPyWidget(down_widget_obj);
    if (!down_widget) {
      throw Exception("Invalid down widget.", PyExcType::kWidgetNotFound);
    }
    b->SetDownWidget(down_widget);
  }
  if (up_widget_obj != Py_None) {
    up_widget = UIV1Python::GetPyWidget(up_widget_obj);
    if (!up_widget) {
      throw Exception("Invalid up widget.", PyExcType::kWidgetNotFound);
    }
    b->SetUpWidget(up_widget);
  }
  if (autoselect_obj != Py_None) {
    b->set_auto_select(Python::GetBool(autoselect_obj));
  }
  if (left_widget_obj != Py_None) {
    left_widget = UIV1Python::GetPyWidget(left_widget_obj);
    if (!left_widget) {
      throw Exception("Invalid left widget.", PyExcType::kWidgetNotFound);
    }
    b->SetLeftWidget(left_widget);
  }
  if (right_widget_obj != Py_None) {
    right_widget = UIV1Python::GetPyWidget(right_widget_obj);
    if (!right_widget) {
      throw Exception("Invalid right widget.", PyExcType::kWidgetNotFound);
    }
    b->SetRightWidget(right_widget);
  }
  if (mesh_transparent_obj != Py_None) {
    b->SetMeshTransparent(
        &PythonClassUIMesh::FromPyObj(mesh_transparent_obj).mesh());
  }
  if (show_buffer_top_obj != Py_None) {
    b->set_show_buffer_top(Python::GetFloat(show_buffer_top_obj));
  }
  if (mesh_opaque_obj != Py_None) {
    b->SetMeshOpaque(&PythonClassUIMesh::FromPyObj(mesh_opaque_obj).mesh());
  }
  if (on_select_call_obj != Py_None) {
    b->SetOnSelectCall(on_select_call_obj);
  }
  if (selectable_obj != Py_None) {
    b->set_selectable(Python::GetBool(selectable_obj));
  }
  if (size_obj != Py_None) {
    Point2D p = Python::GetPoint2D(size_obj);
    b->set_width(p.x);
    b->set_height(p.y);
  }
  if (pos_obj != Py_None) {
    Point2D p = Python::GetPoint2D(pos_obj);
    b->set_translate(p.x, p.y);
  }
  if (scale_obj != Py_None) {
    b->set_scale(Python::GetFloat(scale_obj));
  }
  if (better_bg_fit_obj != Py_None) {
    b->set_better_bg_fit(Python::GetBool(better_bg_fit_obj));
  }
  if (icon_scale_obj != Py_None) {
    b->set_icon_scale(Python::GetFloat(icon_scale_obj));
  }
  if (icon_tint_obj != Py_None) {
    b->set_icon_tint(Python::GetFloat(icon_tint_obj));
  }
  if (icon_color_obj != Py_None) {
    std::vector<float> c = Python::GetFloats(icon_color_obj);
    if (c.size() != 3 && c.size() != 4) {
      throw Exception("Expected 3 or 4 floats for icon_color.",
                      PyExcType::kValue);
    }
    b->set_icon_color(c[0], c[1], c[2], (c.size() > 3) ? c[3] : 1.0f);
  }
  if (extra_touch_border_scale_obj != Py_None) {
    b->set_extra_touch_border_scale(
        Python::GetFloat(extra_touch_border_scale_obj));
  }
  if (texture_obj != Py_None) {
    b->SetTexture(&PythonClassUITexture::FromPyObj(texture_obj).texture());
  }
  if (mask_texture_obj != Py_None) {
    b->SetMaskTexture(
        &PythonClassUITexture::FromPyObj(mask_texture_obj).texture());
  }
  if (tint_texture_obj != Py_None) {
    b->SetTintTexture(
        &PythonClassUITexture::FromPyObj(tint_texture_obj).texture());
  }
  if (icon_obj != Py_None) {
    b->SetIcon(&PythonClassUITexture::FromPyObj(icon_obj).texture());
  }
  if (button_type_obj != Py_None) {
    std::string button_type = Python::GetString(button_type_obj);
    if (button_type == "back") {
      b->set_style(ButtonWidget::Style::kBack);
    } else if (button_type == "backSmall") {
      b->set_style(ButtonWidget::Style::kBackSmall);
    } else if (button_type == "regular") {
      b->set_style(ButtonWidget::Style::kRegular);
    } else if (button_type == "square") {
      b->set_style(ButtonWidget::Style::kSquare);
    } else if (button_type == "tab") {
      b->set_style(ButtonWidget::Style::kTab);
    } else if (button_type == "small") {
      b->set_style(ButtonWidget::Style::kSmall);
    } else if (button_type == "medium") {
      b->set_style(ButtonWidget::Style::kMedium);
    } else if (button_type == "large") {
      b->set_style(ButtonWidget::Style::kLarge);
    } else if (button_type == "larger") {
      b->set_style(ButtonWidget::Style::kLarger);
    } else if (button_type == "squareWide") {
      b->set_style(ButtonWidget::Style::kSquareWide);
    } else {
      throw Exception("Invalid button type: '" + button_type + "'.",
                      PyExcType::kValue);
    }
  }
  if (repeat_obj != Py_None) {
    b->set_repeat(Python::GetBool(repeat_obj));
  }
  if (color_obj != Py_None) {
    std::vector<float> c = Python::GetFloats(color_obj);
    if (c.size() != 3) {
      throw Exception("Expected 3 floats for color.", PyExcType::kValue);
    }
    b->set_color(c[0], c[1], c[2]);
  }
  if (textcolor_obj != Py_None) {
    std::vector<float> c = Python::GetFloats(textcolor_obj);
    if (c.size() != 3 && c.size() != 4) {
      throw Exception("Expected 3 or 4 floats for textcolor.",
                      PyExcType::kValue);
    }
    b->set_text_color(c[0], c[1], c[2], (c.size() > 3) ? c[3] : 1.0f);
  }
  if (tint_color_obj != Py_None) {
    std::vector<float> c = Python::GetFloats(tint_color_obj);
    if (c.size() != 3) {
      throw Exception("Expected 3 floats for tint_color.", PyExcType::kValue);
    }
    b->set_tint_color(c[0], c[1], c[2]);
  }
  if (tint2_color_obj != Py_None) {
    std::vector<float> c = Python::GetFloats(tint2_color_obj);
    if (c.size() != 3) {
      throw Exception("Expected 3 floats for tint2_color.", PyExcType::kValue);
    }
    b->set_tint2_color(c[0], c[1], c[2]);
  }
  if (tint3_color_obj != Py_None) {
    std::vector<float> c = Python::GetFloats(tint3_color_obj);
    if (c.size() != 3) {
      throw Exception("Expected 3 floats for tint3_color.", PyExcType::kValue);
    }
    b->set_tint3_color(c[0], c[1], c[2]);
  }
  if (text_flatness_obj != Py_None) {
    b->set_text_flatness(Python::GetFloat(text_flatness_obj));
  }
  if (text_scale_obj != Py_None) {
    b->set_text_scale(Python::GetFloat(text_scale_obj));
  }
  if (enable_sound_obj != Py_None) {
    b->set_enable_sound(Python::GetBool(enable_sound_obj));
  }
  if (transition_delay_obj != Py_None) {
    // We accept this as seconds; widget takes milliseconds.
    b->set_transition_delay(static_cast<millisecs_t>(
        1000.0f * Python::GetFloat(transition_delay_obj)));
  }
  if (transition_type_obj != Py_None) {
    std::string transition_type = Python::GetString(transition_type_obj);
    if (transition_type == "in_left") {
      b->set_transition_type(ButtonWidget::TransitionType::kInLeft);
    } else if (transition_type == "scale") {
      b->set_transition_type(ButtonWidget::TransitionType::kScale);
    } else {
      throw Exception("Invalid transition_type: '" + transition_type + "'.",
                      PyExcType::kValue);
    }
  }
  if (text_res_scale_obj != Py_None) {
    b->SetTextResScale(Python::GetFloat(text_res_scale_obj));
  }
  if (enabled_obj != Py_None) {
    b->SetEnabled(Python::GetBool(enabled_obj));
  }
  if (opacity_obj != Py_None) {
    b->set_opacity(Python::GetFloat(opacity_obj));
  }
  if (rotate_obj != Py_None) {
    b->set_rotate(Python::GetFloat(rotate_obj));
  }
  if (text_h_align_obj != Py_None) {
    std::string text_h_align = Python::GetString(text_h_align_obj);
    if (text_h_align == "left") {
      b->SetTextHAlign(TextWidget::HAlign::kLeft);
    } else if (text_h_align == "center") {
      b->SetTextHAlign(TextWidget::HAlign::kCenter);
    } else if (text_h_align == "right") {
      b->SetTextHAlign(TextWidget::HAlign::kRight);
    } else {
      throw Exception("Invalid text_h_align: '" + text_h_align + "'.",
                      PyExcType::kValue);
    }
  }
  if (accessory_obj != Py_None) {
    std::string accessory = Python::GetString(accessory_obj);
    if (accessory == "none") {
      b->SetAccessory(ButtonWidget::Accessory::kNone);
    } else if (accessory == "popup") {
      b->SetAccessory(ButtonWidget::Accessory::kPopup);
    } else {
      throw Exception("Invalid accessory: '" + accessory + "'.",
                      PyExcType::kValue);
    }
  }
  if (AnySet({depiction_obj, depiction_key_obj, depiction_h_align_obj,
              depiction_v_align_obj, depiction_debug_obj})) {
    ApplyDepictionArgs(&b->GetDepictionSlot(), depiction_obj, depiction_key_obj,
                       depiction_h_align_obj, depiction_v_align_obj,
                       depiction_debug_obj);
  }
  if (depiction_hit_area_obj != Py_None) {
    b->set_depiction_hit_area(Python::GetBool(depiction_hit_area_obj));
  }
  // If making a new widget add it at the end.
  if (edit_obj == Py_None) {
    g_ui_v1->AddWidget(b.get(), parent_widget);
  }

  // Run any calls built up by UI callbacks.
  ui_op_context.Finish();

  return b->NewPyRef();

  BA_PYTHON_CATCH;
}

static PyMethodDef PyButtonWidgetDef = {
    "buttonwidget",                // name
    (PyCFunction)PyButtonWidget,   // method
    METH_VARARGS | METH_KEYWORDS,  // flags

    "buttonwidget(*,\n"
    "  edit: bauiv1.Widget | None = None,\n"
    "  parent: bauiv1.Widget | None = None,\n"
    "  id: str | None = None,\n"
    "  size: Sequence[float] | None = None,\n"
    "  position: Sequence[float] | None = None,\n"
    "  on_activate_call: Callable | None = None,\n"
    "  label: str | bauiv1.Lstr | bauiv1.LangStr | None = None,\n"
    "  color: Sequence[float] | None = None,\n"
    "  down_widget: bauiv1.Widget | None = None,\n"
    "  up_widget: bauiv1.Widget | None = None,\n"
    "  left_widget: bauiv1.Widget | None = None,\n"
    "  right_widget: bauiv1.Widget | None = None,\n"
    "  texture: bauiv1.Texture | None = None,\n"
    "  text_scale: float | None = None,\n"
    "  textcolor: Sequence[float] | None = None,\n"
    "  enable_sound: bool | None = None,\n"
    "  mesh_transparent: bauiv1.Mesh | None = None,\n"
    "  mesh_opaque: bauiv1.Mesh | None = None,\n"
    "  repeat: bool | None = None,\n"
    "  scale: float | None = None,\n"
    "  transition_delay: float | None = None,\n"
    "  on_select_call: Callable | None = None,\n"
    "  button_type: str | None = None,\n"
    "  extra_touch_border_scale: float | None = None,\n"
    "  selectable: bool | None = None,\n"
    "  show_buffer_top: float | None = None,\n"
    "  icon: bauiv1.Texture | None = None,\n"
    "  iconscale: float | None = None,\n"
    "  icon_tint: float | None = None,\n"
    "  icon_color: Sequence[float] | None = None,\n"
    "  autoselect: bool | None = None,\n"
    "  mask_texture: bauiv1.Texture | None = None,\n"
    "  tint_texture: bauiv1.Texture | None = None,\n"
    "  tint_color: Sequence[float] | None = None,\n"
    "  tint2_color: Sequence[float] | None = None,\n"
    "  text_flatness: float | None = None,\n"
    "  text_res_scale: float | None = None,\n"
    "  enabled: bool | None = None,\n"
    "  text_literal: bool | None = None,\n"
    "  opacity: float | None = None,\n"
    "  rotate: float | None = None,\n"
    "  better_bg_fit: bool | None = None,\n"
    "  transition_type: Literal['in_left', 'scale'] | None = None,\n"
    "  query: bauiv1.Widget | None = None,\n"
    "  on_actions_complete_call: Callable[[], None] | None = None,\n"
    "  text_h_align: Literal['left', 'center', 'right'] | None = None,\n"
    "  accessory: Literal['none', 'popup'] | None = None,\n"
    "  depiction: str | None = None,\n"
    "  depiction_key: str | None = None,\n"
    "  depiction_h_align: Literal['left', 'center', 'right'] | None = None,\n"
    "  depiction_v_align: Literal['top', 'center', 'bottom'] | None = None,\n"
    "  depiction_hit_area: bool | None = None,\n"
    "  depiction_debug: bool | None = None,\n"
    "  tint3_color: Sequence[float] | None = None,\n"
    ") -> bauiv1.Widget\n"
    "\n"
    "Create or edit a button widget.\n"
    "\n"
    "Pass a valid existing bauiv1.Widget as 'edit' to modify it; otherwise\n"
    "a new one is created and returned. Arguments that are not set to None\n"
    "are applied to the Widget.\n"
    "\n"
    "Pass a button as 'query' to instead return its current label text as\n"
    "a str (the translated form when the label is a language-string). This\n"
    "mirrors textwidget's 'query' and is the only way to read a label that\n"
    "was set directly on the button rather than via a separate overlaid\n"
    "text widget.\n"
    "\n"
    "'on_actions_complete_call' runs once after a press sequence that\n"
    "activated the button is over: right after the activation for a\n"
    "normal press or a key/controller press, and on release after the\n"
    "last repeat of a held 'repeat' button. Use it to react to every\n"
    "activation cheaply in 'on_activate_call' and do something costly\n"
    "(a server round trip, say) only once at the end.\n"
    "\n"
    "'text_h_align' places the label: centered (the default) or hugging\n"
    "the left or right edge. 'accessory' draws a small indicator at the\n"
    "right edge saying what a press does ('popup': opens a menu of\n"
    "choices); the label's space shrinks to make room for it.\n"
    "\n"
    "A button with 'enabled' False draws greyed out and can't be\n"
    "activated, but remains selectable (if it otherwise would be), so\n"
    "navigation around it is unaffected; a tap selects it, and a tap or\n"
    "activation that would have fired it plays an error sound instead.\n"
    "\n"
    "A button can show a depiction (a json-serialized\n"
    ":class:`bacommon.depiction.Depiction`) as its body, in place of its\n"
    "texture or standard look (pass an empty string to go back); the\n"
    "label and icon still draw over it. The depiction flashes, pulses\n"
    "and greys out with the button, and never takes its presses. The\n"
    "depiction args work as for :func:`bauiv1.imagewidget`. To show one\n"
    "elsewhere on a button, use an image with the button as its\n"
    "``draw_controller``. With ``depiction_hit_area`` set, mouse and\n"
    "touch only land on the button where its depiction actually draws\n"
    "(an icon hugging one end of a wide button, say), grown to a\n"
    "minimum size so small ones stay easy to tap; keyboard and\n"
    "controller selection are unaffected.",
};

// --------------------------- checkboxwidget ----------------------------------

static auto PyCheckBoxWidget(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  PyObject* size_obj{Py_None};
  PyObject* id_obj{Py_None};
  PyObject* pos_obj{Py_None};
  PyObject* text_obj{Py_None};
  PyObject* value_obj{Py_None};
  PyObject* on_value_change_call_obj{Py_None};
  PyObject* on_select_call_obj{Py_None};
  PyObject* scale_obj{Py_None};
  PyObject* is_radio_button_obj{Py_None};
  PyObject* maxwidth_obj{Py_None};
  PyObject* parent_obj{Py_None};
  PyObject* edit_obj{Py_None};
  ContainerWidget* parent_widget{};
  PyObject* text_scale_obj{Py_None};
  PyObject* textcolor_obj{Py_None};
  PyObject* autoselect_obj{Py_None};
  PyObject* color_obj{Py_None};
  PyObject* style_obj{Py_None};
  PyObject* transition_delay_obj{Py_None};
  PyObject* transition_type_obj{Py_None};
  PyObject* enabled_obj{Py_None};

  static const char* kwlist[] = {"edit",
                                 "parent",
                                 "id",
                                 "size",
                                 "position",
                                 "text",
                                 "value",
                                 "on_value_change_call",
                                 "on_select_call",
                                 "text_scale",
                                 "textcolor",
                                 "scale",
                                 "is_radio_button",
                                 "maxwidth",
                                 "autoselect",
                                 "color",
                                 "style",
                                 "transition_delay",
                                 "transition_type",
                                 "enabled",
                                 nullptr};
  if (!PyArg_ParseTupleAndKeywords(
          args, keywds, "|OOOOOOOOOOOOOOOOOOOO", const_cast<char**>(kwlist),
          &edit_obj, &parent_obj, &id_obj, &size_obj, &pos_obj, &text_obj,
          &value_obj, &on_value_change_call_obj, &on_select_call_obj,
          &text_scale_obj, &textcolor_obj, &scale_obj, &is_radio_button_obj,
          &maxwidth_obj, &autoselect_obj, &color_obj, &style_obj,
          &transition_delay_obj, &transition_type_obj, &enabled_obj)) {
    return nullptr;
  }

  if (!g_base->CurrentContext().IsEmpty()) {
    throw Exception("UI functions must be called with no context set.");
  }

  // Gather up any user code triggered by this stuff and run it at the end
  // before we return.
  base::UI::OperationContext ui_op_context;

  // Grab the edited widget or create a new one.
  Object::Ref<CheckBoxWidget> widget;
  if (edit_obj != Py_None) {
    widget = dynamic_cast<CheckBoxWidget*>(UIV1Python::GetPyWidget(edit_obj));
    if (!widget.exists()) {
      throw Exception("Invalid or nonexistent widget.",
                      PyExcType::kWidgetNotFound);
    }
  } else {
    parent_widget = parent_obj == Py_None
                        ? g_ui_v1->screen_root_widget()
                        : dynamic_cast<ContainerWidget*>(
                              UIV1Python::GetPyWidget(parent_obj));
    if (parent_widget == nullptr) {
      throw Exception("Parent widget nonexistent or not a container.",
                      PyExcType::kWidgetNotFound);
    }
    widget = Object::New<CheckBoxWidget>();
  }

  // Set applicable values.
  if (id_obj != Py_None) {
    widget->SetID(Python::GetString(id_obj));
  }
  if (size_obj != Py_None) {
    Point2D p = Python::GetPoint2D(size_obj);
    widget->SetWidth(p.x);
    widget->SetHeight(p.y);
  }
  if (pos_obj != Py_None) {
    Point2D p = Python::GetPoint2D(pos_obj);
    widget->set_translate(p.x, p.y);
  }
  if (autoselect_obj != Py_None) {
    widget->set_auto_select(Python::GetBool(autoselect_obj));
  }
  if (text_obj != Py_None) {
    // Native language-strings stay structured (retained +
    // re-evaluated on language changes; see the textwidget analog).
    if (base::PythonClassLangStr::Check(text_obj)) {
      widget->SetLangStr(base::PythonClassLangStr::FromPyObj(text_obj).value());
    } else {
      widget->SetText(g_base->python->GetPyLString(text_obj));
    }
  }
  if (value_obj != Py_None) {
    widget->SetValue(Python::GetBool(value_obj));
  }
  if (color_obj != Py_None) {
    std::vector<float> c = Python::GetFloats(color_obj);
    if (c.size() != 3)
      throw Exception("Expected 3 floats for color.", PyExcType::kValue);
    widget->set_color(c[0], c[1], c[2]);
  }
  if (maxwidth_obj != Py_None) {
    widget->SetMaxWidth(Python::GetFloat(maxwidth_obj));
  }
  if (is_radio_button_obj != Py_None) {
    widget->SetIsRadioButton(Python::GetBool(is_radio_button_obj));
  }
  if (enabled_obj != Py_None) {
    widget->SetEnabled(Python::GetBool(enabled_obj));
  }
  if (style_obj != Py_None) {
    auto style_s = Python::GetString(style_obj);
    CheckBoxWidget::Style style;
    if (style_s == "default") {
      style = CheckBoxWidget::Style::kDefault;
    } else if (style_s == "right") {
      style = CheckBoxWidget::Style::kRight;
    } else {
      throw Exception("Invalid style: " + style_s, PyExcType::kValue);
    }
    widget->SetStyle(style);
  }
  if (scale_obj != Py_None) {
    widget->set_scale(Python::GetFloat(scale_obj));
  }
  if (on_value_change_call_obj != Py_None) {
    widget->SetOnValueChangeCall(on_value_change_call_obj);
  }
  if (on_select_call_obj != Py_None) {
    widget->SetOnSelectCall(on_select_call_obj);
  }
  if (text_scale_obj != Py_None) {
    widget->SetTextScale(Python::GetFloat(text_scale_obj));
  }
  if (textcolor_obj != Py_None) {
    std::vector<float> c = Python::GetFloats(textcolor_obj);
    if (c.size() != 3 && c.size() != 4) {
      throw Exception("Expected 3 or 4 float values for textcolor.",
                      PyExcType::kValue);
    }
    if (c.size() == 3) {
      widget->set_text_color(c[0], c[1], c[2], 1.0f);
    } else {
      widget->set_text_color(c[0], c[1], c[2], c[3]);
    }
  }
  if (transition_delay_obj != Py_None) {
    widget->set_transition_delay(static_cast<millisecs_t>(
        1000.0f * Python::GetFloat(transition_delay_obj)));
  }
  if (transition_type_obj != Py_None) {
    std::string transition_type = Python::GetString(transition_type_obj);
    if (transition_type == "in_left") {
      widget->set_transition_type(CheckBoxWidget::TransitionType::kInLeft);
    } else if (transition_type == "scale") {
      widget->set_transition_type(CheckBoxWidget::TransitionType::kScale);
    } else {
      throw Exception("Invalid transition_type: '" + transition_type + "'.",
                      PyExcType::kValue);
    }
  }

  // if making a new widget add it at the end
  if (edit_obj == Py_None) {
    g_ui_v1->AddWidget(widget.get(), parent_widget);
  }

  // Run any calls built up by UI callbacks.
  ui_op_context.Finish();

  return widget->NewPyRef();

  BA_PYTHON_CATCH;
}

static PyMethodDef PyCheckBoxWidgetDef = {
    "checkboxwidget",               // name
    (PyCFunction)PyCheckBoxWidget,  // method
    METH_VARARGS | METH_KEYWORDS,   // flags

    "checkboxwidget(*,\n"
    "  edit: bauiv1.Widget | None = None,\n"
    "  parent: bauiv1.Widget | None = None,\n"
    "  id: str | None = None,\n"
    "  size: Sequence[float] | None = None,\n"
    "  position: Sequence[float] | None = None,\n"
    "  text: str | bauiv1.Lstr | bauiv1.LangStr | None = None,\n"
    "  value: bool | None = None,\n"
    "  on_value_change_call: Callable[[bool], None] | None = None,\n"
    "  on_select_call: Callable[[], None] | None = None,\n"
    "  text_scale: float | None = None,\n"
    "  textcolor: Sequence[float] | None = None,\n"
    "  scale: float | None = None,\n"
    "  is_radio_button: bool | None = None,\n"
    "  maxwidth: float | None = None,\n"
    "  autoselect: bool | None = None,\n"
    "  color: Sequence[float] | None = None,\n"
    "  style: Literal['default', 'right'] | None = None,\n"
    "  transition_delay: float | None = None,\n"
    "  transition_type: Literal['in_left', 'scale'] | None = None,\n"
    "  enabled: bool | None = None,\n"
    ") -> bauiv1.Widget\n"
    "\n"
    "Create or edit a check-box widget.\n"
    "\n"
    "Pass a valid existing bauiv1.Widget as 'edit' to modify it; otherwise\n"
    "a new one is created and returned. Arguments that are not set to None\n"
    "are applied to the Widget.\n"
    "\n"
    "The ``'default'`` style places the box at the left with text\n"
    "following it. The ``'right'`` style places text at the left bounds\n"
    "of the widget and the box at the right bounds, and uses a uniform\n"
    "selection glow. In that style the text is always fit to the space\n"
    "left of the box, so ``maxwidth`` is unnecessary (if passed, it can\n"
    "only shrink the text further).\n"
    "\n"
    "A check box with ``enabled`` False draws greyed out and can't be\n"
    "toggled, but remains selectable, so navigation around it is\n"
    "unaffected; a tap selects it, and a tap or activation that would\n"
    "have toggled it plays an error sound instead.",
};

// ----------------------------- imagewidget -----------------------------------

static auto PyImageWidget(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  PyObject* size_obj{Py_None};
  PyObject* pos_obj{Py_None};
  PyObject* texture_obj{Py_None};
  PyObject* tint_texture_obj{Py_None};
  ContainerWidget* parent_widget{};
  PyObject* parent_obj{Py_None};
  PyObject* edit_obj{Py_None};
  PyObject* color_obj{Py_None};
  PyObject* tint_color_obj{Py_None};
  PyObject* tint2_color_obj{Py_None};
  PyObject* opacity_obj{Py_None};
  PyObject* rotate_obj{Py_None};
  PyObject* mesh_transparent_obj{Py_None};
  PyObject* mesh_opaque_obj{Py_None};
  PyObject* has_alpha_channel_obj{Py_None};
  PyObject* transition_delay_obj{Py_None};
  PyObject* draw_controller_obj{Py_None};
  PyObject* tilt_scale_obj{Py_None};
  PyObject* mask_texture_obj{Py_None};
  PyObject* radial_amount_obj{Py_None};
  PyObject* draw_controller_mult_obj{Py_None};
  PyObject* depth_range_obj{Py_None};
  PyObject* transition_type_obj{Py_None};
  PyObject* match_backing_glow_obj{Py_None};
  PyObject* depiction_obj{Py_None};
  PyObject* depiction_key_obj{Py_None};
  PyObject* depiction_h_align_obj{Py_None};
  PyObject* depiction_v_align_obj{Py_None};
  PyObject* depiction_take_input_obj{Py_None};
  PyObject* depiction_frame_color_obj{Py_None};
  PyObject* depiction_backing_color_obj{Py_None};
  PyObject* depiction_debug_obj{Py_None};
  PyObject* tint3_color_obj{Py_None};
  PyObject* nine_patch_insets_obj{Py_None};
  PyObject* nine_patch_borders_obj{Py_None};
  PyObject* nine_patch_tile_obj{Py_None};

  static const char* kwlist[] = {"edit",
                                 "parent",
                                 "size",
                                 "position",
                                 "color",
                                 "texture",
                                 "opacity",
                                 "rotate",
                                 "mesh_transparent",
                                 "mesh_opaque",
                                 "has_alpha_channel",
                                 "tint_texture",
                                 "tint_color",
                                 "transition_delay",
                                 "draw_controller",
                                 "tint2_color",
                                 "tilt_scale",
                                 "mask_texture",
                                 "radial_amount",
                                 "draw_controller_mult",
                                 "depth_range",
                                 "transition_type",
                                 "match_backing_glow",
                                 "depiction",
                                 "depiction_key",
                                 "depiction_h_align",
                                 "depiction_v_align",
                                 "depiction_take_input",
                                 "depiction_frame_color",
                                 "depiction_backing_color",
                                 "depiction_debug",
                                 "tint3_color",
                                 "nine_patch_insets",
                                 "nine_patch_borders",
                                 "nine_patch_tile",
                                 nullptr};
  if (!PyArg_ParseTupleAndKeywords(
          args, keywds, "|OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO",
          const_cast<char**>(kwlist), &edit_obj, &parent_obj, &size_obj,
          &pos_obj, &color_obj, &texture_obj, &opacity_obj, &rotate_obj,
          &mesh_transparent_obj, &mesh_opaque_obj, &has_alpha_channel_obj,
          &tint_texture_obj, &tint_color_obj, &transition_delay_obj,
          &draw_controller_obj, &tint2_color_obj, &tilt_scale_obj,
          &mask_texture_obj, &radial_amount_obj, &draw_controller_mult_obj,
          &depth_range_obj, &transition_type_obj, &match_backing_glow_obj,
          &depiction_obj, &depiction_key_obj, &depiction_h_align_obj,
          &depiction_v_align_obj, &depiction_take_input_obj,
          &depiction_frame_color_obj, &depiction_backing_color_obj,
          &depiction_debug_obj, &tint3_color_obj, &nine_patch_insets_obj,
          &nine_patch_borders_obj, &nine_patch_tile_obj))
    return nullptr;

  if (!g_base->CurrentContext().IsEmpty()) {
    throw Exception("UI functions must be called with no context set.");
  }

  // Gather up any user code triggered by this stuff and run it at the end
  // before we return.
  base::UI::OperationContext ui_op_context;

  // Grab the edited widget or create a new one.
  Object::Ref<ImageWidget> b;
  if (edit_obj != Py_None) {
    b = dynamic_cast<ImageWidget*>(UIV1Python::GetPyWidget(edit_obj));
    if (!b.exists())
      throw Exception("Invalid or nonexistent widget.",
                      PyExcType::kWidgetNotFound);
  } else {
    parent_widget = parent_obj == Py_None
                        ? g_ui_v1->screen_root_widget()
                        : dynamic_cast<ContainerWidget*>(
                              UIV1Python::GetPyWidget(parent_obj));
    if (parent_widget == nullptr) {
      throw Exception("Parent widget nonexistent or not a container.",
                      PyExcType::kWidgetNotFound);
    }
    b = Object::New<ImageWidget>();
  }
  if (size_obj != Py_None) {
    Point2D p = Python::GetPoint2D(size_obj);
    b->set_width(p.x);
    b->set_height(p.y);
  }
  if (texture_obj != Py_None) {
    b->SetTexture(&PythonClassUITexture::FromPyObj(texture_obj).texture());
  }
  if (tint_texture_obj != Py_None) {
    b->SetTintTexture(
        &PythonClassUITexture::FromPyObj(tint_texture_obj).texture());
  }
  if (mask_texture_obj != Py_None) {
    b->SetMaskTexture(
        &PythonClassUITexture::FromPyObj(mask_texture_obj).texture());
  }
  if (mesh_opaque_obj != Py_None) {
    b->SetMeshOpaque(&PythonClassUIMesh::FromPyObj(mesh_opaque_obj).mesh());
  }
  if (mesh_transparent_obj != Py_None) {
    b->SetMeshTransparent(
        &PythonClassUIMesh::FromPyObj(mesh_transparent_obj).mesh());
  }
  if (draw_controller_obj != Py_None) {
    auto* dcw = UIV1Python::GetPyWidget(draw_controller_obj);
    if (!dcw) {
      throw Exception("Invalid or nonexistent draw-controller widget.",
                      PyExcType::kWidgetNotFound);
    }
    b->set_draw_control_parent(dcw);
  }
  if (has_alpha_channel_obj != Py_None) {
    b->set_has_alpha_channel(Python::GetBool(has_alpha_channel_obj));
  }
  if (opacity_obj != Py_None) {
    b->set_opacity(Python::GetFloat(opacity_obj));
  }
  if (rotate_obj != Py_None) {
    b->set_rotate(Python::GetFloat(rotate_obj));
  }
  if (match_backing_glow_obj != Py_None) {
    b->set_match_backing_glow(Python::GetBool(match_backing_glow_obj));
  }
  if (radial_amount_obj != Py_None) {
    b->set_radial_amount(Python::GetFloat(radial_amount_obj));
  }
  if (pos_obj != Py_None) {
    Point2D p = Python::GetPoint2D(pos_obj);
    b->set_translate(p.x, p.y);
  }
  if (transition_delay_obj != Py_None) {
    // We accept this as seconds; widget takes milliseconds.
    b->set_transition_delay(1000.0f * Python::GetFloat(transition_delay_obj));
  }
  if (transition_type_obj != Py_None) {
    std::string transition_type = Python::GetString(transition_type_obj);
    if (transition_type == "in_left") {
      b->set_transition_type(ImageWidget::TransitionType::kInLeft);
    } else if (transition_type == "scale") {
      b->set_transition_type(ImageWidget::TransitionType::kScale);
    } else {
      throw Exception("Invalid transition_type: '" + transition_type + "'.",
                      PyExcType::kValue);
    }
  }
  if (color_obj != Py_None) {
    std::vector<float> c = Python::GetFloats(color_obj);
    if (c.size() != 3) {
      throw Exception("Expected 3 floats for color.", PyExcType::kValue);
    }
    b->set_color(c[0], c[1], c[2]);
  }
  if (tint_color_obj != Py_None) {
    std::vector<float> c = Python::GetFloats(tint_color_obj);
    if (c.size() != 3) {
      throw Exception("Expected 3 floats for tint_color.", PyExcType::kValue);
    }
    b->set_tint_color(c[0], c[1], c[2]);
  }
  if (tint2_color_obj != Py_None) {
    std::vector<float> c = Python::GetFloats(tint2_color_obj);
    if (c.size() != 3) {
      throw Exception("Expected 3 floats for tint2_color.", PyExcType::kValue);
    }
    b->set_tint2_color(c[0], c[1], c[2]);
  }
  if (tint3_color_obj != Py_None) {
    std::vector<float> c = Python::GetFloats(tint3_color_obj);
    if (c.size() != 3) {
      throw Exception("Expected 3 floats for tint3_color.", PyExcType::kValue);
    }
    b->set_tint3_color(c[0], c[1], c[2]);
  }
  if (nine_patch_insets_obj != Py_None || nine_patch_borders_obj != Py_None
      || nine_patch_tile_obj != Py_None) {
    if (nine_patch_insets_obj == Py_None || nine_patch_borders_obj == Py_None) {
      throw Exception(
          "nine_patch_insets and nine_patch_borders must be passed together"
          " (and with them any nine_patch_tile).",
          PyExcType::kValue);
    }
    std::vector<float> insets = Python::GetFloats(nine_patch_insets_obj);
    std::vector<float> borders = Python::GetFloats(nine_patch_borders_obj);
    if (insets.size() != 4 || borders.size() != 4) {
      throw Exception(
          "Expected 4 floats each for nine_patch_insets and"
          " nine_patch_borders.",
          PyExcType::kValue);
    }
    bool tile_h{};
    bool tile_v{};
    if (nine_patch_tile_obj != Py_None) {
      if (!PySequence_Check(nine_patch_tile_obj)
          || PySequence_Size(nine_patch_tile_obj) != 2) {
        throw Exception("Expected 2 bools for nine_patch_tile.",
                        PyExcType::kValue);
      }
      auto tile_h_obj =
          PythonRef::Stolen(PySequence_GetItem(nine_patch_tile_obj, 0));
      auto tile_v_obj =
          PythonRef::Stolen(PySequence_GetItem(nine_patch_tile_obj, 1));
      tile_h = Python::GetBool(tile_h_obj.get());
      tile_v = Python::GetBool(tile_v_obj.get());
    }
    b->SetNinePatch(insets.data(), borders.data(), tile_h, tile_v);
  }
  if (tilt_scale_obj != Py_None) {
    b->set_tilt_scale(Python::GetFloat(tilt_scale_obj));
  }
  if (draw_controller_mult_obj != Py_None) {
    b->set_draw_controller_mult(Python::GetFloat(draw_controller_mult_obj));
  }
  if (depth_range_obj != Py_None) {
    auto depth_range = Python::GetFloats(depth_range_obj);
    if (depth_range.size() != 2) {
      throw Exception("Expected 2 float values.", PyExcType::kValue);
    }
    if (depth_range[0] < 0.0f || depth_range[1] > 1.0f
        || depth_range[1] <= depth_range[0]) {
      throw Exception(
          "Invalid depth range values;"
          " values must be between 0 and 1 and second value must be larger "
          "than first.",
          PyExcType::kValue);
    }
    b->set_depth_range(depth_range[0], depth_range[1]);
  }
  if (AnySet({depiction_obj, depiction_key_obj, depiction_h_align_obj,
              depiction_v_align_obj, depiction_take_input_obj,
              depiction_frame_color_obj, depiction_backing_color_obj,
              depiction_debug_obj})) {
    DepictionSlot& slot{b->GetDepictionSlot()};
    if (depiction_take_input_obj != Py_None) {
      slot.set_take_input(Python::GetBool(depiction_take_input_obj));
    }
    if (depiction_frame_color_obj != Py_None) {
      std::vector<float> c = Python::GetFloats(depiction_frame_color_obj);
      if (c.size() != 3) {
        throw Exception("Expected 3 floats for depiction_frame_color.",
                        PyExcType::kValue);
      }
      slot.set_frame_color(c[0], c[1], c[2]);
    }
    if (depiction_backing_color_obj != Py_None) {
      std::vector<float> c = Python::GetFloats(depiction_backing_color_obj);
      if (c.size() != 3) {
        throw Exception("Expected 3 floats for depiction_backing_color.",
                        PyExcType::kValue);
      }
      slot.set_backing_color(c[0], c[1], c[2]);
    }
    ApplyDepictionArgs(&slot, depiction_obj, depiction_key_obj,
                       depiction_h_align_obj, depiction_v_align_obj,
                       depiction_debug_obj);
  }
  // if making a new widget add it at the end
  if (edit_obj == Py_None) {
    g_ui_v1->AddWidget(b.get(), parent_widget);
  }

  // Run any calls built up by UI callbacks.
  ui_op_context.Finish();

  return b->NewPyRef();
  BA_PYTHON_CATCH;
}

static PyMethodDef PyImageWidgetDef = {
    "imagewidget",                 // name
    (PyCFunction)PyImageWidget,    // method
    METH_VARARGS | METH_KEYWORDS,  // flags

    "imagewidget(*,\n"
    "  edit: bauiv1.Widget | None = None,\n"
    "  parent: bauiv1.Widget | None = None,\n"
    "  size: Sequence[float] | None = None,\n"
    "  position: Sequence[float] | None = None,\n"
    "  color: Sequence[float] | None = None,\n"
    "  texture: bauiv1.Texture | None = None,\n"
    "  opacity: float | None = None,\n"
    "  rotate: float | None = None,\n"
    "  mesh_transparent: bauiv1.Mesh | None = None,\n"
    "  mesh_opaque: bauiv1.Mesh | None = None,\n"
    "  has_alpha_channel: bool = True,\n"
    "  tint_texture: bauiv1.Texture | None = None,\n"
    "  tint_color: Sequence[float] | None = None,\n"
    "  transition_delay: float | None = None,\n"
    "  draw_controller: bauiv1.Widget | None = None,\n"
    "  tint2_color: Sequence[float] | None = None,\n"
    "  tilt_scale: float | None = None,\n"
    "  mask_texture: bauiv1.Texture | None = None,\n"
    "  radial_amount: float | None = None,\n"
    "  draw_controller_mult: float | None = None,\n"
    "  depth_range: tuple[float, float] | None = None,\n"
    "  transition_type: Literal['in_left', 'scale'] | None = None,\n"
    "  match_backing_glow: bool | None = None,\n"
    "  depiction: str | None = None,\n"
    "  depiction_key: str | None = None,\n"
    "  depiction_h_align: Literal['left', 'center', 'right'] | None = None,\n"
    "  depiction_v_align: Literal['top', 'center', 'bottom'] | None = None,\n"
    "  depiction_take_input: bool | None = None,\n"
    "  depiction_frame_color: Sequence[float] | None = None,\n"
    "  depiction_backing_color: Sequence[float] | None = None,\n"
    "  depiction_debug: bool | None = None,\n"
    "  tint3_color: Sequence[float] | None = None,\n"
    "  nine_patch_insets: Sequence[float] | None = None,\n"
    "  nine_patch_borders: Sequence[float] | None = None,\n"
    "  nine_patch_tile: Sequence[bool] | None = None,\n"
    ") -> bauiv1.Widget\n"
    "\n"
    "Create or edit an image widget.\n"
    "\n"
    "Pass a valid existing bauiv1.Widget as 'edit' to modify it; otherwise\n"
    "a new one is created and returned. Arguments that are not set to None\n"
    "are applied to the Widget.\n"
    "\n"
    "Set ``match_backing_glow`` on images drawn to blend into their\n"
    "parent window's backing; their color then follows the backing's\n"
    "brief glow as the window scales in (only the direct parent is\n"
    "consulted).\n"
    "\n"
    "Pass ``nine_patch_insets`` and ``nine_patch_borders`` together to\n"
    "draw the texture as a 9-patch filling the image's box exactly:\n"
    "the insets say where the texture splits into corners, edges and\n"
    "middle (fractions of its width/height from the left, bottom,\n"
    "right and top), the borders how big those edges draw (in the\n"
    "image's own units, same order; a pair too big for the box shrinks\n"
    "to fit). ``nine_patch_tile`` (horizontal, vertical) repeats the\n"
    "middle at the corners' scale, fitted to a whole number of copies,\n"
    "rather than stretching it; its art must tile seamlessly. Tint,\n"
    "mask and color textures share the 9-patch's layout.\n"
    "\n"
    "An image can show a depiction -- a json-serialized\n"
    ":class:`bacommon.depiction.Depiction` (a character's icon, a name,\n"
    "an image, a live 3d character, ...) -- in place of its texture\n"
    "(pass an empty string to go back to the texture). One with a shape\n"
    "of its own is fitted inside the image's box by\n"
    "``depiction_h_align``/``depiction_v_align``; one without fills it.\n"
    "Art that isn't local yet shows a standin and upgrades in place once\n"
    "it arrives; a kind this build can't draw shows a placeholder (an\n"
    "outlined box with a question mark). An unchanged depiction is kept\n"
    "as is. The image's opacity, transitions, ``mask_texture`` and\n"
    "``draw_controller`` apply to it, so one sitting on a button dims,\n"
    "highlights and greys out with it.\n"
    "\n"
    "``depiction_key`` names what the image shows (unique to it by\n"
    "default): depictions with something long-lived behind them, like a\n"
    "live viewer, carry on with it when given a new depiction under the\n"
    "same key -- including by a new widget, as when a window is rebuilt.\n"
    "Set it before (or along with) the depiction it applies to.\n"
    "\n"
    "Images take no input; with ``depiction_take_input`` set, presses\n"
    "and drags go to depictions that take some (a live viewer's).\n"
    "``depiction_backing_color`` draws beneath the depiction (all that\n"
    "shows while there is none), cut by ``mask_texture``, whose green\n"
    "channel adds a frame in ``depiction_frame_color``; a live viewer's\n"
    "picture honors the mask too. ``depiction_debug`` tints the box the\n"
    "depiction reports covering (what a hit-tested button takes presses\n"
    "over), to check it against what is drawn. See also\n"
    "``get_depiction_control()``.",
};

// ------------------------- get_depiction_control -----------------------------

static auto PyGetDepictionControl(PyObject* self, PyObject* args,
                                  PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  PyObject* widget_obj{};
  static const char* kwlist[] = {"widget", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "O",
                                   const_cast<char**>(kwlist), &widget_obj)) {
    return nullptr;
  }
  Widget* widget = UIV1Python::GetPyWidget(widget_obj);
  DepictionSlot* slot{};
  if (auto* image = dynamic_cast<ImageWidget*>(widget)) {
    slot = image->depiction_slot();
  } else if (auto* button = dynamic_cast<ButtonWidget*>(widget)) {
    slot = button->depiction_slot();
  } else {
    throw Exception("Invalid or nonexistent image or button widget.",
                    PyExcType::kWidgetNotFound);
  }
  PyObject* control = slot ? slot->GetPythonControl() : nullptr;
  if (control == nullptr) {
    Py_RETURN_NONE;
  }
  Py_INCREF(control);
  return control;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyGetDepictionControlDef = {
    "get_depiction_control",             // name
    (PyCFunction)PyGetDepictionControl,  // method
    METH_VARARGS | METH_KEYWORDS,        // flags

    "get_depiction_control(widget: bauiv1.Widget) -> bauiv1.Viewer | None\n"
    "\n"
    "Get the object for driving an image's or button's depiction.\n"
    "\n"
    "Some depictions have a live object behind them whose methods adjust\n"
    "what is shown locally, without a new depiction from the server --\n"
    "a live character viewer is its :class:`bauiv1.Viewer`, for\n"
    "instance (a slider could recolor its character as it moves).\n"
    "Returns None for depictions offering nothing (or not yet shown;\n"
    "live objects are made the first time a depiction is drawn). What\n"
    "is shown remains the server's to decide: the next depiction it\n"
    "sends replaces local tweaks. Don't hold the object long; a\n"
    "depiction can be replaced at any time.\n"
    "\n"
    ":meta private:",
};

// ---------------------------- spinnerwidget ----------------------------------

static auto PySpinnerWidget(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  PyObject* edit_obj{Py_None};
  PyObject* parent_obj{Py_None};
  ContainerWidget* parent_widget{};
  PyObject* size_obj{Py_None};
  PyObject* pos_obj{Py_None};
  PyObject* visible_obj{Py_None};
  PyObject* style_obj{Py_None};
  PyObject* fade_obj{Py_None};
  PyObject* fade_delay_obj{Py_None};
  PyObject* fade_duration_obj{Py_None};

  static const char* kwlist[] = {
      "edit",  "parent", "size",       "position",      "visible",
      "style", "fade",   "fade_delay", "fade_duration", nullptr};
  if (!PyArg_ParseTupleAndKeywords(
          args, keywds, "|OOOOOOOOO", const_cast<char**>(kwlist), &edit_obj,
          &parent_obj, &size_obj, &pos_obj, &visible_obj, &style_obj, &fade_obj,
          &fade_delay_obj, &fade_duration_obj))
    return nullptr;

  if (!g_base->CurrentContext().IsEmpty()) {
    throw Exception("UI functions must be called with no context set.");
  }

  // Gather up any user code triggered by this stuff and run it at the end
  // before we return.
  base::UI::OperationContext ui_op_context;

  // Grab the edited widget or create a new one.
  Object::Ref<SpinnerWidget> b;
  if (edit_obj != Py_None) {
    b = dynamic_cast<SpinnerWidget*>(UIV1Python::GetPyWidget(edit_obj));
    if (!b.exists())
      throw Exception("Invalid or nonexistent widget.",
                      PyExcType::kWidgetNotFound);
  } else {
    parent_widget = parent_obj == Py_None
                        ? g_ui_v1->screen_root_widget()
                        : dynamic_cast<ContainerWidget*>(
                              UIV1Python::GetPyWidget(parent_obj));
    if (parent_widget == nullptr) {
      throw Exception("Parent widget nonexistent or not a container.",
                      PyExcType::kWidgetNotFound);
    }
    b = Object::New<SpinnerWidget>();
  }
  if (size_obj != Py_None) {
    auto size{Python::GetFloat(size_obj)};
    b->set_size(size);
  }
  if (pos_obj != Py_None) {
    Point2D p = Python::GetPoint2D(pos_obj);
    b->set_translate(p.x, p.y);
  }
  if (visible_obj != Py_None) {
    b->set_visible(Python::GetBool(visible_obj));
  }
  if (fade_obj != Py_None) {
    b->set_fade(Python::GetBool(fade_obj));
  }
  if (fade_delay_obj != Py_None) {
    b->set_fade_delay(Python::GetFloat(fade_delay_obj));
  }
  if (fade_duration_obj != Py_None) {
    b->set_fade_duration(Python::GetFloat(fade_duration_obj));
  }
  if (style_obj != Py_None) {
    auto style_str = Python::GetString(style_obj);
    if (style_str == "bomb") {
      b->set_style(SpinnerWidget::Style::kBomb);
    } else if (style_str == "simple") {
      b->set_style(SpinnerWidget::Style::kSimple);
    } else {
      throw Exception("Invalid style value '" + style_str + "'");
    }
  }

  // If making a new widget, add it at the end.
  if (edit_obj == Py_None) {
    g_ui_v1->AddWidget(b.get(), parent_widget);
  }

  // Run any calls built up by UI callbacks.
  ui_op_context.Finish();

  return b->NewPyRef();
  BA_PYTHON_CATCH;
}

static PyMethodDef PySpinnerWidgetDef = {
    "spinnerwidget",               // name
    (PyCFunction)PySpinnerWidget,  // method
    METH_VARARGS | METH_KEYWORDS,  // flags

    "spinnerwidget(*,\n"
    "  edit: bauiv1.Widget | None = None,\n"
    "  parent: bauiv1.Widget | None = None,\n"
    "  size: float | None = None,\n"
    "  position: Sequence[float] | None = None,\n"
    "  style: Literal['bomb', 'simple'] | None = None,\n"
    "  visible: bool | None = None,\n"
    "  fade: bool | None = None,\n"
    "  fade_delay: float | None = None,\n"
    "  fade_duration: float | None = None,\n"
    ") -> bauiv1.Widget\n"
    "\n"
    "Create or edit a spinner widget.\n"
    "\n"
    "Pass a valid existing bauiv1.Widget as 'edit' to modify it; otherwise\n"
    "a new one is created and returned. Arguments that are not set to None\n"
    "are applied to the Widget.\n"
    "\n"
    "With 'fade' on (the default), the spinner stays invisible for\n"
    "'fade_delay' seconds after becoming visible and then fades in over\n"
    "'fade_duration' seconds (both default to 0.5), so one that goes away\n"
    "within the delay never shows at all. With 'fade' off it appears at\n"
    "once.",
};

// ----------------------------- sliderwidget ----------------------------------

static auto PySliderWidget(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  PyObject* edit_obj{Py_None};
  PyObject* parent_obj{Py_None};
  ContainerWidget* parent_widget{};
  PyObject* id_obj{Py_None};
  PyObject* size_obj{Py_None};
  PyObject* pos_obj{Py_None};
  PyObject* color_obj{Py_None};
  PyObject* value_obj{Py_None};
  PyObject* min_value_obj{Py_None};
  PyObject* max_value_obj{Py_None};
  PyObject* increment_obj{Py_None};
  PyObject* on_drag_call_obj{Py_None};
  PyObject* on_change_call_obj{Py_None};
  PyObject* autoselect_obj{Py_None};
  PyObject* transition_delay_obj{Py_None};
  PyObject* transition_type_obj{Py_None};
  PyObject* enabled_obj{Py_None};

  static const char* kwlist[] = {"edit",
                                 "parent",
                                 "id",
                                 "size",
                                 "position",
                                 "color",
                                 "value",
                                 "min_value",
                                 "max_value",
                                 "increment",
                                 "on_drag_call",
                                 "on_change_call",
                                 "autoselect",
                                 "transition_delay",
                                 "transition_type",
                                 "enabled",
                                 nullptr};
  if (!PyArg_ParseTupleAndKeywords(
          args, keywds, "|OOOOOOOOOOOOOOOO", const_cast<char**>(kwlist),
          &edit_obj, &parent_obj, &id_obj, &size_obj, &pos_obj, &color_obj,
          &value_obj, &min_value_obj, &max_value_obj, &increment_obj,
          &on_drag_call_obj, &on_change_call_obj, &autoselect_obj,
          &transition_delay_obj, &transition_type_obj, &enabled_obj)) {
    return nullptr;
  }

  if (!g_base->CurrentContext().IsEmpty()) {
    throw Exception("UI functions must be called with no context set.");
  }

  // Gather up any user code triggered by this stuff and run it at the end
  // before we return.
  base::UI::OperationContext ui_op_context;

  // Grab the edited widget or create a new one.
  Object::Ref<SliderWidget> b;
  if (edit_obj != Py_None) {
    b = dynamic_cast<SliderWidget*>(UIV1Python::GetPyWidget(edit_obj));
    if (!b.exists()) {
      throw Exception("Invalid or nonexistent widget.",
                      PyExcType::kWidgetNotFound);
    }
  } else {
    parent_widget = parent_obj == Py_None
                        ? g_ui_v1->screen_root_widget()
                        : dynamic_cast<ContainerWidget*>(
                              UIV1Python::GetPyWidget(parent_obj));
    if (parent_widget == nullptr) {
      throw Exception("Parent widget nonexistent or not a container.",
                      PyExcType::kWidgetNotFound);
    }
    b = Object::New<SliderWidget>();
  }
  if (id_obj != Py_None) {
    b->SetID(Python::GetString(id_obj));
  }
  if (size_obj != Py_None) {
    Point2D p = Python::GetPoint2D(size_obj);
    b->set_width(p.x);
    b->set_height(p.y);
  }
  if (pos_obj != Py_None) {
    Point2D p = Python::GetPoint2D(pos_obj);
    b->set_translate(p.x, p.y);
  }
  if (color_obj != Py_None) {
    std::vector<float> c = Python::GetFloats(color_obj);
    if (c.size() != 3) {
      throw Exception("Expected 3 floats for color.", PyExcType::kValue);
    }
    b->set_color(c[0], c[1], c[2]);
  }

  // Range before value, so a value handed in alongside a range is clamped
  // against that range rather than the one it replaced.
  if (min_value_obj != Py_None || max_value_obj != Py_None) {
    b->SetRange(
        min_value_obj == Py_None ? 0.0f : Python::GetFloat(min_value_obj),
        max_value_obj == Py_None ? 100.0f : Python::GetFloat(max_value_obj));
  }
  if (increment_obj != Py_None) {
    b->set_increment(Python::GetFloat(increment_obj));
  }
  if (value_obj != Py_None) {
    b->SetValue(Python::GetFloat(value_obj));
  }
  if (on_drag_call_obj != Py_None) {
    b->SetOnDragCall(on_drag_call_obj);
  }
  if (on_change_call_obj != Py_None) {
    b->SetOnChangeCall(on_change_call_obj);
  }
  if (autoselect_obj != Py_None) {
    b->set_auto_select(Python::GetBool(autoselect_obj));
  }
  if (transition_delay_obj != Py_None) {
    b->set_transition_delay(static_cast<millisecs_t>(
        1000.0f * Python::GetFloat(transition_delay_obj)));
  }
  if (transition_type_obj != Py_None) {
    std::string transition_type = Python::GetString(transition_type_obj);
    if (transition_type == "in_left") {
      b->set_transition_type(SliderWidget::TransitionType::kInLeft);
    } else if (transition_type == "scale") {
      b->set_transition_type(SliderWidget::TransitionType::kScale);
    } else {
      throw Exception("Invalid transition_type: '" + transition_type + "'.",
                      PyExcType::kValue);
    }
  }
  if (enabled_obj != Py_None) {
    b->SetEnabled(Python::GetBool(enabled_obj));
  }

  // If making a new widget, add it at the end.
  if (edit_obj == Py_None) {
    g_ui_v1->AddWidget(b.get(), parent_widget);
  }

  // Run any calls built up by UI callbacks.
  ui_op_context.Finish();

  return b->NewPyRef();
  BA_PYTHON_CATCH;
}

static PyMethodDef PySliderWidgetDef = {
    "sliderwidget",                // name
    (PyCFunction)PySliderWidget,   // method
    METH_VARARGS | METH_KEYWORDS,  // flags

    "sliderwidget(*,\n"
    "  edit: bauiv1.Widget | None = None,\n"
    "  parent: bauiv1.Widget | None = None,\n"
    "  id: str | None = None,\n"
    "  size: Sequence[float] | None = None,\n"
    "  position: Sequence[float] | None = None,\n"
    "  color: Sequence[float] | None = None,\n"
    "  value: float | None = None,\n"
    "  min_value: float | None = None,\n"
    "  max_value: float | None = None,\n"
    "  increment: float | None = None,\n"
    "  on_drag_call: Callable[[float], None] | None = None,\n"
    "  on_change_call: Callable[[float], None] | None = None,\n"
    "  autoselect: bool | None = None,\n"
    "  transition_delay: float | None = None,\n"
    "  transition_type: Literal['in_left', 'scale'] | None = None,\n"
    "  enabled: bool | None = None,\n"
    ") -> bauiv1.Widget\n"
    "\n"
    "Create or edit a slider widget.\n"
    "\n"
    "Pass a valid existing bauiv1.Widget as 'edit' to modify it; otherwise\n"
    "a new one is created and returned. Arguments that are not set to None\n"
    "are applied to the Widget.\n"
    "\n"
    "'on_drag_call' is passed the value repeatedly while the nub is being\n"
    "dragged, and for each key or controller step; 'on_change_call' is\n"
    "passed it when a drag is released having changed it, or when a run\n"
    "of key or controller steps that changed it settles (half a second\n"
    "after the last step, or at once if the slider loses selection).\n"
    "\n"
    "A slider with 'enabled' False draws dimmed and ignores input but\n"
    "remains selectable, so navigation around it is unaffected.",
};

// ----------------------------- columnwidget ----------------------------------

static auto PyColumnWidget(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;

  PyObject* id_obj{Py_None};
  PyObject* size_obj{Py_None};
  PyObject* pos_obj{Py_None};
  PyObject* background_obj{Py_None};
  PyObject* selected_child_obj{Py_None};
  PyObject* visible_child_obj{Py_None};
  PyObject* single_depth_obj{Py_None};
  PyObject* print_list_exit_instructions_obj{Py_None};
  PyObject* parent_obj{Py_None};
  PyObject* edit_obj{Py_None};
  ContainerWidget* parent_widget{};
  PyObject* left_border_obj{Py_None};
  PyObject* top_border_obj{Py_None};
  PyObject* bottom_border_obj{Py_None};
  PyObject* selection_loops_to_parent_obj{Py_None};
  PyObject* border_obj{Py_None};
  PyObject* margin_obj{Py_None};
  PyObject* claims_left_right_obj{Py_None};
  static const char* kwlist[] = {"edit",
                                 "parent",
                                 "id",
                                 "size",
                                 "position",
                                 "background",
                                 "selected_child",
                                 "visible_child",
                                 "single_depth",
                                 "print_list_exit_instructions",
                                 "left_border",
                                 "top_border",
                                 "bottom_border",
                                 "selection_loops_to_parent",
                                 "border",
                                 "margin",
                                 "claims_left_right",
                                 nullptr};
  if (!PyArg_ParseTupleAndKeywords(
          args, keywds, "|OOOOOOOOOOOOOOOOO", const_cast<char**>(kwlist),
          &edit_obj, &parent_obj, &id_obj, &size_obj, &pos_obj, &background_obj,
          &selected_child_obj, &visible_child_obj, &single_depth_obj,
          &print_list_exit_instructions_obj, &left_border_obj, &top_border_obj,
          &bottom_border_obj, &selection_loops_to_parent_obj, &border_obj,
          &margin_obj, &claims_left_right_obj))
    return nullptr;

  if (!g_base->CurrentContext().IsEmpty()) {
    throw Exception("UI functions must be called with no context set.");
  }

  // Gather up any user code triggered by this stuff and run it at the end
  // before we return.
  base::UI::OperationContext ui_op_context;

  // Grab the edited widget or create a new one.
  Object::Ref<ColumnWidget> widget;
  if (edit_obj != Py_None) {
    widget = dynamic_cast<ColumnWidget*>(UIV1Python::GetPyWidget(edit_obj));
    if (!widget.exists()) {
      throw Exception("Invalid or nonexistent widget.",
                      PyExcType::kWidgetNotFound);
    }
  } else {
    parent_widget = parent_obj == Py_None
                        ? g_ui_v1->screen_root_widget()
                        : dynamic_cast<ContainerWidget*>(
                              UIV1Python::GetPyWidget(parent_obj));
    if (!parent_widget) {
      throw Exception("Invalid or nonexistent parent widget.",
                      PyExcType::kWidgetNotFound);
    }
    widget = Object::New<ColumnWidget>();
  }

  // Set applicable values.
  if (id_obj != Py_None) {
    widget->SetID(Python::GetString(id_obj));
  }
  if (size_obj != Py_None) {
    Point2D p = Python::GetPoint2D(size_obj);
    widget->SetWidth(p.x);
    widget->SetHeight(p.y);
  }
  if (single_depth_obj != Py_None) {
    widget->set_single_depth(Python::GetBool(single_depth_obj));
  }
  if (pos_obj != Py_None) {
    Point2D p = Python::GetPoint2D(pos_obj);
    widget->set_translate(p.x, p.y);
  }
  if (left_border_obj != Py_None) {
    widget->set_left_border(Python::GetFloat(left_border_obj));
  }
  if (top_border_obj != Py_None) {
    widget->set_top_border(Python::GetFloat(top_border_obj));
  }
  if (border_obj != Py_None) {
    widget->set_border(Python::GetFloat(border_obj));
  }
  if (margin_obj != Py_None) {
    widget->set_margin(Python::GetFloat(margin_obj));
  }
  if (bottom_border_obj != Py_None) {
    widget->set_bottom_border(Python::GetFloat(bottom_border_obj));
  }
  if (print_list_exit_instructions_obj != Py_None) {
    widget->set_should_print_list_exit_instructions(
        Python::GetBool(print_list_exit_instructions_obj));
  }
  if (background_obj != Py_None) {
    widget->set_background(Python::GetBool(background_obj));
  }
  if (selected_child_obj != Py_None) {
    // Need to wrap this in an operation because it can trigger user code.
    base::UI::OperationContext operation_context;

    widget->SelectWidget(UIV1Python::GetPyWidget(selected_child_obj));

    // Run any user code/etc.
    operation_context.Finish();
  }
  if (visible_child_obj != Py_None) {
    widget->ShowWidget(UIV1Python::GetPyWidget(visible_child_obj));
  }
  if (selection_loops_to_parent_obj != Py_None) {
    widget->set_selection_loops_to_parent(
        Python::GetBool(selection_loops_to_parent_obj));
  }
  if (claims_left_right_obj != Py_None) {
    widget->set_claims_left_right(Python::GetBool(claims_left_right_obj));
  }

  // If making a new widget, add it at the end.
  if (edit_obj == Py_None) {
    g_ui_v1->AddWidget(widget.get(), parent_widget);
  }

  // Run any calls built up by UI callbacks.
  ui_op_context.Finish();

  return widget->NewPyRef();

  BA_PYTHON_CATCH;
}

static PyMethodDef PyColumnWidgetDef = {
    "columnwidget",                // name
    (PyCFunction)PyColumnWidget,   // method
    METH_VARARGS | METH_KEYWORDS,  // flags

    "columnwidget(*,\n"
    "  edit: bauiv1.Widget | None = None,\n"
    "  parent: bauiv1.Widget | None = None,\n"
    "  id: str | None = None,\n"
    "  size: Sequence[float] | None = None,\n"
    "  position: Sequence[float] | None = None,\n"
    "  background: bool | None = None,\n"
    "  selected_child: bauiv1.Widget | None = None,\n"
    "  visible_child: bauiv1.Widget | None = None,\n"
    "  single_depth: bool | None = None,\n"
    "  print_list_exit_instructions: bool | None = None,\n"
    "  left_border: float | None = None,\n"
    "  top_border: float | None = None,\n"
    "  bottom_border: float | None = None,\n"
    "  selection_loops_to_parent: bool | None = None,\n"
    "  border: float | None = None,\n"
    "  margin: float | None = None,\n"
    "  claims_left_right: bool | None = None,\n"
    ") -> bauiv1.Widget\n"
    "\n"
    "Create or edit a column widget.\n"
    "\n"
    "Pass a valid existing bauiv1.Widget as 'edit' to modify it; otherwise\n"
    "a new one is created and returned. Arguments that are not set to None\n"
    "are applied to the Widget.",
};

// ---------------------------- containerwidget --------------------------------

static auto PyContainerWidget(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  PyObject* size_obj{Py_None};
  PyObject* pos_obj{Py_None};
  PyObject* background_obj{Py_None};
  PyObject* selected_child_obj{Py_None};
  PyObject* transition_obj{Py_None};
  PyObject* cancel_button_obj{Py_None};
  PyObject* start_button_obj{Py_None};
  PyObject* root_selectable_obj{Py_None};
  PyObject* on_activate_call_obj{Py_None};
  PyObject* claims_left_right_obj{Py_None};
  PyObject* claims_up_down_obj{Py_None};
  PyObject* selection_loops_obj{Py_None};
  PyObject* selection_loops_to_parent_obj{Py_None};
  PyObject* scale_obj{Py_None};
  PyObject* on_outside_click_call_obj{Py_None};
  PyObject* print_list_exit_instructions_obj{Py_None};
  PyObject* single_depth_obj{Py_None};
  PyObject* visible_child_obj{Py_None};
  PyObject* stack_offset_obj{Py_None};
  PyObject* scale_origin_stack_offset_obj{Py_None};
  PyObject* color_obj{Py_None};
  PyObject* on_cancel_call_obj{Py_None};
  PyObject* click_activate_obj{Py_None};
  PyObject* always_highlight_obj{Py_None};
  PyObject* parent_obj{Py_None};
  PyObject* id_obj{Py_None};
  ContainerWidget* parent_widget;
  PyObject* edit_obj{Py_None};
  PyObject* selectable_obj{Py_None};
  PyObject* toolbar_visibility_obj{Py_None};
  PyObject* toolbar_cancel_button_style_obj{Py_None};
  PyObject* on_select_call_obj{Py_None};
  PyObject* claim_outside_clicks_obj{Py_None};
  PyObject* darken_behind_obj{Py_None};
  PyObject* darken_behind_is_permanent_obj{Py_None};
  PyObject* background_offset_obj{Py_None};

  static const char* kwlist[] = {"edit",
                                 "parent",
                                 "id",
                                 "size",
                                 "position",
                                 "background",
                                 "selected_child",
                                 "transition",
                                 "cancel_button",
                                 "start_button",
                                 "root_selectable",
                                 "on_activate_call",
                                 "claims_left_right",
                                 "selection_loops",
                                 "selection_loops_to_parent",
                                 "scale",
                                 "on_outside_click_call",
                                 "single_depth",
                                 "visible_child",
                                 "stack_offset",
                                 "color",
                                 "on_cancel_call",
                                 "print_list_exit_instructions",
                                 "click_activate",
                                 "always_highlight",
                                 "selectable",
                                 "scale_origin_stack_offset",
                                 "toolbar_visibility",
                                 "toolbar_cancel_button_style",
                                 "on_select_call",
                                 "claim_outside_clicks",
                                 "claims_up_down",
                                 "darken_behind",
                                 "darken_behind_is_permanent",
                                 "background_offset",
                                 nullptr};

  if (!PyArg_ParseTupleAndKeywords(
          args, keywds, "|OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO",
          const_cast<char**>(kwlist), &edit_obj, &parent_obj, &id_obj,
          &size_obj, &pos_obj, &background_obj, &selected_child_obj,
          &transition_obj, &cancel_button_obj, &start_button_obj,
          &root_selectable_obj, &on_activate_call_obj, &claims_left_right_obj,
          &selection_loops_obj, &selection_loops_to_parent_obj, &scale_obj,
          &on_outside_click_call_obj, &single_depth_obj, &visible_child_obj,
          &stack_offset_obj, &color_obj, &on_cancel_call_obj,
          &print_list_exit_instructions_obj, &click_activate_obj,
          &always_highlight_obj, &selectable_obj,
          &scale_origin_stack_offset_obj, &toolbar_visibility_obj,
          &toolbar_cancel_button_style_obj, &on_select_call_obj,
          &claim_outside_clicks_obj, &claims_up_down_obj, &darken_behind_obj,
          &darken_behind_is_permanent_obj, &background_offset_obj)) {
    return nullptr;
  }

  if (!g_base->CurrentContext().IsEmpty()) {
    throw Exception("UI functions must be called with no context set.");
  }

  // Defer any user code triggered by selects/etc until the end.
  base::UI::OperationContext ui_op_context;

  // Grab the edited widget or create a new one.
  Object::Ref<ContainerWidget> widget;
  if (edit_obj != Py_None) {
    widget = dynamic_cast<ContainerWidget*>(UIV1Python::GetPyWidget(edit_obj));
    if (!widget.exists()) {
      throw Exception("Invalid or nonexistent widget.",
                      PyExcType::kWidgetNotFound);
    }
    if (id_obj != Py_None) {
      throw Exception("ID can only be set when creating.");
    }
  } else {
    if (parent_obj == Py_None) {
      BA_PRECONDITION(g_ui_v1 && g_ui_v1->screen_root_widget() != nullptr);
    }
    parent_widget = parent_obj == Py_None
                        ? g_ui_v1->screen_root_widget()
                        : dynamic_cast<ContainerWidget*>(
                              UIV1Python::GetPyWidget(parent_obj));
    if (!parent_widget) {
      throw Exception("Invalid or nonexistent parent widget.",
                      PyExcType::kWidgetNotFound);
    }
    widget = Object::New<ContainerWidget>();

    // Id needs to be set before adding to parent.
    if (id_obj != Py_None) {
      widget->SetID(Python::GetString(id_obj));
    }

    g_ui_v1->AddWidget(widget.get(), parent_widget);
  }

  // Set applicable values.
  if (size_obj != Py_None) {
    Point2D p = Python::GetPoint2D(size_obj);
    widget->SetWidth(p.x);
    widget->SetHeight(p.y);
  }
  if (pos_obj != Py_None) {
    Point2D p = Python::GetPoint2D(pos_obj);
    widget->set_translate(p.x, p.y);
  }
  if (on_cancel_call_obj != Py_None) {
    widget->SetOnCancelCall(on_cancel_call_obj);
  }
  if (scale_obj != Py_None) {
    widget->set_scale(Python::GetFloat(scale_obj));
  }
  if (on_select_call_obj != Py_None) {
    widget->SetOnSelectCall(on_select_call_obj);
  }
  if (selectable_obj != Py_None) {
    widget->set_selectable(Python::GetBool(selectable_obj));
  }
  if (single_depth_obj != Py_None) {
    widget->set_single_depth(Python::GetBool(single_depth_obj));
  }
  if (stack_offset_obj != Py_None) {
    Point2D p = Python::GetPoint2D(stack_offset_obj);
    widget->set_stack_offset(p.x, p.y);
  }
  if (scale_origin_stack_offset_obj != Py_None) {
    Point2D p = Python::GetPoint2D(scale_origin_stack_offset_obj);
    widget->SetScaleOriginStackOffset(p.x, p.y);
  }
  if (visible_child_obj != Py_None) {
    widget->ShowWidget(UIV1Python::GetPyWidget(visible_child_obj));
  }
  if (color_obj != Py_None) {
    std::vector<float> c = Python::GetFloats(color_obj);
    if (c.size() != 3 && c.size() != 4) {
      throw Exception("Expected 3 or floats for color.", PyExcType::kValue);
    }
    if (c.size() == 3) {
      widget->set_color(c[0], c[1], c[2], 1.0f);
    } else {
      widget->set_color(c[0], c[1], c[2], c[3]);
    }
  }

  if (on_activate_call_obj != Py_None) {
    widget->SetOnActivateCall(on_activate_call_obj);
  }

  if (on_outside_click_call_obj != Py_None) {
    widget->SetOnOutsideClickCall(on_outside_click_call_obj);
  }

  if (background_obj != Py_None) {
    widget->set_background(Python::GetBool(background_obj));
  }
  if (root_selectable_obj != Py_None) {
    widget->SetRootSelectable(Python::GetBool(root_selectable_obj));
  }
  if (selected_child_obj != Py_None) {
    // Special case: passing 0 implies deselect.
    //
    // Tested for truthiness rather than by extracting a C value: Python
    // ints are arbitrary precision, and PyLong_AsLong on a large one
    // returns -1 (compares unequal to 0, so we would take the right
    // branch by luck) while leaving an OverflowError set for something
    // unrelated to trip over.
    if (PyLong_Check(selected_child_obj)
        && !Python::GetBool(selected_child_obj)) {
      widget->SelectWidget(nullptr);
    } else {
      widget->SelectWidget(UIV1Python::GetPyWidget(selected_child_obj));
    }
  }

  if (transition_obj != Py_None) {
    std::string t = Python::GetString(transition_obj);
    if (t == "in_left") {
      widget->SetTransition(ContainerWidget::TransitionType::kInLeft);
    } else if (t == "in_right") {
      widget->SetTransition(ContainerWidget::TransitionType::kInRight);
    } else if (t == "out_left") {
      widget->SetTransition(ContainerWidget::TransitionType::kOutLeft);
    } else if (t == "out_right") {
      widget->SetTransition(ContainerWidget::TransitionType::kOutRight);
    } else if (t == "in_scale") {
      widget->SetTransition(ContainerWidget::TransitionType::kInScale);
    } else if (t == "out_scale") {
      widget->SetTransition(ContainerWidget::TransitionType::kOutScale);
    }
  }

  if (cancel_button_obj != Py_None) {
    auto* button_widget =
        dynamic_cast<ButtonWidget*>(UIV1Python::GetPyWidget(cancel_button_obj));
    if (!button_widget) {
      throw Exception("Invalid cancel_button.", PyExcType::kWidgetNotFound);
    }
    widget->SetCancelButton(button_widget);
  }
  if (start_button_obj != Py_None) {
    auto* button_widget =
        dynamic_cast<ButtonWidget*>(UIV1Python::GetPyWidget(start_button_obj));
    if (!button_widget) {
      throw Exception("Invalid start_button.", PyExcType::kWidgetNotFound);
    }
    widget->SetStartButton(button_widget);
  }
  if (claims_left_right_obj != Py_None) {
    widget->set_claims_left_right(Python::GetBool(claims_left_right_obj));
  }
  if (claims_up_down_obj != Py_None) {
    widget->set_claims_up_down(Python::GetBool(claims_up_down_obj));
  }
  if (selection_loops_obj != Py_None) {
    widget->set_selection_loops(Python::GetBool(selection_loops_obj));
  }
  if (selection_loops_to_parent_obj != Py_None) {
    widget->set_selection_loops_to_parent(
        Python::GetBool(selection_loops_to_parent_obj));
  }
  if (print_list_exit_instructions_obj != Py_None) {
    widget->set_should_print_list_exit_instructions(
        Python::GetBool(print_list_exit_instructions_obj));
  }
  if (click_activate_obj != Py_None) {
    widget->set_click_activate(Python::GetBool(click_activate_obj));
  }
  if (always_highlight_obj != Py_None) {
    widget->set_always_highlight(Python::GetBool(always_highlight_obj));
  }
  if (toolbar_visibility_obj != Py_None) {
    Widget::ToolbarVisibility val;
    std::string sval = Python::GetString(toolbar_visibility_obj);
    if (sval == "menu_minimal") {
      val = Widget::ToolbarVisibility::kMenuMinimal;
    } else if (sval == "menu_minimal_no_back") {
      val = Widget::ToolbarVisibility::kMenuMinimalNoBack;
    } else if (sval == "menu_store") {
      val = Widget::ToolbarVisibility::kMenuStore;
    } else if (sval == "menu_store_no_back") {
      val = Widget::ToolbarVisibility::kMenuStoreNoBack;
    } else if (sval == "menu_in_game") {
      val = Widget::ToolbarVisibility::kMenuInGame;
    } else if (sval == "menu_tokens") {
      val = Widget::ToolbarVisibility::kMenuTokens;
    } else if (sval == "menu_full") {
      val = Widget::ToolbarVisibility::kMenuFull;
    } else if (sval == "menu_full_no_back") {
      val = Widget::ToolbarVisibility::kMenuFullNoBack;
    } else if (sval == "in_game") {
      val = Widget::ToolbarVisibility::kInGame;
    } else if (sval == "inherit") {
      val = Widget::ToolbarVisibility::kInherit;
    } else if (sval == "no_menu_minimal") {
      val = Widget::ToolbarVisibility::kNoMenuMinimal;
    } else {
      throw Exception("Invalid toolbar_visibility: '" + sval + "'.",
                      PyExcType::kValue);
    }
    widget->SetToolbarVisibility(val);
  }

  if (toolbar_cancel_button_style_obj != Py_None) {
    Widget::ToolbarCancelButtonStyle val;
    std::string sval = Python::GetString(toolbar_cancel_button_style_obj);
    if (sval == "back") {
      val = Widget::ToolbarCancelButtonStyle::kBack;
    } else if (sval == "close") {
      val = Widget::ToolbarCancelButtonStyle::kClose;
    } else {
      throw Exception("Invalid toolbar_cancel_button_style: '" + sval + "'.",
                      PyExcType::kValue);
    }
    widget->SetToolbarCancelButtonStyle(val);
  }

  if (claim_outside_clicks_obj != Py_None) {
    widget->set_claims_outside_clicks(
        Python::GetBool(claim_outside_clicks_obj));
  }

  if (darken_behind_obj != Py_None) {
    widget->set_darken_behind(Python::GetBool(darken_behind_obj));
  }
  if (darken_behind_is_permanent_obj != Py_None) {
    widget->set_darken_behind_is_permanent(
        Python::GetBool(darken_behind_is_permanent_obj));
  }
  if (background_offset_obj != Py_None) {
    auto offset = Python::GetFloats(background_offset_obj);
    if (offset.size() != 2) {
      throw Exception("Expected 2 floats for background_offset.",
                      PyExcType::kValue);
    }
    widget->set_background_offset(offset[0], offset[1]);
  }

  // Run any calls built up by UI callbacks.
  ui_op_context.Finish();

  return widget->NewPyRef();

  BA_PYTHON_CATCH;
}

static PyMethodDef PyContainerWidgetDef = {
    "containerwidget",               // name
    (PyCFunction)PyContainerWidget,  // method
    METH_VARARGS | METH_KEYWORDS,    // flags

    "containerwidget(*,\n"
    "  edit: bauiv1.Widget | None = None,\n"
    "  parent: bauiv1.Widget | None = None,\n"
    "  id: str | None = None,\n"
    "  size: Sequence[float] | None = None,\n"
    "  position: Sequence[float] | None = None,\n"
    "  background: bool | None = None,\n"
    "  selected_child: bauiv1.Widget | None = None,\n"
    "  transition: str | None = None,\n"
    "  cancel_button: bauiv1.Widget | None = None,\n"
    "  start_button: bauiv1.Widget | None = None,\n"
    "  root_selectable: bool | None = None,\n"
    "  on_activate_call: Callable[[], None] | None = None,\n"
    "  claims_left_right: bool | None = None,\n"
    "  selection_loops: bool | None = None,\n"
    "  selection_loops_to_parent: bool | None = None,\n"
    "  scale: float | None = None,\n"
    "  on_outside_click_call: Callable[[], None] | None = None,\n"
    "  single_depth: bool | None = None,\n"
    "  visible_child: bauiv1.Widget | None = None,\n"
    "  stack_offset: Sequence[float] | None = None,\n"
    "  color: Sequence[float] | None = None,\n"
    "  on_cancel_call: Callable[[], None] | None = None,\n"
    "  print_list_exit_instructions: bool | None = None,\n"
    "  click_activate: bool | None = None,\n"
    "  always_highlight: bool | None = None,\n"
    "  selectable: bool | None = None,\n"
    "  scale_origin_stack_offset: Sequence[float] | None = None,\n"
    "  toolbar_visibility: Literal['menu_minimal',\n"
    "                              'menu_minimal_no_back',\n"
    "                              'menu_full',\n"
    "                              'menu_full_no_back',\n"
    "                              'menu_store',\n"
    "                              'menu_store_no_back',\n"
    "                              'menu_in_game',\n"
    "                              'menu_tokens',\n"
    "                              'no_menu_minimal',\n"
    "                              'inherit',\n"
    "                             ] | None = None,\n"
    "  toolbar_cancel_button_style: Literal['back',\n"
    "                              'close',\n"
    "                             ] | None = None,\n"
    "  on_select_call: Callable[[], None] | None = None,\n"
    "  claim_outside_clicks: bool | None = None,\n"
    "  claims_up_down: bool | None = None,\n"
    "  darken_behind: bool | None = None,\n"
    "  darken_behind_is_permanent: bool | None = None,\n"
    "  background_offset: Sequence[float] | None = None) -> bauiv1.Widget\n"
    "\n"
    "Create or edit a container widget.\n"
    "\n"
    "Pass a valid existing bauiv1.Widget as 'edit' to modify it; otherwise\n"
    "a new one is created and returned. Arguments that are not set to None\n"
    "are applied to the Widget.\n"
    "\n"
    "'background_offset' shifts where the background art draws (x, y)\n"
    "without moving anything else, for art whose placement doesn't suit\n"
    "a particular window shape.",
};

// ------------------------------ rowwidget ------------------------------------

static auto PyRowWidget(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;

  PyObject* size_obj{Py_None};
  PyObject* pos_obj{Py_None};
  PyObject* background_obj{Py_None};
  PyObject* selected_child_obj{Py_None};
  PyObject* visible_child_obj{Py_None};
  PyObject* parent_obj{Py_None};
  PyObject* edit_obj{Py_None};
  ContainerWidget* parent_widget{};
  PyObject* claims_left_right_obj{Py_None};
  PyObject* selection_loops_to_parent_obj{Py_None};

  static const char* kwlist[] = {"edit",
                                 "parent",
                                 "size",
                                 "position",
                                 "background",
                                 "selected_child",
                                 "visible_child",
                                 "claims_left_right",
                                 "selection_loops_to_parent",
                                 nullptr};

  if (!PyArg_ParseTupleAndKeywords(
          args, keywds, "|OOOOOOOOO", const_cast<char**>(kwlist), &edit_obj,
          &parent_obj, &size_obj, &pos_obj, &background_obj,
          &selected_child_obj, &visible_child_obj, &claims_left_right_obj,
          &selection_loops_to_parent_obj))
    return nullptr;

  if (!g_base->CurrentContext().IsEmpty()) {
    throw Exception("UI functions must be called with no context set.");
  }

  // Gather up any user code triggered by this stuff and run it at the end
  // before we return.
  base::UI::OperationContext ui_op_context;

  // Grab the edited widget or create a new one.
  Object::Ref<RowWidget> widget;
  if (edit_obj != Py_None) {
    widget = dynamic_cast<RowWidget*>(UIV1Python::GetPyWidget(edit_obj));
    if (!widget.exists()) {
      throw Exception("Invalid or nonexistent widget.",
                      PyExcType::kWidgetNotFound);
    }
  } else {
    parent_widget = parent_obj == Py_None
                        ? g_ui_v1->screen_root_widget()
                        : dynamic_cast<ContainerWidget*>(
                              UIV1Python::GetPyWidget(parent_obj));
    if (!parent_widget) {
      throw Exception("invalid or nonexistent parent widget.",
                      PyExcType::kWidgetNotFound);
    }
    widget = Object::New<RowWidget>();
  }

  // Set applicable values.
  if (size_obj != Py_None) {
    Point2D p = Python::GetPoint2D(size_obj);
    widget->SetWidth(p.x);
    widget->SetHeight(p.y);
  }
  if (pos_obj != Py_None) {
    Point2D p = Python::GetPoint2D(pos_obj);
    widget->set_translate(p.x, p.y);
  }

  if (background_obj != Py_None) {
    widget->set_background(Python::GetBool(background_obj));
  }
  if (selected_child_obj != Py_None) {
    widget->SelectWidget(UIV1Python::GetPyWidget(selected_child_obj));
  }
  if (visible_child_obj != Py_None) {
    widget->ShowWidget(UIV1Python::GetPyWidget(visible_child_obj));
  }
  if (claims_left_right_obj != Py_None) {
    widget->set_claims_left_right(Python::GetBool(claims_left_right_obj));
  }
  if (selection_loops_to_parent_obj != Py_None) {
    widget->set_selection_loops_to_parent(
        Python::GetBool(selection_loops_to_parent_obj));
  }

  // If making a new widget, add it to the parent.
  if (edit_obj == Py_None) {
    g_ui_v1->AddWidget(widget.get(), parent_widget);
  }

  // Run any calls built up by UI callbacks.
  ui_op_context.Finish();

  return widget->NewPyRef();

  BA_PYTHON_CATCH;
}

static PyMethodDef PyRowWidgetDef = {
    "rowwidget",                   // name
    (PyCFunction)PyRowWidget,      // method
    METH_VARARGS | METH_KEYWORDS,  // flags

    "rowwidget(edit: bauiv1.Widget | None = None,\n"
    "  parent: bauiv1.Widget | None = None,\n"
    "  size: Sequence[float] | None = None,\n"
    "  position: Sequence[float] | None = None,\n"
    "  background: bool | None = None,\n"
    "  selected_child: bauiv1.Widget | None = None,\n"
    "  visible_child: bauiv1.Widget | None = None,\n"
    "  claims_left_right: bool | None = None,\n"
    "  selection_loops_to_parent: bool | None = None) -> bauiv1.Widget\n"
    "\n"
    "Create or edit a row widget.\n"
    "\n"
    "Pass a valid existing bauiv1.Widget as 'edit' to modify it; otherwise\n"
    "a new one is created and returned. Arguments that are not set to None\n"
    "are applied to the Widget.",
};

// ---------------------------- scrollwidget -----------------------------------

static auto PyScrollWidget(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  PyObject* size_obj{Py_None};
  PyObject* pos_obj{Py_None};
  PyObject* background_obj{Py_None};
  PyObject* selected_child_obj{Py_None};
  PyObject* capture_arrows_obj{Py_None};
  PyObject* on_select_call_obj{Py_None};
  PyObject* parent_obj{Py_None};
  PyObject* edit_obj{Py_None};
  PyObject* center_small_content_obj{Py_None};
  PyObject* center_small_content_horizontally_obj{Py_None};
  ContainerWidget* parent_widget{};
  PyObject* color_obj{Py_None};
  PyObject* highlight_obj{Py_None};
  PyObject* border_opacity_obj{Py_None};
  PyObject* simple_culling_v_obj{Py_None};
  PyObject* selection_loops_to_parent_obj{Py_None};
  PyObject* claims_left_right_obj{Py_None};
  PyObject* claims_up_down_obj{Py_None};
  PyObject* autoselect_obj{Py_None};
  PyObject* id_obj{Py_None};
  PyObject* hide_border_when_fits_obj{Py_None};
  PyObject* scrollbar_visible_obj{Py_None};
  PyObject* fading_scrollbar_obj{Py_None};
  PyObject* clean_layout_obj{Py_None};

  static const char* kwlist[] = {"edit",
                                 "parent",
                                 "id",
                                 "size",
                                 "position",
                                 "background",
                                 "selected_child",
                                 "capture_arrows",
                                 "on_select_call",
                                 "center_small_content",
                                 "center_small_content_horizontally",
                                 "color",
                                 "highlight",
                                 "border_opacity",
                                 "simple_culling_v",
                                 "selection_loops_to_parent",
                                 "claims_left_right",
                                 "claims_up_down",
                                 "autoselect",
                                 "hide_border_when_fits",
                                 "scrollbar_visible",
                                 "fading_scrollbar",
                                 "clean_layout",
                                 nullptr};

  if (!PyArg_ParseTupleAndKeywords(
          args, keywds, "|OOOOOOOOOOOOOOOOOOOOOOO", const_cast<char**>(kwlist),
          &edit_obj, &parent_obj, &id_obj, &size_obj, &pos_obj, &background_obj,
          &selected_child_obj, &capture_arrows_obj, &on_select_call_obj,
          &center_small_content_obj, &center_small_content_horizontally_obj,
          &color_obj, &highlight_obj, &border_opacity_obj,
          &simple_culling_v_obj, &selection_loops_to_parent_obj,
          &claims_left_right_obj, &claims_up_down_obj, &autoselect_obj,
          &hide_border_when_fits_obj, &scrollbar_visible_obj,
          &fading_scrollbar_obj, &clean_layout_obj))
    return nullptr;

  if (!g_base->CurrentContext().IsEmpty()) {
    throw Exception("UI functions must be called with no context set.");
  }

  // Gather up any user code triggered by this stuff and run it at the end
  // before we return.
  base::UI::OperationContext ui_op_context;

  // Grab the edited widget or create a new one.
  Object::Ref<ScrollWidget> widget;
  if (edit_obj != Py_None) {
    widget = dynamic_cast<ScrollWidget*>(UIV1Python::GetPyWidget(edit_obj));
    if (!widget.exists()) {
      throw Exception("Invalid or nonexistent edit widget.",
                      PyExcType::kWidgetNotFound);
    }
  } else {
    parent_widget = parent_obj == Py_None
                        ? g_ui_v1->screen_root_widget()
                        : dynamic_cast<ContainerWidget*>(
                              UIV1Python::GetPyWidget(parent_obj));
    if (!parent_widget) {
      throw Exception("Invalid or nonexistent parent widget.",
                      PyExcType::kWidgetNotFound);
    }
    widget = Object::New<ScrollWidget>();
  }

  // Set applicable values.
  if (size_obj != Py_None) {
    Point2D p = Python::GetPoint2D(size_obj);
    widget->SetWidth(p.x);
    widget->SetHeight(p.y);
  }
  if (pos_obj != Py_None) {
    Point2D p = Python::GetPoint2D(pos_obj);
    widget->set_translate(p.x, p.y);
  }
  if (highlight_obj != Py_None) {
    widget->set_highlight(Python::GetBool(highlight_obj));
  }
  if (border_opacity_obj != Py_None) {
    widget->set_border_opacity(Python::GetFloat(border_opacity_obj));
  }
  if (hide_border_when_fits_obj != Py_None) {
    widget->set_hide_border_when_fits(
        Python::GetBool(hide_border_when_fits_obj));
  }
  if (scrollbar_visible_obj != Py_None) {
    widget->set_scrollbar_visible(Python::GetBool(scrollbar_visible_obj));
  }
  if (fading_scrollbar_obj != Py_None) {
    widget->set_fading_scrollbar(Python::GetBool(fading_scrollbar_obj));
  }
  if (clean_layout_obj != Py_None) {
    widget->set_clean_layout(Python::GetBool(clean_layout_obj));
  }
  if (on_select_call_obj != Py_None) {
    widget->SetOnSelectCall(on_select_call_obj);
  }
  if (center_small_content_obj != Py_None) {
    widget->set_center_small_content(Python::GetBool(center_small_content_obj));
  }
  if (center_small_content_horizontally_obj != Py_None) {
    widget->set_center_small_content_horizontally(
        Python::GetBool(center_small_content_horizontally_obj));
  }
  if (color_obj != Py_None) {
    std::vector<float> c = Python::GetFloats(color_obj);
    if (c.size() != 3) {
      throw Exception("Expected 3 floats for color.", PyExcType::kValue);
    }
    widget->set_color(c[0], c[1], c[2]);
  }
  if (capture_arrows_obj != Py_None) {
    widget->set_capture_arrows(Python::GetBool(capture_arrows_obj));
  }
  if (background_obj != Py_None) {
    widget->set_background(Python::GetBool(background_obj));
  }
  if (simple_culling_v_obj != Py_None) {
    widget->set_simple_culling_v(Python::GetFloat(simple_culling_v_obj));
  }
  if (selected_child_obj != Py_None) {
    widget->SelectWidget(UIV1Python::GetPyWidget(selected_child_obj));
  }
  if (selection_loops_to_parent_obj != Py_None) {
    widget->set_selection_loops_to_parent(
        Python::GetBool(selection_loops_to_parent_obj));
  }
  if (claims_left_right_obj != Py_None) {
    widget->set_claims_left_right(Python::GetBool(claims_left_right_obj));
  }
  if (claims_up_down_obj != Py_None) {
    widget->set_claims_up_down(Python::GetBool(claims_up_down_obj));
  }
  if (autoselect_obj != Py_None) {
    widget->set_auto_select(Python::GetBool(autoselect_obj));
  }
  if (id_obj != Py_None) {
    widget->SetID(Python::GetString(id_obj));
  }

  // If making a new widget add it at the end.
  if (edit_obj == Py_None) {
    g_ui_v1->AddWidget(widget.get(), parent_widget);
  }

  // Run any calls built up by UI callbacks.
  ui_op_context.Finish();

  return widget->NewPyRef();

  BA_PYTHON_CATCH;
}

static PyMethodDef PyScrollWidgetDef = {
    "scrollwidget",                // name
    (PyCFunction)PyScrollWidget,   // method
    METH_VARARGS | METH_KEYWORDS,  // flags

    "scrollwidget(*,\n"
    "  edit: bauiv1.Widget | None = None,\n"
    "  parent: bauiv1.Widget | None = None,\n"
    "  id: str | None = None,\n"
    "  size: Sequence[float] | None = None,\n"
    "  position: Sequence[float] | None = None,\n"
    "  background: bool | None = None,\n"
    "  selected_child: bauiv1.Widget | None = None,\n"
    "  capture_arrows: bool = False,\n"
    "  on_select_call: Callable | None = None,\n"
    "  center_small_content: bool | None = None,\n"
    "  center_small_content_horizontally: bool | None = None,\n"
    "  color: Sequence[float] | None = None,\n"
    "  highlight: bool | None = None,\n"
    "  border_opacity: float | None = None,\n"
    "  simple_culling_v: float | None = None,\n"
    "  selection_loops_to_parent: bool | None = None,\n"
    "  claims_left_right: bool | None = None,\n"
    "  claims_up_down: bool | None = None,\n"
    "  autoselect: bool | None = None,\n"
    "  hide_border_when_fits: bool | None = None,\n"
    "  scrollbar_visible: bool | None = None,\n"
    "  fading_scrollbar: bool | None = None,\n"
    "  clean_layout: bool | None = None,\n"
    ") -> bauiv1.Widget\n"
    "\n"
    "Create or edit a scroll widget.\n"
    "\n"
    "Pass a valid existing bauiv1.Widget as 'edit' to modify it; otherwise\n"
    "a new one is created and returned. Arguments that are not set to None\n"
    "are applied to the Widget.\n"
    "\n"
    "With 'hide_border_when_fits', the border (and selection glow) is not\n"
    "drawn at all while all content fits, since there is then nothing to\n"
    "scroll.\n"
    "\n"
    "With 'scrollbar_visible' False, the scroll bar (trough and thumb) is\n"
    "neither drawn nor mouse-grabbable; scrolling itself and layout are\n"
    "unaffected.\n"
    "\n"
    "With 'fading_scrollbar', the scroll bar is a thin translucent thumb\n"
    "drawn over the content that fades in while scrolling, hovered or\n"
    "dragged (as horizontal scroll widgets' do) instead of a trough and\n"
    "thumb; only the thumb itself can be grabbed.\n"
    "\n"
    "With 'clean_layout', content is laid out with none of the widget's\n"
    "historical fudge offsets: it starts at the left edge (or is exactly\n"
    "centered), spans the full height, and is clipped exactly to the\n"
    "widget's bounds.",
};

// ---------------------------- hscrollwidget ----------------------------------

static auto PyHScrollWidget(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;

  PyObject* size_obj{Py_None};
  PyObject* pos_obj{Py_None};
  PyObject* background_obj{Py_None};
  PyObject* selected_child_obj{Py_None};
  PyObject* capture_arrows_obj{Py_None};
  PyObject* on_select_call_obj{Py_None};
  PyObject* parent_obj{Py_None};
  PyObject* edit_obj{Py_None};
  PyObject* center_small_content_obj{Py_None};
  ContainerWidget* parent_widget{};
  PyObject* color_obj{Py_None};
  PyObject* highlight_obj{Py_None};
  PyObject* border_opacity_obj{Py_None};
  PyObject* simple_culling_h_obj{Py_None};
  PyObject* claims_left_right_obj{Py_None};
  PyObject* claims_up_down_obj{Py_None};
  PyObject* autoselect_obj{Py_None};
  PyObject* button_inset_left_obj{Py_None};
  PyObject* button_inset_right_obj{Py_None};
  PyObject* transition_in_obj{Py_None};
  PyObject* scrollbar_visible_obj{Py_None};
  PyObject* clean_layout_obj{Py_None};

  static const char* kwlist[] = {"edit",
                                 "parent",
                                 "size",
                                 "position",
                                 "background",
                                 "selected_child",
                                 "capture_arrows",
                                 "on_select_call",
                                 "center_small_content",
                                 "color",
                                 "highlight",
                                 "border_opacity",
                                 "simple_culling_h",
                                 "claims_left_right",
                                 "claims_up_down",
                                 "autoselect",
                                 "button_inset_left",
                                 "button_inset_right",
                                 "transition_in",
                                 "scrollbar_visible",
                                 "clean_layout",
                                 nullptr};

  if (!PyArg_ParseTupleAndKeywords(
          args, keywds, "|OOOOOOOOOOOOOOOOOOOOO", const_cast<char**>(kwlist),
          &edit_obj, &parent_obj, &size_obj, &pos_obj, &background_obj,
          &selected_child_obj, &capture_arrows_obj, &on_select_call_obj,
          &center_small_content_obj, &color_obj, &highlight_obj,
          &border_opacity_obj, &simple_culling_h_obj, &claims_left_right_obj,
          &claims_up_down_obj, &autoselect_obj, &button_inset_left_obj,
          &button_inset_right_obj, &transition_in_obj, &scrollbar_visible_obj,
          &clean_layout_obj))
    return nullptr;

  if (!g_base->CurrentContext().IsEmpty()) {
    throw Exception("UI functions must be called with no context set.");
  }

  // Gather up any user code triggered by this stuff and run it at the end
  // before we return.
  base::UI::OperationContext ui_op_context;

  // Grab the edited widget or create a new one.
  Object::Ref<HScrollWidget> widget;
  if (edit_obj != Py_None) {
    widget = dynamic_cast<HScrollWidget*>(UIV1Python::GetPyWidget(edit_obj));
    if (!widget.exists()) {
      throw Exception("Invalid or nonexistent edit widget.",
                      PyExcType::kWidgetNotFound);
    }
  } else {
    parent_widget = parent_obj == Py_None
                        ? g_ui_v1->screen_root_widget()
                        : dynamic_cast<ContainerWidget*>(
                              UIV1Python::GetPyWidget(parent_obj));
    if (!parent_widget) {
      throw Exception("Invalid or nonexistent parent widget.",
                      PyExcType::kWidgetNotFound);
    }
    widget = Object::New<HScrollWidget>();
  }

  // Set applicable values.
  if (size_obj != Py_None) {
    Point2D p = Python::GetPoint2D(size_obj);
    widget->SetWidth(p.x);
    widget->SetHeight(p.y);
  }
  if (pos_obj != Py_None) {
    Point2D p = Python::GetPoint2D(pos_obj);
    widget->set_translate(p.x, p.y);
  }
  if (highlight_obj != Py_None) {
    widget->set_highlight(Python::GetBool(highlight_obj));
  }
  if (border_opacity_obj != Py_None) {
    widget->setBorderOpacity(Python::GetFloat(border_opacity_obj));
  }
  if (scrollbar_visible_obj != Py_None) {
    widget->set_scrollbar_visible(Python::GetBool(scrollbar_visible_obj));
  }
  if (clean_layout_obj != Py_None) {
    widget->set_clean_layout(Python::GetBool(clean_layout_obj));
  }
  if (on_select_call_obj != Py_None) {
    widget->SetOnSelectCall(on_select_call_obj);
  }
  if (center_small_content_obj != Py_None) {
    widget->SetCenterSmallContent(Python::GetBool(center_small_content_obj));
  }
  if (color_obj != Py_None) {
    std::vector<float> c = Python::GetFloats(color_obj);
    if (c.size() != 3) {
      throw Exception("Expected 3 floats for color.", PyExcType::kValue);
    }
    widget->SetColor(c[0], c[1], c[2]);
  }
  if (capture_arrows_obj != Py_None) {
    widget->set_capture_arrows(Python::GetBool(capture_arrows_obj));
  }
  if (background_obj != Py_None) {
    widget->set_background(Python::GetBool(background_obj));
  }
  if (simple_culling_h_obj != Py_None) {
    widget->set_simple_culling_h(Python::GetFloat(simple_culling_h_obj));
  }
  if (selected_child_obj != Py_None) {
    widget->SelectWidget(UIV1Python::GetPyWidget(selected_child_obj));
  }
  if (claims_left_right_obj != Py_None) {
    widget->set_claims_left_right(Python::GetBool(claims_left_right_obj));
  }
  if (claims_up_down_obj != Py_None) {
    widget->set_claims_up_down(Python::GetBool(claims_up_down_obj));
  }
  if (autoselect_obj != Py_None) {
    widget->set_auto_select(Python::GetBool(autoselect_obj));
  }
  if (button_inset_left_obj != Py_None) {
    widget->set_button_inset_left(Python::GetFloat(button_inset_left_obj));
  }
  if (button_inset_right_obj != Py_None) {
    widget->set_button_inset_right(Python::GetFloat(button_inset_right_obj));
  }
  if (transition_in_obj != Py_None) {
    widget->set_transition_in(Python::GetBool(transition_in_obj));
  }

  // if making a new widget add it at the end
  if (edit_obj == Py_None) {
    g_ui_v1->AddWidget(widget.get(), parent_widget);
  }

  // Run any calls built up by UI callbacks.
  ui_op_context.Finish();

  return widget->NewPyRef();

  BA_PYTHON_CATCH;
}

static PyMethodDef PyHScrollWidgetDef = {
    "hscrollwidget",               // name
    (PyCFunction)PyHScrollWidget,  // method
    METH_VARARGS | METH_KEYWORDS,  // flags

    "hscrollwidget(*,\n"
    "  edit: bauiv1.Widget | None = None,\n"
    "  parent: bauiv1.Widget | None = None,\n"
    "  size: Sequence[float] | None = None,\n"
    "  position: Sequence[float] | None = None,\n"
    "  background: bool | None = None,\n"
    "  selected_child: bauiv1.Widget | None = None,\n"
    "  capture_arrows: bool | None = None,\n"
    "  on_select_call: Callable[[], None] | None = None,\n"
    "  center_small_content: bool | None = None,\n"
    "  color: Sequence[float] | None = None,\n"
    "  highlight: bool | None = None,\n"
    "  border_opacity: float | None = None,\n"
    "  simple_culling_h: float | None = None,\n"
    "  claims_left_right: bool | None = None,\n"
    "  claims_up_down: bool | None = None,\n"
    "  button_inset_left: float | None = None,\n"
    "  button_inset_right: float | None = None,\n"
    "  transition_in: bool | None = None,\n"
    "  scrollbar_visible: bool | None = None,\n"
    "  clean_layout: bool | None = None)  -> bauiv1.Widget\n"
    "\n"
    "Create or edit a horizontal scroll widget.\n"
    "\n"
    "The button insets nudge the page-left/page-right buttons in from\n"
    "the widget's edges; scrolls extended across screen margins use\n"
    "them to keep the buttons anchored to the virtual rect.\n"
    "\n"
    "With 'scrollbar_visible' False, the scroll bar is neither drawn nor\n"
    "mouse-grabbable; scrolling itself and layout are unaffected.\n"
    "\n"
    "With 'clean_layout', content is laid out with none of the widget's\n"
    "historical fudge offsets: it spans the full width (no inset at the\n"
    "ends), sits right on the bottom edge (not lifted to clear the scroll\n"
    "bar, which fades in over it), and is clipped exactly to the\n"
    "widget's bounds.\n"
    "\n"
    "Set 'transition_in' to have the page-left/page-right buttons animate\n"
    "in when the widget first appears. Off by default, so they simply\n"
    "start in their final form; turn it on only in ui that animates its\n"
    "own contents in, so the buttons arrive along with everything else.\n"
    "\n"
    "Pass a valid existing bauiv1.Widget as 'edit' to modify it; otherwise\n"
    "a new one is created and returned. Arguments that are not set to None\n"
    "are applied to the Widget.",
};

// ------------------------------ textwidget -----------------------------------

static auto PyTextWidget(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  PyObject* size_obj{Py_None};
  PyObject* pos_obj{Py_None};
  PyObject* text_obj{Py_None};
  PyObject* v_align_obj{Py_None};
  PyObject* h_align_obj{Py_None};
  PyObject* editable_obj{Py_None};
  PyObject* padding_obj{Py_None};
  PyObject* on_submit_call_obj{Py_None};
  PyObject* on_apply_call_obj{Py_None};
  // REMOVE WHEN API 9 SUPPORT ENDS (deprecated alias of on_submit_call).
  PyObject* on_return_press_call_obj{Py_None};
  PyObject* on_activate_call_obj{Py_None};
  PyObject* selectable_obj{Py_None};
  PyObject* max_chars_obj{Py_None};
  PyObject* color_obj{Py_None};
  PyObject* click_activate_obj{Py_None};
  PyObject* on_select_call_obj{Py_None};
  PyObject* maxwidth_obj{Py_None};
  PyObject* max_height_obj{Py_None};
  PyObject* scale_obj{Py_None};
  PyObject* corner_scale_obj{Py_None};
  PyObject* always_highlight_obj{Py_None};
  PyObject* draw_controller_obj{Py_None};
  PyObject* description_obj{Py_None};
  PyObject* transition_delay_obj{Py_None};
  PyObject* flatness_obj{Py_None};
  PyObject* shadow_obj{Py_None};
  PyObject* big_obj{Py_None};
  PyObject* parent_obj{Py_None};
  ContainerWidget* parent_widget{};
  PyObject* edit_obj{Py_None};
  PyObject* query_obj{Py_None};
  PyObject* autoselect_obj{Py_None};
  PyObject* rotate_obj{Py_None};
  PyObject* enabled_obj{Py_None};
  PyObject* force_internal_editing_obj{Py_None};
  PyObject* always_show_carat_obj{Py_None};
  PyObject* extra_touch_border_scale_obj{Py_None};
  PyObject* res_scale_obj{Py_None};
  PyObject* query_max_chars_obj{Py_None};
  PyObject* query_description_obj{Py_None};
  PyObject* adapter_finished_obj{Py_None};
  PyObject* glow_type_obj{Py_None};
  PyObject* allow_clear_button_obj{Py_None};
  PyObject* id_obj{Py_None};
  PyObject* literal_obj{Py_None};
  PyObject* depth_range_obj{Py_None};
  PyObject* transition_type_obj{Py_None};
  PyObject* password_obj{Py_None};
  PyObject* query_password_obj{Py_None};
  PyObject* string_edit_kind_obj{Py_None};
  PyObject* query_string_edit_kind_obj{Py_None};
  PyObject* invoke_submit_obj{Py_None};
  // REMOVE WHEN API 9 SUPPORT ENDS (deprecated alias of invoke_submit).
  PyObject* invoke_return_press_obj{Py_None};

  static const char* kwlist[] = {"edit",
                                 "parent",
                                 "id",
                                 "size",
                                 "position",
                                 "text",
                                 "v_align",
                                 "h_align",
                                 "editable",
                                 "padding",
                                 "on_submit_call",
                                 "on_apply_call",
                                 "on_activate_call",
                                 "selectable",
                                 "query",
                                 "max_chars",
                                 "color",
                                 "click_activate",
                                 "on_select_call",
                                 "always_highlight",
                                 "draw_controller",
                                 "scale",
                                 "corner_scale",
                                 "description",
                                 "transition_delay",
                                 "maxwidth",
                                 "max_height",
                                 "flatness",
                                 "shadow",
                                 "autoselect",
                                 "rotate",
                                 "enabled",
                                 "force_internal_editing",
                                 "always_show_carat",
                                 "big",
                                 "extra_touch_border_scale",
                                 "res_scale",
                                 "query_max_chars",
                                 "query_description",
                                 "adapter_finished",
                                 "glow_type",
                                 "allow_clear_button",
                                 "literal",
                                 "depth_range",
                                 "transition_type",
                                 "password",
                                 "query_password",
                                 "string_edit_kind",
                                 "query_string_edit_kind",
                                 "invoke_submit",
                                 "on_return_press_call",
                                 "invoke_return_press",
                                 nullptr};
  if (!PyArg_ParseTupleAndKeywords(
          args, keywds, "|OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO",
          const_cast<char**>(kwlist), &edit_obj, &parent_obj, &id_obj,
          &size_obj, &pos_obj, &text_obj, &v_align_obj, &h_align_obj,
          &editable_obj, &padding_obj, &on_submit_call_obj, &on_apply_call_obj,
          &on_activate_call_obj, &selectable_obj, &query_obj, &max_chars_obj,
          &color_obj, &click_activate_obj, &on_select_call_obj,
          &always_highlight_obj, &draw_controller_obj, &scale_obj,
          &corner_scale_obj, &description_obj, &transition_delay_obj,
          &maxwidth_obj, &max_height_obj, &flatness_obj, &shadow_obj,
          &autoselect_obj, &rotate_obj, &enabled_obj,
          &force_internal_editing_obj, &always_show_carat_obj, &big_obj,
          &extra_touch_border_scale_obj, &res_scale_obj, &query_max_chars_obj,
          &query_description_obj, &adapter_finished_obj, &glow_type_obj,
          &allow_clear_button_obj, &literal_obj, &depth_range_obj,
          &transition_type_obj, &password_obj, &query_password_obj,
          &string_edit_kind_obj, &query_string_edit_kind_obj,
          &invoke_submit_obj, &on_return_press_call_obj,
          &invoke_return_press_obj))
    return nullptr;

  // REMOVE WHEN API 9 SUPPORT ENDS: fold the deprecated aliases in.
  if (on_return_press_call_obj != Py_None) {
    if (PyErr_WarnEx(PyExc_DeprecationWarning,
                     "textwidget's on_return_press_call arg will be removed"
                     " when api 9 support ends; use on_submit_call instead.",
                     1)
        == -1) {
      return nullptr;
    }
    if (on_submit_call_obj == Py_None) {
      on_submit_call_obj = on_return_press_call_obj;
    }
  }
  if (invoke_return_press_obj != Py_None) {
    if (PyErr_WarnEx(PyExc_DeprecationWarning,
                     "textwidget's invoke_return_press arg will be removed"
                     " when api 9 support ends; use invoke_submit instead.",
                     1)
        == -1) {
      return nullptr;
    }
    if (invoke_submit_obj == Py_None) {
      invoke_submit_obj = invoke_return_press_obj;
    }
  }

  if (!g_base->CurrentContext().IsEmpty()) {
    throw Exception("UI functions must be called with no context set.");
  }

  // Grab the edited widget or create a new one.
  Object::Ref<TextWidget> widget;

  // Handle query special cases first.
  if (query_obj != Py_None) {
    widget = dynamic_cast<TextWidget*>(UIV1Python::GetPyWidget(query_obj));
    if (!widget.exists()) {
      throw Exception("Invalid or nonexistent widget.",
                      PyExcType::kWidgetNotFound);
    }
    return PyUnicode_FromString(widget->GetQueryText().c_str());
  }
  if (query_max_chars_obj != Py_None) {
    widget =
        dynamic_cast<TextWidget*>(UIV1Python::GetPyWidget(query_max_chars_obj));
    if (!widget.exists()) {
      throw Exception("Invalid or nonexistent widget.",
                      PyExcType::kWidgetNotFound);
    }
    return PyLong_FromLong(widget->max_chars());
  }
  if (query_description_obj != Py_None) {
    widget = dynamic_cast<TextWidget*>(
        UIV1Python::GetPyWidget(query_description_obj));
    if (!widget.exists()) {
      throw Exception("Invalid or nonexistent widget.",
                      PyExcType::kWidgetNotFound);
    }
    return PyUnicode_FromString(widget->description().c_str());
  }
  if (query_password_obj != Py_None) {
    widget =
        dynamic_cast<TextWidget*>(UIV1Python::GetPyWidget(query_password_obj));
    if (!widget.exists()) {
      throw Exception("Invalid or nonexistent widget.",
                      PyExcType::kWidgetNotFound);
    }
    if (widget->password()) {
      Py_RETURN_TRUE;
    }
    Py_RETURN_FALSE;
  }
  if (query_string_edit_kind_obj != Py_None) {
    widget = dynamic_cast<TextWidget*>(
        UIV1Python::GetPyWidget(query_string_edit_kind_obj));
    if (!widget.exists()) {
      throw Exception("Invalid or nonexistent widget.",
                      PyExcType::kWidgetNotFound);
    }
    return PyUnicode_FromString(widget->string_edit_kind().c_str());
  }

  // Ok it's not a query; it's a create or edit.

  // Gather up any user code triggered by this stuff and run it at the end
  // before we return.
  base::UI::OperationContext ui_op_context;

  if (edit_obj != Py_None) {
    widget = dynamic_cast<TextWidget*>(UIV1Python::GetPyWidget(edit_obj));
    if (!widget.exists()) {
      throw Exception("Invalid or nonexistent widget.",
                      PyExcType::kWidgetNotFound);
    }
  } else {
    parent_widget = parent_obj == Py_None
                        ? g_ui_v1->screen_root_widget()
                        : dynamic_cast<ContainerWidget*>(
                              UIV1Python::GetPyWidget(parent_obj));
    if (!parent_widget) {
      throw Exception("Invalid or nonexistent parent widget.",
                      PyExcType::kWidgetNotFound);
    }
    widget = Object::New<TextWidget>();
  }

  // Set applicable values.
  if (max_chars_obj != Py_None) {
    widget->set_max_chars(Python::GetInt(max_chars_obj));
  }
  if (size_obj != Py_None) {
    Point2D p = Python::GetPoint2D(size_obj);
    widget->SetWidth(p.x);
    widget->SetHeight(p.y);
  }
  if (description_obj != Py_None) {
    // FIXME - compiling Lstr values to flat strings before passing them in;
    //  we should probably extend TextWidget to handle this internally, but
    //  punting on that for now.
    widget->set_description(g_base->assets->CompileResourceString(
        g_base->python->GetPyLString(description_obj)));
  }
  if (autoselect_obj != Py_None) {
    widget->set_auto_select(Python::GetBool(autoselect_obj));
  }
  if (transition_type_obj != Py_None) {
    std::string transition_type = Python::GetString(transition_type_obj);
    if (transition_type == "in_left") {
      widget->set_transition_type(TextWidget::TransitionType::kInLeft);
    } else if (transition_type == "scale") {
      widget->set_transition_type(TextWidget::TransitionType::kScale);
    } else {
      throw Exception("Invalid transition_type: '" + transition_type + "'.",
                      PyExcType::kValue);
    }
  }
  if (transition_delay_obj != Py_None) {
    // We accept this as seconds; widget takes milliseconds.
    widget->set_transition_delay(1000.0f
                                 * Python::GetFloat(transition_delay_obj));
  }
  if (enabled_obj != Py_None) {
    widget->SetEnabled(Python::GetBool(enabled_obj));
  }
  if (always_show_carat_obj != Py_None) {
    widget->set_always_show_carat(Python::GetBool(always_show_carat_obj));
  }
  if (big_obj != Py_None) {
    widget->SetBig(Python::GetBool(big_obj));
  }
  if (force_internal_editing_obj != Py_None) {
    widget->set_force_internal_editing(
        Python::GetBool(force_internal_editing_obj));
  }
  if (pos_obj != Py_None) {
    Point2D p = Python::GetPoint2D(pos_obj);
    widget->set_translate(p.x, p.y);
  }
  if (flatness_obj != Py_None) {
    widget->set_flatness(Python::GetFloat(flatness_obj));
  }
  if (rotate_obj != Py_None) {
    widget->set_rotate(Python::GetFloat(rotate_obj));
  }
  if (shadow_obj != Py_None) {
    widget->set_shadow(Python::GetFloat(shadow_obj));
  }
  if (maxwidth_obj != Py_None) {
    widget->set_max_width(Python::GetFloat(maxwidth_obj));
  }
  if (max_height_obj != Py_None) {
    widget->set_max_height(Python::GetFloat(max_height_obj));
  }
  // note: need to make sure to set this before settings text
  // (influences whether we look for json strings or not)
  if (editable_obj != Py_None) {
    widget->SetEditable(Python::GetBool(editable_obj));
  }

  // Make sure to set literal *before* text, as it can affect how we interpret
  // text.
  if (literal_obj != Py_None) {
    widget->SetLiteral(Python::GetBool(literal_obj));
  }
  if (string_edit_kind_obj != Py_None) {
    widget->set_string_edit_kind(Python::GetString(string_edit_kind_obj));
  }
  if (invoke_submit_obj != Py_None && Python::GetBool(invoke_submit_obj)) {
    widget->InvokeSubmit();
  }
  if (password_obj != Py_None) {
    widget->set_password(Python::GetBool(password_obj));
  }
  if (text_obj != Py_None) {
    // Native language-strings are retained by the widget and
    // re-evaluated on language changes (mirroring legacy Lstr
    // behavior); everything else flattens through the standard string
    // slot. Per the D28 semantic split, widgets accept only the
    // verified-local babase.LangStr form — authoring-spec values must
    // be verified (resolved) before display, so no implicit
    // spec-conversion here.
    if (base::PythonClassLangStr::Check(text_obj)) {
      widget->SetLangStr(base::PythonClassLangStr::FromPyObj(text_obj).value());
    } else {
      widget->SetText(g_base->python->GetPyLString(text_obj));
    }
  }
  if (h_align_obj != Py_None) {
    std::string halign = Python::GetString(h_align_obj);
    if (halign == "left") {
      widget->SetHAlign(TextWidget::HAlign::kLeft);
    } else if (halign == "center") {
      widget->SetHAlign(TextWidget::HAlign::kCenter);
    } else if (halign == "right") {
      widget->SetHAlign(TextWidget::HAlign::kRight);
    } else {
      throw Exception("Invalid halign.", PyExcType::kValue);
    }
  }
  if (v_align_obj != Py_None) {
    std::string valign = Python::GetString(v_align_obj);
    if (valign == "top") {
      widget->SetVAlign(TextWidget::VAlign::kTop);
    } else if (valign == "center") {
      widget->SetVAlign(TextWidget::VAlign::kCenter);
    } else if (valign == "bottom") {
      widget->SetVAlign(TextWidget::VAlign::kBottom);
    } else {
      throw Exception("Invalid valign.", PyExcType::kValue);
    }
  }
  if (always_highlight_obj != Py_None) {
    widget->set_always_highlight(Python::GetBool(always_highlight_obj));
  }
  if (padding_obj != Py_None) {
    widget->set_padding(Python::GetFloat(padding_obj));
  }
  if (scale_obj != Py_None) {
    widget->set_center_scale(Python::GetFloat(scale_obj));
  }
  // *normal* widget scale.. we currently plug 'scale' into 'centerScale'.  ew.
  if (corner_scale_obj != Py_None) {
    widget->set_scale(Python::GetFloat(corner_scale_obj));
  }
  if (draw_controller_obj != Py_None) {
    auto* dcw = UIV1Python::GetPyWidget(draw_controller_obj);
    if (!dcw) {
      throw Exception("Invalid or nonexistent draw-controller widget.",
                      PyExcType::kWidgetNotFound);
    }
    widget->set_draw_control_parent(dcw);
  }
  if (on_submit_call_obj != Py_None) {
    widget->SetOnSubmitCall(on_submit_call_obj);
  }
  if (on_apply_call_obj != Py_None) {
    widget->SetOnApplyCall(on_apply_call_obj);
  }
  if (on_select_call_obj != Py_None) {
    widget->SetOnSelectCall(on_select_call_obj);
  }
  if (on_activate_call_obj != Py_None) {
    widget->SetOnActivateCall(on_activate_call_obj);
  }
  if (selectable_obj != Py_None)
    widget->set_selectable(Python::GetBool(selectable_obj));

  if (color_obj != Py_None) {
    std::vector<float> c = Python::GetFloats(color_obj);
    if (c.size() == 3) {
      widget->set_color(c[0], c[1], c[2], 1.0f);
    } else if (c.size() == 4) {
      widget->set_color(c[0], c[1], c[2], c[3]);
    } else {
      throw Exception("Expected 3 or 4 floats for color.", PyExcType::kValue);
    }
  }
  if (click_activate_obj != Py_None) {
    widget->set_click_activate(Python::GetBool(click_activate_obj));
  }
  if (extra_touch_border_scale_obj != Py_None) {
    widget->set_extra_touch_border_scale(
        Python::GetFloat(extra_touch_border_scale_obj));
  }
  if (res_scale_obj != Py_None) {
    widget->set_res_scale(Python::GetFloat(res_scale_obj));
  }
  if (adapter_finished_obj != Py_None) {
    if (adapter_finished_obj == Py_True) {
      widget->AdapterFinished();
    } else {
      throw Exception("Unexpected value for adapter_finished");
    }
  }
  if (glow_type_obj != Py_None) {
    auto glow_type_s = Python::GetString(glow_type_obj);
    TextWidget::GlowType glow_type;
    if (glow_type_s == "uniform") {
      glow_type = TextWidget::GlowType::kUniform;
    } else if (glow_type_s == "gradient") {
      glow_type = TextWidget::GlowType::kGradient;
    } else {
      throw Exception("Invalid glow_type: " + glow_type_s, PyExcType::kValue);
    }
    widget->SetGlowType(glow_type);
  }
  if (allow_clear_button_obj != Py_None) {
    widget->set_allow_clear_button(Python::GetBool(allow_clear_button_obj));
  }
  if (id_obj != Py_None) {
    widget->SetID(Python::GetString(id_obj));
  }
  if (depth_range_obj != Py_None) {
    auto depth_range = Python::GetFloats(depth_range_obj);
    if (depth_range.size() != 2) {
      throw Exception("Expected 2 float values.", PyExcType::kValue);
    }
    if (depth_range[0] < 0.0f || depth_range[1] > 1.0f
        || depth_range[1] <= depth_range[0]) {
      throw Exception(
          "Invalid depth range values;"
          " values must be between 0 and 1 and second value must be larger "
          "than first.",
          PyExcType::kValue);
    }
    widget->set_depth_range(depth_range[0], depth_range[1]);
  }

  // If making a new widget, add it at the end.
  if (edit_obj == Py_None) {
    g_ui_v1->AddWidget(widget.get(), parent_widget);
  }

  // Run any calls built up by UI callbacks.
  ui_op_context.Finish();

  return widget->NewPyRef();

  BA_PYTHON_CATCH;
}

static PyMethodDef PyTextWidgetDef = {
    "textwidget",                  // name
    (PyCFunction)PyTextWidget,     // method
    METH_VARARGS | METH_KEYWORDS,  // flags

    "textwidget(*,\n"
    "  edit: bauiv1.Widget | None = None,\n"
    "  parent: bauiv1.Widget | None = None,\n"
    "  id: str | None = None,\n"
    "  size: Sequence[float] | None = None,\n"
    "  position: Sequence[float] | None = None,\n"
    "  text: str | bauiv1.Lstr | bauiv1.LangStr | None = None,\n"
    "  v_align: str | None = None,\n"
    "  h_align: str | None = None,\n"
    "  editable: bool | None = None,\n"
    "  padding: float | None = None,\n"
    "  on_submit_call: Callable[[], None] | None = None,\n"
    "  on_apply_call: Callable[[str], None] | None = None,\n"
    "  on_activate_call: Callable[[], None] | None = None,\n"
    "  selectable: bool | None = None,\n"
    "  query: bauiv1.Widget | None = None,\n"
    "  max_chars: int | None = None,\n"
    "  color: Sequence[float] | None = None,\n"
    "  click_activate: bool | None = None,\n"
    "  on_select_call: Callable[[], None] | None = None,\n"
    "  always_highlight: bool | None = None,\n"
    "  draw_controller: bauiv1.Widget | None = None,\n"
    "  scale: float | None = None,\n"
    "  corner_scale: float | None = None,\n"
    "  description: str | bauiv1.Lstr | bauiv1.LangStr | None = None,\n"
    "  transition_delay: float | None = None,\n"
    "  maxwidth: float | None = None,\n"
    "  max_height: float | None = None,\n"
    "  flatness: float | None = None,\n"
    "  shadow: float | None = None,\n"
    "  autoselect: bool | None = None,\n"
    "  rotate: float | None = None,\n"
    "  enabled: bool | None = None,\n"
    "  force_internal_editing: bool | None = None,\n"
    "  always_show_carat: bool | None = None,\n"
    "  big: bool | None = None,\n"
    "  extra_touch_border_scale: float | None = None,\n"
    "  res_scale: float | None = None,"
    "  query_max_chars: bauiv1.Widget | None = None,\n"
    "  query_description: bauiv1.Widget | None = None,\n"
    "  adapter_finished: bool | None = None,\n"
    "  glow_type: str | None = None,\n"
    "  allow_clear_button: bool | None = None,\n"
    "  literal: bool | None = None,\n"
    "  depth_range: tuple[float, float] | None = None,\n"
    "  transition_type: Literal['in_left', 'scale'] | None = None,\n"
    "  password: bool | None = None,\n"
    "  query_password: bauiv1.Widget | None = None,\n"
    "  string_edit_kind: str | None = None,\n"
    "  query_string_edit_kind: bauiv1.Widget | None = None,\n"
    "  invoke_submit: bool | None = None,\n"
    "  on_return_press_call: Callable[[], None] | None = None,\n"
    "  invoke_return_press: bool | None = None,\n"
    ") -> bauiv1.Widget\n"
    "\n"
    "Create or edit a text widget.\n"
    "\n"
    "Pass a valid existing bauiv1.Widget as 'edit' to modify it; otherwise\n"
    "a new one is created and returned. Arguments that are not set to None\n"
    "are applied to the Widget.\n"
    "\n"
    "A text widget with ``enabled`` False draws dimmed and can't be\n"
    "edited or activated, but remains selectable (if it otherwise would\n"
    "be), so navigation around it is unaffected.\n"
    "\n"
    "``on_submit_call`` runs when the text is *submitted*: an enter press\n"
    "while editing inline, or the action key / commit button of a\n"
    "platform string-edit dialog for string_edit_kinds that submit\n"
    "(see babase.StringEditKind). It is not a change notification; text\n"
    "can be edited without it ever running. ``invoke_submit`` runs it on\n"
    "demand.\n"
    "\n"
    "``on_apply_call`` runs whenever an edit is *applied* to the widget:\n"
    "a platform string-edit dialog closing with a value, inline editing\n"
    "ending (return, or focus leaving the widget), or the clear button.\n"
    "Not per character, and only when the text actually changed since it\n"
    "was last applied. It is passed the new text (as of the apply; the\n"
    "call runs deferred). Applies precede submits, so an enter press runs\n"
    "this and then ``on_submit_call``. Setting ``text`` from code does not\n"
    "count as an apply.\n"
    "\n"
    "``on_return_press_call`` and ``invoke_return_press`` are deprecated\n"
    "aliases of those two and will be removed when api 9 support ends.",
};

// ------------------------------- widget --------------------------------------

static auto PyWidgetCall(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;

  PyObject* edit_obj{Py_None};
  PyObject* down_widget_obj{Py_None};
  PyObject* up_widget_obj{Py_None};
  PyObject* left_widget_obj{Py_None};
  PyObject* right_widget_obj{Py_None};
  PyObject* show_buffer_top_obj{Py_None};
  PyObject* show_buffer_bottom_obj{Py_None};
  PyObject* show_buffer_left_obj{Py_None};
  PyObject* show_buffer_right_obj{Py_None};
  PyObject* depth_range_obj{Py_None};
  PyObject* autoselect_obj{Py_None};
  PyObject* allow_preserve_selection_obj{Py_None};
  PyObject* auto_select_toolbars_only_obj{Py_None};
  PyObject* draw_behind_obj{Py_None};

  static const char* kwlist[] = {"edit",
                                 "up_widget",
                                 "down_widget",
                                 "left_widget",
                                 "right_widget",
                                 "show_buffer_top",
                                 "show_buffer_bottom",
                                 "show_buffer_left",
                                 "show_buffer_right",
                                 "depth_range",
                                 "autoselect",
                                 "allow_preserve_selection",
                                 "auto_select_toolbars_only",
                                 "draw_behind",
                                 nullptr};
  if (!PyArg_ParseTupleAndKeywords(
          args, keywds, "O|OOOOOOOOOOOOO", const_cast<char**>(kwlist),
          &edit_obj, &up_widget_obj, &down_widget_obj, &left_widget_obj,
          &right_widget_obj, &show_buffer_top_obj, &show_buffer_bottom_obj,
          &show_buffer_left_obj, &show_buffer_right_obj, &depth_range_obj,
          &autoselect_obj, &allow_preserve_selection_obj,
          &auto_select_toolbars_only_obj, &draw_behind_obj))
    return nullptr;

  if (!g_base->CurrentContext().IsEmpty()) {
    throw Exception("UI functions must be called with no context set.");
  }

  // Gather up any user code triggered by this stuff and run it at the end
  // before we return.
  base::UI::OperationContext ui_op_context;

  Widget* widget{};
  if (edit_obj != Py_None) {
    widget = UIV1Python::GetPyWidget(edit_obj);
  }
  if (!widget) {
    throw Exception("Invalid or nonexistent widget passed.",
                    PyExcType::kWidgetNotFound);
  }

  if (down_widget_obj != Py_None) {
    Widget* down_widget = UIV1Python::GetPyWidget(down_widget_obj);
    if (!down_widget) {
      throw Exception("Invalid down widget.", PyExcType::kWidgetNotFound);
    }
    widget->SetDownWidget(down_widget);
  }
  if (up_widget_obj != Py_None) {
    Widget* up_widget = UIV1Python::GetPyWidget(up_widget_obj);
    if (!up_widget) {
      throw Exception("Invalid up widget.", PyExcType::kWidgetNotFound);
    }
    widget->SetUpWidget(up_widget);
  }
  if (left_widget_obj != Py_None) {
    Widget* left_widget = UIV1Python::GetPyWidget(left_widget_obj);
    if (!left_widget) {
      throw Exception("Invalid left widget.", PyExcType::kWidgetNotFound);
    }
    widget->SetLeftWidget(left_widget);
  }
  if (right_widget_obj != Py_None) {
    Widget* right_widget = UIV1Python::GetPyWidget(right_widget_obj);
    if (!right_widget) {
      throw Exception("Invalid right widget.", PyExcType::kWidgetNotFound);
    }
    widget->SetRightWidget(right_widget);
  }
  if (show_buffer_top_obj != Py_None) {
    widget->set_show_buffer_top(Python::GetFloat(show_buffer_top_obj));
  }
  if (show_buffer_bottom_obj != Py_None) {
    widget->set_show_buffer_bottom(Python::GetFloat(show_buffer_bottom_obj));
  }
  if (show_buffer_left_obj != Py_None) {
    widget->set_show_buffer_left(Python::GetFloat(show_buffer_left_obj));
  }
  if (show_buffer_right_obj != Py_None) {
    widget->set_show_buffer_right(Python::GetFloat(show_buffer_right_obj));
  }
  if (depth_range_obj != Py_None) {
    auto depth_range = Python::GetFloats(depth_range_obj);
    if (depth_range.size() != 2) {
      throw Exception("Expected 2 float values.", PyExcType::kValue);
    }
    if (depth_range[0] < 0.0 || depth_range[1] > 1.0
        || depth_range[1] <= depth_range[0]) {
      throw Exception(
          "Invalid depth range values;"
          " values must be between 0 and 1 and second value must be larger "
          "than first.",
          PyExcType::kValue);
    }
    widget->set_depth_range(depth_range[0], depth_range[1]);
  }
  if (autoselect_obj != Py_None) {
    widget->set_auto_select(Python::GetBool(autoselect_obj));
  }
  if (allow_preserve_selection_obj != Py_None) {
    widget->set_allow_preserve_selection(
        Python::GetBool(allow_preserve_selection_obj));
  }
  if (auto_select_toolbars_only_obj != Py_None) {
    widget->set_auto_select_toolbars_only(
        Python::GetBool(auto_select_toolbars_only_obj));
  }

  if (draw_behind_obj != Py_None) {
    widget->set_draw_behind(Python::GetBool(draw_behind_obj));
  }

  // Run any calls built up by UI callbacks.
  ui_op_context.Finish();

  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyWidgetDef = {
    "widget",                      // name
    (PyCFunction)PyWidgetCall,     // method
    METH_VARARGS | METH_KEYWORDS,  // flags

    "widget(*,\n"
    "  edit: bauiv1.Widget,\n"
    "  up_widget: bauiv1.Widget | None = None,\n"
    "  down_widget: bauiv1.Widget | None = None,\n"
    "  left_widget: bauiv1.Widget | None = None,\n"
    "  right_widget: bauiv1.Widget | None = None,\n"
    "  show_buffer_top: float | None = None,\n"
    "  show_buffer_bottom: float | None = None,\n"
    "  show_buffer_left: float | None = None,\n"
    "  show_buffer_right: float | None = None,\n"
    "  depth_range: tuple[float, float] | None = None,\n"
    "  autoselect: bool | None = None,\n"
    "  allow_preserve_selection: bool | None = None,\n"
    "  auto_select_toolbars_only: bool | None = None,\n"
    "  draw_behind: bool | None = None,\n"
    ") -> None\n"
    "\n"
    "Edit common attributes of any widget.\n"
    "\n"
    "Unlike other UI calls, this can only be used to edit, not to "
    "create.\n"
    "\n"
    "``draw_behind`` puts a widget in a single-depth container (such "
    "as a scroll area's contents) behind its siblings, which otherwise "
    "share one depth slice and can fight where they overlap; for "
    "backings laid beneath other widgets.",
};

// ------------------------------- uibounds ------------------------------------

auto PyUIBounds(PyObject* self, PyObject* args, PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  static const char* kwlist[] = {nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "",
                                   const_cast<char**>(kwlist))) {
    return nullptr;
  }
  float x, virtual_res_y;
  x = 0.5f * base::kBaseVirtualResX;
  virtual_res_y = base::kBaseVirtualResY;
  float y = 0.5f * virtual_res_y;
  return Py_BuildValue("(ffff)", -x, x, -y, y);
  BA_PYTHON_CATCH;
}

static PyMethodDef PyUIBoundsDef = {
    "uibounds",                    // name
    (PyCFunction)PyUIBounds,       // method
    METH_VARARGS | METH_KEYWORDS,  // flags

    "uibounds() -> tuple[float, float, float, float]\n"
    "\n"
    "Returns ui-bounds values: (x-min, x-max, y-min, y-max).\n"
    "\n"
    "This is the range of values that can be plugged into 'stack_offset' for\n"
    "a :meth:`bauiv1.containerwidget()` call while guaranteeing that its\n"
    "center remains onscreen.",
};

// -------------------------- get_special_widget -------------------------------

static auto PyGetSpecialWidget(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;

  const char* name;
  static const char* kwlist[] = {"name", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "s",
                                   const_cast<char**>(kwlist), &name)) {
    return nullptr;
  }
  BA_PRECONDITION(g_base->InLogicThread());
  RootWidget* root_widget = g_ui_v1->root_widget();
  BA_PRECONDITION(root_widget);
  Widget* w = root_widget->GetSpecialWidget(name);
  if (w == nullptr) {
    throw Exception("Invalid special widget name '" + std::string(name) + "'.",
                    PyExcType::kValue);
  }
  return w->NewPyRef();
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyGetSpecialWidgetDef = {
    "get_special_widget",             // name
    (PyCFunction)PyGetSpecialWidget,  // method
    METH_VARARGS | METH_KEYWORDS,     // flags

    "get_special_widget(name:\n"
    "    Literal[\n"
    "        'squad_button',\n"
    "        'back_button',\n"
    "        'menu_button',\n"
    "        'account_button',\n"
    "        'achievements_button',\n"
    "        'settings_button',\n"
    "        'inbox_button',\n"
    "        'store_button',\n"
    "        'get_tokens_button',\n"
    "        'inventory_button',\n"
    "        'tickets_meter',\n"
    "        'tokens_meter',\n"
    "        'trophy_meter',\n"
    "        'level_meter',\n"
    "        'overlay_stack',\n"
    "        'chest_0_button',\n"
    "        'chest_1_button',\n"
    "        'chest_2_button',\n"
    "        'chest_3_button',\n"
    "    ]) -> bauiv1.Widget\n"
    "\n"
    "Return special widgets located in system toolbars.",
};

// ------------------------- get_selected_widget -------------------------------

static auto PyGetSelectedWidget(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;

  BA_PRECONDITION(g_base->InLogicThread());
  if (Widget* w = g_ui_v1->GetSelectedWidget()) {
    return w->NewPyRef();
  }
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyGetSelectedWidgetDef = {
    "get_selected_widget",             // name
    (PyCFunction)PyGetSelectedWidget,  // method
    METH_NOARGS,                       // flags

    "get_selected_widget() -> bauiv1.Widget | None\n"
    "\n"
    "Return the current globally selected widget, if any.",
};

// ------------------------------ play_swish -----------------------------------

static auto PyPlaySwish(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;
  BA_PRECONDITION(g_base->InLogicThread());
  g_ui_v1->PlaySwish();
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyPlaySwishDef = {
    "play_swish",              // name
    (PyCFunction)PyPlaySwish,  // method
    METH_NOARGS,               // flags

    "play_swish() -> None\n"
    "\n"
    "Play the standard ui swish.\n"
    "\n"
    "A random pick of the current ui asset set's swish variants -- the\n"
    "same sound buttons make when pressed. Use this for any ui\n"
    "transition sound (opening or closing a window, say) rather than\n"
    "playing a particular swish sound yourself.",
};

// ----------------------------- widget_by_id ----------------------------------

static auto PyWidgetByID(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;

  const char* id;
  static const char* kwlist[] = {"id", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "s",
                                   const_cast<char**>(kwlist), &id)) {
    return nullptr;
  }
  BA_PRECONDITION(g_base->InLogicThread());
  Widget* w{g_ui_v1->WidgetByID(id)};
  if (w != nullptr) {
    return w->NewPyRef();
  }
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyWidgetByIDDef = {
    "widget_by_id",                // name
    (PyCFunction)PyWidgetByID,     // method
    METH_VARARGS | METH_KEYWORDS,  // flags

    "widget_by_id(id: str) -> bauiv1.Widget | None\n"
    "\n"
    "Return a widget with the given ID, or None if there is none.",
};

// ---------------------- root_ui_open_state_change ----------------------------

static auto PyUIOpenStateChange(PyObject* self, PyObject* args,
                                PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;

  const char* tag;
  int change;
  static const char* kwlist[] = {"tag", "change", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "si",
                                   const_cast<char**>(kwlist), &tag, &change)) {
    return nullptr;
  }

  // We can be called from any thread; push to the logic thread.
  base::g_base->logic->event_loop()->PushCall(
      [tagstr = std::string(tag), change] {
        g_ui_v1->UIOpenStateChange(tagstr, change);
      });

  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyUIOpenStateChangeDef = {
    "ui_open_state_change",            // name
    (PyCFunction)PyUIOpenStateChange,  // method
    METH_VARARGS | METH_KEYWORDS,      // flags

    "ui_open_state_change(tag: str, change: int) -> None\n"
    "\n"
    ":meta private:",
};

// -------------------------- root_ui_back_press -------------------------------

static auto PyRootUIBackPress(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;
  BA_PRECONDITION(g_base->InLogicThread());
  RootWidget* root_widget = g_ui_v1->root_widget();
  BA_PRECONDITION(root_widget);
  root_widget->BackPress();
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyRootUIBackPressDef = {
    "root_ui_back_press",            // name
    (PyCFunction)PyRootUIBackPress,  // method
    METH_NOARGS,                     // flags
    "root_ui_back_press() -> None\n"
    "\n"
    "Handle a press of the global back button.\n"
    "\n"
    ":meta private:",
};

// ----------------------------- is_available ----------------------------------

static auto PyIsAvailable(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;
  BA_PRECONDITION(g_base->InLogicThread());

  // Consider ourself available if the active ui delegate is us.
  if (dynamic_cast<UIV1FeatureSet*>(g_base->ui->delegate()) != nullptr) {
    Py_RETURN_TRUE;
  } else {
    Py_RETURN_FALSE;
  }
  BA_PYTHON_CATCH;
}

static PyMethodDef PyIsAvailableDef = {"is_available",              // name
                                       (PyCFunction)PyIsAvailable,  // method
                                       METH_NOARGS,                 // flags

                                       "is_available() -> bool\n"
                                       "\n"
                                       ":meta private:"};

// --------------------------- on_ui_scale_change ------------------------------

static auto PyOnUIScaleChange(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;
  BA_PRECONDITION(g_base->InLogicThread());

  g_ui_v1->OnUIScaleChange();
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyOnUIScaleChangeDef = {
    "on_ui_scale_change",            // name
    (PyCFunction)PyOnUIScaleChange,  // method
    METH_NOARGS,                     // flags

    "on_ui_scale_change() -> None\n"
    "\n"
    ":meta private:",
};

// ------------------------ root_ui_pause_updates ------------------------------

static auto PyRootUIPauseUpdates(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;
  BA_PRECONDITION(g_base->InLogicThread());

  auto* root_widget = g_ui_v1->root_widget();
  BA_PRECONDITION(root_widget);
  root_widget->PauseUpdates();

  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyRootUIPauseUpdatesDef = {
    "root_ui_pause_updates",            // name
    (PyCFunction)PyRootUIPauseUpdates,  // method
    METH_NOARGS,                        // flags

    "root_ui_pause_updates() -> None\n"
    "\n"
    "Temporarily pause updates to the root ui for animation purposes.\n"
    "Make sure that each call to this is matched by a call to \n"
    "root_ui_resume_updates()."};

// ------------------------ root_ui_resume_updates -----------------------------

static auto PyRootUIResumeUpdates(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;
  BA_PRECONDITION(g_base->InLogicThread());

  auto* root_widget = g_ui_v1->root_widget();
  BA_PRECONDITION(root_widget);
  root_widget->ResumeUpdates();

  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyRootUIResumeUpdatesDef = {
    "root_ui_resume_updates",            // name
    (PyCFunction)PyRootUIResumeUpdates,  // method
    METH_NOARGS,                         // flags

    "root_ui_resume_updates() -> None\n"
    "\n"
    "Resume paused updates to the root ui for animation purposes.",
};

// ----------------------------- reload_hooks ---------------------------------

static auto PyReloadHooks(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;

  g_ui_v1->python->ReloadHooks();

  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyReloadHooksDef = {
    "reload_hooks",              // name
    (PyCFunction)PyReloadHooks,  // method
    METH_NOARGS,                 // flags

    "reload_hooks() -> None\n"
    "\n"
    "Reload functions and other objects held by the native layer.\n"
    "Call this if you replace things in a hooks module to get the\n"
    "native layer to see your changes.",
};

// --------------------------- set_ui_asset_set -------------------------------

/// Pull a bauiv1.UIAssetSet apart into its native form.
///
/// The body is generated from the same spec as the dataclass and the
/// struct (see tools/batools/ui_assets.py); hand-writing it would just
/// relocate the drift problem it exists to prevent.
static auto UIAssetSetFromPyArgs(PyObject* args, UIAssetSet* out) -> bool {
#include "ballistica/ui_v1/generated/ui_asset_set_unpack.inc"
}

static auto PySetUIAssetSet(PyObject* self, PyObject* args) -> PyObject* {
  BA_PYTHON_TRY;
  UIAssetSet assets;
  if (!UIAssetSetFromPyArgs(args, &assets)) {
    return nullptr;
  }
  assert(assets.complete());
  g_ui_v1->set_assets(assets);

  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PySetUIAssetSetDef = {
    "set_ui_asset_set_native",     // name
    (PyCFunction)PySetUIAssetSet,  // method
    METH_VARARGS,                  // flags

    "set_ui_asset_set_native(*args: bauiv1.Texture | bauiv1.Mesh"
    " | bauiv1.Sound) -> None\n"
    "\n"
    "(internal) Supply the assets the widget layer draws itself with.\n"
    "\n"
    "Do not call this directly -- bauiv1.set_ui_asset_set() is the\n"
    "entry point. Args arrive positionally in spec order; both sides\n"
    "are generated from src/codegen/bauiv1codegen/ui_assets.py, so\n"
    "they cannot drift.",
};

// ------------------------- clear_ui_asset_set -------------------------------

static auto PyClearUIAssetSet(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;
  g_ui_v1->clear_assets();
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyClearUIAssetSetDef = {
    "clear_ui_asset_set_native",     // name
    (PyCFunction)PyClearUIAssetSet,  // method
    METH_NOARGS,                     // flags

    "clear_ui_asset_set_native() -> None\n"
    "\n"
    "(internal) Drop any app-mode-supplied ui asset set.\n"
    "\n"
    "Called by UIV1AppSubsystem.reset() at each app-mode switch so an\n"
    "incoming app-mode can never inherit the outgoing one's art.",
};

// -----------------------------------------------------------------------------

auto PythonMethodsUIV1::GetMethods() -> std::vector<PyMethodDef> {
  return {
      PyUIOpenStateChangeDef,
      PyRootUIBackPressDef,
      PyGetSpecialWidgetDef,
      PyGetSelectedWidgetDef,
      PyPlaySwishDef,
      PyWidgetByIDDef,
      PyButtonWidgetDef,
      PyCheckBoxWidgetDef,
      PyImageWidgetDef,
      PyGetDepictionControlDef,
      PySpinnerWidgetDef,
      PySliderWidgetDef,
      PyColumnWidgetDef,
      PyContainerWidgetDef,
      PyRowWidgetDef,
      PyScrollWidgetDef,
      PyHScrollWidgetDef,
      PyTextWidgetDef,
      PyWidgetDef,
      PyUIBoundsDef,
      PyGetSoundDef,
      PyGetTextureDef,
      PyGetQRCodeTextureDef,
      PyGetMeshDef,
      PyApSoundGetDef,
      PyApTextureGetDef,
      PyApMeshGetDef,
      PyIsAvailableDef,
      PyOnUIScaleChangeDef,
      PyRootUIPauseUpdatesDef,
      PyRootUIResumeUpdatesDef,
      PyReloadHooksDef,
      PySetUIAssetSetDef,
      PyClearUIAssetSetDef,
  };
}

}  // namespace ballistica::ui_v1
