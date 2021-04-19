// TriMesh vs Plane.
//
// CURRENT STATE:
//	- Meshes collide with planes, but require a large number of contacts.
//	- Have simple contact reduction (basically takes the contacts with the greatest depth).
// TODO LIST:
//	- Reduce the number of contacts better.
//
//-James Dolan.

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

#define REDUCE_CONTACTS 1

int dCollideTPL(dxGeom* gmesh, dxGeom* gplane, int Flags, dContactGeom* Contacts, int Stride)
{
	//printf("eep\n");
	int				ret = 0;
	dxTriMesh		*pTriMesh		= (dxTriMesh *) gmesh;
	dReal			planeEq[4];
    Matrix4x4		WMat;
    const dVector3	&TLPosition		= *(const dVector3*)dGeomGetPosition(pTriMesh);
	const dMatrix3	&TLRotation		= *(const dMatrix3*)dGeomGetRotation(pTriMesh);
	PlanesCache		planeCache;
	dxBody			*pTriMeshBody	= pTriMesh->body;

	if(!pTriMeshBody)
		return ret;

  PlanesCollider &planeCollider{*pTriMesh->_PlanesCollider};

	dGeomPlaneGetParams(gplane, planeEq);

	planeCollider.Collide(planeCache, (Plane *)planeEq, 1, pTriMesh->Data->BVTree, &MakeMatrix(TLPosition, TLRotation, WMat));

	int iTriCount = planeCollider.GetNbTouchedPrimitives();

	if(iTriCount > 0)
	{
		const int *pIndices = (const int*)planeCollider.GetTouchedPrimitives();
		if(pTriMesh->ArrayCallback)
		{
			pTriMesh->ArrayCallback(pTriMesh, gplane, pIndices, iTriCount);
		}
		int iOutContactCount = 0;
		int iMaxContactCount = (Flags & 0xffff);
		for(int i=0; i<iTriCount; i++)
		{
			dContactGeom tNewContact;
			int iTriIndex = pIndices[i];
			dVector3	dv[3];
			FetchTriangle(pTriMesh, iTriIndex, TLPosition, TLRotation, dv);

			tNewContact.normal[0] = planeEq[0];
			tNewContact.normal[1] = planeEq[1];
			tNewContact.normal[2] = planeEq[2];
			tNewContact.normal[3] = 0;

			dNormalize3(tNewContact.normal);

			tNewContact.g1 = gmesh;
			tNewContact.g2 = gplane;

			tNewContact.depth = 0.0f;
			for(int j=0; j<3; j++)
			{
				dReal fDepth = dv[j][0]*planeEq[0] + dv[j][1]*planeEq[1] + dv[j][2]*planeEq[2] + planeEq[3];
				if(fDepth < tNewContact.depth)
				{
					tNewContact.depth = fDepth;
					for(int k=0; k<3; k++)
						tNewContact.pos[k] = dv[j][k];
				}
			}
			tNewContact.depth *= -1;

			if(tNewContact.depth > 0)
			{
				if(iOutContactCount < iMaxContactCount)
				{
					// Just add the contact.
					dContactGeom *pContact = SAFECONTACT(Flags, Contacts, iOutContactCount, Stride);
					*pContact = tNewContact;
					iOutContactCount++;
				}
				else
				{
					#if REDUCE_CONTACTS
					// Replace the contact with the shortest depth
					// assuming our depth is greater.
					dContactGeom *pContact = SAFECONTACT(Flags, Contacts, 0, Stride);
					for(int j=1; j<iOutContactCount; j++)
					{
						dContactGeom *pTemp = SAFECONTACT(Flags, Contacts, j, Stride);
						if(pTemp->depth < pContact->depth)
						{
							pContact = pTemp;
						}
					}
					if(pContact->depth < tNewContact.depth)
					{
						*pContact = tNewContact;
					}
					#else
					break;
					#endif
				}
			}
		}
		ret = iOutContactCount;
	}

	return ret;
}
