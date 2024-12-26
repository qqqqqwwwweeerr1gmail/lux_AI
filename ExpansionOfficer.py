import numpy as np
from Cartographer import Cartographer
import math
from lux.constants import Constants


class ExpansionOfficer:

    def __init__(self, lux_map, city_map, harvesting_grid, builder_obstacles_map, obstacles_map, resource_cluster,
                 movement_officer):
        """
        :param lux_map: A lux map object.
        :param city_map: A grid with 0, 1 and 2 values. (0 for no city, 1 for player city and 2 for opponent city.
        :param harvesting_grid: A grid of of HarvestingTile objects
        """
        self.height = lux_map.height
        self.width = lux_map.width
        self.map = lux_map
        self.city_map = city_map
        self.harvesting_grid = harvesting_grid
        self.builder_obstacles_map = builder_obstacles_map
        self.obstacles_map = obstacles_map
        self.expansion_map = np.zeros([self.width, self.height], np.int32)
        self.strategic_expansion_map = np.zeros([self.width, self.height], np.int32)
        self.resource_cluster = resource_cluster
        self.movement_officer = movement_officer
        self.district_mayors = None

    def build_expansion_maps(self, strategy_information, units):
        """
        Build both normal and strategic expansion map.
        :param strategy_information: StrategyInformation object
        :param units: list of free units.
        :return:
        """
        self.build_expansion_map()
        self.build_strategic_expansion_map(strategy_information=strategy_information, units=units)

    def get_number_of_free_expansion_spots(self):
        """
        Counts the number of free expansion-spots from the expansion map.
        :return:
        """
        number_of_free_expansion_spots = 0
        for x in range(self.width):
            for y in range(self.height):
                if self.expansion_map[x][y] > 0:
                    number_of_free_expansion_spots += 1
        return number_of_free_expansion_spots

    def build_expansion_map(self):
        """
        Builds a grid of possible expansion spots with specific expansion values depending on the amount of attached
        resource tiles.
        """
        for x in range(self.width):
            for y in range(self.height):
                cell = self.map.get_cell(x, y)
                if not cell.has_resource() and self.city_map[x][y] == 0:
                    # cell has no resource tiles and there is no city build on it ---> possible expansion spot.
                    harvesting_tile = self.harvesting_grid[x][y]
                    if (harvesting_tile.num_wood + harvesting_tile.num_coal + harvesting_tile.num_uranium) > 0:
                        expansion_value = 1
                    else:
                        expansion_value = 0
                    self.expansion_map[x][y] = expansion_value

    def update_expansion_maps(self, assigned_expansion_spots: list):
        """
        All assigned_spots will be removed from the expansion_map. (set to 0).
        :param assigned_expansion_spots: List of ExpansionSpots.
        """
        if len(assigned_expansion_spots) > 0:
            for spot in assigned_expansion_spots:
                self.expansion_map[spot.spot_pos[0]][spot.spot_pos[1]] = 0
                self.strategic_expansion_map[spot.spot_pos[0]][spot.spot_pos[1]] = 0

    def find_strategic_expansions(self, unit, max_number):
        if ((len(self.district_mayors) == 1) and (self.district_mayors[0].size == 1)) \
                or (len(self.district_mayors) == 0):
            # if we have no cities or only one of size one we are simply looking for the fastest expansion.
            exp_spots = self.find_fastest_expansion_for_unit(unit=unit, max_number=max_number,
                                                             expansion_map=self.expansion_map)
        else:
            """
            We have at least one city of size 2 or more cities of arbitrary size.
            At this point we care about not building to much around small clusters and not building inside fully
            Captures clusters. --> we optimise our expansion map.
            """
            exp_spots = self.find_fastest_expansion_for_unit(unit=unit, max_number=max_number,
                                                             expansion_map=self.strategic_expansion_map)
        return exp_spots

    def build_strategic_expansion_map(self, strategy_information, units):
        """
        Modifies the expansion_map to form a strategic expansion maps. I think here is a lot of potential for
        improvements.
        :param strategy_information: StrategyInformation object
        :param units: List of free units.
        """

        strategic_expansion_map = self.expansion_map.copy()
        """
        Move to cole tiles before it is researched:
        """
        for x in range(self.width):
            for y in range(self.height):
                if self.city_map[x][y] == 0:
                    cell = self.map.get_cell(x, y)
                    is_possible_coal_expansion_spot = False
                    for direction, delta in self.movement_officer.direction_dict.items():
                        adjacent_pos = cell.pos.translate(direction, 1)
                        if (0 <= adjacent_pos.x < self.width) and (0 <= adjacent_pos.y < self.height):
                            # adjacent_pos is still on map
                            adjacent_cell = self.map.get_cell(adjacent_pos.x, adjacent_pos.y)
                            if adjacent_cell.has_resource() and \
                                    adjacent_cell.resource.type == Constants.RESOURCE_TYPES.COAL:
                                is_possible_coal_expansion_spot = True
                    if is_possible_coal_expansion_spot and \
                            not cell.has_resource() and strategy_information.player_research_points > 40:
                        strategic_expansion_map[x][y] = 1
        """
        Move to uranium before it is researched:
        """
        for x in range(self.width):
            for y in range(self.height):
                if self.city_map[x][y] == 0:
                    cell = self.map.get_cell(x, y)
                    is_uranium_expansion = False
                    for direction, delta in self.movement_officer.direction_dict.items():
                        adjacent_pos = cell.pos.translate(direction, 1)
                        if (0 <= adjacent_pos.x < self.width) and (0 <= adjacent_pos.y < self.height):
                            # adjacent_pos is still on map
                            adjacent_cell = self.map.get_cell(adjacent_pos.x, adjacent_pos.y)
                            if adjacent_cell.has_resource() and \
                                    adjacent_cell.resource.type == Constants.RESOURCE_TYPES.URANIUM:
                                is_uranium_expansion = True
                    if is_uranium_expansion and \
                            not cell.has_resource() and strategy_information.player_research_points > 180:
                        strategic_expansion_map[x][y] = 1

        """
        Add strategic expansion from district mayor expansions:
        """
        for dist_major in self.district_mayors:
            other_district_mayors = [o_dist_major for o_dist_major in self.district_mayors
                                     if o_dist_major != dist_major]
            positions = dist_major.get_strategic_expansion_positions(other_district_mayors=other_district_mayors,
                                                                     harvesting_map=self.harvesting_grid, units=units,
                                                                     strategic_information=strategy_information)
            for pos in positions:
                strategic_expansion_map[pos[0]][pos[1]] = 1

        for cluster in self.resource_cluster:
            """
            Loop through all resorce clusters and adjust there expansion spots depending on the current state of the
            game.
            """
            # don't build more then one city tile at uranium or coal cluster if no opponent is around:
            if ((cluster.captured_by == "p") or (cluster.captured_by == "b")) and ("w" not in cluster.cluster_type)\
                    and (cluster.min_dist_to_opponent_unit > 6):
                for pos in cluster.surrounding_tiles_pos:
                    # exclude all expansion positions if they are not attached to wood tiles.
                    if self.harvesting_grid[pos[0]][pos[1]].num_wood == 0:
                        strategic_expansion_map[pos[0]][pos[1]] = 0

            """
            Handle player wood cluster:
            Don't over expand. We want to reserve wood as long as possible without slowing down our research speed.
            """
            if ((cluster.captured_by == "p") and ("w" in cluster.cluster_type)) \
                    and (cluster.min_dist_to_opponent_unit > 10):
                max_num_expansions = cluster.size - len(cluster.attached_player_city_tiles_pos)
                if max_num_expansions <= 0:
                    for pos in cluster.surrounding_tiles_pos:
                        strategic_expansion_map[pos[0]][pos[1]] = 0

            if ((cluster.captured_by == "p") and ("w" in cluster.cluster_type)) \
                    and (cluster.min_dist_to_opponent_unit > 4) and (strategy_information.step > 30):

                # get attached district mayors:
                attached_district_majors = set()
                for dist_major in self.district_mayors:
                    for pos in cluster.attached_player_city_tiles_pos:
                        if pos in dist_major.city_tiles_positions:
                            attached_district_majors.add(dist_major)

                # stop expanding wood cluster_cities (min size 3) if there would die from the expansion after
                # coal is researched.
                if strategy_information.player_research_status > 0:
                    for att_dist_mayor in attached_district_majors:
                        if (att_dist_mayor.num_possible_expansions == 0) and (att_dist_mayor.size > 2):
                            for pos in att_dist_mayor.expansion_positions:
                                strategic_expansion_map[pos[0]][pos[1]] = 0

                # stop expanding directly on wood clusters if uranium is researched.
                if strategy_information.player_research_status == 2:
                    for pos in cluster.surrounding_tiles_pos:
                        strategic_expansion_map[pos[0]][pos[1]] = 0

                # leave door open to closest coal or uranium cluster
                # start by finding the closest coal or uranium cluster (if there is one in range.)
                cu_clusters = [c for c in self.resource_cluster if ("u" in c.cluster_type) or ("c" in c.cluster_type)]

                close_cu_clusters = []
                for cu_cluster in cu_clusters:
                    dist, _, _ = Cartographer.distance_cluster_to_cluster(cluster1=cluster, cluster2=cu_cluster)
                    if dist < 6:
                        close_cu_clusters.append(cu_cluster)

                num_openings = 0
                for cu_cluster in close_cu_clusters:
                    # try to find best opening position for this cluster.
                    min_dist = np.inf
                    opening_pos = None
                    for pos in cluster.surrounding_tiles_pos:
                        if self.city_map[pos[0]][pos[1]] == 0:
                            dist, _ = Cartographer.distance_to_cluster(pos=pos, cluster=cu_cluster)
                            if dist < min_dist:
                                min_dist = dist
                                opening_pos = pos
                    if (opening_pos is not None) and (num_openings < 2):
                        num_openings += 1
                        strategic_expansion_map[opening_pos[0], opening_pos[1]] = 0

                if num_openings < 2:
                    """
                    We want at least 2 openings per cluster for units to leave with wood for coal and uranium 
                    expansions.
                    Even if we do not have a close by expansion spot it makes sense to keep a door open to connect
                    Attached cities. But we need to protect this gate!
                    """

                    num_further_openings = 2 - num_openings
                    for pos in cluster.surrounding_tiles_pos:
                        if num_further_openings > 0:
                            if self.city_map[pos[0], pos[1]] == 0:
                                strategic_expansion_map[pos[0], pos[1]] = 0
                                num_further_openings -= 1

        self.strategic_expansion_map = strategic_expansion_map

    def find_fastest_expansion_time_from_pos(self, pos, expansion_map, harvesting_map, radius):
        """
        Find's the fastest time to expand if a unit  with cargo = 0 would be standing on the given position.
        The idea is to check expansion times from city tiles to decide where to spawn a unit.
        Restriction: This could lead to an performance issue, so we restrict ourselfs to positions in a given radius.
        Note: Not used jet. Did not increase the performance at all... (needs fixes)
        :param pos: pos tuple
        :param expansion_map: map with expansion values.
        :param harvesting_map: harvesting map from Cartographer
        :param radius: The max radius we are looking for expansion spots.
        """
        min_building_time = np.inf
        for x in range(self.width):
            for y in range(self.height):
                if expansion_map[x][y] > 0:
                    simple_dist = Cartographer.distance(origin=[pos[0], pos[1]], destination=[x, y])
                    if simple_dist <= radius:
                        real_dist = Cartographer.distance_with_obstacles(origin=[pos[0], pos[1]], destination=[x, y],
                                                                         obstacles_map=self.builder_obstacles_map)
                        expansion_spot_collection_amount = harvesting_map[x][y].collection_amount_per_turn
                        building_time = np.inf
                        if real_dist == 1:
                            # spot is next to given position:
                            if expansion_spot_collection_amount > 0:
                                time_to_harvest = int(math.ceil(100 / expansion_spot_collection_amount))
                                building_time = time_to_harvest
                            """
                            Note: If we build a unit (City tiles are first in line), this unit can move in the same 
                            turn and collect at its destination. --> building tile harvesting time in destination.
                            (Max harvesting value in neighbor expansion spot is 60 so no need for max(time, 2).
                            """
                        elif real_dist > 1:
                            # spot is more then one tile away.
                            # try to find best next position
                            possible_spots = []
                            best_spot = None
                            min_dist = np.inf
                            for key, value in self.movement_officer.direction_dict.items():
                                new_x, new_y = x + value[0], y + value[1]
                                if (0 <= new_x < self.map.width) and (0 <= new_y < self.map.height):
                                    new_real_distance = Cartographer.distance_with_obstacles(
                                        origin=[new_x, new_y], destination=[x, y],
                                        obstacles_map=self.builder_obstacles_map)
                                    if new_real_distance < min_dist:
                                        min_dist = new_real_distance
                                    if self.builder_obstacles_map[x][y] == 0:
                                        # free spot:
                                        new_spot_collection_amount = harvesting_map[new_x][new_y].\
                                            collection_amount_per_turn
                                        possible_spots.append([(x, y), new_real_distance, new_spot_collection_amount])
                                    elif self.city_map[x][y] == 1:
                                        # player city tile --> we add 0 as spot harvesting amount.
                                        possible_spots.append([(new_x, new_y), new_real_distance, 0])
                            if len(possible_spots) == 1:
                                best_spot = possible_spots[0]
                            elif len(possible_spots) > 1:
                                # select spots with min distance (greedy)
                                min_dist = sorted(possible_spots, key=lambda k: k[1])[0]
                                possible_spots = [spot for spot in possible_spots if spot[1] == min_dist]
                                if len(possible_spots) == 1:
                                    best_spot = possible_spots[0]
                                elif len(possible_spots) > 1:
                                    # take spot with best collection amount:
                                    max_collection_amount = sorted(possible_spots, key=lambda k: k[2], reverse=True)[0]
                                    best_spot = [spot for spot in possible_spots if spot[2] == max_collection_amount][0]

                            if best_spot is not None:
                                new_spot_collection_amount = harvesting_map[best_spot[0][0]][best_spot[0][1]]. \
                                    collection_amount_per_turn
                                harvesting_amount = new_spot_collection_amount * 2 + 2 * best_spot[2]
                                if harvesting_amount >= 100:
                                    building_time = 2 * best_spot[1]
                                    # 2 + distance
                                else:
                                    new_spot_harvesting_amount = 2 * new_spot_collection_amount
                                    missing_fuel = 100 - new_spot_harvesting_amount
                                    if missing_fuel <= 0:
                                        print("WARNING: Missing Fuel is below zero!!!")
                                    if expansion_spot_collection_amount > 0:
                                        time_to_harvest = int(math.ceil(missing_fuel /
                                                                        expansion_spot_collection_amount))
                                        building_time = time_to_harvest + 2 * best_spot[2]

                        if building_time < min_building_time:
                            min_building_time = building_time
        return min_building_time

    def find_fastest_expansion_for_unit(self, unit, max_number, expansion_map):
        """
        Finds the fastest expansion for a given unit. (max_number many)
        :param max_number: The maximum number of returned expansion spots
        :param unit: Lux game unit
        :param expansion_map: map with expansion values.
        :return: List of sorted expansion spots (up to max_number many)
        """
        if unit.get_cargo_space_left() == 0 and expansion_map[unit.pos.x][unit.pos.y] > 0:
            exp_spot = ExpansionSpot(spot_pos=[unit.pos.x, unit.pos.y], unit=unit,
                                     city_grid=self.city_map, harvesting_map=self.harvesting_grid,
                                     builder_obstacles_map=self.builder_obstacles_map, obstacles_map=self.obstacles_map)
            exp_spot.time_to_build = unit.cooldown
            exp_spots = [exp_spot]
        elif unit.get_cargo_space_left() == 0 and expansion_map[unit.pos.x][unit.pos.y] == 0:
            # find closest spots (closest means fastest if unit has a full cargo.)
            exp_spots = []
            for x in range(self.width):
                for y in range(self.height):
                    if expansion_map[x][y] > 0:
                        exp_spots.append(ExpansionSpot(spot_pos=[x, y], unit=unit, city_grid=self.city_map,
                                                       harvesting_map=self.harvesting_grid,
                                                       builder_obstacles_map=self.builder_obstacles_map,
                                                       obstacles_map=self.obstacles_map))
            if len(exp_spots) > 0:
                exp_spots = sorted(exp_spots, key=lambda k: k.dist, reverse=False)
                for exp_spot in exp_spots:
                    time_to_walk = unit.cooldown + 2 * exp_spot.dist
                    exp_spot.time_to_build = time_to_walk
                exp_spots = sorted(exp_spots, key=lambda k: k.time_to_build, reverse=False)
                exp_spots = exp_spots[:max_number]

        else:
            exp_spots = []
            for x in range(self.width):
                for y in range(self.height):
                    if expansion_map[x][y] > 0:
                        if self.harvesting_grid[x][y].collection_amount_per_turn > 0:
                            exp_spots.append(ExpansionSpot(spot_pos=[x, y], unit=unit, city_grid=self.city_map,
                                                           harvesting_map=self.harvesting_grid,
                                                           builder_obstacles_map=self.builder_obstacles_map,
                                                           obstacles_map=self.obstacles_map))

            if len(exp_spots) > 0:
                exp_spots = sorted(exp_spots, key=lambda k: k.dist, reverse=False)
                for exp_spot in exp_spots:
                    # cargo until next possible step
                    cargo = 100 - unit.get_cargo_space_left() + unit.cooldown * exp_spot.origin_harvesting_amount

                    # add cargo from traveling.
                    """
                    Note: We do not take more the the next step (the next tile) into account.
                    """
                    if exp_spot.dist == 1:
                        # easy case: expansion spot i neighbor tile.
                        cargo += 2 * exp_spot.spot_collection_amount
                    else:
                        # expansion spot is more then one tile away. We add the farming amount of the first tile in the
                        # expansion direction times 2 (unit needs to stand there for 2 round until it can move again).

                        # try to find best next position
                        best_next_pos = None

                        directions = self.movement_officer.get_possible_directions_for_unit(
                            unit=unit, destination=exp_spot.spot_pos, is_builder=True, is_returning_harvester=False,
                            use_obstacle_maps=True)
                        max_direction_value = 0
                        new_positions_with_values = []
                        for direction in directions:
                            new_pos = (unit.pos.x + self.movement_officer.direction_dict[direction][0],
                                       unit.pos.y + self.movement_officer.direction_dict[direction][1])
                            # define direction value

                            if unit.get_cargo_space_left() > 0:
                                direction_value = self.movement_officer.harvesting_map[new_pos[0]][
                                    new_pos[1]].collection_amount_per_turn
                            else:
                                direction_value = 0
                            if direction_value > max_direction_value:
                                max_direction_value = direction_value
                            new_positions_with_values.append([direction_value, new_pos])

                        if len(new_positions_with_values) > 0:
                            best_next_pos = [pos_and_val[1] for pos_and_val in new_positions_with_values if
                                             pos_and_val[0] == max_direction_value][0]

                        if best_next_pos is not None:
                            # farming amount from next cell + farming amount from expansion spot if we find a next pos.
                            cargo += 2 * exp_spot.spot_collection_amount \
                                     + 2 * self.harvesting_grid[best_next_pos[0]][
                                         best_next_pos[1]].collection_amount_per_turn
                        else:
                            # if we don't find a next position.
                            cargo += 2 * exp_spot.spot_collection_amount

                    # calculate building time
                    if cargo >= 100:
                        # by the time the unit can build he will have enough material to build so if it moves directly
                        # to the spot
                        time = unit.cooldown + 2 * exp_spot.dist
                    else:
                        # unit needs to farm at building spot, so we add the spot_harvesting_amount until 100 is reached
                        missing_material = 100 - cargo
                        if exp_spot.spot_collection_amount > 0:
                            # harvesting at spot location:
                            time_to_harvest = int(math.ceil(missing_material / exp_spot.spot_collection_amount))
                        else:
                            # 100 is only a dummy value
                            time_to_harvest = 100
                        time_to_walk = unit.cooldown + 2 * exp_spot.dist
                        time = time_to_walk + time_to_harvest

                    exp_spot.time_to_build = time

                # sort by time_to_build
                exp_spots = sorted(exp_spots, key=lambda k: k.time_to_build, reverse=False)
                exp_spots = exp_spots[:max_number]
        return exp_spots


class ExpansionSpot:
    """
    Holds all information about an expansion spot.
    """
    def __init__(self, spot_pos, unit, city_grid, harvesting_map, builder_obstacles_map, obstacles_map):
        self.id = f"{spot_pos[0]}{spot_pos[1]}"
        self.spot_pos = spot_pos
        self.unit = unit
        self.city_grid = city_grid
        self.harvesting_map = harvesting_map
        self.origin_pos = [unit.pos.x, unit.pos.y]
        if city_grid[unit.pos.x][unit.pos.y] > 0:
            # unit standing on city tile :
            self.origin_harvesting_amount = 0
        else:
            self.origin_harvesting_amount = harvesting_map[unit.pos.x][unit.pos.y].collection_amount_per_turn
        self.spot_collection_amount = harvesting_map[spot_pos[0]][spot_pos[1]].collection_amount_per_turn

        self.harvesting_pos = self.find_harvesting_spot()
        self.dist = self.calculate_distance(builder_obstacles_map=builder_obstacles_map, obstacles_map=obstacles_map)
        self.time_to_build = None

    def find_harvesting_spot(self):
        """
        Finds a suitable farming spot if an expansion spot has no collection amount.
        :return:
        """
        if (self.spot_collection_amount == 0) and (self.unit.get_cargo_space_left() != 0):
            # find closest farming spot near unit
            # look around building unit
            min_dist = np.inf
            closest_spot = None
            closest_spot_pos = None
            for x in range(len(self.city_grid)):
                for y in range(len(self.city_grid[0])):
                    if self.harvesting_map[x][y].num_wood > 0:
                        simple_dist = Cartographer.distance(origin=self.origin_pos, destination=[x, y])
                        if simple_dist < min_dist:
                            min_dist = simple_dist
                            closest_spot = self.harvesting_map[x][y]
                            closest_spot_pos = (x, y)
                        elif simple_dist < min_dist + 2:
                            if self.harvesting_map[x][y].collection_amount_per_turn > closest_spot.collection_amount_per_turn + 10:
                                # we do not adjust min_dist here!
                                closest_spot = self.harvesting_map[x][y]
                                closest_spot_pos = (x, y)
            if closest_spot is not None:
                harvesting_pos = closest_spot_pos
            else:
                harvesting_pos = self.spot_pos
        else:
            # spot_collection_amount < 20 or unit has full cargo.
            harvesting_pos = self.spot_pos
        return harvesting_pos

    def calculate_distance(self, builder_obstacles_map, obstacles_map):
        """
        Calculate distance to expansions spot. If a unit has at least 60 cargo we don't want to walk over city tiles.
        Further more if the distance is more then 8 we use the simple distance for performance reasons.
        We always move to the harvesting position. If we have a full cargo or the spot pos is a good harvesting spot
        we will move to the building spot.
        :return: int
        """
        simple_dist = Cartographer.distance(origin=self.origin_pos, destination=self.harvesting_pos)

        cargo = 100 - self.unit.get_cargo_space_left()
        if cargo >= 60:
            obstacles_map = builder_obstacles_map
        else:
            obstacles_map = obstacles_map

        if simple_dist < 8:
            dist = Cartographer.distance_with_obstacles(obstacles_map=obstacles_map, origin=self.origin_pos,
                                                        destination=self.harvesting_pos)
        else:
            dist = simple_dist
        return dist

    def show(self):
        """
        Display function for debugging.
        """
        print(30 * "-")
        print("spot_pos: ", self.spot_pos)
        print("harvesting_pos: ", self.harvesting_pos)
        print("origin_pos: ", self.origin_pos)
        print("dist: ", self.dist)
        print("origin_harvesting_amount: ", self.origin_harvesting_amount)
        print("spot_harvesting_amount: ", self.spot_collection_amount)
        print("time_to_build: ", self.time_to_build)
        print(30 * "-")


