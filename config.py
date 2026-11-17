SCREEN_W = 1280
SCREEN_H = 720
MAX_DT = 0.05
# pico2d 볼륨은 0~128이다.
SFX_VOLUME = 96
SPRITE_SCALE = 2

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
    # pattern_tiers는 달린 비율이 앞 값을 넘으면 그 등급에서 조각을 고른다. 없으면 직접 설계한 군도를 쓴다.
    # pattern_gap은 조각과 조각 사이의 빈 거리(px, 최소와 최대)다. 줄이면 쉴 틈이 줄어든다.
    # cliff_run_up은 낭떠러지 앞 평지에 까는 조각의 등급이다. None이면 평지를 비워 둔다.
    {'name': '무너지는 고성', 'gravity': 1.0, 'speed': 1.25, 'gold_rate': 1,
     'pattern_tiers': ((0, ('easy',)), (0.1, ('easy', 'castle')), (0.3, ('castle',)), (0.55, ('castle', 'castle_rush')), (0.8, ('castle_rush',))),
     'pattern_gap': (260, 340), 'cliff_run_up': 'run_up',
     'low': ('assets/map/low_crate_big.png', 'assets/map/low_rock_big.png'), 'low_size': (84, 76), 'high': 'assets/map/high_pillar.png',
     'gate': 'assets/map/gate.png',
     'background': (('assets/bg/phase1_far.png', 0.1), ('assets/bg/phase1_near.png', 0.35)),
     'ground': 'assets/map/ground_phase1.png',
     'platform': 'assets/map/platform_phase1.png', 'platform_cap': 'assets/map/platform_cap_phase1.png', 'arena_platforms': ()},
    {'name': '무중력 균열', 'gravity': 0.6, 'speed': 1.25, 'gold_rate': 1.5,
     'pattern_tiers': (), 'pattern_gap': (420, 600), 'cliff_run_up': None,
     'low': ('assets/map/low_crate.png', 'assets/map/low_rock.png'), 'low_size': (60, 60), 'high': 'assets/map/high_pillar.png',
     'gate': 'assets/map/gate.png',
     'background': (('assets/bg/phase2_far.png', 0.1), ('assets/bg/phase2_near.png', 0.35)),
     'ground': 'assets/map/ground_phase2.png',
     'platform': 'assets/map/platform_phase2.png', 'platform_cap': 'assets/map/platform_cap_phase2.png',
     # 아레나 시작 기준 (왼쪽, 오른쪽, 지면 위 높이). 카메라가 멈추면 화면 150~370px, 480~720px에 놓인다.
     'arena_platforms': ((375, 595, 130), (705, 945, 250))},
    {'name': '폭주하는 심연', 'gravity': 1.0, 'speed': 1.75, 'gold_rate': 2,
     'pattern_tiers': ((0, ('normal',)), (0.3, ('normal', 'hard')), (0.65, ('hard',))),
     'pattern_gap': (420, 600), 'cliff_run_up': None,
     'low': ('assets/map/low_crate_phase3.png', 'assets/map/low_rock_phase3.png'), 'low_size': (60, 60), 'high': 'assets/map/high_pillar_phase3.png',
     'gate': 'assets/map/gate_phase3.png',
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
# 보스에 붙어 쓰러뜨려도 장벽까지 장벽이 있는 스테이지 1, 2의 스크롤 속도 × 0.6초(300px) 이상 남아 불릿 타임이 다 보장된다 (CT-6).
BOSS_WALL_GAP = 305
BOSS_INTRO_TIME = 1.2
BOSS_WALK_SPEED = 130
BOSS_ATTACK_RANGE = 230
BOSS_RECOVER_TIME = 1.2
# 공격 준비 동작 동안 흰 몸을 겹쳐 그려 빛나게 한다.
BOSS_GLOW_OPACITY = 0.5
BOSS_GLOW_SPEED = 18
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
# 보스 몸통은 뚫지 못하고, 2단 점프로 머리보다 높이 뛰면 넘어갈 수 있다. 머리 위에 떨어지면 A, D를 누르지 않는 동안 가까운 쪽으로 미끄러져 내려온다.
BOSS_SLIDE_SPEED = 400

EXEC_HP = 1600
EXEC_W = 100
EXEC_H = 190
EXEC_WALK_SPEED = 340
EXEC_ATTACK_RANGE = 260
EXEC_RECOVER_TIME = 0.5
EXEC_GROGGY_TIME = 2
# 수문장과 같은 이유로 빈틈(3연격 뒤, 그로기) 밖에서는 갑옷이 피해를 줄인다.
EXEC_ARMOR_DAMAGE_RATE = 0.1
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
EXEC_THROW_AFTER = 0.2
EXEC_SWORD_SPEED = 650
EXEC_MUZZLE_Y = 110
EXEC_DUEL_HP_RATIO = 0.2
EXEC_DUEL_DAMAGE_RATIO = 0.1
EXEC_ECLIPSE_HP_RATIO = 0.5
EXEC_CLONE_X = 110
EXEC_CLONE_OPACITY = 0.55
EXEC_PILLAR_WINDUP = 0.4
EXEC_PILLAR_AFTER = 0.4
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
# 지면 위 높이. 땅에서 베면 닿지 않고, 저중력 점프(250px)나 발판에서는 닿는다.
WITCH_ANCHOR_Y = (170, 300, 430)
WITCH_MUZZLE_Y = 110
# 플레이어와 가로로 이만큼 떨어진 자리로만 순간이동한다. 플레이어 바로 위나 옆에 나타나 몸통이 겹치지 않게 한다.
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

# 스테이지 2의 중간 보스 '빗자루 마녀'. 달리기 구간을 이 비율만큼 달리면 나타난다.
# 버티는 동안에는 벨 수 없다. MIDBOSS_TIME초를 버티면 반격 단계가 열리고, 튕겨 낸 탄에 맞아 기절한 마녀를 불릿 타임에 좌+우 동시 클릭으로 베어 쓰러뜨린다.
# 놓치면 마녀는 달아난다. 버티는 시간은 달린 시간에 넣지 않는다.
MIDBOSS_STAGE = 1
MIDBOSS_PROGRESS = 0.5
MIDBOSS_TIME = 35
# 개발자 테스트의 '마녀 격파'는 버틸 시간을 이만큼만 남기고 시작한다.
MIDBOSS_DEV_END_TIME = 3
# 마녀를 벤 플레이어가 마녀 중심에서 이만큼 지나간 자리에 선다.
BROOM_CUT_PASS = 90
MIDBOSS_INTRO_TIME = 1.5
MIDBOSS_LEAVE_TIME = 1.2
# 중간 보스전 동안은 중력이 사라져 마우스 커서를 따라 화면 안을 날아다닌다. 커서로 곧장 옮기면 장벽을 건너뛰므로 이 속도로 따라간다.
FLY_SPEED = 600
# 마녀 앞까지만 날 수 있다. 오른쪽에서 들어오는 장벽과 파편이 닿기 전에 볼 시간이 남는다.
FLY_MAX_SCREEN_X = SCREEN_W - 290
# 탄막 사이를 빠져나갈 수 있도록 비행 중에는 몸 가운데만 맞는다.
FLY_HITBOX_W = 36
FLY_HITBOX_H = 60
# 버틸 시간이 절반 남으면 공격이 거세진다. 아래에서 값이 둘인 것은 (전반, 후반)이다.
MIDBOSS_RAGE_RATIO = 0.5
# 공격과 공격 사이에 쉬는 시간. 전기 장벽과 전기장은 겹치면 피할 길이 없어 하나씩만 나온다.
MIDBOSS_WAVE_REST = (1.0, 0.3)
MIDBOSS_FIRST_WAVE = 1.0
BROOM_SCREEN_X = SCREEN_W - 150
BROOM_HOVER_Y = 420
BROOM_HOVER_AMP = 180
BROOM_HOVER_SPEED = 0.8
# 마녀 그림의 중심에서 잰 손의 위치다.
BROOM_MUZZLE_X = -44
BROOM_MUZZLE_Y = 22
# 마녀는 다른 공격이 나오는 동안에도 이 간격(최소, 최대)으로 탄을 쏜다. 쏘기 전 BROOM_CAST_TIME초 동안 손이 빛난다.
BROOM_SHOT_INTERVAL = ((1.4, 2.2), (0.9, 1.5))
BROOM_CAST_TIME = 0.35
BROOM_SHOT_SPEED = 340
# 부채꼴 탄. 플레이어를 겨눈 탄을 가운데 두고 퍼진다. 500px 거리에서 탄 사이가 100px로, 비행 판정(60px)이 빠져나갈 수 있다.
BROOM_FAN_COUNT = (5, 7)
BROOM_FAN_SPREAD = 0.2
# 같은 방향으로 빠르기가 다른 탄을 쏴 차례로 닿게 한다.
BROOM_AIMED_SPEEDS = (300, 400, 500)
# 왼쪽으로 흩뿌리는 탄.
BROOM_SCATTER_COUNT = 6
BROOM_SCATTER_ANGLE = 0.6
BROOM_SCATTER_SPEED = (240, 420)
# 반짝이는 탄은 베면 REFLECTED_SPEED로 마녀 쪽으로 튕겨 나가고, 못 튕기는 탄(검은 탄, 균열 파편)에 닿으면 터진다.
# 터진 자리에서 이 반경 안의 못 튕기는 탄을 가까운 순서로 SPARK_BURST_MAX개까지만 지운다. 전기 장벽과 전기장은 지우지 못한다.
SPARK_BURST_RADIUS = 200
SPARK_BURST_MAX = 5
# 반격 단계. 탄막과 함정이 걷히고, 마녀는 운석을 떨어뜨리며 반짝이는 탄만 하나씩 플레이어를 겨눠 쏜다.
# 반격 단계에서 튕겨 낸 탄은 마녀를 쫓아가 맞고, BROOM_STUN_HITS번 맞은 마녀는 기절해 불릿 타임이 열린다.
BROOM_STUN_HITS = 3
# 반격을 알리는 동안은 공격하지 않는다.
COUNTER_START_DELAY = 1.5
COUNTER_SHOT_INTERVAL = (1.2, 1.8)
# 튕겨 낸 탄이 마녀에게 닿는 범위. 빗자루를 뺀 몸통이다.
BROOM_HIT_W = 110
BROOM_HIT_H = 170
# 운석은 화면 위의 무작위 자리에서 그때 플레이어가 있던 자리를 겨눠 떨어진다. 떨어지기 전 METEOR_WARNING초 동안 지나갈 길이 깜빡인다.
METEOR_INTERVAL = (0.8, 1.3)
METEOR_WARNING = 0.6
METEOR_WARNING_BLINK = 24
METEOR_SPEED = 750
METEOR_SIZE = 36
# 균열 파편 무리. 화면 오른쪽에서 무작위 높이로 쏟아진다.
# 잇달아 나오는 파편은 높이를 ORB_MIN_GAP 이상 벌려 세로로 늘어선 벽이 되지 않게 한다.
ORB_SIZE = 40
ORB_SPEED = (300, 560)
ORB_DRIFT = 60
ORB_MIN_GAP = 150
SWARM_TIME = 5
SWARM_INTERVAL = (0.14, 0.1)
# 무리가 끝난 뒤 남은 파편이 지나갈 시간.
SWARM_CLEAR_TIME = 1.5
# 전기 장벽. 틈 하나를 남기고 화면 높이를 막은 채 오른쪽에서 밀려온다.
# 다음 틈은 FENCE_SHIFT(최소, 최대)만큼 위나 아래에 있다. 장벽 사이 시간(후반 0.9초) 동안 540px를 움직일 수 있다.
FENCE_COUNT = (3, 4)
FENCE_SPEED = (340, 420)
FENCE_SPACING = (460, 380)
FENCE_GAP = 200
FENCE_SHIFT = (120, 280)
FENCE_W = 36
# 전기장. 화면 위아래에서 밀려 들어와 통로만 남기고 덮었다가 물러난다. 통로로는 파편이 날아온다.
# 화면 끝에 붙어 있으면 밀려오자마자 닿으므로, 덮일 자리를 경고 시간 동안 먼저 깜빡여 보여 준다.
PRESS_CORRIDOR = (240, 200)
PRESS_WARNING = 0.8
PRESS_WARNING_OPACITY = 0.3
PRESS_WARNING_BLINK = 18
PRESS_IN_TIME = 1.2
PRESS_HOLD_TIME = 2.6
PRESS_OUT_TIME = 0.6
PRESS_ORB_INTERVAL = 0.55
# 이보다 얕게 덮일 쪽은 내지 않는다.
PRESS_MIN_DEPTH = 30

# 개발자 테스트에서는 이만큼의 골드로 시작해 강화와 스킬을 모두 살 수 있다.
DEV_GOLD = 99_999_999

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
    'spin': {'name': '회전 베기', 'branch': 'sword', 'tier': 1, 'slot': 0, 'cost': 150, 'desc': '공중에서 베면 몸 둘레에 판정이 생기고 위아래로 200px까지 닿아 공중의 사역마를 벤다.'},
    'thrust': {'name': '찌르기', 'branch': 'sword', 'tier': 1, 'slot': 1, 'cost': 200, 'desc': '베기 사거리가 100px에서 150px로 늘어난다.'},
    'charge': {'name': '일섬 충전 +1', 'branch': 'move', 'tier': 1, 'slot': 0, 'cost': 250, 'desc': '일섬 최대 충전이 2회에서 3회로 늘어난다.'},
    'dive': {'name': '급강하', 'branch': 'move', 'tier': 1, 'slot': 1, 'cost': 200, 'desc': '공중에서 S로 수직 낙하한다. 착지 충격파(좌우 150px)로 지상 적을 처치하고, 보스에게는 베기 2배 피해를 준다.'},
    'triple': {'name': '3연격', 'branch': 'sword', 'tier': 2, 'slot': 0, 'cost': 400, 'desc': '0.6초 안에 세 번 베면 세 번째가 피해 3배와 넉백을 준다.'},
    'blink': {'name': '점멸', 'branch': 'move', 'tier': 2, 'slot': 0, 'cost': 400, 'desc': '일섬 대상이 없으면 앞으로 200px 순간이동한다. 충전을 1회 쓰며 낭떠러지 보험이 된다.'},
    'flurry': {'name': '천검난무 (Q)', 'branch': 'sword', 'tier': 3, 'slot': 0, 'cost': 800, 'desc': 'Q로 1.5초 동안 주변을 연속으로 베고 그동안 무적이다. 쿨타임 20초.'},
    'pierce': {'name': '관통 일섬 (E)', 'branch': 'move', 'tier': 3, 'slot': 0, 'cost': 800, 'desc': 'E로 화면 끝까지 직선으로 돌진하며 경로의 적을 모두 벤다. 보스는 뚫지 못하고 일섬 3배 피해를 받는다. 쿨타임 20초.'},
    'fire1': {'name': '화염 베기', 'branch': 'fire', 'tier': 1, 'slot': 0, 'cost': 250, 'desc': '보스에게 화상을 입힌다. 3초 동안 초당 공격력의 30% 피해를 주며 방패와 갑옷을 무시한다.'},
    'ice1': {'name': '서리 베기', 'branch': 'ice', 'tier': 1, 'slot': 0, 'cost': 250, 'desc': '보스를 5번 벨 때마다 2초 동안 보스의 동작이 0.7배속이 된다.'},
    'bolt1': {'name': '감전 베기', 'branch': 'bolt', 'tier': 1, 'slot': 0, 'cost': 250, 'desc': '보스를 벨 때 25% 확률로 번개가 떨어져 공격력의 50% 피해를 추가로 준다.'},
    'fire2': {'name': '시체 폭발', 'branch': 'fire', 'tier': 2, 'slot': 0, 'cost': 400, 'desc': '처치한 적이 터져 반경 120px 안의 적을 처치한다.'},
    'ice2': {'name': '얼음 파편', 'branch': 'ice', 'tier': 2, 'slot': 0, 'cost': 400, 'desc': '처치한 적이 깨지며 파편 3개가 앞으로 날아가 적을 처치한다.'},
    'fire3': {'name': '운석', 'branch': 'fire', 'tier': 3, 'slot': 0, 'cost': 800, 'desc': '보스전에서 좌+우 동시 클릭. 2초 시전 뒤 보스 최대 체력의 12% 피해를 준다. 시전 중에는 공격할 수 없다. 쿨타임 30초.'},
    'ice3': {'name': '빙창', 'branch': 'ice', 'tier': 3, 'slot': 0, 'cost': 800, 'desc': '보스전에서 좌+우 동시 클릭. 맞추면 보스가 2초 빙결되고, 그동안 받는 피해가 1.5배가 된다. 쿨타임 30초.'},
    'bolt3': {'name': '낙뢰', 'branch': 'bolt', 'tier': 3, 'slot': 0, 'cost': 800, 'desc': '보스전에서 좌+우 동시 클릭. 보스 위로 번개 3연발, 한 발에 공격력의 3배 피해를 준다. 쿨타임 30초.'},
    'bolt2': {'name': '연쇄 번개', 'branch': 'bolt', 'tier': 2, 'slot': 0, 'cost': 400, 'desc': '처치하면 가장 가까운 적 1마리에게 번개가 튀어 처치한다. 연쇄된다.'},
}
BRANCH_NAMES = {'sword': '검술', 'move': '기동', 'fire': '화염', 'ice': '빙결', 'bolt': '번개'}
ELEMENTS = ('fire', 'ice', 'bolt')
ELEMENT_CHANGE_COST = 300
ULTIMATE_COOLDOWN = 30
METEOR_CAST_TIME = 2
METEOR_DAMAGE_RATIO = 0.12
# fire/meteor 시트에서 운석이 바닥에 닿는 시점이다.
METEOR_FX_IMPACT = 0.67
LANCE_SPEED = 1400
LANCE_LIFE = 1.2
FREEZE_TIME = 2
FREEZE_DAMAGE_RATE = 1.5
FREEZE_FX_SPEED = 1.25
LIGHTNING_INTERVAL = 0.35
LIGHTNING_COUNT = 3
LIGHTNING_DAMAGE_RATIO = 3
LIGHTNING_FX_SPEED = 2
# lightning/lightning-strike 시트에서 번개가 내리치는 시점이다.
LIGHTNING_FX_IMPACT = 0.8
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
SWORD_REACH = 100
SWORD_H = 120
THRUST_REACH = 150
# 베기 게이지는 노리는 몬스터가 베기 사거리보다 이만큼 더 멀 때부터 그 몬스터 위에 나타난다. 달리기 속도로 약 0.5초다.
SLASH_GAUGE_LEAD = 220
# 게이지가 허용 범위에 들었을 때 베어 처치하면 보통 베기보다 오래 멈추고 크게 흔들리며 화면이 하얗게 번쩍인다.
PERFECT_HIT_STOP = 0.1
PERFECT_SHAKE_TIME = 0.22
PERFECT_SHAKE_AMP = 10
PERFECT_FLASH_OPACITY = 0.4
PERFECT_FLASH_TIME = 0.12
PERFECT_FX_SCALE = 3
TRIPLE_WINDOW = 0.6
TRIPLE_DAMAGE_RATIO = 3
TRIPLE_KNOCKBACK = 70
BLINK_DISTANCE = 200
FLURRY_TIME = 1.5
FLURRY_COOLDOWN = 20
FLURRY_INTERVAL = 0.15
FLURRY_RADIUS = 260
FLURRY_FX_SPEED = 1.5
PIERCE_TIME = 0.3
PIERCE_COOLDOWN = 20
PIERCE_DAMAGE_RATIO = 3
# 화면 오른쪽 끝에서 이만큼 안쪽에서 멈춘다.
PIERCE_END_MARGIN = 60
# 회전 베기는 공중의 적을 노리는 기술이라 좌우보다 위아래로 길다. 몸 중심에서 잰 거리다.
SPIN_REACH_X = 130
SPIN_REACH_Y = 200

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

# 낭떠러지 뒤에 착지할 자리를 비운다.
CHUNK_MARGIN = 300

# 돌과 상자의 크기는 스테이지마다 다르다(STAGES의 low_size).
HIGH_OBSTACLE_W = 150
# 슬라이딩 높이(50)는 지나가고 서 있는 높이(100)는 부딪힌다.
HIGH_OBSTACLE_CLEARANCE = 70
# 가시 바닥. 낮지만 넓어 너무 일찍 뛰면 끝에 걸린다.
SPIKES_W = 150
SPIKES_H = 36
# 방책. 1단 점프 높이(150)보다 높아 2단 점프로만 넘는다.
BARRICADE_W = 70
BARRICADE_H = 220
# 매달린 통나무. pillar와 같은 높이에 길게 걸려 있어 오래 슬라이딩해야 한다. 스테이지 1 속도로 0.72초라 슬라이딩 최대 시간(1초) 안에 지나간다.
# 2단 점프로 통나무 위(210)에 머무는 거리는 260px이라 뛰어넘을 수는 없다.
BEAM_W = 300
BEAM_H = 140
# 굴러오는 바위. 화면에 들어오면 굴러오기 시작해 제자리의 돌보다 빨리 다가온다.
BOULDER_SIZE = 80
BOULDER_SPEED = 220
# 낙석. 플레이어가 TRIGGER_TIME초 거리 안에 오면 천장에서 떨어져 FALL_TIME초 뒤 땅에 박히고, 그 뒤에는 돌처럼 뛰어넘는다.
RUBBLE_W = 80
RUBBLE_H = 72
RUBBLE_TRIGGER_TIME = 0.8
RUBBLE_FALL_TIME = 0.45
RUBBLE_WARNING_H = 8
RUBBLE_SHAKE_TIME = 0.15
RUBBLE_SHAKE_AMP = 5

# 1단 점프 체공 거리는 약 250px, 2단 점프는 약 440px다.
PIT_W_SHORT = 160
PIT_W_LONG = 360

# 일섬을 다 쓴 직후에 진입해도 1회가 충전되도록 충전 시간만큼 평지를 둔다 (DS-8).
CLIFF_RUN_UP_TIME = STATS['dash_recharge']['base']
# 평지가 보장하는 일섬 1회와 공중 점프로 건널 수 있는 폭이다. 2단 점프만으로는 못 건넌다.
CLIFF_W = 600
# 낭떠러지 시작점 기준 (x, 지면 위 높이). 간격은 사거리 400px 안이다 (DS-7).
# 두 번째는 공중 점프 궤적 위에 두어, 일섬 1회로 건널 때 부딪히지 않고 2회를 아낀 플레이어만 베러 올라간다.
CLIFF_FAMILIARS = ((220, 200), (450, 450))

PLATFORM_H = 24
# 청크 E는 건널 수 없는 배치가 나오지 않도록 직접 설계한다 (MP-5). 높이는 모두 지면 위 기준이다.
# 낮은 중력에서 1단 점프는 높이 250px, 평지 기준 체공 거리 약 530px다. 사역마 간격은 사거리 400px 안이다.
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
# 달리기 구간의 패턴 조각. 난이도를 바꾸려면 여기의 목록과 간격만 고치면 된다.
# (종류, x) 목록이고 x는 조각 시작에서 잰 거리(px)다. x와 구덩이 폭에 스테이지 속도를 곱하므로 대응할 시간은 스테이지마다 같다.
#   rock: 낮은 장애물, 점프           pillar: 높은 장애물, 슬라이딩
#   pit: 1단 점프로 넘는 구덩이       pit_long: 2단 점프로 넘는 구덩이
#   grunt: 달려와 베는 근접병         goblin: 웅크렸다가 달려드는 고블린
#   mage: 지상 마법사                 mage_high: 발판 위 마법사
#   bat: 서 있으면 부딪히는 사역마    bat_high: 점프하면 부딪히는 사역마
#   spikes: 가시 바닥, 길게 점프      barricade: 방책, 2단 점프
#   beam: 매달린 통나무, 긴 슬라이딩  boulder: 굴러오는 바위, 점프
#   rubble: 천장에서 떨어지는 낙석, 땅에 박힌 뒤 점프
# 속도 400px/s에서 100px은 0.25초다. 1단 점프는 체공 0.64초(254px), 2단 점프는 약 1.1초(440px)다.
# 만들 때 지킬 것: 슬라이딩 중에는 공격할 수 없으므로 pillar, beam 바로 뒤에 grunt, goblin을 두면 피할 수 없다.
# 천장까지 막는 pillar 앞에 mage_high 발판을 두면 발판에 착지했을 때 넘을 수 없다. 고블린은 스테이지 속도와 상관없이 650px/s로 달린다.
# boulder는 적어 둔 x보다 약 235px 앞에서, goblin은 약 200px 앞에서 만난다. 조각의 첫 요소로 쓸 때는 x를 그만큼 띄워
# 앞 조각의 pillar, beam 바로 뒤에서 만나지 않게 한다. boulder가 굴러오는 길에는 구덩이나 다른 장애물을 두지 않는다.
# barricade는 연달아 넘을 수 없으므로 조각의 마지막 요소로 두지 않는다.
PATTERNS = {
    # 스테이지 1의 도입. 입력 둘, 1초 안팎의 간격으로 조각마다 한 가지를 익힌다.
    'easy': (
        (('rock', 0), ('rock', 380)),
        (('pillar', 0), ('rock', 440)),
        (('grunt', 0), ('grunt', 300)),
        (('rock', 0), ('goblin', 520)),
        (('bat', 0), ('bat', 280)),
        (('pit', 0), ('rock', 480)),
        (('rock', 0), ('mage', 480)),
        (('spikes', 0), ('rock', 460)),
        (('barricade', 0), ('bat', 420)),
        (('beam', 0), ('rock', 620)),
        (('rock', 0), ('boulder', 700)),
        (('rubble', 0), ('rubble', 420)),
    ),
    # 스테이지 1의 중반. 입력 셋에서 넷, 0.5~0.8초 간격으로 점프, 슬라이딩, 베기를 번갈아 요구한다.
    'castle': (
        (('rock', 0), ('spikes', 280), ('rock', 600), ('grunt', 860)),
        (('pillar', 0), ('barricade', 400), ('grunt', 720)),
        (('spikes', 0), ('bat', 300), ('rock', 500), ('bat', 700)),
        (('goblin', 220), ('rock', 340), ('bat', 520)),
        (('beam', 0), ('rock', 440), ('goblin', 740)),
        (('rubble', 0), ('pillar', 280), ('rock', 580), ('goblin', 900)),
        (('barricade', 0), ('spikes', 360), ('grunt', 700)),
        (('rock', 0), ('rock', 280), ('boulder', 720), ('bat', 860)),
        (('pit', 0), ('goblin', 400), ('rock', 540)),
        (('mage', 0), ('beam', 260), ('rock', 740)),
        (('mage_high', 0), ('grunt', 200), ('rock', 420)),
        (('pillar', 0), ('boulder', 600), ('bat', 720)),
        (('bat', 0), ('rock', 200), ('bat_high', 330), ('spikes', 540)),
        (('grunt', 0), ('rubble', 240), ('grunt', 480)),
        (('spikes', 0), ('spikes', 310), ('pillar', 620), ('rock', 980)),
        (('pit', 0), ('barricade', 400), ('bat', 700)),
        (('rock', 0), ('pillar', 280), ('rock', 560), ('pillar', 820)),
        (('bat', 0), ('pillar', 200), ('grunt', 620)),
        (('rubble', 0), ('bat', 240), ('rubble', 440)),
        (('rock', 0), ('grunt', 240), ('spikes', 480)),
    ),
    # 스테이지 1의 후반. 입력 넷 이상, 0.4~0.65초 간격으로 쉬지 않고 이어진다.
    'castle_rush': (
        (('rock', 0), ('rock', 150), ('spikes', 440), ('bat', 700), ('goblin', 960)),
        (('barricade', 0), ('pillar', 320), ('bat', 560), ('barricade', 720), ('grunt', 1060)),
        (('spikes', 0), ('rock', 270), ('beam', 500), ('rock', 930), ('grunt', 1130)),
        (('goblin', 220), ('goblin', 340), ('rock', 420), ('boulder', 860), ('bat', 1000)),
        (('rubble', 0), ('rubble', 250), ('pillar', 500), ('grunt', 860), ('bat', 1020)),
        (('pit_long', 0), ('bat_high', 170), ('spikes', 580), ('bat', 820)),
        (('beam', 0), ('barricade', 500), ('spikes', 820), ('bat', 1060)),
        (('rock', 0), ('bat_high', 130), ('rock', 290), ('bat', 450), ('pillar', 600)),
        (('mage', 0), ('rock', 180), ('mage_high', 420), ('goblin', 660)),
        (('grunt', 0), ('rock', 170), ('grunt', 330), ('pillar', 500), ('rock', 820)),
        (('pillar', 0), ('rock', 260), ('pillar', 480), ('boulder', 1040)),
        (('pit', 0), ('barricade', 400), ('pit', 760), ('rock', 1100), ('bat', 1300)),
        (('boulder', 300), ('boulder', 540), ('spikes', 680), ('bat', 980)),
        (('spikes', 0), ('barricade', 400), ('rock', 740), ('goblin', 1080)),
        (('rock', 0), ('pillar', 250), ('rock', 530), ('pillar', 780), ('rock', 1060)),
        (('spikes', 0), ('bat', 290), ('spikes', 460), ('grunt', 820), ('rock', 1060)),
        (('rubble', 0), ('boulder', 500), ('rubble', 580), ('pillar', 860), ('grunt', 1240)),
        (('barricade', 0), ('goblin', 540), ('beam', 620), ('rock', 1060)),
        (('bat', 0), ('bat', 160), ('rock', 340), ('bat_high', 480), ('pillar', 660)),
        (('rock', 0), ('bat', 150), ('rock', 290), ('bat', 440), ('rock', 580)),
        (('pillar', 0), ('pillar', 230), ('rock', 520), ('spikes', 780), ('bat', 1000)),
    ),
    # 낭떠러지 앞 평지에 까는 조각. 일섬 충전을 기다리는 구간이므로 일섬을 쓰게 만드는 몬스터 없이 장애물만 둔다.
    # 낭떠러지 앞에 숨 돌릴 평지가 남도록 x는 800을 넘기지 않는다.
    'run_up': (
        (('rock', 0), ('spikes', 320), ('rock', 680)),
        (('pillar', 0), ('rock', 340), ('beam', 560)),
        (('rubble', 0), ('barricade', 380), ('rubble', 760)),
        (('spikes', 0), ('pillar', 330), ('boulder', 800)),
        (('barricade', 0), ('rock', 360), ('rock', 660)),
    ),
    # 입력 둘에서 셋, 0.5~0.8초 간격으로 이어 간다.
    'normal': (
        (('rock', 0), ('goblin', 120), ('bat', 200)),
        (('rock', 0), ('pillar', 340)),
        (('pillar', 0), ('grunt', 480), ('rock', 700)),
        (('goblin', 0), ('pillar', 200)),
        (('bat', 0), ('rock', 180), ('bat_high', 300)),
        (('pit', 0), ('goblin', 400), ('rock', 560)),
        (('rock', 0), ('rock', 300), ('grunt', 620)),
        (('mage', 0), ('pillar', 260)),
        (('mage_high', 0), ('grunt', 200), ('rock', 420)),
    ),
    # 입력 셋 이상, 0.3~0.6초 간격이거나 2단 점프를 요구한다.
    'hard': (
        (('rock', 0), ('rock', 140), ('goblin', 420)),
        (('pillar', 0), ('pillar', 260), ('rock', 560)),
        (('goblin', 0), ('goblin', 120), ('goblin', 240)),
        (('pit_long', 0), ('bat_high', 170), ('rock', 560)),
        (('rock', 0), ('bat_high', 130), ('rock', 300), ('bat', 470)),
        (('grunt', 0), ('rock', 170), ('grunt', 330), ('pillar', 520)),
        (('mage', 0), ('rock', 180), ('mage_high', 420), ('goblin', 660)),
        (('pit', 0), ('pillar', 380), ('goblin', 440)),
    ),
}
# 조각과 조각 사이의 빈 거리는 STAGES의 pattern_gap이다. 1단 점프 체공 거리보다 길어 앞 조각에서 착지할 자리는 남긴다.
# 낭떠러지는 조각 사이에 끼우는 휴식 구간이다. 앞에 4초 평지를 두므로 조각 몇 개마다 넣을지가 곧 쉬는 빈도다.
CLIFF_EVERY_MIN = 6
CLIFF_EVERY_MAX = 9
BAT_H = 100
BAT_HIGH_H = 220
MAGE_PLATFORM_H = 130
MAGE_PLATFORM_HALF_W = 200

GRUNT_W = 60
GRUNT_H = 90
GRUNT_SPEED = 160
GRUNT_SIGHT = 600
GRUNT_ATTACK_RANGE = 240
GRUNT_WINDUP_TIME = 0.25
GRUNT_ATTACK_TIME = 0.15
GRUNT_RECOVER_TIME = 0.4
GRUNT_ATTACK_REACH = 50
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
