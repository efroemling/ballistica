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
 *	Cylinder-box collider by Alen Ladavac
 *  Ported to ODE by Nguyen Binh
 */

#include "ode/ode_collision.h"
#include "ode/ode_matrix.h"
#include "ode/ode_rotation.h"
#include "ode/ode_math.h"
#include "ode/ode_collision_util.h"
#include "ode/ode_collision_kernel.h"

static const int MAX_CYLBOX_CLIP_POINTS  = 16;
static const int nCYLINDER_AXIS			 = 2;
// Number of segment of cylinder base circle.
// Must be divisible by 4.
static const int nCYLINDER_SEGMENT		 = 8;

#define MAX_FLOAT	dInfinity

// Data that passed through the collider's functions
typedef struct _sCylinderBoxData
{
	// cylinder parameters
	dMatrix3			mCylinderRot;
	dVector3			vCylinderPos;
	dVector3			vCylinderAxis;
	dReal				fCylinderRadius;
	dReal				fCylinderSize;
	dVector3			avCylinderNormals[nCYLINDER_SEGMENT];
	
	// box parameters

	dMatrix3			mBoxRot;
	dVector3			vBoxPos;
	dVector3			vBoxHalfSize;
	// box vertices array : 8 vertices
	dVector3			avBoxVertices[8];

	// global collider data
	dVector3			vDiff;			
	dVector3			vNormal;
	dReal				fBestDepth;
	dReal				fBestrb;
	dReal				fBestrc;
	int					iBestAxis;

	// contact data
	dVector3			vEp0, vEp1;
	dReal				fDepth0, fDepth1;

	// ODE stuff
	dGeomID				gBox;
	dGeomID				gCylinder;
	dContactGeom*		gContact;
	int					iFlags;
	int					iSkip;
	int					nContacts;
	
} sCylinderBoxData;


// initialize collision data
void _cldInitCylinderBox(sCylinderBoxData& cData) 
{
	// get cylinder position, orientation
	const dReal* pRotCyc = dGeomGetRotation(cData.gCylinder); 
	dMatrix3Copy(pRotCyc,cData.mCylinderRot);

	const dVector3* pPosCyc = (const dVector3*)dGeomGetPosition(cData.gCylinder);
	dVector3Copy(*pPosCyc,cData.vCylinderPos);

	dMat3GetCol(cData.mCylinderRot,nCYLINDER_AXIS,cData.vCylinderAxis);
	
	// get cylinder radius and size
	dGeomCylinderGetParams(cData.gCylinder,&cData.fCylinderRadius,&cData.fCylinderSize);

	// get box position, orientation, size
	const dReal* pRotBox = dGeomGetRotation(cData.gBox);
	dMatrix3Copy(pRotBox,cData.mBoxRot);
	const dVector3* pPosBox  = (const dVector3*)dGeomGetPosition(cData.gBox);
	dVector3Copy(*pPosBox,cData.vBoxPos);

	dGeomBoxGetLengths(cData.gBox, cData.vBoxHalfSize);
	cData.vBoxHalfSize[0] *= REAL(0.5);
	cData.vBoxHalfSize[1] *= REAL(0.5);
	cData.vBoxHalfSize[2] *= REAL(0.5);

	// vertex 0
	cData.avBoxVertices[0][0] = -cData.vBoxHalfSize[0];
	cData.avBoxVertices[0][1] =  cData.vBoxHalfSize[1];
	cData.avBoxVertices[0][2] = -cData.vBoxHalfSize[2];

	// vertex 1
	cData.avBoxVertices[1][0] =  cData.vBoxHalfSize[0];
	cData.avBoxVertices[1][1] =  cData.vBoxHalfSize[1];
	cData.avBoxVertices[1][2] = -cData.vBoxHalfSize[2];

	// vertex 2
	cData.avBoxVertices[2][0] = -cData.vBoxHalfSize[0];
	cData.avBoxVertices[2][1] = -cData.vBoxHalfSize[1];
	cData.avBoxVertices[2][2] = -cData.vBoxHalfSize[2];

	// vertex 3
	cData.avBoxVertices[3][0] =  cData.vBoxHalfSize[0];
	cData.avBoxVertices[3][1] = -cData.vBoxHalfSize[1];
	cData.avBoxVertices[3][2] = -cData.vBoxHalfSize[2];

	// vertex 4
	cData.avBoxVertices[4][0] =  cData.vBoxHalfSize[0];
	cData.avBoxVertices[4][1] =  cData.vBoxHalfSize[1];
	cData.avBoxVertices[4][2] =  cData.vBoxHalfSize[2];

	// vertex 5
	cData.avBoxVertices[5][0] =  cData.vBoxHalfSize[0];
	cData.avBoxVertices[5][1] = -cData.vBoxHalfSize[1];
	cData.avBoxVertices[5][2] =  cData.vBoxHalfSize[2];

	// vertex 6
	cData.avBoxVertices[6][0] = -cData.vBoxHalfSize[0];
	cData.avBoxVertices[6][1] = -cData.vBoxHalfSize[1];
	cData.avBoxVertices[6][2] =  cData.vBoxHalfSize[2];

	// vertex 7
	cData.avBoxVertices[7][0] = -cData.vBoxHalfSize[0];
	cData.avBoxVertices[7][1] =  cData.vBoxHalfSize[1];
	cData.avBoxVertices[7][2] =  cData.vBoxHalfSize[2];

	// temp index
	int i = 0;
	dVector3	vTempBoxVertices[8];
	// transform vertices in absolute space
	for(i=0; i < 8; i++) 
	{
		dMultiplyMat3Vec3(cData.mBoxRot,cData.avBoxVertices[i], vTempBoxVertices[i]);
		dVector3Add(vTempBoxVertices[i], cData.vBoxPos, cData.avBoxVertices[i]);
	}

	// find relative position
	dVector3Subtract(cData.vCylinderPos,cData.vBoxPos,cData.vDiff);
	cData.fBestDepth = MAX_FLOAT;
	cData.vNormal[0] = REAL(0.0);
	cData.vNormal[1] = REAL(0.0);
	cData.vNormal[2] = REAL(0.0);

	// calculate basic angle for nCYLINDER_SEGMENT-gon
	dReal fAngle = M_PI/nCYLINDER_SEGMENT;

	// calculate angle increment
	dReal fAngleIncrement = fAngle * REAL(2.0); 

	// calculate nCYLINDER_SEGMENT-gon points
	for(i = 0; i < nCYLINDER_SEGMENT; i++) 
	{
		cData.avCylinderNormals[i][0] = -dCos(fAngle);
		cData.avCylinderNormals[i][1] = -dSin(fAngle);
		cData.avCylinderNormals[i][2] = 0;

		fAngle += fAngleIncrement;
	}

	cData.fBestrb		= 0;
	cData.fBestrc		= 0;
	cData.iBestAxis		= 0;
	cData.nContacts		= 0;

}

// test for given separating axis
int _cldTestAxis(sCylinderBoxData& cData, dVector3& vInputNormal, int iAxis ) 
{
	// check length of input normal
	dReal fL = dVector3Length(vInputNormal);
	// if not long enough
	if ( fL < 1e-5f ) 
	{
		// do nothing
		return 1;
	}

	// otherwise make it unit for sure
	dNormalize3(vInputNormal);

	// project box and Cylinder on mAxis
	dReal fdot1 = dVector3Dot(cData.vCylinderAxis, vInputNormal);

	dReal frc;

	if (fdot1 > REAL(1.0)) 
	{
		fdot1 = REAL(1.0);
		frc = dFabs(cData.fCylinderSize*REAL(0.5));
	}

	// project box and capsule on iAxis
	frc = dFabs( fdot1 * (cData.fCylinderSize*REAL(0.5))) + cData.fCylinderRadius * dSqrt(REAL(1.0)-(fdot1*fdot1));

	dVector3	vTemp1;
	dReal frb = REAL(0.0);

	dMat3GetCol(cData.mBoxRot,0,vTemp1);
	frb = dFabs(dVector3Dot(vTemp1,vInputNormal))*cData.vBoxHalfSize[0];

	dMat3GetCol(cData.mBoxRot,1,vTemp1);
	frb += dFabs(dVector3Dot(vTemp1,vInputNormal))*cData.vBoxHalfSize[1];

	dMat3GetCol(cData.mBoxRot,2,vTemp1);
	frb += dFabs(dVector3Dot(vTemp1,vInputNormal))*cData.vBoxHalfSize[2];
	
	// project their distance on separating axis
	dReal fd  = dVector3Dot(cData.vDiff,vInputNormal);

	// if they do not overlap exit, we have no intersection
	if ( dFabs(fd) > frc+frb )
	{ 
		return 0; 
	} 

	// get depth
	dReal fDepth = - dFabs(fd) + (frc+frb);

	// get maximum depth
	if ( fDepth < cData.fBestDepth ) 
	{
		cData.fBestDepth = fDepth;
		dVector3Copy(vInputNormal,cData.vNormal);
		cData.iBestAxis  = iAxis;
		cData.fBestrb    = frb;
		cData.fBestrc    = frc;

		// flip normal if interval is wrong faced
		if (fd > 0) 
		{ 
			dVector3Inv(cData.vNormal);
		}
	}

	return 1;
}


// check for separation between box edge and cylinder circle edge
int _cldTestEdgeCircleAxis( sCylinderBoxData& cData,
							const dVector3 &vCenterPoint, 
							const dVector3 &vVx0, const dVector3 &vVx1, 
							int iAxis ) 
{
	// calculate direction of edge
	dVector3 vDirEdge;
	dVector3Subtract(vVx1,vVx0,vDirEdge);
	dNormalize3(vDirEdge);
	// starting point of edge 
	dVector3 vEStart;
	dVector3Copy(vVx0,vEStart);;

	// calculate angle cosine between cylinder axis and edge
	dReal fdot2 = dVector3Dot (vDirEdge,cData.vCylinderAxis);

	// if edge is perpendicular to cylinder axis
	if(dFabs(fdot2) < 1e-5f) 
	{
		// this can't be separating axis, because edge is parallel to circle plane
		return 1;
	}

	// find point of intersection between edge line and circle plane
	dVector3 vTemp1;
	dVector3Subtract(vCenterPoint,vEStart,vTemp1);
	dReal fdot1 = dVector3Dot(vTemp1,cData.vCylinderAxis);
	dVector3 vpnt;
	vpnt[0]= vEStart[0] + vDirEdge[0] * (fdot1/fdot2);
	vpnt[1]= vEStart[1] + vDirEdge[1] * (fdot1/fdot2);
	vpnt[2]= vEStart[2] + vDirEdge[2] * (fdot1/fdot2);

	// find tangent vector on circle with same center (vCenterPoint) that
	// touches point of intersection (vpnt)
	dVector3 vTangent;
	dVector3Subtract(vCenterPoint,vpnt,vTemp1);
	dVector3Cross(vTemp1,cData.vCylinderAxis,vTangent);
	
	// find vector orthogonal both to tangent and edge direction
	dVector3 vAxis;
	dVector3Cross(vTangent,vDirEdge,vAxis);

	// use that vector as separating axis
	return _cldTestAxis( cData, vAxis, iAxis );
}

// Test separating axis for collision
int _cldTestSeparatingAxes(sCylinderBoxData& cData) 
{
	// reset best axis
	cData.fBestDepth = MAX_FLOAT;
	cData.iBestAxis = 0;
	cData.fBestrb = 0;
	cData.fBestrc = 0;
	cData.nContacts = 0;

	dVector3  vAxis = {REAL(0.0),REAL(0.0),REAL(0.0),REAL(0.0)};

	// Epsilon value for checking axis vector length 
	const dReal fEpsilon = 1e-6f;

	// axis A0
	dMat3GetCol(cData.mBoxRot, 0 , vAxis);
	if (!_cldTestAxis( cData, vAxis, 1 )) 
	{
		return 0;
	}

	// axis A1
	dMat3GetCol(cData.mBoxRot, 1 , vAxis);
	if (!_cldTestAxis( cData, vAxis, 2 )) 
	{
		return 0;
	}

	// axis A2
	dMat3GetCol(cData.mBoxRot, 2 , vAxis);
	if (!_cldTestAxis( cData, vAxis, 3 )) 
	{
		return 0;
	}

	// axis C - Cylinder Axis
	//vAxis = vCylinderAxis;
	dVector3Copy(cData.vCylinderAxis , vAxis);
	if (!_cldTestAxis( cData, vAxis, 4 )) 
	{
		return 0;
	}

	// axis CxA0
	//vAxis = ( vCylinderAxis cross mthGetColM33f( mBoxRot, 0 ));
	dVector3CrossMat3Col(cData.mBoxRot, 0 ,cData.vCylinderAxis, vAxis);
	if(dVector3Length2( vAxis ) > fEpsilon ) 
	{
		if (!_cldTestAxis( cData, vAxis, 5 ))
		{
			return 0;
		}
	}

	// axis CxA1
	//vAxis = ( vCylinderAxis cross mthGetColM33f( mBoxRot, 1 ));
	dVector3CrossMat3Col(cData.mBoxRot, 1 ,cData.vCylinderAxis, vAxis);
	if(dVector3Length2( vAxis ) > fEpsilon ) 
	{
		if (!_cldTestAxis( cData, vAxis, 6 )) 
		{
			return 0;
		}
	}

	// axis CxA2
	//vAxis = ( vCylinderAxis cross mthGetColM33f( mBoxRot, 2 ));
	dVector3CrossMat3Col(cData.mBoxRot, 2 ,cData.vCylinderAxis, vAxis);
	if(dVector3Length2( vAxis ) > fEpsilon ) 
	{
		if (!_cldTestAxis( cData, vAxis, 7 ))
		{
			return 0;
		}
	}

	int i = 0;
	dVector3	vTemp1;
	dVector3	vTemp2;
	// here we check box's vertices axis
	for(i=0; i< 8; i++) 
	{
		//vAxis = ( vCylinderAxis cross (cData.avBoxVertices[i] - vCylinderPos));
		dVector3Subtract(cData.avBoxVertices[i],cData.vCylinderPos,vTemp1);
		dVector3Cross(cData.vCylinderAxis,vTemp1,vTemp2);
		//vAxis = ( vCylinderAxis cross vAxis );
		dVector3Cross(cData.vCylinderAxis,vTemp2,vAxis);
		if(dVector3Length2( vAxis ) > fEpsilon ) 
		{
			if (!_cldTestAxis( cData, vAxis, 8 + i ))
			{
				return 0;
			}
		}
	}

	// ************************************
	// this is defined for first 12 axes
	// normal of plane that contains top circle of cylinder
	// center of top circle of cylinder
	dVector3 vcc;
	vcc[0] = (cData.vCylinderPos)[0] + cData.vCylinderAxis[0]*(cData.fCylinderSize*REAL(0.5));
	vcc[1] = (cData.vCylinderPos)[1] + cData.vCylinderAxis[1]*(cData.fCylinderSize*REAL(0.5));
	vcc[2] = (cData.vCylinderPos)[2] + cData.vCylinderAxis[2]*(cData.fCylinderSize*REAL(0.5));
	// ************************************

	if (!_cldTestEdgeCircleAxis( cData, vcc, cData.avBoxVertices[1], cData.avBoxVertices[0], 16)) 
	{
		return 0;
	}

	if (!_cldTestEdgeCircleAxis( cData, vcc, cData.avBoxVertices[1], cData.avBoxVertices[3], 17)) 
	{
		return 0;
	}

	if (!_cldTestEdgeCircleAxis( cData, vcc, cData.avBoxVertices[2], cData.avBoxVertices[3], 18))
	{
		return 0;
	}

	if (!_cldTestEdgeCircleAxis( cData, vcc, cData.avBoxVertices[2], cData.avBoxVertices[0], 19)) 
	{
		return 0;
	}


	if (!_cldTestEdgeCircleAxis( cData, vcc, cData.avBoxVertices[4], cData.avBoxVertices[1], 20))
	{
		return 0;
	}

	if (!_cldTestEdgeCircleAxis( cData, vcc, cData.avBoxVertices[4], cData.avBoxVertices[7], 21))
	{
		return 0;
	}

	if (!_cldTestEdgeCircleAxis( cData, vcc, cData.avBoxVertices[0], cData.avBoxVertices[7], 22)) 
	{
		return 0;
	}

	if (!_cldTestEdgeCircleAxis( cData, vcc, cData.avBoxVertices[5], cData.avBoxVertices[3], 23)) 
	{
		return 0;
	}

	if (!_cldTestEdgeCircleAxis( cData, vcc, cData.avBoxVertices[5], cData.avBoxVertices[6], 24)) 
	{
		return 0;
	}

	if (!_cldTestEdgeCircleAxis( cData, vcc, cData.avBoxVertices[2], cData.avBoxVertices[6], 25)) 
	{
		return 0;
	}

	if (!_cldTestEdgeCircleAxis( cData, vcc, cData.avBoxVertices[4], cData.avBoxVertices[5], 26)) 
	{
		return 0;
	}

	if (!_cldTestEdgeCircleAxis( cData, vcc, cData.avBoxVertices[6], cData.avBoxVertices[7], 27)) 
	{
		return 0;
	}

	// ************************************
	// this is defined for second 12 axes
	// normal of plane that contains bottom circle of cylinder
	// center of bottom circle of cylinder
	//	vcc = vCylinderPos - vCylinderAxis*(fCylinderSize*REAL(0.5));
	vcc[0] = (cData.vCylinderPos)[0] - cData.vCylinderAxis[0]*(cData.fCylinderSize*REAL(0.5));
	vcc[1] = (cData.vCylinderPos)[1] - cData.vCylinderAxis[1]*(cData.fCylinderSize*REAL(0.5));
	vcc[2] = (cData.vCylinderPos)[2] - cData.vCylinderAxis[2]*(cData.fCylinderSize*REAL(0.5));
	// ************************************

	if (!_cldTestEdgeCircleAxis( cData, vcc, cData.avBoxVertices[1], cData.avBoxVertices[0], 28)) 
	{
		return 0;
	}

	if (!_cldTestEdgeCircleAxis( cData, vcc, cData.avBoxVertices[1], cData.avBoxVertices[3], 29)) 
	{
		return 0;
	}

	if (!_cldTestEdgeCircleAxis( cData, vcc, cData.avBoxVertices[2], cData.avBoxVertices[3], 30)) 
	{
		return 0;
	}

	if (!_cldTestEdgeCircleAxis( cData, vcc, cData.avBoxVertices[2], cData.avBoxVertices[0], 31)) 
	{
		return 0;
	}

	if (!_cldTestEdgeCircleAxis( cData, vcc, cData.avBoxVertices[4], cData.avBoxVertices[1], 32)) 
	{
		return 0;
	}

	if (!_cldTestEdgeCircleAxis( cData, vcc, cData.avBoxVertices[4], cData.avBoxVertices[7], 33)) 
	{
		return 0;
	}

	if (!_cldTestEdgeCircleAxis( cData, vcc, cData.avBoxVertices[0], cData.avBoxVertices[7], 34)) 
	{
		return 0;
	}

	if (!_cldTestEdgeCircleAxis( cData, vcc, cData.avBoxVertices[5], cData.avBoxVertices[3], 35)) 
	{
		return 0;
	}

	if (!_cldTestEdgeCircleAxis( cData, vcc, cData.avBoxVertices[5], cData.avBoxVertices[6], 36)) 
	{
		return 0;
	}

	if (!_cldTestEdgeCircleAxis( cData, vcc, cData.avBoxVertices[2], cData.avBoxVertices[6], 37)) 
	{
		return 0;
	}

	if (!_cldTestEdgeCircleAxis( cData, vcc, cData.avBoxVertices[4], cData.avBoxVertices[5], 38)) 
	{
		return 0;
	}

	if (!_cldTestEdgeCircleAxis( cData, vcc, cData.avBoxVertices[6], cData.avBoxVertices[7], 39)) 
	{
		return 0;
	}

	return 1;
}

int _cldClipCylinderToBox(sCylinderBoxData& cData)
{

	// calculate that vector perpendicular to cylinder axis which closes lowest angle with collision normal
	dVector3 vN;
	dReal fTemp1 = dVector3Dot(cData.vCylinderAxis,cData.vNormal);
	vN[0]	=	cData.vNormal[0] - cData.vCylinderAxis[0]*fTemp1;
	vN[1]	=	cData.vNormal[1] - cData.vCylinderAxis[1]*fTemp1;
	vN[2]	=	cData.vNormal[2] - cData.vCylinderAxis[2]*fTemp1;

	// normalize that vector
	dNormalize3(vN);

	// translate cylinder end points by the vector
	dVector3 vCposTrans;
	vCposTrans[0] = cData.vCylinderPos[0] + vN[0] * cData.fCylinderRadius;
	vCposTrans[1] = cData.vCylinderPos[1] + vN[1] * cData.fCylinderRadius;
	vCposTrans[2] = cData.vCylinderPos[2] + vN[2] * cData.fCylinderRadius;

	cData.vEp0[0]  = vCposTrans[0] + cData.vCylinderAxis[0]*(cData.fCylinderSize*REAL(0.5));
	cData.vEp0[1]  = vCposTrans[1] + cData.vCylinderAxis[1]*(cData.fCylinderSize*REAL(0.5));
	cData.vEp0[2]  = vCposTrans[2] + cData.vCylinderAxis[2]*(cData.fCylinderSize*REAL(0.5));

	cData.vEp1[0]  = vCposTrans[0] - cData.vCylinderAxis[0]*(cData.fCylinderSize*REAL(0.5));
	cData.vEp1[1]  = vCposTrans[1] - cData.vCylinderAxis[1]*(cData.fCylinderSize*REAL(0.5));
	cData.vEp1[2]  = vCposTrans[2] - cData.vCylinderAxis[2]*(cData.fCylinderSize*REAL(0.5));

	// transform edge points in box space
	cData.vEp0[0] -= cData.vBoxPos[0];
	cData.vEp0[1] -= cData.vBoxPos[1];
	cData.vEp0[2] -= cData.vBoxPos[2];

	cData.vEp1[0] -= cData.vBoxPos[0];
	cData.vEp1[1] -= cData.vBoxPos[1];
	cData.vEp1[2] -= cData.vBoxPos[2];

	dVector3 vTemp1;
	// clip the edge to box 
	dVector4 plPlane;
	// plane 0 +x
	dMat3GetCol(cData.mBoxRot,0,vTemp1);
	dConstructPlane(vTemp1,cData.vBoxHalfSize[0],plPlane);
	if(!dClipEdgeToPlane( cData.vEp0, cData.vEp1, plPlane )) 
	{ 
		return 0; 
	}

	// plane 1 +y
	dMat3GetCol(cData.mBoxRot,1,vTemp1);
	dConstructPlane(vTemp1,cData.vBoxHalfSize[1],plPlane);
	if(!dClipEdgeToPlane( cData.vEp0, cData.vEp1, plPlane )) 
	{ 
		return 0; 
	}

	// plane 2 +z
	dMat3GetCol(cData.mBoxRot,2,vTemp1);
	dConstructPlane(vTemp1,cData.vBoxHalfSize[2],plPlane);
	if(!dClipEdgeToPlane( cData.vEp0, cData.vEp1, plPlane )) 
	{ 
		return 0; 
	}

	// plane 3 -x
	dMat3GetCol(cData.mBoxRot,0,vTemp1);
	dVector3Inv(vTemp1);
	dConstructPlane(vTemp1,cData.vBoxHalfSize[0],plPlane);
	if(!dClipEdgeToPlane( cData.vEp0, cData.vEp1, plPlane )) 
	{ 
		return 0; 
	}

	// plane 4 -y
	dMat3GetCol(cData.mBoxRot,1,vTemp1);
	dVector3Inv(vTemp1);
	dConstructPlane(vTemp1,cData.vBoxHalfSize[1],plPlane);
	if(!dClipEdgeToPlane( cData.vEp0, cData.vEp1, plPlane )) 
	{ 
		return 0; 
	}

	// plane 5 -z
	dMat3GetCol(cData.mBoxRot,2,vTemp1);
	dVector3Inv(vTemp1);
	dConstructPlane(vTemp1,cData.vBoxHalfSize[2],plPlane);
	if(!dClipEdgeToPlane( cData.vEp0, cData.vEp1, plPlane )) 
	{ 
		return 0; 
	}

	// calculate depths for both contact points
	cData.fDepth0 = cData.fBestrb + dVector3Dot(cData.vEp0, cData.vNormal);
	cData.fDepth1 = cData.fBestrb + dVector3Dot(cData.vEp1, cData.vNormal);

	// clamp depths to 0
	if(cData.fDepth0<0) 
	{
		cData.fDepth0 = REAL(0.0);
	}

	if(cData.fDepth1<0) 
	{
		cData.fDepth1 = REAL(0.0);
	}

	// back transform edge points from box to absolute space
	cData.vEp0[0] += cData.vBoxPos[0];
	cData.vEp0[1] += cData.vBoxPos[1];
	cData.vEp0[2] += cData.vBoxPos[2];

	cData.vEp1[0] += cData.vBoxPos[0];
	cData.vEp1[1] += cData.vBoxPos[1];
	cData.vEp1[2] += cData.vBoxPos[2];

	if (cData.nContacts < (cData.iFlags & NUMC_MASK)){
		dContactGeom* Contact0 = SAFECONTACT(cData.iFlags, cData.gContact, cData.nContacts, cData.iSkip);
		Contact0->depth = cData.fDepth0;
		dVector3Copy(cData.vNormal,Contact0->normal);
		dVector3Copy(cData.vEp0,Contact0->pos);
		Contact0->g1 = cData.gCylinder;
		Contact0->g2 = cData.gBox;
		dVector3Inv(Contact0->normal);
		cData.nContacts++;
	}
	
	if (cData.nContacts < (cData.iFlags & NUMC_MASK)){
		dContactGeom* Contact1 = SAFECONTACT(cData.iFlags, cData.gContact, cData.nContacts, cData.iSkip);
		Contact1->depth = cData.fDepth1;
		dVector3Copy(cData.vNormal,Contact1->normal);
		dVector3Copy(cData.vEp1,Contact1->pos);
		Contact1->g1 = cData.gCylinder;
		Contact1->g2 = cData.gBox;
		dVector3Inv(Contact1->normal);
		cData.nContacts++;
	}

	return 1;
}


void _cldClipBoxToCylinder(sCylinderBoxData& cData ) 
{
	dVector3 vCylinderCirclePos, vCylinderCircleNormal_Rel;
	// check which circle from cylinder we take for clipping
	if ( dVector3Dot(cData.vCylinderAxis, cData.vNormal) > REAL(0.0) ) 
	{
		// get top circle
		vCylinderCirclePos[0] = cData.vCylinderPos[0] + cData.vCylinderAxis[0]*(cData.fCylinderSize*REAL(0.5));
		vCylinderCirclePos[1] = cData.vCylinderPos[1] + cData.vCylinderAxis[1]*(cData.fCylinderSize*REAL(0.5));
		vCylinderCirclePos[2] = cData.vCylinderPos[2] + cData.vCylinderAxis[2]*(cData.fCylinderSize*REAL(0.5));

		vCylinderCircleNormal_Rel[0] = REAL(0.0);
		vCylinderCircleNormal_Rel[1] = REAL(0.0);
		vCylinderCircleNormal_Rel[2] = REAL(0.0);
		vCylinderCircleNormal_Rel[nCYLINDER_AXIS] = REAL(-1.0);
	}
	else 
	{
		// get bottom circle
		vCylinderCirclePos[0] = cData.vCylinderPos[0] - cData.vCylinderAxis[0]*(cData.fCylinderSize*REAL(0.5));
		vCylinderCirclePos[1] = cData.vCylinderPos[1] - cData.vCylinderAxis[1]*(cData.fCylinderSize*REAL(0.5));
		vCylinderCirclePos[2] = cData.vCylinderPos[2] - cData.vCylinderAxis[2]*(cData.fCylinderSize*REAL(0.5));

		vCylinderCircleNormal_Rel[0] = REAL(0.0);
		vCylinderCircleNormal_Rel[1] = REAL(0.0);
		vCylinderCircleNormal_Rel[2] = REAL(0.0);
		vCylinderCircleNormal_Rel[nCYLINDER_AXIS] = REAL(1.0);
	}

	// vNr is normal in Box frame, pointing from Cylinder to Box
	dVector3 vNr;
	dMatrix3 mBoxInv;

	// Find a way to use quaternion
	dMatrix3Inv(cData.mBoxRot,mBoxInv);
	dMultiplyMat3Vec3(mBoxInv,cData.vNormal,vNr);

	dVector3 vAbsNormal;

	vAbsNormal[0] = dFabs( vNr[0] );
	vAbsNormal[1] = dFabs( vNr[1] );
	vAbsNormal[2] = dFabs( vNr[2] );

	// find which face in box is closest to cylinder
	int iB0, iB1, iB2;

	// Different from Croteam's code
	if (vAbsNormal[1] > vAbsNormal[0]) 
	{
		// 1 > 0
		if (vAbsNormal[0]> vAbsNormal[2]) 
		{
			// 0 > 2 -> 1 > 0 >2
			iB0 = 1; iB1 = 0; iB2 = 2;
		} 
		else 
		{
			// 2 > 0-> Must compare 1 and 2
			if (vAbsNormal[1] > vAbsNormal[2])
			{
				// 1 > 2 -> 1 > 2 > 0
				iB0 = 1; iB1 = 2; iB2 = 0;
			}
			else
			{
				// 2 > 1 -> 2 > 1 > 0;
				iB0 = 2; iB1 = 1; iB2 = 0;
			}			
		}
	} 
	else 
	{
		// 0 > 1
		if (vAbsNormal[1] > vAbsNormal[2]) 
		{
			// 1 > 2 -> 0 > 1 > 2
			iB0 = 0; iB1 = 1; iB2 = 2;
		}
		else 
		{
			// 2 > 1 -> Must compare 0 and 2
			if (vAbsNormal[0] > vAbsNormal[2])
			{
				// 0 > 2 -> 0 > 2 > 1;
				iB0 = 0; iB1 = 2; iB2 = 1;
			}
			else
			{
				// 2 > 0 -> 2 > 0 > 1;
				iB0 = 2; iB1 = 0; iB2 = 1;
			}		
		}
	}

	dVector3 vCenter;
	// find center of box polygon
	dVector3 vTemp;
	if (vNr[iB0] > 0) 
	{
		dMat3GetCol(cData.mBoxRot,iB0,vTemp);
		vCenter[0] = cData.vBoxPos[0] - cData.vBoxHalfSize[iB0]*vTemp[0];
		vCenter[1] = cData.vBoxPos[1] - cData.vBoxHalfSize[iB0]*vTemp[1];
		vCenter[2] = cData.vBoxPos[2] - cData.vBoxHalfSize[iB0]*vTemp[2];
	}
	else 
	{
		dMat3GetCol(cData.mBoxRot,iB0,vTemp);
		vCenter[0] = cData.vBoxPos[0] + cData.vBoxHalfSize[iB0]*vTemp[0];
		vCenter[1] = cData.vBoxPos[1] + cData.vBoxHalfSize[iB0]*vTemp[1];
		vCenter[2] = cData.vBoxPos[2] + cData.vBoxHalfSize[iB0]*vTemp[2];
	}

	// find the vertices of box polygon
	dVector3 avPoints[4];
	dVector3 avTempArray1[MAX_CYLBOX_CLIP_POINTS];
	dVector3 avTempArray2[MAX_CYLBOX_CLIP_POINTS];

	int i=0;
	for(i=0; i<MAX_CYLBOX_CLIP_POINTS; i++) 
	{
		avTempArray1[i][0] = REAL(0.0);
		avTempArray1[i][1] = REAL(0.0);
		avTempArray1[i][2] = REAL(0.0);

		avTempArray2[i][0] = REAL(0.0);
		avTempArray2[i][1] = REAL(0.0);
		avTempArray2[i][2] = REAL(0.0);
	}

	dVector3 vAxis1, vAxis2;

	dMat3GetCol(cData.mBoxRot,iB1,vAxis1);
	dMat3GetCol(cData.mBoxRot,iB2,vAxis2);

	avPoints[0][0] = vCenter[0] + cData.vBoxHalfSize[iB1] * vAxis1[0] - cData.vBoxHalfSize[iB2] * vAxis2[0];
	avPoints[0][1] = vCenter[1] + cData.vBoxHalfSize[iB1] * vAxis1[1] - cData.vBoxHalfSize[iB2] * vAxis2[1];
	avPoints[0][2] = vCenter[2] + cData.vBoxHalfSize[iB1] * vAxis1[2] - cData.vBoxHalfSize[iB2] * vAxis2[2];

	avPoints[1][0] = vCenter[0] - cData.vBoxHalfSize[iB1] * vAxis1[0] - cData.vBoxHalfSize[iB2] * vAxis2[0];
	avPoints[1][1] = vCenter[1] - cData.vBoxHalfSize[iB1] * vAxis1[1] - cData.vBoxHalfSize[iB2] * vAxis2[1];
	avPoints[1][2] = vCenter[2] - cData.vBoxHalfSize[iB1] * vAxis1[2] - cData.vBoxHalfSize[iB2] * vAxis2[2];

	avPoints[2][0] = vCenter[0] - cData.vBoxHalfSize[iB1] * vAxis1[0] + cData.vBoxHalfSize[iB2] * vAxis2[0];
	avPoints[2][1] = vCenter[1] - cData.vBoxHalfSize[iB1] * vAxis1[1] + cData.vBoxHalfSize[iB2] * vAxis2[1];
	avPoints[2][2] = vCenter[2] - cData.vBoxHalfSize[iB1] * vAxis1[2] + cData.vBoxHalfSize[iB2] * vAxis2[2];

	avPoints[3][0] = vCenter[0] + cData.vBoxHalfSize[iB1] * vAxis1[0] + cData.vBoxHalfSize[iB2] * vAxis2[0];
	avPoints[3][1] = vCenter[1] + cData.vBoxHalfSize[iB1] * vAxis1[1] + cData.vBoxHalfSize[iB2] * vAxis2[1];
	avPoints[3][2] = vCenter[2] + cData.vBoxHalfSize[iB1] * vAxis1[2] + cData.vBoxHalfSize[iB2] * vAxis2[2];

	// transform box points to space of cylinder circle
	dMatrix3 mCylinderInv;
	dMatrix3Inv(cData.mCylinderRot,mCylinderInv);

	for(i=0; i<4; i++) 
	{
		dVector3Subtract(avPoints[i],vCylinderCirclePos,vTemp);
		dMultiplyMat3Vec3(mCylinderInv,vTemp,avPoints[i]);
	}

	int iTmpCounter1 = 0;
	int iTmpCounter2 = 0;
	dVector4 plPlane;

	// plane of cylinder that contains circle for intersection
	dConstructPlane(vCylinderCircleNormal_Rel,REAL(0.0),plPlane);
	dClipPolyToPlane(avPoints, 4, avTempArray1, iTmpCounter1, plPlane);


	// Body of base circle of Cylinder
	int nCircleSegment = 0;
	for (nCircleSegment = 0; nCircleSegment < nCYLINDER_SEGMENT; nCircleSegment++)
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

		dIASSERT( iTmpCounter1 >= 0 && iTmpCounter1 <= MAX_CYLBOX_CLIP_POINTS );
		dIASSERT( iTmpCounter2 >= 0 && iTmpCounter2 <= MAX_CYLBOX_CLIP_POINTS );
	}
	
	// back transform clipped points to absolute space
	dReal ftmpdot;	
	dReal fTempDepth;
	dVector3 vPoint;

	if (nCircleSegment %2)
	{
		for( i=0; i<iTmpCounter2; i++)
		{
			dMULTIPLY0_331(vPoint,cData.mCylinderRot,avTempArray2[i]);
			vPoint[0] += vCylinderCirclePos[0];
			vPoint[1] += vCylinderCirclePos[1];
			vPoint[2] += vCylinderCirclePos[2];

			dVector3Subtract(vPoint,cData.vCylinderPos,vTemp);
			ftmpdot	 = dVector3Dot(vTemp, cData.vNormal);
			fTempDepth = cData.fBestrc - ftmpdot;
			// Depth must be positive
			if (fTempDepth > REAL(0.0))
			{
				// generate contacts
				if (cData.nContacts < (cData.iFlags & NUMC_MASK)){
					dContactGeom* Contact0 = SAFECONTACT(cData.iFlags, cData.gContact, cData.nContacts, cData.iSkip);
					Contact0->depth = fTempDepth;
					dVector3Copy(cData.vNormal,Contact0->normal);
					dVector3Copy(vPoint,Contact0->pos);
					Contact0->g1 = cData.gCylinder;
					Contact0->g2 = cData.gBox;
					dVector3Inv(Contact0->normal);
					cData.nContacts++;
				}
			}
		}
	}
	else
	{
		for( i=0; i<iTmpCounter1; i++)
		{
			dMULTIPLY0_331(vPoint,cData.mCylinderRot,avTempArray1[i]);
			vPoint[0] += vCylinderCirclePos[0];
			vPoint[1] += vCylinderCirclePos[1];
			vPoint[2] += vCylinderCirclePos[2];

			dVector3Subtract(vPoint,cData.vCylinderPos,vTemp);
			ftmpdot	 = dVector3Dot(vTemp, cData.vNormal);
			fTempDepth = cData.fBestrc - ftmpdot;
			// Depth must be positive
			if (fTempDepth > REAL(0.0))
			{
				// generate contacts
				if (cData.nContacts < (cData.iFlags & NUMC_MASK)){
					dContactGeom* Contact0 = SAFECONTACT(cData.iFlags, cData.gContact, cData.nContacts, cData.iSkip);
					Contact0->depth = fTempDepth;
					dVector3Copy(cData.vNormal,Contact0->normal);
					dVector3Copy(vPoint,Contact0->pos);
					Contact0->g1 = cData.gCylinder;
					Contact0->g2 = cData.gBox;
					dVector3Inv(Contact0->normal);
					cData.nContacts++;
				}
			}
		}
	}
}


// Cylinder - Box by CroTeam
// Ported by Nguyen Binh
int dCollideCylinderBox(dxGeom *o1, dxGeom *o2, int flags, dContactGeom *contact, int skip)
{
	sCylinderBoxData	cData;

	// Assign ODE stuff
	cData.gCylinder = o1;
	cData.gBox		= o2;
	cData.iFlags	= flags;
	cData.iSkip		= skip;
	cData.gContact	= contact;

	// initialize collider
	_cldInitCylinderBox( cData );

	// do intersection test and find best separating axis
	if(!_cldTestSeparatingAxes( cData ) ) 
	{
		// if not found do nothing
		return 0;
	}

	// if best separation axis is not found
	if ( cData.iBestAxis == 0 ) 
	{
		// this should not happen (we should already exit in that case)
		dIASSERT(0);
		// do nothing
		return 0;
	}

	dReal fdot = dVector3Dot(cData.vNormal,cData.vCylinderAxis);
	// choose which clipping method are we going to apply
	if (dFabs(fdot) < REAL(0.9) ) 
	{
		// clip cylinder over box
		if(!_cldClipCylinderToBox(cData)) 
		{
			return 0;
		}
	} 
	else 
	{
		_cldClipBoxToCylinder(cData);  
	}

	return cData.nContacts;
}
