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
# Adding a new room / level:
#   • Add level string to world/tilemap.py
#   • Add entry to _LEVEL_CHAIN and _LEVEL_NAMES below
# =============================================================================

import pygame
from settings           import *
from scenes.base_scene  import BaseScene
from core.camera        import Camera
from core.hitstop       import hitstop
from world.tilemap      import TileMap, LEVEL_1, LEVEL_2, LEVEL_3, LEVEL_4, LEVEL_5
from entities.player    import Player
from entities.enemy     import Enemy
from entities.crawler   import Crawler
from entities.boss      import Boss
from systems.checkpoint import Checkpoint
from systems.collectible import SoulFragment
from systems.minimap    import MiniMap


# Level display names and progression chain
_LEVEL_NAMES = {
    "level_1": "I \u2014 The Outer District",
    "level_2": "II \u2014 The Descent",
    "level_3": "III \u2014 The Foundry",
    "level_4": "IV \u2014 The Ruined Spire",
    "level_5": "V \u2014 The Sanctum",
}
_LEVEL_DATA = {
    "level_1": LEVEL_1,
    "level_2": LEVEL_2,
    "level_3": LEVEL_3,
    "level_4": LEVEL_4,
    "level_5": LEVEL_5,
}
_LEVEL_CHAIN = {
    "level_1": "level_2",
    "level_2": "level_3",
    "level_3": "level_4",
    "level_4": "level_5",
}


class GameplayScene(BaseScene):
    def __init__(self, game):
        super().__init__(game)
        self._setup_done = False

    # ------------------------------------------------------------------

    def on_enter(self, **kwargs) -> None:
        faction    = self.game.player_faction or FACTION_MARKED
        level_name = kwargs.get("level", "level_1")

        level_data = _LEVEL_DATA.get(level_name, LEVEL_1)
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
                save.get("checkpoint_health_frac", 1.0) * self.player.max_health)
            save["respawn"] = False
        else:
            px, py = self.tilemap.player_spawn
            self.player = Player(px, py, faction=faction)

        # Spawn standard enemies
        self.enemies: list = []
        for (ex, ey) in self.tilemap.enemy_spawns:
            self.enemies.append(Enemy(ex, ey))

        # Spawn crawlers
        for (cx2, cy2) in self.tilemap.crawler_spawns:
            self.enemies.append(Crawler(cx2, cy2))

        # Spawn boss
        self._boss = None
        if self.tilemap.boss_spawn:
            bx, by = self.tilemap.boss_spawn
            boss = Boss(bx, by, name="The Warden")
            self.enemies.append(boss)
            self._boss = boss

        # Checkpoints
        self.checkpoints: list[Checkpoint] = list(self.tilemap.checkpoints)

        # Soul fragments
        self.fragments: list[SoulFragment] = []

        # --- Transition state ---
        _fade_in = kwargs.get("_fade_in", False)
        if _fade_in:
            self._transition_phase = "fade_in"
            self._transition_timer = 0
        else:
            self._transition_phase = None
            self._transition_timer = 0
        self._transition_next              = None
        self._transition_next_display_name = ""
        self._transition_surf              = pygame.Surface(
            (SCREEN_WIDTH, SCREEN_HEIGHT))
        self._transition_surf.fill(BLACK)
        self._level_display_name = _LEVEL_NAMES.get(level_name, level_name)

        # --- Pause menu ---
        self._paused        = False
        self._pause_options = ["Resume", "Return to Main Menu", "Settings (soon)"]
        self._pause_sel     = 0

        # --- Map ---
        self._map_open = False
        self._minimap  = MiniMap(self.game)
        self._minimap.mark_visited(level_name)

        # --- Misc HUD state ---
        self._setup_done   = True
        self._death_timer  = 0
        self._damage_flash = 0
        self._prev_iframes = 0

        # Fonts
        self.font_hud       = pygame.font.SysFont("monospace", 16, bold=True)
        self.font_debug     = pygame.font.SysFont("monospace", 13)
        self.font_death     = pygame.font.SysFont("georgia",   52, bold=True)
        self.font_pause     = pygame.font.SysFont("georgia",   48)
        self.font_trans     = pygame.font.SysFont("georgia",   36)
        self.font_boss_name = pygame.font.SysFont("georgia",   14, bold=True)
        self.font_pause_opt = pygame.font.SysFont("georgia",   30)

    # ------------------------------------------------------------------
    # Event handling
    # ------------------------------------------------------------------

    def handle_event(self, event) -> None:
        if not self._setup_done:
            return
        if event.type != pygame.KEYDOWN:
            return

        if self._paused:
            if event.key == pygame.K_ESCAPE:
                self._paused = False
                self._pause_sel = 0
            elif event.key in (pygame.K_UP, pygame.K_w):
                self._pause_sel = (self._pause_sel - 1) % len(self._pause_options)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self._pause_sel = (self._pause_sel + 1) % len(self._pause_options)
            elif event.key == pygame.K_RETURN:
                self._activate_pause_option()
        else:
            if event.key == pygame.K_ESCAPE:
                self._paused   = True
                self._pause_sel = 0
            if event.key == pygame.K_F1:
                self.game.change_scene(SCENE_MAIN_MENU)
            if event.key == pygame.K_m:
                self._map_open = not self._map_open

    def _activate_pause_option(self) -> None:
        opt = self._pause_options[self._pause_sel]
        if opt == "Resume":
            self._paused   = False
            self._pause_sel = 0
        elif opt == "Return to Main Menu":
            self.game.change_scene(SCENE_MAIN_MENU)
        # "Settings (soon)" → stub, do nothing

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, dt: int) -> None:
        if not self._setup_done:
            return

        # --- Transition takes full control ---
        if self._transition_phase is not None:
            self._tick_transition()
            return

        # --- Map and pause freeze game logic ---
        if self._map_open or self._paused:
            return

        # --- Tick hitstop FIRST ---
        hitstop.tick()

        solid = self.tilemap.get_solid_rects()

        if not hitstop.is_active():
            prev_iframes = self._prev_iframes

            # Player
            self.player.update(dt, solid_rects=solid)

            if prev_iframes == 0 and self.player.iframes > 0:
                self._damage_flash = DAMAGE_FLASH_FRAMES
            self._prev_iframes = self.player.iframes
            if self._damage_flash > 0:
                self._damage_flash -= 1

            # Enemies
            for enemy in self.enemies:
                enemy.update(dt, player=self.player, solid_rects=solid)

            # Soul fragments
            for frag in self.fragments:
                frag.update()

        # --- Combat: player hits enemies ---
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
        remaining = []
        for frag in self.fragments:
            if frag.alive and frag.rect.colliderect(self.player.rect):
                self.player._regen_resource(15)
                frag.alive = False
            if frag.alive:
                remaining.append(frag)
        self.fragments = remaining

        # --- Spawn fragments from newly dead enemies ---
        newly_dead = [e for e in self.enemies if not e.alive]
        for dead_e in newly_dead:
            for frag in dead_e.get_drop_fragments():
                self.fragments.append(frag)

        # If the boss just died, clear the boss reference
        if self._boss and not self._boss.alive:
            self._boss = None

        # --- Prune dead enemies ---
        self.enemies = [e for e in self.enemies if e.alive]

        # --- Checkpoints ---
        faction = self.game.player_faction or FACTION_MARKED
        for cp in self.checkpoints:
            cp.update(self.player, self.game, faction)

        # --- Camera ---
        self.camera.follow(self.player)

        # --- Fall-death guard: entity fell below world floor ---
        oob_y = self.tilemap.height + 300
        for enemy in self.enemies:
            if enemy.rect.top > oob_y:
                enemy.die()
        if self.player.rect.top > oob_y:
            self.player.take_damage(self.player.max_health)

        # --- Level transition: right edge → next level (alive players only) ---
        next_level = _LEVEL_CHAIN.get(self._level_name)
        if next_level and self.player.alive and self.player.rect.right >= self.tilemap.width - 64:
            self._begin_transition(SCENE_GAMEPLAY, level=next_level)
            return

        # --- Player death ---
        if not self.player.alive:
            self._death_timer += 1
            if self._death_timer >= 150:
                save = self.game.save_data
                if save.get("checkpoint_pos"):
                    save["respawn"] = True
                    self.game.change_scene(
                        SCENE_GAMEPLAY,
                        level=save.get("checkpoint_level", "level_1"))
                else:
                    self.game.change_scene(SCENE_MAIN_MENU)

    # ------------------------------------------------------------------
    # Transition state machine
    # ------------------------------------------------------------------

    def _begin_transition(self, scene_name: str, **kwargs) -> None:
        self._transition_phase              = "fade_out"
        self._transition_timer              = 0
        self._transition_next               = (scene_name, kwargs)
        next_level                          = kwargs.get("level", "")
        self._transition_next_display_name  = _LEVEL_NAMES.get(next_level,
                                                                next_level)

    def _tick_transition(self) -> None:
        self._transition_timer += 1
        if self._transition_phase == "fade_out":
            if self._transition_timer >= TRANSITION_FADE_FRAMES:
                self._transition_phase = "hold"
                self._transition_timer = 0
        elif self._transition_phase == "hold":
            if self._transition_timer >= TRANSITION_HOLD_FRAMES:
                scene_name, kwargs = self._transition_next
                kwargs["_fade_in"] = True
                self.game.change_scene(scene_name, **kwargs)
        elif self._transition_phase == "fade_in":
            if self._transition_timer >= TRANSITION_IN_FRAMES:
                self._transition_phase = None

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------

    def draw(self, surface: pygame.Surface) -> None:
        if not self._setup_done:
            return

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

        # Hit-stop white flash
        if hitstop.consume_flash():
            flash = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            flash.fill((255, 255, 255, 60))
            surface.blit(flash, (0, 0))

        # Damage vignette
        if self._damage_flash > 0:
            self._draw_damage_vignette(surface)

        # Map overlay (drawn before pause/death so it can coexist)
        if self._map_open:
            self._minimap.draw_overlay(surface, self._level_name, self.tilemap)

        # Pause overlay
        if self._paused:
            self._draw_pause(surface)

        # Death overlay
        if not self.player.alive:
            self._draw_death(surface)

        # Level transition overlay (topmost)
        if self._transition_phase is not None:
            self._draw_transition_overlay(surface)

    # ------------------------------------------------------------------
    # HUD
    # ------------------------------------------------------------------

    def _draw_hud(self, surface: pygame.Surface) -> None:
        faction   = self.game.player_faction or FACTION_MARKED
        res_color = SOUL_COLOR if faction == FACTION_MARKED else HEAT_COLOR
        res_label = "SOUL" if faction == FACTION_MARKED else "HEAT"

        self._draw_bar(surface, x=20, y=20, w=220, h=16,
                       fill=self.player.health / self.player.max_health,
                       fg=HEALTH_COLOR, bg=HEALTH_BG_COLOR, label="HP")

        self._draw_bar(surface, x=20, y=44, w=220, h=12,
                       fill=self.player.resource / self.player.max_resource,
                       fg=res_color, bg=RESOURCE_BG_COLOR, label=res_label)

        self._draw_cooldown_pips(surface, faction, res_color, x=20, y=62)

        tag_color = MARKED_COLOR if faction == FACTION_MARKED else FLESHFORGED_COLOR
        tag_text  = "THE MARKED" if faction == FACTION_MARKED else "FLESHFORGED"
        tag       = self.font_hud.render(tag_text, True, tag_color)
        surface.blit(tag, (20, 80))

        if self.game.save_data.get("checkpoint_pos"):
            self._draw_checkpoint_indicator(surface)

        # Boss health bar
        if self._boss and self._boss.alive:
            self._draw_boss_bar(surface, self._boss)

        hints = [
            "A/D Move   W/Space Jump   Z Attack   X Ability   M Map",
            "ESC Pause  F1 Menu",
        ]
        for i, h in enumerate(hints):
            ht = self.font_debug.render(h, True, (45, 42, 55))
            surface.blit(ht, (20, SCREEN_HEIGHT - 36 + i * 16))

    def _draw_cooldown_pips(self, surface, faction, res_color, x, y):
        max_cd  = 90 if faction == FACTION_MARKED else 240
        cd      = self.player._ability_cooldown
        pip_w, pip_h, gap = 12, 6, 3
        for i in range(5):
            threshold = max_cd * (i + 1) / 5
            lit       = cd <= max_cd - threshold
            color     = res_color if lit else (40, 35, 55)
            rx        = x + i * (pip_w + gap)
            pygame.draw.rect(surface, color, (rx, y, pip_w, pip_h))
            pygame.draw.rect(surface, (80, 75, 100), (rx, y, pip_w, pip_h), 1)

    def _draw_checkpoint_indicator(self, surface):
        cx   = SCREEN_WIDTH - 32
        cy   = 32
        size = 10
        pts  = [(cx, cy - size), (cx + size, cy), (cx, cy + size), (cx - size, cy)]
        pygame.draw.polygon(surface, CHECKPOINT_GLOW_COLOR, pts)
        pygame.draw.polygon(surface, (255, 255, 200), pts, 2)
        lbl = self.font_debug.render("CP", True, (200, 200, 160))
        surface.blit(lbl, (cx - lbl.get_width() // 2, cy + size + 4))

    def _draw_boss_bar(self, surface: pygame.Surface, boss) -> None:
        bar_x   = BOSS_BAR_MARGIN
        bar_y   = BOSS_BAR_Y
        bar_w   = SCREEN_WIDTH - BOSS_BAR_MARGIN * 2
        bar_h   = BOSS_BAR_HEIGHT
        fill    = boss.health / boss.max_health

        # Color by phase
        if boss.phase == 3:
            bar_color = (220, 0, 0)
        elif boss.phase == 2:
            bar_color = (220, 120, 0)
        else:
            bar_color = HEALTH_COLOR

        pygame.draw.rect(surface, HEALTH_BG_COLOR, (bar_x, bar_y, bar_w, bar_h))
        filled_w = int(bar_w * max(0.0, fill))
        pygame.draw.rect(surface, bar_color, (bar_x, bar_y, filled_w, bar_h))
        pygame.draw.rect(surface, (60, 55, 75), (bar_x, bar_y, bar_w, bar_h), 1)

        # Phase threshold ticks at 50% and 25%
        for frac in (0.50, 0.25):
            tx = bar_x + int(bar_w * frac)
            pygame.draw.line(surface, WHITE,
                             (tx, bar_y), (tx, bar_y + bar_h), 2)

        # Boss name label
        name_surf = self.font_boss_name.render(boss.name.upper(), True, (200, 190, 220))
        surface.blit(name_surf,
                     (SCREEN_WIDTH // 2 - name_surf.get_width() // 2,
                      bar_y - name_surf.get_height() - 2))

    def _draw_bar(self, surface, x, y, w, h, fill, fg, bg, label) -> None:
        pygame.draw.rect(surface, bg, (x, y, w, h))
        filled_w = int(w * max(0, min(fill, 1)))
        pygame.draw.rect(surface, fg, (x, y, filled_w, h))
        pygame.draw.rect(surface, (60, 55, 75), (x, y, w, h), 1)
        lbl = self.font_hud.render(label, True, (180, 175, 200))
        surface.blit(lbl, (x + w + 8, y - 2))

    def _draw_damage_vignette(self, surface: pygame.Surface) -> None:
        alpha  = int(160 * self._damage_flash / DAMAGE_FLASH_FRAMES)
        if alpha <= 0:
            return
        border = 60
        vsurf  = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        red    = (200, 20, 20, alpha)
        pygame.draw.rect(vsurf, red, (0, 0, SCREEN_WIDTH, border))
        pygame.draw.rect(vsurf, red, (0, SCREEN_HEIGHT - border, SCREEN_WIDTH, border))
        pygame.draw.rect(vsurf, red, (0, 0, border, SCREEN_HEIGHT))
        pygame.draw.rect(vsurf, red, (SCREEN_WIDTH - border, 0, border, SCREEN_HEIGHT))
        surface.blit(vsurf, (0, 0))

    def _draw_death(self, surface: pygame.Surface) -> None:
        fade    = min(180, self._death_timer * 2)
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, fade))
        surface.blit(overlay, (0, 0))
        if self._death_timer > 30:
            txt = self.font_death.render("you perished", True, (160, 30, 30))
            surface.blit(txt, (SCREEN_WIDTH // 2 - txt.get_width() // 2,
                               SCREEN_HEIGHT // 2 - 40))
        if self._death_timer > 80:
            sub = self.font_hud.render("returning...", True, GRAY)
            surface.blit(sub, (SCREEN_WIDTH // 2 - sub.get_width() // 2,
                               SCREEN_HEIGHT // 2 + 30))

    def _draw_pause(self, surface: pygame.Surface) -> None:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        surface.blit(overlay, (0, 0))

        cx = SCREEN_WIDTH // 2

        # Title
        title = self.font_pause.render("PAUSED", True, WHITE)
        surface.blit(title, (cx - title.get_width() // 2, SCREEN_HEIGHT // 2 - 140))

        # Menu options
        for i, opt in enumerate(self._pause_options):
            is_sel = (i == self._pause_sel)
            color  = WHITE if is_sel else GRAY
            text   = self.font_pause_opt.render(opt, True, color)
            tx     = cx - text.get_width() // 2
            ty     = SCREEN_HEIGHT // 2 - 40 + i * 56
            surface.blit(text, (tx, ty))
            if is_sel:
                pygame.draw.polygon(surface, GOLD, [
                    (tx - 22, ty + 15),
                    (tx - 14, ty + 7),
                    (tx - 6,  ty + 15),
                    (tx - 14, ty + 23),
                ])

        hint = self.font_debug.render(
            "\u2191\u2193 Navigate   ENTER Confirm   ESC Resume", True, (50, 50, 60))
        surface.blit(hint,
                     (cx - hint.get_width() // 2, SCREEN_HEIGHT - 38))

    def _draw_transition_overlay(self, surface: pygame.Surface) -> None:
        if self._transition_phase == "fade_out":
            alpha = int(255 * self._transition_timer / TRANSITION_FADE_FRAMES)
            label = self._transition_next_display_name
        elif self._transition_phase == "hold":
            alpha = 255
            label = self._transition_next_display_name
        else:   # fade_in
            alpha = int(255 * (1 - self._transition_timer / TRANSITION_IN_FRAMES))
            label = self._level_display_name

        alpha = max(0, min(255, alpha))
        self._transition_surf.set_alpha(alpha)
        surface.blit(self._transition_surf, (0, 0))

        # Level name shown during hold + early fade-in
        if label and alpha > 60:
            lbl = self.font_trans.render(label, True, (200, 190, 140))
            surface.blit(lbl, (SCREEN_WIDTH // 2 - lbl.get_width() // 2,
                               SCREEN_HEIGHT // 2 - 20))
