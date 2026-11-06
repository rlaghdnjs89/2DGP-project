# Blade Shift

Python + pico2d 2D 횡스크롤 슬래시 러닝 액션.

기획은 [README.md](README.md)와 `블레이드 시프트 — 게임 기획서.pptx`를 따른다. 규칙, 수치, 예외 처리를 사용자에게 묻거나 정하기 전에 기획서부터 확인한다. 둘이 다르면 나중에 결정된 README를 따른다.

## 엔진 규칙

- 엔진은 pico2d로 고정한다. 다른 엔진이나 프레임워크로 바꾸자고 제안하지 않는다.
- pico2d 코드는 `pico2d` 스킬을 기준으로 쓴다. 다른 스킬의 Godot, Unity, Phaser, pygame 코드는 개념 예시로만 읽고, API는 `pico2d` 스킬이나 설치된 pico2d 소스로 확인한 뒤 쓴다.
- `game-development` 스킬이 안내하는 web-games, engine-selection 등 일부 하위 스킬은 설치하지 않았다. 없으면 건너뛴다.

## 코드 규칙

- 요청한 기능에 필요한 코드만 작성한다. 나중을 대비한 코드는 넣지 않는다.
- 두 곳 이상에서 실제로 쓰이기 전에는 공통 클래스나 추상화를 만들지 않는다.
- 파일을 새로 만들기 전에 기존 코드를 재사용할 수 있는지 확인한다.
- 일어날 수 없는 상황을 처리하는 예외 처리를 넣지 않는다.
- 요청과 무관한 코드를 고치거나 정리하지 않는다.
- 코드를 바꿔서 쓰지 않게 된 코드는 바로 지운다.
- 주석은 코드만 봐서는 알 수 없는 이유가 있을 때만 쓴다.
- 스킬의 지침과 이 규칙이 충돌하면 이 규칙을 따른다.

## 작업별 스킬

| 작업 | 스킬 |
|---|---|
| pico2d API, 게임 루프, 스프라이트, 입력 | `pico2d` |
| 구현 전 가정과 완료 기준 정리 | `karpathy-guidelines` |
| 버그 원인 찾기 | `systematic-debugging` |
| 완료라고 말하기 전 실제 실행 확인 | `verification-before-completion` |
| 달리기, 점프, 2단 점프, 슬라이딩 | `platformer` |
| 화면 스크롤, 대시 시 카메라 | `camera-systems` |
| 캐릭터, 몬스터, 배경 에셋 제작과 라이선스 기록 | `create-game-assets` |
| 무한 맵, 장애물 생성 | `procedural-gen`, `level-design` |
| 입력 버퍼 | `input-systems` |
| 불릿 타임 중 좌+우 동시 클릭 판정 | `pico2d` |
| 페이즈별 중력과 속도, 고정 타임스텝 | `physics-tuning` |
| 근접병, 사역마, 탄막 마법사 | `game-ai` |
| 히트 스톱, 화면 흔들림, 불릿 타임 | `game-feel` |
| 베기와 대시 이펙트, 스프라이트 시트 | `pixelfx`, `2d-games`, `game-art` |
| HUD, 타이틀, 결과 화면 | `game-ui-ux` |
| 최고 기록 저장 | `save-systems` |
| 효과음, 배경음 | `audio-design` |
| 프레임 저하 | `performance-optimization` |
| 재미 검증, 범위 조정, 밸런싱 | `prototype-fast`, `game-design` |

## pixelfx 이펙트

저장소는 프로젝트 옆 `C:\BladeShift\pixelfx`에 있다. 그곳에서 시트를 만들고, 게임에 쓸 PNG와 JSON만 이 프로젝트로 복사한다.

```powershell
cd C:\BladeShift\pixelfx
node tools/list.mjs slash
node tools/render.mjs melee/sword-slash --sheet
```

결과물은 `records/<카테고리>/<이름>/`에 생긴다. JSON의 y는 위에서, pico2d의 bottom은 아래에서 세므로 변환해서 그린다. `(x, y)`는 이펙트의 기준점이 놓일 게임 좌표다.

```python
r = frame["frame"]
px, py = meta["meta"]["pixelfx"]["pivot"]
image.clip_draw(r["x"], image.h - r["y"] - r["h"], r["w"], r["h"],
                x + r["w"] / 2 - px, y + py - r["h"] / 2)
```

- 프레임 길이는 `frame["duration"]`(ms)을 쓴다.
- 타격감 수치는 `meta.pixelfx.act`의 `windup`, `hits[].t`, `hits[].freeze`, `hits[].shake`를 쓴다.
- 왼쪽 방향은 기준점도 뒤집어 그린다. `w`, `h`를 생략하면 시트 전체 크기로 늘어나므로 꼭 넘긴다.

  ```python
  image.clip_composite_draw(r["x"], image.h - r["y"] - r["h"], r["w"], r["h"], 0, 'h',
                            x - r["w"] / 2 + px, y + py - r["h"] / 2, r["w"], r["h"])
  ```
