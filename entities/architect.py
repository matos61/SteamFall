"""
entities/architect.py — The Architect: final boss of SteamFall (LEVEL_10).

The Architect is a four-phase boss whose combat behaviour and defeat dialogue
adapt to the player's faction (Marked or Fleshforged).  It inherits from Boss
and adds:

  Phase 1  (>75% HP)    — standard chase + melee (inherited).
  Phase 2  (75–50% HP)  — adds a teleport every ARCHITECT_TELEPORT_CD frames.
  Phase 3  (50–25% HP)  — adds a 5-projectile fan spread every ARCHITECT_FAN_CD
                          frames.
  Phase 4  (≤25% HP)    — adds Crawler minion spawns every ARCHITECT_MINION_CD
                          frames; all previous behaviours remain active.

Faction-specific intro and defeat dialogue are stored as instance attributes
so gameplay.py can drive the display without coupling to Architect internals.

Tile char: 'X' in the level grid (parsed by world/tilemap.py).
"""

import random
import pygame

from entities.boss   import Boss
from settings        import (
    ARCHITECT_MAX_HEALTH,
    ARCHITECT_PHASE2_THRESH,
    ARCHITECT_PHASE3_THRESH,
    ARCHITECT_PHASE4_THRESH,
    ARCHITECT_TELEPORT_CD,
    ARCHITECT_FAN_CD,
    ARCHITECT_MINION_CD,
    FACTION_MARKED,
    FACTION_FLESHFORGED,
    ENEMY_ATTACK_DAMAGE,
    SCREEN_WIDTH,
    TILE_SIZE,
)


class Architect(Boss):
    """Four-phase final boss whose tactics shift with each health threshold."""

    def __init__(self, x: float, y: float, faction: str = FACTION_MARKED):
        super().__init__(x, y, name="The Architect")

        # Resize the rect to Architect proportions
        self.rect       = pygame.Rect(int(x), int(y), 60, 80)
        self.max_health = ARCHITECT_MAX_HEALTH
        self.health     = ARCHITECT_MAX_HEALTH
        self.color      = (60, 0, 100)   # deep violet; changes per phase draw

        # Faction the player belongs to — drives all dialogue branching
        self.faction = faction

        # Phase-4 state
        self._phase4_entered   = False
        self._teleport_cd      = 0
        self._fan_cd           = 0
        self._minion_cd        = 0
        self._spawned_minions: list = []

        # Defeat dialogue state
        self._defeat_dialogue_active = False
        self._defeat_line_idx        = 0
        self._defeat_line_timer      = 0
        self._defeat_lines: list[str] = []

        # Faction-specific intro lines (3 lines shown before combat starts)
        if faction == FACTION_MARKED:
            self._intro_lines = [
                "The runes you carry are stolen.",
                "You were never chosen \u2014 you were carved.",
                "I will unmake what I made.",
            ]
        else:  # FLESHFORGED
            self._intro_lines = [
                "You call that augmentation?",
                "I designed those mods. I own what you are.",
                "Dismantle. Recycle. Begin again.",
            ]

    # ------------------------------------------------------------------
    # Phase property (overrides Boss.phase — 4 thresholds instead of 3)
    # ------------------------------------------------------------------

    @property
    def phase(self) -> int:  # type: ignore[override]
        frac = self.health / self.max_health
        if frac <= ARCHITECT_PHASE4_THRESH:
            return 4
        if frac <= ARCHITECT_PHASE3_THRESH:
            return 3
        if frac <= ARCHITECT_PHASE2_THRESH:
            return 2
        return 1

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, dt: int, player=None, solid_rects=None) -> None:
        # Tick phase-specific cooldowns
        if self._teleport_cd > 0:
            self._teleport_cd -= 1
        if self._fan_cd > 0:
            self._fan_cd -= 1
        if self._minion_cd > 0:
            self._minion_cd -= 1

        # Phase-4 entrance (fires exactly once)
        if not self._phase4_entered and self.phase >= 4:
            self._phase4_entered   = True
            self._rage_flash_timer = 30

        # Delegate to Boss.update which calls super chain, ticks projectiles, etc.
        super().update(dt, player=player, solid_rects=solid_rects)

    # ------------------------------------------------------------------
    # AI (overrides Boss._update_ai)
    # ------------------------------------------------------------------

    def _update_ai(self, player) -> None:
        # Always run the base chase / melee logic
        super()._update_ai(player)

        ph = self.phase

        # Phase 2+: periodic teleport
        if ph >= 2 and self._teleport_cd == 0:
            self._teleport_cd      = ARCHITECT_TELEPORT_CD
            self._rage_flash_timer = 15
            arena_min = TILE_SIZE * 4
            arena_max = SCREEN_WIDTH - TILE_SIZE * 4
            self.rect.centerx = random.randint(arena_min, arena_max)
            # Keep pixel-precise float position in sync
            self.x = float(self.rect.x)

        # Phase 3+: periodic 5-projectile fan spread
        if ph >= 3 and self._fan_cd == 0:
            self._fan_cd = ARCHITECT_FAN_CD
            self._fire_architect_fan(player)

        # Phase 4: periodic Crawler minion spawn
        if ph >= 4 and self._minion_cd == 0:
            self._minion_cd = ARCHITECT_MINION_CD
            self._spawn_minion()

    # ------------------------------------------------------------------
    # Fan spread (5 projectiles with vy offsets)
    # ------------------------------------------------------------------

    def _fire_architect_fan(self, player) -> None:
        direction = 1 if player.rect.centerx > self.rect.centerx else -1
        for vy_offset in (-6, -3, 0, 3, 6):
            rect = pygame.Rect(
                self.rect.centerx - 6, self.rect.centery - 6, 12, 12)
            self._projectiles.append([rect, direction * 5, float(vy_offset)])

    # ------------------------------------------------------------------
    # Minion spawn
    # ------------------------------------------------------------------

    def _spawn_minion(self) -> None:
        from entities.crawler import Crawler
        crawler = Crawler(self.rect.centerx, self.rect.top)
        self._spawned_minions.append(crawler)

    # ------------------------------------------------------------------
    # Die / defeat dialogue
    # ------------------------------------------------------------------

    def die(self) -> None:
        super().die()
        self._on_defeat()

    def _on_defeat(self) -> None:
        self.alive = False
        self._defeat_dialogue_active = True
        if self.faction == FACTION_MARKED:
            self._defeat_lines = [
                "The ink\u2026 it burns.",
                "You\u2026 were real after all.",
                "Go. The Sanctum is yours.",
            ]
        else:  # FLESHFORGED
            self._defeat_lines = [
                "Efficient.",
                "The design\u2026 improves.",
                "Take it. You\u2019ve earned the forge.",
            ]

    # ------------------------------------------------------------------
    # Draw — deep violet with phase-appropriate colour shift
    # ------------------------------------------------------------------

    def draw(self, surface: pygame.Surface, camera) -> None:
        # Shift body colour by phase so the visual stakes escalate
        ph = self.phase
        if ph == 1:
            self.color = (60,  0,  100)   # deep violet
        elif ph == 2:
            self.color = (100, 0,  120)   # brighter violet
        elif ph == 3:
            self.color = (140, 20, 80)    # violet-crimson
        else:
            self.color = (180, 0,  40)    # blood-red

        super().draw(surface, camera)
