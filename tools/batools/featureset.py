# Released under the MIT License. See LICENSE for details.
#
"""Functionality for working with spinoff feature-sets.

Feature-sets are logical groupings of functionality that can be stripped
out of or added in to spinoff dst projects. This allows for more high level
dependency management and organization than would be possible through
filtering alone.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from efro.util import snake_case_to_title
from efro.error import CleanError
from batools.dummymodule import DummyModuleDef

if TYPE_CHECKING:
    pass

# Cached feature-sets indexed by project root.
_g_feature_sets: dict[str, list[FeatureSet]] = {}


class FeatureSet:
    """Defines a feature-set."""

    _active_feature_set: FeatureSet | None = None

    # Define our types here at the class level so docs generators can do
    # a better job.
    requirements: set[str]
    soft_requirements: set[str]
    has_python_binary_module: bool
    has_python_app_subsystem: bool
    python_app_subsystem_dependencies: set[str]
    allow_as_soft_requirement: bool
    dummy_module_def: DummyModuleDef
    cpp_namespace_check_disable_files: set[str]

    def __init__(self, name: str):

        # (internal; don't set this)
        self.internal = False

        #: Other feature-sets this one requires. Any spinoff project that
        #: includes our feature-set will implicitly include our
        #: requirements as well. We are allowed to access Python modules
        #: of our requirements directly, unlike soft-requirements where
        #: we must limit our access to their app subsystem.
        self.requirements = set()

        #: Feature-sets we can use but can survive without. All usage of
        #: soft requirements must be through app-subsystems
        #: (`ba*.app.foo_bar` for feature-set `foo_bar`, etc.). We must
        #: be prepared for these subsystems to be missing (set to None)
        #: and we must never import their modules directly (since they
        #: might not exist). Note that all featuresets we soft-require
        #: must have 'allow_as_soft_requirement' enabled. While it is
        #: possible to programmatically check for the presence of *any*
        #: feature-set, officially listing soft-requirements ensures that
        #: any expected app-subsystems are in place even for feature-sets
        #: not included in the spinoff project (though be aware their
        #: type annotations will be 'Any | None' in that case instead of
        #: the usual 'FooBarSubsystem | None' due to 'FooBarSubsystem'
        #: not actually existing).
        self.soft_requirements = set()

        #: Whether this featureset defines a native Python module within
        #: its C++ code. The build process will try to create dummy
        #: modules for all native modules, so to avoid errors you must
        #: tell it if you don't have one.
        self.has_python_binary_module = True

        #: If True, for feature-set 'foo_bar', the build system will
        #: define a 'ba*.app.foo_bar' attr which points to a lazy
        #: loaded instance of type 'bafoobar.FooBarSubsystem'.
        self.has_python_app_subsystem = False

        #: By default, Python app subsystems will be created in
        #: alphabetical order based on their feature set name. All
        #: subsystem callbacks adhere to this ordering. If there are any
        #: feature sets whose subsystems should always be created before
        #: this one's, list them here. Note that this does not affect
        #: whether or not the feature set is included in the build; only
        #: the init order in cases when it is.
        self.python_app_subsystem_dependencies = set()

        #: If True, feature-set 'foo_bar', will be allowed to be listed
        #: as a soft-requirement of other feature sets and its
        #: python-app-subsystem will be annotated as type
        #: 'bafoobar.FooBarSubsystem | None' instead of simply
        #: 'bafoobar.FooBarSubsystem'. This forces type-checked code to
        #: account for the possibility that it will not be present. Note
        #: that this currently requires has_python_app_subsystem to be
        #: True (because if a soft-required feature-set is missing we
        #: must assume that is the case anyway because there's no way to
        #: know).
        self.allow_as_soft_requirement = False

        #: Override this to customize how your dummy module is generated.
        self.dummy_module_def = DummyModuleDef()

        #: Paths of files we should disable c++ namespace checks for.
        #: (generally external-originating code that doesn't conform to our
        #: ballistica feature-set based namespace scheme)
        self.cpp_namespace_check_disable_files = set()

        self.validate_name(name)

        # Our standard snake_case name.
        self._name = name

        # Generate a default title form (foo_bar -> Foo Bar). The
        # feature-set config can customize this; for example a word like
        # base_sdk might look better as 'Base SDK' instead of the
        # default 'Base Sdk'.
        self._name_title = snake_case_to_title(self._name)

    @property
    def name(self) -> str:
        """Our base name."""
        return self._name

    @property
    def name_compact(self) -> str:
        """Compact name variation (foo_bar -> foobar). Used for Python bits."""
        return self._name.replace('_', '')

    @property
    def name_title(self) -> str:
        """Title name variation (foo_bar -> Foo Bar). For pretty stuff."""
        return self._name_title

    @name_title.setter
    def name_title(self, val: str) -> None:
        """Set custom title name."""

        # Make sure they don't pass underscores; title versions are just
        # words and spaces.
        if '_' in val:
            raise CleanError(
                f"Custom FeatureSet name_title '{val}' contains"
                ' underscores; it must contain only spaces.'
            )

        # Make sure the value they're providing still matches their base
        # name. It could be easy to let this fall out of sync
        # accidentally.
        if val.lower().replace(' ', '_') != self._name:
            raise CleanError(
                f"Custom FeatureSet name_title '{val}' letters/spacing"
                f" does not match base name '{self._name}'."
            )

        # Ok val; we will accept you.
        self._name_title = val

    @property
    def name_camel(self) -> str:
        """Camel case name (foo_bar -> FooBar). Used for classes, etc."""
        # We want to use any of the customization applied to name_title
        # so let's just give _name_title with spaces stripped out.
        return self._name_title.replace(' ', '')

    @property
    def name_python_package(self) -> str:
        """Python package name (foo_bar -> bafoobar)."""
        return f'ba{self.name_compact}'

    @property
    def name_python_package_meta(self) -> str:
        """The name of our meta Python package."""
        return f'ba{self.name_compact}meta'

    @property
    def name_python_package_tests(self) -> str:
        """The name of our Python tests package."""
        return f'test_{self.name}'

    @property
    def name_python_binary_module(self) -> str:
        """Python binary module name (foo_bar -> _bafoobar)."""
        return f'_ba{self.name_compact}'

    @staticmethod
    def validate_name(name: str) -> None:
        """Validate a standard snake-case feature-set name.

        Throws descriptive CleanErrors if provided name is invalid.
        """

        # Disallow empty.
        if not name:
            raise CleanError('Feature set name cannot be empty.')

        # Require starting with a letter.
        if not name[0].isalpha():
            raise CleanError(
                f"Invalid feature set name '{name}'"
                ' - names must start with a letter.'
            )

        # Require only letters, numbers, and underscores.
        if not name.replace('_', '').isalnum():
            raise CleanError(
                f"Invalid feature set name '{name}'"
                ' - only letters, numbers, and underscores are allowed.'
            )

        # Require all lowercase.
        if not name.islower():
            raise CleanError(
                f"Invalid feature set name '{name}'"
                ' - only lowercase letters are allowed.'
            )

        # Disallow leading, trailing, or consecutive underscores.
        # (these will result in a '' in the split results which evals to False)
        if not all(name.split('_')):
            raise CleanError(
                f"Invalid feature set name '{name}'"
                ' - leading, trailing, and consecutive underscores are'
                ' not allowed.'
            )

    @property
    def path_config_file(self) -> str:
        """Project-relative path to the file defining this feature-set."""
        return f'config/featuresets/featureset_{self.name}.py'

    @property
    def path_python_package(self) -> str:
        """Project-relative path for this feature-set's Python package.

        Note that this does not mean that the package actually exists;
        this just shows where it would.
        """
        return f'src/assets/ba_data/python/{self.name_python_package}'

    @property
    def path_python_package_meta(self) -> str:
        """Project-relative path for this feature-set's Python meta package.

        Note that this does not mean that the package actually exists;
        this just shows where it would.
        """
        return f'src/meta/{self.name_python_package_meta}'

    @property
    def path_python_package_tests(self) -> str:
        """Project-relative path for this feature-set's Python tests package.

        Note that this does not mean that the package actually exists;
        this just shows where it would.
        """
        return f'tests/{self.name_python_package_tests}'

    @property
    def path_native_source(self) -> str:
        """Project-relative path for this feature-set's native source.

        Note that this does not mean that such source actually exists;
        this just shows where it would.
        """
        return f'src/ballistica/{self.name}'

    @property
    def paths(self) -> list[str]:
        """Return all file/dir paths associated with this feature-set.

        Paths are project relative and may not actually exist; this just
        gives their theoretical locations.
        """
        return [
            self.path_config_file,
            self.path_python_package,
            self.path_native_source,
            self.path_python_package_meta,
            self.path_python_package_tests,
        ]

    @classmethod
    def get_active(cls) -> FeatureSet:
        """Return the FeatureSet currently being defined.

        For use by settings scripts.
        """
        if cls._active_feature_set is None:
            raise RuntimeError('No FeatureSet being actively defined.')
        return cls._active_feature_set

    def apply_config(self, config_path: str) -> None:
        """Apply a user config to this feature-set."""
        # pylint: disable=exec-used
        try:
            assert self._active_feature_set is None
            type(self)._active_feature_set = self

            # Apply both src and dist spinoff configs.
            exec_context: dict = {}
            with open(config_path, encoding='utf-8') as infile:
                config_contents = infile.read()

            # Use compile here so we can provide a nice file path for
            # error tracebacks.
            exec(
                compile(config_contents, config_path, 'exec'),
                exec_context,
                exec_context,
            )

        finally:
            assert type(self)._active_feature_set is self
            type(self)._active_feature_set = None

    @classmethod
    def get_all_for_project(cls, project_root: str) -> list[FeatureSet]:
        """Return all feature-sets for the current project."""
        project_root_abs = os.path.abspath(project_root)

        # Only do this once per project.
        if project_root_abs not in _g_feature_sets:
            _g_feature_sets[project_root_abs] = _build_feature_set_list(
                project_root_abs
            )
        return _g_feature_sets[project_root_abs]

    @classmethod
    def resolve_requirements(
        cls, featuresets: list[FeatureSet], reqs: set[str]
    ) -> set[str]:
        """Resolve all required feature-sets based on a given set of them.

        Throws descriptive CleanErrors if any are missing.
        """
        fsets = {f.name: f for f in featuresets}
        reqs_out = set[str]()
        for req in reqs:
            cls._resolve_requirements(fsets, reqs_out, req)
        return reqs_out

    @classmethod
    def _resolve_requirements(
        cls, featuresets: dict[str, FeatureSet], reqs_out: set[str], req: str
    ) -> None:
        if req in reqs_out:
            return
        featureset = featuresets.get(req)
        if featureset is None:
            raise CleanError(f"Required featureset '{req}' not found.")
        reqs_out.add(req)
        for sub_req in featureset.requirements:
            cls._resolve_requirements(featuresets, reqs_out, sub_req)


def _build_feature_set_list(project_root: str) -> list[FeatureSet]:
    featuresets: list[FeatureSet] = []
    fsdir = os.path.join(project_root, 'config', 'featuresets')
    prefix = 'featureset_'
    filenames = os.listdir(fsdir)
    for filename in sorted(filenames):
        if not filename.endswith('.py'):
            continue
        if not filename.startswith(prefix):
            raise CleanError(
                f"Found invalid featuresetdef filename: '{filename}'."
            )
        basename, _ext = os.path.splitext(filename.removeprefix(prefix))
        featureset = FeatureSet(basename)
        featureset.apply_config(os.path.join(fsdir, filename))
        featuresets.append(featureset)

    # Run some sanity checks to make sure our full set of featuresets
    # don't have clashing names/etc. (for instance, foo_v1 and foov_1
    # would resolve to the same foov1 py module name).

    featuresets_by_name = {f.name: f for f in featuresets}
    assert len(featuresets_by_name) == len(featuresets)

    assert len({f.name_compact for f in featuresets}) == len(featuresets)
    assert len({f.name_compact for f in featuresets}) == len(featuresets)

    for featureset in featuresets:
        # Require soft-req-enabled feature-sets to have app subsystems
        # enabled (see above for explanation).
        if featureset.allow_as_soft_requirement:
            if not featureset.has_python_app_subsystem:
                raise CleanError(
                    f"Feature-set '{featureset.name}'"
                    " has 'allow_as_soft_requirement' set to True but"
                    " 'has_python_app_subsystem' set to False;"
                    ' soft-requireable feature-sets currently MUST'
                    ' provide a subsystem.'
                )

        for req in featureset.requirements:
            if req == featureset.name:
                raise CleanError(
                    f"Feature-set '{featureset.name}'"
                    f' lists itself as a requirement; this is not allowed.'
                )
            if req not in featuresets_by_name:
                raise CleanError(
                    f"Undefined feature-set '{req}'"
                    f' listed as a requirement of feature-set'
                    f" '{featureset.name}'."
                )
        for req in featureset.soft_requirements:
            if req == featureset.name:
                raise CleanError(
                    f"Feature-set '{featureset.name}'"
                    f' lists itself as a soft-requirement; this is not allowed.'
                )
            if (
                req in featuresets_by_name
                and not featuresets_by_name[req].allow_as_soft_requirement
            ):
                raise CleanError(
                    f"Feature-set '{req}'"
                    f' is listed as a soft-requirement of feature-set'
                    f" '{featureset.name}' but is not allowed to be soft"
                    ' required.'
                )

    return featuresets
