import webbrowser
from kaggle_environments import make
import time
import random


random_seed = 42
random.seed(random_seed)

game_id = str(time.time_ns())
uuid = game_id + '_' + str(random_seed)
# l = g_l('aaa')
# print(steps)

import yaml
data = {
    'random_seed': random_seed,
    'game_id': game_id,
    'uuid': uuid
}

# Write the data to a YAML file
with open('./mid_yml/data.yml', 'w') as file:
    yaml.dump(data, file, default_flow_style=False)

# Initialize the environment
env = make("lux_ai_2021", configuration={"seed": random_seed, "loglevel": 1, "annotations": True}, debug=True)

# Run your agent
# steps = env.run(["./agent1_multi_.py", "./agent_basic.py"])
# steps = env.run(["./agent1_multi_.py", "./agent2_jp_comesido.py"])
# steps = env.run(["./a3_quickstart.py", "./agent2_jp_comesido.py"])
# steps = env.run(["./a3_quickstart.py", "simple_agent"])
# steps = env.run(["./agent_basic.py", "simple_agent"])
# steps = env.run(["./agent_basic.py", "agent_basic_ws.py"])
# steps = env.run(["./agent_basic_ws_1.py", "agent_basic_ws.py"])
# steps = env.run(["./agent_basic_ws_1.py", "agent2_jp_comesido.py"])
# steps = env.run(["./agent_basic.py", "agent1_multi_.py"])
# steps = env.run(["./agent_1226_1.py", "agent1_multi_.py"])
# steps = env.run(["./agent_1226_2.py", "agent1_multi_.py"])
# steps = env.run(["./agent_1227_1.py", "agent1_multi_.py"])
# steps = env.run(["./agent_1227_1.py", "agent_basic.py"])
steps = env.run(["./agent_1227_2_log.py", "agent_basic.py"])


with open("./outputs/lux_ai_output_"+game_id+".txt", 'w') as file:
    # Write the string to the file
    file.write(str(steps))


# Render and save HTML to a file
html_output = env.render(mode='html')
file_out_name = "./outputs/lux_ai_output_"+game_id+".html"

with open(file_out_name, "w") as f:
    f.write(html_output)

# Open the HTML file in a browser
webbrowser.open('file:///C:/GIT/lux_AI/'+file_out_name)
















