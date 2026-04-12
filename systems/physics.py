# =============================================================================
# systems/physics.py — Gravity and tile collision resolution.
#
# How tile collision works:
#   We resolve X and Y movement SEPARATELY each frame.
#   1. Move on X axis → check tiles → push out horizontally if overlap.
#   2. Move on Y axis → check tiles → push out vertically if overlap.
#      If pushed UP (landed on top) → entity is grounded.
#      If pushed DOWN (hit ceiling)  → zero out upward velocity.
#
# Doing X and Y separately avoids the common bug where moving into a corner
# causes the player to stick to walls or clip through floors.
# =============================================================================

from settings import GRAVITY, TERMINAL_VELOCITY
import pygame


def apply_gravity(entity) -> None:
    """Accelerate entity downward each frame, capped at terminal velocity.

    gravity_mult on the entity scales the pull — Marked players use 0.88 to
    feel slightly arcane-light; Fleshforged use 1.0 for full iron weight.
    """
    entity.vy += GRAVITY * getattr(entity, "gravity_mult", 1.0)
    if entity.vy > TERMINAL_VELOCITY:
        entity.vy = TERMINAL_VELOCITY


def move_and_collide(entity, solid_rects: list[pygame.Rect]) -> None:
    """
    Move entity by (vx, vy) and resolve collisions with solid_rects.
    Sets entity.on_ground = True when standing on a tile.
    """
    entity.on_ground = False

    # --- Horizontal ---
    entity.x += entity.vx
    entity.rect.x = int(entity.x)

    for tile in solid_rects:
        if entity.rect.colliderect(tile):
            if entity.vx > 0:          # Moving right → hit left face of tile
                entity.rect.right = tile.left
            elif entity.vx < 0:        # Moving left  → hit right face of tile
                entity.rect.left  = tile.right
            entity.vx = 0
            entity.x  = float(entity.rect.x)

    # --- Vertical ---
    entity.y += entity.vy
    entity.rect.y = int(entity.y)

    for tile in solid_rects:
        if entity.rect.colliderect(tile):
            if entity.vy > 0:          # Falling down → landed on top of tile
                entity.rect.bottom = tile.top
                entity.vy          = 0
                entity.on_ground   = True
            elif entity.vy < 0:        # Moving up → hit ceiling
                entity.rect.top    = tile.bottom
                entity.vy          = 0
            entity.y = float(entity.rect.y)
