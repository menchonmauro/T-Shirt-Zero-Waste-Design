bl_info = {
    "name": "Remera Remera de Diseño de Residuo Cero Zero Waste",
    "blender": (3, 6, 0),
    "category": "Add Mesh",
    "version": (1, 0, 0),
    "author": "Mauro Menchón",
    "description": "Generador de patrones de diseño de residuo cero (Zero Waste Design) con controles de Remera de Diseño de Residuo Cero",
    "location": "View3D > N-Panel > Remera de Diseño de Residuo Cero",
}

import bpy
import bmesh
from bpy.props import FloatProperty, BoolProperty, EnumProperty, PointerProperty
from bpy.types import PropertyGroup, Panel
import mathutils
from mathutils import Vector
import math

# Datos originales del patrón manteniendo la forma exacta
PATRON_DATA_ORIGINAL = [
    # Contorno exterior completo (clockwise desde superior izquierdo)
    (-89.4295674999999, 108.368099999),  # Esquina superior izquierda
    (-89.4295674999999, 46.210293973832),  # Inicio curva superior izquierda
    
    # Curva superior izquierda (forma interna)
    (-85.4717625, 45.924545373832),
    (-79.56484300000002, 45.106066473832),
    (-70.62415600000001, 43.590944473832),
    (-60.612256, 41.706009473832),
    (-50.739038, 39.683699973832),
    (-45.912316, 38.499673973832),
    (-47.107314, 38.651774473832),
    (-49.425109, 39.163684473832),
    (-55.756944, 40.445362973832),
    (-65.0186505, 42.308007973832),
    (-73.2384505, 43.799537973832),
    (-80.8596695, 44.999889473832),
    (-86.12117, 45.686910973832),
    (-89.4295674999999, 45.959114473832),
    
    # Continúa borde izquierdo hacia abajo
    (-89.4295674999999, 0.0),  # Esquina inferior izquierda
    
    # Borde inferior
    (0.0, 0.0),  # Esquina inferior derecha
    
    # Curva interna derecha (subida)
    (0.0, 48.722702373832),
    (-3.264354, 49.071118373832),
    (-5.339551, 49.799168373832),
    (-7.22611, 50.888833373832),
    (-8.8699315, 52.270691973832),
    (-10.273327, 53.897164973832),
    (-11.4386075, 55.720674473832),
    (-12.3680845, 57.693641473832),
    (-13.064069, 59.768486473832),
    (-13.5288725, 61.897631473832),
    (-13.7756, 63.995550473832),
    (-13.833717, 66.036640473832),
    (-13.717288, 68.062136973832),
    (-13.4194095, 70.082241973832),
    (-12.8864, 72.071916973832),
    (-12.4818445, 73.232615473832),
    (-12.3089495, 73.563895973832),
    (-12.1568235, 73.727955473832),
    (-12.068287, 73.669141473832),
    (-12.046337, 73.491286973832),
    
    # Curva de retorno (bajada)
    (-12.361732, 72.669213973832),
    (-13.0108575, 70.453303973832),
    (-13.485864, 67.418693973832),
    (-13.5381045, 64.635421973832),
    (-13.2607395, 62.131157473832),
    (-12.6965045, 59.646088973832),
    (-11.8349955, 57.253609973832),
    (-10.662807, 55.027113973832),
    (-9.1695335, 53.039994473832),
    (-7.3437705, 51.365644473832),
    (-5.174113, 50.077457473832),
    (-3.2115745, 49.332038973832),
    (-1.6105195, 49.023290973832),
    (0.0, 48.908755973832),
    
    # Borde derecho hacia arriba
    (0.0, 108.368099999),  # Esquina superior derecha
]

def get_pattern_bounds():
    """Obtener límites del patrón original"""
    x_coords = [point[0] for point in PATRON_DATA_ORIGINAL]
    y_coords = [point[1] for point in PATRON_DATA_ORIGINAL]
    
    return {
        'min_x': min(x_coords),
        'max_x': max(x_coords),
        'min_y': min(y_coords),
        'max_y': max(y_coords),
        'width': max(x_coords) - min(x_coords),
        'height': max(y_coords) - min(y_coords),
        'center_x': (min(x_coords) + max(x_coords)) / 2,
        'center_y': (min(y_coords) + max(y_coords)) / 2
    }

ORIGINAL_BOUNDS = get_pattern_bounds()

# Identificar secciones del patrón para controles independientes
CURVE_UPPER_LEFT_INDICES = list(range(1, 16))  # Curva superior izquierda (cuello)
CURVE_INTERNAL_RIGHT_INDICES = list(range(18, 52))  # Curva interna derecha completa (manga)

def redistribute_curve_vertices(curve_points, equidistant=True):
    """Redistribuir vértices de una curva para que sean equidistantes"""
    if not equidistant or len(curve_points) < 3:
        return curve_points
    
    # Calcular la longitud total de la curva
    total_length = 0
    for i in range(len(curve_points) - 1):
        dx = curve_points[i+1][0] - curve_points[i][0]
        dy = curve_points[i+1][1] - curve_points[i][1]
        total_length += math.sqrt(dx*dx + dy*dy)
    
    # Distancia objetivo entre puntos
    segment_length = total_length / (len(curve_points) - 1)
    
    # Redistribuir puntos
    redistributed = [curve_points[0]]  # Mantener el primer punto
    
    current_length = 0
    target_length = segment_length
    
    for i in range(len(curve_points) - 1):
        dx = curve_points[i+1][0] - curve_points[i][0]
        dy = curve_points[i+1][1] - curve_points[i][1]
        segment_len = math.sqrt(dx*dx + dy*dy)
        
        while current_length + segment_len >= target_length and len(redistributed) < len(curve_points):
            # Interpolar punto en la posición objetivo
            t = (target_length - current_length) / segment_len
            new_x = curve_points[i][0] + t * dx
            new_y = curve_points[i][1] + t * dy
            redistributed.append((new_x, new_y))
            target_length += segment_length
        
        current_length += segment_len
    
    # Asegurar que tenemos el mismo número de puntos
    while len(redistributed) < len(curve_points):
        redistributed.append(curve_points[-1])
    
    return redistributed[:len(curve_points)]

class PatronShapeProperties(PropertyGroup):
    """Propiedades para el sistema de Remera de Diseño de Residuo Cero profesional"""
    
    # ──────────────── DIMENSIONES EN CENTÍMETROS ────────────────
    pattern_width: FloatProperty(
        name="Ancho del Patrón (cm)",
        description="Ancho total del patrón en centímetros",
        default=67.5,
        min=10.0,
        max=200.0,
        step=0.5,
        precision=1
    )
    
    pattern_height: FloatProperty(
        name="Alto del Patrón (cm)", 
        description="Alto total del patrón en centímetros",
        default=80.0,
        min=10.0,
        max=200.0,
        step=0.5,
        precision=1
    )
    
    # ──────────────── CURVA SUPERIOR IZQUIERDA (CUELLO) ────────────────
    curve_upper_scale: FloatProperty(
        name="Escala Cuello",
        description="Factor de escala para la curva del cuello",
        default=1.0,
        min=0.1,
        max=5.0,
        step=0.05,
        precision=2
    )
    
    curve_upper_depth: FloatProperty(
        name="Profundidad Cuello",
        description="Profundidad de la curva del cuello (hacia adentro)",
        default=1.0,
        min=0.1,
        max=3.0,
        step=0.05,
        precision=2
    )
    
    curve_upper_position_y: FloatProperty(
        name="Posición Vertical Cuello (cm)",
        description="Posición vertical de la curva del cuello",
        default=0.0,
        min=-20.0,
        max=20.0,
        step=0.5,
        precision=1
    )
    
    # Distribución equidistante para cuello
    cuello_equidistante: BoolProperty(
        name="Cuello Equidistante",
        description="Distribuir vértices del cuello de manera equidistante",
        default=True
    )
    
    # ──────────────── CURVA INTERNA DERECHA (MANGA) ────────────────
    curve_internal_scale: FloatProperty(
        name="Escala Manga",
        description="Factor de escala para la curva de la manga",
        default=1.0,
        min=0.1,
        max=3.0,
        step=0.02,
        precision=2
    )
    
    curve_internal_depth: FloatProperty(
        name="Profundidad Manga",
        description="Profundidad de la curva de la manga (hacia adentro)",
        default=1.0,
        min=0.1,
        max=3.0,
        step=0.05,
        precision=2
    )
    
    curve_internal_position_y: FloatProperty(
        name="Posición Vertical Manga (cm)",
        description="Posición vertical de la curva de la manga",
        default=0.0,
        min=-15.0,
        max=15.0,
        step=0.5,
        precision=1
    )
    
    # Distribución equidistante para manga
    manga_equidistante: BoolProperty(
        name="Manga Equidistante",
        description="Distribuir vértices de la manga de manera equidistante",
        default=True
    )
    
    # ──────────────── POSICIÓN DEL PATRÓN ────────────────
    pattern_position_x: FloatProperty(
        name="Posición X (cm)",
        description="Posición horizontal del patrón completo",
        default=0.0,
        step=1.0
    )
    
    pattern_position_y: FloatProperty(
        name="Posición Y (cm)", 
        description="Posición en profundidad del patrón completo",
        default=0.0,
        step=1.0
    )
    
    pattern_position_z: FloatProperty(
        name="Altura Z (cm)",
        description="Altura del patrón completo",
        default=0.0,
        step=1.0
    )
    
    # ──────────────── CONFIGURACIÓN PROFESIONAL ────────────────
    auto_update: BoolProperty(
        name="Vista Previa en Tiempo Real",
        description="Actualizar automáticamente mientras se ajustan los valores",
        default=True
    )

def transform_pattern_coordinates(props):
    """Transformar coordenadas del patrón manteniendo proporciones"""
    
    # Factor de conversión de centímetros a metros para Blender
    unit_scale = 0.01
    
    # Calcular factores de escala basados en las dimensiones deseadas
    scale_x = (props.pattern_width * unit_scale) / (ORIGINAL_BOUNDS['width'] * 0.05)
    scale_y = (props.pattern_height * unit_scale) / (ORIGINAL_BOUNDS['height'] * 0.05)
    
    # Preparar coordenadas base
    base_coords = []
    for x, y in PATRON_DATA_ORIGINAL:
        new_x = x * 0.05 * scale_x
        new_y = y * 0.05 * scale_y
        base_coords.append((new_x, new_y))
    
    # Redistribuir vértices de las curvas si está habilitado
    if props.cuello_equidistante:
        # Extraer puntos del cuello
        cuello_points = [base_coords[i] for i in CURVE_UPPER_LEFT_INDICES]
        cuello_redistributed = redistribute_curve_vertices(cuello_points, True)
        
        # Reemplazar en las coordenadas base
        for i, idx in enumerate(CURVE_UPPER_LEFT_INDICES):
            if i < len(cuello_redistributed):
                base_coords[idx] = cuello_redistributed[i]
    
    if props.manga_equidistante:
        # Extraer puntos de la manga
        manga_points = [base_coords[i] for i in CURVE_INTERNAL_RIGHT_INDICES]
        manga_redistributed = redistribute_curve_vertices(manga_points, True)
        
        # Reemplazar en las coordenadas base
        for i, idx in enumerate(CURVE_INTERNAL_RIGHT_INDICES):
            if i < len(manga_redistributed):
                base_coords[idx] = manga_redistributed[i]
    
    # Aplicar transformaciones específicas a las curvas
    transformed_coords = []
    for i, (x, y) in enumerate(base_coords):
        new_x, new_y = x, y
        
        if i in CURVE_UPPER_LEFT_INDICES:
            # Curva del cuello
            center_x = base_coords[1][0]
            center_y = base_coords[1][1]
            
            offset_x = new_x - center_x
            offset_y = new_y - center_y
            
            new_x = center_x + offset_x * props.curve_upper_scale * props.curve_upper_depth
            new_y = center_y + offset_y * props.curve_upper_scale + props.curve_upper_position_y * unit_scale
            
        elif i in CURVE_INTERNAL_RIGHT_INDICES:
            # Curva de la manga
            center_x = base_coords[18][0]
            center_y = base_coords[18][1]
            
            offset_x = new_x - center_x
            offset_y = new_y - center_y
            
            new_x = center_x + offset_x * props.curve_internal_scale * props.curve_internal_depth
            new_y = center_y + offset_y * props.curve_internal_scale + props.curve_internal_position_y * unit_scale
        
        # Aplicar posición global
        final_x = new_x + props.pattern_position_x * unit_scale
        final_y = new_y + props.pattern_position_y * unit_scale
        final_z = props.pattern_position_z * unit_scale
        
        transformed_coords.append((final_x, final_y, final_z))
    
    return transformed_coords

class MESH_OT_add_patron_shape(bpy.types.Operator):
    """Crear nuevo patrón"""
    bl_idname = "mesh.add_patron_shape"
    bl_label = "Crear Patrón"
    bl_description = "Crear un nuevo patrón con las configuraciones actuales"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.patron_props
        
        # Crear mesh
        mesh = bpy.data.meshes.new('Patron_Profesional')
        bm = bmesh.new()
        
        # Obtener coordenadas transformadas
        coords = transform_pattern_coordinates(props)
        
        # Crear vértices
        verts = []
        for coord in coords:
            vert = bm.verts.new(coord)
            verts.append(vert)
        
        # Crear aristas del contorno
        for i in range(len(verts)):
            next_i = (i + 1) % len(verts)
            bm.edges.new([verts[i], verts[next_i]])
        
        # Limpiar y finalizar
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
        bm.normal_update()
        
        # Convertir a mesh
        bm.to_mesh(mesh)
        bm.free()
        
        # Crear objeto
        obj_name = f'Patron_{props.pattern_width:.1f}x{props.pattern_height:.1f}cm'
        obj = bpy.data.objects.new(obj_name, mesh)
        context.collection.objects.link(obj)
        
        # Seleccionar objeto
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        
        self.report({'INFO'}, f'Patrón creado: {obj_name}')
        return {'FINISHED'}

class MESH_OT_update_patron(bpy.types.Operator):
    """Actualizar patrón existente"""
    bl_idname = "mesh.update_patron"
    bl_label = "Actualizar Patrón"
    bl_description = "Actualizar el patrón seleccionado con las nuevas configuraciones"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.patron_props
        obj = context.active_object
        
        if not obj or obj.type != 'MESH':
            self.report({'WARNING'}, "Selecciona un objeto mesh para actualizar")
            return {'CANCELLED'}
        
        # Obtener coordenadas actualizadas
        coords = transform_pattern_coordinates(props)
        
        # Recrear mesh
        bm = bmesh.new()
        
        verts = []
        for coord in coords:
            vert = bm.verts.new(coord)
            verts.append(vert)
        
        for i in range(len(verts)):
            next_i = (i + 1) % len(verts)
            bm.edges.new([verts[i], verts[next_i]])
        
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
        bm.normal_update()
        
        # Actualizar mesh del objeto
        bm.to_mesh(obj.data)
        bm.free()
        
        obj.data.update()
        
        self.report({'INFO'}, f'Patrón actualizado: {obj.name}')
        return {'FINISHED'}

class VIEW3D_PT_patron_main_panel(Panel):
    """Panel principal de Remera de Diseño de Residuo Cero profesional"""
    bl_label = "🧵 Remera de Diseño de Residuo Cero Profesional"
    bl_idname = "VIEW3D_PT_patron_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Remera de Diseño de Residuo Cero"
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.patron_props
        
        # ──────────────── ENCABEZADO PROFESIONAL ────────────────
        box = layout.box()
        row = box.row()
        row.scale_y = 1.2
        row.operator("mesh.add_patron_shape", icon='ADD', text="Crear Nuevo Patrón")
        
        row = box.row()
        row.operator("mesh.update_patron", icon='FILE_REFRESH', text="Actualizar Patrón")
        row.prop(props, "auto_update", text="", icon='AUTO')
        
        # ──────────────── DIMENSIONES PRINCIPALES ────────────────
        box = layout.box()
        box.label(text="📏 Dimensiones del Patrón", icon='FULLSCREEN_ENTER')
        
        col = box.column(align=True)
        row = col.row(align=True)
        row.prop(props, "pattern_width", text="Ancho")
        row.prop(props, "pattern_height", text="Alto")
        
        # Mostrar medidas calculadas
        col.separator()
        info_box = col.box()
        info_box.scale_y = 0.8
        info_col = info_box.column(align=True)
        info_col.label(text=f"Área: {props.pattern_width * props.pattern_height:.1f} cm²")
        info_col.label(text=f"Perímetro aprox.: {2 * (props.pattern_width + props.pattern_height):.1f} cm")

class VIEW3D_PT_patron_curves_panel(Panel):
    """Panel para controles de curvas"""
    bl_label = "🔄 Control de Formas"
    bl_idname = "VIEW3D_PT_patron_curves_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Remera de Diseño de Residuo Cero"
    bl_parent_id = "VIEW3D_PT_patron_main_panel"
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.patron_props
        
        # ──────────────── CURVA DEL CUELLO ────────────────
        box = layout.box()
        box.label(text="👔 Cuello", icon='CURVE_BEZCURVE')
        
        col = box.column(align=True)
        col.prop(props, "cuello_equidistante", text="Vértices Equidistantes")
        col.separator()
        col.prop(props, "curve_upper_scale", text="Escala", slider=True)
        col.prop(props, "curve_upper_depth", text="Profundidad", slider=True)
        col.prop(props, "curve_upper_position_y", text="Posición Y")
        
        # ──────────────── CURVA DE LA MANGA ────────────────
        box = layout.box()
        box.label(text="👕 Manga", icon='CURVE_BEZCIRCLE')
        
        col = box.column(align=True)
        col.prop(props, "manga_equidistante", text="Vértices Equidistantes")
        col.separator()
        col.prop(props, "curve_internal_scale", text="Escala", slider=True)
        col.prop(props, "curve_internal_depth", text="Profundidad", slider=True)
        col.prop(props, "curve_internal_position_y", text="Posición Y")

class VIEW3D_PT_patron_position_panel(Panel):
    """Panel para posición"""
    bl_label = "🎯 Posición en Escena"
    bl_idname = "VIEW3D_PT_patron_position_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Remera de Diseño de Residuo Cero"
    bl_parent_id = "VIEW3D_PT_patron_main_panel"
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.patron_props
        
        # ──────────────── POSICIÓN ────────────────
        box = layout.box()
        box.label(text="📍 Posición", icon='OBJECT_ORIGIN')
        
        col = box.column(align=True)
        col.prop(props, "pattern_position_x", text="X")
        col.prop(props, "pattern_position_y", text="Y") 
        col.prop(props, "pattern_position_z", text="Z")

def menu_func(self, context):
    self.layout.separator()
    self.layout.operator(MESH_OT_add_patron_shape.bl_idname, icon='MESH_PLANE')

def register():
    bpy.utils.register_class(PatronShapeProperties)
    bpy.utils.register_class(MESH_OT_add_patron_shape)
    bpy.utils.register_class(MESH_OT_update_patron)
    bpy.utils.register_class(VIEW3D_PT_patron_main_panel)
    bpy.utils.register_class(VIEW3D_PT_patron_curves_panel)
    bpy.utils.register_class(VIEW3D_PT_patron_position_panel)
    
    bpy.types.Scene.patron_props = PointerProperty(type=PatronShapeProperties)
    bpy.types.VIEW3D_MT_mesh_add.append(menu_func)

def unregister():
    bpy.utils.unregister_class(PatronShapeProperties)
    bpy.utils.unregister_class(MESH_OT_add_patron_shape)
    bpy.utils.unregister_class(MESH_OT_update_patron)
    bpy.utils.unregister_class(VIEW3D_PT_patron_main_panel)
    bpy.utils.unregister_class(VIEW3D_PT_patron_curves_panel)
    bpy.utils.unregister_class(VIEW3D_PT_patron_position_panel)
    
    del bpy.types.Scene.patron_props
    bpy.types.VIEW3D_MT_mesh_add.remove(menu_func)

if __name__ == "__main__":
    register()

