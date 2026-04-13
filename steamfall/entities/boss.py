# =============================================================================
# entities/boss.py — Multi-phase boss enemy.
#
# Phases:
#   1  (100%–51% HP): standard chase + melee attack.
#   2  (50%–26% HP):  faster chase, shorter attack cooldown, longer melee range.
#                     Triggers 12-frame hitstop and 30-frame rage flash on entry.
#   3  (25%–0% HP):   same as phase 2 plus projectile attacks every 180 frames.
#
# Tile char: 'B' in the level grid.
# =============================================================================

import pygame
from entities.enemy  import Enemy
from systems.combat  import AttackHitbox
from core.hitstop    import hitstop
from settings        import (BOSS_MAX_HEALTH, BOSS_PHASE2_THRESH,
                              BOSS_PHASE3_THRESH, ENEMY_ATTACK_DAMAGE,
                              ENEMY_ATTACK_RANGE, HITSTOP_FRAMES)


class Boss(Enemy):
    def __init__(self, x: float, y: float, name: str = "??"):
        # Enemy init sets width=36/height=52 — override below
        super().__init__(x, y, patrol_range=0, color=(80, 20, 120))
        # Resize to boss dimensions
        self.rect       = pygame.Rect(int(x), int(y), 52, 72)
        self.max_health = BOSS_MAX_HEALTH
        self.health     = BOSS_MAX_HEALTH
        self.name       = name

        self._phase2_entered    = False
        self._rage_flash_timer  = 0
        self._proj_cooldown     = 0
        self._projectiles: list = []   # Each entry: [pygame.Rect, vx]

    # ------------------------------------------------------------------
    # Phase property
    # ------------------------------------------------------------------

    @property
    def phase(self) -> int:
        frac = self.health / self.max_health
        if frac <= BOSS_PHASE3_THRESH:
            return 3
        if frac <= BOSS_PHASE2_THRESH:
            return 2
        return 1

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, dt: int, player=None, solid_rects=None) -> None:
        # Tick rage flash before physics (so it counts down while in hitstop too)
        if self._rage_flash_timer > 0:
            self._rage_flash_timer -= 1

        # Phase 2 transition check (runs once)
        if not self._phase2_entered and self.phase >= 2:
            self._on_phase2_enter()

        # Tick projectile cooldown
        self._proj_cooldown = max(0, self._proj_cooldown - 1)

        # Base Enemy update handles iframes, AI (_update_ai), physics
        super().update(dt, player=player, solid_rects=solid_rects)

        # Move projectiles and check player collision
        self._tick_projectiles(solid_rects or [], player=player)

    # ------------------------------------------------------------------

    def _on_phase2_enter(self) -> None:
        self._phase2_entered   = True
        self._rage_flash_timer = 30
        hitstop.trigger(12)

    # ------------------------------------------------------------------
    # AI — overrides Enemy._update_ai
    # ------------------------------------------------------------------

    def _update_ai(self, player) -> None:
        dist_x = abs(player.rect.centerx - self.rect.centerx)
        dist_y = abs(player.rect.centery - self.rect.centery)
        in_vert = dist_y < 100

        # Phase-scaled stats
        if self.phase >= 2:
            chase_speed  = 4.0
            attack_cd    = 35
            attack_range = 60
        else:
            chase_speed  = 2.5
            attack_cd    = 60
            attack_range = ENEMY_ATTACK_RANGE

        # State selection
        if dist_x <= attack_range and in_vert:
            self._state = "attack"
        elif dist_x <= 480 and in_vert:
            self._state = "chase"
        else:
            self._state = "patrol"

        if self._state == "patrol":
            self.vx = 0   # Boss waits when player is far away

        elif self._state == "chase":
            direction   = 1 if player.rect.centerx > self.rect.centerx else -1
            self.vx     = direction * chase_speed
            self.facing = direction

        elif self._state == "attack":
            self.vx = 0
            if self._attack_cooldown <= 0:
                self._attack_cooldown = attack_cd
                direction = 1 if player.rect.centerx > self.rect.centerx else -1
                self.facing = direction
                hx = (self.rect.right if direction == 1
                      else self.rect.left - attack_range)
                self.hitboxes.append(
                    AttackHitbox(
                        pygame.Rect(hx, self.rect.top + 10,
                                    attack_range, self.rect.height - 20),
                        damage=ENEMY_ATTACK_DAMAGE,
                        owner=self,
                        knockback_x=5.0,
                        knockback_y=-4.0,
                        duration=10))

        # Phase 3: ranged projectile on separate cooldown
        if self.phase == 3 and self._proj_cooldown <= 0:
            self._proj_cooldown = 180
            direction = 1 if player.rect.centerx > self.rect.centerx else -1
            proj_rect = pygame.Rect(self.rect.centerx - 6,
                                    self.rect.centery - 6, 12, 12)
            self._projectiles.append([proj_rect, direction * 6])

    # ------------------------------------------------------------------

    def _tick_projectiles(self, solid_rects: list, player=None) -> None:
        alive = []
        for proj in self._projectiles:
            rect, vx = proj
            rect.x += int(vx)
            if any(rect.colliderect(t) for t in solid_rects):
                continue   # Hit a wall — destroy
            if player and player.alive and rect.colliderect(player.rect):
                direction = 1 if vx > 0 else -1
                player.take_damage(int(ENEMY_ATTACK_DAMAGE * 0.8),
                                   knockback_dir=direction)
                continue   # Hit player — destroy
            alive.append(proj)
        self._projectiles = alive

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------

    def draw(self, surface: pygame.Surface, camera) -> None:
        super().draw(surface, camera)

        # Rage flash (red tint overlay on the boss sprite)
        if self._rage_flash_timer > 0:
            sr    = camera.apply(self)
            alpha = int(180 * self._rage_flash_timer / 30)
            flash = pygame.Surface((sr.width, sr.height), pygame.SRCALPHA)
            flash.fill((220, 0, 0, alpha))
            surface.blit(flash, sr.topleft)

        # Projectiles
        for proj in self._projectiles:
            rect, _ = proj
            sr = camera.apply_rect(rect)
            pygame.draw.rect(surface, (220, 80, 20), sr)
            pygame.draw.rect(surface, (255, 200, 80), sr, 1)
