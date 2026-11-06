import random

import config
import game_world
from sprite import OneShot, Strip, get_image
from ui import draw_text

LOW_IMAGES = ('assets/map/low_crate.png', 'assets/map/low_rock.png')
HIGH_IMAGE = 'assets/map/high_pillar.png'
GATE_FRAME_W = 64
GATE_FPS = 14
PLATFORM_IMAGE = 'assets/map/platform.png'
PLATFORM_CAP_IMAGE = 'assets/map/platform_cap.png'
PLATFORM_CAP_W = 32
WALL_TOP_IMAGE = 'assets/map/wall_top.png'
WALL_BOTTOM_IMAGE = 'assets/map/wall_bottom.png'
WALL_BREAK_IMAGE = 'assets/map/wall_break.png'
WALL_BREAK_FRAME_W = 60
WALL_BREAK_FPS = 14
# 잘린 윗부분이 날아가는 궤적
FLIGHT_SPEED_X = 500
FLIGHT_SPEED_Y = 700
FLIGHT_GRAVITY = 1200
FLIGHT_SPIN = -5
WARNING_SIZE = 24
WARNING_COLOR = (255, 90, 90)
READY_COLOR = (255, 214, 90)


def draw_strip(image, left, right, bottom, camera):
    """가로로 이어지는 이미지를 [left, right] 구간에 깔되 화면에 보이는 부분만 그린다."""
    x = int(max(left, camera.x))
    end = int(min(right, camera.x + config.SCREEN_W))
    while x < end:
        src = x % image.w
        w = min(image.w - src, end - x)
        image.clip_draw_to_origin(src, 0, w, image.h, x - camera.x, bottom - camera.y, w, image.h)
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
        self.image.draw_to_origin(self.left - camera.x, self.bottom - camera.y, self.right - self.left, self.top - self.bottom)

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
        self.sprite.draw(frame, self.x + config.GATE_W / 2 - camera.x, center_y - camera.y)

    def get_bb(self):
        # 2단 점프로 넘어가지 못하도록 화면 위까지 막는다.
        return self.x, config.GROUND_TOP, self.x + config.GATE_W, config.SCREEN_H

    def handle_collision(self, group, other):
        pass


class Wall:
    def __init__(self, x, player):
        self.x = x
        self.player = player
        self.state = 'intact'
        self.bullet_time_started = False
        self.flight_time = 0
        self.top_image = get_image(WALL_TOP_IMAGE)
        self.bottom_image = get_image(WALL_BOTTOM_IMAGE)

    def update(self, dt):
        if self.state == 'cut':
            self.flight_time += dt
            return
        gap = self.x - (self.player.x + config.PLAYER_W / 2)
        ready = self.player.gauge >= config.GAUGE_MAX
        if ready and not self.bullet_time_started and gap <= config.SCROLL_SPEED * config.WALL_ENTRY_TIME:
            self.bullet_time_started = True
            self.player.enter_bullet_time(self)

    def draw(self, camera):
        scale = config.SPRITE_SCALE
        center_x = self.x + config.WALL_W / 2 - camera.x
        bottom_h = self.bottom_image.h * scale
        top_h = self.top_image.h * scale
        self.bottom_image.draw(center_x, config.GROUND_TOP + bottom_h / 2 - camera.y, config.WALL_W, bottom_h)
        top_y = config.SCREEN_H - top_h / 2 - camera.y
        t = self.flight_time
        if self.state == 'cut':
            x = center_x + FLIGHT_SPEED_X * t
            y = top_y + FLIGHT_SPEED_Y * t - FLIGHT_GRAVITY * t * t / 2
            self.top_image.composite_draw(FLIGHT_SPIN * t, '', x, y, config.WALL_W, top_h)
        else:
            self.top_image.draw(center_x, top_y, config.WALL_W, top_h)
            self.draw_warning()

    def draw_warning(self):
        gap = self.x - self.player.x
        if self.player.bullet_wall or not 0 < gap <= config.SCROLL_SPEED * config.WALL_WARNING_TIME:
            return
        ready = self.player.gauge >= config.GAUGE_MAX
        text = '거대 장벽! 발도술 준비 완료' if ready else '거대 장벽! 게이지 부족'
        draw_text(WARNING_SIZE, config.SCREEN_W - 20, config.SCREEN_H * 0.62, text, READY_COLOR if ready else WARNING_COLOR, align=1)

    def get_bb(self):
        return self.x, config.GROUND_TOP, self.x + config.WALL_W, config.SCREEN_H

    def handle_collision(self, group, other):
        self.shatter()

    def cut(self):
        self.state = 'cut'
        game_world.collision_pairs['player:wall'][1].remove(self)

    def shatter(self):
        game_world.remove_object(self)
        strip = Strip(WALL_BREAK_IMAGE, WALL_BREAK_FRAME_W)
        center = (self.x + config.WALL_W / 2, config.GROUND_TOP + strip.image.h * config.SPRITE_SCALE / 2)
        game_world.add_object(OneShot(strip, WALL_BREAK_FPS, *center), game_world.LAYER_EFFECT)


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
        center_y = bottom + image.h / 2 - camera.y
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
