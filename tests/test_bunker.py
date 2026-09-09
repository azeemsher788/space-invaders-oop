import pytest
from bunker import Bunker
from entities import Laser
import constants as C

def test_bunker_initialization():
    bunker = Bunker(0, 0)
    assert len(bunker.tiles) > 0
    assert not bunker.is_destroyed

def test_bunker_takes_damage():
    bunker = Bunker(0, 0)
    initial_health = bunker.tiles[0].health
    
    # Create a projectile overlapping the first tile
    tile_rect = bunker.tiles[0].rect
    proj = Laser(tile_rect.x, tile_rect.y)
    
    hit = bunker.check_projectile_collision(proj)
    
    assert hit is True
    assert not proj.alive
    assert bunker.tiles[0].health == initial_health - 1

def test_bunker_destruction():
    bunker = Bunker(0, 0)
    # Destroy all tiles
    for tile in bunker.tiles:
        tile.health = 0
        tile.alive = False
    
    bunker.purge_dead_tiles()
    assert bunker.is_destroyed
    assert len(bunker.tiles) == 0
