from pico2d import open_canvas, close_canvas, hide_lattice

import config
import game_framework
import play_mode

open_canvas(config.SCREEN_W, config.SCREEN_H, sync=True)
hide_lattice()
game_framework.run(play_mode)
close_canvas()
