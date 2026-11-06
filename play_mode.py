from pico2d import SDL_KEYDOWN, SDL_KEYUP, SDLK_ESCAPE, SDLK_q

import config
import game_framework
import game_world
import result_mode
import title_mode
from background import Background
from camera import Camera
from chunk_manager import ChunkManager
from player import Player
from ui import HUD, draw_overlay, draw_text

PAUSE_OPACITY = 0.6
PAUSE_TITLE_SIZE = 60
PAUSE_MENU_SIZE = 24

player = None
camera = None
chunks = None
game_over_timer = None
paused = False


def init():
    global player, camera, chunks, game_over_timer, paused
    paused = False
    game_world.clear()
    camera = Camera()
    player = Player(camera)
    chunks = ChunkManager(player)
    game_over_timer = None
    game_world.add_object(Background(player), game_world.LAYER_BACKGROUND)
    game_world.add_object(player, game_world.LAYER_PLAYER)
    game_world.add_object(HUD(player), game_world.LAYER_UI)
    game_world.add_collision_pair('player:ground', player, None)
    game_world.add_collision_pair('player:gate', player, None)
    # 같은 프레임에 닿으면 베기가 이기도록 피격 그룹보다 먼저 처리한다.
    game_world.add_collision_pair('sword:monster', None, None)
    game_world.add_collision_pair('sword:bullet', None, None)
    game_world.add_collision_pair('player:obstacle', player, None)
    game_world.add_collision_pair('player:monster', player, None)
    game_world.add_collision_pair('player:bullet', player, None)
    game_world.add_collision_pair('player:wall', player, None)
    game_world.add_collision_pair('reflected:mage', None, None)


def handle_event(event):
    global paused
    if event.type == SDL_KEYDOWN and event.key == SDLK_ESCAPE and game_over_timer is None:
        paused = not paused
    elif paused:
        if event.type == SDL_KEYDOWN and event.key == SDLK_q:
            game_framework.change_mode(title_mode)
        # 멈춘 동안 S를 떼어도 슬라이딩 입력이 눌린 채로 남지 않게 한다.
        elif event.type == SDL_KEYUP:
            player.handle_event(event)
    elif game_over_timer is None:
        player.handle_event(event)


def update(dt):
    global game_over_timer
    if paused:
        return
    if game_over_timer is not None:
        game_over_timer -= dt
        if game_over_timer <= 0:
            result_mode.set_result(player)
            game_framework.change_mode(result_mode)
            return
        dt *= config.GAME_OVER_TIME_SCALE
    elif player.bullet_wall:
        player.tick_bullet_time(dt)
        dt *= config.BULLET_TIME_SCALE

    game_world.update(dt)
    game_world.handle_collisions()
    camera.follow(player, dt)
    chunks.update(camera, dt)
    if game_over_timer is None and (player.hp <= 0 or player.get_bb()[3] < 0):
        game_over_timer = config.GAME_OVER_TIME


def draw():
    game_world.render(camera)
    if paused:
        draw_overlay('assets/ui/black.png', PAUSE_OPACITY)
        x = config.SCREEN_W / 2
        draw_text(PAUSE_TITLE_SIZE, x, config.SCREEN_H * 0.6, '일시 정지', align=0.5)
        draw_text(PAUSE_MENU_SIZE, x, config.SCREEN_H * 0.45, 'ESC 계속     Q 타이틀', align=0.5)
