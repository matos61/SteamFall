"""Jumper enemy — erratic, spring-loaded enemy that jumps frequently.

Chases the player by hopping toward them.  Hard to hit because it spends
most of its time airborne.  Low health, low damage — threat is the unpredictability.
"""

import pygame
from entities.enemy import Enemy
from settings import (JUMPER_HP, JUMPER_SPEED, JUMPER_DAMAGE,
                      JUMPER_JUMP_FORCE, JUMPER_JUMP_COOLDOWN,
                      JUMPER_BURST_COUNT, JUMPER_BURST_PAUSE,
                      JUMPER_KNOCKBACK_Y_GROUND, JUMPER_KNOCKBACK_Y_AERIAL,
                      JUMPER_COLOR, ENEMY_SIGHT_RANGE, ENEMY_ATTACK_RANGE,
                      ENEMY_IFRAMES)

_PATROL = "patrol"
_CHASE  = "chase"
_ATTACK = "attack"


class Jumper(Enemy):
    def __init__(self, x: float, y: float, patrol_range: int = 100):
        super().__init__(x, y, patrol_range=patrol_range, color=JUMPER_COLOR)
        self.max_health      = JUMPER_HP
        self.health          = JUMPER_HP
        self.rect.width      = 26
        self.rect.height     = 34
        self._iframes_on_hit  = ENEMY_IFRAMES
        self._jump_cooldown   = 0
        self._jump_timer      = 0   # frames since last jump (for auto-jump in patrol)
        self._burst_remaining = JUMPER_BURST_COUNT
        self._burst_pause     = 0

    # ------------------------------------------------------------------

    def _update_ai(self, player) -> None:
        dist_x = abs(player.rect.centerx - self.rect.centerx)
        dist_y = abs(player.rect.centery - self.rect.centery)
        in_range = dist_y < 120

        self._jump_cooldown = max(0, self._jump_cooldown - 1)
        self._jump_timer   += 1

        if dist_x <= ENEMY_ATTACK_RANGE and in_range:
            self._state = _ATTACK
        elif dist_x <= ENEMY_SIGHT_RANGE and in_range:
            self._state = _CHASE
        else:
            self._state = _PATROL

        if self._state == _PATROL:
            self._do_patrol_jump()
        elif self._state == _CHASE:
            self._do_chase_jump(player)
        elif self._state == _ATTACK:
            self._do_attack(player)

    # ------------------------------------------------------------------

    def _do_patrol_jump(self) -> None:
        self._jump_timer = min(self._jump_timer, JUMPER_JUMP_COOLDOWN)
        self.vx = self._patrol_dir * JUMPER_SPEED
        self.facing = self._patrol_dir
        if self.rect.right >= self.right_limit:
            self._patrol_dir = -1
        elif self.rect.left <= self.left_limit:
            self._patrol_dir = 1
        # Auto-jump periodically while patrolling
        if self.on_ground and self._jump_timer > JUMPER_JUMP_COOLDOWN:
            self.vy          = JUMPER_JUMP_FORCE
            self._jump_timer = 0

    def _do_chase_jump(self, player) -> None:
        direction = 1 if player.rect.centerx > self.rect.centerx else -1
        self.vx     = direction * JUMPER_SPEED * 1.3
        self.facing = direction
        if self._burst_pause > 0:
            self._burst_pause -= 1
            return
        if self.on_ground and self._jump_cooldown <= 0:
            self.vy             = JUMPER_JUMP_FORCE
            self._jump_cooldown = JUMPER_JUMP_COOLDOWN
            self._burst_remaining -= 1
            if self._burst_remaining <= 0:
                self._burst_remaining = JUMPER_BURST_COUNT
                self._burst_pause     = JUMPER_BURST_PAUSE

    def _do_attack(self, player) -> None:
        # Bounce away after contact attack
        if self._attack_cooldown > 0:
            return
        self._attack_cooldown = 50
        direction = 1 if player.rect.centerx > self.rect.centerx else -1
        self.facing = direction
        hx = (self.rect.right if direction == 1 else
               self.rect.left - ENEMY_ATTACK_RANGE)
        hrect = pygame.Rect(hx, self.rect.top + 4,
                            ENEMY_ATTACK_RANGE, self.rect.height - 8)
        if not self.on_ground and player.rect.centery > self.rect.centery:
            ky = JUMPER_KNOCKBACK_Y_AERIAL   # downward spike when attacking from above
        else:
            ky = JUMPER_KNOCKBACK_Y_GROUND   # upward bounce on ground-level attack
        from systems.combat import AttackHitbox
        self.hitboxes.append(
            AttackHitbox(hrect, damage=JUMPER_DAMAGE, owner=self,
                         knockback_x=4.0, knockback_y=ky, duration=6))
        # Bounce back after attack
        if self.on_ground:
            self.vy     = JUMPER_JUMP_FORCE * 0.7
            self.vx     = -direction * JUMPER_SPEED * 2

    # ------------------------------------------------------------------

    def draw(self, surface: pygame.Surface, camera) -> None:
        super().draw(surface, camera)
        # Draw compressed-spring coil indicator when crouching before jump
        if self.on_ground and self._jump_cooldown < 8:
            sr = camera.apply(self)
            coil = pygame.Rect(sr.left + 4, sr.bottom - 5, sr.width - 8, 4)
            pygame.draw.rect(surface, (120, 220, 120), coil)
