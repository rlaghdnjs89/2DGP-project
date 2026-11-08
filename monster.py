import math

from pico2d import draw_rectangle

import config
import game_world
import record
import sound
from bullet import Bullet
from sprite import Effect, OneShot, Strip, load_fx_sheet

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

BOSS_FRAME_W = 172
# 172칸 스프라이트의 발바닥은 아래에서 4칸 위에 있다. 발 위치에서 그림 중심까지의 높이다.
BOSS_CENTER_Y = 164
BOSS_FPS = {'idle': 5, 'walk': 9, 'windup': 6, 'attack': 6, 'recover': 5}
BOSS_DEATH_FPS = 8
BOSS_ATTACK_FX = 'heavy-cleave'
BOSS_STATE_SPRITE = {'wait': 'idle', 'intro': 'idle', 'walk': 'walk', 'windup': 'windup', 'strike': 'attack', 'recover': 'recover'}


class Monster:
    def __init__(self, x, y, player):
        self.x = x
        self.y = y
        self.player = player

    def handle_collision(self, group, other):
        if group == 'sword:monster':
            other.player.on_kill(self)
            self.die()

    def gold(self, by_dash, bonus):
        base = self.GOLD + bonus + (self.DASH_BONUS if by_dash else 0)
        return base * config.STAGES[self.player.stage]['gold_rate']

    def dash_x(self):
        return self.x

    def on_dash_hit(self):
        self.player.on_kill(self, by_dash=True)
        self.die()

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
        if self.player.bullet_wall:
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
        if self.player.bullet_wall:
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
        if self.player.bullet_wall or not 0 < self.x - self.player.x <= config.MAGE_SIGHT:
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
            self.player.on_kill(self, bonus=config.MAGE_REFLECT_BONUS)
            self.die()
        else:
            super().handle_collision(group, other)


class BossStrike:
    """보스가 내려찍은 순간의 판정. 보스의 몸통과 따로 두어 점프로 넘을 수 있게 한다."""

    def __init__(self, boss):
        self.boss = boss
        self.timer = config.BOSS_STRIKE_TIME

    def update(self, dt):
        self.timer -= dt
        if self.timer <= 0:
            game_world.remove_object(self)

    def draw(self, camera):
        pass

    def get_bb(self):
        x = self.boss.x
        return x - config.BOSS_STRIKE_REACH, self.boss.y, x - config.BOSS_W / 2, self.boss.y + config.BOSS_STRIKE_H

    def handle_collision(self, group, other):
        pass


class Boss(Monster):
    NAME = '봉인의 수문장'
    AIRBORNE = False

    def __init__(self, x, y, player, wall):
        super().__init__(x, y, player)
        self.wall = wall
        self.hp = config.BOSS_HP
        self.state = 'wait'
        self.timer = 0
        self.time = 0
        self.flash = 0
        self.last_sword = None
        self.act = load_fx_sheet(BOSS_ATTACK_FX)[1]['meta']['pixelfx']['act']
        self.sprites = {name: Strip(f'assets/monster/boss_{name}.png', BOSS_FRAME_W) for name in BOSS_FPS}
        self.flash_sprites = {name: Strip(f'assets/monster/boss_{name}_flash.png', BOSS_FRAME_W) for name in BOSS_FPS}

    def enter(self, state, timer=0):
        self.state = state
        self.timer = timer
        self.time = 0

    def update(self, dt):
        self.time += dt
        self.flash = max(0, self.flash - dt)
        gap = self.x - self.player.x
        if self.state == 'wait':
            if gap <= config.BOSS_ENGAGE_GAP:
                self.player.enter_boss_fight(self)
                self.enter('intro', config.BOSS_INTRO_TIME)
        elif self.state == 'walk':
            if gap <= config.BOSS_ATTACK_RANGE:
                self.enter('windup', self.act['windup'])
            else:
                self.x -= config.BOSS_WALK_SPEED * dt
        else:
            self.timer -= dt
            if self.timer <= 0:
                self.next_state()

    def next_state(self):
        if self.state == 'windup':
            effect = Effect(BOSS_ATTACK_FX, self.x, self.y, scale=config.BOSS_FX_SCALE, flip=True)
            game_world.add_object(effect, game_world.LAYER_EFFECT)
            self.enter('strike', self.act['hits'][0]['t'])
        elif self.state == 'strike':
            self.slam()
            self.enter('recover', config.BOSS_RECOVER_TIME)
        else:
            self.enter('walk')

    def slam(self):
        sound.play('boss_slam')
        hit = self.act['hits'][0]
        self.player.freeze(hit['freeze'] * config.BOSS_HIT_STOP_RATIO)
        self.player.camera.shake(hit['shake'], hit['amp'] * config.SPRITE_SCALE)
        strike = BossStrike(self)
        game_world.add_object(strike, game_world.LAYER_EFFECT)
        game_world.add_collision_pair('player:strike', None, strike)

    def take_hit(self, damage, by_dash=False):
        self.hp -= damage
        self.flash = config.BOSS_FLASH_TIME
        sound.play('boss_hit')
        if self.hp > 0:
            self.player.play_hit_feedback(self, by_dash)
        else:
            self.defeat(by_dash)

    def gold(self, by_dash, bonus):
        stage = self.player.stage
        return config.BOSS_REPEAT_GOLD[stage] if stage in record.data['bosses'] else config.BOSS_FIRST_GOLD[stage]

    def defeat(self, by_dash):
        self.player.on_kill(self, by_dash)
        if self.player.stage not in record.data['bosses']:
            record.data['bosses'].append(self.player.stage)
        self.die()
        self.player.end_boss_fight()
        if self.wall:
            self.wall.unseal()
        else:
            self.player.cleared = True
        self.player.freeze(config.BOSS_DEATH_HIT_STOP)
        self.player.camera.shake(config.BOSS_DEATH_SHAKE_TIME, config.BOSS_DEATH_SHAKE_AMP)
        center_y = self.y + config.BOSS_H / 2
        game_world.add_object(Effect('plasma-explosion', self.x, center_y, scale=config.BOSS_DEATH_FX_SCALE), game_world.LAYER_EFFECT)

    def handle_collision(self, group, other):
        # 칼 판정이 여러 프레임 살아 있어도 한 번 휘두르면 한 번만 맞는다.
        if group == 'sword:monster' and other is not self.last_sword:
            self.last_sword = other
            self.take_hit(1)

    def on_dash_hit(self):
        self.take_hit(config.BOSS_DASH_DAMAGE, by_dash=True)

    def draw(self, camera):
        if self.state in ('windup', 'strike'):
            bottom = config.GROUND_TOP - 8 - camera.y
            draw_rectangle(self.x - config.BOSS_STRIKE_REACH - camera.x, bottom, self.x - config.BOSS_W / 2 - camera.x, bottom + 8,
                           *config.BOSS_STRIKE_WARNING_COLOR, 255, True)
        name = BOSS_STATE_SPRITE[self.state]
        sprite = (self.flash_sprites if self.flash > 0 else self.sprites)[name]
        frame = int(self.time * BOSS_FPS[name]) % sprite.count
        sprite.draw(frame, self.x - camera.x, self.y + BOSS_CENTER_Y - camera.y)

    def make_death(self):
        strip = Strip('assets/monster/boss_death.png', BOSS_FRAME_W)
        return OneShot(strip, BOSS_DEATH_FPS, self.x, self.y + BOSS_CENTER_Y)

    def get_bb(self):
        half_w = config.BOSS_W / 2
        return self.x - half_w, self.y, self.x + half_w, self.y + config.BOSS_H

    def dash_x(self):
        return self.get_bb()[0] - config.PLAYER_W / 2 - config.BOSS_CONTACT_GAP

    def dash_y(self):
        return self.y
