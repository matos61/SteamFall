# =============================================================================
# scenes/main_menu.py — Title screen.
#
# Controls: UP/DOWN to move selection, ENTER to confirm.
# =============================================================================

import random
import pygame
from settings import *
from scenes.base_scene import BaseScene

# Parallax background layers — each entry is (speed_px_per_frame, color, shapes)
# Shapes are (rel_x, y, w, h) tuples pre-computed once at import time.
_RNG = random.Random(42)   # deterministic so layout is consistent across runs


def _make_layer(count: int, color: tuple) -> list:
    """Return a list of (x, y, w, h) rect dicts spread across two screen widths."""
    items = []
    for _ in range(count):
        x = _RNG.randint(0, SCREEN_WIDTH * 2)
        y = _RNG.randint(40, SCREEN_HEIGHT - 80)
        w = _RNG.randint(60, 180)
        h = _RNG.randint(6, 14)
        items.append([x, y, w, h])
    return items


_PARALLAX_LAYERS = [
    # (speed, color, shapes) — luminance raised +15 from original per HK-P4-C
    (1.5, (35, 30, 50), _make_layer(6, (35, 30, 50))),
    (2,   (43, 33, 65), _make_layer(5, (43, 33, 65))),
    (3,   (51, 35, 75), _make_layer(4, (51, 35, 75))),
]


class MainMenuScene(BaseScene):
    def __init__(self, game):
        super().__init__(game)
        self.font_title   = pygame.font.SysFont("georgia", 76, bold=True)
        self.font_sub     = pygame.font.SysFont("georgia", 26)
        self.font_menu    = pygame.font.SysFont("georgia", 34)
        self.font_credits = pygame.font.SysFont("georgia", 26)
        self.font_hint    = pygame.font.SysFont("monospace", 14)

        self.options  = ["Begin", "Quit"]   # rebuilt each on_enter
        self.selected = 0

        # Subtle breathing animation for the title — period ~90 frames (P4-5)
        self._pulse     = 0.0
        self._pulse_dir = 1

        # Credits overlay
        self._credits_open = False

    def on_enter(self, **kwargs):
        # Show "Continue" at the top if a save exists with a checkpoint
        if self.game.save_data.get("checkpoint_pos"):
            self.options = ["Continue", "New Game", "Credits", "Quit"]
        else:
            self.options = ["New Game", "Credits", "Quit"]
        self.selected = 0
        self._credits_open = False

    # ------------------------------------------------------------------

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if self._credits_open:
                # Any key dismisses credits
                self._credits_open = False
                return
            if event.key in (pygame.K_UP, pygame.K_w):
                self.selected = (self.selected - 1) % len(self.options)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected = (self.selected + 1) % len(self.options)
            elif event.key == pygame.K_RETURN:
                self._activate()

    def _activate(self):
        opt = self.options[self.selected]
        if opt == "Continue":
            # Restore faction from save so gameplay uses the right powers
            saved_faction = self.game.save_data.get("faction")
            if saved_faction:
                self.game.player_faction = saved_faction
            self.game.save_data["respawn"] = True
            self.game.change_scene(
                SCENE_GAMEPLAY,
                level=self.game.save_data.get("checkpoint_level", "level_1"))
        elif opt == "New Game":
            self.game.clear_save()
            self.game.change_scene(SCENE_FACTION_SELECT)
        elif opt == "Credits":
            self._credits_open = True
        else:
            self.game.running = False

    # ------------------------------------------------------------------

    def update(self, dt):
        # Pulse at a slightly faster rate than before: period ~90 frames (P4-5)
        self._pulse += 0.044 * self._pulse_dir
        if self._pulse >= 1.0:
            self._pulse_dir = -1
        elif self._pulse <= 0.0:
            self._pulse_dir = 1

        # Scroll parallax layers left (P4-5)
        if not self._credits_open:
            for speed, _color, shapes in _PARALLAX_LAYERS:
                for shape in shapes:
                    shape[0] -= speed
                    if shape[0] + shape[2] < 0:
                        shape[0] += SCREEN_WIDTH * 2

    # ------------------------------------------------------------------

    def draw(self, surface):
        surface.fill((8, 4, 18))   # Very dark purple-black background

        # Parallax background layers (P4-5)
        for _speed, color, shapes in _PARALLAX_LAYERS:
            for sx, sy, sw, sh in shapes:
                # Draw the shape; it may appear once or twice (wrap around)
                if sx < SCREEN_WIDTH:
                    pygame.draw.rect(surface, color, (int(sx), sy, sw, sh))
                if sx + sw > SCREEN_WIDTH:
                    pygame.draw.rect(surface, color,
                                     (int(sx) - SCREEN_WIDTH * 2, sy, sw, sh))

        cx = SCREEN_WIDTH // 2

        # Title with pulsing glow — min-state shifted toward amber per HK-P4-C
        title_color = (
            int(200 + self._pulse * 55),   # R: 200 (amber) → 255 (bright gold)
            int(100 + self._pulse * 110),  # G: 100 (amber) → 210 (bright gold)
            int(20  + self._pulse * 45),   # B:  20 (warm)  →  65
        )
        title       = self.font_title.render("STEAMFALL", True, title_color)
        surface.blit(title, (cx - title.get_width() // 2, 130))

        # Decorative line under title
        pygame.draw.line(surface, GOLD,
            (cx - 260, 225), (cx + 260, 225), 1)

        # Subtitle
        sub = self.font_sub.render(
            "Ink or Iron.  Choose your transcendence.", True, GRAY)
        surface.blit(sub, (cx - sub.get_width() // 2, 242))

        # Menu options
        for i, opt in enumerate(self.options):
            is_sel = (i == self.selected)
            color  = WHITE if is_sel else GRAY
            text   = self.font_menu.render(opt, True, color)
            tx     = cx - text.get_width() // 2
            ty     = 340 + i * 60

            surface.blit(text, (tx, ty))

            # Selection diamond marker
            if is_sel:
                pygame.draw.polygon(surface, GOLD, [
                    (tx - 22, ty + 17),
                    (tx - 14, ty + 9),
                    (tx - 6,  ty + 17),
                    (tx - 14, ty + 25),
                ])

        # Footer hint
        hint = self.font_hint.render(
            "↑↓  Navigate     ENTER  Confirm", True, (60, 60, 60))
        surface.blit(hint, (cx - hint.get_width() // 2, SCREEN_HEIGHT - 38))

        # Credits overlay (P4-5)
        if self._credits_open:
            self._draw_credits(surface)

    def _draw_credits(self, surface: pygame.Surface) -> None:
        """Draw a centered semi-transparent credits overlay."""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        surface.blit(overlay, (0, 0))

        cx = SCREEN_WIDTH  // 2
        cy = SCREEN_HEIGHT // 2

        line_h = self.font_credits.get_height() + 10
        total_h = len(CREDITS_TEXT) * line_h
        start_y = cy - total_h // 2

        for i, line in enumerate(CREDITS_TEXT):
            if not line:
                continue
            if i == 0:
                surf = self.font_title.render(line, True, GOLD)
            else:
                surf = self.font_credits.render(line, True, WHITE)
            surface.blit(surf, (cx - surf.get_width() // 2, start_y + i * line_h))

        hint = self.font_hint.render("Press any key to close", True, (80, 80, 80))
        surface.blit(hint,
                     (cx - hint.get_width() // 2, SCREEN_HEIGHT - 50))
