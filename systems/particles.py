"""Lightweight particle system for visual effects (hit sparks, death bursts, landing dust, etc.).

Usage:
    from systems.particles import particles   # module-level singleton
    particles.emit_hit(x, y, color, facing)
    particles.update()           # once per frame inside hitstop guard
    particles.draw(surface, camera)
    particles.clear()            # call on scene load / level change
"""

import math
import random
import pygame
from settings import (SCREEN_WIDTH, SCREEN_HEIGHT,
                      PARTICLE_GRAVITY, PARTICLE_FRICTION,
                      HIT_PARTICLE_COUNT, HIT_PARTICLE_LIFE,
                      DEATH_PARTICLE_COUNT, DEATH_PARTICLE_LIFE,
                      LANDING_PARTICLE_COUNT, LANDING_PARTICLE_LIFE, LANDING_PARTICLE_COLOR,
                      SOUL_SURGE_PARTICLE_COUNT, SOUL_SURGE_PARTICLE_COLOR,
                      OVERDRIVE_PARTICLE_COUNT, OVERDRIVE_PARTICLE_COLOR,
                      CHECKPOINT_PARTICLE_COUNT, CHECKPOINT_PARTICLE_COLOR)


class Particle:
    __slots__ = ("x", "y", "vx", "vy", "color", "lifetime", "max_lifetime",
                 "size", "_gravity")

    def __init__(self, x: float, y: float, vx: float, vy: float,
                 color: tuple, lifetime: int, size: int = 3, gravity: bool = True):
        self.x            = float(x)
        self.y            = float(y)
        self.vx           = float(vx)
        self.vy           = float(vy)
        self.color        = color
        self.lifetime     = lifetime
        self.max_lifetime = lifetime
        self.size         = size
        self._gravity     = gravity

    def update(self) -> None:
        if self._gravity:
            self.vy += PARTICLE_GRAVITY
        self.x  += self.vx
        self.y  += self.vy
        self.vx *= PARTICLE_FRICTION
        self.lifetime -= 1

    @property
    def alive(self) -> bool:
        return self.lifetime > 0


class ParticleSystem:
    def __init__(self):
        self._particles: list = []

    # ------------------------------------------------------------------
    # Generic emitter (P4-1 spec interface)
    # ------------------------------------------------------------------

    def emit(self, x: float, y: float, count: int, speed: float,
             color: tuple, life: int, spread: int = 360) -> None:
        """Spawn `count` particles at (x, y) in random directions within `spread` degrees.

        Each particle gets a random angle within the spread cone centred straight up
        (−90° / −π/2) when spread < 360, or fully random when spread == 360.
        Velocity magnitude = random(0.5, 1.0) * speed.
        """
        half_rad = math.radians(spread) / 2.0
        for _ in range(count):
            if spread >= 360:
                angle = random.uniform(0.0, math.pi * 2.0)
            else:
                # Centre cone pointing upward (−π/2 = straight up)
                centre = -math.pi / 2.0
                angle  = centre + random.uniform(-half_rad, half_rad)
            mag = random.uniform(0.5, 1.0) * speed
            vx  = math.cos(angle) * mag
            vy  = math.sin(angle) * mag
            self._particles.append(Particle(x, y, vx, vy, color, life))

    # ------------------------------------------------------------------
    # Emission presets
    # ------------------------------------------------------------------

    def emit_hit(self, x: float, y: float, color: tuple, facing: int = 1) -> None:
        """Sparks that fly away from a hit connection point (nail sparks).

        Uses spec constants: HIT_PARTICLE_COUNT sparks, HIT_PARTICLE_LIFE frames.
        """
        for _ in range(HIT_PARTICLE_COUNT):
            # Arc facing the attacker's direction, spread ±90° around forward
            base  = 0.0 if facing == 1 else math.pi
            angle = base + random.uniform(-math.pi * 0.7, math.pi * 0.7)
            speed = random.uniform(2.5, 5.5)
            vx    = math.cos(angle) * speed
            vy    = math.sin(angle) * speed - 1.0   # slight upward bias
            lt    = HIT_PARTICLE_LIFE
            size  = random.randint(2, 4)
            self._particles.append(Particle(x, y, vx, vy, color, lt, size))

    def emit_death(self, x: float, y: float, color: tuple) -> None:
        """Radial burst of particles when an entity dies.

        Uses spec constants: DEATH_PARTICLE_COUNT burst, DEATH_PARTICLE_LIFE frames.
        """
        for _ in range(DEATH_PARTICLE_COUNT):
            angle = random.uniform(0.0, math.pi * 2.0)
            speed = random.uniform(1.5, 6.0)
            vx    = math.cos(angle) * speed
            vy    = math.sin(angle) * speed
            lt    = DEATH_PARTICLE_LIFE
            size  = random.randint(2, 5)
            self._particles.append(Particle(x, y, vx, vy, color, lt, size))

    def emit_landing(self, x: float, y: float) -> None:
        """Dust puffs that scatter sideways when the player lands.

        Uses spec: LANDING_PARTICLE_COUNT puffs split left/right, LANDING_PARTICLE_COLOR.
        Half scatter leftward, half rightward, per the spec's split-direction requirement.
        """
        half = max(1, LANDING_PARTICLE_COUNT // 2)
        for i in range(LANDING_PARTICLE_COUNT):
            # Alternate left/right halves
            direction = -1 if i < half else 1
            vx   = direction * random.uniform(0.5, 2.0)
            vy   = random.uniform(-2.5, -0.5)
            lt   = LANDING_PARTICLE_LIFE
            size = random.randint(2, 4)
            self._particles.append(
                Particle(x, y, vx, vy, LANDING_PARTICLE_COLOR, lt, size, gravity=False))

    def emit_soul_surge(self, x: float, y: float) -> None:
        """Purple shards expanding outward when Soul Surge is activated.

        Uses spec: SOUL_SURGE_PARTICLE_COUNT burst, SOUL_SURGE_PARTICLE_COLOR.
        """
        for _ in range(SOUL_SURGE_PARTICLE_COUNT):
            angle = random.uniform(0.0, math.pi * 2.0)
            speed = random.uniform(2.0, 7.0)
            vx    = math.cos(angle) * speed
            vy    = math.sin(angle) * speed
            lt    = random.randint(20, 30)
            size  = random.randint(2, 5)
            self._particles.append(
                Particle(x, y, vx, vy, SOUL_SURGE_PARTICLE_COLOR, lt, size, gravity=False))

    def emit_overdrive(self, x: float, y: float) -> None:
        """Heat shimmer rising upward when Overdrive is activated.

        Uses spec: OVERDRIVE_PARTICLE_COUNT burst, OVERDRIVE_PARTICLE_COLOR, upward spread.
        """
        for _ in range(OVERDRIVE_PARTICLE_COUNT):
            vx   = random.uniform(-3.5, 3.5)
            vy   = random.uniform(-6.0, -1.5)
            lt   = random.randint(14, 22)
            size = random.randint(2, 4)
            self._particles.append(
                Particle(x, y, vx, vy, OVERDRIVE_PARTICLE_COLOR, lt, size, gravity=False))

    def emit_checkpoint(self, x: float, y: float) -> None:
        """Golden embers rising when a checkpoint is activated.

        Uses spec: CHECKPOINT_PARTICLE_COUNT embers, CHECKPOINT_PARTICLE_COLOR, upward.
        """
        for _ in range(CHECKPOINT_PARTICLE_COUNT):
            vx   = random.uniform(-2.0, 2.0)
            vy   = random.uniform(-5.5, -0.8)
            lt   = random.randint(28, 37)   # ≈ spec's 35 frames
            size = random.randint(2, 4)
            self._particles.append(
                Particle(x, y, vx, vy, CHECKPOINT_PARTICLE_COLOR, lt, size, gravity=True))

    # ------------------------------------------------------------------

    def update(self) -> None:
        for p in self._particles:
            p.update()
        self._particles = [p for p in self._particles if p.alive]

    def draw(self, surface: pygame.Surface, camera) -> None:
        for p in self._particles:
            sx, sy = camera.apply_point(p.x, p.y)
            sx, sy = int(sx), int(sy)
            if sx < -p.size or sx > SCREEN_WIDTH + p.size:
                continue
            if sy < -p.size or sy > SCREEN_HEIGHT + p.size:
                continue
            # Fade color to black as lifetime runs out
            frac  = p.lifetime / p.max_lifetime
            color = (int(p.color[0] * frac),
                     int(p.color[1] * frac),
                     int(p.color[2] * frac))
            half = p.size // 2
            pygame.draw.rect(surface, color, (sx - half, sy - half, p.size, p.size))

    def clear(self) -> None:
        """Discard all particles — call when loading a new level."""
        self._particles.clear()


# Module-level singleton, mirroring the `hitstop` singleton pattern.
particles = ParticleSystem()
