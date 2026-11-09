#!/usr/bin/env python3
"""Synthesize the whole SFX palette from scratch (no licensing, no downloads)."""
import numpy as np
from pathlib import Path
import wave

SR = 48000
OUT = Path(__file__).resolve().parent.parent / "assets" / "sfx"
OUT.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(7)


def t(sec):
    return np.linspace(0, sec, int(SR * sec), endpoint=False)


def env(n, a=0.005, d=0.3, curve=4.0):
    e = np.ones(n)
    ai = max(1, int(a * SR / n * n))
    e[:ai] = np.linspace(0, 1, ai)
    e[ai:] = np.exp(-curve * np.linspace(0, 1, n - ai) / d)
    return e


def write(name, x, peak=0.85):
    x = np.asarray(x, dtype=np.float64)
    x = x / (np.max(np.abs(x)) + 1e-9) * peak
    x = np.tanh(x * 1.1) * 0.92
    data = (np.clip(x, -1, 1) * 32767).astype("<i2")
    with wave.open(str(OUT / f"{name}.wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())
    print(f"{name}  {len(x)/SR:.2f}s")


def sine_sweep(f0, f1, dur, curve=2.0):
    n = int(SR * dur)
    u = np.linspace(0, 1, n) ** curve
    f = f0 + (f1 - f0) * u
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph)


def noise(dur):
    return rng.standard_normal(int(SR * dur))


def lp(x, cutoff, order=2):
    y = x.copy()
    for _ in range(order):
        a = np.exp(-2 * np.pi * cutoff / SR)
        b = 1 - a
        acc = 0.0
        out = np.empty_like(y)
        for i in range(len(y)):
            acc = b * y[i] + a * acc
            out[i] = acc
        y = out
    return y


def lp_fast(x, cutoff, order=2):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    mask = 1 / (1 + (f / cutoff) ** (2 * order))
    return np.fft.irfft(X * mask, n=len(x))


def hp_fast(x, cutoff, order=2):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    mask = (f / cutoff) ** (2 * order) / (1 + (f / cutoff) ** (2 * order))
    return np.fft.irfft(X * mask, n=len(x))


# impact
d = 1.15
x = sine_sweep(120, 34, d, 1.6) * env(len(t(d)), 0.002, 0.55, 5)
x += 0.5 * hp_fast(noise(d), 1200) * env(len(t(d)), 0.001, 0.06, 6)
write("impact", x, 0.92)

# whoosh
d = 0.52
n = int(SR * d)
band = hp_fast(lp_fast(noise(d), 2600), 420)
x = band * (np.sin(np.pi * np.linspace(0, 1, n)) ** 2.2)
write("whoosh", x, 0.6)

# whoosh-short
d = 0.30
n = int(SR * d)
x = hp_fast(lp_fast(noise(d), 5000), 900) * (np.sin(np.pi * np.linspace(0, 1, n)) ** 2.6)
write("whoosh-short", x, 0.5)

# pop
d = 0.16
x = sine_sweep(760, 190, d, 0.7) * env(len(t(d)), 0.001, 0.055, 7)
write("pop", x, 0.75)

# click
d = 0.09
x = sine_sweep(1500, 700, d, 0.6) * env(len(t(d)), 0.0005, 0.03, 8)
write("click", x, 0.6)

# key press
d = 0.075
x = hp_fast(noise(d), 2600) * env(len(t(d)), 0.0004, 0.012, 12)
x += 0.45 * np.sin(2 * np.pi * 2100 * t(d)) * env(len(t(d)), 0.0004, 0.010, 12)
write("key", x, 0.55)

# typing burst
segs = []
for i in range(11):
    d = 0.05
    k = hp_fast(noise(d), 2800) * env(len(t(d)), 0.0004, 0.008, 14)
    segs.append(k)
    segs.append(np.zeros(int(SR * (0.045 + rng.random() * 0.035))))
x = np.concatenate(segs)
write("typing", x, 0.5)

# chime (4-note arpeggio)
d = 0.9
x = np.zeros(int(SR * d))
for f, amp, dec in [(1046.5, 1.0, 0.30), (1568.0, 0.55, 0.26), (2093.0, 0.3, 0.20), (523.25, 0.5, 0.45)]:
    x += amp * np.sin(2 * np.pi * f * t(d)) * np.exp(-t(d) / dec)
write("chime", x, 0.7)

# ping
d = 0.45
x = np.sin(2 * np.pi * 1318.5 * t(d)) * np.exp(-t(d) / 0.12)
x += 0.35 * np.sin(2 * np.pi * 1975.5 * t(d)) * np.exp(-t(d) / 0.07)
write("ping", x, 0.55)

# notify (two rising beeps)
d = 0.75
x = np.zeros(int(SR * d))
for start, f in [(0.0, 880.0), (0.17, 1320.0)]:
    i = int(start * SR)
    seg = t(d - start)
    x[i:i + len(seg)] += np.sin(2 * np.pi * f * seg) * np.exp(-seg / 0.22)
write("notify", x, 0.6)

# riser
d = 2.6
n = int(SR * d)
u = np.linspace(0, 1, n)
low = lp_fast(noise(d), 700)
high = hp_fast(lp_fast(noise(d), 9000), 2600)
x = low * (1 - u) + high * u
x *= (u ** 2.1)
x += 0.25 * np.sin(2 * np.pi * (120 + 260 * u ** 2) * np.cumsum(np.ones(n)) / SR) * (u ** 2)
write("riser", x, 0.55)

# error (downward sweep)
d = 0.5
x = np.zeros(int(SR * d))
for start, f in [(0.0, 392.0), (0.12, 294.0)]:
    i = int(start * SR)
    seg = t(d - start)
    x[i:i + len(seg)] += np.sign(np.sin(2 * np.pi * f * seg)) * np.exp(-seg / 0.10) * 0.5
x = lp_fast(x, 3200)
write("error", x, 0.5)

# stamp thud
d = 0.35
x = sine_sweep(180, 60, d, 2.2) * env(len(t(d)), 0.001, 0.09, 6)
x += 0.4 * hp_fast(noise(d), 900) * env(len(t(d)), 0.001, 0.02, 9)
write("stamp", x, 0.8)

print("SFX done ->", OUT)
