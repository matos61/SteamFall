# =============================================================================
# entities/crawler.py — Crawler enemy type.
#
# Behaviour:
#   • Moves horizontally along the ground (or ceiling) at a constant speed.
#   • Turns around automatically when it hits a wall (vx zeroed by physics).
#   • Deals touch damage via a persistent hitbox that covers its own rect.
#   • 30 HP, 10 contact damage, dark green color.
#
# Inherits from Enemy so it participates in the animation state machine
# (P4-6 / P5-1) and faction-tint blending (P3-2).  _update_ai() is
# overridden to a no-op because the Crawler's movement logic lives directly
# in update() rather than in the three-state patrol/chase/attack AI.
#
# Tile char: lowercase 'c' in the level grid.
# =============================================================================

import pygame
from entities.enemy  import Enemy
from systems.combat  import AttackHitbox
from settings        import (CRAWLER_SPEED, CRAWLER_HP, CRAWLER_DAMAGE,
                              CRAWLER_COLOR, FACTION_MARKED)


class Crawler(Enemy):
    """Ground-hugging auto-patrol enemy with touch damage."""

    def __init__(self, x: float, y: float):
        super().__init__(x, y, patrol_range=0, color=CRAWLER_COLOR)
        # Override dimensions and stats after Enemy.__init__ sets its defaults
        self.rect.width   = 32
        self.rect.height  = 22
        self.max_health   = CRAWLER_HP
        self.health       = CRAWLER_HP
        self.vx           = CRAWLER_SPEED   # Start moving right
        self.facing       = 1
        self.faction_drop = FACTION_MARKED  # drops SoulShard on death

    # ------------------------------------------------------------------

    def _update_ai(self, player) -> None:
        """Crawler does not use the three-state patrol/chase/attack AI."""
        pass

    # ------------------------------------------------------------------

    def update(self, dt: int, player=None, solid_rects=None) -> None:
        # Remember intended direction BEFORE physics may zero out vx on wall impact
        intended_vx = self.vx

        # Enemy.update() handles: Entity.update (iframes), hitbox clear,
        # physics (gravity + collide), and animation state machine.
        super().update(dt, player, solid_rects)

        if not self.alive:
            return

        # Wall detection: physics zeroed out vx → flip direction
        if self.vx == 0 and intended_vx != 0:
            self.facing = -self.facing
            self.vx     = self.facing * CRAWLER_SPEED

        # Ensure speed is maintained (friction doesn't apply — crawlers grip)
        if self.vx != 0:
            self.vx = self.facing * CRAWLER_SPEED

        # Persistent touch-damage hitbox covering the entity rect
        # (Enemy.update cleared hitboxes; re-add here after movement is resolved)
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
        # Enemy.draw() handles animation frames and faction-tint blending (BUG-051)
        super().draw(surface, camera)

        # Draw simple "legs" (two small rects below body) for flavour
        sr = camera.apply(self)
        leg_w, leg_h = 5, 7
        for offset in (4, sr.width - 10):
            pygame.draw.rect(surface, (20, 80, 50),
                             (sr.x + offset, sr.bottom, leg_w, leg_h))
