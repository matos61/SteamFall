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
