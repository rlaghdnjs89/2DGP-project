import config
import game_world
from camera import Camera
from chunk_manager import ChunkManager
from player import Player
from ui import HUD

player = None
camera = None
chunks = None
game_over_timer = None


def init():
    global player, camera, chunks, game_over_timer
    game_world.clear()
    player = Player()
    camera = Camera()
    chunks = ChunkManager(player)
    game_over_timer = None
    game_world.add_object(player, game_world.LAYER_PLAYER)
    game_world.add_object(HUD(player), game_world.LAYER_UI)
    game_world.add_collision_pair('player:ground', player, None)
    # 같은 프레임에 닿으면 베기가 이기도록 피격 그룹보다 먼저 처리한다.
    game_world.add_collision_pair('sword:monster', None, None)
    game_world.add_collision_pair('player:obstacle', player, None)
    game_world.add_collision_pair('player:monster', player, None)


def handle_event(event):
    if game_over_timer is None:
        player.handle_event(event)


def update(dt):
    global game_over_timer
    if game_over_timer is not None:
        game_over_timer -= dt
        if game_over_timer <= 0:
            # 결과 화면이 생기기 전까지는 바로 다시 시작한다.
            init()
            return
        dt *= config.GAME_OVER_TIME_SCALE

    game_world.update(dt)
    game_world.handle_collisions()
    camera.follow(player)
    chunks.update(camera)
    if game_over_timer is None and (player.hp <= 0 or player.get_bb()[3] < 0):
        game_over_timer = config.GAME_OVER_TIME


def draw():
    game_world.render(camera)
