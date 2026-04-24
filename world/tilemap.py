# =============================================================================
# world/tilemap.py — Tile-based level loading and rendering.
#
# Level format (list of strings):
#   '#' = solid tile (ground / wall)
#   ' ' = empty air
#   'P' = player spawn point
#   'E' = standard enemy spawn point
#   'c' = crawler enemy spawn point
#   'C' = checkpoint (glowing pillar save point)
#   'B' = boss spawn point
#   'G' = ShieldGuard spawn point
#   'R' = Ranged enemy spawn point
#   'J' = Jumper enemy spawn point
#   'X' = Architect (final boss) spawn point
#   's' = spike hazard tile (non-solid; player takes damage on contact)
#   '~' = crumble platform (solid until stood on; falls after CRUMBLE_STAND_FRAMES)
#   'N' = NPC spawn point
#   'L' = collectible lore item spawn point
#
# When you have real tile sprites, replace the pygame.draw calls in
# draw_tile() with surface.blit(tile_image, screen_rect).
# =============================================================================

import pygame
from settings import TILE_SIZE, TILE_COLOR, TILE_EDGE_COLOR, CRUMBLE_COLOR, CRUMBLE_WARNING_COLOR


# ---------------------------------------------------------------------------
# Level data — edit these strings to redesign the world.
# Each string = one row of tiles, top to bottom.
# Width is the longest string; shorter rows are padded with spaces.
# ---------------------------------------------------------------------------
LEVEL_1 = [
    # Row 0-2: open sky (camera headroom)
    "                                                                        ",
    "                                                                        ",
    "                                                                        ",
    # Row 3-4: high platforms
    "                                  ###                                   ",
    "                                                                        ",
    # Row 5-6: mid-high platforms
    "                    ###                          ###                    ",
    "                                                                        ",
    # Row 7-8: mid platforms (enemy on one)
    "         ###                   E                         ###            ",
    "                                                                        ",
    # Row 9-10: lower platforms — crawler on the right one, checkpoint mid-level
    "    ###              ###          C             ###                     ",
    "                                                       c                ",
    # Row 11: ground-level entities — E=enemy  P=player  c=crawler
    "  E                       E         P                 E      c          ",
    # Row 12-13: solid ground
    "########################################################################",
    "########################################################################",
    # Row 14-21: underground / sub-floor filler to fill 720px screen
    "#                                                                      #",
    "#                                                                      #",
    "#                                                                      #",
    "#                                                                      #",
    "#                                                                      #",
    "#                                                                      #",
    "#                                                                      #",
    "########################################################################",
]

# ---------------------------------------------------------------------------
# LEVEL_2 — Second room, reached from the right edge of LEVEL_1.
# Different platform layout, more crawlers, two checkpoints.
# ---------------------------------------------------------------------------
LEVEL_2 = [
    # Row 0-2: sky
    "                                                                        ",
    "                                                                        ",
    "                                                                        ",
    # Row 3: high platform with enemy
    "          ###          E                    ###                         ",
    "                                                                        ",
    # Row 5-6: staggered mid platforms
    "   ###                       ###                         ###            ",
    "                                                                        ",
    # Row 7: checkpoint on left, crawler in middle
    "C         ###            c              ###                E            ",
    "                                                                        ",
    # Row 9: lower section — tighter gaps
    "  ###                ###                    ###              ###        ",
    "                                                                        ",
    # Row 11: ground entities P=player spawn (comes from left)
    "P  L  E          c               E            c      L    E             ",
    # Row 12-13: solid floor
    "########################################################################",
    "########################################################################",
    # Row 14-21: sub-floor
    "#                                                                      #",
    "#                                                                      #",
    "#          C                                                           #",
    "#                                                                      #",
    "#                                                                      #",
    "#                                                                      #",
    "#                                                                      #",
    "########################################################################",
]


LEVEL_3 = [
    "                                                                 ",
    "                                                                 ",
    "        ###              ###                     ###             ",
    "                E                   E                     c      ",
    "  ###                          #########                         ",
    "                                                                 ",
    "     E               ###                  E                      ",
    "###########                                         ######       ",
    "                 C               ###           N                 ",
    "#################   s   s   s               E              P     ",
    "#################################################################",
    "#################################################################",
]

LEVEL_4 = [
    "                     #                              ",
    "                                                    ",
    "              ###           ###                     ",
    "    c                                    c          ",
    "         ###                   ###                  ",
    "  E                  c                        E     ",
    "      #######              #######                  ",
    "          L                          L              ",
    "         E         C                 E              ",
    "  ~~~~~~~~~~~~~~     ################               ",
    "                                          P         ",
    "####################################################",
    "####################################################",
]

LEVEL_5 = [
    "                                                     ",
    "                                                     ",
    "  ###                                          ###   ",
    "                                L                    ",
    "                                                     ",
    "     N     C                                         ",
    "   P    ########                      ########       ",
    "                                                     ",
    "                        B                            ",
    "#####################################################",
    "#####################################################",
]

# ---------------------------------------------------------------------------
# LEVEL_6 — Faction branching begins here (levels 6-8 have two variants).
# ---------------------------------------------------------------------------

# LEVEL_6_MARKED — "The Ink Labyrinth"
# Purple-toned labyrinth; introduces ShieldGuards among crawlers.
LEVEL_6_MARKED = [
    "                                                                 ",
    "                                                                 ",
    "      ###          G           ###                               ",
    "                                          ###                    ",
    "  ###                   ###                          ###         ",
    "            c                      c                             ",
    "      G          #######                   G                     ",
    "###########                                         ######       ",
    "                 C               ###                             ",
    "#################                           c              P     ",
    "#################################################################",
    "#################################################################",
]

# LEVEL_6_FLESHFORGED — "The Steam Tunnels"
# Industrial corridors; Ranged enemies in tight passage chokepoints.
LEVEL_6_FLESHFORGED = [
    "                                                                 ",
    "                                                                 ",
    "   ######                R          ######                       ",
    "                                                       ###       ",
    "  ###       ######               ######                          ",
    "              R                                  R               ",
    "     ###                  ###                         ###        ",
    "###########                                         ######       ",
    "                 C               ###                             ",
    "#################                           R              P     ",
    "#################################################################",
    "#################################################################",
]

# ---------------------------------------------------------------------------
# LEVEL_7 — Taller, more vertical; Jumpers feature prominently.
# ---------------------------------------------------------------------------

# LEVEL_7_MARKED — "The Rune Vaults"
# Tall vertical ascent with rune-inscribed platforms; crawlers and Jumpers.
LEVEL_7_MARKED = [
    "                                                                 ",
    "                  ###                  J                        ",
    "   J                                          ###                ",
    "         ###                    ###                              ",
    "                   J                                  ###        ",
    "   ###                    ###              J                     ",
    "          ###                                    ###             ",
    "  c                  J          c                                ",
    "      ########                       ########                    ",
    "                 C                                               ",
    "   ################          ###           c              P      ",
    "#################################################################",
    "#################################################################",
]

# LEVEL_7_FLESHFORGED — "The Engine Room"
# Vertical industrial shafts; Jumpers leap between machinery platforms.
LEVEL_7_FLESHFORGED = [
    "                                                                 ",
    "                  ###                  J                        ",
    "   J                                          ###                ",
    "         ###                    ###                              ",
    "                   J                                  ###        ",
    "   ###                    ###              J                     ",
    "          ###                                    ###             ",
    "  R                  J          R                                ",
    "      ########                       ########                    ",
    "                 C                                               ",
    "   ################          ###           R              P      ",
    "#################################################################",
    "#################################################################",
]

# ---------------------------------------------------------------------------
# LEVEL_8 — Hardest faction level; all enemy types, boss at the end.
# ---------------------------------------------------------------------------

# LEVEL_8_MARKED — "The Sanctum Approach"
# Final Marked gauntlet mixing all enemy types; boss guards the gate.
LEVEL_8_MARKED = [
    "                                                                 ",
    "                                                                 ",
    "   ###         G              J           ###                    ",
    "                                                   ###           ",
    "          ###            ###                    c                ",
    "  G                                   G                    J     ",
    "      #########              #########                           ",
    "  c                 ###                     c                    ",
    "          ###                    ###                             ",
    "   ################   C                          P               ",
    "                                      B                         ",
    "#################################################################",
    "#################################################################",
]

# LEVEL_8_FLESHFORGED — "The Forge Gate"
# Final Fleshforged gauntlet; Ranged and ShieldGuards block the way.
LEVEL_8_FLESHFORGED = [
    "                                                                 ",
    "                                                                 ",
    "   ###         R              J           ###                    ",
    "                                                   ###           ",
    "          ###            ###                    G                ",
    "  R                                   R                    J     ",
    "      #########              #########                           ",
    "  G                 ###                     G                    ",
    "          ###                    ###                             ",
    "   ################   C                          P               ",
    "                                      B                         ",
    "#################################################################",
    "#################################################################",
]

# ---------------------------------------------------------------------------
# LEVEL_9 — "The Convergence" (shared path, all enemy types).
# ---------------------------------------------------------------------------
LEVEL_9 = [
    "                                                                 ",
    "                                                                 ",
    "   ###              J           G           ###                  ",
    "                                                    ###          ",
    "          ###                         ###                        ",
    "  c                  G                         c          R      ",
    "      #########                  #########                       ",
    "                  J      ###           G                         ",
    "   ###                                         J          ###    ",
    "          C         L          ###                L              ",
    "   ################                         c              P     ",
    "#################################################################",
    "#################################################################",
]

# ---------------------------------------------------------------------------
# LEVEL_10 — "The Final Approach" (Architect final boss arena).
# Sparse enemies early, then a wide open arena at the end for the Architect.
# 'X' marks the Architect spawn (replaces the generic 'B' Warden tile).
# ---------------------------------------------------------------------------
LEVEL_10 = [
    "                                                                 ",
    "                                                                 ",
    "   ###                                              ###          ",
    "                    G                                            ",
    "          ###                    ###                             ",
    "                                          J                      ",
    "      #########                                  #########       ",
    "  G                   ###                                        ",
    "          ###                    ###         G                   ",
    "   ################                                    P         ",
    "                                             X                   ",
    "#################################################################",
    "#################################################################",
]


class TileMap:
    def __init__(self, level_data: list, level_name: str = "level_1"):
        self.level_name  = level_name
        self.tiles: list[pygame.Rect] = []   # Solid collision rects
        self.player_spawn = (100, 100)        # Default; overwritten if 'P' found
        self.enemy_spawns: list[tuple]        = []
        self.crawler_spawns: list[tuple]      = []
        self.checkpoints: list                = []
        self.boss_spawn: tuple | None         = None
        self.shield_guard_spawns: list[tuple] = []
        self.ranged_spawns: list[tuple]       = []
        self.jumper_spawns: list[tuple]       = []
        self.architect_spawn: tuple | None    = None
        self.ability_orb_spawns: list[tuple]  = []
        self.spike_tiles: list                = []   # Non-solid; deal damage on contact
        self.crumble_tiles: list              = []   # Solid until stood on; fall and respawn
        self.npc_spawns: list[tuple]          = []   # (x, y) feet positions for NPCs
        self.lore_spawns: list[tuple]         = []   # (x, y) centre positions for lore items

        self._parse(level_data)

        # World pixel dimensions
        max_cols    = max(len(row) for row in level_data)
        self.width  = max_cols        * TILE_SIZE
        self.height = len(level_data) * TILE_SIZE

    # ------------------------------------------------------------------

    def _parse(self, level_data: list):
        from systems.checkpoint import Checkpoint

        for row_idx, row in enumerate(level_data):
            for col_idx, char in enumerate(row):
                x = col_idx * TILE_SIZE
                y = row_idx * TILE_SIZE

                if char == '#':
                    self.tiles.append(pygame.Rect(x, y, TILE_SIZE, TILE_SIZE))

                elif char == 'P':
                    self.player_spawn = (x + TILE_SIZE // 2, y - 64)

                elif char == 'E':
                    self.enemy_spawns.append((x + TILE_SIZE // 2, y - 64))

                elif char == 'c':
                    # Crawler spawns with feet on the tile floor
                    self.crawler_spawns.append((x, y - 22))

                elif char == 'C':
                    self.checkpoints.append(
                        Checkpoint(x, y, level=self.level_name))

                elif char == 'B':
                    self.boss_spawn = (x + TILE_SIZE // 2, y - 72)

                elif char == 'G':
                    self.shield_guard_spawns.append((x + TILE_SIZE // 2, y - 64))

                elif char == 'R':
                    self.ranged_spawns.append((x + TILE_SIZE // 2, y - 64))

                elif char == 'J':
                    self.jumper_spawns.append((x + TILE_SIZE // 2, y - 64))

                elif char == 'X':
                    # Architect (final boss) spawn; feet land 80 px above tile top
                    self.architect_spawn = (x + TILE_SIZE // 2, y - 80)

                elif char == 'A':
                    self.ability_orb_spawns.append((x + TILE_SIZE // 2, y - 18))

                elif char == 's':
                    # Spike tile — NOT solid; player takes damage on overlap
                    self.spike_tiles.append(pygame.Rect(x, y, TILE_SIZE, TILE_SIZE))

                elif char == '~':
                    # Crumble tile — initially solid; falls after player stands on it
                    rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
                    self.tiles.append(rect)
                    self.crumble_tiles.append(
                        {'rect': rect, 'timer': 0, 'state': 'solid'})

                elif char == 'N':
                    # NPC spawn — feet at bottom of tile
                    self.npc_spawns.append((x + TILE_SIZE // 2, y + TILE_SIZE))

                elif char == 'L':
                    # Lore item spawn — centred on tile
                    self.lore_spawns.append((x + TILE_SIZE // 2, y + TILE_SIZE // 2))

    # ------------------------------------------------------------------

    def draw(self, surface: pygame.Surface, camera) -> None:
        """Draw only the tiles visible in the camera window."""
        for tile in self.tiles:
            screen_rect = camera.apply_rect(tile)

            # Skip tiles entirely off-screen (performance optimisation)
            if (screen_rect.right  < 0 or screen_rect.left > surface.get_width() or
                screen_rect.bottom < 0 or screen_rect.top  > surface.get_height()):
                continue

            # Fill
            pygame.draw.rect(surface, TILE_COLOR, screen_rect)
            # Top highlight edge for a slight 3-D feel
            pygame.draw.line(surface, TILE_EDGE_COLOR,
                screen_rect.topleft, screen_rect.topright, 2)

    # ------------------------------------------------------------------

    def get_solid_rects(self) -> list[pygame.Rect]:
        """Return all solid rects — used by the physics system."""
        return self.tiles
