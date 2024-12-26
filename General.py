from lux import annotate
from enum import Enum
import numpy as np
from Cartographer import Cartographer
import math
from ExpansionOfficer import ExpansionSpot


class General:
    def __init__(self, cartographer, expansion_officer, movement_officer, city_council, harvesting_officer, actions):
        self.cartographer = cartographer
        self.expansion_officer = expansion_officer
        self.movement_officer = movement_officer
        self.city_council = city_council
        self.harvesting_officer = harvesting_officer
        self.units_cap = sum([len(x.citytiles) for x in cartographer.player.cities.values()])
        self.num_units = len(cartographer.player.units)
        self.free_units = set(cartographer.player.units.copy())
        self.assigned_builder_ids = set()
        self.night_steps_left = 0
        self.steps_until_night = 0
        self.steps_until_day = 0
        self.day = True
        self.actions = actions
        self.orders = []
        self.strategy_information = None
        max_worker_to_build = self.units_cap - self.num_units
        building_and_research_actions = self.city_council.build_units_and_research(
            max_worker_to_build=max_worker_to_build)
        self.actions += building_and_research_actions
        # update num units
        self.num_units = len(cartographer.player.units)
        self.free_units = set(cartographer.player.units.copy())

    def order(self):
        """
        Gives each unit an order for one step. We need to handle some exceptions though....
        """

        """
        Support early uranium or coal expansion. (if we build a uranium or coal expansion we need to ensure that this 
        expansion wont die.)
        """
        city_units = [u for u in self.free_units if self.cartographer.city_map[u.pos.x][u.pos.y] == 1]
        secured_positions = set()
        for unit in city_units:
            if self.strategy_information.player_research_status == 1:
                # check if coal harvesting spot:
                if self.cartographer.harvesting_map[unit.pos.x][unit.pos.y].num_coal > 0:
                    if (unit.pos.x, unit.pos.y) not in secured_positions:
                        self.assign_order_to_unit(unit=unit, position_tuple=(unit.pos.x, unit.pos.y),
                                                  order_type=OrderType.CitySupport)
                        secured_positions.add((unit.pos.x, unit.pos.y))
            if self.strategy_information.player_research_status == 2:
                # check if coal harvesting spot:
                if self.cartographer.harvesting_map[unit.pos.x][unit.pos.y].num_coal > 0\
                        or self.cartographer.harvesting_map[unit.pos.x][unit.pos.y].num_uranium > 0:
                    if (unit.pos.x, unit.pos.y) not in secured_positions:
                        self.assign_order_to_unit(unit=unit, position_tuple=(unit.pos.x, unit.pos.y),
                                                  order_type=OrderType.CitySupport)
                        secured_positions.add((unit.pos.x, unit.pos.y))
        # get harvesting units

        self.order_unit_distribution()

        if self.strategy_information.num_player_city_tiles > self.strategy_information.num_player_save_city_tiles:
            """
            If we have cities to support we don't want units with substantial amounts of fuel value to switch orders.
            Wood harvester will possible still switch orders.
            """
            harvester = set()
            for unit in self.free_units:
                # get cluster of unit:
                if unit.cargo.coal > 50:
                    unit_cluster = None
                    for cluster in self.cartographer.resource_clusters:
                        if "c" in cluster.cluster_type:
                            cluster_tiles = [rt.pos for rt in cluster.resource_tiles] + \
                                            [t for t in cluster.surrounding_tiles_pos]
                            if (unit.pos.x, unit.pos.y) in cluster_tiles:
                                unit_cluster = cluster
                                break
                    if (unit_cluster is None) or (unit_cluster is not None
                                                and (unit_cluster.min_dist_to_opponent_unit > 6)):
                        # add units to harvesters if they are not part of an coal cluster that is under attack
                        harvester.add(unit)
                if unit.cargo.uranium > 30:
                    harvester.add(unit)
            if len(harvester) > 1:
                self.order_harvesting(units=harvester)

        """
        If a unit is standing on an possible expansion spot and an opponent unit is standing right next to it.
        it should not move.
        """
        check_units = [u for u in self.free_units.copy()
                       if self.cartographer.harvesting_map[u.pos.x][u.pos.y].collection_amount_per_turn > 0]
        for unit in check_units:
            if (self.expansion_officer.expansion_map[unit.pos.x][unit.pos.y] != 0) and (
                    self.expansion_officer.strategic_expansion_map[unit.pos.x][unit.pos.y] == 0):
                # check if enemy unit want on this spot:
                # close by opponent unit:
                opp_unit_close_by = False
                for opp_unit in self.cartographer.opponent.units:
                    dist = Cartographer.distance(origin=(unit.pos.x, unit.pos.y),
                                                 destination=(opp_unit.pos.x, opp_unit.pos.y))
                    if dist <= 2:
                        opp_unit_close_by = True
                        break
                if opp_unit_close_by:
                    self.assign_order_to_unit(unit=unit, position_tuple=(unit.pos.x, unit.pos.y),
                                              order_type=OrderType.ClusterDefence)
            elif (self.expansion_officer.expansion_map[unit.pos.x][unit.pos.y] != 0) and (
                    self.expansion_officer.strategic_expansion_map[unit.pos.x][unit.pos.y] != 0):
                # in this case we should build there.
                spot = ExpansionSpot(spot_pos=[unit.pos.x, unit.pos.y], unit=unit,
                                     city_grid=self.expansion_officer.city_map,
                                     harvesting_map=self.expansion_officer.harvesting_grid,
                                     builder_obstacles_map=self.expansion_officer.builder_obstacles_map,
                                     obstacles_map=self.expansion_officer.obstacles_map)
                self.assign_order_to_unit(unit=spot.unit, position_tuple=spot.harvesting_pos,
                                          order_type=OrderType.Expansion, additional_information=spot)

        """
        Basic order for orders in respect of the steps_until_night.
        """
        if self.steps_until_night < 6:
            # save units that need saving.
            self.order_city_support()
            self.order_expansions()
            self.order_save_spots()
            self.order_unit_blocking()
            self.order_resource_defense()
            self.order_harvesting()
        else:
            self.order_unit_blocking()
            self.order_expansions()
            self.order_resource_defense()
            self.order_city_support()
            self.order_harvesting()

        """
        For debugging:
        Shoa order development and overall development.
        """
        #self.print_orders()
        #self.strategy_information.show()

    def print_orders(self):
        num_orders = len(self.orders)
        building_orders = [o for o in self.orders if o.order_type == OrderType.Expansion]
        city_support = [o for o in self.orders if o.order_type == OrderType.CitySupport]
        save_spot = [o for o in self.orders if o.order_type == OrderType.SaveSpot]
        harvest_go = [o for o in self.orders if o.order_type == OrderType.Harvest_Go]
        harvest_return = [o for o in self.orders if o.order_type == OrderType.Harvest_Return]
        cluster_defence = [o for o in self.orders if o.order_type == OrderType.ClusterDefence]
        distribution = [o for o in self.orders if o.order_type == OrderType.Distribution]
        blockers = [o for o in self.orders if o.order_type == OrderType.Blocking]
        num_free_units = len(self.free_units)
        print(f"step: {self.cartographer.observation['step']}, units / free: ({self.num_units} / "
              f"{num_free_units}) , num_orders: {num_orders} "
              f"(b: {len(building_orders)}, cs:{len(city_support)}, s: {len(save_spot)}, hg: {len(harvest_go)},"
              f" hr: {len(harvest_return)}, cd: {len(cluster_defence)}, d: {len(distribution)}),"
              f" b: {len(blockers)})")

    def execute_orders(self, game_state, show_annotation):
        """
        Executes orders. --> adds actions to actions.
        Note: We wont build 3 days before night if a city can't sustain by its own.
        :param game_state: global game_state
        :param show_annotation: boolean.
        """
        move_orders = []
        for order in self.orders:
            if order.dist == 0:
                if order.order_type == OrderType.Expansion:
                    # try to build:
                    if order.unit.can_act() and order.unit.can_build(game_state.map):
                        if order.additional_information.spot_collection_amount < 21:
                            # city can't be supported by its own. --> don't build 3 steps before night.
                            if self.steps_until_night > 3:
                                action = order.unit.build_city()
                                self.actions.append(action)
                        else:
                            action = order.unit.build_city()
                            self.actions.append(action)
            else:
                # move
                if order.unit.can_act():
                    move_orders.append(order)
        move_actions = self.movement_officer.move_units(move_orders=move_orders)

        for action in move_actions:
            self.actions.append(action)

        if show_annotation:
            self.order_annotation()

    def assign_order_to_unit(self, unit, position_tuple, order_type, additional_information=None):
        """
        Assigns an oder to a unit and thereby removes unit from free units.
        """
        if unit in self.free_units:
            self.orders.append(Order(order_type=order_type, unit=unit,
                                     pos=position_tuple, additional_information=additional_information))
            self.free_units.remove(unit)

    def order_annotation(self):
        """
        Handles order annotations.
        Note: Could be extended by text annotations.
        """
        for order in self.orders:
            if order.order_type == OrderType.Expansion:
                self.actions.append(annotate.circle(order.pos[0], order.pos[1]))
                self.actions.append(annotate.line(order.unit.pos.x, order.unit.pos.y, order.pos[0], order.pos[1]))
            elif order.order_type == OrderType.CitySupport:
                self.actions.append(annotate.x(order.pos[0], order.pos[1]))
                self.actions.append(annotate.line(order.unit.pos.x, order.unit.pos.y, order.pos[0], order.pos[1]))
                self.actions.append(annotate.text(order.unit.pos.x, order.unit.pos.y, "H", 15))
            elif order.order_type == OrderType.SaveSpot:
                self.actions.append(annotate.x(order.pos[0], order.pos[1]))
                self.actions.append(annotate.circle(order.pos[0], order.pos[1]))
                self.actions.append(annotate.line(order.unit.pos.x, order.unit.pos.y, order.pos[0], order.pos[1]))
            elif order.order_type == OrderType.Distribution:
                self.actions.append(annotate.x(order.pos[0], order.pos[1]))
                self.actions.append(annotate.line(order.unit.pos.x, order.unit.pos.y, order.pos[0], order.pos[1]))
            elif order.order_type == OrderType.Blocking:
                self.actions.append(annotate.x(order.pos[0], order.pos[1]))
                self.actions.append(annotate.line(order.unit.pos.x, order.unit.pos.y, order.pos[0], order.pos[1]))

    def get_distribution_options_for_cluster(self, cluster):
        """
        Builds and returns an ClusterDistributionOptions object.
        We use only wood cluster for distribution.
        """
        cluster_dist_opts = ClusterDistributionOptions(cluster=cluster, units=self.free_units,
                                                       strat_info=self.strategy_information,
                                                       city_council=self.city_council)
        other_clusters = [c for c in self.cartographer.resource_clusters if (c != cluster)
                          and ("w" in c.cluster_type) and (c.size >= 2)]

        for other_cluster in other_clusters:
            dist, origin_tile_pos, destination_tile_pos = Cartographer.distance_cluster_to_cluster(
                cluster1=cluster, cluster2=other_cluster)
            if origin_tile_pos is not None:
                cluster_dist_opts.add_spot(DistributionSpot(other_cluster=other_cluster, dist=dist,
                                                            origin_cluster=cluster,
                                                            origin_tile_pos=origin_tile_pos,
                                                            destination_tile_pos=destination_tile_pos))

        cluster_dist_opts.prioritize_spots()
        return cluster_dist_opts

    def order_unit_distribution(self):
        """
        The idea is to strategically distribute the units on the map and thus expand evenly and quickly.
        To do this, we look at all the wood clusters on the map and evaluate them according to size, distance and
        position on the map. For example, a forest cluster of size 6 that is located on both the player's and the
        opponent's territory has a higher priority than a size 8 wood cluster located on the player territory.

        Further more we need to ensure that not all units are leaving one cluster for distribution reasons.
        """
        # get all distribution spots
        cluster_unit_mapping = {}
        cluster_distribution_options = []
        for cluster in self.cartographer.resource_clusters:
            if cluster.captured_by in ["p", "b"]:
                if len(cluster.attached_player_city_tiles_pos) >= 2:
                    # try to move to next cluster.
                    cluster_distribution_option = self.get_distribution_options_for_cluster(cluster=cluster)
                    cluster_distribution_option.trim_spots()
                    for unit in cluster_distribution_option.cluster_units:
                        cluster_unit_mapping[unit] = cluster_distribution_option
                    cluster_distribution_options.append(cluster_distribution_option)
        # Now find suitable units for these spots:
        distribution_spots = []

        for cluster in self.cartographer.resource_clusters:
            # we do not want to have multiple units distribute to the same cluster. This results in bad unit
            # distribution and possible bad defence.
            # --> one distribution for one cluster. (take the spot with the closest distance.
            spots_for_cluster = [spot for cluster_dist_opt in cluster_distribution_options for spot in
                                 cluster_dist_opt.distribution_spots if spot.other_cluster == cluster]
            if len(spots_for_cluster) == 1:
                distribution_spots.append(spots_for_cluster[0])
            elif len(spots_for_cluster) >= 1:
                spots_for_cluster = sorted(spots_for_cluster, key=lambda k: k.dist)
                distribution_spots.append(spots_for_cluster[0])

        # first we sort recording to dist and then priority
        distribution_spots = sorted(sorted(distribution_spots, key=lambda k: k.dist),
                                    key=lambda k: k.priority, reverse=True)
        for dist_spot in distribution_spots:
            # find closest unit that can make it.
            min_dist = np.inf
            closest_unit = None
            for unit in self.free_units:
                dist, pos = Cartographer.distance_to_cluster(pos=(unit.pos.x, unit.pos.y),
                                                             cluster=dist_spot.other_cluster)
                if self.get_unit_range(unit) >= dist:
                    if dist < min_dist:
                        min_dist = dist
                        if unit in cluster_unit_mapping.keys():
                            # check if unit is about to populate another wood cluster. This can be the case if two
                            # wood clusters are close together and one unit is part of both.
                            is_close_to_wood_cluster = False
                            wood_cluster = [c for c in self.cartographer.resource_clusters
                                            if ("w" in c.cluster_type) and (c != dist_spot.origin_cluster)
                                            and (len(c.attached_player_city_tiles_pos) < 2)
                                            and (c.size >= 2)]
                            for cluster in wood_cluster:
                                cluster_dist, _, _ = Cartographer.distance_cluster_to_cluster(
                                    cluster1=dist_spot.origin_cluster, cluster2=cluster)
                                if cluster_dist > 1:
                                    dist, _ = Cartographer.distance_to_cluster(pos=(unit.pos.x, unit.pos.y),
                                                                               cluster=cluster)
                                    if dist == 0:
                                        is_close_to_wood_cluster = True
                                        break
                            if (closest_unit is not None) and (closest_unit in cluster_unit_mapping.keys()):
                                # reset num_usable_units for the old units cluster
                                cluster_unit_mapping[closest_unit].num_usable_units += 1

                            if (cluster_unit_mapping[unit].num_usable_units > 0)\
                                    and (is_close_to_wood_cluster is False):
                                cluster_unit_mapping[unit].num_usable_units -= 1
                                closest_unit = unit
                        else:
                            # Here we need to check if this unit is close to another wood cluster and tries to capture
                            # it. But exclude the origin cluster that the unit was moving from.
                            # get closest cluster:
                            c_min_dist = np.inf
                            closest_dist_cluster = None
                            for cluster_dist_opt in cluster_distribution_options:
                                dist, _ = Cartographer.distance_to_cluster(pos=(unit.pos.x, unit.pos.y),
                                                                           cluster=cluster_dist_opt.cluster)
                                if dist < c_min_dist:
                                    c_min_dist = dist
                                    closest_dist_cluster = cluster_dist_opt

                            if closest_dist_cluster is not None:
                                closest_dist_cluster.num_usable_units -= 1

                            is_close_to_wood_cluster = False
                            wood_cluster = [c for c in self.cartographer.resource_clusters
                                            if ("w" in c.cluster_type) and (c != dist_spot.origin_cluster)
                                            and (len(c.attached_player_city_tiles_pos) < 2)
                                            and (c.size >= 2)]
                            for cluster in wood_cluster:
                                cluster_dist, _, _ = Cartographer.distance_cluster_to_cluster(
                                    cluster1=dist_spot.origin_cluster, cluster2=cluster)
                                if cluster_dist > 1:
                                    dist, _ = Cartographer.distance_to_cluster(pos=(unit.pos.x, unit.pos.y),
                                                                               cluster=cluster)
                                    if dist == 0:
                                        is_close_to_wood_cluster = True
                                        break
                            if is_close_to_wood_cluster is False:
                                if (closest_unit is not None) and (closest_unit in cluster_unit_mapping.keys()):
                                    # reset num_usable_units for the old units cluster
                                    cluster_unit_mapping[closest_unit].num_usable_units += 1
                                closest_unit = unit

            if closest_unit is not None:
                # check if the distribution spot is blocked by opponent city tile.
                dist, pos = Cartographer.distance_to_cluster(pos=(closest_unit.pos.x, closest_unit.pos.y),
                                                             cluster=dist_spot.other_cluster)
                if self.cartographer.city_map[pos[0]][pos[1]] == 2:
                    # tile is blocked: --> find closest free tile:
                    dist_to_closest_free_tile = np.inf
                    closest_free_tile_pos = None
                    for spot in dist_spot.other_cluster.surrounding_tiles_pos:
                        dist = Cartographer.distance_with_obstacles(obstacles_map=self.movement_officer.obstacles_map,
                                                                    origin=[closest_unit.pos.x, closest_unit.pos.y],
                                                                    destination=spot)
                        if dist < dist_to_closest_free_tile:
                            dist_to_closest_free_tile = dist
                            closest_free_tile_pos = spot
                    pos = closest_free_tile_pos
                # check if can harvest at distribution spot
                if (pos is not None) and (self.cartographer.harvesting_map[pos[0]][pos[1]].fuel_value_per_turn < 20):
                    # spot has no harvesting value --> find closest tile with positive harvesting value
                    # This is the case if coal or uranium is part of the cluster and it is not researched jet
                    dist_to_closest_free_tile = np.inf
                    closest_harvesting_tile_pos = None
                    for spot in dist_spot.other_cluster.surrounding_tiles_pos:
                        if self.cartographer.harvesting_map[spot[0]][spot[1]].fuel_value_per_turn >= 20:
                            dist = Cartographer.distance_with_obstacles(
                                obstacles_map=self.movement_officer.obstacles_map,
                                origin=[closest_unit.pos.x, closest_unit.pos.y], destination=spot)
                            if dist < dist_to_closest_free_tile:
                                dist_to_closest_free_tile = dist
                                closest_harvesting_tile_pos = spot
                    pos = closest_harvesting_tile_pos
                if pos is not None:
                    self.assign_order_to_unit(unit=closest_unit, position_tuple=pos,
                                              order_type=OrderType.Distribution)

    def order_resource_defense(self):
        """
        Simply moves units to possible expansion spots to block them for enemy players. Especially useful for player
        wood expansions.
        Note: Mostly redundant due to our new blocking orders.
        :return: Simply assigns orders.
        """
        clusters_to_defence = [cluster for cluster in self.cartographer.resource_clusters
                               if cluster.captured_by in ["p", "b"]]

        clusters_to_defence = sorted(clusters_to_defence, key=lambda k: k.min_dist_to_opponent_unit)

        defence_positions = set()
        for cluster in clusters_to_defence:
            if (cluster.captured_by == "p") or (cluster.captured_by == "b"):
                for pos in cluster.unguarded_expansion_pos:
                    defence_positions.add(pos)

        # check for free units that are already on a defence position.
        for unit in self.free_units:
            if (unit.pos.x, unit.pos.y) in defence_positions:
                self.assign_order_to_unit(unit=unit, position_tuple=(unit.pos.x, unit.pos.y),
                                          order_type=OrderType.ClusterDefence)
                defence_positions.remove((unit.pos.x, unit.pos.y))

        # find closes free unit for each spot:
        for pos in defence_positions:
            # check if pos can be defended (it has a positive harvesting value)
            if self.cartographer.harvesting_map[pos[0]][pos[1]].collection_amount_per_turn > 4:
                closest_dist = np.inf
                closest_unit = None
                for unit in self.free_units:
                    dist = Cartographer.distance(origin=[unit.pos.x, unit.pos.y], destination=pos)
                    if dist < closest_dist:
                        closest_dist = dist
                        closest_unit = unit
                if closest_unit is not None:
                    unit_will_make_it = False
                    if self.day:
                        unit_range = self.get_unit_range(closest_unit)
                        if unit_range >= closest_dist:
                            unit_will_make_it = True
                    else:
                        # move at night
                        if closest_dist == 1:
                            # unit is next to spot: (check if unit can survive at pos)
                            collection_amount = self.cartographer.harvesting_map[pos[0]][
                                pos[1]].collection_amount_per_turn
                            if collection_amount > 4:
                                unit_will_make_it = True
                        else:
                            # check if default direction leads to a farming cell.
                            cell = self.cartographer.map.get_cell(pos[0], pos[1])
                            direct_direction = closest_unit.pos.direction_to(cell.pos)
                            new_pos = closest_unit.pos.translate(direct_direction, 1)
                            collection_amount = self.cartographer.harvesting_map[new_pos.x][new_pos.y].\
                                collection_amount_per_turn
                            if collection_amount > 4:
                                unit_will_make_it = True
                    if unit_will_make_it:
                        self.assign_order_to_unit(unit=closest_unit, position_tuple=pos,
                                                  order_type=OrderType.ClusterDefence)

    def order_unit_blocking(self):
        """
        Orders the closest unit to block en opponent unit if it reaches minimum distance for blocking.
        :return:
        """
        # for now we only block units if our our cluster is in danger.
        min_dist_for_blocking = {"S": 3, "M": 3, "L": 6, "XL": 6}
        clusters_to_defence = [rc for rc in self.cartographer.resource_clusters if (rc.captured_by == "p")
                               and (rc.min_dist_to_opponent_unit <= min_dist_for_blocking[self.cartographer.map_size])]

        def unit_is_allowed_to_block(blocker_unit):
            """
            Checks if a unit is allowed to block other units.
            1) We need to prevent all units from leaving one cluster
            2) If we have only one unit at a specific cluster this unit can't block. --> this unit needs to build!
            3) If a unit is Distributing to an enemy cluster it is allowed to block incoming units.
            """
            allowed_to_block = False
            unit_clusters = []
            for _cluster in self.cartographer.resource_clusters:
                if _cluster.unit_is_in_cluster(unit=blocker_unit):
                    # units can be part of two clusters!
                    unit_clusters.append(_cluster)
            if len(unit_clusters) == 0:
                # unit is part of no cluster
                allowed_to_block = True
            elif len(unit_clusters) == 1:
                # unit is part of one cluster
                unit_cluster = unit_clusters[0]
                if unit_cluster.num_surrounding_units > (unit_cluster.num_send_blockers + 1):
                    # at least one unit remains in cluster.
                    allowed_to_block = True
                    unit_cluster.num_send_blockers += 1
            else:
                # unit is part of more thn one cluster
                allowed_to_block = True
                for uc in unit_clusters:
                    # leave no cluster behind:
                    if uc.num_surrounding_units <= (uc.num_send_blockers + 1):
                        # at least one unit remains in cluster.
                        allowed_to_block = False

                if allowed_to_block is True:
                    for uc in unit_clusters:
                        uc.num_send_blockers += 1

            return allowed_to_block

        for cluster in clusters_to_defence:
            cluster_units = set()
            # exclude o_units that are part of another cluster. We only block units that are coming to our cluster
            other_clusters = [oc for oc in self.cartographer.resource_clusters if oc != cluster]
            for o_unit in cluster.close_opponent_units:
                # check if opponent unit is part of another cluster:
                for oc in other_clusters:
                    if oc.unit_is_in_cluster(unit=o_unit):
                        cluster_units.add(o_unit)
            possible_invaders = [o_u for o_u in cluster.close_opponent_units if o_u not in cluster_units]

            for o_unit in possible_invaders:
                o_unit_dist, cluster_arrival_tile = Cartographer.distance_to_cluster(pos=(o_unit.pos.x, o_unit.pos.y),
                                                                                     cluster=cluster)
                o_unit_cell = self.cartographer.map.get_cell(o_unit.pos.x, o_unit.pos.y)
                arrival_cell = self.cartographer.map.get_cell(cluster_arrival_tile[0], cluster_arrival_tile[1])
                direction = o_unit_cell.pos.direction_to(arrival_cell.pos)
                adjacent_pos = o_unit_cell.pos.translate(direction, 1)
                # axis:
                if np.abs(o_unit.pos.x - cluster_arrival_tile[0]) >= np.abs(o_unit.pos.y - cluster_arrival_tile[1]):
                    moving_axis = "x"
                else:
                    moving_axis = "y"

                # try to find closest unit to block:
                min_dist = np.inf
                closest_unit = None
                for unit in self.free_units:
                    dist_to_o_unit = Cartographer.distance(origin=(unit.pos.x, unit.pos.y),
                                                           destination=(o_unit.pos.x, o_unit.pos.y))
                    dist_to_arrival_tile = Cartographer.distance(origin=(unit.pos.x, unit.pos.y),
                                                                 destination=(arrival_cell.pos.x, arrival_cell.pos.y))

                    if dist_to_arrival_tile < o_unit_dist:
                        if dist_to_o_unit < min_dist:
                            # check if unit is allowed to block
                            if unit_is_allowed_to_block(blocker_unit=unit):
                                min_dist = dist_to_o_unit
                                closest_unit = unit
                    elif dist_to_arrival_tile == o_unit_dist:
                        if (dist_to_o_unit < min_dist) and (unit.cooldown <= o_unit.cooldown):
                            # check if unit is allowed to block
                            if unit_is_allowed_to_block(blocker_unit=unit):
                                min_dist = dist_to_o_unit
                                closest_unit = unit

                if closest_unit is not None:
                    if min_dist == 1:
                        blocking_pos = (closest_unit.pos.x, closest_unit.pos.y)
                    else:
                        if moving_axis == "y":
                            if closest_unit.pos.x != o_unit.pos.x:
                                blocking_pos = (o_unit.pos.x, closest_unit.pos.y)
                            else:
                                blocking_pos = (adjacent_pos.x, adjacent_pos.y)
                        else:
                            if closest_unit.pos.y != o_unit.pos.y:
                                blocking_pos = (closest_unit.pos.x, o_unit.pos.y)
                            else:
                                blocking_pos = (adjacent_pos.x, adjacent_pos.y)
                    self.assign_order_to_unit(unit=closest_unit, position_tuple=blocking_pos,
                                              order_type=OrderType.Blocking)

    def get_save_spots(self):
        """
        Builds a set of save spots. A Save spot is every tile on which a unit will survive the following night.
        This could be a city which will survive the following night or any other farming location.
        Note: Not all harvesting values are save. City tiles on a given harvesting spot can be dangerous.
        :return: set() of tuples
        """
        save_spots = set()
        for x in range(self.cartographer.width):
            for y in range(self.cartographer.height):
                if self.cartographer.city_map[x][y] == 0:
                    # no city tile
                    harvesting_tile = self.cartographer.harvesting_map[x][y]
                    if harvesting_tile.collection_amount_per_turn > 0 and self.cartographer.unit_map[x][y] < 2:
                        # no enemy is standing on this tile
                        save_spots.add(SaveSpot(pos=(x, y), is_city=False))
                elif self.cartographer.city_map[x][y] == 1:
                    # player city tile
                    city_id = self.cartographer.map.get_cell(x, y).citytile.cityid
                    district_mayor = self.city_council.get_district_mayor_by_id(city_id=city_id)
                    if district_mayor.survives_next_night:
                        save_spots.add(SaveSpot(pos=(x, y), is_city=True))
                else:
                    # opponent city tile. --> no save spot
                    pass
        return save_spots

    def order_save_spots(self):
        """
        Order all self.free_units to move to save location to survive the night.
        :return:
        """
        save_spots = self.get_save_spots()
        save_spot_order = []
        """
        Prefer save spots that are not wood harvesting spots: (We do not want to harvest wood if its not ordered)
        """
        priority_1_save_spots = []
        for spot in save_spots:
            if spot.is_city:
                if self.cartographer.harvesting_map[spot.pos[0]][spot.pos[1]].num_wood == 0:
                    # save spot without wood harvesting
                    priority_1_save_spots.append(spot)
            else:
                priority_1_save_spots.append(spot)

        priority_2_save_spots = [s for s in save_spots if s not in priority_1_save_spots]

        def save_spot_distribution(priority_save_spot: list):
            for unit in self.free_units:
                unit_cargo = 100 - unit.get_cargo_space_left()
                unit_will_die = unit_cargo < 40
                spot_positions = [spot.pos for spot in priority_save_spot]
                if (len(priority_save_spot) > 0) and unit_will_die:
                    if (unit.pos.x, unit.pos.y) not in spot_positions:
                        # find closes save spot for unit.
                        min_dist = np.inf
                        closest_spot = None
                        for spot in priority_save_spot:
                            dist = self.cartographer.distance(origin=(unit.pos.x, unit.pos.y), destination=spot.pos)
                            if dist < min_dist:
                                min_dist = dist
                                closest_spot = spot
                            elif (dist == min_dist) and (not spot.is_city):
                                # prefer non city save spots
                                min_dist = dist
                                closest_spot = spot

                        if closest_spot is not None:
                            unit_range = self.get_unit_range(unit=unit)
                            # in 6 steps a unit can move 3 tiles. (minimum)
                            if min_dist <= unit_range:
                                save_spot_order.append([unit, closest_spot])
                                if not closest_spot.is_city:
                                    # city save spots can host any number of units but other save spots only one.
                                    priority_save_spot.remove(closest_spot)
                    else:
                        # unit is standing on save spot.
                        if len(priority_save_spot) > 0:
                            closest_spot = [spot for spot in priority_save_spot
                                            if spot.pos == (unit.pos.x, unit.pos.y)][0]
                            save_spot_order.append([unit, closest_spot])
                            if not closest_spot.is_city:
                                # city save spots can host any number of units but other save spots only one.
                                priority_save_spot.remove(closest_spot)

        # fist priority 1 and then priority 2 save spots
        save_spot_distribution(priority_save_spot=priority_1_save_spots)
        save_spot_distribution(priority_save_spot=priority_2_save_spots)

        for order in save_spot_order:
            self.assign_order_to_unit(unit=order[0], position_tuple=order[1].pos,
                                      order_type=OrderType.SaveSpot)

    def order_city_support(self):
        """
        Orders units for harvesting in the city. This is not the most efficient way to harvest in most cases, but the
        units will not block other units if they are standing on a city tile, so it can be beneficial.
        """
        def find_closes_free_unit_for_spot(district_harvesting_spot):
            """
            Finds the closest unit for given district_harvesting_spot.
            :param district_harvesting_spot: DistrictHarvestingSpot
            :return: closest_unit and its distance to the gives DistrictHarvestingSpot
            """
            m_dist = np.inf
            c_unit = None
            # only free units with less then 50 wood. (We do not want to wast wood.
            for unit in self.free_units:
                # if unit.cargo.wood < 50:
                dist = self.cartographer.distance(origin=district_harvesting_spot.pos,
                                                  destination=(unit.pos.x, unit.pos.y))
                if dist < m_dist:
                    m_dist = dist
                    c_unit = unit
                if m_dist == 0:
                    break
            return c_unit, m_dist

        for dist_mayor in self.city_council.district_mayors:
            if not dist_mayor.survives_next_night:
                for dist_ha_spot in dist_mayor.district_harvesting_spots:
                    if dist_ha_spot.harvesting_value > 27:
                        closest_unit, min_dist = find_closes_free_unit_for_spot(district_harvesting_spot=dist_ha_spot)
                        if closest_unit is not None and (min_dist < self.get_unit_range(unit=closest_unit)):
                            self.assign_order_to_unit(unit=closest_unit, position_tuple=dist_ha_spot.pos,
                                                      order_type=OrderType.CitySupport)

            else:
                # city will survive next night:
                for dist_ha_spot in dist_mayor.district_harvesting_spots:
                    if dist_ha_spot.includes_coal or dist_ha_spot.includes_uranium:
                        closest_unit, min_dist = find_closes_free_unit_for_spot(district_harvesting_spot=dist_ha_spot)
                        if closest_unit is not None and (min_dist < self.get_unit_range(unit=closest_unit)):
                            self.assign_order_to_unit(unit=closest_unit, position_tuple=dist_ha_spot.pos,
                                                      order_type=OrderType.CitySupport)

    def order_harvesting(self, units=None):
        """
        Orders free units or given units to harvest.
        :param units:
        """
        if units is None:
            units = self.free_units

        def get_biggest_priority_city(unit):
            unit_day_range = math.floor(self.steps_until_night / 2)
            # find district in need with the highest priority within unit range
            max_priority = 0
            dist_to_max = np.inf
            max_priority_pos = None
            for district_mayor in district_mayors_for_farming:
                if district_mayor.harvesting_priority > 0:
                    dist, closest_tile_pos = Cartographer.distance_to_district(pos=(unit.pos.x, unit.pos.y),
                                                                               district_mayor=district_mayor)
                    if dist < unit_day_range:
                        """
                        Note: Unit range might be very high since the cargo is full.
                        """
                        if (district_mayor.harvesting_priority > max_priority) or \
                                ((district_mayor.harvesting_priority == max_priority) and (dist < dist_to_max)):
                            max_priority = district_mayor.harvesting_priority
                            dist_to_max = dist
                            max_priority_pos = closest_tile_pos
            return dist_to_max, max_priority_pos, max_priority

        # get all cities that need farming
        harvesting_orders = []
        district_mayors_for_farming = [district_mayor for district_mayor in self.city_council.district_mayors
                                       if not district_mayor.survives_all_nights]

        if self.night_steps_left < 12:
            # we harvest everything in the last day cycle:
            free_harvesting_positions = self.harvesting_officer.free_harvesting_positions
        else:
            free_harvesting_positions = self.harvesting_officer.strategic_harvesting_positions

        for unit in units:
            distance_to_city_tile, tile_pos, priority = get_biggest_priority_city(unit=unit)
            unit_day_range = math.floor(self.steps_until_night / 2)
            if (unit.get_cargo_space_left() == 0) or ((unit.get_cargo_space_left() <= 50) and
                                                      distance_to_city_tile < unit_day_range):
                # go to closest city in need.
                if tile_pos is not None:
                    harvesting_orders.append([unit, tile_pos, OrderType.Harvest_Return])

            else:
                unit_range = self.get_unit_range(unit=unit)
                # if not on harvesting spot move to closes spot.
                fuel_value_at_pos = self.cartographer.harvesting_map[unit.pos.x][unit.pos.y].fuel_value_per_turn
                if fuel_value_at_pos == 0:
                    # unit is not on a harvesting location --> find closest harvesting location:
                    min_dist = np.inf
                    closest_free_harvesting_pos = None
                    for free_pos in free_harvesting_positions:
                        dist = self.cartographer.distance(origin=[unit.pos.x, unit.pos.y],
                                                          destination=[free_pos[0], free_pos[1]])
                        if dist < min_dist:
                            min_dist = dist
                            closest_free_harvesting_pos = free_pos
                    if (closest_free_harvesting_pos is not None) and (unit_range >= min_dist):
                        # remove new position from free_harvesting_positions
                        free_harvesting_positions.remove(closest_free_harvesting_pos)
                        harvesting_orders.append([unit, closest_free_harvesting_pos, OrderType.Harvest_Go])
                else:
                    # look for better spot around.
                    directions = [[0, 1], [1, 0], [0, -1], [-1, 0]]
                    for d in directions:
                        new_x = unit.pos.x + d[0]
                        new_y = unit.pos.y + d[1]
                        max_fuel_value = 0
                        better_harvesting_pos = None
                        if (0 <= new_x < self.cartographer.width) and (0 <= new_y < self.cartographer.height):
                            fuel_value = self.cartographer.harvesting_map[new_x][new_y].fuel_value_per_turn
                            if ((new_x, new_y) in free_harvesting_positions) and fuel_value > max_fuel_value:
                                max_fuel_value = fuel_value
                                better_harvesting_pos = (new_x, new_y)
                        if (better_harvesting_pos is not None) and (max_fuel_value > fuel_value_at_pos):
                            # add old unit position to free_harvesting_positions and remove new position
                            free_harvesting_positions.add((unit.pos.x, unit.pos.y))
                            free_harvesting_positions.remove(better_harvesting_pos)
                            harvesting_orders.append([unit, better_harvesting_pos, OrderType.Harvest_Go])

        for order in harvesting_orders:
            self.assign_order_to_unit(unit=order[0], position_tuple=order[1], order_type=order[2])

    def order_expansions(self):
        """
        Order expansions until no worker is free or no more spots are found.
        Runs a maximum of 10 cycles.
        :return:
        """
        counter = 1
        order_expansions = True
        full_cargo_units = [unit for unit in self.free_units if unit.get_cargo_space_left() == 0]
        if self.strategy_information.player_research_status > 1:
            self.order_closest_expansion_spots(units=full_cargo_units, max_number_per_unit=1)

        while order_expansions:
            counter += 1
            fastest_spots = self.order_fastest_expansion_spots()
            self.expansion_officer.update_expansion_maps(fastest_spots)
            for spot in fastest_spots:
                self.assign_order_to_unit(unit=spot.unit, position_tuple=spot.harvesting_pos,
                                          order_type=OrderType.Expansion, additional_information=spot)
            if (len(self.free_units) == 0) or (self.expansion_officer.get_number_of_free_expansion_spots() == 0)\
                    or counter == 10:
                order_expansions = False

    def order_closest_expansion_spots(self, units, max_number_per_unit=1):
        """
        Only for units with full cargo
        """
        for unit in units:
            unit_expansions = self.expansion_officer.find_strategic_expansions(unit=unit,
                                                                               max_number=max_number_per_unit)
            if len(unit_expansions) > 0:
                self.expansion_officer.update_expansion_maps(unit_expansions)
                self.assign_order_to_unit(unit=unit_expansions[0].unit, position_tuple=unit_expansions[0].harvesting_pos,
                                          order_type=OrderType.Expansion, additional_information=unit_expansions[0])

    def order_fastest_expansion_spots(self, max_number_per_unit=5):
        """
        Finds the fastest 5 expansion spots for each unit. Then we find the fastest unit for each expansion spot and
        therefor fastest expansion overall.
        Note: Lot of space for improvement. (Unit movement and so on ...
        :param max_number_per_unit:
        :return:
        """

        def get_closest_spot_to_opponent_unit(input_spots):
            closest_dist_to_enemy = np.inf
            best_spot = None
            for spot in input_spots:
                for unit in self.cartographer.opponent.units:
                    dist = Cartographer.distance(origin=spot.spot_pos,
                                                 destination=(unit.pos.x, unit.pos.y))
                    if dist < closest_dist_to_enemy:
                        closest_dist_to_enemy = dist
                        best_spot = spot
            return best_spot

        def get_closest_spot_to_next_expansion(input_spots, distribution_option):
            """
            Old (Not uses for now)
            """
            best_distribution_option = distribution_option.distribution_spots[0]
            closest_dist_to_distribution_spot = np.inf
            best_spots = []
            for spot in input_spots:
                dist = Cartographer.distance(
                    origin=spot.spot_pos, destination=(best_distribution_option.origin_tile_pos[0],
                                                       best_distribution_option.origin_tile_pos[1]))
                if dist < closest_dist_to_distribution_spot:
                    closest_dist_to_distribution_spot = dist
                    best_spots = [spot]
                elif dist == closest_dist_to_distribution_spot:
                    best_spots.append(spot)

            closest_spot_to_opponent = get_closest_spot_to_opponent_unit(input_spots)
            if closest_spot_to_opponent in best_spots:
                best_spot = closest_spot_to_opponent
            else:
                best_spot = best_spots[0]

            return best_spot

        expansion_options = []
        for unit in self.free_units:
            unit_expansions = self.expansion_officer.find_strategic_expansions(unit=unit,
                                                                               max_number=max_number_per_unit)
            expansion_options += unit_expansions

        # find best unit to build expansion.
        best_expansion_options = []
        unique_expansion_ids = set([ex_spot.id for ex_spot in expansion_options])
        for exp_id in unique_expansion_ids:
            spots_with_id = [spot for spot in expansion_options if spot.id == exp_id]
            min_time_to_build = min(spot.time_to_build for spot in spots_with_id)
            spots_with_fastest_building_time = [spot for spot in spots_with_id if
                                                spot.time_to_build == min_time_to_build]
            if len(spots_with_fastest_building_time) > 1:
                best_expansion_options += spots_with_fastest_building_time
            else:
                best_expansion_options.append(spots_with_fastest_building_time[0])

        # Now we have the best units for each expansion. Now we need to identify the best expansions since we probable
        # do not have the same amount of units as expansions.
        final_spots = []
        units = set([ex_spot.unit for ex_spot in best_expansion_options])
        for unit in units:
            # all spots where this specific unit is the fastest builder
            unit_spots = [spot for spot in best_expansion_options if unit == spot.unit]
            if len(unit_spots) > 0:
                # some unity may not have a fastest expansion spot since another unit took it.
                min_time_to_build = min(spot.time_to_build for spot in unit_spots) + 1  # min time + 1

                unit_spots_with_min_time = [spot for spot in unit_spots if spot.time_to_build <= min_time_to_build]

                # get unit_cluster:
                unit_clusters = set()
                for cluster in self.cartographer.resource_clusters:
                    dist, _ = Cartographer.distance_to_cluster(pos=(unit.pos.x, unit.pos.y), cluster=cluster)
                    if dist == 0:
                        unit_clusters.add(cluster)
                """
                NOTE: Here we decide how we choose between the best spots for a unit.
                      We prefer spots that are closer to enemy spots and sometime spots that are closer to next 
                      cluster positions for faster expansions.
                """
                if (len(unit_spots_with_min_time) > 1) and (min_time_to_build > 0):
                    if self.strategy_information.num_player_city_tiles == 1:
                        # get closest cluster
                        unit_cluster = None
                        if len(unit_clusters) > 0:
                            # choose the biggest wood cluster as unit cluster.
                            biggest_wood_cluster = None
                            max_num_wood_tiles = 0
                            for uc in unit_clusters:
                                if uc.num_wood_tiles > max_num_wood_tiles:
                                    max_num_wood_tiles = uc.num_wood_tiles
                                    biggest_wood_cluster = uc
                            if biggest_wood_cluster is not None:
                                unit_cluster = biggest_wood_cluster
                            else:
                                # one at random (shot not be possible i guess...)
                                unit_cluster = unit_clusters.pop()

                        if unit_cluster is not None:
                            distribution_option = self.get_distribution_options_for_cluster(cluster=unit_cluster)
                            if len(distribution_option.distribution_spots) > 0:
                                best_distribution_option = distribution_option.distribution_spots[0]
                                closest_dist_to_distribution_spot = np.inf
                                best_spots = []
                                for spot in unit_spots_with_min_time:
                                    dist = Cartographer.distance(
                                        origin=spot.spot_pos, destination=(best_distribution_option.origin_tile_pos[0],
                                                                           best_distribution_option.origin_tile_pos[1]))
                                    if dist < closest_dist_to_distribution_spot:
                                        closest_dist_to_distribution_spot = dist
                                        best_spots = [spot]
                                    elif dist == closest_dist_to_distribution_spot:
                                        best_spots.append(spot)
                                # check if closest spot is paar of min distance spots:
                                closest_spot_to_opponent = get_closest_spot_to_opponent_unit(unit_spots_with_min_time)
                                if closest_spot_to_opponent in best_spots:
                                    best_spot = closest_spot_to_opponent
                                else:
                                    best_spot = best_spots[0]
                            else:
                                # choose spot that is the closest to enemy unit:
                                best_spot = get_closest_spot_to_opponent_unit(unit_spots_with_min_time)
                        else:
                            # choose spot that is the closest to enemy unit:
                            best_spot = get_closest_spot_to_opponent_unit(unit_spots_with_min_time)
                    else:
                        # We have more then one captures cluster
                        # choose spot that is the closest to enemy unit:
                        best_spot = get_closest_spot_to_opponent_unit(unit_spots_with_min_time)
                else:
                    # only one spot, so len(unit_spots_with_min_time) = 1
                    if len(unit_spots_with_min_time) > 1:
                        print("WARNING: something went wrong for distribution spots. (General)")
                    best_spot = unit_spots_with_min_time[0]

                if best_spot is not None:
                    # check if unit can go there
                    unit_will_make_it = False
                    if self.day:
                        unit_range = self.get_unit_range(unit=best_spot.unit)
                        if unit_range >= best_spot.dist:
                            unit_will_make_it = True
                    else:
                        # move at night
                        if best_spot.dist == 1:
                            # unit is next to spot: (check if unit can survive at pos)
                            collection_amount = self.cartographer.harvesting_map[best_spot.spot_pos[0]][
                                best_spot.spot_pos[1]].collection_amount_per_turn
                            if collection_amount > 4:
                                unit_will_make_it = True
                        else:
                            # check if default direction leads to a farming cell.
                            cell = self.cartographer.map.get_cell(best_spot.spot_pos[0], best_spot.spot_pos[1])
                            direct_direction = best_spot.unit.pos.direction_to(cell.pos)
                            new_pos = best_spot.unit.pos.translate(direct_direction, 1)
                            collection_amount = self.cartographer.harvesting_map[new_pos.x][new_pos.y]. \
                                collection_amount_per_turn
                            if collection_amount > 4:
                                unit_will_make_it = True
                    if unit_will_make_it:
                        best_expansion_options = [exp_spot for exp_spot in best_expansion_options
                                                  if exp_spot.id != best_spot.id]
                        final_spots.append(best_spot)
        return final_spots

    def get_unit_range(self, unit):
        """
        Calculates the unit range for a given unit.
        :param unit: lux unit
        """
        cargo = 100 - unit.get_cargo_space_left()
        if self.day:
            unit_range = math.floor(self.steps_until_night / 2) + math.floor(cargo / 16)
            # 16 = 4 * 4 (4 is cool down at night and 4 fuel per step --> 16 fuel per moved tile
        else:
            # night:
            unit_range = math.floor(cargo / 16)
        return unit_range

    def get_day_night_information(self, night_steps_left):
        """
        First of all we need to know in which state we are. In terms of night and day shift.
        There are 30 day steps followed by 10 night steps.
        """
        self.steps_until_night = 30 - self.cartographer.observation["step"] % 40
        if self.steps_until_night > 0:
            self.day = True
            self.steps_until_day = 0
        else:
            self.day = False

        if not self.day:
            night_steps_left -= 1
            self.steps_until_day = self.steps_until_night + 10
        self.night_steps_left = night_steps_left
        return night_steps_left

    def build_strategy_information(self):
        """
        Builds strategy information.
        """
        # Get city information:
        num_player_city_tiles = 0
        num_player_save_city_tiles = 0
        for dist_mayor in self.city_council.district_mayors:
            if dist_mayor.survives_all_nights:
                num_player_save_city_tiles += dist_mayor.size
            num_player_city_tiles += dist_mayor.size

        num_opponent_city_tiles = 0
        num_opponent_save_city_tiles = 0
        for city in self.cartographer.opponent.cities.values():
            city_size = len(city.citytiles)
            survives_all_nights = bool((city.get_light_upkeep() * self.night_steps_left) < city.fuel)
            if survives_all_nights:
                num_opponent_save_city_tiles += city_size
            num_opponent_city_tiles += city_size

        # Get research information:
        if self.cartographer.player.researched_uranium():
            player_research_status = 2
        elif self.cartographer.player.researched_coal():
            player_research_status = 1
        else:
            player_research_status = 0

        if self.cartographer.opponent.researched_uranium():
            opponent_research_status = 2
        elif self.cartographer.opponent.researched_coal():
            opponent_research_status = 1
        else:
            opponent_research_status = 0
        player_research_points = self.cartographer.player.research_points
        opponent_research_points = self.cartographer.opponent.research_points

        # Get map resource information (With Player Research):
        amount_of_wood_fuel = 0
        amount_of_coal_fuel = 0
        amount_of_uranium_fuel = 0

        for cluster in self.cartographer.resource_clusters:
            for resource_tile in cluster.resource_tiles:
                if resource_tile.resource_type == "w":
                    amount_of_wood_fuel += resource_tile.fuel_amount
                elif resource_tile.resource_type == "c":
                    amount_of_coal_fuel += resource_tile.fuel_amount
                elif resource_tile.resource_type == "u":
                    amount_of_uranium_fuel += resource_tile.fuel_amount

        step = self.cartographer.observation["step"]

        # get num player and opponent clusters:
        num_player_cluster = 0
        num_opponent_cluster = 0
        for cluster in self.cartographer.resource_clusters:
            if cluster.captured_by == "p":
                num_player_cluster += 1
            elif cluster.captured_by == "o":
                num_opponent_cluster += 1
            elif cluster.captured_by == "b":
                num_player_cluster += 1
                num_opponent_cluster += 1

        """
        Idea: We could think about the general resource information an the map. Independent of research.
              And the amount of cluster and there sice could also be key. 
        """

        strategy_information = StrategyInformation(num_player_city_tiles=num_player_city_tiles,
                                                   num_player_save_city_tiles=num_player_save_city_tiles,
                                                   num_opponent_city_tiles=num_opponent_city_tiles,
                                                   num_opponent_save_city_tiles=num_opponent_save_city_tiles,
                                                   player_research_status=player_research_status,
                                                   opponent_research_status=opponent_research_status,
                                                   player_research_points=player_research_points,
                                                   opponent_research_points=opponent_research_points,
                                                   amount_of_wood_fuel=amount_of_wood_fuel,
                                                   amount_of_coal_fuel=amount_of_coal_fuel,
                                                   amount_of_uranium_fuel=amount_of_uranium_fuel, step=step,
                                                   map_size=self.cartographer.map_size,
                                                   num_player_cluster=num_player_cluster,
                                                   num_opponent_cluster=num_opponent_cluster)
        self.strategy_information = strategy_information


class OrderType(Enum):
    Expansion = "Expansion"
    Harvest_Go = "Harvest_Go"
    Harvest_Return = "Harvest_Return"
    CitySupport = "CitySupport"
    SaveSpot = "SaveSpot"
    ClusterDefence = "ClusterDefence"
    Distribution = "Distribution"
    Blocking = "Blocking"


class Order:
    def __init__(self, order_type: OrderType, unit, pos, additional_information=None):
        """
        :param order_type: OrderType
        :param unit: lux unit
        :param pos: pos tuple
        """
        self.order_type = order_type
        self.unit = unit
        self.pos = pos
        self.additional_information = additional_information
        self.dist = Cartographer.distance(origin=(unit.pos.x, unit.pos.y), destination=pos)


class SaveSpot:
    def __init__(self, pos, is_city):
        self.pos = pos
        self.is_city = is_city


class StrategyInformation:
    """
    Holds strategic information for one step.
    """
    def __init__(self, num_player_city_tiles, num_player_save_city_tiles, num_opponent_city_tiles, num_player_cluster,
                 num_opponent_cluster,
                 num_opponent_save_city_tiles, player_research_status, opponent_research_status, player_research_points,
                 opponent_research_points, amount_of_wood_fuel, amount_of_coal_fuel, amount_of_uranium_fuel, step,
                 map_size):
        self.num_player_city_tiles = num_player_city_tiles
        self.num_player_save_city_tiles = num_player_save_city_tiles
        self.num_player_cluster = num_player_cluster
        self.num_opponent_city_tiles = num_opponent_city_tiles
        self.num_opponent_save_city_tiles = num_opponent_save_city_tiles
        self.num_opponent_cluster = num_opponent_cluster
        self.player_research_status = player_research_status
        self.opponent_research_status = opponent_research_status
        self.player_research_points = player_research_points
        self.opponent_research_points = opponent_research_points
        self.amount_of_wood_fuel = amount_of_wood_fuel
        self.amount_of_coal_fuel = amount_of_coal_fuel
        self.amount_of_uranium_fuel = amount_of_uranium_fuel
        self.step = step
        self.map_size = map_size

    def show(self):
        print(50 * "-")
        print(f"Step: {self.step}  map_size: {self.map_size}")
        print(f"Fuel left: wood: {self.amount_of_wood_fuel}  |  coal: {self.amount_of_coal_fuel}"
              f"  |  uranium: {self.amount_of_uranium_fuel} ")
        print("           Player  |  Opponent")
        print(f"city_tiles      {self.num_player_city_tiles}  |  {self.num_opponent_city_tiles}")
        print(f"save_tiles      {self.num_player_save_city_tiles}  |  {self.num_opponent_save_city_tiles}")
        print(f"research state  {self.player_research_status}  |  {self.player_research_status}")
        print(f"research points {self.player_research_points}  |  {self.opponent_research_points}")
        print(f"num_player_cluster: {self.num_player_cluster}  |  {self.num_opponent_cluster}")
        print(50 * "-")


class DistributionSpot:
    def __init__(self, origin_cluster, other_cluster, dist, origin_tile_pos, destination_tile_pos):
        self.origin_cluster = origin_cluster
        self.other_cluster = other_cluster
        self.dist = dist
        self.origin_tile_pos = origin_tile_pos
        self.destination_tile_pos = destination_tile_pos
        self.priority = 0


class ClusterDistributionOptions:
    def __init__(self, cluster, units, strat_info, city_council):
        self.cluster = cluster
        self.cluster_units = []
        self.strategic_information = strat_info
        for unit in units:
            dist, _ = Cartographer.distance_to_cluster(pos=(unit.pos.x, unit.pos.y), cluster=cluster)
            if dist == 0:
                self.cluster_units.append(unit)
        self.distribution_spots = []
        # set num of units that could be send away
        """
        Note: If no enemy is around this number is all but one. If otherwise an enemy is around we need to make sure 
        that we can protect the cluster.
        --> We need one unit for each possible expansion spot and one for each city tiles that will not survive the
        next night.
        """
        self.max_num_distributions = 0
        if (cluster.captured_by == "b") or (cluster.captured_by == "p" and cluster.min_dist_to_opponent_unit < 6):
            # we do not want to lose captured clusters
            if strat_info.num_player_cluster == 1:
                if (len(cluster.attached_player_city_tiles_pos) == 2) and (cluster.num_surrounding_units == 2):
                    self.max_num_distributions = 1
                elif (len(cluster.attached_player_city_tiles_pos) == 3) and (cluster.num_surrounding_units > 2):
                    self.max_num_distributions = 2
                elif (len(cluster.attached_player_city_tiles_pos) == 4) and (cluster.num_surrounding_units > 2):
                    self.max_num_distributions = 2
            else:
                num_city_tiles_to_support = len(cluster.attached_player_city_tiles_pos)
                # exclude those that will survive the next night.
                for tile_pos in cluster.attached_player_city_tiles_pos:
                    district_major = city_council.get_district_mayor_by_pos(pos=tile_pos)
                    if district_major.survives_next_night:
                        num_city_tiles_to_support -= 1

                num_support_tiles = num_city_tiles_to_support + cluster.num_possible_expansions
                if cluster.num_surrounding_units > num_support_tiles:
                    self.max_num_distributions = cluster.num_surrounding_units - num_support_tiles
                else:
                    if cluster.num_surrounding_units >= (cluster.num_surrounding_opponent_units + 2):
                        self.max_num_distributions = cluster.num_surrounding_units - \
                                                     (cluster.num_surrounding_opponent_units + 2)
        else:
            if (len(cluster.attached_player_city_tiles_pos) == 2) and (cluster.num_surrounding_units == 2):
                self.max_num_distributions = 1
            elif (len(cluster.attached_player_city_tiles_pos) == 3) and (cluster.num_surrounding_units > 2):
                self.max_num_distributions = 2
            elif (len(cluster.attached_player_city_tiles_pos) >= 3) and (cluster.num_surrounding_units > 2):
                self.max_num_distributions = 2
        self.num_usable_units = self.max_num_distributions

    def add_spot(self, spot: DistributionSpot):
        self.distribution_spots.append(spot)

    def prioritize_spots(self):
        """
        Adds the priority to each spot in self.distribution_spots and then sorts all spots recording to there priority.
        """
        for spot in self.distribution_spots:
            if (spot.other_cluster.num_surrounding_units < 1) \
                    and (len(spot.other_cluster.attached_player_city_tiles_pos) == 0):
                base_priority = spot.other_cluster.num_wood_tiles
                priority = base_priority
                # only if we have no unit there we want to co there.
                # check for territory
                if self.strategic_information.num_player_cluster == 1:
                    # we do not want the player to walk to the opponent cluster first.
                    if spot.other_cluster.territory == "o":
                        priority = 0
                else:
                    # even if we do hae more then one cluster we should still prefer expand on our side of the map first
                    if spot.other_cluster.territory == "o":
                        priority = base_priority * 0.6

                if spot.other_cluster.territory == "b":
                    # We should highly prioritise both clusters.
                    priority = base_priority * 1.51
                """
                Note: Increasing priority fpr clusters with coal or uranium did't work out in the early games.
                """
                spot.priority = priority
        self.distribution_spots = sorted(sorted(self.distribution_spots,
                                                key=lambda k: k.dist), key=lambda k: k.priority, reverse=True)

    def trim_spots(self):
        """
        One cluster can only afford a certain amount of distributions spots. Drop all but the best
        self.max_num_distributions spots.
        """
        self.distribution_spots = [spot for spot in self.distribution_spots if spot.priority > 0]
        self.distribution_spots = self.distribution_spots[:max(self.max_num_distributions, 2)]
