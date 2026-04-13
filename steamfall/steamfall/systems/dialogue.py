# =============================================================================
# systems/dialogue.py — Scrolling dialogue box system.
#
# Usage:
#   box = DialogueBox()
#   box.queue([
#       ("Kael",   "You'll be something great. I see it."),
#       ("",       "He pressed the blade into your hand."),
#   ])
#   # Each frame:
#   box.update()
#   box.draw(screen)
#   # Check box.is_done() to know when all lines are finished.
#   # Call box.advance() on SPACE/ENTER keypress.
# =============================================================================

import pygame
from settings import (SCREEN_WIDTH, SCREEN_HEIGHT, BLACK, WHITE, GRAY, GOLD,
                       MARKED_COLOR, FLESHFORGED_COLOR, TEXT_SCROLL_SPEED,
                       DIALOGUE_FONT_SIZE)


class DialogueBox:
    BOX_HEIGHT  = 160
    BOX_PADDING = 24
    BOX_MARGIN  = 30           # Gap from bottom of screen
    BOX_ALPHA   = 210          # 0=transparent, 255=solid

    def __init__(self, faction: str = ""):
        self.faction     = faction
        self._queue: list[tuple[str, str]] = []
        self._index      = 0           # Which line we're on
        self._char_pos   = 0.0         # How many characters are revealed (float)
        self._done       = True

        # Fonts
        pygame.font.init()
        self.font_body    = pygame.font.SysFont("georgia",    DIALOGUE_FONT_SIZE)
        self.font_speaker = pygame.font.SysFont("georgia",    DIALOGUE_FONT_SIZE - 2, bold=True)
        self.font_hint    = pygame.font.SysFont("monospace",  14)

        # Accent color based on faction
        self._accent = (MARKED_COLOR if faction == "marked"
                        else FLESHFORGED_COLOR if faction == "fleshforged"
                        else GOLD)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def queue(self, lines: list[tuple[str, str]]) -> None:
        """
        Load a list of (speaker_name, text) tuples.
        Pass "" as speaker_name for narration with no label.
        """
        self._queue  = lines
        self._index  = 0
        self._char_pos = 0.0
        self._done   = False

    def advance(self) -> None:
        """
        Called on SPACE or ENTER press.
        If text is still scrolling → jump to full reveal.
        If text is fully shown → move to next line.
        """
        current_text = self._current_text()
        if self._char_pos < len(current_text):
            # Snap to end of current line
            self._char_pos = len(current_text)
        else:
            self._next_line()

    def update(self) -> None:
        """Call every frame to advance the scroll animation."""
        if self._done:
            return
        current_text = self._current_text()
        if self._char_pos < len(current_text):
            self._char_pos = min(self._char_pos + TEXT_SCROLL_SPEED,
                                 len(current_text))

    def is_done(self) -> bool:
        return self._done

    def is_fully_revealed(self) -> bool:
        """True when the current line is fully visible (no longer scrolling)."""
        return self._char_pos >= len(self._current_text())

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def draw(self, surface: pygame.Surface) -> None:
        if self._done:
            return

        box_x = DialogueBox.BOX_MARGIN
        box_y = SCREEN_HEIGHT - DialogueBox.BOX_HEIGHT - DialogueBox.BOX_MARGIN
        box_w = SCREEN_WIDTH  - DialogueBox.BOX_MARGIN * 2
        box_h = DialogueBox.BOX_HEIGHT

        # --- Background ---
        bg = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        bg.fill((8, 5, 18, DialogueBox.BOX_ALPHA))
        surface.blit(bg, (box_x, box_y))

        # --- Border ---
        pygame.draw.rect(surface, self._accent, (box_x, box_y, box_w, box_h), 2)

        p = DialogueBox.BOX_PADDING
        speaker, _ = self._queue[self._index]

        # --- Speaker label (if any) ---
        if speaker:
            label = self.font_speaker.render(speaker.upper(), True, self._accent)
            surface.blit(label, (box_x + p, box_y + p - 4))

        text_y_offset = (p + 28) if speaker else p

        # --- Body text (only revealed characters) ---
        visible_text = self._current_text()[:int(self._char_pos)]
        wrapped      = self._wrap_text(visible_text, box_w - p * 2)
        for i, line in enumerate(wrapped):
            rendered = self.font_body.render(line, True, WHITE)
            surface.blit(rendered, (box_x + p, box_y + text_y_offset + i * 30))

        # --- "Press SPACE" hint when fully revealed ---
        if self.is_fully_revealed():
            hint_text = ("SPACE — continue"
                         if self._index < len(self._queue) - 1
                         else "SPACE — dismiss")
            hint = self.font_hint.render(hint_text, True, GRAY)
            surface.blit(hint,
                (box_x + box_w - hint.get_width() - p,
                 box_y + box_h - hint.get_height() - 10))

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _current_text(self) -> str:
        if self._done or self._index >= len(self._queue):
            return ""
        return self._queue[self._index][1]

    def _next_line(self) -> None:
        self._index += 1
        self._char_pos = 0.0
        if self._index >= len(self._queue):
            self._done = True

    def _wrap_text(self, text: str, max_width: int) -> list[str]:
        """Break text into lines that fit within max_width pixels."""
        words  = text.split(" ")
        lines  = []
        current = ""
        for word in words:
            test = (current + " " + word).strip()
            if self.font_body.size(test)[0] <= max_width:
                current = test
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines
