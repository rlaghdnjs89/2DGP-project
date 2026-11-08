import math

import config
import game_world
import skills
import sound
from bullet import Bullet
from sprite import OneShot, Strip

GRUNT_FRAME_W = 64
GRUNT_FPS = {'run': 14, 'windup': 8, 'attack': 14, 'recover': 6}
DEATH_FPS = 16
GRUNT_NEXT = {
    'windup': ('attack', config.GRUNT_ATTACK_TIME),
    'attack': ('recover', config.GRUNT_RECOVER_TIME),
    'recover': ('run', 0),
}

GOBLIN_FRAME_W = 64
GOBLIN_FPS = {'idle': 4, 'windup': 10, 'charge': 16}

MAGE_FRAME_W = 64
MAGE_FPS = {'idle': 6, 'cast': 8}
FAMILIAR_FRAME_W = 48
FAMILIAR_FPS = 12


class Monster:
    IS_BOSS = False

    def __init__(self, x, y, player):
        self.x = x
        self.y = y
        self.player = player
        self.dead = False

    def handle_collision(self, group, other):
        if group in ('sword:monster', 'shard:monster'):
            self.kill()

    def kill(self, by_dash=False, bonus=0):
        # 한 프레임에 칼과 스킬이 함께 닿아도 한 번만 처치한다.
        if self.dead:
            return
        self.dead = True
        self.die()
        self.player.on_kill(self, by_dash, bonus)
        skills.on_monster_killed(self.player, self)

    def gold(self, by_dash, bonus):
        base = self.GOLD + bonus + (self.DASH_BONUS if by_dash else 0)
        return base * config.STAGES[self.player.stage]['gold_rate']

    def dash_x(self):
        return self.x

    def on_dash_hit(self):
        self.kill(by_dash=True)

    def on_dive_hit(self):
        self.kill()

    def die(self):
        game_world.remove_object(self)
        game_world.add_object(self.make_death(), game_world.LAYER_EFFECT)


class Grunt(Monster):
    GOLD = config.GRUNT_GOLD
    DASH_BONUS = 0
    AIRBORNE = False

    def __init__(self, x, y, player):
        super().__init__(x, y, player)
        self.state = 'run'
        self.timer = 0
        self.time = 0
        self.sprites = {name: Strip(f'assets/monster/grunt_{name}.png', GRUNT_FRAME_W) for name in GRUNT_FPS}

    def update(self, dt):
        self.time += dt
        gap = self.x - self.player.x
        # 불릿 타임에는 달려오기만 하고 공격 동작은 시작하지도 진행하지도 않는다 (CT-3).
        if self.player.bullet_target:
            if self.state == 'run' and 0 <= gap <= config.GRUNT_SIGHT:
                self.x -= config.GRUNT_SPEED * dt
        elif self.state == 'run':
            if 0 <= gap <= config.GRUNT_ATTACK_RANGE:
                self.state = 'windup'
                self.timer = config.GRUNT_WINDUP_TIME
                self.time = 0
            elif 0 <= gap <= config.GRUNT_SIGHT:
                self.x -= config.GRUNT_SPEED * dt
        else:
            self.timer -= dt
            if self.timer <= 0:
                self.state, self.timer = GRUNT_NEXT[self.state]
                self.time = 0

    def draw(self, camera):
        sprite = self.sprites[self.state]
        frame = int(self.time * GRUNT_FPS[self.state]) % sprite.count
        sprite.draw(frame, self.x - camera.x, self.y + config.SPRITE_CENTER_Y - camera.y)

    def make_death(self):
        strip = Strip('assets/monster/grunt_death.png', GRUNT_FRAME_W)
        return OneShot(strip, DEATH_FPS, self.x, self.y + config.SPRITE_CENTER_Y)

    def get_bb(self):
        half_w = config.GRUNT_W / 2
        reach = config.GRUNT_ATTACK_REACH if self.state == 'attack' else 0
        return self.x - half_w - reach, self.y, self.x + half_w, self.y + config.GRUNT_H

    def dash_y(self):
        return self.y


class Goblin(Monster):
    GOLD = config.GOBLIN_GOLD
    DASH_BONUS = 0
    AIRBORNE = False

    def __init__(self, x, y, player):
        super().__init__(x, y, player)
        self.state = 'idle'
        self.timer = 0
        self.time = 0
        self.sprites = {name: Strip(f'assets/monster/goblin_{name}.png', GOBLIN_FRAME_W) for name in GOBLIN_FPS}

    def update(self, dt):
        self.time += dt
        # 불릿 타임에는 달려들지 않는다 (CT-3).
        if self.player.bullet_target:
            return
        if self.state == 'idle':
            if 0 <= self.x - self.player.x <= config.GOBLIN_SIGHT:
                self.state = 'windup'
                self.timer = config.GOBLIN_WINDUP_TIME
                self.time = 0
        elif self.state == 'windup':
            self.timer -= dt
            if self.timer <= 0:
                self.state = 'charge'
                self.time = 0
        else:
            # 피하든 부딪히든 멈추지 않고 화면 왼쪽 밖까지 달려 나간다.
            self.x -= config.GOBLIN_CHARGE_SPEED * dt

    def draw(self, camera):
        sprite = self.sprites[self.state]
        frame = int(self.time * GOBLIN_FPS[self.state]) % sprite.count
        sprite.draw(frame, self.x - camera.x, self.y + config.SPRITE_CENTER_Y - camera.y)

    def make_death(self):
        strip = Strip('assets/monster/goblin_death.png', GOBLIN_FRAME_W)
        return OneShot(strip, DEATH_FPS, self.x, self.y + config.SPRITE_CENTER_Y)

    def get_bb(self):
        half_w = config.GOBLIN_W / 2
        return self.x - half_w, self.y, self.x + half_w, self.y + config.GOBLIN_H

    def dash_y(self):
        return self.y


class Familiar(Monster):
    GOLD = config.FAMILIAR_GOLD
    DASH_BONUS = config.FAMILIAR_DASH_BONUS
    AIRBORNE = True

    def __init__(self, x, y, player):
        super().__init__(x, y, player)
        self.base_y = y
        self.time = 0
        self.sprite = Strip('assets/monster/familiar_float.png', FAMILIAR_FRAME_W)

    def update(self, dt):
        self.time += dt
        self.y = self.base_y + config.FAMILIAR_FLOAT * math.sin(self.time * config.FAMILIAR_FLOAT_SPEED)

    def draw(self, camera):
        frame = int(self.time * FAMILIAR_FPS) % self.sprite.count
        self.sprite.draw(frame, self.x - camera.x, self.y - camera.y)

    def make_death(self):
        strip = Strip('assets/monster/familiar_death.png', FAMILIAR_FRAME_W)
        return OneShot(strip, DEATH_FPS, self.x, self.y)

    def get_bb(self):
        half = config.FAMILIAR_SIZE / 2
        return self.x - half, self.y - half, self.x + half, self.y + half

    def dash_y(self):
        return self.y - config.PLAYER_H / 2


class Mage(Monster):
    GOLD = config.MAGE_GOLD
    DASH_BONUS = 0
    AIRBORNE = False

    def __init__(self, x, y, player):
        super().__init__(x, y, player)
        self.state = 'idle'
        self.time = 0
        self.timer = 0
        self.sprites = {name: Strip(f'assets/monster/mage_{name}.png', MAGE_FRAME_W) for name in MAGE_FPS}
        game_world.add_collision_pair('reflected:mage', None, self)

    def muzzle_y(self):
        return self.y + config.MAGE_MUZZLE_Y

    def fire(self):
        sound.play('fire')
        bullet = Bullet(self.x - config.MAGE_W / 2, self.muzzle_y(), self.player.x, self.player.y + config.MAGE_MUZZLE_Y, self)
        game_world.add_object(bullet, game_world.LAYER_EFFECT)
        game_world.add_collision_pair('player:bullet', None, bullet)
        game_world.add_collision_pair('sword:bullet', None, bullet)

    def update(self, dt):
        self.time += dt
        # 불릿 타임에는 공격이 멈춘다 (CT-3).
        if self.player.bullet_target or not 0 < self.x - self.player.x <= config.MAGE_SIGHT:
            return
        self.timer -= dt
        if self.timer > 0:
            return
        if self.state == 'idle':
            self.state = 'cast'
            self.timer = config.MAGE_CAST_TIME
        else:
            self.fire()
            self.state = 'idle'
            self.timer = config.MAGE_FIRE_INTERVAL - config.MAGE_CAST_TIME
        self.time = 0

    def draw(self, camera):
        sprite = self.sprites[self.state]
        frame = int(self.time * MAGE_FPS[self.state]) % sprite.count
        sprite.draw(frame, self.x - camera.x, self.y + config.SPRITE_CENTER_Y - camera.y)

    def make_death(self):
        strip = Strip('assets/monster/mage_death.png', MAGE_FRAME_W)
        return OneShot(strip, DEATH_FPS, self.x, self.y + config.SPRITE_CENTER_Y)

    def get_bb(self):
        half_w = config.MAGE_W / 2
        return self.x - half_w, self.y, self.x + half_w, self.y + config.MAGE_H

    def dash_y(self):
        return self.y

    def handle_collision(self, group, other):
        if group == 'reflected:mage':
            self.kill(bonus=config.MAGE_REFLECT_BONUS)
        else:
            super().handle_collision(group, other)
