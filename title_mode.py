import math

from pico2d import SDL_KEYDOWN, SDL_MOUSEBUTTONDOWN, SDLK_ESCAPE, SDLK_SPACE, SDLK_r

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
GOLD_COLOR = (255, 214, 90)
SUB_COLOR = (200, 195, 220)
HELP = 'W 점프 (공중에서 2단)   S 슬라이딩   SPACE 일섬   좌클릭 베기   A D 보스전 이동   F 강화   ESC 일시 정지'

camera = None
time = 0
run_sprite = None
reset_armed = False


def init():
    global camera, time, run_sprite, reset_armed
    reset_armed = False
    camera = Camera()
    time = 0
    run_sprite = Strip('assets/player/run.png', 64)
    sound.play_music(0)


def handle_event(event):
    global reset_armed
    if event.type == SDL_KEYDOWN and event.key == SDLK_ESCAPE:
        game_framework.quit()
    elif event.type == SDL_KEYDOWN and event.key == SDLK_r:
        # 실수로 지우지 않도록 한 번 더 눌러야 초기화한다.
        if reset_armed:
            record.reset()
        reset_armed = not reset_armed
    elif event.type == SDL_MOUSEBUTTONDOWN or (event.type == SDL_KEYDOWN and event.key == SDLK_SPACE):
        sound.play('ui_start')
        game_framework.change_mode(play_mode)


def update(dt):
    global time
    time += dt
    camera.x += SCROLL_SPEED * dt


def draw():
    draw_background(0, camera)
    draw_strip(get_image(config.STAGES[0]['ground']), camera.x, camera.x + config.SCREEN_W, 0, camera)
    run_sprite.draw(int(time * RUN_FPS) % run_sprite.count, config.PLAYER_SCREEN_X, config.GROUND_TOP + config.SPRITE_CENTER_Y)

    center_x = config.SCREEN_W / 2
    logo_y = config.SCREEN_H * 0.68
    draw_text(LOGO_SIZE, center_x + 5, logo_y - 5, 'BLADE SHIFT', SHADOW_COLOR, align=0.5)
    draw_text(LOGO_SIZE, center_x, logo_y, 'BLADE SHIFT', LOGO_COLOR, align=0.5)
    # 로고를 가로지르는 칼자국
    get_image('assets/ui/white.png').rotate_draw(0.05, center_x, logo_y, 860, 3)
    draw_text(SUBTITLE_SIZE, center_x, logo_y - 80, '차원 베기 러너', ACCENT_COLOR, align=0.5)

    data = record.data
    draw_text(INFO_SIZE, center_x, config.SCREEN_H * 0.46, f'보유 골드 {data["gold"]:,}', GOLD_COLOR, align=0.5)
    draw_text(INFO_SIZE, center_x, config.SCREEN_H * 0.4,
              f'처치한 보스 {len(data["bosses"])}/{len(config.STAGES)}     최고 도달 스테이지 {data["best_stage"]}', align=0.5)
    if math.sin(time * BLINK_SPEED) > -0.4:
        draw_text(INFO_SIZE, center_x, config.SCREEN_H * 0.32, '클릭 또는 SPACE로 시작', align=0.5)
    reset_text = '한 번 더 누르면 골드, 강화, 기록이 모두 지워집니다' if reset_armed else 'R 기록 초기화'
    draw_text(INFO_SIZE, center_x, config.SCREEN_H * 0.24, reset_text, ACCENT_COLOR if reset_armed else SUB_COLOR, align=0.5)
    draw_text(HELP_SIZE * 2, center_x, 40, HELP, align=0.5)
