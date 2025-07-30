// Released under the MIT License. See LICENSE for details.

#include "ballistica/ui_v1/widget/root_widget.h"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdio>
#include <string>
#include <vector>

#include "ballistica/base/app_mode/app_mode.h"
#include "ballistica/base/assets/assets.h"
#include "ballistica/base/audio/audio.h"
#include "ballistica/base/audio/audio_source.h"
#include "ballistica/base/base.h"
#include "ballistica/base/graphics/renderer/render_pass.h"
#include "ballistica/base/graphics/support/frame_def.h"
#include "ballistica/base/support/app_timer.h"
#include "ballistica/base/support/classic_soft.h"
#include "ballistica/base/support/context.h"
#include "ballistica/base/support/plus_soft.h"
#include "ballistica/base/ui/ui.h"
#include "ballistica/shared/buildconfig/buildconfig_common.h"
#include "ballistica/shared/generic/utils.h"
#include "ballistica/ui_v1/python/ui_v1_python.h"
#include "ballistica/ui_v1/widget/button_widget.h"
#include "ballistica/ui_v1/widget/image_widget.h"
#include "ballistica/ui_v1/widget/stack_widget.h"
#include "ballistica/ui_v1/widget/text_widget.h"

namespace ballistica::ui_v1 {

static const float kBotLeftColorR{0.6f};
static const float kBotLeftColorG{0.6f};
static const float kBotLeftColorB{0.8f};

static const float kMeterColorR{0.4f};
static const float kMeterColorG{0.38f};
static const float kMeterColorB{0.5f};

static const float kChestTextColorR{0.62f};
static const float kChestTextColorG{0.74f};
static const float kChestTextColorB{0.62f};

static const float kChestCanPayTextColorR{0.0f};
static const float kChestCanPayTextColorG{1.0f};
static const float kChestCanPayTextColorB{0.7f};

static const float kChestReadyTextColorR{0.0f};
static const float kChestReadyTextColorG{1.0f};
static const float kChestReadyTextColorB{0.0f};

constexpr std::array<const char*, 4> chest_ids{"0", "1", "2", "3"};

int RootWidget::update_pause_count_;

// Flip this to true when we're ready to use levels.
static const bool kShowLevels{false};

struct RootWidget::ChestSlot_ {
  std::string appearance;
  Button_* button{};
  Image_* lock_icon{};
  Image_* tv_icon{};
  Text_* text{};
  double create_time{-1.0};
  double unlock_time{-1.0};
  double vis_unlock_time{-1.0};
  double ad_allow_time{-1.0};
  double unlock_time_animation_start_time{};
  double unlock_time_animation_end_time{};
  double unlock_time_animation_start_val{};
  double unlock_time_animation_end_val{};
  int unlock_tokens{};
  bool live_display_dirty{};
  bool unlock_time_animating{};
  bool show_token_unlockable{};
  bool needs_faster_refresh{};
};

// For defining toolbar buttons.
struct RootWidget::ButtonDef_ {
  std::string label;
  std::string img;
  std::string mesh_transparent;
  std::string mesh_opaque;
  VAlign_ v_align{VAlign_::kTop};
  UIV1Python::ObjID call{UIV1Python::ObjID::kEmptyCall};
  uint32_t visibility_mask{};
  bool selectable{true};
  bool enable_sound{true};
  bool allow_in_main_menu{true};
  bool allow_in_game{true};
  float h_align{};
  float x{};
  float y{};
  float y_offs_small{};
  float width{100.0f};
  float height{30.0f};
  float scale{1.0f};
  float depth_min{};
  float depth_max{1.0f};
  float color_r{1.0f};
  float color_g{1.0f};
  float color_b{1.0f};
  float opacity{1.0f};
  float disable_offset_scale{1.0f};
  float target_extra_left{0.0f};
  float target_extra_right{0.0f};
  float pre_buffer{0.0f};
  float post_buffer{0.0f};
};

struct RootWidget::Button_ {
  Object::Ref<ButtonWidget> widget;
  float h_align{};
  VAlign_ v_align{VAlign_::kTop};
  float x{};             // user provided x
  float y{};             // user provided y
  float y_offs_small{};  // user provided y offset for small uiscale
  float x_target{};      // final target x (accounting for visibility, etc)
  float y_target{};      // final target y (accounting for visibility, etc)
  float x_smoothed{};    // current x (on way to target)
  float y_smoothed{};    // current y (on way to target)
  float width{100.0f};
  float height{30.0f};
  float scale{1.0f};
  float disable_offset_scale{1.0f};
  float pre_buffer{0.0f};
  float post_buffer{0.0f};
  bool selectable{true};
  bool fully_offscreen{};
  bool enabled{};
  bool force_hide{};
  bool allow_in_main_menu{true};
  bool allow_in_game{true};
  uint32_t visibility_mask{};
};

// For adding text label decorations to buttons.
struct RootWidget::TextDef_ {
  Button_* button{};
  float x{};
  float y{};
  float width{-1.0f};
  float scale{1.0f};
  float depth_min{};
  float depth_max{1.0f};
  float color_r{1.0f};
  float color_g{1.0f};
  float color_b{1.0f};
  float color_a{1.0f};
  float flatness{0.5f};
  float shadow{0.5f};
  std::string text;
  TextWidget::HAlign h_align{TextWidget::HAlign::kCenter};
  TextWidget::VAlign v_align{TextWidget::VAlign::kCenter};
};

struct RootWidget::Text_ {
  Button_* button{};
  Object::Ref<TextWidget> widget;
  float x{};
  float y{};
  bool visible{true};
};

struct RootWidget::ImageDef_ {
  Button_* button{};
  float x{};
  float y{};
  float width{32.0f};
  float height{32.0f};
  float depth_min{};
  float depth_max{1.0f};
  float color_r{1.0f};
  float color_g{1.0f};
  float color_b{1.0f};
  std::string img;
};

struct RootWidget::Image_ {
  Button_* button{};
  Object::Ref<ImageWidget> widget;
  float x{};
  float y{};
  bool visible{true};
};

RootWidget::RootWidget() {
  // We enable a special 'single-depth-root' mode in which we use most of
  // our depth range for our first child (our screen stack) and the small
  // remaining bit for the rest.
  set_single_depth(true);
  set_single_depth_root(true);
  set_background(false);

  // Currently have 4 hard coded chest slot ids; this may change in the
  // future.
  for (auto&& id : chest_ids) {
    chest_slots_[id] = {};
  }
}

RootWidget::~RootWidget() {
  // Stop any currently playing sounds.
  if (league_rank_anim_sound_play_id_.has_value()) {
    g_base->audio->PushSourceStopSoundCall(*league_rank_anim_sound_play_id_);
    league_rank_anim_sound_play_id_.reset();
  }
  if (chest_unlock_time_anim_sound_play_id_.has_value()) {
    g_base->audio->PushSourceStopSoundCall(
        *chest_unlock_time_anim_sound_play_id_);
    chest_unlock_time_anim_sound_play_id_.reset();
  }
  if (tickets_anim_sound_play_id_.has_value()) {
    g_base->audio->PushSourceStopSoundCall(*tickets_anim_sound_play_id_);
    tickets_anim_sound_play_id_.reset();
  }
  if (tokens_anim_sound_play_id_.has_value()) {
    g_base->audio->PushSourceStopSoundCall(*tokens_anim_sound_play_id_);
    tokens_anim_sound_play_id_.reset();
  }
}

void RootWidget::ShowTrophyMeterAnnotation_(const std::string& val,
                                            const Vector3f& color) {
  assert(trophy_meter_annotation_text_);
  auto* widget{trophy_meter_annotation_text_->widget.get()};
  assert(widget);
  widget->set_color(color.x, color.y, color.z, 1.0);
  widget->SetText(val);

  Object::WeakRef<RootWidget> weakref(this);

  trophy_meter_annotation_timer_ = base::AppTimer::New(
      2.0f, false, [this] { HideTrophyMeterAnnotation_(); });
}

void RootWidget::HideTrophyMeterAnnotation_() {
  assert(trophy_meter_annotation_text_);
  trophy_meter_annotation_text_->widget->SetText("");
}

void RootWidget::AddMeter_(MeterType_ type, float h_align, float r, float g,
                           float b, bool plus, const std::string& s) {
  float y_offs_small{7.0f};

  float width = (type == MeterType_::kTrophy) ? 80.0f : 110.0f;
  width = 110.0f;

  // Bar.
  {
    ButtonDef_ bd;
    bd.h_align = h_align;
    bd.v_align = VAlign_::kTop;
    bd.width = width;
    bd.height = 36.0f;
    bd.y = -36.0f + 10.0f - y_offs_small;
    bd.y_offs_small = y_offs_small;
    bd.img = "uiAtlas2";
    bd.mesh_transparent = "currencyMeter";
    bd.selectable = true;

    bd.color_r = kMeterColorR;
    bd.color_g = kMeterColorG;
    bd.color_b = kMeterColorB;

    bd.depth_min = 0.3f;

    if (type == MeterType_::kLevel && !kShowLevels) {
      // Keep levels hidden always.
    } else {
      bd.visibility_mask =
          (static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFull)
           | static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFullNoBack)
           | static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFullRoot));

      bd.allow_in_game = false;

      // Show some in store mode.
      if (type == MeterType_::kLevel || type == MeterType_::kTickets) {
        bd.visibility_mask |=
            static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuStore)
            | static_cast<uint32_t>(
                Widget::ToolbarVisibility::kMenuStoreNoBack);
      }
      // Show some in get-tokens/tokens mode
      if (type == MeterType_::kTokens) {
        bd.visibility_mask |=
            static_cast<uint32_t>(Widget::ToolbarVisibility::kGetTokens)
            | static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuTokens);
      }
    }

    // Adjust buffer between neighbors.
    switch (type) {
      case MeterType_::kLevel:
        bd.pre_buffer = 50.0f;
        break;
      case MeterType_::kTrophy:
        bd.pre_buffer = 50.0f;
        break;
      case MeterType_::kTickets:
        bd.pre_buffer = 50.0f;
        break;
      case MeterType_::kTokens:
        bd.pre_buffer = 50.0f;
        break;
      default:
        break;
    }

    // Extend button target areas to cover where icon will go.
    switch (type) {
      case MeterType_::kLevel:
        bd.target_extra_left = 40.0f;
        break;
      case MeterType_::kTrophy:
        bd.target_extra_left = 40.0f;
        break;
      case MeterType_::kTickets:
        bd.target_extra_right = 40.0f;
        break;
      case MeterType_::kTokens:
        bd.target_extra_right = 40.0f;
        break;
      default:
        break;
    }

    switch (type) {
      case MeterType_::kLevel:
        bd.call = UIV1Python::ObjID::kRootUILevelIconPressCall;
        break;
      case MeterType_::kTrophy:
        bd.call = UIV1Python::ObjID::kRootUITrophyMeterPressCall;
        break;
      case MeterType_::kTokens:
        bd.call = UIV1Python::ObjID::kRootUITokensMeterPressCall;
        break;
      case MeterType_::kTickets:
        bd.call = UIV1Python::ObjID::kRootUITicketIconPressCall;
        break;
      default:
        break;
    }

    Button_* btn = AddButton_(bd);

    // Store the bar button in some cases.
    switch (type) {
      case MeterType_::kLevel:
        level_meter_button_ = btn;
        top_left_buttons_.push_back(btn);
        break;
      case MeterType_::kTrophy:
        trophy_meter_button_ = btn;
        top_left_buttons_.push_back(btn);
        break;
      case MeterType_::kTickets:
        tickets_meter_button_ = btn;
        top_right_buttons_.push_back(btn);
        break;
      case MeterType_::kTokens:
        tokens_meter_button_ = btn;
        top_right_buttons_.push_back(btn);
        break;
      default:
        break;
    }

    // Bar value text.
    {
      TextDef_ td;
      td.button = btn;
      td.width = bd.width * 0.7f;
      td.text = s;
      td.scale = 0.8f;
      td.flatness = 1.0f;
      td.shadow = 1.0f;
      td.depth_min = 0.3f;
      auto* text = AddText_(td);
      switch (type) {
        case MeterType_::kTickets:
          tickets_meter_text_ = text;
          break;
        case MeterType_::kTokens:
          tokens_meter_text_ = text;
          break;
        case MeterType_::kTrophy:
          league_rank_text_ = text;
          break;
        case MeterType_::kLevel:
          xp_text_ = text;
          break;
        default:
          break;
      }
    }
    // Below-bar annotation.
    if (type == MeterType_::kTrophy) {
      TextDef_ td;
      td.button = btn;
      td.text = "";
      td.scale = 0.8f;
      td.flatness = 1.0f;
      td.shadow = 1.0f;
      td.depth_min = 0.3f;
      td.y = -35.0f;
      td.color_r = 0.0f;
      td.color_g = 1.0f;
      td.color_b = 0.0f;
      auto* text = AddText_(td);
      trophy_meter_annotation_text_ = text;
    }

    // Icon on side.
    {
      ImageDef_ imgd;
      imgd.button = btn;
      if (type == MeterType_::kLevel || type == MeterType_::kTrophy) {
        imgd.x = -0.5 * width - 10.0f;
      } else {
        imgd.x = 0.5 * width + 10.0f;
      }

      imgd.y = 0.0f;
      imgd.width = 54.0f;
      imgd.height = 54.0f;
      switch (type) {
        case MeterType_::kLevel:
          imgd.img = "levelIcon";
          break;
        case MeterType_::kTrophy:
          imgd.img = "trophy";
          break;
        case MeterType_::kTokens:
          imgd.img = "coin";
          break;
        case MeterType_::kTickets:
          imgd.img = "tickets";
          break;
        default:
          break;
      }
      imgd.depth_min = 0.3f;
      auto* img = AddImage_(imgd);
      switch (type) {
        case MeterType_::kTrophy:
          trophy_icon_ = img;
          break;
        case MeterType_::kTickets:
          tickets_meter_icon_ = img;
          break;
        case MeterType_::kTokens:
          tokens_meter_icon_ = img;
          break;
        default:
          break;
      }

      // Level num.
      if (type == MeterType_::kLevel) {
        TextDef_ td;
        td.button = btn;
        td.width = imgd.width * 0.8f;
        td.text = "12";
        td.x = imgd.x - 2.1f;
        td.y = imgd.y + 1.0f;
        td.scale = 0.9f;
        td.flatness = 1.0f;
        td.shadow = 1.0f;
        td.depth_min = 0.3f;
        td.color_r = 1.0f;
        td.color_g = 1.0f;
        td.color_b = 1.0f;
        level_text_ = AddText_(td);
      }
    }
  }

  // Plus button.
  if (plus) {
    ButtonDef_ bd;
    bd.h_align = h_align;
    bd.v_align = VAlign_::kTop;
    bd.width = bd.height = 45.0f;
    bd.y = -36.0f + 11.0f - y_offs_small;
    bd.y_offs_small = y_offs_small;
    bd.img = "uiAtlas2";
    bd.mesh_transparent = "currencyPlusButton";
    bd.color_r = 0.35f;
    bd.color_g = 0.35f;
    bd.color_b = 0.55f;
    bd.depth_min = 0.3f;
    switch (type) {
      case MeterType_::kTokens:
        bd.call = UIV1Python::ObjID::kRootUIGetTokensButtonPressCall;
        break;
      default:
        break;
    }
    bd.visibility_mask =
        (static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFull)
         | static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFullNoBack)
         | static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFullRoot));

    // Show some in store mode.
    if (type == MeterType_::kLevel || type == MeterType_::kTickets) {
      bd.visibility_mask |=
          static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuStore)
          | static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuStoreNoBack);
    }
    // Show some in tokens mode.
    if (type == MeterType_::kTokens) {
      bd.visibility_mask |=
          static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuTokens);
    }

    bd.pre_buffer = -10.0f;
    bd.allow_in_game = false;

    Button_* btn = AddButton_(bd);
    if (type == MeterType_::kTokens) {
      get_tokens_button_ = btn;
    }
    top_right_buttons_.push_back(btn);
  }
}

void RootWidget::Setup() {
  // Back button.
  {
    ButtonDef_ bd;
    bd.h_align = 0.0f;
    bd.v_align = VAlign_::kTop;
    bd.width = bd.height = 140.0f;
    bd.color_r = 0.7f;
    bd.color_g = 0.4f;
    bd.color_b = 0.35f;
    bd.y = -40.0f;
    bd.img = "nub";
    bd.call = UIV1Python::ObjID::kRootUIBackButtonPressCall;
    bd.visibility_mask =
        (static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuMinimal)
         | static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFull)
         | static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuStore)
         | static_cast<uint32_t>(Widget::ToolbarVisibility::kGetTokens)
         | static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuTokens));
    bd.pre_buffer = -30.0f;
    Button_* b = back_button_ = AddButton_(bd);
    top_left_buttons_.push_back(b);

    {
      TextDef_ td;
      td.button = b;
      td.x = 5.0f;
      td.y = 3.0f;
      td.width = bd.width * 0.9f;
      td.text = g_base->assets->CharStr(SpecialChar::kBack);
      td.color_a = 1.0f;
      td.scale = 2.0f;
      td.flatness = 0.0f;
      td.shadow = 0.5f;
      AddText_(td);
    }
  }

  // Top bar backing (currency only).
  if (explicit_bool(false)) {
    ButtonDef_ bd;
    bd.h_align = 0.5f;
    bd.v_align = VAlign_::kTop;
    bd.width = 370.0f;
    bd.height = 90.0f;
    bd.x = 256.0f;
    bd.y = -20.0f;
    bd.img = "uiAtlas2";
    bd.mesh_transparent = "toolbarBackingTop2";
    bd.selectable = false;
    bd.color_r = 0.44f;
    bd.color_g = 0.41f;
    bd.color_b = 0.56f;
    bd.opacity = 1.0f;
    bd.depth_min = 0.2f;
    bd.call = UIV1Python::ObjID::kEmptyCall;
    bd.visibility_mask |=
        static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuStore);
    AddButton_(bd);
  }

  // Top bar backing.
  if (explicit_bool(false)) {
    ButtonDef_ bd;
    bd.h_align = 0.5f;
    bd.v_align = VAlign_::kTop;
    bd.width = 850.0f;
    bd.height = 90.0f;
    bd.x = 0.0f;
    bd.y = -20.0f;
    bd.img = "uiAtlas2";
    bd.mesh_transparent = "toolbarBackingTop2";
    bd.selectable = false;
    bd.color_r = 0.44f;
    bd.color_g = 0.41f;
    bd.color_b = 0.56f;
    bd.opacity = 1.0f;
    bd.depth_min = 0.2f;
    // bd.call = "";
    bd.call = UIV1Python::ObjID::kEmptyCall;
    bd.visibility_mask =
        static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFullRoot);
    bd.visibility_mask |=
        static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFull);
    AddButton_(bd);
  }

  // Account Button
  {
    ButtonDef_ bd;
    bd.h_align = 0.0f;
    bd.v_align = VAlign_::kTop;
    bd.width = 160.0f;
    bd.height = 60.0f;
    bd.depth_min = 0.3f;
    bd.y = -34.0f;
    bd.y_offs_small = 10.0f;
    bd.color_r = 0.56f;
    bd.color_g = 0.5f;
    bd.color_b = 0.73f;
    bd.call = UIV1Python::ObjID::kRootUIAccountButtonPressCall;
    bd.pre_buffer = 10.0f;
    bd.visibility_mask =
        (static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFull)
         | static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFullNoBack)
         | static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFullRoot));

    bd.allow_in_game = false;

    Button_* b = account_button_ = AddButton_(bd);
    top_left_buttons_.push_back(b);

    // Player name.
    {
      TextDef_ td;
      td.button = b;
      td.y = 0.0f;
      td.width = bd.width * 0.8f;
      td.text = "AccountName";
      td.scale = 1.2f;
      td.depth_min = 0.3f;
      td.color_r = 0.5f;
      td.color_g = 0.8f;
      td.color_b = 0.8f;
      td.shadow = 1.0f;
      account_name_text_ = AddText_(td);
    }
  }
  AddMeter_(MeterType_::kLevel, 0.0f, 1.0f, 1.0f, 1.0f, false, "");
  AddMeter_(MeterType_::kTrophy, 0.0f, 1.0f, 1.0f, 1.0f, false, "");

  {
    ButtonDef_ b;
    b.h_align = 1.0f;
    b.v_align = VAlign_::kTop;
    b.width = b.height = 65.0f;
    b.y = b.height * -0.48f;
    b.img = "menuButton";
    b.call = UIV1Python::ObjID::kRootUIMenuButtonPressCall;
    b.color_r = 0.3f;
    b.color_g = 0.5f;
    b.color_b = 0.2f;
    b.visibility_mask =
        (static_cast<uint32_t>(Widget::ToolbarVisibility::kInGame)
         | static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuInGame)
         | static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuMinimal)
         | static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuMinimalNoBack)
         | static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuStore)
         | static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuStoreNoBack)
         | static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFull)
         | static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFullNoBack)
         | static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFullRoot));
    b.pre_buffer = 5.0f;
    b.enable_sound = false;
    b.allow_in_main_menu = false;
    menu_button_ = AddButton_(b);
    top_right_buttons_.push_back(menu_button_);
  }

  // Squad button.
  {
    ButtonDef_ b;
    b.h_align = 1.0f;
    b.v_align = VAlign_::kTop;
    b.width = b.height = 70.0f;
    b.y = b.height * -0.41f;
    b.img = "usersButton";
    b.call = UIV1Python::ObjID::kRootUISquadButtonPressCall;
    b.visibility_mask =
        (static_cast<uint32_t>(Widget::ToolbarVisibility::kInGame)
         | static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuInGame)
         | static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuMinimal)
         | static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuMinimalNoBack)
         | static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuStore)
         | static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuStoreNoBack)
         | static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFull)
         | static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFullNoBack)
         | static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFullRoot)
         | static_cast<uint32_t>(Widget::ToolbarVisibility::kGetTokens)
         | static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuTokens)
         | static_cast<uint32_t>(Widget::ToolbarVisibility::kNoMenuMinimal));
    b.pre_buffer = 5.0f;
    b.enable_sound = false;
    squad_button_ = AddButton_(b);
    top_right_buttons_.push_back(squad_button_);

    {
      TextDef_ td;
      td.button = squad_button_;
      td.width = 70.0f;
      td.text = "0";
      td.x = -2.0f;
      td.y = -10.0f;
      td.scale = 1.0f;
      td.flatness = 1.0f;
      td.shadow = 1.0f;
      td.depth_min = 0.3f;
      td.color_r = 0.0f;
      td.color_g = 1.0f;
      td.color_b = 0.0f;
      td.color_a = 0.5f;
      squad_size_text_ = AddText_(td);
    }
  }

  AddMeter_(MeterType_::kTokens, 1.0f, 1.0f, 1.0f, 1.0f, true, "");
  AddMeter_(MeterType_::kTickets, 1.0f, 1.0f, 1.0f, 1.0f, false, "");

  // Chest slots.
  {
    // Bar backing.
    {
      ButtonDef_ bd;
      bd.h_align = 0.5f;
      bd.v_align = VAlign_::kBottom;
      bd.width = 500.0f;
      bd.height = 100.0f;
      bd.x = 0.0f;
      bd.y = 41.0f;
      bd.img = "uiAtlas2";
      bd.mesh_transparent = "toolbarBackingBottom2";
      bd.selectable = false;
      bd.color_r = 0.473f;
      bd.color_g = 0.44f;
      bd.color_b = 0.583f;
      bd.opacity = 1.0f;

      bd.depth_min = 0.2f;
      bd.call = UIV1Python::ObjID::kEmptyCall;
      bd.visibility_mask =
          (static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFull)
           | static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFullNoBack)
           | static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFullRoot));
      bd.allow_in_game = false;
      chest_backing_ = AddButton_(bd);
    }

    auto&& chest0{chest_slots_["0"]};
    auto&& chest1{chest_slots_["1"]};
    auto&& chest2{chest_slots_["2"]};
    auto&& chest3{chest_slots_["3"]};

    // Chest/Slot buttons.
    ButtonDef_ b;
    b.h_align = 0.5f;
    b.v_align = VAlign_::kBottom;
    b.depth_min = 0.3f;
    b.visibility_mask =
        (static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFull)
         | static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFullNoBack)
         | static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFullRoot));
    float spacing = 120.0f;
    b.allow_in_game = false;

    b.y = 44.0f;
    b.img = "chestIconEmpty";
    b.width = b.height = 80.0f;
    b.opacity = 1.0f;

    b.call = UIV1Python::ObjID::kRootUIChestSlot0PressCall;
    b.x = -1.5f * spacing;
    chest0.button = AddButton_(b);

    b.call = UIV1Python::ObjID::kRootUIChestSlot1PressCall;
    b.x = -0.5f * spacing;
    chest1.button = AddButton_(b);

    b.x = 0.5f * spacing;
    b.call = UIV1Python::ObjID::kRootUIChestSlot2PressCall;
    chest2.button = AddButton_(b);

    b.x = 1.5f * spacing;
    b.call = UIV1Python::ObjID::kRootUIChestSlot3PressCall;
    chest3.button = AddButton_(b);

    // Lock icons.
    {
      ImageDef_ imgd;
      imgd.x = -45.0f;
      imgd.y = -23.0f;
      imgd.width = 32.0f;
      imgd.height = 32.0f;
      imgd.img = "lock";
      imgd.depth_min = 0.3f;

      imgd.button = chest0.button;
      chest0.lock_icon = AddImage_(imgd);

      imgd.button = chest1.button;
      chest1.lock_icon = AddImage_(imgd);

      imgd.button = chest2.button;
      chest2.lock_icon = AddImage_(imgd);

      imgd.button = chest3.button;
      chest3.lock_icon = AddImage_(imgd);
    }

    // TV icons.
    {
      ImageDef_ imgd;
      imgd.x = -34.0f;
      imgd.y = -27.0f;
      imgd.width = 32.0f;
      imgd.height = 32.0f;
      imgd.img = "tv";
      imgd.depth_min = 0.3f;
      imgd.color_r = 1.5f;
      imgd.color_g = 1.0f;
      imgd.color_b = 2.0f;

      imgd.button = chest0.button;
      chest0.tv_icon = AddImage_(imgd);

      imgd.button = chest1.button;
      chest1.tv_icon = AddImage_(imgd);

      imgd.button = chest2.button;
      chest2.tv_icon = AddImage_(imgd);

      imgd.button = chest3.button;
      chest3.tv_icon = AddImage_(imgd);
    }

    // Lock times.
    {
      TextDef_ td;
      td.text = "3h 2m";
      td.x = 0.0f;
      td.y = 55.0f;
      td.scale = 0.7f;
      td.flatness = 1.0f;
      td.shadow = 1.0f;
      td.depth_min = 0.3f;
      td.color_r = kChestTextColorR;
      td.color_g = kChestTextColorG;
      td.color_b = kChestTextColorB;

      td.button = chest0.button;
      chest0.text = AddText_(td);

      td.button = chest1.button;
      chest1.text = AddText_(td);

      td.button = chest2.button;
      chest2.text = AddText_(td);

      td.button = chest3.button;
      chest3.text = AddText_(td);
    }
  }

  // Inbox button.
  {
    ButtonDef_ b;
    b.h_align = 0.0f;
    b.v_align = VAlign_::kBottom;
    b.width = b.height = 60.0f;
    b.y = b.height * 0.5f + 2.0f;
    b.color_r = kBotLeftColorR;
    b.color_g = kBotLeftColorG;
    b.color_b = kBotLeftColorB;
    b.img = "logIcon";
    b.call = UIV1Python::ObjID::kRootUIInboxButtonPressCall;
    b.visibility_mask =
        (static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFull)
         | static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFullNoBack)
         | static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFullRoot));
    b.pre_buffer = 20.0f;
    b.allow_in_game = false;
    inbox_button_ = AddButton_(b);

    bottom_left_buttons_.push_back(inbox_button_);

    // Inbox count circle backing.
    {
      ImageDef_ imgd;
      imgd.button = inbox_button_;
      imgd.x = 18.0f;
      imgd.y = 24.0f;
      imgd.width = 32.0f;
      imgd.height = 32.0f;
      imgd.img = "circle";
      imgd.depth_min = 0.3f;
      imgd.color_r = 1.0f;
      imgd.color_g = 0.0f;
      imgd.color_b = 0.0f;
      auto* img = AddImage_(imgd);
      inbox_count_backing_ = img;
    }
    // Inbox count number.
    {
      TextDef_ td;
      td.button = inbox_button_;
      td.width = 24.0f;
      td.text = "2";
      td.x = 17.0f;
      td.y = 24.0f;
      td.scale = 0.8f;
      td.flatness = 1.0f;
      td.shadow = 0.0f;
      td.depth_min = 0.3f;
      td.color_r = 1.0f;
      td.color_g = 1.0f;
      td.color_b = 1.0f;
      inbox_count_text_ = AddText_(td);
    }
    // Inbox announce text.
    {
      TextDef_ td;
      td.button = inbox_button_;
      td.width = 400;
      td.text = "You have unclaimed prizes!";
      td.x = -30.0f;
      td.y = 40.0f;
      td.scale = 0.8f;
      td.flatness = 1.0f;
      td.shadow = 1.0f;
      td.depth_min = 0.3f;
      td.color_r = 1.0f;
      td.color_g = 1.0f;
      td.color_b = 1.0f;
      td.h_align = TextWidget::HAlign::kLeft;
      td.v_align = TextWidget::VAlign::kBottom;
      inbox_announce_text_ = AddText_(td);
    }
  }

  // Achievements button.
  if (explicit_bool(true)) {
    ButtonDef_ b;
    b.h_align = 0.0f;
    b.v_align = VAlign_::kBottom;
    b.width = b.height = 60.0f;
    b.y = b.height * 0.5f + 2.0f;
    b.color_r = kBotLeftColorR;
    b.color_g = kBotLeftColorG;
    b.color_b = kBotLeftColorB;
    b.img = "achievementsIcon";
    b.call = UIV1Python::ObjID::kRootUIAchievementsButtonPressCall;
    b.visibility_mask =
        (static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFull)
         | static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFullNoBack)
         | static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFullRoot));
    b.pre_buffer = 20.0f;
    b.allow_in_game = false;
    achievements_button_ = AddButton_(b);
    bottom_left_buttons_.push_back(achievements_button_);

    auto centerx = -1.5f;
    auto centery = 8.0f;
    {
      TextDef_ td;
      td.button = achievements_button_;
      td.width = 26.0f;
      td.text = "";
      td.x = centerx;
      td.y = centery;
      td.scale = 0.6f;
      td.flatness = 1.0f;
      td.shadow = 0.0f;
      td.depth_min = 0.3f;
      td.color_r = 0.8f;
      td.color_g = 0.75f;
      td.color_b = 0.9f;
      achievement_percent_text_ = AddText_(td);
    }
  }

  // Leaderboards button.
  if (explicit_bool(false)) {
    ButtonDef_ b;
    b.h_align = 0.0f;
    b.v_align = VAlign_::kBottom;
    b.width = b.height = 60.0f;
    b.y = b.height * 0.5f + 2.0f;
    b.color_r = kBotLeftColorR;
    b.color_g = kBotLeftColorG;
    b.color_b = kBotLeftColorB;
    b.img = "leaderboardsIcon";
    b.visibility_mask =
        (static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFull)
         | static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFullNoBack)
         | static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFullRoot));
    AddButton_(b);
  }

  // Settings button.
  {
    ButtonDef_ b;
    b.h_align = 0.0f;
    b.v_align = VAlign_::kBottom;
    b.width = b.height = 60.0f;
    b.y = b.height * 0.58f - 2.0f;
    b.color_r = kBotLeftColorR;
    b.color_g = kBotLeftColorG;
    b.color_b = kBotLeftColorB;
    b.img = "settingsIcon";
    b.call = UIV1Python::ObjID::kRootUISettingsButtonPressCall;
    b.visibility_mask =
        (static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFull)
         | static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFullNoBack)
         | static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFullRoot)
         | static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuInGame));
    b.pre_buffer = 20.0f;
    settings_button_ = AddButton_(b);
    bottom_left_buttons_.push_back(settings_button_);
  }

  // Inventory button.
  {
    ButtonDef_ b;
    b.h_align = 1.0f;
    b.v_align = VAlign_::kBottom;
    b.width = b.height = 135.0f;
    // b.x = -80.0f;
    b.y = b.height * 0.45f;
    b.img = "inventoryIcon";
    b.call = UIV1Python::ObjID::kRootUIInventoryButtonPressCall;
    b.visibility_mask =
        (static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFull)
         | static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFullNoBack)
         | static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFullRoot));
    b.disable_offset_scale = 1.5f;
    b.pre_buffer = 10.0f;
    b.allow_in_game = false;

    // This is a very big icon that can interfere with clicking stuff near
    // it, so suck target area in a bit.
    b.target_extra_left = -20.0f;
    b.target_extra_right = -20.0f;
    inventory_button_ = AddButton_(b);
    bottom_right_buttons_.push_back(inventory_button_);
  }

  // Store button.
  {
    ButtonDef_ b;
    b.h_align = 1.0f;
    b.v_align = VAlign_::kBottom;
    b.width = b.height = 85.0f;
    b.y = b.height * 0.5f;
    b.img = "storeIcon";
    b.call = UIV1Python::ObjID::kRootUIStoreButtonPressCall;
    b.visibility_mask =
        (static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFull)
         | static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFullNoBack)
         | static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFullRoot));
    b.pre_buffer = 10.0f;
    b.allow_in_game = false;

    store_button_ = AddButton_(b);
    bottom_right_buttons_.push_back(store_button_);
  }

  UpdateForFocusedWindow_(nullptr);
}

void RootWidget::StepInbox_(base::RenderPass* renderpass, seconds_t dt) {
  // Quick-out: we only do work while we're animating.
  if (!inbox_animating_) {
    return;
  }

  assert(inbox_button_);
  assert(inbox_announce_text_);
  auto* widget{inbox_button_->widget.get()};
  assert(widget);

  // Stop animating once our anim time has passed (AND we're not announcing
  // anything; we animate indefinitely while announcements are up).
  if (renderpass->frame_def()->display_time() > inbox_anim_flash_time_
      && inbox_announce_text_str_.empty()) {
    inbox_animating_ = false;
    widget->set_color(kBotLeftColorR, kBotLeftColorG, kBotLeftColorB);
    return;
  } else {
    // Flash faster if we're doing a 'flash' and slower otherwise (when announce
    // text is showing).
    float freq_mult;
    if (renderpass->frame_def()->display_time() <= inbox_anim_flash_time_) {
      freq_mult = 4.0f;
    } else {
      freq_mult = 1.0f;
    }
    float mult{1.0f
               + fabsf(2.0f
                       * sinf(freq_mult * 3.1415f
                              * static_cast<float>(
                                  inbox_anim_flash_time_
                                  - renderpass->frame_def()->display_time())))};

    widget->set_color(kBotLeftColorR * mult, kBotLeftColorG * mult,
                      kBotLeftColorB * mult);
    inbox_announce_text_->widget->set_color(
        kBotLeftColorR * mult, kBotLeftColorG * mult * 0.5f, 0.0f, 1.0f);
  }
}

void RootWidget::StepChests_(base::RenderPass* renderpass, seconds_t dt) {
  auto current_display_time = renderpass->frame_def()->display_time();
  // auto current_seconds_since_epoch{g_base->TimeSinceEpochCloudSeconds()};

  bool should_update{};

  // Aim to run at least once per second so time strings stay up to date.
  seconds_t update_increment = 1.0;

  for (auto&& chest_id : chest_ids) {
    auto&& slot{chest_slots_[chest_id]};

    // If a slot is ready to open, refresh fast enough for our text color
    // modulation to look smooth.
    if (slot.needs_faster_refresh) {
      update_increment = 0.05;
    }

    // If the slot needs a regular update (and is not currently animating
    // and updates are not currently paused) give it an opportunity to do
    // so.
    if (slot.live_display_dirty && !slot.unlock_time_animating
        && !update_pause_count_) {
      should_update = true;
    }

    if (!slot.unlock_time_animating) {
      continue;
    }

    // Ok; this slot is animating. No matter what we'll want to update to
    // show the latest vis value.
    should_update = true;

    if (current_display_time > slot.unlock_time_animation_end_time) {
      // Anim is done; reset stuff and do an update to get things back
      // to their default display.
      slot.unlock_time_animating = false;
      // Make note that we need to go back to a live value after this
      // animation. It might not be possible immediately if updates are
      // paused/etc.
      slot.live_display_dirty = true;
      // Stop any playing anim sound.
      if (chest_unlock_time_anim_sound_play_id_.has_value()) {
        g_base->audio->PushSourceStopSoundCall(
            *chest_unlock_time_anim_sound_play_id_);
        chest_unlock_time_anim_sound_play_id_.reset();
      }
    } else {
      // Calc value from 0 to 1 for animation progression.
      auto amt{std::max(
          0.0, std::min(1.0, (current_display_time
                              - slot.unlock_time_animation_start_time)
                                 / (slot.unlock_time_animation_end_time
                                    - slot.unlock_time_animation_start_time)))};

      // Calc the current vis value for the animation.
      slot.vis_unlock_time =
          amt * slot.unlock_time_animation_end_val
          + (1.0 - amt) * slot.unlock_time_animation_start_val;
    }
  }

  if (current_display_time - last_chests_step_time_ >= update_increment) {
    should_update = true;
  }
  if (!should_update) {
    return;
  }

  last_chests_step_time_ = current_display_time;
  UpdateChests_();
}

void RootWidget::StepLeagueRank_(base::RenderPass* renderpass, seconds_t dt) {
  // We only do work here during animations.
  if (!league_rank_animating_) {
    return;
  }
  assert(league_rank_text_);
  assert(trophy_meter_button_);

  auto improving{league_rank_vis_value_ < league_rank_anim_start_val_};
  float anim_dir{league_rank_vis_value_ > league_rank_anim_val_ ? 1.0f : -1.0f};
  float anim_time{static_cast<float>(renderpass->frame_def()->display_time()
                                     - league_rank_anim_start_time_)};
  auto anim_speed{4.0f + anim_time * 20.0f};

  // Get the pain over with quickly if things are getting worse.
  if (!improving) {
    anim_speed *= 4.0f;
  }
  league_rank_anim_val_ += static_cast<float>(dt) * anim_speed * anim_dir;
  league_rank_text_->widget->SetText(
      "#" + std::to_string(static_cast<int>(league_rank_anim_val_)));
  float cscale{1.5f
               - 0.5f * sinf(40.0f * renderpass->frame_def()->display_time())};
  float cscale2{0.7f * 1.0f + 0.3f * cscale};

  if (improving) {
    trophy_meter_button_->widget->set_color(
        kMeterColorR * cscale2, kMeterColorG * cscale, kMeterColorB * cscale2);
  } else {
    trophy_meter_button_->widget->set_color(
        kMeterColorR * cscale, kMeterColorG * cscale2, kMeterColorB * cscale2);
  }

  // If we reach/pass the target point, set the exact final value and end
  // the anim.
  if ((anim_dir > 0.0f
       && league_rank_anim_val_ >= static_cast<float>(league_rank_vis_value_))
      || (anim_dir <= 0.0f
          && league_rank_anim_val_
                 <= static_cast<float>(league_rank_vis_value_))) {
    league_rank_animating_ = false;
    if (league_rank_anim_sound_play_id_.has_value()) {
      g_base->audio->PushSourceStopSoundCall(*league_rank_anim_sound_play_id_);
      league_rank_anim_sound_play_id_.reset();
    }
    g_base->audio->SafePlaySysSound(improving ? base::SysSoundID::kCashRegister
                                              : base::SysSoundID::kPowerDown);
    league_rank_text_->widget->SetText(
        "#" + std::to_string(league_rank_vis_value_));
    trophy_meter_button_->widget->set_color(kMeterColorR, kMeterColorG,
                                            kMeterColorB);
    int diff{league_rank_anim_start_val_ - league_rank_vis_value_};
    auto diff_str{std::to_string(diff)};
    if (diff >= 0) {
      diff_str = "+" + diff_str;
    }
    ShowTrophyMeterAnnotation_(
        diff_str, improving ? Vector3f(0, 1, 0) : Vector3f(1, 0, 0));
  }
}

void RootWidget::StepTicketsMeter_(base::RenderPass* renderpass, seconds_t dt) {
  auto do_update{false};

  auto current_display_time = renderpass->frame_def()->display_time();

  // If our live display is dirty and there's not animation or pauses going
  // on, update our display from the live data.
  if (tickets_meter_live_display_dirty_ && !tickets_meter_animating_
      && !update_pause_count_) {
    tickets_meter_vis_value_ = tickets_meter_value_;
    tickets_meter_live_display_dirty_ = false;
    do_update = true;
  }

  // If we're animating, calc a new interpolated value and always update.
  if (tickets_meter_animating_) {
    // Always update when animating.
    do_update = true;

    if (current_display_time > tickets_anim_end_time_) {
      // Anim is done; reset stuff and do an update to get things back
      // to their default display.
      tickets_meter_animating_ = false;
      // g_base->audio->SafePlaySysSound(base::SysSoundID::kCashRegister);
      // Make note that we need to go back to a live value after this
      // animation. It might not be possible immediately if updates are
      // paused/etc.
      tickets_meter_live_display_dirty_ = true;
      // Stop any playing anim sound.
      if (tickets_anim_sound_play_id_.has_value()) {
        g_base->audio->PushSourceStopSoundCall(*tickets_anim_sound_play_id_);
        tickets_anim_sound_play_id_.reset();
      }
    }
    // Calc value from 0 to 1 for animation progression.
    auto amt{std::max(
        0.0, std::min(1.0, (current_display_time - tickets_anim_start_time_)
                               / (tickets_anim_end_time_
                                  - tickets_anim_start_time_)))};

    // Calc the current vis value for the animation.
    tickets_meter_vis_value_ = static_cast<int>(
        amt * static_cast<double>(tickets_anim_end_value_)
        + (1.0 - amt) * static_cast<double>(tickets_anim_start_value_));
  }

  if (!do_update) {
    return;
  }

  // Ok; update our visuals.
  assert(tickets_meter_text_);
  tickets_meter_text_->widget->SetText(
      tickets_meter_vis_value_ >= 0 ? std::to_string(tickets_meter_vis_value_)
                                    : "");
  UpdateTicketsMeterTextColor_();
}

void RootWidget::StepTokensMeter_(base::RenderPass* renderpass, seconds_t dt) {
  auto do_update{false};

  auto current_display_time = renderpass->frame_def()->display_time();

  // If our live display is dirty and there's not animation or pauses going
  // on, update our display from the live data.
  if (tokens_meter_live_display_dirty_ && !tokens_meter_animating_
      && !update_pause_count_) {
    tokens_meter_vis_value_ = tokens_meter_value_;
    tokens_meter_live_display_dirty_ = false;
    do_update = true;
  }

  // If we're animating, calc a new interpolated value and always update.
  if (tokens_meter_animating_) {
    // Always update when animating.
    do_update = true;

    if (current_display_time > tokens_anim_end_time_) {
      // Anim is done; reset stuff and do an update to get things back
      // to their default display.
      tokens_meter_animating_ = false;
      // g_base->audio->SafePlaySysSound(base::SysSoundID::kCashRegister);
      // Make note that we need to go back to a live value after this
      // animation. It might not be possible immediately if updates are
      // paused/etc.
      tokens_meter_live_display_dirty_ = true;
      // Stop any playing anim sound.
      if (tokens_anim_sound_play_id_.has_value()) {
        g_base->audio->PushSourceStopSoundCall(*tokens_anim_sound_play_id_);
        tokens_anim_sound_play_id_.reset();
      }
    }
    // Calc value from 0 to 1 for animation progression.
    auto amt{std::max(
        0.0, std::min(1.0, (current_display_time - tokens_anim_start_time_)
                               / (tokens_anim_end_time_
                                  - tokens_anim_start_time_)))};
    // Calc the current vis value for the animation.
    tokens_meter_vis_value_ = static_cast<int>(
        amt * static_cast<double>(tokens_anim_end_value_)
        + (1.0 - amt) * static_cast<double>(tokens_anim_start_value_));
  }

  if (!do_update) {
    return;
  }

  // Ok; update our visuals.
  assert(tokens_meter_text_);
  assert(get_tokens_button_);
  if (gold_pass_) {
    // Use the infinity symbol if we have full unicode support.
    tokens_meter_text_->widget->SetText(
        g_buildconfig.enable_os_font_rendering() ? "\xE2\x88\x9E" : "inf");
  } else {
    tokens_meter_text_->widget->SetText(
        tokens_meter_vis_value_ >= 0 ? std::to_string(tokens_meter_vis_value_)
                                     : "");
  }
  UpdateTokensMeterTextColor_();
}

void RootWidget::Draw(base::RenderPass* renderpass, bool transparent) {
  // Keep this handy for stuff that wants to use it.
  last_draw_display_time_ = renderpass->frame_def()->display_time();

  // Opaque pass gets drawn first; use that as an opportunity to step up our
  // motion.
  if (!transparent) {
    Update_(renderpass);
  }
  ContainerWidget::Draw(renderpass, transparent);
}

void RootWidget::Update_(base::RenderPass* renderpass) {
  seconds_t current_time = renderpass->frame_def()->display_time();
  seconds_t time_diff = std::min(seconds_t{0.1}, current_time - update_time_);

  // Keep track of how long updates have been paused for and warn if it
  // seems like we're stuck.
  if (update_pause_count_ > 0) {
    auto oldtime{update_pause_total_time_};
    update_pause_total_time_ += time_diff;
    seconds_t threshold{30.0};
    if (oldtime < threshold && update_pause_total_time_ >= threshold) {
      g_core->logging->Log(LogName::kBaApp, LogLevel::kWarning,
                           "RootWidget updates have been paused for "
                               + std::to_string(update_pause_total_time_)
                               + " seconds; something may be broken.");
    }
  } else {
    update_pause_total_time_ = 0.0;
  }

  StepChildWidgets_(time_diff);
  StepChests_(renderpass, time_diff);
  StepLeagueRank_(renderpass, time_diff);
  StepInbox_(renderpass, time_diff);
  StepTicketsMeter_(renderpass, time_diff);
  StepTokensMeter_(renderpass, time_diff);

  update_time_ = current_time;
}

auto RootWidget::AddButton_(const ButtonDef_& def) -> RootWidget::Button_* {
  base::ScopedSetContext ssc(nullptr);
  buttons_.emplace_back();
  Button_& b(buttons_.back());
  b.x = b.x_smoothed = b.x_target = def.x;
  b.y = b.y_smoothed = b.y_target = def.y;
  b.y_offs_small = def.y_offs_small;
  b.visibility_mask = def.visibility_mask;
  b.disable_offset_scale = def.disable_offset_scale;
  b.pre_buffer = def.pre_buffer;
  b.post_buffer = def.post_buffer;
  b.scale = def.scale;
  b.width = def.width;
  b.height = def.height;
  b.h_align = def.h_align;
  b.v_align = def.v_align;
  b.selectable = def.selectable;
  b.allow_in_game = def.allow_in_game;
  b.allow_in_main_menu = def.allow_in_main_menu;
  b.widget = Object::New<ButtonWidget>();
  b.widget->set_color(def.color_r, def.color_g, def.color_b);
  b.widget->set_opacity(def.opacity);
  b.widget->set_auto_select(true);
  b.widget->set_text(def.label);
  b.widget->set_enabled(def.selectable);
  b.widget->set_selectable(def.selectable);
  b.widget->set_depth_range(def.depth_min, def.depth_max);
  b.widget->set_target_extra_left(def.target_extra_left);
  b.widget->set_target_extra_right(def.target_extra_right);

  b.widget->set_enable_sound(def.enable_sound);

  // Make sure up/down moves focus into the main stack.
  assert(screen_stack_widget_ != nullptr);
  assert(b.v_align != VAlign_::kCenter);
  if (b.v_align == VAlign_::kTop) {
    b.widget->SetDownWidget(screen_stack_widget_);
  } else {
    b.widget->SetUpWidget(screen_stack_widget_);
  }

  // We wanna prevent anyone from redirecting these to point to outside
  // widgets since we'll probably outlive those outside widgets.
  b.widget->set_neighbors_locked(true);

  if (!def.img.empty()) {
    base::Assets::AssetListLock lock;
    b.widget->SetTexture(g_base->assets->GetTexture(def.img).get());
  }
  if (!def.mesh_transparent.empty()) {
    base::Assets::AssetListLock lock;
    b.widget->SetMeshTransparent(
        g_base->assets->GetMesh(def.mesh_transparent).get());
  }
  if (!def.mesh_opaque.empty()) {
    base::Assets::AssetListLock lock;
    b.widget->SetMeshOpaque(g_base->assets->GetMesh(def.mesh_opaque).get());
  }
  if (def.call != UIV1Python::ObjID::kEmptyCall) {
    b.widget->SetOnActivateCall(g_ui_v1->python->objs().Get(def.call).get());
  }
  AddWidget(b.widget.get());
  return &b;
}

auto RootWidget::AddText_(const TextDef_& def) -> RootWidget::Text_* {
  base::ScopedSetContext ssc(nullptr);
  texts_.emplace_back();
  Text_& t(texts_.back());
  t.button = def.button;
  t.widget = Object::New<TextWidget>();
  t.widget->SetWidth(0.0f);
  t.widget->SetHeight(0.0f);
  t.widget->SetHAlign(def.h_align);
  t.widget->SetVAlign(def.v_align);
  t.widget->SetText(def.text);
  t.widget->set_max_width(def.width);
  t.widget->set_center_scale(def.scale);
  t.widget->set_color(def.color_r, def.color_g, def.color_b, def.color_a);
  t.widget->set_shadow(def.shadow);
  t.widget->set_flatness(def.flatness);
  t.widget->set_depth_range(def.depth_min, def.depth_max);
  assert(def.button->widget.exists());
  t.widget->set_draw_control_parent(def.button->widget.get());
  t.x = def.x;
  t.y = def.y;
  AddWidget(t.widget.get());
  return &t;
}

auto RootWidget::AddImage_(const ImageDef_& def) -> RootWidget::Image_* {
  base::ScopedSetContext ssc(nullptr);
  images_.emplace_back();
  Image_& img(images_.back());
  img.button = def.button;
  img.widget = Object::New<ImageWidget>();
  img.widget->set_width(def.width);
  img.widget->set_height(def.height);
  img.widget->set_depth_range(def.depth_min, def.depth_max);
  if (!def.img.empty()) {
    base::Assets::AssetListLock lock;
    img.widget->SetTexture(g_base->assets->GetTexture(def.img).get());
  }
  img.widget->set_color(def.color_r, def.color_g, def.color_b);
  assert(def.button->widget.exists());
  img.widget->set_draw_control_parent(def.button->widget.get());
  img.x = def.x - def.width * 0.5f;
  img.y = def.y - def.height * 0.5f;
  AddWidget(img.widget.get());
  return &img;
}

void RootWidget::UpdateForFocusedWindow() {
  UpdateForFocusedWindow_(
      screen_stack_widget_ != nullptr
          ? screen_stack_widget_->GetTopmostToolbarInfluencingWidget()
          : nullptr);
}

void RootWidget::UpdateForFocusedWindow_(Widget* widget) {
  // Take note whether we're currently in a main menu vs gameplay.
  in_main_menu_ = g_base->app_mode()->IsInMainMenu();

  if (widget == nullptr) {
    toolbar_visibility_ = ToolbarVisibility::kInGame;
  } else {
    toolbar_visibility_ = widget->toolbar_visibility();
  }
  MarkForUpdate();
}

void RootWidget::StepChildWidgets_(seconds_t dt) {
  // Hitches tend to break our math and cause buttons to overshoot on their
  // transitions in and then back up. So let's limit our max dt to about
  // what ~30fps would give us.
  dt = std::min(dt, 1.0 / 30.0);

  float dt_ms = dt * 1000.0;

  if (!child_widgets_dirty_) {
    return;
  }

  bool is_small{g_base->ui->uiscale() == UIScale::kSmall};

  // Update enabled-state for all buttons.
  for (Button_& b : buttons_) {
    bool enable_button =
        static_cast<bool>(static_cast<uint32_t>(toolbar_visibility_)
                          & static_cast<uint32_t>(b.visibility_mask));
    // When we're in the main menu, always disable the menu button and shift
    // the party button a bit to the right
    if (in_main_menu_) {
      if (!b.allow_in_main_menu) {
        enable_button = false;
      }
    } else {
      if (!b.allow_in_game) {
        enable_button = false;
      }
    }
    // Back button is always disabled in medium/large UI.
    if (&b == back_button_ && !is_small) {
      enable_button = false;
    }
    if (b.force_hide) {
      enable_button = false;
    }
    auto prev_enabled{b.enabled};
    b.enabled = enable_button;

    // If trophy meter just switched to enabled, give it a chance to display
    // new value animations/etc.
    if (&b == trophy_meter_button_ && !prev_enabled && enable_button) {
      trophy_meter_display_timer_ = base::AppTimer::New(
          1.0f, false, [this] { UpdateLeagueRankDisplay_(); });
    }

    // Same for inbox.
    if (&b == inbox_button_ && !prev_enabled && enable_button) {
      inbox_display_timer_ =
          base::AppTimer::New(1.0f, false, [this] { UpdateInboxDisplay_(); });
    }
  }

  // Go through our corner button lists updating positions based on
  // what is visible.
  float xpos = 0.0f;
  for (auto* btn : top_left_buttons_) {
    auto enabled = btn->enabled;
    float bwidthhalf = btn->width * 0.5f;
    if (enabled) {
      xpos += bwidthhalf + btn->pre_buffer;
    }
    btn->x = xpos;
    if (enabled) {
      xpos += bwidthhalf + btn->post_buffer;
    }
  }
  xpos = 0.0f;
  for (auto* btn : top_right_buttons_) {
    auto enabled = btn->enabled;
    float bwidthhalf = btn->width * 0.5;
    if (enabled) {
      xpos -= bwidthhalf + btn->pre_buffer;
    }
    btn->x = xpos;
    if (enabled) {
      xpos -= bwidthhalf + btn->post_buffer;
    }
  }
  xpos = 0.0f;
  float bottom_left_height{};
  for (auto* btn : bottom_left_buttons_) {
    auto enabled = btn->enabled;
    float bwidthhalf = btn->width * 0.5;
    if (enabled) {
      xpos += bwidthhalf + btn->pre_buffer;
      bottom_left_height =
          std::max(bottom_left_height, btn->y + btn->height * 0.5f);
    }
    btn->x = xpos;
    if (enabled) {
      xpos += bwidthhalf + btn->post_buffer;
    }
  }
  bottom_left_height_ = bottom_left_height * base_scale_;

  xpos = 0.0f;
  for (auto* btn : bottom_right_buttons_) {
    auto enabled = btn->enabled;
    float bwidthhalf = btn->width * 0.5;
    if (enabled) {
      xpos -= bwidthhalf + btn->pre_buffer;
    }
    btn->x = xpos;
    if (enabled) {
      xpos -= bwidthhalf + btn->post_buffer;
    }
  }

  // Go through our buttons updating their target points and smooth values.
  // If everything has arrived at its target point, mark us as not dirty.
  bool have_dirty = false;
  for (Button_& b : buttons_) {
    // Update our target position.
    b.x_target = b.x;
    b.y_target = b.y + (is_small ? b.y_offs_small : 0.0f);
    float disable_offset = b.disable_offset_scale * 110.0f
                           * ((b.v_align == VAlign_::kTop) ? 1.0f : -1.0f);

    // Can turn this down to debug visibility.
    if (explicit_bool(false)) {
      disable_offset *= 0.1f;
    }

    if (&b == back_button_) {
      // Whenever back button is enabled, left on account button should go
      // to it; otherwise it goes nowhere.
      Widget* ab = account_button_->widget.get();
      ab->set_neighbors_locked(false);
      ab->SetLeftWidget(b.enabled ? back_button_->widget.get() : ab);
      account_button_->widget->set_neighbors_locked(true);
    }

    if (!b.enabled) {
      b.y_target += disable_offset;
    }

    // Now push our smooth value towards our target value.
    b.x_smoothed += (b.x_target - b.x_smoothed) * 0.015f * dt_ms;
    b.y_smoothed += (b.y_target - b.y_smoothed) * 0.015f * dt_ms;

    // Snap in place once we reach the target; otherwise note that we need
    // to keep going.
    if (std::abs(b.x_target - b.x_smoothed) < 0.1f
        && std::abs(b.y_target - b.y_smoothed) < 0.1f) {
      b.x_smoothed = b.x_target;
      b.y_smoothed = b.y_target;

      // Also flip off visibility if we're moving offscreen and have
      // reached our target.
      if (!b.enabled) {
        b.fully_offscreen = true;
        b.widget->set_visible_in_container(false);
      }
    } else {
      have_dirty = true;
      // Always remain visible while still moving.
      b.fully_offscreen = false;
      b.widget->set_visible_in_container(true);
    }

    // Now calc final abs x and y based on screen size, smoothed positions,
    // etc.
    float x, y;
    x = width() * b.h_align
        + base_scale_ * (b.x_smoothed - b.width * b.scale * 0.5f);
    switch (b.v_align) {
      case VAlign_::kTop:
        y = height() + base_scale_ * (b.y_smoothed - b.height * b.scale * 0.5f);
        break;
      case VAlign_::kCenter:
        y = height() * 0.5f
            + base_scale_ * (b.y_smoothed - b.height * b.scale * 0.5f);
        break;
      case VAlign_::kBottom:
        y = base_scale_ * (b.y_smoothed - b.height * b.scale * 0.5f);
        break;
    }
    b.widget->set_selectable(b.enabled && b.selectable);
    b.widget->set_enabled(b.enabled && b.selectable);
    b.widget->set_translate(x, y);
    b.widget->set_width(b.width);
    b.widget->set_height(b.height);
    b.widget->set_scale(b.scale * base_scale_);
  }

  for (Text_& t : texts_) {
    // Move the text widget to wherever its target button is (plus offset).
    Button_* b = t.button;
    float x =
        b->widget->tx() + base_scale_ * b->scale * (b->width * 0.5f + t.x);
    float y =
        b->widget->ty() + base_scale_ * b->scale * (b->height * 0.5f + t.y);
    t.widget->set_translate(x, y);
    t.widget->set_scale(base_scale_ * b->scale);
    t.widget->set_visible_in_container(!b->fully_offscreen && t.visible);
  }

  for (Image_& img : images_) {
    // Move the image widget to wherever its target button is (plus offset).
    Button_* b = img.button;
    float x =
        b->widget->tx() + base_scale_ * b->scale * (b->width * 0.5f + img.x);
    float y =
        b->widget->ty() + base_scale_ * b->scale * (b->height * 0.5f + img.y);
    img.widget->set_translate(x, y);
    img.widget->set_scale(base_scale_ * b->scale);
    img.widget->set_visible_in_container(!b->fully_offscreen && img.visible);
  }

  child_widgets_dirty_ = have_dirty;
}

void RootWidget::UpdateLayout() {
  // Now actually put things in place.
  base_scale_ = 1.0f;
  switch (g_base->ui->uiscale()) {
    case UIScale::kLarge:
      base_scale_ = 0.6f;
      break;
    case UIScale::kMedium:
      base_scale_ = 0.8f;
      break;
    default:
      base_scale_ = 1.18f;
      break;
  }

  // Update the window stack.
  BA_DEBUG_UI_READ_LOCK;
  if (screen_stack_widget_ != nullptr) {
    screen_stack_widget_->set_translate(0, 0);
    screen_stack_widget_->SetWidth(width());
    screen_stack_widget_->SetHeight(height());
  }
  if (overlay_stack_widget_ != nullptr) {
    overlay_stack_widget_->set_translate(0, 0);
    overlay_stack_widget_->SetWidth(width());
    overlay_stack_widget_->SetHeight(height());
  }
  child_widgets_dirty_ = true;

  // Run an immediate step to update things; (avoids jumpy positions if
  // resizing game window))
  StepChildWidgets_(0.0);
}

void RootWidget::OnUIScaleChange() { MarkForUpdate(); }

auto RootWidget::HandleMessage(const base::WidgetMessage& m) -> bool {
  // If a cancel message comes through and our back button is enabled, fire
  // our back button. In all other cases just do the default.
  if (m.type == base::WidgetMessage::Type::kCancel && back_button_ != nullptr
      && back_button_->widget->enabled()
      && !overlay_stack_widget_->HasChildren()) {
    back_button_->widget->Activate();
    return true;
  } else {
    return ContainerWidget::HandleMessage(m);
  }
}

void RootWidget::SquadPress() {
  assert(g_base->InLogicThread());
  if (squad_button_) {
    squad_button_->widget->Activate();
  }
}

void RootWidget::BackPress() {
  assert(g_base->InLogicThread());
  screen_stack_widget_->HandleMessage(
      base::WidgetMessage(base::WidgetMessage::Type::kCancel));
}

void RootWidget::SetScreenWidget(StackWidget* w) {
  // this needs to happen before any buttons get added.
  assert(buttons_.empty());
  AddWidget(w);
  screen_stack_widget_ = w;
}

void RootWidget::SetOverlayWidget(StackWidget* w) {
  // this needs to happen after our buttons and things get added..
  assert(!buttons_.empty());

  AddWidget(w);
  overlay_stack_widget_ = w;
}

auto RootWidget::GetSpecialWidget(const std::string& s) const -> Widget* {
  if (s == "squad_button") {
    return squad_button_ ? squad_button_->widget.get() : nullptr;
  } else if (s == "back_button") {
    return back_button_ ? back_button_->widget.get() : nullptr;
  } else if (s == "account_button") {
    return account_button_ ? account_button_->widget.get() : nullptr;
  } else if (s == "achievements_button") {
    return achievements_button_ ? achievements_button_->widget.get() : nullptr;
  } else if (s == "inbox_button") {
    return inbox_button_ ? inbox_button_->widget.get() : nullptr;
  } else if (s == "settings_button") {
    return settings_button_ ? settings_button_->widget.get() : nullptr;
  } else if (s == "store_button") {
    return store_button_ ? store_button_->widget.get() : nullptr;
  } else if (s == "get_tokens_button") {
    return get_tokens_button_ ? get_tokens_button_->widget.get() : nullptr;
  } else if (s == "inventory_button") {
    return inventory_button_ ? inventory_button_->widget.get() : nullptr;
  } else if (s == "tickets_meter") {
    return tickets_meter_button_ ? tickets_meter_button_->widget.get()
                                 : nullptr;
  } else if (s == "tokens_meter") {
    return tokens_meter_button_ ? tokens_meter_button_->widget.get() : nullptr;
  } else if (s == "trophy_meter") {
    return trophy_meter_button_ ? trophy_meter_button_->widget.get() : nullptr;
  } else if (s == "level_meter") {
    return level_meter_button_ ? level_meter_button_->widget.get() : nullptr;
  } else if (s == "overlay_stack") {
    return overlay_stack_widget_;
  } else if (s == "chest_0_button") {
    return chest_slots_.at("0").button->widget.get();
  } else if (s == "chest_1_button") {
    return chest_slots_.at("1").button->widget.get();
  } else if (s == "chest_2_button") {
    return chest_slots_.at("2").button->widget.get();
  } else if (s == "chest_3_button") {
    return chest_slots_.at("3").button->widget.get();
  }
  return nullptr;
}

void RootWidget::SetAccountSignInState(bool signed_in,
                                       const std::string& name) {
  if (account_name_text_) {
    auto* w{account_name_text_->widget.get()};
    auto* wb{account_button_->widget.get()};
    assert(w);
    assert(wb);

    if (signed_in) {
      w->SetText(g_base->assets->CharStr(SpecialChar::kV2Logo) + name);
      w->set_color(0.0f, 0.4f, 0.1f, 1.0f);
      w->set_shadow(0.2f);
      w->set_flatness(1.0f);
      wb->set_color(0.8f, 1.2f, 0.8f);
    } else {
      w->SetText("{\"r\":\"notSignedInText\"}");
      w->set_color(1.0f, 0.2f, 0.2f, 1.0f);
      w->set_shadow(0.5f);
      w->set_flatness(1.0f);
      wb->set_color(0.45f, 0.4f, 0.4f);
    }
  }
}

void RootWidget::SetSquadSizeLabel(int val) {
  if (squad_size_text_) {
    auto* w{squad_size_text_->widget.get()};
    assert(w);
    w->SetText(std::to_string(val));
    if (val > 0) {
      w->set_color(0.0f, 1.0f, 0.0f, 1.0f);
    } else {
      w->set_color(0.0f, 1.0f, 0.0f, 0.5f);
    }
  }
}

void RootWidget::SetTicketsMeterValue(int val) {
  // Simply store our live value and flag that we have a new live value to
  // update with.
  tickets_meter_value_ = val;
  tickets_meter_live_display_dirty_ = true;
}

void RootWidget::SetTokensMeterValue(int val, bool gold_pass) {
  // Simply store our live value and flag that we have a new live value to
  // update with.
  tokens_meter_value_ = val;
  gold_pass_ = gold_pass;
  tokens_meter_live_display_dirty_ = true;

  // Flag a re-layout since gold pass appearing/disappearing may change our
  // widget layout (plus button disappearing, etc.).
  assert(get_tokens_button_);
  if (gold_pass_) {
    get_tokens_button_->force_hide = true;
  } else {
    get_tokens_button_->force_hide = false;
  }

  child_widgets_dirty_ = true;
}

auto RootWidget::ColorForLeagueValue_(const std::string& value) -> Vector3f {
  Vector3f color{};
  // Set league icon color.
  if (league_type_vis_value_ == "") {
    color = {0.4f, 0.4f, 0.4f};
  } else if (league_type_vis_value_ == "b") {
    color = {1.0f, 0.7f, 0.5f};
  } else if (league_type_vis_value_ == "s") {
    color = {1.0f, 1.0f, 1.4f};
  } else if (league_type_vis_value_ == "g") {
    color = {1.4f, 1.0f, 0.4f};
  } else if (league_type_vis_value_ == "d") {
    color = {1.0f, 0.8f, 2.0f};
  } else {
    g_core->logging->Log(
        LogName::kBa, LogLevel::kError,
        "RootWidget: Invalid league type '" + league_type_vis_value_ + "'.");
  }
  return color;
}

void RootWidget::SetAccountState(const std::string& league_type,
                                 int league_number, int league_rank,
                                 int inbox_count, bool inbox_count_is_max) {
  // Restore *actual* values as well as vis values.
  league_type_value_ = league_type_vis_value_ = league_type;
  league_number_value_ = league_number_vis_value_ = league_number;
  league_rank_value_ = league_rank_vis_value_ = league_rank;
  inbox_count_value_ = inbox_count_vis_value_ = inbox_count;
  inbox_count_is_max_value_ = inbox_count_is_max_vis_value_ =
      inbox_count_is_max;

  // Apply current values instantly to the UI with no animations.
  league_rank_text_->widget->SetText(
      league_rank_vis_value_ > 0
          ? ("#" + std::to_string(league_rank_vis_value_))
          : "");

  SetInboxCountValue_(inbox_count_vis_value_, inbox_count_is_max_vis_value_);
  auto color{ColorForLeagueValue_(league_type_vis_value_)};
  trophy_icon_->widget->set_color(color.x, color.y, color.z);
  UpdateInboxDisplay_();
  UpdateLeagueRankDisplay_();
}

void RootWidget::SetInboxCountValue_(int count, bool is_max) {
  assert(inbox_count_text_);

  std::string sval;

  if (count > 0) {
    sval = std::to_string(count);
    if (is_max) {
      sval += "+";
    }
  } else {
    sval = "";
  }
  inbox_count_text_->widget->SetText(sval);

  auto backing_was_visible{inbox_count_backing_->visible};

  // Hide for both 'unset' (-1) and 0.
  auto backing_is_visible = (count > 0);

  // Request a refresh if our visibility is changing.
  if (backing_was_visible != backing_is_visible) {
    inbox_count_backing_->visible = backing_is_visible;
    inbox_count_text_->visible = backing_is_visible;
    child_widgets_dirty_ = true;
  }
}

void RootWidget::UpdateInboxDisplay_() {
  assert(inbox_count_text_);

  // If we're offscreen AND are displaying some values already, we're
  // done for now. We'll try updating again next time we're visible.
  if (!inbox_button_->enabled && inbox_count_vis_value_ >= 0) {
    return;
  }

  auto prev_inbox_count_vis_value{inbox_count_vis_value_};

  // Ok; we officially want to show the latest values we have. Mark them as
  // visible and either animate or immediately switch to them.
  inbox_count_vis_value_ = inbox_count_value_;
  inbox_count_is_max_vis_value_ = inbox_count_is_max_value_;

  SetInboxCountValue_(inbox_count_vis_value_, inbox_count_is_max_vis_value_);

  // Let's flash the inbox icon when new messages come in.
  auto flash{true};

  // Don't flash if we're going from/to an unset state.
  if (prev_inbox_count_vis_value < 0 || inbox_count_vis_value_ < 0) {
    flash = false;
  }

  // Don't flash if count is staying same or going down.
  if (inbox_count_vis_value_ <= prev_inbox_count_vis_value) {
    flash = false;
  }

  if (flash) {
    inbox_animating_ = true;
    inbox_anim_flash_time_ = g_base->logic->display_time() + 1.5;
    g_base->audio->SafePlaySysSound(base::SysSoundID::kDing);
  }
}

void RootWidget::UpdateLeagueRankDisplay_() {
  assert(trophy_icon_);
  assert(league_rank_text_);
  assert(trophy_meter_button_);

  // If we're offscreen AND are displaying some values already, we're
  // done for now. We'll try updating again next time we're visible.
  if (!trophy_meter_button_->enabled && league_rank_vis_value_ > 0) {
    return;
  }

  auto prev_league_type_vis_value{league_type_vis_value_};
  auto prev_league_number_vis_value{league_number_vis_value_};
  auto prev_league_rank_vis_value{league_rank_vis_value_};

  // Ok; we officially want to show the latest values we have. Mark them as
  // visible and either animate or immediately switch to them.
  league_rank_vis_value_ = league_rank_value_;
  league_type_vis_value_ = league_type_value_;
  league_number_vis_value_ = league_number_value_;

  // We don't animate league color; always just apply it immediately.
  auto color{ColorForLeagueValue_(league_type_vis_value_)};
  trophy_icon_->widget->set_color(color.x, color.y, color.z);

  // We may want to animate rank.
  if (league_rank_animating_) {
    // If there's already an animation going, do nothing. It will keep going
    // until we're showing our vis vals.
  } else {
    auto animate{true};

    // Don't animate if we're offscreen.
    if (!trophy_meter_button_->enabled) {
      animate = false;
    }

    // Don't animate if we're coming from or going to an 'empty' value.
    if (prev_league_rank_vis_value <= 0 || league_rank_vis_value_ <= 0) {
      animate = false;
    }

    // Don't animate if league type or league num is changing.
    if (prev_league_number_vis_value != league_number_vis_value_
        || prev_league_type_vis_value != league_type_vis_value_) {
      animate = false;
    }

    // Don't animate if our rank is staying the same.
    if (prev_league_rank_vis_value == league_rank_vis_value_) {
      animate = false;
    }

    if (animate) {
      // Start up an animation.
      league_rank_animating_ = true;
      league_rank_anim_start_val_ = prev_league_rank_vis_value;
      league_rank_anim_val_ = prev_league_rank_vis_value;

      league_rank_anim_start_time_ = g_base->logic->display_time();

      auto improving{league_rank_vis_value_ < league_rank_anim_start_val_};

      // Play score-increase sound only if we're improving.
      if (improving) {
        if (base::AudioSource* s = g_base->audio->SourceBeginNew()) {
          s->SetPositional(false);
          league_rank_anim_sound_play_id_ = s->Play(
              g_base->assets->SysSound(base::SysSoundID::kScoreIncrease));
          s->End();
        }
      }
    } else {
      // Just set new values immediately.
      league_rank_text_->widget->SetText(
          league_rank_vis_value_ > 0
              ? ("#" + std::to_string(league_rank_vis_value_))
              : "");
    }
  }
}

void RootWidget::SetLeagueRankValues(const std::string& league_type,
                                     int league_number, int league_rank) {
  // Store latest values and then (possibly) apply them to our display.
  league_type_value_ = league_type;
  league_number_value_ = league_number;
  league_rank_value_ = league_rank;
  UpdateLeagueRankDisplay_();
}

void RootWidget::SetInboxState(int val, bool is_max,
                               const std::string& announce_text) {
  // Store latest values and then (possibly) apply them to our display.
  inbox_count_value_ = val;
  inbox_count_is_max_value_ = is_max;
  inbox_announce_text_str_ = announce_text;

  // We update announce text immediately.
  assert(inbox_announce_text_);
  inbox_announce_text_->widget->SetText(inbox_announce_text_str_);

  // Setting a non-empty announce value flips us into animation mode so
  // we continually update flashing/etc.
  if (!inbox_announce_text_str_.empty()) {
    inbox_animating_ = true;
  }

  UpdateInboxDisplay_();
}

void RootWidget::SetAchievementPercentText(const std::string& val) {
  assert(achievement_percent_text_);
  achievement_percent_text_->widget->SetText(val);
}

void RootWidget::SetLevelText(const std::string& val) {
  assert(level_text_);
  level_text_->widget->SetText(val);
}

void RootWidget::SetXPText(const std::string& val) {
  assert(xp_text_);
  xp_text_->widget->SetText(val);
}

void RootWidget::UpdateTicketsMeterTextColor_() {
  assert(tickets_meter_text_);

  if (!have_live_values_) {
    tickets_meter_text_->widget->set_color(1.0f, 1.0f, 1.0f, 0.4f);
  } else {
    if (tickets_meter_animating_) {
      float mult{1.2f
                 + (0.5f * sinf(8.0f * 3.1415f * (last_draw_display_time_)))};
      tickets_meter_text_->widget->set_color(0.2f * mult, 1.0f * mult,
                                             0.2f * mult, 1.0f);
    } else {
      tickets_meter_text_->widget->set_color(1.0f, 1.0f, 1.0f, 1.0f);
    }
  }
}

void RootWidget::UpdateTokensMeterTextColor_() {
  if (gold_pass_ && have_live_values_) {
    tokens_meter_text_->widget->set_color(1.0f, 0.6f, 0.1f, 0.6f);
    return;
  }

  if (!have_live_values_) {
    tokens_meter_text_->widget->set_color(1.0f, 1.0f, 1.0f, 0.4f);
  } else {
    if (tokens_meter_animating_) {
      float mult{1.2f
                 + (0.5f * sinf(8.0f * 3.1415f * (last_draw_display_time_)))};
      tokens_meter_text_->widget->set_color(0.2f * mult, 1.0f * mult,
                                            0.2f * mult, 1.0f);
    } else {
      tokens_meter_text_->widget->set_color(1.0f, 1.0f, 1.0f, 1.0f);
    }
  }
}

void RootWidget::SetHaveLiveValues(bool have_live_values) {
  have_live_values_ = have_live_values;
  auto oval{have_live_values ? 1.0f : 0.4f};
  auto oval2{have_live_values ? 1.0f : 0.4f};

  assert(tickets_meter_icon_);
  tickets_meter_icon_->widget->set_opacity(oval2);
  UpdateTicketsMeterTextColor_();

  assert(tokens_meter_text_);
  assert(tokens_meter_icon_);
  UpdateTokensMeterTextColor_();
  tokens_meter_icon_->widget->set_opacity(oval2);

  assert(inbox_button_);
  inbox_button_->widget->set_opacity(oval2);

  assert(achievements_button_);
  achievements_button_->widget->set_opacity(oval2);
  assert(achievement_percent_text_);
  achievement_percent_text_->widget->set_color(1.0f, 1.0f, 1.0f, oval);

  assert(store_button_);
  store_button_->widget->set_opacity(oval2);

  assert(inventory_button_);
  inventory_button_->widget->set_opacity(oval2);

  assert(get_tokens_button_);
  get_tokens_button_->widget->set_opacity(oval2);

  assert(league_rank_text_);
  league_rank_text_->widget->set_color(1.0f, 1.0f, 1.0f, oval);

  assert(tickets_meter_button_);
  tickets_meter_button_->widget->set_opacity(oval2);

  assert(tokens_meter_button_);
  tokens_meter_button_->widget->set_opacity(oval2);

  assert(trophy_meter_button_);
  trophy_meter_button_->widget->set_opacity(oval2);

  assert(trophy_icon_);
  trophy_icon_->widget->set_opacity(oval2);

  for (auto&& chest_id : chest_ids) {
    auto&& button{chest_slots_.at(chest_id).button};
    assert(button);
    button->widget->set_opacity(have_live_values ? 1.0f : 0.5f);
  }
  assert(chest_backing_);
  chest_backing_->widget->set_opacity(have_live_values ? 1.0f : 0.5f);
}

void RootWidget::SetChests(
    const std::string& chest_0_appearance,
    const std::string& chest_1_appearance,
    const std::string& chest_2_appearance,
    const std::string& chest_3_appearance, seconds_t chest_0_create_time,
    seconds_t chest_1_create_time, seconds_t chest_2_create_time,
    seconds_t chest_3_create_time, seconds_t chest_0_unlock_time,
    seconds_t chest_1_unlock_time, seconds_t chest_2_unlock_time,
    seconds_t chest_3_unlock_time, int chest_0_unlock_tokens,
    int chest_1_unlock_tokens, int chest_2_unlock_tokens,
    int chest_3_unlock_tokens, seconds_t chest_0_ad_allow_time,
    seconds_t chest_1_ad_allow_time, seconds_t chest_2_ad_allow_time,
    seconds_t chest_3_ad_allow_time) {
  auto& chest0{chest_slots_["0"]};
  chest0.appearance = chest_0_appearance;
  chest0.create_time = chest_0_create_time;
  chest0.unlock_time = chest_0_unlock_time;
  chest0.unlock_tokens = chest_0_unlock_tokens;
  chest0.ad_allow_time = chest_0_ad_allow_time;
  chest0.live_display_dirty = true;
  // Assume no for the following until we calc otherwise.
  chest0.show_token_unlockable = false;
  chest0.needs_faster_refresh = false;

  auto& chest1{chest_slots_["1"]};
  chest1.appearance = chest_1_appearance;
  chest1.create_time = chest_1_create_time;
  chest1.unlock_time = chest_1_unlock_time;
  chest1.unlock_tokens = chest_1_unlock_tokens;
  chest1.ad_allow_time = chest_1_ad_allow_time;
  chest1.live_display_dirty = true;
  // Assume no for the following until we calc otherwise.
  chest1.show_token_unlockable = false;
  chest1.needs_faster_refresh = false;

  auto& chest2{chest_slots_["2"]};
  chest2.appearance = chest_2_appearance;
  chest2.create_time = chest_2_create_time;
  chest2.unlock_time = chest_2_unlock_time;
  chest2.unlock_tokens = chest_2_unlock_tokens;
  chest2.ad_allow_time = chest_2_ad_allow_time;
  chest2.live_display_dirty = true;
  // Assume no for the following until we calc otherwise.
  chest2.show_token_unlockable = false;
  chest2.needs_faster_refresh = false;

  auto& chest3{chest_slots_["3"]};
  chest3.appearance = chest_3_appearance;
  chest3.create_time = chest_3_create_time;
  chest3.unlock_time = chest_3_unlock_time;
  chest3.unlock_tokens = chest_3_unlock_tokens;
  chest3.ad_allow_time = chest_3_ad_allow_time;
  chest3.live_display_dirty = true;
  // Assume no for the following until we calc otherwise.
  chest3.show_token_unlockable = false;
  chest3.needs_faster_refresh = false;
}

void RootWidget::OnLanguageChange() {
  ContainerWidget::OnLanguageChange();
  translations_dirty_ = true;
}

void RootWidget::UpdateChests_() {
  // Note: For consistency, this should only be run as part of Draw().

  // Make sure we've got the latest translated strings for open times.
  if (translations_dirty_) {
    time_suffix_hours_ =
        g_base->assets->CompileResourceString(R"({"r":"timeSuffixHoursText"})");
    time_suffix_minutes_ = g_base->assets->CompileResourceString(
        R"({"r":"timeSuffixMinutesText"})");
    time_suffix_seconds_ = g_base->assets->CompileResourceString(
        R"({"r":"timeSuffixSecondsText"})");
    open_me_text_ =
        g_base->assets->CompileResourceString(R"({"r":"openMeText"})");
    translations_dirty_ = false;
  }

  // We drop the backing/slots down a bit if we have no chests.
  auto have_chests{false};

  for (auto&& chest_id : chest_ids) {
    const auto& slot{chest_slots_[chest_id]};
    if (!slot.appearance.empty()) {
      have_chests = true;
      break;
    }
  }

  auto now{g_base->TimeSinceEpochCloudSeconds()};

  // auto current_seconds_since_epoch{g_base->TimeSinceEpochCloudSeconds()};

  for (auto&& chest_id : chest_ids) {
    auto&& slot{chest_slots_[chest_id]};

    // For each slot we keep track of whether we could pay to unlock it
    // at this very moment.
    slot.show_token_unlockable = false;
    if (highlight_potential_token_purchases_ && !gold_pass_
        && !slot.appearance.empty() && slot.unlock_time > slot.create_time) {
      // How far along in timed unlock this chest is.
      float amt = std::max(
          0.0f,
          std::min(1.0f, 1.0f
                             - static_cast<float>(
                                 (now - slot.create_time)
                                 / (slot.unlock_time - slot.create_time))));
      // If we have a valid tokens value and that seems to be higher than
      // what the unlock should cost right now, assume we can unlock.
      if (tokens_meter_value_ >= 0
          && tokens_meter_value_ > ceil(slot.unlock_tokens * amt)) {
        slot.show_token_unlockable = true;
      }
    }

    // Make our live unlock time visible *unless* we've got live updates
    // paused or are in the middle of an animation.
    if (!update_pause_count_ && !slot.unlock_time_animating) {
      slot.vis_unlock_time = slot.unlock_time;
      // We're updating from live values here; can mark clean.
      slot.live_display_dirty = false;
    }

    assert(slot.button);
    assert(slot.lock_icon);
    Object::Ref<base::TextureAsset> tex;
    if (slot.appearance == "") {
      // Empty slot.
      slot.button->widget->set_color(0.473f, 0.44f, 0.583f);
      slot.button->width = slot.button->height = 80.0f;
      slot.button->y = have_chests ? 44.0f : -2.0f;
      {
        base::Assets::AssetListLock lock;
        tex = g_base->assets->GetTexture("chestIconEmpty");
      }
      slot.lock_icon->visible = false;
      slot.tv_icon->visible = false;
      slot.text->visible = false;

      slot.button->widget->SetTintTexture(nullptr);
      slot.button->widget->set_tint_color(1.0f, 1.0f, 1.0f);
      slot.button->widget->set_tint2_color(1.0f, 1.0f, 1.0f);

      slot.needs_faster_refresh = false;

    } else {
      Object::Ref<base::TextureAsset> textint;

      // Chest in slot.
      have_chests = true;
      slot.button->width = slot.button->height = 110.0f;
      slot.button->y = 44.0f;
      std::string chest_tex_closed;
      std::string chest_tex_closed_tint;
      Vector3f chest_color;
      Vector3f chest_tint;
      Vector3f chest_tint2;
      if (auto* classic = g_base->classic()) {
        classic->GetClassicChestDisplayInfo(
            slot.appearance, &chest_tex_closed, &chest_tex_closed_tint,
            &chest_color, &chest_tint, &chest_tint2);
      } else {
        chest_tex_closed = "chestIcon";
        chest_tex_closed_tint = "white";
        chest_color = Vector3f{1.0f, 1.0f, 1.0f};
        chest_tint = Vector3f{1.0f, 1.0f, 1.0f};
        chest_tint2 = Vector3f{1.0f, 1.0f, 1.0f};
      }
      {
        base::Assets::AssetListLock lock;
        tex = g_base->assets->GetTexture(chest_tex_closed);
        textint = g_base->assets->GetTexture(chest_tex_closed_tint);
      }
      slot.button->widget->set_color(chest_color.x, chest_color.y,
                                     chest_color.z);
      slot.button->widget->SetTintTexture(textint.get());
      slot.button->widget->set_tint_color(chest_tint.x, chest_tint.y,
                                          chest_tint.z);
      slot.button->widget->set_tint2_color(chest_tint2.x, chest_tint2.y,
                                           chest_tint2.z);

      auto seconds_to_unlock{
          gold_pass_ ? 0
                     : static_cast<int>(std::ceil(slot.vis_unlock_time - now))};

      // We flash when chests are showing 'open me' so need faster
      // refreshes.
      slot.needs_faster_refresh =
          (seconds_to_unlock <= 0 || slot.show_token_unlockable);

      // Set text contents and widget vis depending on whether we're
      // counting down or ready to open.
      if (seconds_to_unlock > 0) {
        // Show the ad-available tag IF the ad provides an allow-ad time
        // AND that time has passed AND we've got an ad ready to go.
        auto allow_ad{slot.ad_allow_time > 0.0 && slot.ad_allow_time <= now
                      && g_base->HavePlus()
                      && g_base->Plus()->HaveIncentivizedAd()};

        slot.lock_icon->visible = true;
        // slot.text->visible = true;
        slot.tv_icon->visible = allow_ad;

        // Special case - flash 'open me' if we have enough tokens to
        // unlock.
        if (!slot.unlock_time_animating && slot.show_token_unlockable
            && std::fmod(last_draw_display_time_, 4.0) < 2.0) {
          slot.text->widget->SetText("*" + open_me_text_);
        } else {
          slot.text->widget->SetText(
              GetTimeStr_(seconds_to_unlock, slot.unlock_time_animating));
        }

      } else {
        slot.lock_icon->visible = false;
        slot.tv_icon->visible = false;
        slot.text->widget->SetText(open_me_text_);
      }

      // Set text color based on whether we're animating, whether we can pay
      // to unlock right now, etc.
      slot.text->visible = true;
      if (slot.unlock_time_animating) {
        float mult{1.2f
                   + (0.5f * sinf(8.0f * 3.1415f * (last_chests_step_time_)))};
        slot.text->widget->set_color(0.2 * mult, 1.0 * mult, 0.2 * mult, 1.0);
      } else {
        float mult{1.0f};

        // Draw text in a teal color if we can pay to unlock and green
        // otherwise.
        if (seconds_to_unlock <= 0) {
          mult = 0.8 + 0.2 * std::abs(sin(last_draw_display_time_ * 6.0));
          slot.text->widget->set_color(kChestReadyTextColorR * mult,
                                       kChestReadyTextColorG * mult,
                                       kChestReadyTextColorB * mult, 1.0f);
        } else if (slot.show_token_unlockable) {
          mult = 0.8 + 0.2 * std::abs(sin(last_draw_display_time_ * 6.0));
          slot.text->widget->set_color(kChestCanPayTextColorR * mult,
                                       kChestCanPayTextColorG * mult,
                                       kChestCanPayTextColorB * mult, 1.0f);
        } else {
          slot.text->widget->set_color(kChestTextColorR * mult,
                                       kChestTextColorG * mult,
                                       kChestTextColorB * mult, 1.0f);
        }
      }
    }
    slot.button->widget->SetTexture(tex.get());
  }

  assert(chest_backing_);
  chest_backing_->y = have_chests ? 41.0f : -15.0f;

  child_widgets_dirty_ = true;
}

auto RootWidget::GetTimeStr_(seconds_t diff, bool animating) -> std::string {
  // NOTE: Adapted from time_display_node.cc. Not sure if it would make
  // sense to share this code somewhere?..
  std::string output;
  auto show_sub_seconds{false};

  auto t{static_cast<millisecs_t>(diff * 1000.0)};
  bool is_negative = false;
  if (t < 0) {
    t = -t;
    is_negative = true;
  }

  // Hours
  int h = static_cast_check_fit<int>(((t / 1000) / (60 * 60)));
  if (h != 0) {
    std::string s = time_suffix_hours_;
    char buffer[100];
    snprintf(buffer, sizeof(buffer), "%d", h);
    Utils::StringReplaceOne(&s, "${COUNT}", buffer);
    if (!output.empty()) {
      output += " ";
    }
    output += s;
  }

  // Minutes.
  int m = static_cast_check_fit<int>(((t / 1000) / 60) % 60);
  if (m != 0) {
    std::string s = time_suffix_minutes_;
    char buffer[100];
    snprintf(buffer, sizeof(buffer), "%d", m);
    Utils::StringReplaceOne(&s, "${COUNT}", buffer);
    if (!output.empty()) {
      output += " ";
    }
    output += s;
  }

  // Only show seconds when within a few minutes and only if we aren't
  // animating (otherwise we see animations go 3m..2m..1m 57s etc which
  // looks odd.)
  if (m < 2 && !animating) {
    if (show_sub_seconds) {
      float sec = fmod(static_cast<float>(t) / 1000.0f, 60.0f);
      if (sec >= 0.005f || output.empty()) {
        std::string s = time_suffix_seconds_;
        char buffer[100];
        snprintf(buffer, sizeof(buffer), "%.2f", sec);
        Utils::StringReplaceOne(&s, "${COUNT}", buffer);
        if (!output.empty()) {
          output += " ";
        }
        output += s;
      }
    } else {
      // Seconds (integer).
      int sec = static_cast_check_fit<int>(t / 1000 % 60);
      if (sec != 0 || output.empty()) {
        std::string s = time_suffix_seconds_;
        char buffer[100];
        snprintf(buffer, sizeof(buffer), "%d", sec);
        Utils::StringReplaceOne(&s, "${COUNT}", buffer);
        if (!output.empty()) {
          output += " ";
        }
        output += s;
      }
    }
  }
  if (is_negative) {
    output = "-" + output;
  }
  return output;
}

void RootWidget::PauseUpdates() {
  assert(g_base->InLogicThread());
  update_pause_count_ += 1;
}

void RootWidget::ResumeUpdates() {
  assert(g_base->InLogicThread());
  update_pause_count_ -= 1;
  if (update_pause_count_ < 0) {
    BA_LOG_ONCE(LogName::kBaApp, LogLevel::kError,
                "RootWidget update-pause-count < 0; should not happen.");
  }
}

void RootWidget::AnimateChestUnlockTime(const std::string& chestid,
                                        seconds_t duration,
                                        seconds_t startvalue,
                                        seconds_t endvalue) {
  assert(g_base->InLogicThread());

  auto&& chest_iter{chest_slots_.find(chestid)};
  if (chest_iter == chest_slots_.end()) {
    throw Exception("Invalid chest slot id: " + chestid, PyExcType::kValue);
  }
  auto&& chest{chest_iter->second};
  chest.unlock_time_animating = true;
  chest.unlock_time_animation_start_time = g_base->logic->display_time();
  chest.unlock_time_animation_end_time =
      chest.unlock_time_animation_start_time + duration;

  chest.unlock_time_animation_start_val = startvalue;
  chest.unlock_time_animation_end_val = endvalue;

  // Only do one of these sounds at a time; if we ever need multiple we'll
  // need multiple sound-play-ids.
  if (!chest_unlock_time_anim_sound_play_id_.has_value()) {
    if (base::AudioSource* s = g_base->audio->SourceBeginNew()) {
      s->SetPositional(false);
      chest_unlock_time_anim_sound_play_id_ =
          s->Play(g_base->assets->SysSound(base::SysSoundID::kScoreIncrease));
      s->End();
    }
  }
}

void RootWidget::AnimateTickets(seconds_t duration, int startvalue,
                                int endvalue) {
  assert(g_base->InLogicThread());

  tickets_meter_animating_ = true;
  tickets_anim_start_time_ = g_base->logic->display_time();
  tickets_anim_end_time_ = tickets_anim_start_time_ + duration;
  tickets_anim_start_value_ = startvalue;
  tickets_anim_end_value_ = endvalue;

  // Only do one of these sounds at a time; if we ever need multiple we'll
  // need multiple sound-play-ids.
  if (!tickets_anim_sound_play_id_.has_value()) {
    if (base::AudioSource* s = g_base->audio->SourceBeginNew()) {
      s->SetPositional(false);
      tickets_anim_sound_play_id_ =
          s->Play(g_base->assets->SysSound(base::SysSoundID::kScoreIncrease));
      s->End();
    }
  }
}

void RootWidget::AnimateTokens(seconds_t duration, int startvalue,
                               int endvalue) {
  assert(g_base->InLogicThread());

  tokens_meter_animating_ = true;
  tokens_anim_start_time_ = g_base->logic->display_time();
  tokens_anim_end_time_ = tokens_anim_start_time_ + duration;
  tokens_anim_start_value_ = startvalue;
  tokens_anim_end_value_ = endvalue;

  // Only do one of these sounds at a time; if we ever need multiple we'll
  // need multiple sound-play-ids.
  if (!tokens_anim_sound_play_id_.has_value()) {
    if (base::AudioSource* s = g_base->audio->SourceBeginNew()) {
      s->SetPositional(false);
      tokens_anim_sound_play_id_ =
          s->Play(g_base->assets->SysSound(base::SysSoundID::kScoreIncrease));
      s->End();
    }
  }
}

}  // namespace ballistica::ui_v1
