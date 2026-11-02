"""Bake every point cache of the open .blend, then render the animation.

Usage (background Blender):
    blender.exe -b hornet.blend -P scripts\render-animation.py -- <out_mp4> [samples] [frame_step] [stills:f1,f2,...]

Bakes all physics caches (cloth) with bake_all, renders the scene's frame
range to an MP4 (H.264), and optionally renders the listed frames as PNG
stills next to the MP4 (same base name plus -fNNN.png) for inspection.
"""
import sys
import os
import time
import bpy

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if len(argv) < 1:
    raise SystemExit("usage: -- <out_mp4> [samples] [frame_step] [stills:f1,f2,...]")
out_path = argv[0]
samples = int(argv[1]) if len(argv) > 1 and argv[1] != "-" else None
frame_step = int(argv[2]) if len(argv) > 2 else 1
stills = []
for a in argv[3:]:
    if a.startswith("stills:"):
        stills = [int(x) for x in a[7:].split(",") if x]
os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)

scene = bpy.context.scene
print("engine:", scene.render.engine, "camera:", scene.camera.name if scene.camera else None,
      "frames:", scene.frame_start, scene.frame_end, "fps:", scene.render.fps)
if scene.render.engine == "CYCLES":
    scene.cycles.device = "GPU"
    if samples is not None:
        scene.cycles.samples = samples
    print("cycles samples:", scene.cycles.samples)

# Bake all point caches (cloth). Report what exists first.
for ob in scene.objects:
    for mod in ob.modifiers:
        if mod.type == "CLOTH":
            pc = mod.point_cache
            print(f"cloth on {ob.name}: cache frames {pc.frame_start}-{pc.frame_end}, "
                  f"baked={pc.is_baked}, disk={pc.use_disk_cache}")
t0 = time.time()
bpy.ops.ptcache.bake_all(bake=True)
print(f"baked all caches in {time.time() - t0:.1f} s")
for ob in scene.objects:
    for mod in ob.modifiers:
        if mod.type == "CLOTH":
            print(f"cloth on {ob.name}: baked={mod.point_cache.is_baked}")

rs = scene.render
base, _ = os.path.splitext(out_path)

# Stills first (PNG), for inspection.
if stills:
    rs.image_settings.media_type = "IMAGE"
    rs.image_settings.file_format = "PNG"
    rs.image_settings.color_mode = "RGBA"
    for f in stills:
        scene.frame_set(f)
        rs.filepath = f"{base}-f{f:03d}.png"
        t0 = time.time()
        bpy.ops.render.render(write_still=True)
        print(f"rendered still frame {f} -> {rs.filepath} in {time.time() - t0:.1f} s")

# Then the video.
scene.frame_step = frame_step
rs.image_settings.media_type = "VIDEO"
rs.image_settings.file_format = "FFMPEG"
rs.ffmpeg.format = "MPEG4"
rs.ffmpeg.codec = "H264"
rs.ffmpeg.constant_rate_factor = "HIGH"
rs.ffmpeg.ffmpeg_preset = "GOOD"
rs.ffmpeg.gopsize = 12
rs.filepath = out_path
rs.use_file_extension = False
t0 = time.time()
bpy.ops.render.render(animation=True)
print(f"rendered animation -> {out_path} in {time.time() - t0:.1f} s")
print("done")
