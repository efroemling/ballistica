// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/node/sound_node.h"

#include <vector>

#include "ballistica/base/audio/audio.h"
#include "ballistica/base/audio/audio_source.h"
#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging_macros.h"
#include "ballistica/scene_v1/assets/scene_sound.h"
#include "ballistica/scene_v1/node/node_attribute.h"
#include "ballistica/scene_v1/node/node_type.h"

namespace ballistica::scene_v1 {

class SoundNodeType : public NodeType {
 public:
#define BA_NODE_TYPE_CLASS SoundNode
  BA_NODE_CREATE_CALL(CreateSound);
  BA_FLOAT_ARRAY_ATTR(position, position, SetPosition);
  BA_FLOAT_ATTR(volume, volume, SetVolume);
  BA_BOOL_ATTR(positional, positional, SetPositional);
  BA_BOOL_ATTR(music, music, SetMusic);
  BA_BOOL_ATTR(loop, loop, SetLoop);
  BA_SOUND_ATTR(sound, sound, SetSound);
#undef BA_NODE_TYPE_CLASS
  SoundNodeType()
      : NodeType("sound", CreateSound),
        position(this),
        volume(this),
        positional(this),
        music(this),
        loop(this),
        sound(this) {}
};
static NodeType* node_type{};

auto SoundNode::InitType() -> NodeType* {
  node_type = new SoundNodeType();
  return node_type;
}

SoundNode::SoundNode(Scene* scene) : Node(scene, node_type) {}

SoundNode::~SoundNode() {
  if (playing_) {
    g_base->audio->PushSourceStopSoundCall(play_id_);
  }
}

void SoundNode::SetPosition(const std::vector<float>& vals) {
  if (vals.size() != 3) {
    throw Exception("Expected float array of size 3 for position",
                    PyExcType::kValue);
  }
  position_ = vals;

  // We don't actually update here; we just mark our position as dirty
  // and then update it every now and then.
  position_dirty_ = true;
}

void SoundNode::SetVolume(float val) {
  if (val == volume_) {
    return;
  }
  volume_ = val;

  // FIXME we could probably update this in an infrequent manner in case its
  //  being driven by another attr.
  if (playing_) {
    base::AudioSource* s = g_base->audio->SourceBeginExisting(play_id_, 106);
    if (s) {
      s->SetGain(volume_);
      s->End();
    }
  }
}

void SoundNode::SetLoop(bool val) {
  if (loop_ == val) {
    return;
  }
  loop_ = val;

  // We don't actually update looping on a playing sound.
  if (playing_) {
    BA_LOG_ONCE(LogName::kBa, LogLevel::kError,
                "Can't set 'loop' attr on already-playing sound.");
  }
}

void SoundNode::SetSound(SceneSound* s) {
  if (s == sound_.get()) {
    return;
  }
  sound_ = s;

  // We'll start playing in our next Step; this allows
  // time for other setAttrs to go through first such as looping.
  // (which can't happen after we start playing)
}

void SoundNode::SetPositional(bool val) {
  if (val == positional_) {
    return;
  }
  positional_ = val;
  if (playing_) {
    BA_LOG_ONCE(LogName::kBa, LogLevel::kError,
                "Can't set 'positional' attr on already-playing sound");
  }
}

void SoundNode::SetMusic(bool val) {
  if (val == music_) {
    return;
  }
  music_ = val;
  if (playing_) {
    base::AudioSource* s = g_base->audio->SourceBeginExisting(play_id_, 104);
    if (s) {
      s->SetIsMusic(music_);
      s->End();
    }
  }
}

void SoundNode::Step() {
  // If we want to start playing, do so.
  if (!playing_ && sound_.exists()) {
    base::AudioSource* s = g_base->audio->SourceBeginNew();
    if (s) {
      assert(position_.size() == 3);
      s->SetPosition(position_[0], position_[1], position_[2]);
      s->SetLooping(loop_);
      s->SetPositional(positional_);
      s->SetGain(volume_);
      s->SetIsMusic(music_);
      play_id_ = s->Play(sound_->GetSoundData());
      playing_ = true;
      s->End();
    }
  }
  if (positional_ && position_dirty_ && playing_) {
    millisecs_t t = g_core->AppTimeMillisecs();
    if (t - last_position_update_time_ > 100) {
      base::AudioSource* s = g_base->audio->SourceBeginExisting(play_id_, 107);
      if (s) {
        s->SetPosition(position_[0], position_[1], position_[2]);
        s->End();
      }
      last_position_update_time_ = t;
      position_dirty_ = false;
    }
  }
}

}  // namespace ballistica::scene_v1
