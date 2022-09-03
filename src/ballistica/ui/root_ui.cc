// Released under the MIT License. See LICENSE for details.

#include "ballistica/ui/root_ui.h"

#include "ballistica/game/connection/connection_set.h"
#include "ballistica/game/game.h"
#include "ballistica/game/session/host_session.h"
#include "ballistica/graphics/component/simple_component.h"
#include "ballistica/input/device/keyboard_input.h"
#include "ballistica/input/device/touch_input.h"
#include "ballistica/input/input.h"
#include "ballistica/python/python.h"
#include "ballistica/ui/ui.h"
#include "ballistica/ui/widget/container_widget.h"

namespace ballistica {

// Phasing these out; replaced by buttons in our rootwidget.
#define DO_OLD_MENU_PARTY_BUTTONS (!BA_TOOLBAR_TEST)

const float kMenuButtonSize = 40.0f;
const float kMenuButtonDrawDepth = -0.07f;

RootUI::RootUI() {
  float base_scale;
  switch (g_ui->scale()) {
    case UIScale::kLarge:
      base_scale = 1.0f;
      break;
    case UIScale::kMedium:
      base_scale = 1.5f;
      break;
    case UIScale::kSmall:
      base_scale = 2.0f;
      break;
    default:
      base_scale = 1.0f;
      break;
  }
  menu_button_size_ = kMenuButtonSize * base_scale;
}
RootUI::~RootUI() = default;

void RootUI::TogglePartyWindowKeyPress() {
  assert(InLogicThread());
  if (g_game->GetPartySize() > 1 || g_game->connections()->connection_to_host()
      || always_draw_party_icon()) {
    ActivatePartyIcon();
  }
}

void RootUI::ActivatePartyIcon() const {
  assert(InLogicThread());
  ScopedSetContext cp(g_game->GetUIContext());

  // Originate from center of party icon. If menu button is shown, it is to the
  // left of that.
  float icon_pos_h =
      g_graphics->screen_virtual_width() * 0.5f - menu_button_size_ * 0.5f;
  float icon_pos_v =
      g_graphics->screen_virtual_height() * 0.5f - menu_button_size_ * 0.5f;
  bool menu_active = !(g_ui && g_ui->screen_root_widget()
                       && g_ui->screen_root_widget()->HasChildren());
  if (menu_active) {
    icon_pos_h -= menu_button_size_;
  }
  g_python->obj(Python::ObjID::kPartyIconActivateCall)
      .Call(Vector2f(icon_pos_h, icon_pos_v));
}

auto RootUI::HandleMouseButtonDown(float x, float y) -> bool {
  // Whether the menu button is visible/active.
  bool menu_active = !(g_ui && g_ui->screen_root_widget()
                       && g_ui->screen_root_widget()->HasChildren());

  // Handle party button presses (need to do this before UI since it
  // floats over the top). Party button is to the left of menu button.
  if (explicit_bool(DO_OLD_MENU_PARTY_BUTTONS)) {
    bool party_button_active =
        (!party_window_open_
         && (g_game->connections()->GetConnectedClientCount() > 0
             || g_game->connections()->connection_to_host()
             || always_draw_party_icon()));
    float party_button_left =
        menu_active ? 2 * menu_button_size_ : menu_button_size_;
    float party_button_right = menu_active ? menu_button_size_ : 0;
    if (party_button_active
        && (g_graphics->screen_virtual_width() - x < party_button_left)
        && (g_graphics->screen_virtual_width() - x >= party_button_right)
        && (g_graphics->screen_virtual_height() - y < menu_button_size_)) {
      ActivatePartyIcon();
      return true;
    }
  }
  // Menu button.
  if (explicit_bool(DO_OLD_MENU_PARTY_BUTTONS)) {
    if (menu_active
        && (g_graphics->screen_virtual_width() - x < menu_button_size_)
        && (g_graphics->screen_virtual_height() - y < menu_button_size_)) {
      menu_button_pressed_ = true;
      menu_button_hover_ = true;
      return true;
    }
  }

  return false;
}

void RootUI::HandleMouseButtonUp(float x, float y) {
  if (menu_button_pressed_) {
    menu_button_pressed_ = false;
    menu_button_hover_ = false;

    // If we've got a touch input, bring the menu up in its name..
    // otherwise go with keyboard input.
    InputDevice* input_device = nullptr;
    auto* touch_input = g_input->touch_input();
    auto* keyboard_input = g_input->keyboard_input();
    if (touch_input) {
      input_device = touch_input;
    } else if (keyboard_input) {
      input_device = keyboard_input;
    }
    if ((g_graphics->screen_virtual_width() - x < menu_button_size_)
        && (g_graphics->screen_virtual_height() - y < menu_button_size_)) {
      g_game->PushMainMenuPressCall(input_device);
      last_menu_button_press_time_ = GetRealTime();
    }
  }
}

void RootUI::HandleMouseMotion(float x, float y) {
  // Menu button hover.
  if (menu_button_pressed_) {
    menu_button_hover_ =
        ((g_graphics->screen_virtual_width() - x < menu_button_size_)
         && (g_graphics->screen_virtual_height() - y < menu_button_size_));
  }
}

void RootUI::Draw(FrameDef* frame_def) {
  if (explicit_bool(DO_OLD_MENU_PARTY_BUTTONS)) {
    millisecs_t real_time = frame_def->real_time();

    // Menu button.
    // Update time-dependent stuff to this point.
    bool active = !(g_ui && g_ui->screen_root_widget()
                    && g_ui->screen_root_widget()->HasChildren());
    if (real_time - menu_update_time_ > 500) {
      menu_update_time_ = real_time - 500;
    }
    while (menu_update_time_ < real_time) {
      menu_update_time_ += 10;
      if (!active && (real_time - last_menu_button_press_time_ > 100)) {
        menu_fade_ = std::max(0.0f, menu_fade_ - 0.05f);
      } else {
        menu_fade_ = std::min(1.0f, menu_fade_ + 0.05f);
      }
    }

    // Don't draw menu button on certain UIs such as TV or VR.
    bool draw_menu_button = true;

    if (g_buildconfig.ostype_android()) {
      // Draw if we have a touchscreen or are in desktop mode.
      if (g_input->touch_input() == nullptr
          && !g_platform->IsRunningOnDesktop()) {
        draw_menu_button = false;
      }
    } else if (g_buildconfig.rift_build()) {
      if (IsVRMode()) {
        draw_menu_button = false;
      }
    }

    if (draw_menu_button) {
      SimpleComponent c(frame_def->overlay_pass());
      c.SetTransparent(true);
      c.SetTexture(g_media->GetTexture(SystemTextureID::kMenuButton));

      // Draw menu button.
      float width = g_graphics->screen_virtual_width();
      float height = g_graphics->screen_virtual_height();
      if ((menu_button_pressed_ && menu_button_hover_)
          || real_time - last_menu_button_press_time_ < 100) {
        c.SetColor(1, 2, 0.5f, 1);
      } else {
        c.SetColor(0.3f, 0.3f + 0.2f * menu_fade_, 0.2f, menu_fade_);
      }
      c.PushTransform();
      c.Translate(width - menu_button_size_ * 0.5f,
                  height - menu_button_size_ * 0.38f, kMenuButtonDrawDepth);
      c.Scale(menu_button_size_ * 0.8f, menu_button_size_ * 0.8f);
      c.DrawModel(g_media->GetModel(SystemModelID::kImage1x1));
      c.PopTransform();
      c.Submit();
    }

    // To the left of the menu button, draw our connected-players indicator
    // (this probably shouldn't live here).
    bool draw_connected_players_icon = false;
    int party_size = g_game->GetPartySize();
    bool is_host = (g_game->connections()->connection_to_host() == nullptr);
    millisecs_t last_connection_to_client_join_time =
        g_game->last_connection_to_client_join_time();

    bool show_client_joined =
        (is_host && last_connection_to_client_join_time != 0
         && real_time - last_connection_to_client_join_time < 5000);

    if (!party_window_open_
        && (party_size != 0 || g_game->connections()->connection_to_host()
            || always_draw_party_icon_)) {
      draw_connected_players_icon = true;
    }

    if (draw_connected_players_icon) {
      // Flash and show a message if we're in the main menu instructing the
      // player to start a game.
      bool flash = false;
      HostSession* s = g_game->GetForegroundContext().GetHostSession();
      if (s && s->is_main_menu() && party_size > 0 && show_client_joined)
        flash = true;

      SimpleComponent c(frame_def->overlay_pass());
      c.SetTransparent(true);
      c.SetTexture(g_media->GetTexture(SystemTextureID::kUsersButton));

      // Draw button.
      float width = g_graphics->screen_virtual_width();
      float height = g_graphics->screen_virtual_height();
      c.PushTransform();
      float extra_offset =
          (draw_menu_button && menu_fade_ > 0.0f) ? -menu_button_size_ : 0.0f;
      {
        float smoothing = 0.8f;
        connected_client_extra_offset_smoothed_ =
            smoothing * connected_client_extra_offset_smoothed_
            + (1.0f - smoothing) * extra_offset;
      }
      c.Translate(width - menu_button_size_ * 0.4f
                      + connected_client_extra_offset_smoothed_,
                  height - menu_button_size_ * 0.35f, kMenuButtonDrawDepth);
      c.Scale(menu_button_size_ * 0.8f, menu_button_size_ * 0.8f);
      if (flash && frame_def->base_time() % 250 < 125) {
        c.SetColor(1.0f, 1.4f, 1.0f);
      }
      c.DrawModel(g_media->GetModel(SystemModelID::kImage1x1));
      c.PopTransform();
      c.Submit();

      // Based on who has menu control, we may show a key/button below the party
      // icon.
      if (!active) {
        if (InputDevice* uiid = g_ui->GetUIInputDevice()) {
          std::string party_button_name = uiid->GetPartyButtonName();
          if (!party_button_name.empty()) {
            if (!party_button_text_group_.exists()) {
              party_button_text_group_ = Object::New<TextGroup>();
            }
            if (party_button_name != party_button_text_group_->getText()) {
              party_button_text_group_->SetText(party_button_name,
                                                TextMesh::HAlign::kCenter,
                                                TextMesh::VAlign::kTop);
            }
            int text_elem_count = party_button_text_group_->GetElementCount();
            for (int e = 0; e < text_elem_count; e++) {
              c.SetTexture(party_button_text_group_->GetElementTexture(e));
              c.SetMaskUV2Texture(
                  party_button_text_group_->GetElementMaskUV2Texture(e));
              c.SetShadow(
                  -0.003f * party_button_text_group_->GetElementUScale(e),
                  -0.003f * party_button_text_group_->GetElementVScale(e), 0.0f,
                  1.0f);
              c.SetFlatness(1.0f);
              c.SetColor(0.8f, 1, 0.8f, 0.9f);
              c.PushTransform();
              c.Translate(width - menu_button_size_ * 0.42f
                              + connected_client_extra_offset_smoothed_,
                          height - menu_button_size_ * 0.77f,
                          kMenuButtonDrawDepth);
              c.Scale(menu_button_size_ * 0.015f, menu_button_size_ * 0.015f);
              c.DrawMesh(party_button_text_group_->GetElementMesh(e));
              c.PopTransform();
            }
            c.Submit();
          }
        }
      }

      {
        // Update party count text if party size has changed.
        if (party_size_text_group_num_ != party_size) {
          party_size_text_group_num_ = party_size;
          if (!party_size_text_group_.exists()) {
            party_size_text_group_ = Object::New<TextGroup>();
          }
          party_size_text_group_->SetText(
              std::to_string(party_size_text_group_num_));

          // ..we also may want to update our 'someone joined' message if we're
          // host
          if (is_host) {
            if (!start_a_game_text_group_.exists()) {
              start_a_game_text_group_ = Object::New<TextGroup>();
            }
            if (party_size == 2) {  // (includes us as host)
              start_a_game_text_group_->SetText(
                  g_game->GetResourceString("joinedPartyInstructionsText"),
                  TextMesh::HAlign::kRight, TextMesh::VAlign::kTop);
            } else if (party_size > 2) {
              start_a_game_text_group_->SetText(
                  std::to_string(party_size - 1) +
                      " friends have joined your party.\nGo to 'Play' to start "
                      "a game.",
                  TextMesh::HAlign::kRight, TextMesh::VAlign::kTop);
            }
          }
        }

        // Draw party member count.
        int text_elem_count = party_size_text_group_->GetElementCount();
        for (int e = 0; e < text_elem_count; e++) {
          c.SetTexture(party_size_text_group_->GetElementTexture(e));
          c.SetMaskUV2Texture(
              party_size_text_group_->GetElementMaskUV2Texture(e));
          c.SetShadow(-0.003f * party_size_text_group_->GetElementUScale(e),
                      -0.003f * party_size_text_group_->GetElementVScale(e),
                      0.0f, 1.0f);
          c.SetFlatness(1.0f);
          if (flash && frame_def->base_time() % 250 < 125) {
            c.SetColor(1, 1, 0);
          } else {
            if (party_size > 0) {
              c.SetColor(0.2f, 1.0f, 0.2f);
            } else {
              c.SetColor(0.5f, 0.65f, 0.5f);
            }
          }
          c.PushTransform();
          c.Translate(width - menu_button_size_ * 0.49f
                          + connected_client_extra_offset_smoothed_,
                      height - menu_button_size_ * 0.6f, kMenuButtonDrawDepth);
          c.Scale(menu_button_size_ * 0.01f, menu_button_size_ * 0.01f);
          c.DrawMesh(party_size_text_group_->GetElementMesh(e));
          c.PopTransform();
        }
        c.Submit();
      }

      // Draw 'someone joined' text if applicable.
      if (is_host) {
        if (flash) {
          float blend = 0.8f;
          start_a_game_text_scale_ =
              blend * start_a_game_text_scale_ + (1.0f - blend) * 1.0f;
        } else {
          float blend = 0.8f;
          start_a_game_text_scale_ =
              blend * start_a_game_text_scale_ + (1.0f - blend) * 0.0f;
        }

        if (start_a_game_text_scale_ > 0.001f) {
          // 'start a game' notice
          int text_elem_count = start_a_game_text_group_->GetElementCount();
          for (int e = 0; e < text_elem_count; e++) {
            c.SetTexture(start_a_game_text_group_->GetElementTexture(e));
            c.SetMaskUV2Texture(
                start_a_game_text_group_->GetElementMaskUV2Texture(e));
            c.SetShadow(-0.003f * start_a_game_text_group_->GetElementUScale(e),
                        -0.003f * start_a_game_text_group_->GetElementVScale(e),
                        0.0f, 1.0f);
            c.SetFlatness(1.0f);
            if (flash && frame_def->base_time() % 250 < 125) {
              c.SetColor(1, 1, 0);
            } else {
              c.SetColor(0, 1, 0);
            }
            c.PushTransform();
            c.Translate(width - 10, height - menu_button_size_ * 0.7f, -0.07f);
            c.Scale(start_a_game_text_scale_, start_a_game_text_scale_);
            c.DrawMesh(start_a_game_text_group_->GetElementMesh(e));
            c.PopTransform();
          }
          c.Submit();
        }
      }
    }
  }
}

}  // namespace ballistica
