import json
import os

import config

PATH = 'save.json'
VERSION = 2


def default_data():
    return {'version': VERSION, 'gold': 0, 'stats': {name: 0 for name in config.STATS}, 'skills': [], 'element': None, 'bosses': [], 'best_stage': 0, 'best_clear_time': None}


data = default_data()
# 개발자 테스트 중에는 진짜 기록을 여기 맡겨 두고, 테스트 기록은 저장하지 않는다.
real_data = None
# 테스트에서 고른 강화는 게임을 끄기 전까지 다음 테스트에도 남는다.
dev_data = None


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


def start_dev():
    """골드가 무제한이고 모든 보스를 잡아 스킬트리 3단계까지 열린 테스트 기록으로 바꾼다."""
    global data, real_data, dev_data
    if real_data is None:
        real_data = data
    if dev_data is None:
        dev_data = default_data()
        dev_data['bosses'] = list(range(len(config.STAGES)))
    dev_data['gold'] = config.DEV_GOLD
    data = dev_data


def end_dev():
    global data, real_data
    if real_data is not None:
        data = real_data
        real_data = None


def reset_dev():
    global dev_data
    dev_data = None


def is_dev():
    return real_data is not None


def save():
    if is_dev():
        return
    # 쓰는 도중에 꺼져도 이전 기록이 남도록 임시 파일에 쓰고 바꿔치기한다.
    temp = PATH + '.tmp'
    with open(temp, 'w', encoding='utf-8') as f:
        json.dump(data, f)
    os.replace(temp, PATH)


def stat(name):
    info = config.STATS[name]
    return info['base'] + info['step'] * data['stats'][name]


def next_stat_cost(name):
    """다음 단계의 비용. 최대 단계면 None이다."""
    costs = config.STATS[name]['costs']
    level = data['stats'][name]
    return costs[level] if level < len(costs) else None


def buy_stat(name):
    cost = next_stat_cost(name)
    if cost is None or data['gold'] < cost:
        return False
    data['gold'] -= cost
    data['stats'][name] += 1
    save()
    return True


def has_skill(skill_id):
    return skill_id in data['skills']


def element_spent(element):
    return sum(config.SKILLS[skill]['cost'] for skill in data['skills'] if config.SKILLS[skill]['branch'] == element)


def is_element_change(skill_id):
    branch = config.SKILLS[skill_id]['branch']
    return branch in config.ELEMENTS and data['element'] not in (None, branch)


def skill_price(skill_id):
    """다른 원소로 바꿀 때는 변경 비용을 더하고, 지금 원소에 쓴 골드를 돌려받는 만큼 뺀다."""
    cost = config.SKILLS[skill_id]['cost']
    if is_element_change(skill_id):
        return cost + config.ELEMENT_CHANGE_COST - element_spent(data['element'])
    return cost


def skill_lock_reason(skill_id):
    """아직 살 수 없는 이유. 살 수 있으면 None이다."""
    info = config.SKILLS[skill_id]
    tier = info['tier']
    if tier == 1:
        return None
    # 보스 번호는 스테이지 순서이고, 2단계는 보스 1(0번), 3단계는 보스 2(1번)가 연다.
    if tier - 2 not in data['bosses']:
        return f'보스 {tier - 1} 처치 후 해금'
    learned = [skill for skill in data['skills'] if config.SKILLS[skill]['branch'] == info['branch'] and config.SKILLS[skill]['tier'] == tier - 1]
    return None if learned else f'{config.BRANCH_NAMES[info["branch"]]} {tier - 1}단계를 먼저 배워야 합니다'


def buy_skill(skill_id):
    price = skill_price(skill_id)
    if has_skill(skill_id) or skill_lock_reason(skill_id) or data['gold'] < price:
        return False
    branch = config.SKILLS[skill_id]['branch']
    if is_element_change(skill_id):
        data['skills'] = [skill for skill in data['skills'] if config.SKILLS[skill]['branch'] != data['element']]
    if branch in config.ELEMENTS:
        data['element'] = branch
    data['gold'] -= price
    data['skills'].append(skill_id)
    save()
    return True


def forget_skill(skill_id):
    """개발자 테스트에서 배운 스킬을 지워 다른 조합을 시험한다."""
    data['skills'].remove(skill_id)
    if not any(config.SKILLS[skill]['branch'] == data['element'] for skill in data['skills']):
        data['element'] = None


def reset():
    global data
    data = default_data()
    save()
