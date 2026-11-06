import ctypes

from pico2d import TTF_SizeUTF8, draw_rectangle, load_font

import config

HP_SIZE = 32
HP_GAP = 10
MARGIN = 20
FONT_PATH = 'assets/fonts/Galmuri11.ttf'
TEXT_COLOR = (250, 250, 250)
SCORE_SIZE = 24
COMBO_SIZE = 24

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


class HUD:
    def __init__(self, player):
        self.player = player

    def update(self, dt):
        pass

    def draw(self, camera):
        for i in range(config.HP_MAX):
            left = MARGIN + i * (HP_SIZE + HP_GAP)
            bottom = config.SCREEN_H - MARGIN - HP_SIZE
            filled = i < self.player.hp
            draw_rectangle(left, bottom, left + HP_SIZE, bottom + HP_SIZE, 210, 40, 60, 255, filled)

        right = config.SCREEN_W - MARGIN
        top = config.SCREEN_H - MARGIN - SCORE_SIZE / 2
        draw_text(SCORE_SIZE, right, top, f'SCORE {self.player.score:,}', align=1)
        if self.player.combo > 0:
            draw_text(COMBO_SIZE, right, config.SCREEN_H / 2, f'COMBO {self.player.combo}', align=1)
