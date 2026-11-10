# -*- coding: utf-8 -*-
# place_jefrey.py
# Coloca a Jefrey (capitan) en la esquina hacia la que apunta el CENTRO de la camara del viewport
# y pone un texto flotante encima. NO guarda el nivel.
#
# Antes de ejecutar: mueve la camara del viewport para que el centro de la vista este sobre el PISO,
# justo en la esquina donde quieres a Jefrey. Luego en el Cmd del editor:
#   py "C:/Users/sevic/Documents/Unreal Projects/BackrUrms 5.8/Tools/place_jefrey.py"
import math
import unreal

MESH_NAME     = "jefrey+capitan+epstein"
TEXT          = "Donde esta mi isla?"
TEXT_LABEL    = "Texto_Jefrey"
INWARD_EXTRA  = 15.0     # cm extra de separacion respecto a las paredes
FACE_YAW_OFFSET = 0.0    # si Jefrey mira de lado/espaldas al verlo, prueba 90, -90 o 180
TEXT_YAW_OFFSET = 0.0    # si el texto se ve al reves/espejo, prueba 180
TEXT_SIZE     = 35.0     # alto de las letras en cm
TEXT_GAP      = 25.0     # separacion entre la cabeza y el texto
TEXT_COLOR    = (255, 40, 40, 255)   # R, G, B, A

def log(m):  unreal.log("[Jefrey] " + str(m))
def warn(m): unreal.log_warning("[Jefrey] " + str(m))

ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
act = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
world = ues.get_editor_world()

# 1) Camara del viewport
cam = ues.get_level_viewport_camera_info()
if cam is None:
    raise RuntimeError("No pude leer la camara del viewport.")
if len(cam) == 3:
    cam_loc, cam_rot = cam[1], cam[2]
else:
    cam_loc, cam_rot = cam[0], cam[1]
log("Camara: loc=%s rot=%s" % (cam_loc, cam_rot))

# 2) Buscar a Jefrey en el nivel
all_actors = act.get_all_level_actors()
jef = None
for a in all_actors:
    if isinstance(a, unreal.StaticMeshActor):
        sm = a.static_mesh_component.get_editor_property("static_mesh")
        if sm is not None and sm.get_name() == MESH_NAME:
            jef = a
            break
if jef is None:
    raise RuntimeError("No encuentro en el nivel el actor con la malla '%s'." % MESH_NAME)
log("Jefrey encontrado: %s en %s" % (jef.get_actor_label(), jef.get_actor_location()))

# 3) Rayo desde el centro de la vista
start = cam_loc
end = cam_loc + cam_rot.get_forward_vector() * 30000.0
res = unreal.SystemLibrary.line_trace_single(
    world, start, end, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [jef],
    unreal.DrawDebugTrace.NONE, True)
hit = None
if isinstance(res, unreal.HitResult):
    hit = res
elif isinstance(res, tuple):
    for r in res:
        if isinstance(r, unreal.HitResult):
            hit = r
if hit is None:
    raise RuntimeError("El rayo no devolvio un resultado utilizable: %s" % (res,))
t = hit.to_tuple()
if not t[0]:
    raise RuntimeError("El rayo no toco nada. Apunta el centro de la vista a una pared o al piso, mas cerca.")
p = t[5]  # punto de impacto
hit_actor = t[9]
log("Punto de impacto: %s sobre %s" % (p, hit_actor.get_name() if hit_actor else "?"))

# 4) Direccion horizontal hacia la camara (hacia el interior del cuarto)
dx, dy = cam_loc.x - p.x, cam_loc.y - p.y
n = math.hypot(dx, dy)
if n < 1.0:
    raise RuntimeError("La camara esta justo encima del punto; alejala un poco.")
dx, dy = dx / n, dy / n
face_yaw = math.degrees(math.atan2(dy, dx))

# 5) Rotar a Jefrey hacia el cuarto y medir su tamano
r = jef.get_actor_rotation()
jef.set_actor_rotation(unreal.Rotator(r.roll, r.pitch, face_yaw + FACE_YAW_OFFSET), False)
origin, ext = jef.get_actor_bounds(False)
radius = max(ext.x, ext.y)
cur = jef.get_actor_location()
# mover en XY: centro de su caja a (punto + direccion interior * (radio + extra))
cx = p.x + dx * (radius + INWARD_EXTRA)
cy = p.y + dy * (radius + INWARD_EXTRA)
jef.set_actor_location(unreal.Vector(cur.x + (cx - origin.x), cur.y + (cy - origin.y), cur.z), False, False)
# ajustar altura: base de su caja a la altura del piso
origin, ext = jef.get_actor_bounds(False)
bottom = origin.z - ext.z
cur = jef.get_actor_location()
jef.set_actor_location(unreal.Vector(cur.x, cur.y, cur.z + (p.z - bottom)), False, False)
origin, ext = jef.get_actor_bounds(False)
log("Jefrey colocado. Centro=%s extent=%s" % (origin, ext))

# 6) Texto flotante encima de su cabeza (reusa el actor si ya existe)
text_actor = None
for a in act.get_all_level_actors():
    if isinstance(a, unreal.TextRenderActor) and a.get_actor_label() == TEXT_LABEL:
        text_actor = a
        break
tloc = unreal.Vector(origin.x, origin.y, origin.z + ext.z + TEXT_GAP + TEXT_SIZE * 0.5)
trot = unreal.Rotator(0.0, 0.0, face_yaw + TEXT_YAW_OFFSET)
if text_actor is None:
    text_actor = act.spawn_actor_from_class(unreal.TextRenderActor, tloc, trot)
    text_actor.set_actor_label(TEXT_LABEL)
else:
    text_actor.set_actor_location(tloc, False, False)
    text_actor.set_actor_rotation(trot, False)

comp = text_actor.get_editor_property("text_render")
for name, value in (
        ("text", TEXT),
        ("world_size", TEXT_SIZE),
        ("text_render_color", unreal.Color(r=TEXT_COLOR[0], g=TEXT_COLOR[1], b=TEXT_COLOR[2], a=TEXT_COLOR[3])),
        ("horizontal_alignment", unreal.HorizTextAligment.EHTA_CENTER),
        ("vertical_alignment", unreal.VerticalTextAligment.EVRTA_TEXT_CENTER)):
    try:
        comp.set_editor_property(name, value)
    except Exception as e:
        warn("No pude fijar %s: %s" % (name, e))
log("Texto listo: '%s' en %s" % (TEXT, tloc))

act.set_selected_level_actors([jef, text_actor])
log("LISTO. El nivel NO se guardo. Revisa en el viewport y guarda con Ctrl+S si te gusta.")
