# =============================================================================
# systems/animation.py — Simple sprite animation state machine.
#
# States: idle, walk, jump, fall, attack, hurt, death
# Each state owns a list of pygame.Surface frames.
#
# Frame loading (P4-6):
#   If a sprite_dir is passed to AnimationController and
#   `{sprite_dir}/{state}/` exists with PNG files, they are loaded and
#   scaled to (width, height).  When the directory is absent, or loading
#   fails, the controller falls back to brightness-varying colored rects
#   so the game always renders without any art assets.
#
# AnimationController.update() advances the frame ticker.
# AnimationController.set_state() only resets the counter when the state
# actually changes, so animations are not interrupted unnecessarily.
# =============================================================================

import os
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

# Frame counts per state (placeholder fallback)
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
                 width: int, height: int,
                 sprite_dir: str | None = None) -> list:
    """
    Build animation frames for *state*.

    When *sprite_dir* is provided and `{sprite_dir}/{state}/` contains PNG
    files, those are loaded and scaled to (width, height).  Otherwise returns
    placeholder colored-rect surfaces.
    """
    # --- Attempt PNG load when sprite directory is provided ---
    if sprite_dir:
        state_path = os.path.join(sprite_dir, state)
        if os.path.isdir(state_path):
            png_files = sorted(
                f for f in os.listdir(state_path) if f.lower().endswith(".png"))
            if png_files:
                loaded = []
                for fname in png_files:
                    try:
                        img = pygame.image.load(
                            os.path.join(state_path, fname)).convert_alpha()
                        img = pygame.transform.scale(img, (width, height))
                        loaded.append(img)
                    except (pygame.error, FileNotFoundError):
                        pass
                if loaded:
                    return loaded

    # --- Fallback: placeholder colored-rect frames ---
    count  = _STATE_FRAMES[state]
    frames = []
    r, g, b = base_color
    for i in range(count):
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
    base_color  : tuple       RGB color used for placeholder frames.
    width, height : int       Entity dimensions.
    sprite_dir  : str | None  Optional path to `assets/sprites/<entity>/`.
                              When the per-state subdirectory contains PNGs
                              they are loaded; otherwise falls back to colored
                              rects (P4-6).
    """

    VALID_STATES = ("idle", "walk", "jump", "fall", "attack", "hurt", "death")

    def __init__(self, base_color: tuple, width: int, height: int,
                 sprite_dir: str | None = None):
        self._color     = base_color
        self._width     = width
        self._height    = height
        self._sprite_dir = sprite_dir

        # Build frame lists for every state
        self._frames: dict[str, list[pygame.Surface]] = {}
        for state in self.VALID_STATES:
            self._frames[state] = _make_frames(
                base_color, state, width, height, sprite_dir)

        self.state         = "idle"
        self._frame_idx    = 0
        self._tick         = 0

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
