
// Should be included by Opcode.h if needed

	#define ICE_DONT_CHECK_COMPILER_OPTIONS

	// From Windows...
	typedef int                 BOOL;
	#ifndef FALSE
	#define FALSE               0
	#endif

	#ifndef TRUE
	#define TRUE                1
	#endif

	#include <stdio.h>
	#include <stdlib.h>
	#include <assert.h>
	#include <string.h>
	#include <float.h>
	#include <math.h>

	#ifndef ASSERT
		#define	ASSERT(exp)	{}
	#endif
	#define ICE_COMPILE_TIME_ASSERT(exp)	extern char ICE_Dummy[ (exp) ? 1 : -1 ]

	#define	Log				printf
	#define	SetIceError(a,b)	false
	#define	EC_OUTOFMEMORY	"Out of memory"

	#include "ode/IcePreprocessor.h"

	#undef ICECORE_API
	#define ICECORE_API	OPCODE_API

	#include "ode/IceTypes.h"
	#include "ode/IceFPU.h"
	#include "ode/IceMemoryMacros.h"

	namespace IceCore
	{
		#include "ode/IceUtils.h"
		#include "ode/IceContainer.h"
		#include "ode/IcePairs.h"
		#include "ode/IceRevisitedRadix.h"
		#include "ode/IceRandom.h"
	}
	using namespace IceCore;

	#define ICEMATHS_API	OPCODE_API
	namespace IceMaths
	{
		#include "ode/IceAxes.h"
		#include "ode/IcePoint.h"
		#include "ode/IceHPoint.h"
		#include "ode/IceMatrix3x3.h"
		#include "ode/IceMatrix4x4.h"
		#include "ode/IcePlane.h"
		#include "ode/IceRay.h"
		#include "ode/IceIndexedTriangle.h"
		#include "ode/IceTriangle.h"
		#include "ode/IceTriList.h"
		#include "ode/IceAABB.h"
		#include "ode/IceOBB.h"
		#include "ode/IceBoundingSphere.h"
		#include "ode/IceSegment.h"
		#include "ode/IceLSS.h"
	}
	using namespace IceMaths;
