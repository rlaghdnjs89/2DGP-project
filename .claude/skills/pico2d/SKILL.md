---
name: pico2d
description: Blade Shift에서 쓰는 Python pico2d 1.5.1의 실제 API와 함정. pico2d로 창, 게임 루프, 입력, 이미지와 스프라이트, 좌우 반전, 히트박스, 폰트, 사운드 코드를 쓰거나 고칠 때, 또는 그려지는 위치가 어긋나거나 load_image가 실패할 때 사용한다. Use for any pico2d code, game loop, sprite drawing, mouse or keyboard input, or audio in this project.
---

# pico2d

다른 게임 스킬의 엔진 코드를 pico2d로 옮길 때 이 문서를 기준으로 삼는다. 여기에 없는 API는 추측하지 말고 설치된 소스 `site-packages/pico2d/pico2d.py`를 읽는다. pico2d는 충돌 판정, 씬 관리, 애니메이션, 카메라를 제공하지 않으므로 직접 작성한다.

## 기본 루프

```python
from pico2d import *

MAX_DT = 0.05

open_canvas(1280, 720)
hide_lattice()

running = True
last = get_time()
while running:
    now = get_time()
    # 창을 드래그하는 동안 루프가 멈추면 dt가 커져 장애물을 통과하거나 추락한다.
    dt = min(now - last, MAX_DT)
    last = now

    for event in get_events():
        if event.type == SDL_QUIT:
            running = False

    clear_canvas()
    update_canvas()

close_canvas()
```

- `from pico2d import *`로 `SDLK_*`, `SDL_BUTTON_*`, `SDL_KEYDOWN` 같은 SDL 상수도 함께 들어온다.
- `open_canvas`는 기본적으로 vsync가 꺼져 있다. 움직임은 항상 `dt`에 곱해 계산한다.
- `get_events()`는 프레임마다 호출해야 창이 응답한다.
- 히트 스톱이나 불릿 타임은 게임 로직에 넘기는 `dt`만 줄이고, 입력 처리는 계속한다.

## 좌표

| 대상 | 원점과 방향 |
|---|---|
| 그리기, `draw_rectangle` | 왼쪽 아래, y는 위로 증가 |
| 마우스 `event.x`, `event.y` | 왼쪽 위, y는 아래로 증가 |
| `clip_draw`의 `left`, `bottom` | 이미지 왼쪽 아래 |
| `draw`, `clip_draw`의 `x`, `y` | 그림의 **중심** |

마우스 좌표를 게임 좌표로 바꾼다.

```python
mouse_y = get_canvas_height() - 1 - event.y
```

## 함정

- `clear_canvas()`는 기본적으로 회색 바탕에 격자를 그린다. `open_canvas` 직후 `hide_lattice()`를 호출한다.
- `clip_composite_draw`는 `w`, `h`를 생략하면 잘라낸 크기가 아니라 **이미지 전체 크기**로 늘려 그린다. 항상 `w`, `h`를 넘긴다.

  ```python
  image.clip_composite_draw(left, bottom, width, height, 0, 'h', x, y, width, height)
  ```

- `load_image`, `load_font`, `load_wav`, `load_music`은 `open_canvas` 뒤에 호출한다. 파일이 없으면 `IOError`가 나고, 상대 경로는 실행 위치 기준이다.
- `opacify(o)`는 텍스처 자체를 바꾸므로 그 이미지를 쓰는 모든 객체에 남는다. 다 그린 뒤 `opacify(1)`로 되돌린다.
- `Font.draw(x, y, text, color)`의 `x`는 왼쪽 끝, `y`는 세로 중앙이다. 호출할 때마다 텍스처를 새로 만든다. 한글을 쓰려면 한글을 포함한 폰트 파일이 필요하다. 숫자를 그대로 넘기면 `AttributeError`가 나므로 점수는 `str(score)`로 바꿔 넘긴다.
- 키를 누르고 있을 때의 반복 이벤트는 `get_events()`가 걸러낸다. 누른 순간 한 번만 `SDL_KEYDOWN`이 온다. 지속 입력은 `SDL_KEYDOWN`과 `SDL_KEYUP` 사이의 상태로 관리한다.
- `load_music`과 `load_wav`는 오디오 장치가 없으면 `IOError`를 낸다. 볼륨 범위는 0~128이고, 음악은 한 번에 하나만 재생된다.

## 이미지 API

| 호출 | 용도 |
|---|---|
| `draw(x, y, w=None, h=None)` | 전체 이미지, 중심 기준 |
| `draw_to_origin(x, y, w=None, h=None)` | 전체 이미지, 왼쪽 아래 기준 |
| `clip_draw(left, bottom, width, height, x, y, w=None, h=None)` | 스프라이트 시트의 한 칸 |
| `clip_draw_to_origin(left, bottom, width, height, x, y, w=None, h=None)` | 한 칸, 왼쪽 아래 기준 |
| `composite_draw(rad, flip, x, y, w=None, h=None)` | 전체 이미지의 회전, 반전 |
| `clip_composite_draw(left, bottom, width, height, rad, flip, x, y, w, h)` | 한 칸의 회전, 반전 |

`rad`는 라디안이고 양수면 반시계 방향이다. `flip`은 `''`, `'h'`, `'v'`, `'hv'` 중 하나다.

## 입력

| 동작 | 이벤트 |
|---|---|
| `W`, `S`, `Space`, `ESC` | `SDL_KEYDOWN` + `event.key`가 `SDLK_w`, `SDLK_s`, `SDLK_SPACE`, `SDLK_ESCAPE` |
| 좌클릭, 우클릭 | `SDL_MOUSEBUTTONDOWN` + `event.button`이 `SDL_BUTTON_LEFT`, `SDL_BUTTON_RIGHT` |

좌우 동시 클릭 이벤트는 없으므로 두 버튼의 시간차로 판정한다. 평소 좌클릭은 지연 없이 기본 베기를 실행하고, 동시 클릭은 불릿 타임 중에만 받는다. 불릿 타임 중 마우스 입력은 동시 클릭 판정에만 쓴다. 불릿 타임 동안에는 적의 공격과 탄막이 멈추므로 패링 입력이 필요 없다. 플레이어 피격 판정도 장벽만 남기고 끈다.

```python
SIMULTANEOUS_WINDOW = 0.15
OTHER_BUTTON = {SDL_BUTTON_LEFT: SDL_BUTTON_RIGHT, SDL_BUTTON_RIGHT: SDL_BUTTON_LEFT}
press_times = {}

def handle_mouse_down(button):
    if not bullet_time:
        if button == SDL_BUTTON_LEFT:
            slash()
        return

    if button not in OTHER_BUTTON:
        return

    # 불릿 타임으로 느려져도 판정 시간은 변하지 않도록 실제 시간을 쓴다.
    now = get_time()
    other = OTHER_BUTTON[button]
    if other in press_times and now - press_times[other] <= SIMULTANEOUS_WINDOW:
        press_times.clear()
        dimension_cut()
    else:
        press_times[button] = now
```

`event.type == SDL_MOUSEBUTTONDOWN`일 때 `handle_mouse_down(event.button)`을 호출한다. 시각을 `-1.0` 같은 값으로 초기화해 `abs(left - right)`로 비교하면, 두 값이 같은 상태에서 가운데 버튼만 눌러도 발동하므로 그렇게 쓰지 않는다.

## 충돌과 디버그

충돌 판정은 객체마다 `get_bb()`가 `(left, bottom, right, top)`을 돌려주게 하고 AABB로 직접 비교한다. 히트박스는 `draw_rectangle(*obj.get_bb())`로 화면에 그려 확인한다.

## 동작 확인

- `SDL_VIDEODRIVER=dummy`에서는 렌더러가 만들어지지 않아 `load_image`가 실패한다. 실제 창을 띄워서 테스트한다.
- 그려진 결과를 코드로 검사할 때는 `SDL_RenderReadPixels`에 `SDL_PIXELFORMAT_RGBA32`를 쓰고, 화면 전체를 한 번에 읽는다. 렌더러는 `pico2d.pico2d.renderer`다.
