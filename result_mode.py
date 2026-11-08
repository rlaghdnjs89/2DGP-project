import math

from pico2d import SDL_KEYDOWN, SDLK_ESCAPE, SDLK_r

import config
import game_framework
import play_mode
import record
import sound
import title_mode
from background import draw_background
from camera import Camera
from ui import draw_overlay, draw_text

TITLE_SIZE = 60
LINE_SIZE = 24
OVERLAY_OPACITY = 0.55
BLINK_SPEED = 6
NEW_COLOR = (255, 214, 90)
SUB_COLOR = (200, 195, 220)

kills = 0
stage = 0
cleared = False
best_stage = 0
is_new = False
time = 0
camera = None


def set_result(player):
    global kills, stage, cleared
    kills = player.kills
    stage = player.stage
    cleared = player.cleared


def init():
    global best_stage, is_new, time, camera
    best_stage = record.load_best_stage()
    is_new = stage + 1 > best_stage
    if is_new:
        best_stage = stage + 1
        record.save_best_stage(best_stage)
        sound.play('new_record')
    time = 0
    camera = Camera()


def handle_event(event):
    if event.type != SDL_KEYDOWN:
        return
    if event.key == SDLK_r:
        game_framework.change_mode(play_mode)
    elif event.key == SDLK_ESCAPE:
        game_framework.change_mode(title_mode)


def update(dt):
    global time
    time += dt


def draw():
    draw_background(stage, camera)
    draw_overlay('assets/ui/black.png', OVERLAY_OPACITY)

    x = config.SCREEN_W / 2
    draw_text(TITLE_SIZE, x, config.SCREEN_H * 0.82, 'CLEAR' if cleared else 'GAME OVER', align=0.5)
    stage_name = config.STAGES[stage]['name']
    draw_text(LINE_SIZE, x, config.SCREEN_H * 0.6, f'도달 스테이지  STAGE {stage + 1} · {stage_name}', align=0.5)
    if is_new and math.sin(time * BLINK_SPEED) > -0.3:
        draw_text(LINE_SIZE, x, config.SCREEN_H * 0.54, 'NEW RECORD!', NEW_COLOR, align=0.5)
    draw_text(LINE_SIZE, x, config.SCREEN_H * 0.46, f'최고 도달 스테이지  {best_stage}', align=0.5)
    draw_text(LINE_SIZE, x, config.SCREEN_H * 0.4, f'처치 수  {kills}', align=0.5)
    draw_text(LINE_SIZE, x, config.SCREEN_H * 0.14, 'R 재도전     ESC 타이틀', SUB_COLOR, align=0.5)
