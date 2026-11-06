import config


class Camera:
    def __init__(self):
        self.x = 0

    def follow(self, target):
        self.x = target.x - config.PLAYER_SCREEN_X
