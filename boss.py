import math
import random

from pico2d import draw_rectangle

import config
import game_world
import record
import sound
from bullet import Bullet
from monster import Familiar, Monster
from sprite import Effect, OneShot, Strip, get_image, load_fx_sheet


WAVE_FRAME_W = 48
WAVE_FPS = 14


class AttackBox:
    """보스의 몸통과 따로 두는 공격 판정. 점프나 후퇴로 피할 수 있게 한다."""

    def __init__(self, left, bottom, right, top):
        self.left = left
        self.bottom = bottom
        self.right = right
        self.top = top
        self.timer = config.BOSS_STRIKE_TIME

    def update(self, dt):
        self.timer -= dt
        if self.timer <= 0:
            game_world.remove_object(self)

    def draw(self, camera):
        pass

    def get_bb(self):
        return self.left, self.bottom, self.right, self.top

    def handle_collision(self, group, other):
        pass


class FloorWave:
    """바닥을 따라 왼쪽으로 달리는 충격파. 화면 왼쪽 밖으로 나가면 사라진다."""

    def __init__(self, x, y, speed, camera):
        self.x = x
        self.y = y
        self.speed = speed
        self.camera = camera
        self.time = 0
        self.strip = Strip('assets/monster/boss_wave.png', WAVE_FRAME_W)

    def update(self, dt):
        self.time += dt
        self.x -= self.speed * dt
        if self.x < self.camera.base_x - config.BOSS_WAVE_W:
            game_world.remove_object(self)

    def draw(self, camera):
        frame = int(self.time * WAVE_FPS) % self.strip.count
        self.strip.draw(frame, self.x - camera.x, self.y + self.strip.image.h - camera.y)

    def get_bb(self):
        half_w = config.BOSS_WAVE_W / 2
        return self.x - half_w, self.y, self.x + half_w, self.y + config.BOSS_WAVE_H

    def handle_collision(self, group, other):
        pass


class GroundHazard:
    """바닥에 범위를 표시했다가 정해진 시간 뒤 판정을 내는 공격."""

    def __init__(self, boss, x, w, h, warning_time, impact_sound):
        self.boss = boss
        self.left = x - w / 2
        self.right = x + w / 2
        self.h = h
        self.timer = warning_time
        self.impact_sound = impact_sound

    def update(self, dt):
        self.timer -= dt
        if self.timer <= 0:
            sound.play(self.impact_sound)
            self.boss.player.camera.shake(config.BOSS_BLOCK_SHAKE_TIME, config.BOSS_BLOCK_SHAKE_AMP)
            self.boss.add_attack(AttackBox(self.left, config.GROUND_TOP, self.right, config.GROUND_TOP + self.h))
            game_world.remove_object(self)

    def draw(self, camera):
        bottom = config.GROUND_TOP - 8 - camera.y
        draw_rectangle(self.left - camera.x, bottom, self.right - camera.x, bottom + 8, *config.BOSS_STRIKE_WARNING_COLOR, 255, True)


class StrikeWarning:
    """곧 판정이 나올 범위를 보여 준다."""

    def __init__(self, left, bottom, right, top, time):
        self.left = left
        self.bottom = bottom
        self.right = right
        self.top = top
        self.timer = time

    def update(self, dt):
        self.timer -= dt
        if self.timer <= 0:
            game_world.remove_object(self)

    def draw(self, camera):
        left, right = self.left - camera.x, self.right - camera.x
        bottom, top = self.bottom - camera.y, self.top - camera.y
        # draw_rectangle은 반투명으로 칠하지 못해 플레이어를 가리므로 반투명 이미지를 늘려 그린다.
        get_image('assets/ui/warning.png').draw_to_origin(left, bottom, right - left, top - bottom)
        draw_rectangle(left, bottom, right, top, *config.BOSS_STRIKE_WARNING_COLOR, 255, False)


class Boss(Monster):
    """스테이지 끝을 지키는 보스의 공통 동작. 상태별 행동은 think에서 정한다."""
    AIRBORNE = False
    IS_BOSS = True

    def __init__(self, x, y, player, wall):
        super().__init__(x, y, player)
        self.wall = wall
        self.start_x = x
        self.hp = self.MAX_HP
        self.state = 'wait'
        self.timer = 0
        self.time = 0
        self.flash = 0
        self.last_sword = None
        self.attacks = []
        self.burn_timer = 0
        self.slow_timer = 0
        self.frost_hits = 0
        self.status_fx = {}

    def enter(self, state, timer=0):
        self.state = state
        self.timer = timer
        self.time = 0

    def update(self, dt):
        self.time += dt
        self.flash = max(0, self.flash - dt)
        self.tick_status(dt)
        if self.hp <= 0:
            return
        if self.state != 'wait':
            self.think(dt * self.time_rate())
        elif self.x - self.player.x <= config.BOSS_ENGAGE_GAP:
            self.player.enter_boss_fight(self)
            self.enter('intro', config.BOSS_INTRO_TIME)

    def add_hazard(self, hazard):
        self.attacks.append(hazard)
        game_world.add_object(hazard, game_world.LAYER_WARNING)

    def add_attack(self, attack):
        self.attacks.append(attack)
        game_world.add_object(attack, game_world.LAYER_EFFECT)
        game_world.add_collision_pair('player:strike', None, attack)

    def gold(self, by_dash, bonus):
        stage = self.player.stage
        return config.BOSS_REPEAT_GOLD[stage] if stage in record.data['bosses'] else config.BOSS_FIRST_GOLD[stage]

    def tick_status(self, dt):
        if self.burn_timer > 0:
            self.burn_timer -= dt
            self.lose_hp(record.stat('attack') * config.BURN_DAMAGE_RATIO * dt)
            if self.burn_timer <= 0:
                self.hide_status('burning')
        if self.slow_timer > 0:
            self.slow_timer -= dt
            if self.slow_timer <= 0:
                self.hide_status('slowed')

    def show_status(self, name):
        if name not in self.status_fx:
            info = config.STATUS_FX[name]
            self.status_fx[name] = Effect(name, 0, info['y'], self, scale=info['scale'], loop=True)
            game_world.add_object(self.status_fx[name], game_world.LAYER_EFFECT)

    def hide_status(self, name):
        game_world.remove_object(self.status_fx.pop(name))

    def time_rate(self):
        return config.FROST_SLOW_RATE if self.slow_timer > 0 else 1

    def damage_rate(self):
        return 1

    def on_damaged(self):
        pass

    def take_hit(self, damage, by_dash=False):
        self.hp -= damage * self.damage_rate()
        self.flash = config.BOSS_FLASH_TIME
        sound.play('boss_hit')
        if self.hp > 0:
            self.player.play_hit_feedback(self, by_dash)
            self.on_damaged()
        else:
            self.defeat(by_dash)

    def lose_hp(self, amount):
        """화상과 감전처럼 방패와 갑옷을 무시하는 피해."""
        self.hp -= amount
        if self.hp > 0:
            self.on_damaged()
        else:
            self.defeat(False)

    def ignite(self):
        self.burn_timer = config.BURN_TIME
        self.show_status('burning')

    def apply_element(self):
        """베기가 들어갔을 때 각인의 효과를 준다."""
        if record.has_skill('fire1'):
            self.ignite()
        elif record.has_skill('ice1'):
            self.frost_hits += 1
            if self.frost_hits >= config.FROST_HITS:
                self.frost_hits = 0
                self.slow_timer = config.FROST_SLOW_TIME
                self.show_status('slowed')
        elif record.has_skill('bolt1') and random.random() < config.ZAP_CHANCE:
            sound.play('zap')
            effect = Effect('zap-hit', self.x, self.y + self.H / 2)
            game_world.add_object(effect, game_world.LAYER_EFFECT)
            self.lose_hp(record.stat('attack') * config.ZAP_DAMAGE_RATIO)

    def defeat(self, by_dash):
        self.player.on_kill(self, by_dash)
        for name in list(self.status_fx):
            self.hide_status(name)
        if self.player.stage not in record.data['bosses']:
            record.data['bosses'].append(self.player.stage)
        self.die()
        self.player.end_boss_fight()
        for attack in self.attacks:
            game_world.remove_object(attack)
        if self.wall:
            self.wall.unseal()
        else:
            self.player.cleared = True
        self.player.freeze(config.BOSS_DEATH_HIT_STOP)
        self.player.camera.shake(config.BOSS_DEATH_SHAKE_TIME, config.BOSS_DEATH_SHAKE_AMP)
        center_y = self.y + self.H / 2
        game_world.add_object(Effect('plasma-explosion', self.x, center_y, scale=config.BOSS_DEATH_FX_SCALE), game_world.LAYER_EFFECT)

    def handle_collision(self, group, other):
        # 칼 판정이 여러 프레임 살아 있어도 한 번 휘두르면 한 번만 맞는다.
        if group == 'sword:monster' and other is not self.last_sword:
            self.last_sword = other
            self.on_slash(other)

    def on_slash(self, sword):
        ratio = config.TRIPLE_DAMAGE_RATIO if sword.finisher else 1
        self.take_hit(record.stat('attack') * ratio)
        if self.hp > 0:
            self.apply_element()
            if sword.finisher:
                self.knock_back()

    def knock_back(self):
        # 시작 자리 뒤로는 밀리지 않는다.
        self.x = min(self.x + config.TRIPLE_KNOCKBACK, self.start_x)

    def on_dash_hit(self):
        self.take_hit(record.stat('attack') * config.DASH_DAMAGE_RATIO, by_dash=True)

    def on_dive_hit(self):
        self.take_hit(record.stat('attack') * config.DIVE_BOSS_DAMAGE_RATIO)

    def get_bb(self):
        half_w = self.W / 2
        return self.x - half_w, self.y, self.x + half_w, self.y + self.H

    def dash_x(self):
        return self.get_bb()[0] - config.PLAYER_W / 2 - config.BOSS_CONTACT_GAP

    def dash_y(self):
        return self.y


WARDEN_FRAME_W = 172
# 172칸 스프라이트의 발바닥은 아래에서 4칸 위에 있다. 발 위치에서 그림 중심까지의 높이다.
WARDEN_CENTER_Y = 164
WARDEN_FPS = {'idle': 5, 'walk': 9, 'windup': 6, 'attack': 6, 'recover': 5, 'guard': 4, 'groggy': 3}
WARDEN_DEATH_FPS = 8
WARDEN_ATTACK_FX = 'heavy-cleave'
WARDEN_STATE_SPRITE = {'wait': 'idle', 'intro': 'idle', 'walk': 'walk', 'windup': 'windup', 'strike': 'attack', 'recover': 'recover',
                       'guard': 'guard', 'groggy': 'groggy', 'wave_windup': 'windup', 'wave_gap': 'attack', 'wave_recover': 'recover'}
# 이 순서대로 공격을 돌린다. 내려찍기는 플레이어가 사거리에 들어올 때까지 걸어간다.
WARDEN_PATTERN = ('slam', 'wave', 'slam', 'guard')


class Warden(Boss):
    NAME = '봉인의 수문장'
    MAX_HP = config.BOSS_HP
    W = config.BOSS_W
    H = config.BOSS_H

    def __init__(self, x, y, player, wall):
        super().__init__(x, y, player, wall)
        self.pattern = 0
        self.raging = False
        self.cleave = load_fx_sheet(WARDEN_ATTACK_FX)[1]['meta']['pixelfx']['act']
        self.sprites = {name: Strip(f'assets/monster/boss_{name}.png', WARDEN_FRAME_W) for name in WARDEN_FPS}
        self.flash_sprites = {name: Strip(f'assets/monster/boss_{name}_flash.png', WARDEN_FRAME_W) for name in WARDEN_FPS}
        self.rage_sprites = {name: Strip(f'assets/monster/boss_{name}_rage.png', WARDEN_FRAME_W) for name in WARDEN_FPS}

    def think(self, dt):
        if self.state == 'walk':
            self.walk(dt)
        else:
            self.timer -= dt
            if self.timer <= 0:
                self.next_state()

    def walk(self, dt):
        attack = WARDEN_PATTERN[self.pattern]
        if attack == 'slam' and self.x - self.player.x > config.BOSS_ATTACK_RANGE:
            self.x -= config.BOSS_WALK_SPEED * dt
            return
        self.pattern = (self.pattern + 1) % len(WARDEN_PATTERN)
        if attack == 'slam':
            self.enter('windup', self.cleave['windup'])
        elif attack == 'wave':
            self.enter('wave_windup', config.BOSS_WAVE_WINDUP)
        else:
            self.enter('guard', config.BOSS_GUARD_TIME)

    def next_state(self):
        if self.state == 'windup':
            effect = Effect(WARDEN_ATTACK_FX, self.x, self.y, scale=config.BOSS_FX_SCALE, flip=True)
            game_world.add_object(effect, game_world.LAYER_EFFECT)
            self.enter('strike', self.cleave['hits'][0]['t'])
        elif self.state == 'strike':
            self.slam()
            if self.raging:
                self.drop_rocks()
            self.enter('recover', config.BOSS_RECOVER_TIME)
        elif self.state == 'wave_windup':
            self.send_wave()
            self.enter('wave_gap', config.BOSS_WAVE_INTERVAL)
        elif self.state == 'wave_gap':
            self.send_wave()
            self.enter('wave_recover', config.BOSS_WAVE_RECOVER)
        else:
            self.enter('walk')

    def drop_rocks(self):
        player_x = self.player.x
        for x in (player_x - config.ROCK_SPREAD, player_x, player_x + config.ROCK_SPREAD):
            self.add_hazard(GroundHazard(self, x, config.ROCK_W, config.ROCK_H, config.ROCK_WARNING_TIME, 'rock'))
            effect = Effect('boulder', x - config.ROCK_ARC_X * config.SPRITE_SCALE, self.y)
            game_world.add_object(effect, game_world.LAYER_EFFECT)

    def send_wave(self):
        sound.play('boss_wave')
        self.player.camera.shake(config.BOSS_BLOCK_SHAKE_TIME, config.BOSS_BLOCK_SHAKE_AMP)
        left = self.x - config.BOSS_W / 2
        effect = Effect('ground-slam', left, self.y, speed=config.BOSS_WAVE_FX_SPEED)
        game_world.add_object(effect, game_world.LAYER_EFFECT)
        self.add_attack(FloorWave(left, self.y, config.BOSS_WAVE_SPEED * self.time_rate(), self.player.camera))

    def slam(self):
        sound.play('boss_slam')
        hit = self.cleave['hits'][0]
        self.player.freeze(hit['freeze'] * config.BOSS_HIT_STOP_RATIO)
        self.player.camera.shake(hit['shake'], hit['amp'] * config.SPRITE_SCALE)
        self.add_attack(AttackBox(self.x - config.BOSS_STRIKE_REACH, self.y, self.x - config.BOSS_W / 2, self.y + config.BOSS_STRIKE_H))

    def time_rate(self):
        return super().time_rate() * (config.BOSS_RAGE_SPEED if self.raging else 1)

    def damage_rate(self):
        if self.state == 'groggy':
            return config.BOSS_GROGGY_DAMAGE_RATE
        return 1 if self.state == 'recover' else config.BOSS_ARMOR_DAMAGE_RATE

    def on_damaged(self):
        if not self.raging and self.hp <= self.MAX_HP * config.BOSS_RAGE_HP_RATIO:
            self.raging = True
            sound.play('boss_roar')
            self.player.camera.shake(config.BOSS_DEATH_SHAKE_TIME, config.BOSS_DEATH_SHAKE_AMP)

    def on_slash(self, sword):
        if self.state != 'guard':
            super().on_slash(sword)
            return
        # 방패는 베기를 튕겨낸다. 일섬만 깰 수 있다. 화상은 방패를 무시한다.
        if record.has_skill('fire1'):
            self.ignite()
        sound.play('shield_block')
        self.player.freeze(config.BOSS_BLOCK_HIT_STOP)
        self.player.camera.shake(config.BOSS_BLOCK_SHAKE_TIME, config.BOSS_BLOCK_SHAKE_AMP)
        effect = Effect('shield-block', self.x - config.BOSS_W / 2, self.y + config.BOSS_H / 2, scale=config.BOSS_BLOCK_FX_SCALE, flip=True)
        game_world.add_object(effect, game_world.LAYER_EFFECT)

    def on_dash_hit(self):
        if self.state == 'guard':
            sound.play('wall_break')
            self.enter('groggy', config.BOSS_GROGGY_TIME)
        super().on_dash_hit()

    def draw(self, camera):
        # 공격이 나가기 전에 맞을 범위를 바닥에 보여 준다.
        if self.state in ('windup', 'strike', 'wave_windup'):
            left = self.x - config.BOSS_STRIKE_REACH if self.state != 'wave_windup' else camera.x
            bottom = config.GROUND_TOP - 8 - camera.y
            draw_rectangle(left - camera.x, bottom, self.x - config.BOSS_W / 2 - camera.x, bottom + 8,
                           *config.BOSS_STRIKE_WARNING_COLOR, 255, True)
        name = WARDEN_STATE_SPRITE[self.state]
        body = self.rage_sprites if self.raging else self.sprites
        sprite = (self.flash_sprites if self.flash > 0 else body)[name]
        frame = int(self.time * WARDEN_FPS[name]) % sprite.count
        sprite.draw(frame, self.x - camera.x, self.y + WARDEN_CENTER_Y - camera.y)

    def make_death(self):
        strip = Strip('assets/monster/boss_death.png', WARDEN_FRAME_W)
        return OneShot(strip, WARDEN_DEATH_FPS, self.x, self.y + WARDEN_CENTER_Y)


WITCH_FRAME_W = 96
WITCH_CENTER_Y = 90
WITCH_FPS = {'float': 8, 'cast': 8}
WITCH_DEATH_FPS = 8
WITCH_CIRCLE_FRAME_W = 48
WITCH_CIRCLE_FPS = 12
WITCH_CAST_STATES = ('fan_windup', 'summon_windup', 'hole_windup')
WITCH_PATTERN = ('fan', 'teleport', 'summon', 'fan', 'teleport')
WITCH_RAGE_PATTERN = ('fan', 'teleport', 'hole', 'summon', 'fan', 'teleport')
# 가운데가 조준 방향이다. 검은 탄은 패링할 수 없다.
WITCH_FAN = ('black', 'purple', 'black', 'purple', 'black')
WITCH_COLLISION_GROUPS = ('player:monster', 'sword:monster', 'reflected:mage', 'shard:monster')


EXEC_FRAME_W = 172
EXEC_CENTER_Y = 164
EXEC_FPS = {'idle': 5, 'walk': 12, 'windup': 8, 'low': 8, 'high': 8, 'throw': 8, 'recover': 5, 'groggy': 3}
EXEC_DEATH_FPS = 8
EXEC_STATE_SPRITE = {'wait': 'idle', 'intro': 'idle', 'walk': 'walk', 'combo_windup': 'windup', 'recover': 'recover', 'groggy': 'groggy',
                     'throw_windup': 'windup', 'throw_after': 'throw'}
EXEC_COMBO = ('low', 'high', 'low')
EXEC_PATTERN = ('combo', 'throw')
EXEC_SWORD_FRAME_W = 64


class Executor(Boss):
    NAME = '심연의 집행자'
    MAX_HP = config.EXEC_HP
    W = config.EXEC_W
    H = config.EXEC_H

    def __init__(self, x, y, player, wall):
        super().__init__(x, y, player, wall)
        self.pattern = 0
        self.combo_index = 0
        self.sprites = {name: Strip(f'assets/monster/exec_{name}.png', EXEC_FRAME_W) for name in EXEC_FPS}
        self.flash_sprites = {name: Strip(f'assets/monster/exec_{name}_flash.png', EXEC_FRAME_W) for name in EXEC_FPS}
        game_world.add_collision_pair('reflected:mage', None, self)

    def muzzle_y(self):
        return self.y + config.EXEC_MUZZLE_Y

    def time_rate(self):
        return super().time_rate()

    def damage_rate(self):
        if self.state == 'groggy':
            return config.EXEC_GROGGY_DAMAGE_RATE
        return 1 if self.state == 'recover' else config.EXEC_ARMOR_DAMAGE_RATE

    def think(self, dt):
        if self.state == 'walk':
            self.walk(dt)
        else:
            self.timer -= dt
            if self.timer <= 0:
                self.next_state()

    def walk(self, dt):
        attack = EXEC_PATTERN[self.pattern]
        if attack == 'combo' and self.x - self.player.x > config.EXEC_ATTACK_RANGE:
            self.x -= config.EXEC_WALK_SPEED * dt
            return
        self.pattern = (self.pattern + 1) % len(EXEC_PATTERN)
        if attack == 'combo':
            self.combo_index = 0
            self.begin_strike()
        else:
            self.enter('throw_windup', config.EXEC_THROW_WINDUP)

    def strike_range(self, kind):
        if kind == 'low':
            return self.y, self.y + config.EXEC_LOW_H
        return self.y + config.EXEC_HIGH_BOTTOM, self.y + config.EXEC_HIGH_TOP

    def begin_strike(self):
        bottom, top = self.strike_range(EXEC_COMBO[self.combo_index])
        left = self.x - config.EXEC_STRIKE_REACH
        self.add_hazard(StrikeWarning(left, bottom, self.x - self.W / 2, top, config.EXEC_STRIKE_WINDUP))
        self.enter('combo_windup', config.EXEC_STRIKE_WINDUP)

    def strike(self):
        kind = EXEC_COMBO[self.combo_index]
        bottom, top = self.strike_range(kind)
        sound.play('slash')
        self.add_attack(AttackBox(self.x - config.EXEC_STRIKE_REACH, bottom, self.x - self.W / 2, top))
        effect = Effect('sword-slash-fire', self.x - self.W / 2, (bottom + top) / 2, speed=config.EXEC_STRIKE_FX_SPEED,
                        scale=config.EXEC_STRIKE_FX_SCALE, flip=True)
        game_world.add_object(effect, game_world.LAYER_EFFECT)
        self.enter('combo_swing', config.EXEC_SWING_TIME)

    def next_state(self):
        if self.state == 'combo_windup':
            self.strike()
        elif self.state == 'combo_swing':
            self.combo_index += 1
            if self.combo_index < len(EXEC_COMBO):
                self.begin_strike()
            else:
                self.enter('recover', config.EXEC_RECOVER_TIME)
        elif self.state == 'throw_windup':
            self.throw_sword()
            self.enter('throw_after', config.EXEC_THROW_AFTER)
        else:
            self.enter('walk')

    def throw_sword(self):
        sound.play('fire')
        x, y = self.x - self.W / 2, self.muzzle_y()
        sword = Bullet(x, y, self.player.x, self.player.y + config.PLAYER_H / 2, self, 'assets/monster/exec_sword.png', config.EXEC_SWORD_SPEED, EXEC_SWORD_FRAME_W)
        self.attacks.append(sword)
        game_world.add_object(sword, game_world.LAYER_EFFECT)
        game_world.add_collision_pair('player:bullet', None, sword)
        game_world.add_collision_pair('sword:bullet', None, sword)

    def handle_collision(self, group, other):
        if group == 'reflected:mage':
            sound.play('shield_block')
            self.player.camera.shake(config.BOSS_BLOCK_SHAKE_TIME, config.BOSS_BLOCK_SHAKE_AMP)
            self.enter('groggy', config.EXEC_GROGGY_TIME)
        else:
            super().handle_collision(group, other)

    def sprite_name(self):
        if self.state == 'combo_swing':
            return EXEC_COMBO[self.combo_index]
        return EXEC_STATE_SPRITE[self.state]

    def draw(self, camera):
        name = self.sprite_name()
        sprite = (self.flash_sprites if self.flash > 0 else self.sprites)[name]
        frame = int(self.time * EXEC_FPS[name]) % sprite.count
        sprite.draw(frame, self.x - camera.x, self.y + EXEC_CENTER_Y - camera.y)

    def make_death(self):
        strip = Strip('assets/monster/exec_death.png', EXEC_FRAME_W)
        return OneShot(strip, EXEC_DEATH_FPS, self.x, self.y + EXEC_CENTER_Y)


class SummonedFamiliar(Familiar):
    """보스전이 늘어져도 골드를 벌 수 없도록 골드를 주지 않는다."""
    GOLD = 0
    DASH_BONUS = 0


class BlackHole:
    """아레나 가운데로 플레이어를 끌어당긴다. 중심에 닿으면 HP가 준다."""

    def __init__(self, player, x, y):
        self.player = player
        self.x = x
        self.y = y
        self.timer = config.WITCH_HOLE_TIME
        self.effect = Effect('black-hole', x, y, loop=True)
        game_world.add_object(self.effect, game_world.LAYER_EFFECT)

    def update(self, dt):
        self.timer -= dt
        gap = self.x - self.player.x
        self.player.x += math.copysign(min(abs(gap), config.WITCH_HOLE_PULL * dt), gap)
        if self.timer <= 0:
            self.close()

    def close(self):
        game_world.remove_object(self.effect)
        game_world.remove_object(self)

    def draw(self, camera):
        pass

    def get_bb(self):
        return self.x - config.WITCH_HOLE_RADIUS, self.y, self.x + config.WITCH_HOLE_RADIUS, self.y + config.WITCH_HOLE_H

    def handle_collision(self, group, other):
        pass


class Witch(Boss):
    NAME = '균열의 마녀'
    MAX_HP = config.WITCH_HP
    W = config.WITCH_W
    H = config.WITCH_H
    AIRBORNE = True

    def __init__(self, x, y, player, wall):
        super().__init__(x, y + config.WITCH_ANCHOR_Y[0], player, wall)
        self.pattern = 0
        self.hidden = False
        self.familiars = []
        self.hole = None
        self.slash_hits = 0
        self.sprites = {name: Strip(f'assets/monster/witch_{name}.png', WITCH_FRAME_W) for name in WITCH_FPS}
        self.flash_sprites = {name: Strip(f'assets/monster/witch_{name}_flash.png', WITCH_FRAME_W) for name in WITCH_FPS}
        game_world.add_collision_pair('reflected:mage', None, self)

    def muzzle_y(self):
        return self.y + config.WITCH_MUZZLE_Y

    def think(self, dt):
        self.timer -= dt
        if self.timer <= 0:
            self.next_state()

    def next_state(self):
        if self.state == 'idle':
            self.start_pattern()
        elif self.state == 'fan_windup':
            self.fire_fan()
            self.enter('idle', config.WITCH_IDLE_TIME)
        elif self.state == 'vanish':
            self.reappear()
            self.enter('idle', config.WITCH_IDLE_TIME)
        elif self.state == 'summon_windup':
            self.summon()
            self.enter('idle', config.WITCH_IDLE_TIME)
        elif self.state == 'hole_windup':
            self.open_hole()
            self.enter('idle', config.WITCH_IDLE_TIME)
        else:
            self.start_pattern()

    def start_pattern(self):
        if self.slash_hits >= config.WITCH_ESCAPE_HITS:
            self.slash_hits = 0
            self.vanish()
            return
        low_hp = self.hp <= self.MAX_HP * config.WITCH_HOLE_HP_RATIO
        pattern = WITCH_RAGE_PATTERN if low_hp else WITCH_PATTERN
        # 패턴이 바뀌는 순간 자리가 어긋나지 않게 길이에 맞춰 돌린다.
        attack = pattern[self.pattern % len(pattern)]
        self.pattern = (self.pattern + 1) % len(pattern)
        if attack == 'fan':
            self.enter('fan_windup', config.WITCH_FAN_WINDUP)
        elif attack == 'teleport':
            self.vanish()
        elif attack == 'summon':
            self.enter('summon_windup', config.WITCH_SUMMON_WINDUP)
        else:
            self.enter('hole_windup', config.WITCH_HOLE_WINDUP)

    def fire_fan(self):
        sound.play('fire')
        muzzle_y = self.muzzle_y()
        aim = math.atan2(self.player.y + config.PLAYER_H / 2 - muzzle_y, self.player.x - self.x)
        for i, kind in enumerate(WITCH_FAN):
            angle = aim + (i - len(WITCH_FAN) // 2) * config.WITCH_FAN_SPREAD
            bullet = Bullet(self.x, muzzle_y, self.x + math.cos(angle), muzzle_y + math.sin(angle), self, f'assets/monster/bullet_{kind}.png', config.WITCH_BULLET_SPEED)
            self.attacks.append(bullet)
            game_world.add_object(bullet, game_world.LAYER_EFFECT)
            game_world.add_collision_pair('player:bullet', None, bullet)
            if kind == 'purple':
                game_world.add_collision_pair('sword:bullet', None, bullet)

    def summon(self):
        sound.play('teleport')
        group = game_world.collision_pairs['player:monster'][1]
        self.familiars = [familiar for familiar in self.familiars if familiar in group]
        # 이미 떠 있는 사역마가 있으면 그만큼 덜 불러 3마리를 넘지 않게 한다.
        for dx, height in config.WITCH_SUMMON_SPOTS[len(self.familiars):]:
            familiar = SummonedFamiliar(self.x + dx, config.GROUND_TOP + height, self.player)
            self.familiars.append(familiar)
            self.attacks.append(familiar)
            game_world.add_object(familiar, game_world.LAYER_MONSTER)
            game_world.add_collision_pair('player:monster', None, familiar)
            game_world.add_collision_pair('sword:monster', None, familiar)
            game_world.add_collision_pair('shard:monster', None, familiar)

    def open_hole(self):
        sound.play('blackhole')
        self.hole = BlackHole(self.player, self.player.camera.base_x + config.SCREEN_W / 2, config.GROUND_TOP)
        self.attacks.append(self.hole)
        game_world.add_object(self.hole, game_world.LAYER_EFFECT)
        game_world.add_collision_pair('player:strike', None, self.hole)

    def defeat(self, by_dash):
        if self.hole:
            game_world.remove_object(self.hole.effect)
        super().defeat(by_dash)

    def pick_destination(self):
        spots = [(self.start_x + dx, config.GROUND_TOP + height) for dx in config.WITCH_ANCHOR_X for height in config.WITCH_ANCHOR_Y
                 if not (self.start_x + dx == self.x and config.GROUND_TOP + height == self.y)]
        far = [spot for spot in spots if spot[0] - self.player.x >= config.WITCH_TELEPORT_GAP]
        # 플레이어가 맨 오른쪽까지 와 있으면 가장 먼 자리의 다른 높이로 간다.
        rightmost = self.start_x + config.WITCH_ANCHOR_X[-1]
        return random.choice(far or [spot for spot in spots if spot[0] == rightmost])

    def vanish(self):
        sound.play('teleport')
        game_world.add_object(Effect('blink-out', self.x, self.y, speed=config.BLINK_FX_SPEED, scale=config.BLINK_FX_SCALE), game_world.LAYER_EFFECT)
        self.hidden = True
        for group in WITCH_COLLISION_GROUPS:
            game_world.remove_collision(group, self)
        # 나타날 자리를 미리 보여 준다. 반사 탄이 따라가도록 위치도 먼저 옮겨 둔다.
        self.x, self.y = self.pick_destination()
        circle = OneShot(Strip('assets/monster/witch_circle.png', WITCH_CIRCLE_FRAME_W), WITCH_CIRCLE_FPS, self.x, self.y + self.H / 2)
        self.attacks.append(circle)
        game_world.add_object(circle, game_world.LAYER_EFFECT)
        self.enter('vanish', config.WITCH_TELEPORT_TIME)

    def reappear(self):
        self.hidden = False
        game_world.add_object(Effect('blink-in', self.x, self.y, speed=config.BLINK_FX_SPEED, scale=config.BLINK_FX_SCALE), game_world.LAYER_EFFECT)
        for group in WITCH_COLLISION_GROUPS:
            game_world.add_collision_pair(group, None, self)

    def handle_collision(self, group, other):
        if group == 'reflected:mage':
            self.take_hit(record.stat('attack') * config.WITCH_REFLECT_DAMAGE_RATIO)
        else:
            super().handle_collision(group, other)

    def knock_back(self):
        pass

    def on_slash(self, sword):
        self.slash_hits += 1
        ratio = config.TRIPLE_DAMAGE_RATIO if sword.finisher else 1
        self.take_hit(record.stat('attack') * ratio * config.WITCH_SLASH_DAMAGE_RATE)
        if self.hp > 0:
            self.apply_element()

    def on_dash_hit(self):
        # 돌진하는 사이 사라졌으면 빗나간다.
        if not self.hidden:
            super().on_dash_hit()

    def draw(self, camera):
        if self.hidden:
            return
        name = 'cast' if self.state in WITCH_CAST_STATES else 'float'
        sprite = (self.flash_sprites if self.flash > 0 else self.sprites)[name]
        frame = int(self.time * WITCH_FPS[name]) % sprite.count
        sprite.draw(frame, self.x - camera.x, self.y + WITCH_CENTER_Y - camera.y)

    def make_death(self):
        strip = Strip('assets/monster/witch_death.png', WITCH_FRAME_W)
        return OneShot(strip, WITCH_DEATH_FPS, self.x, self.y + WITCH_CENTER_Y)
