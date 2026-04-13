# =============================================================================
# scenes/fleshforged_prologue.py — Story beats for the Fleshforged path.
#
# Revised direction:
# - Sera's self-sacrifice is the only path to the protagonist's survival.
# - The writing is darker, more tragic, and more intimate.
# - The scene aims for high-stakes, grief-driven momentum without mimicking any
#   specific copyrighted prose style.
# =============================================================================

import pygame
from settings import *
from scenes.base_scene import BaseScene
from systems.dialogue import DialogueBox
from systems.tutorial_minigame import TutorialMinigame
from systems.voice_player import VoicePlayer


FLESHFORGED_BEATS = [
    ((18, 10, 5), "",
        "Duskholm crouched at the end of the rail line like something that had survived too long to die cleanly."),

    ((18, 10, 5), "",
        "You and Sera worked the east shaft because east-shaft crews came back with enough ore to eat, and sometimes enough to pretend tomorrow had shape."),

    ((18, 10, 5), "",
        "Her shoulder was plated in salvage steel. Your right lung hissed through an old pressure valve every winter morning. Love, in Duskholm, meant learning the sounds of each other's damage."),

    ((18, 10, 5), "Sera",
        "Good news. I stole a heat canister from the foreman's lockbox. Bad news: if he notices, we may have to become different people by dawn."),

    ((18, 10, 5), "__tutorial__",
        {"type": "move", "prompt": "Take the canister."}),

    ((18, 10, 5), "Sera",
        "There. Look at that. For one entire minute, we're rich."),

    ((18, 10, 5), "",
        "You laughed, and the sound startled both of you. In Duskholm, joy was always suspicious when it arrived on time."),

    ((10, 5, 2), "",
        "The shaft gave way at eleven past midday. No siren. No shouted warning. Just one clean instant where the world forgot it was supposed to hold."),

    ((10, 5, 2), "",
        "Then the dark came down with all its weight."),

    ((8, 4, 1), "",
        "When you woke, the stone had your legs. Dust packed your mouth. Something sharp had gone into your side and stayed there, moving when you breathed."),

    ((8, 4, 1), "Sera",
        "Stay with me. Look at me. If you close your eyes now, I swear I'll drag you back just so I can kill you myself."),

    ((10, 5, 2), "__tutorial__",
        {"type": "jump", "prompt": "Move before the shaft buries you both."}),

    ((8, 4, 1), "Sera",
        "Good. Again. Breathe ugly if you have to. Just breathe."),

    ((14, 7, 3), "",
        "Dr. Orven kept his surgery above the mine pumps, where the heat from the engines made the blood smell sweet and rotten at the same time."),

    ((14, 7, 3), "Dr. Orven",
        "Spine shattered. Lung punctured. Lower frame ruined. Without intervention, death is imminent."),

    ((12, 6, 2), "Dr. Orven",
        "You do not have the credit for a rebuild. He dies tonight unless I strip her implants, graft the usable metal, and cannibalize the rest for the cost of the operation."),

    ((12, 6, 2), "",
        "The room went still. Even the pumps seemed to listen."),

    ((10, 5, 2), "",
        "You tried to speak. What came out was blood."),

    ((10, 5, 2), "Sera",
        "No. Don't waste breath trying to save me from this."),

    ((10, 5, 2), "Sera",
        "Listen to me. You live. That is the whole of it. There is no second choice here. There is you, or there is a body for me to hold until it gets cold."),

    ((10, 5, 2), "",
        "She knelt beside the table and pressed her forehead to yours. The metal in her shoulder clicked softly as she shook."),

    ((10, 5, 2), "Sera",
        "You always thought survival was something ugly people did. So do it ugly. Do it bleeding. Do it without me. But do it."),

    ((10, 5, 2), "Sera",
        "Take what I bought you and climb so high this world chokes trying to name what you became."),

    ((8, 4, 1), "",
        "Orven's assistants held her down because she would not let herself tremble while you watched."),

    ((8, 4, 1), "",
        "The last thing you saw before the sedative took you was Sera turning her face toward you and smiling like she had already made peace with the theft of herself."),

    ((22, 12, 5), "",
        "You woke in a military clinic stitched together with her metal, her sacrifice bolted into your spine, your lungs, your gait. Every step belonged partly to the dead."),

    ((22, 12, 5), "__tutorial__",
        {"type": "attack", "prompt": "Test the frame she died to give you."}),

    ((22, 12, 5), "",
        "Her chair was gone. Her clothes were gone. Even her name had been cleared from the intake slate. The state had already begun the work of pretending she had always been material."),

    ((22, 12, 5), "",
        "A recruiter in ash-gray uniform waited beside your bed with the patience of a creditor."),

    ((22, 12, 5), "Recruiter",
        "Your reconstruction is complete. The military has assumed your outstanding debt, your maintenance, and your deployment rights."),

    ((22, 12, 5), "Recruiter",
        "At dawn, you will report for induction. The nation has invested heavily in your continued heartbeat."),

    ((22, 12, 5), "__tutorial__",
        {"type": "ability_fleshforged", "prompt": "Ignite the overdrive. Make her death cost the world something."}),

    ((22, 12, 5), "",
        "You stood on legs she purchased with her own body and felt the machinery answer. Grief did not leave you. It hardened. That would have to be enough."),
]


class FleshforgedPrologueScene(BaseScene):
    def __init__(self, game):
        super().__init__(game)
        self._beat_index = 0
        self._dialogue = DialogueBox(faction=FACTION_FLESHFORGED)
        self._tutorial = None
        self._voice = VoicePlayer()
        self._font_skip = pygame.font.SysFont("monospace", 13)
        self._fade_alpha = 255
        self._fade_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self._fade_surf.fill(BLACK)
        r, g, b = FLESHFORGED_BEATS[0][0]
        self._bg = [float(r), float(g), float(b)]

    def on_enter(self, **kwargs):
        self._beat_index = 0
        r, g, b = FLESHFORGED_BEATS[0][0]
        self._bg = [float(r), float(g), float(b)]
        self._fade_alpha = 255
        self._tutorial = None
        self._load_beat(0)

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

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._voice.stop()
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
            self.game.change_scene(SCENE_GAMEPLAY)
        else:
            self._load_beat(self._beat_index)

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

    def draw(self, surface):
        surface.fill((int(self._bg[0]), int(self._bg[1]), int(self._bg[2])))

        if self._fade_alpha > 0:
            self._fade_surf.set_alpha(self._fade_alpha)
            surface.blit(self._fade_surf, (0, 0))

        progress = (self._beat_index + 1) / len(FLESHFORGED_BEATS)
        bar_w = int(SCREEN_WIDTH * progress)
        pygame.draw.rect(surface, FLESHFORGED_COLOR, (0, 0, bar_w, 3))

        skip = self._font_skip.render("ESC — skip prologue", True, (65, 42, 22))
        surface.blit(skip, (SCREEN_WIDTH - skip.get_width() - 16, 10))

        if self._tutorial is not None:
            self._tutorial.draw(surface)
        else:
            self._dialogue.draw(surface)
