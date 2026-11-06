import random

import config


class Camera:
    def __init__(self):
        self.base_x = 0
        self.x = 0
        self.y = 0
        self.shake_time = 0
        self.shake_total = 1
        self.shake_amp = 0
        self.offset_x = 0

    def follow(self, target, dt):
        # 평소에는 플레이어와 같은 속도로 움직여 간격이 없고, 일섬으로 벌어진 간격만 서서히 줄인다.
        self.base_x += target.speed() * dt
        gap = target.x - config.PLAYER_SCREEN_X - self.base_x
        self.base_x += gap * min(1, config.CAMERA_CATCH_UP * dt)
        self.x = self.base_x + self.offset_x

    def update_shake(self, dt):
        self.shake_time = max(0, self.shake_time - dt)
        # 흔들림이 줄어들며 끝나야 다음 장면으로 자연스럽게 돌아온다.
        amp = self.shake_amp * self.shake_time / self.shake_total
        self.offset_x = random.uniform(-amp, amp)
        self.x = self.base_x + self.offset_x
        self.y = random.uniform(-amp, amp)

    def shake(self, time, amp):
        # 약한 흔들림이 진행 중인 큰 흔들림을 덮어쓰지 않게 한다.
        if amp * time < self.shake_amp * self.shake_time:
            return
        self.shake_time = time
        self.shake_total = time
        self.shake_amp = amp
