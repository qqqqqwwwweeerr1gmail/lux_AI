
from lux.constants import Constants


class HarvestingOfficer:
    def __init__(self, harvesting_map, resource_clusters, lux_map):
        self.map = lux_map
        self.height = lux_map.height
        self.width = lux_map.width
        self.harvesting_map = harvesting_map
        self.resource_clusters = resource_clusters
        self.free_harvesting_positions = self.get_free_harvesting_positions()
        self.strategic_harvesting_positions = self.get_strategic_harvesting_positions()

    def get_free_harvesting_positions(self):
        """
        Get's all free harvesting locations as set.
        :return: set of position tuples.
        """
        free_harvesting_tiles = set()
        for x in range(self.width):
            for y in range(self.height):
                if self.harvesting_map[x][y].fuel_value_per_turn > 0:
                    free_harvesting_tiles.add((x, y))
        return free_harvesting_tiles

    def get_strategic_harvesting_positions(self):
        """
        Removing harvesting positions from the free_harvesting_positions if they would lead to unnecessary wood
        harvesting.
        :return: set of position tuples.
        """
        strategic_harvesting_positions = self.free_harvesting_positions.copy()
        for cluster in self.resource_clusters:
            if cluster.captured_by == "p":
                possible_farming_tiles = [rt.pos for rt in cluster.resource_tiles] + \
                                         [st for st in cluster.surrounding_tiles_pos
                                          if st not in cluster.attached_player_city_tiles_pos]

                for tile_pos in possible_farming_tiles:
                    harvesting_tile = self.harvesting_map[tile_pos[0]][tile_pos[1]]
                    if harvesting_tile.num_wood > 0:
                        directions = [[0, 1], [1, 0], [0, -1], [-1, 0], [0, 0]]
                        is_harvesting_spot = True
                        for d in directions:
                            new_x = tile_pos[0] + d[0]
                            new_y = tile_pos[1] + d[1]
                            if (0 <= new_x < self.width) and (0 <= new_y < self.height):
                                cell = self.map.get_cell(new_x, new_y)
                                if cell.has_resource():
                                    if cell.resource.type == Constants.RESOURCE_TYPES.WOOD:
                                        if cell.resource.amount < 200:
                                            is_harvesting_spot = False
                                            break
                        if (not is_harvesting_spot) and (tile_pos in strategic_harvesting_positions):
                            strategic_harvesting_positions.remove(tile_pos)

        return strategic_harvesting_positions
