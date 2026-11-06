import game_world


def init():
    game_world.clear()


def handle_event(event):
    pass


def update(dt):
    game_world.update(dt)
    game_world.handle_collisions()


def draw():
    game_world.render(None)
