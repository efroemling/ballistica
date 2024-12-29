// Released under the MIT License. See LICENSE for details.

#include "ballistica/ui_v1/widget/root_widget.h"

#include <algorithm>
#include <string>
#include <vector>

#include "ballistica/base/app_mode/app_mode.h"
#include "ballistica/base/assets/assets.h"
#include "ballistica/base/graphics/renderer/render_pass.h"
#include "ballistica/base/graphics/support/frame_def.h"
#include "ballistica/base/support/context.h"
#include "ballistica/shared/buildconfig/buildconfig_common.h"
#include "ballistica/shared/foundation/inline.h"
#include "ballistica/ui_v1/python/ui_v1_python.h"
#include "ballistica/ui_v1/widget/button_widget.h"
#include "ballistica/ui_v1/widget/image_widget.h"
#include "ballistica/ui_v1/widget/stack_widget.h"

namespace ballistica::ui_v1 {

static const float kBotLeftColorR{0.6f};
static const float kBotLeftColorG{0.6f};
static const float kBotLeftColorB{0.8f};

// Flip this to true when we're ready to use levels.
static const bool kShowLevels{false};

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
}

RootWidget::~RootWidget() = default;

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

    bd.color_r = 0.4f;
    bd.color_g = 0.38f;
    bd.color_b = 0.5f;

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
    // bd.x = x - 68;
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

  // Inbox button.
  {
    ButtonDef_ b;
    b.h_align = 0.0f;
    b.v_align = VAlign_::kBottom;
    b.width = b.height = 60.0f;
    // b.x = bx;
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
    b.pre_buffer = 25.0f;
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
    b.pre_buffer = 25.0f;
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
    // b.x = bx;
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
    // bx += 70.0f;
  }

  // Settings button.
  {
    ButtonDef_ b;
    b.h_align = 0.0f;
    b.v_align = VAlign_::kBottom;
    b.width = b.height = 60.0f;
    // b.x = bx;
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
    b.pre_buffer = 25.0f;
    settings_button_ = AddButton_(b);
    bottom_left_buttons_.push_back(settings_button_);
  }

  // Chests.
  {
    float backing_r = 0.43f;
    float backing_g = 0.40f;
    float backing_b = 0.53f;
    float backing_cover_r = backing_r;
    float backing_cover_g = backing_g;
    float backing_cover_b = backing_b;
    float backing_a = 1.0f;
    backing_r *= 1.1f;
    backing_g *= 1.1f;
    backing_b *= 1.1f;
    backing_cover_r *= 1.1f;
    backing_cover_g *= 1.1f;
    backing_cover_b *= 1.1f;

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
      bd.color_r = backing_r;
      bd.color_g = backing_g;
      bd.color_b = backing_b;
      bd.opacity = backing_a;

      bd.depth_min = 0.2f;
      bd.call = UIV1Python::ObjID::kEmptyCall;
      bd.visibility_mask =
          (static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFull)
           | static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFullNoBack)
           | static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFullRoot));
      bd.allow_in_game = false;
      chest_backing_ = AddButton_(bd);
    }

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
    b.color_r = backing_cover_r;
    b.color_g = backing_cover_g;
    b.color_b = backing_cover_b;
    b.opacity = 1.0f;

    b.call = UIV1Python::ObjID::kRootUIChestSlot0PressCall;
    b.x = -1.5f * spacing;
    chest_0_button_ = AddButton_(b);

    b.call = UIV1Python::ObjID::kRootUIChestSlot1PressCall;
    b.x = -0.5f * spacing;
    chest_1_button_ = AddButton_(b);

    b.x = 0.5f * spacing;
    b.call = UIV1Python::ObjID::kRootUIChestSlot2PressCall;
    chest_2_button_ = AddButton_(b);

    b.x = 1.5f * spacing;
    b.call = UIV1Python::ObjID::kRootUIChestSlot3PressCall;
    chest_3_button_ = AddButton_(b);
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
    b.pre_buffer = 20.0f;
    b.allow_in_game = false;
    inventory_button_ = AddButton_(b);
    bottom_right_buttons_.push_back(inventory_button_);
  }

  // Store button.
  {
    ButtonDef_ b;
    b.h_align = 1.0f;
    b.v_align = VAlign_::kBottom;
    b.width = b.height = 85.0f;
    // b.x = -206.0f;
    b.y = b.height * 0.5f;
    b.img = "storeIcon";
    b.call = UIV1Python::ObjID::kRootUIStoreButtonPressCall;
    b.visibility_mask =
        (static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFull)
         | static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFullNoBack)
         | static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFullRoot));
    b.pre_buffer = 20.0f;
    b.allow_in_game = false;

    store_button_ = AddButton_(b);
    bottom_right_buttons_.push_back(store_button_);
  }

  UpdateForFocusedWindow_(nullptr);
}

void RootWidget::Draw(base::RenderPass* pass, bool transparent) {
  // Opaque pass gets drawn first; use that as an opportunity to step up our
  // motion.

  if (!transparent) {
    millisecs_t current_time = pass->frame_def()->display_time_millisecs();
    millisecs_t time_diff =
        std::min(millisecs_t{100}, current_time - update_time_);

    StepChildWidgets_(static_cast<float>(time_diff));
    update_time_ = current_time;
  }
  ContainerWidget::Draw(pass, transparent);
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
  t.widget->SetHAlign(TextWidget::HAlign::kCenter);
  t.widget->SetVAlign(TextWidget::VAlign::kCenter);
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

void RootWidget::StepChildWidgets_(float dt) {
  // Hitches tend to break our math and cause buttons to overshoot on their
  // transitions in and then back up. So let's limit our max dt to about
  // what ~30fps would give us.
  dt = std::min(dt, 1000.0f / 30.0f);

  if (!child_widgets_dirty_) {
    return;
  }

  bool is_small{g_base->ui->scale() == UIScale::kSmall};

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
    b.enabled = enable_button;
  }

  // Go through our corner button lists updating positions based on
  // what is visible.
  float xpos = 0.0f;
  for (auto* btn : top_left_buttons_) {
    auto enabled = btn->enabled;
    float bwidthhalf = btn->width * 0.5;
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
    b.x_smoothed += (b.x_target - b.x_smoothed) * 0.015f * dt;
    b.y_smoothed += (b.y_target - b.y_smoothed) * 0.015f * dt;

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
  switch (g_base->ui->scale()) {
    case UIScale::kLarge:
      base_scale_ = 0.6f;
      break;
    case UIScale::kMedium:
      base_scale_ = 0.8f;
      break;
    default:
      base_scale_ = 1.0f;
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
  StepChildWidgets_(0.0f);
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
    return chest_0_button_->widget.get();
  } else if (s == "chest_1_button") {
    return chest_1_button_->widget.get();
  } else if (s == "chest_2_button") {
    return chest_2_button_->widget.get();
  } else if (s == "chest_3_button") {
    return chest_3_button_->widget.get();
  }
  return nullptr;
}

void RootWidget::SetAccountState(bool signed_in, const std::string& name) {
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

void RootWidget::SetTicketsMeterText(const std::string& val) {
  assert(tickets_meter_text_);
  tickets_meter_text_->widget->SetText(val);
}

void RootWidget::SetTokensMeterText(const std::string& val, bool gold_pass) {
  assert(tokens_meter_text_);
  assert(get_tokens_button_);
  if (gold_pass) {
    get_tokens_button_->force_hide = true;

    // Use the infinity symbol if we have full unicode support.
    tokens_meter_text_->widget->SetText(
        g_buildconfig.enable_os_font_rendering() ? "\xE2\x88\x9E" : "inf");
    tokens_meter_text_->widget->set_color(1.0f, 0.6f, 0.1f, 0.6f);
  } else {
    get_tokens_button_->force_hide = false;
    tokens_meter_text_->widget->SetText(val);
    tokens_meter_text_->widget->set_color(1.0f, 1.0f, 1.0f, 1.0f);
  }
  // May need to animate in/out.
  child_widgets_dirty_ = true;
}

void RootWidget::SetLeagueRankText(const std::string& val) {
  assert(league_rank_text_);
  league_rank_text_->widget->SetText(val);
}

void RootWidget::SetLeagueType(const std::string& val) {
  Vector3f color{};

  if (val == "") {
    color = {0.4f, 0.4f, 0.4f};
  } else if (val == "b") {
    color = {1.0f, 0.7f, 0.5f};
  } else if (val == "s") {
    color = {1.0f, 1.0f, 1.4f};
  } else if (val == "g") {
    color = {1.4f, 1.0f, 0.4f};
  } else if (val == "d") {
    color = {1.0f, 0.8f, 2.0f};
  } else {
    g_core->Log(LogName::kBa, LogLevel::kError,
                "RootWidget: Invalid league type '" + val + "'.");
  }
  assert(trophy_icon_);
  trophy_icon_->widget->set_color(color.x, color.y, color.z);
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

void RootWidget::SetHaveLiveValues(bool have_live_values) {
  // auto cval{have_live_values ? 1.0f : 0.4f};
  auto oval{have_live_values ? 1.0f : 0.4f};
  auto oval2{have_live_values ? 1.0f : 0.4f};

  assert(tickets_meter_text_);
  assert(tickets_meter_icon_);
  tickets_meter_text_->widget->set_color(1.0f, 1.0f, 1.0f, oval);
  // tickets_meter_icon_->widget->set_color(cval, cval, cval);
  tickets_meter_icon_->widget->set_opacity(oval2);

  assert(tokens_meter_text_);
  assert(tokens_meter_icon_);
  tokens_meter_text_->widget->set_color(1.0f, 1.0f, 1.0f, oval);
  // tokens_meter_icon_->widget->set_color(cval, cval, cval);
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

  for (auto* button :
       {chest_0_button_, chest_1_button_, chest_2_button_, chest_3_button_}) {
    assert(button);
    button->widget->set_opacity(have_live_values ? 1.0f : 0.5f);
  }
  assert(chest_backing_);
  chest_backing_->widget->set_opacity(have_live_values ? 1.0f : 0.5f);
}

void RootWidget::SetChests(const std::string& chest_0_appearance,
                           const std::string& chest_1_appearance,
                           const std::string& chest_2_appearance,
                           const std::string& chest_3_appearance) {
  std::vector<std::pair<const std::string&, Button_*>> pairs = {
      {chest_0_appearance, chest_0_button_},
      {chest_1_appearance, chest_1_button_},
      {chest_2_appearance, chest_2_button_},
      {chest_3_appearance, chest_3_button_},
  };

  auto have_chests{false};
  for (const auto& [appearance, b] : pairs) {
    if (appearance != "") {
      have_chests = true;
    }
  }

  for (const auto& [appearance, b] : pairs) {
    assert(b);
    if (appearance == "") {
      b->widget->set_color(0.473f, 0.44f, 0.583f);
      b->width = b->height = 80.0f;
      b->y = have_chests ? 44.0f : -2.0f;
      {
        base::Assets::AssetListLock lock;
        b->widget->SetTexture(
            g_base->assets->GetTexture("chestIconEmpty").get());
      }
    } else {
      have_chests = true;
      b->widget->set_color(1.0f, 1.0f, 1.0f);
      b->width = b->height = 110.0f;
      b->y = 44.0f;
      {
        base::Assets::AssetListLock lock;
        b->widget->SetTexture(g_base->assets->GetTexture("chestIcon").get());
      }
    }
  }
  assert(chest_backing_);
  chest_backing_->y = have_chests ? 41.0f : -15.0f;

  child_widgets_dirty_ = true;
}

void RootWidget::SetInboxCountText(const std::string& val) {
  assert(inbox_count_text_);

  inbox_count_text_->widget->SetText(val);

  auto backing_was_visible{inbox_count_backing_->visible};
  auto backing_is_visible = (val != "" && val != "0");

  if (backing_was_visible != backing_is_visible) {
    inbox_count_backing_->visible = backing_is_visible;
    inbox_count_text_->visible = backing_is_visible;
    child_widgets_dirty_ = true;
  }
}

}  // namespace ballistica::ui_v1
