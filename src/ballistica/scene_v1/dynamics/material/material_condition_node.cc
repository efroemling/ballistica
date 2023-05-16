// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/dynamics/material/material_condition_node.h"

#include "ballistica/scene_v1/dynamics/material/material.h"
#include "ballistica/scene_v1/support/client_session.h"
#include "ballistica/scene_v1/support/session_stream.h"
#include "ballistica/shared/generic/utils.h"

namespace ballistica::scene_v1 {

auto MaterialConditionNode::GetFlattenedSize() -> size_t {
  // we need one byte for our opmode
  // plus the condition byte and either 0, 1, or 2 values depending on our
  // condition if we're a leaf node, otherwise add the size of our children
  size_t size = 1;
  if (opmode == OpMode::LEAF_NODE) {
    size += 1 + sizeof(uint32_t) * GetValueCount();
  } else {
    size += (left_child->GetFlattenedSize() + right_child->GetFlattenedSize());
  }
  return size;
}

void MaterialConditionNode::Flatten(char** buffer,
                                    SessionStream* output_stream) {
  // Pack our opmode in. Or if we're a leaf note stick zero in.
  Utils::EmbedInt8(buffer, static_cast<int8_t>(opmode));
  if (opmode == OpMode::LEAF_NODE) {
    Utils::EmbedInt8(buffer, static_cast<int8_t>(cond));
    switch (GetValueCount()) {
      case 0:
        break;
      case 1: {
        // If this condition uses the material val1, embed its stream ID
        if (cond == MaterialCondition::kDstIsMaterial
            || cond == MaterialCondition::kDstNotMaterial) {
          Utils::EmbedInt32NBO(
              buffer, static_cast_check_fit<int32_t>(
                          output_stream->GetMaterialID(val1_material.Get())));
        } else {
          Utils::EmbedInt32NBO(buffer, val1);
        }
        break;
      }
      case 2:
        Utils::EmbedInt32NBO(buffer, val1);
        Utils::EmbedInt32NBO(buffer, val2);
        break;
      default:
        throw Exception();
    }
  } else {
    left_child->Flatten(buffer, output_stream);
    right_child->Flatten(buffer, output_stream);
  }
}

void MaterialConditionNode::Restore(const char** buffer, ClientSession* cs) {
  opmode = static_cast<OpMode>(Utils::ExtractInt8(buffer));
  if (opmode == OpMode::LEAF_NODE) {
    cond = static_cast<MaterialCondition>(Utils::ExtractInt8(buffer));
    int val_count = GetValueCount();
    switch (val_count) {
      case 0:
        break;
      case 1:
        if (cond == MaterialCondition::kDstIsMaterial
            || cond == MaterialCondition::kDstNotMaterial) {
          val1_material = cs->GetMaterial(Utils::ExtractInt32NBO(buffer));
        } else {
          val1 = Utils::ExtractInt32NBO(buffer);
        }
        break;
      case 2:
        val1 = Utils::ExtractInt32NBO(buffer);
        val2 = Utils::ExtractInt32NBO(buffer);
        break;

// Currently not reachable, but guarding in case GetValueCount changes.
#pragma clang diagnostic push
#pragma ide diagnostic ignored "UnreachableCode"
      default:
        throw Exception();
#pragma clang diagnostic pop
    }
  } else {
    // not a leaf node - make ourself some children
    left_child = Object::New<MaterialConditionNode>();
    left_child->Restore(buffer, cs);
    right_child = Object::New<MaterialConditionNode>();
    right_child->Restore(buffer, cs);
  }
}

}  // namespace ballistica::scene_v1
