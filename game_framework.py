from pico2d import SDL_QUIT, clear_canvas, get_events, get_time, update_canvas

import config


def run(mode):
    mode.init()
    running = True
    last = get_time()
    while running:
        now = get_time()
        # 창을 드래그하는 동안 루프가 멈추면 dt가 커져 지면을 통과할 수 있다.
        dt = min(now - last, config.MAX_DT)
        last = now

        for event in get_events():
            if event.type == SDL_QUIT:
                running = False
            else:
                mode.handle_event(event)

        mode.update(dt)
        clear_canvas()
        mode.draw()
        update_canvas()
