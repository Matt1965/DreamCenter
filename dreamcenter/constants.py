import pygame as pg
from typing import Dict, Tuple

DESIRED_FPS = 60

SCREENRECT = pg.Rect(0, 0, 1280, 720)

SPRITES = {
    "edwardo": "edwardo.png",
    "edwardowithgun": "edwardowithgun.png",
    "background": "main_bg.png",
}

# Holds the converted and imported sprite images. The key is a tuple
# of (flipped_x, flipped_y, sprite_name)
IMAGE_SPRITES: Dict[Tuple[bool, bool, str], pg.Surface] = {}