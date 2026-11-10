import math
import random

import config
import game_world
import record
import sound
from sprite import Effect, get_image

SHARD_W = 28
SHARD_H = 12
LANCE_W = 84
LANCE_H = 28
BOLT_SEGMENTS = 5
BOLT_WIGGLE = 14
BOLT_WIDTH = 3


def cast_ultimate(skill, player, boss):
    obj = {'fire3': MeteorCast, 'ice3': IceLance, 'bolt3': LightningCall}[skill](player, boss)
    game_world.add_object(obj, game_world.LAYER_EFFECT)


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
        # 플레이어가 보는 쪽으로 날아간다.
        shard = IceShard(x, y, math.radians(angle if player.facing > 0 else 180 - angle))
        game_world.add_object(shard, game_world.LAYER_EFFECT)
        game_world.add_collision_pair('shard:monster', shard, None)


def chain_lightning(player, monster):
    x, y = monster.dash_x(), monster.dash_y() + config.PLAYER_H / 2

    def distance(other):
        return math.hypot(other.dash_x() - x, other.dash_y() + config.PLAYER_H / 2 - y)

    target = min(nearby_monsters(player), key=distance, default=None)
    if target and distance(target) <= config.CHAIN_RANGE:
        game_world.add_object(ChainBolt(x, y, target), game_world.LAYER_EFFECT)


class MeteorCast:
    def __init__(self, player, boss):
        self.player = player
        self.boss = boss
        self.timer = config.METEOR_CAST_TIME
        self.dropped = False
        player.cast_timer = config.METEOR_CAST_TIME
        sound.play('cut_charge')
        game_world.add_object(Effect('charge-up', 0, 0, player), game_world.LAYER_EFFECT)

    def update(self, dt):
        self.timer -= dt
        if not self.dropped and self.timer <= config.METEOR_FX_IMPACT:
            self.dropped = True
            game_world.add_object(Effect('meteor', self.boss.x, self.boss.y), game_world.LAYER_EFFECT)
        if self.timer <= 0:
            game_world.remove_object(self)
            if self.player.boss is self.boss:
                sound.play('cut_boom')
                self.player.camera.shake(config.BOSS_DEATH_SHAKE_TIME, config.BOSS_DEATH_SHAKE_AMP)
                self.boss.lose_hp(self.boss.MAX_HP * config.METEOR_DAMAGE_RATIO)

    def draw(self, camera):
        pass


class IceLance:
    def __init__(self, player, boss):
        self.player = player
        self.boss = boss
        self.x = player.x
        self.y = player.y + config.PLAYER_H / 2
        self.angle = math.atan2(boss.y + boss.H / 2 - self.y, boss.x - self.x)
        self.life = config.LANCE_LIFE
        self.image = get_image('assets/monster/ice_shard.png')
        sound.play('fire')

    def update(self, dt):
        self.x += math.cos(self.angle) * config.LANCE_SPEED * dt
        self.y += math.sin(self.angle) * config.LANCE_SPEED * dt
        self.life -= dt
        left, bottom, right, top = self.boss.get_bb()
        hit = left <= self.x <= right and bottom <= self.y <= top and not self.boss.hidden
        if hit and self.player.boss is self.boss:
            self.boss.freeze()
        if hit or self.life <= 0:
            game_world.remove_object(self)

    def draw(self, camera):
        self.image.rotate_draw(self.angle, self.x - camera.x, self.y - camera.y, LANCE_W, LANCE_H)


class LightningCall:
    def __init__(self, player, boss):
        self.player = player
        self.boss = boss
        self.time = 0
        self.sent = 0
        self.landed = 0

    def update(self, dt):
        self.time += dt
        fx_delay = config.LIGHTNING_FX_IMPACT / config.LIGHTNING_FX_SPEED
        if self.sent < config.LIGHTNING_COUNT and self.time >= self.sent * config.LIGHTNING_INTERVAL:
            self.sent += 1
            effect = Effect('lightning-strike', self.boss.x, self.boss.y, speed=config.LIGHTNING_FX_SPEED)
            game_world.add_object(effect, game_world.LAYER_EFFECT)
        if self.time >= self.landed * config.LIGHTNING_INTERVAL + fx_delay:
            self.landed += 1
            if self.player.boss is self.boss:
                sound.play('zap')
                self.boss.lose_hp(record.stat('attack') * config.LIGHTNING_DAMAGE_RATIO)
            if self.landed == config.LIGHTNING_COUNT:
                game_world.remove_object(self)

    def draw(self, camera):
        pass


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
