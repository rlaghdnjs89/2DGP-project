LAYER_PLAYER = 0
# 플레이어가 구덩이로 떨어질 때 지면 뒤로 가려지도록 지면을 앞에 그린다.
LAYER_MAP = 1

layers = [[], []]
collision_pairs = {}


def add_object(obj, layer):
    layers[layer].append(obj)


def remove_object(obj):
    for layer in layers:
        if obj in layer:
            layer.remove(obj)
    for group_a, group_b in collision_pairs.values():
        if obj in group_a:
            group_a.remove(obj)
        if obj in group_b:
            group_b.remove(obj)


def clear():
    for layer in layers:
        layer.clear()
    collision_pairs.clear()


def update(dt):
    for layer in layers:
        for obj in layer:
            obj.update(dt)


def render(camera):
    for layer in layers:
        for obj in layer:
            obj.draw(camera)


def add_collision_pair(group, a, b):
    group_a, group_b = collision_pairs.setdefault(group, ([], []))
    if a is not None:
        group_a.append(a)
    if b is not None:
        group_b.append(b)


def collide(a, b):
    a_left, a_bottom, a_right, a_top = a.get_bb()
    b_left, b_bottom, b_right, b_top = b.get_bb()
    # 지면에 정확히 닿아 있는 경우도 충돌로 본다. dt가 0인 프레임에 공중 판정이 나면 안 된다.
    return not (a_left > b_right or a_right < b_left or a_bottom > b_top or a_top < b_bottom)


def handle_collisions():
    for group, (group_a, group_b) in collision_pairs.items():
        for a in group_a:
            for b in group_b:
                if collide(a, b):
                    a.handle_collision(group, b)
                    b.handle_collision(group, a)
