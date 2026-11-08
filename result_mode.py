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
SUB_COLOR = (200, 195, 220)
GOLD_COLOR = (255, 214, 90)
NEW_COLOR = (255, 214, 90)
BLINK_SPEED = 6
CLEAR_TIME_SIZE = 72

kills = 0
run_gold = 0
stage = 0
cleared = False
clear_time = 0
is_new_best = False
time = 0
camera = None


def set_result(player):
    global kills, run_gold, stage, cleared, clear_time
    clear_time = player.run_time
    kills = player.kills
    run_gold = player.run_gold
    stage = player.stage
    cleared = player.cleared


def init():
    global camera, is_new_best, time
    is_new_best = False
    time = 0
    if cleared:
        best = record.data['best_clear_time']
        is_new_best = best is None or clear_time < best
        if is_new_best:
            record.data['best_clear_time'] = clear_time
            sound.play('new_record')
    record.save()
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


def format_time(seconds):
    minutes, rest = divmod(seconds, 60)
    return f'{int(minutes)}:{rest:05.2f}'


def draw():
    draw_background(stage, camera)
    draw_overlay('assets/ui/black.png', OVERLAY_OPACITY)

    x = config.SCREEN_W / 2
    if cleared:
        draw_clear(x)
    else:
        draw_death(x)
    draw_text(LINE_SIZE, x, config.SCREEN_H * 0.14, 'R 재도전     ESC 타이틀', SUB_COLOR, align=0.5)


def draw_clear(x):
    draw_text(TITLE_SIZE, x, config.SCREEN_H * 0.82, 'CLEAR', GOLD_COLOR, align=0.5)
    draw_text(LINE_SIZE, x, config.SCREEN_H * 0.68, '클리어 시간', SUB_COLOR, align=0.5)
    draw_text(CLEAR_TIME_SIZE, x, config.SCREEN_H * 0.6, format_time(clear_time), align=0.5)
    if is_new_best and math.sin(time * BLINK_SPEED) > -0.3:
        draw_text(LINE_SIZE, x, config.SCREEN_H * 0.5, 'NEW RECORD!', NEW_COLOR, align=0.5)
    draw_text(LINE_SIZE, x, config.SCREEN_H * 0.43, f'최단 기록  {format_time(record.data["best_clear_time"])}', align=0.5)
    draw_text(LINE_SIZE, x, config.SCREEN_H * 0.36, f'이번 런에서 모은 골드  +{run_gold:,}', GOLD_COLOR, align=0.5)
    draw_text(LINE_SIZE, x, config.SCREEN_H * 0.3, f'처치 수  {kills}', align=0.5)


def draw_death(x):
    draw_text(TITLE_SIZE, x, config.SCREEN_H * 0.82, 'GAME OVER', align=0.5)
    stage_name = config.STAGES[stage]['name']
    draw_text(LINE_SIZE, x, config.SCREEN_H * 0.6, f'도달 스테이지  STAGE {stage + 1} · {stage_name}', align=0.5)
    draw_text(LINE_SIZE, x, config.SCREEN_H * 0.52, f'이번 런에서 모은 골드  +{run_gold:,}', GOLD_COLOR, align=0.5)
    draw_text(LINE_SIZE, x, config.SCREEN_H * 0.46, f'보유 골드  {record.data["gold"]:,}', GOLD_COLOR, align=0.5)
    draw_text(LINE_SIZE, x, config.SCREEN_H * 0.4, f'처치 수  {kills}', align=0.5)
    draw_text(LINE_SIZE, x, config.SCREEN_H * 0.28, '골드는 그대로 남습니다', SUB_COLOR, align=0.5)
