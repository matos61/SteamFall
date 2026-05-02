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

---

# HK Feel Review — Phase 2 Content (2026-04-21)

_Focus: Architect boss (P2-4), upgrade balance (P2-5), LEVEL_9/10 arenas, Soul Surge / Overdrive feel, and drop rewards (P2-6)._

---

## 1. Architect Boss (P2-4) — 4-Phase Climax Feel

The 4-phase escalation is structurally sound: colour shifts (deep violet → blood-red), a phase-4 rage flash (`_rage_flash_timer = 30`), and cumulative ability stacking all reinforce the sense of a boss deteriorating under pressure. However, the teleport telegraph is weak. `_teleport_cd = ARCHITECT_TELEPORT_CD` (200 frames, `settings.py` line 201) counts down between teleports, but the only pre-teleport signal is `_rage_flash_timer = 15` — a 15-frame red tint that is already in heavy use for phase transitions and is not visually distinct from ongoing combat noise. In HK, teleports are preceded by a dedicated 20-30 frame dissolve animation that is visually unambiguous. Recommend adding a dedicated `_teleport_wind_timer` constant — suggested `ARCHITECT_TELEPORT_WARN = 20` — during which the Architect is locked in place and a distinct colour pulse fires, before the actual position jump. Additionally `ARCHITECT_TELEPORT_CD = 200` is generous (~3.3 s at 60 FPS): reducing to `140` would increase urgency at phase 2 without overwhelming the player alongside the fan spread that activates at phase 3. The Crawler minion spawns at `ARCHITECT_MINION_CD = 300` (5 s) are infrequent enough that they risk feeling like background noise rather than genuine pressure; reducing to `210` and capping simultaneous live Crawlers at 2 would create threat without cluttering the arena.

```python
# settings.py — recommended changes
ARCHITECT_TELEPORT_CD   = 140   # was 200 — tighter cadence once phase 2 starts
ARCHITECT_TELEPORT_WARN = 20    # NEW — dedicated pre-teleport warning frames (lock + distinct flash)
ARCHITECT_MINION_CD     = 210   # was 300 — more frequent spawns create real pressure
```

---

## 2. Upgrade Balance (P2-5)

At player base HP of `PLAYER_MAX_HEALTH = 100`, `UPGRADE_HP_BONUS = 25` is a 25% increase per selection — meaningful at every stage. Against the Architect (`ARCHITECT_MAX_HEALTH = 600`), the player is expected to take multiple hits, so extra HP has high practical value. `UPGRADE_DMG_BONUS = 5` is the least impactful: player base `ATTACK_DAMAGE` is 20 (hardcoded in `player.py` line 35), so +5 is a 25% damage increase per upgrade, which sounds comparable to HP — but because damage is applied per swing and the player can swing multiple times per encounter, the actual time-to-kill improvement compounds, making DMG upgrades quietly stronger than HP in skilled hands. `UPGRADE_RES_BONUS = 20` against `PLAYER_MAX_SOUL / PLAYER_MAX_HEAT` needs calibration context; without the base value visible in this block, the ratio is opaque. The core imbalance is that DMG bonus is additive with Overdrive's 1.3× multiplier (`player.py` line 277), meaning at 2 DMG upgrades the player deals `(20+10)*1.3 = 39` — nearly doubling base damage in Overdrive. This compounds sharply and should be capped or made multiplicative before factoring Overdrive. Recommend raising `UPGRADE_DMG_BONUS` slightly to 6 for feel while making it pre-Overdrive only (apply bonus to base before the multiplier, which it already does — keep that), and consider adding a constant `UPGRADE_DMG_MAX_STACKS = 3` to limit runaway scaling.

```python
# settings.py — recommended changes
UPGRADE_DMG_BONUS  = 6          # was 5 — marginally more noticeable per swing
UPGRADE_HP_BONUS   = 25         # keep — 25% base HP per selection is well-calibrated
UPGRADE_RES_BONUS  = 20         # keep pending base-resource audit; add UPGRADE_RES_MAX_STACKS = 3
```

---

## 3. LEVEL_9 and LEVEL_10 Arena Layout

LEVEL_9 ("The Convergence") is well-constructed for a gauntlet: three distinct platform strata, scattered enemies across types (`G`, `J`, `c`, `C`, `R`), and a floor-level checkpoint `P` at the far right. The `################` mid-left platform on row 10 creates a natural defensive high ground, and enemy placement is offset so no single attack covers multiple threats. LEVEL_10 ("The Final Approach") opens cleanly with only a few weak enemies before the Architect (`X`) spawns at row 10, column 45. The bottom two rows of solid floor give stable footing, and the absence of mid-arena platforms is good design for a dash/teleport boss — the Architect can freely move horizontally. However there is a potential issue: the `#########` platforms at rows 6 (cols 6–14) and (cols 49–57) are each 9-tile wide ledges with no gaps. The Architect's fan spread fires 5 projectiles at `vy_offset` values of `-6, -3, 0, +3, +6` (`architect.py` line 155) — the uppermost two shots at `vy = -6` and `vy = -3` will arc upward steeply enough to clear any enemy standing on these ledges and hit a player hiding behind them. This is the intended design and works correctly. The only platform concern is the `################` platform at row 9 (cols 3–18): it sits one row above the floor and extends 16 tiles, which is long enough that the Architect's teleport destination range (`arena_min = TILE_SIZE*4` to `arena_max = SCREEN_WIDTH - TILE_SIZE*4`) may occasionally drop the Architect on top of this platform rather than floor level, since `rect.centerx` is repositioned but `rect.y` is unchanged during the teleport (`architect.py` line 135–137). Recommend verifying that this platform does not exist in the final LEVEL_10 layout or that the teleport logic clamps the Architect to floor Y after the position change.

---

## 4. Soul Surge / Overdrive Feel

Soul Surge fires four `80×80` px hitboxes (`player.py` line 318) centered 20 px offset from the player in each cardinal direction, each dealing 35 damage with a 12-frame duration. The AOE size of 80 px is generous — approximately 2.7 tiles — and will reliably catch the Architect at close range. The 35 damage against Architect's 600 HP represents a 5.8% chunk per activation, which is noticeable but not game-breaking. The `_ability_cooldown = 90` (1.5 s) is responsive enough to fire multiple times per phase. Overdrive gives 3 seconds (`_ability_timer = 180`) of `speed * 1.6` and `damage * 1.3` with `_ability_cooldown = 240` (4 s between uses). The 3 s duration feels rewarding — long enough to land 4–5 attacks and notice the speed boost. `UPGRADE_RES_BONUS = 20` only increases the maximum resource pool, not the regen rate (passive regen is `0.05/frame` regardless of pool size — `player.py` line 192). This means a larger pool provides more stored uses rather than faster recharge, which is the correct tradeoff for a capstone ability. The practical effect is approximately 1 additional Overdrive activation per full pool if bonus pushes the max above `ABILITY_COST * N` thresholds. This is low-key but meaningful; to make it feel more rewarding, consider adding `UPGRADE_RES_REGEN_BONUS = 0.008` (applied additively per upgrade to the 0.05 base regen) so resource upgrades visibly speed up the refill bar.

```python
# settings.py — recommended addition
UPGRADE_RES_REGEN_BONUS = 0.008   # NEW — per-upgrade passive regen boost; +0.008/frame per stack
```

---

## 5. Drop Rewards (P2-6)

`HEAT_CORE_HEAL = 8` and `SOUL_SHARD_HEAL = 8` both heal 8 HP against a player pool of 100–125 HP (base + up to 3 HP upgrades at `UPGRADE_HP_BONUS = 25` = 175 max, but realistically 100–125 at standard play). An 8 HP heal is 6.4–8% of base HP — equivalent to a Soul Vessel in HK restoring roughly 11% per mask depending on max masks. This ratio is slightly below HK's floor but within acceptable range for a drop that can come from standard enemies. The more material issue is perception: 8 HP against the Architect's melee damage of `ENEMY_ATTACK_DAMAGE` (sourced from `settings.py`) may represent only 1–2 hits of buffer. If `ENEMY_ATTACK_DAMAGE` is in the 18–20 range (as implied by boss projectile damage being `ENEMY_ATTACK_DAMAGE * 0.8` per `boss.py` line 234), 8 HP is less than half a hit — too small to feel impactful as a mid-boss-fight pickup. Recommend raising both heals to 12 HP for faction drops, which sits at ~10% of base HP and matches HK's single-mask restoration. The Architect's boss drop of 3 `SoulFragment`s (spaced at `cx-20`, `cx`, `cx+20` — `boss.py` lines 251–255) is a solid reward moment. Three fragments spread across 40 px will be clearly visible and collectible without overlapping. The narrative weight of the drop is appropriate for a final boss. No change needed to the fragment count, but consider separating them more (`cx-40`, `cx`, `cx+40`) so they do not stack under the Architect corpse.

```python
# settings.py — recommended changes
HEAT_CORE_HEAL  = 12   # was 8 — ~10% base HP; feels impactful against boss-level damage
SOUL_SHARD_HEAL = 12   # was 8 — match Marked/Fleshforged heal parity
```

---

## Summary Table (2026-04-21)

| Topic | Status | Key Issue | Recommended Change |
|---|---|---|---|
| Architect teleport telegraph | Gap | 15-frame rage flash reuses existing effect — not readable as a teleport warn | Add `ARCHITECT_TELEPORT_WARN = 20`; lock Architect and fire distinct pulse pre-teleport |
| Architect teleport cadence | Gap | `ARCHITECT_TELEPORT_CD = 200` is too slow at phase 2 | Reduce to `140` |
| Crawler minion spawns | Gap | `ARCHITECT_MINION_CD = 300` — too infrequent, feel like noise | Reduce to `210`; cap simultaneous live Crawlers at 2 |
| Upgrade balance — DMG | Minor | `UPGRADE_DMG_BONUS = 5` compounds with 1.3× Overdrive; runaway at 2+ stacks | Raise to `6`; add `UPGRADE_DMG_MAX_STACKS = 3` cap |
| Upgrade balance — RES | Minor | `UPGRADE_RES_BONUS = 20` only widens pool, not regen | Add `UPGRADE_RES_REGEN_BONUS = 0.008` per stack |
| LEVEL_10 Architect teleport Y | Gap | Teleport repositions only `centerx`; long platform at row 9 may catch Architect mid-platform | Verify no platform at row 9 cols 3–18 or clamp teleport to floor Y |
| Soul Surge AOE | Good | 80×80 px, 35 dmg, 12-frame duration — well-calibrated | No change |
| Overdrive duration | Good | 180 frames (3 s), 1.3× speed+dmg — rewarding and fair | No change |
| Resource upgrade feel | Minor | Pool increase alone feels passive | Add per-upgrade regen bonus constant |
| Faction heal drops | Gap | 8 HP heal is less than half a hit of boss damage — not impactful | Raise `HEAT_CORE_HEAL` and `SOUL_SHARD_HEAL` to `12` |
| Boss SoulFragment drop | Good | 3 fragments, spread 40 px — clear reward moment | Consider widening spread to 80 px (`cx±40`) to avoid stacking |

---

# HK Feel Review — Phase 3 Story Integration (2026-04-25)

_Focus: ending scene pacing, lore item display, NPC interaction feedback, mid-game cutscene trigger, faction tint intensity._

---

## 1. Ending Scene Pacing

**Files:** `scenes/marked_ending.py` lines 17–41; `scenes/fleshforged_ending.py` lines 17–41.

Both endings use exactly 8 beats. The beat list is player-advanced (SPACE/RETURN) with no auto-timer, which is the correct approach — HK's own ending slides (e.g. the Pure Vessel / Hollow Knight endings) are player-paced. The structural concern is **quantity and internal rhythm, not the advance mechanic**.

Eight beats is two too many for this register. HK endings peak at 5–6 title cards for their darkest routes (e.g. the Grimm Troupe banishment, the Dream No More sequence). Both Steamfall endings contain two consecutive "Narrator" beats that carry the same emotional register — the Marked path at beats 4–5 ("The city does not forget..." / "You do not return...") and the Fleshforged path at beats 5–6 ("The augments remember..." / "The Foundry rebuilds...") — which read as padding. The final `"???"` beat ("The cycle endures.") is the correct punctuation mark; its power is diluted by the two preceding beats drawing out the same theme.

Additionally, the background colour interpolation speed (`spd = 0.07` per frame — `marked_ending.py` line 108, `fleshforged_ending.py` line 108) means the colour lerp lags behind the beat advance by roughly 60–90 frames when a player advances quickly. On a fast read-through the background is still transitioning from beat 3's colour when beat 5 is already on screen — the tonal shift that the background colours are intended to provide is lost. HK's equivalent effect (screen colour fades) are beat-synchronous, not async.

**Recommended changes:**

- Collapse each pair of same-register Narrator beats into one line. For Marked: merge beats index 4 and 5 into `"The city does not forget its debts. You do not return to the mines — the ink does not allow it."` (6 beats total). For Fleshforged: merge beats index 4 and 5 into `"The augments remember her work. The Foundry does not sleep."` (6 beats total). This removes the padding without losing any narrative content.
- Raise `spd` from `0.07` to `0.18` in both ending files (lines 108) so the background colour change resolves within ~18 frames of a beat load — beat-synchronous in practice. At 0.07 it takes ~100 frames (1.7 s) to reach 50% of the target, which outlasts a fast reader's time on any single beat.

---

## 2. Lore Item Display

**File:** `settings.py` line 248; `scenes/gameplay.py` lines 663–669.

```python
LORE_DISPLAY_FRAMES = 300   # 5 seconds at 60 FPS
```

The auto-dismiss timer of 5 seconds is fundamentally the wrong model for lore text in a HK-inspired game. In Hollow Knight, lore tablets stay on screen until the player presses the interact button to dismiss them — the player is never interrupted by an auto-dismiss. The current implementation in `gameplay.py` lines 663–664 sets `self._lore_timer = LORE_DISPLAY_FRAMES` on collect and counts it down at line 669; gameplay continues during this countdown (the player keeps moving while the text is displayed). This means:

1. A player who collects a lore item mid-combat will have the text disappear from their peripheral vision before they have had a chance to read it.
2. A slow reader on longer entries (e.g. `'YIELD PER SOUL: 0.04 KW-hr...'` or the Architect's note — both in `_LORE_TEXT` at `gameplay.py` lines 99–113) has 5 seconds of on-screen time while also fighting enemies, which is insufficient for deliberate reading.

The current value of 300 frames is a reasonable floor if the timer model is kept, but the model itself conflicts with HK's "lore is a pause moment" philosophy. The LoreItem collect path at `collectible.py` lines 256–265 returns the text string; the display and dismiss logic is entirely in `gameplay.py` and can be changed without touching `collectible.py`.

**Recommended change:** Replace the frame-count auto-dismiss with a player-acknowledge model. In `gameplay.py`, when `self._lore_text` is set, also set a `self._lore_waiting_dismiss = True` flag and pause enemy AI updates (or at minimum halt the player's ability to pick up further items) until the player presses SPACE/RETURN to dismiss. If an auto-timer fallback is required for accessibility, raise `LORE_DISPLAY_FRAMES` from `300` to `480` (8 s) as the floor:

```python
# settings.py
LORE_DISPLAY_FRAMES = 480   # was 300 — 8 s floor; prefer player-dismiss model
```

---

## 3. NPC Interaction Feedback

**Files:** `settings.py` lines 240–242; `entities/npc.py` lines 40–44; `scenes/gameplay.py` lines 781–784.

```python
NPC_WIDTH         = 24    # settings.py line 240
NPC_INTERACT_DIST = 60    # settings.py line 242
```

The proximity check at `gameplay.py` line 784 is centre-to-centre horizontal distance only:

```python
dist = abs(self.player.rect.centerx - npc.rect.centerx)
npc._show_hint = dist < NPC_INTERACT_DIST
```

At `NPC_INTERACT_DIST = 60` px on a 24 px wide NPC sprite, the effective trigger radius extends 60 px from the NPC centre — approximately 2.5 sprite-widths to either side. This is generous and does not create a feel problem in isolation. The feel problem is elsewhere: the hint letter `"E"` (rendered bold monospace 14pt at `npc.py` line 41) snaps on and off with no transition. In HK, the interaction indicator (the glowing lore tablet symbol) fades in over ~10 frames when the player enters range. The snap-on `"E"` is jarring by contrast and gives no sense of "entering range" — it simply appears.

Additionally, the proximity check uses only the X axis (`centerx` delta) with no Y component. If an NPC is on a platform 80 px above the player, the hint will trigger when the player walks beneath it, which looks broken — the player has no way to interact from below but the `"E"` is showing. HK's interaction indicators are suppressed when the NPC is not on the same platform level.

The 60 px interaction distance itself is slightly tight relative to the 24-wide sprite for a player who approaches at a running pace (5 px/frame): the hint will have appeared only 12 frames before the player reaches the NPC edge at full speed. That is approximately 0.2 seconds — not enough time to register, stop, and press E before overshooting. A value of 80 px gives 0.33 s of lead time at full run, which is more readable.

**Recommended changes:**

- Raise `NPC_INTERACT_DIST` from `60` to `80` in `settings.py` line 242 to provide adequate hint lead time at full player speed.
- In `npc.py`, replace the instant alpha toggle with a frame counter: add `self._hint_alpha = 0` in `__init__`, ramp it toward 255 when `_show_hint` is True and toward 0 when False (`delta = 25` per frame gives a 10-frame fade). Render the `"E"` label through a surface with `set_alpha(self._hint_alpha)`.
- Extend the proximity check in `gameplay.py` to also gate on vertical proximity (`abs(player.rect.centery - npc.rect.centery) < NPC_HEIGHT * 2`) so off-platform NPCs do not falsely trigger the hint.

```python
# settings.py
NPC_INTERACT_DIST = 80   # was 60 — 0.33 s lead time at full sprint (5 px/frame)
```

---

## 4. Mid-Game Cutscene Trigger

**Files:** `scenes/gameplay.py` lines 806–819; `settings.py` lines 232–233; `scenes/marked_prologue.py` lines 143–157 (comment + beats 33–36); `scenes/fleshforged_prologue.py` lines 126–139 (comment + beats 30–33).

```python
# settings.py lines 232–233
MARKED_LORE_BEAT_START      = 33
FLESHFORGED_LORE_BEAT_START = 30

# gameplay.py lines 806–817
if self._level_name == "level_3":
    ...
    self._begin_transition(faction_scene, beat_start=beat, return_level="level_4")
```

The cutscene fires unconditionally when the player exits Level 3's right edge. This is the core design tension. In HK, mid-game lore is almost never triggered by a mandatory threshold crossing — it is unlocked by finding an optional NPC, acquiring a specific item, or entering an opt-in zone. The Dreamers' lore cutscenes, the White Lady dialogue, and the Seer sequences are all player-initiated. Forcing a cutscene on a level-exit is closer to a Metroidvania checkpoint interrupt, which breaks the exploratory feel.

The content of the cutscene (the Rune-Archivist and Sera's Datalog beats) is correctly characterised as "faction perspective lore" — it is expository, not an emotional climax. In HK, expository beats are delivered through NPCs or optional map areas, not through mandatory transition interrupts. Placing this same content in an optional zone within level 4 (a hidden room, or an NPC placed early in level 4 with `_NPC_DIALOGUE[("level_4", N)]`) would preserve the information while honouring player agency.

If the forced trigger is kept for Phase 3 (acceptable as a placeholder), the `return_level="level_4"` parameter at `gameplay.py` line 817 correctly returns the player to level 4 after the cutscene — the transition is not disorienting. However there is a secondary pacing issue: the Fleshforged mid-game beats (30–33 in `fleshforged_prologue.py`) include Sera's Datalog entries that use a bureaucratic, technical register (`"Soul energy is not mystical. It is thermodynamic..."`) — this reads well in isolation but immediately follows what is likely the player's most intense combat section (level 3 is a Foundry gauntlet). The tonal whiplash from intense combat to dry datalog is abrupt. The Marked equivalent (Rune-Archivist lines) shares the same beat register and the same pacing problem, though the more dramatic phrasing (`"The Architect was not built. It was summoned."`) lands harder.

**Recommended changes:**

- Preferred: convert the forced trigger to an optional trigger. Replace the `gameplay.py` lines 806–817 level-exit check with an NPC encounter placed at the beginning of level 4 (`_NPC_DIALOGUE[("level_4", 1)]`) that fires the same prologue scene when interacted with. This keeps the content accessible to all players without interrupting the exit flow.
- If the forced trigger is retained: add a 1-level delay — fire the cutscene on exit from level 4 instead of level 3, after the player has had a natural rest at the level 4 checkpoint. This eliminates the mid-combat tonal whiplash. Change `gameplay.py` line 808 from `"level_3"` to `"level_4"` and update `return_level` to `"level_5"`. Update `settings.py` comment at line 231 accordingly.

---

## 5. Faction Tint Intensity

**File:** `entities/enemy.py` lines 158–168.

```python
# enemy.py lines 158–166
# P3-2: 50/50 blend toward faction tint for themed levels
if self.faction_tint == FACTION_FLESHFORGED:
    tint = (160, 130, 100)
    color = tuple(int(a * 0.5 + b * 0.5)
                  for a, b in zip(base_color, tint))
elif self.faction_tint == FACTION_MARKED:
    tint = (100, 60, 160)
    color = tuple(int(a * 0.5 + b * 0.5)
                  for a, b in zip(base_color, tint))
```

The 50/50 blend is a readable midpoint on paper, but the tint colours chosen are low-saturation. Fleshforged tint `(160, 130, 100)` is a desaturated tan — blended 50/50 with a base enemy colour of e.g. `(140, 60, 60)` (a typical dark-red enemy) it produces `(150, 95, 80)`, a muddy brownish-rust that reads as a dirty version of the original colour rather than a clear faction signal. Marked tint `(100, 60, 160)` is more saturated and will shift enemy colours more visibly toward purple — this is the stronger of the two tints.

In HK, palette contamination in enemy-dense levels is aggressive: Husk enemies in fungal areas have visible green tinting, Deepnest enemies have a dark-grey shift. The signal is readable at a glance because the tint channels are high-contrast against the base colour. For Steamfall, the Fleshforged tint especially needs more saturation — raising the red channel and dropping the green would make it read as fire-orange rather than tan.

Additionally, a 50/50 blend applied to the render colour only (not to the health bar or any outline) means that on small sprites (enemies are 24×28 px per the general enemy rect) the colour shift may be difficult to distinguish from normal colour variation between enemy types, especially at distance.

**Recommended changes:**

- Raise the Fleshforged tint from `(160, 130, 100)` to `(200, 110, 50)` — a clearer fire-orange — and raise the blend weight from 0.5 to 0.65 (enemy 35%, tint 65%) so the tint dominates. This makes the tint read as a deliberate faction marking rather than a dirty overlay.
- Keep the Marked tint at `(100, 60, 160)` but also raise its blend weight to 0.65 for consistency.
- The blend weight is currently a magic number in the draw method. Extract it to `settings.py` as `FACTION_TINT_BLEND = 0.65` and reference it from `enemy.py`, so it can be tuned from one location.

```python
# settings.py — recommended additions
FACTION_TINT_BLEND        = 0.65          # was implicit 0.5 in enemy.py — raises tint dominance
FLESHFORGED_TINT_COLOR    = (200, 110, 50)  # was (160, 130, 100) — clearer fire-orange
MARKED_TINT_COLOR         = (100,  60, 160) # unchanged — already saturated enough
```

In `enemy.py` lines 160–166, replace:
```python
tint = (160, 130, 100)
color = tuple(int(a * 0.5 + b * 0.5) for a, b in zip(base_color, tint))
```
with:
```python
from settings import FLESHFORGED_TINT_COLOR, FACTION_TINT_BLEND
tint  = FLESHFORGED_TINT_COLOR
blend = FACTION_TINT_BLEND
color = tuple(int(a * (1 - blend) + b * blend) for a, b in zip(base_color, tint))
```
(and equivalently for the Marked branch using `MARKED_TINT_COLOR`).

---

## Summary Table (2026-04-25)

| Topic | File(s) | Key Issue | Recommended Change |
|---|---|---|---|
| Ending beat count | `marked_ending.py` L17–41; `fleshforged_ending.py` L17–41 | 8 beats — two same-register Narrator beats dilute the final `"???"` punch | Merge duplicate-register pairs; reduce to 6 beats per ending |
| Background lerp speed | `marked_ending.py` L108; `fleshforged_ending.py` L108 | `spd = 0.07` — colour lags ~90 frames behind beat advance on fast read | Raise `spd` to `0.18` for near-beat-synchronous colour |
| Lore auto-dismiss | `settings.py` L248; `gameplay.py` L663–669 | `LORE_DISPLAY_FRAMES = 300` — auto-dismiss during active gameplay interrupts reading | Prefer player-dismiss model; raise floor to `480` if timer kept |
| NPC hint snap-on | `npc.py` L40–44 | `"E"` hint appears instantly — no range-entry feel | Add 10-frame fade-in alpha ramp on `_hint_alpha` |
| NPC interact distance | `settings.py` L242 | `NPC_INTERACT_DIST = 60` — only 12 frames of hint lead at full sprint | Raise to `80` (0.33 s lead at 5 px/frame) |
| NPC hint Y-gating | `gameplay.py` L783–784 | Centre-X only check — off-platform NPCs falsely trigger hint | Add vertical proximity gate (`abs(dy) < NPC_HEIGHT * 2`) |
| Cutscene trigger model | `gameplay.py` L806–817 | Forced exit trigger violates HK's player-agency lore philosophy | Convert to optional NPC in level 4, or delay to level-4 exit |
| Mid-game tonal whiplash | `fleshforged_prologue.py` L129–139 | Dry Datalog register immediately follows intense combat | Delay trigger one level (4 → 5) to allow checkpoint rest |
| Faction tint visibility | `enemy.py` L158–168 | Fleshforged tint `(160,130,100)` is desaturated tan — reads as dirty, not faction-marked | Raise to `(200,110,50)`; increase blend to `FACTION_TINT_BLEND = 0.65` |
| Tint as magic number | `enemy.py` L160–166 | Blend weight `0.5` and tint colours are hardcoded inline | Extract to `settings.py` as `FACTION_TINT_BLEND`, `FLESHFORGED_TINT_COLOR`, `MARKED_TINT_COLOR` |

---

## Phase 4 Feel Review — 2026-04-29

### 1. Particle System Constants (P4-1)

The ROADMAP P4-1 spec (line 1347) proposed `PARTICLE_GRAVITY = 0.3` and `PARTICLE_FRICTION = 0.88`. The live `settings.py` values (lines 257–258) are `PARTICLE_GRAVITY = 0.25` and `PARTICLE_DRAG = 0.92`. The downward pull has been softened and the horizontal damping loosened relative to the spec — both moves make particles linger longer and arc more shallowly. For hit sparks that is mildly too floaty: HK's nail sparks fall quickly and spend only a handful of frames before vanishing. Restoring `PARTICLE_GRAVITY` to `0.3` and tightening drag to `0.88` (matching the spec) would produce a snappier, more percussive burst.

Count-wise, the live constants differ from the spec: `PARTICLE_HIT_COUNT = 5` (spec: 6), `PARTICLE_DEATH_COUNT = 12` (spec: 14), `PARTICLE_CHECKPOINT_COUNT = 14` (spec: 12). The hit and death counts are both one step below spec — at small sprite scale any reduction below 6/14 starts to feel thin on contact. Recommend raising both back to spec values.

Emit sites in `gameplay.py` (lines 768, 879–883) cover enemy death and player death. `player.py` lines 181–182 and 330–331 add landing and ability particles. However there is no hit-spark emit site on the enemy side — particle sparks are not emitted when the player's nail connects with a living enemy, only when the enemy dies. In HK, the nail contact flash is the primary tactile feedback. This is the highest-priority missing emit site for Phase 4.

**Recommended constant changes:**
```python
# settings.py
PARTICLE_GRAVITY   = 0.30   # was 0.25 — snappier arc, matches spec
PARTICLE_DRAG      = 0.88   # was 0.92 — faster horizontal decay, less float
PARTICLE_HIT_COUNT = 6      # was 5 — matches spec; thin below 6 at sprite scale
PARTICLE_DEATH_COUNT = 14   # was 12 — matches spec; death burst needs density
```

Add a hit-spark emit call in `gameplay.py` at the `hb.check_hits()` loop (lines 633–635): emit `PARTICLE_HIT_COUNT` sparks at the hit point when `check_hits` registers a landing blow.

---

### 2. Death Screen Timing (P4-2)

The death screen implementation in `gameplay.py` `_draw_death` (lines 1206–1229) is clean: the overlay alpha ramps from 0 to 180 over 90 frames (`min(180, self._death_timer * 2)`), the faction text appears at frame 30, and the "returning..." subline appears at frame 80. The respawn fires at frame 150 (line 885). The total 2.5-second window is correct for HK's "You Died" pacing.

The faction text and colour choices are well-calibrated: Marked purple `(130, 60, 200)` against the dark overlay reads clearly (line 1218); Fleshforged orange `(220, 100, 20)` likewise (line 1220). These match the faction signature colors in `settings.py` lines 23–24.

What the death screen lacks is any camera or physics punctuation at the moment of death. In HK, the Knight's body freezes for approximately 8–12 frames before the screen darkens — a micro-pause that lets the player register the hit that killed them. Currently the death particles emit on `_death_timer == 1` (line 879) while the camera continues to follow the player position. The player's body simply stops rendering as alive with no physical freeze. Adding a 6–8 frame `hitstop.trigger(6)` call on `_death_timer == 1` before the overlay begins would deliver this beat cheaply with existing infrastructure.

A second gap: the "returning..." prompt at frame 80 appears during the full 150-frame window but there is no way for the player to skip the remainder. HK allows pressing any key to accelerate the respawn once the death title has fully appeared (around frame 30–40 equivalent). Adding a `pygame.KEYDOWN` check inside the `not self.player.alive` branch of `handle_event` to set `_death_timer = 149` (fire respawn next frame) when `_death_timer > 60` would improve pacing without skipping the emotional beat.

**Recommended changes:**
- `gameplay.py` line 879: after emitting death particles, call `hitstop.trigger(6)` to freeze the frame for 6 frames — the death blow lands with weight before the screen darkens.
- `gameplay.py` `handle_event`: add early-skip on any key once `_death_timer > 60`.

---

### 3. Sound Architecture (P4-3)

The ROADMAP P4-3 spec (line 1437) lists seven SFX: attack, hit, jump, death, checkpoint, ability, boss_phase. All seven are present in `settings.py` (lines 274–280) and wired in `gameplay.py` and `player.py`. The music split — `MUSIC_LEVEL_1`, `MUSIC_LEVEL_5`, `MUSIC_BOSS` — covers three distinct tracks for five distinct biomes, which is functional but sparse. Level 5 gets its own track (sanctum.ogg); levels 1–4 share `outer_district.ogg`; levels 6–10 share `boss.ogg` whenever a boss is present and fall back to `MUSIC_LEVEL_1` otherwise. Levels 6–8 are the faction branches — long stretches of gameplay with neither a boss track nor a dedicated faction track. These sections will play `outer_district.ogg`, which carries no faction identity. HK's equivalent (the Queen's Gardens, Ancient Basin) each have a dedicated track that reinforces location mood. Recommend reserving paths for faction branch music even if no asset is available yet:

```python
# settings.py — recommended additions
MUSIC_MARKED_BRANCH      = "assets/music/marked_branch.ogg"      # levels 6-8 Marked path
MUSIC_FLESHFORGED_BRANCH = "assets/music/fleshforged_branch.ogg" # levels 6-8 Fleshforged path
```

The volume split `AUDIO_MUSIC_VOLUME = 0.5` / `AUDIO_SFX_VOLUME = 0.7` (settings.py lines 272–273) matches HK's convention of SFX slightly above music in the mix. No change needed.

One missing SFX call site: enemy hit-connect (when the player's nail lands on a living enemy) currently has no SFX emit. The spec lists `SOUND_HIT = "assets/sounds/hit.wav"` and wires it to `take_damage`, but `take_damage` is called on the enemy, not from `gameplay.py`. Verify that `audio.play_sfx("hit")` is called inside `entity.py` or `enemy.py` `take_damage()` — if it is absent there, the hit sound will never play during normal combat, only on player-damage events.

---

### 4. Main Menu Atmosphere (P4-5)

The parallax background in `main_menu.py` uses three layers at speeds 1, 2, 3 px/frame (line 31–33). The shapes are thin horizontal rectangles (6–14 px tall, 60–180 px wide, lines 22–25) in very dark near-black colours (`(20,15,35)`, `(28,18,50)`, `(36,20,60)`). The overall effect is correct in structure but the shapes are nearly invisible against the `(8, 4, 18)` background fill (line 120). The darkest layer at `(20,15,35)` has a luminance delta of approximately 14–17 against the background — below the perceptual threshold on most monitors in a dimly lit room. HK's main menu parallax (the roots and lanterns of Dirtmouth) is intentionally low-contrast but retains clear silhouette separation.

The speed differential between layers 1 and 3 (3×) is appropriate — enough to convey depth without feeling mechanical. The 1 px/frame background layer is at the edge of perceptibility on a 60 FPS loop; consider 1.5 px/frame minimum for that layer to ensure motion is registered.

The title pulse uses `self._pulse += 0.044 * self._pulse_dir` (line 103), giving an ~90-frame period as specified. The glow range is `180 + pulse * 75` (line 135), yielding RGB from `(180, 151, 50)` to `(255, 214, 50)`. This is a warm gold drift — feels appropriate for Steamfall's aesthetic, though the green channel `int(glow_val * 0.84)` tracks the red channel with a fixed ratio, meaning the hue barely shifts during the pulse. A slight hue rotation (e.g. edging the min state toward amber `(180, 120, 40)` vs. the max state at `(255, 220, 60)`) would give the pulse more visual character.

The credits overlay (lines 177–201) uses any-key dismiss — correct UX for a single-screen credits list. No changes needed to the credits flow.

**Recommended changes:**
```python
# main_menu.py _PARALLAX_LAYERS (lines 31–33): raise layer colors for visibility
(1, (35, 28, 55), _make_layer(6, (35, 28, 55))),   # was (20,15,35) — +15 luminance
(2, (45, 32, 68), _make_layer(5, (45, 32, 68))),   # was (28,18,50)
(3, (55, 38, 78), _make_layer(4, (55, 38, 78))),   # was (36,20,60)
```

Raise the slow layer speed from 1 to 1.5 px/frame (line 31) so near-background motion is perceivable on all displays.

---

### 5. NPC Hint Fade (P3 deferred)

The Phase 3 review (Summary Table, 2026-04-25) flagged that the `"E"` hint label in `npc.py` snaps on and off instantly (lines 40–45) and recommended a 10-frame alpha fade-in. As of the current `npc.py`, the implementation is unchanged: `_show_hint` is set as a boolean in `gameplay.py` line 828 and rendered without any alpha transition at `npc.py` lines 41–45. There is no `_hint_alpha` field, no ramp counter, and no `set_alpha` call. The snap-on behaviour is still present.

This deferred recommendation is directly actionable with no dependency on art assets or audio. The full fix requires three small changes:

1. **`entities/npc.py` `__init__`**: add `self._hint_alpha = 0` (integer 0–255).
2. **`entities/npc.py` `draw`**: replace the `if self._show_hint:` block with an alpha-ramp: increment `_hint_alpha` by 25 when `_show_hint` is True, decrement by 25 otherwise, clamp to `[0, 255]`. Create a surface for the label, call `set_alpha(self._hint_alpha)`, and blit only when `_hint_alpha > 0`.
3. **`gameplay.py` line 828**: the existing boolean assignment is sufficient; the ramp runs inside `npc.draw()` so no gameplay change is needed.

Re-flagging for Phase 4 implementation. Additionally, the Y-axis proximity gate recommended in the Phase 3 review (to prevent off-platform NPCs from triggering the hint) is also still absent from `gameplay.py` lines 825–828. Both fixes are in the same two files and should be batched into a single commit.

---

## Summary Table (2026-04-29)

| Topic | File(s) | Key Issue | Recommended Change |
|---|---|---|---|
| Particle gravity / drag | `settings.py` L257–258 | `PARTICLE_GRAVITY = 0.25` / `PARTICLE_DRAG = 0.92` — particles float; arc too shallow for HK impact | Restore to spec: `PARTICLE_GRAVITY = 0.30`, `PARTICLE_DRAG = 0.88` |
| Particle hit/death counts | `settings.py` L259–260 | `PARTICLE_HIT_COUNT = 5`, `PARTICLE_DEATH_COUNT = 12` — below spec; bursts feel thin | Raise to `PARTICLE_HIT_COUNT = 6`, `PARTICLE_DEATH_COUNT = 14` |
| Missing hit-spark emit site | `gameplay.py` L633–635 | No particles emitted when nail connects with living enemy — central HK tactile beat absent | Add `particles.emit_hit()` call in `hb.check_hits()` loop on successful hit |
| Death screen — no freeze frame | `gameplay.py` L879 | Player body vanishes without physics pause — no "weight" to the death blow | Call `hitstop.trigger(6)` on `_death_timer == 1` before overlay begins |
| Death screen — no skip | `gameplay.py` `handle_event` | Full 150-frame window is mandatory; HK allows key-press to accelerate past frame 60 | Handle `KEYDOWN` when `_death_timer > 60` to set `_death_timer = 149` |
| Missing faction branch music | `settings.py` | Levels 6–8 fall back to `outer_district.ogg`; no faction audio identity in branch levels | Add `MUSIC_MARKED_BRANCH` and `MUSIC_FLESHFORGED_BRANCH` path constants; wire in `on_enter` |
| Hit SFX call site audit | `entities/entity.py` or `gameplay.py` | `SOUND_HIT` is defined but unclear if `audio.play_sfx("hit")` fires on enemy `take_damage` | Verify `audio.play_sfx("hit")` is called inside `take_damage()` for enemy hits |
| Parallax layer visibility | `scenes/main_menu.py` L31–33 | Layer colors `(20,15,35)` — `(36,20,60)` are near-invisible against `(8,4,18)` background | Raise each layer color by ~+15 luminance; raise slow layer speed from 1 to 1.5 px/frame |
| Title pulse hue | `scenes/main_menu.py` L135–136 | Pulse drifts only in brightness; hue is static — less character than HK's logo animations | Shift min-state toward amber `(180,120,40)` for a visible warm-to-bright hue drift |
| NPC hint fade-in (P3 deferred) | `entities/npc.py` L40–45; `scenes/gameplay.py` L825–828 | `"E"` hint still snaps on/off with no alpha ramp — re-flagged from Phase 3 review | Add `_hint_alpha` ramp (±25/frame) in `npc.draw()`; add Y-axis proximity gate in `gameplay.py` |

---

## Phase 5 Feel Analysis (2026-05-02)

_Focus: Phase 4 additions — particle system (P4-1), death screen (P4-2), audio architecture (P4-3), sprite animation state mapping (P4-6), tile sprite fallback (P4-7), main menu polish (P4-5), settings screen (P4-4), ending scenes (P3-3). Evaluated against the HK feel pillars._

---

### Status of Phase 4 Review Recommendations

Before listing new gaps, the previous review pass (2026-04-29) flagged nine items. Their current status after P4-0c:

| Previous Flag | Status |
|---|---|
| `PARTICLE_GRAVITY = 0.30`, `PARTICLE_DRAG = 0.88` | **FIXED** — `settings.py` L258–259 now match spec values |
| `HIT_PARTICLE_COUNT = 6`, `DEATH_PARTICLE_COUNT = 14` | **FIXED** — `settings.py` L263, L269 now match spec |
| Missing hit-spark emit in `gameplay.py` hit loop | **FIXED** — `systems/combat.py` L75 calls `particles.emit_hit()` on every confirmed hit |
| Death screen `hitstop.trigger(6)` | **FIXED** — `gameplay.py` L908 fires on `_death_timer == 1` |
| Death screen player skip after frame 60 | **FIXED** — `gameplay.py` L441–444 handles `KEYDOWN` when `_death_timer > 60` |
| Faction branch music constants | **FIXED** — `MUSIC_MARKED_BRANCH` and `MUSIC_FLESHFORGED_BRANCH` in `settings.py` L313–314; wired in `gameplay.py` `on_enter` |
| Hit SFX audit | **FIXED** — `systems/combat.py` L76 calls `audio.play_sfx("hit")` |
| Parallax layer visibility and speed | **FIXED** — `main_menu.py` L31–33 luminance raised +15; slow layer speed is 1.5 px/frame |
| Title pulse hue amber drift | **FIXED** — `main_menu.py` L135–139 min-state is amber `(200, 100, 20)`; max-state bright gold |
| NPC hint fade-in (P3 deferred) | **FIXED** — `npc.py` L27–53 implements `_hint_alpha` ramp ±25/frame |

All nine prior recommendations have been applied. The items below are **new gaps** found in the Phase 4 code.

---

### 1. `PARTICLE_ABILITY_COUNT` Is Imported but Never Used

**File:** `systems/particles.py` L22.

```python
# particles.py L14–22
from settings import (... PARTICLE_ABILITY_COUNT)
```

`PARTICLE_ABILITY_COUNT = 8` is declared in `settings.py` L292 and imported into `particles.py` L22, but it is never referenced anywhere in the file. Neither `emit_soul_surge` (L134–147) nor `emit_overdrive` (L149–160) uses it — each function hardcodes its count via the specific `SOUL_SURGE_PARTICLE_COUNT` and `OVERDRIVE_PARTICLE_COUNT` constants instead. The import is a dead reference and the constant itself is orphaned.

This is not a crash bug, but it is a HK-feel gap by proxy: the constant name suggests there should be a unified ability activation emission path. Currently there is no single emit function that produces a generic "ability fired" burst — each ability has its own emitter. If a future ability (e.g., a dash or secondary) needs particles, a developer will duplicate the emission pattern rather than calling a shared function. In HK, spell activations share a common visual grammar (bright colour burst, brief shimmer) that reinforces the "something powerful just happened" signal regardless of spell type.

**Recommended change:** Remove the dead `PARTICLE_ABILITY_COUNT` import from `particles.py` L22 and the constant from `settings.py` L292, OR give the constant a home by adding a generic `emit_ability(x, y, color)` method to `ParticleSystem` that uses it:

```python
# systems/particles.py — add alongside emit_soul_surge / emit_overdrive
def emit_ability(self, x: float, y: float, color: tuple) -> None:
    """Generic ability-fire burst — used when a new ability has no bespoke emitter."""
    for _ in range(PARTICLE_ABILITY_COUNT):
        angle = random.uniform(0.0, math.pi * 2.0)
        speed = random.uniform(2.0, 6.0)
        vx = math.cos(angle) * speed
        vy = math.sin(angle) * speed
        lt = random.randint(14, 24)
        size = random.randint(2, 4)
        self._particles.append(
            Particle(x, y, vx, vy, color, lt, size, gravity=False))
```

If the constant is removed instead, also remove `PARTICLE_ABILITY_COUNT = 8` from `settings.py` L292 and `PARTICLE_DUST_COLOR = LANDING_PARTICLE_COLOR` from `settings.py` L293 (which is also never referenced in `particles.py`).

---

### 2. `emit_landing` Lifetime Is Shorter Than Expected — Dust Disappears Too Quickly

**File:** `systems/particles.py` L129; `settings.py` L287–288.

```python
# particles.py L129
lt = random.randint(8, 14)
```

Landing dust particles have a lifetime of 8–14 frames. At 60 FPS this is 133–233 ms. The constant `LANDING_PARTICLE_COUNT = 4` (settings.py L287) produces four dust puffs, each one vanishing in under a quarter-second. In HK, landing dust (from the Knight dropping any significant height) persists for approximately 18–24 frames — long enough to be seen in peripheral vision while the player immediately begins moving. At 8–14 frames the dust evaporates before the player's eye can register it, especially since gameplay resumes at the same instant.

The spec at ROADMAP L1381 says landing particles should "drift outward, fade alpha" — the current implementation satisfies the geometry (left/right split, slight upward initial vy) but the lifetime is roughly half what is needed to be felt. Note that `LANDING_PARTICLE_COUNT = 4` was already at the minimum spec value (ROADMAP L1381: "4 dust particles"); with only 4 particles and a sub-14-frame lifetime the effect is barely perceptible on a running player.

**Recommended changes:**

```python
# settings.py
LANDING_PARTICLE_COUNT = 6      # was 4 — minimum 6 particles for visible dust at sprite scale
```

```python
# systems/particles.py L129 — change lifetime range
lt = random.randint(16, 22)     # was random.randint(8, 14) — 0.27–0.37 s; matches HK dust
```

The `lt` range in `emit_landing` is hardcoded rather than referencing a constant. Add a `LANDING_PARTICLE_LIFE` constant to `settings.py` and use it (mirrors the pattern used by `HIT_PARTICLE_LIFE` and `DEATH_PARTICLE_LIFE`):

```python
# settings.py — add alongside other particle constants (around L288)
LANDING_PARTICLE_LIFE = 20   # NEW — frames; hardcoded 8–14 in particles.py emit_landing
```

---

### 3. Player Death Particles Use a Generic Red Burst, Not Faction Color

**File:** `scenes/gameplay.py` L901–907.

```python
# gameplay.py L901–907
particles.emit(
    self.player.rect.centerx,
    self.player.rect.centery,
    count=DEATH_PARTICLE_COUNT // 2,
    speed=3.0,
    color=RED,
    life=25,
    spread=360,
)
```

When the player dies, the death burst emits `DEATH_PARTICLE_COUNT // 2 = 7` particles in plain `RED` (imported from settings as `(200, 20, 20)`). The faction-specific death text is applied at `gameplay.py` L1237–1247 (purple for Marked, orange for Fleshforged), but the particle color ignores faction entirely. In HK, the Knight's death is a single coherent visual moment — the shade burst, screen overlay, and text all share a palette. The current implementation has the faction-colored text floating above a faction-neutral red particle cloud, which dilutes the faction identity signal precisely at the most emotionally loaded moment in a run.

This is the counterpart to the death text being faction-specific: both elements should share the palette.

**Recommended change:** In `gameplay.py` `_draw_death` handler (or `update()` at the death particle emit site, L901–907), replace the hardcoded `RED` with a faction-resolved color:

```python
# gameplay.py around L901 — replace color=RED with:
_faction = getattr(self.game, "player_faction", None)
_death_color = (180, 140, 220) if _faction == FACTION_MARKED else \
               (220, 160, 80)  if _faction == FACTION_FLESHFORGED else RED
particles.emit(
    self.player.rect.centerx, self.player.rect.centery,
    count=DEATH_PARTICLE_COUNT // 2,
    speed=3.0,
    color=_death_color,
    life=25,
    spread=360,
)
```

The color values `(180, 140, 220)` and `(220, 160, 80)` already match the death text colors at `gameplay.py` L1241, L1244. No new constants needed; the death text color values could alternatively be extracted to `settings.py` as `DEATH_TEXT_COLOR_MARKED` and `DEATH_TEXT_COLOR_FLESHFORGED` for DRY compliance, but that is a build-agent concern — the color match is the HK-feel fix.

---

### 4. Hurt State in `_update_animation` Flickers Rapidly — Jarring Under P4-6 Sprites

**File:** `entities/player.py` L370–371; `systems/animation.py` L30.

```python
# player.py L370–371
elif self.iframes > 0 and self.iframes % 6 < 3:
    self._anim.set_state("hurt")
```

```python
# animation.py L30
"hurt": 6,  # frames per animation tick in _STATE_FPS
```

With `PLAYER_IFRAMES = 45` (settings.py L73), the `iframes % 6 < 3` condition toggles the "hurt" state on for 3 frames and off for 3 frames, cycling 7–8 times over the full 45-frame iframe window. Each time the condition is False the state machine falls through to whichever state applies (walk, jump, idle, attack), then returns to "hurt" 3 frames later. This means `AnimationController.set_state()` is called with alternating `"hurt"` → `"walk/idle"` → `"hurt"` → ... on every 3rd frame.

Using colored-rect placeholder frames (the current default), this flicker is readable because the draw method (`player.py` L405–407) independently draws a white outline during iframes — the visual cue is the outline, not the animation state. Under real PNG sprites (P4-6/P5-1), however, each `set_state` call that differs from the previous resets `_frame_idx` to 0 (`animation.py` L129–131):

```python
if name != self.state:
    self.state      = name
    self._frame_idx = 0
    self._tick      = 0
```

The animation state machine will restart from frame 0 of the idle/walk/attack sprite, then snap back to frame 0 of the hurt sprite 3 frames later, repeatedly. Under real sprites this will produce a jarring seizure of conflicting animation frames for the full 45-frame iframe window — exactly the opposite of HK's iframe flash, which is a smooth blink on a held pose.

HK's iframe flash is a draw-layer effect (the Knight flashes transparent/opaque) applied to the current animation state, not an animation state switch. The "hurt" animation in HK plays once on the first hit, then the Knight returns to the locomotion state while blinking.

**Recommended change:** Remove the iframe-based `set_state("hurt")` from `_update_animation` and keep "hurt" as a one-shot transition that plays once on the first frame of iframe, then returns to locomotion state. The iframe blink should be handled purely in `draw()` via the existing outline logic.

The minimal fix is to change the condition from a frame-mod flicker to a one-shot trigger: only set "hurt" on the first frame of iframe (when iframes transitions from 0 to a positive value), then let the state resolve normally afterward. The existing iframe outline in `draw()` (L405–407) already handles the visual blink without any animation state switch.

```python
# entities/player.py _update_animation — replace the hurt branch:
# BEFORE:
elif self.iframes > 0 and self.iframes % 6 < 3:
    self._anim.set_state("hurt")
# AFTER (one-shot transition only):
elif self.iframes == PLAYER_IFRAMES:   # first frame of iframe window only
    self._anim.set_state("hurt")
```

This plays the hurt animation once (it will run through its 3 frames × 6 ticks = 18 frames of animation), then the state machine falls through to normal locomotion while the outline blink continues independently. Under placeholder rects the behavior is visually identical to today; under real sprites the hurt clip plays once cleanly.

Note: `PLAYER_IFRAMES` must be imported in `player.py` for this comparison — it is already imported at L26.

---

### 5. Enemy Animation State Machine Is Missing `fall` and `jump` States

**File:** `entities/enemy.py` L86–94.

```python
# enemy.py L86–94
if self.iframes > 0:
    self._anim.set_state("hurt")
elif self._state == _ATTACK:
    self._anim.set_state("attack")
elif abs(self.vx) > 0.1:
    self._anim.set_state("walk")
else:
    self._anim.set_state("idle")
```

The enemy animation controller has `jump` and `fall` states loaded (`animation.py` L35–37, `_STATE_FRAMES` dict), but the enemy state selector never drives them. Any enemy that is airborne (launched by knockback, walking off a ledge, or a Jumper entity mid-hop) will display the `walk` or `idle` sprite while visibly not touching the ground. In HK, every airborne entity uses its airborne animation — the visual mismatch between physics state (falling) and animation state (walking) is a polish gap that becomes visible as soon as real sprites land in `assets/sprites/enemy/`.

Jumper (`entities/jumper.py`) is the most egregious case: it deliberately launches into the air on every hop, but the animation state machine will show `walk` or `idle` for the entire arc.

**Recommended change:** Add `vy` inspection to the enemy animation selector, matching the logic in `player.py` L374–377:

```python
# entities/enemy.py — replace the animation block (L86–94):
if self.iframes > 0:
    self._anim.set_state("hurt")
elif self._state == _ATTACK:
    self._anim.set_state("attack")
elif not self.on_ground and self.vy < -1.0:
    self._anim.set_state("jump")
elif not self.on_ground and self.vy > 1.0:
    self._anim.set_state("fall")
elif abs(self.vx) > 0.1:
    self._anim.set_state("walk")
else:
    self._anim.set_state("idle")
```

The `vy` threshold of `±1.0` (vs. the player's `vy < 0` / `vy > 0`) avoids flickering on shallow bounces where `vy` hovers near zero at the apex of a short hop. Subclasses (Jumper, Boss) inherit this fix immediately since they call `super().update()` which runs this block.

---

### 6. Tile Sprite Coverage Stops at Level 5 — Levels 6–10 Have No Tile Sheet Mapping

**File:** `world/tilemap.py` L47–55.

```python
# tilemap.py L47–55
def _tile_sheet_for_level(level_name: str) -> pygame.Surface | None:
    if level_name in ("level_1", "level_2"):
        return _load_tile_sprite(TILE_SHEET_LEVEL_1_2)
    if level_name in ("level_3", "level_4"):
        return _load_tile_sprite(TILE_SHEET_LEVEL_3_4)
    if level_name == "level_5":
        return _load_tile_sprite(TILE_SHEET_LEVEL_5)
    return None   # levels 6–10 always fall back to colored rects
```

The three tile sheet constants (`TILE_SHEET_LEVEL_1_2`, `TILE_SHEET_LEVEL_3_4`, `TILE_SHEET_LEVEL_5`) only cover levels 1–5. Levels 6–10 unconditionally return `None`, meaning even when tile art assets are delivered they will render as colored rects in the faction branches and boss levels. LEVEL_5 (`"V — The Sanctum"`) uses `sanctum.ogg` — a dedicated biome — but LEVEL_6 through LEVEL_10 have no corresponding tile sheet path defined in `settings.py`.

HK assigns distinct visual palettes to each major biome region. The faction branches (levels 6–8) and the final levels (9–10) are the most tonally distinct sections of the game and are precisely the sections that need separate tile palettes.

**Recommended change:** Add three more tile sheet constants to `settings.py` and extend `_tile_sheet_for_level` to cover the full level range:

```python
# settings.py — add after TILE_SHEET_LEVEL_5 (L324)
TILE_SHEET_LEVEL_6_MARKED      = "assets/tiles/ink_labyrinth.png"
TILE_SHEET_LEVEL_6_FLESHFORGED = "assets/tiles/steam_tunnels.png"
TILE_SHEET_LEVEL_9_10          = "assets/tiles/convergence.png"
```

```python
# world/tilemap.py _tile_sheet_for_level — extend:
if level_name in ("level_6_marked", "level_7_marked", "level_8_marked"):
    return _load_tile_sprite(TILE_SHEET_LEVEL_6_MARKED)
if level_name in ("level_6_fleshforged", "level_7_fleshforged", "level_8_fleshforged"):
    return _load_tile_sprite(TILE_SHEET_LEVEL_6_FLESHFORGED)
if level_name in ("level_9", "level_10"):
    return _load_tile_sprite(TILE_SHEET_LEVEL_9_10)
```

This change is a `tilemap.py`-only expansion of existing pattern code (no logic change); it adds six new path constants to `settings.py` and three branches to a pure-lookup function.

---

### 7. Audio — No `SOUND_ENEMY_DEATH` SFX Call Site

**File:** `scenes/gameplay.py` L783–787.

```python
# gameplay.py L783–787
newly_dead = [e for e in self.enemies if not e.alive]
for dead_e in newly_dead:
    particles.emit_death(dead_e.rect.centerx, dead_e.rect.centery,
                         dead_e.color)
    for drop in dead_e.get_drop_fragments():
        ...
```

Enemy death emits a particle burst (correct) but plays no SFX. The audio system has `SOUND_DEATH = "assets/sounds/death.wav"` wired to the player death event (`gameplay.py` L909), but there is no dedicated enemy-death sound. In HK, each enemy type has a death chirp or crumble sound that closes the engagement — it provides the auditory punctuation for a kill. Without it, kills are silent beyond the hit-stop white flash.

The existing `SOUND_HIT` plays on every confirmed hit (via `combat.py` L76), which provides partial feedback, but a kill with no distinct sound leaves the player uncertain whether the enemy is dead or just in hit-stun.

**Recommended change:** Add `SOUND_ENEMY_DEATH` to `settings.py` and wire it at the enemy-death emit site in `gameplay.py`:

```python
# settings.py — add alongside other SOUND_ constants (around L307)
SOUND_ENEMY_DEATH = "assets/sounds/enemy_death.wav"
```

```python
# systems/audio.py _SFX_KEYS dict — add entry:
"enemy_death": SOUND_ENEMY_DEATH,
```

```python
# scenes/gameplay.py L786 — add SFX call in the newly-dead loop:
for dead_e in newly_dead:
    particles.emit_death(dead_e.rect.centerx, dead_e.rect.centery,
                         dead_e.color)
    audio.play_sfx("enemy_death")   # ADD THIS LINE
    for drop in dead_e.get_drop_fragments():
        ...
```

The `audio.py` `play_sfx` is no-op when the file is absent, so this is safe to add before the sound asset exists.

---

### 8. Settings Screen — No Audio Preview on Volume Change

**File:** `scenes/settings.py` L79–89.

```python
# settings.py scene L75–89
def _adjust(self, delta: float) -> None:
    if self._sel == 0:
        ...
        self.game.audio.set_music_volume(self._music_vol)
        self.game.save_data["music_vol"] = self._music_vol
    elif self._sel == 1:
        ...
        self.game.audio.set_sfx_volume(self._sfx_vol)
        self.game.save_data["sfx_vol"] = self._sfx_vol
```

Adjusting SFX Volume changes the volume but does not play a test sound, so the player has no immediate auditory feedback confirming the new level. In HK's settings, adjusting SFX volume plays a brief tick or whoosh at the new level so the player can hear the change in real time. The current implementation applies the volume change silently — the player must exit settings and re-enter gameplay to hear the effect.

**Recommended change:** After `self.game.audio.set_sfx_volume(self._sfx_vol)` in `_adjust`, call `self.game.audio.play_sfx("hit")` (or another short SFX) as an immediate preview:

```python
# scenes/settings.py L84 — add preview call after volume set:
self.game.audio.set_sfx_volume(self._sfx_vol)
self.game.audio.play_sfx("hit")   # preview the new SFX volume immediately
self.game.save_data["sfx_vol"] = self._sfx_vol
```

No new constants needed; `SOUND_HIT` is already defined and loaded.

---

### 9. Lore Item Display — Auto-Dismiss Timer Still Active; Player-Dismiss Still Absent (P3 Deferred, Re-Flagged)

**File:** `scenes/gameplay.py` L715–721; `settings.py` L254.

The Phase 3 review (2026-04-25, item 2) recommended replacing the `LORE_DISPLAY_FRAMES = 300` auto-dismiss with a player-acknowledge model (SPACE/RETURN to dismiss). As of the current code:

```python
# gameplay.py L715–721
if result:
    self._lore_text  = result
    self._lore_timer = LORE_DISPLAY_FRAMES   # 300 frames = 5 seconds
...
if self._lore_timer > 0:
    self._lore_timer -= 1
```

The auto-dismiss is unchanged. `settings.py` L254 still reads `LORE_DISPLAY_FRAMES = 300`. There is no `_lore_waiting_dismiss` flag, no `KEYDOWN` intercept for lore text in `handle_event`, and the game logic does not pause during lore display.

The Phase 3 review also recommended raising the fallback floor to `LORE_DISPLAY_FRAMES = 480` (8 s) if the timer model is kept. Neither the floor raise nor the player-dismiss model has been implemented. Since Phase 5 will add more lore discovery moments (P5-1/P5-2 will apply art assets that make lore items more visually salient, increasing discover rate), this gap becomes more urgent.

**Recommended changes (same as Phase 3 review; re-citing with current line numbers):**

```python
# settings.py L254 — raise floor if timer model kept:
LORE_DISPLAY_FRAMES = 480   # was 300 — 8 s floor; prefer player-dismiss model
```

For the player-dismiss model, add to `gameplay.py` `handle_event` (after the boss-intro intercept and before pause handling, around L440):

```python
# gameplay.py handle_event — add lore dismiss before pause handling:
if self._lore_timer > 0 and self._lore_text:
    if event.key in (pygame.K_SPACE, pygame.K_RETURN):
        self._lore_timer = 0
        self._lore_text  = ""
        return
```

This requires no new constants and is a minimal 4-line addition.

---

### Summary Table (2026-05-02)

| Topic | File(s) | Key Issue | Recommended Change |
|---|---|---|---|
| `PARTICLE_ABILITY_COUNT` dead import | `systems/particles.py` L22; `settings.py` L292 | Constant imported but never used — orphaned | Remove from both files, OR add a `emit_ability(x, y, color)` method that uses it |
| Landing dust too brief | `systems/particles.py` L129; `settings.py` L287 | Lifetime 8–14 frames too short to register in peripheral vision | Raise to `random.randint(16, 22)`; add `LANDING_PARTICLE_LIFE = 20` constant; raise count to `LANDING_PARTICLE_COUNT = 6` |
| Player death particles faction-neutral | `scenes/gameplay.py` L901–907 | Death burst uses hardcoded `RED` regardless of faction | Resolve death color from `player_faction`; use same colors as death text (`(180,140,220)` Marked / `(220,160,80)` Fleshforged) |
| Hurt animation flicker | `entities/player.py` L370–371 | `iframes % 6 < 3` alternates "hurt" ↔ locomotion state 7× — will seizure under real sprites | Change to one-shot: set "hurt" only on `iframes == PLAYER_IFRAMES` (first frame); draw blink via existing outline |
| Enemy animation missing jump/fall | `entities/enemy.py` L86–94 | Airborne enemies (esp. Jumper) always show walk/idle — visual mismatch once sprites land | Add `not self.on_ground` branches for `"jump"` / `"fall"` states, same as player logic |
| Tile sheets stop at level 5 | `world/tilemap.py` L47–55; `settings.py` L318–324 | Levels 6–10 always return `None` from `_tile_sheet_for_level` — no art coverage for faction branches | Add `TILE_SHEET_LEVEL_6_MARKED`, `TILE_SHEET_LEVEL_6_FLESHFORGED`, `TILE_SHEET_LEVEL_9_10` constants; extend the lookup function |
| No enemy death SFX | `scenes/gameplay.py` L783–787; `systems/audio.py` L21–29 | Enemy kills are silent — no auditory kill confirmation | Add `SOUND_ENEMY_DEATH` constant; wire `audio.play_sfx("enemy_death")` in death loop |
| Settings screen silent volume change | `scenes/settings.py` L83–86 | Adjusting SFX volume has no auditory preview | Call `audio.play_sfx("hit")` after each SFX volume adjustment |
| Lore display no player-dismiss (P3 deferred × 2) | `scenes/gameplay.py` L715–721; `settings.py` L254 | Auto-dismiss still active; no SPACE shortcut; timer floor still 300 | Add `KEYDOWN` intercept in `handle_event`; raise `LORE_DISPLAY_FRAMES` to `480` as fallback |
