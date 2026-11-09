# -*- coding: utf-8 -*-
# fix_jefrey_text.py
# NO mueve a Jefrey. Reubica el texto 'Texto_Jefrey' encima de su cabeza, lo endereza, lo pone rojo
# y deja la camara del viewport mirando a Jefrey. No guarda el nivel.
#   py "C:/Users/sevic/Documents/Unreal Projects/BackrUrms 5.8/Tools/fix_jefrey_text.py"
import math
import unreal

MESH_NAME  = "jefrey+capitan+epstein"
TEXT_LABEL = "Texto_Jefrey"
TEXT       = "Donde esta mi isla?"
TEXT_SIZE  = 35.0
TEXT_GAP   = 25.0
JEFREY_FRONT_OFFSET = -90.0  # direccion de su frente respecto a su yaw (si mira al reves, prueba 90)
TEXT_YAW_OFFSET = 0.0      # si el texto se ve al reves/espejo prueba 180
TEXT_COLOR = (255, 40, 40, 255)   # R, G, B, A
CAM_DIST   = 700.0

def log(m):  unreal.log("[Jefrey] " + str(m))
def warn(m): unreal.log_warning("[Jefrey] " + str(m))

ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
act = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

jef, text_actor = None, None
for a in act.get_all_level_actors():
    if isinstance(a, unreal.StaticMeshActor) and jef is None:
        sm = a.static_mesh_component.get_editor_property("static_mesh")
        if sm is not None and sm.get_name() == MESH_NAME:
            jef = a
    if isinstance(a, unreal.TextRenderActor) and a.get_actor_label() == TEXT_LABEL:
        text_actor = a
if jef is None:
    raise RuntimeError("No encuentro a Jefrey en el nivel.")

origin, ext = jef.get_actor_bounds(False)
jrot = jef.get_actor_rotation()
log("Jefrey: loc=%s rot=%s | centro=%s extent=%s" % (jef.get_actor_location(), jrot, origin, ext))

tloc = unreal.Vector(origin.x, origin.y, origin.z + ext.z + TEXT_GAP + TEXT_SIZE * 0.5)
front_yaw = jrot.yaw + JEFREY_FRONT_OFFSET
trot = unreal.Rotator(0.0, 0.0, front_yaw + TEXT_YAW_OFFSET)   # (roll, pitch, yaw)
if text_actor is None:
    text_actor = act.spawn_actor_from_class(unreal.TextRenderActor, tloc, trot)
    text_actor.set_actor_label(TEXT_LABEL)
    log("No existia el texto; creado.")
else:
    log("Texto antes: loc=%s rot=%s" % (text_actor.get_actor_location(), text_actor.get_actor_rotation()))

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
# el texto es la raiz del actor: se coloca al final, con transformacion de mundo
text_actor.set_actor_location(tloc, False, False)
text_actor.set_actor_rotation(trot, False)
log("Texto ahora: loc=%s rot=%s" % (text_actor.get_actor_location(), text_actor.get_actor_rotation()))

# Camara delante de Jefrey (en la direccion hacia donde apunta su +X), mirandolo
yaw = front_yaw
cam_loc = unreal.Vector(origin.x + math.cos(math.radians(yaw)) * CAM_DIST,
                        origin.y + math.sin(math.radians(yaw)) * CAM_DIST,
                        origin.z + ext.z * 0.4)
try:
    ues.set_level_viewport_camera_info(cam_loc, unreal.Rotator(0.0, -5.0, yaw + 180.0))
except Exception as e:
    warn("No pude mover la camara: %s" % e)
act.set_selected_level_actors([jef, text_actor])
log("LISTO (nivel sin guardar).")
