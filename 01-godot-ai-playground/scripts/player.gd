extends CharacterBody2D

@export var speed: float = 140.0

signal goal_reached

func _physics_process(_delta: float) -> void:
	var direction := Vector2(
		Input.get_axis("move_left", "move_right"),
		Input.get_axis("move_up", "move_down")
	).normalized()

	velocity = direction * speed
	move_and_slide()

func _on_goal_body_entered(body: Node2D) -> void:
	if body == self:
		emit_signal("goal_reached")
