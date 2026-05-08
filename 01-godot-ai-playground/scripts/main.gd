extends Node2D

@onready var player: CharacterBody2D = $Player
@onready var goal: Area2D = $Goal
@onready var status_label: Label = $UI/StatusLabel

var episode_steps: int = 0

func _ready() -> void:
	goal.body_entered.connect(_on_goal_reached)
	_reset_episode()

func _process(_delta: float) -> void:
	episode_steps += 1
	status_label.text = "Steps: %d" % episode_steps

func _on_goal_reached(body: Node2D) -> void:
	if body == player:
		status_label.text = "Goal reached in %d steps!" % episode_steps
		await get_tree().create_timer(1.0).timeout
		_reset_episode()

func _reset_episode() -> void:
	episode_steps = 0
	player.global_position = Vector2(64, 64)
