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

---

# Hollow Knight Feel Review — Phase 2-1 Enemy Types

_Evaluated 2026-04-18. Focus: ShieldGuard, Ranged, Jumper — combat feel and enemy variety for levels 6–8._

---

## 1. ShieldGuard — Frontal Block Mechanics

### Current state

`SHIELD_GUARD_DEFENSE = 0.35` in `settings.py` (line 150) means the shield absorbs 65% of frontal damage — the guard takes 35% through the shield. `SHIELD_GUARD_HP = 80` and `SHIELD_GUARD_SPEED = 1.2` (`settings.py` lines 147–149).

The facing logic in `shield_guard.py` lines 41–45 updates `self.facing` every AI frame to always point at the player, then calls `super()._update_ai(player)`. This means the ShieldGuard perpetually faces the player — the shield is always between the guard and the player regardless of the player's movement. There is no window during which the player can naturally get behind it through horizontal repositioning alone.

### Gap vs. HK (Baldurs)

HK's Baldurs are full-100% frontal blocks — they bounce the nail off completely and deal contact damage if struck from the front. The player is forced to use Desolate Dive, wait for the Baldur's opening animation, or strike from behind. The 100% block is not more punishing than 65% — it is actually cleaner *design* because it creates an unambiguous binary: "you cannot deal damage this way, find another angle." The current 65% partial block is a middle ground that teaches neither rule clearly. Players can brute-force the guard by tanking the shield and dealing reduced damage rather than adapting tactically.

The always-facing behavior in `_update_ai` is the deeper problem. The guard should update its facing only when certain conditions are met (e.g. it begins a charge), giving the player a brief window during patrol state to attack from the rear.

### Recommended changes

```python
# settings.py
SHIELD_GUARD_DEFENSE   = 0.0    # was 0.35 — full frontal block (0 damage through shield)
SHIELD_GUARD_HP        = 65     # was 80 — reduce HP to compensate for 100% block;
                                #   circumventing the shield is now the expected route
SHIELD_GUARD_SPEED     = 1.6    # was 1.2 — slightly faster chase so it closes distance
                                #   and punishes players who try to kite in a straight line
```

In `shield_guard.py` line 41–45, replace the always-facing logic:

```python
# Current (always faces player — blocks every attack):
def _update_ai(self, player) -> None:
    if player.rect.centerx > self.rect.centerx:
        self.facing = 1
    else:
        self.facing = -1
    super()._update_ai(player)

# Recommended (only face player while in CHASE or ATTACK; patrol facing follows patrol_dir):
def _update_ai(self, player) -> None:
    super()._update_ai(player)          # sets self._state
    if self._state in (_CHASE, _ATTACK):
        self.facing = 1 if player.rect.centerx > self.rect.centerx else -1
    # During _PATROL, facing follows _patrol_dir naturally via _do_patrol
```

This creates the tactical opening: sprint behind the guard while it is patrolling → attack from rear → guard turns → reposition. Mirrors the Baldur dynamic cleanly.

**Justification**: HK's shield enemies are iconic precisely because they enforce a rule with no exception. A 65% partial block creates an incentive to just attack the front — it is a damage-sponge, not a puzzle.

---

## 2. Ranged — Projectile Pressure and Movement

### Current state

`RANGED_ATTACK_COOLDOWN = 90` frames (`settings.py` line 158) — one shot every 1.5 seconds at 60 FPS. `RANGED_PROJ_SPEED = 5` px/frame (line 157). The preferred standoff distance is hardcoded at `_PREFERRED_DIST = 220` in `ranged.py` line 18. Projectiles travel in a flat horizontal line (`vx` only, `vy = 0`).

### Gap vs. HK (Husk Sentries / Vengeflies)

HK's ranged units create pressure through two mechanisms: (a) **volume** — shot frequency is high enough that standing still is not viable, and (b) **coverage area** — projectiles arc, fan, or home slightly, so the player cannot simply stand above or below the sentry. The current `RANGED_ATTACK_COOLDOWN = 90` is too long. At 1.5 s between shots on a flat trajectory, the player can comfortably stand at a vertical offset from the Ranged enemy (on a platform above or below) and attack it freely while the projectiles sail past horizontally. The enemy creates zero pressure unless the player is at the exact same Y.

The `_PREFERRED_DIST = 220` hardcode (line 18, `ranged.py`) belongs in `settings.py` for tuning visibility.

### Recommended changes

```python
# settings.py
RANGED_ATTACK_COOLDOWN  = 55     # was 90 — ~0.9 s between shots; forces player movement
RANGED_PROJ_SPEED       = 6      # was 5 — faster projectile closes reaction window
RANGED_PREFERRED_DIST   = 240    # NEW — move the hardcode out of ranged.py for tuning
```

Replace the hardcode in `ranged.py` line 18:
```python
# was:
_PREFERRED_DIST = 220
# becomes:
from settings import RANGED_PREFERRED_DIST
_PREFERRED_DIST = RANGED_PREFERRED_DIST
```

Add a slight vertical velocity component to `_fire()` in `ranged.py` line 94–98 so projectiles arc toward the player's current Y:

```python
def _fire(self, player) -> None:
    vx = RANGED_PROJ_SPEED * self.facing
    # Mild arc: calculate vy so the bolt reaches player's Y after ~40 frames of travel
    dist_x = abs(player.rect.centerx - self.rect.centerx)
    travel_frames = max(1, dist_x / RANGED_PROJ_SPEED)
    raw_vy = (player.rect.centery - self.rect.centery) / travel_frames
    vy = max(-4.0, min(4.0, raw_vy))   # clamp to ±4 px/frame — no homing, just a lob
    cx = self.rect.right if self.facing == 1 else self.rect.left - 10
    cy = self.rect.centery - 4
    self.projectiles.append(Projectile(cx, cy, vx, RANGED_DAMAGE, self, vy=vy))
```

The `Projectile` class (`ranged.py` lines 22–43) also needs `vy` added and applied each frame. Its `update` method should apply gravity lightly (`vy += 0.15` per frame, same mild arc as HK bolts) and update `self.rect.y` accordingly.

**Justification**: At 90-frame cooldown with a flat projectile, vertical platform positioning trivially defeats the Ranged enemy. At 55-frame cooldown with mild arc, the player is forced to keep moving and cannot camp a ledge — matching HK's "ranged enemies deny safe zones" principle.

---

## 3. Jumper — Erraticism and Urgency

### Current state

`JUMPER_JUMP_COOLDOWN = 55` frames (`settings.py` line 168) — one hop every ~0.92 seconds while chasing. `JUMPER_JUMP_FORCE = -11` (line 167). `JUMPER_SPEED = 2.0` (line 165). The jump direction is always directly toward the player (`_do_chase_jump`, `ranged.py` line 68–75): `direction = 1 if player ... else -1` — purely horizontal targeting with no vertical arc variation.

### Gap vs. HK (Aspid Hunters)

HK's Aspids jump in rapid bursts (2–3 fast hops in quick succession) separated by a brief landing pause. Their trajectory angles vary because their launch force has a fixed magnitude that produces a fixed-angle parabola at player-direction — unpredictable when the player is above or at an angle. The Jumper has two problems: (1) `JUMPER_JUMP_COOLDOWN = 55` is long enough that the player can attack during every landing window — the Jumper is easily readable and exploitable. (2) The patrol auto-jump in `_do_patrol_jump` (lines 56–66) fires on the same `JUMPER_JUMP_COOLDOWN` timer, so patrol and chase behavior are in lockstep — no burst pattern.

There is also a subtle bug adjacent to feel: `_jump_timer` is only reset (`self._jump_timer = 0`) in `_do_patrol_jump` but not in `_do_chase_jump`. This means if the enemy transitions from patrol to chase with a nearly-full timer, the first chase jump fires immediately — accidental but actually desirable. However the cooldown (`_jump_cooldown`) used in chase and the timer (`_jump_timer`) used in patrol are two different counters tracking the same concept (time between jumps) with different reset logic — a maintenance hazard.

### Recommended changes

```python
# settings.py
JUMPER_JUMP_COOLDOWN = 32     # was 55 — ~0.53 s; creates urgency, harder to exploit landing
JUMPER_JUMP_FORCE    = -12    # was -11 — slightly higher hop, harder to hit mid-air
JUMPER_SPEED         = 2.4    # was 2.0 — faster horizontal component matches more aggressive cadence
```

To create burst-hop behavior (2 rapid hops then a pause), add `JUMPER_BURST_COUNT = 2` and `JUMPER_BURST_PAUSE = 70` to `settings.py`, then track a burst counter in `Jumper.__init__`:

```python
# In Jumper.__init__ (jumper.py):
self._burst_remaining = 0
self._burst_pause     = 0
```

In `_do_chase_jump`, implement the burst:
```python
def _do_chase_jump(self, player) -> None:
    direction = 1 if player.rect.centerx > self.rect.centerx else -1
    self.vx     = direction * JUMPER_SPEED * 1.3
    self.facing = direction
    if self._burst_pause > 0:
        self._burst_pause -= 1
        return
    if self.on_ground and self._jump_cooldown <= 0:
        self.vy             = JUMPER_JUMP_FORCE
        self._jump_cooldown = JUMPER_JUMP_COOLDOWN
        self._burst_remaining -= 1
        if self._burst_remaining <= 0:
            self._burst_remaining = JUMPER_BURST_COUNT   # reset
            self._burst_pause     = JUMPER_BURST_PAUSE   # long pause after burst
```

**Justification**: At 55-frame cooldown, the Jumper's rhythm is regular and the landing window is easily read. At 32-frame cooldown in 2-hop bursts, the player must dodge two fast hops then capitalize on the longer inter-burst pause — matching HK's Aspid read-react dynamic. The longer pause also gives a clear reward window for well-timed players.

---

## 4. Enemy Variety Mixing — Levels 6–8 Combinations

HK's room design principle: each room selects 2–3 enemy types whose individual weaknesses become each other's strengths, creating emergent difficulty without either type alone being overwhelming.

### Recommended pairings

**Combination A: ShieldGuard + Jumper (L6 — introduce the mechanic)**

ShieldGuard forces the player to reposition to attack from the rear. Jumper punishes repositioning by jumping unpredictably into the player's intended path. The player cannot simply sprint past the ShieldGuard because the Jumper is airborne. This pairing teaches the block-and-reposition mechanic under light pressure before adding projectiles.
- Room width: 18–22 tiles so the player has room to circle but not enough to safely kite both.
- Spawn: ShieldGuard center, Jumper on a raised platform to one side so it approaches from above.

**Combination B: Ranged + Jumper (L7 — pressure from two axes)**

Ranged denies horizontal safe zones, Jumper denies vertical ones. The player must engage the Jumper at melee range while arcing shots from the Ranged approach. Works because both enemies are relatively fragile (40 HP and 35 HP respectively per `settings.py` lines 154 and 163) — the player can eliminate one quickly. Keeps urgency high throughout.
- Place Ranged on an elevated ledge so its arc shots drop down onto the player level — maximizes the value of the vy arc fix recommended above.

**Combination C: ShieldGuard + Ranged (L8 — high-pressure composition)**

ShieldGuard demands close-range flanking. Ranged enemy punishes the player for the lateral movement needed to flank. The player must time their repositioning sprint to coincide with the Ranged enemy's cooldown window. This is the highest-skill combination — save for L8.
- Do not add a Jumper to this combination; three enemy types simultaneously overwhelms the available reading bandwidth in a 2D platformer. Two synergistic enemies at high tuning values is sufficient.

**General placement principle** (all rooms L6–8): include at least one elevated platform (2–3 tiles high) per room. All three Phase 2-1 enemies are designed for flat-ground encounters but HK's rooms create vertical mixing. Platforms give Jumpers a landing target, give Ranged a firing perch, and give the player a dodge axis that is not purely horizontal.

---

## 5. Remaining Movement and Combat Gaps (not addressed in 2026-04-12 pass)

### 5a. ShieldGuard touch-damage knockback direction

`shield_guard.py` never calls `player.take_damage(..., knockback_dir=...)`. The previous pass noted (REVIEW_HK.md Pillar 4, "What remains") that callers in enemy files need to pass `knockback_dir` explicitly. ShieldGuard, Ranged, and Jumper all go through `AttackHitbox._apply_hit` (combat.py line 55–65) which does apply `target.vx` and `target.vy` from its own knockback fields. This is fine for hitbox-based attacks. However if any of these enemies deal touch damage (body contact via solid collision, not `AttackHitbox`), the `knockback_dir` gap still applies. Flag for build-agent to audit the `gameplay.py` projectile-player collision handler (noted in the Ranged docstring: "gameplay.py is responsible for checking projectile-player collisions") — verify it calls `player.take_damage(proj.damage, knockback_dir=...)` with correct direction.

### 5b. Ranged projectile has no vy field — flat trajectories only

`Projectile.__init__` in `ranged.py` line 24 accepts only `vx`. Adding `vy` (recommended above in section 2) requires the constructor signature change and `update()` to apply it. This is a straightforward extension; flag for build-agent.

### 5c. ShieldGuard attack hitbox knockback values

`shield_guard.py` line 71: `knockback_x=4.5, knockback_y=-2.0`. Compare to the base enemy `knockback_x=3.5, knockback_y=-2.5` (enemy.py line 122). The ShieldGuard's shield bash should carry higher vertical arc — it is a heavy upward shove from a bulk enemy, per HK's shell-shielded enemies. Recommend `knockback_y=-3.5` to send the player upward and create a clear landing-recovery window after each ShieldGuard strike.

```python
# settings.py (new constant)
SHIELD_GUARD_KNOCKBACK_Y = -3.5   # was hardcoded -2.0 in shield_guard.py line 71
```

### 5d. Jumper attack hitbox — downward spike when jumping

`jumper.py` line 89–91: when the Jumper attacks mid-air, it uses the same flat `knockback_y=-4.5` regardless of relative vertical position. HK's Aspids deal an angled knockback that reflects their attack angle. For the Jumper, if it attacks while airborne (`not self.on_ground`) and the player is below it, recommend `knockback_y = +2.0` (downward spike — player gets slammed down, not bounced up). This makes Jumper feel more physically coherent and creates a distinct "caught from above" damage pattern that the player learns to read.

```python
# settings.py (new constants)
JUMPER_KNOCKBACK_Y_GROUND  = -4.5   # was hardcoded — upward bounce when hit at ground level
JUMPER_KNOCKBACK_Y_AERIAL  =  2.0   # NEW — downward spike when Jumper attacks from above
```

### 5e. ENEMY_IFRAMES interaction with Jumper burst

`ENEMY_IFRAMES = 10` (settings.py line 67). At `JUMPER_JUMP_COOLDOWN = 32` (recommended), the Jumper's burst lands two hops ~32 frames apart. If the player hits the Jumper mid-first-hop, the 10-frame iframe window expires long before the second hop — the player can get two swings per burst window. This is correct and desirable (matching HK's reward for precise timing on fast enemies). No change needed; noted for confirmation.

---

## Summary Table (2026-04-18 additions)

| Enemy / Area | Status | Key Gap | Recommended Action |
|---|---|---|---|
| ShieldGuard block | Gap | 65% partial block rewards brute force | Set `SHIELD_GUARD_DEFENSE = 0.0`; reduce `SHIELD_GUARD_HP` to 65 |
| ShieldGuard facing | Gap | Always faces player — no rear-attack window | Restrict facing update to CHASE/ATTACK states only |
| Ranged cooldown | Gap | 90-frame cooldown creates no pressure | Reduce `RANGED_ATTACK_COOLDOWN` to 55 |
| Ranged projectile | Gap | Flat trajectory defeated by vertical positioning | Add `vy` arc component; move `_PREFERRED_DIST` to `settings.py` |
| Jumper frequency | Gap | 55-frame cooldown — rhythm predictable | Reduce `JUMPER_JUMP_COOLDOWN` to 32; add 2-hop burst pattern |
| Jumper direction | Gap | Always horizontal targeting — no arc variation | Burst/pause cadence adds apparent unpredictability |
| L6–8 room mixing | Gap | No guidance on combination design | Use A/B/C pairings above; add vertical platform per room |
| Touch knockback in projectiles | Gap | gameplay.py collision path may skip knockback_dir | Audit projectile-player collision handler |
| ShieldGuard knockback_y | Minor | -2.0 is weak for a bulk enemy | Raise to -3.5; extract to `SHIELD_GUARD_KNOCKBACK_Y` |
| Jumper aerial spike | Minor | Same knockback_y regardless of attack angle | Add `JUMPER_KNOCKBACK_Y_AERIAL = 2.0` for above-player attacks |
