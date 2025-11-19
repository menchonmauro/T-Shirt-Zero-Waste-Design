# -*- coding: utf-8 -*-
bl_info = {
    "name": "Coser (Depurado)",
    "author": "ChatGPT",
    "version": (1, 0, 1),
    "blender": (3, 6, 0),
    "location": "View3D > N-panel > Coser",
    "description": "Cose (conecta) dos series de vértices según orden por eje o por índice. Panel minimalista con un único botón.",
    "category": "Mesh",
}

import bpy, bmesh
from mathutils import Vector
from bpy.types import Operator, Panel
from bpy.props import EnumProperty, BoolProperty


# ---------------------------
# Utilidades
# ---------------------------
def _active_bmesh(context):
    obj = context.active_object
    if not obj or obj.type != 'MESH':
        return None, None
    try:
        bpy.ops.object.mode_set(mode='EDIT')
    except Exception:
        pass
    me = obj.data
    bm = bmesh.from_edit_mesh(me)
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    return obj, bm


def _selected_islands(bm):
    """Devuelve listas de vértices seleccionados agrupadas por islas."""
    sel_verts = [v for v in bm.verts if v.select]
    if not sel_verts:
        return []

    visited = set()
    islands = []
    for v in sel_verts:
        if v.index in visited:
            continue
        stack = [v]
        comp = []
        visited.add(v.index)
        while stack:
            cur = stack.pop()
            comp.append(cur)
            for e in cur.link_edges:
                other = e.other_vert(cur)
                if other.select and other.index not in visited:
                    visited.add(other.index)
                    stack.append(other)
        islands.append(sorted(comp, key=lambda vv: vv.index))
    return islands


def _principal_axis_axis_from_bbox(verts):
    """Devuelve el eje con mayor extensión."""
    xs = [v.co.x for v in verts]
    ys = [v.co.y for v in verts]
    zs = [v.co.z for v in verts]
    ex, ey, ez = (max(xs)-min(xs)), (max(ys)-min(ys)), (max(zs)-min(zs))
    if ex >= ey and ex >= ez:
        return 'X'
    if ey >= ex and ey >= ez:
        return 'Y'
    return 'Z'


def _sort_series(series, order_mode, axis='AUTO', invert=False):
    verts = list(series)
    if order_mode == 'INDEX':
        verts.sort(key=lambda v: v.index)
    else:
        ax = _principal_axis_axis_from_bbox(verts) if axis == 'AUTO' else axis
        verts.sort(key=lambda v: getattr(v.co, ax.lower()))
    if invert:
        verts.reverse()
    return verts


def _ensure_edge(bm, v0, v1):
    if v0 == v1:
        return None
    for e in v0.link_edges:
        if v1 in e.verts:
            return e
    try:
        return bm.edges.new((v0, v1))
    except ValueError:
        return None


# ---------------------------
# Operador principal
# ---------------------------
class MESH_OT_coser_series(Operator):
    bl_idname = "mesh.coser_series"
    bl_label = "Coser Series"
    bl_description = "Cose dos series de vértices según orden por eje o por índice"
    bl_options = {'REGISTER', 'UNDO'}

    order_mode: EnumProperty(
        name="Orden de cada serie",
        items=[
            ('AXIS', "Por eje", "Ordenar por coordenada en un eje"),
            ('INDEX', "Por índice", "Ordenar por índice de vértice"),
        ],
        default='AXIS'
    )

    axis: EnumProperty(
        name="Eje",
        items=[
            ('AUTO', "Auto", "Detecta mayor extensión"),
            ('X', "X", "Ordena por X"),
            ('Y', "Y", "Ordena por Y"),
            ('Z', "Z", "Ordena por Z"),
        ],
        default='AUTO'
    )

    invert_a: BoolProperty(name="Invertir Serie A", default=False)
    invert_b: BoolProperty(name="Invertir Serie B", default=False)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=380)

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        col.prop(self, "order_mode", text="Orden de cada serie")
        row = col.row(align=True)
        row.enabled = (self.order_mode == 'AXIS')
        row.prop(self, "axis", text="")
        col.separator()
        row2 = col.row(align=True)
        row2.prop(self, "invert_a")
        row2.prop(self, "invert_b")

    def execute(self, context):
        obj, bm = _active_bmesh(context)
        if not bm:
            self.report({'ERROR'}, "Seleccioná una malla activa")
            return {'CANCELLED'}

        islands = _selected_islands(bm)
        if len(islands) < 2:
            self.report({'ERROR'}, "Seleccioná vértices de al menos dos series (islas) separadas")
            return {'CANCELLED'}

        islands.sort(key=lambda comp: len(comp), reverse=True)
        a, b = islands[:2]

        a_sorted = _sort_series(a, self.order_mode, axis=self.axis, invert=self.invert_a)
        b_sorted = _sort_series(b, self.order_mode, axis=self.axis, invert=self.invert_b)

        count = min(len(a_sorted), len(b_sorted))
        created = 0
        for i in range(count):
            if _ensure_edge(bm, a_sorted[i], b_sorted[i]):
                created += 1

        bmesh.update_edit_mesh(obj.data)
        self.report({'INFO'}, f"Cosedas {created} aristas entre {count} pares")
        return {'FINISHED'}


# ---------------------------
# Panel minimalista “Coser”
# ---------------------------
class VIEW3D_PT_coser(Panel):
    bl_label = "Coser"
    bl_idname = "VIEW3D_PT_coser"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Coser"

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        col.operator(MESH_OT_coser_series.bl_idname, text="Coser", icon='AUTOMERGE_OFF')


# ---------------------------
# Registro
# ---------------------------
classes = (
    MESH_OT_coser_series,
    VIEW3D_PT_coser,
)

def register():
    for c in classes:
        bpy.utils.register_class(c)

def unregister():
    for c in reversed(classes):
        bpy.utils.unregister_class(c)

if __name__ == "__main__":
    register()
