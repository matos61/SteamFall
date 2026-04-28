# =============================================================================
# core/game.py — Central game manager.
#
# Responsibilities:
#   • Creates the window and clock
#   • Owns a dictionary of all scenes
#   • Runs the main loop: events → update → draw
#   • change_scene() is the only way scenes talk to the manager
#
# Scenes never import each other — they only call game.change_scene().
# This keeps dependencies clean and avoids circular imports.
# =============================================================================

import json
import pathlib
import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TITLE, BLACK, SCENE_MAIN_MENU, SAVE_FILE
from systems.audio import audio as _audio_singleton


class Game:
    def __init__(self):
        self.screen  = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock   = pygame.time.Clock()
        self.running = True

        # --- Audio ---
        self.audio = _audio_singleton   # AudioManager singleton; no-op when assets absent

        # --- Shared game state (read by any scene) ---
        self.player_faction = None   # Set in FactionSelectScene
        self.save_data      = {}     # Will hold checkpoints, inventory, etc.
        self.load_from_disk()        # Restore previous run's save if present

        # Build all scenes now so they're ready to receive on_enter() calls.
        # We do the imports inside the method to prevent circular-import issues
        # at module load time.
        self._scenes       = {}
        self._build_scenes()

        # Start on the main menu
        self.current_scene = self._scenes[SCENE_MAIN_MENU]
        self.current_scene.on_enter()

    # ------------------------------------------------------------------

    def _build_scenes(self):
        # Local imports so each scene file can do "from settings import …"
        # without accidentally importing game.py back at the top level.
        from scenes.main_menu            import MainMenuScene
        from scenes.faction_select       import FactionSelectScene
        from scenes.marked_prologue      import MarkedPrologueScene
        from scenes.fleshforged_prologue import FleshforgedPrologueScene
        from scenes.gameplay             import GameplayScene
        from scenes.marked_ending        import MarkedEndingScene
        from scenes.fleshforged_ending   import FleshforgedEndingScene
        from scenes.settings             import SettingsScene

        from settings import (SCENE_FACTION_SELECT, SCENE_MARKED_PROLOGUE,
                               SCENE_FLESHFORGED_PROLOGUE, SCENE_GAMEPLAY,
                               SCENE_MARKED_ENDING, SCENE_FLESHFORGED_ENDING,
                               SCENE_SETTINGS)

        self._scenes = {
            SCENE_MAIN_MENU:             MainMenuScene(self),
            SCENE_FACTION_SELECT:        FactionSelectScene(self),
            SCENE_MARKED_PROLOGUE:       MarkedPrologueScene(self),
            SCENE_FLESHFORGED_PROLOGUE:  FleshforgedPrologueScene(self),
            SCENE_GAMEPLAY:              GameplayScene(self),
            SCENE_MARKED_ENDING:         MarkedEndingScene(self),
            SCENE_FLESHFORGED_ENDING:    FleshforgedEndingScene(self),
            SCENE_SETTINGS:              SettingsScene(self),
        }

    # ------------------------------------------------------------------

    def save_to_disk(self) -> None:
        pathlib.Path(SAVE_FILE).write_text(json.dumps(self.save_data, indent=2))

    def load_from_disk(self) -> None:
        p = pathlib.Path(SAVE_FILE)
        if p.exists():
            try:
                self.save_data = json.loads(p.read_text())
            except (json.JSONDecodeError, OSError):
                self.save_data = {}

    def clear_save(self) -> None:
        self.save_data = {}
        self.save_to_disk()

    # ------------------------------------------------------------------

    def change_scene(self, scene_name: str, **kwargs) -> None:
        """
        Switch the active scene.
        kwargs are forwarded to the new scene's on_enter() so you can pass
        information (e.g. which level to load) without global state.
        """
        if scene_name not in self._scenes:
            raise ValueError(f"Unknown scene '{scene_name}'. "
                             f"Available: {list(self._scenes.keys())}")
        self.current_scene = self._scenes[scene_name]
        self.current_scene.on_enter(**kwargs)

    # ------------------------------------------------------------------

    def run(self) -> None:
        """Main game loop — runs until the window is closed."""
        while self.running:

            # dt = milliseconds since last frame (we pass it for future
            # use; currently most logic runs per-frame, not per-second)
            dt = self.clock.tick(FPS)

            # 1. Collect all events this frame
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False
                self.current_scene.handle_event(event)

            # 2. Update game logic
            self.current_scene.update(dt)

            # 3. Render
            self.screen.fill(BLACK)
            self.current_scene.draw(self.screen)
            pygame.display.flip()
