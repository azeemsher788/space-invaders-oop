"""
vfx.py
======
Visual-Effects system — manages short-lived particle events such as
explosions and floating score popups.

All VFX objects are lightweight data containers updated and drawn each frame
by the VFXManager.  When an effect's lifetime expires it is flagged dead
and pruned from the active list.
"""

from __future__ import annotations

import pygame

import constants as C
import sprites as SPR

# ---------------------------------------------------------------------------
# Individual VFX objects
# ---------------------------------------------------------------------------


class Explosion:
    """
    A one-shot starburst explosion at a given position.

    Attributes
    ----------
    x, y : int
        Centre pixel position.
    _surface : pygame.Surface
        Pre-rendered starburst sprite.
    _born : int
        pygame.time.get_ticks() at creation.
    alive : bool
        Set to False when the duration has elapsed.
    """

    def __init__(self, x: int, y: int, size: int = 30) -> None:
        self.x: int = x - size // 2
        self.y: int = y - size // 2
        self._surface: pygame.Surface = SPR.make_explosion_surface(size)
        self._born: int = pygame.time.get_ticks()
        self.alive: bool = True

    def update(self) -> None:
        if pygame.time.get_ticks() - self._born > C.EXPLOSION_DURATION:
            self.alive = False

    def draw(self, screen: pygame.Surface) -> None:
        # Fade alpha over lifetime
        elapsed = pygame.time.get_ticks() - self._born
        alpha = max(0, 255 - int(255 * elapsed / C.EXPLOSION_DURATION))
        self._surface.set_alpha(alpha)
        screen.blit(self._surface, (self.x, self.y))


class ScorePopup:
    """
    A floating "+NNN" label that rises and fades.

    Attributes
    ----------
    text : str
        Display text (e.g. "+150").
    x, y : float
        Current render position (y rises over time).
    alive : bool
        Cleared when alpha reaches zero.
    """

    _DURATION: int = 900  # ms
    _RISE_SPEED: float = 0.04  # pixels per ms

    def __init__(self, text: str, x: int, y: int) -> None:
        self.text: str = text
        self.x: float = float(x)
        self.y: float = float(y)
        self._born: int = pygame.time.get_ticks()
        self.alive: bool = True
        self._font = pygame.font.SysFont("consolas", 18, bold=True)

    def update(self, dt: int) -> None:
        self.y -= self._RISE_SPEED * dt
        if pygame.time.get_ticks() - self._born > self._DURATION:
            self.alive = False

    def draw(self, screen: pygame.Surface) -> None:
        elapsed = pygame.time.get_ticks() - self._born
        alpha = max(0, 255 - int(255 * elapsed / self._DURATION))
        surf = self._font.render(self.text, True, C.YELLOW)
        surf.set_alpha(alpha)
        screen.blit(surf, (int(self.x), int(self.y)))


class UFOScoreDisplay:
    """Brief stationary score label shown when the UFO is destroyed."""

    _DURATION: int = 1200

    def __init__(self, value: int, x: int, y: int) -> None:
        self._text: str = str(value)
        self.x: int = x
        self.y: int = y
        self._born: int = pygame.time.get_ticks()
        self.alive: bool = True
        self._font = pygame.font.SysFont("consolas", 26, bold=True)

    def update(self, _dt: int) -> None:  # noqa: ARG002
        if pygame.time.get_ticks() - self._born > self._DURATION:
            self.alive = False

    def draw(self, screen: pygame.Surface) -> None:
        elapsed = pygame.time.get_ticks() - self._born
        alpha = max(0, 255 - int(255 * elapsed / self._DURATION))
        surf = self._font.render(self._text, True, (255, 60, 60))
        surf.set_alpha(alpha)
        screen.blit(surf, (self.x, self.y))


# ---------------------------------------------------------------------------
# Manager
# ---------------------------------------------------------------------------


class VFXManager:
    """
    Central registry for all active visual effects.

    Call :py:meth:`spawn_explosion` / :py:meth:`spawn_popup` etc. to add
    effects, then call :py:meth:`update` and :py:meth:`draw` each frame.
    """

    def __init__(self) -> None:
        self._explosions: list[Explosion] = []
        self._popups: list[ScorePopup] = []
        self._ufo_displays: list[UFOScoreDisplay] = []

    # ------------------------------------------------------------------

    def spawn_explosion(self, cx: int, cy: int, size: int = 30) -> None:
        """Add an explosion centred at (cx, cy)."""
        self._explosions.append(Explosion(cx, cy, size))

    def spawn_popup(self, text: str, x: int, y: int) -> None:
        """Add a floating score text popup."""
        self._popups.append(ScorePopup(text, x, y))

    def spawn_ufo_score(self, value: int, x: int, y: int) -> None:
        """Show the UFO destroyed score label."""
        self._ufo_displays.append(UFOScoreDisplay(value, x, y))

    # ------------------------------------------------------------------

    def update(self, dt: int) -> None:
        """Advance all active effects; prune expired ones."""
        for e in self._explosions:
            e.update()
        for p in self._popups:
            p.update(dt)
        for u in self._ufo_displays:
            u.update(dt)

        self._explosions = [e for e in self._explosions if e.alive]
        self._popups = [p for p in self._popups if p.alive]
        self._ufo_displays = [u for u in self._ufo_displays if u.alive]

    def draw(self, screen: pygame.Surface) -> None:
        """Render all active effects."""
        for e in self._explosions:
            e.draw(screen)
        for p in self._popups:
            p.draw(screen)
        for u in self._ufo_displays:
            u.draw(screen)
