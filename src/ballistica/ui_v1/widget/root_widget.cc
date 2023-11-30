// Released under the MIT License. See LICENSE for details.

#include "ballistica/ui_v1/widget/root_widget.h"

#include "ballistica/base/app_mode/app_mode.h"
#include "ballistica/base/graphics/renderer/renderer.h"
#include "ballistica/ui_v1/python/ui_v1_python.h"
#include "ballistica/ui_v1/widget/button_widget.h"
#include "ballistica/ui_v1/widget/stack_widget.h"

namespace ballistica::ui_v1 {

// color we mult toolbars by in medium and large ui modes
// (in small mode we keep them more the normal window color since everything
// overlaps)
#define TOOLBAR_COLOR_R 0.75f
#define TOOLBAR_COLOR_G 0.85f
#define TOOLBAR_COLOR_B 0.85f

#define TOOLBAR_BACK_COLOR_R 0.8f
#define TOOLBAR_BACK_COLOR_G 0.8f
#define TOOLBAR_BACK_COLOR_B 0.8f

// opacity in med/large
#define TOOLBAR_OPACITY 1.0f

// opacity in small
#define TOOLBAR_OPACITY_2 1.0f

#define BOT_LEFT_COLOR_R 0.6
#define BOT_LEFT_COLOR_G 0.6
#define BOT_LEFT_COLOR_B 0.8

// for defining toolbar buttons.
struct RootWidget::ButtonDef {
  float h_align{};
  VAlign v_align{VAlign::kTop};
  float x{};
  float y{};
  float width{100.0f};
  float height{30.0f};
  float scale{1.0f};
  float depth_min{};
  float depth_max{1.0f};
  std::string label;
  std::string img;
  std::string mesh_transparent;
  std::string mesh_opaque;
  UIV1Python::ObjID call{UIV1Python::ObjID::kEmptyCall};
  float color_r{1.0f};
  float color_g{1.0f};
  float color_b{1.0f};
  float opacity{1.0f};
  bool selectable{true};
  uint32_t visibility_mask{};
};

struct RootWidget::Button {
  Object::Ref<ButtonWidget> widget;
  float h_align{};
  VAlign v_align{VAlign::kTop};
  float x{};           // user provided x
  float y{};           // user provided y
  float x_target{};    // final target x (accounting for visibility, etc)
  float y_target{};    // final target y (accounting for visibility, etc)
  float x_smoothed{};  // current x (on way to target)
  float y_smoothed{};  // current y (on way to target)
  float width{100.0f};
  float height{30.0f};
  float scale{1.0f};
  bool selectable{true};
  uint32_t visibility_mask{};
};

// for adding text label decorations to buttons
struct RootWidget::TextDef {
  Button* button = nullptr;
  float x = 0.0f;
  float y = 0.0f;
  float width = -1.0f;
  float scale = 1.0f;
  float depth_min = 0.0f;
  float depth_max = 1.0f;
  float color_r = 1.0f;
  float color_g = 1.0f;
  float color_b = 1.0f;
  float color_a = 1.0f;
  float flatness = 0.5f;
  float shadow = 0.5f;
  std::string text;
};

struct RootWidget::Text {
  Button* button{};
  Object::Ref<TextWidget> widget;
  float x{};
  float y{};
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

auto RootWidget::AddCover(float h_align, VAlign v_align, float x, float y,
                          float w, float h, float o) -> RootWidget::Button* {
  // Currently just not doing these in vr mode.
  if (g_core->vr_mode()) {
    return nullptr;
  }

  ButtonDef bd;
  bd.h_align = h_align;
  bd.v_align = v_align;
  bd.width = w;
  bd.height = h;
  bd.x = x;
  bd.y = y;
  bd.img = "softRect";
  bd.selectable = false;
  bd.color_r = 0.0f;
  bd.color_g = 0.0f;
  bd.color_b = 0.0f;
  bd.opacity = o;
  bd.call = UIV1Python::ObjID::kEmptyCall;

  bd.visibility_mask =
      static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFullRoot);
  // When the user specifies no backing it means they intend to cover the
  // screen with a flat-ish window texture.. however this only applies to
  // phone-size; for other sizes we always draw a backing.
  if (g_base->ui->scale() != UIScale::kSmall) {
    bd.visibility_mask |=
        static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFull);
  }

  Button* b = AddButton(bd);
  return b;
}

#pragma clang diagnostic push
#pragma ide diagnostic ignored "ConstantParameter"

void RootWidget::AddMeter(float h_align, float x, int type, float r, float g,
                          float b, bool plus, const std::string& s) {
  float yoffs = (g_base->ui->scale() == UIScale::kSmall) ? 0.0f : -7.0f;

  float width = type == 1 ? 80.0f : 110.0f;
  // bar
  {
    ButtonDef bd;
    bd.h_align = h_align;
    bd.v_align = VAlign::kTop;
    bd.width = width;
    bd.height = 36.0f;
    bd.x = x;
    bd.y = -36.0f + 10.0f + yoffs;
    bd.img = "uiAtlas2";
    bd.mesh_transparent = "currencyMeter";
    bd.selectable = false;
    bd.color_r = 0.32f;
    bd.color_g = 0.30f;
    bd.color_b = 0.4f;
    if (g_base->ui->scale() != UIScale::kSmall) {
      bd.color_r *= TOOLBAR_COLOR_R;
      bd.color_g *= TOOLBAR_COLOR_G;
      bd.color_b *= TOOLBAR_COLOR_B;
    }
    bd.depth_min = 0.3f;
    bd.call = UIV1Python::ObjID::kEmptyCall;
    bd.visibility_mask =
        (static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFull)
         | static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFullRoot));

    // show in currency mode
    if (type == 2 || type == 3) {
      bd.visibility_mask |=
          static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuCurrency);
    }
    Button* btn = AddButton(bd);

    // Bar value text.
    {
      TextDef td;
      td.button = btn;
      td.width = bd.width * 0.7f;
      td.text = s;
      td.scale = 0.8f;
      td.flatness = 1.0f;
      td.shadow = 1.0f;
      td.depth_min = 0.3f;
      AddText(td);
    }
  }
  // Icon on left.
  {
    ButtonDef bd;
    bd.h_align = h_align;
    bd.v_align = VAlign::kTop;
    bd.width = bd.height = 50.0f;
    if (type == 0 || type == 1) {
      bd.x = x - width * 0.5f - 10.0f;
    } else {
      bd.x = x + width * 0.5f + 10.0f;
    }
    bd.y = -32.0f + 7.0f + yoffs;
    bd.color_r = r;
    bd.color_g = g;
    bd.color_b = b;
    bd.depth_min = 0.3f;
    switch (type) {
      case 0:
        bd.img = "levelIcon";
        bd.call = UIV1Python::ObjID::kLevelIconPressCall;
        break;
      case 1:
        bd.img = "trophy";
        bd.call = UIV1Python::ObjID::kTrophyIconPressCall;
        break;
      case 2:
        bd.img = "coin";
        bd.call = UIV1Python::ObjID::kCoinIconPressCall;
        break;
      case 3:
        bd.img = "tickets";
        bd.call = UIV1Python::ObjID::kTicketIconPressCall;
        break;

#pragma clang diagnostic push
#pragma ide diagnostic ignored "UnreachableCode"
      default:
        break;
#pragma clang diagnostic pop
    }
    bd.visibility_mask =
        (static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFull)
         | static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFullRoot));
    // show in currency mode
    if (type == 2 || type == 3) {
      bd.visibility_mask |=
          static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuCurrency);
    }
    Button* btn = AddButton(bd);
    switch (type) {  // NOLINT
      case 3:
        tickets_info_button_ = btn;
        break;
      default:
        break;
    }

    // Level num.
    if (type == 0) {
      TextDef td;
      td.button = btn;
      td.width = bd.width * 0.8f;
      td.text = "12";
      td.x = -1.6f;
      td.y = 0.8f;
      td.scale = 0.9f;
      td.flatness = 1.0f;
      td.shadow = 1.0f;
      td.depth_min = 0.3f;
      td.color_r = 1.0f;
      td.color_g = 1.0f;
      td.color_b = 1.0f;
      AddText(td);
    }
  }
  // plus button
  if (plus) {
    ButtonDef bd;
    bd.h_align = h_align;
    bd.v_align = VAlign::kTop;
    bd.width = bd.height = 45.0f;
    // bd.x = x + 72;
    bd.x = x - 68;
    bd.y = -36.0f + 11.0f + yoffs;
    bd.img = "uiAtlas2";
    bd.mesh_transparent = "currencyPlusButton";
    bd.color_r = 0.35f;
    bd.color_g = 0.35f;
    bd.color_b = 0.55f;
    if (g_base->ui->scale() != UIScale::kSmall) {
      bd.color_r *= TOOLBAR_COLOR_R;
      bd.color_g *= TOOLBAR_COLOR_G;
      bd.color_b *= TOOLBAR_COLOR_B;
    }
    bd.depth_min = 0.3f;
    bd.call = UIV1Python::ObjID::kEmptyCall;
    bd.visibility_mask =
        (static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFull)
         | static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFullRoot));

    // Show in currency mode.
    if (type == 2 || type == 3) {
      bd.visibility_mask |=
          static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuCurrency);
    }
    Button* btn = AddButton(bd);
    if (type == 3) {
      tickets_plus_button_ = btn;
    }
  }
}

#pragma clang diagnostic pop

void RootWidget::Setup() {
  if (!explicit_bool(BA_UI_V1_TOOLBAR_TEST)) {
    return;
  }

  // back button
  {
    ButtonDef bd;
    bd.h_align = 0.0f;
    bd.v_align = VAlign::kTop;
    bd.width = bd.height = 140.0f;
    bd.color_r = 0.7f;
    bd.color_g = 0.4f;
    bd.color_b = 0.35f;

    bd.x = 40.0f;
    bd.y = -40.0f;
    bd.img = "nub";
    bd.call = UIV1Python::ObjID::kBackButtonPressCall;
    bd.visibility_mask =
        (static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuMinimal)
         | static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFull));
    Button* b = back_button_ = AddButton(bd);

    // clan
    {
      TextDef td;
      td.button = b;
      td.x = 5.0f;
      td.y = 3.0f;
      td.width = bd.width * 0.9f;
      td.text = g_base->assets->CharStr(SpecialChar::kBack);
      td.color_a = 1.0f;
      td.scale = 2.0f;
      td.flatness = 0.0f;
      td.shadow = 0.5f;
      AddText(td);
    }
  }

  // Widen this a bit in small mode so it just covers most of the top
  // - that looks funny in medium/large mode though
  // if (g_ui->scale() == UIScale::kSmall) {
  //   AddCover(0.5f, VAlign::kTop, 0.0f, 320.0f,
  //             g_ui->scale() == UIScale::kSmall ? 1000.0f :
  //             1000.0f, 800.0f, 0.4f);
  // }
  // if (c) {
  //   c->visibility_mask |=
  //   static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuCurrency);
  // }

  // top bar backing (currency only)
  if (explicit_bool(false)) {
    ButtonDef bd;
    bd.h_align = 0.5f;
    bd.v_align = VAlign::kTop;
    bd.width = 370.0f;
    // if (g_ui->scale() != UIScale::kSmall) {
    //   bd.width = 950.0f;
    // }
    bd.height = 90.0f;
    bd.x = 256.0f;
    bd.y = -20.0f;
    bd.img = "uiAtlas2";
    // if (g_ui->scale() != UIScale::kSmall) {
    //   bd.mesh_transparent = "toolbarBackingTop";
    // } else {
    bd.mesh_transparent = "toolbarBackingTop2";
    // }
    bd.selectable = false;
    bd.color_r = 0.44f;
    bd.color_g = 0.41f;
    bd.color_b = 0.56f;
    bd.opacity = 1.0f;
    // if (g_ui->scale() != UIScale::kSmall) {
    //   bd.color_r *= TOOLBAR_COLOR_R;
    //   bd.color_g *= TOOLBAR_COLOR_G;
    //   bd.color_b *= TOOLBAR_COLOR_B;
    //   bd.opacity *= TOOLBAR_OPACITY;
    // } else {
    //   bd.opacity *= TOOLBAR_OPACITY_2;
    // }
    bd.depth_min = 0.2f;
    // bd.call = "";
    bd.call = UIV1Python::ObjID::kEmptyCall;

    // bd.visibility_mask =
    // static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFullRoot);
    // bd.visibility_mask |=
    // static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFull);
    bd.visibility_mask |=
        static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuCurrency);
    AddButton(bd);
  }

  // top bar backing
  if (explicit_bool(false)) {
    ButtonDef bd;
    bd.h_align = 0.5f;
    bd.v_align = VAlign::kTop;
    bd.width = 850.0f;
    if (g_base->ui->scale() != UIScale::kSmall) {
      bd.width = 850.0f;
    }
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
    if (g_base->ui->scale() != UIScale::kSmall) {
      bd.color_r *= TOOLBAR_COLOR_R * TOOLBAR_BACK_COLOR_R;
      bd.color_g *= TOOLBAR_COLOR_G * TOOLBAR_BACK_COLOR_G;
      bd.color_b *= TOOLBAR_COLOR_B * TOOLBAR_BACK_COLOR_B;
      bd.opacity *= TOOLBAR_OPACITY;
    } else {
      bd.opacity *= TOOLBAR_OPACITY_2;
    }
    bd.depth_min = 0.2f;
    // bd.call = "";
    bd.call = UIV1Python::ObjID::kEmptyCall;
    bd.visibility_mask =
        static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFullRoot);
    bd.visibility_mask |=
        static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFull);
    // bd.visibility_mask |=
    // static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuCurrency);
    AddButton(bd);
  }

  float yoffs = (g_base->ui->scale() == UIScale::kSmall) ? 0.0f : -10.0f;

  // account button
  {
    ButtonDef bd;
    bd.h_align = 0.1f;
    bd.v_align = VAlign::kTop;
    bd.width = 160.0f;
    bd.height = 60.0f;
    bd.depth_min = 0.3f;
    bd.x = (g_base->ui->scale() == UIScale::kSmall) ? 100.0f : -50.0f;
    bd.y = -24.0f + yoffs;
    bd.color_r = 0.56f;
    bd.color_g = 0.5f;
    bd.color_b = 0.73f;
    if (g_base->ui->scale() != UIScale::kSmall) {
      bd.color_r *= TOOLBAR_COLOR_R;
      bd.color_g *= TOOLBAR_COLOR_G;
      bd.color_b *= TOOLBAR_COLOR_B;
    }
    // bd.call = "";
    bd.call = UIV1Python::ObjID::kEmptyCall;
    bd.visibility_mask =
        (static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFull)
         | static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFullRoot));

    // on desktop, stick this in the top left corner
    // if (g_ui->scale() == UIScale::kLarge) {
    //   bd.h_align = 0.0f;
    //   bd.x = 120.0f;
    // }

    Button* b = account_button_ = AddButton(bd);

    // player name
    {
      TextDef td;
      td.button = b;
      td.y = 9.0f;
      td.width = bd.width * 0.9f;
      td.text = "Player Name";
      td.scale = 1.2f;
      td.depth_min = 0.3f;
      td.color_r = 0.5f;
      td.color_g = 0.8f;
      td.color_b = 0.8f;
      td.shadow = 1.0f;
      AddText(td);
    }
    // clan
    {
      TextDef td;
      td.button = b;
      td.y = -12.0f;
      td.width = bd.width * 0.9f;
      td.depth_min = 0.3f;
      td.text = "Clan Name";
      td.color_a = 0.6f;
      td.scale = 0.6f;
      td.flatness = 1.0f;
      td.shadow = 0.0f;
      AddText(td);
    }
  }

  float anchorx = (g_base->ui->scale() == UIScale::kSmall) ? 0.3f : 0.25f;

  AddMeter(anchorx, 200.0f - 148.0f, 0, 1.0f, 1.0f, 1.0f, false, "456/1000");
  AddMeter(anchorx, 200.0f, 1, 1.0f, 1.0f, 1.0f, false, "123");

  AddMeter(0.7f, -100.0f, 2, 1.0f, 1.0f, 1.0f, true, "12343");
  AddMeter(0.7f, -100.0f + 188.0f, 3, 1.0f, 1.0f, 1.0f, true, "123");

  // party button
  {
    ButtonDef b;
    b.h_align = 1.0f;
    b.v_align = VAlign::kTop;
    b.width = b.height = 70.0f;
    b.x = -110.0f;
    b.y = b.height * -0.41f;
    b.img = "usersButton";
    b.call = UIV1Python::ObjID::kFriendsButtonPressCall;
    b.visibility_mask =
        (static_cast<uint32_t>(Widget::ToolbarVisibility::kInGame)
         | static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuMinimal)
         | static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuMinimalNoBack)
         | static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuCurrency)
         | static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFull)
         | static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFullRoot));
    party_button_ = AddButton(b);
  }

  // menu button (only shows up when we're not in a menu)
  // FIXME - this should never be visible on TV or VR UI modes
  {
    ButtonDef b;
    b.h_align = 1.0f;
    b.v_align = VAlign::kTop;
    b.width = b.height = 65.0f;
    b.x = -36.0f;
    b.y = b.height * -0.48f;
    b.img = "menuButton";
    b.call = UIV1Python::ObjID::kBackButtonPressCall;
    b.color_r = 0.3f;
    b.color_g = 0.5f;
    b.color_b = 0.2f;
    b.visibility_mask =
        (static_cast<uint32_t>(Widget::ToolbarVisibility::kInGame)
         | static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuMinimal)
         | static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuMinimalNoBack)
         | static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuCurrency)
         | static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFull)
         | static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFullRoot));
    menu_button_ = AddButton(b);
  }

  // bot-left cover
  // AddCover(0.0f, VAlign::kBottom, 0.0f, -210.0f, 600.0f, 600.0f, 0.25f);

  float bx = 45.0f;

  // log button
  {
    ButtonDef b;
    b.h_align = 0.0f;
    b.v_align = VAlign::kBottom;
    b.width = b.height = 50.0f;
    b.x = bx;
    b.y = b.height * 0.5f + 5;
    b.color_r = BOT_LEFT_COLOR_R;
    b.color_g = BOT_LEFT_COLOR_G;
    b.color_b = BOT_LEFT_COLOR_B;
    b.img = "logIcon";
    b.visibility_mask =
        (static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFull)
         | static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFullRoot));
    AddButton(b);
  }

  bx += 70.0f;

  // achievements button
  {
    ButtonDef b;
    b.h_align = 0.0f;
    b.v_align = VAlign::kBottom;
    b.width = b.height = 50.0f;
    b.x = bx;
    b.y = b.height * 0.5f + 5;
    b.color_r = BOT_LEFT_COLOR_R;
    b.color_g = BOT_LEFT_COLOR_G;
    b.color_b = BOT_LEFT_COLOR_B;
    b.img = "achievementsIcon";
    b.visibility_mask =
        (static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFull)
         | static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFullRoot));
    AddButton(b);
  }

  bx += 70.0f;

  // leaderboards button
  {
    ButtonDef b;
    b.h_align = 0.0f;
    b.v_align = VAlign::kBottom;
    b.width = b.height = 50.0f;
    b.x = bx;
    b.y = b.height * 0.5f + 5;
    b.color_r = BOT_LEFT_COLOR_R;
    b.color_g = BOT_LEFT_COLOR_G;
    b.color_b = BOT_LEFT_COLOR_B;
    b.img = "leaderboardsIcon";
    b.visibility_mask =
        (static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFull)
         | static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFullRoot));
    AddButton(b);
  }

  bx += 70.0f;

  // settings button
  {
    ButtonDef b;
    b.h_align = 0.0f;
    b.v_align = VAlign::kBottom;
    b.width = b.height = 50.0f;
    b.x = bx;
    b.y = b.height * 0.58f;
    b.color_r = BOT_LEFT_COLOR_R;
    b.color_g = BOT_LEFT_COLOR_G;
    b.color_b = BOT_LEFT_COLOR_B;
    b.img = "settingsIcon";
    b.visibility_mask =
        (static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFull)
         | static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFullRoot));
    settings_button_ = AddButton(b);
  }

  // chests
  {
    // AddCover(0.5f, VAlign::kBottom, 0.0f, -180.0f, 600.0f, 550.0f, 0.35f);

    float backingR = 0.44f;
    float backingG = 0.41f;
    float backingB = 0.56f;
    float backingCoverR = backingR;
    float backingCoverG = backingG;
    float backingCoverB = backingB;
    float backingA = 1.0f;
    if (g_base->ui->scale() != UIScale::kSmall) {
      backingR *= TOOLBAR_COLOR_R * TOOLBAR_BACK_COLOR_R;
      backingG *= TOOLBAR_COLOR_G * TOOLBAR_BACK_COLOR_G;
      backingB *= TOOLBAR_COLOR_B * TOOLBAR_BACK_COLOR_B;
      backingCoverR *= TOOLBAR_COLOR_R;
      backingCoverG *= TOOLBAR_COLOR_G;
      backingCoverB *= TOOLBAR_COLOR_B;
      backingA *= TOOLBAR_OPACITY;
    } else {
      backingR *= 1.1f;
      backingG *= 1.1f;
      backingB *= 1.1f;
      backingCoverR *= 1.1f;
      backingCoverG *= 1.1f;
      backingCoverB *= 1.1f;
      backingA *= TOOLBAR_OPACITY_2;
    }

    // bar backing
    {
      ButtonDef bd;
      bd.h_align = 0.5f;
      bd.v_align = VAlign::kBottom;
      bd.width = 550.0f;
      bd.height = 110.0f;
      bd.x = 0.0f;
      bd.y = 41.0f;
      bd.img = "uiAtlas2";
      bd.mesh_transparent = "toolbarBackingBottom2";
      bd.selectable = false;
      bd.color_r = backingR;
      bd.color_g = backingG;
      bd.color_b = backingB;
      bd.opacity = backingA;

      bd.depth_min = 0.2f;
      // bd.call = "";
      bd.call = UIV1Python::ObjID::kEmptyCall;
      bd.visibility_mask =
          static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFullRoot);
      bd.visibility_mask |=
          static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFull);

      AddButton(bd);
    }

    ButtonDef b;
    b.h_align = 0.5f;
    b.v_align = VAlign::kBottom;
    b.width = b.height = 110.0f;
    b.x = 0.0f;
    b.y = b.height * 0.4f;
    b.img = "chestIcon";
    b.depth_min = 0.3f;
    b.visibility_mask =
        (static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFull)
         | static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFullRoot));
    float spacing = 110.0f;
    b.x = -2.0f * spacing;
    AddButton(b);

    b.x = -1.0f * spacing;
    b.img = "chestOpenIcon";
    b.y = b.height * 0.5f;
    AddButton(b);

    // test - empty icons
    b.y = b.height * 0.4f;
    b.x = 0.0f;
    b.img = "chestIconEmpty";
    b.width = b.height = 80.0f;
    b.color_r = backingCoverR;
    b.color_g = backingCoverG;
    b.color_b = backingCoverB;
    b.opacity = 1.0f;
    AddButton(b);
    b.x = 1.0f * spacing;
    AddButton(b);
    b.x = 2.0f * spacing;

    // test - multi-icon tile
    b.img = "chestIconMulti";
    AddButton(b);
  }

  // bot-right cover
  // AddCover(1.0f, VAlign::kBottom, 0.0f, -210.0f, 600.0f, 600.0f, 0.25f);

  // // settings button
  // {
  //   ButtonDef b;
  //   b.h_align = 1.0f;
  //   b.v_align = VAlign::kBottom;
  //   b.width = b.height = 50.0f;
  //   b.x = -225.0f;
  //   b.y = b.height * 0.5f + 10;
  //   b.img = "settingsIcon";
  //   b.visibility_mask =
  //   (static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFull)
  //                       |
  //                       static_cast<int>(Widget::ToolbarVisibility::kMenuFullRoot));
  //   AddButton(b);
  // }

  // store button
  {
    ButtonDef b;
    b.h_align = 1.0f;
    b.v_align = VAlign::kBottom;
    b.width = b.height = 85.0f;
    b.x = -206.0f;
    b.y = b.height * 0.5f;
    b.img = "storeIcon";
    b.visibility_mask =
        (static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFull)
         | static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFullRoot));
    AddButton(b);
  }

  // inventory button
  {
    ButtonDef b;
    b.h_align = 1.0f;
    b.v_align = VAlign::kBottom;
    b.width = b.height = 135.0f;
    b.x = -80.0f;
    b.y = b.height * 0.45f;
    b.img = "inventoryIcon";
    b.visibility_mask =
        (static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFull)
         | static_cast<uint32_t>(Widget::ToolbarVisibility::kMenuFullRoot));
    AddButton(b);
  }

  UpdateForFocusedWindow(nullptr);
}

void RootWidget::Draw(base::RenderPass* pass, bool transparent) {
  // Opaque pass gets drawn first; use that as an opportunity to step up our
  // motion.
  if (!transparent) {
    millisecs_t current_time = pass->frame_def()->display_time_millisecs();
    millisecs_t time_diff =
        std::min(millisecs_t{100}, current_time - update_time_);
    StepPositions(static_cast<float>(time_diff));
    update_time_ = current_time;
  }
  ContainerWidget::Draw(pass, transparent);
}

auto RootWidget::AddButton(const ButtonDef& def) -> RootWidget::Button* {
  base::ScopedSetContext ssc(nullptr);
  buttons_.emplace_back();
  Button& b(buttons_.back());
  b.x = b.x_smoothed = b.x_target = def.x;
  b.y = b.y_smoothed = b.y_target = def.y;
  b.visibility_mask = def.visibility_mask;
  b.scale = def.scale;
  b.width = def.width;
  b.height = def.height;
  b.h_align = def.h_align;
  b.v_align = def.v_align;
  b.selectable = def.selectable;
  b.widget = Object::New<ButtonWidget>();
  b.widget->SetColor(def.color_r, def.color_g, def.color_b);
  b.widget->set_opacity(def.opacity);
  b.widget->set_auto_select(true);
  b.widget->set_text(def.label);
  b.widget->set_enabled(def.selectable);
  b.widget->set_selectable(def.selectable);
  b.widget->SetDepthRange(def.depth_min, def.depth_max);

  // Make sure up/down moves focus into the main stack.
  assert(screen_stack_widget_ != nullptr);
  assert(b.v_align != VAlign::kCenter);
  if (b.v_align == VAlign::kTop) {
    b.widget->set_down_widget(screen_stack_widget_);
  } else {
    b.widget->set_up_widget(screen_stack_widget_);
  }
  // We wanna prevent anyone from redirecting these to point to outside
  // widgets since we'll probably outlive those outside widgets.
  b.widget->set_neighbors_locked(true);

  if (!def.img.empty()) {
    b.widget->SetTexture(g_base->assets->GetTexture(def.img).Get());
  }
  if (!def.mesh_transparent.empty()) {
    b.widget->SetMeshTransparent(
        g_base->assets->GetMesh(def.mesh_transparent).Get());
  }
  if (!def.mesh_opaque.empty()) {
    b.widget->SetMeshOpaque(g_base->assets->GetMesh(def.mesh_opaque).Get());
  }
  if (def.call != UIV1Python::ObjID::kEmptyCall) {
    b.widget->set_on_activate_call(g_ui_v1->python->objs().Get(def.call).Get());
  }
  AddWidget(b.widget.Get());
  return &b;
}

auto RootWidget::AddText(const TextDef& def) -> RootWidget::Text* {
  base::ScopedSetContext ssc(nullptr);
  texts_.emplace_back();
  Text& t(texts_.back());
  t.button = def.button;
  t.widget = Object::New<TextWidget>();
  t.widget->SetWidth(0.0f);
  t.widget->SetHeight(0.0f);
  t.widget->set_halign(TextWidget::HAlign::kCenter);
  t.widget->set_valign(TextWidget::VAlign::kCenter);
  t.widget->SetText(def.text);
  t.widget->set_max_width(def.width);
  t.widget->set_center_scale(def.scale);
  t.widget->set_color(def.color_r, def.color_g, def.color_b, def.color_a);
  t.widget->set_shadow(def.shadow);
  t.widget->set_flatness(def.flatness);
  t.widget->SetDepthRange(def.depth_min, def.depth_max);
  assert(def.button->widget.Exists());
  t.widget->set_draw_control_parent(def.button->widget.Get());
  t.x = def.x;
  t.y = def.y;
  AddWidget(t.widget.Get());
  return &t;
}

void RootWidget::UpdateForFocusedWindow() {
  UpdateForFocusedWindow(
      screen_stack_widget_ != nullptr
          ? screen_stack_widget_->GetTopmostToolbarInfluencingWidget()
          : nullptr);
}

void RootWidget::UpdateForFocusedWindow(Widget* widget) {
  // Take note if the current session is the main menu; we do a few things
  // differently there.
  in_main_menu_ = g_base->app_mode()->InClassicMainMenuSession();

  if (widget == nullptr) {
    toolbar_visibility_ = ToolbarVisibility::kInGame;
  } else {
    toolbar_visibility_ = widget->toolbar_visibility();
  }
  MarkForUpdate();
}

void RootWidget::StepPositions(float dt) {
  if (!positions_dirty_) {
    return;
  }

  // Go through our buttons updating their target points and smooth values.
  // If everything has arrived at its target point, mark us as not dirty.
  bool have_dirty = false;
  for (Button& b : buttons_) {
    // Update our target position.
    b.x_target = b.x;
    b.y_target = b.y;
    float disable_offset =
        110.0f * ((b.v_align == VAlign::kTop) ? 1.0f : -1.0f);
    // float top_right_offset = 100.0f;

    // Can turn this down to debug visibility.
    if (explicit_bool(false)) {
      disable_offset *= 0.5f;
      // top_right_offset *= 0.5f;
    }
    bool enable_button =
        static_cast<bool>(static_cast<uint32_t>(toolbar_visibility_)
                          & static_cast<uint32_t>(b.visibility_mask));

    // When we're in the main menu, always disable the menu button and shift
    // the party button a bit to the right
    if (in_main_menu_) {
      if (&b == menu_button_) {
        enable_button = false;
      }
      if (&b == party_button_) {
        b.x_target += 70.0f;
      }
    }
    if (&b == back_button_) {
      // Back button is always disabled in medium/large UI.
      if (g_base->ui->scale() != UIScale::kSmall) {
        enable_button = false;
      }

      // Whenever back button is enabled, left on account button should go
      // to it; otherwise it goes nowhere.
      Widget* ab = account_button_->widget.Get();
      ab->set_neighbors_locked(false);
      ab->set_left_widget(enable_button ? back_button_->widget.Get() : ab);
      account_button_->widget->set_neighbors_locked(true);
    }

    if (!enable_button) {
      b.y_target += disable_offset;
    }

    // special case: we shift buttons on the top right to the right if the
    // menu button is hidden (and also if the button is hidden; otherwise
    // things come in diagonally)
    //
    // if (b.h_align == HAlign::kRight and b.v_align == VAlign::kTop
    // if (b.h_align >= 1.0f and b.v_align == VAlign::kTop
    //     and (toolbar_visibility_ != ToolbarVisibility::kInGame or not
    //     enable_button)) {
    // b.x_target += top_right_offset;
    // }

    // Now push our smooth value towards our target value...
    b.x_smoothed += (b.x_target - b.x_smoothed) * 0.015f * dt;
    b.y_smoothed += (b.y_target - b.y_smoothed) * 0.015f * dt;

    // Snap in place once we reach the target; otherwise note that we need
    // to keep going.
    if (std::abs(b.x_target - b.x_smoothed) < 0.1f
        && std::abs(b.y_target - b.y_smoothed) < 0.1f) {
      b.x_smoothed = b.x_target;
      b.y_smoothed = b.y_target;

      // Also flip off visibility if we're moving offscreen and have reached
      // our target.
      if (!enable_button) {
        b.widget->set_visible_in_container(false);
      }
    } else {
      have_dirty = true;
      // Always remain visible while still moving.
      b.widget->set_visible_in_container(true);
    }

    // Now calc final abs x and y based on screen size, smoothed positions,
    // etc.
    float x, y;
    x = width() * b.h_align
        + base_scale_ * (b.x_smoothed - b.width * b.scale * 0.5f);
    switch (b.v_align) {
      case VAlign::kTop:
        y = height() + base_scale_ * (b.y_smoothed - b.height * b.scale * 0.5f);
        break;
      case VAlign::kCenter:
        y = height() * 0.5f
            + base_scale_ * (b.y_smoothed - b.height * b.scale * 0.5f);
        break;
      case VAlign::kBottom:
        y = base_scale_ * (b.y_smoothed - b.height * b.scale * 0.5f);
        break;
    }
    b.widget->set_selectable(enable_button && b.selectable);
    b.widget->set_enabled(enable_button && b.selectable);
    b.widget->set_translate(x, y);
    b.widget->set_width(b.width);
    b.widget->set_height(b.height);
    b.widget->set_scale(b.scale * base_scale_);
  }

  for (Text& t : texts_) {
    // Move the text widget to wherever its target button is (plus offset).
    Button* b = t.button;
    float x =
        b->widget->tx() + base_scale_ * b->scale * (b->width * 0.5f + t.x);
    float y =
        b->widget->ty() + base_scale_ * b->scale * (b->height * 0.5f + t.y);
    t.widget->set_translate(x, y);
    t.widget->set_scale(base_scale_ * b->scale);
  }

  positions_dirty_ = have_dirty;
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

  // TEST - cycle through our scales
  if (explicit_bool(false)) {
    auto foo = time(nullptr) % 3;
    if (foo == 0) {
      base_scale_ = 1.0f;
    } else if (foo == 1) {
      base_scale_ = 0.75f;
    } else {
      base_scale_ = 0.5f;
    }
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
  positions_dirty_ = true;

  // Run an immediate step to update things; (avoids jumpy positions if
  // resizing game window))
  StepPositions(0.0f);
}

auto RootWidget::HandleMessage(const base::WidgetMessage& m) -> bool {
  // If a cancel message comes through and our back button is active, fire our
  // back button.
  // ..in all other cases just do the default.
  if (m.type == base::WidgetMessage::Type::kCancel && back_button_ != nullptr
      && back_button_->widget->enabled()
      && !overlay_stack_widget_->HasChildren()) {
    back_button_->widget->Activate();
    return true;
  } else {
    return ContainerWidget::HandleMessage(m);
  }
}

void RootWidget::SetScreenWidget(StackWidget* w) {
  // this needs to happen before any buttons get added..
  assert(buttons_.empty());
  AddWidget(w);
  screen_stack_widget_ = w;
}

void RootWidget::SetOverlayWidget(StackWidget* w) {
  // this needs to happen after our buttons and things get added..
  if (explicit_bool(BA_UI_V1_TOOLBAR_TEST)) {
    assert(!buttons_.empty());
  }
  AddWidget(w);
  overlay_stack_widget_ = w;
}

void RootWidget::OnCancelCustom() {
  // Need to revisit this. If the cancel event it pushes is not handled, it will
  // wind up back here where it pushes another back call. This cycle repeats
  // forever until something comes along which does handle cancel events and
  // then it gets them all. Current repro case is Sign-in-with-BombSquad-Account
  // window - press escape a few times while that is up and then click cancel;
  // This code is only used for toolbar mode so should be safe to leave it
  // disabled for now. g_ui->PushBackButtonCall(nullptr);
}

auto RootWidget::GetSpecialWidget(const std::string& s) const -> Widget* {
  if (s == "party_button") {
    return party_button_ ? party_button_->widget.Get() : nullptr;
  } else if (s == "tickets_plus_button") {
    return tickets_plus_button_ ? tickets_plus_button_->widget.Get() : nullptr;
  } else if (s == "back_button") {
    return back_button_ ? back_button_->widget.Get() : nullptr;
  } else if (s == "account_button") {
    return account_button_ ? account_button_->widget.Get() : nullptr;
  } else if (s == "settings_button") {
    return settings_button_ ? settings_button_->widget.Get() : nullptr;
  } else if (s == "tickets_info_button") {
    return tickets_info_button_ ? tickets_info_button_->widget.Get() : nullptr;
  } else if (s == "overlay_stack") {
    return overlay_stack_widget_;
  }
  return nullptr;
}

}  // namespace ballistica::ui_v1
