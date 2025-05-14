// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_SUPPORT_PLAYER_H_
#define BALLISTICA_SCENE_V1_SUPPORT_PLAYER_H_

#include <string>
#include <unordered_map>
#include <vector>

#include "ballistica/scene_v1/node/node.h"
#include "ballistica/scene_v1/support/host_session.h"
#include "ballistica/shared/foundation/object.h"
#include "ballistica/shared/math/vector3f.h"

// How much time should pass before we kick idle players (in milliseconds).
#define BA_PLAYER_TIME_OUT 60000
#define BA_PLAYER_TIME_OUT_WARN 10000

namespace ballistica::scene_v1 {

// A player (from the game's point of view).
class Player : public Object {
 public:
  Player(int id, HostSession* host_session);
  ~Player() override;

  void AssignInputCall(InputType type, PyObject* call_obj);
  void InputCommand(InputType type, float value = 0.0f);

  auto GetName(bool full = false, bool icon = true) const -> std::string;
  void SetName(const std::string& name, const std::string& full_name,
               bool real);
  auto name_is_real() const -> bool { return name_is_real_; }

  void ResetInput();
  auto GetHostSession() const -> HostSession*;

  auto id() const -> int { return id_; }

  auto NewPyRef() -> PyObject* { return GetPyRef(true); }
  auto BorrowPyRef() -> PyObject* { return GetPyRef(false); }

  /// The player node for the current activity.
  auto node() const -> Node* {
    assert(g_base->InLogicThread());
    return node_.get();
  }
  /// Set the player node for the current activity.
  void set_node(Node* node) {
    assert(g_base->InLogicThread());
    node_ = node;
  }

  /// Returns a NEW ref or nullptr.
  auto GetPyTeam() -> PyObject*;  // Returns a borrowed ref.
  void SetPyTeam(PyObject* team);

  auto GetPyCharacter() -> PyObject*;  // Returns a borrowed ref.
  void SetPyCharacter(PyObject* team);

  auto GetPyColor() -> PyObject*;  // Returns a borrowed ref.
  void SetPyColor(PyObject* team);

  auto GetPyHighlight() -> PyObject*;  // Returns a borrowed ref.
  void SetPyHighlight(PyObject* team);

  auto GetPyActivityPlayer() -> PyObject*;  // Returns a borrowed ref.
  void SetPyActivityPlayer(PyObject* team);

  auto has_py_data() const -> bool { return has_py_data_; }
  void set_has_py_data(bool has) { has_py_data_ = has; }

  auto input_device_delegate() const -> SceneV1InputDeviceDelegate* {
    return input_device_delegate_.get();
  }
  void set_input_device_delegate(SceneV1InputDeviceDelegate* input_device);

  auto GetAge() const -> millisecs_t;
  auto accepted() const -> bool { return accepted_; }

  void SetPosition(const Vector3f& position);

  // If an public account-id can be determined with relative
  // certainty for this player, returns it. Otherwise returns
  // an empty string.
  auto GetPublicV1AccountID() const -> std::string;

  void SetHostActivity(HostActivity* host_activity);
  auto GetHostActivity() const -> HostActivity*;

  auto HasPyRef() -> bool { return (py_ref_ != nullptr); }

  void SetIcon(const std::string& tex_name, const std::string& tint_tex_name,
               const std::vector<float>& tint_color,
               const std::vector<float>& tint2_color);

  auto icon_tex_name() const -> const std::string& {
    BA_PRECONDITION(icon_set_);
    return icon_tex_name_;
  }
  auto icon_tint_tex_name() const -> const std::string& {
    BA_PRECONDITION(icon_set_);
    return icon_tint_tex_name_;
  }
  auto icon_tint_color() const -> const std::vector<float>& {
    BA_PRECONDITION(icon_set_);
    return icon_tint_color_;
  }
  auto icon_tint2_color() const -> const std::vector<float>& {
    BA_PRECONDITION(icon_set_);
    return icon_tint2_color_;
  }
  void set_accepted(bool value) { accepted_ = value; }
  auto time_out() const -> millisecs_t { return time_out_; }
  void set_time_out(millisecs_t value) { time_out_ = value; }
  void set_have_position(bool value) { have_position_ = value; }

  void ClearHostSessionForTearDown();

 private:
  auto GetPyRef(bool new_ref) -> PyObject*;
  void RunInput(InputType type, float value = 0.0f);
  bool icon_set_{};
  std::string icon_tex_name_;
  std::string icon_tint_tex_name_;
  std::vector<float> icon_tint_color_;
  std::vector<float> icon_tint2_color_;
  Object::WeakRef<HostSession> host_session_;
  Object::WeakRef<HostActivity> host_activity_;
  Object::WeakRef<Node> node_;
  bool in_activity_{};
  Object::WeakRef<SceneV1InputDeviceDelegate> input_device_delegate_;
  PyObject* py_ref_{};
  bool accepted_{};
  bool has_py_data_{};
  millisecs_t creation_time_{};
  int id_{};
  std::string name_;
  std::string full_name_;

  // Is the current name real (as opposed to a standin
  // title such as '<choosing player>')
  bool name_is_real_{};
  bool left_held_{};
  bool right_held_{};
  bool up_held_{};
  bool down_held_{};
  bool hold_position_{};
  bool send_hold_state_{};
  bool fly_held_{};
  float lr_state_{};
  float ud_state_{};
  float run_state_{};
  millisecs_t time_out_{BA_PLAYER_TIME_OUT};

  // Player's position for use by input devices and whatnot for guides.
  // FIXME: This info should be acquired through the player node.
  bool have_position_{};
  Vector3f position_{0.0f, 0.0f, 0.0f};

  // These should be destructed before the rest of our class goes down,
  // so they should be here at the bottom..
  // (they might access our name string or other stuff declared above)
  // PythonRef py_actor_;
  PythonRef py_team_weak_ref_;
  PythonRef py_character_;
  PythonRef py_color_;
  PythonRef py_highlight_;
  PythonRef py_activityplayer_;
  std::unordered_map<int, Object::Ref<base::PythonContextCall> > calls_;
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_SUPPORT_PLAYER_H_
