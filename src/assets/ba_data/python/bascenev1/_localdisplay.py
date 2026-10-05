# Released under the MIT License. See LICENSE for details.
#
"""Local displays: per-machine content driven by a shared scene node."""

import logging
import weakref
from enum import Enum
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Annotated, override, cast, assert_never

from efro.dataclassio import (
    ioprepped,
    IOAttrs,
    IOMultiType,
    dataclass_from_json,
    dataclass_to_json,
)

import babase
import _bascenev1
from bascenev1._actorhost import ActorHost

if TYPE_CHECKING:
    from typing import Callable

    import bascenev1


class LocalDisplayTypeID(Enum):
    """Type ID for each of our :class:`LocalDisplayConfig` subclasses."""

    UNKNOWN = 'u'
    CLASSIC_CONTROLS = 'cc'


class LocalDisplayConfig(IOMultiType[LocalDisplayTypeID]):
    """Describes what a :class:`LocalDisplay` should show.

    Configs ride the ``config`` attr of a ``localdisplay`` scene node
    wrapped in a :class:`LocalDisplayConfigSet`; every machine that
    receives the node (the host included) picks the entry for its own
    build and builds its own local version of what it describes.

    Forward compatibility: configs are decoded lossily, so a client
    that predates a config *type* gets :class:`UnknownLocalDisplayConfig`
    (which the set's selection skips over in favor of an older entry,
    or shows nothing), and one that predates a *field* on a known type
    ignores it while its own defaults fill any fields the newer host
    omitted. New types and fields are therefore safe to add at any
    time; only removing or retyping an existing field is a breaking
    change.
    """

    @override
    @classmethod
    def get_type_id(cls) -> LocalDisplayTypeID:
        # Require child classes to supply this themselves.
        raise NotImplementedError()

    @override
    @classmethod
    def get_type_id_storage_name(cls) -> str:
        # Pin this explicitly; it is part of the wire format.
        return '_t'

    @override
    @classmethod
    def get_type(cls, type_id: LocalDisplayTypeID) -> type[LocalDisplayConfig]:
        """Return the subclass for each of our type-ids."""
        t = LocalDisplayTypeID
        if type_id is t.UNKNOWN:
            return UnknownLocalDisplayConfig
        if type_id is t.CLASSIC_CONTROLS:
            return ClassicControlsLocalDisplayConfig

        # Make sure we handle all types.
        assert_never(type_id)

    @override
    @classmethod
    def get_unknown_type_fallback(cls) -> LocalDisplayConfig:
        # A config type from a newer build than ours; stand in a
        # placeholder so the display simply shows nothing.
        return UnknownLocalDisplayConfig()


@ioprepped
@dataclass
class UnknownLocalDisplayConfig(LocalDisplayConfig):
    """Fallback substitute for config types we don't recognize."""

    @override
    @classmethod
    def get_type_id(cls) -> LocalDisplayTypeID:
        return LocalDisplayTypeID.UNKNOWN


@ioprepped
@dataclass
class ClassicControlsLocalDisplayConfig(LocalDisplayConfig):
    """The classic 4-button controls guide.

    Each machine shows the button names for its own controllers.
    """

    #: Screen position (in the same space text/image nodes use).
    position: Annotated[tuple[float, float], IOAttrs('p')] = (390.0, 120.0)

    #: Overall scale.
    scale: Annotated[float, IOAttrs('s')] = 1.0

    #: Seconds before the guide starts trying to fade in.
    delay: Annotated[float, IOAttrs('d')] = 0.0

    #: If set, the guide fades back out and dies after this many seconds.
    lifespan: Annotated[float | None, IOAttrs('l')] = None

    #: Whether to use brighter colors (for showing over gameplay).
    bright: Annotated[bool, IOAttrs('b')] = False

    @override
    @classmethod
    def get_type_id(cls) -> LocalDisplayTypeID:
        return LocalDisplayTypeID.CLASSIC_CONTROLS


@ioprepped
@dataclass
class LocalDisplayConfigSet:
    """What a ``localdisplay`` node's ``config`` attr actually carries.

    A map of minimum engine build number to the
    :class:`LocalDisplayConfig` clients at or above that build should
    use. Each client picks the entry with the highest build it
    satisfies, so a host can hand newer clients a richer display while
    older ones keep getting something they understand. A single entry
    at build 0 applies to everyone (see :meth:`single`).
    """

    configs: Annotated[dict[int, LocalDisplayConfig], IOAttrs('c')] = field(
        default_factory=dict
    )

    @classmethod
    def single(cls, config: LocalDisplayConfig) -> LocalDisplayConfigSet:
        """Return a set holding one config that applies to all builds."""
        return cls(configs={0: config})

    def to_json(self) -> str:
        """Return our json form for a node's ``config`` attr."""
        return dataclass_to_json(self)

    def select(self, build_number: int) -> LocalDisplayConfig | None:
        """Return the config for a given engine build, or None.

        Entries requiring newer builds are skipped, as are entries that
        decoded to :class:`UnknownLocalDisplayConfig` when an older
        recognized entry is available.
        """
        fallback: LocalDisplayConfig | None = None
        for min_build in sorted(self.configs, reverse=True):
            if min_build > build_number:
                continue
            config = self.configs[min_build]
            if isinstance(config, UnknownLocalDisplayConfig):
                if fallback is None:
                    fallback = config
                continue
            return config
        return fallback


class LocalDisplayHandler:
    """Builds and manages the content of one :class:`LocalDisplay`.

    One of these exists per display; it is created via the factory
    registered for the display's config type (see
    :func:`register_local_display_handler`) with the display's context
    current, so it can create actors, nodes, timers, etc. directly.
    Everything it creates dies with the display.
    """

    def __init__(self, display: LocalDisplay) -> None:
        self._display = weakref.ref(display)

    @property
    def display(self) -> LocalDisplay:
        """The display we belong to.

        Raises a :class:`~babase.NotFoundError` if it no longer exists.
        """
        display = self._display()
        if display is None:
            raise babase.NotFoundError()
        return display

    def on_visible_changed(self, visible: bool) -> None:
        """Called when the node's ``visible`` attr changes.

        Hosts flip this off ahead of deleting the node so displays get
        a chance to fade out gracefully.
        """

    def on_config_changed(self, config: LocalDisplayConfig) -> None:
        """Called when the config changes but keeps its type.

        The default implementation ignores the change.
        """

    def on_expire(self) -> None:
        """Called when the display is expiring.

        Actors and nodes created under the display are torn down
        automatically after this; only clean up things that aren't.
        """


_handler_factories: dict[
    type[LocalDisplayConfig],
    Callable[[LocalDisplay, LocalDisplayConfig], LocalDisplayHandler],
] = {}


def register_local_display_handler[T: LocalDisplayConfig](
    configtype: type[T],
    factory: Callable[[LocalDisplay, T], LocalDisplayHandler],
) -> None:
    """Register the handler to build for a config type.

    The factory is called with the display and its decoded config, with
    the display's context current. Registering again replaces the
    previous factory.
    """
    # Our dict is keyed by exact config type, so the narrower factory
    # signature is safe here.
    _handler_factories[configtype] = cast(
        'Callable[[LocalDisplay, LocalDisplayConfig], LocalDisplayHandler]',
        factory,
    )


class LocalDisplay(ActorHost):
    """The local side of a ``localdisplay`` scene node.

    Each machine receiving the node (host and every client) gets its
    own one of these, owning a private context whose scene is never
    streamed anywhere. Actors created within that context bind to the
    display exactly as they would to an activity, and are expired when
    the node dies.

    Only display-style actors make sense here (text, images,
    animation). Anything that reaches for players, shared objects or
    materials belongs to an activity and will not work in a display.

    Instances are created by the engine; don't instantiate these
    directly.
    """

    def __init__(self, node: bascenev1.Node, context: babase.ContextRef):
        super().__init__()
        self._node = node
        self._context = context
        self._handler: LocalDisplayHandler | None = None
        self._config: LocalDisplayConfig | None = None
        self._visible = bool(node.visible)
        self._prune_dead_actors_timer: bascenev1.Timer | None = None

        with self._context:
            # A lightweight time source for bs.animate() and friends.
            # Note that a sessionglobals node also switches its scene
            # to the fixed vr overlay, so in vr our content sits at
            # the fixed session position instead of following the
            # activity's setting.
            self._globalsnode = _bascenev1.newnode('sessionglobals')
            self._prune_dead_actors_timer = _bascenev1.Timer(
                5.17, self._prune_dead_actors, repeat=True
            )

    def _start(self) -> None:
        # Called by the engine once it has registered us as the Python
        # side of our context (so getlocaldisplay() resolves to us);
        # only now can handlers/actors be built.
        self._apply_config()

    @override
    def __repr__(self) -> str:
        return f'<bascenev1.LocalDisplay config={self._config!r}>'

    @property
    def context(self) -> babase.ContextRef:
        """A context-ref pointing at this display's private context."""
        return self._context

    @property
    def node(self) -> bascenev1.Node:
        """The ``localdisplay`` node we belong to."""
        return self._node

    @property
    def globalsnode(self) -> bascenev1.Node:
        """The globals node driving time for animation in this display.

        Raises a :class:`~babase.NodeNotFoundError` if it no longer
        exists.
        """
        node = self._globalsnode
        if not node:
            raise babase.NodeNotFoundError()
        return node

    @property
    def config(self) -> LocalDisplayConfig | None:
        """Our current decoded config (None if unset or invalid)."""
        return self._config

    @property
    def visible(self) -> bool:
        """The node's current ``visible`` value."""
        return self._visible

    def _on_node_attrs_changed(self) -> None:
        # Called by the engine whenever our node's config or visible
        # attrs change.
        if self._expired or not self._node:
            return
        self._apply_config()
        visible = bool(self._node.visible)
        if visible != self._visible:
            self._visible = visible
            if self._handler is not None:
                try:
                    with self._context:
                        self._handler.on_visible_changed(visible)
                except Exception:
                    logging.exception(
                        'Error in on_visible_changed() for %s.', self
                    )

    def _apply_config(self) -> None:
        cfgstr = self._node.config
        config: LocalDisplayConfig | None = None
        if cfgstr:
            try:
                # Lossy so newer config types/fields from newer hosts
                # degrade gracefully instead of erroring (see
                # LocalDisplayConfig).
                configset = dataclass_from_json(
                    LocalDisplayConfigSet, cfgstr, lossy=True
                )
                config = configset.select(babase.app.env.engine_build_number)
            except Exception:
                logging.exception(
                    'Error decoding local-display config %r.', cfgstr
                )
        if config == self._config:
            return

        # A change of config type means a new handler; otherwise the
        # existing one gets told about the change.
        if type(config) is not type(self._config):
            self._expire_handler()
            self._config = config
            if isinstance(config, UnknownLocalDisplayConfig):
                # From a newer build than ours; nothing we can show.
                logging.debug(
                    'Ignoring unrecognized local-display config %r.', cfgstr
                )
            elif config is not None:
                factory = _handler_factories.get(type(config))
                if factory is None:
                    logging.warning(
                        'No local-display handler registered for %s.',
                        type(config).__name__,
                    )
                else:
                    try:
                        with self._context:
                            self._handler = factory(self, config)
                    except Exception:
                        logging.exception(
                            'Error creating local-display handler for %s.',
                            self,
                        )
            return

        assert config is not None
        self._config = config
        if self._handler is not None:
            try:
                with self._context:
                    self._handler.on_config_changed(config)
            except Exception:
                logging.exception('Error in on_config_changed() for %s.', self)

    def _expire_handler(self) -> None:
        handler = self._handler
        self._handler = None
        if handler is not None:
            try:
                handler.on_expire()
            except Exception:
                logging.exception('Error in on_expire() for %s.', self)

    def _expire(self) -> None:
        # Called by the engine as our node goes down; we run in an empty
        # context. After this, the engine tears down our scene, timers,
        # and everything created in our context.
        if self._expired:
            return
        self._expired = True
        self._expire_handler()
        self._expire_actors()
        self._actor_refs = []
        self._actor_weak_refs = []
        self._prune_dead_actors_timer = None
