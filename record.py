import json
import os

PATH = 'save.json'
VERSION = 2


def default_data():
    return {'version': VERSION, 'gold': 0, 'bosses': [], 'best_stage': 0, 'best_clear_time': None}


data = default_data()


def load():
    global data
    data = default_data()
    try:
        with open(PATH, encoding='utf-8') as f:
            loaded = json.load(f)
        if loaded['version'] == VERSION:
            data.update(loaded)
    # 첫 실행이면 파일이 없고, 사용자가 고치거나 쓰다 끊기면 내용이 깨져 있을 수 있다.
    except (OSError, ValueError, KeyError, TypeError):
        pass


def save():
    # 쓰는 도중에 꺼져도 이전 기록이 남도록 임시 파일에 쓰고 바꿔치기한다.
    temp = PATH + '.tmp'
    with open(temp, 'w', encoding='utf-8') as f:
        json.dump(data, f)
    os.replace(temp, PATH)


def reset():
    global data
    data = default_data()
    save()
