"""Render the brief's five views of the open .blend to PNG files.

Usage (background Blender, run from any directory):
    blender.exe -b hornet.blend -P scripts\render-views.py -- <out_dir> <prefix> [samples]

Views 1-4 are rendered through Cam_02_Hero with the Rig_Pivot empty (lights and
hero camera are parented to it) rotated about Z, so every view is lit like the
hero view. View 5 uses Cam_05_EyeCloseup with the pivot at 0.
"""
import sys
import os
import math
import time
import bpy

VIEWS = [
    ("01_front", "Cam_02_Hero", 35.0),
    ("02_hero", "Cam_02_Hero", 0.0),
    ("03_sideleft", "Cam_02_Hero", 125.0),
    ("04_backleft", "Cam_02_Hero", 170.0),
    ("05_eyecloseup", "Cam_05_EyeCloseup", 0.0),
]

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if len(argv) < 2:
    raise SystemExit("usage: -- <out_dir> <prefix> [samples]")
out_dir, prefix = argv[0], argv[1]
samples = int(argv[2]) if len(argv) > 2 else None
os.makedirs(out_dir, exist_ok=True)

scene = bpy.context.scene
print("engine:", scene.render.engine, "resolution:",
      scene.render.resolution_x, scene.render.resolution_y,
      scene.render.resolution_percentage)
if scene.render.engine == "CYCLES":
    prefs = bpy.context.preferences.addons.get("cycles")
    if prefs:
        cp = prefs.preferences
        print("compute_device_type:", cp.compute_device_type)
        try:
            cp.get_devices_for_type(cp.compute_device_type)
            print("devices:", [(d.name, d.type, d.use) for d in cp.devices])
        except Exception as exc:
            print("device listing failed:", exc)
    scene.cycles.device = "GPU"
    if samples is not None:
        scene.cycles.samples = samples
    print("cycles samples:", scene.cycles.samples, "device:", scene.cycles.device)

# Blender 5.x: the file may be saved with media_type VIDEO; stills need IMAGE first.
scene.render.image_settings.media_type = "IMAGE"
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGBA"

pivot = bpy.data.objects.get("Rig_Pivot")
if pivot is None:
    raise SystemExit("no Rig_Pivot empty in the file")

for name, cam_name, angle in VIEWS:
    cam = bpy.data.objects.get(cam_name)
    if cam is None:
        raise SystemExit(f"camera {cam_name} not found")
    pivot.rotation_euler = (0.0, 0.0, math.radians(angle))
    bpy.context.view_layer.update()
    scene.camera = cam
    loc = cam.matrix_world.translation
    path = os.path.join(out_dir, f"{prefix}-{name}.png")
    scene.render.filepath = path
    t0 = time.time()
    bpy.ops.render.render(write_still=True)
    print(f"rendered {name} via {cam_name} at pivot {angle:.0f} deg, camera at "
          f"({loc.x:.2f}, {loc.y:.2f}, {loc.z:.2f}) -> {path} in {time.time() - t0:.1f} s")

pivot.rotation_euler = (0.0, 0.0, 0.0)
print("done")
