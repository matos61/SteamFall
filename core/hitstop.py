# =============================================================================
# core/hitstop.py — Hit-stop singleton.
#
# Hit-stop is the brief freeze that makes hits feel impactful (Hollow Knight).
# When triggered, all entity updates pause for a few frames while drawing
# continues normally.  A 1-frame white overlay is also shown (handled in HUD).
# =============================================================================


class HitStop:
    """
    Singleton that tracks how many freeze-frames remain.

    Usage (always use the module-level ``hitstop`` instance):
        hitstop.trigger(4)        # freeze for 4 frames
        if hitstop.is_active():   # should we skip entity updates?
    """

    def __init__(self):
        self._frames_remaining = 0
        self._flash            = False   # True only on the first frame of a hitstop

    # ------------------------------------------------------------------

    def trigger(self, frames: int = 4) -> None:
        """Start or extend a hitstop of `frames` freeze-frames."""
        self._frames_remaining = max(self._frames_remaining, frames)
        self._flash = True

    def is_active(self) -> bool:
        return self._frames_remaining > 0

    def consume_flash(self) -> bool:
        """Return True (and clear the flag) if we should draw the hit-flash."""
        if self._flash:
            self._flash = False
            return True
        return False

    def tick(self) -> None:
        """Decrement the counter once per game-loop frame."""
        if self._frames_remaining > 0:
            self._frames_remaining -= 1


# Module-level singleton — import this everywhere you need it.
hitstop = HitStop()
