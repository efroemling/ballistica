# Shared Source

This is the one directory under **src/ballistica** that does *not* correspond
to a feature-set. All code in this directory lives in the root 'ballistica'
namespace and can be used by any feature-set.

Likewise, code here must be sure to not have any dependencies on any
feature sets aside from 'core'.