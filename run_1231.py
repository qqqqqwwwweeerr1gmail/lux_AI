import webbrowser
from kaggle_environments import make
import time

from common.up_yml import ws_up_yml

random_seed_action = 42
random_seed_action = 40
random_seed_action = 39
random_seed_action = 77
random_seed_action = 70

random_seed_game = 42
# random_seed_game = 11
# random_seed_game = 10
# random_seed_game = 11
# random_seed_game = 14
# random_seed_game = 10

# Initialize the environment
env = make("lux_ai_2021", configuration={"seed": random_seed_game, "loglevel": 1, "annotations": True}, debug=True)

# agents = ["agent_1227_2_log.py", "agent_1227_2_log.py"]
# agents = ["agent_1230.py", "agent_1230.py"]
# agents = ["agent_basic.py", "agent_1230.py"]
# agents = ["a_1230_2.py", "agent_basic.py"]
# agents = ["agent_basic.py", "a_1230_2.py"]
# agents = ["a_1230_2.py", "a_1230_2.py"]
agents = ["agent_basic.py", "a_1230_3_o.py"]
agents = ["a_1230_3_o.py", "a_1230_3_o.py"]
agents = ["a_1230_3_o.py", "agent_basic.py"]
agents = ["a_1230_3_o.py", "a_1230_3_oo.py"]
agents = ["a_1230_4.py", "a_1230_4.py"]
agents = ["a_1230_5.py", "a_1230_5.py"]
agents = ["a_1230_6.py", "a_1230_6.py"]
agents = ["a1231_1_wc.py", "a1231_1_w.py"]
agents = ["agent1_multi_.py", "agent2_jp_comesido.py"]
# agents = ["a1231_1_3w1c.py", "a1231_1_3w1c.py"]
# agents = ["agent1_multi_.py", "a1231_1_3w1c.py"]
# agents = ["a1231_2_wr.py", "a1231_1_3w1c.py"]
# agents = ["agent2_jp_comesido.py", "a1231_1_3w1c.py"]
# agents = ["a_1230_6.py", "agent_basic.py"]
# agents = ["agent_basic.py", "a_1230_6.py"]

steps = env.run(agents)

tns = str(time.time_ns())
game_id = str(random_seed_game)+'_'+agents[0].split('.py')[0]+'_vs_'+agents[1].split('.py')[0]+'_'+tns
uuid = game_id + '_' + str(random_seed_action)
# # l = g_l('aaa')
# # print(steps)
#
# import yaml
# data = {
#     'random_seed_action': random_seed_action,
#     'random_seed_game': random_seed_game,
#     'game_id': game_id,
#     'uuid': uuid
# }
# with open('./mid_yml/data.yml', 'w') as file:
#     yaml.dump(data, file, default_flow_style=False)

ws_up_yml(random_seed_action=random_seed_action,random_seed_game=random_seed_game,game_id=game_id,uuid=uuid)

with open("./outputs/lux_"+game_id+".txt", 'w') as file:
    file.write(str(steps))


html_output = env.render(mode='html')
file_out_name = "./outputs/lux_"+game_id+".html"

with open(file_out_name, "w") as f:
    f.write(html_output)

webbrowser.open('file:///C:/GIT/lux_AI/'+file_out_name)
















