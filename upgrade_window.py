from pico2d import SDL_BUTTON_LEFT, SDL_KEYDOWN, SDL_MOUSEBUTTONDOWN, SDL_MOUSEMOTION, SDLK_ESCAPE, SDLK_f, draw_rectangle

import config
import game_world
import record
import sound
from sprite import Effect, get_image
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
TAB_Y = PANEL_TOP - 32
TAB_W = 110
TAB_H = 40
TAB_X = (760, 880)
COLUMNS = ('sword', 'move', 'fire', 'ice', 'bolt')
NODE_W = 90
NODE_H = 64
NODE_GAP_X = 9
NODE_GAP_Y = 12
TREE_TOP = LIST_TOP - 34
NODE_LEARNED = (214, 176, 70)
NODE_LOCKED = (30, 26, 44)
NODE_LEARNED_TEXT = (30, 20, 10)
LOCK_SIZE = 20
LINE_COLOR = (110, 100, 140)


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


class SkillNode:
    def __init__(self, skill_id):
        self.id = skill_id
        self.info = config.SKILLS[skill_id]
        self.left = LIST_LEFT + COLUMNS.index(self.info['branch']) * (NODE_W + NODE_GAP_X)
        # 1단계 자리가 둘이므로 2단계부터는 한 칸 아래에 놓는다.
        row = self.info['slot'] if self.info['tier'] == 1 else self.info['tier']
        self.top = TREE_TOP - row * (NODE_H + NODE_GAP_Y)

    def contains(self, x, y):
        return self.left <= x <= self.left + NODE_W and self.top - NODE_H <= y <= self.top

    def draw(self, hover):
        learned = record.has_skill(self.id)
        locked = record.skill_lock_reason(self.id)
        if learned:
            fill, text_color = NODE_LEARNED, NODE_LEARNED_TEXT
        elif locked:
            fill, text_color = NODE_LOCKED, SUB_COLOR
        else:
            fill, text_color = (ROW_HOVER if hover else ROW_COLOR), (250, 250, 250)
        right, bottom = self.left + NODE_W, self.top - NODE_H
        draw_rectangle(self.left, bottom, right, self.top, *fill, 255, True)
        draw_rectangle(self.left, bottom, right, self.top, *(BORDER_COLOR if hover else LINE_COLOR), 255, False)
        center_x = self.left + NODE_W / 2
        draw_text(SMALL_SIZE, center_x, self.top - 20, self.info['name'], text_color, align=0.5)
        if learned:
            draw_text(SMALL_SIZE, center_x, bottom + 18, '배움', text_color, align=0.5)
        elif locked:
            get_image('assets/ui/lock.png').draw_to_origin(center_x - LOCK_SIZE / 2, bottom + 6, LOCK_SIZE, LOCK_SIZE)
        else:
            price = record.skill_price(self.id)
            draw_text(SMALL_SIZE, center_x, bottom + 18, f'{price}G', GOLD_COLOR if record.data['gold'] >= price else DENY_COLOR, align=0.5)

    def draw_detail(self, y):
        width = DETAIL_RIGHT - DETAIL_LEFT
        y = draw_wrapped(BIG_SIZE, DETAIL_LEFT, y, self.info['name'], width, (250, 250, 250)) - 8
        y = draw_wrapped(SMALL_SIZE, DETAIL_LEFT, y, f'{config.BRANCH_NAMES[self.info["branch"]]} {self.info["tier"]}단계', width) - 6
        y = draw_wrapped(SMALL_SIZE, DETAIL_LEFT, y, self.info['desc'], width, (250, 250, 250)) - 12
        reason = record.skill_lock_reason(self.id)
        if record.has_skill(self.id):
            text = '이미 배웠습니다. 다시 누르면 취소합니다 (개발자 테스트).' if record.is_dev() else '이미 배웠습니다.'
            draw_wrapped(SMALL_SIZE, DETAIL_LEFT, y, text, width, GOLD_COLOR)
            return
        if reason:
            draw_wrapped(SMALL_SIZE, DETAIL_LEFT, y, reason, width, DENY_COLOR)
            return
        if record.is_element_change(self.id):
            element = record.data['element']
            text = f'각인 변경: {config.ELEMENT_CHANGE_COST}G를 내고 {config.BRANCH_NAMES[element]}에 쓴 {record.element_spent(element)}G를 돌려받습니다.'
            y = draw_wrapped(SMALL_SIZE, DETAIL_LEFT, y, text, width, DENY_COLOR) - 8
        elif self.info['branch'] in config.ELEMENTS and not record.data['element']:
            y = draw_wrapped(SMALL_SIZE, DETAIL_LEFT, y, '처음 사는 각인이 원소를 정합니다.', width) - 8
        draw_wrapped(BIG_SIZE, DETAIL_LEFT, y, f'{record.skill_price(self.id)}G', width, GOLD_COLOR)

    def buy(self, player):
        if record.is_dev() and record.has_skill(self.id):
            record.forget_skill(self.id)
            # 충전 +1을 지우면 남은 충전이 최대를 넘어 충전이 멈추지 않으므로 맞춘다.
            player.dash_charges = min(player.dash_charges, player.max_dash_charges())
            return True
        return record.buy_skill(self.id)


class UpgradeWindow:
    """진화의 원석 앞에서 F로 여는 강화 창. 여는 동안 세계는 멈추고 이펙트만 움직인다."""

    def __init__(self, player, altar):
        self.player = player
        self.altar = altar
        self.tabs = {'stats': [StatRow(name, i) for i, name in enumerate(config.STATS)],
                     'skills': [SkillNode(skill_id) for skill_id in config.SKILLS]}
        self.tab_buttons = {'stats': Button(TAB_X[0], TAB_Y, TAB_W, TAB_H, '능력치'), 'skills': Button(TAB_X[1], TAB_Y, TAB_W, TAB_H, '스킬트리')}
        self.tab = 'stats'
        self.hover = None
        self.button = Button(*CHALLENGE_BUTTON, '도전')
        self.effect = None
        game_world.add_object(self, game_world.LAYER_UI)

    def close(self):
        game_world.remove_object(self)
        self.player.window = None

    def item_at(self, x, y):
        return next((item for item in self.tabs[self.tab] if item.contains(x, y)), None)

    def handle_event(self, event):
        if event.type == SDL_KEYDOWN and event.key in (SDLK_f, SDLK_ESCAPE):
            self.close()
        elif event.type == SDL_MOUSEMOTION:
            x, y = mouse_pos(event)
            self.hover = self.item_at(x, y)
            self.button.hover = self.button.contains(x, y)
            for button in self.tab_buttons.values():
                button.hover = button.contains(x, y)
        elif event.type == SDL_MOUSEBUTTONDOWN and event.button == SDL_BUTTON_LEFT:
            x, y = mouse_pos(event)
            if self.button.contains(x, y):
                self.close()
                self.altar.start_challenge()
                return
            for tab, button in self.tab_buttons.items():
                if button.contains(x, y):
                    self.tab = tab
                    self.hover = None
                    return
            item = self.item_at(x, y)
            if item:
                self.try_buy(item)

    def try_buy(self, item):
        if not item.buy(self.player):
            sound.play('deny')
            return
        sound.play('upgrade')
        # 연달아 사도 빛이 겹겹이 쌓이지 않게 새 연출로 바꾼다.
        if self.effect:
            game_world.remove_object(self.effect)
        self.effect = Effect('level-up', self.altar.x, config.GROUND_TOP, speed=UPGRADE_FX_SPEED)
        game_world.add_object(self.effect, game_world.LAYER_EFFECT)

    def draw_tree_lines(self):
        for i, branch in enumerate(COLUMNS):
            left = LIST_LEFT + i * (NODE_W + NODE_GAP_X)
            center_x = left + NODE_W / 2
            draw_text(SMALL_SIZE, center_x, LIST_TOP - 14, config.BRANCH_NAMES[branch], SUB_COLOR, align=0.5)
            nodes = [node for node in self.tabs['skills'] if node.info['branch'] == branch]
            draw_rectangle(center_x - 1, min(node.top - NODE_H for node in nodes), center_x + 1, max(node.top for node in nodes), *LINE_COLOR, 255, True)

    def update(self, dt):
        pass

    def draw(self, camera):
        draw_rectangle(PANEL_LEFT, PANEL_BOTTOM, PANEL_RIGHT, PANEL_TOP, *PANEL_COLOR, 255, True)
        draw_rectangle(PANEL_LEFT, PANEL_BOTTOM, PANEL_RIGHT, PANEL_TOP, *BORDER_COLOR, 255, False)
        draw_text(BIG_SIZE, LIST_LEFT, PANEL_TOP - 32, '진화의 원석')
        draw_text(BIG_SIZE, PANEL_RIGHT - 12, PANEL_TOP - 26, f'골드 {record.data["gold"]:,}', GOLD_COLOR, align=1)
        draw_text(SMALL_SIZE, PANEL_RIGHT - 12, PANEL_TOP - 50, f'이번 런 +{self.player.run_gold:,}', SUB_COLOR, align=1)

        for tab, button in self.tab_buttons.items():
            button.draw(tab == self.tab)
        if self.tab == 'skills':
            self.draw_tree_lines()
        for item in self.tabs[self.tab]:
            item.draw(item is self.hover)

        if self.hover:
            self.hover.draw_detail(LIST_TOP - 16)
        else:
            draw_wrapped(SMALL_SIZE, DETAIL_LEFT, LIST_TOP - 16, '항목에 마우스를 올리면 설명과 수치 변화가 나옵니다. 클릭하면 바로 구매합니다.', DETAIL_RIGHT - DETAIL_LEFT)

        self.button.draw()
        draw_text(SMALL_SIZE, DETAIL_LEFT, 62, 'F 또는 ESC로 닫기', SUB_COLOR)
