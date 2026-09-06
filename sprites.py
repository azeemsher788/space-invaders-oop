"""
sprites.py
==========
Pure-pygame Surface factory.  All visual assets are procedurally generated
with anti-aliased polygons and pixel-art-style blit operations so the game
requires **zero external image files**.

Design note
-----------
Keeping asset generation isolated in a single module means the rest of the
code-base works with plain pygame.Surface objects and never touches drawing
primitives directly — a clean separation of concerns.
"""

from __future__ import annotations

import math
import pygame
from constants import (
    PLAYER_WIDTH, PLAYER_HEIGHT,
    ALIEN_WIDTH, ALIEN_HEIGHT,
    BUNKER_TILE_SIZE,
    GREEN, CYAN, MAGENTA, ORANGE, RED, WHITE, YELLOW,
    BUNKER_GREEN, SHIELD_COLOR,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _surface(w: int, h: int) -> pygame.Surface:
    """Return a transparent surface of the given dimensions."""
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    surf.fill((0, 0, 0, 0))
    return surf


def _hline(surf: pygame.Surface, y: int, x1: int, x2: int,
           color: tuple) -> None:
    """Draw a horizontal run of pixels (inclusive range)."""
    pygame.draw.line(surf, color, (x1, y), (x2, y))


# ---------------------------------------------------------------------------
# Player ship
# ---------------------------------------------------------------------------

def make_player_surface() -> pygame.Surface:
    """
    Build and return the player ship surface.

    The ship is a sleek, forward-facing fighter silhouette drawn with
    polygon fills and glow accents — inspired by classic Space Invaders
    but with a modern neon aesthetic.

    Returns
    -------
    pygame.Surface
        SRCALPHA surface of size (PLAYER_WIDTH × PLAYER_HEIGHT).
    """
    w, h = PLAYER_WIDTH, PLAYER_HEIGHT
    surf = _surface(w, h)

    # --- fuselage (centre body) ---
    body_pts = [
        (w // 2, 0),
        (w // 2 + 8, h // 2),
        (w // 2 + 14, h),
        (w // 2 - 14, h),
        (w // 2 - 8, h // 2),
    ]
    pygame.draw.polygon(surf, ORANGE, body_pts)

    # --- left / right wings ---
    left_wing = [(0, h), (w // 2 - 14, h), (w // 2 - 8, h // 2),
                 (w // 2 - 4, h // 2 + 4)]
    right_wing = [(w, h), (w // 2 + 14, h), (w // 2 + 8, h // 2),
                  (w // 2 + 4, h // 2 + 4)]
    wing_color = (180, 80, 0)
    pygame.draw.polygon(surf, wing_color, left_wing)
    pygame.draw.polygon(surf, wing_color, right_wing)

    # --- cockpit highlight ---
    pygame.draw.circle(surf, SHIELD_COLOR, (w // 2, h // 2 + 4), 5)
    pygame.draw.circle(surf, WHITE, (w // 2, h // 2 + 4), 2)

    # --- engine nozzles ---
    for nx in (w // 2 - 10, w // 2 + 10):
        pygame.draw.rect(surf, (255, 160, 0), (nx - 3, h - 6, 6, 6))

    return surf


# ---------------------------------------------------------------------------
# Alien sprites (5 rows → 3 visual types, two-frame animation)
# ---------------------------------------------------------------------------

def _alien_type_for_row(row: int) -> int:
    """Map a fleet row index (0 = bottom) to an alien visual type (0/1/2)."""
    if row <= 1:
        return 0   # squid  — green
    if row <= 3:
        return 1   # crab   — cyan
    return 2       # octopus — magenta


def _make_squid(frame: int) -> pygame.Surface:
    """Two-frame pixel-art squid alien (classic bottom rows)."""
    w, h = ALIEN_WIDTH, ALIEN_HEIGHT
    surf = _surface(w, h)
    c = GREEN
    if frame == 0:
        pattern = [
            "  XXXXX  ",
            " XXXXXXX ",
            "XXX X XXX",
            "XXXXXXXXX",
            " X X X X ",
            "  X   X  ",
            " X     X ",
        ]
    else:
        pattern = [
            "  XXXXX  ",
            " XXXXXXX ",
            "XXX X XXX",
            "XXXXXXXXX",
            "X X X X X",
            "X       X",
            " X     X ",
        ]
    _draw_pattern(surf, pattern, c, w, h)
    return surf


def _make_crab(frame: int) -> pygame.Surface:
    """Two-frame pixel-art crab alien (classic middle rows)."""
    w, h = ALIEN_WIDTH, ALIEN_HEIGHT
    surf = _surface(w, h)
    c = CYAN
    if frame == 0:
        pattern = [
            " X     X ",
            "  X   X  ",
            " XXXXXXX ",
            "XX X X XX",
            "XXXXXXXXX",
            " XXXXXXX ",
            " X X X X ",
            "X       X",
        ]
    else:
        pattern = [
            " X     X ",
            "X X   X X",
            "X XXXXX X",
            "XXX X XXX",
            "XXXXXXXXX",
            " XXXXXXX ",
            "  X X X  ",
            " X     X ",
        ]
    _draw_pattern(surf, pattern, c, w, h)
    return surf


def _make_octopus(frame: int) -> pygame.Surface:
    """Two-frame pixel-art octopus alien (classic top rows)."""
    w, h = ALIEN_WIDTH, ALIEN_HEIGHT
    surf = _surface(w, h)
    c = MAGENTA
    if frame == 0:
        pattern = [
            "  XXXXX  ",
            " XXXXXXX ",
            "XX XXXXX ",
            "XX X X XX",
            "XXXXXXXXX",
            " XXXXXXX ",
            "  X X X  ",
            " X X X X ",
        ]
    else:
        pattern = [
            "  XXXXX  ",
            " XXXXXXX ",
            "XXXXXXXXX",
            "XX X X XX",
            "XXXXXXXXX",
            " X X X X ",
            "X       X",
            "  X   X  ",
        ]
    _draw_pattern(surf, pattern, c, w, h)
    return surf


def _draw_pattern(surf: pygame.Surface, pattern: list[str],
                  color: tuple, w: int, h: int) -> None:
    """Blit a pixel-art pattern string onto a surface, centred."""
    cell_w = w // max(len(row) for row in pattern)
    cell_h = h // len(pattern)
    for ry, row in enumerate(pattern):
        for cx, ch in enumerate(row):
            if ch == 'X':
                pygame.draw.rect(
                    surf, color,
                    (cx * cell_w, ry * cell_h, cell_w, cell_h)
                )


def make_alien_surfaces() -> dict[int, list[pygame.Surface]]:
    """
    Pre-render all alien sprite frames.

    Returns
    -------
    dict[int, list[pygame.Surface]]
        Mapping of alien_type → [frame0_surface, frame1_surface].
    """
    return {
        0: [_make_squid(0), _make_squid(1)],
        1: [_make_crab(0), _make_crab(1)],
        2: [_make_octopus(0), _make_octopus(1)],
    }


def alien_type_for_row(row: int) -> int:
    """Public re-export of the row→type mapping."""
    return _alien_type_for_row(row)


# ---------------------------------------------------------------------------
# UFO / Mystery ship
# ---------------------------------------------------------------------------

def make_ufo_surface() -> pygame.Surface:
    """Return a neon-red UFO/mystery-ship surface."""
    w, h = 52, 24
    surf = _surface(w, h)
    c = (255, 40, 40)
    pygame.draw.ellipse(surf, c, (6, h // 2, w - 12, h // 2))
    pygame.draw.ellipse(surf, (200, 200, 200), (14, 4, w - 28, h // 2))
    pygame.draw.ellipse(surf, (255, 255, 100), (22, 6, 8, 6))
    return surf


# ---------------------------------------------------------------------------
# Projectiles
# ---------------------------------------------------------------------------

def make_laser_surface() -> pygame.Surface:
    """Player laser bolt — thin neon-orange pillar with glow."""
    surf = _surface(4, 18)
    pygame.draw.rect(surf, ORANGE, (1, 0, 2, 18))
    pygame.draw.rect(surf, WHITE,  (1, 6, 2, 6))
    return surf


def make_bomb_surface() -> pygame.Surface:
    """Alien bomb — zigzag red projectile."""
    surf = _surface(6, 18)
    pts = [(3, 0), (6, 5), (0, 10), (6, 15), (3, 18)]
    pygame.draw.lines(surf, RED, False, pts, 2)
    return surf


# ---------------------------------------------------------------------------
# Bunker tile
# ---------------------------------------------------------------------------

def make_bunker_tile_surface(health: int, max_health: int) -> pygame.Surface:
    """
    Return a bunker pixel-tile surface whose colour and damage cracks
    reflect the remaining health fraction.

    Parameters
    ----------
    health : int
        Current health of this tile.
    max_health : int
        Maximum possible health.

    Returns
    -------
    pygame.Surface
    """
    s = BUNKER_TILE_SIZE
    surf = _surface(s, s)
    frac = health / max_health
    r = int(BUNKER_GREEN[0] * frac)
    g = int(BUNKER_GREEN[1] * frac)
    b = int(BUNKER_GREEN[2] * frac)
    pygame.draw.rect(surf, (r, g, b), (0, 0, s, s))
    if frac < 0.67:
        pygame.draw.line(surf, (0, 0, 0), (1, 1), (s - 2, s - 2))
    if frac < 0.34:
        pygame.draw.line(surf, (0, 0, 0), (s - 2, 1), (1, s - 2))
    return surf


# ---------------------------------------------------------------------------
# Explosion
# ---------------------------------------------------------------------------

def make_explosion_surface(size: int = 30) -> pygame.Surface:
    """
    Procedural starburst explosion effect.

    Parameters
    ----------
    size : int
        Diameter of the explosion in pixels.

    Returns
    -------
    pygame.Surface
    """
    surf = _surface(size, size)
    cx, cy = size // 2, size // 2
    for i in range(12):
        angle = math.radians(i * 30)
        ex = int(cx + math.cos(angle) * (size // 2 - 2))
        ey = int(cy + math.sin(angle) * (size // 2 - 2))
        color = YELLOW if i % 2 == 0 else ORANGE
        pygame.draw.line(surf, color, (cx, cy), (ex, ey), 2)
    pygame.draw.circle(surf, WHITE, (cx, cy), 4)
    return surf
