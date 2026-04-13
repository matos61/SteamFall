# =============================================================================
# systems/tutorial_minigame.py — Inline control tutorial played during prologues.
#
# Usage (from a prologue scene):
#   tut = TutorialMinigame('move', 'Reach for it.', FACTION_MARKED)
#   # Each frame while active:
#   tut.handle_event(event)   # in handle_event
#   tut.update()              # in update
#   tut.draw(surface)         # in draw (drawn over background, before dialogue)
#   # When tut.is_complete() → True, the scene advances to the next beat.
#
# Goal types:
#   'move'                — walk right to reach a collectible
#   'jump'                — jump a gap to reach a collectible on the far platform
#   'attack'              — walk close to a dummy target and press Z
#   'ability_marked'      — press X to trigger Soul Surge
#   'ability_fleshforged' — press X to trigger Overdrive
# =============================================================================

import pygame
from settings import (SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, GOLD,
                      MARKED_COLOR, FLESHFORGED_COLOR, FACTION_MARKED)

# Physics constants for the mini-stage (tuned independently of game physics)
_GRAVITY   = 0.65
_JUMP_VY   = -11.5
_SPEED     = 4.2
_ATK_REACH = 44    # pixels the swing hitbox extends forward


class TutorialMinigame:
    # Stage dimensions
    STAGE_W  = 520
    STAGE_H  = 200
    GROUND_H = 30
    # Mini-player dimensions
    PW = 22
    PH = 38

    def __init__(self, goal_type: str, prompt: str, faction: str):
        self.goal_type = goal_type
        self.prompt    = prompt
        self.faction   = faction
        self._accent   = MARKED_COLOR if faction == FACTION_MARKED else FLESHFORGED_COLOR
        self._done     = False

        # Stage rect — centered on screen
        sx = (SCREEN_WIDTH  - self.STAGE_W) // 2
        sy = (SCREEN_HEIGHT - self.STAGE_H) // 2 + 20
        self._stage = pygame.Rect(sx, sy, self.STAGE_W, self.STAGE_H)

        # Ground level y-coordinate
        ground_y = sy + self.STAGE_H - self.GROUND_H

        # Platform geometry
        if goal_type == 'jump':
            # Left platform + 80px gap + right platform
            left_w  = 200
            right_x = sx + left_w + 80
            right_w = self.STAGE_W - left_w - 80
            self._platforms = [
                pygame.Rect(sx,      ground_y, left_w,  self.GROUND_H),
                pygame.Rect(right_x, ground_y, right_w, self.GROUND_H),
            ]
        else:
            self._platforms = [pygame.Rect(sx, ground_y, self.STAGE_W, self.GROUND_H)]

        # Mini player state
        self._px: float = float(sx + 40)
        self._py: float = float(ground_y - self.PH)
        self._pvx: float = 0.0
        self._pvy: float = 0.0
        self._on_ground:  bool = True
        self._facing:     int  = 1     # always starts facing right
        self._jump_queued: bool = False

        # Attack state
        self._atk_timer  = 0
        self._atk_done   = False

        # Ability state
        self._abi_used   = False
        self._abi_flash  = 0   # counts down for visual burst

        # Collected / hit flags for items / dummies
        self._target_hit = False

        # Success flash
        self._flash = 0

        # Blink timer for hint
        self._blink = 0

        # --- Place target based on goal ---
        ground_top = ground_y  # top surface of the ground rect(s)

        if goal_type == 'move':
            # Collectible near the far right of stage
            tx = sx + self.STAGE_W - 42
            ty = ground_top - 26
            self._target = pygame.Rect(tx, ty, 24, 26)

        elif goal_type == 'jump':
            # Collectible on the right platform
            right_plat = self._platforms[1]
            tx = right_plat.right - 38
            ty = right_plat.top - 26
            self._target = pygame.Rect(tx, ty, 24, 26)

        elif goal_type == 'attack':
            # Dummy target — player walks up and swings
            tx = sx + 200
            ty = ground_top - 40
            self._target = pygame.Rect(tx, ty, 28, 40)

        else:
            # ability_* — no physical target
            self._target = None

        # Fonts
        pygame.font.init()
        self._font_prompt = pygame.font.SysFont("georgia",   20)
        self._font_hint   = pygame.font.SysFont("monospace", 14)
        self._font_done   = pygame.font.SysFont("georgia",   28, bold=True)
        self._font_small  = pygame.font.SysFont("monospace", 12)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> None:
        if self._done:
            return
        if event.type != pygame.KEYDOWN:
            return

        # Jump (keydown so it doesn't auto-repeat weirdly)
        if event.key in (pygame.K_w, pygame.K_UP, pygame.K_SPACE):
            if self._on_ground and self.goal_type == 'jump':
                self._pvy = _JUMP_VY
                self._on_ground = False

        # Attack
        if event.key in (pygame.K_z, pygame.K_j):
            if self.goal_type == 'attack' and not self._atk_done:
                self._atk_timer = 14
                self._atk_done  = True

        # Ability
        if event.key in (pygame.K_x, pygame.K_k):
            if self.goal_type in ('ability_marked', 'ability_fleshforged') and not self._abi_used:
                self._abi_used  = True
                self._abi_flash = 50

    def update(self) -> None:
        if self._done:
            return

        self._blink += 1
        keys = pygame.key.get_pressed()

        # Movement (all goal types allow walking except ability-only)
        if self.goal_type != 'ability_marked' and self.goal_type != 'ability_fleshforged':
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self._pvx   = -_SPEED
                self._facing = -1
            elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self._pvx   = _SPEED
                self._facing = 1
            else:
                self._pvx *= 0.82

        # Gravity
        self._pvy += _GRAVITY
        if self._pvy > 18:
            self._pvy = 18

        # Move
        self._px += self._pvx
        self._py += self._pvy

        # Platform collision
        self._on_ground = False
        pr = pygame.Rect(int(self._px), int(self._py), self.PW, self.PH)
        for plat in self._platforms:
            if (pr.colliderect(plat) and self._pvy >= 0 and
                    pr.bottom - self._pvy <= plat.top + 6):
                self._py = float(plat.top - self.PH)
                self._pvy      = 0.0
                self._on_ground = True

        # Stage horizontal bounds
        if self._px < self._stage.left:
            self._px  = float(self._stage.left)
            self._pvx = 0.0
        if self._px + self.PW > self._stage.right:
            self._px  = float(self._stage.right - self.PW)
            self._pvx = 0.0

        # Attack timer
        if self._atk_timer > 0:
            self._atk_timer -= 1

        # Ability flash countdown
        if self._abi_flash > 0:
            self._abi_flash -= 1

        # --- Completion checks ---
        pr = pygame.Rect(int(self._px), int(self._py), self.PW, self.PH)

        if self.goal_type in ('move', 'jump') and self._target and not self._target_hit:
            if pr.colliderect(self._target):
                self._target_hit = True
                self._flash      = 50

        elif self.goal_type == 'attack' and self._atk_done and self._atk_timer > 0 and not self._target_hit:
            # Hitbox extends from player's right edge (always facing right here)
            atk_rect = pygame.Rect(pr.right, pr.top + 6, _ATK_REACH, self.PH - 12)
            if atk_rect.colliderect(self._target):
                self._target_hit = True
                self._flash      = 50

        elif self.goal_type in ('ability_marked', 'ability_fleshforged') and self._abi_used and self._abi_flash == 0 and self._flash == 0:
            self._flash = 50

        # Flash countdown → completion
        if self._flash > 0:
            self._flash -= 1
            if self._flash == 0:
                self._done = True

    def draw(self, surface: pygame.Surface) -> None:
        # Darken the prologue background so the stage pops
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        surface.blit(overlay, (0, 0))

        # Stage background
        bg = pygame.Surface((self.STAGE_W, self.STAGE_H), pygame.SRCALPHA)
        bg.fill((10, 6, 22, 230))
        surface.blit(bg, self._stage.topleft)

        # Stage border (accent color)
        pygame.draw.rect(surface, self._accent, self._stage, 2)

        # Platforms
        for plat in self._platforms:
            pygame.draw.rect(surface, (55, 50, 70), plat)
            pygame.draw.rect(surface, (80, 75, 100), plat, 1)

        # Target / collectible / dummy
        if self._target and not self._target_hit:
            if self.goal_type in ('move', 'jump'):
                self._draw_collectible(surface, self._target)
            elif self.goal_type == 'attack':
                self._draw_dummy(surface, self._target)

        # Mini player
        pr = pygame.Rect(int(self._px), int(self._py), self.PW, self.PH)
        pygame.draw.rect(surface, self._accent, pr)

        # Eye (direction indicator)
        eye_x = pr.right - 5 if self._facing == 1 else pr.left + 5
        pygame.draw.circle(surface, (255, 255, 255), (eye_x, pr.top + 9), 3)
        pygame.draw.circle(surface, (0, 0, 0),       (eye_x, pr.top + 9), 1)

        # Attack arc visual
        if self._atk_timer > 0:
            arc_rect = pygame.Rect(pr.right, pr.top + 6, _ATK_REACH, self.PH - 12)
            arc_s    = pygame.Surface((arc_rect.width, arc_rect.height), pygame.SRCALPHA)
            alpha    = int(200 * self._atk_timer / 14)
            arc_s.fill((*GOLD, alpha))
            surface.blit(arc_s, arc_rect.topleft)

        # Ability burst visual
        if self._abi_flash > 0:
            self._draw_ability_burst(surface, pr)

        # Prompt text above stage
        prompt_s = self._font_prompt.render(self.prompt, True, (230, 225, 240))
        surface.blit(prompt_s, (
            self._stage.centerx - prompt_s.get_width() // 2,
            self._stage.top - 34,
        ))

        # Key hint below stage — blinks
        if (self._blink % 64) < 46 and not self._target_hit and not self._abi_used:
            hint   = self._key_hint()
            hint_s = self._font_hint.render(hint, True, self._accent)
            surface.blit(hint_s, (
                self._stage.centerx - hint_s.get_width() // 2,
                self._stage.bottom + 12,
            ))

        # Success flash and checkmark
        if self._flash > 0:
            frac     = self._flash / 50
            alpha    = int(110 * frac)
            fl_surf  = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            fl_surf.fill((*self._accent, alpha))
            surface.blit(fl_surf, (0, 0))

            check = self._font_done.render("done", True, WHITE)
            cy    = self._stage.centery - check.get_height() // 2
            surface.blit(check, (self._stage.centerx - check.get_width() // 2, cy))

    # ------------------------------------------------------------------
    # Internal draw helpers
    # ------------------------------------------------------------------

    def _draw_collectible(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        # Glowing gold square
        pygame.draw.rect(surface, GOLD, rect)
        pygame.draw.rect(surface, (255, 240, 130), rect, 2)
        lbl = self._font_small.render("*", True, (20, 14, 4))
        surface.blit(lbl, (rect.centerx - lbl.get_width() // 2,
                           rect.centery - lbl.get_height() // 2))

    def _draw_dummy(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        # Straw-colored training dummy
        pygame.draw.rect(surface, (90, 55, 35), rect)
        pygame.draw.rect(surface, (130, 95, 60), rect, 2)
        # X marker
        x1, y1 = rect.left + 6, rect.top + 6
        x2, y2 = rect.right - 6, rect.bottom - 6
        pygame.draw.line(surface, (170, 130, 90), (x1, y1), (x2, y2), 2)
        pygame.draw.line(surface, (170, 130, 90), (x2, y1), (x1, y2), 2)

    def _draw_ability_burst(self, surface: pygame.Surface, pr: pygame.Rect) -> None:
        cx, cy  = pr.centerx, pr.centery
        frac    = 1.0 - self._abi_flash / 50
        radius  = int(20 + 80 * frac)
        alpha   = max(0, int(200 * (1.0 - frac)))

        ring = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(ring, (*self._accent, alpha), (radius, radius), radius, 3)
        surface.blit(ring, (cx - radius, cy - radius))

        if self.goal_type == 'ability_fleshforged':
            # Extra warm inner fill for overdrive
            inner = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(inner, (*self._accent, alpha // 3), (radius, radius), radius)
            surface.blit(inner, (cx - radius, cy - radius))

    def _key_hint(self) -> str:
        return {
            'move':               "A / D — Move",
            'jump':               "A / D — Move       W / Space — Jump",
            'attack':             "A / D — Move       Z — Attack",
            'ability_marked':     "X — Soul Surge",
            'ability_fleshforged':"X — Overdrive",
        }.get(self.goal_type, "")

    def is_complete(self) -> bool:
        return self._done
