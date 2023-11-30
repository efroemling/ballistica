// Released under the MIT License. See LICENSE for details.

#include "ballistica/ui_v1/support/root_ui.h"

#include "ballistica/base/app_mode/app_mode.h"
#include "ballistica/base/graphics/component/simple_component.h"
#include "ballistica/base/input/device/keyboard_input.h"
#include "ballistica/base/input/device/touch_input.h"
#include "ballistica/base/input/input.h"
#include "ballistica/ui_v1/python/ui_v1_python.h"
#include "ballistica/ui_v1/widget/container_widget.h"

namespace ballistica::ui_v1 {

// Phasing these out; replaced by buttons in our rootwidget.
#define DO_OLD_MENU_PARTY_BUTTONS (!BA_UI_V1_TOOLBAR_TEST)

const float kMenuButtonSize = 40.0f;
const float kMenuButtonDrawDepth = -0.07f;

RootUI::RootUI() {
  float base_scale;
  switch (g_base->ui->scale()) {
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
  assert(g_base->InLogicThread());
  if (g_base->app_mode()->GetPartySize() > 1
      || g_base->app_mode()->HasConnectionToHost()
      || always_draw_party_icon()) {
    ActivatePartyIcon();
  }
}

void RootUI::ActivatePartyIcon() const {
  assert(g_base->InLogicThread());
  base::ScopedSetContext ssc(nullptr);

  // Originate from center of party icon. If menu button is shown, it is to the
  // left of that.
  float icon_pos_h = g_base->graphics->screen_virtual_width() * 0.5f
                     - menu_button_size_ * 0.5f;
  float icon_pos_v = g_base->graphics->screen_virtual_height() * 0.5f
                     - menu_button_size_ * 0.5f;
  bool menu_active = !(g_ui_v1 && g_ui_v1->screen_root_widget()
                       && g_ui_v1->screen_root_widget()->HasChildren());
  if (menu_active) {
    icon_pos_h -= menu_button_size_;
  }
  g_ui_v1->python->objs()
      .Get(UIV1Python::ObjID::kPartyIconActivateCall)
      .Call(Vector2f(icon_pos_h, icon_pos_v));
}

auto RootUI::HandleMouseButtonDown(float x, float y) -> bool {
  // Whether the menu button is visible/active.
  bool menu_active = !(g_ui_v1 && g_ui_v1->screen_root_widget()
                       && g_ui_v1->screen_root_widget()->HasChildren());

  // Handle party button presses (need to do this before UI since it
  // floats over the top). Party button is to the left of menu button.
  if (explicit_bool(DO_OLD_MENU_PARTY_BUTTONS)) {
    bool party_button_active = (!party_window_open_
                                && (g_base->app_mode()->HasConnectionToClients()
                                    || g_base->app_mode()->HasConnectionToHost()
                                    || always_draw_party_icon()));
    float party_button_left =
        menu_active ? 2 * menu_button_size_ : menu_button_size_;
    float party_button_right = menu_active ? menu_button_size_ : 0;
    if (party_button_active
        && (g_base->graphics->screen_virtual_width() - x < party_button_left)
        && (g_base->graphics->screen_virtual_width() - x >= party_button_right)
        && (g_base->graphics->screen_virtual_height() - y
            < menu_button_size_)) {
      ActivatePartyIcon();
      return true;
    }
  }
  // Menu button.
  if (explicit_bool(DO_OLD_MENU_PARTY_BUTTONS)) {
    if (menu_active
        && (g_base->graphics->screen_virtual_width() - x < menu_button_size_)
        && (g_base->graphics->screen_virtual_height() - y
            < menu_button_size_)) {
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
    base::InputDevice* input_device = nullptr;
    auto* touch_input = g_base->input->touch_input();
    auto* keyboard_input = g_base->input->keyboard_input();
    if (touch_input) {
      input_device = touch_input;
    } else if (keyboard_input) {
      input_device = keyboard_input;
    }

    // Handle top right corner menu button.
    if ((g_base->graphics->screen_virtual_width() - x < menu_button_size_)
        && (g_base->graphics->screen_virtual_height() - y
            < menu_button_size_)) {
      g_base->ui->PushMainMenuPressCall(input_device);
      last_menu_button_press_time_ = g_core->GetAppTimeMillisecs();
    }
  }
}

void RootUI::HandleMouseMotion(float x, float y) {
  // Menu button hover.
  if (menu_button_pressed_) {
    menu_button_hover_ =
        ((g_base->graphics->screen_virtual_width() - x < menu_button_size_)
         && (g_base->graphics->screen_virtual_height() - y
             < menu_button_size_));
  }
}

void RootUI::Draw(base::FrameDef* frame_def) {
  if (explicit_bool(DO_OLD_MENU_PARTY_BUTTONS)) {
    millisecs_t real_time = frame_def->app_time_millisecs();

    // Menu button.
    // Update time-dependent stuff to this point.
    bool active = !(g_ui_v1 && g_ui_v1->screen_root_widget()
                    && g_ui_v1->screen_root_widget()->HasChildren());
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
      if (g_base->input->touch_input() == nullptr
          && !g_core->platform->IsRunningOnDesktop()) {
        draw_menu_button = false;
      }
    } else if (g_buildconfig.rift_build()) {
      if (g_core->vr_mode()) {
        draw_menu_button = false;
      }
    }

    if (draw_menu_button) {
      base::SimpleComponent c(frame_def->overlay_pass());
      c.SetTransparent(true);
      c.SetTexture(g_base->assets->SysTexture(base::SysTextureID::kMenuButton));

      // Draw menu button.
      float width = g_base->graphics->screen_virtual_width();
      float height = g_base->graphics->screen_virtual_height();
      if ((menu_button_pressed_ && menu_button_hover_)
          || real_time - last_menu_button_press_time_ < 100) {
        c.SetColor(1, 2, 0.5f, 1);
      } else {
        c.SetColor(0.3f, 0.3f + 0.2f * menu_fade_, 0.2f, menu_fade_);
      }
      {
        auto xf = c.ScopedTransform();
        c.Translate(width - menu_button_size_ * 0.5f,
                    height - menu_button_size_ * 0.38f, kMenuButtonDrawDepth);
        c.Scale(menu_button_size_ * 0.8f, menu_button_size_ * 0.8f);
        c.DrawMeshAsset(g_base->assets->SysMesh(base::SysMeshID::kImage1x1));
      }
      c.Submit();
    }

    // To the left of the menu button, draw our connected-players indicator
    // (this probably shouldn't live here).
    bool draw_connected_players_icon = false;
    int party_size = g_base->app_mode()->GetPartySize();
    bool is_host = (!g_base->app_mode()->HasConnectionToHost());
    millisecs_t last_connection_to_client_join_time =
        g_base->app_mode()->LastClientJoinTime();

    bool show_client_joined =
        (is_host && last_connection_to_client_join_time != 0
         && real_time - last_connection_to_client_join_time < 5000);

    if (!party_window_open_
        && (party_size != 0 || g_base->app_mode()->HasConnectionToHost()
            || always_draw_party_icon_)) {
      draw_connected_players_icon = true;
    }

    if (draw_connected_players_icon) {
      // Flash and show a message if we're in the main menu instructing the
      // player to start a game.
      bool flash = false;
      bool in_main_menu = g_base->app_mode()->InClassicMainMenuSession();

      if (in_main_menu && party_size > 0 && show_client_joined) flash = true;

      base::SimpleComponent c(frame_def->overlay_pass());
      c.SetTransparent(true);
      c.SetTexture(
          g_base->assets->SysTexture(base::SysTextureID::kUsersButton));

      // Draw button.
      float width = g_base->graphics->screen_virtual_width();
      float height = g_base->graphics->screen_virtual_height();
      {
        auto xf = c.ScopedTransform();

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
        if (flash && frame_def->display_time_millisecs() % 250 < 125) {
          c.SetColor(1.0f, 1.4f, 1.0f);
        }
        c.DrawMeshAsset(g_base->assets->SysMesh(base::SysMeshID::kImage1x1));
      }
      c.Submit();

      // Based on who has menu control, we may show a key/button below the
      // party icon.
      if (!active) {
        if (base::InputDevice* uiid = g_base->ui->GetUIInputDevice()) {
          std::string party_button_name = uiid->GetPartyButtonName();
          if (!party_button_name.empty()) {
            if (!party_button_text_group_.Exists()) {
              party_button_text_group_ = Object::New<base::TextGroup>();
            }
            if (party_button_name != party_button_text_group_->text()) {
              party_button_text_group_->SetText(party_button_name,
                                                base::TextMesh::HAlign::kCenter,
                                                base::TextMesh::VAlign::kTop);
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
              {
                auto xf = c.ScopedTransform();
                c.Translate(width - menu_button_size_ * 0.42f
                                + connected_client_extra_offset_smoothed_,
                            height - menu_button_size_ * 0.77f,
                            kMenuButtonDrawDepth);
                c.Scale(menu_button_size_ * 0.015f, menu_button_size_ * 0.015f);
                c.DrawMesh(party_button_text_group_->GetElementMesh(e));
              }
            }
            c.Submit();
          }
        }
      }

      {
        // Update party count text if party size has changed.
        if (party_size_text_group_num_ != party_size) {
          party_size_text_group_num_ = party_size;
          if (!party_size_text_group_.Exists()) {
            party_size_text_group_ = Object::New<base::TextGroup>();
          }
          party_size_text_group_->SetText(
              std::to_string(party_size_text_group_num_));

          // ..we also may want to update our 'someone joined' message if
          // we're host
          if (is_host) {
            if (!start_a_game_text_group_.Exists()) {
              start_a_game_text_group_ = Object::New<base::TextGroup>();
            }
            if (party_size == 2) {  // (includes us as host)
              start_a_game_text_group_->SetText(
                  g_base->assets->GetResourceString(
                      "joinedPartyInstructionsText"),
                  base::TextMesh::HAlign::kRight, base::TextMesh::VAlign::kTop);
            } else if (party_size > 2) {
              start_a_game_text_group_->SetText(
                  std::to_string(party_size - 1) +
                      " friends have joined your party.\nGo to 'Play' to start "
                      "a game.",
                  base::TextMesh::HAlign::kRight, base::TextMesh::VAlign::kTop);
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
          if (flash && frame_def->display_time_millisecs() % 250 < 125) {
            c.SetColor(1, 1, 0);
          } else {
            if (party_size > 0) {
              c.SetColor(0.2f, 1.0f, 0.2f);
            } else {
              c.SetColor(0.5f, 0.65f, 0.5f);
            }
          }
          {
            auto xf = c.ScopedTransform();
            c.Translate(width - menu_button_size_ * 0.49f
                            + connected_client_extra_offset_smoothed_,
                        height - menu_button_size_ * 0.6f,
                        kMenuButtonDrawDepth);
            c.Scale(menu_button_size_ * 0.01f, menu_button_size_ * 0.01f);
            c.DrawMesh(party_size_text_group_->GetElementMesh(e));
          }
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
            if (flash && frame_def->display_time_millisecs() % 250 < 125) {
              c.SetColor(1, 1, 0);
            } else {
              c.SetColor(0, 1, 0);
            }
            {
              auto xf = c.ScopedTransform();
              c.Translate(width - 10, height - menu_button_size_ * 0.7f,
                          -0.07f);
              c.Scale(start_a_game_text_scale_, start_a_game_text_scale_);
              c.DrawMesh(start_a_game_text_group_->GetElementMesh(e));
            }
          }
          c.Submit();
        }
      }
    }
  }
}

}  // namespace ballistica::ui_v1
