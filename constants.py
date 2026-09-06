"""
constants.py
============
Single source of truth for all game-wide constants and tunable parameters.
Centralising these values here makes tweaking game-feel trivially easy
without hunting through business-logic files.
"""

# ---------------------------------------------------------------------------
# Display
# ---------------------------------------------------------------------------
SCREEN_WIDTH: int  = 900
SCREEN_HEIGHT: int = 700
FPS: int           = 60
TITLE: str         = "Space Invaders — by Azeem Sher"

# ---------------------------------------------------------------------------
# Colours  (R, G, B)
# ---------------------------------------------------------------------------
BLACK        = (  0,   0,   0)
WHITE        = (255, 255, 255)
GREEN        = ( 57, 255, 119)   # neon-green aliens (row 0)
CYAN         = (  0, 255, 255)   # mid-row aliens
MAGENTA      = (255,  50, 200)   # top-row aliens
YELLOW       = (255, 220,   0)   # HUD accent
RED          = (255,  50,  50)   # enemy bombs
ORANGE       = (255, 140,   0)   # player laser
DARK_BG      = (  5,   5,  20)   # near-black space background
BUNKER_GREEN = ( 30, 180,  30)   # bunker tile colour
STAR_COLOR   = (180, 180, 220)   # parallax star tint
SHIELD_COLOR = (100, 220, 255)   # player shield VFX

# ---------------------------------------------------------------------------
# Player
# ---------------------------------------------------------------------------
PLAYER_SPEED: int          = 5
PLAYER_LASER_COOLDOWN: int = 400   # ms between shots
PLAYER_LASER_SPEED: int    = 10    # pixels per frame upward
PLAYER_LIVES: int          = 3
PLAYER_WIDTH: int          = 52
PLAYER_HEIGHT: int         = 32
PLAYER_Y_OFFSET: int       = 60    # distance from screen bottom

# ---------------------------------------------------------------------------
# Alien Fleet
# ---------------------------------------------------------------------------
ALIEN_ROWS: int           = 5
ALIEN_COLS: int           = 11
ALIEN_H_SPACING: int      = 60
ALIEN_V_SPACING: int      = 50
ALIEN_FLEET_TOP: int      = 80
ALIEN_FLEET_LEFT: int     = 60
ALIEN_STEP_DOWN: int      = 20
ALIEN_WIDTH: int          = 36
ALIEN_HEIGHT: int         = 28

ALIEN_MOVE_INTERVAL_MAX: int = 800
ALIEN_MOVE_INTERVAL_MIN: int = 80

ALIEN_BOMB_SPEED: int    = 5
ALIEN_BOMB_CHANCE: float = 0.0015
ALIEN_MAX_BOMBS: int     = 4

ALIEN_SCORE = {0: 10, 1: 10, 2: 20, 3: 20, 4: 30}

# ---------------------------------------------------------------------------
# Bunkers / Defensive Barriers
# ---------------------------------------------------------------------------
BUNKER_COUNT: int        = 4
BUNKER_Y: int            = SCREEN_HEIGHT - 160
BUNKER_TILE_SIZE: int    = 8
BUNKER_MAX_HEALTH: int   = 3

# ---------------------------------------------------------------------------
# UFO / Mystery Ship
# ---------------------------------------------------------------------------
UFO_SPEED: int           = 3
UFO_SCORE: int           = 150
UFO_SPAWN_INTERVAL: int  = 25_000
UFO_SPAWN_CHANCE: float  = 0.004

# ---------------------------------------------------------------------------
# HUD
# ---------------------------------------------------------------------------
HUD_FONT_SIZE_LARGE: int  = 28
HUD_FONT_SIZE_SMALL: int  = 18
HUD_MARGIN: int           = 12

# ---------------------------------------------------------------------------
# Visual effects
# ---------------------------------------------------------------------------
EXPLOSION_DURATION: int  = 300
NUM_STARS: int           = 120
STAR_LAYERS: int         = 3
