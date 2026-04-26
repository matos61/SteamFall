# =============================================================================
# settings.py — All game-wide constants live here.
# Change values here instead of hunting through multiple files.
# =============================================================================

# --- Screen ---
SCREEN_WIDTH  = 1280
SCREEN_HEIGHT = 720
FPS           = 60
TITLE         = "Steamfall"

# --- Colors (R, G, B) ---
BLACK         = (0,   0,   0)
WHITE         = (255, 255, 255)
GRAY          = (120, 120, 120)
DARK_GRAY     = (30,  30,  30)
GOLD          = (210, 175, 55)
RED           = (220, 50,  50)
GREEN         = (60,  200, 80)

# Faction signature colors
MARKED_COLOR       = (140, 60,  220)   # Deep purple — ink and soul
FLESHFORGED_COLOR  = (210, 85,  30)    # Burnt orange — iron and heat

# HUD colors
HEALTH_COLOR       = (200, 40,  40)
HEALTH_BG_COLOR    = (60,  10,  10)
SOUL_COLOR         = (110, 50,  200)
HEAT_COLOR         = (200, 100, 20)
RESOURCE_BG_COLOR  = (20,  20,  40)

# Tile colors (used until real sprites are added)
TILE_COLOR         = (55,  50,  70)
TILE_EDGE_COLOR    = (80,  75,  100)

# Checkpoint colors
CHECKPOINT_COLOR      = (80,  70,  110)   # Inactive pillar — muted purple-grey
CHECKPOINT_GLOW_COLOR = (180, 140, 255)   # Active pillar — bright arcane glow

# --- Physics (baseline — firmer arc, closer to Hollow Knight feel) ---
GRAVITY           = 0.85   # was 0.6 — firm downward pull, no floaty hang time
TERMINAL_VELOCITY = 20     # was 18  — faster fall, more commitment to jumping
FRICTION          = 0.74   # was 0.78 — slightly more slide on landing

# --- Faction-specific physics feel ---
# These are applied on top of the baseline inside player.py.
# They exist so the two factions feel mechanically distinct, matching their lore.
#
# Marked — "The body is a vessel. Power through insight and sacrifice."
#   Lighter gravity, full air precision, quicker stops. Arcane agility.
MARKED_GRAVITY_MULT  = 0.88   # Soul partially defies gravity — slight float
MARKED_AIR_CONTROL   = 1.00   # Full air steering — mystical precision
MARKED_FRICTION      = 0.80   # Crisp, quick stops — footwork mastery
MARKED_JUMP_MULT     = 1.06   # Slightly higher arc — ascension motif
MARKED_JUMP_CUT      = 0.82   # Gentler variable-height cut — floatier short hop
#
# Fleshforged — "The soul is chemical. Control the form."
#   Full gravity, momentum carries through turns, higher top speed, harder landings.
FLESHFORGED_GRAVITY_MULT = 1.00   # Iron skeleton — no quarter from gravity
FLESHFORGED_AIR_CONTROL  = 0.72   # Momentum-based — hard to change direction mid-air
FLESHFORGED_FRICTION     = 0.70   # More slide — augmented mass keeps moving
FLESHFORGED_JUMP_MULT    = 0.94   # Slightly lower arc — heavy body
FLESHFORGED_JUMP_CUT     = 0.72   # Aggressive variable-height cut — commits to arc

# --- Player ---
PLAYER_SPEED      = 5      # Horizontal run speed
ENEMY_IFRAMES     = 10     # Enemy invincibility frames after a hit (shorter than
                           # player iframes so combo attacks feel responsive)
PLAYER_JUMP_FORCE = -12    # was -13 — slightly lower peak, snappier arc
PLAYER_MAX_HEALTH = 100
PLAYER_MAX_SOUL   = 100    # Marked resource (arcane energy)
PLAYER_MAX_HEAT   = 100    # Fleshforged resource (heat/overdrive)
PLAYER_IFRAMES    = 45     # Invincibility frames after taking a hit
PLAYER_ATTACK_DURATION = 12   # Frames the attack hitbox stays active
PLAYER_ATTACK_COOLDOWN = 25   # Frames between attacks

# --- Hollow Knight feel constants ---
ATTACK_RECOIL_VX    = 1.5    # Horizontal pushback when player attacks (nail recoil)
WINDUP_FRAMES       = 4      # Frames before attack hitbox becomes active (telegraph)
DAMAGE_FLASH_FRAMES = 20     # Frames the red screen-edge vignette persists after a hit
TOUCH_KNOCKBACK_VX  = 4.5    # Horizontal speed applied to player on touch damage
TOUCH_KNOCKBACK_VY  = -3.0   # Vertical speed applied to player on touch damage

# --- Enemy ---
ENEMY_PATROL_SPEED  = 1.5
ENEMY_CHASE_SPEED   = 2.5
ENEMY_SIGHT_RANGE   = 260   # Pixels; enemy starts chasing within this range
ENEMY_ATTACK_RANGE  = 40    # Pixels; enemy deals damage within this range
ENEMY_ATTACK_DAMAGE = 15

# --- Tiles ---
TILE_SIZE = 32

# --- Dialogue ---
TEXT_SCROLL_SPEED  = 2     # Characters revealed per frame
DIALOGUE_FONT_SIZE = 22

# --- Scene Names (use these strings to switch scenes) ---
SCENE_MAIN_MENU            = "main_menu"
SCENE_FACTION_SELECT       = "faction_select"
SCENE_MARKED_PROLOGUE      = "marked_prologue"
SCENE_FLESHFORGED_PROLOGUE = "fleshforged_prologue"
SCENE_GAMEPLAY             = "gameplay"

# --- Faction Keys ---
FACTION_MARKED      = "marked"
FACTION_FLESHFORGED = "fleshforged"

# --- Hitstop ---
HITSTOP_FRAMES = 4    # Default freeze-frame count when a hit lands

# --- Crawler enemy ---
CRAWLER_SPEED  = 1.8
CRAWLER_HP     = 30
CRAWLER_DAMAGE = 10
CRAWLER_COLOR  = (40, 120, 80)   # Dark green

# --- Soul Fragment collectible ---
SOUL_FRAGMENT_COLOR = (130, 80, 220)   # Soft purple orb
SOUL_FRAGMENT_SIZE  = 12               # Pixels square

# --- Boss ---
BOSS_MAX_HEALTH    = 400
BOSS_PHASE2_THRESH = 0.50   # Health fraction when phase 2 starts
BOSS_PHASE3_THRESH = 0.25   # Health fraction when phase 3 starts
BOSS_BAR_HEIGHT    = 18
BOSS_BAR_Y         = SCREEN_HEIGHT - 38
BOSS_BAR_MARGIN    = 80

# --- Save ---
SAVE_FILE = "steamfall_save.json"

# --- Level transitions ---
TRANSITION_FADE_FRAMES = 40
TRANSITION_HOLD_FRAMES = 20
TRANSITION_IN_FRAMES   = 30

# --- Minimap ---
MAP_TILE_SIZE = 4
MAP_ALPHA     = 210

# --- Ability slots ---
ABILITY_SLOTS_DEFAULT = 0
ABILITY_SLOTS_MAX     = 1

# --- ShieldGuard enemy ---
SHIELD_GUARD_HP          = 65      # was 80 — lower HP compensates for full frontal block
SHIELD_GUARD_SPEED       = 1.6     # was 1.2 — faster chase punishes kiting
SHIELD_GUARD_DAMAGE      = 20
SHIELD_GUARD_DEFENSE     = 0.0     # was 0.35 — full frontal block; player must flank
SHIELD_GUARD_KNOCKBACK_Y = -3.5    # Heavy upward bash (extracted from hardcode)
SHIELD_GUARD_COLOR       = (50, 80, 140)   # Steel blue

# --- Ranged enemy ---
RANGED_HP              = 40
RANGED_SPEED           = 1.0
RANGED_DAMAGE          = 12
RANGED_PROJ_SPEED      = 6         # was 5 — faster bolt, tighter reaction window
RANGED_ATTACK_COOLDOWN = 55        # was 90 — ~0.9 s between shots; creates real pressure
RANGED_SIGHT_RANGE     = 380       # Wider than melee enemies
RANGED_PREFERRED_DIST  = 240       # was hardcoded 220 in ranged.py
RANGED_COLOR           = (100, 60, 30)   # Rust brown

# --- Jumper enemy ---
JUMPER_HP               = 35
JUMPER_SPEED            = 2.4      # was 2.0 — faster horizontal component
JUMPER_DAMAGE           = 12
JUMPER_JUMP_FORCE       = -12      # was -11 — higher hop, harder to hit mid-air
JUMPER_JUMP_COOLDOWN    = 32       # was 55 — ~0.53 s; urgency, harder to exploit landing
JUMPER_BURST_COUNT      = 2        # Jumps per burst before pause
JUMPER_BURST_PAUSE      = 70       # Frames of pause after a full burst
JUMPER_KNOCKBACK_Y_GROUND = -4.5   # Upward bounce on ground-level attack (was hardcoded)
JUMPER_KNOCKBACK_Y_AERIAL =  2.0   # Downward spike when Jumper attacks from above
JUMPER_COLOR            = (50, 140, 80)   # Sickly green

# --- P2-3: Warden scripting ---
# Boss scripted intro cutscene
BOSS_INTRO_TRIGGER_DIST    = 520   # px — proximity that starts the pre-fight cutscene

# Phase-transition announce banner
BOSS_PHASE_ANNOUNCE_FRAMES = 90    # frames the phase banner stays visible

# Phase 2 — dash charge attack
BOSS_DASH_SPEED            = 9     # vx during the dash
BOSS_DASH_FRAMES           = 22    # frames each dash lasts
BOSS_DASH_COOLDOWN         = 110   # frames between dash opportunities

# Phase 3 — projectile spread
BOSS_PROJ_SPREAD_VY        = 3     # vy offset for the upper/lower spread projectiles

# Phase 3 — arena shrink walls
ARENA_SHRINK_SPEED         = 0.5   # px/frame the walls move inward
ARENA_SHRINK_AMOUNT        = 200   # max px each side shrinks inward
ARENA_WALL_COLOR           = (45, 25, 75)   # dark purple tile colour

# --- P2-4: The Architect final boss ---
ARCHITECT_MAX_HEALTH    = 600
ARCHITECT_PHASE2_THRESH = 0.75   # 75% HP — adds teleport
ARCHITECT_PHASE3_THRESH = 0.50   # 50% HP — adds 5-projectile fan
ARCHITECT_PHASE4_THRESH = 0.25   # 25% HP — adds Crawler spawns
ARCHITECT_TELEPORT_CD   = 140    # frames between teleports (was 200)
ARCHITECT_TELEPORT_WARN = 20     # NEW — pre-teleport lock+pulse frames before position jump
ARCHITECT_FAN_CD        = 90     # frames between fan spread shots
ARCHITECT_MINION_CD     = 210    # frames between Crawler spawns (was 300)

# --- P2-5: Upgrade system ---
UPGRADE_HP_BONUS        = 25     # Max HP increase per upgrade selection
UPGRADE_DMG_BONUS       = 6      # Attack damage bonus per upgrade selection (was 5)
UPGRADE_DMG_MAX_STACKS  = 3      # NEW — max times "dmg" upgrade can be applied
UPGRADE_RES_BONUS       = 20     # Max resource increase per upgrade selection
UPGRADE_RES_REGEN_BONUS = 0.008  # NEW — additive boost to 0.05/frame passive regen per stack

# --- P2-6: Enemy drops ---
HEAT_CORE_SIZE    = 10                  # px square
HEAT_CORE_HEAL    = 12                  # HP healed when picked up by Fleshforged
HEAT_CORE_COLOR   = (220, 100, 20)      # Burnt orange
SOUL_SHARD_SIZE   = 10
SOUL_SHARD_HEAL   = 12                 # HP healed when picked up by Marked
SOUL_SHARD_COLOR  = (130, 80, 220)      # Soft purple (matches SOUL_FRAGMENT_COLOR)
DROP_BOB_SPEED    = 0.08                # radians/frame for bobbing sinusoid
DROP_BOB_AMP      = 3                   # pixel amplitude of bob

# --- P2-7: Environmental hazards ---
SPIKE_DAMAGE           = 20             # HP lost per frame of contact with a spike tile
CRUMBLE_STAND_FRAMES   = 30            # Frames player must stand on tile before it falls
CRUMBLE_RESPAWN_FRAMES = 180           # Frames before a crumble tile reappears
SPIKE_COLOR            = (180, 60, 60)  # Dark red spike pixel color
CRUMBLE_COLOR          = (110, 90, 60)  # Brownish crumble tile color
CRUMBLE_WARNING_COLOR  = (160, 120, 40) # Color shift when about to crumble

# --- P3-1: Mid-game lore beat start indices ---
MARKED_LORE_BEAT_START      = 33   # Index of first mid-game Marked lore beat in MARKED_BEATS
FLESHFORGED_LORE_BEAT_START = 30   # Index of first mid-game Fleshforged lore beat in FLESHFORGED_BEATS

# --- P3-3: Ending scenes ---
SCENE_MARKED_ENDING      = "marked_ending"
SCENE_FLESHFORGED_ENDING = "fleshforged_ending"

# --- P3-4: NPC encounters ---
NPC_WIDTH         = 24
NPC_HEIGHT        = 40
NPC_INTERACT_DIST = 80      # Pixels — E-key trigger range
NPC_COLOR         = (140, 160, 140)

# --- P3-0b: Faction tint constants (extracted from enemy.py magic numbers) ---
FACTION_TINT_BLEND     = 0.65                 # Blend weight toward tint color
FLESHFORGED_TINT_COLOR = (200, 110, 50)       # Iron-orange enemy tint
MARKED_TINT_COLOR      = (100, 60, 160)       # Acolyte-purple enemy tint

# --- P3-5: Collectible lore items ---
LORE_ITEM_SIZE      = 16
LORE_ITEM_COLOR     = (160, 140, 100)    # Parchment tone
LORE_DISPLAY_FRAMES = 300                # 5 seconds at 60 FPS

# --- Phase 4: Particle system ---
PARTICLE_GRAVITY          = 0.25   # px/frame² downward acceleration
PARTICLE_DRAG             = 0.92   # horizontal velocity multiplier per frame
PARTICLE_HIT_COUNT        = 5      # sparks emitted per hit connection
PARTICLE_DEATH_COUNT      = 12     # particles per entity death burst
PARTICLE_LAND_COUNT       = 6      # dust puffs emitted on landing
PARTICLE_ABILITY_COUNT    = 8      # particles per ability activation
PARTICLE_CHECKPOINT_COUNT = 14     # golden embers per checkpoint activation
PARTICLE_DUST_COLOR       = (160, 140, 110)   # warm tan for landing dust
