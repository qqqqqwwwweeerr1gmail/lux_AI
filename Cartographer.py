import numpy as np
from lux.constants import Constants
from lux.game_constants import GAME_CONSTANTS
from collections import deque
# from IPython.core.display import display, HTML
# display(HTML("<style>.container { width:100% !important; }</style>"))

class Cartographer:
    def __init__(self, lux_map, player, opponent, observation):
        self.observation = observation
        self.height = lux_map.height
        self.width = lux_map.width
        self.map = lux_map
        self.player = player
        self.opponent = opponent
        self.city_map = np.zeros([self.width, self.height], np.int16)
        self.unit_map = np.zeros([self.width, self.height], np.int16)
        self.fuel_map = np.zeros([self.width, self.height], np.int16)
        self.resource_map = np.zeros([self.width, self.height], str)
        self.harvesting_map = np.zeros([self.width, self.height], HarvestingTile)
        self.resource_clusters = []
        map_size_dict = {12: "S", 16: "M", 24: "L", 32: "XL"}
        self.map_size = map_size_dict[self.width]
        self.territory_map = None

    def map_battlefield(self):
        self.build_city_map()
        self.build_unit_map()
        self.build_fuel_map()
        self.build_resource_map()
        self.build_harvesting_map()

    """
    ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    Some methods to map the battlefield.
    ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    """

    def build_city_map(self):
        """
        Returns a grid with values 0, 1 or 2
        0: No-city on postion
        1: Player-city on postion
        2. Opponent-city on postion
        """
        player_city_tiles = {(tile.pos.x, tile.pos.y) for city in self.player.cities.values()
                             for tile in city.citytiles}
        opponent_city_tiles = {(tile.pos.x, tile.pos.y) for city in self.opponent.cities.values()
                               for tile in city.citytiles}

        for x in range(self.width):
            for y in range(self.height):
                if (x, y) in player_city_tiles:
                    self.city_map[x][y] = 1
                elif (x, y) in opponent_city_tiles:
                    self.city_map[x][y] = 2

    def build_unit_map(self):
        """
        Returns a grid with values 0, 1 or 2.
        0: No-unit on postion
        1: Player-unit on postion
        2: Opponent-unit on postion
        """
        player_unit_tiles = {(unit.pos.x, unit.pos.y) for unit in self.player.units}
        opponent_unit_tiles = {(unit.pos.x, unit.pos.y) for unit in self.opponent.units}

        for x in range(self.width):
            for y in range(self.height):
                if (x, y) in player_unit_tiles:
                    self.unit_map[x][y] = 1
                elif (x, y) in opponent_unit_tiles:
                    self.unit_map[x][y] = 2

    def build_fuel_map(self):
        """
        Returns a grid with the amount of fuel left on each cell from a players perspective. This included the players
        research level.
        Can be used for resource cluster evaluation.
        """
        for x in range(self.width):
            for y in range(self.height):
                cell = self.map.get_cell(x, y)
                if cell.has_resource():
                    if cell.resource.type == Constants.RESOURCE_TYPES.WOOD:
                        self.fuel_map[x][y] = 1 * cell.resource.amount
                    elif cell.resource.type == Constants.RESOURCE_TYPES.COAL and self.player.researched_coal():
                        self.fuel_map[x][y] = 10 * cell.resource.amount
                    elif cell.resource.type == Constants.RESOURCE_TYPES.URANIUM and self.player.researched_uranium():
                        self.fuel_map[x][y] = 40 * cell.resource.amount

    def build_resource_map(self):
        """
        Returns a grid with values w, c or u.
        Just for debugging and some simple map visualisations.
        w: Wood
        c: Coal
        u: Uranium
        """
        for x in range(self.width):
            for y in range(self.height):
                cell = self.map.get_cell(x, y)
                if cell.has_resource():
                    if cell.resource.type == Constants.RESOURCE_TYPES.WOOD:
                        self.resource_map[x][y] = "w"
                    elif cell.resource.type == Constants.RESOURCE_TYPES.COAL:
                        self.resource_map[x][y] = "c"
                    elif cell.resource.type == Constants.RESOURCE_TYPES.URANIUM:
                        self.resource_map[x][y] = "u"

    def build_harvesting_map(self):
        """
        Builds a grid of HarvestingTiles. The research status of the player is taken into account.
        """
        for x in range(self.width):
            for y in range(self.height):
                cell = self.map.get_cell(x, y)
                fuel_value_per_turn = 0
                collection_amount_per_turn = 0
                num_wood = 0
                num_coal = 0
                num_uranium = 0
                for k, direction in GAME_CONSTANTS["DIRECTIONS"].items():
                    adjacent_pos = cell.pos.translate(direction, 1)
                    if (0 <= adjacent_pos.x < self.width) and (0 <= adjacent_pos.y < self.height):
                        # adjacent_pos is still on map
                        adjacent_cell = self.map.get_cell(adjacent_pos.x, adjacent_pos.y)
                        if adjacent_cell.has_resource():
                            if adjacent_cell.resource.type == Constants.RESOURCE_TYPES.WOOD:
                                fuel_value_per_turn += 20
                                collection_amount_per_turn += 20
                                num_wood += 1
                            elif adjacent_cell.resource.type == Constants.RESOURCE_TYPES.COAL and \
                                    self.player.researched_coal():
                                fuel_value_per_turn += 50
                                collection_amount_per_turn += 5
                                num_coal += 1
                            elif adjacent_cell.resource.type == Constants.RESOURCE_TYPES.URANIUM and \
                                    self.player.researched_uranium():
                                fuel_value_per_turn += 80
                                collection_amount_per_turn += 2
                                num_uranium += 1

                self.harvesting_map[x][y] = HarvestingTile(fuel_value_per_turn, collection_amount_per_turn, num_wood,
                                                           num_coal, num_uranium)

    def build_territory_map(self):
        """
        With this map we can decide whether a resource tile is on the player's side rather than on the opponent's side.
        Note: Only works if both starting cities are alive. Use this in turn one and save the output globally.
        """
        territory_map = np.zeros([self.width, self.height], np.int16)
        player_city = None
        opponent_city = None

        if len(self.player.cities.keys()) > 0:
            player_city = self.player.cities[list(self.player.cities.keys())[0]]
        if len(self.opponent.cities.keys()) > 0:
            opponent_city = self.opponent.cities[list(self.opponent.cities.keys())[0]]

        if (player_city is not None) and (opponent_city is not None):
            # get mirror axis:
            if player_city.citytiles[0].pos.x == opponent_city.citytiles[0].pos.x:
                # mirror_axis --> x
                for x in range(self.width):
                    for y in range(self.height):
                        if y < self.height / 2:
                            if player_city.cityid == "c_1":
                                territory_map[x][y] = 1
                            else:
                                territory_map[x][y] = 2
                        else:
                            if player_city.cityid == "c_1":
                                territory_map[x][y] = 2
                            else:
                                territory_map[x][y] = 1
            else:
                # mirror_axis --> y
                for x in range(self.width):
                    for y in range(self.height):
                        if x < self.width / 2:
                            if player_city.cityid == "c_1":
                                territory_map[x][y] = 1
                            else:
                                territory_map[x][y] = 2
                        else:
                            if player_city.cityid == "c_1":
                                territory_map[x][y] = 2
                            else:
                                territory_map[x][y] = 1
        else:
            print("can't build territory_map")
        return territory_map

    def build_resource_cluster(self):
        """
        Builds list of ResourceClusters.
        Note: clusters that connect diagonal are not counting as one cluster. (They are added together later)
        """
        directions = [[0, 1], [1, 0], [0, -1], [-1, 0]]
        mapped_tiles = set()
        for x in range(self.width):
            for y in range(self.height):
                if (x, y) not in mapped_tiles:
                    cell = self.map.get_cell(x, y)
                    if cell.has_resource():
                        # build cluster:
                        resource_cluster = ResourceCluster(map_size=self.map_size)
                        resource_tile = ResourceTile(pos_tuple=(x, y), resource_type=self.resource_map[x][y],
                                                     fuel_amount=self.fuel_map[x][y])
                        resource_cluster.add_resource_tile(resource_tile=resource_tile)
                        mapped_tiles.add((x, y))
                        cluster_discovered = False
                        tiles_to_visit = set()
                        while not cluster_discovered:
                            for d in directions:
                                new_x = x + d[0]
                                new_y = y + d[1]
                                if (new_x, new_y) not in mapped_tiles:
                                    # check if tile is on map.
                                    if (0 <= new_x < self.width) and (0 <= new_y < self.height):
                                        cell = self.map.get_cell(new_x, new_y)
                                        if cell.has_resource():
                                            resource_tile = ResourceTile(pos_tuple=(new_x, new_y),
                                                                         resource_type=self.resource_map[new_x][new_y],
                                                                         fuel_amount=self.fuel_map[new_x][new_y])
                                            resource_cluster.add_resource_tile(resource_tile=resource_tile)
                                            mapped_tiles.add((new_x, new_y))
                                            tiles_to_visit.add((new_x, new_y))
                            if len(tiles_to_visit) == 0:
                                cluster_discovered = True
                            else:
                                x, y = tiles_to_visit.pop()
                        resource_cluster.check_surrounding(map_width=self.width, map_height=self.height,
                                                           city_map=self.city_map, player=self.player,
                                                           opponent=self.opponent, unit_map=self.unit_map,
                                                           territory_map=self.territory_map)
                        self.resource_clusters.append(resource_cluster)
        # add clusters that are diagonally connected together.
        all_connected = False
        combined_clusters = []
        clusters = set(self.resource_clusters.copy())
        joint_clusters = set()
        if len(clusters) > 0:
            while not all_connected:
                cluster = clusters.pop()
                combined = False
                if cluster not in joint_clusters:
                    other_clusters = [c for c in clusters if c not in joint_clusters]
                    for other_cluster in other_clusters:
                        for r1_tile in cluster.resource_tiles:
                            for r2_tile in other_cluster.resource_tiles:
                                dist = self.distance(origin=r1_tile.pos, destination=r2_tile.pos)
                                if dist == 2:
                                    # check for diagonal connection.
                                    if (r1_tile.pos[0] != r2_tile.pos[0]) and (r1_tile.pos[1] != r2_tile.pos[1]):
                                        # --> diagonal connection:
                                        joint_clusters.add(other_cluster)
                                        joint_clusters.add(cluster)
                                        cluster += other_cluster
                                        combined = True
                                        break

                if combined:
                    clusters.add(cluster)
                else:
                    if cluster not in joint_clusters:
                        combined_clusters.append(cluster)
                if len(clusters) == 0:
                    all_connected = True
        self.resource_clusters = combined_clusters

    """
    ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    Some basic distance methods.
    ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    """

    @staticmethod
    def distance(origin, destination):
        """
        Return Manhatten distance between two points.
        :param origin: list [x, y]
        :param destination: list [x, y]
        :return: int
        """
        return np.abs(origin[0] - destination[0]) + np.abs(origin[1] - destination[1])

    @staticmethod
    def distance_with_obstacles(obstacles_map, origin, destination):
        """
        Return the shortest distance between two point without moving over obstacles given a grid of obstacles. An
        obstacles is identified by any value greater then 0 in the given grid.
        If no way is found we return 1000.
        """
        obstacles_map[origin[0]][origin[1]] = 0  # the starting position cant be an obstacle
        directions = [[0, 1], [1, 0], [0, -1], [-1, 0]]
        q = deque()
        origin.append(0)
        q.append(origin)  # [row, col, distance]

        visited = set()
        while len(q) > 0:
            cr, cc, c_dist = q.popleft()
            if cr == destination[0] and cc == destination[1]:
                return c_dist
            if obstacles_map[cr][cc] >= 1:  #
                # obstacle
                continue
            for direction in directions:
                nr, nc = cr + direction[0], cc + direction[1]
                if 0 <= nr < len(obstacles_map) and 0 <= nc < len(obstacles_map[0]) and (nr, nc) not in visited:
                    q.append([nr, nc, c_dist + 1])
                    visited.add((nr, nc))
        return 1000

    @staticmethod
    def distance_to_district(pos, district_mayor):
        """
        Return the distance and the closes tile from a position to a district.
        :param pos: pos tuple
        :param district_mayor: DistrictMayor
        :return: distance, pos
        """
        min_tile_dist = np.inf
        closest_tile_pos = None
        for city_tile in district_mayor.city.citytiles:
            dist = Cartographer.distance(origin=[pos[0], pos[1]], destination=[city_tile.pos.x, city_tile.pos.y])
            if dist < min_tile_dist:
                min_tile_dist = dist
                closest_tile_pos = (city_tile.pos.x, city_tile.pos.y)
        if min_tile_dist < 100:
            return min_tile_dist, closest_tile_pos
        else:
            return 1000, None

    @staticmethod
    def distance_cluster_to_district(cluster, district_mayor):
        """
        Calculate the min distance between a ResourceCluster and a DistrictMajor
        :param cluster: ResourceCluster
        :param district_mayor: DistrictMajor
        :return: Min distance between both clusters as distance.
        """
        min_dist = np.inf
        dist = 1000
        for resource_tile in cluster.resource_tiles:
            dist, _ = Cartographer.distance_to_district(pos=resource_tile.pos, district_mayor=district_mayor)
            if dist < min_dist:
                min_dist = dist
        return dist

    @staticmethod
    def distance_to_cluster(pos, cluster):
        """
        Distance between a position and a resource cluster.
        :param pos: position tuple.
        :param cluster: ResourceCluster
        :return: distance , closest tile pos
        """
        min_tile_dist = np.inf
        closest_tile_pos = None
        resource_positions = set([rt.pos for rt in cluster.resource_tiles])
        for tile_pos in cluster.surrounding_tiles_pos.union(resource_positions):
            dist = Cartographer.distance(origin=pos, destination=tile_pos)
            if dist < min_tile_dist:
                min_tile_dist = dist
                closest_tile_pos = tile_pos
        if closest_tile_pos is not None:
            return min_tile_dist, closest_tile_pos
        else:
            return 1000, None

    @staticmethod
    def distance_cluster_to_cluster(cluster1, cluster2):
        """
        Calculates the distance between two resource clusters.
        :param cluster1: ResourceCluster
        :param cluster2: ResourceCluster
        :return: distance , closest tile pos 1, closest tile pos 2
        """
        connection_tile_pos_1 = None
        connection_tile_pos_2 = None
        min_dist = np.inf
        for tile_pos in cluster1.surrounding_tiles_pos:
            dist, tile_2_pos = Cartographer.distance_to_cluster(pos=tile_pos, cluster=cluster2)
            if dist < min_dist:
                min_dist = dist
                connection_tile_pos_1 = tile_pos
                connection_tile_pos_2 = tile_2_pos
        if connection_tile_pos_1 is not None:
            return min_dist, connection_tile_pos_1, connection_tile_pos_2
        else:
            return 1000, None, None

    @staticmethod
    def distance_district_to_district(district1, district2):
        """
        Calculates the distance between two resource clusters.
        :param district1: DistrictMayor
        :param district2: DistrictMayor
        :return: distance , closest tile pos 1, closest tile pos 2
        """
        connection_tile_pos_1 = None
        connection_tile_pos_2 = None
        min_dist = np.inf
        for tile_pos in district1.city_tiles_positions:
            dist, tile_2_pos = Cartographer.distance_to_district(pos=tile_pos, district_mayor=district2)
            if dist < min_dist:
                min_dist = dist
                connection_tile_pos_1 = tile_pos
                connection_tile_pos_2 = tile_2_pos
        if connection_tile_pos_1 is not None:
            return min_dist, connection_tile_pos_1, connection_tile_pos_2
        else:
            return 1000, None, None


class HarvestingTile:
    """
    Stores harvesting information per tile.
    fuel_value_per_turn: The maximal amount of collected fuel per turn.
    collection_amount_per_turn: the amount of collectible resources per turn.
    num_wood: num reachable wood tiles
    num_coal: num reachable coal tiles
    num_uranium: num reachable uranium tiles
    """
    def __init__(self, fuel_value_per_turn, collection_amount_per_turn, num_wood, num_coal, num_uranium):
        self.fuel_value_per_turn = fuel_value_per_turn
        self.collection_amount_per_turn = collection_amount_per_turn
        self.num_wood = num_wood
        self.num_coal = num_coal
        self.num_uranium = num_uranium


class ResourceTile:
    def __init__(self, pos_tuple, resource_type, fuel_amount):
        self.pos = pos_tuple
        self.resource_type = resource_type
        self.fuel_amount = fuel_amount


class ResourceCluster:
    """
    This class hold resource cluster specific information.
    """
    def __init__(self, map_size):
        self.map_size = map_size
        self.resource_tiles = set()
        self.size = 0
        self.fuel_amount = 0
        self.cluster_type = None
        self.surrounding_tiles_pos = set()
        self.territory = None  # can be None p for player o for opponent or b for both
        self.captured_by = None  # can be None p for player o for opponent or b for both
        self.attached_player_city_tiles_pos = set()
        self.attached_opponent_city_tiles_pos = set()
        self.unguarded_expansion_pos = set()
        self.close_opponent_units = []
        self.min_dist_to_opponent_unit = np.inf
        self.num_surrounding_units = 0
        self.num_surrounding_opponent_units = 0
        self.num_possible_expansions = 0
        self.num_wood_tiles = 0
        self.num_send_blockers = 0

    def __add__(self, other):
        """
        Adds two clusters together.
        """
        new_cluster = ResourceCluster(map_size=self.map_size)
        new_cluster.resource_tiles = set.union(self.resource_tiles, other.resource_tiles)
        new_cluster.size = self.size + other.size
        new_cluster.fuel_amount = self.fuel_amount + other.fuel_amount
        combined_cluster_types = sorted(set([t for t in self.cluster_type] + [t for t in other.cluster_type]))
        new_cluster.cluster_type = "".join(combined_cluster_types)
        new_cluster.surrounding_tiles_pos = set.union(self.surrounding_tiles_pos, other.surrounding_tiles_pos)
        if self.territory == other.territory:
            new_cluster.territory = self.territory
        else:
            new_cluster.territory = "b"

        if self.captured_by == other.captured_by:
            if self.captured_by is None:
                new_cluster.captured_by = None
            else:
                new_cluster.captured_by = self.captured_by
        elif self.captured_by != other.captured_by:
            if self.captured_by is None:
                new_cluster.captured_by = other.captured_by
            elif other.captured_by is None:
                new_cluster.captured_by = self.captured_by
            else:
                new_cluster.captured_by = "b"

        new_cluster.attached_player_city_tiles_pos = set.union(self.attached_player_city_tiles_pos,
                                                               other.attached_player_city_tiles_pos)
        new_cluster.attached_opponent_city_tiles_pos = set.union(self.attached_opponent_city_tiles_pos,
                                                                 other.attached_opponent_city_tiles_pos)
        new_cluster.unguarded_expansion_pos = set.union(self.unguarded_expansion_pos, other.unguarded_expansion_pos)
        new_cluster.min_dist_to_opponent_unit = min(self.min_dist_to_opponent_unit, other.min_dist_to_opponent_unit)
        new_cluster.num_surrounding_units = self.num_surrounding_units + other.num_surrounding_units
        new_cluster.num_surrounding_opponent_units = \
            self.num_surrounding_opponent_units + other.num_surrounding_opponent_units
        new_cluster.num_possible_expansions = self.num_possible_expansions + other.num_possible_expansions
        new_cluster.num_wood_tiles = self.num_wood_tiles + other.num_wood_tiles
        new_cluster.num_send_blockers = self.num_send_blockers + other.num_send_blockers
        return new_cluster

    def unit_is_in_cluster(self, unit):
        """
        Checks if a unit is part of a resource cluster. (Standing on or around it)
        :param unit: luc unit
        :return: boolean
        """
        is_part_of_cluster = False
        if (unit.pos.x, unit.pos.y) in [rt.pos for rt in self.resource_tiles]:
            is_part_of_cluster = True
        if (unit.pos.x, unit.pos.y) in self.surrounding_tiles_pos:
            is_part_of_cluster = True
        return is_part_of_cluster

    def add_resource_tile(self, resource_tile):
        self.resource_tiles.add(resource_tile)
        self.size += 1
        self.fuel_amount += resource_tile.fuel_amount
        if self.cluster_type is None:
            self.cluster_type = resource_tile.resource_type
        else:
            if resource_tile.resource_type not in self.cluster_type:
                self.cluster_type += resource_tile.resource_type
                sorted_items = sorted(self.cluster_type)
                self.cluster_type = "".join(sorted_items)

    def check_surrounding(self, map_width, map_height, city_map, player, opponent, unit_map, territory_map):
        """
        Checks the surrounding for this cluster and fills all its properties.
        :param map_width: lux map width
        :param map_height: lux map height
        :param city_map: Cartographer.city_map
        :param player: lux player
        :param opponent: lux opponent
        :param unit_map: Cartographer.unit_map
        :param territory_map: Cartographer.territory_map
        :return:
        """
        surrounding_tiles_pos = set()
        resource_tiles_pos = [(rt.pos[0], rt.pos[1]) for rt in self.resource_tiles]
        directions = [[0, 1], [1, 0], [0, -1], [-1, 0]]
        for tile in self.resource_tiles:
            for d in directions:
                new_x = tile.pos[0] + d[0]
                new_y = tile.pos[1] + d[1]
                if (0 <= new_x < map_width) and (0 <= new_y < map_height):
                    if ((new_x, new_y) not in surrounding_tiles_pos) and ((new_x, new_y) not in resource_tiles_pos):
                        surrounding_tiles_pos.add((new_x, new_y))
        self.surrounding_tiles_pos = surrounding_tiles_pos

        for pos in surrounding_tiles_pos:
            if city_map[pos[0]][pos[1]] == 1:
                # player city_tile
                self.attached_player_city_tiles_pos.add(pos)
            elif city_map[pos[0]][pos[1]] == 2:
                # opponent city_tile
                self.attached_opponent_city_tiles_pos.add(pos)
            else:
                # free spot:
                self.num_possible_expansions += 1

        if len(self.attached_player_city_tiles_pos) > 0:
            if len(self.attached_opponent_city_tiles_pos) > 0:
                self.captured_by = "b"
            else:
                self.captured_by = "p"
        else:
            if len(self.attached_opponent_city_tiles_pos) > 0:
                self.captured_by = "o"

        # check for closes opponent.
        opponent_obstacle_map = city_map.copy()
        for x in range(len(city_map)):
            for y in range(len(city_map[0])):
                if unit_map[x][y] == 1:
                    opponent_obstacle_map[x][y] = 1
        # --> units and city tiles count as obstacle for opponent units.
        """
        Note: If no unit is around 10 tiles the default value will be 100,
        """
        close_opponent_units = []
        min_dist = 100
        for tile in resource_tiles_pos:
            for unit in opponent.units:
                dist = Cartographer.distance(origin=(unit.pos.x, unit.pos.y), destination=tile)
                if dist < 8:
                    dist = Cartographer.distance_with_obstacles(origin=[unit.pos.x, unit.pos.y], destination=tile,
                                                                obstacles_map=opponent_obstacle_map)
                    if dist < min_dist:
                        if self.map_size in ["S", "M"]:
                            if dist <= 3:
                                close_opponent_units.append([unit, dist])
                        elif self.map_size in ["L", "XL"]:
                            if dist <= 6:
                                close_opponent_units.append([unit, dist])
                        min_dist = dist
        close_opponent_units = sorted(close_opponent_units, key=lambda k: k[1])
        close_opponent_units = [c[0] for c in close_opponent_units]
        self.close_opponent_units = close_opponent_units
        self.min_dist_to_opponent_unit = min_dist

        # check number of surrounding player units.
        for pos in surrounding_tiles_pos:
            if unit_map[pos[0]][pos[1]] == 1:
                if city_map[pos[0]][pos[1]] == 1:
                    # city tile --> check for more then on unit if
                    num_units = len([u for u in player.units if (u.pos.x, u.pos.y) == pos])
                    self.num_surrounding_units += num_units
                else:
                    self.num_surrounding_units += 1
            else:
                # no unit is standing on this tile:
                if city_map[pos[0]][pos[1]] == 0:
                    # no city tile on this position
                    self.unguarded_expansion_pos.add(pos)
        for pos in resource_tiles_pos:
            if unit_map[pos[0]][pos[1]] == 1:
                self.num_surrounding_units += 1

        # check number of surrounding opponent units.
        if self.min_dist_to_opponent_unit < 2:

            for pos in self.surrounding_tiles_pos.union(resource_tiles_pos):
                if unit_map[pos[0]][pos[1]] == 2:
                    if city_map[pos[0]][pos[1]] == 2:
                        num_units = len([u for u in opponent.units if (u.pos.x, u.pos.y) == pos])
                        self.num_surrounding_opponent_units += num_units
                    else:
                        self.num_surrounding_opponent_units += 1

        # check territory:
        for tile in self.resource_tiles:
            if territory_map[tile.pos[0]][tile.pos[1]] == 1:
                # player territory
                if self.territory is None:
                    self.territory = "p"
                elif self.territory == "o":
                    self.territory = "b"
                    break
            if territory_map[tile.pos[0]][tile.pos[1]] == 2:
                # opponent territory
                if self.territory is None:
                    self.territory = "o"
                elif self.territory == "p":
                    self.territory = "b"
                    break

        # count_num_wood_tiles:
        self.num_wood_tiles = len([rt for rt in self.resource_tiles if rt.resource_type == "w"])

    def show(self):
        """
        For debugging.
        """
        print(30 * "-")
        print(f"size: {self.size}")
        print(f"fuel_amount: {self.fuel_amount}")
        print(f"cluster_type: {self.cluster_type}")
        print(f"territory: {self.territory}")
        print(f"captures_by: {self.captured_by}")
        print(f"min_dist_to_opponent_unit: {self.min_dist_to_opponent_unit}")
        print(f"num_surrounding_units: {self.num_surrounding_units}")
        print(f"num_possible_expansions: {self.num_possible_expansions}")
        print(f"unguarded_expansion_pos: {self.unguarded_expansion_pos}")
        print(f"num_wood_tiles: {self.num_wood_tiles}")
        print(30 * "-")
