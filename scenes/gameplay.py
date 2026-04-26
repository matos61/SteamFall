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
from systems.collectible import SoulFragment, HeatCore, SoulShard, AbilityOrb, LoreItem
from systems.minimap    import MiniMap
from entities.npc       import NPC


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


# Lore item text indexed by (level_name, lore_index).  Index matches the order
# 'L' tiles appear in each level string (top-to-bottom, left-to-right).
_LORE_TEXT: dict[tuple, tuple[str, str]] = {
    ("level_2", 0): ("lore_foundry_plaque",
                     "'YIELD PER SOUL: 0.04 KW-hr. DAILY EXTRACTION QUOTA: 400 SOULS. — FORGEMASTER DIRECTORATE'"),
    ("level_2", 1): ("lore_marked_inscription",
                     "'The second Rite requires a willing vessel. Kael volunteered before we could ask.'"),
    ("level_4", 0): ("lore_warden_sigil",
                     "'THRESHOLD GUARDIAN — UNIT 01. COMMAND: HOLD. OVERRIDE: NONE.'"),
    ("level_4", 1): ("lore_architects_note",
                     "'If the fanatics reach the vault, kill the lattice. Better silence than their Rite. — The Architect'"),
    ("level_5", 0): ("lore_miners_diary",
                     "'Day 47. The ink spreads up my left arm now. Foreman says I'm lucky. Lucky.'"),
    ("level_9", 0): ("lore_convergence_wall",
                     "'THEY MEET HERE. THEY ALWAYS MEET HERE. DO NOT STAY.'"),
    ("level_9", 1): ("lore_final_door",
                     "'The Founder passed through this door 200 years ago. No one followed. Something came out.'"),
}


# NPC dialogue lines keyed by (level_name, npc_index).
# Each value is a list of (speaker, text) tuples shown when the player talks to that NPC.
_NPC_DIALOGUE = {
    ("level_3", 0): [
        ("Survivor", "I've been hiding here since the Rite went wrong. The Marked sealed the tunnels."),
        ("Survivor", "I heard the machines stop last night. Haven't heard that in years."),
    ],
    ("level_5", 0): [
        ("Warden's Herald", "The Warden protects the threshold. It does not reason. It does not tire."),
        ("Warden's Herald", "Turn back, or be unmade."),
    ],
}


def _level_faction_tint(level_name: str) -> str:
    """Return the faction tint string for enemies in the given level (P3-2).

    Marked-branch levels 6-8 are infested with Fleshforged enemies (iron-orange).
    Fleshforged-branch levels 6-8 are infested with Marked enemies (acolyte purple).
    All other levels use no tint.
    """
    if level_name in ("level_6_marked", "level_7_marked", "level_8_marked"):
        return FACTION_FLESHFORGED
    if level_name in ("level_6_fleshforged", "level_7_fleshforged", "level_8_fleshforged"):
        return FACTION_MARKED
    return ""


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


def _apply_upgrade_to_player(player, upg_id: str,
                             save_upgrades: list | None = None) -> None:
    """Apply a single upgrade to a Player instance. Called on collection and on level load.

    save_upgrades is the full list from save_data["upgrades"]; used to enforce stack caps.
    """
    if upg_id == "hp":
        player.max_health            += UPGRADE_HP_BONUS
        player.health                 = min(player.health + UPGRADE_HP_BONUS,
                                            player.max_health)
    elif upg_id == "dmg":
        # P2-8: skip if already at max stacks
        if save_upgrades is not None:
            existing = sum(1 for u in save_upgrades if u == "dmg")
            if existing > UPGRADE_DMG_MAX_STACKS:
                return
        player.attack_damage_bonus   += UPGRADE_DMG_BONUS
    elif upg_id == "res":
        player.max_resource_bonus    += UPGRADE_RES_BONUS
        player._res_regen_bonus      += UPGRADE_RES_REGEN_BONUS   # P2-8: speed up passive regen


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
        _respawn = save.get("checkpoint_pos") and save.get("respawn")
        if _respawn:
            cx, cy = save["checkpoint_pos"]
            self.player = Player(cx, cy, faction=faction)
            save["respawn"] = False
        else:
            px, py = self.tilemap.player_spawn
            self.player = Player(px, py, faction=faction)

        # Apply saved upgrades before setting respawn health so max_health is correct
        _saved_upgrades = save.get("upgrades", [])
        for upg in _saved_upgrades:
            _apply_upgrade_to_player(self.player, upg, save_upgrades=_saved_upgrades)

        # Restore ability unlock state from save (BUG-019)
        self.player.ability_slots = save.get("ability_slots", ABILITY_SLOTS_DEFAULT)

        if _respawn:
            self.player.health = int(
                save.get("checkpoint_health_frac", 1.0) * self.player.max_health)

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
            arch     = Architect(ax, ay, faction=_faction,
                                 level_width=self.tilemap.width,
                                 level_floor_y=self.tilemap.height - TILE_SIZE * 2)
            self.enemies.append(arch)
            self._architect = arch

        # P3-2: Apply faction tint to spawned enemies for themed levels (skip bosses)
        _tint = _level_faction_tint(level_name)
        if _tint:
            for e in self.enemies:
                if not isinstance(e, (Boss, Architect)):
                    e.faction_tint = _tint

        # Checkpoints
        self.checkpoints: list[Checkpoint] = list(self.tilemap.checkpoints)

        # Ability orbs (BUG-019)
        self.ability_orbs: list[AbilityOrb] = [
            AbilityOrb(ax, ay)
            for (ax, ay) in self.tilemap.ability_orb_spawns
        ]

        # Soul fragments (neutral resource orbs)
        self.fragments: list[SoulFragment] = []

        # Faction-specific drops: HeatCore (Fleshforged) or SoulShard (Marked)
        # Kept separate from fragments because their collect() takes (player, game).
        self.drops: list = []

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

        # --- NPCs (P3-4) ---
        self.npcs: list[NPC] = []
        for idx, (nx, ny) in enumerate(self.tilemap.npc_spawns):
            lines = _NPC_DIALOGUE.get((level_name, idx), [])
            self.npcs.append(NPC(nx, ny, lines=lines))
        self._npc_dialogue: DialogueBox | None = None

        # --- Lore items (P3-5) ---
        lore_found = self.game.save_data.get("lore_found", [])
        self.lore_items: list[LoreItem] = []
        for idx, (lx, ly) in enumerate(self.tilemap.lore_spawns):
            entry = _LORE_TEXT.get((level_name, idx))
            if entry is None:
                continue
            lore_id, text = entry
            if lore_id not in lore_found:
                self.lore_items.append(LoreItem(lx, ly, lore_id, text))
        self._lore_text   = ""
        self._lore_timer  = 0
        self._lore_font   = pygame.font.SysFont("georgia", 22)

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

        # --- P2-5: Upgrade selection ---
        self._upgrade_active   = False
        self._upgrade_pending  = False
        self._upgrade_sel      = 0
        self._upgrade_choices  = []   # list of (upg_id, name, description)

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

        # Upgrade selection intercepts all input until a choice is made
        if self._upgrade_active:
            if event.key in (pygame.K_UP, pygame.K_w):
                self._upgrade_sel = (self._upgrade_sel - 1) % len(self._upgrade_choices)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self._upgrade_sel = (self._upgrade_sel + 1) % len(self._upgrade_choices)
            elif event.key == pygame.K_RETURN:
                upg_id = self._upgrade_choices[self._upgrade_sel][0]
                self._confirm_upgrade(upg_id)
            return

        # Boss intro freezes all other input; only SPACE/RETURN advances dialogue
        if self._boss_intro_active:
            if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                if self._boss_dialogue:
                    self._boss_dialogue.advance()
            return

        # Architect defeat dialogue: SPACE/RETURN advances the line immediately
        if (self._architect and not self._architect.alive
                and not self._architect_victory_done
                and self._architect._defeat_dialogue_active):
            if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                arch = self._architect
                if arch._defeat_line_idx < len(arch._defeat_lines):
                    arch._defeat_line_idx += 1
                    self._architect_defeat_timer = 0
            return

        # NPC dialogue intercepts SPACE/RETURN until the box is dismissed
        if self._npc_dialogue is not None:
            if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self._npc_dialogue.advance()
                if self._npc_dialogue.is_done():
                    self._npc_dialogue = None
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
            # E key: interact with nearest in-range NPC (P3-4)
            if event.key == pygame.K_e:
                for npc in self.npcs:
                    if npc._show_hint and npc.lines:
                        faction = self.game.player_faction or FACTION_MARKED
                        self._npc_dialogue = DialogueBox(faction=faction)
                        self._npc_dialogue.queue(npc.lines)
                        break

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

        # --- NPC dialogue freezes game logic; tick the dialogue box ---
        if self._npc_dialogue is not None:
            self._npc_dialogue.update()
            for npc in self.npcs:
                npc._show_hint = False
            return

        # --- Upgrade selection screen freezes game logic ---
        if self._upgrade_active:
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
        # Inject arena shrink walls into solid rects so physics respects them.
        # BUG-025: left and right walls are injected independently so the right
        # wall is solid on the first frame of phase transition even when the left
        # wall hasn't started moving yet.
        if self._shrink_active:
            _extra_walls = []
            if self._shrink_left_x > 0:
                _extra_walls.append(
                    pygame.Rect(0, 0, int(self._shrink_left_x), self.tilemap.height))
            if self._shrink_right_x < self.tilemap.width:
                _extra_walls.append(
                    pygame.Rect(int(self._shrink_right_x), 0,
                                self.tilemap.width - int(self._shrink_right_x),
                                self.tilemap.height))
            if _extra_walls:
                solid = list(solid) + _extra_walls

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

            # --- Spike damage: player overlapping any spike tile ---
            if self.player.alive and self.player.iframes == 0:
                for spike_rect in self.tilemap.spike_tiles:
                    if self.player.rect.colliderect(spike_rect):
                        self.player.take_damage(SPIKE_DAMAGE)
                        break

            # --- Crumble tile logic ---
            for tile_dict in self.tilemap.crumble_tiles:
                t_rect = tile_dict['rect']
                state  = tile_dict['state']

                if state == 'solid':
                    # Check if player is standing on this tile's top edge
                    player_on = (
                        self.player.on_ground
                        and abs(self.player.rect.bottom - t_rect.top) <= 2
                        and self.player.rect.right > t_rect.left
                        and self.player.rect.left  < t_rect.right
                    )
                    if player_on:
                        tile_dict['timer'] += 1
                        if tile_dict['timer'] >= CRUMBLE_STAND_FRAMES:
                            # Tile falls: remove from solid set
                            tile_dict['state'] = 'falling'
                            tile_dict['timer'] = 0
                            if t_rect in self.tilemap.tiles:
                                self.tilemap.tiles.remove(t_rect)
                    else:
                        # Reset timer when player steps off
                        if tile_dict['timer'] > 0:
                            tile_dict['timer'] = max(0, tile_dict['timer'] - 1)

                elif state == 'falling':
                    tile_dict['timer'] += 1
                    if tile_dict['timer'] >= CRUMBLE_RESPAWN_FRAMES:
                        # Tile respawns: add back to solid set
                        tile_dict['state'] = 'solid'
                        tile_dict['timer'] = 0
                        if t_rect not in self.tilemap.tiles:
                            self.tilemap.tiles.append(t_rect)

            # Soul fragments
            for frag in self.fragments:
                frag.update()

            # Faction drops (HeatCore / SoulShard)
            for drop in self.drops:
                drop.update()

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

        # --- Collect faction drops (HeatCore / SoulShard) ---
        remaining_drops = []
        for drop in self.drops:
            if drop.alive and drop.rect.colliderect(self.player.rect):
                drop.collect(self.player, self.game)
            if drop.alive:
                remaining_drops.append(drop)
        self.drops = remaining_drops

        # --- Collect ability orbs (BUG-019) ---
        remaining_orbs = []
        for orb in self.ability_orbs:
            orb.update()
            if orb.alive and orb.rect.colliderect(self.player.rect):
                orb.collect(self.player, self.game)
            if orb.alive:
                remaining_orbs.append(orb)
        self.ability_orbs = remaining_orbs

        # --- Lore item collection (P3-5) ---
        remaining_lore = []
        for item in self.lore_items:
            item.update()
            if item.alive and item.rect.colliderect(self.player.rect):
                result = item.collect(self.player, self.game)
                if result:
                    self._lore_text  = result
                    self._lore_timer = LORE_DISPLAY_FRAMES
            if item.alive:
                remaining_lore.append(item)
        self.lore_items = remaining_lore
        if self._lore_timer > 0:
            self._lore_timer -= 1

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

        # --- Architect phase announce + arena shrink trigger (BUG-021) ---
        if self._architect and self._architect.alive and self._architect.announce_phase:
            phase = self._architect.announce_phase
            self._architect.announce_phase = 0
            labels = ("", "I", "II", "III", "IV")
            suffixes = {2: " \u2014 AWAKENED", 3: " \u2014 UNBOUND", 4: " \u2014 ABSOLUTE"}
            suffix = suffixes.get(phase, "")
            self._boss_phase_text  = f"PHASE {labels[phase]}{suffix}"
            self._boss_phase_timer = BOSS_PHASE_ANNOUNCE_FRAMES
            self._screen_shake     = 10
            if phase == 4:
                self._shrink_active       = True
                self._shrink_left_x       = 0.0
                self._shrink_right_x      = float(self.tilemap.width)
                self._shrink_target_left  = float(ARENA_SHRINK_AMOUNT)
                self._shrink_target_right = float(
                    self.tilemap.width - ARENA_SHRINK_AMOUNT)

        # --- Flush Architect-spawned minions into the main enemy list ---
        # P2-8: enforce crawler cap of 2 live Crawlers in the arena at once.
        # Collect additions first so we never modify the list we're iterating.
        minion_additions = []
        for e in self.enemies:
            if isinstance(e, Architect) and hasattr(e, '_spawned_minions'):
                minion_additions.extend(e._spawned_minions)
                e._spawned_minions.clear()
        if minion_additions:
            live_crawlers = sum(1 for e in self.enemies
                                if isinstance(e, Crawler) and e.alive)
            for minion in minion_additions:
                if isinstance(minion, Crawler):
                    if live_crawlers < 2:
                        self.enemies.append(minion)
                        live_crawlers += 1
                    # else: cap reached; discard this minion
                else:
                    self.enemies.append(minion)

        # --- Spawn drops from newly dead enemies + prune enemy list ---
        # Guard with hitstop check so drops spawn exactly once per kill,
        # not once per frozen frame during the hitstop window (BUG-007/BUG-011).
        if not hitstop.is_active():
            newly_dead = [e for e in self.enemies if not e.alive]
            for dead_e in newly_dead:
                for drop in dead_e.get_drop_fragments():
                    if isinstance(drop, (HeatCore, SoulShard)):
                        self.drops.append(drop)
                    else:
                        self.fragments.append(drop)

            # If the Warden boss just died, trigger upgrade selection
            if self._boss and not self._boss.alive:
                self._boss = None
                self._upgrade_pending = True

            # If the Architect just died, keep the reference for defeat dialogue
            # but remove it from the active enemy list so it stops updating.
            if self._architect and not self._architect.alive:
                pass  # reference kept; pruned below

            # Prune dead enemies
            self.enemies = [e for e in self.enemies if e.alive]

        # --- Activate upgrade selection screen after boss kill ---
        if self._upgrade_pending:
            self._upgrade_pending = False
            self._setup_upgrade_choices()
            return

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
                    # All lines shown; wait 2 seconds (120 frames) then trigger ending
                    self._architect_defeat_timer += 1
                    if self._architect_defeat_timer >= 120:
                        self._architect_victory_done = True
                        self.game.save_data["victory"] = True
                        self.game.save_data["faction"] = arch.faction
                        self.game.save_to_disk()
                        # P3-3: go to faction-specific ending scene
                        ending = (SCENE_MARKED_ENDING
                                  if (self.game.player_faction or FACTION_MARKED)
                                  == FACTION_MARKED
                                  else SCENE_FLESHFORGED_ENDING)
                        self._begin_transition(ending)

        # --- NPC proximity hints (P3-4) ---
        for npc in self.npcs:
            dist_x = abs(self.player.rect.centerx - npc.rect.centerx)
            dist_y = abs(self.player.rect.centery - npc.rect.centery)
            npc._show_hint = dist_x < NPC_INTERACT_DIST and dist_y < NPC_INTERACT_DIST

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
                # P3-1: leaving level_3 triggers a faction mid-game lore cutscene
                if self._level_name == "level_3":
                    faction_scene = (SCENE_MARKED_PROLOGUE
                                     if _faction == FACTION_MARKED
                                     else SCENE_FLESHFORGED_PROLOGUE)
                    beat = (MARKED_LORE_BEAT_START
                            if _faction == FACTION_MARKED
                            else FLESHFORGED_LORE_BEAT_START)
                    self._begin_transition(faction_scene,
                                           beat_start=beat,
                                           return_level="level_4")
                else:
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
        active_boss = self._architect if subject == "architect" else self._boss
        if self._boss_dialogue:
            self._boss_dialogue.update()
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

        # Environmental hazards
        self._draw_hazards(surface)

        # Arena shrink walls (draw as tiled columns)
        if self._shrink_active:
            self._draw_arena_walls(surface)

        # Checkpoints
        for cp in self.checkpoints:
            cp.draw(surface, self.camera)

        # Soul fragments
        for frag in self.fragments:
            frag.draw(surface, self.camera)

        # Faction drops (HeatCore / SoulShard)
        for drop in self.drops:
            drop.draw(surface, self.camera)

        # Ability orbs
        for orb in self.ability_orbs:
            orb.draw(surface, self.camera)

        # Lore items (P3-5)
        for item in self.lore_items:
            item.draw(surface, self.camera)

        # Entities
        for enemy in self.enemies:
            enemy.draw(surface, self.camera)
        # NPCs (P3-4)
        for npc in self.npcs:
            npc.draw(surface, self.camera)
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

        # NPC dialogue overlay (P3-4)
        if self._npc_dialogue is not None:
            self._npc_dialogue.draw(surface)

        # Lore text overlay (P3-5)
        if self._lore_timer > 0:
            self._draw_lore_overlay(surface)

        # Upgrade selection overlay
        if self._upgrade_active:
            self._draw_upgrade_screen(surface)

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

    def _draw_hazards(self, surface: pygame.Surface) -> None:
        """Draw spike tiles as triangles and crumble tiles as colored rects."""
        # --- Spike tiles: row of small upward triangles ---
        for spike_rect in self.tilemap.spike_tiles:
            sr = self.camera.apply_rect(spike_rect)
            if (sr.right < 0 or sr.left > SCREEN_WIDTH or
                    sr.bottom < 0 or sr.top > SCREEN_HEIGHT):
                continue
            # Draw 3 triangle spikes evenly spaced across the tile width
            spike_w = sr.width // 3
            for i in range(3):
                tx = sr.left + i * spike_w
                # Triangle: base across the bottom, tip at the top-centre
                tip_x   = tx + spike_w // 2
                base_y  = sr.bottom
                tip_y   = sr.top + 4
                left_x  = tx + 2
                right_x = tx + spike_w - 2
                pygame.draw.polygon(surface, SPIKE_COLOR,
                                    [(left_x, base_y), (right_x, base_y),
                                     (tip_x, tip_y)])

        # --- Crumble tiles: colored rect, crack line in warning state ---
        for tile_dict in self.tilemap.crumble_tiles:
            state  = tile_dict['state']
            if state == 'falling':
                continue   # Tile is gone; nothing to draw
            t_rect = tile_dict['rect']
            sr     = self.camera.apply_rect(t_rect)
            if (sr.right < 0 or sr.left > SCREEN_WIDTH or
                    sr.bottom < 0 or sr.top > SCREEN_HEIGHT):
                continue
            timer = tile_dict['timer']
            in_warning = (state == 'solid'
                          and timer > CRUMBLE_STAND_FRAMES * 0.6)
            color = CRUMBLE_WARNING_COLOR if in_warning else CRUMBLE_COLOR
            pygame.draw.rect(surface, color, sr)
            # Top edge highlight (matches normal tile style)
            pygame.draw.line(surface, (180, 160, 100),
                             sr.topleft, sr.topright, 2)
            if in_warning:
                # Diagonal crack line across the tile
                pygame.draw.line(surface, (80, 60, 30),
                                 (sr.left + 4,  sr.top + 4),
                                 (sr.right - 4, sr.bottom - 4), 2)

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
        # BUG-022: drive banner index from DialogueBox so it stays in sync with
        # the player pressing SPACE to advance, rather than a separate 120-frame timer.
        line_idx = self._boss_dialogue._index if self._boss_dialogue else 0
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
        hint_font = pygame.font.SysFont("monospace", 13)
        hint = hint_font.render("SPACE — continue", True, (180, 160, 100))
        surface.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2,
                            by + bg.get_height() + 6))

    def _draw_lore_overlay(self, surface: pygame.Surface) -> None:
        """Draw the collected lore text as a fading centred text box (P3-5)."""
        if self._lore_timer <= 0 or not self._lore_text:
            return
        # Fade out over the last 60 frames
        if self._lore_timer <= 60:
            alpha = int(255 * self._lore_timer / 60)
        else:
            alpha = 200
        max_w  = SCREEN_WIDTH * 3 // 4
        words  = self._lore_text.split()
        lines  = []
        line   = ""
        for word in words:
            test = (line + " " + word).strip()
            if self._lore_font.size(test)[0] <= max_w:
                line = test
            else:
                if line:
                    lines.append(line)
                line = word
        if line:
            lines.append(line)
        line_h  = self._lore_font.get_height() + 4
        pad     = 16
        box_w   = max_w + pad * 2
        box_h   = len(lines) * line_h + pad * 2
        box_x   = (SCREEN_WIDTH  - box_w) // 2
        box_y   = SCREEN_HEIGHT  // 2 - box_h // 2
        bg_surf = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        bg_surf.fill((10, 8, 5, min(200, alpha)))
        surface.blit(bg_surf, (box_x, box_y))
        color = LORE_ITEM_COLOR
        for i, ln in enumerate(lines):
            rendered = self._lore_font.render(ln, True, color)
            rendered.set_alpha(alpha)
            surface.blit(rendered, (box_x + pad, box_y + pad + i * line_h))

    def _draw_phase_announce(self, surface: pygame.Surface) -> None:
        """Draw the phase-transition banner centred on screen."""
        frac  = self._boss_phase_timer / BOSS_PHASE_ANNOUNCE_FRAMES
        alpha = min(255, int(frac * 510))   # fade in fast, fade out slow
        if alpha <= 0:
            return
        color = (220, 60, 60) if ("UNLEASHED" in self._boss_phase_text or "ABSOLUTE" in self._boss_phase_text) else (220, 140, 40)
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

    # ------------------------------------------------------------------
    # P2-5: Upgrade system
    # ------------------------------------------------------------------

    def _setup_upgrade_choices(self) -> None:
        if not self.player.alive:
            return
        faction   = self.game.player_faction or FACTION_MARKED
        res_label = "Soul" if faction == FACTION_MARKED else "Heat"
        self._upgrade_choices = [
            ("hp",  "Heart of Iron",   f"+{UPGRADE_HP_BONUS} Max HP"),
            ("dmg", "Sharpened Edge",  f"+{UPGRADE_DMG_BONUS} Attack Damage"),
            ("res", "Reservoir Surge", f"+{UPGRADE_RES_BONUS} Max {res_label}"),
        ]
        self._upgrade_sel    = 0
        self._upgrade_active = True

    def _confirm_upgrade(self, upg_id: str) -> None:
        upgs = self.game.save_data.setdefault("upgrades", [])
        # P2-8: enforce DMG stack cap — silently skip if already at max stacks
        if upg_id == "dmg":
            existing = sum(1 for u in upgs if u == "dmg")
            if existing >= UPGRADE_DMG_MAX_STACKS:
                self._upgrade_active = False
                return
        upgs.append(upg_id)
        self.game.save_to_disk()
        _apply_upgrade_to_player(self.player, upg_id, save_upgrades=upgs)
        self._upgrade_active = False

    def _draw_upgrade_screen(self, surface: pygame.Surface) -> None:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        cx     = SCREEN_WIDTH // 2
        faction = self.game.player_faction or FACTION_MARKED
        accent  = MARKED_COLOR if faction == FACTION_MARKED else FLESHFORGED_COLOR

        # Title
        title = self.font_phase_ann.render("UPGRADE UNLOCKED", True, GOLD)
        surface.blit(title, (cx - title.get_width() // 2, 160))

        sub = self.font_hud.render("Choose one permanent upgrade:", True, (170, 160, 190))
        surface.blit(sub, (cx - sub.get_width() // 2, 222))

        # Option boxes
        box_w, box_h, spacing = 400, 70, 88
        start_y = 268
        for i, (upg_id, name, desc) in enumerate(self._upgrade_choices):
            bx     = cx - box_w // 2
            by     = start_y + i * spacing
            is_sel = (i == self._upgrade_sel)

            box_surf = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
            box_surf.fill((*accent, 70) if is_sel else (20, 18, 30, 140))
            surface.blit(box_surf, (bx, by))
            border_color = accent if is_sel else (60, 55, 75)
            pygame.draw.rect(surface, border_color, (bx, by, box_w, box_h),
                             2 if is_sel else 1)

            if is_sel:
                mid_y = by + box_h // 2
                pygame.draw.polygon(surface, GOLD, [
                    (bx - 18, mid_y),
                    (bx - 10, mid_y - 8),
                    (bx - 2,  mid_y),
                    (bx - 10, mid_y + 8),
                ])

            name_surf = self.font_pause_opt.render(name, True, WHITE if is_sel else GRAY)
            surface.blit(name_surf, (bx + 16, by + 8))

            desc_surf = self.font_debug.render(desc, True, (180, 175, 200))
            surface.blit(desc_surf, (bx + 16, by + box_h - 22))

        hint = self.font_debug.render(
            "\u2191\u2193 Navigate   ENTER Confirm", True, (50, 50, 60))
        surface.blit(hint, (cx - hint.get_width() // 2, SCREEN_HEIGHT - 38))
