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
from settings import (SCREEN_WIDTH, SCREEN_HEIGHT, GOLD, SOUL_COLOR, HEAT_COLOR,
                      PARTICLE_GRAVITY, PARTICLE_DRAG,
                      PARTICLE_HIT_COUNT, PARTICLE_DEATH_COUNT,
                      PARTICLE_LAND_COUNT, PARTICLE_ABILITY_COUNT,
                      PARTICLE_CHECKPOINT_COUNT, PARTICLE_DUST_COLOR)


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
        self.vx *= PARTICLE_DRAG
        self.lifetime -= 1

    @property
    def alive(self) -> bool:
        return self.lifetime > 0


class ParticleSystem:
    def __init__(self):
        self._particles: list = []

    # ------------------------------------------------------------------
    # Emission presets
    # ------------------------------------------------------------------

    def emit_hit(self, x: float, y: float, color: tuple, facing: int = 1) -> None:
        """Sparks that fly away from a hit connection point (nail sparks)."""
        for _ in range(PARTICLE_HIT_COUNT):
            # Arc facing the attacker's direction, spread ±90° around forward
            base  = 0.0 if facing == 1 else math.pi
            angle = base + random.uniform(-math.pi * 0.7, math.pi * 0.7)
            speed = random.uniform(2.5, 5.5)
            vx    = math.cos(angle) * speed
            vy    = math.sin(angle) * speed - 1.0   # slight upward bias
            lt    = random.randint(8, 16)
            size  = random.randint(2, 4)
            self._particles.append(Particle(x, y, vx, vy, color, lt, size))

    def emit_death(self, x: float, y: float, color: tuple) -> None:
        """Radial burst of particles when an entity dies."""
        for _ in range(PARTICLE_DEATH_COUNT):
            angle = random.uniform(0.0, math.pi * 2.0)
            speed = random.uniform(1.5, 6.0)
            vx    = math.cos(angle) * speed
            vy    = math.sin(angle) * speed
            lt    = random.randint(18, 35)
            size  = random.randint(2, 5)
            self._particles.append(Particle(x, y, vx, vy, color, lt, size))

    def emit_landing(self, x: float, y: float) -> None:
        """Dust puffs that scatter sideways when the player lands."""
        for _ in range(PARTICLE_LAND_COUNT):
            vx   = random.uniform(-3.0, 3.0)
            vy   = random.uniform(-2.5, -0.5)
            lt   = random.randint(8, 18)
            size = random.randint(2, 4)
            self._particles.append(
                Particle(x, y, vx, vy, PARTICLE_DUST_COLOR, lt, size, gravity=False))

    def emit_soul_surge(self, x: float, y: float) -> None:
        """Purple shards expanding outward when Soul Surge is activated."""
        for _ in range(PARTICLE_ABILITY_COUNT):
            angle = random.uniform(0.0, math.pi * 2.0)
            speed = random.uniform(2.0, 7.0)
            vx    = math.cos(angle) * speed
            vy    = math.sin(angle) * speed
            lt    = random.randint(20, 38)
            size  = random.randint(2, 5)
            self._particles.append(
                Particle(x, y, vx, vy, SOUL_COLOR, lt, size, gravity=False))

    def emit_overdrive(self, x: float, y: float) -> None:
        """Heat shimmer rising upward when Overdrive is activated."""
        for _ in range(PARTICLE_ABILITY_COUNT):
            vx   = random.uniform(-3.5, 3.5)
            vy   = random.uniform(-6.0, -1.5)
            lt   = random.randint(14, 26)
            size = random.randint(2, 4)
            self._particles.append(
                Particle(x, y, vx, vy, HEAT_COLOR, lt, size, gravity=False))

    def emit_checkpoint(self, x: float, y: float) -> None:
        """Golden embers rising when a checkpoint is activated."""
        for _ in range(PARTICLE_CHECKPOINT_COUNT):
            vx   = random.uniform(-2.0, 2.0)
            vy   = random.uniform(-5.5, -0.8)
            lt   = random.randint(28, 65)
            size = random.randint(2, 4)
            self._particles.append(
                Particle(x, y, vx, vy, GOLD, lt, size, gravity=True))

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
