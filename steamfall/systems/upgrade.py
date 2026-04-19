# =============================================================================
# systems/upgrade.py — Boss-kill upgrade selection menu.
#
# After defeating a boss the player chooses one of three permanent stat
# upgrades.  The choice is stored in save_data["upgrades"] and applied to
# the player object immediately; it also persists via save_to_disk().
# =============================================================================

import pygame
from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    WHITE, GRAY, GOLD, BLACK,
    MARKED_COLOR, FLESHFORGED_COLOR, FACTION_MARKED,
    UPGRADE_ATTACK_BONUS, UPGRADE_HEALTH_BONUS, UPGRADE_SPEED_BONUS,
)

UPGRADES = [
    {
        "key":  "attack",
        "name": "Resonant Blade",
        "desc": f"+{UPGRADE_ATTACK_BONUS} Attack Damage — sharpen the edge",
    },
    {
        "key":  "health",
        "name": "Iron Marrow",
        "desc": f"+{UPGRADE_HEALTH_BONUS} Max Health — fortify the vessel",
    },
    {
        "key":  "speed",
        "name": "Wraith Step",
        "desc": f"+{int(UPGRADE_SPEED_BONUS * 100)}% Move Speed — blur the boundary",
    },
]


class UpgradeMenu:
    """Navigable overlay shown after a boss kill."""

    def __init__(self):
        self._sel        = 0
        self._font_title = pygame.font.SysFont("georgia", 42, bold=True)
        self._font_item  = pygame.font.SysFont("georgia", 30)
        self._font_desc  = pygame.font.SysFont("georgia", 18)
        self._font_hint  = pygame.font.SysFont("monospace", 14)

    # ------------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event):
        """Return the chosen upgrade dict on ENTER, otherwise None."""
        if event.type != pygame.KEYDOWN:
            return None
        if event.key in (pygame.K_UP, pygame.K_w):
            self._sel = (self._sel - 1) % len(UPGRADES)
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self._sel = (self._sel + 1) % len(UPGRADES)
        elif event.key == pygame.K_RETURN:
            return UPGRADES[self._sel]
        return None

    # ------------------------------------------------------------------

    def draw(self, surface: pygame.Surface, faction: str) -> None:
        faction_color = MARKED_COLOR if faction == FACTION_MARKED else FLESHFORGED_COLOR

        # Dark full-screen tint
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        cx      = SCREEN_WIDTH  // 2
        panel_w = 580
        panel_h = 350
        panel_x = cx - panel_w // 2
        panel_y = SCREEN_HEIGHT // 2 - panel_h // 2

        # Panel background
        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((14, 10, 28, 220))
        surface.blit(panel, (panel_x, panel_y))
        pygame.draw.rect(surface, faction_color,
                         (panel_x, panel_y, panel_w, panel_h), 2)

        # Title
        title = self._font_title.render("CHOOSE AN UPGRADE", True, faction_color)
        surface.blit(title, (cx - title.get_width() // 2, panel_y + 18))

        pygame.draw.line(surface, faction_color,
                         (panel_x + 24, panel_y + 70),
                         (panel_x + panel_w - 24, panel_y + 70), 1)

        # Option rows
        for i, upg in enumerate(UPGRADES):
            row_y  = panel_y + 88 + i * 76
            is_sel = (i == self._sel)

            if is_sel:
                hl = pygame.Surface((panel_w - 40, 66), pygame.SRCALPHA)
                hl.fill((*faction_color, 40))
                surface.blit(hl, (panel_x + 20, row_y - 6))
                pygame.draw.rect(surface, faction_color,
                                 (panel_x + 20, row_y - 6, panel_w - 40, 66), 1)

            name_col = WHITE if is_sel else GRAY
            desc_col = (180, 175, 200) if is_sel else (80, 78, 100)
            surface.blit(self._font_item.render(upg["name"], True, name_col),
                         (panel_x + 50, row_y))
            surface.blit(self._font_desc.render(upg["desc"], True, desc_col),
                         (panel_x + 50, row_y + 33))

            if is_sel:
                mx, my = panel_x + 32, row_y + 16
                pygame.draw.polygon(surface, GOLD, [
                    (mx,      my - 8),
                    (mx + 8,  my),
                    (mx,      my + 8),
                    (mx - 8,  my),
                ])

        # Hint
        hint = self._font_hint.render(
            "↑↓ Select     ENTER Confirm", True, (60, 60, 60))
        surface.blit(hint, (cx - hint.get_width() // 2,
                             panel_y + panel_h - 26))
