import pygame as pg
from typing import Dict, Tuple

DESIRED_FPS = 60

# Tile width and height.
TILE_HEIGHT = 50
TILE_WIDTH = 50

# Number of tiles in the Y and X axes
TILES_Y = 20
TILES_X = 32

FONT_NAME = None
FONT_SIZE = 20

SCREENRECT = pg.Rect(0, 0, TILE_WIDTH * TILES_X, TILE_HEIGHT * TILES_Y)

SPRITES = {
    "edwardo": "edwardo.png",
    "edwardowithgun": "edwardowithgun.png",
    "background": "background.png",
    "logo": "logo.png",
    "edit_background": "edit_background.png",
}

# Holds the converted and imported sprite images. The key is a tuple
# of (flipped_x, flipped_y, sprite_name)
IMAGE_SPRITES: Dict[Tuple[bool, bool, str], pg.Surface] = {}

ALLOWED_BG = [
    "bricks1",

]

SOUNDS = {}

