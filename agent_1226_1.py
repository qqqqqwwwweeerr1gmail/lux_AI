
import math, sys
import time
from lux.game import Game
from lux.game_map import Cell, RESOURCE_TYPES
from lux.constants import Constants
from lux.game_constants import GAME_CONSTANTS
from lux import annotate

DIRECTIONS = Constants.DIRECTIONS
game_state = None
from lux.annotate import *

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
    # return ['m u_1 n',circle(15,15),x(14,14),line(1,1,9,12),sidetext('fli fly')]
    # return ['m u_1 n',circle(15,15),x(14,14),line(1,1,9,12),text(1,2,'H',15),sidetext('fli fly')]
    # return ['m u_1 n',circle(15,15),x(14,14),line(1,1,9,12),text(1,2,'H'),sidetext('fli fly')]
    if observation["step"] % 2 ==1:
        return ['m u_1 n',circle(15,1),x(4,14),line(1,1,9,12),text(1,2,'H'),sidetext('fli fly')]
    else:
        return ['m u_1 n',circle(15,15),x(14,14),line(1,1,9,2),text(1,2,'H'),sidetext('fli fly111')]



















