# =============================================================================
# systems/minimap.py — In-game map overlay.
#
# Shows which levels have been visited (room chain at the top) and renders
# the current room's tile layout at a small scale below it.
# Toggle with M key in gameplay.
# =============================================================================

import pygame
from settings import (SCREEN_WIDTH, SCREEN_HEIGHT, TILE_COLOR, TILE_SIZE,
                      MARKED_COLOR, DARK_GRAY, MAP_TILE_SIZE, MAP_ALPHA,
                      WHITE, GRAY, GOLD)

_LEVEL_ORDER = ["level_1", "level_2", "level_3", "level_4", "level_5"]
_LEVEL_LABELS = {
    "level_1": "I",
    "level_2": "II",
    "level_3": "III",
    "level_4": "IV",
    "level_5": "V",
}


class MiniMap:
    def __init__(self, game):
        self._game = game

    # ------------------------------------------------------------------

    def mark_visited(self, level_name: str) -> None:
        visited = self._game.save_data.setdefault("visited_levels", [])
        if level_name not in visited:
            visited.append(level_name)
            self._game.save_to_disk()

    # ------------------------------------------------------------------

    def draw_overlay(self, surface: pygame.Surface,
                     current_level_name: str,
                     tilemap) -> None:
        panel_w = int(SCREEN_WIDTH * 0.70)
        panel_h = int(SCREEN_HEIGHT * 0.70)
        panel_x = (SCREEN_WIDTH  - panel_w) // 2
        panel_y = (SCREEN_HEIGHT - panel_h) // 2

        # Semi-transparent background panel
        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((0, 0, 0, MAP_ALPHA))
        surface.blit(panel, (panel_x, panel_y))
        pygame.draw.rect(surface, GRAY, (panel_x, panel_y, panel_w, panel_h), 1)

        font_title = pygame.font.SysFont("georgia",   22, bold=True)
        font_room  = pygame.font.SysFont("monospace", 13)
        font_hint  = pygame.font.SysFont("monospace", 13)

        # Title
        title = font_title.render("MAP", True, WHITE)
        surface.blit(title, (panel_x + 14, panel_y + 10))

        # --- Room chain ---
        visited = self._game.save_data.get("visited_levels", [])
        room_w, room_h = 80, 28
        room_gap       = 18
        total_w        = len(_LEVEL_ORDER) * room_w + (len(_LEVEL_ORDER) - 1) * room_gap
        rx             = panel_x + (panel_w - total_w) // 2
        ry             = panel_y + 44

        for i, lname in enumerate(_LEVEL_ORDER):
            r = pygame.Rect(rx + i * (room_w + room_gap), ry, room_w, room_h)

            if lname == current_level_name:
                fill = MARKED_COLOR
            elif lname in visited:
                fill = DARK_GRAY
            else:
                fill = (18, 18, 28)

            pygame.draw.rect(surface, fill, r)
            pygame.draw.rect(surface, GRAY, r, 1)

            lbl = font_room.render(_LEVEL_LABELS[lname], True, WHITE)
            surface.blit(lbl, (r.centerx - lbl.get_width() // 2,
                               r.centery - lbl.get_height() // 2))

            # Connecting line between rooms
            if i < len(_LEVEL_ORDER) - 1:
                lx = r.right
                ly = r.centery
                pygame.draw.line(surface, GRAY,
                                 (lx, ly), (lx + room_gap, ly), 1)

        # --- Tile layout of current room ---
        layout_margin = 12
        layout_y      = ry + room_h + 20
        available_w   = panel_w - layout_margin * 2
        available_h   = panel_h - (layout_y - panel_y) - 28

        # Scale to fit in available space — build grid dimensions once
        level_grid = _get_level_data(tilemap)
        cols       = max(len(row) for row in level_grid) if level_grid else 0
        rows       = len(level_grid)

        if cols > 0 and rows > 0:
            ts = min(MAP_TILE_SIZE,
                     available_w // cols,
                     available_h // rows)
            ts = max(1, ts)

            map_pixel_w = cols * ts
            map_pixel_h = rows * ts
            ox = panel_x + layout_margin + (available_w - map_pixel_w) // 2
            oy = layout_y

            for tile in tilemap.tiles:
                tx = (tile.x // TILE_SIZE) * ts + ox
                ty = (tile.y // TILE_SIZE) * ts + oy
                pygame.draw.rect(surface, TILE_COLOR, (tx, ty, ts, ts))

            # Enemy spawns — small red dots
            for (ex, ey) in (tilemap.enemy_spawns + tilemap.crawler_spawns
                             + tilemap.shield_guard_spawns + tilemap.ranged_spawns
                             + tilemap.jumper_spawns):
                dx = int(ex / TILE_SIZE) * ts + ox + ts // 2
                dy = int(ey / TILE_SIZE) * ts + oy + ts // 2
                pygame.draw.circle(surface, (200, 40, 40), (dx, dy), max(1, ts // 2))

            # Boss spawn — orange dot
            if getattr(tilemap, "boss_spawn", None):
                bx_t = int(tilemap.boss_spawn[0] / TILE_SIZE) * ts + ox + ts // 2
                by_t = int(tilemap.boss_spawn[1] / TILE_SIZE) * ts + oy + ts // 2
                pygame.draw.circle(surface, (220, 100, 20), (bx_t, by_t), max(2, ts))

            # Player spawn — green dot
            px_t = int(tilemap.player_spawn[0] / TILE_SIZE) * ts + ox + ts // 2
            py_t = int(tilemap.player_spawn[1] / TILE_SIZE) * ts + oy + ts // 2
            pygame.draw.circle(surface, (60, 200, 80), (px_t, py_t), max(2, ts))

            # Checkpoint positions — yellow diamond
            for cp in tilemap.checkpoints:
                cx_t = (cp.rect.centerx // TILE_SIZE) * ts + ox + ts // 2
                cy_t = (cp.rect.top     // TILE_SIZE) * ts + oy + ts // 2
                size = max(2, ts)
                pts  = [(cx_t,        cy_t - size),
                        (cx_t + size, cy_t),
                        (cx_t,        cy_t + size),
                        (cx_t - size, cy_t)]
                pygame.draw.polygon(surface, GOLD, pts)

        # Hint footer
        hint = font_hint.render("M — Close Map", True, (70, 70, 70))
        surface.blit(hint,
                     (panel_x + panel_w - hint.get_width() - 10,
                      panel_y + panel_h - hint.get_height() - 6))


def _get_level_data(tilemap) -> list:
    """Infer row/col count from existing tile rects."""
    if not tilemap or not tilemap.tiles:
        return []
    max_row = max(t.y // TILE_SIZE for t in tilemap.tiles) + 1
    max_col = max(t.x // TILE_SIZE for t in tilemap.tiles) + 1
    # Return a dummy 2-D list of the right dimensions (values unused)
    return [[' '] * max_col for _ in range(max_row)]
