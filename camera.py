import random

import config


class Camera:
    def __init__(self):
        self.base_x = 0
        self.x = 0
        self.y = 0
        self.shake_time = 0
        self.shake_amp = 0

    def follow(self, target, dt):
        # 평소에는 플레이어와 같은 속도로 움직여 간격이 없고, 일섬으로 벌어진 간격만 서서히 줄인다.
        self.base_x += target.speed() * dt
        gap = target.x - config.PLAYER_SCREEN_X - self.base_x
        self.base_x += gap * min(1, config.CAMERA_CATCH_UP * dt)

        self.shake_time = max(0, self.shake_time - dt)
        amp = self.shake_amp if self.shake_time > 0 else 0
        self.x = self.base_x + random.uniform(-amp, amp)
        self.y = random.uniform(-amp, amp)

    def shake(self, time, amp):
        self.shake_time = time
        self.shake_amp = amp
