#include "ode/ode_collision.h"
#include "ode/ode_matrix.h"
#include "ode/ode_rotation.h"
#include "ode/ode_math.h"
#include "ode/ode_collision_util.h"

#define SQRT3_2 ((dReal)0.86602540378443864676)
#define dLENGTH(a) (dSqrt( ((a)[0])*((a)[0]) + ((a)[1])*((a)[1]) + ((a)[2])*((a)[2]) ));
#define dOPC(a,op,b,c) \
  (a)[0] = ((b)[0]) op (c); \
  (a)[1] = ((b)[1]) op (c); \
  (a)[2] = ((b)[2]) op (c);
#define dOPE(a,op,b) \
  (a)[0] op ((b)[0]); \
  (a)[1] op ((b)[1]); \
  (a)[2] op ((b)[2]);
#define dOP(a,op,b,c) \
  (a)[0] = ((b)[0]) op ((c)[0]); \
  (a)[1] = ((b)[1]) op ((c)[1]); \
  (a)[2] = ((b)[2]) op ((c)[2]);


/*
 *  There are five cases: no collision, one-point collision when one 
 edge
 *  circle intersects the plane, two-point collision when both edge 
 circles
 *  intersect the plane, three-point collision when the two edge 
 circles are
 *  on opposite sides of the plane, and deep collision when the center 
 of
 *  the cylinder has penetrated the plane (ugh).  The contact normal is
 *  always perpendicular to the plane.
 */

static void generatePlaneContact(dxGeom *geom, dxGeom *plane,
											dContactGeom *contact, int skip,
											dVector4 pparams, dVector3 point) {
	dContactGeom *c = CONTACT(contact,skip);
	dReal depth = -dDOT(pparams,point);
	c->pos[0] = point[0] + depth*pparams[0];
	c->pos[1] = point[1] + depth*pparams[1];
	c->pos[2] = point[2] + depth*pparams[2];
	c->normal[0] = pparams[0];
	c->normal[1] = pparams[1];
	c->normal[2] = pparams[2];
	c->depth = depth;
	c->g1 = geom;
	c->g2 = plane;
}

int dCollideCylinderPlane(dxGeom *o1, dxGeom *o2, int flags,
								  dContactGeom *contact, int skip)
{
	int maxContacts = flags&0xFFFF, numContacts = 0;
	dReal radius, half_length;
	dGeomCylinderGetParams( o1, &radius, &half_length );
	half_length /= 2;
	const dReal *pos = dGeomGetPosition( o1 );
	const dReal *rot = dGeomGetRotation( o1 );

	dVector4 pparams;
	dGeomPlaneGetParams( o2, pparams );

	// Early-out now by colliding against the cylinder's bounding 
	//sphere?

		dVector3 axis = { rot[2], rot[6], rot[10] };
	dVector3 ctop = { pos[0]+half_length*axis[0],
							pos[1]+half_length*axis[1],
							pos[2]+half_length*axis[2] };
	dVector3 cbot = { pos[0]-half_length*axis[0],
							pos[1]-half_length*axis[1],
							pos[2]-half_length*axis[2] };

	dVector3 cross, rvec;
	dCROSS(cross,=,pparams,axis);
	dReal projectedRadius = radius * dLENGTH(cross);
	dNormalize3(cross);
	dCROSS(rvec,=,cross,axis);
	dNormalize3(rvec);
	dOPC(rvec,*,rvec,radius);
	if( dDOT(pparams,rvec) > 0 ) {
		dOPE(rvec,=-,rvec);
	}
	dReal dtop = dDOT(pparams,ctop);
	dReal dbot = dDOT(pparams,cbot);
	dVector3 point;

	// Has the center penetrated?
	if( dDOT(pparams,pos) <= pparams[3] ) {
		// Drat.  Hopefully this will blast us out of the plane.
		if( dtop < dbot ) { dOP(point,+,ctop,rvec); }
		else { dOP(point,+,cbot,rvec); }
		generatePlaneContact(o1,o2,contact,(numContacts++)*skip,
									pparams,point);
	}
	else {
		// Has the top face penetrated?
		if( dtop - projectedRadius <= pparams[3] ) {
			dOP(point,+,ctop,rvec);
			generatePlaneContact(o1,o2,contact,(numContacts++)*skip,
										pparams,point);
			// Are we allowed to look for more contacts?
			if( maxContacts >= 2 ) {
				// Has the bottom face penetrated too?
				if( dbot - projectedRadius <= pparams[3] ) {
					dOP(point,+,cbot,rvec);
                     
					generatePlaneContact(o1,o2,contact,(numContacts++)*skip,
												pparams,point);
				}
				// Has the *whole* top face penetrated?
				else if( dtop + projectedRadius <= pparams[3] ) {
					if( maxContacts >= 3 ) {
						dVector3 rvec2;
						dCROSS(rvec2,=,axis,rvec);
						dOPC(rvec,/,rvec,2);
						dOPC(rvec2,*,rvec2,SQRT3_2);
						point[0] = ctop[0]-rvec[0]+rvec2[0];
						point[1] = ctop[1]-rvec[1]+rvec2[1];
						point[2] = ctop[2]-rvec[2]+rvec2[2];
						generatePlaneContact(o1,o2,contact,
													(numContacts++)*skip,
													pparams,point);
						point[0] = ctop[0]-rvec[0]-rvec2[0];
						point[1] = ctop[1]-rvec[1]-rvec2[1];
						point[2] = ctop[2]-rvec[2]-rvec2[2];
						generatePlaneContact(o1,o2,contact,
													(numContacts++)*skip,
													pparams,point);
					}
					else {
						dOP(point,-,ctop,rvec);
						generatePlaneContact(o1,o2,contact,
													(numContacts++)*skip,
													pparams,point);
					}
				}
			}
		}
		// Has the bottom face penetrated?
		else if( dbot - projectedRadius <= pparams[3] ) {
			dOP(point,+,cbot,rvec);
			generatePlaneContact(o1,o2,contact,(numContacts++)*skip,
										pparams,point);
			// Are we allowed to look for more contacts?
			if( maxContacts >= 2 ) {
				// Has the *whole* bottom face penetrated?
				if( dbot + projectedRadius <= pparams[3] ) {
					if( maxContacts >= 3 ) {
						dVector3 rvec2;
						dCROSS(rvec2,=,axis,rvec);
						dOPC(rvec,/,rvec,2);
						dOPC(rvec2,*,rvec2,SQRT3_2);
						point[0] = cbot[0]-rvec[0]+rvec2[0];
						point[1] = cbot[1]-rvec[1]+rvec2[1];
						point[2] = cbot[2]-rvec[2]+rvec2[2];
						generatePlaneContact(o1,o2,contact,
													(numContacts++)*skip,
													pparams,point);
						point[0] = cbot[0]-rvec[0]-rvec2[0];
						point[1] = cbot[1]-rvec[1]-rvec2[1];
						point[2] = cbot[2]-rvec[2]-rvec2[2];
						generatePlaneContact(o1,o2,contact,
													(numContacts++)*skip,
													pparams,point);
					}
					else {
						dOP(point,-,cbot,rvec);
						generatePlaneContact(o1,o2,contact,
													(numContacts++)*skip,
													pparams,point);
					}
				}
			}
		}
	}
	return numContacts;
}
