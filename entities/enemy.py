# =============================================================================
# entities/enemy.py — Basic patrol + chase enemy.
#
# Behaviour state machine:
#   PATROL → walks back and forth between left_limit and right_limit.
#   CHASE  → moves toward the player when they enter sight range.
#   ATTACK → stops and deals damage when the player is in melee range.
#
# To create a new enemy type later, subclass Enemy and override
# _update_ai() with different behaviour.
# =============================================================================

import pygame
from entities.entity   import Entity
from systems.combat    import AttackHitbox
from settings          import (ENEMY_PATROL_SPEED, ENEMY_CHASE_SPEED,
                                ENEMY_SIGHT_RANGE, ENEMY_ATTACK_RANGE,
                                ENEMY_ATTACK_DAMAGE, FLESHFORGED_COLOR, RED,
                                ENEMY_IFRAMES,
                                FACTION_FLESHFORGED, FACTION_MARKED,
                                FACTION_TINT_BLEND, FLESHFORGED_TINT_COLOR,
                                MARKED_TINT_COLOR, SPRITE_DIR_ENEMY)

# AI states
_PATROL = "patrol"
_CHASE  = "chase"
_ATTACK = "attack"


class Enemy(Entity):
    def __init__(self, x: float, y: float,
                 patrol_range: int = 160,
                 color: tuple = (160, 45, 45)):
        super().__init__(x, y, width=36, height=52, color=color, max_health=60)

        # Patrol boundaries
        self.left_limit  = x - patrol_range
        self.right_limit = x + patrol_range

        self._state           = _PATROL
        self._patrol_dir      = 1          # +1 right, -1 left
        self._attack_cooldown = 0
        self._iframes_on_hit  = ENEMY_IFRAMES   # Shorter than player iframes → combos work

        # Hitboxes spawned this frame (cleared after checking)
        self.hitboxes: list[AttackHitbox] = []

        # Faction-specific drop type (set in subclass __init__ as needed)
        # "" → neutral SoulFragment; FACTION_FLESHFORGED → HeatCore; FACTION_MARKED → SoulShard
        self.faction_drop: str = ""

        # Visual tint applied in levels with strong faction theming (P3-2)
        # "" → no tint; FACTION_FLESHFORGED → iron-orange blend; FACTION_MARKED → acolyte purple blend
        self.faction_tint: str = ""

        # Animation controller (P4-6) — lazily initialised on first update() call
        # so subclasses that override self.rect dimensions are always handled correctly.
        self._anim = None

    # ------------------------------------------------------------------

    def update(self, dt: int, player=None, solid_rects=None) -> None:
        super().update(dt)

        if not self.alive:
            return

        self._attack_cooldown = max(0, self._attack_cooldown - 1)
        self.hitboxes.clear()

        if player and player.alive:
            self._update_ai(player)

        # Import here to avoid circular imports at module load time
        from systems.physics import apply_gravity, move_and_collide
        apply_gravity(self)
        if solid_rects:
            move_and_collide(self, solid_rects)

        # P4-6: lazily init AnimationController on first update using final rect dims
        if self._anim is None:
            from systems.animation import AnimationController
            self._anim = AnimationController(
                self.color, self.rect.width, self.rect.height,
                sprite_dir=SPRITE_DIR_ENEMY)
        if self.iframes > 0:
            self._anim.set_state("hurt")
        elif self._state == _ATTACK:
            self._anim.set_state("attack")
        elif abs(self.vx) > 0.1:
            self._anim.set_state("walk")
        else:
            self._anim.set_state("idle")
        self._anim.update()

    # ------------------------------------------------------------------

    def _update_ai(self, player) -> None:
        dist_x = abs(player.rect.centerx - self.rect.centerx)
        dist_y = abs(player.rect.centery - self.rect.centery)

        # Only react to player on roughly the same vertical level
        in_vertical_range = dist_y < 80

        if dist_x <= ENEMY_ATTACK_RANGE and in_vertical_range:
            self._state = _ATTACK
        elif dist_x <= ENEMY_SIGHT_RANGE and in_vertical_range:
            self._state = _CHASE
        else:
            self._state = _PATROL

        if self._state == _PATROL:
            self._do_patrol()
        elif self._state == _CHASE:
            self._do_chase(player)
        elif self._state == _ATTACK:
            self._do_attack(player)

    # ------------------------------------------------------------------

    def _do_patrol(self) -> None:
        self.vx = self._patrol_dir * ENEMY_PATROL_SPEED
        self.facing = self._patrol_dir

        # Reverse at patrol limits
        if self.rect.right >= self.right_limit:
            self._patrol_dir = -1
        elif self.rect.left <= self.left_limit:
            self._patrol_dir = 1

    def _do_chase(self, player) -> None:
        direction = 1 if player.rect.centerx > self.rect.centerx else -1
        self.vx     = direction * ENEMY_CHASE_SPEED
        self.facing = direction

    def _do_attack(self, player) -> None:
        self.vx = 0   # Stop while attacking

        if self._attack_cooldown > 0:
            return

        self._attack_cooldown = 60   # One attack per second

        # Build hitbox extending in the facing direction
        direction = 1 if player.rect.centerx > self.rect.centerx else -1
        self.facing = direction
        hx = (self.rect.right if direction == 1 else
              self.rect.left - ENEMY_ATTACK_RANGE)
        hitbox_rect = pygame.Rect(hx, self.rect.top + 8,
                                  ENEMY_ATTACK_RANGE, self.rect.height - 16)
        self.hitboxes.append(
            AttackHitbox(hitbox_rect, damage=ENEMY_ATTACK_DAMAGE,
                         owner=self, knockback_x=3.5, knockback_y=-2.5,
                         duration=8))

    # ------------------------------------------------------------------

    def get_drop_fragments(self) -> list:
        """Return collectibles to spawn when this enemy dies.

        The drop type depends on self.faction_drop:
          FACTION_FLESHFORGED → one HeatCore
          FACTION_MARKED      → one SoulShard
          ""  (default)       → one SoulFragment (neutral / resource orb)
        """
        cx, cy = self.rect.centerx, self.rect.centery
        if self.faction_drop == FACTION_FLESHFORGED:
            from systems.collectible import HeatCore
            return [HeatCore(cx, cy)]
        if self.faction_drop == FACTION_MARKED:
            from systems.collectible import SoulShard
            return [SoulShard(cx, cy)]
        from systems.collectible import SoulFragment
        return [SoulFragment(cx, cy)]

    def draw(self, surface: pygame.Surface, camera) -> None:
        # P4-6: ensure controller exists (fallback if update() was somehow skipped)
        if self._anim is None:
            from systems.animation import AnimationController
            self._anim = AnimationController(
                self.color, self.rect.width, self.rect.height,
                sprite_dir=SPRITE_DIR_ENEMY)

        screen_rect = camera.apply(self)

        # Hit flash: solid red fill replaces the frame during iframes (2-frame strobe)
        if self.iframes > 0 and self.iframes % 4 < 2:
            pygame.draw.rect(surface, RED, screen_rect)
        else:
            frame = self._anim.current_frame
            if frame.get_size() != (screen_rect.width, screen_rect.height):
                frame = pygame.transform.scale(
                    frame, (screen_rect.width, screen_rect.height))
            # P3-2: faction tint — blend the frame toward the tint color via
            # a semi-transparent overlay (equivalent to the previous per-channel
            # lerp at weight FACTION_TINT_BLEND for placeholder solid-color frames,
            # and a natural tint overlay for real sprites).
            if self.faction_tint:
                tint = (FLESHFORGED_TINT_COLOR if self.faction_tint == FACTION_FLESHFORGED
                        else MARKED_TINT_COLOR)
                frame = frame.copy()
                tint_surf = pygame.Surface(frame.get_size(), pygame.SRCALPHA)
                tint_surf.fill((*tint, int(255 * FACTION_TINT_BLEND)))
                frame.blit(tint_surf, (0, 0))
            surface.blit(frame, screen_rect.topleft)

        # Health bar (shown when below max health)
        if self.health < self.max_health and self.max_health > 0:
            bw = screen_rect.width
            bh = 5
            bx = screen_rect.x
            by = screen_rect.y - 10
            filled = int(bw * self.health / self.max_health)
            pygame.draw.rect(surface, (60, 10, 10),  (bx, by, bw, bh))
            pygame.draw.rect(surface, (200, 40, 40), (bx, by, filled, bh))
