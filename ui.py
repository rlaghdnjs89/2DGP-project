import ctypes
import random

from pico2d import TTF_SizeUTF8, load_font

import config
import record
from sprite import get_image

HP_SIZE = 32
HP_GAP = 10
MARGIN = 20
FONT_PATH = 'assets/fonts/Galmuri11.ttf'
TEXT_COLOR = (250, 250, 250)
SCORE_SIZE = 24
COMBO_SIZE = 24
DASH_SIZE = 24
DASH_COOLDOWN_COLOR = (130, 130, 130)
PHASE_SIZE = 24
HEART_SHAKE_TIME = 0.3
HEART_SHAKE = 4
HEAL_NOTICE_TIME = 1.2
HEAL_COLOR = (120, 240, 140)
FLASH_TIME = 0.5
BANNER_HOLD_TIME = 1.0
BANNER_SHRINK_TIME = 0.5
# 픽셀 폰트가 깨지지 않는 크기만 거쳐 줄어든다.
BANNER_SIZES = (60, 48, 36, 24)

fonts = {}


def get_font(size):
    if size not in fonts:
        fonts[size] = load_font(FONT_PATH, size)
    return fonts[size]


def text_width(font, text):
    w = ctypes.c_int()
    h = ctypes.c_int()
    TTF_SizeUTF8(font.font, text.encode('utf-8'), ctypes.byref(w), ctypes.byref(h))
    return w.value


def draw_text(size, x, y, text, color=TEXT_COLOR, align=0):
    """align은 x가 글자의 어디에 놓이는지 나타낸다. 0은 왼쪽 끝, 0.5는 가운데, 1은 오른쪽 끝이다."""
    font = get_font(size)
    font.draw(x - text_width(font, text) * align, y, text, color)


def draw_overlay(path, opacity):
    image = get_image(path)
    image.opacify(opacity)
    image.draw_to_origin(0, 0, config.SCREEN_W, config.SCREEN_H)
    # opacify는 텍스처 자체를 바꾸므로 같은 이미지를 쓰는 다른 곳에 남지 않게 되돌린다.
    image.opacify(1)


class HUD:
    def __init__(self, player):
        self.player = player
        self.shown_phase = player.phase
        self.shown_hp = player.hp
        self.best = record.load_best()
        self.flash = 0
        self.heart_shake = 0
        self.heal_notice = 0
        # 배너는 페이즈가 바뀔 때만 나오므로 처음에는 이미 끝난 상태로 둔다.
        self.banner_time = BANNER_HOLD_TIME + BANNER_SHRINK_TIME

    def update(self, dt):
        self.flash = max(0, self.flash - dt)
        self.heart_shake = max(0, self.heart_shake - dt)
        self.heal_notice = max(0, self.heal_notice - dt)
        self.banner_time += dt
        if self.player.hp < self.shown_hp:
            self.heart_shake = HEART_SHAKE_TIME
        elif self.player.hp > self.shown_hp:
            self.heal_notice = HEAL_NOTICE_TIME
        self.shown_hp = self.player.hp
        if self.shown_phase != self.player.phase:
            self.shown_phase = self.player.phase
            self.flash = FLASH_TIME
            self.banner_time = 0

    def phase_label(self):
        return f'PHASE {self.player.phase + 1} · {config.PHASES[self.player.phase]["name"]}'

    def draw_phase(self):
        center_x = config.SCREEN_W / 2
        top_y = config.SCREEN_H - MARGIN - PHASE_SIZE / 2
        t = (self.banner_time - BANNER_HOLD_TIME) / BANNER_SHRINK_TIME
        if t >= 1:
            draw_text(PHASE_SIZE, center_x, top_y, self.phase_label(), align=0.5)
            return
        t = max(0, t)
        size = BANNER_SIZES[min(len(BANNER_SIZES) - 1, int(t * len(BANNER_SIZES)))]
        y = config.SCREEN_H * 0.72 + (top_y - config.SCREEN_H * 0.72) * t
        draw_text(size, center_x, y, self.phase_label(), align=0.5)

    def draw(self, camera):
        full = get_image('assets/ui/heart_full.png')
        empty = get_image('assets/ui/heart_empty.png')
        for i in range(config.HP_MAX):
            left = MARGIN + i * (HP_SIZE + HP_GAP)
            bottom = config.SCREEN_H - MARGIN - HP_SIZE
            if self.heart_shake > 0:
                left += random.randint(-HEART_SHAKE, HEART_SHAKE)
                bottom += random.randint(-HEART_SHAKE, HEART_SHAKE)
            image = full if i < self.player.hp else empty
            image.draw_to_origin(left, bottom, HP_SIZE, HP_SIZE)

        self.draw_phase()

        right = config.SCREEN_W - MARGIN
        top = config.SCREEN_H - MARGIN - SCORE_SIZE / 2
        draw_text(SCORE_SIZE, right, top, f'SCORE {self.player.score:,}', align=1)
        draw_text(SCORE_SIZE, right, top - SCORE_SIZE - 6, f'BEST {max(self.best, self.player.score):,}', align=1)
        if self.player.combo > 0:
            draw_text(COMBO_SIZE, right, config.SCREEN_H / 2, f'COMBO {self.player.combo}', align=1)
        if self.heal_notice > 0:
            draw_text(COMBO_SIZE, right, config.SCREEN_H / 2 - COMBO_SIZE - 8, 'HP +1', HEAL_COLOR, align=1)

        if self.player.dash_cooldown > 0:
            draw_text(DASH_SIZE, MARGIN, MARGIN + DASH_SIZE / 2, f'일섬 {self.player.dash_cooldown:.1f}', DASH_COOLDOWN_COLOR)
        else:
            draw_text(DASH_SIZE, MARGIN, MARGIN + DASH_SIZE / 2, '일섬 준비')

        if self.flash > 0:
            draw_overlay('assets/ui/white.png', self.flash / FLASH_TIME)
