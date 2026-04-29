"""scenes/settings.py — In-game settings screen (Task P4-4).

Accessible from the pause menu.  Three adjustable rows:
  Music Volume  — 0.0–1.0 in 0.1 steps, visualised as a 10-pip bar.
  SFX Volume    — same.
  Fullscreen    — boolean toggle, shown as ON / OFF.

UP/DOWN navigates rows; LEFT/RIGHT adjusts the selected row; ESC returns to
the scene stored in `_return_scene` (set via on_enter(return_scene=…)).
Volume changes take effect immediately via game.audio and are persisted in
game.save_data.
"""

import pygame
from scenes.base_scene import BaseScene
from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    WHITE, GRAY, BLACK, DARK_GRAY,
    SCENE_MAIN_MENU,
    AUDIO_MUSIC_VOLUME, AUDIO_SFX_VOLUME,
)

# Pip dimensions for the volume bar
_PIP_W  = 16
_PIP_H  = 12
_PIP_GAP = 4


class SettingsScene(BaseScene):
    """Settings screen: Music Volume, SFX Volume, Fullscreen toggle."""

    def on_enter(self, **kwargs) -> None:
        self._return_scene = kwargs.get("return_scene", SCENE_MAIN_MENU)
        self._rows         = ["Music Volume", "SFX Volume", "Fullscreen"]
        self._sel          = 0

        # Reload persisted values (fall back to defaults if absent)
        self._music_vol  = float(
            self.game.save_data.get("music_vol", AUDIO_MUSIC_VOLUME))
        self._sfx_vol    = float(
            self.game.save_data.get("sfx_vol", AUDIO_SFX_VOLUME))
        self._fullscreen = bool(
            self.game.save_data.get("fullscreen", False))

        # Apply current values immediately so audio reflects save state
        self.game.audio.set_music_volume(self._music_vol)
        self.game.audio.set_sfx_volume(self._sfx_vol)

        # Fonts (created fresh on each enter so pygame.font is ready)
        self._font_title = pygame.font.SysFont("georgia",   42)
        self._font_row   = pygame.font.SysFont("georgia",   28)
        self._font_hint  = pygame.font.SysFont("monospace", 14)

    # ------------------------------------------------------------------
    # Event handling
    # ------------------------------------------------------------------

    def handle_event(self, event) -> None:
        if event.type != pygame.KEYDOWN:
            return

        if event.key == pygame.K_ESCAPE:
            self.game.change_scene(self._return_scene)
            return

        if event.key in (pygame.K_UP, pygame.K_w):
            self._sel = (self._sel - 1) % len(self._rows)
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self._sel = (self._sel + 1) % len(self._rows)
        elif event.key in (pygame.K_LEFT, pygame.K_a):
            self._adjust(-0.1)
        elif event.key in (pygame.K_RIGHT, pygame.K_d):
            self._adjust(+0.1)

    def _adjust(self, delta: float) -> None:
        if self._sel == 0:
            self._music_vol = round(max(0.0, min(1.0,
                                                  self._music_vol + delta)), 1)
            self.game.audio.set_music_volume(self._music_vol)
            self.game.save_data["music_vol"] = self._music_vol
        elif self._sel == 1:
            self._sfx_vol = round(max(0.0, min(1.0,
                                               self._sfx_vol + delta)), 1)
            self.game.audio.set_sfx_volume(self._sfx_vol)
            self.game.save_data["sfx_vol"] = self._sfx_vol
        elif self._sel == 2:
            self._fullscreen = not self._fullscreen
            pygame.display.toggle_fullscreen()
            self.game.save_data["fullscreen"] = self._fullscreen

    # ------------------------------------------------------------------

    def update(self, dt: int) -> None:
        pass

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(BLACK)

        cx = SCREEN_WIDTH // 2

        # Title — centred at the top quarter of the screen
        title = self._font_title.render("SETTINGS", True, WHITE)
        surface.blit(title, (cx - title.get_width() // 2, 60))

        # Three rows, starting at SCREEN_HEIGHT//2 - 60, spaced 70 px apart
        label_x = SCREEN_WIDTH // 4
        row_start_y = SCREEN_HEIGHT // 2 - 60

        for i, row_name in enumerate(self._rows):
            y     = row_start_y + i * 70
            color = WHITE if i == self._sel else GRAY

            # Selection marker ▶ left of label
            if i == self._sel:
                marker = self._font_row.render("▶", True, WHITE)
                surface.blit(marker, (label_x - marker.get_width() - 10, y))

            # Row label
            lbl = self._font_row.render(row_name, True, color)
            surface.blit(lbl, (label_x, y))

            # Value display — right of label
            val_x = label_x + lbl.get_width() + 20

            if i == 0:
                # Music Volume pip bar
                filled = round(self._music_vol * 10)
                self._draw_pip_bar(surface, val_x, y + (lbl.get_height() - _PIP_H) // 2,
                                   filled)
            elif i == 1:
                # SFX Volume pip bar
                filled = round(self._sfx_vol * 10)
                self._draw_pip_bar(surface, val_x, y + (lbl.get_height() - _PIP_H) // 2,
                                   filled)
            else:
                # Fullscreen ON/OFF label
                fs_text = "ON" if self._fullscreen else "OFF"
                fs_surf = self._font_row.render(fs_text, True, color)
                surface.blit(fs_surf, (val_x, y))

        # Hint at the bottom
        hint = self._font_hint.render(
            "← → Adjust   ↑↓ Navigate   ESC Back",
            True, GRAY)
        surface.blit(hint,
                     (cx - hint.get_width() // 2, SCREEN_HEIGHT - 50))

    def _draw_pip_bar(self, surface: pygame.Surface,
                      x: int, y: int, filled: int) -> None:
        """Draw 10 pips starting at (x, y).  `filled` pips use WHITE; rest DARK_GRAY."""
        for p in range(10):
            px    = x + p * (_PIP_W + _PIP_GAP)
            color = WHITE if p < filled else DARK_GRAY
            pygame.draw.rect(surface, color, (px, y, _PIP_W, _PIP_H))
