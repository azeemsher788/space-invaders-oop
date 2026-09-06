"""
hud.py
======
HUD (Heads-Up Display) — responsible for rendering all overlay UI elements:
score, high score, lives counter, level indicator, and game-state messages
(GAME OVER, PAUSED, LEVEL COMPLETE).

Design note
-----------
The HUD is strictly a *renderer* — it reads from the PlayerShip and game state
but never modifies them.  This clean read-only contract means the HUD can be
swapped, tested, or replaced without touching game logic.
"""

from __future__ import annotations

import pygame

import constants as C
from entities import PlayerShip


class HUD:
    """
    Stateless overlay renderer for the game's heads-up display.

    All font objects are cached at construction time so we pay the
    initialisation cost once, not every frame.

    Parameters
    ----------
    screen : pygame.Surface
        The main display surface (stored as a reference for convenience).
    """

    def __init__(self, screen: pygame.Surface) -> None:
        self._screen = screen
        self._font_large  = pygame.font.SysFont("consolas", C.HUD_FONT_SIZE_LARGE, bold=True)
        self._font_small  = pygame.font.SysFont("consolas", C.HUD_FONT_SIZE_SMALL)
        self._font_title  = pygame.font.SysFont("consolas", 52, bold=True)
        self._font_medium = pygame.font.SysFont("consolas", 32, bold=True)
        self._ship_icon   = pygame.transform.scale(
            self._make_mini_ship(), (28, 18)
        )
        self._high_score: int = 0

    # ------------------------------------------------------------------

    @staticmethod
    def _make_mini_ship() -> pygame.Surface:
        """Return a tiny ship icon for the lives counter."""
        import sprites as SPR
        return SPR.make_player_surface()

    # ------------------------------------------------------------------

    def update_high_score(self, score: int) -> None:
        """Update the stored high score if *score* is greater."""
        if score > self._high_score:
            self._high_score = score

    # ------------------------------------------------------------------

    def draw(self, player: PlayerShip, level: int) -> None:
        """
        Render all HUD elements onto the stored screen surface.

        Parameters
        ----------
        player : PlayerShip
            Source of score and lives data.
        level : int
            Current game level number.
        """
        m = C.HUD_MARGIN
        sw = C.SCREEN_WIDTH

        # --- Score label & value ---
        score_label = self._font_small.render("SCORE", True, C.YELLOW)
        score_val   = self._font_large.render(f"{player.score:06d}", True, C.WHITE)
        self._screen.blit(score_label, (m, m))
        self._screen.blit(score_val,   (m, m + 20))

        # --- High score ---
        hi_label = self._font_small.render("HI-SCORE", True, C.YELLOW)
        hi_val   = self._font_large.render(f"{self._high_score:06d}", True, C.WHITE)
        hi_x = sw // 2 - hi_val.get_width() // 2
        self._screen.blit(hi_label, (sw // 2 - hi_label.get_width() // 2, m))
        self._screen.blit(hi_val,   (hi_x, m + 20))

        # --- Level ---
        lvl_text = self._font_small.render(f"LEVEL  {level}", True, C.CYAN)
        self._screen.blit(lvl_text, (sw - lvl_text.get_width() - m, m))

        # --- Lives counter ---
        lives_label = self._font_small.render("LIVES", True, C.YELLOW)
        self._screen.blit(lives_label, (m, C.SCREEN_HEIGHT - 36))
        for i in range(player.lives):
            self._screen.blit(
                self._ship_icon,
                (m + 54 + i * 34, C.SCREEN_HEIGHT - 38)
            )

        # --- Bottom neon dividers ---
        pygame.draw.line(self._screen, C.CYAN,
                         (0, 65), (sw, 65), 1)
        pygame.draw.line(self._screen, C.GREEN,
                         (0, C.SCREEN_HEIGHT - 48),
                         (sw, C.SCREEN_HEIGHT - 48), 1)

    # ------------------------------------------------------------------

    def draw_message(self, lines: list[str], colors: list[tuple],
                     y_start: int = 0) -> None:
        """
        Render a centred multi-line message on screen.

        Parameters
        ----------
        lines : list[str]
            Text lines to render top-to-bottom.
        colors : list[tuple]
            RGB colour for each line (must match length of *lines*).
        y_start : int
            Vertical offset from centre; 0 = vertically centred.
        """
        total_h = len(lines) * 60
        start_y = (C.SCREEN_HEIGHT - total_h) // 2 + y_start
        for i, (text, color) in enumerate(zip(lines, colors)):
            font = self._font_title if i == 0 else self._font_medium
            rendered = font.render(text, True, color)
            x = C.SCREEN_WIDTH  // 2 - rendered.get_width() // 2
            y = start_y + i * 60
            self._screen.blit(rendered, (x, y))

    # ------------------------------------------------------------------

    def draw_score_popup(self, text: str, x: int, y: int,
                         alpha: int = 255) -> None:
        """
        Render a floating score popup (e.g. "+150") at an arbitrary position.

        Parameters
        ----------
        text : str
            Text to display.
        x, y : int
            Pixel position.
        alpha : int
            Transparency 0-255.
        """
        surf = self._font_small.render(text, True, C.YELLOW)
        surf.set_alpha(alpha)
        self._screen.blit(surf, (x, y))

    # ------------------------------------------------------------------

    def draw_ufo_score(self, value: int, x: int, y: int) -> None:
        """Render the UFO score label at the given position."""
        text = self._font_medium.render(str(value), True, (255, 40, 40))
        self._screen.blit(text, (x, y))
