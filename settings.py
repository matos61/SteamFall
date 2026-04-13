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
