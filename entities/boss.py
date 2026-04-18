# =============================================================================
# entities/boss.py — Multi-phase boss: The Warden.
#
# Phases:
#   1  (100%–51% HP): standard chase + melee attack.
#   2  (50%–26% HP):  faster chase, shorter attack cooldown, longer melee
#                     range, plus a horizontal dash charge attack.
#                     Triggers 12-frame hitstop + 45-frame rage flash on entry.
#   3  (25%–0% HP):   phase 2 moves plus a 3-way projectile spread every 160
#                     frames, plus arena-shrink signal to gameplay.py.
#                     Triggers 20-frame hitstop + 60-frame rage flash on entry.
#
# announce_phase — read and cleared by gameplay.py to show the phase banner
#                  and start the arena-shrink effect.
#
# Tile char: 'B' in the level grid.
# =============================================================================

import pygame
from entities.enemy  import Enemy
from systems.combat  import AttackHitbox
from core.hitstop    import hitstop
from settings        import (BOSS_MAX_HEALTH, BOSS_PHASE2_THRESH,
                              BOSS_PHASE3_THRESH, ENEMY_ATTACK_DAMAGE,
                              ENEMY_ATTACK_RANGE,
                              BOSS_DASH_SPEED, BOSS_DASH_FRAMES,
                              BOSS_DASH_COOLDOWN, BOSS_PROJ_SPREAD_VY)

_MAX_RAGE_FLASH = 60   # Normalise alpha against this cap


class Boss(Enemy):
    def __init__(self, x: float, y: float, name: str = "??"):
        super().__init__(x, y, patrol_range=0, color=(80, 20, 120))
        self.rect       = pygame.Rect(int(x), int(y), 52, 72)
        self.max_health = BOSS_MAX_HEALTH
        self.health     = BOSS_MAX_HEALTH
        self.name       = name

        # Phase tracking
        self._phase2_entered   = False
        self._phase3_entered   = False
        self._rage_flash_timer = 0

        # --- Scripted intro cutscene (P2-3a) ---
        self._intro_done      = False
        self._intro_timer     = 0
        self._intro_lines     = [
            "You carry the stench of the unfinished rite.",
            "The Sanctum does not open for the half-made.",
            "Kneel, or be unmade entirely.",
        ]
        self._intro_line_idx   = 0
        self._intro_line_timer = 0

        # Projectiles (phase 3): each entry is [pygame.Rect, vx, vy]
        self._proj_cooldown    = 0
        self._projectiles: list = []

        # Dash attack (phase 2+)
        self._dash_cooldown    = 60   # short initial delay so dash isn't instant
        self._dashing          = False
        self._dash_timer       = 0
        self._dash_dir         = 1

        # Signal consumed by gameplay.py to show phase banner / start shrink
        self.announce_phase    = 0

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
        if self._rage_flash_timer > 0:
            self._rage_flash_timer -= 1

        # Phase transitions (each fires exactly once)
        if not self._phase2_entered and self.phase >= 2:
            self._on_phase2_enter()
        if not self._phase3_entered and self.phase >= 3:
            self._on_phase3_enter()

        # Cooldown ticks
        self._proj_cooldown = max(0, self._proj_cooldown - 1)
        if self._dash_cooldown > 0:
            self._dash_cooldown -= 1

        super().update(dt, player=player, solid_rects=solid_rects)
        self._tick_projectiles(solid_rects or [], player=player)

    # ------------------------------------------------------------------

    def _on_phase2_enter(self) -> None:
        self._phase2_entered   = True
        self._rage_flash_timer = 45
        self.announce_phase    = 2
        hitstop.trigger(12)

    def _on_phase3_enter(self) -> None:
        self._phase3_entered   = True
        self._rage_flash_timer = 60
        self.announce_phase    = 3
        hitstop.trigger(20)

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

        # Phase 2+: active dash overrides everything else
        if self._dashing:
            self._tick_dash()
            return

        # State selection
        if dist_x <= attack_range and in_vert:
            self._state = "attack"
        elif dist_x <= 480 and in_vert:
            self._state = "chase"
        else:
            self._state = "patrol"

        if self._state == "patrol":
            self.vx = 0

        elif self._state == "chase":
            direction   = 1 if player.rect.centerx > self.rect.centerx else -1
            self.vx     = direction * chase_speed
            self.facing = direction
            # Phase 2+: trigger dash when ready
            if self.phase >= 2 and self._dash_cooldown == 0:
                self._start_dash(direction)

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

        # Phase 3: 3-way projectile spread on separate cooldown
        if self.phase == 3 and self._proj_cooldown == 0:
            self._proj_cooldown = 160
            self._fire_spread(player)

    # ------------------------------------------------------------------
    # Dash attack helpers
    # ------------------------------------------------------------------

    def _start_dash(self, direction: int) -> None:
        self._dashing       = True
        self._dash_timer    = 0
        self._dash_dir      = direction
        self._dash_cooldown = BOSS_DASH_COOLDOWN
        # Wide hitbox that persists for the full dash duration
        hx = self.rect.centerx - 44
        self.hitboxes.append(
            AttackHitbox(
                pygame.Rect(hx, self.rect.top, 88, self.rect.height),
                damage=int(ENEMY_ATTACK_DAMAGE * 1.4),
                owner=self,
                knockback_x=7.0,
                knockback_y=-5.0,
                duration=BOSS_DASH_FRAMES))

    def _tick_dash(self) -> None:
        self.vx         = self._dash_dir * BOSS_DASH_SPEED
        self.facing     = self._dash_dir
        self._dash_timer += 1
        if self._dash_timer >= BOSS_DASH_FRAMES:
            self._dashing = False
            self.vx       = 0

    # ------------------------------------------------------------------
    # Phase 3 projectile spread
    # ------------------------------------------------------------------

    def _fire_spread(self, player) -> None:
        direction = 1 if player.rect.centerx > self.rect.centerx else -1
        # Fan: straight, up-angled, down-angled using BOSS_PROJ_SPREAD_VY
        for vy_offset in (0, -BOSS_PROJ_SPREAD_VY, BOSS_PROJ_SPREAD_VY):
            rect = pygame.Rect(
                self.rect.centerx - 6, self.rect.centery - 6, 12, 12)
            self._projectiles.append([rect, direction * 5, float(vy_offset)])

    def _tick_projectiles(self, solid_rects: list, player=None) -> None:
        alive = []
        for proj in self._projectiles:
            rect, vx, vy = proj
            rect.x += int(vx)
            rect.y += int(vy)
            if any(rect.colliderect(t) for t in solid_rects):
                continue
            if player and player.alive and rect.colliderect(player.rect):
                direction = 1 if vx > 0 else -1
                player.take_damage(int(ENEMY_ATTACK_DAMAGE * 0.8),
                                   knockback_dir=direction)
                continue
            alive.append(proj)
        self._projectiles = alive

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------

    def draw(self, surface: pygame.Surface, camera) -> None:
        super().draw(surface, camera)

        # Rage flash — phase-appropriate tint that fades over time
        if self._rage_flash_timer > 0:
            sr    = camera.apply(self)
            frac  = min(1.0, self._rage_flash_timer / _MAX_RAGE_FLASH)
            alpha = int(180 * frac)
            flash = pygame.Surface((sr.width, sr.height), pygame.SRCALPHA)
            # Phase 3 → deep red; Phase 2 → orange
            if self.phase >= 3:
                flash_color = (200, 0, 0, alpha)
            else:
                flash_color = (220, 100, 0, alpha)
            flash.fill(flash_color)
            surface.blit(flash, sr.topleft)

        # Dash speed-lines — thin horizontal lines behind the boss during dash
        if self._dashing:
            sr = camera.apply(self)
            for offset_y in (sr.height // 4, sr.height // 2, 3 * sr.height // 4):
                line_len = 40
                start_x  = sr.right if self._dash_dir == 1 else sr.left + line_len
                end_x    = start_x - line_len * self._dash_dir
                pygame.draw.line(surface, (180, 100, 220),
                                 (start_x, sr.top + offset_y),
                                 (end_x,   sr.top + offset_y), 2)

        # Projectiles
        for proj in self._projectiles:
            rect, _, _ = proj
            sr = camera.apply_rect(rect)
            pygame.draw.rect(surface, (220, 80, 20), sr)
            pygame.draw.rect(surface, (255, 200, 80), sr, 1)
