# =============================================================================
# main.py — Entry point. Run this file to start the game.
#   python main.py
# =============================================================================

import pygame
from core.game import Game


def main():
    pygame.init()           # Start all pygame subsystems (display, audio, fonts…)
    game = Game()
    game.run()
    pygame.quit()           # Clean shutdown


if __name__ == "__main__":
    main()
