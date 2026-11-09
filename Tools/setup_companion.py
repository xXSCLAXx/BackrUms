# -*- coding: utf-8 -*-
# setup_companion.py
# Crea /Game/BackrUms/Companion/BP_Companion (Character con la malla de Anakin, en T-pose)
# y, si LVL_Test esta abierto, coloca una instancia junto al PlayerStart SIN guardar el nivel.
# Es idempotente: se puede volver a ejecutar para reajustar valores (no borra el grafo).
#
# Uso en el editor:  Cmd ->  py "C:/Users/sevic/Documents/Unreal Projects/BackrUrms 5.8/Tools/setup_companion.py"
import unreal

PKG_DIR       = "/Game/BackrUms/Companion"
BP_NAME       = "BP_Companion"
MESH_PATH     = "/Game/BackrUms/Characters/Anakin/Richard+choque__1_/SkeletalMeshes/Richard+choque__1_"
LEVEL_NAME    = "LVL_Test"
MESH_YAW      = -90.0    # si camina de costado o de espaldas, prueba 0, 90, 180
MAX_WALK_SPEED = 650.0
ACTOR_SCALE   = 2.5      # igual que el Anakin original del nivel (~2.5)
SIDE_OFFSET   = 150.0    # solo para colocarlo al inicio, a la derecha del PlayerStart

def log(m):  unreal.log("[Companion] " + str(m))
def warn(m): unreal.log_warning("[Companion] " + str(m))

eal   = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()

# 1) Malla
mesh = unreal.load_asset(MESH_PATH)
if mesh is None:
    raise RuntimeError("No encuentro la malla de Anakin en " + MESH_PATH)

# 2) Blueprint (se crea solo si no existe)
bp_path = PKG_DIR + "/" + BP_NAME
if not eal.does_directory_exist(PKG_DIR):
    eal.make_directory(PKG_DIR)
if eal.does_asset_exist(bp_path):
    bp = unreal.load_asset(bp_path)
    log("BP_Companion ya existe, solo reajusto valores (el grafo no se toca).")
else:
    factory = unreal.BlueprintFactory()
    factory.set_editor_property("parent_class", unreal.Character)
    bp = tools.create_asset(BP_NAME, PKG_DIR, unreal.Blueprint, factory)
    if bp is None:
        raise RuntimeError("No se pudo crear el Blueprint")
    log("BP_Companion creado.")

cls = bp.generated_class()
cdo = unreal.get_default_object(cls)

# 3) Capsula y malla segun el tamano real de la malla
half_h, radius, feet_z = 88.0, 34.0, 0.0
try:
    b = mesh.get_bounds()
    half_h = max(float(b.box_extent.z), 20.0)
    radius = max(min(float(max(b.box_extent.x, b.box_extent.y)) * 0.5, 60.0), 20.0)
    feet_z = float(b.origin.z) - float(b.box_extent.z)
    log("Bounds malla: extent=%s origin=%s -> capsula half_height=%.1f radius=%.1f" % (b.box_extent, b.origin, half_h, radius))
except Exception as e:
    warn("No pude leer los bounds (%s); uso valores por defecto." % e)

capsule = cdo.get_editor_property("capsule_component")
capsule.set_editor_property("capsule_half_height", half_h)
capsule.set_editor_property("capsule_radius", radius)
capsule.set_editor_property("relative_scale3d", unreal.Vector(ACTOR_SCALE, ACTOR_SCALE, ACTOR_SCALE))  # escala capsula y malla juntas

mesh_comp = cdo.get_editor_property("mesh")
mesh_comp.set_editor_property("skeletal_mesh", mesh)
mesh_comp.set_editor_property("relative_location", unreal.Vector(0.0, 0.0, -half_h - feet_z))
mesh_comp.set_editor_property("relative_rotation", unreal.Rotator(0.0, 0.0, MESH_YAW))  # (roll, pitch, yaw)

# 4) Movimiento: sin animaciones, T-pose, mira hacia donde camina
cdo.set_editor_property("use_controller_rotation_yaw", False)
cdo.set_editor_property("auto_possess_ai", unreal.AutoPossessAI.PLACED_IN_WORLD_OR_SPAWNED)  # necesario para que se mueva
cmc = cdo.get_editor_property("character_movement")
cmc.set_editor_property("max_walk_speed", MAX_WALK_SPEED)
cmc.set_editor_property("orient_rotation_to_movement", True)
cmc.set_editor_property("use_controller_desired_rotation", False)
cmc.set_editor_property("rotation_rate", unreal.Rotator(0.0, 0.0, 540.0))

# 5) Compilar y guardar SOLO el Blueprint nuevo
try:
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
except Exception as e:
    warn("compile_blueprint fallo: %s (compilalo con el boton Compilar del BP)" % e)
eal.save_loaded_asset(bp)

# Verificacion leyendo de vuelta
cdo2 = unreal.get_default_object(bp.generated_class())
log("VERIF malla=%s | speed=%s | autopossess=%s" % (
    cdo2.get_editor_property("mesh").get_editor_property("skeletal_mesh"),
    cdo2.get_editor_property("character_movement").get_editor_property("max_walk_speed"),
    cdo2.get_editor_property("auto_possess_ai")))

# 6) Colocarlo en el nivel abierto (NO guarda el nivel)
try:
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    if world.get_name() != LEVEL_NAME:
        warn("El nivel abierto es '%s', no '%s'. No coloco nada; arrastra BP_Companion al nivel a mano." % (world.get_name(), LEVEL_NAME))
    else:
        actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        all_actors = actors.get_all_level_actors()
        if any(a.get_class().get_name() == BP_NAME + "_C" for a in all_actors):
            log("Ya hay un BP_Companion en el nivel; no coloco otro.")
        else:
            starts = [a for a in all_actors if isinstance(a, unreal.PlayerStart)]
            if not starts:
                warn("No hay PlayerStart; arrastra BP_Companion al nivel a mano.")
            else:
                ps = starts[0]
                loc = ps.get_actor_location() + ps.get_actor_right_vector() * SIDE_OFFSET + unreal.Vector(0, 0, half_h * ACTOR_SCALE + 20.0)
                a = actors.spawn_actor_from_class(cls, loc, ps.get_actor_rotation())
                log("Companion colocado en el nivel (SIN guardar el nivel): %s" % a)
except Exception as e:
    warn("No pude colocarlo en el nivel (%s). Arrastra BP_Companion desde el Content Browser." % e)

log("LISTO. Ahora agrega los nodos del Event Graph y compila.")
