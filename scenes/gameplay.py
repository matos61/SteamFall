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

import random
import pygame
from settings           import *
from scenes.base_scene  import BaseScene
from core.camera        import Camera
from core.hitstop       import hitstop
from systems.dialogue   import DialogueBox
from world.tilemap      import (TileMap,
                                LEVEL_1, LEVEL_2, LEVEL_3, LEVEL_4, LEVEL_5,
                                LEVEL_6_MARKED, LEVEL_6_FLESHFORGED,
                                LEVEL_7_MARKED, LEVEL_7_FLESHFORGED,
                                LEVEL_8_MARKED, LEVEL_8_FLESHFORGED,
                                LEVEL_9, LEVEL_10)
from entities.player       import Player
from entities.enemy        import Enemy
from entities.crawler      import Crawler
from entities.boss         import Boss
from entities.architect    import Architect
from entities.shield_guard import ShieldGuard
from entities.ranged       import Ranged
from entities.jumper       import Jumper
from systems.checkpoint import Checkpoint
from systems.collectible import SoulFragment
from systems.minimap    import MiniMap


# Scripted dialogue for The Warden boss encounter
_WARDEN_INTRO_LINES = [
    ("",            "The torches flicker. A hulking shape separates from the shadow."),
    ("The Warden",  "...Another one. They always have that same fire in their eyes."),
    ("The Warden",  "Marked or Forged — it makes no difference here. Both claim to transcend. Both break."),
    ("The Warden",  "I have guarded this threshold for thirty years. None have passed."),
    ("",            "His war-blade scrapes the stone floor. The air grows cold."),
    ("The Warden",  "Come then. Prove me wrong."),
]

# Level display names and progression chain
_LEVEL_NAMES = {
    "level_1":             "I \u2014 The Outer District",
    "level_2":             "II \u2014 The Descent",
    "level_3":             "III \u2014 The Foundry",
    "level_4":             "IV \u2014 The Ruined Spire",
    "level_5":             "V \u2014 The Sanctum",
    "level_6_marked":      "VI \u2014 The Ink Labyrinth",
    "level_6_fleshforged": "VI \u2014 The Steam Tunnels",
    "level_7_marked":      "VII \u2014 The Rune Vaults",
    "level_7_fleshforged": "VII \u2014 The Engine Room",
    "level_8_marked":      "VIII \u2014 The Sanctum Approach",
    "level_8_fleshforged": "VIII \u2014 The Forge Gate",
    "level_9":             "IX \u2014 The Convergence",
    "level_10":            "X \u2014 The Final Approach",
}
_LEVEL_DATA = {
    "level_1":             LEVEL_1,
    "level_2":             LEVEL_2,
    "level_3":             LEVEL_3,
    "level_4":             LEVEL_4,
    "level_5":             LEVEL_5,
    "level_6_marked":      LEVEL_6_MARKED,
    "level_6_fleshforged": LEVEL_6_FLESHFORGED,
    "level_7_marked":      LEVEL_7_MARKED,
    "level_7_fleshforged": LEVEL_7_FLESHFORGED,
    "level_8_marked":      LEVEL_8_MARKED,
    "level_8_fleshforged": LEVEL_8_FLESHFORGED,
    "level_9":             LEVEL_9,
    "level_10":            LEVEL_10,
}
# _LEVEL_CHAIN covers levels 1–5 and 9–10.
# Levels 6–8 use faction branching; handled by _faction_next_level().
_LEVEL_CHAIN = {
    "level_1":             "level_2",
    "level_2":             "level_3",
    "level_3":             "level_4",
    "level_4":             "level_5",
    "level_9":             "level_10",
}


def _faction_next_level(current_level: str, faction: str) -> str | None:
    """Return the next level key, resolving faction variants for levels 6-8."""
    variant = "fleshforged" if faction == FACTION_FLESHFORGED else "marked"
    if current_level == "level_5":
        return f"level_6_{variant}"
    if current_level in ("level_6_marked", "level_6_fleshforged"):
        return f"level_7_{variant}"
    if current_level in ("level_7_marked", "level_7_fleshforged"):
        return f"level_8_{variant}"
    if current_level in ("level_8_marked", "level_8_fleshforged"):
        return "level_9"
    return _LEVEL_CHAIN.get(current_level)


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

        # Spawn P2-1 enemy types
        for (gx, gy) in self.tilemap.shield_guard_spawns:
            self.enemies.append(ShieldGuard(gx, gy))
        for (rx, ry) in self.tilemap.ranged_spawns:
            self.enemies.append(Ranged(rx, ry))
        for (jx, jy) in self.tilemap.jumper_spawns:
            self.enemies.append(Jumper(jx, jy))

        # Spawn Warden boss (tile 'B')
        self._boss = None
        if self.tilemap.boss_spawn:
            bx, by = self.tilemap.boss_spawn
            boss = Boss(bx, by, name="The Warden")
            self.enemies.append(boss)
            self._boss = boss

        # Spawn Architect final boss (tile 'X')
        self._architect = None
        if self.tilemap.architect_spawn:
            ax, ay   = self.tilemap.architect_spawn
            _faction = self.game.player_faction or FACTION_MARKED
            arch     = Architect(ax, ay, faction=_faction)
            self.enemies.append(arch)
            self._architect = arch

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

        # --- Architect defeat dialogue cadence ---
        self._architect_defeat_timer = 0   # counts frames between lines
        self._architect_victory_done = False

        # Fonts
        self.font_hud       = pygame.font.SysFont("monospace", 16, bold=True)
        self.font_debug     = pygame.font.SysFont("monospace", 13)
        self.font_death     = pygame.font.SysFont("georgia",   52, bold=True)
        self.font_pause     = pygame.font.SysFont("georgia",   48)
        self.font_trans     = pygame.font.SysFont("georgia",   36)
        self.font_boss_name = pygame.font.SysFont("georgia",   14, bold=True)
        self.font_pause_opt = pygame.font.SysFont("georgia",   30)
        self.font_phase_ann = pygame.font.SysFont("georgia",   42, bold=True)

        # --- Boss intro cutscene ---
        self._boss_intro_active  = False
        self._boss_intro_done    = False
        self._boss_intro_subject = "warden"   # "warden" or "architect"
        self._boss_dialogue      = None

        # --- Phase announce banner ---
        self._boss_phase_text  = ""
        self._boss_phase_timer = 0

        # --- Screen shake ---
        self._screen_shake = 0

        # --- Phase 3 arena shrink walls ---
        self._shrink_active       = False
        self._shrink_left_x       = 0.0
        self._shrink_right_x      = float(self.tilemap.width)
        self._shrink_target_left  = 0.0
        self._shrink_target_right = float(self.tilemap.width)

    # ------------------------------------------------------------------
    # Event handling
    # ------------------------------------------------------------------

    def handle_event(self, event) -> None:
        if not self._setup_done:
            return
        if event.type != pygame.KEYDOWN:
            return

        # Boss intro freezes all other input; only SPACE/RETURN advances dialogue
        if self._boss_intro_active:
            if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                if self._boss_dialogue:
                    self._boss_dialogue.advance()
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

        # --- Boss intro: trigger then freeze while active ---
        # Warden intro
        if (self._boss and self._boss.alive
                and not self._boss_intro_done
                and not self._boss_intro_active):
            dist = abs(self.player.rect.centerx - self._boss.rect.centerx)
            if dist < BOSS_INTRO_TRIGGER_DIST:
                self._start_boss_intro()

        # Architect intro — uses same cutscene machinery but tracks _intro_done
        # on the Architect instance itself (no separate _architect_intro_done flag needed).
        if (self._architect and self._architect.alive
                and not self._architect._intro_done
                and not self._boss_intro_active):
            dist = abs(self.player.rect.centerx - self._architect.rect.centerx)
            if dist < BOSS_INTRO_TRIGGER_DIST:
                self._start_architect_intro()

        if self._boss_intro_active:
            self._tick_boss_intro()
            return

        # --- Phase announce timer ---
        if self._boss_phase_timer > 0:
            self._boss_phase_timer -= 1

        # --- Screen shake decay ---
        if self._screen_shake > 0:
            self._screen_shake -= 1

        # --- Arena shrink advance ---
        if self._shrink_active:
            if self._shrink_left_x < self._shrink_target_left:
                self._shrink_left_x = min(
                    self._shrink_left_x + ARENA_SHRINK_SPEED,
                    self._shrink_target_left)
            if self._shrink_right_x > self._shrink_target_right:
                self._shrink_right_x = max(
                    self._shrink_right_x - ARENA_SHRINK_SPEED,
                    self._shrink_target_right)

        # --- Tick hitstop FIRST ---
        hitstop.tick()

        solid = self.tilemap.get_solid_rects()
        # Inject arena shrink walls into solid rects so physics respects them
        if self._shrink_active and self._shrink_left_x > 0:
            solid = list(solid) + [
                pygame.Rect(0, 0,
                            int(self._shrink_left_x), self.tilemap.height),
                pygame.Rect(int(self._shrink_right_x), 0,
                            self.tilemap.width - int(self._shrink_right_x),
                            self.tilemap.height),
            ]

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

        # --- Ranged projectile collisions ---
        for enemy in living_enemies:
            if isinstance(enemy, Ranged):
                for proj in enemy.projectiles:
                    if proj.alive and proj.rect.colliderect(self.player.rect):
                        kdir = 1 if proj.vx > 0 else -1
                        self.player.take_damage(proj.damage, knockback_dir=kdir)
                        proj.alive = False

        # --- Touch damage: player body overlaps enemy body ---
        if self.player.iframes == 0:
            for enemy in living_enemies:
                if self.player.rect.colliderect(enemy.rect):
                    kdir = 1 if self.player.rect.centerx > enemy.rect.centerx else -1
                    self.player.take_damage(ENEMY_ATTACK_DAMAGE // 2,
                                            knockback_dir=kdir)
                    break

        # --- Collect soul fragments ---
        remaining = []
        for frag in self.fragments:
            if frag.alive and frag.rect.colliderect(self.player.rect):
                self.player._regen_resource(15)
                frag.alive = False
            if frag.alive:
                remaining.append(frag)
        self.fragments = remaining

        # --- Boss phase announce + arena shrink trigger ---
        if self._boss and self._boss.alive and self._boss.announce_phase:
            phase = self._boss.announce_phase
            self._boss.announce_phase = 0
            labels = ("", "I", "II", "III")
            suffix = " \u2014 ENRAGED" if phase == 2 else " \u2014 UNLEASHED"
            self._boss_phase_text  = f"PHASE {labels[phase]}{suffix}"
            self._boss_phase_timer = BOSS_PHASE_ANNOUNCE_FRAMES
            self._screen_shake     = 10
            if phase == 3:
                self._shrink_active       = True
                self._shrink_left_x       = 0.0
                self._shrink_right_x      = float(self.tilemap.width)
                self._shrink_target_left  = float(ARENA_SHRINK_AMOUNT)
                self._shrink_target_right = float(
                    self.tilemap.width - ARENA_SHRINK_AMOUNT)

        # --- Flush Architect-spawned minions into the main enemy list ---
        # Collect additions first so we never modify the list we're iterating.
        minion_additions = []
        for e in self.enemies:
            if isinstance(e, Architect) and hasattr(e, '_spawned_minions'):
                minion_additions.extend(e._spawned_minions)
                e._spawned_minions.clear()
        self.enemies.extend(minion_additions)

        # --- Spawn fragments from newly dead enemies + prune enemy list ---
        # Guard with hitstop check so drops spawn exactly once per kill,
        # not once per frozen frame during the hitstop window (BUG-007/BUG-011).
        if not hitstop.is_active():
            newly_dead = [e for e in self.enemies if not e.alive]
            for dead_e in newly_dead:
                for frag in dead_e.get_drop_fragments():
                    self.fragments.append(frag)

            # If the Warden boss just died, clear that reference
            if self._boss and not self._boss.alive:
                self._boss = None

            # If the Architect just died, keep the reference for defeat dialogue
            # but remove it from the active enemy list so it stops updating.
            if self._architect and not self._architect.alive:
                pass  # reference kept; pruned below

            # Prune dead enemies
            self.enemies = [e for e in self.enemies if e.alive]

        # --- Architect defeat dialogue advancement ---
        if self._architect and not self._architect.alive and not self._architect_victory_done:
            arch = self._architect
            if arch._defeat_dialogue_active:
                if arch._defeat_line_idx < len(arch._defeat_lines):
                    self._architect_defeat_timer += 1
                    if self._architect_defeat_timer >= 120:
                        self._architect_defeat_timer = 0
                        arch._defeat_line_idx += 1
                else:
                    # All lines shown; wait 2 seconds (120 frames) then write victory
                    self._architect_defeat_timer += 1
                    if self._architect_defeat_timer >= 120:
                        self._architect_victory_done = True
                        self.game.save_data["victory"] = True
                        self.game.save_data["faction"] = arch.faction
                        self.game.save_to_disk()
                        self._begin_transition(SCENE_MAIN_MENU)

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
        _faction = self.game.player_faction or FACTION_MARKED
        next_level = _faction_next_level(self._level_name, _faction)
        if self.player.alive and self.player.rect.right >= self.tilemap.width - 64:
            if next_level:
                self._begin_transition(SCENE_GAMEPLAY, level=next_level)
                return
            elif self._level_name == "level_10":
                # Architect defeated / level 10 right-edge reached: Victory!
                self.game.save_data["victory"] = True
                self.game.save_to_disk()
                self._begin_transition(SCENE_MAIN_MENU)
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
    # Boss intro cutscene
    # ------------------------------------------------------------------

    def _start_boss_intro(self) -> None:
        self._boss_intro_active = True
        self._boss_intro_subject = "warden"
        faction = self.game.player_faction or FACTION_MARKED
        self._boss_dialogue = DialogueBox(faction=faction)
        self._boss_dialogue.queue(_WARDEN_INTRO_LINES)
        # Freeze player in place
        self.player.vx = 0
        self.player.vy = 0

    def _start_architect_intro(self) -> None:
        self._boss_intro_active  = True
        self._boss_intro_subject = "architect"
        faction = self.game.player_faction or FACTION_MARKED
        self._boss_dialogue = DialogueBox(faction=faction)
        # Build DialogueBox lines from the Architect's own intro_lines list
        arch_lines = [(self._architect.name, line)
                      for line in self._architect._intro_lines]
        self._boss_dialogue.queue(arch_lines)
        self.player.vx = 0
        self.player.vy = 0

    def _tick_boss_intro(self) -> None:
        subject = getattr(self, "_boss_intro_subject", "warden")
        # Pick the active boss entity so we can tick its line counters
        active_boss = self._architect if subject == "architect" else self._boss
        if self._boss_dialogue:
            self._boss_dialogue.update()
            # Advance the entity's own intro line timer so _draw_boss_intro
            # banner stays in sync (P2-3a spec requirement).
            if active_boss:
                active_boss._intro_line_timer += 1
                if active_boss._intro_line_timer >= 120:
                    active_boss._intro_line_timer = 0
                    active_boss._intro_line_idx  += 1
                    if active_boss._intro_line_idx >= len(active_boss._intro_lines):
                        active_boss._intro_line_idx = len(active_boss._intro_lines) - 1
            if self._boss_dialogue.is_done():
                self._boss_intro_active = False
                self._boss_dialogue     = None
                if subject == "warden":
                    self._boss_intro_done = True
                    if self._boss:
                        self._boss._intro_done = True
                else:
                    if self._architect:
                        self._architect._intro_done = True

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

        # Apply screen shake by temporarily nudging camera offset
        shake_x = shake_y = 0
        if self._screen_shake > 0:
            amp     = self._screen_shake // 2 + 1
            shake_x = random.randint(-amp, amp)
            shake_y = random.randint(-amp, amp)
            self.camera.offset.x += shake_x
            self.camera.offset.y += shake_y

        # World
        self.tilemap.draw(surface, self.camera)

        # Arena shrink walls (draw as tiled columns)
        if self._shrink_active:
            self._draw_arena_walls(surface)

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

        # Restore shake offset before HUD (HUD is in screen space)
        if shake_x or shake_y:
            self.camera.offset.x -= shake_x
            self.camera.offset.y -= shake_y

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

        # Phase announce banner
        if self._boss_phase_timer > 0:
            self._draw_phase_announce(surface)

        # Boss intro: timed-text banner (P2-3a spec) + rich DialogueBox layer
        self._draw_boss_intro(surface)
        if self._boss_intro_active and self._boss_dialogue:
            self._boss_dialogue.draw(surface)

        # Architect defeat dialogue overlay
        self._draw_architect_defeat(surface)

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

        # Boss health bar — Warden
        if self._boss and self._boss.alive:
            self._draw_boss_bar(surface, self._boss)

        # Boss health bar — Architect (uses same renderer; works for any Boss subclass)
        if self._architect and self._architect.alive:
            self._draw_boss_bar(surface, self._architect)

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

        # Color by phase (handles both 3-phase Warden and 4-phase Architect)
        if boss.phase >= 4:
            bar_color = (180, 0, 60)    # Architect phase 4 — blood violet
        elif boss.phase == 3:
            bar_color = (220, 0, 0)
        elif boss.phase == 2:
            bar_color = (220, 120, 0)
        else:
            bar_color = HEALTH_COLOR

        pygame.draw.rect(surface, HEALTH_BG_COLOR, (bar_x, bar_y, bar_w, bar_h))
        filled_w = int(bar_w * max(0.0, fill))
        pygame.draw.rect(surface, bar_color, (bar_x, bar_y, filled_w, bar_h))
        pygame.draw.rect(surface, (60, 55, 75), (bar_x, bar_y, bar_w, bar_h), 1)

        # Phase threshold ticks — 4-phase boss gets 3 ticks; 3-phase gets 2
        if isinstance(boss, Architect):
            tick_fracs = (0.75, 0.50, 0.25)
        else:
            tick_fracs = (0.50, 0.25)
        for frac in tick_fracs:
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

    def _draw_arena_walls(self, surface: pygame.Surface) -> None:
        """Draw the closing arena-shrink walls as stacked tile rects."""
        def _draw_wall_column(world_rect: pygame.Rect) -> None:
            sr = self.camera.apply_rect(world_rect)
            # Clip to screen before tiling to avoid millions of off-screen draws
            visible = sr.clip(pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT))
            if visible.width <= 0 or visible.height <= 0:
                return
            pygame.draw.rect(surface, ARENA_WALL_COLOR, visible)
            # Draw top edge highlights every TILE_SIZE rows for a tiled look
            for ty in range(visible.top, visible.bottom, TILE_SIZE):
                pygame.draw.line(surface, TILE_EDGE_COLOR,
                                 (visible.left, ty), (visible.right, ty), 1)

        lw = int(self._shrink_left_x)
        rw = int(self.tilemap.width - self._shrink_right_x)
        if lw > 0:
            _draw_wall_column(pygame.Rect(0, 0, lw, self.tilemap.height))
        if rw > 0:
            _draw_wall_column(pygame.Rect(
                int(self._shrink_right_x), 0, rw, self.tilemap.height))

    def _draw_boss_intro(self, surface: pygame.Surface) -> None:
        """Draw the current boss intro line in a simple tinted banner.

        Handles both Warden (purple tint) and Architect (violet-gold tint).
        The richer DialogueBox path draws on top, but this provides a fallback.
        """
        if not self._boss_intro_active:
            return
        subject = getattr(self, "_boss_intro_subject", "warden")
        active_boss = self._architect if subject == "architect" else self._boss
        if not active_boss or active_boss._intro_done:
            return
        line_idx = active_boss._intro_line_idx
        lines    = active_boss._intro_lines
        if line_idx >= len(lines):
            return
        line = lines[line_idx]
        font = pygame.font.SysFont("georgia", 22)
        if subject == "architect":
            text_color = (255, 200, 255)   # pale violet-white
            bg_color   = (30, 5, 40)
        else:
            text_color = (220, 180, 255)
            bg_color   = (20, 10, 30)
        text = font.render(f'"{line}"', True, text_color)
        bg   = pygame.Surface((text.get_width() + 32, text.get_height() + 16))
        bg.set_alpha(180)
        bg.fill(bg_color)
        bx = SCREEN_WIDTH // 2 - bg.get_width() // 2
        by = 60
        surface.blit(bg, (bx, by))
        surface.blit(text, (bx + 16, by + 8))

    def _draw_architect_defeat(self, surface: pygame.Surface) -> None:
        """Draw faction-specific defeat dialogue lines after the Architect dies."""
        arch = self._architect
        if not arch or not arch._defeat_dialogue_active:
            return
        if arch._defeat_line_idx >= len(arch._defeat_lines):
            return
        line = arch._defeat_lines[arch._defeat_line_idx]
        font = pygame.font.SysFont("georgia", 22)
        text = font.render(f'"{line}"', True, (255, 220, 140))
        bg   = pygame.Surface((text.get_width() + 32, text.get_height() + 16))
        bg.set_alpha(180)
        bg.fill((30, 20, 5))
        bx = SCREEN_WIDTH // 2 - bg.get_width() // 2
        by = SCREEN_HEIGHT // 2 - bg.get_height() // 2
        surface.blit(bg, (bx, by))
        surface.blit(text, (bx + 16, by + 8))

    def _draw_phase_announce(self, surface: pygame.Surface) -> None:
        """Draw the phase-transition banner centred on screen."""
        frac  = self._boss_phase_timer / BOSS_PHASE_ANNOUNCE_FRAMES
        alpha = min(255, int(frac * 510))   # fade in fast, fade out slow
        if alpha <= 0:
            return
        color = (220, 60, 60) if "UNLEASHED" in self._boss_phase_text else (220, 140, 40)
        txt   = self.font_phase_ann.render(self._boss_phase_text, True, color)
        txt.set_alpha(alpha)
        surface.blit(txt, (SCREEN_WIDTH // 2 - txt.get_width() // 2,
                           SCREEN_HEIGHT // 2 - 80))

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
