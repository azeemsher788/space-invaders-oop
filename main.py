"""
Space Invaders — Modern OOP Implementation
==========================================
Entry point script.

Run this module to launch the game:
    $ python main.py
"""

import sys

from engine import GameEngine


def main() -> None:
    """Instantiate and run the main game engine."""
    try:
        engine = GameEngine()
        engine.run()
    except KeyboardInterrupt:
        print("\nExiting Space Invaders. Goodbye!")
        sys.exit(0)


if __name__ == "__main__":
    main()
