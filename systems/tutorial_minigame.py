# =============================================================================
# systems/tutorial_minigame.py — Inline control tutorial played during prologues.
#
# Revised direction:
# - left/right attack behavior fixed
# - failed jump attempts auto-reset the mini-stage
# - prolonged inactivity/timeouts auto-reset the tutorial
# - reset prompt is shown briefly after a failure
# =============================================================================

import pygame
from settings import (SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, GOLD,
                      MARKED_COLOR, FLESHFORGED_COLOR, FACTION_MARKED)

_GRAVITY = 0.65
_JUMP_VY = -11.5
_SPEED = 4.2
_ATK_REACH = 44
_RESET_TIMEOUT_FRAMES = 60 * 12
_RESET_MESSAGE_FRAMES = 48


class TutorialMinigame:
    STAGE_W = 520
    STAGE_H = 200
    GROUND_H = 30
    PW = 22
    PH = 38

    def __init__(self, goal_type: str, prompt: str, faction: str):
        self.goal_type = goal_type
        self.prompt = prompt
        self.faction = faction
        self._accent = MARKED_COLOR if faction == FACTION_MARKED else FLESHFORGED_COLOR
        self._done = False

        sx = (SCREEN_WIDTH - self.STAGE_W) // 2
        sy = (SCREEN_HEIGHT - self.STAGE_H) // 2 + 20
        self._stage = pygame.Rect(sx, sy, self.STAGE_W, self.STAGE_H)
        self._ground_y = sy + self.STAGE_H - self.GROUND_H

        self._reset_notice = 0
        self._elapsed_frames = 0

        pygame.font.init()
        self._font_prompt = pygame.font.SysFont("georgia", 20)
        self._font_hint = pygame.font.SysFont("monospace", 14)
        self._font_done = pygame.font.SysFont("georgia", 28, bold=True)
        self._font_small = pygame.font.SysFont("monospace", 12)

        self._build_layout()
        self._reset_stage(initial=True)

    def _build_layout(self):
        sx = self._stage.left
        ground_y = self._ground_y

        if self.goal_type == 'jump':
            left_w = 200
            right_x = sx + left_w + 80
            right_w = self.STAGE_W - left_w - 80
            self._platforms = [
                pygame.Rect(sx, ground_y, left_w, self.GROUND_H),
                pygame.Rect(right_x, ground_y, right_w, self.GROUND_H),
            ]
        else:
            self._platforms = [pygame.Rect(sx, ground_y, self.STAGE_W, self.GROUND_H)]

        if self.goal_type == 'move':
            tx = sx + self.STAGE_W - 42
            ty = ground_y - 26
            self._target_template = pygame.Rect(tx, ty, 24, 26)
        elif self.goal_type == 'jump':
            right_plat = self._platforms[1]
            tx = right_plat.right - 38
            ty = right_plat.top - 26
            self._target_template = pygame.Rect(tx, ty, 24, 26)
        elif self.goal_type == 'attack':
            tx = sx + 200
            ty = ground_y - 40
            self._target_template = pygame.Rect(tx, ty, 28, 40)
        else:
            self._target_template = None

    def _reset_stage(self, initial: bool = False):
        sx = self._stage.left
        self._px = float(sx + 40)
        self._py = float(self._ground_y - self.PH)
        self._pvx = 0.0
        self._pvy = 0.0
        self._on_ground = True
        self._facing = 1
        self._atk_timer = 0
        self._atk_done = False
        self._abi_used = False
        self._abi_flash = 0
        self._target_hit = False
        self._flash = 0
        self._blink = 0
        self._elapsed_frames = 0
        self._target = self._target_template.copy() if self._target_template else None
        if not initial:
            self._reset_notice = _RESET_MESSAGE_FRAMES

    def handle_event(self, event: pygame.event.Event) -> None:
        if self._done or event.type != pygame.KEYDOWN:
            return

        if event.key in (pygame.K_w, pygame.K_UP, pygame.K_SPACE):
            if self._on_ground and self.goal_type == 'jump':
                self._pvy = _JUMP_VY
                self._on_ground = False

        if event.key in (pygame.K_z, pygame.K_j):
            if self.goal_type == 'attack' and not self._atk_done:
                self._atk_timer = 14
                self._atk_done = True

        if event.key in (pygame.K_x, pygame.K_k):
            if self.goal_type in ('ability_marked', 'ability_fleshforged') and not self._abi_used:
                self._abi_used = True
                self._abi_flash = 50

    def update(self) -> None:
        if self._done:
            return

        self._blink += 1
        self._elapsed_frames += 1
        if self._reset_notice > 0:
            self._reset_notice -= 1

        keys = pygame.key.get_pressed()
        if self.goal_type not in ('ability_marked', 'ability_fleshforged'):
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self._pvx = -_SPEED
                self._facing = -1
            elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self._pvx = _SPEED
                self._facing = 1
            else:
                self._pvx *= 0.82

        self._pvy += _GRAVITY
        if self._pvy > 18:
            self._pvy = 18

        self._px += self._pvx
        self._py += self._pvy

        self._on_ground = False
        pr = pygame.Rect(int(self._px), int(self._py), self.PW, self.PH)
        for plat in self._platforms:
            if (pr.colliderect(plat) and self._pvy >= 0 and
                    pr.bottom - self._pvy <= plat.top + 6):
                self._py = float(plat.top - self.PH)
                self._pvy = 0.0
                self._on_ground = True

        if self._px < self._stage.left:
            self._px = float(self._stage.left)
            self._pvx = 0.0
        if self._px + self.PW > self._stage.right:
            self._px = float(self._stage.right - self.PW)
            self._pvx = 0.0

        if self._py > self._stage.bottom + 40:
            self._reset_stage()
            return

        if self._elapsed_frames >= _RESET_TIMEOUT_FRAMES and not self._target_hit and not self._abi_used:
            self._reset_stage()
            return

        if self._atk_timer > 0:
            self._atk_timer -= 1
        if self._abi_flash > 0:
            self._abi_flash -= 1

        pr = pygame.Rect(int(self._px), int(self._py), self.PW, self.PH)

        if self.goal_type in ('move', 'jump') and self._target and not self._target_hit:
            if pr.colliderect(self._target):
                self._target_hit = True
                self._flash = 50

        elif self.goal_type == 'attack' and self._atk_done and self._atk_timer > 0 and not self._target_hit:
            if self._facing == 1:
                atk_rect = pygame.Rect(pr.right, pr.top + 6, _ATK_REACH, self.PH - 12)
            else:
                atk_rect = pygame.Rect(pr.left - _ATK_REACH, pr.top + 6, _ATK_REACH, self.PH - 12)

            if atk_rect.colliderect(self._target):
                self._target_hit = True
                self._flash = 50

        elif self.goal_type in ('ability_marked', 'ability_fleshforged') and self._abi_used and self._abi_flash == 0 and self._flash == 0:
            self._flash = 50

        if self._flash > 0:
            self._flash -= 1
            if self._flash == 0:
                self._done = True

    def draw(self, surface: pygame.Surface) -> None:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        surface.blit(overlay, (0, 0))

        bg = pygame.Surface((self.STAGE_W, self.STAGE_H), pygame.SRCALPHA)
        bg.fill((10, 6, 22, 230))
        surface.blit(bg, self._stage.topleft)
        pygame.draw.rect(surface, self._accent, self._stage, 2)

        for plat in self._platforms:
            pygame.draw.rect(surface, (55, 50, 70), plat)
            pygame.draw.rect(surface, (80, 75, 100), plat, 1)

        if self._target and not self._target_hit:
            if self.goal_type in ('move', 'jump'):
                self._draw_collectible(surface, self._target)
            elif self.goal_type == 'attack':
                self._draw_dummy(surface, self._target)

        pr = pygame.Rect(int(self._px), int(self._py), self.PW, self.PH)
        pygame.draw.rect(surface, self._accent, pr)

        eye_x = pr.right - 5 if self._facing == 1 else pr.left + 5
        pygame.draw.circle(surface, WHITE, (eye_x, pr.top + 9), 3)
        pygame.draw.circle(surface, (0, 0, 0), (eye_x, pr.top + 9), 1)

        if self._atk_timer > 0:
            if self._facing == 1:
                arc_rect = pygame.Rect(pr.right, pr.top + 6, _ATK_REACH, self.PH - 12)
            else:
                arc_rect = pygame.Rect(pr.left - _ATK_REACH, pr.top + 6, _ATK_REACH, self.PH - 12)
            arc_s = pygame.Surface((arc_rect.width, arc_rect.height), pygame.SRCALPHA)
            alpha = int(200 * self._atk_timer / 14)
            arc_s.fill((*GOLD, alpha))
            surface.blit(arc_s, arc_rect.topleft)

        if self._abi_flash > 0:
            self._draw_ability_burst(surface, pr)

        prompt_s = self._font_prompt.render(self.prompt, True, (230, 225, 240))
        surface.blit(prompt_s, (self._stage.centerx - prompt_s.get_width() // 2, self._stage.top - 34))

        if (self._blink % 64) < 46 and not self._target_hit and not self._abi_used:
            hint_s = self._font_hint.render(self._key_hint(), True, self._accent)
            surface.blit(hint_s, (self._stage.centerx - hint_s.get_width() // 2, self._stage.bottom + 12))

        if self._reset_notice > 0:
            reset_s = self._font_hint.render('resetting trial…', True, GOLD)
            surface.blit(reset_s, (self._stage.centerx - reset_s.get_width() // 2, self._stage.bottom + 32))

        if self._flash > 0:
            frac = self._flash / 50
            alpha = int(110 * frac)
            fl_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            fl_surf.fill((*self._accent, alpha))
            surface.blit(fl_surf, (0, 0))
            check = self._font_done.render('done', True, WHITE)
            cy = self._stage.centery - check.get_height() // 2
            surface.blit(check, (self._stage.centerx - check.get_width() // 2, cy))

    def _draw_collectible(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        pygame.draw.rect(surface, GOLD, rect)
        pygame.draw.rect(surface, (255, 240, 130), rect, 2)
        lbl = self._font_small.render('*', True, (20, 14, 4))
        surface.blit(lbl, (rect.centerx - lbl.get_width() // 2, rect.centery - lbl.get_height() // 2))

    def _draw_dummy(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        pygame.draw.rect(surface, (90, 55, 35), rect)
        pygame.draw.rect(surface, (130, 95, 60), rect, 2)
        x1, y1 = rect.left + 6, rect.top + 6
        x2, y2 = rect.right - 6, rect.bottom - 6
        pygame.draw.line(surface, (170, 130, 90), (x1, y1), (x2, y2), 2)
        pygame.draw.line(surface, (170, 130, 90), (x2, y1), (x1, y2), 2)

    def _draw_ability_burst(self, surface: pygame.Surface, pr: pygame.Rect) -> None:
        cx, cy = pr.centerx, pr.centery
        frac = 1.0 - self._abi_flash / 50
        radius = int(20 + 80 * frac)
        alpha = max(0, int(200 * (1.0 - frac)))
        ring = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(ring, (*self._accent, alpha), (radius, radius), radius, 3)
        surface.blit(ring, (cx - radius, cy - radius))
        if self.goal_type == 'ability_fleshforged':
            inner = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(inner, (*self._accent, alpha // 3), (radius, radius), radius)
            surface.blit(inner, (cx - radius, cy - radius))

    def _key_hint(self) -> str:
        return {
            'move': 'A / D — Move',
            'jump': 'A / D — Move       W / Space — Jump',
            'attack': 'A / D — Move       Z — Attack',
            'ability_marked': 'X — Soul Surge',
            'ability_fleshforged': 'X — Overdrive',
        }.get(self.goal_type, '')

    def is_complete(self) -> bool:
        return self._done
