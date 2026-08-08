// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_SUPPORT_REPLAY_WRITER_H_
#define BALLISTICA_SCENE_V1_SUPPORT_REPLAY_WRITER_H_

#include <cstdio>
#include <list>
#include <string>
#include <vector>

#include "ballistica/base/assets/assets_server.h"

namespace ballistica::scene_v1 {

class ReplayWriter : public base::AssetsServer::Processor {
 public:
  /// Protocol-version must be the version of the actual stream being
  /// recorded (the hosted protocol when recording our own host-session;
  /// the negotiated connection protocol when recording as a client) —
  /// NOT simply kProtocolVersionMax, since as a client we may be
  /// ingesting an older-protocol stream which gets written verbatim.
  explicit ReplayWriter(int protocol_version);
  void Finish();

  /// Provide the stream's declared asset-package table for the file
  /// HEADER listing (protocol 39+). A duplicate of what the stream
  /// itself declares up front, placed where lightweight consumers can
  /// read it without decompressing/parsing the stream (pre-playback
  /// content resolve, Watch-tab requirement display). Call from the
  /// logic thread once the table is known: host recordings know it at
  /// session creation; client recordings learn it when the baseline's
  /// declaration finishes parsing. First call wins; message writing is
  /// held until this arrives so the listing can prefix the stream.
  void SetAssetPackageTable(const std::vector<std::string>& table);

  void PushAddMessageToReplayCall(const std::vector<uint8_t>& message);

  void Process() override;

 private:
  void WriteReplayMessages_();
  void WriteAssetPackageListing_();
  int protocol_version_;
  std::list<std::vector<uint8_t> > replay_messages_;
  FILE* replay_out_file_{};
  size_t replay_bytes_written_{};
  size_t replay_message_bytes_{};
  std::vector<std::string> asset_package_table_;
  bool have_asset_package_table_{};
  bool listing_written_{};
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_SUPPORT_REPLAY_WRITER_H_
