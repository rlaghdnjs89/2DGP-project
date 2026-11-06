from pico2d import draw_rectangle

import config


class Run:
    COLOR = (40, 90, 200)

    def __init__(self, player):
        self.player = player

    def enter(self):
        pass

    def update(self, dt):
        pass


class Player:
    def __init__(self):
        self.x = config.PLAYER_SCREEN_X
        self.y = config.GROUND_TOP
        self.prev_y = self.y
        self.vy = 0
        self.h = config.PLAYER_H
        self.on_ground = True

        self.run = Run(self)
        self.state = self.run

    def change_state(self, state):
        self.state = state
        state.enter()

    def handle_event(self, event):
        pass

    def update(self, dt):
        self.state.update(dt)

        self.x += config.SCROLL_SPEED * dt

        # 등가속도 공식을 그대로 써서 프레임 수와 무관하게 점프 높이가 같게 한다.
        gravity = config.GRAVITY if self.vy > 0 else config.GRAVITY * config.FALL_GRAVITY_RATIO
        self.prev_y = self.y
        self.y += self.vy * dt - gravity * dt * dt / 2
        self.vy -= gravity * dt
        # 다음 충돌 처리에서 지면에 닿으면 다시 True가 된다.
        self.on_ground = False

    def draw(self, camera):
        left, bottom, right, top = self.get_bb()
        draw_rectangle(left - camera.x, bottom, right - camera.x, top, *self.state.COLOR, 255, True)

    def get_bb(self):
        half_w = config.PLAYER_W / 2
        return self.x - half_w, self.y, self.x + half_w, self.y + self.h

    def handle_collision(self, group, other):
        if group == 'player:ground' and self.vy <= 0 and self.prev_y >= other.top:
            self.y = other.top
            self.vy = 0
            self.on_ground = True
