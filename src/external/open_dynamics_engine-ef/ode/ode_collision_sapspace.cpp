/*************************************************************************
 *                                                                       *
 * Open Dynamics Engine, Copyright (C) 2001-2003 Russell L. Smith.       *
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

/*
 *  Sweep and Prune adaptation/tweaks for ODE by Aras Pranckevicius.
 *  Original code:
 *		OPCODE - Optimized Collision Detection
 *		Copyright (C) 2001 Pierre Terdiman
 *		Homepage: http://www.codercorner.com/Opcode.htm
 *
 *	This version does complete radix sort, not "classical" SAP. So, we
 *	have no temporal coherence, but are able to handle any movement
 *	velocities equally well.
 */

 // Silence warnings about shortening 64 vit values into 32 bit containers
#if __clang__
#pragma clang diagnostic ignored "-Wshorten-64-to-32"
#endif
#ifdef _MSC_VER
#pragma warning( disable: 4267)
#endif

#include "ode/ode_common.h"
#include "ode/ode_matrix.h"
#include "ode/ode_collision_space.h"
#include "ode/ode_collision.h"
#include "ode/ode_collision_kernel.h"

#include "ode/ode_collision_space_internal.h"

#include "ode/ode_Opcode.h"


// --------------------------------------------------------------------------
//  Box pruning code
// --------------------------------------------------------------------------

// InsertionSort has better coherence, RadixSort is better for one-shot queries.
#define PRUNING_SORTER	RadixSort
//#define PRUNING_SORTER	InsertionSort

// Global pruning sorter for coherence
static PRUNING_SORTER* gCompletePruningSorter = 0;

static inline PRUNING_SORTER* get_pruning_sorter()
{
	if( !gCompletePruningSorter )
		gCompletePruningSorter = new PRUNING_SORTER;
	return gCompletePruningSorter;
}
// TBD: who should call this?
void release_pruning_sorters()
{
	if( gCompletePruningSorter ) {
		delete gCompletePruningSorter;
		gCompletePruningSorter = 0;
	}
}

/**
 *	Complete box pruning.
 *  Returns a list of overlapping pairs of boxes, each box of the pair
 *  belongs to the same set.
 *  NOTE: code uses floats instead of dReals because Opcode's radix sort
 *  is optimized for floats :)
 *
 *	@param	count	[in] number of boxes.
 *	@param	geoms	[in] geoms of boxes.
 *	@param	pairs	[out] array of overlapping pairs.
 *	@param	axes	[in] projection order (0,2,1 is often best).
 *	@return	true	If success.
 */
static bool complete_box_pruning( int count, const dxGeom** geoms, Pairs& pairs, const Axes& axes )
{
	// Checks
	if (!count || !geoms)
		return false;

	// Catch axes
	udword Axis0 = axes.mAxis0;
	udword Axis1 = axes.mAxis1;
	udword Axis2 = axes.mAxis2;

	// Axis indices into geom's aabb are: min=idx, max=idx+1
	udword ax0idx = Axis0*2;
	udword ax1idx = Axis1*2;
	udword ax2idx = Axis2*2;

	// Allocate some temporary data
	// TBD: persistent allocation between queries?
	float* PosList = new float[count+1];

	// 1) Build main list using the primary axis
	for( int i = 0; i < count; ++i )
		PosList[i] = (float)geoms[i]->aabb[ax0idx];
	PosList[count++] = MAX_FLOAT;

	// 2) Sort the list
	PRUNING_SORTER* RS = get_pruning_sorter();
	const udword* Sorted = RS->Sort(PosList, count).GetRanks();

	// 3) Prune the list
	const udword* const LastSorted = &Sorted[count];
	const udword* RunningAddress = Sorted;
	udword Index0, Index1;
	while( RunningAddress < LastSorted && Sorted < LastSorted ) {
		Index0 = *Sorted++;

		while( PosList[*RunningAddress++] < PosList[Index0] ) {
			// empty, the loop just advances RunningAddress
		}

		if( RunningAddress < LastSorted ) {
			const udword* RunningAddress2 = RunningAddress;

			float idx0ax0max = (float)geoms[Index0]->aabb[ax0idx+1];
			float idx0ax1max = (float)geoms[Index0]->aabb[ax1idx+1];
			float idx0ax2max = (float)geoms[Index0]->aabb[ax2idx+1];
			while( PosList[Index1 = *RunningAddress2++] <= idx0ax0max ) {
//				if(Index0!=Index1)
//				{
					const dReal* aabb0 = geoms[Index0]->aabb;
					const dReal* aabb1 = geoms[Index1]->aabb;
					if( idx0ax1max < (float)aabb1[ax1idx] || (float)aabb1[ax1idx+1] < (float)aabb0[ax1idx] ) {
						// no intersection
					} else {
						if( idx0ax2max < (float)aabb1[ax2idx] || (float)aabb1[ax2idx+1] < (float)aabb0[ax2idx] ) {
							// no intersection
						} else {
							// yes! :)
							pairs.AddPair( Index0, Index1 );
						}
					}
//				}
			}
		}
	}
	DELETEARRAY(PosList);
	return true;
}


// --------------------------------------------------------------------------
//  SAP space code
// --------------------------------------------------------------------------

#define GEOM_ENABLED(g) ((g)->gflags & GEOM_ENABLED)

/*
 *  A bit of repetitive work - similar to collideAABBs, but doesn't check
 *  if AABBs intersect (because SAP returns pairs with overlapping AABBs).
 */
static void collideGeomsNoAABBs( dxGeom *g1, dxGeom *g2, void *data, dNearCallback *callback )
{
	dIASSERT( (g1->gflags & GEOM_AABB_BAD)==0 );
	dIASSERT( (g2->gflags & GEOM_AABB_BAD)==0 );

	// no contacts if both geoms on the same body, and the body is not 0
	if (g1->body == g2->body && g1->body) return;

	// test if the category and collide bitfields match
	if ( ((g1->category_bits & g2->collide_bits) ||
		(g2->category_bits & g1->collide_bits)) == 0) {
		return;
	}

	dReal *bounds1 = g1->aabb;
	dReal *bounds2 = g2->aabb;

	// check if either object is able to prove that it doesn't intersect the
	// AABB of the other
	if (g1->AABBTest (g2,bounds2) == 0) return;
	if (g2->AABBTest (g1,bounds1) == 0) return;

	// the objects might actually intersect - call the space callback function
	callback (data,g1,g2);
};


// --------------------------------------------------------------------------
//  SAP space

// Kind of HACK:
// We abuse 'next' and 'tome' members of dxGeom to store indices
// into dirty/geom lists.
#define GEOM_SET_DIRTY_IDX(g,idx) { g->next = (dxGeom*)(size_t)(idx); }
#define GEOM_SET_GEOM_IDX(g,idx) { g->tome = (dxGeom**)(size_t)(idx); }
#define GEOM_GET_DIRTY_IDX(g) ((size_t)g->next)
#define GEOM_GET_GEOM_IDX(g) ((size_t)g->tome)
#define GEOM_INVALID_IDX (-1)


struct dxSAPSpace : public dxSpace {
	typedef dArray<dxGeom*> TGeomPtrArray;

	// We have two lists (arrays of pointers) to dirty and clean
	// geoms. Each geom knows it's index into the corresponding list
	// (see macros above).
	TGeomPtrArray	DirtyList;	// dirty geoms
	TGeomPtrArray	GeomList;	// clean geoms

	// For SAP, we ultimately separate "normal" geoms and the ones that have
	// infinite AABBs. No point doing SAP on infinite ones (and it doesn't handle
	// infinite geoms anyway).
	TGeomPtrArray	TmpGeomList;	// temporary for normal geoms
	TGeomPtrArray	TmpInfGeomList;	// temporary for geoms with infinite AABBs

	// Our sorting axes.
	Axes			SortAxes;


	dxSAPSpace( dSpaceID _space, AxisOrder sortAxes );
	virtual ~dxSAPSpace();

	// dxSpace
	virtual dxGeom* getGeom(int i);
	virtual void add(dxGeom* g);
	virtual void remove(dxGeom* g);
	virtual void dirty(dxGeom* g);
	virtual void computeAABB();
	virtual void cleanGeoms();
	virtual void collide (void *data, dNearCallback *callback);
	// TBD: not implemented yet
	virtual void collide2 (void *data, dxGeom *geom, dNearCallback *callback);
};



dxSAPSpace::dxSAPSpace( dSpaceID _space, AxisOrder sortAxes )
:	dxSpace( _space ),
	SortAxes( sortAxes )
{
	type = dSweepAndPruneSpaceClass;

	// Init AABB to infinity
	aabb[0] = -dInfinity;
	aabb[1] = dInfinity;
	aabb[2] = -dInfinity;
	aabb[3] = dInfinity;
	aabb[4] = -dInfinity;
	aabb[5] = dInfinity;
}

dxSAPSpace::~dxSAPSpace()
{
}

dxGeom* dxSAPSpace::getGeom( int i )
{
	dUASSERT( i >= 0 && i < count, "index out of range" );
	int dirtySize = DirtyList.size();
	if( i < dirtySize )
		return DirtyList[i];
	else
		return GeomList[i-dirtySize];
}

void dxSAPSpace::add( dxGeom* g )
{
	CHECK_NOT_LOCKED (this);
	dAASSERT(g);
	dUASSERT(g->parent_space == 0 && g->next == 0, "geom is already in a space");

	g->gflags |= GEOM_DIRTY | GEOM_AABB_BAD;

	// add to dirty list
	GEOM_SET_DIRTY_IDX( g, DirtyList.size() );
	GEOM_SET_GEOM_IDX( g, GEOM_INVALID_IDX );
	DirtyList.push( g );

	g->parent_space = this;
	this->count++;

	dGeomMoved(this);
}


void dxSAPSpace::remove( dxGeom* g )
{
	CHECK_NOT_LOCKED(this);
	dAASSERT(g);
	dUASSERT(g->parent_space == this,"object is not in this space");

	// remove
	int dirtyIdx = GEOM_GET_DIRTY_IDX(g);
	int geomIdx = GEOM_GET_GEOM_IDX(g);
	// must be in one list, not in both
	dUASSERT(
		dirtyIdx==GEOM_INVALID_IDX && geomIdx>=0 && geomIdx<GeomList.size() ||
		geomIdx==GEOM_INVALID_IDX && dirtyIdx>=0 && dirtyIdx<DirtyList.size(),
		"geom indices messed up" );
	if( dirtyIdx != GEOM_INVALID_IDX ) {
		// we're in dirty list, remove
		int dirtySize = DirtyList.size();
		dxGeom* lastG = DirtyList[dirtySize-1];
		DirtyList[dirtyIdx] = lastG;
		GEOM_SET_DIRTY_IDX(lastG,dirtyIdx);
		GEOM_SET_DIRTY_IDX(g,GEOM_INVALID_IDX);
		DirtyList.setSize( dirtySize-1 );
	} else {
		// we're in geom list, remove
		int geomSize = GeomList.size();
		dxGeom* lastG = GeomList[geomSize-1];
		GeomList[geomIdx] = lastG;
		GEOM_SET_GEOM_IDX(lastG,geomIdx);
		GEOM_SET_GEOM_IDX(g,GEOM_INVALID_IDX);
		GeomList.setSize( geomSize-1 );
	}
	count--;

	// safeguard
	g->parent_space = 0;

	// the bounding box of this space (and that of all the parents) may have
	// changed as a consequence of the removal.
	dGeomMoved(this);
}

void dxSAPSpace::dirty( dxGeom* g )
{
	dAASSERT(g);
	dUASSERT(g->parent_space == this,"object is not in this space");

	// check if already dirtied
	int dirtyIdx = GEOM_GET_DIRTY_IDX(g);
	if( dirtyIdx != GEOM_INVALID_IDX )
		return;

	int geomIdx = GEOM_GET_GEOM_IDX(g);
	dUASSERT( geomIdx>=0 && geomIdx<GeomList.size(), "geom indices messed up" );

	// remove from geom list, place last in place of this
	int geomSize = GeomList.size();
	dxGeom* lastG = GeomList[geomSize-1];
	GeomList[geomIdx] = lastG;
	GEOM_SET_GEOM_IDX(lastG,geomIdx);
	GeomList.setSize( geomSize-1 );

	// add to dirty list
	GEOM_SET_GEOM_IDX( g, GEOM_INVALID_IDX );
	GEOM_SET_DIRTY_IDX( g, DirtyList.size() );
	DirtyList.push( g );
}

void dxSAPSpace::computeAABB()
{
	// TBD?
}

void dxSAPSpace::cleanGeoms()
{
	int dirtySize = DirtyList.size();
	if( !dirtySize )
		return;

	// compute the AABBs of all dirty geoms, clear the dirty flags,
	// remove from dirty list, place into geom list
	lock_count++;

	int geomSize = GeomList.size();
	GeomList.setSize( geomSize + dirtySize ); // ensure space in geom list

	for( int i = 0; i < dirtySize; ++i ) {
		dxGeom* g = DirtyList[i];
		if( IS_SPACE(g) ) {
			((dxSpace*)g)->cleanGeoms();
		}
		g->recomputeAABB();
		g->gflags &= (~(GEOM_DIRTY|GEOM_AABB_BAD));
		// remove from dirty list, add to geom list
		GEOM_SET_DIRTY_IDX( g, GEOM_INVALID_IDX );
		GEOM_SET_GEOM_IDX( g, geomSize + i );
		GeomList[geomSize+i] = g;
	}
	// clear dirty list
	DirtyList.setSize( 0 );

	lock_count--;
}


void dxSAPSpace::collide (void *data, dNearCallback *callback)
{
	dAASSERT (callback);

	lock_count++;

	cleanGeoms();

	// by now all geoms are in GeomList, and DirtyList must be empty
	int geomSize = GeomList.size();
	dUASSERT( geomSize == count, "geom counts messed up" );

	// separate all geoms into infinite AABBs and normal AABBs
	TmpGeomList.setSize(0);
	TmpInfGeomList.setSize(0);
	int axis0max = SortAxes.mAxis0*2+1;
	for( int i = 0; i < geomSize; ++i ) {
		dxGeom* g =GeomList[i];
		if( !GEOM_ENABLED(g) ) // skip disabled ones
			continue;
		const dReal& amax = g->aabb[axis0max];
		if( amax == dInfinity ) // HACK? probably not...
			TmpInfGeomList.push( g );
		else
			TmpGeomList.push( g );
	}

	// do SAP on normal AABBs
	Pairs overlapBoxes;
	//bool isok = complete_box_pruning( TmpGeomList.size(), (const dxGeom**)TmpGeomList.data(), overlapBoxes, SortAxes );
	complete_box_pruning( TmpGeomList.size(), (const dxGeom**)TmpGeomList.data(), overlapBoxes, SortAxes );

	// collide overlapping
	udword overlapCount = overlapBoxes.GetNbPairs();
	for( udword j = 0; j < overlapCount; ++j ) {
		const Pair* pair = overlapBoxes.GetPair(j);
		dxGeom* g1 = TmpGeomList[pair->id0];
		dxGeom* g2 = TmpGeomList[pair->id1];
		collideGeomsNoAABBs( g1, g2, data, callback );
	}

	int infSize = TmpInfGeomList.size();
	int normSize = TmpGeomList.size();
	int m, n;
	for( m = 0; m < infSize; ++m ) {
		dxGeom* g1 = TmpInfGeomList[m];
		// collide infinite ones
		for( n = m+1; n < infSize; ++n ) {
			dxGeom* g2 = TmpInfGeomList[n];
			collideGeomsNoAABBs( g1, g2, data, callback );
		}
		// collide infinite ones with normal ones
		for( n = 0; n < normSize; ++n ) {
			dxGeom* g2 = TmpGeomList[n];
			collideGeomsNoAABBs( g1, g2, data, callback );
		}
	}

	lock_count--;
}


void dxSAPSpace::collide2( void *data, dxGeom *geom, dNearCallback *callback )
{
	// TBD
	/*
	dAASSERT (geom && callback);

	lock_count++;
	cleanGeoms();
	geom->recomputeAABB();

	// intersect bounding boxes
	for (dxGeom *g=first; g; g=g->next) {
		if (GEOM_ENABLED(g)){
			collideAABBs (g,geom,data,callback);
		}
	}

	lock_count--;
	*/
}

dSpaceID dSweepAndPruneSpaceCreate(dxSpace* space,int sortAxes) {
	return new dxSAPSpace( space, (AxisOrder)sortAxes );
}
