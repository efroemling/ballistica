// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/assets/sound_asset.h"

#include <cstdio>
#include <cstring>
#include <string>
#include <vector>

#include "ballistica/core/logging/logging.h"

#if BA_ENABLE_AUDIO
#if BA_USE_TREMOR_VORBIS
#include "ivorbisfile.h"  // NOLINT
#else
#include <vorbis/vorbisfile.h>
#endif
#endif  // BA_ENABLE_AUDIO

#include "ballistica/base/assets/assets.h"
#include "ballistica/base/audio/audio_server.h"
#include "ballistica/base/python/base_python.h"
#include "ballistica/core/core.h"
#include "ballistica/core/platform/core_platform.h"

// Need to move away from OpenAL on Apple stuff.
#if __clang__
#pragma GCC diagnostic ignored "-Wdeprecated-declarations"
#endif

namespace ballistica::base {

#if BA_ENABLE_AUDIO

const int kReadBufferSize = 32768;  // 32 KB buffers

static auto CallbackRead(void* ptr, size_t size, size_t nmemb,
                         void* data_source) -> size_t {
  return fread(ptr, size, nmemb, static_cast<FILE*>(data_source));
}
static auto CallbackSeek(void* data_source, ogg_int64_t offset, int whence)
    -> int {
  return fseek(static_cast<FILE*>(data_source),
               static_cast_check_fit<long>(offset), whence);  // NOLINT
}
static auto CallbackClose(void* data_source) -> int {
  return fclose(static_cast<FILE*>(data_source));
}
static long CallbackTell(void* data_source) {  // NOLINT (vorbis uses long)
  return ftell(static_cast<FILE*>(data_source));
}

// This function loads a .ogg file into a memory buffer and returns
// the format and frequency.  return value is true on success or false if a
// fallback was used
static auto LoadOgg(const char* file_name, std::vector<char>* buffer,
                    ALenum* format, ALsizei* freq) -> bool {
  int bit_stream;
  int bytes;
  char array[kReadBufferSize];  // Local fixed size array
  FILE* f;
  bool fallback = false;

  // Open for binary reading.
  f = g_core->platform->FOpen(file_name, "rb");
  if (f == nullptr) {
    fallback = true;
    g_core->logging->Log(LogName::kBaAudio, LogLevel::kError,
                         std::string("Can't open sound file '") + file_name
                             + "' for reading...");

    // Attempt a fallback standin; if that doesn't work, throw in the towel.
    file_name = "data/global/audio/blank.ogg";
    f = g_core->platform->FOpen(file_name, "rb");
    if (f == nullptr)
      throw Exception(std::string("Can't open fallback sound file '")
                      + file_name + "' for reading...");
  }

  vorbis_info* p_info;
  OggVorbis_File ogg_file;
  ov_callbacks callbacks;
  callbacks.read_func = CallbackRead;
  callbacks.seek_func = CallbackSeek;
  callbacks.close_func = CallbackClose;
  callbacks.tell_func = CallbackTell;

  // Try opening the given file
  if (ov_open_callbacks(f, &ogg_file, nullptr, 0, callbacks) != 0) {
    g_core->logging->Log(
        LogName::kBaAudio, LogLevel::kError,
        std::string("Error decoding sound file '") + file_name + "'");

    fclose(f);

    // Attempt fallback.
    file_name = "data/global/audio/blank.ogg";
    f = g_core->platform->FOpen(file_name, "rb");

    // If fallback doesn't work, throw in the towel.
    if (f == nullptr)
      throw Exception(std::string("Can't open fallback sound file '")
                      + file_name + "' for reading...");
    if (ov_open_callbacks(f, &ogg_file, nullptr, 0, callbacks) != 0)
      throw Exception(std::string("Error decoding fallback sound file '")
                      + file_name + "'");
  }

  // Get some information about the OGG file.
  p_info = ov_info(&ogg_file, -1);

  // Check the number of channels. Always use 16-bit samples.
  if (p_info->channels == 1) {
    (*format) = AL_FORMAT_MONO16;
  } else {
    (*format) = AL_FORMAT_STEREO16;
  }

  // The frequency of the sampling rate.
  (*freq) = static_cast<ALsizei>(p_info->rate);

  bool corrupt = false;

  // Keep reading until all is read.
  do {
    // Read up to a buffer's worth of decoded sound data.
#if BA_USE_TREMOR_VORBIS
    bytes = static_cast<int>(
        ov_read(&ogg_file, array, kReadBufferSize, &bit_stream));
#else
    bytes = static_cast<int>(
        ov_read(&ogg_file, array, kReadBufferSize, 0, 2, 1, &bit_stream));
#endif

    // If something went wrong in the decode, just spit out an empty sound and
    // an error message that the user should re-install.
    if (bytes < 0) {
      corrupt = true;
      ov_clear(&ogg_file);
      break;
    }

    // Append to end of buffer
    buffer->insert(buffer->end(), array, array + bytes);
  } while (bytes > 0);

  // Clean up!
  ov_clear(&ogg_file);

  if (corrupt) {
    static bool reported_corrupt = false;
    if (!reported_corrupt) {
      reported_corrupt = true;
      g_base->python->objs().PushCall(
          BasePython::ObjID::kPrintCorruptFileErrorCall);
    }
    (*buffer) = std::vector<char>(32 * 100, 0);
  }

  if ((*buffer).empty()) {
    throw Exception(std::string("Error: got zero-length buffer from ogg-file '")
                    + file_name + "'");
  }
  return !fallback;
}

static void LoadCachedOgg(const char* file_name, std::vector<char>* buffer,
                          ALenum* format, ALsizei* freq) {
  std::string sound_cache_dir =
      g_core->GetCacheDirectory() + BA_DIRSLASH + "audio";
  static bool made_sound_cache_dir = false;
  if (!made_sound_cache_dir) {
    g_core->platform->MakeDir(sound_cache_dir);
    made_sound_cache_dir = true;
  }
  std::vector<char> b(strlen(file_name) + 1);
  memcpy(b.data(), file_name, b.size());
  for (char* c = &b[0]; *c != 0; c++) {
    if ((*c) == '/') *c = '_';
  }
  std::string cache_file_name = sound_cache_dir + "/" + &b[0] + ".cache";

  // If we have a cache file and it matches the mod time on the ogg, attempt to
  // load it.
  struct BA_STAT stat_ogg {};
  time_t ogg_mod_time = 0;
  if (g_core->platform->Stat(file_name, &stat_ogg) == 0) {
    ogg_mod_time = stat_ogg.st_mtime;
  }
  FILE* f_cache = g_core->platform->FOpen(cache_file_name.c_str(), "rb");
  if (f_cache && ogg_mod_time != 0) {
    bool got_cache = false;
    time_t cache_mod_time;
    if (fread(&cache_mod_time, sizeof(cache_mod_time), 1, f_cache) == 1) {
      if (cache_mod_time == ogg_mod_time) {
        if (fread(&(*format), sizeof((*format)), 1, f_cache) == 1) {
          if (fread(&(*freq), sizeof((*freq)), 1, f_cache) == 1) {
            uint32_t buffer_size;
            if (fread(&buffer_size, sizeof(buffer_size), 1, f_cache) == 1) {
              (*buffer).resize(buffer_size);
              if (fread(&(*buffer)[0], buffer_size, 1, f_cache) == 1) {
                got_cache = true;
              }
            }
          }
        }
      }
    }
    fclose(f_cache);
    if (got_cache) {
      // At a loss for how this happened, but wound up loading cache files
      // with invalid formats of 0 once. Report and ignore if we see
      // something like that.
      if (*format != AL_FORMAT_MONO16 && *format != AL_FORMAT_STEREO16) {
        g_core->logging->Log(LogName::kBaAudio, LogLevel::kError,
                             std::string("Ignoring invalid audio cache of ")
                                 + file_name + " with format "
                                 + std::to_string(*format));
      } else {
        return;  // SUCCESS!!!!
      }
    }
  }

  // Ok that didn't work. Load the actual ogg.
  (*buffer).clear();
  bool success = LoadOgg(file_name, buffer, format, freq);

  // If the load went cleanly, attempt to write a cache file.
  if (success) {
    FILE* f = g_core->platform->FOpen(cache_file_name.c_str(), "wb");
    bool success2 = false;
    if (f) {
      if (fwrite(&ogg_mod_time, sizeof(ogg_mod_time), 1, f) == 1) {
        if (fwrite(&(*format), sizeof((*format)), 1, f) == 1) {
          if (fwrite(&(*freq), sizeof((*freq)), 1, f) == 1) {
            auto buffer_size = static_cast<uint32_t>((*buffer).size());
            if (fwrite(&buffer_size, sizeof(buffer_size), 1, f) == 1) {
              if (fwrite(&(*buffer)[0], buffer_size, 1, f) == 1) {
                success2 = true;
              }
            }
          }
        }
      }
      fclose(f);

      // Attempt to clean up if it looks like something went wrong.
      if (!success2) {
        g_core->platform->Unlink(cache_file_name.c_str());
      }
    }
  }
}

#endif  // BA_ENABLE_AUDIO

SoundAsset::SoundAsset(const std::string& file_name_in)
    : file_name_(file_name_in) {
  file_name_full_ =
      g_base->assets->FindAssetFile(Assets::FileType::kSound, file_name_in);
  valid_ = true;
}

auto SoundAsset::GetAssetType() const -> AssetType { return AssetType::kSound; }

auto SoundAsset::GetName() const -> std::string {
  return (!file_name_.empty()) ? file_name_ : "invalid sound";
}

void SoundAsset::DoPreload() {
#if BA_ENABLE_AUDIO

  // Its an ogg sound file.
  // if it has 'music' in its name, we'll stream it;
  // otherwise we load it in its entirety into our load-buffer.
  if (strstr(file_name_full_.c_str(), "Music.ogg")) {
    is_streamed_ = true;
  } else if (strstr(file_name_full_.c_str(), ".ogg")) {
    is_streamed_ = false;
    LoadCachedOgg(file_name_full_.c_str(), &load_buffer_, &format_, &freq_);
  } else {
    throw Exception("Unsupported sound file (needs to end in .ogg): '"
                    + file_name_full_ + "'");
  }
#endif  // BA_ENABLE_AUDIO
}

void SoundAsset::DoLoad() {
  assert(g_base->InAudioThread());
  assert(valid_);

#if BA_ENABLE_AUDIO
  assert(!g_base->audio_server->paused());

  // Note: streamed sources create buffers as they're used; not here.
  if (!is_streamed_) {
    // Generate our buffer.
    CHECK_AL_ERROR;
    alGenBuffers(1, &buffer_);
    CHECK_AL_ERROR;

    // Preload pulled data into our load-buffer, and send that along to openal.
    alBufferData(buffer_, format_, &load_buffer_[0],
                 static_cast<ALsizei>(load_buffer_.size()), freq_);

    CHECK_AL_ERROR;

    // Done with load buffer; clear its used memory.
    std::vector<char>().swap(load_buffer_);
  }

  CHECK_AL_ERROR;
#endif  // BA_ENABLE_AUDIO
}

void SoundAsset::DoUnload() {
  assert(g_base->InAudioThread());
  assert(valid_);
#if BA_ENABLE_AUDIO
  if (!is_streamed_) {
    assert(buffer_);
    CHECK_AL_ERROR;
    alDeleteBuffers(1, &buffer_);
    CHECK_AL_ERROR;
  }
#endif  // BA_ENABLE_AUDIO
}

void SoundAsset::UpdatePlayTime() {
  last_play_time_ = g_core->AppTimeMillisecs();
}

}  // namespace ballistica::base
