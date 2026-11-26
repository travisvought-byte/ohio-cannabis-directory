"""A chiptune shanty bed for the Pillage the Reefer promo, plus the game's own sound effects.

The effects are the same oscillator recipes the game plays (pillage/game.js sfx()).
Writes a 44.1 kHz stereo WAV.
"""
import sys, wave
import numpy as np

SR = 44100
NOTE = {'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3, 'E': 4, 'F': 5, 'F#': 6, 'Gb': 6, 'G': 7, 'G#': 8, 'Ab': 8, 'A': 9, 'A#': 10, 'Bb': 10, 'B': 11}


def hz(n):
    name, octv = n[:-1], int(n[-1])
    midi = 12 * (octv + 1) + NOTE[name]
    return 440.0 * 2 ** ((midi - 69) / 12)


def osc(kind, f, dur, f_to=None):
    t = np.arange(int(dur * SR)) / SR
    if f_to:
        k = np.log(f_to / f) / dur
        phase = 2 * np.pi * f * (np.exp(k * t) - 1) / k
    else:
        phase = 2 * np.pi * f * t
    if kind == 'sine':
        return np.sin(phase)
    if kind == 'square':
        return np.sign(np.sin(phase)) * 0.8
    if kind == 'triangle':
        return 2 / np.pi * np.arcsin(np.sin(phase))
    if kind == 'saw':
        return 2 * ((phase / (2 * np.pi)) % 1) - 1
    raise ValueError(kind)


def env(n, a=0.006, r=0.05, sustain=1.0, decay=None):
    e = np.ones(n) * sustain
    na, nr = max(1, int(a * SR)), max(1, int(r * SR))
    e[:na] = np.linspace(0, 1, na)
    if decay:
        e[na:] = np.exp(-np.arange(n - na) / (decay * SR))
    e[-nr:] *= np.linspace(1, 0, nr)
    return e


def game_tone(f, dur, kind, vol, f_to=None):
    """The game's tone(): exponential attack to vol in 12 ms, exponential fall to silence over dur."""
    n = int((dur + 0.03) * SR)
    t = np.arange(n) / SR
    g = np.where(t < 0.012, 0.0001 * (vol / 0.0001) ** (t / 0.012), vol * (0.0001 / vol) ** np.clip((t - 0.012) / max(1e-3, dur - 0.012), 0, 1))
    return osc(kind, f, n / SR, f_to * 1.0 if f_to else None)[:n] * g


def sfx(name):
    parts = []
    if name == 'coin':
        parts = [(0, 1046, 0.08, 'square', 0.04), (0.07, 1568, 0.14, 'square', 0.04)]
    elif name == 'pickup':
        parts = [(0, 523, 0.1, 'triangle', 0.09), (0.09, 784, 0.16, 'triangle', 0.09)]
    elif name == 'boom':
        parts = [(0, 150, 0.45, 'saw', 0.08, 45)]
    elif name == 'fanfare':
        parts = [(i * 0.13, f, 0.24, 'triangle', 0.09) for i, f in enumerate([523, 659, 784, 1046])]
    elif name == 'splash':
        parts = [(0, 320, 0.3, 'sine', 0.07, 90)]
    out = np.zeros(int(1.2 * SR))
    for p in parts:
        at, f, dur, kind, vol = p[:5]
        to = p[5] if len(p) > 5 else None
        s = game_tone(f, dur, kind, vol, to)
        i = int(at * SR)
        out[i:i + len(s)] += s[:len(out) - i]
    return out


# A jig in 6/8, D minor, dotted quarter = 100. Each entry: (note or None, length in eighths).
PHRASE_A = [
    [('A4', 1), ('D5', 1), ('D5', 1), ('D5', 1), ('E5', 1), ('F5', 1)],
    [('E5', 1), ('D5', 1), ('C5', 1), ('D5', 2), ('A4', 1)],
    [('G4', 1), ('C5', 1), ('C5', 1), ('C5', 1), ('D5', 1), ('E5', 1)],
    [('D5', 1), ('C5', 1), ('A4', 1), ('C5', 2), ('G4', 1)],
    [('A4', 1), ('D5', 1), ('D5', 1), ('D5', 1), ('E5', 1), ('F5', 1)],
    [('G5', 1), ('F5', 1), ('E5', 1), ('F5', 1), ('E5', 1), ('D5', 1)],
    [('E5', 1), ('C#5', 1), ('A4', 1), ('E5', 1), ('C#5', 1), ('A4', 1)],
    [('C#5', 1), ('D5', 1), ('E5', 1), ('A4', 3)],
]
PHRASE_B = [
    [('F5', 1), ('E5', 1), ('D5', 1), ('A5', 2), ('F5', 1)],
    [('G5', 1), ('F5', 1), ('E5', 1), ('D5', 2), ('A4', 1)],
    [('E5', 1), ('D5', 1), ('C5', 1), ('G5', 2), ('E5', 1)],
    [('F5', 1), ('E5', 1), ('D5', 1), ('C5', 2), ('G4', 1)],
    [('A4', 1), ('D5', 1), ('F5', 1), ('A5', 1), ('G5', 1), ('F5', 1)],
    [('Bb5', 1), ('A5', 1), ('G5', 1), ('F5', 1), ('E5', 1), ('D5', 1)],
    [('E5', 1), ('C#5', 1), ('A4', 1), ('E5', 1), ('G5', 1), ('E5', 1)],
    [('C#5', 1), ('E5', 1), ('C#5', 1), ('D5', 3)],
]
CHORDS_A = ['D', 'D', 'C', 'C', 'D', 'D', 'A', 'A']
CHORDS_B = ['D', 'D', 'C', 'C', 'D', 'Bb', 'A', 'D']
BASS = {'D': ('D3', 'A2'), 'C': ('C3', 'G2'), 'Bb': ('Bb2', 'F2'), 'A': ('A2', 'E2')}
EIGHTH = 0.2


def music(total):
    out = np.zeros(int((total + 8) * SR))
    lead_l = np.zeros_like(out)
    bars = [(PHRASE_A, CHORDS_A), (PHRASE_B, CHORDS_B), (PHRASE_A, CHORDS_A), (PHRASE_B, CHORDS_B)]
    t = 0.0
    rng = np.random.default_rng(7)
    for phrase, chords in bars:
        for bar, ch in zip(phrase, chords):
            if t > total + 1:
                break
            # lead
            tt = t
            for note, ln in bar:
                dur = ln * EIGHTH
                if note:
                    s = osc('triangle', hz(note), dur * 0.92) * env(int(dur * 0.92 * SR), a=0.004, r=0.04, decay=0.5)
                    s += 0.25 * osc('square', hz(note), dur * 0.92) * env(int(dur * 0.92 * SR), a=0.004, r=0.04, decay=0.12)
                    i = int(tt * SR)
                    lead_l[i:i + len(s)] += 0.16 * s
                tt += dur
            # bass: root on the beat, fifth on the third eighth of each half
            r1, r5 = BASS[ch]
            for half in range(2):
                bt = t + half * 3 * EIGHTH
                for note, at, ln in [(r1, 0, 2), (r5, 2, 1)]:
                    d = ln * EIGHTH * 0.85
                    s = osc('square', hz(note), d) * env(int(d * SR), a=0.003, r=0.03, decay=0.18)
                    s = np.convolve(s, np.ones(6) / 6, mode='same')  # soften the square
                    i = int((bt + at * EIGHTH) * SR)
                    out[i:i + len(s)] += 0.075 * s
                # kick on each beat
                kd = 0.22
                k = osc('sine', 110, kd, 42) * env(int(kd * SR), a=0.001, r=0.02, decay=0.06)
                i = int(bt * SR)
                out[i:i + len(k)] += 0.34 * k
                # light hats on the off eighths
                for e in (1, 2):
                    hd = 0.05
                    h = rng.standard_normal(int(hd * SR)) * env(int(hd * SR), a=0.001, r=0.01, decay=0.012)
                    h = np.diff(h, prepend=0)  # brighter
                    i = int((bt + e * EIGHTH) * SR)
                    out[i:i + len(h)] += (0.035 if e == 2 else 0.022) * h
            t += 6 * EIGHTH
    return out, lead_l


def build(total, events, path):
    bed, lead = music(total)
    n = int(total * SR)
    bed, lead = bed[:n], lead[:n]
    fx = np.zeros(n)
    for at, name, gain in events:
        s = sfx(name) * gain
        i = int(at * SR)
        fx[i:i + len(s)] += s[:max(0, n - i)]
    # duck the music a little under each effect
    duck = np.ones(n)
    for at, name, gain in events:
        i, j = int(at * SR), int((at + 0.6) * SR)
        duck[i:j] = np.minimum(duck[i:j], 0.55)
    duck = np.convolve(duck, np.ones(2205) / 2205, mode='same')
    # fade in and out
    fade = np.ones(n)
    fi, fo = int(0.25 * SR), int(1.4 * SR)
    fade[:fi] = np.linspace(0, 1, fi)
    fade[-fo:] = np.linspace(1, 0, fo) ** 1.5
    mus_l = (bed + lead * 1.0) * duck
    mus_r = (bed + lead * 0.8) * duck
    # a short room echo on the lead for width
    d = int(0.11 * SR)
    mus_r[d:] += 0.18 * lead[:-d] * duck[d:]
    L = (mus_l + fx) * fade
    R = (mus_r + fx) * fade
    peak = max(np.abs(L).max(), np.abs(R).max())
    L, R = L / peak * 0.89, R / peak * 0.89
    st = np.stack([L, R], axis=1)
    pcm = (st * 32767).astype('<i2')
    with wave.open(path, 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


if __name__ == '__main__':
    build(28.0, [(5.0, 'coin', 4.0), (9.0, 'fanfare', 2.5), (14.0, 'boom', 5.0), (14.3, 'fanfare', 2.5)], sys.argv[1] if len(sys.argv) > 1 else 'test.wav')
    print('ok')
