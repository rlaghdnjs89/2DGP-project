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

PHASES = (
    {'name': '무너지는 고성', 'score': 0, 'gravity': 1.0, 'speed': 1.0, 'score_rate': 1,
     'low': ('assets/map/low_crate.png', 'assets/map/low_rock.png'), 'high': 'assets/map/high_pillar.png',
     'gate': 'assets/map/gate.png', 'music': 'bgm_phase1',
     'background': (('assets/bg/phase1_far.png', 0.1), ('assets/bg/phase1_near.png', 0.35)),
     'ground': 'assets/map/ground_phase1.png',
     'platform': 'assets/map/platform_phase1.png', 'platform_cap': 'assets/map/platform_cap_phase1.png'},
    {'name': '무중력 균열', 'score': 3000, 'gravity': 0.5, 'speed': 1.0, 'score_rate': 1,
     'low': ('assets/map/low_crate.png', 'assets/map/low_rock.png'), 'high': 'assets/map/high_pillar.png',
     'gate': 'assets/map/gate.png', 'music': 'bgm_phase2',
     'background': (('assets/bg/phase2_far.png', 0.1), ('assets/bg/phase2_near.png', 0.35)),
     'ground': 'assets/map/ground_phase2.png',
     'platform': 'assets/map/platform_phase2.png', 'platform_cap': 'assets/map/platform_cap_phase2.png'},
    {'name': '폭주하는 심연', 'score': 8000, 'gravity': 1.0, 'speed': 1.5, 'score_rate': 2,
     'low': ('assets/map/low_crate_phase3.png', 'assets/map/low_rock_phase3.png'), 'high': 'assets/map/high_pillar_phase3.png',
     'gate': 'assets/map/gate_phase3.png', 'music': 'bgm_phase3',
     'background': (('assets/bg/phase3_far.png', 0.1), ('assets/bg/phase3_near.png', 0.35)),
     'ground': 'assets/map/ground_phase3.png',
     'platform': 'assets/map/platform_phase3.png', 'platform_cap': 'assets/map/platform_cap_phase3.png'},
)
PHASE_INVINCIBLE_TIME = 1.0
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
CUT_SCORE = 500
CUT_SHAKE_TIME = 0.8
CUT_SHAKE_AMP = 20
# impact-frame 시트 한 칸(320×180)을 화면보다 크게 그려 크게 흔들려도 가장자리가 드러나지 않게 한다.
IMPACT_FRAME_SCALE = 5
# 흑백 번쩍임이 터지는 장면을 오래 가리지 않게 느려진 시간을 감안해 빨리 재생한다.
IMPACT_FRAME_SPEED = 8

WALL_W = 120
# 달린 시간으로 잰다. 보스전 시간은 세지 않는다.
WALL_CYCLE = 30
WALL_WARNING_TIME = 1.5
# 불릿 타임 3초 동안 스크롤 속도 × 0.6초만큼 전진하므로 그보다 멀리서 시작해야 입력할 시간이 다 보장된다 (CT-6).
WALL_ENTRY_TIME = 0.7
CHUNK_F_LENGTH = 2600
WALL_OFFSET = 1900

# 내려찍기를 피하지 않고 베기와 일섬만 쓰면 HP 3칸으로는 이길 수 없는 값이다.
BOSS_HP = 36
BOSS_DASH_DAMAGE = 3
BOSS_SCORE = 500
BOSS_W = 110
BOSS_H = 210
# 일섬 사거리(400)보다 멀리서 보스전을 시작해 카메라가 멈추기 전에는 일섬이 닿지 않게 한다.
BOSS_ENGAGE_GAP = 450
# 보스에 붙어 쓰러뜨려도 장벽까지 Phase 3 스크롤 속도 × 0.6초(360px) 이상 남아 불릿 타임이 다 보장된다 (CT-6).
BOSS_WALL_GAP = 305
BOSS_INTRO_TIME = 1.2
BOSS_WALK_SPEED = 130
BOSS_ATTACK_RANGE = 230
BOSS_RECOVER_TIME = 1.2
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
DASH_MAX_CHARGES = 2
# 2초면 적이 나오는 속도보다 빨리 차서 지상 적의 70~80%를 일섬으로 처치할 수 있어 제한이 약하다.
DASH_RECHARGE_TIME = 4.0
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

# 일섬을 다 쓴 직후에 진입해도 1회가 충전되도록 충전 시간만큼 평지를 둔다 (DS-8).
CLIFF_RUN_UP_TIME = DASH_RECHARGE_TIME
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
# 페이즈 3은 D를 두 번 넣어 마법사 비중을 높인다.
PHASE_CHUNKS = (('A', 'B', 'C', 'D', 'G'), ('E1', 'E2', 'E3'), ('A', 'B', 'C', 'D', 'D', 'G'))

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

GOBLIN_W = 50
# 1단 점프(150)로 여유 있게 넘도록 낮다.
GOBLIN_H = 60
# 웅크리는 동안에도 플레이어가 달려와 가까워지므로, 달려드는 모습이 보일 만큼 멀리서 알아챈다.
GOBLIN_SIGHT = 700
GOBLIN_WINDUP_TIME = 0.5
GOBLIN_CHARGE_SPEED = 650
GOBLIN_SCORE = 150

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
DISTANCE_SCORE_RATE = 10
