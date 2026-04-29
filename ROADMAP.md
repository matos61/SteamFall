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
| Heavier gravity / tighter arc (GRAVITY 0.6→0.85, JUMP_FORCE -13→-12) | ✅ Done | `settings.py` (GRAVITY=0.85, JUMP_FORCE=-12, FRICTION=0.74, TERMINAL_VELOCITY=20) |
| Air control reduction (faction-specific: Marked 1.00, Fleshforged 0.72) | ✅ Done | `entities/player.py` (`_air_control` mult), `settings.py` |
| Movement lock during windup (`vx = 0` when `_windup_timer > 0`) | ✅ Done | `entities/player.py` — applied in P2-1 commit |
| Enemy-specific 2-frame hit flash color | ✅ Done | `entities/enemy.py` — red 2-frame flash in draw override |
| Caller-side `knockback_dir` in enemy touch damage | ✅ Done | `scenes/gameplay.py` — body contact with directional knockback |
| Particle system (landing dust, nail sparks, camera pan) | ⏳ Phase 4 | New `systems/particles.py` |
| Architect teleport telegraph (`ARCHITECT_TELEPORT_WARN=20`, lock+distinct pulse before teleport) | ⏳ P2-8 | `entities/architect.py`, `settings.py` |
| Architect teleport cadence (`ARCHITECT_TELEPORT_CD` 200→140, `ARCHITECT_MINION_CD` 300→210) | ⏳ P2-8 | `settings.py` |
| Upgrade DMG cap (`UPGRADE_DMG_BONUS` 5→6, `UPGRADE_DMG_MAX_STACKS=3`) | ⏳ P2-8 | `settings.py`, `entities/player.py` |
| Upgrade RES regen (`UPGRADE_RES_REGEN_BONUS=0.008` per stack, applied to passive regen) | ⏳ P2-8 | `settings.py`, `entities/player.py` |
| Faction heal drops (`HEAT_CORE_HEAL`/`SOUL_SHARD_HEAL` 8→12) | ✅ Incorporated into P2-6 spec | `settings.py` |
| Boss SoulFragment spread (widen from ±20 to ±40 px at drop) | ✅ Incorporated into P2-6 spec | `entities/boss.py` |
| LEVEL_10 Architect teleport Y floor clamp (prevent landing on mid-arena platform at row 9) | ⏳ P2-8 | `entities/architect.py` |
| Minimap room-chain extended to levels 6–10 (FLAG-009) | ⏳ P2-8 | `systems/minimap.py` |
| ShieldGuard full block (DEFENSE 0.35→0.0, HP 80→65); fix facing locked to patrol dir | ✅ Done | `settings.py`, `entities/shield_guard.py` — P2-2b |
| Ranged: reduce cooldown (90→55 frames); add projectile arc (vy from player delta Y, ±4 cap); extract `RANGED_PREFERRED_DIST` constant | ✅ Done | `entities/ranged.py`, `settings.py` — P2-2b |
| Jumper: reduce cooldown (55→32 frames); add burst pattern (`JUMPER_BURST_COUNT=2`, `JUMPER_BURST_PAUSE=70`) | ✅ Done | `entities/jumper.py`, `settings.py` — P2-2b |
| Add `SHIELD_GUARD_KNOCKBACK_Y=-3.5`, `JUMPER_KNOCKBACK_Y_AERIAL=2.0` knockback constants | ✅ Done | `settings.py`, respective entity files — P2-2b |

---

## Phase 2 — Content Expansion ✅ COMPLETE (2026-04-23)

All Phase 2 tasks are done. The game has 10 levels (with faction branches at 6–8), three enemy varieties, a two-boss climax, an upgrade system, environmental hazards, enemy drops, and a full minimap. Phase 3 (Story Integration) is next.

**Priority order for build-agent** (tackle in this order):

1. ~~**P2-0 (tech debt unblock)**~~ ✅ **DONE (2026-04-17):** `Enemy.get_drop_fragments()` added; enemy iframes fixed via `ENEMY_IFRAMES=6` overriding `PLAYER_IFRAMES=45`.
2. ~~**P2-1 (enemy variety)**~~ ✅ **DONE (2026-04-17):** `ShieldGuard`, `Ranged`, `Jumper` created in `entities/`; wired into `tilemap.py` (`'G'`/`'R'`/`'J'` tile chars) and `gameplay.py`.
3. ~~**P2-2 (levels 6–10)**~~ ✅ **DONE (2026-04-18):** `LEVEL_6_MARKED/FLESHFORGED` through `LEVEL_10` in `tilemap.py`; `_faction_next_level()` routing in `gameplay.py`; victory flag on level 10 completion.
4. ~~**P2-2b (HK feel sprint)**~~ ✅ **DONE (2026-04-18):** All 13 constants in place; ShieldGuard full block + patrol-facing fix; Ranged arc projectile; Jumper burst pattern + aerial knockback.
5. ~~**P2-3 (Warden scripting)**~~ ✅ **DONE (2026-04-18):** 3-beat Warden intro dialogue; phase-differentiated rage flash (orange/red); BOSS_PROJ_SPREAD_VY; BUG-016 fixed. Prior commits had already implemented dash, arena shrink, and projectile spread.
6. ~~**P2-4 (Architect boss)**~~ ✅ **DONE (2026-04-18):** `entities/architect.py` created; 4-phase AI (teleport/fan/minions); faction-specific intro + defeat dialogue; 'X' tile in LEVEL_10; victory write to save_data.
7. ~~**P2-5 (upgrade system)**~~ ✅ **DONE (2026-04-21):** Upgrade screen on Warden kill; three choices (HP/DMG/RES); stored in `save_data["upgrades"]`; reapplied on level load.
8. ~~**P2-0c (critical bug-fix sprint)**~~ ✅ **DONE (2026-04-23):** BUG-018 through BUG-025 all fixed — ability-slots gate added (BUG-019), Architect level_width param (BUG-020), Architect phase-announce wired (BUG-021), upgrade-while-dead guard (BUG-018), announce_phase=4 signal (BUG-021 addendum), BUG-022/023/024/025 resolved.
9. ~~**P2-6 (enemy drops)**~~ ✅ **DONE (2026-04-23):** `HeatCore`/`SoulShard` confirmed in place; `HEAT_CORE_HEAL`/`SOUL_SHARD_HEAL` raised to 12; Boss `get_drop_fragments()` spread widened to ±40 px.
10. ~~**P2-7 (environmental hazards)**~~ ✅ **DONE (2026-04-23):** Spike tiles (`'s'`) and crumble platforms (`'~'`) parsed; spike damage, crumble state machine, and hazard draw added to `gameplay.py`; test tiles placed in LEVEL_3 and LEVEL_4.
11. ~~**P2-8 (HK feel sprint — Architect/Upgrades/Minimap)**~~ ✅ **DONE (2026-04-23):** Teleport warn (20-frame white-blue pulse + Y-floor clamp); crawler cap (≤2 live); `UPGRADE_DMG_MAX_STACKS=3`; `_res_regen_bonus` additive regen; minimap 2-row layout covering all 13 level nodes.

---

### Task P2-0: Tech Debt Unblock ✅ DONE (2026-04-17)

**What was built:**
- `entities/enemy.py`: Added `get_drop_fragments()` returning a list of one `SoulFragment` at the enemy's center. Added `self._iframes_on_hit = ENEMY_IFRAMES` in `__init__`.
- `entities/entity.py`: Exposed `_iframes_on_hit` as an overridable instance variable; `take_damage()` now uses it instead of hardcoded `PLAYER_IFRAMES`.
- `settings.py`: Added `ENEMY_IFRAMES = 6`.

---

### Task P2-1: Enemy Variety ✅ DONE (2026-04-17)

**What was built:**
- `entities/shield_guard.py`: `ShieldGuard(Enemy)` — 65% frontal damage reduction; slow, high-damage melee; colored steel-gray.
- `entities/ranged.py`: `Ranged(Enemy)` — holds distance, fires `Projectile` objects tracked per frame at range; projectiles deal `ENEMY_ATTACK_DAMAGE * 0.8`.
- `entities/jumper.py`: `Jumper(Enemy)` — erratic hop AI, spring-coil visual during wind-up; bounces backward on attack.
- `settings.py`: 15 new constants for the three enemy types.
- `world/tilemap.py`: `'G'`/`'R'`/`'J'` tile chars; `shield_guard_spawns`, `ranged_spawns`, `jumper_spawns` lists in `TileMap.__init__`.
- `scenes/gameplay.py`: Imports and spawns all three; handles ranged projectile–player collision.

**HK feel improvements applied in same commit:**
- `entities/player.py`: `vx = 0` during `_windup_timer > 0` (movement lock during windup).
- `entities/enemy.py`: Red 2-frame hit flash on enemy draw (replaces white flicker).
- `scenes/gameplay.py`: Enemy body contact deals half-damage with directional knockback.

---

### Task P2-0b: Critical Bug-Fix Sprint ✅ DONE (2026-04-18)

_Review-agent 2026-04-18 pass found these correctness bugs that must be fixed before P2-3 content work._

**Files to touch:**
- `entities/shield_guard.py` (BUG-005)
- `entities/ranged.py` (BUG-006, BUG-014)
- `entities/jumper.py` (BUG-008)
- `entities/player.py` (BUG-009, BUG-010, BUG-015)
- `scenes/gameplay.py` (BUG-007 / BUG-011)
- `systems/minimap.py` (BUG-013)

**Fixes required:**

- **BUG-005** `shield_guard.py:34`: Change `knockback_dir == self.facing` → `knockback_dir == -self.facing`. The guard AI always faces toward the player, so knockback always points opposite to facing — the block condition was never True.

- **BUG-006** `ranged.py` `Projectile`: Add `self._dist_traveled = 0` and a `max_range` (e.g. `RANGED_SIGHT_RANGE * 2`) to `Projectile.__init__`. In `update()`, increment `_dist_traveled` by `abs(vx)` each frame; set `self.alive = False` when it exceeds `max_range`.

- **BUG-007 / BUG-011** `gameplay.py`: Move the dead-enemy fragment-spawn and enemy-prune block inside the `if not hitstop.is_active():` guard (or add a `_dropped = False` flag to each enemy and set it True after the first drop). Fragments must spawn at most once per kill.

- **BUG-008** `jumper.py`: Clamp `_jump_timer` when entering patrol. Simplest fix: at the top of `_do_patrol_jump`, add `self._jump_timer = min(self._jump_timer, JUMPER_JUMP_COOLDOWN)` to prevent an instant jump after re-entering patrol from a long chase.

- **BUG-009** `player.py:175`: After the `elif self._coyote_timer > 0` block, add `elif self.on_ground: self._coyote_timer = 0` to reset the stale coyote timer on landing.

- **BUG-010** `player.py:241`: Guard the variable-jump cut with `self._jump_held`: change to `if not jump_pressed and self._jump_held and self.vy < -4: self.vy *= self._jump_cut`.

- **BUG-013** `minimap.py:120`: Add `+ tilemap.shield_guard_spawns + tilemap.ranged_spawns + tilemap.jumper_spawns` to the enemy-dot loop.

- **BUG-014** `ranged.py`: Before `self._do_patrol()` call, set `self._state = _PATROL`.

- **BUG-015** `player.py`: Remove `_regen_resource(3)` from `_handle_attack` (on key press). Move it to `systems/combat.py` `AttackHitbox._apply_hit()`: after dealing damage, if `hasattr(self, 'owner') and hasattr(self.owner, 'faction') and self.owner.faction == FACTION_MARKED: self.owner._regen_resource(3)`. Import `FACTION_MARKED` in `combat.py`.

**Acceptance criteria — done when:**
- ShieldGuard blocks frontal hits (player hits from front → 65% reduction; from behind → full damage).
- Projectiles disappear after traveling `RANGED_SIGHT_RANGE * 2` pixels.
- Killing an enemy drops exactly one fragment set regardless of hitstop duration.
- Jumper does not jump on the very first frame of patrol after a long chase.
- Coyote timer is 0 after landing; no spurious double-jump through coyote window.
- Knockback arcs are not dampened by the variable-jump cut.
- Minimap shows G/R/J spawn dots.
- Ranged enemy's `_state` reflects its actual behaviour (PATROL when not in sight).
- Marked soul regen only triggers on hits that connect, not on missed swings.

---

### Task P2-2: Levels 6–10 ✅ DONE (2026-04-18)

**What was built:**
- `world/tilemap.py`: `LEVEL_6_MARKED`, `LEVEL_6_FLESHFORGED`, `LEVEL_7_MARKED`, `LEVEL_7_FLESHFORGED`, `LEVEL_8_MARKED`, `LEVEL_8_FLESHFORGED`, `LEVEL_9`, `LEVEL_10`.
- `scenes/gameplay.py`: `_LEVEL_DATA` dict, `_faction_next_level()` helper routing levels 6–8 by faction, victory flag written to `save_data` on level 10 completion.

---

### Task P2-2b: HK Feel Sprint — ShieldGuard / Ranged / Jumper ✅ DONE (2026-04-18)

**What was built:**
- `settings.py`: All 13 constants updated/added (SHIELD_GUARD_DEFENSE=0.0, SHIELD_GUARD_HP=65, SHIELD_GUARD_SPEED=1.6, SHIELD_GUARD_KNOCKBACK_Y=-3.5, RANGED_ATTACK_COOLDOWN=55, RANGED_PROJ_SPEED=6, RANGED_PREFERRED_DIST=240, JUMPER_JUMP_COOLDOWN=32, JUMPER_JUMP_FORCE=-12, JUMPER_SPEED=2.4, JUMPER_BURST_COUNT=2, JUMPER_BURST_PAUSE=70, JUMPER_KNOCKBACK_Y_GROUND=-4.5, JUMPER_KNOCKBACK_Y_AERIAL=2.0).
- `entities/shield_guard.py`: DEFENSE=0.0 (100% frontal block); facing update gated to CHASE/ATTACK state; SHIELD_GUARD_KNOCKBACK_Y extracted; BUG-005 fix confirmed present.
- `entities/ranged.py`: Projectile has vy field + mild gravity arc (0.15/frame); _fire() computes arc toward player Y (±4 cap); _PREFERRED_DIST uses RANGED_PREFERRED_DIST constant.
- `entities/jumper.py`: Burst pattern with _burst_remaining / _burst_pause; aerial vs ground knockback via JUMPER_KNOCKBACK_Y_AERIAL / JUMPER_KNOCKBACK_Y_GROUND.

**Known remaining issue:** BUG-016 (ShieldGuard patrol facing) — see Known Bugs #13.

---

### Task P2-2b: HK Feel Sprint — ShieldGuard / Ranged / Jumper (SPEC — kept for reference)

_Unblocked by P2-0b completion (2026-04-18). See `REVIEW_HK.md` 2026-04-18 pass for full justification._

**Files to touch:**
- `settings.py` (constants)
- `entities/shield_guard.py` (full block + facing fix + knockback constant)
- `entities/ranged.py` (arc projectile + cooldown + RANGED_PREFERRED_DIST)
- `entities/jumper.py` (burst pattern + aerial knockback constant)

**What to build:**

`settings.py` — update and add:
```python
SHIELD_GUARD_DEFENSE       = 0.0    # was 0.35 — full frontal block; forces player to flank
SHIELD_GUARD_HP            = 65     # was 80 — lower HP compensates for 100% block
SHIELD_GUARD_SPEED         = 1.6    # was 1.2 — faster chase so it punishes kiting
SHIELD_GUARD_KNOCKBACK_Y   = -3.5   # NEW — heavy upward bash; extract from hardcode in shield_guard.py
RANGED_ATTACK_COOLDOWN     = 55     # was 90 — ~0.9 s between shots; creates real pressure
RANGED_PROJ_SPEED          = 6      # was 5 — faster bolt, tighter reaction window
RANGED_PREFERRED_DIST      = 240    # NEW — extract _PREFERRED_DIST = 220 hardcode from ranged.py
JUMPER_JUMP_COOLDOWN       = 32     # was 55 — ~0.53 s; urgency, harder to exploit landing
JUMPER_JUMP_FORCE          = -12    # was -11 — higher hop, harder to hit mid-air
JUMPER_SPEED               = 2.4    # was 2.0 — faster horizontal component
JUMPER_BURST_COUNT         = 2      # NEW — jumps per burst before pause
JUMPER_BURST_PAUSE         = 70     # NEW — frames of pause after a full burst
JUMPER_KNOCKBACK_Y_GROUND  = -4.5   # NEW — upward bounce on ground-level attack (was hardcoded)
JUMPER_KNOCKBACK_Y_AERIAL  =  2.0   # NEW — downward spike when Jumper attacks from above
```

`entities/shield_guard.py`:
- Update `SHIELD_GUARD_DEFENSE` reference (now 0.0 — the guard absorbs the full hit; player takes 0 damage from front).
- Fix facing update: currently `_update_ai` always sets `self.facing` toward the player before calling `super()`. Change so `self.facing` is only updated when `self._state in (_CHASE, _ATTACK)`. During `_PATROL`, facing follows patrol direction naturally.
- Replace `knockback_y=-2.0` hardcode in the melee `AttackHitbox` creation with `SHIELD_GUARD_KNOCKBACK_Y`.

`entities/ranged.py`:
- Replace `_PREFERRED_DIST = 220` module constant with `from settings import RANGED_PREFERRED_DIST` and `_PREFERRED_DIST = RANGED_PREFERRED_DIST`.
- Add `vy=0` parameter to `Projectile.__init__`; store as `self.vy`. In `Projectile.update()`, apply `self.vy += 0.15` (mild gravity) and `self.rect.y += int(self.vy)` each frame.
- In `Ranged._fire(player)`, compute a mild vy arc toward the player's current Y:
  ```python
  dist_x = abs(player.rect.centerx - self.rect.centerx)
  travel_frames = max(1, dist_x / RANGED_PROJ_SPEED)
  raw_vy = (player.rect.centery - self.rect.centery) / travel_frames
  vy = max(-4.0, min(4.0, raw_vy))
  ```
  Pass `vy=vy` to the `Projectile` constructor.

`entities/jumper.py`:
- Add `self._burst_remaining = JUMPER_BURST_COUNT` and `self._burst_pause = 0` to `__init__`.
- In `_do_chase_jump`, implement burst:
  - If `self._burst_pause > 0`: decrement and return early (no jump).
  - If `self.on_ground and self._jump_cooldown <= 0`: launch jump, decrement `_burst_remaining`. If `_burst_remaining <= 0`, reset `_burst_remaining = JUMPER_BURST_COUNT` and set `_burst_pause = JUMPER_BURST_PAUSE`.
- Replace `knockback_y=-4.5` hardcode in melee `AttackHitbox` with conditional: if `not self.on_ground and player.rect.centery > self.rect.centery` use `JUMPER_KNOCKBACK_Y_AERIAL` (downward spike), else use `JUMPER_KNOCKBACK_Y_GROUND`.
- Replace the existing `knockback_y` hardcode constant with the new settings constants.

**Acceptance criteria — done when:**
- ShieldGuard takes 0 damage when struck from the front (shield side); full damage from behind.
- ShieldGuard faces patrol direction during patrol; only turns toward player in CHASE/ATTACK.
- Ranged fires every ~0.9 s (55 frames) with projectiles that arc toward the player's Y.
- Ranged projectiles use `RANGED_PREFERRED_DIST` (not the hardcode 220).
- Jumper fires 2 hops in quick succession then pauses ~1.17 s before bursting again.
- Jumper aerial attack sends player downward; ground attack sends player upward.
- `python main.py` launches without ImportError.

---

### Task P2-5: Upgrade System ✅ DONE (2026-04-21)

**What was built:**
- `settings.py`: `UPGRADE_HP_BONUS = 25`, `UPGRADE_DMG_BONUS = 5`, `UPGRADE_RES_BONUS = 20`.
- `entities/player.py`: `attack_damage_bonus: int = 0` and `max_resource_bonus: float = 0.0` additive fields; applied in `_handle_attack` damage calc and `max_resource` property.
- `scenes/gameplay.py`: `_apply_upgrade_to_player()` helper; `_setup_upgrade_choices()` / `_confirm_upgrade()` / `_draw_upgrade_screen()` methods; upgrade triggered on Warden (`_boss`) death; saved upgrades reapplied on `on_enter()`; upgrade screen intercepts all input until dismissed.

---

### Task P2-0c: Critical Bug-Fix Sprint ✅ DONE (2026-04-23)

**What was built:**
- `entities/player.py`: `self.ability_slots = ABILITY_SLOTS_DEFAULT` in `__init__`; `if self.ability_slots < 1: return` gate in `_handle_ability()`.
- `scenes/gameplay.py`: Slot restore from save in `on_enter()`; `AbilityOrb` spawn/collect/draw loops; `_setup_upgrade_choices()` early-return on dead player; Architect `announce_phase` block with phase-4 arena-shrink; banner index driven by `_boss_dialogue._index`; `"res"` upgrade no longer calls `_regen_resource`; shrink-wall injection uses independent left/right conditions.
- `world/tilemap.py`: `ability_orb_spawns` list in `__init__`; `'A'` tile handler in `_parse()`.
- `entities/architect.py`: `level_width` constructor param; `arena_max` uses `self._level_width`; `announce_phase = 4` on phase-4 entry.
- `systems/collectible.py`: `if not self.alive: return` guard in `AbilityOrb.collect()`.

_Unblocked by P2-5 completion. Review-agent 2026-04-21 pass found these correctness bugs that must be fixed before P2-6 content work. Critical bugs marked 🔴; minor/deferred marked ⚠️._

**Files to touch:**
- `scenes/gameplay.py` (BUG-018, BUG-021, BUG-022, BUG-023, BUG-025)
- `entities/player.py` (BUG-019)
- `world/tilemap.py` (BUG-019)
- `entities/architect.py` (BUG-020)
- `systems/collectible.py` (BUG-024)

**Fixes required:**

- 🔴 **BUG-018** `gameplay.py`: In `_setup_upgrade_choices()` (or at its call site), add `if not self.player.alive: return` to prevent the upgrade screen from activating when the player dies on the same frame as the Warden.

- 🔴 **BUG-019** (three-file fix):
  1. `entities/player.py`: Add `self.ability_slots: int = ABILITY_SLOTS_DEFAULT` to `__init__`; import `ABILITY_SLOTS_DEFAULT` from settings; add `if self.ability_slots < 1: return` at the top of `_handle_ability()`.
  2. `scenes/gameplay.py:on_enter()`: After creating the player, add `self.player.ability_slots = save.get("ability_slots", ABILITY_SLOTS_DEFAULT)`. Spawn `AbilityOrb` objects for `tilemap.ability_orb_spawns`.
  3. `world/tilemap.py`: Add `self.ability_orb_spawns: list = []` to `__init__`; add `'A'` tile handler in `_parse()` appending `(x + TILE_SIZE//2, y - 18)`.

- 🔴 **BUG-020** `architect.py` / `gameplay.py`: Add `level_width: int = SCREEN_WIDTH` constructor parameter to `Architect.__init__`, store as `self._level_width`. In `_update_ai`, replace `arena_max = SCREEN_WIDTH - TILE_SIZE * 4` with `arena_max = self._level_width - TILE_SIZE * 4`. In `gameplay.py`, pass `level_width=self.tilemap.width` when instantiating Architect.

- 🔴 **BUG-021** `gameplay.py`: After the Warden announce block (around line 471), add a parallel block for `self._architect`: check `self._architect.announce_phase`, consume it, show the phase banner, and trigger arena-shrink on phase 4. The shrink should reference `self._architect`, not `self._boss`.

- ⚠️ **BUG-022** `gameplay.py`: Drive the boss-intro banner index from `self._boss_dialogue._index` rather than `active_boss._intro_line_idx`. The entity-level `_intro_line_timer` / `_intro_line_idx` increment in `_tick_boss_intro` can be removed.

- ⚠️ **BUG-023** `gameplay.py`: In `_apply_upgrade_to_player`, remove the `_regen_resource(UPGRADE_RES_BONUS)` call for the `"res"` case so resource is not silently refilled above checkpoint state on every level load.

- ⚠️ **BUG-024** `collectible.py`: Add `if not self.alive: return` as the first line of `AbilityOrb.collect()`.

- ⚠️ **BUG-025** `gameplay.py`: Separate the shrink-wall injection conditions — add the left wall rect only when `self._shrink_left_x > 0`, and add the right wall rect only when `self._shrink_right_x < self.tilemap.width` (independent checks, not coupled via a single condition on `_shrink_left_x`).

**Acceptance criteria — done when:**
- `python main.py` launches without ImportError.
- Player ability is locked at game start; picking up an `AbilityOrb` unlocks it and persists across saves.
- Warden kills player simultaneously → upgrade screen does not appear; death sequence runs normally.
- Architect teleports freely across the full width of LEVEL_10 (2080 px), not only into the left 1152 px.
- Architect phase 2/3/4 transitions display the phase-announce banner.
- `"res"` upgrade does not refill the resource bar above checkpoint state on level reload.

---

### Task P2-6: Enemy Drops ✅ DONE (2026-04-23)

**What was built:**
- `settings.py`: `HEAT_CORE_HEAL` and `SOUL_SHARD_HEAL` raised from 8 → 12 (per hk-agent review).
- `entities/boss.py`: `get_drop_fragments()` spread widened from ±20 px to ±40 px so fragments don't stack under the Warden corpse.
- All other P2-6 code (`HeatCore`, `SoulShard`, faction_drop attributes, gameplay loops) was already present from prior commits.

**Files to touch:**
- `systems/collectible.py` (add `HeatCore` and `SoulShard` classes)
- `entities/enemy.py` (update `get_drop_fragments()` to return faction-appropriate drop)
- `entities/boss.py` (override drop to return 3 fragments)
- `scenes/gameplay.py` (handle pickup collision + apply faction heal)
- `settings.py` (add drop constants)

**What to build:**

`settings.py`:
```python
HEAT_CORE_SIZE       = 10      # px square
HEAT_CORE_HEAL       = 12      # HP healed when picked up by Fleshforged (raised from 8 per hk-agent review)
HEAT_CORE_COLOR      = (220, 100, 20)   # Burnt orange
SOUL_SHARD_SIZE      = 10
SOUL_SHARD_HEAL      = 12      # HP healed when picked up by Marked (raised from 8 per hk-agent review)
SOUL_SHARD_COLOR     = (130, 80, 220)   # Soft purple (matches SOUL_FRAGMENT_COLOR)
DROP_BOB_SPEED       = 0.08    # radians/frame for bobbing sinusoid
DROP_BOB_AMP         = 3       # pixel amplitude of bob
```

`systems/collectible.py` — add two new classes after `SoulFragment`:

`HeatCore(x, y)`: bright orange spinning diamond collectible.
- `rect` (10×10 px, centered on x, y), `alive=True`, `_bob=0`.
- `update()`: `_bob += DROP_BOB_SPEED`; shift `rect.y` by `sin(_bob) * DROP_BOB_AMP`.
- `draw(surface, camera)`: draw a small diamond using `HEAT_CORE_COLOR`.
- `collect(player, game)`: if `player.faction == FACTION_FLESHFORGED`, call `player.heal(HEAT_CORE_HEAL)`; always set `alive = False`.

`SoulShard(x, y)`: soft purple diamond collectible.
- Same structure as `HeatCore` but uses `SOUL_SHARD_COLOR` and heals Marked players (`SOUL_SHARD_HEAL`).

`entities/enemy.py` — update `get_drop_fragments()`:
- Rename to still return `SoulFragment` by default (backward-compatible), but also check `self.faction_drop` attribute.
- Add `self.faction_drop: str = ""` in `Enemy.__init__` (empty string = neutral drop).
- If `faction_drop == FACTION_FLESHFORGED`: return one `HeatCore` at center.
- If `faction_drop == FACTION_MARKED`: return one `SoulShard` at center.
- Else (neutral): return one `SoulFragment` at center (existing behavior).
- ShieldGuard and Ranged are Fleshforged-flavored → set `faction_drop = FACTION_FLESHFORGED` in their `__init__`.
- Jumper and Crawler are Marked-flavored → set `faction_drop = FACTION_MARKED` in their `__init__`.
- Base Enemy (and Boss) remain neutral (SoulFragment).

`entities/boss.py` — override `get_drop_fragments()`:
- Return three `SoulFragment` objects spread around the boss center (+/- 40px offsets — widened from ±20 px per hk-agent review to avoid stacking under corpse).

`scenes/gameplay.py`:
- Import `HeatCore` and `SoulShard` from `systems.collectible`.
- In `update()`, after fragment collection, add a similar loop for `self.drops: list = []` (initialise in `on_enter()`).
- When enemies die, call `get_drop_fragments()` — the returned objects (now HeatCore/SoulShard/SoulFragment depending on enemy type) go into `self.drops`.
- Each frame, check `player.rect.colliderect(drop.rect)` → call `drop.collect(player, game)` → remove from list.
- In `draw()`, call `drop.draw(surface, camera)` for all drops after fragments.

**Acceptance criteria — done when:**
- Killing a ShieldGuard or Ranged spawns a HeatCore; Fleshforged player picking it up heals 8 HP; Marked player gets no heal but the drop is consumed.
- Killing a Jumper or Crawler spawns a SoulShard; Marked player heals 8 HP on pickup.
- Killing the Warden boss drops 3 SoulFragments (spread, not stacked).
- Drops bob up and down while alive.
- `python main.py` launches without ImportError.

---

### Task P2-7: Environmental Hazards ✅ DONE (2026-04-23)

**What was built:**
- `settings.py`: 6 new constants (`SPIKE_DAMAGE`, `CRUMBLE_STAND_FRAMES`, `CRUMBLE_RESPAWN_FRAMES`, `SPIKE_COLOR`, `CRUMBLE_COLOR`, `CRUMBLE_WARNING_COLOR`).
- `world/tilemap.py`: `spike_tiles` and `crumble_tiles` lists in `__init__`; `'s'` handler (non-solid, appends to `spike_tiles`); `'~'` handler (initially solid + added to `crumble_tiles` dict); test spikes added to LEVEL_3 row 9; LEVEL_4 row 9 left platform converted to crumble tiles.
- `scenes/gameplay.py`: spike damage check in update loop; full crumble state machine (solid→warning→falling→respawn) that adds/removes rects from `tilemap.tiles`; `_draw_hazards()` method rendering spike triangles and crumble rects with crack overlay in warning state.

**Files to touch:**
- `world/tilemap.py` (parse `'s'` spike tiles and `'~'` crumble tiles)
- `systems/physics.py` (or `gameplay.py`) (spike damage, crumble logic)
- `scenes/gameplay.py` (tick crumble platforms, draw hazards, apply spike damage)
- `settings.py` (hazard constants)

**What to build:**

`settings.py`:
```python
SPIKE_DAMAGE        = 20    # HP lost per frame of contact with a spike tile
CRUMBLE_STAND_FRAMES = 30   # Frames player must stand on crumble tile before it falls
CRUMBLE_RESPAWN_FRAMES = 180  # Frames before a crumble tile reappears
SPIKE_COLOR         = (180, 60, 60)   # Dark red spike pixel color
CRUMBLE_COLOR       = (110, 90, 60)   # Brownish crumble tile color
CRUMBLE_WARNING_COLOR = (160, 120, 40)  # Color shift when about to crumble
```

`world/tilemap.py`:
- In `_parse()`, add: `'s'` → append `pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)` to `self.spike_tiles: list = []`; mark as non-solid (player can enter but takes damage).
- `'~'` → append `{'rect': pygame.Rect(x, y, TILE_SIZE, TILE_SIZE), 'timer': 0, 'state': 'solid'}` dict to `self.crumble_tiles: list = []`; initially solid.

`scenes/gameplay.py`:
- In `update()`, after physics: check if player rect overlaps any spike tile rect → `player.take_damage(SPIKE_DAMAGE)`.
- For each crumble tile in `tilemap.crumble_tiles`:
  - If `state == 'solid'` and player stands on its top edge: increment `timer`; change color to warning at `timer > CRUMBLE_STAND_FRAMES * 0.6`; at `timer >= CRUMBLE_STAND_FRAMES` set `state = 'falling'`, `timer = 0`, remove from solid-tile set used by physics.
  - If `state == 'falling'`: increment `timer`; at `>= CRUMBLE_RESPAWN_FRAMES` set `state = 'solid'`, `timer = 0`, add back to solid-tile set.
- In `draw()`, render spike tiles as a row of small triangles (3-point polygon per tile), crumble tiles as colored rects with a crack overlay line when in warning state.

**Acceptance criteria — done when:**
- Stepping on a spike tile immediately deals 20 HP damage.
- Standing on a `'~'` tile for 30 frames causes it to disappear (player falls through).
- Crumble tile reappears after 3 seconds (180 frames).
- Visual warning (color shift) appears before the tile crumbles.
- `python main.py` launches without ImportError.

---

### Task P2-8: HK Feel Sprint — Architect / Upgrades / Minimap ✅ DONE (2026-04-23)

**What was built:**
- `settings.py`: `ARCHITECT_TELEPORT_CD` 200→140; `ARCHITECT_TELEPORT_WARN=20`; `ARCHITECT_MINION_CD` 300→210; `UPGRADE_DMG_BONUS` 5→6; `UPGRADE_DMG_MAX_STACKS=3`; `UPGRADE_RES_REGEN_BONUS=0.008`.
- `entities/architect.py`: `level_floor_y` constructor param + Y-floor clamp on teleport; 20-frame white-blue warn timer before position change; `vx=0` lock during warning; warn flash overlay in `draw()`.
- `entities/player.py`: `_res_regen_bonus: float = 0.0`; passive regen uses `0.05 + self._res_regen_bonus`.
- `scenes/gameplay.py`: "dmg" upgrade capped at `UPGRADE_DMG_MAX_STACKS`; "res" upgrade adds `UPGRADE_RES_REGEN_BONUS` to player; live-Crawler count check discards excess beyond cap of 2; `level_floor_y` passed to Architect constructor.
- `systems/minimap.py`: `_LEVEL_ORDER` extended to 13 keys; two-row layout (levels 1–5 top, levels 6–10 bottom with faction-pair columns and single nodes for 9/10).

_Blocked until P2-7 is complete. Implements all outstanding hk-agent recommendations from the 2026-04-21 pass._

**Files to touch:**
- `settings.py` (new and updated constants)
- `entities/architect.py` (teleport warn + cadence + minion cap + Y floor clamp)
- `entities/player.py` (upgrade DMG cap, RES regen bonus)
- `systems/minimap.py` (extend room-chain to levels 6–10)

**What to build:**

`settings.py` — add / update:
```python
ARCHITECT_TELEPORT_CD   = 140   # was 200 — tighter cadence from phase 2 onward
ARCHITECT_TELEPORT_WARN = 20    # NEW — pre-teleport lock+pulse frames before position jump
ARCHITECT_MINION_CD     = 210   # was 300 — more frequent minion pressure; cap live crawlers at 2
UPGRADE_DMG_BONUS       = 6     # was 5 — marginal per-swing increase
UPGRADE_DMG_MAX_STACKS  = 3     # NEW — cap to prevent Overdrive compound runaway
UPGRADE_RES_REGEN_BONUS = 0.008 # NEW — per-upgrade additive boost to 0.05/frame passive regen
```

`entities/architect.py`:
- Add `_teleport_warn_timer = 0` to `__init__`.
- Before the teleport position change, decrement `_teleport_cd` as normal; when it reaches 0, instead of teleporting immediately, set `_teleport_warn_timer = ARCHITECT_TELEPORT_WARN` and lock `vx = 0`.
- While `_teleport_warn_timer > 0`, decrement it and draw a distinct white-blue pulse (separate from `_rage_flash_timer`). When it reaches 0, execute the actual position change.
- In `_on_phase2_enter()`, replace `ARCHITECT_TELEPORT_CD` constant reference (already imported) — no code change needed since the constant change handles this.
- Add a cap on simultaneous live crawlers: in the minion-spawn branch, count `sum(1 for e in live_enemies if isinstance(e, Crawler))` before spawning; skip if `>= 2`. Gameplay.py must pass the enemy list to Architect or the cap can be enforced in gameplay.py after the minion call.
- For the Y floor clamp: after setting `self.rect.centerx`, also set `self.rect.bottom = self._level_floor_y` where `self._level_floor_y` is stored from a constructor parameter (default `SCREEN_HEIGHT - TILE_SIZE * 2`). Pass `level_floor_y=self.tilemap.height - TILE_SIZE * 2` when spawning in `gameplay.py`.

`entities/player.py`:
- Apply `UPGRADE_DMG_MAX_STACKS` cap in `_apply_upgrade_to_player` (or inside `gameplay.py`): count `"dmg"` entries in `save_data["upgrades"]`; skip if `>= UPGRADE_DMG_MAX_STACKS`.
- Add `self._res_regen_bonus: float = 0.0` to `__init__`. In the passive regen line (`player.py:192`), change `0.05` to `0.05 + self._res_regen_bonus`. In `gameplay.py` `_apply_upgrade_to_player`, for the `"res"` case, add `player._res_regen_bonus += UPGRADE_RES_REGEN_BONUS`.

`systems/minimap.py`:
- Extend `_LEVEL_ORDER` to all 13 level keys: `["level_1", "level_2", "level_3", "level_4", "level_5", "level_6_marked", "level_6_fleshforged", "level_7_marked", "level_7_fleshforged", "level_8_marked", "level_8_fleshforged", "level_9", "level_10"]`.
- Add matching `_LEVEL_LABELS` entries for all new keys (short names to fit the panel: "VI-M", "VI-F", etc.).
- Lay the room chain in two rows: levels 1–5 top row, levels 6–10 bottom row (use the faction branches as two parallel nodes in row 2).

**Acceptance criteria — done when:**
- Architect flashes a distinct pre-teleport warning for 20 frames before jumping position.
- No more than 2 live Crawlers in the arena at once.
- 3rd `"dmg"` upgrade selection works; a 4th is blocked/skipped.
- Resource upgrade visibly speeds up the regen bar.
- Minimap room-chain shows all 13 level nodes across 2 rows; current level is highlighted regardless of faction branch.
- `python main.py` launches without ImportError.

---

## Phase 3 — Story Integration ✅ COMPLETE (2026-04-25)

All Phase 3 tasks are done. The game has mid-game lore cutscenes, faction-tinted enemies, two ending branches, NPC encounters, and collectible lore items. Phase 4 (Polish) is next.

**Priority order for build-agent** (tackle in this order):

1. ~~**P3-0b (critical bug-fix sprint)**~~ ✅ **DONE (2026-04-27)** — BUG-026 through BUG-031 and HK-P3-A/B/C all verified in code.
2. ~~**P3-1 (Mid-game lore beats)**~~ ✅ **DONE (2026-04-25)**
3. ~~**P3-2 (Faction enemy design)**~~ ✅ **DONE (2026-04-25)**
4. ~~**P3-3 (Ending branches)**~~ ✅ **DONE (2026-04-25)**
5. ~~**P3-4 (NPC encounters)**~~ ✅ **DONE (2026-04-25)**
6. ~~**P3-5 (Collectible lore items)**~~ ✅ **DONE (2026-04-25)**

---

### Task P3-0b: Critical Bug-Fix Sprint (Phase 3 review pass) ✅ DONE (2026-04-27)

_Review-agent 2026-04-25 pass found these bugs in Phase 3 code. All verified fixed in code as of 2026-04-27 orchestrator check._

**Files to touch:**
- `scenes/marked_ending.py` (BUG-026, HK-P3-B)
- `scenes/fleshforged_ending.py` (BUG-026, HK-P3-B)
- `scenes/gameplay.py` (BUG-027, BUG-028, BUG-029, BUG-031, HK-P3-A)
- `world/tilemap.py` (BUG-030)
- `settings.py` (HK-P3-A, HK-P3-C)
- `entities/enemy.py` (HK-P3-C)

**Fixes required:**

- 🔴 **BUG-026** `marked_ending.py:82–85` / `fleshforged_ending.py:82–85`: Rapid double-press on SPACE skips two beats in ending scenes because `_advance()` does not guard against being called when `DialogueBox` is already done. Fix: add `if self._dialogue.is_done(): return` as the first line of `_advance()` in both files.

- 🔴 **BUG-027** `gameplay.py:1360`: `_draw_phase_announce` color check only tests for `"UNLEASHED"` (Warden-specific), so all Architect phase banners (`"AWAKENED"`, `"UNBOUND"`, `"ABSOLUTE"`) always render in amber. Phase 4 `"ABSOLUTE"` should escalate to deep red. Fix: extend the condition to `("UNLEASHED" in self._boss_phase_text or "ABSOLUTE" in self._boss_phase_text)`.

- 🔴 **BUG-028** `gameplay.py:257–261`: `_level_faction_tint` loop applies `faction_tint` to every entry in `self.enemies` including `Boss` and `Architect`, washing out their phase-scaling colors in levels 6–8. Fix: skip boss types — `if not isinstance(e, (Boss, Architect)): e.faction_tint = _tint`.

- 🔴 **BUG-029** `gameplay.py:757–779`: Architect defeat dialogue auto-advances on 120-frame timers with no player SPACE shortcut and no hint text, locking the player out for up to 8 seconds silently. Fix: intercept SPACE/RETURN in `handle_event` when `self._architect and not self._architect.alive and not self._architect_victory_done` to advance `_defeat_line_idx` immediately; also render a `"SPACE — continue"` hint in `_draw_architect_defeat`.

- ⚠️ **BUG-030** `tilemap.py` `LEVEL_2`: Row 16 contains a `'C'` checkpoint inside the sealed sub-floor chamber (below the solid ground at rows 12–13), which is permanently unreachable. Fix: remove the `'C'` from row 16 or relocate it to a reachable platform row (3–10) in LEVEL_2.

- ⚠️ **BUG-031** `gameplay.py:461–463`: When NPC dialogue is active the update() early-return skips the proximity hint loop, leaving `_show_hint = True` so the "E" badge renders on top of an open dialogue box. Fix: add `for npc in self.npcs: npc._show_hint = False` inside the `_npc_dialogue is not None` early-return block before returning.

**HK feel (fold in, low-risk):**

- **HK-P3-A** `settings.py`: Raise `NPC_INTERACT_DIST` from 60 → 80 px; also add a vertical proximity gate in `gameplay.py:783–784` (`abs(player.rect.centery - npc.rect.centery) < NPC_INTERACT_DIST`).
- **HK-P3-B** `scenes/marked_ending.py` and `scenes/fleshforged_ending.py`: Change the background lerp speed constant `spd = 0.07` to `spd = 0.18` so color shifts are beat-synchronous.
- **HK-P3-C** `settings.py`: Add `FACTION_TINT_BLEND = 0.65`, `FLESHFORGED_TINT_COLOR = (200, 110, 50)`, `MARKED_TINT_COLOR = (100, 60, 160)`. Update `entities/enemy.py` faction tint blend to use these constants (was hardcoded `0.5` and `(160, 130, 100)`).

**Acceptance criteria — done when:**
- Rapid double-tapping SPACE in an ending scene advances exactly one beat per press.
- Architect `"ABSOLUTE"` phase banner renders in deep red, not amber.
- Boss and Architect entity colors are unaffected by faction tinting in levels 6–8.
- Architect defeat dialogue can be advanced by pressing SPACE; a hint is visible.
- LEVEL_2 has no checkpoint inside the solid sub-floor.
- NPC "E" badge disappears while a dialogue box is open.
- NPC "E" hint triggers at 80 px (not 60); vertical proximity gate active.
- Ending scene background color shifts track beat advances (lerp speed 0.18).
- Faction tint uses `FLESHFORGED_TINT_COLOR`/`MARKED_TINT_COLOR` constants; blend weight is `FACTION_TINT_BLEND = 0.65`.
- `python main.py` launches without ImportError.

---

### Task P3-1: Mid-Game Lore Beats ✅ DONE (2026-04-25)

**Files to touch:**
- `scenes/marked_prologue.py` (add `beat_start` kwarg + 4 new beats at indices 21–24)
- `scenes/fleshforged_prologue.py` (add `beat_start` kwarg + 4 new beats at indices 22–25)
- `scenes/gameplay.py` (trigger cutscene on level 3 → level 4 transition)
- `settings.py` (add `MARKED_LORE_BEAT_START`, `FLESHFORGED_LORE_BEAT_START`)

**What to build:**

`settings.py`:
```python
MARKED_LORE_BEAT_START      = 21
FLESHFORGED_LORE_BEAT_START = 22
```

`scenes/marked_prologue.py` and `scenes/fleshforged_prologue.py`:
- In `on_enter(**kwargs)`, read `beat_start = kwargs.get("beat_start", 0)` and initialise the beat index to that value.
- After the final beat, check `kwargs.get("return_level")`. If set, call `game.change_scene(SCENE_GAMEPLAY, level=kwargs["return_level"])`. Otherwise continue to the normal next scene (existing behavior unchanged when `beat_start=0`).

`scenes/marked_prologue.py` — append 4 beats at the end:
- Beat 21: bg `(30, 20, 50)`, speaker `"Rune-Archivist"`, text `"The Runed Archives. Hidden beneath the Foundry. Kael knew it was here."`
- Beat 22: bg `(40, 15, 60)`, speaker `"Rune-Archivist"`, text `"The Fleshforged do not transcend. They consume. Every augment is a theft — soul energy harvested from the Marked."`
- Beat 23: bg `(50, 20, 70)`, speaker `"Rune-Archivist"`, text `"The Architect was not built. It was summoned. It is what remains of the Founder after the first Rite failed."`
- Beat 24: bg `(20, 10, 40)`, speaker `"???"`, text `"Kael gave you this knowledge. Use it."`

`scenes/fleshforged_prologue.py` — append 4 beats at the end:
- Beat 22: bg `(60, 30, 10)`, speaker `"Sera's Datalog"`, text `"The Forgemaster's schematics. Sera copied them before the ambush. The Marked sabotaged the Rite deliberately."`
- Beat 23: bg `(70, 25, 10)`, speaker `"Sera's Datalog"`, text `"Soul energy is not mystical. It is thermodynamic — latent chemical potential extracted by augment cores. The Marked know this and call it heresy."`
- Beat 24: bg `(80, 30, 10)`, speaker `"Sera's Datalog"`, text `"The Architect is a weapons system. Whoever activates it first controls the city's energy supply. The Marked want it silent. You cannot let that happen."`
- Beat 25: bg `(50, 20, 10)`, speaker `"???"`, text `"Sera built this into your augments. Find the Architect before they do."`

`scenes/gameplay.py`:
- In `_check_level_transition()` (or `_begin_transition()`), when leaving level_3 for level_4, replace the direct `_begin_transition(SCENE_GAMEPLAY, level="level_4")` with a cutscene trigger:
  ```python
  if self._level_name == "level_3":
      faction_scene = SCENE_MARKED_PROLOGUE if self.game.player_faction == FACTION_MARKED \
                      else SCENE_FLESHFORGED_PROLOGUE
      beat = MARKED_LORE_BEAT_START if self.game.player_faction == FACTION_MARKED \
             else FLESHFORGED_LORE_BEAT_START
      self._begin_transition(faction_scene, beat_start=beat, return_level="level_4")
  ```

**Acceptance criteria — done when:**
- Completing level 3 triggers the faction cutscene before level 4 loads.
- Marked players see 4 new beats from the Rune-Archivist.
- Fleshforged players see 4 new beats from Sera's Datalog.
- After the cutscene, level 4 loads and play resumes normally.
- Starting a new game still plays prologues from beat 0 (default behavior unbroken).
- `python main.py` launches without ImportError.

---

### Task P3-2: Faction Enemy Design ✅ DONE (2026-04-25)

**Files to touch:**
- `entities/enemy.py` (add `faction_tint` attribute, blend in draw)
- `scenes/gameplay.py` (assign tint when spawning enemies based on level name)

**What to build:**

`entities/enemy.py`:
- Add `self.faction_tint: str = ""` to `Enemy.__init__`.
- In `draw(surface, camera)`, after computing the base draw color, blend it 50/50 toward a tint target if `faction_tint` is set:
  - `FACTION_FLESHFORGED` tint target: `(160, 130, 100)` (iron-orange).
  - `FACTION_MARKED` tint target: `(100, 60, 160)` (acolyte purple).
  - Blend formula: `blended = tuple(int(a * 0.5 + b * 0.5) for a, b in zip(base_color, tint))`.
  - Apply the blended color for the entity rect draw only (not the health bar).

`scenes/gameplay.py`:
- Add module-level helper `_level_faction_tint(level_name: str) -> str`:
  - `"level_6_marked"`, `"level_7_marked"`, `"level_8_marked"` → `FACTION_FLESHFORGED` (Fleshforged enemies appear in Marked zones).
  - `"level_6_fleshforged"`, `"level_7_fleshforged"`, `"level_8_fleshforged"` → `FACTION_MARKED`.
  - All other levels → `""` (no tint).
- After spawning all enemies in `on_enter()`, set `e.faction_tint = _level_faction_tint(level_name)` for each enemy `e`.

**Acceptance criteria — done when:**
- Enemies in Marked faction levels (6M/7M/8M) appear iron-orange blended.
- Enemies in Fleshforged faction levels (6F/7F/8F) appear purple blended.
- Enemies in neutral levels (1–5, 9, 10) are unaffected.
- `python main.py` launches without ImportError.

---

### Task P3-3: Ending Branches ✅ DONE (2026-04-25)

**Files to touch:**
- `scenes/marked_ending.py` (create)
- `scenes/fleshforged_ending.py` (create)
- `core/game.py` (register new scenes)
- `scenes/gameplay.py` (trigger ending after Architect defeat)
- `settings.py` (add `SCENE_MARKED_ENDING`, `SCENE_FLESHFORGED_ENDING`)

**What to build:**

`settings.py`:
```python
SCENE_MARKED_ENDING      = "marked_ending"
SCENE_FLESHFORGED_ENDING = "fleshforged_ending"
```

`scenes/marked_ending.py`: `MarkedEnding(BaseScene)` — structured identically to `MarkedPrologue` (scrolling DialogueBox, per-beat background, fade-in transitions, ESC to skip). 8 beats:
1. bg `(20, 10, 40)`, speaker `"???"`: `"The Rite is complete. The ink holds."`
2. bg `(30, 15, 50)`, speaker `"Narrator"`: `"The Architect's collapse unseals the Archive vault. Ancient rune-scripts flood the surface for the first time in centuries."`
3. bg `(40, 20, 60)`, speaker `"Narrator"`: `"The Fleshforged machinery grinds to silence. Without the stolen soul-current, the augments go cold."`
4. bg `(50, 25, 70)`, speaker `"Rune-Archivist"`: `"You are the first Transcendent. What was taken from Kael was not wasted."`
5. bg `(30, 15, 55)`, speaker `"Narrator"`: `"The city does not forget its debts. The Marked rebuild in the silence."`
6. bg `(20, 10, 45)`, speaker `"Narrator"`: `"You do not return to the mines. The ink does not allow it."`
7. bg `(15, 8, 40)`, speaker `"Narrator"`: `"Somewhere beneath the Foundry, a new Rite is already being prepared."`
8. bg `(10, 5, 30)`, speaker `"???"`: `"The cycle endures."`
- After beat 8: set `game.save_data["ending"] = "marked"`, call `game.save_to_disk()`, call `game.change_scene(SCENE_MAIN_MENU)`.

`scenes/fleshforged_ending.py`: `FleshforgedEnding(BaseScene)` — same structure. 8 beats:
1. bg `(60, 25, 5)`, speaker `"???"`: `"The Architect is yours. Sera would call this victory."`
2. bg `(70, 30, 5)`, speaker `"Narrator"`: `"The energy lattice snaps into place. The city's heat-grid flickers back to life under Fleshforged control."`
3. bg `(60, 25, 5)`, speaker `"Narrator"`: `"The Marked flee underground. Without the Architect's amplification, their Rites are limited to single practitioners."`
4. bg `(50, 20, 5)`, speaker `"Sera's Datalog"`: `"Addendum — final entry. Power source secured. City access: 100%. Soul-drain reversed."`
5. bg `(40, 15, 5)`, speaker `"Narrator"`: `"The augments remember her work. Every Fleshforged operative carries a piece of what Sera built."`
6. bg `(30, 12, 5)`, speaker `"Narrator"`: `"The Foundry rebuilds. It does not sleep."`
7. bg `(20, 10, 5)`, speaker `"Narrator"`: `"Somewhere beneath the old Archive, something ancient did not die."`
8. bg `(10, 5, 5)`, speaker `"???"`: `"The cycle endures."`
- After beat 8: set `game.save_data["ending"] = "fleshforged"`, call `game.save_to_disk()`, call `game.change_scene(SCENE_MAIN_MENU)`.

`core/game.py`:
- Import `MarkedEnding`, `FleshforgedEnding` from their respective modules.
- Register both scenes at startup using the same pattern as existing scenes.

`scenes/gameplay.py`:
- In the Architect defeat handler (where `game.save_data["victory"] = True` is set), add:
  ```python
  ending = SCENE_MARKED_ENDING if self.game.player_faction == FACTION_MARKED \
           else SCENE_FLESHFORGED_ENDING
  self._begin_transition(ending)
  ```

**Acceptance criteria — done when:**
- Defeating the Architect as Marked triggers the Marked ending (purple beats).
- Defeating the Architect as Fleshforged triggers the Fleshforged ending (orange beats).
- All 8 beats play through; after the last beat the game returns to main menu.
- `save_data["ending"]` is written correctly and persists.
- `python main.py` launches without ImportError.

---

### Task P3-4: NPC Encounters ✅ DONE (2026-04-25)

**Files to touch:**
- `entities/npc.py` (create)
- `world/tilemap.py` (add `'N'` tile handler, `npc_spawns` list)
- `scenes/gameplay.py` (spawn NPCs, `E` key interaction, proximity hint)
- `settings.py` (add NPC constants)

**What to build:**

`settings.py`:
```python
NPC_WIDTH         = 24
NPC_HEIGHT        = 40
NPC_INTERACT_DIST = 60      # pixels — E-key trigger range
NPC_COLOR         = (140, 160, 140)
```

`entities/npc.py`: `NPC` class (not an Entity — cannot take damage).
- `__init__(x, y, name="???", lines=None)`: stores `rect` (NPC_WIDTH × NPC_HEIGHT, feet at `y`), `name`, `lines: list[tuple[str, str]]` (default `[]`). `_show_hint = False`.
- `draw(surface, camera)`: draw colored rect using `NPC_COLOR`; if `_show_hint`, draw a small `"E"` label centered 8 px above the rect.

`world/tilemap.py`:
- Add `self.npc_spawns: list = []` to `__init__`.
- In `_parse()`: `'N'` → append `(x + TILE_SIZE//2, y)` to `npc_spawns`.
- Place one `'N'` tile in LEVEL_3 (row 8, near the center) and one in LEVEL_5 (row 5, left of the checkpoint).

`scenes/gameplay.py`:
- Define a module-level dict `_NPC_DIALOGUE` mapping `(level_name, npc_index)` keys to `list[tuple[str, str]]`:
  ```python
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
  ```
- In `on_enter()`: import `NPC`; spawn `NPC` objects for `tilemap.npc_spawns`; assign lines from `_NPC_DIALOGUE`.
- In `update()`: for each NPC, set `npc._show_hint = (dist_to_player < NPC_INTERACT_DIST)`.
- In `handle_event()`: on `K_e`, if any NPC is in hint range and no dialogue is active, open a `DialogueBox` with that NPC's `lines`.
- In `draw()`: draw all NPCs (after tiles, before HUD).

**Acceptance criteria — done when:**
- An NPC appears in level 3 and level 5.
- Walking within 60 px shows a `"E"` label above the NPC.
- Pressing `E` opens dialogue; SPACE advances it; last line dismisses the box.
- `python main.py` launches without ImportError.

---

### Task P3-5: Collectible Lore Items ✅ DONE (2026-04-25)

**Files to touch:**
- `systems/collectible.py` (add `LoreItem` class)
- `world/tilemap.py` (add `'L'` tile handler, `lore_spawns` list)
- `scenes/gameplay.py` (spawn lore items, collect, show text overlay)
- `settings.py` (add lore constants)

**What to build:**

`settings.py`:
```python
LORE_ITEM_SIZE       = 16
LORE_ITEM_COLOR      = (160, 140, 100)    # Parchment tone
LORE_DISPLAY_FRAMES  = 300   # 5 seconds at 60 FPS
```

`systems/collectible.py` — add `LoreItem(x, y, lore_id, text)`:
- `rect` (LORE_ITEM_SIZE × LORE_ITEM_SIZE, centered on x, y), `alive=True`, `_glow=0`.
- `update()`: `_glow = (_glow + 1) % 60`.
- `draw(surface, camera)`: draw a rect with `LORE_ITEM_COLOR`; brightness pulses by ±15 with `sin(_glow / 60 * 2π)`.
- `collect(player, game)`: if `lore_id` not in `game.save_data.setdefault("lore_found", [])`, append it; call `game.save_to_disk()`; set `alive = False`; return `self._text` for the caller to display. If already collected, just set `alive = False` and return `None`.

`world/tilemap.py`:
- Add `self.lore_spawns: list = []` to `__init__`.
- `'L'` → append `(x + TILE_SIZE//2, y)` to `lore_spawns`.
- Place `'L'` tiles: 2 in LEVEL_2, 2 in LEVEL_4, 1 in LEVEL_5, 2 in LEVEL_9.

`scenes/gameplay.py`:
- Define module-level `_LORE_TEXT: list[tuple[str, str]]` pairing lore IDs with text strings (one entry per `'L'` tile across all levels, indexed positionally). Example entries:
  - `("lore_foundry_plaque", "'YIELD PER SOUL: 0.04 KW-hr. DAILY EXTRACTION QUOTA: 400 SOULS. — FORGEMASTER DIRECTORATE'")`
  - `("lore_marked_inscription", "'The second Rite requires a willing vessel. Kael volunteered before we could ask.'")`
  - `("lore_warden_sigil", "'THRESHOLD GUARDIAN — UNIT 01. COMMAND: HOLD. OVERRIDE: NONE.'")`
  - `("lore_architects_note", "'If the fanatics reach the vault, kill the lattice. Better silence than their Rite. — The Architect'")`
  - `("lore_miners_diary", "'Day 47. The ink spreads up my left arm now. Foreman says I'm lucky. Lucky.'")`
  - `("lore_convergence_wall", "'THEY MEET HERE. THEY ALWAYS MEET HERE. DO NOT STAY.'")`
  - `("lore_final_door", "'The Founder passed through this door 200 years ago. No one followed. Something came out.'")`
- In `on_enter()`: spawn `LoreItem(x, y, lore_id, text)` for each entry in `tilemap.lore_spawns`; skip if `lore_id` already in `save_data["lore_found"]` (item stays collected across sessions).
- In `update()`: on pickup, store returned `text` in `self._lore_text`, set `self._lore_timer = LORE_DISPLAY_FRAMES`.
- In `draw()`: if `_lore_timer > 0`, draw a centered semi-transparent text box with `self._lore_text` (georgia 22, faded parchment color); alpha fades over last 60 frames; decrement `_lore_timer`.

**Acceptance criteria — done when:**
- Lore items appear as glowing parchment-colored squares at `'L'` positions.
- Collecting one shows its text for 5 seconds then fades.
- `save_data["lore_found"]` grows on each unique collect and persists.
- Items already collected do not respawn after save/load.
- `python main.py` launches without ImportError.

## HK Feel Improvements — Phase 3 (reviewed 2026-04-25)

_Evaluated by hk-agent 2026-04-25; see `REVIEW_HK.md` for full analysis._

| Improvement | Status | Effort | Files |
|---|---|---|---|
| Raise `NPC_INTERACT_DIST` 60 → 80 px; add vertical proximity gate | ⏳ P3-0b | Trivial | `settings.py`, `scenes/gameplay.py` |
| Background lerp speed `0.07` → `0.18` in ending scenes (beat-synchronous color) | ⏳ P3-0b | Trivial | `scenes/marked_ending.py`, `scenes/fleshforged_ending.py` |
| Extract faction tint constants (`FACTION_TINT_BLEND=0.65`, `FLESHFORGED_TINT_COLOR=(200,110,50)`, `MARKED_TINT_COLOR=(100,60,160)`); remove magic numbers from `enemy.py` | ⏳ P3-0b | Minor | `settings.py`, `entities/enemy.py` |
| Lore item display: add player-dismiss flag; raise floor to `LORE_DISPLAY_FRAMES=480` (8 s) if timer kept | ⏳ Phase 4 | Moderate | `settings.py`, `scenes/gameplay.py` |
| Ending scenes: merge consecutive same-register Narrator beats (8 → 6 beats each) for tighter closing weight | ⏳ Phase 4 | Design | `scenes/marked_ending.py`, `scenes/fleshforged_ending.py` |
| Mid-game cutscene: remove forced level-3 exit trigger; move lore to optional NPC in level 4 (HK agency principle) | ⏳ Phase 4 | Design | `scenes/gameplay.py`, `world/tilemap.py` |

**Items marked P3-0b** should be folded into the P3-0b bug-fix sprint (constants and tint extraction are low-risk alongside the bug fixes).

---

## Phase 4 — Polish

_Phase 4 begins 2026-04-27. Pre-phase review by review-agent and hk-agent is recommended before build-agent starts P4-1._

**Priority order for build-agent** (tackle in this order):

1. ~~**P4-0b (pre-phase review)**~~ ✅ **DONE (2026-04-29)** — both passes complete (review-agent BUG-032–043; hk-agent Phase 4 feel analysis in `REVIEW_HK.md`).
2. ~~**P4-0c (critical bug-fix sprint)**~~ ✅ **DONE (2026-04-29)** — BUG-032 through BUG-041 all verified fixed in code.
3. ~~**P4-1 (particle system)**~~ ✅ **DONE (2026-04-29)** — `systems/particles.py` updated; all emit sites wired; NPC hint alpha-fade (HK-P4-D) and particle constant alignment (HK-P4-A) folded in.
4. ~~**P4-2 (death screen polish)**~~ ✅ **DONE (2026-04-29)** — faction text + colors, death particles, hitstop snap, player-skip shortcut (HK-P4-B folded in).
5. **P4-3 (sound system)** — `systems/audio.py`; blocked on audio asset availability.
6. **P4-4 (settings screen)** — implement the "Settings (soon)" stub as a real scene.
7. **P4-5 (main menu polish)** — parallax, animated logo, Credits option.
8. **P4-6 (sprite replacement)** — blocked on art assets; largest scope.
9. **P4-7 (tile sprites)** — blocked on art assets; pairs with P4-6.

---

### Task P4-0b: Pre-Phase Review ✅ DONE (2026-04-29) — both passes complete

_Review-agent found BUG-032 through BUG-043 (see Known Bugs). Six are 🔴 critical and must be fixed before P4-1 content work._

**Critical bugs (block P4-1):** BUG-032, BUG-033, BUG-034, BUG-035, BUG-036, BUG-037
**Minor bugs (can fold into P4-1 commit):** BUG-038, BUG-039, BUG-040, BUG-041
**Pre-identified P4 hooks (no fix needed yet):** BUG-042, BUG-043

---

### Task P4-0c: Critical Bug-Fix Sprint (Phase 4 pre-start) ✅ DONE (2026-04-29)

_All fixes confirmed present in code (prior pass). Verified with `python main.py` — no ImportError._

**Files to touch:**
- `scenes/gameplay.py` (BUG-032, BUG-035, BUG-036, BUG-037)
- `systems/collectible.py` (BUG-033)
- `systems/checkpoint.py` (BUG-034)

**Fixes required:**

- 🔴 **BUG-032** `gameplay.py` `_apply_upgrade_to_player`: Change `if dmg_count > UPGRADE_DMG_MAX_STACKS` to `if dmg_count >= UPGRADE_DMG_MAX_STACKS` so the 3rd stack is the cap, not the 4th.

- 🔴 **BUG-033** `collectible.py` `LoreItem.collect()`: The already-collected branch (`lore_id in lore_found`) should not silently destroy the item — the `on_enter` pre-spawn filter should prevent this from ever being reached. Add `assert lore_id not in game.save_data.get("lore_found", []), "LoreItem spawned despite already being collected"` to the top of `collect()` in debug builds, or at minimum add a comment. No behavior change; just guard the invariant.

- 🔴 **BUG-034** `checkpoint.py` line 55: Change `game.save_data["faction"] = game.player_faction` to `if game.player_faction is not None: game.save_data["faction"] = game.player_faction`.

- 🔴 **BUG-035** `gameplay.py` Warden boss intro banner: The banner index loop should be bounded by the length of `_WARDEN_INTRO_LINES` (6), not `Boss._intro_lines` (3). Fix the banner index guard to `if self._boss_dialogue._index < len(_WARDEN_INTRO_LINES)`.

- 🔴 **BUG-036** `gameplay.py` Architect defeat dialogue: At the moment `_architect_victory_done` transitions to the defeat-dialogue state, set `self.player._iframes = 9999` (or a sufficiently long iframe count) to make the player invincible through the entire cutscene. Clear it when the cutscene ends and `change_scene` fires.

- 🔴 **BUG-037** `gameplay.py` level transition check: Gate `_check_level_transition()` inside `update()` with `if not getattr(self, '_architect_victory_done', False)` to prevent the right-edge trigger from firing during the Architect defeat sequence.

**Also fold in (minor, low-risk):**

- ⚠️ **BUG-038** `architect.py`: Move phase-color computation into `_update_ai()` and store as `self._phase_color`; use it in both `draw()` and any future particle emits.
- ⚠️ **BUG-039** `minimap.py`: Add `+ TILE_SIZE * 2` to enemy dot Y offset in `draw_overlay`.
- ⚠️ **BUG-040** `npc.py`: Add Y-axis camera cull check alongside existing X check.
- ⚠️ **BUG-041** `gameplay.py` lore overlay: Remove `set_alpha(200)` from the text surface; keep it only on the background panel.

**Acceptance criteria — done when:**
- `UPGRADE_DMG_MAX_STACKS` cap is exactly 3 (not 4).
- Checkpoint activation never writes `None` as faction in save data.
- Warden intro banner remains visible for all 6 dialogue lines.
- Player is invincible during Architect defeat cutscene; cannot die to minions.
- Right-edge transition cannot fire during Architect defeat sequence.
- `python main.py` launches without ImportError.

---

### Task P4-1: Particle System

**Files to touch:**
- `systems/particles.py` (create)
- `scenes/gameplay.py` (emit particles at key events)
- `settings.py` (particle constants)

**What to build:**

`settings.py`:
```python
PARTICLE_GRAVITY      = 0.3    # px/frame² downward pull on particles
PARTICLE_FRICTION     = 0.88   # per-frame vx damping
HIT_PARTICLE_COUNT    = 6      # sparks per hit
HIT_PARTICLE_SPEED    = 4.0    # initial speed
HIT_PARTICLE_LIFE     = 18     # frames
DEATH_PARTICLE_COUNT  = 14     # burst on enemy death
DEATH_PARTICLE_LIFE   = 30
SOUL_SURGE_PARTICLE_COUNT = 10
SOUL_SURGE_PARTICLE_COLOR = (140, 80, 220)
OVERDRIVE_PARTICLE_COUNT  = 8
OVERDRIVE_PARTICLE_COLOR  = (220, 120, 20)
CHECKPOINT_PARTICLE_COUNT = 12
CHECKPOINT_PARTICLE_COLOR = (200, 180, 80)
LANDING_PARTICLE_COUNT    = 4
LANDING_PARTICLE_COLOR    = (120, 100, 70)
```

`systems/particles.py`: `Particle` and `ParticleSystem` classes.
- `Particle(x, y, vx, vy, color, life)`: rect (3×3), updates vx/vy with gravity/friction, alive when `life > 0`.
- `ParticleSystem`: maintains a list of `Particle`. Methods:
  - `emit(x, y, count, speed, color, life, spread=360)` — spawn particles in random directions within `spread` degrees.
  - `update()` — tick all particles, prune dead ones.
  - `draw(surface, camera)` — draw each particle rect with alpha proportional to remaining life.

`scenes/gameplay.py` emit sites:
- Player hit → `self._particles.emit(player center, HIT_PARTICLE_COUNT, ..., color=RED)`
- Enemy hit → emit at hit point (from AttackHitbox or on `take_damage`) using `HIT_PARTICLE_COUNT` sparks.
- Enemy death → `DEATH_PARTICLE_COUNT` burst, color = enemy base color.
- Soul Surge activation → `SOUL_SURGE_PARTICLE_COUNT` outward burst.
- Overdrive activation → `OVERDRIVE_PARTICLE_COUNT` heat shimmer upward.
- Checkpoint activation → `CHECKPOINT_PARTICLE_COUNT` golden embers upward.
- Player landing (on_ground transition False→True) → `LANDING_PARTICLE_COUNT` dust sideways.

**Acceptance criteria — done when:**
- Hitting an enemy emits 6 spark particles that arc outward and fade.
- Enemy death emits a 14-particle burst.
- Soul Surge and Overdrive emit faction-colored particles on activation.
- Checkpoint activation emits golden embers.
- Landing from a jump emits 4 dust particles.
- `python main.py` launches without ImportError.

---

### Task P4-2: Death Screen Polish

**Files to touch:**
- `scenes/gameplay.py` (replace death text with faction-specific variant)
- `settings.py` (add death text constants)

**What to build:**

`settings.py`:
```python
DEATH_TEXT_MARKED      = "The ink fades..."
DEATH_TEXT_FLESHFORGED = "The forge goes cold..."
DEATH_TEXT_NEUTRAL     = "You perished."
```

`scenes/gameplay.py`:
- In `_draw_death_screen()`, replace the hardcoded `"you perished"` string with:
  ```python
  faction = getattr(self.game, 'player_faction', None)
  if faction == FACTION_MARKED:
      msg = DEATH_TEXT_MARKED
  elif faction == FACTION_FLESHFORGED:
      msg = DEATH_TEXT_FLESHFORGED
  else:
      msg = DEATH_TEXT_NEUTRAL
  ```
- Emit 6 `DEATH_PARTICLE_COUNT // 2` particles from the player's last position when the death screen first shows (use a `_death_particles_emitted` flag).

**Acceptance criteria — done when:**
- Marked player death shows "The ink fades..." in purple-toned text.
- Fleshforged death shows "The forge goes cold..." in orange-toned text.
- 6 particles emit from the player position on death screen entry.
- `python main.py` launches without ImportError.

---

### Task P4-3: Sound System

**Files to touch:**
- `systems/audio.py` (create)
- `scenes/gameplay.py` (wire play calls at key events)
- `settings.py` (add audio constants)

_Blocked on audio asset files. Build-agent should create the `audio.py` wrapper and all call sites, leaving asset paths as `None`-safe stubs that no-op when the file is missing. Assets will be dropped into `assets/sounds/` and `assets/music/` when available._

**What to build:**

`settings.py`:
```python
AUDIO_MUSIC_VOLUME = 0.5
AUDIO_SFX_VOLUME   = 0.7
SOUND_ATTACK       = "assets/sounds/attack.wav"
SOUND_HIT          = "assets/sounds/hit.wav"
SOUND_JUMP         = "assets/sounds/jump.wav"
SOUND_DEATH        = "assets/sounds/death.wav"
SOUND_CHECKPOINT   = "assets/sounds/checkpoint.wav"
SOUND_ABILITY      = "assets/sounds/ability.wav"
SOUND_BOSS_PHASE   = "assets/sounds/boss_phase.wav"
MUSIC_LEVEL_1      = "assets/music/outer_district.ogg"
MUSIC_LEVEL_5      = "assets/music/sanctum.ogg"
MUSIC_BOSS         = "assets/music/boss.ogg"
```

`systems/audio.py`: `AudioManager` singleton.
- `__init__()`: attempt `pygame.mixer.pre_init(44100, -16, 2, 512)` and `pygame.mixer.init()`. Load each sound file with `pygame.mixer.Sound(path)` if the file exists; else store `None`.
- `play_sfx(key)`: call `.play()` if sound is not None.
- `play_music(path, loops=-1)`: call `pygame.mixer.music.load(path)` and `.play(loops)` if file exists; no-op otherwise.
- `set_sfx_volume(v)` / `set_music_volume(v)`: update all loaded sounds and music.

`scenes/gameplay.py` call sites: play SFX at attack swing, hit land, jump, death, checkpoint activate, ability use, boss phase transition. Play `MUSIC_LEVEL_5` on entering level 5; `MUSIC_BOSS` when boss spawns.

**Acceptance criteria — done when:**
- `python main.py` launches without error whether or not asset files exist.
- All call sites are wired (SFX plays when assets are present; no crash when absent).
- `AudioManager` is instantiated once and accessible as `game.audio`.

---

### Task P4-4: Settings Screen

**Files to touch:**
- `scenes/settings.py` (create)
- `core/game.py` (register scene)
- `scenes/gameplay.py` (wire "Settings (soon)" option to new scene)
- `settings.py` (add scene name constant)

**What to build:**

`settings.py`: Add `SCENE_SETTINGS = "settings"`.

`scenes/settings.py`: `SettingsScene(BaseScene)`.
- Three rows: Music Volume, SFX Volume, Fullscreen.
- UP/DOWN to select row; LEFT/RIGHT to adjust value (volume ±0.1, fullscreen toggle).
- ESC returns to the previous scene (store `_return_scene` from `kwargs.get("return_scene", SCENE_MAIN_MENU)`).
- Volume changes call `game.audio.set_music_volume()` / `set_sfx_volume()` immediately.
- Fullscreen toggle calls `pygame.display.toggle_fullscreen()`.
- Draw: centered panel, three rows with sliders (10-pip bar) and value labels.

`scenes/gameplay.py`: In pause menu, "Settings (soon)" → `game.change_scene(SCENE_SETTINGS, return_scene=SCENE_GAMEPLAY)`.

**Acceptance criteria — done when:**
- Pressing ENTER on "Settings (soon)" in the pause menu opens the settings screen.
- Volume changes take effect immediately and persist in `game.save_data`.
- ESC from settings returns to the pause menu.
- `python main.py` launches without ImportError.

---

### Task P4-5: Main Menu Polish

**Files to touch:**
- `scenes/main_menu.py` (add parallax, animated logo, Credits option)
- `settings.py` (add credits constants)

**What to build:**

`settings.py`:
```python
CREDITS_TEXT = [
    "Steamfall",
    "",
    "Design & Code  —  build-agent",
    "Story         —  hk-agent",
    "Review        —  review-agent",
    "Direction     —  orchestrator",
]
```

`scenes/main_menu.py`:
- Background: draw 2–3 layers of slowly scrolling rectangles (parallax clouds/platforms) at different speeds (1, 2, 3 px/frame right-to-left; wrap at screen edge).
- Logo: pulse the title glow at a slightly faster rate (period 90 frames instead of 120).
- Add "Credits" as the last menu option (before Quit).
- Selecting "Credits" shows a centered scrolling credits list over a dark overlay; any key dismisses it.

**Acceptance criteria — done when:**
- Main menu background shows 2+ parallax scroll layers.
- "Credits" option appears in the menu and shows the credits text.
- Existing "Continue" / "New Game" / "Quit" flow is unbroken.
- `python main.py` launches without ImportError.

---

### Task P4-6: Sprite Replacement

_Blocked on art assets. Build-agent should update `AnimationController._make_frames()` to load from `assets/sprites/<entity>/` directories when the directory exists, falling back to placeholder colored rects when not. This future-proofs all entity draws without requiring assets today._

**Files to touch:**
- `systems/animation.py` (extend `_make_frames` to load PNGs when available)
- `entities/player.py` (pass sprite dir path to AnimationController)
- `entities/enemy.py` and subclasses (same)
- `settings.py` (add sprite path constants)

**Acceptance criteria — done when:**
- When `assets/sprites/player/idle/` contains PNG files, they are loaded and used instead of colored rects.
- When the directory is absent, colored rects render as before (no crash).
- `python main.py` launches without ImportError.

---

### Task P4-7: Tile Sprites

_Blocked on art assets. Same pattern as P4-6._

**Files to touch:**
- `world/tilemap.py` (load tile sprite sheet when `assets/tiles/<biome>.png` exists)
- `settings.py` (add tile sprite path constants)

**Acceptance criteria — done when:**
- When `assets/tiles/outer_district.png` exists, it is used for level 1–2 tile rendering.
- Fallback to colored rects when assets are absent.
- `python main.py` launches without ImportError.

---

## Known Bugs / Tech Debt

_Legend: ✅ Fixed | ⚠️ Flagged / deferred | 🔴 Open_

1. ✅ **CRITICAL — Missing files cause immediate ImportError on startup** — Fixed by Task P1-1. All files created; `CHECKPOINT_GLOW_COLOR` added to `settings.py`.

2. ✅ **`HitStop` classmethod+property bug** — Fixed (REVIEW_BUGS BUG-004). Removed the `_inst` class variable and `instance` classmethod from `core/hitstop.py`.

3. ✅ **`TileMap` missing attributes** — Fixed by Task P1-1. `crawler_spawns`, `checkpoints`, `boss_spawn`, `ability_orb_spawns` all initialised in `TileMap.__init__`.

4. ✅ **`Enemy.get_drop_fragments()` missing** — Fixed by P2-0 (2026-04-17). Method added to `entities/enemy.py`; returns a `SoulFragment` at enemy center.

5. ✅ **Entity iframes applied to enemies** — Fixed by P2-0 (2026-04-17). `ENEMY_IFRAMES = 6` added to `settings.py`; `Entity._iframes_on_hit` is now overridable; `Enemy.__init__` sets it to `ENEMY_IFRAMES`.

6. ✅ **Pause menu is not a real menu** — Fixed by Task P1-5. Full navigable pause overlay with Resume / Return to Main Menu / Settings (soon).

7. ⚠️ **`player.py` animation draw duplication** — Deferred. Eye and attack-arc draw code is overlaid on top of the animation blit; works correctly but structure is messy. Consolidate in Phase 4 (sprite pass).

8. ✅ **`dialogue.py` hint text hardcoded** — Fixed (REVIEW_BUGS BUG-003). `else` branch now reads `"SPACE — dismiss"`.

9. ⚠️ **Level transition uses raw pixel boundary** — Deferred. Works reliably for current level widths. If level geometry changes add a `'>'` exit tile in the parser. Assign to build-agent if levels are resized.

10. ⚠️ **Wildcard imports in scene files** — Flagged (REVIEW_BUGS FLAG-001). Architectural style; not blocking; defer to Phase 4 cleanup.

11. 🔴 **Audio subsystem incomplete** — `systems/voice_player.py` added (voice lines); `systems/audio.py` for music/SFX still absent. `pygame.mixer` is initialised by `pygame.init()` but no sounds play. Assign to build-agent in Phase 4.

12. ⚠️ **World bounds not enforced for enemies** — Flagged. Low-priority edge case; assign to build-agent if enemies escape the visible world during playtesting.

13. ✅ **BUG-016: ShieldGuard patrol facing inconsistency** — Fixed (P2-3 commit). Added `self.facing = self._patrol_dir` in `ShieldGuard._do_patrol()`.

14. ⚠️ **BUG-017: Boss intro first line shows for 119 frames instead of 120** — Off-by-one in `_tick_boss_intro()` (timer increments before the ≥120 check). Cosmetic only (~16 ms at 60 fps). Fix: change `if self._boss._intro_line_timer >= 120` to `>= 121`, or increment timer after the check. Assign to build-agent as low-priority hotfix.

15. ✅ **BUG-018: Upgrade screen activates while player is dead** — Fixed by P2-0c (2026-04-23). `if not self.player.alive: return` guard added to `_setup_upgrade_choices()`.

16. ✅ **BUG-019: P1-8 ability-slots feature entirely absent from live code** — Fixed by P2-0c (2026-04-23). `ability_slots` guard in `Player._handle_ability()`; slot restore in `gameplay.py:on_enter()`; `'A'` tile handler and `ability_orb_spawns` in `tilemap.py`.

17. ✅ **BUG-020: Architect teleport uses `SCREEN_WIDTH` as arena bound instead of level width** — Fixed by P2-0c (2026-04-23). `level_width` constructor parameter added to `Architect`; `arena_max = self._level_width - TILE_SIZE*4`; `level_width=self.tilemap.width` passed from `gameplay.py`.

18. ✅ **BUG-021: Architect phase transitions never trigger phase-announce banner or arena-shrink** — Fixed by P2-0c (2026-04-23). Parallel announce-and-shrink block added for `self._architect` in `gameplay.py`; `announce_phase = 4` signal wired.

19. ✅ **BUG-022: Boss intro banner timer desynchronised from DialogueBox** — Fixed by P2-0c (2026-04-23). Banner index now driven from `self._boss_dialogue._index`.

20. ✅ **BUG-023: `"res"` upgrade silently refills resource bar on every level load** — Fixed by P2-0c (2026-04-23). `_regen_resource` call removed from `_apply_upgrade_to_player` for `"res"` case.

21. ✅ **BUG-024: `AbilityOrb.collect()` lacks double-collect guard** — Fixed by P2-0c (2026-04-23). `if not self.alive: return` guard added at top of `collect()`.

22. ✅ **BUG-025: Arena-shrink left/right wall injection coupled via single condition** — Fixed by P2-0c (2026-04-23). Left wall injected only when `_shrink_left_x > 0`; right wall injected independently when `_shrink_right_x < self.tilemap.width`.

23. ✅ **BUG-026: Ending scenes skip two beats on rapid double-press** — Fixed in P3-0b (2026-04-27). `if self._dialogue.is_done(): return` guard added to `_advance()` in both ending scenes.

24. ✅ **BUG-027: Architect phase banners always render amber — `"UNLEASHED"` color check never matches** — Fixed in P3-0b (2026-04-27). Condition extended to `("UNLEASHED" in ... or "ABSOLUTE" in ...)`.

25. ✅ **BUG-028: Faction tint applied to Boss / Architect in levels 6–8** — Fixed in P3-0b (2026-04-27). `isinstance(e, (Boss, Architect))` guard added to the tint loop.

26. ✅ **BUG-029: Architect defeat dialogue has no SPACE shortcut — player silently locked out up to 8 s** — Fixed in P3-0b (2026-04-27). SPACE/RETURN advance `_defeat_line_idx`; hint rendered.

27. ✅ **BUG-030: Unreachable checkpoint in LEVEL_2 sub-floor** — Fixed in P3-0b (2026-04-27). Checkpoint relocated to row 8 (reachable platform).

28. ✅ **BUG-031: NPC "E" hint badge persists while dialogue box is open** — Fixed in P3-0b (2026-04-27). `npc._show_hint = False` set inside the `_npc_dialogue` early-return block.

29. ⚠️ **FLAG-010: `game/story.py` `StoryState` class is dead code** — defined but never imported or used. Either wire into `core/game.py` or remove. Low-priority; defer to Phase 4 cleanup.

_Review-agent 2026-04-27 pass (P4-0b pre-phase):_

30. 🔴 **BUG-032** `gameplay.py` `_apply_upgrade_to_player`: DMG stack cap uses `>` instead of `>=`, allowing one extra stack beyond `UPGRADE_DMG_MAX_STACKS` on level reload. Fix: change to `>= UPGRADE_DMG_MAX_STACKS`. Assign to build-agent in P4-0b.

31. 🔴 **BUG-033** `collectible.py` `LoreItem.collect()`: already-collected branch sets `self.alive = False` and returns `None` silently — if the pre-spawn filter in `on_enter` is bypassed the item vanishes with no feedback. Fix: guard is acceptable if filter is always in place; annotate with a comment confirming the invariant, or add an `assert lore_id not in save_data["lore_found"]` to catch regressions. Assign to build-agent in P4-0b.

32. 🔴 **BUG-034** `checkpoint.py` line 55: Activation overwrites `save_data["faction"]` with `game.player_faction` which can be `None` on a "Continue" load without a faction in save data, corrupting the faction key. Fix: only write if `game.player_faction is not None`. Assign to build-agent in P4-0b.

33. 🔴 **BUG-035** `gameplay.py` lines 1299–1321: Warden boss intro banner indexes `Boss._intro_lines` (3 entries) via `DialogueBox._index`, but the DialogueBox was loaded with `_WARDEN_INTRO_LINES` (6 entries) — banner disappears silently for dialogue lines 3–5. Fix: use `_WARDEN_INTRO_LINES` length as the index bound, or separate the banner list from the dialogue list. Assign to build-agent in P4-0b.

34. 🔴 **BUG-036** `gameplay.py` lines 779–861: Player can be killed by surviving Crawler minions during Architect defeat dialogue, firing `change_scene` before `victory = True` is saved (game ends as death, not victory). Fix: set `player.invincible = True` (or apply a long iframe) when the defeat dialogue begins. Assign to build-agent in P4-0b.

35. 🔴 **BUG-037** `gameplay.py` lines 825–848: Level right-edge transition check is not suppressed during Architect defeat dialogue — player can walk to the right edge and trigger `SCENE_MAIN_MENU` before victory is saved. Fix: gate `_check_level_transition()` with `if not self._architect_victory_done`. Assign to build-agent in P4-0b.

36. ⚠️ **BUG-038** `architect.py` lines 221–229: `self.color` is set inside `draw()`, not `update()`, so the death particle burst on a phase-transition death frame uses last frame's color. Fix: compute phase color in `update()` or `_update_ai()` and store it before `die()` is called. Assign to build-agent in P4-0b.

37. ⚠️ **BUG-039** `minimap.py` lines 215–220: Enemy spawn dots are rendered 2 tile-rows above their actual tile position because the -64 px Y-spawn offset applied at spawn time is not compensated on the minimap row calculation. Fix: add `+ TILE_SIZE * 2` (or `+ 64`) to the enemy dot's Y offset in `draw_overlay`. Assign to build-agent in P4-0b.

38. ⚠️ **BUG-040** `npc.py` lines 35–36: NPC off-screen culling checks only X axis; NPCs far above/below the viewport blit every frame. Fix: also check `camera.apply(npc.rect).bottom > 0 and camera.apply(npc.rect).top < SCREEN_HEIGHT`. Low priority; assign to build-agent in P4-0b.

39. ⚠️ **BUG-041** `gameplay.py` lines 1372–1381: Lore overlay text uses `set_alpha(200)` during the steady-state window (80% opaque), while the background also uses alpha 200 — stacked alpha makes text appear dimmer than intended. Fix: render text surface without `set_alpha`; apply alpha only to the background panel. Cosmetic; assign to build-agent in P4-0b.

40. ⚠️ **BUG-042** `gameplay.py` lines 1174–1186: No hook point yet for P4-2 faction-specific death text and death-particle emit. Hook should be: `if self._death_timer == 1:` (first frame of death screen). Pre-identified for build-agent when implementing P4-2.

41. ⚠️ **BUG-043** `gameplay.py` lines 450–457 / `settings.py` / `core/game.py`: P4-4 settings screen transition is a no-op stub. Requires: `SCENE_SETTINGS` constant in `settings.py`, scene registration in `game._build_scenes`, and new `scenes/settings.py`. All three touch points noted; unblocked by P4-4 spec in ROADMAP.

_hk-agent 2026-04-29 Phase 4 feel pass (see `REVIEW_HK.md` for full analysis):_

42. ✅ **HK-P4-A** `systems/particles.py` (to be created in P4-1): `PARTICLE_GRAVITY` spec value is 0.3 but current `settings.py` has 0.25; `PARTICLE_DRAG` (friction) spec is 0.88 but `settings.py` has 0.92 — will produce overly floaty arcs. Also `PARTICLE_HIT_COUNT = 5` and `PARTICLE_DEATH_COUNT = 12` are below spec density. Recommend aligning to spec before P4-1 ships. Also: P4-1 spec is missing a hit-spark emit site for nail-connects-living-enemy (only enemy-death burst is listed for enemies). Assign to build-agent in P4-1.

43. ✅ **HK-P4-B** `scenes/gameplay.py` (death screen, `_draw_death`): No freeze-frame on death onset. Recommend `hitstop.trigger(6)` at `_death_timer == 1` (line ~879) for a punchy death snap. Also: no player-skip mechanism in the 150-frame window — recommend `KEYDOWN` early-exit when `_death_timer > 60` to avoid lockout feel. Assign to build-agent in P4-2.

44. ⚠️ **HK-P4-C** `scenes/main_menu.py` (parallax layers): Layer fill colors `(20,15,35)` / `(28,17,48)` / `(36,20,60)` have a luminance delta of only ~14–17 against the `(8,4,18)` background — effectively invisible. Recommend raising each layer by +15 luminance and the slowest scroll from 1 to 1.5 px/frame. Title pulse hue is brightness-only; recommend shifting the min-state toward amber for visible character. Assign to build-agent in P4-5.

45. ✅ **HK-P4-D** `entities/npc.py` lines 40–45 / `scenes/gameplay.py` lines 825–828: NPC `"E"` hint still snaps on/off instantly (Phase 3 deferral never implemented). Add `_hint_alpha` field to `NPC.__init__`, alpha-ramp logic in `npc.draw()` (delta 25/frame → 10-frame fade), and Y-axis proximity gate in `gameplay.py`. Assign to build-agent in P4-1 (fold into same commit as particle system since both touch gameplay.py).

46. ⚠️ **HK-P4-E** `scenes/gameplay.py` / `settings.py`: Faction branch levels 6–8 fall back to `outer_district.ogg` — no faction audio identity. Recommend adding `MUSIC_MARKED_BRANCH` / `MUSIC_FLESHFORGED_BRANCH` constants to `settings.py` and wiring them in the level-load music logic. Assign to build-agent in P4-3.

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
| `scenes/gameplay.py` | build-agent | P3 + P3-0b complete; P4-1/P4-2/P4-4 will touch this |
| `entities/entity.py` | build-agent | Stable (iframe fix done in P2-0) |
| `entities/player.py` | build-agent | Animation draw consolidation deferred to P4-6 (sprite pass) |
| `entities/enemy.py` | build-agent | Stable; faction tint constants extracted (P3-0b) |
| `entities/crawler.py` | build-agent | Created (P1-1); stable |
| `entities/boss.py` | build-agent | Warden scripting complete (P2-3); stable |
| `entities/architect.py` | build-agent | Stable (P2-0c + P2-8 complete) |
| `entities/shield_guard.py` | build-agent | Created (P2-1); stable |
| `entities/ranged.py` | build-agent | Created (P2-1); stable |
| `entities/jumper.py` | build-agent | Created (P2-1); stable |
| `systems/physics.py` | build-agent | Stable; do not change call signatures |
| `systems/combat.py` | build-agent | Stable; hitbox logic complete |
| `systems/dialogue.py` | build-agent | Hint text fix done (Tech Debt #8); stable |
| `systems/animation.py` | build-agent | Stable; P4-6 extends `_make_frames` for PNG loading |
| `systems/checkpoint.py` | build-agent | Created (P1-1); stable |
| `systems/collectible.py` | build-agent | Stable (P3-5 `LoreItem` complete) |
| `systems/minimap.py` | build-agent | 13-level room-chain complete (P2-8); stable |
| `systems/particles.py` | build-agent | To be created in P4-1 |
| `systems/audio.py` | build-agent | To be created in P4-3 |
| `scenes/marked_ending.py` | build-agent | P3-3 + P3-0b complete; stable |
| `scenes/fleshforged_ending.py` | build-agent | P3-3 + P3-0b complete; stable |
| `scenes/settings.py` | build-agent | To be created in P4-4 |
| `entities/npc.py` | build-agent | Created (P3-4); P3-0b complete; stable |
| `systems/tutorial_minigame.py` | build-agent (created outside roadmap) | Inline control tutorial for prologues; stable |
| `systems/voice_player.py` | build-agent (created outside roadmap) | Voice-line playback; integrate with P4-3 audio pass |
| `world/tilemap.py` | build-agent | All levels complete; P3-0b BUG-030 fixed; stable |
| `REVIEW_BUGS.md` | review-agent (own) | Never modifies .py files |
| `REVIEW_HK.md` | hk-agent (own) | Never modifies .py files |
