#!/usr/bin/env python3
"""M1 SIGNATURE MOVE — extruded 3D type slam + camera push + DOF.
Blender bpy headless (Cycles CPU, low samples, film transparent). ALPHA PNG sequence
for compositing as accent layer. Framing validated: word band ~75% width, volt card
inside frame so alpha shows at edges. Engine log: blender-bpy/cycles-cpu."""
import bpy, os, sys, math

OUT = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else "/tmp/my-project/p21work/scratch/m1_seq"
WORD = sys.argv[sys.argv.index("--word") + 1] if "--word" in sys.argv else "WELCOME"
FSTART = int(sys.argv[sys.argv.index("--start") + 1]) if "--start" in sys.argv else 0
FEND = int(sys.argv[sys.argv.index("--end") + 1]) if "--end" in sys.argv else None
FPS = 24
DUR = 3.5
N = int(FPS * DUR)
W, H = 405, 720
os.makedirs(OUT, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene
scn.render.engine = 'CYCLES'
scn.cycles.device = 'CPU'
scn.cycles.samples = 18
scn.cycles.use_denoising = True
scn.render.film_transparent = True
scn.render.resolution_x = W
scn.render.resolution_y = H
scn.render.fps = FPS
scn.render.image_settings.file_format = 'PNG'
scn.render.image_settings.color_mode = 'RGBA'
scn.render.filepath = os.path.join(OUT, "f_")
scn.frame_start = FSTART
scn.frame_end = (N - 1) if FEND is None else FEND

font_path = "/home/z/my-project/download/edit-master-skill/assets/fonts/Montserrat.ttf"
font = bpy.data.fonts.load(font_path)

cu = bpy.data.curves.new(type='FONT', name='txt')
cu.body = WORD
cu.font = font
cu.align_x = 'CENTER'
cu.align_y = 'CENTER'
cu.extrude = 0.10
cu.bevel_depth = 0.016
cu.bevel_resolution = 2
cu.size = 0.52
txt = bpy.data.objects.new("Txt", cu)
scn.collection.objects.link(txt)
txt.rotation_euler = (math.radians(84), 0, 0)
txt.location = (0, 0, 0.75)

mat = bpy.data.materials.new("slab")
mat.use_nodes = True
bsdf = mat.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (0.09, 0.09, 0.10, 1)
bsdf.inputs["Roughness"].default_value = 0.30
if "Metallic" in bsdf.inputs:
    bsdf.inputs["Metallic"].default_value = 0.12
txt.data.materials.append(mat)

volt = bpy.data.materials.new("volt")
volt.use_nodes = True
vb = volt.node_tree.nodes["Principled BSDF"]
vb.inputs["Base Color"].default_value = (0.847, 0.953, 0.29, 1)
vb.inputs["Roughness"].default_value = 0.9
import bmesh
plane = bpy.data.objects.new("VoltCard", bpy.data.meshes.new("vm"))
scn.collection.objects.link(plane)
bm = bmesh.new()
bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.92)
bm.to_mesh(plane.data)
bm.free()
plane.data.materials.append(volt)
plane.rotation_euler = (math.radians(90), 0, 0)
plane.location = (0, 0.02, 0.50)

key = bpy.data.lights.new("key", 'AREA')
key.energy = 1800
key.size = 5
ko = bpy.data.objects.new("Key", key)
scn.collection.objects.link(ko)
ko.location = (2.6, 3.6, 3.6)
ko.rotation_euler = (math.radians(28), math.radians(-30), 0)

fill = bpy.data.lights.new("fill", 'AREA')
fill.energy = 500
fill.size = 8
fo = bpy.data.objects.new("Fill", fill)
scn.collection.objects.link(fo)
fo.location = (-2.6, -2.0, 1.8)
fo.rotation_euler = (math.radians(72), math.radians(36), 0)

world = bpy.data.worlds.new("w")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.045, 0.045, 0.055, 1)
world.node_tree.nodes["Background"].inputs[1].default_value = 1.0
scn.world = world

cam = bpy.data.cameras.new("cam")
cam.lens = 50
cam.dof.use_dof = True
cam.dof.focus_distance = 5.6
cam.dof.aperture_fstop = 2.8
co = bpy.data.objects.new("Cam", cam)
scn.collection.objects.link(co)
co.location = (0, -5.5, 0.32)
co.rotation_euler = (math.radians(86), 0, 0)
scn.camera = co


def ease_out_back(t, s=1.55):
    t = min(max(t, 0.0), 1.0)
    t1 = t - 1
    return 1 + (s + 1) * (t1 ** 3) + s * (t1 ** 2)


slam_frames = 10
for f in range(FSTART, scn.frame_end + 1):
    scn.frame_set(f)
    t = f / slam_frames
    s = 3.2 - (3.2 - 1.0) * ease_out_back(t) if f <= slam_frames else 1.0
    txt.scale = (s, s, s)
    txt.keyframe_insert("scale", frame=f)
    if f > slam_frames:
        w = math.sin((f - slam_frames) / 3.0) * 0.015
        txt.rotation_euler = (math.radians(84 + w * 8), 0, 0)
        txt.keyframe_insert("rotation_euler", frame=f)
    y = -5.5 + 0.5 * (f / max(1, scn.frame_end))
    co.location = (0, y, 0.32 - 0.10 * (f / max(1, scn.frame_end)))
    co.keyframe_insert("location", frame=f)

bpy.context.view_layer.update()
bpy.ops.render.render(animation=True)
print("M1 RENDER DONE", OUT, "frames:", FSTART, "-", scn.frame_end)
