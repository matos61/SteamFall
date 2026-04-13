# =============================================================================
# systems/animation.py — Simple sprite animation state machine.
#
# States: idle, walk, jump, fall, attack, hurt, death
# Each state owns a list of pygame.Surface frames (colored rects for now).
# AnimationController.update() advances the frame ticker.
# AnimationController.set_state() only resets the counter when the state
# actually changes, so animations are not interrupted unnecessarily.
# =============================================================================

import pygame


# Number of game-frames each animation frame is shown for
_STATE_FPS = {
    "idle":   8,
    "walk":   5,
    "jump":   12,
    "fall":   8,
    "attack": 3,
    "hurt":   6,
    "death":  10,
}

# Frame counts per state (all use solid colored rects with slight variation)
_STATE_FRAMES = {
    "idle":   4,
    "walk":   6,
    "jump":   3,
    "fall":   3,
    "attack": 4,
    "hurt":   3,
    "death":  5,
}


def _make_frames(base_color: tuple, state: str,
                 width: int, height: int) -> list:
    """
    Build placeholder frames as colored surfaces with slight brightness
    variation per frame so you can visually see the animation playing.
    """
    count = _STATE_FRAMES[state]
    frames = []
    r, g, b = base_color
    for i in range(count):
        # Each frame shifts brightness slightly
        delta = int((i - count // 2) * 12)
        fr    = max(0, min(255, r + delta))
        fg    = max(0, min(255, g + delta))
        fb    = max(0, min(255, b + delta))
        surf  = pygame.Surface((width, height))
        surf.fill((fr, fg, fb))
        frames.append(surf)
    return frames


class AnimationController:
    """
    Manages animation state and frame advancement for an entity.

    Parameters
    ----------
    base_color : tuple  RGB color used to tint all placeholder frames.
    width, height : int  Entity dimensions (placeholder frame size).
    """

    VALID_STATES = ("idle", "walk", "jump", "fall", "attack", "hurt", "death")

    def __init__(self, base_color: tuple, width: int, height: int):
        self._color  = base_color
        self._width  = width
        self._height = height

        # Build frame lists for every state
        self._frames: dict[str, list[pygame.Surface]] = {}
        for state in self.VALID_STATES:
            self._frames[state] = _make_frames(base_color, state, width, height)

        self.state         = "idle"
        self._frame_idx    = 0
        self._tick         = 0          # Counts up to _STATE_FPS[state]

    # ------------------------------------------------------------------

    def set_state(self, name: str) -> None:
        """Change state; only resets frame counter when state actually changes."""
        if name not in self._frames:
            return
        if name != self.state:
            self.state      = name
            self._frame_idx = 0
            self._tick      = 0

    def update(self) -> None:
        """Advance animation ticker by one game frame."""
        fps = _STATE_FPS.get(self.state, 8)
        self._tick += 1
        if self._tick >= fps:
            self._tick      = 0
            frame_count     = len(self._frames[self.state])
            self._frame_idx = (self._frame_idx + 1) % frame_count

    @property
    def current_frame(self) -> pygame.Surface:
        """Return the Surface for the current animation frame."""
        return self._frames[self.state][self._frame_idx]
