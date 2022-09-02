// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_GAME_PLAYER_H_
#define BALLISTICA_GAME_PLAYER_H_

#include <string>
#include <unordered_map>
#include <vector>

#include "ballistica/core/object.h"
#include "ballistica/input/input.h"
#include "ballistica/math/vector3f.h"
#include "ballistica/scene/scene.h"

// How much time should pass before we kick idle players (in milliseconds).
#define BA_PLAYER_TIME_OUT 60000
#define BA_PLAYER_TIME_OUT_WARN 10000

namespace ballistica {

// A player (from the game's point of view).
class Player : public Object {
 public:
  Player(int id, HostSession* host_session);
  ~Player() override;

  auto SetInputDevice(InputDevice* input_device) -> void;
  auto AssignInputCall(InputType type, PyObject* call_obj) -> void;
  auto InputCommand(InputType type, float value = 0.0f) -> void;

  auto SetName(const std::string& name, const std::string& full_name, bool real)
      -> void;
  auto GetName(bool full = false, bool icon = true) const -> std::string;
  auto name_is_real() const -> bool { return name_is_real_; }
  auto ResetInput() -> void;
  auto GetHostSession() const -> HostSession*;

  auto id() const -> int { return id_; }

  auto NewPyRef() -> PyObject* { return GetPyRef(true); }
  auto BorrowPyRef() -> PyObject* { return GetPyRef(false); }

  // Set the player node for the current activity.
  auto set_node(Node* node) -> void {
    assert(InLogicThread());
    node_ = node;
  }
  auto node() const -> Node* {
    assert(InLogicThread());
    return node_.get();
  }

  auto SetPyTeam(PyObject* team) -> void;
  auto GetPyTeam() -> PyObject*;  // Returns a borrowed ref.

  auto SetPyCharacter(PyObject* team) -> void;
  auto GetPyCharacter() -> PyObject*;  // Returns a borrowed ref.

  auto SetPyColor(PyObject* team) -> void;
  auto GetPyColor() -> PyObject*;  // Returns a borrowed ref.

  auto SetPyHighlight(PyObject* team) -> void;
  auto GetPyHighlight() -> PyObject*;  // Returns a borrowed ref.

  auto SetPyActivityPlayer(PyObject* team) -> void;
  auto GetPyActivityPlayer() -> PyObject*;  // Returns a borrowed ref.

  auto set_has_py_data(bool has) -> void { has_py_data_ = has; }
  auto has_py_data() const -> bool { return has_py_data_; }

  auto GetInputDevice() const -> InputDevice* { return input_device_.get(); }
  auto GetAge() const -> millisecs_t { return GetRealTime() - creation_time_; }
  auto accepted() const -> bool { return accepted_; }

  auto SetPosition(const Vector3f& position) -> void;

  // If an public account-id can be determined with relative
  // certainty for this player, returns it. Otherwise returns
  // an empty string.
  auto GetPublicAccountID() const -> std::string;

  auto SetHostActivity(HostActivity* host_activity) -> void;
  auto GetHostActivity() const -> HostActivity*;

  auto has_py_ref() -> bool { return (py_ref_ != nullptr); }

  auto SetIcon(const std::string& tex_name, const std::string& tint_tex_name,
               const std::vector<float>& tint_color,
               const std::vector<float>& tint2_color) -> void;

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
  auto set_accepted(bool value) -> void { accepted_ = value; }
  auto time_out() const -> millisecs_t { return time_out_; }
  auto set_time_out(millisecs_t value) -> void { time_out_ = value; }
  auto set_have_position(bool value) -> void { have_position_ = value; }

 private:
  auto GetPyRef(bool new_ref) -> PyObject*;
  auto RunInput(InputType type, float value = 0.0f) -> void;
  bool icon_set_{};
  std::string icon_tex_name_;
  std::string icon_tint_tex_name_;
  std::vector<float> icon_tint_color_;
  std::vector<float> icon_tint2_color_;
  Object::WeakRef<HostSession> host_session_;
  Object::WeakRef<HostActivity> host_activity_;
  Object::WeakRef<Node> node_;
  bool in_activity_{};
  Object::WeakRef<InputDevice> input_device_;
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
  bool have_position_{false};
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
  std::unordered_map<int, Object::Ref<PythonContextCall> > calls_;
};

}  // namespace ballistica

#endif  // BALLISTICA_GAME_PLAYER_H_
