# Scene Stream on the Wire

**Description:** How a hosting session's scene stream is framed, folded and delivered to 1.8 peers, and the fold-scope rule that keeps those encodings logic-neutral.

## The model this must not disturb

A host writes a stream of session commands (`SessionCommand`, in
`scene_v1.h`) as it runs: time steps, scene steps, node adds and attr
sets, connects, removals. Every client (and a replay) runs the same
commands in the same order, and the point in the stream at which a
command sits *is* its time: base time only advances on time-step
commands, and the client releases queued commands to its interpreter
on each time step (`ClientSession::AddCommand`), which is also what
its pacing (`ClientSessionNet::OnBaseTimeStepAdded`) counts.

Everything in this doc reduces bytes without changing that: no
command runs at a different client time, no time-step event appears
or disappears from the client's point of view, and the host's own
scene is never affected. Where a change could not meet that bar it
was not done (see "Not done" at the end).

## Compatibility direction

Compatibility runs in exactly one direction. A host speaks only the
newest protocol (`kProtocolVersionHostMin` == `kProtocolVersionMax` in
`scene_v1.h`, raised together), so a host never has an older client
attached — never design, gate, or test for "old client joins new
host". What must keep working is a new *client* joining an *older*
server (down to `kProtocolVersionClientMin`) and playing old replays:
there the legacy stream layouts and sim/draw paths stay exactly as
they were, and new behavior keys off the session's (or replay
header's) protocol version. Unknown values arriving from a newer peer
are ignored rather than treated as errors.

"Older" means pre-1.8 (37 and below) only. The 1.8 cycle's
intermediate protocols (`kProtocolVersionDevGapMin`..`Max`, 38 up to
the one before the final) are refused as a client and for replays
(`IsJoinableHostProtocol`; Eric, 2026-10-01), so no decode path exists
for them alone -- a branch serving only that band is dead code. Keep
`kProtocolVersionDevGapMax` one below `kProtocolVersionMax` on any
further bump before 1.8 ships (a static_assert enforces it).

## Framing (protocol 44)

`[BA_MESSAGE_SESSION_COMMANDS][varint len][cmd id][zigzag varint
ints...]` per command; floats and chars are raw. Writer
`SessionStream::WriteInt_`, reader `ClientSession::ReadVarint_`;
`kProtocolVersionCompactStream`. Older streams keep the fixed
int32/uint16 layout, selected by the stream's protocol (handshake or
replay header).

A message ships once per foreground-scene step
(`SessionStream::EndCommand`: `foreground_step_pending_`, with
`other_step_pending_` as a two-step fallback for a paused or absent
activity). Commands written between steps ride with the next step, at
most 8ms later and inside the client's playback buffer.

## Folded and packed commands

Two kinds, both gated on protocol 44 and both encoding-only:

**Folded** (`kStepSceneGraphAndTime`, `kAddAnimCurve`): the client
performs exactly the operations the separate commands would have, in
the same order, at the same point. A scene step followed by a time
step is one command; `bs.animate()` (node add, owner, OnCreate, four
attr sets, two connects) is one command
(`_bascenev1.animcurve` does the work natively, in the old order).

**Packed** (`kTimeStepSceneGraphAndTime`, `kAddNodeWithAttrs`): wire
only. The client expands them back into the original commands at
receipt (`ClientSession::ExpandPackedCommand_`) before the
pending-release / pacing logic or any handler sees them, so everything
downstream is byte-for-byte the unpacked stream. Used where a merged
command would have changed *when* the client did something: a single
time+step+time command would run the step in the same client update
as the leading delta, where today the update loop can pause between
them.

### The fold scope

The host never reconstructs a packed command from Python values. It
runs the ordinary code (real node, real attr sets, real connects,
which all write their ordinary commands) inside
`SessionStream::BeginFold()`; the commands are held aside;
`CommitFold*` writes the one command from them, and `AbortFold()`
replays them verbatim if anything throws or the held sequence is not
exactly what the packing expects (e.g. an attr type the client's
re-split table does not cover). A fold can therefore never desync a
client: the worst case is the old encoding.

`kAddNodeWithAttrs` carries each attr set as `[cmd][body minus node
id]`; the client re-splits from the per-command value layouts in
`SkipPackedAttrValue_`, which must match the writers in
`session_stream.cc` and `IsPackableAttrCommand`. Adding a packable
attr command means updating both.

## Physics corrections

Sent every `dynamics_sync_time` (500ms) per scene, all kBody rigid
bodies of every node, absolute state. Under 44
(`kProtocolVersionCompactCorrections`): flag byte, position as 3 x
int24 millimetres, orientation as a packed smallest-three quaternion
(4 bytes), f16 per non-zero velocity component, varint framing
(`RigidBody::EmbedCompact` / `ExtractCompact`,
`Scene::GetCorrectionMessageCompact_`).

They go **unreliable** to 44+ peers (`kProtocolVersionUnreliableParts`)
as `BA_SCENEPACKET_MESSAGE_UNRELIABLE_PART` packets: <= 32 parts sharing
one unreliable number, reassembled by the receiver and applied
all-or-nothing (a partial correction is a sim explosion), only once
the reliable stream has reached the correction's stamp (an early one
is held and applied at exactly that point inside the reliable
catch-up loop) and at most `kUnreliableStaleTolerance` (2) reliable
messages behind. A lost part means that correction is superseded by
the next, instead of stalling the in-order reliable stream for a
resend. `BA_RELIABLE_CORRECTIONS` (`--reliable-corrections`) is the
A/B switch. Client-side blending (`RigidBody::AddBlendOffset`) is a
no-op today, so every correction is a hard snap; lowering the rate
needs a working blend first.

## Reliable stream loss recovery

Every game packet carries the receiver's next-wanted reliable number
plus a have-bitfield for the messages after it. Under 44 that field is
32 bits instead of 8 (`kPacketWideAcksFlag` on the type byte, so each
packet declares its own layout; `kProtocolVersionWideAcks`), a receiver
with a gap acks within `kGapAckDelay` (20ms) instead of on the 100ms
keepalive, and a message the peer's acks prove lost resends on
`kLossResendTime` (40ms or 0.75 x ping) instead of the doubling backoff
(capped at `kMaxResendTime`). Before this the client fell 130
messages/s behind at 20% loss and was pruned; after, 20% plays at run
rate ~1.0 (`docs/initiatives/bandwidth.md` has the table).

## Packet budget

`kMaxPacketSize` (700) is the huffman-era limit and stays for legacy
peers; 44+ peers get `kMaxPacketSizeBig` (1200, QUIC's minimum
datagram / IPv6's 1280 MTU minus headers, so no fragmentation without
path-MTU discovery), with reliable multipart chunks sized to it
(`Connection::MaxPacketSize_`). Compression only shrinks a packet, so
the raw budget bounds the wire size.

## Instrumentation

- `test_game_run --stream-stats` (`BA_STREAM_STATS`): a host logs
  every 5s the raw command bytes by command type, by node type and by
  attr, correction bytes, framing adjacency counters, and each
  client's wire/raw bytes, packets, resends and injected drops. A
  client logs a `client pacing` line (buffered step time, run rate,
  delay estimates, unreliable reassembly counters).
- `--packet-dump` (`BA_PACKET_DUMP`): raw outgoing packets to
  `<ba_root>/packet_dump_<n>.bin`, u16-length-prefixed. The corpus for
  dictionary training and for the scan below.
- `tools/pcommand stream_scan <dump...>` (`batoolsinternal/streamscan.py`):
  offline breakdown of the command stream — KB/s by command, by (node
  type, attr), command bigrams, node-creation signatures (what a
  `newnode(attrs)` or utility call costs), float-attr value spreads.
  Command ids come from the `SessionCommand` enum and attr names from
  the node-attr golden, so it tracks the code. Use it to rank
  candidates; then measure wire cost with a synthetic A/B on an idle
  host with a client attached, because raw share and wire share
  disagree (repetitive framing compresses to a fraction; float payload
  does not).
- `--packet-loss N` (`BA_PACKET_LOSS`): drop N% of a process's
  outgoing game packets; put it on the host.
- `--limbs bg|main` must match on host and client so corrections
  address the same bodies.

## Not done, and why

- Coalescing time-sets across other commands, phase-locking the
  activity scene's step timer to the session's, withholding the
  end-of-update time-step: each moves when a command executes or
  changes the step cadence a client's pacing sees.
- Quantizing player input floats to int8: only logic-neutral if the
  host quantizes at the input layer too, which changes stick
  resolution. Small win (~0.15 KB/s raw); Eric's call.
- Client-side auto-removal of finished animcurves: changes node
  lifetime.
