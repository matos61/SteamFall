# steamfall/scenes/cutscene_scene.py
from steamfall.core.scene import Scene
from steamfall.engine.input import get_input
import pygame

class CutsceneScene(Scene):
    def __init__(self, app, lines):
        super().__init__(app)
        self.lines = lines
        self.index = 0
        self.font = pygame.font.SysFont("georgia", 24)

    def update(self, dt):
        keys = get_input()
        if keys.get("advance"):
            self.index += 1
            if self.index >= len(self.lines):
                self.app.change_scene("MenuScene")

    def draw(self, surface):
        surface.fill((10, 10, 10))
        if self.index < len(self.lines):
            text = self.font.render(self.lines[self.index], True, (230, 230, 230))
            surface.blit(text, (60, 60))
