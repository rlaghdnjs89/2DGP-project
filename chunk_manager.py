import random

import config
import game_world
from obstacle import Ground, make_high_obstacle, make_low_obstacle


def build_chunk_a():
    length = config.CHUNK_A_LENGTH
    half_gap = config.OBSTACLE_GAP_MIN // 2
    first_end = length // 2 - half_gap - config.LOW_OBSTACLE_W
    second_end = length - config.CHUNK_MARGIN - config.LOW_OBSTACLE_W
    obstacles = [
        (make_low_obstacle, random.randint(config.CHUNK_MARGIN, first_end)),
        (make_low_obstacle, random.randint(length // 2 + half_gap, second_end)),
    ]
    return length, obstacles


def build_chunk_b():
    length = config.CHUNK_B_LENGTH
    kinds = [(make_low_obstacle, config.LOW_OBSTACLE_W), (make_high_obstacle, config.HIGH_OBSTACLE_W)]
    random.shuffle(kinds)
    obstacles = []
    x = config.CHUNK_MARGIN
    # 낮은 장애물과 높은 장애물을 번갈아 놓아 점프와 슬라이딩을 교대로 요구한다.
    while x + config.HIGH_OBSTACLE_W <= length - config.CHUNK_MARGIN:
        make, width = kinds[len(obstacles) % 2]
        obstacles.append((make, x))
        x += width + random.randint(config.OBSTACLE_GAP_MIN, config.OBSTACLE_GAP_MAX)
    return length, obstacles


CHUNK_BUILDERS = {'A': build_chunk_a, 'B': build_chunk_b}


class ChunkManager:
    def __init__(self):
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

    def spawn_chunk(self, chunk):
        length, obstacles = CHUNK_BUILDERS[chunk]()
        self.add_ground(self.end_x, self.end_x + length)
        for make, offset in obstacles:
            self.add_obstacle(make(self.end_x + offset))
        self.end_x += length
        self.last_chunk = chunk

    def update(self, camera):
        if self.end_x <= camera.x + config.SCREEN_W:
            candidates = [chunk for chunk in CHUNK_BUILDERS if chunk != self.last_chunk]
            self.spawn_chunk(random.choice(candidates))

        for obj in self.objects[:]:
            if obj.get_bb()[2] < camera.x:
                self.objects.remove(obj)
                game_world.remove_object(obj)
