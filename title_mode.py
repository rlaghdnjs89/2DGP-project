import math

from pico2d import SDL_BUTTON_LEFT, SDL_KEYDOWN, SDL_MOUSEBUTTONDOWN, SDL_MOUSEMOTION, SDLK_ESCAPE, SDLK_F1, SDLK_SPACE, SDLK_r

import config
import game_framework
import play_mode
import record
import sound
from background import draw_background
from camera import Camera
from obstacle import draw_strip
from player import PlayerArt
from sprite import get_image
from ui import Button, draw_overlay, draw_text, mouse_pos

LOGO_SIZE = 96
SUBTITLE_SIZE = 36
INFO_SIZE = 24
HELP_SIZE = 12
SCROLL_SPEED = 240
BLINK_SPEED = 5
LOGO_COLOR = (250, 250, 255)
SHADOW_COLOR = (40, 20, 70)
ACCENT_COLOR = (255, 90, 110)
GOLD_COLOR = (255, 214, 90)
SUB_COLOR = (200, 195, 220)
DEV_OPACITY = 0.75
DEV_TITLE_SIZE = 48
DEV_BUTTON_W = 220
DEV_BUTTON_H = 56
DEV_BUTTON_GAP = 250
DEV_RESET_W = 300
HELP = 'W 점프 (공중에서 2단)   S 슬라이딩   SPACE 일섬   좌클릭 베기   A D 보스전 이동   F 강화   ESC 일시 정지'

camera = None
time = 0
player_art = None
reset_armed = False
dev_open = False
# (버튼, 시작 스테이지 번호, 원석 다음에 나올 것)
dev_starts = []
dev_reset_button = None


def init():
    global camera, time, player_art, reset_armed, dev_open, dev_starts, dev_reset_button
    # 개발자 테스트에서 돌아오면 진짜 기록을 다시 보여 준다.
    record.end_dev()
    reset_armed = False
    dev_open = False
    dev_starts = []
    for row, (goal, label) in enumerate((('run', '스테이지'), ('midboss', '중간 보스'), ('boss', '보스'))):
        for stage in range(len(config.STAGES)):
            # 중간 보스는 스테이지 2에만 있다.
            if goal == 'midboss' and stage != config.MIDBOSS_STAGE:
                continue
            x = config.SCREEN_W / 2 + (stage - (len(config.STAGES) - 1) / 2) * DEV_BUTTON_GAP
            dev_starts.append((Button(x, config.SCREEN_H * (0.6 - row * 0.11), DEV_BUTTON_W, DEV_BUTTON_H, f'{label} {stage + 1}'), stage, goal))
    # 중간 보스 옆 칸. 버틸 시간이 거의 끝난 채로 시작해 격파 연출을 바로 시험한다.
    dev_starts.append((Button(config.SCREEN_W / 2 + DEV_BUTTON_GAP, config.SCREEN_H * (0.6 - 0.11), DEV_BUTTON_W, DEV_BUTTON_H, '마녀 격파'),
                       config.MIDBOSS_STAGE, 'midboss_end'))
    dev_reset_button = Button(config.SCREEN_W / 2, config.SCREEN_H * 0.26, DEV_RESET_W, DEV_BUTTON_H, '테스트 강화 초기화')
    camera = Camera()
    time = 0
    player_art = PlayerArt(0)


def handle_dev_event(event):
    global dev_open
    if event.type == SDL_KEYDOWN and event.key in (SDLK_F1, SDLK_ESCAPE):
        dev_open = False
    elif event.type == SDL_MOUSEMOTION:
        x, y = mouse_pos(event)
        for button, _, _ in dev_starts:
            button.hover = button.contains(x, y)
        dev_reset_button.hover = dev_reset_button.contains(x, y)
    elif event.type == SDL_MOUSEBUTTONDOWN and event.button == SDL_BUTTON_LEFT:
        x, y = mouse_pos(event)
        if dev_reset_button.contains(x, y):
            record.reset_dev()
            sound.play('upgrade')
            return
        for button, stage, goal in dev_starts:
            if button.contains(x, y):
                sound.play('ui_start')
                record.start_dev()
                play_mode.dev_start = (stage, goal)
                game_framework.change_mode(play_mode)
                return


def handle_event(event):
    global reset_armed, dev_open
    if dev_open:
        handle_dev_event(event)
    elif event.type == SDL_KEYDOWN and event.key == SDLK_F1:
        dev_open = True
    elif event.type == SDL_KEYDOWN and event.key == SDLK_ESCAPE:
        game_framework.quit()
    elif event.type == SDL_KEYDOWN and event.key == SDLK_r:
        # 실수로 지우지 않도록 한 번 더 눌러야 초기화한다.
        if reset_armed:
            record.reset()
        reset_armed = not reset_armed
    elif event.type == SDL_MOUSEBUTTONDOWN or (event.type == SDL_KEYDOWN and event.key == SDLK_SPACE):
        sound.play('ui_start')
        play_mode.dev_start = None
        game_framework.change_mode(play_mode)


def update(dt):
    global time
    time += dt
    camera.x += SCROLL_SPEED * dt


def draw():
    draw_background(0, camera)
    draw_strip(get_image(config.STAGES[0]['ground']), camera.x, camera.x + config.SCREEN_W, 0, camera)
    player_art.draw('run', time, config.PLAYER_SCREEN_X, config.GROUND_TOP)

    center_x = config.SCREEN_W / 2
    if dev_open:
        draw_dev_panel(center_x)
        return
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
    draw_text(INFO_SIZE, config.SCREEN_W - 20, config.SCREEN_H - 30, 'F1 개발자 테스트', SUB_COLOR, align=1)


def draw_dev_panel(center_x):
    draw_overlay('assets/ui/black.png', DEV_OPACITY)
    draw_text(DEV_TITLE_SIZE, center_x, config.SCREEN_H * 0.86, '개발자 테스트', ACCENT_COLOR, align=0.5)
    draw_text(INFO_SIZE, center_x, config.SCREEN_H * 0.77, '골드 무제한 · 스킬트리 3단계까지 모두 열림 · 기록은 저장되지 않음', GOLD_COLOR, align=0.5)
    draw_text(INFO_SIZE, center_x, config.SCREEN_H * 0.71, '진화의 원석에서 시작합니다. F로 강화 창을 열고, 배운 스킬을 다시 누르면 취소됩니다.', SUB_COLOR, align=0.5)
    for button, _, _ in dev_starts:
        button.draw()
    dev_reset_button.draw()
    draw_text(INFO_SIZE, center_x, config.SCREEN_H * 0.18, '고른 강화는 게임을 끄기 전까지 다음 테스트에도 남습니다', SUB_COLOR, align=0.5)
    draw_text(INFO_SIZE, center_x, 40, 'F1 또는 ESC 닫기', align=0.5)
