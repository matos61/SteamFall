# =============================================================================
# scenes/gameplay.py — Main platformer loop.
#
# What happens here each frame:
#   1. Player reads input + moves (inside player.update())
#   2. Enemies run AI + move  (inside enemy.update())
#   3. Physics resolves gravity and tile collisions
#   4. Combat: player attacks hit enemies, enemy attacks hit player
#   5. Camera follows player
#   6. Everything is drawn: tiles → enemies → player → HUD
#
# Adding a new room / level later:
#   • Add a new level string list to world/tilemap.py
#   • Call game.change_scene(SCENE_GAMEPLAY, level="level_2")
#   • Add a branch in on_enter() to load the right level
# =============================================================================

import pygame
from settings           import *
from scenes.base_scene  import BaseScene
from core.camera        import Camera
from core.hitstop       import hitstop
from world.tilemap      import TileMap, LEVEL_1, LEVEL_2
from entities.player    import Player
from entities.enemy     import Enemy
from entities.crawler   import Crawler
from systems.checkpoint import Checkpoint
from systems.collectible import SoulFragment


class GameplayScene(BaseScene):
    def __init__(self, game):
        super().__init__(game)
        self._setup_done = False

    # ------------------------------------------------------------------

    def on_enter(self, **kwargs) -> None:
        faction    = self.game.player_faction or FACTION_MARKED
        level_name = kwargs.get("level", "level_1")

        # Pick level data
        level_data = LEVEL_2 if level_name == "level_2" else LEVEL_1
        self._level_name = level_name

        # Build the level
        self.tilemap = TileMap(level_data, level_name=level_name)
        self.camera  = Camera(self.tilemap.width, self.tilemap.height)

        # Spawn player — use checkpoint position if respawning after death
        save = self.game.save_data
        if save.get("checkpoint_pos") and save.get("respawn"):
            cx, cy = save["checkpoint_pos"]
            self.player = Player(cx, cy, faction=faction)
            self.player.health = int(
                save.get("checkpoint_health_frac", 1.0) * self.player.max_health
            )
            save["respawn"] = False
        else:
            px, py = self.tilemap.player_spawn
            self.player = Player(px, py, faction=faction)

        # Spawn standard enemies at all 'E' markers
        self.enemies: list = []
        for (ex, ey) in self.tilemap.enemy_spawns:
            self.enemies.append(Enemy(ex, ey))

        # Spawn crawlers at all 'c' markers
        for (cx2, cy2) in self.tilemap.crawler_spawns:
            self.enemies.append(Crawler(cx2, cy2))

        # Checkpoints
        self.checkpoints: list[Checkpoint] = list(self.tilemap.checkpoints)

        # Soul fragments (collectibles that drop when enemies die)
        self.fragments: list[SoulFragment] = []

        self._setup_done    = True
        self._death_timer   = 0
        self._damage_flash  = 0   # HK-style red edge vignette on taking a hit
        self._prev_iframes  = 0   # Track iframes last frame to detect new hits

        # Fonts for HUD
        self.font_hud    = pygame.font.SysFont("monospace", 16, bold=True)
        self.font_debug  = pygame.font.SysFont("monospace", 13)
        self.font_death  = pygame.font.SysFont("georgia",   52, bold=True)
        self.font_pause  = pygame.font.SysFont("georgia",   48)

        # Paused?
        self._paused = False

    # ------------------------------------------------------------------
    # Event handling
    # ------------------------------------------------------------------

    def handle_event(self, event) -> None:
        if not self._setup_done:
            return
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._paused = not self._paused
            # Quick return to main menu while testing
            if event.key == pygame.K_F1:
                self.game.change_scene(SCENE_MAIN_MENU)

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, dt: int) -> None:
        if not self._setup_done or self._paused:
            return

        # --- Tick hitstop FIRST so the frame-count is correct ---
        hitstop.tick()

        solid = self.tilemap.get_solid_rects()

        # --- Skip entity updates while hitstop is active ---
        if not hitstop.is_active():
            # Snapshot iframes before update to detect a new hit this frame
            prev_iframes = self._prev_iframes

            # --- Player ---
            self.player.update(dt, solid_rects=solid)

            # If iframes just went from 0 → positive the player was just hit
            if prev_iframes == 0 and self.player.iframes > 0:
                self._damage_flash = DAMAGE_FLASH_FRAMES

            # Store for next frame comparison, and tick down the vignette
            self._prev_iframes = self.player.iframes
            if self._damage_flash > 0:
                self._damage_flash -= 1

            # --- Enemies ---
            for enemy in self.enemies:
                enemy.update(dt, player=self.player, solid_rects=solid)

            # --- Soul fragments ---
            for frag in self.fragments:
                frag.update()

        # --- Combat: player hits enemies ---
        # (hitbox checks still run so hitstop can be triggered)
        living_enemies = [e for e in self.enemies if e.alive]
        for hb in self.player.all_hitboxes():
            hb.check_hits(living_enemies)
            hb.update()

        # --- Combat: enemies hit player ---
        for enemy in living_enemies:
            for hb in enemy.hitboxes:
                hb.check_hits([self.player])
                hb.update()

        # --- Collect soul fragments ---
        remaining_frags = []
        for frag in self.fragments:
            if frag.alive and frag.rect.colliderect(self.player.rect):
                self.player._regen_resource(15)
                frag.alive = False
            if frag.alive:
                remaining_frags.append(frag)
        self.fragments = remaining_frags

        # --- Spawn fragments from newly dead enemies ---
        newly_dead = [e for e in self.enemies if not e.alive]
        for dead_e in newly_dead:
            for frag in dead_e.get_drop_fragments():
                self.fragments.append(frag)

        # --- Prune dead enemies ---
        self.enemies = [e for e in self.enemies if e.alive]

        # --- Checkpoints ---
        faction = self.game.player_faction or FACTION_MARKED
        for cp in self.checkpoints:
            cp.update(self.player, self.game, faction)

        # --- Camera ---
        self.camera.follow(self.player)

        # --- Level transition: right edge → level 2 ---
        if (self._level_name == "level_1" and
                self.player.rect.right >= self.tilemap.width - 64):
            self.game.change_scene(SCENE_GAMEPLAY, level="level_2")
            return

        # --- Player death ---
        if not self.player.alive:
            self._death_timer += 1
            if self._death_timer >= 150:   # ~2.5 seconds at 60fps
                save = self.game.save_data
                if save.get("checkpoint_pos"):
                    # Respawn at checkpoint
                    save["respawn"] = True
                    self.game.change_scene(SCENE_GAMEPLAY,
                                           level=save.get("checkpoint_level",
                                                          "level_1"))
                else:
                    self.game.change_scene(SCENE_MAIN_MENU)

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------

    def draw(self, surface: pygame.Surface) -> None:
        if not self._setup_done:
            return

        # Background gradient-ish (simple dark fill with slightly lighter top)
        surface.fill((10, 7, 22))

        # World
        self.tilemap.draw(surface, self.camera)

        # Checkpoints
        for cp in self.checkpoints:
            cp.draw(surface, self.camera)

        # Soul fragments
        for frag in self.fragments:
            frag.draw(surface, self.camera)

        # Entities
        for enemy in self.enemies:
            enemy.draw(surface, self.camera)

        self.player.draw(surface, self.camera)

        # HUD
        self._draw_hud(surface)

        # Hit-stop flash: 1-frame white overlay when a hit lands
        if hitstop.consume_flash():
            flash = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            flash.fill((255, 255, 255, 60))
            surface.blit(flash, (0, 0))

        # Damage vignette: red edge flash when the player takes a hit (HK-style)
        if self._damage_flash > 0:
            self._draw_damage_vignette(surface)

        # Pause overlay
        if self._paused:
            self._draw_pause(surface)

        # Death overlay
        if not self.player.alive:
            self._draw_death(surface)

    # ------------------------------------------------------------------
    # HUD
    # ------------------------------------------------------------------

    def _draw_hud(self, surface: pygame.Surface) -> None:
        faction     = self.game.player_faction or FACTION_MARKED
        res_color   = SOUL_COLOR if faction == FACTION_MARKED else HEAT_COLOR
        res_label   = "SOUL" if faction == FACTION_MARKED else "HEAT"

        # --- Health bar ---
        self._draw_bar(surface,
            x=20, y=20, w=220, h=16,
            fill=self.player.health / self.player.max_health,
            fg=HEALTH_COLOR, bg=HEALTH_BG_COLOR, label="HP")

        # --- Resource bar ---
        self._draw_bar(surface,
            x=20, y=44, w=220, h=12,
            fill=self.player.resource / self.player.max_resource,
            fg=res_color, bg=RESOURCE_BG_COLOR, label=res_label)

        # --- Ability cooldown pips (5 pips under resource bar) ---
        self._draw_cooldown_pips(surface, faction, res_color, x=20, y=62)

        # Faction tag
        tag_color = MARKED_COLOR if faction == FACTION_MARKED else FLESHFORGED_COLOR
        tag_text  = ("THE MARKED" if faction == FACTION_MARKED else "FLESHFORGED")
        tag       = self.font_hud.render(tag_text, True, tag_color)
        surface.blit(tag, (20, 80))

        # --- Checkpoint indicator (top-right when a checkpoint is active) ---
        if self.game.save_data.get("checkpoint_pos"):
            self._draw_checkpoint_indicator(surface)

        # Controls reminder
        hints = [
            "A/D Move   W/Space Jump   Z Attack   X Ability",
            "ESC Pause  F1 Menu",
        ]
        for i, h in enumerate(hints):
            ht = self.font_debug.render(h, True, (45, 42, 55))
            surface.blit(ht, (20, SCREEN_HEIGHT - 36 + i * 16))

    def _draw_cooldown_pips(self, surface, faction, res_color, x, y):
        """5 small pips showing ability cooldown. Lit = ready."""
        max_cd  = 90   # Marked soul surge cooldown
        if faction != FACTION_MARKED:
            max_cd = 240   # Fleshforged overdrive cooldown
        cd      = self.player._ability_cooldown
        pip_w, pip_h, gap = 12, 6, 3
        for i in range(5):
            # Pip is lit if the cooldown fraction is low enough
            threshold = max_cd * (i + 1) / 5
            lit = cd <= max_cd - threshold
            color = res_color if lit else (40, 35, 55)
            rx = x + i * (pip_w + gap)
            pygame.draw.rect(surface, color, (rx, y, pip_w, pip_h))
            pygame.draw.rect(surface, (80, 75, 100), (rx, y, pip_w, pip_h), 1)

    def _draw_checkpoint_indicator(self, surface):
        """Small glowing diamond top-right to show an active checkpoint."""
        cx = SCREEN_WIDTH - 32
        cy = 32
        size = 10
        pts  = [(cx, cy - size), (cx + size, cy),
                (cx, cy + size), (cx - size, cy)]
        pygame.draw.polygon(surface, CHECKPOINT_GLOW_COLOR, pts)
        pygame.draw.polygon(surface, (255, 255, 200), pts, 2)
        lbl = self.font_debug.render("CP", True, (200, 200, 160))
        surface.blit(lbl, (cx - lbl.get_width() // 2, cy + size + 4))

    def _draw_bar(self, surface, x, y, w, h, fill, fg, bg, label) -> None:
        pygame.draw.rect(surface, bg, (x, y, w, h))
        filled_w = int(w * max(0, min(fill, 1)))
        pygame.draw.rect(surface, fg, (x, y, filled_w, h))
        pygame.draw.rect(surface, (60, 55, 75), (x, y, w, h), 1)
        lbl = self.font_hud.render(label, True, (180, 175, 200))
        surface.blit(lbl, (x + w + 8, y - 2))

    def _draw_damage_vignette(self, surface: pygame.Surface) -> None:
        """Red screen-edge vignette drawn when the player takes a hit (HK feel)."""
        # Fade: strongest on frame 0, zero by DAMAGE_FLASH_FRAMES
        alpha = int(160 * self._damage_flash / DAMAGE_FLASH_FRAMES)
        if alpha <= 0:
            return
        border = 60   # Pixel thickness of the vignette border
        vsurf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        # Draw four edge rectangles to form a border-only red overlay
        red = (200, 20, 20, alpha)
        pygame.draw.rect(vsurf, red, (0, 0, SCREEN_WIDTH, border))               # top
        pygame.draw.rect(vsurf, red, (0, SCREEN_HEIGHT - border, SCREEN_WIDTH, border))  # bottom
        pygame.draw.rect(vsurf, red, (0, 0, border, SCREEN_HEIGHT))               # left
        pygame.draw.rect(vsurf, red, (SCREEN_WIDTH - border, 0, border, SCREEN_HEIGHT))  # right
        surface.blit(vsurf, (0, 0))

    def _draw_death(self, surface: pygame.Surface) -> None:
        # Fade in dark overlay over time
        fade = min(180, self._death_timer * 2)
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, fade))
        surface.blit(overlay, (0, 0))

        if self._death_timer > 30:   # Wait a beat before showing text
            txt = self.font_death.render("you perished", True, (160, 30, 30))
            surface.blit(txt, (SCREEN_WIDTH // 2 - txt.get_width() // 2,
                               SCREEN_HEIGHT // 2 - 40))
        if self._death_timer > 80:
            sub = self.font_hud.render("returning...", True, GRAY)
            surface.blit(sub, (SCREEN_WIDTH // 2 - sub.get_width() // 2,
                               SCREEN_HEIGHT // 2 + 30))

    def _draw_pause(self, surface: pygame.Surface) -> None:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        surface.blit(overlay, (0, 0))
        txt = self.font_pause.render("PAUSED", True, WHITE)
        surface.blit(txt, (SCREEN_WIDTH // 2 - txt.get_width() // 2,
                           SCREEN_HEIGHT // 2 - 40))
        sub = self.font_hud.render("ESC — Resume     F1 — Main Menu", True, GRAY)
        surface.blit(sub, (SCREEN_WIDTH // 2 - sub.get_width() // 2,
                           SCREEN_HEIGHT // 2 + 30))
