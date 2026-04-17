# Steamfall — Development Roadmap

## Storyboard Summary

Steamfall is a 2D Metroidvania-style platformer built around a philosophical schism between two factions competing for "transcendence":

**The Marked** are the Church of Runes — a secretive mystical order that transcends the body through arcane tattoos and soul energy. Their worldview holds that the physical form is merely a vessel; true power comes from insight, sacrifice, and communion with ancient rune-scripts. Players who choose this path gain Soul Surge (area burst) and regenerate soul resource by landing attacks.

**The Fleshforged** are military-industrial augmenters — they believe the soul is chemical, the body a machine to be optimized. Power is built, not gifted. Players who choose this path gain Overdrive (speed+damage boost) and use Heat as their resource, supplied by mechanical mods.

The player is an orphan/miner survivor whose closest companion (Kael for Marked, Sera for Fleshforged) sacrifices themselves so the player can undergo their faction's transformative rite. The player then awakens into a world under threat, tasked with surviving and ultimately confronting whatever power shattered the ceremony's ritual — presumably a boss tied to the opposing faction or an ancient third power.

---

## What Is Built (v0.1)

- **Window and game loop** (`main.py`, `core/game.py`): Pygame window at 1280x720, 60fps clock, clean scene-switching via `game.change_scene()`.
- **Scene manager**: All scenes registered at startup, `on_enter(**kwargs)` pattern for passing data between scenes without globals.
- **Main menu** (`scenes/main_menu.py`): Animated title with pulsing glow, UP/DOWN navigation, ENTER to confirm, "Begin" / "Quit" options.
- **Faction select** (`scenes/faction_select.py`): Side-by-side panels for The Marked (purple) and Fleshforged (orange), LEFT/RIGHT to choose, ENTER to confirm, ESC to go back.
- **Marked prologue** (`scenes/marked_prologue.py`): 21-beat story sequence with scrolling dialogue, per-beat background color, fade-in transitions, ESC to skip.
- **Fleshforged prologue** (`scenes/fleshforged_prologue.py`): 22-beat equivalent for the Fleshforged path.
- **Dialogue box system** (`systems/dialogue.py`): Faction-colored border, scrolling character reveal, SPACE to advance or skip-to-end, text wrapping, speaker label rendering.
- **Gameplay scene** (`scenes/gameplay.py`): Full platformer loop — player update, enemy AI, physics, combat, camera follow, HUD draw, death screen, pause overlay, level-1→level-2 transition trigger, checkpoint-respawn logic.
- **Camera** (`core/camera.py`): Smooth lerp follow with world-edge clamping, `apply()` / `apply_rect()` / `apply_point()` helpers.
- **Hit-stop** (`core/hitstop.py`): Singleton freeze-frame system; 1-frame white flash overlay on hit; `trigger()`, `is_active()`, `tick()`, `consume_flash()` API.
- **Base entity** (`entities/entity.py`): Float position + integer Rect, health/iframes/alive/facing, `take_damage()`, `heal()`, `die()`, default colored-rect draw with iframe flicker and health bar.
- **Player** (`entities/player.py`): Full movement with coyote time (6 frames), jump buffer (8 frames), variable jump height; melee attack (Z/J) with forward hitbox; faction abilities (Soul Surge / Overdrive, X/K); passive resource regen; animation state machine integration; overdrive orange glow; attack arc visual.
- **Basic enemy** (`entities/enemy.py`): Three-state AI (PATROL / CHASE / ATTACK), patrol range, sight range, melee attack with hitbox, per-frame hitbox debug outlines.
- **Animation controller** (`systems/animation.py`): States (idle/walk/jump/fall/attack/hurt/death), per-state frame counts and FPS, placeholder colored-surface frames with brightness variation, state transitions without mid-animation reset.
- **Physics** (`systems/physics.py`): Gravity + terminal velocity; separate X/Y AABB tile collision resolving horizontal then vertical; `on_ground` flag set on landing.
- **Combat** (`systems/combat.py`): `AttackHitbox` with damage, knockback, duration, already-hit tracking; hitstop trigger on hit.
- **HUD** (`scenes/gameplay.py`): Health bar, resource bar (soul/heat), 5-pip ability cooldown display, faction tag, checkpoint indicator (diamond top-right), control-hint footer.
- **Tile map** (`world/tilemap.py`): ASCII level format (`#` = solid, `P` = player spawn, `E` = enemy spawn), camera-culled tile rendering with top-edge highlight; LEVEL_1 defined.
- **Settings** (`settings.py`): Centralized constants for screen, colors, physics, player stats, enemy stats, tiles, dialogue, scene names, faction keys.

---

## What Is In Progress

- **`entities/crawler.py`**: Referenced in `gameplay.py` (`from entities.crawler import Crawler`) and `tilemap.crawler_spawns`, but the file does not exist. The level format comment mentions `'c'` as a tile type but `_parse()` does not handle it.
- **`systems/checkpoint.py`**: Referenced in `gameplay.py` (`from systems.checkpoint import Checkpoint`) and `tilemap.checkpoints`, but the file does not exist. `TileMap._parse()` also has no `'C'` tile handler to produce `self.checkpoints`.
- **`systems/collectible.py`**: Referenced in `gameplay.py` (`from systems.collectible import SoulFragment`) and `enemy.get_drop_fragments()`, but the file does not exist. Enemy has no `get_drop_fragments()` method.
- **`LEVEL_2`**: Imported in `gameplay.py` (`from world.tilemap import TileMap, LEVEL_1, LEVEL_2`) but not defined in `tilemap.py`.
- **`CHECKPOINT_GLOW_COLOR`**: Used in `gameplay.py` `_draw_checkpoint_indicator()` but not defined in `settings.py`.
- **Animation controller** is built and integrated, but the player draw method uses `self._anim.current_frame` while the original `entity.py` draw still draws a plain rect — enemies still render as rectangles only.
- **`_update_animation()`** in `player.py` calls `self._anim.set_state()` and `update()` but the "hurt" and "death" states are selected but never consumed — player draw does not call `anim.current_frame` for hurt state (it redraws the rect with an outline instead).
- **Pause menu** (`_draw_pause`): Shows "PAUSED" text and two hints, but ESC just toggles `_paused` bool with no actual menu (no "Return to Main Menu" button with navigation, no Settings stub).
- **Level transition**: Triggers correctly on reaching the right edge of level 1, but there is no visual transition effect (no fade, no level name overlay).

---

## Phase 1 — Core Loop Complete ✅

All Phase 1 tasks are complete as of 2026-04-17. The game launches without ImportError and has a playable loop through five levels with save/load, a boss, a map, and proper UI.

---

### Task P1-1: Fix Missing Imports — Crawler, Checkpoint, SoulFragment, LEVEL_2, CHECKPOINT_GLOW_COLOR ✅ DONE

**Files to touch:**
- `entities/crawler.py` (create)
- `systems/checkpoint.py` (create)
- `systems/collectible.py` (create)
- `world/tilemap.py` (extend)
- `settings.py` (add constant)

**What to build:**

`settings.py`: Add `CHECKPOINT_GLOW_COLOR = (200, 200, 80)` (yellow-white glow).

`entities/crawler.py`: A `Crawler(Enemy)` subclass. Crawlers are smaller (28×22 px), faster patrol (speed 2.5), low health (30), and hug the floor. They should be colored `(120, 35, 35)`. Override `__init__` to set dimensions and stats; inherit all AI logic from `Enemy`.

`systems/checkpoint.py`: `Checkpoint` class. Constructor takes `(x, y)`. Attributes: `rect` (16×32 px, feet at y), `activated=False`. Method `update(player, game, faction)`: if `player.rect.colliderect(self.rect)` and not activated, set `activated=True`, write `game.save_data["checkpoint_pos"] = (rect.centerx, rect.top)`, `game.save_data["checkpoint_level"] = current_level` (pass level name into constructor), `game.save_data["checkpoint_health_frac"] = 1.0`. Method `draw(surface, camera)`: draw a 6×24 px pillar with a 12×8 px top gem; use `CHECKPOINT_GLOW_COLOR` when activated, `GRAY` otherwise.

`systems/collectible.py`: `SoulFragment` class. Constructor `(x, y)`. Attributes: `rect` (10×10 px), `alive=True`, `_bob_timer=0`. Method `update()`: increment `_bob_timer`, offset `rect.y` by `sin(_bob_timer * 0.08) * 3`. Method `draw(surface, camera)`: draw a small diamond shape using `SOUL_COLOR`. Enemy base class in `entities/enemy.py` needs `get_drop_fragments()` added: return a list with one `SoulFragment` at `self.rect.center` (import guard to avoid circular imports).

`world/tilemap.py`:
- Add `LEVEL_2` (see Task P1-4 for level data).
- Extend `TileMap.__init__` to also set `self.crawler_spawns: list = []` and `self.checkpoints: list = []`.
- In `_parse()`, add handlers: `'c'` → append to `self.crawler_spawns` (same offset calc as `'E'`); `'C'` → append a `Checkpoint(x, y - 64, level_name="level_N")` to `self.checkpoints` (pass level name via TileMap constructor parameter defaulting to `"level_1"`).
- Update `TileMap.__init__` signature to accept `level_name: str = "level_1"` and store it for checkpoint creation.

**Acceptance criteria — done when:**
- `python main.py` launches without ImportError.
- Crawlers spawn at `'c'` tile positions.
- Touching a checkpoint glows it and saves `checkpoint_pos` in `game.save_data`.
- Dying with an active checkpoint respawns at the checkpoint (existing respawn logic in gameplay.py already handles this).
- `CHECKPOINT_GLOW_COLOR` renders without NameError.

---

### Task P1-2: Boss Fight Framework ✅ DONE

**Files to touch:**
- `entities/boss.py` (create)
- `world/tilemap.py` (add boss spawn tile `'B'`)
- `scenes/gameplay.py` (spawn boss, draw boss health bar)
- `settings.py` (add boss constants)

**What to build:**

`settings.py`:
```
BOSS_MAX_HEALTH     = 400
BOSS_PHASE2_THRESH  = 0.50   # Fraction of max health when phase 2 starts
BOSS_PHASE3_THRESH  = 0.25
BOSS_BAR_HEIGHT     = 18
BOSS_BAR_Y          = SCREEN_HEIGHT - 38
BOSS_BAR_MARGIN     = 80
```

`entities/boss.py`: `Boss(Enemy)` class.
- `__init__(x, y, name="??")`: call `super().__init__(x, y, patrol_range=0, color=(80, 20, 120))`, set `max_health = BOSS_MAX_HEALTH`, `health = BOSS_MAX_HEALTH`, `width=52`, `height=72`, `self.name = name`, `self.phase = 1`.
- Phase property: `@property phase` returns 1, 2, or 3 based on `health / max_health` vs thresholds.
- Override `_update_ai(player)`:
  - Phase 1: standard chase + attack (inherit logic or replicate).
  - Phase 2 (`health <= BOSS_PHASE2_THRESH * max_health`): increase chase speed to 4.0, attack cooldown reduced to 35, attack range extended to 60. Call `_on_phase2_enter()` once when transitioning (set `_phase2_entered` flag).
  - Phase 3 (`health <= BOSS_PHASE3_THRESH * max_health`): add a ranged projectile attack on a separate 180-frame cooldown. Projectile is a simple `pygame.Rect` stored in `self._projectiles` list, moving at `vx=6 * facing` until it hits a solid tile or the player. For now, projectile is represented as a small rect that deals `ENEMY_ATTACK_DAMAGE * 0.8` on contact.
- `_on_phase2_enter()`: trigger a 12-frame hitstop and set a `_rage_flash_timer = 30` for a visual cue.
- `draw(surface, camera)`: call `super().draw()`, then if `_rage_flash_timer > 0` draw a pulsing red tint overlay rect on the entity, decrement timer. Draw projectiles.

`world/tilemap.py`:
- In `_parse()`, handle `'B'`: append `(x + TILE_SIZE//2, y - 72)` to a new `self.boss_spawn` attribute (single tuple or `None`).

`scenes/gameplay.py`:
- In `on_enter()`, after spawning enemies, check `self.tilemap.boss_spawn`. If not `None`, create `self.boss = Boss(*self.tilemap.boss_spawn, name="The Warden")` and append to `self.enemies`.
- Also set `self._boss` reference separately so draw can access it by type.
- In `_draw_hud()`, if any enemy in `self.enemies` is a `Boss` and `boss.alive`, call `_draw_boss_bar(surface, boss)`.
- `_draw_boss_bar(surface, boss)`: draw a full-width health bar at the bottom of the screen using `BOSS_BAR_Y`, `BOSS_BAR_MARGIN`, boss name as label, two threshold tick marks at 50% and 25% positions, color transitions from `HEALTH_COLOR` (phase 1) → `(220, 120, 0)` (phase 2) → `(220, 0, 0)` (phase 3).

**Acceptance criteria — done when:**
- A level with `'B'` in the tile data spawns a Boss.
- Boss health bar renders at the bottom of the screen.
- Boss enters phase 2 at 50% health (slightly faster, shorter cooldown).
- Boss enters phase 3 at 25% health (projectiles fly at player).
- Boss death removes the health bar and counts as a regular enemy kill.

---

### Task P1-3: Save / Load to Disk ✅ DONE

**Files to touch:**
- `core/game.py` (add `save_to_disk()` and `load_from_disk()`)
- `systems/checkpoint.py` (call save on activation)
- `settings.py` (add save file path constant)

**What to build:**

`settings.py`: Add `SAVE_FILE = "steamfall_save.json"`.

`core/game.py`:
- Add `import json, os, pathlib` at the top (inside the method to keep the file clean, or at module level).
- Add method `save_to_disk() -> None`:
  ```python
  def save_to_disk(self):
      import json, pathlib
      pathlib.Path(SAVE_FILE).write_text(
          json.dumps(self.save_data, indent=2))
  ```
- Add method `load_from_disk() -> None`:
  ```python
  def load_from_disk(self):
      import json, pathlib
      p = pathlib.Path(SAVE_FILE)
      if p.exists():
          self.save_data = json.loads(p.read_text())
  ```
- In `__init__`, after `self.save_data = {}`, call `self.load_from_disk()` so previous progress is restored.
- Add method `clear_save() -> None`: sets `self.save_data = {}` and calls `save_to_disk()` (used by "New Game" flow).

`systems/checkpoint.py`: In `update()`, after writing `game.save_data`, call `game.save_to_disk()`.

`scenes/main_menu.py`:
- Add a "Continue" option at the top if `game.save_data` is non-empty (check `game.save_data.get("checkpoint_pos")`).
- Selecting "Continue" calls `game.change_scene(SCENE_GAMEPLAY, level=game.save_data.get("checkpoint_level", "level_1"))` and sets `game.save_data["respawn"] = True`.
- Selecting "Begin" (renamed "New Game") calls `game.clear_save()` first, then proceeds to faction select.

**Acceptance criteria — done when:**
- Touching a checkpoint writes `steamfall_save.json` to disk.
- Restarting the game and selecting "Continue" puts the player at the saved checkpoint.
- "New Game" deletes the old save and starts fresh.
- `steamfall_save.json` is valid JSON and can be manually read.

---

### Task P1-4: Levels 2 Through 5 (Level Data) ✅ DONE

**Files to touch:**
- `world/tilemap.py` (add LEVEL_2 through LEVEL_5)
- `scenes/gameplay.py` (extend level transition chain)

**What to build:**

`world/tilemap.py`: Add the following level data constants after LEVEL_1. Use the tile key: `#` = solid, ` ` = air, `P` = player spawn, `E` = basic enemy, `c` = crawler, `C` = checkpoint, `B` = boss.

**LEVEL_2** — "The Descent": taller map, more vertical platforming, ceilings, crawlers introduced.
```python
LEVEL_2 = [
    "                                                     ",  # row 0
    "                                                     ",  # row 1
    "  ###                                   ###          ",  # row 2
    "                    ###                              ",  # row 3
    "           ###                  c                    ",  # row 4
    "                          #####                      ",  # row 5
    "  c        E                              ###        ",  # row 6
    "#####          ###              ###                  ",  # row 7
    "                                                     ",  # row 8
    "       C          E                    E             ",  # row 9
    "###############                     ########         ",  # row 10
    "                     ###                       P     ",  # row 11
    "#####################################################",  # row 12 ground
    "#####################################################",  # row 13
]
```

**LEVEL_3** — "The Foundry": wide industrial level, multiple enemy types, checkpoint mid-level.
```python
LEVEL_3 = [
    "                                                                 ",
    "                                                                 ",
    "        ###              ###                     ###             ",
    "                E                   E                     c      ",
    "  ###                          #########                         ",
    "                                                                 ",
    "     E               ###                  E                      ",
    "###########                                         ######       ",
    "                 C               ###                             ",
    "#################                           E              P     ",
    "#################################################################",
    "#################################################################",
]
```

**LEVEL_4** — "The Ruined Spire": vertical ascent, platforms shrink, more enemies.
```python
LEVEL_4 = [
    "                     #                              ",
    "                                                    ",
    "              ###           ###                     ",
    "    c                                    c          ",
    "         ###                   ###                  ",
    "  E                  c                        E     ",
    "      #######              #######                  ",
    "                                                    ",
    "         E         C                 E              ",
    "  ################   ################               ",
    "                                          P         ",
    "####################################################",
    "####################################################",
]
```

**LEVEL_5** — "The Sanctum / The Forge Floor" (boss level): large open arena, single boss `B`, checkpoint before boss, no regular enemy spawns.
```python
LEVEL_5 = [
    "                                                     ",
    "                                                     ",
    "  ###                                          ###   ",
    "                                                     ",
    "                                                     ",
    "           C                                         ",
    "   P    ########                      ########       ",
    "                                                     ",
    "                        B                            ",
    "#####################################################",
    "#####################################################",
]
```

`scenes/gameplay.py`:
- Import all five levels.
- Extend the transition chain in `update()`:
  - level_1 right edge → level_2
  - level_2 right edge → level_3
  - level_3 right edge → level_4
  - level_4 right edge → level_5
- Use a helper method `_check_level_transition()` to keep update() tidy.

**Acceptance criteria — done when:**
- Playing from level 1 through 5 without crashes.
- Each level loads its tile data, spawns correct entity types.
- LEVEL_5 spawns a boss and no regular enemies.

---

### Task P1-5: Pause Menu with Navigation ✅ DONE

**Files to touch:**
- `scenes/gameplay.py` (replace `_draw_pause` with a full menu)

**What to build:**

Replace the current `_draw_pause` text display and the bare ESC toggle with a proper navigable pause menu.

State added to `on_enter()`:
```python
self._paused        = False
self._pause_options = ["Resume", "Return to Main Menu", "Settings (soon)"]
self._pause_sel     = 0
```

`handle_event()` changes:
- When `ESC` pressed: toggle `_paused`. If un-pausing, reset `_pause_sel = 0`.
- When `_paused` is True, intercept `K_UP` / `K_DOWN` to move `_pause_sel`, `K_RETURN` to activate selected option.
  - "Resume": set `_paused = False`.
  - "Return to Main Menu": call `game.change_scene(SCENE_MAIN_MENU)`.
  - "Settings (soon)": do nothing (stub for Phase 4).

`_draw_pause(surface)`:
- Draw a semi-transparent dark overlay (alpha 150).
- Draw "PAUSED" title (georgia 48, white, centered, y = screen_height//2 - 140).
- Draw each option in a list below the title, spaced 56px apart. Selected option uses `WHITE`; others use `GRAY`. Draw a small `▶` diamond marker left of selected item.
- Draw a faint hint at the bottom: "↑↓ Navigate   ENTER Confirm   ESC Resume".

**Acceptance criteria — done when:**
- ESC opens a pause menu with three options listed.
- UP/DOWN navigates them.
- ENTER on "Resume" resumes the game.
- ENTER on "Return to Main Menu" goes back to main menu.
- "Settings (soon)" is listed but does nothing when selected.

---

### Task P1-6: Transition Screen Between Rooms ✅ DONE

**Files to touch:**
- `scenes/gameplay.py` (add transition state and drawing)
- `settings.py` (add transition constants)

**What to build:**

`settings.py`:
```python
TRANSITION_FADE_FRAMES = 40   # frames to fade out
TRANSITION_HOLD_FRAMES = 20   # frames to hold black with level name
TRANSITION_IN_FRAMES   = 30   # frames to fade in
```

`scenes/gameplay.py`:
Add a transition state machine that runs before a level switch.

New attributes in `on_enter()`:
```python
self._transition_phase  = None   # None, "fade_out", "hold", "fade_in"
self._transition_timer  = 0
self._transition_next   = None   # (scene_name, kwargs) to call after fade
self._transition_surf   = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
self._transition_surf.fill(BLACK)
self._level_display_name = _LEVEL_NAMES.get(level_name, level_name)
```

Add module-level dict before the class:
```python
_LEVEL_NAMES = {
    "level_1": "I — The Outer District",
    "level_2": "II — The Descent",
    "level_3": "III — The Foundry",
    "level_4": "IV — The Ruined Spire",
    "level_5": "V — The Sanctum",
}
```

Add method `_begin_transition(scene_name, **kwargs)`:
```python
def _begin_transition(self, scene_name, **kwargs):
    self._transition_phase = "fade_out"
    self._transition_timer = 0
    self._transition_next  = (scene_name, kwargs)
```

In `update()`, replace direct `game.change_scene()` calls for level transitions with `self._begin_transition(SCENE_GAMEPLAY, level="level_N")`.

Also in `update()`, add a transition tick block at the TOP (before other logic):
```python
if self._transition_phase is not None:
    self._tick_transition()
    return   # freeze game logic during transition
```

Add method `_tick_transition()`:
- "fade_out": increment timer; when `>= TRANSITION_FADE_FRAMES`, switch to "hold", reset timer.
- "hold": increment timer; when `>= TRANSITION_HOLD_FRAMES`, switch to "fade_in", reset timer, then call `self.game.change_scene(*...)` with the next scene — but immediately set `self._transition_phase = "fade_in"` and `timer = 0` so the NEW scene instance continues the fade-in.
  - Actually simpler: just call `game.change_scene` and let `on_enter` reset `_transition_phase = "fade_in"`. Pass `_fade_in=True` as a kwarg.
  - In `on_enter`, if `kwargs.get("_fade_in")`, set `self._transition_phase = "fade_in"` and `self._transition_timer = 0`.
- "fade_in": increment timer; when `>= TRANSITION_IN_FRAMES`, set `_transition_phase = None`.

In `draw()`, after everything else is drawn, add a `_draw_transition_overlay(surface)` call:
```python
def _draw_transition_overlay(self, surface):
    if self._transition_phase is None:
        return
    if self._transition_phase == "fade_out":
        alpha = int(255 * self._transition_timer / TRANSITION_FADE_FRAMES)
    elif self._transition_phase == "hold":
        alpha = 255
    else:  # fade_in
        alpha = int(255 * (1 - self._transition_timer / TRANSITION_IN_FRAMES))
    
    self._transition_surf.set_alpha(alpha)
    surface.blit(self._transition_surf, (0, 0))
    
    if self._transition_phase in ("hold", "fade_in") and alpha > 60:
        # Draw level name centered
        font = pygame.font.SysFont("georgia", 36)
        label = font.render(self._level_display_name, True, (200, 190, 140))
        surface.blit(label, (SCREEN_WIDTH//2 - label.get_width()//2,
                              SCREEN_HEIGHT//2 - 20))
```

**Acceptance criteria — done when:**
- Moving to the right edge of a level fades to black over ~40 frames.
- Black screen holds for ~20 frames showing the next level's display name.
- New level fades in over ~30 frames.
- No gameplay logic runs during the transition (player cannot move or die).

---

### Task P1-7: In-Game Map System ✅ DONE

**Files to touch:**
- `systems/minimap.py` (create)
- `scenes/gameplay.py` (integrate map, M key toggle)
- `settings.py` (add map constants)

**What to build:**

The map is a simple room tracker that marks which levels have been visited and shows a schematic of the current room's tile layout.

`settings.py`:
```python
MAP_TILE_SIZE  = 4     # Pixels per tile on the minimap
MAP_ALPHA      = 210
```

`systems/minimap.py`: `MiniMap` class.
- `__init__(game)`: stores reference to `game` for reading `save_data`.
- `mark_visited(level_name)`: adds `level_name` to `game.save_data.setdefault("visited_levels", [])`.
- `draw_overlay(surface, current_level_name, tilemap)`:
  - Draw a centered semi-transparent black panel (`SCREEN_WIDTH*0.7` × `SCREEN_HEIGHT*0.7`).
  - Draw a title "MAP" in top-left of panel.
  - Draw a horizontal room chain at the top of the panel: one rectangle per level name in `_LEVEL_ORDER = ["level_1","level_2","level_3","level_4","level_5"]`. Each rect is 80×30 px. Fill: `MARKED_COLOR` if current; `DARK_GRAY` if visited; `(20,20,30)` if not visited. Label each with its display name (truncated). Connect rects with a horizontal line.
  - Below the room chain, draw the current room's tile layout at `MAP_TILE_SIZE` per tile. Solid tiles (`#`) draw as `TILE_COLOR` rectangles. Entity spawn positions from `tilemap.enemy_spawns` draw as small red dots. Player spawn draws as a green dot. Checkpoint positions draw as yellow diamonds.
  - Draw "M — Close Map" hint at the bottom of the panel.

`scenes/gameplay.py`:
- Import `MiniMap` from `systems.minimap`.
- In `on_enter()`, create `self._minimap = MiniMap(self.game)` and call `self._minimap.mark_visited(level_name)`.
- Add `self._map_open = False` to `on_enter()`.
- In `handle_event()`, toggle `self._map_open` on `K_m`.
- In `update()`, skip normal updates when `_map_open` is True (game pauses like pause menu).
- In `draw()`, after the HUD, if `_map_open`, call `self._minimap.draw_overlay(surface, self._level_name, self.tilemap)`.

**Acceptance criteria — done when:**
- Pressing M opens a map overlay that pauses game logic.
- Pressing M again closes it.
- The current room's tile layout is visibly drawn.
- Previously visited rooms are indicated differently from unvisited rooms in the room chain.

---

### Task P1-8: Ability Unlock Gates ✅ DONE

**Files to touch:**
- `entities/player.py` (add ability slot count, lock ability if slots = 0)
- `systems/collectible.py` (add `AbilityOrb` collectible)
- `world/tilemap.py` (add `'A'` tile for ability orb)
- `scenes/gameplay.py` (spawn orbs, handle collection)
- `settings.py` (add ability slot constants)

**What to build:**

Players start with 0 ability slots. Ability Orbs are placed in the level (tile `'A'`). Collecting one permanently unlocks the ability (stored in `save_data`).

`settings.py`:
```python
ABILITY_SLOTS_DEFAULT = 0   # Start locked
ABILITY_SLOTS_MAX     = 1   # Only one ability in v0.1
```

`entities/player.py`:
- Add `self.ability_slots: int = kwargs.get("ability_slots", ABILITY_SLOTS_DEFAULT)` (or pass via constructor parameter).
- In `_handle_ability()`, add a guard at the top: `if self.ability_slots < 1: return`.

`systems/collectible.py` (extend file):
- Add `AbilityOrb(x, y)` class with a `rect` (18×18 px), `alive=True`, `_glow_timer=0`.
- `update()`: increment `_glow_timer`.
- `draw(surface, camera)`: draw a pulsing circle/diamond using faction color cycling (use `GOLD` as neutral color).
- `collect(player, game)`: set `player.ability_slots = min(player.ability_slots + 1, ABILITY_SLOTS_MAX)`, set `self.alive = False`, update `game.save_data["ability_slots"] = player.ability_slots`, call `game.save_to_disk()`.

`world/tilemap.py`:
- Add `self.ability_orb_spawns: list = []` in `__init__`.
- In `_parse()`: `'A'` → append `(x + TILE_SIZE//2, y - 18)` to `ability_orb_spawns`.

`scenes/gameplay.py`:
- Spawn `AbilityOrb` objects for all `tilemap.ability_orb_spawns`.
- In `on_enter()`, restore `player.ability_slots` from `game.save_data.get("ability_slots", ABILITY_SLOTS_DEFAULT)`.
- In `update()`, check orb collisions: if `player.rect.colliderect(orb.rect)`, call `orb.collect(player, game)`, remove from list.
- In `_draw_hud()`, if `player.ability_slots == 0`, tint the ability pip row `(40, 30, 50)` with a small lock icon text "LOCKED" in gray (monospace 12).

**Acceptance criteria — done when:**
- Player starts with ability locked (X key does nothing).
- Walking over an AbilityOrb unlocks the ability permanently.
- After dying and respawning (or restarting), the ability remains unlocked if saved via checkpoint.
- The HUD shows "LOCKED" on the pip row when ability_slots is 0.

---

## HK Feel Improvements (applied alongside Phase 1)

_Applied by hk-agent 2026-04-12; see `REVIEW_HK.md` for full analysis._

| Improvement | Status | Files Changed |
|---|---|---|
| Attack recoil (`ATTACK_RECOIL_VX = 1.5`) | ✅ Done | `entities/player.py`, `settings.py` |
| Windup frames (`WINDUP_FRAMES = 4`) | ✅ Done | `entities/player.py`, `settings.py` |
| Windup visual (dim gold glow) | ✅ Done | `entities/player.py` |
| Damage vignette (red border on hit) | ✅ Done | `scenes/gameplay.py`, `settings.py` |
| Touch knockback API (`take_damage(knockback_dir)`) | ✅ Done | `entities/entity.py` |
| Heavier gravity / tighter arc (GRAVITY 0.6→0.85, JUMP_FORCE -13→-12) | ⏳ Pending | Assign to build-agent |
| Air control reduction (speed × 0.7 when airborne) | ⏳ Pending | `entities/player.py` — assign to build-agent |
| Movement lock during windup (`vx = 0` when `_windup_timer > 0`) | ⏳ Pending | `entities/player.py` — assign to build-agent |
| Enemy-specific 2-frame hit flash color | ⏳ Pending | `entities/enemy.py` — assign to build-agent |
| Caller-side `knockback_dir` in enemy touch damage | ⏳ Pending | `entities/enemy.py`, `entities/crawler.py` |
| Particle system (landing dust, nail sparks, camera pan) | ⏳ Phase 4 | New `systems/particles.py` |

---

## Phase 2 — Content Expansion

**Priority order for build-agent** (tackle in this order):

1. **P2-0 (tech debt unblock):** Fix Tech Debt #4 (`Enemy.get_drop_fragments()`) and Tech Debt #5 (enemy iframes) in `entities/enemy.py` + `entities/entity.py`. These will crash any playtest with enemies present.
2. **P2-1 (enemy variety):** Add `ShieldGuard` (Enemy subclass, higher defense, blocks from front), `Ranged` (fires projectile in line of sight), `Jumper` (erratic vertical movement pattern). Each new class goes in its own file under `entities/` and must be listed in this table before creation.
3. **P2-2 (levels 6–10):** Tile data for levels 6–10 in `world/tilemap.py`; introduce branching (Marked path vs Fleshforged path levels 6–8 differ, converge at level 9).
4. **P2-3 (Warden scripting):** Fully scripted boss intro dialogue, phase-transition visual effects, unique per-phase attack patterns, Phase 3 arena shrink via platform tiles.
5. **P2-4 (Architect boss):** Final boss, four phases, faction-specific defeat dialogue.
6. **P2-5 (upgrade system):** After boss kill, award one of three permanent stat upgrades; store in `save_data["upgrades"]`.
7. **P2-6 (enemy drops):** `HeatCore` and `SoulShard` collectibles (extend `systems/collectible.py`) dropped based on enemy faction; faction-matched healing.
8. **P2-7 (environmental hazards):** Spike tiles (`'s'`), crumbling platforms (`'~'` disappears after 30 standing frames); add parsers to `TileMap` and collision handling to `physics.py`/`gameplay.py`.

## Phase 3 — Story Integration

- **Mid-game lore beats**: After completing level 3, trigger a short dialogue cutscene (same DialogueBox system as prologue) revealing a faction-specific secret. Use `game.change_scene(SCENE_MARKED_PROLOGUE)` with a `beat_start` kwarg to replay from a specific beat index.
- **Faction enemy design**: Marked levels feature Fleshforged enemies (iron-color); Fleshforged levels feature Marked acolytes (purple-tinted). Midgame levels have both.
- **Ending branches**: Two ending scenes (`scenes/marked_ending.py`, `scenes/fleshforged_ending.py`), each with 8–10 story beats, triggered after defeating The Architect depending on `game.player_faction`.
- **NPC encounters**: Friendly NPCs with dialogue trees appear in "safe room" tiles (`'N'`). Press `E` near them to talk. Dialogue advances the lore without cutscenes.
- **Collectible lore items**: Books / inscriptions (`'L'` tile) reveal a single paragraph of world-building when collected. Stored in `save_data["lore_found"]`; accessible from pause menu "Lore" tab.

## Phase 4 — Polish

- **Sprite replacement**: Replace all placeholder colored-rect entity renders with sprite sheets loaded via `pygame.image.load`. `AnimationController` already supports frame lists — swap `_make_frames()` to load from asset files.
- **Tile sprites**: Replace `pygame.draw.rect` tile rendering with a 32×32 tile sprite sheet (one image per biome: Outer District, Foundry, Spire, Sanctum).
- **Particle system**: Add a `systems/particles.py` module. Emit particles on: hit (blood/sparks), death (burst), Soul Surge (purple shards), Overdrive activation (heat shimmer), checkpoint activation (golden embers).
- **Sound**: Add `systems/audio.py` wrapping `pygame.mixer`. Sounds needed: attack swing, hit land, jump, death, checkpoint activate, ability use, boss phase transition, ambient level music (one track per biome).
- **Settings screen**: Implement the "Settings (soon)" pause menu stub from P1-5 as a real scene (`scenes/settings.py`) with: volume sliders (music, SFX), fullscreen toggle, key rebinding stubs.
- **Main menu polish**: Add background parallax scroll, animated logo, "Credits" option listing contributors.
- **Death screen polish**: Replace "you perished" text with faction-specific message ("The ink fades..." / "The forge goes cold...") with subtle particle decay effect.

---

## Known Bugs / Tech Debt

_Legend: ✅ Fixed | ⚠️ Flagged / deferred | 🔴 Open_

1. ✅ **CRITICAL — Missing files cause immediate ImportError on startup** — Fixed by Task P1-1. All files created; `CHECKPOINT_GLOW_COLOR` added to `settings.py`.

2. ✅ **`HitStop` classmethod+property bug** — Fixed (REVIEW_BUGS BUG-004). Removed the `_inst` class variable and `instance` classmethod from `core/hitstop.py`.

3. ✅ **`TileMap` missing attributes** — Fixed by Task P1-1. `crawler_spawns`, `checkpoints`, `boss_spawn`, `ability_orb_spawns` all initialised in `TileMap.__init__`.

4. 🔴 **`Enemy.get_drop_fragments()` missing** — Still open. `gameplay.py` calls this method on every dead enemy but `entities/enemy.py` has no `get_drop_fragments()`. Will throw `AttributeError` on first enemy death. **Assign to build-agent; fix before next playtest.**

5. 🔴 **Entity iframes applied to enemies** — Still open. `entity.py` `take_damage()` applies `PLAYER_IFRAMES = 45` to all entities; enemies become briefly invincible after each hit. Override in `Enemy.__init__` with a shorter constant (e.g. 6 frames). **Assign to build-agent.**

6. ✅ **Pause menu is not a real menu** — Fixed by Task P1-5. Full navigable pause overlay with Resume / Return to Main Menu / Settings (soon).

7. ⚠️ **`player.py` animation draw duplication** — Deferred. Eye and attack-arc draw code is overlaid on top of the animation blit; works correctly but structure is messy. Consolidate in Phase 4 (sprite pass).

8. ✅ **`dialogue.py` hint text hardcoded** — Fixed (REVIEW_BUGS BUG-003). `else` branch now reads `"SPACE — dismiss"`.

9. ⚠️ **Level transition uses raw pixel boundary** — Deferred. Works reliably for current level widths. If level geometry changes add a `'>'` exit tile in the parser. Assign to build-agent if levels are resized.

10. ⚠️ **Wildcard imports in scene files** — Flagged (REVIEW_BUGS FLAG-001). Architectural style; not blocking; defer to Phase 4 cleanup.

11. 🔴 **Audio subsystem incomplete** — `systems/voice_player.py` added (voice lines); `systems/audio.py` for music/SFX still absent. `pygame.mixer` is initialised by `pygame.init()` but no sounds play. Assign to build-agent in Phase 4.

12. ⚠️ **World bounds not enforced for enemies** — Flagged. Low-priority edge case; assign to build-agent if enemies escape the visible world during playtesting.

---

## Agent Coordination Notes

| File / Directory | Owner Agent | Notes |
|---|---|---|
| `ROADMAP.md` | orchestrator | Update after each Phase is complete or task status changes |
| `AGENTS.md` | orchestrator | Update if new agents are added |
| `settings.py` | build-agent (primary) | All new constants go here; review-agent and hk-agent may read only |
| `main.py` | build-agent | Rarely changes; only for new subsystem init |
| `core/game.py` | build-agent | Save/load complete (P1-3); stable |
| `core/camera.py` | build-agent | Stable; unlikely to change |
| `core/hitstop.py` | build-agent | Stable (Tech Debt #2 fixed) |
| `scenes/base_scene.py` | build-agent | Stable interface; do not change method signatures |
| `scenes/main_menu.py` | build-agent | Continue/New Game complete (P1-3); stable |
| `scenes/faction_select.py` | build-agent | Stable until Phase 3 |
| `scenes/marked_prologue.py` | build-agent | Stable until Phase 3 |
| `scenes/fleshforged_prologue.py` | build-agent | Stable until Phase 3 |
| `scenes/gameplay.py` | build-agent | All Phase 1 features integrated; open tasks: Tech Debt #4, #5 |
| `entities/entity.py` | build-agent | Open: iframe fix (Tech Debt #5) |
| `entities/player.py` | build-agent | Ability slots done; animation draw consolidation deferred to Phase 4 |
| `entities/enemy.py` | build-agent | Open: `get_drop_fragments()` (Tech Debt #4), iframe fix (Tech Debt #5) |
| `entities/crawler.py` | build-agent | Created (P1-1); stable |
| `entities/boss.py` | build-agent | Created (P1-2); Phase 2 scripted intro pending |
| `systems/physics.py` | build-agent | Stable; do not change call signatures |
| `systems/combat.py` | build-agent | Stable; hitbox logic complete |
| `systems/dialogue.py` | build-agent | Hint text fix done (Tech Debt #8); stable |
| `systems/animation.py` | build-agent | Stable until sprite replacement (Phase 4) |
| `systems/checkpoint.py` | build-agent | Created (P1-1); stable |
| `systems/collectible.py` | build-agent | Created (P1-1, P1-8); extend with HeatCore/SoulShard in Phase 2 |
| `systems/minimap.py` | build-agent | Created (P1-7); stable |
| `systems/tutorial_minigame.py` | build-agent (created outside roadmap) | Inline control tutorial for prologues; registered here for tracking |
| `systems/voice_player.py` | build-agent (created outside roadmap) | Voice-line playback; no MP3 assets yet; blocked on Phase 4 audio pass |
| `world/tilemap.py` | build-agent | LEVEL_1–5 complete; extend with LEVEL_6–10 in Phase 2 |
| `REVIEW_BUGS.md` | review-agent (own) | Never modifies .py files |
| `REVIEW_HK.md` | hk-agent (own) | Never modifies .py files |
