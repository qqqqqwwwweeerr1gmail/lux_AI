import os
import time,random
import yaml


def ws_up_yml(random_seed_action=-1,random_seed_game=-1,game_id='',uuid=''):
    data = {
        'random_seed_action': random_seed_action if random_seed_action != -1 else random.randint(0, 100),
        'random_seed_game': random_seed_game if random_seed_game != -1 else random.randint(0, 100),
        'game_id': game_id,
        'uuid': uuid
    }

    with open('C:\GIT\lux_AI/mid_yml/data.yml', 'w') as file:
        yaml.dump(data, file, default_flow_style=False)


if __name__ == '__main__':
    ws_up_yml()





















