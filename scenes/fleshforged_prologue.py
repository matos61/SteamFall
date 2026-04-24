# =============================================================================
# scenes/fleshforged_prologue.py — Story beats for the Fleshforged path.
#
# Beat format mirrors marked_prologue.py — see that file for documentation.
# "__tutorial__" beats pause the narrative for an inline control tutorial.
# =============================================================================

import pygame
from settings import *
from scenes.base_scene         import BaseScene
from systems.dialogue          import DialogueBox
from systems.tutorial_minigame import TutorialMinigame
from systems.voice_player      import VoicePlayer


FLESHFORGED_BEATS = [
    # ==========================================================================
    # DUSKHOLM — THE MINE
    # ==========================================================================
    ((18, 10,  5), "",
        "Duskholm sat at the end of the rail line like a boot sole — worn, forgotten, but still holding something up."),

    ((18, 10,  5), "",
        "You and Sera worked the east shaft. Six days on, one off. The off day you spent sleeping until your hands stopped shaking."),

    ((18, 10,  5), "",
        "Her mod: reinforced shoulder joint, salvage-grade, left side. Yours: a pressure valve in the right lung, fitted three years back over a badly healed cave-in injury. Both second-hand. Both hurt in the cold."),

    ((18, 10,  5), "Sera",
        "Good news. Found a bonus canister in the foreman's lockbox. Technically, I just found it. It was in a locked box. Details."),

    # TUTORIAL: learn to move
    ((18, 10,  5), "__tutorial__",
        {"type": "move", "prompt": "Pick it up."}),

    ((18, 10,  5), "Sera",
        "Tonight we eat like people who have things to celebrate."),

    ((18, 10,  5), "",
        "You laughed. It felt strange in your chest — like a rusty hinge finally moving. But real."),

    # ==========================================================================
    # THE COLLAPSE
    # ==========================================================================
    ((10,  5,  2), "",
        "The east shaft collapsed at eleven past midday. No alarm. The main pulley just gave — one second of silence, then the noise."),

    ((10,  5,  2), "",
        "Then the weight."),

    (( 8,  4,  1), "",
        "You came back to yourself with the ceiling across your spine and no feeling below the hips. Dust everywhere. The lamps had all gone out."),

    (( 8,  4,  1), "Sera",
        "Stay with me. Don't sleep. I've got you — just keep breathing."),

    # TUTORIAL: learn to jump (escape the collapsing shaft)
    ((10,  5,  2), "__tutorial__",
        {"type": "jump", "prompt": "Get clear — the shaft is coming down."}),

    (( 8,  4,  1), "Sera",
        "I've got you. You're still breathing. That's enough for now. That's everything."),

    # ==========================================================================
    # DR. ORVEN
    # ==========================================================================
    ((14,  7,  3), "",
        "Dr. Orven worked out of a converted pump station two levels up from the mine floor. He didn't ask questions. He asked for payment first."),

    ((14,  7,  3), "Dr. Orven",
        "Spine is shattered at L2 and L3. Three ribs have punctured the left lung. You need a full lower rebuild and complete respiratory overhaul."),

    ((14,  7,  3), "Dr. Orven",
        "Option one: forty-year military debt contract. Surgery is fronted; you work it off in service."),

    ((12,  6,  2), "Dr. Orven",
        "Option two: she donates her existing mods toward the cost. She walks out on her own feet. You get pieced back together."),

    ((12,  6,  2), "",
        "Sera was already shaking her head before he finished the sentence."),

    # ==========================================================================
    # SERA'S CHOICE
    # ==========================================================================
    ((10,  5,  2), "Sera",
        "Don't you dare. If you so much as look at option two I will walk out of here right now and you will never find another surgeon willing to touch you."),

    ((10,  5,  2), "Sera",
        "You take the debt. You go up. You climb until you're the kind of person this was worth something for. For both of us."),

    ((12,  6,  3), "",
        "You watched her convince Orven to front the surgery on a military bond. She pressed her thumb to the contract seal and didn't flinch once."),

    (( 8,  4,  1), "",
        "The anesthesia took hold. The last thing you felt was her hand letting go."),

    # ==========================================================================
    # AWAKENING — REBUILT
    # ==========================================================================
    ((22, 12,  5), "",
        "You woke in a military clinic. Your spine moved. Your lungs drew a full breath — clean, deep, mechanical. Completely yours."),

    # TUTORIAL: learn to attack (testing the rebuilt frame)
    ((22, 12,  5), "__tutorial__",
        {"type": "attack", "prompt": "Test the new frame."}),

    ((22, 12,  5), "",
        "Sera's chair was empty. The orderly wouldn't meet your eyes. You didn't ask."),

    ((22, 12,  5), "",
        "A man in a military coat stood at the foot of your bed. He had been waiting a while, by the look of it."),

    ((22, 12,  5), "Recruiter",
        "The contract has been honored. The surgery was performed, the mods installed. What you owe now is service."),

    ((22, 12,  5), "Recruiter",
        "You leave at dawn. What you make of what you've been given — that's entirely your affair."),

    # TUTORIAL: learn the faction ability (overdrive ignition)
    ((22, 12,  5), "__tutorial__",
        {"type": "ability_fleshforged", "prompt": "Ignite the overdrive. Show us what it bought."}),

    ((22, 12,  5), "",
        "You said nothing. You stood. The floor was cold beneath your new feet. You were not."),

    # ==========================================================================
    # MID-GAME LORE BEATS (indices 30-33) — triggered by leaving level 3.
    # ==========================================================================
    ((60, 30, 10), "Sera's Datalog",
        "The Forgemaster's schematics. Sera copied them before the ambush. The Marked sabotaged the Rite deliberately."),

    ((70, 25, 10), "Sera's Datalog",
        "Soul energy is not mystical. It is thermodynamic — latent chemical potential extracted by augment cores. The Marked know this and call it heresy."),

    ((80, 30, 10), "Sera's Datalog",
        "The Architect is a weapons system. Whoever activates it first controls the city's energy supply. The Marked want it silent. You cannot let that happen."),

    ((50, 20, 10), "???",
        "Sera built this into your augments. Find the Architect before they do."),
]


class FleshforgedPrologueScene(BaseScene):
    def __init__(self, game):
        super().__init__(game)
        self._beat_index    = 0
        self._return_level  = None
        self._dialogue      = DialogueBox(faction=FACTION_FLESHFORGED)
        self._tutorial      = None
        self._voice         = VoicePlayer()
        self._font_skip     = pygame.font.SysFont("monospace", 13)
        self._fade_alpha    = 255
        self._fade_surf     = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self._fade_surf.fill(BLACK)
        r, g, b = FLESHFORGED_BEATS[0][0]
        self._bg = [float(r), float(g), float(b)]

    # ------------------------------------------------------------------

    def on_enter(self, **kwargs):
        beat_start          = kwargs.get("beat_start", 0)
        self._return_level  = kwargs.get("return_level", None)
        self._beat_index    = beat_start
        r, g, b = FLESHFORGED_BEATS[beat_start][0]
        self._bg         = [float(r), float(g), float(b)]
        self._fade_alpha = 255
        self._tutorial   = None
        self._load_beat(beat_start)

    def _load_beat(self, index: int):
        _, speaker, data = FLESHFORGED_BEATS[index]
        if speaker == "__tutorial__":
            self._tutorial = TutorialMinigame(
                goal_type=data["type"],
                prompt=data["prompt"],
                faction=FACTION_FLESHFORGED,
            )
            self._dialogue.queue([])
            self._voice.stop()
        else:
            self._tutorial = None
            self._dialogue.queue([(speaker, data)])
            self._voice.play(FACTION_FLESHFORGED, index)

    def _bg_target(self):
        return FLESHFORGED_BEATS[self._beat_index][0]

    # ------------------------------------------------------------------

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._voice.stop()
                if self._return_level:
                    self.game.change_scene(SCENE_GAMEPLAY, level=self._return_level)
                else:
                    self.game.change_scene(SCENE_GAMEPLAY)
                return
            if self._tutorial is not None:
                self._tutorial.handle_event(event)
                return
            if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self._advance()

    def _advance(self):
        if self._tutorial is not None:
            return
        self._voice.stop()
        self._dialogue.advance()
        if self._dialogue.is_done():
            self._next_beat()

    def _next_beat(self):
        self._beat_index += 1
        if self._beat_index >= len(FLESHFORGED_BEATS):
            if self._return_level:
                self.game.change_scene(SCENE_GAMEPLAY, level=self._return_level)
            else:
                self.game.change_scene(SCENE_GAMEPLAY)
        else:
            self._load_beat(self._beat_index)

    # ------------------------------------------------------------------

    def update(self, dt):
        if self._tutorial is not None:
            self._tutorial.update()
            if self._tutorial.is_complete():
                self._tutorial = None
                self._next_beat()
        else:
            self._dialogue.update()

        if self._fade_alpha > 0:
            self._fade_alpha = max(0, self._fade_alpha - 5)

        tr, tg, tb = self._bg_target()
        spd = 0.07
        self._bg[0] += (tr - self._bg[0]) * spd
        self._bg[1] += (tg - self._bg[1]) * spd
        self._bg[2] += (tb - self._bg[2]) * spd

    # ------------------------------------------------------------------

    def draw(self, surface):
        surface.fill((int(self._bg[0]), int(self._bg[1]), int(self._bg[2])))

        if self._fade_alpha > 0:
            self._fade_surf.set_alpha(self._fade_alpha)
            surface.blit(self._fade_surf, (0, 0))

        # Progress bar
        progress = (self._beat_index + 1) / len(FLESHFORGED_BEATS)
        bar_w    = int(SCREEN_WIDTH * progress)
        pygame.draw.rect(surface, FLESHFORGED_COLOR, (0, 0, bar_w, 3))

        # Skip hint
        skip = self._font_skip.render("ESC — skip prologue", True, (65, 42, 22))
        surface.blit(skip, (SCREEN_WIDTH - skip.get_width() - 16, 10))

        if self._tutorial is not None:
            self._tutorial.draw(surface)
        else:
            self._dialogue.draw(surface)
