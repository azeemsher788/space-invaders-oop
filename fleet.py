"""
fleet.py
========
AlienFleet — the central orchestrator for enemy movement, animation, and
bomb-dropping logic.

Fleet state machine
-------------------
The fleet cycles through three movement phases each "tick":

    1. MOVE_HORIZONTAL  — shift all alive aliens ±ALIEN_MOVE_STEP pixels.
    2. CHECK_EDGE       — if any alien has crossed the left/right boundary,
                          switch direction and issue a DROP command.
    3. DROP             — shift every alien down ALIEN_STEP_DOWN pixels, then
                          resume horizontal movement in the new direction.

Dynamic speed scaling
---------------------
The movement interval (ms between ticks) is linearly interpolated between
ALIEN_MOVE_INTERVAL_MAX (all aliens alive) and ALIEN_MOVE_INTERVAL_MIN
(last alien alive) based on the fraction of aliens remaining:

    interval = MIN + (MAX - MIN) * (alive / total)

This faithfully reproduces the famous arcade acceleration where the lone
survivor becomes terrifyingly fast.
"""

from __future__ import annotations

import random
from enum import Enum, auto
from typing import Optional

import pygame

import constants as C
import sprites as SPR
from entities import Alien, Bomb


class _MovePhase(Enum):
    """Internal state-machine phases for fleet movement."""

    HORIZONTAL = auto()
    DROP = auto()


class AlienFleet:
    """
    Manages the entire grid of Alien entities as a single cohesive unit.

    The fleet is a 2-D list (grid[row][col]) of Alien objects (or None for
    destroyed slots).  All movement decisions are made at the fleet level;
    individual aliens only know their own pixel position.

    Parameters
    ----------
    level : int
        Current game level — shifts starting position down slightly each
        level to create pressure, and seeds base speed.

    Attributes
    ----------
    grid : list[list[Optional[Alien]]]
        Row-major grid; grid[0] is the bottom row.
    aliens : list[Alien]
        Flat list of all currently alive Alien objects (updated on kill).
    direction : int
        +1 = moving right, -1 = moving left.
    _move_dx : int
        Horizontal pixel step per tick.
    _last_move_time : int
        pygame.time.get_ticks() of the last movement tick.
    _phase : _MovePhase
        Current movement state-machine phase.
    bombs : list[Bomb]
        Active bombs dropped by the fleet.
    """

    _MOVE_DX: int = 12  # pixels per horizontal step

    def __init__(self, level: int = 1) -> None:
        self._alien_surfaces = SPR.make_alien_surfaces()
        self.direction: int = 1
        self._phase: _MovePhase = _MovePhase.HORIZONTAL
        self._last_move_time: int = pygame.time.get_ticks()
        self.bombs: list[Bomb] = []
        self._total_aliens: int = C.ALIEN_ROWS * C.ALIEN_COLS

        # Level offset: fleet starts slightly lower each subsequent level
        y_offset = min((level - 1) * C.ALIEN_V_SPACING, C.ALIEN_V_SPACING * 2)

        self.grid: list[list[Optional[Alien]]] = []
        self.aliens: list[Alien] = []

        for row in range(C.ALIEN_ROWS):
            grid_row: list[Optional[Alien]] = []
            for col in range(C.ALIEN_COLS):
                x = C.ALIEN_FLEET_LEFT + col * C.ALIEN_H_SPACING
                y = C.ALIEN_FLEET_TOP + y_offset + row * C.ALIEN_V_SPACING
                alien = Alien(x, y, row, col, alien_surfaces=self._alien_surfaces)
                grid_row.append(alien)
                self.aliens.append(alien)
            self.grid.append(grid_row)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def alive_count(self) -> int:
        """Number of aliens still alive."""
        return len(self.aliens)

    @property
    def is_empty(self) -> bool:
        """True when every alien has been destroyed."""
        return len(self.aliens) == 0

    @property
    def _move_interval(self) -> int:
        """
        Dynamic movement interval in milliseconds.

        Linearly interpolated between MAX (full fleet) and MIN (last alien)
        based on the fraction of aliens remaining.
        """
        frac = self.alive_count / self._total_aliens
        return int(
            C.ALIEN_MOVE_INTERVAL_MIN
            + (C.ALIEN_MOVE_INTERVAL_MAX - C.ALIEN_MOVE_INTERVAL_MIN) * frac
        )

    # ------------------------------------------------------------------
    # Boundary helpers
    # ------------------------------------------------------------------

    def _leftmost_x(self) -> int:
        """Return the minimum x coordinate among all alive aliens."""
        return min(int(a.x) for a in self.aliens)

    def _rightmost_x(self) -> int:
        """Return the maximum right-edge x coordinate among all alive aliens."""
        return max(int(a.x) + C.ALIEN_WIDTH for a in self.aliens)

    def _lowest_y(self) -> int:
        """Return the maximum bottom-edge y coordinate among all alive aliens."""
        return max(int(a.y) + C.ALIEN_HEIGHT for a in self.aliens)

    # ------------------------------------------------------------------
    # Front-line column logic (only front-line aliens drop bombs)
    # ------------------------------------------------------------------

    def _front_line_aliens(self) -> list[Alien]:
        """
        Return the bottom-most alive alien in each column.

        These are the only ones eligible to fire bombs (matching the
        original arcade behaviour where occluded aliens cannot fire).
        """
        front: dict[int, Alien] = {}
        for alien in self.aliens:
            col = alien.col
            if col not in front or alien.row < front[col].row:
                front[col] = alien
        return list(front.values())

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, dt: int) -> None:
        """
        Tick the fleet state machine and spawn bombs if eligible.

        Parameters
        ----------
        dt : int
            Elapsed milliseconds since the previous frame (not directly used
            for movement — movement uses absolute timestamps for precision).
        """
        now = pygame.time.get_ticks()

        # --- Movement tick ---
        if now - self._last_move_time >= self._move_interval:
            self._last_move_time = now
            self._tick_movement()

        # --- Update active bombs ---
        for bomb in self.bombs:
            bomb.update(dt)
        self.bombs = [b for b in self.bombs if b.alive]

        # --- Possibly drop new bomb ---
        self._maybe_drop_bomb()

    def _tick_movement(self) -> None:
        """Execute one movement tick according to the current phase."""
        if self._phase == _MovePhase.HORIZONTAL:
            dx = self._MOVE_DX * self.direction
            for alien in self.aliens:
                alien.x += dx
                alien.toggle_frame()

            # Check for edge collision
            hit_right = self._rightmost_x() >= C.SCREEN_WIDTH - 10
            hit_left = self._leftmost_x() <= 10

            if (self.direction == 1 and hit_right) or (
                self.direction == -1 and hit_left
            ):
                self._phase = _MovePhase.DROP
        else:
            # DROP phase: move fleet down then reverse direction
            for alien in self.aliens:
                alien.y += C.ALIEN_STEP_DOWN
            self.direction *= -1
            self._phase = _MovePhase.HORIZONTAL

    def _maybe_drop_bomb(self) -> None:
        """
        Randomly select a front-line alien to drop a bomb.

        Firing is gated by ALIEN_MAX_BOMBS and ALIEN_BOMB_CHANCE to keep
        gameplay balanced without making it trivially easy or impossible.
        """
        if len(self.bombs) >= C.ALIEN_MAX_BOMBS:
            return
        front = self._front_line_aliens()
        if not front:
            return
        for alien in front:
            if random.random() < C.ALIEN_BOMB_CHANCE:
                self.bombs.append(alien.drop_bomb())
                if len(self.bombs) >= C.ALIEN_MAX_BOMBS:
                    break

    # ------------------------------------------------------------------
    # Kill
    # ------------------------------------------------------------------

    def kill_alien(self, alien: Alien) -> int:
        """
        Remove *alien* from the fleet and return its score value.

        Parameters
        ----------
        alien : Alien
            The alien to destroy.

        Returns
        -------
        int
            Score points awarded for this kill.
        """
        alien.alive = False
        if alien in self.aliens:
            self.aliens.remove(alien)
        if alien in self.grid[alien.row]:
            self.grid[alien.row][alien.col] = None
        return alien.score_value

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------

    def draw(self, screen: pygame.Surface) -> None:
        """Blit all alive aliens and active bombs onto *screen*."""
        for alien in self.aliens:
            alien.draw(screen)
        for bomb in self.bombs:
            bomb.draw(screen)

    # ------------------------------------------------------------------
    # Invasion check
    # ------------------------------------------------------------------

    def has_invaded(self) -> bool:
        """
        Return True if any alien has reached the player's defensive line.

        This ends the current game immediately — matching arcade rules.
        """
        return self._lowest_y() >= C.BUNKER_Y
