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



