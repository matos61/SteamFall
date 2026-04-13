# =============================================================================
# scenes/marked_prologue.py — Story beats for the Marked (arcane tattoo) path.
#
# Each "beat" is: (background_color, speaker, dialogue_text)
# The scene cycles through beats when the player presses SPACE.
# After the last beat it transitions to the gameplay scene.
# =============================================================================

import pygame
from settings import *
from scenes.base_scene import BaseScene
from systems.dialogue  import DialogueBox


# ---------------------------------------------------------------------------
# Beat format: (bg_color_rgb, speaker_string, dialogue_text)
#   bg_color: fill color that evokes the setting (dark = night/despair, etc.)
#   speaker: "" for narrator captions
# ---------------------------------------------------------------------------
MARKED_BEATS = [
    # -- Childhood --
    ((10,  6,  20), "",         "The slums had no name. Only hunger, and the smell of old rain."),
    ((10,  6,  20), "Narrator", "You and Kael survived on what you could steal."),
    ((14,  8,  25), "Narrator", "Tonight was another hungry night — until you spotted the unguarded stall."),
    ((14,  8,  25), "Narrator", "You reached for the bread. Then a fist found your jaw."),
    ((10,  5,  15), "Narrator", "The other orphans took everything. Left you bleeding on the cobblestone."),

    # -- Brotherhood --
    ((12,  8,  22), "Kael",     "Here. Take mine."),
    ((12,  8,  22), "Narrator", "You two sat beneath a ruined statue. Strange markings covered its base — you'd never noticed before."),
    ((12,  8,  22), "Kael",     "You see those carvings? I think they're words. Old ones."),

    # -- The Church --
    ((5,   3,  18), "Narrator", "They came in winter. Robed figures with lanterns that burned purple-white."),
    ((5,   3,  18), "Elder",    "We have watched you both. Come. The Church of Runes offers more than bread."),
    ((5,   3,  18), "Narrator", "The first tattoo was burned into your wrist. Fire. Then cold. Then something vast opened behind your eyes."),

    # -- Trials --
    ((8,   4,  22), "Elder",    "Most do not survive the Arcane Trials. You will.  Or you will become a lesson."),
    ((8,   4,  22), "Narrator", "Seven entered. Five did not return. Only you and Kael remained, breathing hard in the glow of solved runes."),

    # -- The Knife --
    ((4,   2,  14), "Elder",    "The final rite is simple. Only one soul shall ascend. The other... nourishes the ink."),
    ((4,   2,  14), "Narrator", "A blade clattered onto the stone floor between you."),
    ((4,   2,  14), "Narrator", "You reached for words. Found none. Kael was already moving."),
    ((4,   2,  14), "Kael",     "Don't.  I've seen what you can do. What you'll do."),
    ((4,   2,  14), "Kael",     "You'll be something great. I see it."),
    ((4,   2,  14), "Narrator", "He pressed the handle into your hand. Then fell on the blade himself."),

    # -- Awakening --
    ((20, 10,  50), "Narrator", "You woke alone. The hall hummed with power. Runes burned along your skin."),
    ((20, 10,  50), "Narrator", "Then the doors shattered inward. Something had followed the ceremony's light."),
    ((20, 10,  50), "Narrator", "You rose. For the first time, you did not feel afraid."),
    ((20, 10,  50), "",         "[ MOVE  ·  FIGHT  ·  SURVIVE ]"),
]


class MarkedPrologueScene(BaseScene):
    def __init__(self, game):
        super().__init__(game)
        self._beat_index  = 0
        self._dialogue    = DialogueBox(faction=FACTION_MARKED)
        self._font_skip   = pygame.font.SysFont("monospace", 13)
        self._fade_alpha  = 255       # Used for fade-in at each beat
        self._fade_surf   = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self._fade_surf.fill(BLACK)

    # ------------------------------------------------------------------

    def on_enter(self, **kwargs):
        self._beat_index = 0
        self._load_beat(0)

    def _load_beat(self, index: int):
        _, speaker, text = MARKED_BEATS[index]
        self._dialogue.queue([(speaker, text)])
        self._fade_alpha = 180   # Start each beat with a quick fade-in

    # ------------------------------------------------------------------

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self._advance()
            elif event.key == pygame.K_ESCAPE:
                # Skip entire prologue
                self.game.change_scene(SCENE_GAMEPLAY)

    def _advance(self):
        self._dialogue.advance()
        if self._dialogue.is_done():
            self._beat_index += 1
            if self._beat_index >= len(MARKED_BEATS):
                self.game.change_scene(SCENE_GAMEPLAY)
            else:
                self._load_beat(self._beat_index)

    # ------------------------------------------------------------------

    def update(self, dt):
        self._dialogue.update()
        # Fade in
        if self._fade_alpha > 0:
            self._fade_alpha = max(0, self._fade_alpha - 6)

    # ------------------------------------------------------------------

    def draw(self, surface):
        # Background color for this beat
        bg_color = MARKED_BEATS[self._beat_index][0]
        surface.fill(bg_color)

        # Fade overlay
        if self._fade_alpha > 0:
            self._fade_surf.set_alpha(self._fade_alpha)
            surface.blit(self._fade_surf, (0, 0))

        # Beat counter (subtle)
        counter = self._font_skip.render(
            f"{self._beat_index + 1} / {len(MARKED_BEATS)}    ESC — skip prologue",
            True, (45, 35, 60))
        surface.blit(counter, (20, 16))

        # Dialogue box
        self._dialogue.draw(surface)
