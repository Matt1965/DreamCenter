import pygame as pg
from typing import Dict, Tuple
from itertools import chain
from dreamcenter.enumeration import MovementType

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

# identifiers for clarity in event handling
MOUSE_LEFT, MOUSE_MIDDLE, MOUSE_RIGHT = 1, 2, 3

# Dict of all game images
# Animation images added separately
SPRITES = {
    "edwardo": "edwardo.png",
    "background": "background.png",
    "logo": "logo.png",
    "edit_background": "edit_background.png",
    "play_background": "play_background.png",
    "blank": "blank.png",
    "bricks1": "bricks1.png",
    "bricks2": "bricks2.png",
    "bricks3": "bricks3.png",
    "bricks4": "bricks4.png",
    "wood_floor": "wood_floor.png",
    "bloody_floor": "bloody_floor.png",
    "projectile": "projectile.png",
    "skeleton": "Skeleton_Walk_000.png",
    "collision_mask": "collision_mask.png",
    "bg_mask": "bg_mask.png",
    "pause_menu": "pause_menu.png",
    "game_over_splash": "game_over_splash.png",
    "half_heart": "half_heart.png",
    "empty_heart": "empty_heart.png",
    "black": "black.png",
    "office_floor": "office_floor.png",
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
    "painting": "painting.png",
    "spider": "spider_stopped_000.png",
    "random": "random.png",
    "edward_arm": "edward_arm.png",
    "school_wall": "school_wall.png",
    "school_wall_back": "school_wall_back.png",
    "school_wall_back_corner": "school_wall_back_corner.png",
    "school_wall_incorner": "school_wall_incorner.png",
    "school_wall_outcorner": "school_wall_outcorner.png",
    "school_wall_back_incorner": "school_wall_back_incorner.png",
    "school_wall_blank": "school_wall_blank.png",
    "window": "window.png",
    "blackboard": "blackboard.png",
    "papers": "papers.png",
    "chair": "chair.png",
    "chair_remains": "chair_remains.png",
}

# Animation dicts
ANIMATIONS = {
    "projectile_explode": ["projectile_{:003}".format(frame) for frame in range(1, 3 + 1)],
    "money_stopped": ["Money_{:003}".format(frame) for frame in range(1, 4 + 1)],
    "skeleton_walk": ["Skeleton_Walk_{:003}".format(frame) for frame in range(1, 3 + 1)],
    "skeleton_death": ["Skeleton_Death_{:003}".format(frame) for frame in range(1, 3 + 1)],
    "skeleton_stopped": ["Skeleton_Stopped_{:003}".format(frame) for frame in range(1, 3 + 1)],
    "spider_walk": ["spider_walk_{:003}".format(frame) for frame in range(1, 2 + 1)],
    "spider_death": ["spider_death_{:003}".format(frame) for frame in range(1, 3 + 1)],
    "spider_stopped": ["spider_stopped_{:003}".format(frame) for frame in range(1, 3 + 1)],
    "chair_death": ["chair_{:003}".format(frame) for frame in range(1, 2 + 1)],
    "edward_idle": ["edward_idle_{:003}".format(frame) for frame in range(1, 3 + 1)],
    "edward_walk": ["edward_walk_{:003}".format(frame) for frame in range(1, 4 + 1)],
    "edward_arm_fire": ["edward_arm_{:003}".format(frame) for frame in range(1, 3 + 1)],
}

# Adding animation images to sprite dict
for animation in chain.from_iterable(ANIMATIONS.values()):
    SPRITES[animation] = f"{animation}.png"

# Holds the converted and imported sprite images. The key is a tuple
# of (flipped_x, flipped_y, sprite_name)
IMAGE_SPRITES: Dict[Tuple[bool, bool, str], pg.Surface] = {}

# Sprites which can be considered background for game_edit usage
ALLOWED_BG = [
    "bricks1",
    "bricks2",
    "bricks3",
    "bricks4",
    "bloody_floor",
    "blank",
    "black",
    "wood_door",
    "grey_brick",
    "office_floor",
    "wood_floor",
    "school_wall",
    "school_wall_back",
    "school_wall_back_corner",
    "school_wall_incorner",
    "school_wall_outcorner",
    "school_wall_back_incorner",
    "school_wall_blank",
]

# Sprites which can be considered enemy for game_edit usage
ALLOWED_ENEMY = [
    "skeleton",
    "spider",
]

# Sprites which can be considered shrub for game_edit usage
ALLOWED_SHRUB = [
    "painting",
    "window",
    "blackboard",
    "papers",
    "chair",
]

# Sprites which can be considered buff for game_play usage
ALLOWED_BUFFS = [
    "buff_accumen",
    "buff_corpus",
    "buff_intuitus",
    "buff_nova",
    "buff_pax",
]

# List of sprites considered walls
WALLS = [
    "bricks1",
    "bricks2",
    "bricks3",
    "bricks4",
    "black",
    "school_wall",
    "school_wall_incorner",
    "school_wall_outcorner",
    "school_wall_blank",
]

# List of sprites considered doors
DOORS = [
    "wood_door",
]

DEBRIS = {
    "chair": {"replacement": "chair_remains", "anim_dying": ANIMATIONS["chair_death"]},
}

"""
(top left, top right), (bottom left, bottom right)
"""
TILE_MAPS = {
    "bricks1": ((0, 0), (0, 0)),
    "bricks2": ((0, 0), (0, 0)),
    "bricks3": ((0, 0), (0, 0)),
    "bricks4": ((0, 0), (0, 0)),
    "grey_brick": ((1, 1), (1, 1)),
    "bloody_floor": ((1, 1), (1, 1)),
    "blank": ((1, 1), (1, 1)),
    "black": ((0, 0), (0, 0)),
    "wood_door": ((1, 1), (1, 1)),
    "office_floor": ((1, 1), (1, 1)),
    "wood_floor": ((1, 1), (1, 1)),
    "school_wall": ((0, 0), (0, 0)),
    "school_wall_incorner": ((0, 0), (0, 0)),
    "school_wall_outcorner": ((0, 0), (0, 0)),
    "school_wall_blank": ((0, 0), (0, 0)),
    "school_wall_back": ((0, 0), (0, 0)),
    "school_wall_back_corner": ((0, 0), (0, 0)),
    "school_wall_back_incorner": ((0, 0), (0, 0)),
}

SOUNDS = {}

# Key assignment for game_edit sprite type switching
KEY_ENEMY = 0
KEY_BACKGROUND = 1
KEY_SHRUB = 2
KEY_BUFF = 3

CACHE = {}

"""
( UP, RIGHT, DOWN, LEFT )
1 = door
0 = no door
"""
LEVEL_CONNECTIONS = {
    "4_way": {"connection": (1, 1, 1, 1), "type": "basic"},
    "3_way_no_down": {"connection": (1, 1, 0, 1), "type": "basic"},
    "3_way_no_up": {"connection": (0, 1, 1, 1), "type": "basic"},
    "3_way_no_left": {"connection": (1, 1, 1, 0), "type": "basic"},
    "3_way_no_right": {"connection": (1, 0, 1, 1), "type": "basic"},
    "down_dead": {"connection": (0, 0, 1, 0), "type": "basic"},
    "up_dead": {"connection": (1, 0, 0, 0), "type": "basic"},
    "left_dead": {"connection": (0, 0, 0, 1), "type": "basic"},
    "right_dead": {"connection": (0, 1, 0, 0), "type": "basic"},
    "down_left": {"connection": (0, 0, 1, 1), "type": "basic"},
    "down_right": {"connection": (0, 1, 1, 0), "type": "basic"},
    "up_left": {"connection": (1, 0, 0, 1), "type": "basic"},
    "up_right": {"connection": (1, 1, 0, 0), "type": "basic"},
    "up_down": {"connection": (1, 0, 1, 0), "type": "basic"},
    "left_right": {"connection": (0, 1, 0, 1), "type": "basic"},
    "up_shop": {"connection": (1, 0, 0, 0), "type": "shop"},
    "down_shop": {"connection": (0, 0, 1, 0), "type": "shop"},
    "left_shop": {"connection": (0, 0, 0, 1), "type": "shop"},
    "right_shop": {"connection": (0, 1, 0, 0), "type": "shop"},
}

CONNECTION_MATCH = {}

# Values used in map_logic assigning the upper maximum and middle starting position
MAP_GRID_UPPER_MAX = 40
STARTING_POSITION = (19, 19)

# dict{dict} used to determine enemy stats on creation
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
        "movement": MovementType.chase,
        "movement_cooldown": 0,
    },
    "spider": {
        "value": 2,
        "health": 10,
        "aggro_distance": 300,
        "speed": 3.5,
        "collision_damage": 1,
        "anim_dying": ANIMATIONS["spider_death"],
        "anim_walk": ANIMATIONS["spider_walk"],
        "anim_stop": ANIMATIONS["spider_stopped"],
        "movement": MovementType.wander_chase,
        "movement_cooldown": 70,
    },
}

# dict{dict} used to determine item stats on creation
ITEM_STATS = {
    "money": {
        "anim_stop": ANIMATIONS["money_stopped"],
    }
}
