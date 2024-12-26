
from kaggle_environments import make
import time

# Create the environment
env = make("lux_ai_2021", configuration={"seed": 41, "loglevel": 1, "annotations": True}, debug=True)

# Run the environment with the specified agents
steps = env.run(["./agent1.py", "./agent1.py"])

# Iterate over each step and render it
for step in steps:
    # Render the current step
    display = env.render(mode="html", width=1200, height=800)

    # Display the rendered step (if using Jupyter, this will display in the notebook)
    # If not using Jupyter, you might need to save each frame to a file or use a different method to view it
    print('---------------------------------')
    print(display)
    print('---------------------------------')

    # Pause for a short time to simulate frame-by-frame viewing
    time.sleep(1)  # Adjust the sleep time as needed





















