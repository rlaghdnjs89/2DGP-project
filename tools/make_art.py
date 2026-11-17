"""게임 그래픽을 코드로 그려 assets/ 아래에 저장한다.

실행: python tools/make_art.py  (Pillow 필요, 게임 실행에는 필요 없다)

캐릭터는 관절 뼈대에 포즈를 주어 그리므로 비율과 팔레트가 모든 프레임에서 같다.
스프라이트는 원본 해상도로 저장하고 게임에서 2배로 그린다. 왼쪽을 보는 몬스터는 처음부터 왼쪽을 보게 저장한다.
"""
import math
import os
import random

from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets')

FRAME = 64
FEET_Y = 60
CENTER_X = 32


def hex_color(text):
    return tuple(int(text[i:i + 2], 16) for i in (0, 2, 4)) + (255,)


# 공통 그리기 --------------------------------------------------------------

def new_frame(w=FRAME, h=FRAME):
    return Image.new('RGBA', (w, h), (0, 0, 0, 0))


def disc(img, cx, cy, r, color):
    px = img.load()
    for y in range(max(0, int(cy - r - 1)), min(img.height, int(cy + r + 2))):
        for x in range(max(0, int(cx - r - 1)), min(img.width, int(cx + r + 2))):
            if (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= r * r:
                px[x, y] = color


def capsule(img, p0, p1, r0, r1, color):
    length = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
    steps = max(1, int(length * 2))
    for i in range(steps + 1):
        t = i / steps
        disc(img, p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t, r0 + (r1 - r0) * t, color)


def polygon(img, points, color):
    px = img.load()
    min_y = max(0, int(min(p[1] for p in points)))
    max_y = min(img.height - 1, int(max(p[1] for p in points)) + 1)
    for y in range(min_y, max_y + 1):
        crossings = []
        for i, a in enumerate(points):
            b = points[(i + 1) % len(points)]
            if (a[1] <= y + 0.5 < b[1]) or (b[1] <= y + 0.5 < a[1]):
                crossings.append(a[0] + (y + 0.5 - a[1]) / (b[1] - a[1]) * (b[0] - a[0]))
        crossings.sort()
        for left, right in zip(crossings[::2], crossings[1::2]):
            for x in range(max(0, int(left + 0.5)), min(img.width, int(right + 0.5))):
                px[x, y] = color


def rect(img, left, top, right, bottom, color):
    px = img.load()
    for y in range(max(0, int(top)), min(img.height, int(bottom))):
        for x in range(max(0, int(left)), min(img.width, int(right))):
            px[x, y] = color


def direction(angle):
    """0도는 아래, 양수는 앞쪽(오른쪽), 180도는 위."""
    a = math.radians(angle)
    return math.sin(a), math.cos(a)


def along(p, angle, length):
    dx, dy = direction(angle)
    return p[0] + dx * length, p[1] + dy * length


def outlined(img, color):
    src = img.load()
    out = img.copy()
    px = out.load()
    for y in range(img.height):
        for x in range(img.width):
            if src[x, y][3] != 0:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < img.width and 0 <= ny < img.height and src[nx, ny][3] != 0:
                    px[x, y] = color
                    break
    return out


def dissolve(img, amount, seed, tint=None, rise=0):
    """프레임을 조각내 사라지게 한다. 사망 애니메이션에 쓴다."""
    rng = random.Random(seed)
    src = img.load()
    out = new_frame(img.width, img.height)
    px = out.load()
    for y in range(img.height):
        for x in range(img.width):
            if src[x, y][3] == 0 or rng.random() < amount:
                continue
            color = src[x, y]
            if tint:
                color = tuple(int(c + (t - c) * 0.6) for c, t in zip(color[:3], tint)) + (255,)
            ny = y - int(rise * rng.random())
            nx = x + int((rng.random() - 0.5) * rise)
            if 0 <= nx < img.width and 0 <= ny < img.height:
                px[nx, ny] = color
    return out


def flipped(img):
    return img.transpose(Image.FLIP_LEFT_RIGHT)


def strip(frames):
    w, h = frames[0].size
    sheet = new_frame(w * len(frames), h)
    for i, frame in enumerate(frames):
        sheet.paste(frame, (i * w, 0))
    return sheet


def save(img, path):
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    img.save(full)


# 사람형 뼈대 --------------------------------------------------------------

class Pose:
    def __init__(self, **kw):
        self.lean = 0
        self.tilt = 0
        self.front_leg = (10, -10)
        self.back_leg = (-10, -10)
        self.front_arm = (20, 30)
        self.back_arm = (-20, 30)
        self.weapon = None
        self.scarf = 0
        self.scarf_lift = 0
        self.hip_y = None
        self.dx = 0
        self.shield = False
        self.__dict__.update(kw)


def leg_points(hip, thigh, knee, upper, lower):
    k = along(hip, thigh, upper)
    a = along(k, thigh + knee, lower)
    foot = along(a, thigh + knee + 90, 3.5)
    return k, a, foot


def resolve_hip(pose, b):
    """지면에 닿는 포즈는 더 낮은 발이 지면에 놓이도록 엉덩이 높이를 정한다."""
    if pose.hip_y is not None:
        return CENTER_X + pose.dx, pose.hip_y
    lowest = 0
    for thigh, knee in (pose.front_leg, pose.back_leg):
        _, ankle, foot = leg_points((0, 0), thigh, knee, b['thigh'], b['shin'])
        lowest = max(lowest, ankle[1], foot[1])
    return CENTER_X + pose.dx, FEET_Y - lowest - 1.5


def draw_leg(img, hip, leg, b, thigh_color, shin_color, boot_color):
    k, a, foot = leg_points(hip, leg[0], leg[1], b['thigh'], b['shin'])
    capsule(img, hip, k, b['thigh_r'], b['knee_r'], thigh_color)
    capsule(img, k, a, b['knee_r'], b['ankle_r'], shin_color)
    capsule(img, a, foot, b['ankle_r'], 1.6, boot_color)


def draw_arm(img, shoulder, arm, b, upper_color, lower_color, hand_color):
    e = along(shoulder, arm[0], b['upper_arm'])
    h = along(e, arm[0] + arm[1], b['lower_arm'])
    capsule(img, shoulder, e, b['arm_r'], b['arm_r'] - 0.4, upper_color)
    capsule(img, e, h, b['arm_r'] - 0.4, b['arm_r'] - 0.8, lower_color)
    disc(img, h[0], h[1], b['arm_r'] - 0.3, hand_color)
    return h


# 플레이어: 남색 도복에 붉은 머플러, 푸른 날의 검을 든 검객 -------------------------

P = {
    'outline': hex_color('12101f'),
    'gi': hex_color('3d4a9a'),
    'gi_light': hex_color('6277d6'),
    'gi_dark': hex_color('2a3070'),
    'pants': hex_color('343a80'),
    'pants_dark': hex_color('262a5e'),
    'boot': hex_color('15142c'),
    'skin': hex_color('f4cfa6'),
    'skin_dark': hex_color('cf9d7c'),
    'hair': hex_color('1c1a33'),
    'hair_light': hex_color('37345e'),
    'scarf': hex_color('e8384f'),
    'scarf_dark': hex_color('a81f3e'),
    'blade': hex_color('e8fbff'),
    'edge': hex_color('63e3ff'),
    'guard': hex_color('e9b949'),
    'grip': hex_color('2a2238'),
}

PLAYER_BODY = {
    'thigh': 9.5, 'shin': 9.5, 'torso': 13, 'upper_arm': 7, 'lower_arm': 7,
    'thigh_r': 3.1, 'knee_r': 2.6, 'ankle_r': 2.1, 'arm_r': 2.5, 'hip_r': 4.0, 'chest_r': 4.6, 'head_r': 6.2,
}


def draw_scarf(img, neck, pose):
    points = [neck]
    for i in range(1, 8):
        wave = math.sin(pose.scarf + i * 0.95) * (0.55 + i * 0.32)
        points.append((neck[0] - 3.6 * i, neck[1] + 1 + wave - pose.scarf_lift * i * 0.75))
    for i in range(len(points) - 1):
        r0 = 2.5 - i * 0.22
        color = P['scarf'] if i % 2 == 0 else P['scarf_dark']
        capsule(img, points[i], points[i + 1], r0, r0 - 0.22, color)


def draw_player_head(img, center, pose):
    x, y = center
    disc(img, x, y, 6.2, P['hair'])
    # 뒤로 뻗은 머리칼이 달릴 때 실루엣을 만든다.
    polygon(img, [(x - 5, y - 4), (x - 10, y - 5), (x - 6, y - 1)], P['hair'])
    polygon(img, [(x - 5, y - 1), (x - 9.5, y + 1), (x - 5, y + 2.5)], P['hair'])
    polygon(img, [(x - 1, y - 6), (x + 3, y - 9), (x + 3.5, y - 5)], P['hair'])
    disc(img, x + 1.6, y + 1.2, 4.3, P['skin'])
    rect(img, x + 3, y - 0.5, x + 4, y + 1.5, P['outline'])
    rect(img, x + 0, y - 0.5, x + 1, y + 1.5, P['outline'])
    capsule(img, (x - 6, y - 2.3), (x + 5.5, y - 2.3), 0.9, 0.9, P['scarf'])
    capsule(img, (x - 2.5, y - 4.6), (x + 2.5, y - 5.0), 0.5, 0.5, P['hair_light'])


def draw_katana(img, hand, angle):
    tip = along(hand, angle, 24)
    guard = along(hand, angle, 3.2)
    butt = along(hand, angle, -2.5)
    capsule(img, butt, guard, 1.0, 1.0, P['grip'])
    normal = angle + 90
    capsule(img, along(guard, normal, 2.3), along(guard, normal, -2.3), 0.7, 0.7, P['guard'])
    capsule(img, guard, tip, 1.15, 0.45, P['blade'])
    capsule(img, along(guard, normal, 0.8), along(tip, normal, 0.3), 0.45, 0.3, P['edge'])


def draw_player(pose):
    b = PLAYER_BODY
    img = new_frame()
    hip = resolve_hip(pose, b)
    neck = along(hip, 180 - pose.lean, b['torso'])
    head = along(neck, 180 - pose.lean - pose.tilt, 5.2)
    shoulder_front = along(neck, -pose.lean, 2.2)
    shoulder_back = (shoulder_front[0] - 1.2, shoulder_front[1])

    draw_scarf(img, neck, pose)
    draw_arm(img, shoulder_back, pose.back_arm, b, P['gi_dark'], P['gi_dark'], P['skin_dark'])
    draw_leg(img, (hip[0] - 0.8, hip[1]), pose.back_leg, b, P['pants_dark'], P['pants_dark'], P['boot'])
    draw_leg(img, (hip[0] + 0.8, hip[1]), pose.front_leg, b, P['pants'], P['pants'], P['boot'])

    capsule(img, hip, neck, b['hip_r'], b['chest_r'], P['gi'])
    chest = along(hip, 180 - pose.lean, b['torso'] * 0.62)
    capsule(img, (chest[0] + 1.2, chest[1] - 3), (chest[0] + 1.6, chest[1] + 2), 1.4, 1.2, P['gi_light'])
    capsule(img, (hip[0] - 4, hip[1] - 0.5), (hip[0] + 4, hip[1] - 0.5), 1.2, 1.2, P['scarf'])
    capsule(img, (hip[0] - 3, hip[1]), (hip[0] - 7, hip[1] + 3.5), 0.9, 0.6, P['scarf_dark'])

    disc(img, neck[0], neck[1] + 0.2, 3.5, P['scarf'])
    draw_player_head(img, head, pose)

    front_hand = along(along(shoulder_front, pose.front_arm[0], b['upper_arm']), pose.front_arm[0] + pose.front_arm[1], b['lower_arm'])
    if pose.weapon is not None:
        draw_katana(img, front_hand, pose.weapon)
    draw_arm(img, shoulder_front, pose.front_arm, b, P['gi'], P['gi_light'], P['skin'])
    return outlined(img, P['outline'])


def run_pose(i, count=8):
    t = i / count * math.pi * 2

    def leg(phase):
        return 6 + 40 * math.cos(phase), -(14 + 78 * max(0, -math.sin(phase)))

    return Pose(
        lean=16,
        tilt=-6,
        front_leg=leg(t),
        back_leg=leg(t + math.pi),
        front_arm=(-48 + 6 * math.cos(t), -18),
        back_arm=(-5 + 40 * math.cos(t), 70),
        weapon=-112 + 4 * math.cos(t),
        scarf=-t,
        scarf_lift=0.12,
    )


def make_player():
    run = [draw_player(run_pose(i)) for i in range(8)]
    save(strip(run), 'player/run.png')

    rise = [
        draw_player(Pose(lean=8, tilt=-4, hip_y=32, front_leg=(62, -92), back_leg=(-22, -30), front_arm=(-56, -14),
                         back_arm=(30, 60), weapon=-122, scarf=s, scarf_lift=-0.1))
        for s in (0, 2)
    ]
    save(strip(rise), 'player/rise.png')

    fall = [
        draw_player(Pose(lean=4, tilt=-2, hip_y=30, front_leg=(34, -58), back_leg=(-12, -42), front_arm=(-70, -6),
                         back_arm=(58, 28), weapon=-138, scarf=s, scarf_lift=0.46))
        for s in (0, 2)
    ]
    save(strip(fall), 'player/fall.png')

    slide = [
        draw_player(Pose(lean=-58, tilt=52, hip_y=53, front_leg=(82, -4), back_leg=(46, -96), front_arm=(-112, 24),
                         back_arm=(-30, -40), weapon=-96, scarf=s, scarf_lift=0.05, dx=-3))
        for s in (0, 1.5, 3, 4.5)
    ]
    save(strip(slide), 'player/slide.png')

    stance = {'front_leg': (40, -32), 'back_leg': (-30, -24)}
    slash = [
        draw_player(Pose(lean=-4, tilt=4, front_arm=(174, -24), back_arm=(-30, 50), weapon=-150, scarf=0, scarf_lift=0.2, **stance)),
        draw_player(Pose(lean=10, tilt=-4, front_arm=(120, -18), back_arm=(-40, 40), weapon=94, scarf=1, scarf_lift=0.1, **stance)),
        draw_player(Pose(lean=24, tilt=-10, front_arm=(78, -6), back_arm=(-54, 26), weapon=62, scarf=2, scarf_lift=0.05, **stance)),
        draw_player(Pose(lean=22, tilt=-10, front_arm=(50, 6), back_arm=(-58, 26), weapon=30, scarf=3, scarf_lift=0.05, **stance)),
    ]
    save(strip(slash), 'player/slash.png')

    cut = [
        draw_player(Pose(lean=-14, tilt=8, front_arm=(30, 20), back_arm=(20, 30), weapon=70, scarf=0, scarf_lift=0.1, **stance)),
        draw_player(Pose(lean=2, tilt=0, front_arm=(110, -10), back_arm=(70, 20), weapon=130, scarf=1, scarf_lift=0.2, **stance)),
        draw_player(Pose(lean=12, tilt=-6, front_arm=(170, -10), back_arm=(120, 10), weapon=172, scarf=2, scarf_lift=0.4, **stance)),
        draw_player(Pose(lean=10, tilt=-4, front_arm=(176, -6), back_arm=(130, 6), weapon=-176, scarf=3, scarf_lift=0.5, **stance)),
    ]
    save(strip(cut), 'player/cut.png')

    idle = [
        draw_player(Pose(lean=6, tilt=-3, front_leg=(30, -30), back_leg=(-22, -22), front_arm=(34, 30), back_arm=(8, 34),
                         weapon=66, scarf=i * 1.5, scarf_lift=0.1))
        for i in range(4)
    ]
    save(strip(idle), 'player/idle.png')

    # 칼을 뒤로 빼고 낮게 웅크린 발도 자세. 힘이 찰수록 머플러가 위로 솟는다.
    charge = [
        draw_player(Pose(lean=24, tilt=-14, front_leg=(58, -74), back_leg=(-48, -34), front_arm=(-34, 56), back_arm=(34, 64),
                         weapon=-104, scarf=i * 1.6, scarf_lift=-0.1 - i * 0.1))
        for i in range(4)
    ]
    save(strip(charge), 'player/charge.png')

    dash = [
        draw_player(Pose(lean=66, tilt=-46, hip_y=38, dx=-4, front_leg=(50, -56), back_leg=(-74, -6), front_arm=(88, 4),
                         back_arm=(-96, 10), weapon=92, scarf=s, scarf_lift=-0.03))
        for s in (0, 2.5)
    ]
    save(strip(dash), 'player/dash.png')

    hit = [
        draw_player(Pose(lean=-22, tilt=14, front_leg=(26, -38), back_leg=(-4, -46), front_arm=(-120, 30),
                         back_arm=(120, 30), weapon=-160, scarf=s, scarf_lift=0.5))
        for s in (0, 2)
    ]
    white = [tint_all(hit[0], (255, 255, 255)), hit[1]]
    save(strip(white), 'player/hit.png')


def tinted(img, color, amount):
    out = img.copy()
    px = out.load()
    for y in range(out.height):
        for x in range(out.width):
            r, g, b, a = px[x, y]
            if a != 0:
                px[x, y] = (int(r + (color[0] - r) * amount), int(g + (color[1] - g) * amount), int(b + (color[2] - b) * amount), a)
    return out


def tint_all(img, color):
    out = img.copy()
    px = out.load()
    for y in range(out.height):
        for x in range(out.width):
            if px[x, y][3] != 0:
                px[x, y] = color + (255,)
    return out


# 탄과 얼음 파편 ---------------------------------------------------------------

def make_projectiles():
    shard = new_frame(14, 6)
    polygon(shard, [(0, 3), (5, 0), (14, 3), (5, 6)], hex_color('bff4ff'))
    polygon(shard, [(0, 3), (5, 3), (14, 3), (5, 6)], hex_color('5fd8ff'))
    save(shard, 'monster/ice_shard.png')

    for name, glow_c, body_c, core_c in (('bullet', 'a8341c', 'ff7a2f', 'fff0b0'), ('bullet_reflected', '1f6fb0', '5fd8ff', 'f0fcff'),
                                         ('bullet_purple', '5b2fa6', 'c77dff', 'ffe9ff'), ('bullet_black', 'ff3b6b', '1a0f28', '5a3a8a')):
        frames = []
        for i in range(4):
            img = new_frame(16, 16)
            disc(img, 8, 8, 7.5, hex_color(glow_c))
            disc(img, 8, 8, 5.2, hex_color(body_c))
            disc(img, 8, 8, 2.8, hex_color(core_c))
            a = i / 4 * math.pi * 2
            rect(img, 8 + math.cos(a) * 5, 8 + math.sin(a) * 5, 8 + math.cos(a) * 5 + 2, 8 + math.sin(a) * 5 + 2, hex_color(core_c))
            frames.append(img)
        save(strip(frames), f'monster/{name}.png')


# 보스: 뿔 달린 투구와 보랏빛 망토의 거대 기사, 불씨 날의 대검 ------------------------

B = {
    'outline': hex_color('120a18'),
    'armor': hex_color('4c4a66'),
    'armor_light': hex_color('8583a8'),
    'armor_dark': hex_color('2c2a42'),
    'trim': hex_color('e9b949'),
    'cape': hex_color('5b2fa6'),
    'cape_dark': hex_color('3a1c70'),
    'horn': hex_color('d9d2c0'),
    'visor': hex_color('120a18'),
    'eye': hex_color('ff4a4a'),
    'core': hex_color('c77dff'),
    'core_light': hex_color('ffe9ff'),
    'grip': hex_color('2a2238'),
    'blade': hex_color('b7bccb'),
    'blade_dark': hex_color('6d7286'),
    'ember': hex_color('ff9a3d'),
}
BOSS_FRAME = 172
BOSS_FEET_Y = 168
BOSS_BODY = {
    'thigh': 20, 'shin': 20, 'torso': 28, 'upper_arm': 16, 'lower_arm': 16,
    'thigh_r': 8, 'knee_r': 7, 'ankle_r': 6, 'arm_r': 7, 'hip_r': 11, 'chest_r': 16,
}


def draw_greatsword(img, hand, angle):
    tip = along(hand, angle, 50)
    base = along(hand, angle, 7)
    normal = angle + 90
    capsule(img, along(hand, angle, -6), base, 1.8, 1.8, B['grip'])
    polygon(img, [along(base, normal, 4.5), along(tip, normal, 1.5), along(tip, normal, -1.5), along(base, normal, -4.5)], B['blade'])
    capsule(img, base, along(tip, angle, -6), 1.2, 0.6, B['blade_dark'])
    capsule(img, along(base, normal, 4.2), along(tip, normal, 1.2), 0.8, 0.5, B['ember'])
    capsule(img, along(base, normal, 7), along(base, normal, -7), 1.6, 1.6, B['trim'])


def draw_shield(img, center):
    x, y = center
    points = [(x - 12, y - 26), (x + 12, y - 26), (x + 16, y - 6), (x + 10, y + 16), (x, y + 30), (x - 10, y + 16), (x - 16, y - 6)]
    polygon(img, points, B['trim'])
    inner = [(x - 9, y - 22), (x + 9, y - 22), (x + 12, y - 6), (x + 7, y + 14), (x, y + 25), (x - 7, y + 14), (x - 12, y - 6)]
    polygon(img, inner, B['armor'])
    polygon(img, [(x - 9, y - 22), (x, y - 22), (x, y + 25), (x - 7, y + 14), (x - 12, y - 6)], B['armor_light'])
    disc(img, x, y - 2, 5, B['core'])
    disc(img, x, y - 2, 2.5, B['core_light'])


def draw_boss_leg(img, hip, leg, thigh_color, shin_color):
    b = BOSS_BODY
    knee, ankle, _ = leg_points(hip, leg[0], leg[1], b['thigh'], b['shin'])
    foot = along(ankle, leg[0] + leg[1] + 90, 8)
    capsule(img, hip, knee, b['thigh_r'], b['knee_r'], thigh_color)
    capsule(img, knee, ankle, b['knee_r'], b['ankle_r'], shin_color)
    capsule(img, ankle, foot, b['ankle_r'], 3.5, B['armor_dark'])
    disc(img, knee[0], knee[1], b['knee_r'] - 1.5, B['armor_light'])


def draw_boss_head(img, center):
    x, y = center
    polygon(img, [(x - 7, y - 8), (x - 22, y - 26), (x - 12, y - 6)], B['horn'])
    polygon(img, [(x + 6, y - 9), (x + 20, y - 28), (x + 13, y - 6)], B['horn'])
    disc(img, x, y, 12, B['armor'])
    disc(img, x - 2, y - 3, 8, B['armor_light'])
    disc(img, x, y, 10, B['armor'])
    rect(img, x - 4, y - 2, x + 13, y + 3, B['visor'])
    rect(img, x + 3, y - 1, x + 7, y + 2, B['eye'])
    rect(img, x + 9, y - 1, x + 12, y + 2, B['eye'])
    capsule(img, (x - 2, y - 11), (x + 2, y - 11), 1.2, 1.2, B['trim'])


def draw_boss(pose):
    b = BOSS_BODY
    img = new_frame(BOSS_FRAME, BOSS_FRAME)
    lowest = 0
    for thigh, knee in (pose.front_leg, pose.back_leg):
        _, ankle, foot = leg_points((0, 0), thigh, knee, b['thigh'], b['shin'])
        lowest = max(lowest, ankle[1] + b['ankle_r'], foot[1] + 3.5)
    hip = (BOSS_FRAME / 2 + pose.dx, BOSS_FEET_Y - lowest)
    neck = along(hip, 180 - pose.lean, b['torso'])
    head = along(neck, 180 - pose.lean - pose.tilt, 13)
    shoulder_front = along(neck, -pose.lean, 3)
    shoulder_back = (shoulder_front[0] - 7, shoulder_front[1])

    sway = math.sin(pose.scarf) * 4
    polygon(img, [(neck[0] - 8, neck[1]), (neck[0] + 6, neck[1]), (hip[0] - 4, hip[1] + 26 + sway), (hip[0] - 30 + sway, BOSS_FEET_Y - 12),
                  (hip[0] - 38 + sway, hip[1] + 8)], B['cape'])
    polygon(img, [(neck[0] - 8, neck[1]), (hip[0] - 30 + sway, BOSS_FEET_Y - 12), (hip[0] - 38 + sway, hip[1] + 8)], B['cape_dark'])

    draw_arm(img, shoulder_back, pose.back_arm, b, B['armor_dark'], B['armor_dark'], B['armor_dark'])
    draw_boss_leg(img, (hip[0] - 4, hip[1]), pose.back_leg, B['armor_dark'], B['armor_dark'])
    draw_boss_leg(img, (hip[0] + 4, hip[1]), pose.front_leg, B['armor'], B['armor'])

    capsule(img, hip, neck, b['hip_r'], b['chest_r'], B['armor'])
    chest = along(hip, 180 - pose.lean, b['torso'] * 0.62)
    capsule(img, (chest[0] - 8, chest[1] - 6), (chest[0] - 6, chest[1] + 8), 2.2, 1.6, B['armor_light'])
    disc(img, chest[0] + 3, chest[1], 6, B['armor_dark'])
    disc(img, chest[0] + 3, chest[1], 4, B['core'])
    disc(img, chest[0] + 3, chest[1], 2, B['core_light'])
    capsule(img, (hip[0] - 10, hip[1] - 1), (hip[0] + 10, hip[1] - 1), 2.4, 2.4, B['trim'])
    disc(img, shoulder_back[0], shoulder_back[1], 9, B['armor_dark'])

    draw_boss_head(img, head)

    front_hand = along(along(shoulder_front, pose.front_arm[0], b['upper_arm']), pose.front_arm[0] + pose.front_arm[1], b['lower_arm'])
    draw_greatsword(img, front_hand, pose.weapon)
    draw_arm(img, shoulder_front, pose.front_arm, b, B['armor'], B['armor_light'], B['armor_dark'])
    if pose.shield:
        draw_shield(img, (front_hand[0] + 6, front_hand[1]))
    disc(img, shoulder_front[0], shoulder_front[1], 10, B['armor'])
    capsule(img, (shoulder_front[0] - 7, shoulder_front[1] - 4), (shoulder_front[0] + 7, shoulder_front[1] - 4), 2, 2, B['armor_light'])
    return flipped(outlined(img, B['outline']))


def save_boss_strip(name, frames):
    save(strip(frames), f'monster/boss_{name}.png')
    # 맞은 순간 같은 프레임을 흰색으로 바꿔 그린다.
    save(strip([tint_all(frame, (255, 255, 255)) for frame in frames]), f'monster/boss_{name}_flash.png')
    # 분노 상태는 온몸이 붉게 달아오른다.
    save(strip([tinted(frame, (255, 40, 30), 0.38) for frame in frames]), f'monster/boss_{name}_rage.png')


def make_boss_wave():
    frames = []
    for i in range(4):
        rng = random.Random(70 + i)
        img = new_frame(48, 40)
        for layer, (height, color) in enumerate(((36, 'ff5a1f'), (26, 'ffb347'), (14, 'fff3c4'))):
            lean = 8 + 2 * math.sin(i / 4 * math.pi * 2)
            width = 22 - layer * 5
            polygon(img, [(24 - width, 40), (24 - lean, 40 - height), (24 + width * 0.3, 40 - height * 0.7), (24 + width, 40)], hex_color(color))
        for _ in range(8):
            x, y = rng.randint(4, 43), rng.randint(0, 38)
            rect(img, x, y, x + 2, y + 2, hex_color(rng.choice(['fff3c4', 'ffb347'])))
        frames.append(img)
    save(strip(frames), 'monster/boss_wave.png')


def make_boss():
    stance = {'front_leg': (30, -30), 'back_leg': (-24, -20)}
    idle = [draw_boss(Pose(lean=8, tilt=-4, front_arm=(46, 24), back_arm=(10, 30), weapon=74 + i, scarf=i * 1.5, **stance)) for i in range(4)]
    save_boss_strip('idle', idle)

    walk = []
    for i in range(6):
        t = i / 6 * math.pi * 2

        def leg(phase):
            return 2 + 26 * math.cos(phase), -(10 + 50 * max(0, -math.sin(phase)))

        walk.append(draw_boss(Pose(lean=12, tilt=-6, front_leg=leg(t), back_leg=leg(t + math.pi), front_arm=(46 + 6 * math.cos(t), 24),
                                   back_arm=(-6 - 18 * math.cos(t), 30), weapon=74, scarf=t)))
    save_boss_strip('walk', walk)

    windup = [
        draw_boss(Pose(lean=-8, tilt=6, front_arm=(164, -24), back_arm=(140, -20), weapon=-168, scarf=0, **stance)),
        draw_boss(Pose(lean=-14, tilt=8, front_arm=(174, -30), back_arm=(150, -24), weapon=-156, scarf=1, **stance)),
    ]
    save_boss_strip('windup', windup)

    attack = [
        draw_boss(Pose(lean=14, tilt=-8, front_arm=(122, -12), back_arm=(96, -6), weapon=118, scarf=2, **stance)),
        draw_boss(Pose(lean=30, tilt=-14, front_arm=(62, -6), back_arm=(44, 0), weapon=50, scarf=3, **stance)),
    ]
    save_boss_strip('attack', attack)

    recover = [
        draw_boss(Pose(lean=32, tilt=-16, front_arm=(56, 0), back_arm=(38, 4), weapon=44, scarf=i, **stance))
        for i in (3, 4)
    ]
    save_boss_strip('recover', recover)

    guard = [draw_boss(Pose(lean=6, tilt=-2, front_arm=(82, 14), back_arm=(30, 30), weapon=170, scarf=i, shield=True, **stance)) for i in (0, 1)]
    save_boss_strip('guard', guard)

    kneel = {'front_leg': (66, -90), 'back_leg': (-8, -100)}
    groggy = [draw_boss(Pose(lean=38 + i * 3, tilt=-22, front_arm=(24, 6), back_arm=(14, 8), weapon=20, scarf=i, **kneel)) for i in (0, 1)]
    save_boss_strip('groggy', groggy)

    body = draw_boss(Pose(lean=-24, tilt=12, front_leg=(40, -44), back_leg=(10, -50), front_arm=(-120, 20), back_arm=(110, 20), weapon=-150))
    death = [tint_all(body, (255, 245, 255))]
    for i, (amount, tint) in enumerate(((0.15, (230, 190, 255)), (0.3, (200, 130, 255)), (0.5, (170, 100, 240)), (0.7, (130, 70, 200)), (0.88, (90, 50, 150)))):
        death.append(dissolve(body, amount, 51 + i, tint, 6 + i * 8))
    save(strip(death), 'monster/boss_death.png')


# 심연의 집행자: 수문장과 같은 뼈대에 핏빛 갑옷과 검은 망토, 불타는 대검 --------------------

EXECUTOR_COLORS = {
    'armor': hex_color('5a1f2a'),
    'armor_light': hex_color('a8323e'),
    'armor_dark': hex_color('2e0f18'),
    'trim': hex_color('ff9a3d'),
    'cape': hex_color('1c0b14'),
    'cape_dark': hex_color('0c0508'),
    'horn': hex_color('3a2028'),
    'visor': hex_color('0a0408'),
    'eye': hex_color('ffdf5a'),
    'core': hex_color('ff5a1f'),
    'core_light': hex_color('fff3c4'),
    'grip': hex_color('1a0f18'),
    'blade': hex_color('e8384f'),
    'blade_dark': hex_color('7a1420'),
    'ember': hex_color('ffb347'),
}


def save_executor_strip(name, frames):
    save(strip(frames), f'monster/exec_{name}.png')
    save(strip([tint_all(frame, (255, 255, 255)) for frame in frames]), f'monster/exec_{name}_flash.png')


def make_executor():
    warden_colors = dict(B)
    B.update(EXECUTOR_COLORS)
    stance = {'front_leg': (34, -34), 'back_leg': (-28, -24)}
    save_executor_strip('idle', [draw_boss(Pose(lean=14, tilt=-6, front_arm=(50, 20), back_arm=(14, 30), weapon=66 + i, scarf=i * 1.5, **stance)) for i in range(4)])
    walk = []
    for i in range(6):
        t = i / 6 * math.pi * 2

        def leg(phase):
            return 4 + 34 * math.cos(phase), -(12 + 64 * max(0, -math.sin(phase)))

        walk.append(draw_boss(Pose(lean=22, tilt=-10, front_leg=leg(t), back_leg=leg(t + math.pi), front_arm=(60, 16),
                                   back_arm=(-10 - 22 * math.cos(t), 30), weapon=60, scarf=t)))
    save_executor_strip('walk', walk)
    save_executor_strip('windup', [draw_boss(Pose(lean=-12, tilt=6, front_arm=(170, -28), back_arm=(140, -20), weapon=-160, scarf=i, **stance)) for i in (0, 1)])
    save_executor_strip('low', [draw_boss(Pose(lean=34, tilt=-14, front_arm=(50, -2), back_arm=(30, 4), weapon=72 - i * 10, scarf=i, **stance)) for i in (0, 1)])
    save_executor_strip('high', [draw_boss(Pose(lean=4, tilt=-4, front_arm=(112, -4), back_arm=(70, 8), weapon=106 + i * 8, scarf=i, **stance)) for i in (0, 1)])
    save_executor_strip('throw', [draw_boss(Pose(lean=26, tilt=-10, front_arm=(120, 10), back_arm=(-20, 30), weapon=150, scarf=i, **stance)) for i in (0, 1)])
    save_executor_strip('recover', [draw_boss(Pose(lean=36, tilt=-18, front_arm=(50, 4), back_arm=(32, 6), weapon=36, scarf=i, **stance)) for i in (3, 4)])
    kneel = {'front_leg': (66, -90), 'back_leg': (-8, -100)}
    save_executor_strip('groggy', [draw_boss(Pose(lean=40 + i * 3, tilt=-24, front_arm=(20, 6), back_arm=(10, 8), weapon=16, scarf=i, **kneel)) for i in (0, 1)])
    body = draw_boss(Pose(lean=-24, tilt=12, front_leg=(40, -44), back_leg=(10, -50), front_arm=(-120, 20), back_arm=(110, 20), weapon=-150))
    death = [tint_all(body, (255, 245, 230))]
    for i, (amount, tint) in enumerate(((0.15, (255, 170, 120)), (0.3, (255, 110, 70)), (0.5, (220, 70, 50)), (0.7, (150, 40, 40)), (0.88, (80, 20, 30)))):
        death.append(dissolve(body, amount, 81 + i, tint, 6 + i * 8))
    save(strip(death), 'monster/exec_death.png')
    B.update(warden_colors)

    frames = []
    for i in range(2):
        img = new_frame(64, 24)
        polygon(img, [(2, 12), (46, 6), (54, 8), (54, 16), (46, 18)], hex_color('ffb347' if i else 'ff5a1f'))
        polygon(img, [(6, 12), (46, 9), (52, 10), (52, 14), (46, 15)], hex_color('e8384f'))
        polygon(img, [(10, 12), (44, 11), (44, 13)], hex_color('fff3c4'))
        rect(img, 52, 3, 56, 21, hex_color('e9b949'))
        rect(img, 56, 10, 63, 14, hex_color('1a0f18'))
        frames.append(img)
    save(strip(frames), 'monster/exec_sword.png')


# 균열의 마녀: 뾰족한 관을 쓴 채 떠다니는 보라 로브, 두 손으로 탄을 모은다 ----------------

W = {
    'outline': hex_color('100620'),
    'robe': hex_color('3a1f6e'),
    'robe_light': hex_color('6a3fb0'),
    'robe_dark': hex_color('221045'),
    'skin': hex_color('d8c8f0'),
    'eye': hex_color('ff5fd2'),
    'crown': hex_color('e9b949'),
    'glow': hex_color('c77dff'),
    'core': hex_color('ffe9ff'),
}
WITCH_FRAME = 96
WITCH_FRAME_H = 112


def draw_witch(bob, arm_lift, glow):
    img = new_frame(WITCH_FRAME, WITCH_FRAME_H)
    cx = WITCH_FRAME / 2
    hem = WITCH_FRAME_H - 8 + bob
    shoulder = hem - 54
    head = (cx + 2, shoulder - 12)
    polygon(img, [(cx - 26, hem - 4), (cx - 14, hem + 2), (cx - 4, hem - 6), (cx + 8, hem + 3), (cx + 22, hem - 7), (cx + 11, shoulder), (cx - 11, shoulder)], W['robe'])
    polygon(img, [(cx + 22, hem - 7), (cx + 8, hem + 3), (cx + 3, shoulder), (cx + 11, shoulder)], W['robe_light'])
    polygon(img, [(cx - 26, hem - 4), (cx - 14, hem + 2), (cx - 5, shoulder), (cx - 11, shoulder)], W['robe_dark'])
    rect(img, cx - 9, shoulder + 16, cx + 10, shoulder + 19, W['crown'])
    disc(img, head[0], head[1], 9, W['skin'])
    polygon(img, [(head[0] - 11, head[1] - 2), (head[0] - 8, head[1] - 24), (head[0] - 1, head[1] - 8), (head[0] + 3, head[1] - 28),
                  (head[0] + 7, head[1] - 8), (head[0] + 13, head[1] - 22), (head[0] + 11, head[1] - 2)], W['crown'])
    rect(img, head[0] + 2, head[1] - 1, head[0] + 5, head[1] + 2, W['eye'])
    rect(img, head[0] + 6, head[1] - 1, head[0] + 8, head[1] + 2, W['eye'])
    hand = (cx + 22, shoulder + 10 - arm_lift)
    capsule(img, (cx + 6, shoulder + 4), hand, 3.2, 2.4, W['robe_light'])
    capsule(img, (cx - 6, shoulder + 4), (cx - 18, shoulder + 14 - arm_lift / 2), 3.2, 2.4, W['robe_dark'])
    disc(img, hand[0], hand[1], 2.6, W['skin'])
    img = outlined(img, W['outline'])
    if glow:
        disc(img, hand[0] + 4, hand[1] - 2, 8, W['glow'])
        disc(img, hand[0] + 4, hand[1] - 2, 4, W['core'])
    return flipped(img)


def save_witch_strip(name, frames):
    save(strip(frames), f'monster/witch_{name}.png')
    save(strip([tint_all(frame, (255, 255, 255)) for frame in frames]), f'monster/witch_{name}_flash.png')


def witch_death_frames(body):
    """하얗게 번쩍인 뒤 보랏빛 조각으로 흩어진다."""
    death = [tint_all(body, (255, 240, 255))]
    for i, (amount, tint) in enumerate(((0.2, (230, 190, 255)), (0.4, (190, 130, 255)), (0.6, (150, 90, 230)), (0.8, (100, 60, 180)))):
        death.append(dissolve(body, amount, 61 + i, tint, 6 + i * 8))
    return death


def make_witch():
    save_witch_strip('float', [draw_witch(math.sin(i / 6 * math.pi * 2) * 2, 0, False) for i in range(6)])
    save_witch_strip('cast', [draw_witch(-2, 10 + i * 3, True) for i in range(3)])
    save(strip(witch_death_frames(draw_witch(0, 0, False))), 'monster/witch_death.png')

    frames = []
    for i in range(6):
        img = new_frame(48, 48)
        px = img.load()
        for y in range(48):
            for x in range(48):
                d = math.hypot(x + 0.5 - 24, y + 0.5 - 24)
                a = math.atan2(y + 0.5 - 24, x + 0.5 - 24) + i * 0.5
                if 19 <= d <= 22 or (11 <= d <= 13 and math.sin(a * 6) > 0):
                    px[x, y] = hex_color('c77dff')
                elif 13 < d < 19 and abs(math.sin(a * 3)) < 0.12:
                    px[x, y] = hex_color('ffe9ff')
        frames.append(img)
    save(strip(frames), 'monster/witch_circle.png')


# 빗자루 마녀(스테이지 2 중간 보스)와 그 공격 ---------------------------------------

BROOM_FRAME = 128
BROOM = {
    'handle': hex_color('7a4a2a'),
    'handle_light': hex_color('b07a44'),
    'bristle': hex_color('e9b949'),
    'bristle_dark': hex_color('a8741c'),
}


def draw_broom_witch(bob, arm_lift, glow, sway):
    """빗자루에 걸터앉아 뒤따라오는 플레이어(왼쪽)를 돌아본다. 빗자루는 달리는 방향(오른쪽)을 향한다."""
    img = new_frame(BROOM_FRAME, WITCH_FRAME_H)
    witch = draw_witch(bob, arm_lift, glow)
    img.paste(witch, ((BROOM_FRAME - WITCH_FRAME) // 2, 0), witch)
    broom = new_frame(BROOM_FRAME, WITCH_FRAME_H)
    y = WITCH_FRAME_H - 24 + bob
    capsule(broom, (28, y), (124, y - 4), 2.4, 1.6, BROOM['handle'])
    capsule(broom, (30, y - 1), (122, y - 5), 0.7, 0.7, BROOM['handle_light'])
    polygon(broom, [(31, y - 4), (31, y + 4), (5, y + 11 + sway), (2, y + 1 + sway), (6, y - 9 + sway)], BROOM['bristle'])
    polygon(broom, [(31, y), (31, y + 4), (5, y + 11 + sway), (3, y + 4 + sway)], BROOM['bristle_dark'])
    rect(broom, 28, y - 5, 32, y + 5, W['glow'])
    img.alpha_composite(outlined(broom, W['outline']))
    return img


def make_broom_witch():
    save(strip([draw_broom_witch(math.sin(i / 6 * math.pi * 2) * 2, 0, False, (i % 3) - 1) for i in range(6)]), 'monster/broom_fly.png')
    save(strip([draw_broom_witch(-2, 10 + i * 3, True, i - 1) for i in range(3)]), 'monster/broom_cast.png')
    save(strip(witch_death_frames(draw_broom_witch(0, 0, False, 0))), 'monster/broom_death.png')

    # 반짝이는 탄: 금빛 탄에서 가로세로 빛살과 대각선 빛살이 번갈아 길어지며 반짝인다. 베어 튕겨 낼 수 있다.
    frames = []
    for i in range(4):
        img = new_frame(24, 24)
        for length, turn in (((11.5, 9.5, 7.5, 9.5)[i], 0), ((7, 9, 11, 9)[i], math.pi / 4)):
            for k in range(4):
                a = turn + k * math.pi / 2
                capsule(img, (12, 12), (12 + math.cos(a) * length, 12 + math.sin(a) * length), 2.2, 0.7, hex_color('fff6c8'))
        disc(img, 12, 12, 5.6, hex_color('ff9d2e'))
        disc(img, 12, 12, 4.2, hex_color('ffe27a'))
        disc(img, 12, 12, 2.4, hex_color('ffffff'))
        frames.append(img)
    save(strip(frames), 'monster/bullet_spark.png')

    # 균열 파편: 검은 탄을 키워 가시를 두른 모습. 가시가 돌며 날아온다.
    frames = []
    for i in range(4):
        img = new_frame(24, 24)
        for k in range(8):
            a = (k + i / 4) / 8 * math.pi * 2
            side = a + math.pi / 2
            tip = (12 + math.cos(a) * 11.5, 12 + math.sin(a) * 11.5)
            polygon(img, [tip, (12 + math.cos(a) * 6 + math.cos(side) * 3, 12 + math.sin(a) * 6 + math.sin(side) * 3),
                          (12 + math.cos(a) * 6 - math.cos(side) * 3, 12 + math.sin(a) * 6 - math.sin(side) * 3)], hex_color('ff3b6b'))
        disc(img, 12, 12, 8.5, hex_color('ff3b6b'))
        disc(img, 12, 12, 6.8, hex_color('1a0f28'))
        disc(img, 12, 12, 3.6, hex_color('5a3a8a'))
        rect(img, 8, 11, 13, 13, hex_color('ffe9ff'))
        frames.append(img)
    save(strip(frames), 'monster/rift_orb.png')

    # 번개 한 토막. 양 끝이 가운데 높이에서 만나 이어 붙여도 끊기지 않는다.
    rng = random.Random(77)
    frames = []
    for _ in range(4):
        img = new_frame(32, 16)
        points = [(0, 8)] + [(x, 8 + rng.uniform(-5, 5)) for x in (6, 12, 19, 26)] + [(32, 8)]
        branch = points[rng.randint(1, 4)]
        twig = (branch[0] + 7, branch[1] + rng.choice((-6, 6)))
        capsule(img, branch, twig, 1.2, 0.6, (255, 79, 216, 150))
        for a, b in zip(points, points[1:]):
            capsule(img, a, b, 2.8, 2.8, (255, 79, 216, 150))
        for a, b in zip(points, points[1:]):
            capsule(img, a, b, 1.1, 1.1, hex_color('fff0ff'))
        frames.append(img)
    save(strip(frames), 'monster/bolt.png')

    shock = new_frame(1, 1)
    shock.putpixel((0, 0), (214, 70, 255, 70))
    save(shock, 'monster/shock.png')


# 발판 --------------------------------------------------------------------

def periodic_noise(w, h, cell_x, cell_y, rng):
    """가로로 이어 붙여도 끊기지 않는 값 잡음. 0~1을 돌려준다."""
    columns = w // cell_x
    rows = h // cell_y + 2
    grid = [[rng.random() for _ in range(columns)] for _ in range(rows)]
    out = []
    for y in range(h):
        gy = y / cell_y
        y0 = int(gy)
        fy = gy - y0
        fy = fy * fy * (3 - 2 * fy)
        row = []
        for x in range(w):
            gx = x / cell_x
            x0 = int(gx)
            fx = gx - x0
            fx = fx * fx * (3 - 2 * fx)
            a = grid[y0][x0 % columns] * (1 - fx) + grid[y0][(x0 + 1) % columns] * fx
            b = grid[y0 + 1][x0 % columns] * (1 - fx) + grid[y0 + 1][(x0 + 1) % columns] * fx
            row.append(a * (1 - fy) + b * fy)
        out.append(row)
    return out


def make_platform(rng, top, top_light, body, dark):
    width = 640
    img = new_frame(width, 24)
    px = img.load()
    hang = periodic_noise(width, 1, 8, 1, rng)[0]
    top_c, top_l, body_c, dark_c = hex_color(top), hex_color(top_light), hex_color(body), hex_color(dark)
    for x in range(width):
        bottom = 12 + int(hang[x] * 12)
        for y in range(bottom):
            color = body_c if y < 9 else dark_c
            if (x // 12 + y // 4) % 5 == 0:
                color = dark_c
            px[x, y] = color
        px[x, 0] = top_l
        px[x, 1] = top_c
        px[x, 2] = top_c
    cap = new_frame(16, 24)
    cap_px = cap.load()
    for x in range(16):
        reach = (16 - x) * 1.4
        bottom = int(max(4, 24 - reach))
        for y in range(bottom):
            color = body_c if y < 9 else dark_c
            cap_px[x, y] = color
        cap_px[x, 0] = top_l
        cap_px[x, 1] = top_c
        cap_px[x, 2] = top_c
    return img.resize((width * 2, 48), Image.NEAREST), cap


def make_platforms():
    rng = random.Random(21)
    platform, cap = make_platform(rng, 'c2401a', 'ff8a3d', '46201f', '2a1014')
    save(platform, 'map/platform_phase3.png')
    save(cap, 'map/platform_cap_phase3.png')
    platform, cap = make_platform(rng, '6f8a58', '9ab86f', '5a506e', '3a3350')
    save(platform, 'map/platform_phase1.png')
    save(cap, 'map/platform_cap_phase1.png')


# 장애물 --------------------------------------------------------------------

def make_crate(w=30, h=30):
    img = new_frame(w, h)
    wood, wood_dark, wood_light, iron = hex_color('a56a33'), hex_color('734521'), hex_color('c98f4e'), hex_color('565a68')
    rect(img, 1, 1, w - 1, h - 1, wood)
    for y in (h * 3 // 10, h * 19 // 30):
        rect(img, 1, y, w - 1, y + 1, wood_dark)
    capsule(img, (4, 4), (w - 4, h - 4), 1.3, 1.3, wood_light)
    capsule(img, (w - 4, 4), (4, h - 4), 1.0, 1.0, wood_dark)
    rect(img, 1, 1, w - 1, 4, wood_light)
    rect(img, 1, h - 4, w - 1, h - 1, wood_dark)
    for x, y in ((1, 1), (w - 6, 1), (1, h - 6), (w - 6, h - 6)):
        rect(img, x, y, x + 5, y + 5, iron)
    return outlined(img, hex_color('1a1020'))


def make_rock(w=30, h=30):
    def scaled(points):
        return [(x * w / 30, y * h / 30) for x, y in points]

    img = new_frame(w, h)
    polygon(img, scaled([(1, 29), (2, 16), (8, 6), (17, 2), (25, 8), (29, 19), (29, 29)]), hex_color('6b6577'))
    polygon(img, scaled([(4, 18), (9, 8), (17, 4), (22, 9), (14, 13)]), hex_color('93899f'))
    polygon(img, scaled([(14, 29), (18, 18), (29, 19), (29, 29)]), hex_color('4a4557'))
    capsule(img, *scaled([(9, 19), (14, 24)]), 0.6, 0.6, hex_color('3a3646'))
    capsule(img, *scaled([(20, 11), (24, 16)]), 0.6, 0.6, hex_color('4a4557'))
    return outlined(img, hex_color('1a1020'))


def make_spikes():
    """바닥 철판에 박힌 가시 다섯 개."""
    w, h = 75, 18
    img = new_frame(w, h)
    steel, light, dark = hex_color('9aa0b4'), hex_color('dfe4f2'), hex_color('565a68')
    for i in range(5):
        left = 2 + i * 14.4
        polygon(img, [(left, h - 4), (left + 6.5, 1), (left + 13, h - 4)], steel)
        polygon(img, [(left, h - 4), (left + 6.5, 1), (left + 5, h - 4)], light)
        polygon(img, [(left + 9, h - 4), (left + 6.5, 1), (left + 13, h - 4)], dark)
    rect(img, 1, h - 5, w - 1, h - 1, dark)
    rect(img, 1, h - 5, w - 1, h - 4, steel)
    return outlined(img, hex_color('1a1020'))


def make_barricade():
    """끝을 깎은 통나무를 엮은 방책. 1단 점프보다 높다."""
    w, h = 35, 110
    img = new_frame(w, h)
    wood, wood_dark, wood_light, iron = hex_color('8a5a2e'), hex_color('5c3a1c'), hex_color('b98549'), hex_color('565a68')
    rng = random.Random(31)
    for i, tip in enumerate((10, 2, 7)):
        left = 2 + i * 10.5
        polygon(img, [(left, tip + 14), (left + 5, tip), (left + 10, tip + 14), (left + 10, h - 1), (left, h - 1)], wood)
        rect(img, left, tip + 14, left + 3, h - 1, wood_light)
        rect(img, left + 8, tip + 14, left + 10, h - 1, wood_dark)
        polygon(img, [(left + 5, tip), (left + 10, tip + 14), (left + 6, tip + 14)], wood_dark)
        for _ in range(4):
            y = rng.randint(tip + 20, h - 10)
            rect(img, left + 4, y, left + 6, y + 5, wood_dark)
    for y in (38, 82):
        rect(img, 1, y, w - 1, y + 5, iron)
        rect(img, 1, y, w - 1, y + 1, hex_color('8d92a6'))
        for x in (5, 16, 27):
            rect(img, x, y + 2, x + 2, y + 4, hex_color('2a2238'))
    return outlined(img, hex_color('1a1020'))


def make_beam():
    """사슬에 매달린 가시 통나무. 아래 70px이 통나무이고 그 위는 화면 꼭대기까지 닿는 사슬이다."""
    w, h, log_h = 150, 265, 70
    img = new_frame(w, h)
    wood, wood_dark, wood_light = hex_color('7a4f2a'), hex_color('4e3018'), hex_color('a8763f')
    iron, iron_light, iron_dark = hex_color('565a68'), hex_color('8d92a6'), hex_color('2a2238')
    top = h - log_h
    for x in (22, w - 22):
        for y in range(0, top + 6, 8):
            capsule(img, (x, y), (x, y + 5), 2.4, 2.4, iron if (y // 8) % 2 else iron_light)
            disc(img, x, y + 2.5, 1.0, iron_dark)
    rect(img, 2, top + 4, w - 2, h - 12, wood)
    rect(img, 2, top + 4, w - 2, top + 10, wood_light)
    rect(img, 2, h - 22, w - 2, h - 12, wood_dark)
    rng = random.Random(33)
    for _ in range(14):
        x, y = rng.randint(6, w - 16), rng.randint(top + 14, h - 26)
        rect(img, x, y, x + rng.randint(5, 10), y + 1, wood_dark)
    for x in (10, w - 20, w // 2 - 5):
        rect(img, x, top + 2, x + 10, h - 10, iron)
        rect(img, x, top + 2, x + 3, h - 10, iron_light)
    # 아래로 난 가시가 위험한 면을 알려 준다.
    for x in range(8, w - 8, 12):
        polygon(img, [(x - 5, h - 12), (x + 5, h - 12), (x, h - 1)], iron_light)
        polygon(img, [(x, h - 12), (x + 5, h - 12), (x, h - 1)], iron)
    return outlined(img, hex_color('1a1020'))


def make_boulder():
    """굴러오는 둥근 바위. 돌려 그려도 어색하지 않게 무늬를 고르게 둔다."""
    size = 40
    img = new_frame(size, size)
    c = size / 2
    disc(img, c, c, 18.5, hex_color('6b6577'))
    disc(img, c - 3, c - 3, 13, hex_color('7f778c'))
    disc(img, c - 6, c - 7, 6, hex_color('93899f'))
    dark = hex_color('4a4557')
    for a in range(0, 360, 72):
        p0 = (c + math.cos(math.radians(a)) * 8, c + math.sin(math.radians(a)) * 8)
        p1 = (c + math.cos(math.radians(a + 25)) * 16, c + math.sin(math.radians(a + 25)) * 16)
        capsule(img, p0, p1, 0.8, 0.5, dark)
    for a in range(36, 360, 120):
        disc(img, c + math.cos(math.radians(a)) * 13, c + math.sin(math.radians(a)) * 13, 2.2, dark)
    return outlined(img, hex_color('1a1020'))


def make_rubble():
    """천장에서 떨어지는 성벽 조각. 벽돌 줄눈이 보여 돌과 구분된다."""
    w, h = 40, 36
    img = new_frame(w, h)
    shape = [(1, h - 1), (3, 14), (10, 9), (15, 2), (25, 5), (30, 1), (38, 12), (w - 1, h - 1)]
    polygon(img, shape, hex_color('7d7691'))
    polygon(img, [(20, h - 1), (24, 14), (38, 12), (w - 1, h - 1)], hex_color('5e586e'))
    px = img.load()
    dark = hex_color('3d384c')
    for y in range(h):
        for x in range(w):
            if px[x, y][3] and (y % 9 == 4 or (x + (y // 9) * 7) % 14 == 0):
                px[x, y] = dark
    polygon(img, [(3, 14), (10, 9), (15, 2), (17, 8), (9, 13)], hex_color('a39db4'))
    return outlined(img, hex_color('1a1020'))


def make_castle_obstacles():
    """스테이지 1의 커진 돌과 상자, 새 장애물."""
    save(make_crate(42, 38), 'map/low_crate_big.png')
    save(make_rock(42, 38), 'map/low_rock_big.png')
    save(make_spikes(), 'map/spikes.png')
    save(make_barricade(), 'map/barricade.png')
    save(make_beam(), 'map/beam.png')
    save(make_boulder(), 'map/boulder.png')
    save(make_rubble(), 'map/rubble.png')


def make_pillar():
    w, h = 75, 265
    img = new_frame(w, h)
    px = img.load()
    rng = random.Random(5)
    base, light, dark = hex_color('5e586e'), hex_color('7d7691'), hex_color('3d384c')
    jag = periodic_noise(w, 1, 8, 1, rng)[0]
    for x in range(4, w - 4):
        bottom = h - 1 - int(jag[x] * 9)
        band = (x - 4) // 12
        for y in range(0, bottom):
            color = light if band % 2 == 0 and (x - 4) % 12 < 3 else base
            if (x - 4) % 12 >= 10:
                color = dark
            px[x, y] = color
    # 돌 마디와 금
    for y in range(20, h - 20, 56):
        rect(img, 2, y, w - 2, y + 4, light)
        rect(img, 2, y + 4, w - 2, y + 6, dark)
    for _ in range(5):
        x, y = rng.randint(8, w - 8), rng.randint(30, h - 30)
        for _ in range(rng.randint(8, 18)):
            if px[x, y][3] != 0:
                px[x, y] = dark
            x = max(0, min(w - 1, x + rng.choice((-1, 0, 1))))
            y = min(h - 1, y + 1)
    # 부서진 끝의 가시가 위험한 면을 알려 준다.
    for x in range(8, w - 8, 14):
        polygon(img, [(x - 5, h - 14), (x + 5, h - 14), (x, h - 1)], light)
        polygon(img, [(x, h - 14), (x + 5, h - 14), (x, h - 1)], dark)
    return outlined(img, hex_color('1a1020'))


WALL_W = 60
WALL_H = 300
WALL_CUT_Y = 150
WALL_CUT_SLOPE = 14


def make_wall_pieces():
    """거대 장벽. 대각선으로 잘린 윗부분과 아랫부분을 따로 저장한다."""
    rng = random.Random(9)
    whole = new_frame(WALL_W, WALL_H)
    px = whole.load()
    base, light, dark = hex_color('4a3f6b'), hex_color('6a5b94'), hex_color('2d2548')
    for y in range(WALL_H):
        for x in range(WALL_W):
            row = y // 20
            offset = 10 if row % 2 else 0
            if y % 20 == 0 or (x + offset) % 20 == 0:
                color = dark
            else:
                color = base if rng.random() > 0.08 else light
            px[x, y] = color
    rect(whole, 0, 0, 5, WALL_H, light)
    rect(whole, WALL_W - 5, 0, WALL_W, WALL_H, dark)
    for y in range(16, WALL_H - 16, 34):
        cy = y + 10
        polygon(whole, [(30, cy - 9), (39, cy), (30, cy + 9), (21, cy)], hex_color('2a1450'))
        polygon(whole, [(30, cy - 6), (36, cy), (30, cy + 6), (24, cy)], hex_color('c77dff'))
        polygon(whole, [(30, cy - 3), (33, cy), (30, cy + 3), (27, cy)], hex_color('ffe9ff'))

    def is_top(x, y):
        return y < WALL_CUT_Y + (x - WALL_W / 2) / WALL_W * WALL_CUT_SLOPE * 2

    top = new_frame(WALL_W, WALL_H)
    bottom = new_frame(WALL_W, WALL_H)
    top_px, bottom_px = top.load(), bottom.load()
    for y in range(WALL_H):
        for x in range(WALL_W):
            (top_px if is_top(x, y) else bottom_px)[x, y] = px[x, y]
    top = outlined(top, hex_color('140c22'))
    bottom = outlined(bottom, hex_color('140c22'))
    return whole, top.crop(top.getbbox()), bottom.crop(bottom.getbbox())


def make_wall_seal():
    """장벽을 X자로 묶은 붉은 사슬과 가운데 봉인."""
    img = new_frame(WALL_W, WALL_H)
    dark, glow, core = hex_color('5a1030'), hex_color('ff4a6b'), hex_color('ffe0e6')
    for top in range(0, WALL_H, 70):
        for start, end in (((0, top), (WALL_W, top + 70)), ((WALL_W, top), (0, top + 70))):
            for i in range(10):
                t = i / 9
                x, y = start[0] + (end[0] - start[0]) * t, start[1] + (end[1] - start[1]) * t
                disc(img, x, y, 3.4, dark)
                disc(img, x, y, 2.2 if i % 2 == 0 else 1.2, glow)
    cx, cy = WALL_W / 2, WALL_H / 2
    disc(img, cx, cy, 26, dark)
    disc(img, cx, cy, 22, glow)
    disc(img, cx, cy, 18, dark)
    polygon(img, [(cx, cy - 15), (cx + 12, cy), (cx, cy + 15), (cx - 12, cy)], glow)
    polygon(img, [(cx, cy - 8), (cx + 6, cy), (cx, cy + 8), (cx - 6, cy)], core)
    return img


def make_obstacles():
    save(make_wall_seal(), 'map/wall_seal.png')
    save(make_crate(), 'map/low_crate.png')
    save(make_rock(), 'map/low_rock.png')
    save(make_pillar(), 'map/high_pillar.png')
    # 페이즈 3은 같은 모양을 심연의 붉은 빛으로 물들인다.
    glow = (255, 90, 40)
    save(tinted(make_crate(), glow, 0.32), 'map/low_crate_phase3.png')
    save(tinted(make_rock(), glow, 0.32), 'map/low_rock_phase3.png')
    save(tinted(make_pillar(), glow, 0.32), 'map/high_pillar_phase3.png')
    whole, top, bottom = make_wall_pieces()
    save(top, 'map/wall_top.png')
    save(bottom, 'map/wall_bottom.png')
    tint = (220, 190, 255)
    save(strip([dissolve(whole, amount, 40 + i, tint, 6 + i * 8) for i, amount in enumerate((0.1, 0.3, 0.5, 0.72, 0.9))]), 'map/wall_break.png')


# 차원 관문 ------------------------------------------------------------------

GATE_FRAME_W = 64
GATE_FRAME_H = 300


def make_gate():
    frames = []
    for i in range(6):
        rng = random.Random(100 + i)
        img = new_frame(GATE_FRAME_W, GATE_FRAME_H)
        cx = GATE_FRAME_W / 2
        points = []
        y = 0
        while y < GATE_FRAME_H:
            points.append((cx + rng.uniform(-4, 4), y))
            y += rng.randint(8, 18)
        points.append((cx, GATE_FRAME_H))
        for a, b in zip(points, points[1:]):
            capsule(img, a, b, 15, 15, (70, 30, 150, 120))
        for a, b in zip(points, points[1:]):
            capsule(img, a, b, 9, 9, (140, 80, 240, 200))
        for a, b in zip(points, points[1:]):
            capsule(img, a, b, 4, 4, hex_color('e6d4ff'))
        for a, b in zip(points, points[1:]):
            capsule(img, a, b, 1.6, 1.6, (255, 255, 255, 255))
        for _ in range(26):
            x = rng.randint(4, GATE_FRAME_W - 5)
            y = rng.randint(0, GATE_FRAME_H - 1)
            rect(img, x, y, x + 2, y + 2, hex_color(rng.choice(['ffffff', 'cdb8ff', 'a860ff'])))
        frames.append(img)
    save(strip(frames), 'map/gate.png')
    save(strip([tinted(frame, (255, 70, 30), 0.55) for frame in frames]), 'map/gate_phase3.png')


# 진화의 원석: 빛나는 원석을 두 손으로 받쳐 든 석상 -----------------------------------

ALTAR_W = 80
ALTAR_H = 112


def draw_altar(pulse):
    stone, light, dark = hex_color('6f6a80'), hex_color('a39db4'), hex_color('453f56')
    img = new_frame(ALTAR_W, ALTAR_H)
    cx, base = ALTAR_W / 2, ALTAR_H - 2
    rect(img, cx - 28, base - 10, cx + 28, base, dark)
    rect(img, cx - 28, base - 10, cx - 20, base, stone)
    rect(img, cx - 22, base - 20, cx + 22, base - 10, stone)
    rect(img, cx - 22, base - 20, cx - 15, base - 10, light)
    polygon(img, [(cx - 18, base - 20), (cx + 18, base - 20), (cx + 10, base - 56), (cx - 10, base - 56)], stone)
    polygon(img, [(cx + 18, base - 20), (cx + 6, base - 20), (cx + 4, base - 56), (cx + 10, base - 56)], dark)
    polygon(img, [(cx - 18, base - 20), (cx - 11, base - 20), (cx - 6, base - 56), (cx - 10, base - 56)], light)
    disc(img, cx, base - 62, 8, stone)
    polygon(img, [(cx - 8, base - 62), (cx, base - 75), (cx + 8, base - 62)], stone)
    disc(img, cx + 1, base - 60, 4.5, dark)
    capsule(img, (cx - 10, base - 52), (cx - 15, base - 76), 3.4, 2.6, light)
    capsule(img, (cx + 10, base - 52), (cx + 15, base - 76), 3.4, 2.6, dark)
    img = outlined(img, hex_color('14101e'))

    cy = base - 90 + math.sin(pulse) * 2
    radius = 17 + 2 * math.sin(pulse)
    disc(img, cx, cy, radius, (95, 227, 255, 60))
    disc(img, cx, cy, radius - 5, (95, 227, 255, 110))
    gem = [(cx, cy - 13), (cx + 8, cy - 3), (cx, cy + 12), (cx - 8, cy - 3)]
    polygon(img, gem, hex_color('5fe3ff'))
    polygon(img, [(cx, cy - 13), (cx + 8, cy - 3), (cx, cy + 12)], hex_color('1f8fc8'))
    polygon(img, [(cx - 5, cy - 3), (cx, cy - 10), (cx + 2, cy - 3), (cx, cy + 4)], hex_color('d8fbff'))
    return img


def make_altar():
    save(strip([draw_altar(i / 8 * math.pi * 2) for i in range(8)]), 'map/altar.png')


# UI -----------------------------------------------------------------------

def make_heart(fill, shade, shine):
    img = new_frame(16, 16)
    fill_c, shade_c = hex_color(fill), hex_color(shade)
    disc(img, 4.8, 5.5, 3.8, fill_c)
    disc(img, 11.2, 5.5, 3.8, fill_c)
    polygon(img, [(1.2, 6.5), (14.8, 6.5), (8, 14.5)], fill_c)
    polygon(img, [(8, 14.5), (14.8, 6.5), (11, 9)], shade_c)
    rect(img, 3, 4, 5, 6, hex_color(shine))
    return outlined(img, hex_color('140c1e'))


def make_coin():
    frames = []
    # 옆에서 본 폭이 바뀌어 동전이 도는 것처럼 보인다.
    for half_w in (5.5, 3.5, 1.2, 3.5):
        img = new_frame(14, 14)
        px = img.load()
        for y in range(14):
            for x in range(14):
                d = ((x + 0.5 - 7) / half_w) ** 2 + ((y + 0.5 - 7) / 5.5) ** 2
                if d <= 1:
                    px[x, y] = hex_color('ffe58a') if d < 0.4 else hex_color('f5b82e')
        frames.append(outlined(img, hex_color('5a3a10')))
    save(strip(frames), 'ui/coin.png')


def make_darkness():
    """가운데만 뚫린 어둠. 게임에서 8배로 늘려 화면 어디서든 덮게 그린다."""
    img = new_frame(320, 180)
    px = img.load()
    for y in range(180):
        for x in range(320):
            d = math.hypot(x + 0.5 - 160, y + 0.5 - 90)
            # 경계를 세 단으로 끊어 도트 그림 느낌을 살린다.
            alpha = 0 if d < 22 else 90 if d < 28 else 170 if d < 34 else 240
            px[x, y] = (6, 2, 12, alpha)
    save(img, 'ui/darkness.png')


def make_lock():
    img = new_frame(10, 10)
    rect(img, 1, 4, 9, 10, hex_color('c8c0d8'))
    rect(img, 4, 6, 6, 8, hex_color('2a2238'))
    rect(img, 2, 1, 3, 4, hex_color('8d86a0'))
    rect(img, 7, 1, 8, 4, hex_color('8d86a0'))
    rect(img, 3, 0, 7, 1, hex_color('8d86a0'))
    save(img, 'ui/lock.png')


def make_ui():
    save(make_heart('ef3b52', 'b0213f', 'ffc2c8'), 'ui/heart_full.png')
    save(make_heart('3a3348', '2a2536', '4a4358'), 'ui/heart_empty.png')
    white = new_frame(1, 1)
    white.putpixel((0, 0), (255, 255, 255, 255))
    save(white, 'ui/white.png')
    black = new_frame(1, 1)
    black.putpixel((0, 0), (0, 0, 0, 255))
    save(black, 'ui/black.png')
    warning = new_frame(1, 1)
    warning.putpixel((0, 0), (255, 70, 70, 90))
    save(warning, 'ui/warning.png')


if __name__ == '__main__':
    make_player()
    make_projectiles()
    make_boss()
    make_boss_wave()
    make_witch()
    make_broom_witch()
    make_executor()
    make_platforms()
    make_obstacles()
    make_castle_obstacles()
    make_gate()
    make_altar()
    make_coin()
    make_lock()
    make_darkness()
    make_ui()
