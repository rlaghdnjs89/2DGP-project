import math
import random

import config
import game_world
import sound
from sprite import Effect, OneShot, Strip, get_image
from ui import draw_text

GATE_FRAME_W = 64
GATE_FPS = 14
PLATFORM_CAP_W = 32
WALL_TOP_IMAGE = 'assets/map/wall_top.png'
WALL_BOTTOM_IMAGE = 'assets/map/wall_bottom.png'
WALL_BREAK_IMAGE = 'assets/map/wall_break.png'
WALL_SEAL_IMAGE = 'assets/map/wall_seal.png'
SEAL_PULSE_SPEED = 4
SEAL_BREAK_FX_SCALE = 2
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


def make_low_obstacle(left, phase):
    image = random.choice(config.PHASES[phase]['low'])
    return Obstacle(left, config.GROUND_TOP, config.LOW_OBSTACLE_W, config.LOW_OBSTACLE_H, image)


def make_high_obstacle(left, phase):
    bottom = config.GROUND_TOP + config.HIGH_OBSTACLE_CLEARANCE
    # 천장까지 막아 점프로는 넘을 수 없게 한다.
    return Obstacle(left, bottom, config.HIGH_OBSTACLE_W, config.SCREEN_H - bottom, config.PHASES[phase]['high'])


class PhaseGate:
    def __init__(self, x, phase):
        self.x = x
        self.phase = phase
        self.time = 0
        self.sprite = Strip(config.PHASES[phase]['gate'], GATE_FRAME_W)

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
        self.sealed = True
        self.time = 0
        self.bullet_time_started = False
        self.flight_time = 0
        self.top_image = get_image(WALL_TOP_IMAGE)
        self.bottom_image = get_image(WALL_BOTTOM_IMAGE)
        self.seal_image = get_image(WALL_SEAL_IMAGE)

    def update(self, dt):
        self.time += dt
        if self.state == 'cut':
            self.flight_time += dt
            return
        gap = self.x - (self.player.x + config.PLAYER_W / 2)
        if not self.sealed and not self.bullet_time_started and gap <= self.player.speed() * config.WALL_ENTRY_TIME:
            self.bullet_time_started = True
            self.player.enter_bullet_time(self)

    def unseal(self):
        self.sealed = False
        sound.play('seal_break')
        center_y = (config.GROUND_TOP + config.SCREEN_H) / 2
        effect = Effect('plasma-explosion', self.x + config.WALL_W / 2, center_y, scale=SEAL_BREAK_FX_SCALE)
        game_world.add_object(effect, game_world.LAYER_EFFECT)

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
            if self.sealed:
                self.draw_seal(center_x)
            self.draw_warning()

    def draw_seal(self, center_x):
        self.seal_image.opacify(0.75 + 0.25 * math.sin(self.time * SEAL_PULSE_SPEED))
        self.seal_image.draw(center_x, (config.GROUND_TOP + config.SCREEN_H) / 2, config.WALL_W, config.SCREEN_H - config.GROUND_TOP)
        # opacify는 텍스처 자체를 바꾸므로 다음 장벽에 남지 않게 되돌린다.
        self.seal_image.opacify(1)

    def draw_warning(self):
        gap = self.x - self.player.x
        if self.player.boss or self.player.bullet_wall or not 0 < gap <= self.player.speed() * config.WALL_WARNING_TIME:
            return
        if self.sealed:
            draw_text(WARNING_SIZE, config.SCREEN_W - 20, config.SCREEN_H * 0.62, '봉인된 장벽! 수문장을 베어라', WARNING_COLOR, align=1)
        else:
            draw_text(WARNING_SIZE, config.SCREEN_W - 20, config.SCREEN_H * 0.62, '봉인 해제! 발도술 준비', READY_COLOR, align=1)

    def get_bb(self):
        return self.x, config.GROUND_TOP, self.x + config.WALL_W, config.SCREEN_H

    def handle_collision(self, group, other):
        self.shatter()

    def cut(self):
        self.state = 'cut'
        game_world.remove_collision('player:wall', self)

    def shatter(self):
        sound.play('wall_break')
        game_world.remove_object(self)
        strip = Strip(WALL_BREAK_IMAGE, WALL_BREAK_FRAME_W)
        center = (self.x + config.WALL_W / 2, config.GROUND_TOP + strip.image.h * config.SPRITE_SCALE / 2)
        game_world.add_object(OneShot(strip, WALL_BREAK_FPS, *center), game_world.LAYER_EFFECT)


class Platform:
    def __init__(self, left, right, top, phase):
        self.left = left
        self.right = right
        self.top = top
        self.image = get_image(config.PHASES[phase]['platform'])
        self.cap = get_image(config.PHASES[phase]['platform_cap'])

    def update(self, dt):
        pass

    def draw(self, camera):
        h = self.image.h
        bottom = self.top - h
        draw_strip(self.image, self.left + PLATFORM_CAP_W, self.right - PLATFORM_CAP_W, bottom, camera)
        center_y = bottom + h / 2 - camera.y
        half_cap = PLATFORM_CAP_W / 2
        self.cap.draw(self.left + half_cap - camera.x, center_y, PLATFORM_CAP_W, h)
        self.cap.composite_draw(0, 'h', self.right - half_cap - camera.x, center_y, PLATFORM_CAP_W, h)

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
