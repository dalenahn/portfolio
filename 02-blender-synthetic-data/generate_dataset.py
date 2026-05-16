"""
Synthetic dataset generator for Blender 4.x.

Renders N images of a single 3D primitive (cube / sphere / cone) at randomized
position, rotation, material, and background. For each image, writes a YOLO-format
label file with the object's 2D bounding box.

Run headless:

    blender --background --python generate_dataset.py -- --count 500 --out ./sample_output --seed 42
"""

import argparse
import math
import os
import random
import sys
from dataclasses import dataclass

import bpy
from mathutils import Vector


# ---------- CLI ----------

def parse_args() -> argparse.Namespace:
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--count", type=int, default=50, help="Number of images to render")
    p.add_argument("--out", type=str, default="./sample_output", help="Output directory")
    p.add_argument("--seed", type=int, default=42, help="RNG seed for reproducibility")
    p.add_argument("--resolution", type=int, default=256, help="Square image edge in px")
    return p.parse_args(argv)


# ---------- Scene setup ----------

PRIMITIVES = ("cube", "sphere", "cone")
CLASS_IDS = {name: i for i, name in enumerate(PRIMITIVES)}


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for block in (bpy.data.meshes, bpy.data.materials, bpy.data.lights):
        for item in list(block):
            block.remove(item)


def make_camera() -> bpy.types.Object:
    bpy.ops.object.camera_add(location=(0, -5, 2), rotation=(math.radians(75), 0, 0))
    cam = bpy.context.object
    bpy.context.scene.camera = cam
    return cam


def make_light() -> bpy.types.Object:
    bpy.ops.object.light_add(type="AREA", location=(2, -2, 4))
    light = bpy.context.object
    light.data.energy = 500.0
    light.data.size = 2.0
    return light


def make_primitive(kind: str) -> bpy.types.Object:
    if kind == "cube":
        bpy.ops.mesh.primitive_cube_add(size=1.0)
    elif kind == "sphere":
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.6)
    elif kind == "cone":
        bpy.ops.mesh.primitive_cone_add(radius1=0.6, depth=1.2)
    else:
        raise ValueError(f"Unknown primitive: {kind}")
    return bpy.context.object


def colorize(obj: bpy.types.Object, rgb: tuple[float, float, float]) -> None:
    mat = bpy.data.materials.new(name=f"mat_{obj.name}")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
    bsdf.inputs["Roughness"].default_value = random.uniform(0.2, 0.8)
    obj.data.materials.append(mat)


def set_background_color(rgb: tuple[float, float, float]) -> None:
    world = bpy.context.scene.world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (*rgb, 1.0)


# ---------- Bounding box math ----------

@dataclass
class BBox:
    cls_id: int
    cx: float
    cy: float
    w: float
    h: float

    def to_yolo(self) -> str:
        return f"{self.cls_id} {self.cx:.6f} {self.cy:.6f} {self.w:.6f} {self.h:.6f}"


def project_bbox(obj: bpy.types.Object, cam: bpy.types.Object, cls_id: int) -> BBox | None:
    """Project object's 8 mesh-bound corners to camera NDC, then to pixel-normalized YOLO."""
    scene = bpy.context.scene
    render = scene.render
    width, height = render.resolution_x, render.resolution_y

    corners = [obj.matrix_world @ Vector(c) for c in obj.bound_box]

    from bpy_extras.object_utils import world_to_camera_view
    xs, ys = [], []
    for c in corners:
        ndc = world_to_camera_view(scene, cam, c)
        if ndc.z <= 0:
            return None
        xs.append(ndc.x)
        ys.append(1.0 - ndc.y)  # flip Y to image coords

    x_min, x_max = max(0.0, min(xs)), min(1.0, max(xs))
    y_min, y_max = max(0.0, min(ys)), min(1.0, max(ys))
    if x_max <= x_min or y_max <= y_min:
        return None

    cx = (x_min + x_max) / 2.0
    cy = (y_min + y_max) / 2.0
    w = x_max - x_min
    h = y_max - y_min
    return BBox(cls_id, cx, cy, w, h)


# ---------- Render loop ----------

def render_one(index: int, out_dir: str, cam: bpy.types.Object) -> None:
    clear_scene()
    cam = make_camera()
    make_light()

    kind = random.choice(PRIMITIVES)
    obj = make_primitive(kind)
    obj.location = (
        random.uniform(-1.2, 1.2),
        random.uniform(-0.5, 0.5),
        random.uniform(0.0, 0.8),
    )
    obj.rotation_euler = (
        random.uniform(0, math.tau),
        random.uniform(0, math.tau),
        random.uniform(0, math.tau),
    )
    colorize(obj, (random.random(), random.random(), random.random()))
    set_background_color((random.random() * 0.4, random.random() * 0.4, random.random() * 0.4))

    img_path = os.path.join(out_dir, "images", f"{index:05d}.png")
    label_path = os.path.join(out_dir, "labels", f"{index:05d}.txt")
    bpy.context.scene.render.filepath = img_path
    bpy.ops.render.render(write_still=True)

    bbox = project_bbox(obj, cam, CLASS_IDS[kind])
    with open(label_path, "w") as f:
        if bbox is not None:
            f.write(bbox.to_yolo() + "\n")


def main() -> None:
    args = parse_args()
    random.seed(args.seed)

    os.makedirs(os.path.join(args.out, "images"), exist_ok=True)
    os.makedirs(os.path.join(args.out, "labels"), exist_ok=True)

    scene = bpy.context.scene
    scene.render.resolution_x = args.resolution
    scene.render.resolution_y = args.resolution
    scene.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in {e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items} else "BLENDER_EEVEE"
    scene.render.image_settings.file_format = "PNG"

    cam = make_camera()
    for i in range(args.count):
        render_one(i, args.out, cam)
        if i % 25 == 0:
            print(f"[gen] rendered {i + 1}/{args.count}")

    # write a tiny data.yaml so the dataset is YOLO-trainable as-is
    yaml_path = os.path.join(args.out, "data.yaml")
    with open(yaml_path, "w") as f:
        f.write("path: .\n")
        f.write("train: images\n")
        f.write("val: images\n")
        f.write(f"nc: {len(PRIMITIVES)}\n")
        f.write(f"names: {list(PRIMITIVES)}\n")
    print(f"[gen] done. dataset at {args.out}")


if __name__ == "__main__":
    main()
