/*************************************************************************
 *                                                                       *
 * Open Dynamics Engine, Copyright (C) 2001,2002 Russell L. Smith.       *
 * All rights reserved.  Email: russ@q12.org   Web: www.q12.org          *
 *                                                                       *
 * This library is free software; you can redistribute it and/or         *
 * modify it under the terms of EITHER:                                  *
 *   (1) The GNU Lesser General Public License as published by the Free  *
 *       Software Foundation; either version 2.1 of the License, or (at  *
 *       your option) any later version. The text of the GNU Lesser      *
 *       General Public License is included with this library in the     *
 *       file LICENSE.TXT.                                               *
 *   (2) The BSD-style license that is included with this library in     *
 *       the file LICENSE-BSD.TXT.                                       *
 *                                                                       *
 * This library is distributed in the hope that it will be useful,       *
 * but WITHOUT ANY WARRANTY; without even the implied warranty of        *
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the files    *
 * LICENSE.TXT and LICENSE-BSD.TXT for more details.                     *
 *                                                                       *
 *************************************************************************/

#ifndef _ODE_UTIL_H_
#define _ODE_UTIL_H_

#include "ode/ode_objects_private.h"

#include <stdio.h>
#include <stdlib.h>


void dInternalHandleAutoDisabling (dxWorld *world, dReal stepsize);
void dxStepBody (dxBody *b, dReal h);

typedef void (*dstepper_fn_t) (dxWorld *world, dxBody * const *body, int nb,
        dxJoint * const *_joint, int nj, dReal stepsize);

void dxProcessIslands (dxWorld *world, dReal stepsize, dstepper_fn_t stepper);



/////////ERIC ADDED STUFF//////////////////////
#define VALUE_TESTING 0

// Set to 1 to printf whenever heap allocation is used instead of alloca.
// Useful for checking whether alloca thresholds are sized appropriately.
#define BA_ODE_ALLOCA_DEBUG 0

// ericf addition: a bare-bones scoped heap buffer, used by TRIXY_ALLOCA
// below for allocations too big to safely put on the stack.
class dxHeapBuffer {
public:
  dxHeapBuffer() : _ptr(NULL) {}
  ~dxHeapBuffer() { free(_ptr); }
  void allocate(size_t size) {
    free(_ptr);
    _ptr = malloc(size);
    dIASSERT(_ptr);
  }
  void* getPtr() const { return _ptr; }
private:
  dxHeapBuffer(const dxHeapBuffer&);
  dxHeapBuffer& operator=(const dxHeapBuffer&);
  void* _ptr;
};

// ericf addition: alloca for small sizes (fast), heap for big ones.
// alloca'd memory lives until the *calling function* returns, so big
// counts (modded games spawning thousands of objects) can otherwise blow
// past the thread's stack. Heap memory is freed when `name ## BUF` goes
// out of scope, so declare it at the scope the memory must live for.
#if BA_ODE_ALLOCA_DEBUG
#define TRIXY_ALLOCA_THRESHOLD(name, type, n, threshold)                 \
  dxHeapBuffer name##BUF;                                              \
  if ((size_t)(n) > (size_t)(threshold)) {                             \
    printf("ODE_ALLOCA_DEBUG: TRIXY_ALLOCA heap: " #name               \
           " size=%lu threshold=%lu\n",                                \
           (unsigned long)(n), (unsigned long)(threshold));            \
    name##BUF.allocate((n));                                           \
    name = (type*)name##BUF.getPtr();                                  \
  } else {                                                             \
    name = (type*)dALLOCA16((n));                                      \
    dIASSERT(name);                                                    \
  }
#else
#define TRIXY_ALLOCA_THRESHOLD(name, type, n, threshold)                 \
  dxHeapBuffer name##BUF;                                              \
  if ((size_t)(n) > (size_t)(threshold)) {                             \
    name##BUF.allocate((n));                                           \
    name = (type*)name##BUF.getPtr();                                  \
  } else {                                                             \
    name = (type*)dALLOCA16((n));                                      \
    dIASSERT(name);                                                    \
  }
#endif

#define TRIXY_ALLOCA(name, type, n) TRIXY_ALLOCA_THRESHOLD(name, type, n, 12000)

#if VALUE_TESTING
extern FILE *f;
extern bool testLogging;
void odeTestEnableLogging();
void odeTestDisableLogging();

#define PRINT_DBL_HEX(x) {int *poo = (int*)&(x); fprintf(f,"0x%X%X\n",poo[0],poo[1]);}
#define PRINT_DBL_HEX_STDOUT(x) {int *poo = (int*)&(x); printf("0x%X%X\n",poo[0],poo[1]);}
void printBody(dxBody* b, int index);
void printJoint(dxJoint* j, int index);
#endif

//////////////////////////////////////////////

#endif
