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

## Phase 2 — Content Expansion

**Priority order for build-agent** (tackle in this order):

1. ~~**P2-0 (tech debt unblock)**~~ ✅ **DONE (2026-04-17):** `Enemy.get_drop_fragments()` added; enemy iframes fixed via `ENEMY_IFRAMES=6` overriding `PLAYER_IFRAMES=45`.
2. ~~**P2-1 (enemy variety)**~~ ✅ **DONE (2026-04-17):** `ShieldGuard`, `Ranged`, `Jumper` created in `entities/`; wired into `tilemap.py` (`'G'`/`'R'`/`'J'` tile chars) and `gameplay.py`.
3. ~~**P2-2 (levels 6–10)**~~ ✅ **DONE (2026-04-18):** `LEVEL_6_MARKED/FLESHFORGED` through `LEVEL_10` in `tilemap.py`; `_faction_next_level()` routing in `gameplay.py`; victory flag on level 10 completion.
4. ~~**P2-2b (HK feel sprint)**~~ ✅ **DONE (2026-04-18):** All 13 constants in place; ShieldGuard full block + patrol-facing fix; Ranged arc projectile; Jumper burst pattern + aerial knockback.
5. ~~**P2-3 (Warden scripting)**~~ ✅ **DONE (2026-04-18):** 3-beat Warden intro dialogue; phase-differentiated rage flash (orange/red); BOSS_PROJ_SPREAD_VY; BUG-016 fixed. Prior commits had already implemented dash, arena shrink, and projectile spread.
6. ~~**P2-4 (Architect boss)**~~ ✅ **DONE (2026-04-18):** `entities/architect.py` created; 4-phase AI (teleport/fan/minions); faction-specific intro + defeat dialogue; 'X' tile in LEVEL_10; victory write to save_data.
7. ~~**P2-5 (upgrade system)**~~ ✅ **DONE (2026-04-21):** Upgrade screen on Warden kill; three choices (HP/DMG/RES); stored in `save_data["upgrades"]`; reapplied on level load.
8. ~~**P2-0c (critical bug-fix sprint)**~~ ✅ **DONE (2026-04-23):** BUG-018 through BUG-025 all fixed — ability-slots gate added (BUG-019), Architect level_width param (BUG-020), Architect phase-announce wired (BUG-021), upgrade-while-dead guard (BUG-018), announce_phase=4 signal (BUG-021 addendum), BUG-022/023/024/025 resolved.
9. **P2-6 (enemy drops):** `HeatCore` and `SoulShard` collectibles (extend `systems/collectible.py`) dropped based on enemy faction; faction-matched healing. **← NEXT for build-agent**
10. **P2-7 (environmental hazards):** Spike tiles (`'s'`), crumbling platforms (`'~'` disappears after 30 standing frames); add parsers to `TileMap` and collision handling to `physics.py`/`gameplay.py`.
11. **P2-8 (HK feel sprint — Architect/Upgrades/Minimap):** All outstanding hk-agent 2026-04-21 recommendations — teleport telegraph, minion cap, upgrade DMG/RES, minimap room-chain 6–10.

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

### Task P2-6: Enemy Drops

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

### Task P2-7: Environmental Hazards

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

### Task P2-8: HK Feel Sprint — Architect / Upgrades / Minimap

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

15. 🔴 **BUG-018: Upgrade screen activates while player is dead** — If the player and Warden die on the same frame, `_upgrade_active = True` blocks the death sequence indefinitely via the early-return guard. Fix: add `if not self.player.alive: return` at the top of `_setup_upgrade_choices()`. Assign to build-agent (P2-0c).

16. 🔴 **BUG-019: P1-8 ability-slots feature entirely absent from live code** — `Player._handle_ability()` has no `ability_slots` guard; `gameplay.py:on_enter()` never restores `ability_slots` from save; `TileMap._parse()` has no `'A'` handler and `ability_orb_spawns` is never populated. Ability is always unlocked from the start regardless of save state. Three-file fix required (see P2-0c spec). Assign to build-agent.

17. 🔴 **BUG-020: Architect teleport uses `SCREEN_WIDTH` as arena bound instead of level width** — `arena_max = SCREEN_WIDTH - TILE_SIZE*4` = 1152 px, but LEVEL_10 is 2080 px wide. Right 928 px of the level is never a valid teleport target; Architect can't reach its own spawn area post-phase-2. Fix: add `level_width` constructor parameter to `Architect`; use `self._level_width - TILE_SIZE*4` as `arena_max`. Assign to build-agent (P2-0c).

18. 🔴 **BUG-021: Architect phase transitions never trigger phase-announce banner or arena-shrink** — `gameplay.py` checks only `self._boss.announce_phase`; no parallel check exists for `self._architect`. Architect transitions through 4 phases silently. Fix: add an announce-and-shrink block for `self._architect` after the Warden block. Assign to build-agent (P2-0c).

19. ⚠️ **BUG-022: Boss intro banner timer desynchronised from DialogueBox** — `_tick_boss_intro` advances `_intro_line_idx` on a 120-frame timer independently of the player pressing SPACE in the DialogueBox. Fix: drive banner index from `DialogueBox._index`. Assign to build-agent (P2-0c).

20. ⚠️ **BUG-023: `"res"` upgrade silently refills resource bar on every level load** — `_apply_upgrade_to_player` calls `_regen_resource(UPGRADE_RES_BONUS)` for `"res"` entries on every `on_enter()`, so the player respawns with more resource than saved. Fix: remove the `_regen_resource` call from that path. Assign to build-agent (P2-0c).

21. ⚠️ **BUG-024: `AbilityOrb.collect()` lacks double-collect guard** — No `if not self.alive: return` guard; will matter once BUG-019 is fixed and orbs are spawned. Fix: add guard at top of `collect()`. Assign to build-agent (P2-0c).

22. ⚠️ **BUG-025: Arena-shrink left/right wall injection coupled via single condition** — `if self._shrink_left_x > 0` gates both walls; right wall not solid on phase-3 frame 1. Fix: separate conditions for each wall. Assign to build-agent (P2-0c).

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
| `scenes/gameplay.py` | build-agent | Open: BUG-018, BUG-021, BUG-022, BUG-023, BUG-025 (P2-0c) |
| `entities/entity.py` | build-agent | Stable (iframe fix done in P2-0) |
| `entities/player.py` | build-agent | Open: BUG-019 ability-slots gate (P2-0c); animation draw consolidation deferred to Phase 4 |
| `entities/enemy.py` | build-agent | Stable (get_drop_fragments + ENEMY_IFRAMES done in P2-0) |
| `entities/crawler.py` | build-agent | Created (P1-1); stable |
| `entities/boss.py` | build-agent | Warden scripting complete (P2-3); stable |
| `entities/architect.py` | build-agent | Open: BUG-020 teleport bound, BUG-021 phase-announce (P2-0c) |
| `entities/shield_guard.py` | build-agent | Created (P2-1); stable |
| `entities/ranged.py` | build-agent | Created (P2-1); stable |
| `entities/jumper.py` | build-agent | Created (P2-1); stable |
| `systems/physics.py` | build-agent | Stable; do not change call signatures |
| `systems/combat.py` | build-agent | Stable; hitbox logic complete |
| `systems/dialogue.py` | build-agent | Hint text fix done (Tech Debt #8); stable |
| `systems/animation.py` | build-agent | Stable until sprite replacement (Phase 4) |
| `systems/checkpoint.py` | build-agent | Created (P1-1); stable |
| `systems/collectible.py` | build-agent | Open: BUG-024 double-collect guard (P2-0c); extend with HeatCore/SoulShard (P2-6) |
| `systems/minimap.py` | build-agent | Created (P1-7); extend room-chain to 13 levels in P2-8 |
| `systems/tutorial_minigame.py` | build-agent (created outside roadmap) | Inline control tutorial for prologues; registered here for tracking |
| `systems/voice_player.py` | build-agent (created outside roadmap) | Voice-line playback; no MP3 assets yet; blocked on Phase 4 audio pass |
| `world/tilemap.py` | build-agent | LEVEL_1–5 complete; extend with LEVEL_6–10 in Phase 2 |
| `REVIEW_BUGS.md` | review-agent (own) | Never modifies .py files |
| `REVIEW_HK.md` | hk-agent (own) | Never modifies .py files |
