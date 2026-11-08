from pico2d import SDL_KEYDOWN, SDLK_ESCAPE, SDLK_r

import config
import game_framework
import play_mode
import record
import title_mode
from background import draw_background
from camera import Camera
from ui import draw_overlay, draw_text

TITLE_SIZE = 60
LINE_SIZE = 24
OVERLAY_OPACITY = 0.55
SUB_COLOR = (200, 195, 220)
GOLD_COLOR = (255, 214, 90)

kills = 0
run_gold = 0
stage = 0
cleared = False
camera = None


def set_result(player):
    global kills, run_gold, stage, cleared
    kills = player.kills
    run_gold = player.run_gold
    stage = player.stage
    cleared = player.cleared


def init():
    global camera
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
    pass


def draw():
    draw_background(stage, camera)
    draw_overlay('assets/ui/black.png', OVERLAY_OPACITY)

    x = config.SCREEN_W / 2
    draw_text(TITLE_SIZE, x, config.SCREEN_H * 0.82, 'CLEAR' if cleared else 'GAME OVER', align=0.5)
    stage_name = config.STAGES[stage]['name']
    draw_text(LINE_SIZE, x, config.SCREEN_H * 0.6, f'도달 스테이지  STAGE {stage + 1} · {stage_name}', align=0.5)
    draw_text(LINE_SIZE, x, config.SCREEN_H * 0.52, f'이번 런에서 모은 골드  +{run_gold:,}', GOLD_COLOR, align=0.5)
    draw_text(LINE_SIZE, x, config.SCREEN_H * 0.46, f'보유 골드  {record.data["gold"]:,}', GOLD_COLOR, align=0.5)
    draw_text(LINE_SIZE, x, config.SCREEN_H * 0.4, f'처치 수  {kills}', align=0.5)
    draw_text(LINE_SIZE, x, config.SCREEN_H * 0.28, '골드는 그대로 남습니다', SUB_COLOR, align=0.5)
    draw_text(LINE_SIZE, x, config.SCREEN_H * 0.14, 'R 재도전     ESC 타이틀', SUB_COLOR, align=0.5)
