# =============================================================================
# entities/boss.py — Three-phase boss enemy.
#
# The Warden is a large boss (52×72 px) with three escalating phases:
#   Phase 1 (100–51% HP): standard chase + melee
#   Phase 2 (50–26% HP):  faster chase, shorter attack cooldown, wider range;
#                          one-shot rage flash on entry
#   Phase 3 (25–0% HP):   adds a homing projectile volley every 180 frames
# =============================================================================

import pygame
from entities.enemy    import Enemy, _PATROL, _CHASE, _ATTACK
from systems.combat    import AttackHitbox
from core.hitstop      import hitstop
from settings import (
    BOSS_MAX_HEALTH, BOSS_PHASE2_THRESH, BOSS_PHASE3_THRESH,
    BOSS_ATTACK_DAMAGE, BOSS_PROJ_RANGE,
    ENEMY_SIGHT_RANGE, ENEMY_IFRAMES,
)


class _Projectile:
    """Simple linear projectile with mild gravity and range limit."""

    def __init__(self, x: float, y: float,
                 vx: float, vy: float, damage: int):
        self.rect   = pygame.Rect(int(x) - 6, int(y) - 6, 12, 12)
        self.vx     = vx
        self.vy     = vy
        self.damage = damage
        self.alive  = True
        self._dist  = 0.0

    def update(self, solid_rects: list) -> None:
        self.rect.x += int(self.vx)
        self.rect.y += int(self.vy)
        self.vy     += 0.12   # mild gravity
        self._dist  += abs(self.vx) + abs(self.vy)
        if self._dist > BOSS_PROJ_RANGE:
            self.alive = False
            return
        for tile in solid_rects:
            if self.rect.colliderect(tile):
                self.alive = False
                return

    def draw(self, surface: pygame.Surface, camera) -> None:
        sr = camera.apply_rect(self.rect)
        if sr.right < 0 or sr.left > surface.get_width():
            return
        pygame.draw.ellipse(surface, (200, 40, 200), sr)
        pygame.draw.ellipse(surface, (255, 120, 255), sr, 2)


class Boss(Enemy):
    """Large boss enemy with phased AI and projectile attacks."""

    def __init__(self, x: float, y: float, name: str = "??"):
        super().__init__(x, y, patrol_range=0, color=(80, 20, 120))
        self.max_health      = BOSS_MAX_HEALTH
        self.health          = BOSS_MAX_HEALTH
        self.rect.width      = 52
        self.rect.height     = 72
        self.name            = name
        self._hit_iframes    = ENEMY_IFRAMES

        self._phase2_entered   = False
        self._rage_flash_timer = 0
        self._proj_cooldown    = 120   # Start at half cooldown so phase 3 isn't instant
        self._projectiles: list[_Projectile] = []

    # ------------------------------------------------------------------

    @property
    def phase(self) -> int:
        frac = self.health / self.max_health
        if frac <= BOSS_PHASE3_THRESH:
            return 3
        if frac <= BOSS_PHASE2_THRESH:
            return 2
        return 1

    def _on_phase2_enter(self) -> None:
        self._phase2_entered   = True
        self._rage_flash_timer = 30
        hitstop.trigger(12)

    # ------------------------------------------------------------------

    def _update_ai(self, player) -> None:
        hp_frac = self.health / self.max_health

        if not self._phase2_entered and hp_frac <= BOSS_PHASE2_THRESH:
            self._on_phase2_enter()

        # Phase-scaled parameters
        if self.phase >= 2:
            chase_speed  = 4.0
            atk_range    = 60
            atk_cooldown = 35
        else:
            chase_speed  = 2.5
            atk_range    = 40
            atk_cooldown = 60

        dist_x = abs(player.rect.centerx - self.rect.centerx)
        dist_y = abs(player.rect.centery - self.rect.centery)

        if dist_x <= atk_range and dist_y < 100:
            self._state = _ATTACK
        elif dist_x <= ENEMY_SIGHT_RANGE * 2.5:
            self._state = _CHASE
        else:
            self._state = _PATROL

        if self._state == _PATROL:
            self._do_patrol()
        elif self._state == _CHASE:
            direction   = 1 if player.rect.centerx > self.rect.centerx else -1
            self.vx     = direction * chase_speed
            self.facing = direction
        elif self._state == _ATTACK:
            self.vx = 0
            if self._attack_cooldown <= 0:
                self._attack_cooldown = atk_cooldown
                direction   = 1 if player.rect.centerx > self.rect.centerx else -1
                self.facing = direction
                hx = (self.rect.right if direction == 1
                      else self.rect.left - atk_range)
                self.hitboxes.append(
                    AttackHitbox(
                        pygame.Rect(hx, self.rect.top + 8,
                                    atk_range, self.rect.height - 16),
                        damage=BOSS_ATTACK_DAMAGE,
                        owner=self,
                        knockback_x=5.0,
                        knockback_y=-4.0,
                        duration=10,
                    )
                )

        # Phase 3: fire projectiles
        if self.phase == 3:
            if self._proj_cooldown <= 0:
                self._fire_projectile(player)
                self._proj_cooldown = 180
            else:
                self._proj_cooldown -= 1

    def _fire_projectile(self, player) -> None:
        cx, cy   = self.rect.center
        pcx, pcy = player.rect.center
        vx       = 6.0 * self.facing
        dist_x   = abs(pcx - cx)
        frames   = max(1, dist_x / max(1, abs(vx)))
        vy       = max(-4.0, min(4.0, (pcy - cy) / frames))
        self._projectiles.append(
            _Projectile(cx, cy, vx, vy, int(BOSS_ATTACK_DAMAGE * 0.8))
        )

    # ------------------------------------------------------------------

    def update(self, dt: int, player=None, solid_rects=None) -> None:
        super().update(dt, player=player, solid_rects=solid_rects)
        sr = solid_rects or []
        for proj in self._projectiles:
            proj.update(sr)
        self._projectiles = [p for p in self._projectiles if p.alive]
        if self._rage_flash_timer > 0:
            self._rage_flash_timer -= 1

    def get_projectiles(self) -> list:
        return self._projectiles

    # ------------------------------------------------------------------

    def draw(self, surface: pygame.Surface, camera) -> None:
        super().draw(surface, camera)

        if self._rage_flash_timer > 0:
            sr    = camera.apply(self)
            alpha = int(120 * self._rage_flash_timer / 30)
            tint  = pygame.Surface((sr.width, sr.height), pygame.SRCALPHA)
            tint.fill((220, 30, 30, alpha))
            surface.blit(tint, sr.topleft)

        for proj in self._projectiles:
            proj.draw(surface, camera)
