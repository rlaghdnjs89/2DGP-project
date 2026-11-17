import math
import random

import config
import game_world
import sound
from sprite import Effect, OneShot, Strip, get_image

BROOM_FRAME_W = 128
BROOM_FPS = 8
BROOM_START_X = config.SCREEN_W + BROOM_FRAME_W
SHOT_IMAGE = 'assets/monster/bullet_black.png'
SHOT_FRAME_W = 16
ORB_IMAGE = 'assets/monster/rift_orb.png'
ORB_FRAME_W = 24
SHOT_FPS = 12
SPARK_IMAGE = 'assets/monster/bullet_spark.png'
SPARK_FRAME_W = 24
REFLECTED_IMAGE = 'assets/monster/bullet_reflected.png'
PARRY_FX_SCALE = 1
BURST_FX_SPEED = 2
DEATH_IMAGE = 'assets/monster/broom_death.png'
DEATH_FPS = 8
HIT_FX_SPEED = 2
STUN_IMAGE = 'assets/monster/stun_stars.png'
STUN_FRAME_W = 56
STUN_FPS = 10
# 마녀 중심에서 기절 별까지의 높이. 왕관 바로 위다.
STUN_Y = 104
METEOR_IMAGE = 'assets/monster/meteor.png'
METEOR_FRAME_W = 56
# 운석 그림에서 바위 중심은 그림 중심보다 이만큼 앞(오른쪽)에 있다.
METEOR_ROCK_X = 12
METEOR_WARNING_IMAGE = 'assets/ui/warning.png'
BOLT_IMAGE = 'assets/monster/bolt.png'
BOLT_FRAME_W = 32
BOLT_FPS = 14
SHOCK_IMAGE = 'assets/monster/shock.png'
# 전기장 안쪽에 이 간격으로 흐린 번개 줄을 그린다.
PRESS_LINE_GAP = 70
PRESS_LINE_OPACITY = 0.45
WAVES = ('swarm', 'fences', 'press')
SHOTS = ('fan', 'aimed', 'scatter')

# 중간 보스전의 탄과 함정은 월드 좌표에 두고, 매 프레임 플레이어가 달리는 만큼 함께 밀어 화면에 붙어 있게 한다.


def draw_bolt(camera, x0, y0, x1, y1, time, opacity=1):
    """(x0, y0)에서 (x1, y1)까지 번개 토막을 이어 그린다."""
    image = get_image(BOLT_IMAGE)
    scale = config.SPRITE_SCALE
    length = math.hypot(x1 - x0, y1 - y0)
    angle = math.atan2(y1 - y0, x1 - x0)
    count = max(1, round(length / (BOLT_FRAME_W * scale)))
    frames = image.w // BOLT_FRAME_W
    frame = int(time * BOLT_FPS)
    image.opacify(opacity)
    for i in range(count):
        t = (i + 0.5) / count
        # 이웃한 토막이 같은 모양으로 늘어서지 않게 토막마다 다른 프레임에서 시작한다.
        image.clip_composite_draw((frame + i * 3) % frames * BOLT_FRAME_W, 0, BOLT_FRAME_W, image.h, angle, '',
                                  x0 + (x1 - x0) * t - camera.x, y0 + (y1 - y0) * t - camera.y, length / count, image.h * scale)
    image.opacify(1)


class Shot:
    """(vx, vy)로 나는 탄. 화면 밖으로 나가거나 플레이어에 맞으면 사라진다."""

    def __init__(self, player, x, y, vx, vy, image, frame_w, size):
        self.player = player
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.size = size
        self.time = 0
        self.strip = Strip(image, frame_w)

    def update(self, dt):
        self.time += dt
        self.x += (self.player.speed() + self.vx) * dt
        self.y += self.vy * dt
        screen_x = self.x - self.player.camera.base_x
        if not (-self.size <= screen_x <= config.SCREEN_W + 2 * self.size and config.GROUND_TOP <= self.y <= config.SCREEN_H + self.size):
            game_world.remove_object(self)

    def draw(self, camera):
        self.strip.draw(int(self.time * SHOT_FPS) % self.strip.count, self.x - camera.x, self.y - camera.y)

    def get_bb(self):
        half = self.size / 2
        return self.x - half, self.y - half, self.x + half, self.y + half

    def handle_collision(self, group, other):
        pass


class SparkShot(Shot):
    """반짝이는 탄. 베면 마녀 쪽으로 튕겨 나가고, 튕겨 나간 탄이 못 튕기는 탄에 닿으면 터져 주변의 못 튕기는 탄까지 지운다."""

    def __init__(self, witch, x, y, vx, vy):
        super().__init__(witch.player, x, y, vx, vy, SPARK_IMAGE, SPARK_FRAME_W, config.BULLET_SIZE)
        self.witch = witch
        self.reflected = False

    def aim_at_witch(self):
        angle = math.atan2(self.witch.y - self.y, self.witch.x - self.x)
        self.vx = math.cos(angle) * config.REFLECTED_SPEED
        self.vy = math.sin(angle) * config.REFLECTED_SPEED

    def update(self, dt):
        # 반격 단계에서는 위아래로 떠다니는 마녀를 놓치지 않게 매 프레임 마녀를 향한다.
        if self.reflected and self.witch.state == 'counter':
            self.aim_at_witch()
        super().update(dt)

    def reflect(self):
        self.reflected = True
        self.aim_at_witch()
        self.strip = Strip(REFLECTED_IMAGE, SHOT_FRAME_W)
        game_world.remove_collision('player:bullet', self)
        game_world.remove_collision('sword:bullet', self)
        game_world.add_collision_pair('reflected:shot', self, None)
        game_world.add_collision_pair('reflected:witch', self, None)
        self.player.on_parry(self.x, self.y)
        game_world.add_object(Effect('parry', self.x, self.y, scale=PARRY_FX_SCALE), game_world.LAYER_EFFECT)

    def burst(self):
        reflected, shots = game_world.collision_pairs['reflected:shot']
        # 한 프레임에 여러 탄과 겹쳐도 한 번만 터진다.
        if self not in reflected:
            return
        game_world.remove_object(self)

        def distance(shot):
            return math.hypot(shot.x - self.x, shot.y - self.y)

        near = sorted((shot for shot in shots if distance(shot) <= config.SPARK_BURST_RADIUS), key=distance)
        for shot in near[:config.SPARK_BURST_MAX]:
            game_world.remove_object(shot)
            game_world.add_object(Effect('parry', shot.x, shot.y, scale=PARRY_FX_SCALE), game_world.LAYER_EFFECT)
        sound.play('kill')
        self.player.camera.shake(config.BOSS_BLOCK_SHAKE_TIME, config.BOSS_BLOCK_SHAKE_AMP)
        game_world.add_object(Effect('plasma-explosion', self.x, self.y, speed=BURST_FX_SPEED), game_world.LAYER_EFFECT)

    def handle_collision(self, group, other):
        if group == 'sword:bullet':
            self.reflect()
        elif group == 'reflected:shot':
            self.burst()


class Meteor(Shot):
    """화면 위에서 플레이어가 있던 자리를 겨눠 곧게 떨어지는 운석. 떨어지기 전에 지나갈 길이 깜빡인다. 벨 수 없다."""

    def __init__(self, player, x, y, angle):
        speed = config.METEOR_SPEED
        super().__init__(player, x, y, math.cos(angle) * speed, math.sin(angle) * speed, METEOR_IMAGE, METEOR_FRAME_W, config.METEOR_SIZE)
        self.angle = angle
        self.warning = config.METEOR_WARNING

    def update(self, dt):
        if self.warning > 0:
            self.warning -= dt
            self.x += self.player.speed() * dt
            if self.warning <= 0:
                sound.play('flame')
            return
        super().update(dt)
        if self.y - self.size / 2 <= config.GROUND_TOP:
            sound.play('rock')
            game_world.remove_object(self)
            game_world.add_object(Effect('heavy-landing', self.x, config.GROUND_TOP), game_world.LAYER_EFFECT)

    def draw(self, camera):
        angle = self.angle
        if self.warning > 0:
            # 땅에 닿을 때까지의 길을 운석 폭으로 칠한다.
            length = (self.y - config.GROUND_TOP) / -math.sin(angle)
            image = get_image(METEOR_WARNING_IMAGE)
            image.opacify(0.5 + 0.5 * math.sin(self.warning * config.METEOR_WARNING_BLINK))
            image.composite_draw(angle, '', self.x + math.cos(angle) * length / 2 - camera.x, self.y + math.sin(angle) * length / 2 - camera.y,
                                 length, self.size)
            image.opacify(1)
            return
        image = self.strip.image
        w, h = METEOR_FRAME_W, image.h
        scale = config.SPRITE_SCALE
        frame = int(self.time * SHOT_FPS) % self.strip.count
        # 바위 중심이 판정 가운데에 오도록 그림을 날아온 쪽으로 물린다.
        back = METEOR_ROCK_X * scale
        image.clip_composite_draw(frame * w, 0, w, h, angle, '', self.x - math.cos(angle) * back - camera.x,
                                  self.y - math.sin(angle) * back - camera.y, w * scale, h * scale)


class Fence:
    """오른쪽에서 밀려오는 세로 전기 장벽의 한 토막. 틈의 위아래에 하나씩 놓는다."""

    def __init__(self, player, x, bottom, top, speed):
        self.player = player
        self.x = x
        self.bottom = bottom
        self.top = top
        self.speed = speed
        self.time = 0

    def update(self, dt):
        self.time += dt
        self.x += (self.player.speed() - self.speed) * dt
        if self.x - self.player.camera.base_x < -config.FENCE_W:
            game_world.remove_object(self)

    def draw(self, camera):
        for dx in (-config.FENCE_W / 4, config.FENCE_W / 4):
            draw_bolt(camera, self.x + dx, self.bottom, self.x + dx, self.top, self.time + dx)

    def get_bb(self):
        half_w = config.FENCE_W / 2
        return self.x - half_w, self.bottom, self.x + half_w, self.top

    def handle_collision(self, group, other):
        pass


class Press:
    """화면 위(side 1)나 아래(side -1)에서 밀려 들어와 depth만큼 덮었다가 물러나는 전기장."""

    def __init__(self, player, side, depth):
        self.player = player
        self.side = side
        self.depth = depth
        self.time = 0

    def reach(self):
        time = self.time - config.PRESS_WARNING
        stay = config.PRESS_IN_TIME + config.PRESS_HOLD_TIME
        if time < config.PRESS_IN_TIME:
            return self.depth * max(0, time) / config.PRESS_IN_TIME
        if time < stay:
            return self.depth
        return self.depth * (1 - (time - stay) / config.PRESS_OUT_TIME)

    def edge(self, reach):
        return config.SCREEN_H - reach if self.side > 0 else config.GROUND_TOP + reach

    def update(self, dt):
        self.time += dt
        if self.time >= config.PRESS_WARNING + config.PRESS_IN_TIME + config.PRESS_HOLD_TIME + config.PRESS_OUT_TIME:
            game_world.remove_object(self)

    def draw_field(self, camera, reach, opacity):
        image = get_image(SHOCK_IMAGE)
        image.opacify(opacity)
        image.draw_to_origin(0, min(self.edge(0), self.edge(reach)) - camera.y, config.SCREEN_W, reach)
        image.opacify(1)

    def draw(self, camera):
        if self.time < config.PRESS_WARNING:
            blink = 0.5 + 0.5 * math.sin(self.time * config.PRESS_WARNING_BLINK)
            self.draw_field(camera, self.depth, blink)
            y = self.edge(self.depth)
            draw_bolt(camera, camera.x, y, camera.x + config.SCREEN_W, y, self.time, config.PRESS_WARNING_OPACITY)
            return
        reach = self.reach()
        edge = self.edge(reach)
        self.draw_field(camera, reach, 1)
        for i in range(int(reach // PRESS_LINE_GAP) + 1):
            y = edge + self.side * i * PRESS_LINE_GAP
            draw_bolt(camera, camera.x, y, camera.x + config.SCREEN_W, y, self.time + i, 1 if i == 0 else PRESS_LINE_OPACITY)

    def get_bb(self):
        # 가로로는 화면 전체를 덮는다.
        left = self.player.camera.base_x - config.SCREEN_W
        right = left + 3 * config.SCREEN_W
        edge = self.edge(self.reach())
        return (left, edge, right, config.SCREEN_H) if self.side > 0 else (left, config.GROUND_TOP, right, edge)

    def handle_collision(self, group, other):
        pass


class BroomWitch:
    """스테이지 2의 중간 보스. 빗자루를 타고 플레이어 앞을 날며 탄을 쏘고, 파편 무리와 전기 함정을 무작위 순서로 불러낸다.
    버틸 시간이 다 지나면 반격 단계에서 운석을 떨어뜨리며 반짝이는 탄만 쏜다. 튕겨 낸 탄에 BROOM_STUN_HITS번 맞으면 기절해 불릿 타임이 열리고,
    그동안 좌+우 동시 클릭으로 벨 수 있다."""
    NAME = '빗자루 마녀'

    def __init__(self, start_x, player):
        self.player = player
        self.start_x = start_x
        self.state = 'wait'
        self.time = 0
        self.timer = 0
        self.remain = config.MIDBOSS_TIME
        self.hits = 0
        self.flash = 0
        self.stun_time = 0
        self.meteor_timer = 0
        # 마녀는 화면의 같은 자리에 떠 있으므로 화면 좌표로 둔다.
        self.screen_x = BROOM_START_X
        self.y = config.BROOM_HOVER_Y
        self.hazards = []
        self.wave = None
        self.wave_timer = config.MIDBOSS_FIRST_WAVE
        self.shot_timer = config.BROOM_SHOT_INTERVAL[0][1]
        self.orb_time = 0
        self.orb_timer = 0
        self.orb_interval = 0
        self.orb_range = (0, 0)
        self.orb_y = 0
        self.sprites = {name: Strip(f'assets/monster/broom_{name}.png', BROOM_FRAME_W) for name in ('fly', 'cast')}
        self.flash_sprites = {name: Strip(f'assets/monster/broom_{name}_flash.png', BROOM_FRAME_W) for name in ('fly', 'cast')}
        self.stars = Strip(STUN_IMAGE, STUN_FRAME_W)

    def rage(self):
        """공격이 거세지는 후반이면 1, 아니면 0. (전반, 후반) 값을 고르는 데 쓴다."""
        return int(self.remain <= config.MIDBOSS_TIME * config.MIDBOSS_RAGE_RATIO)

    def left(self):
        return self.player.camera.base_x

    @property
    def x(self):
        return self.left() + self.screen_x

    def update(self, dt):
        self.flash = max(0, self.flash - dt)
        if self.state == 'finish':
            # 기절한 동안은 떠다니지 않고 날던 모습 그대로 굳는다. 머리 위의 별만 돈다.
            self.stun_time += dt
            return
        self.time += dt
        if self.state == 'wait':
            # 앞 청크의 낭떠러지와 사역마가 화면 뒤로 다 빠진 뒤에 시작한다.
            if self.left() >= self.start_x:
                self.player.enter_midboss(self)
                self.state = 'intro'
                self.timer = config.MIDBOSS_INTRO_TIME
            return
        self.y = config.BROOM_HOVER_Y + config.BROOM_HOVER_AMP * math.sin(self.time * config.BROOM_HOVER_SPEED)
        if self.state == 'fight':
            self.fight(dt)
        elif self.state == 'counter':
            self.counter(dt)
        elif self.state == 'intro':
            self.timer -= dt
            t = max(0, self.timer / config.MIDBOSS_INTRO_TIME)
            self.screen_x = config.BROOM_SCREEN_X + (BROOM_START_X - config.BROOM_SCREEN_X) * t * t
            if self.timer <= 0:
                self.state = 'fight'
        elif self.state == 'leave':
            self.timer -= dt
            t = 1 - max(0, self.timer / config.MIDBOSS_LEAVE_TIME)
            self.screen_x = config.BROOM_SCREEN_X + (BROOM_START_X - config.BROOM_SCREEN_X) * t * t
            if self.timer <= 0:
                self.player.end_midboss()
                game_world.remove_object(self)

    def fight(self, dt):
        self.remain -= dt
        if self.remain <= 0:
            self.start_counter()
            return
        self.shot_timer -= dt
        if self.shot_timer <= 0:
            self.fire()
            self.shot_timer = random.uniform(*config.BROOM_SHOT_INTERVAL[self.rage()])
        self.wave_timer -= dt
        if self.wave_timer <= 0:
            self.start_wave()
        if self.orb_time > 0:
            self.orb_time -= dt
            self.orb_timer -= dt
            while self.orb_timer <= 0:
                self.orb_timer += self.orb_interval
                self.send_orb()

    def clear_hazards(self):
        for hazard in self.hazards:
            game_world.remove_object(hazard)
        self.hazards.clear()

    def start_counter(self):
        """탄막과 함정을 걷고 반격 단계를 연다. 반격을 알리는 COUNTER_START_DELAY초 동안은 공격하지 않는다."""
        self.clear_hazards()
        self.remain = 0
        self.state = 'counter'
        self.timer = config.COUNTER_START_DELAY
        self.shot_timer = config.COUNTER_START_DELAY
        self.meteor_timer = config.COUNTER_START_DELAY
        game_world.add_collision_pair('reflected:witch', None, self)

    def counter(self, dt):
        self.timer -= dt
        self.shot_timer -= dt
        if self.shot_timer <= 0:
            sound.play('fire')
            x, y = self.hand()
            self.add_shot(x, y, self.aim_at_player(x, y), config.BROOM_SHOT_SPEED, True)
            self.shot_timer = random.uniform(*config.COUNTER_SHOT_INTERVAL)
        self.meteor_timer -= dt
        if self.meteor_timer <= 0:
            self.drop_meteor()
            self.meteor_timer = random.uniform(*config.METEOR_INTERVAL)

    def drop_meteor(self):
        x = self.left() + random.uniform(0, config.SCREEN_W)
        y = config.SCREEN_H + config.METEOR_SIZE / 2
        self.add_hazard(Meteor(self.player, x, y, self.aim_at_player(x, y)), 'player:bullet')

    def get_bb(self):
        half_w = config.BROOM_HIT_W / 2
        half_h = config.BROOM_HIT_H / 2
        return self.x - half_w, self.y - half_h, self.x + half_w, self.y + half_h

    def handle_collision(self, group, other):
        # 반격 단계에서 튕겨 낸 반짝이는 탄에 맞았다.
        game_world.remove_object(other)
        self.hits += 1
        self.flash = config.BOSS_FLASH_TIME
        sound.play('boss_hit')
        self.player.camera.shake(config.BOSS_BLOCK_SHAKE_TIME, config.BOSS_BLOCK_SHAKE_AMP)
        game_world.add_object(Effect('crit-hit', other.x, other.y, speed=HIT_FX_SPEED), game_world.LAYER_EFFECT)
        if self.hits >= config.BROOM_STUN_HITS:
            game_world.remove_collision('reflected:witch', self)
            self.open_finish()

    def open_finish(self):
        """기절한 마녀를 두고 운석과 탄을 걷은 뒤 불릿 타임을 연다. 좌+우 동시 클릭이 들어오면 on_cut, 놓치면 on_bullet_timeout으로 이어진다."""
        self.clear_hazards()
        self.state = 'finish'
        self.player.enter_bullet_time(self)

    def on_bullet_timeout(self):
        sound.play('teleport')
        self.state = 'leave'
        self.timer = config.MIDBOSS_LEAVE_TIME

    def cut_center(self):
        return self.x, self.y

    def on_cut(self):
        x, y = self.cut_center()
        player = self.player
        player.end_midboss()
        # 모은 힘으로 마녀를 꿰뚫고 지나가 그 뒤에 선다.
        player.streak_to(x + config.BROOM_CUT_PASS, y - config.PLAYER_H / 2)
        game_world.remove_object(self)
        # 절단의 폭발이 마녀 자리에서 터지므로, 흩어지는 모습이 묻히지 않게 이펙트보다 위에 그린다.
        game_world.add_object(OneShot(Strip(DEATH_IMAGE, BROOM_FRAME_W), DEATH_FPS, x, y), game_world.LAYER_WARNING)

    def add_hazard(self, hazard, group):
        self.hazards.append(hazard)
        game_world.add_object(hazard, game_world.LAYER_EFFECT)
        game_world.add_collision_pair(group, None, hazard)

    def add_unparryable(self, shot):
        self.add_hazard(shot, 'player:bullet')
        game_world.add_collision_pair('reflected:shot', None, shot)

    def add_shot(self, x, y, angle, speed, spark=False):
        vx, vy = math.cos(angle) * speed, math.sin(angle) * speed
        if spark:
            shot = SparkShot(self, x, y, vx, vy)
            self.add_hazard(shot, 'player:bullet')
            game_world.add_collision_pair('sword:bullet', None, shot)
        else:
            self.add_unparryable(Shot(self.player, x, y, vx, vy, SHOT_IMAGE, SHOT_FRAME_W, config.BULLET_SIZE))

    def hand(self):
        return self.x + config.BROOM_MUZZLE_X, self.y + config.BROOM_MUZZLE_Y

    def aim_at_player(self, x, y):
        """(x, y)에서 플레이어 몸 가운데를 향하는 각도."""
        left, bottom, right, top = self.player.get_bb()
        return math.atan2((bottom + top) / 2 - y, (left + right) / 2 - x)

    def fire(self):
        sound.play('fire')
        x, y = self.hand()
        aim = self.aim_at_player(x, y)
        kind = random.choice(SHOTS)
        # 어느 묶음이든 반짝이는 탄이 하나 섞인다.
        if kind == 'fan':
            count = config.BROOM_FAN_COUNT[self.rage()]
            # 플레이어를 겨눈 가운데 탄이 반짝인다.
            for i in range(count):
                self.add_shot(x, y, aim + (i - count // 2) * config.BROOM_FAN_SPREAD, config.BROOM_SHOT_SPEED, i == count // 2)
        elif kind == 'aimed':
            # 맨 앞에서 오는 가장 빠른 탄이 반짝여, 튕겨 내면 뒤따르는 탄과 부딪힌다.
            for speed in config.BROOM_AIMED_SPEEDS:
                self.add_shot(x, y, aim, speed, speed == max(config.BROOM_AIMED_SPEEDS))
        else:
            for i in range(config.BROOM_SCATTER_COUNT):
                angle = math.pi + random.uniform(-config.BROOM_SCATTER_ANGLE, config.BROOM_SCATTER_ANGLE)
                self.add_shot(x, y, angle, random.uniform(*config.BROOM_SCATTER_SPEED), i == 0)

    def start_orbs(self, time, interval, low, high):
        self.orb_time = time
        self.orb_interval = interval
        self.orb_timer = 0
        self.orb_range = (low, high)
        self.orb_y = random.uniform(low, high)

    def send_orb(self):
        low, high = self.orb_range
        gap = min(config.ORB_MIN_GAP, (high - low) / 3)
        y = random.uniform(low, high)
        while abs(y - self.orb_y) < gap:
            y = random.uniform(low, high)
        self.orb_y = y
        orb = Shot(self.player, self.left() + config.SCREEN_W + config.ORB_SIZE, y, -random.uniform(*config.ORB_SPEED),
                   random.uniform(-config.ORB_DRIFT, config.ORB_DRIFT), ORB_IMAGE, ORB_FRAME_W, config.ORB_SIZE)
        self.add_unparryable(orb)

    def start_wave(self):
        self.wave = random.choice([wave for wave in WAVES if wave != self.wave])
        if self.wave == 'swarm':
            length = self.start_swarm()
        elif self.wave == 'fences':
            length = self.start_fences()
        else:
            length = self.start_press()
        self.wave_timer = length + config.MIDBOSS_WAVE_REST[self.rage()]

    def start_swarm(self):
        half = config.ORB_SIZE / 2
        self.start_orbs(config.SWARM_TIME, config.SWARM_INTERVAL[self.rage()], config.GROUND_TOP + half, config.SCREEN_H - half)
        return config.SWARM_TIME + config.SWARM_CLEAR_TIME

    def start_fences(self):
        sound.play('zap')
        rage = self.rage()
        speed = config.FENCE_SPEED[rage]
        half_gap = config.FENCE_GAP / 2
        low, high = config.GROUND_TOP + half_gap, config.SCREEN_H - half_gap
        gap_y = random.uniform(low, high)
        x = self.left() + config.SCREEN_W + config.FENCE_W
        for _ in range(config.FENCE_COUNT[rage]):
            self.add_hazard(Fence(self.player, x, config.GROUND_TOP, gap_y - half_gap, speed), 'player:strike')
            self.add_hazard(Fence(self.player, x, gap_y + half_gap, config.SCREEN_H, speed), 'player:strike')
            x += config.FENCE_SPACING[rage]
            shift = random.uniform(*config.FENCE_SHIFT) * random.choice((-1, 1))
            # 화면 밖으로 나가는 쪽이면 반대쪽으로 옮기고, 그래도 넘치면 끝에 붙인다.
            if not low <= gap_y + shift <= high:
                shift = -shift
            gap_y = max(low, min(gap_y + shift, high))
        # 마지막 장벽이 화면을 다 지나갈 때까지다.
        return (x - self.left()) / speed

    def start_press(self):
        sound.play('zap')
        half = config.PRESS_CORRIDOR[self.rage()] / 2
        center = random.uniform(config.GROUND_TOP + half, config.SCREEN_H - half)
        for side, depth in ((1, config.SCREEN_H - center - half), (-1, center - half - config.GROUND_TOP)):
            if depth >= config.PRESS_MIN_DEPTH:
                self.add_hazard(Press(self.player, side, depth), 'player:strike')
        stay = config.PRESS_WARNING + config.PRESS_IN_TIME + config.PRESS_HOLD_TIME
        orb_half = config.ORB_SIZE / 2
        self.start_orbs(stay, config.PRESS_ORB_INTERVAL, center - half + orb_half, center + half - orb_half)
        return stay + config.PRESS_OUT_TIME

    def draw(self, camera):
        if self.state == 'wait':
            return
        casting = self.state in ('fight', 'counter') and self.shot_timer <= config.BROOM_CAST_TIME
        sprite = (self.flash_sprites if self.flash > 0 else self.sprites)['cast' if casting else 'fly']
        # 화면 좌표에도 카메라 흔들림은 그대로 싣는다.
        x = self.screen_x + camera.base_x - camera.x
        y = self.y - camera.y
        sprite.draw(int(self.time * BROOM_FPS) % sprite.count, x, y)
        if self.state == 'finish':
            self.stars.draw(int(self.stun_time * STUN_FPS) % self.stars.count, x, y + STUN_Y)
