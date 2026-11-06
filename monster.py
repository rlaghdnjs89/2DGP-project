import math

from pico2d import draw_rectangle

import config
import game_world

GRUNT_COLORS = {'run': (170, 60, 70), 'windup': (230, 150, 60), 'attack': (250, 80, 40), 'recover': (120, 70, 80)}
GRUNT_NEXT = {
    'windup': ('attack', config.GRUNT_ATTACK_TIME),
    'attack': ('recover', config.GRUNT_RECOVER_TIME),
    'recover': ('run', 0),
}

FAMILIAR_COLOR = (130, 70, 190)


class Monster:
    def __init__(self, x, y, player):
        self.x = x
        self.y = y
        self.player = player

    def handle_collision(self, group, other):
        if group == 'sword:monster':
            other.player.on_kill(self)
            game_world.remove_object(self)


class Grunt(Monster):
    SCORE = config.GRUNT_SCORE
    DASH_BONUS = 0
    AIRBORNE = False

    def __init__(self, x, y, player):
        super().__init__(x, y, player)
        self.state = 'run'
        self.timer = 0

    def update(self, dt):
        gap = self.x - self.player.x
        if self.state == 'run':
            if 0 <= gap <= config.GRUNT_ATTACK_RANGE:
                self.state = 'windup'
                self.timer = config.GRUNT_WINDUP_TIME
            elif 0 <= gap <= config.GRUNT_SIGHT:
                self.x -= config.GRUNT_SPEED * dt
        else:
            self.timer -= dt
            if self.timer <= 0:
                self.state, self.timer = GRUNT_NEXT[self.state]

    def draw(self, camera):
        left, bottom, right, top = self.get_bb()
        draw_rectangle(left - camera.x, bottom, right - camera.x, top, *GRUNT_COLORS[self.state], 255, True)

    def get_bb(self):
        half_w = config.GRUNT_W / 2
        reach = config.GRUNT_ATTACK_REACH if self.state == 'attack' else 0
        return self.x - half_w - reach, self.y, self.x + half_w, self.y + config.GRUNT_H

    def dash_y(self):
        return self.y


class Familiar(Monster):
    SCORE = config.FAMILIAR_SCORE
    DASH_BONUS = config.FAMILIAR_DASH_BONUS
    AIRBORNE = True

    def __init__(self, x, y, player):
        super().__init__(x, y, player)
        self.base_y = y
        self.time = 0

    def update(self, dt):
        self.time += dt
        self.y = self.base_y + config.FAMILIAR_FLOAT * math.sin(self.time * config.FAMILIAR_FLOAT_SPEED)

    def draw(self, camera):
        left, bottom, right, top = self.get_bb()
        draw_rectangle(left - camera.x, bottom, right - camera.x, top, *FAMILIAR_COLOR, 255, True)

    def get_bb(self):
        half = config.FAMILIAR_SIZE / 2
        return self.x - half, self.y - half, self.x + half, self.y + half

    def dash_y(self):
        return self.y - config.PLAYER_H / 2
