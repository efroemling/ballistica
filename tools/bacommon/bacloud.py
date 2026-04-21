# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to the bacloud tool.

.. warning::

  This is an internal api and subject to change at any time. Do not use
  it in mod code.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Annotated

from efro.dataclassio import ioprepped, IOAttrs

if TYPE_CHECKING:
    pass

# Version is sent to the master-server with all commands. Can be incremented
# if we need to change behavior server-side to go along with client changes.
#
# 15 (2026-04): Workspace upload protocol switched from inline gzipped
#               bytes (``uploads_inline``) to direct-to-GCS streaming
#               via signed URLs (``uploads_signed``). Old clients will
#               be rejected by the bumped ``MIN_VERSION`` server-side.
# 16 (2026-04): Dropped ``md5_b64`` from ``DirectoryManifestFile``.
#               The streaming upload pipeline now relies solely on
#               SHA-256 verification at finalize time; md5 was
#               redundant with the content-addressable cloud_file_id
#               check and just doubled hashing cost client-side.
# 17 (2026-04): Workspace download / asset-package file-download
#               switched from inline gzipped bytes (``downloads_inline``)
#               to direct-from-GCS streaming via signed GET URLs
#               (``downloads_signed``). Removes the Cloud Run 32 MB
#               response-size cap for CloudFile-backed downloads.
#               ``downloads_inline`` remains for small ad-hoc blobs
#               (asset manifests, admin test payloads).
# 18 (2026-04): Added ``upload_plan`` response field for a simpler,
#               framework-managed upload protocol used by new admin
#               archive commands (and eventually the workspace put
#               path). Old clients don't understand the new field
#               and would silently skip uploads.
BACLOUD_VERSION = 18


def asset_file_cache_path(filehash: str) -> str:
    """Given a sha256 hex file hash, return a storage path."""

    # We expect a 64 byte hex str with only lowercase letters and
    # numbers. Note to self: I considered base64 hashes to save space
    # but then remembered that lots of filesystems out there ignore case
    # so that would not end well.
    assert len(filehash) == 64
    assert filehash.islower()
    assert filehash.isalnum()

    # Split into a few levels of directories to keep directory listings
    # and operations reasonable. This will give 256 top level dirs, each
    # with 256 subdirs. So if we have 65,536 files in our cache then
    # dirs will average 1 file each. That seems like a reasonable spread
    # I think.
    return f'{filehash[:2]}/{filehash[2:4]}/{filehash[4:]}'


@ioprepped
@dataclass
class RequestData:
    """Request sent to bacloud server."""

    command: Annotated[str, IOAttrs('c')]
    token: Annotated[str | None, IOAttrs('t')]
    payload: Annotated[dict, IOAttrs('p')]
    tzoffset: Annotated[float, IOAttrs('z')]
    isatty: Annotated[bool, IOAttrs('y')]


# Types used by the UploadPlan protocol. See ResponseData.UploadPlan.


@ioprepped
@dataclass
class UploadPlanFileInfo:
    """A single file entry the client is reporting to the server."""

    #: Relative path (from the upload plan's source_dir).
    name: Annotated[str, IOAttrs('n')]

    #: SHA-256 hex digest of the file body.
    sha256: Annotated[str, IOAttrs('h')]

    #: Size in bytes.
    size: Annotated[int, IOAttrs('s')]


@ioprepped
@dataclass
class UploadPlanPrepareRequest:
    """Client → server: request signed upload sessions for files."""

    files: Annotated[list[UploadPlanFileInfo], IOAttrs('f')]

    #: CloudFileCategory value (e.g. 'archive_misc'). Tells the
    #: server which bucket new uploads should land in.
    cloud_file_category: Annotated[str, IOAttrs('ct')]


@ioprepped
@dataclass
class UploadPlanPrepareItem:
    """Server → client: one file's prepare result."""

    #: Relative path matching the request entry.
    name: Annotated[str, IOAttrs('n')]

    #: The cloud_file_id this file maps to. Present when the file
    #: already exists server-side (dedup hit) — no upload needed.
    cloud_file_id: Annotated[str | None, IOAttrs('c', store_default=False)] = (
        None
    )

    #: Signed URL the client should PUT bytes to. Present when the
    #: file does not yet exist and needs to be uploaded.
    upload_url: Annotated[str | None, IOAttrs('u', store_default=False)] = None

    #: Headers the client must include on the PUT. Present when
    #: upload_url is set.
    upload_headers: Annotated[
        dict[str, str], IOAttrs('h', store_default=False)
    ] = field(default_factory=dict)

    #: Server-side upload session id. Present when upload_url is set.
    #: Passed back to the server in the finalize request.
    session_id: Annotated[str | None, IOAttrs('s', store_default=False)] = None


@ioprepped
@dataclass
class UploadPlanPrepareResponse:
    """Server → client: prepare results for each file."""

    items: Annotated[list[UploadPlanPrepareItem], IOAttrs('i')]


@ioprepped
@dataclass
class UploadPlanFinalizeRequest:
    """Client → server: finalize uploaded files by session id."""

    #: Map of file name → session_id for files that were uploaded.
    sessions: Annotated[dict[str, str], IOAttrs('s')]


@ioprepped
@dataclass
class UploadPlanFinalizeResponse:
    """Server → client: cloud-file-ids for each finalized upload."""

    #: Map of file name → cloud_file_id.
    cloud_file_ids: Annotated[dict[str, str], IOAttrs('c')]


@ioprepped
@dataclass
class UploadPlanCommit:
    """Client → command's finalize handler: full upload results.

    The client builds this after completing the prepare/upload/
    finalize cycle and invokes the upload-plan's
    ``finalize_command`` with it as the payload.
    """

    #: Complete mapping of {relative_path: cloud_file_id} for every
    #: file in the plan's source_dir.
    files: Annotated[dict[str, str], IOAttrs('f')]

    #: The opaque state dict from the original UploadPlan.
    state: Annotated[dict, IOAttrs('s')]


@ioprepped
@dataclass
class ResponseData:
    """Response sent from the bacloud server to the client."""

    @ioprepped
    @dataclass
    class SignedUploadEntry:
        """Describes one direct-to-GCS streaming upload to perform."""

        #: Local file the client should read and PUT.
        path: Annotated[str, IOAttrs('p')]

        #: Signed GCS URL to PUT the bytes to.
        upload_url: Annotated[str, IOAttrs('u')]

        #: HTTP headers the client must include on the PUT (notably
        #: ``Content-MD5`` and ``Content-Type`` — these are bound into
        #: the URL signature, so the client cannot modify them).
        upload_headers: Annotated[dict[str, str], IOAttrs('h')]

        #: Server-side upload session id; the client passes this back
        #: in the next ``end_command`` args under ``uploads_signed`` to
        #: tell the server which upload to finalize.
        session_id: Annotated[str, IOAttrs('s')]

    @ioprepped
    @dataclass
    class SignedDownloadEntry:
        """Describes one direct-from-GCS streaming download to perform.

        The client streams bytes from ``download_url`` straight to
        ``path``, hashing as it goes and verifying against ``sha256``
        before atomic-renaming into place. Since the bytes bypass the
        bacloud response envelope entirely, there is no per-file size
        cap — files of any size can be delivered this way.
        """

        #: Local path the client should write the file to. Will be
        #: created (and its parent dirs) if missing; any existing file
        #: at the path is replaced atomically.
        path: Annotated[str, IOAttrs('p')]

        #: Signed GCS URL to GET the bytes from.
        download_url: Annotated[str, IOAttrs('u')]

        #: Hex-encoded SHA-256 of the expected file body. The client
        #: streams through ``hashlib.sha256`` and refuses to commit the
        #: file if the final digest does not match.
        sha256: Annotated[str, IOAttrs('h')]

        #: Expected file size in bytes, for progress reporting and a
        #: belt-and-suspenders sanity check against the streamed total.
        size: Annotated[int, IOAttrs('s')]

    @ioprepped
    @dataclass
    class UploadPlan:
        """Declarative plan for uploading a set of local files.

        When a command returns an ``UploadPlan`` in its response, the
        bacloud client takes over: it walks ``source_dir``, computes
        sha256+size for each file, checks which ones already exist
        server-side (dedup), streams the missing ones direct-to-GCS
        via signed URLs, and then invokes ``finalize_command`` with
        the resulting ``{relative_path: cloud_file_id}`` mapping.

        The entire upload protocol (manifest, dedup, signed uploads,
        finalize) is handled by shared client/server infrastructure.
        Individual commands only need to describe *what* to upload
        and *what to do* with the cloud-file-ids afterward.
        """

        #: Local directory to upload. All files under this directory
        #: (recursively) will be uploaded.
        source_dir: Annotated[str, IOAttrs('sd')]

        #: Command the client should invoke after all uploads are
        #: complete. The client will pass a ``UploadPlanCommit``
        #: payload to this command.
        finalize_command: Annotated[str, IOAttrs('fc')]

        #: Opaque state dict passed back to ``finalize_command`` so
        #: the originating command can remember its context (e.g.
        #: archive-id, version-number) without storing server-side.
        finalize_state: Annotated[dict, IOAttrs('fs')]

        #: Which CloudFileCategory new uploads should land in. Carried
        #: through to the prepare step, which embeds it into the
        #: signed upload session. Stored as the enum value string.
        cloud_file_category: Annotated[str, IOAttrs('ct')]

        #: Optional description shown to the user during the upload.
        description: Annotated[str, IOAttrs('de', store_default=False)] = ''

    @ioprepped
    @dataclass
    class Downloads:
        """Info about downloads included in a response."""

        @ioprepped
        @dataclass
        class Entry:
            """Individual download."""

            path: Annotated[str, IOAttrs('p')]

            #: Args include with this particular request (combined with
            #: baseargs).
            args: Annotated[dict[str, str], IOAttrs('a')]

            # TODO: could add a hash here if we want the client to
            # verify hashes.

        #: If present, will be prepended to all entry paths via os.path.join.
        basepath: Annotated[str | None, IOAttrs('p')]

        #: Server command that should be called for each download. The
        #: server command is expected to respond with a downloads_inline
        #: containing a single 'default' entry. In the future this may
        #: be expanded to a more streaming-friendly process.
        cmd: Annotated[str, IOAttrs('c')]

        #: Args that should be included with all download requests.
        baseargs: Annotated[dict[str, str], IOAttrs('a')]

        #: Everything that should be downloaded.
        entries: Annotated[list[Entry], IOAttrs('e')]

    #: If present, client should print this message before any other
    #: response processing (including error handling) occurs.
    message: Annotated[str | None, IOAttrs('m', store_default=False)] = None

    #: Value for the 'end' arg of the message print() call.
    message_end: Annotated[str, IOAttrs('m_end', store_default=False)] = '\n'

    #: If present, client should print this message before any other
    #: response processing (including error handling) occurs.
    message_stderr: Annotated[
        str | None, IOAttrs('m2', store_default=False)
    ] = None

    #: Value for the 'end' arg of the message print() call.
    message_stderr_end: Annotated[
        str, IOAttrs('m2_end', store_default=False)
    ] = '\n'

    #: If present, client should abort with this error message and
    #: return-code 2.
    error: Annotated[str | None, IOAttrs('e', store_default=False)] = None

    #: If present for an interactive command, specifies the return code
    #: for the process. Note that this only applies if error is not set.
    #: Standard return codes are 0 for success, 1 for a successful run
    #: but negative result, and 2 for errors.
    return_code: Annotated[int | None, IOAttrs('r', store_default=False)] = None

    #: How long to wait before proceeding with remaining response (can
    #: be useful when waiting for server progress in a loop).
    delay_seconds: Annotated[float, IOAttrs('d', store_default=False)] = 0.0

    #: If present, a token that should be stored client-side and passed
    #: with subsequent commands.
    login: Annotated[str | None, IOAttrs('l', store_default=False)] = None

    #: If True, any existing client-side token should be discarded.
    logout: Annotated[bool, IOAttrs('lo', store_default=False)] = False

    #: If present, client should generate a manifest of this dir.
    #: It should be added to end_command args as 'manifest'.
    dir_manifest: Annotated[str | None, IOAttrs('man', store_default=False)] = (
        None
    )

    #: If present, files the client should PUT directly to GCS via
    #: the provided signed URLs and then send the resulting session
    #: ids back to the server in the next end_command's args under
    #: 'uploads_signed' (a ``dict[path, session_id]`` keyed by the
    #: same local path that was sent in the entry). Streams without
    #: ever buffering the file body in master-server memory, so it
    #: imposes no per-file size limit.
    uploads_signed: Annotated[
        list[SignedUploadEntry] | None,
        IOAttrs('usgn', store_default=False),
    ] = None

    #: If present, an upload plan the client should execute. See
    #: :class:`UploadPlan` for details. The client handles the full
    #: upload protocol (manifest, dedup, signed uploads, finalize)
    #: and then invokes the plan's ``finalize_command`` with the
    #: resulting cloud-file-id mapping.
    upload_plan: Annotated[
        UploadPlan | None, IOAttrs('upl', store_default=False)
    ] = None

    #: Free-form structured payload the server can return for
    #: client-internal consumption (e.g. upload-plan prepare/finalize
    #: results). Not displayed to the user and not written to disk.
    raw_result: Annotated[dict | None, IOAttrs('rr', store_default=False)] = (
        None
    )

    #: If present, file paths that should be deleted on the client.
    deletes: Annotated[
        list[str] | None, IOAttrs('dlt', store_default=False)
    ] = None

    #: If present, describes files the client should individually
    #: request from the server if not already present on the client.
    downloads: Annotated[
        Downloads | None, IOAttrs('dl', store_default=False)
    ] = None

    #: If present, pathnames mapped to gzipped data to be written to the
    #: client. This should only be used for relatively small files as
    #: they are all included inline as part of the response — Cloud
    #: Run caps buffered response bodies at 32 MB, which places a hard
    #: ceiling on any payload delivered this way. For larger or
    #: CloudFile-backed downloads, use ``downloads_signed`` instead.
    downloads_inline: Annotated[
        dict[str, bytes] | None, IOAttrs('dinl', store_default=False)
    ] = None

    #: If present, files the client should GET directly from GCS via
    #: the provided signed URLs, verifying the streamed content against
    #: the provided SHA-256. Streams without ever buffering the file
    #: body in master-server memory, so it imposes no per-file size
    #: limit and bypasses the Cloud Run 32 MB response cap that
    #: constrains ``downloads_inline``.
    downloads_signed: Annotated[
        list[SignedDownloadEntry] | None,
        IOAttrs('dsgn', store_default=False),
    ] = None

    #: If present, all empty dirs under this one should be removed.
    dir_prune_empty: Annotated[
        str | None, IOAttrs('dpe', store_default=False)
    ] = None

    #: If present, url to display to the user.
    open_url: Annotated[str | None, IOAttrs('url', store_default=False)] = None

    #: If present, a line of input is read and placed into end_command
    #: args as 'input'. The first value is the prompt printed before
    #: reading and the second is whether it should be read as a password
    #: (without echoing to the terminal).
    input_prompt: Annotated[
        tuple[str, bool] | None, IOAttrs('inp', store_default=False)
    ] = None

    #: If present, a message that should be printed after all other
    #: response processing is done.
    end_message: Annotated[str | None, IOAttrs('em', store_default=False)] = (
        None
    )

    #: End arg for end_message print() call.
    end_message_end: Annotated[str, IOAttrs('eme', store_default=False)] = '\n'

    #: If present, a message that should be printed after all other
    #: response processing is done.
    end_message_stderr: Annotated[
        str | None, IOAttrs('em2', store_default=False)
    ] = None

    #: End arg for end_message print() call.
    end_message_stderr_end: Annotated[
        str, IOAttrs('em2e', store_default=False)
    ] = '\n'

    #: If present, this command is run with these args at the end of
    #: response processing.
    end_command: Annotated[
        tuple[str, dict] | None, IOAttrs('ec', store_default=False)
    ] = None
