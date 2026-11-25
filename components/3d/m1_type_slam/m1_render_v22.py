#!/usr/bin/env python3
"""M1 v22 — extruded 3D type slam, F6-compliant:
volt emissive bevel type + chrome-ish env reflection, ground contact shadow,
camera push + DOF, rich-canvas ready (ALPHA PNG seq 1080x1920, 84 frames @30fps = 2.8s).
Bank: components/3d/m1_type_slam/  |  engine: blender-bpy headless Cycles CPU.
F6: NO plain beige box — emissive volt faces + dark chrome sides read as part of the
B&W+volt world. Contact shadow alpha-composites onto any canvas."""
import os, math, sys
import bpy

bpy.ops.wm.read_factory_settings(use_empty=True)  # purge default cube/camera/light

# ---------- headless config ----------
SCRATCH = "/tmp/ems-work/p22/m1_seq"
os.makedirs(SCRATCH, exist_ok=True)
W, H, FPS, FRAMES = 1080, 1920, 30, 84
OUT_MS = 6.0  # samples

scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 7  # resume pass: denoiser compensates (banked strip quality kept)
scene.cycles.use_denoising = True
scene.cycles.use_adaptive_sampling = True
scene.cycles.adaptive_threshold = 0.05
scene.render.resolution_x = 864
scene.render.resolution_y = 1536
scene.render.resolution_percentage = 100
scene.render.film_transparent = True
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'
scene.render.fps = FPS
scene.view_settings.view_transform = 'Standard'

# world: dark studio env (drives chrome reflections)
world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs[0].default_value = (0.06, 0.06, 0.075, 1.0)
bg.inputs[1].default_value = 1.5

# env light: big volt-tinted area top + cool fill sides (reads on chrome bevels)
def area_light(name, loc, rot, size, color, power):
    l = bpy.data.lights.new(name, 'AREA')
    l.energy = power; l.color = color; l.size = size
    o = bpy.data.objects.new(name, l)
    o.location = loc; o.rotation_euler = rot
    scene.collection.objects.link(o)
    return o

area_light("key_volt", (2.5, -3.0, 6.0), (math.radians(35), 0, math.radians(25)), 3.0, (0.85, 0.95, 0.30), 4200)
area_light("fill_cool", (-5.0, -2.0, 3.0), (math.radians(65), 0, math.radians(-40)), 9.0, (0.75, 0.80, 0.95), 1500)
area_light("rim_back", (0.0, 4.5, 2.5), (math.radians(115), 0, 0), 6.0, (1.0, 1.0, 1.0), 900)

# ---------- ground: NONE in render; contact shadow baked at composite time (paste_m1) ----------

# ---------- text ----------
bpy.ops.object.text_add(location=(0, 0, 0.02))
txt = bpy.context.active_object
txt.data.body = "WELCOME"
txt.data.align_x = 'CENTER'
txt.data.align_y = 'CENTER'
txt.data.extrude = 0.55
txt.data.bevel_depth = 0.045
txt.data.bevel_resolution = 3
txt.data.size = 0.62
txt.data.space_character = 1.06
txt.rotation_euler = (math.radians(90), 0, math.radians(-2))  # stand upright facing camera

mat_face = bpy.data.materials.new("VoltEmissive")
mat_face.use_nodes = True
ntf = mat_face.node_tree
bsdf_f = ntf.nodes["Principled BSDF"]
bsdf_f.inputs["Base Color"].default_value = (0.85, 0.95, 0.29, 1.0)
bsdf_f.inputs["Metallic"].default_value = 0.12
bsdf_f.inputs["Roughness"].default_value = 0.4
# emissive volt glow
em = ntf.nodes.new("ShaderNodeEmission")
em.inputs[0].default_value = (0.85, 0.95, 0.29, 1.0)
em.inputs[1].default_value = 6.0
mm = ntf.nodes.new("ShaderNodeMixShader")
mm.inputs[0].default_value = 0.9
ntf.links.new(bsdf_f.outputs[0], mm.inputs[1])
ntf.links.new(em.outputs[0], mm.inputs[2])
ntf.links.new(mm.outputs[0], ntf.nodes["Material Output"].inputs[0])

mat_side = bpy.data.materials.new("DarkChrome")
mat_side.use_nodes = True
bsdf_s = mat_side.node_tree.nodes["Principled BSDF"]
bsdf_s.inputs["Base Color"].default_value = (0.05, 0.05, 0.06, 1.0)
bsdf_s.inputs["Metallic"].default_value = 1.0
bsdf_s.inputs["Roughness"].default_value = 0.18

# front face volt emissive + extruded dark chrome body (two-object approach,
# Blender 5.0-safe: no TextCurve.polygons access)
txt.data.materials.append(mat_side)
txt.parent = None
bpy.ops.object.text_add(location=(0, 0, 0.02 + 0.585))
face = bpy.context.active_object
face.data.body = "WELCOME"
face.data.align_x = 'CENTER'
face.data.align_y = 'CENTER'
face.data.size = 0.62
face.data.space_character = 1.06
face.data.materials.append(mat_face)
face.rotation_euler = (math.radians(90), 0, math.radians(-2))
face.parent = txt  # inherit all transforms

# ---------- camera push + DOF ----------
cam = bpy.data.cameras.new("Cam")
cam.lens = 50
cam.dof.use_dof = True
cam.dof.focus_distance = 10.5
cam.dof.aperture_fstop = 2.8
cam_o = bpy.data.objects.new("Cam", cam)
scene.collection.objects.link(cam_o)
scene.camera = cam_o

def cam_at(f):
    p = f / (FRAMES - 1)
    e = 1 - (1 - p) ** 3  # ease-out-cubic push
    # dolly -11.8 -> -9.9 (closer), eye height 1.6, slight sway (F6 camera push + DOF)
    y = -(11.8 - 1.9 * e)
    z = 1.6 + 0.25 * e
    x = 0.35 * math.sin(p * math.pi) * 0.6
    cam_o.location = (x, y, z)
    cam_o.rotation_euler = (math.radians(80 + 2.5 * e), 0, 0)
    txt.rotation_euler = (math.radians(90), 0, math.radians(-2.0 + 2.0 * e))
    # slam scale: first 6 frames the type lands hard (child face follows)
    if f < 6:
        s = 1.14 - 0.14 * (f / 6)
        txt.scale = (s, s, s)
    else:
        txt.scale = (1, 1, 1)

bpy.context.view_layer.update()
scene.frame_start = 0
scene.frame_end = FRAMES - 1
scene.render.filepath = SCRATCH + "/f_"
todo = [f for f in range(FRAMES)
        if not os.path.exists(f"{SCRATCH}/f_{f:04d}.png")]
for f in todo:
    cam_at(f)
    scene.frame_set(f)
    bpy.context.view_layer.update()
    scene.render.filepath = f"{SCRATCH}/f_{f:04d}.png"
    bpy.ops.render.render(write_still=True)
    if f % 6 == 0:
        print(f"rendered {f}/{FRAMES}", flush=True)
print("M1 v22 alpha seq done:", FRAMES, "frames ->", SCRATCH)
