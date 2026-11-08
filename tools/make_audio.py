"""게임 효과음과 배경음을 코드로 합성해 assets/sound 아래에 저장한다.

실행: python tools/make_audio.py  (표준 라이브러리만 쓴다, 게임 실행에는 필요 없다)
"""
import math
import os
import random
import struct
import wave

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'sound')
RATE = 22050
NOTE_NAMES = {'C': 0, 'C#': 1, 'D': 2, 'D#': 3, 'E': 4, 'F': 5, 'F#': 6, 'G': 7, 'G#': 8, 'A': 9, 'A#': 10, 'B': 11}


def note_freq(name):
    pitch, octave = name[:-1], int(name[-1])
    semitone = NOTE_NAMES[pitch] + (octave - 4) * 12 - 9
    return 440.0 * 2 ** (semitone / 12)


def save(samples, name, peak=0.8):
    """peak에 맞춰 키운 뒤 16비트 모노 WAV로 저장한다."""
    os.makedirs(ROOT, exist_ok=True)
    top = max(abs(s) for s in samples) or 1
    gain = peak / top
    with wave.open(os.path.join(ROOT, name + '.wav'), 'wb') as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(RATE)
        f.writeframes(b''.join(struct.pack('<h', int(s * gain * 32767)) for s in samples))


def silence(seconds):
    return [0.0] * int(seconds * RATE)


def add(buffer, voice, start=0, gain=1.0):
    begin = int(start * RATE)
    for i, sample in enumerate(voice):
        if begin + i >= len(buffer):
            break
        buffer[begin + i] += sample * gain


def pulse(phase, duty=0.5):
    return 1.0 if (phase % 1.0) < duty else -1.0


def triangle(phase):
    p = phase % 1.0
    return 4 * p - 1 if p < 0.5 else 3 - 4 * p


def tone(freq, seconds, wave_fn=pulse, attack=0.005, decay=0.0, sustain=1.0, release=0.03, slide=0.0, vibrato=0.0):
    count = int(seconds * RATE)
    out = []
    phase = 0.0
    for i in range(count):
        t = i / RATE
        f = freq + slide * t
        if vibrato:
            f *= 1 + vibrato * math.sin(2 * math.pi * 5.5 * t)
        phase += f / RATE
        env = sustain
        if t < attack:
            env = t / attack
        elif t < attack + decay:
            env = 1 - (1 - sustain) * (t - attack) / decay
        if t > seconds - release:
            env *= max(0, (seconds - t) / release)
        out.append(wave_fn(phase) * env)
    return out


def noise(seconds, rng, decay_power=2.0, low_pass=0.0):
    """low_pass는 0~1, 클수록 높은 소리를 깎아 묵직해진다."""
    count = int(seconds * RATE)
    out = []
    last = 0.0
    for i in range(count):
        env = (1 - i / count) ** decay_power
        last = last * low_pass + rng.uniform(-1, 1) * (1 - low_pass)
        out.append(last * env)
    return out


# 효과음 --------------------------------------------------------------------

def make_sfx():
    rng = random.Random(3)
    # 반복해서 듣는 베기는 높낮이가 다른 세 벌을 번갈아 낸다.
    for i, pitch in enumerate((1.0, 1.12, 0.9)):
        slash = silence(0.2)
        add(slash, noise(0.16, rng, 2.2, 0.15), gain=0.8)
        add(slash, tone(1500 * pitch, 0.1, triangle, slide=-9000, release=0.05), gain=0.35)
        save(slash, f'slash_{i}')

    kill = silence(0.25)
    add(kill, noise(0.1, rng, 3, 0.2), gain=0.6)
    add(kill, tone(880, 0.09, pulse, release=0.04), gain=0.3)
    add(kill, tone(1320, 0.14, pulse, release=0.08), 0.05, 0.3)
    save(kill, 'kill')

    dash = silence(0.3)
    add(dash, tone(300, 0.2, triangle, slide=5000, release=0.05), gain=0.5)
    add(dash, noise(0.25, rng, 1.2, 0.3), gain=0.6)
    save(dash, 'dash')

    jump = silence(0.14)
    add(jump, tone(330, 0.12, lambda p: pulse(p, 0.25), slide=1800, release=0.04), gain=0.5)
    save(jump, 'jump', 0.5)

    hurt = silence(0.35)
    add(hurt, tone(180, 0.3, pulse, slide=-300, release=0.1), gain=0.6)
    add(hurt, noise(0.2, rng, 2, 0.5), gain=0.8)
    save(hurt, 'hurt')

    parry = silence(0.4)
    add(parry, tone(2093, 0.3, triangle, release=0.25), gain=0.5)
    add(parry, tone(3136, 0.2, triangle, release=0.18), gain=0.3)
    add(parry, noise(0.05, rng, 2, 0.0), gain=0.6)
    save(parry, 'parry')

    fire = silence(0.22)
    add(fire, tone(700, 0.2, pulse, slide=-2400, release=0.05), gain=0.5)
    save(fire, 'fire', 0.5)

    gate = silence(1.2)
    add(gate, tone(110, 1.1, triangle, slide=500, release=0.3), gain=0.6)
    add(gate, tone(220, 1.1, lambda p: pulse(p, 0.25), slide=1000, release=0.3), gain=0.25)
    add(gate, noise(1.1, rng, 1.5, 0.6), gain=0.7)
    save(gate, 'gate')

    cut = silence(0.9)
    add(cut, noise(0.14, rng, 1.5, 0.0), gain=0.9)
    add(cut, tone(2400, 0.14, triangle, slide=-14000, release=0.04), gain=0.5)
    add(cut, tone(70, 0.8, triangle, slide=-40, release=0.4), 0.05, 1.0)
    add(cut, noise(0.7, rng, 1.6, 0.8), 0.05, 1.0)
    save(cut, 'cut', 0.9)

    wall = silence(0.8)
    add(wall, tone(60, 0.7, pulse, slide=-30, release=0.3), gain=0.4)
    add(wall, noise(0.7, rng, 1.4, 0.75), gain=1.0)
    save(wall, 'wall_break')

    heal = silence(0.5)
    for i, n in enumerate(('A5', 'E6')):
        add(heal, tone(note_freq(n), 0.3, triangle, release=0.2), i * 0.1, 0.6)
    save(heal, 'heal')

    start = silence(0.3)
    for i, n in enumerate(('E5', 'B5')):
        add(start, tone(note_freq(n), 0.12, pulse, release=0.05), i * 0.09, 0.4)
    save(start, 'ui_start')

    over = silence(1.3)
    for i, n in enumerate(('A4', 'F4', 'D4', 'A3')):
        add(over, tone(note_freq(n), 0.42, pulse, release=0.2), i * 0.22, 0.4)
    save(over, 'game_over')

    record = silence(1.2)
    for i, n in enumerate(('G4', 'C5', 'E5', 'G5', 'C6')):
        add(record, tone(note_freq(n), 0.3 if i == 4 else 0.14, pulse, release=0.08), i * 0.11, 0.35)
    add(record, tone(note_freq('C6'), 0.6, triangle, release=0.4), 0.44, 0.4)
    save(record, 'new_record')

    make_boss_sfx()
    make_gold_sfx()


def make_boss_sfx():
    # 위쪽 효과음이 바뀌지 않도록 난수를 따로 쓴다.
    rng = random.Random(11)

    # 차원 절단을 모으는 1.6초(charge-up의 폭발 시점)에 맞춰 점점 커지다가 끊긴다.
    charge = silence(1.6)
    add(charge, tone(55, 1.6, pulse, attack=1.4, slide=40, release=0.02), gain=0.3)
    add(charge, tone(220, 1.6, triangle, attack=1.4, slide=700, vibrato=0.02, release=0.02), gain=0.5)
    add(charge, list(reversed(noise(1.6, rng, 1.6, 0.5))), gain=0.8)
    t, gap = 0.1, 0.22
    while t < 1.58:
        add(charge, tone(rng.uniform(1800, 3200), 0.025, pulse, release=0.015), t, 0.25)
        t += gap
        gap = max(0.03, gap * 0.85)
    save(charge, 'cut_charge', 0.8)

    boom = silence(1.6)
    add(boom, tone(70, 1.5, triangle, slide=-30, release=0.8), gain=1.0)
    add(boom, tone(38, 1.5, pulse, release=1.0), gain=0.35)
    add(boom, noise(1.5, rng, 2.2, 0.85), gain=1.2)
    add(boom, noise(0.25, rng, 2, 0.1), gain=0.6)
    save(boom, 'cut_boom', 0.9)

    slam = silence(0.7)
    add(slam, tone(90, 0.6, triangle, slide=-90, release=0.3), gain=1.0)
    add(slam, noise(0.6, rng, 2.2, 0.8), gain=1.0)
    add(slam, noise(0.06, rng, 2, 0.1), gain=0.5)
    save(slam, 'boss_slam', 0.8)

    hit = silence(0.2)
    add(hit, tone(1320, 0.14, triangle, release=0.1), gain=0.5)
    add(hit, tone(2093, 0.1, pulse, release=0.08), gain=0.2)
    add(hit, noise(0.05, rng, 2, 0.1), gain=0.6)
    save(hit, 'boss_hit', 0.6)

    roar = silence(1.1)
    add(roar, tone(70, 1.0, pulse, attack=0.2, slide=30, vibrato=0.05, release=0.4), gain=0.5)
    add(roar, tone(105, 1.0, lambda p: pulse(p, 0.25), attack=0.2, slide=40, vibrato=0.07, release=0.4), gain=0.3)
    add(roar, noise(1.0, rng, 1.0, 0.75), gain=0.8)
    save(roar, 'boss_roar', 0.8)

    seal = silence(1.0)
    for i, n in enumerate(('A5', 'C6', 'E6', 'A6')):
        add(seal, tone(note_freq(n), 0.3, triangle, release=0.2), i * 0.06, 0.4)
    add(seal, noise(0.7, rng, 2.4, 0.3), 0.18, 0.7)
    add(seal, tone(110, 0.7, triangle, slide=-50, release=0.4), 0.18, 0.7)
    save(seal, 'seal_break', 0.8)

    block = silence(0.3)
    add(block, tone(1760, 0.18, triangle, slide=-400, release=0.14), gain=0.6)
    add(block, tone(2637, 0.12, pulse, release=0.1), gain=0.2)
    add(block, noise(0.08, rng, 2, 0.2), gain=0.7)
    save(block, 'shield_block', 0.7)

    wave = silence(0.5)
    add(wave, tone(70, 0.45, pulse, slide=-30, release=0.2), gain=0.5)
    add(wave, noise(0.45, rng, 1.6, 0.7), gain=1.0)
    save(wave, 'boss_wave', 0.7)

    rock = silence(0.4)
    add(rock, tone(110, 0.3, triangle, slide=-120, release=0.15), gain=0.8)
    add(rock, noise(0.35, rng, 2.4, 0.6), gain=1.0)
    save(rock, 'rock', 0.6)


def make_gold_sfx():
    coin = silence(0.16)
    add(coin, tone(note_freq('B5'), 0.05, pulse, release=0.02), gain=0.4)
    add(coin, tone(note_freq('E6'), 0.12, pulse, release=0.08), 0.04, 0.4)
    save(coin, 'coin', 0.45)

    deny = silence(0.18)
    add(deny, tone(150, 0.08, pulse, release=0.02), gain=0.5)
    add(deny, tone(120, 0.1, pulse, release=0.04), 0.08, 0.5)
    save(deny, 'deny', 0.5)

    upgrade = silence(0.7)
    for i, n in enumerate(('C5', 'E5', 'G5', 'C6')):
        add(upgrade, tone(note_freq(n), 0.3, triangle, release=0.2), i * 0.07, 0.5)
    add(upgrade, tone(note_freq('C7'), 0.3, pulse, release=0.25), 0.28, 0.12)
    save(upgrade, 'upgrade', 0.7)


# 배경음 --------------------------------------------------------------------

def make_track(name, bpm, chords, melody, seed, bass_steps=(0, 2, 4, 6), arp_gain=0.14, lead_wave=None, half_time=False, lead_vibrato=0.0):
    """chords는 마디별 코드 음 이름, melody는 8분음표 단위 음 이름(None은 쉼표)이다. 8마디를 두 번 돌아 이어 붙인다."""
    rng = random.Random(seed)
    beat = 60 / bpm
    eighth = beat / 2
    sixteenth = beat / 4
    bar = beat * 4
    loops = 2
    bars = len(chords) * loops
    out = silence(bars * bar)
    lead_wave = lead_wave or (lambda p: pulse(p, 0.25))

    kick = tone(120, 0.12, triangle, slide=-700, release=0.06)
    snare = noise(0.14, rng, 2.2, 0.15)
    hat = noise(0.03, rng, 2, 0.0)

    for b in range(bars):
        start = b * bar
        chord = chords[b % len(chords)]
        root = note_freq(chord[0])
        for step in range(8):
            t = start + step * eighth
            if half_time:
                if step == 0:
                    add(out, kick, t, 0.6)
                if step == 4:
                    add(out, snare, t, 0.3)
            else:
                if step % 4 == 0:
                    add(out, kick, t, 0.65)
                if step % 4 == 2:
                    add(out, snare, t, 0.35)
            add(out, hat, t, 0.12)
        for step in bass_steps:
            octave = 2 if step % 4 == 2 else 1
            add(out, tone(root / 2 * octave, eighth * 0.9, triangle, release=0.02), start + step * eighth, 0.5)
        for step in range(16):
            n = chord[step % len(chord)]
            add(out, tone(note_freq(n) * 2, sixteenth * 0.85, lambda p: pulse(p, 0.125), release=0.02), start + step * sixteenth, arp_gain)

    # 두 번째 바퀴에서는 한 옥타브 위 소리를 겹쳐 변화를 준다.
    for loop in range(loops):
        loop_start = loop * len(chords) * bar
        i = 0
        while i < len(melody):
            n = melody[i]
            if n is None:
                i += 1
                continue
            length = 1
            while i + length < len(melody) and melody[i + length] == '-':
                length += 1
            t = loop_start + i * eighth
            add(out, tone(note_freq(n), eighth * length * 0.95, lead_wave, release=0.04, vibrato=lead_vibrato), t, 0.3)
            if loop == 1:
                add(out, tone(note_freq(n) * 2, eighth * length * 0.95, triangle, release=0.04), t, 0.12)
            i += length
    save(out, name, 0.7)


def parse(text):
    """'A4 - C5 .'처럼 쓴 멜로디를 목록으로 바꾼다. '-'는 앞 음을 잇고 '.'은 쉼표다."""
    return [None if token == '.' else token for token in text.split()]


def make_music():
    make_track(
        'bgm_phase1', 150,
        [('A3', 'C4', 'E4'), ('F3', 'A3', 'C4'), ('C4', 'E4', 'G4'), ('G3', 'B3', 'D4'),
         ('A3', 'C4', 'E4'), ('F3', 'A3', 'C4'), ('D3', 'F3', 'A3'), ('E3', 'G#3', 'B3')],
        parse('A4 - C5 - E5 D5 C5 B4  A4 - F4 - C5 - A4 -  G4 - C5 - E5 G5 E5 C5  D5 - B4 - G4 A4 B4 D5 '
              'E5 - A5 - G5 E5 D5 C5  F5 - E5 C5 D5 - C5 A4  D5 - F5 - A5 G5 F5 E5  E5 - G#4 B4 E5 - - .'),
        1)
    make_track(
        'bgm_phase2', 120,
        [('D3', 'F3', 'A3'), ('A#2', 'D3', 'F3'), ('G2', 'A#2', 'D3'), ('A2', 'C#3', 'E3'),
         ('D3', 'F3', 'A3'), ('F3', 'A3', 'C4'), ('G2', 'A#2', 'D3'), ('A2', 'C#3', 'E3')],
        parse('A4 - - - F4 - D4 -  A#4 - - - F4 - D4 -  G4 - A#4 - D5 - - -  C#5 - - - A4 - - - '
              'A4 - D5 - F5 - - -  E5 - C5 - A4 - - -  A#4 - G4 - A#4 - D5 -  C#5 - - - - - . .'),
        2, bass_steps=(0, 4), arp_gain=0.2, lead_wave=triangle, half_time=True, lead_vibrato=0.006)
    make_track(
        'bgm_phase3', 176,
        [('E3', 'G3', 'B3'), ('F3', 'A3', 'C4'), ('E3', 'G3', 'B3'), ('D3', 'F#3', 'A3'),
         ('E3', 'G3', 'B3'), ('F3', 'A3', 'C4'), ('G3', 'B3', 'D4'), ('F3', 'A3', 'C4')],
        parse('E5 E5 . E5 F5 - E5 D5  C5 C5 . C5 D5 - E5 C5  B4 E5 G5 - F5 E5 D5 E5  F#5 - D5 - A4 - D5 F#5 '
              'E5 G5 B5 - A5 G5 F5 E5  F5 A5 C6 - B5 A5 G5 F5  G5 - B5 - D6 - B5 G5  A5 - F5 - C5 - E5 -'),
        3, bass_steps=(0, 1, 2, 3, 4, 5, 6, 7), arp_gain=0.1)


if __name__ == '__main__':
    make_sfx()
    make_music()
