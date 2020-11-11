// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene/node/node_attribute_connection.h"

#include <string>

#include "ballistica/scene/node/node.h"
#include "ballistica/scene/node/node_attribute.h"
#include "ballistica/scene/node/node_type.h"

namespace ballistica {

void NodeAttributeConnection::Update() {
  assert(src_node.exists() && dst_node.exists());
  auto* src_node_p{src_node.get()};

  // We no longer update after errors now.
  // (the constant stream of exceptions slows things down too much)
  if (have_error) {
    return;
  }

  try {
    // Pull data from the src to match the dst type.
    NodeAttributeUnbound* src_attr =
        src_node->type()->GetAttribute(src_attr_index);
    assert(src_attr);
    NodeAttributeUnbound* dst_attr =
        dst_node->type()->GetAttribute(dst_attr_index);
    assert(dst_attr);
    switch (dst_attr->type()) {
      case NodeAttributeType::kFloat:
        dst_attr->Set(dst_node.get(), src_attr->GetAsFloat(src_node_p));
        break;
      case NodeAttributeType::kInt:
        dst_attr->Set(dst_node.get(), src_attr->GetAsInt(src_node_p));
        break;
      case NodeAttributeType::kBool:
        dst_attr->Set(dst_node.get(), src_attr->GetAsBool(src_node_p));
        break;
      case NodeAttributeType::kString:
        dst_attr->Set(dst_node.get(), src_attr->GetAsString(src_node_p));
        break;
      case NodeAttributeType::kIntArray:
        dst_attr->Set(dst_node.get(), src_attr->GetAsInts(src_node_p));
        break;
      case NodeAttributeType::kFloatArray:
        dst_attr->Set(dst_node.get(), src_attr->GetAsFloats(src_node_p));
        break;
      case NodeAttributeType::kNode:
        dst_attr->Set(dst_node.get(), src_attr->GetAsNode(src_node_p));
        break;
      case NodeAttributeType::kNodeArray:
        dst_attr->Set(dst_node.get(), src_attr->GetAsNodes(src_node_p));
        break;
      case NodeAttributeType::kPlayer:
        dst_attr->Set(dst_node.get(), src_attr->GetAsPlayer(src_node_p));
        break;
      case NodeAttributeType::kMaterialArray:
        dst_attr->Set(dst_node.get(), src_attr->GetAsMaterials(src_node_p));
        break;
      case NodeAttributeType::kTexture:
        dst_attr->Set(dst_node.get(), src_attr->GetAsTexture(src_node_p));
        break;
      case NodeAttributeType::kTextureArray:
        dst_attr->Set(dst_node.get(), src_attr->GetAsTextures(src_node_p));
        break;
      case NodeAttributeType::kSound:
        dst_attr->Set(dst_node.get(), src_attr->GetAsSound(src_node_p));
        break;
      case NodeAttributeType::kSoundArray:
        dst_attr->Set(dst_node.get(), src_attr->GetAsSounds(src_node_p));
        break;
      case NodeAttributeType::kModel:
        dst_attr->Set(dst_node.get(), src_attr->GetAsModel(src_node_p));
        break;
      case NodeAttributeType::kModelArray:
        dst_attr->Set(dst_node.get(), src_attr->GetAsModels(src_node_p));
        break;
      case NodeAttributeType::kCollideModel:
        dst_attr->Set(dst_node.get(), src_attr->GetAsCollideModel(src_node_p));
        break;
      case NodeAttributeType::kCollideModelArray:
        dst_attr->Set(dst_node.get(), src_attr->GetAsCollideModels(src_node_p));
        break;
      default:
        throw Exception("FIXME: unimplemented for attr type: '"
                        + dst_attr->GetTypeName() + "'");
    }
  } catch (const std::exception& e) {
    // Print errors only once per connection to avoid overwhelming the logs.
    // (though we now stop updating after an error so this is redundant).
    if (!have_error) {
      have_error = true;
      NodeAttributeUnbound* src_attr =
          src_node->type()->GetAttribute(src_attr_index);
      NodeAttributeUnbound* dst_attr =
          dst_node->type()->GetAttribute(dst_attr_index);
      Log("ERROR: attribute connection update: " + std::string(e.what())
          + "; srcAttr='" + src_attr->name() + "', src_node='"
          + src_node->type()->name() + "', srcNodeName='" + src_node->label()
          + "', dstAttr='" + dst_attr->name() + "', dstNode='"
          + dst_node->type()->name() + "', dstNodeName='" + dst_node->label()
          + "'");
    }
  }
}
}  // namespace ballistica
