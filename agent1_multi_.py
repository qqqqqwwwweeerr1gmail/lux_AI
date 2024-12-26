import time
from lux.game import Game
from Cartographer import Cartographer
from ExpansionOfficer import ExpansionOfficer
from General import General
from MovementOfficer import MovementOfficer
from CityCouncil import CityCouncil
from HarvestingOfficer import HarvestingOfficer

game_state = None


def agent(observation, configuration):
    global game_state
    global night_steps_left
    global territory_map

    step_start = time.time()

    if observation["step"] == 0:
        game_state = Game()
        game_state._initialize(observation["updates"])
        game_state._update(observation["updates"][2:])
        game_state.id = observation.player
    else:
        game_state._update(observation["updates"])

    actions = []

    player = game_state.players[observation.player]
    opponent = game_state.players[(observation.player + 1) % 2]

    if observation["step"] == 0:
        """
        Set some initial variables:
        """
        night_steps_left = 90
        cartographer = Cartographer(lux_map=game_state.map, player=player, opponent=opponent, observation=observation)
        territory_map = cartographer.build_territory_map()

    cartographer = Cartographer(lux_map=game_state.map, player=player, opponent=opponent, observation=observation)
    cartographer.territory_map = territory_map
    cartographer.map_battlefield()
    cartographer.build_resource_cluster()
    harvesting_officer = HarvestingOfficer(harvesting_map=cartographer.harvesting_map,
                                           resource_clusters=cartographer.resource_clusters, lux_map=game_state.map)
    movement_officer = MovementOfficer(step=observation["step"], city_map=cartographer.city_map,
                                       unit_map=cartographer.unit_map, player=player,
                                       opponent=opponent, lux_map=game_state.map,
                                       harvesting_map=cartographer.harvesting_map)
    expansion_officer = ExpansionOfficer(lux_map=game_state.map, city_map=cartographer.city_map,
                                         harvesting_grid=cartographer.harvesting_map,
                                         builder_obstacles_map=movement_officer.builder_obstacles_map,
                                         obstacles_map=movement_officer.obstacles_map,
                                         resource_cluster=cartographer.resource_clusters,
                                         movement_officer=movement_officer)
    city_council = CityCouncil(lux_map=game_state.map, city_map=cartographer.city_map, unit_map=cartographer.unit_map,
                               player=player, harvesting_map=cartographer.harvesting_map,
                               expansion_officer=expansion_officer)
    general = General(cartographer=cartographer, expansion_officer=expansion_officer, movement_officer=movement_officer,
                      city_council=city_council, harvesting_officer=harvesting_officer, actions=actions)
    night_steps_left = general.get_day_night_information(night_steps_left=night_steps_left)
    movement_officer.day = general.day
    city_council.summon_district_mayors(night_steps_left=general.night_steps_left)
    expansion_officer.district_mayors = city_council.district_mayors
    general.build_strategy_information()
    expansion_officer.build_expansion_maps(strategy_information=general.strategy_information, units=general.free_units)
    general.order()
    movement_officer.build_movement_map(orders=general.orders)
    general.execute_orders(game_state=game_state, show_annotation=True)

    step_end = time.time()
    step_duration = step_end - step_start
    if step_duration > 1:
        print(f"WARNING: Step Duration {step_duration} Seconds (Step: {observation['step']})")
    print('-----------------------------------------------------------------------------------------')
    print(observation["step"], actions)
    print('-----------------------------------------------------------------------------------------')
    return actions
