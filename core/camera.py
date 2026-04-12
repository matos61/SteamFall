# =============================================================================
# core/camera.py — Scrolling camera that smoothly follows the player.
#
# How it works:
#   The camera stores an (offset_x, offset_y) that represents how far the
#   "window" into the world has scrolled.  When drawing, subtract the offset
#   from every world-space position so entities appear relative to the screen.
# =============================================================================

import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT


class Camera:
    def __init__(self, world_width: int, world_height: int):
        self.offset      = pygame.math.Vector2(0, 0)
        self.world_w     = world_width
        self.world_h     = world_height
        self.lerp_speed  = 0.12   # 0 = frozen, 1 = instant snap to target

    # ------------------------------------------------------------------
    # Call once per frame, passing the player (or any target with .rect)
    # ------------------------------------------------------------------
    def follow(self, target) -> None:
        # Where we *want* the camera to be (target centered on screen)
        target_x = target.rect.centerx - SCREEN_WIDTH  // 2
        target_y = target.rect.centery - SCREEN_HEIGHT // 2

        # Lerp smoothly toward the target position
        self.offset.x += (target_x - self.offset.x) * self.lerp_speed
        self.offset.y += (target_y - self.offset.y) * self.lerp_speed

        # Don't scroll past world edges
        self.offset.x = max(0, min(self.offset.x, self.world_w - SCREEN_WIDTH))
        self.offset.y = max(0, min(self.offset.y, self.world_h - SCREEN_HEIGHT))

    # ------------------------------------------------------------------
    # Use these when you want to blit something at its world position
    # ------------------------------------------------------------------
    def apply(self, entity) -> pygame.Rect:
        """Return entity.rect shifted into screen space."""
        return entity.rect.move(-int(self.offset.x), -int(self.offset.y))

    def apply_rect(self, rect: pygame.Rect) -> pygame.Rect:
        """Apply offset to any plain Rect (e.g. a tile)."""
        return rect.move(-int(self.offset.x), -int(self.offset.y))

    def apply_point(self, x: float, y: float) -> tuple:
        """Convert a world-space point to screen-space."""
        return (x - self.offset.x, y - self.offset.y)
