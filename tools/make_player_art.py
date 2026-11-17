"""Gemini로 만든 초록 배경 플레이어 시트를 게임용 스트립으로 바꾼다.

실행: python tools/make_player_art.py 1  (Pillow 필요, 게임 실행에는 필요 없다)

tools/player_src/stage<N>/<애니메이션>.png 를 읽어 assets/player/stage<N>/ 에 같은 이름의 스트립과 meta.json을 쓴다.
시트의 프레임은 칼이 옆 프레임에 겹치기도 해서 열 간격으로 자를 수 없다.
그래서 몸통(가는 칼과 끈을 깎아 낸 덩어리)을 프레임마다 하나씩 찾고, 각 픽셀을 이어진 길로 가장 가까운 몸통에 붙인다.
"""
import json
import os
import sys
from collections import deque

from PIL import Image, ImageChops, ImageFilter

TOOLS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(TOOLS, '..')

# 화면에서 idle 캐릭터(삿갓 끝부터 발끝까지)의 높이. 보이는 몸이 충돌 판정과 어긋나지 않게 히트박스 PLAYER_H(100)에 맞춘다.
IDLE_HEIGHT = 100
# 발 아래로 남기는 여백. 발이 히트박스 바닥에 닿도록 게임에서 이만큼 내려 그린다.
FOOT_PAD = 2
# 시트마다 캐릭터를 그린 크기가 달라서, 모양이 변하지 않는 삿갓의 원본 너비(hat)로 크기를 맞춘다. 너비는 눈으로 잰 값이다.
# watermark: False면 워터마크가 없는 시트라 구석을 고치지 않는다. hold: 끝까지 재생한 뒤 마지막 프레임에 머문다.
# frames: 시트에서 찾을 프레임 수. erase: 잔상처럼 쓸모없는 부분을 지울 원본 좌표 사각형 (left, top, right, bottom).
# ghost: (y, dy) 원본의 y 위쪽을 dy만큼 위에 있는 줄로 덮어쓴다.
# give: (from, to, 원본 좌표 사각형) 사각형 안에서 from 프레임이 가져간 픽셀을 to 프레임에 준다.
# keep: 찾은 프레임 중 쓸 것. fps: 게임의 기본 재생 속도 대신 쓸 값.
SHEETS = {
    'stage1': {
        'idle': {'frames': 4, 'hat': 426},
        'run': {'frames': 7, 'hat': 102, 'watermark': False},
        'rise': {'frames': 4, 'hat': 491},
        'fall': {'frames': 4, 'hat': 424, 'erase': [(0, 0, 2752, 468)]},
        # 서 있다가 점점 낮아지는 동작이라 반복하지 않고 마지막 프레임에 머문다.
        # 히트박스는 처음부터 낮으므로 낮은 자세에 빨리 닿게 빠르게 재생한다.
        'slide': {'frames': 4, 'hat': 114, 'watermark': False, 'hold': True, 'fps': 16},
        # 위쪽 잔상 줄이 아래 줄을 320px 위로 그대로 복사한 것이라 삿갓 꼭대기와 겹친다.
        # 560 위의 줄은 겹치지 않은 잔상 쪽에서 가져온다.
        # 3번째 프레임의 칼끝이 4번째 프레임 몸에 닿아 칼 앞쪽이 4번째로 넘어가므로 되돌린다.
        'slash': {'frames': 5, 'hat': 340, 'ghost': (560, 320), 'give': [(3, 2, (1900, 690, 2165, 790))]},
        'dash': {'frames': 3, 'hat': 486, 'erase': [(0, 0, 3168, 200)]},
        'hit': {'frames': 3, 'hat': 491},
        'charge': {'frames': 5, 'hat': 335},
        'cut': {'frames': 6, 'hat': 325},
    },
}
WATERMARK_BOX = 450


def remove_watermark(img):
    """Gemini 워터마크(반투명 흰 별)는 오른쪽 아래 구석에 있다. 캐릭터의 밝은 부분을 건드리지 않게 그 구석만 고친다.
    배경 위의 별은 연한 초록이라 배경색으로, 캐릭터 위의 별은 회색이라 어둡게 되돌린다."""
    px = img.load()
    for y in range(img.height - WATERMARK_BOX, img.height):
        for x in range(img.width - WATERMARK_BOX, img.width):
            r, g, b = px[x, y]
            if min(r, g, b) <= 70:
                continue
            if g - max(r, b) > 40:
                px[x, y] = (0, 255, 0)
            else:
                px[x, y] = (r // 5, g // 5, b // 5)


def key_green(img, watermark):
    """초록 배경을 투명하게 하고 가장자리에 번진 초록을 뺀다. 연기처럼 초록과 섞인 픽셀은 반투명이 된다."""
    img = img.convert('RGB')
    if watermark:
        remove_watermark(img)
    r, g, b = img.split()
    green = ImageChops.darker(ImageChops.subtract(g, r), ImageChops.subtract(g, b))
    alpha = green.point(lambda v: 255 if v < 25 else 0 if v > 110 else int(255 * (110 - v) / 85))
    g = ImageChops.darker(g, ImageChops.lighter(r, b))
    return Image.merge('RGBA', (r, g, b, alpha))


def components(mask):
    """mask(0/255 L 이미지)의 연결 요소를 (넓이, 픽셀 목록)으로 돌려준다."""
    w, h = mask.size
    px = mask.load()
    seen = [[False] * w for _ in range(h)]
    found = []
    for y in range(h):
        for x in range(w):
            if px[x, y] and not seen[y][x]:
                seen[y][x] = True
                queue, pixels = deque([(x, y)]), []
                while queue:
                    cx, cy = queue.popleft()
                    pixels.append((cx, cy))
                    for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                        if 0 <= nx < w and 0 <= ny < h and px[nx, ny] and not seen[ny][nx]:
                            seen[ny][nx] = True
                            queue.append((nx, ny))
                found.append(pixels)
    return found


def split_frames(img, count, gives):
    """img를 프레임 count개로 나눠 (프레임 이미지, 몸통 중심 x, 발 y)를 왼쪽부터 돌려준다. 좌표는 img 기준이다."""
    w, h = img.size
    mask = img.getchannel('A').point(lambda v: 255 if v >= 128 else 0)
    core_mask = mask.filter(ImageFilter.MinFilter(7))
    cores = sorted(components(core_mask), key=len, reverse=True)[:count]
    cores.sort(key=lambda pixels: min(x for x, _ in pixels))
    owner = [[-1] * w for _ in range(h)]
    px = mask.load()
    queue = deque()
    for i, pixels in enumerate(cores):
        for x, y in pixels:
            owner[y][x] = i
            queue.append((x, y))
    # 모든 몸통에서 동시에 퍼져 나가 먼저 닿은 몸통이 그 픽셀을 갖는다.
    while queue:
        x, y = queue.popleft()
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < w and 0 <= ny < h and px[nx, ny] and owner[ny][nx] < 0:
                owner[ny][nx] = owner[y][x]
                queue.append((nx, ny))
    # 반투명 가장자리와 연기는 가장 가까운 불투명 픽셀의 주인을 따른다.
    alpha = img.getchannel('A').load()
    queue = deque((x, y) for y in range(h) for x in range(w) if owner[y][x] >= 0)
    while queue:
        x, y = queue.popleft()
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < w and 0 <= ny < h and alpha[nx, ny] and owner[ny][nx] < 0:
                owner[ny][nx] = owner[y][x]
                queue.append((nx, ny))
    for src_frame, dst_frame, (left, top, right, bottom) in gives:
        for y in range(top, bottom):
            for x in range(left, right):
                if owner[y][x] == src_frame:
                    owner[y][x] = dst_frame

    src = img.load()
    frames = []
    for i, pixels in enumerate(cores):
        frame = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        dst = frame.load()
        for y in range(h):
            row = owner[y]
            for x in range(w):
                if row[x] == i:
                    dst[x, y] = src[x, y]
        center_x = (min(x for x, _ in pixels) + max(x for x, _ in pixels)) / 2
        solid = frame.getchannel('A').point(lambda v: 255 if v >= 128 else 0)
        frames.append((frame, center_x, solid.getbbox()[3]))
    return frames


def main(stage):
    name = f'stage{stage}'
    src_dir = os.path.join(TOOLS, 'player_src', name)
    out_dir = os.path.join(ROOT, 'assets', 'player', name)
    os.makedirs(out_dir, exist_ok=True)
    specs = SHEETS[name]
    sheets = {}
    for anim, spec in specs.items():
        sheet = key_green(Image.open(os.path.join(src_dir, anim + '.png')), spec.get('watermark', True))
        if 'ghost' in spec:
            y, dy = spec['ghost']
            copy = Image.new('RGBA', (sheet.width, y), (0, 0, 0, 0))
            copy.paste(sheet.crop((0, 0, sheet.width, y - dy)), (0, dy))
            sheet.paste(copy, (0, 0))
        for box in spec.get('erase', ()):
            sheet.paste((0, 0, 0, 0), box)
        sheets[anim] = sheet

    idle_box = sheets['idle'].getchannel('A').point(lambda v: 255 if v >= 128 else 0).getbbox()
    idle_scale = IDLE_HEIGHT / (idle_box[3] - idle_box[1])

    placed = {}
    for anim, spec in specs.items():
        sheet = sheets[anim]
        scale = idle_scale * specs['idle']['hat'] / spec['hat']
        small = sheet.resize((round(sheet.width * scale), round(sheet.height * scale)), Image.LANCZOS)
        gives = [(a, b, tuple(round(v * scale) for v in box)) for a, b, box in spec.get('give', ())]
        frames = split_frames(small, spec['frames'], gives)
        placed[anim] = [frames[i] for i in spec.get('keep', range(len(frames)))]

    # 뒤집어 그려도 몸통이 같은 자리에 오도록 칸의 가운데를 몸통 중심에 맞춘다.
    half_w = above = 0
    for frames in placed.values():
        for frame, center_x, feet_y in frames:
            left, top, right, _ = frame.getbbox()
            half_w = max(half_w, center_x - left, right - center_x)
            above = max(above, feet_y - top)
    cell_w = int(half_w * 2) + 2
    cell_h = int(above) + FOOT_PAD + 1
    for anim, frames in placed.items():
        strip = Image.new('RGBA', (cell_w * len(frames), cell_h), (0, 0, 0, 0))
        for i, (frame, center_x, feet_y) in enumerate(frames):
            dx = round(i * cell_w + cell_w / 2 - center_x)
            dy = round(cell_h - FOOT_PAD - feet_y)
            box = frame.getbbox()
            strip.alpha_composite(frame.crop(box), (box[0] + dx, box[1] + dy))
        strip.save(os.path.join(out_dir, anim + '.png'))
        print(anim, len(frames), 'frames')
    with open(os.path.join(out_dir, 'meta.json'), 'w', encoding='utf-8') as f:
        fps = {anim: spec['fps'] for anim, spec in specs.items() if 'fps' in spec}
        hold = [anim for anim, spec in specs.items() if spec.get('hold')]
        json.dump({'frame_w': cell_w, 'center_y': cell_h / 2 - FOOT_PAD, 'fps': fps, 'hold': hold}, f)
    print('cell', cell_w, cell_h)


if __name__ == '__main__':
    main(int(sys.argv[1]))
