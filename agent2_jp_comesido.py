

# housekeeping
import math, sys
import random

if __package__ == "":
    # for kaggle-environments
    from lux.game import Game
    from lux.game_map import Cell, RESOURCE_TYPES, Position
    from lux.game_objects import Unit
    from lux.constants import Constants
    from lux.game_constants import GAME_CONSTANTS
    from lux import annotate
else:
    # for CLI tool
    from .lux.game import Game
    from .lux.game_map import Cell, RESOURCE_TYPES, Position
    from .lux.constants import Constants
    from .lux.game_constants import GAME_CONSTANTS
    from .lux import annotate

DIRECTIONS = Constants.DIRECTIONS
game_state = None


def agent(observation, configuration):
    print(observation["reward"])
    global game_state

    ### Do not edit ###
    if observation["step"] == 0:
        game_state = Game()
        game_state._initialize(observation["updates"])
        game_state._update(observation["updates"][2:])
        game_state.id = observation.player
    else:
        game_state._update(observation["updates"])

    actions = []
    test_actions = []

    ### AI Code goes down here! ###
    player = game_state.players[observation.player]
    opponent = game_state.players[(observation.player + 1) % 2]
    width, height = game_state.map.width, game_state.map.height

    ##############################
    ### NOVEL CODE STARTS HERE ###
    ##############################

    # helper functions
    def researched(resource):
        """
        given a Resource object, return whether the player has researched the resource type
        """
        if resource.type == Constants.RESOURCE_TYPES.WOOD:
            return True
        if resource.type == Constants.RESOURCE_TYPES.COAL \
                and player.research_points >= GAME_CONSTANTS['PARAMETERS']['RESEARCH_REQUIREMENTS']['COAL']:
            return True
        if resource.type == Constants.RESOURCE_TYPES.URANIUM \
                and player.research_points >= GAME_CONSTANTS['PARAMETERS']['RESEARCH_REQUIREMENTS']['URANIUM']:
            return True
        return False

    def enough(resource):
        if resource.type == Constants.RESOURCE_TYPES.WOOD \
                and resource.amount < 500:
            return False
        return True

    def get_cells(cell_type):  # resource, researched resource, player citytile, enemy citytile, empty
        """
        Given a cell type, returns a list of Cell objects of the given type
        Options are: ['resource', 'researched resource', 'player citytile', 'enemy citytile', 'empty']
        """
        cells_of_type = []
        for y in range(height):
            for x in range(width):
                cell = game_state.map.get_cell(x, y)
                if (
                        ( cell_type == 'resource' and cell.has_resource() ) \
                        or ( cell_type == 'researched resource' and cell.has_resource() and researched(cell.resource) and enough(cell.resource) ) \
                        or ( cell_type == 'player citytile' and cell.citytile is not None and cell.citytile.team == observation.player ) \
                        or ( cell_type == 'enemy citytile' and cell.citytile is not None and cell.citytile.team != observation.player ) \
                        or ( cell_type == 'empty' and cell.citytile is None and not cell.has_resource() )
                ):
                    cells_of_type.append(cell)

        return cells_of_type

    def find_nearest_position(target_position, option_positions):
        """
        target_position: Position object
        option_positions: list of Position, Cell, or Unit objects (must all be the same type)
        finds the closest option_position to the target_position
        """

        # convert option_positions list to Position objects
        if type(option_positions[0]) in [Cell, Unit]:
            option_positions = [cell.pos for cell in option_positions]

        # find closest position
        closest_dist = math.inf
        closest_position = None
        for position in option_positions:
            dist = target_position.distance_to(position)
            if dist < closest_dist:
                closest_dist = dist
                closest_position = position

        return closest_position

    target_tiles = [] # to help avoid collisions
    def move_unit(unit, position):
        """
        moves the given unit towards the given position
        also checks basic collision detection, and adds annotations for any movement
        """

        direction = unit.pos.direction_to(position)
        target_tile = unit.pos.translate(direction, 1)
        target_cell = game_state.map.get_cell_by_pos(target_tile)
        # 的のcitytileがある場合はランダムに動く
        if target_cell.citytile is not None and target_cell.citytile.team != observation.player:
            move_random(unit)
            return
        # 別ユニットがいる場合はランダムに動く
        if not (target_cell.citytile is not None and target_cell.citytile.team == observation.player) and any([target_tile.equals(u.pos) for u in (player.units + opponent.units)]):
            move_random(unit)
            return

        # if target_tile is not being targeted already, move there
        if target_tile not in target_tiles or target_tile in [tile.pos for tile in citytile_cells]:
            target_tiles.append(target_tile)
            actions.append(unit.move(direction))
            actions.append(annotate.line(unit.pos.x, unit.pos.y, position.x, position.y))

        # else, mark an X on the map
        else:
            actions.append(annotate.x(target_tile.x, target_tile.y))

    def go_home(unit):
        """
        moves the given unit towards the nearest citytile
        """

        nearest_citytile_position = find_nearest_position(unit.pos, citytile_cells)
        move_unit(unit, nearest_citytile_position)

    def move_random(unit):
        """
        moves random
        """

        # 無限ループを防ぐために一定割合で何もしない
        if random.random() < 0.1:
            return
        seed = random.random()
        random_pos = game_state.map.get_cell(int(game_state.map.width*seed), int(game_state.map.width*seed)).pos
        move_unit(unit, random_pos)


    #############################
    ### ALGORITHM STARTS HERE ###
    #############################

    # get all resource tiles
    researched_resource_cells = get_cells('researched resource')
    citytile_cells = get_cells('player citytile')

    # calculate number of citytiles
    num_citytiles = len(citytile_cells)

    # iterate over units
    for unit in player.units:
        if unit.is_worker() and unit.can_act():

            # if night and there are cities, return home:
            if game_state.turn % 40 > 30 and len(player.cities) > 0:
                go_home(unit)

            # if there is cargo space, find nearest resource and move towards it
            elif (unit.get_cargo_space_left() > 0) and (len(researched_resource_cells) > 0):
                nearest_resource_position = find_nearest_position(unit.pos, researched_resource_cells)
                move_unit(unit, nearest_resource_position)

            # if cargo is full
            else:
                # ランダムに動いたときに、何もない場所にきたら建てる
                if unit.can_build(game_state.map):
                    actions.append(unit.build_city())


                else:
                    # 5割の確率で近くのcitytileに帰り、5割はランダムに動く
                    if (random.random() > 0.5):
                        nearest_citytile_position = find_nearest_position(unit.pos, citytile_cells)
                        move_unit(unit, nearest_citytile_position)
                    else:
                        move_random(unit)

        if unit.is_cart() and unit.can_act():
            # if night and there are cities, return home:
            if game_state.turn % 40 > 30 and len(player.cities) > 0:
                go_home(unit)

            # if there is cargo space, find nearest resource and move towards it
            elif (unit.get_cargo_space_left() > 0) and (len(researched_resource_cells) > 0):
                nearest_resource_position = find_nearest_position(unit.pos, researched_resource_cells)
                move_unit(unit, nearest_resource_position)

            else:
                go_home(unit)


    # iterate through cities
    for k, city in player.cities.items():
        for citytile in city.citytiles:
            if citytile.can_act():

                # if there is space for more units, build a worker
                if num_citytiles > len(player.units):
                    # 一定確率でワーカーかカートを生成
                    if (random.random() > 0.2):
                        actions.append(citytile.build_worker())
                    else:
                        actions.append(citytile.build_cart())

                # else research
                else:
                    actions.append(citytile.research())

    return actions






















