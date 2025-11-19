bl_info = {
    "name": "Doblar",
    "author": "Mauro Menchón",
    "version": (1, 0, 0),
    "blender": (3, 6, 0),
    "location": "View3D > Sidebar (N) > Doblar",
    "description": "Pliegues por seam, límite topológico estricto (incluye bordes), control por índice y combinación AND/OR con modificador",
    "category": "Mesh",
}

import bpy
import bmesh
from mathutils import Vector, Matrix
import math
from collections import defaultdict, deque
import heapq

# ---------- Utilidades geométricas y loops ----------

def get_seam_edges_indices(obj, use_selected=False):
    me = obj.data
    if use_selected:
        return {e.index for e in me.edges if e.select}
    else:
        return {e.index for e in me.edges if e.use_seam}

def edge_loops_from_edge_set(obj, edge_idx_set):
    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.edges.ensure_lookup_table()
    bm.verts.ensure_lookup_table()

    edges = [bm.edges[i] for i in edge_idx_set if i < len(bm.edges)]
    if not edges:
        bm.free()
        return [], [], []

    vert_to_edges = defaultdict(list)
    for e in edges:
        vert_to_edges[e.verts[0].index].append(e)
        vert_to_edges[e.verts[1].index].append(e)

    visited = set()
    loops_idx_pairs = []

    def follow_loop(start_edge):
        loop_pairs = []
        v0, v1 = start_edge.verts
        visited.add(start_edge.index)
        loop_pairs.append((v0.index, v1.index))
        cur, prev = v1, v0

        # adelante
        while True:
            next_edges = [ed for ed in vert_to_edges[cur.index] if ed.index in edge_idx_set and ed.index not in visited]
            ne = None
            for cand in next_edges:
                a, b = cand.verts
                if (a.index == cur.index and b.index != prev.index) or (b.index == cur.index and a.index != prev.index):
                    ne = cand; break
            if ne is None: break
            a, b = ne.verts
            nxt = b if a.index == cur.index else a
            loop_pairs.append((cur.index, nxt.index))
            visited.add(ne.index)
            prev, cur = cur, nxt

        # atrás
        cur, prev = v0, v1
        while True:
            next_edges = [ed for ed in vert_to_edges[cur.index] if ed.index in edge_idx_set and ed.index not in visited]
            ne = None
            for cand in next_edges:
                a, b = cand.verts
                if (a.index == cur.index and b.index != prev.index) or (b.index == cur.index and a.index != prev.index):
                    ne = cand; break
            if ne is None: break
            a, b = ne.verts
            nxt = b if a.index == cur.index else a
            loop_pairs.insert(0, (nxt.index, cur.index))
            visited.add(ne.index)
            prev, cur = cur, nxt

        return loop_pairs

    for e in edges:
        if e.index in visited: continue
        loops_idx_pairs.append(follow_loop(e))

    mw = obj.matrix_world
    world_loops = []
    verts_per_loop = []
    for loop in loops_idx_pairs:
        world_pairs = []
        vset = set()
        for i0, i1 in loop:
            p0 = mw @ bm.verts[i0].co
            p1 = mw @ bm.verts[i1].co
            world_pairs.append((p0.copy(), p1.copy()))
            vset.add(i0); vset.add(i1)
        world_loops.append(world_pairs)
        verts_per_loop.append(vset)

    bm.free()
    return world_loops, loops_idx_pairs, verts_per_loop

def average_direction(loop_pairs):
    acc = Vector((0,0,0))
    for p0, p1 in loop_pairs:
        d = (p1 - p0)
        if d.length_squared != 0:
            acc += d.normalized()
    if acc.length_squared == 0:
        return Vector((0,0,1))
    return acc.normalized()

def loop_center(loop_pairs):
    pts = []
    for p0, p1 in loop_pairs:
        pts.extend((p0,p1))
    if not pts:
        return Vector((0,0,0))
    c = Vector((0,0,0))
    for p in pts: c += p
    return c / len(pts)

def signed_axis_from_normal_and_dir(n, d):
    z = d.normalized()
    y = n.normalized()
    x = y.cross(z)
    if x.length_squared == 0:
        x = Vector((1,0,0)).cross(z)
        if x.length_squared == 0:
            x = Vector((0,1,0))
    x.normalize()
    y = z.cross(x).normalized()
    return Matrix((
        (x.x, y.x, z.x, 0.0),
        (x.y, y.y, z.y, 0.0),
        (x.z, y.z, z.z, 0.0),
        (0.0, 0.0, 0.0, 1.0),
    ))

def estimate_mesh_normal(obj):
    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.faces.ensure_lookup_table()
    n = Vector((0,0,1))
    if len(bm.faces) > 0:
        acc = Vector((0,0,0))
        for f in bm.faces: acc += f.normal
        if acc.length_squared != 0:
            n = (obj.matrix_world.to_3x3() @ (acc / len(bm.faces))).normalized()
    bm.free()
    return n

# ---------- Grafo geodésico con barreras (incluye bordes si se pide) ----------

def build_vertex_graph(obj, barrier_mode, include_border=False):
    """
    include_border=True => trata los edges frontera / non-manifold como barrera.
    """
    me = obj.data
    mw = obj.matrix_world

    bm = bmesh.new()
    bm.from_mesh(me)
    bm.edges.ensure_lookup_table()
    bm.verts.ensure_lookup_table()

    verts_world = [mw @ v.co for v in me.vertices]

    def edge_is_barrier(e):
        # atributos de Mesh (seam/sharp)
        me_e = me.edges[e.index]
        seam = me_e.use_seam
        sharp = getattr(me_e, "use_edge_sharp", False)
        border = (len(e.link_faces) != 2)  # 1 cara (borde), 0 (sueltos) o non-manifold
        if include_border and border:
            return True
        if barrier_mode == 'NONE':
            return False
        if barrier_mode == 'SEAM':
            return seam
        if barrier_mode == 'SHARP':
            return sharp
        if barrier_mode == 'SEAM_OR_SHARP':
            return seam or sharp
        return False

    adj = defaultdict(list)
    for e in bm.edges:
        if edge_is_barrier(e):
            continue
        i = e.verts[0].index
        j = e.verts[1].index
        w = (verts_world[j] - verts_world[i]).length
        adj[i].append((j, w))
        adj[j].append((i, w))

    bm.free()
    return adj

def dijkstra_from_seeds(adj, seeds, max_dist=float("inf")):
    dist, pq = {}, []
    for s in seeds:
        if s in adj or True:  # permitir semillas aisladas
            dist[s] = 0.0
            heapq.heappush(pq, (0.0, s))
    while pq:
        d, u = heapq.heappop(pq)
        if d > dist[u] or d > max_dist: 
            continue
        for v, w in adj.get(u, []):
            nd = d + w
            if nd < dist.get(v, float("inf")) and nd <= max_dist:
                dist[v] = nd
                heapq.heappush(pq, (nd, v))
    return dist

# ---------- Semillas del lado correcto ----------

def side_ring_seeds(obj, loop_idx_pairs, pivot_inv, desired_side):
    me = obj.data
    mw = obj.matrix_world
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()

    pair_to_edge = {}
    for e in bm.edges:
        a, b = e.verts[0].index, e.verts[1].index
        pair_to_edge[tuple(sorted((a,b)))] = e

    seeds = set()
    seam_verts = set([v for pair in loop_idx_pairs for v in pair])

    def side_ok(world_pt):
        p_local = pivot_inv @ world_pt.to_4d()
        x = p_local.x
        return True if desired_side == 'BOTH' else (x >= 0.0 if desired_side == 'POSITIVE' else x <= 0.0)

    for a, b in loop_idx_pairs:
        e = pair_to_edge.get(tuple(sorted((a,b))))
        if e is None: continue
        for f in e.link_faces:
            c_world = mw @ f.calc_center_median()
            if side_ok(c_world):
                for v in f.verts:
                    if v.index not in seam_verts:
                        seeds.add(v.index)

    bm.free()
    return seeds

# ---------- Helpers de pintura sólida ----------

def flood_within_rect(adj, seeds, ok_mask):
    visited = set()
    dq = deque()
    for s in seeds:
        if 0 <= s < len(ok_mask) and ok_mask[s]:
            visited.add(s)
            dq.append(s)
    while dq:
        u = dq.popleft()
        for v, _w in adj.get(u, []):
            if v not in visited and 0 <= v < len(ok_mask) and ok_mask[v]:
                visited.add(v)
                dq.append(v)
    return visited

# ---------- Pesos (sólidos) ----------

def ensure_vertex_group(obj, name):
    vg = obj.vertex_groups.get(name)
    if vg is None:
        vg = obj.vertex_groups.new(name=name)
    return vg

def assign_weights(obj, vg, seeds, seam_vertices, barrier_mode,
                   side_filter_func=None, frame_matrix=None,
                   coverage_mode='ALL', across=1.0, along=1.0,
                   seam_z_range=None, end_margin=0.0,
                   limit_by_topology=False):
    me = obj.data
    mw = obj.matrix_world
    verts_world = [mw @ v.co for v in me.vertices]

    # limpiar
    vg.add(range(len(me.vertices)), 0.0, 'REPLACE')

    # seam siempre rojo
    for s in seam_vertices:
        if 0 <= s < len(me.vertices):
            vg.add([s], 1.0, 'REPLACE')

    # --- Tira del seam (rectángulo local) ---
    if coverage_mode == 'SEAM_STRIP':
        if frame_matrix is None or seam_z_range is None:
            return
        zmin, zmax = seam_z_range
        low  = min(zmin, zmax) - end_margin
        high = max(zmin, zmax) + end_margin

        ok_mask = []
        for vi in range(len(me.vertices)):
            p_local = frame_matrix @ verts_world[vi].to_4d()
            inside = (abs(p_local.x) <= across) and (low <= p_local.z <= high)
            if side_filter_func:
                inside = inside and side_filter_func(p_local)
            ok_mask.append(bool(inside))

        if limit_by_topology:
            # Grafo con BORDES como barrera adicional
            adj = build_vertex_graph(obj, barrier_mode, include_border=True)
            seeds_used = list(seeds) if seeds else list(seam_vertices)
            visited = flood_within_rect(adj, seeds_used, ok_mask)
            for vi in visited:
                vg.add([vi], 1.0, 'REPLACE')
        else:
            for vi, ok in enumerate(ok_mask):
                if ok:
                    vg.add([vi], 1.0, 'REPLACE')
        return

    # --- Modos ALL / RANGE: geodésico ---
    adj = build_vertex_graph(obj, barrier_mode, include_border=limit_by_topology)
    seeds_used = list(seeds) if seeds else list(seam_vertices)
    dist = dijkstra_from_seeds(adj, seeds_used, max_dist=float('inf'))

    if coverage_mode == 'ALL':
        for vi in dist.keys():
            if side_filter_func and frame_matrix is not None:
                p_local = frame_matrix @ verts_world[vi].to_4d()
                if not side_filter_func(p_local):
                    continue
            vg.add([vi], 1.0, 'REPLACE')

    elif coverage_mode == 'RANGE':
        for vi in dist.keys():
            p_local = frame_matrix @ verts_world[vi].to_4d()
            if side_filter_func and not side_filter_func(p_local): 
                continue
            if abs(p_local.x) <= across and abs(p_local.z) <= along:
                vg.add([vi], 1.0, 'REPLACE')

# ---------- Crear pliegues ----------

def _seam_z_range_local(obj, seam_vertices, inv_pivot):
    me = obj.data
    mw = obj.matrix_world
    zs = []
    for vid in seam_vertices:
        if 0 <= vid < len(me.vertices):
            p_world = mw @ me.vertices[vid].co
            p_local = inv_pivot @ p_world.to_4d()
            zs.append(p_local.z)
    if not zs:
        return (0.0, 0.0)
    return (min(zs), max(zs))

def create_fold_for_loop(obj, loop_pairs, loop_idx_pairs, idx, props, normal_hint=None, per_loop_settings=None):
    center = loop_center(loop_pairs)
    d = average_direction(loop_pairs)
    if normal_hint is None:
        normal_hint = estimate_mesh_normal(obj)

    # Pivot
    empty_name = f"FoldPivot_{obj.name}_{idx:02d}"
    empty = bpy.data.objects.new(empty_name, None)
    empty.empty_display_type = 'PLAIN_AXES'
    empty.empty_display_size = 0.2
    bpy.context.collection.objects.link(empty)
    pivot_matrix = Matrix.Translation(center) @ signed_axis_from_normal_and_dir(normal_hint, d)
    empty.matrix_world = pivot_matrix
    inv_pivot = pivot_matrix.inverted()

    # Grupo
    vg_name = f"FoldGroup_{obj.name}_{idx:02d}"
    vg = ensure_vertex_group(obj, vg_name)

    # Vértices seam
    seam_vertices = set()
    for v0, v1 in loop_idx_pairs:
        seam_vertices.add(v0); seam_vertices.add(v1)

    # Config
    cfg = per_loop_settings or {
        "side": props.side_mode,
        "coverage": props.coverage_mode,
        "width": props.width,
        "length": props.length_range,
        "barrier": props.barrier_mode,
        "angle": props.angle,
        "invert": props.invert_angle,
        "end_margin": props.end_margin,
        "limit_topology": props.strip_limit_topology,
    }

    def side_filter_func(p_local4):
        x = p_local4.x
        if cfg["side"] == 'BOTH': return True
        return x >= 0.0 if cfg["side"] == 'POSITIVE' else x <= 0.0

    ring_seeds = side_ring_seeds(obj, loop_idx_pairs, inv_pivot, cfg["side"])
    if not ring_seeds:
        ring_seeds = set(seam_vertices)

    zmin, zmax = _seam_z_range_local(obj, seam_vertices, inv_pivot)

    assign_weights(
        obj=obj, vg=vg,
        seeds=list(ring_seeds),
        seam_vertices=list(seam_vertices),
        barrier_mode=cfg["barrier"],
        side_filter_func=(side_filter_func if cfg["side"] != 'BOTH' else None),
        frame_matrix=inv_pivot,
        coverage_mode=cfg["coverage"],
        across=cfg["width"], along=cfg["length"],
        seam_z_range=(zmin, zmax),
        end_margin=cfg["end_margin"],
        limit_by_topology=cfg["limit_topology"]
    )

    # Modificador
    mod = obj.modifiers.new(f"Fold_{idx:02d}", 'SIMPLE_DEFORM')
    mod.deform_method = 'BEND'
    mod.deform_axis = 'Z'
    mod.origin = empty
    mod.vertex_group = vg.name
    ang = -cfg["angle"] if cfg["invert"] else cfg["angle"]
    mod.angle = math.radians(ang)

    # Tag
    tag = obj.get("_fold_along_seams", [])
    tag.append({
        "pivot": empty.name,
        "vgroup": vg.name,
        "modifier": mod.name,
        "side": cfg["side"],
        "coverage": cfg["coverage"],
        "width": cfg["width"],
        "length": cfg["length"],
        "barrier": cfg["barrier"],
        "angle": cfg["angle"],
        "invert": cfg["invert"],
        "end_margin": cfg["end_margin"],
        "limit_topology": cfg["limit_topology"],
    })
    obj["_fold_along_seams"] = tag
    return empty, vg, mod

def clear_folds(obj):
    tag = obj.get("_fold_along_seams", [])
    for item in tag:
        mod = obj.modifiers.get(item.get("modifier", ""))
        if mod: 
            try: obj.modifiers.remove(mod)
            except Exception: pass
        vg = obj.vertex_groups.get(item.get("vgroup", ""))
        if vg:
            try: obj.vertex_groups.remove(vg)
            except Exception: pass
        pivname = item.get("pivot", "")
        if pivname and pivname in bpy.data.objects:
            try: bpy.data.objects.remove(bpy.data.objects[pivname], do_unlink=True)
            except Exception: pass
    if "_fold_along_seams" in obj:
        del obj["_fold_along_seams"]

# ---------- Propiedades y UI ----------

class FOLD_props(bpy.types.PropertyGroup):
    width: bpy.props.FloatProperty(name="Ancho", default=0.05, min=0.0, soft_max=1.0)
    length_range: bpy.props.FloatProperty(name="Largo (Rango)", default=1.0, min=0.0, soft_max=10.0)
    end_margin: bpy.props.FloatProperty(name="Margen extremo", default=0.0, min=0.0, soft_max=2.0)
    coverage_mode: bpy.props.EnumProperty(
        name="Cobertura (default)",
        items=[('ALL',"Todo (sólido)",""),
               ('RANGE',"Rango",""),
               ('SEAM_STRIP',"Tira del seam (sin degradé)","")],
        default='SEAM_STRIP'
    )
    strip_limit_topology: bpy.props.BoolProperty(
        name="Limitar por topología (bordes)",
        description="Corta por barreras y también por BORDES/holes de la malla",
        default=True
    )
    angle: bpy.props.FloatProperty(name="Ángulo (°)", default=30.0, subtype='ANGLE')
    invert_angle: bpy.props.BoolProperty(name="Invertir ángulo", default=False)
    use_selected_edges: bpy.props.BoolProperty(name="Usar edges seleccionados", default=False)
    barrier_mode: bpy.props.EnumProperty(
        name="Barreras (default)",
        items=[('NONE',"Ninguna",""),('SEAM',"Seam",""),('SHARP',"Sharp",""),('SEAM_OR_SHARP',"Seam o Sharp","")],
        default='SEAM_OR_SHARP'
    )
    side_mode: bpy.props.EnumProperty(name="Lado (default)",
        items=[('BOTH',"Ambos",""),('POSITIVE',"+X",""),('NEGATIVE',"−X","")], default='BOTH')

    # por índice
    loop_index: bpy.props.IntProperty(name="Índice de pliegue", default=0, min=0)
    loop_side: bpy.props.EnumProperty(name="Lado (índice)",
        items=[('BOTH',"Ambos",""),('POSITIVE',"+X",""),('NEGATIVE',"−X","")], default='BOTH')
    loop_coverage: bpy.props.EnumProperty(name="Cobertura (índice)",
        items=[('ALL',"Todo (sólido)",""),('RANGE',"Rango",""),('SEAM_STRIP',"Tira del seam","")], default='SEAM_STRIP')
    loop_width: bpy.props.FloatProperty(name="Ancho (índice)", default=0.05, min=0.0, soft_max=1.0)
    loop_length: bpy.props.FloatProperty(name="Largo (índice)", default=1.0, min=0.0, soft_max=10.0)
    loop_end_margin: bpy.props.FloatProperty(name="Margen (índice)", default=0.0, min=0.0, soft_max=2.0)
    loop_barrier: bpy.props.EnumProperty(
        name="Barreras (índice)",
        items=[('NONE',"Ninguna",""),('SEAM',"Seam",""),('SHARP',"Sharp",""),('SEAM_OR_SHARP',"Seam o Sharp","")],
        default='SEAM_OR_SHARP'
    )
    loop_limit_topology: bpy.props.BoolProperty(name="Limitar por topología (índice)", default=True)

    # combinación + modificador
    combine_mode: bpy.props.EnumProperty(
        name="Modo de composición",
        items=[('INTERSECTION',"Intersección (AND)",""),('UNION',"Unión (OR)","")],
        default='INTERSECTION'
    )
    combine_indices: bpy.props.StringProperty(name="Índices a combinar", default="*")
    combine_group_name: bpy.props.StringProperty(name="Nombre grupo combinado", default="FoldCombined")
    combine_mod_name: bpy.props.StringProperty(name="Nombre modificador", default="FoldCombined_Mod")
    combine_pivot_name: bpy.props.StringProperty(name="Nombre pivote", default="FoldCombined_Pivot")
    combine_axis: bpy.props.EnumProperty(name="Eje del modificador", items=[('X',"X",""),('Y',"Y",""),('Z',"Z","")], default='Z')
    combine_angle: bpy.props.FloatProperty(name="Ángulo combinado (°)", default=30.0, subtype='ANGLE')
    combine_invert: bpy.props.BoolProperty(name="Invertir ángulo combinado", default=False)
    combine_recenter_pivot: bpy.props.BoolProperty(name="Recentra pivote cada vez", default=True)

# ---------- Helpers de recálculo (índice) ----------

def _seam_data_for_index(obj, i, use_selected_edges):
    seam_edge_idxs = get_seam_edges_indices(obj, use_selected=use_selected_edges)
    world_loops, loops_idx_pairs, _ = edge_loops_from_edge_set(obj, seam_edge_idxs)
    if not world_loops or i >= len(loops_idx_pairs): 
        return None
    n = estimate_mesh_normal(obj)
    center = loop_center(world_loops[i]); d = average_direction(world_loops[i])
    pivot_matrix = Matrix.Translation(center) @ signed_axis_from_normal_and_dir(n, d)
    inv_pivot = pivot_matrix.inverted()
    seam_vertices = set()
    for a,b in loops_idx_pairs[i]:
        seam_vertices.add(a); seam_vertices.add(b)
    zmin, zmax = _seam_z_range_local(obj, seam_vertices, inv_pivot)
    return inv_pivot, list(seam_vertices), (zmin, zmax), world_loops, loops_idx_pairs

def _recompute_one(obj, i, props):
    tag = obj.get("_fold_along_seams", [])
    if not tag or i < 0 or i >= len(tag): return False
    data = _seam_data_for_index(obj, i, props.use_selected_edges)
    if not data: return False
    inv_pivot, seam_vertices, zrange, world_loops, loops_idx_pairs = data
    item = tag[i]
    side_mode  = item.get("side", 'BOTH')
    coverage   = item.get("coverage", 'SEAM_STRIP')
    width      = float(item.get("width", 0.05))
    length     = float(item.get("length", 1.0))
    end_margin = float(item.get("end_margin", 0.0))
    barrier    = item.get("barrier", 'SEAM_OR_SHARP')
    limit_topo = bool(item.get("limit_topology", True))
    vgn = item.get("vgroup", "")
    vg = obj.vertex_groups.get(vgn)
    if not vg: return False

    def side_filter_func(p_local4, sm=side_mode):
        x = p_local4.x
        if sm == 'BOTH': return True
        return x >= 0.0 if sm == 'POSITIVE' else x <= 0.0

    seeds = side_ring_seeds(obj, loops_idx_pairs[i], inv_pivot, side_mode)
    if not seeds: seeds = set(seam_vertices)

    assign_weights(
        obj=obj, vg=vg,
        seeds=list(seeds),
        seam_vertices=list(seam_vertices),
        barrier_mode=barrier,
        side_filter_func=(side_filter_func if side_mode != 'BOTH' else None),
        frame_matrix=inv_pivot,
        coverage_mode=coverage,
        across=width, along=length,
        seam_z_range=zrange,
        end_margin=end_margin,
        limit_by_topology=limit_topo
    )
    return True

# ---------- Operadores principales ----------

class FOLD_OT_create(bpy.types.Operator):
    bl_idname = "mesh.fold_along_seams_create"
    bl_label = "Crear pliegues"
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        obj = context.object
        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, "Selecciona un objeto MESH"); return {'CANCELLED'}
        props = context.scene.fold_props

        seam_edge_idxs = get_seam_edges_indices(obj, use_selected=props.use_selected_edges)
        world_loops, loops_idx_pairs, _ = edge_loops_from_edge_set(obj, seam_edge_idxs)
        if not world_loops:
            self.report({'ERROR'}, "No se encontraron líneas de pliegue"); return {'CANCELLED'}

        n = estimate_mesh_normal(obj)
        for i, (wloop, iloop) in enumerate(zip(world_loops, loops_idx_pairs)):
            create_fold_for_loop(obj, wloop, iloop, i, props, normal_hint=n, per_loop_settings=None)

        self.report({'INFO'}, f"Creado(s) {len(world_loops)} pliegue(s)")
        return {'FINISHED'}

class FOLD_OT_clear(bpy.types.Operator):
    bl_idname = "mesh.fold_along_seams_clear"
    bl_label = "Borrar pliegues"
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        obj = context.object
        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, "Selecciona un objeto MESH"); return {'CANCELLED'}
        clear_folds(obj)
        self.report({'INFO'}, "Pliegues borrados"); return {'FINISHED'}

class FOLD_OT_reweight_index(bpy.types.Operator):
    bl_idname = "mesh.fold_along_seams_reweight_index"
    bl_label = "Recalcular (índice)"
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        obj = context.object
        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, "Selecciona un objeto MESH"); return {'CANCELLED'}
        props = context.scene.fold_props
        ok = _recompute_one(obj, props.loop_index, props)
        if not ok:
            self.report({'ERROR'}, "No se pudo recalcular ese índice"); return {'CANCELLED'}
        self.report({'INFO'}, f"Recalculado pliegue {props.loop_index}")
        return {'FINISHED'}

class FOLD_OT_set_loop_settings(bpy.types.Operator):
    bl_idname = "mesh.fold_along_seams_set_loop_settings"
    bl_label = "Aplicar configuración al pliegue"
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        obj = context.object
        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, "Selecciona un objeto MESH"); return {'CANCELLED'}
        p = context.scene.fold_props
        tag = obj.get("_fold_along_seams", [])
        i = p.loop_index
        if i < 0 or i >= len(tag):
            self.report({'ERROR'}, "Índice fuera de rango"); return {'CANCELLED'}
        tag[i]["side"] = p.loop_side
        tag[i]["coverage"] = p.loop_coverage
        tag[i]["width"] = p.loop_width
        tag[i]["length"] = p.loop_length
        tag[i]["end_margin"] = p.loop_end_margin
        tag[i]["barrier"] = p.loop_barrier
        tag[i]["limit_topology"] = p.loop_limit_topology
        obj["_fold_along_seams"] = tag
        ok = _recompute_one(obj, i, p)
        if not ok:
            self.report({'ERROR'}, "No se pudo aplicar/recalcular"); return {'CANCELLED'}
        self.report({'INFO'}, f"Aplicado al pliegue {i}")
        return {'FINISHED'}

# ---------- Visualización ----------

def _activate_group_and_select(obj, vg_name, threshold=1e-6):
    me = obj.data
    vg = obj.vertex_groups.get(vg_name)
    if not vg: return False
    obj.vertex_groups.active = vg
    me.use_paint_mask_vertex = True
    for v in me.vertices: v.select = False
    for v in me.vertices:
        try:
            if vg.weight(v.index) > threshold:
                v.select = True
        except RuntimeError:
            pass
    return True

class FOLD_OT_view_group_index(bpy.types.Operator):
    bl_idname = "mesh.fold_along_seams_view_group_index"
    bl_label = "Ver grupo (índice)"
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        obj = context.object
        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, "Selecciona un objeto MESH"); return {'CANCELLED'}
        p = context.scene.fold_props
        tag = obj.get("_fold_along_seams", [])
        i = p.loop_index
        if not tag or i < 0 or i >= len(tag):
            self.report({'ERROR'}, "Índice fuera de rango"); return {'CANCELLED'}
        vg_name = tag[i].get("vgroup", "")
        ok = _activate_group_and_select(obj, vg_name)
        if not ok:
            self.report({'ERROR'}, "No se pudo activar ese grupo"); return {'CANCELLED'}
        bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
        self.report({'INFO'}, f"Mostrando grupo {vg_name}")
        return {'FINISHED'}

class FOLD_OT_clear_view_mask(bpy.types.Operator):
    bl_idname = "mesh.fold_along_seams_clear_view_mask"
    bl_label = "Quitar máscara"
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        obj = context.object
        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, "Selecciona un objeto MESH"); return {'CANCELLED'}
        me = obj.data
        me.use_paint_mask_vertex = False
        for v in me.vertices: v.select = False
        self.report({'INFO'}, "Máscara desactivada")
        return {'FINISHED'}

# ---------- Combinación + Modificador ----------

class FOLD_OT_combine_groups(bpy.types.Operator):
    bl_idname = "mesh.fold_along_seams_combine"
    bl_label = "Construir combinado + modificador"
    bl_options = {'REGISTER', 'UNDO'}

    def parse_indices(self, s, n):
        s = s.strip()
        if s == "*" or s == "": return list(range(n))
        out = []
        for tok in s.split(","):
            tok = tok.strip()
            if not tok: continue
            try:
                i = int(tok)
                if 0 <= i < n: out.append(i)
            except ValueError:
                pass
        return sorted(set(out))

    def execute(self, context):
        obj = context.object
        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, "Selecciona un objeto MESH"); return {'CANCELLED'}

        p = context.scene.fold_props
        tag = obj.get("_fold_along_seams", [])
        if not tag:
            self.report({'ERROR'}, "No hay pliegues para combinar"); return {'CANCELLED'}

        idxs = self.parse_indices(p.combine_indices, len(tag))
        if not idxs:
            self.report({'ERROR'}, "Lista de índices vacía"); return {'CANCELLED'}

        groups = []
        for i in idxs:
            vgn = tag[i].get("vgroup","")
            vg = obj.vertex_groups.get(vgn)
            if vg: groups.append(vg)
        if not groups:
            self.report({'ERROR'}, "No se encontraron grupos válidos"); return {'CANCELLED'}

        dst = ensure_vertex_group(obj, p.combine_group_name)
        me = obj.data
        dst.add(range(len(me.vertices)), 0.0, 'REPLACE')

        for v in me.vertices:
            vals = []
            for vg in groups:
                try:
                    vals.append(1.0 if vg.weight(v.index) > 1e-6 else 0.0)
                except RuntimeError:
                    vals.append(0.0)
            take = (all(vals) if p.combine_mode == 'INTERSECTION' else any(vals))
            if take:
                dst.add([v.index], 1.0, 'REPLACE')

        mw = obj.matrix_world
        pts = []
        for v in me.vertices:
            try:
                if dst.weight(v.index) > 1e-6:
                    pts.append(mw @ v.co)
            except RuntimeError:
                pass
        if not pts:
            self.report({'ERROR'}, "El grupo combinado quedó vacío"); return {'CANCELLED'}
        centroid = Vector((0,0,0))
        for q in pts: centroid += q
        centroid /= len(pts)

        piv_name = p.combine_pivot_name
        empty = bpy.data.objects.get(piv_name)
        if empty is None:
            empty = bpy.data.objects.new(piv_name, None)
            empty.empty_display_type = 'PLAIN_AXES'
            empty.empty_display_size = 0.3
            bpy.context.collection.objects.link(empty)
        if p.combine_recenter_pivot:
            empty.location = centroid

        mod_name = p.combine_mod_name
        mod = obj.modifiers.get(mod_name)
        if mod is None:
            mod = obj.modifiers.new(mod_name, 'SIMPLE_DEFORM')
        mod.deform_method = 'BEND'
        mod.deform_axis = p.combine_axis
        mod.origin = empty
        mod.vertex_group = dst.name
        ang = -p.combine_angle if p.combine_invert else p.combine_angle
        mod.angle = math.radians(ang)

        obj.vertex_groups.active = dst
        bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
        self.report({'INFO'}, f"Combinado '{dst.name}' ({p.combine_mode}), eje {p.combine_axis}")
        return {'FINISHED'}

# ---------- Panel ----------

class FOLD_PT_panel(bpy.types.Panel):
    bl_label = "Doblar"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Doblar'
    def draw(self, context):
        p = context.scene.fold_props
        col = self.layout.column(align=True)

        col.label(text="Predeterminados (para crear):")
        col.prop(p, "coverage_mode")
        col.prop(p, "strip_limit_topology")
        row = col.row(align=True); row.prop(p, "width"); row.prop(p, "length_range")
        col.prop(p, "end_margin")
        col.prop(p, "angle"); col.prop(p, "invert_angle")
        col.prop(p, "side_mode")
        col.prop(p, "barrier_mode")
        col.prop(p, "use_selected_edges")
        col.separator()
        col.operator("mesh.fold_along_seams_create", icon='MOD_SIMPLEDEFORM')
        col.operator("mesh.fold_along_seams_clear", icon='TRASH')

        col.separator()
        box = col.box(); box.label(text="Ajustes por índice")
        box.prop(p, "loop_index")
        box.prop(p, "loop_side")
        box.prop(p, "loop_coverage")
        box.prop(p, "loop_limit_topology")
        r2 = box.row(align=True); r2.prop(p, "loop_width"); r2.prop(p, "loop_length")
        box.prop(p, "loop_end_margin")
        box.prop(p, "loop_barrier")
        box.operator("mesh.fold_along_seams_set_loop_settings", icon='CHECKMARK')
        box.operator("mesh.fold_along_seams_reweight_index", icon='BRUSH_DATA')

        col.separator()
        vis = col.box(); vis.label(text="Visualizar en Weight Paint")
        vis.operator("mesh.fold_along_seams_view_group_index", icon='HIDE_OFF')
        vis.operator("mesh.fold_along_seams_clear_view_mask", icon='HIDE_ON')

        col.separator()
        cmb = col.box(); cmb.label(text="Combinación + Modificador")
        cmb.prop(p, "combine_mode")
        cmb.prop(p, "combine_indices")
        cmb.prop(p, "combine_group_name")
        cmb.prop(p, "combine_mod_name")
        cmb.prop(p, "combine_pivot_name")
        rowm = cmb.row(align=True); rowm.prop(p, "combine_axis"); rowm.prop(p, "combine_angle")
        cmb.prop(p, "combine_invert")
        cmb.prop(p, "combine_recenter_pivot")
        cmb.operator("mesh.fold_along_seams_combine", icon='MOD_SIMPLEDEFORM')

# ---------- Registro ----------

classes = (
    FOLD_props,
    FOLD_OT_create,
    FOLD_OT_clear,
    FOLD_OT_reweight_index,
    FOLD_OT_set_loop_settings,
    FOLD_OT_view_group_index,
    FOLD_OT_clear_view_mask,
    FOLD_OT_combine_groups,
    FOLD_PT_panel,
)

def register():
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.Scene.fold_props = bpy.props.PointerProperty(type=FOLD_props)

def unregister():
    for c in reversed(classes):
        bpy.utils.unregister_class(c)
    if hasattr(bpy.types.Scene, "fold_props"):
        del bpy.types.Scene.fold_props

if __name__ == "__main__":
    register()


