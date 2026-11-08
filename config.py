SCREEN_W = 1280
SCREEN_H = 720
MAX_DT = 0.05
# pico2d 볼륨은 0~128이다.
MUSIC_VOLUME = 64
# 불릿 타임에는 음악을 줄여 긴장감을 만든다.
MUSIC_VOLUME_DUCK = 20
SFX_VOLUME = 96
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

STAGES = (
    {'name': '무너지는 고성', 'gravity': 1.0, 'speed': 1.0, 'gold_rate': 1,
     'low': ('assets/map/low_crate.png', 'assets/map/low_rock.png'), 'high': 'assets/map/high_pillar.png',
     'gate': 'assets/map/gate.png', 'music': 'bgm_phase1',
     'background': (('assets/bg/phase1_far.png', 0.1), ('assets/bg/phase1_near.png', 0.35)),
     'ground': 'assets/map/ground_phase1.png',
     'platform': 'assets/map/platform_phase1.png', 'platform_cap': 'assets/map/platform_cap_phase1.png', 'arena_platforms': ()},
    {'name': '무중력 균열', 'gravity': 0.5, 'speed': 1.0, 'gold_rate': 1.5,
     'low': ('assets/map/low_crate.png', 'assets/map/low_rock.png'), 'high': 'assets/map/high_pillar.png',
     'gate': 'assets/map/gate.png', 'music': 'bgm_phase2',
     'background': (('assets/bg/phase2_far.png', 0.1), ('assets/bg/phase2_near.png', 0.35)),
     'ground': 'assets/map/ground_phase2.png',
     'platform': 'assets/map/platform_phase2.png', 'platform_cap': 'assets/map/platform_cap_phase2.png',
     # 아레나 시작 기준 (왼쪽, 오른쪽, 지면 위 높이). 카메라가 멈추면 화면 150~370px, 480~720px에 놓인다.
     'arena_platforms': ((375, 595, 130), (705, 945, 250))},
    {'name': '폭주하는 심연', 'gravity': 1.0, 'speed': 1.5, 'gold_rate': 2,
     'low': ('assets/map/low_crate_phase3.png', 'assets/map/low_rock_phase3.png'), 'high': 'assets/map/high_pillar_phase3.png',
     'gate': 'assets/map/gate_phase3.png', 'music': 'bgm_phase3',
     'background': (('assets/bg/phase3_far.png', 0.1), ('assets/bg/phase3_near.png', 0.35)),
     'ground': 'assets/map/ground_phase3.png',
     'platform': 'assets/map/platform_phase3.png', 'platform_cap': 'assets/map/platform_cap_phase3.png', 'arena_platforms': ()},
)
STAGE_INVINCIBLE_TIME = 1.0
# 달린 시간으로 잰다. 보스전 시간은 세지 않는다.
STAGE_RUN_TIME = 90
GATE_W = 40

BULLET_TIME_SCALE = 0.2
BULLET_TIME_MAX = 3.0
SIMULTANEOUS_WINDOW = 0.15
# 힘을 모으는 시간은 charge-up 이펙트가 터지는 시점(meta.pixelfx.act.hits[0].t)을 쓴다.
CUT_FX_SCALE = 3
CUT_RUMBLE_AMP = 5
CUT_DIM_OPACITY = 0.7
# implosion 시트에서 빛이 터지는 시점(초). 힘을 다 모으는 순간에 맞춰 재생 속도를 정한다.
IMPLOSION_POP_TIME = 1.0
# 터진 뒤 이 시간 동안 0.15배속에서 원래 속도로 서서히 돌아온다.
CUT_AFTER_TIME = 0.9
CUT_AFTER_SCALE = 0.15
CUT_SHAKE_TIME = 0.8
CUT_SHAKE_AMP = 20
# impact-frame 시트 한 칸(320×180)을 화면보다 크게 그려 크게 흔들려도 가장자리가 드러나지 않게 한다.
IMPACT_FRAME_SCALE = 5
# 흑백 번쩍임이 터지는 장면을 오래 가리지 않게 느려진 시간을 감안해 빨리 재생한다.
IMPACT_FRAME_SPEED = 8

WALL_W = 120
WALL_WARNING_TIME = 1.5
# 불릿 타임 3초 동안 스크롤 속도 × 0.6초만큼 전진하므로 그보다 멀리서 시작해야 입력할 시간이 다 보장된다 (CT-6).
WALL_ENTRY_TIME = 0.7
ARENA_LENGTH = 2000
ARENA_WALL_OFFSET = 1300

ALTAR_CHUNK_LENGTH = 2200
# 원석이 화면에 들어올 때(플레이어 앞 960px) 앞 청크의 적이 모두 뒤에 있도록 청크 안쪽 깊이 둔다.
ALTAR_OFFSET = 1300
ALTAR_STOP_GAP = 130
ALTAR_SLOW_DISTANCE = 830
ALTAR_MIN_SPEED_RATIO = 0.15
ALTAR_COUNTDOWN = 3

# 내려찍기를 피하지 않고 베기와 일섬만 쓰면 HP 3칸으로는 이길 수 없는 값이다.
BOSS_HP = 600
# 스테이지 순서다. 처음 쓰러뜨릴 때와 다시 쓰러뜨릴 때의 골드.
BOSS_FIRST_GOLD = (200, 400, 800)
BOSS_REPEAT_GOLD = (100, 200, 400)
# 일섬 피해는 베기의 3배다.
DASH_DAMAGE_RATIO = 3
BOSS_W = 110
BOSS_H = 210
# 일섬 사거리(400)보다 멀리서 보스전을 시작해 카메라가 멈추기 전에는 일섬이 닿지 않게 한다.
BOSS_ENGAGE_GAP = 450
# 보스에 붙어 쓰러뜨려도 장벽까지 스테이지 3 스크롤 속도 × 0.6초(360px) 이상 남아 불릿 타임이 다 보장된다 (CT-6).
BOSS_WALL_GAP = 305
BOSS_INTRO_TIME = 1.2
BOSS_WALK_SPEED = 130
BOSS_ATTACK_RANGE = 230
BOSS_RECOVER_TIME = 1.2
# 첫 파동을 1단 점프로 넘으면 착지할 무렵 둘째 파동이 와 공중 점프를 써야 한다.
BOSS_WAVE_WINDUP = 0.6
BOSS_WAVE_INTERVAL = 0.55
BOSS_WAVE_RECOVER = 0.8
BOSS_WAVE_SPEED = 520
BOSS_WAVE_W = 50
BOSS_WAVE_H = 70
BOSS_WAVE_FX_SPEED = 1.5
BOSS_RAGE_HP_RATIO = 0.5
BOSS_RAGE_SPEED = 1.3
# nature/boulder 시트의 바위가 날아가 바닥에 부딪히는 시점과 기준점에서 떨어진 거리(시트 픽셀)다.
ROCK_WARNING_TIME = 0.6
ROCK_ARC_X = 113
ROCK_SPREAD = 240
ROCK_W = 120
ROCK_H = 170
BOSS_GUARD_TIME = 2
BOSS_GROGGY_TIME = 2
BOSS_GROGGY_DAMAGE_RATE = 1.5
# 빈틈(내려찍기 뒤, 그로기) 밖에서는 갑옷이 피해를 줄인다. 초당 4번 베기만 반복하면 강화 없이도 10초 안에 끝나기 때문이다.
BOSS_ARMOR_DAMAGE_RATE = 0.4
BOSS_BLOCK_FX_SCALE = 3
BOSS_BLOCK_HIT_STOP = 0.06
BOSS_BLOCK_SHAKE_TIME = 0.12
BOSS_BLOCK_SHAKE_AMP = 4
# 내려찍기 판정. 높이는 1단 점프(150)로 넘을 수 있고, 뒤로 물러나 피할 수도 있다.
BOSS_STRIKE_TIME = 0.12
BOSS_STRIKE_REACH = 340
BOSS_STRIKE_H = 110
BOSS_STRIKE_WARNING_COLOR = (255, 70, 70)
BOSS_FX_SCALE = 4
# heavy-cleave의 멈춤 수치는 그대로 쓰면 내려찍을 때마다 흐름이 끊겨 줄여 쓴다.
BOSS_HIT_STOP_RATIO = 0.5
BOSS_FLASH_TIME = 0.08
BOSS_DEATH_FX_SCALE = 3
BOSS_DEATH_HIT_STOP = 0.2
BOSS_DEATH_SHAKE_TIME = 0.5
BOSS_DEATH_SHAKE_AMP = 14
BOSS_FIGHT_MOVE_SPEED = 360
# 충돌 판정이 경계를 포함하므로 맞닿지 않게 띄운다.
BOSS_CONTACT_GAP = 2

EXEC_HP = 1600
EXEC_W = 100
EXEC_H = 190
EXEC_WALK_SPEED = 260
EXEC_ATTACK_RANGE = 260
EXEC_RECOVER_TIME = 1.0
EXEC_GROGGY_TIME = 2
EXEC_GROGGY_DAMAGE_RATE = 1.5
# 수문장과 같은 이유로 빈틈(3연격 뒤, 그로기) 밖에서는 갑옷이 피해를 줄인다.
EXEC_ARMOR_DAMAGE_RATE = 0.3
# 낮은 베기를 점프로 넘고 착지(0.49초)한 뒤 슬라이딩으로 높은 베기를 피할 수 있는 간격이다.
EXEC_STRIKE_WINDUP = 0.55
EXEC_SWING_TIME = 0.12
EXEC_STRIKE_REACH = 320
EXEC_LOW_H = 90
# 슬라이딩 높이(50)보다 위라 슬라이딩으로만 지나갈 수 있다.
EXEC_HIGH_BOTTOM = 60
EXEC_HIGH_TOP = 300
EXEC_STRIKE_FX_SCALE = 4
EXEC_STRIKE_FX_SPEED = 2
EXEC_THROW_WINDUP = 0.6
EXEC_THROW_AFTER = 0.5
EXEC_SWORD_SPEED = 650
EXEC_MUZZLE_Y = 110
EXEC_DUEL_HP_RATIO = 0.2
EXEC_DUEL_DAMAGE_RATIO = 0.1
EXEC_ECLIPSE_HP_RATIO = 0.5
EXEC_CLONE_X = 110
EXEC_CLONE_OPACITY = 0.55
EXEC_PILLAR_WINDUP = 0.4
EXEC_PILLAR_AFTER = 0.8
# flame-pillar 시트의 불기둥이 솟는 시점에 맞춘 경고 시간이다. 불기둥이 잦아들기 전까지 맞는다.
EXEC_PILLAR_WARNING = 0.6
EXEC_PILLAR_HIT_TIME = 0.5
EXEC_PILLAR_SPREAD = 300
EXEC_PILLAR_W = 110
EXEC_PILLAR_H = 420

WITCH_HP = 1000
WITCH_W = 90
WITCH_H = 170
WITCH_IDLE_TIME = 0.45
# 시작 위치에서 잰 순간이동 자리. 처음 자리가 화면 770px쯤이고 오른쪽 장벽은 1075px이다.
WITCH_ANCHOR_X = (0, 130, 240)
# 지면 위 높이. 땅에서 베면 닿지 않고, 저중력 점프(300px)나 발판에서는 닿는다.
WITCH_ANCHOR_Y = (170, 300, 430)
WITCH_MUZZLE_Y = 110
# 플레이어가 코앞에 있으면 그 자리로는 순간이동하지 않는다. 플레이어가 마녀를 넘어가지 못하는 규칙 때문이다.
WITCH_TELEPORT_GAP = 150
WITCH_TELEPORT_TIME = 0.5
WITCH_FAN_WINDUP = 0.6
WITCH_FAN_SPREAD = 0.28
WITCH_BULLET_SPEED = 420
WITCH_REFLECT_DAMAGE_RATIO = 3
# 저중력에서는 점프해 붙어 베기만 반복해도 10초 안에 끝나므로, 반사 탄과 일섬이 주된 공격 수단이 되게 베기를 줄인다.
WITCH_SLASH_DAMAGE_RATE = 0.2
# 이만큼 베이면 다음 행동 대신 바로 순간이동해 거리를 벌린다.
WITCH_ESCAPE_HITS = 2
WITCH_SUMMON_WINDUP = 0.6
# 마녀 기준 x, 지면 위 높이. 땅에서 마녀 쪽으로 올라가는 계단이라 일섬(사거리 400px)으로 밟아 이어 갈 수 있다.
WITCH_SUMMON_SPOTS = ((-330, 190), (-210, 300), (-90, 410))
WITCH_HOLE_HP_RATIO = 0.5
WITCH_HOLE_WINDUP = 0.6
WITCH_HOLE_TIME = 3
# 플레이어의 보스전 이동 속도(360)보다 느려 A, D로 버틸 수 있다.
WITCH_HOLE_PULL = 230
WITCH_HOLE_RADIUS = 40
WITCH_HOLE_H = 120
BLINK_FX_SPEED = 3
BLINK_FX_SCALE = 3

# 5단계 능력치의 공통 비용이다. 초반은 첫 모음으로 바로 살 수 있게 싸고 후반으로 갈수록 비싸다.
STAT_COSTS = (40, 80, 140, 220, 320)
STATS = {
    'hp': {'name': '체력', 'effect': '최대 HP +1', 'base': 3, 'step': 1, 'costs': (80, 200, 400), 'format': '{:.0f}칸'},
    'attack': {'name': '공격력', 'effect': '보스에게 주는 베기 피해 +3', 'base': 10, 'step': 3, 'costs': STAT_COSTS, 'format': '{:.0f}'},
    'attack_speed': {'name': '공격 속도', 'effect': '베기 후딜레이 -0.02초', 'base': 0.25, 'step': -0.02, 'costs': STAT_COSTS, 'format': '{:.2f}초'},
    'dash_recharge': {'name': '일섬 충전', 'effect': '충전 시간 -0.4초', 'base': 4.0, 'step': -0.4, 'costs': STAT_COSTS, 'format': '{:.1f}초'},
    'gold_gain': {'name': '골드 획득', 'effect': '얻는 골드 +10%', 'base': 0, 'step': 0.1, 'costs': STAT_COSTS, 'format': '+{:.0%}'},
}

# 갈래마다 1단계는 처음부터, 2단계는 보스 1 처치 후, 3단계는 보스 2 처치 후에 열린다.
# slot은 같은 단계에 노드가 둘일 때 위아래 자리다.
SKILLS = {
    'spin': {'name': '회전 베기', 'branch': 'sword', 'tier': 1, 'slot': 0, 'cost': 150, 'desc': '공중에서 베면 몸 둘레 전체에 판정이 생겨 위아래 사역마도 벤다.'},
    'thrust': {'name': '찌르기', 'branch': 'sword', 'tier': 1, 'slot': 1, 'cost': 200, 'desc': '베기 사거리가 140px에서 220px로 늘어난다.'},
    'charge': {'name': '일섬 충전 +1', 'branch': 'move', 'tier': 1, 'slot': 0, 'cost': 250, 'desc': '일섬 최대 충전이 2회에서 3회로 늘어난다.'},
    'dive': {'name': '급강하', 'branch': 'move', 'tier': 1, 'slot': 1, 'cost': 200, 'desc': '공중에서 S로 수직 낙하한다. 착지 충격파(좌우 150px)로 지상 적을 처치하고, 보스에게는 베기 2배 피해를 준다.'},
    'triple': {'name': '3연격', 'branch': 'sword', 'tier': 2, 'slot': 0, 'cost': 400, 'desc': '0.6초 안에 세 번 베면 세 번째가 피해 3배와 넉백을 준다.'},
    'blink': {'name': '점멸', 'branch': 'move', 'tier': 2, 'slot': 0, 'cost': 400, 'desc': '일섬 대상이 없으면 앞으로 200px 순간이동한다. 충전을 1회 쓰며 낭떠러지 보험이 된다.'},
    'fire1': {'name': '화염 베기', 'branch': 'fire', 'tier': 1, 'slot': 0, 'cost': 250, 'desc': '보스에게 화상을 입힌다. 3초 동안 초당 공격력의 30% 피해를 주며 방패와 갑옷을 무시한다.'},
    'ice1': {'name': '서리 베기', 'branch': 'ice', 'tier': 1, 'slot': 0, 'cost': 250, 'desc': '보스를 5번 벨 때마다 2초 동안 보스의 동작이 0.7배속이 된다.'},
    'bolt1': {'name': '감전 베기', 'branch': 'bolt', 'tier': 1, 'slot': 0, 'cost': 250, 'desc': '보스를 벨 때 25% 확률로 번개가 떨어져 공격력의 50% 피해를 추가로 준다.'},
    'fire2': {'name': '시체 폭발', 'branch': 'fire', 'tier': 2, 'slot': 0, 'cost': 400, 'desc': '처치한 적이 터져 반경 120px 안의 적을 처치한다.'},
    'ice2': {'name': '얼음 파편', 'branch': 'ice', 'tier': 2, 'slot': 0, 'cost': 400, 'desc': '처치한 적이 깨지며 파편 3개가 앞으로 날아가 적을 처치한다.'},
    'bolt2': {'name': '연쇄 번개', 'branch': 'bolt', 'tier': 2, 'slot': 0, 'cost': 400, 'desc': '처치하면 가장 가까운 적 1마리에게 번개가 튀어 처치한다. 연쇄된다.'},
}
BRANCH_NAMES = {'sword': '검술', 'move': '기동', 'fire': '화염', 'ice': '빙결', 'bolt': '번개'}
ELEMENTS = ('fire', 'ice', 'bolt')
ELEMENT_CHANGE_COST = 300
CORPSE_RADIUS = 120
CORPSE_FX_SPEED = 3
CORPSE_FX_SCALE = 1
SHARD_ANGLES = (-18, 0, 18)
SHARD_SPEED = 800
SHARD_LIFE = 0.7
SHATTER_FX_SPEED = 2.5
SHATTER_FX_SCALE = 1
# 끝없이 번지면 화면의 적이 한 번에 사라지므로 닿는 거리를 둔다.
CHAIN_RANGE = 450
CHAIN_DELAY = 0.1
BURN_TIME = 3
BURN_DAMAGE_RATIO = 0.3
FROST_HITS = 5
FROST_SLOW_TIME = 2
FROST_SLOW_RATE = 0.7
ZAP_CHANCE = 0.25
ZAP_DAMAGE_RATIO = 0.5
# status 시트는 기본 캐릭터(24×38) 기준이다. 화상은 보스 몸집에 맞춰 키우고, 둔화 시계는 몸을 가리지 않게 머리 위에 작게 띄운다.
STATUS_FX = {'burning': {'scale': 5, 'y': 0}, 'slowed': {'scale': 3, 'y': 120}}

INVINCIBLE_TIME = 1.5
HIT_STUN_TIME = 0.3
GAME_OVER_TIME = 0.5
GAME_OVER_TIME_SCALE = 0.25
# 마지막 보스가 쓰러지는 장면을 보여 준 뒤 결과 화면으로 넘어간다.
CLEAR_TIME = 1.5

# 판정이 살아 있는 시간. 이후 공격 속도 능력치의 시간까지는 다음 베기를 막는 후딜레이다.
SWORD_TIME = 0.1
SWORD_REACH = 140
SWORD_H = 140
THRUST_REACH = 220
TRIPLE_WINDOW = 0.6
TRIPLE_DAMAGE_RATIO = 3
TRIPLE_KNOCKBACK = 70
BLINK_DISTANCE = 200
SPIN_RADIUS = 130

DASH_RANGE = 400
DASH_TIME = 0.15
DASH_MAX_CHARGES = 2
DASH_HANG_TIME = 0.3
DIVE_SPEED = 1400
DIVE_REACH = 150
DIVE_BOSS_DAMAGE_RATIO = 2
DIVE_HIT_STOP = 0.06
DIVE_SHAKE_TIME = 0.25
DIVE_SHAKE_AMP = 9

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

# 일섬을 다 쓴 직후에 진입해도 1회가 충전되도록 충전 시간만큼 평지를 둔다 (DS-8).
CLIFF_RUN_UP_TIME = STATS['dash_recharge']['base']
# 평지가 보장하는 일섬 1회와 공중 점프로 건널 수 있는 폭이다. 2단 점프만으로는 못 건넌다.
CLIFF_W = 600
# 낭떠러지 시작점 기준 (x, 지면 위 높이). 간격은 사거리 400px 안이다 (DS-7).
# 두 번째는 공중 점프 궤적 위에 두어, 일섬 1회로 건널 때 부딪히지 않고 2회를 아낀 플레이어만 베러 올라간다.
CLIFF_FAMILIARS = ((220, 200), (450, 450))

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
# 청크 G. 고블린이 한 마리씩 달려들도록 고블린 시야보다 넓게 띄운다.
CHUNK_G = {
    'length': 2700,
    'goblins': (700, 1500, 2300),
}
# 스테이지 3은 D를 두 번 넣어 마법사 비중을 높인다.
STAGE_CHUNKS = (('A', 'B', 'C', 'D', 'G'), ('E1', 'E2', 'E3'), ('A', 'B', 'C', 'D', 'D', 'G'))

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
GRUNT_GOLD = 5

GOBLIN_W = 50
# 1단 점프(150)로 여유 있게 넘도록 낮다.
GOBLIN_H = 60
# 웅크리는 동안에도 플레이어가 달려와 가까워지므로, 달려드는 모습이 보일 만큼 멀리서 알아챈다.
GOBLIN_SIGHT = 700
GOBLIN_WINDUP_TIME = 0.5
GOBLIN_CHARGE_SPEED = 650
GOBLIN_GOLD = 7

FAMILIAR_SIZE = 56
FAMILIAR_FLOAT = 12
FAMILIAR_FLOAT_SPEED = 2.5
FAMILIAR_GOLD = 6
FAMILIAR_DASH_BONUS = 2

MAGE_W = 60
MAGE_H = 100
MAGE_SIGHT = 900
MAGE_FIRE_INTERVAL = 2.0
MAGE_CAST_TIME = 0.4
# 탄 높이를 슬라이딩 높이(50)보다 위에 두어 슬라이딩으로도 피할 수 있게 한다.
MAGE_MUZZLE_Y = 80
MAGE_GOLD = 10
MAGE_REFLECT_BONUS = 5
BULLET_SPEED = 300
REFLECTED_SPEED = 900
BULLET_SIZE = 28
PARRY_GOLD = 1

# 베기 처치의 멈춤과 흔들림은 pixelfx sword-slash의 수치를 쓴다. 그 값은 서 있는 캐릭터 기준이라
# 계속 달리는 게임에서 그대로 쓰면 흐름이 끊겨 줄여 쓴다.
SLASH_HIT_STOP_RATIO = 0.5
DASH_HIT_STOP = 0.05
DASH_SHAKE_TIME = 0.14
DASH_SHAKE_AMP = 5
HURT_HIT_STOP = 0.1
HURT_SHAKE_TIME = 0.25
HURT_SHAKE_AMP = 7
CUT_HIT_STOP = 0.2
KNOCKBACK_SPEED = 500
BLINK_HZ = 12
BLINK_OPACITY = 0.35
TRAIL_TIME = 0.14
TRAIL_OPACITY = 0.45

COMBO_HEAL = 10

# 처치 한 번에 튀어나오는 동전의 최대 개수. 골드 액수와 상관없이 화면이 동전으로 덮이지 않게 한다.
COIN_MAX = 12
COIN_POP_TIME = 0.4
COIN_POP_SPEED_X = 220
COIN_POP_SPEED_Y = 460
COIN_GRAVITY = 1400
COIN_ABSORB_SPEED = 900
COIN_ABSORB_ACCEL = 4000
