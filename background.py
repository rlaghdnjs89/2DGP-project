import config
from sprite import get_image


class Background:
    def __init__(self, player):
        self.player = player

    def update(self, dt):
        pass

    def draw(self, camera):
        for path, parallax in config.PHASES[self.player.phase]['background']:
            image = get_image(path)
            w = image.w * config.SPRITE_SCALE
            h = image.h * config.SPRITE_SCALE
            # 이미지 두 장을 이어 그려 화면을 항상 덮는다.
            x = -(camera.x * parallax % w)
            image.draw_to_origin(x, 0, w, h)
            image.draw_to_origin(x + w, 0, w, h)
