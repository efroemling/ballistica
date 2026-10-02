# Released under the MIT License. See LICENSE for details.
#
"""Client-facing types related to asset packages."""

from enum import Enum
from dataclasses import dataclass
from typing import NewType, Annotated

from efro.dataclassio import ioprepped, IOAttrs


class AssetPackageResolveError(Enum):
    """Why an asset-package resolve failed (structured for branching).

    The server sends this back when a resolve fails, so the client can
    react precisely (e.g. prompt for sign-in on ``AUTH_REQUIRED``)
    rather than parsing the human-readable error string. On the client
    it arrives as :attr:`babase.AssetResolveError.code`.

    New values may be added over time; code branching on these should
    handle unrecognized ones (older clients see any value they don't
    know as ``INTERNAL``).
    """

    #: Caller is unauthenticated and the version is non-public; signing in
    #: with an account that has access may resolve it.
    AUTH_REQUIRED = 'auth'
    #: Caller is authenticated but lacks access to this (non-public)
    #: version (not the owner / not on the package's dev team).
    ACCESS_DENIED = 'access'
    #: The requested asset-package-version id is unknown / invalid.
    NOT_FOUND = 'notfound'
    #: A requested dimension value was invalid (texture profile/quality,
    #: language, etc.).
    INVALID = 'invalid'
    #: An internal/assemble error occurred server-side.
    INTERNAL = 'internal'
    #: The client build is too old to address current asset-package
    #: manifests (which use clean source-named logical paths); the user
    #: must update. Clients predating the build-number field also land
    #: here.
    CLIENT_TOO_OLD = 'tooold'
    #: The package's own source content failed to build -- a problem the
    #: package author can fix (e.g. a malformed sound or texture file).
    #: The human-readable error names the offending source file(s);
    #: clients should surface it verbatim. Old clients see this as
    #: ``INTERNAL``.
    CONTENT = 'content'


@ioprepped
@dataclass
class AssetPackageDisplayInfo:
    """Names an asset package for people (as in an error message).

    Sent alongside resolve failures that are about one particular
    package (``AUTH_REQUIRED``, ``ACCESS_DENIED``) so the client can say
    which package it is in its own (translated) words, e.g.
    "asset package 'foo' by efro".
    """

    #: The package's name (``foo`` in ``a-0.foo.260911``).
    name: Annotated[str, IOAttrs('n')]

    #: Its owner's display name (account tag), or their account id if
    #: no tag could be found.
    owner: Annotated[str, IOAttrs('o')]


#: An asset-package-version's numeric id: a permanent int minted by the
#: master server when the version is created, never reused, and a full
#: alternate to the version's string id (``a-0.babuiltinassets.260927``).
#: Numeric ids are what machinery stores and sends; string ids are for
#: people (display, authoring). A distinct type (a plain ``int`` on the
#: wire) so one can't be mixed up with other ints, such as asset
#: indices.
ApverNum = NewType('ApverNum', int)
