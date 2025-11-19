# -*- coding: utf-8 -*-
import bpy, bmesh, os, math
from mathutils import Vector
from bpy.props import (
    BoolProperty, FloatProperty, EnumProperty, StringProperty, IntProperty, PointerProperty
)
from bpy.types import Operator, Panel, PropertyGroup

bl_info = {
    "name": "Exporta a SVG",
    "author": "Mauro Menchón",
    "version": (1, 0, 0),
    "blender": (3, 6, 0),
    "location": "View3D > Sidebar > Cloth Tools",
    "description": "Exporta patrones a SVG con capas separadas y IDs centrados en líneas",
    "category": "Mesh",
}

# -------------------- Utilidades geométricas --------------------
def axis_extents_world(verts_world):
    xs = [v.x for v in verts_world]; ys = [v.y for v in verts_world]; zs = [v.z for v in verts_world]
    return (max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs))

def auto_plane(verts_world):
    ex, ey, ez = axis_extents_world(verts_world)
    candidates = [('XY', ez), ('XZ', ey), ('YZ', ex)]
    candidates.sort(key=lambda t: t[1])
    return candidates[0][0]

def project_point_world_to_2d(vec_world, mode):
    if mode == 'XY': return Vector((vec_world.x, vec_world.y))
    if mode == 'XZ': return Vector((vec_world.x, vec_world.z))
    if mode == 'YZ': return Vector((vec_world.y, vec_world.z))
    return Vector((vec_world.x, vec_world.y))

# -------------------- Colocador de etiquetas --------------------
class LabelPlacer:
    def __init__(self, width, height, margin_cm, cell=6):
        self.w, self.h = width, height
        self.margin = margin_cm
        self.cell = max(4, int(cell))
        self.grid = {}
        self.items = []

    def _cell_idx(self, x, y): return int(x // self.cell), int(y // self.cell)
    def _clamp(self, x, y, w, h):
        x0 = self.margin + w/2; y0 = self.margin + h/2
        x1 = self.w - self.margin - w/2; y1 = self.h - self.margin - h/2
        return (max(x0, min(x, x1)), max(y0, min(y, y1)))
    def _neighbors(self, x, y):
        cx, cy = self._cell_idx(x, y); res=[]
        for ix in range(cx-1, cx+2):
            for iy in range(cy-1, cy+2):
                res.extend(self.grid.get((ix,iy),()))
        return res
    def local_density(self, x, y, radius=12):
        r2 = radius*radius; cnt=0
        for j in self._neighbors(x, y):
            x2,y2,_,_,_ = self.items[j]
            if (x-x2)*(x-x2)+(y-y2)*(y-y2) <= r2: cnt+=1
        return cnt
    def _conflicts(self, x, y, w, h, min_dist, prio):
        for j in self._neighbors(x, y):
            x2,y2,w2,h2,pr2 = self.items[j]
            if (abs(x-x2) <= (w+w2)*0.52 and abs(y-y2) <= (h+h2)*0.52): return True
            md = max(min_dist, min_dist*1.35 if pr2 < prio else min_dist)
            if (x-x2)*(x-x2)+(y-y2)*(y-y2) < md*md: return True
        return False
    def _reserve(self, x, y, w, h, prio):
        idx = len(self.items); self.items.append((x,y,w,h,prio))
        cx, cy = self._cell_idx(x, y); self.grid.setdefault((cx,cy),[]).append(idx)
    def place(self, x, y, w, h, *, prio=1, rings=12, step=None, min_dist=8):
        x, y = self._clamp(x, y, w, h); step = self.cell if step is None else max(2, step)
        for r in range(0, rings+1):
            for qx,qy in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,1),(1,-1),(-1,-1),(0,0)):
                px = x + qx*r*step; py = y + qy*r*step
                px, py = self._clamp(px, py, w, h)
                if not self._conflicts(px, py, w, h, min_dist, prio):
                    self._reserve(px, py, w, h, prio); return (px, py)
        return None

# -------------------- Propiedades --------------------
class PatternCleanSettings(PropertyGroup):
    # Rótulo
    project: StringProperty(name="Proyecto", default="Patrón")
    piece: StringProperty(name="Pieza", default="")
    size: StringProperty(name="Talle", default="")
    client: StringProperty(name="Cliente/Org", default="")
    author: StringProperty(name="Autor", default="")
    fabric: StringProperty(name="Tela", default="")
    color: StringProperty(name="Color", default="")
    notes: StringProperty(name="Notas", default="")
    show_titleblock: BoolProperty(name="Incluir rótulo", default=True)

    # Canvas / proyección
    projection_mode: EnumProperty(
        name="Plano",
        items=[('AUTO', "Auto", ""), ('XY', "XY", ""), ('XZ', "XZ", ""), ('YZ', "YZ", "")],
        default='AUTO',
    )
    margin_cm: FloatProperty(name="Margen (cm)", default=1.5, min=0.5, max=10.0)
    filename: StringProperty(name="Archivo", default="patron_v3_3.svg")

    # Unidades del documento
    doc_unit: EnumProperty(
        name="Unidad documento",
        items=[('CM','cm',''),('MM','mm',''),('IN','in',''),('PX','px','')],
        default='CM'
    )

    # Tipografías
    font_size_strategy: EnumProperty(
        name="Escala tipografías",
        items=[
            ('ABS', "Físico (cm/mm/px/pt)", "No cambia con tamaño de tela"),
            ('REL_MIN', "% del lado menor", "Escala según el lado menor del canvas"),
            ('REL_MAX', "% del lado mayor", "Escala según el lado mayor del canvas"),
        ],
        default='REL_MIN'
    )
    font_pct: FloatProperty(
        name="Porcentaje (REL)",
        description="Porcentaje del lado elegido para el tamaño base",
        default=0.05, min=0.01, max=0.50, subtype='PERCENTAGE'
    )
    font_dim_ratio: FloatProperty(name="Relativo medidas", default=0.90, min=0.40, max=1.50)
    font_id_ratio:  FloatProperty(name="Relativo IDs",     default=0.80, min=0.40, max=1.50)

    font_unit_mode: EnumProperty(
        name="Unidad tipografías",
        items=[
            ('ABS_CM','cm (absoluto)',''),
            ('ABS_MM','mm (absoluto)',''),
            ('ABS_PX','px (absoluto)',''),
            ('ABS_PT','pt (absoluto)',''),
            ('REL_PCT','% (relativo a base)','')],
        default='ABS_CM'
    )

    font_main_cm: FloatProperty(name="Texto base (cm)", default=0.10, min=0.04, max=1.5)
    font_dim_cm:  FloatProperty(name="Texto medidas (cm)", default=0.09, min=0.04, max=1.5)
    font_id_cm:   FloatProperty(name="Texto ID (cm)",      default=0.08, min=0.04, max=1.5)

    # Cotas
    show_edge_lengths: BoolProperty(name="Mostrar longitudes", default=True)
    max_edge_labels:   IntProperty(name="Máx. longitudes", default=18, min=0, max=999)
    min_edge_len_cm:   FloatProperty(name="Longitud mínima (cm)", default=1.0, min=0.0, max=100.0)
    
    # Separación medidas internas vs externas
    internal_offset_cm: FloatProperty(name="Offset medidas internas (cm)", default=1.5, min=0.3, max=5.0)
    external_offset_cm: FloatProperty(name="Offset medidas externas (cm)", default=2.5, min=0.5, max=8.0)

    # IDs
    show_ids:       BoolProperty(name="Mostrar IDs", default=True)
    max_vertex_ids: IntProperty(name="Máx. IDs vértices", default=60, min=0, max=500)
    show_vertex_dots: BoolProperty(name="Marcar vértices", default=True)
    
    # IDs centrados en líneas
    center_ids_on_edges: BoolProperty(name="Centrar IDs en líneas", default=True)

    # Ordinadas
    show_ordinate: BoolProperty(name="Medidas a bordes (X/Y)", default=False)
    ordinate_from_left:   BoolProperty(name="Desde izquierdo", default=True)
    ordinate_from_bottom: BoolProperty(name="Desde inferior",  default=True)
    max_ordinate_labels:  IntProperty(name="Máx. medidas a bordes", default=10, min=0, max=999)

# -------------------- Operador --------------------
class OBJECT_OT_export_pattern_clean(Operator):
    bl_idname = "mesh.export_pattern_clean_svg_v3_3"
    bl_label = "Exportar SVG (v3.3 Capas)"
    bl_options = {'REGISTER', 'UNDO'}

    @staticmethod
    def _fmt_doc_len(cm_val, unit):
        if unit=='CM': return f"{cm_val:.3f}cm"
        if unit=='MM': return f"{cm_val*10.0:.3f}mm"
        if unit=='IN': return f"{cm_val/2.54:.4f}in"
        if unit=='PX': return f"{cm_val*37.7952755906:.1f}px"
        return f"{cm_val:.3f}cm"

    @staticmethod
    def _fmt_font(cm_val, mode, base_cm=None):
        if mode=='ABS_CM': return f"{cm_val:.4f}cm"
        if mode=='ABS_MM': return f"{cm_val*10.0:.4f}mm"
        if mode=='ABS_PX': return f"{cm_val*37.7952755906:.3f}px"
        if mode=='ABS_PT': return f"{cm_val*28.3464566929:.3f}pt"
        if mode=='REL_PCT':
            if not base_cm or base_cm==0: base_cm=cm_val
            return f"{(cm_val/base_cm)*100.0:.1f}%"
        return f"{cm_val:.4f}cm"

    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, "Seleccioná una malla activa"); return {'CANCELLED'}
        s = context.scene.pattern_clean_settings

        prev_mode = obj.mode
        try: bpy.ops.object.mode_set(mode='EDIT')
        except Exception: pass
        bm = bmesh.from_edit_mesh(obj.data)
        bm.verts.ensure_lookup_table(); bm.edges.ensure_lookup_table()

        verts_all = list(bm.verts)
        if not verts_all:
            self.report({'ERROR'}, "No hay vértices para exportar"); return {'CANCELLED'}

        idx_map = {v.index: i for i, v in enumerate(verts_all)}
        edges = []
        for e in bm.edges:
            i0, i1 = e.verts[0].index, e.verts[1].index
            if i0 in idx_map and i1 in idx_map: edges.append((idx_map[i0], idx_map[i1]))

        verts_world = [(obj.matrix_world @ v.co).copy() for v in verts_all]
        mode = s.projection_mode if s.projection_mode != 'AUTO' else auto_plane(verts_world)
        verts_2d = [project_point_world_to_2d(vw, mode) * 100.0 for vw in verts_world]

        min_x = min(v.x for v in verts_2d); max_x = max(v.x for v in verts_2d)
        min_y = min(v.y for v in verts_2d); max_y = max(v.y for v in verts_2d)
        width_cm  = (max_x - min_x) + s.margin_cm*2.0
        height_cm = (max_y - min_y) + s.margin_cm*2.0
        offset = Vector((-min_x + s.margin_cm, -min_y + s.margin_cm))
        verts_2d = [v + offset for v in verts_2d]
        def svg_y(y): return height_cm - y

        # Calcular centroide del patrón
        centroid = Vector((0, 0))
        for v in verts_2d:
            centroid += v
        centroid /= len(verts_2d)

        # Tamaños de texto
        if s.font_size_strategy == 'ABS':
            base_main_cm = s.font_main_cm
            base_dim_cm  = s.font_dim_cm
            base_id_cm   = s.font_id_cm
        else:
            ref = min(width_cm, height_cm) if s.font_size_strategy == 'REL_MIN' else max(width_cm, height_cm)
            base_main_cm = max(0.04, ref * (s.font_pct / 100.0))
            base_dim_cm  = base_main_cm * s.font_dim_ratio
            base_id_cm   = base_main_cm * s.font_id_ratio

        area = max(width_cm*height_cm, 1.0)
        approx_labels = min(len(edges), s.max_edge_labels) + min(len(verts_2d), s.max_vertex_ids)
        dens = approx_labels / area
        gscale = 1.0
        if dens > 0.25: gscale = 0.88
        if dens > 0.40: gscale = 0.75
        if dens > 0.60: gscale = 0.66

        font_main_cm = max(0.04, base_main_cm * gscale)
        font_dim_cm  = max(0.04, base_dim_cm  * gscale)
        font_id_cm   = max(0.04, base_id_cm   * gscale)

        placer = LabelPlacer(width_cm, height_cm, s.margin_cm, cell=int(max(6, font_main_cm*28)))

        export_folder = os.path.join(os.path.expanduser('~'), 'Desktop', 'exports', 'patrones')
        os.makedirs(export_folder, exist_ok=True)
        svg_path = os.path.join(export_folder, s.filename if s.filename.lower().endswith('.svg') else (s.filename + ".svg"))

        # COLORES
        EDGE_COLOR = "#000000"
        DIM_COLOR = "#C00000"
        AUX_COLOR = "#777777"
        ID_COLOR = "#0000FF"

        # TRAZOS ESTANDARIZADOS A 0.4mm = 0.04cm
        STROKE_PATTERN = 0.04  # Trazo del patrón
        STROKE_DIM = 0.04      # Trazo dimensiones
        STROKE_AUX = 0.04      # Trazo auxiliar

        fmt_font = lambda cm: self._fmt_font(cm, s.font_unit_mode, base_cm=font_main_cm)
        font_main_css = fmt_font(font_main_cm)
        font_dim_css  = fmt_font(font_dim_cm)
        font_id_css   = fmt_font(font_id_cm)

        W_attr = self._fmt_doc_len(width_cm,  s.doc_unit)
        H_attr = self._fmt_doc_len(height_cm, s.doc_unit)

        with open(svg_path, 'w', encoding='utf-8') as f:
            f.write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W_attr}" height="{H_attr}" viewBox="0 0 {width_cm:.3f} {height_cm:.3f}">\n')

            dash_aux = STROKE_AUX*8.0; gap_aux = STROKE_AUX*4.0
            f.write('<defs>\n<style type="text/css"><![CDATA[\n')
            if s.font_unit_mode == 'REL_PCT':
                f.write(f'svg{{font-size:{font_main_cm:.4f}cm;}}\n')
            f.write(f'.edge{{stroke:{EDGE_COLOR};stroke-width:{STROKE_PATTERN:.4f}cm;fill:none;stroke-linecap:round;stroke-linejoin:round;}}\n')
            f.write(f'.dim{{stroke:{DIM_COLOR};stroke-width:{STROKE_DIM:.4f}cm;fill:none;stroke-linecap:round;}}\n')
            f.write(f'.aux{{stroke:{AUX_COLOR};stroke-width:{STROKE_AUX:.4f}cm;fill:none;stroke-dasharray:{dash_aux:.3f},{gap_aux:.3f};}}\n')
            f.write(f'.txt{{font-family:Arial,Helvetica,sans-serif;font-size:{font_main_css};fill:{EDGE_COLOR};}}\n')
            f.write(f'.txtDim{{font-family:Arial,Helvetica,sans-serif;font-size:{font_dim_css};fill:{DIM_COLOR};font-weight:600;}}\n')
            f.write(f'.txtID{{font-family:Arial,Helvetica,sans-serif;font-size:{font_id_css};fill:{ID_COLOR};}}\n')
            f.write(']]></style>\n')

            arrow_size = font_dim_cm * 1.4
            f.write(f'<marker id="arrow" markerWidth="{arrow_size:.3f}" markerHeight="{arrow_size:.3f}" refX="{arrow_size*0.5:.3f}" refY="{arrow_size*0.5:.3f}" orient="auto" markerUnits="userSpaceOnUse">')
            f.write(f'<path d="M0,0 L0,{arrow_size:.3f} L{arrow_size*0.8:.3f},{arrow_size*0.5:.3f} z" fill="{DIM_COLOR}"/></marker>\n')
            f.write('</defs>\n\n')

            # ===== CAPA 1: TRAZO DEL PATRÓN =====
            f.write('<g id="capa-trazo-patron">\n')
            for i0, i1 in edges:
                v0, v1 = verts_2d[i0], verts_2d[i1]
                f.write(f'  <line class="edge" x1="{v0.x:.4f}" y1="{svg_y(v0.y):.4f}" x2="{v1.x:.4f}" y2="{svg_y(v1.y):.4f}"/>\n')
            f.write('</g>\n\n')

            # ===== CAPA 2: LÍNEAS INTERNAS (auxiliares dentro del patrón) =====
            f.write('<g id="capa-lineas-internas">\n')
            # (Esta capa está reservada para líneas auxiliares internas si las necesitas)
            f.write('</g>\n\n')

            # Preparar medidas internas y externas
            internal_measures = []
            external_measures = []
            
            if s.show_edge_lengths and s.max_edge_labels > 0 and len(edges) > 0:
                cand=[]
                for (i0,i1) in edges:
                    v0,v1 = verts_2d[i0], verts_2d[i1]
                    L = (v1-v0).length
                    if L >= s.min_edge_len_cm: cand.append((i0,i1,L))
                cand.sort(key=lambda t: -t[2])
                step = max(1, len(cand)//s.max_edge_labels)
                chosen = [c for idx,c in enumerate(cand) if idx%step==0][:s.max_edge_labels]

                for (i0,i1,L) in chosen:
                    v0,v1 = verts_2d[i0], verts_2d[i1]
                    mid = (v0+v1)*0.5
                    
                    # Determinar si es interna o externa según relación con centroide
                    to_centroid = centroid - mid
                    dirv = v1 - v0
                    if dirv.length == 0: continue
                    
                    normal = Vector((-dirv.y, dirv.x)).normalized()
                    
                    # Si el producto punto entre normal y dirección al centroide es positivo,
                    # la medida va hacia adentro
                    dot = normal.dot(to_centroid)
                    
                    if dot > 0:
                        internal_measures.append((i0, i1, L, mid, normal, dirv))
                    else:
                        external_measures.append((i0, i1, L, mid, -normal, dirv))

            # ===== CAPA 3: MEDIDAS INTERNAS =====
            f.write('<g id="capa-medidas-internas">\n')
            box_w = font_dim_cm*5.0; box_h = font_dim_cm*2.0
            min_d = max(6.0, font_dim_cm*10)
            
            for (i0, i1, L, mid, normal, dirv) in internal_measures:
                offset_dist = s.internal_offset_cm
                base = mid + normal * offset_dist
                
                dens = placer.local_density(base.x, base.y, radius=12)
                local_scale = 1.0 if dens<=2 else (0.85 if dens<=5 else 0.72)
                bw = box_w*local_scale; bh = box_h*local_scale
                
                pos = placer.place(base.x, svg_y(base.y), bw, bh, prio=0, rings=10, step=int(max(4, font_dim_cm*8)), min_dist=min_d)
                if pos:
                    x, y = pos
                    aux_end = mid + normal * (offset_dist * 0.85)
                    f.write(f'  <line class="aux" x1="{mid.x:.4f}" y1="{svg_y(mid.y):.4f}" x2="{aux_end.x:.4f}" y2="{svg_y(aux_end.y):.4f}"/>\n')
                    f.write(f'  <text class="txtDim" x="{x:.4f}" y="{y:.4f}" text-anchor="middle" dominant-baseline="middle">{L:.1f}</text>\n')
            
            f.write('</g>\n\n')

            # ===== CAPA 4: MEDIDAS EXTERNAS =====
            f.write('<g id="capa-medidas-externas">\n')
            
            for (i0, i1, L, mid, normal, dirv) in external_measures:
                offset_dist = s.external_offset_cm
                base = mid + normal * offset_dist
                
                dens = placer.local_density(base.x, base.y, radius=12)
                local_scale = 1.0 if dens<=2 else (0.85 if dens<=5 else 0.72)
                bw = box_w*local_scale; bh = box_h*local_scale
                
                pos = placer.place(base.x, svg_y(base.y), bw, bh, prio=0, rings=10, step=int(max(4, font_dim_cm*8)), min_dist=min_d)
                if pos:
                    x, y = pos
                    aux_end = mid + normal * (offset_dist * 0.85)
                    f.write(f'  <line class="aux" x1="{mid.x:.4f}" y1="{svg_y(mid.y):.4f}" x2="{aux_end.x:.4f}" y2="{svg_y(aux_end.y):.4f}"/>\n')
                    f.write(f'  <text class="txtDim" x="{x:.4f}" y="{y:.4f}" text-anchor="middle" dominant-baseline="middle">{L:.1f}</text>\n')
            
            f.write('</g>\n\n')

            # ===== ORDINADAS (opcional) =====
            if s.show_ordinate and s.max_ordinate_labels>0:
                f.write('<g id="capa-ordinadas">\n')
                Lm = s.margin_cm; Bm = s.margin_cm
                step_o = max(1, len(verts_2d)//s.max_ordinate_labels); count=0
                arrow = ' marker-start="url(#arrow)" marker-end="url(#arrow)"'
                for i,v in enumerate(verts_2d):
                    if i%step_o!=0: continue
                    if count>=s.max_ordinate_labels: break
                    if s.ordinate_from_left:
                        dx = v.x - Lm
                        if dx>0.5:
                            ysvg=svg_y(v.y); offy=-font_dim_cm*0.8
                            f.write(f'  <line class="aux" x1="{Lm:.4f}" y1="{ysvg:.4f}" x2="{v.x:.4f}" y2="{ysvg:.4f}"/>\n')
                            f.write(f'  <line class="dim" x1="{Lm:.4f}" y1="{ysvg+offy:.4f}" x2="{v.x:.4f}" y2="{ysvg+offy:.4f}"{arrow}/>\n')
                            pos = placer.place((Lm+v.x)/2, ysvg+offy-font_dim_cm*0.3, font_dim_cm*4.5, font_dim_cm*1.9, prio=1, min_dist=max(6.0, font_dim_cm*9))
                            if pos:
                                x,y=pos; f.write(f'  <text class="txtDim" x="{x:.4f}" y="{y:.4f}" text-anchor="middle">{dx:.1f}</text>\n')
                            count+=1
                    if s.ordinate_from_bottom and count<s.max_ordinate_labels:
                        dy = v.y - Bm
                        if dy>0.5:
                            offx=font_dim_cm*0.8
                            f.write(f'  <line class="aux" x1="{v.x:.4f}" y1="{svg_y(Bm):.4f}" x2="{v.x:.4f}" y2="{svg_y(v.y):.4f}"/>\n')
                            f.write(f'  <line class="dim" x1="{v.x+offx:.4f}" y1="{svg_y(Bm):.4f}" x2="{v.x+offx:.4f}" y2="{svg_y(v.y):.4f}"{arrow}/>\n')
                            pos = placer.place(v.x+offx+font_dim_cm*0.4, (svg_y(Bm)+svg_y(v.y))/2, font_dim_cm*4.5, font_dim_cm*1.9, prio=1, min_dist=max(6.0, font_dim_cm*9))
                            if pos:
                                x,y=pos; f.write(f'  <text class="txtDim" x="{x:.4f}" y="{y:.4f}" text-anchor="middle" dominant-baseline="middle">{dy:.1f}</text>\n')
                            count+=1
                f.write('</g>\n\n')

            # ===== CAPA 5: IDs Y PUNTOS =====
            f.write('<g id="capa-ids-vertices">\n')
            dot_r = max(0.06, font_id_cm*0.28)
            
            if s.show_vertex_dots:
                for idx, v in enumerate(verts_2d):
                    f.write(f'  <circle cx="{v.x:.4f}" cy="{svg_y(v.y):.4f}" r="{dot_r:.4f}" fill="{ID_COLOR}"/>\n')
            
            # IDs centrados en las líneas
            if s.show_ids:
                max_ids = max(0, min(s.max_vertex_ids, len(verts_2d)))
                step_ids = max(1, int(math.ceil(len(verts_2d)/max(1, max_ids))))
                
                if s.center_ids_on_edges and len(edges) > 0:
                    # IDs centrados en cada línea
                    edge_step = max(1, len(edges) // max_ids)
                    edge_count = 0
                    
                    for idx, (i0, i1) in enumerate(edges):
                        if idx % edge_step != 0 or edge_count >= max_ids:
                            continue
                        
                        v0, v1 = verts_2d[i0], verts_2d[i1]
                        mid = (v0 + v1) * 0.5
                        
                        # Calcular offset perpendicular pequeño
                        dirv = v1 - v0
                        if dirv.length == 0: continue
                        
                        normal = Vector((-dirv.y, dirv.x)).normalized()
                        
                        # Decidir lado del offset según centroide
                        to_centroid = centroid - mid
                        if normal.dot(to_centroid) < 0:
                            normal = -normal
                        
                        offset_small = font_id_cm * 1.2
                        base = mid + normal * offset_small
                        
                        bw = font_id_cm * 4.0
                        bh = font_id_cm * 1.8
                        
                        pos = placer.place(base.x, svg_y(base.y), bw, bh, prio=2, rings=8, step=int(max(4, font_id_cm*8)), min_dist=max(5.0, font_id_cm*9))
                        if pos:
                            x, y = pos
                            # Mostrar ambos índices del edge
                            f.write(f'  <text class="txtID" x="{x:.4f}" y="{y:.4f}" text-anchor="middle" dominant-baseline="middle">{i0}-{i1}</text>\n')
                            edge_count += 1
                else:
                    # IDs en vértices (modo tradicional)
                    quad_cycle = [(1,1),(-1,1),(1,-1),(-1,-1)]
                    qidx = 0
                    
                    for idx, v in enumerate(verts_2d):
                        if idx % step_ids != 0:
                            continue
                        
                        q = quad_cycle[qidx % 4]
                        qidx += 1
                        off = Vector((q[0] * font_id_cm * 1.5, q[1] * font_id_cm * 0.9))
                        
                        dens = placer.local_density(v.x + off.x, v.y + off.y, radius=10)
                        local = 1.0 if dens <= 2 else (0.85 if dens <= 5 else 0.70)
                        bw = font_id_cm * 3.6 * local
                        bh = font_id_cm * 1.7 * local
                        
                        pos = placer.place(v.x + off.x, svg_y(v.y + off.y), bw, bh, prio=2, rings=8, step=int(max(4, font_id_cm*8)), min_dist=max(5.0, font_id_cm*9))
                        if pos:
                            x, y = pos
                            f.write(f'  <text class="txtID" x="{x:.4f}" y="{y:.4f}" text-anchor="middle" dominant-baseline="middle">{idx}</text>\n')

            # Rótulo
            if s.show_titleblock:
                tb_w = min(8.0, width_cm*0.42)
                tb_h = font_main_cm*7.0
                tb_x = s.margin_cm
                tb_y = s.margin_cm
                f.write(f'  <rect x="{tb_x:.4f}" y="{svg_y(tb_y+tb_h):.4f}" width="{tb_w:.4f}" height="{tb_h:.4f}" stroke="{EDGE_COLOR}" stroke-width="{STROKE_PATTERN:.4f}cm" fill="none"/>\n')
                line = tb_y + tb_h - font_main_cm*0.7
                pad = font_main_cm*0.45
                
                def row(label, value, bold=False):
                    nonlocal line
                    if not value: return
                    txt = f'<tspan font-weight="700">{label}: </tspan>{value}' if bold else f'{label}: {value}'
                    f.write(f'  <text class="txt" x="{tb_x+pad:.4f}" y="{svg_y(line):.4f}" textLength="{tb_w - pad*2:.4f}">{txt}</text>\n')
                    line -= font_main_cm*0.95
                
                row("Proyecto", s.project, True)
                row("Pieza", s.piece)
                row("Talle", s.size)
                row("Cliente", s.client)
                row("Tela", s.fabric)
                row("Color", s.color)
                row("Notas", s.notes)

            f.write('</g>\n')
            f.write('</svg>\n')

        try: bpy.ops.object.mode_set(mode=prev_mode)
        except Exception: pass

        self.report({'INFO'}, f"SVG exportado: {svg_path}")
        return {'FINISHED'}

# -------------------- Panel --------------------
class VIEW3D_PT_pattern_clean_panel(Panel):
    bl_label = "Exporta a SVG"
    bl_category = "Exportar"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    
    def draw(self, context):
        s = context.scene.pattern_clean_settings
        L = self.layout

        box = L.box()
        box.label(text="Datos del patrón", icon='TEXT')
        col = box.column(align=True)
        for prop in ("project","piece","size","client","author","fabric","color","notes"):
            col.prop(s, prop)
        col.prop(s, "show_titleblock")

        box = L.box()
        box.label(text="Exportación 1:1", icon='EXPORT')
        col = box.column(align=True)
        col.prop(s, "projection_mode")
        col.prop(s, "margin_cm")
        col.prop(s, "filename")
        col.prop(s, "doc_unit")

        box = L.box()
        box.label(text="Tipografías", icon='FONT_DATA')
        col = box.column(align=True)
        col.prop(s, "font_size_strategy")
        col.prop(s, "font_pct")
        row = col.row(align=True)
        row.prop(s, "font_dim_ratio")
        row.prop(s, "font_id_ratio")
        col.prop(s, "font_unit_mode")
        row = col.row(align=True)
        row.prop(s, "font_main_cm")
        row.prop(s, "font_dim_cm")
        row.prop(s, "font_id_cm")

        box = L.box()
        box.label(text="Cotas y Medidas", icon='DRIVER_DISTANCE')
        col = box.column(align=True)
        row = col.row(align=True)
        row.prop(s, "show_edge_lengths")
        row.prop(s, "max_edge_labels")
        col.prop(s, "min_edge_len_cm")
        
        col.separator()
        col.label(text="Separación medidas:")
        row = col.row(align=True)
        row.prop(s, "internal_offset_cm")
        row.prop(s, "external_offset_cm")

        box = L.box()
        box.label(text="IDs y Vértices", icon='LINENUMBERS_ON')
        col = box.column(align=True)
        row = col.row(align=True)
        row.prop(s, "show_ids")
        row.prop(s, "max_vertex_ids")
        col.prop(s, "show_vertex_dots")
        col.prop(s, "center_ids_on_edges")

        box = L.box()
        box.label(text="Medidas a bordes (opcional)", icon='ORIENTATION_VIEW')
        col = box.column(align=True)
        col.prop(s, "show_ordinate")
        row = col.row(align=True)
        row.prop(s, "ordinate_from_left")
        row.prop(s, "ordinate_from_bottom")
        col.prop(s, "max_ordinate_labels")

        L.separator()
        L.operator(OBJECT_OT_export_pattern_clean.bl_idname, icon='EXPORT', text="Exportar Patrón SVG")

# -------------------- Registro --------------------
classes = (PatternCleanSettings, OBJECT_OT_export_pattern_clean, VIEW3D_PT_pattern_clean_panel)

def register():
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.Scene.pattern_clean_settings = PointerProperty(type=PatternCleanSettings)

def unregister():
    del bpy.types.Scene.pattern_clean_settings
    for c in reversed(classes):
        bpy.utils.unregister_class(c)

if __name__ == "__main__":
    register()
