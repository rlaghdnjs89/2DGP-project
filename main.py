import os

from pico2d import open_canvas, close_canvas, hide_lattice

import config
import game_framework
import sound
import title_mode

# 에셋과 기록 파일을 상대 경로로 읽으므로 어디서 실행해도 프로젝트 폴더를 기준으로 삼는다.
os.chdir(os.path.dirname(os.path.abspath(__file__)))
open_canvas(config.SCREEN_W, config.SCREEN_H, sync=True)
hide_lattice()
sound.load()
game_framework.run(title_mode)
close_canvas()
