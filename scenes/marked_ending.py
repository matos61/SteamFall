# =============================================================================
# scenes/marked_ending.py — 8-beat ending cutscene for the Marked path.
#
# Triggered after the player defeats the Architect as a Marked character.
# Plays 8 narrative beats then writes save_data["ending"] = "marked" and
# returns to the main menu.
# =============================================================================

import pygame
from settings import (FACTION_MARKED, MARKED_COLOR,
                      SCREEN_WIDTH, SCREEN_HEIGHT, BLACK,
                      SCENE_MAIN_MENU, SCENE_MARKED_ENDING)
from scenes.base_scene import BaseScene
from systems.dialogue  import DialogueBox


_MARKED_ENDING_BEATS = [
    ((20, 10, 40), "???",
        "The Rite is complete. The ink holds."),

    ((30, 15, 50), "Narrator",
        "The Architect's collapse unseals the Archive vault. Ancient rune-scripts flood the surface for the first time in centuries."),

    ((40, 20, 60), "Narrator",
        "The Fleshforged machinery grinds to silence. Without the stolen soul-current, the augments go cold."),

    ((50, 25, 70), "Rune-Archivist",
        "You are the first Transcendent. What was taken from Kael was not wasted."),

    ((30, 15, 55), "Narrator",
        "The city does not forget its debts. The Marked rebuild in the silence."),

    ((20, 10, 45), "Narrator",
        "You do not return to the mines. The ink does not allow it."),

    ((15,  8, 40), "Narrator",
        "Somewhere beneath the Foundry, a new Rite is already being prepared."),

    ((10,  5, 30), "???",
        "The cycle endures."),
]


class MarkedEndingScene(BaseScene):
    def __init__(self, game):
        super().__init__(game)
        self._beat_index = 0
        self._dialogue   = DialogueBox(faction=FACTION_MARKED)
        self._font_skip  = pygame.font.SysFont("monospace", 13)
        self._fade_alpha = 255
        self._fade_surf  = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self._fade_surf.fill(BLACK)
        r, g, b = _MARKED_ENDING_BEATS[0][0]
        self._bg = [float(r), float(g), float(b)]

    # ------------------------------------------------------------------

    def on_enter(self, **kwargs):
        self._beat_index = 0
        r, g, b = _MARKED_ENDING_BEATS[0][0]
        self._bg         = [float(r), float(g), float(b)]
        self._fade_alpha = 255
        self._load_beat(0)

    def _load_beat(self, index: int):
        _, speaker, text = _MARKED_ENDING_BEATS[index]
        self._dialogue.queue([(speaker, text)])

    def _bg_target(self):
        return _MARKED_ENDING_BEATS[self._beat_index][0]

    # ------------------------------------------------------------------

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._finish()
                return
            if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self._advance()

    def _advance(self):
        if self._dialogue.is_done():
            return
        self._dialogue.advance()
        if self._dialogue.is_done():
            self._next_beat()

    def _next_beat(self):
        self._beat_index += 1
        if self._beat_index >= len(_MARKED_ENDING_BEATS):
            self._finish()
        else:
            self._load_beat(self._beat_index)

    def _finish(self):
        self.game.save_data["ending"] = "marked"
        self.game.save_to_disk()
        self.game.change_scene(SCENE_MAIN_MENU)

    # ------------------------------------------------------------------

    def update(self, dt):
        self._dialogue.update()

        if self._fade_alpha > 0:
            self._fade_alpha = max(0, self._fade_alpha - 5)

        tr, tg, tb = self._bg_target()
        spd = 0.18
        self._bg[0] += (tr - self._bg[0]) * spd
        self._bg[1] += (tg - self._bg[1]) * spd
        self._bg[2] += (tb - self._bg[2]) * spd

    # ------------------------------------------------------------------

    def draw(self, surface):
        surface.fill((int(self._bg[0]), int(self._bg[1]), int(self._bg[2])))

        if self._fade_alpha > 0:
            self._fade_surf.set_alpha(self._fade_alpha)
            surface.blit(self._fade_surf, (0, 0))

        progress = (self._beat_index + 1) / len(_MARKED_ENDING_BEATS)
        bar_w    = int(SCREEN_WIDTH * progress)
        pygame.draw.rect(surface, MARKED_COLOR, (0, 0, bar_w, 3))

        skip = self._font_skip.render("ESC — skip ending", True, (50, 40, 70))
        surface.blit(skip, (SCREEN_WIDTH - skip.get_width() - 16, 10))

        self._dialogue.draw(surface)
