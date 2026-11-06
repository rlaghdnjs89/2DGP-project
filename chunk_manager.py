import random

import config
import game_world
from obstacle import Ground


CHUNK_LENGTHS = {'A': config.CHUNK_A_LENGTH, 'B': config.CHUNK_B_LENGTH}


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

    def spawn_chunk(self, chunk):
        length = CHUNK_LENGTHS[chunk]
        self.add_ground(self.end_x, self.end_x + length)
        self.end_x += length
        self.last_chunk = chunk

    def update(self, camera):
        if self.end_x <= camera.x + config.SCREEN_W:
            candidates = [chunk for chunk in CHUNK_LENGTHS if chunk != self.last_chunk]
            self.spawn_chunk(random.choice(candidates))

        for obj in self.objects[:]:
            if obj.get_bb()[2] < camera.x:
                self.objects.remove(obj)
                game_world.remove_object(obj)
