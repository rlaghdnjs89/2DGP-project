from pico2d import draw_rectangle

import config

GROUND_MARK_GAP = 200


class Ground:
    def __init__(self, left, right):
        self.left = left
        self.right = right
        self.top = config.GROUND_TOP

    def update(self, dt):
        pass

    def draw(self, camera):
        left = self.left - camera.x
        right = self.right - camera.x
        draw_rectangle(left, 0, right, self.top, 90, 80, 70, 255, True)
        # 배경이 없어도 달리는 속도가 보이도록 일정 간격으로 표시한다.
        mark = self.left + (-self.left % GROUND_MARK_GAP)
        while mark < self.right:
            screen_x = mark - camera.x
            draw_rectangle(screen_x, self.top - 12, screen_x + 8, self.top, 60, 52, 45, 255, True)
            mark += GROUND_MARK_GAP

    def get_bb(self):
        return self.left, 0, self.right, self.top

    def handle_collision(self, group, other):
        pass
