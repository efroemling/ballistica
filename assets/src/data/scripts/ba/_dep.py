# Copyright (c) 2011-2019 Eric Froemling
"""Functionality related to object/asset dependencies."""
# pylint: disable=redefined-builtin

from __future__ import annotations

import weakref
from typing import (Generic, TypeVar, TYPE_CHECKING, cast, Type, overload)

import _ba
from ba import _general

if TYPE_CHECKING:
    from typing import Optional, Any, Dict, List, Set
    import ba

T = TypeVar('T', bound='DepComponent')
TI = TypeVar('TI', bound='InstancedDepComponent')
TS = TypeVar('TS', bound='StaticDepComponent')


class Dependency(Generic[T]):
    """A dependency on a DepComponent (with an optional config).

    Category: Dependency Classes

    This class is used to request and access functionality provided
    by other DepComponent classes from a DepComponent class.
    The class functions as a descriptor, allowing dependencies to
    be added at a class level much the same as properties or methods
    and then used with class instances to access those dependencies.
    For instance, if you do 'floofcls = ba.Dependency(FloofClass)' you
    would then be able to instantiate a FloofClass in your class's
    methods via self.floofcls().
    """

    def __init__(self, cls: Type[T], config: Any = None):
        """Instantiate a Dependency given a ba.DepComponent subtype.

        Optionally, an arbitrary object can be passed as 'config' to
        influence dependency calculation for the target class.
        """
        self.cls: Type[T] = cls
        self.config = config
        self._hash: Optional[int] = None

    def get_hash(self) -> int:
        """Return the dependency's hash, calculating it if necessary."""
        if self._hash is None:
            self._hash = _general.make_hash((self.cls, self.config))
        return self._hash

    # NOTE: it appears that mypy is currently not able to do overloads based
    # on the type of 'self', otherwise we could just overload this to
    # return different things based on self's type and avoid the need for
    # the fake dep classes below.
    # See https://github.com/python/mypy/issues/5320
    # noinspection PyShadowingBuiltins
    def __get__(self, obj: Any, type: Any = None) -> Any:
        if obj is None:
            raise TypeError("Dependency must be accessed through an instance.")

        # We expect to be instantiated from an already living DepComponent
        # with valid dep-data in place..
        assert type is not None
        depdata = getattr(obj, '_depdata')
        if depdata is None:
            raise RuntimeError("Invalid dependency access.")
        assert isinstance(depdata, DepData)

        # Now look up the data for this particular dep
        depset = depdata.depset()
        assert isinstance(depset, DepSet)
        assert self._hash in depset.depdatas
        depdata = depset.depdatas[self._hash]
        assert isinstance(depdata, DepData)
        if depdata.valid is False:
            raise RuntimeError(
                f'Accessing DepComponent {depdata.cls} in an invalid state.')
        assert self.cls.dep_get_payload(depdata) is not None
        return self.cls.dep_get_payload(depdata)


# We define a 'Dep' which at runtime simply aliases the Dependency class
# but in type-checking points to two overloaded functions based on the argument
# type. This lets the type system know what type of object the Dep represents.
# (object instances in the case of StaticDep classes or object types in the
# case of regular deps) At some point hopefully we can replace this with a
# simple overload in Dependency.__get__ based on the type of self
# (see note above).
if not TYPE_CHECKING:
    Dep = Dependency
else:

    class _InstanceDep(Dependency[TI]):
        """Fake stub we use to tell the type system we provide a type."""

        # noinspection PyShadowingBuiltins
        def __get__(self, obj: Any, type: Any = None) -> Type[TI]:
            return cast(Type[TI], None)

    class _StaticDep(Dependency[TS]):
        """Fake stub we use to tell the type system we provide an instance."""

        # noinspection PyShadowingBuiltins
        def __get__(self, obj: Any, type: Any = None) -> TS:
            return cast(TS, None)

    # pylint: disable=invalid-name
    # noinspection PyPep8Naming
    @overload
    def Dep(cls: Type[TI], config: Any = None) -> _InstanceDep[TI]:
        """test"""
        return _InstanceDep(cls, config)

    # noinspection PyPep8Naming
    @overload
    def Dep(cls: Type[TS], config: Any = None) -> _StaticDep[TS]:
        """test"""
        return _StaticDep(cls, config)

    # noinspection PyPep8Naming
    def Dep(cls: Any, config: Any = None) -> Any:
        """test"""
        return Dependency(cls, config)

    # pylint: enable=invalid-name


class BoundDepComponent:
    """A DepComponent class bound to its DepSet data.

    Can be called to instantiate the class with its data properly in place."""

    def __init__(self, cls: Any, depdata: DepData):
        self.cls = cls
        # BoundDepComponents can be stored on depdatas so we use weakrefs
        # to avoid dependency cycles.
        self.depdata = weakref.ref(depdata)

    def __call__(self, *args: Any, **keywds: Any) -> Any:
        # We don't simply call our target type to instantiate it;
        # instead we manually call __new__ and then __init__.
        # This allows us to inject its data properly before __init__().
        obj = self.cls.__new__(self.cls, *args, **keywds)
        obj._depdata = self.depdata()
        assert isinstance(obj._depdata, DepData)
        obj.__init__(*args, **keywds)
        return obj


class DepComponent:
    """Base class for all classes that can act as dependencies.

    category: Dependency Classes
    """

    _depdata: DepData

    def __init__(self) -> None:
        """Instantiate a DepComponent."""

        # For now lets issue a warning if these are instantiated without
        # data; we'll make this an error once we're no longer seeing warnings.
        depdata = getattr(self, '_depdata', None)
        if depdata is None:
            print(f'FIXME: INSTANTIATING DEP CLASS {type(self)} DIRECTLY.')

        self.context = _ba.Context('current')

    @classmethod
    def is_present(cls, config: Any = None) -> bool:
        """Return whether this component/config is present on this device."""
        del config  # Unused here.
        return True

    @classmethod
    def get_dynamic_deps(cls, config: Any = None) -> List[Dependency]:
        """Return any dynamically-calculated deps for this component/config.

        Deps declared statically as part of the class do not need to be
        included here; this is only for additional deps that may vary based
        on the dep config value. (for instance a map required by a game type)
        """
        del config  # Unused here.
        return []

    @classmethod
    def dep_get_payload(cls, depdata: DepData) -> Any:
        """Return user-facing data for a loaded dep.

        If this dep does not yet have a 'payload' value, it should
        be generated and cached.  Otherwise the existing value
        should be returned.
        This is the value given for a DepComponent when accessed
        through a Dependency instance on a live object, etc.
        """
        del depdata  # Unused here.


class DepData:
    """Data associated with a dependency in a dependency set."""

    def __init__(self, depset: DepSet, dep: Dependency[T]):
        # Note: identical Dep/config pairs will share data, so the dep
        # entry on a given Dep may not point to.
        self.cls = dep.cls
        self.config = dep.config

        # Arbitrary data for use by dependencies in the resolved set
        # (the static instance for static-deps, etc).
        self.payload: Any = None
        self.valid: bool = False

        # Weakref to the depset that includes us (to avoid ref loop).
        self.depset = weakref.ref(depset)


class DepSet(Generic[TI]):
    """Set of resolved dependencies and their associated data."""

    def __init__(self, root: Dependency[TI]):
        self.root = root
        self._resolved = False

        # Dependency data indexed by hash.
        self.depdatas: Dict[int, DepData] = {}

        # Instantiated static-components.
        self.static_instances: List[StaticDepComponent] = []

    def __del__(self) -> None:
        # When our dep-set goes down, clear out all dep-data payloads
        # so we can throw errors if anyone tries to use them anymore.
        for depdata in self.depdatas.values():
            depdata.payload = None
            depdata.valid = False

    def resolve(self) -> None:
        """Resolve the total set of required dependencies for the set.

        Raises a ba.DependencyError if dependencies are missing (or other
        Exception types on other errors).
        """

        if self._resolved:
            raise Exception("DepSet has already been resolved.")

        print('RESOLVING DEP SET')

        # First, recursively expand out all dependencies.
        self._resolve(self.root, 0)

        # Now, if any dependencies are not present, raise an Exception
        # telling exactly which ones (so hopefully they'll be able to be
        # downloaded/etc.
        missing = [
            Dependency(entry.cls, entry.config)
            for entry in self.depdatas.values()
            if not entry.cls.is_present(entry.config)
        ]
        if missing:
            from ba._error import DependencyError
            raise DependencyError(missing)

        self._resolved = True
        print('RESOLVE SUCCESS!')

    def get_asset_package_ids(self) -> Set[str]:
        """Return the set of asset-package-ids required by this dep-set.

        Must be called on a resolved dep-set.
        """
        ids: Set[str] = set()
        if not self._resolved:
            raise Exception('Must be called on a resolved dep-set.')
        for entry in self.depdatas.values():
            if issubclass(entry.cls, AssetPackage):
                assert isinstance(entry.config, str)
                ids.add(entry.config)
        return ids

    def load(self) -> Type[TI]:
        """Attach the resolved set to the current context.

        Returns a wrapper which can be used to instantiate the root dep.
        """
        # NOTE: stuff below here should probably go in a separate 'instantiate'
        # method or something.
        if not self._resolved:
            raise Exception("Can't instantiate an unresolved DepSet")

        # Go through all of our dep entries and give them a chance to
        # preload whatever they want.
        for entry in self.depdatas.values():
            # First mark everything as valid so recursive loads don't fail.
            assert entry.valid is False
            entry.valid = True
        for entry in self.depdatas.values():
            # Do a get on everything which will init all payloads
            # in the proper order recursively.
            # NOTE: should we guard for recursion here?...
            entry.cls.dep_get_payload(entry)

        # NOTE: like above, we're cheating here and telling the type
        # system we're simply returning the root dependency class, when
        # actually it's a bound-dependency wrapper containing its data/etc.
        # ..Should fix if/when mypy is smart enough to preserve type safety
        # on the wrapper's __call__()
        rootdata = self.depdatas[self.root.get_hash()]
        return cast(Type[TI], BoundDepComponent(self.root.cls, rootdata))

    def _resolve(self, dep: Dependency[T], recursion: int) -> None:

        # Watch for wacky infinite dep loops.
        if recursion > 10:
            raise Exception('Max recursion reached')

        hashval = dep.get_hash()

        if hashval in self.depdatas:
            # Found an already resolved one; we're done here.
            return

        # Add our entry before we recurse so we don't repeat add it if
        # there's a dependency loop.
        self.depdatas[hashval] = DepData(self, dep)

        # Grab all Dependency instances we find in the class.
        subdeps = [
            cls for cls in dep.cls.__dict__.values()
            if isinstance(cls, Dependency)
        ]

        # ..and add in any dynamic ones it provides.
        subdeps += dep.cls.get_dynamic_deps(dep.config)
        for subdep in subdeps:
            self._resolve(subdep, recursion + 1)


class InstancedDepComponent(DepComponent):
    """Base class for DepComponents intended to be instantiated as needed."""

    @classmethod
    def dep_get_payload(cls, depdata: DepData) -> Any:
        """Data provider override; returns a BoundDepComponent."""
        if depdata.payload is None:
            # The payload we want for ourself in the dep-set is simply
            # the bound-def that users can use to instantiate our class
            # with its data properly intact. We could also just store
            # the class and instantiate one of these each time.
            depdata.payload = BoundDepComponent(cls, depdata)
        return depdata.payload


class StaticDepComponent(DepComponent):
    """Base for DepComponents intended to be instanced once and shared."""

    @classmethod
    def dep_get_payload(cls, depdata: DepData) -> Any:
        """Data provider override; returns shared instance."""
        if depdata.payload is None:
            # We want to share a single instance of our object with anything
            # in the set that requested it, so create a temp bound-dep and
            # create an instance from that.
            depcls = BoundDepComponent(cls, depdata)

            # Instances have a strong ref to depdata so we can't give
            # depdata a strong reference to it without creating a cycle.
            # We also can't just weak-ref the instance or else it won't be
            # kept alive. Our solution is to stick strong refs to all static
            # components somewhere on the DepSet.
            instance = depcls()
            assert depdata.depset
            depset2 = depdata.depset()
            assert depset2 is not None
            depset2.static_instances.append(instance)
            depdata.payload = weakref.ref(instance)
        assert isinstance(depdata.payload, weakref.ref)
        payload = depdata.payload()
        if payload is None:
            raise RuntimeError(
                f'Accessing DepComponent {cls} in an invalid state.')
        return payload


class AssetPackage(StaticDepComponent):
    """DepComponent representing a bundled package of game assets."""

    def __init__(self) -> None:
        super().__init__()
        # pylint: disable=no-member
        assert isinstance(self._depdata.config, str)
        self.package_id = self._depdata.config
        print(f'LOADING ASSET PACKAGE {self.package_id}')

    @classmethod
    def is_present(cls, config: Any = None) -> bool:
        assert isinstance(config, str)

        # Temp: hard-coding for a single asset-package at the moment.
        if config == 'stdassets@1':
            return True
        return False

    def gettexture(self, name: str) -> ba.Texture:
        """Load a named ba.Texture from the AssetPackage.

        Behavior is similar to ba.gettexture()
        """
        return _ba.get_package_texture(self, name)

    def getmodel(self, name: str) -> ba.Model:
        """Load a named ba.Model from the AssetPackage.

        Behavior is similar to ba.getmodel()
        """
        return _ba.get_package_model(self, name)

    def getcollidemodel(self, name: str) -> ba.CollideModel:
        """Load a named ba.CollideModel from the AssetPackage.

        Behavior is similar to ba.getcollideModel()
        """
        return _ba.get_package_collide_model(self, name)

    def getsound(self, name: str) -> ba.Sound:
        """Load a named ba.Sound from the AssetPackage.

        Behavior is similar to ba.getsound()
        """
        return _ba.get_package_sound(self, name)

    def getdata(self, name: str) -> ba.Data:
        """Load a named ba.Data from the AssetPackage.

        Behavior is similar to ba.getdata()
        """
        return _ba.get_package_data(self, name)


class TestClassFactory(StaticDepComponent):
    """Another test dep-obj."""

    _assets = Dep(AssetPackage, 'stdassets@1')

    def __init__(self) -> None:
        super().__init__()
        print("Instantiating TestClassFactory")
        self.tex = self._assets.gettexture('black')
        self.model = self._assets.getmodel('landMine')
        self.sound = self._assets.getsound('error')
        self.data = self._assets.getdata('langdata')


class TestClassObj(InstancedDepComponent):
    """Another test dep-obj."""


class TestClass(InstancedDepComponent):
    """A test dep-obj."""

    _actorclass = Dep(TestClassObj)
    _factoryclass = Dep(TestClassFactory, 123)
    _factoryclass2 = Dep(TestClassFactory, 124)

    def __init__(self, arg: int) -> None:
        super().__init__()
        del arg
        self._actor = self._actorclass()
        print('got actor', self._actor)
        print('have factory', self._factoryclass)
        print('have factory2', self._factoryclass2)


def test_depset() -> None:
    """Test call to try this stuff out..."""
    # noinspection PyUnreachableCode
    if False:  # pylint: disable=using-constant-test
        print('running test_depset()...')

        def doit() -> None:
            from ba._error import DependencyError
            depset = DepSet(Dep(TestClass))
            resolved = False
            try:
                depset.resolve()
                resolved = True
            except DependencyError as exc:
                for dep in exc.deps:
                    if dep.cls is AssetPackage:
                        print('MISSING PACKAGE', dep.config)
                    else:
                        raise Exception('unknown dependency error for ' +
                                        str(dep.cls))
            except Exception as exc:
                print('DepSet resolve failed with exc type:', type(exc))
            if resolved:
                testclass = depset.load()
                instance = testclass(123)
                print("INSTANTIATED ROOT:", instance)

        doit()

        # To test this, add prints on __del__ for stuff used above;
        # everything should be dead at this point if we have no cycles.
        print('everything should be cleaned up...')
        _ba.quit()
