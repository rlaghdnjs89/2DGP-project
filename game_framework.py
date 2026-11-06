from pico2d import SDL_QUIT, clear_canvas, get_events, get_time, update_canvas

import config


current_mode = None
running = True


def change_mode(mode):
    global current_mode
    current_mode = mode
    mode.init()


def quit():
    global running
    running = False


def run(mode):
    global running
    change_mode(mode)
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
                current_mode.handle_event(event)

        current_mode.update(dt)
        clear_canvas()
        current_mode.draw()
        update_canvas()
