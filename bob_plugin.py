import os
import os.path
import bpy
import bmesh
import struct
import math
from mathutils import Vector
from bpy.props import StringProperty, BoolProperty
from bpy_extras.io_utils import ImportHelper, ExportHelper, axis_conversion

from contextlib import contextmanager
from collections import defaultdict

bl_info = {
    "name": "BOB/COB format",
    "description": "Import-Export BombSquad .bob and .cob files.",
    "author": "Mrmaxmeier, Aryan",
    "version": (2, 6),
    "blender": (2, 80, 0),
    "location": "File > Import-Export",
    "warning": "",
    "wiki_url": "",
    "category": "Import-Export"
}

BOB_FILE_ID = 45623
COB_FILE_ID = 13466

"""
.BOB File Structure:

MAGIC 45623 (I)
meshFormat  (I)
vertexCount (I)
faceCount   (I)
VertexObject x vertexCount (fff HH hhh xx)
index x faceCount*3 (b / H)

struct VertexObjectFull {
    float position[3];
    bs_uint16 uv[2]; // normalized to 16 bit unsigned ints 0 - 65535
    bs_sint16  normal[3]; // normalized to 16 bit signed ints -32768 - 32767
    bs_uint8 _padding[2];
};


.COB File Structure:

MAGIC 13466 (I)
vertexCount (I)
faceCount   (I)
vertexPos x vertexCount (fff)
index x faceCount*3 (I)
normal x faceCount (fff)
"""


@contextmanager
def to_bmesh(mesh, save=False):
    try:
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bm.faces.ensure_lookup_table()
        yield bm
    finally:
        if save:
            bm.to_mesh(mesh)
        bm.free()
        del bm


def clamp(val, minimum=0, maximum=1):
    if max(min(val, maximum), minimum) != val:
        print("clamped", val, "to", max(min(val, maximum), minimum))
    return max(min(val, maximum), minimum)


class ImportBOB(bpy.types.Operator, ImportHelper):
    """Load an Bombsquad Mesh file"""
    bl_idname = "import_mesh.bob"
    bl_label = "Import Bombsquad Mesh"
    filename_ext = ".bob"
    filter_glob: StringProperty(
        default="*.bob",
        options={'HIDDEN'},
    )

    def execute(self, context):
        keywords = self.as_keywords(ignore=('filter_glob',))
        mesh = load(self, context, **keywords)
        if not mesh:
            return {'CANCELLED'}

        scene = bpy.context.scene
        obj = bpy.data.objects.new(mesh.name, mesh)
        scene.collection.objects.link(obj)
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        obj.matrix_world = axis_conversion(from_forward='-Z', from_up='Y').to_4x4()
        bpy.context.view_layer.update()
        return {'FINISHED'}


class ExportBOB(bpy.types.Operator, ExportHelper):
    """Save an Bombsquad Mesh file"""
    bl_idname = "export_mesh.bob"
    bl_label = "Export Bombsquad Mesh"
    filter_glob: StringProperty(
        default="*.bob",
        options={'HIDDEN'},
    )
    check_extension = True
    filename_ext = ".bob"

    triangulate: BoolProperty(
        name="Force Triangulation",
        description="force triangulation of .bob files",
        default=False,
    )

    def execute(self, context):
        keywords = self.as_keywords(ignore=('filter_glob',))
        return save(self, context, **keywords)


def import_bob_menu(self, context):
    self.layout.operator(ImportBOB.bl_idname, text="Bombsquad Mesh (.bob)")


def export_bob_menu(self, context):
    self.layout.operator(ExportBOB.bl_idname, text="Bombsquad Mesh (.bob)")


class ImportCOB(bpy.types.Operator, ImportHelper):
    """Load an Bombsquad Collision Mesh"""
    bl_idname = "import_mesh.cob"
    bl_label = "Import Bombsquad Collision Mesh"
    filename_ext = ".cob"
    filter_glob: StringProperty(
        default="*.cob",
        options={'HIDDEN'},
    )

    def execute(self, context):
        keywords = self.as_keywords(ignore=('filter_glob',))
        mesh = loadcob(self, context, **keywords)
        if not mesh:
            return {'CANCELLED'}

        scene = bpy.context.scene
        obj = bpy.data.objects.new(mesh.name, mesh)
        scene.collection.objects.link(obj)
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        obj.matrix_world = axis_conversion(from_forward='-Z', from_up='Y').to_4x4()
        bpy.context.view_layer.update()
        return {'FINISHED'}


class ExportCOB(bpy.types.Operator, ExportHelper):
    """Save an Bombsquad Collision Mesh file"""
    bl_idname = "export_mesh.cob"
    bl_label = "Export Bombsquad Collision Mesh"
    filter_glob: StringProperty(
        default="*.cob",
        options={'HIDDEN'},
    )
    check_extension = True
    filename_ext = ".cob"

    triangulate: BoolProperty(
        name="Force Triangulation",
        description="force triangulation of .cob files",
        default=True,
    )

    def execute(self, context):
        keywords = self.as_keywords(ignore=('filter_glob',))
        return savecob(self, context, **keywords)


def import_cob_menu(self, context):
    self.layout.operator(ImportCOB.bl_idname, text="Bombsquad Collision Mesh (.cob)")


def export_cob_menu(self, context):
    self.layout.operator(ExportCOB.bl_idname, text="Bombsquad Collision Mesh (.cob)")


def import_leveldefs(self, context):
    self.layout.operator(ImportLevelDefs.bl_idname, text="Bombsquad Level Definitions (.py)")


def export_leveldefs(self, context):
    self.layout.operator(ExportLevelDefs.bl_idname, text="Bombsquad Level Definitions (.py)")


def load(operator, context, filepath):
    filepath = os.fsencode(filepath)
    bs_dir = os.path.dirname(os.path.dirname(filepath))
    texname = os.path.basename(filepath).rstrip(b".bob") + b".dds"
    texpath = os.path.join(bs_dir, b"textures", texname)
    print(texpath)
    has_texture = os.path.isfile(texpath)
    print("texture file found:", has_texture)

    with open(filepath, 'rb') as file:
        def readstruct(s):
            tup = struct.unpack(s, file.read(struct.calcsize(s)))
            return tup[0] if len(tup) == 1 else tup

        assert readstruct("I") == BOB_FILE_ID
        meshFormat = readstruct("I")
        assert meshFormat in [0, 1]

        vertexCount = readstruct("I")
        faceCount = readstruct("I")

        verts = []
        faces = []
        edges = []
        indices = []
        uv_list = []
        normal_list = []

        for i in range(vertexCount):
            vertexObj = readstruct("fff HH hhh xx")
            position = (vertexObj[0], vertexObj[1], vertexObj[2])
            uv = (vertexObj[3] / 65535, vertexObj[4] / 65535)
            normal = (vertexObj[5] / 32767, vertexObj[6] / 32767, vertexObj[7] / 32767)
            verts.append(position)
            uv_list.append(uv)
            normal_list.append(normal)

        for i in range(faceCount * 3):
            if meshFormat == 0:
                # MESH_FORMAT_UV16_N8_INDEX8
                indices.append(readstruct("b"))
            elif meshFormat == 1:
                # MESH_FORMAT_UV16_N8_INDEX16
                indices.append(readstruct("H"))

        for i in range(faceCount):
            faces.append((indices[i * 3], indices[i * 3 + 1], indices[i * 3 + 2]))

        bob_name = bpy.path.display_name_from_filepath(filepath)
        mesh = bpy.data.meshes.new(name=bob_name)
        mesh.from_pydata(verts, edges, faces)

        with to_bmesh(mesh, save=True) as bm:
            for i, face in enumerate(bm.faces):
                for vi, vert in enumerate(face.verts):
                    vert.normal = normal_list[vert.index]

        uv_texture = mesh.uv_layers.new(name=texname.decode("ascii", "ignore"))
        texture = None
        if has_texture:
            texture = bpy.data.images.load(texpath)
        #    uv_texture.data[0].image = texture

        with to_bmesh(mesh, save=True) as bm:
            uv_layer = bm.loops.layers.uv.verify()
            tex_layer = bm.faces.layers.face_map.verify()
            for i, face in enumerate(bm.faces):
                for vi, vert in enumerate(face.verts):
                    uv = uv_list[vert.index]
                    uv = (uv[0], 1 - uv[1])
                    face.loops[vi][uv_layer].uv = uv
        #            if texture:
        #                face[tex_layer].image = texture

        mesh.validate()
        mesh.update()

        return mesh


class Verts:
    def __init__(self):
        self._verts = []
        self._by_blender_index = defaultdict(list)

    def get(self, coords, normal, blender_index, uv=None):
        instance = Vert(coords=coords, normal=normal, uv=uv)
        for other in self._by_blender_index[blender_index]:
            if instance.similar(other):
                return other
        self._by_blender_index[blender_index].append(instance)
        instance.index = len(self._verts)
        self._verts.append(instance)
        return instance

    def __len__(self):
        return len(self._verts)

    def __iter__(self):
        return iter(self._verts)


def vec_similar(v1, v2):
    return (v1 - v2).length < 0.01


class Vert:
    def __init__(self, coords, normal, uv):
        self.coords = coords
        self.normal = normal
        self.uv = uv

    def similar(self, other):
        is_similar = vec_similar(self.coords, other.coords)
        is_similar = is_similar and vec_similar(self.normal, other.normal)
        if self.uv and other.uv:
            is_similar = is_similar and vec_similar(self.uv, other.uv)
        return is_similar


def save(operator, context, filepath, triangulate, check_existing):
    print("exporting", filepath)
    global_matrix = axis_conversion(to_forward='-Z', to_up='Y').to_4x4()
    scene = context.scene
    obj = bpy.context.active_object
    mesh = obj.to_mesh()
    mesh.transform(global_matrix @ obj.matrix_world)  # inverse transformation

    with to_bmesh(mesh) as bm:
        triangulate = triangulate or any([len(face.verts) != 3 for face in bm.faces])
    if triangulate or any([len(face.vertices) != 3 for face in mesh.loop_triangles]):
        print("triangulating...")
        with to_bmesh(mesh, save=True) as bm:
            bmesh.ops.triangulate(bm, faces=bm.faces)
        mesh.update(calc_edges=True)

    filepath = os.fsencode(filepath)

    with open(filepath, 'wb') as file:

        def writestruct(s, *args):
            file.write(struct.pack(s, *args))

        writestruct('I', BOB_FILE_ID)
        writestruct('I', 1)  # MESH_FORMAT_UV16_N8_INDEX16

        verts = Verts()
        faces = []
        with to_bmesh(mesh) as bm:
            uv_layer = None
            if len(bm.loops.layers.uv) > 0:
                uv_layer = bm.loops.layers.uv[0]
            for i, face in enumerate(bm.faces):
                faceverts = []
                for vi, vert in enumerate(face.verts):
                    uv = face.loops[vi][uv_layer].uv if uv_layer else None
                    v = verts.get(coords=vert.co, normal=vert.normal, uv=uv, blender_index=vert.index)
                    faceverts.append(v)
                faces.append(faceverts)

            print("verts: {} [best: {}, worst: {}]".format(len(verts), len(mesh.vertices), len(faces) * 3))
            print("faces:", len(faces))
            writestruct('I', len(verts))
            writestruct('I', len(faces))

            for vert in verts:
                writestruct('fff', *vert.coords)
                if vert.uv:
                    uv = vert.uv
                    writestruct('HH', int(clamp(uv[0]) * 65535), int((1 - clamp(uv[1])) * 65535))
                else:
                    writestruct('HH', 0, 0)
                normal = tuple(map(lambda n: int(clamp(n, -1, 1) * 32767), vert.normal))
                writestruct('hhh', *normal)
                writestruct('xx')

            for face in faces:
                assert len(face) == 3
                for vert in face:
                    writestruct('H', vert.index)

    return {'FINISHED'}


def loadcob(operator, context, filepath):
    with open(os.fsencode(filepath), 'rb') as file:
        def readstruct(s):
            tup = struct.unpack(s, file.read(struct.calcsize(s)))
            return tup[0] if len(tup) == 1 else tup

        assert readstruct("I") == COB_FILE_ID

        vertexCount = readstruct("I")
        faceCount = readstruct("I")

        verts = []
        faces = []
        edges = []
        indices = []

        for i in range(vertexCount):
            vertexObj = readstruct("fff")
            position = (vertexObj[0], vertexObj[1], vertexObj[2])
            verts.append(position)

        for i in range(faceCount * 3):
            indices.append(readstruct("I"))

        for i in range(faceCount):
            faces.append((indices[i * 3], indices[i * 3 + 1], indices[i * 3 + 2]))

        bob_name = bpy.path.display_name_from_filepath(filepath)
        mesh = bpy.data.meshes.new(name=bob_name)
        mesh.from_pydata(verts, edges, faces)

        mesh.validate()
        mesh.update()

        return mesh


def savecob(operator, context, filepath, triangulate, check_existing):
    print("exporting", filepath)
    global_matrix = axis_conversion(to_forward='-Z', to_up='Y').to_4x4()
    scene = context.scene
    obj = bpy.context.active_object
    mesh = obj.to_mesh()
    mesh.transform(global_matrix @ obj.matrix_world)  # inverse transformation
    mesh.calc_loop_triangles();

    with to_bmesh(mesh) as bm:
        triangulate = triangulate or any([len(face.verts) != 3 for face in bm.faces])
    if triangulate or any([len(face.vertices) != 3 for face in mesh.loop_triangles]):
        print("triangulating...")
        with to_bmesh(mesh, save=True) as bm:
            bmesh.ops.triangulate(bm, faces=bm.faces)
        mesh.update(calc_edges=True)

    with open(os.fsencode(filepath), 'wb') as file:

        def writestruct(s, *args):
            file.write(struct.pack(s, *args))

        writestruct('I', COB_FILE_ID)
        writestruct('I', len(mesh.vertices))

        faceVerts = []
        faceNormal = []
        with to_bmesh(mesh) as bm:
            for i, face in enumerate(bm.faces):
                for vi, vert in enumerate(face.verts):
                    faceVerts.append(vert.index)
                faceNormal.append(face.normal)

        writestruct('I', int(len(faceVerts)/3))

        for i, vert in enumerate(mesh.vertices):
            writestruct('fff', *vert.co)
            print(*vert.co)


        for vertid in faceVerts:
            writestruct('I', vertid)

        for norm in faceNormal:
            writestruct('fff', *norm)

        print('finished')

    return {'FINISHED'}


def flpV(vector):
    vector = vector.copy()
    vector.y = -vector.y
    return vector.xzy


class ImportLevelDefs(bpy.types.Operator, ImportHelper):
    """Load Bombsquad Level Defs"""
    bl_idname = "import_bombsquad.leveldefs"
    bl_label = "Import Bombsquad Level Definitions"
    filename_ext = ".py"
    filter_glob: StringProperty(
        default="*.py",
        options={'HIDDEN'},
    )

    def execute(self, context):
        keywords = self.as_keywords(ignore=('filter_glob',))
        print("executing", keywords["filepath"])
        data = {}
        with open(os.fsencode(keywords["filepath"]), "r") as file:
            exec(file.read(), data)
        del data["__builtins__"]
        if "points" not in data or "boxes" not in data:
            return {'CANCELLED'}

        scene = bpy.context.scene
        points = bpy.data.collections.new("points")
        bpy.context.scene.collection.children.link(points)
        boxes = bpy.data.collections.new("boxes")
        scene.collection.children.link(boxes)
        scene.cursor.location = (0,0,0)
        bpy.context.view_layer.update()

        def makeBox(middle, scale, collection):
            bpy.ops.mesh.primitive_cube_add(location=middle)
            cube = bpy.context.active_object
            cube.scale = scale
            cube.show_name = True
            cube.show_wire = True
            cube.display_type = 'WIRE'
            cube.name = key
            bpy.data.collections[collection].objects.link(cube)
            bpy.context.collection.objects.unlink(cube)
            return cube

        for key, pos in data["points"].items():
            if len(pos) == 6:
                middle, size = Vector(pos[:3]), Vector(pos[3:])
                if "spawn" in key.lower():
                    size.y = 0.05
                cube = makeBox((middle.x,-middle.z,middle.y), size, 'points')
                bpy.ops.object.select_all(action='DESELECT')
                cube.select_set(True)
                bpy.context.view_layer.objects.active = cube
                scene.tool_settings.transform_pivot_point = 'CURSOR'
                bpy.ops.transform.rotate(value=-math.pi/2, orient_axis='X', orient_type='GLOBAL')

            else:
                empty = bpy.data.objects.new(key, None)
                middle = Vector(pos[:3])
                empty.location = (middle.x,-middle.z,middle.y)
                empty.empty_display_size = 0.45
                points.objects.link(empty)
                empty.show_name = True
                bpy.ops.object.select_all(action='DESELECT')
                empty.select_set(True)
                bpy.context.view_layer.objects.active = empty
                scene.tool_settings.transform_pivot_point = 'CURSOR'
                bpy.ops.transform.rotate(value=-math.pi/2, orient_axis='X', orient_type='GLOBAL')

        for key, pos in data["boxes"].items():
            middle, size = Vector(pos[:3]), flpV(Vector(pos[6:9]))
            cube = makeBox((middle.x,-middle.z,middle.y), size/2, 'boxes')

        bpy.context.view_layer.update()
        return {'FINISHED'}


class ExportLevelDefs(bpy.types.Operator, ImportHelper):
    """Export Bombsquad Level Defs"""
    bl_idname = "export_bombsquad.leveldefs"
    bl_label = "Export Bombsquad Level Definitions"
    filename_ext = ".py"
    filter_glob: StringProperty(
        default="*.py",
        options={'HIDDEN'},
    )

    def execute(self, context):
        keywords = self.as_keywords(ignore=('filter_glob',))
        filepath = keywords["filepath"]
        print("writing level defs", filepath)

        if len(bpy.data.collections["points"].objects)==0 or len(bpy.data.collections["boxes"].objects)==0:
            return {'CANCELLED'}

        def v_to_str(v, flip=True, isScale=False):
            if flip:
                v = flpV(v)
            if isScale:
                v = Vector([abs(n) for n in v])
            return repr(tuple([round(n, 5) for n in tuple(v)]))

        with open(os.fsencode(filepath), "w+") as file:
            file.write("# This file generated from '{}'\n".format(os.path.basename(bpy.data.filepath)))
            file.write("points, boxes = {}, {}\n")

            for point in bpy.data.collections["points"].objects:
                pos = point.matrix_world.to_translation()
                if point.type == 'MESH':  # spawn point with random variance
                    scale = point.scale
                    file.write("points['{}'] = {}".format(point.name, v_to_str(pos)))
                    file.write(" + {}\n".format(v_to_str(scale, False, isScale=True)))
                else:
                    file.write("points['{}'] = {}\n".format(point.name, v_to_str(pos)))

            for box in bpy.data.collections["boxes"].objects:
                pos = box.matrix_world.to_translation()
                scale = box.scale*2
                file.write("boxes['{}'] = {}".format(box.name, v_to_str(pos)))
                file.write(" + (0, 0, 0) + {}\n".format(v_to_str(scale, isScale=True)))

        return {'FINISHED'}


classes = (
    ImportBOB,
    ExportBOB,
    ImportCOB,
    ExportCOB,
    ImportLevelDefs,
    ExportLevelDefs
)

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    #bpy.utils.register_module(__name__)
    bpy.types.TOPBAR_MT_file_import.append(import_bob_menu)
    bpy.types.TOPBAR_MT_file_export.append(export_bob_menu)
    bpy.types.TOPBAR_MT_file_import.append(import_cob_menu)
    bpy.types.TOPBAR_MT_file_export.append(export_cob_menu)
    bpy.types.TOPBAR_MT_file_import.append(import_leveldefs)
    bpy.types.TOPBAR_MT_file_export.append(export_leveldefs)


def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
    #bpy.utils.unregister_module(__name__)
    bpy.types.TOPBAR_MT_file_import.remove(import_bob_menu)
    bpy.types.TOPBAR_MT_file_export.remove(export_bob_menu)
    bpy.types.TOPBAR_MT_file_import.remove(import_cob_menu)
    bpy.types.TOPBAR_MT_file_export.remove(export_cob_menu)
    bpy.types.TOPBAR_MT_file_import.remove(import_leveldefs)
    bpy.types.TOPBAR_MT_file_export.remove(export_leveldefs)


if __name__ == "__main__":
    register()
