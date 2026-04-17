# =============================================================================
# entities/entity.py — Base class for everything that moves in the world.
#
# Both Player and Enemy inherit from this.
# Stores position as floats (x, y) for smooth sub-pixel movement, but
# uses an integer pygame.Rect for collision so pygame math stays clean.
# =============================================================================

import pygame
from settings import PLAYER_IFRAMES, TOUCH_KNOCKBACK_VX, TOUCH_KNOCKBACK_VY


class Entity:
    def __init__(self, x: float, y: float, width: int, height: int,
                 color: tuple, max_health: int = 100):
        # Position (float for smooth movement)
        self.x  = float(x)
        self.y  = float(y)

        # Velocity
        self.vx = 0.0
        self.vy = 0.0

        # Collision rectangle (integer-snapped from x, y each frame)
        self.rect = pygame.Rect(int(x), int(y), width, height)

        # Appearance (placeholder color until real sprites are added)
        self.color = color

        # Health
        self.max_health = max_health
        self.health     = max_health
        self.alive      = True

        # Physics state
        self.on_ground   = False
        self.gravity_mult = 1.0   # Override in subclasses for faction-specific weight

        # Invincibility frames (counted down each frame)
        self.iframes       = 0
        # Override in subclasses to give enemies shorter iframes than the player
        self._hit_iframes  = PLAYER_IFRAMES

        # Which direction the entity is facing: +1 = right, -1 = left
        self.facing     = 1

    # ------------------------------------------------------------------

    def take_damage(self, amount: int, knockback_dir: int = 0) -> None:
        """Reduce health, accounting for active iframes.

        knockback_dir: +1 or -1 to apply an involuntary bounce (touch damage),
                       0 means no knockback is applied here (weapon hitboxes
                       apply their own knockback after calling this method).
        """
        if self.iframes > 0:
            return
        self.health -= amount
        self.iframes = self._hit_iframes
        if knockback_dir != 0:
            self.vx = knockback_dir * TOUCH_KNOCKBACK_VX
            self.vy = TOUCH_KNOCKBACK_VY
        if self.health <= 0:
            self.health = 0
            self.die()

    def heal(self, amount: int) -> None:
        self.health = min(self.health + amount, self.max_health)

    def die(self) -> None:
        self.alive = False

    # ------------------------------------------------------------------

    def sync_rect(self) -> None:
        """Push float position into integer rect (call after moving)."""
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)

    # ------------------------------------------------------------------

    def update(self, dt: int) -> None:
        """Override in subclasses — called once per frame."""
        if self.iframes > 0:
            self.iframes -= 1

    def draw(self, surface: pygame.Surface, camera) -> None:
        """
        Default draw: a colored rectangle.
        Replace with sprite blitting once you have art assets.
        """
        screen_rect = camera.apply(self)

        # Flash white during iframes to signal invincibility
        color = (220, 220, 220) if (self.iframes > 0 and self.iframes % 4 < 2) else self.color
        pygame.draw.rect(surface, color, screen_rect)

        # Health bar (shown when below max health)
        if self.health < self.max_health and self.max_health > 0:
            bar_w  = self.rect.width
            bar_h  = 5
            bar_x  = screen_rect.x
            bar_y  = screen_rect.y - 10
            filled = int(bar_w * self.health / self.max_health)
            pygame.draw.rect(surface, (60, 10, 10),   (bar_x, bar_y, bar_w, bar_h))
            pygame.draw.rect(surface, (200, 40, 40),  (bar_x, bar_y, filled, bar_h))
