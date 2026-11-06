import game_world
from camera import Camera
from obstacle import Ground
from player import Player

player = None
camera = None


def init():
    global player, camera
    game_world.clear()
    player = Player()
    camera = Camera()
    game_world.add_object(player, game_world.LAYER_PLAYER)
    game_world.add_collision_pair('player:ground', player, None)

    ground = Ground(0, 1_000_000)
    game_world.add_object(ground, game_world.LAYER_MAP)
    game_world.add_collision_pair('player:ground', None, ground)


def handle_event(event):
    player.handle_event(event)


def update(dt):
    game_world.update(dt)
    game_world.handle_collisions()
    camera.follow(player)


def draw():
    game_world.render(camera)
