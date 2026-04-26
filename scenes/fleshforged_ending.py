# =============================================================================
# scenes/fleshforged_ending.py — 8-beat ending cutscene for the Fleshforged path.
#
# Triggered after the player defeats the Architect as a Fleshforged character.
# Plays 8 narrative beats then writes save_data["ending"] = "fleshforged" and
# returns to the main menu.
# =============================================================================

import pygame
from settings import (FACTION_FLESHFORGED, FLESHFORGED_COLOR,
                      SCREEN_WIDTH, SCREEN_HEIGHT, BLACK,
                      SCENE_MAIN_MENU, SCENE_FLESHFORGED_ENDING)
from scenes.base_scene import BaseScene
from systems.dialogue  import DialogueBox


_FLESHFORGED_ENDING_BEATS = [
    ((60, 25,  5), "???",
        "The Architect is yours. Sera would call this victory."),

    ((70, 30,  5), "Narrator",
        "The energy lattice snaps into place. The city's heat-grid flickers back to life under Fleshforged control."),

    ((60, 25,  5), "Narrator",
        "The Marked flee underground. Without the Architect's amplification, their Rites are limited to single practitioners."),

    ((50, 20,  5), "Sera's Datalog",
        "Addendum — final entry. Power source secured. City access: 100%. Soul-drain reversed."),

    ((40, 15,  5), "Narrator",
        "The augments remember her work. Every Fleshforged operative carries a piece of what Sera built."),

    ((30, 12,  5), "Narrator",
        "The Foundry rebuilds. It does not sleep."),

    ((20, 10,  5), "Narrator",
        "Somewhere beneath the old Archive, something ancient did not die."),

    ((10,  5,  5), "???",
        "The cycle endures."),
]


class FleshforgedEndingScene(BaseScene):
    def __init__(self, game):
        super().__init__(game)
        self._beat_index = 0
        self._dialogue   = DialogueBox(faction=FACTION_FLESHFORGED)
        self._font_skip  = pygame.font.SysFont("monospace", 13)
        self._fade_alpha = 255
        self._fade_surf  = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self._fade_surf.fill(BLACK)
        r, g, b = _FLESHFORGED_ENDING_BEATS[0][0]
        self._bg = [float(r), float(g), float(b)]

    # ------------------------------------------------------------------

    def on_enter(self, **kwargs):
        self._beat_index = 0
        r, g, b = _FLESHFORGED_ENDING_BEATS[0][0]
        self._bg         = [float(r), float(g), float(b)]
        self._fade_alpha = 255
        self._load_beat(0)

    def _load_beat(self, index: int):
        _, speaker, text = _FLESHFORGED_ENDING_BEATS[index]
        self._dialogue.queue([(speaker, text)])

    def _bg_target(self):
        return _FLESHFORGED_ENDING_BEATS[self._beat_index][0]

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
        if self._beat_index >= len(_FLESHFORGED_ENDING_BEATS):
            self._finish()
        else:
            self._load_beat(self._beat_index)

    def _finish(self):
        self.game.save_data["ending"] = "fleshforged"
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

        progress = (self._beat_index + 1) / len(_FLESHFORGED_ENDING_BEATS)
        bar_w    = int(SCREEN_WIDTH * progress)
        pygame.draw.rect(surface, FLESHFORGED_COLOR, (0, 0, bar_w, 3))

        skip = self._font_skip.render("ESC — skip ending", True, (65, 42, 22))
        surface.blit(skip, (SCREEN_WIDTH - skip.get_width() - 16, 10))

        self._dialogue.draw(surface)
