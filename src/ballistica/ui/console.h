// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_UI_CONSOLE_H_
#define BALLISTICA_UI_CONSOLE_H_

#include <list>
#include <string>
#include <utility>

#include "ballistica/core/object.h"
#include "ballistica/graphics/renderer.h"

namespace ballistica {

class Console {
 public:
  Console();
  ~Console();
  auto active() const -> bool { return (state_ != State::kInactive); }
  enum class State { kInactive, kMini, kFull };
  auto transition_start() const -> millisecs_t { return transition_start_; }
  auto HandleTextEditing(const std::string& text) -> bool;
  auto HandleKeyPress(const SDL_Keysym* keysym) -> bool;
  auto HandleKeyRelease(const SDL_Keysym* keysym) -> bool;
  void ToggleState();
  void Print(const std::string& s_in);
  void Draw(RenderPass* pass);

 private:
  ImageMesh bg_mesh_;
  ImageMesh stripe_mesh_;
  ImageMesh shadow_mesh_;
  TextGroup built_text_group_;
  TextGroup title_text_group_;
  TextGroup prompt_text_group_;
  TextGroup input_text_group_;
  millisecs_t last_input_text_change_time_{};
  bool input_text_dirty_{true};
  millisecs_t transition_start_{};
  State state_{State::kInactive};

  class Message {
   public:
    Message(std::string s_in, millisecs_t c)
        : creation_time(c), s(std::move(s_in)) {}
    millisecs_t creation_time;
    std::string s;
    auto getText() -> TextGroup& {
      if (!s_mesh_.exists()) {
        s_mesh_ = Object::New<TextGroup>();
        s_mesh_->SetText(s);
      }
      return *s_mesh_;
    }

   private:
    Object::Ref<TextGroup> s_mesh_;
  };
  std::string input_string_;
  std::list<std::string> input_history_;
  int input_history_position_{};
  std::list<Message> lines_;
  std::string last_line_;
  Object::Ref<TextGroup> last_line_mesh_group_;
  bool last_line_mesh_dirty_{true};
};

}  // namespace ballistica

#endif  // BALLISTICA_UI_CONSOLE_H_
