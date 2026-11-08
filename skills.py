import math
import random

import config
import game_world
import record
import sound
from sprite import Effect, get_image

SHARD_W = 28
SHARD_H = 12
BOLT_SEGMENTS = 5
BOLT_WIGGLE = 14
BOLT_WIDTH = 3


def on_monster_killed(player, monster):
    """각인 2단계. 일반 적을 처치하면 터지거나 깨지거나 번개가 튄다."""
    if record.has_skill('fire2'):
        explode_corpse(player, monster)
    elif record.has_skill('ice2'):
        shatter(player, monster)
    elif record.has_skill('bolt2'):
        chain_lightning(player, monster)


def nearby_monsters(player):
    return [monster for monster in game_world.collision_pairs['player:monster'][1] if not monster.IS_BOSS]


def explode_corpse(player, monster):
    sound.play('rock')
    x, y = monster.dash_x(), monster.dash_y()
    effect = Effect('small-explosion', x, y, speed=config.CORPSE_FX_SPEED, scale=config.CORPSE_FX_SCALE)
    game_world.add_object(effect, game_world.LAYER_EFFECT)
    for other in nearby_monsters(player):
        if math.hypot(other.dash_x() - x, other.dash_y() - y) <= config.CORPSE_RADIUS:
            other.kill()


def shatter(player, monster):
    sound.play('shield_block')
    x, y = monster.dash_x(), monster.dash_y() + config.PLAYER_H / 2
    effect = Effect('ice-shatter', x, monster.dash_y(), speed=config.SHATTER_FX_SPEED, scale=config.SHATTER_FX_SCALE)
    game_world.add_object(effect, game_world.LAYER_EFFECT)
    for angle in config.SHARD_ANGLES:
        shard = IceShard(x, y, math.radians(angle))
        game_world.add_object(shard, game_world.LAYER_EFFECT)
        game_world.add_collision_pair('shard:monster', shard, None)


def chain_lightning(player, monster):
    x, y = monster.dash_x(), monster.dash_y() + config.PLAYER_H / 2

    def distance(other):
        return math.hypot(other.dash_x() - x, other.dash_y() + config.PLAYER_H / 2 - y)

    target = min(nearby_monsters(player), key=distance, default=None)
    if target and distance(target) <= config.CHAIN_RANGE:
        game_world.add_object(ChainBolt(x, y, target), game_world.LAYER_EFFECT)


class IceShard:
    def __init__(self, x, y, angle):
        self.x = x
        self.y = y
        self.angle = angle
        self.life = config.SHARD_LIFE
        self.image = get_image('assets/monster/ice_shard.png')

    def update(self, dt):
        self.x += math.cos(self.angle) * config.SHARD_SPEED * dt
        self.y += math.sin(self.angle) * config.SHARD_SPEED * dt
        self.life -= dt
        if self.life <= 0:
            game_world.remove_object(self)

    def draw(self, camera):
        self.image.rotate_draw(self.angle, self.x - camera.x, self.y - camera.y, SHARD_W, SHARD_H)

    def get_bb(self):
        half = SHARD_W / 2
        return self.x - half, self.y - half, self.x + half, self.y + half

    def handle_collision(self, group, other):
        game_world.remove_object(self)


class ChainBolt:
    """앞 적에서 다음 적으로 튀는 번개. 잠깐 보여 준 뒤 대상을 처치한다."""

    def __init__(self, x, y, target):
        self.x = x
        self.y = y
        self.target = target
        self.timer = config.CHAIN_DELAY
        self.image = get_image('assets/ui/white.png')
        sound.play('zap')

    def update(self, dt):
        self.timer -= dt
        if self.timer <= 0:
            game_world.remove_object(self)
            effect = Effect('zap-hit', self.target.dash_x(), self.target.dash_y() + config.PLAYER_H / 2)
            game_world.add_object(effect, game_world.LAYER_EFFECT)
            self.target.kill()

    def draw(self, camera):
        end_x, end_y = self.target.dash_x(), self.target.dash_y() + config.PLAYER_H / 2
        last_x, last_y = self.x, self.y
        for i in range(1, BOLT_SEGMENTS + 1):
            t = i / BOLT_SEGMENTS
            wiggle = 0 if i == BOLT_SEGMENTS else random.uniform(-BOLT_WIGGLE, BOLT_WIGGLE)
            x, y = self.x + (end_x - self.x) * t, self.y + (end_y - self.y) * t + wiggle
            length = math.hypot(x - last_x, y - last_y)
            self.image.rotate_draw(math.atan2(y - last_y, x - last_x), (x + last_x) / 2 - camera.x, (y + last_y) / 2 - camera.y, length, BOLT_WIDTH)
            last_x, last_y = x, y
