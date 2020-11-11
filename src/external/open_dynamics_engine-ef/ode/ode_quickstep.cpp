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

#include "ode/ode_objects_private.h"
#include "ode/ode_joint.h"
#include "ode/ode_config.h"
#include "ode/ode_math.h"
#include "ode/ode_rotation.h"
#include "ode/ode_timer.h"
#include "ode/ode_error.h"
#include "ode/ode_matrix.h"
#include "ode/ode_misc.h"
#include "ode/ode_lcp.h"
#include "ode/ode_util.h"
#include "ode/ode_misc.h"

#define ALLOCA dALLOCA16

typedef const dReal *dRealPtr;
typedef dReal *dRealMutablePtr;
#define dRealArray(name,n) dReal name[n];

// ericf addition - a simple memory buffer
class _Buffer{
public:
    _Buffer():_ptr(NULL),_allocated(false){
    }
    void allocate(unsigned long size){
        if (_allocated && _ptr) free(_ptr);
        //dIASSERT(size > 0);
        _ptr = malloc(size);
        dIASSERT(_ptr);
        _allocated = true;
    }
    ~_Buffer(){
        if (_allocated && _ptr) free(_ptr);
        _ptr = NULL;
    }
    void* getPtr() const {return _ptr;}
private:
    void* _ptr;
    bool _allocated;
};


// ...ericf update - we can shave a bit of time off by using our own bare-bones buffer class...
#define TRIXY_ALLOCA(name,type,n) _Buffer name ## BUF; if (n > 6000){name ## BUF.allocate((n)); name = (type*)name ## BUF.getPtr();} else {name = (type*)ALLOCA((n)); dIASSERT(name);}

#define dRealAllocaArray(name,n) dReal *name; TRIXY_ALLOCA(name,dReal,n*sizeof(dReal))
//#define dRealAllocaArray(name,n) dReal *name = (dReal*) ALLOCA ((n)*sizeof(dReal));


// whether to use quickstep feedback patch submitted to the ode mailing
// list by Jaroslav Sinecky in June '05
#define JUNE_05_PATCH 1

//***************************************************************************
// configuration

// for the SOR and CG methods:
// uncomment the following line to use warm starting. this definitely
// help for motor-driven joints. unfortunately it appears to hurt
// with high-friction contacts using the SOR method. use with care

#define WARM_STARTING 0


// for the SOR method:
// uncomment the following line to determine a new constraint-solving
// order for each iteration. however, the qsort per iteration is expensive,
// and the optimal order is somewhat problem dependent. 
// @@@ try the leaf->root ordering.

//#define REORDER_CONSTRAINTS 1


// for the SOR method:
// uncomment the following line to randomly reorder constraint rows
// during the solution. depending on the situation, this can help a lot
// or hardly at all, but it doesn't seem to hurt.

// ericf note: this was on for original release; trying it off to save processing..
#define RANDOMLY_REORDER_CONSTRAINTS 0

#if JUNE_05_PATCH

//****************************************************************************
// special matrix multipliers

// multiply block of B matrix (q x 6) with 12 dReal per row with C vektor (q)
static void Multiply1_12q1 (dReal *A, dReal *B, dReal *C, int q)
{
	int k;
	dReal sum;
	dIASSERT (q>0 && A && B && C);
	sum = 0;
	for (k=0; k<q; k++) sum += B[k*12] * C[k];
	A[0] = sum;
	sum = 0;
	for (k=0; k<q; k++) sum += B[1+k*12] * C[k];
	A[1] = sum;
	sum = 0;
	for (k=0; k<q; k++) sum += B[2+k*12] * C[k];
	A[2] = sum;
	sum = 0;
	for (k=0; k<q; k++) sum += B[3+k*12] * C[k];
	A[3] = sum;
	sum = 0;
	for (k=0; k<q; k++) sum += B[4+k*12] * C[k];
	A[4] = sum;
	sum = 0;
	for (k=0; k<q; k++) sum += B[5+k*12] * C[k];
	A[5] = sum;
}
#endif


//***************************************************************************
// testing stuff

#ifdef TIMING
#define IFTIMING(x) x
#else
#define IFTIMING(x) /* */
#endif

//***************************************************************************
// various common computations involving the matrix J

// compute iMJ = inv(M)*J'

static void compute_invM_JT (int m, dRealMutablePtr J, dRealMutablePtr iMJ, int *jb,
	dxBody * const *body, dRealPtr invI)
{
	int i,j;
	dRealMutablePtr iMJ_ptr = iMJ;
	dRealMutablePtr J_ptr = J;
	for (i=0; i<m; i++) {
		int b1 = jb[i*2];	
		int b2 = jb[i*2+1];
		dReal k = body[b1]->invMass;
		for (j=0; j<3; j++) iMJ_ptr[j] = k*J_ptr[j];
		dMULTIPLY0_331 (iMJ_ptr + 3, invI + 12*b1, J_ptr + 3);
		if (b2 >= 0) {
			k = body[b2]->invMass;
			for (j=0; j<3; j++) iMJ_ptr[j+6] = k*J_ptr[j+6];
			dMULTIPLY0_331 (iMJ_ptr + 9, invI + 12*b2, J_ptr + 9);
		}
		J_ptr += 12;
		iMJ_ptr += 12;
	}
}


// compute out = inv(M)*J'*in.

static void multiply_invM_JT (int m, int nb, dRealMutablePtr iMJ, int *jb,
	dRealMutablePtr in, dRealMutablePtr out)
{
	int i,j;
	dSetZero (out,6*nb);
	dRealPtr iMJ_ptr = iMJ;
	for (i=0; i<m; i++) {
		int b1 = jb[i*2];	
		int b2 = jb[i*2+1];
		dRealMutablePtr out_ptr = out + b1*6;
		for (j=0; j<6; j++) out_ptr[j] += iMJ_ptr[j] * in[i];
		iMJ_ptr += 6;
		if (b2 >= 0) {
			out_ptr = out + b2*6;
			for (j=0; j<6; j++) out_ptr[j] += iMJ_ptr[j] * in[i];
		}
		iMJ_ptr += 6;
	}
}


// compute out = J*in.

static void multiply_J (int m, dRealMutablePtr J, int *jb,
	dRealMutablePtr in, dRealMutablePtr out)
{
	int i,j;
	dRealPtr J_ptr = J;
	for (i=0; i<m; i++) {
		int b1 = jb[i*2];	
		int b2 = jb[i*2+1];
		dReal sum = 0;
		dRealMutablePtr in_ptr = in + b1*6;
		for (j=0; j<6; j++) sum += J_ptr[j] * in_ptr[j];				
		J_ptr += 6;
		if (b2 >= 0) {
			in_ptr = in + b2*6;
			for (j=0; j<6; j++) sum += J_ptr[j] * in_ptr[j];				
		}
		J_ptr += 6;
		out[i] = sum;
	}
}


// compute out = (J*inv(M)*J' + cfm)*in.
// use z as an nb*6 temporary.

#if 0
static void multiply_J_invM_JT (int m, int nb, dRealMutablePtr J, dRealMutablePtr iMJ, int *jb,
	dRealPtr cfm, dRealMutablePtr z, dRealMutablePtr in, dRealMutablePtr out)
{
	multiply_invM_JT (m,nb,iMJ,jb,in,z);
	multiply_J (m,J,jb,z,out);

	// add cfm
	for (int i=0; i<m; i++) out[i] += cfm[i] * in[i];
}
#endif

//***************************************************************************
// conjugate gradient method with jacobi preconditioner
// THIS IS EXPERIMENTAL CODE that doesn't work too well, so it is ifdefed out.
//
// adding CFM seems to be critically important to this method.

#if 0

static inline dReal dot (int n, dRealPtr x, dRealPtr y)
{
	dReal sum=0;
	for (int i=0; i<n; i++) sum += x[i]*y[i];
	return sum;
}


// x = y + z*alpha

static inline void add (int n, dRealMutablePtr x, dRealPtr y, dRealPtr z, dReal alpha)
{
	for (int i=0; i<n; i++) x[i] = y[i] + z[i]*alpha;
}


static void CG_LCP (int m, int nb, dRealMutablePtr J, int *jb, dxBody * const *body,
	dRealPtr invI, dRealMutablePtr lambda, dRealMutablePtr fc, dRealMutablePtr b,
	dRealMutablePtr lo, dRealMutablePtr hi, dRealPtr cfm, int *findex,
	dxQuickStepParameters *qs)
{
	int i,j;
	const int num_iterations = qs->num_iterations;

	// precompute iMJ = inv(M)*J'
	dRealAllocaArray (iMJ,m*12);
	compute_invM_JT (m,J,iMJ,jb,body,invI);

	dReal last_rho = 0;
	dRealAllocaArray (r,m);
	dRealAllocaArray (z,m);
	dRealAllocaArray (p,m);
	dRealAllocaArray (q,m);

	// precompute 1 / diagonals of A
	dRealAllocaArray (Ad,m);
	dRealPtr iMJ_ptr = iMJ;
	dRealPtr J_ptr = J;
	for (i=0; i<m; i++) {
		dReal sum = 0;
		for (j=0; j<6; j++) sum += iMJ_ptr[j] * J_ptr[j];
		if (jb[i*2+1] >= 0) {
			for (j=6; j<12; j++) sum += iMJ_ptr[j] * J_ptr[j];
		}
		iMJ_ptr += 12;
		J_ptr += 12;
		Ad[i] = REAL(1.0) / (sum + cfm[i]);
	}

#ifdef WARM_STARTING
	// compute residual r = b - A*lambda
	multiply_J_invM_JT (m,nb,J,iMJ,jb,cfm,fc,lambda,r);
	for (i=0; i<m; i++) r[i] = b[i] - r[i];
#else
	dSetZero (lambda,m);
	memcpy (r,b,m*sizeof(dReal));		// residual r = b - A*lambda
#endif
	
	for (int iteration=0; iteration < num_iterations; iteration++) {
		for (i=0; i<m; i++) z[i] = r[i]*Ad[i];	// z = inv(M)*r
		dReal rho = dot (m,r,z);		// rho = r'*z
		
		// @@@
		// we must check for convergence, otherwise rho will go to 0 if
		// we get an exact solution, which will introduce NaNs into the equations.
		if (rho < 1e-10) {
			printf ("CG returned at iteration %d\n",iteration);
			break;
		}
		
		if (iteration==0) {
			memcpy (p,z,m*sizeof(dReal));	// p = z
		}
		else {
			add (m,p,z,p,rho/last_rho);	// p = z + (rho/last_rho)*p
		}
		
		// compute q = (J*inv(M)*J')*p
		multiply_J_invM_JT (m,nb,J,iMJ,jb,cfm,fc,p,q);
	
		dReal alpha = rho/dot (m,p,q);		// alpha = rho/(p'*q)
		add (m,lambda,lambda,p,alpha);		// lambda = lambda + alpha*p
		add (m,r,r,q,-alpha);			// r = r - alpha*q
		last_rho = rho;
	}

	// compute fc = inv(M)*J'*lambda
	multiply_invM_JT (m,nb,iMJ,jb,lambda,fc);

#if 0
	// measure solution error
	multiply_J_invM_JT (m,nb,J,iMJ,jb,cfm,fc,lambda,r);
	dReal error = 0;
	for (i=0; i<m; i++) error += dFabs(r[i] - b[i]);
	printf ("lambda error = %10.6e\n",error);
#endif
}

#endif

//***************************************************************************
// SOR-LCP method

// nb is the number of bodies in the body array.
// J is an m*12 matrix of constraint rows
// jb is an array of first and second body numbers for each constraint row
// invI is the global frame inverse inertia for each body (stacked 3x3 matrices)
//
// this returns lambda and fc (the constraint force).
// note: fc is returned as inv(M)*J'*lambda, the constraint force is actually J'*lambda
//
// b, lo and hi are modified on exit


struct IndexError {
	dReal error;		// error to sort on
	int findex;
	int index;		// row index
};


#ifdef REORDER_CONSTRAINTS

static int compare_index_error (const void *a, const void *b)
{
	const IndexError *i1 = (IndexError*) a;
	const IndexError *i2 = (IndexError*) b;
	if (i1->findex < 0 && i2->findex >= 0) return -1;
	if (i1->findex >= 0 && i2->findex < 0) return 1;
	if (i1->error < i2->error) return -1;
	if (i1->error > i2->error) return 1;
	return 0;
}

#endif


static void SOR_LCP (int m, int nb, dRealMutablePtr J, int *jb, dxBody * const *body,
	dRealPtr invI, dRealMutablePtr lambda, dRealMutablePtr fc, dRealMutablePtr b,
	dRealMutablePtr lo, dRealMutablePtr hi, dRealPtr cfm, int *findex,
	dxQuickStepParameters *qs)
{
	const int num_iterations = qs->num_iterations;
	const dReal sor_w = qs->w;		// SOR over-relaxation parameter

	int i,j;

#ifdef WARM_STARTING
	// for warm starting, this seems to be necessary to prevent
	// jerkiness in motor-driven joints. i have no idea why this works.
	for (i=0; i<m; i++) lambda[i] *= (dReal) 0.9;
#else
	dSetZero (lambda,m);
#endif

	// the lambda computed at the previous iteration.
	// this is used to measure error for when we are reordering the indexes.
	dRealAllocaArray (last_lambda,m);

	// a copy of the 'hi' vector in case findex[] is being used
	dRealAllocaArray (hicopy,m);
	memcpy (hicopy,hi,m*sizeof(dReal));

	// precompute iMJ = inv(M)*J'
	dRealAllocaArray (iMJ,m*12);
	compute_invM_JT (m,J,iMJ,jb,body,invI);

	// compute fc=(inv(M)*J')*lambda. we will incrementally maintain fc
	// as we change lambda.
#ifdef WARM_STARTING
	multiply_invM_JT (m,nb,iMJ,jb,lambda,fc);
#else
	dSetZero (fc,nb*6);
#endif

	// precompute 1 / diagonals of A
	dRealAllocaArray (Ad,m);
	dRealPtr iMJ_ptr = iMJ;
	dRealMutablePtr J_ptr = J;
	for (i=0; i<m; i++) {

		dReal sum = 0;
		for (j=0; j<6; j++) sum += iMJ_ptr[j] * J_ptr[j];
		if (jb[i*2+1] >= 0) {
			for (j=6; j<12; j++) sum += iMJ_ptr[j] * J_ptr[j];
		}
		iMJ_ptr += 12;
		J_ptr += 12;
		Ad[i] = sor_w / (sum + cfm[i]);
	}

	// scale J and b by Ad
	J_ptr = J;
	for (i=0; i<m; i++) {
		for (j=0; j<12; j++) {
			J_ptr[0] *= Ad[i];
			J_ptr++;
		}

		b[i] *= Ad[i];
	}

	// scale Ad by CFM
	for (i=0; i<m; i++) Ad[i] *= cfm[i];

	// order to solve constraint rows in
	IndexError *order = (IndexError*) alloca (m*sizeof(IndexError));

#ifndef REORDER_CONSTRAINTS
	// make sure constraints with findex < 0 come first.
	j=0;
	for (i=0; i<m; i++) if (findex[i] < 0) order[j++].index = i;
	for (i=0; i<m; i++) if (findex[i] >= 0) order[j++].index = i;
	dIASSERT (j==m);
#endif

	for (int iteration=0; iteration < num_iterations; iteration++) {

#ifdef REORDER_CONSTRAINTS
		// constraints with findex < 0 always come first.
		if (iteration < 2) {
			// for the first two iterations, solve the constraints in
			// the given order
			for (i=0; i<m; i++) {
				order[i].error = i;
				order[i].findex = findex[i];
				order[i].index = i;
			}
		}
		else {
			// sort the constraints so that the ones converging slowest
			// get solved last. use the absolute (not relative) error.
			for (i=0; i<m; i++) {
				dReal v1 = dFabs (lambda[i]);
				dReal v2 = dFabs (last_lambda[i]);
				dReal max = (v1 > v2) ? v1 : v2;
				if (max > 0) {
					//@@@ relative error: order[i].error = dFabs(lambda[i]-last_lambda[i])/max;
					order[i].error = dFabs(lambda[i]-last_lambda[i]);
				}
				else {
					order[i].error = dInfinity;
				}
				order[i].findex = findex[i];
				order[i].index = i;
			}
		}
		qsort (order,m,sizeof(IndexError),&compare_index_error);
#endif

//ericf: we save and restore the random seed here so each island is not affected by the
//existance of other islands
#ifdef RANDOMLY_REORDER_CONSTRAINTS
		unsigned long oldSeed = dRandGetSeed();
		if ((iteration & 7) == 0) {
			for (i=1; i<m; ++i) {
				IndexError tmp = order[i];
				int swapi = dRandInt(i+1);
				order[i] = order[swapi];
				order[swapi] = tmp;
			}
		}
		dRandSetSeed(oldSeed);
#endif

		//@@@ potential optimization: swap lambda and last_lambda pointers rather
		//    than copying the data. we must make sure lambda is properly
		//    returned to the caller
		memcpy (last_lambda,lambda,m*sizeof(dReal));

		for (int i=0; i<m; i++) {
			// @@@ potential optimization: we could pre-sort J and iMJ, thereby
			//     linearizing access to those arrays. hmmm, this does not seem
			//     like a win, but we should think carefully about our memory
			//     access pattern.
		
			int index = order[i].index;
			J_ptr = J + index*12;
			iMJ_ptr = iMJ + index*12;
		
			// set the limits for this constraint. note that 'hicopy' is used.
			// this is the place where the QuickStep method differs from the
			// direct LCP solving method, since that method only performs this
			// limit adjustment once per time step, whereas this method performs
			// once per iteration per constraint row.
			// the constraints are ordered so that all lambda[] values needed have
			// already been computed.
			if (findex[index] >= 0) {
				hi[index] = dFabs (hicopy[index] * lambda[findex[index]]);
				lo[index] = -hi[index];
			}

			int b1 = jb[index*2];
			int b2 = jb[index*2+1];
			dReal delta = b[index] - lambda[index]*Ad[index];
			dRealMutablePtr fc_ptr = fc + 6*b1;

			//DIFF HERE

			// @@@ potential optimization: SIMD-ize this and the b2 >= 0 case
			delta -=fc_ptr[0] * J_ptr[0] + fc_ptr[1] * J_ptr[1] +
				fc_ptr[2] * J_ptr[2] + fc_ptr[3] * J_ptr[3] +
				fc_ptr[4] * J_ptr[4] + fc_ptr[5] * J_ptr[5];
			// @@@ potential optimization: handle 1-body constraints in a separate
			//     loop to avoid the cost of test & jump?
			if (b2 >= 0) {
				fc_ptr = fc + 6*b2;
				delta -=fc_ptr[0] * J_ptr[6] + fc_ptr[1] * J_ptr[7] +
					fc_ptr[2] * J_ptr[8] + fc_ptr[3] * J_ptr[9] +
					fc_ptr[4] * J_ptr[10] + fc_ptr[5] * J_ptr[11];
			}

			// compute lambda and clamp it to [lo,hi].
			// @@@ potential optimization: does SSE have clamping instructions
			//     to save test+jump penalties here?
			dReal new_lambda = lambda[index] + delta;
			if (new_lambda < lo[index]) {
				delta = lo[index]-lambda[index];
				lambda[index] = lo[index];
			}
			else if (new_lambda > hi[index]) {
				delta = hi[index]-lambda[index];
				lambda[index] = hi[index];
			}
			else {
				lambda[index] = new_lambda;
			}

			//@@@ a trick that may or may not help
			//dReal ramp = (1-((dReal)(iteration+1)/(dReal)num_iterations));
			//delta *= ramp;


			// update fc.
			// @@@ potential optimization: SIMD for this and the b2 >= 0 case
			fc_ptr = fc + 6*b1;
			fc_ptr[0] += delta * iMJ_ptr[0];
			fc_ptr[1] += delta * iMJ_ptr[1];
			fc_ptr[2] += delta * iMJ_ptr[2];
			fc_ptr[3] += delta * iMJ_ptr[3];
			fc_ptr[4] += delta * iMJ_ptr[4];
			fc_ptr[5] += delta * iMJ_ptr[5];
			// @@@ potential optimization: handle 1-body constraints in a separate
			//     loop to avoid the cost of test & jump?
			if (b2 >= 0) {
				fc_ptr = fc + 6*b2;
				fc_ptr[0] += delta * iMJ_ptr[6];
				fc_ptr[1] += delta * iMJ_ptr[7];
				fc_ptr[2] += delta * iMJ_ptr[8];
				fc_ptr[3] += delta * iMJ_ptr[9];
				fc_ptr[4] += delta * iMJ_ptr[10];
				fc_ptr[5] += delta * iMJ_ptr[11];
			}
		}
	}
}


void dxQuickStepper (dxWorld *world, dxBody * const *body, int nb,
		     dxJoint * const *_joint, int nj, dReal stepsize)
{
	int i,j;
	IFTIMING(dTimerStart("preprocessing");)

	dReal stepsize1 = dRecip(stepsize);

	// number all bodies in the body list - set their tag values
	for (i=0; i<nb; i++) body[i]->tag = i;
	
	// make a local copy of the joint array, because we might want to modify it.
	// (the "dxJoint *const*" declaration says we're allowed to modify the joints
	// but not the joint array, because the caller might need it unchanged).
	//@@@ do we really need to do this? we'll be sorting constraint rows individually, not joints
	dxJoint **joint = (dxJoint**) alloca (nj * sizeof(dxJoint*));
	memcpy (joint,_joint,nj * sizeof(dxJoint*));
	
	// for all bodies, compute the inertia tensor and its inverse in the global
	// frame, and compute the rotational force and add it to the torque
	// accumulator. I and invI are a vertical stack of 3x4 matrices, one per body.
#if !JUNE_05_PATCH
	dRealAllocaArray (I,3*4*nb);	// need to remember all I's for feedback purposes only
#endif
	dRealAllocaArray (invI,3*4*nb);
	for (i=0; i<nb; i++) {
		dMatrix3 tmp;

#if JUNE_05_PATCH
		dMatrix3 I;
#endif


		// compute inertia tensor in global frame
		dMULTIPLY2_333 (tmp,body[i]->mass.I,body[i]->R);
#if !JUNE_05_PATCH
		dMULTIPLY0_333 (I+i*12,body[i]->R,tmp);
#else
		dMULTIPLY0_333 (I,body[i]->R,tmp);
#endif
		// compute inverse inertia tensor in global frame
		dMULTIPLY2_333 (tmp,body[i]->invI,body[i]->R);
		dMULTIPLY0_333 (invI+i*12,body[i]->R,tmp);
		// compute rotational force

        // ERICF TEST
// #ifndef dNODEBUG
//         {
//             dReal testVal = (nb > 0)?dFabs(body[0]->lvel[0]):0.0;
//             if (isnan(testVal) || isinf(testVal) || testVal > 9999.0f){
//                 printf("ARGGGGG3!\n");
//             }
//         }
// #endif


#define SIMPLE_ROTATION 1


#if !SIMPLE_ROTATION

#if !JUNE_05_PATCH
		dMULTIPLY0_331 (tmp,I+i*12,body[i]->avel);
#else
		dMULTIPLY0_331 (tmp,I,body[i]->avel);
#endif
		dCROSS (body[i]->tacc,-=,body[i]->avel,tmp);
#endif // SIMPLE_ROTATION

	}

    // {
    //     dReal testVal = (nb > 0)?dFabs(body[0]->facc[0]):0.0;
    //     if (isnan(testVal) || isinf(testVal) || testVal > 9999.0f){
    //         printf("WHOOOOOAAAAAA!\n");
    //     }
    // }
    
	// add the gravity force to all bodies
	for (i=0; i<nb; i++) {
		if ((body[i]->flags & dxBodyNoGravity)==0) {
			body[i]->facc[0] += body[i]->mass.mass * world->gravity[0];
			body[i]->facc[1] += body[i]->mass.mass * world->gravity[1];
			body[i]->facc[2] += body[i]->mass.mass * world->gravity[2];
		}
        // else{
        //     body[i]->facc[0] = 0;
        //     body[i]->facc[1] = 0;
        //     body[i]->facc[2] = 0;
        //     body[i]->lvel[0] = 0;
        //     body[i]->lvel[1] = 0;
        //     body[i]->lvel[2] = 0;
        //     body[i]->avel[0] = 0;
        //     body[i]->avel[1] = 0;
        //     body[i]->avel[2] = 0;
        // }
	}

	// get joint information (m = total constraint dimension, nub = number of unbounded variables).
	// joints with m=0 are inactive and are removed from the joints array
	// entirely, so that the code that follows does not consider them.
	//@@@ do we really need to save all the info1's
    //printf("SIZE IS %d coutn is %d\n",sizeof(dxJoint::Info1),nj);
	dxJoint::Info1 *info = (dxJoint::Info1*) alloca (nj*sizeof(dxJoint::Info1));
	for (i=0, j=0; j<nj; j++) {	// i=dest, j=src
		joint[j]->vtable->getInfo1 (joint[j],info+i);
		dIASSERT (info[i].m >= 0 && info[i].m <= 6 && info[i].nub >= 0 && info[i].nub <= info[i].m);
		if (info[i].m > 0) {
			joint[i] = joint[j];
			i++;
		}
	}
	nj = i;

	// create the row offset array
	int m = 0;
	int *ofs = (int*) alloca (nj*sizeof(int));
	for (i=0; i<nj; i++) {
		ofs[i] = m;
		m += info[i].m;
	}
    //printf("ROWS %d\n",m);

	// if there are constraints, compute the constraint force
	dRealAllocaArray (J,m*12);
	int *jb = (int*) alloca (m*2*sizeof(int));
	if (m > 0) {
		// create a constraint equation right hand side vector `c', a constraint
		// force mixing vector `cfm', and LCP low and high bound vectors, and an
		// 'findex' vector.
		dRealAllocaArray (c,m);
		dRealAllocaArray (cfm,m);
		dRealAllocaArray (lo,m);
		dRealAllocaArray (hi,m);
		int *findex = (int*) alloca (m*sizeof(int));
		dSetZero (c,m);
		dSetValue (cfm,m,world->global_cfm);
		dSetValue (lo,m,-dInfinity);
		dSetValue (hi,m, dInfinity);
		for (i=0; i<m; i++) findex[i] = -1;

		// get jacobian data from constraints. an m*12 matrix will be created
		// to store the two jacobian blocks from each constraint. it has this
		// format:
		//
		//   l1 l1 l1 a1 a1 a1 l2 l2 l2 a2 a2 a2 \    .
		//   l1 l1 l1 a1 a1 a1 l2 l2 l2 a2 a2 a2  }-- jacobian for joint 0, body 1 and body 2 (3 rows)
		//   l1 l1 l1 a1 a1 a1 l2 l2 l2 a2 a2 a2 /
		//   l1 l1 l1 a1 a1 a1 l2 l2 l2 a2 a2 a2 }--- jacobian for joint 1, body 1 and body 2 (3 rows)
		//   etc...
		//
		//   (lll) = linear jacobian data
		//   (aaa) = angular jacobian data
		//
		IFTIMING (dTimerNow ("create J");)
		dSetZero (J,m*12);
		dxJoint::Info2 Jinfo;
		Jinfo.rowskip = 12;
		Jinfo.fps = stepsize1;
		Jinfo.erp = world->global_erp;


		for (i=0; i<nj; i++) {


			Jinfo.J1l = J + ofs[i]*12;
			Jinfo.J1a = Jinfo.J1l + 3;
			Jinfo.J2l = Jinfo.J1l + 6;
			Jinfo.J2a = Jinfo.J1l + 9;
			Jinfo.c = c + ofs[i];
			Jinfo.cfm = cfm + ofs[i];
			Jinfo.lo = lo + ofs[i];
			Jinfo.hi = hi + ofs[i];
			Jinfo.findex = findex + ofs[i];
			joint[i]->vtable->getInfo2 (joint[i],&Jinfo);
			// adjust returned findex values for global index numbering
			for (j=0; j<info[i].m; j++) {
				if (findex[ofs[i] + j] >= 0) findex[ofs[i] + j] += ofs[i];
			}

		}

#if JUNE_05_PATCH
		// we need a copy of Jacobian for joint feedbacks
		// because it gets destroyed by SOR solver
		// instead of saving all Jacobian, we can save just rows
		// for joints, that requested feedback (which is normaly much less)
		int mfb = 0; // number of rows we will have to save
		for (i=0; i<nj; i++) 
			if (joint[i]->feedback)
				mfb += info[i].m;
		dRealAllocaArray (Jcopy,mfb*12); 
		if (mfb > 0) {
			mfb = 0;
			for (i=0; i<nj; i++) 
				if (joint[i]->feedback) {
					memcpy(Jcopy+mfb*12, J+ofs[i]*12, info[i].m*12*sizeof(dReal));
					mfb += info[i].m;
				}
		}


#endif

		// create an array of body numbers for each joint row
		int *jb_ptr = jb;
		for (i=0; i<nj; i++) {
			int b1 = (joint[i]->node[0].body) ? (joint[i]->node[0].body->tag) : -1;
			int b2 = (joint[i]->node[1].body) ? (joint[i]->node[1].body->tag) : -1;
			for (j=0; j<info[i].m; j++) {
				jb_ptr[0] = b1;
				jb_ptr[1] = b2;
				jb_ptr += 2;
			}
		}
		dIASSERT (jb_ptr == jb+2*m);

		// compute the right hand side `rhs'
		IFTIMING (dTimerNow ("compute rhs");)
		dRealAllocaArray (tmp1,nb*6);
		// put v/h + invM*fe into tmp1
		for (i=0; i<nb; i++) {
			dReal body_invMass = body[i]->invMass;
			for (j=0; j<3; j++) tmp1[i*6+j] = body[i]->facc[j] * body_invMass + body[i]->lvel[j] * stepsize1;
			dMULTIPLY0_331 (tmp1 + i*6 + 3,invI + i*12,body[i]->tacc);
			for (j=0; j<3; j++) tmp1[i*6+3+j] += body[i]->avel[j] * stepsize1;

		}

		// put J*tmp1 into rhs
		dRealAllocaArray (rhs,m);
		multiply_J (m,J,jb,tmp1,rhs);

		// complete rhs
		for (i=0; i<m; i++){
			rhs[i] = c[i]*stepsize1 - rhs[i];
		}

		// scale CFM
		for (i=0; i<m; i++){
			cfm[i] *= stepsize1;
		}

		// load lambda from the value saved on the previous iteration
		dRealAllocaArray (lambda,m);
#ifdef WARM_STARTING
		dSetZero (lambda,m);	//@@@ shouldn't be necessary
		for (i=0; i<nj; i++) {
			memcpy (lambda+ofs[i],joint[i]->lambda,info[i].m * sizeof(dReal));
		}
#endif


		//check the stuff going into SOR_LCP

		// solve the LCP problem and get lambda and invM*constraint_force
		IFTIMING (dTimerNow ("solving LCP problem");)
		dRealAllocaArray (cforce,nb*6);
		SOR_LCP (m,nb,J,jb,body,invI,lambda,cforce,rhs,lo,hi,cfm,findex,&world->qs);

        // ERICF TEST
        {
//             dReal testVal = (nb > 0)?dFabs(cforce[0]):0.0;
//             if (isnan(testVal) || isinf(testVal) || testVal > 9999.0f){
//                 printf("ARGGGGG1!\n");
//                 for (i=0; i<nj; i++) {
//                     printf("%f ",joint[i]->lambda[0]);
//                 }
//                 printf("dn\n");

//             }
//             else{

// #               ifdef WARM_STARTING
//                 // save lambda for the next iteration
//                 //@@@ note that this doesn't work for contact joints yet, as they are
//                 // recreated every iteration
//                 for (i=0; i<nj; i++) {
//                     memcpy (joint[i]->lambda,lambda+ofs[i],info[i].m * sizeof(dReal));
//                 }
// #               endif

                // note that the SOR method overwrites rhs and J at this point, so
                // they should not be used again.

                // add stepsize * cforce to the body velocity
                for (i=0; i<nb; i++) {
                    for (j=0; j<3; j++){
                        body[i]->lvel[j] += stepsize * cforce[i*6+j];
                    }
                    for (j=0; j<3; j++){
                        body[i]->avel[j] += stepsize * cforce[i*6+3+j];
                    }
                }
            // }

            // ERICF TEST
// #ifndef dNODEBUG
//             {
//                 dReal testVal = (nb > 0)?dFabs(body[0]->lvel[0]):0.0;
//                 if (isnan(testVal) || isinf(testVal) || testVal > 9999.0f){
//                     printf("ARGGGGGffff1! %f\n",cforce[0]);
//                 }
//             }
// #endif



#if !JUNE_05_PATCH
            // if joint feedback is requested, compute the constraint force.
            // BUT: cforce is inv(M)*J'*lambda, whereas we want just J'*lambda,
            // so we must compute M*cforce.
            // @@@ if any joint has a feedback request we compute the entire
            //     adjusted cforce, which is not the most efficient way to do it.
            for (j=0; j<nj; j++) {
                if (joint[j]->feedback) {
                    // compute adjusted cforce
                    for (i=0; i<nb; i++) {
                        dReal k = body[i]->mass.mass;
                        cforce [i*6+0] *= k;
                        cforce [i*6+1] *= k;
                        cforce [i*6+2] *= k;
                        dVector3 tmp;
                        dMULTIPLY0_331 (tmp, I + 12*i, cforce + i*6 + 3);
                        cforce [i*6+3] = tmp[0];
                        cforce [i*6+4] = tmp[1];
                        cforce [i*6+5] = tmp[2];
                    }
                    // compute feedback for this and all remaining joints
                    for (; j<nj; j++) {
                        dJointFeedback *fb = joint[j]->feedback;
                        if (fb) {
                            int b1 = joint[j]->node[0].body->tag;
                            memcpy (fb->f1,cforce+b1*6,3*sizeof(dReal));
                            memcpy (fb->t1,cforce+b1*6+3,3*sizeof(dReal));
                            if (joint[j]->node[1].body) {
                                int b2 = joint[j]->node[1].body->tag;
                                memcpy (fb->f2,cforce+b2*6,3*sizeof(dReal));
                                memcpy (fb->t2,cforce+b2*6+3,3*sizeof(dReal));
                            }
                        }
                    }
                }
            }
#else
            if (mfb > 0) {
                // straightforward computation of joint contraint forces:
                // multiply related lambdas with respective J' block for joints
                // where feedback was requested
                mfb = 0;
                for (i=0; i<nj; i++) {
                    if (joint[i]->feedback) {
                        dJointFeedback *fb = joint[i]->feedback;
                        dReal data[6];
                        Multiply1_12q1 (data, Jcopy+mfb*12, lambda+ofs[i], info[i].m);
                        fb->f1[0] = data[0];
                        fb->f1[1] = data[1];
                        fb->f1[2] = data[2];
                        fb->t1[0] = data[3];
                        fb->t1[1] = data[4];
                        fb->t1[2] = data[5];
                        if (joint[i]->node[1].body)
                        {
                            Multiply1_12q1 (data, Jcopy+mfb*12+6, lambda+ofs[i], info[i].m);
                            fb->f2[0] = data[0];
                            fb->f2[1] = data[1];
                            fb->f2[2] = data[2];
                            fb->t2[0] = data[3];
                            fb->t2[1] = data[4];
                            fb->t2[2] = data[5];
                        }
                        mfb += info[i].m;
                    }
                }
            }
#endif
        }

    }

	// compute the velocity update:
	// add stepsize * invM * fe to the body velocity

	IFTIMING (dTimerNow ("compute velocity update");)

    // ERICF CHANGE - take a look at the velocity on our first body - if it looks like it exploded,
    // ignore this entire update.
    {
        // dReal testVal = (nb > 0)?dFabs(body[0]->lvel[0] + (stepsize * body[0]->invMass * body[0]->facc[0])):0.0;
        // if (isnan(testVal) || isinf(testVal) || testVal > 9999.0f){
        //     printf("SKIPPPPPPPING!\n");
        // }
        // else{
            for (i=0; i<nb; i++) {
                dReal body_invMass = body[i]->invMass;
                for (j=0; j<3; j++) body[i]->lvel[j] += stepsize * body_invMass * body[i]->facc[j];
                for (j=0; j<3; j++) body[i]->tacc[j] *= stepsize;
                dMULTIPLYADD0_331 (body[i]->avel,invI + i*12,body[i]->tacc);
// #ifndef dNODEBUG
//                 for (j=0; j<3; j++){
//                     if ((dFabs(body[i]->lvel[j]) > 9999.0f) || (dFabs(body[i]->avel[j]) > 9999.0f)){
//                         printf("WTFFFFFFF!!!!\n");
//                     }
//                 }
// #endif
            }
        // }
    }
    
#if 0
	// check that the updated velocity obeys the constraint (this check needs unmodified J)
	dRealAllocaArray (vel,nb*6);
	for (i=0; i<nb; i++) {
		for (j=0; j<3; j++) vel[i*6+j] = body[i]->lvel[j];
		for (j=0; j<3; j++) vel[i*6+3+j] = body[i]->avel[j];
	}
	dRealAllocaArray (tmp,m);
	multiply_J (m,J,jb,vel,tmp);
	dReal error = 0;
	for (i=0; i<m; i++) error += dFabs(tmp[i]);
	printf ("velocity error = %10.6e\n",error);
#endif

	// update the position and orientation from the new linear/angular velocity
	// (over the given timestep)
	IFTIMING (dTimerNow ("update position");)
	for (i=0; i<nb; i++) dxStepBody (body[i],stepsize);

	IFTIMING (dTimerNow ("tidy up");)

	// zero all force accumulators
	for (i=0; i<nb; i++) {
		dSetZero (body[i]->facc,3);
		dSetZero (body[i]->tacc,3);
	}

	IFTIMING (dTimerEnd();)
	IFTIMING (if (m > 0) dTimerReport (stdout,1);)
}
