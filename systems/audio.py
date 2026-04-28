"""systems/audio.py — AudioManager: music and SFX wrapper.

All file paths are treated as optional — if a sound or music file does not
exist the call is silently ignored so the game runs without any audio assets.

Usage:
    from systems.audio import audio   # module-level singleton
    audio.play_sfx("attack")
    audio.play_music(MUSIC_LEVEL_5)
"""

import os
import pygame
from settings import (
    AUDIO_MUSIC_VOLUME, AUDIO_SFX_VOLUME,
    SOUND_ATTACK, SOUND_HIT, SOUND_JUMP, SOUND_DEATH,
    SOUND_CHECKPOINT, SOUND_ABILITY, SOUND_BOSS_PHASE,
)

# Key names for play_sfx()
_SFX_KEYS = {
    "attack":     SOUND_ATTACK,
    "hit":        SOUND_HIT,
    "jump":       SOUND_JUMP,
    "death":      SOUND_DEATH,
    "checkpoint": SOUND_CHECKPOINT,
    "ability":    SOUND_ABILITY,
    "boss_phase": SOUND_BOSS_PHASE,
}


class AudioManager:
    def __init__(self):
        self._sounds: dict = {}
        self._sfx_volume   = AUDIO_SFX_VOLUME
        self._music_volume = AUDIO_MUSIC_VOLUME
        self._mixer_ok     = False

        try:
            pygame.mixer.pre_init(44100, -16, 2, 512)
            pygame.mixer.init()
            self._mixer_ok = True
        except pygame.error:
            return

        for key, path in _SFX_KEYS.items():
            if path and os.path.exists(path):
                try:
                    snd = pygame.mixer.Sound(path)
                    snd.set_volume(self._sfx_volume)
                    self._sounds[key] = snd
                except pygame.error:
                    pass

    # ------------------------------------------------------------------

    def play_sfx(self, key: str) -> None:
        if not self._mixer_ok:
            return
        snd = self._sounds.get(key)
        if snd:
            snd.play()

    def play_music(self, path: str, loops: int = -1) -> None:
        if not self._mixer_ok or not path or not os.path.exists(path):
            return
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(self._music_volume)
            pygame.mixer.music.play(loops)
        except pygame.error:
            pass

    def stop_music(self) -> None:
        if self._mixer_ok:
            pygame.mixer.music.stop()

    def set_sfx_volume(self, v: float) -> None:
        self._sfx_volume = max(0.0, min(1.0, v))
        for snd in self._sounds.values():
            snd.set_volume(self._sfx_volume)

    def set_music_volume(self, v: float) -> None:
        self._music_volume = max(0.0, min(1.0, v))
        if self._mixer_ok:
            pygame.mixer.music.set_volume(self._music_volume)


# Module-level singleton
audio = AudioManager()
