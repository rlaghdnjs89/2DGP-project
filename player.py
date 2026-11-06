from pico2d import SDL_KEYDOWN, SDL_KEYUP, SDLK_s, SDLK_w, draw_rectangle

import config


class Run:
    COLOR = (40, 90, 200)

    def __init__(self, player):
        self.player = player

    def enter(self):
        self.player.air_jumps = config.AIR_JUMPS

    def update(self, dt):
        player = self.player
        if player.jump_buffer > 0:
            player.jump()
        elif player.slide_buffer > 0 and player.s_held:
            player.change_state(player.slide_state)
        elif not player.on_ground:
            player.change_state(player.jump_state)


class Slide:
    COLOR = (200, 140, 40)

    def __init__(self, player):
        self.player = player
        self.timer = 0

    def enter(self):
        self.timer = 0
        self.player.slide_buffer = 0

    def update(self, dt):
        player = self.player
        self.timer += dt
        if not player.on_ground:
            player.change_state(player.jump_state)
        elif not player.s_held or self.timer >= config.SLIDE_MAX_TIME:
            player.change_state(player.run_state)


class Jump:
    COLOR = (40, 160, 90)

    def __init__(self, player):
        self.player = player

    def enter(self):
        pass

    def update(self, dt):
        player = self.player
        if player.on_ground:
            player.change_state(player.run_state)
            # 착지 직전에 누른 입력이 같은 프레임에 이어지도록 Run에 바로 넘긴다.
            player.run_state.update(dt)
        elif player.jump_buffer > 0 and player.air_jumps > 0:
            player.air_jumps -= 1
            player.jump()


class Hit:
    COLOR = (200, 60, 60)

    def __init__(self, player):
        self.player = player
        self.timer = 0

    def enter(self):
        self.timer = 0

    def update(self, dt):
        player = self.player
        self.timer += dt
        if self.timer >= config.HIT_STUN_TIME:
            player.change_state(player.run_state if player.on_ground else player.jump_state)


class Player:
    def __init__(self):
        self.x = config.PLAYER_SCREEN_X
        self.y = config.GROUND_TOP
        self.prev_y = self.y
        self.vy = 0
        self.on_ground = True
        self.air_jumps = config.AIR_JUMPS
        self.jump_buffer = 0
        self.slide_buffer = 0
        self.s_held = False
        self.hp = config.HP_MAX
        self.invincible_timer = 0

        self.run_state = Run(self)
        self.slide_state = Slide(self)
        self.jump_state = Jump(self)
        self.hit_state = Hit(self)
        self.state = self.run_state

    def change_state(self, state):
        self.state = state
        state.enter()

    def jump(self):
        self.vy = config.JUMP_SPEED
        self.jump_buffer = 0
        self.change_state(self.jump_state)

    def handle_event(self, event):
        if event.type == SDL_KEYDOWN and event.key == SDLK_w:
            self.jump_buffer = config.INPUT_BUFFER
        elif event.type == SDL_KEYDOWN and event.key == SDLK_s:
            self.s_held = True
            self.slide_buffer = config.INPUT_BUFFER
        elif event.type == SDL_KEYUP and event.key == SDLK_s:
            self.s_held = False

    def update(self, dt):
        self.state.update(dt)
        self.jump_buffer = max(0, self.jump_buffer - dt)
        self.slide_buffer = max(0, self.slide_buffer - dt)
        self.invincible_timer = max(0, self.invincible_timer - dt)

        self.x += config.SCROLL_SPEED * dt

        # 등가속도 공식을 그대로 써서 프레임 수와 무관하게 점프 높이가 같게 한다.
        gravity = config.GRAVITY if self.vy > 0 else config.GRAVITY * config.FALL_GRAVITY_RATIO
        self.prev_y = self.y
        self.y += self.vy * dt - gravity * dt * dt / 2
        self.vy -= gravity * dt
        # 다음 충돌 처리에서 지면에 닿으면 다시 True가 된다.
        self.on_ground = False

    def draw(self, camera):
        left, bottom, right, top = self.get_bb()
        draw_rectangle(left - camera.x, bottom, right - camera.x, top, *self.state.COLOR, 255, True)

    def get_bb(self):
        half_w = config.PLAYER_W / 2
        h = config.SLIDE_H if self.state is self.slide_state else config.PLAYER_H
        return self.x - half_w, self.y, self.x + half_w, self.y + h

    def take_damage(self):
        if self.invincible_timer > 0:
            return
        self.hp -= 1
        self.invincible_timer = config.INVINCIBLE_TIME
        # player:ground 그룹을 먼저 처리하므로 이번 프레임의 착지 여부가 이미 반영되어 있다.
        if self.on_ground:
            self.change_state(self.hit_state)

    def handle_collision(self, group, other):
        if group == 'player:ground':
            if self.vy <= 0 and self.prev_y >= other.top:
                self.y = other.top
                self.vy = 0
                self.on_ground = True
        else:
            self.take_damage()
