import config


class Camera:
    def __init__(self):
        self.x = 0

    def follow(self, target, dt):
        # 평소에는 플레이어와 같은 속도로 움직여 간격이 없고, 일섬으로 벌어진 간격만 서서히 줄인다.
        self.x += config.SCROLL_SPEED * dt
        gap = target.x - config.PLAYER_SCREEN_X - self.x
        self.x += gap * min(1, config.CAMERA_CATCH_UP * dt)
