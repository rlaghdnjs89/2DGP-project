from pico2d import (SDL_BUTTON_LEFT, SDL_BUTTON_RIGHT, SDL_KEYDOWN, SDL_KEYUP, SDL_MOUSEBUTTONDOWN, SDLK_SPACE, SDLK_a,
                    SDLK_d, SDLK_s, SDLK_w, get_time)

import config
import game_world
import sound
from sprite import Effect, Strip, load_fx_sheet
from ui import draw_overlay

FRAME_W = 64
ANIMATION_FPS = {'run': 16, 'idle': 6, 'rise': 8, 'fall': 8, 'slide': 10, 'slash': 16, 'dash': 16, 'hit': 16, 'charge': 10, 'cut': 16}
OTHER_BUTTON = {SDL_BUTTON_LEFT: SDL_BUTTON_RIGHT, SDL_BUTTON_RIGHT: SDL_BUTTON_LEFT}
MOVE_KEYS = {SDLK_a: -1, SDLK_d: 1}
CHARGE_FX = 'charge-up'
IMPLOSION_FX = 'implosion'
BURST_FX = 'plasma-explosion'
# 시트에서 검기가 빠르게 끝나도록 빨리 재생한다.
SLASH_FX_SPEED = 1.6
SLASH_FX_Y = 8
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
        else:
            player.try_attack()


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
        if player.state is self and self.timer >= config.SLASH_TIME:
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


class Layer:
    """이펙트 사이에 끼워 넣는 그리기 호출."""

    def __init__(self, draw):
        self.draw = draw

    def update(self, dt):
        pass


class Cut:
    """차원 절단. 힘을 모은 뒤 터뜨리고, 터진 뒤의 느린 시간은 Player.tick_cut_after가 맡는다."""

    def __init__(self, player):
        self.player = player
        self.timer = 0
        self.wall = None
        self.layers = ()
        self.dim_opacity = 0
        self.ANIMATION = 'charge'
        self.charge_time = load_fx_sheet(CHARGE_FX)[1]['meta']['pixelfx']['act']['hits'][0]['t']

    def enter(self):
        player = self.player
        self.timer = 0
        self.wall = player.bullet_wall
        self.ANIMATION = 'charge'
        player.bullet_wall = None
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
        if self.wall is None:
            return
        self.timer += dt
        power = min(1, self.timer / self.charge_time)
        self.dim_opacity = config.CUT_DIM_OPACITY * power
        # 힘이 찰수록 땅이 크게 울린다.
        self.player.camera.shake(0.05, config.CUT_RUMBLE_AMP * power)
        if self.timer >= self.charge_time:
            for layer in self.layers:
                game_world.remove_object(layer)
            self.player.cut_wall(self.wall)
            self.wall = None
            self.ANIMATION = 'cut'
            self.player.animation_time = 0


class Sword:
    def __init__(self, player):
        self.player = player
        self.timer = config.SWORD_TIME

    def update(self, dt):
        self.timer -= dt
        if self.timer <= 0:
            game_world.remove_object(self)

    def draw(self, camera):
        pass

    def get_bb(self):
        left = self.player.x + config.PLAYER_W / 2
        bottom = self.player.y + (config.PLAYER_H - config.SWORD_H) / 2
        return left, bottom, left + config.SWORD_REACH, bottom + config.SWORD_H

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
        player.x -= config.KNOCKBACK_SPEED * max(0, 1 - self.timer / config.HIT_STUN_TIME) * dt
        if self.timer >= config.HIT_STUN_TIME:
            player.change_state(player.run_state if player.on_ground else player.jump_state)


class Player:
    def __init__(self, camera):
        self.camera = camera
        self.x = config.PLAYER_SCREEN_X
        self.y = config.GROUND_TOP
        self.prev_y = self.y
        self.vy = 0
        self.on_ground = True
        self.air_jumps = config.AIR_JUMPS
        self.jump_buffer = 0
        self.slide_buffer = 0
        self.slash_buffer = 0
        self.dash_buffer = 0
        self.s_held = False
        self.sword = None
        self.dash_charges = config.DASH_MAX_CHARGES
        self.dash_recharge = config.DASH_RECHARGE_TIME
        self.hang_timer = 0
        self.hp = config.HP_MAX
        self.invincible_timer = 0
        self.score = 0
        self.distance_score = 0
        self.kills = 0
        self.combo = 0
        self.stage = 0
        self.boss = None
        self.cleared = False
        self.held_move = set()
        self.bullet_wall = None
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
        if self.dash_buffer > 0 and self.dash_charges > 0:
            target = self.find_dash_target()
            if target:
                self.start_dash(target)
                return True
        if self.slash_buffer > 0 and self.state is not self.slash_state:
            self.start_slash()
            return True
        return False

    def start_slash(self):
        sound.play('slash')
        self.slash_buffer = 0
        self.slash_state.prev_state = self.state
        self.change_state(self.slash_state)
        self.sword = Sword(self)
        game_world.add_object(self.sword, game_world.LAYER_EFFECT)
        game_world.add_object(Effect('sword-slash', 0, SLASH_FX_Y, self, SLASH_FX_SPEED), game_world.LAYER_EFFECT)
        game_world.add_collision_pair('sword:monster', self.sword, None)
        game_world.add_collision_pair('sword:bullet', self.sword, None)

    def find_dash_target(self):
        def dist2(monster):
            return (monster.x - self.x) ** 2 + (monster.dash_y() - self.y) ** 2

        monsters = game_world.collision_pairs['player:monster'][1]
        in_range = [m for m in monsters if m.x > self.x and dist2(m) <= config.DASH_RANGE ** 2]
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

    def finish_dash(self, target):
        target.on_dash_hit()
        if target.AIRBORNE:
            self.hang_timer = config.DASH_HANG_TIME
        self.change_state(self.jump_state)

    def tick_dash_recharge(self, dt):
        if self.dash_charges == config.DASH_MAX_CHARGES:
            self.dash_recharge = config.DASH_RECHARGE_TIME
            return
        self.dash_recharge -= dt
        if self.dash_recharge <= 0:
            self.dash_charges += 1
            self.dash_recharge = config.DASH_RECHARGE_TIME

    def enter_boss_fight(self, boss):
        sound.play('boss_roar')
        self.boss = boss

    def end_boss_fight(self):
        self.boss = None

    def enter_bullet_time(self, wall):
        sound.set_music_volume(config.MUSIC_VOLUME_DUCK)
        self.bullet_wall = wall
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
        self.bullet_wall = None

    def tick_bullet_time(self, real_dt):
        self.bullet_timer -= real_dt
        if self.bullet_timer <= 0:
            self.end_bullet_time()

    def handle_cut_click(self, button):
        if button not in OTHER_BUTTON:
            return
        # 불릿 타임으로 느려져도 판정 시간은 변하지 않도록 실제 시간을 쓴다 (CT-1).
        now = get_time()
        other = OTHER_BUTTON[button]
        if other in self.press_times and now - self.press_times[other] <= config.SIMULTANEOUS_WINDOW:
            self.change_state(self.cut_state)
        else:
            self.press_times[button] = now

    def cut_wall(self, wall):
        sound.play('cut')
        sound.play('cut_boom')
        wall.cut()
        self.add_score(config.CUT_SCORE)
        self.cut_after_timer = config.CUT_AFTER_TIME
        self.camera.shake(config.CUT_SHAKE_TIME, config.CUT_SHAKE_AMP)
        self.freeze(config.CUT_HIT_STOP)
        center_x = self.camera.base_x + config.SCREEN_W / 2
        game_world.add_object(Effect(BURST_FX, wall.x + config.WALL_W / 2, config.SCREEN_H / 2, scale=config.CUT_FX_SCALE), game_world.LAYER_EFFECT)
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
        if self.bullet_wall:
            # 불릿 타임 중 마우스는 동시 클릭 판정에만 쓰고 다른 입력은 받지 않는다 (CT-2, Q3).
            if event.type == SDL_MOUSEBUTTONDOWN:
                self.handle_cut_click(event.button)
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
        elif event.type == SDL_MOUSEBUTTONDOWN and event.button == SDL_BUTTON_LEFT:
            self.slash_buffer = config.INPUT_BUFFER
        elif event.type == SDL_KEYDOWN and event.key == SDLK_SPACE:
            self.dash_buffer = config.INPUT_BUFFER

    def freeze(self, time):
        self.hit_stop = max(self.hit_stop, time)

    def update(self, dt):
        self.animation_time += dt
        self.trail = [(x, y, age + dt) for x, y, age in self.trail if age + dt < config.TRAIL_TIME]
        if self.state is self.dash_state:
            self.trail.append((self.x, self.y, 0))
        self.state.update(dt)
        self.jump_buffer = max(0, self.jump_buffer - dt)
        self.slide_buffer = max(0, self.slide_buffer - dt)
        self.slash_buffer = max(0, self.slash_buffer - dt)
        self.dash_buffer = max(0, self.dash_buffer - dt)
        self.tick_dash_recharge(dt)
        self.invincible_timer = max(0, self.invincible_timer - dt)

        if not self.boss:
            self.distance_score += config.DISTANCE_SCORE_RATE * config.STAGES[self.stage]['speed'] * dt
        # 소수점이 쌓이도록 따로 누적하고 정수 부분만 점수로 옮긴다.
        gained = int(self.distance_score)
        self.distance_score -= gained
        self.add_score(gained)

        # 돌진 중에는 Dash가 위치를 직접 정하고, 절단 중에는 그 자리에 떠서 힘을 모은다.
        if self.state is self.dash_state or self.state is self.cut_state:
            return

        self.x += self.speed() * dt
        if self.boss:
            # 스프라이트가 오른쪽만 보므로 보스를 넘어가지 못하게 한다.
            half_w = config.PLAYER_W / 2
            self.x = max(self.camera.base_x + half_w, min(self.x, self.boss.dash_x()))
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
        # 다음 충돌 처리에서 지면에 닿으면 다시 True가 된다.
        self.on_ground = False

    def animation_name(self):
        if self.state is self.jump_state:
            return 'rise' if self.vy > 0 else 'fall'
        if self.state is self.run_state and self.boss and self.speed() == 0:
            return 'idle'
        return self.state.ANIMATION

    def draw(self, camera):
        dash_sprite = self.sprites['dash']
        for x, y, age in self.trail:
            opacity = config.TRAIL_OPACITY * (1 - age / config.TRAIL_TIME)
            dash_sprite.draw(0, x - camera.x, y + config.SPRITE_CENTER_Y - camera.y, opacity)

        name = self.animation_name()
        sprite = self.sprites[name]
        frame = int(self.animation_time * ANIMATION_FPS[name]) % sprite.count
        blink = self.invincible_timer > 0 and int(self.invincible_timer * config.BLINK_HZ) % 2 == 0
        opacity = config.BLINK_OPACITY if blink else 1
        sprite.draw(frame, self.x - camera.x, self.y + config.SPRITE_CENTER_Y - camera.y, opacity)

    def get_bb(self):
        half_w = config.PLAYER_W / 2
        h = config.SLIDE_H if self.state is self.slide_state else config.PLAYER_H
        return self.x - half_w, self.y, self.x + half_w, self.y + h

    def is_invincible(self):
        # 불릿 타임에는 장벽 외의 피해를 받지 않는다. 장벽에 닿으면 불릿 타임을 먼저 끝낸다.
        return (self.invincible_timer > 0 or self.bullet_wall is not None
                or self.state is self.dash_state or self.state is self.cut_state)

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
            if self.state is self.hit_state:
                return 0
            return sum(MOVE_KEYS[key] for key in self.held_move) * config.BOSS_FIGHT_MOVE_SPEED
        return config.SCROLL_SPEED * config.STAGES[self.stage]['speed']

    def add_score(self, points):
        # 진입 순간 총점이 뛰지 않도록 얻는 시점에 배율을 곱한다 (Q1).
        self.score += points * config.STAGES[self.stage]['score_rate']

    def play_hit_feedback(self, monster, by_dash):
        y = monster.dash_y() + config.PLAYER_H / 2
        if by_dash:
            self.freeze(config.DASH_HIT_STOP)
            self.camera.shake(config.DASH_SHAKE_TIME, config.DASH_SHAKE_AMP)
            effect = Effect('crit-hit', monster.dash_x(), y, speed=DASH_KILL_FX_SPEED)
        else:
            hit = load_fx_sheet('sword-slash')[1]['meta']['pixelfx']['act']['hits'][0]
            self.freeze(hit['freeze'] * config.SLASH_HIT_STOP_RATIO)
            self.camera.shake(hit['shake'], hit['amp'] * config.SPRITE_SCALE)
            effect = Effect('hit-spark', monster.dash_x(), y, speed=KILL_FX_SPEED, scale=KILL_FX_SCALE)
        game_world.add_object(effect, game_world.LAYER_EFFECT)

    def on_parry(self):
        sound.play('parry')
        self.add_score(config.PARRY_SCORE)

    def on_kill(self, monster, by_dash=False, bonus=0):
        self.add_score(monster.SCORE + bonus + (monster.DASH_BONUS if by_dash else 0))
        sound.play('kill')
        self.play_hit_feedback(monster, by_dash)
        self.kills += 1
        self.combo += 1
        if self.combo % config.COMBO_HEAL == 0 and self.hp < config.HP_MAX:
            sound.play('heal')
            self.hp += 1

    def enter_stage(self, stage):
        sound.play('gate')
        sound.play_music(stage)
        self.stage = stage
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
            if self.bullet_wall:
                self.end_bullet_time()
            self.take_damage()
        else:
            self.take_damage()
