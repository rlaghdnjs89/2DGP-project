# 에셋 출처

| 파일 | 출처 | 라이선스 |
|---|---|---|
| `fonts/Galmuri11.ttf` | [Galmuri](https://github.com/quiple/galmuri), Lee Minseo | SIL OFL 1.1 (`fonts/Galmuri-OFL.txt`) |
| `player/`, `monster/`(보스, 탄), `map/`(지면, 스테이지 2 발판 제외), `ui/` | 이 프로젝트의 `tools/make_art.py`가 코드로 그림 (Claude와 함께 작성) | 프로젝트 소유 |
| `map/ground_phase*`, `map/platform_phase2`, `map/platform_cap_phase2` | 생성형 AI(Google Gemini)로 만든 지면 그림에서 걷는 면 아래 120px 띠를 잘라 좌우 반전본을 이어 붙임. 발판은 떠 있는 석판의 앞줄을 잘라 만듦 | 프로젝트 소유 |
| `monster/grunt_*`, `goblin_*`, `familiar_*`, `mage_*` | 생성형 AI(Google Gemini)로 만든 시트에서 초록 배경을 지우고 프레임별로 잘라 줄임. 사망 프레임은 첫 프레임을 조각내 만듦 | 프로젝트 소유 |
| `bg/` | 생성형 AI(Google Gemini)로 만든 그림을 1280×720으로 줄이고 근경의 초록 배경을 투명하게 바꾸고 색을 옅게 함. 원경은 좌우 반전본을 이어 붙임 | 프로젝트 소유 |
| `fx/sword-slash` | [pixelfx](https://github.com/patch-gg/pixelfx), `melee/sword-slash`를 `--sheet --no-actor --bg none`으로 렌더링 | MIT, Patch, Hugo Duprez |
| `sound/` | 이 프로젝트의 `tools/make_audio.py`가 코드로 합성함 (Claude와 함께 작성) | 프로젝트 소유 |
| `fx/impact-frame`, `fx/parry`, `fx/hit-spark`, `fx/crit-hit` | pixelfx, `impacts/`의 같은 이름 효과를 같은 방법으로 렌더링 | MIT, Patch, Hugo Duprez |
| `fx/level-up`, `fx/shield-block` | pixelfx, `ui/level-up`, `impacts/shield-block`을 같은 방법으로 렌더링 | MIT, Patch, Hugo Duprez |
| `fx/dagger-flurry` | pixelfx, `melee/dagger-flurry`를 같은 방법에 `--fps 15`를 더해 렌더링 | MIT, Patch, Hugo Duprez |
| `fx/spin-slash`, `fx/thrust`, `fx/double-slash` | pixelfx, `melee/`의 같은 이름 효과를 같은 방법으로 렌더링 | MIT, Patch, Hugo Duprez |
| `fx/heavy-landing` | pixelfx, `impacts/heavy-landing`을 같은 방법으로 렌더링 | MIT, Patch, Hugo Duprez |
| `fx/sword-slash-fire`, `-ice`, `-bolt` | pixelfx, `melee/sword-slash`를 같은 방법에 `--opts`의 `palette`로 색만 바꿔 렌더링 | MIT, Patch, Hugo Duprez |
| `fx/small-explosion`, `fx/ice-shatter` | pixelfx, `explosions/small-explosion`, `ice/ice-shatter`를 같은 방법에 `--fps 15`를 더해 렌더링 | MIT, Patch, Hugo Duprez |
| `fx/burning`, `fx/slowed`, `fx/zap-hit` | pixelfx, `status/burning`, `status/slowed`, `lightning/zap-hit`을 같은 방법으로 렌더링 | MIT, Patch, Hugo Duprez |
| `fx/ground-slam`, `fx/boulder` | pixelfx, `impacts/ground-slam`, `nature/boulder`를 같은 방법에 `--fps 15`를 더해 렌더링 | MIT, Patch, Hugo Duprez |
| `fx/meteor`, `fx/lightning-strike`, `fx/freeze` | pixelfx, `fire/meteor`, `lightning/lightning-strike`, `ice/freeze`를 같은 방법에 `--fps 15`를 더해 렌더링 | MIT, Patch, Hugo Duprez |
| `fx/flame-pillar`, `fx/eclipse` | pixelfx, `fire/flame-pillar`, `shadow/eclipse`를 같은 방법에 `--fps 15`를 더해 렌더링 | MIT, Patch, Hugo Duprez |
| `fx/blink-out`, `fx/blink-in`, `fx/black-hole` | pixelfx, `arcane/blink-out`, `arcane/blink-in`, `shadow/black-hole`을 같은 방법에 `--fps 15`를 더해 렌더링 | MIT, Patch, Hugo Duprez |
| `fx/heavy-cleave`, `fx/charge-up`, `fx/implosion`, `fx/plasma-explosion` | pixelfx, `melee/heavy-cleave`, `lightning/charge-up`, `explosions/implosion`, `explosions/plasma-explosion`을 같은 방법으로 렌더링 | MIT, Patch, Hugo Duprez |
