import random
from dataclasses import dataclass, field
from dreamcenter.constants import LEVEL_CONNECTIONS, MAP_GRID_UPPER_MAX

@dataclass
class Map:
    end_points: list = field(default_factory=list)
    seed_amt: int = field(default=15)
    map_grid: list[list[dict]] = field(default_factory=list)

    def __post_init__(self):
        self.create_blank_grid()
        self.map_grid[19][19]["level"] = "4_way"

    def set_starting_growth(self, growth) -> None:
        """
        Function to set the amount of rooms 'grown' from the center
        """
        self.seed_amt = growth

    def create_blank_grid(self) -> None:
        """
        Creates a blank map of {"level": "blank", "growth": 0, "position": (row, column)} for size of grid
        """
        for row in range(MAP_GRID_UPPER_MAX):
            _temp_column = []
            for column in range(MAP_GRID_UPPER_MAX):
                _temp_column.append({"level": "blank", "growth": 0, "position": (row, column), "saved_state": {}})
            self.map_grid.append(_temp_column)
        self.map_grid[19][19]["growth"] = self.seed_amt

    def check_cardinals(self, grid_pos) -> bool:
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

    def distribute_growth(self, grid_pos) -> None:
        """
        Function handles giving the growth value it holds to the surrounding cells.
        A growth value of 1 is considered a dead end
        Growth value becomes 0 after tile index assignment
        """
        tiles = []
        growth_amt = self.map_grid[grid_pos[0]][grid_pos[1]]["growth"]

        # Collects all of the surrounding tiles and saves them into 'tiles'
        for x, y in [(1, 0), (0, 1), (-1, 0), (0, -1)]:
            try:
                tiles.append(self.map_grid[grid_pos[0] + x][grid_pos[1] + y])
            except IndexError:
                pass
        """
        Removes tiles from 'tiles' based on the criteria:
        Having growth, which indicates running into another branch's growth space
        Not being blank, which indicates running into another branch
        Check cardinals function, see function for details
        """
        for tile in tiles.copy():
            if tile["growth"] != 0 or \
                    tile["level"] != "blank" or \
                    self.check_cardinals((tile["position"][0], tile["position"][1])):
                tiles.remove(tile)

        #
        if len(tiles) == 0:
            self.redistribute_growth(growth_amt)
        elif len(tiles) == 1:
            tiles[0]["growth"] = growth_amt - 1
        else:
            growth_amt -= 1
            for i in range(growth_amt):
                bucket = random.randint(0, len(tiles)-1)
                tiles[bucket]["growth"] += 1

    def redistribute_growth(self, amount) -> None:
        """
        Distributes left over growth to valid tiles.
        Is triggered when function distribute_growth has nowhere to place its values
        """
        pass

    def connection_finder(self, grid_pos) -> tuple:
        """
        Handles finding the connection schema in order to query LEVEL_CONNECTIONS
        connection schema : (up, right, down, left)
        :param grid_pos: Tile position needing a connection match for
        :return: The connection schema needed
        """
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
    def level_matcher(connections) -> tuple:
        """
        Matches connection tuple with levels from LEVEL_CONNECTIONS and returns a list
        """
        matched_levels = []
        for key, value in LEVEL_CONNECTIONS.items():
            if connections == value["connection"]:
                matched_levels.append(key)
        return matched_levels

    def generate_map(self) -> None:
        """
        Handles the full building of a map
        Continues to loop until no tile has assigned a level in the last cycle
        """
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

        # Special room assignments
        self.identify_end_points()
        self.assign_special("shop")


    def visualize_map(self) -> list:
        """
        Dev tool for generating a text map used for debugging
        """
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

    def identify_end_points(self) -> None:
        """
        Assigns all tiles in grid with only 1 connection to the end_points list
        """
        for row in self.map_grid:
            for tile in row:
                try:
                    if sum(LEVEL_CONNECTIONS[tile["level"]]["connection"]) == 1:
                        self.end_points.append(tile["position"])
                except KeyError:
                    pass

    def assign_special(self, type) -> None:
        """
        Chooses a random end point tile, removes it from the end point list,
        and assigns a random level of type shop to that position
        """
        special_pool = []

        grid_pos = random.choice(self.end_points)
        self.end_points.remove(grid_pos)

        for level in LEVEL_CONNECTIONS:
            # Exclude any levels not of type shop
            if LEVEL_CONNECTIONS[level]["type"] != type:
                continue

            if LEVEL_CONNECTIONS[level]["connection"] == \
                    LEVEL_CONNECTIONS[self.map_grid[grid_pos[0]][grid_pos[1]]["level"]]["connection"]:
                special_pool.append(level)

        self.map_grid[grid_pos[0]][grid_pos[1]]["level"] = random.choice(special_pool)
