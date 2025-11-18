bl_info = {
    "name": "Patronaje: Remera de Diseño de Residuo Cero - Patternmaking: Zero-Waste T-Shirt",
    "blender": (3, 6, 0),
    "category": "Add Mesh",
    "version": (3, 1, 0),
    "author": "Mauro Menchón",
    "description": "Patronaje de remeras de diseño de residuo cero, mediante edición de proporciones, ingreso de datos manuales y restricciones opcionales",
    "location": "View3D > N-Panel > Patronaje: Remera de Diseño de Residuo Cero",
}

import bpy
import bmesh
import math
import json
from bpy.props import FloatProperty, BoolProperty, PointerProperty, StringProperty
from bpy.types import PropertyGroup, Panel, Operator
from bpy_extras.io_utils import ExportHelper, ImportHelper

# === Geometría base (no tocar) ===
PATRON_DATA_ORIGINAL = [
    (-89.4295674999999, 108.368099999),  # 0 sup izq
    # Curva superior izquierda (manga)
    (-89.4295674999999, 46.210293973832),  # 1 inicio manga
    (-85.4717625, 45.924545373832),
    (-79.56484300000002, 45.106066473832),
    (-70.62415600000001, 43.590944473832),
    (-60.612256, 41.706009473832),
    (-50.739038, 39.683699973832),
    (-45.912316, 38.499673973832),
    (-45.912316, 38.40),  # 8 (sisa)
    (-50.739038, 39.60),
    (-60.612256, 41.60),
    (-70.62415600000001, 43.50),
    (-79.56484300000002, 45.00),
    (-85.4717625, 45.80),
    (-89.4295674999999, 46.10),   # 14 (costura espalda)
    (-89.4295674999999, 0.0),     # 15 inf izq
    (0.0, 0.0),                    # 16 inf der (ORIGEN deseado)
    # Curva interna derecha (cuello)
    (0.0, 48.81875597), # 17
    (-1.61574627, 48.94363393),
    (-3.22292108, 49.25368203),
    (-5.19177542, 50.00156821),
    (-7.36759500, 51.29351360),
    (-9.19916964, 52.97313001),
    (-10.69661122, 54.96572999),
    (-11.87160416, 57.19749147),
    (-12.73489788, 59.59486630),
    (-13.30018230, 62.08450426),
    (-13.57806829, 64.59372045),
    (-13.52570075, 67.38230419),
    (-13.04997109, 70.42167816),
    (-12.40017228, 72.64027494),
    (-12.32340131, 72.65777902),  # 31 base cuello
    (-12.97174391, 70.44492978),
    (-13.44602725, 67.41508375),
    (-13.49814071, 64.63712349),
    (-13.22129670, 62.13781068),
    (-12.65811112, 59.65731164),
    (-11.79838684, 57.26972847),
    (-10.62900278, 55.04849795),
    (-9.13989736, 53.06685893),
    (-7.31994600, 51.39777534),
    (-5.15645058, 50.11334673),
    (-3.20022792, 49.37039591),
    (-1.60529273, 49.06294801),
    (0.0, 48.94875597), # 44
    (0.0, 108.368099999),  # 45 sup der
]

CURVE_UPPER_LEFT_INDICES = list(range(1, 15))   # Manga
CURVE_INTERNAL_RIGHT_INDICES = list(range(17, 45))  # Cuello

def get_bounds(data):
    xs = [p[0] for p in data]; ys = [p[1] for p in data]
    return {'width': max(xs) - min(xs), 'height': max(ys) - min(ys)}

ORIGINAL_BOUNDS = get_bounds(PATRON_DATA_ORIGINAL)

def redistribute_curve_vertices(curve_points, equidistant=True):
    if not equidistant or len(curve_points) < 3:
        return curve_points
    dists = [0.0]
    for i in range(1, len(curve_points)):
        x0, y0 = curve_points[i-1]; x1, y1 = curve_points[i]
        dists.append(dists[-1] + math.hypot(x1-x0, y1-y0))
    total = dists[-1]
    if total == 0.0:
        return curve_points
    seg = total / (len(curve_points)-1)
    out = [curve_points[0]]
    j = 1
    for k in range(1, len(curve_points)-1):
        target = k * seg
        while j < len(curve_points) and dists[j] < target:
            j += 1
        j = min(j, len(curve_points)-1)
        x0,y0 = curve_points[j-1]; x1,y1 = curve_points[j]
        t = 0.0 if dists[j] == dists[j-1] else (target - dists[j-1])/(dists[j]-dists[j-1])
        out.append((x0 + t*(x1-x0), y0 + t*(y1-y0)))
    out.append(curve_points[-1])
    return out

# ========= Auto Update =========
def _active_mesh(context):
    obj = context.active_object
    return obj if (obj and obj.type == 'MESH') else None

def _maybe_auto_update(self, context):
    try:
        p = getattr(context.scene, "patron_props", None)
        if not p or not p.auto_update:
            return
        if _active_mesh(context):
            bpy.ops.mesh.update_patron()
    except Exception:
        pass

# ========= Propiedades =========
class PatronShapeProperties(PropertyGroup):
    # Dimensiones (cm)
    pattern_width:  FloatProperty(name="Ancho del Patrón (cm)", default=67.5, min=10.0, max=400.0, step=0.5, precision=1, update=_maybe_auto_update)
    pattern_height: FloatProperty(name="Alto del Patrón (cm)",  default=80.0, min=10.0, max=400.0, step=0.5, precision=1, update=_maybe_auto_update)
    mantener_proporcion: BoolProperty(name="Mantener proporción original", default=False, update=_maybe_auto_update)

    # Manga
    usar_mitad_auto: BoolProperty(name="Profundidad = 1/2 ancho (auto)", default=True, update=_maybe_auto_update)
    curve_upper_depth_cm: FloatProperty(name="Profundidad Manga (cm)", default=30.0, min=0.1, max=400.0, step=0.5, precision=1, update=_maybe_auto_update)
    manga_usar_escala_x: BoolProperty(name="Usar Escala X en manga", default=False, update=_maybe_auto_update)
    manga_limitar_x_a_mitad: BoolProperty(name="Limitar X a 1/2 del ancho", default=True, update=_maybe_auto_update)
    curve_upper_scale_x: FloatProperty(name="Escala Manga X", default=1.0, min=0.1, max=5.0, step=0.05, precision=2, update=_maybe_auto_update)
    curve_upper_scale_y: FloatProperty(name="Escala Manga Y", default=1.0, min=0.1, max=5.0, step=0.05, precision=2, update=_maybe_auto_update)
    curve_upper_position_y: FloatProperty(name="Posición Vertical Manga (cm)", default=0.0, min=-20.0, max=20.0, step=0.5, precision=1, update=_maybe_auto_update)
    manga_equidistante: BoolProperty(name="Manga Equidistante", default=False, update=_maybe_auto_update)
    lock_manga_lengths: BoolProperty(name="Bloquear la relación entre la sisa y la costura de la espalda", default=False, update=_maybe_auto_update)

    # Cuello
    cuello_seguir_patron: BoolProperty(name="Cuello sigue el escalado del patrón", default=True, update=_maybe_auto_update)
    cuello_scale_x: FloatProperty(name="Escala Cuello X", default=1.0, min=0.1, max=5.0, step=0.02, precision=2, update=_maybe_auto_update)
    cuello_scale_y: FloatProperty(name="Escala Cuello Y", default=1.0, min=0.1, max=5.0, step=0.02, precision=2, update=_maybe_auto_update)
    cuello_profundidad_cm: FloatProperty(name="Profundidad Cuello (cm)", default=0.0, min=0.0, max=200.0, step=0.5, precision=1, update=_maybe_auto_update)
    curve_internal_position_y: FloatProperty(name="Posición Vertical del cuello (cm)", default=0.0, min=-15.0, max=15.0, step=0.5, precision=1, update=_maybe_auto_update)
    cuello_equidistante: BoolProperty(name="Cuello Equidistante", default=False, update=_maybe_auto_update)

    # Límite fijo 2 cm (superior e inferior)
    cuello_limitar_altura: BoolProperty(
        name="Limitar altura del cuello (h + 2 cm)",
        description="Si está activo, el cuello no puede acercarse al borde superior más que h + 2 cm. Desactivar para permitir escalas Y más libres.",
        default=True, update=_maybe_auto_update
    )

    # Bloqueo de largos 31/17 (cuello)
    lock_neck_lengths: BoolProperty(
        name="Bloquear la relación entre las medidas del cuello",
        default=False, update=_maybe_auto_update
    )

    # Posición OBJETO (cm)
    pattern_position_x: FloatProperty(name="Posición X (cm)", default=0.0, step=1.0, update=_maybe_auto_update)
    pattern_position_y: FloatProperty(name="Posición Y (cm)", default=0.0, step=1.0, description="En vista superior: eje Y. En vista frontal: profundidad (Y).", update=_maybe_auto_update)
    pattern_position_z: FloatProperty(name="Altura Z (cm)", default=0.0, step=1.0, update=_maybe_auto_update)

    # Vista y preview
    vista_frontal_xz: BoolProperty(name="Generar en vista frontal (XZ)", default=True, update=_maybe_auto_update)
    auto_update: BoolProperty(name="Vista Previa en Tiempo Real", default=True)

    # === Entradas manuales (Manga)
    man_enable_v8_left:   BoolProperty(name="Ingresar manualmente", default=False, update=_maybe_auto_update)
    man_v8_left_cm:       FloatProperty(name="", default=20.0, min=0.0, max=1000.0, precision=1, update=_maybe_auto_update)

    man_enable_v8_bottom: BoolProperty(name="Ingresar manualmente", default=False, update=_maybe_auto_update)
    man_v8_bottom_cm:     FloatProperty(name="", default=25.0, min=0.0, max=1000.0, precision=1, update=_maybe_auto_update)

    man_enable_v14_bottom: BoolProperty(name="Ingresar manualmente", default=False, update=_maybe_auto_update)
    man_v14_bottom_cm:     FloatProperty(name="", default=25.0, min=0.0, max=1000.0, precision=1, update=_maybe_auto_update)

    man_enable_sisa_sisa:  BoolProperty(name="Ingresar manualmente", default=False, update=_maybe_auto_update)
    man_sisa_sisa_cm:      FloatProperty(name="", default=40.0, min=0.0, max=4000.0, precision=1, update=_maybe_auto_update)

    # === Entradas manuales (Cuello)
    man_enable_base:       BoolProperty(name="Ingresar manualmente", default=False, update=_maybe_auto_update)
    man_base_cm:           FloatProperty(name="", default=8.0, min=0.0, max=1000.0, precision=1, update=_maybe_auto_update)

    man_enable_base_total: BoolProperty(name="Ingresar manualmente", default=False, update=_maybe_auto_update)
    man_base_total_cm:     FloatProperty(name="", default=16.0, min=0.0, max=2000.0, precision=1, update=_maybe_auto_update)

    man_enable_len_base:   BoolProperty(name="Ingresar manualmente", default=False, update=_maybe_auto_update)
    man_len_base_cm:       FloatProperty(name="", default=20.0, min=0.0, max=2000.0, precision=1, update=_maybe_auto_update)

    man_enable_len_17:     BoolProperty(name="Ingresar manualmente", default=False, update=_maybe_auto_update)
    man_len_17_cm:         FloatProperty(name="", default=20.0, min=0.0, max=2000.0, precision=1, update=_maybe_auto_update)

# === Lista de propiedades a guardar/cargar ===
PATRON_SETTINGS_KEYS = [
    # Dimensiones
    "pattern_width", "pattern_height", "mantener_proporcion",
    # Manga
    "usar_mitad_auto", "curve_upper_depth_cm",
    "manga_usar_escala_x", "manga_limitar_x_a_mitad",
    "curve_upper_scale_x", "curve_upper_scale_y",
    "curve_upper_position_y", "manga_equidistante",
    "lock_manga_lengths",
    # Cuello
    "cuello_seguir_patron", "cuello_scale_x", "cuello_scale_y",
    "cuello_profundidad_cm", "curve_internal_position_y",
    "cuello_equidistante", "cuello_limitar_altura", "lock_neck_lengths",
    # Posición objeto
    "pattern_position_x", "pattern_position_y", "pattern_position_z",
    "vista_frontal_xz",
    # Entradas manuales Manga
    "man_enable_v8_left", "man_v8_left_cm",
    "man_enable_v8_bottom", "man_v8_bottom_cm",
    "man_enable_v14_bottom", "man_v14_bottom_cm",
    "man_enable_sisa_sisa", "man_sisa_sisa_cm",
    # Entradas manuales Cuello
    "man_enable_base", "man_base_cm",
    "man_enable_base_total", "man_base_total_cm",
    "man_enable_len_base", "man_len_base_cm",
    "man_enable_len_17", "man_len_17_cm",
]

# ===== Helpers de anclaje/orientación/medición =====
def _apply_orientation_and_anchor(coords_xy_m, anchor_index=16, frontal=False):
    ax, ay = coords_xy_m[anchor_index]
    out = []
    for (x, y) in coords_xy_m:
        lx = x - ax
        ly = y - ay
        out.append((lx, 0.0, ly) if frontal else (lx, ly, 0.0))
    return out

def _measure_cm(props, coords, vidx, lateral_edge='LEFT', decimals=1):
    """coords: ya ANCLADAS en el plano final (XY o XZ).
    Devuelve (distancia_lateral_cm, distancia_desde_borde_inferior_cm)
    usando como 'borde inferior' el mínimo V real de toda la pieza.
    """
    unit_cm_per_m = 100.0

    # Coordenadas del punto a medir y borde inferior real
    if props.vista_frontal_xz:
        x = coords[vidx][0]
        v = coords[vidx][2]  # Z como vertical en vista frontal
        bottom_v = min(c[2] for c in coords)  # borde inferior real
    else:
        x = coords[vidx][0]
        v = coords[vidx][1]  # Y como vertical en vista superior
        bottom_v = min(c[1] for c in coords)  # borde inferior real

    # Bordes laterales de la tela (anclado en 16)
    right_x = 0.0
    left_x  = -(props.pattern_width * 0.01)

    # Distancia vertical desde el borde inferior real
    dist_bottom_cm = max(0.0, (v - bottom_v) * unit_cm_per_m)

    # Distancia lateral hacia el borde solicitado
    if lateral_edge == 'RIGHT':
        dist_lat_cm = max(0.0, (right_x - x) * unit_cm_per_m)
    else:
        dist_lat_cm = max(0.0, (x - left_x) * unit_cm_per_m)

    # Redondeo
    f = 10**decimals
    fmt = lambda val: math.floor(val*f + 0.5)/f
    return fmt(dist_lat_cm), fmt(dist_bottom_cm)

# ===== Núcleo de transformación =====
def transform_pattern_coordinates(props):
    unit = 0.01  # cm -> m
    MIN_GAP_CM = 0.5   # gap mínimo para evitar encimado (0.5 cm)
    MIN_GAP_M  = MIN_GAP_CM * unit

    # 1) Escala global del patrón
    sx_w = (props.pattern_width * unit) / (ORIGINAL_BOUNDS['width'] * 0.05)
    sy_h = (props.pattern_height * unit) / (ORIGINAL_BOUNDS['height'] * 0.05)
    sx = sx_w
    sy = sx_w if props.mantener_proporcion else sy_h

    # 2) Base escalada (XY en metros, sin anclar)
    base = [(x * 0.05 * sx, y * 0.05 * sy) for (x, y) in PATRON_DATA_ORIGINAL]

    # BORDES REALES DE LA TELA (EXCLUYENDO CURVA MANGA)
    # Top = vértices superiores 0 y 45
    top_fabric_y = max(base[0][1], base[45][1])
    # Bottom = vértices inferiores 15 y 16
    bottom_fabric_y = min(base[15][1], base[16][1])

    # 3) Equidistancias opcionales
    if props.manga_equidistante:
        pts = [base[i] for i in CURVE_UPPER_LEFT_INDICES]
        red = redistribute_curve_vertices(pts, True)
        for k, idx in enumerate(CURVE_UPPER_LEFT_INDICES):
            base[idx] = red[k]
    if props.cuello_equidistante:
        pts = [base[i] for i in CURVE_INTERNAL_RIGHT_INDICES]
        red = redistribute_curve_vertices(pts, True)
        for k, idx in enumerate(CURVE_INTERNAL_RIGHT_INDICES):
            base[idx] = red[k]

    # Vértices de referencia
    ax, ay = base[16]
    cx, cy = base[1]
    x8, y8 = base[8]
    y14 = base[14][1]
    neck_cx, neck_cy = base[17]

    # === Factores baseline (MANGA) ===
    max_x_off = max(abs(base[i][0] - cx) for i in CURVE_UPPER_LEFT_INDICES) or 1e-9
    target_depth_cm = (props.pattern_width / 2.0) if props.usar_mitad_auto else min(props.curve_upper_depth_cm, props.pattern_width/2.0)
    x_factor_from_depth = (target_depth_cm * unit) / max_x_off
    if props.manga_usar_escala_x:
        manga_factor_x = props.curve_upper_scale_x
        if props.manga_limitar_x_a_mitad:
            cap_m = (props.pattern_width / 2.0) * unit
            manga_factor_x = min(manga_factor_x, cap_m / max_x_off)
    else:
        manga_factor_x = x_factor_from_depth
    cap_m = (props.pattern_width / 2.0) * unit
    cur_max_y = max(abs(base[i][1] - cy) for i in CURVE_UPPER_LEFT_INDICES) or 1e-9
    manga_factor_y = min(props.curve_upper_scale_y, cap_m / cur_max_y)

    # === Overrides manuales (MANGA, ancho) ===
    left_x  = -(props.pattern_width * unit)
    if props.man_enable_sisa_sisa and props.man_sisa_sisa_cm > 0.0:
        target_half_m = (props.man_sisa_sisa_cm * unit) / 2.0
        target_x_anchor = -target_half_m
        denom = (x8 - cx) or 1e-9
        manga_factor_x = (target_x_anchor + ax - cx) / denom
    elif props.man_enable_v8_left and props.man_v8_left_cm >= 0.0:
        target_left_m = props.man_v8_left_cm * unit
        target_x_anchor = left_x + target_left_m
        denom = (x8 - cx) or 1e-9
        manga_factor_x = (target_x_anchor + ax - cx) / denom

    if props.manga_limitar_x_a_mitad:
        manga_factor_x = min(manga_factor_x, (props.pattern_width * unit / 2.0) / max_x_off)

    # === MANGA: independencia vertical v8/v14 con preservación de GAP ===
    y8_no_off  = cy + (y8  - cy) * manga_factor_y
    y14_no_off = cy + (y14 - cy) * manga_factor_y

    # Usamos SIEMPRE el borde de la tela como referencia para largos verticales
    bottom_edge_for_manga = bottom_fabric_y

    s_my = 1.0
    off_my = 0.01 * props.curve_upper_position_y

    L8_enabled  = props.man_enable_v8_bottom
    L14_enabled = props.man_enable_v14_bottom
    L8_m  = props.man_v8_bottom_cm  * unit
    L14_m = props.man_v14_bottom_cm * unit

    if L8_enabled and L14_enabled and not props.lock_manga_lengths:
        denom = (y8_no_off - y14_no_off)
        if abs(denom) > 1e-9:
            s_my = (L8_m - L14_m) / denom
        else:
            s_my = 1.0
        off_my = (bottom_edge_for_manga + L14_m) - (cy + s_my * (y14_no_off - cy))
    else:
        s_my = 1.0
        if L8_enabled:
            off_my = (bottom_edge_for_manga + L8_m) - y8_no_off
        elif L14_enabled:
            off_my = (bottom_edge_for_manga + L14_m) - y14_no_off
        else:
            off_my = max(-0.20, min(0.20, off_my))

    # >>> Preservar GAP manga (evitar encimado de v8 y v14)
    gap_base_m = abs(y8_no_off - y14_no_off)
    if gap_base_m < 1e-9:
        gap_base_m = 1e-9
    s_min_gap = MIN_GAP_M / gap_base_m
    if s_my < s_min_gap:
        s_my = s_min_gap
        if L8_enabled and L14_enabled and not props.lock_manga_lengths:
            off_my = (bottom_edge_for_manga + L14_m) - (cy + s_my * (y14_no_off - cy))
        elif L8_enabled:
            off_my = (bottom_edge_for_manga + L8_m) - (cy + s_my * (y8_no_off - cy))
        elif L14_enabled:
            off_my = (bottom_edge_for_manga + L14_m) - (cy + s_my * (y14_no_off - cy))

    # >>> Límites 2 cm para la MANGA (#1, sisa #8 y costura espalda #14)
    y1_orig   = base[1][1]
    y1_no_off = cy + (y1_orig - cy) * manga_factor_y

    margin_top    = 0.02  # 2 cm
    margin_bottom = 0.02  # 2 cm

    # Restrición superior: ninguno de los 3 puede superar top_fabric_y - 2cm
    off_max1 = top_fabric_y - margin_top - (cy + s_my * (y1_no_off  - cy))
    off_max2 = top_fabric_y - margin_top - (cy + s_my * (y8_no_off  - cy))
    off_max3 = top_fabric_y - margin_top - (cy + s_my * (y14_no_off - cy))
    allowed_off_max = min(off_max1, off_max2, off_max3)

    # Restricción inferior: sisa y costura de espalda no pueden bajar de bottom_fabric_y + 2cm
    off_min_8  = bottom_fabric_y + margin_bottom - (cy + s_my * (y8_no_off  - cy))
    off_min_14 = bottom_fabric_y + margin_bottom - (cy + s_my * (y14_no_off - cy))
    allowed_off_min = max(off_min_8, off_min_14)

    # Clampear off_my dentro del rango permitido
    if allowed_off_min > allowed_off_max:
        # Si las restricciones se cruzan, priorizamos que no se salgan por arriba
        off_my = min(off_my, allowed_off_max)
    else:
        if off_my > allowed_off_max:
            off_my = allowed_off_max
        if off_my < allowed_off_min:
            off_my = allowed_off_min

    # === Factores baseline (CUELLO) con CAP absoluto mitad de ancho ===
    if props.cuello_seguir_patron:
        def neck_dxdy(idx):
            bx, by = base[idx]; return (bx - neck_cx, by - neck_cy)
    else:
        def neck_dxdy(idx):
            bx, by = base[idx]; return ((bx - neck_cx)/sx, (by - neck_cy)/sy)

    neck_base_max_x = max(abs(neck_dxdy(i)[0]) for i in CURVE_INTERNAL_RIGHT_INDICES) or 1e-9
    half_width_m = (props.pattern_width * unit) / 2.0
    depth_cm_cap = min(props.cuello_profundidad_cm, props.pattern_width / 2.0)
    depth_mult = (depth_cm_cap * unit / neck_base_max_x) if depth_cm_cap > 0.0 else 1.0

    neck_mult_x_total = props.cuello_scale_x * depth_mult
    max_sx_half = half_width_m / neck_base_max_x
    neck_mult_x_total = min(neck_mult_x_total, max_sx_half)

    neck_mult_y_total = props.cuello_scale_y
    ys_all_tmp = [y for (_, y) in base]
    top_edge_y_tmp = max(ys_all_tmp); bottom_edge_y_tmp = min(ys_all_tmp)
    margin = 0.02
    allowed_gap = (top_edge_y_tmp - margin) - (bottom_edge_y_tmp + margin)
    dy_vals = [neck_dxdy(i)[1] for i in CURVE_INTERNAL_RIGHT_INDICES]
    base_h = max(1e-9, max(dy_vals) - min(dy_vals))
    max_sy = max(0.0, allowed_gap / base_h)
    neck_mult_y_total = min(neck_mult_y_total, max_sy)

    # === Overrides manuales (CUELLO, base en X) + CAP mitad de ancho ===
    dx31, _ = neck_dxdy(31)
    if props.man_enable_base_total and props.man_base_total_cm > 0.0:
        target_half_m = (props.man_base_total_cm * unit) / 2.0
        target_x_anchor = -target_half_m
        denom = dx31 or 1e-9
        neck_mult_x_total = (target_x_anchor + ax - neck_cx) / denom
    elif props.man_enable_base and props.man_base_cm >= 0.0:
        target_m = props.man_base_cm * unit
        target_x_anchor = -target_m
        denom = dx31 or 1e-9
        neck_mult_x_total = (target_x_anchor + ax - neck_cx) / denom
    neck_mult_x_total = min(neck_mult_x_total, max_sx_half)

    # === Regla frontera sisa para X (si y(17) < y(8)) ===
    y8_actual_manga = cy + s_my * (y8_no_off - cy) + off_my
    y17_no_off_y = neck_cy + neck_dxdy(17)[1] * neck_mult_y_total
    if y17_no_off_y < y8_actual_manga:
        x8_actual = cx + (x8 - cx) * manga_factor_x
        if abs(dx31) > 1e-9:
            sx_frontera = (x8_actual - 0.02 - neck_cx) / dx31
            if neck_mult_x_total > 1.0 and dx31 > 0.0:
                neck_mult_x_total = min(neck_mult_x_total, sx_frontera)
    neck_mult_x_total = min(neck_mult_x_total, max_sx_half)

    # === Aplicar transformaciones base (sin offset de cuello) ===
    out_xy = []
    neck_points_no_off = {}
    for i, (x, y) in enumerate(base):
        nx, ny = x, y
        if i in CURVE_UPPER_LEFT_INDICES:
            nx = cx + (x - cx) * manga_factor_x
            y_scaled = cy + (y - cy) * manga_factor_y
            ny = cy + s_my * (y_scaled - cy) + off_my
        elif i in CURVE_INTERNAL_RIGHT_INDICES:
            dx, dy = neck_dxdy(i)
            nx = neck_cx + dx * neck_mult_x_total
            ny = neck_cy + dy * neck_mult_y_total
            neck_points_no_off[i] = (nx, ny)
        out_xy.append((nx, ny))

    # === Offset/escala vertical del cuello con independencia 31/17 + PRESERVACIÓN DE GAP ===
    if neck_points_no_off:
        bottom_edge_y_before = min(y for (_, y) in out_xy)

        y31_no_off = neck_points_no_off[31][1]
        y17_no_off = neck_points_no_off[17][1]

        L31_enabled = props.man_enable_len_base
        L17_enabled = props.man_enable_len_17
        L31_m = props.man_len_base_cm * unit
        L17_m = props.man_len_17_cm * unit

        s_extra = 1.0
        desired_off_m = props.curve_internal_position_y * unit

        if L31_enabled and L17_enabled and not props.lock_neck_lengths:
            denom = (y31_no_off - y17_no_off)
            if abs(denom) > 1e-9:
                s_extra = (L31_m - L17_m) / denom
            else:
                s_extra = 1.0
            desired_off_m = (bottom_edge_y_before + L17_m) - (neck_cy + s_extra * (y17_no_off - neck_cy))

            ys_all2 = [y for (_, y) in out_xy]
            top_edge_y = max(ys_all2); bottom_edge_y = min(ys_all2)
            margin = 0.02
            neck_y_vals = [p[1] for p in neck_points_no_off.values()]
            dy_cur_max = max(neck_y_vals) - neck_cy
            dy_cur_min = min(neck_y_vals) - neck_cy
            s_top = (top_edge_y - margin - (neck_cy + desired_off_m)) / (dy_cur_max if dy_cur_max != 0 else 1e-9)
            s_bottom = (bottom_edge_y + margin - (neck_cy + desired_off_m)) / (dy_cur_min if dy_cur_min != 0 else -1e-9)
            s_allowed = min(s_top if s_top > 0 else 1e9, s_bottom if s_bottom > 0 else 1e9)
            s_extra = max(0.0, min(s_extra, s_allowed))

            allowed_max_31 = out_xy[0][1] - 0.02
            y31_after = neck_cy + s_extra * (y31_no_off - neck_cy) + desired_off_m
            if y31_after > allowed_max_31:
                desired_off_m = allowed_max_31 - (neck_cy + s_extra * (y31_no_off - neck_cy))

            for i in CURVE_INTERNAL_RIGHT_INDICES:
                nx, ny = out_xy[i]
                ny = neck_cy + s_extra * (ny - neck_cy) + desired_off_m
                out_xy[i] = (nx, ny)

        else:
            if L31_enabled and not L17_enabled:
                target_y31 = bottom_edge_y_before + L31_m
                delta = target_y31 - y31_no_off
            elif L17_enabled and not L31_enabled:
                target_y17 = bottom_edge_y_before + L17_m
                delta = target_y17 - y17_no_off
            elif props.lock_neck_lengths and (L31_enabled or L17_enabled):
                if L31_enabled and L17_enabled:
                    target_y17 = bottom_edge_y_before + L17_m
                    delta = target_y17 - y17_no_off
                elif L31_enabled:
                    target_y31 = bottom_edge_y_before + L31_m
                    delta = target_y31 - y31_no_off
                else:
                    target_y17 = bottom_edge_y_before + L17_m
                    delta = target_y17 - y17_no_off
            else:
                delta = max(-0.15, min(0.15, props.curve_internal_position_y * unit))

            ys_all2 = [y for (_, y) in out_xy]
            top_edge_y = max(ys_all2); bottom_edge_y = min(ys_all2)
            margin = 0.02

            neck_y_vals = [p[1] for p in neck_points_no_off.values()]
            y_min_no_off = min(neck_y_vals)
            y_max_no_off = max(neck_y_vals)

            delta_max_up   = (top_edge_y - margin)    - y_max_no_off
            delta_max_down = (bottom_edge_y + margin) - y_min_no_off
            delta = max(delta_max_down, min(delta, delta_max_up))

            allowed_max_31 = out_xy[0][1] - 0.02
            if y31_no_off + delta > allowed_max_31:
                delta = allowed_max_31 - y31_no_off

            for i in CURVE_INTERNAL_RIGHT_INDICES:
                nx, ny = out_xy[i]
                ny = ny + delta
                out_xy[i] = (nx, ny)

    # Contención vertical absoluta con margen 2 cm para el cuello
    ys_all = [y for (_, y) in out_xy]
    top_edge_y = max(ys_all)
    bottom_edge_y = min(ys_all)
    margin = 0.02
    allowed_max = top_edge_y - margin
    allowed_min = bottom_edge_y + margin
    neck_max = max(out_xy[i][1] for i in CURVE_INTERNAL_RIGHT_INDICES)
    neck_min = min(out_xy[i][1] for i in CURVE_INTERNAL_RIGHT_INDICES)
    corr = 0.0
    if neck_max > allowed_max:
        corr = allowed_max - neck_max
    elif neck_min < allowed_min:
        corr = allowed_min - neck_min
    if corr != 0.0:
        for i in CURVE_INTERNAL_RIGHT_INDICES:
            nx, ny = out_xy[i]
            out_xy[i] = (nx, ny + corr)

    # 5) Anclar y orientar
    out_xyz = _apply_orientation_and_anchor(out_xy, anchor_index=16, frontal=props.vista_frontal_xz)
    return out_xyz

# ===== Construcción de malla y operadores =====
def _build_mesh_from_coords(coords_xyz):
    mesh = bpy.data.meshes.new('Patron_Profesional')
    bm = bmesh.new()
    verts = [bm.verts.new(c) for c in coords_xyz]
    bm.verts.ensure_lookup_table()
    for i in range(len(verts)):
        bm.edges.new([verts[i], verts[(i + 1) % len(verts)]])
    bm.verts.ensure_lookup_table(); bm.edges.ensure_lookup_table()
    try:
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
    except Exception:
        pass
    bm.normal_update(); bm.to_mesh(mesh); bm.free()
    return mesh

def _apply_object_location_from_props(obj, props):
    unit = 0.01
    obj.location = (props.pattern_position_x*unit,
                    props.pattern_position_y*unit,
                    props.pattern_position_z*unit)

class MESH_OT_add_patron_shape(Operator):
    bl_idname = "mesh.add_patron_shape"
    bl_label = "Crear Patrón"
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        p = context.scene.patron_props
        coords = transform_pattern_coordinates(p)
        mesh = _build_mesh_from_coords(coords)
        obj = bpy.data.objects.new(f'Patron_{p.pattern_width:.1f}x{p.pattern_height:.1f}cm', mesh)
        context.collection.objects.link(obj)
        bpy.context.view_layer.objects.active = obj; obj.select_set(True)
        _apply_object_location_from_props(obj, p)
        self.report({'INFO'}, 'Patrón creado (origen en corner inferior derecho)')
        return {'FINISHED'}

class MESH_OT_update_patron(Operator):
    bl_idname = "mesh.update_patron"
    bl_label = "Actualizar Patrón"
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        p = context.scene.patron_props
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            self.report({'WARNING'}, 'Seleccioná un objeto mesh para actualizar')
            return {'CANCELLED'}
        coords = transform_pattern_coordinates(p)
        mesh = _build_mesh_from_coords(coords)
        obj.data = mesh
        _apply_object_location_from_props(obj, p)
        self.report({'INFO'}, 'Patrón actualizado')
        return {'FINISHED'}

# ====== GUARDAR / CARGAR MEDIDAS ======

class PATRON_OT_save_settings(Operator, ExportHelper):
    """Guardar todas las medidas actuales en un archivo JSON"""
    bl_idname = "patron.save_settings"
    bl_label = "Guardar medidas..."
    filename_ext = ".json"

    filter_glob: StringProperty(
        default="*.json",
        options={'HIDDEN'},
        maxlen=255,
    )

    def execute(self, context):
        p = context.scene.patron_props
        data = {}
        for key in PATRON_SETTINGS_KEYS:
            if hasattr(p, key):
                data[key] = getattr(p, key)
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.report({'ERROR'}, f"No se pudo guardar el archivo: {e}")
            return {'CANCELLED'}
        self.report({'INFO'}, f"Medidas guardadas en {self.filepath}")
        return {'FINISHED'}

class PATRON_OT_load_settings(Operator, ImportHelper):
    """Cargar medidas desde un archivo JSON previamente guardado"""
    bl_idname = "patron.load_settings"
    bl_label = "Cargar medidas..."
    filename_ext = ".json"

    filter_glob: StringProperty(
        default="*.json",
        options={'HIDDEN'},
        maxlen=255,
    )

    def execute(self, context):
        p = context.scene.patron_props
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            self.report({'ERROR'}, f"No se pudo leer el archivo: {e}")
            return {'CANCELLED'}

        # Evitamos loops excesivos: desactivamos auto_update mientras cargamos
        auto_prev = p.auto_update
        p.auto_update = False
        try:
            for key, value in data.items():
                if key in PATRON_SETTINGS_KEYS and hasattr(p, key):
                    setattr(p, key, value)
        except Exception as e:
            self.report({'ERROR'}, f"Error aplicando medidas: {e}")
            p.auto_update = auto_prev
            return {'CANCELLED'}

        p.auto_update = auto_prev
        # Forzamos una actualización del mesh si hay uno activo
        if _active_mesh(context):
            bpy.ops.mesh.update_patron()

        self.report({'INFO'}, f"Medidas cargadas desde {self.filepath}")
        return {'FINISHED'}

# ===== Paneles =====
class VIEW3D_PT_patron_main_panel(Panel):
    bl_label = "🧵 Patronaje: Remera de diseño de residuo cero - Zero Waste T-shirt"
    bl_idname = "VIEW3D_PT_PAT_MAIN"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Remera de Diseño de Residuo Cero"
    def draw(self, context):
        layout = self.layout; p = context.scene.patron_props

        box = layout.box()
        r = box.row(); r.scale_y = 1.2
        r.operator("mesh.add_patron_shape", icon='ADD', text="Crear Nuevo Patrón")
        r = box.row()
        r.operator("mesh.update_patron", icon='FILE_REFRESH', text="Actualizar Patrón")
        r.prop(p, "auto_update", text="", icon='AUTO')

        box = layout.box()
        box.label(text="📏 Dimensiones", icon='FULLSCREEN_ENTER')
        col = box.column(align=True)
        row = col.row(align=True); row.prop(p, "pattern_width", text="Ancho")
        row2 = col.row(align=True); row2.enabled = not p.mantener_proporcion
        row2.prop(p, "pattern_height", text="Alto")
        col.prop(p, "mantener_proporcion")
        col.separator()
        col.prop(p, "vista_frontal_xz", text="Generar en vista frontal (XZ)")

        # NUEVA SECCIÓN: Guardar / Cargar medidas
        box2 = layout.box()
        box2.label(text="💾 Guardar / Cargar medidas")
        row = box2.row(align=True)
        row.operator("patron.save_settings", icon='FILE_TICK', text="Guardar medidas...")
        row.operator("patron.load_settings", icon='FILE_FOLDER', text="Cargar medidas...")

class VIEW3D_PT_patron_curves_panel(Panel):
    bl_label = "🔄 Control de Formas"
    bl_idname = "VIEW3D_PT_PAT_CURVES"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Remera de Diseño de Residuo Cero"
    bl_parent_id = "VIEW3D_PT_PAT_MAIN"
    def draw(self, context):
        layout = self.layout; p = context.scene.patron_props

        coords = transform_pattern_coordinates(p)

        # ========== MANGA ==========
        b = layout.box(); b.label(text="👔 Manga", icon='CURVE_BEZCURVE')
        mbox = b.box(); mbox.label(text="📐 Medidas clave (en cm)")

        dx8_left_cm, dy8_bottom_cm = _measure_cm(p, coords, 8, lateral_edge='LEFT', decimals=1)
        dx8_right_cm, _            = _measure_cm(p, coords, 8, lateral_edge='RIGHT', decimals=1)
        sisa_sisa = round(dx8_right_cm * 2.0, 1)
        _dx14_left_cm, dy14_bottom_cm = _measure_cm(p, coords, 14, lateral_edge='LEFT', decimals=1)

        col = mbox.column(align=True)
        row = col.row(align=True); row.label(text=f"Distancia desde borde lateral a sisa: {dx8_left_cm:.1f}")
        sub = row.row(align=True); sub.prop(p, "man_enable_v8_left", text=""); sub.prop(p, "man_v8_left_cm", text="cm")

        row = col.row(align=True); row.label(text=f"Distancia desde borde inferior a sisa: {dy8_bottom_cm:.1f}")
        sub = row.row(align=True); sub.prop(p, "man_enable_v8_bottom", text=""); sub.prop(p, "man_v8_bottom_cm", text="cm")

        row = col.row(align=True); row.label(text=f"Costura de espalda desde el borde inferior de la tela: {dy14_bottom_cm:.1f}")
        sub = row.row(align=True); sub.prop(p, "man_enable_v14_bottom", text=""); sub.prop(p, "man_v14_bottom_cm", text="cm")

        row = col.row(align=True); row.prop(p, "lock_manga_lengths", text="Bloquear la relación entre la sisa y la costura de la espalda")

        row = col.row(align=True); row.label(text=f"Distancia de sisa a sisa: {sisa_sisa:.1f}")
        sub = row.row(align=True); sub.prop(p, "man_enable_sisa_sisa", text=""); sub.prop(p, "man_sisa_sisa_cm", text="cm")

        c = b.column(align=True)
        c.prop(p, "manga_usar_escala_x")
        row = c.row(align=True)
        row.enabled = (not p.manga_usar_escala_x) and (not p.usar_mitad_auto)
        c2 = c.row(align=True); c2.enabled = (not p.manga_usar_escala_x); c2.prop(p, "usar_mitad_auto")
        row.prop(p, "curve_upper_depth_cm")
        half = p.pattern_width / 2.0
        applied = half if p.usar_mitad_auto else min(p.curve_upper_depth_cm, half)
        if not p.manga_usar_escala_x:
            c.label(text=f"Profundidad aplicada: {applied:.1f} cm (1/2 ancho = {half:.1f} cm)")
        rowx = c.row(align=True); rowx.enabled = p.manga_usar_escala_x; rowx.prop(p, "curve_upper_scale_x", slider=True)
        c.prop(p, "manga_limitar_x_a_mitad")
        c.separator(); c.prop(p, "curve_upper_scale_y", text="Escala Y (limitada)", slider=True)
        c.prop(p, "curve_upper_position_y")

        # ========== CUELLO ==========
        b2 = layout.box(); b2.label(text="👕 Cuello", icon='CURVE_BEZCIRCLE')
        mbox2 = b2.box(); mbox2.label(text="📐 Medidas clave (en cm)")

        dx31_right_cm, dy31_bottom_cm = _measure_cm(p, coords, 31, lateral_edge='RIGHT', decimals=1)
        _dx17_right_cm, dy17_bottom_cm = _measure_cm(p, coords, 17, lateral_edge='RIGHT', decimals=1)
        base_total = round(dx31_right_cm * 2.0, 1)

        col2 = mbox2.column(align=True)
        row = col2.row(align=True); row.label(text=f"Base del cuello: {dx31_right_cm:.1f}")
        sub = row.row(align=True); sub.prop(p, "man_enable_base", text=""); sub.prop(p, "man_base_cm", text="cm")

        row = col2.row(align=True); row.label(text=f"Largo, distancia desde el borde inferior hasta la base del cuello: {dy31_bottom_cm:.1f}")
        sub = row.row(align=True); sub.prop(p, "man_enable_len_base", text=""); sub.prop(p, "man_len_base_cm", text="cm")

        row = col2.row(align=True); row.label(text=f"Distancia desde el borde inferior hasta el cuello: {dy17_bottom_cm:.1f}")
        sub = row.row(align=True); sub.prop(p, "man_enable_len_17", text=""); sub.prop(p, "man_len_17_cm", text="cm")

        row = col2.row(align=True); row.label(text=f"Base del cuello total: {base_total:.1f}")
        sub = row.row(align=True); sub.prop(p, "man_enable_base_total", text=""); sub.prop(p, "man_base_total_cm", text="cm")

        c2 = b2.column(align=True)
        c2.prop(p, "cuello_scale_x", slider=True)
        c2.prop(p, "cuello_scale_y", slider=True)
        c2.prop(p, "cuello_profundidad_cm")
        c2.prop(p, "curve_internal_position_y", text="Posición Vertical del cuello")
        c2.prop(p, "lock_neck_lengths", text="Bloquear la relación entre las medidas del cuello")
        c2.prop(p, "cuello_equidistante", text="Vértices Equidistantes")

class VIEW3D_PT_patron_position_panel(Panel):
    bl_label = "🎯 Posición en Escena"
    bl_idname = "VIEW3D_PT_PAT_POS"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Remera de Diseño de Residuo Cero"
    bl_parent_id = "VIEW3D_PT_PAT_MAIN"
    def draw(self, context):
        layout = self.layout; p = context.scene.patron_props
        b = layout.box(); b.label(text="📍 Posición (del OBJETO)", icon='OBJECT_ORIGIN')
        c = b.column(align=True)
        c.prop(p, "pattern_position_x", text="X")
        c.prop(p, "pattern_position_y", text="Y / Profundidad")
        c.prop(p, "pattern_position_z", text="Z")

def menu_func(self, context):
    self.layout.separator()
    self.layout.operator(MESH_OT_add_patron_shape.bl_idname, icon='MESH_PLANE')

def register():
    bpy.utils.register_class(PatronShapeProperties)
    bpy.utils.register_class(MESH_OT_add_patron_shape)
    bpy.utils.register_class(MESH_OT_update_patron)
    bpy.utils.register_class(PATRON_OT_save_settings)
    bpy.utils.register_class(PATRON_OT_load_settings)
    bpy.utils.register_class(VIEW3D_PT_patron_main_panel)
    bpy.utils.register_class(VIEW3D_PT_patron_curves_panel)
    bpy.utils.register_class(VIEW3D_PT_patron_position_panel)
    bpy.types.Scene.patron_props = PointerProperty(type=PatronShapeProperties)
    bpy.types.VIEW3D_MT_mesh_add.append(menu_func)

def unregister():
    bpy.types.VIEW3D_MT_mesh_add.remove(menu_func)
    del bpy.types.Scene.patron_props
    bpy.utils.unregister_class(VIEW3D_PT_patron_position_panel)
    bpy.utils.unregister_class(VIEW3D_PT_patron_curves_panel)
    bpy.utils.unregister_class(VIEW3D_PT_patron_main_panel)
    bpy.utils.unregister_class(PATRON_OT_load_settings)
    bpy.utils.unregister_class(PATRON_OT_save_settings)
    bpy.utils.unregister_class(MESH_OT_update_patron)
    bpy.utils.unregister_class(MESH_OT_add_patron_shape)
    bpy.utils.unregister_class(PatronShapeProperties)

if __name__ == "__main__":
    register()
