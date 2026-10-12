// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_NODE_LOCAL_DISPLAY_NODE_H_
#define BALLISTICA_SCENE_V1_NODE_LOCAL_DISPLAY_NODE_H_

#include <string>

#include "ballistica/scene_v1/node/node.h"
#include "ballistica/shared/python/python_ref.h"

namespace ballistica::scene_v1 {

/// A node that results in every machine (host and each client) running
/// its own local Python-driven display described by the node's config.
///
/// The node itself carries only a json 'config' string and a 'visible'
/// flag over the wire. On creation, each machine spins up a
/// LocalDisplayContext (a private stream-less scene plus timers) and a
/// Python bascenev1.LocalDisplay object that builds whatever the config
/// describes in that context; everything it creates dies with the node.
/// This is how things like the controls guide can show each player the
/// button names of *their* controllers rather than the host's.
class LocalDisplayNode : public Node {
 public:
  static auto InitType() -> NodeType*;
  explicit LocalDisplayNode(Scene* scene);
  ~LocalDisplayNode() override;

  void OnCreate() override;
  void Step() override;
  void Draw(base::FrameDef* frame_def) override;
  void OnScreenSizeChange() override;
  void OnLanguageChange() override;

  auto config() const -> std::string { return config_; }
  void SetConfig(const std::string& val);
  auto visible() const -> bool { return visible_; }
  void SetVisible(bool val);

  auto context() const -> LocalDisplayContext* { return context_.get(); }

 private:
  void NotifyPyAttrsChanged_();
  void ExpirePy_();

  std::string config_;
  bool visible_{true};
  bool created_{};
  Object::Ref<LocalDisplayContext> context_;
  PythonRef py_display_;
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_NODE_LOCAL_DISPLAY_NODE_H_
