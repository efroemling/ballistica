# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to object/asset dependencies."""

from __future__ import annotations

import weakref
from typing import Generic, TypeVar, TYPE_CHECKING, override

import babase

import _bascenev1

if TYPE_CHECKING:
    from typing import Any

    import bascenev1

T = TypeVar('T', bound='DependencyComponent')


class Dependency(Generic[T]):
    """A dependency on a DependencyComponent (with an optional config).

    Category: **Dependency Classes**

    This class is used to request and access functionality provided
    by other DependencyComponent classes from a DependencyComponent class.
    The class functions as a descriptor, allowing dependencies to
    be added at a class level much the same as properties or methods
    and then used with class instances to access those dependencies.
    For instance, if you do 'floofcls = bascenev1.Dependency(FloofClass)'
    you would then be able to instantiate a FloofClass in your class's
    methods via self.floofcls().
    """

    def __init__(self, cls: type[T], config: Any = None):
        """Instantiate a Dependency given a bascenev1.DependencyComponent type.

        Optionally, an arbitrary object can be passed as 'config' to
        influence dependency calculation for the target class.
        """
        self.cls: type[T] = cls
        self.config = config
        self._hash: int | None = None

    def get_hash(self) -> int:
        """Return the dependency's hash, calculating it if necessary."""
        from efro.util import make_hash

        if self._hash is None:
            self._hash = make_hash((self.cls, self.config))
        return self._hash

    def __get__(self, obj: Any, cls: Any = None) -> T:
        if not isinstance(obj, DependencyComponent):
            if obj is None:
                raise TypeError(
                    'Dependency must be accessed through an instance.'
                )
            raise TypeError(
                f'Dependency cannot be added to class of type {type(obj)}'
                ' (class must inherit from bascenev1.DependencyComponent).'
            )

        # We expect to be instantiated from an already living
        # DependencyComponent with valid dep-data in place..
        assert cls is not None

        # Get the DependencyEntry this instance is associated with and from
        # there get back to the DependencySet
        entry = getattr(obj, '_dep_entry')
        if entry is None:
            raise RuntimeError('Invalid dependency access.')
        entry = entry()
        assert isinstance(entry, DependencyEntry)
        depset = entry.depset()
        assert isinstance(depset, DependencySet)

        if not depset.resolved:
            raise RuntimeError(
                "Can't access data on an unresolved DependencySet."
            )

        # Look up the data in the set based on the hash for this Dependency.
        assert self._hash in depset.entries
        entry = depset.entries[self._hash]
        assert isinstance(entry, DependencyEntry)
        retval = entry.get_component()
        assert isinstance(retval, self.cls)
        return retval


class DependencyComponent:
    """Base class for all classes that can act as or use dependencies.

    Category: **Dependency Classes**
    """

    _dep_entry: weakref.ref[DependencyEntry]

    def __init__(self) -> None:
        """Instantiate a DependencyComponent."""

        # For now lets issue a warning if these are instantiated without
        # a dep-entry; we'll make this an error once we're no longer
        # seeing warnings.
        # entry = getattr(self, '_dep_entry', None)
        # if entry is None:
        #     print(f'FIXME: INSTANTIATING DEP CLASS {type(self)} DIRECTLY.')

    @classmethod
    def dep_is_present(cls, config: Any = None) -> bool:
        """Return whether this component/config is present on this device."""
        del config  # Unused here.
        return True

    @classmethod
    def get_dynamic_deps(cls, config: Any = None) -> list[Dependency]:
        """Return any dynamically-calculated deps for this component/config.

        Deps declared statically as part of the class do not need to be
        included here; this is only for additional deps that may vary based
        on the dep config value. (for instance a map required by a game type)
        """
        del config  # Unused here.
        return []


class DependencyEntry:
    """Data associated with a dep/config pair in bascenev1.DependencySet."""

    # def __del__(self) -> None:
    #     print('~DepEntry()', self.cls)

    def __init__(self, depset: DependencySet, dep: Dependency[T]):
        # print("DepEntry()", dep.cls)
        self.cls = dep.cls
        self.config = dep.config

        # Arbitrary data for use by dependencies in the resolved set
        # (the static instance for static-deps, etc).
        self.component: DependencyComponent | None = None

        # Weakref to the depset that includes us (to avoid ref loop).
        self.depset = weakref.ref(depset)

    def get_component(self) -> DependencyComponent:
        """Return the component instance, creating it if necessary."""
        if self.component is None:
            # We don't simply call our type to instantiate our instance;
            # instead we manually call __new__ and then __init__.
            # This allows us to inject its data properly before __init__().
            print('creating', self.cls)
            instance = self.cls.__new__(self.cls)
            # pylint: disable=protected-access, unnecessary-dunder-call
            instance._dep_entry = weakref.ref(self)
            instance.__init__()  # type: ignore

            depset = self.depset()
            assert depset is not None
            self.component = instance
        component = self.component
        assert isinstance(component, self.cls)
        if component is None:
            raise RuntimeError(
                f'Accessing DependencyComponent {self.cls} '
                'in an invalid state.'
            )
        return component


class DependencySet(Generic[T]):
    """Set of resolved dependencies and their associated data.

    Category: **Dependency Classes**

    To use DependencyComponents, a set must be created, resolved, and then
    loaded. The DependencyComponents are only valid while the set remains
    in existence.
    """

    def __init__(self, root_dependency: Dependency[T]):
        # print('DepSet()')
        self._root_dependency = root_dependency
        self._resolved = False
        self._loaded = False

        # Dependency data indexed by hash.
        self.entries: dict[int, DependencyEntry] = {}

    # def __del__(self) -> None:
    #     print("~DepSet()")

    def resolve(self) -> None:
        """Resolve the complete set of required dependencies for this set.

        Raises a bascenev1.DependencyError if dependencies are missing (or
        other Exception types on other errors).
        """

        if self._resolved:
            raise RuntimeError('DependencySet has already been resolved.')

        # print('RESOLVING DEP SET')

        # First, recursively expand out all dependencies.
        self._resolve(self._root_dependency, 0)

        # Now, if any dependencies are not present, raise an Exception
        # telling exactly which ones (so hopefully they'll be able to be
        # downloaded/etc.
        missing = [
            Dependency(entry.cls, entry.config)
            for entry in self.entries.values()
            if not entry.cls.dep_is_present(entry.config)
        ]
        if missing:
            raise DependencyError(missing)

        self._resolved = True
        # print('RESOLVE SUCCESS!')

    @property
    def resolved(self) -> bool:
        """Whether this set has been successfully resolved."""
        return self._resolved

    def get_asset_package_ids(self) -> set[str]:
        """Return the set of asset-package-ids required by this dep-set.

        Must be called on a resolved dep-set.
        """
        ids: set[str] = set()
        if not self._resolved:
            raise RuntimeError('Must be called on a resolved dep-set.')
        for entry in self.entries.values():
            if issubclass(entry.cls, AssetPackage):
                assert isinstance(entry.config, str)
                ids.add(entry.config)
        return ids

    def load(self) -> None:
        """Instantiate all DependencyComponents in the set.

        Returns a wrapper which can be used to instantiate the root dep.
        """
        # NOTE: stuff below here should probably go in a separate 'instantiate'
        # method or something.
        if not self._resolved:
            raise RuntimeError("Can't load an unresolved DependencySet")

        for entry in self.entries.values():
            # Do a get on everything which will init all payloads
            # in the proper order recursively.
            entry.get_component()

        self._loaded = True

    @property
    def root(self) -> T:
        """The instantiated root DependencyComponent instance for the set."""
        if not self._loaded:
            raise RuntimeError('DependencySet is not loaded.')

        rootdata = self.entries[self._root_dependency.get_hash()].component
        assert isinstance(rootdata, self._root_dependency.cls)
        return rootdata

    def _resolve(self, dep: Dependency[T], recursion: int) -> None:
        # Watch for wacky infinite dep loops.
        if recursion > 10:
            raise RecursionError('Max recursion reached')

        hashval = dep.get_hash()

        if hashval in self.entries:
            # Found an already resolved one; we're done here.
            return

        # Add our entry before we recurse so we don't repeat add it if
        # there's a dependency loop.
        self.entries[hashval] = DependencyEntry(self, dep)

        # Grab all Dependency instances we find in the class.
        subdeps = [
            cls
            for cls in dep.cls.__dict__.values()
            if isinstance(cls, Dependency)
        ]

        # ..and add in any dynamic ones it provides.
        subdeps += dep.cls.get_dynamic_deps(dep.config)
        for subdep in subdeps:
            self._resolve(subdep, recursion + 1)


class AssetPackage(DependencyComponent):
    """bascenev1.DependencyComponent representing a bundled package of assets.

    Category: **Asset Classes**
    """

    def __init__(self) -> None:
        super().__init__()

        # This is used internally by the get_package_xxx calls.
        self.context = babase.ContextRef()

        entry = self._dep_entry()
        assert entry is not None
        assert isinstance(entry.config, str)
        self.package_id = entry.config
        print(f'LOADING ASSET PACKAGE {self.package_id}')

    @override
    @classmethod
    def dep_is_present(cls, config: Any = None) -> bool:
        assert isinstance(config, str)

        # Temp: hard-coding for a single asset-package at the moment.
        if config == 'stdassets@1':
            return True
        return False

    def gettexture(self, name: str) -> bascenev1.Texture:
        """Load a named bascenev1.Texture from the AssetPackage.

        Behavior is similar to bascenev1.gettexture()
        """
        return _bascenev1.get_package_texture(self, name)

    def getmesh(self, name: str) -> bascenev1.Mesh:
        """Load a named bascenev1.Mesh from the AssetPackage.

        Behavior is similar to bascenev1.getmesh()
        """
        return _bascenev1.get_package_mesh(self, name)

    def getcollisionmesh(self, name: str) -> bascenev1.CollisionMesh:
        """Load a named bascenev1.CollisionMesh from the AssetPackage.

        Behavior is similar to bascenev1.getcollisionmesh()
        """
        return _bascenev1.get_package_collision_mesh(self, name)

    def getsound(self, name: str) -> bascenev1.Sound:
        """Load a named bascenev1.Sound from the AssetPackage.

        Behavior is similar to bascenev1.getsound()
        """
        return _bascenev1.get_package_sound(self, name)

    def getdata(self, name: str) -> bascenev1.Data:
        """Load a named bascenev1.Data from the AssetPackage.

        Behavior is similar to bascenev1.getdata()
        """
        return _bascenev1.get_package_data(self, name)


class TestClassFactory(DependencyComponent):
    """Another test dep-obj."""

    _assets = Dependency(AssetPackage, 'stdassets@1')

    def __init__(self) -> None:
        super().__init__()
        print('Instantiating TestClassFactory')
        self.tex = self._assets.gettexture('black')
        self.mesh = self._assets.getmesh('landMine')
        self.sound = self._assets.getsound('error')
        self.data = self._assets.getdata('langdata')


class TestClassObj(DependencyComponent):
    """Another test dep-obj."""


class TestClass(DependencyComponent):
    """A test dep-obj."""

    _testclass = Dependency(TestClassObj)
    _factoryclass = Dependency(TestClassFactory, 123)
    _factoryclass2 = Dependency(TestClassFactory, 123)

    def __del__(self) -> None:
        print('~TestClass()')

    def __init__(self) -> None:
        super().__init__()
        print('TestClass()')
        self._actor = self._testclass
        print('got actor', self._actor)
        print('have factory', self._factoryclass)
        print('have factory2', self._factoryclass2)


def test_depset() -> None:
    """Test call to try this stuff out..."""
    if bool(False):
        print('running test_depset()...')

        def doit() -> None:
            depset = DependencySet(Dependency(TestClass))
            try:
                depset.resolve()
            except DependencyError as exc:
                for dep in exc.deps:
                    if dep.cls is AssetPackage:
                        print('MISSING ASSET PACKAGE', dep.config)
                    else:
                        raise RuntimeError(
                            f'Unknown dependency error for {dep.cls}'
                        ) from exc
            except Exception as exc:
                print('DependencySet resolve failed with exc type:', type(exc))
            if depset.resolved:
                depset.load()
                testobj = depset.root
                # instance = testclass(123)
                print('INSTANTIATED ROOT:', testobj)

        doit()

        # To test this, add prints on __del__ for stuff used above;
        # everything should be dead at this point if we have no cycles.
        print('everything should be cleaned up...')
        babase.quit()


class DependencyError(Exception):
    """Exception raised when one or more bascenev1.Dependency items are missing.

    Category: **Exception Classes**

    (this will generally be missing assets).
    """

    def __init__(self, deps: list[bascenev1.Dependency]):
        super().__init__()
        self._deps = deps

    @property
    def deps(self) -> list[bascenev1.Dependency]:
        """The list of missing dependencies causing this error."""
        return self._deps
