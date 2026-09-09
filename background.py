"""
background.py
=============
Parallax starfield background renderer.

Stars are divided into STAR_LAYERS depth layers, each scrolling at a
different speed to create a convincing sense of depth.  The star positions
are generated once at construction time so there is no per-frame heap
allocation.
"""

from __future__ import annotations

import random

import pygame

import constants as C


class Star:
    """A single background star with position, layer, and brightness."""

    __slots__ = ("x", "y", "layer", "brightness", "speed")

    def __init__(self) -> None:
        self.x: float = random.uniform(0, C.SCREEN_WIDTH)
        self.y: float = random.uniform(0, C.SCREEN_HEIGHT)
        self.layer: int = random.randint(0, C.STAR_LAYERS - 1)
        # Brighter = closer (higher layer number)
        base = 80 + self.layer * 50
        self.brightness: int = min(255, base + random.randint(-20, 20))
        self.speed: float = 0.05 + self.layer * 0.04


class Starfield:
    """
    Manages and renders a parallax star background.

    Parameters
    ----------
    count : int
        Total number of stars to generate.
    """

    def __init__(self, count: int = C.NUM_STARS) -> None:
        self._stars: list[Star] = [Star() for _ in range(count)]

    def update(self) -> None:
        """Slowly drift stars downward to simulate forward motion."""
        for s in self._stars:
            s.y += s.speed
            if s.y > C.SCREEN_HEIGHT:
                s.y = 0.0
                s.x = random.uniform(0, C.SCREEN_WIDTH)

    def draw(self, screen: pygame.Surface) -> None:
        """Render all stars as single pixels with layer-dependent brightness."""
        for s in self._stars:
            b = s.brightness
            color = (b, b, min(255, b + 30))  # slight blue tint
            screen.set_at((int(s.x), int(s.y)), color)
