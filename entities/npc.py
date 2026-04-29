# =============================================================================
# entities/npc.py — Non-player characters the player can talk to.
#
# NPCs cannot take damage.  When the player is within NPC_INTERACT_DIST pixels,
# a small "E" hint renders above them.  Pressing E opens their dialogue.
# =============================================================================

import pygame
from settings import NPC_WIDTH, NPC_HEIGHT, NPC_COLOR, WHITE


class NPC:
    def __init__(self, x: float, y: float,
                 name: str = "???",
                 lines: list | None = None):
        self.name  = name
        self.lines = lines or []   # list of (speaker, text) tuples

        # Rect with feet at y
        self.rect = pygame.Rect(
            int(x) - NPC_WIDTH // 2,
            int(y) - NPC_HEIGHT,
            NPC_WIDTH,
            NPC_HEIGHT,
        )

        self._show_hint  = False
        self._hint_alpha = 0                # 0–255; ramped in draw() for smooth fade-in
        self._hint_font  = pygame.font.SysFont("monospace", 14, bold=True)

    # ------------------------------------------------------------------

    def draw(self, surface: pygame.Surface, camera) -> None:
        screen_rect = camera.apply_rect(self.rect)

        if (screen_rect.right < 0 or screen_rect.left > surface.get_width()
                or screen_rect.bottom < 0 or screen_rect.top > surface.get_height()):
            return

        pygame.draw.rect(surface, NPC_COLOR, screen_rect)

        # Ramp _hint_alpha toward 255 when in range, toward 0 when out of range.
        # Delta of 25/frame gives a ~10-frame fade-in / fade-out (HK-P4-D).
        if self._show_hint:
            self._hint_alpha = min(255, self._hint_alpha + 25)
        else:
            self._hint_alpha = max(0, self._hint_alpha - 25)

        if self._hint_alpha > 0:
            label = self._hint_font.render("E", True, WHITE)
            hint_surf = pygame.Surface(label.get_size(), pygame.SRCALPHA)
            hint_surf.blit(label, (0, 0))
            hint_surf.set_alpha(self._hint_alpha)
            lx = screen_rect.centerx - label.get_width() // 2
            ly = screen_rect.top - label.get_height() - 6
            surface.blit(hint_surf, (lx, ly))
