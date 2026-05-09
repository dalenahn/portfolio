# Godot 4 — top-down sandbox

A small top-down 2D scene. Player spawns in the corner, has to reach the goal tile, step count is shown in the UI and resets when the goal is reached.

## Run

1. Install Godot 4.2+
2. Open `project.godot`
3. Press F5

Move with WASD.

## Files

- `scenes/main.tscn` — the scene
- `scripts/main.gd` — episode loop, step counter, reset
- `scripts/player.gd` — CharacterBody2D movement
- `icon.svg` — project icon
