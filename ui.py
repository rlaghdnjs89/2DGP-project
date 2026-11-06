from pico2d import draw_rectangle

import config

HP_SIZE = 32
HP_GAP = 10
MARGIN = 20


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
