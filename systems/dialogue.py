# =============================================================================
# systems/dialogue.py — Scrolling dialogue box system.
#
# Usage:
#   box = DialogueBox()
#   box.queue([
#       ("Kael",   "You'll be something great. I see it."),
#       ("",       "He pressed the blade into your hand."),  # "" = narrator
#   ])
#   # Each frame:
#   box.update()
#   box.draw(screen)
#   # Check box.is_done() to know when all lines are finished.
#   # Call box.advance() on SPACE/ENTER keypress.
#
# Visual conventions:
#   • Named speaker  → WHITE text, faction-colored name badge
#   • "" (narrator)  → muted lavender-white, no badge, text starts at box top
# =============================================================================

import pygame
from settings import (SCREEN_WIDTH, SCREEN_HEIGHT, BLACK, WHITE, GRAY, GOLD,
                       MARKED_COLOR, FLESHFORGED_COLOR, TEXT_SCROLL_SPEED,
                       DIALOGUE_FONT_SIZE)

# Frames after text fully reveals before showing the advance prompt
_HINT_DELAY  = 22
# Frames per blink half-cycle for the advance cursor
_BLINK_CYCLE = 28
# Color for narrator lines (no speaker) — slightly muted, cooler white
_NARRATOR_COLOR = (195, 188, 215)


class DialogueBox:
    BOX_HEIGHT  = 160
    BOX_PADDING = 24
    BOX_MARGIN  = 30
    BOX_ALPHA   = 215

    def __init__(self, faction: str = ""):
        self.faction     = faction
        self._queue: list[tuple[str, str]] = []
        self._index      = 0
        self._char_pos   = 0.0
        self._done       = True
        self._reveal_timer = 0   # Counts up once text is fully shown
        self._blink_timer  = 0   # Drives the blinking advance cursor

        pygame.font.init()
        self.font_body    = pygame.font.SysFont("georgia",   DIALOGUE_FONT_SIZE)
        self.font_speaker = pygame.font.SysFont("georgia",   DIALOGUE_FONT_SIZE - 2,
                                                bold=True)
        self.font_hint    = pygame.font.SysFont("monospace", 13)

        self._accent = (MARKED_COLOR     if faction == "marked"   else
                        FLESHFORGED_COLOR if faction == "fleshforged" else
                        GOLD)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def queue(self, lines: list[tuple[str, str]]) -> None:
        self._queue        = lines
        self._index        = 0
        self._char_pos     = 0.0
        self._done         = False
        self._reveal_timer = 0
        self._blink_timer  = 0

    def advance(self) -> None:
        current_text = self._current_text()
        if self._char_pos < len(current_text):
            self._char_pos = len(current_text)   # Snap to full reveal
        else:
            self._next_line()

    def update(self) -> None:
        if self._done:
            return
        current_text = self._current_text()
        if self._char_pos < len(current_text):
            self._char_pos = min(self._char_pos + TEXT_SCROLL_SPEED,
                                 len(current_text))
            self._reveal_timer = 0
        else:
            # Text is fully revealed — tick hint delay and blink
            self._reveal_timer += 1
            if self._reveal_timer >= _HINT_DELAY:
                self._blink_timer += 1

    def is_done(self) -> bool:
        return self._done

    def is_fully_revealed(self) -> bool:
        return self._char_pos >= len(self._current_text())

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def draw(self, surface: pygame.Surface) -> None:
        if self._done:
            return

        box_x = self.BOX_MARGIN
        box_y = SCREEN_HEIGHT - self.BOX_HEIGHT - self.BOX_MARGIN
        box_w = SCREEN_WIDTH  - self.BOX_MARGIN * 2
        box_h = self.BOX_HEIGHT

        # --- Background ---
        bg = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        bg.fill((8, 5, 18, self.BOX_ALPHA))
        surface.blit(bg, (box_x, box_y))

        # --- Border — pulses brighter once text is fully revealed ---
        if self._reveal_timer >= _HINT_DELAY:
            pulse = abs((_BLINK_CYCLE - (self._blink_timer % (_BLINK_CYCLE * 2)))
                        / _BLINK_CYCLE)   # 0.0 → 1.0 → 0.0
            r = int(self._accent[0] * (0.65 + 0.35 * pulse))
            g = int(self._accent[1] * (0.65 + 0.35 * pulse))
            b = int(self._accent[2] * (0.65 + 0.35 * pulse))
            border_color = (r, g, b)
        else:
            border_color = self._accent
        pygame.draw.rect(surface, border_color, (box_x, box_y, box_w, box_h), 2)

        p        = self.BOX_PADDING
        speaker  = self._queue[self._index][0]
        is_narr  = (speaker == "")

        # --- Speaker badge (characters only) ---
        if not is_narr:
            label = self.font_speaker.render(speaker.upper(), True, self._accent)
            surface.blit(label, (box_x + p, box_y + p - 4))

        text_y_offset = p if is_narr else (p + 28)
        text_color    = _NARRATOR_COLOR if is_narr else WHITE

        # --- Body text (only revealed characters) ---
        visible = self._current_text()[:int(self._char_pos)]
        wrapped = self._wrap_text(visible, box_w - p * 2)
        for i, line in enumerate(wrapped):
            rendered = self.font_body.render(line, True, text_color)
            surface.blit(rendered, (box_x + p, box_y + text_y_offset + i * 30))

        # --- Advance cursor — appears after hint delay, blinks ---
        if self._reveal_timer >= _HINT_DELAY:
            # Blink: visible for half the cycle
            visible_cursor = (self._blink_timer % (_BLINK_CYCLE * 2)) < _BLINK_CYCLE
            if visible_cursor:
                cursor = self.font_hint.render("▶", True, self._accent)
                surface.blit(cursor,
                    (box_x + box_w - cursor.get_width() - p,
                     box_y + box_h - cursor.get_height() - 10))

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _current_text(self) -> str:
        if self._done or self._index >= len(self._queue):
            return ""
        return self._queue[self._index][1]

    def _next_line(self) -> None:
        self._index       += 1
        self._char_pos     = 0.0
        self._reveal_timer = 0
        self._blink_timer  = 0
        if self._index >= len(self._queue):
            self._done = True

    def _wrap_text(self, text: str, max_width: int) -> list[str]:
        words   = text.split(" ")
        lines   = []
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
