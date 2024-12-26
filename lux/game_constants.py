import json
from os import path
dir_path = path.dirname(__file__)
constants_path = path.abspath(path.join(dir_path, "game_constants.json"))
with open(constants_path) as f:
    GAME_CONSTANTS = json.load(f)


if __name__ == '__main__':
    print(GAME_CONSTANTS)
    print(GAME_CONSTANTS.keys())