from pico2d import draw_rectangle

import config

GROUND_MARK_GAP = 200

LOW_COLOR = (120, 110, 100)
HIGH_COLOR = (70, 70, 90)


class Obstacle:
    def __init__(self, left, bottom, w, h, color):
        self.left = left
        self.bottom = bottom
        self.right = left + w
        self.top = bottom + h
        self.color = color

    def update(self, dt):
        pass

    def draw(self, camera):
        draw_rectangle(self.left - camera.x, self.bottom, self.right - camera.x, self.top, *self.color, 255, True)

    def get_bb(self):
        return self.left, self.bottom, self.right, self.top

    def handle_collision(self, group, other):
        pass


def make_low_obstacle(left):
    return Obstacle(left, config.GROUND_TOP, config.LOW_OBSTACLE_W, config.LOW_OBSTACLE_H, LOW_COLOR)


def make_high_obstacle(left):
    bottom = config.GROUND_TOP + config.HIGH_OBSTACLE_CLEARANCE
    # 천장까지 막아 점프로는 넘을 수 없게 한다.
    return Obstacle(left, bottom, config.HIGH_OBSTACLE_W, config.SCREEN_H - bottom, HIGH_COLOR)


class Ground:
    def __init__(self, left, right):
        self.left = left
        self.right = right
        self.top = config.GROUND_TOP

    def update(self, dt):
        pass

    def draw(self, camera):
        left = self.left - camera.x
        right = self.right - camera.x
        draw_rectangle(left, 0, right, self.top, 90, 80, 70, 255, True)
        # 배경이 없어도 달리는 속도가 보이도록 일정 간격으로 표시한다.
        mark = self.left + (-self.left % GROUND_MARK_GAP)
        while mark < self.right:
            screen_x = mark - camera.x
            draw_rectangle(screen_x, self.top - 12, screen_x + 8, self.top, 60, 52, 45, 255, True)
            mark += GROUND_MARK_GAP

    def get_bb(self):
        return self.left, 0, self.right, self.top

    def handle_collision(self, group, other):
        pass
