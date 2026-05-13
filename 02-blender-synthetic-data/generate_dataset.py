"""
Synthetic dataset generator (early version).

Renders a batch of cubes at random rotations against a plain background.
No labels yet, just images.
"""

import bpy
import math
import os
import random
import sys


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    count = 10
    out = "./sample_output"
    for i, a in enumerate(argv):
        if a == "--count":
            count = int(argv[i + 1])
        if a == "--out":
            out = argv[i + 1]
    return count, out


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def main():
    count, out = parse_args()
    os.makedirs(out, exist_ok=True)

    scene = bpy.context.scene
    scene.render.resolution_x = 256
    scene.render.resolution_y = 256
    scene.render.image_settings.file_format = "PNG"

    clear_scene()
    bpy.ops.object.camera_add(location=(0, -5, 2), rotation=(math.radians(75), 0, 0))
    scene.camera = bpy.context.object
    bpy.ops.object.light_add(type="AREA", location=(2, -2, 4))
    bpy.context.object.data.energy = 500.0

    for i in range(count):
        # remove previous cube if any
        for obj in [o for o in bpy.data.objects if o.type == "MESH"]:
            bpy.data.objects.remove(obj, do_unlink=True)

        bpy.ops.mesh.primitive_cube_add(size=1.0)
        cube = bpy.context.object
        cube.rotation_euler = (
            random.uniform(0, math.tau),
            random.uniform(0, math.tau),
            random.uniform(0, math.tau),
        )

        scene.render.filepath = os.path.join(out, f"{i:05d}.png")
        bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    main()
