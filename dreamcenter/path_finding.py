import operator
from pathfinding.core.grid import Grid
from pathfinding.core.diagonal_movement import DiagonalMovement
from pathfinding.finder.a_star import AStarFinder
from pygame import Vector2 as Vector
from itertools import accumulate, repeat
from dreamcenter.constants import (
    TILE_MAPS,
    TILE_WIDTH,
    TILE_HEIGHT,
)

finder = AStarFinder(diagonal_movement=DiagonalMovement.if_at_most_one_obstacle)


def define_grid(level) -> Grid:
    """
    Breaks apart the tiles into 4 quadrants
    Uses the information stored in TILE_MAPS to build a path grid
    """
    matrix = []
    _matrix_row = []
    _matrix_row2 = []

    for row in level:
        for tile in row:
            _matrix_row += TILE_MAPS[tile.index][0]
            _matrix_row2 += TILE_MAPS[tile.index][1]
        matrix.append(_matrix_row)
        matrix.append(_matrix_row2)
        _matrix_row, _matrix_row2 = [], []

    return Grid(matrix=matrix)


def find_path(start, end, grid) -> list[tuple]:
    """
    Uses the pathfinder library function to define the shortest path to a point using A* logic
    """
    _start = grid.node(int(start[0] // (TILE_HEIGHT / 2)), int(start[1] // (TILE_WIDTH / 2)))
    _end = grid.node(int(end[0] // (TILE_HEIGHT / 2)), int(end[1] // (TILE_WIDTH / 2)))

    path, runs = finder.find_path(_start, _end, grid)
    grid.cleanup()

    return path


def convert_path(path, speed) -> iter:
    """
    Converts the shortest path into a chain of iterators similar to other movement zips
    """
    vector_path = []
    grid_size = TILE_WIDTH / 2

    for cell in range(len(path)):
        _v1 = Vector(path[cell][0] * grid_size, path[cell][1] * grid_size)
        try:
            _v2 = Vector(path[cell + 1][0] * grid_size, path[cell + 1][1] * grid_size)
        except IndexError:
            return vector_path
        _vh = (_v2 - _v1).normalize() * speed

        vector_path += accumulate(repeat(_vh, int(grid_size/2)), func=operator.add, initial=_v1)

    return vector_path
