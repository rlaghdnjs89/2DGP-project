import json

from pico2d import load_image

import config
import game_world

images = {}
sheets = {}


def get_image(path):
    if path not in images:
        images[path] = load_image(path)
    return images[path]


class Strip:
    """프레임을 가로로 늘어놓은 이미지. 원본 픽셀을 SPRITE_SCALE배로 그린다."""

    def __init__(self, path, frame_w):
        self.image = get_image(path)
        self.frame_w = frame_w
        self.count = self.image.w // frame_w

    def draw(self, frame, x, y, opacity=1, flip=False):
        w, h = self.frame_w, self.image.h
        scale = config.SPRITE_SCALE
        self.image.opacify(opacity)
        if flip:
            self.image.clip_composite_draw(frame * w, 0, w, h, 0, 'h', x, y, w * scale, h * scale)
        else:
            self.image.clip_draw(frame * w, 0, w, h, x, y, w * scale, h * scale)
        # opacify는 텍스처 자체를 바꾸므로 같은 이미지를 쓰는 다른 객체에 남지 않게 되돌린다.
        self.image.opacify(1)


class OneShot:
    """한 번 재생하고 사라지는 애니메이션. 몬스터 사망에 쓴다."""

    def __init__(self, strip, fps, x, y):
        self.strip = strip
        self.fps = fps
        self.x = x
        self.y = y
        self.time = 0

    def update(self, dt):
        self.time += dt
        if self.time * self.fps >= self.strip.count:
            game_world.remove_object(self)

    def draw(self, camera):
        self.strip.draw(int(self.time * self.fps), self.x - camera.x, self.y - camera.y)


def load_fx_sheet(name):
    if name not in sheets:
        with open(f'assets/fx/{name}.json', encoding='utf-8') as f:
            sheets[name] = json.load(f)
    return get_image(f'assets/fx/{name}.png'), sheets[name]


class Effect:
    """pixelfx 시트를 재생한다. anchor를 주면 anchor를 따라다니고, flip이면 왼쪽을 향하며, loop면 지울 때까지 되풀이한다."""

    def __init__(self, name, x, y, anchor=None, speed=1, scale=config.SPRITE_SCALE, flip=False, loop=False):
        self.image, data = load_fx_sheet(name)
        self.flip = flip
        self.loop = loop
        self.frames = data['frames']
        self.pivot = data['meta']['pixelfx']['pivot']
        self.x = x
        self.y = y
        self.anchor = anchor
        self.speed = speed
        self.scale = scale
        self.index = 0
        self.elapsed = 0

    def update(self, dt):
        self.elapsed += dt * self.speed * 1000
        while self.elapsed >= self.frames[self.index]['duration']:
            self.elapsed -= self.frames[self.index]['duration']
            self.index += 1
            if self.index == len(self.frames) and self.loop:
                self.index = 0
            elif self.index == len(self.frames):
                game_world.remove_object(self)
                self.index -= 1
                return

    def draw(self, camera):
        x, y = self.x, self.y
        if self.anchor:
            x += self.anchor.x
            y += self.anchor.y
        r = self.frames[self.index]['frame']
        scale = self.scale
        px, py = self.pivot
        # JSON의 y는 위에서, pico2d의 bottom은 아래에서 센다.
        bottom = self.image.h - r['y'] - r['h']
        center_y = y - camera.y + (py - r['h'] / 2) * scale
        if self.flip:
            self.image.clip_composite_draw(r['x'], bottom, r['w'], r['h'], 0, 'h',
                                           x - camera.x - (r['w'] / 2 - px) * scale, center_y, r['w'] * scale, r['h'] * scale)
        else:
            self.image.clip_draw(r['x'], bottom, r['w'], r['h'],
                                 x - camera.x + (r['w'] / 2 - px) * scale, center_y, r['w'] * scale, r['h'] * scale)
