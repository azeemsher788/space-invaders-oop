import pytest
from fleet import AlienFleet, _MovePhase
import constants as C

def test_fleet_initialization():
    fleet = AlienFleet(level=1)
    assert len(fleet.aliens) == C.ALIEN_ROWS * C.ALIEN_COLS
    assert fleet._phase == _MovePhase.HORIZONTAL

def test_fleet_empty():
    fleet = AlienFleet(level=1)
    # We need to copy the list because kill_alien modifies it
    for alien in list(fleet.aliens):
        fleet.kill_alien(alien)
    assert fleet.is_empty
    
def test_fleet_scaling_speed():
    fleet = AlienFleet(level=1)
    initial_interval = fleet._move_interval
    
    # Kill half the aliens
    half_count = len(fleet.aliens) // 2
    for alien in list(fleet.aliens)[:half_count]:
        fleet.kill_alien(alien)
        
    scaled_interval = fleet._move_interval
    
    # Speed should increase (interval decreases) as aliens die
    assert scaled_interval < initial_interval
