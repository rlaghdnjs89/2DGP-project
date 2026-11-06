SCREEN_W = 1280
SCREEN_H = 720
MAX_DT = 0.05
SPRITE_SCALE = 2
# 64칸 스프라이트의 발바닥은 아래에서 4칸 위에 있다. 발 위치에서 그림 중심까지의 높이다.
SPRITE_CENTER_Y = 56

SCROLL_SPEED = 400
GROUND_TOP = 120

PLAYER_W = 60
PLAYER_H = 100
# 일섬 뒤에도 돌아오는 화면 왼쪽 1/4 위치 (DS-6)
PLAYER_SCREEN_X = SCREEN_W / 4
CAMERA_CATCH_UP = 6

JUMP_HEIGHT = 150
TIME_TO_APEX = 0.35
GRAVITY = 2 * JUMP_HEIGHT / TIME_TO_APEX ** 2
JUMP_SPEED = 2 * JUMP_HEIGHT / TIME_TO_APEX
FALL_GRAVITY_RATIO = 1.5
AIR_JUMPS = 1
INPUT_BUFFER = 0.12

SLIDE_MAX_TIME = 1.0
SLIDE_H = PLAYER_H * 0.5

PHASES = (
    {'name': '무너지는 고성', 'score': 0, 'gravity': 1.0,
     'background': (('assets/bg/phase1_far.png', 0.1), ('assets/bg/phase1_near.png', 0.35)),
     'ground': 'assets/map/ground_phase1.png',
     'platform': 'assets/map/platform_phase1.png', 'platform_cap': 'assets/map/platform_cap_phase1.png'},
    {'name': '무중력 균열', 'score': 3000, 'gravity': 0.5,
     'background': (('assets/bg/phase2_far.png', 0.1), ('assets/bg/phase2_near.png', 0.35)),
     'ground': 'assets/map/ground_phase2.png',
     'platform': 'assets/map/platform_phase2.png', 'platform_cap': 'assets/map/platform_cap_phase2.png'},
)
PHASE_INVINCIBLE_TIME = 1.0
GATE_W = 40

GAUGE_MAX = 100
GAUGE_SLASH_KILL = 10
GAUGE_DASH_KILL = 15
BULLET_TIME_SCALE = 0.2
BULLET_TIME_MAX = 3.0
SIMULTANEOUS_WINDOW = 0.15
CUT_TIME = 0.35
CUT_SCORE = 500
CUT_SHAKE_TIME = 0.35
CUT_SHAKE_AMP = 12
# impact-frame 시트 한 칸(320×180)이 화면을 덮는 배율
IMPACT_FRAME_SCALE = 4

WALL_W = 120
# 약 45초마다 장벽이 나오고, 이 주기에 나온 적이 기준보다 적으면 장애물 러시를 후보에서 뺀다.
WALL_CYCLE = 45
WALL_CYCLE_ENEMIES = 12
WALL_WARNING_TIME = 1.5
# 불릿 타임 3초 동안 스크롤 속도 × 0.6초만큼 전진하므로 그보다 멀리서 시작해야 입력할 시간이 다 보장된다 (CT-6).
WALL_ENTRY_TIME = 0.7
CHUNK_F_LENGTH = 2600
WALL_OFFSET = 1900
WALL_MONSTER_OFFSETS = (500, 900, 1250)
WALL_FAMILIAR_HEIGHT = 180

HP_MAX = 3
INVINCIBLE_TIME = 1.5
HIT_STUN_TIME = 0.3
GAME_OVER_TIME = 0.5
GAME_OVER_TIME_SCALE = 0.25

SLASH_TIME = 0.25
# 판정이 살아 있는 시간. 이후 SLASH_TIME까지는 다음 베기를 막는 후딜레이다.
SWORD_TIME = 0.1
SWORD_REACH = 140
SWORD_H = 140

DASH_RANGE = 400
DASH_TIME = 0.15
DASH_COOLDOWN = 2.0
DASH_HANG_TIME = 0.3

CHUNK_A_LENGTH = 2400
CHUNK_B_LENGTH = 2800
# 청크가 이어지는 곳에서도 장애물 간격이 좁아지지 않게 양 끝을 비운다.
CHUNK_MARGIN = 300
OBSTACLE_GAP_MIN = 550
OBSTACLE_GAP_MAX = 750

LOW_OBSTACLE_W = 60
LOW_OBSTACLE_H = 60
HIGH_OBSTACLE_W = 150
# 슬라이딩 높이(50)는 지나가고 서 있는 높이(100)는 부딪힌다.
HIGH_OBSTACLE_CLEARANCE = 70

# 1단 점프 체공 거리는 약 250px, 2단 점프는 약 440px다.
PIT_W_SHORT = 160
PIT_W_LONG = 360
PIT_CHANCE = 0.3

# 일섬을 막 쓴 직후에 진입해도 쿨타임이 돌도록 스크롤 속도 × 2초 이상 평지를 둔다 (DS-8).
CLIFF_RUN_UP = SCROLL_SPEED * 2
CLIFF_W = 1100
# 낭떠러지 시작점 기준 (x, 지면 위 높이). 간격은 사거리 400px 안이다 (DS-7).
CLIFF_FAMILIARS = ((220, 200), (560, 250), (900, 200))

PLATFORM_H = 24
# 청크 E는 건널 수 없는 배치가 나오지 않도록 직접 설계한다 (MP-5). 높이는 모두 지면 위 기준이다.
# 낮은 중력에서 1단 점프는 높이 300px, 평지 기준 체공 거리 약 500px다. 사역마 간격은 사거리 400px 안이다.
ISLAND_CHUNKS = {
    'E1': {
        'length': 2800,
        'pits': ((400, 2100),),
        'platforms': ((700, 1000, 100), (1300, 1600, 220), (1900, 2200, 100)),
        'familiars': ((1150, 300), (1450, 360), (1750, 300), (2350, 200)),
    },
    'E2': {
        'length': 2800,
        'pits': ((500, 1900),),
        'platforms': ((1150, 1850, 60),),
        'familiars': ((680, 220), (1000, 300), (2000, 300), (2300, 220)),
    },
    'E3': {
        'length': 2800,
        'pits': ((300, 2150),),
        'platforms': ((500, 800, 40), (1000, 1250, 260), (1450, 1750, 40), (1950, 2200, 260)),
        'familiars': ((900, 260), (1125, 400), (1350, 280), (1850, 260), (2320, 240)),
    },
}
# 청크 D. x는 청크 시작 기준, 높은 장애물로 슬라이딩을 요구한 뒤 지면과 발판의 마법사를 만난다.
CHUNK_D = {
    'length': 2600,
    'high_obstacle': 500,
    'platforms': ((1500, 1900, 130),),
    'mages': ((1150, 0), (1700, 130)),
}
PHASE_CHUNKS = (('A', 'B', 'C', 'D'), ('E1', 'E2', 'E3'))
# 지면에서 싸우는 페이즈. 나머지 페이즈의 장벽 청크에는 근접병 대신 사역마를 둔다.
GROUND_FIGHT_PHASES = (0,)

GRUNT_W = 60
GRUNT_H = 90
GRUNT_SPEED = 160
GRUNT_SIGHT = 600
GRUNT_ATTACK_RANGE = 240
GRUNT_WINDUP_TIME = 0.25
GRUNT_ATTACK_TIME = 0.15
GRUNT_RECOVER_TIME = 0.4
GRUNT_ATTACK_REACH = 50
# 근접병은 시야에 들어온 뒤 100px쯤 달려오므로 장애물 뒤에 이만큼 비워 착지 자리를 남긴다.
GRUNT_GAP_MIN = 350
GRUNT_GAP_MAX = 450
GRUNT_3RD_CHANCE = 0.5
GRUNT_SCORE = 100

FAMILIAR_SIZE = 56
FAMILIAR_FLOAT = 12
FAMILIAR_FLOAT_SPEED = 2.5
FAMILIAR_SCORE = 150
FAMILIAR_DASH_BONUS = 50

MAGE_W = 60
MAGE_H = 100
MAGE_SIGHT = 900
MAGE_FIRE_INTERVAL = 2.0
MAGE_CAST_TIME = 0.4
# 탄 높이를 슬라이딩 높이(50)보다 위에 두어 슬라이딩으로도 피할 수 있게 한다.
MAGE_MUZZLE_Y = 80
MAGE_SCORE = 200
MAGE_REFLECT_BONUS = 100
BULLET_SPEED = 300
REFLECTED_SPEED = 900
BULLET_SIZE = 28
PARRY_SCORE = 50
GAUGE_PARRY = 5

COMBO_HEAL = 10
DISTANCE_SCORE_RATE = 10
