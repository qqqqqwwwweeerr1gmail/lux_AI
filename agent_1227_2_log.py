
import math, sys
import time
import random

from lux.game import Game
from lux.game_map import Cell, RESOURCE_TYPES
from lux.constants import Constants
from lux.game_constants import GAME_CONSTANTS
from lux import annotate

DIRECTIONS = Constants.DIRECTIONS
game_state = None
from lux.annotate import circle as annotate_circle, x as annotate_x, line as annotate_line, text as annotate_text, sidetext as annotate_sidetext

import yaml

from logs.log_ import g_l


with open('./mid_yml/data.yml', 'r') as file:
    data = yaml.safe_load(file)

print(data)
l = g_l(data["uuid"])


def agent(observation, configuration):
    global game_state

    ### Do not edit ###
    if observation["step"] == 0:
        game_state = Game()
        game_state._initialize(observation["updates"])
        game_state._update(observation["updates"][2:])
        game_state.id = observation.player
        return ['m u_1 n']
    else:
        game_state._update(observation["updates"])

    l.info(observation["step"])

    acs = []

    player = game_state.players[observation.player]
    opponent = game_state.players[(observation.player + 1) % 2]
    width, height = game_state.map.width, game_state.map.height

    resource_tiles: list[Cell] = []
    for y in range(height):
        for x in range(width):
            cell = game_state.map.get_cell(x, y)
            if cell.has_resource():
                resource_tiles.append(cell)
    workers = [unit for unit in player.units if unit.is_worker()]
    carts = [unit for unit in player.units if unit.is_cart()]
    rp = player.research_points
    team = player.team
    cities = player.cities
    city_tile_count = player.city_tile_count
    workers_count = player.workers_count
    carts_count = player.carts_count
    # city = cities[list(cities.keys())[0]]
    # cityid = city.cityid
    # cityteam = city.team
    # cityfuel = city.fuel
    # citytiles = city.citytiles
    # citylight_upkeep = city.light_upkeep
    # city_tile = city.citytiles[0]
    # city_tilecityid =city_tile.cityid
    # city_tileteam = city_tile.team
    # city_tilepos = city_tile.pos
    # city_tilecooldown = city_tile.cooldown


    for index_city ,city in player.cities.items():
        for city_tile in city.citytiles:
            if city_tile.can_act():
                if workers_count > carts_count:
                    acs.append(city_tile.build_cart())
                else:
                    acs.append(city_tile.build_worker())

    for worker in workers:
        if worker.can_build(game_state.map):
            acs.append(worker.build_city())
        elif worker.can_act():
            acs.append(worker.move(random.choice(['n','c','e','w'])))

    for cart in carts:
        if cart.can_build(game_state.map):
            acs.append(cart.build_city())
        elif cart.can_act():
            acs.append(cart.move(random.choice(['n','c','e','w'])))
    for unit in player.units:
        # print('pos',unit.pos)
        # print('team',unit.team)
        # print('id',unit.id)
        # print('type',unit.type)
        # print('cooldown',unit.cooldown)
        # print('cargo',unit.cargo)
        # print('.cargo.wood',unit.cargo.wood)
        # print('.cargo.coal',unit.cargo.coal)
        # print('.cargo.uranium',unit.cargo.uranium)
        # print('get_cargo_space_left',unit.get_cargo_space_left())
        # print('can_build',unit.can_build(game_state.map))
        # print('is_worker',unit.is_worker())
        # print('is_cart',unit.is_cart())
        # print('can_act',unit.can_act())
        # print('move',unit.move('n'))
        # print('transfer',unit.transfer(0,'wood',20))
        # print('build_city',unit.build_city())
        # print('pillage',unit.pillage())
        # time.sleep(10)
        pass
    acs.append(annotate_sidetext(str(acs).replace('\'','"')+'\r\nafdfddsf'))
    l.info(observation["step"])
    l.info(acs)
    l.info('')
    if observation["step"] <1000:

        return acs
    else:
        # actions = ['m u_1 n',circle(15,1),x(14,4),line(1,1,9,2),text(1,20,'i ove u'),sidetext('fli fly')]
        return []





















