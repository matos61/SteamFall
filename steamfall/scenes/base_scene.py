# =============================================================================
# scenes/base_scene.py — Abstract base that every scene inherits from.
#
# Think of a "scene" like a screen in the game:
#   Main Menu, Faction Select, Prologue, Gameplay, Pause, Game Over, etc.
#
# Every scene must implement three methods:
#   handle_event(event) — respond to keyboard / mouse / window events
#   update(dt)          — advance logic by one frame
#   draw(surface)       — render everything to the screen surface
# =============================================================================


class BaseScene:
    def __init__(self, game):
        # Every scene gets a reference to the Game manager so it can
        # call game.change_scene() and read game.player_faction, etc.
        self.game = game

    def on_enter(self, **kwargs) -> None:
        """
        Called once when this scene becomes active.
        Override this to reset state (e.g. restart music, reset timers).
        kwargs lets the previous scene pass data in via change_scene().
        """
        pass

    # --- These three MUST be overridden in every subclass ---

    def handle_event(self, event) -> None:
        raise NotImplementedError(f"{type(self).__name__} must implement handle_event()")

    def update(self, dt: int) -> None:
        raise NotImplementedError(f"{type(self).__name__} must implement update()")

    def draw(self, surface) -> None:
        raise NotImplementedError(f"{type(self).__name__} must implement draw()")
