from pico2d import draw_rectangle

import config
import game_world
import record
import sound
from monster import Monster
from sprite import Effect, OneShot, Strip, load_fx_sheet


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
            self.think(dt)
        elif self.x - self.player.x <= config.BOSS_ENGAGE_GAP:
            self.player.enter_boss_fight(self)
            self.enter('intro', config.BOSS_INTRO_TIME)

    def add_attack(self, attack):
        self.attacks.append(attack)
        game_world.add_object(attack, game_world.LAYER_EFFECT)
        game_world.add_collision_pair('player:strike', None, attack)

    def gold(self, by_dash, bonus):
        stage = self.player.stage
        return config.BOSS_REPEAT_GOLD[stage] if stage in record.data['bosses'] else config.BOSS_FIRST_GOLD[stage]

    def damage_rate(self):
        return 1

    def take_hit(self, damage, by_dash=False):
        self.hp -= damage * self.damage_rate()
        self.flash = config.BOSS_FLASH_TIME
        sound.play('boss_hit')
        if self.hp > 0:
            self.player.play_hit_feedback(self, by_dash)
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
                       'guard': 'guard', 'groggy': 'groggy'}
# 이 순서대로 공격을 돌린다. 내려찍기는 플레이어가 사거리에 들어올 때까지 걸어간다.
WARDEN_PATTERN = ('slam', 'guard')


class Warden(Boss):
    NAME = '봉인의 수문장'
    MAX_HP = config.BOSS_HP

    def __init__(self, x, y, player, wall):
        super().__init__(x, y, player, wall)
        self.pattern = 0
        self.cleave = load_fx_sheet(WARDEN_ATTACK_FX)[1]['meta']['pixelfx']['act']
        self.sprites = {name: Strip(f'assets/monster/boss_{name}.png', WARDEN_FRAME_W) for name in WARDEN_FPS}
        self.flash_sprites = {name: Strip(f'assets/monster/boss_{name}_flash.png', WARDEN_FRAME_W) for name in WARDEN_FPS}

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
        else:
            self.enter('guard', config.BOSS_GUARD_TIME)

    def next_state(self):
        if self.state == 'windup':
            effect = Effect(WARDEN_ATTACK_FX, self.x, self.y, scale=config.BOSS_FX_SCALE, flip=True)
            game_world.add_object(effect, game_world.LAYER_EFFECT)
            self.enter('strike', self.cleave['hits'][0]['t'])
        elif self.state == 'strike':
            self.slam()
            self.enter('recover', config.BOSS_RECOVER_TIME)
        else:
            self.enter('walk')

    def slam(self):
        sound.play('boss_slam')
        hit = self.cleave['hits'][0]
        self.player.freeze(hit['freeze'] * config.BOSS_HIT_STOP_RATIO)
        self.player.camera.shake(hit['shake'], hit['amp'] * config.SPRITE_SCALE)
        self.add_attack(AttackBox(self.x - config.BOSS_STRIKE_REACH, self.y, self.x - config.BOSS_W / 2, self.y + config.BOSS_STRIKE_H))

    def damage_rate(self):
        return config.BOSS_GROGGY_DAMAGE_RATE if self.state == 'groggy' else 1

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
        if self.state in ('windup', 'strike'):
            bottom = config.GROUND_TOP - 8 - camera.y
            draw_rectangle(self.x - config.BOSS_STRIKE_REACH - camera.x, bottom, self.x - config.BOSS_W / 2 - camera.x, bottom + 8,
                           *config.BOSS_STRIKE_WARNING_COLOR, 255, True)
        name = WARDEN_STATE_SPRITE[self.state]
        sprite = (self.flash_sprites if self.flash > 0 else self.sprites)[name]
        frame = int(self.time * WARDEN_FPS[name]) % sprite.count
        sprite.draw(frame, self.x - camera.x, self.y + WARDEN_CENTER_Y - camera.y)

    def make_death(self):
        strip = Strip('assets/monster/boss_death.png', WARDEN_FRAME_W)
        return OneShot(strip, WARDEN_DEATH_FPS, self.x, self.y + WARDEN_CENTER_Y)
