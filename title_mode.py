import math

from pico2d import SDL_KEYDOWN, SDL_MOUSEBUTTONDOWN, SDLK_ESCAPE, SDLK_SPACE

import config
import game_framework
import play_mode
import record
import sound
from background import draw_background
from camera import Camera
from obstacle import draw_strip
from sprite import Strip, get_image
from ui import draw_text

LOGO_SIZE = 96
SUBTITLE_SIZE = 36
INFO_SIZE = 24
HELP_SIZE = 12
SCROLL_SPEED = 240
RUN_FPS = 16
BLINK_SPEED = 5
LOGO_COLOR = (250, 250, 255)
SHADOW_COLOR = (40, 20, 70)
ACCENT_COLOR = (255, 90, 110)
HELP = 'W 점프 (공중에서 2단)   S 슬라이딩   SPACE 일섬   좌클릭 베기   ESC 일시 정지'

camera = None
time = 0
best = 0
run_sprite = None


def init():
    global camera, time, best, run_sprite
    camera = Camera()
    time = 0
    best = record.load_best()
    run_sprite = Strip('assets/player/run.png', 64)
    sound.play_music(0)


def handle_event(event):
    if event.type == SDL_KEYDOWN and event.key == SDLK_ESCAPE:
        game_framework.quit()
    elif event.type == SDL_MOUSEBUTTONDOWN or (event.type == SDL_KEYDOWN and event.key == SDLK_SPACE):
        sound.play('ui_start')
        game_framework.change_mode(play_mode)


def update(dt):
    global time
    time += dt
    camera.x += SCROLL_SPEED * dt


def draw():
    draw_background(0, camera)
    draw_strip(get_image(config.PHASES[0]['ground']), camera.x, camera.x + config.SCREEN_W, 0, camera)
    run_sprite.draw(int(time * RUN_FPS) % run_sprite.count, config.PLAYER_SCREEN_X, config.GROUND_TOP + config.SPRITE_CENTER_Y)

    center_x = config.SCREEN_W / 2
    logo_y = config.SCREEN_H * 0.68
    draw_text(LOGO_SIZE, center_x + 5, logo_y - 5, 'BLADE SHIFT', SHADOW_COLOR, align=0.5)
    draw_text(LOGO_SIZE, center_x, logo_y, 'BLADE SHIFT', LOGO_COLOR, align=0.5)
    # 로고를 가로지르는 칼자국
    get_image('assets/ui/white.png').rotate_draw(0.05, center_x, logo_y, 860, 3)
    draw_text(SUBTITLE_SIZE, center_x, logo_y - 80, '차원 베기 러너', ACCENT_COLOR, align=0.5)

    draw_text(INFO_SIZE, center_x, config.SCREEN_H * 0.4, f'BEST {best:,}', align=0.5)
    if math.sin(time * BLINK_SPEED) > -0.4:
        draw_text(INFO_SIZE, center_x, config.SCREEN_H * 0.32, '클릭 또는 SPACE로 시작', align=0.5)
    draw_text(HELP_SIZE * 2, center_x, 40, HELP, align=0.5)
