from Cartographer import Cartographer
import numpy as np


class CityCouncil:
    """
    Manages information about each city.
    Each city has a DistrictMayor and the CityCouncil manages them.
    """
    def __init__(self, lux_map, city_map, unit_map, player, harvesting_map, expansion_officer):
        self.map = lux_map
        self.city_map = city_map
        self.unit_map = unit_map
        self.player = player
        self.harvesting_map = harvesting_map
        self.cities = player.cities
        self.expansion_officer = expansion_officer
        self.district_mayors = []

    def distribute_fuel_income(self):
        """
        Distributes the fuel-income per turn by giving each city a priority. (for harvesters)
        :return:
        """
        for dm in self.district_mayors:
            if not dm.survives_all_nights:
                if not dm.survives_next_night:
                    dm.harvesting_priority = dm.size + 1
                else:
                    dm.harvesting_priority = dm.size

    def summon_district_mayors(self, night_steps_left):
        district_mayors = []
        for city in self.cities.values():
            district_mayors.append(DistrictMayor(city=city, harvesting_map=self.harvesting_map,
                                                 night_steps_left=night_steps_left, lux_map=self.map,
                                                 city_map=self.city_map, unit_map=self.unit_map))
        self.district_mayors = district_mayors
        self.distribute_fuel_income()

    def get_district_mayor_by_id(self, city_id):
        """
        Return district major based on his city_id
        :param city_id: str
        :return: DistrictMayor
        """
        return_district_major = None
        for district_mayor in self.district_mayors:
            if district_mayor.city.cityid == city_id:
                return_district_major = district_mayor
                break
        return return_district_major

    def get_district_mayor_by_pos(self, pos):
        """
        Return district major based on pos
        :param pos: tupel
        :return: DistrictMayor
        """
        return_district_major = None
        for district_mayor in self.district_mayors:
            if pos in district_mayor.city_tiles_positions:
                return_district_major = district_mayor
                break
        return return_district_major

    def build_fastest_expanding_units_and_research(self, max_worker_to_build):
        """
        Build units where the expansion time is shortest. It is not always advantageous to build a new unit when it is
        possible.
        Logic: Build units on tiles with the least expansion time. If we have more than one tile with the same time,
         we choose the tile of the newest city.
        Note: Not used. Needs to be improved...
        :param : max_worker_to_build: Maximum number of workers we can build this turn.
        """
        actions = []
        if max_worker_to_build > 0:
            # order city by id: returns list of tuples [[city_id, city], ...] that can be sorted by city_id
            city_ids = [[city.cityid[city.cityid.find("_") + 1:], city] for city in self.cities.values()]
            cities = sorted(city_ids, key=lambda k: k[0], reverse=True)
            tiles_with_expansion_time_and_age = []
            # [tile, min_expansion_time, age]
            age = 0
            for city in cities:
                for city_tile in reversed(city[1].citytiles):
                    expansion_time = self.expansion_officer.find_fastest_expansion_time_from_pos(
                        pos=(city_tile.pos.x, city_tile.pos.y),
                        expansion_map=self.expansion_officer.strategic_expansion_map,
                        harvesting_map=self.harvesting_map, radius=5)
                    expansion_time += city_tile.cooldown
                    tiles_with_expansion_time_and_age.append([city_tile, expansion_time, age])
                    age += 1
            # sort city_tiles by expansion_time and then by age. --> if we have two tiles with the same expansion value
            # we prefer the city_tile from the newer city.
            tiles_with_expansion_time_and_age = sorted(tiles_with_expansion_time_and_age, key=lambda k: (k[1], k[2]))
            # try to build the units with the first max_worker_to_build city_tiles.
            index = 1
            for tile_info in tiles_with_expansion_time_and_age:
                city_tile = tile_info[0]
                if index <= max_worker_to_build:
                    if city_tile.can_act():
                        action = city_tile.build_worker()
                        actions.append(action)
                else:
                    # research if necessary
                    if not self.player.researched_uranium():
                        action = city_tile.research()
                        actions.append(action)
                index += 1

        else:
            # we cant build workers. So research if possible and necessary:
            for city in self.cities.values():
                for city_tile in city.citytiles:
                    if not self.player.researched_uranium() and city_tile.can_act():
                        action = city_tile.research()
                        actions.append(action)
        return actions

    def build_units_and_research(self, max_worker_to_build):
        """
        Handle unit building and researching.
        :param max_worker_to_build:
        :return:
        """
        actions = []
        # order city by id: returns list of tuples [[city_id, city], ...] that can be sorted by city_id
        city_ids = [[city.cityid[city.cityid.find("_") + 1:], city] for city in self.cities.values()]
        # sort cities by id:
        cities = sorted(city_ids, key=lambda k: k[0], reverse=True)
        for city in cities:
            # now we loop in reverse to prefer newer city tiles for unit production.
            for city_tile in reversed(city[1].citytiles):
                if city_tile.can_act():
                    if max_worker_to_build > 0:
                        action = city_tile.build_worker()
                        actions.append(action)
                        max_worker_to_build -= 1
                    else:
                        if not self.player.researched_uranium():
                            # We only research until we researched uranium. Then we stop and
                            # don't wast city cd for useless further research points.
                            action = city_tile.research()
                            actions.append(action)
        return actions


class DistrictMayor:
    """"
    Handles information from one city.
    """
    def __init__(self, city, harvesting_map, night_steps_left, lux_map, city_map, unit_map):
        self.origin = [city.citytiles[0].pos.x, city.citytiles[0].pos.y]
        self.city_tiles_positions = set([(tile.pos.x, tile.pos.y) for tile in city.citytiles])
        self.city = city
        self.city_map = city_map
        self.harvesting_map = harvesting_map
        self.size = len(city.citytiles)
        self.light_upkeep = city.get_light_upkeep()
        self.survives_next_night = bool((self.light_upkeep * 10) < city.fuel)
        self.survives_all_nights = bool((self.light_upkeep * night_steps_left) < city.fuel)
        self.expansion_positions = self.get_expansion_positions(lux_map=lux_map, city_map=city_map)
        self.free_district_harvesting_spots = []
        self.best_free_harvesting_spot = None
        self.update_district_harvesting_information(harvesting_map=harvesting_map, unit_map=unit_map,
                                                    assigned_positions=[])
        self.fuel_income_per_turn = self.get_fuel_income_per_turn(harvesting_map=harvesting_map, unit_map=unit_map)
        # Resource drops on CityTiles is before CityTiles consume fuel so we add fuel_income_per_turn to city.fuel
        self.district_harvesting_spots = self.get_district_harvesting_spots(harvesting_map=harvesting_map)
        self.harvesting_priority = 0
        self.num_possible_expansions = self.get_min_num_possible_expansions(night_steps_left)

    def get_min_num_possible_expansions(self, night_steps_left):
        """
        Calculates the max number of possible expansions that won't kill the city until the end of the game.
        :param night_steps_left:
        :return: num possible expansions as int
        """
        if self.survives_all_nights:
            num_possible_expansions = 0
            for i in range(11):
                # max will be 10 but this should be enough
                if bool(((self.light_upkeep + i * 24) * night_steps_left) < self.city.fuel):
                    num_possible_expansions += 1
                else:
                    break
        else:
            num_possible_expansions = 0

        return num_possible_expansions

    def get_strategic_expansion_positions(self, other_district_mayors, units, harvesting_map, strategic_information):
        """
        Logic:
        1) Expand on uranium and coal cities if they would survive the next night
        2) Expand cities that would survive until the end.
        3) Try to wall enemies
        """

        """
        1) Expand on uranium and coal cities if they would survive the next night.
        a) If city.size == 1 --> expand in all possible directions
        b) Else expand in direction of all other clusters with min size 2.
        c) And we ensure that expansion spots ar not only attached to coal or uranium tiles. Otherwise they might be 
            blocked by harvesters.
        d) expand in all directions if its last day and city would survive last night
        """
        def add_positions_close_other_clusters(usable_positions):
            for other_dist_mayor in priority_other_district_mayors:
                min_dist = np.inf
                expansion_pos = None
                for pos in usable_positions:
                    dist, _ = Cartographer.distance_to_district(pos=pos, district_mayor=other_dist_mayor)
                    if dist < min_dist:
                        min_dist = dist
                        expansion_pos = pos
                if expansion_pos is not None:
                    strategic_expansion_positions.add(expansion_pos)

        strategic_expansion_positions = set()
        is_coal_or_uranium_expansion = False
        for ha_spot in self.district_harvesting_spots:
            if ha_spot.includes_coal or ha_spot.includes_uranium:
                is_coal_or_uranium_expansion = True

        priority_other_district_mayors = [dm for dm in other_district_mayors if dm.size >= 2]

        if is_coal_or_uranium_expansion and self.survives_next_night:
            if self.size == 1:
                """ a) """
                strategic_expansion_positions = self.expansion_positions.copy()
            else:
                """ b) """
                add_positions_close_other_clusters(usable_positions=self.expansion_positions)
                """ c) """
                no_non_c_u_harvesting_expansion_spot = True
                for pos in strategic_expansion_positions:
                    harvesting_tile = harvesting_map[pos[0]][pos[1]]
                    if ((harvesting_tile.num_coal == 0) and (harvesting_tile.num_uranium == 0)) or \
                            harvesting_tile.num_wood > 0:
                        no_non_c_u_harvesting_expansion_spot = False
                        break
                if no_non_c_u_harvesting_expansion_spot:
                    # try to find expansion spot that is not a coal or uranium spot:
                    possible_position = set()
                    for pos in self.expansion_positions:
                        harvesting_tile = harvesting_map[pos[0]][pos[1]]
                        if ((harvesting_tile.num_coal == 0) and (harvesting_tile.num_uranium == 0)) or \
                                harvesting_tile.num_wood > 0:
                            possible_position.add(pos)

                    add_positions_close_other_clusters(usable_positions=possible_position)
                """ d) """
                if strategic_information.step >= 320:
                    for pos in self.expansion_positions:
                        strategic_expansion_positions.add(pos)

        elif is_coal_or_uranium_expansion is False and (self.num_possible_expansions > 0):
            """
            2) Expand cities that would survive until the end. 
            a) expand in direction of closest unit with 100 wood 
            b) if no spots where found try the same thing but with cycles
            c) expand in all directions if last day
            """
            """ a) """
            full_cargo_units = [unit for unit in units if unit.get_cargo_space_left() == 0]
            # use only expansion positions that are not attached to a wood cluster and that are not closing a cyrcle.
            possible_expansions_positions = []
            for pos in self.expansion_positions:
                if harvesting_map[pos[0]][pos[1]].num_wood == 0:
                    # check if more then one other city tile is connected to pos (one and 3 is ok but 2 is not ok)
                    # not on map counts as city tile.
                    num_surrounding_city_tiles = 0
                    directions = [[0, 1], [1, 0], [0, -1], [-1, 0]]
                    for d in directions:
                        new_x = pos[0] + d[0]
                        new_y = pos[1] + d[1]
                        if (0 <= new_x < len(self.harvesting_map)) and (0 <= new_y < len(self.harvesting_map[0])):
                            if self.city_map[new_x][new_y] > 0:
                                num_surrounding_city_tiles += 1
                        else:
                            num_surrounding_city_tiles += 1
                    if num_surrounding_city_tiles != 2:
                        possible_expansions_positions.append(pos)

            num_expansions = 0
            min_dist = np.inf
            positions = set()
            for i in range(self.num_possible_expansions):
                used_units = set()
                for unit in full_cargo_units:
                    for tile_pos in possible_expansions_positions:
                        dist = Cartographer.distance(origin=(unit.pos.x, unit.pos.y), destination=tile_pos)
                        if dist < min_dist:
                            positions = set()
                            positions.add(tile_pos)
                            used_units = set()
                            used_units.add(unit)
                            min_dist = dist
                        elif dist == min_dist:
                            positions.add(tile_pos)
                            used_units.add(unit)
                for pos in positions:
                    strategic_expansion_positions.add(pos)
                    num_expansions += 1
                for u in used_units:
                    full_cargo_units.remove(u)

            """ b) """
            if (self.num_possible_expansions - num_expansions) > 0:
                # use only expansion positions that are not attached to a wood cluster
                possible_expansions_positions = [pos for pos in self.expansion_positions
                                                 if harvesting_map[pos[0]][pos[1]].num_wood == 0]
                num_expansions = 0
                min_dist = np.inf
                positions = set()
                for i in range(self.num_possible_expansions):
                    used_units = set()
                    for unit in full_cargo_units:
                        for tile_pos in possible_expansions_positions:
                            dist = Cartographer.distance(origin=(unit.pos.x, unit.pos.y), destination=tile_pos)
                            if dist < min_dist:
                                positions = set()
                                positions.add(tile_pos)
                                used_units = set()
                                used_units.add(unit)
                                min_dist = dist
                            elif dist == min_dist:
                                positions.add(tile_pos)
                                used_units.add(unit)
                    for pos in positions:
                        strategic_expansion_positions.add(pos)
                        num_expansions += 1
                    for u in used_units:
                        full_cargo_units.remove(u)

            """ c) """
            if strategic_information.step >= 320:
                for pos in possible_expansions_positions:
                    strategic_expansion_positions.add(pos)

        return strategic_expansion_positions

    def update_district_harvesting_information(self, harvesting_map, unit_map, assigned_positions):
        """
        Updates free_district_harvesting_spots and best_free_harvesting_spot.
        :param harvesting_map: harvesting map
        :param unit_map: unit map
        :param assigned_positions: list of tuples with positions of taken tiles.
        """
        self.free_district_harvesting_spots = self.get_free_district_harvesting_spots(harvesting_map=harvesting_map,
                                                                                      unit_map=unit_map,
                                                                                      assigned_positions=
                                                                                      assigned_positions)
        if len(self.free_district_harvesting_spots) == 1:
            self.best_free_harvesting_spot = sorted(self.free_district_harvesting_spots,
                                                    key=lambda k: k.harvesting_value, reverse=True)[0]
        elif len(self.free_district_harvesting_spots) > 1:
            self.best_free_harvesting_spot = self.free_district_harvesting_spots[0]
        else:
            self.best_free_harvesting_spot = None

    def get_expansion_positions(self, lux_map, city_map):
        """
        All tiles that would expand this city. Regardless if it would be a good expansion or not.
        :return:
        """
        expansion_positions = set()
        directions = [[1, 0], [0, 1], [-1, 0], [0, -1]]
        for tile in self.city.citytiles:
            for d in directions:
                adjacent_pos = [tile.pos.x + d[0], tile.pos.y + d[1]]
                if (0 <= adjacent_pos[0] < lux_map.width) and (0 <= adjacent_pos[1] < lux_map.height):
                    cell = lux_map.get_cell(tile.pos.x + d[0], tile.pos.y + d[1])
                    if not cell.has_resource() and city_map[tile.pos.x + d[0]][tile.pos.y + d[1]] == 0:
                        expansion_positions.add((tile.pos.x + d[0], tile.pos.y + d[1]))
        return expansion_positions

    def get_district_harvesting_spots(self, harvesting_map):
        """
        Builds a sorted list of HarvestingSpots for this district. Includes only spots with positive harvesting_value.
        :param harvesting_map: Cartographer.harvesting_map
        :return: A sorted list of HarvestingSpots.
        """
        district_harvesting_spots = []
        for tile in self.city.citytiles:
            # city tile is free
            harvesting_tile = harvesting_map[tile.pos.x][tile.pos.y]
            if harvesting_tile.fuel_value_per_turn > 0:
                district_harvesting_spots.append(DistrictHarvestingSpot(pos=(tile.pos.x, tile.pos.y),
                                                                        harvesting_tile=harvesting_tile))
        district_harvesting_spots = sorted(district_harvesting_spots, key=lambda k: k.harvesting_value, reverse=True)
        return district_harvesting_spots

    def get_free_district_harvesting_spots(self, harvesting_map, unit_map, assigned_positions):
        """
        Get all free district harvesting spots based on the unit_map and additional assigned positions.
        :param harvesting_map: harvesting map
        :param unit_map: unit map
        :param assigned_positions: list of tuples with positions of taken tiles.
        :return: a list of DistrictHarvestingSpot with positions and specific harvesting value.
        """

        own_unit_map = unit_map.copy()
        for pos_list in assigned_positions:
            own_unit_map[pos_list[0]][pos_list[1]] = 1

        district_harvesting_spots = []
        for tile in self.city.citytiles:
            if own_unit_map[tile.pos.x][tile.pos.y] == 0:
                # city tile is free
                harvesting_tile = harvesting_map[tile.pos.x][tile.pos.y]
                district_harvesting_spots.append(DistrictHarvestingSpot(pos=(tile.pos.x, tile.pos.y),
                                                                        harvesting_tile=harvesting_tile))
        return district_harvesting_spots

    def get_fuel_income_per_turn(self, harvesting_map, unit_map):
        """
        Calculates the fuel-income per turn for this city. (from city harvesters only)
        :param harvesting_map: Cartographer.harvesting_map
        :param unit_map: Cartographer.unit_map
        :return:
        """
        fuel_income_per_turn = 0
        for tile in self.city.citytiles:
            if unit_map[tile.pos.x][tile.pos.y] == 1:
                # min one unit standing on city tile --> is harvesting for city
                fuel_income_per_turn += harvesting_map[tile.pos.x][tile.pos.y].fuel_value_per_turn
        return fuel_income_per_turn

    def show(self):
        """
        For debugging.
        """
        print(30 * "*")
        print("City_id: ", self.city.cityid)
        print("Size: ", self.size)
        print("fuel:", self.city.fuel)
        print("fuel_consumption_per_night: ", self.light_upkeep)
        print("survives_next_night: ", self.survives_next_night)
        print("survives_all_nights: ", self.survives_all_nights)
        print("expansion_positions: ", self.expansion_positions)
        print("fuel_income_per_turn: ", self.fuel_income_per_turn)
        print(30 * "*")


class DistrictHarvestingSpot:
    """
    Holds information about a district harvesting spot.
    """
    def __init__(self, pos, harvesting_tile):
        self.pos = pos
        self.harvesting_value = harvesting_tile.fuel_value_per_turn
        self.includes_wood = (harvesting_tile.num_wood > 0)
        self.includes_coal = (harvesting_tile.num_coal > 0)
        self.includes_uranium = (harvesting_tile.num_uranium > 0)
