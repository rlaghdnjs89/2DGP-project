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


def tint_all(img, color):
    out = img.copy()
    px = out.load()
    for y in range(out.height):
        for x in range(out.width):
            if px[x, y][3] != 0:
                px[x, y] = color + (255,)
    return out


# 근접병: 녹슨 갑옷을 입은 언데드 병사, 큰 식칼 --------------------------------------

G = {
    'outline': hex_color('1a0f12'),
    'armor': hex_color('77808f'),
    'armor_light': hex_color('b0bac7'),
    'armor_dark': hex_color('464c5c'),
    'cloth': hex_color('8e2f36'),
    'cloth_dark': hex_color('5c1e28'),
    'skin': hex_color('8fae78'),
    'skin_dark': hex_color('5f7f58'),
    'eye': hex_color('ffdf3d'),
    'blade': hex_color('c9ced6'),
    'blade_dark': hex_color('7d8591'),
    'rust': hex_color('a65a2e'),
}

GRUNT_BODY = {
    'thigh': 7.5, 'shin': 7.5, 'torso': 11, 'upper_arm': 7, 'lower_arm': 7,
    'thigh_r': 3.7, 'knee_r': 3.2, 'ankle_r': 2.8, 'arm_r': 3.2, 'hip_r': 5.0, 'chest_r': 6.6, 'head_r': 6,
}


def draw_cleaver(img, hand, angle):
    tip = along(hand, angle, 25)
    base = along(hand, angle, 4)
    back = angle - 90
    capsule(img, along(hand, angle, -3), base, 1.1, 1.1, G['rust'])
    polygon(img, [base, tip, along(tip, back, 6.5), along(base, back, 5)], G['blade'])
    capsule(img, base, tip, 0.5, 0.5, G['armor_light'])
    capsule(img, along(base, back, 5), along(tip, back, 6.5), 0.5, 0.5, G['blade_dark'])


def draw_grunt_head(img, center):
    x, y = center
    disc(img, x, y + 1, 5.6, G['skin'])
    disc(img, x, y - 1.6, 6.4, G['armor'])
    rect(img, x - 7, y - 1, x + 7, y + 1, G['armor_dark'])
    polygon(img, [(x - 6, y - 6), (x - 11, y - 12), (x - 3, y - 8)], G['armor_light'])
    polygon(img, [(x + 3, y - 7), (x + 9, y - 13), (x + 6, y - 5)], G['armor_light'])
    capsule(img, (x - 3, y - 6), (x + 3, y - 6.4), 0.7, 0.7, G['armor_light'])
    rect(img, x + 1.5, y - 0.5, x + 4.5, y + 1.5, G['eye'])
    rect(img, x + 1, y + 3, x + 5, y + 4, G['skin_dark'])


def draw_grunt(pose):
    b = GRUNT_BODY
    img = new_frame()
    hip = resolve_hip(pose, b)
    neck = along(hip, 180 - pose.lean, b['torso'])
    head = along(neck, 180 - pose.lean - pose.tilt, 5.0)
    shoulder_front = along(neck, -pose.lean, 2.5)
    shoulder_back = (shoulder_front[0] - 2.5, shoulder_front[1])

    draw_arm(img, shoulder_back, pose.back_arm, b, G['armor_dark'], G['skin_dark'], G['skin_dark'])
    draw_leg(img, (hip[0] - 1.6, hip[1]), pose.back_leg, b, G['cloth_dark'], G['armor_dark'], G['armor_dark'])
    draw_leg(img, (hip[0] + 1.6, hip[1]), pose.front_leg, b, G['cloth'], G['armor'], G['armor_dark'])

    capsule(img, hip, neck, b['hip_r'], b['chest_r'], G['armor'])
    chest = along(hip, 180 - pose.lean, b['torso'] * 0.6)
    capsule(img, (chest[0] + 1.5, chest[1] - 3), (chest[0] + 2, chest[1] + 2), 1.5, 1.2, G['armor_light'])
    capsule(img, (hip[0] - 5, hip[1]), (hip[0] + 5, hip[1]), 1.6, 1.6, G['cloth'])
    disc(img, shoulder_back[0], shoulder_back[1], 4.2, G['armor_dark'])

    draw_grunt_head(img, head)

    front_hand = along(along(shoulder_front, pose.front_arm[0], b['upper_arm']), pose.front_arm[0] + pose.front_arm[1], b['lower_arm'])
    if pose.weapon is not None:
        draw_cleaver(img, front_hand, pose.weapon)
    draw_arm(img, shoulder_front, pose.front_arm, b, G['armor'], G['skin'], G['skin'])
    disc(img, shoulder_front[0], shoulder_front[1], 4.2, G['armor'])
    capsule(img, (shoulder_front[0] - 2.5, shoulder_front[1] - 2), (shoulder_front[0] + 2.5, shoulder_front[1] - 2), 1.0, 1.0, G['armor_light'])
    return flipped(outlined(img, G['outline']))


def make_grunt():
    run = []
    for i in range(6):
        t = i / 6 * math.pi * 2

        def leg(phase):
            return 2 + 34 * math.cos(phase), -(12 + 66 * max(0, -math.sin(phase)))

        run.append(draw_grunt(Pose(lean=14, tilt=-8, front_leg=leg(t), back_leg=leg(t + math.pi), front_arm=(30 + 10 * math.cos(t), -40),
                                   back_arm=(-10 - 28 * math.cos(t), 50), weapon=120)))
    save(strip(run), 'monster/grunt_run.png')

    stance = {'front_leg': (34, -36), 'back_leg': (-26, -22)}
    windup = [
        draw_grunt(Pose(lean=-10, tilt=8, front_arm=(170, -40), back_arm=(-40, 50), weapon=-156, **stance)),
        draw_grunt(Pose(lean=-14, tilt=10, front_arm=(178, -46), back_arm=(-46, 50), weapon=-166, **stance)),
    ]
    save(strip(windup), 'monster/grunt_windup.png')

    attack = [
        draw_grunt(Pose(lean=22, tilt=-10, front_arm=(112, -10), back_arm=(-58, 30), weapon=98, **stance)),
        draw_grunt(Pose(lean=30, tilt=-12, front_arm=(82, 2), back_arm=(-64, 24), weapon=78, **stance)),
    ]
    save(strip(attack), 'monster/grunt_attack.png')

    recover = [
        draw_grunt(Pose(lean=26, tilt=-14, front_arm=(50, 10), back_arm=(-30, 30), weapon=40, **stance)),
        draw_grunt(Pose(lean=20, tilt=-10, front_arm=(36, 0), back_arm=(-20, 30), weapon=26, **stance)),
    ]
    save(strip(recover), 'monster/grunt_recover.png')

    body = draw_grunt(Pose(lean=-34, tilt=14, front_leg=(46, -40), back_leg=(14, -50), front_arm=(-140, 20), back_arm=(120, 20), weapon=-170))
    tint = (255, 240, 220)
    death = [
        tint_all(body, tint),
        dissolve(body, 0.2, 11, tint, 3),
        dissolve(body, 0.45, 12, (220, 120, 90), 8),
        dissolve(body, 0.7, 13, (160, 70, 70), 14),
        dissolve(body, 0.9, 14, (100, 50, 60), 20),
    ]
    save(strip(death), 'monster/grunt_death.png')


# 사역마: 박쥐 날개를 단 외눈 임프 ---------------------------------------------------

F = {
    'outline': hex_color('140a28'),
    'body': hex_color('8a4fe0'),
    'body_light': hex_color('b98bff'),
    'body_dark': hex_color('5b2fa6'),
    'wing': hex_color('43237f'),
    'wing_light': hex_color('6a3cb8'),
    'eye': hex_color('fff3b0'),
    'pupil': hex_color('e8384f'),
    'horn': hex_color('ffd166'),
}
FAMILIAR_FRAME = 48


def draw_familiar(flap, bob=0):
    size = FAMILIAR_FRAME
    img = new_frame(size, size)
    cx, cy = size / 2, size / 2 + bob
    tip_y = cy - 15 * math.cos(flap) - 1
    mid_y = cy - 7 * math.cos(flap) - 2
    for side in (-1, 1):
        wing = [(cx + side * 6, cy - 4), (cx + side * 14, mid_y - 3), (cx + side * 22, tip_y),
                (cx + side * 18, mid_y + 6), (cx + side * 13, mid_y + 4), (cx + side * 10, cy + 5)]
        polygon(img, wing, F['wing'])
        capsule(img, (cx + side * 7, cy - 3), (cx + side * 14, mid_y - 3), 1.0, 0.8, F['wing_light'])
        capsule(img, (cx + side * 14, mid_y - 3), (cx + side * 21, tip_y), 0.8, 0.5, F['wing_light'])
    capsule(img, (cx, cy + 9), (cx - 4 + 3 * math.sin(flap), cy + 17), 1.5, 0.7, F['body_dark'])
    disc(img, cx, cy, 11, F['body'])
    disc(img, cx - 2.5, cy - 3, 6.5, F['body_light'])
    disc(img, cx - 0.5, cy + 1, 8.5, F['body'])
    polygon(img, [(cx - 7, cy - 8), (cx - 10, cy - 16), (cx - 3, cy - 10)], F['horn'])
    polygon(img, [(cx + 7, cy - 8), (cx + 10, cy - 16), (cx + 3, cy - 10)], F['horn'])
    disc(img, cx - 1, cy, 6, F['eye'])
    disc(img, cx - 2.5, cy + 0.5, 2.6, F['pupil'])
    rect(img, cx - 3.5, cy - 1, cx - 1.5, cy + 0, (255, 255, 255, 255))
    return outlined(img, F['outline'])


def make_familiar():
    frames = [draw_familiar(i / 6 * math.pi * 2, math.sin(i / 6 * math.pi * 2) * -1.2) for i in range(6)]
    save(strip(frames), 'monster/familiar_float.png')
    body = draw_familiar(0)
    death = [
        tint_all(body, (255, 255, 255)),
        dissolve(body, 0.25, 21, (255, 220, 255), 4),
        dissolve(body, 0.5, 22, (210, 140, 255), 10),
        dissolve(body, 0.75, 23, (150, 90, 230), 16),
        dissolve(body, 0.92, 24, (100, 60, 180), 22),
    ]
    save(strip(death), 'monster/familiar_death.png')


# 탄막 마법사: 불꽃 눈의 후드 로브, 구슬 지팡이 ---------------------------------------

M = {
    'outline': hex_color('14081c'),
    'robe': hex_color('b0442e'),
    'robe_light': hex_color('e0703f'),
    'robe_dark': hex_color('6f2530'),
    'hood': hex_color('4a1c34'),
    'face': hex_color('1c0d22'),
    'eye': hex_color('ffe16a'),
    'staff': hex_color('8a6036'),
    'orb': hex_color('ffb347'),
    'orb_core': hex_color('fff3c4'),
    'trim': hex_color('e9b949'),
}


def draw_mage(bob, staff_lift, glow):
    img = new_frame()
    cx, base = CENTER_X, FEET_Y
    hem = base
    waist = base - 22 + bob
    shoulder = base - 34 + bob
    polygon(img, [(cx - 15, hem), (cx + 15, hem), (cx + 8, waist), (cx + 7, shoulder), (cx - 7, shoulder), (cx - 8, waist)], M['robe'])
    polygon(img, [(cx + 15, hem), (cx + 5, hem), (cx + 3, shoulder), (cx + 7, shoulder), (cx + 8, waist)], M['robe_dark'])
    polygon(img, [(cx - 15, hem), (cx - 9, hem), (cx - 5, shoulder), (cx - 7, shoulder), (cx - 8, waist)], M['robe_light'])
    rect(img, cx - 14, hem - 3, cx + 15, hem - 1, M['trim'])
    rect(img, cx - 8, waist, cx + 9, waist + 2, M['trim'])
    head_y = shoulder - 6
    disc(img, cx, head_y, 8, M['hood'])
    polygon(img, [(cx - 8, head_y - 2), (cx - 2, head_y - 16), (cx + 7, head_y - 3)], M['hood'])
    disc(img, cx + 2, head_y + 1, 5, M['face'])
    rect(img, cx + 1, head_y, cx + 3, head_y + 2, M['eye'])
    rect(img, cx + 5, head_y, cx + 7, head_y + 2, M['eye'])

    hand = (cx + 13, shoulder + 7 - staff_lift)
    capsule(img, (cx + 4, shoulder + 3), hand, 2.6, 2.2, M['robe'])
    capsule(img, (hand[0], hand[1] + 15), (hand[0], hand[1] - 18), 1.1, 1.1, M['staff'])
    orb = (hand[0], hand[1] - 22)
    if glow:
        disc(img, orb[0], orb[1], 7.5, mix(M['orb'], (120, 40, 20), 0.6))
    disc(img, orb[0], orb[1], 5, M['orb'])
    disc(img, orb[0], orb[1], 2.5, M['orb_core'])
    return flipped(outlined(img, M['outline']))


def make_mage():
    idle = [draw_mage(math.sin(i / 4 * math.pi * 2) * 1.2, 0, False) for i in range(4)]
    save(strip(idle), 'monster/mage_idle.png')
    cast = [draw_mage(-1, 4, True), draw_mage(-2, 8, True), draw_mage(-1, 8, True)]
    save(strip(cast), 'monster/mage_cast.png')
    body = draw_mage(0, 0, False)
    death = [
        tint_all(body, (255, 240, 210)),
        dissolve(body, 0.2, 31, (255, 200, 150), 4),
        dissolve(body, 0.45, 32, (240, 130, 80), 9),
        dissolve(body, 0.7, 33, (180, 80, 60), 15),
        dissolve(body, 0.9, 34, (110, 50, 60), 21),
    ]
    save(strip(death), 'monster/mage_death.png')

    for name, glow_c, body_c, core_c in (('bullet', 'a8341c', 'ff7a2f', 'fff0b0'), ('bullet_reflected', '1f6fb0', '5fd8ff', 'f0fcff')):
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


# 배경 --------------------------------------------------------------------

BG_W = 640
BG_H = 360
BAYER = ((0, 8, 2, 10), (12, 4, 14, 6), (3, 11, 1, 9), (15, 7, 13, 5))


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


def fbm(w, h, cell, octaves, rng):
    layers = [periodic_noise(w, h, max(4, cell >> i), max(4, cell >> i), rng) for i in range(octaves)]
    weights = [0.5 ** i for i in range(octaves)]
    total = sum(weights)
    return [[sum(layers[i][y][x] * weights[i] for i in range(octaves)) / total for x in range(w)] for y in range(h)]


def streaks(rng):
    """가로로 길게 늘어진 구름 잡음."""
    wide = periodic_noise(BG_W, BG_H, 128, 18, rng)
    thin = periodic_noise(BG_W, BG_H, 40, 8, rng)
    return [[wide[y][x] * 0.7 + thin[y][x] * 0.3 for x in range(BG_W)] for y in range(BG_H)]


def gradient(colors, dither=0.6):
    """위에서 아래로 팔레트를 내려가며 격자 점묘로 띠 사이를 섞는다."""
    img = new_frame(BG_W, BG_H)
    px = img.load()
    palette = [hex_color(c) for c in colors]
    last = len(palette) - 1
    for y in range(BG_H):
        t = y / (BG_H - 1) * last
        for x in range(BG_W):
            threshold = (BAYER[y % 4][x % 4] / 16 - 0.5) * dither
            px[x, y] = palette[max(0, min(last, int(t + threshold + 0.5)))]
    return img


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3)) + (255,)


def add_noise_tone(img, noise, low, color, strength):
    """잡음이 low를 넘는 곳을 color 쪽으로 물들인다. 구름과 성운에 쓴다."""
    px = img.load()
    tone = hex_color(color)
    for y in range(BG_H):
        for x in range(BG_W):
            n = noise[y][x]
            if n > low:
                amount = min(1, (n - low) / (1 - low) * 2.4)
                level = amount * 4 + BAYER[y % 4][x % 4] / 16
                px[x, y] = mix(px[x, y], tone, int(level) / 4 * strength)
    return img


def wrap_x(x):
    return x % BG_W


def stars(img, rng, count, colors, top=0, bottom=BG_H):
    px = img.load()
    for _ in range(count):
        x, y = rng.randrange(BG_W), rng.randrange(top, bottom)
        color = hex_color(rng.choice(colors))
        px[x, y] = color
        if rng.random() < 0.12:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                px[wrap_x(x + dx), min(BG_H - 1, max(0, y + dy))] = mix(color, (0, 0, 0), 0.4)


def skyline(img, rng, base, height_min, height_max, block_min, block_max, color, rim=None, crenel=True, spire_chance=0.4):
    """가로로 이어지는 성곽 실루엣. base는 그림 아래에서 잰 높이다."""
    px = img.load()
    tone = hex_color(color)
    rim_tone = hex_color(rim) if rim else None
    x = 0
    while x < BG_W:
        width = rng.randint(block_min, block_max)
        height = rng.randint(height_min, height_max)
        top = BG_H - base - height
        spire = rng.random() < spire_chance
        for i in range(width):
            column = wrap_x(x + i)
            column_top = top
            if crenel and (i // 3) % 2 == 0:
                column_top += 3
            if spire:
                center = abs(i - width / 2)
                column_top = top - int(max(0, width / 2 - center) * 1.6)
            for y in range(column_top, BG_H):
                px[column, y] = tone
            if rim_tone:
                px[column, column_top] = rim_tone
        # 창문
        for wy in range(top + 6, BG_H - base, 14):
            if width > 8 and rng.random() < 0.5:
                wx = wrap_x(x + rng.randint(2, width - 3))
                for dy in range(3):
                    px[wx, min(BG_H - 1, wy + dy)] = mix(tone, (255, 170, 90), 0.5)
        x += width + rng.randint(0, 6)
    return img


def ruined_wall(rng, color, brick, rim, glow):
    """무너진 성벽 층. 윗면이 부서져 있고 아치 창이 뚫려 뒤가 비친다."""
    img = new_frame(BG_W, BG_H)
    px = img.load()
    edge = periodic_noise(BG_W, 1, 80, 1, rng)[0]
    tone, brick_tone, rim_tone = hex_color(color), hex_color(brick), hex_color(rim)
    # 벽돌 단위로 끊어 산이 아니라 무너진 석벽으로 보이게 한다.
    block_tops = {}
    for block in range(BG_W // 16):
        height = 90 + edge[block * 16] * 120 + rng.randint(-16, 16)
        block_tops[block] = BG_H - int(height // 8) * 8
    tops = [block_tops[x // 16] for x in range(BG_W)]
    for x in range(BG_W):
        for y in range(tops[x], BG_H):
            row = y // 8
            offset = 0 if row % 2 == 0 else 8
            on_line = y % 8 == 0 or (x + offset) % 16 == 0
            px[x, y] = brick_tone if on_line else tone
        px[x, tops[x]] = rim_tone
        px[x, min(BG_H - 1, tops[x] + 1)] = rim_tone
    # 아치 창
    for ax in range(40, BG_W, 96):
        arch_w = 13
        arch_bottom = BG_H - 66
        arch_top = arch_bottom - 44
        if tops[ax] > arch_top - 10:
            continue
        for x in range(ax - arch_w, ax + arch_w + 1):
            dx = abs(x - ax)
            curve = arch_top + int(arch_w - math.sqrt(max(0, arch_w * arch_w - dx * dx)))
            for y in range(curve, arch_bottom):
                px[x, y] = (0, 0, 0, 0)
            px[x, arch_bottom] = rim_tone
        # 횃불로 눈길을 줄 점을 만든다.
        torch_x = ax + 34
        disc(img, torch_x, arch_top + 8, 4, mix(hex_color(glow), tone, 0.55))
        disc(img, torch_x, arch_top + 8, 2, hex_color(glow))
        rect(img, torch_x - 1, arch_top + 10, torch_x + 1, arch_top + 16, brick_tone)
    return img


def floating_rocks(rng, tone):
    """발판으로 착각하지 않도록 윗면이 둥글고 강조 없이 배경에 묻히는 색으로 그린다."""
    img = new_frame(BG_W, BG_H)
    tone_c = hex_color(tone)
    for x0 in range(30, BG_W, 150):
        cx = x0 + rng.randint(-20, 20)
        cy = rng.randint(70, 180)
        half = rng.randint(16, 34)
        depth = rng.randint(16, 34)
        for i in range(-half, half + 1, 2):
            bump = int(math.sqrt(max(0, half * half - i * i)) * 0.5)
            rect(img, cx + i, cy - bump, cx + i + 2, cy + 1, tone_c)
        points = [(cx - half, cy)]
        steps = 6
        for i in range(1, steps):
            t = i / steps
            points.append((cx - half + 2 * half * t, cy + depth * math.sin(t * math.pi) * rng.uniform(0.6, 1.1)))
        points.append((cx + half, cy))
        polygon(img, points, tone_c)
    return img


def rift(img, rng, x, color, core, width=3):
    y = 0
    points = []
    while y < BG_H:
        points.append((x, y))
        x += rng.randint(-9, 9)
        y += rng.randint(10, 28)
    points.append((x, BG_H))
    glow = hex_color(color)
    for a, b in zip(points, points[1:]):
        capsule(img, a, b, width + 2, width + 1, mix(glow, (10, 5, 30), 0.72))
    for a, b in zip(points, points[1:]):
        capsule(img, a, b, width, max(1, width - 1), glow)
    for a, b in zip(points, points[1:]):
        capsule(img, a, b, 1, 1, hex_color(core))


def make_backgrounds():
    rng = random.Random(7)
    sky = gradient(['191733', '241f47', '35275f', '522c6c', '7a3370', 'a8425f', 'd2634b', 'e88a4d'])
    add_noise_tone(sky, streaks(rng), 0.6, 'f0a070', 0.3)
    disc(sky, 460, 190, 34, hex_color('f6c58a'))
    disc(sky, 460, 190, 30, hex_color('fbdca8'))
    skyline(sky, rng, 40, 50, 120, 14, 40, '40285c', crenel=True, spire_chance=0.35)
    skyline(sky, rng, 30, 20, 70, 18, 46, '2c2048', crenel=True, spire_chance=0.2)
    save(sky, 'bg/phase1_far.png')
    save(ruined_wall(rng, '2c2340', '372c50', '5a4876', 'ff9a3d'), 'bg/phase1_near.png')

    void = gradient(['05041a', '0a0728', '120a3a', '1b0e4e', '280f5e', '35106e'])
    noise = fbm(BG_W, BG_H, 80, 4, rng)
    add_noise_tone(void, noise, 0.5, '6a2bb0', 0.55)
    add_noise_tone(void, noise, 0.62, 'b050d8', 0.45)
    stars(void, rng, 260, ['ffffff', 'cdb8ff', '8fd8ff'])
    rift(void, rng, 180, 'a860ff', 'f3e6ff', 3)
    rift(void, rng, 500, '7f45e0', 'd8c2ff', 2)
    save(void, 'bg/phase2_far.png')
    save(floating_rocks(rng, '1a1040'), 'bg/phase2_near.png')


# 지면과 발판 ----------------------------------------------------------------

GROUND_W = 640
GROUND_H = 60


def brick_ground(rng, base, dark, light, mortar, top, top_light, accent=None):
    img = new_frame(GROUND_W, GROUND_H)
    px = img.load()
    colors = [hex_color(base), hex_color(dark), hex_color(light)]
    mortar_c = hex_color(mortar)
    shades = {(i, j): rng.choice(colors) for i in range(GROUND_W // 32 + 1) for j in range(GROUND_H // 10 + 1)}
    for y in range(GROUND_H):
        row = y // 10
        offset = 16 if row % 2 else 0
        for x in range(GROUND_W):
            shifted = (x + offset) % GROUND_W
            if y % 10 == 0 or shifted % 32 == 0:
                color = mortar_c
            else:
                color = shades[(shifted // 32, row)]
            # 아래로 갈수록 어둡게 해 시선이 윗면에 머물게 한다.
            px[x, y] = mix(color, mortar_c, min(0.75, y / GROUND_H))
    top_c, top_l = hex_color(top), hex_color(top_light)
    for x in range(GROUND_W):
        depth = 3 + (rng.random() < 0.3)
        for y in range(depth):
            px[x, y] = top_l if y == 0 else top_c
    if accent:
        accent_c = hex_color(accent)
        for _ in range(14):
            x, y = rng.randrange(GROUND_W), rng.randint(8, 30)
            for _ in range(rng.randint(6, 14)):
                px[x % GROUND_W, min(GROUND_H - 1, y)] = accent_c
                x += rng.choice((-1, 0, 1))
                y += 1
    return img.resize((GROUND_W * 2, GROUND_H * 2), Image.NEAREST)


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


def make_map():
    rng = random.Random(21)
    save(brick_ground(rng, '4f4660', '443c54', '5a506e', '2a2438', '6f8a58', '9ab86f'), 'map/ground_phase1.png')
    save(brick_ground(rng, '453690', '3a2c80', '5040a4', '221a50', '8f78f0', 'e9dcff', accent='a890ff'), 'map/ground_phase2.png')
    platform, cap = make_platform(rng, '8f78f0', 'e9dcff', '55449a', '352a70')
    save(platform, 'map/platform_phase2.png')
    save(cap, 'map/platform_cap_phase2.png')
    platform, cap = make_platform(rng, '6f8a58', '9ab86f', '5a506e', '3a3350')
    save(platform, 'map/platform_phase1.png')
    save(cap, 'map/platform_cap_phase1.png')


# 장애물 --------------------------------------------------------------------

def make_crate():
    img = new_frame(30, 30)
    wood, wood_dark, wood_light, iron = hex_color('a56a33'), hex_color('734521'), hex_color('c98f4e'), hex_color('565a68')
    rect(img, 1, 1, 29, 29, wood)
    for y in (9, 19):
        rect(img, 1, y, 29, y + 1, wood_dark)
    capsule(img, (4, 4), (26, 26), 1.3, 1.3, wood_light)
    capsule(img, (26, 4), (4, 26), 1.0, 1.0, wood_dark)
    rect(img, 1, 1, 29, 4, wood_light)
    rect(img, 1, 26, 29, 29, wood_dark)
    for x, y in ((1, 1), (24, 1), (1, 24), (24, 24)):
        rect(img, x, y, x + 5, y + 5, iron)
    return outlined(img, hex_color('1a1020'))


def make_rock():
    img = new_frame(30, 30)
    polygon(img, [(1, 29), (2, 16), (8, 6), (17, 2), (25, 8), (29, 19), (29, 29)], hex_color('6b6577'))
    polygon(img, [(4, 18), (9, 8), (17, 4), (22, 9), (14, 13)], hex_color('93899f'))
    polygon(img, [(14, 29), (18, 18), (29, 19), (29, 29)], hex_color('4a4557'))
    capsule(img, (9, 19), (14, 24), 0.6, 0.6, hex_color('3a3646'))
    capsule(img, (20, 11), (24, 16), 0.6, 0.6, hex_color('4a4557'))
    return outlined(img, hex_color('1a1020'))


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


def make_obstacles():
    save(make_crate(), 'map/low_crate.png')
    save(make_rock(), 'map/low_rock.png')
    save(make_pillar(), 'map/high_pillar.png')
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


def make_ui():
    save(make_heart('ef3b52', 'b0213f', 'ffc2c8'), 'ui/heart_full.png')
    save(make_heart('3a3348', '2a2536', '4a4358'), 'ui/heart_empty.png')
    white = new_frame(1, 1)
    white.putpixel((0, 0), (255, 255, 255, 255))
    save(white, 'ui/white.png')
    black = new_frame(1, 1)
    black.putpixel((0, 0), (0, 0, 0, 255))
    save(black, 'ui/black.png')


if __name__ == '__main__':
    make_player()
    make_grunt()
    make_familiar()
    make_mage()
    make_backgrounds()
    make_map()
    make_obstacles()
    make_gate()
    make_ui()
