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
 *	Cylinder-sphere collider by Alen Ladavac (Croteam)
 *  Ported to ODE by Nguyen Binh ( www.coderfarm.com )
 */

// NOTES :
// I only try to solve some obvious problems on cylinder-sphere
// If you like to solve all problem when very large sphere drop over 
// very small cylinder or vice versa, you will need to re-organize the code.
// I would eventually, try to do it later, when I have more time.
// On this version, I only try to solve the problem when a very large cylinder
// drop over very small sphere.

#include "ode/ode_collision.h"
#include "ode/ode_matrix.h"
#include "ode/ode_rotation.h"
#include "ode/ode_math.h"
#include "ode/ode_collision_util.h"
#include "ode/ode_collision_kernel.h"
#include "ode/ode_objects.h"

// Axis of Cylinder - ODE use axis Z.
static const int	nCYLINDER_AXIS = 2;

// Method to cure very deep penetration
// When two objects are in very deep penetration, we should exaggerate
// the depth value between them or numerical errors will make one object go
// through the other.
// 0 : do nothing - keep the calculated depth
// 1 : exaggerate calculated depth by multiple of fDepthRecoverRatio times.
// 2 : exaggerate calculated depth by multiple of log of ration between
//     heavy object and light object. This method take a little more computing
//	   power but can be used to solved almost all "drop very large object over
//	   small object" problems.

#define _DEPTH_RECOVER_METHOD_ 0

#if (_DEPTH_RECOVER_METHOD_ == 1)
static const dReal fDepthRecoverRatio = REAL(2.0);
#endif

int dCollideCylinderSphere(dxGeom *gCylinder, dxGeom *gSphere, int flags, dContactGeom *contact, int skip)
{
	// get source hull position and orientation
	// Number of contacts
    int		nContacts = 0;

	dQuaternion mQuatCylinder;
	dGeomGetQuaternion(gCylinder,mQuatCylinder);

	dVector3 vCylinderPos; 
	dMatrix3 mCylinderRot;
	const dReal* pRotCyc = dGeomGetRotation(gCylinder); 
	dMatrix3Copy(pRotCyc,mCylinderRot);

	const dVector3* pPosCyc = (const dVector3*)dGeomGetPosition(gCylinder);
	dVector3Copy(*pPosCyc,vCylinderPos);

	// get capsule radius and size
	dReal fCylinderRadius;
	dReal fCylinderSize;

	dGeomCylinderGetParams(gCylinder,&fCylinderRadius,&fCylinderSize);

	// get destination hull position and radius
	dMatrix3 mSphereRot;
	dVector3 vSpherePos;

	dReal fSphereRadius = dGeomSphereGetRadius(gSphere);

	const dReal* pSphereRot = dGeomGetRotation(gSphere); 
	dMatrix3Copy(pSphereRot,mSphereRot);

	const dVector3* pSpherePos = (const dVector3*)dGeomGetPosition(gSphere);
	dVector3Copy(*pSpherePos,vSpherePos);

	// transform sphere position in cylinder frame
	dVector3 vSpherePosInCylinderFrame;
	// temporary variables
	dVector3 vTemp;
	dVector3 vTemp2;
	
	// Sphere position relative to Cylinder
	dVector3Subtract(vSpherePos,vCylinderPos,vTemp);

	dQuaternion mInvQuatCylinder;
	dQuatInv(mQuatCylinder,mInvQuatCylinder);
	dQuatTransform(mInvQuatCylinder,vTemp,vSpherePosInCylinderFrame);

	// cylinder boundaries along cylinder axis
	dReal fHighCylinderBase =  fCylinderSize*0.5f;
	dReal fLowCylinderBase  = -fCylinderSize*0.5f;

	dReal fDeltaHigh = (vSpherePosInCylinderFrame[nCYLINDER_AXIS]  - fHighCylinderBase );
	dReal fDeltaLow = (fLowCylinderBase - vSpherePosInCylinderFrame[nCYLINDER_AXIS] );

	// check if sphere intersecting with cylindrical part - side part
	if( fDeltaHigh <= REAL(0.0) && fDeltaLow <= REAL(0.0)) 
	{
		// This mean the center of sphere lies between high and low base along cylinder axis
		// of the cylinder

		// calculate center of sphere on cylindrical axis which is referent for collision
		// This circle of cylinder is in the same level with the center of sphere
		dVector3 vBodyPoint = {REAL(0.0),REAL(0.0),REAL(0.0)};
		vBodyPoint[nCYLINDER_AXIS] = vSpherePosInCylinderFrame[nCYLINDER_AXIS];

		// calculate distance between two spheres
		dVector3Subtract(vSpherePosInCylinderFrame,vBodyPoint,vTemp );
		dReal fDistance = dVector3Length( vTemp );

		if ( fDistance <= (fCylinderRadius + fSphereRadius)) 
		{			
			dReal	 fTemp;
			dReal	 fDepth;
			dVector3 vPoint;

			// Axis dependent - Should change when you don't use cylinder along z axis
			if (dFabs(vSpherePosInCylinderFrame[0]) <= fCylinderRadius 
				&& dFabs(vSpherePosInCylinderFrame[1]) <= fCylinderRadius)
			{
				// Actually, not side penetrate but very deep top (or) bottom penetrate
				// We have to use some trick to solve it.

				// First try to find top or bottom penetrate
				dVector3	vCylinderLinearVel = {REAL(0.0),REAL(0.0),REAL(0.0),REAL(0.0)};
				dVector3	vSphereLinearVel   = {REAL(0.0),REAL(0.0),REAL(0.0),REAL(0.0)};
				dBodyID		CylinderBody	= dGeomGetBody(gCylinder);
				dBodyID		SphereBody		= dGeomGetBody(gSphere);

				// Get linear velocity
				if (CylinderBody)
				{
					const dReal* pCylinderVel = dBodyGetLinearVel(CylinderBody);
					vCylinderLinearVel[0] = pCylinderVel[0];
					vCylinderLinearVel[1] = pCylinderVel[1];
					vCylinderLinearVel[2] = pCylinderVel[2];
				}

				if (SphereBody)
				{
					const dReal* pSphereVel = dBodyGetLinearVel(SphereBody);
					vSphereLinearVel[0] = pSphereVel[0];
					vSphereLinearVel[1] = pSphereVel[1];
					vSphereLinearVel[2] = pSphereVel[2];
				}

				dVector3	vSphereVelInCylinderFrame;
				dVector3Subtract(vSphereLinearVel,vCylinderLinearVel,vSphereVelInCylinderFrame);

				#if (_DEPTH_RECOVER_METHOD_ == 2)
				dReal fRelativeVel = dVector3Length(vSphereVelInCylinderFrame);
				#endif

				dNormalize3(vSphereVelInCylinderFrame);

                dVector3	vCylinderAxis;
				dMat3GetCol(mCylinderRot,nCYLINDER_AXIS,vCylinderAxis);
				dNormalize3(vCylinderAxis);

                dReal fAngle = dVector3Dot(vSphereVelInCylinderFrame,vCylinderAxis);

				// Solve problem when drop very large cylinder over very small sphere
				if (fAngle < 0 )
				{
					// Top penetrate
					// collision normal showing up from top cylinder plane
					dVector3 vNormal = {REAL(0.0),REAL(0.0),REAL(0.0)};
					vNormal[nCYLINDER_AXIS] = REAL(-1.0);

					// Transform to cylinder space
					dQuatTransform(mQuatCylinder,vNormal,vTemp2);
					dNormalize3(vTemp2);

					// set collision point in cylinder frame
					dVector3Copy(vSpherePosInCylinderFrame,vPoint);
					vPoint[nCYLINDER_AXIS] = fHighCylinderBase;

					// transform in absolute space
					dQuatTransform(mQuatCylinder,vPoint,vTemp);
					dVector3Add(vTemp,vCylinderPos,vPoint);

					// calculate collision depth          
					dReal fDepth = fSphereRadius - fDeltaHigh;	
					// Experiment show that we need to exaggerate depth ratio to 
					// keep the small object from being stuck in other

					#if (_DEPTH_RECOVER_METHOD_ == 1)
					// Constant ratio
					fDepth *= fDepthRecoverRatio;
					#endif // (_DEPTH_RECOVER_METHOD_ == 1)

					// use log of ratio between large object and small object masses
					#if (_DEPTH_RECOVER_METHOD_ == 2)
					if (CylinderBody && SphereBody) 
					{
						// No static geom -> need to exaggerate
						dMass sphereMass;
						dBodyGetMass(SphereBody,&sphereMass);
						dMass cylinderMass;
						dBodyGetMass(CylinderBody,&cylinderMass);

						dReal fRatio1 = cylinderMass.mass/sphereMass.mass;
						
						if (fRatio1 > REAL(1.0))
						{
							fDepth *=  fRelativeVel *dSqrt(fRatio1);
						}
						else
						{
							fDepth *= fRelativeVel * dSqrt( REAL(1.0) / fRatio1);
						}													
					}
					#endif // (_DEPTH_RECOVER_METHOD_ == 2)

					// generate contact
					if (nContacts < (flags & NUMC_MASK))
					{
						dContactGeom* Contact = SAFECONTACT(flags, contact, nContacts, skip );
						Contact->depth = fDepth;
						dVector3Copy(vTemp2,Contact->normal);
						dVector3Copy(vPoint,Contact->pos);
						Contact->g1 = gCylinder;
						Contact->g2 = gSphere;
						nContacts++;
					}

					return nContacts;
				}
				else
				{
					// Near Bottom
					dVector3 vNormal = {REAL(0.0),REAL(0.0),REAL(0.0)};
					vNormal[nCYLINDER_AXIS] = REAL(1.0);
					// Transform to cylinder space
					dQuatTransform(mQuatCylinder,vNormal,vTemp2);
					dNormalize3(vTemp2);

					// set collision point in cylinder frame
					dVector3Copy(vSpherePosInCylinderFrame,vPoint);
					vPoint[nCYLINDER_AXIS] = fLowCylinderBase;

					// transform in absolute space
					dQuatTransform(mQuatCylinder,vPoint,vTemp);
					dVector3Add(vTemp,vCylinderPos,vPoint);

					// calculate collision depth          
					dReal fDepth = fSphereRadius - fDeltaLow;
					// Experiment show that we need to exaggerate depth ratio to 
					// keep the small sphere from being stuck

					#if (_DEPTH_RECOVER_METHOD_ == 1)
					// Constant ratio
					fDepth *= fDepthRecoverRatio;
					#endif // (_DEPTH_RECOVER_METHOD_ == 1)

					// use log of ratio between large object and small object masses
					#if (_DEPTH_RECOVER_METHOD_ == 2)
					if (CylinderBody && SphereBody) 
					{
						// No static geom -> need to exaggerate
						dMass sphereMass;
						dBodyGetMass(SphereBody,&sphereMass);
						dMass cylinderMass;
						dBodyGetMass(CylinderBody,&cylinderMass);

						dReal fRatio1 = cylinderMass.mass/sphereMass.mass;

						if (fRatio1 > REAL(1.0))
						{
							fDepth *=  fRelativeVel *dSqrt(fRatio1);
						}
						else
						{
							fDepth *= fRelativeVel * dSqrt( REAL(1.0) / fRatio1);
						}								
					}
					#endif // (_DEPTH_RECOVER_METHOD_ == 2)


					// generate contact
					if (nContacts < (flags & NUMC_MASK))
					{
						dContactGeom* Contact = SAFECONTACT(flags, contact, nContacts, skip );
						Contact->depth = fDepth;
						dVector3Copy(vTemp2,Contact->normal);
						dVector3Copy(vPoint,Contact->pos);
						Contact->g1 = gCylinder;
						Contact->g2 = gSphere;
						nContacts++;							
					}

					return nContacts;
				}
			}

			// calculate collision normal
			dVector3 vNormal;
			dQuatTransform(mQuatCylinder,vBodyPoint,vTemp);
			dVector3Add(vTemp,vCylinderPos,vTemp2);
			dVector3Subtract(vSpherePos,vTemp2,vNormal);
			dNormalize3(vNormal);
	
			// calculate collision point
			fTemp = fCylinderRadius-fSphereRadius-fDistance;
			
			vPoint[0] = vSpherePos[0] + vNormal[0]* fTemp *REAL(0.5);
			vPoint[1] = vSpherePos[1] + vNormal[1]* fTemp *REAL(0.5);
			vPoint[2] = vSpherePos[2] + vNormal[2]* fTemp *REAL(0.5);

			// calculate penetration depth
			fDepth = fCylinderRadius + fSphereRadius-fDistance;

			// generate contact
			if (nContacts < (flags & NUMC_MASK))
			{
				dContactGeom* Contact = SAFECONTACT(flags, contact, nContacts, skip );
				Contact->depth = fDepth;
				dVector3Copy(vNormal,Contact->normal);
				dVector3Copy(vPoint,Contact->pos);
				Contact->g1 = gCylinder;
				Contact->g2 = gSphere;
				nContacts++;
				dVector3Inv(Contact->normal);
			}

			return nContacts;
		}
		// check if sphere is intersecting with top or bottom circle of cylinder
	} 
	else 
	{
		// test sphere on top circle of cylinder
		if ( fDeltaHigh >  REAL(0.0)) 
		{
			// check if sphere is intersecting top plane
			if( fDeltaHigh < fSphereRadius ) 
			{
				// calculate center of sphere on cylindrical axis which is referent for collision
				dVector3 vBodyPoint = {REAL(0.0),REAL(0.0),REAL(0.0)};
                vBodyPoint[nCYLINDER_AXIS] = vSpherePosInCylinderFrame[nCYLINDER_AXIS];

				// distance between sphere and cylinder axis
				dVector3Subtract(vSpherePosInCylinderFrame,vBodyPoint,vTemp);
				dReal fDistance = dVector3Length(vTemp);

				// see if our intersection point is inside top circle
				if( fDistance < fCylinderRadius) 
				{
					// collision normal showing up from top cylinder plane
					dVector3 vNormal = {REAL(0.0),REAL(0.0),REAL(0.0)};
					vNormal[nCYLINDER_AXIS] = REAL(-1.0);
					// Transform to cylinder space
					dQuatTransform(mQuatCylinder,vNormal,vTemp2);
					dNormalize3(vTemp2);
					// set collision point in cylinder frame
					dVector3 vPoint;
					dVector3Copy(vSpherePosInCylinderFrame,vPoint);
					vPoint[nCYLINDER_AXIS] = fHighCylinderBase;

					// transform in absolute space
					dQuatTransform(mQuatCylinder,vPoint,vTemp);
					dVector3Add(vTemp,vCylinderPos,vPoint);

					// calculate collision depth          
					dReal fDepth = fSphereRadius - fDeltaHigh;

					// generate contact
					if (nContacts < (flags & NUMC_MASK))
					{
						dContactGeom* Contact = SAFECONTACT(flags, contact, nContacts, skip );
						Contact->depth = fDepth;
						dVector3Copy(vTemp2,Contact->normal);
						dVector3Copy(vPoint,Contact->pos);
						Contact->g1 = gCylinder;
						Contact->g2 = gSphere;
						nContacts++;
					}

					return nContacts;
				} 

				// if we got here then we are potentially intersecting the top ring 
				// of the cylinder

				// define top circle center point on cylinder axis
				dVector3 vE0 = {REAL(0.0),REAL(0.0),REAL(0.0)};
				vE0[nCYLINDER_AXIS] = fHighCylinderBase;

				// set direction vector from center to circle edge
				dVector3 vDirVector;
				dVector3Subtract(vSpherePosInCylinderFrame,vE0,vDirVector);

				// project it onto top plane
				vDirVector[nCYLINDER_AXIS] = REAL(0.0);

				// and make it unit vector
				dNormalize3(vDirVector);

				// define point on the top circle edge
				dVector3 vPoint;
				vPoint[0] = vE0[0] + vDirVector[0] * fCylinderRadius;
				vPoint[1] = vE0[1] + vDirVector[1] * fCylinderRadius;
				vPoint[2] = vE0[2] + vDirVector[2] * fCylinderRadius;

				// calculate distance from edge to sphere
				dVector3Subtract(vPoint,vSpherePosInCylinderFrame,vTemp);
				dReal fDistEdgeToSphere = dVector3Length(vTemp);
				
				// if edge/sphere are intersecting
				if (fDistEdgeToSphere < fSphereRadius ) 
				{
					// transform in absolute space
					dQuatTransform(mQuatCylinder,vPoint,vTemp);
					dVector3Add(vTemp,vCylinderPos,vPoint);

					// calculate collision normal
					dVector3 vNormal;
					dVector3Subtract(vPoint,vSpherePos,vNormal);

					// and make it unit vector
					dNormalize3(vNormal);
					// calculate penetration depth
					dReal fDepth = fSphereRadius - fDistEdgeToSphere;

					// generate contact
					if (nContacts < (flags & NUMC_MASK))
					{
						dContactGeom* Contact = SAFECONTACT(flags, contact, nContacts, skip );
						Contact->depth = fDepth;
						dVector3Copy(vNormal,Contact->normal);
						dVector3Copy(vPoint,Contact->pos);
						Contact->g1 = gCylinder;
						Contact->g2 = gSphere;
						nContacts++;
					}

					return nContacts;
				}
			}
 
			// test sphere on bottom circle of cylinder
		} 
		else 
		if (vSpherePosInCylinderFrame[nCYLINDER_AXIS] < fLowCylinderBase) 
		{

			if( fDeltaLow < fSphereRadius ) 
			{
				// calculate center of sphere on cylindrical axis which is referent for collision
				dVector3 vBodyPoint = {REAL(0.0),REAL(0.0),REAL(0.0)};
				vBodyPoint[nCYLINDER_AXIS] = vSpherePosInCylinderFrame[nCYLINDER_AXIS];

				// distance between sphere and cylinder axis
				dVector3Subtract(vSpherePosInCylinderFrame,vBodyPoint,vTemp);
				dReal fDistance = dVector3Length(vTemp);

				// see if our intersection point is inside bottom circle
				if( fDistance < fCylinderRadius ) 
				{
					// collision normal showing up from top cylinder plane
					dVector3 vNormal =  {REAL(0.0),REAL(0.0),REAL(0.0)};//(0,-1,0);
					vNormal[nCYLINDER_AXIS] = REAL(1.0);
					
					dQuatTransform(mQuatCylinder,vNormal,vTemp2);
					dNormalize3(vTemp2);

					// set collision point in cylinder frame
					dVector3 vPoint;
					dVector3Copy(vSpherePosInCylinderFrame,vPoint);
					vPoint[nCYLINDER_AXIS] = fLowCylinderBase;

					// transform in absolute space
					dQuatTransform(mQuatCylinder,vPoint,vTemp);
					dVector3Add(vTemp,vCylinderPos,vPoint);

					// calculate collision depth          
					dReal fDepth = fSphereRadius - fDeltaLow;

					// generate contact
					if (nContacts < (flags & NUMC_MASK))
					{
						dContactGeom* Contact = SAFECONTACT(flags, contact, nContacts, skip );
						Contact->depth = fDepth;
						dVector3Copy(vTemp2,Contact->normal);
						dVector3Copy(vPoint,Contact->pos);
						Contact->g1 = gCylinder;
						Contact->g2 = gSphere;
						nContacts++;
					}

					return nContacts;
				}

				// if we got here then we are potentially intersecting the bottom ring 
				// of the cylinder

				// define top circle center point on cylinder axis
				dVector3 vE0 =  {REAL(0.0),REAL(0.0),REAL(0.0)};//(0,fLowCylinderBase,0);
				vE0[nCYLINDER_AXIS] = fLowCylinderBase;

				// set direction vector from center to circle edge
				dVector3 vDirVector;
				dVector3Subtract(vSpherePosInCylinderFrame,vE0,vDirVector);

				// project it onto top plane
				vDirVector[nCYLINDER_AXIS] = REAL(0.0);

				// and make it unit vector
				dNormalize3(vDirVector);

				// define point on the top circle edge
				dVector3 vPoint;
				vPoint[0] = vE0[0] + vDirVector[0] * fCylinderRadius;
				vPoint[1] = vE0[1] + vDirVector[1] * fCylinderRadius;
				vPoint[2] = vE0[2] + vDirVector[2] * fCylinderRadius;

				dVector3Subtract(vPoint,vSpherePosInCylinderFrame,vTemp);
				dReal fDistEdgeToSphere = dVector3Length(vTemp);

				// if edge/sphere are intersecting
				if (fDistEdgeToSphere < fSphereRadius )
				{
					// transform in absolute space
					dQuatTransform(mQuatCylinder,vPoint,vTemp);
					dVector3Add(vTemp,vCylinderPos,vPoint);

					// calculate collision normal
					dVector3 vNormal;// = dVector3(vPoint - vSpherePos);
					dVector3Subtract(vPoint,vSpherePos,vNormal);

					// and make it unit vector
					dNormalize3(vNormal);

					// calculate penetration depth
					dReal fDepth = fSphereRadius - fDistEdgeToSphere;

					if (nContacts < (flags & NUMC_MASK))
					{
						dContactGeom* Contact = SAFECONTACT(flags, contact, nContacts, skip );
						Contact->depth = fDepth;
						dVector3Copy(vNormal,Contact->normal);
						dVector3Copy(vPoint,Contact->pos);
						Contact->g1 = gCylinder;
						Contact->g2 = gSphere;
						nContacts++;
					}

					return nContacts;
				}
			}    
		}
	} 

	return nContacts;
}


