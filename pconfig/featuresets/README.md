# Ballistica Feature Sets

This directory contains a config file for each feature-set in the project.
Feature sets are high level subsets of an engine or app which can be easily
added, removed, duplicated, etc.

### Naming Conventions

Feature sets should have lowercase alphanumeric names with underscores between
words. An example would be `foo_bar`. Variations of this name may be used
throughout code; for example `FooBar` may be used in class names where
camel-case is standard or `foobar` may be used in Python module names where
brevity is desirable.

### Locations

The build system looks for feature-set files in specific predefined locations
with specific naming conventions:

- **Feature Set Definition**: To define feature set `foo_bar`, a file must exist
  in this directory called `featureset_foo_bar.py`.
- **Python Package**: If feature set `foo_bar` provides a Python package, it
  should be a directory named `bafoobar` ('ba' prefix, name with spaces removed)
  that lives under [src/assets/ba_data/python](../../src/assets/ba_data/python).
- **Native Code**: If feature set `foo_bar` provides a native component (C++
  code or otherwise) it should live in a directory named `foo_bar` (unmodified
  feature set name) under [src/ballistica](../../src/ballistica).
- **Meta Package**: If feature set `foo_bar` provides a meta package (that is,
  code or data used to generate other source code), it should be a directory
  named `bafoobarmeta` ('ba' prefix, name with spaces removed, 'meta' suffix)
  that lives under [src/meta](../../src/meta).
- **Test Package**: If feature set `foo_bar` provides a set of tests, it should
  be a directory named `test_foo_bar` ('test_' prefix, unmodified feature set
  name) under [tests](../../tests).

