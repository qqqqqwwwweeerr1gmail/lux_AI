
import math, sys
import time
from common.ws_random import Random_bot
from common.opposite import get_opposite_direction, get_opposite_ew, get_di, get_opposite_di
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
# l = g_l(data["uuid"])
random_seed_action = data["random_seed_action"]
r_bot = Random_bot(seed=random_seed_action)
game_di = ''
l = ''

def agent(observation, configuration):
    global game_state
    global game_di
    global l

    ### Do not edit ###
    if observation["step"] == 0:
        game_state = Game()
        game_state._initialize(observation["updates"])
        game_state._update(observation["updates"][2:])
        game_state.id = observation.player
        # return ['m u_1 n']
    else:
        game_state._update(observation["updates"])


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
    workers_count = len(workers)
    carts_count = len(carts)
    rp = player.research_points
    team = player.team
    cities = player.cities
    city_tile_count = player.city_tile_count
    # workers_count = player.workers_count
    # carts_count = player.carts_count
    if observation["step"]+1 == 100:
        print()
        pass


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

    if not l:
        l = g_l(data["uuid"]+'_'+str(team))
        # l_team = 'Done'

    l.info(observation["step"]+1)
    if not game_di:
        game_di = get_di(list(player.cities.values())[0].citytiles[0].pos,list(opponent.cities.values())[0].citytiles[0].pos,team)

    for index_city, city in player.cities.items():
        for city_tile in city.citytiles:
            if city_tile.can_act():
                if workers_count > carts_count:
                    acs.append(city_tile.build_cart())
                else:
                    acs.append(city_tile.build_worker())

    citys = [city for index_city, city in player.cities.items()]
    city_tiles = [[ct for ct in c.citytiles]for c in citys]
    city_tiles_flat = [item for ct in city_tiles for item in ct]

    if team % 2 == 1:
        if game_di == 'ew':
            city_tiles_flat_so = sorted(city_tiles_flat, key=lambda cell: (-cell.pos.x, cell.pos.y))
        if game_di == 'ns':
            city_tiles_flat_so = sorted(city_tiles_flat, key=lambda cell: (cell.pos.x, -cell.pos.y))
    else:
        city_tiles_flat_so = sorted(city_tiles_flat, key=lambda cell: (cell.pos.x, cell.pos.y))

    acts_city = [ct.build_cart() if workers_count > carts_count and ct.can_act() else ct.build_cart() for ct in city_tiles_flat_so]
    acs.extend(acts_city)

    for worker in workers:
        if worker.can_build(game_state.map):
            acs.append(worker.build_city())
        elif worker.can_act():
            acs.append(worker.move(get_opposite_di(r_bot.ba(['n','c','e','w','s']),player.team,game_di)))

    for cart in carts:
        if cart.can_build(game_state.map):
            acs.append(cart.build_city())
        elif cart.can_act():
            acs.append(cart.move(get_opposite_di(r_bot.ba(['n','c','e','w','s']),player.team,game_di)))

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

    acs.append(annotate_sidetext(str(acs).replace('\'','"')))
    l.info(observation["step"]+1)
    acs2log = [i + ' ' * (8 - len(i)) if i.startswith('bw ') and len(i) != 8 else i for i in acs]
    acs2log = [i + ' ' * (8 - len(i)) if i.startswith('m ') and len(i) != 8 else i for i in acs2log]
    l.info(acs2log)
    l.info('num_cities:'+str(len(player.cities)))
    l.info('num_workers:'+str(len(workers)))
    l.info('num_carts:'+str(len(carts)))
    # l.info('num_workers:',workers)
    l.info('')
    if observation["step"] <1000:

        return acs
    else:
        # actions = ['m u_1 n',circle(15,1),x(14,4),line(1,1,9,2),text(1,20,'i ove u'),sidetext('fli fly')]
        return []





















