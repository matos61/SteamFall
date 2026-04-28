# =============================================================================
# systems/collectible.py — Collectible soul / heat fragments.
#
# SoulFragment: a small 12×12 orb that bobs up and down.
# Spawned when an enemy dies.  Collected by walking into it — grants 15
# resource (soul or heat depending on player faction).
#
# HeatCore:    burnt-orange diamond drop from Fleshforged enemies.
#              Heals Fleshforged players by HEAT_CORE_HEAL on pickup.
# SoulShard:   soft-purple diamond drop from Marked enemies.
#              Heals Marked players by SOUL_SHARD_HEAL on pickup.
# AbilityOrb:  gold pulsing orb that unlocks the player's special ability.
# =============================================================================

import math
import pygame
from settings import (SOUL_FRAGMENT_COLOR, SOUL_FRAGMENT_SIZE,
                      HEAT_CORE_SIZE, HEAT_CORE_HEAL, HEAT_CORE_COLOR,
                      SOUL_SHARD_SIZE, SOUL_SHARD_HEAL, SOUL_SHARD_COLOR,
                      DROP_BOB_SPEED, DROP_BOB_AMP,
                      FACTION_FLESHFORGED, FACTION_MARKED,
                      LORE_ITEM_SIZE, LORE_ITEM_COLOR)


class SoulFragment:
    """
    A small floating collectible orb.

    Parameters
    ----------
    x, y : float  World-space centre position where the fragment spawns.
    """

    def __init__(self, x: float, y: float):
        self._origin_y = float(y)
        self._x        = float(x)
        self._y        = float(y)
        self._tick     = 0
        self.alive     = True
        s = SOUL_FRAGMENT_SIZE
        self.rect = pygame.Rect(int(x) - s // 2, int(y) - s // 2, s, s)

    # ------------------------------------------------------------------

    def update(self) -> None:
        self._tick += 1
        # Bob up and down using a sine wave (±6 pixels over ~2 seconds)
        self._y    = self._origin_y + math.sin(self._tick * 0.07) * 6
        self.rect.centery = int(self._y)
        self.rect.centerx = int(self._x)

    # ------------------------------------------------------------------

    def draw(self, surface: pygame.Surface, camera) -> None:
        sr = camera.apply_rect(self.rect)

        # Skip if off-screen
        if sr.right < 0 or sr.left > surface.get_width():
            return

        # Pulsing glow alpha
        alpha = 140 + int(math.sin(self._tick * 0.1) * 50)
        alpha = max(50, min(200, alpha))

        # Outer glow
        glow_surf = pygame.Surface((sr.width + 12, sr.height + 12),
                                   pygame.SRCALPHA)
        glow_surf.fill((*SOUL_FRAGMENT_COLOR, alpha // 3))
        surface.blit(glow_surf, (sr.x - 6, sr.y - 6))

        # Core orb circle
        center = sr.center
        radius = sr.width // 2
        pygame.draw.circle(surface, SOUL_FRAGMENT_COLOR, center, radius)
        pygame.draw.circle(surface, (255, 255, 255), center, max(1, radius - 3))


# ---------------------------------------------------------------------------

def _draw_diamond(surface: pygame.Surface, color: tuple,
                  cx: int, cy: int, half: int) -> None:
    """Draw a simple 4-point diamond centred on (cx, cy) with half-extent *half*."""
    pts = [(cx, cy - half), (cx + half, cy), (cx, cy + half), (cx - half, cy)]
    pygame.draw.polygon(surface, color, pts)


class HeatCore:
    """Burnt-orange diamond collectible dropped by Fleshforged enemies.

    Heals a Fleshforged player by HEAT_CORE_HEAL HP on pickup.
    Marked players can still collect it (consuming the drop) but gain no heal.
    """

    def __init__(self, x: float, y: float):
        self._origin_y = float(y)
        self._x        = float(x)
        self._y        = float(y)
        self._bob      = 0.0
        self.alive     = True
        s = HEAT_CORE_SIZE
        self.rect = pygame.Rect(int(x) - s // 2, int(y) - s // 2, s, s)

    def update(self) -> None:
        self._bob += DROP_BOB_SPEED
        self._y = self._origin_y + math.sin(self._bob) * DROP_BOB_AMP
        self.rect.centery = int(self._y)
        self.rect.centerx = int(self._x)

    def draw(self, surface: pygame.Surface, camera) -> None:
        sr = camera.apply_rect(self.rect)
        if sr.right < 0 or sr.left > surface.get_width():
            return
        _draw_diamond(surface, HEAT_CORE_COLOR, sr.centerx, sr.centery,
                      sr.width // 2)
        # bright inner highlight
        _draw_diamond(surface, (255, 200, 100), sr.centerx, sr.centery,
                      max(1, sr.width // 4))

    def collect(self, player, game) -> None:  # noqa: ARG002
        if getattr(player, "faction", None) == FACTION_FLESHFORGED:
            player.heal(HEAT_CORE_HEAL)
        self.alive = False


# ---------------------------------------------------------------------------


class SoulShard:
    """Soft-purple diamond collectible dropped by Marked enemies.

    Heals a Marked player by SOUL_SHARD_HEAL HP on pickup.
    Fleshforged players consume the drop but gain no heal.
    """

    def __init__(self, x: float, y: float):
        self._origin_y = float(y)
        self._x        = float(x)
        self._y        = float(y)
        self._bob      = 0.0
        self.alive     = True
        s = SOUL_SHARD_SIZE
        self.rect = pygame.Rect(int(x) - s // 2, int(y) - s // 2, s, s)

    def update(self) -> None:
        self._bob += DROP_BOB_SPEED
        self._y = self._origin_y + math.sin(self._bob) * DROP_BOB_AMP
        self.rect.centery = int(self._y)
        self.rect.centerx = int(self._x)

    def draw(self, surface: pygame.Surface, camera) -> None:
        sr = camera.apply_rect(self.rect)
        if sr.right < 0 or sr.left > surface.get_width():
            return
        _draw_diamond(surface, SOUL_SHARD_COLOR, sr.centerx, sr.centery,
                      sr.width // 2)
        # bright inner highlight
        _draw_diamond(surface, (200, 160, 255), sr.centerx, sr.centery,
                      max(1, sr.width // 4))

    def collect(self, player, game) -> None:  # noqa: ARG002
        if getattr(player, "faction", None) == FACTION_MARKED:
            player.heal(SOUL_SHARD_HEAL)
        self.alive = False


# ---------------------------------------------------------------------------


class AbilityOrb:
    """Gold pulsing orb that permanently unlocks the player's special ability.

    Placed in levels via the 'A' tile character.  Collecting it increments
    player.ability_slots up to ABILITY_SLOTS_MAX and persists to save_data.
    """

    def __init__(self, x: float, y: float):
        from settings import GOLD, ABILITY_SLOTS_MAX   # late import to avoid circular
        self._GOLD             = GOLD
        self._ABILITY_SLOTS_MAX = ABILITY_SLOTS_MAX
        self._origin_y = float(y)
        self._x        = float(x)
        self._y        = float(y)
        self._glow_timer = 0
        self.alive     = True
        self.rect = pygame.Rect(int(x) - 9, int(y) - 9, 18, 18)

    def update(self) -> None:
        self._glow_timer += 1
        self._y = self._origin_y + math.sin(self._glow_timer * DROP_BOB_SPEED) * DROP_BOB_AMP
        self.rect.centery = int(self._y)
        self.rect.centerx = int(self._x)

    def draw(self, surface: pygame.Surface, camera) -> None:
        sr = camera.apply_rect(self.rect)
        if sr.right < 0 or sr.left > surface.get_width():
            return
        alpha = 140 + int(math.sin(self._glow_timer * 0.1) * 50)
        alpha = max(50, min(200, alpha))
        glow_surf = pygame.Surface((sr.width + 12, sr.height + 12), pygame.SRCALPHA)
        glow_surf.fill((*self._GOLD, alpha // 3))
        surface.blit(glow_surf, (sr.x - 6, sr.y - 6))
        _draw_diamond(surface, self._GOLD, sr.centerx, sr.centery, sr.width // 2)
        _draw_diamond(surface, (255, 255, 200), sr.centerx, sr.centery,
                      max(1, sr.width // 4))

    def collect(self, player, game) -> None:
        if not self.alive:
            return
        player.ability_slots = min(
            getattr(player, "ability_slots", 0) + 1, self._ABILITY_SLOTS_MAX)
        self.alive = False
        game.save_data["ability_slots"] = player.ability_slots
        game.save_to_disk()


# ---------------------------------------------------------------------------


class LoreItem:
    """Parchment-coloured collectible that reveals a lore text blurb on pickup.

    Parameters
    ----------
    x, y     : World-space centre position.
    lore_id  : Unique string key stored in save_data["lore_found"].
    text     : The text string displayed when collected.
    """

    def __init__(self, x: float, y: float, lore_id: str, text: str):
        self._x       = float(x)
        self._y       = float(y)
        self._lore_id = lore_id
        self._text    = text
        self._glow    = 0
        self.alive    = True
        s = LORE_ITEM_SIZE
        self.rect = pygame.Rect(int(x) - s // 2, int(y) - s // 2, s, s)

    def update(self) -> None:
        self._glow = (self._glow + 1) % 60
        # Gentle bob
        self._y_disp = self._y + math.sin(self._glow / 60 * 2 * math.pi) * 3
        self.rect.centery = int(self._y_disp)
        self.rect.centerx = int(self._x)

    def draw(self, surface: pygame.Surface, camera) -> None:
        sr = camera.apply_rect(self.rect)
        if sr.right < 0 or sr.left > surface.get_width():
            return
        brightness = int(math.sin(self._glow / 60 * 2 * math.pi) * 15)
        r = min(255, max(0, LORE_ITEM_COLOR[0] + brightness))
        g = min(255, max(0, LORE_ITEM_COLOR[1] + brightness))
        b = min(255, max(0, LORE_ITEM_COLOR[2] + brightness))
        _draw_diamond(surface, (r, g, b), sr.centerx, sr.centery, sr.width // 2)

    def collect(self, player, game) -> str | None:
        """Mark as collected, save, and return the lore text (or None if already collected)."""
        lore_found = game.save_data.setdefault("lore_found", [])
        if self._lore_id not in lore_found:
            lore_found.append(self._lore_id)
            game.save_to_disk()
            self.alive = False
            return self._text
        # Invariant: on_enter() pre-filters already-collected lore items, so this branch
        # should never be reached in normal play.
        self.alive = False
        return None
