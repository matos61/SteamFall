"""Ranged enemy — holds its ground and fires projectiles in line of sight.

Stays at a preferred distance from the player and shoots on cooldown.
Projectiles are stored in self.projectiles and drawn/moved each frame.
gameplay.py is responsible for checking projectile-player collisions.
"""

import pygame
from entities.enemy import Enemy
from settings import (RANGED_HP, RANGED_SPEED, RANGED_DAMAGE, RANGED_PROJ_SPEED,
                      RANGED_ATTACK_COOLDOWN, RANGED_SIGHT_RANGE, RANGED_COLOR,
                      RANGED_PREFERRED_DIST,
                      ENEMY_IFRAMES, TILE_SIZE,
                      FACTION_FLESHFORGED)

_PATROL    = "patrol"
_RETREAT   = "retreat"   # Back away to maintain preferred firing distance
_SHOOT     = "shoot"

_PREFERRED_DIST = RANGED_PREFERRED_DIST   # Pixels — ideal separation from player


class Projectile:
    """A simple axis-aligned projectile spawned by Ranged enemies."""

    def __init__(self, x: int, y: int, vx: float, damage: int, owner, vy: float = 0):
        self.rect          = pygame.Rect(x, y, 10, 8)
        self.vx            = vx
        self.vy            = vy
        self.damage        = damage
        self.owner         = owner
        self.alive         = True
        self._dist_traveled = 0
        self.max_range      = RANGED_SIGHT_RANGE * 2

    def update(self, solid_rects) -> None:
        self.rect.x += int(self.vx)
        self.vy += 0.15   # mild gravity arc
        self.rect.y += int(self.vy)
        self._dist_traveled += abs(self.vx)
        if self._dist_traveled >= self.max_range:
            self.alive = False
            return
        for r in solid_rects:
            if self.rect.colliderect(r):
                self.alive = False
                return

    def draw(self, surface: pygame.Surface, camera) -> None:
        if not self.alive:
            return
        sr = camera.apply_rect(self.rect)
        pygame.draw.rect(surface, (220, 160, 40), sr)
        pygame.draw.rect(surface, (255, 220, 80), sr, 1)


class Ranged(Enemy):
    def __init__(self, x: float, y: float, patrol_range: int = 100):
        super().__init__(x, y, patrol_range=patrol_range, color=RANGED_COLOR)
        self.max_health      = RANGED_HP
        self.health          = RANGED_HP
        self.rect.width      = 32
        self.rect.height     = 46
        self._iframes_on_hit = ENEMY_IFRAMES
        self.projectiles: list[Projectile] = []
        self.faction_drop    = FACTION_FLESHFORGED   # drops HeatCore on death

    # ------------------------------------------------------------------

    def update(self, dt: int, player=None, solid_rects=None) -> None:
        super().update(dt, player=player, solid_rects=solid_rects)
        # Move and expire projectiles
        sr = solid_rects or []
        for proj in self.projectiles:
            proj.update(sr)
        self.projectiles = [p for p in self.projectiles if p.alive]

    # ------------------------------------------------------------------

    def _update_ai(self, player) -> None:
        dist_x = abs(player.rect.centerx - self.rect.centerx)
        dist_y = abs(player.rect.centery - self.rect.centery)
        in_sight = dist_y < 80 and dist_x <= RANGED_SIGHT_RANGE

        if not in_sight:
            self._state = _PATROL
            self._do_patrol()
            return

        # Face player
        self.facing = 1 if player.rect.centerx > self.rect.centerx else -1

        if dist_x < _PREFERRED_DIST - 40:
            # Too close — retreat
            self.vx = -self.facing * RANGED_SPEED
        elif dist_x > _PREFERRED_DIST + 40:
            # Too far — close in slowly
            self.vx = self.facing * RANGED_SPEED * 0.6
        else:
            self.vx = 0

        # Shoot on cooldown
        if self._attack_cooldown <= 0:
            self._fire(player)
            self._attack_cooldown = RANGED_ATTACK_COOLDOWN

    def _fire(self, player) -> None:
        vx = RANGED_PROJ_SPEED * self.facing
        cx = self.rect.right if self.facing == 1 else self.rect.left - 10
        cy = self.rect.centery - 4
        dist_x      = abs(player.rect.centerx - self.rect.centerx)
        travel_frames = max(1, dist_x / RANGED_PROJ_SPEED)
        raw_vy      = (player.rect.centery - self.rect.centery) / travel_frames
        vy          = max(-4.0, min(4.0, raw_vy))
        self.projectiles.append(Projectile(cx, cy, vx, RANGED_DAMAGE, self, vy=vy))

    # ------------------------------------------------------------------

    def draw(self, surface: pygame.Surface, camera) -> None:
        super().draw(surface, camera)
        for proj in self.projectiles:
            proj.draw(surface, camera)
