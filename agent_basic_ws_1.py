import math, sys
from lux.game import Game
from lux.game_map import Cell, RESOURCE_TYPES
from lux.constants import Constants
from lux.game_constants import GAME_CONSTANTS
from lux import annotate

DIRECTIONS = Constants.DIRECTIONS
game_state = None
stattes = 0

def agent(observation, configuration):
    global game_state
    global stattes

    print('++++++++++++++++++++111111111++++++++++++++++++++++++++++++')
    print('++++++++++++++++++++++++++++++++++++++++++++++++++')
    print('observation["step"]',observation["step"])
    print(stattes)

    ### Do not edit ###
    if observation["step"] == 0:
        game_state = Game()
        game_state._initialize(observation["updates"])
        game_state._update(observation["updates"][2:])
        game_state.id = observation.player
    else:
        game_state._update(observation["updates"])
    
    actions = []

    ### AI Code goes down here! ### 
    player = game_state.players[observation.player]
    opponent = game_state.players[(observation.player + 1) % 2]
    width, height = game_state.map.width, game_state.map.height

    resource_tiles: list[Cell] = []
    for y in range(height):
        for x in range(width):
            cell = game_state.map.get_cell(x, y)
            if cell.has_resource():
                resource_tiles.append(cell)

    # we iterate over all our units and do something with them

    stattes_map = {0:'n',1:'e',2:'s',3:'w'}
    # stattes_map = {0:'n',1:'',2:'s',3:'w'}
    # stattes_map = {0:'n',1:'s'}

    for unit in player.units:
        if unit.is_worker() and unit.can_act():
            # actions.append(unit.move('n'))
            actions.append(unit.move(stattes_map[stattes]))
            # stattes = (stattes +1)%4
            stattes = (stattes +1)%4

    # you can add debug annotations using the functions in the annotate object
    # actions.append(annotate.circle(0, 0))
    print(actions)
    print('---------------------')
    return actions
