// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_GRAPHICS_SUPPORT_RENDER_COMMAND_BUFFER_H_
#define BALLISTICA_BASE_GRAPHICS_SUPPORT_RENDER_COMMAND_BUFFER_H_

#include <vector>

#include "ballistica/base/assets/texture_asset.h"
#include "ballistica/base/graphics/mesh/mesh.h"
#include "ballistica/base/graphics/support/frame_def.h"
#include "ballistica/shared/ballistica.h"
#include "ballistica/shared/math/matrix44f.h"

namespace ballistica::base {

class RenderCommandBuffer {
 public:
  // IMPORTANT: make sure to update has_draw_commands with any new
  // ones added here.
  enum class Command {
    kEnd,
    kShader,
    kDrawMeshAsset,
    kDrawMeshAssetInstanced,
    kDrawMesh,
    kDrawScreenQuad,
    kScissorPush,
    kScissorPop,
    kPushTransform,
    kPopTransform,
    kTranslate2,
    kTranslate3,
    kCursorTranslate,
    kScaleUniform,
    kTranslateToProjectedPoint,
#if BA_VR_BUILD
    kTransformToRightHand,
    kTransformToLeftHand,
    kTransformToHead,
#endif
    kScale2,
    kScale3,
    kRotate,
    kMultMatrix,
    kFlipCullFace,
    kSimpleComponentInlineColor,
    kObjectComponentInlineColor,
    kObjectComponentInlineAddColor,
    kBeginDebugDrawTriangles,
    kBeginDebugDrawLines,
    kEndDebugDraw,
    kDebugDrawVertex3
  };

  RenderCommandBuffer() = default;
  void PutCommand(Command c) {
    assert(!finalized_);
    commands_.push_back(c);
  }

  void PutFloat(float val) {
    assert(!finalized_);
    fvals_.push_back(val);
  }

  void PutFloats(float f1, float f2) {
    assert(!finalized_);
    int s = static_cast<int>(fvals_.size());
    fvals_.resize(fvals_.size() + 2);
    float* f = &(fvals_[s]);
    *f++ = f1;
    *f = f2;
  }

  void PutFloats(float f1, float f2, float f3) {
    assert(!finalized_);
    int s = static_cast<int>(fvals_.size());
    fvals_.resize(fvals_.size() + 3);
    float* f = &(fvals_[s]);
    *f++ = f1;
    *f++ = f2;
    *f = f3;
  }

  void PutFloats(float f1, float f2, float f3, float f4) {
    assert(!finalized_);
    int s = static_cast<int>(fvals_.size());
    fvals_.resize(fvals_.size() + 4);
    float* f = &(fvals_[s]);
    *f++ = f1;
    *f++ = f2;
    *f++ = f3;
    *f = f4;
  }

  void PutFloats(float f1, float f2, float f3, float f4, float f5) {
    assert(!finalized_);
    int s = static_cast<int>(fvals_.size());
    fvals_.resize(fvals_.size() + 5);
    float* f = &(fvals_[s]);
    *f++ = f1;
    *f++ = f2;
    *f++ = f3;
    *f++ = f4;
    *f = f5;
  }

  void PutFloats(float f1, float f2, float f3, float f4, float f5, float f6) {
    assert(!finalized_);
    int s = static_cast<int>(fvals_.size());
    fvals_.resize(fvals_.size() + 6);
    float* f = &(fvals_[s]);
    *f++ = f1;
    *f++ = f2;
    *f++ = f3;
    *f++ = f4;
    *f++ = f5;
    *f = f6;
  }

  void PutFloats(float f1, float f2, float f3, float f4, float f5, float f6,
                 float f7) {
    assert(!finalized_);
    int s = static_cast<int>(fvals_.size());
    fvals_.resize(fvals_.size() + 7);
    float* f = &(fvals_[s]);
    *f++ = f1;
    *f++ = f2;
    *f++ = f3;
    *f++ = f4;
    *f++ = f5;
    *f++ = f6;
    *f = f7;
  }

  void PutFloats(float f1, float f2, float f3, float f4, float f5, float f6,
                 float f7, float f8) {
    assert(!finalized_);
    int s = static_cast<int>(fvals_.size());
    fvals_.resize(fvals_.size() + 8);
    float* f = &(fvals_[s]);
    *f++ = f1;
    *f++ = f2;
    *f++ = f3;
    *f++ = f4;
    *f++ = f5;
    *f++ = f6;
    *f++ = f7;
    *f = f8;
  }

  void PutFloats(float f1, float f2, float f3, float f4, float f5, float f6,
                 float f7, float f8, float f9) {
    assert(!finalized_);
    int s = static_cast<int>(fvals_.size());
    fvals_.resize(fvals_.size() + 9);
    float* f = &(fvals_[s]);
    *f++ = f1;
    *f++ = f2;
    *f++ = f3;
    *f++ = f4;
    *f++ = f5;
    *f++ = f6;
    *f++ = f7;
    *f++ = f8;
    *f = f9;
  }

  void PutFloats(float f1, float f2, float f3, float f4, float f5, float f6,
                 float f7, float f8, float f9, float f10) {
    assert(!finalized_);
    int s = static_cast<int>(fvals_.size());
    fvals_.resize(fvals_.size() + 10);
    float* f = &(fvals_[s]);
    *f++ = f1;
    *f++ = f2;
    *f++ = f3;
    *f++ = f4;
    *f++ = f5;
    *f++ = f6;
    *f++ = f7;
    *f++ = f8;
    *f++ = f9;
    *f = f10;
  }

  void PutFloats(float f1, float f2, float f3, float f4, float f5, float f6,
                 float f7, float f8, float f9, float f10, float f11,
                 float f12) {
    assert(!finalized_);
    int s = static_cast<int>(fvals_.size());
    fvals_.resize(fvals_.size() + 12);
    float* f = &(fvals_[s]);
    *f++ = f1;
    *f++ = f2;
    *f++ = f3;
    *f++ = f4;
    *f++ = f5;
    *f++ = f6;
    *f++ = f7;
    *f++ = f8;
    *f++ = f9;
    *f++ = f10;
    *f++ = f11;
    *f = f12;
  }

  void PutFloats(float f1, float f2, float f3, float f4, float f5, float f6,
                 float f7, float f8, float f9, float f10, float f11, float f12,
                 float f13, float f14, float f15) {
    assert(!finalized_);
    int s = static_cast<int>(fvals_.size());
    fvals_.resize(fvals_.size() + 15);
    float* f = &(fvals_[s]);
    *f++ = f1;
    *f++ = f2;
    *f++ = f3;
    *f++ = f4;
    *f++ = f5;
    *f++ = f6;
    *f++ = f7;
    *f++ = f8;
    *f++ = f9;
    *f++ = f10;
    *f++ = f11;
    *f++ = f12;
    *f++ = f13;
    *f++ = f14;
    *f = f15;
  }

  void PutFloatArray16(const float* f_in) {
    assert(!finalized_);
    int s = static_cast<int>(fvals_.size());
    fvals_.resize(fvals_.size() + 16);
    float* f = &(fvals_[s]);
    memcpy(f, f_in, sizeof(float) * 16);
  }

  void PutMatrices(const std::vector<Matrix44f>& mats) {
    assert(!finalized_);
    static_assert(sizeof(Matrix44f[2]) == sizeof(float[16][2]));
    ivals_.push_back(static_cast<int>(mats.size()));
    int s = static_cast<int>(fvals_.size());
    int f_count = static_cast<int>(16 * mats.size());
    fvals_.resize(fvals_.size() + f_count);
    float* f = &(fvals_[s]);
    const float* f_in = mats[0].m;
    memcpy(f, f_in, sizeof(float) * f_count);
  }

  void PutInt(int val) {
    assert(!finalized_);
    ivals_.push_back(val);
  }

  void PutMeshAsset(MeshAsset* mesh) {
    assert(frame_def_);
    assert(!finalized_);
    frame_def_->AddComponent(Object::Ref<Asset>(mesh));
    meshes_.push_back(mesh);
  }

  void PutTexture(TextureAsset* texture) {
    assert(frame_def_);
    assert(!finalized_);
    frame_def_->AddComponent(Object::Ref<Asset>(texture));
    textures_.push_back(texture);
  }

  void PutTexture(const Object::Ref<TextureAsset>& texture) {
    assert(texture.Exists());
    PutTexture(texture.Get());
  }

  void PutCubeMapTexture(TextureAsset* texture) {
    assert(frame_def_);
    assert(!finalized_);
    frame_def_->AddComponent(Object::Ref<Asset>(texture));
    textures_.push_back(texture);
  }

  void PutMeshData(MeshData* mesh_data) {
    assert(!finalized_);
    mesh_datas_.push_back(mesh_data);
  }

  // Return next item.
  auto GetCommand() -> Command {
    assert(finalized_);
    assert(commands_index_ <= commands_.size());
    return (commands_index_ == commands_.size()) ? Command::kEnd
                                                 : commands_[commands_index_++];
  }

  auto GetInt() -> int {
    assert(finalized_);
    assert(ivals_index_ < ivals_.size());
    return ivals_[ivals_index_++];
  }

  auto GetFloat() -> float {
    assert(finalized_);
    assert(fvals_index_ < fvals_.size());
    return fvals_[fvals_index_++];
  }

  void GetFloats(float* f1, float* f2) {
    assert(finalized_);
    assert(fvals_index_ + 2 <= fvals_.size());
    *f1 = fvals_[fvals_index_++];
    *f2 = fvals_[fvals_index_++];
  }

  void GetFloats(float* f1, float* f2, float* f3) {
    assert(finalized_);
    assert(fvals_index_ + 3 <= fvals_.size());
    *f1 = fvals_[fvals_index_++];
    *f2 = fvals_[fvals_index_++];
    *f3 = fvals_[fvals_index_++];
  }

  void GetFloats(float* f1, float* f2, float* f3, float* f4) {
    assert(finalized_);
    assert(fvals_index_ + 4 <= fvals_.size());
    *f1 = fvals_[fvals_index_++];
    *f2 = fvals_[fvals_index_++];
    *f3 = fvals_[fvals_index_++];
    *f4 = fvals_[fvals_index_++];
  }

  void GetFloats(float* f1, float* f2, float* f3, float* f4, float* f5) {
    assert(finalized_);
    assert(fvals_index_ + 5 <= fvals_.size());
    *f1 = fvals_[fvals_index_++];
    *f2 = fvals_[fvals_index_++];
    *f3 = fvals_[fvals_index_++];
    *f4 = fvals_[fvals_index_++];
    *f5 = fvals_[fvals_index_++];
  }

  void GetFloats(float* f1, float* f2, float* f3, float* f4, float* f5,
                 float* f6) {
    assert(finalized_);
    assert(fvals_index_ + 6 <= fvals_.size());
    *f1 = fvals_[fvals_index_++];
    *f2 = fvals_[fvals_index_++];
    *f3 = fvals_[fvals_index_++];
    *f4 = fvals_[fvals_index_++];
    *f5 = fvals_[fvals_index_++];
    *f6 = fvals_[fvals_index_++];
  }

  void GetFloats(float* f1, float* f2, float* f3, float* f4, float* f5,
                 float* f6, float* f7) {
    assert(finalized_);
    assert(fvals_index_ + 7 <= fvals_.size());
    *f1 = fvals_[fvals_index_++];
    *f2 = fvals_[fvals_index_++];
    *f3 = fvals_[fvals_index_++];
    *f4 = fvals_[fvals_index_++];
    *f5 = fvals_[fvals_index_++];
    *f6 = fvals_[fvals_index_++];
    *f7 = fvals_[fvals_index_++];
  }

  void GetFloats(float* f1, float* f2, float* f3, float* f4, float* f5,
                 float* f6, float* f7, float* f8) {
    assert(finalized_);
    assert(fvals_index_ + 8 <= fvals_.size());
    *f1 = fvals_[fvals_index_++];
    *f2 = fvals_[fvals_index_++];
    *f3 = fvals_[fvals_index_++];
    *f4 = fvals_[fvals_index_++];
    *f5 = fvals_[fvals_index_++];
    *f6 = fvals_[fvals_index_++];
    *f7 = fvals_[fvals_index_++];
    *f8 = fvals_[fvals_index_++];
  }

  void GetFloats(float* f1, float* f2, float* f3, float* f4, float* f5,
                 float* f6, float* f7, float* f8, float* f9) {
    assert(finalized_);
    assert(fvals_index_ + 9 <= fvals_.size());
    *f1 = fvals_[fvals_index_++];
    *f2 = fvals_[fvals_index_++];
    *f3 = fvals_[fvals_index_++];
    *f4 = fvals_[fvals_index_++];
    *f5 = fvals_[fvals_index_++];
    *f6 = fvals_[fvals_index_++];
    *f7 = fvals_[fvals_index_++];
    *f8 = fvals_[fvals_index_++];
    *f9 = fvals_[fvals_index_++];
  }

  void GetFloats(float* f1, float* f2, float* f3, float* f4, float* f5,
                 float* f6, float* f7, float* f8, float* f9, float* f10) {
    assert(finalized_);
    assert(fvals_index_ + 10 <= fvals_.size());
    *f1 = fvals_[fvals_index_++];
    *f2 = fvals_[fvals_index_++];
    *f3 = fvals_[fvals_index_++];
    *f4 = fvals_[fvals_index_++];
    *f5 = fvals_[fvals_index_++];
    *f6 = fvals_[fvals_index_++];
    *f7 = fvals_[fvals_index_++];
    *f8 = fvals_[fvals_index_++];
    *f9 = fvals_[fvals_index_++];
    *f10 = fvals_[fvals_index_++];
  }

  void GetFloats(float* f1, float* f2, float* f3, float* f4, float* f5,
                 float* f6, float* f7, float* f8, float* f9, float* f10,
                 float* f11, float* f12) {
    assert(finalized_);
    assert(fvals_index_ + 12 <= fvals_.size());
    *f1 = fvals_[fvals_index_++];
    *f2 = fvals_[fvals_index_++];
    *f3 = fvals_[fvals_index_++];
    *f4 = fvals_[fvals_index_++];
    *f5 = fvals_[fvals_index_++];
    *f6 = fvals_[fvals_index_++];
    *f7 = fvals_[fvals_index_++];
    *f8 = fvals_[fvals_index_++];
    *f9 = fvals_[fvals_index_++];
    *f10 = fvals_[fvals_index_++];
    *f11 = fvals_[fvals_index_++];
    *f12 = fvals_[fvals_index_++];
  }

  void GetFloats(float* f1, float* f2, float* f3, float* f4, float* f5,
                 float* f6, float* f7, float* f8, float* f9, float* f10,
                 float* f11, float* f12, float* f13, float* f14, float* f15) {
    assert(finalized_);
    assert(fvals_index_ + 15 <= fvals_.size());
    *f1 = fvals_[fvals_index_++];
    *f2 = fvals_[fvals_index_++];
    *f3 = fvals_[fvals_index_++];
    *f4 = fvals_[fvals_index_++];
    *f5 = fvals_[fvals_index_++];
    *f6 = fvals_[fvals_index_++];
    *f7 = fvals_[fvals_index_++];
    *f8 = fvals_[fvals_index_++];
    *f9 = fvals_[fvals_index_++];
    *f10 = fvals_[fvals_index_++];
    *f11 = fvals_[fvals_index_++];
    *f12 = fvals_[fvals_index_++];
    *f13 = fvals_[fvals_index_++];
    *f14 = fvals_[fvals_index_++];
    *f15 = fvals_[fvals_index_++];
  }

  auto GetMatrix() -> Matrix44f* {
    assert(finalized_);
    assert(fvals_index_ + 16 <= fvals_.size());
    static_assert(sizeof(Matrix44f) == sizeof(float[16]));
    auto* m = reinterpret_cast<Matrix44f*>(&fvals_[fvals_index_]);
    fvals_index_ += 16;
    return m;
  }

  auto GetMatrices(int* count) -> Matrix44f* {
    assert(finalized_);
    assert(ivals_index_ < ivals_.size());
    *count = ivals_[ivals_index_++];
    int f_count = 16 * (*count);
    assert(fvals_index_ + f_count <= fvals_.size());
    static_assert(sizeof(Matrix44f[2]) == sizeof(float[16][2]));
    auto* m = reinterpret_cast<Matrix44f*>(&fvals_[fvals_index_]);
    fvals_index_ += f_count;
    return m;
  }

  auto GetMesh() -> const MeshAsset* {
    assert(finalized_);
    assert(meshes_index_ < meshes_.size());
    return meshes_[meshes_index_++];
  }

  template <typename T>
  auto GetMeshRendererData() -> T* {
    assert(finalized_);
    assert(mesh_datas_index_ < mesh_datas_.size());
    T* m;
    m = static_cast<T*>(mesh_datas_[mesh_datas_index_]->renderer_data());
    assert(m);
    assert(
        m == dynamic_cast<T*>(mesh_datas_[mesh_datas_index_]->renderer_data()));
    mesh_datas_index_++;
    return m;
  }

  auto GetTexture() -> const TextureAsset* {
    assert(finalized_);
    assert(textures_index_ < textures_.size());
    return textures_[textures_index_++];
  }

  void Reset() {
    commands_.resize(0);
    fvals_.resize(0);
    ivals_.resize(0);
    meshes_.resize(0);
    textures_.resize(0);
    mesh_datas_.resize(0);
    finalized_ = false;
  }

  // Call once done writing to buffer.
  void Finalize() {
    assert(!finalized_);
    finalized_ = true;
  }

  // Set up iterators to read back data.
  void ReadBegin() {
    assert(finalized_);
    commands_index_ = 0;
    fvals_index_ = 0;
    ivals_index_ = 0;
    meshes_index_ = 0;
    textures_index_ = 0;
    mesh_datas_index_ = 0;
  }
  auto has_draw_commands() const -> bool {
    for (auto& command : commands_) {
      switch (command) {
        case Command::kDrawMeshAsset:
        case Command::kDrawMeshAssetInstanced:
        case Command::kDrawMesh:
        case Command::kDrawScreenQuad:
          return true;
        default:
          break;
      }
    }
    return false;
  }

  // Sanity check: Makes sure all buffer iterators are at their end.
  auto IsEmpty() -> bool {
    return (
        (commands_index_ == commands_.size()) && (fvals_index_ == fvals_.size())
        && (ivals_index_ == ivals_.size()) && (meshes_index_ == meshes_.size())
        && (textures_index_ == textures_.size())
        && (mesh_datas_index_ == mesh_datas_.size()));
  }

  auto frame_def() const -> FrameDef* {
    assert(frame_def_);
    return frame_def_;
  }

  void set_frame_def(FrameDef* f) { frame_def_ = f; }

 private:
  std::vector<Command> commands_;
  std::vector<float> fvals_;
  std::vector<int> ivals_;
  std::vector<MeshAsset*> meshes_{};
  std::vector<TextureAsset*> textures_{};
  std::vector<MeshData*> mesh_datas_{};
  unsigned int commands_index_{};
  unsigned int fvals_index_{};
  unsigned int ivals_index_{};
  unsigned int meshes_index_{};
  unsigned int textures_index_{};
  unsigned int mesh_datas_index_{};
  bool finalized_{};
  FrameDef* frame_def_{};
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_GRAPHICS_SUPPORT_RENDER_COMMAND_BUFFER_H_
