# Blender — synthetic dataset generator

Renders YOLO-format labeled images of randomized 3D primitives. Headless Python, deterministic given a seed.

## Run

```
blender --background --python generate_dataset.py -- --count 500 --out ./sample_output --seed 42
```

Each render produces a 256x256 PNG of a single primitive (cube, sphere, or cone) with randomized position, rotation, material, and background, plus a YOLO label file with the 2D bounding box.

Output:

```
sample_output/
├── images/00000.png ...
├── labels/00000.txt ...
└── data.yaml
```

Requires Blender 4.x.
