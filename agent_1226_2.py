
import math, sys
import time
from lux.game import Game
from lux.game_map import Cell, RESOURCE_TYPES
from lux.constants import Constants
from lux.game_constants import GAME_CONSTANTS
from lux import annotate

DIRECTIONS = Constants.DIRECTIONS
game_state = None
from lux.annotate import circle as annotate_circle, x as annotate_x, line as annotate_line, text as annotate_text, sidetext as annotate_sidetext

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

    actions = []

    player = game_state.players[observation.player]
    opponent = game_state.players[(observation.player + 1) % 2]
    width, height = game_state.map.width, game_state.map.height

    resource_tiles: list[Cell] = []
    for y in range(height):
        for x in range(width):
            cell = game_state.map.get_cell(x, y)
            if cell.has_resource():
                resource_tiles.append(cell)

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
        # print('can_act',unit.can_act())
        # print('move',unit.move('n'))
        # print('transfer',unit.transfer(0,'wood',20))
        # print('build_city',unit.build_city())
        # print('pillage',unit.pillage())
        # time.sleep(10)
        pass

    if observation["step"] % 2 ==1:
        # actions = ['m u_1 n',circle(15,15),x(14,14),line(1,1,9,12),text(1,2,'H'),sidetext('fli fly')]
        actions = ['m u_1 n']
        # actions = ['m u_1 n',circle(15,15)]
        actions = ['m u_1 n', annotate_circle(15, 15), annotate_x(14, 14), annotate_line(1, 1, 9, 12), annotate_text(1, 2, 'H'), annotate_sidetext('fli fly')]

        return actions
    else:
        # actions = ['m u_1 n',circle(15,1),x(14,4),line(1,1,9,2),text(1,20,'i ove u'),sidetext('fli fly')]
        return []


















