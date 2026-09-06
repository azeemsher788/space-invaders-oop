"""
engine.py
=========
GameEngine — the top-level orchestrator for the entire Space Invaders game.

Responsibilities
----------------
* Initialise pygame and create the display window.
* Own the canonical game-loop (fixed-step update + uncapped render).
* Dispatch keyboard events to entity key-state flags (non-blocking input).
* Run all collision-detection passes each frame.
* Coordinate state transitions: TITLE → PLAYING → LEVEL_COMPLETE →
  GAME_OVER → (restart).
* Delegate rendering to the correct subsystems in correct Z-order.

Game-loop design
----------------
The engine targets C.FPS using pygame.Clock.tick(FPS) which caps the loop
and returns the actual delta-time (dt) in milliseconds.  Physics and AI use
dt so that updates remain correct even when frame-rate drops.  Rendering
always uses the most up-to-date entity positions so motion appears smooth.

Collision detection strategy
-----------------------------
We use a two-phase approach:
  1. Broad phase: only check projectiles against entities whose bounding
     boxes are in plausible proximity (coarse layer by Y band).
  2. Narrow phase: pygame.Rect.colliderect() — O(1) AABB test.

For Space Invaders' entity counts (< 60 aliens, < 5 projectiles, < ~800
bunker tiles) this is entirely sufficient without a spatial hash.
"""

from __future__ import annotations

import random
import sys
from enum import Enum, auto
from typing import Optional

import pygame

import constants as C
from entities import PlayerShip, UFO, Laser, Bomb
from fleet import AlienFleet
from bunker import Bunker, build_bunkers
from hud import HUD
from background import Starfield
from vfx import VFXManager


# ---------------------------------------------------------------------------
# Game-state enumeration
# ---------------------------------------------------------------------------

class GameState(Enum):
    TITLE          = auto()
    PLAYING        = auto()
    LEVEL_COMPLETE = auto()
    GAME_OVER      = auto()
    PAUSED         = auto()


# ---------------------------------------------------------------------------
# GameEngine
# ---------------------------------------------------------------------------

class GameEngine:
    """
    Central controller for the Space Invaders game.

    Instantiate once and call :py:meth:`run` to start the main loop.

    Attributes
    ----------
    screen : pygame.Surface
        Main display surface.
    clock : pygame.time.Clock
        Frame-rate limiter and dt source.
    state : GameState
        Current game-state machine phase.
    player : PlayerShip
    fleet : AlienFleet
    bunkers : list[Bunker]
    lasers : list[Laser]
    ufo : UFO | None
    hud : HUD
    starfield : Starfield
    vfx : VFXManager
    level : int
        Current level (1-indexed).
    """

    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption(C.TITLE)
        self.screen: pygame.Surface = pygame.display.set_mode(
            (C.SCREEN_WIDTH, C.SCREEN_HEIGHT)
        )
        self.clock: pygame.time.Clock = pygame.time.Clock()

        # --- sub-systems ---
        self.starfield: Starfield = Starfield()
        self.vfx: VFXManager = VFXManager()

        # --- game state ---
        self.level: int = 1
        self.state: GameState = GameState.TITLE
        self._state_timer: int = 0    # timestamp of last state transition

        # --- title screen ---
        self._title_font = pygame.font.SysFont("consolas", 58, bold=True)
        self._sub_font   = pygame.font.SysFont("consolas", 24)

        # --- create game objects (will be reset per game) ---
        self.player: PlayerShip = PlayerShip()
        self.fleet: AlienFleet  = AlienFleet(self.level)
        self.bunkers: list[Bunker] = build_bunkers()
        self.lasers: list[Laser]   = []
        self.ufo: Optional[UFO]    = None
        self._last_ufo_time: int   = pygame.time.get_ticks()
        self._ufo_killed_timer: int = 0   # shows score label briefly

        self.hud: HUD = HUD(self.screen)

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def run(self) -> None:
        """
        Start and run the main game loop until the window is closed.

        The loop structure is:
          1. Process events (O(events) per frame)
          2. Update state   (O(entities) per frame)
          3. Detect collisions
          4. Render
          5. Flip display buffer
        """
        while True:
            dt: int = self.clock.tick(C.FPS)
            self._process_events()
            self._update(dt)
            self._render()
            pygame.display.flip()

    # ------------------------------------------------------------------
    # Event processing
    # ------------------------------------------------------------------

    def _process_events(self) -> None:
        """
        Dispatch all pending pygame events.

        Key-press/release events update boolean flags on the PlayerShip
        rather than firing immediate actions — this eliminates OS key-repeat
        delay and gives precise per-frame input control.
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.KEYDOWN:
                self._on_key_down(event.key)

            elif event.type == pygame.KEYUP:
                self._on_key_up(event.key)

    def _on_key_down(self, key: int) -> None:
        """Handle key-press events for the current game state."""
        if self.state == GameState.TITLE:
            if key in (pygame.K_RETURN, pygame.K_SPACE):
                self._start_game()
            return

        if self.state == GameState.GAME_OVER:
            if key in (pygame.K_RETURN, pygame.K_r):
                self._start_game()
            return

        if self.state == GameState.LEVEL_COMPLETE:
            return   # auto-transitions after a short delay

        # --- Playing / Paused ---
        if key == pygame.K_p:
            self._toggle_pause()
            return

        if self.state == GameState.PAUSED:
            return

        if key in (pygame.K_LEFT, pygame.K_a):
            self.player.move_left = True
        elif key in (pygame.K_RIGHT, pygame.K_d):
            self.player.move_right = True
        elif key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
            self.player.fire_pressed = True

    def _on_key_up(self, key: int) -> None:
        """Clear movement/fire flags on key-release."""
        if key in (pygame.K_LEFT, pygame.K_a):
            self.player.move_left = False
        elif key in (pygame.K_RIGHT, pygame.K_d):
            self.player.move_right = False
        elif key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
            self.player.fire_pressed = False

    # ------------------------------------------------------------------
    # State management
    # ------------------------------------------------------------------

    def _start_game(self) -> None:
        """Reset all game objects and transition to PLAYING state."""
        self.level  = 1
        self.player = PlayerShip()
        self.fleet  = AlienFleet(self.level)
        self.bunkers = build_bunkers()
        self.lasers  = []
        self.ufo     = None
        self._last_ufo_time = pygame.time.get_ticks()
        self.vfx = VFXManager()
        self.state = GameState.PLAYING

    def _advance_level(self) -> None:
        """Move to the next level: rebuild fleet and bunkers, keep player."""
        self.level += 1
        self.fleet   = AlienFleet(self.level)
        self.bunkers = build_bunkers()
        self.lasers  = []
        self.ufo     = None
        self._last_ufo_time = pygame.time.get_ticks()
        self.state = GameState.PLAYING

    def _toggle_pause(self) -> None:
        if self.state == GameState.PAUSED:
            self.state = GameState.PLAYING
        else:
            self.state = GameState.PAUSED

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def _update(self, dt: int) -> None:
        """Route per-frame logic to the appropriate state handler."""
        self.starfield.update()
        self.vfx.update(dt)

        if self.state == GameState.PLAYING:
            self._update_playing(dt)
        elif self.state == GameState.LEVEL_COMPLETE:
            self._update_level_complete()
        elif self.state == GameState.GAME_OVER:
            self.hud.update_high_score(self.player.score)

    def _update_playing(self, dt: int) -> None:
        """All per-frame logic while the game is actively running."""

        # --- Player ---
        self.player.update(dt)
        if self.player.fire_pressed:
            laser = self.player.try_fire()
            if laser:
                self.lasers.append(laser)

        # --- Lasers ---
        for laser in self.lasers:
            laser.update(dt)
        self.lasers = [l for l in self.lasers if l.alive]

        # --- Fleet ---
        self.fleet.update(dt)

        # --- UFO ---
        self._update_ufo(dt)

        # --- Collisions ---
        self._detect_collisions()

        # --- Win / Lose conditions ---
        if self.fleet.is_empty:
            self.state = GameState.LEVEL_COMPLETE
            self._state_timer = pygame.time.get_ticks()
            return

        if self.fleet.has_invaded() or self.player.lives <= 0:
            self.state = GameState.GAME_OVER
            self.hud.update_high_score(self.player.score)
            return

    def _update_level_complete(self) -> None:
        """Auto-advance to the next level after a brief celebration pause."""
        if pygame.time.get_ticks() - self._state_timer > 2_500:
            self._advance_level()

    # ------------------------------------------------------------------
    # UFO logic
    # ------------------------------------------------------------------

    def _update_ufo(self, dt: int) -> None:
        """Spawn and update the UFO mystery ship."""
        now = pygame.time.get_ticks()

        if self.ufo is None:
            # Try to spawn
            if now - self._last_ufo_time > C.UFO_SPAWN_INTERVAL:
                if random.random() < C.UFO_SPAWN_CHANCE:
                    self.ufo = UFO()
        else:
            self.ufo.update(dt)
            if not self.ufo.alive:
                self.ufo = None
                self._last_ufo_time = now

    # ------------------------------------------------------------------
    # Collision detection
    # ------------------------------------------------------------------

    def _detect_collisions(self) -> None:
        """
        Run all collision passes for the current frame.

        Passes (in priority order):
          1. Player lasers  vs. Aliens
          2. Player lasers  vs. UFO
          3. Player lasers  vs. Bunker tiles
          4. Alien bombs    vs. Bunker tiles
          5. Alien bombs    vs. Player ship
        """
        self._laser_vs_aliens()
        self._laser_vs_ufo()
        self._laser_vs_bunkers()
        self._bombs_vs_bunkers()
        self._bombs_vs_player()

    def _laser_vs_aliens(self) -> None:
        """Check each alive laser against all alive aliens."""
        for laser in self.lasers:
            if not laser.alive:
                continue
            for alien in self.fleet.aliens[:]:   # iterate a snapshot
                if laser.rect.colliderect(alien.rect):
                    pts = self.fleet.kill_alien(alien)
                    self.player.score += pts
                    self.hud.update_high_score(self.player.score)
                    laser.alive = False
                    # VFX
                    cx = int(alien.x + C.ALIEN_WIDTH  // 2)
                    cy = int(alien.y + C.ALIEN_HEIGHT // 2)
                    self.vfx.spawn_explosion(cx, cy, 32)
                    self.vfx.spawn_popup(f"+{pts}", cx - 12, cy - 20)
                    break

    def _laser_vs_ufo(self) -> None:
        """Check if the player's laser has hit the UFO."""
        if self.ufo is None or not self.ufo.alive:
            return
        for laser in self.lasers:
            if not laser.alive:
                continue
            if laser.rect.colliderect(self.ufo.rect):
                pts = self.ufo.score_value
                self.player.score += pts
                self.hud.update_high_score(self.player.score)
                laser.alive = False
                cx = int(self.ufo.x + 26)
                cy = int(self.ufo.y + 12)
                self.vfx.spawn_explosion(cx, cy, 40)
                self.vfx.spawn_ufo_score(pts, cx - 16, cy - 20)
                self.ufo.alive = False
                self.ufo = None
                self._last_ufo_time = pygame.time.get_ticks()
                break

    def _laser_vs_bunkers(self) -> None:
        """Check player lasers against all bunker tiles."""
        for laser in self.lasers:
            if not laser.alive:
                continue
            for bunker in self.bunkers:
                if bunker.check_projectile_collision(laser):
                    cx, cy = int(laser.x), int(laser.y)
                    self.vfx.spawn_explosion(cx, cy, 12)
                    break

    def _bombs_vs_bunkers(self) -> None:
        """Check alien bombs against all bunker tiles."""
        for bomb in self.fleet.bombs:
            if not bomb.alive:
                continue
            for bunker in self.bunkers:
                if bunker.check_projectile_collision(bomb):
                    cx, cy = int(bomb.x), int(bomb.y)
                    self.vfx.spawn_explosion(cx, cy, 12)
                    break
        # Prune destroyed tiles
        for bunker in self.bunkers:
            bunker.purge_dead_tiles()

    def _bombs_vs_player(self) -> None:
        """Check alien bombs against the player ship."""
        if self.player.is_invincible:
            return
        for bomb in self.fleet.bombs:
            if not bomb.alive:
                continue
            if bomb.rect.colliderect(self.player.rect):
                bomb.alive = False
                self.player.hit()
                cx = int(self.player.x + C.PLAYER_WIDTH  // 2)
                cy = int(self.player.y + C.PLAYER_HEIGHT // 2)
                self.vfx.spawn_explosion(cx, cy, 48)

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def _render(self) -> None:
        """Full render pass — background → entities → HUD → overlays."""
        # 1. Background
        self.screen.fill(C.DARK_BG)
        self.starfield.draw(self.screen)

        if self.state == GameState.TITLE:
            self._render_title()
            return

        # 2. Bunkers
        for bunker in self.bunkers:
            bunker.draw(self.screen)

        # 3. Entities
        self.fleet.draw(self.screen)
        self.player.draw(self.screen)

        for laser in self.lasers:
            laser.draw(self.screen)

        if self.ufo and self.ufo.alive:
            self.ufo.draw(self.screen)

        # 4. VFX (above entities, below HUD)
        self.vfx.draw(self.screen)

        # 5. HUD (always on top)
        self.hud.draw(self.player, self.level)

        # 6. State overlays
        if self.state == GameState.PAUSED:
            self._render_pause_overlay()
        elif self.state == GameState.GAME_OVER:
            self._render_game_over()
        elif self.state == GameState.LEVEL_COMPLETE:
            self._render_level_complete()

    # ------------------------------------------------------------------
    # Overlay renderers
    # ------------------------------------------------------------------

    def _render_title(self) -> None:
        """Animated title screen with pulsing glow effect."""
        now = pygame.time.get_ticks()

        # --- SPACE INVADERS title ---
        pulse = abs(((now // 8) % 255) - 127)
        title_color = (255, 80 + pulse // 3, 0)
        title_surf = self._title_font.render("SPACE INVADERS", True, title_color)
        tx = C.SCREEN_WIDTH  // 2 - title_surf.get_width() // 2
        ty = C.SCREEN_HEIGHT // 2 - 140
        self.screen.blit(title_surf, (tx, ty))

        # --- Sub-heading ---
        sub = self._sub_font.render("by  Azeem Sher  —  github.com/azeemsher788", True, C.CYAN)
        self.screen.blit(sub, (C.SCREEN_WIDTH // 2 - sub.get_width() // 2, ty + 80))

        # --- Score table ---
        rows = [
            ("= = =", C.MAGENTA, "30 PTS"),
            ("> < >", C.CYAN,    "20 PTS"),
            ("v ^ v", C.GREEN,   "10 PTS"),
            (" UFO ", (255, 40, 40), "??? PTS"),
        ]
        sy = ty + 145
        for sym, col, pts in rows:
            s1 = self._sub_font.render(sym, True, col)
            s2 = self._sub_font.render(f"= {pts}", True, C.WHITE)
            self.screen.blit(s1, (C.SCREEN_WIDTH // 2 - 100, sy))
            self.screen.blit(s2, (C.SCREEN_WIDTH // 2 - 10, sy))
            sy += 34

        # --- Blinking PRESS START ---
        if (now // 500) % 2 == 0:
            ps = self._sub_font.render("PRESS  ENTER  TO  START", True, C.YELLOW)
            self.screen.blit(ps, (C.SCREEN_WIDTH // 2 - ps.get_width() // 2,
                                  ty + 305))

        # --- Controls ---
        ctrl = self._sub_font.render(
            "A / ← → / D  move    SPACE  fire    P  pause",
            True, (120, 120, 160)
        )
        self.screen.blit(ctrl, (C.SCREEN_WIDTH // 2 - ctrl.get_width() // 2,
                                C.SCREEN_HEIGHT - 50))

    def _render_pause_overlay(self) -> None:
        """Semi-transparent darkening overlay with PAUSED text."""
        overlay = pygame.Surface((C.SCREEN_WIDTH, C.SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        self.screen.blit(overlay, (0, 0))
        self.hud.draw_message(
            ["PAUSED", "Press P to resume"],
            [C.YELLOW, C.WHITE]
        )

    def _render_game_over(self) -> None:
        """Game-over overlay with score and restart prompt."""
        overlay = pygame.Surface((C.SCREEN_WIDTH, C.SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))
        self.hud.draw_message(
            ["GAME OVER", f"Score: {self.player.score:,}", "Press ENTER or R to retry"],
            [C.RED, C.WHITE, C.YELLOW]
        )

    def _render_level_complete(self) -> None:
        """Level-complete banner."""
        overlay = pygame.Surface((C.SCREEN_WIDTH, C.SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        self.screen.blit(overlay, (0, 0))
        self.hud.draw_message(
            [f"LEVEL {self.level} CLEAR!", "Get ready…"],
            [C.GREEN, C.CYAN]
        )
