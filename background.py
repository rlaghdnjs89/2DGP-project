import config
from sprite import get_image


def draw_background(stage, camera):
    for path, parallax in config.STAGES[stage]['background']:
        image = get_image(path)
        # 이미지 두 장을 이어 그려 화면을 항상 덮는다. 정수로 맞춰 이음매에 틈이 생기지 않게 한다.
        x = -(int(camera.x * parallax) % image.w)
        image.draw_to_origin(x, 0)
        image.draw_to_origin(x + image.w, 0)


class Background:
    def __init__(self, player):
        self.player = player

    def update(self, dt):
        pass

    def draw(self, camera):
        draw_background(self.player.stage, camera)
