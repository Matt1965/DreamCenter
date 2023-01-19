import random
from dataclasses import dataclass, field
from dreamcenter.constants import LEVEL_CONNECTIONS, MAP_GRID_UPPER_MAX


@dataclass
class Map:
    seed_amt: int = field(default=15)
    map_grid: list[list[dict]] = field(default_factory=list)

    def __post_init__(self):
        self.create_blank_grid()
        self.map_grid[19][19]["level"] = "4_way"

    def set_starting_growth(self, growth):
        self.seed_amt = growth

    def create_blank_grid(self):
        """
        Creates a blank map of {"level": "blank", "growth": 0, "position": (row, column)} for size of grid
        """
        for row in range(MAP_GRID_UPPER_MAX):
            _temp_column = []
            for column in range(MAP_GRID_UPPER_MAX):
                _temp_column.append({"level": "blank", "growth": 0, "position": (row, column), "saved_state": {}})
            self.map_grid.append(_temp_column)
        self.map_grid[19][19]["growth"] = self.seed_amt

    def check_cardinals(self, grid_pos):
        """
        Returns true if more than 1 of the 4 positions around grid_pos have a growth greater than 0
        """
        counter = 0

        for x, y in [(1, 0), (0, 1), (-1, 0), (0, -1)]:
            try:
                if self.map_grid[grid_pos[0] + x][grid_pos[1] + y]["growth"] > 0 \
                        or self.map_grid[grid_pos[0] + x][grid_pos[1] + y]["level"] != "blank":
                    counter += 1
            except IndexError:
                pass

        return True if counter > 1 else False

    def distribute_growth(self, grid_pos):
        tiles = []
        growth_amt = self.map_grid[grid_pos[0]][grid_pos[1]]["growth"]

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
            tiles[0]["growth"] = growth_amt - 1
        elif len(tiles) == 0:
            self.redistribute_growth(growth_amt)
        else:
            growth_amt -= 1
            for i in range(growth_amt):
                bucket = random.randint(0, len(tiles)-1)
                tiles[bucket]["growth"] += 1

    def redistribute_growth(self, amount):
        pass

    def connection_finder(self, grid_pos):
        connections = [0, 0, 0, 0]
        counter = 0
        for y, x in [(-1, 0), (0, 1), (1, 0), (0, -1)]:
            try:
                if self.map_grid[grid_pos[0] + y][grid_pos[1] + x]["growth"] > 0 \
                        or self.map_grid[grid_pos[0] + y][grid_pos[1] + x]["level"] != "blank":
                    connections[counter] = 1
            except IndexError:
                pass
            counter += 1
        return tuple(connections)

    @staticmethod
    def level_matcher(connections):
        matched_levels = []
        for key, value in LEVEL_CONNECTIONS.items():
            if connections == value:
                matched_levels.append(key)
        return matched_levels

    def generate_map(self):
        growing = True
        while growing:
            growing = False
            for row in self.map_grid:
                for tile in row:
                    if tile["growth"] > 1:
                        self.distribute_growth(tile["position"])
                    if tile["growth"] > 0:
                        connections_found = self.connection_finder(tile["position"])
                        levels_matched = self.level_matcher(connections_found)
                        tile["level"] = random.choice(levels_matched)
                        tile["growth"] = 0
                        growing = True

    def visualize_map(self):
        visualized_map = []
        level_count = 0
        for row in self.map_grid:
            temp_row = []
            for tile in row:
                temp_row.append(tile["level"])
                if tile["level"] != "blank":
                    level_count += 1
            visualized_map.append(temp_row)
        return visualized_map
