import random
from collections import namedtuple

import config
import game_world
from boss import Warden
from monster import Familiar, Goblin, Grunt, Mage
from obstacle import EvolutionAltar, Ground, Platform, StageGate, Wall, make_high_obstacle, make_low_obstacle

Chunk = namedtuple('Chunk', 'length obstacles pits monsters platforms', defaults=((), (), (), ()))


def grunt_gap():
    return random.randint(config.GRUNT_GAP_MIN, config.GRUNT_GAP_MAX)


def build_chunk_a(stage):
    obstacles = []
    monsters = []
    x = random.randint(config.CHUNK_MARGIN, config.CHUNK_MARGIN + 150)
    for _ in range(2):
        obstacles.append((make_low_obstacle, x))
        x += config.LOW_OBSTACLE_W + grunt_gap()
        monsters.append((Grunt, x, config.GROUND_TOP))
        x += random.randint(config.OBSTACLE_GAP_MIN // 2, config.OBSTACLE_GAP_MAX // 2)
    if random.random() < config.GRUNT_3RD_CHANCE:
        monsters.append((Grunt, x, config.GROUND_TOP))
    return Chunk(config.CHUNK_A_LENGTH, obstacles, monsters=monsters)


def build_chunk_b(stage):
    length = config.CHUNK_B_LENGTH
    kinds = [(make_low_obstacle, config.LOW_OBSTACLE_W), (make_high_obstacle, config.HIGH_OBSTACLE_W)]
    random.shuffle(kinds)
    obstacles = []
    pits = []
    x = config.CHUNK_MARGIN
    # 낮은 장애물과 높은 장애물을 번갈아 놓아 점프와 슬라이딩을 교대로 요구한다.
    while x + config.PIT_W_LONG <= length - config.CHUNK_MARGIN:
        if random.random() < config.PIT_CHANCE:
            width = random.choice((config.PIT_W_SHORT, config.PIT_W_LONG))
            pits.append((x, width))
        else:
            make, width = kinds[len(obstacles) % 2]
            obstacles.append((make, x))
        x += width + random.randint(config.OBSTACLE_GAP_MIN, config.OBSTACLE_GAP_MAX)
    return Chunk(length, obstacles, pits)


def build_chunk_c(stage):
    start = int(config.SCROLL_SPEED * config.STAGES[stage]['speed'] * config.CLIFF_RUN_UP_TIME)
    pits = [(start, config.CLIFF_W)]
    monsters = [(Familiar, start + x, config.GROUND_TOP + y) for x, y in config.CLIFF_FAMILIARS]
    return Chunk(start + config.CLIFF_W + config.CHUNK_MARGIN, pits=pits, monsters=monsters)


def build_chunk_d(stage):
    layout = config.CHUNK_D
    obstacles = [(make_high_obstacle, layout['high_obstacle'])]
    monsters = [(Mage, x, config.GROUND_TOP + y) for x, y in layout['mages']]
    return Chunk(layout['length'], obstacles, monsters=monsters, platforms=layout['platforms'])


def build_chunk_g(stage):
    monsters = [(Goblin, x, config.GROUND_TOP) for x in config.CHUNK_G['goblins']]
    return Chunk(config.CHUNK_G['length'], monsters=monsters)


def build_island(name):
    layout = config.ISLAND_CHUNKS[name]
    monsters = [(Familiar, x, config.GROUND_TOP + y) for x, y in layout['familiars']]
    return Chunk(layout['length'], pits=layout['pits'], monsters=monsters, platforms=layout['platforms'])


# 스테이지 순서다.
BOSSES = (Warden, Warden, Warden)

CHUNK_BUILDERS = {
    'A': build_chunk_a,
    'B': build_chunk_b,
    'C': build_chunk_c,
    'D': build_chunk_d,
    'G': build_chunk_g,
    'E1': lambda stage: build_island('E1'),
    'E2': lambda stage: build_island('E2'),
    'E3': lambda stage: build_island('E3'),
}


class ChunkManager:
    def __init__(self, player):
        self.player = player
        self.objects = []
        self.last_chunk = None
        self.stage = 0
        self.run_time = 0
        self.altar_placed = False
        # 시작 지점에서 반응할 시간을 주도록 첫 화면은 평지로 둔다.
        self.add_ground(0, config.SCREEN_W)
        self.end_x = config.SCREEN_W

    def add_ground(self, left, right):
        ground = Ground(left, right, self.stage)
        self.objects.append(ground)
        game_world.add_object(ground, game_world.LAYER_MAP)
        game_world.add_collision_pair('player:ground', None, ground)

    def add_platform(self, left, right, height):
        platform = Platform(left, right, config.GROUND_TOP + height, self.stage)
        self.objects.append(platform)
        game_world.add_object(platform, game_world.LAYER_MAP)
        game_world.add_collision_pair('player:ground', None, platform)

    def add_gate(self, stage):
        gate = StageGate(self.end_x, stage)
        self.objects.append(gate)
        game_world.add_object(gate, game_world.LAYER_MAP)
        game_world.add_collision_pair('player:gate', None, gate)

    def add_obstacle(self, obstacle):
        self.objects.append(obstacle)
        game_world.add_object(obstacle, game_world.LAYER_MAP)
        game_world.add_collision_pair('player:obstacle', None, obstacle)

    def add_monster(self, monster):
        self.objects.append(monster)
        game_world.add_object(monster, game_world.LAYER_MONSTER)
        game_world.add_collision_pair('player:monster', None, monster)
        game_world.add_collision_pair('sword:monster', None, monster)

    def add_wall(self, x):
        wall = Wall(x, self.player)
        self.objects.append(wall)
        game_world.add_object(wall, game_world.LAYER_MAP)
        game_world.add_collision_pair('player:wall', None, wall)
        return wall

    def spawn_altar(self):
        self.add_ground(self.end_x, self.end_x + config.ALTAR_CHUNK_LENGTH)
        altar = EvolutionAltar(self.end_x + config.ALTAR_OFFSET, self.player)
        self.objects.append(altar)
        game_world.add_object(altar, game_world.LAYER_MAP)
        self.end_x += config.ALTAR_CHUNK_LENGTH
        self.altar_placed = True

    def spawn_arena(self):
        self.add_ground(self.end_x, self.end_x + config.ARENA_LENGTH)
        wall_x = self.end_x + config.ARENA_WALL_OFFSET
        # 마지막 보스를 쓰러뜨리면 바로 클리어이므로 뒤를 막는 장벽이 없다.
        wall = self.add_wall(wall_x) if self.stage + 1 < len(config.STAGES) else None
        self.add_monster(BOSSES[self.stage](wall_x - config.BOSS_WALL_GAP, config.GROUND_TOP, self.player, wall))
        self.end_x += config.ARENA_LENGTH
        self.last_chunk = None
        self.altar_placed = False
        if wall:
            self.stage += 1
            self.run_time = 0
            self.add_gate(self.stage)

    def spawn_chunk(self, chunk):
        built = CHUNK_BUILDERS[chunk](self.stage)
        ground_left = self.end_x
        for offset, width in built.pits:
            self.add_ground(ground_left, self.end_x + offset)
            ground_left = self.end_x + offset + width
        self.add_ground(ground_left, self.end_x + built.length)
        for left, right, height in built.platforms:
            self.add_platform(self.end_x + left, self.end_x + right, height)
        for make, offset in built.obstacles:
            self.add_obstacle(make(self.end_x + offset, self.stage))
        for make, offset, y in built.monsters:
            self.add_monster(make(self.end_x + offset, y, self.player))
        self.end_x += built.length
        self.last_chunk = chunk

    def progress(self):
        return min(1, self.run_time / config.STAGE_RUN_TIME)

    def pick_chunk(self):
        return random.choice([chunk for chunk in config.STAGE_CHUNKS[self.stage] if chunk != self.last_chunk])

    def update(self, camera, dt):
        # 아레나를 붙인 뒤 다음 스테이지의 관문을 지나기 전까지는 달린 시간을 세지 않는다.
        if not self.player.boss and self.player.stage == self.stage:
            self.run_time += dt
        if self.end_x <= camera.x + config.SCREEN_W:
            if self.run_time < config.STAGE_RUN_TIME:
                self.spawn_chunk(self.pick_chunk())
            elif not self.altar_placed:
                self.spawn_altar()
            else:
                self.spawn_arena()

        for obj in self.objects[:]:
            if obj.get_bb()[2] < camera.x:
                self.objects.remove(obj)
                game_world.remove_object(obj)
