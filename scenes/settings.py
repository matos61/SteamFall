"""scenes/settings.py — In-game settings screen (P4-4).

Accessible from the pause menu via "Settings (soon)" option.
Three rows: Music Volume, SFX Volume, Fullscreen.
UP/DOWN selects row; LEFT/RIGHT adjusts value; ESC returns to the previous scene.
"""

import pygame
from scenes.base_scene import BaseScene
from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    WHITE, GRAY, BLACK,
    SCENE_MAIN_MENU, SCENE_SETTINGS,
    AUDIO_MUSIC_VOLUME, AUDIO_SFX_VOLUME,
)


class SettingsScene(BaseScene):
    """Three-row settings overlay: Music Volume, SFX Volume, Fullscreen toggle."""

    _ROWS = ["Music Volume", "SFX Volume", "Fullscreen"]

    def __init__(self, game):
        super().__init__(game)
        self._return_scene = SCENE_MAIN_MENU
        self._sel          = 0
        self._fullscreen   = False

        # Volume values pulled from save_data or defaults
        self._music_vol = float(game.save_data.get("music_volume", AUDIO_MUSIC_VOLUME))
        self._sfx_vol   = float(game.save_data.get("sfx_volume",   AUDIO_SFX_VOLUME))

        self._font_title = pygame.font.SysFont("georgia",   36, bold=True)
        self._font_row   = pygame.font.SysFont("georgia",   26)
        self._font_hint  = pygame.font.SysFont("monospace", 14)

    # ------------------------------------------------------------------

    def on_enter(self, **kwargs) -> None:
        self._return_scene = kwargs.get("return_scene", SCENE_MAIN_MENU)
        self._sel          = 0
        # Reload persisted values on each enter so they reflect the current save
        self._music_vol = float(
            self.game.save_data.get("music_volume", AUDIO_MUSIC_VOLUME))
        self._sfx_vol   = float(
            self.game.save_data.get("sfx_volume",   AUDIO_SFX_VOLUME))

    # ------------------------------------------------------------------

    def handle_event(self, event) -> None:
        if event.type != pygame.KEYDOWN:
            return

        if event.key == pygame.K_ESCAPE:
            self.game.change_scene(self._return_scene)
            return

        if event.key in (pygame.K_UP, pygame.K_w):
            self._sel = (self._sel - 1) % len(self._ROWS)
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self._sel = (self._sel + 1) % len(self._ROWS)
        elif event.key in (pygame.K_LEFT, pygame.K_a):
            self._adjust(-0.1)
        elif event.key in (pygame.K_RIGHT, pygame.K_d):
            self._adjust(+0.1)
        elif event.key == pygame.K_RETURN:
            if self._sel == 2:   # Fullscreen toggle via ENTER as well
                self._toggle_fullscreen()

    def _adjust(self, delta: float) -> None:
        if self._sel == 0:
            self._music_vol = max(0.0, min(1.0, self._music_vol + delta))
            self.game.audio.set_music_volume(self._music_vol)
            self.game.save_data["music_volume"] = round(self._music_vol, 2)
            self.game.save_to_disk()
        elif self._sel == 1:
            self._sfx_vol = max(0.0, min(1.0, self._sfx_vol + delta))
            self.game.audio.set_sfx_volume(self._sfx_vol)
            self.game.save_data["sfx_volume"] = round(self._sfx_vol, 2)
            self.game.save_to_disk()
        elif self._sel == 2:
            self._toggle_fullscreen()

    def _toggle_fullscreen(self) -> None:
        self._fullscreen = not self._fullscreen
        pygame.display.toggle_fullscreen()

    # ------------------------------------------------------------------

    def update(self, dt: int) -> None:
        pass

    # ------------------------------------------------------------------

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(BLACK)

        cx = SCREEN_WIDTH  // 2
        cy = SCREEN_HEIGHT // 2

        # Panel background
        panel_w, panel_h = 480, 320
        panel_x = cx - panel_w // 2
        panel_y = cy - panel_h // 2
        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((10, 10, 20, 220))
        surface.blit(panel, (panel_x, panel_y))
        pygame.draw.rect(surface, GRAY, (panel_x, panel_y, panel_w, panel_h), 1)

        # Title
        title = self._font_title.render("SETTINGS", True, WHITE)
        surface.blit(title, (cx - title.get_width() // 2, panel_y + 22))

        # Rows
        for i, row_name in enumerate(self._ROWS):
            y     = panel_y + 100 + i * 64
            color = WHITE if i == self._sel else GRAY

            # Row label
            lbl = self._font_row.render(row_name, True, color)
            surface.blit(lbl, (panel_x + 30, y))

            # Value display
            if i == 0:
                val_text, val_frac = f"{self._music_vol:.0%}", self._music_vol
            elif i == 1:
                val_text, val_frac = f"{self._sfx_vol:.0%}", self._sfx_vol
            else:
                val_text  = "ON" if self._fullscreen else "OFF"
                val_frac  = None

            val_surf = self._font_row.render(val_text, True, color)
            surface.blit(val_surf, (panel_x + panel_w - val_surf.get_width() - 30, y))

            # 10-pip slider for volume rows
            if val_frac is not None:
                bar_x  = panel_x + 30
                bar_y  = y + lbl.get_height() + 4
                bar_w  = panel_w - 60
                pip_w  = (bar_w - 9 * 4) // 10
                filled = round(val_frac * 10)
                for p in range(10):
                    px   = bar_x + p * (pip_w + 4)
                    pcol = WHITE if (i == self._sel and p < filled) else (50, 50, 50)
                    pygame.draw.rect(surface, pcol, (px, bar_y, pip_w, 6))

            # Selection marker
            if i == self._sel:
                pygame.draw.polygon(surface, WHITE,
                                    [(panel_x + 14, y + 6),
                                     (panel_x + 14, y + 18),
                                     (panel_x + 22, y + 12)])

        # Hint footer
        hint = self._font_hint.render(
            "↑↓ Select   ←→ Adjust   ESC Back", True, (80, 80, 80))
        surface.blit(hint, (cx - hint.get_width() // 2,
                            panel_y + panel_h - hint.get_height() - 10))
