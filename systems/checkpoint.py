# =============================================================================
# systems/checkpoint.py — Checkpoint save points.
#
# A Checkpoint is a glowing pillar in the level.  When the player walks over
# it for the first time it activates: position + health fraction are written
# into game.save_data so the player can respawn there on death.
#
# Tile char: 'C' in the level grid.
# =============================================================================

import pygame
from settings import TILE_SIZE, CHECKPOINT_COLOR, CHECKPOINT_GLOW_COLOR


class Checkpoint:
    """
    A single in-world save point.

    Parameters
    ----------
    x, y : float  World-space pixel position (top-left of the tile cell).
    level : str   Which level this checkpoint belongs to ("level_1" etc.).
    """

    WIDTH  = 12
    HEIGHT = 48

    def __init__(self, x: float, y: float, level: str = "level_1"):
        # Center the pillar horizontally in the tile cell
        cx = x + (TILE_SIZE - self.WIDTH) // 2
        cy = y + TILE_SIZE - self.HEIGHT   # Sit on the tile floor
        self.rect    = pygame.Rect(int(cx), int(cy), self.WIDTH, self.HEIGHT)
        self.active  = False
        self.level   = level
        self._glow   = 0   # Oscillating brightness offset for draw
        self._tick   = 0

    # ------------------------------------------------------------------

    def update(self, player, game, faction: str) -> None:
        """Check overlap with player; activate if not already active."""
        self._tick += 1
        self._glow  = int(abs((self._tick % 60) - 30))  # 0–30, ping-pong

        if not self.active and self.rect.colliderect(player.rect):
            self._activate(player, game)

    def _activate(self, player, game) -> None:
        self.active = True
        game.save_data["checkpoint_pos"]          = (self.rect.centerx,
                                                      self.rect.top)
        game.save_data["checkpoint_health_frac"]  = (player.health /
                                                      player.max_health)
        game.save_data["checkpoint_level"]        = self.level
        game.save_data["faction"]                 = game.player_faction
        game.save_data["respawn"]                 = False
        game.save_to_disk()
        from systems.particles import particles
        particles.emit_checkpoint(self.rect.centerx, self.rect.top)

    # ------------------------------------------------------------------

    def draw(self, surface: pygame.Surface, camera) -> None:
        sr = camera.apply_rect(self.rect)

        # Skip if off-screen
        if sr.right < 0 or sr.left > surface.get_width():
            return

        # Base pillar color
        if self.active:
            g = min(255, CHECKPOINT_GLOW_COLOR[1] + self._glow * 4)
            color = (CHECKPOINT_GLOW_COLOR[0], g, CHECKPOINT_GLOW_COLOR[2])
        else:
            color = CHECKPOINT_COLOR

        pygame.draw.rect(surface, color, sr)

        # Top gem / crystal cap
        cap_rect = pygame.Rect(sr.x - 4, sr.y - 6, self.WIDTH + 8, 10)
        gem_col  = (255, 255, 180) if self.active else (120, 115, 140)
        pygame.draw.ellipse(surface, gem_col, cap_rect)

        # Faint glow halo when active
        if self.active:
            halo = pygame.Surface((sr.width + 20, sr.height + 20), pygame.SRCALPHA)
            alpha = 30 + self._glow * 3
            halo.fill((*CHECKPOINT_GLOW_COLOR, alpha))
            surface.blit(halo, (sr.x - 10, sr.y - 10))
