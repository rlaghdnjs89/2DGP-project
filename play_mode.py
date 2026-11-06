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
    game_world.add_collision_pair('player:obstacle', player, None)


def handle_event(event):
    player.handle_event(event)


def update(dt):
    game_world.update(dt)
    game_world.handle_collisions()
    camera.follow(player)
    chunks.update(camera)
    # 게임 오버와 결과 화면이 생기기 전까지 추락하면 바로 다시 시작한다.
    if player.get_bb()[3] < 0:
        init()


def draw():
    game_world.render(camera)
