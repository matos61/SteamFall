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
