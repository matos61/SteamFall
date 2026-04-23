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

# All 13 level keys in display order.
# Row 1: levels 1-5  (linear progression)
# Row 2: levels 6-10 (faction branches as two parallel nodes per tier, then 9 + 10)
_LEVEL_ORDER = [
    "level_1", "level_2", "level_3", "level_4", "level_5",
    "level_6_marked", "level_6_fleshforged",
    "level_7_marked", "level_7_fleshforged",
    "level_8_marked", "level_8_fleshforged",
    "level_9", "level_10",
]
_LEVEL_LABELS = {
    "level_1":             "I",
    "level_2":             "II",
    "level_3":             "III",
    "level_4":             "IV",
    "level_5":             "V",
    "level_6_marked":      "VI-M",
    "level_6_fleshforged": "VI-F",
    "level_7_marked":      "VII-M",
    "level_7_fleshforged": "VII-F",
    "level_8_marked":      "VIII-M",
    "level_8_fleshforged": "VIII-F",
    "level_9":             "IX",
    "level_10":            "X",
}

# Row groupings for the two-row layout
_ROW1 = ["level_1", "level_2", "level_3", "level_4", "level_5"]
# Row 2 is laid out as columns; each column holds a Marked/Fleshforged pair (or single node)
_ROW2_COLS = [
    ["level_6_marked",  "level_6_fleshforged"],
    ["level_7_marked",  "level_7_fleshforged"],
    ["level_8_marked",  "level_8_fleshforged"],
    ["level_9"],
    ["level_10"],
]


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

        # --- Room chain (two rows) ---
        visited    = self._game.save_data.get("visited_levels", [])
        room_w     = 72    # slightly narrower to fit two rows
        room_h     = 24
        room_gap   = 10
        row_gap    = 8     # vertical gap between row 1 and row 2

        # Row 1: levels 1–5
        total_w_r1 = len(_ROW1) * room_w + (len(_ROW1) - 1) * room_gap
        rx1        = panel_x + (panel_w - total_w_r1) // 2
        ry1        = panel_y + 44

        def _draw_room(lname, rect):
            if lname == current_level_name:
                fill = MARKED_COLOR
            elif lname in visited:
                fill = DARK_GRAY
            else:
                fill = (18, 18, 28)
            pygame.draw.rect(surface, fill, rect)
            pygame.draw.rect(surface, GRAY, rect, 1)
            lbl = font_room.render(_LEVEL_LABELS[lname], True, WHITE)
            surface.blit(lbl, (rect.centerx - lbl.get_width() // 2,
                               rect.centery - lbl.get_height() // 2))

        r1_rects = []
        for i, lname in enumerate(_ROW1):
            r = pygame.Rect(rx1 + i * (room_w + room_gap), ry1, room_w, room_h)
            _draw_room(lname, r)
            r1_rects.append(r)
            if i < len(_ROW1) - 1:
                pygame.draw.line(surface, GRAY,
                                 (r.right, r.centery),
                                 (r.right + room_gap, r.centery), 1)

        # Row 2: faction branches + levels 9 and 10
        # Each column has 1 or 2 stacked nodes; column width = room_w, col gap = room_gap
        # Faction pairs are stacked vertically; single nodes are vertically centred.
        col_w          = room_w + room_gap
        sub_h          = room_h          # height of each sub-node in faction column
        sub_gap        = 4               # gap between Marked and Fleshforged in same tier
        col_pair_h     = sub_h * 2 + sub_gap   # total height of a faction-pair column
        ry2_top        = ry1 + room_h + row_gap

        total_w_r2     = len(_ROW2_COLS) * room_w + (len(_ROW2_COLS) - 1) * room_gap
        rx2            = panel_x + (panel_w - total_w_r2) // 2

        # Remember centrepoints for inter-column connectors
        prev_col_right  = None
        prev_col_cy     = None

        for ci, col_levels in enumerate(_ROW2_COLS):
            col_x = rx2 + ci * (room_w + room_gap)

            if len(col_levels) == 2:
                # Faction pair: top = Marked variant, bottom = Fleshforged variant
                lname_a, lname_b = col_levels
                ra = pygame.Rect(col_x, ry2_top, room_w, sub_h)
                rb = pygame.Rect(col_x, ry2_top + sub_h + sub_gap, room_w, sub_h)
                _draw_room(lname_a, ra)
                _draw_room(lname_b, rb)
                # Vertical divider line between pair
                pygame.draw.line(surface, GRAY,
                                 (ra.centerx, ra.bottom),
                                 (rb.centerx, rb.top), 1)
                col_cy    = (ra.centery + rb.centery) // 2
                col_right = ra.right
            else:
                # Single node — vertically centred in the pair height
                lname = col_levels[0]
                top   = ry2_top + (col_pair_h - room_h) // 2
                r     = pygame.Rect(col_x, top, room_w, room_h)
                _draw_room(lname, r)
                col_cy    = r.centery
                col_right = r.right

            # Horizontal connector from previous column
            if prev_col_right is not None:
                # Draw line at the average y of the two centre-y values
                connector_y = (prev_col_cy + col_cy) // 2
                pygame.draw.line(surface, GRAY,
                                 (prev_col_right, connector_y),
                                 (col_x, connector_y), 1)

            prev_col_right = col_right + room_gap  # right edge + gap
            prev_col_cy    = col_cy

        # Connector from row-1 level_5 to row-2 first column (faction branches)
        if r1_rects:
            level5_rect = r1_rects[-1]
            # Vertical drop from level_5 bottom to row-2 top
            drop_x = rx2 + (room_w // 2)   # approximate x of first row-2 column
            pygame.draw.line(surface, GRAY,
                             (level5_rect.centerx, level5_rect.bottom),
                             (level5_rect.centerx, ry2_top), 1)

        # Bottom of the room chain
        ry_chain_bottom = ry2_top + col_pair_h

        # --- Tile layout of current room ---
        layout_margin = 12
        layout_y      = ry_chain_bottom + 16
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
