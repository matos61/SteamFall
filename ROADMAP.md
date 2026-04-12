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

## Phase 1 — Core Loop Complete

The following ordered tasks make the game fully playable from start through at least two levels with save/load, a boss, a map, and proper UI.

---

### Task P1-1: Fix Missing Imports — Crawler, Checkpoint, SoulFragment, LEVEL_2, CHECKPOINT_GLOW_COLOR

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

### Task P1-2: Boss Fight Framework

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

### Task P1-3: Save / Load to Disk

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

### Task P1-4: Levels 2 Through 5 (Level Data)

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

### Task P1-5: Pause Menu with Navigation

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

### Task P1-6: Transition Screen Between Rooms

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

### Task P1-7: In-Game Map System

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

### Task P1-8: Ability Unlock Gates

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

## Phase 2 — Content Expansion

- **Enemy variety**: Add `ShieldGuard` (Enemy subclass, higher defense, blocks from front), `Ranged` (fires projectile in line of sight), `Jumper` (erratic vertical movement pattern).
- **Level count**: Levels 6–10 using tile data; introduce branching (Marked path vs Fleshforged path levels 6–8 differ, converge at level 9).
- **Boss fight – The Warden (level 5)**: Fully scripted boss intro dialogue, phase transition visual effects, unique attack patterns per phase. Phase 3 arena shrinks via spawning platform tiles.
- **Boss fight – The Architect (level 10)**: Final boss with four phases, one per faction weakness, unique defeat dialogue per faction choice.
- **Upgrade system**: After boss kill, player is awarded a permanent stat upgrade (choose from 3 options — more health, faster attack cooldown, larger resource pool). Stored in `save_data["upgrades"]`.
- **Enemy drops**: Enemies drop different collectible types — `HeatCore` (Fleshforged heals) and `SoulShard` (Marked heals) — based on enemy faction.
- **Environmental hazards**: Spike tiles (`'s'`), acid pools, crumbling platforms (tile `'~'` that disappears after standing on it for 30 frames).

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

1. **CRITICAL — Missing files cause immediate ImportError on startup**: `entities/crawler.py`, `systems/checkpoint.py`, `systems/collectible.py` are imported in `gameplay.py` but do not exist. `LEVEL_2` is imported from `tilemap.py` but not defined there. `CHECKPOINT_GLOW_COLOR` is used in `gameplay.py` but not in `settings.py`. The game will crash on `import` before any scene renders. Fix: Task P1-1.

2. **`HitStop` classmethod+property bug**: `core/hitstop.py` defines `instance` as both `@classmethod` and `@property`, which is deprecated/broken in Python 3.11+. However, the module-level `hitstop = HitStop()` singleton is what all code actually imports and uses, so the class method is dead code. The `@classmethod @property` decorator should be removed to avoid confusion and future breakage.

3. **`TileMap` missing attributes**: `TileMap.__init__` only initializes `self.tiles`, `self.player_spawn`, and `self.enemy_spawns`. The `gameplay.py` scene accesses `tilemap.crawler_spawns`, `tilemap.checkpoints`, and (after Phase 1) `tilemap.boss_spawn` and `tilemap.ability_orb_spawns`. These will throw `AttributeError` at runtime.

4. **`Enemy.get_drop_fragments()` missing**: `gameplay.py` calls `dead_e.get_drop_fragments()` on every dead enemy, but `Enemy` has no such method. This will throw `AttributeError` every time an enemy dies.

5. **Entity iframes applied to enemies**: `entity.py` `take_damage()` applies `PLAYER_IFRAMES = 45` to all entities, including enemies. Enemies end up invincible for 45 frames (0.75 seconds) after being hit. They should have a shorter iframe window (e.g., 4–8 frames) or none. Fix: give `Enemy.__init__` its own iframe constant, or override `take_damage()`.

6. **Pause menu is not a real menu**: `_draw_pause` renders static text but pressing UP/DOWN/ENTER during pause has no effect (events are swallowed but not routed to pause menu navigation). "Return to Main Menu" is not interactive — only F1 works. Fix: Task P1-5.

7. **`gameplay.py` animation draw duplication**: The `player.py` `draw()` method was rewritten to use `self._anim.current_frame` but an old copy of `draw()` is still present in `player.py` that also draws eye circles and attack arc on top of the animation blit. This causes the eye/arc to be drawn correctly, but the code structure has two draw sections. Should be consolidated.

8. **`dialogue.py` hint text hardcoded to "SPACE — continue"** on both branches of the condition (line 131-133 of dialogue.py). The else branch says "SPACE — continue" instead of "SPACE — close" or similar. Minor UX bug.

9. **Level transition check uses raw pixel boundary**: `gameplay.py` checks `player.rect.right >= self.tilemap.width - 64` for level transition. If the player is tall or the level width is not tile-aligned, this could trigger prematurely or not at all. Should be a dedicated exit tile or zone marker (`'>'` tile type) parsed by TileMap.

10. **`faction_select.py` uses `*` import from settings**: `from settings import *` is used in several scene files. While convenient, it makes dependency tracking harder and can shadow local names. Future refactor should enumerate specific imports.

11. **No audio subsystem**: `pygame.mixer` is never initialized. `pygame.init()` in `main.py` initializes all subsystems including mixer, so it won't crash, but no sounds exist yet.

12. **World bounds not enforced for enemies**: Enemies use `move_and_collide` for horizontal tile collisions but have no check against world pixel boundaries (x < 0, x > world_width). A chased enemy could theoretically be knocked off-screen.

---

## Agent Coordination Notes

| File / Directory | Owner Agent | Notes |
|---|---|---|
| `ROADMAP.md` | orchestrator | Update after each Phase is complete or task status changes |
| `AGENTS.md` | orchestrator | Update if new agents are added |
| `settings.py` | build-agent (primary) | All new constants go here; review-agent and hk-agent may read only |
| `main.py` | build-agent | Rarely changes; only for new subsystem init |
| `core/game.py` | build-agent | Save/load additions go here (P1-3) |
| `core/camera.py` | build-agent | Stable; unlikely to change |
| `core/hitstop.py` | build-agent | Fix classmethod+property bug (Tech Debt #2) |
| `scenes/base_scene.py` | build-agent | Stable interface; do not change method signatures |
| `scenes/main_menu.py` | build-agent | Add "Continue" option (P1-3) |
| `scenes/faction_select.py` | build-agent | Stable until Phase 3 |
| `scenes/marked_prologue.py` | build-agent | Stable until Phase 3 |
| `scenes/fleshforged_prologue.py` | build-agent | Stable until Phase 3 |
| `scenes/gameplay.py` | build-agent | Primary integration point for all Phase 1 tasks |
| `entities/entity.py` | build-agent | Minimal changes expected; iframe fix (Tech Debt #5) |
| `entities/player.py` | build-agent | Ability slots (P1-8), animation draw consolidation |
| `entities/enemy.py` | build-agent | Add `get_drop_fragments()` (Tech Debt #4), iframe fix |
| `entities/crawler.py` | build-agent (create) | P1-1 |
| `entities/boss.py` | build-agent (create) | P1-2 |
| `systems/physics.py` | build-agent | Stable; do not change call signatures |
| `systems/combat.py` | build-agent | Stable; hitbox logic complete |
| `systems/dialogue.py` | build-agent | Hint text fix (Tech Debt #8) |
| `systems/animation.py` | build-agent | Stable until sprite replacement (Phase 4) |
| `systems/checkpoint.py` | build-agent (create) | P1-1 |
| `systems/collectible.py` | build-agent (create) | P1-1, P1-8 |
| `systems/minimap.py` | build-agent (create) | P1-7 |
| `world/tilemap.py` | build-agent | Add LEVEL_2–5 (P1-4), extend parser (P1-1) |
| `REVIEW_BUGS.md` | review-agent (create/own) | Never modifies .py files |
| `REVIEW_HK.md` | hk-agent (create/own) | Never modifies .py files |
