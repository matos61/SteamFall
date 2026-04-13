# =============================================================================
# scenes/faction_select.py — Choose between The Marked and The Fleshforged.
#
# Controls: LEFT/RIGHT (or A/D) to switch selection, ENTER to confirm.
# =============================================================================

import pygame
from settings import *
from scenes.base_scene import BaseScene


# Lore lines shown in each panel
_MARKED_LINES = [
    "The body is a vessel.",
    "Power is earned through insight,",
    "sacrifice, and devotion.",
    "",
    "Rune casting  ·  Stealth",
    "Soul surge  ·  Arcane trials",
]

_FLESHFORGED_LINES = [
    "The soul is chemical.",
    "Power is built, not given.",
    "Control the form. Transcend.",
    "",
    "Augments  ·  Brute force",
    "Heat drive  ·  Military grade",
]


class FactionSelectScene(BaseScene):
    def __init__(self, game):
        super().__init__(game)
        self.font_title  = pygame.font.SysFont("georgia", 44, bold=True)
        self.font_name   = pygame.font.SysFont("georgia", 36, bold=True)
        self.font_body   = pygame.font.SysFont("georgia", 21)
        self.font_hint   = pygame.font.SysFont("monospace", 14)
        self.selected    = 0   # 0 = Marked, 1 = Fleshforged

    def on_enter(self, **kwargs):
        self.selected = 0

    # ------------------------------------------------------------------

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_LEFT,  pygame.K_a):
                self.selected = 0
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self.selected = 1
            elif event.key == pygame.K_RETURN:
                self._confirm()
            elif event.key == pygame.K_ESCAPE:
                self.game.change_scene(SCENE_MAIN_MENU)

    def _confirm(self):
        if self.selected == 0:
            self.game.player_faction          = FACTION_MARKED
            self.game.save_data["faction"]    = FACTION_MARKED
        else:
            self.game.player_faction          = FACTION_FLESHFORGED
            self.game.save_data["faction"]    = FACTION_FLESHFORGED
        self.game.save_to_disk()
        if self.selected == 0:
            self.game.change_scene(SCENE_MARKED_PROLOGUE)
        else:
            self.game.change_scene(SCENE_FLESHFORGED_PROLOGUE)

    # ------------------------------------------------------------------

    def update(self, dt):
        pass

    # ------------------------------------------------------------------

    def draw(self, surface):
        surface.fill((8, 4, 18))

        cx = SCREEN_WIDTH // 2

        # Header
        title = self.font_title.render("Choose Your Path", True, WHITE)
        surface.blit(title, (cx - title.get_width() // 2, 32))
        pygame.draw.line(surface, GRAY, (cx - 300, 92), (cx + 300, 92), 1)

        # Panels
        self._draw_panel(surface, 0, "THE MARKED",     MARKED_COLOR,      _MARKED_LINES,
                          x=55,  y=110, w=520, h=460)
        self._draw_panel(surface, 1, "FLESHFORGED",    FLESHFORGED_COLOR, _FLESHFORGED_LINES,
                          x=SCREEN_WIDTH - 55 - 520, y=110, w=520, h=460)

        # Divider "VS"
        vs = self.font_body.render("vs", True, (60, 60, 60))
        surface.blit(vs, (cx - vs.get_width() // 2, SCREEN_HEIGHT // 2 - 12))

        # Footer
        hint = self.font_hint.render(
            "← →  Select     ENTER  Confirm     ESC  Back", True, (55, 55, 55))
        surface.blit(hint, (cx - hint.get_width() // 2, SCREEN_HEIGHT - 36))

    # ------------------------------------------------------------------

    def _draw_panel(self, surface, index, name, color, lines, x, y, w, h):
        selected = (self.selected == index)

        # Background
        alpha = 55 if selected else 18
        bg = pygame.Surface((w, h), pygame.SRCALPHA)
        bg.fill((*color, alpha))
        surface.blit(bg, (x, y))

        # Border (thicker + brighter when selected)
        border_color = color if selected else (50, 45, 60)
        border_width = 3    if selected else 1
        pygame.draw.rect(surface, border_color, (x, y, w, h), border_width)

        cx = x + w // 2

        # Faction name
        label = self.font_name.render(name, True, color)
        surface.blit(label, (cx - label.get_width() // 2, y + 28))

        # Decorative rule
        pygame.draw.line(surface, color,
            (x + 40, y + 80), (x + w - 40, y + 80), 1)

        # Description lines
        for i, line in enumerate(lines):
            text = self.font_body.render(line, True, WHITE if selected else GRAY)
            surface.blit(text, (cx - text.get_width() // 2, y + 104 + i * 36))

        # Selected indicator
        if selected:
            sel_text = self.font_body.render("▶  SELECTED  ◀", True, color)
            surface.blit(sel_text, (cx - sel_text.get_width() // 2, y + h - 52))
