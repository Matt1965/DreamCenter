import pygame as pg
from typing import Dict, Tuple
from itertools import chain

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

MOUSE_LEFT, MOUSE_MIDDLE, MOUSE_RIGHT = 1, 2, 3

SPRITES = {
    "edwardo": "edwardo.png",
    "edwardowithgun": "edwardowithgun.png",
    "background": "background.png",
    "logo": "logo.png",
    "edit_background": "edit_background.png",
    "play_background": "play_background.png",
    "blank": "blank.png",
    "bricks1": "bricks1.png",
    "bricks2": "bricks2.png",
    "bricks3": "bricks3.png",
    "bloody_floor": "bloody_floor.png",
    "projectile": "projectile.png",
    "skeleton": "Skeleton_Walk_000.png",
    "collision_mask": "collision_mask.png",
    "pause_menu": "pause_menu.png",
    "game_over_splash": "game_over_splash.png",
    "half_heart": "half_heart.png",
    "empty_heart": "empty_heart.png",
    "black": "black.png",
    "wood_door": "wood_door.png",
    "map_4_way": "map_4_way.png",
    "map_3_way": "map_3_way.png",
    "map_2_way": "map_2_way.png",
    "map_2_way_straight": "map_2_way_straight.png",
    "map_1_way": "map_1_way.png",
    "map_border": "map_border.png",
    "map_display": "map_display.png",
    "map_you_are_here": "map_you_are_here.png",
    "money": "money_000.png",
    "text": "blank.png",
    "buff_accumen": "buff_accumen.png",
    "buff_corpus": "buff_corpus.png",
    "buff_intuitus": "buff_intuitus.png",
    "buff_nova": "buff_nova.png",
    "buff_pax": "buff_pax.png",
    "stapler": "stapler.png",
    "grey_brick": "grey_brick.png",
}

ANIMATIONS = {
    "projectile_explode": ["projectile_{:003}".format(frame) for frame in range(1, 3 + 1)],
    "money_stopped": ["Money_{:003}".format(frame) for frame in range(1, 4 + 1)],
    "skeleton_walk": ["Skeleton_Walk_{:003}".format(frame) for frame in range(1, 3 + 1)],
    "skeleton_death": ["Skeleton_Death_{:003}".format(frame) for frame in range(1, 3 + 1)],
    "skeleton_stopped": ["Skeleton_Stopped_{:003}".format(frame) for frame in range(1, 3 + 1)],
}

for animation in chain.from_iterable(ANIMATIONS.values()):
    SPRITES[animation] = f"{animation}.png"

# Holds the converted and imported sprite images. The key is a tuple
# of (flipped_x, flipped_y, sprite_name)
IMAGE_SPRITES: Dict[Tuple[bool, bool, str], pg.Surface] = {}


ALLOWED_BG = [
    "bricks1",
    "bricks2",
    "bricks3",
    "bloody_floor",
    "blank",
    "black",
    "wood_door",
    "grey_brick",
]

ALLOWED_ENEMY = [
    "skeleton",
]

ALLOWED_BUFFS = [
    "buff_accumen",
    "buff_corpus",
    "buff_intuitus",
    "buff_nova",
    "buff_pax",
]

WALLS = [
    "bricks1",
    "bricks2",
    "bricks3",
    "black",
]

DOORS = [
    "wood_door",
]

"""
(top left, top right), (bottom left, bottom right)
"""
TILE_MAPS = {
    "bricks1": ((0, 0), (0, 0)),
    "bricks2": ((0, 0), (0, 0)),
    "bricks3": ((0, 0), (0, 0)),
    "grey_brick": ((1, 1), (1, 1)),
    "bloody_floor": ((1, 1), (1, 1)),
    "blank": ((1, 1), (1, 1)),
    "black": ((0, 0), (0, 0)),
    "wood_door": ((1, 1), (1, 1)),
}

SOUNDS = {}

KEY_ENEMY = 0
KEY_BACKGROUND = 1
KEY_SHRUB = 2

CACHE = {}

"""
( UP, RIGHT, DOWN, LEFT )
1 = door
0 = no door
"""
LEVEL_CONNECTIONS = {
    "4_way": (1, 1, 1, 1),
    "3_way_no_down": (1, 1, 0, 1),
    "3_way_no_up": (0, 1, 1, 1),
    "3_way_no_left": (1, 1, 1, 0),
    "3_way_no_right": (1, 0, 1, 1),
    "down_dead": (0, 0, 1, 0),
    "up_dead": (1, 0, 0, 0),
    "left_dead": (0, 0, 0, 1),
    "right_dead": (0, 1, 0, 0),
    "down_left": (0, 0, 1, 1),
    "down_right": (0, 1, 1, 0),
    "up_left": (1, 0, 0, 1),
    "up_right": (1, 1, 0, 0),
    "up_down": (1, 0, 1, 0),
    "left_right": (0, 1, 0, 1),
}

CONNECTION_MATCH = {}

MAP_GRID_UPPER_MAX = 40
STARTING_POSITION = (19, 19)

ENEMY_STATS = {
    "skeleton": {
        "value": 5,
        "health": 50,
        "aggro_distance": 500,
        "speed": 2,
        "collision_damage": 1,
        "anim_dying": ANIMATIONS["skeleton_death"],
        "anim_walk": ANIMATIONS["skeleton_walk"],
        "anim_stop": ANIMATIONS["skeleton_stopped"],
    }
}

ITEM_STATS = {
    "money": {
        "anim_stop": ANIMATIONS["money_stopped"],
    }
}
