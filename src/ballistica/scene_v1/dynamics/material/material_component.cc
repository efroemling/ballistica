// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/dynamics/material/material_component.h"

#include <vector>

#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging.h"
#include "ballistica/scene_v1/dynamics/material/impact_sound_material_action.h"
#include "ballistica/scene_v1/dynamics/material/material.h"
#include "ballistica/scene_v1/dynamics/material/material_condition_node.h"
#include "ballistica/scene_v1/dynamics/material/material_context.h"
#include "ballistica/scene_v1/dynamics/material/node_message_material_action.h"
#include "ballistica/scene_v1/dynamics/material/node_mod_material_action.h"
#include "ballistica/scene_v1/dynamics/material/part_mod_material_action.h"
#include "ballistica/scene_v1/dynamics/material/roll_sound_material_action.h"
#include "ballistica/scene_v1/dynamics/material/skid_sound_material_action.h"
#include "ballistica/scene_v1/dynamics/material/sound_material_action.h"
#include "ballistica/scene_v1/dynamics/part.h"
#include "ballistica/scene_v1/node/node.h"

namespace ballistica::scene_v1 {

MaterialComponent::MaterialComponent() {}

MaterialComponent::MaterialComponent(
    const Object::Ref<MaterialConditionNode>& conditions_in,
    const std::vector<Object::Ref<MaterialAction> >& actions_in)
    : conditions(conditions_in), actions(actions_in) {}

MaterialComponent::~MaterialComponent() {}

auto MaterialComponent::eval_conditions(
    const Object::Ref<MaterialConditionNode>& condition, const Material& c,
    const Part* part, const Part* opposing_part, const MaterialContext& s)
    -> bool {
  // If there's no condition, succeed.
  if (!condition.exists()) {
    return true;
  }

  // If we're a leaf node, evaluate.
  if (condition->opmode == MaterialConditionNode::OpMode::LEAF_NODE) {
    switch (condition->cond) {
      case MaterialCondition::kTrue:
        return true;
      case MaterialCondition::kFalse:
        return false;
      case MaterialCondition::kDstIsMaterial:
        return (
            (opposing_part->ContainsMaterial(condition->val1_material.get())));
      case MaterialCondition::kDstNotMaterial:
        return (
            !(opposing_part->ContainsMaterial(condition->val1_material.get())));
      case MaterialCondition::kDstIsPart:
        return ((opposing_part->id() == condition->val1));
      case MaterialCondition::kDstNotPart:
        return opposing_part->id() != condition->val1;
      case MaterialCondition::kSrcDstSameMaterial:
        return ((opposing_part->ContainsMaterial(&c)));
      case MaterialCondition::kSrcDstDiffMaterial:
        return (!(opposing_part->ContainsMaterial(&c)));
      case MaterialCondition::kSrcDstSameNode:
        return ((opposing_part->node() == part->node()));
      case MaterialCondition::kSrcDstDiffNode:
        return opposing_part->node() != part->node();
      case MaterialCondition::kSrcYoungerThan:
        return part->GetAge() < condition->val1;
      case MaterialCondition::kSrcOlderThan:
        return ((part->GetAge() >= condition->val1));
      case MaterialCondition::kDstYoungerThan:
        return opposing_part->GetAge() < condition->val1;
      case MaterialCondition::kDstOlderThan:
        return ((opposing_part->GetAge() >= condition->val1));
      case MaterialCondition::kCollidingDstNode:
        return (part->IsCollidingWith(opposing_part->node()->id()));
      case MaterialCondition::kNotCollidingDstNode:
        return (!(part->IsCollidingWith(opposing_part->node()->id())));
      case MaterialCondition::kEvalColliding:
        return s.collide && s.node_collide;
      case MaterialCondition::kEvalNotColliding:
        return (!s.collide || !s.node_collide);
      default:
        throw Exception();
    }
  } else {
    // A trunk node; eval our left and right children and return
    // the boolean operation between them.
    assert(condition->left_child.exists());
    assert(condition->right_child.exists());

    bool left_result =
        eval_conditions(condition->left_child, c, part, opposing_part, s);

    // In some cases we don't even need to calc the right result.
    switch (condition->opmode) {
      case MaterialConditionNode::OpMode::AND_OPERATOR:
        // AND can't succeed if left is false.
        if (!left_result) return false;
        break;
      case MaterialConditionNode::OpMode::OR_OPERATOR:
        // OR has succeeded if we've got a true.
        if (left_result) return true;
        break;
      default:
        break;
    }

    bool right_result =
        eval_conditions(condition->right_child, c, part, opposing_part, s);

    switch (condition->opmode) {
      case MaterialConditionNode::OpMode::AND_OPERATOR:
        return left_result && right_result;
      case MaterialConditionNode::OpMode::OR_OPERATOR:
        return left_result || right_result;
      case MaterialConditionNode::OpMode::XOR_OPERATOR:
        return ((left_result && !right_result)
                || (!left_result && right_result));
      default:
        throw Exception();
    }
  }
}

auto MaterialComponent::GetFlattenedSize() -> size_t {
  size_t size{};

  // Embed a byte telling whether we have conditions or not.
  size += 1;

  // Embed the size of the condition tree.
  if (conditions.exists()) {
    size += conditions->GetFlattenedSize();
  }

  // An int32 for the action count.
  size += sizeof(uint32_t);

  // Plus the total size of all actions.
  for (auto& action : actions) {
    if (action->IsNeededOnClient()) {
      // 1 type byte plus the action's size.
      size += 1 + action->GetFlattenedSize();
    }
  }
  return size;
}

void MaterialComponent::Flatten(char** buffer, SessionStream* output_stream) {
  // Embed a byte telling whether we have conditions.
  Utils::EmbedInt8(buffer, conditions.exists());

  // If we have conditions, have the tree embed itself.
  if (conditions.exists()) {
    conditions->Flatten(buffer, output_stream);
  }

  // Embed our action count; we have to manually go through and count
  // actions that we'll be sending.
  int count = 0;
  for (auto& action : actions) {
    if ((*action).IsNeededOnClient()) {
      assert((*action).GetType() != MaterialAction::Type::NODE_USER_MESSAGE);
      count++;
    }
  }
  Utils::EmbedInt32NBO(buffer, count);

  // Embed our actions.
  for (auto& action : actions) {
    if ((*action).IsNeededOnClient()) {
      Utils::EmbedInt8(buffer, static_cast<int8_t>((*action).GetType()));
      (*action).Flatten(buffer, output_stream);
    }
  }
}

void MaterialComponent::Restore(const char** buffer, ClientSession* cs) {
  // Pull the byte telling us if we have conditions.
  bool haveConditions = Utils::ExtractInt8(buffer);

  // If there's conditions, create a condition node and have it extract itself.
  if (haveConditions) {
    conditions = Object::New<MaterialConditionNode>();
    conditions->Restore(buffer, cs);
  }

  // Pull our action count.
  int action_count = Utils::ExtractInt32NBO(buffer);

  // Restore all actions.
  for (int i = 0; i < action_count; i++) {
    // Pull the action type.
    auto type = static_cast<MaterialAction::Type>(Utils::ExtractInt8(buffer));
    Object::Ref<MaterialAction> action;
    switch (type) {
      case MaterialAction::Type::NODE_MESSAGE:
        action = Object::New<NodeMessageMaterialAction>();
        break;
      case MaterialAction::Type::SOUND:
        action = Object::New<SoundMaterialAction>();
        break;
      case MaterialAction::Type::IMPACT_SOUND:
        action = Object::New<ImpactSoundMaterialAction>();
        break;
      case MaterialAction::Type::SKID_SOUND:
        action = Object::New<SkidSoundMaterialAction>();
        break;
      case MaterialAction::Type::ROLL_SOUND:
        action = Object::New<RollSoundMaterialAction>();
        break;
      case MaterialAction::Type::PART_MOD:
        action = Object::New<PartModMaterialAction>();
        break;
      case MaterialAction::Type::NODE_MOD:
        action = Object::New<NodeModMaterialAction>();
        break;
      default:
        g_core->logging->Log(LogName::kBa, LogLevel::kError,
                             "Invalid material action: '"
                                 + std::to_string(static_cast<int>(type))
                                 + "'.");
        throw Exception();
    }
    action->Restore(buffer, cs);
    actions.push_back(action);
  }
}

void MaterialComponent::Apply(MaterialContext* context, const Part* src_part,
                              const Part* dst_part) {
  assert(context && src_part && dst_part);
  for (auto& action : actions) {
    (*action).Apply(context, src_part, dst_part, action);
  }
}

}  // namespace ballistica::scene_v1
