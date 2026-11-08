import random

from pico2d import load_music, load_wav

import config

SFX = {
    'slash': ('slash_0', 'slash_1', 'slash_2'),
    'kill': ('kill',),
    'dash': ('dash',),
    'jump': ('jump',),
    'hurt': ('hurt',),
    'parry': ('parry',),
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
    'heal': ('heal',),
    'ui_start': ('ui_start',),
    'game_over': ('game_over',),
    'new_record': ('new_record',),
}

sounds = {}
music = {}
current = None


def load():
    try:
        for name, files in SFX.items():
            sounds[name] = [load_wav(f'assets/sound/{file}.wav') for file in files]
            for sound in sounds[name]:
                sound.set_volume(config.SFX_VOLUME)
        for phase_info in config.PHASES:
            music[phase_info['music']] = load_music(f'assets/sound/{phase_info["music"]}.wav')
    # 오디오 장치가 없는 PC에서는 pico2d가 IOError를 낸다. 소리 없이 게임은 그대로 돌린다.
    except IOError:
        sounds.clear()
        music.clear()


def play(name):
    if name in sounds:
        random.choice(sounds[name]).play()


def play_music(phase):
    global current
    name = config.PHASES[phase]['music']
    if name in music and current != name:
        current = name
        music[name].set_volume(config.MUSIC_VOLUME)
        music[name].repeat_play()


def set_music_volume(volume):
    if current:
        music[current].set_volume(volume)


def stop_music():
    global current
    if current:
        music[current].stop()
        current = None


def pause_music():
    if current:
        music[current].pause()


def resume_music():
    if current:
        music[current].resume()
