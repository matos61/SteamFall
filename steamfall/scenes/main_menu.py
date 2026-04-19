# =============================================================================
# scenes/main_menu.py — Title screen.
#
# Controls: UP/DOWN to move selection, ENTER to confirm.
# =============================================================================

import pygame
from settings import *
from scenes.base_scene import BaseScene


class MainMenuScene(BaseScene):
    def __init__(self, game):
        super().__init__(game)
        self.font_title  = pygame.font.SysFont("georgia", 76, bold=True)
        self.font_sub    = pygame.font.SysFont("georgia", 26)
        self.font_menu   = pygame.font.SysFont("georgia", 34)

        self.options  = ["Begin", "Quit"]   # rebuilt in on_enter
        self.selected = 0

        # Subtle breathing animation for the title
        self._pulse     = 0.0
        self._pulse_dir = 1

    def on_enter(self, **kwargs):
        # Show "Continue" at top when a checkpoint save exists
        if self.game.save_data.get("checkpoint_pos"):
            self.options = ["Continue", "New Game", "Quit"]
        else:
            self.options = ["New Game", "Quit"]
        self.selected = 0

    # ------------------------------------------------------------------

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.selected = (self.selected - 1) % len(self.options)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected = (self.selected + 1) % len(self.options)
            elif event.key == pygame.K_RETURN:
                self._activate()

    def _activate(self):
        opt = self.options[self.selected]
        if opt == "Continue":
            self.game.save_data["respawn"] = True
            self.game.change_scene(
                SCENE_GAMEPLAY,
                level=self.game.save_data.get("checkpoint_level", "level_1"),
            )
        elif opt == "New Game":
            self.game.player_faction = None
            self.game.clear_save()
            self.game.change_scene(SCENE_FACTION_SELECT)
        else:
            self.game.running = False

    # ------------------------------------------------------------------

    def update(self, dt):
        # Pulse value oscillates 0 → 12 → 0, used for title brightness
        self._pulse += 0.04 * self._pulse_dir
        if self._pulse >= 1.0:
            self._pulse_dir = -1
        elif self._pulse <= 0.0:
            self._pulse_dir = 1

    # ------------------------------------------------------------------

    def draw(self, surface):
        surface.fill((8, 4, 18))   # Very dark purple-black background

        cx = SCREEN_WIDTH // 2

        # Title with pulsing glow color
        glow_val = int(180 + self._pulse * 75)
        title_color = (glow_val, int(glow_val * 0.84), 50)
        title = self.font_title.render("STEAMFALL", True, title_color)
        surface.blit(title, (cx - title.get_width() // 2, 130))

        # Decorative line under title
        pygame.draw.line(surface, GOLD,
            (cx - 260, 225), (cx + 260, 225), 1)

        # Subtitle
        sub = self.font_sub.render("Ink or Iron.  Choose your transcendence.", True, GRAY)
        surface.blit(sub, (cx - sub.get_width() // 2, 242))

        # Menu options
        for i, opt in enumerate(self.options):
            is_sel = (i == self.selected)
            color  = WHITE if is_sel else GRAY
            text   = self.font_menu.render(opt, True, color)
            tx     = cx - text.get_width() // 2
            ty     = 360 + i * 64

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
        hint = pygame.font.SysFont("monospace", 14).render(
            "↑↓  Navigate     ENTER  Confirm", True, (60, 60, 60))
        surface.blit(hint, (cx - hint.get_width() // 2, SCREEN_HEIGHT - 38))
