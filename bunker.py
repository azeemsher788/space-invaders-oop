"""
bunker.py
=========
Bunker — a destructible defensive barrier composed of a grid of BunkerTile
objects.

Architecture
------------
Each Bunker is a self-contained manager for its tile grid.  Tiles are stored
in a flat list for O(n) iteration during drawing and collision checks.  The
Bunker exposes `check_projectile_collision(projectile)` which tests every
alive tile using pygame.Rect.colliderect — fast enough for our scale without
a spatial index.

Bunker shape
------------
The classic Space Invaders bunker is a rounded-top rectangle with two notch
cut-outs at the bottom to create the "arch" silhouette.  We encode this as a
binary occupancy grid of tile cells.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

import constants as C
from entities import BunkerTile, Projectile

if TYPE_CHECKING:
    pass  # avoid circular imports if needed


# ---------------------------------------------------------------------------
# Bunker occupancy shape (1 = tile present, 0 = empty)
# ---------------------------------------------------------------------------
# Width: 9 cells, Height: 7 cells → each cell = BUNKER_TILE_SIZE px
_SHAPE: list[list[int]] = [
    [0, 0, 1, 1, 1, 1, 1, 0, 0],
    [0, 1, 1, 1, 1, 1, 1, 1, 0],
    [1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 1, 0, 0, 1, 0, 0, 1, 1],
    [1, 1, 0, 0, 1, 0, 0, 1, 1],
]


class Bunker:
    """
    A destructible defensive barrier made of individual BunkerTile blocks.

    Parameters
    ----------
    left_x : int
        X pixel coordinate of the bunker's left edge.
    top_y : int
        Y pixel coordinate of the bunker's top edge.

    Attributes
    ----------
    tiles : list[BunkerTile]
        All currently intact tile blocks.
    """

    COLS: int = len(_SHAPE[0])
    ROWS: int = len(_SHAPE)
    WIDTH: int = COLS * C.BUNKER_TILE_SIZE
    HEIGHT: int = ROWS * C.BUNKER_TILE_SIZE

    def __init__(self, left_x: int, top_y: int) -> None:
        self.left_x: int = left_x
        self.top_y: int = top_y
        self.tiles: list[BunkerTile] = []
        self._build_tiles()

    # ------------------------------------------------------------------

    def _build_tiles(self) -> None:
        """Instantiate BunkerTile objects matching the occupancy shape."""
        s = C.BUNKER_TILE_SIZE
        for row, cells in enumerate(_SHAPE):
            for col, present in enumerate(cells):
                if present:
                    tx = self.left_x + col * s
                    ty = self.top_y + row * s
                    self.tiles.append(BunkerTile(tx, ty))

    # ------------------------------------------------------------------

    def check_projectile_collision(self, proj: Projectile) -> bool:
        """
        Test whether *proj* has hit any alive tile in this bunker.

        On a hit the tile takes one damage point and the projectile is
        destroyed.

        Parameters
        ----------
        proj : Projectile
            Any laser or bomb projectile.

        Returns
        -------
        bool
            True if a collision was detected and handled.
        """
        proj_rect = proj.rect
        for tile in self.tiles:
            if tile.alive and proj_rect.colliderect(tile.rect):
                tile.take_damage()
                proj.alive = False
                return True
        return False

    # ------------------------------------------------------------------

    def purge_dead_tiles(self) -> None:
        """Remove destroyed tiles from the internal list (call once per frame)."""
        self.tiles = [t for t in self.tiles if t.alive]

    # ------------------------------------------------------------------

    @property
    def is_destroyed(self) -> bool:
        """True when every tile in this bunker has been eliminated."""
        return not any(t.alive for t in self.tiles)

    # ------------------------------------------------------------------

    def draw(self, screen: pygame.Surface) -> None:
        """Blit all alive tiles onto *screen*."""
        for tile in self.tiles:
            if tile.alive:
                tile.draw(screen)


# ---------------------------------------------------------------------------
# Factory helper
# ---------------------------------------------------------------------------


def build_bunkers() -> list[Bunker]:
    """
    Construct and evenly space BUNKER_COUNT bunkers across the screen width.

    Returns
    -------
    list[Bunker]
        A list of freshly initialised Bunker objects.
    """
    bunkers: list[Bunker] = []
    usable_width = C.SCREEN_WIDTH - 2 * 60  # left & right margin
    spacing = usable_width // C.BUNKER_COUNT
    for i in range(C.BUNKER_COUNT):
        bx = 60 + i * spacing + (spacing - Bunker.WIDTH) // 2
        bunkers.append(Bunker(bx, C.BUNKER_Y))
    return bunkers
