from pico2d import draw_rectangle

import config

GRUNT_COLORS = {'run': (170, 60, 70), 'windup': (230, 150, 60), 'attack': (250, 80, 40), 'recover': (120, 70, 80)}
GRUNT_NEXT = {
    'windup': ('attack', config.GRUNT_ATTACK_TIME),
    'attack': ('recover', config.GRUNT_RECOVER_TIME),
    'recover': ('run', 0),
}


class Grunt:
    def __init__(self, x, y, player):
        self.x = x
        self.y = y
        self.player = player
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

    def handle_collision(self, group, other):
        pass
