# =============================================================================
# entities/enemy.py — Basic patrol + chase enemy.
#
# Behaviour state machine:
#   PATROL → walks back and forth between left_limit and right_limit.
#   CHASE  → moves toward the player when they enter sight range.
#   ATTACK → stops and deals damage when the player is in melee range.
#
# To create a new enemy type later, subclass Enemy and override
# _update_ai() with different behaviour.
# =============================================================================

import pygame
from entities.entity   import Entity
from systems.combat    import AttackHitbox
from settings          import (ENEMY_PATROL_SPEED, ENEMY_CHASE_SPEED,
                                ENEMY_SIGHT_RANGE, ENEMY_ATTACK_RANGE,
                                ENEMY_ATTACK_DAMAGE, FLESHFORGED_COLOR, RED,
                                ENEMY_IFRAMES)

# AI states
_PATROL = "patrol"
_CHASE  = "chase"
_ATTACK = "attack"


class Enemy(Entity):
    def __init__(self, x: float, y: float,
                 patrol_range: int = 160,
                 color: tuple = (160, 45, 45)):
        super().__init__(x, y, width=36, height=52, color=color, max_health=60)

        # Patrol boundaries
        self.left_limit  = x - patrol_range
        self.right_limit = x + patrol_range

        self._state           = _PATROL
        self._patrol_dir      = 1          # +1 right, -1 left
        self._attack_cooldown = 0
        self._iframes_on_hit  = ENEMY_IFRAMES   # Shorter than player iframes → combos work

        # Hitboxes spawned this frame (cleared after checking)
        self.hitboxes: list[AttackHitbox] = []

    # ------------------------------------------------------------------

    def update(self, dt: int, player=None, solid_rects=None) -> None:
        super().update(dt)

        if not self.alive:
            return

        self._attack_cooldown = max(0, self._attack_cooldown - 1)
        self.hitboxes.clear()

        if player and player.alive:
            self._update_ai(player)

        # Import here to avoid circular imports at module load time
        from systems.physics import apply_gravity, move_and_collide
        apply_gravity(self)
        if solid_rects:
            move_and_collide(self, solid_rects)

    # ------------------------------------------------------------------

    def _update_ai(self, player) -> None:
        dist_x = abs(player.rect.centerx - self.rect.centerx)
        dist_y = abs(player.rect.centery - self.rect.centery)

        # Only react to player on roughly the same vertical level
        in_vertical_range = dist_y < 80

        if dist_x <= ENEMY_ATTACK_RANGE and in_vertical_range:
            self._state = _ATTACK
        elif dist_x <= ENEMY_SIGHT_RANGE and in_vertical_range:
            self._state = _CHASE
        else:
            self._state = _PATROL

        if self._state == _PATROL:
            self._do_patrol()
        elif self._state == _CHASE:
            self._do_chase(player)
        elif self._state == _ATTACK:
            self._do_attack(player)

    # ------------------------------------------------------------------

    def _do_patrol(self) -> None:
        self.vx = self._patrol_dir * ENEMY_PATROL_SPEED
        self.facing = self._patrol_dir

        # Reverse at patrol limits
        if self.rect.right >= self.right_limit:
            self._patrol_dir = -1
        elif self.rect.left <= self.left_limit:
            self._patrol_dir = 1

    def _do_chase(self, player) -> None:
        direction = 1 if player.rect.centerx > self.rect.centerx else -1
        self.vx     = direction * ENEMY_CHASE_SPEED
        self.facing = direction

    def _do_attack(self, player) -> None:
        self.vx = 0   # Stop while attacking

        if self._attack_cooldown > 0:
            return

        self._attack_cooldown = 60   # One attack per second

        # Build hitbox extending in the facing direction
        direction = 1 if player.rect.centerx > self.rect.centerx else -1
        self.facing = direction
        hx = (self.rect.right if direction == 1 else
              self.rect.left - ENEMY_ATTACK_RANGE)
        hitbox_rect = pygame.Rect(hx, self.rect.top + 8,
                                  ENEMY_ATTACK_RANGE, self.rect.height - 16)
        self.hitboxes.append(
            AttackHitbox(hitbox_rect, damage=ENEMY_ATTACK_DAMAGE,
                         owner=self, knockback_x=3.5, knockback_y=-2.5,
                         duration=8))

    # ------------------------------------------------------------------

    def get_drop_fragments(self) -> list:
        """Return soul fragments to spawn when this enemy dies."""
        from systems.collectible import SoulFragment
        return [SoulFragment(self.rect.centerx, self.rect.centery)]

    def draw(self, surface: pygame.Surface, camera) -> None:
        super().draw(surface, camera)
