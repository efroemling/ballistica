// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/node/local_display_node.h"

#include <Python.h>

#include <string>

#include "ballistica/base/python/class/python_class_context_ref.h"
#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging.h"
#include "ballistica/scene_v1/node/node_attribute.h"
#include "ballistica/scene_v1/node/node_type.h"
#include "ballistica/scene_v1/python/scene_v1_python.h"
#include "ballistica/scene_v1/support/local_display_context.h"
#include "ballistica/scene_v1/support/scene.h"
#include "ballistica/shared/python/python.h"

namespace ballistica::scene_v1 {

class LocalDisplayNodeType : public NodeType {
 public:
#define BA_NODE_TYPE_CLASS LocalDisplayNode
  BA_NODE_CREATE_CALL(CreateLocalDisplayNode);
  BA_STRING_ATTR(config, config, SetConfig);
  BA_BOOL_ATTR(visible, visible, SetVisible);
#undef BA_NODE_TYPE_CLASS

  LocalDisplayNodeType()
      : NodeType("localdisplay", CreateLocalDisplayNode),
        config(this),
        visible(this) {}
};

static NodeType* node_type{};

auto LocalDisplayNode::InitType() -> NodeType* {
  node_type = new LocalDisplayNodeType();
  return node_type;
}

LocalDisplayNode::LocalDisplayNode(Scene* scene) : Node(scene, node_type) {}

LocalDisplayNode::~LocalDisplayNode() {
  // Let our Python side wind down (expiring actors/etc.) while our
  // context is still valid, then take the context (and its scene, timers,
  // and everything created in it) down with us.
  ExpirePy_();
  if (context_.exists()) {
    context_->Shutdown();
  }
  context_.Clear();
}

void LocalDisplayNode::OnCreate() {
  assert(g_base->InLogicThread());

  // OnCreate runs on both the host (after initial attrs are set) and on
  // clients (via the kNodeOnCreate stream command), so this is the spot
  // where each machine spins up its own local side of us.
  if (created_) {
    return;
  }
  created_ = true;

  context_ = Object::New<LocalDisplayContext>(scene());

  PythonRef cref(base::PythonClassContextRef::Create(context_.get()),
                 PythonRef::kSteal);
  PythonRef args(Py_BuildValue("(OO)", BorrowPyRef(), cref.get()),
                 PythonRef::kSteal);
  {
    Python::ScopedCallLabel label("LocalDisplay instantiation");
    py_display_ = g_scene_v1->python->objs()
                      .Get(SceneV1Python::ObjID::kLocalDisplayClass)
                      .Call(args);
  }
  if (!py_display_.exists()) {
    g_core->logging->Log(LogName::kBa, LogLevel::kError,
                         "Error creating Python LocalDisplay for "
                             + GetObjectDescription() + ".");
    return;
  }
  context_->RegisterPyLocalDisplay(py_display_.get());

  // Now that getlocaldisplay() resolves to it, let it build its content.
  try {
    Python::ScopedCallLabel label("LocalDisplay start");
    py_display_.GetAttr("_start").Call();
  } catch (const std::exception& e) {
    g_core->logging->Log(LogName::kBa, LogLevel::kError,
                         "Error starting Python LocalDisplay for "
                             + GetObjectDescription() + ": " + e.what());
  }
}

void LocalDisplayNode::Step() {
  if (context_.exists()) {
    context_->Step();
  }
}

void LocalDisplayNode::Draw(base::FrameDef* frame_def) {
  if (context_.exists()) {
    context_->Draw(frame_def);
  }
}

void LocalDisplayNode::OnScreenSizeChange() {
  if (context_.exists()) {
    context_->OnScreenSizeChange();
  }
}

void LocalDisplayNode::OnLanguageChange() {
  if (context_.exists()) {
    context_->LanguageChanged();
  }
}

void LocalDisplayNode::SetConfig(const std::string& val) {
  if (val == config_) {
    return;
  }
  config_ = val;
  NotifyPyAttrsChanged_();
}

void LocalDisplayNode::SetVisible(bool val) {
  if (val == visible_) {
    return;
  }
  visible_ = val;
  NotifyPyAttrsChanged_();
}

void LocalDisplayNode::NotifyPyAttrsChanged_() {
  // Before OnCreate we have no Python side yet; it reads our attrs
  // fresh when it comes up.
  if (!created_ || !py_display_.exists()) {
    return;
  }
  try {
    Python::ScopedCallLabel label("LocalDisplay attr update");
    py_display_.GetAttr("_on_node_attrs_changed").Call();
  } catch (const std::exception& e) {
    g_core->logging->Log(LogName::kBa, LogLevel::kError,
                         "Error updating Python LocalDisplay for "
                             + GetObjectDescription() + ": " + e.what());
  }
}

void LocalDisplayNode::ExpirePy_() {
  if (!py_display_.exists()) {
    return;
  }
  try {
    // Run in an empty context; nothing should be happening in here
    // except deleting things, which requires no context.
    base::ScopedSetContext ssc(nullptr);
    Python::ScopedCallLabel label("LocalDisplay expire");
    py_display_.GetAttr("_expire").Call();
  } catch (const std::exception& e) {
    g_core->logging->Log(LogName::kBa, LogLevel::kError,
                         "Error expiring Python LocalDisplay for "
                             + GetObjectDescription() + ": " + e.what());
  }
  py_display_.Release();
}

}  // namespace ballistica::scene_v1
