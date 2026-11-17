import math
import random

import config
import game_world
import sound
from sprite import Strip, get_image

BROOM_FRAME_W = 128
BROOM_FPS = 8
BROOM_START_X = config.SCREEN_W + BROOM_FRAME_W
SHOT_IMAGE = 'assets/monster/bullet_black.png'
SHOT_FRAME_W = 16
ORB_IMAGE = 'assets/monster/rift_orb.png'
ORB_FRAME_W = 24
SHOT_FPS = 12
BOLT_IMAGE = 'assets/monster/bolt.png'
BOLT_FRAME_W = 32
BOLT_FPS = 14
SHOCK_IMAGE = 'assets/monster/shock.png'
# 전기장 안쪽에 이 간격으로 흐린 번개 줄을 그린다.
PRESS_LINE_GAP = 70
PRESS_LINE_OPACITY = 0.45
# 팔에 닿았는지 이 간격으로 점을 찍어 확인한다. 비행 판정의 폭보다 촘촘해 빠뜨리지 않는다.
ROTOR_CHECK_STEP = 12
WAVES = ('swarm', 'rotor', 'fences', 'press')
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


class Rotor:
    """한 점을 축으로 도는 전기 팔. 사각 판정으로는 나타낼 수 없어 닿았는지를 직접 확인한다."""

    def __init__(self, player, x, y, spin):
        self.player = player
        self.x = x
        self.y = y
        self.spin = spin
        self.angle = random.uniform(0, math.pi * 2)
        self.time = 0
        self.live = False
        self.hub = Strip(ORB_IMAGE, ORB_FRAME_W)

    def arms(self):
        for i in range(config.ROTOR_ARMS):
            angle = self.angle + i * math.pi * 2 / config.ROTOR_ARMS
            yield math.cos(angle), math.sin(angle)

    def update(self, dt):
        self.time += dt
        self.x += self.player.speed() * dt
        self.angle += self.spin * dt
        if self.time >= config.ROTOR_WARNING + config.ROTOR_TIME:
            game_world.remove_object(self)
        elif self.time >= config.ROTOR_WARNING:
            if not self.live:
                self.live = True
                sound.play('zap')
            if self.touches(self.player.get_bb()):
                self.player.take_damage()

    def touches(self, bb):
        left, bottom, right, top = bb
        half = config.ROTOR_THICKNESS / 2
        for dx, dy in self.arms():
            for r in range(0, config.ROTOR_LENGTH, ROTOR_CHECK_STEP):
                if left - half <= self.x + dx * r <= right + half and bottom - half <= self.y + dy * r <= top + half:
                    return True
        return False

    def draw(self, camera):
        opacity = 1 if self.live else config.ROTOR_WARNING_OPACITY
        for dx, dy in self.arms():
            draw_bolt(camera, self.x, self.y, self.x + dx * config.ROTOR_LENGTH, self.y + dy * config.ROTOR_LENGTH, self.time, opacity)
        self.hub.draw(int(self.time * SHOT_FPS) % self.hub.count, self.x - camera.x, self.y - camera.y, opacity)


class BroomWitch:
    """스테이지 2의 중간 보스. 빗자루를 타고 플레이어 앞을 날며 탄을 쏘고, 파편 무리와 전기 함정을 무작위 순서로 불러낸다."""
    NAME = '빗자루 마녀'

    def __init__(self, start_x, player):
        self.player = player
        self.start_x = start_x
        self.state = 'wait'
        self.time = 0
        self.timer = 0
        self.remain = config.MIDBOSS_TIME
        # 마녀는 맞지 않으므로 화면 좌표로 둔다.
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

    def rage(self):
        """공격이 거세지는 후반이면 1, 아니면 0. (전반, 후반) 값을 고르는 데 쓴다."""
        return int(self.remain <= config.MIDBOSS_TIME * config.MIDBOSS_RAGE_RATIO)

    def left(self):
        return self.player.camera.base_x

    def update(self, dt):
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
            return
        self.timer -= dt
        if self.state == 'intro':
            t = max(0, self.timer / config.MIDBOSS_INTRO_TIME)
            self.screen_x = config.BROOM_SCREEN_X + (BROOM_START_X - config.BROOM_SCREEN_X) * t * t
            if self.timer <= 0:
                self.state = 'fight'
        else:
            t = 1 - max(0, self.timer / config.MIDBOSS_LEAVE_TIME)
            self.screen_x = config.BROOM_SCREEN_X + (BROOM_START_X - config.BROOM_SCREEN_X) * t * t
            if self.timer <= 0:
                self.player.end_midboss()
                game_world.remove_object(self)

    def fight(self, dt):
        self.remain -= dt
        if self.remain <= 0:
            self.leave()
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

    def leave(self):
        sound.play('teleport')
        for hazard in self.hazards:
            game_world.remove_object(hazard)
        self.remain = 0
        self.state = 'leave'
        self.timer = config.MIDBOSS_LEAVE_TIME

    def add_hazard(self, hazard, group):
        self.hazards.append(hazard)
        game_world.add_object(hazard, game_world.LAYER_EFFECT)
        if group:
            game_world.add_collision_pair(group, None, hazard)

    def add_shot(self, x, y, angle, speed):
        shot = Shot(self.player, x, y, math.cos(angle) * speed, math.sin(angle) * speed, SHOT_IMAGE, SHOT_FRAME_W, config.BULLET_SIZE)
        self.add_hazard(shot, 'player:bullet')

    def fire(self):
        sound.play('fire')
        x = self.left() + self.screen_x + config.BROOM_MUZZLE_X
        y = self.y + config.BROOM_MUZZLE_Y
        left, bottom, right, top = self.player.get_bb()
        aim = math.atan2((bottom + top) / 2 - y, (left + right) / 2 - x)
        kind = random.choice(SHOTS)
        if kind == 'fan':
            count = config.BROOM_FAN_COUNT[self.rage()]
            for i in range(count):
                self.add_shot(x, y, aim + (i - count // 2) * config.BROOM_FAN_SPREAD, config.BROOM_SHOT_SPEED)
        elif kind == 'aimed':
            for speed in config.BROOM_AIMED_SPEEDS:
                self.add_shot(x, y, aim, speed)
        else:
            for _ in range(config.BROOM_SCATTER_COUNT):
                angle = math.pi + random.uniform(-config.BROOM_SCATTER_ANGLE, config.BROOM_SCATTER_ANGLE)
                self.add_shot(x, y, angle, random.uniform(*config.BROOM_SCATTER_SPEED))

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
        self.add_hazard(orb, 'player:bullet')

    def start_wave(self):
        self.wave = random.choice([wave for wave in WAVES if wave != self.wave])
        if self.wave == 'swarm':
            length = self.start_swarm()
        elif self.wave == 'rotor':
            length = self.start_rotor()
        elif self.wave == 'fences':
            length = self.start_fences()
        else:
            length = self.start_press()
        self.wave_timer = length + config.MIDBOSS_WAVE_REST[self.rage()]

    def start_swarm(self):
        half = config.ORB_SIZE / 2
        self.start_orbs(config.SWARM_TIME, config.SWARM_INTERVAL[self.rage()], config.GROUND_TOP + half, config.SCREEN_H - half)
        return config.SWARM_TIME + config.SWARM_CLEAR_TIME

    def start_rotor(self):
        spin = config.ROTOR_SPIN[self.rage()] * random.choice((-1, 1))
        self.add_hazard(Rotor(self.player, self.left() + config.SCREEN_W / 2, config.ROTOR_Y, spin), None)
        return config.ROTOR_WARNING + config.ROTOR_TIME

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
        casting = self.state == 'fight' and self.shot_timer <= config.BROOM_CAST_TIME
        sprite = self.sprites['cast' if casting else 'fly']
        # 화면 좌표에도 카메라 흔들림은 그대로 싣는다.
        sprite.draw(int(self.time * BROOM_FPS) % sprite.count, self.screen_x + camera.base_x - camera.x, self.y - camera.y)
