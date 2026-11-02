"""Enable the BlenderMCP addon on startup and save that in the preferences.

Blender runs this once through `blender --python scripts/enable-addon.py`, which
scripts/restart-blender.ps1 passes. The addon registers its own auto-start, so
the socket server comes up a moment later without anyone pressing a button.
Safe to run again: an addon that is already enabled is left alone.
"""

import bpy

MODULE = "blender_mcp"

if MODULE in bpy.context.preferences.addons:
    print(f"BlenderMCP: addon '{MODULE}' is already enabled.")
else:
    bpy.ops.preferences.addon_enable(module=MODULE)
    if MODULE in bpy.context.preferences.addons:
        bpy.ops.wm.save_userpref()
        print(f"BlenderMCP: addon '{MODULE}' enabled and preferences saved.")
    else:
        print(f"BlenderMCP: FAILED to enable addon '{MODULE}'. Check the console above for the import error.")
