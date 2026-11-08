import math

import config
import game_world
from sprite import Effect, Strip

FRAME_W = 16
FPS = 12
PARRY_FX_SCALE = 1


def direction_to(x0, y0, x1, y1):
    length = math.hypot(x1 - x0, y1 - y0)
    return (x1 - x0) / length, (y1 - y0) / length


class Bullet:
    def __init__(self, x, y, target_x, target_y, owner, image='assets/monster/bullet.png', speed=config.BULLET_SPEED):
        self.x = x
        self.y = y
        self.owner = owner
        self.player = owner.player
        dx, dy = direction_to(x, y, target_x, target_y)
        self.vx = dx * speed
        self.vy = dy * speed
        self.reflected = False
        self.time = 0
        self.strip = Strip(image, FRAME_W)

    def update(self, dt):
        # 불릿 타임에는 탄막이 멈춘다 (CT-3).
        if self.player.bullet_target:
            return
        self.time += dt
        # 쏜 적이 순간이동해도 빗나가지 않게 따라간다. 먼저 쓰러졌으면 그대로 날아가 사라진다.
        if self.reflected and not self.owner.dead:
            self.aim_at_owner()
        self.x += self.vx * dt
        self.y += self.vy * dt
        if abs(self.x - self.player.x) > config.SCREEN_W or not config.GROUND_TOP < self.y < config.SCREEN_H:
            game_world.remove_object(self)

    def draw(self, camera):
        self.strip.draw(int(self.time * FPS) % self.strip.count, self.x - camera.x, self.y - camera.y)

    def get_bb(self):
        half = config.BULLET_SIZE / 2
        return self.x - half, self.y - half, self.x + half, self.y + half

    def reflect(self):
        self.reflected = True
        self.strip = Strip('assets/monster/bullet_reflected.png', FRAME_W)
        game_world.remove_collision('player:bullet', self)
        game_world.remove_collision('sword:bullet', self)
        game_world.add_collision_pair('reflected:mage', self, None)
        # 쏜 뒤에 플레이어가 전진했으므로 그대로 뒤집으면 빗나간다.
        self.aim_at_owner()
        self.player.on_parry(self.x, self.y)
        game_world.add_object(Effect('parry', self.x, self.y, scale=PARRY_FX_SCALE), game_world.LAYER_EFFECT)

    def aim_at_owner(self):
        target_y = self.owner.muzzle_y()
        if (self.x, self.y) != (self.owner.x, target_y):
            dx, dy = direction_to(self.x, self.y, self.owner.x, target_y)
            self.vx = dx * config.REFLECTED_SPEED
            self.vy = dy * config.REFLECTED_SPEED

    def handle_collision(self, group, other):
        if group == 'sword:bullet':
            self.reflect()
        elif group == 'reflected:mage':
            game_world.remove_object(self)
