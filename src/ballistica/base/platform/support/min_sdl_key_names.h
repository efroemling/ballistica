// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_PLATFORM_SUPPORT_MIN_SDL_KEY_NAMES_H_
#define BALLISTICA_BASE_PLATFORM_SUPPORT_MIN_SDL_KEY_NAMES_H_

#include <string>

#include "ballistica/base/input/device/keyboard_input.h"
#include "ballistica/core/logging/logging_macros.h"

namespace ballistica::base {

// The following was pulled from sdl2
#if BA_MINSDL_BUILD
static const char* const scancode_names[SDL_NUM_SCANCODES] = {
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    "A",
    "B",
    "C",
    "D",
    "E",
    "F",
    "G",
    "H",
    "I",
    "J",
    "K",
    "L",
    "M",
    "N",
    "O",
    "P",
    "Q",
    "R",
    "S",
    "T",
    "U",
    "V",
    "W",
    "X",
    "Y",
    "Z",
    "1",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
    "0",
    "Return",
    "Escape",
    "Backspace",
    "Tab",
    "Space",
    "-",
    "=",
    "[",
    "]",
    "\\",
    "#",
    ";",
    "'",
    "`",
    ",",
    ".",
    "/",
    "CapsLock",
    "F1",
    "F2",
    "F3",
    "F4",
    "F5",
    "F6",
    "F7",
    "F8",
    "F9",
    "F10",
    "F11",
    "F12",
    "PrintScreen",
    "ScrollLock",
    "Pause",
    "Insert",
    "Home",
    "PageUp",
    "Delete",
    "End",
    "PageDown",
    "Right",
    "Left",
    "Down",
    "Up",
    "Numlock",
    "Keypad /",
    "Keypad *",
    "Keypad -",
    "Keypad +",
    "Keypad Enter",
    "Keypad 1",
    "Keypad 2",
    "Keypad 3",
    "Keypad 4",
    "Keypad 5",
    "Keypad 6",
    "Keypad 7",
    "Keypad 8",
    "Keypad 9",
    "Keypad 0",
    "Keypad .",
    nullptr,
    "Application",
    "Power",
    "Keypad =",
    "F13",
    "F14",
    "F15",
    "F16",
    "F17",
    "F18",
    "F19",
    "F20",
    "F21",
    "F22",
    "F23",
    "F24",
    "Execute",
    "Help",
    "Menu",
    "Select",
    "Stop",
    "Again",
    "Undo",
    "Cut",
    "Copy",
    "Paste",
    "Find",
    "Mute",
    "VolumeUp",
    "VolumeDown",
    nullptr,
    nullptr,
    nullptr,
    "Keypad ,",
    "Keypad = (AS400)",
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    "AltErase",
    "SysReq",
    "Cancel",
    "Clear",
    "Prior",
    "Return",
    "Separator",
    "Out",
    "Oper",
    "Clear / Again",
    "CrSel",
    "ExSel",
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    "Keypad 00",
    "Keypad 000",
    "ThousandsSeparator",
    "DecimalSeparator",
    "CurrencyUnit",
    "CurrencySubUnit",
    "Keypad (",
    "Keypad )",
    "Keypad {",
    "Keypad }",
    "Keypad Tab",
    "Keypad Backspace",
    "Keypad A",
    "Keypad B",
    "Keypad C",
    "Keypad D",
    "Keypad E",
    "Keypad F",
    "Keypad XOR",
    "Keypad ^",
    "Keypad %",
    "Keypad <",
    "Keypad >",
    "Keypad &",
    "Keypad &&",
    "Keypad |",
    "Keypad ||",
    "Keypad :",
    "Keypad #",
    "Keypad Space",
    "Keypad @",
    "Keypad !",
    "Keypad MemStore",
    "Keypad MemRecall",
    "Keypad MemClear",
    "Keypad MemAdd",
    "Keypad MemSubtract",
    "Keypad MemMultiply",
    "Keypad MemDivide",
    "Keypad +/-",
    "Keypad Clear",
    "Keypad ClearEntry",
    "Keypad Binary",
    "Keypad Octal",
    "Keypad Decimal",
    "Keypad Hexadecimal",
    nullptr,
    nullptr,
    "Left Ctrl",
    "Left Shift",
    "Left Alt",
    "Left GUI",
    "Right Ctrl",
    "Right Shift",
    "Right Alt",
    "Right GUI",
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    "ModeSwitch",
    "AudioNext",
    "AudioPrev",
    "AudioStop",
    "AudioPlay",
    "AudioMute",
    "MediaSelect",
    "WWW",
    "Mail",
    "Calculator",
    "Computer",
    "AC Search",
    "AC Home",
    "AC Back",
    "AC Forward",
    "AC Stop",
    "AC Refresh",
    "AC Bookmarks",
    "BrightnessDown",
    "BrightnessUp",
    "DisplaySwitch",
    "KBDIllumToggle",
    "KBDIllumDown",
    "KBDIllumUp",
    "Eject",
    "Sleep",
    "App1",
    "App2",
    "AudioRewind",
    "AudioFastForward",
};

#pragma clang diagnostic push
#pragma ide diagnostic ignored "hicpp-signed-bitwise"

static char* UCS4ToUTF8(uint32_t ch, char* dst) {
  auto* p = reinterpret_cast<uint8_t*>(dst);
  if (ch <= 0x7F) {
    *p = static_cast<uint8_t>(ch);
    ++dst;
  } else if (ch <= 0x7FF) {
    p[0] = static_cast<uint8_t>(0xC0 | static_cast<uint8_t>((ch >> 6) & 0x1F));
    p[1] = static_cast<uint8_t>(0x80 | static_cast<uint8_t>(ch & 0x3F));
    dst += 2;
  } else if (ch <= 0xFFFF) {
    p[0] = static_cast<uint8_t>(0xE0 | static_cast<uint8_t>((ch >> 12) & 0x0F));
    p[1] = static_cast<uint8_t>(0x80 | static_cast<uint8_t>((ch >> 6) & 0x3F));
    p[2] = static_cast<uint8_t>(0x80 | static_cast<uint8_t>(ch & 0x3F));
    dst += 3;
  } else if (ch <= 0x1FFFFF) {
    p[0] = static_cast<uint8_t>(0xF0 | static_cast<uint8_t>((ch >> 18) & 0x07));
    p[1] = static_cast<uint8_t>(0x80 | static_cast<uint8_t>((ch >> 12) & 0x3F));
    p[2] = static_cast<uint8_t>(0x80 | static_cast<uint8_t>((ch >> 6) & 0x3F));
    p[3] = static_cast<uint8_t>(0x80 | static_cast<uint8_t>(ch & 0x3F));
    dst += 4;
  } else if (ch <= 0x3FFFFFF) {
    p[0] = static_cast<uint8_t>(0xF8 | static_cast<uint8_t>((ch >> 24) & 0x03));
    p[1] = static_cast<uint8_t>(0x80 | static_cast<uint8_t>((ch >> 18) & 0x3F));
    p[2] = static_cast<uint8_t>(0x80 | static_cast<uint8_t>((ch >> 12) & 0x3F));
    p[3] = static_cast<uint8_t>(0x80 | static_cast<uint8_t>((ch >> 6) & 0x3F));
    p[4] = static_cast<uint8_t>(0x80 | static_cast<uint8_t>(ch & 0x3F));
    dst += 5;
  } else {
    p[0] = static_cast<uint8_t>(0xFC | static_cast<uint8_t>((ch >> 30) & 0x01));
    p[1] = static_cast<uint8_t>(0x80 | static_cast<uint8_t>((ch >> 24) & 0x3F));
    p[2] = static_cast<uint8_t>(0x80 | static_cast<uint8_t>((ch >> 18) & 0x3F));
    p[3] = static_cast<uint8_t>(0x80 | static_cast<uint8_t>((ch >> 12) & 0x3F));
    p[4] = static_cast<uint8_t>(0x80 | static_cast<uint8_t>((ch >> 6) & 0x3F));
    p[5] = static_cast<uint8_t>(0x80 | static_cast<uint8_t>(ch & 0x3F));
    dst += 6;
  }
  return dst;
}
#pragma clang diagnostic pop

static const char* GetScancodeName(SDL_Scancode scancode) {
  const char* name;
  if (static_cast<int>(scancode) < SDL_SCANCODE_UNKNOWN
      || scancode >= SDL_NUM_SCANCODES) {
    BA_LOG_ONCE(LogName::kBaInput, LogLevel::kError,
                "GetScancodeName passed invalid scancode "
                    + std::to_string(static_cast<int>(scancode)));
    return "";
  }

  name = scancode_names[scancode];
  if (name) {
    return name;
  } else {
    return "";
  }
}

auto MinSDL_GetKeyName(int keycode) -> std::string {
  SDL_Keycode key{keycode};
  static char name[8];
  char* end;

  // Handle a few specially per platform.
  if (g_buildconfig.platform_macos()) {
    switch (key) {
      case SDLK_LGUI:
        return "Left Command";
      case SDLK_RGUI:
        return "Right Command";
      case SDLK_LALT:
        return "Left Option";
      case SDLK_RALT:
        return "Right Option";
      default:
        break;
    }
  }

  if (key & SDLK_SCANCODE_MASK) {
    return GetScancodeName((SDL_Scancode)(key & ~SDLK_SCANCODE_MASK));
  }

  switch (key) {
    case SDLK_RETURN:
      return GetScancodeName(SDL_SCANCODE_RETURN);
    case SDLK_ESCAPE:
      return GetScancodeName(SDL_SCANCODE_ESCAPE);
    case SDLK_BACKSPACE:
      return GetScancodeName(SDL_SCANCODE_BACKSPACE);
    case SDLK_TAB:
      return GetScancodeName(SDL_SCANCODE_TAB);
    case SDLK_SPACE:
      return GetScancodeName(SDL_SCANCODE_SPACE);
    case SDLK_DELETE:
      return GetScancodeName(SDL_SCANCODE_DELETE);
    default:
      /* Unaccented letter keys on latin keyboards are normally
         labeled in upper case (and probably on others like Greek or
         Cyrillic too, so if you happen to know for sure, please
         adapt this). */
      if (key >= 'a' && key <= 'z') {
        key -= 32;
      }

      end = UCS4ToUTF8(static_cast<uint32_t>(key), name);
      *end = '\0';
      return name;
  }
}

#endif  // BA_MINSDL_BUILD

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_PLATFORM_SUPPORT_MIN_SDL_KEY_NAMES_H_
