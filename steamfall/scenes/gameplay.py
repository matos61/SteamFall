# =============================================================================
# scenes/gameplay.py — Main platformer loop.
#
# Frame order:
#   1. Player reads input + moves  (player.update)
#   2. Enemies run AI + move       (enemy.update)
#   3. Physics resolves collisions (inside update calls above)
#   4. Combat: player hits enemies; enemies hit player; boss projectiles hit player
#   5. Collectibles: fragments picked up, enemies pruned
#   6. Checkpoints ticked; camera follows player
#   7. Level-transition / death checks
#   8. Everything drawn: tiles → pickups → enemies → player → HUD → overlays
# =============================================================================

import pygame
from settings           import *
from scenes.base_scene  import BaseScene
from core.camera        import Camera
from core.hitstop       import hitstop
from world.tilemap      import (TileMap,
                                LEVEL_1, LEVEL_2, LEVEL_3, LEVEL_4, LEVEL_5)
from entities.player    import Player
from entities.enemy     import Enemy
from entities.crawler   import Crawler
from entities.boss      import Boss
from systems.checkpoint import Checkpoint
from systems.collectible import SoulFragment
from systems.upgrade    import UpgradeMenu, UPGRADES

# Level name → data
_LEVEL_DATA = {
    "level_1": LEVEL_1,
    "level_2": LEVEL_2,
    "level_3": LEVEL_3,
    "level_4": LEVEL_4,
    "level_5": LEVEL_5,
}

# Transition chain (right-edge walk triggers next level)
_NEXT_LEVEL = {
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
    # Scene entry
    # ------------------------------------------------------------------

    def on_enter(self, **kwargs) -> None:
        faction    = self.game.player_faction or FACTION_MARKED
        level_name = kwargs.get("level", "level_1")

        level_data       = _LEVEL_DATA.get(level_name, LEVEL_1)
        self._level_name = level_name

        self.tilemap = TileMap(level_data, level_name=level_name)
        self.camera  = Camera(self.tilemap.width, self.tilemap.height)

        # Spawn player — checkpoint respawn or fresh spawn
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

        # Restore ability unlock and apply any earned upgrades
        self.player.ability_slots = save.get("ability_slots", ABILITY_SLOTS_DEFAULT)
        for upg_key in save.get("upgrades", []):
            self._apply_upgrade_to_player(upg_key)

        # Spawn regular enemies
        self.enemies: list = []
        for ex, ey in self.tilemap.enemy_spawns:
            self.enemies.append(Enemy(ex, ey))
        for cx2, cy2 in self.tilemap.crawler_spawns:
            self.enemies.append(Crawler(cx2, cy2))

        # Spawn boss if level has one
        self._boss: Boss | None = None
        if self.tilemap.boss_spawn:
            bx, by = self.tilemap.boss_spawn
            self._boss = Boss(bx, by, name="The Warden")
            self.enemies.append(self._boss)

        self.checkpoints: list = list(self.tilemap.checkpoints)
        self.fragments:   list = []

        self._setup_done   = True
        self._death_timer  = 0
        self._damage_flash = 0
        self._prev_iframes = 0

        # Upgrade overlay state
        self._upgrade_pending = False
        self._upgrade_menu:   UpgradeMenu | None = None

        # Pause menu state
        self._paused       = False
        self._pause_options = ["Resume", "Return to Main Menu", "Settings (soon)"]
        self._pause_sel    = 0

        # Fonts
        self.font_hud        = pygame.font.SysFont("monospace", 16, bold=True)
        self.font_debug      = pygame.font.SysFont("monospace", 13)
        self.font_death      = pygame.font.SysFont("georgia",   52, bold=True)
        self.font_pause      = pygame.font.SysFont("georgia",   48)
        self.font_pause_item = pygame.font.SysFont("georgia",   34)

    # ------------------------------------------------------------------
    # Event handling
    # ------------------------------------------------------------------

    def handle_event(self, event) -> None:
        if not self._setup_done:
            return

        # Upgrade menu captures all input while active
        if self._upgrade_pending and self._upgrade_menu:
            chosen = self._upgrade_menu.handle_event(event)
            if chosen:
                self._commit_upgrade(chosen["key"])
                self._upgrade_pending = False
                self._upgrade_menu    = None
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._paused = not self._paused
                if not self._paused:
                    self._pause_sel = 0

            elif self._paused:
                if event.key in (pygame.K_UP, pygame.K_w):
                    self._pause_sel = (self._pause_sel - 1) % len(self._pause_options)
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    self._pause_sel = (self._pause_sel + 1) % len(self._pause_options)
                elif event.key == pygame.K_RETURN:
                    self._activate_pause_option()

            elif event.key == pygame.K_F1:
                self.game.change_scene(SCENE_MAIN_MENU)

    def _activate_pause_option(self) -> None:
        opt = self._pause_options[self._pause_sel]
        if opt == "Resume":
            self._paused    = False
            self._pause_sel = 0
        elif opt == "Return to Main Menu":
            self.game.change_scene(SCENE_MAIN_MENU)
        # "Settings (soon)" → no-op stub

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, dt: int) -> None:
        if not self._setup_done or self._paused or self._upgrade_pending:
            return

        hitstop.tick()
        solid = self.tilemap.get_solid_rects()

        if not hitstop.is_active():
            prev_iframes = self._prev_iframes

            self.player.update(dt, solid_rects=solid)

            if prev_iframes == 0 and self.player.iframes > 0:
                self._damage_flash = DAMAGE_FLASH_FRAMES

            self._prev_iframes = self.player.iframes
            if self._damage_flash > 0:
                self._damage_flash -= 1

            for enemy in self.enemies:
                enemy.update(dt, player=self.player, solid_rects=solid)

            for frag in self.fragments:
                frag.update()

        # --- Combat: player attacks hit enemies ---
        living_enemies = [e for e in self.enemies if e.alive]
        for hb in self.player.all_hitboxes():
            hb.check_hits(living_enemies)
            hb.update()

        # --- Combat: enemy attacks hit player ---
        for enemy in living_enemies:
            for hb in enemy.hitboxes:
                hb.check_hits([self.player])
                hb.update()

        # --- Boss projectiles hit player ---
        if self._boss and self._boss.alive:
            for proj in self._boss.get_projectiles():
                if proj.alive and proj.rect.colliderect(self.player.rect):
                    knockback = 1 if proj.vx >= 0 else -1
                    self.player.take_damage(proj.damage, knockback_dir=knockback)
                    proj.alive = False

        # --- Collect soul fragments ---
        remaining = []
        for frag in self.fragments:
            if frag.alive and frag.rect.colliderect(self.player.rect):
                self.player._regen_resource(15)
                frag.alive = False
            if frag.alive:
                remaining.append(frag)
        self.fragments = remaining

        # --- Newly dead enemies: drop fragments; detect boss kill ---
        newly_dead = [e for e in self.enemies if not e.alive]
        for dead_e in newly_dead:
            for frag in dead_e.get_drop_fragments():
                self.fragments.append(frag)
            if isinstance(dead_e, Boss) and not self._upgrade_pending:
                self._upgrade_pending = True
                self._upgrade_menu    = UpgradeMenu()
                self._boss            = None   # clear so bar disappears

        # --- Prune dead enemies ---
        self.enemies = [e for e in self.enemies if e.alive]

        # --- Checkpoints ---
        faction = self.game.player_faction or FACTION_MARKED
        for cp in self.checkpoints:
            cp.update(self.player, self.game, faction)

        # --- Camera ---
        self.camera.follow(self.player)

        # --- Level transition (right-edge walk) ---
        next_lv = _NEXT_LEVEL.get(self._level_name)
        if next_lv and self.player.rect.right >= self.tilemap.width - 64:
            self.game.change_scene(SCENE_GAMEPLAY, level=next_lv)
            return

        # --- Player death ---
        if not self.player.alive:
            self._death_timer += 1
            if self._death_timer >= 150:
                sv = self.game.save_data
                if sv.get("checkpoint_pos"):
                    sv["respawn"] = True
                    self.game.change_scene(SCENE_GAMEPLAY,
                                           level=sv.get("checkpoint_level",
                                                         "level_1"))
                else:
                    self.game.change_scene(SCENE_MAIN_MENU)

    # ------------------------------------------------------------------
    # Upgrade helpers
    # ------------------------------------------------------------------

    def _apply_upgrade_to_player(self, key: str) -> None:
        """Apply a saved upgrade key directly to self.player (on-enter restore)."""
        if key == "attack":
            self.player.attack_bonus += UPGRADE_ATTACK_BONUS
        elif key == "health":
            self.player.max_health += UPGRADE_HEALTH_BONUS
            self.player.health      = self.player.max_health
        elif key == "speed":
            self.player._upgrade_speed_mult += UPGRADE_SPEED_BONUS

    def _commit_upgrade(self, key: str) -> None:
        """Record upgrade in save_data, apply to live player, write to disk."""
        self.game.save_data.setdefault("upgrades", []).append(key)
        self._apply_upgrade_to_player(key)
        self.game.save_to_disk()

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------

    def draw(self, surface: pygame.Surface) -> None:
        if not self._setup_done:
            return

        surface.fill((10, 7, 22))
        self.tilemap.draw(surface, self.camera)

        for cp in self.checkpoints:
            cp.draw(surface, self.camera)
        for frag in self.fragments:
            frag.draw(surface, self.camera)
        for enemy in self.enemies:
            enemy.draw(surface, self.camera)
        self.player.draw(surface, self.camera)

        self._draw_hud(surface)

        if hitstop.consume_flash():
            flash = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            flash.fill((255, 255, 255, 60))
            surface.blit(flash, (0, 0))

        if self._damage_flash > 0:
            self._draw_damage_vignette(surface)

        if self._paused:
            self._draw_pause(surface)

        if not self.player.alive:
            self._draw_death(surface)

        if self._upgrade_pending and self._upgrade_menu:
            faction = self.game.player_faction or FACTION_MARKED
            self._upgrade_menu.draw(surface, faction)

    # ------------------------------------------------------------------
    # HUD
    # ------------------------------------------------------------------

    def _draw_hud(self, surface: pygame.Surface) -> None:
        faction   = self.game.player_faction or FACTION_MARKED
        res_color = SOUL_COLOR if faction == FACTION_MARKED else HEAT_COLOR
        res_label = "SOUL"     if faction == FACTION_MARKED else "HEAT"

        self._draw_bar(surface, x=20, y=20, w=220, h=16,
                       fill=self.player.health / self.player.max_health,
                       fg=HEALTH_COLOR, bg=HEALTH_BG_COLOR, label="HP")

        self._draw_bar(surface, x=20, y=44, w=220, h=12,
                       fill=self.player.resource / self.player.max_resource,
                       fg=res_color, bg=RESOURCE_BG_COLOR, label=res_label)

        self._draw_cooldown_pips(surface, faction, res_color, x=20, y=62)

        tag_color = MARKED_COLOR if faction == FACTION_MARKED else FLESHFORGED_COLOR
        tag_text  = "THE MARKED" if faction == FACTION_MARKED else "FLESHFORGED"
        surface.blit(self.font_hud.render(tag_text, True, tag_color), (20, 80))

        if self.game.save_data.get("checkpoint_pos"):
            self._draw_checkpoint_indicator(surface)

        # Boss health bar when boss is alive
        if self._boss and self._boss.alive:
            self._draw_boss_bar(surface, self._boss)

        hints = [
            "A/D Move   W/Space Jump   Z Attack   X Ability",
            "ESC Pause  F1 Menu",
        ]
        for i, h in enumerate(hints):
            ht = self.font_debug.render(h, True, (45, 42, 55))
            surface.blit(ht, (20, SCREEN_HEIGHT - 36 + i * 16))

    def _draw_boss_bar(self, surface: pygame.Surface, boss: Boss) -> None:
        bar_x = BOSS_BAR_MARGIN
        bar_w = SCREEN_WIDTH - BOSS_BAR_MARGIN * 2
        bar_y = BOSS_BAR_Y

        if boss.phase == 3:
            bar_color = (220, 0, 0)
        elif boss.phase == 2:
            bar_color = (220, 120, 0)
        else:
            bar_color = HEALTH_COLOR

        pygame.draw.rect(surface, (30, 10, 10),
                         (bar_x, bar_y, bar_w, BOSS_BAR_HEIGHT))
        fill_w = int(bar_w * max(0, boss.health / boss.max_health))
        pygame.draw.rect(surface, bar_color,
                         (bar_x, bar_y, fill_w, BOSS_BAR_HEIGHT))
        pygame.draw.rect(surface, (120, 80, 140),
                         (bar_x, bar_y, bar_w, BOSS_BAR_HEIGHT), 1)

        # Phase threshold ticks (50% and 25%)
        t50 = bar_x + int(bar_w * BOSS_PHASE2_THRESH)
        t25 = bar_x + int(bar_w * BOSS_PHASE3_THRESH)
        pygame.draw.line(surface, (255, 200, 60),
                         (t50, bar_y), (t50, bar_y + BOSS_BAR_HEIGHT), 2)
        pygame.draw.line(surface, (255, 80, 80),
                         (t25, bar_y), (t25, bar_y + BOSS_BAR_HEIGHT), 2)

        font_boss = pygame.font.SysFont("georgia", 14, bold=True)
        lbl = font_boss.render(boss.name, True, (200, 180, 220))
        surface.blit(lbl, (bar_x, bar_y - 18))

    def _draw_cooldown_pips(self, surface, faction, res_color, x, y) -> None:
        max_cd  = 90 if faction == FACTION_MARKED else 240
        cd      = self.player._ability_cooldown
        pip_w, pip_h, gap = 12, 6, 3
        for i in range(5):
            threshold = max_cd * (i + 1) / 5
            lit   = cd <= max_cd - threshold
            color = res_color if lit else (40, 35, 55)
            rx = x + i * (pip_w + gap)
            pygame.draw.rect(surface, color,           (rx, y, pip_w, pip_h))
            pygame.draw.rect(surface, (80, 75, 100),   (rx, y, pip_w, pip_h), 1)

    def _draw_checkpoint_indicator(self, surface) -> None:
        cx, cy = SCREEN_WIDTH - 32, 32
        size   = 10
        pts    = [(cx, cy - size), (cx + size, cy),
                  (cx, cy + size), (cx - size, cy)]
        pygame.draw.polygon(surface, CHECKPOINT_GLOW_COLOR, pts)
        pygame.draw.polygon(surface, (255, 255, 200), pts, 2)
        lbl = self.font_debug.render("CP", True, (200, 200, 160))
        surface.blit(lbl, (cx - lbl.get_width() // 2, cy + size + 4))

    def _draw_bar(self, surface, x, y, w, h, fill, fg, bg, label) -> None:
        pygame.draw.rect(surface, bg, (x, y, w, h))
        pygame.draw.rect(surface, fg, (x, y, int(w * max(0, min(fill, 1))), h))
        pygame.draw.rect(surface, (60, 55, 75), (x, y, w, h), 1)
        surface.blit(self.font_hud.render(label, True, (180, 175, 200)),
                     (x + w + 8, y - 2))

    # ------------------------------------------------------------------
    # Overlays
    # ------------------------------------------------------------------

    def _draw_damage_vignette(self, surface: pygame.Surface) -> None:
        alpha = int(160 * self._damage_flash / DAMAGE_FLASH_FRAMES)
        if alpha <= 0:
            return
        border = 60
        vsurf  = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        red    = (200, 20, 20, alpha)
        pygame.draw.rect(vsurf, red, (0,                      0,      SCREEN_WIDTH, border))
        pygame.draw.rect(vsurf, red, (0, SCREEN_HEIGHT - border, SCREEN_WIDTH, border))
        pygame.draw.rect(vsurf, red, (0,                      0,      border, SCREEN_HEIGHT))
        pygame.draw.rect(vsurf, red, (SCREEN_WIDTH - border,  0,      border, SCREEN_HEIGHT))
        surface.blit(vsurf, (0, 0))

    def _draw_death(self, surface: pygame.Surface) -> None:
        fade = min(180, self._death_timer * 2)
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
        surface.blit(title, (cx - title.get_width() // 2,
                              SCREEN_HEIGHT // 2 - 140))

        # Options
        for i, opt in enumerate(self._pause_options):
            is_sel = (i == self._pause_sel)
            color  = WHITE if is_sel else GRAY
            txt    = self.font_pause_item.render(opt, True, color)
            tx     = cx - txt.get_width() // 2
            ty     = SCREEN_HEIGHT // 2 - 56 + i * 56
            surface.blit(txt, (tx, ty))
            if is_sel:
                pygame.draw.polygon(surface, GOLD, [
                    (tx - 22, ty + 17),
                    (tx - 14, ty + 9),
                    (tx - 6,  ty + 17),
                    (tx - 14, ty + 25),
                ])

        hint_font = pygame.font.SysFont("monospace", 14)
        hint = hint_font.render(
            "↑↓ Navigate   ENTER Confirm   ESC Resume", True, (50, 50, 60))
        surface.blit(hint, (cx - hint.get_width() // 2, SCREEN_HEIGHT - 38))
