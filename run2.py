import webbrowser
from kaggle_environments import make

# Initialize the environment
env = make("lux_ai_2021", configuration={"seed": 42, "loglevel": 1, "annotations": True}, debug=True)

# Run your agent
# steps = env.run(["./agent1_multi_.py", "./agent_basic.py"])
# steps = env.run(["./agent1_multi_.py", "./agent2_jp_comesido.py"])
# steps = env.run(["./a3_quickstart.py", "./agent2_jp_comesido.py"])
# steps = env.run(["./a3_quickstart.py", "simple_agent"])
# steps = env.run(["./agent_basic.py", "simple_agent"])
# steps = env.run(["./agent_basic.py", "agent_basic_ws.py"])
# steps = env.run(["./agent_basic_ws_1.py", "agent_basic_ws.py"])
# steps = env.run(["./agent_basic_ws_1.py", "agent2_jp_comesido.py"])
steps = env.run(["./agent_basic.py", "agent_basic.py"])
# steps = env.run(["./agent_basic_ws_basic.py", "agent_basic_ws.py"])
print(steps)
# Render and save HTML to a file
html_output = env.render(mode='html')
with open("lux_ai_output.html", "w") as f:
    f.write(html_output)

# Open the HTML file in a browser
# webbrowser.open('lux_ai_output.html')