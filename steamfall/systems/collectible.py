# =============================================================================
# systems/collectible.py — Collectible soul / heat fragments.
#
# SoulFragment: a small 12×12 orb that bobs up and down.
# Spawned when an enemy dies.  Collected by walking into it — grants 15
# resource (soul or heat depending on player faction).
# =============================================================================

import math
import pygame
from settings import SOUL_FRAGMENT_COLOR, SOUL_FRAGMENT_SIZE


class SoulFragment:
    """
    A small floating collectible orb.

    Parameters
    ----------
    x, y : float  World-space centre position where the fragment spawns.
    """

    def __init__(self, x: float, y: float):
        self._origin_y = float(y)
        self._x        = float(x)
        self._y        = float(y)
        self._tick     = 0
        self.alive     = True
        s = SOUL_FRAGMENT_SIZE
        self.rect = pygame.Rect(int(x) - s // 2, int(y) - s // 2, s, s)

    # ------------------------------------------------------------------

    def update(self) -> None:
        self._tick += 1
        # Bob up and down using a sine wave (±6 pixels over ~2 seconds)
        self._y    = self._origin_y + math.sin(self._tick * 0.07) * 6
        self.rect.centery = int(self._y)
        self.rect.centerx = int(self._x)

    # ------------------------------------------------------------------

    def draw(self, surface: pygame.Surface, camera) -> None:
        sr = camera.apply_rect(self.rect)

        # Skip if off-screen
        if sr.right < 0 or sr.left > surface.get_width():
            return

        # Pulsing glow alpha
        alpha = 140 + int(math.sin(self._tick * 0.1) * 50)
        alpha = max(50, min(200, alpha))

        # Outer glow
        glow_surf = pygame.Surface((sr.width + 12, sr.height + 12),
                                   pygame.SRCALPHA)
        glow_surf.fill((*SOUL_FRAGMENT_COLOR, alpha // 3))
        surface.blit(glow_surf, (sr.x - 6, sr.y - 6))

        # Core orb circle
        center = sr.center
        radius = sr.width // 2
        pygame.draw.circle(surface, SOUL_FRAGMENT_COLOR, center, radius)
        pygame.draw.circle(surface, (255, 255, 255), center, max(1, radius - 3))
