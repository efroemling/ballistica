// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene/v1/scene_v1.h"

#include "ballistica/app/app.h"
#include "ballistica/scene/node/anim_curve_node.h"
#include "ballistica/scene/node/bomb_node.h"
#include "ballistica/scene/node/combine_node.h"
#include "ballistica/scene/node/explosion_node.h"
#include "ballistica/scene/node/flag_node.h"
#include "ballistica/scene/node/flash_node.h"
#include "ballistica/scene/node/globals_node.h"
#include "ballistica/scene/node/image_node.h"
#include "ballistica/scene/node/light_node.h"
#include "ballistica/scene/node/locator_node.h"
#include "ballistica/scene/node/math_node.h"
#include "ballistica/scene/node/null_node.h"
#include "ballistica/scene/node/player_node.h"
#include "ballistica/scene/node/region_node.h"
#include "ballistica/scene/node/scorch_node.h"
#include "ballistica/scene/node/session_globals_node.h"
#include "ballistica/scene/node/shield_node.h"
#include "ballistica/scene/node/sound_node.h"
#include "ballistica/scene/node/spaz_node.h"
#include "ballistica/scene/node/terrain_node.h"
#include "ballistica/scene/node/text_node.h"
#include "ballistica/scene/node/texture_sequence_node.h"
#include "ballistica/scene/node/time_display_node.h"

namespace ballistica {

static void SetupNodeMessageType(const std::string& name, NodeMessageType val,
                                 const std::string& format) {
  assert(g_app != nullptr);
  g_app->node_message_types[name] = val;
  assert(static_cast<int>(val) >= 0);
  if (g_app->node_message_formats.size() <= static_cast<size_t>(val)) {
    g_app->node_message_formats.resize(static_cast<size_t>(val) + 1);
  }
  g_app->node_message_formats[static_cast<size_t>(val)] = format;
}

SceneV1::SceneV1() {
  NodeType* node_types[] = {NullNode::InitType(),
                            GlobalsNode::InitType(),
                            SessionGlobalsNode::InitType(),
                            PropNode::InitType(),
                            FlagNode::InitType(),
                            BombNode::InitType(),
                            ExplosionNode::InitType(),
                            ShieldNode::InitType(),
                            LightNode::InitType(),
                            TextNode::InitType(),
                            AnimCurveNode::InitType(),
                            ImageNode::InitType(),
                            TerrainNode::InitType(),
                            MathNode::InitType(),
                            LocatorNode::InitType(),
                            PlayerNode::InitType(),
                            CombineNode::InitType(),
                            SoundNode::InitType(),
                            SpazNode::InitType(),
                            RegionNode::InitType(),
                            ScorchNode::InitType(),
                            FlashNode::InitType(),
                            TextureSequenceNode::InitType(),
                            TimeDisplayNode::InitType()};

  int next_type_id = 0;
  assert(g_app != nullptr);
  for (auto* t : node_types) {
    g_app->node_types[t->name()] = t;
    g_app->node_types_by_id[next_type_id] = t;
    t->set_id(next_type_id++);
  }

  // Types: I is 32 bit int, i is 16 bit int, c is 8 bit int,
  // F is 32 bit float, f is 16 bit float,
  // s is string, b is bool.
  SetupNodeMessageType("flash", NodeMessageType::kFlash, "");
  SetupNodeMessageType("footing", NodeMessageType::kFooting, "c");
  SetupNodeMessageType("impulse", NodeMessageType::kImpulse, "fffffffffifff");
  SetupNodeMessageType("kick_back", NodeMessageType::kKickback, "fffffff");
  SetupNodeMessageType("celebrate", NodeMessageType::kCelebrate, "i");
  SetupNodeMessageType("celebrate_l", NodeMessageType::kCelebrateL, "i");
  SetupNodeMessageType("celebrate_r", NodeMessageType::kCelebrateR, "i");
  SetupNodeMessageType("knockout", NodeMessageType::kKnockout, "f");
  SetupNodeMessageType("hurt_sound", NodeMessageType::kHurtSound, "");
  SetupNodeMessageType("picked_up", NodeMessageType::kPickedUp, "");
  SetupNodeMessageType("jump_sound", NodeMessageType::kJumpSound, "");
  SetupNodeMessageType("attack_sound", NodeMessageType::kAttackSound, "");
  SetupNodeMessageType("scream_sound", NodeMessageType::kScreamSound, "");
  SetupNodeMessageType("stand", NodeMessageType::kStand, "ffff");
}

}  // namespace ballistica
