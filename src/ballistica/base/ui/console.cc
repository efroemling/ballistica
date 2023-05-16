// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/ui/console.h"

#include "ballistica/base/app/app_mode.h"
#include "ballistica/base/audio/audio.h"
#include "ballistica/base/graphics/component/simple_component.h"
#include "ballistica/base/graphics/text/text_graphics.h"
#include "ballistica/base/input/input.h"
#include "ballistica/base/logic/logic.h"
#include "ballistica/core/core.h"
#include "ballistica/core/platform/support/min_sdl.h"
#include "ballistica/shared/foundation/event_loop.h"
#include "ballistica/shared/generic/utils.h"
#include "ballistica/shared/python/python_command.h"
#include "ballistica/shared/python/python_sys.h"

namespace ballistica::base {

// How much of the screen the console covers when it is at full size.
const float kConsoleSize = 0.9f;
const float kConsoleZDepth = 0.0f;
const int kConsoleLineLimit = 80;
const int kStringBreakUpSize = 1950;
const int kActivateKey1 = SDLK_BACKQUOTE;
const int kActivateKey2 = SDLK_F2;

Console::Console() {
  assert(g_base->InLogicThread());
  std::string title = std::string("BallisticaKit ") + kEngineVersion + " ("
                      + std::to_string(kEngineBuildNumber) + ")";
  if (g_buildconfig.debug_build()) {
    title += " (debug)";
  }
  if (g_buildconfig.test_build()) {
    title += " (test)";
  }

  title_text_group_.SetText(title);
  built_text_group_.SetText("Built: " __DATE__ " " __TIME__);
  prompt_text_group_.SetText(">");
}

Console::~Console() = default;

auto Console::HandleKeyPress(const SDL_Keysym* keysym) -> bool {
  assert(g_base->InLogicThread());

  // Handle our toggle buttons no matter whether we're active.
  switch (keysym->sym) {
    case kActivateKey1:
    case kActivateKey2: {
      if (!g_buildconfig.demo_build() && !g_buildconfig.arcade_build()) {
        // (reset input so characters don't continue walking and stuff)
        g_base->input->ResetHoldStates();
        if (auto console = g_base->console()) {
          console->ToggleState();
        }
      }
      return true;
    }
    default:
      break;
  }

  if (state_ == State::kInactive) {
    return false;
  }

  // The rest of these presses we only handle while active.
  switch (keysym->sym) {
    case SDLK_ESCAPE:
      ToggleState();
      break;
    case SDLK_BACKSPACE:
    case SDLK_DELETE: {
      std::vector<uint32_t> unichars =
          Utils::UnicodeFromUTF8(input_string_, "fjco38");
      if (!unichars.empty()) {
        unichars.resize(unichars.size() - 1);
        input_string_ = Utils::UTF8FromUnicode(unichars);
        input_text_dirty_ = true;
      }
      break;
    }
    case SDLK_UP:
    case SDLK_DOWN: {
      if (input_history_.empty()) {
        break;
      }
      if (keysym->sym == SDLK_UP) {
        input_history_position_++;
      } else {
        input_history_position_--;
      }
      int input_history_position_used =
          (input_history_position_ - 1)
          % static_cast<int>(input_history_.size());
      int j = 0;
      for (auto& i : input_history_) {
        if (j == input_history_position_used) {
          input_string_ = i;
          input_text_dirty_ = true;
          break;
        }
        j++;
      }
      break;
    }
    case SDLK_KP_ENTER:
    case SDLK_RETURN: {
      input_history_position_ = 0;
      if (input_string_ == "clear") {
        last_line_.clear();
        lines_.clear();
      } else {
        PushCommand(input_string_);
      }
      input_history_.push_front(input_string_);
      if (input_history_.size() > 100) input_history_.pop_back();
      input_string_.resize(0);
      input_text_dirty_ = true;
      break;
    }
    default: {
#if BA_SDL2_BUILD || BA_MINSDL_BUILD
      // (in SDL2/Non-SDL we dont' get chars from keypress events;
      // they come through as text edit events)
#else   // BA_SDL2_BUILD
      if (keysym->unicode < 0x80 && keysym->unicode > 0) {
        std::vector<uint32_t> unichars =
            Utils::UnicodeFromUTF8(input_string_, "cjofrh0");
        unichars.push_back(keysym->unicode);
        input_string_ = Utils::GetValidUTF8(
            Utils::UTF8FromUnicode(unichars).c_str(), "sdkr");
        input_text_dirty_ = true;
      }
#endif  // BA_SDL2_BUILD
      break;
    }
  }
  return true;
}

void Console::PushCommand(const std::string& command) {
  assert(g_base);
  g_base->logic->event_loop()->PushCall([command] {
    // These are always run in whichever context is 'visible'.
    ScopedSetContext ssc(g_base->app_mode->GetForegroundContext());
    PythonCommand cmd(command, "<console>");
    if (!g_core->user_ran_commands) {
      g_core->user_ran_commands = true;
    }
    if (cmd.CanEval()) {
      auto obj = cmd.Eval(true, nullptr, nullptr);
      if (obj.Exists() && obj.Get() != Py_None) {
        g_base->console()->Print(obj.Repr() + "\n");
      }
    } else {
      // Not eval-able; just exec it.
      cmd.Exec(true, nullptr, nullptr);
    }
  });
}

void Console::ToggleState() {
  assert(g_base->InLogicThread());
  switch (state_) {
    case State::kInactive:
      state_ = State::kMini;
      break;
    case State::kMini:
      state_ = State::kFull;
      break;
    case State::kFull:
      state_ = State::kInactive;
      break;
  }
  g_base->audio->PlaySound(g_base->assets->SysSound(SysSoundID::kBlip));
  transition_start_ = g_core->GetAppTimeMillisecs();
}

auto Console::HandleTextEditing(const std::string& text) -> bool {
  assert(g_base->InLogicThread());
  if (state_ == State::kInactive) {
    return false;
  }

  // Ignore back-tick because we use that key to toggle the console.
  if (text == "`") {
    return false;
  }
  input_string_ += text;
  input_text_dirty_ = true;
  return true;
}

auto Console::HandleKeyRelease(const SDL_Keysym* keysym) -> bool {
  // Always absorb our activate keys.
  if (keysym->sym == kActivateKey1 || keysym->sym == kActivateKey2) {
    return true;
  }

  // Otherwise simply absorb all key-ups if we're active.
  return state_ != State::kInactive;
}

#pragma clang diagnostic push
#pragma ide diagnostic ignored "LocalValueEscapesScope"

void Console::Print(const std::string& s_in) {
  assert(g_base->InLogicThread());
  std::string s = Utils::GetValidUTF8(s_in.c_str(), "cspr");
  last_line_ += s;
  std::vector<std::string> broken_up;
  g_base->text_graphics->BreakUpString(last_line_.c_str(), kStringBreakUpSize,
                                       &broken_up);

  // Spit out all completed lines and keep the last one as lastline.
  for (size_t i = 0; i < broken_up.size() - 1; i++) {
    lines_.emplace_back(broken_up[i], g_core->GetAppTimeMillisecs());
    if (lines_.size() > kConsoleLineLimit) {
      lines_.pop_front();
    }
  }
  last_line_ = broken_up[broken_up.size() - 1];
  last_line_mesh_dirty_ = true;
}

#pragma clang diagnostic pop

void Console::Draw(RenderPass* pass) {
  millisecs_t transition_ticks = 100;
  if ((transition_start_ != 0)
      && (state_ != State::kInactive
          || ((g_core->GetAppTimeMillisecs() - transition_start_)
              < transition_ticks))) {
    float ratio =
        (static_cast<float>(g_core->GetAppTimeMillisecs() - transition_start_)
         / static_cast<float>(transition_ticks));
    float bottom;
    float mini_size = 90;
    if (state_ == State::kMini) {
      bottom = pass->virtual_height() - mini_size;
    } else {
      bottom = pass->virtual_height() - pass->virtual_height() * kConsoleSize;
    }
    if (g_core->GetAppTimeMillisecs() - transition_start_ < transition_ticks) {
      if (state_ == State::kMini) {
        bottom = pass->virtual_height() * (1.0f - ratio) + bottom * (ratio);
      } else if (state_ == State::kFull) {
        bottom =
            (pass->virtual_height() - pass->virtual_height() * kConsoleSize)
                * (ratio)
            + (pass->virtual_height() - mini_size) * (1.0f - ratio);
      } else {
        bottom = pass->virtual_height() * ratio + bottom * (1.0f - ratio);
      }
    }
    {
      bg_mesh_.SetPositionAndSize(0, bottom, kConsoleZDepth,
                                  pass->virtual_width(),
                                  (pass->virtual_height() - bottom));
      stripe_mesh_.SetPositionAndSize(0, bottom + 15, kConsoleZDepth,
                                      pass->virtual_width(), 15);
      shadow_mesh_.SetPositionAndSize(0, bottom - 7, kConsoleZDepth,
                                      pass->virtual_width(), 7);
      SimpleComponent c(pass);
      c.SetTransparent(true);
      c.SetColor(0, 0, 0.1f, 0.9f);
      c.DrawMesh(&bg_mesh_);
      c.Submit();
      c.SetColor(1.0f, 1.0f, 1.0f, 0.1f);
      c.DrawMesh(&stripe_mesh_);
      c.Submit();
      c.SetColor(0, 0, 0, 0.1f);
      c.DrawMesh(&shadow_mesh_);
      c.Submit();
    }
    if (input_text_dirty_) {
      input_text_group_.SetText(input_string_);
      input_text_dirty_ = false;
      last_input_text_change_time_ = pass->frame_def()->real_time();
    }
    {
      SimpleComponent c(pass);
      c.SetTransparent(true);
      c.SetColor(0.5f, 0.5f, 0.7f, 1.0f);
      int elem_count = built_text_group_.GetElementCount();
      for (int e = 0; e < elem_count; e++) {
        c.SetTexture(built_text_group_.GetElementTexture(e));
        c.PushTransform();
        c.Translate(pass->virtual_width() - 175.0f, bottom + 0, kConsoleZDepth);
        c.Scale(0.5f, 0.5f, 0.5f);
        c.DrawMesh(built_text_group_.GetElementMesh(e));
        c.PopTransform();
      }
      elem_count = title_text_group_.GetElementCount();
      for (int e = 0; e < elem_count; e++) {
        c.SetTexture(title_text_group_.GetElementTexture(e));
        c.PushTransform();
        c.Translate(20.0f, bottom + 0, kConsoleZDepth);
        c.Scale(0.5f, 0.5f, 0.5f);
        c.DrawMesh(title_text_group_.GetElementMesh(e));
        c.PopTransform();
      }
      elem_count = prompt_text_group_.GetElementCount();
      for (int e = 0; e < elem_count; e++) {
        c.SetTexture(prompt_text_group_.GetElementTexture(e));
        c.SetColor(1, 1, 1, 1);
        c.PushTransform();
        c.Translate(5.0f, bottom + 15.0f, kConsoleZDepth);
        c.Scale(0.5f, 0.5f, 0.5f);
        c.DrawMesh(prompt_text_group_.GetElementMesh(e));
        c.PopTransform();
      }
      elem_count = input_text_group_.GetElementCount();
      for (int e = 0; e < elem_count; e++) {
        c.SetTexture(input_text_group_.GetElementTexture(e));
        c.PushTransform();
        c.Translate(15.0f, bottom + 15.0f, kConsoleZDepth);
        c.Scale(0.5f, 0.5f, 0.5f);
        c.DrawMesh(input_text_group_.GetElementMesh(e));
        c.PopTransform();
      }
      c.Submit();
    }

    // Carat.
    millisecs_t real_time = pass->frame_def()->real_time();
    if (real_time % 200 < 100
        || (real_time - last_input_text_change_time_ < 100)) {
      SimpleComponent c(pass);
      c.SetTransparent(true);
      c.SetColor(1, 1, 1, 0.7f);
      c.PushTransform();
      c.Translate(
          19.0f + g_base->text_graphics->GetStringWidth(input_string_) * 0.5f,
          bottom + 23.0f, kConsoleZDepth);
      c.Scale(5, 11, 1.0f);
      c.DrawMeshAsset(g_base->assets->SysMesh(SysMeshID::kImage1x1));
      c.PopTransform();
      c.Submit();
    }

    // Draw console messages.
    {
      float draw_scale = 0.5f;
      SimpleComponent c(pass);
      c.SetTransparent(true);
      c.SetColor(1, 1, 1, 1);
      float h = 0.5f
                * (g_base->graphics->screen_virtual_width()
                   - (kStringBreakUpSize * draw_scale));
      float v = bottom + 32.0f;
      if (!last_line_.empty()) {
        if (last_line_mesh_dirty_) {
          if (!last_line_mesh_group_.Exists()) {
            last_line_mesh_group_ = Object::New<TextGroup>();
          }
          last_line_mesh_group_->SetText(last_line_);
          last_line_mesh_dirty_ = false;
        }
        int elem_count = last_line_mesh_group_->GetElementCount();
        for (int e = 0; e < elem_count; e++) {
          c.SetTexture(last_line_mesh_group_->GetElementTexture(e));
          c.PushTransform();
          c.Translate(h, v + 2, kConsoleZDepth);
          c.Scale(draw_scale, draw_scale);
          c.DrawMesh(last_line_mesh_group_->GetElementMesh(e));
          c.PopTransform();
        }
        v += 14;
      }
      for (auto i = lines_.rbegin(); i != lines_.rend(); i++) {
        int elem_count = i->GetText().GetElementCount();
        for (int e = 0; e < elem_count; e++) {
          c.SetTexture(i->GetText().GetElementTexture(e));
          c.PushTransform();
          c.Translate(h, v + 2, kConsoleZDepth);
          c.Scale(draw_scale, draw_scale);
          c.DrawMesh(i->GetText().GetElementMesh(e));
          c.PopTransform();
        }
        v += 14;
        if (v > pass->virtual_height() + 14) {
          break;
        }
      }
      c.Submit();
    }
  }
}

}  // namespace ballistica::base
