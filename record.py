import json
import os

PATH = 'best_score.json'
VERSION = 1


def load_best():
    try:
        with open(PATH, encoding='utf-8') as f:
            return int(json.load(f)['best'])
    # 첫 실행이면 파일이 없고, 사용자가 고치거나 쓰다 끊기면 내용이 깨져 있을 수 있다.
    except (OSError, ValueError, KeyError, TypeError):
        return 0


def save_best(score):
    # 쓰는 도중에 꺼져도 이전 기록이 남도록 임시 파일에 쓰고 바꿔치기한다.
    temp = PATH + '.tmp'
    with open(temp, 'w', encoding='utf-8') as f:
        json.dump({'version': VERSION, 'best': score}, f)
    os.replace(temp, PATH)
