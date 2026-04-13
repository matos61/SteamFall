# =============================================================================
# scenes/fleshforged_prologue.py — Story beats for the Fleshforged path.
# Same structure as marked_prologue.py — swap beats, swap faction color.
# =============================================================================

import pygame
from settings import *
from scenes.base_scene import BaseScene
from systems.dialogue  import DialogueBox


FLESHFORGED_BEATS = [
    # -- Mine life --
    ((18, 10,  5), "",       "Duskholm. End of the rail line. Beginning of nothing."),
    ((18, 10,  5), "Narrator","You and Sera worked the east shaft. Six days a week. No days off if rent was late."),
    ((18, 10,  5), "Narrator","Her mod was a reinforced shoulder joint. Yours: a pressure-regulating lung insert. Both were second-hand. Both hurt."),
    ((18, 10,  5), "Sera",    "Tonight we eat real food. I found a bonus canister in the company locker."),
    ((18, 10,  5), "Narrator","You laughed. First time in a week."),

    # -- Collapse --
    ((10,  5,  2), "Narrator","The east shaft collapsed at midday. No warning. Just sound, then dark, then weight."),
    ((10,  5,  2), "Narrator","You couldn't feel your legs. You could feel Sera's hands. Pulling."),
    ((10,  5,  2), "Sera",    "Stay with me. Stay with me. Stay with me—"),

    # -- The doctor --
    ((14,  7,  3), "Narrator","Dr. Orven didn't ask questions. He asked for payment first."),
    ((14,  7,  3), "Dr. Orven","Spine's gone. Three ribs punctured a lung. You need a full lower rebuild plus respiratory mod."),
    ((14,  7,  3), "Dr. Orven","One option: you go into debt for the full surgery. Forty years minimum. Or..."),
    ((14,  7,  3), "Dr. Orven","...you donate your existing mods to her. She walks out. You don't."),
    ((14,  7,  3), "Narrator","Sera was already shaking her head."),

    # -- Her choice --
    ((12,  6,  3), "Sera",    "Don't you dare. Don't you dare make that choice."),
    ((12,  6,  3), "Sera",    "You take the debt. You go further. You climb. For both of us."),
    ((12,  6,  3), "Narrator","She convinced Orven to front the surgery on a military contract. She signed it for you."),
    ((12,  6,  3), "Narrator","The anesthesia took hold. Her hand let go."),

    # -- Awakening --
    ((22, 12,  5), "Narrator","You woke rebuilt. Your spine was titanium-laced. Your lung was clean, mechanical, permanent."),
    ((22, 12,  5), "Narrator","Sera's chair was empty. Orven wouldn't meet your eyes."),
    ((22, 12,  5), "Narrator","A man in a military coat stood at the foot of the bed."),
    ((22, 12,  5), "Recruiter","The contract covers your surgery. In return: service. You leave at dawn."),
    ((22, 12,  5), "Narrator","You said nothing. You stood. That was enough."),
    ((22, 12,  5), "",        "[ MOVE  ·  FIGHT  ·  CLIMB ]"),
]


class FleshforgedPrologueScene(BaseScene):
    def __init__(self, game):
        super().__init__(game)
        self._beat_index  = 0
        self._dialogue    = DialogueBox(faction=FACTION_FLESHFORGED)
        self._font_skip   = pygame.font.SysFont("monospace", 13)
        self._fade_alpha  = 255
        self._fade_surf   = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self._fade_surf.fill(BLACK)

    def on_enter(self, **kwargs):
        self._beat_index = 0
        self._load_beat(0)

    def _load_beat(self, index: int):
        _, speaker, text = FLESHFORGED_BEATS[index]
        self._dialogue.queue([(speaker, text)])
        self._fade_alpha = 180

    # ------------------------------------------------------------------

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self._advance()
            elif event.key == pygame.K_ESCAPE:
                self.game.change_scene(SCENE_GAMEPLAY)

    def _advance(self):
        self._dialogue.advance()
        if self._dialogue.is_done():
            self._beat_index += 1
            if self._beat_index >= len(FLESHFORGED_BEATS):
                self.game.change_scene(SCENE_GAMEPLAY)
            else:
                self._load_beat(self._beat_index)

    def update(self, dt):
        self._dialogue.update()
        if self._fade_alpha > 0:
            self._fade_alpha = max(0, self._fade_alpha - 6)

    def draw(self, surface):
        bg_color = FLESHFORGED_BEATS[self._beat_index][0]
        surface.fill(bg_color)

        if self._fade_alpha > 0:
            self._fade_surf.set_alpha(self._fade_alpha)
            surface.blit(self._fade_surf, (0, 0))

        counter = self._font_skip.render(
            f"{self._beat_index + 1} / {len(FLESHFORGED_BEATS)}    ESC — skip prologue",
            True, (60, 35, 18))
        surface.blit(counter, (20, 16))

        self._dialogue.draw(surface)
