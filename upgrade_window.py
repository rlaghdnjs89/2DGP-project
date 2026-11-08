from pico2d import SDL_BUTTON_LEFT, SDL_KEYDOWN, SDL_MOUSEBUTTONDOWN, SDL_MOUSEMOTION, SDLK_ESCAPE, SDLK_f, draw_rectangle

import config
import game_world
import record
import sound
from sprite import Effect
from ui import Button, draw_text, get_font, mouse_pos, text_width

# 왼쪽의 플레이어와 석상이 보이도록 오른쪽에 둔다.
PANEL_LEFT = 540
PANEL_RIGHT = 1270
PANEL_BOTTOM = 20
PANEL_TOP = 700
PANEL_COLOR = (24, 18, 40)
BORDER_COLOR = (240, 240, 250)
LIST_LEFT = 552
LIST_RIGHT = 1040
LIST_TOP = 628
ROW_H = 76
ROW_GAP = 4
ROW_COLOR = (38, 30, 62)
ROW_HOVER = (62, 50, 100)
PIP_W = 16
PIP_H = 10
PIP_ON = (255, 214, 90)
PIP_OFF = (70, 62, 96)
DETAIL_LEFT = 1054
DETAIL_RIGHT = 1258
BIG_SIZE = 24
SMALL_SIZE = 12
GOLD_COLOR = (255, 214, 90)
SUB_COLOR = (200, 195, 220)
DENY_COLOR = (255, 80, 80)
CHALLENGE_BUTTON = ((LIST_LEFT + LIST_RIGHT) / 2, 62, 200, 56)
UPGRADE_FX_SPEED = 1.5


def draw_wrapped(size, x, y, text, width, color=SUB_COLOR):
    """width에 맞춰 글자 단위로 줄을 바꾼다. 다음 줄의 y를 돌려준다."""
    font = get_font(size)
    line = ''
    for char in text:
        if text_width(font, line + char) > width:
            draw_text(size, x, y, line, color)
            y -= size + 6
            line = char.lstrip()
        else:
            line += char
    if line:
        draw_text(size, x, y, line, color)
        y -= size + 6
    return y


class StatRow:
    def __init__(self, name, index):
        self.name = name
        self.info = config.STATS[name]
        self.top = LIST_TOP - index * (ROW_H + ROW_GAP)
        self.bottom = self.top - ROW_H

    def contains(self, x, y):
        return LIST_LEFT <= x <= LIST_RIGHT and self.bottom <= y <= self.top

    def value_text(self):
        now = self.info['format'].format(record.stat(self.name))
        if record.next_stat_cost(self.name) is None:
            return now
        return f'{now} → {self.info["format"].format(record.stat(self.name) + self.info["step"])}'

    def draw(self, hover):
        draw_rectangle(LIST_LEFT, self.bottom, LIST_RIGHT, self.top, *(ROW_HOVER if hover else ROW_COLOR), 255, True)
        x = LIST_LEFT + 12
        draw_text(BIG_SIZE, x, self.top - 24, self.info['name'])
        for i in range(len(self.info['costs'])):
            left = x + i * (PIP_W + 4)
            pip_top = self.bottom + 12 + PIP_H
            color = PIP_ON if i < record.data['stats'][self.name] else PIP_OFF
            draw_rectangle(left, self.bottom + 12, left + PIP_W, pip_top, *color, 255, True)
        draw_text(BIG_SIZE, x + 128, self.top - 24, self.value_text())
        draw_text(SMALL_SIZE, x + 128, self.bottom + 16, self.info['effect'], SUB_COLOR)
        cost = record.next_stat_cost(self.name)
        if cost is None:
            draw_text(BIG_SIZE, LIST_RIGHT - 12, (self.top + self.bottom) / 2, 'MAX', SUB_COLOR, align=1)
        else:
            color = GOLD_COLOR if record.data['gold'] >= cost else DENY_COLOR
            draw_text(BIG_SIZE, LIST_RIGHT - 12, (self.top + self.bottom) / 2, f'{cost}G', color, align=1)

    def draw_detail(self, y):
        y = draw_wrapped(BIG_SIZE, DETAIL_LEFT, y, self.info['name'], DETAIL_RIGHT - DETAIL_LEFT, (250, 250, 250)) - 8
        y = draw_wrapped(SMALL_SIZE, DETAIL_LEFT, y, self.info['effect'], DETAIL_RIGHT - DETAIL_LEFT) - 12
        y = draw_wrapped(BIG_SIZE, DETAIL_LEFT, y, self.value_text(), DETAIL_RIGHT - DETAIL_LEFT, GOLD_COLOR) - 12
        level = record.data['stats'][self.name]
        draw_wrapped(SMALL_SIZE, DETAIL_LEFT, y, f'단계 {level} / {len(self.info["costs"])}', DETAIL_RIGHT - DETAIL_LEFT)

    def buy(self, player):
        if record.buy_stat(self.name):
            player.apply_stats()
            return True
        return False


class UpgradeWindow:
    """진화의 원석 앞에서 F로 여는 강화 창. 여는 동안 세계는 멈추고 이펙트만 움직인다."""

    def __init__(self, player, altar):
        self.player = player
        self.altar = altar
        self.rows = [StatRow(name, i) for i, name in enumerate(config.STATS)]
        self.hover = None
        self.button = Button(*CHALLENGE_BUTTON, '도전')
        self.effect = None
        game_world.add_object(self, game_world.LAYER_UI)

    def close(self):
        game_world.remove_object(self)
        self.player.window = None

    def row_at(self, x, y):
        return next((row for row in self.rows if row.contains(x, y)), None)

    def handle_event(self, event):
        if event.type == SDL_KEYDOWN and event.key in (SDLK_f, SDLK_ESCAPE):
            self.close()
        elif event.type == SDL_MOUSEMOTION:
            x, y = mouse_pos(event)
            self.hover = self.row_at(x, y)
            self.button.hover = self.button.contains(x, y)
        elif event.type == SDL_MOUSEBUTTONDOWN and event.button == SDL_BUTTON_LEFT:
            x, y = mouse_pos(event)
            if self.button.contains(x, y):
                self.close()
                self.altar.start_challenge()
                return
            row = self.row_at(x, y)
            if row:
                self.try_buy(row)

    def try_buy(self, row):
        if not row.buy(self.player):
            sound.play('deny')
            return
        sound.play('upgrade')
        # 연달아 사도 빛이 겹겹이 쌓이지 않게 새 연출로 바꾼다.
        if self.effect:
            game_world.remove_object(self.effect)
        self.effect = Effect('level-up', self.altar.x, config.GROUND_TOP, speed=UPGRADE_FX_SPEED)
        game_world.add_object(self.effect, game_world.LAYER_EFFECT)

    def update(self, dt):
        pass

    def draw(self, camera):
        draw_rectangle(PANEL_LEFT, PANEL_BOTTOM, PANEL_RIGHT, PANEL_TOP, *PANEL_COLOR, 255, True)
        draw_rectangle(PANEL_LEFT, PANEL_BOTTOM, PANEL_RIGHT, PANEL_TOP, *BORDER_COLOR, 255, False)
        draw_text(BIG_SIZE, LIST_LEFT, PANEL_TOP - 32, '진화의 원석')
        draw_text(BIG_SIZE, PANEL_RIGHT - 12, PANEL_TOP - 26, f'골드 {record.data["gold"]:,}', GOLD_COLOR, align=1)
        draw_text(SMALL_SIZE, PANEL_RIGHT - 12, PANEL_TOP - 50, f'이번 런 +{self.player.run_gold:,}', SUB_COLOR, align=1)

        for row in self.rows:
            row.draw(row is self.hover)

        if self.hover:
            self.hover.draw_detail(LIST_TOP - 16)
        else:
            draw_wrapped(SMALL_SIZE, DETAIL_LEFT, LIST_TOP - 16, '항목에 마우스를 올리면 설명과 수치 변화가 나옵니다. 클릭하면 바로 구매합니다.', DETAIL_RIGHT - DETAIL_LEFT)

        self.button.draw()
        draw_text(SMALL_SIZE, DETAIL_LEFT, 62, 'F 또는 ESC로 닫기', SUB_COLOR)
