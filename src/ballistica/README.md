# Ballistica Native Layer Source

This directory is where most of Ballistica's 'native' layer lives. This code is
mostly C++ but with a smattering of other languages depending on the platform.
It gets compiled into several Python binary modules such as `_babase` or
`_bascenev1` which are then used by user-facing Python packages such as
[babase](../assets/ba_data/python/babase) or
[bascenev1](../assets/ba_data/python/bascenev1). Be aware that this separation
into distinct binary modules is largely for logic/organization purposes and does
not imply separate binaries; it is common for a Ballistica app to be
compiled into a single monolithic binary containing all of these modules
and often the Python library itself.

## Feature Sets and C++

Similar to other places in the engine layout, code here is organized based on
[feature-sets](../../config/featuresets). Feature-sets make it easy to isolate,
add, and remove functionality from a Ballistica app at a high level. The only
subdirectory here *not* associated with a feature-set is 'shared'.

On the Python side, a feature-set generally (but not always) has a corresponding
Python package. To access the `scene_v1` feature-set from Python, for instance,
one does `import bascenev1`. In turn, `bascenev1` itself may import
functionality it needs from other feature-set packages such as `babase` or
`baclassic`. And so on and so on. In this way, Python's module system provides
an elegant way to split the Python parts of the engine into logical pieces and
init each one only when it is needed.

In order to keep things as consistent as possible between the Python and native
layers, our native layer has recently been redesigned to sit on top of Python's
module system. So even though our feature-sets still often talk to each other
directly through native C++ interfaces, they go through Python's import
mechanism to init each other and acquire those interfaces.

The benefits of this setup are safety and consistency. It does not matter if we
do `import bascenev1` in Python or `scene_v1::SceneV1FeatureSet::Import()` from
C++; in either case we can be sure that both Python and C++ parts of the
`scene_v1` feature-set have been inited and are ready for use. In earlier
iterations of the feature-set system, the Python and C++ worlds were more
independent; one had to take care to avoid using certain parts of a feature-set
from C++ if that feature-set's Python side had not yet been imported, which was
both more confusing and more error prone.

## C++ 'Module' Mechanism Details

At the C++ level, we use a combination of C++ namespaces and global variables
to mimic Python's module mechanism.

Python consists of modules that import other modules (or stuff from within those
modules) into their own global namespaces for their own code to use. So when you
write `import babase` at the top of your Python module, this is what you are
doing - you are creating a `babase` global for yourself that you can then use
from anywhere in your module.

Our analog to Python modules in Ballistica C++ is the
`FeatureSetNativeComponent` class. Feature-sets can define a subclass of
`FeatureSetNativeComponent` which exposes some C++ functionality, and other
feature-sets can call that class's static `Import()` method to get access to the
shared single instance of that class. So far this sounds pretty similar to
Python modules.

Where it breaks down, however, is the concept of module globals - the `babase`
we imported at the top of our Python script and can then use throughout it. Yes,
we could create a global `g_base` pointer in C++ for the `BaseFeatureSet` we
just imported, but then *all* our C++ code can access that global and there's no
elegant way to ensure it has been imported before being used. Alternately we
could have *no* globals and just have each `FeatureSetNativeComponent` store
pointers to any other `FeatureSetNativeComponent` it uses, but then we'd have to
be passing around, storing, and jumping through tons of feature-set pointers
constantly to do anything in the engine.

In the end, the happy-medium solution employed by Ballistica is a combination of
globals and namespaces. Each feature-set has its own C++ namespace that is
basically thought of as its module namespace in Python. When a feature-set gets
imported, it does a one-time import of any other feature-sets that it uses and
stores pointers to them in its own private namespace globals. So the `scene_v1`
feature-set, when imported, might import the `base` feature-set as a `g_base`
global. But because `scene_v1` has its own namespace, this global will actually
be `ballistica::scene_v1::g_base` which will be distinct from any `g_base`
global held by any other feature-set. So as long as each feature-set correctly
lives in its own namespace and uses only its own set of globals, things should
work pretty much as they do on the Python layer; feature-sets simply import
what they use when they themselves are imported and all code throughout the
feature-set assumes it is safe to use those imported things.

Check out the [Template Feature Set](template_fs) for examples of wrangling
globals and namespaces to implement a feature-set-front-end in C++.
