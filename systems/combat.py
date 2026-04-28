# =============================================================================
# systems/combat.py — Attack hitboxes, damage, knockback, iframes.
#
# How combat works:
#   • When a player or enemy attacks, create an AttackHitbox for a few frames.
#   • Each frame: check if the hitbox overlaps any valid targets.
#   • If it does: deal damage, apply knockback, give the target iframes.
#   • Iframes (invincibility frames) prevent being hit multiple times from
#     the same attack, and give the player a short window to escape.
# =============================================================================

import pygame
from core.hitstop import hitstop
from settings import FACTION_MARKED
from systems.particles import particles
from systems.audio import audio


class AttackHitbox:
    """
    A temporary rectangle that deals damage to entities it touches.
    Created by the player or an enemy, lives for `duration` frames, then gone.
    """
    def __init__(self, rect: pygame.Rect, damage: int, owner,
                 knockback_x: float = 4.0, knockback_y: float = -3.0,
                 duration: int = 10):
        self.rect        = rect.copy()
        self.damage      = damage
        self.owner       = owner          # The entity that created this hitbox
        self.knockback_x = knockback_x    # Horizontal knockback force
        self.knockback_y = knockback_y    # Vertical knockback force (negative = up)
        self.duration    = duration
        self.alive       = True
        self._already_hit: set = set()    # Track who was already hit this swing

    def update(self) -> None:
        self.duration -= 1
        if self.duration <= 0:
            self.alive = False

    def check_hits(self, targets: list) -> None:
        """
        Test this hitbox against a list of target entities.
        Deals damage + knockback to each target hit (once per swing).
        """
        if not self.alive:
            return
        for target in targets:
            if target is self.owner:
                continue                  # Can't hit yourself
            if id(target) in self._already_hit:
                continue                  # Already hit this target this swing
            if not target.alive:
                continue
            if self.rect.colliderect(target.rect):
                self._apply_hit(target)

    def _apply_hit(self, target) -> None:
        self._already_hit.add(id(target))
        target.take_damage(self.damage)

        # Knockback direction depends on relative positions
        direction = 1 if target.rect.centerx >= self.owner.rect.centerx else -1
        target.vx = direction * self.knockback_x
        target.vy = self.knockback_y

        # Marked faction: soul regen on confirmed hit (not on missed swings)
        if (hasattr(self, 'owner') and hasattr(self.owner, 'faction')
                and self.owner.faction == FACTION_MARKED):
            self.owner._regen_resource(3)

        # Nail sparks fly from the point of contact
        hit_x = (self.rect.centerx + target.rect.centerx) // 2
        hit_y = target.rect.centery
        particles.emit_hit(hit_x, hit_y, target.color, direction)
        audio.play_sfx("hit")

        # Hit-stop: freeze game for 4 frames so hits feel punchy
        hitstop.trigger(4)
