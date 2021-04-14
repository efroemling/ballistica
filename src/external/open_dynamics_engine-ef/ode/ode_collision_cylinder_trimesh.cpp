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
 *	Cylinder-trimesh collider by Alen Ladavac
 *   Ported to ODE by Nguyen Binh
 */

 // Silence warnings about shortening 64 vit values into 32 bit containers
#if __clang__
#pragma clang diagnostic ignored "-Wshorten-64-to-32"
#endif
#ifdef _MSC_VER
#pragma warning( disable: 4267)
#endif

#include "ode/ode_collision.h"
#include "ode/ode_matrix.h"
#include "ode/ode_rotation.h"
#include "ode/ode_math.h"
#include "ode/ode_collision_util.h"

#define TRIMESH_INTERNAL
#include "ode/ode_collision_trimesh_internal.h"


#define MAX_REAL	dInfinity
static const int	nCYLINDER_AXIS				= 2;
static const int    nCYLINDER_CIRCLE_SEGMENTS	= 8;
static const int    nMAX_CYLINDER_TRIANGLE_CLIP_POINTS	= 12;
static const int	gMaxLocalContacts = 32;

#define OPTIMIZE_CONTACTS 1

// Local contacts data
typedef struct _sLocalContactData
{
	dVector3	vPos;
	dVector3	vNormal;
	dReal		fDepth;
	int			nFlags; // 0 = filtered out, 1 = OK
}sLocalContactData;

typedef struct _sCylinderTrimeshColliderData
{
	// cylinder data
	dMatrix3	mCylinderRot;
	dQuaternion	qCylinderRot;
	dQuaternion	qInvCylinderRot;
	dVector3	vCylinderPos;
	dVector3	vCylinderAxis;
	dReal		fCylinderRadius;
	dReal		fCylinderSize;
	dVector3	avCylinderNormals[nCYLINDER_CIRCLE_SEGMENTS];

	// mesh data
	dQuaternion	qTrimeshRot;
	dQuaternion	qInvTrimeshRot;
	dMatrix3	mTrimeshRot;
	dVector3	vTrimeshPos;

	// global collider data
	dVector3	vBestPoint;
	dReal		fBestDepth;
	dReal		fBestCenter;
	dReal		fBestrt;
	int			iBestAxis;
	dVector3	vContactNormal;
	dVector3	vNormal;
	dVector3	vE0;
	dVector3	vE1;
	dVector3	vE2;

	// ODE stuff
	dGeomID				gCylinder;
	dxTriMesh*			gTrimesh;
	dContactGeom*		gContact;
	int					iFlags;
	int					iSkip;
	int					nContacts;// = 0;
	sLocalContactData	gLocalContacts[gMaxLocalContacts];
} sCylinderTrimeshColliderData;

// Short type name
typedef  sCylinderTrimeshColliderData sData;

// Use to classify contacts to be "near" in position
static const dReal fSameContactPositionEpsilon = REAL(0.0001); // 1e-4
// Use to classify contacts to be "near" in normal direction
static const dReal fSameContactNormalEpsilon = REAL(0.0001); // 1e-4

// If this two contact can be classified as "near"
inline int _IsNearContacts(sLocalContactData& c1,sLocalContactData& c2)
{
	int bPosNear = 0;
	int bSameDir = 0;
	dVector3	vDiff;

	// First check if they are "near" in position
	dVector3Subtract(c1.vPos,c2.vPos,vDiff);
	if (  (dFabs(vDiff[0]) < fSameContactPositionEpsilon)
		&&(dFabs(vDiff[1]) < fSameContactPositionEpsilon)
		&&(dFabs(vDiff[2]) < fSameContactPositionEpsilon))
	{
		bPosNear = 1;
	}

	// Second check if they are "near" in normal direction
	dVector3Subtract(c1.vNormal,c2.vNormal,vDiff);
	if (  (dFabs(vDiff[0]) < fSameContactNormalEpsilon)
		&&(dFabs(vDiff[1]) < fSameContactNormalEpsilon)
		&&(dFabs(vDiff[2]) < fSameContactNormalEpsilon) )
	{
		bSameDir = 1;
	}

	// Will be "near" if position and normal direction are "near"
	return (bPosNear && bSameDir);
}

inline int _IsBetter(sLocalContactData& c1,sLocalContactData& c2)
{
	// The not better will be throw away
	// You can change the selection criteria here
	return (c1.fDepth > c2.fDepth);
}

// iterate through gLocalContacts and filtered out "near contact"
inline void	_OptimizeLocalContacts(sData& cData)
{
	int nContacts = cData.nContacts;

	for (int i = 0; i < nContacts-1; i++)
	{
		for (int j = i+1; j < nContacts; j++)
		{
			if (_IsNearContacts(cData.gLocalContacts[i],cData.gLocalContacts[j]))
			{
				// If they are seem to be the samed then filtered
				// out the least penetrate one
				if (_IsBetter(cData.gLocalContacts[j],cData.gLocalContacts[i]))
				{
					cData.gLocalContacts[i].nFlags = 0; // filtered 1st contact
				}
				else
				{
					cData.gLocalContacts[j].nFlags = 0; // filtered 2nd contact
				}

				// NOTE
				// There is other way is to add two depth together but
				// it not work so well. Why???
			}
		}
	}
}

inline int	_ProcessLocalContacts(sData& cData)
{
	if (cData.nContacts == 0)
	{
		return 0;
	}

#ifdef OPTIMIZE_CONTACTS
	if (cData.nContacts > 1)
	{
		// Can be optimized...
		_OptimizeLocalContacts(cData);
	}
#endif

	int iContact = 0;
	dContactGeom* Contact = 0;

	int nFinalContact = 0;

	for (iContact = 0; iContact < cData.nContacts; iContact ++)
	{
		if (1 == cData.gLocalContacts[iContact].nFlags)
		{
            // eric added - dont go over our contact limit
            if (iContact >= (cData.iFlags & 0x0ffff))
                break;
			Contact = SAFECONTACT(cData.iFlags, cData.gContact, nFinalContact, cData.iSkip);
			Contact->depth = cData.gLocalContacts[iContact].fDepth;
			dVector3Copy(cData.gLocalContacts[iContact].vNormal,Contact->normal);
			dVector3Copy(cData.gLocalContacts[iContact].vPos,Contact->pos);
			Contact->g1 = cData.gCylinder;
			Contact->g2 = cData.gTrimesh;
			dVector3Inv(Contact->normal);

			nFinalContact++;
		}
	}
	// debug
	//if (nFinalContact != cData.nContacts)
	//{
	//	printf("[Info] %d contacts generated,%d  filtered.\n",cData.nContacts,cData.nContacts-nFinalContact);
	//}

	return nFinalContact;
}


bool _cldTestAxis(sData& cData,
				  const dVector3 &v0,
				  const dVector3 &v1,
				  const dVector3 &v2,
                  dVector3& vAxis,
				  int iAxis,
				  bool bNoFlip = false)
{

	// calculate length of separating axis vector
	dReal fL = dVector3Length(vAxis);
	// if not long enough
	if ( fL < 1e-5f )
	{
		// do nothing
		return true;
	}

	// otherwise normalize it
	vAxis[0] /= fL;
	vAxis[1] /= fL;
	vAxis[2] /= fL;

	dReal fdot1 = dVector3Dot(cData.vCylinderAxis,vAxis);
	// project capsule on vAxis
	dReal frc;

	if (fdot1 > REAL(1.0) )
	{
		fdot1 = REAL(1.0);
		frc = dFabs(cData.fCylinderSize* REAL(0.5));
	}
	else
	{
		frc = dFabs((cData.fCylinderSize* REAL(0.5)) * fdot1)
			+ cData.fCylinderRadius * dFabs(REAL(1.0)-(fdot1*fdot1));
	}

	dVector3 vV0;
	dVector3Subtract(v0,cData.vCylinderPos,vV0);
	dVector3 vV1;
	dVector3Subtract(v1,cData.vCylinderPos,vV1);
	dVector3 vV2;
	dVector3Subtract(v2,cData.vCylinderPos,vV2);

	// project triangle on vAxis
	dReal afv[3];
	afv[0] = dVector3Dot( vV0 , vAxis );
	afv[1] = dVector3Dot( vV1 , vAxis );
	afv[2] = dVector3Dot( vV2 , vAxis );

	dReal fMin = MAX_REAL;
	dReal fMax = -MAX_REAL;

	// for each vertex
	for(int i = 0; i < 3; i++)
	{
		// find minimum
		if (afv[i]<fMin)
		{
			fMin = afv[i];
		}
		// find maximum
		if (afv[i]>fMax)
		{
			fMax = afv[i];
		}
	}

	// find capsule's center of interval on axis
	dReal fCenter = (fMin+fMax)* REAL(0.5);
	// calculate triangles halfinterval
	dReal fTriangleRadius = (fMax-fMin)*REAL(0.5);

	// if they do not overlap,
	if( dFabs(fCenter) > (frc+fTriangleRadius) )
	{
		// exit, we have no intersection
		return false;
	}

	// calculate depth
	dReal fDepth = -(dFabs(fCenter) - (frc + fTriangleRadius ) );

	// if greater then best found so far
	if ( fDepth < cData.fBestDepth )
	{
		// remember depth
		cData.fBestDepth			= fDepth;
		cData.fBestCenter		    = fCenter;
		cData.fBestrt				= frc;
		dVector3Copy(vAxis,cData.vContactNormal);
		cData.iBestAxis				= iAxis;

		// flip normal if interval is wrong faced
		if ( fCenter< REAL(0.0) && !bNoFlip)
		{
			dVector3Inv(cData.vContactNormal);
			cData.fBestCenter = -fCenter;
		}
	}

	return true;
}

// intersection test between edge and circle
bool _cldTestCircleToEdgeAxis(sData& cData,
							  const dVector3 &v0, const dVector3 &v1, const dVector3 &v2,
                              const dVector3 &vCenterPoint, const dVector3 &vCylinderAxis1,
                              const dVector3 &vVx0, const dVector3 &vVx1, int iAxis)
{
	// calculate direction of edge
	dVector3 vkl;
	dVector3Subtract( vVx1 , vVx0 , vkl);
	dNormalize3(vkl);
	// starting point of edge
	dVector3 vol;
	dVector3Copy(vVx0,vol);

	// calculate angle cosine between cylinder axis and edge
	dReal fdot2 = dVector3Dot(vkl , vCylinderAxis1);

	// if edge is perpendicular to cylinder axis
	if(dFabs(fdot2)<1e-5f)
	{
		// this can't be separating axis, because edge is parallel to circle plane
		return true;
	}

	// find point of intersection between edge line and circle plane
	dVector3 vTemp;
	dVector3Subtract(vCenterPoint,vol,vTemp);
	dReal fdot1 = dVector3Dot(vTemp,vCylinderAxis1);
	dVector3 vpnt;// = vol + vkl * (fdot1/fdot2);
	vpnt[0] = vol[0] + vkl[0] * fdot1/fdot2;
	vpnt[1] = vol[1] + vkl[1] * fdot1/fdot2;
	vpnt[2] = vol[2] + vkl[2] * fdot1/fdot2;

	// find tangent vector on circle with same center (vCenterPoint) that touches point of intersection (vpnt)
	dVector3 vTangent;
	dVector3Subtract(vCenterPoint,vpnt,vTemp);
	dVector3Cross(vTemp,vCylinderAxis1,vTangent);

	// find vector orthogonal both to tangent and edge direction
	dVector3 vAxis;
	dVector3Cross(vTangent,vkl,vAxis);

	// use that vector as separating axis
	return _cldTestAxis( cData ,v0, v1, v2, vAxis, iAxis );
}

// helper for less key strokes
// r = ( (v1 - v2) cross v3 ) cross v3
inline void _CalculateAxis(const dVector3& v1,
						   const dVector3& v2,
						   const dVector3& v3,
						   dVector3& r)
{
	dVector3 t1;
	dVector3 t2;

	dVector3Subtract(v1,v2,t1);
	dVector3Cross(t1,v3,t2);
	dVector3Cross(t2,v3,r);
}

bool _cldTestSeparatingAxes(sData& cData,
							const dVector3 &v0,
							const dVector3 &v1,
							const dVector3 &v2)
{

	// calculate edge vectors
	dVector3Subtract(v1 ,v0 , cData.vE0);
	// cData.vE1 has been calculated before -> so save some cycles here
	dVector3Subtract(v0 ,v2 , cData.vE2);

	// calculate caps centers in absolute space
	dVector3 vCp0;
	vCp0[0] = cData.vCylinderPos[0] + cData.vCylinderAxis[0]*(cData.fCylinderSize* REAL(0.5));
	vCp0[1] = cData.vCylinderPos[1] + cData.vCylinderAxis[1]*(cData.fCylinderSize* REAL(0.5));
	vCp0[2] = cData.vCylinderPos[2] + cData.vCylinderAxis[2]*(cData.fCylinderSize* REAL(0.5));

	dVector3 vCp1;
	vCp1[0] = cData.vCylinderPos[0] - cData.vCylinderAxis[0]*(cData.fCylinderSize* REAL(0.5));
	vCp1[1] = cData.vCylinderPos[1] - cData.vCylinderAxis[1]*(cData.fCylinderSize* REAL(0.5));
	vCp1[2] = cData.vCylinderPos[2] - cData.vCylinderAxis[2]*(cData.fCylinderSize* REAL(0.5));

	// reset best axis
	cData.iBestAxis = 0;
	dVector3 vAxis;

	// axis cData.vNormal
	//vAxis = -cData.vNormal;
	vAxis[0] = -cData.vNormal[0];
	vAxis[1] = -cData.vNormal[1];
	vAxis[2] = -cData.vNormal[2];
	if (!_cldTestAxis(cData, v0, v1, v2, vAxis, 1, true))
	{
		return false;
	}

	// axis CxE0
	// vAxis = ( cData.vCylinderAxis cross cData.vE0 );
	dVector3Cross(cData.vCylinderAxis, cData.vE0,vAxis);
	if (!_cldTestAxis(cData, v0, v1, v2, vAxis, 2))
	{
		return false;
	}

	// axis CxE1
	// vAxis = ( cData.vCylinderAxis cross cData.vE1 );
	dVector3Cross(cData.vCylinderAxis, cData.vE1,vAxis);
	if (!_cldTestAxis(cData, v0, v1, v2, vAxis, 3))
	{
		return false;
	}

	// axis CxE2
	// vAxis = ( cData.vCylinderAxis cross cData.vE2 );
	dVector3Cross(cData.vCylinderAxis, cData.vE2,vAxis);
	if (!_cldTestAxis( cData ,v0, v1, v2, vAxis, 4))
	{
		return false;
	}

	// first vertex on triangle
	// axis ((V0-Cp0) x C) x C
	//vAxis = ( ( v0-vCp0 ) cross cData.vCylinderAxis ) cross cData.vCylinderAxis;
	_CalculateAxis(v0 , vCp0 , cData.vCylinderAxis , vAxis);
	if (!_cldTestAxis(cData, v0, v1, v2, vAxis, 11))
	{
		return false;
	}

	// second vertex on triangle
	// axis ((V1-Cp0) x C) x C
	// vAxis = ( ( v1-vCp0 ) cross cData.vCylinderAxis ) cross cData.vCylinderAxis;
	_CalculateAxis(v1 , vCp0 , cData.vCylinderAxis , vAxis);
	if (!_cldTestAxis(cData, v0, v1, v2, vAxis, 12))
	{
		return false;
	}

	// third vertex on triangle
	// axis ((V2-Cp0) x C) x C
	//vAxis = ( ( v2-vCp0 ) cross cData.vCylinderAxis ) cross cData.vCylinderAxis;
	_CalculateAxis(v2 , vCp0 , cData.vCylinderAxis , vAxis);
	if (!_cldTestAxis(cData, v0, v1, v2, vAxis, 13))
	{
		return FALSE;
	}

	// test cylinder axis
	// vAxis = cData.vCylinderAxis;
	dVector3Copy(cData.vCylinderAxis , vAxis);
	if (!_cldTestAxis(cData , v0, v1, v2, vAxis, 14))
	{
		return false;
	}

	// Test top and bottom circle ring of cylinder for separation
	dVector3 vccATop;
	vccATop[0] = cData.vCylinderPos[0] + cData.vCylinderAxis[0]*(cData.fCylinderSize * REAL(0.5));
	vccATop[1] = cData.vCylinderPos[1] + cData.vCylinderAxis[1]*(cData.fCylinderSize * REAL(0.5));
	vccATop[2] = cData.vCylinderPos[2] + cData.vCylinderAxis[2]*(cData.fCylinderSize * REAL(0.5));

	dVector3 vccABottom;
	vccABottom[0] = cData.vCylinderPos[0] - cData.vCylinderAxis[0]*(cData.fCylinderSize * REAL(0.5));
	vccABottom[1] = cData.vCylinderPos[1] - cData.vCylinderAxis[1]*(cData.fCylinderSize * REAL(0.5));
	vccABottom[2] = cData.vCylinderPos[2] - cData.vCylinderAxis[2]*(cData.fCylinderSize * REAL(0.5));


  if (!_cldTestCircleToEdgeAxis(cData, v0, v1, v2, vccATop, cData.vCylinderAxis, v0, v1, 15))
  {
    return false;
  }

  if (!_cldTestCircleToEdgeAxis(cData, v0, v1, v2, vccATop, cData.vCylinderAxis, v1, v2, 16))
  {
    return false;
  }

  if (!_cldTestCircleToEdgeAxis(cData, v0, v1, v2, vccATop, cData.vCylinderAxis, v0, v2, 17))
  {
    return false;
  }

  if (!_cldTestCircleToEdgeAxis(cData, v0, v1, v2, vccABottom, cData.vCylinderAxis, v0, v1, 18))
  {
    return false;
  }

  if (!_cldTestCircleToEdgeAxis(cData, v0, v1, v2, vccABottom, cData.vCylinderAxis, v1, v2, 19))
  {
    return false;
  }

  if (!_cldTestCircleToEdgeAxis(cData, v0, v1, v2, vccABottom, cData.vCylinderAxis, v0, v2, 20))
  {
    return false;
  }

  return true;
}

bool _cldClipCylinderEdgeToTriangle(sData& cData, const dVector3 &v0, const dVector3 &v1, const dVector3 &v2)
{
	// translate cylinder
	dReal fTemp = dVector3Dot(cData.vCylinderAxis , cData.vContactNormal);
	dVector3 vN2;
	vN2[0] = cData.vContactNormal[0] - cData.vCylinderAxis[0]*fTemp;
	vN2[1] = cData.vContactNormal[1] - cData.vCylinderAxis[1]*fTemp;
	vN2[2] = cData.vContactNormal[2] - cData.vCylinderAxis[2]*fTemp;

	fTemp = dVector3Length(vN2);
	if (fTemp < 1e-5)
	{
		return false;
	}

	// Normalize it
	vN2[0] /= fTemp;
	vN2[1] /= fTemp;
	vN2[2] /= fTemp;

	// calculate caps centers in absolute space
	dVector3 vCposTrans;
	vCposTrans[0] = cData.vCylinderPos[0] + vN2[0]*cData.fCylinderRadius;
	vCposTrans[1] = cData.vCylinderPos[1] + vN2[1]*cData.fCylinderRadius;
	vCposTrans[2] = cData.vCylinderPos[2] + vN2[2]*cData.fCylinderRadius;

	dVector3 vCEdgePoint0;
	vCEdgePoint0[0]  = vCposTrans[0] + cData.vCylinderAxis[0] * (cData.fCylinderSize* REAL(0.5));
	vCEdgePoint0[1]  = vCposTrans[1] + cData.vCylinderAxis[1] * (cData.fCylinderSize* REAL(0.5));
	vCEdgePoint0[2]  = vCposTrans[2] + cData.vCylinderAxis[2] * (cData.fCylinderSize* REAL(0.5));

	dVector3 vCEdgePoint1;
	vCEdgePoint1[0]  = vCposTrans[0] - cData.vCylinderAxis[0] * (cData.fCylinderSize* REAL(0.5));
	vCEdgePoint1[1]  = vCposTrans[1] - cData.vCylinderAxis[1] * (cData.fCylinderSize* REAL(0.5));
	vCEdgePoint1[2]  = vCposTrans[2] - cData.vCylinderAxis[2] * (cData.fCylinderSize* REAL(0.5));

	// transform cylinder edge points into triangle space
	vCEdgePoint0[0] -= v0[0];
	vCEdgePoint0[1] -= v0[1];
	vCEdgePoint0[2] -= v0[2];

	vCEdgePoint1[0] -= v0[0];
	vCEdgePoint1[1] -= v0[1];
	vCEdgePoint1[2] -= v0[2];

	dVector4 plPlane;
	dVector3 vPlaneNormal;

	// triangle plane
	//plPlane = Plane4f( -cData.vNormal, 0);
	vPlaneNormal[0] = -cData.vNormal[0];
	vPlaneNormal[1] = -cData.vNormal[1];
	vPlaneNormal[2] = -cData.vNormal[2];
	dConstructPlane(vPlaneNormal,REAL(0.0),plPlane);
	if(!dClipEdgeToPlane( vCEdgePoint0, vCEdgePoint1, plPlane ))
	{
		return false;
	}

	// plane with edge 0
	//plPlane = Plane4f( ( cData.vNormal cross cData.vE0 ), 1e-5f);
	dVector3Cross(cData.vNormal,cData.vE0,vPlaneNormal);
	dConstructPlane(vPlaneNormal,1e-5f,plPlane);
	if(!dClipEdgeToPlane( vCEdgePoint0, vCEdgePoint1, plPlane ))
	{
		return false;
	}

	// plane with edge 1
	//dVector3 vTemp = ( cData.vNormal cross cData.vE1 );
	dVector3Cross(cData.vNormal,cData.vE1,vPlaneNormal);
	fTemp = dVector3Dot(cData.vE0 , vPlaneNormal) - 1e-5;
	//plPlane = Plane4f( vTemp, -(( cData.vE0 dot vTemp )-1e-5f));
	dConstructPlane(vPlaneNormal,-fTemp,plPlane);
	if(!dClipEdgeToPlane( vCEdgePoint0, vCEdgePoint1, plPlane ))
	{
		return false;
	}

	// plane with edge 2
	// plPlane = Plane4f( ( cData.vNormal cross cData.vE2 ), 1e-5f);
	dVector3Cross(cData.vNormal,cData.vE2,vPlaneNormal);
	dConstructPlane(vPlaneNormal,1e-5f,plPlane);
	if(!dClipEdgeToPlane( vCEdgePoint0, vCEdgePoint1, plPlane ))
	{
		return false;
	}

	// return capsule edge points into absolute space
	vCEdgePoint0[0] += v0[0];
	vCEdgePoint0[1] += v0[1];
	vCEdgePoint0[2] += v0[2];

	vCEdgePoint1[0] += v0[0];
	vCEdgePoint1[1] += v0[1];
	vCEdgePoint1[2] += v0[2];

	// calculate depths for both contact points
	dVector3 vTemp;
	dVector3Subtract(vCEdgePoint0,cData.vCylinderPos, vTemp);
	dReal fRestDepth0 = -dVector3Dot(vTemp,cData.vContactNormal) + cData.fBestrt;
	dVector3Subtract(vCEdgePoint1,cData.vCylinderPos, vTemp);
	dReal fRestDepth1 = -dVector3Dot(vTemp,cData.vContactNormal) + cData.fBestrt;

	dReal fDepth0 = cData.fBestDepth - (fRestDepth0);
	dReal fDepth1 = cData.fBestDepth - (fRestDepth1);

	// clamp depths to zero
	if(fDepth0 < REAL(0.0) )
	{
		fDepth0 = REAL(0.0);
	}

	if(fDepth1<REAL(0.0))
	{
		fDepth1 = REAL(0.0);
	}

	// Generate contact 0
	{
		cData.gLocalContacts[cData.nContacts].fDepth = fDepth0;
		dVector3Copy(cData.vContactNormal,cData.gLocalContacts[cData.nContacts].vNormal);
		dVector3Copy(vCEdgePoint0,cData.gLocalContacts[cData.nContacts].vPos);
		cData.gLocalContacts[cData.nContacts].nFlags = 1;
		cData.nContacts++;
	}

	// Generate contact 1
	{
		// generate contacts
		cData.gLocalContacts[cData.nContacts].fDepth = fDepth1;
		dVector3Copy(cData.vContactNormal,cData.gLocalContacts[cData.nContacts].vNormal);
		dVector3Copy(vCEdgePoint1,cData.gLocalContacts[cData.nContacts].vPos);
		cData.gLocalContacts[cData.nContacts].nFlags = 1;
		cData.nContacts++;
	}

	return true;
}

void _cldClipCylinderToTriangle(sData& cData,const dVector3 &v0, const dVector3 &v1, const dVector3 &v2)
{
	dVector3 avPoints[3];
	dVector3 avTempArray1[nMAX_CYLINDER_TRIANGLE_CLIP_POINTS];
	dVector3 avTempArray2[nMAX_CYLINDER_TRIANGLE_CLIP_POINTS];

	dSetZero(&avTempArray1[0][0],nMAX_CYLINDER_TRIANGLE_CLIP_POINTS * 4);
	dSetZero(&avTempArray2[0][0],nMAX_CYLINDER_TRIANGLE_CLIP_POINTS * 4);

	// setup array of triangle vertices
	dVector3Copy(v0,avPoints[0]);
	dVector3Copy(v1,avPoints[1]);
	dVector3Copy(v2,avPoints[2]);

	dVector3 vCylinderCirclePos, vCylinderCircleNormal_Rel;
	dSetZero(vCylinderCircleNormal_Rel,4);
	// check which circle from cylinder we take for clipping
	if ( dVector3Dot(cData.vCylinderAxis , cData.vContactNormal) > REAL(0.0))
	{
		// get top circle
		vCylinderCirclePos[0] = cData.vCylinderPos[0] + cData.vCylinderAxis[0]*(cData.fCylinderSize*REAL(0.5));
		vCylinderCirclePos[1] = cData.vCylinderPos[1] + cData.vCylinderAxis[1]*(cData.fCylinderSize*REAL(0.5));
		vCylinderCirclePos[2] = cData.vCylinderPos[2] + cData.vCylinderAxis[2]*(cData.fCylinderSize*REAL(0.5));

		vCylinderCircleNormal_Rel[nCYLINDER_AXIS] = REAL(-1.0);
	}
	else
	{
		// get bottom circle
		vCylinderCirclePos[0] = cData.vCylinderPos[0] - cData.vCylinderAxis[0]*(cData.fCylinderSize*REAL(0.5));
		vCylinderCirclePos[1] = cData.vCylinderPos[1] - cData.vCylinderAxis[1]*(cData.fCylinderSize*REAL(0.5));
		vCylinderCirclePos[2] = cData.vCylinderPos[2] - cData.vCylinderAxis[2]*(cData.fCylinderSize*REAL(0.5));

		vCylinderCircleNormal_Rel[nCYLINDER_AXIS] = REAL(1.0);
	}

	dVector3 vTemp;
	dQuatInv(cData.qCylinderRot , cData.qInvCylinderRot);
	// transform triangle points to space of cylinder circle
	for(int i=0; i<3; i++)
	{
		dVector3Subtract(avPoints[i] , vCylinderCirclePos , vTemp);
		dQuatTransform(cData.qInvCylinderRot,vTemp,avPoints[i]);
	}

	int iTmpCounter1 = 0;
	int iTmpCounter2 = 0;
	dVector4 plPlane;

	// plane of cylinder that contains circle for intersection
	//plPlane = Plane4f( vCylinderCircleNormal_Rel, 0.0f );
	dConstructPlane(vCylinderCircleNormal_Rel,REAL(0.0),plPlane);
	dClipPolyToPlane(avPoints, 3, avTempArray1, iTmpCounter1, plPlane);

	// Body of base circle of Cylinder
	int nCircleSegment = 0;
	for (nCircleSegment = 0; nCircleSegment < nCYLINDER_CIRCLE_SEGMENTS; nCircleSegment++)
	{
		dConstructPlane(cData.avCylinderNormals[nCircleSegment],cData.fCylinderRadius,plPlane);

		if (0 == (nCircleSegment % 2))
		{
			dClipPolyToPlane( avTempArray1 , iTmpCounter1 , avTempArray2, iTmpCounter2, plPlane);
		}
		else
		{
			dClipPolyToPlane( avTempArray2, iTmpCounter2, avTempArray1 , iTmpCounter1 , plPlane );
		}

		dIASSERT( iTmpCounter1 >= 0 && iTmpCounter1 <= nMAX_CYLINDER_TRIANGLE_CLIP_POINTS );
		dIASSERT( iTmpCounter2 >= 0 && iTmpCounter2 <= nMAX_CYLINDER_TRIANGLE_CLIP_POINTS );
	}

	// back transform clipped points to absolute space
	dReal ftmpdot;
	dReal fTempDepth;
	dVector3 vPoint;

	int i = 0;
	if (nCircleSegment %2)
	{
		for( i=0; i<iTmpCounter2; i++)
		{
			dQuatTransform(cData.qCylinderRot,avTempArray2[i], vPoint);
			vPoint[0] += vCylinderCirclePos[0];
			vPoint[1] += vCylinderCirclePos[1];
			vPoint[2] += vCylinderCirclePos[2];

			dVector3Subtract(vPoint,cData.vCylinderPos,vTemp);
			ftmpdot	 = dFabs(dVector3Dot(vTemp, cData.vContactNormal));
			fTempDepth = cData.fBestrt - ftmpdot;
			// Depth must be positive
			if (fTempDepth > REAL(0.0))
			{
				cData.gLocalContacts[cData.nContacts].fDepth = fTempDepth;
				dVector3Copy(cData.vContactNormal,cData.gLocalContacts[cData.nContacts].vNormal);
				dVector3Copy(vPoint,cData.gLocalContacts[cData.nContacts].vPos);
				cData.gLocalContacts[cData.nContacts].nFlags = 1;
				cData.nContacts++;
			}
		}
	}
	else
	{
		for( i=0; i<iTmpCounter1; i++)
		{
			dQuatTransform(cData.qCylinderRot,avTempArray1[i], vPoint);
			vPoint[0] += vCylinderCirclePos[0];
			vPoint[1] += vCylinderCirclePos[1];
			vPoint[2] += vCylinderCirclePos[2];

			dVector3Subtract(vPoint,cData.vCylinderPos,vTemp);
			ftmpdot	 = dFabs(dVector3Dot(vTemp, cData.vContactNormal));
			fTempDepth = cData.fBestrt - ftmpdot;
			// Depth must be positive
			if (fTempDepth > REAL(0.0))
			{
				cData.gLocalContacts[cData.nContacts].fDepth = fTempDepth;
				dVector3Copy(cData.vContactNormal,cData.gLocalContacts[cData.nContacts].vNormal);
				dVector3Copy(vPoint,cData.gLocalContacts[cData.nContacts].vPos);
				cData.gLocalContacts[cData.nContacts].nFlags = 1;
				cData.nContacts++;
			}
		}
	}
}

void TestOneTriangleVsCylinder(   sData& cData,
								  const dVector3 &v0,
                                  const dVector3 &v1,
                                  const dVector3 &v2,
                                  const bool bDoubleSided)
{

	// calculate triangle normal
	dVector3Subtract( v2 , v1 ,cData.vE1);
	dVector3 vTemp;
	dVector3Subtract( v0 , v1 ,vTemp);
	dVector3Cross(cData.vE1 , vTemp , cData.vNormal );

	dNormalize3( cData.vNormal);

	// create plane from triangle
	//Plane4f plTrianglePlane = Plane4f( vPolyNormal, v0 );
	dReal plDistance = -dVector3Dot(v0, cData.vNormal);
	dVector4 plTrianglePlane;
	dConstructPlane( cData.vNormal,plDistance,plTrianglePlane);

	 // calculate sphere distance to plane
	dReal fDistanceCylinderCenterToPlane = dPointPlaneDistance(cData.vCylinderPos , plTrianglePlane);

	// Sphere must be over positive side of triangle
	if(fDistanceCylinderCenterToPlane < 0 && !bDoubleSided)
	{
		// if not don't generate contacts
		return;
	 }

	dVector3 vPnt0;
	dVector3 vPnt1;
	dVector3 vPnt2;

	if (fDistanceCylinderCenterToPlane < REAL(0.0) )
	{
		// flip it
		dVector3Copy(v0 , vPnt0);
		dVector3Copy(v1 , vPnt2);
		dVector3Copy(v2 , vPnt1);
	}
	else
	{
		dVector3Copy(v0 , vPnt0);
		dVector3Copy(v1 , vPnt1);
		dVector3Copy(v2 , vPnt2);
	}

	cData.fBestDepth = MAX_REAL;

	// do intersection test and find best separating axis
	if(!_cldTestSeparatingAxes(cData , vPnt0, vPnt1, vPnt2) )
	{
		// if not found do nothing
		return;
	}

	// if best separation axis is not found
	if ( cData.iBestAxis == 0 )
	{
		// this should not happen (we should already exit in that case)
		dIASSERT(false);
		// do nothing
		return;
	}

	dReal fdot = dVector3Dot( cData.vContactNormal , cData.vCylinderAxis );

	// choose which clipping method are we going to apply
	if (dFabs(fdot) < REAL(0.9) )
	{
		if (!_cldClipCylinderEdgeToTriangle(cData ,vPnt0, vPnt1, vPnt2))
		{
			return;
		}
	}
	else
	{
		_cldClipCylinderToTriangle(cData ,vPnt0, vPnt1, vPnt2);
	}

}

void _InitCylinderTrimeshData(sData& cData)
{
	// get cylinder information
	// Rotation
	const dReal* pRotCyc = dGeomGetRotation(cData.gCylinder);
	dMatrix3Copy(pRotCyc,cData.mCylinderRot);
	dGeomGetQuaternion(cData.gCylinder,cData.qCylinderRot);

	// Position
	const dVector3* pPosCyc = (const dVector3*)dGeomGetPosition(cData.gCylinder);
	dVector3Copy(*pPosCyc,cData.vCylinderPos);
	// Cylinder axis
	dMat3GetCol(cData.mCylinderRot,nCYLINDER_AXIS,cData.vCylinderAxis);
	// get cylinder radius and size
	dGeomCylinderGetParams(cData.gCylinder,&cData.fCylinderRadius,&cData.fCylinderSize);

	// get trimesh position and orientation
	const dReal* pRotTris = dGeomGetRotation(cData.gTrimesh);
	dMatrix3Copy(pRotTris,cData.mTrimeshRot);
	dGeomGetQuaternion(cData.gTrimesh,cData.qTrimeshRot);

	// Position
	const dVector3* pPosTris = (const dVector3*)dGeomGetPosition(cData.gTrimesh);
	dVector3Copy(*pPosTris,cData.vTrimeshPos);


	// calculate basic angle for 8-gon
	dReal fAngle = M_PI / nCYLINDER_CIRCLE_SEGMENTS;
	// calculate angle increment
	dReal fAngleIncrement = fAngle*REAL(2.0);

	// calculate plane normals
	// axis dependant code
	for(int i=0; i<nCYLINDER_CIRCLE_SEGMENTS; i++)
	{
		cData.avCylinderNormals[i][0] = -dCos(fAngle);
		cData.avCylinderNormals[i][1] = -dSin(fAngle);
		cData.avCylinderNormals[i][2] = REAL(0.0);

		fAngle += fAngleIncrement;
	}

	dSetZero(cData.vBestPoint,4);
	// reset best depth
	cData.fBestCenter = REAL(0.0);
}

// cylinder to mesh collider
int dCollideCylinderTrimesh(dxGeom *o1, dxGeom *o2, int flags, dContactGeom *contact, int skip)
{
	// Main data holder
	sData cData;

	// Assign ODE stuff
	cData.gCylinder	 = o1;
	cData.gTrimesh	 = (dxTriMesh*)o2;
	cData.iFlags	 = flags;
	cData.iSkip		 = skip;
	cData.gContact	 = contact;
	cData.nContacts  = 0;

	_InitCylinderTrimeshData(cData);

  OBBCollider& Collider{cData.gTrimesh->_OBBCollider};

	Point cCenter(cData.vCylinderPos[0],cData.vCylinderPos[1],cData.vCylinderPos[2]);

	Point cExtents(cData.fCylinderRadius,cData.fCylinderRadius,cData.fCylinderRadius);
	cExtents[nCYLINDER_AXIS] = cData.fCylinderSize * REAL(0.5);

	Matrix3x3 obbRot;

	obbRot[0][0] = cData.mCylinderRot[0];
	obbRot[1][0] = cData.mCylinderRot[1];
	obbRot[2][0] = cData.mCylinderRot[2];

	obbRot[0][1] = cData.mCylinderRot[4];
	obbRot[1][1] = cData.mCylinderRot[5];
	obbRot[2][1] = cData.mCylinderRot[6];

	obbRot[0][2] = cData.mCylinderRot[8];
	obbRot[1][2] = cData.mCylinderRot[9];
	obbRot[2][2] = cData.mCylinderRot[10];

	OBB obbCCylinder(cCenter,cExtents,obbRot);

	Matrix4x4 CCylinderMatrix;
	MakeMatrix(cData.vCylinderPos, cData.mCylinderRot, CCylinderMatrix);

	Matrix4x4 MeshMatrix;
	MakeMatrix(cData.vTrimeshPos, cData.mTrimeshRot, MeshMatrix);

	// TC results
	if (cData.gTrimesh->doBoxTC)
	{
		dxTriMesh::BoxTC* BoxTC = 0;
		for (int i = 0; i < cData.gTrimesh->BoxTCCache.size(); i++)
		{
			if (cData.gTrimesh->BoxTCCache[i].Geom == cData.gCylinder)
			{
				BoxTC = &cData.gTrimesh->BoxTCCache[i];
				break;
			}
		}
		if (!BoxTC)
		{
			cData.gTrimesh->BoxTCCache.push(dxTriMesh::BoxTC());

			BoxTC = &cData.gTrimesh->BoxTCCache[cData.gTrimesh->BoxTCCache.size() - 1];
			BoxTC->Geom = cData.gCylinder;
			BoxTC->FatCoeff = REAL(1.0);
		}

		// Intersect
		Collider.SetTemporalCoherence(true);
		Collider.Collide(*BoxTC, obbCCylinder, cData.gTrimesh->Data->BVTree, null, &MeshMatrix);
	}
	else
	{
		Collider.SetTemporalCoherence(false);
		//Collider.Collide(dxTriMesh::defaultBoxCache, obbCCylinder, cData.gTrimesh->Data->BVTree, null,&MeshMatrix);
		Collider.Collide(cData.gTrimesh->boxCache, obbCCylinder, cData.gTrimesh->Data->BVTree, null,&MeshMatrix);
	}

	// Retrieve data
	int TriCount = Collider.GetNbTouchedPrimitives();
	const int* Triangles = (const int*)Collider.GetTouchedPrimitives();


	if (TriCount != 0)
	{
		if (cData.gTrimesh->ArrayCallback != null)
		{
			cData.gTrimesh->ArrayCallback(cData.gTrimesh, cData.gCylinder, Triangles, TriCount);
		}

		//int OutTriCount = 0;

		// loop through all intersecting triangles
		for (int i = 0; i < TriCount; i++)
		{
			if(cData.nContacts	>= (cData.iFlags & NUMC_MASK))
			{
				break;
			}

			const int& Triint = Triangles[i];
			if (!Callback(cData.gTrimesh, cData.gCylinder, Triint)) continue;


			dVector3 dv[3];
			FetchTriangle(cData.gTrimesh, Triint, cData.vTrimeshPos, cData.mTrimeshRot, dv);

			// test this triangle
			TestOneTriangleVsCylinder(cData , dv[0],dv[1],dv[2], false);
		}
	}

	return _ProcessLocalContacts(cData);
}
