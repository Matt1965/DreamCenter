import pygame as pg
from dreamcenter.constants import (
    SCREENRECT,
    TILE_WIDTH,
    TILE_HEIGHT,
    TILES_X,
    TILES_Y,
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


