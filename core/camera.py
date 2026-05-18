# =============================================================================
# core/camera.py — Scrolling camera that smoothly follows the player.
#
# How it works:
#   The camera stores an (offset_x, offset_y) that represents how far the
#   "window" into the world has scrolled.  When drawing, subtract the offset
#   from every world-space position so entities appear relative to the screen.
# =============================================================================

import pygame
from settings import (SCREEN_WIDTH, SCREEN_HEIGHT,
                      CAMERA_DEAD_ZONE_X, CAMERA_DEAD_ZONE_Y, CAMERA_LOOK_AHEAD_X)


class Camera:
    def __init__(self, world_width: int, world_height: int):
        self.offset      = pygame.math.Vector2(0, 0)
        self.world_w     = world_width
        self.world_h     = world_height
        self.lerp_speed  = 0.15   # was 0.12 — snappier tracking during Overdrive dashes

    # ------------------------------------------------------------------
    # Call once per frame, passing the player (or any target with .rect)
    # ------------------------------------------------------------------
    def follow(self, target) -> None:
        # Look-ahead: shift target forward in the direction the player is facing
        facing   = getattr(target, 'facing', 0)
        target_x = target.rect.centerx - SCREEN_WIDTH  // 2 + facing * CAMERA_LOOK_AHEAD_X
        target_y = target.rect.centery - SCREEN_HEIGHT // 2

        # Dead zone on X: only lerp when target is outside the dead-zone band
        dx = target_x - self.offset.x
        if abs(dx) > CAMERA_DEAD_ZONE_X:
            move = dx - CAMERA_DEAD_ZONE_X * (1 if dx > 0 else -1)
            self.offset.x += move * self.lerp_speed

        # Dead zone on Y: only lerp when target is outside the dead-zone band
        dy = target_y - self.offset.y
        if abs(dy) > CAMERA_DEAD_ZONE_Y:
            move_y = dy - CAMERA_DEAD_ZONE_Y * (1 if dy > 0 else -1)
            self.offset.y += move_y * self.lerp_speed

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
