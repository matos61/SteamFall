# =============================================================================
# scenes/marked_prologue.py — Story beats for the Marked (arcane tattoo) path.
#
# Beat format:
#   (bg_color_rgb, speaker, text_or_config)
#
#   speaker == ""              → narrator caption (no badge, dimmer text)
#   speaker == "__tutorial__"  → inline control tutorial (text is a config dict)
#
# Scene lerps background color smoothly between beats.
# Tutorial beats pause dialogue and hand control to TutorialMinigame.
# =============================================================================

import pygame
from settings import *
from scenes.base_scene         import BaseScene
from systems.dialogue          import DialogueBox
from systems.tutorial_minigame import TutorialMinigame
from systems.voice_player      import VoicePlayer


MARKED_BEATS = [
    # ==========================================================================
    # THE GREYPIT
    # ==========================================================================
    ((10,  6, 20), "",
        "Greypit. They called it that because the only thing it ever grew was graves."),

    ((10,  6, 20), "",
        "You and Kael had a system. You spooked the mark — he swept the drop. Together you ate. Some nights."),

    ((14,  8, 25), "",
        "Tonight's mark: one loaf of dark rye at Maren's stall. Unguarded. You'd clocked the gap in her rhythm for three days."),

    # TUTORIAL: learn to move
    ((14,  8, 25), "__tutorial__",
        {"type": "move", "prompt": "Reach for it."}),

    ((14,  8, 25), "",
        "A fist. Jaw. The cobblestones came up fast and tasted like copper and old rain."),

    ((10,  5, 15), "",
        "The other orphans swarmed before you stopped moving. Took the bread, your boots, the copper pin Kael had kept safe for you all winter."),

    # ==========================================================================
    # BROTHERHOOD
    # ==========================================================================
    ((12,  8, 22), "Kael",
        "Here. Take mine."),

    ((12,  8, 22), "",
        "Half a loaf, hard as the statue at your backs. You ate. He watched the carvings on its base instead."),

    ((12,  8, 22), "Kael",
        "See those markings? I've been reading them. Three weeks. I have eight words."),

    ((12,  8, 22), "",
        "You told him that was the most useless thing you'd ever heard anyone do with hunger. He grinned."),

    ((12,  8, 22), "Kael",
        "Old words have power. Even here. Especially here."),

    # ==========================================================================
    # THE CHURCH ARRIVES
    # ==========================================================================
    (( 5,  3, 18), "",
        "The robed figures came in the deep of winter. Their lanterns burned a color that had no name in Greypit."),

    (( 5,  3, 18), "Elder",
        "We have watched you both. The Church of Runes offers more than bread. It offers a shape to what you already are."),

    (( 5,  3, 18), "",
        "The first tattoo took four hours. Fire, then cold, then something vast cracked open behind your eyes like a door that had always been there."),

    # TUTORIAL: learn to attack (the Arcane Trials begin)
    (( 8,  4, 22), "__tutorial__",
        {"type": "attack", "prompt": "Strike the trial rune."}),

    # ==========================================================================
    # THE TRIALS
    # ==========================================================================
    (( 8,  4, 22), "Elder",
        "The Arcane Trials will demand everything you have built of yourself. Most who enter do not return. This is not a warning. It is a fact."),

    (( 8,  4, 22), "",
        "Seven entered the Trial Halls. Five names were carved into the memorial wall before the week was out."),

    (( 8,  4, 22), "Kael",
        "Stay close. Whatever they show you in there — don't let it change your answer."),

    (( 8,  4, 22), "",
        "You never learned what answer he meant. You assumed there was time."),

    # ==========================================================================
    # THE KNIFE
    # ==========================================================================
    (( 4,  2, 14), "Elder",
        "The final rite is simple. Only one soul shall ascend. The other nourishes the ink."),

    (( 4,  2, 14), "",
        "A blade landed between you on the stone floor. Clean edge. Well-oiled handle. They had prepared it."),

    (( 4,  2, 14), "",
        "You looked at Kael. He was already looking at the door — not the blade. Like he had already settled this before you walked in."),

    (( 4,  2, 14), "Kael",
        "Don't. I've already decided."),

    (( 4,  2, 14), "",
        "Kael—"),

    (( 4,  2, 14), "Kael",
        "I watched you in those halls. The way you moved. You were magnificent. You were ours."),

    (( 4,  2, 14), "Kael",
        "That matters more than me. Go. Be something the world can't ignore."),

    (( 2,  1,  8), "",
        "He was faster. He was always faster than you."),

    (( 2,  1,  8), "",
        "He pressed the handle into your hands. And fell."),

    # ==========================================================================
    # AWAKENING
    # ==========================================================================
    ((20, 10, 50), "",
        "You woke alone in the Hall of Runes. Every inch of your skin burned with living light."),

    ((20, 10, 50), "",
        "The ink had taken. It sang in your veins — not like power. Like purpose. Like something that had always been there finally given a name."),

    # TUTORIAL: learn the faction ability
    ((20, 10, 50), "__tutorial__",
        {"type": "ability_marked", "prompt": "Release what was poured into you."}),

    ((20, 10, 50), "",
        "Then the doors tore inward. Something had followed the light of the ceremony through the dark."),

    ((20, 10, 50), "",
        "You rose. For the first time in your life, you were not afraid of what came next."),
]


class MarkedPrologueScene(BaseScene):
    def __init__(self, game):
        super().__init__(game)
        self._beat_index = 0
        self._dialogue   = DialogueBox(faction=FACTION_MARKED)
        self._tutorial   = None
        self._voice      = VoicePlayer()
        self._font_skip  = pygame.font.SysFont("monospace", 13)
        self._fade_alpha = 255
        self._fade_surf  = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self._fade_surf.fill(BLACK)
        r, g, b = MARKED_BEATS[0][0]
        self._bg = [float(r), float(g), float(b)]

    # ------------------------------------------------------------------

    def on_enter(self, **kwargs):
        self._beat_index = 0
        r, g, b = MARKED_BEATS[0][0]
        self._bg         = [float(r), float(g), float(b)]
        self._fade_alpha = 255
        self._tutorial   = None
        self._load_beat(0)

    def _load_beat(self, index: int):
        _, speaker, data = MARKED_BEATS[index]
        if speaker == "__tutorial__":
            self._tutorial = TutorialMinigame(
                goal_type=data["type"],
                prompt=data["prompt"],
                faction=FACTION_MARKED,
            )
            self._dialogue.queue([])   # Clear any leftover dialogue state
            self._voice.stop()
        else:
            self._tutorial = None
            self._dialogue.queue([(speaker, data)])
            self._voice.play(FACTION_MARKED, index)

    def _bg_target(self):
        return MARKED_BEATS[self._beat_index][0]

    # ------------------------------------------------------------------

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            # ESC always skips to gameplay
            if event.key == pygame.K_ESCAPE:
                self._voice.stop()
                self.game.change_scene(SCENE_GAMEPLAY)
                return
            # While a tutorial is running, delegate ALL input to it
            if self._tutorial is not None:
                self._tutorial.handle_event(event)
                return
            if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self._advance()

    def _advance(self):
        if self._tutorial is not None:
            return   # Tutorial completes itself
        # If voice is still mid-line and text is fully revealed, let voice finish;
        # a second press skips it.
        self._voice.stop()
        self._dialogue.advance()
        if self._dialogue.is_done():
            self._next_beat()

    def _next_beat(self):
        self._beat_index += 1
        if self._beat_index >= len(MARKED_BEATS):
            self.game.change_scene(SCENE_GAMEPLAY)
        else:
            self._load_beat(self._beat_index)

    # ------------------------------------------------------------------

    def update(self, dt):
        # Tutorial takes over update while active
        if self._tutorial is not None:
            self._tutorial.update()
            if self._tutorial.is_complete():
                self._tutorial = None
                self._next_beat()
        else:
            self._dialogue.update()

        if self._fade_alpha > 0:
            self._fade_alpha = max(0, self._fade_alpha - 5)

        # Lerp background toward current beat's target color
        tr, tg, tb = self._bg_target()
        spd = 0.07
        self._bg[0] += (tr - self._bg[0]) * spd
        self._bg[1] += (tg - self._bg[1]) * spd
        self._bg[2] += (tb - self._bg[2]) * spd

    # ------------------------------------------------------------------

    def draw(self, surface):
        surface.fill((int(self._bg[0]), int(self._bg[1]), int(self._bg[2])))

        # Entry fade from black
        if self._fade_alpha > 0:
            self._fade_surf.set_alpha(self._fade_alpha)
            surface.blit(self._fade_surf, (0, 0))

        # Progress bar — thin line at very top, faction-colored
        progress = (self._beat_index + 1) / len(MARKED_BEATS)
        bar_w    = int(SCREEN_WIDTH * progress)
        pygame.draw.rect(surface, MARKED_COLOR, (0, 0, bar_w, 3))

        # Skip hint — top right, very subtle
        skip = self._font_skip.render("ESC — skip prologue", True, (50, 40, 70))
        surface.blit(skip, (SCREEN_WIDTH - skip.get_width() - 16, 10))

        # Tutorial overlays background; dialogue box sits at the bottom
        if self._tutorial is not None:
            self._tutorial.draw(surface)
        else:
            self._dialogue.draw(surface)
