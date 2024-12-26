# for kaggle-environments
from lux.game import Game
from lux.game_map import Cell, RESOURCE_TYPES
from lux.constants import Constants
from lux.game_constants import GAME_CONSTANTS
from lux import annotate
import math
import json
from kaggle_environments import make
env = make("lux_ai_2021", configuration={"seed": 41, "loglevel": 1, "annotations" : True}, debug=True)
# steps = env.run(["./agent.py", "./agent.py"])
# steps = env.run(["./agent1.py", "./agent1.py"])
steps = env.run(["./agent_basic.py", "./agent_basic.py"])

# html_output  = env.render(mode="html", width=1200, height=800)
html_output  = env.render(mode="html")


# Save the HTML output to a file
with open("lux_ai_2021_simulation1.html", "w") as file:
    file.write(html_output)

print("Simulation saved to lux_ai_2021_simulation.html")


















