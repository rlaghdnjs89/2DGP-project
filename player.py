import math

from pico2d import (SDL_BUTTON_LEFT, SDL_BUTTON_RIGHT, SDL_KEYDOWN, SDL_KEYUP, SDL_MOUSEBUTTONDOWN, SDLK_SPACE, SDLK_a,
                    SDLK_d, SDLK_e, SDLK_q, SDLK_s, SDLK_w, get_time)

import config
import game_world
import record
import skills
import sound
from coin import Coin
from sprite import Effect, Strip, load_fx_sheet
from ui import draw_overlay

FRAME_W = 64
ANIMATION_FPS = {'run': 16, 'idle': 6, 'rise': 8, 'fall': 8, 'slide': 10, 'slash': 16, 'dash': 16, 'hit': 16, 'charge': 10, 'cut': 16}
OTHER_BUTTON = {SDL_BUTTON_LEFT: SDL_BUTTON_RIGHT, SDL_BUTTON_RIGHT: SDL_BUTTON_LEFT}
MOVE_KEYS = {SDLK_a: -1, SDLK_d: 1}
ULTIMATES = ('fire3', 'ice3', 'bolt3')
CHARGE_FX = 'charge-up'
IMPLOSION_FX = 'implosion'
BURST_FX = 'plasma-explosion'
# 시트에서 검기가 빠르게 끝나도록 빨리 재생한다.
SLASH_FX_SPEED = 1.6
SLASH_FX_Y = 8
THRUST_FX_SPEED = 2.5
# 찌르기 검기 끝이 찌르기 사거리 끝에 닿는 크기다.
THRUST_FX_SCALE = 1.3
KILL_FX_SPEED = 1.5
KILL_FX_SCALE = 2
DASH_KILL_FX_SPEED = 2


class Run:
    ANIMATION = 'run'

    def __init__(self, player):
        self.player = player

    def enter(self):
        self.player.air_jumps = config.AIR_JUMPS

    def update(self, dt):
        player = self.player
        if player.jump_buffer > 0:
            player.jump()
        elif player.try_attack():
            pass
        elif player.slide_buffer > 0 and player.s_held:
            player.change_state(player.slide_state)
        elif not player.on_ground:
            player.change_state(player.jump_state)


class Slide:
    ANIMATION = 'slide'

    def __init__(self, player):
        self.player = player
        self.timer = 0

    def enter(self):
        self.timer = 0
        self.player.slide_buffer = 0

    def update(self, dt):
        player = self.player
        self.timer += dt
        # 슬라이딩 중에 누른 공격이 끝난 뒤에 뒤늦게 나가지 않게 버린다.
        player.slash_buffer = 0
        player.dash_buffer = 0
        if not player.on_ground:
            player.change_state(player.jump_state)
        elif not player.s_held or self.timer >= config.SLIDE_MAX_TIME:
            player.change_state(player.run_state)


class Jump:
    def __init__(self, player):
        self.player = player

    def enter(self):
        pass

    def update(self, dt):
        player = self.player
        if player.on_ground:
            player.change_state(player.run_state)
            # 착지 직전에 누른 입력이 같은 프레임에 이어지도록 Run에 바로 넘긴다.
            player.run_state.update(dt)
        elif player.jump_buffer > 0 and player.air_jumps > 0:
            player.air_jumps -= 1
            player.jump()
        elif player.slide_buffer > 0 and record.has_skill('dive'):
            player.change_state(player.dive_state)
        else:
            player.try_attack()


class Dive:
    ANIMATION = 'fall'

    def __init__(self, player):
        self.player = player

    def enter(self):
        self.player.slide_buffer = 0
        self.player.hang_timer = 0

    def update(self, dt):
        player = self.player
        player.vy = -config.DIVE_SPEED
        if player.on_ground:
            player.land_dive()


class Slash:
    ANIMATION = 'slash'

    def __init__(self, player):
        self.player = player
        self.timer = 0
        self.prev_state = None

    def enter(self):
        self.timer = 0

    def update(self, dt):
        player = self.player
        self.timer += dt
        # 왼손과 오른손 조작을 분리하므로 베는 중에도 점프와 슬라이딩은 그대로 받는다.
        self.prev_state.update(dt)
        if player.state is self and self.timer >= record.stat('attack_speed'):
            player.change_state(self.prev_state)


class Dash:
    ANIMATION = 'dash'

    def __init__(self, player):
        self.player = player
        self.timer = 0
        self.target = None
        self.start_x = 0
        self.start_y = 0

    def enter(self):
        self.timer = 0
        self.start_x = self.player.x
        self.start_y = self.player.y

    def update(self, dt):
        player = self.player
        self.timer += dt
        t = min(1, self.timer / config.DASH_TIME)
        # 대상이 움직여도 빗나가지 않도록 매 프레임 현재 위치로 보간한다.
        player.x = self.start_x + (self.target.dash_x() - self.start_x) * t
        player.y = self.start_y + (self.target.dash_y() - self.start_y) * t
        if t >= 1:
            player.finish_dash(self.target)


class Flurry:
    """천검난무. 그 자리에 떠서 주변을 연속으로 베고 그동안 무적이다."""
    ANIMATION = 'slash'

    def __init__(self, player):
        self.player = player
        self.timer = 0
        self.next_hit = 0
        self.effect = None

    def enter(self):
        player = self.player
        self.timer = config.FLURRY_TIME
        self.next_hit = 0
        player.flurry_cooldown = config.FLURRY_COOLDOWN
        player.vy = 0
        self.effect = Effect('dagger-flurry', 0, 0, player, config.FLURRY_FX_SPEED, flip=player.facing < 0, loop=True)
        game_world.add_object(self.effect, game_world.LAYER_EFFECT)

    def update(self, dt):
        player = self.player
        self.timer -= dt
        self.next_hit -= dt
        # 다음 프레임의 중력을 건너뛰어 그 높이에 머문다.
        player.hang_timer = dt
        if self.next_hit <= 0:
            self.next_hit = config.FLURRY_INTERVAL
            self.hit_around()
        if self.timer <= 0:
            game_world.remove_object(self.effect)
            player.change_state(player.run_state if player.on_ground else player.jump_state)

    def hit_around(self):
        player = self.player
        sound.play('slash')
        center_y = player.y + config.PLAYER_H / 2
        for monster in game_world.collision_pairs['player:monster'][1][:]:
            if math.hypot(monster.dash_x() - player.x, monster.dash_y() + config.PLAYER_H / 2 - center_y) <= config.FLURRY_RADIUS:
                monster.on_flurry_hit()


class Pierce:
    """관통 일섬. 화면 끝까지 곧게 돌진하며 경로의 적을 벤다."""
    ANIMATION = 'dash'

    def __init__(self, player):
        self.player = player
        self.timer = 0
        self.start_x = 0
        self.end_x = 0

    def enter(self):
        player = self.player
        self.timer = 0
        self.start_x = player.x
        if player.facing > 0:
            self.end_x = max(player.x, min(player.camera.base_x + config.SCREEN_W - config.PIERCE_END_MARGIN, player.forward_limit()))
        else:
            self.end_x = min(player.x, max(player.camera.base_x + config.PIERCE_END_MARGIN, player.forward_limit()))
        player.pierce_cooldown = config.PIERCE_COOLDOWN
        player.vy = 0
        player.hang_timer = 0

    def update(self, dt):
        player = self.player
        self.timer += dt
        t = min(1, self.timer / config.PIERCE_TIME)
        player.x = self.start_x + (self.end_x - self.start_x) * t
        for monster in game_world.collision_pairs['player:monster'][1][:]:
            if not monster.IS_BOSS and game_world.collide(player, monster):
                monster.kill(by_dash=True)
        if t >= 1:
            player.finish_pierce()


class Layer:
    """이펙트 사이에 끼워 넣는 그리기 호출."""

    def __init__(self, draw):
        self.draw = draw

    def update(self, dt):
        pass


class Flash:
    """화면 전체가 하얗게 번쩍였다가 사라진다."""

    def __init__(self, opacity, time):
        self.opacity = opacity
        self.time = time
        self.timer = time

    def update(self, dt):
        self.timer -= dt
        if self.timer <= 0:
            game_world.remove_object(self)

    def draw(self, camera):
        draw_overlay('assets/ui/white.png', self.opacity * self.timer / self.time)


class Cut:
    """차원 절단. 힘을 모은 뒤 터뜨리고, 터진 뒤의 느린 시간은 Player.tick_cut_after가 맡는다."""

    def __init__(self, player):
        self.player = player
        self.timer = 0
        self.target = None
        self.layers = ()
        self.dim_opacity = 0
        self.ANIMATION = 'charge'
        self.charge_time = load_fx_sheet(CHARGE_FX)[1]['meta']['pixelfx']['act']['hits'][0]['t']

    def enter(self):
        player = self.player
        self.timer = 0
        self.target = player.bullet_target
        self.ANIMATION = 'charge'
        player.bullet_target = None
        player.vy = 0
        player.hang_timer = 0
        sound.play('cut_charge')
        self.dim_opacity = 0
        # 주변은 어두워지고, implosion의 어두운 구체가 플레이어를 가리지 않게 구체 위에 플레이어를 다시 그린다.
        dim = Layer(lambda camera: draw_overlay('assets/ui/black.png', self.dim_opacity))
        body = Layer(player.draw)
        self.layers = (dim, body)
        implosion_speed = config.IMPLOSION_POP_TIME / self.charge_time
        implosion = Effect(IMPLOSION_FX, 0, config.PLAYER_H / 2, player, implosion_speed, config.CUT_FX_SCALE)
        for layer in (dim, implosion, body, Effect(CHARGE_FX, 0, 0, player, scale=config.CUT_FX_SCALE)):
            game_world.add_object(layer, game_world.LAYER_EFFECT)

    def update(self, dt):
        if self.target is None:
            return
        self.timer += dt
        power = min(1, self.timer / self.charge_time)
        self.dim_opacity = config.CUT_DIM_OPACITY * power
        # 힘이 찰수록 땅이 크게 울린다.
        self.player.camera.shake(0.05, config.CUT_RUMBLE_AMP * power)
        if self.timer >= self.charge_time:
            for layer in self.layers:
                game_world.remove_object(layer)
            self.player.cut_target(self.target)
            self.target = None
            self.ANIMATION = 'cut'
            self.player.animation_time = 0


class Sword:
    def __init__(self, player, spin, finisher, perfect_target):
        self.player = player
        self.spin = spin
        self.finisher = finisher
        # 게이지가 허용 범위에 있을 때 벤 몬스터. 이 칼로 처치하면 더 강한 타격 연출을 낸다.
        self.perfect_target = perfect_target
        self.timer = config.SWORD_TIME
        self.hit_boss = False

    def update(self, dt):
        self.timer -= dt
        if self.timer <= 0:
            game_world.remove_object(self)

    def draw(self, camera):
        pass

    def get_bb(self):
        return self.player.slash_bb(self.spin)

    def handle_collision(self, group, other):
        pass


class Hit:
    ANIMATION = 'hit'

    def __init__(self, player):
        self.player = player
        self.timer = 0

    def enter(self):
        self.timer = 0

    def update(self, dt):
        player = self.player
        self.timer += dt
        # 맞은 순간 뒤로 밀렸다가 경직이 풀릴 때쯤 다시 달리는 속도를 되찾는다.
        player.x -= player.facing * config.KNOCKBACK_SPEED * max(0, 1 - self.timer / config.HIT_STUN_TIME) * dt
        if self.timer >= config.HIT_STUN_TIME:
            player.change_state(player.run_state if player.on_ground else player.jump_state)


class Player:
    def __init__(self, camera):
        self.camera = camera
        self.x = config.PLAYER_SCREEN_X
        self.y = config.GROUND_TOP
        self.prev_y = self.y
        self.vy = 0
        # 1이면 오른쪽, -1이면 왼쪽을 본다. 달리기 구간에서는 늘 오른쪽이고 보스전에서는 보스 쪽을 본다.
        self.facing = 1
        self.on_ground = True
        self.air_jumps = config.AIR_JUMPS
        self.jump_buffer = 0
        self.slide_buffer = 0
        self.slash_buffer = 0
        self.dash_buffer = 0
        self.s_held = False
        self.sword = None
        self.dash_charges = self.max_dash_charges()
        self.dash_recharge = record.stat('dash_recharge')
        self.hang_timer = 0
        self.max_hp = int(record.stat('hp'))
        self.hp = self.max_hp
        self.invincible_timer = 0
        self.kills = 0
        self.run_time = 0
        self.run_gold = 0
        self.gold_fraction = 0
        self.combo = 0
        self.stage = 0
        record.data['best_stage'] = max(record.data['best_stage'], self.stage + 1)
        self.boss = None
        self.altar = None
        self.window = None
        self.next_wall = None
        self.flurry_cooldown = 0
        self.pierce_cooldown = 0
        self.ultimate_cooldown = 0
        self.cast_timer = 0
        self.cleared = False
        self.triple_count = 0
        self.triple_timer = 0
        self.held_move = set()
        self.bullet_target = None
        self.bullet_timer = 0
        self.cut_after_timer = 0
        self.press_times = {}
        self.animation_time = 0
        self.hit_stop = 0
        self.trail = []
        self.sprites = {name: Strip(f'assets/player/{name}.png', FRAME_W) for name in ANIMATION_FPS}

        self.run_state = Run(self)
        self.slide_state = Slide(self)
        self.jump_state = Jump(self)
        self.slash_state = Slash(self)
        self.dash_state = Dash(self)
        self.dive_state = Dive(self)
        self.flurry_state = Flurry(self)
        self.pierce_state = Pierce(self)
        self.cut_state = Cut(self)
        self.hit_state = Hit(self)
        self.state = self.run_state

    def change_state(self, state):
        self.state = state
        self.animation_time = 0
        state.enter()

    def jump(self):
        sound.play('jump')
        self.vy = config.JUMP_SPEED
        self.jump_buffer = 0
        self.hang_timer = 0
        self.change_state(self.jump_state)

    def try_attack(self):
        # 운석을 시전하는 동안에는 공격할 수 없다.
        if self.cast_timer > 0:
            self.slash_buffer = 0
            self.dash_buffer = 0
            return False
        if self.dash_buffer > 0 and self.dash_charges > 0:
            target = self.find_dash_target()
            if target:
                self.start_dash(target)
                return True
            if record.has_skill('blink'):
                self.blink()
                return True
        if self.slash_buffer > 0 and self.state is not self.slash_state:
            self.start_slash()
            return True
        return False

    def start_slash(self):
        sound.play('slash')
        self.slash_buffer = 0
        spin = self.spin_ready()
        aim = self.gauge_target()
        perfect_target = aim[0] if aim and aim[1] <= aim[2] else None
        self.slash_state.prev_state = self.state
        self.change_state(self.slash_state)
        finisher = self.count_triple()
        self.sword = Sword(self, spin, finisher, perfect_target)
        game_world.add_object(self.sword, game_world.LAYER_EFFECT)
        self.play_slash_effect(spin, finisher)
        game_world.add_collision_pair('sword:monster', self.sword, None)
        game_world.add_collision_pair('sword:bullet', self.sword, None)

    def spin_ready(self):
        """지금 베면 회전 베기가 나가는지."""
        return not self.on_ground and record.has_skill('spin')

    def slash_bb(self, spin):
        if spin:
            center_y = self.y + config.PLAYER_H / 2
            return (self.x - config.SPIN_REACH_X, center_y - config.SPIN_REACH_Y,
                    self.x + config.SPIN_REACH_X, center_y + config.SPIN_REACH_Y)
        bottom = self.y + (config.PLAYER_H - config.SWORD_H) / 2
        reach = config.THRUST_REACH if record.has_skill('thrust') else config.SWORD_REACH
        front = self.x + self.facing * config.PLAYER_W / 2
        left, right = (front, front + reach) if self.facing > 0 else (front - reach, front)
        return left, bottom, right, bottom + config.SWORD_H

    def gauge_target(self):
        """베기 게이지를 띄울 (몬스터, 몬스터까지 남은 거리, 베기 사거리)를 돌려준다.
        앞에 있고 베기 높이에 걸치는 몬스터 중 가장 가까운 것이다. 남은 거리가 사거리 이하면 지금 베어 맞힐 수 있다."""
        if self.bullet_target or not self.can_use_skill_key():
            return None
        sword_left, sword_bottom, sword_right, sword_top = self.slash_bb(self.spin_ready())
        front = self.x + self.facing * config.PLAYER_W / 2
        reach = sword_right - front if self.facing > 0 else front - sword_left
        aims = []
        for monster in skills.nearby_monsters(self):
            left, bottom, right, top = monster.get_bb()
            gap = left - front if self.facing > 0 else front - right
            # 이미 몸에 닿은 몬스터는 피해를 준 뒤라 노릴 대상이 아니다.
            if 0 <= gap <= reach + config.SLASH_GAUGE_LEAD and bottom <= sword_top and top >= sword_bottom:
                aims.append((gap, monster))
        if not aims:
            return None
        gap, monster = min(aims, key=lambda aim: aim[0])
        return monster, gap, reach

    def count_triple(self):
        """이번 베기가 3연격의 마지막이면 True를 돌려준다."""
        if not record.has_skill('triple'):
            return False
        if self.triple_timer <= 0:
            self.triple_count = 0
            self.triple_timer = config.TRIPLE_WINDOW
        self.triple_count += 1
        if self.triple_count < 3:
            return False
        self.triple_timer = 0
        return True

    def play_slash_effect(self, spin, finisher):
        flip = self.facing < 0
        if finisher:
            game_world.add_object(Effect('double-slash', 0, SLASH_FX_Y, self, SLASH_FX_SPEED, flip=flip), game_world.LAYER_EFFECT)
            return
        if spin:
            game_world.add_object(Effect('spin-slash', 0, SLASH_FX_Y, self, SLASH_FX_SPEED, flip=flip), game_world.LAYER_EFFECT)
            return
        # 각인이 있으면 검기가 그 원소의 색으로 바뀐다.
        slash = 'sword-slash-' + record.data['element'] if record.data['element'] else 'sword-slash'
        game_world.add_object(Effect(slash, 0, SLASH_FX_Y, self, SLASH_FX_SPEED, flip=flip), game_world.LAYER_EFFECT)
        if record.has_skill('thrust'):
            game_world.add_object(Effect('thrust', 0, 0, self, THRUST_FX_SPEED, THRUST_FX_SCALE, flip), game_world.LAYER_EFFECT)

    def find_dash_target(self):
        def dist2(monster):
            return (monster.x - self.x) ** 2 + (monster.dash_y() - self.y) ** 2

        monsters = game_world.collision_pairs['player:monster'][1]
        in_range = [m for m in monsters if (m.x - self.x) * self.facing > 0 and dist2(m) <= config.DASH_RANGE ** 2]
        return min(in_range, key=dist2, default=None)

    def start_dash(self, target):
        sound.play('dash')
        self.dash_buffer = 0
        self.dash_charges -= 1
        self.hang_timer = 0
        self.vy = 0
        # 돌진 중에 남은 베기 판정이 대상을 먼저 처치하면 돌진이 끝날 때 또 처치하게 된다.
        if self.sword:
            game_world.remove_object(self.sword)
        self.dash_state.target = target
        self.change_state(self.dash_state)

    def blink(self):
        sound.play('teleport')
        self.dash_buffer = 0
        self.dash_charges -= 1
        game_world.add_object(Effect('blink-out', self.x, self.y, speed=config.BLINK_FX_SPEED), game_world.LAYER_EFFECT)
        x = self.x + self.facing * config.BLINK_DISTANCE
        self.x = min(x, self.forward_limit()) if self.facing > 0 else max(x, self.forward_limit())
        if not self.on_ground:
            self.vy = 0
            self.hang_timer = config.DASH_HANG_TIME
        game_world.add_object(Effect('blink-in', self.x, self.y, speed=config.BLINK_FX_SPEED), game_world.LAYER_EFFECT)

    def can_use_skill_key(self):
        return self.state in (self.run_state, self.jump_state, self.slash_state)

    def use_flurry(self):
        if record.has_skill('flurry') and self.flurry_cooldown <= 0 and self.can_use_skill_key():
            self.change_state(self.flurry_state)

    def use_pierce(self):
        if record.has_skill('pierce') and self.pierce_cooldown <= 0 and self.can_use_skill_key():
            sound.play('dash')
            if self.sword:
                game_world.remove_object(self.sword)
            self.change_state(self.pierce_state)

    def finish_pierce(self):
        sound.play('kill')
        game_world.add_object(Effect('crit-hit', self.x, self.y + config.PLAYER_H / 2, speed=DASH_KILL_FX_SPEED), game_world.LAYER_EFFECT)
        boss = self.boss
        # 공중의 마녀처럼 높이가 다르면 닿지 않는다.
        if boss and self.y <= boss.y + boss.H and self.y + config.PLAYER_H >= boss.y:
            boss.on_pierce_hit()
        self.hang_timer = config.DASH_HANG_TIME
        self.change_state(self.jump_state)

    def forward_limit(self):
        """스킬로 앞으로 튀어 나갈 때 넘으면 안 되는 위치."""
        if self.boss:
            return self.boss.dash_x()
        if self.altar:
            return self.altar.stop_x()
        if self.next_wall:
            return self.next_wall.x - config.PLAYER_W / 2 - config.BOSS_CONTACT_GAP
        return math.inf

    def finish_dash(self, target):
        target.on_dash_hit()
        if target.AIRBORNE:
            self.hang_timer = config.DASH_HANG_TIME
        self.change_state(self.jump_state)

    def land_dive(self):
        sound.play('rock')
        self.freeze(config.DIVE_HIT_STOP)
        self.camera.shake(config.DIVE_SHAKE_TIME, config.DIVE_SHAKE_AMP)
        game_world.add_object(Effect('heavy-landing', self.x, self.y), game_world.LAYER_EFFECT)
        left, right = self.x - config.DIVE_REACH, self.x + config.DIVE_REACH
        for monster in game_world.collision_pairs['player:monster'][1][:]:
            bb = monster.get_bb()
            # 지상 적만 맞는다. 공중의 사역마와 발판 위의 적은 충격파가 닿지 않는다.
            if not monster.AIRBORNE and bb[0] <= right and bb[2] >= left and abs(monster.y - self.y) < config.PLAYER_H:
                monster.on_dive_hit()
        self.change_state(self.run_state)

    def max_dash_charges(self):
        return config.DASH_MAX_CHARGES + 1 if record.has_skill('charge') else config.DASH_MAX_CHARGES

    def tick_dash_recharge(self, dt):
        if self.dash_charges == self.max_dash_charges():
            self.dash_recharge = record.stat('dash_recharge')
            return
        self.dash_recharge -= dt
        if self.dash_recharge <= 0:
            self.dash_charges += 1
            self.dash_recharge = record.stat('dash_recharge')

    def enter_boss_fight(self, boss):
        sound.play('boss_roar')
        self.boss = boss

    def end_boss_fight(self):
        self.boss = None
        self.facing = 1

    def at_altar(self):
        return self.altar is not None and self.altar.is_stopped()

    def apply_stats(self):
        # 원석에서는 항상 HP가 가득 차 있으므로 늘어난 칸도 채운다.
        self.max_hp = int(record.stat('hp'))
        self.hp = self.max_hp

    def arrive_at_altar(self):
        self.hp = self.max_hp
        sound.play('heal')
        self.jump_buffer = 0
        self.slide_buffer = 0
        self.slash_buffer = 0
        self.dash_buffer = 0

    def enter_bullet_time(self, wall):
        sound.set_music_volume(config.MUSIC_VOLUME_DUCK)
        self.bullet_target = wall
        self.bullet_timer = config.BULLET_TIME_MAX
        self.press_times.clear()
        self.jump_buffer = 0
        self.slide_buffer = 0
        self.slash_buffer = 0
        self.dash_buffer = 0
        # 슬라이딩에서는 절단으로 넘어갈 수 없으므로 달리기로 돌린다 (Q3).
        if self.state is self.slide_state:
            self.change_state(self.run_state)

    def end_bullet_time(self):
        sound.set_music_volume(config.MUSIC_VOLUME)
        self.bullet_target = None

    def tick_bullet_time(self, real_dt):
        self.bullet_timer -= real_dt
        if self.bullet_timer <= 0:
            target = self.bullet_target
            self.end_bullet_time()
            target.on_bullet_timeout()

    def is_simultaneous_click(self, button):
        if button not in OTHER_BUTTON:
            return False
        # 불릿 타임으로 느려져도 판정 시간은 변하지 않도록 실제 시간을 쓴다 (CT-1).
        now = get_time()
        other = OTHER_BUTTON[button]
        if other in self.press_times and now - self.press_times[other] <= config.SIMULTANEOUS_WINDOW:
            self.press_times.clear()
            return True
        self.press_times[button] = now
        return False

    def learned_ultimate(self):
        return next((skill for skill in ULTIMATES if record.has_skill(skill)), None)

    def use_ultimate(self):
        skill = self.learned_ultimate()
        # 궁극기는 보스에게만 쓰므로 달리기 구간에서는 쿨타임을 쓰지 않는다.
        if skill and self.boss and self.ultimate_cooldown <= 0 and self.cast_timer <= 0:
            self.ultimate_cooldown = config.ULTIMATE_COOLDOWN
            skills.cast_ultimate(skill, self, self.boss)

    def cut_target(self, target):
        sound.play('cut')
        sound.play('cut_boom')
        target.on_cut()
        self.cut_after_timer = config.CUT_AFTER_TIME
        self.camera.shake(config.CUT_SHAKE_TIME, config.CUT_SHAKE_AMP)
        self.freeze(config.CUT_HIT_STOP)
        center_x = self.camera.base_x + config.SCREEN_W / 2
        game_world.add_object(Effect(BURST_FX, *target.cut_center(), scale=config.CUT_FX_SCALE), game_world.LAYER_EFFECT)
        game_world.add_object(Effect('impact-frame', center_x, config.SCREEN_H / 2, speed=config.IMPACT_FRAME_SPEED, scale=config.IMPACT_FRAME_SCALE),
                              game_world.LAYER_EFFECT)

    def tick_cut_after(self, real_dt):
        """터진 뒤의 느린 시간을 실제 시간으로 재고, 이번 프레임의 시간 배율을 돌려준다."""
        self.cut_after_timer -= real_dt
        if self.cut_after_timer <= 0:
            sound.set_music_volume(config.MUSIC_VOLUME)
            self.change_state(self.run_state if self.on_ground else self.jump_state)
            return 1
        t = 1 - self.cut_after_timer / config.CUT_AFTER_TIME
        return config.CUT_AFTER_SCALE + (1 - config.CUT_AFTER_SCALE) * t * t

    def handle_event(self, event):
        if event.type in (SDL_KEYDOWN, SDL_KEYUP) and event.key in MOVE_KEYS:
            # 보스전이 아닐 때 누른 키도 보스전에 들어가면 바로 움직이도록 항상 기록한다.
            if event.type == SDL_KEYDOWN:
                self.held_move.add(event.key)
            else:
                self.held_move.discard(event.key)
            return
        if self.at_altar():
            # 안전 구역에서는 원석 조작만 받는다.
            self.altar.handle_event(event)
            if event.type == SDL_KEYUP and event.key == SDLK_s:
                self.s_held = False
            return
        if self.bullet_target:
            # 불릿 타임 중 마우스는 동시 클릭 판정에만 쓰고 다른 입력은 받지 않는다 (CT-2, Q3).
            if event.type == SDL_MOUSEBUTTONDOWN:
                if self.is_simultaneous_click(event.button):
                    self.change_state(self.cut_state)
            elif event.type == SDL_KEYUP and event.key == SDLK_s:
                self.s_held = False
            return
        if event.type == SDL_KEYDOWN and event.key == SDLK_w:
            self.jump_buffer = config.INPUT_BUFFER
        elif event.type == SDL_KEYDOWN and event.key == SDLK_s:
            self.s_held = True
            self.slide_buffer = config.INPUT_BUFFER
        elif event.type == SDL_KEYUP and event.key == SDLK_s:
            self.s_held = False
        elif event.type == SDL_MOUSEBUTTONDOWN:
            # 평소 좌클릭은 지연 없이 베기가 나가고, 우클릭까지 이어지면 궁극기가 함께 나간다.
            if event.button == SDL_BUTTON_LEFT:
                self.slash_buffer = config.INPUT_BUFFER
            if self.is_simultaneous_click(event.button):
                self.use_ultimate()
        elif event.type == SDL_KEYDOWN and event.key == SDLK_SPACE:
            self.dash_buffer = config.INPUT_BUFFER
        elif event.type == SDL_KEYDOWN and event.key == SDLK_q:
            self.use_flurry()
        elif event.type == SDL_KEYDOWN and event.key == SDLK_e:
            self.use_pierce()

    def freeze(self, time):
        self.hit_stop = max(self.hit_stop, time)

    def update(self, dt):
        self.animation_time += dt
        self.trail = [(x, y, age + dt) for x, y, age in self.trail if age + dt < config.TRAIL_TIME]
        if self.state is self.dash_state or self.state is self.pierce_state:
            self.trail.append((self.x, self.y, 0))
        self.face_boss()
        self.state.update(dt)
        self.jump_buffer = max(0, self.jump_buffer - dt)
        self.slide_buffer = max(0, self.slide_buffer - dt)
        self.slash_buffer = max(0, self.slash_buffer - dt)
        self.dash_buffer = max(0, self.dash_buffer - dt)
        self.tick_dash_recharge(dt)
        self.triple_timer = max(0, self.triple_timer - dt)
        self.flurry_cooldown = max(0, self.flurry_cooldown - dt)
        self.pierce_cooldown = max(0, self.pierce_cooldown - dt)
        self.ultimate_cooldown = max(0, self.ultimate_cooldown - dt)
        self.cast_timer = max(0, self.cast_timer - dt)
        self.invincible_timer = max(0, self.invincible_timer - dt)

        # 돌진 중에는 상태가 위치를 직접 정하고, 절단 중에는 그 자리에 떠서 힘을 모은다.
        if self.state in (self.dash_state, self.pierce_state, self.cut_state):
            return

        self.x += self.speed() * dt
        self.prev_y = self.y
        if self.hang_timer > 0:
            self.hang_timer -= dt
        else:
            # 등가속도 공식을 그대로 써서 프레임 수와 무관하게 점프 높이가 같게 한다.
            gravity = config.GRAVITY * config.STAGES[self.stage]['gravity']
            if self.vy <= 0:
                gravity *= config.FALL_GRAVITY_RATIO
            self.y += self.vy * dt - gravity * dt * dt / 2
            self.vy -= gravity * dt
            # 중력이 약한 스테이지에서는 2단 점프로 화면 위까지 올라갈 수 있어 천장에서 멈춘다.
            if self.y + config.PLAYER_H > config.SCREEN_H:
                self.y = config.SCREEN_H - config.PLAYER_H
                self.vy = min(self.vy, 0)
        if self.boss:
            self.stay_in_arena(dt)
        elif self.bullet_target:
            # 보스 뒤에서 쓰러뜨려 장벽 코앞에서 불릿 타임이 시작돼도 입력할 시간이 다 남도록 불릿 타임 동안에는 장벽에 닿지 않는다 (CT-6).
            self.x = min(self.x, self.bullet_target.x - config.PLAYER_W / 2 - config.BOSS_CONTACT_GAP)
        # 다음 충돌 처리에서 지면에 닿으면 다시 True가 된다.
        self.on_ground = False

    def face_boss(self):
        # 돌진 중에는 처음 노린 쪽을 그대로 본다.
        if self.boss and self.state not in (self.dash_state, self.pierce_state) and self.x != self.boss.x:
            self.facing = 1 if self.boss.x > self.x else -1

    def stay_in_arena(self, dt):
        """보스전에서 화면과 장벽 안에 머물고 보스 몸통을 뚫지 못한다. 보스 머리보다 높이 뛰면 위로 넘어갈 수 있다."""
        boss = self.boss
        half_w = config.PLAYER_W / 2
        gap = config.BOSS_CONTACT_GAP
        self.x = max(self.camera.base_x + half_w, min(self.x, boss.arena_right() - half_w - gap))
        # 순간이동 중인 마녀는 몸통이 없다.
        if boss.hidden:
            return
        left, bottom, right, top = boss.get_bb()
        reach = half_w + gap
        if self.x + reach <= left or self.x - reach >= right or self.y >= top + gap or self.y + config.PLAYER_H <= bottom - gap:
            return
        side = 1 if self.x > boss.x else -1
        if self.prev_y >= top + gap:
            # 머리 위에 내려앉으면 누르는 쪽으로 걸어가고, 누르지 않으면 가까운 쪽으로 미끄러져 내려온다.
            self.y = top + gap
            self.vy = 0
            if self.speed() == 0:
                self.x += side * config.BOSS_SLIDE_SPEED * dt
        elif self.prev_y + config.PLAYER_H <= bottom - gap:
            # 공중의 마녀 아래에서 뛰어오르면 머리를 부딪힌다.
            self.y = bottom - gap - config.PLAYER_H
            self.vy = min(self.vy, 0)
        else:
            self.x = right + reach if side > 0 else left - reach

    def animation_name(self):
        if self.state is self.jump_state:
            return 'rise' if self.vy > 0 else 'fall'
        if self.state is self.run_state and self.speed() == 0:
            return 'idle'
        return self.state.ANIMATION

    def draw(self, camera):
        dash_sprite = self.sprites['dash']
        for x, y, age in self.trail:
            opacity = config.TRAIL_OPACITY * (1 - age / config.TRAIL_TIME)
            dash_sprite.draw(0, x - camera.x, y + config.SPRITE_CENTER_Y - camera.y, opacity, self.facing < 0)

        name = self.animation_name()
        sprite = self.sprites[name]
        frame = int(self.animation_time * ANIMATION_FPS[name]) % sprite.count
        blink = self.invincible_timer > 0 and int(self.invincible_timer * config.BLINK_HZ) % 2 == 0
        opacity = config.BLINK_OPACITY if blink else 1
        sprite.draw(frame, self.x - camera.x, self.y + config.SPRITE_CENTER_Y - camera.y, opacity, self.facing < 0)

    def get_bb(self):
        half_w = config.PLAYER_W / 2
        h = config.SLIDE_H if self.state is self.slide_state else config.PLAYER_H
        return self.x - half_w, self.y, self.x + half_w, self.y + h

    def is_invincible(self):
        # 불릿 타임에는 장벽 외의 피해를 받지 않는다. 장벽에 닿으면 불릿 타임을 먼저 끝낸다.
        return (self.invincible_timer > 0 or self.bullet_target is not None or self.at_altar()
                or self.state in (self.dash_state, self.pierce_state, self.flurry_state, self.cut_state))

    def take_damage(self):
        if self.is_invincible():
            return
        self.hp -= 1
        self.invincible_timer = config.INVINCIBLE_TIME
        self.combo = 0
        sound.play('hurt')
        self.freeze(config.HURT_HIT_STOP)
        self.camera.shake(config.HURT_SHAKE_TIME, config.HURT_SHAKE_AMP)
        # player:ground 그룹을 먼저 처리하므로 이번 프레임의 착지 여부가 이미 반영되어 있다.
        if self.on_ground:
            self.change_state(self.hit_state)

    def camera_locked(self):
        return self.boss is not None or self.state is self.cut_state

    def speed(self):
        if self.state is self.cut_state:
            return 0
        if self.boss:
            if self.state is self.hit_state or self.state is self.dive_state:
                return 0
            return sum(MOVE_KEYS[key] for key in self.held_move) * config.BOSS_FIGHT_MOVE_SPEED
        run_speed = config.SCROLL_SPEED * config.STAGES[self.stage]['speed']
        return run_speed * self.altar.speed_ratio() if self.altar else run_speed

    def play_hit_feedback(self, monster, by_dash, perfect=False):
        y = monster.dash_y() + config.PLAYER_H / 2
        flip = self.facing < 0
        if perfect:
            self.freeze(config.PERFECT_HIT_STOP)
            self.camera.shake(config.PERFECT_SHAKE_TIME, config.PERFECT_SHAKE_AMP)
            # 멈춤 동안에는 효과 레이어도 멈추므로 번쩍임이 멈춘 화면 위에 그대로 남았다가 사라진다.
            game_world.add_object(Flash(config.PERFECT_FLASH_OPACITY, config.PERFECT_FLASH_TIME), game_world.LAYER_EFFECT)
            effect = Effect('crit-hit', monster.dash_x(), y, speed=DASH_KILL_FX_SPEED, scale=config.PERFECT_FX_SCALE, flip=flip)
        elif by_dash:
            self.freeze(config.DASH_HIT_STOP)
            self.camera.shake(config.DASH_SHAKE_TIME, config.DASH_SHAKE_AMP)
            effect = Effect('crit-hit', monster.dash_x(), y, speed=DASH_KILL_FX_SPEED, flip=flip)
        else:
            hit = load_fx_sheet('sword-slash')[1]['meta']['pixelfx']['act']['hits'][0]
            self.freeze(hit['freeze'] * config.SLASH_HIT_STOP_RATIO)
            self.camera.shake(hit['shake'], hit['amp'] * config.SPRITE_SCALE)
            effect = Effect('hit-spark', monster.dash_x(), y, speed=KILL_FX_SPEED, scale=KILL_FX_SCALE, flip=flip)
        game_world.add_object(effect, game_world.LAYER_EFFECT)

    def gain_gold(self, amount, x, y):
        # 배율로 생기는 소수점이 쌓이도록 따로 누적하고 정수 부분만 골드로 옮긴다.
        self.gold_fraction += amount * (1 + record.stat('gold_gain'))
        gained = int(self.gold_fraction)
        self.gold_fraction -= gained
        record.data['gold'] += gained
        self.run_gold += gained
        for i in range(min(gained, config.COIN_MAX)):
            game_world.add_object(Coin(x, y, self, i == 0), game_world.LAYER_EFFECT)

    def on_parry(self, x, y):
        sound.play('parry')
        self.gain_gold(config.PARRY_GOLD, x, y)

    def on_kill(self, monster, by_dash=False, bonus=0, perfect=False):
        self.gain_gold(monster.gold(by_dash, bonus), monster.dash_x(), monster.dash_y() + config.PLAYER_H / 2)
        sound.play('kill')
        self.play_hit_feedback(monster, by_dash, perfect)
        self.kills += 1
        self.combo += 1
        if self.combo % config.COMBO_HEAL == 0 and self.hp < self.max_hp:
            sound.play('heal')
            self.hp += 1

    def enter_stage(self, stage):
        sound.play('gate')
        sound.play_music(stage)
        self.stage = stage
        record.data['best_stage'] = max(record.data['best_stage'], stage + 1)
        self.invincible_timer = max(self.invincible_timer, config.STAGE_INVINCIBLE_TIME)

    def handle_collision(self, group, other):
        if group == 'player:ground':
            if self.vy <= 0 and self.prev_y >= other.top:
                self.y = other.top
                self.vy = 0
                self.on_ground = True
        elif group == 'player:gate':
            if other.stage > self.stage:
                self.enter_stage(other.stage)
        elif group == 'player:bullet':
            # 피해를 주면 곧바로 무적이 되므로 탄 쪽에서 무적을 확인하면 맞은 탄이 사라지지 않는다.
            if not self.is_invincible():
                self.take_damage()
                game_world.remove_object(other)
        elif group == 'player:wall':
            # 입력하지 못한 채 닿으면 절단 기회는 끝난다. 무적이면 HP는 그대로이고 장벽만 부서진다 (Q4).
            if self.bullet_target:
                self.end_bullet_time()
            self.take_damage()
        else:
            self.take_damage()
