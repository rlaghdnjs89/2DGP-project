"""생성형 AI로 만든 초록 배경 주인공 시트를 게임용 스트립으로 바꾼다.

실행: python tools/make_player_art.py 1  (Pillow 필요, 게임 실행에는 필요 없다)

tools/player_src/stage<N>/<동작>.png를 읽어 assets/player/stage<N>/<동작>.png로 저장한다.
AI 시트는 프레임 간격, 크기, 발 높이가 제각각이라 프레임을 하나씩 떼어 다시 맞춘다.
- 크기: 시트마다 프레임 면적의 중앙값이 같아지게 줄인다. 실루엣 면적은 자세가 바뀌어도 크게 변하지 않는다.
- 가로: 몸통 중심을 칸 가운데에 둔다. 좌우 반전이 칸 가운데를 축으로 일어나기 때문이다.
- 세로: 발이 칸 맨 아래에 오게 한다. BODY_ALIGNED 시트는 몸통 중심을 서 있을 때와 같은 높이에 둔다.
"""
import heapq
import os
import statistics
import sys
from collections import deque

from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import config  # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
# 서 있는 자세(idle)에서 머리끝부터 발까지의 화면 높이다. 판정 높이(100)보다 상투만큼 크다.
STAND_H = 112
# 자세가 거의 같아서 프레임끼리 면적이 다르면 AI가 크기를 다르게 그린 것이라 프레임마다 맞추는 시트.
# 나머지 시트는 면적 차이가 자세(펼친 소매, 접은 다리) 때문이라 시트 전체를 같은 배율로 줄인다.
PER_FRAME_SCALE = {'idle'}
# 발 대신 몸통 높이를 맞추는 시트. 공중 동작이다.
BODY_ALIGNED = {'rise', 'fall'}
# 줄인 프레임에서 가장자리로부터 이만큼 안쪽을 몸통으로 친다. 칼, 소매 끝, 머리카락은 빠진다.
BODY_R = 3
# 가장 큰 몸통의 이 비율보다 작은 몸통 조각(손, 머리)은 프레임으로 치지 않는다.
FIGURE_RATIO = 0.2
CORE_R = 6
# 몸통에서 이어지지 않은 조각(머리카락 끝)은 이 거리 안의 프레임에 붙이고, 더 멀면 버린다(워터마크, 잡티).
ATTACH_DIST = 40


def key_green(img):
    """초록 배경을 투명하게 하고 가장자리에 번진 초록을 뺀다."""
    out = Image.new('RGBA', img.size)
    src = img.load()
    dst = out.load()
    w, h = img.size
    # 오른쪽 아래의 Gemini 워터마크는 검은 발 위에서 회색으로 남는다.
    mark_x, mark_y = w - w * 0.12, h - h * 0.3
    for y in range(h):
        for x in range(w):
            r, g, b = src[x, y][:3]
            d = g - max(r, b)
            if d >= 120:
                continue
            a = 1 if d <= 20 else 1 - (d - 20) / 100
            if x > mark_x and y > mark_y:
                if d > 20:
                    continue
                if max(r, g, b) - min(r, g, b) < 10 and 40 < r < 130:
                    r = g = b = 0
            dst[x, y] = (r, min(g, max(r, b)), b, round(a * 255))
    return out


def components(mask, w, h):
    label = [[-1] * w for _ in range(h)]
    comps = []
    for sy in range(h):
        for sx in range(w):
            if not mask[sy][sx] or label[sy][sx] >= 0:
                continue
            idx = len(comps)
            pixels = []
            stack = [(sx, sy)]
            label[sy][sx] = idx
            while stack:
                x, y = stack.pop()
                pixels.append((x, y))
                for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if 0 <= nx < w and 0 <= ny < h and mask[ny][nx] and label[ny][nx] < 0:
                        label[ny][nx] = idx
                        stack.append((nx, ny))
            comps.append(pixels)
    return comps


def neighbors(x, y, w, h):
    for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
        if 0 <= nx < w and 0 <= ny < h:
            yield nx, ny


def thickness(mask, w, h):
    """픽셀마다 가장 가까운 배경까지의 거리."""
    dist = [[0 if not mask[y][x] else -1 for x in range(w)] for y in range(h)]
    queue = deque((x, y) for y in range(h) for x in range(w) if not mask[y][x])
    while queue:
        x, y = queue.popleft()
        for nx, ny in neighbors(x, y, w, h):
            if dist[ny][nx] < 0:
                dist[ny][nx] = dist[y][x] + 1
                queue.append((nx, ny))
    return dist


def bbox(pixels):
    xs = [p[0] for p in pixels]
    ys = [p[1] for p in pixels]
    return min(xs), min(ys), max(xs), max(ys)


def box_dist(a, b):
    dx = max(a[0] - b[2], b[0] - a[2], 0)
    dy = max(a[1] - b[3], b[1] - a[3], 0)
    return max(dx, dy)


def split_frames(img):
    w, h = img.size
    alpha = img.getchannel('A').load()
    mask = [[alpha[x, y] > 0 for x in range(w)] for y in range(h)]
    dist = thickness(mask, w, h)
    # 가장자리에서 CORE_R보다 안쪽만 남기면 옆 프레임과 닿은 칼끝, 소매 끝 같은 가는 연결이 끊겨 몸통만 남는다.
    cores = sorted(components([[d > CORE_R for d in row] for row in dist], w, h), key=len, reverse=True)
    cores = [c for c in cores if len(c) >= len(cores[0]) * FIGURE_RATIO]
    # 두꺼운 곳부터 채우면 칼끝과 소매가 닿은 가장 가는 곳에서 두 프레임이 만난다.
    owner = [[-1] * w for _ in range(h)]
    heap = []
    for i, core in enumerate(cores):
        for x, y in core:
            owner[y][x] = i
            heapq.heappush(heap, (-dist[y][x], len(heap), x, y))
    count = len(heap)
    while heap:
        _, _, x, y = heapq.heappop(heap)
        for nx, ny in neighbors(x, y, w, h):
            if mask[ny][nx] and owner[ny][nx] < 0:
                owner[ny][nx] = owner[y][x]
                count += 1
                heapq.heappush(heap, (-dist[ny][nx], count, nx, ny))
    figures = [[] for _ in cores]
    for y in range(h):
        for x in range(w):
            if owner[y][x] >= 0:
                figures[owner[y][x]].append((x, y))
    boxes = [bbox(f) for f in figures]
    loose = [[mask[y][x] and owner[y][x] < 0 for x in range(w)] for y in range(h)]
    for piece in components(loose, w, h):
        dist, i = min((box_dist(bbox(piece), b), i) for i, b in enumerate(boxes))
        if dist <= ATTACH_DIST:
            figures[i].extend(piece)
    figures.sort(key=lambda f: bbox(f)[0])
    frames = []
    src = img.load()
    for pixels in figures:
        left, top, right, bottom = bbox(pixels)
        frame = Image.new('RGBA', (right - left + 1, bottom - top + 1))
        dst = frame.load()
        for x, y in pixels:
            dst[x - left, y - top] = src[x, y]
        frames.append(frame)
    return frames


def area(frame):
    return sum(value * count for value, count in enumerate(frame.getchannel('A').histogram())) / 255


def body_center(frame):
    """칼, 소매, 머리카락은 프레임마다 다르게 펄럭여 실루엣 무게중심을 흔드므로 몸통만으로 중심을 잡는다."""
    w, h = frame.size
    alpha = frame.getchannel('A').load()
    dist = thickness([[alpha[x, y] > 128 for x in range(w)] for y in range(h)], w, h)
    body = [(x, y) for y in range(h) for x in range(w) if dist[y][x] > BODY_R]
    return sum(x for x, _ in body) / len(body), sum(y for _, y in body) / len(body)


def main():
    stage = sys.argv[1]
    src_dir = os.path.join(ROOT, 'tools', 'player_src', f'stage{stage}')
    out_dir = os.path.join(ROOT, 'assets', 'player', f'stage{stage}')
    os.makedirs(out_dir, exist_ok=True)
    sheets = {os.path.splitext(n)[0]: split_frames(key_green(Image.open(os.path.join(src_dir, n)).convert('RGB')))
              for n in sorted(os.listdir(src_dir))}

    # 이 면적이면 서 있는 자세의 키가 STAND_H가 된다.
    target_area = (STAND_H / statistics.median(f.height / area(f) ** 0.5 for f in sheets['idle'])) ** 2
    scaled = {}
    for name, frames in sheets.items():
        if name in PER_FRAME_SCALE:
            scales = [(target_area / area(f)) ** 0.5 for f in frames]
        else:
            scales = [(target_area / statistics.median(map(area, frames))) ** 0.5] * len(frames)
        scaled[name] = [f.resize((round(f.width * s), round(f.height * s)), Image.LANCZOS) for f, s in zip(frames, scales)]
    # 서 있을 때 발에서 몸통 중심까지의 높이.
    stand_center = statistics.median(f.height - body_center(f)[1] for f in scaled['idle'])

    half_w = config.PLAYER_ART_W // 2
    for name, frames in scaled.items():
        placed = []
        for frame in frames:
            cx, cy = body_center(frame)
            # 칸 맨 아래를 0으로 하는 프레임 위쪽 끝의 높이. 땅에 선 동작은 프레임 맨 아래가 발이다.
            top = cy + stand_center if name in BODY_ALIGNED else frame.height
            placed.append((frame, cx, top))
        # 몸통 높이를 맞춘 시트에서 다리가 땅 밑으로 내려가면 시트 전체를 같이 올려 프레임끼리 흔들리지 않게 한다.
        lift = max(0, max(f.height - top for f, _, top in placed))
        placed = [(f, cx, top + lift) for f, cx, top in placed]
        cell_h = round(max(top for _, _, top in placed))
        strip = Image.new('RGBA', (config.PLAYER_ART_W * len(placed), cell_h))
        for i, (frame, cx, top) in enumerate(placed):
            x = round(i * config.PLAYER_ART_W + half_w - cx)
            if x < i * config.PLAYER_ART_W or x + frame.width > (i + 1) * config.PLAYER_ART_W:
                sys.exit(f'{name} {i + 1}번째 프레임이 PLAYER_ART_W({config.PLAYER_ART_W})보다 넓다: 폭 {frame.width}, 중심 {cx:.0f}')
            strip.alpha_composite(frame, (x, round(cell_h - top)))
        strip.save(os.path.join(out_dir, f'{name}.png'))
        print(f'{name}: {len(placed)}프레임, 칸 {config.PLAYER_ART_W}x{cell_h}, 폭 {max(f.width for f, _, _ in placed)}')


main()
