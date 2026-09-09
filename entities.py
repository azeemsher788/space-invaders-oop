"""
entities.py
===========
Core game-entity classes.

Class hierarchy
---------------
Entity (abstract base)
├── PlayerShip
├── Alien
├── UFO
├── Projectile
│   ├── Laser      (player projectile)
│   └── Bomb       (alien projectile)
└── BunkerTile     (individual destructible tile block)

Design decisions
----------------
* Every entity owns its *logical* state (position, velocity, health) and
  exposes a `rect` property so collision detection can work uniformly on
  pygame.Rect objects without caring about entity type.
* Drawing is intentionally kept minimal here — each entity exposes a
  `surface` attribute that the renderer blits; entities never call
  `screen.blit` themselves (SRP / testability).
* AlienFleet is in fleet.py to keep this file focused on individual actors.
"""

from __future__ import annotations

from typing import Optional

import pygame

import constants as C
import sprites as SPR

# ---------------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------------


class Entity:
    """
    Lightweight base class shared by all game objects.

    Attributes
    ----------
    x, y : float
        Sub-pixel position of the entity's top-left corner.
    surface : pygame.Surface
        The pre-rendered visual surface for this entity.
    alive : bool
        When False the entity should be removed from all collections.
    """

    def __init__(self, x: float, y: float, surface: pygame.Surface) -> None:
        self.x: float = x
        self.y: float = y
        self.surface: pygame.Surface = surface
        self.alive: bool = True

    # ------------------------------------------------------------------
    @property
    def rect(self) -> pygame.Rect:
        """Bounding-box rect derived from current position and surface size."""
        return pygame.Rect(
            int(self.x),
            int(self.y),
            self.surface.get_width(),
            self.surface.get_height(),
        )

    # ------------------------------------------------------------------
    def update(self, dt: int) -> None:
        """
        Advance entity state by *dt* milliseconds.

        Parameters
        ----------
        dt : int
            Elapsed milliseconds since the previous frame.
        """

    def draw(self, screen: pygame.Surface) -> None:
        """Blit this entity onto *screen* at its current position."""
        screen.blit(self.surface, (int(self.x), int(self.y)))


# ---------------------------------------------------------------------------
# Player ship
# ---------------------------------------------------------------------------


class PlayerShip(Entity):
    """
    The player-controlled cannon at the bottom of the screen.

    Movement is handled via key-state polling (set by GameEngine) rather
    than per-event callbacks to eliminate OS key-repeat latency — a
    standard technique for responsive arcade-style controls.

    Attributes
    ----------
    lives : int
        Remaining lives.
    score : int
        Accumulated score (owned here for convenience; HUD reads it).
    move_left, move_right : bool
        Key-state flags set by GameEngine.
    fire_pressed : bool
        Key-state flag for fire button.
    _last_shot_time : int
        pygame.time.get_ticks() value of the most recent laser fired.
    invincible_until : int
        Timestamp until which the player is immune (post-respawn grace).
    """

    def __init__(self) -> None:
        surf = SPR.make_player_surface()
        x = C.SCREEN_WIDTH // 2 - C.PLAYER_WIDTH // 2
        y = C.SCREEN_HEIGHT - C.PLAYER_Y_OFFSET
        super().__init__(x, y, surf)

        self.lives: int = C.PLAYER_LIVES
        self.score: int = 0

        # key-state flags
        self.move_left: bool = False
        self.move_right: bool = False
        self.fire_pressed: bool = False

        self._last_shot_time: int = 0
        self.invincible_until: int = 0

    # ------------------------------------------------------------------
    @property
    def is_invincible(self) -> bool:
        """True while post-respawn invincibility grace period is active."""
        return pygame.time.get_ticks() < self.invincible_until

    # ------------------------------------------------------------------
    def update(self, dt: int) -> None:  # noqa: ARG002
        """Move the ship based on key-state flags; clamp to screen bounds."""
        if self.move_left:
            self.x -= C.PLAYER_SPEED
        if self.move_right:
            self.x += C.PLAYER_SPEED

        # clamp
        self.x = max(0.0, min(self.x, C.SCREEN_WIDTH - C.PLAYER_WIDTH))

    # ------------------------------------------------------------------
    def try_fire(self) -> Optional["Laser"]:
        """
        Attempt to fire a laser respecting the cooldown timer.

        Returns
        -------
        Laser or None
            A new Laser projectile if the cooldown has elapsed, else None.
        """
        now = pygame.time.get_ticks()
        if now - self._last_shot_time >= C.PLAYER_LASER_COOLDOWN:
            self._last_shot_time = now
            lx = self.x + C.PLAYER_WIDTH // 2 - 2
            ly = self.y - 18
            return Laser(lx, ly)
        return None

    # ------------------------------------------------------------------
    def hit(self) -> None:
        """Register a hit: decrement lives and grant invincibility window."""
        if self.is_invincible:
            return
        self.lives -= 1
        self.invincible_until = pygame.time.get_ticks() + 2_000  # 2 s grace

    # ------------------------------------------------------------------
    def draw(self, screen: pygame.Surface) -> None:
        """Draw the ship; flash during invincibility using alternating frames."""
        if self.is_invincible:
            if (pygame.time.get_ticks() // 100) % 2 == 0:
                return  # blink effect
        screen.blit(self.surface, (int(self.x), int(self.y)))


# ---------------------------------------------------------------------------
# Alien
# ---------------------------------------------------------------------------


class Alien(Entity):
    """
    A single alien in the fleet grid.

    Attributes
    ----------
    row : int
        Row index within the fleet (0 = bottom).
    col : int
        Column index within the fleet.
    alien_type : int
        Visual category (0 squid / 1 crab / 2 octopus).
    score_value : int
        Points awarded when this alien is destroyed.
    _frame : int
        Current animation frame index (0 or 1).
    _all_frames : list[pygame.Surface]
        Pre-rendered frames for this alien type.
    """

    def __init__(
        self,
        x: float,
        y: float,
        row: int,
        col: int,
        alien_surfaces: dict[int, list[pygame.Surface]],
    ) -> None:
        self.row = row
        self.col = col
        self.alien_type: int = SPR.alien_type_for_row(row)
        self._all_frames: list[pygame.Surface] = alien_surfaces[self.alien_type]
        self._frame: int = 0
        self.score_value: int = C.ALIEN_SCORE.get(row, 10)
        super().__init__(x, y, self._all_frames[0])

    # ------------------------------------------------------------------
    def toggle_frame(self) -> None:
        """Advance to the next animation frame (called by AlienFleet on move)."""
        self._frame = 1 - self._frame
        self.surface = self._all_frames[self._frame]

    # ------------------------------------------------------------------
    def drop_bomb(self) -> "Bomb":
        """Create and return a bomb fired from this alien's current position."""
        bx = self.x + C.ALIEN_WIDTH // 2 - 3
        by = self.y + C.ALIEN_HEIGHT
        return Bomb(bx, by)


# ---------------------------------------------------------------------------
# UFO (Mystery Ship)
# ---------------------------------------------------------------------------


class UFO(Entity):
    """
    The bonus mystery ship that occasionally crosses the top of the screen.

    Attributes
    ----------
    direction : int
        +1 for left-to-right, -1 for right-to-left.
    score_value : int
        Points awarded if the player destroys this UFO.
    """

    UFO_W: int = 52
    UFO_H: int = 24

    def __init__(self) -> None:
        # pylint: disable=import-outside-toplevel
        import random

        self.direction: int = random.choice((-1, 1))
        if self.direction == 1:
            start_x = -self.UFO_W
        else:
            start_x = C.SCREEN_WIDTH
        surf = SPR.make_ufo_surface()
        super().__init__(start_x, 28.0, surf)
        self.score_value: int = C.UFO_SCORE

    def update(self, dt: int) -> None:  # noqa: ARG002
        self.x += C.UFO_SPEED * self.direction
        if self.x > C.SCREEN_WIDTH + self.UFO_W or self.x < -self.UFO_W * 2:
            self.alive = False


# ---------------------------------------------------------------------------
# Projectiles
# ---------------------------------------------------------------------------


class Projectile(Entity):
    """Base class for any projectile (laser or bomb)."""

    def __init__(self, x: float, y: float, dy: float, surface: pygame.Surface) -> None:
        super().__init__(x, y, surface)
        self.dy: float = dy  # vertical velocity (pixels/frame, sign=direction)

    def update(self, dt: int) -> None:  # noqa: ARG002
        self.y += self.dy
        if self.y < -30 or self.y > C.SCREEN_HEIGHT + 30:
            self.alive = False


class Laser(Projectile):
    """
    Upward-moving projectile fired by the player.

    The laser travels at a fixed speed regardless of frame-rate because
    game-loop timing is managed by the GameEngine clock.
    """

    def __init__(self, x: float, y: float) -> None:
        surf = SPR.make_laser_surface()
        super().__init__(x, y, dy=-C.PLAYER_LASER_SPEED, surface=surf)


class Bomb(Projectile):
    """Downward-moving projectile dropped by an alien."""

    def __init__(self, x: float, y: float) -> None:
        surf = SPR.make_bomb_surface()
        super().__init__(x, y, dy=C.ALIEN_BOMB_SPEED, surface=surf)


# ---------------------------------------------------------------------------
# BunkerTile
# ---------------------------------------------------------------------------


class BunkerTile(Entity):
    """
    One pixel-tile block within a defensive bunker.

    Each tile tracks its own health; when health reaches zero the tile
    disappears.  The Bunker class manages a grid of these.

    Attributes
    ----------
    health : int
        Remaining hit-points for this tile.
    max_health : int
        Maximum health used for damage-colour calculation.
    """

    def __init__(self, x: float, y: float) -> None:
        self.max_health: int = C.BUNKER_MAX_HEALTH
        self.health: int = self.max_health
        surf = SPR.make_bunker_tile_surface(self.health, self.max_health)
        super().__init__(x, y, surf)

    # ------------------------------------------------------------------
    def take_damage(self) -> bool:
        """
        Apply one point of damage to this tile.

        Returns
        -------
        bool
            True if the tile has been destroyed (health ≤ 0).
        """
        self.health -= 1
        if self.health <= 0:
            self.alive = False
            return True
        # Refresh the damaged surface
        self.surface = SPR.make_bunker_tile_surface(self.health, self.max_health)
        return False
