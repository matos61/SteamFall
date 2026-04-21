# =============================================================================
# entities/crawler.py — Crawler enemy type.
#
# Behaviour:
#   • Moves horizontally along the ground (or ceiling) at a constant speed.
#   • Turns around automatically when it hits a wall (vx zeroed by physics).
#   • Deals touch damage via a persistent hitbox that covers its own rect.
#   • 30 HP, 10 contact damage, dark green color.
#
# Tile char: lowercase 'c' in the level grid.
# =============================================================================

import pygame
from entities.entity import Entity
from systems.combat  import AttackHitbox
from settings        import (CRAWLER_SPEED, CRAWLER_HP, CRAWLER_DAMAGE,
                              CRAWLER_COLOR, FACTION_MARKED)


class Crawler(Entity):
    """Ground-hugging auto-patrol enemy with touch damage."""

    def __init__(self, x: float, y: float):
        super().__init__(x, y, width=32, height=22, color=CRAWLER_COLOR,
                         max_health=CRAWLER_HP)
        self.vx           = CRAWLER_SPEED   # Start moving right
        self.facing       = 1
        self.faction_drop = FACTION_MARKED  # drops SoulShard on death
        # Hitboxes list (re-created each frame to match current position)
        self.hitboxes: list[AttackHitbox] = []

    # ------------------------------------------------------------------

    def update(self, dt: int, player=None, solid_rects=None) -> None:
        super().update(dt)

        if not self.alive:
            return

        self.hitboxes.clear()

        # Move horizontally; remember the vx we *intended* to use
        intended_vx = self.vx

        from systems.physics import apply_gravity, move_and_collide
        apply_gravity(self)
        if solid_rects:
            move_and_collide(self, solid_rects)

        # Wall detection: physics zeroed out vx → flip direction
        if self.vx == 0 and intended_vx != 0:
            self.facing = -self.facing
            self.vx     = self.facing * CRAWLER_SPEED

        # Ensure speed is maintained (friction doesn't apply — crawlers grip)
        if self.vx != 0:
            self.vx = self.facing * CRAWLER_SPEED

        # Persistent touch-damage hitbox covering the entity rect
        self.hitboxes.append(
            AttackHitbox(self.rect.copy(), damage=CRAWLER_DAMAGE,
                         owner=self, knockback_x=4.0, knockback_y=-2.5,
                         duration=1))

    # ------------------------------------------------------------------

    def get_drop_fragments(self) -> list:
        """Called by gameplay once when the crawler dies; returns typed drop.

        Crawlers are Marked-flavored so they drop a SoulShard.
        """
        from systems.collectible import SoulShard
        return [SoulShard(self.rect.centerx, self.rect.centery)]

    # ------------------------------------------------------------------

    def draw(self, surface: pygame.Surface, camera) -> None:
        super().draw(surface, camera)

        # Draw simple "legs" (two small rects below body) for flavour
        sr = camera.apply(self)
        leg_w, leg_h = 5, 7
        for offset in (4, sr.width - 10):
            pygame.draw.rect(surface, (20, 80, 50),
                             (sr.x + offset, sr.bottom, leg_w, leg_h))
