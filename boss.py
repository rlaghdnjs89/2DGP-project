from pico2d import draw_rectangle

import config
import game_world
import record
import sound
from monster import Monster
from sprite import Effect, OneShot, Strip, load_fx_sheet


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


class Boss(Monster):
    """스테이지 끝을 지키는 보스의 공통 동작. 상태별 행동은 think에서 정한다."""
    AIRBORNE = False

    def __init__(self, x, y, player, wall):
        super().__init__(x, y, player)
        self.wall = wall
        self.hp = self.MAX_HP
        self.state = 'wait'
        self.timer = 0
        self.time = 0
        self.flash = 0
        self.last_sword = None
        self.attacks = []

    def enter(self, state, timer=0):
        self.state = state
        self.timer = timer
        self.time = 0

    def update(self, dt):
        self.time += dt
        self.flash = max(0, self.flash - dt)
        if self.state != 'wait':
            self.think(dt * self.time_rate())
        elif self.x - self.player.x <= config.BOSS_ENGAGE_GAP:
            self.player.enter_boss_fight(self)
            self.enter('intro', config.BOSS_INTRO_TIME)

    def add_hazard(self, hazard):
        self.attacks.append(hazard)
        game_world.add_object(hazard, game_world.LAYER_EFFECT)

    def add_attack(self, attack):
        self.attacks.append(attack)
        game_world.add_object(attack, game_world.LAYER_EFFECT)
        game_world.add_collision_pair('player:strike', None, attack)

    def gold(self, by_dash, bonus):
        stage = self.player.stage
        return config.BOSS_REPEAT_GOLD[stage] if stage in record.data['bosses'] else config.BOSS_FIRST_GOLD[stage]

    def time_rate(self):
        return 1

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

    def defeat(self, by_dash):
        self.player.on_kill(self, by_dash)
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
        center_y = self.y + config.BOSS_H / 2
        game_world.add_object(Effect('plasma-explosion', self.x, center_y, scale=config.BOSS_DEATH_FX_SCALE), game_world.LAYER_EFFECT)

    def handle_collision(self, group, other):
        # 칼 판정이 여러 프레임 살아 있어도 한 번 휘두르면 한 번만 맞는다.
        if group == 'sword:monster' and other is not self.last_sword:
            self.last_sword = other
            self.on_slash()

    def on_slash(self):
        self.take_hit(record.stat('attack'))

    def on_dash_hit(self):
        self.take_hit(record.stat('attack') * config.DASH_DAMAGE_RATIO, by_dash=True)

    def get_bb(self):
        half_w = config.BOSS_W / 2
        return self.x - half_w, self.y, self.x + half_w, self.y + config.BOSS_H

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
        return config.BOSS_RAGE_SPEED if self.raging else 1

    def damage_rate(self):
        if self.state == 'groggy':
            return config.BOSS_GROGGY_DAMAGE_RATE
        return 1 if self.state == 'recover' else config.BOSS_ARMOR_DAMAGE_RATE

    def on_damaged(self):
        if not self.raging and self.hp <= self.MAX_HP * config.BOSS_RAGE_HP_RATIO:
            self.raging = True
            sound.play('boss_roar')
            self.player.camera.shake(config.BOSS_DEATH_SHAKE_TIME, config.BOSS_DEATH_SHAKE_AMP)

    def on_slash(self):
        if self.state != 'guard':
            super().on_slash()
            return
        # 방패는 베기를 튕겨낸다. 일섬만 깰 수 있다.
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
