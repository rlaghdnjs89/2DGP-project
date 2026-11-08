import random
from collections import namedtuple

import config
import game_world
from monster import Boss, Familiar, Goblin, Grunt, Mage
from obstacle import Ground, PhaseGate, Platform, Wall, make_high_obstacle, make_low_obstacle

Chunk = namedtuple('Chunk', 'length obstacles pits monsters platforms wall', defaults=((), (), (), (), None))


def grunt_gap():
    return random.randint(config.GRUNT_GAP_MIN, config.GRUNT_GAP_MAX)


def build_chunk_a(phase):
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


def build_chunk_b(phase):
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


def build_chunk_c(phase):
    start = int(config.SCROLL_SPEED * config.PHASES[phase]['speed'] * config.CLIFF_RUN_UP_TIME)
    pits = [(start, config.CLIFF_W)]
    monsters = [(Familiar, start + x, config.GROUND_TOP + y) for x, y in config.CLIFF_FAMILIARS]
    return Chunk(start + config.CLIFF_W + config.CHUNK_MARGIN, pits=pits, monsters=monsters)


def build_chunk_d(phase):
    layout = config.CHUNK_D
    obstacles = [(make_high_obstacle, layout['high_obstacle'])]
    monsters = [(Mage, x, config.GROUND_TOP + y) for x, y in layout['mages']]
    return Chunk(layout['length'], obstacles, monsters=monsters, platforms=layout['platforms'])


def build_chunk_g(phase):
    monsters = [(Goblin, x, config.GROUND_TOP) for x in config.CHUNK_G['goblins']]
    return Chunk(config.CHUNK_G['length'], monsters=monsters)


def build_island(name):
    layout = config.ISLAND_CHUNKS[name]
    monsters = [(Familiar, x, config.GROUND_TOP + y) for x, y in layout['familiars']]
    return Chunk(layout['length'], pits=layout['pits'], monsters=monsters, platforms=layout['platforms'])


def build_chunk_f(phase):
    return Chunk(config.CHUNK_F_LENGTH, wall=config.WALL_OFFSET)


CHUNK_BUILDERS = {
    'A': build_chunk_a,
    'B': build_chunk_b,
    'C': build_chunk_c,
    'D': build_chunk_d,
    'G': build_chunk_g,
    'E1': lambda phase: build_island('E1'),
    'E2': lambda phase: build_island('E2'),
    'E3': lambda phase: build_island('E3'),
    'F': build_chunk_f,
}


class ChunkManager:
    def __init__(self, player):
        self.player = player
        self.objects = []
        self.last_chunk = None
        self.phase = 0
        self.cycle_time = 0
        # 시작 지점에서 반응할 시간을 주도록 첫 화면은 평지로 둔다.
        self.add_ground(0, config.SCREEN_W)
        self.end_x = config.SCREEN_W

    def add_ground(self, left, right):
        ground = Ground(left, right, self.phase)
        self.objects.append(ground)
        game_world.add_object(ground, game_world.LAYER_MAP)
        game_world.add_collision_pair('player:ground', None, ground)

    def add_platform(self, left, right, height):
        platform = Platform(left, right, config.GROUND_TOP + height, self.phase)
        self.objects.append(platform)
        game_world.add_object(platform, game_world.LAYER_MAP)
        game_world.add_collision_pair('player:ground', None, platform)

    def add_gate(self, phase):
        gate = PhaseGate(self.end_x, phase)
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
        self.add_monster(Boss(x - config.BOSS_WALL_GAP, config.GROUND_TOP, self.player, wall))

    def spawn_chunk(self, chunk):
        built = CHUNK_BUILDERS[chunk](self.phase)
        ground_left = self.end_x
        for offset, width in built.pits:
            self.add_ground(ground_left, self.end_x + offset)
            ground_left = self.end_x + offset + width
        self.add_ground(ground_left, self.end_x + built.length)
        for left, right, height in built.platforms:
            self.add_platform(self.end_x + left, self.end_x + right, height)
        for make, offset in built.obstacles:
            self.add_obstacle(make(self.end_x + offset, self.phase))
        for make, offset, y in built.monsters:
            self.add_monster(make(self.end_x + offset, y, self.player))
        if built.wall is not None:
            self.add_wall(self.end_x + built.wall)
        self.end_x += built.length
        self.last_chunk = chunk

    def pick_chunk(self):
        return random.choice([chunk for chunk in config.PHASE_CHUNKS[self.phase] if chunk != self.last_chunk])

    def update(self, camera, dt):
        if not self.player.boss:
            self.cycle_time += dt
        if self.end_x <= camera.x + config.SCREEN_W:
            next_phase = self.phase + 1
            # 일섬 연쇄 도중에 물리가 바뀌지 않도록 청크가 이어지는 지점에서만 페이즈를 넘긴다 (Q7).
            if next_phase < len(config.PHASES) and self.player.score >= config.PHASES[next_phase]['score']:
                self.phase = next_phase
                self.add_gate(next_phase)
            if self.cycle_time >= config.WALL_CYCLE:
                self.spawn_chunk('F')
                self.cycle_time = 0
            else:
                self.spawn_chunk(self.pick_chunk())

        for obj in self.objects[:]:
            if obj.get_bb()[2] < camera.x:
                self.objects.remove(obj)
                game_world.remove_object(obj)
