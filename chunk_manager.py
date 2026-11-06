import random
from collections import namedtuple

import config
import game_world
from monster import Familiar, Grunt
from obstacle import Ground, make_high_obstacle, make_low_obstacle

Chunk = namedtuple('Chunk', 'length obstacles pits monsters', defaults=((), (), ()))


def grunt_gap():
    return random.randint(config.GRUNT_GAP_MIN, config.GRUNT_GAP_MAX)


def build_chunk_a():
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


def build_chunk_b():
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


def build_chunk_c():
    start = config.CLIFF_RUN_UP
    pits = [(start, config.CLIFF_W)]
    monsters = [(Familiar, start + x, config.GROUND_TOP + y) for x, y in config.CLIFF_FAMILIARS]
    return Chunk(start + config.CLIFF_W + config.CHUNK_MARGIN, pits=pits, monsters=monsters)


CHUNK_BUILDERS = {'A': build_chunk_a, 'B': build_chunk_b, 'C': build_chunk_c}


class ChunkManager:
    def __init__(self, player):
        self.player = player
        self.objects = []
        self.last_chunk = None
        # 시작 지점에서 반응할 시간을 주도록 첫 화면은 평지로 둔다.
        self.add_ground(0, config.SCREEN_W)
        self.end_x = config.SCREEN_W

    def add_ground(self, left, right):
        ground = Ground(left, right)
        self.objects.append(ground)
        game_world.add_object(ground, game_world.LAYER_MAP)
        game_world.add_collision_pair('player:ground', None, ground)

    def add_obstacle(self, obstacle):
        self.objects.append(obstacle)
        game_world.add_object(obstacle, game_world.LAYER_MAP)
        game_world.add_collision_pair('player:obstacle', None, obstacle)

    def add_monster(self, monster):
        self.objects.append(monster)
        game_world.add_object(monster, game_world.LAYER_MONSTER)
        game_world.add_collision_pair('player:monster', None, monster)
        game_world.add_collision_pair('sword:monster', None, monster)

    def spawn_chunk(self, chunk):
        built = CHUNK_BUILDERS[chunk]()
        ground_left = self.end_x
        for offset, width in built.pits:
            self.add_ground(ground_left, self.end_x + offset)
            ground_left = self.end_x + offset + width
        self.add_ground(ground_left, self.end_x + built.length)
        for make, offset in built.obstacles:
            self.add_obstacle(make(self.end_x + offset))
        for make, offset, y in built.monsters:
            self.add_monster(make(self.end_x + offset, y, self.player))
        self.end_x += built.length
        self.last_chunk = chunk

    def update(self, camera):
        if self.end_x <= camera.x + config.SCREEN_W:
            candidates = [chunk for chunk in CHUNK_BUILDERS if chunk != self.last_chunk]
            self.spawn_chunk(random.choice(candidates))

        for obj in self.objects[:]:
            if obj.get_bb()[2] < camera.x:
                self.objects.remove(obj)
                game_world.remove_object(obj)
