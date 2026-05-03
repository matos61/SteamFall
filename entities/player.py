# =============================================================================
# entities/player.py — Player controller. Faction-aware.
#
# Controls:
#   Move       : A / D  or  LEFT / RIGHT arrows
#   Jump       : W / UP / SPACE
#   Attack     : Z  or  J
#   Faction Ability: X  or  K
#     Marked      → Soul Surge (area burst of arcane energy)
#     Fleshforged → Overdrive  (speed + damage boost for a few seconds)
#
# Visual placeholders:
#   The player is currently a colored rectangle.
#   When you add sprite sheets, replace the draw() logic in entity.py
#   and here with surface.blit(frame, screen_rect).
# =============================================================================

import pygame
from entities.entity     import Entity
from systems.combat      import AttackHitbox
from systems.animation   import AnimationController
from systems.audio       import audio
from settings import (
    PLAYER_SPEED, PLAYER_JUMP_FORCE, PLAYER_MAX_HEALTH,
    PLAYER_MAX_SOUL, PLAYER_MAX_HEAT, PLAYER_IFRAMES,
    PLAYER_ATTACK_DURATION, PLAYER_ATTACK_COOLDOWN,
    FACTION_MARKED, FACTION_FLESHFORGED, FRICTION,
    MARKED_COLOR, FLESHFORGED_COLOR, WHITE, GOLD,
    ATTACK_RECOIL_VX, WINDUP_FRAMES,
    MARKED_GRAVITY_MULT,  MARKED_AIR_CONTROL,  MARKED_FRICTION,
    MARKED_JUMP_MULT,     MARKED_JUMP_CUT,
    FLESHFORGED_GRAVITY_MULT, FLESHFORGED_AIR_CONTROL, FLESHFORGED_FRICTION,
    FLESHFORGED_JUMP_MULT,    FLESHFORGED_JUMP_CUT,
    ABILITY_SLOTS_DEFAULT,
    SPRITE_DIR_PLAYER,
)

ATTACK_DAMAGE    = 20
ATTACK_REACH     = 52    # Pixels the attack hitbox extends forward
ABILITY_COST     = 30    # Resource cost per ability use


class Player(Entity):
    def __init__(self, x: float, y: float, faction: str):
        color = MARKED_COLOR if faction == FACTION_MARKED else FLESHFORGED_COLOR
        super().__init__(x, y, width=30, height=54, color=color,
                         max_health=PLAYER_MAX_HEALTH)

        self.faction = faction

        # Faction resource bars
        self.soul = PLAYER_MAX_SOUL   # Marked mana (arcane energy)
        self.heat = PLAYER_MAX_HEAT   # Fleshforged fuel

        # Attack state
        self._attack_timer    = 0     # Counts down while attacking
        self._attack_cooldown = 0     # Counts down between attacks
        self._windup_timer    = 0     # Counts down during pre-attack windup (no hitbox)
        self.hitboxes: list[AttackHitbox] = []

        # Ability state
        self._ability_active   = False
        self._ability_timer    = 0
        self._ability_cooldown = 0

        # Overdrive (Fleshforged) modifier
        self._overdrive = False

        # Soul Surge (Marked) AOE hitboxes
        self._surge_hitboxes: list[AttackHitbox] = []

        # --- Feel improvements (Hollow Knight-style) ---
        # Coyote time: lets you jump for a few frames after walking off a ledge
        self._coyote_timer  = 0
        COYOTE_FRAMES       = 6   # frames of grace after leaving ground

        # Jump buffer: press jump just before landing and it fires on contact
        self._jump_buffer   = 0
        JUMP_BUFFER_FRAMES  = 8   # frames the buffered jump stays pending

        # Variable jump height: releasing the jump key early cuts upward velocity
        self._jump_held     = False

        # Store constants on self so _handle_movement can read them
        self._COYOTE_FRAMES      = COYOTE_FRAMES
        self._JUMP_BUFFER_FRAMES = JUMP_BUFFER_FRAMES

        # Death state — holds us in a death pose before switching scenes
        self.death_timer = 0

        # Landing dust: set > 0 on the frame the player lands
        self._land_timer = 0

        # P2-5 upgrade bonuses (additive; set from gameplay.py via save_data)
        self.attack_damage_bonus: int   = 0
        self.max_resource_bonus: float  = 0.0
        self._res_regen_bonus: float    = 0.0   # P2-8: per-"res"-upgrade additive regen boost

        # P1-8 / BUG-019: ability gate — restored from save_data by gameplay.py
        self.ability_slots: int = ABILITY_SLOTS_DEFAULT

        # Animation state machine
        self._anim = AnimationController(color, width=30, height=54,
                                         sprite_dir=SPRITE_DIR_PLAYER)

        # --- Faction-specific physics feel ---
        # Values pulled from settings so designers can tune without touching code.
        if faction == FACTION_MARKED:
            # Arcane agility: lighter gravity, full air precision, crisp stops
            self.gravity_mult    = MARKED_GRAVITY_MULT
            self._air_control    = MARKED_AIR_CONTROL
            self._faction_fric   = MARKED_FRICTION
            self._jump_force     = PLAYER_JUMP_FORCE * MARKED_JUMP_MULT
            self._jump_cut       = MARKED_JUMP_CUT
        else:
            # Iron body: full gravity, momentum-based, commits to direction
            self.gravity_mult    = FLESHFORGED_GRAVITY_MULT
            self._air_control    = FLESHFORGED_AIR_CONTROL
            self._faction_fric   = FLESHFORGED_FRICTION
            self._jump_force     = PLAYER_JUMP_FORCE * FLESHFORGED_JUMP_MULT
            self._jump_cut       = FLESHFORGED_JUMP_CUT

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def resource(self) -> float:
        """Current resource value (soul or heat depending on faction)."""
        return self.soul if self.faction == FACTION_MARKED else self.heat

    @property
    def max_resource(self) -> float:
        base = PLAYER_MAX_SOUL if self.faction == FACTION_MARKED else PLAYER_MAX_HEAT
        return base + self.max_resource_bonus

    def _spend_resource(self, amount: float) -> bool:
        """Deduct resource; return False if not enough."""
        if self.faction == FACTION_MARKED:
            if self.soul < amount:
                return False
            self.soul -= amount
        else:
            if self.heat < amount:
                return False
            self.heat -= amount
        return True

    def _regen_resource(self, amount: float) -> None:
        if self.faction == FACTION_MARKED:
            self.soul = min(self.soul + amount, self.max_resource)
        else:
            self.heat = min(self.heat + amount, self.max_resource)

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, dt: int, solid_rects=None) -> None:
        super().update(dt)

        if not self.alive:
            return

        keys = pygame.key.get_pressed()
        self.hitboxes.clear()
        self._surge_hitboxes.clear()

        # Track whether we were grounded BEFORE physics this frame
        # so coyote time can be set correctly
        was_on_ground = self.on_ground

        from systems.physics import apply_gravity, move_and_collide
        apply_gravity(self)
        if solid_rects:
            move_and_collide(self, solid_rects)

        # Landing detection — set dust timer on the frame we first touch ground
        if not was_on_ground and self.on_ground:
            self._land_timer = 10
            from systems.particles import particles
            particles.emit_landing(self.rect.centerx, self.rect.bottom)
        if self._land_timer > 0:
            self._land_timer -= 1

        # Coyote time: count down after leaving ground (walked off ledge)
        if was_on_ground and not self.on_ground:
            self._coyote_timer = self._COYOTE_FRAMES
        elif self._coyote_timer > 0:
            self._coyote_timer -= 1
        elif self.on_ground:
            self._coyote_timer = 0

        # Jump buffer: count down after pressing jump in the air
        if self._jump_buffer > 0:
            self._jump_buffer -= 1

        self._handle_movement(keys)
        self._handle_attack(keys)
        self._handle_ability(keys)
        self._tick_ability()
        self._regen_resource(0.05 + self._res_regen_bonus)   # Slow passive regen
        self._update_animation()

    # ------------------------------------------------------------------

    def _handle_movement(self, keys) -> None:
        # Windup locks movement — the fighter plants their feet to swing
        if self._windup_timer > 0:
            self.vx = 0
            return

        speed = PLAYER_SPEED * (1.6 if self._overdrive else 1.0)

        # Air control: Fleshforged have reduced steering in the air (momentum).
        # Marked have full control — arcane precision.
        if not self.on_ground:
            speed *= self._air_control

        # Slightly reduce speed mid-attack so swings have weight
        if self._attack_timer > 0:
            speed *= 0.55

        moving = False
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vx     = -speed
            self.facing = -1
            moving      = True
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vx     = speed
            self.facing = 1
            moving      = True

        if not moving:
            # Faction-specific friction: Marked stop crisply, Fleshforged slide
            self.vx *= self._faction_fric

        # --- Jump ---
        jump_pressed = keys[pygame.K_UP] or keys[pygame.K_w] or keys[pygame.K_SPACE]

        # Buffer the jump request so near-miss landings register
        if jump_pressed and not self._jump_held:
            self._jump_buffer = self._JUMP_BUFFER_FRAMES

        # Consume buffered jump when grounded or within coyote window
        can_jump = self.on_ground or self._coyote_timer > 0
        if self._jump_buffer > 0 and can_jump:
            self.vy             = self._jump_force   # Faction-scaled jump arc
            self._jump_buffer   = 0
            self._coyote_timer  = 0
            self._jump_held     = True
            audio.play_sfx("jump")

        # Variable jump height: releasing jump early cuts the arc.
        # Marked cut is gentle (floatier short hop).
        # Fleshforged cut is sharp (committed arc or nothing).
        # Variable jump height: releasing jump early cuts the arc.
        # Guard with _jump_held so knockback arcs are NOT dampened.
        if not jump_pressed and self._jump_held and self.vy < -4:
            self.vy *= self._jump_cut   # Faction-tuned dampening

        # Clear _jump_held once the key is released or the player lands
        if not jump_pressed and self._jump_held:
            self._jump_held = False

        # Reset jump_held when we land so the next press works
        if self.on_ground and not jump_pressed:
            self._jump_held = False

    # ------------------------------------------------------------------

    def _handle_attack(self, keys) -> None:
        if self._attack_cooldown > 0:
            self._attack_cooldown -= 1

        # --- Windup phase: brief telegraph before hitbox becomes active ---
        if self._windup_timer > 0:
            self._windup_timer -= 1
            if self._windup_timer == 0:
                # Windup finished — now start the real attack
                self._attack_timer = PLAYER_ATTACK_DURATION
            return

        if self._attack_timer > 0:
            self._attack_timer -= 1
            # Create hitbox while timer is active (first 2/3 of duration)
            if self._attack_timer > PLAYER_ATTACK_DURATION // 3:
                dmg    = int((ATTACK_DAMAGE + self.attack_damage_bonus) * (1.3 if self._overdrive else 1.0))
                hx     = (self.rect.right if self.facing == 1
                           else self.rect.left - ATTACK_REACH)
                hrect  = pygame.Rect(hx, self.rect.top + 10,
                                     ATTACK_REACH, self.rect.height - 20)
                self.hitboxes.append(
                    AttackHitbox(hrect, damage=dmg, owner=self,
                                 knockback_x=5.0, knockback_y=-3.0,
                                 duration=1))
            return

        if (keys[pygame.K_z] or keys[pygame.K_j]) and self._attack_cooldown == 0:
            # Nail recoil: push player back opposite the swing direction
            self.vx = -self.facing * ATTACK_RECOIL_VX
            # Begin windup telegraph before hitbox activates
            self._windup_timer    = WINDUP_FRAMES
            self._attack_cooldown = PLAYER_ATTACK_COOLDOWN
            audio.play_sfx("attack")

    # ------------------------------------------------------------------

    def _handle_ability(self, keys) -> None:
        if self.ability_slots < 1:
            return
        if self._ability_cooldown > 0:
            self._ability_cooldown -= 1
            return

        if not (keys[pygame.K_x] or keys[pygame.K_k]):
            return

        if self.faction == FACTION_MARKED:
            self._activate_soul_surge()
        else:
            self._activate_overdrive()

    def _activate_soul_surge(self) -> None:
        """Marked ability: burst of arcane force in all directions."""
        if not self._spend_resource(ABILITY_COST):
            return
        self._ability_cooldown = 90
        audio.play_sfx("ability")
        from systems.particles import particles
        particles.emit_soul_surge(self.rect.centerx, self.rect.centery)
        # Create four outward hitboxes (up, down, left, right)
        cx, cy = self.rect.center
        size   = 80
        for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
            hrect = pygame.Rect(cx + dx*20 - size//2,
                                cy + dy*20 - size//2,
                                size, size)
            self._surge_hitboxes.append(
                AttackHitbox(hrect, damage=35, owner=self,
                             knockback_x=7.0, knockback_y=-5.0,
                             duration=12))

    def _activate_overdrive(self) -> None:
        """Fleshforged ability: speed + damage boost for 3 seconds."""
        if not self._spend_resource(ABILITY_COST):
            return
        audio.play_sfx("ability")
        from systems.particles import particles
        particles.emit_overdrive(self.rect.centerx, self.rect.centery)
        self._overdrive        = True
        self._ability_active   = True
        self._ability_timer    = 180   # 3 seconds at 60 fps
        self._ability_cooldown = 240

    def _tick_ability(self) -> None:
        if self._ability_active:
            self._ability_timer -= 1
            if self._ability_timer <= 0:
                self._ability_active = False
                self._overdrive      = False

    # ------------------------------------------------------------------
    # Animation state selection
    # ------------------------------------------------------------------

    def _update_animation(self) -> None:
        if not self.alive:
            self._anim.set_state("death")
        elif self.iframes == PLAYER_IFRAMES:
            self._anim.set_state("hurt")
        elif self._windup_timer > 0 or self._attack_timer > 0:
            self._anim.set_state("attack")
        elif not self.on_ground and self.vy < 0:
            self._anim.set_state("jump")
        elif not self.on_ground and self.vy > 0:
            self._anim.set_state("fall")
        elif abs(self.vx) > 0.5:
            self._anim.set_state("walk")
        else:
            self._anim.set_state("idle")
        self._anim.update()

    # ------------------------------------------------------------------
    # All active hitboxes (attack + ability combined) for gameplay.py
    # ------------------------------------------------------------------
    def all_hitboxes(self) -> list:
        return self.hitboxes + self._surge_hitboxes

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------

    def draw(self, surface: pygame.Surface, camera) -> None:
        screen_rect = camera.apply(self)

        # Blit the animation frame (scaled to the entity rect)
        frame = self._anim.current_frame
        if frame.get_size() != (screen_rect.width, screen_rect.height):
            frame = pygame.transform.scale(frame,
                                           (screen_rect.width, screen_rect.height))
        surface.blit(frame, screen_rect.topleft)

        # Override color tints for special states (drawn on top via rect outline)
        if self.iframes > 0 and self.iframes % 4 < 2:
            # Bright white outline during iframes
            pygame.draw.rect(surface, (230, 230, 230), screen_rect, 2)
        elif self._overdrive:
            pygame.draw.rect(surface, (255, 160, 40), screen_rect, 2)

        # Eyes (simple directional indicator)
        eye_x = screen_rect.right - 8 if self.facing == 1 else screen_rect.left + 4
        pygame.draw.circle(surface, WHITE, (eye_x, screen_rect.top + 14), 4)
        pygame.draw.circle(surface, (0, 0, 0), (eye_x, screen_rect.top + 14), 2)

        # Attack arc (visual feedback — thin rect in swing direction)
        # During windup, draw a dim "charging" glow; during active swing, full arc
        if self._windup_timer > 0:
            arc_x = screen_rect.right if self.facing == 1 else screen_rect.left - 18
            arc_rect = pygame.Rect(arc_x, screen_rect.top + 12, 18, screen_rect.height - 24)
            arc_surf = pygame.Surface((arc_rect.width, arc_rect.height), pygame.SRCALPHA)
            # Grow from dim to bright over the windup window
            frac = 1.0 - self._windup_timer / WINDUP_FRAMES
            alpha = int(60 + 80 * frac)
            arc_surf.fill((*GOLD, alpha))
            surface.blit(arc_surf, arc_rect.topleft)
        elif self._attack_timer > PLAYER_ATTACK_DURATION // 3:
            arc_x = screen_rect.right if self.facing == 1 else screen_rect.left - 18
            arc_rect = pygame.Rect(arc_x, screen_rect.top + 12, 18, screen_rect.height - 24)
            arc_surf = pygame.Surface((arc_rect.width, arc_rect.height), pygame.SRCALPHA)
            alpha = int(200 * self._attack_timer / PLAYER_ATTACK_DURATION)
            arc_surf.fill((*GOLD, alpha))
            surface.blit(arc_surf, arc_rect.topleft)

        # Landing dust puff — two small fading marks at ground level
        if self._land_timer > 0:
            alpha    = int(160 * self._land_timer / 10)
            dust_w   = screen_rect.width + 14
            dust_h   = 3
            dust_y   = screen_rect.bottom - 1
            dust_x   = screen_rect.left - 7
            dust_s   = pygame.Surface((dust_w, dust_h), pygame.SRCALPHA)
            dust_col = (180, 175, 200, alpha)
            # Two short marks spread outward from the center
            hw = dust_w // 3
            pygame.draw.rect(dust_s, dust_col, (0,        0, hw, dust_h))
            pygame.draw.rect(dust_s, dust_col, (dust_w - hw, 0, hw, dust_h))
            surface.blit(dust_s, (dust_x, dust_y))

        # Soul surge rings
        for hb in self._surge_hitboxes:
            sr = camera.apply_rect(hb.rect)
            ring_surf = pygame.Surface((sr.width, sr.height), pygame.SRCALPHA)
            ring_surf.fill((*MARKED_COLOR, 80))
            surface.blit(ring_surf, sr.topleft)
            pygame.draw.rect(surface, MARKED_COLOR, sr, 2)
