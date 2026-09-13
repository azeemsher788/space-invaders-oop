import os

import pygame
import pytest

# Initialize pygame headless for tests
os.environ["SDL_VIDEODRIVER"] = "dummy"


@pytest.fixture(scope="session", autouse=True)
def setup_pygame():
    pygame.init()
    pygame.display.set_mode((1, 1))
    yield
    pygame.quit()
