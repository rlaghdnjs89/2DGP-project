import random
from collections import namedtuple

import config
import game_world
from boss import Executor, Warden, Witch
from monster import Familiar, Goblin, Grunt, Mage
from obstacle import EvolutionAltar, Ground, Platform, StageGate, Wall, make_high_obstacle, make_low_obstacle

Chunk = namedtuple('Chunk', 'length obstacles pits monsters platforms', defaults=((), (), (), ()))


# 조각의 종류별 (몬스터, 지면 위 높이).
PATTERN_MONSTERS = {
    'grunt': (Grunt, 0),
    'goblin': (Goblin, 0),
    'mage': (Mage, 0),
    'mage_high': (Mage, config.MAGE_PLATFORM_H),
    'bat': (Familiar, config.BAT_H),
    'bat_high': (Familiar, config.BAT_HIGH_H),
}
PATTERN_OBSTACLES = {'rock': (make_low_obstacle, config.LOW_OBSTACLE_W), 'pillar': (make_high_obstacle, config.HIGH_OBSTACLE_W)}
PATTERN_PITS = {'pit': config.PIT_W_SHORT, 'pit_long': config.PIT_W_LONG}


def build_pattern(pattern, stage):
    speed = config.STAGES[stage]['speed']
    start = random.randint(config.PATTERN_GAP_MIN, config.PATTERN_GAP_MAX) * speed
    obstacles, pits, monsters, platforms = [], [], [], []
    end = start
    for kind, x in pattern:
        offset = int(start + x * speed)
        width = 0
        if kind in PATTERN_OBSTACLES:
            make, width = PATTERN_OBSTACLES[kind]
            obstacles.append((make, offset))
        elif kind in PATTERN_PITS:
            width = int(PATTERN_PITS[kind] * speed)
            pits.append((offset, width))
        else:
            make, height = PATTERN_MONSTERS[kind]
            monsters.append((make, offset, config.GROUND_TOP + height))
            if kind == 'mage_high':
                platforms.append((offset - config.MAGE_PLATFORM_HALF_W, offset + config.MAGE_PLATFORM_HALF_W, config.MAGE_PLATFORM_H))
        end = max(end, offset + width)
    return Chunk(int(end), obstacles, pits, monsters, platforms)


def build_cliff(stage):
    start = int(config.SCROLL_SPEED * config.STAGES[stage]['speed'] * config.CLIFF_RUN_UP_TIME)
    pits = [(start, config.CLIFF_W)]
    monsters = [(Familiar, start + x, config.GROUND_TOP + y) for x, y in config.CLIFF_FAMILIARS]
    return Chunk(start + config.CLIFF_W + config.CHUNK_MARGIN, pits=pits, monsters=monsters)


def build_island(name):
    layout = config.ISLAND_CHUNKS[name]
    monsters = [(Familiar, x, config.GROUND_TOP + y) for x, y in layout['familiars']]
    return Chunk(layout['length'], pits=layout['pits'], monsters=monsters, platforms=layout['platforms'])


# 스테이지 순서다.
BOSSES = (Warden, Witch, Executor)


class ChunkManager:
    def __init__(self, player):
        self.player = player
        self.objects = []
        self.last_chunk = None
        self.stage = 0
        self.run_time = 0
        self.altar_placed = False
        self.patterns_until_cliff = random.randint(config.CLIFF_EVERY_MIN, config.CLIFF_EVERY_MAX)
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
        game_world.add_collision_pair('shard:monster', None, monster)

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
        for left, right, height in config.STAGES[self.stage]['arena_platforms']:
            self.add_platform(self.end_x + left, self.end_x + right, height)
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

    def spawn_chunk(self, built, name):
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
        self.last_chunk = name

    def progress(self):
        return min(1, self.run_time / config.STAGE_RUN_TIME)

    def pick_pattern(self):
        tiers = next(tiers for start, tiers in reversed(config.STAGES[self.stage]['pattern_tiers']) if self.progress() >= start)
        return random.choice([pattern for tier in tiers for pattern in config.PATTERNS[tier] if pattern != self.last_chunk])

    def spawn_run_chunk(self):
        if not config.STAGES[self.stage]['pattern_tiers']:
            name = random.choice([island for island in config.ISLAND_CHUNKS if island != self.last_chunk])
            self.spawn_chunk(build_island(name), name)
        elif self.patterns_until_cliff == 0:
            self.patterns_until_cliff = random.randint(config.CLIFF_EVERY_MIN, config.CLIFF_EVERY_MAX)
            self.spawn_chunk(build_cliff(self.stage), 'cliff')
        else:
            self.patterns_until_cliff -= 1
            pattern = self.pick_pattern()
            self.spawn_chunk(build_pattern(pattern, self.stage), pattern)

    def update(self, camera, dt):
        # 아레나를 붙인 뒤 다음 스테이지의 관문을 지나기 전까지는 달린 시간을 세지 않는다.
        if not self.player.boss and self.player.stage == self.stage:
            self.run_time += dt
        if self.end_x <= camera.x + config.SCREEN_W:
            if self.run_time < config.STAGE_RUN_TIME:
                self.spawn_run_chunk()
            elif not self.altar_placed:
                self.spawn_altar()
            else:
                self.spawn_arena()

        for obj in self.objects[:]:
            if obj.get_bb()[2] < camera.x:
                self.objects.remove(obj)
                game_world.remove_object(obj)
