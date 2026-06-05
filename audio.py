"""
Mr Fi 🐸 — v5
audio.py: Cute built-in sound effects — no files needed.
"""
import math

_mixer_ok = False

def _init():
    global _mixer_ok
    if _mixer_ok:
        return True
    try:
        import pygame
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
        _mixer_ok = True
    except Exception:
        pass
    return _mixer_ok


def _make_wave(freq, ms, vol, shape="sine", decay=True):
    """Generate a numpy stereo wave."""
    import numpy as np
    sr     = 22050
    n      = int(sr * ms / 1000)
    t      = np.linspace(0, ms / 1000, n, False)
    if shape == "sine":
        wave = np.sin(freq * 2 * math.pi * t)
    elif shape == "square":
        wave = np.sign(np.sin(freq * 2 * math.pi * t))
    elif shape == "triangle":
        wave = 2 * np.abs(2 * (t * freq - np.floor(t * freq + 0.5))) - 1
    else:
        wave = np.sin(freq * 2 * math.pi * t)
    if decay:
        env = np.linspace(1.0, 0.0, n) ** 1.5
        wave = wave * env
    wave = (wave * 32767 * vol).astype(np.int16)
    return np.repeat(wave.reshape(-1, 1), 2, axis=1)


def beep(freq=440, ms=80, vol=0.3, shape="sine"):
    """Generic beep — used by Button clicks."""
    if not _init(): return
    try:
        import pygame, numpy as np
        snd = pygame.sndarray.make_sound(_make_wave(freq, ms, vol, shape))
        snd.play()
    except Exception:
        pass


# ── Named cute sound effects ──────────────────────────────────────────────────

def play_click():
    """Soft UI click."""
    beep(660, 55, 0.22, "sine")


def play_coin():
    """Coin pickup — two-note ding."""
    if not _init(): return
    try:
        import pygame, numpy as np
        w1 = _make_wave(880, 60, 0.28, "sine")
        w2 = _make_wave(1320, 80, 0.22, "sine")
        wave = np.concatenate([w1, w2])
        pygame.sndarray.make_sound(wave).play()
    except Exception:
        pass


def play_eat():
    """Eating nom-nom — descending chirps."""
    if not _init(): return
    try:
        import pygame, numpy as np
        parts = []
        for f in [900, 750, 600]:
            parts.append(_make_wave(f, 55, 0.25, "triangle"))
        pygame.sndarray.make_sound(np.concatenate(parts)).play()
    except Exception:
        pass


def play_happy():
    """Happy jingle — ascending arpeggio."""
    if not _init(): return
    try:
        import pygame, numpy as np
        notes = [523, 659, 784, 1047]   # C5 E5 G5 C6
        parts = [_make_wave(f, 70, 0.2, "sine") for f in notes]
        pygame.sndarray.make_sound(np.concatenate(parts)).play()
    except Exception:
        pass


def play_sad():
    """Sad descending tone."""
    if not _init(): return
    try:
        import pygame, numpy as np
        parts = [_make_wave(f, 90, 0.2, "sine") for f in [440, 370, 294]]
        pygame.sndarray.make_sound(np.concatenate(parts)).play()
    except Exception:
        pass


def play_level_up():
    """Level-up fanfare."""
    if not _init(): return
    try:
        import pygame, numpy as np
        notes = [523, 659, 784, 1047, 1047]
        durs  = [60,  60,  60,  80,   120]
        parts = [_make_wave(f, d, 0.25, "sine") for f, d in zip(notes, durs)]
        pygame.sndarray.make_sound(np.concatenate(parts)).play()
    except Exception:
        pass


def play_pat():
    """Pat / petting sound — soft warm chord."""
    if not _init(): return
    try:
        import pygame, numpy as np
        import numpy as np2
        w1 = _make_wave(523, 120, 0.18, "sine")
        w2 = _make_wave(659, 120, 0.14, "sine")
        mixed = ((w1.astype(np2.int32) + w2.astype(np2.int32)) // 2).astype(np2.int16)
        pygame.sndarray.make_sound(mixed).play()
    except Exception:
        pass
