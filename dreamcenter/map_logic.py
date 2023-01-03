import random
from dataclasses import dataclass, field
from dreamcenter.constants import LEVEL_CONNECTIONS, MAP_GRID_UPPER_MAX
import time


@dataclass
class Map:
    seed_amt: int
    map_grid: list[list[dict]] = field(default_factory=list)

    def __post_init__(self):
        self.create_blank_grid()
        self.map_grid[24][24]["growth"] = self.seed_amt

    def create_blank_grid(self):
        for row in range(MAP_GRID_UPPER_MAX):
            _temp_column = []
            for column in range(MAP_GRID_UPPER_MAX):
                _temp_column.append({"level": "blank", "growth": 0, "position": (row, column)})
            self.map_grid.append(_temp_column)

    def check_cardinals(self, grid_pos):
        """
        Returns true if more than 1 of the 4 positions around grid_pos have a growth greater than 0
        """
        _growth_counter = 0

        for x, y in [(1, 0), (0, 1), (-1, 0), (0, -1)]:
            try:
                if self.map_grid[grid_pos[0] + x][grid_pos[1] + y]["growth"] > 0:
                    _growth_counter += 1
            except IndexError:
                pass

        return True if _growth_counter > 1 else False

    def distribute_growth(self, grid_pos):
        tiles = []
        growth_amt = self.map_grid[grid_pos[0]][grid_pos[1]]["growth"]

        if growth_amt == 1:
            return

        for x, y in [(1, 0), (0, 1), (-1, 0), (0, -1)]:
            try:
                tiles.append(self.map_grid[grid_pos[0] + x][grid_pos[1] + y])
            except IndexError:
                pass

        for tile in tiles.copy():
            if tile["growth"] != 0 or \
                    tile["level"] != "blank" or \
                    self.check_cardinals((tile["position"][0], tile["position"][1])):
                tiles.remove(tile)

        if len(tiles) == 1:
            tiles[0]["growth"] = growth_amt
        elif len(tiles) == growth_amt:
            for tile in tiles:
                tile["growth"] = 1
        elif len(tiles) == 0:
            self.redistribute_growth(growth_amt)
            return
        else:
            for i in range(growth_amt):
                bucket = random.randint(0, len(tiles)-1)
                tiles[bucket]["growth"] += 1

    def redistribute_growth(self, amount):
        pass

    def connection_finder(self, grid_pos):
        connections = [0, 0, 0, 0]
        counter = 0
        print("------------connection info-----------")
        for y, x in [(1, 0), (0, -1), (-1, 0), (0, 1)]:
            try:
                print(self.map_grid[grid_pos[0] + y][grid_pos[1] + x]["growth"])
                if self.map_grid[grid_pos[0] + y][grid_pos[1] + x]["growth"] > 0 \
                        or self.map_grid[grid_pos[0] + y][grid_pos[1] + x]["level"] != "blank":
                    connections[counter] = 1
            except IndexError:
                pass
            counter += 1
        print("--------------------------------------")
        return tuple(connections)

    @staticmethod
    def level_matcher(connections):
        matched_levels = []
        for key, value in LEVEL_CONNECTIONS.items():
            if connections == value:
                matched_levels.append(key)
        return matched_levels

    def define_seed(self, value):
        self.map_grid[24][24]["growth"] = value

    def generate_map(self):
        growing = True
        while growing:
            print('growing...')
            growing = False
            for row in self.map_grid:
                for tile in row:
                    if tile["growth"] > 0:
                        print(tile)
                        self.distribute_growth(tile["position"])
                        connections_found = self.connection_finder(tile["position"])
                        print(connections_found)
                        levels_matched = self.level_matcher(connections_found)
                        print(levels_matched)
                        tile["level"] = random.choice(levels_matched)
                        tile["growth"] = 0
                        growing = True
                        time.sleep(.5)

    def visualize_map(self):
        visualized_map = []
        for row in self.map_grid:
            temp_row = []
            for tile in row:
                temp_row.append(tile["level"])
            visualized_map.append(temp_row)
        return visualized_map
