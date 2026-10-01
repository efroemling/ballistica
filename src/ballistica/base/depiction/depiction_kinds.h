// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_DEPICTION_DEPICTION_KINDS_H_
#define BALLISTICA_BASE_DEPICTION_DEPICTION_KINDS_H_

namespace ballistica::base {

/// Register the depiction kinds base draws itself (character icons,
/// names, images). Called once, before the registry first makes a
/// depiction. Logic thread.
void RegisterBaseDepictionKinds();

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_DEPICTION_DEPICTION_KINDS_H_
