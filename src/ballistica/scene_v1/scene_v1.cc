// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/scene_v1.h"

#include <list>
#include <string>
#include <unordered_map>

#include "ballistica/scene_v1/node/anim_curve_node.h"
#include "ballistica/scene_v1/node/bomb_node.h"
#include "ballistica/scene_v1/node/combine_node.h"
#include "ballistica/scene_v1/node/explosion_node.h"
#include "ballistica/scene_v1/node/flag_node.h"
#include "ballistica/scene_v1/node/flash_node.h"
#include "ballistica/scene_v1/node/globals_node.h"
#include "ballistica/scene_v1/node/image_node.h"
#include "ballistica/scene_v1/node/light_node.h"
#include "ballistica/scene_v1/node/locator_node.h"
#include "ballistica/scene_v1/node/math_node.h"
#include "ballistica/scene_v1/node/null_node.h"
#include "ballistica/scene_v1/node/player_node.h"
#include "ballistica/scene_v1/node/region_node.h"
#include "ballistica/scene_v1/node/scorch_node.h"
#include "ballistica/scene_v1/node/session_globals_node.h"
#include "ballistica/scene_v1/node/shield_node.h"
#include "ballistica/scene_v1/node/sound_node.h"
#include "ballistica/scene_v1/node/spaz_node.h"
#include "ballistica/scene_v1/node/terrain_node.h"
#include "ballistica/scene_v1/node/text_node.h"
#include "ballistica/scene_v1/node/texture_sequence_node.h"
#include "ballistica/scene_v1/node/time_display_node.h"
#include "ballistica/scene_v1/python/scene_v1_python.h"
#include "ballistica/scene_v1/support/huffman.h"
#include "ballistica/shared/generic/utils.h"

namespace ballistica::scene_v1 {

core::CoreFeatureSet* g_core{};
base::BaseFeatureSet* g_base{};
SceneV1FeatureSet* g_scene_v1{};

void SceneV1FeatureSet::OnModuleExec(PyObject* module) {
  // Ok, our feature-set's Python module is getting imported.
  // Like any normal Python module, we take this opportunity to
  // import/create the stuff we use.

  // Importing core should always be the first thing we do.
  // Various ballistica functionality will fail if this has not been done.
  assert(g_core == nullptr);
  g_core = core::CoreFeatureSet::Import();

  g_core->logging->Log(LogName::kBaLifecycle, LogLevel::kInfo,
                       "_bascenev1 exec begin");

  // Create our feature-set's C++ front-end.
  assert(g_scene_v1 == nullptr);
  g_scene_v1 = new SceneV1FeatureSet();

  // Store our C++ front-end with our Python module. This is what allows
  // other C++ code to 'import' our C++ front end and talk to us directly.
  g_scene_v1->StoreOnPythonModule(module);

  // Define our classes.
  g_scene_v1->python->AddPythonClasses(module);

  // Import any Python stuff we use into objs_.
  g_scene_v1->python->ImportPythonObjs();

  // Import any other C++ feature-set-front-ends we use.
  assert(g_base == nullptr);
  g_base = base::BaseFeatureSet::Import();

  g_core->logging->Log(LogName::kBaLifecycle, LogLevel::kInfo,
                       "_bascenev1 exec end");
}

SceneV1FeatureSet::SceneV1FeatureSet()
    : python{new SceneV1Python()}, huffman{new Huffman()} {
  NodeType* init_node_types[] = {NullNode::InitType(),
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

  int next_type_id{};
  for (auto* t : init_node_types) {
    node_types_[t->name()] = t;
    node_types_by_id_[next_type_id] = t;
    t->set_id(next_type_id++);
  }

  // Types: I is 32 bit int, i is 16 bit int, c is 8 bit int,
  // F is 32 bit float, f is 16 bit float,
  // s is string, b is bool.
  SetupNodeMessageType_("flash", NodeMessageType::kFlash, "");
  SetupNodeMessageType_("footing", NodeMessageType::kFooting, "c");
  SetupNodeMessageType_("impulse", NodeMessageType::kImpulse, "fffffffffifff");
  SetupNodeMessageType_("kick_back", NodeMessageType::kKickback, "fffffff");
  SetupNodeMessageType_("celebrate", NodeMessageType::kCelebrate, "i");
  SetupNodeMessageType_("celebrate_l", NodeMessageType::kCelebrateL, "i");
  SetupNodeMessageType_("celebrate_r", NodeMessageType::kCelebrateR, "i");
  SetupNodeMessageType_("knockout", NodeMessageType::kKnockout, "f");
  SetupNodeMessageType_("hurt_sound", NodeMessageType::kHurtSound, "");
  SetupNodeMessageType_("picked_up", NodeMessageType::kPickedUp, "");
  SetupNodeMessageType_("jump_sound", NodeMessageType::kJumpSound, "");
  SetupNodeMessageType_("attack_sound", NodeMessageType::kAttackSound, "");
  SetupNodeMessageType_("scream_sound", NodeMessageType::kScreamSound, "");
  SetupNodeMessageType_("stand", NodeMessageType::kStand, "ffff");
}

auto SceneV1FeatureSet::Import() -> SceneV1FeatureSet* {
  // Since we provide a native Python module, we piggyback our C++ front-end
  // on top of that. This way our C++ and Python dependencies are resolved
  // consistently no matter which side we are imported from.
  return ImportThroughPythonModule<SceneV1FeatureSet>("_bascenev1");
}

void SceneV1FeatureSet::Reset() {
  assert(g_base->InLogicThread());
  g_scene_v1->python->Reset();
}

void SceneV1FeatureSet::ResetRandomNames() {
  assert(g_base->InLogicThread());
  if (random_name_registry_ == nullptr) {
    return;
  }
  random_name_registry_->clear();
}

auto SceneV1FeatureSet::GetRandomName(const std::string& full_name)
    -> std::string {
  assert(g_base->InLogicThread());

  // Hmm; statically allocating this is giving some crashes on shutdown :-(
  if (random_name_registry_ == nullptr) {
    random_name_registry_ = new std::unordered_map<std::string, std::string>();
  }

  auto i = random_name_registry_->find(full_name);
  if (i == random_name_registry_->end()) {
    // Doesn't exist. Pull a random one and add it.
    // Refill the global list if its empty.
    if (default_names_.empty()) {
      const std::list<std::string>& random_name_list =
          Utils::GetRandomNameList();
      for (const auto& i2 : random_name_list) {
        default_names_.push_back(i2);
      }
    }

    // Ok now pull a random one off the list and assign it to us
    int index = static_cast<int>(rand() % default_names_.size());  // NOLINT
    auto i3 = default_names_.begin();
    for (int j = 0; j < index; j++) {
      i3++;
    }
    (*random_name_registry_)[full_name] = *i3;
    default_names_.erase(i3);
  }
  return (*random_name_registry_)[full_name];
}

void SceneV1FeatureSet::SetupNodeMessageType_(const std::string& name,
                                              NodeMessageType val,
                                              const std::string& format) {
  node_message_types_[name] = val;
  assert(static_cast<int>(val) >= 0);
  if (node_message_formats_.size() <= static_cast<size_t>(val)) {
    node_message_formats_.resize(static_cast<size_t>(val) + 1);
  }
  node_message_formats_[static_cast<size_t>(val)] = format;
}

}  // namespace ballistica::scene_v1
