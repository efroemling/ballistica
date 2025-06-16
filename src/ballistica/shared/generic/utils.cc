// Released under the MIT License. See LICENSE for details.

#include "ballistica/shared/generic/utils.h"

#include <cstdio>
#include <fstream>
#include <list>
#include <sstream>
#include <string>
#include <vector>

#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging.h"
#include "ballistica/core/support/base_soft.h"
#include "ballistica/shared/foundation/exception.h"
#include "ballistica/shared/generic/json.h"
#include "ballistica/shared/generic/utf8.h"
#include "ballistica/shared/math/random.h"
#include "ballistica/shared/math/vector3f.h"

namespace ballistica {

using core::g_core;

#define USE_BAKED_RANDS 1

#if BA_PLATFORM_WINDOWS
#endif

#if USE_BAKED_RANDS
float Utils::precalc_rands_1_[kPrecalcRandsCount] = {
    0.00424972f, 0.0470216f,   0.545227f,  0.538243f,  0.214183f,  0.627205f,
    0.194698f,   0.917583f,    0.468622f,  0.0779965f, 0.304211f,  0.773231f,
    0.522742f,   0.378898f,    0.404598f,  0.468434f,  0.081512f,  0.408348f,
    0.0808838f,  0.427364f,    0.226629f,  0.234887f,  0.516467f,  0.0457478f,
    0.455418f,   0.194083f,    0.502244f,  0.0733989f, 0.458193f,  0.898715f,
    0.624819f,   0.70762f,     0.759858f,  0.559276f,  0.956318f,  0.408562f,
    0.206264f,   0.322909f,    0.293165f,  0.524073f,  0.407753f,  0.961242f,
    0.278234f,   0.423968f,    0.631937f,  0.534858f,  0.842336f,  0.786993f,
    0.934668f,   0.739984f,    0.968577f,  0.468159f,  0.804702f,  0.0686368f,
    0.397594f,   0.60871f,     0.485322f,  0.907066f,  0.587516f,  0.364387f,
    0.791611f,   0.899199f,    0.0186556f, 0.446891f,  0.0138f,    0.999024f,
    0.556364f,   0.29821f,     0.23943f,   0.338024f,  0.157135f,  0.25299f,
    0.791138f,   0.367175f,    0.584245f,  0.496136f,  0.358228f,  0.280143f,
    0.538658f,   0.190721f,    0.656737f,  0.010905f,  0.520343f,  0.678249f,
    0.930145f,   0.823978f,    0.457201f,  0.988418f,  0.854635f,  0.955912f,
    0.0226999f,  0.183605f,    0.838141f,  0.210646f,  0.160344f,  0.111269f,
    0.348488f,   0.648031f,    0.844362f,  0.65157f,   0.0598469f, 0.952439f,
    0.265193f,   0.768256f,    0.773861f,  0.723251f,  0.53157f,   0.36183f,
    0.485393f,   0.348683f,    0.551617f,  0.648207f,  0.656125f,  0.879799f,
    0.0674501f,  0.000782927f, 0.607129f,  0.116035f,  0.67095f,   0.692934f,
    0.276618f,   0.137535f,    0.771033f,  0.278625f,  0.686023f,  0.873823f,
    0.254666f,   0.75378f};
float Utils::precalc_rands_2_[kPrecalcRandsCount] = {
    0.425019f,   0.29261f,   0.623541f,  0.241628f,  0.772656f, 0.434116f,
    0.295335f,   0.814317f,  0.122326f,  0.887651f,  0.873536f, 0.692463f,
    0.730894f,   0.142115f,  0.0722184f, 0.977652f,  0.971393f, 0.111517f,
    0.41341f,    0.699999f,  0.955932f,  0.746667f,  0.267962f, 0.883952f,
    0.202871f,   0.952115f,  0.221069f,  0.616162f,  0.842076f, 0.705628f,
    0.332754f,   0.974675f,  0.940277f,  0.756059f,  0.831943f, 0.70631f,
    0.674705f,   0.13903f,   0.22751f,   0.0875125f, 0.101364f, 0.593826f,
    0.271567f,   0.63593f,   0.970994f,  0.359381f,  0.147583f, 0.987353f,
    0.960315f,   0.904639f,  0.874661f,  0.352573f,  0.630782f, 0.578075f,
    0.364932f,   0.588095f,  0.799978f,  0.0502811f, 0.379093f, 0.252171f,
    0.598992f,   0.843808f,  0.544584f,  0.895444f,  0.935885f, 0.592526f,
    0.810681f,   0.0200064f, 0.0986983f, 0.164623f,  0.975185f, 0.0102097f,
    0.648763f,   0.114897f,  0.400273f,  0.549732f,  0.732205f, 0.363931f,
    0.223837f,   0.4427f,    0.770981f,  0.280827f,  0.407232f, 0.323108f,
    0.9429f,     0.594368f,  0.175995f,  0.34f,      0.857507f, 0.016013f,
    0.516969f,   0.847756f,  0.638805f,  0.324338f,  0.897038f, 0.0950314f,
    0.0460401f,  0.449791f,  0.189096f,  0.931966f,  0.846644f, 0.64728f,
    0.096389f,   0.075902f,  0.27798f,   0.673576f,  0.102553f, 0.275159f,
    0.00170948f, 0.319388f,  0.0328678f, 0.411649f,  0.496922f, 0.778794f,
    0.634341f,   0.158655f,  0.0157559f, 0.195268f,  0.663882f, 0.148622f,
    0.118159f,   0.552174f,  0.757064f,  0.854851f,  0.991449f, 0.349681f,
    0.17858f,    0.774876f};
float Utils::precalc_rands_3_[kPrecalcRandsCount] = {
    0.29369f,    0.894838f,  0.857948f,   0.04309f,   0.0296678f, 0.180115f,
    0.694884f,   0.227017f,  0.936936f,   0.746493f,  0.511976f,  0.231185f,
    0.1333f,     0.524805f,  0.774586f,   0.395971f,  0.206664f,  0.274414f,
    0.178939f,   0.88643f,   0.346536f,   0.22934f,   0.635988f,  0.589186f,
    0.652835f,   0.195603f,  0.504794f,   0.831229f,  0.769911f,  0.494712f,
    0.60128f,    0.367987f,  0.239279f,   0.0791311f, 0.469948f,  0.948189f,
    0.760893f,   0.670452f,  0.753765f,   0.822003f,  0.628783f,  0.432039f,
    0.226478f,   0.0678665f, 0.497384f,   0.110421f,  0.428975f,  0.446298f,
    0.00813589f, 0.2634f,    0.434728f,   0.693152f,  0.547276f,  0.702469f,
    0.407723f,   0.11742f,   0.235373f,   0.0738137f, 0.410148f,  0.231855f,
    0.256911f,   0.879873f,  0.818198f,   0.73404f,   0.423038f,  0.577114f,
    0.116636f,   0.247292f,  0.822178f,   0.817466f,  0.940992f,  0.593788f,
    0.751732f,   0.0681611f, 0.38832f,    0.352672f,  0.174289f,  0.582884f,
    0.0338663f,  0.460085f,  0.869757f,   0.854794f,  0.35513f,   0.477297f,
    0.31343f,    0.545157f,  0.943892f,   0.383522f,  0.121732f,  0.131018f,
    0.690497f,   0.231025f,  0.395681f,   0.144711f,  0.521456f,  0.192024f,
    0.796611f,   0.64258f,   0.13998f,    0.560008f,  0.549709f,  0.831634f,
    0.010101f,   0.684939f,  0.00884889f, 0.796426f,  0.603282f,  0.591985f,
    0.731204f,   0.950351f,  0.408559f,   0.592352f,  0.76991f,   0.196648f,
    0.376926f,   0.508574f,  0.809908f,   0.862359f,  0.863431f,  0.884588f,
    0.895885f,   0.391311f,  0.976098f,   0.473118f,  0.286659f,  0.0946781f,
    0.402437f,   0.347471f};
#else   // USE_BAKED_RANDS
float Utils::precalc_rands_1_[kPrecalcRandsCount];
float Utils::precalc_rands_2_[kPrecalcRandsCount];
float Utils::precalc_rands_3_[kPrecalcRandsCount];
#endif  // USE_BAKED_RANDS

Utils::Utils() {
  // Is this gonna be consistent cross-platform?... :-/
  srand(543);  // NOLINT

  // We now bake these in so they match across platforms...
#if USE_BAKED_RANDS
#else
  // set up our precalculated rand vals
  for (int i = 0; i < kPrecalcRandsCount; i++) {
    precalc_rands_1_[i] = static_cast<float>(rand()) / RAND_MAX;  // NOLINT
    precalc_rands_2_[i] = static_cast<float>(rand()) / RAND_MAX;  // NOLINT
    precalc_rands_3_[i] = static_cast<float>(rand()) / RAND_MAX;  // NOLINT
  }
#endif
  // huffman_ = std::make_unique<Huffman>();
}

Utils::~Utils() = default;

auto Utils::StringReplaceOne(std::string* target, const std::string& key,
                             const std::string& replacement) -> bool {
  assert(target != nullptr);
  size_t pos = target->find(key);
  if (pos != std::string::npos) {
    target->replace(pos, key.size(), replacement);
    return true;
  }
  return false;
}

// from https://stackoverflow.com/questions/5343190/
// how-do-i-replace-all-instances-of-a-string-with-another-string/14678800
void Utils::StringReplaceAll(std::string* target, const std::string& key,
                             const std::string& replacement) {
  assert(target != nullptr);
  if (key.empty()) {
    return;
  }
  std::string ws_ret;
  ws_ret.reserve(target->length());
  size_t start_pos = 0, pos;
  while ((pos = target->find(key, start_pos)) != std::string::npos) {
    ws_ret += target->substr(start_pos, pos - start_pos);
    ws_ret += replacement;
    pos += key.length();
    start_pos = pos;
  }
  ws_ret += target->substr(start_pos);
  target->swap(ws_ret);  // faster than str = ws_ret;
}

auto Utils::IsValidUTF8(const std::string& val) -> bool {
  std::string out = Utils::GetValidUTF8(val.c_str(), "bsivu8");
  return (out == val);
}

static auto utf8_check_is_valid(const std::string& string) -> bool {
  int c, i, ix, n, j;
  for (i = 0, ix = static_cast<int>(string.length()); i < ix; i++) {
    c = (unsigned char)string[i];
    // if (c==0x09 || c==0x0a || c==0x0d
    // || (0x20 <= c && c <= 0x7e) ) n = 0;  // is_printable_ascii
    if (0x00 <= c && c <= 0x7f) {
      n = 0;                          // 0bbbbbbb
    } else if ((c & 0xE0) == 0xC0) {  // NOLINT
      n = 1;                          // 110bbbbb
    } else if (c == 0xed && i < (ix - 1)
               && ((unsigned char)string[i + 1] & 0xa0) == 0xa0) {  // NOLINT
      return false;                   // U+d800 to U+dfff
    } else if ((c & 0xF0) == 0xE0) {  // NOLINT
      n = 2;                          // 1110bbbb
    } else if ((c & 0xF8) == 0xF0) {  // NOLINT
      n = 3;                          // 11110bbb
    } else {
      // else if (($c & 0xFC) == 0xF8)
      // n=4;  // 111110bb //byte 5, unnecessary in 4 byte UTF-8
      // else if (($c & 0xFE) == 0xFC)
      // n=5;  // 1111110b //byte 6, unnecessary in 4 byte UTF-8

      return false;
    }
    for (j = 0; j < n && i < ix; j++) {  // n bytes matching 10bbbbbb follow ?
      // NOLINTNEXTLINE
      if ((++i == ix) || (((unsigned char)string[i] & 0xC0) != 0x80)) {
        return false;
      }
    }
  }
  return true;
}

// added by ericf from http://stackoverflow.com/questions/17316506/
// strip-invalid-utf8-from-string-in-c-c
// static std::string correct_non_utf_8(std::string *str) {
auto Utils::GetValidUTF8(const char* str, const char* loc) -> std::string {
  int i, f_size = static_cast<int>(strlen(str));
  unsigned char c, c2 = 0, c3, c4;
  std::string to;
  to.reserve(static_cast<size_t>(f_size));

  // ok, it seems we're somehow letting some funky utf8 through that's
  // causing crashes.. for now lets try this all-or-nothing func and return
  // ascii only if it fails
  if (!utf8_check_is_valid(str)) {
    // now strip out anything but normal ascii...
    for (i = 0; i < f_size; i++) {
      c = (unsigned char)(str)[i];
      if (c < 127) {  // normal ASCII
        to.append(1, static_cast<char>(c));
      }
    }

    // phone home a few times for bad strings
    static int logged_count = 0;
    if (logged_count < 10) {
      std::string log_str;
      for (i = 0; i < f_size; i++) {
        c = (unsigned char)(str)[i];
        log_str += std::to_string(static_cast<int>(c));
        if (i + 1 < f_size) {
          log_str += ',';
        }
      }
      logged_count++;
      g_core->logging->Log(LogName::kBa, LogLevel::kError,
                           "GOT INVALID UTF8 SEQUENCE: (" + log_str
                               + "); RETURNING '" + to + "'; LOC '" + loc
                               + "'");
    }

  } else {
    for (i = 0; i < f_size; i++) {
      c = (unsigned char)(str)[i];
      if (c < 32) {                          // control char
        if (c == 9 || c == 10 || c == 13) {  // allow only \t \n \r
          to.append(1, static_cast<char>(c));
        }
        continue;
      } else if (c < 127) {  // normal ASCII
        to.append(1, static_cast<char>(c));
        continue;
      } else if (c < 160) {
        // control char (nothing should be defined here either
        // ASCI, ISO_8859-1 or UTF8, so skipping)
        if (c2 == 128) {  // fix microsoft mess, add euro
          to.append(1, static_cast<char>((unsigned char)(226)));
          to.append(1, static_cast<char>((unsigned char)(130)));
          to.append(1, static_cast<char>((unsigned char)(172)));
        }
        if (c2 == 133) {  // fix IBM mess, add NEL = \n\r
          to.append(1, 10);
          to.append(1, 13);
        }
        continue;
      } else if (c < 192) {  // invalid for UTF8, converting ASCII
        to.append(1, static_cast<char>((unsigned char)194));
        to.append(1, static_cast<char>(c));
        continue;
      } else if (c < 194) {  // invalid for UTF8, converting ASCII
        to.append(1, static_cast<char>((unsigned char)195));
        to.append(1, c - 64);
        continue;
      } else if (c < 224 && i + 1 < f_size) {  // possibly 2byte UTF8
        c2 = (unsigned char)(str)[i + 1];
        if (c2 > 127 && c2 < 192) {    // valid 2byte UTF8
          if (c == 194 && c2 < 160) {  // control char, skipping
          } else {
            to.append(1, static_cast<char>(c));
            to.append(1, static_cast<char>(c2));
          }
          i++;
          continue;
        }
      } else if (c < 240 && i + 2 < f_size) {  // possibly 3byte UTF8
        c2 = (unsigned char)(str)[i + 1];
        c3 = (unsigned char)(str)[i + 2];
        if (c2 > 127 && c2 < 192 && c3 > 127 && c3 < 192) {  // valid 3byte UTF8
          to.append(1, static_cast<char>(c));
          to.append(1, static_cast<char>(c2));
          to.append(1, static_cast<char>(c3));
          i += 2;
          continue;
        }
      } else if (c < 245 && i + 3 < f_size) {  // possibly 4byte UTF8
        c2 = (unsigned char)(str)[i + 1];
        c3 = (unsigned char)(str)[i + 2];
        c4 = (unsigned char)(str)[i + 3];
        if (c2 > 127 && c2 < 192 && c3 > 127 && c3 < 192 && c4 > 127
            && c4 < 192) {
          // valid 4byte UTF8
          to.append(1, static_cast<char>(c));
          to.append(1, static_cast<char>(c2));
          to.append(1, static_cast<char>(c3));
          to.append(1, static_cast<char>(c4));
          i += 3;
          continue;
        }
      }
      // invalid UTF8, converting ASCII
      // (c>245 || string too short for multi-byte))
      to.append(1, static_cast<char>((unsigned char)195));
      to.append(1, c - 64);
    }
  }
  return to;
}

auto Utils::UTF8StringLength(const char* val) -> int {
  std::string valid_str = GetValidUTF8(val, "gusl1");
  return u8_strlen(valid_str.c_str());
}

auto Utils::GetUTF8Value(const char* c) -> uint32_t {
  int offset = 0;
  uint32_t val = u8_nextchar(c, &offset);

  // Hack: allow showing euro even if we don't support unicode font rendering.
  if (!g_buildconfig.enable_os_font_rendering()) {
    if (val == 8364) {
      val = 0xE000;
    }
  }
  return val;
}

auto Utils::UTF8FromUnicode(std::vector<uint32_t> unichars) -> std::string {
  int buffer_size = static_cast<int>(unichars.size() * 4 + 1);
  // at most 4 chars per unichar plus ending zero
  std::vector<char> buffer(static_cast<size_t>(buffer_size));
  int len = u8_toutf8(buffer.data(), buffer_size, unichars.data(),
                      static_cast<int>(unichars.size()));
  assert(len == unichars.size());
  buffer.resize(strlen(buffer.data()) + 1);
  return buffer.data();
}

auto Utils::UnicodeFromUTF8(const std::string& s_in, const char* loc)
    -> std::vector<uint32_t> {
  std::string s = GetValidUTF8(s_in.c_str(), loc);
  // worst case every char is a character (plus trailing 0)
  std::vector<uint32_t> vals(s.size() + 1);
  int converted = u8_toucs(&vals[0], static_cast<int>(vals.size()), s.c_str(),
                           static_cast<int>(s.size()));
  vals.resize(static_cast<size_t>(converted));
  return vals;
}

auto Utils::UTF8FromUnicodeChar(uint32_t c) -> std::string {
  char buffer[10];
  u8_toutf8(buffer, sizeof(buffer), &c, 1);
  return buffer;
}

void Utils::AdvanceUTF8(const char** c) {
  int offset = 0;
  u8_nextchar(*c, &offset);
  *c += offset;
}

auto Utils::GetJSONString(const char* s) -> std::string {
  std::string str;
  cJSON* str_obj = cJSON_CreateString(s);
  char* str_buffer = cJSON_PrintUnformatted(str_obj);
  str = str_buffer;
  free(str_buffer);
  cJSON_Delete(str_obj);
  return str;
}

auto Utils::PtrToString(const void* val) -> std::string {
  char buffer[128];
  snprintf(buffer, sizeof(buffer), "%p", val);
  return buffer;
}

// FIXME: This should not live here.
static const char* g_default_random_names[] = {
    "Flopsy",  "Skippy",    "Boomer",   "Jolly",    "Zeus",     "Garth",
    "Dizzy",   "Mullet",    "Ogre",     "Ginger",   "Nippy",    "Murphy",
    "Crom",    "Sparky",    "Wedge",    "Arthur",   "Benji",    "Pan",
    "Wallace", "Hamish",    "Luke",     "Cowboy",   "Uncas",    "Magua",
    "Robin",   "Lancelot",  "Mad Dog",  "Maximus",  "Leonidas", "Don Quixote",
    "Beowulf", "Gilgamesh", "Conan",    "Cicero",   "Elmer",    "Flynn",
    "Duck",    "Uther",     "Darkness", "Sunshine", "Willy",    "Elvis",
    "Dolph",   "Rico",      "Magoogan", "Willow",   "Rose",     "Egg",
    "Thunder", "Jack",      "Dude",     "Walter",   "Donny",    "Larry",
    "Chunk",   "Socrates",  nullptr};

static std::list<std::string>* g_random_names_list = nullptr;

auto Utils::GetRandomNameList() -> const std::list<std::string>& {
  assert(core::g_base_soft && core::g_base_soft->InLogicThread());
  if (g_random_names_list == nullptr) {
    // This will init the list with our default english names.
    SetRandomNameList(std::list<std::string>(1, "DEFAULT_NAMES"));
  }

  if (g_random_names_list != nullptr) {
    return *g_random_names_list;
  }
  throw Exception("random name list uninited");
}

void Utils::SetRandomNameList(const std::list<std::string>& custom_names) {
  assert(core::g_base_soft && core::g_base_soft->InLogicThread());
  if (!g_random_names_list) {
    g_random_names_list = new std::list<std::string>;
  } else {
    g_random_names_list->clear();
  }
  bool add_default_names = false;
  if (custom_names.empty()) {
    add_default_names = true;
  }
  for (const auto& custom_name : custom_names) {
    if (custom_name == "DEFAULT_NAMES") {
      add_default_names = true;
    } else {
      g_random_names_list->push_back(custom_name);
    }
  }
  if (add_default_names) {
    for (const char** c = g_default_random_names; *c != nullptr; c++) {
      g_random_names_list->push_back(*c);
    }
  }
}

auto Utils::Sphrand(float radius) -> Vector3f {
  while (true) {
    float x = RandomFloat();
    float y = RandomFloat();
    float z = RandomFloat();
    x = -1.0f + x * 2.0f;
    y = -1.0f + y * 2.0f;
    z = -1.0f + z * 2.0f;
    if (x * x + y * y + z * z <= 1.0f) {
      return {x * radius, y * radius, z * radius};
    }
  }
}

auto Utils::FileToString(const std::string& file_name) -> std::string {
  std::ifstream file_stream{file_name};
  if (file_stream.fail()) {
    throw Exception("Error opening file for reading: '" + file_name + "'");
  }
  std::ostringstream str_stream{};
  file_stream >> str_stream.rdbuf();
  if (file_stream.fail() && !file_stream.eof()) {
    throw Exception("Error reading file: '" + file_name + "'");
  }
  return str_stream.str();
}

auto Utils::BaseName(const std::string& val) -> std::string {
  const char* c = val.c_str();
  const char* lastvalid = c;
  while (*c != 0) {
    if (*c == '/' || *c == '\\') {
      lastvalid = c + 1;
    }
    ++c;
  }
  return lastvalid;
}

auto Utils::StripNonAsciiFromUTF8(const std::string& str) -> std::string {
  auto uni = UnicodeFromUTF8(str, "wGcwe87");
  uni.erase(
      std::remove_if(uni.begin(), uni.end(), [](int i) { return i > 127; }),
      uni.end());
  return UTF8FromUnicode(uni);
}

}  // namespace ballistica
