import game_world
from camera import Camera
from chunk_manager import ChunkManager
from player import Player

player = None
camera = None
chunks = None


def init():
    global player, camera, chunks
    game_world.clear()
    player = Player()
    camera = Camera()
    chunks = ChunkManager()
    game_world.add_object(player, game_world.LAYER_PLAYER)
    game_world.add_collision_pair('player:ground', player, None)


def handle_event(event):
    player.handle_event(event)


def update(dt):
    game_world.update(dt)
    game_world.handle_collisions()
    camera.follow(player)
    chunks.update(camera)


def draw():
    game_world.render(camera)
