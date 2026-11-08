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
SCORE_SIZE = 72
LINE_SIZE = 24
OVERLAY_OPACITY = 0.55
BLINK_SPEED = 6
NEW_COLOR = (255, 214, 90)
SUB_COLOR = (200, 195, 220)

score = 0
kills = 0
stage = 0
cleared = False
best = 0
is_new = False
time = 0
camera = None


def set_result(player):
    global score, kills, stage, cleared
    score = player.score
    kills = player.kills
    stage = player.stage
    cleared = player.cleared


def init():
    global best, is_new, time, camera
    previous = record.load_best()
    is_new = score > previous
    if is_new:
        record.save_best(score)
        sound.play('new_record')
    best = max(previous, score)
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
    draw_text(LINE_SIZE, x, config.SCREEN_H * 0.68, '최종 점수', SUB_COLOR, align=0.5)
    draw_text(SCORE_SIZE, x, config.SCREEN_H * 0.6, f'{score:,}', align=0.5)
    if is_new and math.sin(time * BLINK_SPEED) > -0.3:
        draw_text(LINE_SIZE, x, config.SCREEN_H * 0.5, 'NEW RECORD!', NEW_COLOR, align=0.5)

    draw_text(LINE_SIZE, x, config.SCREEN_H * 0.42, f'최고 기록  {best:,}', align=0.5)
    draw_text(LINE_SIZE, x, config.SCREEN_H * 0.36, f'처치 수  {kills}', align=0.5)
    stage_name = config.STAGES[stage]['name']
    draw_text(LINE_SIZE, x, config.SCREEN_H * 0.3, f'도달 스테이지  STAGE {stage + 1} · {stage_name}', align=0.5)
    draw_text(LINE_SIZE, x, config.SCREEN_H * 0.14, 'R 재도전     ESC 타이틀', SUB_COLOR, align=0.5)
