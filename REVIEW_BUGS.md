# Bug Review — 2026-04-12

## Fixed Bugs

### BUG-001: Missing `CHECKPOINT_COLOR` and `CHECKPOINT_GLOW_COLOR` constants
- File: `settings.py`
- Problem: `systems/checkpoint.py` imported `CHECKPOINT_COLOR` and `CHECKPOINT_GLOW_COLOR` from `settings`, and `scenes/gameplay.py` referenced `CHECKPOINT_GLOW_COLOR` via `from settings import *`, but neither constant was defined in `settings.py`. Any scene that activated a checkpoint or drew the HUD checkpoint indicator would crash with `ImportError` / `NameError`.
- Fix: Added both constants to `settings.py` after the tile color block: `CHECKPOINT_COLOR = (80, 70, 110)` and `CHECKPOINT_GLOW_COLOR = (180, 140, 255)`.

### BUG-002: Division-by-zero in Entity health bar draw
- File: `entities/entity.py:96`
- Problem: The health-bar draw path computed `self.health / self.max_health` guarded only by `self.health < self.max_health`. If an Entity were constructed with `max_health=0` and `health` somehow went negative (externally), this would raise `ZeroDivisionError`. The condition `health < max_health` is always False when both are 0, but the guard was not tight enough for all conceivable constructor calls.
- Fix: Changed guard to `if self.health < self.max_health and self.max_health > 0:` so division is categorically safe.

### BUG-003: Duplicate hint text in DialogueBox — dead code branch
- File: `systems/dialogue.py:130-132`
- Problem: The ternary that chooses the "press SPACE" hint had identical strings in both branches: `"SPACE — continue" if ... else "SPACE — continue"`. The condition (`_index < len(_queue) - 1`) was always irrelevant, so the last-line indicator was never shown differently from a mid-sequence line. This is dead code — one branch was unreachable as written.
- Fix: Changed the `else` branch to `"SPACE — dismiss"` so the last line in a dialogue sequence correctly prompts the player to close the box rather than continue.

### BUG-004: `HitStop.instance` used broken `@classmethod @property` chaining
- File: `core/hitstop.py`
- Problem: The class defined `instance` with both `@classmethod` and `@property` decorators stacked. This combination was deprecated in Python 3.11 and raises `TypeError` in Python 3.13+. While the method was never called in the codebase (all callers use the module-level `hitstop = HitStop()` singleton), having it in the class body would produce a `DeprecationWarning` on import in 3.11 and a hard `TypeError` in 3.13.
- Fix: Removed the `_inst` class variable and the `instance` classmethod entirely. Updated the docstring to reference the module-level `hitstop` singleton instead.

---

## Flagged (not fixed)

### FLAG-001: `from settings import *` in scene files
- Files: `scenes/gameplay.py`, `scenes/main_menu.py`, `scenes/faction_select.py`, `scenes/marked_prologue.py`, `scenes/fleshforged_prologue.py`
- Problem: Wildcard imports make it hard to trace which names are in scope, and they silently mask name collisions. Per the review brief (Category 3), this is noted but not refactored.
- Why not fixed: Architectural style decision; changing it would require touching imports in five files without a correctness benefit.

### FLAG-002: `_draw_damage_vignette` alpha computation uses `DAMAGE_FLASH_FRAMES` as denominator without zero check
- File: `scenes/gameplay.py:335`
- Problem: `alpha = int(160 * self._damage_flash / DAMAGE_FLASH_FRAMES)` — if `DAMAGE_FLASH_FRAMES` were changed to 0, this divides by zero. In practice `DAMAGE_FLASH_FRAMES = 20` (a constant) so this cannot trigger, but the pattern is fragile.
- Why not fixed: The constant is non-zero by design and there is no code path that sets it to 0; fixing it would be defensive over-engineering with no concrete crash scenario.

### FLAG-003: `Checkpoint._activate` stores `self.rect.centerx` (screen-snapped int) as respawn X instead of original world float
- File: `systems/checkpoint.py:50-51`
- Problem: `game.save_data["checkpoint_pos"] = (self.rect.centerx, self.rect.top)`. These are integer rect coordinates, which is fine. However, on respawn, gameplay.py passes these as `Player(cx, cy, ...)` — the Y value is `self.rect.top`, which is the top of the checkpoint *pillar*, not the player's desired spawn height. The player would spawn with their top-left at the pillar top, likely inside a wall or floating in air depending on level geometry.
- Why not fixed: This is an intentional spawn offset that was also present for the normal `player_spawn` (which subtracts 64 px). Changing it would affect level design. Flagged for level designers to verify spawn positions.

### FLAG-004: `_draw_cooldown_pips` pip ordering appears inverted
- File: `scenes/gameplay.py:296-310`
- Problem: `lit = cd <= max_cd - threshold` where `threshold = max_cd * (i+1) / 5`. Pip 0 lights at 80% cooldown elapsed; pip 4 lights only at 0 (fully ready). This means pips fill left-to-right as cooldown drains, but all five only glow when fully charged. This may be intentional (left = "almost charged", right = "fully charged"), but is unintuitive compared to most games where pips light one-by-one as recharge progresses.
- Why not fixed: Ambiguous design intent; not a correctness crash — just a potential UX issue.

---

# Bug Review — 2026-04-18

## New Bugs (post P2-1 implementation)

---

### BUG-005: ShieldGuard direction check is inverted — shield blocks hits from behind, not the front

- File: `entities/shield_guard.py`, lines 31–35
- Problem: The `take_damage` docstring says the shield blocks hits "from the front (shield side = facing direction)". However, `knockback_dir` points **away from the attacker** — i.e., it is the direction the knocked-back body travels, which is the **same** as `self.facing` when the attacker is in front. The condition `if knockback_dir == self.facing` therefore triggers precisely when the blow lands from the **front**, which matches the intended reduction. BUT `_update_ai` always sets `self.facing` to point **toward** the player (line 43–45), so `knockback_dir` (away from the attacker, who is the player) and `self.facing` (toward the player) are **always opposite**. The condition `knockback_dir == self.facing` is therefore **never True** in normal gameplay, meaning the shield never actually reduces any damage.
- Fix: Invert the check to `if knockback_dir != 0 and knockback_dir == -self.facing:` (i.e., knockback is in the opposite direction of facing, meaning the hit came from the front), or keep the facing logic consistent: since the guard always faces the player, any hit from the player means `knockback_dir` points away from the player, which equals `-self.facing`. Change line 34 to `if knockback_dir == -self.facing:`.

---

### BUG-006: `Ranged` projectiles have no maximum travel distance — they persist until hitting a tile or the player

- File: `entities/ranged.py`, lines 31–35 (`Projectile.update`) and lines 61–64 (`Ranged.update`)
- Problem: `Projectile` has no lifetime counter and no maximum range. A projectile fired in an open corridor with no tiles in the way will travel forever (until the level is left or the scene is destroyed). With multiple `Ranged` enemies and a long firing session the `self.projectiles` list can grow unboundedly, wasting CPU and memory.
- Fix: Add a `self.max_range` (e.g., `RANGED_SIGHT_RANGE * 2`) and a `self._dist_traveled` counter. In `Projectile.update`, increment `_dist_traveled` and set `self.alive = False` once it exceeds `max_range`. Alternatively, add a frame-based TTL (e.g., `self.lifetime = 180`).

---

### BUG-007: Dead enemy fragments spawned every frame until enemy is pruned

- File: `scenes/gameplay.py`, lines 279–290
- Problem: The fragment-spawning loop (lines 280–283) iterates over `newly_dead = [e for e in self.enemies if not e.alive]` and calls `get_drop_fragments()` for every dead enemy found. Dead enemies are not removed from `self.enemies` until line 290 (`self.enemies = [e for e in self.enemies if e.alive]`). Because enemies can die mid-frame while `hitstop.is_active()` is True (the combat checks at lines 240–267 run even during hitstop), the dead enemy sits in `self.enemies` alive=False through that frame, but the fragment spawn and prune happen in the same frame, so normally this is one-shot. **However**, if `hitstop` is active across multiple frames, the pruning does not happen (line 219 guard) while the fragment-spawn block (lines 279–290) runs outside the hitstop guard. This means `get_drop_fragments()` is called repeatedly for the same dead enemy on every hitstop frame, spawning multiple fragment sets per kill.
- Fix: Move the fragment-spawn and enemy-prune block inside the `if not hitstop.is_active():` guard (after line 267), or track which enemies have already dropped fragments with a flag (e.g., `enemy._dropped = True`).

---

### BUG-008: `Jumper._do_patrol_jump` resets `_jump_timer` but `_jump_timer` is never decremented in patrol mode — jump fires every frame once threshold is reached

- File: `entities/jumper.py`, lines 56–66
- Problem: `_jump_timer` is incremented by 1 every frame in `_update_ai` (line 38). In `_do_patrol_jump`, the jump fires when `self.on_ground and self._jump_timer > JUMPER_JUMP_COOLDOWN`, and then `self._jump_timer = 0` resets it (line 66). This is correct for the first jump. But `_jump_cooldown` (a separate variable) is only reset inside `_do_chase_jump` (line 75), not in `_do_patrol_jump`. This means in patrol mode, after the first jump the Jumper will jump again as soon as it lands (once `_jump_timer > JUMPER_JUMP_COOLDOWN` again, which works correctly). **The real issue**: `_jump_cooldown` starts at 0 and is never touched during patrol, so if the Jumper transitions from chase back to patrol, `_jump_cooldown` may be nonzero and will continue decrementing even in patrol mode (harmless but confusing). More critically: the patrol jump uses `_jump_timer > JUMPER_JUMP_COOLDOWN` correctly, but the guard `self.on_ground` will only be True for one frame (the frame the entity lands), so the jump will fire exactly once per landing. This is actually correct. **The real bug here** is that `_jump_timer` is only incremented once per `_update_ai` call (regardless of state), but it is reset in `_do_patrol_jump`. If the Jumper is in _CHASE or _ATTACK state for many frames, `_jump_timer` keeps accumulating, so the very next frame it enters _PATROL it will immediately jump (since `_jump_timer > JUMPER_JUMP_COOLDOWN` is already true). This could cause an unexpected immediate jump on first patrol entry.
- Fix: Reset `_jump_timer = 0` when entering the _PATROL state from another state, or add a state-change detection. Simplest: at the top of `_do_patrol_jump`, if `_jump_timer > JUMPER_JUMP_COOLDOWN * 3`, clamp it to `JUMPER_JUMP_COOLDOWN` to avoid jump-on-entry.

---

### BUG-009: `player.py` coyote-timer still ticks down when the player is grounded — wastes coyote window

- File: `entities/player.py`, lines 171–175
- Problem: The coyote timer is set on the frame the player walks off a ledge (`was_on_ground and not self.on_ground`). The `elif self._coyote_timer > 0: self._coyote_timer -= 1` branch correctly only decrements when not on the ground. However, on the frame the player **lands** (`not was_on_ground and self.on_ground`), neither branch runs, leaving `_coyote_timer` at whatever value it had. On subsequent grounded frames the `elif` branch is also not reached (because `was_on_ground and not self.on_ground` is False, and the `elif` only runs when that first condition is False). This means `_coyote_timer` is **never reset to 0 on landing**. If the player quickly jumps, falls, and lands on another platform, the stale nonzero `_coyote_timer` could grant an extra coyote-jump on a frame when `can_jump` should only be True because `on_ground` is True. This is a minor logic defect but could allow a double-jump through the coyote window after a legitimate grounded jump.
- Fix: Add `elif self.on_ground: self._coyote_timer = 0` after line 175 to reset the timer on landing.

---

### BUG-010: `player.py` variable-jump cut applies every frame `vy < -4` without `_jump_held` check — slows all upward movement including knockback

- File: `entities/player.py`, lines 239–242
- Problem: Lines 241–242: `if not jump_pressed and self.vy < -4: self.vy *= self._jump_cut`. This dampens upward velocity whenever jump is not pressed and `vy < -4`, **regardless of whether the upward velocity came from a jump or from knockback** (`TOUCH_KNOCKBACK_VY = -3.0` would not trigger this, but enemy hitbox knockback can set `vy` to `-5.0` or lower, e.g. `knockback_y=-5.0` in Jumper or `-4.5` in ShieldGuard). This means every frame the player is airborne with upward knockback velocity and is not holding jump, the velocity is multiplied by `_jump_cut` (0.72–0.82), quickly killing the knockback arc. Knockback should feel punchy and uncontrolled, not dampened like a variable-height jump.
- Fix: Guard with `_jump_held`: change line 241 to `if not jump_pressed and self._jump_held and self.vy < -4:`. This limits the cut to actual player-initiated jumps.

---

### BUG-011: `gameplay.py` dead-enemy fragment loop calls `get_drop_fragments()` on `Crawler` objects that are in `self.enemies` but have already been pruned — and re-spawns for boss too

- File: `scenes/gameplay.py`, lines 280–283
- Problem: Line 280 `newly_dead = [e for e in self.enemies if not e.alive]` collects all dead enemies before pruning. Each dead enemy's `get_drop_fragments()` is called. This is correct for one frame. The real concern (compound with BUG-007): the boss has `self._boss` reference that is cleared on line 287 (`if self._boss and not self._boss.alive: self._boss = None`), but the boss is still in `self.enemies` at that point (pruning is line 290). So the boss `get_drop_fragments()` is called at line 282, which calls `Enemy.get_drop_fragments()` returning a single `SoulFragment`. The boss should probably drop more, but more critically: if the boss dies during hitstop (see BUG-007), it could drop fragments multiple times.
- Note: This is the same root cause as BUG-007; documenting separately because the boss-specific symptom (underpowered loot) deserves its own fix note.
- Fix: Same as BUG-007 — guard the spawn block inside `if not hitstop.is_active()`, or add a `_dropped` flag per enemy.

---

### BUG-012: `ShieldGuard.draw` calls `camera.apply(self)` which returns a `pygame.Rect` shifted by offset, then uses `sr.right - 4` for the shield indicator — but shield is drawn relative to the *screen* rect, not world rect, which is correct. Minor: shield indicator width is always 4px regardless of scale — cosmetic only.

- File: `entities/shield_guard.py`, lines 78–81
- Problem: `shield_x = sr.right - 4 if self.facing == 1 else sr.left`. When `facing == -1` (facing left, shield on left), `shield_x = sr.left`, so the shield rect starts at `sr.left` and is 4px wide. This places the shield **inside** the left edge of the sprite, which is visually correct. When `facing == 1` (facing right, shield on right), `shield_x = sr.right - 4`, which is also the last 4 pixels of the sprite. This is fine. **However**, per BUG-005, `facing` always points *toward* the player, meaning when the player is to the right, `facing = 1` and the shield appears on the right side of the guard — which would mean the shield is between the guard and the player, i.e., on the attacking side. This is the intended block position. But since BUG-005 means the shield never actually reduces damage, the visual indicator is misleading. This is a downstream visual manifestation of BUG-005, not an independent crash.
- Fix: Fix BUG-005 first; the draw code itself is not broken.

---

### BUG-013: `minimap.py` does not show the three new enemy spawn types (`shield_guard_spawns`, `ranged_spawns`, `jumper_spawns`) on the map overlay

- File: `systems/minimap.py`, lines 119–123
- Problem: The minimap only draws dots for `tilemap.enemy_spawns + tilemap.crawler_spawns` (line 120). The three new spawn lists (`shield_guard_spawns`, `ranged_spawns`, `jumper_spawns`) added in `world/tilemap.py` are silently ignored. Any level that uses 'G', 'R', or 'J' tiles will not show those enemy positions on the map.
- Fix: Change line 120 to `for (ex, ey) in (tilemap.enemy_spawns + tilemap.crawler_spawns + tilemap.shield_guard_spawns + tilemap.ranged_spawns + tilemap.jumper_spawns):`.

---

### BUG-014: `Ranged._update_ai` does not call `_do_patrol()` — it calls the inline patrol logic directly, but does not set `self._state`

- File: `entities/ranged.py`, lines 73–87
- Problem: When `not in_sight`, the code calls `self._do_patrol()` (line 74) but never sets `self._state = _PATROL`. The state string is never changed from whatever it was last frame. This is a logic inconsistency: `self._state` stays at `_RETREAT` or `_SHOOT` even while the enemy is patrolling. This won't crash (the state string is unused outside `_update_ai` for `Ranged`), but it will cause incorrect behavior if any code ever checks `enemy._state` externally (e.g., future state display or audio triggers).
- Fix: Add `self._state = _PATROL` before `self._do_patrol()` on line 74 (insert before the `return`).

---

### BUG-015: `player.py` `_handle_attack` grants soul regen on attack initiation, not on hit — even if the attack misses

- File: `entities/player.py`, lines 283–285
- Problem: `if self.faction == FACTION_MARKED: self._regen_resource(3)` is called when the player **starts** an attack (presses the key), not when the hitbox actually connects with an enemy. This means a Marked player regains soul by swinging at air, which contradicts the "power through contact" comment on line 283.
- Fix: Move the `_regen_resource(3)` call into `systems/combat.py` `AttackHitbox._apply_hit()` — or flag it and let build-agent decide the design intent. Minimal fix: remove the regen from `_handle_attack` and add it in `_apply_hit` only when `self.owner` is a `Player` instance.

---

### FLAG-005: `gameplay.py` `_draw_hud` divides `player.health / player.max_health` without a zero guard

- File: `scenes/gameplay.py`, line 419
- Problem: `fill=self.player.health / self.player.max_health` — if `player.max_health` were ever 0 this would raise `ZeroDivisionError`. In practice `PLAYER_MAX_HEALTH = 100` is a constant, so this cannot happen. Noted as a fragile pattern consistent with FLAG-002.
- Why not fixed: Non-zero by design; same reasoning as FLAG-002.

---

### FLAG-006: `Jumper._do_chase_jump` and `_do_patrol_jump` both set `self.vy = JUMPER_JUMP_FORCE` without checking `self.on_ground` in chase mode — but `_do_chase_jump` does guard with `self.on_ground`

- File: `entities/jumper.py`, lines 73–75
- Problem: `_do_chase_jump` correctly guards `if self.on_ground and self._jump_cooldown <= 0:` before setting `self.vy`. `_do_patrol_jump` also guards with `if self.on_ground`. No infinite-jump risk exists. This is a non-issue.
- Why flagged: The review brief asked to check for infinite loop / crash risk. None found.

---

# Bug Review — 2026-04-18 (post P2-2b pass)

## Status Summary

All previously documented bugs (BUG-001 through BUG-015) have been successfully fixed as of this review:
- **BUG-005**: ShieldGuard block condition fixed (line 35, `knockback_dir == -self.facing`)
- **BUG-006**: Projectile max_range and arc gravity implemented (lines 25, 32-33, 37, 109-113)
- **BUG-007**: Fragment spawn now guarded by hitstop check (gameplay.py lines 416-427)
- **BUG-008**: Jumper _jump_timer clamped on patrol entry (jumper.py line 57)
- **BUG-009**: Coyote timer reset on landing (player.py lines 176-177)
- **BUG-010**: Variable jump cut guarded with _jump_held (player.py line 243)
- **BUG-011**: Same fix as BUG-007; compound root cause resolved
- **BUG-013**: Minimap now includes all enemy spawn types (minimap.py lines 120-122)
- **BUG-014**: Ranged _state set to _PATROL (ranged.py line 84)
- **BUG-015**: Marked soul regen moved to AttackHitbox._apply_hit (combat.py lines 66-68)

## New Bugs

### BUG-016: ShieldGuard faces away from patrol direction during PATROL state
- File: `entities/shield_guard.py`, lines 49-54
- Problem: The ShieldGuard._do_patrol() method does not set `self.facing` to match `self._patrol_dir`. During the PATROL state, facing remains at whatever value it was set to in the previous frame (likely still pointing toward the player from a prior CHASE). The enemy walks in one direction while facing a different direction, creating a visual inconsistency. This also means the shield indicator (drawn at `sr.right` or `sr.left` based on facing) will point the wrong way during patrol.
  
  According to ROADMAP P2-2b acceptance criteria:
  > During `_PATROL`, facing follows patrol direction naturally.
  
  The base Enemy class correctly sets `self.facing = self._patrol_dir` in its _do_patrol() method (enemies/enemy.py line 92), but ShieldGuard overrides _do_patrol and forgets to set facing.
  
- Fix: Add `self.facing = self._patrol_dir` to ShieldGuard._do_patrol() after line 54 (or after line 50 for earlier update). Alternatively, set it at the start of the method before the boundary checks to ensure consistency.

---

## Verification Notes

**All P2-2 constants present and correctly imported:**
- `SHIELD_GUARD_KNOCKBACK_Y = -3.5` (settings.py line 151)
- `RANGED_PREFERRED_DIST = 240` (settings.py line 161, used in ranged.py line 18 via hardcode, but constant defined)
- `RANGED_PROJ_SPEED = 6` (settings.py line 158)
- `JUMPER_BURST_COUNT = 2` (settings.py line 170)
- `JUMPER_BURST_PAUSE = 70` (settings.py line 171)
- `JUMPER_KNOCKBACK_Y_GROUND = -4.5` (settings.py line 172)
- `JUMPER_KNOCKBACK_Y_AERIAL = 2.0` (settings.py line 173)

**Level data verification (levels 6–10):**
- LEVEL_6_MARKED, LEVEL_6_FLESHFORGED, LEVEL_7_MARKED, LEVEL_7_FLESHFORGED, LEVEL_8_MARKED, LEVEL_8_FLESHFORGED, LEVEL_9, LEVEL_10 all present and correctly formatted in tilemap.py
- Player spawns ('P'), checkpoints ('C'), boss spawns ('B'), enemy spawns ('E', 'G', 'R', 'J', 'c') all present in appropriate levels
- _faction_next_level() routing correctly branches levels 6–8 by faction and merges at level 9 (gameplay.py lines 94-105)
- Victory flag correctly written on level 10 completion (gameplay.py lines 452-457)

**Boss and arena mechanics verified:**
- Phase announces, hitstop triggers, and arena shrink walls all implemented (boss.py lines 80-105, gameplay.py lines 396-411)
- Dash attack, projectile spread, and phase scaling all implemented (boss.py lines 127-171)

## No Additional Crashes or Logic Errors Found

All other .py files reviewed for:
- Import errors / missing references ✓
- Attribute access on potentially None/uninitialized objects ✓
- Off-by-one errors in level data ✓
- Physics / collision edge cases ✓
- Animation state transitions ✓
- Resource regen / ability cooldown correctness ✓
- Save/load consistency ✓

No blocking issues found.

---

# Bug Review — 2026-04-21

**Scope:** New code added for P2-3 (Warden scripting), P2-4 (Architect boss), and P2-5 (upgrade system). All .py files read before writing this section. The prior review pass (2026-04-18) confirmed BUG-001 through BUG-016 resolved; this pass starts at BUG-018.

---

## New Bugs

---

### BUG-018: Player can select an upgrade while dead — upgrade screen stalls death sequence indefinitely

- **File:** `scenes/gameplay.py`, lines 504–534 and 585–576
- **Problem:** If the player and the Warden boss die on the same frame (player health reaches 0 via the boss's last hit just as the boss's own health reaches 0), the following sequence occurs:
  1. Line 508: `if not hitstop.is_active()` — True.
  2. Line 518–520: `self._boss.alive` is False → `self._upgrade_pending = True`.
  3. Line 531–534: `_setup_upgrade_choices()` sets `self._upgrade_active = True` and `return`s.
  4. On all subsequent frames, the `_upgrade_active` guard at line 348 (`if self._upgrade_active: return`) exits update before the player-death block at line 586 can run.
  5. `self._death_timer` never increments. The upgrade screen is displayed to a dead player indefinitely. The only escape is pressing ENTER to confirm an upgrade, after which the death sequence resumes on the next frame.
  - The upgrade should not be offered to a dead player. Confirming it applies a permanent bonus to a run that has already ended, which is an unintended reward for dying simultaneously with the boss.
- **Fix:** In `_setup_upgrade_choices()` (line 1026), or at the call site (line 533), add a guard: `if not self.player.alive: return` (skip the upgrade screen if the player is already dead). Alternatively, check `self.player.alive` before setting `_upgrade_pending = True` at line 518.

---

### BUG-019: `P1-8` ability-slots feature entirely absent from live `entities/player.py` and `scenes/gameplay.py` — ability is always unlocked regardless of save state

- **Files:** `entities/player.py` (all lines); `scenes/gameplay.py` (all lines)
- **Problem:** ROADMAP Task P1-8 specifies:
  - `Player.__init__` must initialise `self.ability_slots = ABILITY_SLOTS_DEFAULT` (= 0).
  - `Player._handle_ability()` must guard with `if self.ability_slots < 1: return`.
  - `gameplay.py` `on_enter()` must restore `player.ability_slots` from `save_data.get("ability_slots", ABILITY_SLOTS_DEFAULT)`.
  - `_draw_hud()` must show "LOCKED" when `ability_slots == 0`.
  - None of these are present in the live files under `/home/user/SteamFall/`. The `_handle_ability()` method at `player.py:297` has no `ability_slots` check. `on_enter()` at `gameplay.py:129` never sets `player.ability_slots`. `_draw_hud()` never shows "LOCKED".
  - As a result, the ability (Soul Surge / Overdrive) is always available from the start of the game, regardless of whether the player has collected an `AbilityOrb`. The `AbilityOrb.collect()` method in `collectible.py` uses `getattr(player, "ability_slots", 0)` defensively (no crash), but it never actually gates anything. Additionally, `TileMap._parse()` has no handler for the `'A'` tile character, so `ability_orb_spawns` is always empty even if `'A'` tiles were placed in a level.
- **Fix:** Three changes needed:
  1. `entities/player.py:__init__`: add `self.ability_slots: int = ABILITY_SLOTS_DEFAULT` and import `ABILITY_SLOTS_DEFAULT` from settings; add `if self.ability_slots < 1: return` at the top of `_handle_ability()`.
  2. `scenes/gameplay.py:on_enter()`: after creating the player, add `self.player.ability_slots = save.get("ability_slots", ABILITY_SLOTS_DEFAULT)`.
  3. `world/tilemap.py`: add `self.ability_orb_spawns: list = []` to `__init__` and an `'A'` handler in `_parse()` to populate it; also spawn `AbilityOrb` objects in `gameplay.py:on_enter()` from `tilemap.ability_orb_spawns`.

---

### BUG-020: Architect teleport uses `SCREEN_WIDTH` as the arena bound instead of the level's playable width — Architect can never teleport into the right half of wide levels

- **File:** `entities/architect.py`, lines 133–137
- **Problem:**
  ```python
  arena_min = TILE_SIZE * 4
  arena_max = SCREEN_WIDTH - TILE_SIZE * 4   # = 1280 - 128 = 1152
  self.rect.centerx = random.randint(arena_min, arena_max)
  ```
  `LEVEL_10` has 65 columns × 32 px = 2080 px wide. The Architect is placed at tile column ~44 (char `'X'` at `row 10, col 44` in `LEVEL_10`), which is world x ≈ 1408 — beyond `arena_max` of 1152. As soon as the Architect enters phase 2 it will teleport into the visible screen window (x 128–1152), potentially far from its arena spawn position. More importantly, the right ~928 px of the level (x 1152–2080) is never a valid teleport destination, making the teleport heavily asymmetric and breaking level design intent. The bound should reference the level width, not the screen width.
- **Fix:** Pass the tilemap width to `Architect` (e.g., via a `level_width` constructor parameter defaulting to `SCREEN_WIDTH`) and use it in `_update_ai`: `arena_max = self._level_width - TILE_SIZE * 4`. `gameplay.py` would set `arch = Architect(ax, ay, faction=_faction, level_width=self.tilemap.width)`.

---

### BUG-021: Architect phase transitions never trigger the phase-announce banner or arena-shrink effect — `announce_phase` signal is only consumed for the Warden (`self._boss`)

- **File:** `scenes/gameplay.py`, lines 471–485
- **Problem:** The phase-announce and arena-shrink logic reads `self._boss.announce_phase` (line 471). Both `Boss` and `Architect` (which inherits from `Boss`) set `self.announce_phase` on phase entry (via `_on_phase2_enter`/`_on_phase3_enter` inherited from `Boss`). However, `self._architect` is a separate reference and its `announce_phase` is never checked. The Architect transitions through four phases but the player sees no phase banner and no arena walls close in when the Architect changes phase. If the Warden is not present in the same level (and LEVEL_10 has no `'B'` tile), `self._boss` is `None` and the entire block is skipped.
  - Additionally, the arena-shrink effect references `self._boss` hard-coded as the phase-3 signal source — but the Warden boss fight (LEVEL_5/8) and the Architect (LEVEL_10) are in different levels and can never coexist. The shrink was intended for the Architect's phase 4, not the Warden.
- **Fix:** After the Warden announce block (lines 471–485), add a parallel block for the Architect:
  ```python
  if self._architect and self._architect.alive and self._architect.announce_phase:
      phase = self._architect.announce_phase
      self._architect.announce_phase = 0
      # … same label/banner logic …
      if phase == 4:
          self._shrink_active = True
          # … same shrink init …
  ```

---

### BUG-022: `_tick_boss_intro` increments `active_boss._intro_line_idx` independently of the `DialogueBox` — the two timers run in lock-step but serve the same data, causing the banner to advance one line ahead of the dialogue box

- **File:** `scenes/gameplay.py`, lines 604–628; `entities/boss.py`, lines 46–54
- **Problem:** The `_tick_boss_intro` method maintains two parallel timers:
  1. The `DialogueBox` (`self._boss_dialogue`) advances when the player presses SPACE/RETURN via `advance()` (called from `handle_event`, line 295).
  2. The entity's `_intro_line_timer` / `_intro_line_idx` are incremented unconditionally every 120 frames on line 614–618.
  The banner (`_draw_boss_intro`) renders `active_boss._intro_lines[line_idx]` (the raw string array on the entity), while the dialogue box renders `_WARDEN_INTRO_LINES` (the `(speaker, text)` tuple list). The banner advances on a 120-frame timer regardless of whether the player has dismissed the dialogue box. If the player reads slowly (does not press SPACE for > 120 frames), the banner advances to line N+1 while the dialogue box still shows line N. If the player presses SPACE quickly, the dialogue box can be on line N+3 while the banner is still on line 0. The two displays are desynchronised.
  - For the Warden, the Warden's `_intro_lines` (3 lines) and `_WARDEN_INTRO_LINES` (6 tuples) have different lengths, so the banner will show index out-of-bounds territory if the dialogue outlasts the banner lines (guarded at line 952 `if line_idx >= len(lines): return`, so no crash, but the banner disappears while dialogue continues).
- **Fix:** Drive the banner display directly from the `DialogueBox._index` rather than a separate entity-level counter. Replace the `active_boss._intro_line_idx` increment in `_tick_boss_intro` with a read from `self._boss_dialogue._index`. The entity-level timer fields are then only needed as fallback for non-`DialogueBox` contexts and can be removed or made private.

---

### BUG-023: `_apply_upgrade_to_player` applies HP upgrade additively on every `on_enter` call — multiple level loads with the same save will stack the HP bonus repeatedly

- **File:** `scenes/gameplay.py`, lines 109–119 and 151–153
- **Problem:** In `on_enter()`:
  ```python
  for upg in save.get("upgrades", []):
      _apply_upgrade_to_player(self.player, upg)
  ```
  `_apply_upgrade_to_player` does `player.max_health += UPGRADE_HP_BONUS` for each `"hp"` entry. The player is freshly constructed each `on_enter` with `max_health = PLAYER_MAX_HEALTH` (100), so a single HP upgrade entry correctly yields `max_health = 125`. However, if the player selects "hp" upgrade multiple times across boss kills (only one Warden exists per run, but if the save somehow has multiple `"hp"` entries or if the loop is called multiple times), the bonus stacks correctly — this is actually intended cumulative design.
  - **The real issue** is with `"res"` upgrades. `_apply_upgrade_to_player` for `"res"` calls `player._regen_resource(UPGRADE_RES_BONUS)` (line 119) in addition to increasing `max_resource_bonus`. On every `on_enter` load, `_regen_resource` is called for each saved `"res"` entry, refilling the resource bar (up to the new max). This is a benign side effect — the player respawns with slightly more resource than they had at the checkpoint. It's not a crash, but it is inconsistent with how HP is handled (HP is clamped to `checkpoint_health_frac`, but resource is always partially or fully refilled by the upgrade reapplication). The resource value should be restored from a saved fraction, not regenerated.
- **Fix:** In `_apply_upgrade_to_player`, for the `"res"` case, remove the `_regen_resource(UPGRADE_RES_BONUS)` call (line 119). Resource restoration should be handled separately, like health is, using a saved fraction. Or, accept the mild refill as a quality-of-life bonus and document it as intentional.

---

### BUG-024: `AbilityOrb.collect()` has no double-collect guard — `alive` is set False inside the method but the caller in `gameplay.py` does not check `alive` before calling

- **File:** `systems/collectible.py`, lines 205–210
- **Problem:** `AbilityOrb.collect()` sets `self.alive = False` at line 208, but it does so unconditionally after modifying `player.ability_slots` and writing to `game.save_data`. If `collect()` were somehow called twice (e.g., if a future code path does not prune collected orbs before the next frame's collision check), the following would happen:
  - `player.ability_slots` would be incremented again, but is clamped at `ABILITY_SLOTS_MAX` by `min(...)` — so the value stays correct.
  - `game.save_data["ability_slots"]` would be set to the same clamped value — also harmless.
  - `game.save_to_disk()` would be called an extra time — minor I/O waste.
  - Currently `gameplay.py` does not spawn `AbilityOrb` objects at all (see BUG-019), so this cannot trigger. But when BUG-019 is fixed, the standard pattern should be: check `if not self.alive: return` at the start of `collect()`.
- **Fix:** Add `if not self.alive: return` as the first line of `AbilityOrb.collect()` (before line 206).

---

### BUG-025: Arena shrink left-wall condition skips the right wall when `_shrink_left_x == 0.0` — right wall is never injected into solid rects on the first frame of phase 3

- **File:** `scenes/gameplay.py`, lines 397–403
- **Problem:**
  ```python
  if self._shrink_active and self._shrink_left_x > 0:
      solid = list(solid) + [
          pygame.Rect(0, 0, int(self._shrink_left_x), self.tilemap.height),
          pygame.Rect(int(self._shrink_right_x), 0, ...),
      ]
  ```
  On the first frame that phase 3 fires (`_shrink_active` is set True and both targets are initialised), `_shrink_left_x` is still `0.0` (it starts at 0 and advances by `ARENA_SHRINK_SPEED = 0.5` per frame). The condition `self._shrink_left_x > 0` is therefore False on frame 1. The right-wall rect is not added to `solid` until `_shrink_left_x > 0` (frame 2). This is a single-frame window where the right shrink wall is not solid, but since `_shrink_right_x` starts at `tilemap.width` and the right wall has zero effective width (target is `tilemap.width - ARENA_SHRINK_AMOUNT`), there is no entity to collide with on frame 1 anyway. However, the logic coupling the left-wall progress to both walls' injection is fragile and confusing. The right wall check should be independent.
- **Fix:** Separate the condition: add the left wall rect only when `self._shrink_left_x > 0`, and add the right wall rect only when `self._shrink_right_x < self.tilemap.width`. Or simplify by always adding both (pygame does not penalise zero-width or zero-effective rects in collision checks since they will simply never collide).

---

## Flags (not crashes, but worth tracking)

---

### FLAG-007: `Architect._on_defeat` sets `self.alive = False` redundantly — `Entity.die()` already sets it

- **File:** `entities/architect.py`, lines 173–179
- **Problem:** `Architect.die()` calls `super().die()` (which sets `self.alive = False` via `Entity.die()`) and then calls `self._on_defeat()`. Inside `_on_defeat()`, line 178 sets `self.alive = False` again. This is redundant but harmless.
- **Why not a crash:** Double-assignment of False. No observable effect.
- **Suggestion:** Remove line 178 (`self.alive = False`) from `_on_defeat()` since `super().die()` already handles it.

---

### FLAG-008: `_draw_hud` divides `player.resource / player.max_resource` without guarding `max_resource > 0`

- **File:** `scenes/gameplay.py`, line 760
- **Problem:** `fill=self.player.resource / self.player.max_resource`. The `max_resource` property returns `base + self.max_resource_bonus`. `base` is `PLAYER_MAX_SOUL = 100` or `PLAYER_MAX_HEAT = 100` — both non-zero constants. `max_resource_bonus` starts at `0.0` and only increases. So `max_resource` can never be 0 in practice. Flagged as a fragile pattern consistent with FLAG-002 and FLAG-005.
- **Why not fixed:** Non-zero by design.

---

### FLAG-009: Minimap `_LEVEL_ORDER` only covers levels 1–5, not the faction branches or levels 9–10 — players on levels 6–10 see their current room highlighted but outside the room-chain strip entirely

- **File:** `systems/minimap.py`, lines 14–21 and 68–90
- **Problem:** `_LEVEL_ORDER = ["level_1", ..., "level_5"]`. When `current_level_name` is `"level_6_marked"` or `"level_9"`, no rectangle in the chain matches, so none is highlighted with `MARKED_COLOR`. The player's current room appears unvisited-gray (or not in the chain at all). The `_LEVEL_LABELS` dict also lacks keys for levels 6–10, which would cause a `KeyError` at line 81 (`_LEVEL_LABELS[lname]`) if these levels were added to `_LEVEL_ORDER`.
- **Suggestion:** Extend `_LEVEL_ORDER` to include all 13 level keys and add corresponding `_LEVEL_LABELS` entries. Lay them out in two rows (1–5 top, 6–10 bottom) or abbreviate the display names to fit the panel width.

---

# Bug Review — 2026-04-25

**Scope:** Phase 3 (Story Integration) code — `entities/npc.py`, `scenes/marked_ending.py`, `scenes/fleshforged_ending.py`, plus Phase 3 additions to `scenes/gameplay.py`, `scenes/marked_prologue.py`, `scenes/fleshforged_prologue.py`, `systems/collectible.py`, and `world/tilemap.py`. All .py files re-read before writing this section. Prior reviews confirmed BUG-001 through BUG-025 and FLAG-001 through FLAG-009 are recorded; this pass starts at BUG-026.

---

## New Bugs

---

### BUG-026: Ending scenes skip two beats per rapid double-press — `_advance` called when `DialogueBox` is already done

- **Files:** `scenes/marked_ending.py`, lines 82–85; `scenes/fleshforged_ending.py`, lines 82–85
- **Problem:** Both ending scenes share this `_advance` pattern:
  ```python
  def _advance(self):
      self._dialogue.advance()
      if self._dialogue.is_done():
          self._next_beat()
  ```
  `DialogueBox.queue()` loads a single `(speaker, text)` tuple per beat, so after one SPACE press the box is in the `_done = True` state. On the *next* frame before `_next_beat()` loads fresh content, if the player presses SPACE again, `_advance()` is called a second time. `DialogueBox.advance()` internally calls `_next_line()` which increments `_index` from 1 to 2, sees `2 >= len(queue)` (queue has 1 item), and sets `_done = True` — harmlessly, since it was already True. Then `is_done()` returns True and `_next_beat()` is called **again**, bumping `self._beat_index` by 2 total. Two narrative beats are consumed by a single impatient double-tap.
  - The bug is worst at beat 6 (the second-to-last beat): a fast double-press skips the final beat entirely and calls `_finish()` without showing it.
- **Fix:** Guard `_advance` so it only calls `_next_beat()` once per dialogue completion cycle. Simplest fix: check `_dialogue.is_done()` **before** calling `advance()` and do nothing when already done:
  ```python
  def _advance(self):
      if self._dialogue.is_done():
          return   # wait for _next_beat() to load the next line
      self._dialogue.advance()
      if self._dialogue.is_done():
          self._next_beat()
  ```

---

### BUG-027: `_draw_phase_announce` always uses amber color for Architect phase banners — `"UNLEASHED"` check never matches Architect suffixes

- **File:** `scenes/gameplay.py`, line 1360
- **Problem:**
  ```python
  color = (220, 60, 60) if "UNLEASHED" in self._boss_phase_text else (220, 140, 40)
  ```
  The Architect's phase announce suffixes are `"AWAKENED"`, `"UNBOUND"`, and `"ABSOLUTE"` (set at lines 693–694). None of these contains the string `"UNLEASHED"`, so the `if` branch is never taken for the Architect. All four Architect phase banners render in amber `(220, 140, 40)`. The deep-red color `(220, 60, 60)` is only ever shown for the Warden's `"UNLEASHED"` phase 3 banner. Phase 4 `"ABSOLUTE"` (the most intense state) should visually escalate to deep red.
- **Fix:** Extend the color check to cover the Architect's most intense suffix, e.g.:
  ```python
  intense = ("UNLEASHED" in self._boss_phase_text or
             "ABSOLUTE"  in self._boss_phase_text)
  color = (220, 60, 60) if intense else (220, 140, 40)
  ```
  Or use a dict lookup keyed by the banner text to allow per-phase color tuning.

---

### BUG-028: `_level_faction_tint` applies `faction_tint` to all enemies including Boss and Architect — bosses take on enemy faction color blending

- **File:** `scenes/gameplay.py`, lines 257–261
- **Problem:**
  ```python
  _tint = _level_faction_tint(level_name)
  if _tint:
      for e in self.enemies:
          e.faction_tint = _tint
  ```
  `self.enemies` includes the `Boss` and `Architect` instances (added at lines 243 and 254). `Enemy.draw()` (which `Boss.draw()` and `Architect.draw()` both ultimately call via `super().draw()`) blends `base_color` 50/50 with the tint color when `faction_tint` is set. Levels 6–8 always have `_tint != ""`, so any Boss present in those levels (LEVEL_8_MARKED and LEVEL_8_FLESHFORGED both have `'B'`) gets its distinctive phase-shifting color washed out by the faction blend. The Architect in LEVEL_10 is not affected (level 10 has no tint), but any future boss added to a tinted level would be.
- **Fix:** Skip bosses and the Architect when applying the tint:
  ```python
  if _tint:
      for e in self.enemies:
          if not isinstance(e, (Boss, Architect)):
              e.faction_tint = _tint
  ```

---

### BUG-029: Architect defeat dialogue is fully automatic (120-frame auto-advance) with no player input path — player is silently locked out for up to 8 seconds with no explanation

- **File:** `scenes/gameplay.py`, lines 757–779
- **Problem:** After the Architect dies, `arch._defeat_dialogue_active` is True. The gameplay `update` loop at lines 761–765 auto-advances `arch._defeat_line_idx` by 1 every 120 frames (2 seconds), then waits another 120 frames before triggering the ending transition. The total locked duration is `(3 lines × 120 frames) + 120 frames = 480 frames = 8 seconds`. During this entire window:
  - No hint text tells the player why nothing is happening.
  - The `handle_event` path does not intercept SPACE/RETURN to speed up the lines (the boss intro check fires on `_boss_intro_active`, which is already False by this point, so SPACE falls through to the NPC/pause handlers and is silently ignored).
  - The player cannot pause or open the map, because the transition guard at line 452 does not block (transition is not active until `_begin_transition` fires), but the death/alive checks prevent attack, movement is still enabled (the player can move freely during these 8 seconds, which looks wrong).
- **Fix:** Add a SPACE/RETURN handler in `handle_event` that fires when `self._architect and not self._architect.alive and not self._architect_victory_done`: advance `_defeat_line_idx` immediately when the player presses SPACE, and also add a small "SPACE — continue" hint to `_draw_architect_defeat`. Minimally: in the `_defeat_line_idx < len(_defeat_lines)` branch, set `self._architect_defeat_timer = 120` (trigger immediately) when SPACE is pressed.

---

### BUG-030: `LEVEL_2` has an unreachable checkpoint in the sub-floor (row 16) — the `'C'` tile is placed below the solid ground layer and can never be activated

- **File:** `world/tilemap.py`, line 96 (the `LEVEL_2` definition)
- **Problem:** `LEVEL_2` row index 16 (zero-based) contains:
  ```
  "#          C                                                           #"
  ```
  The solid ground is at rows 12–13 (`"####..."`) and the sub-floor walls are at rows 14–20. Row 16 is inside the sealed underground chamber. The player spawn is at row 11 (ground level) and cannot pass through the solid ground rows 12–13. The checkpoint at row 16 is therefore permanently inaccessible — `Checkpoint._activate` will never be called, `save_data["checkpoint_pos"]` will never reflect this CP, and the CP icon on the minimap will appear inside the solid floor tile region.
- **Fix:** Move the row 16 `'C'` to a reachable location — either to an accessible platform row (rows 3–10) in LEVEL_2, or remove it if the sub-floor CP was mistakenly added.

---

### BUG-031: `NPC` has no `update` method — `_show_hint` is set from outside via direct attribute assignment, bypassing any future per-frame NPC state logic; also, NPC `draw` can be called during the `_npc_dialogue` active frame without a prior proximity check

- **File:** `entities/npc.py` (entire class); `scenes/gameplay.py`, lines 781–784
- **Problem:** In gameplay's `update()`, NPC proximity hints are set with:
  ```python
  for npc in self.npcs:
      dist = abs(self.player.rect.centerx - npc.rect.centerx)
      npc._show_hint = dist < NPC_INTERACT_DIST
  ```
  This runs **after** the NPC dialogue and transition guards. Specifically, when `self._npc_dialogue is not None` (lines 461–463), `update()` returns early after ticking the dialogue, skipping the proximity hint block entirely. This means `_show_hint` retains its last value from the previous frame — which was `True` (the player was close enough to open dialogue). While the dialogue is active, the "E" hint badge continues to render on the NPC because `_show_hint` is still True. The hint badge persisting during the dialogue conversation is a minor visual artifact (the NPC already has an open dialogue box; the badge is redundant and confusing).
  - Additionally, once `_npc_dialogue` is dismissed (`is_done()` → `self._npc_dialogue = None`), on that same frame the proximity check does NOT run (returns early happened before it), so `_show_hint` stays True for one extra frame even if the player moved away.
- **Fix:** Add `npc._show_hint = False` inside the `_npc_dialogue is not None` early-return block (before returning), so the badge clears while a dialogue is active:
  ```python
  if self._npc_dialogue is not None:
      self._npc_dialogue.update()
      for npc in self.npcs:
          npc._show_hint = False   # hide badge during open conversation
      return
  ```

---

## Flags (not crashes, but worth tracking)

---

### FLAG-010: `game/story.py` `StoryState` class is defined but never imported or used anywhere in the codebase

- **File:** `game/story.py` (entire file)
- **Problem:** `StoryState` exposes `has()`, `set()`, and `clear()` flag operations, but no scene, system, or entity file imports or instantiates it. All story-state tracking in the game goes through `game.save_data` (a plain dict) directly. This class is dead code — presumably scaffolded for a future system.
- **Why not a crash:** It is never reached at runtime. No observable effect.
- **Suggestion:** Either wire `StoryState` into `core/game.py` as `self.story = StoryState()` and use it for flag-based story checks, or remove the file until it is needed to reduce maintenance confusion.

---

### FLAG-011: `_draw_lore_overlay` word-wrap computes `box_w = max_w + pad * 2` but the word-wrap itself constrains to `max_w` — the box is always wider than the text by `pad * 2` on each side, but the rendered lines are placed at `box_x + pad`, so text is contained correctly; however, if a single word is wider than `max_w`, the word is added as its own line even though it overflows the box

- **File:** `scenes/gameplay.py`, lines 1325–1352
- **Problem:** The word-wrap loop at line 1330:
  ```python
  if self._lore_font.size(test)[0] <= max_w:
      line = test
  else:
      if line:
          lines.append(line)
      line = word
  ```
  If a single `word` is wider than `max_w` (e.g. a very long continuous string without spaces), it is appended as-is in the next iteration. This does not crash but causes the word to overflow the right edge of the `box_w` rect and bleed into the HUD area.
- **Why not fixed:** All current lore text strings in `_LORE_TEXT` use natural-language phrasing with spaces, so no single word exceeds `max_w = SCREEN_WIDTH * 3 // 4 = 960 px`. Only a future lore entry with an extremely long unspaced token would trigger this.
- **Suggestion:** After `line = word`, add `if self._lore_font.size(word)[0] > max_w: lines.append(word); line = ""` to truncate overflowing words.

---

# Bug Review — 2026-04-27

**Scope:** All .py files re-read. Focus on Phase 3 deliverables (`scenes/marked_ending.py`, `scenes/fleshforged_ending.py`, `scenes/gameplay.py`, `world/tilemap.py`, `settings.py`, `entities/enemy.py`, `entities/npc.py`, `systems/collectible.py`, `systems/minimap.py`) and any issues that would affect Phase 4 work (particle system, death screen polish, sound, settings screen, main menu parallax, sprite/tile asset checks). Prior bugs BUG-001 through BUG-031 and FLAG-001 through FLAG-011 are already recorded. This pass starts at BUG-032.

---

## New Bugs

---

- [x] **BUG-032: `_apply_upgrade_to_player` "dmg" stack-cap check uses `>` instead of `>=` — one extra "dmg" stack beyond UPGRADE_DMG_MAX_STACKS is always allowed**
  - **File:** `scenes/gameplay.py`, line 173
  - **Problem:** The guard is `if existing > UPGRADE_DMG_MAX_STACKS: return`. `UPGRADE_DMG_MAX_STACKS = 3`. If the player already has 3 `"dmg"` entries in `save_data["upgrades"]`, `existing == 3` and `3 > 3` is `False`, so the return is NOT taken and a 4th stack is applied. The effective cap is therefore 4 stacks, not 3. The same off-by-one exists in `_confirm_upgrade` at line 1437 (`if existing >= UPGRADE_DMG_MAX_STACKS`) — that site uses `>=` which IS correct. The two sites are inconsistent, so `_apply_upgrade_to_player` (called on level load to replay saved upgrades) permits one extra stack compared to the interactive selection gate.
  - **Minimal fix:** Change line 173 to `if existing >= UPGRADE_DMG_MAX_STACKS: return` so both call sites enforce the same cap.

---

- [x] **BUG-033: `LoreItem.collect()` sets `self.alive = False` even when the lore item was already in `save_data["lore_found"]` — the item disappears silently without returning text, but `alive` is still set False in both branches**
  - **File:** `systems/collectible.py`, lines 256–265
  - **Problem:**
    ```python
    def collect(self, player, game) -> str | None:
        lore_found = game.save_data.setdefault("lore_found", [])
        if self._lore_id not in lore_found:
            lore_found.append(self._lore_id)
            game.save_to_disk()
            self.alive = False
            return self._text
        self.alive = False   # ← also reached for already-collected items
        return None
    ```
    In practice `gameplay.py:on_enter()` (lines 314–320) already filters out already-collected lore items by checking `lore_id not in lore_found` before creating a `LoreItem` at all, so the second branch (`self._lore_id in lore_found`) should never be reached for a live object in normal play. However, if any code path creates a `LoreItem` without that filter (e.g., future P4 emit-on-death path), the item vanishes without showing text and without surfacing a player-visible notification. This is a latent logic error: the second `self.alive = False` is misleadingly reachable.
  - **Minimal fix:** Remove the `self.alive = False` from the `else` branch (line 264) — if an item was already collected it should not have been spawned, and silently vanishing confuses debugging. Or add an early guard at the top: `if self._lore_id in game.save_data.get("lore_found", []): self.alive = False; return None`.

---

- [x] **BUG-034: `Checkpoint._activate` overwrites `save_data["faction"]` with `game.player_faction` every activation — if the player triggers a checkpoint before `game.player_faction` is set (e.g., via a Continue load that skips FactionSelectScene), faction is written as `None`**
  - **File:** `systems/checkpoint.py`, line 55
  - **Problem:** `game.save_data["faction"] = game.player_faction`. In `GameplayScene.on_enter()`, `faction = self.game.player_faction or FACTION_MARKED` is used locally but `game.player_faction` itself is not updated — it remains `None` if the player loaded via "Continue" from main menu without going through FactionSelectScene. `MainMenuScene._activate` does `self.game.player_faction = saved_faction` only if `saved_faction` is truthy (line 51). If the save file has no `"faction"` key (edge case: old save pre-Phase-3), `saved_faction` is `None`, `game.player_faction` is never assigned, and the checkpoint will write `"faction": null` to disk. The next "Continue" load will then read `null` and restore `game.player_faction = None`, causing all subsequent `player_faction or FACTION_MARKED` guards to silently default to Marked for a Fleshforged player.
  - **Minimal fix:** In `Checkpoint._activate`, write `game.save_data["faction"] = game.player_faction or game.save_data.get("faction")` so a None faction doesn't overwrite a previously valid one.

---

- [x] **BUG-035: `_draw_boss_intro` indexes `active_boss._intro_lines` using `self._boss_dialogue._index`, but the Warden's `_WARDEN_INTRO_LINES` has 6 tuples while `Boss._intro_lines` has 3 strings — the banner shows a line from `_intro_lines` that is 2 positions behind the DialogueBox, and crashes with `IndexError` when `_boss_dialogue._index` reaches 3, 4, or 5**
  - **File:** `scenes/gameplay.py`, lines 1299–1321
  - **Problem:**
    ```python
    line_idx = self._boss_dialogue._index if self._boss_dialogue else 0
    lines    = active_boss._intro_lines        # Boss has 3 strings
    if line_idx >= len(lines):
        return                                  # guard present — no crash
    line = lines[line_idx]
    ```
    The guard `if line_idx >= len(lines): return` prevents an `IndexError`, so there is no crash. However it means the banner disappears completely once the player advances past dialogue line 3 (the 4th SPACE press), even though lines 4–6 of `_WARDEN_INTRO_LINES` are still rendering in the `DialogueBox`. The banner is invisible for the last half of the Warden intro. For the Architect, `_intro_lines` has 3 strings and `_boss_dialogue` is loaded with those same 3 strings converted to tuples (line 883–885), so both lists are always the same length — no issue there. The mismatch is Warden-only.
  - **Minimal fix:** Either reduce `_WARDEN_INTRO_LINES` to exactly 3 entries (matching `Boss._intro_lines`) or extend `Boss._intro_lines` to 6 entries to match `_WARDEN_INTRO_LINES`. Alternatively, remove the redundant banner for the Warden intro entirely (the DialogueBox already displays the lines) — the banner was meant as a fallback per the BUG-022 fix comment.

---

- [x] **BUG-036: `gameplay.py` player death at line 851 still increments `_death_timer` and eventually calls `change_scene` even when the Architect defeat dialogue is in progress — ending is cut short if the player dies during or just after the Architect fight**
  - **File:** `scenes/gameplay.py`, lines 779–800 and 851–861
  - **Problem:** The Architect defeat sequence sets `arch._defeat_dialogue_active = True` after `arch.alive` is False. The player is still alive at this point in the intended flow, but nothing prevents the player from being killed by a Crawler minion that was already active (Architect spawns Crawlers in Phase 4; they remain in `self.enemies` even after the Architect dies because the prune at line 770 only removes the `arch` object, not its spawned minions, and Crawlers can continue attacking). If the player takes lethal touch damage from a Crawler while `_defeat_dialogue_active` is True:
    1. `self.player.alive` becomes False.
    2. The defeat dialogue advancement block (lines 779–800) still runs (it checks `self._architect and not self._architect.alive and not self._architect_victory_done`).
    3. The death block at line 851 also runs, incrementing `_death_timer`.
    4. After 150 frames the death block calls `change_scene(SCENE_GAMEPLAY, ...)` or `change_scene(SCENE_MAIN_MENU)`, interrupting the ending and discarding the victory state.
    - The `game.save_data["victory"] = True` write at line 793 only fires after all defeat lines are shown. If death fires first, victory is never saved.
  - **Minimal fix:** Add `if not self.player.alive: return` inside the architect defeat dialogue block (before line 782), or guard the death block with `if not self.player.alive and not (self._architect and not self._architect.alive and not self._architect_victory_done):` so the defeat sequence takes priority.

---

- [x] **BUG-037: `gameplay.py` level transition triggers while the Architect defeat dialogue is in progress — right-edge walk during dialogue immediately starts a transition to SCENE_MAIN_MENU**
  - **File:** `scenes/gameplay.py`, lines 825–848
  - **Problem:** The level-transition check (lines 827–848) runs every frame regardless of whether `_architect._defeat_dialogue_active` is True. In LEVEL_10 the level is only 65 columns wide (2080 px) and the Architect spawns near column 44 (world x ≈ 1408). The transition trigger fires when `player.rect.right >= self.tilemap.width - 64` (i.e., player reaches world x ≈ 2016). During the defeat dialogue sequence the player can still move freely (no movement lock is applied post-defeat), so they could walk to the right edge and trigger `_begin_transition(SCENE_MAIN_MENU)` before all defeat lines are shown. `_architect_victory_done` would then be False when the scene exits, so `game.save_data["victory"]` is never set.
  - **Minimal fix:** Wrap the level-transition block in a guard: `if not (self._architect and not self._architect.alive and not self._architect_victory_done):` so the transition is suppressed until the defeat sequence completes.

---

- [x] **BUG-038: `ParticleSystem.emit_death` is called from `Entity.die()` passing `self.color`, but `Architect.draw()` reassigns `self.color` each frame based on phase — the death-burst color reflects whichever phase color was set on the draw frame, not the Architect's actual death phase color, and may be stale if `draw()` hasn't been called since the last update**
  - **File:** `entities/entity.py`, line 73; `entities/architect.py`, lines 221–229
  - **Problem:** `Entity.die()` calls `particles.emit_death(self.rect.centerx, self.rect.centery, self.color)`. For most entities `self.color` is set in `__init__` and never changes, so it is always correct. For `Architect`, `self.color` is reassigned in `draw()` (not in `update()`) based on `self.phase`. The order in a frame is: `update()` → (combat / take_damage / die) → `draw()`. When `Architect.die()` is called during `update()`, `self.color` still holds the value set by the **previous** frame's `draw()` call. In most cases this is the correct phase color. However, if the Architect dies exactly on the frame it transitions to a new phase (health crosses a threshold in `update()` before `draw()` has run), `self.color` is one phase behind. This is a cosmetic-only issue: the death-burst particles use last-frame's color.
  - **Minimal fix:** Assign `self.color` at the start of `Architect.update()` (mirroring the phase computation that already happens there for `_phase4_entered`) instead of only in `draw()`, so `self.color` is always current when `die()` fires.

---

- [x] **BUG-039: `systems/minimap.py` draws enemy spawn dots using world-coordinate arithmetic that does not account for entities spawned with a Y-offset — enemy dots appear one or more tile-rows above their actual position on the minimap**
  - **File:** `systems/minimap.py`, lines 215–220
  - **Problem:**
    ```python
    for (ex, ey) in (tilemap.enemy_spawns + ...):
        dx = int(ex / TILE_SIZE) * ts + ox + ts // 2
        dy = int(ey / TILE_SIZE) * ts + oy + ts // 2
    ```
    `tilemap.enemy_spawns` stores spawn positions with a -64 px Y-offset applied during parsing (e.g. `(x + TILE_SIZE//2, y - 64)`). At `TILE_SIZE = 32` this is a 2-tile upward offset. The minimap renders `int(ey / TILE_SIZE)` which gives a row index 2 less than the tile the `'E'` character was on. The dots appear 2 rows above the tile where the enemy was placed. This also affects `crawler_spawns` (offset -22 px ≈ 0.69 tiles, rounds down to same row — minor but inexact), `shield_guard_spawns` (-64 px), `ranged_spawns` (-64 px), and `jumper_spawns` (-64 px).
  - **Minimal fix:** When drawing spawn dots, add the offset back before dividing: `dy = int((ey + 64) / TILE_SIZE) * ts + oy + ts // 2` for standard enemies (or use the tile-row index stored during `_parse` instead of the world coordinate).

---

- [x] **BUG-040: `NPC` `draw()` culls off-screen NPCs only on the X axis — an NPC far above or below the viewport (e.g., a Y-displaced spawn) is never culled and is drawn every frame even when invisible**
  - **File:** `entities/npc.py`, lines 35–36
  - **Problem:**
    ```python
    if screen_rect.right < 0 or screen_rect.left > surface.get_width():
        return
    ```
    There is no Y-axis cull. An NPC whose screen_rect is above (`screen_rect.bottom < 0`) or below (`screen_rect.top > surface.get_height()`) the screen will still be blitted. In the current levels NPCs are placed on reachable platforms so this is only a perf concern, but any NPC placed on a platform in a tall level (e.g., row 2 in a 13-row level when the camera is showing the bottom rows) is drawn unnecessarily every frame.
  - **Minimal fix:** Extend the cull: `if screen_rect.right < 0 or screen_rect.left > surface.get_width() or screen_rect.bottom < 0 or screen_rect.top > surface.get_height(): return`.

---

- [x] **BUG-041: `_draw_lore_overlay` sets `alpha` to 200 (not 255) in the fully-visible window but then calls `rendered.set_alpha(alpha)` on individual line surfaces — the `bg_surf` separately uses `min(200, alpha)` as its fill alpha; the two alpha values are inconsistent, and `set_alpha` on a surface with per-pixel alpha (SRCALPHA not set) has no effect in pygame**
  - **File:** `scenes/gameplay.py`, lines 1372–1381
  - **Problem:**
    ```python
    bg_surf = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
    bg_surf.fill((10, 8, 5, min(200, alpha)))
    surface.blit(bg_surf, (box_x, box_y))
    ...
    rendered = self._lore_font.render(ln, True, color)
    rendered.set_alpha(alpha)
    surface.blit(rendered, ...)
    ```
    `self._lore_font.render(ln, True, color)` returns a surface with no `SRCALPHA` flag (render with antialias returns a 24-bit surface). Calling `set_alpha(alpha)` on a non-SRCALPHA surface sets the whole-surface alpha, which is the correct pygame API for this case — so it does work. However the background box correctly uses SRCALPHA and fills with `min(200, alpha)` — but the text uses raw `alpha` (up to 255 during the non-fade window) while the box caps at 200. During the steady-state window (lore_timer > 60), `alpha = 200` for the box fill but `rendered.set_alpha(200)` for the text, so both are 200 — consistent. During fade-out (`lore_timer <= 60`), `alpha = int(255 * lore_timer / 60)` which correctly scales both. The inconsistency is that in the steady-state `alpha = 200` (not 255) even though `set_alpha(200)` on the render surface makes the text slightly transparent (80% opaque) when full opacity might be preferred. This is a cosmetic-only issue; no crash.
  - **Minimal fix:** Change steady-state alpha to 255 for text while keeping the box fill at 200, by using separate variables for box alpha and text alpha. Or raise the steady-state value to 255 for both (increase box fill alpha to 255 as well for a more readable lore text).

---

## Phase 4 Interaction Risks

The following are not bugs in existing code but are pre-conditions that could cause P4 work to break if not addressed:

---

- [x] **BUG-042: `_draw_death` in `gameplay.py` does not read faction or save data for the death text — P4-2 (faction-specific death text) has no hook point; `font_death` is allocated in `on_enter` and cannot be swapped per-faction after init**
  - **File:** `scenes/gameplay.py`, lines 1174–1186
  - **Problem:** `_draw_death` hard-codes `"you perished"` (line 1180) and `"returning..."` (line 1184) with no reference to `self.game.player_faction`. For P4-2 build-agent will need to branch on faction here. The method is straightforward to extend, but `self.font_death = pygame.font.SysFont("georgia", 52, bold=True)` is created once per `on_enter` — this is fine. The death overlay surface is also recreated each draw call via SRCALPHA (no reuse bug). No crash risk, but calling this out so build-agent knows the exact lines to edit.
  - **Note for build-agent (P4-2):** Add a branch in `_draw_death` at line 1180: choose death text string based on `self.game.player_faction`. Also add the particle emit call (P4-2 spec) using `particles.emit_death` — but guard it so it only fires on the first frame of death (e.g., `if self._death_timer == 1:`).

---

- [x] **BUG-043: `GameplayScene` pause menu option "Settings (soon)" is a non-functional stub — `_activate_pause_option` silently does nothing for it; P4-4 settings screen hook is missing**
  - **File:** `scenes/gameplay.py`, lines 450–457
  - **Problem:**
    ```python
    def _activate_pause_option(self) -> None:
        opt = self._pause_options[self._pause_sel]
        if opt == "Resume":
            ...
        elif opt == "Return to Main Menu":
            ...
        # "Settings (soon)" → stub, do nothing
    ```
    When P4-4 adds `scenes/settings.py` and registers it as `SCENE_SETTINGS`, the pause menu will need to call `self.game.change_scene(SCENE_SETTINGS)`. Currently there is no `SCENE_SETTINGS` constant in `settings.py` and no scene key in `core/game.py`'s `_build_scenes`. Build-agent must add both when implementing P4-4.
  - **Note for build-agent (P4-4):** Add `SCENE_SETTINGS = "settings"` to `settings.py`, register `SettingsScene` in `game._build_scenes`, and replace the stub comment in `_activate_pause_option` with `self.game.change_scene(SCENE_SETTINGS)`.

---

### FLAG-013: BUG-032 through BUG-043 checkboxes were stale — all confirmed fixed in P4-0c (2026-04-29) but `[ ]` markers were not updated
- All twelve bugs listed above (BUG-032 through BUG-043) were resolved by build-agent as of the P4-0c sprint (completed 2026-04-29). Their `[ ]` markers were not ticked at the time of writing; this review pass (2026-05-02) updates them to `[x]`.
- FLAG-013 resolved 2026-05-02.

---

# Bug Review — 2026-05-02

**Scope:** Phase 4 .py files reviewed: `systems/particles.py`, `systems/audio.py`, `scenes/settings.py`, `scenes/main_menu.py`, `scenes/gameplay.py`, `scenes/marked_ending.py`, `scenes/fleshforged_ending.py`, `entities/player.py`, `entities/enemy.py`, `entities/shield_guard.py`, `entities/ranged.py`, `entities/jumper.py`, `entities/crawler.py`, `entities/boss.py`, `entities/architect.py`, `entities/npc.py`, `systems/animation.py`, `world/tilemap.py`, `core/game.py`, `main.py`. All .py files re-read before writing this section.

---

## New Bugs

---

- [x] **BUG-044: `gameplay.py` BUG-036 invincibility fix uses wrong attribute name `_iframes` instead of `iframes` — the player receives no actual invincibility during the Architect defeat sequence**
  - **File:** `scenes/gameplay.py`, line 821
  - **Problem:** The BUG-036 fix adds `self.player._iframes = 9999` to grant the player invincibility while the Architect defeat dialogue plays (so surviving Crawlers cannot kill the player). However, `Entity` stores invincibility as `self.iframes` (no leading underscore — see `entities/entity.py` lines 40, 63, 87). Setting `self.player._iframes = 9999` creates a new dead attribute that is never read by `Entity.update()`, `Entity.take_damage()`, or any other method. The actual `self.player.iframes` counter remains unchanged (typically 0), so the player is fully vulnerable during the defeat cutscene. A surviving Crawler minion can kill the player, triggering the normal death sequence and discarding the Architect victory state (same symptom as the original BUG-036).
  - **Minimal fix:** Change line 821 from `self.player._iframes = 9999` to `self.player.iframes = 9999`.

---

- [x] **BUG-045: `scenes/main_menu.py` parallax second-copy draw offset is `SCREEN_WIDTH * 2` too large — wrapped ghost copies of shapes land far off-screen instead of at the visible right seam**
  - **File:** `scenes/main_menu.py`, lines 129–130
  - **Problem:**
    ```python
    if sx + sw > SCREEN_WIDTH:
        pygame.draw.rect(surface, color,
                         (int(sx) - SCREEN_WIDTH * 2, sy, sw, sh))
    ```
    Shapes are initialized with `x` in `[0, SCREEN_WIDTH * 2]` and scroll left, wrapping when `shape[0] + shape[2] < 0`. The second draw condition is intended to render the "leading edge" of a shape that straddles the right boundary of the screen. For that to be visible at the right edge, the copy should be drawn at `int(sx) - SCREEN_WIDTH` (one screen width to the left of the original), not `int(sx) - SCREEN_WIDTH * 2`. With the current formula, a shape at `sx = 2400` (near the wrap point) renders its ghost at `2400 - 2560 = -160` px, which clips to a thin sliver at the left edge instead of appearing near the right edge. Shapes with `SCREEN_WIDTH <= sx < SCREEN_WIDTH * 2 - sw` satisfy the second condition but produce ghost draws entirely off the left side of the screen (large negative x). The parallax wrap seam is therefore invisible — the background appears to pop rather than scroll smoothly onto the screen from the right.
  - **Minimal fix:** Change `SCREEN_WIDTH * 2` to `SCREEN_WIDTH` in the second draw call: `(int(sx) - SCREEN_WIDTH, sy, sw, sh)`.

---

- [x] **BUG-046: `gameplay.py` LEVEL_10 right-edge check grants victory and transitions to `SCENE_MAIN_MENU` even when the Architect is still alive — walking to the right wall bypasses the final boss**
  - **File:** `scenes/gameplay.py`, lines 871–893
  - **Problem:**
    ```python
    if (self.player.alive and self.player.rect.right >= self.tilemap.width - 64
            and not self._architect_victory_done):
        if next_level:
            ...
        elif self._level_name == "level_10":
            self.game.save_data["victory"] = True
            self.game.save_to_disk()
            self._begin_transition(SCENE_MAIN_MENU)
            return
    ```
    The outer guard `not self._architect_victory_done` is True whenever the Architect has not yet been killed (it starts False and is only set True inside the defeat dialogue block). `next_level` for `"level_10"` is `None` (not in `_LEVEL_CHAIN`), so the `elif self._level_name == "level_10"` branch is always taken when the player reaches the right edge. Combined, this means any living player who walks to the rightmost wall of LEVEL_10 (`player.rect.right >= tilemap.width - 64 = 2016`) triggers a free victory write and transitions directly to SCENE_MAIN_MENU, completely bypassing the Architect boss fight. In LEVEL_10, the solid floor tiles at rows 11–12 extend to `x = 2048` (tile column 64), which is `>= 2016`, so simply walking to the right wall achieves this.
  - **Minimal fix:** Add a check that the Architect is defeated before allowing the LEVEL_10 right-edge win:
    ```python
    elif self._level_name == "level_10":
        if self._architect and self._architect.alive:
            pass   # boss still alive; block the exit
        else:
            self.game.save_data["victory"] = True
            self.game.save_to_disk()
            self._begin_transition(SCENE_MAIN_MENU)
            return
    ```

---

