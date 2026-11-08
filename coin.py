import math
import random

import config
import game_world
import sound
from sprite import Strip

FRAME_W = 14
FPS = 12


class Coin:
    """처치한 자리에서 튀어 올랐다가 플레이어에게 빨려 든다. 골드는 처치할 때 이미 들어와 있어 구덩이로 떨어져도 잃지 않는다."""

    def __init__(self, x, y, player, audible):
        self.x = x
        self.y = y
        self.player = player
        self.audible = audible
        self.vx = random.uniform(-config.COIN_POP_SPEED_X, config.COIN_POP_SPEED_X)
        self.vy = random.uniform(config.COIN_POP_SPEED_Y * 0.5, config.COIN_POP_SPEED_Y)
        self.time = 0
        self.strip = Strip('assets/ui/coin.png', FRAME_W)

    def update(self, dt):
        self.time += dt
        if self.time < config.COIN_POP_TIME:
            self.x += self.vx * dt
            self.y += self.vy * dt
            self.vy -= config.COIN_GRAVITY * dt
            return
        dx = self.player.x - self.x
        dy = self.player.y + config.PLAYER_H / 2 - self.y
        distance = math.hypot(dx, dy)
        # 달리는 플레이어를 따라잡도록 시간이 갈수록 빨라진다.
        step = (config.COIN_ABSORB_SPEED + config.COIN_ABSORB_ACCEL * (self.time - config.COIN_POP_TIME)) * dt
        if distance <= step:
            if self.audible:
                sound.play('coin')
            game_world.remove_object(self)
        else:
            self.x += dx / distance * step
            self.y += dy / distance * step

    def draw(self, camera):
        self.strip.draw(int(self.time * FPS) % self.strip.count, self.x - camera.x, self.y - camera.y)
