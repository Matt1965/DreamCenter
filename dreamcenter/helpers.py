import pygame as pg
from pygame import Vector2 as Vector
import tkinter
import random
import math
from tkinter import filedialog
from contextlib import contextmanager
from math import atan2, degrees, pi
from dreamcenter.constants import (
    SCREENRECT,
    TILE_WIDTH,
    TILE_HEIGHT,
    TILES_X,
    TILES_Y,
    CONNECTION_MATCH,
    IMAGE_SPRITES,
)


def create_surface(size=SCREENRECT.size, flags=pg.SRCALPHA):
    return pg.Surface(size, flags=flags)


def get_grid_rect(gx, gy):
    return pg.Rect(gx * TILE_WIDTH, gy * TILE_HEIGHT, TILE_WIDTH, TILE_HEIGHT)


def tile_positions():
    """
    Given a range of TILES_Y and TILES_X, generate
    all grid positions along with their top-left position.
    """
    for y in range(TILES_Y):
        for x in range(TILES_X):
            yield y, x, x * TILE_WIDTH, y * TILE_HEIGHT


def tile_position(position):
    """
    Given a position, calculate the grid tile position
    """
    x, y = position
    return x // TILE_WIDTH, y // TILE_HEIGHT


def extend(iterable, repeat):
    """
    Given an iterable, repeat each element `repeat` times before
    continuing to the next.
    """
    return (elem for elem in iterable for _ in range(repeat))


def get_line(start, end):
    """
    Bresenham's Line Algorithm
    Produces a list of tuples from start and end
    """
    # Setup initial conditions
    x1, y1 = start
    x2, y2 = end
    dx = x2 - x1
    dy = y2 - y1

    # Determine how steep the line is
    is_steep = abs(dy) > abs(dx)

    # Rotate line
    if is_steep:
        x1, y1 = y1, x1
        x2, y2 = y2, x2

    # Swap start and end points if necessary and store swap state
    swapped = False
    if x1 > x2:
        x1, x2 = x2, x1
        y1, y2 = y2, y1
        swapped = True

    # Recalculate differentials
    dx = x2 - x1
    dy = y2 - y1

    # Calculate error
    error = int(dx / 2.0)
    ystep = 1 if y1 < y2 else -1

    # Iterate over bounding box generating points between start and end
    y = y1
    points = []
    for x in range(x1, x2 + 1):
        coord = (y, x) if is_steep else (x, y)
        points.append(coord)
        error -= abs(dy)
        if error < 0:
            y += ystep
            error += dx

    # Reverse the list if the coordinates were swapped
    if swapped:
        points.reverse()
    return points


def angle_to(v1, v2):
    """
    Finds the angle between two vectors, `v1` and `v2`.

    This function is clever enough to convert between cartesian and
    screen coordinate systems and, thanks to `atan2`, all the gnarly
    computational stuff you'd otherwise have to do with normal `atan`
    is done for us.
    """
    dx, dy = v1 - v2
    rads = atan2(-dy, dx)
    rads %= 2 * pi
    degs = degrees(rads)
    return degs


def collide_mask(group_a, group_b, collide_type=pg.sprite.collide_mask):
    """
    Uses the sprite mask attribute to check if two groups of sprites are colliding.
    """
    for sprite_a, sprite_b in pg.sprite.groupcollide(
            group_a,
            group_b,
            False,
            False,
            collided=collide_type,
    ).items():
        yield sprite_a, sprite_b


def create_tile_map(default_value=None) -> list:
    """
    Creates a grid tile map with default value of None
    """
    return [[default_value for _ in range(TILES_X)] for _ in range(TILES_Y)]


def connection_match_builder():
    CONNECTION_MATCH.update({(1, 1, 1, 1): IMAGE_SPRITES[(False, False, "map_4_way")]})
    CONNECTION_MATCH.update({(1, 1, 0, 1): pg.transform.rotate(IMAGE_SPRITES[(False, False, "map_3_way")], 90)})
    CONNECTION_MATCH.update({(0, 1, 1, 1): pg.transform.rotate(IMAGE_SPRITES[(False, False, "map_3_way")], 270)})
    CONNECTION_MATCH.update({(1, 1, 1, 0): IMAGE_SPRITES[(False, False, "map_3_way")]})
    CONNECTION_MATCH.update({(1, 0, 1, 1): IMAGE_SPRITES[(True, False, "map_3_way")]})
    CONNECTION_MATCH.update({(0, 0, 1, 0): IMAGE_SPRITES[(False, True, "map_1_way")]})
    CONNECTION_MATCH.update({(1, 0, 0, 0): IMAGE_SPRITES[(False, False, "map_1_way")]})
    CONNECTION_MATCH.update({(0, 0, 0, 1): pg.transform.rotate(IMAGE_SPRITES[(False, False, "map_1_way")], 90)})
    CONNECTION_MATCH.update({(0, 1, 0, 0): pg.transform.rotate(IMAGE_SPRITES[(False, False, "map_1_way")], 270)})
    CONNECTION_MATCH.update({(0, 0, 1, 1): IMAGE_SPRITES[(True, True, "map_2_way")]})
    CONNECTION_MATCH.update({(0, 1, 1, 0): IMAGE_SPRITES[(False, True, "map_2_way")]})
    CONNECTION_MATCH.update({(1, 0, 0, 1): IMAGE_SPRITES[(True, False, "map_2_way")]})
    CONNECTION_MATCH.update({(1, 1, 0, 0): IMAGE_SPRITES[(False, False, "map_2_way")]})
    CONNECTION_MATCH.update({(1, 0, 1, 0): IMAGE_SPRITES[(False, False, "map_2_way_straight")]})
    CONNECTION_MATCH.update({(0, 1, 0, 1): pg.transform.rotate(IMAGE_SPRITES[(False, False, "map_2_way_straight")], 90)})


@contextmanager
def open_dialog(title="Open file...", filetypes=(("Tower Defense Levels", "*json"),)):
    """
    Context manager that yields the opened file, which could be
    None if the user exits it without selecting. If there is a file it
    is closed when the context manager exits.
    """
    f = None
    try:
        f = tkinter.filedialog.askopenfile(title=title, filetypes=filetypes)
        yield f
    finally:
        if f is not None:
            f.close()


@contextmanager
def save_dialog(title="Save file...", filetypes=(("Tower Defense Levels", "*.json"),)):
    f = tkinter.filedialog.asksaveasfile(title=title, filetypes=filetypes)
    try:
        yield f
    finally:
        if f is not None:
            f.close()


def random_normalized_vector() -> Vector:
    angle = math.radians(random.randint(0, 360))
    return Vector(math.cos(angle), math.sin(angle))


def range_check(origin, target, distance):
    """
    Checks the range between 2 points
    Does not consider obstacles
    """
    line_of_sight = get_line(origin, target)

    if Vector(line_of_sight[0]).distance_to(line_of_sight[-1]) > distance:
        return False

    return True