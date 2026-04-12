# Hollow Knight Feel Review — Steamfall

_Evaluated 2026-04-12 against the Hollow Knight feel pillars._

---

## Pillar 1: Movement Weight

### Current state
- `PLAYER_SPEED = 5`: horizontal speed set directly on `vx` each frame — effectively instant top speed (no acceleration ramp). This is correct HK behaviour.
- `FRICTION = 0.78`: applied per-frame when no key is held. Gives a quick but not abrupt stop. HK's stop is marginally tighter (≈0.72–0.75).
- `GRAVITY = 0.6`: light gravity produces a slightly floaty feel. HK's gravity equivalent is roughly `0.85–1.0` pixels/frame².
- `PLAYER_JUMP_FORCE = -13`: produces a tall arc. HK's jump is snappier — roughly `-11` to `-12` paired with heavier gravity.
- Air control: no distinction in air vs. ground speed — player turns instantly mid-air at full speed. HK reduces air steering to ~70% of ground responsiveness.
- Landing squat: not present (would require an animation frame, deferred to art pass).

### Gap vs. HK
The primary gap is gravity feel. Increasing gravity while slightly reducing jump force would tighten the arc and remove floatiness without making platforming harder.

### What was implemented
Nothing structural (movement core is in good shape). Constants below are the recommended next step.

### What remains
- Landing squat (2-frame crouched sprite) — needs sprite asset.
- Air control reduction (apply `speed *= 0.7` when not on ground in `_handle_movement`).

### Recommended settings.py values
```python
GRAVITY           = 0.85   # was 0.6 — tighter arcs, less floaty
TERMINAL_VELOCITY = 20     # was 18 — matches heavier gravity
PLAYER_JUMP_FORCE = -12    # was -13 — shorter arc pairs with higher gravity
FRICTION          = 0.74   # was 0.78 — slightly snappier stop
```

---

## Pillar 2: Attack Commitment

### Current state before changes
- No recoil: `vx` was unchanged when attacking.
- No windup: hitbox was created the same frame Z was pressed.
- Speed was reduced to 55% during attack swing (good weight, but not HK-style).

### Gap vs. HK
HK nails feel impactful because (a) the Knight visibly snaps backward the instant the nail swings, and (b) there is a 3-frame window where the enemy can react and the player cannot cancel. Both were missing.

### What was implemented
1. **Attack recoil** (`ATTACK_RECOIL_VX = 1.5`): when Z is pressed, `self.vx = -self.facing * ATTACK_RECOIL_VX` is applied before any hitbox — the player nudges backward into the swing.
2. **Windup frames** (`WINDUP_FRAMES = 4`): pressing Z now sets `_windup_timer = 4`. The hitbox does not exist during this window. After 4 frames `_attack_timer` is set and the hitbox becomes active. This gives enemies (and the player) a beat to feel the telegraph.
3. **Windup visual**: a dim gold glow appears on the swing side during windup, brightening as it resolves — a zero-asset visual cue that reinforces the telegraph.

### What remains
- Horizontal position lock (preventing walking through the windup): currently the player can still move during windup. To add: set `vx = 0` and block movement key input while `_windup_timer > 0`. Requires a small change in `_handle_movement`.

---

## Pillar 3: Enemy Hit Reaction

### Current state
- `_apply_hit()` in `systems/combat.py` applies both `vx` and `vy` (directional arc) — correct.
- Hitstop is triggered for 4 frames on every hit — correct.
- iframes flash: the entity flickers white every 4 frames during iframes — close to HK's 2-frame snap, but readable.

### Gap vs. HK
HK snaps the enemy to a saturated lighter color for exactly 2 frames, then returns to normal. The current implementation uses a white flicker every 4 frames which is more subtle. For enemies (not player), this could be tightened to a 2-frame pulse (`iframes % 4 < 2` → `iframes % 4 < 2` is already that cadence — acceptable).

### What was implemented
No changes needed here — the arc knockback and hitstop are already in place and work correctly.

### What remains
- Enemy-specific hit flash color (e.g. bright orange/white for 2 frames) rather than the same white used for player iframes. Implement in `entities/enemy.py` draw override.

---

## Pillar 4: Death and Damage Feel

### Current state before changes
- No involuntary knockback on touch damage (crawler body contact).
- No screen feedback when the player is hit.
- Death triggers a 2.5-second "you perished" overlay and respawns at checkpoint — correct HK behaviour.

### Gap vs. HK
Touch damage from crawlers had no velocity response — the player could stand inside a crawler and take a series of hits with no physical consequence. HK always bounces the Knight on any damage source.

### What was implemented
1. **`take_damage(amount, knockback_dir=0)`** in `entity.py`: optional `knockback_dir` parameter. When non-zero, applies `vx = knockback_dir * TOUCH_KNOCKBACK_VX` (4.5 px/frame) and `vy = TOUCH_KNOCKBACK_VY` (-3.0). Weapon hitboxes continue to apply their own knockback after calling `take_damage`, so there is no double-apply.
2. **Damage vignette** in `gameplay.py`: tracks `_prev_iframes` and `_damage_flash`. When the player's iframes transition from 0 → positive (new hit), `_damage_flash = DAMAGE_FLASH_FRAMES` (20). Each frame `_draw_damage_vignette()` draws four red border rectangles (60 px thick, alpha fading from 160 → 0 over 20 frames) around the screen edges — no full overlay, just a border pulse.

### What remains
- Callers of `take_damage()` on the player from touch sources (e.g. `Crawler.update()` or similar) need to pass `knockback_dir` explicitly (e.g. `player.take_damage(amount, knockback_dir=-player.facing)` or computed from relative positions). Deferred because `entities/enemy.py` and `entities/crawler.py` are build-agent territory.
- Soul loss on death (HK sheds soul at death location as collectibles) — not yet implemented; would be a good addition once the fragment system is more complete.

---

## Pillar 5: Environmental Feedback

### Current state
- No landing dust particles.
- No spark particles on wall attacks.
- No camera pan on room entry.
- Camera follows player each frame (smooth, no pan).

### Gap vs. HK
HK's particle system is central to its tactile feel. Every significant physical event (landing after a fall, nail sparks on walls, spell bursts) emits particles. Steamfall currently has none.

### What was implemented
Nothing — particle system requires new infrastructure (`systems/particles.py`, emitter management in `gameplay.py`) and is too large to add safely in a single isolated pass.

### What remains (recommended next pass)
1. **Landing dust**: track `prev_vy` on player. If `prev_vy > 8` (hard landing) and `on_ground` just became True, emit 6–8 short-lived dust sprites from the player's feet. Particles live 8–12 frames, drift outward, fade alpha.
2. **Nail sparks on wall hit**: in `move_and_collide`, when a horizontal collision occurs and player is attacking, emit 4–6 spark particles.
3. **Camera pan on level entry**: briefly offset camera by `(±120, 0)` at scene start and ease it to center over 30 frames using `lerp`.

---

## Summary Table

| Pillar | Status | Implemented Here | Remaining |
|---|---|---|---|
| Movement weight | Partial | — | Heavier gravity, air control reduction, landing squat sprite |
| Attack commitment | Done | Recoil, windup frames, windup glow | Movement lock during windup |
| Enemy hit reaction | Good | — | Enemy-specific 2-frame flash color |
| Death / damage feel | Done | Damage vignette, touch knockback API | Caller-side knockback_dir wiring in enemy files |
| Environmental feedback | Gap | — | Full particle system pass |
