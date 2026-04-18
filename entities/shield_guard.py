"""Shield Guard — a heavily armoured enemy that blocks attacks from the front.

Hits from the player's facing direction deal only SHIELD_GUARD_DEFENSE fraction
of normal damage.  Hits from behind deal full damage.  Moves slowly but hits hard.
"""

import pygame
from entities.enemy import Enemy
from settings import (SHIELD_GUARD_HP, SHIELD_GUARD_SPEED, SHIELD_GUARD_DAMAGE,
                      SHIELD_GUARD_DEFENSE, SHIELD_GUARD_COLOR,
                      SHIELD_GUARD_KNOCKBACK_Y,
                      ENEMY_ATTACK_RANGE, ENEMY_SIGHT_RANGE, ENEMY_IFRAMES)

_PATROL = "patrol"
_CHASE  = "chase"
_ATTACK = "attack"


class ShieldGuard(Enemy):
    def __init__(self, x: float, y: float, patrol_range: int = 120):
        super().__init__(x, y, patrol_range=patrol_range, color=SHIELD_GUARD_COLOR)
        self.max_health      = SHIELD_GUARD_HP
        self.health          = SHIELD_GUARD_HP
        self.rect.width      = 38
        self.rect.height     = 58
        self._iframes_on_hit = ENEMY_IFRAMES

    # ------------------------------------------------------------------

    def take_damage(self, amount: int, knockback_dir: int = 0) -> None:
        """Reduce damage when hit from the front (shield side = facing direction)."""
        if knockback_dir != 0:
            # knockback_dir points away from attacker; if it matches our facing,
            # the blow came from the front → partial block.
            if knockback_dir == -self.facing:
                amount = max(1, int(amount * SHIELD_GUARD_DEFENSE))
        super().take_damage(amount, knockback_dir)

    # ------------------------------------------------------------------

    def _update_ai(self, player) -> None:
        # Run base AI first so _state is resolved correctly this frame
        super()._update_ai(player)
        # Only turn toward the player while actively chasing or attacking;
        # during patrol the guard faces its patrol direction naturally.
        if self._state in (_CHASE, _ATTACK):
            self.facing = 1 if player.rect.centerx > self.rect.centerx else -1

    def _do_patrol(self) -> None:
        self.vx     = self._patrol_dir * SHIELD_GUARD_SPEED
        self.facing = self._patrol_dir          # BUG-016: sync facing to patrol direction
        if self.rect.right >= self.right_limit:
            self._patrol_dir = -1
        elif self.rect.left <= self.left_limit:
            self._patrol_dir = 1

    def _do_chase(self, player) -> None:
        direction = 1 if player.rect.centerx > self.rect.centerx else -1
        self.vx = direction * SHIELD_GUARD_SPEED

    def _do_attack(self, player) -> None:
        self.vx = 0
        if self._attack_cooldown > 0:
            return
        self._attack_cooldown = 75
        direction = 1 if player.rect.centerx > self.rect.centerx else -1
        hx = (self.rect.right if direction == 1 else self.rect.left - ENEMY_ATTACK_RANGE)
        hrect = pygame.Rect(hx, self.rect.top + 10,
                            ENEMY_ATTACK_RANGE, self.rect.height - 20)
        from systems.combat import AttackHitbox
        self.hitboxes.append(
            AttackHitbox(hrect, damage=SHIELD_GUARD_DAMAGE, owner=self,
                         knockback_x=4.5, knockback_y=SHIELD_GUARD_KNOCKBACK_Y,
                         duration=10))

    # ------------------------------------------------------------------

    def draw(self, surface: pygame.Surface, camera) -> None:
        super().draw(surface, camera)
        # Draw a small shield indicator on the front face
        sr = camera.apply(self)
        shield_x = sr.right - 4 if self.facing == 1 else sr.left
        shield_rect = pygame.Rect(shield_x, sr.top + sr.height // 4, 4, sr.height // 2)
        pygame.draw.rect(surface, (180, 200, 230), shield_rect)
