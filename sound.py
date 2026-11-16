import random

from pico2d import load_wav

import config

SFX = {
    'slash': ('slash_0', 'slash_1', 'slash_2'),
    'kill': ('kill',),
    'dash': ('dash',),
    'jump': ('jump',),
    'hurt': ('hurt',),
    'parry': ('parry',),
    'coin': ('coin',),
    'deny': ('deny',),
    'upgrade': ('upgrade',),
    'fire': ('fire',),
    'gate': ('gate',),
    'cut': ('cut',),
    'cut_charge': ('cut_charge',),
    'cut_boom': ('cut_boom',),
    'wall_break': ('wall_break',),
    'seal_break': ('seal_break',),
    'boss_roar': ('boss_roar',),
    'boss_hit': ('boss_hit',),
    'boss_slam': ('boss_slam',),
    'shield_block': ('shield_block',),
    'boss_wave': ('boss_wave',),
    'rock': ('rock',),
    'zap': ('zap',),
    'teleport': ('teleport',),
    'blackhole': ('blackhole',),
    'flame': ('flame',),
    'heal': ('heal',),
    'ui_start': ('ui_start',),
    'game_over': ('game_over',),
    'new_record': ('new_record',),
}

sounds = {}


def load():
    try:
        for name, files in SFX.items():
            sounds[name] = [load_wav(f'assets/sound/{file}.wav') for file in files]
            for sound in sounds[name]:
                sound.set_volume(config.SFX_VOLUME)
    # 오디오 장치가 없는 PC에서는 pico2d가 IOError를 낸다. 소리 없이 게임은 그대로 돌린다.
    except IOError:
        sounds.clear()


def play(name):
    if name in sounds:
        random.choice(sounds[name]).play()

