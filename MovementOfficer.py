from Cartographer import Cartographer
import numpy as np
from General import OrderType


class MovementOfficer:
    """
    Handles movement orders.
    """
    def __init__(self, step, city_map, unit_map, player, opponent, lux_map, harvesting_map):
        self.direction_dict = {"e": [1, 0], "s": [0, 1], "w": [-1, 0], "n": [0, -1]}
        self.step = step
        self.unit_map = unit_map
        self.city_map = city_map
        self.player = player
        self.opponent = opponent
        self.obstacles_map = np.zeros([len(self.unit_map), len(self.unit_map[0])], np.int16)
        self.builder_obstacles_map = np.zeros([len(self.unit_map), len(self.unit_map[0])], np.int16)
        self.map = lux_map
        self.harvesting_map = harvesting_map
        self.movement_map = np.zeros([len(self.unit_map), len(self.unit_map[0])], object)
        self.day = None

    def build_movement_map(self, orders):
        """
        Builds movement map with orders in mind.
        A builder which is at his building position can't be moved even if he hast cd == 0.
        :param orders: List of orders.
        """
        for player_unit in self.player.units:
            if player_unit.cooldown > 0:
                # unit wont move this turn;
                self.movement_map[player_unit.pos.x][player_unit.pos.y] = "x"
            else:
                # check if unit could be moved and if it has an order to do something.
                unit_order = [o for o in orders if o.unit == player_unit]
                if len(unit_order) == 1:
                    # unit could move but has an order
                    if (unit_order[0].order_type == OrderType.Expansion) and (unit_order[0].dist == 0):
                        # builder standing on his expansion spot --> can't be moved
                        self.movement_map[player_unit.pos.x][player_unit.pos.y] = "x"
                    elif unit_order[0].dist == 0:
                        # todo: potential for improvements. Move harvesting units for example in favor of other
                        #  harvesting units
                        # some other unit with order and cd 0 that sits on its destination.
                        self.movement_map[player_unit.pos.x][player_unit.pos.y] = "x"
                    else:
                        # some units with move order that is not at its destination. Move this unit first.
                        self.movement_map[player_unit.pos.x][
                            player_unit.pos.y] = f"p {player_unit.id} {1}"  # 1 == Has order
                else:
                    # unit could move and has no order
                    self.movement_map[player_unit.pos.x][player_unit.pos.y] = f"p {player_unit.id} {0}"  # 0 == No order

        for opp_unit in self.opponent.units:
            if opp_unit.cooldown > 0:
                # unit wont move this turn;
                self.movement_map[opp_unit.pos.x][opp_unit.pos.y] = "x"
            else:
                # unit could move
                self.movement_map[opp_unit.pos.x][opp_unit.pos.y] = "x"

        for x in range(len(self.city_map)):
            for y in range(len(self.city_map[0])):
                if self.city_map[x][y] == 2:
                    # opponent city tile:
                    self.movement_map[x][y] = "x"

                elif self.city_map[x][y] == 1:
                    # player city tile
                    self.movement_map[x][y] = "c"
        return self.movement_map

    def get_possible_directions_for_unit(self, unit, destination, is_builder, is_returning_harvester,
                                         use_obstacle_maps=False):
        """
        Greedy ....
        """
        possible_directions_dict = {}
        distances = []

        if is_builder:
            cargo = 100 - unit.get_cargo_space_left()
            if cargo < 60:
                # treat builder as normal unit:
                is_builder = False

        for key, value in self.direction_dict.items():
            new_x, new_y = unit.pos.x + value[0], unit.pos.y + value[1]
            if (0 <= new_x < self.map.width) and (0 <= new_y < self.map.height):
                # new position is on map. --> check for obstacles:
                if use_obstacle_maps:
                    if is_builder or is_returning_harvester:
                        if self.builder_obstacles_map[new_x][new_y] == 0:
                            dist = Cartographer.distance(origin=[new_x, new_y], destination=destination)
                            distances.append(dist)
                            possible_directions_dict[key] = [(new_x, new_y), dist, (new_x == destination[0])
                                                             or (new_y == destination[1])]
                            # new_position, distance to destination, on the same axis
                    else:
                        if self.obstacles_map[new_x][new_y] == 0:
                            dist = Cartographer.distance(origin=[new_x, new_y], destination=destination)
                            distances.append(dist)
                            possible_directions_dict[key] = [(new_x, new_y), dist, (new_x == destination[0])
                                                             or (new_y == destination[1])]
                        # new_position, distance to destination, on the same axis

                else:
                    # use movement_map
                    if self.movement_map[new_x][new_y] != "x":
                        if is_builder or is_returning_harvester:
                            if self.movement_map[new_x][new_y] != "c":
                                dist = Cartographer.distance(origin=[new_x, new_y], destination=destination)
                                distances.append(dist)
                                possible_directions_dict[key] = [(new_x, new_y), dist, (new_x == destination[0])
                                                                 or (new_y == destination[1])]
                                # new_position, distance to destination, on the same axis
                        else:
                            dist = Cartographer.distance(origin=[new_x, new_y], destination=destination)
                            distances.append(dist)
                            possible_directions_dict[key] = [(new_x, new_y), dist, (new_x == destination[0])
                                                             or (new_y == destination[1])]
                            # new_position, distance to destination, on the same axis

        shortest_directions = [k for k, v in possible_directions_dict.items() if v[1] == min(distances)]
        if len(shortest_directions) > 1:
            # exclude opposite direction
            shortest_directions_ex_opposite = [k for k in shortest_directions if not possible_directions_dict[k][2]]
            if len(shortest_directions_ex_opposite) > 1:
                # choose random direction between the other
                possible_directions = shortest_directions_ex_opposite
            elif len(shortest_directions_ex_opposite) == 1:
                possible_directions = shortest_directions_ex_opposite
            else:
                # len(shortest_directions_ex_opposite) == 0
                # this means that the destination is diagonal to the origin.
                # So we choose one at random.
                possible_directions = shortest_directions
        elif len(shortest_directions) == 1:
            possible_directions = shortest_directions
        else:
            possible_directions = []

        return possible_directions

    def move_units(self, move_orders):
        """
        Main method of MevementOfficer.
        Logic: The idea is that we try to move each unit towards its destination
        without collisions and blockades. So we start with units that have free movement options. Imagine a chain of
        five units that all have the same destination. Here we make sure that the movement action is performed in such
        a way thatthat the first unit (at the head of the chain) is moved first, and then the second unit is moved to
        the old place of the first unit and so on. If a unit without an order and cd = 0 blocks a unit with an order,
        we move that unit out of the way.

        :param move_orders: list of move orders.
        """
        actions = []
        unit_movement_options = set()
        for order in move_orders:

            directions = self.get_possible_directions_for_unit(
                unit=order.unit, destination=order.pos,
                is_returning_harvester=((order.order_type == OrderType.Harvest_Return) and (order.dist > 1)),
                is_builder=order.order_type == OrderType.Expansion)

            unit_movement_options.add(MovementOptions(order=order, directions=directions,
                                                      harvesting_map=self.harvesting_map,
                                                      movement_map=self.movement_map, day=self.day))

        def try_to_move_unit_without_order(unit_id, blocked_positions):
            """
            Check if there is a spot where the unit can move without blocking another possibility of movement.
            :return: bool
            """
            can_be_moved = False
            evasive_pos = ()
            evasive_direction = None
            unit = [u for u in self.player.units if u.id == unit_id]
            if len(unit) > 0:
                unit = unit[0]
                for direction, delta in self.direction_dict.items():
                    new_x = unit.pos.x + delta[0]
                    new_y = unit.pos.y + delta[1]
                    if (0 <= new_x < self.map.width) and (0 <= new_y < self.map.height):
                        if (self.movement_map[new_x][new_y] == "c" or self.movement_map[new_x][new_y] == 0) and \
                                ((new_x, new_y) not in blocked_positions):
                            evasive_direction = direction
                            evasive_pos = (new_x, new_y)
                            can_be_moved = True
                            break
            if can_be_moved:
                # We move the unit and update our Movement map. Other units cant be moved to this position.
                self.movement_map[evasive_pos[0]][evasive_pos[1]] = "x"
                if self.movement_map[unit.pos.x][unit.pos.y][0] == "p":
                    self.movement_map[unit.pos.x][unit.pos.y] = 0
                for v in unit_movement_options:
                    v.remove_option_direction(pos=(evasive_pos[0], evasive_pos[1]))
                    v.build_options_from_directions()
                actions.append(unit.move(evasive_direction))
                return True
            else:
                return False

        def assign_position(move_action):
            """
            Moves unit from move action to best direction.
            Removes the given spots from all other Move Actions after adding the move actions.
            Resets all other options for the moved unit.
            :param move_action: MoveAction
            :return:
            """
            actions.append(move_action.order.unit.move(move_action.best_option.direction))
            self.movement_map[move_action.best_option.pos[0]][move_action.best_option.pos[1]] = "x"
            if self.movement_map[move_action.order.unit.pos.x][move_action.order.unit.pos.y][0] == "p":
                # update movement map. If this unit was a blocker --> remove it. Otherwise it was standing on a city and
                # we leave the entry as "c.
                self.movement_map[move_action.order.unit.pos.x][move_action.order.unit.pos.y] = 0
            for v in unit_movement_options:
                v.remove_option_direction(pos=move_action.best_option.pos)
                v.build_options_from_directions()

        loop_move_actions = set()

        def stay(move_action):
            """
            Assing unit to its current spot and mark this spot on the movement map as obstacle.
            :param move_action:
            :return:
            """
            self.movement_map[move_action.order.unit.pos.x][move_action.order.unit.pos.y] = "x"
            for v in unit_movement_options:
                v.remove_option_direction(pos=(move_action.order.unit.pos.x, move_action.order.unit.pos.y))
                v.build_options_from_directions()

        def try_to_execute_move_action(move_action):

            if move_action.can_move and not move_action.best_option.collision:
                # has a best option that will not collide with other units.
                # check if another unit wants to go there:
                possible_collision = False
                critical_collision = False
                for v in unit_movement_options:
                    if v.order.unit.id != move_action.order.unit.id:
                        if v.includes_option_with_position(pos=move_action.best_option.pos):
                            if v.num_options == 1:
                                possible_collision = True
                                critical_collision = True
                            else:
                                possible_collision = True
                if critical_collision:

                    if move_action.num_options == 1:
                        # we have a critical collision and both unit can only move on that single tile.
                        # --> prefer builder
                        if move_action.order.order_type == OrderType.Expansion:
                            # if i am a builder --> take the spot. Else --> don't move
                            assign_position(move_action=move_action)
                        else:
                            # i am not a builder and therefor i will not move
                            stay(move_action)
                    elif move_action.num_options > 1:
                        # we have a collision and at least one unit can only move on that one tile in our best option.
                        # But we have other option. Try them first.
                        move_action.remove_option_direction(pos=move_action.best_option.pos)
                        move_action.build_options_from_directions()
                        try_to_execute_move_action(move_action=move_action)
                else:
                    # no critical collision
                    if possible_collision:
                        # we have a possible collision but all other units have at least one additional option.
                        # --> just move
                        assign_position(move_action=move_action)
                    else:
                        # no collision at all. We can move:
                        assign_position(move_action=move_action)
            elif move_action.can_move and move_action.best_option.collision:
                # we have a best option but we will collide with other units.
                if move_action.best_option.collision_unit_has_order:
                    # our_best_option will collide with another unit with an order.
                    if move_action in loop_move_actions:
                        # we are in a loop --> try to move this unit if possible:
                        if move_action.num_options > 1:
                            # we have additional options: --> remove best option and add updated move action.
                            loop_move_actions.remove(move_action)
                            move_action.remove_option_direction(pos=move_action.best_option.pos)
                            move_action.build_options_from_directions()
                            try_to_execute_move_action(move_action=move_action)
                        else:
                            # we have only one or zero move action.
                            stay(move_action)
                    else:
                        # first time seeing this move action. Try to move blocking unit with order first:
                        blocking_unit_move_action = [mo for mo in unit_movement_options if mo.order.unit.id ==
                                                     move_action.best_option.collision_unit_id]
                        if len(blocking_unit_move_action) > 0:
                            blocking_unit_move_action = blocking_unit_move_action[0]
                            unit_movement_options.add(move_action)
                            loop_move_actions.add(move_action)
                            unit_movement_options.remove(blocking_unit_move_action)
                            try_to_execute_move_action(move_action=blocking_unit_move_action)
                        else:
                            print(f"WARNING: step: ({self.step}). Something went wrong while moving.")
                else:
                    # our best_option will collide with another unit with no order.
                    # try to move blocking unit
                    possible_taken_positions = set()
                    for v in unit_movement_options:
                        # don't move on current positions of units with orders
                        possible_taken_positions.add((v.order.unit.pos.x, v.order.unit.pos.y))
                        if len(v.options) > 0:
                            for o in v.options:
                                possible_taken_positions.add(o.pos)

                    moved_unit = try_to_move_unit_without_order(unit_id=move_action.best_option.collision_unit_id,
                                                                blocked_positions=possible_taken_positions)
                    if moved_unit:
                        # we moved the blocking unit aside and can move now:
                        assign_position(move_action=move_action)
                    else:
                        # we cant move the blocking unit.
                        if move_action.num_options > 1:
                            # we have additional options: --> remove best option and add updated move action.
                            move_action.remove_option_direction(pos=move_action.best_option.pos)
                            move_action.build_options_from_directions()
                            try_to_execute_move_action(move_action=move_action)
                        else:
                            # don't move at all:
                            stay(move_action)
            else:
                # we have nowhere to go and this means that this unit is an obstacle. --> remove all options with the
                # given position of the unit
                stay(move_action)

        all_units_moved = False
        while not all_units_moved:
            if len(unit_movement_options) == 0:
                all_units_moved = True
            else:
                move_action = unit_movement_options.pop()
                try_to_execute_move_action(move_action=move_action)

        return actions

    def build_obstacles_maps(self):
        """
        Builds obstacles maps and builder_obstacles_map bases on cities and units.
        Considers units with cd 0 not as obstacle.
        :return:
        """
        for x in range(len(self.city_map)):
            for y in range(len(self.city_map[0])):
                if self.city_map[x][y] == 2:
                    # opponent city tile:
                    self.obstacles_map[x][y] = 2
                    self.builder_obstacles_map[x][y] = 2
                elif self.city_map[x][y] == 1:
                    # player city tile
                    self.builder_obstacles_map[x][y] = 1
                else:
                    # no city tile:
                    if self.unit_map[x][y] == 2:
                        # opponent unit:
                        unit = [u for u in self.opponent.units if (u.pos.x, u.pos.y) == (x, y)][0]
                        if unit.cooldown > 0:
                            # unit won't move in this turn
                            self.obstacles_map[x][y] = 2
                            self.builder_obstacles_map[x][y] = 2
                    elif self.unit_map[x][y] == 1:
                        # player unit:
                        unit = [u for u in self.player.units if (u.pos.x, u.pos.y) == (x, y)][0]
                        if unit.cooldown > 0:
                            # unit won't move in this turn
                            self.obstacles_map[x][y] = 1
                            self.builder_obstacles_map[x][y] = 1


class MovementOptions:
    def __init__(self, order, directions, harvesting_map, movement_map, day):
        self._direction_dict = {"e": [1, 0], "s": [0, 1], "w": [-1, 0], "n": [0, -1]}
        self.order = order
        self.directions = directions
        self.harvesting_map = harvesting_map
        self.movement_map = movement_map
        self.day = day
        self.num_options = 0
        self.best_option = None
        self.can_move = False
        self.options = None
        self.build_options_from_directions()

    def reset_option(self):
        """
        After we moved a unit its option will be cleared that none of them will interfere with other move actions.
        """
        self.num_options = 0
        self.directions = []
        self.best_option = None
        self.can_move = False
        self.options = None

    def includes_option_with_position(self, pos):
        """
        Checks if a given position is part of an option and if it can be removed and the unit can still move.
        :param pos: position tuple
        """
        if self.options is not None:
            pos_option = [o for o in self.options if o.pos == pos]
            if len(pos_option) == 0:
                # no option with given position
                return False
            else:
                return True

    def remove_option_direction(self, pos):
        """
        Removes a direction from the move options.
        :param pos: position tuple
        """
        if self.includes_option_with_position(pos=pos):
            option_to_remove = [o for o in self.options if o.pos == pos][0]
            new_possible_directions = [d for d in self.directions if d != option_to_remove.direction]
            self.directions = new_possible_directions

    def build_options_from_directions(self):
        """
        Builds move actions for given directions.
        :return:
        """
        self.options = []
        self.best_option = None
        max_direction_value = 0

        for direction in self.directions:
            collision_unit_id = None
            collision_unit_has_order = False
            new_pos = (self.order.unit.pos.x + self._direction_dict[direction][0],
                       self.order.unit.pos.y + self._direction_dict[direction][1])
            # define direction value

            if self.order.order_type == OrderType.Expansion:
                if self.order.unit.get_cargo_space_left() > 0:
                    direction_value = self.harvesting_map[new_pos[0]][new_pos[1]].collection_amount_per_turn
                else:
                    direction_value = 0
            elif self.order.order_type == OrderType.Harvest_Go:
                direction_value = self.harvesting_map[new_pos[0]][new_pos[1]].fuel_value_per_turn
            else:
                direction_value = 0

            if isinstance(self.movement_map[new_pos[0]][new_pos[1]], str) and \
                    self.movement_map[new_pos[0]][new_pos[1]][0] == "p":
                # ['p', 'u_15', '1']
                collision_info = self.movement_map[new_pos[0]][new_pos[1]].split()
                collision_unit_id = collision_info[1]
                collision_unit_has_order = bool(int(collision_info[2]))
                collision = True
            else:
                collision = False
            if direction_value > max_direction_value:
                max_direction_value = direction_value
            self.options.append(
                MoveOption(direction=direction, pos=new_pos, value=direction_value, collision=collision,
                           collision_unit_id=collision_unit_id, collision_unit_has_order=collision_unit_has_order))
        # remove options that would kill units at night:
        if not self.day:
            # unit wont survive night if next step is not a harvesting spot.
            if self.order.unit.get_cargo_space_left() >= 60:
                possible_options = []
                for option in self.options:
                    if self.harvesting_map[option.pos[0]][option.pos[1]].collection_amount_per_turn >= 4:
                        possible_options.append(option)
                self.options = possible_options

        if len(self.options) > 1:
            # get_options with max direction value:
            best_options = [o for o in self.options if o.value == max_direction_value]
            if len(best_options) > 1:
                # more then one optimal option: --> exclude collision moves
                best_no_collision_options = [o for o in best_options if not o.collision]
                if len(best_no_collision_options) == 0:
                    best_option = best_options[0]
                elif len(best_no_collision_options) == 1:
                    best_option = best_no_collision_options[0]
                else:
                    # > 1
                    best_option = best_no_collision_options[0]
            else:
                # we have one option with max direction value:
                best_option = best_options[0]
        elif len(self.options) == 1:
            # single option
            best_option = self.options[0]
        else:
            # no movement option
            best_option = None
        self.best_option = best_option
        if self.best_option is not None:
            self.can_move = True
        else:
            self.can_move = False
        self.num_options = len(self.options)

    def show(self):
        print(30*"*")
        print(f"num_options: {self.num_options}")
        print(f"best_option: {self.best_option}")
        print(f"can_move: {self.can_move}")


class MoveOption:
    def __init__(self, direction, pos, value, collision, collision_unit_id=None, collision_unit_has_order=None):
        self.direction = direction
        self.pos = pos
        self.value = value
        self.collision = collision
        self.collision_unit_id = collision_unit_id
        self.collision_unit_has_order = collision_unit_has_order

    def __str__(self):
        return f"d: {self.direction}, pos: {self.pos}, value: {self.value}, collision: {self.collision}"
