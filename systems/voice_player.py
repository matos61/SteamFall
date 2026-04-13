# =============================================================================
# systems/voice_player.py — In-game voice line playback.
#
# Loads pre-generated MP3 files from assets/audio/voice/ and plays them on a
# dedicated mixer channel so they never conflict with music or SFX channels.
#
# Completely graceful when files are absent — the game runs silently if no
# voice files have been generated yet.
#
# Usage (inside a prologue scene):
#   from systems.voice_player import VoicePlayer
#   self._voice = VoicePlayer()
#
#   # On beat load:
#   self._voice.play("marked", beat_index)
#
#   # On advance / skip:
#   self._voice.stop()
# =============================================================================

import os
import pygame

# Reserved mixer channel index — kept well above SFX channels (0–5).
_VOICE_CHANNEL = 7

# Path root relative to the repo (not the script location)
_VOICE_DIR = os.path.join(
    os.path.dirname(__file__), "..", "assets", "audio", "voice"
)


class VoicePlayer:
    def __init__(self):
        # Channel initialises lazily so construction never throws even if
        # pygame.mixer isn't ready yet.
        self._channel: pygame.mixer.Channel | None = None
        self._current: pygame.mixer.Sound | None   = None
        # Simple LRU-style cache so re-visiting a beat doesn't re-load disk.
        self._cache: dict[str, pygame.mixer.Sound]  = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def play(self, faction: str, beat_index: int) -> None:
        """Play the voice line for a given faction / beat index.

        No-ops silently if the file doesn't exist or mixer isn't available.
        """
        path = os.path.normpath(
            os.path.join(_VOICE_DIR, f"{faction}_{beat_index:03d}.mp3")
        )
        if not os.path.exists(path):
            return

        try:
            ch = self._get_channel()
            if ch is None:
                return

            if path not in self._cache:
                self._cache[path] = pygame.mixer.Sound(path)

            snd = self._cache[path]
            ch.stop()
            ch.play(snd)
            self._current = snd

        except Exception:
            # Voice is always optional — swallow all errors.
            pass

    def stop(self) -> None:
        """Interrupt the currently playing voice line."""
        try:
            ch = self._get_channel()
            if ch:
                ch.stop()
        except Exception:
            pass
        self._current = None

    def is_playing(self) -> bool:
        """True while a voice line is actively playing."""
        try:
            ch = self._get_channel()
            return bool(ch and ch.get_busy())
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _get_channel(self) -> pygame.mixer.Channel | None:
        if not pygame.mixer.get_init():
            return None
        if self._channel is None:
            # Ensure the mixer has enough channels
            if pygame.mixer.get_num_channels() <= _VOICE_CHANNEL:
                pygame.mixer.set_num_channels(_VOICE_CHANNEL + 1)
            self._channel = pygame.mixer.Channel(_VOICE_CHANNEL)
        return self._channel
