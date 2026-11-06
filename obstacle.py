import random

import config
from sprite import Strip, get_image

LOW_IMAGES = ('assets/map/low_crate.png', 'assets/map/low_rock.png')
HIGH_IMAGE = 'assets/map/high_pillar.png'
GATE_FRAME_W = 64
GATE_FPS = 14
PLATFORM_IMAGE = 'assets/map/platform.png'
PLATFORM_CAP_IMAGE = 'assets/map/platform_cap.png'
PLATFORM_CAP_W = 32


def draw_strip(image, left, right, bottom, camera):
    """가로로 이어지는 이미지를 [left, right] 구간에 깔되 화면에 보이는 부분만 그린다."""
    x = int(max(left, camera.x))
    end = int(min(right, camera.x + config.SCREEN_W))
    while x < end:
        src = x % image.w
        w = min(image.w - src, end - x)
        image.clip_draw_to_origin(src, 0, w, image.h, x - camera.x, bottom, w, image.h)
        x += w


class Obstacle:
    def __init__(self, left, bottom, w, h, image_path):
        self.left = left
        self.bottom = bottom
        self.right = left + w
        self.top = bottom + h
        self.image = get_image(image_path)

    def update(self, dt):
        pass

    def draw(self, camera):
        self.image.draw_to_origin(self.left - camera.x, self.bottom, self.right - self.left, self.top - self.bottom)

    def get_bb(self):
        return self.left, self.bottom, self.right, self.top

    def handle_collision(self, group, other):
        pass


def make_low_obstacle(left):
    return Obstacle(left, config.GROUND_TOP, config.LOW_OBSTACLE_W, config.LOW_OBSTACLE_H, random.choice(LOW_IMAGES))


def make_high_obstacle(left):
    bottom = config.GROUND_TOP + config.HIGH_OBSTACLE_CLEARANCE
    # 천장까지 막아 점프로는 넘을 수 없게 한다.
    return Obstacle(left, bottom, config.HIGH_OBSTACLE_W, config.SCREEN_H - bottom, HIGH_IMAGE)


class PhaseGate:
    def __init__(self, x, phase):
        self.x = x
        self.phase = phase
        self.time = 0
        self.sprite = Strip('assets/map/gate.png', GATE_FRAME_W)

    def update(self, dt):
        self.time += dt

    def draw(self, camera):
        frame = int(self.time * GATE_FPS) % self.sprite.count
        center_y = config.GROUND_TOP + self.sprite.image.h * config.SPRITE_SCALE / 2
        self.sprite.draw(frame, self.x + config.GATE_W / 2 - camera.x, center_y)

    def get_bb(self):
        # 2단 점프로 넘어가지 못하도록 화면 위까지 막는다.
        return self.x, config.GROUND_TOP, self.x + config.GATE_W, config.SCREEN_H

    def handle_collision(self, group, other):
        pass


class Platform:
    def __init__(self, left, right, top):
        self.left = left
        self.right = right
        self.top = top

    def update(self, dt):
        pass

    def draw(self, camera):
        image = get_image(PLATFORM_IMAGE)
        bottom = self.top - image.h
        draw_strip(image, self.left + PLATFORM_CAP_W, self.right - PLATFORM_CAP_W, bottom, camera)
        cap = get_image(PLATFORM_CAP_IMAGE)
        center_y = bottom + image.h / 2
        half_cap = PLATFORM_CAP_W / 2
        cap.draw(self.left + half_cap - camera.x, center_y, PLATFORM_CAP_W, image.h)
        cap.composite_draw(0, 'h', self.right - half_cap - camera.x, center_y, PLATFORM_CAP_W, image.h)

    def get_bb(self):
        return self.left, self.top - config.PLATFORM_H, self.right, self.top

    def handle_collision(self, group, other):
        pass


class Ground:
    def __init__(self, left, right, phase):
        self.left = left
        self.right = right
        self.top = config.GROUND_TOP
        self.image = get_image(config.PHASES[phase]['ground'])

    def update(self, dt):
        pass

    def draw(self, camera):
        draw_strip(self.image, self.left, self.right, 0, camera)

    def get_bb(self):
        return self.left, 0, self.right, self.top

    def handle_collision(self, group, other):
        pass
