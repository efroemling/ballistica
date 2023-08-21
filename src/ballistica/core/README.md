# Core Feature Set

This feature set contains basic state and functionality for the overall
Ballistica system.

**Core** is a unique feature set in that it is *not* associated with a Python
module. It instead directly allocates and/or returns itself when its `Import()`
method is called in C++.

This is because, in 'monolithic' builds (where a complete Ballistica app is
compiled into a single binary), **core** itself is responsible for bootstrapping
the Python environment. One can't import something through Python when there's
no Python.

So the purpose of **core** is to be the bare minimum functionality that needs to
exist to bootstrap Python.
